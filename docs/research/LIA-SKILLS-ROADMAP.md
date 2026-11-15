# Roadmap de Skills próprias da Lia (`lia-`)

**Documento:** `docs/research/LIA-SKILLS-ROADMAP.md` (Missões 4 e 8)
**Agente:** Research — Lia Agent Hub · **Branch:** `arena/db625478-lia-agenthub`
**Data:** 2026-11-15 (UTC)
**Estado:** `PROPOSED`. **Nenhuma skill foi criada, implementada ou publicada nesta rodada.** O mandato é explícito: primeiro inventário e priorização, não produção em massa.

Fontes de evidência: [`LIA-SKILLS-INVENTORY.md`](LIA-SKILLS-INVENTORY.md) (48 skills Lia + capacidades relacionadas), [`THIRD-PARTY-SKILLS-CATALOG.md`](THIRD-PARTY-SKILLS-CATALOG.md) (fontes externas) e [`SKILL-LICENSE-AND-PROVENANCE-AUDIT.md`](SKILL-LICENSE-AND-PROVENANCE-AUDIT.md) (licenças e proveniência).

---

## 1. Regra de admissão de uma nova skill `lia-`

Uma oportunidade só vira skill se passar nos **seis** testes abaixo. Isso existe para impedir que o catálogo cresça por duplicação.

| # | Teste | Reprova se… |
|---|---|---|
| T1 | **Problema real e repetido** | o problema ocorreu uma vez ou é hipotético |
| T2 | **Nenhuma skill existente cobre** | já há skill Lia com a mesma responsabilidade (mesmo que em outro repositório) |
| T3 | **É instrução, não runtime** | exige executar, orquestrar, instalar ou guardar credencial — isso é do host (Studio/Forge/Project), nunca do Hub |
| T4 | **Saída verificável** | não produz evidência revisável (relatório, matriz, registro com hashes) |
| T5 | **Reuso por ≥2 produtos Lia** | só serve a um repositório e a um fluxo pontual |
| T6 | **Base de licença limpa** | deriva de fonte sem licença, ou mistura camadas (código/conteúdo/marca) sem separação |

---

## 2. Oportunidades priorizadas

### 2.1 Resumo (ordem de prioridade)

| # | Skill proposta | Problema | Criação | Vale criar agora? | Total (35) |
|---|---|---|---|---|---:|
| 1 | `lia-license-audit` | 47 skills Lia sem licença no payload; 4 repositórios sem `LICENSE`; auditoria de terceiros feita à mão | Original (método já executado nesta rodada) | **SIM — agora** | 33 |
| 2 | `lia-skill-intake` | não há procedimento repetível para admitir skill de terceiro (licença, proveniência, scripts, unicode, quarentena) | Original | **SIM — agora** | 32 |
| 3 | `lia-provenance-record` | cadeia de derivação registrada em dois formatos diferentes (`## Origem` no Studio, `UPSTREAM.md` no Project) | Original | **SIM — agora** | 31 |
| 4 | `lia-skill-validator` | validação estrutural existe em código no Hub e em teste no Project, mas não como procedimento aplicável em qualquer repo | Original (consolida prática existente) | **SIM — agora** | 31 |
| 5 | `lia-upstream-drift-watch` | 3 commits upstream fixados (`05ad7c8`, `cf1e126`, alethe v19) podem divergir do HEAD sem que ninguém perceba | Original | **SIM — agora** | 30 |
| 6 | `lia-repo-audit` | auditoria de repositórios/branches/commits com classe de evidência é feita manualmente a cada sessão | Original | **SIM — agora** | 30 |
| 7 | `lia-research-evidence` | classes `IMPLEMENTED/EXECUTED/VALIDATED/PROPOSED/RESEARCH` são regra em `AGENTS.md`, mas não há procedimento que as aplique a um relatório | Original | **SIM — agora** (baixo custo) | 29 |
| 8 | `lia-capability-catalog-sync` | quatro catálogos coexistem (Project `AGENT-SKILLS-CATALOG.md`, Forge `registry.mjs` 49, Project `lia-capability-catalog` 44, Hub `index.json`) | Original | **Próxima fase** (depende de decisão de fronteira) | 28 |
| 9 | `lia-mcp-catalog` | MCP da Forge (10 tools) e 19 servidores de terceiros já mapeados, mas sem procedimento de catalogação sem execução | Original | **Próxima fase** | 27 |
| 10 | `lia-package-export` | exportar `.lia-capability` com `NOTICE`/`UPSTREAM.md`/licença por camada exige procedimento, não só código | Original | **Próxima fase** (depende do Hub integrado) | 27 |
| 11 | `lia-brand-consistency` | **duplicação existente**: `lia-brand-check` (Forge) ≈ `lia-brand-consistency-review` (Model-Lab) | Consolidação | **Decisão humana antes** | 26 |
| 12 | `lia-handoff` | `lia-task-handoff` (Studio) e fluxos de handoff do Project/Forge repetem o mesmo contrato | Consolidação | **Roadmap** | 24 |
| 13 | `lia-skill-localization` | skills externas úteis estão em inglês; o ecossistema Lia trabalha em pt-BR | Original | **Roadmap** | 22 |
| 14 | `lia-orchestration-contract` | **tripla sobreposição**: `lia-agent-orchestration` (Project), `multi-agent-orchestration` (Model-Lab), `alethe` (terceiro) | Consolidação | **Roadmap + decisão humana** | 21 |

