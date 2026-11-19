"""Offline materialization of an explicitly pinned Skill package."""
from __future__ import annotations

import io
import json
import re
import stat
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from ..domain.integrity import sha256_bytes, tree_hash
from ..domain.paths import validate_relative
from .safe_extract import MAX_FILES, MAX_SINGLE, MAX_TOTAL_BYTES, inspect_directory, stat_import_path


def read_lock(lock_path: Path) -> dict:
    lock_stat = stat_import_path(lock_path)
    if not stat.S_ISREG(lock_stat.st_mode) or lock_stat.st_size > MAX_SINGLE:
        raise ValueError("Manifesto de consumo excede o limite de tamanho.")
    lock = json.loads(lock_path.read_bytes())
    if not isinstance(lock, dict) or type(lock.get("lockVersion")) is not int or lock["lockVersion"] != 1:
        raise ValueError("Versão do manifesto de consumo desconhecida.")
    keys = ("skillId", "capabilityId", "version", "packageSha256", "treeSha256", "profile")
    if any(not isinstance(lock.get(key), str) or not lock[key].strip() for key in keys):
        raise ValueError("Manifesto de consumo incompleto.")
    if any(not re.fullmatch(r"[a-f0-9]{64}", lock[key]) for key in ("packageSha256", "treeSha256")):
        raise ValueError("Hash inválido no manifesto de consumo.")
    skill_id = lock["skillId"]
    revision = lock.get("revision")
    if not skill_id.startswith("urn:lia:cap:") or type(revision) is not int or revision < 1:
        raise ValueError("Identidade ou revisão da oficina inválida.")
    UUID(skill_id.removeprefix("urn:lia:cap:"))
    dependencies = lock.get("dependencies")
    if not isinstance(dependencies, list) or len(dependencies) > 100:
        raise ValueError("Lista de dependências inválida.")
    seen = {skill_id}
    for requirement in dependencies:
        if not isinstance(requirement, dict) or set(requirement) != {"skillId", "revision", "treeSha256"}:
            raise ValueError("Dependência precisa declarar ID, revisão e árvore.")
        identity = requirement["skillId"]
        if (not isinstance(identity, str) or not identity.startswith("urn:lia:cap:")
                or identity in seen or type(requirement["revision"]) is not int
                or requirement["revision"] < 1
                or not isinstance(requirement["treeSha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", requirement["treeSha256"])):
            raise ValueError("Dependência fixa inválida ou duplicada.")
        UUID(identity.removeprefix("urn:lia:cap:"))
        seen.add(identity)
    return lock


def dependency_pin(lock: dict) -> dict:
    return {name: lock[name] for name in ("skillId", "revision", "treeSha256")}


def _verify_dependencies(lock: dict, sources: tuple[tuple[Path, Path], ...]) -> None:
    if len(sources) > 100:
        raise ValueError("O conjunto local excede 100 dependências.")
    supplied = {}
    for pin_path, directory in sources:
        pin = read_lock(pin_path)
        identity = pin["skillId"]
        if identity == lock["skillId"] or identity in supplied or pin["profile"] != lock["profile"]:
            raise ValueError("Dependência local duplicada ou de outro perfil.")
        supplied[identity] = (pin, directory)
    validated = set()
    visiting = {lock["skillId"]}

    def visit(requirement: dict) -> None:
        identity = requirement["skillId"]
        if identity in visiting:
            raise ValueError(f"Ciclo de dependência: {identity}")
        local = supplied.get(identity)
        if local is None:
            raise ValueError(f"Dependência local ausente: {identity}")
        pin, directory = local
        if requirement != dependency_pin(pin):
            raise ValueError(f"Revisão de dependência divergente: {identity}")
        if identity in validated:
            return
        visiting.add(identity)
        for child in pin["dependencies"]:
            visit(child)
        files = inspect_directory(directory).files
        if not any(entry.path == "SKILL.md" for entry in files) or tree_hash({
            entry.path: sha256_bytes(entry.data) for entry in files
        }) != pin["treeSha256"]:
            raise ValueError(f"Árvore da dependência local diverge: {identity}")
        visiting.remove(identity)
        validated.add(identity)

    for requirement in lock["dependencies"]:
        visit(requirement)
    if validated != supplied.keys():
        raise ValueError("Dependência local fornecida sem referência no manifesto.")


def materialize(lock_path: Path, package_path: Path, destination: Path, *,
                dependencies: tuple[tuple[Path, Path], ...] = ()) -> dict:
    """Verify the dependency closure and package before preparing a new directory."""
    lock = read_lock(lock_path)
    _verify_dependencies(lock, dependencies)
    skill_id, revision = lock["skillId"], lock["revision"]
    package_stat = stat_import_path(package_path)
    if not stat.S_ISREG(package_stat.st_mode) or package_stat.st_size > MAX_TOTAL_BYTES:
        raise ValueError("Pacote inválido ou grande demais.")
    if destination.exists() or destination.is_symlink():
        raise ValueError("O destino já existe. Escolha uma pasta nova.")

    with package_path.open("rb") as stream:
        data = stream.read(MAX_TOTAL_BYTES + 1)
    if len(data) > MAX_TOTAL_BYTES or sha256_bytes(data) != lock["packageSha256"]:
        raise ValueError("O SHA-256 do pacote diverge da revisão fixada.")
    with zipfile.ZipFile(io.BytesIO(data)) as package:
        entries = package.infolist()
        if len(entries) > MAX_FILES or sum(item.file_size for item in entries) > MAX_TOTAL_BYTES:
            raise ValueError("O pacote excede os limites de materialização.")
        names = [item.filename for item in entries]
        if len(names) != len(set(names)):
            raise ValueError("O pacote contém entradas repetidas.")
        manifest_entry = package.getinfo("manifest.json")
        if manifest_entry.file_size > MAX_SINGLE:
            raise ValueError("O manifesto do pacote excede o limite.")
        manifest = json.loads(package.read(manifest_entry))
        if (manifest["formatVersion"], manifest["type"], manifest["id"], manifest["version"]) != (
            1, "agent-skill", lock["capabilityId"], lock["version"]
        ):
            raise ValueError("O manifesto do pacote diverge da Skill fixada.")
        provenance_entry = package.getinfo("provenance.json")
        if provenance_entry.file_size > MAX_SINGLE:
            raise ValueError("A procedência excede o limite.")
        provenance = json.loads(package.read(provenance_entry))
        if provenance["source"]["upstream"] != f"{skill_id}:{revision}":
            raise ValueError("A procedência diverge da revisão da oficina.")
        declared = manifest["payload"]["files"]
        declared_by_path = {item["path"]: item for item in declared}
        payload = [item for item in entries if item.filename.startswith("payload/")]
        if len(declared) != len(declared_by_path) or {
            item.filename.removeprefix("payload/") for item in payload
        } != set(declared_by_path):
            raise ValueError("O payload diverge da lista declarada de arquivos.")

        destination.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix=".lia-skill-", dir=destination.parent) as temporary:
            staging = Path(temporary) / "skill"
            staging.mkdir()
            hashes = {}
            seen = set()
            for item in payload:
                rel = item.filename.removeprefix("payload/")
                safe = validate_relative(rel)
                canonical = safe.posix.casefold()
                if safe.posix != rel or canonical in seen or item.is_dir():
                    raise ValueError("O payload contém caminhos ambíguos.")
                seen.add(canonical)
                mode = stat.S_IFMT(item.external_attr >> 16)
                if mode not in (0, stat.S_IFREG) or item.external_attr & 0x400:
                    raise ValueError("O payload contém link ou arquivo especial.")
                if item.file_size > MAX_SINGLE or item.file_size != declared_by_path[rel]["size"]:
                    raise ValueError("O tamanho do arquivo diverge do manifesto.")
                content = package.read(item)
                hashes[rel] = sha256_bytes(content)
                if hashes[rel] != declared_by_path[rel]["sha256"]:
                    raise ValueError("O SHA-256 do arquivo diverge do manifesto.")
                target = staging / safe.posix
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as output:
                    output.write(content)
            digest = tree_hash(hashes)
            if "SKILL.md" not in hashes or digest != lock["treeSha256"] or digest != manifest["hashes"]["treeHash"]:
                raise ValueError("A árvore da Skill diverge da revisão fixada.")
            if destination.exists() or destination.is_symlink():
                raise ValueError("O destino passou a existir durante a operação.")
            staging.rename(destination)

    return {"path": str(destination), "treeSha256": digest, "profile": lock["profile"]}
