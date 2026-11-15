# Fase 0 — mandato de pesquisa, auditoria e especificação

**Estado:** autorizada como trabalho documental/investigativo.  
**Implementação de produto:** não autorizada.  
**Repositório de trabalho:** `BloomRX/Lia-AgentHub`.  
**Base inicial da sessão:** `main`; a sessão Arena cria sua própria branch de trabalho.

## Objetivo

Determinar, com evidências, se o Lia Agent Hub deve existir como aplicação independente e qual é o menor produto útil que administra capacidades para agentes sem duplicar responsabilidades de Lia Studio e Lia Forge.

O documento [PRODUCT-VISION.md](PRODUCT-VISION.md) é o briefing. É uma direção proposta, não uma especificação já aprovada.

## Missão do Arena

### 1. Auditar o ecossistema Lia

Auditar repositórios, branches, PRs e commits relevantes. Não limitar a inspeção à branch `main`; também não tratar uma branch de desenvolvimento como código integrado.

**Lia Studio**
- Referência inicial: `BloomRX/Lia-Studio`, branch `arena/01a0f4ab-lia-gamedev`.
- Comparar, quando relevantes, as branches `arena/3668aa2f-lia-studio`, `arena/327100c7-lia-studio`, `arena/cf17bb1d-lia-studio` e `arena/c00122c3-lia-studio`.
- Inspecionar especialmente: `docs/AI-AGENTS-ARCHITECTURE.md`, `docs/AI-CONTEXT-AND-PERMISSIONS.md`, `docs/AI-EXECUTION-ORCHESTRATION.md`, `docs/AI-MULTI-AGENT-CONTRACT.md`, `docs/AI-INTEGRATION-CATALOG.md`, `app/lia/skills.py`, `app/lia/tool_registry.py`, `app/lia/permissions.py`, `app/lia/providers.py` e os testes correspondentes.
- Diferenciar contratos documentados, código real, simulações, integrações conectadas e capacidades ainda não observadas.

**Lia Project**
- Referência inicial: `BloomRX/Lia-Project`, branch `arena/01a10290-lia-project`.
- Inspecionar `docs/project/AGENT-SKILLS.md`, `docs/project/AGENT-ORCHESTRATION.md`, `docs/architecture/AGENT-SKILLS-AUDIT-LIA.md`, `docs/architecture/LIA-AGENT-CONSUMPTION-AUDIT.md` e `docs/research/lia-capability-catalog/`.
- Comparar branches relevantes, inclusive `agents/docs`, `arena/826a33f1-lia-project` e `codex/lia-multi-provider-voice`, sem presumir que seu conteúdo foi integrado.

**Lia Forge**
- Referência de implementação: `BloomRX/Lia-Forge`, branch `arena/649f88bd-3dspritesheet`.
- Referência de pesquisa T14: `arena/6113e868-lia-forge`.
- Inspecionar especialmente `docs/TOOL-PROVIDER-HUB.md`, `docs/WORKFLOW-ENGINE.md`, `docs/INTELLIGENT-ORCHESTRATOR.md`, `docs/SKILLS-KNOWLEDGE-ENGINE.md`, `docs/AGENT-SKILLS-MCP-IMPLEMENTATION-ASSESSMENT.md`, `docs/T14-AGENT-ORCHESTRATION-ARCHITECTURE.md` e o código de `shared/hub/`, `shared/adapters/`, `shared/capabilities/` e `shared/orchestrator/`.
- Comparar com `main` e PRs. A presença de implementação em `arena/649f88bd-3dspritesheet` não significa que esteja integrada em `main`.

A lista acima é uma linha de partida; verificar se branches e caminhos ainda existem e localizar a autoridade documental atual antes de tirar conclusões.

### 2. Mapear sobreposições e lacunas

Para cada capacidade, indicar:
- produto responsável;
- código e documentação que já existem;
- branch/commit onde existem;
- estado: IMPLEMENTED, EXECUTED, VALIDATED, PROPOSED, PLANNED, RESEARCH ou UNKNOWN;
- o que pode ser compartilhado sem transferir execução ao Hub;
- o que não deve ser duplicado;
- lacunas confirmadas e evidências necessárias.

### 3. Pesquisa externa atualizada

