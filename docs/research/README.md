# Pesquisa — Lia Agent Hub: índice e controle do agente de pesquisa

**Repositório:** `BloomRX/Lia-AgentHub`
**Papel desta linha de trabalho:** agente de pesquisa (Fase 0 — pesquisa, auditoria e especificação) + inventário e catalogação de Agent Skills.
**Estado:** documentação e investigação. **Implementação de produto: não autorizada nesta branch.**
**Última atualização:** 2026-11-15

## Branch de trabalho

| Item | Valor |
|---|---|
| Branch ativa | `arena/db625478-lia-agenthub` |
| Criada a partir de | `main` @ `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` ("Kit Marca Lia") |
| Publicação | push em `origin` a cada entrega |
| Commits em `main` | nenhum |
| Merge / force-push / PR | **nenhum** — dependem de autorização humana |

### Branches de referência (somente leitura)

| Branch | O que contém | Uso aqui |
|---|---|---|
| `arena/a92004be-lia-agenthub` (`b4eb85f`; avançou para `704dfd3f` durante a sessão) | Fase 0 documental anterior + MVP da Fase 1 implementado (`src/lia_agenthub/`, 200+ testes, empacotamento Windows) | **referência de contrato**: o modelo de dados, o importador, o índice e o formato de pacote lidos e usados como formato oficial de catalogação. Nada foi mergeado nem alterado |
| `arena/b6febe41-lia-agenthub` | UI/UX (`docs/design/*`) | identificada e **não tocada** |

## Entregáveis desta rodada

| Arquivo | Missão | Estado |
|---|---|---|
| [`LIA-SKILLS-INVENTORY.md`](LIA-SKILLS-INVENTORY.md) | 1 — inventariar os projetos Lia | **DRAFT para revisão** |
| [`THIRD-PARTY-SKILLS-CATALOG.md`](THIRD-PARTY-SKILLS-CATALOG.md) | 2 — pesquisar skills de terceiros · 8 — priorização | **DRAFT para revisão** |
| [`SKILL-LICENSE-AND-PROVENANCE-AUDIT.md`](SKILL-LICENSE-AND-PROVENANCE-AUDIT.md) | 3 — auditoria de licença · 6 — identidade e proveniência | **DRAFT para revisão** |
| [`LIA-SKILLS-ROADMAP.md`](LIA-SKILLS-ROADMAP.md) | 4 — oportunidades `lia-` · 8 — priorização | **DRAFT para revisão** |
| [`SKILL-CATALOG-IMPORT-REPORT.md`](SKILL-CATALOG-IMPORT-REPORT.md) | 5 — catalogar no formato do Hub | **DRAFT para revisão** |
| [`catalog/`](catalog/README.md) | 5 — 48 registros prontos (`schemaVersion 1`) | **gerado, não importado** |
| [`tools/build-catalog-records.py`](tools/build-catalog-records.py) | 5 — reprodutibilidade dos registros | **ferramenta de pesquisa (stdlib)** |

### Entregáveis da Fase 0 do briefing que **ainda não** foram produzidos nesta branch

`docs/research/ECOSYSTEM-AUDIT.md` · `docs/research/EXISTING-CAPABILITIES-MATRIX.md` · `docs/research/EXTERNAL-ECOSYSTEM-RESEARCH.md` · `docs/architecture/PRODUCT-BOUNDARIES.md` · `docs/architecture/CAPABILITY-DATA-MODEL.md` · `docs/architecture/SECURITY-AND-TRUST-MODEL.md` · `docs/architecture/DISTRIBUTION-CONTRACTS.md` · `docs/product/MVP-AND-ROADMAP.md` · atualização de `docs/DECISION-REGISTER.md` · resumo executivo com recomendação.

> Parte desse conteúdo existe na branch de referência (`docs/research/REPOSITORY-AND-BRANCH-AUDIT.md`, `docs/research/INTEGRATION-CANDIDATES.md`, `docs/architecture/*`, `docs/product/*`, `docs/PHASE-0-FINAL-REPORT.md`). Nesta branch ele foi **referenciado, não duplicado**. Decidir se a Fase 0 continua daqui ou a partir da branch de referência é **decisão humana**.

## Números desta rodada