### 2.2 Fichas das sete primeiras (as que valem agora)

#### 1. `lia-license-audit`

| Campo | Valor |
|---|---|
| Problema | O ecossistema Lia tem **47 skills autorais/adaptadas sem arquivo de licença dentro do payload**, **4 repositórios sem `LICENSE` na raiz** (Project, Model-Lab, Go, AgentHub) e dezenas de candidatos externos cuja licença só é verificável arquivo a arquivo (`anthropics/skills` tem 19 `LICENSE.txt`; `sickn33` tem 648 arquivos de licença; `modelcontextprotocol/servers` é misto em transição). Hoje essa análise é refeita à mão a cada sessão |
| Projetos Lia que a usariam | **Hub** (intake e exportação), **Project** (21 skills + AIRI vendado + `alethe`), **Studio** (12 adaptadas), **Forge** (SBOM de 464 pacotes + 1 skill), **Model-Lab** (9 skills + pesos/modelos), **Go** |
| Entradas | repositório, branch, commit, caminho do payload; texto de licença encontrado; declaração em README (quando não há arquivo); lista de dependências; inventário de assets de marca |
| Saídas | registro por item com: classe (`USE_AS_IS`/`ADAPT_ALLOWED`/`FORK_CANDIDATE`/`INDEPENDENT_REIMPLEMENTATION`/`RESEARCH_ONLY`/`BLOCKED`), obrigações de atribuição/redistribuição/código-fonte, restrições comerciais, camadas separadas (código/conteúdo/pesos/dados/marca), nível de confiança e pendências humanas |
| Responsabilidades | classificar com evidência e **nunca** inferir permissão; separar camadas; registrar pendência humana quando ambíguo |
| O que **não** faz | dar parecer jurídico, aceitar termos, decidir distribuição comercial, remover avisos |
| Referências externas | `agentskills.io/specification` (campo `license`); `anthropics/skills` (licença por skill + `THIRD_PARTY_NOTICES.md`); `modelcontextprotocol/servers/LICENSE` (licença mista em transição); `Lia-Forge:THIRD_PARTY_NOTICES.md` (padrão de SBOM); `Lia-Model-Lab:.agents/skills/model-license-release-review` (método análogo para pesos) |
| Tipo de criação | **Original** — o método foi executado nesta rodada e está documentado na auditoria de licença; nenhuma fonte externa é copiada |
| Decisão | **criar agora**. É a skill que destrava todas as outras: sem licença resolvida, nada pode ser redistribuído |

#### 2. `lia-skill-intake`

