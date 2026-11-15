# Fase 0 — Relatório final do Agent 0

**Documento:** `docs/PHASE-0-FINAL-REPORT.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Data:** 2026-11-15 (UTC)
**Natureza:** relatório executivo consolidado. **Nenhuma implementação foi realizada.** A Fase 1 não foi iniciada.

---

## 1. Identificação da entrega

| Item | Valor |
|---|---|
| Repositório | `BloomRX/Lia-AgentHub` |
| **Branch criada** | `arena/a92004be-lia-agenthub` |
| **Branch de origem** | `main` |
| **Commit inicial** | `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` — *"Kit Marca Lia"* (2026-11-14 22:35 -0300) |
| **Commit final** | registrado em §12 deste documento e no commit desta entrega |
| Merge em `main` | **Não** (proibido nesta fase) |
| PR aberto | **Nenhum** |
| Alteração da branch padrão do GitHub | **Não** |
| Alteração em Lia-Studio / Lia-Forge / Lia-Project | **Não** — clones somente-leitura em `/tmp`, fora do workspace |

---

## 2. Resumo executivo

> **O Lia Agent Hub deve existir como aplicação independente — mas não como o produto que a visão inicial sugere.**
>
> A auditoria encontrou **oito lacunas transversais** que nenhum dos três produtos Lia atende: registro de proveniência, pipeline de intake, formato de pacote portátil, análise de licença, contrato de distribuição, detecção de conteúdo malicioso em prosa, versionamento de capacidade e catálogo de MCP. **Nenhuma delas exige executar nada.**
>
> O código maduro do ecossistema confirma essa leitura: o Studio tem funções puras de permissão e catálogo de Skills; o Forge tem um registry de capacidades e um adapter SDK; o Project tem o melhor modelo de dados (8 camadas) — mas tudo isso está **em branches não integradas**, e **nada** disso é proveniência ou distribuição.
>
> A recomendação é um produto que **organiza, valida estrutura, registra decisão humana, versiona e empacota** capacidades. Isso é entregável offline, sozinho, sem runtime, sem rede e sem modelo — e é a única posição que não exige afirmar o que não se pode provar.

### 2.1 As seis conclusões

| # | Conclusão | Evidência |
|---|---|---|
| 1 | **O produto é viável e tem escopo próprio** | 8 lacunas confirmadas; nenhuma é atendida por Studio, Forge ou Project |
| 2 | **O escopo correto é registro, não runtime** | Teste T1–T5 (`PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §1.3) rejeita execução, orquestração, credencial e assets |
| 3 | **O formato Agent Skills é a única interoperabilidade gratuita** | Padrão aberto, 6 campos, `.agents/skills/` já usado pelo Studio |
| 4 | **Desktop Windows, núcleo Python stdlib, UI web local, PyInstaller** | Única combinação que passa K1 (sem runtime para o usuário) e K2 (domínio puro) |
| 5 | **O MVP entrega valor sem executar nada** | M1–M8: biblioteca, import, validação, contenção, proveniência, versão, pacote, índice |
| 6 | **Test Lab não pertence ao MVP** | Não há sandbox comprovado em Windows; `D-05` e `D-18` abertos |

### 2.2 O que isso muda em relação à visão inicial

| Visão inicial (`PRODUCT-VISION.md`) | Recomendação da Fase 0 |
|---|---|
| MCP Workshop com "testar ferramentas e recursos em ambiente controlado" | **Fase 2 catalogando apenas**; teste é Fase 4 bloqueada |
| Test & Security Lab no MVP implícito | **Fora do MVP.** Sem sandbox, "testamos" é alegação falsa |
| Skill Creator com assistência de IA | **Não no MVP.** Exige provider, chave, custo e egress |
| Catálogo remoto / comunidade (Fase 5) | **`DEFERRED`** — não é pré-requisito de nada |
| "API local" como opção aberta | **Arquivo vence.** API só com necessidade demonstrada |

---

## 3. Repositórios e branches auditados

**Data da consulta:** 2026-11-15 (UTC). **Método:** clone `--filter=blob:none --no-checkout` + `git fetch` de todas as refs + GitHub API. **Nenhuma execução.**

### 3.1 Lia-Studio

