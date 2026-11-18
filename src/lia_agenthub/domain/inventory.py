"""Inventário de capacidades v1 — leitura, validação e classificação.

Este módulo é **domínio puro**: não lê arquivo, não grava, não abre socket.
Ele recebe texto e devolve um resultado. Quem lê arquivo é o adaptador; quem
grava é o repositório.

O contrato está em `docs/architecture/CAPABILITY-INVENTORY-CONTRACT.md`.
Regras que o código implementa literalmente e que não podem ser afrouxadas:

  - `inventoryVersion` desconhecida é **rejeitada sem gravação**.
  - O mesmo `revision` com digest diferente é **conflito**, não atualização.
  - Omissão (`complete: false`) **nunca apaga** registro.
  - Campo desconhecido é **preservado** e não tem efeito na admissão.
  - Nada aqui promove estado: `inventoried` é o teto do intake.
  - Hash não prova autoria; licença declarada não é permissão.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

#: Versão de intercâmbio que este leitor entende. Uma versão nova exige leitor
#: novo — ignorar o campo seria aceitar contrato que não sei ler.
INVENTORY_VERSION = 1

#: Limites aplicados ANTES de processar o documento (contrato, §Envelope).
#: Sem eles, um inventário de 2 GB ou com 10 milhões de registros derruba o
#: processo antes de qualquer validação útil.
MAX_BYTES = 8 * 1024 * 1024
MAX_RECORDS = 5000
MAX_EVIDENCE = 20000
MAX_REFERENCIAS_POR_REGISTRO = 2000

#: Projetos emissores aceitos. `lia-model-lab` é aceito para preservar a
#: referência histórica — está suspenso, mas o contrato o lista e inventários
#: antigos precisam continuar legíveis.
PROJETOS_CONHECIDOS = (
    "lia-project", "lia-forge", "lia-studio", "lia-model-lab", "lia-agent-hub",
)

#: Projetos que NÃO são fonte ativa nesta fase. Receber é permitido (preserva
#: histórico); o relatório marca como inativo para que ninguém conte com ele.
PROJETOS_INATIVOS = ("lia-model-lab",)

#: `kind` controlado pelo contrato.
KINDS = (
    "agent-skill", "mcp-server", "mcp-tool", "cli", "plugin", "package",
    "agent-profile", "model-provider", "workflow", "resource",
)

#: Tipos v1 legados que NÃO têm `kind` direto. O contrato manda manter o tipo
#: legado como alias de classificação e não inventar `kind`.
KIND_LEGADO = {
    "cli-tool": "cli",
    "provider-model": "model-provider",
}

#: Tipos legados sem correspondência: ficam na fila de recebimento com tipo
#: pendente e FORA dos registros normalizados (contrato §Compatibilidade v1).
KIND_PENDENTE = ("api-service", "framework", "template", "reference", "unknown")

#: Estados de projeção do contrato. O intake só alcança `inventoried`.
ESTADOS = (
    "inventoried", "cataloged", "imported", "validated",
    "approved-for-distribution", "available-for-configuration",
    "configured", "operational", "blocked",
)

#: Estados que exigem evidência de host ou decisão humana. O intake jamais os
#: atribui — nem por presença de campo, nem por otimismo.
ESTADOS_NAO_ALCANCAVEIS_PELO_INTAKE = ESTADOS[2:]

REDISTRIBUICAO = ("unknown", "pending", "allowed", "denied")
COMPATIBILIDADE = ("unknown", "declared", "contract-checked", "host-verified",
                   "incompatible")

#: `urn:lia:cap:<uuid>` ou identificador externo preservado. O contrato exige
#: que o ID central NÃO seja derivado de nome, local, versão ou hash.
#: Campos que o contrato define num registro. Qualquer outro é preservado em
#: `desconhecidos` sem efeito na admissão (contrato, §Envelope).
_CAMPOS_REGISTRO = frozenset({
    "id", "revisionId", "version", "kind", "name", "description", "origins",
    "aliases", "license", "integrity", "dependencies", "environment", "offers",
    "compatibility", "details", "observations", "history",
})

_ID_URN = re.compile(r"^urn:lia:cap:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                     r"[0-9a-f]{4}-[0-9a-f]{12}$")
#: Prefixo reservado do contrato. Se começa assim, TEM de ser UUID: senão
#: `urn:lia:cap:nao-e-uuid` passaria como "URN genérica" e viraria identidade.
_ID_PREFIXO_CONTRATO = "urn:lia:cap:"

#: Identificador com escopo declarado (`urn:`, `projeto:`, etc.), para IDs
#: reservados por origem autorizada. URL com `://` NÃO serve: o contrato exige
#: identidade estável, e endereço muda. `_ID_URN` é verificado primeiro.
_ID_EXTERNO = re.compile(r"^[a-z][a-z0-9+.-]*:(?!//)[^\s]+$", re.IGNORECASE)
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(\.\d+)?([Zz]|[+-]\d{2}:\d{2})$")

#: Padrões de credencial. A varredura é a mesma doutrina do descritor MCP:
#: segredo não entra, nem em campo que "parece" metadado.
_PADROES_SEGREDO = (
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"ya29\.[0-9A-Za-z_\-]{10,}"),
    re.compile(r"\bghp_[0-9A-Za-z]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"eyJhbGciOi[A-Za-z0-9_\-]{10,}"),
    # Chave privada colada num campo que devia ser metadado.
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    # Credencial AWS em texto.
    re.compile(r"\baws_secret_access_key\s*[=:]\s*[A-Za-z0-9/+=]{8,}", re.IGNORECASE),
    # Cabeçalho de autorização copiado junto com a configuração.
    re.compile(r"\bauthorization\s*[:=]\s*bearer\s+\S{10,}", re.IGNORECASE),
    # userinfo em URL: https://user:senha@host
    re.compile(r"^[a-z][a-z0-9+.-]*://[^/\s@]+:[^/\s@]+@", re.IGNORECASE),
)

#: Nomes de chave que, com valor preenchido, caracterizam CÓPIA DE CONFIG
#: PRIVADA — o contrato manda recusar. Olhar só o valor não pega
#: `{"MEU_TOKEN": "abc123"}`; olhar só o valor também não pega um `.env` que
#: já tenha sido colado. As duas varreduras juntas cobrem os dois casos.
_PADROES_CHAVE_SEGREDO = re.compile(
    r"(^|[_.-])(token|secret|senha|password|passwd|apikey|api_key|access_?key|"
    r"private_?key|credential|credentials|auth|authorization|bearer|"
    r"client_?secret|session_?id)([_.-]|$)", re.IGNORECASE)

#: Valores que NÃO são segredo mesmo com chave suspeita: referência a cofre,
#: placeholder explícito, vazio. Recusar esses tornaria o intake inútil.
_VALOR_REFERENCIA = re.compile(
    r"^(vault://|secret://|env:|\$\{|<|\{\{|\*\*\*|redacted|placeholder|"
    r"changeme|example)", re.IGNORECASE)


class Severidade(str, Enum):
    """Mesma escala do validador de Skill, para não haver dois vocabulários."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    REVIEW = "review"


