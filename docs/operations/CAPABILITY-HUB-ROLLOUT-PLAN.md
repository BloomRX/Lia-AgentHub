# Plano de produto e migração para o Lia Agent Hub

**19 de novembro de 2026 · Plano de implementação.** A entrega começa no Hub e
termina com a adoção pelos projetos Lia. A fonte canônica das Skills
administradas passa para o Hub. Cada projeto conserva as referências às versões
que escolheu e instala uma cópia materializada somente quando seu host precisa
dos arquivos para carregar a Skill. Essa cópia é derivada, auditável e recriável.

O plano usa a [governança central](../architecture/CENTRAL-CAPABILITY-GOVERNANCE.md),
o [inventário v1](../architecture/CAPABILITY-INVENTORY-CONTRACT.md) e o
[contrato de hosts](../architecture/CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md).
Os 17 registros v1 já verificados são a primeira base de compatibilidade.
As referências do Lia-Research sobre licença, atribuição e duplicatas
(LR-LIC-001, LR-LIC-003, DR-0007) orientam a migração. LR-MCP-002, DR-0011
e DR-0012 orientam o catálogo MCP e a configuração revisável.

## 1. Produto e escopo da oficina

| Capacidade | Ações no Hub | Ações no projeto ou host |
| --- | --- | --- |
| Agent Skill | Criar rascunho, duplicar com atribuição, editar SKILL.md e anexos permitidos, inspecionar diferenças, validar, versionar e empacotar | Selecionar a revisão, materializar localmente e carregar sob as permissões do host |
| Servidor MCP e ferramenta MCP | Criar e editar descritores passivos, relacionar tools ao servidor, comparar contrato e preparar configuração revisável | Instalar quando aplicável, configurar, resolver segredos, conectar e registrar evidência operacional |
| CLI, plugin, pacote, perfil, modelo, provedor, workflow e recurso | Catalogar tipos reais, referências, versões, requisitos, dependências e evidências. Editar metadados sob autoridade do mantenedor | Adotar, configurar ou executar conforme política própria |

A oficina de Skills começa com criação do SKILL.md, edição de frontmatter e
Markdown, prévia local, relatório de referências, diff de conteúdo e metadados
e histórico. Rascunho é editável. Publicar uma revisão congela conteúdo e hash.
Conflitos de edição retornam a versão atual para comparação. Um fork guarda
ID e crédito do upstream e exige base para copiar ou redistribuir. Skills
referenciadas podem ser mantidas por ponteiro quando a cópia não estiver
autorizada. Scripts podem ser inventariados e inspecionados como dados.
A primeira entrega da oficina usa domínio e CLI. A experiência visual será
desenhada no Stitch sobre os contratos aprovados.

## 2. Fluxo de dados e decisões

1. Receber inventário, conferir origem e hash e classificar tipos.
2. Registrar identidade estável e revisão, preservando aliases locais.
3. Adicionar payload autorizado à quarentena ou criar registro referenciado.
4. Validar estrutura, arquivos, dependências, referências e integridade.
5. Registrar aprovação humana por revisão, digest e canal, quando necessária.
6. Preparar pacote ou configuração, com atribuição e avisos.
7. O projeto revisa e fixa ID central, revisão, hash, perfil e dependências
   resolvidas num manifesto de consumo versionado. O manifesto declara
   também as referências indispensáveis ao bootstrap.
8. O host materializa a revisão mediante ação explícita ou usa um pacote
   local previamente preparado. Pode iniciar com Hub fechado e sem rede.
   Divergência de hash ou dependência obrigatória ausente produz erro acionável.
9. Evidência emitida pelo host distingue disponível para configuração,
   configurado e operacional. Publicação, licença declarada, confiança e
   integridade mantêm seus escopos próprios.

O índice e os pacotes atuais permanecem legíveis. O novo manifesto é aditivo.
Credenciais ficam nos hosts. Referências, links, anexos e metadados importados
são tratados como dados. D-05 e D-18 mantêm execução e Test Lab fora da
entrega. D-16 e direitos de terceiros seguem sob decisão humana.

## 3. Fases de implementação