| Branch | HEAD | Arquivos | O que contém |
|---|---|---:|---|
| `main` | `ba70d224359b84a8e114f87b545d83f260f2deb1` | 8 | **Só documentação.** Sem código |
| `arena/01a0f4ab-lia-gamedev` | `4868a18e8cc4d3e35c5a8313adac7e0e7911a1ce` | **179** | **Código real** (`app/lia/` — 38 módulos). 79 commits à frente de `main`. **Não é ancestral de `main`** |
| `arena/studio-docs` | `095dbb04` | 32 | Base documental |
| `arena/04710d54-lia-studio` | `f24fcb16` | 33 | Pesquisa Skills/MCP (Agent 6) |
| `arena/cf17bb1d-lia-studio` | `bf7f7cf8` | 179 | Auditoria de segurança de runtime |
| `arena/327100c7-lia-studio` | `3e86c071` | 179 | Auditoria de integração de engines |
| `arena/3668aa2f-lia-studio` | `f91e5cb8` | 180 | Auditoria de UI/UX |
| `arena/c00122c3-lia-studio` | `394a1273` | 180 | Auditoria de gameplay/QA |

**PR #1** (`arena/01a0f4ab-lia-gamedev → main`) **aberto**.

**Implementado** (na branch, não em `main`): `skills.py` (186 linhas, SHA-256 por conteúdo, teto 64 KB, rejeita symlink, catálogo por prefixo de 8 KB), `tool_registry.py` (preflight puro), `permissions.py` (negação prevalecente em 4 camadas), `runtime_policy.py`, `execution.py` (simulação rotulada), 16 Skills em `.agents/skills/`, 26 arquivos em `tests/` (25 Python), shell desktop WebView2. **38 módulos** em `app/lia/`.

**Não existe:** MCP, adapter de engine, runtime de agente geral, `.exe` validado para distribuição.

### 3.2 Lia-Forge

| Branch | HEAD | Arquivos | O que contém |
|---|---|---:|---|
| `main` | `6bd9a5a7006c7c6ccf5edcb5d577283d61a39949` | 42 | **Só documentação.** `grep -c "^shared/"` = **0** |
| `arena/649f88bd-3dspritesheet` | `b0bb5e74e41c3d149018261b8e494616ef578bd8` | **222** | **Código real** (`shared/`, `electron/`, `src/`). 82 commits à frente. Não é ancestral |
| `arena/6113e868-lia-forge` | `3aabf999` | 43 | Auditoria de agentes/Skills/MCP |
| `arena/624582f5-lia-forge` | `76b1b244` | 47 | Limpeza de histórico |
| `arena/ca5fcc8f-lia-forge` | `6aee1946` | 43 | Auditoria Blender |
| `arena/e209a742-lia-forge` | `84aeca48` | 43 | Lacuna Three.js |
| `arena/ee48e1c5-lia-forge` | `a4fc756e` | 208 | Auditoria de UI |

**Implementado:** `capabilities/registry.mjs` (estados `implemented/partial/proposed/planned`, `null` = não medido), `hub/provider-hub.mjs` (`ready/unknown/blocked/missing`), `adapters/sdk.mjs` (15 campos), `engine/*` (DAG, gates, autorização), `fs/path-containment.mjs`, **servidor MCP real** (`scripts/spriteforge-mcp.mjs`), 47 arquivos em `tests/` (41 `*smoke*`) encadeados no script `npm test`.

**Documentado como `PLANNED`/`PROPOSED`:** `SKILLS-KNOWLEDGE-ENGINE.md` (manifesto de skill com `source`/`license`/`trust`), `CAPABILITY-BOUNDARIES-AND-ROADMAP.md`, `STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md`.

### 3.3 Lia-Project (Waifu)

| Branch | HEAD | Arquivos | Natureza |
|---|---|---:|---|
| `main` | `9c7ac183fd54b8eae0425038190a2c56ec237ff8` | 5.756 | 349 commits |
| `arena/01a10290-lia-project` | `0bf06292` | **6.189** | 203 commits à frente; não é ancestral |
| `arena/826a33f1-lia-project` | `16c97fd4` | 14 | Pesquisa de modelos/providers |
| `agents/docs` | `7913c62a` | 8 | Snapshot documental |
| `codex/lia-multi-provider-voice` | `fd0451d7` | 6.190 | Arquitetura de voz |
| `docs/especificacao-geral-produto-lia` | `b2745f71` | 5.840 | Especificação geral |
| `arena/18f50ae7` | `4acd20e6` | 6.275 | Beta + QA de áudio |
| `arena/250b337a` | `dd8dc0ca` | 6.220 | Fase 1 |
| `arena/4ec8f22b` | `2eabc52b` | 6.190 | Build/lint |
| `arena/c6b02f64` | `0093de09` | 6.198 | Segurança do beta |
| `qa/windows-benchmarks` | `91b8995a` | 20 | Benchmarks Windows |