@dataclass
class Achado:
    """Um problema localizado. `where` aponta ao registro e ao campo."""

    severity: Severidade
    code: str
    message: str
    where: str = ""
    hint: str = ""

    def as_dict(self) -> dict:
        return {"severity": self.severity.value, "code": self.code,
                "message": self.message, "where": self.where,
                "hint": self.hint}


def _erro(code, msg, where="", hint=""):
    return Achado(Severidade.ERROR, code, msg, where, hint)


def _aviso(code, msg, where="", hint=""):
    return Achado(Severidade.WARNING, code, msg, where, hint)


def _revisao(code, msg, where="", hint=""):
    return Achado(Severidade.REVIEW, code, msg, where, hint)


# ---------------------------------------------------------------------------
# Classificação de duplicatas e conflitos
# ---------------------------------------------------------------------------
class Classe(str, Enum):
    """O que fazer com um registro recebido, comparado ao que já existe.

    A ordem importa: conflito de identidade vence atualização, porque
    sobrescrever uma revisão disputada perde o relato do outro lado.
    """

    NOVO = "new"
    #: Mesma identidade, mesma revisão, mesmo digest: recepção idempotente.
    DUPLICATA_EXATA = "exact-duplicate"
    #: Mesmo id + revisão, digest diferente: bloqueia, preserva os dois.
    CONFLITO_IDENTIDADE = "identity-conflict"
    #: Mesmo id, revisão diferente: atualização, preservando a anterior.
    ATUALIZACAO = "update"
    #: Revisão mais antiga que a já registrada: downgrade exige escolha.
    DOWNGRADE = "downgrade"
    #: Mesmo conteúdo (hash) em id diferente: candidato a conteúdo idêntico.
    MESMO_CONTEUDO = "same-content"
    #: Mesmo nome, conteúdo diferente: sobreposição — registros separados.
    SOBREPOSICAO = "overlap"
    #: Tipo sem `kind` no contrato: fica na fila, não é normalizado.
    TIPO_PENDENTE = "pending-type"


@dataclass
class Registro:
    """Registro recebido, normalizado e sanitizado."""

    id: str
    revision_id: str
    kind: str | None
    name: str
    description: str | None
    version: str | None
    #: Campos do contrato preservados. `None` é desconhecido; `[]` é vazio.
    bruto: dict = field(default_factory=dict)
    #: Digest canônico do registro — identifica a revisão por conteúdo.
    digest: str = ""
    #: Tipo legado preservado como alias quando não há `kind` no contrato.
    tipo_legado: str | None = None
    #: Campos que não existem no contrato, preservados sem efeito na admissão.
    desconhecidos: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "revisionId": self.revision_id, "kind": self.kind,
            "legacyType": self.tipo_legado, "name": self.name,
            "description": self.description, "version": self.version,
            "digest": self.digest, "record": self.bruto,
            "unknownFields": self.desconhecidos,
        }


