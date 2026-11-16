# Relatório de integração — Google Stitch no Lia Agent Hub

**Data:** 2026-11-15
**Branch:** `arena/a92004be-lia-agenthub`
**Escopo:** tornar o Stitch uma capacidade de primeira classe do Hub — MCP,
Agent Skills, workflow de UI/UX e design brief do próprio Hub.

---

## 1. Resumo

O Hub passou a **registrar, catalogar e distribuir configuração** do Google
Stitch. Ele não conecta, não autentica e não executa nada do Stitch.

| Entregue | Estado |
|---|---|
| Descritor do servidor MCP | pronto e versionado |
| 16 Skills oficiais catalogadas por importador real | 16/16, 0 falhas |
| Workflow UI/UX de 7 etapas | pronto, importa como `reference` |
| Padrão de handoff em `docs/design/` | pronto |
| Instruções Codex e outros hosts | pronto |
| Design brief do Hub + prompts | pronto (5 docs + 7 prompts) |
| Telas geradas no Stitch | **não** — sem acesso autenticado |
| Testes de integração | 38 novos, verdes |

**Nada foi copiado do upstream para o repositório.** O que o Hub guarda é
registro e proveniência, não payload de terceiro.

---

## 2. O que foi de fato importado × catalogado × dependente de conexão

Esta é a distinção central do relatório. Ela é a mesma doutrina de quatro
estados documentada em `docs/stitch/MCP-SETUP.md` §5.

### 2.1 Importado pelo Hub (executado de verdade)

O importador de produção rodou sobre o clone oficial
`google-labs-code/stitch-skills` @ `0337446dadde`, em biblioteca temporária:

- **17 registros** gravados: 16 `agent-skill` + 1 `mcp-server`
- **0 falhas**
- Descrições reais de 84 a 642 caracteres
- Namespace `stitch` preservado em 8 das 16 Skills
- Pacote: `docs/stitch/catalog/google-stitch.records.json`

O catálogo é **gerado por script** (`docs/stitch/tools/build-stitch-catalog.py`),
nunca escrito à mão. Regenerar é reproduzir.

### 2.2 Catalogado (o Hub conhece e descreve)

- Serviço MCP: endpoint, transporte `http`, autenticação por API key,
  **nomes** de cabeçalho, 12 ferramentas agrupadas em 4 grupos
- 16 Skills com origem, commit de origem, hash de conteúdo e hash de árvore
- Dependências reais entre Skills, lidas do texto do upstream
- Licença por componente, com evidência e base declarada

### 2.3 Dependente de conexão externa (não feito, e não simulado)

- Nenhuma tela foi criada no projeto `14298534195629906316`
- Nenhuma chamada MCP foi feita — na importação, na descoberta ou fora dela
- `connectivityVerified: false` em todo registro que envolve o serviço

**Nesta sessão não havia cliente MCP, credencial ou `gcloud`.** O projeto do
usuário está inacessível por meios legítimos. Entregamos o pacote que permite
a outra sessão executar sem repetir investigação.

---

## 3. Defeitos reais encontrados e corrigidos

A integração de material de terceiro expôs falhas que o corpus de teste do Lia
não pegaria. Ambas eram silenciosas.

### 3.1 Descrição em bloco YAML gravada como `>-`

**Sintoma:** 8 das 16 Skills oficiais usam `description: >-` e o parser gravava
o indicador literal, descartando o texto. A descrição aparecia como `>-`.

**Causa:** o leitor de frontmatter tratava cada chave como escalar de uma linha.

**Correção:** dobra de blocos YAML (`>`, `|` e modificadores de chomping) em
`src/lia_agenthub/domain/skills.py`. Coberto por `TestDescricaoEmBlocoYaml`
(6 testes, 5 formatos).

**Por que passou despercebido:** o corpus Lia usa descrição de uma linha em
100% dos casos. Só a importação de conteúdo externo revelou.

### 3.2 `contentHash` vazio para recursos sem `SKILL.md`

**Sintoma:** o registro do servidor MCP saía com `contentHash: ""`. Um
consumidor que confere integridade recebia nada — justamente no tipo que mais
depende de conferir o descritor.

**Causa dupla, e a segunda mais grave:** o hash era calculado sobre `SKILL.md`
apenas, e havia uma **segunda atribuição** de `report.hashes` mais adiante no
fluxo que recalculava com a regra antiga e apagava qualquer correção anterior.