| Campo | Valor |
|---|---|
| Problema | Admitir uma skill de terceiro exige uma sequência fixa (identificar origem → ler licença → verificar commit → inspecionar payload sem executar → checar scripts/unicode/marcas → quarantinar → registrar → decidir). O Hub implementa partes disso em código (`safe_extract`, `unicode_policy`, `importer`), mas **não existe o procedimento** para o humano/agente que faz curadoria |
| Projetos Lia | **Hub** (função central), **Project** (já fez isso com `alethe` e com 21 derivações do AIRI), **Studio** (fez com 12 adaptações) |
| Entradas | URL/commit ou caminho local; resultado de `lia-license-audit`; inventário de arquivos |
| Saídas | decisão de admissão com classe, registro de proveniência pronto para `source.derivedFrom`, lista do que foi removido (hooks, scripts, marcas, credenciais) e do que foi acrescentado, e o estado explícito: **encontrado → analisado → catalogado → aprovado → incorporado** |
| Responsabilidades | garantir que nenhum recurso vire "aprovado" por ter sido encontrado; impedir cópia de material sem licença |
| Referências externas | `anthropics/skills/skill-creator` (Apache-2.0, por skill); `guanyang/open-agent-hub` (link por host em vez de cópia); `sickn33/agentic-awesome-skills` (`schemas/aas-v1/*`, `verification/`) |
| Tipo de criação | **Original**, com `INDEPENDENT_REIMPLEMENTATION` de padrões observados |
| Decisão | **criar agora** |

#### 3. `lia-provenance-record`

| Campo | Valor |
|---|---|
| Problema | Dois formatos convivem: Studio usa seção `## Origem` no próprio `SKILL.md` + `THIRD_PARTY_NOTICES.md` na raiz; Project usa `LICENSE` + `UPSTREAM.md` dentro do payload. O modelo do Hub tem `source.upstream/commit/method/originalName` e `versionOf`, mas **nenhum campo de derivação** (lacuna L-04). Resultado: a cadeia se perde quando a skill viaja sozinha |
| Projetos Lia | todos os que publicam ou consomem skills derivadas |
| Entradas | origem imediata (repo/branch/commit), upstream real (projeto/URL/arquivo/commit/data), licença por camada, transformação, remoções, acréscimos |
| Saídas | bloco de proveniência canônico (§7.2 da auditoria) pronto para `UPSTREAM.md` **dentro do payload** e para o campo aditivo `source.derivedFrom` proposto |
| Referências externas | `Kc1t/alethe-orchestrate-skill` + `Lia-Project:.agents/skills/alethe/UPSTREAM.md` (melhor exemplo interno); `witnesstodark/mr-mak-workspace` (`THIRD_PARTY_NOTICES.md` separando MIT do Apache-2.0 de `img2threejs`) |
| Tipo de criação | **Original** |
| Decisão | **criar agora** — resolve L-01 e L-04 sem mudar contrato de produção |

#### 4. `lia-skill-validator`

| Campo | Valor |
|---|---|
| Problema | A especificação tem regras objetivas (`name` 1–64 minúsculo e igual ao nome da pasta, `description` ≤1.024, `compatibility` ≤500, corpo <500 linhas, sem chaves fora dos 6 campos, referências a arquivos existentes). O Hub valida isso em `domain/skills.py`; o Project tem `tools/test_agent_skills.py` (que reprova skill fora do catálogo). **Nenhum dos dois é utilizável por Studio/Forge/Model-Lab**, e há três defeitos conhecidos de importação (L-02 descrição vazia, L-03 `metadata` aninhado ignorado, L-05 aviso espúrio de pasta) |
| Projetos Lia | todos os 5 que têm skills |
| Entradas | pasta da skill; nome da pasta; conjunto de arquivos do payload |
| Saídas | relatório com erros/avisos por código (`NO_FRONTMATTER`, `MISSING_FIELD`, `UNKNOWN_FIELD`, `NAME_FORMAT`, `NAME_FOLDER_MISMATCH`, `DESCRIPTION_TOO_LONG`, `COMPATIBILITY_TOO_LONG`, `EMPTY_BODY`, `BOM_PRESENT`, referências quebradas) + veredito "pode publicar / corrigir antes" |
| Referências externas | `agentskills.io/specification` (fonte primária lida nesta sessão); `anthropics/skills/skill-creator` e `skill-test` (upstream MIT do Claude-Code-Game-Studios tem `skill-improve`/`skill-test` — comparar antes de escrever) |
| Tipo de criação | **Original** (procedimento), reimplementando regras da especificação |
| Decisão | **criar agora** |

