# Inventário de Skills e capacidades dos projetos Lia

**Documento:** `docs/research/LIA-SKILLS-INVENTORY.md` (Missão 1)
**Agente:** Research — Lia Agent Hub
**Branch de trabalho:** `arena/db625478-lia-agenthub` (base `main` @ `34a27f484e5f85987390a27fe7e0c0b3cd205bb2`)
**Data da inspeção:** 2026-11-15 (UTC)
**Método:** somente leitura. Listagem de árvores via GitHub API, download de tarball/clone esparso para inspeção estática, leitura de arquivos e cálculo de hashes. **Nenhuma Skill, script ou comando de terceiros foi executado. Nada foi instalado. Nenhum payload foi copiado para este repositório.**

---

## 1. Resumo executivo

| Achado | Número | Onde |
|---|---:|---|
| Pastas de Agent Skills prontas para catálogo (formato `SKILL.md`) | **48** | Studio 16 · Project 22 · Model-Lab 9 · Forge 1 |
| Dessas, autorais/adaptadas pela Lia | **47** | — |
| Dessas, terceiro vendorizado com patches locais | **1** (`alethe`) | Lia-Project |
| Skills vendadas do upstream AIRI dentro do Lia-Project | **29** | `airi/.agents/skills/` (28) + `airi/integrations/minecraft/codex-skills/` (1) |
| Skills de terceiros num pacote ZIP guardado no Lia-Studio | **20** | `docs/Mr-Mak-Skills-Free.zip` (764 arquivos, não importado) |
| Perfis de agente Codex (não são Skills) | **7** | Lia-Model-Lab `.codex/agents/*.toml` |
| Capacidades de produção registradas em código (não são Skills) | **49** | Lia-Forge `shared/capabilities/registry.mjs` (16 implemented · 5 partial · 5 proposed · 24 planned) |
| Ferramentas MCP implementadas num produto Lia | **10** | Lia-Forge `scripts/spriteforge-mcp.mjs` (servidor `lia-forge`) |
| Registros de catálogo de modelos/pesos já existentes | **44** catalogados · ~131 descobertos · **0** validados | Lia-Project `docs/research/lia-capability-catalog/` |
| Skills em `main` de qualquer repositório Lia | **9** (só Lia-Model-Lab) | todas as outras vivem em branches não integradas |

**Três conclusões que atravessam o inventário:**

1. **O ecossistema Lia já tem 47 capacidades autorais/adaptadas em formato Agent Skills** — o Hub não nasce com catálogo vazio. Mas **quase nada está em `main`**: Studio, Project e Forge mantêm Skills apenas em branches de sessão. Existência em branch não integrada **não** é presença em `main`.
2. **Nenhuma dessas 47 pastas carrega licença dentro do payload.** Só `alethe` tem `LICENSE` próprio. O Hub detecta licença **apenas por arquivo na raiz do payload** (`adapters/importer.py::_detect_license`), portanto as 47 entrariam como `licenseKnown: false` — ver §7 e o relatório de importação.
3. **Há duplicação real e não decidida:** `lia-brand-check` (Forge) e `lia-brand-consistency-review` (Model-Lab) fazem o mesmo trabalho de revisão de marca; `lia-agent-orchestration` (Project), `multi-agent-orchestration` (Model-Lab) e `alethe` (terceiro) sobrepõem-se em orquestração. Consolidar é decisão de produto, não de pesquisa.

---

## 2. Critério de classificação (o que é Skill e o que não é)

Nem todo arquivo de instrução é uma Skill. Critério aplicado, derivado da especificação Agent Skills (`agentskills.io/specification`, consultada em 2026-11-15) e do validador implementado no Hub (`src/lia_agenthub/domain/skills.py`):

| Classe | Teste objetivo | Tratamento no Hub |
|---|---|---|
| **Agent Skill** | pasta com `SKILL.md` e frontmatter `name` + `description` | `type: agent-skill` — catalogável hoje |
| **Instrução de projeto** | `AGENTS.md`, `CLAUDE.md`, `.claude/rules/*.md`, `docs/AGENTS.md` — sempre carregado, sem ativação por descrição | **não** é Skill; no máximo `type: reference` |
| **Perfil de agente** | `.codex/agents/*.toml` (nome + instruções + skills referenciadas) | **não** é Skill; candidato a tipo próprio (lacuna do modelo, ver §7) |
| **Workflow/pipeline** | grafo executável (`electron/workflow-*.cjs`, `shared/engine/*`) | **não** é Skill; é runtime do host |
| **Template** | documento modelo sem `SKILL.md` (`templates/MODEL-CARD.md`) | catalogável como `type: template`; quando está dentro de uma Skill, é payload dela |
| **Ferramenta/CLI/servidor** | código executável (`tools/project_cli.py`, `scripts/spriteforge-mcp.mjs`) | `type: cli-tool` / `mcp-server`; exige análise de risco própria |
| **Registro de capacidades** | catálogo em código/JSON (`registry.mjs`, `catalog.data.json`) | **não** é Skill; é dado de outro produto |
| **Documentação/pesquisa** | relatórios, matrizes, auditorias | referência; não catalogar como capacidade |

