"""Pipeline de importação — 6 passos, nenhum efeito colateral antes da admissão.

SECURITY §8: nada é executado, nada é copiado para a biblioteca antes de
todas as verificações passarem.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from ..domain.errors import ImportRejected, SecurityError
from ..domain.integrity import content_hashes, sha256_bytes, tree_hash
from ..domain.model import (
    Capability, License, LicenseStatus, ResourceType, Severity, Source, Trust,
    new_id, notice_obrigatorio,
)
from ..domain.paths import looks_like_script
from ..domain.skills import (
    check_references, folder_name_do_recurso, has_blocking, summarize,
    validate_skill,
)
from ..domain.unicode_policy import Context, has_bom, scan, strip_bom
from .repository import Repository
from .safe_extract import Extraction, inspect_directory, inspect_package, inspect_zip

MANIFEST_NAME = "manifest.json"


@dataclass
class ImportReport:
    """O que se sabe, o que não se sabe, e o que exige humano."""

    ok: bool
    capability_id: str | None = None
    name: str = ""
    resource_type: str = ResourceType.UNKNOWN.value
    files: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    unicode_findings: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    detected_license: str | None = None
    license_status: str = LicenseStatus.UNKNOWN.value
    requires_review: bool = False
    blocked_reason: str = ""
    hint: str = ""
    contains_scripts: bool = False
    hashes: dict[str, str] = field(default_factory=dict)
    staged_at: str | None = None
    already_present: bool = False

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "capabilityId": self.capability_id,
            "name": self.name,
            "resourceType": self.resource_type,
            "files": self.files,
            "issues": self.issues,
            "unicodeFindings": self.unicode_findings,
            "warnings": self.warnings,
            "detectedLicense": self.detected_license,
            "licenseStatus": self.license_status,
            "requiresReview": self.requires_review,
            "blockedReason": self.blocked_reason,
            "hint": self.hint,
            "containsScripts": self.contains_scripts,
            "hashes": self.hashes,
            "stagedAt": self.staged_at,
            "alreadyPresent": self.already_present,
            "note": (
                "Hashes verificam integridade, não autoria. Nenhum arquivo foi "
                "executado. Confiança é decisão humana."
            ),
        }


LICENSE_FILE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING", "LICENCE")


def _detect_license(files: dict[str, bytes]) -> tuple[str | None, str]:
    """Detecta PRESENÇA de licença. Não infere SPDX. Não presume permissão."""
    for rel, data in files.items():
        if "/" in rel:
            continue
        if rel.upper().split(".")[0] in ("LICENSE", "LICENCE", "COPYING"):
            head = data[:2048].decode("utf-8", "replace")
            for known, label in (
                ("MIT License", "MIT"),
                ("Apache License", "Apache-2.0"),
                ("GNU GENERAL PUBLIC LICENSE", "GPL"),
                ("GNU LESSER GENERAL PUBLIC LICENSE", "LGPL"),
                ("BSD 3-Clause", "BSD-3-Clause"),
                ("BSD 2-Clause", "BSD-2-Clause"),
                ("Mozilla Public License", "MPL"),
                ("Creative Commons", "CC (ver arquivo)"),
                ("The Unlicense", "Unlicense"),
            ):
                if known in head:
                    return label, LicenseStatus.DECLARED.value
            # Arquivo presente, texto não reconhecido: NÃO inventamos um código.
            return None, LicenseStatus.UNKNOWN.value
    return None, LicenseStatus.UNKNOWN.value


def _detect_type(files: dict[str, bytes]) -> ResourceType:
    names = {p.lower() for p in files}
    if "skill.md" in names:
        return ResourceType.AGENT_SKILL
    if any(n.endswith("package.json") for n in names):
        return ResourceType.MCP_SERVER
    if any(n.endswith((".md", ".txt")) for n in names):
        return ResourceType.REFERENCE
    return ResourceType.UNKNOWN


def _resolve_version(manifest: dict | None, skill_text: bytes | None) -> str:
    """Versão declarada pelo próprio recurso, na ordem mais confiável.

    Manifesto de pacote vence (foi escrito pelo Hub). Depois o frontmatter da
    SKILL.md. Sem declaração, `0.1.0` — e `0.1.0` significa "não declarada",
    não "primeira versão": o histórico é quem diz o que aconteceu.
    """
    if manifest and manifest.get("version"):
        return str(manifest["version"])
    if skill_text is not None:
        from ..domain.skills import parse_frontmatter
        fm = parse_frontmatter(skill_text.decode("utf-8", "replace")).frontmatter
        if fm.get("version"):
            return str(fm["version"]).strip()
    return "0.1.0"


def _read_manifest(files: dict[str, bytes]) -> dict | None:
    raw = files.get(MANIFEST_NAME)
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


class Importer:
    def __init__(self, repo: Repository):
        self.repo = repo

    # ---- entrada ---------------------------------------------------------
    def from_path(self, raw_path: str | Path, *, upstream: str | None = None,
                  dry_run: bool = False,
                  version_of: str | None = None) -> ImportReport:
        path = Path(raw_path)
        if not path.exists():
            return ImportReport(False, blocked_reason=f"Caminho não existe: {path}",
                                hint="Verifique o caminho e tente novamente.")

        try:
            if path.is_dir():
                extraction = inspect_directory(path)
            elif path.name.endswith(".lia-capability"):
                # Pacote do Hub: o conteúdo vive sob payload/. Desembrulhar antes
                # de tudo — senão o reimport produziria payload/payload/SKILL.md
                # e o hash nunca casaria com a origem.
                extraction = inspect_package(path)
            elif path.suffix.lower() == ".zip":
                extraction = inspect_zip(path.read_bytes())
            else:
                # arquivo solto: vira um pacote de um arquivo só
                data = path.read_bytes()
                from .safe_extract import ExtractedFile
                extraction = Extraction(files=[
                    ExtractedFile(path=path.name, data=data,
                                  is_executable=looks_like_script((path.name,)))])
        except SecurityError as e:
            return ImportReport(False, blocked_reason=e.message, hint=e.hint)

        return self.from_extraction(extraction, upstream=upstream or str(path),
                                    dry_run=dry_run, version_of=version_of)

    def from_extraction(self, extraction: Extraction, *, upstream: str | None = None,
                        dry_run: bool = False,
                        version_of: str | None = None) -> ImportReport:
        files = {f.path: f.data for f in extraction.files}
        report = ImportReport(ok=False, warnings=list(extraction.warnings))
        report.contains_scripts = extraction.contains_scripts

        # ---- 1. BOM: normaliza e REGISTRA (nunca silencioso) -------------
        normalized: dict[str, bytes] = {}
        for rel, data in files.items():
            if has_bom(data):
                report.warnings.append(
                    f"`{rel}` tinha BOM (U+FEFF) no início; removido e registrado.")
                data = strip_bom(data)
            normalized[rel] = data
        files = normalized

        # ---- 2. Unicode por região, sem apagar nada ----------------------
        unicode_block = False
        for rel, data in files.items():
            if not rel.lower().endswith((".md", ".txt", ".json")):
                continue
            text = data.decode("utf-8", "replace")
            res = scan(text, context=Context.PROSE)
            report.unicode_findings.extend(
                {**f.as_dict(), "file": rel} for f in res.findings
            )
            if res.rejected:
                unicode_block = True
                report.issues.append({
                    "severity": "error", "code": "UNICODE_REJECT",
                    "message": f"{len(res.rejected)} caractere(s) bidirecional(is) ou de "
                               f"tag em contexto que não admite uso legítimo.",
                    "where": rel,
                })

        if unicode_block:
            report.blocked_reason = (
                "O recurso contém caracteres invisíveis que não têm uso legítimo "
                "em bloco de código ou identificador.")
            report.hint = (
                "Abra o arquivo apontado e remova os caracteres listados. Eles podem "
                "ter sido inseridos por acidente ou de propósito.")
            return report

        if any(f["category"] == "B" for f in report.unicode_findings):
            report.requires_review = True
        if any(f["category"] == "D" for f in report.unicode_findings):
            report.requires_review = True

        # ---- 3. tipo + validação estrutural ------------------------------
        rtype = _detect_type(files)
        report.resource_type = rtype.value

        skill_text = files.get("SKILL.md") or files.get("skill.md")
        skill_name = ""
        declared_license: str | None = None
        declared_description = ""
        domain, tags, author = "", [], None

        if rtype is ResourceType.AGENT_SKILL and skill_text is not None:
            text = skill_text.decode("utf-8", "replace")
            # A pasta do recurso vem do CAMINHO DE ORIGEM, não do layout
            # interno do payload. Antes usava-se o primeiro segmento de
            # qualquer arquivo com "/", então um recurso flat com `docs/x.md`
            # era comparado contra a pasta `docs`. Ver folder_name_do_recurso.
            folder = folder_name_do_recurso(upstream, list(files))
            issues = validate_skill(text, folder_name=folder)
            # Referências a arquivos: só faz sentido com o pacote completo em mãos.
            # folder_name é necessário aqui: sem ele, uma referência no
            # formato `<a-propria-skill>/x.md` não é reconhecida como interna.
            issues.extend(check_references(text, set(files), folder_name=folder))
            report.issues.extend(i.as_dict() for i in issues)
            if has_blocking(issues):
                # R-4.1d: citar o CÓDIGO real. A mensagem genérica mandava
                # "corrigir os campos apontados como erro" mesmo quando a
                # causa era outra — o usuário caçava um problema inexistente
                # no frontmatter.
                erros = [i for i in issues if i.severity is Severity.ERROR]
                codigos = sorted({i.code for i in erros})
                report.blocked_reason = (
                    "O recurso foi recusado por erro estrutural: "
                    + ", ".join(codigos) + ".")
                report.hint = "; ".join(sorted({i.message for i in erros})[:3])
                return report
            from ..domain.skills import parse_frontmatter
            fm = parse_frontmatter(text).frontmatter
            skill_name = fm.get("name", "")
            # P-E2: declaração de licença no frontmatter.
            declared_license = (fm.get("license") or "").strip() or None
            declared_description = (fm.get("description") or "").strip()
            # `metadata` é um saco de chaves livres do formato Agent Skills.
            # Jogá-lo inteiro em `domain` rotulava toda skill com a string crua
            # ("tags:juridico,..."). Extraímos só o que sabemos interpretar.
            meta = fm.get("metadata", "") or ""
            domain = ""
            for chave in ("domain", "dominio", "domínio"):
                for par in meta.replace(";", ",").split(","):
                    if par.strip().lower().startswith(chave + ":"):
                        domain = par.split(":", 1)[1].strip()
            if "tags:" in meta:
                bruto = meta.split("tags:", 1)[1]
                # corta na próxima chave conhecida, se houver
                for sep in (" domain:", " dominio:", " author:", " license:"):
                    if sep in bruto:
                        bruto = bruto.split(sep, 1)[0]
                tags = [x.strip() for x in bruto.replace(";", ",").split(",") if x.strip()]
            for chave in ("author", "autor"):
                if chave + ":" in meta:
                    author = meta.split(chave + ":", 1)[1].split(",")[0].strip() or None
                    break

        # ---- 4. manifesto de pacote .lia-capability ----------------------
        # Preferir o manifesto lido pelo extrator de pacotes: ele não está em
        # `files` porque `payload/` foi desembrulhado.
        manifest = extraction.manifest or _read_manifest(files)
        if manifest:
            declared = manifest.get("files") or manifest.get("payload", {}).get("files") or []
            for entry in declared:
                rel = entry.get("path") if isinstance(entry, dict) else None
                if not rel:
                    continue
                if rel not in files:
                    report.issues.append({
                        "severity": "warning", "code": "MANIFEST_MISSING_FILE",
                        "message": f"O manifesto declara `{rel}`, que não está no pacote.",
                        "where": MANIFEST_NAME,
                    })
            extra = set(files) - {"manifest.json"} - {
                (e.get("path") if isinstance(e, dict) else None) for e in declared
            } - {"provenance.json", "NOTICE", "THIRD_PARTY_NOTICES.md"}
            for rel in sorted(x for x in extra if x):
                report.issues.append({
                    "severity": "warning", "code": "UNMANIFESTED_FILE",
                    "message": f"`{rel}` está no pacote mas não consta no manifesto.",
                    "where": MANIFEST_NAME,
                })

        # ---- 5. licença: presença, nunca inferência ----------------------
        #
        # P-E2 / R-2.3: o campo `license` do frontmatter é uma DECLARAÇÃO do
        # autor, não permissão. Antes ele era ignorado: se não houvesse
        # arquivo `LICENSE`, o registro saía `unknown` — 47 recursos do acervo
        # real "sem licença" que na verdade tinham licença escrita no texto.
        #
        # Ordem de confiança: arquivo de licença (evidência física) vence
        # frontmatter (afirmação). Se só há frontmatter, registramos como
        # declarado e a base aponta que a evidência é textual — nunca
        # `redistributable=True`, que continua exigindo decisão humana.
        detected, lstatus = _detect_license(files)
        base_declarada = "arquivo de licença no payload" if detected else ""
        if detected is None and declared_license:
            detected = declared_license
            lstatus = LicenseStatus.DECLARED.value
            base_declarada = ("frontmatter da SKILL.md — afirmação do autor, "
                              "não verificação")
        report.detected_license = detected
        report.license_status = lstatus
        if detected is None:
            report.warnings.append(
                "Nenhum arquivo de licença encontrado. Ausência de licença NÃO "
                "significa que o recurso é livre.")

        # ---- 6. metadados e staging -------------------------------------
        display = skill_name or (manifest or {}).get("name") or Path(upstream or "recurso").stem
        cap_id = new_id(display, salt=tree_hash({k: sha256_bytes(v) for k, v in files.items()}))
        report.capability_id = cap_id
        report.name = display

        # Conteúdo idêntico já na biblioteca: o id é derivado do conteúdo,
        # então isto é IDENTIDADE, não conflito. Reportar como tal é mais
        # honesto do que fingir que é uma importação nova.
        if self.repo.exists(cap_id):
            report.ok = True
            report.already_present = True
            report.blocked_reason = ""
            report.warnings.append(
                "Conteúdo idêntico já está na sua biblioteca. Nada foi duplicado.")
            report.hint = "Se quiser outra cópia, altere o conteúdo ou renomeie o recurso."
            return report

        if dry_run:
            report.ok = True
            report.warnings.append("Simulação: nada foi gravado no disco.")
            return report

        per_file = {rel: sha256_bytes(data) for rel, data in files.items()}
        th = tree_hash(per_file)
        primary = files.get("SKILL.md") or files.get("skill.md") or b""
        report.hashes = {"contentHash": sha256_bytes(primary) if primary else "", "treeHash": th}
        report.files = [
            {"path": rel, "size": len(data),
             "sha256": per_file[rel],
             "normalizedSha256": content_hashes(data)["normalized"],
             "executable": looks_like_script(tuple(rel.split("/")))}
            for rel, data in sorted(files.items())
        ]

        now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        cap = Capability(
            id=cap_id,
            name=display,
            version=_resolve_version(manifest, skill_text),
            type=rtype,
            # P-E1: manifesto primeiro; frontmatter como fallback quando não
            # houver manifesto. Antes o fallback não existia e o catálogo
            # inteiro saía com 48 descrições vazias mesmo tendo o texto no
            # SKILL.md. Só preenche o que estava vazio — aditivo.
            description=((manifest or {}).get("description", "") or ""
                         or declared_description),
            domain=domain,
            tags=tags,
            author=author,
            # Licença DETECTADA é registrada como declarada — mas nunca como
            # permissão. Detectar um arquivo MIT não é revisar a licença, e o
            # direito de redistribuir continua sendo decisão humana.
            #
            # `notice_required` é DERIVADO da licença identificada, não lido do
            # payload: um recurso importado não decide obrigação legal sobre si
            # mesmo. Antes o campo era omitido e voltava sempre False, então
            # um MIT era exportado sem NOTICE — obrigação do texto MIT
            # descumprida por omissão, não por decisão.
            license=License(
                code=detected,
                status=LicenseStatus(lstatus),
                redistributable=False,
                notice_required=notice_obrigatorio(detected),
                redistribution_basis=base_declarada or None,
            ),
            source=Source(upstream=upstream, imported_at=now, method="local"),
            trust=Trust.UNREVIEWED,
            content_hash=report.hashes["contentHash"],
            tree_hash=th,
            contains_scripts=report.contains_scripts,
            version_of=version_of,
        )
        provider = {"schemaVersion": 1, "upstream": upstream, "importedAt": now,
                    "method": "local", "files": report.files,
                    "hashes": report.hashes,
                    "note": "Hashes provam integridade, não autoria."}

        self.repo.stage(cap_id, files, cap.as_dict(), provider,
                        {"action": "import", "at": now, "upstream": upstream})

        report.ok = True
        report.staged_at = now
        report.warnings.append(
            "O recurso está na quarentena. A promoção à biblioteca é uma decisão sua.")
        return report

    def promote(self, cap_id: str) -> Capability:
        return self.repo.promote(cap_id).capability
