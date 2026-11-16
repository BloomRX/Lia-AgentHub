"""Empacotamento e exportação — formato .lia-capability (M7).

Estrutura do pacote:
  manifest.json        obrigatório, raiz
  payload/             conteúdo, caminhos POSIX
  provenance.json
  NOTICE               se a licença exigir
  THIRD_PARTY_NOTICES.md
  (sem signatures/ — não implementado; não existe campo `signed`)

Decisão de política (D-25): exportar é classificado por DESTINO.
  private/self → sempre permitido
  shared       → permitido com aviso
  public       → recusado sem direito comprovado
"""
from __future__ import annotations

import datetime as _dt
import json
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..domain.errors import IntegrityError, LiaError
from ..domain.integrity import sha256_bytes, tree_hash
from ..domain.model import Capability
from .atomic import atomic_write_bytes
from .repository import Repository

FORMAT_VERSION = 1
MANIFEST = "manifest.json"
PROVENANCE = "provenance.json"


class Target(str, Enum):
    PRIVATE = "private"
    SELF = "self"
    SHARED = "shared"
    PUBLIC = "public"


class ExportRefused(LiaError):
    pass


@dataclass
class ExportResult:
    ok: bool
    path: str | None = None
    package_hash: str | None = None
    warnings: list[str] | None = None
    refused_reason: str = ""
    hint: str = ""


#: Nomes de arquivo de licença aceitos, em ordem de preferência. Espelha a
#: detecção do importador para que os dois concordem sobre o que é "o texto".
_NOMES_LICENCA = ("LICENSE", "LICENCE", "COPYING", "LICENSE.md", "LICENSE.txt")


def _e_metadado_interno(rel: str) -> bool:
    """`rel` aponta para dentro de um diretório `.lia/`?

    Mesma canonicalização do validador de caminho (`.lia`, `.LIA`, `.lia.` no
    fim todos colapsam), aplicada a CADA segmento — um `.lia` aninhado em
    qualquer profundidade é metadado do Hub, nunca conteúdo de recurso.
    """
    for parte in rel.replace("\\", "/").split("/"):
        if parte.rstrip(" .").lower() == ".lia":
            return True
    return False


def _texto_da_licenca(files: dict[str, bytes]) -> str:
    """Texto do arquivo de licença na RAIZ do payload, se houver.

    Só a raiz: um `LICENSE` dentro de `vendor/` é de outra pessoa e não é o
    texto que se aplica a este recurso. Devolve "" quando não achar texto
    legível — quem chama decide como avisar.
    """
    for nome in _NOMES_LICENCA:
        for rel in files:
            if "/" in rel or rel.upper() != nome.upper():
                continue
            texto = files[rel].decode("utf-8", "replace").strip()
            if texto:
                return texto[:20_000]   # teto: texto de licença é curto
    return ""


def _manifest_for(cap: Capability, files: list[dict], target: Target,
                  exported_at: str) -> dict:
    return {
        "formatVersion": FORMAT_VERSION,
        "schemaVersion": 1,
        "id": cap.id,
        "name": cap.name,
        "version": cap.version,
        "type": cap.type.value,
        "description": cap.description,
        "domain": cap.domain,
        "tags": list(cap.tags),
        "author": cap.author,
        "license": cap.license.as_dict(),
        "trust": cap.trust.value,
        "exportTarget": target.value,
        "exportedAt": exported_at,
        "containsScripts": cap.contains_scripts,
        "declaredPermissions": list(cap.declared_permissions),
        "egress": list(cap.egress),
        "secrets": {"envVars": list(cap.secrets_env_vars)},
        "payload": {"root": "payload/", "files": files},
        "hashes": {"contentHash": cap.content_hash, "treeHash": cap.tree_hash},
        "notices": {
            "licenseUnknown": not cap.license.is_known,
            "redistributionBasisMissing": not cap.license.redistribution_basis,
        },
        "integrityNote": (
            "Hashes SHA-256 provam que o conteúdo não mudou. NÃO são assinatura "
            "digital e NÃO provam autoria."
        ),
    }


