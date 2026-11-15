# Lia Agent Hub — Visão de Produto e Direção Arquitetural

**Status:** proposta inicial para pesquisa e definição de produto  
**Nome:** Lia Agent Hub (nome de trabalho; sujeito a validação)  
**Tipo:** plataforma independente para criar, descobrir, validar, organizar, versionar e distribuir capacidades para agentes de IA  
**Implementação:** não autorizada nesta fase  
**Documento:** briefing de referência para uma sessão dedicada ao Lia Agent Hub

---

## 1. Resumo executivo

O **Lia Agent Hub** é a proposta de um terceiro produto independente no ecossistema Lia. Seu propósito não é ser apenas um catálogo ou instalador de Skills e MCPs: deve ser uma oficina e plataforma para **criar, descobrir, editar, testar, validar, versionar, empacotar e distribuir capacidades para agentes de IA**.

Essas capacidades devem poder atender diferentes domínios, não somente desenvolvimento de jogos. Exemplos:

- Desenvolvimento de jogos e engines.
- Programação e engenharia de software.
- Arte, design e criação de conteúdo.
- Pesquisa e análise.
- Produtividade e automação.
- Lazer, hobbies e entretenimento.
- Outros domínios e projetos que utilizem agentes compatíveis.

O Lia Studio e o Lia Forge seriam consumidores independentes das capacidades publicadas ou disponibilizadas pelo Hub:

- **Lia Agent Hub:** cria, organiza, valida, empacota e distribui capacidades.
- **Lia Studio:** coordena agentes e o desenvolvimento de jogos; mantém o contexto do projeto, as permissões e a execução das ferramentas no ambiente de desenvolvimento.
- **Lia Forge:** produz e valida assets por meio de seus próprios modelos, providers e workflows especializados; pode consumir Skills e integrações compatíveis sem transferir ao Hub a lógica especializada de produção.

A direção recomendada é construir primeiro uma **biblioteca compartilhada e portátil de capacidades**, com uma aplicação própria para administrá-la. O Hub não deve se tornar um runtime obrigatório para Studio, Forge ou agentes externos.

**Ainda não se deve criar o repositório de produto nem implementar o aplicativo.** Primeiro é necessário auditar o que Studio e Forge já possuem, pesquisar as soluções existentes, definir o escopo, os contratos, a segurança e a estratégia de distribuição e, então, aprovar uma especificação.

## 2. Problema e motivação

Skills, MCPs, CLIs, APIs, plugins, extensões, bibliotecas, frameworks e workflows podem ampliar as capacidades dos agentes. Porém, sem uma camada especializada para administrá-los, cada produto pode acabar:

- Repetindo pesquisas e avaliações de ferramentas.
- Mantendo catálogos e versões duplicados.
- Criando Skills equivalentes em diferentes projetos.
- Instalando recursos sem uma avaliação consistente de licença, segurança e manutenção.
- Misturando instruções de uma Skill com código executável ou ferramentas externas.
- Acoplando a gestão das capacidades a um único aplicativo ou runtime.
- Atualizando recursos sem histórico, validação ou possibilidade clara de reversão.

O Hub pretende oferecer um local independente para trabalhar essas capacidades e disponibilizá-las a diferentes produtos e agentes, preservando a autonomia de cada consumidor.

## 3. Princípios fundamentais

1. **Independente:** o Hub deve ter utilidade própria e não depender do Studio ou do Forge para funcionar.
2. **Portátil:** priorizar formatos e contratos abertos sempre que adequados, evitando aprisionar Skills a um único agente ou aplicação.
3. **Local-first:** começar com funcionamento local, sem exigir conta, nuvem ou serviço pago para as funções essenciais.
4. **Provider-neutral:** não exigir um único modelo, provedor de IA ou serviço externo. O usuário deve poder escolher opções locais, gratuitas ou pagas quando aplicável.
5. **Human-in-control:** descoberta, criação assistida, instalação, execução, atualização e publicação devem ter controles e consentimentos claros.
6. **Segurança por padrão:** conteúdo externo deve ser tratado como não confiável até ser inspecionado e validado.
7. **Separação de responsabilidades:** criar e distribuir capacidades é diferente de executá-las em um projeto.
8. **Sem duplicação de domínio:** o Hub não deve absorver os workflows especializados de produção de assets do Forge nem a orquestração e QA de jogos do Studio.
9. **Rastreabilidade:** registrar fonte, autor, licença, versão, dependências, alterações, validações e proveniência.
10. **Extensível:** permitir novos domínios, produtos e tipos de agente sem redesenhar a plataforma a cada integração.