---

## 3. Exatidão da inspeção — repositórios, branches e commits

| Repositório | Branch inspecionada | Commit | Data do commit | Como foi inspecionado |
|---|---|---|---|---|
| `BloomRX/Lia-Studio` | `arena/01a0f4ab-lia-gamedev` | `203b60f17d177f7faf79d293b95f078d0d0a729a` | 2026-11-15T04:46:37Z | tarball codeload, leitura estática |
| `BloomRX/Lia-Studio` | `arena/3668aa2f-lia-studio` | (mesmo conjunto de Skills) | — | árvore via API |
| `BloomRX/Lia-Studio` | `main` | — | — | árvore via API: **8 arquivos, nenhuma Skill** |
| `BloomRX/Lia-Project` | `arena/c6b02f64-lia-project` | `0093de090d86c291b7a85eaeacebe0a559585359` | 2026-11-14T19:07:16Z | clone esparso `--filter=blob:none` (`.agents`, `docs`, `tools`, `Tests`) |
| `BloomRX/Lia-Project` | `codex/lia-ui-ux-fase-1` | `e72574e8d743986a2eee8eeec41f80350bd470d8` | 2026-11-15T05:42:29Z | árvore via API: mesmo conjunto de 22 |
| `BloomRX/Lia-Project` | `docs/especificacao-geral-produto-lia` | `b2745f716d` | 2026-10-30T05:42:28Z | árvore via API: subconjunto de 6 Skills |
| `BloomRX/Lia-Project` | `main` | `9c7ac183fd` | 2026-10-30T05:41:59Z | árvore via API: **sem `.agents/` na raiz**; 29 Skills vendadas em `airi/` |
| `BloomRX/Lia-Model-Lab` | `main` | `3ec4313ba57ec94a7f3d93ec4f7a0d533d5077cf` | 2026-11-03T01:34:12Z | tarball codeload |
| `BloomRX/Lia-Model-Lab` | `arena/skills-model-lab` | `9b99756a7aaea25ed3c891a101de3bb766470494` | 2026-10-30T05:40:54Z | tarball codeload (mesmo conjunto) |
| `BloomRX/Lia-Forge` | `arena/649f88bd-3dspritesheet` | `35b207f7b1ae5bc0c104fbdd0e9cf6ae83944692` | 2026-11-15T02:11:52Z | tarball codeload |
| `BloomRX/Lia-Forge` | `main` | — | — | árvore via API: **42 arquivos, nenhuma Skill** |
| `BloomRX/Lia-Go` | `main` / `arena/f1ac5ed6-lia-go` | — | — | árvore via API: `.agents/skills/.gitkeep` (placeholder vazio) |
| `BloomRX/Lia-AgentHub` | `arena/a92004be-lia-agenthub` | `b4eb85f` (a branch avançou para `704dfd3f` durante a sessão) | 2026-11-15 | tarball codeload: o próprio Hub (modelo de dados lido aqui) |
| `BloomRX/Lia-AgentHub` | `arena/b6febe41-lia-agenthub` | — | 2026-11-15 | árvore via API: branch de UI/UX (`docs/design/*`) — **não tocada** |

Também verificados e **sem** Skills em `main`: `LiaVoiceStudio` (só `AGENTS.md`), `3d-create`, `3d-sprite`, `ChibiCreate`, `ComfyUI_Colab`, `SilksongREA`, `animations-free` — repositórios de assets/conteúdo. Limitação: para esses, apenas `main` foi listado; branches de sessão não foram varridas.

---

## 4. Lia Studio — 16 Skills (`arena/01a0f4ab-lia-gamedev` @ `203b60f`)

Convenção canônica declarada em `.agents/skills/README.md`: `.agents/skills/<id>/` compatível com Agent Skills; `.claude/skills/` só como *junction* local no Windows, ignorada pelo Git; cada Skill tem uma responsabilidade e aponta para as outras. O README é explícito: **"Skills são opcionais e combináveis, não papéis de Agent nem capacidades concedidas"** e **"a biblioteca do Studio permite consultá-las, mas ainda não as aplica por um runtime"**.

Estado de todas: **IMPLEMENTED como instrução versionada; nenhuma EXECUTED por runtime** (não há runtime de Skills no Studio; `app/lia/skills.py` apenas lista/duplica).