| Fase | Trabalho | Critério de saída |
| --- | --- | --- |
| 0 · Inventário | Fixar branch e commit de cada projeto. Identificar SKILL.md, arquivos dependentes, aliases, caminhos usados por agentes e automações, licença e origem. Classificar cópia própria, compartilhável, derivada ou de terceiros | Inventário conferido pelo mantenedor. Cada Skill tem destino, origem, dependências e situação jurídica, inclusive quando desconhecida |
| 1 · Registro | Leitor somente leitura, limites, identidade persistente, revisões, aliases, duplicatas, conflitos e relatórios | Reimportação idempotente. Mesmo ID/revisão com hash diferente gera conflito. Os 17 registros v1 e consumidores de índice e pacote passam |
| 2 · Oficina | Rascunho, criação, edição, prévia, diff, validação, publicação imutável, forks e restauração de revisão | Criar e editar uma Skill sintética até gerar pacote verificável. Conflito concorrente, anexos inseguros e tentativa de perda de atribuição exercitados |
| 3 · Consumo | Manifesto por projeto, adaptação dos caminhos atuais, materialização local e configuração revisável | Instalação explícita em checkout limpo, inicialização offline, revisão fixada e rematerialização com digest idêntico |
| 4 · Migração | Rodar inventário, migração, operação paralela, corte e rollback por projeto | Paridade nos fluxos de cada projeto, reversão testada e aprovação do mantenedor para a remoção |
| 5 · Operação | Atualização explícita, rollback, revogação, relatórios e verificação de referências fixadas | Atualização ensaiada, restauração reproduzida e responsabilidades de manutenção registradas |

## 4. Ordem inicial de adoção

| Projeto | Primeira onda e verificação antes do corte |
| --- | --- |
| Agent Hub | Publicar uma Skill própria como primeira cobaia. Verificar bootstrap num checkout limpo e com Hub fechado antes de retirar qualquer Skill de desenvolvimento da árvore |
| Lia Desktop / Lia-Project | Pilotar uma Skill com dependências simples. Resolver os caminhos usados por perfis e ferramentas do Desktop. Verificar abertura de workspace e carregamento da revisão fixada |
| Lia Forge | Pilotar uma Skill de pipeline. Verificar referências, assets e ferramentas auxiliares. Preservar atribuição e licença por componente |
| Lia Studio | Pilotar uma Skill de desenvolvimento ou editor. Verificar caminhos usados por sessões e automações e reproduzir o carregamento em um projeto isolado |
| Lia Model Lab | Pilotar uma Skill de avaliação. Versionar separadamente scripts de avaliação, modelos, pesos e evidências de medição |
| Lia Go | Inventariar Skills se houver e migrar as de desenvolvimento quando o bootstrap estiver comprovado. Consumo no aplicativo depende do recorte de IA e do contrato de host já em discussão |
| Lia-Research | Usar os IDs e evidências como referência. Se houver Skills administráveis no repositório, aplicar o mesmo inventário e corte com seu mantenedor. Relatórios e corpus permanecem no Research |

A fase 0 confirma o universo de repositórios e registra outros projetos Lia
que mantiverem Skills, com o mesmo procedimento. Ordem e primeira Skill são
escolhas iniciais do plano, sujeitas aos resultados do inventário.

## 5. Procedimento obrigatório de corte por projeto

1. Registrar baseline Git, inventário, hashes de árvore, grafo de anexos e
   todos os carregadores, caminhos e referências de automação. Guardar o SHA
   anterior ao corte e a lista exata de arquivos que podem ser removidos.
2. Importar o material elegível no Hub, com origem fixada e atribuição.
   Conferir hash e leitura de anexos. Material com autoria ou direitos
   pendentes fica referenciado ou bloqueado para a ação afetada.
3. Com cópias ainda disponíveis, introduzir manifesto de consumo e configurar
   o host para usar as revisões do Hub. Materializar somente via ação
   autorizada. Verificar paridade de nomes, bytes, comportamento dos
   carregadores, CI, ferramentas, bootstrap e uso offline.
4. Testar a operação em checkout limpo sem depender das cópias antigas.
   Ensaiar a reversão. Após revisão do mantenedor, remover as cópias
   autoritativas dos caminhos versionados e ajustar as referências no mesmo
   corte revisável. Arquivos consumidos apenas por cópia derivada ficam fora
   da árvore versionada ou são artefatos gerados rastreáveis.