**Achado de maior valor:** `docs/research/lia-capability-catalog/` em `arena/01a10290` — `03-ESQUEMA-E-DADOS.md` (510 linhas) separa **8 camadas** (Capability/Model/Weights/Runtime/Provider/Adapter/Configuration/Routing) com dono por camada, e define **7 estados de ciclo de vida**.

### 3.4 Lia-AgentHub

`main` @ `34a27f48` — 1 commit, 7 arquivos, sem código. **O `KIT-PROJETO-NOVO.zip` foi lido integralmente** (23 arquivos, 188 KB), confirmado presente.

---

## 4. Integrações avaliadas

| Candidata | Tipo | Licença | Windows | Decisão | Destino |
|---|---|---|---|---|---|
| **Agent Skills** (padrão) | formato | Apache-2.0 / CC-BY-4.0 | N/A | **INTEGRATE** | SHARED |
| **Obsidian** | app | gratuito pessoal / comercial pago `RESEARCH` | Sim | **REFERENCE** | OTHER |
| **MCPVault** | MCP server | **MIT** | Sim (Node ≥22.12) | **REFERENCE** | REFERENCE |
| **Graphify** | skill + CLI | **Apache-2.0** + NOTICE | Sim (Py 3.10+) | **STUDY → REFERENCE** | REFERENCE |
| **ai-memory** | MCP + CLI + serviço | **MIT** | **WSL2 sim / nativo experimental** | **STUDY** | STUDIO + catálogo |
| **uv** | CLI/gerenciador | **Apache-2.0** | Sim | **INTEGRATE** (infra) | HUB |
| **CanIRunAI** | serviço web | não confirmada | N/A | **REFERENCE** | REFERENCE |

### 4.1 Duas ressalvas de pesquisa registradas

1. **`canirunai.kc1t.com` não foi alcançável e não aparece em busca.** O que existe é `canirun.ai` (e um deploy `canirunai-five.vercel.app`). **Não tratei os dois como o mesmo produto** — pergunta em aberto para o usuário.
2. **HTTP direto para sites de terceiros foi bloqueado neste sandbox** (verificado: `agentskills.io`, `obsidian.md`, `modelcontextprotocol.io`, `canirun.ai` retornaram código 000). Usei GitHub API e extração de busca. A única afirmação que depende de fonte não lida é o **licenciamento do Obsidian**, marcada `RESEARCH (não verificada)`.

### 4.2 Nenhuma das quatro ferramentas do briefing vira dependência

Isso não é conservadorismo — é a leitura de que **o Hub resolve um problema que nenhuma delas resolve**: identidade, proveniência, licença, versionamento e empacotamento de capacidades.

**Três padrões foram aproveitados sem custo de licença:**
- Contenção de caminho em Windows (MCPVault, `pathfilter.ts` — inclusive correção documentada de bug de profundidade e canonicalização de pontos/espaços finais).
- Proveniência dentro do artefato (Graphify: `graph.schema_version` + `graph.graphify_version`).
- Wiki Markdown como fonte de verdade com índice derivado reconstruível (ai-memory).

---

## 5. Recomendação de plataforma e stack

| Dimensão | Recomendação |
|---|---|
| **Plataforma** | Aplicativo **desktop Windows**, instalador por usuário, sem admin |
| **Núcleo** | **Python 3.9+ biblioteca padrão apenas** (domínio puro, sem I/O, sem framework, sem rede) |
| **Interface** | **Web local** (HTML/CSS/JS) servida pelo próprio processo, em janela **WebView2** |
| **Empacotamento** | **PyInstaller**; instalação em `%LOCALAPPDATA%\Programs\Lia\AgentHub` |
| **Distribuição** | Fonte (`run.py`) e `.exe` com **comportamento e pastas idênticos** |
| **Sistemas** | **Windows obrigatório**; **Linux secundário**; macOS não no MVP; mobile não |

### 5.1 Por que não Electron

Viável e **não recomendado**: o produto é um editor de texto e arquivos. Electron adiciona Node + npm + electron-builder + download de runtime a um release que precisa de um runtime só. O Project documenta internamente que o segundo Electron completo do Stage é problema estrutural — evidência de que o custo é real e já foi pago uma vez.