## 4. Modelo de responsabilidades no ecossistema Lia

### 4.1 Lia Agent Hub — criação e distribuição

Responsabilidades propostas:

- Descobrir e catalogar Skills e outros recursos para agentes.
- Criar e editar Skills, inclusive com assistência de IA.
- Inspecionar estrutura, instruções, scripts, referências e dependências.
- Criar, documentar e testar configurações e pacotes de MCPs.
- Avaliar CLIs, APIs, plugins, extensões, bibliotecas, frameworks e workflows.
- Validar formato, compatibilidade, qualidade e riscos.
- Administrar metadados, fontes, licenças, versões e histórico.
- Empacotar, exportar, importar e distribuir capacidades.
- Organizar coleções por domínio, projeto, produto e agente.
- Manter relatórios de avaliação e estado de confiança.

### 4.2 Lia Studio — desenvolvimento de jogos e runtime host

Responsabilidades que permanecem no Studio:

- Orquestrar agentes e subagentes de desenvolvimento.
- Gerenciar projetos, tarefas, sessões e contexto de desenvolvimento.
- Controlar permissões dos agentes no contexto do projeto.
- Gerenciar conexões e execução de MCPs no ambiente do Studio.
- Controlar credenciais, aprovações, isolamento, orçamento, cancelamento e auditoria da execução.
- Integrar engines, terminal, Git, arquivos, builds, testes e ferramentas de desenvolvimento.
- Executar QA de gameplay e validar o jogo em funcionamento.
- Selecionar e habilitar Skills adequadas aos agentes, tarefas e projetos.

O Studio pode ter uma interface de descoberta/seleção de Skills e estado de sincronização, mas não deve ser o proprietário exclusivo da biblioteca universal nem precisar implementar um segundo criador genérico de Skills.

### 4.3 Lia Forge — produção especializada de assets

Responsabilidades que permanecem no Forge:

- Criar e manter workflows próprios de geração e edição de assets.
- Gerenciar providers e modelos especializados em 2D, 3D, personagens, texturas, spritesheets, rigging, animações, materiais e áudio.
- Executar pipelines de produção de assets.
- Validar aspectos técnicos dos artefatos produzidos.
- Registrar metadados, versões, hashes, proveniência e estágios do asset.
- Manter suas regras de domínio e sua experiência de produção independente.
- Consumir Skills e ferramentas compatíveis disponibilizadas pelo Hub, sem depender dele para executar seus recursos essenciais.

O Hub não deve duplicar o Tool Provider Hub, Workflow Engine, Intelligent Orchestrator ou os pipelines especializados já projetados no Forge. Antes de propor uma capacidade, deve consultar a implementação e os documentos atuais do Forge.

## 5. Separar criação/distribuição de execução

A arquitetura deve distinguir dois planos:

### Plano A — autoria, curadoria e distribuição (Lia Agent Hub)

Responsável por criar, editar, inspecionar, validar, versionar, empacotar e disponibilizar capacidades.

### Plano B — consumo, permissões e execução (aplicações host)

Responsável por carregar e executar capacidades no contexto real de cada produto, agente ou projeto.

Exemplos:

- O Hub pode criar e empacotar uma Skill para operar Blender; o Studio ou Forge decide qual agente pode utilizá-la.
- O Hub pode documentar e validar um servidor MCP; o Studio ou Forge mantém a conexão, credenciais, aprovações e política de execução no seu contexto.
- O Hub pode distribuir uma Skill compatível com vários agentes; cada host decide se ela é compatível e se está autorizada naquele projeto.

**O Hub não deve ser um runtime central obrigatório.** Também não deve concentrar todas as credenciais de Studio, Forge ou agentes externos. Credenciais, aprovações e políticas de execução pertencem ao host que executa a capacidade.

## 6. Tipos de recursos que o Hub deve distinguir

O Hub não deve tratar todos os recursos como se fossem Skills. Deve classificar explicitamente:

1. **Agent Skill:** instruções, conhecimento e procedimentos reutilizáveis; pode conter referências e scripts.
2. **MCP Server:** disponibiliza ferramentas, recursos ou prompts via protocolo MCP.
3. **CLI / ferramenta executável:** programa chamado por um agente ou workflow.
4. **API / serviço externo:** capacidade acessada por uma interface de serviço.
5. **Plugin / extensão:** amplia outro aplicativo ou ambiente.
6. **Framework / runtime de agentes:** infraestrutura para construir ou executar agentes.
7. **Provider / modelo de IA:** serviço ou modelo que fornece uma capacidade de IA.
8. **Workflow / pipeline / template:** sequência estruturada de operações.
9. **Biblioteca / SDK:** componente reutilizável por código.
10. **Referência técnica:** documentação, pesquisa ou exemplo que não é um recurso instalável.