| Skill | Função declarada | Origem | Payload | Compatibilidade declarada | Reuso potencial | Id calculado |
|---|---|---|---|---|---|---|
| `lia-game-audio-plan` | Planejar banco de sons e eventos verificáveis sem gerar, baixar ou instalar áudio. | Adaptada (MIT) | 1 arq. / 1814 B | nenhuma declarada | Lia-Forge (audio/VFX/UI de asset), Lia-Project (revisao visual) | `lia-game-audio-plan-c5a95aba` |
| `lia-game-balance-review` | Analisar dados de combate, economia e progressão sem inventar métricas ou alterar valores. | Adaptada (MIT) | 1 arq. / 1747 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-balance-review-377a41f7` |
| `lia-game-bug-triage` | Classificar bugs de jogo por reprodução, impacto e evidência sem fechá-los automaticamente. | Adaptada (MIT) | 1 arq. / 1732 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-bug-triage-09484de7` |
| `lia-game-design-review` | Revisar a coerência e verificabilidade de um documento de design de jogo sem aprovar uma fase. | Adaptada (MIT) | 1 arq. / 1826 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-design-review-a62f237f` |
| `lia-game-level-design` | Preparar layout revisável de fase e contrato de integração, sem presumir cena implementada. | Adaptada (MIT) | 1 arq. / 1823 B | nenhuma declarada | Lia-Forge (audio/VFX/UI de asset), Lia-Project (revisao visual) | `lia-game-level-design-9ea257b2` |
| `lia-game-playtest-report` | Organizar observações reais de playtest, separando feedback humano de hipótese ou simulação. | Adaptada (MIT) | 1 arq. / 1756 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-playtest-report-169d003f` |
| `lia-game-project-bootstrap` | > | Original Lia | 8 arq. / 19151 B | nenhuma declarada | Lia-Go (bootstrap de projeto), Lia-Forge (brief de asset), Lia-AgentHub (exemplo de skill com templates/) | `lia-game-project-bootstrap-4d1c8510` |
| `lia-game-qa-plan` | Planejar verificações de lógica, integração, interface e gameplay por Task, sem fingir teste executado. | Adaptada (MIT) | 1 arq. / 1784 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-qa-plan-3bf0e9fe` |
| `lia-game-story-readiness` | Verificar se uma Task de jogo pode ser iniciada sem pressupor que será executada ou aprovada. | Adaptada (MIT) | 1 arq. / 1830 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-story-readiness-028a61fe` |
| `lia-game-test-evidence-review` | Revisar qualidade, proveniência e cobertura de testes e evidências de jogo sem abrir gates. | Adaptada (MIT) | 1 arq. / 1814 B | nenhuma declarada | Lia-Project (QA/regressao), Lia-Forge (revisao de asset), Lia-Go (revisao documental) | `lia-game-test-evidence-review-9c629b6c` |
| `lia-game-ui-plan` | Planejar HUD e menus a partir de estado real do jogo e revisar acessibilidade. | Adaptada (MIT) | 1 arq. / 1780 B | nenhuma declarada | Lia-Forge (audio/VFX/UI de asset), Lia-Project (revisao visual) | `lia-game-ui-plan-5fea1856` |
| `lia-game-vfx-plan` | Definir intenção, gatilhos e ciclo de vida de efeitos visuais antes da integração na engine. | Adaptada (MIT) | 1 arq. / 1791 B | nenhuma declarada | Lia-Forge (audio/VFX/UI de asset), Lia-Project (revisao visual) | `lia-game-vfx-plan-d3096c0e` |
| `lia-game-visual-review` | Planejar e revisar comparações visuais de gameplay com evidência nativa quando disponível. | Adaptada (MIT) | 1 arq. / 1790 B | nenhuma declarada | Lia-Forge (audio/VFX/UI de asset), Lia-Project (revisao visual) | `lia-game-visual-review-c29e0ace` |
| `lia-module-planning` | Use depois da Etapa 0 quando o Dev pedir para dividir a visão do jogo em módulos, tarefas, dependências e critérios d… | Original Lia | 1 arq. / 2627 B | nenhuma declarada | Lia-Go (bootstrap de projeto), Lia-Forge (brief de asset), Lia-AgentHub (exemplo de skill com templates/) | `lia-module-planning-d3e0b2f1` |
| `lia-project-resume` | Use ao reabrir um projeto de jogo após pausa, receber um handoff ou perguntar onde paramos; reconstrói estado, bloque… | Original Lia | 1 arq. / 2313 B | nenhuma declarada | Lia-Go (bootstrap de projeto), Lia-Forge (brief de asset), Lia-AgentHub (exemplo de skill com templates/) | `lia-project-resume-566d8b15` |
| `lia-task-handoff` | Use antes de trocar de sessão/agente, delegar uma Task ou interromper trabalho para entregar handoff com IDs, context… | Original Lia | 1 arq. / 2521 B | nenhuma declarada | Lia-Go (bootstrap de projeto), Lia-Forge (brief de asset), Lia-AgentHub (exemplo de skill com templates/) | `lia-task-handoff-8041c0fb` |

**Detalhes que importam para o catálogo:**