def export(cap_id: str, repo: Repository, destination: Path, *,
           target: Target = Target.PRIVATE) -> ExportResult:
    """Gera o pacote. Valida antes de escrever."""
    try:
        stored = repo.load(cap_id)
    except LiaError as e:
        return ExportResult(False, refused_reason=e.message, hint=e.hint)

    cap = stored.capability
    warnings: list[str] = []

    # ---- política por destino (D-25) ------------------------------------
    if target is Target.PUBLIC:
        if not cap.license.redistributable:
            return ExportResult(
                False,
                refused_reason=(
                    "Exportação pública recusada: o recurso não está marcado como "
                    "redistribuível."),
                hint=(
                    "Redistribuição exige uma base registrada — uma licença revisada "
                    "que permita distribuir. Isso é uma decisão humana, não do Hub."),
            )
        if not cap.license.redistribution_basis:
            return ExportResult(
                False,
                refused_reason="Exportação pública recusada: falta a base de redistribuição.",
                hint="Registre a licença e a base antes de redistribuir.")

    if target is Target.SHARED:
        warnings.append(
            "STOP_AND_READ: esta capacidade não tem licença revisada. Você está "
            "decidindo compartilhá-la. O Hub não verificou se você tem esse direito "
            "e não pode verificar.")
        if not cap.license.is_known:
            warnings.append("O pacote leva `license: null` para que quem receber saiba "
                            "o mesmo que você sabe.")

    if cap.trust.value == "unreviewed":
        warnings.append(
            "Recurso não revisado por humano. O nome do arquivo recebe sufixo "
            "-NAO-REVISADO e o manifesto marca `trust: unreviewed`.")
    if cap.contains_scripts:
        warnings.append(
            "O pacote contém scripts. Nada foi executado ao empacotar; quem receber "
            "recebe `containsScripts: true`.")
    if cap.secrets_env_vars:
        warnings.append(
            f"São exportados apenas os NOMES de {len(cap.secrets_env_vars)} variável(is). "
            f"Nenhum valor é exportado — valores nunca entram no Hub.")

    # ---- montar o ZIP em memória ----------------------------------------
    files = repo.payload_files(cap_id)
    if not files:
        return ExportResult(False, refused_reason="A capacidade não tem payload.",
                            hint="Reimporte o recurso.")

    # Defesa na SAÍDA, não só na entrada. Registros importados antes da
    # correção ainda podem ter `.lia/` no payload. Exportá-los propagaria
    # metadados internos forjados para quem recebesse o pacote — a fronteira
    # de confiança vale nos dois sentidos. Removemos e AVISAMOS: descartar em
    # silêncio esconderia que o registro está contaminado.
    internos = [rel for rel in files if _e_metadado_interno(rel)]
    if internos:
        for rel in internos:
            del files[rel]
        warnings.append(
            f"{len(internos)} arquivo(s) em `.lia/` foram EXCLUÍDOS deste pacote "
            f"porque `.lia` é metadado interno do Hub e não pode viajar dentro "
            f"de um payload. Isto indica que o recurso foi importado antes da "
            f"correção ou que o payload foi alterado: {', '.join(sorted(internos)[:5])}")
        if not files:
            return ExportResult(
                False,
                refused_reason="O payload só continha metadados internos `.lia/`.",
                hint="Reimporte o recurso a partir da origem original.")

    per_file = [{"path": rel, "size": len(data), "sha256": sha256_bytes(data)}
                for rel, data in sorted(files.items())]
    th = tree_hash({f["path"]: f["sha256"] for f in per_file})
    if cap.tree_hash and cap.tree_hash != th:
        warnings.append(
            "O treeHash atual difere do registrado na importação. O conteúdo pode ter "
            "sido alterado desde então; o pacote registra o hash ATUAL.")

    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    manifest = _manifest_for(cap, per_file, target, now)
    manifest["hashes"]["treeHash"] = th

    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, data in sorted(files.items()):
            zf.writestr(f"payload/{rel}", data)
        zf.writestr(MANIFEST, json.dumps(manifest, ensure_ascii=False, indent=2))
        prov = {"schemaVersion": 1, "source": cap.source.as_dict(),
                "hashes": manifest["hashes"],
                "note": "Procedência declarada. Não é prova de autoria."}
        zf.writestr(PROVENANCE, json.dumps(prov, ensure_ascii=False, indent=2))
        if cap.license.notice_required:
            # O texto da licença encontrado no payload vai junto. MIT, BSD e
            # Apache exigem que o aviso de copyright e o texto acompanhem a
            # redistribuição — um NOTICE que só aponta para o nome da licença
            # não cumpre isso. Se o arquivo não estiver no payload, dizemos
            # isso em vez de fingir que está.
            texto_licenca = _texto_da_licenca(files)
            if texto_licenca:
                zf.writestr("NOTICE",
                            f"{cap.name} — licença {cap.license.code}\n"
                            f"{'=' * 60}\n\n"
                            f"Texto da licença encontrado no pacote:\n\n"
                            f"{texto_licenca}\n"
                            f"{'=' * 60}\n\n"
                            f"Este aviso foi incluído porque a licença "
                            f"{cap.license.code} exige que o texto acompanhe a "
                            f"redistribuição. O Lia Agent Hub não verificou "
                            f"autoria nem titularidade.\n")
            else:
                zf.writestr("NOTICE",
                            f"{cap.name} — licença {cap.license.code}\n\n"
                            f"A licença identificada exige aviso, mas nenhum "
                            f"arquivo de licença legível foi encontrado no "
                            f"payload. Peça o texto ao autor original antes de "
                            f"redistribuir.\n")
        zf.writestr("THIRD_PARTY_NOTICES.md",
                    "# Avisos de terceiros\n\n"
                    f"Recurso: {cap.name}\n\n"
                    f"Licença declarada: {cap.license.code or 'NÃO DECLARADA'}\n\n"
                    "Este pacote foi montado pelo Lia Agent Hub, que não executa "
                    "conteúdo e não verifica autoria.\n")

    data = buf.getvalue()
    package_hash = sha256_bytes(data)

    suffix = "-NAO-REVISADO" if cap.trust.value == "unreviewed" else ""
    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{cap.id}-{cap.version}{suffix}.lia-capability"
    out = dest_dir / filename

    counter = 1
    while out.exists():
        out = dest_dir / f"{cap.id}-{cap.version}{suffix}-{counter}.lia-capability"
        counter += 1

    atomic_write_bytes(out, data)
    return ExportResult(True, path=str(out), package_hash=package_hash,
                        warnings=warnings)