### 5.2 Por que não web/mobile

**Rejeitado pela natureza do produto, não por incapacidade:** o Hub depende de sistema de arquivos real e de pastas que o usuário copia e leva. Sem isso, a regra nº 3 da marca ("o trabalho dele é dele") não tem como ser cumprida sem inventar exportação compensatória.

### 5.3 Divisão em três entregas

`F1a` domínio + CLI → `F1b` interface web → `F1c` `.exe`. Isso permite valor antes de resolver empacotamento e permite que o Dev valide no Windows em etapas.

---

## 6. Arquitetura recomendada

### 6.1 Fronteira

```
LIA AGENT HUB                        HOSTS (Studio, Forge, Claude Code, …)
Plano A: autoria, curadoria,         Plano B: consumo, permissões, execução
validação, versionamento,
empacotamento, distribuição
                                     dono de: sessão, cofre, MCP, permissão
dono de: identidade, proveniência,   dono de: runtime, orquestração
licença, confiança, formato,
validação estrutural
                                     ↑
        └──────── arquivo em disco ──┘
             (única integração)
```

### 6.2 Cinco camadas com regra de dependência

| Camada | Conteúdo | Regra |
|---|---|---|
| **L5** Interface | a decidir (`D-14`) | chama L4 |
| **L4** Casos de uso | importar, criar, validar, versionar, empacotar, exportar | chama L3 + L2 |
| **L3** **Domínio** | Capability, Provenance, License, Trust, Validation, Package | **biblioteca padrão apenas. Sem I/O, sem framework, sem rede, sem SO** |
| **L2** Adapters | filesystem, git, zip, sha256, parser Markdown/frontmatter, license detection | única camada com I/O |
| **L1** Armazenamento | biblioteca local, índice derivado | arquivos |

**Proibido no núcleo:** execução, cliente MCP, rede.

### 6.3 Modelo de dados — o que o Hub acrescenta

Adota os vocabulários existentes (Forge `capabilityId`/`status`/`requirements`/trust; Project 8 camadas e ciclo de vida; Agent Skills frontmatter). **Acrescenta apenas:**

- `source {upstream, commit, author, contentHash}` **persistido**
- `license {code, content, weights, reviewedAt}` **por camada**
- `provenanceChain[]`
- `integrity` do pacote (`treeHash`)
- `egress {destinations, carriesUserData, consentRequired}`
- `secrets {envVars[]}` — **apenas nomes**
- `compatibility {hosts, produces, consumes}`
- Formato `.lia-capability`

**Nenhum desses campos tem lugar para uma credencial.**

### 6.4 Escala de confiança

`unreviewed` → `user-provided` → `reviewed-external` → `first-party`.

**Só humano promove para `reviewed-external`**, com autor + data + método + achados. Scanner verde produz `evidence`, nunca `trust`. Nunca promove por tempo, popularidade ou ausência de incidente.

---

## 7. MVPs recomendados

### 7.1 O teste

Uma máquina Windows limpa, **sem internet, sem conta, sem Python**: importar uma `SKILL.md`, ver o relatório honesto, revisar, empacotar, exportar, copiar para `.agents/skills/` — e o Studio (ou Claude Code) usar **sem saber que o Hub existiu**.

### 7.2 Escopo (8 capacidades)

| # | Capacidade | Lacuna |
|---|---|---|
| M1 | Biblioteca local em arquivos | L-01 |
| M2 | Importar + inspecionar com relatório honesto | L-01, L-02, L-06 |
| M3 | Validador estrutural Agent Skills | L-02 |
| M4 | Contenção de caminho (C1–C12) | L-02 |
| M5 | Proveniência + licença por camada | L-01, L-04 |
| M6 | Versionamento + diff entre versões | L-07 |
| M7 | Empacotar/exportar `.lia-capability` | L-03 |
| M8 | Catálogo `index.json` que o host lê | L-05 |

**Opcionais com folga:** criar a partir de template; coleções; declarar diretório de conhecimento.

### 7.3 Fora do MVP com motivo

| Excluído | Motivo técnico |
|---|---|
| Executar capacidade | Sem sandbox comprovado em Windows |
| Conectar MCP | É do host |
| Catálogo remoto | Backend, moderação, custo, `D-12` |
| Busca semântica | Exige modelo + rede |
| Assistência de IA | Provider, chave, custo, egress |
| Import por URL/git | Rede + consentimento |
| Mobile | Sem sistema de arquivos real |
| API local | Arquivo resolve |