- `lia-game-project-bootstrap` é a única com `references/` (2 arquivos) e `templates/` (5: `GDD.md`, `SCOPE.md`, `DECISIONS.md`, `REFERENCIAS.md`, `PROJECT_BRIEF.md`) — 159 linhas de corpo, dentro do limite recomendado (<500) da especificação.
- As 12 adaptadas têm corpo padronizado de ~23 linhas e uma seção `## Origem` que **liga ao arquivo exato do upstream no commit citado** — padrão de proveniência melhor do que a maioria dos catálogos públicos.
- As 4 originais declaram origem conceitual (`GameDevPipeline`, `plan`/`feature-handoff` do Mr. Mak) **sem copiar conteúdo**.
- Licença do repositório: **MIT** (`LICENSE`, © 2026 BloomRX e colaboradores da Lia Studio) + `THIRD_PARTY_NOTICES.md` + textos integrais em `docs/licenses/CLAUDE-CODE-GAME-STUDIOS-MIT.txt` e `docs/licenses/MR-MAK-WORKSPACE-MIT.txt`. **Esses arquivos ficam na raiz do repositório, fora do payload da Skill** — consequência direta no §7.
- `docs/Mr-Mak-Skills-Free.zip` (9,9 MB, 764 arquivos): pacote de terceiros **guardado, não importado**. Contém 20 Skills duplicadas em `.agents/skills/` e `.claude/skills/`, `LICENSE` MIT, `THIRD_PARTY_NOTICES.md`, `SKILLS-README.md` e o subprojeto `img2threejs` com licença **Apache-2.0** própria. Ver catálogo de terceiros.

## 5. Lia Model Lab — 9 Skills (`main` @ `3ec4313`)

Único repositório Lia com Skills **em `main`**. O `.agents/skills/README.md` as chama de "procedimentos versionados" e registra honestamente: **"descoberta automática no Arena não foi comprovada. Leia manualmente a skill aplicável"**.

| Skill | Função declarada | Origem | Payload | Compatibilidade declarada | Reuso potencial | Id calculado |
|---|---|---|---|---|---|---|
| `capability-mapping` | Separar pesos, especialistas, runtime, integrações e critérios operacionais. | Original Lia | 1 arq. / 1902 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `capability-mapping-9dddebe4` |
| `dataset-governance` | Auditar direitos, privacidade, schema e isolamento dos dados. | Original Lia | 1 arq. / 1987 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `dataset-governance-f6d13852` |
| `experiment-reproducibility` | Verificar identidade, hashes, ambientes e retomada sem executar workloads. | Original Lia | 1 arq. / 2257 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `experiment-reproducibility-8c60e8a2` |
| `finetuning-plan` | Planejar SFT LoRA/QLoRA sem executar treinamento. | Original Lia | 1 arq. / 2436 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `finetuning-plan-9707e89b` |
| `lia-brand-consistency-review` | Revisar nome, autonomia, privacidade e alegações conforme marca Lia. | Original Lia | 1 arq. / 1844 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `lia-brand-consistency-review-13dd0f3d` |
| `model-candidate-research` | Comparar checkpoints abertos com fontes primárias e recomendação condicional. | Original Lia | 1 arq. / 2032 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `model-candidate-research-69cd1d06` |
| `model-evaluation` | Comparar base, adapter e quantização sem ocultar regressões. | Original Lia | 1 arq. / 2473 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `model-evaluation-7396dd64` |
| `model-license-release-review` | Revisar direitos por artefato sem aceitar termos ou publicar. | Original Lia | 1 arq. / 2044 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `model-license-release-review-139a1796` |
| `multi-agent-orchestration` | Coordenar revisões independentes com fallback sequencial real. | Original Lia | 1 arq. / 1957 B | nenhuma declarada | Lia-AgentHub (model-license-release-review e quase um lia-license-audit), Lia-Project (capability-mapping), Lia-Forge (model-candidate-research para pesos de asset) | `multi-agent-orchestration-cc95e4a5` |

**Recursos relacionados que NÃO são Skills (mas são capacidades catalogáveis):**

| Recurso | Caminho | Classe | Estado |
|---|---|---|---|
| 7 perfis de agente Codex | `.codex/agents/{brand-reviewer,capability-architect,dataset-auditor,evaluation-reviewer,license-reviewer,model-researcher,training-planner}.toml` | perfil de agente | IMPLEMENTED como arquivo; execução no Codex declarada **NOT-TESTED** no `.codex/README.md` |
| 5 templates de documento | `templates/{ADR,AVALIACAO,DATASET-CARD,EXPERIMENTO,MODEL-CARD}.md` | template | IMPLEMENTED |
| Requisitos de capacidade | `configs/capability-requirements.yaml`, `configs/model-candidates.yaml`, `configs/sft-pilot.template.yaml` | dado/configuração | IMPLEMENTED |
| Matrizes de capacidade | `docs/01-AIRI-CAPABILITY-INVENTORY.md`, `docs/02-LIA-CAPABILITY-MATRIX.md`, `docs/14-ORQUESTRACAO-DE-AGENTES.md` | documentação | IMPLEMENTED |
| Verificação CI | `.github/workflows/verify.yml` | automação | IMPLEMENTED (execução não verificada nesta pesquisa) |

**Lacuna de licença:** `Lia-Model-Lab` **não tem `LICENSE` na raiz** e a API do GitHub não reporta SPDX. As 9 Skills são autorais, mas o direito de redistribuição **não está declarado** — decisão humana pendente (ver auditoria de licença).

## 6. Lia Project — 22 Skills (`arena/c6b02f64-lia-project` @ `0093de09`)