Um recurso pode depender de outro. Por exemplo, uma Skill pode instruir o agente a usar um servidor MCP e uma CLI. Essas dependências devem ser registradas separadamente, com versões, fontes e riscos próprios.

O formato de Agent Skills com `SKILL.md` deve ser avaliado como uma opção de portabilidade. A compatibilidade não deve ser presumida: o Hub deverá validar requisitos e diferenças entre os agentes/hosts consumidores.

## 7. Áreas funcionais propostas

### 7.1 Capability Library

- Catálogo local de recursos.
- Pesquisa, filtros, categorias, tags e coleções.
- Fontes oficiais, repositórios e documentação.
- Estado de manutenção e versões.
- Licenças e condições comerciais.
- Compatibilidade com produtos, agentes e runtimes.
- Dependências e recursos relacionados.
- Estados distintos: descoberto, em análise, aprovado, instalado/exportado, desatualizado, rejeitado ou arquivado.

### 7.2 Skill Creator

- Criar Skill do zero ou a partir de template.
- Assistência de IA para estruturar e revisar instruções.
- Editor para `SKILL.md`, referências e scripts.
- Visualização da estrutura do pacote.
- Metadados, escopo, compatibilidade e dependências.
- Histórico de alterações e comparação entre versões.
- Testes com cenários positivos, negativos e casos-limite.
- Exportação em formato portátil.

### 7.3 MCP Workshop

- Registrar e inspecionar servidores MCP.
- Acompanhar documentação, versões, fontes e licenças.
- Validar configuração e dependências.
- Testar ferramentas e recursos em ambiente controlado.
- Inspecionar permissões, operações, entradas e saídas.
- Criar documentação e exemplos de integração.
- Preparar pacotes/configurações para uso nos hosts.

O Workshop não deve se tornar o gerenciador central das conexões em produção de todos os produtos. Cada host deve executar e controlar suas próprias conexões.

### 7.4 Test & Security Lab

- Validar estrutura e metadados.
- Inspecionar scripts e executáveis.
- Detectar instruções suspeitas, prompt injection e comportamento inesperado.
- Verificar dependências, versões e integridade.
- Avaliar permissões e acesso a arquivos/rede/credenciais.
- Executar testes em ambiente isolado quando tecnicamente possível.
- Produzir evidências, limitações e relatório de confiança.
- Distinguir validação estática, teste controlado e validação real no host.

Nenhuma validação automática deve ser apresentada como garantia absoluta de segurança.

### 7.5 Publish & Distribute

- Versionar e empacotar capacidades.
- Exportar/importar arquivos e pacotes.
- Distribuir para Studio, Forge e agentes compatíveis.
- Administrar coleções e canais de versão.
- Controlar atualização e reversão.
- Exigir aprovação explícita para mudanças relevantes.
- Manter rastreabilidade da origem e da versão distribuída.

### 7.6 Domínios e coleções

O catálogo deve permitir categorias como:

- Game Development: Godot, Unity, Unreal, Blender, level design, game testing.
- Programming: linguagens, frameworks, arquitetura, depuração, testes e Git.
- Art & Design: UI/UX, ilustração, modelagem e design visual.
- Research: investigação, análise, documentação e avaliação técnica.
- Productivity & Automation: organização, automação e produtividade.
- Audio & Media: áudio, voz, edição, música e processamento de mídia.
- Leisure & Hobbies: jogos de mesa, hobbies e atividades recreativas.
- General Agent Capabilities: capacidades transversais.

As categorias são uma organização inicial, não uma lista fechada.

## 8. Distribuição e escopos de uso

Uma capacidade poderá ter um ou mais escopos:

- **Global:** disponível para vários produtos ou agentes autorizados.
- **Produto:** específica do Studio, Forge ou outro aplicativo.
- **Projeto:** disponível apenas em um projeto determinado.
- **Agente:** atribuída a um agente ou subagente específico.
- **Pessoal/local:** privada no ambiente do usuário.
- **Externa/exportada:** empacotada para um agente ou runtime de terceiros.

O escopo de disponibilidade não concede automaticamente permissão de execução. O host consumidor deve fazer suas próprias verificações de compatibilidade, confiança e autorização.

Não assumir sincronização em nuvem. A primeira estratégia deve considerar biblioteca local e importação/exportação explícitas. Sincronização remota, contas, marketplace ou colaboração online são possibilidades futuras, sujeitas a análise de custo, segurança e necessidade.

