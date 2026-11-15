# Candidatos de integração — pesquisa externa

**Documento:** `docs/research/INTEGRATION-CANDIDATES.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch:** `arena/a92004be-lia-agenthub`
**Data da consulta:** 2026-11-15 (UTC)
**Natureza:** pesquisa documental em fontes primárias. **Nada foi instalado, baixado, executado, clonado ou aceito em termos de licença.** Nenhum dado do usuário foi enviado a nenhum serviço.
**Cobre também o entregável `docs/research/EXTERNAL-ECOSYSTEM-RESEARCH.md` do briefing.**

---

## 0. Método e limitação de acesso

### 0.1 O que foi possível

| Canal | Uso |
|---|---|
| GitHub REST API (`gh api`) | metadados de repositório, licença, estrelas, forks, `pushed_at`, releases, árvore de arquivos, conteúdo de `README`/`SECURITY.md`/código-fonte específico |
| Leitura de código-fonte remoto | `pathfilter.ts` (mcpvault), `package.json`, `SECURITY.md` |
| Busca web com extração de conteúdo | especificação Agent Skills, CanIRunAI, comparações |

### 0.2 O que **não** foi possível — e por quê isso importa

**HTTP direto para os sites de terceiros foi bloqueado neste sandbox.** Verificado:

```
canirunai.kc1t.com   → 000 (sem conexão)
canirun.ai           → 000
obsidian.md/license  → 000
modelcontextprotocol.io → 000
agentskills.io       → 000
```

Consequências, registradas como limitação real:

1. **Não li a página de licença do Obsidian na fonte.** A afirmação sobre o licenciamento do Obsidian abaixo vem de conhecimento geral e está marcada `RESEARCH (não verificada nesta sessão)`. **É a única afirmação deste documento que exige reverificação humana antes de virar decisão.**
2. Não li `docs.astral.sh/uv` diretamente; usei o `README` oficial do repositório `astral-sh/uv` (fonte primária do projeto).
3. Não li `docs.graphify.com`; usei `README` e API do repositório oficial (fonte primária do projeto).
4. Para o **`canirunai.kc1t.com` especificamente**: o domínio citado no briefing **não foi alcançável e não aparece nos resultados de busca**. O que existe e foi documentado é **`canirun.ai`**, projeto distinto, com um deploy alternativo em `canirunai-five.vercel.app` encontrado na busca. Ver §6 — **não tratei os dois como o mesmo produto.**
5. A especificação Agent Skills foi lida por extração de `agentskills.io/specification` e por `agentskills/agentskills` (repo), ambos retornados pela busca com conteúdo completo.

### 0.3 Vocabulário de classificação usado

Tipo de recurso, conforme taxonomia do próprio produto (`PRODUCT-VISION.md` §6):

`1` Agent Skill · `2` MCP Server · `3` CLI/ferramenta · `4` API/serviço · `5` Plugin/extensão · `6` Framework/runtime de agente · `7` Provider/modelo · `8` Workflow/pipeline/template · `9` Biblioteca/SDK · `10` Referência técnica

Destino: `HUB` · `STUDIO` · `FORGE` · `SHARED` · `OTHER` · `REFERENCE` · `REJECTED`

Decisão: `INTEGRATE` · `STUDY` · `REFERENCE` · `REJECT` · `DEFER`

---

## 1. Resumo executivo — as sete decisões

| # | Candidata | Decisão recomendada | Uma frase |
|---|---|---|---|
| 1 | **Agent Skills (padrão aberto)** | **INTEGRATE** (formato canônico) | É o único formato aberto, governado e amplamente adotado; adotá-lo é mais barato que qualquer formato próprio |
| 2 | **MCPVault** | **REFERENCE** (não integrar como dependência) | Resolve bem demais um problema específico do Obsidian; o Hub precisa do problema genérico, não do Obsidian |
| 3 | **Graphify** | **STUDY → REFERENCE** | Excelente ferramenta, licença Apache-2.0 limpa, mas é *produto* que roda sobre código, não *formato de capacidade*; não é dependência do Hub |
| 4 | **ai-memory** | **STUDY** (destino provável: `SHARED`/`STUDIO`, não `HUB`) | Resolve memória entre agentes — problema real do ecossistema, mas **do host**, não do Hub; e captura por hook é dado sensível |
| 5 | **uv** | **INTEGRATE** (como infraestrutura do *runtime empacotado*, não do usuário) | É o padrão de fato para ambiente Python isolado e é a única forma honesta de "usuário nunca roda pip" |
| 6 | **CanIRunAI** | **REFERENCE** (capacidade opcional, não dependência) | A pergunta "roda nesta máquina?" é legítima; a resposta não pode depender de um site de terceiro |
| 7 | **Obsidian** | **REFERENCE** (compatibilidade, não requisito) | Vault é diretório de Markdown; o Hub trata *qualquer* diretório de Markdown, e o Obsidian é um caso particular |

**A conclusão que atravessa as sete:** nenhuma delas deve ser **dependência obrigatória** do Hub. Três são **formatos ou infraestrutura** (`Agent Skills`, `uv`), três são **ferramentas de referência** (`MCPVault`, `Graphify`, `CanIRunAI`), uma é **capacidade de outro produto** (`ai-memory`). Isso é consistente com a regra nº 6 da marca (neutralidade) e com o princípio de autonomia dos hosts.

---

## 2. Agent Skills — o padrão de formato

**Não estava na lista de prioridades do briefing, mas é a decisão de maior impacto.** Sem ela, `D-03` (formato canônico) não tem resposta defensável.

### 2.1 Ficha

| Campo | Valor |
|---|---|
| Finalidade | Empacotar conhecimento procedural para agentes: diretório + `SKILL.md` |
| Tipo | `1` (Agent Skill) + `9` (especificação/validador) |
| Origem | Desenvolvido pela Anthropic (out/2025), publicado como padrão aberto em **2025-12-18** |
| Governança | `agentskills.io`; especificação em `agentskills/agentskills` |
| Licença | **Apache-2.0** (código) / **CC-BY-4.0** (documentação) |
| Maturidade | `RESEARCH` → alta adoção declarada (40+ clientes); validável localmente |

### 2.2 O que a especificação define (fonte primária)

**Estrutura:** diretório com `SKILL.md` obrigatório; `scripts/`, `references/`, `assets/` opcionais. **A localização do diretório não é definida pela especificação** — é o ponto de fragmentação conhecido.

**Frontmatter — exatamente seis campos:**

| Campo | Obrigatório | Restrição |
|---|---|---|
| `name` | **Sim** | 1–64 chars; `a-z`, `0-9`, hífen; sem hífen inicial/final/duplo; **deve coincidir com o nome do diretório** (após NFKC) |
| `description` | **Sim** | 1–1.024 chars; deve dizer **o que faz e quando usar** |
| `license` | Não | Nome SPDX ou referência a arquivo de licença incluído |
| `compatibility` | Não | ≤500 chars; requisitos de ambiente (produto, pacotes, rede) |
| `metadata` | Não | Mapa string→string para propriedades fora da spec |
| `allowed-tools` | Não | Lista separada por espaço; **experimental**, suporte varia |

**Regras adicionais observadas:** o frontmatter deve começar no byte 0; corpo recomendado <500 linhas / <5.000 tokens; *"anything else fails validation"* para chaves não previstas; carregamento em 3 camadas (metadata ~100 tokens sempre → corpo na ativação → recursos sob demanda).

### 2.3 Por que **é** a escolha certa para o Hub

1. **O ecossistema Lia já está alinhado.** Studio usa `.agents/skills/<id>/SKILL.md` com `name`+`description` e declara no `README` *"formato compatível com Agent Skills"*. O Hub adotar o padrão **não cria** trabalho de migração — **reduz**.
2. **`license` e `metadata` são exatamente os campos que faltam no Studio.** As oito lacunas (L-01, L-07) se resolvem **preenchendo campos da spec**, não inventando schema.
3. **Zero runtime.** É diretório + arquivo. Portátil por construção, sobrevive a qualquer troca de stack.
4. **Governança neutra.** Não é propriedade de um fornecedor — o que satisfaz a regra da marca.

### 2.4 Por que **não é suficiente** (o que o Hub precisa acrescentar)

A especificação é deliberadamente mínima, e isso deixa buracos que o Hub deve cobrir **fora** do `SKILL.md`:

| Buraco | Consequência | Como o Hub cobre |
|---|---|---|
| Sem campo de **versão** obrigatório | `metadata.version` é convenção, não norma | Manifesto próprio do pacote, ao lado do `SKILL.md` |
| Sem campo de **proveniência** (upstream, commit, autor, hash) | Não há cadeia de custódia | `source` no manifesto do pacote |
| `license` é **informação, sem enforcement** | Ninguém valida | Análise de licença no intake + registro em `THIRD_PARTY_NOTICES` do pacote |
| `allowed-tools` é **experimental** | Não é fronteira de segurança | Hub trata como *declaração*, nunca como concessão |
| `description` **é superfície de ataque** (dispara ativação) | Envenenamento semântico documentado | Revisão humana + diff em atualização obrigatórios |
| `compatibility` é **auto-declarado** | Nada verifica | Validador do Hub compara com inventário real do host (quando o host informar) |
| Localização não é definida pela spec | Fragmentação (`.agents/`, `.claude/`, `.cursor/`…) | Hub **emite** para `.agents/skills/` (convenção neutra) e documenta a política de espelho/junction por host |

### 2.5 Riscos registrados

| Risco | Severidade | Mitigação |
|---|---|---|
| Chave fora da spec quebra clientes estritos (ex.: upload para API de Skills rejeita chave desconhecida com erro, não ignora) | Média | Manifesto do Hub fica **ao lado**, nunca dentro do frontmatter |
| Fragmentação de localização | Média | `.agents/skills/` como canônico; cópia/espelho é do host |
| Skills com `scripts/` são mais arriscadas (2,12× segundo pesquisa citada pelo Agent 6) | Alta | Hub separa **prosa** de **scripts** e trata como dois níveis de confiança |
| Padrão pode evoluir | Baixa | `metadata` + manifesto versionado |

**Decisão:** `INTEGRATE` como **formato canônico de Skill**, com manifesto complementar do Hub. **Destino:** `SHARED`. Exige aprovação humana para `D-03`.

---

## 3. Obsidian e MCPVault

### 3.1 Obsidian

| Campo | Valor |
|---|---|
| Finalidade | Aplicativo de notas em Markdown com grafo de links |
| Tipo | `5` (aplicativo/extensão) + `10` |
| Licença | **Gratuito para uso pessoal; licença comercial paga para uso em empresa** — `RESEARCH (não verificado em obsidian.md nesta sessão; HTTP bloqueado)` |
| Formatos | Diretório ("vault") com `.md`, `.markdown`, `.txt`, `.base` (YAML), `.canvas` (JSON) |
| Requisito para o Hub | **Nenhum** — um vault é um diretório comum |

**Conclusão sobre o Obsidian:** o Hub **não** precisa do Obsidian. Precisa tratar **qualquer diretório de Markdown** como fonte de conhecimento. O Obsidian é, no máximo, um **cliente de leitura** do que o Hub organiza. Torná-lo requisito violaria a regra nº 1 da marca (funciona sozinho).

**Sobre `%USERPROFILE%\Lia\<App>` vs OneDrive:** o kit registra que `Documentos` é sincronizada com OneDrive por padrão e que pesos/cache ali causam upload involuntário de gigabytes. Isso **é** uma restrição real de desenho de armazenamento e está incorporado em `DATA-STORAGE-AND-PORTABILITY.md`. A ressalva do próprio kit de que *o comportamento do OneDrive com junction precisa de teste real* permanece aberta (`PROPOSED`, gate Windows).

### 3.2 MCPVault

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/bitbonsai/mcpvault` |
| Site | `https://mcpvault.org` (não alcançável nesta sessão) |
| Pacote | `@bitbonsai/mcpvault` v**0.18.4** (release 2026-11-14T12:56Z) |
| Linguagem | TypeScript; Node.js **≥22.12.0** (`.nvmrc` = 24) |
| Licença | **MIT** (`package.json` `"license": "MIT"`) |
| Atividade | `pushed_at` 2026-11-14; 1.724 ★; 138 forks; 19 issues abertas; **não arquivado** |
| Tipo | `2` (MCP Server) |