Maior conjunto do ecossistema. O repositório já mantém catálogo próprio (`docs/architecture/AGENT-SKILLS-CATALOG.md`, revisão de 30/10/2026: "22 skills raiz (21 Lia + Alethe), 28 AIRI") e um teste que o protege (`test_every_skill_is_in_the_catalog`, em `tools/test_agent_skills.py`): **Skill nova sem linha no catálogo reprova a suíte**. O Hub deve consumir esse catálogo, não substituí-lo.

| Skill | Função declarada | Origem | Payload | Compatibilidade declarada | Reuso potencial | Id calculado |
|---|---|---|---|---|---|---|
| `airi-upstream-integration` | Avalia e integra seletivamente atualizacoes do AIRI vendado em airi/, sem re-clone cego e sem perder as modificacoes … | Original Lia | 1 arq. / 4674 B | Requer git e acesso a github.com. O clone de comparacao vive fora do repositorio. | Lia-Project | `airi-upstream-integration-46870e84` |
| `alethe` | Orchestrate bounded Codex, Claude Code, Agy, Kimi, or custom CLI workers to finish work with the least lead context a… | Terceiro vendorizado + patches | 23 arq. / 1450260 B | nenhuma declarada | Lia-Project (orquestracao), Lia-AgentHub (referencia de orquestracao SEM executar) | `alethe-855b31e6` |
| `lia-agent-evaluation` | Monta comparacao controlada de qualidade do modelo na Lia - imagem, ferramentas, streaming SSE, argumentos invalidos,… | Original Lia | 1 arq. / 4974 B | Requer acesso ao provedor configurado. Sem credencial, o item e BLOCKED - nao FAIL. | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-agent-evaluation-b50f56a2` |
| `lia-agent-orchestration` | Divide trabalho entre agentes, subagentes ou workers com escopo e contexto mínimos, escolhe a capacidade adequada à t… | Original Lia | 1 arq. / 3105 B | A seleção de modelo e esforço depende do runner e não é garantida pelo repositório. Aleth… | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-agent-orchestration-810fc789` |
| `lia-ai-sdk-integration` | Avalia integrações de geração de texto, streaming, ferramentas, saída estruturada, embeddings, imagem ou voz com xsAI… | Original Lia | 1 arq. / 1390 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-ai-sdk-integration-af3bb9c4` |
| `lia-browser-automation` | Automatiza navegador e renderer de Electron com agent-browser/CDP para investigação, testes exploratórios e QA. Use s… | Original Lia | 1 arq. / 1747 B | Requer agent-browser instalado e endpoint CDP ativo; não instala ferramentas automaticame… | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-browser-automation-bd764479` |
| `lia-electron-cdp-debugging` | Descobre a janela renderer correta de um app Electron por CDP quando há várias janelas, rotas duplicadas ou alvos cri… | Original Lia | 1 arq. / 1240 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-electron-cdp-debugging-87bab323` |
| `lia-eventa-ipc` | Usa @moeru/eventa para eventos tipados, RPC ou streaming quando a dependência estiver presente. Use ao implementar ou… | Original Lia | 1 arq. / 1031 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-eventa-ipc-82243469` |
| `lia-pnpm-workspaces` | Trabalha com pnpm, dependências e workspaces no repositório Lia. Use antes de alterar dependências, filtros ou builds. | Original Lia | 1 arq. / 931 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-pnpm-workspaces-3f63a0ff` |
| `lia-regression-investigation` | Investiga causa de bug ou regressao na Lia com experimento controlado, uma variavel por vez, teste que falha antes da… | Original Lia | 1 arq. / 4632 B | Nenhuma. Metodo; serve a qualquer ambiente e a qualquer suite da Lia. | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-regression-investigation-5c9848cc` |
| `lia-release-gate` | Executa e documenta o gate de release da Lia no Windows, separando PASS, FAIL, BLOCKED e NOT RUN. Use ao rodar os tes… | Original Lia | 1 arq. / 4723 B | O gate real exige Windows com o checkout, Node e Python no PATH. Fora do Windows apenas a… | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-release-gate-f2b7f765` |
| `lia-safe-change` | Protege o trabalho existente ao implementar mudanças na Lia. Use antes de editar código, reorganizar arquivos, integr… | Original Lia | 1 arq. / 2759 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-safe-change-035dd03a` |
| `lia-security-review` | Revisa alterações da Lia quanto a permissões, execução de ferramentas, arquivos, segredos, processos, dependências e … | Original Lia | 1 arq. / 2473 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-security-review-5c8dc85a` |
| `lia-test-discipline` | Localiza e executa a suíte certa da Lia entre Python tools/, Node Tests/tools, Vitest lia-app e Vitest core-agent. Us… | Original Lia | 1 arq. / 2800 B | Exige Node, pnpm e Python. Suítes Vitest exigem dependências do workspace instaladas. | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-test-discipline-7aa20996` |
| `lia-ui-quality-review` | Revisa telas e fluxos da Lia quanto a clareza, acessibilidade, consistência visual e usabilidade para pessoas não téc… | Original Lia | 1 arq. / 1488 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-ui-quality-review-1288bf29` |
| `lia-unocss-ui` | Trabalha com UnoCSS em partes da Lia que realmente usam essa tecnologia. Use ao editar estilos em uma área que usa Un… | Original Lia | 1 arq. / 746 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-unocss-ui-71a3e789` |
| `lia-visual-evidence` | Produz evidência visual repetível de fluxos da Lia em Electron ou navegador usando Vishot quando disponível. Use ao r… | Original Lia | 1 arq. / 1647 B | Requer Vishot e runtime disponível; não instala Playwright/Chromium sem autorização. | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-visual-evidence-388d125f` |
| `lia-voice-diagnostics` | Investiga falhas no caminho de voz da Lia, separando microfone/permissões, captura, VAD, STT, modelo conversacional, … | Original Lia | 1 arq. / 2935 B | Testes completos de áudio exigem dispositivos e permissões reais; mocks e logs não substi… | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-voice-diagnostics-3e2a6b75` |
| `lia-vue-development` | Desenvolve e revisa Vue 3, TypeScript, Pinia e VueUse na Lia, quando a área afetada realmente usa essa stack. Use ao … | Original Lia | 1 arq. / 1544 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-vue-development-d2e8cbe2` |
| `lia-vue-testing` | Escreve e depura testes de componentes Vue, composables, stores Pinia e interfaces DOM. Use ao escrever ou investigar… | Original Lia | 1 arq. / 1361 B | nenhuma declarada | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-vue-testing-456bff43` |
| `lia-windows-electron-validation` | Valida o comportamento real do Launcher e do Stage Electron da Lia no Windows, incluindo janela visível, processos fi… | Original Lia | 1 arq. / 1756 B | Exige Windows e checkout local. Automação controlada prova critérios observáveis; áudio f… | Lia-Studio, Lia-Forge, Lia-Go, Lia-AgentHub | `lia-windows-electron-validation-05d6d591` |
| `stage-runtime-debugging` | Diagnostica o Stage da Lia no Windows quando ele nao inicia, inicia sem janela, congela ou nao encerra, separando fal… | Original Lia | 1 arq. / 4593 B | Exige Windows com o checkout e Node no PATH. O Stage e um processo Electron supervisionad… | Lia-Project, Lia-Studio (build desktop) | `stage-runtime-debugging-32a68b69` |

