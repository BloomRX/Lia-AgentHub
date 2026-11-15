# Catálogo de Skills e capacidades de terceiros

**Documento:** `docs/research/THIRD-PARTY-SKILLS-CATALOG.md` (Missão 2)
**Agente:** Research — Lia Agent Hub · **Branch:** `arena/db625478-lia-agenthub`
**Data das consultas:** 2026-11-15 (UTC)
**Natureza:** `RESEARCH`. **Nada foi clonado, instalado, baixado para execução, executado, aceito em licença ou redistribuído.** Inspeção por API do GitHub (metadados, árvores, conteúdo de arquivos específicos), leitura de `LICENSE`/`README` remotos e pesquisa web. Nenhum dado do usuário foi enviado a serviços externos.

> A análise de licença item a item — com obrigações de atribuição, redistribuição, código-fonte, restrições comerciais e conclusão — está em [`SKILL-LICENSE-AND-PROVENANCE-AUDIT.md`](SKILL-LICENSE-AND-PROVENANCE-AUDIT.md). Este documento responde "o que existe, o que contém e para que serviria"; a auditoria responde "o que temos o direito de fazer".

---

## 1. Método, alcance e limitações

### 1.1 Canais que funcionaram

| Canal | Uso | Exemplo de evidência |
|---|---|---|
| GitHub REST API (`gh api repos/…`) | licença SPDX, estrelas, forks, `created_at`, `pushed_at`, `archived`, branch padrão | `anthropics/skills` → `license: none`, push 2026-11-14 |
| GitHub Trees API (`git/trees/HEAD?recursive=1`) | contagem real de `SKILL.md`, arquivos de licença aninhados, presença de `scripts/` | `sickn33/agentic-awesome-skills` → 9.454 `SKILL.md`, 648 arquivos de licença |
| GitHub Contents API | leitura de `LICENSE`, `README`, `UPSTREAM.md`, frontmatter de `SKILL.md` específicos | `modelcontextprotocol/servers/LICENSE` (transição MIT→Apache-2.0) |
| GitHub Commits API | confirmar que commits citados por repositórios Lia ainda existem | `05ad7c8a5b…`, `cf1e126025…`, `c36c341c34…` |
| `fetch_page` em fonte primária | especificação Agent Skills | `https://agentskills.io/specification` (lida integralmente nesta sessão) |
| `web_search` | diretórios e ecossistema sem acesso direto | `skills.sh` (fontes secundárias, ver §6) |

### 1.2 Limitações registradas (não esconder o que não foi possível)

1. **`skills.sh` não foi lido na fonte primária** nesta sessão; as afirmações sobre ele vêm de três fontes secundárias (§6) e estão marcadas como tal.
2. **Nenhum repositório de terceiros foi clonado.** Contagens vêm da Trees API; conteúdo, de arquivos individuais lidos pela Contents API. Onde não li o arquivo, o campo diz "não lido".
3. **Estrelas/forks são métricas de popularidade, não de qualidade.** O mandato do projeto é explícito: não recomendar dependência por popularidade. Nenhuma classificação abaixo usa estrela como critério.
4. **Licença reportada pela API ≠ licença real.** Três casos provam isso nesta lista: `anthropics/skills` (API: `none`; cada skill tem `LICENSE.txt` Apache-2.0), `vercel-labs/agent-skills` (API: `none`; `README` declara MIT, sem arquivo `LICENSE`), `modelcontextprotocol/servers` (API: `NOASSERTION`; licença mista em transição).
5. **Não há parecer jurídico.** Ambiguidades viram pendência de revisão humana.

### 1.3 Vocabulário

`USE_AS_IS` · `ADAPT_ALLOWED` · `FORK_CANDIDATE` · `INDEPENDENT_REIMPLEMENTATION` · `RESEARCH_ONLY` · `BLOCKED` (definições na auditoria de licença, §1).

---

## 2. Padrão e referência normativa