5. Rodar regressão após remoção. Registrar projeto, commits, hashes, revisões,
   testes e exceções. Se falhar, reverter o commit de corte e restaurar as
   referências e a última revisão materializada. Preservar o histórico no Hub.

Dependências de bootstrap só entram na remoção quando um checkout limpo
consegue reconstruir a configuração sem depender da própria Skill removida.
Conteúdo de terceiros sem base de cópia e recursos específicos de build
devem ter exceção nominal, motivo, mantenedor e condição de fechamento.
Deduplicação se decide por revisão com atribuição preservada. Igualdade de
nome ou hash não autoriza fusão ou reclassificação de autoria.

## 6. Aceitação final

- Cada projeto tem inventário conferido e resultado registrado para cada Skill.
- Skills migradas têm fonte canônica no Hub, revisão fixada, hash e autoria.
  Referências bloqueadas e exceções têm responsável e motivo.
- A oficina cria, edita, valida, compara e publica revisões reproduzíveis.
- Testes cobrem leitor v1, edição concorrente, integridade, arquivos inseguros,
  licenças, revogação, atualização e rollback. Testes reais por projeto
  comprovam caminhos, CI e funcionamento offline após o corte.
- O Hub prepara metadados, pacotes e configurações sem executar capacidades.
  Instalação e operação seguem com evidência de cada host.
- Distribuição pública do executável segue sua homologação própria, incluindo
  WebView2, Windows limpo, assinatura e decisão de licença.

## Execução · baselines do inventário

A branch do Hub avançou até `7eb65a4`. Nessa revisão já existem leitor,
recebimento de inventário, projeção de proveniência múltipla e quarentena por
colisão de aliases. A oficina de edição e os cortes seguem fases próprias.

A primeira varredura consultou árvores Git fixadas em commits por
`docs/operations/evidence/scan-rollout-sources.ps1`. Gerou um arquivo local
`%TEMP%\lia-skills-source-inventory.json` com caminhos, blobs Git, modos de
arquivo e arquivos adjacentes a cada Skill. Arquivo adjacente é candidato a
anexo. As referências efetivas, autoria e direitos ainda precisam de revisão.

| Projeto | Revisão examinada | SKILL.md versionados |
| --- | --- | --- |
| Hub | 7eb65a4 | 0 |
| Desktop / Project | 9778ffb | 51 |
| Studio | b099c4a | 16 |
| Forge 2.0 | 4b4c714 | 1 |
| Go | be21889 | 0 |
| Research | 33074e2 | 0 |
| Model Lab | Revisão não resolvida. API retornou 404 | Desconhecido |

Os totais valem para as revisões examinadas. Os checkouts antigos de Project
e Forge apontavam para diretórios Git ausentes. A descoberta de revisões
alternativas e repositórios adicionais segue na fase 0. Os candidatos desta
varredura ainda aguardam classificação de migração.

## Execução · oficina de Skills pela CLI

A oficina mantém rascunhos Markdown e revisões publicadas em SQLite sob
a raiz de dados do Hub. A geração protege contra edições concorrentes.
Publicar a mesma geração é idempotente. Restaurar cria uma nova geração
editável e conserva as revisões anteriores.

| CLI  | Uso |
| --- | --- |
| python -m lia_agenthub skill create SKILL.md | Criar rascunho |
| python -m lia_agenthub skill edit ID GERACAO SKILL.md | Substituir o texto com controle de versão |
| python -m lia_agenthub skill preview ID | Mostrar conteúdo e achados de validação |
| python -m lia_agenthub skill publish ID GERACAO | Gravar revisão imutável com SHA-256 |
| python -m lia_agenthub skill history ID | Listar revisões publicadas |
| python -m lia_agenthub skill diff ID REVISAO | Comparar a revisão com o rascunho |
| python -m lia_agenthub skill restore ID GERACAO REVISAO | Restaurar o conteúdo em nova geração |
| python -m lia_agenthub skill pack ID REVISAO --dest PASTA | Gerar backup privado da revisão em .lia-capability |

A cobertura atual da oficina é o texto do SKILL.md. Anexos, forks com
procedência, integração das revisões ao catálogo central e materialização
pelos hosts continuam pendentes. Execução de conteúdo permanece com o host.