**`alethe` — o único terceiro vendorizado dentro de um repositório Lia:**

- Upstream `Kc1t/alethe-orchestrate-skill`, versão 19 (2026-10-23), commit de comparação anterior `c36c341c34360f970a07fe3e2d2600ca2bba8ed2` (**verificado: existe**, 2026-10-28).
- Licença **MIT** (© 2026 Kauã Miguel), cópia integral **dentro** do payload (`LICENSE`) — por isso é o único registro com `license.code = MIT` e `containsScripts = true`.
- Patches locais de segurança de 28/10/2026 (editor com DOM/textContent, filtro de URL, reserva atômica de estimativas) documentados em `UPSTREAM.md` e `docs/architecture/ALETHE-HARDENING-2026-10-28.md`. `UPSTREAM.md` declara: **"A cópia no repositório não instala CLIs, não configura credenciais e não comprova que o Codex local detecta ou executa a skill."**
- **Risco não coberto pela MIT:** `assets/brands/` contém sinais distintivos de terceiros (`claude-official.png.b64`, `openai-official-white.svg`, `kimi-official.png.b64`, `antigravity-official.svg`, `router9-official.svg`). Licença de código ≠ licença de marca.
- `frontmatter` usa `metadata:` **aninhado** (`argument-hint`, `version: "19"`), que o parser simples do Hub ignora → a versão importada cairia para `0.1.0` (ver §7).

**Skills vendadas do AIRI (`airi/.agents/skills/`, 28 + 1 em `airi/integrations/minecraft/codex-skills/`):**
upstream `moeru-ai/airi`, **MIT** (© 2024-PRESENT Neko Ayaka), versão declarada em `docs/licenses/THIRD-PARTY-NOTICES.md`: `v0.12.0-beta.5`, commit `2c1e223c…`. Nomes: `agent-browser`, `agent-browser-electron`, `create-pr`, `enforce-rules-for-unocss`, `enforce-rules-for-vitest`, `eventa`, `pinia`, `pnpm`, `release-note-writer`, `simple-english`, `stage-tamagotchi-godot-csharp`, `tsdown`, `unocss`, `upload-github-attachment`, `use-agent-browser-*` (3), `use-vishot*` (6), `vue`, `vue-best-practices`, `vue-testing-best-practices`, `vueuse-functions`, `web-design-guidelines`, `xsai`, `minecraft-debug-mcp`. O próprio Lia-Project já as auditou uma a uma em `docs/architecture/AGENT-SKILLS-CATALOG.md` (decisões "Adaptada"/"Não copiar integralmente") e as trata como **fonte temporária**, não dependência permanente. **Não foram re-auditadas aqui** — referência cruzada, sem duplicação.

**Lacuna de licença:** nem `main` (`9c7ac183fd`) nem `arena/c6b02f64` têm `LICENSE` na raiz do Lia-Project. Existem `docs/licenses/THIRD-PARTY-NOTICES.md` e `docs/licenses/ASSET-LICENSES.md` (terceiros/assets), mas **a licença do código autoral não está declarada**.