**Correção:** fallback explícito para o arquivo primário real
(`mcp.json`, `workflow.md`, `README.md`, `manifest.json`) e remoção da
atribuição duplicada em `src/lia_agenthub/adapters/importer.py`.

**Lição registrada:** corrigir a primeira ocorrência sem varrer o arquivo
inteiro teria deixado o defeito vivo com aparência de corrigido.

---

## 4. Modelo de dados

Nenhuma categoria nova. Stitch entra nos contratos existentes:

- `mcp-server` — tipo já existente em `ResourceType`, consumido por
  `src/lia_agenthub/domain/mcp.py`
- `agent-skill` — tipo existente, com namespace
- `workflow` e `reference` — usados pelo workflow e pelo handoff

Não foi criada categoria "design" nem "stitch". O Stitch é descoberto pelas
dimensões que já existem: tipo, domínio, tags e proveniência.

### Descritor MCP

`docs/stitch/mcp/google-stitch.mcp.json`:

- endpoint `https://stitch.googleapis.com/mcp`
- transporte `http`
- autenticação `api-key`
- `headers: ["X-Goog-Api-Key"]` — **nome do cabeçalho, nunca o valor**
- 12 ferramentas em 4 grupos
- `category: "UI/UX Design"`, origem Google Stitch

O importador rejeita o recurso se encontrar credencial no descritor
(`TestDescritorMCP::test_credencial_no_descritor_recusa_o_recurso`), e o
endpoint entra em `egress` para que a análise de risco enxergue o destino.

---

## 5. Skills catalogadas

16 Skills em 3 plugins, todas oficiais:

| Plugin | Skills | Tamanho |
|---|---|---|
| `stitch-design` | 6 | 248K |
| `stitch-build` | 5 | 284K |
| `stitch-utilities` | 5 | 116K |

**Dependências reais** (lidas do upstream, não presumidas):

- `code-to-design` → `extract-design-md`, `extract-static-html`,
  `manage-design-system`, `upload-to-stitch`
- `manage-design-system` → `code-to-design`, `upload-to-stitch`
- `upload-to-stitch` → `extract-static-html`

12 Skills mencionam o MCP do Stitch como pré-requisito. Isso significa que a
maioria **não funciona sem host configurado e autenticado** — o catálogo
registra essa dependência em vez de escondê-la atrás de "disponível".

### Licença

O repositório upstream é **Apache-2.0 na raiz**, mas **nenhuma das 16 Skills
declara licença no próprio frontmatter**. O registro captura exatamente isso:
`spdx`, `kind: repository-root-LICENSE` e uma nota dizendo que a Skill não traz
campo próprio. `redistributable` permanece `false` em todos os registros —
licença declarada não é permissão de redistribuição.

---

## 6. Workflow e handoff

**Workflow:** `docs/stitch/workflow/lia-uiux-workflow.md`, 7 etapas —
Discovery, Design brief, Prompt engineering, Design generation, Design
validation, Handoff, Implementation feedback.

Dois princípios não negociáveis, verificados por teste:

1. Stitch é referência visual; **código, contratos e requisitos continuam fonte
   da verdade funcional e arquitetural**
2. Não aceitar a primeira geração; e nunca alterar um contrato para acomodar um
   mockup

**Handoff:** `docs/stitch/handoff/README.md` define `docs/design/` com
`DESIGN-SYSTEM.md`, `DESIGN-DECISIONS.md`, `stitch/{screens,assets,prompts,exports}/`,
`approved/` e `implementation-mapping/`. Adapta o padrão existente em vez de
criar estrutura paralela.

> **Limitação registrada:** o workflow importa como tipo `reference`, não
> `workflow`, porque o Hub não lê `type:` do frontmatter (P-E5, fora de escopo).
> O comportamento é o esperado hoje; não foi contornado com gambiarra.

---

## 7. Design brief do Hub

`docs/stitch/design-brief-hub/`:

| Arquivo | Conteúdo |
|---|---|
| `README.md` | escopo, método, o que foi e não foi feito |
| `01-POSITIONING.md` | público, proposta de valor, identidade |
| `02-INFORMATION-ARCHITECTURE.md` | navegação e telas, derivadas de 20 rotas reais |
| `03-DESIGN-SYSTEM.md` | cor, tipografia, componentes, semântica |
| `04-STATES-AND-INTERACTIONS.md` | vazio, carregando, erro, sucesso, ações |
| `05-PROMPTS.md` | 7 prompts autossuficientes, prontos para colar |