## 9. Segurança, licenças e confiança

O Hub deve tratar conteúdo externo como não confiável por padrão. Uma Skill pode conter instruções maliciosas, referências externas ou scripts executáveis; um MCP pode oferecer operações com acesso a arquivos, rede ou serviços.

A avaliação deve considerar:

- Licença do código, conteúdo, modelos e dados.
- Uso comercial e redistribuição.
- Permissões e escopos de execução.
- Scripts e dependências executáveis.
- Acesso a arquivos, diretórios e rede.
- Credenciais, tokens e dados enviados a terceiros.
- Prompt injection e instruções ocultas.
- Processo de atualização e risco de cadeia de suprimentos.
- Integridade, hashes e origem do pacote.
- Estado de manutenção, vulnerabilidades e transparência do projeto.

O Hub deve separar claramente:

- Descoberto — apenas localizado.
- Em análise — ainda não avaliado suficientemente.
- Validado — passou pelos testes especificados, com limitações registradas.
- Aprovado para distribuição — autorizado para disponibilização em determinado escopo.
- Habilitado no host — o aplicativo consumidor habilitou o recurso.
- Rejeitado/arquivado — não recomendado ou não mais mantido.

A aprovação no Hub não deve substituir o consentimento nem a política de execução do Studio, Forge ou outro host.

## 10. Relação com pesquisas existentes e Agent 6

Antes de propor a arquitetura definitiva, a sessão dedicada ao Lia Agent Hub deverá consultar o trabalho já realizado nos projetos.

### No Lia Studio

Auditar a arquitetura de agentes, Skills, Tool Registry, MCP, permissões, providers, execução e segurança. Identificar o que já existe, o que está em desenvolvimento e o que é apenas proposta.

### No Lia Forge

Auditar, entre outros documentos e componentes existentes:

- Tool Provider Hub.
- Workflow Engine.
- Intelligent Orchestrator.
- Asset Pipelines.
- Catálogos de modelos e providers.
- Avaliações de ferramentas externas.
- ADRs, auditorias e contratos de domínio.

Verificar os nomes e caminhos reais dos documentos no estado atual dos repositórios. Não pressupor que títulos lembrados ainda correspondem aos arquivos atuais.

### Pesquisa externa

Pesquisar fontes oficiais e projetos ativos, incluindo catálogos de Skills, servidores MCP, ferramentas para agentes, CLIs, APIs, plugins, frameworks e recursos de gamedev.

O usuário também poderá fornecer links específicos. Cada link deverá ser investigado, mesmo que não apareça nos catálogos mais conhecidos.

Para cada descoberta, registrar o tipo de recurso, fonte oficial, licença, manutenção, compatibilidade, requisitos, custos, riscos, duplicação e recomendação.

### Classificação de destino

Cada descoberta deve ser classificada como:

- Lia Agent Hub / biblioteca transversal.
- Lia Studio.
- Lia Forge.
- Compartilhada por mais de um produto.
- Outro domínio/projeto/agente.
- Apenas referência.
- Não recomendada.

Não forçar uma ferramenta a pertencer ao Studio ou Forge quando sua natureza for geral ou independente.

## 11. O que não deve ser absorvido pelo Hub

O Hub não deve:

- Tornar-se o orquestrador geral dos agentes do Studio.
- Substituir o runtime, as permissões ou a gestão de sessões do Studio.
- Substituir os workflows, providers ou orquestrador especializado do Forge.
- Executar QA de gameplay.
- Tornar-se uma engine ou ambiente completo de desenvolvimento de jogos.
- Centralizar credenciais de todos os produtos.
- Obrigar Studio, Forge ou agentes externos a depender de um serviço remoto.
- Instalar ou atualizar recursos silenciosamente.
- Tratar toda descoberta como segura ou autorizada.
- Duplicar funcionalidades já implementadas sem justificar a necessidade.

## 12. Questões que precisam de pesquisa e decisão