#### 5. `lia-upstream-drift-watch`

| Campo | Valor |
|---|---|
| Problema | Três commits upstream estão fixados em produção Lia: `05ad7c8a5b…` (Claude-Code-Game-Studios), `cf1e126025…` (mr-mak-workspace), alethe **v19** (`c36c341c34…` como comparação anterior). Nesta sessão todos foram **verificados como existentes**, e as 7 skills adaptadas do primeiro continuam no HEAD (que hoje tem 78). Nada garante que continuem: upstream pode renomear, relicenciar ou remover |
| Projetos Lia | Studio (12 adaptadas), Project (`alethe`), Forge (dependências npm/MCP), Hub (especificação Agent Skills) |
| Entradas | par (repositório upstream, commit fixado); lista de arquivos derivados |
| Saídas | relatório de divergência: commit ainda existe? HEAD mudou o quê nos arquivos de origem? licença mudou? houve renomeação? qual o impacto na skill derivada? |
| Referências externas | prática de `UPSTREAM.md` do `alethe` ("antes de atualizar, comparar o upstream por conteúdo") |
| Tipo de criação | **Original** |
| Decisão | **criar agora** (baixo custo, evita surpresa de licenciamento) |

#### 6. `lia-repo-audit`

| Campo | Valor |
|---|---|
| Problema | Toda sessão de pesquisa refaz o mesmo trabalho: listar repositórios, branches, commits, árvores e separar o que está em `main` do que só existe em branch de sessão. Nesta rodada foram 13 repositórios e ~35 branches. Sem procedimento, cada agente chega a contagens diferentes |
| Projetos Lia | todos; especialmente o Hub (que precisa saber o que catalogar) |
| Entradas | organização/usuário, repositórios, branches de interesse |
| Saídas | tabela com repo/branch/commit/data/método de inspeção + contagens verificáveis + distinção explícita `main` × branch não integrada |
| Referências externas | `Lia-Forge:docs/T14-AGENT-SOLUTIONS-CATALOG.md` (método declarado: API, sem clone, com data); `Lia-AgentHub@arena/a92004be:docs/research/REPOSITORY-AND-BRANCH-AUDIT.md` (auditoria anterior — **não duplicar**, referenciar) |
| Tipo de criação | **Original** |
| Decisão | **criar agora** |

#### 7. `lia-research-evidence`

| Campo | Valor |
|---|---|
| Problema | As classes de evidência são obrigatórias por regra (`AGENTS.md` do Hub; documentos da Forge e do Project usam `RESEARCH`, `PROPOSED`, `NOT-TESTED`, `BLOCKED`), mas não há procedimento que as aplique de forma consistente. Risco concreto observado: um relatório chamar de "validado" o que foi apenas executado com stub |
| Projetos Lia | todos os agentes de pesquisa |
| Entradas | rascunho de relatório + lista de afirmações |
| Saídas | cada afirmação rotulada (`IMPLEMENTED`/`EXECUTED`/`VALIDATED`/`PROPOSED`/`PLANNED`/`RESEARCH`/`UNKNOWN`) com a evidência que a sustenta e o que falta para subir de classe |
| Referências externas | nenhuma necessária; base normativa interna |
| Tipo de criação | **Original** |
| Decisão | **criar agora** (custo quase zero, efeito imediato na qualidade dos relatórios) |

---

## 3. Oportunidades adiadas — e por quê