**Superfície de ferramentas — 18 tools:**

| Grupo | Tools |
|---|---|
| Arquivo | `read_note`, `write_note` (overwrite/append/prepend), `patch_note`, `delete_note`, `move_note`, `move_file` |
| Leitura parcial | `get_note_outline`, `read_note_lines` |
| Diretório / lote | `list_directory`, `read_multiple_notes` |
| Busca | `search_notes` (multi-palavra + reranking BM25) |
| Metadados/tags | `get_frontmatter`, `update_frontmatter`, `get_notes_info`, `get_vault_stats`, `manage_tags`, `list_all_tags` |
| Wiki links | `wiki_link` (resolve nome; devolve alternativas quando ambíguo) |

**Controles de segurança verificados no código-fonte (`src/pathfilter.ts`):**

- `RESTRICTED_SEGMENTS` negados **em qualquer profundidade**, não só na raiz: `.obsidian`, `.git`, `node_modules`, `.ds_store`, `.thumbs.db`. O comentário no código documenta que o glob antigo só pegava a raiz e vazava `.git`/`.obsidian` aninhados (issue #128) — **é um projeto que já foi corrigido por auditoria**, sinal positivo.
- Comparação **case-insensitive** (Windows/macOS resolvem `.Git` → `.git`).
- `canonicalizeForMatch()` remove pontos/espaços finais por segmento, porque **o Windows normaliza `".git."` e `".git "` para `.git`**. Isso é um detalhe de plataforma que quase ninguém acerta.
- Extensões permitidas por allowlist (`.md`, `.markdown`, `.txt`, `.base`, `.canvas`) — **não é um servidor de arquivos genérico**.
- `--read-only` remove as tools mutantes da descoberta e as rejeita se chamadas diretamente.
- `delete_note`/`move_file` exigem confirmação com caminho coincidente.
- Bloqueia ainda: travessia (`..`), escape por symlink, dotfiles.

**`SECURITY.md`:** canal privado de vulnerabilidade, resposta em 72 h, escopo declarado inclui path traversal, acesso arbitrário, injeção de comando, exfiltração, corrupção de frontmatter, DoS, supply chain. **Menos de 1 % dos projetos MCP têm isso.**

### 3.3 Por que **não** integrar como dependência

| Motivo | Detalhe |
|---|---|
| **Requisito de ambiente** | Exige **Node.js ≥22.12** instalado na máquina. Contradiz a regra nº 2 da marca ("baixou, abriu, funciona"; usuário não instala runtime) — a menos que o Hub empacote Node, o que traz peso e outro vetor de atualização |
| **Resolve um caso particular** | 18 tools com semântica de Obsidian (`wiki_link`, `manage_tags`, `.canvas`, `.base`, frontmatter AST). O Hub precisa de um subconjunto genérico |
| **Distribuição via `npx @latest`** | O README recomenda `npx @bitbonsai/mcpvault@latest`. **`@latest` não é pinado** — é exatamente o padrão de "atualização silenciosa" que `D-10` proíbe. Se o Hub promover MCPs, deve exigir versão exata + hash |
| **Sobreposição parcial** | As 6 tools de arquivo (`read/write/patch/delete/move`) colidem com o que o Hub fará para editar Skills |

### 3.4 O que **aproveitar** (valor real da pesquisa)

MCPVault é a melhor referência pública que encontrei para **contenção de caminho em Windows**. Padrões que o Hub deve copiar como *desenho*, não como código:

1. Negação de segmento proibido **em qualquer profundidade** (o bug #128 é o exemplo de por que glob ancorado na raiz falha).
2. `canonicalizeForMatch` com remoção de pontos/espaços finais — específico do Windows.
3. Allowlist de extensão, não denylist.
4. `--read-only` que **remove a tool da descoberta** e **rejeita chamada direta** — duas barreiras, não uma.
5. Confirmação por repetição do caminho em operação destrutiva.

**Decisão:** `REFERENCE` — adotar os padrões de contenção; **não** adicionar como dependência. **Destino:** `REFERENCE` para os padrões; `HUB` apenas se um dia houver suporte explícito a vaults Obsidian como *tipo de fonte de conhecimento* (então seria adapter opcional, nunca requisito).

---

## 4. Graphify

### 4.1 Ficha

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/Graphify-Labs/graphify` |
| Site / docs | `https://graphify.com`, `https://docs.graphify.com` (não alcançáveis nesta sessão) |
| Pacote PyPI | **`graphifyy`** (duplo `y`) — *"Other `graphify*` packages on PyPI are not affiliated"*; o comando é `graphify` |
| Linguagem | Python **3.10+** |
| Licença | **Apache-2.0** + arquivo **`NOTICE`** presente + **`LICENSE-MIT`** adicional (dupla) |
| Atividade | `pushed_at` 2026-11-14; 147.802 ★; 14.167 forks; 1.634 issues abertas; **não arquivado** |
| Criado | 2026-04-03 (projeto **jovem** para essa escala) |
| Tipo | `1` (publica uma *skill* `/graphify`) + `3` (CLI) + `9` (biblioteca) |

### 4.2 O que faz (segundo a fonte primária)

- Converte codebase + docs + PDFs + imagens + vídeo em **grafo de conhecimento consultável**.
- **Código é processado localmente** via AST com *tree-sitter*: determinístico, sem LLM, nada sai da máquina.
- Docs/PDFs/imagens/vídeo passam por **modelo do assistente ou API key configurada** — ou seja, **há egress opcional** dependendo do que se processa.
- Cada aresta é marcada `EXTRACTED` (explícito na fonte) ou `INFERRED` (resolvido pelo grafo). **Distinção fato × inferência no próprio artefato** — é o mesmo princípio que este projeto exige em documentação.
- **Não usa vector store nem embeddings**; grafo real, traversável.
- Instala skill em 20+ assistentes (Claude Code, Cursor, Codex, Gemini CLI, Copilot, OpenCode, Kimi, Aider…), Windows incluído.

### 4.3 Artefatos gerados — e por que isso é relevante

```
graphify-out/
├── graph.html       visualização
├── GRAPH_REPORT.md  destaques
└── graph.json       grafo completo
```

`graph.json` carrega **`graph.schema_version`** (integrações detectam mudança incompatível) e **`graph.graphify_version`** (qual release produziu). Comandos: `graphify explain`, `graphify path A B` (com confiança = a do salto mais fraco), `graphify query`.

**Isto é exatamente o padrão de proveniência de artefato que o Hub deve exigir de qualquer gerador de artefato:** versão de schema + versão de produtor, dentro do próprio arquivo. É um bom modelo a citar, mesmo se a ferramenta não for usada.

### 4.4 Requisitos e compatibilidade

| Item | Situação |
|---|---|
| Python | 3.10+ |
| Gerenciador | `uv` (**recomendado**) ou `pipx`; `pip` puro pode exigir ajuste de PATH |
| Windows | Suportado; instalação via `winget install astral-sh.uv` |
| Hardware comum | O parsing AST é barato; o custo real vem de LLM nas mídias |
| Rede | **Opcional**, mas necessária para o passo semântico em docs/PDF/imagem/vídeo |
| Concorrência | `graphify install --project` escreve no repositório atual |

### 4.5 Riscos e decisão

| Risco | Detalhe |
|---|---|
| **Escala de popularidade vs. idade** | 147 k ★ em ~7 meses é anômalo. Não é argumento contra o código, mas **não é evidência de estabilidade**; 1.634 issues abertas indica superfície grande |
| **Produto comercial no mesmo repo** | "Graphify Cloud" (YC S26) é oferecido no README. O OSS é Apache-2.0 e local para código; o cloud é outro produto. **Não confundir** licença do OSS com termos do cloud |
| **`NOTICE` obrigatório** | Apache-2.0 exige preservar `NOTICE`. Se o Hub empacotasse Graphify, teria de redistribuir o `NOTICE` |
| **Não é formato de capacidade** | Produz grafo de *um* repositório; não cataloga nem distribui capacidades |
| **Egress** | O passo semântico manda conteúdo para modelo. Isso é dado do usuário. Exigiria consentimento explícito por execução |

**Decisão:** `STUDY` → `REFERENCE`.
- **Não** integrar como dependência do Hub (não é o problema do Hub).
- **Adotar como referência** os padrões: `schema_version` + `producer_version` no artefato; aresta `EXTRACTED`/`INFERRED`; "código local por padrão, mídia com LLM opt-in".
- **Uso legítimo possível:** uma *capacidade catalogada* do tipo `3` (CLI) que o usuário instala por conta própria e o Hub apenas registra com proveniência. Isso é o comportamento correto do Hub e não exige licença especial.
- **Destino:** `OTHER`/`REFERENCE`. Registro em `THIRD_PARTY_NOTICES.md` **só** se houver redistribuição.

---

## 5. ai-memory

### 5.1 Ficha

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/akitaonrails/ai-memory` |
| Site | `https://aimemory.sh` |
| Linguagem | **Rust** (binário único autocontido) |
| Licença | **MIT** |
| Atividade | `pushed_at` 2026-11-14; 15.894 ★; 1.177 forks; 22 issues abertas |
| Tipo | `2` (MCP) + `3` (CLI) + `4` (serviço local) + `6` (infra de memória para harnesses) |

### 5.2 Arquitetura declarada (fonte primária)

```
capture ──▶ consolidate ──▶ recall ──▶ handoff
 hooks        session-end      search     next agent,
 observe      summaries as     + brief    any harness
 silently     wiki pages       injection
```

| Propriedade | Detalhe |
|---|---|
| Fonte de verdade | **Wiki Markdown versionada em git** — `.md` comuns; `grep`, Obsidian, `rsync` |
| Índice | Banco **derivado**, reconstruível a partir dos arquivos. **Sem vector store obrigatório** |
| Captura | **Lifecycle hooks** registram prompts, tool calls e limites de sessão — **automaticamente e em silêncio** |
| Fronteira de privacidade | *"sanitize it at a typed privacy boundary before anything is stored"* |
| LLM | Caminho padrão com **zero chamadas de LLM**; "dream"/consolidação por LLM é **opt-in e off por padrão** |
| Handoffs | Protocolo tipado; cada handoff tem dono e é reivindicado **exatamente uma vez** |
| Multi-usuário | Auth, atribuição por pessoa e log de auditoria **incluídos, não são tier pago** |
| Decaimento | Por agenda, ajustável por tier; uso retarda o decaimento; **nada é apagado de verdade** (original fica no git, `restore-page`) |
| Harnesses | 20+ (Claude Code, Codex, Cursor, Gemini CLI, OpenCode, Kimi, Kiro, Copilot CLI…) |

**Compatibilidade Windows (declarada na matriz de suporte):**

| Alvo | Status |
|---|---|
| Linux | Supported |
| macOS | Supported |
| **Windows via WSL2** | **Supported** |
| **Windows nativo** | **Experimental** |
| Instalação Windows | `install.ps1` verifica SHA-256, instala em `%LOCALAPPDATA%\Programs\ai-memory`, adiciona ao `PATH` do usuário; `ai-memory setup` cria entrada de logon, sem console |

Isso responde diretamente à pergunta do briefing: **Windows nativo é `Experimental`, não suportado.** WSL2 é o caminho suportado.

### 5.3 O problema real que existe aqui — e por que **não** é do Hub

O ecossistema Lia **não tem memória entre agentes**. Confirmado na auditoria:

- Project: memória **lexical apenas**, 100 entradas, sem embeddings, sem grafo, sem consolidação (`01-ESTADO-DA-ARQUITETURA.md` §1.4).
- Studio: `memory-bank/` é memória *do código*, versionada no repositório — coisa diferente.
- Forge: nenhuma.

**Portanto a lacuna é real.** Mas a pergunta correta é: **de quem é?**

| Argumento | Avaliação |
|---|---|
| "Memória de sessão de agente" é execução e contexto | → `STUDIO` (dono de sessões, contexto e permissões) |
| "Memória de projeto" atravessa produtos | → `SHARED`, mas não pertence ao Hub |
| "Memória do usuário / de personagem" | → `PROJECT` (Waifu), **privada, nunca compartilhada por padrão** |
| Catalogar o ai-memory como **capacidade** (fonte, licença, versão, requisitos, dados que captura) | → **`HUB`** — e é só isso |

**O Hub deve catalogar o ai-memory, não executá-lo.** O Hub pode dizer: *"este recurso captura prompts e tool calls por hook; requer WSL2 para suporte; licença MIT; instala em `%LOCALAPPDATA%`; envia dados a um servidor local seu"*. O Hub **não deve** instalar hooks, capturar conversas ou armazenar memória.

### 5.4 Riscos — os mais sérios desta pesquisa

| Risco | Severidade | Por quê |
|---|---|---|
| **Captura automática por hook** | **Alta** | Registra prompts e tool calls **sem pedido explícito por evento**. Isso é exatamente o que o briefing proíbe: *"Não proponha capturar conversas ou tool calls sem consentimento e controle de escopo"* |
| **Servidor HTTP com bearer token** | Média | Serviço local por usuário com token em arquivo `owner-only`. Exposição depende de bind e firewall |
| **`install.ps1 \| iex`** | **Alta** | O README recomenda `irm ... \| iex`. Executa script remoto sem inspeção prévia. Incompatível com a regra nº 4 da marca (não esconder risco) |
| **Windows nativo experimental** | Média | O caminho suportado é WSL2; nativo pode quebrar |
| **Cross-project profile** | Média | Perfil "de como você trabalha" chega a todo repositório novo. Útil, mas é dado comportamental atravessando projetos |
| **Escala de captura** | Média | 20+ harnesses integrados significa superfície de configuração muito grande |

### 5.5 Decisão

**`STUDY`.** Recomendação explícita:

1. **Não integrar ao Hub em nenhuma fase próxima.** Não é o problema do Hub.
2. **Catalogar** como capacidade candidata (`HUB`) com os campos de risco acima preenchidos — inclusive um campo de *"dados que captura"* e *"consentimento exigido"*.
3. **Encaminhar a avaliação de adoção** para o **Lia Studio**, que é o dono de sessão/contexto, com três condições não negociáveis: (a) captura **opt-in por projeto**, nunca global por padrão; (b) **sem** `irm | iex`; instalar por pacote versionado com hash; (c) revisão do que sai do processo antes de qualquer hook.
4. **Estudar** dois padrões que valem independentemente da ferramenta: **wiki Markdown como fonte de verdade + índice derivado reconstruível** e **handoff reivindicado exatamente uma vez**. Ambos são boas ideias para o contrato de handoff do Hub (que é sobre *capacidade*, não sobre memória).

**Destino:** `STUDIO` (avaliação) + `HUB` (catálogo) + `REFERENCE` (padrões).

---

## 6. uv

### 6.1 Ficha

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/astral-sh/uv` |
| Docs | `https://docs.astral.sh/uv/` (não alcançável nesta sessão; `README` do repo é fonte primária) |
| Linguagem | **Rust** |
| Licença | **Apache-2.0** (`LICENSE-APACHE` + `LICENSE-MIT` presentes) |
| Atividade | `pushed_at` 2026-11-14; 92.012 ★; 3.081 issues abertas |
| Tipo | `3` (CLI) + `9` (biblioteca/gerenciador) |

### 6.2 O que resolve

| Recurso | Detalhe |
|---|---|
| Substitui | `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, `virtualenv` e parte do `setuptools` |
| Instala e gerencia **versões do Python** | `uv python install 3.12` — **não depende de Python pré-instalado** |
| Ferramentas isoladas | `uv tool install <pkg>` / `uvx <pkg>` — ambiente efêmero por ferramenta |
| Lockfile universal | Resolução reproduzível entre plataformas |
| Sistemas | macOS, Linux, **Windows** |
| Instalação Windows | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` (ou `winget`, ou `pip install uv`) |

### 6.3 A decisão que isso habilita

O briefing pergunta: *"Determine se o Hub precisa de um gerenciador próprio de ambientes ou se deve utilizar ferramentas existentes por meio de adapters."*

**Resposta: nenhum gerenciador próprio.** Três razões:

1. **Escrever um gerenciador de ambiente Python é um projeto de anos** e não é o valor do Hub.
2. **`uv` é o único caminho honesto para a regra da marca** "o usuário final nunca roda `pip`, nunca precisa de Python instalado". O `GUIA-APP-NOVO` do kit (camada 3) exige exatamente isso. `uv python install` **instala o Python**; `uv tool install` isola a ferramenta.
3. **Já é a escolha do ecossistema:** o Graphify recomenda `uv tool install`; a própria doc do `uv` cita integração com ferramentas de agente.

### 6.4 Onde `uv` **não** se aplica — e é importante

| Situação | Por que `uv` não resolve |
|---|---|
| **Testar uma Skill/MCP de terceiro** | `uv tool install` instala **no ambiente do usuário**. Teste deve ocorrer em ambiente **descartável e isolado**, não no perfil. Exige sandbox/container/VM, não gerenciador de pacote |
| **Node/Electron** | `uv` é só Python. O Forge é Node; o Studio tem shell WebView2 |
| **Runtime empacotado** | Se o Hub for distribuído como `.exe`, `uv` é ferramenta **de build**, não do usuário final |
| **Modelos/pesos** | Fora de escopo (`uv` é pacote, não peso) |

### 6.5 Decisão

**`INTEGRATE`** — mas com escopo preciso:

- **Como infraestrutura de desenvolvimento e de empacotamento** do Hub (`uv.lock` versionado, ambiente reprodutível).
- **Como backend de ambiente isolado para o Test Lab, em fase posterior** — com uma ressalva: o Test Lab do Hub deve ser declarado **`PROPOSED`** até existir prova de que o isolamento é real. `uv tool install` **não é sandbox**.
- **Registrar em `THIRD_PARTY_NOTICES.md`** com Apache-2.0 e preservação do `NOTICE`, **se** for redistribuído.
- **Nunca** exigir que o usuário instale `uv` para usar o Hub. O instalador entrega pronto.

**Destino:** `HUB` (infraestrutura). **Risco de duplicação:** alto se alguém propuser "gerenciador de ambientes do Hub" — este documento recomenda **não**.

---

## 7. CanIRunAI

### 7.1 O problema com a referência do briefing

O briefing cita `https://canirunai.kc1t.com`. Nesta sessão:

- `curl https://canirunai.kc1t.com` → **sem conexão** (código 000).
- Busca web **não retorna esse domínio**.
- O que existe e foi documentado é **`https://canirun.ai`** — projeto com nome quase idêntico, e um deploy alternativo em `canirunai-five.vercel.app`.

**Não tratei os dois como o mesmo produto.** Registro como ambiguidade que exige confirmação humana: *o briefing refere-se a `canirun.ai` ou a outro serviço em `kc1t.com`?* Se for outro, esta seção precisa ser refeita.

### 7.2 O que `canirun.ai` faz (fonte: extração de busca)

| Propriedade | Detalhe |
|---|---|
| Função | Detectar hardware e ranquear modelos abertos locais que "cabem" |
| Detecção | **Client-side**: WebGL `WEBGL_debug_renderer_info`, WebGPU `navigator.gpu.requestAdapter()`, `navigator.hardwareConcurrency`, `navigator.deviceMemory` |
| Escopo | ~60–314 dispositivos, ~50–60 modelos; filtros por tarefa, provider, licença, quantização, contexto, velocidade |
| Cálculo | VRAM/unified memory; Apple Silicon reserva ~75 %; reserva ~2,5 GB para o SO |
| Nota | **55 % velocidade, 35 % folga de memória, ~10 % bônus de qualidade** |
| Classificação | runs great / runs well / decent / tight fit / barely runs / too heavy |
| Privacidade | Declara processamento **no navegador**, sem envio ao servidor |
| Limite declarado pelo próprio site | **"estimates based on browser APIs, actual specs may vary"**; não é benchmark |

### 7.3 Análise para o Hub

A **capacidade** é legítima e útil: *"este modelo cabe nesta máquina?"* é pergunta que o ecossistema faz (Forge tem `requirements {vramMb, ramMb, gpu}` com `null` = não medido; Project tem regra de VRAM por aritmética, explicitamente **não** benchmark).

Mas há três problemas em transformar isso em dependência:

1. **O Hub não mede hardware — o host mede.** Medir GPU é responsabilidade do host que vai executar (Studio/Forge). O Hub só pode **registrar** o que o host informou.
2. **Estimativa por browser API não é medição.** `navigator.deviceMemory` é arredondado; WebGL em contexto degradado; iGPU e unified memory são aproximações. O próprio site diz isso.
3. **Dependência de terceiro não verificável.** O briefing já proíbe transformar o site em dependência obrigatória — concordo, e acrescento: também como dependência *opcional chamada em tempo de execução*, porque isso é egress (o hardware do usuário vira requisição).

### 7.4 Decisão

**`REFERENCE`.** Recomendação concreta:

- **Não** chamar o serviço. Nem obrigatório, nem opcional em runtime.
- **Implementar como capacidade opcional local** (`PROPOSED`, fase ≥4): ler o hardware pela API do SO — no Windows, `Get-CimInstance Win32_VideoController` / DXGI (VRAM) e `GlobalMemoryStatusEx` (RAM). Isso é **medição local**, sem egress, coerente com a marca.
- **Adotar a heurística documentada** como ponto de partida: reserva de SO, fração de unified memory, faixas por VRAM. É a única parte transferível e é pública.
- **Nunca** apresentar estimativa como benchmark. A regra do Project (*"aritmética, não benchmark"*) aplica-se.

**Destino:** `REFERENCE` para a heurística; `HUB` apenas como metadado "requisitos de hardware" preenchido pelo host. **Pergunta humana pendente:** confirmar a que serviço o briefing se refere.

---

## 8. Matriz consolidada

| Candidata | Tipo | Licença | Windows | Atividade | Dados acessados | Dados transmitidos | Decisão | Destino |
|---|---|---|---|---|---|---|---|---|
| **Agent Skills** | 1, 9 | Apache-2.0 / CC-BY-4.0 | N/A (formato) | Governança neutra | Nenhum | Nenhum | **INTEGRATE** | SHARED |
| **Obsidian** | 5, 10 | Gratuito pessoal / comercial pago `RESEARCH` | Sim | Ativo | Diretório local | Nenhum (app local) | **REFERENCE** | OTHER |
| **MCPVault** | 2 | **MIT** | Sim (Node ≥22.12) | Ativo, auditado | Arquivos do vault | Nenhum | **REFERENCE** | REFERENCE |
| **Graphify** | 1, 3, 9 | **Apache-2.0** + NOTICE (+MIT) | Sim (Py 3.10+) | Muito ativo; jovem | Codebase local (AST) | **Mídia/docs → LLM** se configurado | **STUDY→REFERENCE** | REFERENCE |
| **ai-memory** | 2, 3, 4, 6 | **MIT** | **WSL2 suportado; nativo experimental** | Ativo | **Prompts + tool calls via hook** | Servidor local do usuário | **STUDY** | STUDIO / HUB (catálogo) |
| **uv** | 3, 9 | **Apache-2.0** | Sim | Muito ativo | Ambiente Python | Registro de pacotes | **INTEGRATE** | HUB (infra) |
| **CanIRunAI** | 4 | Não confirmada | N/A | Ativo | Hardware (browser) | Nenhum (declarado) | **REFERENCE** | REFERENCE |

---

## 9. O que **não** foi pesquisado nesta fase — e por que

Para evitar a impressão de cobertura total:

| Tema que seria natural no escopo | Estado | Motivo |
|---|---|---|
| Registro oficial de MCP (`registry.modelcontextprotocol.io`) | `RESEARCH` (herdado do Agent 6, não verificado aqui) | HTTP bloqueado; o relatório `ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md` (Studio `arena/04710d54`) já cobre com detalhe |
| `skills.sh`, ClawHub, SkillsMP | `RESEARCH` herdado | idem, já coberto pelo Agent 6 |
| Scanners de segurança (`snyk/agent-scan`, Cisco `mcp-scanner`) | `RESEARCH` herdado | Não avaliados quanto a licença/execução nesta sessão |
| Formatos de SBOM (SPDX, CycloneDX) | **Não pesquisado** | Pendência para a fase de especificação de segurança |
| Assinatura de pacote (Sigstore, minisign) | **Não pesquisado** | Pendência |
| Sandboxes Windows reais (AppContainer, Windows Sandbox, containers) | **Não pesquisado** | Crítico para `D-05`/`D-18` — **recomendo sessão dedicada antes de implementar Test Lab** |

**Recomendação:** não tratar `D-05` (isolamento reproduzível) como resolvida por esta pesquisa. O Hub pode entregar valor grande **sem** executar nada, e essa é a única posição defensável agora.

---

## 10. Conclusões

1. **Três integrações, nenhuma obrigatória:** formato Agent Skills (`SHARED`), `uv` (infraestrutura), e o **vocabulário** de capacidade/estado que o Forge e o Project já validaram.
2. **Nenhuma das quatro ferramentas do briefing vira dependência.** Todas são `REFERENCE` ou `STUDY`. Isso não é conservadorismo: é a leitura de que **o Hub resolve um problema que nenhuma delas resolve** (registro, proveniência, empacotamento e distribuição de capacidades).
3. **A pesquisa produziu três padrões de segurança reutilizáveis** sem custo de licença: contenção de caminho em Windows (MCPVault), proveniência dentro do artefato (Graphify), e wiki Markdown como fonte de verdade com índice derivado (ai-memory).
4. **A pergunta de `canirunai.kc1t.com` está em aberto.** Não inventei a resposta.
5. **Duas lacunas de pesquisa ficaram abertas e são relevantes:** isolamento/sandbox em Windows e cadeia de suprimentos (SBOM/assinatura). Ambas bloqueiam `D-05` e `D-18`, e nenhuma bloqueia o MVP proposto.

---

## Referências

**Fontes primárias consultadas (2026-11-15 UTC):**

| Recurso | URL | O que foi lido |
|---|---|---|
| Agent Skills — especificação | `https://agentskills.io/specification` | Frontmatter completo, regras de `name`/`description`, campos opcionais |
| Agent Skills — repo | `https://github.com/agentskills/agentskills` | `docs/specification.mdx` |
| MCPVault | `https://github.com/bitbonsai/mcpvault` | `README.md` (1.021 linhas), `SECURITY.md`, `package.json`, `src/pathfilter.ts`, releases |
| Graphify | `https://github.com/Graphify-Labs/graphify` | `README.md` (542 linhas), árvore de arquivos (`LICENSE`, `LICENSE-MIT`, `NOTICE`), metadados |
| ai-memory | `https://github.com/akitaonrails/ai-memory` | `README.md` (838 linhas) — arquitetura, matriz de suporte, instalação |
| uv | `https://github.com/astral-sh/uv` | `README.md` (326 linhas), licenças (`LICENSE-APACHE`, `LICENSE-MIT`) |
| CanIRunAI | `https://canirun.ai` | Extração de conteúdo via busca; método de detecção e heurística |
| Model Context Protocol | `https://github.com/modelcontextprotocol/modelcontextprotocol` | Tags de versão (`2025-11-25` estável, `2026-07-28`); **spec não lida** |

**Fontes secundárias (citadas pelo Agent 6, não verificadas nesta sessão):** `ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md` em `BloomRX/Lia-Studio@arena/04710d54-lia-studio` — dados de Snyk ToxicSkills, OWASP MCP Top 10, contagem do registro MCP.
