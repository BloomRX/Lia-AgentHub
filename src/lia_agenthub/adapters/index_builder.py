"""Índice compartilhável — IDX-1 publicar, IDX-2 validar, IDX-3 leitor de referência.

O índice NÃO é assinado. Ele tem hashes, que provam integridade do arquivo,
não autoria (SECURITY §3.7.1). Não existe campo `signed` aqui.

Portabilidade: caminhos POSIX, sem absolutos, sem segredos, sem dependência
de rede. Um leitor de 20 linhas consegue consumi-lo.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from ..domain.errors import IntegrityError, ValidationError
from ..domain.model import Capability, Lifecycle
from .atomic import atomic_write_json, read_json
from .repository import Repository

INDEX_NAME = "index.json"
SCHEMA_NAME = "index.schema.json"
INDEX_SCHEMA_VERSION = 1

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Lia Agent Hub — índice de capacidades",
    "type": "object",
    "required": ["schemaVersion", "generatedAt", "capabilities"],
    "properties": {
        "schemaVersion": {"type": "integer"},
        "generatedAt": {"type": "string"},
        "signed": {"const": False,
                   "description": "Sempre false: assinatura não é implementada."},
        "capabilities": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "name", "version", "type", "trust", "license"],
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "version": {"type": "string"},
                    "type": {"type": "string"},
                    "trust": {"enum": ["unreviewed", "user-provided",
                                       "reviewed-external", "first-party"]},
                    "license": {"type": ["string", "null"]},
                    "licenseKnown": {"type": "boolean"},
                    "treeHash": {"type": "string"},
                    "containsScripts": {"type": "boolean"},
                    "egress": {"type": "array"},
                    "package": {"type": ["string", "null"]},
                    "notEvaluated": {"type": "array"},
                },
            },
        },
    },
}


def build_index(repo: Repository, *, packages_dir: Path | None = None) -> dict:
    entries = []
    for stored in repo.list_all():
        cap = stored.capability
        if cap.lifecycle is not Lifecycle.ACTIVE:
            continue
        entries.append({
            "id": cap.id,
            "name": cap.name,
            "version": cap.version,
            "type": cap.type.value,
            "description": cap.description[:280],
            "domain": cap.domain,
            "tags": list(cap.tags),
            "author": cap.author,
            "trust": cap.trust.value,
            "license": cap.license.code,
            "licenseKnown": cap.license.is_known,
            "redistributable": cap.license.redistributable,
            "treeHash": cap.tree_hash,
            "containsScripts": cap.contains_scripts,
            "egress": list(cap.egress),
            "package": None,
            "notEvaluated": [
                "Conteúdo malicioso em prosa",
                "Segurança de scripts",
                "Comportamento em execução",
            ],
        })

    packages = sorted(Path(packages_dir).glob("*.lia-capability")) if packages_dir and Path(packages_dir).is_dir() else []
    by_prefix = {}
    for p in packages:
        by_prefix.setdefault(p.name.split("-0.")[0], p.name)

    for e in entries:
        if e["id"] in by_prefix:
            e["package"] = f"packages/{by_prefix[e['id']]}"

    return {
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "generatedAt": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "signed": False,
        "signatureNote": (
            "Este índice NÃO é assinado. Hashes provam integridade do arquivo, "
            "não autoria nem confiança."
        ),
        "capabilities": entries,
    }


def publish(repo: Repository, *, packages_dir: Path | None = None) -> dict:
    """IDX-1 publicar + IDX-2 validar. Recusa publicar índice inconsistente."""
    index = build_index(repo, packages_dir=packages_dir)
    problems = validate_index(index)
    if problems:
        raise ValidationError(
            "O índice gerado é inconsistente e não foi publicado: " + "; ".join(problems),
            "Isso indica um bug ou biblioteca corrompida; recarregue a biblioteca.")
    target = repo.locations.common
    target.mkdir(parents=True, exist_ok=True)
    atomic_write_json(target / INDEX_NAME, index)
    atomic_write_json(target / SCHEMA_NAME, SCHEMA)
    return index


def validate_index(index: dict) -> list[str]:
    """IDX-2. Sem dependência de jsonschema: validação mínima, explícita."""
    problems: list[str] = []
    if not isinstance(index, dict):
        return ["O índice não é um objeto JSON."]
    for key in ("schemaVersion", "generatedAt", "capabilities"):
        if key not in index:
            problems.append(f"Campo obrigatório ausente: `{key}`")
    if index.get("signed") is not False:
        problems.append("O índice declara `signed` diferente de false — assinatura "
                        "não é implementada e não pode ser afirmada.")
    caps = index.get("capabilities")
    if not isinstance(caps, list):
        problems.append("`capabilities` deve ser uma lista.")
        return problems
    seen = set()
    for i, c in enumerate(caps):
        if not isinstance(c, dict):
            problems.append(f"Entrada {i} não é objeto.")
            continue
        for key in ("id", "name", "version", "type", "trust", "license"):
            if key not in c:
                problems.append(f"Entrada {i} sem `{key}`")
        cid = c.get("id")
        if cid in seen:
            problems.append(f"`id` duplicado no índice: {cid}")
        seen.add(cid)
        pkg = c.get("package")
        if pkg and (pkg.startswith("/") or ".." in pkg or "\\" in pkg):
            problems.append(f"`package` com caminho inseguro: {pkg}")
    return problems


def read_index(common_dir: Path) -> dict | None:
    """IDX-3. Leitor de referência: funciona com o Hub desinstalado."""
    return read_json(Path(common_dir) / INDEX_NAME)


def check_consistency(index: dict, packages_dir: Path, library_dir: Path) -> dict:
    """Detecta índice que aponta para pacote ausente e vice-versa."""
    missing_packages, orphan_packages = [], []
    for c in index.get("capabilities", []):
        pkg = c.get("package")
        if not pkg:
            continue
        if not (Path(packages_dir) / Path(pkg).name).is_file():
            missing_packages.append({"id": c["id"], "package": pkg})

    known = {c["id"] for c in index.get("capabilities", [])}
    if Path(packages_dir).is_dir():
        for p in sorted(Path(packages_dir).glob("*.lia-capability")):
            stem = p.name.replace(".lia-capability", "")
            if not any(stem.startswith(k) for k in known):
                orphan_packages.append(p.name)

    indexed = {c["id"] for c in index.get("capabilities", [])}
    on_disk = set()
    if Path(library_dir).is_dir():
        for entry in Path(library_dir).iterdir():
            if (entry / ".lia" / "capability.json").is_file():
                on_disk.add(entry.name)

    fantasmas = sorted(indexed - on_disk)

    return {
        # Uma capacidade indexada que não existe no disco é inconsistência:
        # o índice estaria prometendo algo que o usuário não tem.
        "ok": not missing_packages and not orphan_packages and not fantasmas,
        "missingPackages": missing_packages,
        "orphanPackages": orphan_packages,
        "notIndexed": sorted(on_disk - indexed),
        "indexedButMissingOnDisk": fantasmas,
    }