| Skill proposta | Por que **não** agora |
|---|---|
| `lia-capability-catalog-sync` | depende de decidir a **fronteira** entre os quatro catálogos existentes. Sincronizar antes de decidir cria acoplamento. Exige decisão humana (D-07, D-09) |
| `lia-mcp-catalog` | útil, mas o Hub ainda não integra MCP de ponta a ponta (`_detect_type` só reconhece `mcp-server` por `package.json`), e a Forge já tem matriz própria de 19 servidores (T14, 2026-11-14). Risco de duplicar |
| `lia-package-export` | depende de o Hub estar integrado em `main` e de a convenção de empacotamento (§7.4 da auditoria) ser aprovada |
| `lia-brand-consistency` | **consolidação**, não criação: `lia-brand-check` (Forge) e `lia-brand-consistency-review` (Model-Lab) já existem e são boas. Fundir sem decisão humana quebraria referências nos dois repositórios |
| `lia-handoff` | `lia-task-handoff` (Studio) já é canônica e bem escrita; generalizar exige acordo entre Studio e Project |
| `lia-skill-localization` | relevante (todo o acervo externo útil está em inglês), mas só faz sentido depois que houver fluxo de admissão. Precedente a estudar: `jnMetaCode/superpowers-zh` (derivado traduzido de coleção MIT) |
| `lia-orchestration-contract` | três implementações sobrepostas e uma delas é de terceiro com scripts e marcas. Consolidar exige decisão de produto e análise de risco (D-18) |
| `lia-asset-pipeline`, `lia-blender-workflow` (sugeridas no mandato) | **não criar como skill**: pipeline de assets é responsabilidade da **Forge**, que já tem `shared/capabilities/registry.mjs` (49 capacidades), Workflow Engine, Provider Hub e um servidor MCP com 10 tools. Uma skill Lia sobre isso duplicaria runtime. O que cabe ao Hub é **catalogar** as capacidades da Forge, não reescrevê-las |
| `lia-ui-ux-review` (sugerida no mandato) | já existe: `lia-ui-quality-review` (Project, 12 linhas) + `.claude/rules/interface.md` (Forge) + `docs/design/UI-UX-AUDIT.md` (branch de UI/UX do Hub). **Reutilizar**, não criar |
| `lia-agent-orchestration` (sugerida no mandato) | já existe com esse nome exato no Project (65 linhas) + `multi-agent-orchestration` no Model-Lab + `docs/project/AGENT-ORCHESTRATION.md`. **Reutilizar/consolidar** |

---

## 4. Priorização (critérios da Missão 8)

Escala 1–5. **Utilidade** = quantos produtos Lia se beneficiam; **Maturidade** = quanto do método já existe documentado; **Manutenção** = custo de manter correta (5 = barato); **Compatibilidade** = encaixe no formato Agent Skills e no modelo do Hub; **Licença** = clareza da base legal (5 = original Lia); **Integração** = facilidade de publicar/consumir; **Estratégico** = quanto destrava outras decisões.

| Skill | Util. | Mat. | Manut. | Compat. | Licença | Integr. | Estratég. | **Total** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `lia-license-audit` | 5 | 5 | 4 | 5 | 5 | 4 | 5 | **33** |
| `lia-skill-intake` | 5 | 4 | 4 | 5 | 5 | 4 | 5 | **32** |
| `lia-provenance-record` | 5 | 5 | 4 | 5 | 5 | 4 | 3 | **31** |
| `lia-skill-validator` | 5 | 4 | 4 | 5 | 5 | 4 | 4 | **31** |
| `lia-upstream-drift-watch` | 4 | 4 | 4 | 5 | 5 | 4 | 4 | **30** |
| `lia-repo-audit` | 5 | 5 | 4 | 5 | 5 | 3 | 3 | **30** |
| `lia-research-evidence` | 5 | 5 | 5 | 4 | 5 | 4 | 2 | **29** *(custo mínimo)* |
| `lia-capability-catalog-sync` | 5 | 3 | 3 | 4 | 5 | 3 | 5 | **28** |
| `lia-mcp-catalog` | 4 | 3 | 3 | 4 | 5 | 3 | 4 | **26**→**27** com `lia-skill-validator` pronta |
| `lia-package-export` | 4 | 3 | 3 | 5 | 5 | 3 | 4 | **27** |
| `lia-brand-consistency` | 4 | 5 | 3 | 5 | 5 | 2 | 2 | **26** |
| `lia-handoff` | 4 | 5 | 3 | 5 | 5 | 2 | 1 | **25**→**24** (baixa urgência) |
| `lia-skill-localization` | 3 | 2 | 3 | 4 | 4 | 3 | 3 | **22** |
| `lia-orchestration-contract` | 4 | 4 | 2 | 3 | 3 | 2 | 3 | **21** |