@dataclass
class Envelope:
    """Envelope validado."""

    inventory_version: int
    inventory_id: str
    revision: str
    generated_at: str
    issuer: dict
    complete: bool
    file_digest: str
    registros: list[Registro] = field(default_factory=list)
    evidencia: list[dict] = field(default_factory=list)
    desconhecidos: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "inventoryVersion": self.inventory_version,
            "inventoryId": self.inventory_id,
            "revision": self.revision,
            "generatedAt": self.generated_at,
            "issuer": self.issuer,
            "complete": self.complete,
            "fileDigest": self.file_digest,
            "recordCount": len(self.registros),
            "evidenceCount": len(self.evidencia),
            "unknownFields": self.desconhecidos,
        }


@dataclass
class Leitura:
    """Resultado de ler um inventário. Nunca levanta exceção por conteúdo."""

    ok: bool
    envelope: Envelope | None = None
    achados: list[Achado] = field(default_factory=list)

    @property
    def erros(self) -> list[Achado]:
        return [a for a in self.achados if a.severity is Severidade.ERROR]

    def resumo(self) -> dict:
        contagem = {s.value: 0 for s in Severidade}
        for a in self.achados:
            contagem[a.severity.value] += 1
        return contagem


# ---------------------------------------------------------------------------
# Leitura do documento
# ---------------------------------------------------------------------------
def _rejeitar_chaves_duplicadas(pares):
    """`object_pairs_hook` que recusa chave repetida no mesmo objeto.

    `json.loads` padrão mantém a última e descarta a primeira em silêncio.
    Num inventário, `"revision": "a", "revision": "b"` é ou erro de geração ou
    tentativa de confundir o leitor. Nenhum dos dois deve passar.
    """
    vistos: set[str] = set()
    for chave, _ in pares:
        if chave in vistos:
            raise ValueError(f"chave JSON duplicada no mesmo objeto: {chave!r}")
        vistos.add(chave)
    return dict(pares)


def _recusar_constante(nome: str):
    """`NaN`/`Infinity` não são JSON. `json.loads` os aceita por padrão."""
    raise ValueError(f"constante JSON inválida: {nome}. O documento precisa ser JSON estrito.")


def _texto_nao_vazio(valor: Any) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _digest_canonico(obj: Any) -> str:
    """SHA-256 do JSON canônico. Compara CONTEÚDO, não formatação.

    Sem `sort_keys` e sem separador fixo, reordenar chaves produziria digest
    diferente para o mesmo dado e o conflito seria falso.
    """
    canonico = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonico).hexdigest()


