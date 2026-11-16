"""Descritor de servidor MCP — o Hub registra, não conecta.

Um `mcp-server` é diferente de uma Agent Skill: não tem corpo de instruções,
tem um ENDPOINT, um TRANSPORTE e um FLUXO DE AUTENTICAÇÃO. Representá-lo como
se fosse uma Skill perderia essas três coisas — e é justamente o que o host
precisa saber para configurar a conexão.

Princípio que este módulo faz valer, e os testes verificam:

  O Hub descreve COMO conectar. Ele nunca conecta, nunca guarda credencial e
  nunca afirma que o serviço está operacional. "Catalogado" não é "disponível":
  disponibilidade depende de o host ter autenticado, e isso só o host sabe.

O descritor mora no payload do recurso como `mcp.json`, ao lado do `SKILL.md`
quando houver. É arquivo de dados, não código: nunca é executado.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

DESCRITOR = "mcp.json"

#: Transportes que o ecossistema MCP define hoje.
TRANSPORTES = ("http", "sse", "stdio")

#: Como o segredo deve ser apresentado pelo host. O Hub registra o MECANISMO,
#: nunca o valor. `none` existe porque há servidor público legítimo.
AUTENTICACOES = ("none", "api-key", "oauth2", "bearer", "basic", "unknown")

#: Nomes de campo que NUNCA podem carregar valor secreto no descritor. Se um
#: descritor trouxer `"apiKey": "AIza..."`, ele é recusado: o Hub não é
#: cofre, e um segredo versionado num pacote é um segredo vazado.
_CAMPOS_DE_SEGREDO = frozenset({
    "apikey", "api_key", "key", "token", "accesstoken", "access_token",
    "secret", "clientsecret", "client_secret", "password", "passwd",
    "authorization", "bearerauthorization", "x-goog-api-key", "credentials",
})

#: Valores que PARECEM segredo. Cobre chave do Google, Bearer, JWT e prefixos
#: comuns. Deliberadamente conservador: falso positivo aqui é um erro que o
#: autor corrige; falso negativo é credencial publicada.
_PADROES_SEGREDO = (
    re.compile(r"^AIza[0-9A-Za-z_\-]{35}$"),           # Google API key
    re.compile(r"^ya29\.[0-9A-Za-z_\-]+$"),            # Google OAuth token
    re.compile(r"^eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\."),  # JWT
    re.compile(r"^(Bearer|Basic)\s+\S{8,}$", re.I),
)


class DescritorInvalido(ValueError):
    """O descritor MCP existe mas não é utilizável."""


@dataclass
class MCPServer:
    """Descrição de um servidor MCP. Deliberadamente sem campo de segredo."""

    endpoint: str
    transport: str = "http"
    authentication: str = "unknown"
    #: Cabeçalhos que o host deve enviar, com NOMES apenas. O valor é sempre
    #: responsabilidade do host, que o obtém pelo fluxo de autenticação.
    headers: list[str] = field(default_factory=list)
    #: Ferramentas expostas, quando o autor do descritor as declarou. Nunca
    #: descobertas pelo Hub — o Hub não faz chamada de rede.
    tools: list[dict] = field(default_factory=list)
    category: str = ""
    provider: str = ""
    #: Requisitos de conta/plano que o host precisa satisfazer.
    account_requirements: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "endpoint": self.endpoint,
            "transport": self.transport,
            "authentication": self.authentication,
            "headers": list(self.headers),
            "tools": [dict(t) for t in self.tools],
            "category": self.category,
            "provider": self.provider,
            "accountRequirements": list(self.account_requirements),
            "docs": list(self.docs),
            # Nunca True: o Hub não conecta. O host é quem sabe se está ativo.
            "connectivityVerified": False,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "MCPServer":
        if not isinstance(d, dict):
            raise DescritorInvalido("O descritor MCP precisa ser um objeto JSON.")
        endpoint = str(d.get("endpoint") or "").strip()
        if not endpoint:
            raise DescritorInvalido("O descritor MCP não declara `endpoint`.")
        transport = str(d.get("transport") or "http").strip().lower()
        if transport not in TRANSPORTES:
            raise DescritorInvalido(
                f"Transporte `{transport}` não é conhecido. "
                f"Use um de: {', '.join(TRANSPORTES)}.")
        auth = str(d.get("authentication") or "unknown").strip().lower()
        if auth not in AUTENTICACOES:
            auth = "unknown"
        cabecalhos = d.get("headers") or []
        if isinstance(cabecalhos, dict):
            # Forma permissiva: mapa nome->valor. Só os NOMES sobrevivem, e
            # um valor com cara de segredo derruba o descritor inteiro.
            nomes = []
            for nome, valor in cabecalhos.items():
                _recusar_segredo(str(nome), valor)
                nomes.append(str(nome))
            cabecalhos = nomes
        return cls(
            endpoint=endpoint,
            transport=transport,
            authentication=auth,
            headers=[str(h) for h in cabecalhos],
            tools=[dict(t) for t in (d.get("tools") or []) if isinstance(t, dict)],
            category=str(d.get("category") or ""),
            provider=str(d.get("provider") or ""),
            account_requirements=[str(x) for x in (d.get("accountRequirements") or [])],
            docs=[str(x) for x in (d.get("docs") or [])],
        )


def _recusar_segredo(campo: str, valor: Any) -> None:
    """Levanta se `valor` parece credencial. Usado em todo o descritor."""
    if valor is None:
        return
    texto = str(valor).strip()
    if not texto:
        return
    for padrao in _PADROES_SEGREDO:
        if padrao.match(texto):
            raise DescritorInvalido(
                f"O campo `{campo}` contém algo que parece uma credencial. "
                f"O Hub não armazena segredos: registre apenas o NOME do "
                f"cabeçalho e deixe o valor para o host, via autenticação.")


def varrer_segredos(descritor: dict[str, Any]) -> list[str]:
    """Campos do descritor que parecem carregar segredo. Vazio = limpo.

    Percorre recursivamente porque segredo escondido dentro de `tools` ou de
    `accountRequirements` é tão vazado quanto no topo.
    """
    achados: list[str] = []

    def visitar(obj: Any, caminho: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                chave = str(k).lower().replace("-", "").replace("_", "")
                if chave in _CAMPOS_DE_SEGREDO and v not in (None, "", [], {}):
                    achados.append(f"{caminho}.{k}")
                visitar(v, f"{caminho}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                visitar(v, f"{caminho}[{i}]")
        elif isinstance(obj, str):
            for padrao in _PADROES_SEGREDO:
                if padrao.match(obj.strip()):
                    achados.append(caminho)
                    break

    visitar(descritor, "")
    return achados


def ler_descritor(files: dict[str, bytes]) -> MCPServer | None:
    """Lê `mcp.json` do payload, se existir. Nunca inventa um descritor."""
    bruto = files.get(DESCRITOR)
    if bruto is None:
        return None
    try:
        dados = json.loads(bruto.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DescritorInvalido(f"`{DESCRITOR}` não é JSON válido: {exc}") from exc
    if not isinstance(dados, dict):
        raise DescritorInvalido(f"`{DESCRITOR}` precisa conter um objeto JSON.")
    suspeitos = varrer_segredos(dados)
    if suspeitos:
        raise DescritorInvalido(
            "O descritor MCP contém campos que parecem credencial: "
            + ", ".join(sorted(suspeitos))
            + ". O Hub não armazena segredos.")
    return MCPServer.from_dict(dados)