| Fonte | O que é | Licença verificada | Conteúdo verificado | Utilidade para o Hub | Classe |
|---|---|---|---|---|---|
| [`agentskills/agentskills`](https://github.com/agentskills/agentskills) | Especificação e documentação do formato Agent Skills (★27.310, criado 2025-12-16, push 2026-11-04) | **Apache-2.0** (API + `LICENSE` lido) | repositório da especificação | **Formato canônico**: é o contrato que o validador do Hub já implementa (`domain/skills.py`, 6 campos) | `USE_AS_IS` (norma) |
| [`agentskills.io/specification`](https://agentskills.io/specification) | Texto primário da especificação | documentação do padrão | **lido nesta sessão**: estrutura de pasta; frontmatter com `name` (1–64, minúsculo, sem hífen duplo/pontas, **deve igualar o nome da pasta**) e `description` (1–1.024, diz o que faz e quando usar) obrigatórios; `license`, `compatibility` (≤500), `metadata` (mapa string→string), `allowed-tools` (experimental) opcionais; `scripts/`, `references/`, `assets/` convencionais;carregamento progressivo em 3 camadas (~100 tokens de metadados → corpo <5.000 tokens → recursos sob demanda); corpo recomendado <500 linhas | Base de todos os critérios de validação e das lacunas L-02/L-03 do inventário | `USE_AS_IS` (norma) |
| [`anthropics/skills`](https://github.com/anthropics/skills) | Skills de exemplo da Anthropic, incluindo as que operam documentos no Claude (★195.120, push 2026-11-14) | **API: `none`.** Sem `LICENSE` na raiz; **cada uma das 19 skills tem `LICENSE.txt`** e o frontmatter usa `license: Complete terms in LICENSE.txt`; `LICENSE.txt` de `skill-creator` lido = **Apache-2.0**; `THIRD_PARTY_NOTICES.md` na raiz lista dependências (ex.: `imageio` BSD-2-Clause) | 19 skills: `academy-guide`, `algorithmic-art`, `brand-guidelines`, `canvas-design`, `claude-api`, `discernment-nudge`, `doc-coauthoring`, `docx`, `frontend-design`, `internal-comms`, `mcp-builder`, `pdf`, `pptx`, `skill-creator`, `slack-gif-creator`, `theme-factory`, `web-artifacts-builder`, `webapp-testing`, `xlsx`; + `spec/agent-skills-spec.md`, `template/`, `.claude-plugin/marketplace.json` | **`skill-creator` e `mcp-builder` são as duas referências mais úteis** para o Skill Creator e o MCP Workshop do Hub; `brand-guidelines` é precedente direto de skill de marca (comparar com `lia-brand-check`) | `ADAPT_ALLOWED` por skill (verificar `LICENSE.txt` de cada uma) |
| [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) | Coleção oficial da Vercel (★34.097, criado 2025-12-08, push 2026-11-12) | **API: `none`; nenhum arquivo `LICENSE`/`NOTICE` na árvore (444 blobs).** `README` tem seção `## License` → **MIT** (declaração em README, não em arquivo próprio) | 9 `SKILL.md`; `skills.sh.json` (manifesto do diretório skills.sh); `packages/`, `scripts/`, `AGENTS.md`, `CLAUDE.md` | Referência de **publicação em diretório** (manifesto `skills.sh.json`) e de skills de front-end/React | `RESEARCH_ONLY` → `ADAPT_ALLOWED` **pendente** de confirmação da declaração MIT e do titular |

---

## 3. Coleções de Skills de desenvolvimento (candidatas a reuso)

| Fonte | Licença verificada | Conteúdo verificado (árvore) | Atividade | Utilidade para Lia | Classe proposta |
|---|---|---|---|---|---|
| [`obra/superpowers`](https://github.com/obra/superpowers) | **MIT** (`LICENSE` lido: © 2025 Jesse Vincent) | 15 `SKILL.md` (`brainstorming`, `systematic-debugging`, `test-driven-development`, `writing-plans`, `writing-skills`, `verification-before-completion`, `requesting-code-review`, `receiving-code-review`, `dispatching-parallel-agents`, `subagent-driven-development`, `executing-plans`, `using-git-worktrees`, `finishing-a-development-branch`, `diagnosing-superpowers`, `using-superpowers`) + `hooks/`, `scripts/`, `tests/`, `docs/` e **12 diretórios de plugin por host** (`.agents`, `.claude-plugin`, `.codex-plugin`, `.cursor-plugin`, `.devin-plugin`, `.hermes-plugin`, `.kimi-plugin`, `.muse-plugin`, `.opencode`, `.pi`, `.antigravity-plugin`, `.github`) | ★317.905, push 2026-11-03, criado 2025-10-09 | **Dois valores distintos:** (a) skills de método (`verification-before-completion`, `writing-plans`) que sobrepõem `lia-test-discipline`/`lia-release-gate`; (b) **o padrão de empacotamento multi-host**, que é exatamente o problema de distribuição do Hub | `ADAPT_ALLOWED` (skills) + `FORK_CANDIDATE` **não** — estudar empacotamento como `REFERENCE` de arquitetura |
| [`mattpocock/skills`](https://github.com/mattpocock/skills) | **MIT** (`LICENSE` lido: © 2026 Matt Pocock) | 39 `SKILL.md` em categorias `skills/engineering` (20), `skills/productivity` (7), `skills/in-progress` (8), `skills/misc` (3); `.claude-plugin`, `docs`, `scripts`, `.changeset`, `.out-of-scope` | ★324.857, push 2026-11-13, criado 2026-02-03 | Skills de engenharia/TypeScript úteis ao Lia-Project (Vue/TS); a pasta `in-progress` mostra **estado não-final declarado no próprio layout** — boa prática de ciclo de vida | `ADAPT_ALLOWED` (por skill, evitando `in-progress`) |
| [`sickn33/agentic-awesome-skills`](https://github.com/sickn33/agentic-awesome-skills) | **MIT na raiz** (`LICENSE` lido: © 2026 Antigravity User) **+ 648 arquivos de licença internos**, sendo **184 `UPSTREAM-LICENSE.txt`**, 347 `LICENSE`, 75 `LICENSE.txt`, 21 `LICENSE.md`, e licenças específicas de terceiros: `LICENSE-MICROSOFT` (2), `LICENSE-SIMPLE-ICONS.txt`, `LICENSE-SVGL.txt`, `LICENSE-PAYMENT-ICONS.txt`, `impeccable-LICENSE-Apache-2.0.txt` (3), `taste-skill-LICENSE-MIT.txt` (3) | **9.454 `SKILL.md`** em 31.044 blobs; organização em `plugins/` (ex.: `plugins/agentic-awesome-skills-claude` com 2.891 e `plugins/agentic-awesome-skills` com 2.870 → **conteúdo largamente duplicado por host**); `schemas/aas-v1/` com **11 JSON Schemas** (`catalog-manifest`, `catalog-metadata`, `skills-index.v1`, `skill-score.v1`, `managed-state`, `plan`, `recovery-plan`, `result-envelope`, `selection-evidence`, `selection-input`, `stack-manifest`, `doctor-result`, `journal`); `verification/` com runner e receipts; `skill_categorization/`, `data/`, `docs_zh-CN/` | ★49.745, push 2026-11-14, criado 2026-01-14 | **Maior acervo encontrado e o único com esquema de catálogo + score + verificação publicados.** Para o Hub vale mais como **referência de esquema** (`skills-index.v1`, `skill-score.v1`) do que como fonte de skills: a licença de cada skill é a do upstream dela, não a MIT da raiz | `RESEARCH_ONLY` para o acervo; `ADAPT_ALLOWED` **somente** com resolução de licença por skill; esquemas = `REFERENCE` |
| [`jnMetaCode/superpowers-zh`](https://github.com/jnMetaCode/superpowers-zh) | **MIT** (API) | tradução chinesa de `obra/superpowers` + 4 skills originais | ★8.541, push 2026-11-15 | Precedente de **derivado traduzido** de coleção MIT: mostra que a obrigação de aviso sobrevive à tradução | `RESEARCH_ONLY` (não há ganho para o ecossistema Lia, que trabalha em pt-BR) |
| [`michaelboeding/skills`](https://github.com/michaelboeding/skills), [`crystian/skills`](https://github.com/crystian/skills), [`beeyev/skills`](https://github.com/beeyev/skills), [`milanvrskovy/mvsd-ai-skills`](https://github.com/milanvrskovy/mvsd-ai-skills), [`OpenMatter-Network/agent-io-skills`](https://github.com/OpenMatter-Network/agent-io-skills) | **MIT** (API, cada) | coleções pessoais pequenas declaradas compatíveis com `SKILL.md` | ★30 / ★24 / ★16 / ★15 / ★10; push 2026-10-14 / 2026-04-18 / 2026-07-07 / 2026-06-01 / 2026-06-01 | Baixo valor estratégico; úteis só como amostra de convenções de comunidade | `RESEARCH_ONLY` |
| [`abdullahkhawer/devops-skills`](https://github.com/abdullahkhawer/devops-skills) | **Apache-2.0** (API) | coleção DevOps | ★11, push 2026-09-22, branch padrão `master` | DevOps não é domínio prioritário do ecossistema Lia hoje | `RESEARCH_ONLY` |

---

## 4. Domínios específicos do ecossistema Lia

### 4.1 Jogos, 2D/3D, Blender, engines

| Fonte | Licença verificada | Conteúdo | Atividade | Utilidade | Classe proposta |
|---|---|---|---|---|---|
| [`Donchitos/Claude-Code-Game-Studios`](https://github.com/Donchitos/Claude-Code-Game-Studios) | **MIT** (API; texto integral já copiado pelo Studio em `docs/licenses/CLAUDE-CODE-GAME-STUDIOS-MIT.txt`) | **78 `SKILL.md`** em `.claude/skills/` no HEAD (e no commit citado pelo Studio): `adopt`, `architecture-decision`, `architecture-review`, `art-bible`, `asset-audit`, `asset-spec`, `balance-check`, `brainstorm`, `bug-report`, `bug-triage`, `changelog`, `code-review`, `consistency-check`, `content-audit`, `create-architecture`, `create-control-manifest`, `create-epics`, `create-stories`, `day-one-patch`, `design-review`, `design-system`, `dev-story`, `estimate`, `gate-check`, `help`, `hotfix`, `launch-checklist`, `localize`, `map-systems`, `milestone-review`, `onboard`, `patch-notes`, `perf-profile`, `playtest-report`, `project-stage-detect`, `propagate-design-change`, `prototype`, `qa-plan`, `quick-design`, `regression-suite`, `release-checklist`, `retrospective`, `reverse-document`, `review-all-gdds`, `scope-check`, `security-audit`, `settings`, `setup-engine`, `skill-improve`, `skill-test`, `smoke-check`, `soak-test`, `sprint-plan`, `sprint-status`, `start`, `story-done`, `story-readiness`, `team-*` (7), `tech-debt`, `test-evidence-review`, `test-flakiness`, `test-helpers`, `test-setup`, `ux-design`, `ux-review`, `vertical-slice` | ★39.469, push 2026-11-09, criado 2026-02-12 | **Já é upstream de 7 skills do Studio** (commit `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418`, verificado: existe, 2026-10-19, "Release 1.2.0"). As 7 adaptadas **continuam presentes no HEAD** → sem quebra de proveniência. Restam **71 skills não aproveitadas**, entre elas `asset-audit`, `asset-spec`, `art-bible`, `skill-improve`, `skill-test`, `regression-suite`, `security-audit` — de interesse direto do Hub e da Forge | `ADAPT_ALLOWED` (MIT, manter aviso) |
| [`witnesstodark/mr-mak-workspace`](https://github.com/witnesstodark/mr-mak-workspace) | **MIT** (API; texto integral copiado pelo Studio em `docs/licenses/MR-MAK-WORKSPACE-MIT.txt`) | **20 skills** no HEAD (mesmas do ZIP guardado no Studio): `3d-production-routing`, `blender-game-animation`, `character-sheet-pipeline`, `fal-ai-generation`, `feature-handoff`, `game-animation-integration`, `game-audio-workflow`, `game-level-design`, `game-ui-workflow`, `game-vfx-workflow`, `gameplay-visual-review`, `higgsfield-workflow`, `image-reference-workflow`, `img2threejs`, `materials-to-game`, `motion-reference-workflow`, `plan`, `video-watch`, `voice-dictation-setup`, `workspace-authoring` | ★792, push 2026-11-12, criado 2026-09-15 | **Já é upstream de 5 skills do Studio** (commit `cf1e1260253a61499dc67fe2332a330bf1b85c14`, verificado: existe, 2026-11-06). É a **única fonte encontrada com skills de pipeline de asset** (Blender, character sheet, materiais, 3D→three.js) — domínio da Forge | `ADAPT_ALLOWED`, **exceto** `img2threejs` (Apache-2.0 próprio, ver auditoria) e `fal-ai-generation`/`higgsfield-workflow` (chamam serviços pagos → `RESEARCH_ONLY`) |
| [`TabooHarmony/roblox-brain`](https://github.com/TabooHarmony/roblox-brain) | **MIT** (API) | conhecimento de Roblox Studio para agentes | ★192, push 2026-10-15 | Fora do escopo atual (Roblox não é alvo declarado) | `RESEARCH_ONLY` |
| [`MRCalderon3D/everything-game-dev-code`](https://github.com/MRCalderon3D/everything-game-dev-code) | **MIT** (API) | "42 agents" + scaffold universal de game dev | ★109, push 2026-11-06 | Amostra de agentes (não skills) para game dev; comparar com os 78 itens do Claude-Code-Game-Studios antes de qualquer uso | `RESEARCH_ONLY` |
| [`devdavv/unity-ai-workflow`](https://github.com/devdavv/unity-ai-workflow) | **MIT** (API) | regras/agentes para Unity 6.2+ | ★47, push 2026-04-01 | Relevante só se Unity virar destino; Unity tem licença própria (ver Forge T14) | `RESEARCH_ONLY` |
| [`laurentvv/godot-skill-quality`](https://github.com/laurentvv/godot-skill-quality) | **MIT** (API) | skills `SKILL.md` para qualidade visual de cenas Godot 4 | ★0, criado 2026-11-01 | Projeto de 2 semanas, sem comunidade → risco de manutenção alto | `RESEARCH_ONLY` (reavaliar se Godot virar engine do Studio) |
| [`gomesgustavoo/vr-dev-skills`](https://github.com/gomesgustavoo/vr-dev-skills) | **MIT** (API) | skills para Meta Quest | ★10, push 2026-10-20 | fora do escopo | `RESEARCH_ONLY` |
| [`huayuehua15-netizen/gamedev-agent-skills`](https://github.com/huayuehua15-netizen/gamedev-agent-skills) | **MIT** (API) | skills 3D game dev, docs em chinês | ★0, push 2026-11-05 | barreira de idioma + maturidade zero | `RESEARCH_ONLY` |
| [`Yuki001/game-dev-skills`](https://github.com/Yuki001/game-dev-skills) | **NENHUMA** (API: `none`) | repositório pessoal de skills de jogos | ★116, push 2026-11-09 | popular, mas **sem licença**: não copiar, não adaptar, não redistribuir | **`BLOCKED`** (link apenas como referência de ideias, sem cópia) |
| [`indiesoftby/defold-agent-config`](https://github.com/indiesoftby/defold-agent-config) | **`NOASSERTION`** (API) — arquivo de licença não reconhecido, **não lido nesta sessão** | `AGENTS.md` + skills para Defold | ★108, push 2026-04-23 | Defold não é alvo; licença não confirmada | `RESEARCH_ONLY` |
| [`Firmansjk/BlenderGIS-Terrain-Export-AISkill`](https://github.com/Firmansjk/BlenderGIS-Terrain-Export-AISkill), [`ameratom/3d-text-animation-skill`](https://github.com/ameratom/3d-text-animation-skill) | **NENHUMA** (API: `none`) | templates de skill Blender/3D | ★0 | sem licença | **`BLOCKED`** |

> **Blender/ComfyUI/Aseprite/Godot/Unity/Unreal (servidores MCP):** a Forge já publicou matriz com licença verificada em 2026-11-14 para ~19 servidores (`Lia-Forge@main:docs/T14-AGENT-SKILLS-MCP-MATRIX.md`), incluindo `ahujasid/mcp-for-blender` (MIT), `Comfy-Org/comfy-mcp` (**dual AGPL-3.0/comercial → BLOCKED**), `artokun/comfyui-mcp` (MIT), `joenorton/comfyui-mcp-server` (Apache-2.0), `diivi/aseprite-mcp` (MIT + editor pago), `Coding-Solo/godot-mcp` (MIT), `CoplayDev/unity-mcp` (MIT), `chongdashu/unreal-mcp` e `flopperam/unreal-engine-mcp` (**sem licença → BLOCKED**), `pixellab-code/pixellab-mcp` (**sem licença → BLOCKED**). **Não duplicado aqui** — referência cruzada obrigatória antes de qualquer decisão sobre MCP de DCC.

### 4.2 Segurança, QA, revisão de código

| Fonte | Licença verificada | Conteúdo | Atividade | Utilidade | Classe proposta |
|---|---|---|---|---|---|
| [`Garyson26/Trident-SecOps-Skills`](https://github.com/Garyson26/Trident-SecOps-Skills) | **MIT** (`LICENSE` lido: © 2026 Garyson26) | **24 `SKILL.md`** em 75 blobs; um único `LICENSE` na raiz | ★42, push 2026-09-30, criado 2026-06-01 | Complementa `lia-security-review` (que é genérica e curta, 38 linhas) com procedimentos de SecOps; baixo volume de manutenção | `ADAPT_ALLOWED` (por skill, com revisão de conteúdo — instruções de segurança mal escritas são risco) |
| [`anthropics/skills` → `webapp-testing`](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | Apache-2.0 (`LICENSE.txt` da skill) | toolkit de teste de apps web locais com Playwright | push 2026-11-14 | Referência para evidência visual/testes web; **exige Playwright instalado** → não é skill offline | `ADAPT_ALLOWED` com `compatibility` explícita |
| [`Tariux/AI-Skills-Not-Awesome`](https://github.com/Tariux/AI-Skills-Not-Awesome) | **NENHUMA** (API: `none`) | prompts sistêmicos e padrões de comportamento | ★48, push 2026-11-15 | sem licença | **`BLOCKED`** |

### 4.3 Orquestração, memória e planejamento

| Fonte | Licença verificada | Conteúdo | Atividade | Utilidade | Classe proposta |
|---|---|---|---|---|---|
| [`Kc1t/alethe-orchestrate-skill`](https://github.com/Kc1t/alethe-orchestrate-skill) | **MIT** (cópia integral já vendorizada no Lia-Project, © 2026 Kauã Miguel) | skill v19 com `scripts/orchestrate.py`, `scripts/diagram.py`, `playbooks.yaml`, `prices.json`, `schemas/plan.schema.json`, `references/` (8), `assets/` (2 HTML + **5 marcas de terceiros**) | ★146, push 2026-11-04, criado 2026-10-19 | **Já está no ecossistema** (Lia-Project, com patches locais de segurança de 2026-10-28). Coordena CLIs externas; não instala nem comprova subagents | `ADAPT_ALLOWED` para o código (MIT), **com duas ressalvas**: scripts exigem análise de risco (`containsScripts: true`) e os assets de marca **não** são cobertos pela MIT |
| [`23blocks-OS/ai-maestro`](https://github.com/23blocks-OS/ai-maestro) | **MIT** (API) | orquestrador com sistema de skills e memória | ★853, push 2026-11-10 | Orquestração é responsabilidade dos **hosts** (Studio/Forge), não do Hub → fora da fronteira | `RESEARCH_ONLY` (destino: `OTHER`) |
| [`Ibrahim-3d/orchestrator-supaconductor`](https://github.com/Ibrahim-3d/orchestrator-supaconductor) | **AGPL-3.0** (API) | orquestração multiagente com execução paralela | ★384, push 2026-09-27 | **Copyleft de rede**: incompatível com distribuição fechada/empacotada sem abrir o derivado | **`BLOCKED`** para incorporação; `RESEARCH_ONLY` para padrões |
| [`multica-ai/andrej-karpathy-skills`](https://github.com/multica-ai/andrej-karpathy-skills) | **NENHUMA** (API: `none`) | `CLAUDE.md` derivado de observações públicas de Andrej Karpathy | ★233.323, push 2026-04-20 | extremamente popular, **sem licença** — e ainda deriva de declarações de terceiro | **`BLOCKED`** (não copiar; `open-agent-hub` declara derivar seus `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` daqui → contaminação a verificar se algum dia usarmos esse hub) |

### 4.4 MCP (protocolo, servidores e construção)

| Fonte | Licença verificada | Conteúdo | Atividade | Utilidade | Classe proposta |
|---|---|---|---|---|---|
| [`modelcontextprotocol/servers`](https://github.com/modelcontextprotocol/servers) | **`NOASSERTION`** (API). `LICENSE` **lido**: "transição de MIT para Apache-2.0"; contribuições novas = Apache-2.0; documentação (exceto specs) = **CC-BY-4.0**; contribuições antigas sem consentimento de relicenciamento **permanecem MIT** | servidores de referência do MCP | ★92.009, push 2026-11-12, criado 2024-11-19 | Referência de servidores; **licença por contribuição, não por repositório** → qualquer reuso exige identificar o arquivo e sua licença | `RESEARCH_ONLY` por padrão; `ADAPT_ALLOWED` **só** por arquivo com licença confirmada |
| [`anthropics/skills` → `mcp-builder`](https://github.com/anthropics/skills/tree/main/skills/mcp-builder) | Apache-2.0 (`LICENSE.txt` da skill); frontmatter `license: Complete terms in LICENSE.txt` | guia para construir servidores MCP em Python (FastMCP) ou Node/TS (SDK) | push 2026-11-14 | Insumo direto para o "MCP Workshop" do Hub **sem executar nada**: é instrução, não runtime | `ADAPT_ALLOWED` |
| [`modelcontextprotocol.io`](https://modelcontextprotocol.io/) | documentação do protocolo | — | — | não alcançado diretamente nesta sessão (limitação de rede do sandbox); usar o repositório oficial como fonte primária | pendente |

---

## 5. Catálogos, registries e "hubs" de terceiros (arte anterior do próprio produto)

Esta seção é a mais importante para o Hub: são soluções que **já fazem o que o Hub se propõe a fazer**. Nenhuma é recomendação de dependência.

| Fonte | O que faz | Licença | Evidência verificada | Leitura para o Hub | Classe |
|---|---|---|---|---|---|
| [`guanyang/open-agent-hub`](https://github.com/guanyang/open-agent-hub) | CLI "zero-dependency" (`scripts/hub.js`) que **linka** Skills, Agents e Commands para workspaces ou configuração global de 8 hosts | **MIT** (`LICENSE` lido: © 2026 guanyang) | 2.691 blobs, **114 `SKILL.md`**, **109 arquivos de licença**; `skills_index.json` (índice de metadados gerado por varredura), `skills_sources.json` (fontes para `oah sync`), `spec/Specification.md`, `template/`, `agents/`, `commands/`, `.claude-plugin`/`.codex-plugin`/`.cursor-plugin`; tabela de compatibilidade no README: Claude Code `.claude/`, Antigravity `.agents/`, Gemini CLI `.gemini/`, Codex `.codex/`, Cursor `.cursor/`, Trae `.trae/`, OpenCode `.opencode/`, Kiro `.kiro/` (projeto e global); declara derivar `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` de `multica-ai/andrej-karpathy-skills` (**sem licença**) | ★1.003, push 2026-11-15, criado 2026-01-13 | **Arte anterior direta.** Já resolve: ativação por host sem copiar (link), índice derivado por varredura, sync de fontes, templates. **Diferença essencial para o Hub:** ele **não** faz proveniência, licença por camada, quarentena, hash de integridade nem histórico de versões — que são exatamente as oito lacunas que o Hub se propõe a cobrir. O README dele também prova que "link em vez de cópia" é aceitável para usuários de 8 hosts | `REFERENCE` (arquitetura) · `RESEARCH_ONLY` (conteúdo, pela derivação não licenciada) |
| [`skills.sh`](https://skills.sh/) (Vercel) | diretório + leaderboard + CLI (`npx skills add owner/repo`, `npx skills find`, `npx skills list`) | CLI declarada MIT; diretório gratuito, sem tiers pagos | **fonte primária não lida**; três fontes secundárias: [rywalker.com/research/skills-sh](https://rywalker.com/research/skills-sh) (2026-06-11), [dev.to](https://dev.to/stevengonsalvez/skillssh-npm-for-agent-skills-35jc) (2026-07-10), [extensão VS Code "Skills.sh — Agent Skills Manager"](https://open-vsx.org/extension/AbelMak/skills-sh) (2026-03-25) | Diretórios canônicos declarados: `~/.agents/skills/` (skills.sh), `~/.claude/skills/`, `~/.cursor/skills/`, `~/.codeium/windsurf/skills/`, `~/.copilot/skills/`, `~/.codex/skills/`, `~/.roo/skills/`, `~/.gemini/skills/`, `~/.trae/skills/`, `~/.kiro/skills/`, `~/.continue/skills/` + nível de projeto. **Sem fluxo de submissão e sem revisão**: entrada por telemetria de instalação; ranking por contagem de instalação (jogoável); pesquisadores da Trail of Bits **teriam contornado o detector de skill maliciosa**; resposta do Vercel = parceria de scanning com Snyk, não revisão humana | `REFERENCE` (distribuição/descoberta) — e **evidência a favor** do desenho do Hub: catálogo local, revisão humana e proveniência são o que um diretório por telemetria não oferece | `REFERENCE` |
| [`hesreallyhim/awesome-claude-code`](https://github.com/hesreallyhim/awesome-claude-code) | lista curada de recursos | **CC-BY-NC-ND 4.0** (`LICENSE` lido: © 2026 hesreallyhim; "licensed under Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International"; o autor pede contato para usos modificados e diz ter adotado a licença para evitar apropriação) | ★58.057, push 2026-11-15 | lista de links | **`RESEARCH_ONLY`** — NC + ND impedem copiar, adaptar ou republicar, inclusive em catálogo interno derivado |
| [`VoltAgent/awesome-agent-skills`](https://github.com/VoltAgent/awesome-agent-skills) | "coleção curada de 1000+ agent skills" | **MIT** (API) | **a árvore tem 4 blobs e 0 `SKILL.md`** → é uma lista de **links**, não um acervo | ★37.204, push 2026-11-05 | Descoberta de candidatos; nada para importar | `RESEARCH_ONLY` |
| [`VoltAgent/awesome-claude-code-subagents`](https://github.com/VoltAgent/awesome-claude-code-subagents) | 100+ **subagentes** Claude Code | **MIT** (API) | subagentes ≠ skills (são papéis com prompt, não pacotes `SKILL.md`) | ★26.563, push 2026-11-02 | Útil ao Studio/orquestração, não ao catálogo de skills do Hub | `RESEARCH_ONLY` (destino: `STUDIO`) |
| [`travisvn/awesome-claude-skills`](https://github.com/travisvn/awesome-claude-skills) | lista curada de skills | **NENHUMA** (API: `none`; raiz contém só `.gitignore`, `CONTRIBUTING.md`, `README.md`) | ★15.823, push 2026-04-28 (8 meses sem atualização) | lista de links sem licença e sem manutenção | **`BLOCKED`** para cópia/derivação; links podem ser visitados individualmente e cada alvo auditado por conta própria |
| [`mdskills.ai`](https://www.mdskills.ai/specs/skill-md), [`agentman.ai`](https://agentman.ai/blog/build-your-first-agent-skill-skillmd-anatomy), [`skills.wondel.ai`](https://skills.wondel.ai/learn/agent-skills-standard/) | diretórios/artigos sobre o formato | conteúdo de site | fontes secundárias encontradas em busca (2026-06/08) | confirmam o mesmo frontmatter de 6 campos e a adoção multi-host; **não substituem a especificação** | `REFERENCE` |

---

## 6. Consolidado por classe de decisão proposta

| Classe | Itens | Observação |
|---|---|---|
| `USE_AS_IS` (norma/standard) | `agentskills/agentskills`, `agentskills.io/specification` | adotar como formato canônico já é o comportamento implementado no validador do Hub |
| `ADAPT_ALLOWED` | `anthropics/skills` (por skill), `obra/superpowers`, `mattpocock/skills`, `Donchitos/Claude-Code-Game-Studios`, `witnesstodark/mr-mak-workspace` (exceto `img2threejs`, `fal-ai-generation`, `higgsfield-workflow`), `Garyson26/Trident-SecOps-Skills`, `Kc1t/alethe-orchestrate-skill` (com ressalvas), `abdullahkhawer/devops-skills` | todos exigem preservar aviso + atribuição; ver auditoria |
| `FORK_CANDIDATE` | **nenhum** nesta rodada | não há justificativa de manutenção para um fork próprio de coleção alheia enquanto houver adaptação pontual |
| `INDEPENDENT_REIMPLEMENTATION` | padrões de `guanyang/open-agent-hub` (índice derivado, link por host), `skills.sh` (manifesto de publicação), `sickn33` (esquemas de índice/score) | reimplementar a **ideia** em código Lia, sem copiar material protegido |
| `RESEARCH_ONLY` | `vercel-labs/agent-skills` (pendente), `sickn33/agentic-awesome-skills` (acervo), `modelcontextprotocol/servers`, `jnMetaCode/superpowers-zh`, coleções pessoais MIT, `23blocks-OS/ai-maestro`, `hesreallyhim/awesome-claude-code`, listas `VoltAgent`, jogos fora do escopo | interessante, sem base suficiente para incorporar agora |
| `BLOCKED` | `Yuki001/game-dev-skills`, `multica-ai/andrej-karpathy-skills`, `Tariux/AI-Skills-Not-Awesome`, `travisvn/awesome-claude-skills`, `Ibrahim-3d/orchestrator-supaconductor` (AGPL-3.0), `Firmansjk/…`, `ameratom/…`, `Comfy-Org/comfy-mcp` (dual AGPL/comercial, via Forge T14), `chongdashu/unreal-mcp`, `flopperam/unreal-engine-mcp`, `pixellab-code/pixellab-mcp` | ausência de licença **não** é permissão; AGPL é incompatível com a distribuição pretendida |

---

## 7. Estado da análise por item (o que falta fazer)

| Nível | Significado | Itens nesta rodada |
|---|---|---|
| **Encontrado** | apareceu em busca/API | ~40 repositórios listados |
| **Analisado (metadados)** | licença SPDX, atividade, conteúdo da árvore verificados | 24 |
| **Analisado (conteúdo)** | `LICENSE` e/ou `SKILL.md`/`README` lidos | 12 |
| **Analisado (por skill)** | licença de **cada** skill verificada individualmente | **1** (`anthropics/skills`: 19 `LICENSE.txt` confirmados na árvore, 1 lido) |
| **Aprovado para uso** | decisão humana registrada | **0** |
| **Incorporado a um projeto Lia** | código/conteúdo integrado | **0 por esta pesquisa** — o que já existe (`alethe` no Project, 12 adaptadas no Studio) veio de sessões anteriores e está auditado no inventário |

**Nenhuma skill de terceiros foi aprovada aqui.** Aprovação exige decisão humana (D-11, D-16, D-18, D-20 do `docs/DECISION-REGISTER.md`).

## 8. Priorização (critérios da Missão 8)

Pontuação 1–5 por critério, apenas para ordenar trabalho de análise — **não** é aprovação.

| # | Fonte | Utilidade Lia | Maturidade | Manutenção | Compatibilidade técnica | Clareza de licença | Facilidade de integração | Valor estratégico | **Total** | Próxima ação |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `agentskills/agentskills` + spec | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **35** | já adotado como formato; manter vigilância de versão |
| 2 | `anthropics/skills` (`skill-creator`, `mcp-builder`, `webapp-testing`, `brand-guidelines`) | 5 | 5 | 5 | 5 | 4 (por skill) | 4 | 5 | **33** | ler `LICENSE.txt` das 4 skills alvo e decidir adaptação |
| 3 | `Donchitos/Claude-Game-Studios` (71 skills não aproveitadas) | 5 | 4 | 4 | 5 | 5 | 4 | 4 | **31** | selecionar `asset-audit`, `asset-spec`, `skill-improve`, `skill-test`, `regression-suite`, `security-audit` |
| 4 | `witnesstodark/mr-mak-workspace` (15 skills não aproveitadas) | 5 | 4 | 3 | 4 | 4 (img2threejs à parte) | 4 | 4 | **28** | selecionar as de pipeline de asset para a Forge |
| 5 | `obra/superpowers` (padrão de empacotamento multi-host) | 4 | 4 | 4 | 5 | 5 | 3 | 5 | **30** | estudar `.*-plugin/` como referência de contrato de distribuição |
| 6 | `guanyang/open-agent-hub` | 4 | 3 | 4 | 4 | 3 (derivação não licenciada) | 3 | 5 | **26** | ler `spec/Specification.md` e `skills_index.json` para o contrato de exportação |
| 7 | `sickn33/agentic-awesome-skills` (esquemas) | 4 | 3 | 4 | 4 | 3 | 2 | 4 | **24** | ler `schemas/aas-v1/skills-index.v1` e `skill-score.v1` |
| 8 | `mattpocock/skills` | 3 | 4 | 4 | 5 | 5 | 4 | 3 | **28** | aproveitar skills de `engineering/`; ignorar `in-progress/` |
| 9 | `Garyson26/Trident-SecOps-Skills` | 3 | 3 | 3 | 5 | 5 | 4 | 3 | **26** | comparar com `lia-security-review` antes de adaptar |
| 10 | `Kc1t/alethe-orchestrate-skill` | 3 | 3 | 3 | 3 | 4 | 2 (scripts + marcas) | 3 | **21** | manter vendorizado no Project; **não** redistribuir pelo Hub sem remover assets de marca |
| 11 | `skills.sh` / `vercel-labs/agent-skills` | 3 | 4 | 4 | 4 | 2 | 2 | 4 | **23** | confirmar licença na fonte primária antes de qualquer publicação externa |
| 12 | `modelcontextprotocol/servers` | 3 | 5 | 5 | 3 | 2 (mista) | 2 | 3 | **23** | usar como referência por arquivo, nunca por repositório |

**Redundantes / obsoletos / abandonados / com risco de manutenção:**

| Item | Motivo |
|---|---|
| `travisvn/awesome-claude-skills` | sem licença **e** sem push desde 2026-04-28 |
| `laurentvv/godot-skill-quality`, `huayuehua15-netizen/gamedev-agent-skills`, `Firmansjk/…`, `ameratom/…` | ★0, criados há dias/semanas, sem comunidade |
| `sickn33/agentic-awesome-skills` (acervo) | 9.454 `SKILL.md` com duplicação massiva entre `plugins/` (2.891 vs 2.870) → custo de curadoria maior que o benefício |
| `VoltAgent/awesome-agent-skills` | descrição promete "1000+ skills"; a árvore tem 4 arquivos — é lista de links |
| coleções pessoais MIT (`michaelboeding`, `crystian`, `beeyev`, `milanvrskovy`, `OpenMatter-Network`) | baixo volume, sem manutenção previsível, sem valor estratégico |
| `jnMetaCode/superpowers-zh` | derivado traduzido; ecossistema Lia trabalha em pt-BR |
| `23blocks-OS/ai-maestro`, `Ibrahim-3d/orchestrator-supaconductor` | orquestração é responsabilidade de host (Studio/Forge), não do Hub; o segundo é AGPL-3.0 |
