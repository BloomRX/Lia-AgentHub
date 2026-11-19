"""Recebimento de inventários v1 — arquivo, recibos e admissão.

Fronteira desta camada, e ela é rígida: **metadados e referências apenas**.
Nada aqui executa, instala, conecta ou copia payload. O documento chega como
JSON, é validado pelo domínio e, se aprovado, vira recibo em disco e
metadado catalogado. Nem uma linha do inventário é interpretada como comando.

Persistência, em `Locations.common` (compartilhado entre projetos):

    <common>/Inventarios/recibos/<receiptId>.json    recibo imutável
    <common>/Inventarios/recebidos/<inventoryId>.jsonl
                                                     feed por emissor
    <common>/Inventarios/estado.json                 índice de id->revisão
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from ..domain import inventory as dom
from .atomic import atomic_write_json, atomic_write_text, dir_lock, read_json
from .paths_resolver import Locations


#: Estados REAIS do fluxo. Não são etiquetas de UI: `recebido` e `quarentena`
#: gravam em lugares diferentes e têm consequências diferentes. Nenhum deles
#: é `approved`, `configured` ou `operational` — o intake não chega lá.
ESTADO_RECEBIDO = "recebido"
ESTADO_QUARENTENA = "quarentena"
ESTADO_REJEITADO = "rejeitado"

#: Teto do intake, por contrato. Existe para que ninguém leia "recebido" como
#: "aprovado". O Hub só registra que viu; confiança, licença e operação são
#: decisões humanas em outra etapa.
ESTADO_CATALOGADO = "inventoried"


class IntakeError(Exception):
    """Recusa do intake. Mensagem é para o usuário, não para log."""


@dataclass
class Recibo:
    """Prova do que foi recebido, quando e de quem. Imutável por convenção."""

    receipt_id: str
    recebido_em: str
    estado: str
    inventory_id: str
    revision: str
    project: str
    file_digest: str
    file_name: str
    file_bytes: int
    complete: bool
    record_count: int
    admitted: int
    quarantined: int
    inventory_state: str
    achados: list[dict] = field(default_factory=list)
    registros: list[dict] = field(default_factory=list)
    observacao: str = ""

    def as_dict(self) -> dict:
        return {
            "receiptId": self.receipt_id,
            "receivedAt": self.recebido_em,
            "state": self.estado,
            "inventoryState": self.inventory_state,
            "inventoryId": self.inventory_id,
            "revision": self.revision,
            "issuerProject": self.project,
            "fileDigest": self.file_digest,
            "fileName": self.file_name,
            "fileBytes": self.file_bytes,
            "complete": self.complete,
            "recordCount": self.record_count,
            "admitted": self.admitted,
            "quarantined": self.quarantined,
            "findings": self.achados,
            "records": self.registros,
            "note": self.observacao,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Recibo":
        return cls(
            receipt_id=d.get("receiptId", ""), recebido_em=d.get("receivedAt", ""),
            estado=d.get("state", ""), inventory_id=d.get("inventoryId", ""),
            revision=d.get("revision", ""), project=d.get("issuerProject", ""),
            file_digest=d.get("fileDigest", ""), file_name=d.get("fileName", ""),
            file_bytes=int(d.get("fileBytes") or 0), complete=bool(d.get("complete")),
            record_count=int(d.get("recordCount") or 0),
            admitted=int(d.get("admitted") or 0),
            quarantined=int(d.get("quarantined") or 0),
            inventory_state=d.get("inventoryState", ""),
            achados=d.get("findings") or [], registros=d.get("records") or [],
            observacao=d.get("note", ""),
        )


def _agora() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


class InventoryStore:
    """Leitura e gravação dos recibos. Único lugar que monta esses caminhos."""

    def __init__(self, locations: Locations):
        self.locations = locations
        self.root = Path(locations.common) / "Inventarios"
        self.recibos = self.root / "recibos"
        self.recebidos = self.root / "recebidos"
        self.estado_path = self.root / "estado.json"

    def ensure(self) -> None:
        self.recibos.mkdir(parents=True, exist_ok=True)
        self.recebidos.mkdir(parents=True, exist_ok=True)

    # -- estado (id -> revisões conhecidas) -------------------------------
    def estado(self) -> dict:
        """Índice de identidade. `{}` quando ainda não há nada recebido.

        Um índice corrompido é erro explícito, não silêncio: tratar como vazio
        faria o próximo inventário "atualizar" tudo e perder o histórico.
        """
        if not self.estado_path.exists():
            return {}
        dados = read_json(self.estado_path, default=None)
        if not isinstance(dados, dict):
            raise IntakeError(
                f"O índice de identidade em {self.estado_path} está ilegível. "
                "Não vou tratar inventário novo como se nada existisse — "
                "isso apagaria o histórico. Verifique o arquivo.")
        # Campos adicionados pela projeção multi-origem são opcionais para
        # compatibilidade com índices anteriores, mas, quando presentes,
        # precisam manter a forma esperada. Falhar antes de gravar recibos
        # evita uma atualização parcial sobre estado adulterado/corrompido.
        for reg_id, info in dados.items():
            if not isinstance(info, dict):
                raise IntakeError(f"Entrada inválida no índice de identidade: {reg_id}.")
            revisoes = info.get("revisions", {})
            if not isinstance(revisoes, dict):
                raise IntakeError(f"Revisões inválidas no índice de identidade: {reg_id}.")
            projetos = info.get("issuerProjects")
            if projetos is not None and (
                    not isinstance(projetos, list)
                    or any(not isinstance(p, str) for p in projetos)):
                raise IntakeError(f"Origens emissoras inválidas no índice: {reg_id}.")
            for rev_id, revisao in revisoes.items():
                if not isinstance(revisao, dict):
                    raise IntakeError(
                        f"Revisão inválida no índice: {reg_id}/{rev_id}.")
                fontes = revisao.get("sources")
                if fontes is not None and (
                        not isinstance(fontes, list)
                        or any(not isinstance(f, dict) for f in fontes)):
                    raise IntakeError(
                        f"Declarações de origem inválidas: {reg_id}/{rev_id}.")
                for fonte in fontes or []:
                    if (not isinstance(fonte.get("issuer"), dict)
                            or not isinstance(fonte.get("receiptIds"), list)
                            or any(not isinstance(r, str) for r in fonte["receiptIds"])
                            or not isinstance(fonte.get("origins"), list)):
                        raise IntakeError(
                            f"Declaração de origem incompleta: {reg_id}/{rev_id}.")
        return dados

    def conhecidos(self) -> list[dom.Conhecido]:
        out: list[dom.Conhecido] = []
        for reg_id, info in self.estado().items():
            if not isinstance(info, dict):
                continue
            for rev, dados_rev in (info.get("revisions") or {}).items():
                if not isinstance(dados_rev, dict):
                    continue
                out.append(dom.Conhecido(
                    id=reg_id, revision_id=rev,
                    digest=dados_rev.get("digest", ""),
                    name=dados_rev.get("name", ""),
                    kind=dados_rev.get("kind"),
                    version=dados_rev.get("version"),
                    aliases=dados_rev.get("aliases") or [],
                ))
        return out

    def gravar_recibo(self, recibo: Recibo) -> Path:
        self.ensure()
        destino = self.recibos / f"{recibo.receipt_id}.json"
        if destino.exists():
            # Recibo é prova; reescrever apagaria o que foi de fato visto.
            raise IntakeError(f"Recibo {recibo.receipt_id} já existe; não sobrescrevo prova.")
        atomic_write_json(destino, recibo.as_dict())
        return destino

    def gravar_estado(self, estado: dict) -> None:
        self.ensure()
        atomic_write_json(self.estado_path, estado)

    def anexar_feed(self, inventory_id: str, registro: dict) -> None:
        """Acrescenta ao feed do emissor. Append-only, uma linha por revisão."""
        self.ensure()
        seguro = hashlib.sha256(inventory_id.encode("utf-8")).hexdigest()[:32]
        destino = self.recebidos / f"{seguro}.jsonl"
        linha = json.dumps(registro, ensure_ascii=False, sort_keys=True)
        anterior = destino.read_text(encoding="utf-8") if destino.exists() else ""
        atomic_write_text(destino, anterior + linha + "\n")

    def listar_recibos(self, limite: int = 200) -> list[dict]:
        if not self.recibos.exists():
            return []
        arquivos = sorted(self.recibos.glob("*.json"), reverse=True)[:limite]
        out = []
        for caminho in arquivos:
            d = read_json(caminho, default=None)
            if isinstance(d, dict):
                out.append(d)
        return out

    def ler_recibo(self, receipt_id: str) -> dict:
        # `receipt_id` vem do usuário/rota. Só aceitamos o formato que nós
        # mesmos geramos, para que `../` não vire leitura fora do diretório.
        if not receipt_id or not all(
                c.isalnum() or c in "-_" for c in receipt_id):
            raise IntakeError("Identificador de recibo inválido.")
        dados = read_json(self.recibos / f"{receipt_id}.json", default=None)
        if not isinstance(dados, dict):
            raise IntakeError(f"Recibo não encontrado: {receipt_id}")
        return dados


@dataclass
class Plano:
    """Resultado de um intake — em dry-run ou efetivado.

    A mesma estrutura serve aos dois; `efetivado` diz qual dos dois foi. Isso
    é deliberado: se o preview e a gravação tivessem formatos diferentes, o
    usuário confirmaria uma coisa e gravaria outra.
    """

    efetivado: bool
    leitura: dom.Leitura
    nome_arquivo: str
    bytes_lidos: int
    classificados: list[dom.Classificado] = field(default_factory=list)
    estado_proposto: str = ESTADO_REJEITADO
    problema_feed: str = ""
    receipt_id: str = ""
    recibo_path: str = ""
    destino_quarentena: str = ""

    @property
    def ok(self) -> bool:
        return self.leitura.ok and not self.problema_feed

    def as_dict(self) -> dict:
        env = self.leitura.envelope
        contagem: dict[str, int] = {}
        for c in self.classificados:
            contagem[c.classe.value] = contagem.get(c.classe.value, 0) + 1
        return {
            "ok": self.ok,
            "committed": self.efetivado,
            "dryRun": not self.efetivado,
            "state": self.estado_proposto,
            "findings": [a.as_dict() for a in self.leitura.achados],
            "summary": self.leitura.resumo(),
            "envelope": env.as_dict() if env else None,
            "fileName": self.nome_arquivo,
            "fileBytes": self.bytes_lidos,
            "records": [c.as_dict() for c in self.classificados],
            "classifications": contagem,
            "feedProblem": self.problema_feed,
            "receiptId": self.receipt_id,
            "receiptPath": self.recibo_path,
            "quarantinePath": self.destino_quarentena,
            "boundary": {
                "executes": False, "installs": False, "connects": False,
                "copiesPayload": False, "grantsTrust": False,
                "approvesLicense": False, "promotesState": False,
                "maxState": ESTADO_CATALOGADO,
            },
        }


class InventoryIntake:
    """Serviço de recebimento. `ler_arquivo` é a única porta de entrada."""

    def __init__(self, locations: Locations):
        self.locations = locations
        self.store = InventoryStore(locations)

    # -- entrada -----------------------------------------------------------
    def previsualizar(self, caminho: str | Path) -> Plano:
        """Dry-run: valida e classifica, **não grava nada**."""
        return self._processar(caminho, efetivar=False)

    def receber(self, caminho: str | Path) -> Plano:
        """Efetiva o recebimento. Revalida do zero — nunca confia no preview."""
        return self._processar(caminho, efetivar=True)

    # -- núcleo ------------------------------------------------------------
    def _processar(self, caminho: str | Path, *, efetivar: bool) -> Plano:
        caminho = Path(caminho)
        nome = caminho.name
        try:
            dados = caminho.read_bytes()
        except FileNotFoundError:
            return Plano(False, dom.Leitura(False, None, [dom._erro(
                "FILE_NOT_FOUND", f"Arquivo não encontrado: {caminho}", "")]),
                nome, 0)
        except IsADirectoryError:
            return Plano(False, dom.Leitura(False, None, [dom._erro(
                "FILE_IS_DIRECTORY",
                "O caminho é um diretório; o intake recebe um arquivo de inventário.", "")]),
                nome, 0)
        except OSError as e:
            return Plano(False, dom.Leitura(False, None, [dom._erro(
                "FILE_UNREADABLE", f"Não foi possível ler o arquivo: {e}", "")]),
                nome, 0)

        leitura = dom.ler(dados)
        plano = Plano(False, leitura, nome, len(dados))

        if not leitura.ok or leitura.envelope is None:
            # Rejeitado sem gravação. Nem recibo: nada foi admitido, e um
            # recibo de documento rejeitado sugeriria que algo entrou.
            plano.estado_proposto = ESTADO_REJEITADO
            return plano

        env = leitura.envelope
        conhecidos = self.store.conhecidos()
        plano.classificados = dom.classificar(env.registros, conhecidos)

        admitidos = [c for c in plano.classificados if c.admitido]
        bloquearam = [c for c in plano.classificados
                      if c.classe in (
                          dom.Classe.CONFLITO_IDENTIDADE,
                          dom.Classe.ALIAS_CANDIDATO,
                          dom.Classe.DOWNGRADE,
                      )]
        plano.estado_proposto = ESTADO_QUARENTENA if bloquearam else ESTADO_RECEBIDO

        # Feed: mesmo `inventoryId` com `revision` repetida e digest diferente
        # é conflito de FEED — o contrato é explícito. Detectamos antes de gravar.
        plano.problema_feed = self._conflito_de_feed(env)
        if plano.problema_feed:
            plano.estado_proposto = ESTADO_REJEITADO
            return plano

        if not efetivar:
            return plano

        return self._efetivar(plano, env, dados)

    def _conflito_de_feed(self, env: dom.Envelope) -> str:
        """`revision` é único por feed. Mesma revisão, digest diferente: para."""
        seguro = hashlib.sha256(env.inventory_id.encode("utf-8")).hexdigest()[:32]
        feed = self.store.recebidos / f"{seguro}.jsonl"
        if not feed.exists():
            return ""
        for linha in feed.read_text(encoding="utf-8").splitlines():
            if not linha.strip():
                continue
            try:
                anterior = json.loads(linha)
            except json.JSONDecodeError:
                return (f"O feed de {env.inventory_id} tem uma linha ilegível. "
                        "Não gravo por cima de feed corrompido.")
            if anterior.get("revision") == env.revision:
                if anterior.get("fileDigest") == env.file_digest:
                    return ""  # idempotente: mesma revisão, mesmo conteúdo
                return (f"O emissor {env.issuer.get('project')} já publicou a "
                        f"revisão {env.revision!r} de {env.inventory_id} com outro "
                        "conteúdo. Mesma revisão com digest diferente é conflito "
                        "de feed: preciso que o emissor publique uma revisão nova.")
        return ""

    def _efetivar(self, plano: Plano, env: dom.Envelope, dados: bytes) -> Plano:
        self.store.ensure()
        # Trava o índice: duas instâncias do Hub não podem classificar contra
        # o mesmo estado e gravar as duas.
        with dir_lock(self.store.root / ".intake.lock") as travou:
            if not travou:
                raise IntakeError(
                    "Outro recebimento está em andamento (trava de "
                    f"{self.store.root}). Aguarde e tente de novo.")

            # Reclassificar sob a trava: o estado pode ter mudado entre o
            # preview e a confirmação.
            conhecidos = self.store.conhecidos()
            plano.classificados = dom.classificar(env.registros, conhecidos)

            admitidos = [c for c in plano.classificados if c.admitido]
            quarentena = [c for c in plano.classificados if not c.admitido]

            recibo = Recibo(
                receipt_id=f"rec-{secrets.token_hex(8)}",
                recebido_em=_agora(),
                estado=plano.estado_proposto,
                inventory_id=env.inventory_id,
                revision=env.revision,
                project=str(env.issuer.get("project") or ""),
                file_digest=env.file_digest,
                file_name=plano.nome_arquivo,
                file_bytes=len(dados),
                complete=env.complete,
                record_count=len(env.registros),
                admitted=len(admitidos),
                quarantined=len(quarentena),
                inventory_state=ESTADO_CATALOGADO,
                achados=[a.as_dict() for a in plano.leitura.achados],
                registros=[c.as_dict() for c in plano.classificados],
                observacao=(
                    "Recebimento de METADADOS. Nada foi executado, instalado ou "
                    "conectado. `inventoried` é o teto: confiança, licença e "
                    "operação continuam pendentes de decisão humana."),
            )

            # Recibo primeiro: se o índice falhar depois, existe prova de que
            # o documento chegou e de como foi classificado.
            destino = self.store.gravar_recibo(recibo)
            plano.receipt_id = recibo.receipt_id
            plano.recibo_path = str(destino)

            if quarentena:
                plano.destino_quarentena = str(self._gravar_quarentena(recibo, quarentena))

            self._atualizar_estado(env, admitidos, recibo.receipt_id)
            self.store.anexar_feed(env.inventory_id, {
                "revision": env.revision,
                "fileDigest": env.file_digest,
                "receivedAt": recibo.recebido_em,
                "receiptId": recibo.receipt_id,
                "recordCount": len(env.registros),
                "admitted": len(admitidos),
                "quarantined": len(quarentena),
            })
            plano.efetivado = True
        return plano

    def _gravar_quarentena(self, recibo: Recibo, itens: list[dom.Classificado]) -> Path:
        """Quarentena é diretório separado com metadados — não um rótulo.

        O que entra aqui NÃO foi admitido no acervo: conflito de identidade e
        downgrade ficam retidos até decisão humana. O conteúdo só é referenciado
        por digest; o payload não é copiado.
        """
        pasta = Path(self.locations.quarantine) / "Inventarios" / recibo.receipt_id
        pasta.mkdir(parents=True, exist_ok=True)
        atomic_write_json(pasta / "retencao.json", {
            "receiptId": recibo.receipt_id,
            "receivedAt": recibo.recebido_em,
            "inventoryId": recibo.inventory_id,
            "revision": recibo.revision,
            "reason": "Conflito de identidade ou downgrade: retido até decisão humana.",
            "records": [c.as_dict() for c in itens],
            "note": ("Metadados retidos. Nenhum arquivo do emissor foi copiado, "
                     "executado ou instalado."),
        })
        return pasta

    def _atualizar_estado(self, env: dom.Envelope,
                          admitidos: list[dom.Classificado],
                          receipt_id: str) -> None:
        """Atualiza a projeção sem descartar declarações de outras origens.

        O índice é uma projeção reconstruível; recibos continuam sendo a prova
        imutável. Uma mesma identidade/revisão pode ser declarada por feeds
        diferentes. Nesse caso, preservamos cada alegação de origem em
        `sources`, sem eleger uma origem canônica nem fundir licenças.
        """
        estado = self.store.estado()
        agora = _agora()

        for c in admitidos:
            reg = c.registro
            entrada = estado.setdefault(reg.id, {"revisions": {}})
            revisoes = entrada.setdefault("revisions", {})
            revisao = revisoes.get(reg.revision_id)

            if revisao is None:
                revisao = {
                    "digest": reg.digest,
                    "name": reg.name,
                    "kind": reg.kind,
                    "version": reg.version,
                    "receiptId": receipt_id,
                    "receivedAt": agora,
                    "state": ESTADO_CATALOGADO,
                    "sources": [],
                }
                revisoes[reg.revision_id] = revisao

            # A classificação já impede admitir o mesmo id/revisão com outro
            # digest. Esta guarda evita corromper a projeção se o estado tiver
            # sido alterado fora do fluxo esperado.
            elif revisao.get("digest") != reg.digest:
                raise IntakeError(
                    f"Conflito de digest para {reg.id} / {reg.revision_id}; "
                    "a projeção existente foi preservada.")

            # Relações e aliases permanecem declarações do emissor. Não são
            # resolvidos, instalados nem convertidos em autorização pelo Hub.
            for campo in ("aliases", "dependencies", "offers", "compatibility"):
                revisao[campo] = reg.bruto.get(campo, [])

            sources = revisao.setdefault("sources", [])
            issuer = {
                "project": env.issuer.get("project"),
                "repository": env.issuer.get("repository"),
                "maintainer": env.issuer.get("maintainer"),
            }
            claim_key = (
                env.inventory_id, env.revision, issuer["project"],
                reg.revision_id, reg.digest,
            )
            claim = next((
                item for item in sources
                if (
                    item.get("inventoryId"),
                    item.get("inventoryRevision"),
                    (item.get("issuer") or {}).get("project"),
                    item.get("recordRevisionId"),
                    item.get("recordDigest"),
                ) == claim_key
            ), None)

            if claim is None:
                claim = {
                    "inventoryId": env.inventory_id,
                    "inventoryRevision": env.revision,
                    "issuer": issuer,
                    "recordRevisionId": reg.revision_id,
                    "recordDigest": reg.digest,
                    "receivedAt": agora,
                    "receiptIds": [],
                    "origins": reg.bruto.get("origins", []),
                }
                sources.append(claim)

            # Reenvio idempotente mantém uma única alegação de origem, mas
            # todos os recibos continuam rastreáveis.
            recibos = claim.setdefault("receiptIds", [])
            if receipt_id not in recibos:
                recibos.append(receipt_id)

            entrada["lastRevision"] = reg.revision_id
            entrada["name"] = reg.name
            entrada["kind"] = reg.kind
            entrada["issuerProject"] = env.issuer.get("project")
            projetos = entrada.setdefault("issuerProjects", [])
            if issuer["project"] and issuer["project"] not in projetos:
                projetos.append(issuer["project"])

        self.store.gravar_estado(estado)
