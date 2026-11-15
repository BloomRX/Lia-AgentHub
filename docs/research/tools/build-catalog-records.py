#!/usr/bin/env python3
"""Ferramenta de PESQUISA — gera registros de catálogo no formato do Lia Agent Hub.

O que este script faz
    Lê pastas de Agent Skills de repositórios Lia já clonados localmente (somente
    leitura) e produz, para cada uma, o registro que o Hub gravaria em
    `<Biblioteca>/<id>/.lia/capability.json` + `.lia/provenance.json`.

O que este script NÃO faz
    - Não importa nada para a biblioteca real do Hub (o Hub não foi executado).
    - Não copia payload de skills para dentro deste repositório.
    - Não altera código de produção, não instala dependências (só stdlib).
    - Não decide licença nem confiança: isso é humano.

Fidelidade ao contrato implementado
    Algoritmo reimplementado a partir da leitura estática de:
      src/lia_agenthub/domain/integrity.py   (sha256_bytes, tree_hash)
      src/lia_agenthub/domain/model.py       (Capability.as_dict, new_id, enums)
      src/lia_agenthub/domain/paths.py       (looks_like_script, EXEC_EXTS)
      src/lia_agenthub/adapters/importer.py  (BOM, _detect_license, _detect_type,
                                              _resolve_version, domain/tags/author,
                                              contentHash/treeHash, provenance)
    na branch `arena/a92004be-lia-agenthub`, commit `b4eb85f` (ver README do catálogo).
    Valores são RESEARCH/EXECUTED por esta ferramenta; só viram VALIDATED quando o
    Hub real importar o mesmo payload e produzir o mesmo id/hash.

Uso
    python3 docs/research/tools/build-catalog-records.py \
        --sources docs/research/catalog/sources.json \
        --out docs/research/catalog
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- integridade
CHUNK = 1 << 20

EXEC_EXTS = {
    ".exe", ".dll", ".bat", ".cmd", ".com", ".scr", ".msi", ".ps1", ".vbs",
    ".js", ".mjs", ".cjs", ".sh", ".py", ".rb", ".pl", ".jar", ".so", ".dylib",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_newlines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def content_hashes(data: bytes) -> dict:
    return {"asReceived": sha256_bytes(data),
            "normalized": sha256_bytes(normalize_newlines(data))}


def tree_hash(entries: dict) -> str:
    h = hashlib.sha256()
    for path in sorted(entries):
        h.update(path.encode("utf-8"))
        h.update(b"\x00")
        h.update(entries[path].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def looks_like_script(parts) -> bool:
    if any(p.lower() == "scripts" for p in parts[:-1]):
        return True
    return bool(parts) and Path(parts[-1]).suffix.lower() in EXEC_EXTS


# ---------------------------------------------------------------- frontmatter
NAME_MAX = 64
DESCRIPTION_MAX = 1024
KNOWN_FIELDS = {"name", "description", "license", "compatibility", "metadata",
                "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(text: str):
    """Parser simples do Hub: `chave: valor` por linha; aninhamento é ignorado."""
    if not text.startswith("---"):
        return {}, text, False
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text, False
    raw = text[4:end] if text.startswith("---\n") else text[3:end]
    body = text[end + 4:]
    fm = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, body, True


def has_bom(data: bytes) -> bool:
    return data.startswith(b"\xef\xbb\xbf")


def strip_bom(data: bytes) -> bytes:
    return data[3:] if has_bom(data) else data


# ---------------------------------------------------------------- modelo
def new_id(name: str, *, salt: str = "") -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or "cap"
    digest = hashlib.sha256((name + salt).encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}"


LICENSE_LABELS = (
    ("MIT License", "MIT"),
    ("Apache License", "Apache-2.0"),
    ("GNU GENERAL PUBLIC LICENSE", "GPL"),
    ("GNU LESSER GENERAL PUBLIC LICENSE", "LGPL"),
    ("BSD 3-Clause", "BSD-3-Clause"),
    ("BSD 2-Clause", "BSD-2-Clause"),
    ("Mozilla Public License", "MPL"),
    ("Creative Commons", "CC (ver arquivo)"),
    ("The Unlicense", "Unlicense"),
)


def detect_license(files: dict):
    """Presença de LICENSE na RAIZ do payload. Não infere SPDX, não presume nada."""
    for rel, data in files.items():
        if "/" in rel:
            continue
        if rel.upper().split(".")[0] in ("LICENSE", "LICENCE", "COPYING"):
            head = data[:2048].decode("utf-8", "replace")
            for known, label in LICENSE_LABELS:
                if known in head:
                    return label, "declared", rel
            return None, "unknown", rel
    return None, "unknown", None


def detect_type(files: dict) -> str:
    names = {p.lower() for p in files}
    if "skill.md" in names:
        return "agent-skill"
    if any(n.endswith("package.json") for n in names):
        return "mcp-server"
    if any(n.endswith((".md", ".txt")) for n in names):
        return "reference"
    return "unknown"


def resolve_version(fm: dict) -> str:
    """Sem manifesto de pacote: frontmatter `version` (chave de topo) ou 0.1.0."""
    if fm.get("version"):
        return str(fm["version"]).strip()
    return "0.1.0"


def validate_structural(text: str) -> list:
    """Reproduz os avisos/erros estruturais que o Hub registraria."""
    issues = []
    fm, body, ok = parse_frontmatter(text)
    if has_bom(text.encode("utf-8")):
        issues.append({"severity": "warning", "code": "BOM_PRESENT"})
    if not ok:
        issues.append({"severity": "error", "code": "NO_FRONTMATTER"})
        return issues
    for field in sorted({"name", "description"} - set(fm)):
        issues.append({"severity": "error", "code": "MISSING_FIELD", "field": field})
    for field in sorted(set(fm) - KNOWN_FIELDS):
        issues.append({"severity": "warning", "code": "UNKNOWN_FIELD", "field": field})
    name = fm.get("name", "")
    if name and not NAME_RE.match(name):
        issues.append({"severity": "error", "code": "NAME_FORMAT"})
    if name and len(name) > NAME_MAX:
        issues.append({"severity": "error", "code": "NAME_TOO_LONG"})
    desc = fm.get("description", "")
    if desc and len(desc) > DESCRIPTION_MAX:
        issues.append({"severity": "error", "code": "DESCRIPTION_TOO_LONG",
                       "length": len(desc)})
    compat = fm.get("compatibility", "")
    if compat and len(compat) > 500:
        issues.append({"severity": "warning", "code": "COMPATIBILITY_TOO_LONG",
                       "length": len(compat)})
    if not body.strip():
        issues.append({"severity": "warning", "code": "EMPTY_BODY"})
    return issues


# ---------------------------------------------------------------- leitura
def read_payload(folder: Path) -> dict:
    files = {}
    for p in sorted(folder.rglob("*")):
        if not p.is_file() or p.is_symlink():
            continue
        files[p.relative_to(folder).as_posix()] = p.read_bytes()
    return files


def build_record(folder: Path, *, upstream: str) -> dict:
    raw = read_payload(folder)
    warnings = []
    files = {}
    for rel, data in raw.items():
        if has_bom(data):
            warnings.append(f"`{rel}` tinha BOM (U+FEFF); removido e registrado.")
            data = strip_bom(data)
        files[rel] = data

    rtype = detect_type(files)
    skill_bytes = files.get("SKILL.md") or files.get("skill.md")
    fm, _body, _ok = ({}, "", False)
    issues = []
    skill_name = ""
    domain, tags, author = "", [], None
    if rtype == "agent-skill" and skill_bytes is not None:
        text = skill_bytes.decode("utf-8", "replace")
        issues = validate_structural(text)
        if any(i["severity"] == "error" for i in issues):
            return {"blocked": True, "issues": issues, "files": sorted(files)}
        fm, _body, _ok = parse_frontmatter(text)
        skill_name = fm.get("name", "")
        meta = fm.get("metadata", "") or ""
        for chave in ("domain", "dominio", "domínio"):
            for par in meta.replace(";", ",").split(","):
                if par.strip().lower().startswith(chave + ":"):
                    domain = par.split(":", 1)[1].strip()
        if "tags:" in meta:
            bruto = meta.split("tags:", 1)[1]
            for sep in (" domain:", " dominio:", " author:", " license:"):
                if sep in bruto:
                    bruto = bruto.split(sep, 1)[0]
            tags = [x.strip() for x in bruto.replace(";", ",").split(",") if x.strip()]
        for chave in ("author", "autor"):
            if chave + ":" in meta:
                author = meta.split(chave + ":", 1)[1].split(",")[0].strip() or None
                break
        # O Hub deriva o nome da pasta do primeiro caminho com "/": ao importar a
        # pasta da skill diretamente, isso aponta para a primeira SUBPASTA.
        derived_folder = next((p.split("/")[0] for p in files if "/" in p), None)
        if derived_folder and skill_name and skill_name != derived_folder:
            issues.append({"severity": "warning", "code": "NAME_FOLDER_MISMATCH",
                           "detail": f"name=`{skill_name}` vs pasta derivada "
                                     f"`{derived_folder}` (artefato de import direto)"})

    detected, lstatus, lic_file = detect_license(files)
    if detected is None:
        warnings.append("Nenhum arquivo de licença encontrado na raiz do payload. "
                        "Ausência de licença NÃO significa que o recurso é livre.")

    display = skill_name or folder.name
    per_file = {rel: sha256_bytes(data) for rel, data in files.items()}
    th = tree_hash(per_file)
    primary = skill_bytes or b""
    hashes = {"contentHash": sha256_bytes(primary) if primary else "", "treeHash": th}
    cap_id = new_id(display, salt=th)
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    contains_scripts = any(looks_like_script(tuple(rel.split("/"))) for rel in files)

    capability = {
        "schemaVersion": 1,
        "id": cap_id,
        "name": display,
        "version": resolve_version(fm),
        "type": rtype,
        "description": "",
        "domain": domain,
        "tags": tags,
        "author": author,
        "license": {
            "code": detected, "content": None, "weights": None, "status": lstatus,
            "redistributable": False, "redistribution_basis": None,
            "notice_required": bool(detected),
        },
        "source": {"upstream": upstream, "commit": None, "imported_at": None,
                   "method": "local", "original_name": None},
        "trust": "unreviewed",
        "lifecycle": "quarantined",
        "contentHash": hashes["contentHash"],
        "treeHash": th,
        "containsScripts": contains_scripts,
        "declaredPermissions": [],
        "egress": [],
        "secrets": {"envVars": []},
        "requirements": None,
        "history": [],
        "versionOf": None,
    }
    provenance = {
        "schemaVersion": 1,
        "upstream": upstream,
        "importedAt": None,
        "method": "local",
        "files": [
            {"path": rel, "size": len(files[rel]), "sha256": per_file[rel],
             "normalizedSha256": content_hashes(files[rel])["normalized"],
             "executable": looks_like_script(tuple(rel.split("/")))}
            for rel in sorted(files)
        ],
        "hashes": hashes,
        "note": "Hashes provam integridade, não autoria.",
    }
    return {
        "blocked": False,
        "capability": capability,
        "provenance": provenance,
        "frontmatter": fm,
        "issues": issues,
        "warnings": warnings,
        "licenseFile": lic_file,
        "generatedAt": now,
        "fileCount": len(files),
        "bytes": sum(len(d) for d in files.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sources = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for src in sources["sources"]:
        base = Path(src["localRoot"])
        if not base.is_dir():
            print(f"[SKIP] {src['slug']}: {base} não existe", file=sys.stderr)
            continue
        records = []
        for entry in src["skills"]:
            folder = base / entry["folder"]
            if not folder.is_dir():
                print(f"[SKIP] {src['slug']}/{entry['folder']} ausente", file=sys.stderr)
                continue
            default_upstream = f'{src["upstream"]}{entry["folder"]}'
            built = build_record(folder, upstream=entry.get("upstream") or default_upstream)
            rec = {
                "capability": built.get("capability"),
                "provenance": built.get("provenance"),
                "researchNotes": {
                    **entry.get("research", {}),
                    "sourceRepo": src["repo"],
                    "sourceBranch": src["branch"],
                    "sourceCommit": src["commit"],
                    "sourcePath": str(folder.relative_to(base.parent)) if base.parent else entry["folder"],
                    "folder": entry["folder"],
                    "fileCount": built.get("fileCount"),
                    "payloadBytes": built.get("bytes"),
                    "frontmatter": built.get("frontmatter"),
                    "structuralIssues": built.get("issues"),
                    "importWarnings": built.get("warnings"),
                    "licenseFileInPayload": built.get("licenseFile"),
                    "blocked": built.get("blocked", False),
                    "generatedAt": built.get("generatedAt"),
                    "evidenceClass": "EXECUTED (ferramenta de pesquisa) — não VALIDATED pelo Hub",
                },
            }
            records.append(rec)
            total += 1
        payload = {
            "schemaNote": (
                "Registros no formato implementado pelo Lia Agent Hub "
                "(schemaVersion 1). `capability` e `provenance` seguem o contrato "
                "de `.lia/capability.json` e `.lia/provenance.json`. "
                "`researchNotes` é metadado de pesquisa e NÃO faz parte do contrato."
            ),
            "source": {
                "repo": src["repo"], "branch": src["branch"], "commit": src["commit"],
                "inspectedAt": src.get("inspectedAt"), "localRoot": src["localRoot"],
                "upstream": src["upstream"],
            },
            "generator": {
                "tool": "docs/research/tools/build-catalog-records.py",
                "algorithmSource": src.get("algorithmSource"),
                "hubBranch": src.get("hubBranch"),
                "hubCommit": src.get("hubCommit"),
                "note": ("Reimplementação de pesquisa do algoritmo documentado. "
                         "O Hub não foi executado; nada foi gravado na biblioteca real."),
            },
            "recordCount": len(records),
            "records": records,
        }
        out = out_dir / f"{src['slug']}.records.json"
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(f"[OK] {out} — {len(records)} registros")
    print(f"Total: {total} registros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
