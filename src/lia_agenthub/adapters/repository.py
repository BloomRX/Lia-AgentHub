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
from datetime import datetime, timezone
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
        #: Registros que existem no disco mas não puderam ser lidos. Preenchido
        #: a cada varredura; nunca é limpo automaticamente para não mascarar
        #: uma falha antiga. Quem chama `list_all()`/`list_quarantine()` deve
        #: olhar aqui antes de afirmar que a biblioteca está vazia.
        self.erros_de_leitura: list[dict] = []

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

    def _ler_entradas(self, base: Path) -> list[StoredCapability]:
        """Varre um diretório e devolve o que conseguir ler.

        Regra: um registro ilegível não pode derrubar a lista inteira, mas
        também não pode desaparecer em silêncio. Antes, `except (KeyError,
        ValueError)` engolia o item e o usuário via a biblioteca "menor" sem
        saber por quê — e um `TypeError` (campo desconhecido em `Source`)
        escapava do filtro e derrubava tudo.

        Agora cada falha é registrada em `self.erros_de_leitura`, com o id da
        pasta e o motivo. Quem chama decide o que fazer: a UI mostra, o
        diagnóstico lista, os testes verificam.
        """
        out: list[StoredCapability] = []
        # R-1.3: limpa ANTES de varrer, senão o erro de uma chamada anterior
        # fica misturado com os desta — e o chamador não consegue saber o que
        # é atual. O atributo é por varredura, não acumulativo.
        self.erros_de_leitura = []
        if not base.is_dir():
            return out
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue
            data = read_json(entry / ".lia" / "capability.json")
            if data is None:
                # Sem metadata legível não há capacidade. Ainda assim registra:
                # uma pasta com payload e sem registro é sinal de dado perdido.
                self.erros_de_leitura.append({
                    "id": entry.name, "pasta": str(entry),
                    "motivo": "capability.json ausente ou ilegível (JSON inválido)"})
                continue
            try:
                out.append(StoredCapability(Capability.from_dict(data), entry))
            except Exception as e:  # noqa: BLE001 — fronteira de leitura de disco
                # Amplo de propósito: qualquer falha ao interpretar um registro
                # de terceiro/antigo é isolada no item, nunca na biblioteca.
                # Não é `pass`: o erro fica registrado e é devolvido a quem lê.
                self.erros_de_leitura.append({
                    "id": entry.name, "pasta": str(entry),
                    "motivo": f"{type(e).__name__}: {e}"})
        return out

    def list_all(self) -> list[StoredCapability]:
        """Varre o disco. Não confia no índice — ele é conveniência."""
        return self._ler_entradas(self.locations.library)

    def list_quarantine(self) -> list[StoredCapability]:
        """Varre a quarentena. Mesma regra: o disco é a verdade."""
        return self._ler_entradas(self.locations.quarantine)

    def payload_files(self, cap_id: str) -> dict[str, bytes]:
        """Lê o payload de onde a capacidade estiver: biblioteca ou quarentena.

        Validação e detalhe acontecem ANTES da promoção, então procurar só na
        biblioteca faria a quarentena parecer vazia.
        """
        st = self._load_any(cap_id)
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

    def supersede(self, old_id: str, new_id: str) -> None:
        """Substitui `old_id` por `new_id` preservando o anterior no disco.

        A versão antiga NÃO é apagada: vira `superseded` e continua consultável.
        Atualização silenciosa que perde a anterior é exatamente o que este
        método existe para impedir.
        """
        old = self._load_any(old_id)
        if (self.locations.library / old_id).exists():
            old.capability.lifecycle = Lifecycle.SUPERSEDED
            atomic_write_json(old.meta / "capability.json", old.capability.as_dict())
            self.append_history(old_id, {
                "action": "superseded-by", "by": new_id,
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
        # O novo passa a apontar para o antigo: a linhagem fica explícita.
        new = self._load_any(new_id)
        new.capability.version_of = old_id
        atomic_write_json(new.meta / "capability.json", new.capability.as_dict())
        self.append_history(new_id, {
            "action": "supersedes", "previous": old_id,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        })

    def versions_of(self, cap_id: str) -> list[dict]:
        """Linhagem: percute `version_of` para trás e devolve todas as versões."""
        cadeia, vistos, atual = [], set(), None
        try:
            atual = self._load_any(cap_id).capability
        except NotFound:
            return []
        while atual is not None and atual.id not in vistos:
            vistos.add(atual.id)
            cadeia.append({
                "id": atual.id, "name": atual.name, "version": atual.version,
                "lifecycle": atual.lifecycle.value, "treeHash": atual.tree_hash,
                "importedAt": atual.source.imported_at,
            })
            anterior = atual.version_of
            if not anterior:
                break
            try:
                atual = self._load_any(anterior).capability
            except NotFound:
                break
        return cadeia

    def append_history(self, cap_id: str, entry: dict) -> None:
        st = self._load_any(cap_id)
        hist = read_json(st.meta / "history.json", default=[]) or []
        hist.append(entry)
        atomic_write_json(st.meta / "history.json", hist)

    def save_validation(self, cap_id: str, report: dict) -> None:
        st = self._load_any(cap_id)
        atomic_write_json(st.meta / "validation.json", report)

    def read_validation(self, cap_id: str) -> dict | None:
        st = self._load_any(cap_id)
        return read_json(st.meta / "validation.json")

    def history(self, cap_id: str) -> list[dict]:
        st = self._load_any(cap_id)
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

    def _load_any(self, cap_id: str) -> StoredCapability:
        """Carrega de onde estiver. Duplicata importa ANTES de promover."""
        for base in (self.locations.library, self.locations.quarantine):
            data = read_json(base / cap_id / ".lia" / "capability.json")
            if data is not None:
                return StoredCapability(Capability.from_dict(data), base / cap_id)
        raise NotFound(
            f"Capacidade `{cap_id}` não encontrada.",
            "Ela pode ter sido removida. Recarregue a lista.")

    def find_duplicates(self, cap_id: str) -> list[str]:
        """Mesmo treeHash de outra capacidade, na biblioteca ou na quarentena.

        Detecta reimportação disfarçada e avisa antes de o usuário promover
        algo que já tem.
        """
        target = self._load_any(cap_id).capability.tree_hash
        if not target:
            return []
        # Só IDs diferentes contam como duplicata: mesmo ID é a MESMA capacidade,
        # e o importador já reporta isso como `alreadyPresent`.
        others = self.list_all() + self.list_quarantine()
        return sorted({
            other.capability.id
            for other in others
            if other.capability.id != cap_id and other.capability.tree_hash == target
        })