1. O nome final será Lia Agent Hub, Lia Skills, Lia Capability Hub ou outro?
2. O produto deve gerenciar apenas Skills e MCPs ou um catálogo mais amplo de capacidades desde o começo?
3. Quais formatos de Skill e metadados serão canônicos? Como preservar compatibilidade com formatos abertos?
4. Como representar dependências entre Skills, MCPs, CLIs e APIs?
5. Como testar Skills e servidores MCP de maneira reproduzível e isolada no Windows e Linux?
6. Qual estratégia local-first para armazenamento, versionamento, backup e exportação?
7. Como Studio e Forge receberão atualizações: importação, pacote local, API local ou outro contrato?
8. O Hub deve ter um SDK/CLI para integração com aplicações e agentes externos?
9. Quais recursos devem ser disponibilizados por API local e quais podem ser simples arquivos/pacotes?
10. Como evitar que atualizações alterem silenciosamente o comportamento dos agentes?
11. Como preservar licenças e avisos de terceiros em pacotes distribuídos?
12. Em que momento um catálogo remoto ou comunidade de publicação faria sentido?
13. Quais funcionalidades são essenciais para o primeiro MVP e quais devem esperar?
14. É melhor construir o aplicativo como produto Electron independente, aplicação web local ou outra arquitetura? A decisão deve considerar a tecnologia já adotada nos outros projetos, mas não a copiar automaticamente.

## 13. Fases candidatas de evolução

As fases abaixo são uma hipótese para discussão, não uma autorização de execução.

### Fase 0 — Pesquisa, auditoria e especificação

- Auditar Studio e Forge.
- Pesquisar soluções existentes.
- Mapear requisitos e usuários.
- Definir arquitetura, contratos, ameaças, licenças e MVP.
- Produzir ADRs e especificação revisável.

### Fase 1 — Biblioteca local e portabilidade

- Catálogo local.
- Importação/exportação de Skills.
- Metadados e proveniência.
- Versionamento e histórico.
- Compatibilidade e escopos.

### Fase 2 — Skill Creator e validação

- Editor e templates.
- Criação assistida.
- Validador estrutural.
- Testes controlados.
- Relatórios de qualidade e segurança.

### Fase 3 — MCP Workshop

- Catálogo e inspeção de servidores.
- Configuração e documentação.
- Testes controlados.
- Dependências e pacotes de integração.

### Fase 4 — Integrações com Studio e Forge

- Contratos explícitos de distribuição/consumo.
- Compatibilidade e instalação controlada.
- Atualizações com aprovação.
- Sem compartilhamento direto de stores internos.

### Fase 5 — Ecossistema mais amplo

- SDK/CLI e integrações externas.
- Coleções compartilháveis.
- Catálogo remoto opcional.
- Colaboração e publicação comunitária, se justificadas.

## 14. Critérios para aprovar um aplicativo independente

A proposta de um produto autônomo deve ser confirmada por evidências de que:

- Há usuários além do Studio e Forge.
- A criação e gestão de capacidades têm ciclo de vida próprio.
- Há valor real em compartilhar e distribuir recursos entre projetos e agentes.
- Os formatos e contratos podem ser suficientemente portáteis.
- A manutenção do Hub não cria mais acoplamento do que remove.
- O MVP pode ser entregue sem reconstruir runtimes ou gerenciadores já existentes.

Se a pesquisa mostrar que um aplicativo independente seria prematuro, a alternativa deve ser manter a biblioteca e os contratos como componentes independentes, adiando a interface própria — sem abandonar a portabilidade.

## 15. Instrução para a sessão dedicada ao Lia Agent Hub

A nova sessão deve tratar este documento como **briefing inicial e proposta de produto**, não como arquitetura final aprovada.

Ordem de trabalho recomendada:

1. Ler este documento integralmente.
2. Auditar os repositórios atuais do Lia Studio e Lia Forge, usando suas branches de desenvolvimento relevantes e identificando os documentos reais.
3. Diferenciar implementação existente, protótipo, pesquisa, proposta e decisão aprovada.
4. Identificar sobreposições e lacunas.
5. Pesquisar soluções externas e referências oficiais atualizadas.
6. Incorporar os links específicos enviados pelo usuário.
7. Propor escopo, arquitetura, contratos e MVP do Lia Agent Hub.
8. Produzir documentação de pesquisa e especificação para revisão humana.

**Restrições iniciais:** não criar código de produto, não instalar ferramentas, não migrar funcionalidades, não modificar o Studio nem o Forge e não abrir uma implementação antes da aprovação humana da especificação.

A sessão deve terminar com recomendações fundamentadas, decisões pendentes claramente identificadas e uma proposta de próximos passos. Não tratar nenhuma fase candidata deste documento como autorização automática para implementação.

---

## 16. Referências conceituais iniciais

Estas referências são pontos de partida, não endossos ou decisões de integração:

- Agent Skills — especificação e documentação do formato aberto: https://agentskills.io/
- MCP — documentação oficial do Model Context Protocol: https://modelcontextprotocol.io/
- Skills.sh — diretório/ecossistema de descoberta de Skills: https://skills.sh/

Todas as referências externas devem ser verificadas quanto a estado atual, licença, manutenção, segurança e adequação antes de serem recomendadas para uso no ecossistema Lia.