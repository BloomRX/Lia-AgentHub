# Google Stitch via MCP — configuração no host

O Hub **registra** como conectar. Ele não conecta, não autentica e não
armazena credencial. Quem executa a conexão é o host, com a conta do usuário.

| Item | Valor |
|---|---|
| Nome | Google Stitch MCP |
| Endpoint | `https://stitch.googleapis.com/mcp` |
| Transporte | **HTTP** (streamable). Não é stdio, não é SSE |
| Autenticação | API key **ou** OAuth via Google Cloud |
| Categoria | UI/UX Design |
| Tipo no Hub | `mcp-server` |
| Documentação oficial | <https://stitch.google.com/docs/mcp/setup> |

Fonte: documentação oficial consultada em 2026-11-15. O endpoint e o
transporte são fatos do serviço; o Hub não os verificou por conexão (§5).

## 1. Autenticação — duas formas

### A. API key (mais simples)

1. Abrir <https://stitch.google.com/settings>.
2. Seção **API Keys** → **Create API Key**.
3. Copiar a chave e guardá-la onde o host espera o segredo.

Cabeçalho: `X-Goog-Api-Key: <chave>`

### B. OAuth / Application Default Credentials

Para ambiente onde segredo persistente em disco é proibido, ou cliente que só
aceita fluxo de login.

```bash
gcloud auth login                        # como usuário
gcloud auth application-default login    # como aplicação
gcloud config set project "$PROJECT_ID"
gcloud beta services mcp enable stitch.googleapis.com --project="$PROJECT_ID"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="user:$(gcloud config get-value account)" \
  --role="roles/serviceusage.serviceUsageConsumer" --condition=None
TOKEN=$(gcloud auth application-default print-access-token)
```

Cabeçalhos: `Authorization: Bearer <token>` e `X-Goog-User-Project: <project id>`

**O token expira em cerca de 1 hora.** Renovar exige repetir a geração e
atualizar a configuração do cliente — a maioria dos clientes MCP não lê `.env`
automaticamente. É limitação do serviço, não do Hub.

## 2. Configuração por cliente

### Cursor — `.cursor/mcp.json`

```json
{
  "mcpServers": {
    "stitch": {
      "url": "https://stitch.googleapis.com/mcp",
      "headers": { "X-Goog-Api-Key": "<SUA_CHAVE>" }
    }
  }
}
```

### VS Code — `mcp.json`

```json
{
  "servers": {
    "stitch": {
      "url": "https://stitch.googleapis.com/mcp",
      "type": "http",
      "headers": {
        "Accept": "application/json",
        "X-Goog-Api-Key": "<SUA_CHAVE>"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add stitch --transport http https://stitch.googleapis.com/mcp \
  --header "X-Goog-Api-Key: <SUA_CHAVE>" -s user
```

`-s user` grava em `~/.claude.json`; `-s project` grava em `./.mcp.json`.

### Antigravity — MCP Servers → View raw config

```json
{
  "mcpServers": {
    "stitch": {
      "serverUrl": "https://stitch.googleapis.com/mcp",
      "headers": { "X-Goog-Api-Key": "<SUA_CHAVE>" }
    }
  }
}
```

> Note a diferença: Antigravity usa `serverUrl`, os outros usam `url`. Não é
> erro de digitação — é incompatibilidade real entre clientes.

### Gemini CLI

```bash
gemini extensions install https://github.com/gemini-cli-extensions/stitch
```

### Codex

O Codex consome as **Skills** pelo marketplace (ver `CODEX-AND-OTHER-HOSTS.md`).
Para o servidor MCP, usar a configuração MCP do host com o endpoint e o
cabeçalho acima.

## 3. Regra de segredo — inegociável

- O Hub **recusa** um descritor que pareça conter credencial
  (`docs/stitch/mcp/google-stitch.mcp.json` lista só **nomes** de cabeçalho).
- Nunca commitar chave, token ou `.env`.
- Nunca colar chave em prompt, issue, log ou captura de tela.
- Rotacionar em <https://stitch.google.com/settings> se houver suspeita.

O Hub registra `headers: ["X-Goog-Api-Key"]` — o NOME. O valor é do host.

## 4. Ferramentas expostas pelo servidor

12 ferramentas, em 4 grupos. Lista conforme documentação oficial; o Hub a
registra como **declaração do provedor**, não como descoberta própria.

| Grupo | Ferramentas |
|---|---|
| Project Management | `create_project`, `get_project`, `list_projects` |
| Screen Management | `list_screens`, `get_screen` |
| AI Generation | `generate_screen_from_text`, `edit_screens`, `generate_variants` |
| Design Systems | `create_design_system`, `update_design_system`, `list_design_systems`, `apply_design_system` |

`generate_screen_from_text` aceita `modelId` `GEMINI_3_FLASH` ou
`GEMINI_3_PRO`. O Hub não escolhe modelo por ninguém.

## 5. Quatro estados que não são a mesma coisa

Esta distinção é a parte mais importante deste documento. Confundir os quatro
é o erro que faz alguém achar que tem uma capacidade quando não tem.

| Estado | Significa | Como saber |
|---|---|---|
| **Catalogado no Hub** | Existe registro com endpoint e auth | `hub.detail(<id>)` retorna `type: mcp-server` |
| **Configurado no host** | O cliente tem a entrada MCP | Arquivo de config do cliente existe |
| **Autenticado** | A conta autorizou o acesso | Uma chamada de ferramenta responde sem erro de auth |
| **Disponível na sessão** | O agente vê as ferramentas agora | As 12 ferramentas aparecem na sessão |

Só o quarto estado permite usar. O Hub sempre reporta
`connectivityVerified: false` — porque catalogar não verifica conexão, e afirmar
o contrário seria mentira verificável.

## 6. Limitações registradas

- **O token OAuth expira em ~1 hora.** Renovação é manual em vários clientes.
- **`serverUrl` vs `url`** difere entre clientes; copiar configuração de um
  para outro não funciona.
- **O Hub não faz chamada de rede.** Nenhuma: nem na importação, nem na
  descoberta, nem ao abrir o detalhe. Verificar conectividade é do host.
- **Sem conta Stitch não há capacidade.** O serviço exige conta Google com
  acesso; nada aqui contorna isso.