def verify_package(path: str | Path) -> dict:
    """Reabre um pacote e confere os hashes contra o manifesto."""
    path = Path(path)
    try:
        zf = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, FileNotFoundError) as e:
        raise IntegrityError(f"Não foi possível abrir o pacote: {e}",
                             "O arquivo pode estar corrompido.")

    with zf:
        try:
            manifest = json.loads(zf.read(MANIFEST).decode("utf-8"))
        except (KeyError, json.JSONDecodeError):
            raise IntegrityError(
                "O pacote não tem manifesto válido.",
                "Sem manifesto não há como verificar integridade ou procedência.")

        declared = {f["path"]: f["sha256"] for f in manifest["payload"]["files"]}
        real, problems = {}, []
        for rel, expected in declared.items():
            try:
                data = zf.read(f"payload/{rel}")
            except KeyError:
                problems.append(f"Arquivo declarado ausente no pacote: `{rel}`")
                continue
            actual = sha256_bytes(data)
            real[rel] = actual
            if actual != expected:
                problems.append(f"Hash não confere para `{rel}`")

        for name in zf.namelist():
            if name.startswith("payload/") and name[len("payload/"):] not in declared:
                problems.append(f"Arquivo não declarado no manifesto: `{name}`")

        computed_tree = tree_hash(real) if real else ""
        declared_tree = manifest.get("hashes", {}).get("treeHash", "")
        tree_ok = computed_tree == declared_tree

    return {
        "ok": not problems and tree_ok,
        "manifest": manifest,
        "problems": problems,
        "treeHashOk": tree_ok,
        "computedTreeHash": computed_tree,
        "declaredTreeHash": declared_tree,
    }
