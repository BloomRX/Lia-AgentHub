# Pesquisa Fase 0 — índice e controle do agente de pesquisa

**Repositório:** `BloomRX/Lia-AgentHub`
**Papel desta linha de trabalho:** agente de pesquisa (Fase 0 — pesquisa, auditoria e especificação).
**Estado:** documentação e investigação. **Implementação de produto: não autorizada.**
**Última atualização:** 2026-11-15

## Branch de trabalho

| Item | Valor |
|---|---|
| Branch ativa | `arena/db625478-lia-agenthub` |
| Criada a partir de | `main` @ `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` ("Kit Marca Lia") |
| Publicação | push para `origin` no início da sessão, para tornar o trabalho visível e revisável |
| Commits em `main` | nenhum (regra do fluxo de branches) |
| Merge / force-push | não realizados; dependem de autorização humana |

Esta branch segue `docs/BRANCH-AND-RELEASE-FLOW.md`: `main` permanece linha documental estável; o trabalho da sessão ocorre aqui.

## Documentos-base já lidos nesta branch

1. `README.md` — escopo, fronteira Hub/Studio/Forge, princípios.
2. `AGENTS.md` — regras de trabalho, restrições da Fase 0, classificação de evidência.
3. `docs/PRODUCT-VISION.md` — briefing e direção proposta (não é arquitetura aprovada).
4. `docs/PHASE-0-ARENA-BRIEF.md` — mandato, alvos de auditoria, entregáveis.
5. `docs/DECISION-REGISTER.md` — decisões D-01 a D-20, todas `OPEN`.
6. `docs/BRANCH-AND-RELEASE-FLOW.md` — fluxo de branches e releases.
7. `docs/KIT-PROJETO-NOVO.zip` — presente na branch; conteúdo **não inspecionado** nesta rodada (item pendente de decisão do responsável, ver abaixo).

## Entregáveis da Fase 0 — status

Status permitidos: `NOT STARTED`, `IN PROGRESS`, `DRAFT`, `REVIEW`, `DONE`. Nada aqui foi iniciado além deste índice.

| # | Arquivo | Status |
|---|---|---|
| 1 | `docs/research/ECOSYSTEM-AUDIT.md` | NOT STARTED |
| 2 | `docs/research/EXISTING-CAPABILITIES-MATRIX.md` | NOT STARTED |
| 3 | `docs/research/EXTERNAL-ECOSYSTEM-RESEARCH.md` | NOT STARTED |
| 4 | `docs/architecture/PRODUCT-BOUNDARIES.md` | NOT STARTED |
| 5 | `docs/architecture/CAPABILITY-DATA-MODEL.md` | NOT STARTED |
| 6 | `docs/architecture/SECURITY-AND-TRUST-MODEL.md` | NOT STARTED |
| 7 | `docs/architecture/DISTRIBUTION-CONTRACTS.md` | NOT STARTED |
| 8 | `docs/product/MVP-AND-ROADMAP.md` | NOT STARTED |
| 9 | `docs/DECISION-REGISTER.md` (atualização) | NOT STARTED |
| 10 | Resumo executivo com recomendação | NOT STARTED |

## Convenções de evidência (obrigatórias em todo relatório)

- **IMPLEMENTED** — código identificado em commit/branch específicos.
- **EXECUTED** — execução comprovada, informando ambiente, ferramenta e entrada.
- **VALIDATED** — execução com ferramenta/entrada reais e evidência revisável.
- **PROPOSED / PLANNED** — proposta ou roadmap, ainda não entregue.
- **RESEARCH** — informação obtida em fontes, sem teste local.
- **UNKNOWN** — não foi possível confirmar.

Regra adicional: presença em branch não integrada **não** é presença em `main`. Toda descoberta recebe classificação de destino (Hub, Studio, Forge, compartilhada, outro domínio, referência, não recomendada).

## Limitações de verificação do ambiente atual

Registradas para não superestimar nenhuma conclusão futura:

- Acesso de rede direto do sandbox limitado a `github.com`, `api.github.com`, `codeload.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`.
- Fontes externas de briefing (`agentskills.io`, `modelcontextprotocol.io`, `skills.sh`) precisam ser alcançadas pelos canais de pesquisa disponíveis; se o texto primário não for acessível, o relatório deve declarar a limitação e a data de consulta.
- Nenhum teste foi executado nesta rodada. Nenhuma ferramenta de terceiro foi instalada, baixada ou executada.
- Ambiente Windows não está disponível aqui; requisitos Windows serão tratados como RESEARCH/PROPOSED, nunca como VALIDATED.

## Registro de sessões

### Sessão 1 — 2026-11-15

- **Ação:** leitura integral dos documentos-base; criação deste índice; publicação da branch `arena/db625478-lia-agenthub` em `origin`.
- **Mudanças:** apenas `docs/research/README.md` (novo). Nenhum código, nenhum scaffolding, nenhuma dependência.
- **Testes:** não executados (Fase 0 é documental).
- **Pendências humanas:** confirmação de que esta é a branch ativa de desenvolvimento; definição da ordem de prioridade dos entregáveis; decisão sobre inspeção do `docs/KIT-PROJETO-NOVO.zip`.

## Próximos passos propostos (aguardando priorização)

1. **Auditoria do ecossistema Lia** (`ECOSYSTEM-AUDIT.md`): verificar existência atual das branches citadas no brief em `BloomRX/Lia-Studio`, `BloomRX/Lia-Project` e `BloomRX/Lia-Forge`; registrar commit, data, documentos reais encontrados e estado de cada capacidade.
2. **Matriz de capacidades** (`EXISTING-CAPABILITIES-MATRIX.md`): dono, branch/commit, estado, o que é compartilhável sem transferir execução ao Hub, o que não deve ser duplicado, lacunas.
3. **Pesquisa externa** (`EXTERNAL-ECOSYSTEM-RESEARCH.md`): Agent Skills, MCP, registries/catálogos, assinatura e proveniência, sandboxing Windows/Linux, compatibilidade entre hosts — com fonte primária, URL, versão, data e licença.
4. **Arquitetura e contratos** (itens 4 a 7), **MVP e roadmap** (item 8) e **atualização do registro de decisões** (item 9), sempre separando recomendação do Arena da decisão humana.

Nenhum passo acima inicia implementação. A Fase 0 termina em revisão consolidada; a Fase 1 não começa automaticamente.