Pesquisar documentação oficial e soluções atuais para:
- Agent Skills e formatos portáteis;
- Model Context Protocol (MCP), SDKs, inspeção e testes;
- catálogos, registries, packaging e distribuição de capacidades;
- assinatura, integridade, proveniência, SBOM e cadeia de suprimentos;
- sandboxes e testes isolados em Windows e Linux;
- compatibilidade entre Codex, Claude Code, OpenCode e outros hosts/agentes;
- ferramentas de criação, avaliação e manutenção de Skills/MCPs.

Referências iniciais do briefing: https://agentskills.io/ , https://modelcontextprotocol.io/ e https://skills.sh/ . Verificar documentação, repositórios, licença, atividade, limitações e estado atual. Não recomendar dependência por popularidade.

### 4. Definir produto, arquitetura e MVP

Apresentar alternativas, vantagens, desvantagens e recomendação para:
- usuários e casos de uso além do ecossistema Lia;
- escopo inicial de tipos de capacidades;
- diferença entre biblioteca transversal, catálogo e aplicação independente;
- modelo de dados/manifestos, dependências e compatibilidade;
- formatos canônicos e interoperabilidade;
- armazenamento local, backup, versionamento e exportação;
- testes estáticos versus execução em sandbox;
- confiança, permissões, licença e proveniência;
- mecanismo de distribuição/consumo pelos hosts;
- necessidade e momento de SDK/CLI ou API local;
- tecnologia da aplicação, considerando Windows como alvo relevante sem copiar automaticamente a stack de outros produtos;
- MVP mínimo que prove valor sem reconstruir runtime/orquestradores.

Não escolher silenciosamente uma opção quando a decisão for de produto ou risco humano.

## Entregáveis esperados

Produzir documentação Markdown nesta branch do Lia-AgentHub:

1. `docs/research/ECOSYSTEM-AUDIT.md` — auditoria factual dos três projetos e branches.
2. `docs/research/EXISTING-CAPABILITIES-MATRIX.md` — capacidades existentes, estados, donos e lacunas.
3. `docs/research/EXTERNAL-ECOSYSTEM-RESEARCH.md` — soluções e padrões, com fontes primárias e classificação.
4. `docs/architecture/PRODUCT-BOUNDARIES.md` — fronteiras entre Hub, Studio, Forge e hosts externos.
5. `docs/architecture/CAPABILITY-DATA-MODEL.md` — proposta de tipos, manifestos, dependências, proveniência e ciclo de vida.
6. `docs/architecture/SECURITY-AND-TRUST-MODEL.md` — ameaças, níveis de confiança, inspeção, sandbox, consentimentos e limites.
7. `docs/architecture/DISTRIBUTION-CONTRACTS.md` — proposta de exportação/consumo, sem implementação.
8. `docs/product/MVP-AND-ROADMAP.md` — opções e recomendação de MVP, fases, critérios de aceite e itens adiados.
9. `docs/DECISION-REGISTER.md` — atualizar cada questão com evidência, opções, recomendação e decisão humana pendente/aprovada.

Adicionar um resumo executivo com recomendação: avançar como app independente, reduzir para biblioteca/CLI primeiro ou outra alternativa justificada.

## Critérios de qualidade

- Citar URL, documento, branch e commit exatos.
- Separar fato, inferência e recomendação.
- Marcar o que não foi testado e o que depende de ambiente Windows.
- Identificar decisões que exigem o responsável do produto; não tomar essas decisões em seu nome.
- Evitar reescrever documentos existentes sem motivo; referenciar e resumir.
- Não copiar código nem trazer dependências ao Lia-AgentHub nesta fase.

## Fora do escopo

Não criar app, UI, scaffolding, instalador, CLI executável, banco de produção ou serviço local. Não instalar nem executar soluções externas. Não alterar Lia Studio, Lia Project ou Lia Forge. Não integrar Skills/MCPs. Não abrir PR de implementação.

## Fechamento da Fase 0

A Fase 0 termina quando os entregáveis estiverem commitados na branch de trabalho e houver uma revisão consolidada que permita ao usuário aprovar, corrigir ou rejeitar:
- a independência do produto;
- o escopo do MVP;
- as fronteiras entre produtos;
- a arquitetura e o modelo de distribuição;
- o plano de segurança e validação;
- a autorização para a próxima fase.

**Não iniciar Fase 1 automaticamente ao terminar a pesquisa.**
