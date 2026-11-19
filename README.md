# Lia Agent Hub

**Plataforma independente para criar, descobrir, validar, organizar, versionar, empacotar e distribuir capacidades para agentes de IA.**

> **Estado atual: MVP funcional; expansão do registro central em andamento.**
> M1–M8 do MVP e o intake v1 estão implementados. A última linha de base
> executada antes da expansão registrou **823 testes aprovados e 2 ignorados**.
> Esta branch acrescentou dez casos de regressão para proveniência multi-origem,
> aliases e relações declaradas; eles ainda aguardam execução em CI/ambiente local.
> Permanecem pendentes a medição de rede em Windows, o build do `.exe` em
> ambiente com PyInstaller e a decisão de licença (`D-16`).
>
> Ver [docs/MVP-GUIA.md](docs/MVP-GUIA.md) para instalar e usar,
> [docs/DESENVOLVIMENTO.md](docs/DESENVOLVIMENTO.md) para desenvolver, e
> **[docs/operations/FUNCTIONAL-COMPLETION-REPORT.md](docs/operations/FUNCTIONAL-COMPLETION-REPORT.md)**
> para o relatório de conclusão — o documento que diz, requisito por requisito,
> o que é PASS, o que é PARTIAL e o que continua BLOCKED.

O Lia Agent Hub é um produto de escopo transversal: deve atender Game Development, programação, arte e design, pesquisa, produtividade, automação, mídia, lazer e outros domínios que utilizem agentes compatíveis.

## O que a Fase 0 concluiu

O Hub **é** viável como aplicação independente — com um escopo mais estreito do que a visão inicial sugeria:

> O Hub registra capacidades: dá a elas **identidade, origem, versão, licença, avaliação de risco e forma de pacote**. Ele **não** as executa, não as autoriza, não guarda credenciais e não orquestra nada.

A auditoria encontrou **oito lacunas** que nenhum dos produtos Lia atende hoje — registro de proveniência, pipeline de intake, formato de pacote portátil, análise de licença, contrato de distribuição, detecção de conteúdo malicioso em prosa, versionamento de capacidade e catálogo de MCP. **Nenhuma exige executar código.**

## O que está pronto e o que não está

### Concluído (documentação)

- [x] Auditoria de 4 repositórios, 30 branches e ~40 módulos, com commit exato
- [x] Pesquisa de 7 candidatas externas com licença, egress e decisão
- [x] Fronteiras de produto e arquitetura em 5 camadas
- [x] Modelo de dados de capacidade e formato de pacote `.lia-capability`
- [x] Modelo de segurança com 10 classes de ameaça e 7 riscos residuais declarados
- [x] Armazenamento, portabilidade e backup
- [x] Comparação de plataforma com 8 critérios ponderados
- [x] MVP de 8 capacidades e roadmap em 6 fases
- [x] 27 decisões registradas com recomendação — **0 aprovadas**
- [x] Revisão de consistência (Fase 0.1): piso de Python corrigido, política Unicode por categoria, terminologia de integridade, exportação por destino

### Implementado (MVP)

- [x] Aplicação desktop local com interface web embarcada (7 módulos de domínio,
      6 adaptadores, servidor local com token de sessão)
- [x] Biblioteca com busca e filtros por tipo, confiança e tag
- [x] Importação de arquivo, pasta, `.zip` e `.lia-capability`, com quarentena
      obrigatória e promoção explícita
- [x] Validação estrutural de `SKILL.md` e política Unicode por região
- [x] Procedência, licença (presença ≠ permissão) e risco por regras explícitas
- [x] SHA-256 por arquivo e de árvore; deduplicação por conteúdo
- [x] Exportação `.lia-capability` com verificação de adulteração
- [x] `index.json` portátil, validável, sem segredos
- [x] **Leitor de referência independente** (`docs/examples/independent-reader/`)
      — roda com o Hub desinstalado e prova que o contrato é consumível (IDX-3)
- [x] **CLI de desenvolvimento**: `diagnostico`, `validate`, `pack`, `export`,
      `index`, `verify-package`, com códigos de saída estáveis
- [x] **Diff semântico entre versões**: corpo, `description`, `allowed-tools`
- [x] **Configuração de host para servidor MCP** para colar no cliente —
      cabeçalho entra como nome, nunca valor
- [x] **Controle de rede do WebView2** por argumentos documentados
- [x] **Intake de inventários v1** — leitura somente-leitura, validação
      estrita, dry-run, classificação de duplicatas/conflitos e recibos com
      proveniência; não executa, não instala, não conecta e não aprova licença
      ([docs/operations/INVENTORY-INTAKE.md](docs/operations/INVENTORY-INTAKE.md))
- [x] 823 testes: unit, integração, segurança, persistência, interface e build
- [x] Build configurado para Windows via PyInstaller
- [ ] **Executável Windows gerado e testado** — não validado neste ambiente
      (sem Windows nem WebView2); o script de build roda testes e aborta se
      algum falhar. O spec do PyInstaller é validado estaticamente por teste,
      mas **não foi empacotado**: falta `libpython` compartilhada neste ambiente
- [ ] **Zero egress na janela nativa** — o controle de rede do runtime está
      implementado; a **medição** em Windows continua pendente (`D-09`)
- [ ] **Licença do repositório** — D-16 aberta, aguarda decisão humana
- [ ] **Nenhuma alteração** em Lia Studio, Lia Forge ou Lia Project

## Fronteira dos produtos