| Métrica | Valor |
|---|---|
| Repositórios Lia inspecionados | 13 (7 com inspeção profunda de árvores/branches) |
| Branches Lia listadas | 35 |
| Pastas de Agent Skills catalogáveis | **48** (Studio 16 · Project 22 · Model-Lab 9 · Forge 1) |
| Skills vendadas do AIRI + skills no ZIP Mr-Mak | 29 + 20 (não catalogadas, justificativa no relatório) |
| Fontes externas verificadas | ~40 (24 por metadados, 12 por conteúdo, 1 por skill) |
| Licenças identificadas na fonte | **MIT**: 12 com texto lido + 15 por metadados da API · **Apache-2.0**: 3 · **CC-BY-NC-ND 4.0**: 1 · **mista em transição MIT→Apache-2.0**: 1 · **AGPL-3.0**: 1 (+1 dual AGPL/comercial por referência à Forge T14) · **ausência de licença**: 11 |
| Registros gerados no formato do Hub | **48** · payload referenciado 1.572.502 bytes |
| Recursos gravados na biblioteca real do Hub | **0** (Hub não executado; razões no relatório §3.1) |
| Recursos aprovados para uso | **0** (decisão humana) |
| Lacunas do modelo de dados documentadas | 9 (E-1…E-9) + 8 propostas aditivas (P-E1…P-E8) |
| Decisões humanas pendentes registradas | 10 (P-1…P-10) |

## Convenções de evidência (obrigatórias)

`IMPLEMENTED` (código em commit/branch) · `EXECUTED` (execução comprovada, com ambiente/ferramenta/entrada) · `VALIDATED` (execução com ferramenta/entrada reais e evidência revisável) · `PROPOSED`/`PLANNED` · `RESEARCH` (fonte, sem teste local) · `UNKNOWN`.

Regra: presença em branch não integrada **não** é presença em `main`. Proposta não é implementação. Smoke test com stub não é validação.

## Limitações de verificação

- Rede direta do sandbox limitada a `github.com`, `api.github.com`, `codeload.github.com`, `registry.npmjs.org`, `files.pythonhosted.org`. **`agentskills.io` foi alcançado por `fetch_page`** (especificação lida na fonte primária); **`skills.sh` não** — as afirmações sobre ele vêm de três fontes secundárias datadas.
- **Nenhum teste foi executado. Nenhuma ferramenta de terceiro foi instalada ou executada. Nenhuma skill, script ou comando de repositório de terceiros foi rodado.**
- Sem ambiente Windows: nada aqui é `VALIDATED` para Windows.
- Repositórios de assets (`3d-create`, `ChibiCreate`, `ComfyUI_Colab`, `SilksongREA`, `animations-free`, `3d-sprite`, `LiaVoiceStudio`) tiveram apenas `main` varrido.

## Registro de sessões

### Sessão 1 — 2026-11-15

1. Leitura integral de `README.md`, `AGENTS.md`, `docs/PRODUCT-VISION.md`, `docs/PHASE-0-ARENA-BRIEF.md`, `docs/DECISION-REGISTER.md`, `docs/BRANCH-AND-RELEASE-FLOW.md`; abertura e publicação da branch.
2. Missão 1: inventário de 13 repositórios Lia (árvores via API; tarball/clone esparso somente leitura), com commits exatos e critério do que é ou não Skill.
3. Missões 2 e 3: verificação de ~40 fontes externas (licença, atividade, contagem real de `SKILL.md`, licenças aninhadas) e auditoria de licença/proveniência, incluindo os 5 terceiros já consumidos pela Lia (commits upstream confirmados) e a licença **ausente** dos próprios repositórios Lia.
4. Missão 5: leitura do contrato implementado do Hub e geração de 48 registros (`capability.json` + `provenance.json`) com `id`, `contentHash` e `treeHash` calculados por ferramenta de pesquisa.
5. Missões 4, 6 e 8: roadmap de 14 oportunidades `lia-` (7 recomendadas para agora), convenções de identidade/proveniência e priorização por 7 critérios.
6. **Mudanças:** apenas documentos e registros em `docs/research/` desta branch. Nenhum código de produto, nenhum scaffolding, nenhuma dependência, nenhuma cópia de payload entre repositórios.

## Próximos passos propostos (aguardando priorização humana)

1. Decidir P-1 (licença dos repositórios Lia) — destrava qualquer redistribuição das 47 skills autorais.
2. Decidir se a Fase 0 continua nesta branch ou a partir da branch de referência (evita duplicar `PRODUCT-BOUNDARIES`, `SECURITY-AND-TRUST-MODEL`, `MVP-AND-ROADMAP`).
3. Autorizar (ou não) o roteiro de importação real das 48 skills e a conferência dos hashes (§5 do relatório).
4. Autorizar (ou não) as evoluções aditivas P-E1…P-E8 no modelo de dados.
5. Escolher as 3 skills da Onda 1 (`lia-license-audit`, `lia-provenance-record`, `lia-skill-validator`) para criação — **criação é Fase 1, exige autorização**.
