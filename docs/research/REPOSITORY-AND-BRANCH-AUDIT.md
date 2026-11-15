# Auditoria de repositórios e branches — ecossistema Lia

**Documento:** `docs/research/REPOSITORY-AND-BRANCH-AUDIT.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch de trabalho:** `arena/a92004be-lia-agenthub`
**Base:** `main` @ `34a27f484e5f85987390a27fe7e0c0b3cd205bb2`
**Data da auditoria:** 2026-11-15 (UTC)
**Natureza:** leitura estática de objetos Git e da API do GitHub. **Nada foi executado, instalado, clonado para dentro do workspace, alterado ou integrado.**
**Cobre também o entregável do briefing `docs/research/ECOSYSTEM-AUDIT.md` e a matriz `docs/research/EXISTING-CAPABILITIES-MATRIX.md` (ver §9).**

---

## 0. Como ler este documento

### 0.1 Método

| Item | O que foi feito |
|---|---|
| Acesso | `git clone --filter=blob:none --no-checkout` em `/tmp/audit/*` (fora do workspace, não persistido) + GitHub API (`gh api`) |
| Histórico | `git fetch` de **todas** as refs de branch (`+refs/heads/*:refs/remotes/origin/*`) |
| Conteúdo | `git ls-tree -r`, `git show <ref>:<path>`, contagem de linhas/bytes |
| Execução | **Nenhuma.** Nenhum teste, build, `npm ci`, `python`, MCP ou CLI foi executado em nenhum repositório |
| Rede | GitHub API e busca web. **HTTP direto para sites de terceiros foi bloqueado neste sandbox** (ver `INTEGRATION-CANDIDATES.md` §1) |
| Limite | Contagem de arquivos vem de `git ls-tree`. Não houve auditoria linha a linha de 6.000+ arquivos; a inspeção foi dirigida aos módulos declarados no briefing e confirmados existentes |

### 0.2 Escala de estado (obrigatória em todo o projeto)

| Rótulo | Critério aplicado nesta auditoria |
|---|---|
| `IMPLEMENTED` | código identificado em commit/branch específico, com módulo localizável |
| `EXECUTED` | haveria prova de execução (log, artefato, relatório datado) no próprio repositório |
| `VALIDATED` | execução + evidência revisável na plataforma-alvo |
| `PROPOSED` | documento de proposta, sem código correspondente |
| `PLANNED` | item de roadmap declarado |
| `RESEARCH` | pesquisa/benchmark externo, sem implementação |
| `UNKNOWN` | não foi possível confirmar |

**Regra aplicada:** documentação extensa **não** promove estado. `main` de dois dos três repositórios é composta quase só de documentos — e isso está registrado como tal.

### 0.3 Achado estrutural que governa toda a leitura

Os três repositórios têm uma `main` **documental e rasa**, e uma branch de sessão com o código real, **não integrada**:

| Repositório | `main` (commits / arquivos) | Branch com código real | Commits à frente de `main` | Ancestral de `main`? | PR aberto? |
|---|---:|---|---:|---|---|
| `BloomRX/Lia-Studio` | 4 / 8 | `arena/01a0f4ab-lia-gamedev` @ `4868a18e` | **79** | **Não** | **#1 aberto** |
| `BloomRX/Lia-Forge` | 4 / 42 | `arena/649f88bd-3dspritesheet` @ `b0bb5e74` | **82** | **Não** | Não |
| `BloomRX/Lia-Project` | 349 / 5.756 | `arena/01a10290-lia-project` @ `0bf06292` | **203** | **Não** | Não (3 PRs anteriores fechados) |
| `BloomRX/Lia-AgentHub` | 1 / 7 | `arena/a92004be-lia-agenthub` (esta) | — | Sim | — |

`git merge-base --is-ancestor origin/main <branch>` retornou **NO** nos três casos: as branches de desenvolvimento **divergiram** de `main`, não são fast-forward. Portanto:

> **Nenhuma conclusão deste documento deve ser lida como "o produto tem X". A leitura correta é "a branch Y, no commit Z, contém o módulo W".**

---

## 1. Lia-Studio

### 1.1 Identidade e inventário

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/BloomRX/Lia-Studio` (público) |
| `main` | `ba70d224359b84a8e114f87b545d83f260f2deb1` — 2026-10-30 — *"docs: align Studio with Lia brand standards"* |
| Conteúdo de `main` | 8 arquivos: `AGENTS.md`, `README.md`, 2 `docs/`, 4 `planejamento/`. **Sem código.** |
| Branch de implementação | `arena/01a0f4ab-lia-gamedev` @ `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce` — 2026-11-15 00:43 UTC |
| Arquivos na branch | 179 |
| Linguagem / dependências | Python 3.9+ **stdlib apenas** no núcleo (`app/lia/`), SPA estática em `app/static/`, `desktop.py` opcional (WebView2) |
| Licença | MIT no código (`LICENSE`, "Copyright (c) 2026 BloomRX e colaboradores da Lia Studio"); marca fora da MIT — declarado em `THIRD_PARTY_NOTICES.md` |
| PR | **#1 aberto** `arena/01a0f4ab-lia-gamedev → main` |

Outras branches examinadas (todas de documentação/auditoria, nenhuma com código próprio):

| Branch | HEAD | Arquivos | Natureza |
|---|---|---:|---|
| `arena/studio-docs` | `095dbb04` | 32 | base documental das sessões |
| `arena/04710d54-lia-studio` | `f24fcb16` | 33 | **pesquisa transversal Agent 6 — Skills/MCP/ferramentas** |
| `arena/cf17bb1d-lia-studio` | `bf7f7cf8` | 179 | auditoria de segurança de runtime |
| `arena/327100c7-lia-studio` | `3e86c071` | 179 | auditoria de integração de engines (14 áreas) |
| `arena/3668aa2f-lia-studio` | `f91e5cb8` | 180 | auditoria de UI/UX |
| `arena/c00122c3-lia-studio` | `394a1273` | 180 | auditoria de gameplay/QA + homologação Windows |

### 1.2 O que está `IMPLEMENTED` na branch de desenvolvimento

Todos os caminhos abaixo foram lidos no commit `4868a18e`. Tamanhos em bytes/linhas são medidos, não estimados.

| Módulo | Tamanho | O que faz de fato | Classificação |
|---|---:|---|---|
| `app/lia/skills.py` | 8.400 B / 186 linhas | Biblioteca de Skills em `.agents/skills/<id>/SKILL.md` (distribuídas, read-only) + Skills do usuário em `projects/_skills/lia-user-<hex12>/`. Revisão SHA-256 por conteúdo; teto de 64 KB; **rejeita symlink**; catálogo leve lê só 8 KB de prefixo; parser de `description` sem YAML completo; mensagens de erro em pt-BR | `IMPLEMENTED` |
| `app/lia/tool_registry.py` | 4.897 B / 118 linhas | Tool Registry **declarativo** com 4 campos (`tool_id`, `origin`, `capabilities`, `requires_approval`, `potentially_paid`); `preflight_tool()` **puro, sem I/O**; retorna `blocked` / `awaiting_approval` / `policy_eligible`; valida tipos com `type(x) is`, rejeita catálogo vindo de Skills/texto | `IMPLEMENTED` (catálogo vazio por padrão: `entries: Tuple = ()`) |
| `app/lia/permissions.py` | 4.505 B / 101 linhas | `evaluate_permission()` puro: camadas Projeto → Profile → Task → Subtask; **negação vence em qualquer camada**; exige `capability ∈ task_requirements` **e** `∈ allow` em todas as camadas; valida todas as políticas antes de avaliar | `IMPLEMENTED` |
| `app/lia/runtime_policy.py` | 11.407 B / 222 linhas | Persistência de grants por projeto/task (`request`/`allow`/`deny`), revisão por hash, confirmação obrigatória (`confirmed is not True` → erro) | `IMPLEMENTED` |
| `app/lia/execution.py` | 4.849 B / 100 linhas | Execução **explicitamente SIMULADA**; resultado prefixado `[RESULTADO SIMULADO — nenhuma inferência real foi executada]` | `IMPLEMENTED` (como simulação) |
| `app/lia/agent_cli.py` | — | Transporte CLI experimental, validado **só com executável falso**; documenta que `--allowedTools` **não é sandbox** | `IMPLEMENTED` com escopo estreito |
| `.agents/skills/` | 16 Skills | 4 originais + 12 adaptadas de fontes MIT, com origem e licença citadas em cada `SKILL.md` | `IMPLEMENTED` |
| `tests/` | 26 arquivos (25 `test_*.py`) | Suíte ampla (`test_core`, `test_permissions`, `test_tool_registry`, `test_skills_progressive`, `test_dependency_layers`…) | `IMPLEMENTED` — **não executada nesta auditoria** |

### 1.3 O que **não** existe no Studio

| Item | Evidência | Classificação |
|---|---|---|
| Runtime de agente geral | `execution.py` simula; `agent_cli.py` sem rota/login/sessão real | `PLANNED` |
| MCP Registry / conexão MCP | campo `mcp_connection_ids` sempre vazio; nenhum servidor MCP no código | `PROPOSED` |
| Adapters de engine | `ENGINE-ADAPTER-ARCHITECTURE.md`; nenhum adapter implementado | `PROPOSED` |
| Validação real no Windows do shell desktop | `DESKTOP-WINDOWS-*` registram build/abertura, **não** aptidão para distribuição; 12 casos de symlink **não executados** | `EXECUTED` parcial, `VALIDATED` **não** |

### 1.4 O que o Studio já resolve bem e **não deve ser reimplementado**

1. **Negação como mecanismo, não como pedido** (`permissions.py`): negação vence, política malformada bloqueia, motivo não ecoa ID do chamador. É o melhor modelo de permissão do ecossistema hoje.
2. **Catálogo leve + corpo sob demanda** (`skills.py::_metadata`): só 8 KB por Skill no listar. É a implementação real de *progressive disclosure*.
3. **Rejeição de symlink na leitura de Skill**: barreira concreta contra escape de raiz.
4. **README honesto**: separa "implementado e aceito", "apenas simulado", "integrado mas não validado no Windows" e "o que cada aceite **não** significa". É o molde de comunicação do projeto inteiro.

### 1.5 Risco de duplicação e acoplamento

| Risco | Detalhe |
|---|---|
| **Alto** — segundo criador de Skills | O Studio já tem Workspace de Skills com editor e "duplicar para editar". Se o Hub criar um editor genérico, existirão **dois** editores. A diferença legítima: o do Studio é **escopado ao projeto** (teto 64 KB, sem proveniência, sem licença, sem empacotamento); o do Hub seria **de biblioteca** (proveniência, licença, versão, pacote). Essa diferença precisa ser explícita ou a duplicação é real |
| **Médio** — modelo de permissão | Se o Hub inventar um segundo vocabulário de capabilities, os grants do Studio não conversam. O Hub deve **referenciar** capability IDs, não definir política |
| **Baixo** — execução | O Studio já declara que não executa; o Hub também não deve. Sem conflito |

---

## 2. Lia-Forge

### 2.1 Identidade e inventário

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/BloomRX/Lia-Forge` (público) |
| `main` | `6bd9a5a7006c7c6ccf5edcb5d577283d61a39949` — 2026-11-13 — *"Documenta auditoria local de materiais Blender"* |
| Conteúdo de `main` | **42 arquivos, 100 % documentação.** `grep -c "^shared/"` = **0** |
| Branch de implementação | `arena/649f88bd-3dspritesheet` @ `b0bb5e74e41c3d149018261b8e494616ef578bd8` — 2026-11-15 00:46 UTC |
| Arquivos na branch | 222 |
| Stack | Electron + React/Vite (E SM `shared/`, `electron/`), launcher Python de desenvolvimento, MCP server Node |
| Licença | MIT (código) + `THIRD_PARTY_NOTICES.md` |
| `npm test` | 41 arquivos `*-smoke.mjs/cjs` encadeados (47 em `tests/`) — **não executados nesta auditoria** |

Outras branches:

| Branch | HEAD | Arquivos | Natureza |
|---|---|---:|---|
| `arena/6113e868-lia-forge` | `3aabf999` | 43 | auditoria de agentes, Skills, MCP, automação |
| `arena/624582f5-lia-forge` | `76b1b244` | 47 | limpeza de histórico + generalização de nomes de terceiros |
| `arena/ca5fcc8f-lia-forge` | `6aee1946` | 43 | avaliação técnica da frente Blender |
| `arena/e209a742-lia-forge` | `84aeca48` | 43 | auditoria da lacuna Three.js |
| `arena/ee48e1c5-lia-forge` | `a4fc756e` | 208 | auditoria de UI (27 arquivos em `shared/`) |

### 2.2 O que está `IMPLEMENTED` na branch de desenvolvimento

Esta é a **implementação mais avançada do ecossistema em matéria de "capacidade"** e é a principal referência arquitetural para o Hub.

| Módulo | O que faz | Relevância para o Hub |
|---|---|---|
| `shared/capabilities/registry.mjs` | Catálogo versionado de capacidades, **puro**, sem conhecer ferramentas. `status ∈ {implemented, partial, proposed, planned}`; `requirements {os,gpu,vramMb,ramMb,diskMb,network,runtimes,tools}` com **`null` = não medido, nunca zero inventado** | **Modelo de estado de capacidade** que o Hub deve herdar |
| `shared/hub/provider-hub.mjs` | Resolve capacidade → adapter → ferramenta; estados `ready / unknown / blocked / missing`; ordem `ready > unknown > missing > blocked`; empate → local antes de remoto; `detail` explica o bloqueio | Modelo de **resolução e ranking** reutilizável |
| `shared/adapters/sdk.mjs` | Manifesto de 15 campos, 3 classes (`local-tool`, `internal-process`, `remote-service`), 9 códigos de erro, ações protegidas, custo/licença explícitos | **Contrato de adapter** — o Hub deve usar o mesmo vocabulário |
| `shared/engine/{dag,gates,run-authorization,run-states,execution-manager}.mjs` | DAG, gates, autorização de run, máquina de estados | Referência; **execução não pertence ao Hub** |
| `shared/fs/path-containment.mjs` + `tests/path-containment-smoke.mjs` | Contenção de caminho | **Padrão de segurança obrigatório** para o Hub |
| `shared/http/api-policy.mjs`, `tests/http-bind-smoke.mjs` | Política de bind/HTTP local | Referência para API local opcional |
| `shared/qa/{preflight,spritesheet,validators,png}.mjs` | Validadores de artefato | Não é escopo do Hub |
| `scripts/spriteforge-mcp.mjs` | **Servidor MCP real** (stdio), tools `spriteforge_*`, `mcp-install` para claude/codex/opencode | **O único MCP de primeira parte do ecossistema.** O Hub deve saber catalogá-lo, não substituí-lo |
| Caminhos | `SPRITEFORGE_PROJECT_ROOT`, `LIA_HOME`, `%USERPROFILE%\Lia\Forge`, `%LOCALAPPDATA%\Lia\Modelos`, `%APPDATA%\Lia\Forge\config\model-license-acceptances.json` | **Implementação real do padrão `Lia\` do kit** |

### 2.3 Documentação estratégica do Forge (não é implementação)

| Documento | Estado declarado | Uso para o Hub |
|---|---|---|
| `docs/TOOL-PROVIDER-HUB.md` | *"parcialmente implementado (T13)"* | Vocabulário Tool/Provider/Adapter/Plugin/Workflow/Skill/Agent — **adotar** |
| `docs/SKILLS-KNOWLEDGE-ENGINE.md` | *"alvo `PLANNED`"* | Já propõe **manifesto de skill** com `source {upstream, commit, author, contentHash}`, `license {id,url,reviewedAt}`, `trust {reviewed-external, first-party, user-provided, unreviewed}` — **é praticamente o registro que o Hub precisa** |
| `docs/CAPABILITY-BOUNDARIES-AND-ROADMAP.md` | `PROPOSED` | Classificação nativa/provider/adapter/backend/destino; princípio anti-duplicação |
| `docs/STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md` | `PROPOSED` | Registra decisão do Dev: *"Studio decide o jogo; Forge produz assets para qualquer consumidor"*; e **`REQUIRES_HUMAN_DECISION` para o protocolo entre apps** |
| `docs/PROVIDER-AND-MODEL-ADMISSION-POLICY.md`, `ADR-001` | normativo interno | Política de admissão de provider — o Hub deve **referenciar**, não redefinir |

### 2.4 O que **não** existe no Forge

- Integração real com Blender/ComfyUI **validada**: existem adapters e testes, mas o README declara que build/UI da fatia e execução Blender real **não foram validados** no sandbox; nenhum `.exe` produzido ou assinado.
- Catálogo/índice compartilhado de pesos: **não existe**; `models` vazio de propósito.
- Descoberta compartilhada da marca (`%APPDATA%\Lia\lia.json`, `HKCU\Software\Lia`): **proposta do kit, não implementada**.
- Protocolo Studio↔Forge: **`REQUIRES_HUMAN_DECISION`**, explicitamente.

### 2.5 Risco de duplicação

| Risco | Detalhe |
|---|---|
| **Alto** — Capability Registry próprio | O Forge já tem registry + hub + adapter SDK funcionando. Um "registry do Hub" que ignore esses contratos cria o terceiro vocabulário. **Mitigação:** o Hub deve emitir registros **compatíveis** com o vocabulário do Forge (mesmos estados, `null` para não medido, classes de adapter) |
| **Alto** — gestão de modelos/pesos | Já existe downloader com trava, SHA-256, aceite de licença em `%APPDATA%`. O Hub **não** deve criar um segundo gerenciador |
| **Médio** — catálogo de providers | `PROVIDER-AND-MODEL-ADMISSION-POLICY` é do Forge. O Hub pode catalogar *metadados públicos* de modelos, nunca política de admissão |

---

## 3. Lia-Project (a Waifu)

### 3.1 Identidade e inventário

| Campo | Valor |
|---|---|
| Repositório | `https://github.com/BloomRX/Lia-Project` (público) — **é a Waifu**, nome histórico |
| `main` | `9c7ac183fd54b8eae0425038190a2c56ec237ff8` — 2026-10-30 — 349 commits, **5.756 arquivos** |
| Branch de desenvolvimento | `arena/01a10290-lia-project` @ `0bf06292` — 2026-11-14 19:02 UTC — 6.189 arquivos (**203 commits à frente**) |
| Stack | Electron/TypeScript (`lia/`, `airi/`), TypeScript |
| Tamanho do repo | ~366 MB |
| PRs | #1, #2, #3 — **fechados** |

Outras branches:

| Branch | HEAD | Arquivos | Natureza |
|---|---|---:|---|
| `arena/826a33f1-lia-project` | `16c97fd4` | 14 | pesquisa de modelos/providers + recursos em desktop |
| `agents/docs` | `7913c62a` | 8 | snapshot documental curado |
| `codex/lia-multi-provider-voice` | `fd0451d7` | 6.190 | arquitetura de voz multi-provider |
| `docs/especificacao-geral-produto-lia` | `b2745f71` | 5.840 | especificação geral alinhada à independência |
| `arena/18f50ae7` | `4acd20e6` | 6.275 | matriz beta + QA de áudio |
| `arena/250b337a` | `dd8dc0ca` | 6.220 | correções de fase 1 |
| `arena/4ec8f22b` | `2eabc52b` | 6.190 | higiene de build/lint |
| `arena/c6b02f64` | `0093de09` | 6.198 | correções de segurança do beta |
| `qa/windows-benchmarks` | `91b8995a` | 20 | benchmarks Windows |

### 3.2 Descobertas relevantes para o Hub

O documento mais valioso do ecossistema para o modelo de dados está aqui, **em branch**, não em `main`:

`docs/research/lia-capability-catalog/` (branch `arena/01a10290`, base `29999aff`, 11/11/2026):

| Documento | Linhas | Contribuição |
|---|---:|---|
| `01-ESTADO-DA-ARQUITETURA.md` | 108 | Escala de 5 estados; inventário de capacidades do Brain (`LiaBrainCapabilities`, 9 booleanos), engine registry, catálogo de 10 providers, cofre de credenciais, memória |
| `02-CATALOGO-MESTRE.md` | — | Catálogo de modelos/pesos/runtimes/providers com licença **por camada**; regra explícita "*`?` significa não confirmado, não é sim*"; VRAM por aritmética, **não** benchmark |
| `03-ESQUEMA-E-DADOS.md` | 510 | **Separação em 8 camadas**: Capability / Model / Weights / Runtime / Provider / Adapter / Configuration / Routing policy — cada uma com dono diferente. Taxonomia `dominio.acao`. **7 estados de ciclo de vida mutuamente exclusivos** (`catalogued → installable → installed → configured → …`) |
| `04-MATRIZES-E-PRIORIDADES.md` | — | Matrizes de decisão |

Outros módulos relevantes (`IMPLEMENTED`, na branch de desenvolvimento): `brain/types.ts` (contrato de 9 capacidades), `brain/capabilities.ts` (elegibilidade pura), `brain/engine-registry.ts`, `shared/lia/provider-catalog.ts` (10 providers curados), `secrets/vault.ts` (lease privada do processo dono; renderer nunca recebe a chave), memória lexical sem embeddings (`memory-context.ts`).

### 3.3 Por que isso importa para o Hub

1. **A separação em 8 camadas é o antídoto correto contra o erro que o Hub cometeria:** tratar "modelo", "pesos", "runtime", "provider" e "adapter" como a mesma coisa. O Hub deve adotar esse vocabulário; inventar outro seria duplicação pura.
2. **Os 7 estados de ciclo de vida** já resolvem "listado ≠ instalado ≠ configurado" — exatamente a distinção que o Hub precisa para não mentir sobre o que existe.
3. **A memória da Waifu é do usuário e é privada.** `AGENTS.md` do kit e o glossário são explícitos: nunca entra em repositório; nunca cruza para outro app sem opt-in por categoria. O Hub **não** deve propor capturar memória de convivência.
4. **O cofre de credenciais é do host** (`secrets/vault.ts`). Confirma a regra do briefing: o Hub não é cofre central.

### 3.4 Risco de duplicação

| Risco | Detalhe |
|---|---|
| **Alto** — vocabulário de capability | Se o Hub definir `capability` diferente de `LiaBrainCapabilities` / taxonomia `dominio.acao`, os produtos passam a falar línguas diferentes |
| **Médio** — catálogo de modelos | Project já tem catálogo mestre com licença por camada. O Hub deve **importar/consumir** esse formato, não criar um paralelo |
| **Proibido** — memória | Memória de convivência é dado privado do usuário; fora de escopo do Hub |

---

## 4. Lia-AgentHub (este repositório)

| Campo | Valor |
|---|---|
| `main` | `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` — *"Kit Marca Lia"* — **1 commit** |
| Arquivos | `AGENTS.md`, `README.md`, `docs/{BRANCH-AND-RELEASE-FLOW,DECISION-REGISTER,PHASE-0-ARENA-BRIEF,PRODUCT-VISION}.md`, `docs/KIT-PROJETO-NOVO.zip` |
| Branch desta sessão | `arena/a92004be-lia-agenthub` |
| Código de produto | **Nenhum.** Correto para a Fase 0 |

O `KIT-PROJETO-NOVO.zip` **está presente e foi lido integralmente** nesta sessão (25 arquivos; 60.924 B comprimido / 117.176 B descomprimido). Conteúdo confirmado: `LEIA-ME.md`, `APP-WINDOWS/{GUIA-APP-NOVO, PADRAO-DA-MARCA, GLOSSARIO}.md`, `APP-MOBILE-OU-WEB/{GUIA-APP-NOVO, PADRAO-MOBILE-WEB, GLOSSARIO}.md`, e `arquivos-prontos/` com `CLAUDE.md`, `AGENTS.md`, `ONDE-VAI-CADA-ARQUIVO.md`, `gitignore-acrescentar.txt`, `memory-bank--{estado,padroes,decisoes}.md`, `rule-exemplo--interface.md`, `skill-exemplo--SKILL.md`.

---

## 5. Matriz de lacunas confirmadas

Lacunas **transversais** — nenhum dos três produtos as cobre hoje:

| # | Lacuna | Evidência da ausência | Consequência |
|---|---|---|---|
| L-01 | **Formato de registro de capacidade com proveniência** (fonte, commit, autor, hash, licença por camada, revisor, data) | Studio: sem proveniência (só SHA-256 do conteúdo). Forge: **propõe** em `SKILLS-KNOWLEDGE-ENGINE` (`PLANNED`), não implementa. Project: catálogo de modelos tem licença, mas não para Skills | Terceiro recurso importado não tem cadeia de custódia |
| L-02 | **Pipeline de intake/inspeção** de conteúdo externo | Cada produto tem regra em prosa ("conteúdo externo é não confiável"); nenhum tem verificador executável | Regra sem mecanismo |
| L-03 | **Formato de pacote portátil** exportável | Studio exporta projeto (manifesto do índice). Forge exporta pacote de assets. **Nenhum exporta "capacidade"** | Não há como levar uma Skill de um produto para outro com metadados |
| L-04 | **Análise de licença** | `THIRD_PARTY_NOTICES.md` preenchido à mão, por produto | Licença de dependência transitiva não é verificada |
| L-05 | **Contrato de distribuição entre apps** | Forge: `REQUIRES_HUMAN_DECISION`. Studio: preview de brief, `sent: False`. Project: nenhum | Cada integração seria artesanal |
| L-06 | **Detecção de conteúdo malicioso em prosa** (Unicode invisível, instrução de exfiltração) | Não existe em nenhum dos três | Superfície de ataque conhecida e não coberta |
| L-07 | **Versionamento de capacidade** com semver + hash + changelog + diff | Studio: revisão por hash de conteúdo, sem semver. Forge: `version` no manifesto de adapter | Atualização não é comparável nem reversível |
| L-08 | **Registro de MCP como recurso catalogado** (fonte, comando, variáveis de ambiente *por nome*, capabilities declaradas) | Studio: nenhum MCP. Forge: um servidor MCP próprio, sem catálogo | Não há lugar para "avaliar um MCP antes de conectar" |

**L-01 a L-08 são exatamente o escopo defensável do Agent Hub.** Note o que **não** está na lista: executar Skills, orquestrar agentes, produzir assets, rotear modelos. Isso confirma a fronteira do briefing.

---

## 6. Sobreposições a eliminar (ou a não criar)

| Sobreposição | Onde já existe | Regra proposta |
|---|---|---|
| Catálogo de Skills | Studio `skills.py` + `.agents/skills/` | O Studio continua dono do catálogo **do projeto**. O Hub é dono da **biblioteca** e do **pacote**. O Studio importa pacote; não vira cliente de API |
| Modelo de capability | Forge `capabilities/registry.mjs`; Project `03-ESQUEMA-E-DADOS.md` | **Adotar o vocabulário existente.** Zero vocabulário novo |
| Estado de disponibilidade | Forge `ready/unknown/missing/blocked`; Project `catalogued/installable/installed/configured` | Hub usa `trust` + `lifecycle` **derivados** desses dois, sem redefinir |
| Permissões | Studio `permissions.py` | Hub **não** define política de execução. Só declara *permissões requeridas* como metadado |
| Adapter/provider | Forge `adapters/sdk.mjs` | Hub referencia; não implementa adapter de execução |
| Servidor MCP | Forge `spriteforge-mcp.mjs` | Hub cataloga; não substitui |
| Cofre de credenciais | Project `secrets/vault.ts` | Hub **nunca** guarda segredo. Só nome de variável |
| Gerenciador de pesos | Forge downloader | Fora de escopo do Hub |

---

## 7. Fatos que a auditoria **não** estabelece

Listados explicitamente para impedir que sessões futuras os tratem como verdade:

1. **Nenhum teste foi executado.** Nem `npm test` (Forge), nem `python -m unittest` (Studio), nem qualquer verificação do Project. As suítes *existem*; o resultado é `UNKNOWN` nesta sessão.
2. **Nenhuma validação em Windows foi observada diretamente.** O que existe são relatórios datados (`ALPHA-*-WINDOWS-*.txt`, `DESKTOP-WINDOWS-*`) produzidos por outras sessões/máquinas. São `EXECUTED` segundo o próprio relatório, não re-verificados aqui.
3. **`main` do Studio e do Forge não contém código.** Qualquer afirmação "o Studio faz X" refere-se a `arena/01a0f4ab-lia-gamedev`; "o Forge faz Y" refere-se a `arena/649f88bd-3dspritesheet`.
4. **As branches divergiram de `main`.** Não são fast-forward; uma futura integração exigirá reconciliação, não merge trivial.
5. **O Lia-Project tem ~366 MB e 6.189 arquivos na branch de desenvolvimento.** A inspeção foi dirigida, não exaustiva. Partes do produto (Stage, voz, áudio) não foram auditadas porque não tocam o escopo do Hub.
6. **O PR #1 do Studio está aberto e não foi revisado nesta sessão.** Não se sabe se será integrado.

---

## 8. Conclusões da auditoria

1. **Existe duplicação real de conceitos, não de código.** Três produtos implementaram ou propuseram "capacidade", "registro" e "estado" com formas incompatíveis. Isso justifica uma camada compartilhada.
2. **O código mais maduro de "capacidade" está no Forge** (`registry.mjs` + `provider-hub.mjs` + `adapters/sdk.mjs`), e o **modelo de dados mais maduro está no Project** (`03-ESQUEMA-E-DADOS.md`). O Hub deve **consolidar os dois**, não competir com eles.
3. **O código mais seguro está no Studio** (`permissions.py`, `tool_registry.py`, `skills.py`): funções puras, sem I/O, negação prevalecente, rejeição de symlink. É o padrão de qualidade que o núcleo do Hub deve igualar.
4. **As oito lacunas transversais (L-01…L-08) não são atendidas por nenhum produto e são atendíveis sem executar nada.** Este é o núcleo do MVP proposto em `docs/product/MVP-AND-ROADMAP.md`.
5. **O que o Hub não deve fazer está inequívoco nos três repositórios:** não orquestrar (Studio), não executar (Studio declara que não executa), não produzir assets (Forge), não rotear modelos (Project), não guardar credenciais (Project já tem cofre), não gerenciar pesos (Forge já tem downloader).

---

## 9. Mapa de entregáveis e rastreabilidade

| Entregável pedido no briefing da Fase 0 | Onde está neste trabalho |
|---|---|
| `ECOSYSTEM-AUDIT.md` | **este documento** |
| `EXISTING-CAPABILITIES-MATRIX.md` | §1.2, §2.2, §3.2 (tabelas por módulo) + §5 (lacunas) |
| `EXTERNAL-ECOSYSTEM-RESEARCH.md` | `docs/research/INTEGRATION-CANDIDATES.md` |
| `PRODUCT-BOUNDARIES.md` | `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §1–§4 |
| `CAPABILITY-DATA-MODEL.md` | `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §6 |
| `SECURITY-AND-TRUST-MODEL.md` | `docs/architecture/SECURITY-AND-TRUST-MODEL.md` |
| `DISTRIBUTION-CONTRACTS.md` | `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §8 + `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` §5 |
| `MVP-AND-ROADMAP.md` | `docs/product/MVP-AND-ROADMAP.md` |
| `DECISION-REGISTER.md` | atualizado em `docs/DECISION-REGISTER.md` |

---

## Referências desta auditoria

**Repositórios (consultados 2026-11-15 UTC):**
- `https://github.com/BloomRX/Lia-Studio` — `main` `ba70d224359b84a8e114f87b545d83f260f2deb1`; `arena/01a0f4ab-lia-gamedev` `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce`; `arena/04710d54-lia-studio` `f24fcb16c6f9a2c44442b83e3cc066e82181b2f5`
- `https://github.com/BloomRX/Lia-Forge` — `main` `6bd9a5a7006c7c6ccf5edcb5d577283d61a39949`; `arena/649f88bd-3dspritesheet` `b0bb5e74e41c3d149018261b8e494616ef578bd8`
- `https://github.com/BloomRX/Lia-Project` — `main` `9c7ac183fd54b8eae0425038190a2c56ec237ff8`; `arena/01a10290-lia-project` `0bf0629263ba2c030efe07fc070283a4e025467a`; `arena/826a33f1-lia-project` `16c97fd486229ea43c294fcf09b8781a6932415f`
- `https://github.com/BloomRX/Lia-AgentHub` — `main` `34a27f484e5f85987390a27fe7e0c0b3cd205bb2`

**Arquivos citados (caminho na branch indicada):**
- Studio: `app/lia/{skills,tool_registry,permissions,runtime_policy,execution,providers,agent_cli}.py`, `tests/*.py`, `.agents/skills/README.md`, `docs/{README,AI-AGENTS-ARCHITECTURE,AI-INTEGRATION-CATALOG,DECISOES-PENDENTES-INTEGRACOES}.md`, `THIRD_PARTY_NOTICES.md`
- Forge: `shared/capabilities/registry.mjs`, `shared/hub/provider-hub.mjs`, `shared/adapters/sdk.mjs`, `shared/engine/*.mjs`, `shared/fs/path-containment.mjs`, `scripts/spriteforge-mcp.mjs`, `docs/{TOOL-PROVIDER-HUB,SKILLS-KNOWLEDGE-ENGINE,CAPABILITY-BOUNDARIES-AND-ROADMAP,STUDIO-FORGE-CONSISTENCY-ARCHITECTURE,lia-ecosystem-integration}.md`, `README.md`
- Project: `docs/research/lia-capability-catalog/{01,02,03,04}-*.md`, `docs/architecture/{LIA-AGENT-CONSUMPTION-AUDIT,AGENT-SKILLS-AUDIT-*}.md`, `docs/project/{AGENT-SKILLS,AGENT-ORCHESTRATION}.md`