### 7.4 Fases

| Fase | Conteúdo | Gate |
|---|---|---|
| 0 | Documentação | **revisão humana** |
| 1 | MVP (M1–M8), F1a/F1b/F1c | execução real no Windows pelo Dev |
| 2 | MCP Workshop (catálogo só) | revisão de que "catalogar ≠ testar" |
| 3 | Distribuição + guias de integração | um host real consumiu o índice |
| **4** | **Test Lab** | **⛔ `D-05` + `D-18` + modelo de ameaças + prova de não-resíduo** |
| 5 | SDK, catálogo remoto, comunidade | `D-08`, `D-12`, `D-16` |

---

## 8. Decisões que ainda precisam do usuário

### 8.1 As quatro que bloqueiam a Fase 1

| ID | Questão | Recomendação Agent 0 |
|---|---|---|
| **D-13** | Escopo do MVP | M1–M8 (escopo B) |
| **D-14** | Stack e plataforma | Python stdlib + WebView2 + PyInstaller, Windows |
| **D-03** | Formato canônico | Agent Skills + manifesto `.lia/` |
| **D-06** | Armazenamento | arquivos + índice derivado, `Lia\AgentHub\` |

### 8.2 As duas que bloqueiam a Fase 4

**D-05** (isolamento reproduzível) e **D-18** (risco aceitável ao testar código de terceiro) — ambas `OPEN`, e recomendo **sessão de pesquisa dedicada** antes de qualquer compromisso.

### 8.3 Demais abertas

- **D-01** nome final (recomendo manter; resolver ambiguidade na descrição).
- **D-16** licença e política de publicação — **sem recomendação**; é decisão do responsável.
- **D-12** catálogo remoto — `DEFERRED`.

### 8.4 Registro completo

24 decisões em `docs/DECISION-REGISTER.md`: **4 `OPEN`**, **19 `RECOMMENDED`**, **1 `DEFERRED`**, **0 `APPROVED`**.

---

## 9. Limitações encontradas

Registradas para que nenhuma sessão futura as trate como resolvidas:

| # | Limitação | Impacto | Contornável? |
|---|---|---|---|
| L1 | **HTTP direto para sites de terceiros bloqueado no sandbox** | Não li `obsidian.md/license`, `docs.astral.sh/uv`, `docs.graphify.com`, `modelcontextprotocol.io` diretamente. Usei GitHub API (fonte primária dos projetos) e extração de busca | Parcial — o licenciamento do Obsidian precisa de reverificação humana |
| L2 | **`canirunai.kc1t.com` não alcançável e ausente da busca** | Não sei se o briefing refere-se a `canirun.ai` ou a outro serviço | **Não** — pergunta ao usuário |
| L3 | **Nenhum teste foi executado** em nenhum repositório | Suítes existem (Studio: 30 arquivos; Forge: 45); resultado é `UNKNOWN` | Sim, com autorização |
| L4 | **Nenhuma validação Windows observada diretamente** | Os relatórios `ALPHA-*-WINDOWS-*.txt` e `DESKTOP-WINDOWS-*` são `EXECUTED` segundo eles mesmos, não re-verificados | Sim, pelo Dev |
| L5 | **Lia-Project tem 6.189 arquivos / ~366 MB na branch de desenvolvimento** | Inspeção dirigida, não exaustiva. Stage, voz e áudio não auditados por não tocarem o escopo do Hub | Aceitável para esta fase |
| L6 | **Nenhuma pesquisa de SBOM nem de assinatura de pacote** | `D-11` fica com recomendação parcial; assinatura é Fase 3+ | Sim, sessão dedicada |
| L7 | **Isolamento/sandbox em Windows não pesquisado a fundo** | `D-05` e `D-18` permanecem `OPEN` sem recomendação técnica forte | Sim, sessão dedicada — **necessária** |
| L8 | **Números de incidentes de segurança são `RESEARCH` herdado** (Snyk ToxicSkills, Liu et al.) | Citados do relatório do Agent 6 no Studio, não verificados nas fontes primárias | Parcial |
| L9 | **Não houve subagentes** | Toda a investigação foi feita pela sessão principal, sequencialmente | Superado — o trabalho foi concluído |
| L10 | **PR #1 do Studio está aberto e não foi revisado** | Não sei se o código do Studio será integrado nem quando | Não é bloqueio do Hub |
| L11 | **Este repositório não tem `LICENSE` nem `THIRD_PARTY_NOTICES.md`** | O kit exige ambos desde o primeiro commit (`GUIA-APP-NOVO.md` §2.1, §2.5). O endpoint de licença do GitHub retorna 404 nos quatro repositórios Lia, porque o arquivo não está na branch padrão | Sim — **criar quando `D-16` for decidida**; a Fase 1 não deve começar sem eles |

---

## 10. Confirmação de ausência de implementação

Declaro explicitamente, conforme as restrições da §13 do mandato:

| Restrição | Cumprida? |
|---|---|
| Não implementar código do produto | **Sim** — apenas Markdown |
| Não instalar dependências | **Sim** |
| Não executar ferramentas externas | **Sim** — nenhum MCP, CLI, Skill ou servidor executado |
| Não fazer migrações | **Sim** |
| Não criar builds ou instaladores | **Sim** |
| Não alterar Lia Studio | **Sim** — clone somente-leitura em `/tmp`, fora do workspace |
| Não alterar Lia Forge | **Sim** |
| Não alterar Lia Project | **Sim** |
| Não integrar branches de outros agentes | **Sim** |
| Não criar runtime de agentes | **Sim** |
| Não publicar capacidades | **Sim** |
| Não alterar configurações do usuário | **Sim** |
| Não fazer merge na `main` | **Sim** |
| Não mudar a branch padrão do GitHub | **Sim** |
| Não decidir unilateralmente questões do usuário | **Sim** — 24 decisões registradas, **0 aprovadas** |

**Verificação objetiva:** todos os arquivos adicionados são `.md`. Não há `package.json`, `.py`, `.js`, `.ts`, `.json` de configuração, lockfile ou binário. Os clones de auditoria vivem em `/tmp` e não entram no snapshot do repositório.

---

## 11. Documentos desta entrega

| Documento | Conteúdo | Situação |
|---|---|---|
| `docs/research/REPOSITORY-AND-BRANCH-AUDIT.md` | Auditoria dos 4 repositórios, 30 branches, módulos, estados, lacunas L-01…L-08, sobreposições | **Novo** |
| `docs/research/INTEGRATION-CANDIDATES.md` | 7 candidatas externas com licença, Windows, egress, riscos e decisão | **Novo** |
| `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` | T1–T5, fronteiras, vocabulário, camadas, modelo de dados, contratos, formato de pacote, alternativas descartadas | **Novo** |
| `docs/architecture/SECURITY-AND-TRUST-MODEL.md` | 10 classes de ameaça, escala de confiança, contenção C1–C12, catálogo honesto de detecção, 7 riscos residuais | **Novo** |
| `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` | Classes de dado, layout `Lia\`, escrita atômica, backup, portabilidade entre SO, migração, desinstalação | **Novo** |
| `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | 8 critérios ponderados, 5 opções, recomendação, riscos S-01…S-08, matriz de SO | **Novo** |
| `docs/product/MVP-AND-ROADMAP.md` | Teste do MVP, M1–M8, critérios de aceite, 6 fases, 3 escopos comparados, riscos R-01…R-07 | **Novo** |
| `docs/DECISION-REGISTER.md` | 24 decisões com estado, alternativas, evidência, recomendação, impacto de adiar, exigência humana | **Atualizado** (perguntas originais preservadas) |
| `docs/PHASE-0-FINAL-REPORT.md` | Este relatório | **Novo** |
| `README.md` | Estado da pesquisa, links, fronteiras | **Atualizado** |

