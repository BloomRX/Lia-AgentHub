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
from .safe_extract import MAX_FILES, MAX_SINGLE, MAX_TOTAL_BYTES, stat_import_path


def materialize(lock_path: Path, package_path: Path, destination: Path) -> dict:
    """Verify selected package bytes before preparing a new directory."""
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
    if lock.get("dependencies") != []:
        raise ValueError("O manifesto precisa declarar que esta Skill não tem dependências.")
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
