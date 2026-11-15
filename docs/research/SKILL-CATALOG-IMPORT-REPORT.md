# Relatório de catalogação no formato do Lia Agent Hub

**Documento:** `docs/research/SKILL-CATALOG-IMPORT-REPORT.md` (Missão 5)
**Agente:** Research — Lia Agent Hub · **Branch:** `arena/db625478-lia-agenthub`
**Data:** 2026-11-15 (UTC)
**Formato usado:** o **oficial já implementado** no Hub (`schemaVersion: 1`), lido na branch de referência `arena/a92004be-lia-agenthub`, commit `b4eb85f`. Nenhum campo foi inventado; nenhum catálogo paralelo foi criado.

> **Resultado em uma linha:** **48 registros prontos para importação** foram produzidos (1,5 MB de payload referenciado), **0 recursos foram efetivamente gravados na biblioteca real do Hub** — o Hub não foi executado nesta sessão, e as razões e o caminho de verificação estão nas §4 e §7.

---

## 1. O que foi examinado antes de catalogar (contrato real, não suposto)

| Arquivo (branch `arena/a92004be-lia-agenthub` @ `b4eb85f`) | O que define | Uso neste trabalho |
|---|---|---|
| `src/lia_agenthub/domain/model.py` | `SCHEMA_VERSION = 1`; `Capability.as_dict()` (chaves exatas: `schemaVersion`, `id`, `name`, `version`, `type`, `description`, `domain`, `tags`, `author`, `license`, `source`, `trust`, `lifecycle`, `contentHash`, `treeHash`, `containsScripts`, `declaredPermissions`, `egress`, `secrets.envVars`, `requirements`, `history`, `versionOf`); enums `ResourceType` (11), `Trust` (4), `Lifecycle` (4), `LicenseStatus` (3), `Severity` (4); `License` **por camada** (`code`, `content`, `weights`, `status`, `redistributable`, `redistribution_basis`, `notice_required`); `Source` (`upstream`, `commit`, `imported_at`, `method`, `original_name`); `new_id(nome, salt)` | formato dos registros gerados |
| `src/lia_agenthub/domain/integrity.py` | `sha256_bytes`, `content_hashes` (`asReceived` × `normalized`), `tree_hash` (sha256 sobre `path\x00hash\n` em ordem estável); "hash ≠ assinatura"; não existe campo `signed` | cálculo de `contentHash`, `treeHash` e hashes por arquivo |
| `src/lia_agenthub/domain/paths.py` | controles C1–C13; `DENY_NAMES` (`.ssh`, `.env`, `credentials`, `.npmrc`…); `EXEC_EXTS`; `MAX_PATH_LEN = 200`; `MAX_DEPTH = 24`; `looks_like_script` (`scripts/` em qualquer nível **ou** extensão executável) | `containsScripts` e `executable` por arquivo |
| `src/lia_agenthub/domain/skills.py` | 6 campos conhecidos (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`), 2 obrigatórios; limites 64/1024/500; parser **simples** (`chave: valor`; aninhamento ignorado de propósito, para não depender de PyYAML); códigos de issue | validação estrutural reproduzida nos registros |
| `src/lia_agenthub/domain/risk.py` | `Risk` (low/medium/high/unknown), fatores com peso, `ALWAYS_NOT_EVALUATED` (4 itens), disclaimer "não é aprovação" | o que **não** afirmamos sobre risco |
| `src/lia_agenthub/adapters/repository.py` | layout real: `<Biblioteca>/<id>/payload/` + `.lia/{capability,provenance,history,validation}.json`; **índice é derivado, o disco vence**; `stage()` grava em Quarentena; `promote()` move e ativa; `supersede()` preserva a versão anterior | forma dos arquivos `.lia/*` gerados |
| `src/lia_agenthub/adapters/paths_resolver.py` | `%USERPROFILE%\Lia\AgentHub\{Biblioteca,Quarentena,Exportados,Colecoes}`, `%USERPROFILE%\Lia\Comum\Capacidades`, `%APPDATA%`, `%LOCALAPPDATA%`, override `LIA_AGENTHUB_HOME` | onde a importação real acontece (não neste repositório) |
| `src/lia_agenthub/adapters/importer.py` | pipeline de 6 passos; BOM removido **e registrado**; varredura Unicode por região (categorias B e D → `requires_review`); `_detect_type`; validação estrutural + `check_references`; manifesto; `_detect_license` (**só arquivo na raiz do payload**); `domain`/`tags`/`author` extraídos da string inline de `metadata`; `cap_id = new_id(display, salt=tree_hash)`; `contentHash` = sha256 do `SKILL.md`; staging em quarentena | algoritmo reproduzido pela ferramenta de pesquisa |
| `src/lia_agenthub/adapters/index_builder.py` | `index.json` (`schemaVersion 1`, `signed: false`), campos por entrada (`id`, `name`, `version`, `type`, `description[:280]`, `domain`, `tags`, `author`, `trust`, `license`, `licenseKnown`, `redistributable`, `treeHash`, `containsScripts`, `egress`, `package`, `notEvaluated`); só entradas `ACTIVE` entram no índice | o que aparecerá (e o que **não** aparecerá) no índice compartilhado |
| `src/lia_agenthub/adapters/packager.py` | pacote `.lia-capability`: `manifest.json` (`formatVersion 1`, `schemaVersion 1`, `payload.files`, `hashes`, `notices`, `integrityNote`), `payload/`, `provenance.json`, `NOTICE`, `THIRD_PARTY_NOTICES.md`; **sem `signatures/`**; `Target` = `private|self|shared|public` | convenção de empacotamento proposta na auditoria §7.4 |
| `docs/examples/comum-index.example.json` | exemplo sintético do índice compartilhado | conferência do formato de saída |

**A branch de referência moveu durante a sessão** (`b4eb85f` → `704dfd3f`, adicionando `docs/architecture/CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md`). O código lido aqui é o de `b4eb85f`; nenhum arquivo do modelo de dados mudou entre os dois commits (a diferença é 1 documento).

---

## 2. O que foi produzido

| Arquivo | Conteúdo | Registros |
|---|---|---:|
| `docs/research/catalog/sources.json` | fontes fixadas: repositório, branch, **commit**, data de inspeção, raiz local inspecionada, e as notas de pesquisa por skill | 48 entradas de fonte |
| `docs/research/catalog/lia-studio.records.json` | `Lia-Studio@203b60f17d177f7faf79d293b95f078d0d0a729a` · `.agents/skills/` | **16** |
| `docs/research/catalog/lia-project.records.json` | `Lia-Project@0093de090d86c291b7a85eaeacebe0a559585359` · `.agents/skills/` | **22** |
| `docs/research/catalog/lia-model-lab.records.json` | `Lia-Model-Lab@3ec4313ba57ec94a7f3d93ec4f7a0d533d5077cf` · `.agents/skills/` | **9** |
| `docs/research/catalog/lia-forge.records.json` | `Lia-Forge@35b207f7b1ae5bc0c104fbdd0e9cf6ae83944692` · `.agents/skills/` | **1** |
| `docs/research/tools/build-catalog-records.py` | ferramenta de pesquisa (somente stdlib) que reimplementa o algoritmo documentado e gera os registros | — |

Cada registro tem **três blocos**, deliberadamente separados:

```jsonc
{
  "capability":    { /* exatamente .lia/capability.json — contrato do Hub */ },
  "provenance":    { /* exatamente .lia/provenance.json — contrato do Hub */ },
  "researchNotes": { /* metadado de PESQUISA: origem, commit, licença, reuso,
                         issues estruturais, avisos de importação.
                         NÃO faz parte do contrato e não deve ser gravado
                         em .lia/ sem decisão humana */ }
}
```

Exemplo real (gerado, não ilustrativo):

| Campo | Valor |
|---|---|
| `id` | `lia-game-qa-plan-3bf0e9fe` |
| `name` / `type` / `version` | `lia-game-qa-plan` / `agent-skill` / `0.1.0` |
| `contentHash` | `3aefa8664adb2c2c5de2f91da818d9cf6cf74bcb686957d41bb62460bf7bd38f` |
| `treeHash` | `f3ea0279f796bfcb047b3a1dcc28d4e4c476b404d050b76255d522a6ac3739a8` |
| `source.upstream` | `BloomRX/Lia-Studio@203b60f:.agents/skills/lia-game-qa-plan` |
| `trust` / `lifecycle` | `unreviewed` / `quarantined` (**correto por desenho**: promoção é decisão humana) |
| `license.status` | `unknown` — nenhum `LICENSE` na raiz do payload |
| `researchNotes.derivationUrl` | `…/Donchitos/Claude-Code-Game-Studios/blob/05ad7c8a5b…/.claude/skills/qa-plan/SKILL.md` |

### 2.1 Números consolidados dos 48 registros

| Métrica | Valor |
|---|---|
| Tipo detectado | **48 `agent-skill`** (todos têm `SKILL.md` na raiz do payload) |
| Payload total referenciado | **1.572.502 bytes** |
| Payloads com mais de um arquivo | **2**: `alethe` (23 arquivos) e `lia-game-project-bootstrap` (8) |
| `containsScripts: true` | **1** (`alethe` — `scripts/orchestrate.py`, `scripts/diagram.py`) |
| Licença detectada no payload | **1** (`alethe` → `MIT`); **47** → `unknown` |
| `version` resultante | **48 × `0.1.0`** (nenhuma declara `version` como chave de topo) |
| `description` resultante | **48 vazias** — embora **48/48** tenham `description` no frontmatter |
| `compatibility` no frontmatter | **11** |
| `license` no frontmatter (campo da spec) | **1** (`lia-eventa-ipc: MIT`) — **ignorado** pelo importador, que só lê arquivo de licença |
| Campos de frontmatter fora da spec | **0** (as 48 são estruturalmente limpas) |
| Issues estruturais | **2 × `NAME_FOLDER_MISMATCH`** (artefato do import direto, ver §4.2) |
| Avisos de importação | **47 ×** "nenhum arquivo de licença encontrado" |
| `metadata:` aninhado | **1** (`alethe`) → lido como string vazia, perdendo `version: "19"` e `argument-hint` |

---

## 3. O que foi **efetivamente registrado** no catálogo real

**Nada.** Estado explícito, sem eufemismo:

| Estágio | Quantidade | Onde |
|---|---:|---|
| Recurso **encontrado** | 48 skills Lia + 29 vendadas do AIRI + 20 no ZIP Mr-Mak + ~40 fontes externas | inventário e catálogo de terceiros |
| Recurso **analisado** | 48 (payload, frontmatter, hashes, licença, proveniência) + 24 externos (metadados) + 12 externos (conteúdo) | este relatório + auditoria |
| Recurso **catalogado (registro pronto no formato do Hub)** | **48** | `docs/research/catalog/*.records.json` |
| Recurso **gravado na biblioteca do Hub** (`%USERPROFILE%\Lia\AgentHub\Biblioteca`) | **0** | — |
| Recurso **promovido da quarentena** | **0** | promoção é ação humana separada, por desenho do produto |
| Recurso **aprovado para uso** | **0** | exige decisão humana |
| Recurso **incorporado a um projeto Lia** | **0 por esta pesquisa** | o que já existe (`alethe`, 12 adaptadas no Studio) veio de sessões anteriores |

### 3.1 Por que nada foi gravado

1. **O Hub não está nesta branch.** `arena/db625478-lia-agenthub` parte de `main`, que só tem documentação. O código do Hub vive em `arena/a92004be-lia-agenthub`, branch de outra sessão, que **não foi mergeada** (regra: não fazer merge de branch de especialista sem autorização).
2. **Fase 0 proíbe execução/instalação.** `AGENTS.md`: não instalar, baixar ou executar ferramentas; não implementar produto. Rodar o Hub exigiria ambiente Python + dependências (`pyproject.toml`) — introdução de dependências, também vedada.
3. **Copiar payload entre repositórios exige autorização.** `AGENTS.md` veda "integrar, migrar ou copiar código entre repositórios" sem autorização posterior. Por isso os registros **referenciam** os payloads por repo/branch/commit/caminho e **não** os duplicam neste repositório.
4. **Sem Windows.** O destino real é `%USERPROFILE%\Lia\…`; não há como gravar nem validar nesse ambiente a partir daqui.
5. **Nenhuma skill de terceiros tem decisão de licença.** Enquanto P-4/P-5/P-8/P-10 da auditoria estiverem abertas, catalogar terceiros como "aprovado" seria falso.

---

## 4. O que **não** foi possível registrar — e por quê

### 4.1 Recursos encontrados e deliberadamente não registrados

| Recurso | Quantidade | Motivo | O que destravaria |
|---|---:|---|---|
| Skills vendadas do AIRI (`airi/.agents/skills/`) | 28 + 1 | fonte **temporária** em processo de desacoplamento; o próprio Lia-Project já as auditou uma a uma e decidiu o destino de cada | decisão de catalogar conteúdo de fork vendado (D-20) |
| Pacote `docs/Mr-Mak-Skills-Free.zip` (Lia-Studio) | 20 skills / 764 arquivos | conteúdo de terceiros versionado dentro de um repositório Lia; o Studio registra que **não comparou arquivo a arquivo** com a fonte pública; `img2threejs` tem Apache-2.0 próprio | usar o upstream MIT (`witnesstodark/mr-mak-workspace@cf1e126`) como fonte, não o ZIP |
| Servidor MCP `lia-forge` (`scripts/spriteforge-mcp.mjs`, 10 tools) | 1 | é **código de produção** de outro repositório; copiá-lo exigiria autorização; e `_detect_type` só classifica `mcp-server` quando há `package.json` no payload | decisão de fronteira + pacote com `package.json` e licença das dependências (`@modelcontextprotocol/sdk`, `zod`) verificada |
| `scripts/mcp_config.py` (instalador de configuração MCP) | 1 | idem (código de produção, efeito colateral em configs de hosts) | mesma decisão |
| Perfis de agente Codex (`.codex/agents/*.toml`, Model-Lab) | 7 | `_detect_type` retornaria **`unknown`** (não é `.md`/`.txt`/`SKILL.md`/`package.json`) — o modelo enumera tipos, mas a detecção não os cobre | evolução da detecção (§5, item E-5) ou manifesto explícito |
| Templates do Model-Lab (`templates/*.md`) | 5 | importados soltos virariam `type: reference`, perdendo a semântica de `template` | registrar como pacote com manifesto declarando `type: template` |
| Capability Registry da Forge (`shared/capabilities/registry.mjs`, 49 capacidades) | 49 | **não é capacidade de agente**: é registro de capacidades de produção de assets, dono = Forge. Catalogar aqui criaria o segundo catálogo paralelo que o mandato proíbe | contrato de leitura entre Forge e Hub (D-07), sem transferência de execução |
| Catálogo de modelos do Lia-Project (`docs/research/lia-capability-catalog/`, 44 registros) | 44 | domínio diferente (modelos/pesos/runtimes/providers), já com esquema e estados próprios | mapeamento de tipos, não absorção |
| Fontes externas (anthropics/skills, superpowers, mattpocock, secops, mr-mak, ccgs…) | ~40 | **nenhuma cópia foi feita**; licenças pendentes de decisão humana | P-4, P-5, P-8 da auditoria |

### 4.2 Campos que o modelo atual **não comporta** (com evidência de código)

| # | Lacuna | Evidência | Efeito nos 48 registros |
|---|---|---|---|
| E-1 | **Descrição não vem do `SKILL.md`** | `importer.py`: `description=(manifest or {}).get("description","")` | **48 descrições vazias**; o índice compartilhado mostraria 48 linhas sem descrição, embora todas tenham `description` no frontmatter |
| E-2 | **Licença só por arquivo na raiz do payload** | `_detect_license` faz `if "/" in rel: continue` | **47 de 48** com `license.status: unknown` e `licenseKnown: false`; o campo `license: MIT` no frontmatter de `lia-eventa-ipc` é **ignorado** |
| E-3 | **`metadata:` aninhado é descartado** | `skills.py::parse_frontmatter` ignora linhas indentadas de propósito (sem PyYAML) | `alethe` perde `version: "19"` → `0.1.0`; qualquer skill que declare `metadata.author/version/tags` perde os três (e a spec oficial usa exatamente esse formato aninhado no exemplo) |
| E-4 | **Sem campo de derivação** | `model.py::Source` tem `upstream`, `commit`, `method`, `original_name`; `versionOf` é linhagem de versões | 12 skills adaptadas do Studio + `alethe` não conseguem expressar "adaptada de X no commit Y" dentro do contrato |
| E-5 | **Detecção de tipo limitada** | `_detect_type`: `SKILL.md`→skill, `package.json`→mcp-server, `.md`/`.txt`→reference, senão unknown | 7 perfis `.toml` → `unknown`; 5 templates → `reference` |
| E-6 | **Nome da pasta derivado da primeira subpasta** | `importer.py`: `folder = next((p.split("/")[0] for p in files if "/" in p), None)` | `alethe` e `lia-game-project-bootstrap` recebem aviso espúrio `NAME_FOLDER_MISMATCH` ("`name` é X mas a pasta é `assets`/`references`") ao importar a pasta diretamente |
| E-7 | **`requirements` sempre `null`** | nenhum caminho de importação preenche `requirements` | dependências declaradas em `compatibility` (11 skills) não viram requisito estruturado |
| E-8 | **Sem camada de marca** | `License` tem `code`/`content`/`weights`, não `trademark` | `alethe` carrega 5 sinais distintivos de terceiros sem campo onde registrar o impedimento |
| E-9 | **Índice só lista `ACTIVE`** | `index_builder.build_index` filtra `lifecycle is not ACTIVE` | os 48, importados, ficariam em **quarentena** e portanto **invisíveis no índice compartilhado** até promoção humana (comportamento correto, mas precisa ser comunicado ao usuário) |

### 4.3 Propostas de evolução **compatíveis** (aditivas; não alteram contrato em produção nesta fase)

| # | Proposta | Compatibilidade | Impacto se não for feita |
|---|---|---|---|
| P-E1 | `description`: usar frontmatter como fallback quando não houver manifesto | aditiva (só preenche o que hoje é vazio) | catálogo com 48 descrições vazias |
| P-E2 | Ler o campo `license` do frontmatter **como declaração** (nunca como permissão) e registrar `license.status: declared` com `redistribution_basis` apontando o arquivo/texto | aditiva; preserva o princípio "presença ≠ permissão" | 47 recursos "sem licença" que **têm** licença declarada no texto |
| P-E3 | Aceitar `metadata:` aninhado **ou** documentar a restrição e exigir manifesto para skills com versão | aditiva se for parser tolerante; neutra se for documentação | `alethe` v19 importada como 0.1.0; perda de autoria/tags |
| P-E4 | `source.derivedFrom[]` (projeto, url, commit, licença, transformação, remoções, data) — JSON na auditoria §7.3 | aditiva; leitores antigos ignoram chave desconhecida | cadeia de proveniência fora do contrato |
| P-E5 | Detecção de tipo por manifesto (`type: template|cli-tool|mcp-server|provider-model`) quando não houver marcador implícito | aditiva | perfis `.toml` e templates catalogados como `unknown`/`reference` |
| P-E6 | Derivar o nome da pasta do **caminho de origem** informado na importação, não do primeiro caminho com `/` | correção de comportamento (exige teste) | aviso espúrio em toda skill com subpastas |
| P-E7 | Popular `requirements` a partir de `compatibility` + inventário de dependências declarado | aditiva | risco/compatibilidade sem base estruturada |
| P-E8 | Camada `license.trademark` (ou `brand`) + recusa de exportação `shared`/`public` quando houver sinal distintivo de terceiro sem autorização registrada | aditiva ao modelo; muda política de exportação | redistribuição de marcas de terceiros (caso `alethe`) |

**Nenhuma destas propostas foi implementada.** Código de produção do Hub não foi alterado por esta pesquisa.

---

## 5. Como importar de verdade (roteiro para o responsável)

Pré-condição: checkout dos repositórios **nos commits exatos** de `sources.json`. Hashes só conferem se os bytes forem idênticos.

| Passo | Ação | Resultado esperado |
|---|---|---|
| 1 | Abrir o Hub (branch `arena/a92004be-lia-agenthub`, após revisão humana) e importar **uma** pasta: `Lia-Studio@203b60f:.agents/skills/lia-game-qa-plan` | relatório de importação com `capabilityId = lia-game-qa-plan-3bf0e9fe` |
| 2 | Comparar com o registro gerado | `id`, `contentHash` (`3aefa866…`) e `treeHash` (`f3ea0279…`) **idênticos** → o algoritmo reproduzido está correto |
| 3 | Conferir os avisos | 1 aviso de licença ausente; `description` vazia; `version` `0.1.0` (lacunas E-1/E-2 confirmadas em ambiente real) |
| 4 | Repetir para `alethe` e `lia-game-project-bootstrap` | `containsScripts: true` no primeiro; `NAME_FOLDER_MISMATCH` espúrio nos dois (E-6) |
| 5 | Importar as 46 restantes em lote, **sem promover** | 48 itens em Quarentena, invisíveis no índice (E-9, comportamento correto) |
| 6 | Decidir promoção **item a item** | só o que tiver licença resolvida (P-1 da auditoria) deve virar `ACTIVE` |
| 7 | Exportar uma skill adaptada como `.lia-capability` | verificar se `NOTICE`/`THIRD_PARTY_NOTICES.md` carregam o aviso MIT do upstream (convenção §7.4 da auditoria) |

**Critério de aceite da reprodução:** para os 48 registros, `id`, `contentHash` e `treeHash` idênticos aos gerados. Qualquer divergência invalida a ferramenta de pesquisa e deve ser registrada como erro deste documento — não como "diferença aceitável".

---

## 6. Diferenciação obrigatória de estados (regra do mandato)

| Estado | Definição aplicada aqui |
|---|---|
| **Encontrado** | o arquivo existe num repo/branch/commit identificado |
| **Analisado** | payload, frontmatter, licença e proveniência foram lidos; hashes calculados |
| **Catalogado** | registro completo **no formato do Hub** foi produzido (`docs/research/catalog/`) |
| **Aprovado para uso** | **nenhum** — exige decisão humana registrada |
| **Incorporado a um projeto Lia** | **nenhum por esta pesquisa** |

Uma skill **não** foi marcada como aprovada por ter sido encontrada ou catalogada. `trust: unreviewed` e `lifecycle: quarantined` foram preservados em **todos** os 48 registros exatamente por isso.

---

## 7. Classes de evidência deste relatório

| Afirmação | Classe |
|---|---|
| Contrato de dados, layout de armazenamento, algoritmo de hash, regras de validação e formato de pacote do Hub | **IMPLEMENTED** (código lido em `arena/a92004be-lia-agenthub@b4eb85f`) |
| 48 registros com `id`/`contentHash`/`treeHash` calculados | **EXECUTED** por ferramenta de pesquisa (`docs/research/tools/build-catalog-records.py`, Python 3 stdlib, Linux, entrada = payloads nos commits listados). **Não é VALIDATED**: o Hub não os produziu |
| Lacunas E-1…E-9 | **IMPLEMENTED-as-defect** (comportamento deduzido da leitura do código, com arquivo e linha; não reproduzido em execução) |
| Roteiro de importação (§5) | **PROPOSED** — não executado |
| Propostas P-E1…P-E8 | **PROPOSED** — nenhuma alteração de código foi feita |
| Informações sobre fontes externas | **RESEARCH** (API/fontes primárias, com data) |
| Qualquer execução em Windows | **não existe** — nenhuma validação Windows foi feita |