## 6.1 Lia Forge — 1 Skill + capacidades de produção (`arena/649f88bd-3dspritesheet` @ `35b207f`)

| Skill | Função declarada | Origem | Payload | Compatibilidade declarada | Reuso potencial | Id calculado |
|---|---|---|---|---|---|---|
| `lia-brand-check` | Audita uma mudança da Lia Forge contra os princípios de autonomia, dados do usuário, consentimento, transparência e i… | Original Lia | 1 arq. / 2662 B | nenhuma declarada | todos os produtos Lia (revisao de marca e consenso de dados) | `lia-brand-check-79f82f4e` |

A Forge tem **uma** Skill, presente em cinco branches (`arena/649f88bd-3dspritesheet`, `arena/26157d5b`, `arena/ee48e1c5`, `codex/windows-stability-fixes`, `validation/windows-integrated-35b207f`) e **ausente em `main`**. Licença do repositório na branch: **MIT** (© 2026 Lia Forge contributors) + `THIRD_PARTY_NOTICES.md` com **464 pacotes npm** resolvidos a partir do `package-lock.json` (lockfile v3) — o melhor SBOM do ecossistema Lia. O aviso é explícito: nome, marca e `assets/lia-forge.svg`/`.ico` **não** são licenciados pela MIT.

**Capacidades da Forge que NÃO são Skills (e que o Hub não deve duplicar):**

| Recurso | Caminho | Classe | Estado declarado no próprio código |
|---|---|---|---|
| Capability Registry | `shared/capabilities/registry.mjs` | registro de capacidades de produção (49 ids: `image2d.*`, `rig2d.*`, `model3d.*`, `character.*`, `motion.*`…) | `CAPABILITY_SCHEMA_VERSION = 1`; statuses `implemented` (16), `partial` (5), `proposed` (5), `planned` (24); comentário: "Nenhuma capacidade declarada aqui implica implementação, execução ou validação" |
| Tool & Provider Hub | `shared/hub/provider-hub.mjs` | resolução capacidade→adapter→ferramenta | `HUB_SCHEMA_VERSION = 1`; estados `ready/unknown/blocked/missing`; "O Hub não executa" |
| Servidor MCP `lia-forge` | `scripts/spriteforge-mcp.mjs` | MCP server (`@modelcontextprotocol/sdk` + `zod`) | 10 tools: `spriteforge_get_status`, `_comfyui_status`, `_list_comfyui_workflows`, `_list_free_models`, `_list_assets`, `_create_asset`, `_add_reference`, `_prepare_task`, `_update_stage`, `_open_panel` |
| Instalador de configuração MCP | `scripts/mcp_config.py` | CLI de configuração | grava entradas MCP **project-scoped** para clientes suportados, com contenção de caminho e recusa de symlinks |
| Workflow Engine | `electron/workflow-*.cjs`, `shared/engine/*` | runtime de execução | IMPLEMENTED (smoke tests em `tests/*-smoke.cjs`) |
| Skills & Knowledge Engine | `docs/SKILLS-KNOWLEDGE-ENGINE.md` | proposta | **PLANNED**; traz um manifesto YAML proposto (`id`, `version`, `assetCategories`, `stages`, `requiredCapabilities`, `humanGates`, `risks`, `source`, `license`, `trust`) |
| Matrizes de terceiros | `docs/T14-AGENT-SKILLS-MCP-MATRIX.md`, `docs/T14-AGENT-SOLUTIONS-CATALOG.md` (`main`) | pesquisa | RESEARCH de 2026-11-14, com licenças verificadas de ~19 servidores MCP |

**Colisão de vocabulário a resolver (risco de arquitetura, não de código):** a Forge já chama de "Hub" o seu `shared/hub/provider-hub.mjs` e de "capability" as suas 49 capacidades de produção de assets. O Lia Agent Hub usa as mesmas palavras para outro domínio (registro/distribuição de capacidades de agente). Sem um glossário de fronteira, os dois catálogos serão confundidos por humanos e por agentes.

## 6.2 Lia Go, Lia AgentHub e demais repositórios

| Repositório | O que existe | Classe | Estado |
|---|---|---|---|
| `Lia-Go` | `.agents/skills/.gitkeep` (pasta vazia) em `arena/f1ac5ed6-lia-go`; `tools/project_cli.py`, `tools/test_project_cli.py`, `tools/test_creation.py`; `AGENTS.md`, `docs/AGENTS.md` | placeholder + CLI | PLANNED (Skills) / IMPLEMENTED (CLI, sem licença declarada no repo) |
| `Lia-AgentHub` (`arena/a92004be`) | Hub: domínio, adaptadores, servidor local, UI estática, testes, empacotamento Windows | aplicação | IMPLEMENTED na branch; **não integrada em `main`**; sem `LICENSE` na raiz (há `THIRD_PARTY_NOTICES.md`) |
| `Lia-AgentHub` (`arena/b6febe41`) | `docs/design/*` (auditoria UI/UX, spec tela a tela, protótipo HTML) | design | IMPLEMENTED como documento; branch de outro especialista — não tocada |
| `LiaVoiceStudio`, `3d-create`, `3d-sprite`, `ChibiCreate`, `ComfyUI_Colab`, `SilksongREA`, `animations-free` | nenhum `SKILL.md`, `.agents/` ou `.claude/` em `main` | assets/conteúdo | sem capacidades de agente |

