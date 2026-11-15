"""Repositório em arquivos — a biblioteca. Arquivos são a fonte de verdade.

Layout por capacidade:
  <Biblioteca>/<id>/
    payload/            conteúdo original, preservado byte a byte
    .lia/capability.json metadados do Hub
    .lia/provenance.json procedência
    .lia/history.json    histórico de importações e alterações
    .lia/validation.json último relatório de validação

O índice é DERIVADO. Se ele sumir, é reconstruído varrendo os diretórios.
O disco vence sempre — nunca o índice.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from ..domain.errors import ConflictError, NotFound
from ..domain.integrity import sha256_bytes, tree_hash
from ..domain.model import Capability, Lifecycle
from .atomic import atomic_write_bytes, atomic_write_json, read_json


@dataclass
class StoredCapability:
    capability: Capability
    root: Path

    @property
    def payload(self) -> Path:
        return self.root / "payload"

    @property
    def meta(self) -> Path:
        return self.root / ".lia"


class Repository:
    def __init__(self, locations):
        self.locations = locations

    # ---- leitura ---------------------------------------------------------
    def exists(self, cap_id: str) -> bool:
        return (self.locations.library / cap_id / ".lia" / "capability.json").is_file()

    def load(self, cap_id: str) -> StoredCapability:
        root = self.locations.library / cap_id
        data = read_json(root / ".lia" / "capability.json")
        if data is None:
            raise NotFound(
                f"Capacidade `{cap_id}` não encontrada na biblioteca.",
                "Ela pode ter sido removida. Recarregue a biblioteca.")
        return StoredCapability(capability=Capability.from_dict(data), root=root)

    def list_all(self) -> list[StoredCapability]:
        """Varre o disco. Não confia no índice — ele é conveniência."""
        out: list[StoredCapability] = []
        lib = self.locations.library
        if not lib.is_dir():
            return out
        for entry in sorted(lib.iterdir()):
            if not entry.is_dir():
                continue
            data = read_json(entry / ".lia" / "capability.json")
            if data is None:
                continue
            try:
                out.append(StoredCapability(Capability.from_dict(data), entry))
            except (KeyError, ValueError):
                continue  # entrada corrompida: ignorada, não derruba a lista
        return out

    def list_quarantine(self) -> list[StoredCapability]:
        """Varre a quarentena. Mesma regra: o disco é a verdade."""
        out: list[StoredCapability] = []
        base = self.locations.quarantine
        if not base.is_dir():
            return out
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            data = read_json(entry / ".lia" / "capability.json")
            if data is None:
                continue
            try:
                out.append(StoredCapability(Capability.from_dict(data), entry))
            except (KeyError, ValueError):
                continue
        return out

    def payload_files(self, cap_id: str) -> dict[str, bytes]:
        st = self.load(cap_id)
        files: dict[str, bytes] = {}
        if not st.payload.is_dir():
            return files
        for p in sorted(st.payload.rglob("*")):
            if p.is_file() and not p.is_symlink():
                files[p.relative_to(st.payload).as_posix()] = p.read_bytes()
        return files

    # ---- escrita ---------------------------------------------------------
    def stage(self, cap_id: str, files: dict[str, bytes], metadata: dict,
              provenance: dict, history_entry: dict) -> Path:
        """Grava em Quarentena primeiro. Promover é ação separada."""
        root = self.locations.quarantine / cap_id
        if root.exists():
            shutil.rmtree(root)
        payload = root / "payload"
        payload.mkdir(parents=True, exist_ok=True)

        for rel, data in files.items():
            target = payload / rel
            # Defesa em profundidade: o caminho já foi validado, mas
            # nunca escrevemos sem confirmar que o pai resolve sob payload.
            if not str(target.resolve()).startswith(str(payload.resolve())):
                raise ConflictError(
                    f"Destino fora da área autorizada: `{rel}`.",
                    "Importação bloqueada por segurança.")
            atomic_write_bytes(target, data)

        meta = root / ".lia"
        atomic_write_json(meta / "capability.json", metadata)
        atomic_write_json(meta / "provenance.json", provenance)
        atomic_write_json(meta / "history.json", [history_entry])
        return root

    def promote(self, cap_id: str) -> StoredCapability:
        """Move da quarentena para a biblioteca. Falha se já existir."""
        src = self.locations.quarantine / cap_id
        dst = self.locations.library / cap_id
        if not src.is_dir():
            raise NotFound(f"`{cap_id}` não está na quarentena.", "Importe novamente.")
        if dst.exists():
            raise ConflictError(
                f"Já existe uma capacidade com o id `{cap_id}` na biblioteca.",
                "Use 'atualizar' ou escolha outro nome. Nada foi sobrescrito.")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        st = self.load(cap_id)
        st.capability.lifecycle = Lifecycle.ACTIVE
        atomic_write_json(st.meta / "capability.json", st.capability.as_dict())
        return st

    def append_history(self, cap_id: str, entry: dict) -> None:
        st = self.load(cap_id)
        hist = read_json(st.meta / "history.json", default=[]) or []
        hist.append(entry)
        atomic_write_json(st.meta / "history.json", hist)

    def save_validation(self, cap_id: str, report: dict) -> None:
        st = self.load(cap_id)
        atomic_write_json(st.meta / "validation.json", report)

    def read_validation(self, cap_id: str) -> dict | None:
        st = self.load(cap_id)
        return read_json(st.meta / "validation.json")

    def history(self, cap_id: str) -> list[dict]:
        st = self.load(cap_id)
        return read_json(st.meta / "history.json", default=[]) or []

    def delete(self, cap_id: str, *, confirmed: bool = False) -> None:
        """Remoção é irreversível — exige confirmação explícita."""
        if not confirmed:
            raise ConflictError(
                "Remoção não confirmada.", "Marque a confirmação: é irreversível.")
        for base in (self.locations.library, self.locations.quarantine):
            target = base / cap_id
            if target.exists():
                shutil.rmtree(target)
                return
        raise NotFound(f"`{cap_id}` não existe.", "Nada foi removido.")

    # ---- integridade -----------------------------------------------------
    def recompute_hashes(self, cap_id: str) -> dict[str, str]:
        files = self.payload_files(cap_id)
        per_file = {rel: sha256_bytes(data) for rel, data in files.items()}
        combined = tree_hash(per_file)
        primary = files.get("SKILL.md")
        return {
            "contentHash": sha256_bytes(primary) if primary else "",
            "treeHash": combined,
        }

    def find_duplicates(self, cap_id: str) -> list[str]:
        """Mesmo treeHash de outra capacidade. Detecta reimportação disfarçada."""
        st = self.load(cap_id)
        target = st.capability.tree_hash
        if not target:
            return []
        return [
            other.capability.id
            for other in self.list_all()
            if other.capability.id != cap_id and other.capability.tree_hash == target
        ]