**Nenhuma funcionalidade foi inventada.** As telas do brief correspondem a
rotas que existem em `src/lia_agenthub/interface/server.py`, e um teste
(`test_prompts_do_hub_nao_inventam_funcionalidade`) falha se o brief citar rota
inexistente.

Os exemplos dentro dos prompts também são medidos, não decorativos: os avisos
do prompt de importação (namespace + 4 escapes de referência) são exatamente o
que o importador reporta para `code-to-design`.

A decisão de design mais importante está registrada no brief: **nunca verde
para "importado"**. Verde significa revisado por humano. Âmbar é quarentena.
Isso impede que a UI sugira confiança que o produto não verificou.

---

## 8. Codex e outros hosts

`docs/stitch/CODEX-AND-OTHER-HOSTS.md` distingue:

- Skill **catalogada no Hub** ≠ instalada no agente ≠ MCP configurado no host
  ≠ capacidade **disponível na sessão**
- Nenhum estado implica o seguinte; o Hub cobre só o primeiro
- Instalação via marketplace `google-labs-code/stitch-skills`; instalação
  compartilhada × por projeto; **não copiar todas as Skills para todos os
  projetos** quando o marketplace resolve

**Correção aplicada:** uma versão anterior deste documento instruía
`codex plugin install <plugin> --scope user`. Esse comando **não existe na
documentação oficial**. Foi removido e substituído pelo caminho via UI, com nota
do motivo. Um teste (`test_nenhum_documento_inventa_comando_cli`) impede a
reintrodução de linha de comando não verificada.

---

## 9. Testes

`tests/integration/test_stitch_integration.py` — **38 testes**, em 4 grupos:

| Grupo | Cobre |
|---|---|
| `TestDescritorMCP` | transporte, autenticação, segredo, egress, tipo, varredura recursiva |
| `TestCatalogoStitch` | 16+1, origem/commit, hashes, descrição, namespace, licença, ausência de payload |
| `TestDocumentacaoStitch` | existência, coerência CATALOG.md↔JSON, 7 etapas, precedência, rotas reais |
| `TestFronteirasStitch` | não executa script, não abre socket, exporta sem segredo |

O teste mais valioso é `test_hub_nao_faz_chamada_de_rede_na_importacao`: ele
monkeypatcha `socket.connect` para falhar e prova **ativamente** que a
importação não abre conexão. Uma promessa em prosa não seria evidência.

**Suíte total: 504 passed** (466 antes desta rodada + 38 novos).
Corpus Lia: 53/53. Stitch: 16/16.

---

## 10. O que continua aberto

| Item | Situação |
|---|---|
| Telas no projeto `14298534195629906316` | não criadas — exige host autenticado |
| `connectivityVerified` | `false` — por princípio, não por falha |
| `THIRD_PARTY_NOTICES.md` | **não atualizado**: nenhum payload foi incorporado, então o texto atual segue verdadeiro |
| P-E1/P-E2 | documentados em `docs/research/SKILL-CATALOG-IMPORT-REPORT.md` §4.3 — o arquivo **não existe nesta branch** (vive em `origin/arena/1a7ed773-lia-agenthub` e `origin/arena/db625478-lia-agenthub`); não reabertos, e não referenciados como se estivessem aqui |
| P-E5 (`type:` do frontmatter) | fora de escopo; afeta o workflow |

Nenhum desses itens foi declarado pronto. A ausência é registrada, não
contornada.

---

## 11. Como uma sessão com acesso executa

1. Instalar o MCP no host conforme `docs/stitch/MCP-SETUP.md` (API key ou OAuth)
2. Verificar que a sessão lista as 12 ferramentas — se não listar, não está
   autenticada, e o Hub não pode resolver isso
3. Importar o workflow (`docs/stitch/workflow/lia-uiux-workflow.md`) como
   referência
4. Seguir `05-PROMPTS.md` na ordem 0 → 6, aplicando o design system primeiro
5. Validar cada geração contra `04-STATES-AND-INTERACTIONS.md`; rejeitar a
   primeira
6. Registrar o aprovado em `docs/design/approved/` com a proveniência do
   projeto e das telas

O passo 6 é o que mantém o handoff auditável: sem ele, a tela aprovada vira
uma imagem sem origem.