| Produto | É dono de | Não faz |
|---|---|---|
| **Lia Agent Hub** | Identidade, proveniência, licença, confiança, validação estrutural, versionamento, empacotamento, distribuição | Executar, autorizar, guardar credencial, orquestrar, produzir asset |
| **Lia Studio** | Sessão, contexto de desenvolvimento, permissões, aprovações, execução de agentes, QA de jogo | Ser o dono exclusivo da biblioteca de capacidades |
| **Lia Forge** | Providers, modelos, pesos, workflows, pipelines, validação técnica de assets | Catalogar capacidades genéricas |

**A única integração entre o Hub e os demais é arquivo em disco.** Não há runtime, não há API obrigatória, não há serviço residente. Se o Hub for desinstalado, os hosts continuam funcionando.

## Princípios

Independência, portabilidade, local-first, neutralidade de providers, controle humano, **segurança por padrão**, separação entre autoria e execução, rastreabilidade e extensibilidade.

Três que merecem destaque porque a pesquisa mostrou que são fáceis de perder:

1. **Nada é executado no MVP.** Sem sandbox comprovado em Windows, prometer "testado" seria alegação falsa.
2. **Confiança é decisão humana registrada**, não score. Scanner verde produz evidência, nunca aprovação.
3. **Nenhum segredo tem lugar no schema.** `secrets.envVars` aceita apenas nomes de variáveis.
4. **Integridade não é assinatura.** O Hub verifica hashes; não assina nada. "Índice assinado" é vocabulário proibido até existir assinatura de verdade.
5. **Privado e público não são a mesma operação.** Backup local nunca é bloqueado; redistribuição pública exige direitos comprovados.

## Documentação

### Research
- [Auditoria de repositórios e branches](docs/research/REPOSITORY-AND-BRANCH-AUDIT.md)
- [Candidatos de integração e pesquisa externa](docs/research/INTEGRATION-CANDIDATES.md)
- [Revisão de consistência da Fase 0.1](docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md)

### Architecture
- [Fronteiras de produto, arquitetura e modelo de dados](docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md)
- [Modelo de segurança e confiança](docs/architecture/SECURITY-AND-TRUST-MODEL.md)
- [Dados, armazenamento e portabilidade](docs/architecture/DATA-STORAGE-AND-PORTABILITY.md)

### Product
- [Plataforma e stack](docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md)
- [MVP e roadmap](docs/product/MVP-AND-ROADMAP.md)

### Operações
- [Relatório de conclusão funcional](docs/operations/FUNCTIONAL-COMPLETION-REPORT.md) — M1–M8 com classe, evidência e comandos
- [Checklist de prontidão](docs/operations/PRODUCT-READINESS-CHECKLIST.md) — o que está pronto, para quê, e o que nunca deve ser verdade
- [Validação Windows](docs/operations/WINDOWS-VALIDATION-REPORT.md) — execução real, com o que passou e o que ficou bloqueado
- [Plano de validação e build](docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md)

### Google Stitch
- [Relatório de integração](docs/operations/STITCH-INTEGRATION-REPORT.md) — o que foi importado, catalogado e o que depende de host autenticado
- [Catálogo do Stitch](docs/stitch/CATALOG.md) — 16 Skills e 1 servidor MCP, com dependências reais
- [Configuração do MCP](docs/stitch/MCP-SETUP.md) — endpoint, autenticação e limites; o Hub não conecta
- [Codex e outros hosts](docs/stitch/CODEX-AND-OTHER-HOSTS.md) — catalogado, instalado, configurado e disponível não são a mesma coisa
- [Workflow de UI/UX](docs/stitch/workflow/lia-uiux-workflow.md) — 7 etapas, do discovery ao feedback de implementação
- [Padrão de handoff](docs/stitch/handoff/README.md) — `docs/design/` e a regra de precedência
- [Design brief do Hub](docs/stitch/design-brief-hub/README.md) — identidade, telas, estados e prompts

### Governança
- [Relatório final da Fase 0](docs/PHASE-0-FINAL-REPORT.md)
- [Registro de decisões](docs/DECISION-REGISTER.md)
- [Visão de produto e direção arquitetural](docs/PRODUCT-VISION.md)
- [Mandato de pesquisa da Fase 0](docs/PHASE-0-ARENA-BRIEF.md)
- [Fluxo de branches e releases](docs/BRANCH-AND-RELEASE-FLOW.md)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) — nenhum código de terceiros incorporado
- [`.gitignore`](.gitignore) — higiene adaptada do kit Lia

## Próximo passo

A Fase 1 depende de quatro decisões humanas (`D-13` escopo do MVP, `D-14` stack, `D-03` formato, `D-06` armazenamento) e de uma quinta que pode correr em paralelo: pesquisa de isolamento em Windows (`D-05`/`D-18`), que determina se o produto terá Test Lab algum dia.

`D-16` — a **licença deste repositório** — continua aberta e é decisão humana. O `LICENSE` **não** foi criado, de propósito.

A implementação só começa após revisão humana e aprovação explícita da especificação resultante.

Consulte também [AGENTS.md](AGENTS.md) para as regras deste repositório, inclusive a distinção obrigatória entre `IMPLEMENTED`, `EXECUTED`, `VALIDATED`, `PROPOSED`, `PLANNED`, `RESEARCH` e `UNKNOWN`.

## Inventário e governança central

A [proposta de governança central](docs/architecture/CENTRAL-CAPABILITY-GOVERNANCE.md)
define a entrada por projeto e o compartilhamento de capacidades. O
[contrato de inventário](docs/architecture/CAPABILITY-INVENTORY-CONTRACT.md)
especifica registros, evidências e compatibilidade com o formato v1.
A [matriz e o plano](docs/operations/CAPABILITY-REGISTRY-READINESS.md)
registram lacunas e testes executados.