**Mapeamento com os entregáveis do mandato (§11) e do brief (`PHASE-0-ARENA-BRIEF.md`):**

| Pedido | Entregue em |
|---|---|
| `REPOSITORY-AND-BRANCH-AUDIT.md` | documento próprio |
| `INTEGRATION-CANDIDATES.md` | documento próprio |
| `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` | documento próprio |
| `SECURITY-AND-TRUST-MODEL.md` | documento próprio |
| `DATA-STORAGE-AND-PORTABILITY.md` | documento próprio |
| `MVP-AND-ROADMAP.md` | documento próprio |
| `PLATFORM-AND-TECHNOLOGY-DECISION.md` | documento próprio |
| `DECISION-REGISTER.md` | atualizado |
| `PHASE-0-FINAL-REPORT.md` | este documento |
| `ECOSYSTEM-AUDIT.md` (brief) | `REPOSITORY-AND-BRANCH-AUDIT.md` |
| `EXISTING-CAPABILITIES-MATRIX.md` (brief) | `REPOSITORY-AND-BRANCH-AUDIT.md` §1.2, §2.2, §3.2, §5 |
| `EXTERNAL-ECOSYSTEM-RESEARCH.md` (brief) | `INTEGRATION-CANDIDATES.md` |
| `PRODUCT-BOUNDARIES.md`, `CAPABILITY-DATA-MODEL.md`, `DISTRIBUTION-CONTRACTS.md` (brief) | `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §2, §6, §7–§8 |

Consolidei documentos do brief em documentos mais densos para evitar fragmentação — cada um declara no cabeçalho o que cobre. Não criei arquivo vazio.

---

## 12. Fechamento e próxima sequência

### 12.1 Commits desta entrega

Os commits são organizados por assunto nesta branch. O hash final é o `HEAD` de `arena/a92004be-lia-agenthub` após esta entrega; `git log` é a fonte de verdade (um relatório que grava o próprio hash do commit que o contém nasceria obsoleto).

### 12.2 O que a revisão humana precisa decidir

1. **Aprovar, ajustar ou rejeitar a independência do produto** (recomendo: aprovar, com o escopo de registro).
2. **Aprovar o escopo do MVP** (`D-13`) — M1–M8, com Test Lab fora.
3. **Aprovar as fronteiras** entre Hub, Studio e Forge.
4. **Aprovar arquitetura e contrato de distribuição** (arquivo, `.lia-capability`, `index.json`).
5. **Aprovar o plano de segurança**, inclusive os 7 riscos residuais declarados.
6. **Autorizar — ou não — a Fase 1.**

### 12.3 Próxima sequência recomendada de agentes

| Agente | Missão | Pré-requisito |
|---|---|---|
| **Agent 1 — Especificação de domínio** | Detalhar L3: tipos, validações, mensagens de erro, schema `capability.json` final, casos de teste negativos | `D-03`, `D-06`, `D-13` aprovadas |
| **Agent 2 — Especificação de formato e empacotamento** | `.lia-capability`, `manifest.json`, `treeHash`, regras de portabilidade entre SO, `NOTICE` | `D-03`, `D-11`, `D-21` |
| **Agent 3 — Pesquisa de isolamento Windows** | Responder `D-05`/`D-18` com prova real: contêiner, VM, usuário restrito, não-resíduo. **Sem esta, a Fase 4 não existe** | independente — pode começar já |
| **Agent 4 — Especificação de UI** | Telas: biblioteca, import, revisão, diff, export. Aplicar `GLOSSARIO.md` e as regras de interface do kit | `D-14` aprovada |
| **Agent 5 — Implementação F1a** (Codex) | Domínio + CLI, após aprovação | Fase 1 autorizada |
| **Agent 6 — Integração com hosts** | Guias de leitura de `index.json` para Studio e Forge — **documentação, sem alterar os produtos** | Fase 3 |

**Recomendação explícita:** o **Agent 3 pode e deve começar antes** das aprovações, porque `D-05`/`D-18` são as duas únicas decisões técnicas sem base para recomendar, e elas determinam se o produto terá Test Lab algum dia.

### 12.4 O que **não** fazer a seguir

- **Não implementar** antes da aprovação de `D-13` e `D-14`.
- **Não** colocar Test Lab no MVP para "melhorar o produto".
- **Não** criar um segundo editor de Skills concorrendo com o do Studio.
- **Não** inventar vocabulário de capacidade — adotar o do Forge e do Project.
- **Não** transformar recomendação deste relatório em decisão aprovada.

---

## 13. Declaração final

A Fase 0 está concluída como **trabalho documental**. O produto **Lia Agent Hub é viável e justificável**, com um escopo estreito e verificável: registrar, validar estrutura, registrar decisão humana, versionar e empacotar capacidades.

O que torna essa conclusão defensável não é a quantidade de documentos — é que **cada recomendação tem evidência rastreável em branch e commit**, e que **cada afirmação que não pude verificar está marcada como tal**. As dez limitações da §9 são parte da entrega, não uma nota de rodapé.

A Fase 1 não foi iniciada. Aguardo revisão e aprovação humana.
