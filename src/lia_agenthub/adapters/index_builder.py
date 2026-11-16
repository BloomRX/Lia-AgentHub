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
        "scope": {"const": "active",
                  "description": "Estados incluídos neste índice. Sempre 'active': "
                                 "conteúdo em quarentena nunca é publicado."},
        "scopeNote": {"type": "string"},
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
                    "lifecycle": {"enum": ["active", "superseded",
                                           "archived", "quarantined"],
                                  "description": "Estado do registro. Presente para que "
                                                 "um leitor saiba POR QUE um recurso "
                                                 "está fora do índice, em vez de "
                                                 "concluir que ele sumiu."},
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


def _package_for(cap_id: str, packages: list[Path]) -> str | None:
    """Pacote mais recente (por nome ordenado) que pertence a esta capacidade."""
    candidatos = [p.name for p in packages
                  if p.name == f"{cap_id}.lia-capability"
                  or p.name.startswith(f"{cap_id}-")]
    return sorted(candidatos)[-1] if candidatos else None


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
            "lifecycle": cap.lifecycle.value,
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

    # Liga cada entrada ao seu pacote pelo prefixo do id. Antes isto partia o
    # nome em "-0.", o que só funcionava com versão 0.x — bastou a versão
    # declarada na SKILL.md passar a ser respeitada para o vínculo quebrar.
    packages = (sorted(Path(packages_dir).glob("*.lia-capability"))
                if packages_dir and Path(packages_dir).is_dir() else [])

    for e in entries:
        nome = _package_for(e["id"], packages)
        if nome:
            e["package"] = f"packages/{nome}"

    return {
        "schemaVersion": INDEX_SCHEMA_VERSION,
        "generatedAt": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        # O índice é a lista do que pode ser CONSUMIDO, então só entram
        # registros `active`. Declarar o escopo é o que evita a leitura
        # errada: sem isto, um recurso `superseded` ausente do índice parecia
        # ter sumido do disco. Ele não sumiu — mudou de estado.
        #
        # Segurança: conteúdo em QUARENTENA não entra num arquivo feito para
        # ser compartilhado. Incluí-lo publicaria recurso não revisado e
        # converteria quarentena em vitrine.
        "scope": "active",
        "scopeNote": (
            "Somente registros com lifecycle=active. Registros em "
            "quarentena, superseded ou archived continuam no disco e são "
            "consultáveis pela biblioteca, mas não fazem parte desta lista "
            "compartilhável. Ausência aqui NÃO significa ausência no disco."
        ),
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
        # `lifecycle` e `scope` são NOVOS: entradas geradas por versões
        # anteriores não os têm. Validamos a forma quando presentes, sem
        # exigir presença — exigir invalidaria todo índice antigo e forçaria
        # migração para uma mudança que é aditiva.
        ciclo = c.get("lifecycle")
        if ciclo is not None and ciclo not in ("active", "superseded",
                                               "archived", "quarantined"):
            problems.append(f"Entrada {i} com `lifecycle` inválido: {ciclo}")
        if ciclo == "quarantined":
            problems.append(
                f"Entrada {i} está em quarentena mas aparece no índice público. "
                f"Índice é lista de consumo; quarentena não pode estar nele.")
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
            if not any(stem == k or stem.startswith(f"{k}-") for k in known):
                orphan_packages.append(p.name)

    indexed = {c["id"] for c in index.get("capabilities", [])}

    # Lê o estado de CADA registro do disco, não só a presença. A versão
    # anterior tratava "existe no disco e não está no índice" como problema,
    # o que produzia alarme falso para `superseded`/`archived` — estados que
    # estão corretamente fora de um índice que só publica `active`.
    estado_no_disco: dict[str, str] = {}
    fora_do_indice_esperado: dict[str, str] = {}
    if Path(library_dir).is_dir():
        for entry in Path(library_dir).iterdir():
            meta = entry / ".lia" / "capability.json"
            if not meta.is_file():
                continue
            data = read_json(meta) or {}
            ciclo = data.get("lifecycle", "quarantined")
            estado_no_disco[entry.name] = ciclo

    on_disk = set(estado_no_disco)
    fantasmas = sorted(indexed - on_disk)

    faltando = sorted(on_disk - indexed)
    for cap_id in faltando:
        if estado_no_disco.get(cap_id) != "active":
            fora_do_indice_esperado[cap_id] = estado_no_disco[cap_id]

    # Só é problema um registro ATIVO que ficou fora do índice. Registro em
    # outro estado está fora por desenho, e misturá-lo com erro esconderia o
    # erro real no meio de ruído esperado.
    nao_indexados_ativos = [c for c in faltando
                            if estado_no_disco.get(c) == "active"]

    return {
        # Uma capacidade indexada que não existe no disco é inconsistência:
        # o índice estaria prometendo algo que o usuário não tem.
        "ok": (not missing_packages and not orphan_packages
               and not fantasmas and not nao_indexados_ativos),
        "missingPackages": missing_packages,
        "orphanPackages": orphan_packages,
        # Ativos que deveriam estar no índice e não estão: isto é divergência.
        "notIndexed": nao_indexados_ativos,
        # Fora do índice por estado (superseded/archived/quarantined): normal,
        # listado à parte para o relatório distinguir "ausente" de "fora".
        "notIndexedByState": fora_do_indice_esperado,
        "indexedButMissingOnDisk": fantasmas,
    }