def hash_arquivo(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def _achar_segredo(valor: Any, caminho: str = "") -> list[str]:
    """Varre recursivamente. Devolve caminhos que contêm credencial."""
    achados: list[str] = []
    if isinstance(valor, str):
        for padrao in _PADROES_SEGREDO:
            if padrao.search(valor):
                achados.append(caminho or "(raiz)")
                break
    elif isinstance(valor, dict):
        for k, v in valor.items():
            onde = f"{caminho}.{k}" if caminho else k
            if (_PADROES_CHAVE_SEGREDO.search(str(k))
                    and isinstance(v, str) and len(v.strip()) >= 8
                    and not _VALOR_REFERENCIA.match(v.strip())):
                achados.append(onde)
            achados.extend(_achar_segredo(v, onde))
    elif isinstance(valor, list):
        for i, v in enumerate(valor):
            achados.extend(_achar_segredo(v, f"{caminho}[{i}]"))
    return achados


def _validar_origem(origem: Any, onde: str, ev_ids: set[str]) -> list[Achado]:
    """`origins[]`: lista não vazia, caminho relativo POSIX, URL sanitizada."""
    out: list[Achado] = []
    if not isinstance(origem, dict):
        return [_erro("ORIGIN_NOT_OBJECT", "origem deve ser um objeto.", onde)]
    repo = origem.get("repository")
    if repo is not None and not isinstance(repo, str):
        out.append(_erro("ORIGIN_BAD_REPOSITORY", "`repository` deve ser texto ou null.", onde))
    caminho = origem.get("path")
    if caminho is not None:
        if not isinstance(caminho, str):
            out.append(_erro("ORIGIN_BAD_PATH", "`path` deve ser texto ou null.", onde))
        elif caminho.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", caminho):
            # O contrato exige caminho RELATIVO verificável. Um caminho
            # absoluto v1 é referência local do emissor, nunca origem a
            # publicar — publicá-lo vazaria a árvore de diretórios dele.
            out.append(_erro(
                "ORIGIN_ABSOLUTE_PATH",
                f"`path` deve ser relativo POSIX; recebido absoluto: {caminho!r}.",
                onde, "Publique o caminho dentro do repositório, não o caminho local."))
        elif ".." in caminho.split("/"):
            out.append(_erro("ORIGIN_PATH_TRAVERSAL",
                             f"`path` contém `..`: {caminho!r}.", onde))
    commit = origem.get("commit")
    if commit is not None:
        if not isinstance(commit, str):
            out.append(_erro("ORIGIN_BAD_COMMIT", "`commit` deve ser texto ou null.", onde))
        elif commit and not re.fullmatch(r"[0-9a-f]{7,64}", commit):
            out.append(_aviso("ORIGIN_SHORT_COMMIT",
                              f"`commit` não parece SHA de git: {commit!r}.", onde,
                              "O contrato pede commit completo quando conhecido."))
    # `origins[].evidenceIds` é referência como qualquer outra. Antes desta
    # correção só `integrity` e `compatibility` eram verificados, então uma
    # origem apontando para evidência inexistente passava em silêncio — e a
    # proveniência ficava "documentada" por um ID que não existe.
    for ev in origem.get("evidenceIds") or []:
        if ev not in ev_ids:
            out.append(_erro("EVIDENCE_UNRESOLVED",
                             f"`evidenceIds` referencia `{ev}`, ausente do envelope.",
                             onde))
    return out


def _validar_integridade(item: Any, onde: str, ev_ids: set[str]) -> list[Achado]:
    out: list[Achado] = []
    if not isinstance(item, dict):
        return [_erro("INTEGRITY_NOT_OBJECT", "item de `integrity` deve ser objeto.", onde)]
    alg = item.get("algorithm")
    digest = item.get("digest")
    if alg == "sha256":
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            out.append(_erro(
                "INTEGRITY_BAD_SHA256",
                "digest SHA-256 deve ter 64 caracteres hexadecimais minúsculos.",
                onde, f"Recebido: {digest!r}."))
    if not _texto_nao_vazio(alg):
        out.append(_aviso("INTEGRITY_NO_ALGORITHM",
                          "item de `integrity` sem `algorithm`.", onde))
    for ev in item.get("evidenceIds") or []:
        if ev not in ev_ids:
            out.append(_erro("EVIDENCE_UNRESOLVED",
                             f"`evidenceIds` referencia `{ev}`, ausente do envelope.",
                             onde))
    return out


def _validar_registro(bruto: Any, onde: str, ev_ids: set[str],
                      ) -> tuple[Registro | None, list[Achado]]:
    """Valida um registro. Devolve `(normalizado, achados)`.

    Devolve `None` quando falta campo obrigatório: sem id, revisão ou `kind`
    o registro não é identificável, e inventar identidade seria pior que
    recusar.
    """
    out: list[Achado] = []
    if not isinstance(bruto, dict):
        return None, [_erro("RECORD_NOT_OBJECT", "registro deve ser objeto JSON.", onde)]

    desconhecidos = {k: v for k, v in bruto.items()
                     if k not in _CAMPOS_REGISTRO}

    reg_id = bruto.get("id")
    revisao = bruto.get("revisionId")
    if not _texto_nao_vazio(reg_id):
        out.append(_erro("RECORD_MISSING_ID", "`id` é obrigatório e não vazio.", onde))
    elif reg_id.startswith(_ID_PREFIXO_CONTRATO) and not _ID_URN.match(reg_id):
        out.append(_erro(
            "RECORD_BAD_ID",
            f"`id` com prefixo do contrato precisa ser `urn:lia:cap:<uuid>`: {reg_id!r}.",
            onde, "Prefixo reservado com valor não-UUID confundiria a identidade."))
    elif not (_ID_URN.match(reg_id) or _ID_EXTERNO.match(reg_id)):
        out.append(_erro(
            "RECORD_BAD_ID",
            f"`id` deve ser `urn:lia:cap:<uuid>` ou identificador com escopo: {reg_id!r}.",
            onde, "O contrato proíbe derivar o ID de nome, local, versão ou hash."))
    if not _texto_nao_vazio(revisao):
        out.append(_erro("RECORD_MISSING_REVISION",
                         "`revisionId` é obrigatório e não vazio.", onde))

    kind = bruto.get("kind")
    tipo_legado = None
    if not _texto_nao_vazio(kind):
        out.append(_erro("RECORD_MISSING_KIND", "`kind` é obrigatório.", onde))
    elif kind in KIND_LEGADO:
        tipo_legado = kind
        kind = KIND_LEGADO[kind]
        out.append(_aviso(
            "KIND_MAPPED_FROM_V1",
            f"`kind` {tipo_legado!r} é tipo v1; mapeado para {kind!r}. "
            "O valor original fica como alias de classificação.",
            onde))
    elif kind in KIND_PENDENTE:
        tipo_legado = kind
        kind = None
        out.append(_revisao(
            "KIND_PENDING",
            f"`kind` {tipo_legado!r} não tem correspondência no contrato. "
            "Registro fica na fila de recebimento com tipo pendente.",
            onde, "O contrato manda manter fora dos registros normalizados."))
    elif kind not in KINDS:
        out.append(_erro("RECORD_UNKNOWN_KIND",
                         f"`kind` desconhecido: {kind!r}.", onde,
                         f"Aceitos: {', '.join(KINDS)}."))
        kind = None

    nome = bruto.get("name")
    if not _texto_nao_vazio(nome):
        out.append(_erro("RECORD_MISSING_NAME", "`name` é obrigatório e não vazio.", onde))

    origens = bruto.get("origins")
    if not isinstance(origens, list) or not origens:
        out.append(_erro("RECORD_MISSING_ORIGINS",
                         "`origins` é obrigatório e deve ser lista não vazia.", onde))
    else:
        for i, o in enumerate(origens):
            out.extend(_validar_origem(o, f"{onde}.origins[{i}]", ev_ids))

    if len(origens or []) > MAX_REFERENCIAS_POR_REGISTRO:
        out.append(_erro("RECORD_TOO_MANY_ORIGINS",
                         f"{len(origens)} origens; limite {MAX_REFERENCIAS_POR_REGISTRO}.", onde))

    lic = bruto.get("license")
    if lic is not None:
        if not isinstance(lic, dict):
            out.append(_erro("LICENSE_NOT_OBJECT", "`license` deve ser objeto ou null.", onde))
        else:
            red = lic.get("redistribution")
            if isinstance(red, dict):
                status = red.get("status")
                if status is not None and status not in REDISTRIBUICAO:
                    out.append(_erro(
                        "LICENSE_BAD_REDISTRIBUTION",
                        f"`license.redistribution.status` inválido: {status!r}.", onde,
                        f"Aceitos: {', '.join(REDISTRIBUICAO)}."))
                if status == "allowed" and not (red.get("authorizationIds") or []):
                    # `allowed` sem autorização é exatamente a promoção
                    # automática que o contrato proíbe.
                    out.append(_erro(
                        "LICENSE_ALLOWED_WITHOUT_AUTHORIZATION",
                        "`redistribution.status: allowed` sem `authorizationIds`.", onde,
                        "`allowed` exige autorização comprovada e vinculada a "
                        "versão, hash, escopo e canal."))
                for a in red.get("authorizationIds") or []:
                    if a not in ev_ids:
                        out.append(_erro(
                            "LICENSE_UNRESOLVED_AUTHORIZATION",
                            f"`authorizationIds` referencia `{a}`, ausente do envelope.",
                            onde))

    for i, item in enumerate(bruto.get("integrity") or []):
        out.extend(_validar_integridade(item, f"{onde}.integrity[{i}]", ev_ids))

    for i, comp in enumerate(bruto.get("compatibility") or []):
        if isinstance(comp, dict):
            res = comp.get("result")
            if res is not None and res not in COMPATIBILIDADE:
                out.append(_erro("COMPATIBILITY_BAD_RESULT",
                                 f"`compatibility[{i}].result` inválido: {res!r}.",
                                 onde, f"Aceitos: {', '.join(COMPATIBILIDADE)}."))
            for ev in comp.get("evidenceIds") or []:
                if ev not in ev_ids:
                    out.append(_erro("EVIDENCE_UNRESOLVED",
                                     f"`evidenceIds` referencia `{ev}`, ausente do envelope.",
                                     f"{onde}.compatibility[{i}]"))

    if any(a.severity is Severidade.ERROR for a in out):
        return None, out

    return Registro(
        id=reg_id,
        revision_id=revisao,
        kind=kind,
        name=nome,
        description=bruto.get("description"),
        version=bruto.get("version"),
        # Cópia PROFUNDA: `Registro.bruto` precisa continuar válido mesmo se
        # quem chamou mexer no dict original depois.
        bruto=json.loads(json.dumps(bruto, ensure_ascii=False)),
        digest=_digest_canonico(bruto),
        tipo_legado=tipo_legado,
        desconhecidos=desconhecidos,
    ), out




def _validar_data(valor: Any, onde: str) -> list[Achado]:
    if not isinstance(valor, str) or not _RFC3339.match(valor):
        return [_erro("ENVELOPE_BAD_TIMESTAMP",
                      f"`generatedAt` deve ser RFC 3339 com fuso: {valor!r}.", onde)]
    try:
        datetime.fromisoformat(valor.replace("Z", "+00:00").replace("z", "+00:00"))
    except ValueError:
        return [_erro("ENVELOPE_BAD_TIMESTAMP",
                      f"`generatedAt` não é data válida: {valor!r}.", onde)]
    return []


def ler(dados: bytes) -> Leitura:
    """Lê e valida um inventário v1. **Nunca** levanta por conteúdo ruim.

    Retorna `Leitura(ok=False)` com achados localizados. Sem `ok`, o Chamador
    não deve gravar nada — é a regra "rejeitada sem gravação" do contrato.
    """
    achados: list[Achado] = []

    if len(dados) > MAX_BYTES:
        return Leitura(False, None, [_erro(
            "ENVELOPE_TOO_LARGE",
            f"arquivo tem {len(dados)} bytes; limite {MAX_BYTES}.",
            hint="Divida o inventário por projeto ou por revisão.")])

    try:
        texto = dados.decode("utf-8")
    except UnicodeDecodeError as e:
        return Leitura(False, None, [_erro(
            "ENVELOPE_NOT_UTF8", f"documento não é UTF-8 válido: {e}", "")])

    try:
        # `parse_constant` recusa NaN/Infinity: não são JSON e quebrariam
        # qualquer consumidor posterior que faça parse estrito.
        doc = json.loads(texto, object_pairs_hook=_rejeitar_chaves_duplicadas,
                         parse_constant=_recusar_constante)
    except ValueError as e:
        return Leitura(False, None, [_erro("ENVELOPE_BAD_JSON", str(e), "",
                                           "O arquivo precisa ser JSON válido.")])

    if not isinstance(doc, dict):
        return Leitura(False, None, [_erro("ENVELOPE_NOT_OBJECT",
                                           "a raiz do inventário deve ser um objeto JSON.")])

    # ---- versão: rejeita ANTES de qualquer outra coisa ----
    versao = doc.get("inventoryVersion")
    if versao is None:
        return Leitura(False, None, [_erro("ENVELOPE_MISSING_VERSION",
                                           "`inventoryVersion` é obrigatório.")])
    if versao != INVENTORY_VERSION:
        return Leitura(False, None, [_erro(
            "ENVELOPE_UNSUPPORTED_VERSION",
            f"`inventoryVersion` {versao!r} não é suportado por este leitor "
            f"(suporta {INVENTORY_VERSION}).",
            "", "Versão desconhecida é rejeitada sem gravação, por contrato.")])

    # ---- obrigatórios do envelope ----
    for campo in ("inventoryId", "revision"):
        if not _texto_nao_vazio(doc.get(campo)):
            achados.append(_erro("ENVELOPE_MISSING_FIELD",
                                 f"`{campo}` é obrigatório e não vazio.", campo))

    achados.extend(_validar_data(doc.get("generatedAt"), "generatedAt"))

    if not isinstance(doc.get("complete"), bool):
        achados.append(_erro("ENVELOPE_BAD_COMPLETE",
                             "`complete` é obrigatório e deve ser booleano.",
                             "complete",
                             "Omissão é declarada com `false`, nunca pela ausência."))

    issuer = doc.get("issuer")
    if not isinstance(issuer, dict):
        achados.append(_erro("ENVELOPE_MISSING_ISSUER",
                             "`issuer` é obrigatório e deve ser objeto."))
    else:
        for campo in ("project", "repository", "maintainer"):
            if campo not in issuer:
                achados.append(_erro("ISSUER_MISSING_FIELD",
                                     f"`issuer.{campo}` é obrigatório.", "issuer"))
        projeto = issuer.get("project")
        if projeto is not None:
            if projeto not in PROJETOS_CONHECIDOS and projeto != "external":
                achados.append(_erro(
                    "ISSUER_UNKNOWN_PROJECT",
                    f"`issuer.project` desconhecido: {projeto!r}.",
                    "issuer", f"Conhecidos: {', '.join(PROJETOS_CONHECIDOS)}."))
            elif projeto in PROJETOS_INATIVOS:
                # Recebemos para preservar histórico, mas o relatório precisa
                # dizer que não é fonte ativa nesta fase.
                achados.append(_aviso(
                    "ISSUER_INACTIVE_PROJECT",
                    f"`{projeto}` está suspenso e não é fonte ativa de inventários.",
                    "issuer", "A referência histórica é preservada; não contar com ele."))

    # ---- evidência (precisa existir antes de resolver referências) ----
    evidencia = doc.get("evidence")
    ev_ids: set[str] = set()
    if evidencia is not None:
        if not isinstance(evidencia, list):
            achados.append(_erro("ENVELOPE_BAD_EVIDENCE",
                                 "`evidence` deve ser lista quando presente.", "evidence"))
            evidencia = []
        elif len(evidencia) > MAX_EVIDENCE:
            achados.append(_erro("ENVELOPE_TOO_MUCH_EVIDENCE",
                                 f"{len(evidencia)} evidências; limite {MAX_EVIDENCE}.",
                                 "evidence"))
            evidencia = []
        else:
            for i, ev in enumerate(evidencia):
                onde = f"evidence[{i}]"
                if not isinstance(ev, dict):
                    achados.append(_erro("EVIDENCE_NOT_OBJECT",
                                         "evidência deve ser objeto.", onde))
                    continue
                ev_id = ev.get("id")
                if not _texto_nao_vazio(ev_id):
                    achados.append(_erro("EVIDENCE_MISSING_ID",
                                         "evidência sem `id`.", onde))
                    continue
                if ev_id in ev_ids:
                    achados.append(_erro("EVIDENCE_DUPLICATE_ID",
                                         f"`id` de evidência repetido: {ev_id!r}.", onde))
                ev_ids.add(ev_id)
                for campo in ("kind", "locator", "recordedAt", "recordedBy", "subject"):
                    if campo not in ev:
                        achados.append(_erro(
                            "EVIDENCE_MISSING_FIELD",
                            f"evidência `{ev_id}` sem `{campo}`.", onde,
                            "O contrato lista id, kind, locator, recordedAt, recordedBy e subject."))
                if "recordedAt" in ev:
                    achados.extend(_validar_data(ev["recordedAt"], f"{onde}.recordedAt"))
    else:
        evidencia = []

    # ---- registros ----
    registros_brutos = doc.get("records")
    registros: list[Registro] = []
    if not isinstance(registros_brutos, list):
        achados.append(_erro("ENVELOPE_MISSING_RECORDS",
                             "`records` é obrigatório e deve ser lista "
                             "(lista vazia é válida).", "records"))
        registros_brutos = []
    elif len(registros_brutos) > MAX_RECORDS:
        achados.append(_erro("ENVELOPE_TOO_MANY_RECORDS",
                             f"{len(registros_brutos)} registros; limite {MAX_RECORDS}.",
                             "records"))
        registros_brutos = []

    vistos: dict[tuple[str, str], int] = {}
    for i, bruto in enumerate(registros_brutos):
        onde = f"records[{i}]"
        registro, achados_reg = _validar_registro(bruto, onde, ev_ids)
        achados.extend(achados_reg)
        if registro is None:
            continue
        # Distintos por par (id, revisionId) dentro do envelope. O mesmo par
        # repetido é erro de geração, não duplicata aceitável.
        chave = (registro.id, registro.revision_id)
        if chave in vistos:
            achados.append(_erro(
                "ENVELOPE_DUPLICATE_RECORD",
                f"par (id, revisionId) repetido no envelope: {chave}; "
                f"primeira ocorrência em records[{vistos[chave]}].",
                onde, "O contrato exige registros distintos por par id/revisão."))
            continue
        vistos[chave] = i
        registros.append(registro)

    # ---- segredo, em qualquer lugar do documento ----
    for caminho in _achar_segredo(doc):
        achados.append(_erro(
            "SECRET_IN_INVENTORY",
            f"valor com aparência de credencial em `{caminho}`.", caminho,
            "O intake recusa o documento inteiro. Segredo não entra nem como metadado."))

    # ---- campos desconhecidos do envelope: preservados, sem efeito ----
    desconhecidos_doc = {k: v for k, v in doc.items() if k not in _CAMPOS_ENVELOPE}
    if desconhecidos_doc:
        achados.append(Achado(
            Severidade.INFO, "ENVELOPE_UNKNOWN_FIELDS",
            f"campos fora do contrato preservados: {', '.join(sorted(desconhecidos_doc))}.",
            "", "Preservados por contrato; não têm efeito na admissão."))

    if any(a.severity is Severidade.ERROR for a in achados):
        return Leitura(False, None, achados)

    envelope = Envelope(
        inventory_version=int(versao),
        inventory_id=doc["inventoryId"],
        revision=doc["revision"],
        generated_at=doc["generatedAt"],
        issuer=issuer,
        complete=bool(doc["complete"]),
        file_digest=hash_arquivo(dados),
        registros=registros,
        evidencia=evidencia,
        desconhecidos=desconhecidos_doc,
    )
    return Leitura(True, envelope, achados)



_CAMPOS_ENVELOPE = frozenset({
    "inventoryVersion", "inventoryId", "revision", "generatedAt", "issuer",
    "records", "evidence", "complete",
})


# ---------------------------------------------------------------------------
# Classificação contra o que já foi recebido
# ---------------------------------------------------------------------------
#: Registro já conhecido pelo Hub, no formato mínimo que a comparação precisa.
#: Não carrega payload: o intake trabalha com metadados.
@dataclass
class Conhecido:
    """O que o recibo anterior registrou para um `id`."""

    id: str
    revision_id: str
    digest: str
    name: str = ""
    kind: str | None = None
    #: `version` declarada pelo emissor, quando houver. Só serve para comparar
    #: downgrade quando os dois lados usam o mesmo esquema reconhecível.
    version: str | None = None


@dataclass
class Classificado:
    """Um registro recebido, com a decisão de admissão."""

    registro: Registro
    classe: Classe
    #: Registros existentes que explicam a classificação (para conflito,
    #: sobreposição e mesmo conteúdo). Vazio nas demais.
    relacionados: list[str] = field(default_factory=list)
    #: Por que esta classe, em texto legível.
    motivo: str = ""
    #: `True` quando pode entrar no acervo como metadado catalogado.
    admitido: bool = False

    def as_dict(self) -> dict:
        """Formato achatado: classificação ao lado do registro, sem aninhar
        `record` dentro de `record`. Quem lê o recibo quer `license` e
        `origins` no lugar óbvio."""
        saida = self.registro.as_dict()
        saida.update({
            "classification": self.classe.value,
            "reason": self.motivo,
            "admitted": self.admitido,
            "related": list(self.relacionados),
        })
        return saida


def classificar(registros: list[Registro],
                existentes: list[Conhecido]) -> list[Classificado]:
    """Classifica cada registro recebido contra os já conhecidos.

    Regras do contrato (§Duplicatas, versões e compartilhamento), na ordem em
    que a gravidade manda:

      mesmo id + mesma revisão + mesmo digest  -> duplicata exata (idempotente)
      mesmo id + mesma revisão + digest dif.   -> CONFLITO: bloqueia, preserva
      mesmo id + revisão diferente             -> atualização (anterior fica)
      mesmo digest + id diferente              -> mesmo conteúdo, aliases
      mesmo nome + digest diferente            -> sobreposição, registros separados

    Um registro nunca é admitido como atualização se houver conflito: perder
    a revisão disputada é irreversível, e o contrato proíbe sobrescrever.
    """
    por_id: dict[str, list[Conhecido]] = {}
    por_digest: dict[str, list[Conhecido]] = {}
    por_nome: dict[str, list[Conhecido]] = {}
    for c in existentes:
        por_id.setdefault(c.id, []).append(c)
        por_digest.setdefault(c.digest, []).append(c)
        if c.name:
            por_nome.setdefault(c.name.casefold(), []).append(c)

    # Um conflito em qualquer registro do lote impede o lote inteiro? Não: o
    # contrato fala em bloquear a "revisão disputada", não o documento. Cada
    # registro carrega sua própria decisão.
    saida: list[Classificado] = []

    for reg in registros:
        anteriores = por_id.get(reg.id, [])
        mesma_rev = [c for c in anteriores if c.revision_id == reg.revision_id]

        if mesma_rev:
            if any(c.digest == reg.digest for c in mesma_rev):
                saida.append(Classificado(
                    reg, Classe.DUPLICATA_EXATA,
                    motivo=("mesmo id, mesma revisão e mesmo digest: "
                            "recepção idempotente, nada a regravar."),
                    admitido=True))
            else:
                # Preserva AMBOS. O Hub não decide qual relato é verdadeiro.
                saida.append(Classificado(
                    reg, Classe.CONFLITO_IDENTIDADE,
                    relacionados=[c.id for c in mesma_rev],
                    motivo=("mesmo id e mesma revisão com digest diferente. "
                            "Publicação desta revisão fica bloqueada; os dois "
                            "relatos são preservados para investigação."),
                    admitido=False))
            continue

        if anteriores:
            # Revisão diferente. Comparação semântica de versão só vale quando
            # os dois lados declaram `version`; sem isso, a ordem é
            # desconhecida e o registro é tratado como atualização a revisar.
            c = anteriores[0]
            classe = Classe.ATUALIZACAO
            motivo = (f"mesmo id com revisão diferente "
                      f"({c.revision_id!r} -> {reg.revision_id!r}); "
                      "a revisão anterior permanece preservada.")
            if reg.version and _eh_downgrade(reg.version, anteriores):
                classe = Classe.DOWNGRADE
                motivo = ("a versão declarada é anterior à registrada; "
                          "downgrade exige escolha explícita do host.")
            saida.append(Classificado(reg, classe, motivo=motivo,
                                      admitido=classe is Classe.ATUALIZACAO))
            continue

        if reg.tipo_legado in KIND_PENDENTE:
            saida.append(Classificado(
                reg, Classe.TIPO_PENDENTE,
                motivo=(f"tipo v1 {reg.tipo_legado!r} não tem `kind` no contrato; "
                        "fica na fila de recebimento, fora dos normalizados."),
                admitido=False))
            continue

        # Id novo. Ainda pode colidir por conteúdo ou por nome.
        mesmo_conteudo = por_digest.get(reg.digest, [])
        if mesmo_conteudo:
            saida.append(Classificado(
                reg, Classe.MESMO_CONTEUDO,
                relacionados=[c.id for c in mesmo_conteudo],
                motivo=("conteúdo idêntico já existe em outro id. "
                        "Aliases, autoria e base de licença são preservados "
                        "separadamente; hash não identifica autoria."),
                admitido=True))
            continue

        sobreposto = por_nome.get(reg.name.casefold(), [])
        if sobreposto:
            saida.append(Classificado(
                reg, Classe.SOBREPOSICAO,
                relacionados=[c.id for c in sobreposto],
                motivo=("mesmo nome e conteúdo diferente. Registros ficam "
                        "separados; variante e fork só com evidência."),
                admitido=True))
            continue

        saida.append(Classificado(reg, Classe.NOVO, admitido=True,
                                  motivo="id desconhecido; entra como metadado novo."))

    return saida


def _eh_downgrade(versao_nova: str, anteriores: list[Conhecido]) -> bool:
    """Comparação semântica mínima de versão declarada.

    Só compara quando ambos os lados são `N.N.N` numéricos. Qualquer outro
    formato preserva a grafia e NÃO arrisca dizer que é downgrade — o contrato
    manda aplicar comparação semântica só quando o esquema é declarado.
    """
    def partes(v: str) -> tuple[int, int, int] | None:
        m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(v).strip())
        return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

    nova = partes(versao_nova)
    if nova is None:
        return False
    for c in anteriores:
        if not c.version:
            continue
        antiga = partes(c.version)
        if antiga is not None and nova < antiga:
            return True
    return False