---

## 7. Lacunas confirmadas (com evidência)

| # | Lacuna | Evidência | Impacto no catálogo |
|---|---|---|---|
| L-01 | **Licença fora do payload.** Nenhuma das 47 Skills Lia tem `LICENSE`/`COPYING` na própria pasta; os avisos ficam na raiz do repositório | `importer.py::_detect_license` ignora caminhos com `/` | 47 de 48 registros entram com `license.status = "unknown"`, `licenseKnown: false`, `redistributable: false` |
| L-02 | **Descrição não vem do `SKILL.md`.** O Hub só preenche `description` a partir de `manifest.json` | `importer.py`: `description=(manifest or {}).get("description","")` | catálogo com 48 descrições vazias, embora todo `SKILL.md` tenha `description` no frontmatter |
| L-03 | **`metadata:` aninhado é ignorado.** O parser do Hub é deliberadamente simples (`chave: valor`, aninhamento descartado) | `skills.py::parse_frontmatter`; spec Agent Skills usa `metadata:` aninhado no exemplo oficial | `alethe` perde `version: "19"` → `0.1.0`; qualquer Skill que declare `metadata.author/version/tags` perde os três |
| L-04 | **Sem campo de derivação.** O modelo tem `source.upstream`, `source.original_name` e `versionOf` (linhagem de versões), mas nada que exprima "adaptada de X no commit Y" | `model.py::Source`; 12 Skills do Studio e 1 do Project são adaptações | a cadeia de proveniência de adaptação fica só em `researchNotes` (fora do contrato) |
| L-05 | **Aviso espúrio de pasta.** O nome da pasta é derivado do primeiro caminho com `/`, ou seja, da primeira **subpasta** do payload | `importer.py`: `folder = next((p.split("/")[0] for p in files if "/" in p), None)` + `skills.py` `NAME_FOLDER_MISMATCH` | importar `lia-game-project-bootstrap/` diretamente gera aviso "`name` é X mas a pasta é `references`" |
| L-06 | **Convenção de identidade inconsistente.** 8 de 9 Skills do Model-Lab e 2 do Project (`airi-upstream-integration`, `stage-runtime-debugging`) não usam o prefixo `lia-` | frontmatter lido em cada pasta | busca/filtragem por autoria Lia não é confiável sem metadado explícito |
| L-07 | **Duplicação entre produtos.** `lia-brand-check` (Forge) ≈ `lia-brand-consistency-review` (Model-Lab); `lia-agent-orchestration` (Project) ≈ `multi-agent-orchestration` (Model-Lab) ≈ `alethe` (terceiro) | corpos das Skills lidos | duas fichas para a mesma responsabilidade; decisão de consolidação é humana |
| L-08 | **Quase nada em `main`.** 39 das 48 Skills vivem só em branches de sessão | §3 | o Hub catalogaria capacidades que o próprio ecossistema ainda não integrou |
| L-09 | **Licença dos repositórios Lia ausente.** `Lia-Project`, `Lia-Model-Lab`, `Lia-Go`, `Lia-AgentHub` não têm `LICENSE` na raiz (API GitHub: SPDX `none`); Studio e Forge têm MIT apenas em branches | §4–§6.2 | redistribuir Skills desses repositórios exige decisão humana prévia |
| L-10 | **Perfis de agente e templates não têm tipo próprio no fluxo real.** O modelo enumera `cli-tool`, `template`, `provider-model`, `workflow`, mas a detecção automática só reconhece `agent-skill` (por `SKILL.md`), `mcp-server` (por `package.json`) e `reference` (por `.md`/`.txt`) | `model.py::ResourceType`; `importer.py::_detect_type` | os 7 perfis `.toml` do Model-Lab e os 5 templates cairiam em `reference`/`unknown` |

---

## 8. O que este inventário NÃO afirma

- **Nenhuma Skill foi executada**, aplicada por um agente, nem validada em Windows. Estado geral: IMPLEMENTED como arquivo; EXECUTED/VALIDATED: não.
- A existência de uma Skill num repositório **não** indica que algum host a descubra: o Model-Lab declara descoberta não comprovada; `alethe` declara que a cópia não comprova execução; o Studio declara que a biblioteca "ainda não as aplica por um runtime".
- Os ids e hashes deste inventário foram calculados por ferramenta de pesquisa (`docs/research/tools/build-catalog-records.py`), **não** pelo Hub. Só viram VALIDATED quando uma importação real produzir o mesmo valor.
- As 29 Skills do AIRI e as 20 do pacote Mr-Mak **não** foram auditadas arquivo a arquivo aqui; o Lia-Project e o Lia-Studio já têm auditorias próprias, referenciadas sem duplicação.