**Sequência recomendada (3 ondas, sem datas — datas são decisão humana):**

1. **Onda 1 — confiança:** `lia-license-audit` → `lia-provenance-record` → `lia-skill-validator`. Sem estas três, nada pode ser distribuído com honestidade.
2. **Onda 2 — admissão:** `lia-skill-intake` → `lia-upstream-drift-watch` → `lia-repo-audit` → `lia-research-evidence`.
3. **Onda 3 — catálogo:** `lia-capability-catalog-sync` → `lia-mcp-catalog` → `lia-package-export`, todas dependentes de decisão de fronteira.

---

## 5. Redundâncias, obsolescência e risco de manutenção (dentro da Lia)

| Item | Situação | Recomendação |
|---|---|---|
| `lia-brand-check` (Forge) × `lia-brand-consistency-review` (Model-Lab) | **mesma responsabilidade**, mesma saída `OK/RISCO/PENDING`, dois textos diferentes, dois repositórios | consolidar em uma skill compartilhada; decisão humana (P-2 da auditoria trata da camada de marca) |
| `lia-agent-orchestration` (Project) × `multi-agent-orchestration` (Model-Lab) × `alethe` (terceiro vendorizado) | três respostas para delegação de trabalho; a terceira tem scripts e marcas de terceiros | definir **uma** autoridade de contrato (provavelmente `docs/project/AGENT-ORCHESTRATION.md`) e fazer as outras apontarem para ela |
| `lia-test-discipline` + `lia-release-gate` (Project) × `verification-before-completion`/`test-driven-development` (obra/superpowers, MIT) | sobreposição conceitual com fonte externa de alta qualidade | não adaptar por adaptar: as skills do Project são específicas das suítes Lia (Python `tools/`, Node `Tests/tools`, Vitest) — **manter** e citar o externo como referência |
| 8 de 9 skills do Model-Lab e 2 do Project sem prefixo `lia-` | identidade inconsistente (10 casos) | decidir renomeação (muda caminhos referenciados por docs e testes) ou adotar metadado explícito de autoria |
| 39 das 48 skills fora de `main` | risco de perda/obsolescência: work de sessão não integrado | promover o que for aprovado para `main` — decisão humana, fora do escopo desta pesquisa |
| `docs/Mr-Mak-Skills-Free.zip` (9,9 MB) dentro do Lia-Studio | conteúdo de terceiros versionado num repositório Lia, sem comparação arquivo a arquivo com a fonte pública (registrado pelo próprio Studio) | remover do repositório e manter apenas a referência ao upstream MIT + commit |
| Skills do Model-Lab com "descoberta automática não comprovada" | risco de capacidade existir e nunca ser usada | registrar no catálogo do Hub o estado **real** (`IMPLEMENTED`, não `VALIDATED`) |
| `lia-release-gate`, `stage-runtime-debugging`, `lia-windows-electron-validation` | exigem **Windows** para validação real; nenhuma foi validada nesta pesquisa | manter estado `EXECUTED/VALIDATED: não` até haver evidência em máquina Windows |

---

## 6. O que este roadmap não autoriza

- **Não** autoriza criar, publicar ou distribuir nenhuma skill.
- **Não** autoriza copiar conteúdo de terceiros: as referências externas são fontes de método, e qualquer adaptação depende da auditoria de licença.
- **Não** decide fronteiras entre Hub, Studio, Forge e Project — isso é `docs/architecture/PRODUCT-BOUNDARIES.md` (entregável da Fase 0 ainda não produzido nesta branch) e decisão humana.
- **Não** define datas, responsáveis nem esforço. Define **ordem** e **critério**.
