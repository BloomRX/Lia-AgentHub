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

## Execução · consumo local de revisões

O comando de empacotamento da oficina aceita --profile e retorna um objeto
lock. O projeto revisa e guarda esse objeto como manifesto. Ele fixa o ID
da oficina, a revisão, o ID do pacote v1, a versão declarada, o perfil e os
dois hashes SHA-256. A primeira implementação aceita Skills sem dependências
resolvidas externamente. A seleção e o armazenamento local do pacote são
responsabilidade do consumidor.

Passos para reproduzir o ensaio:

1. Usar python -m lia_agenthub skill pack ID REVISAO --profile PERFIL.
2. Salvar somente o objeto lock do JSON retornado em skill-lock.json.
3. Executar python -m lia_agenthub skill materialize skill-lock.json PACOTE DESTINO.
   Destino é um diretório novo. O comando precisa da CLI, do manifesto e do
   pacote local. A base de dados da oficina pode estar ausente.
4. Para atualizar ou reverter, materializar a revisão fixada correspondente em
   diretório novo e alterar a referência do host depois da verificação.

O materializador verifica o pacote, o manifesto, a procedência e cada arquivo,
valida os caminhos e só expõe a pasta final depois de conferir a árvore.
O ensaio automatizado comprova bytes idênticos, recusa pacote alterado,
preservação de destino existente, materialização da segunda revisão e
reprodução da primeira. Ainda falta validar o carregamento em projetos reais.

A regressão Windows desta etapa registrou 837 testes aprovados e um skip de
symlink. Na triagem inicial, 22 Skills do Project estavam em .agents e 29
sob airi; as 16 do Studio e a do Forge 2.0 estavam em .agents. As amostras
lia-agent-evaluation, lia-game-design-review e lia-brand-check não declaram
licença no frontmatter. Os três commits contêm LICENSE na raiz. A cobertura
de cada arquivo e a atribuição de upstream ainda precisam ser confirmadas
no inventário de migração.

## Execução · anexos e primeiro piloto do Hub

Create e edit recebem um SKILL.md em UTF-8 ou uma pasta de Skill. Editar
somente o SKILL.md mantém os anexos registrados. Editar pela pasta substitui
o conjunto de anexos mediante conferência de geração. Preview lista anexos,
diff mostra adições, remoções e mudanças, e publish fixa o hash da árvore.
Restore recupera conteúdo e anexos da revisão anterior. Revisões antigas
sem anexos continuam legíveis.

O piloto local lia-inventory-review publicou a revisão 1 com dois arquivos
e gerou um pacote privado para o perfil lia-agent-hub. A CLI materializou
o pacote em outra pasta sem criar a raiz de dados informada pelo consumidor.
Get-FileHash confirmou byte a byte o SKILL.md e revisao.md. O digest de árvore
foi fc46ee5cfeee5cd3a01b34e4a198a28acf01ecdc81a9faf2a94c00f4161b3106.
O cenário materializou os arquivos como dados. Falta provar o carregamento
pelo host de um projeto e a remoção controlada de uma cópia real.

A regressão desta entrega registrou 838 aprovados e um skip de symlink.
A verificação direta da licença corrige a triagem anterior: o caminho
LICENSE na raiz do commit de Project retornou 404. Studio e Forge 2.0
retornaram textos MIT. A licença do repositório e o escopo de eventual
material de terceiros devem ser conferidos separadamente por Skill.

## Execução · procedência e ensaio de migração do Studio

A oficina aceita create --origin com um snapshot de procedência composto por
repositório HTTPS, commit Git completo, caminho, autor, mantenedor, caminho e
SHA-256 da evidência de licença e SHA-256 da árvore de origem. A oficina
compara a árvore aos arquivos recebidos, conserva a evidência ao editar e
inclui os dados em provenance.json do pacote privado. Campos desconhecidos
são recusados. Autor e mantenedor podem ser nulos. Registrar a procedência
não concede autorização de redistribuição.

O ensaio local usou lia-game-design-review, de
BloomRX/Lia-Studio@b099c4ad6b1d26b7e857290fcb333e311b8ae515. A GitHub API
entregou a Skill e o LICENSE da raiz. git hash-object --no-filters
conferiu os dois blobs. A Skill não declara autor próprio. O pacote
conservou a origem e a evidência do LICENSE como metadados. O LICENSE
original permaneceu junto dos artefatos do ensaio local.

A CLI recriou .agents/skills/lia-game-design-review/SKILL.md num destino
isolado e conferiu SHA-256 do arquivo comparado ao blob baixado. Hash da
árvore: 1a4b2cd91999be9183767244d01af9fc47c1150e0a15259368cc57bbb773b652.
O ensaio não é prova de adoção operacional. Faltam o carregamento pelo host
real, a validação de dependências e o corte da cópia no Studio.

O leitor real do checkout Studio em 4e103271633cdd12c03019fa2d6d517cbc35de59
também listou e abriu a Skill materializada como builtin por list_skills e
get_skill. No ensaio, SKILLS_DIR apontou para a pasta isolada. A revisão
calculada pelo Studio foi
82aed1a88f28f85f95c20f4725fe493d62ef2c1767802df9c5f81b6b5592f43a.
Isso confirma a leitura pelo código existente. O caminho de bootstrap e a
receita desktop do Studio, que empacota .agents/skills, ainda precisam
consumir a revisão materializada em um checkout limpo.

## Execução · ensaio de corte e build do Studio

O comando scripts/bootstrap_studio_skill.ps1 prepara uma Skill fixada no
caminho padrão do Studio. Ele exige paths locais e perfil lia-studio,
recusa o manifesto de outra Skill e preserva qualquer destino existente.

Em 4e103271633cdd12c03019fa2d6d517cbc35de59, exportei uma árvore limpa do
Studio para pasta de ensaio, retirei a pasta de lia-game-design-review
somente da cópia isolada, materializei a revisão do Hub no caminho padrão e
rodei python -m unittest discover -s tests -p test_skills_progressive.py.
Os três testes passaram. O leitor listou a Skill como builtin pela
configuração padrão. Recoloquei a pasta original e os mesmos três testes
passaram na reversão. Um segundo snapshot limpo confirmou o script de
bootstrap, a recusa de manifesto incorreto e a proteção do destino existente.

A exportação Git do Windows continha 23 CRLF. O pacote preservou LF, igual
ao blob Git c8604014913cf28b3bb4751a92183e5a06bdb23b. Os arquivos ficaram
idênticos após normalizar essas terminações. O build desktop real via
desktop/build_windows.ps1 e PyInstaller terminou com LiaStudio.exe e com
o SHA-256 82aed1a88f28f85f95c20f4725fe493d62ef2c1767802df9c5f81b6b5592f43a
para a Skill incluída. Janela e runtime do Studio ficaram fora deste ensaio.

O corte no repositório ainda depende de acordar com o mantenedor como o
projeto obterá o pacote aprovado e persistirá o manifesto, revisar as
restrições de licença e aplicar o mesmo procedimento ao inventário inteiro.

## Execução · ensaio do inventário completo do Studio

O commit de base 4e103271633cdd12c03019fa2d6d517cbc35de59 contém 16 Skills
versionadas e 7 anexos sob a Skill de bootstrap. Uma exportação Git com
core.autocrlf=false forneceu os arquivos. Cada arquivo conferiu com seu
blob Git antes de entrar na oficina. Os 16 pacotes privados carregam
procedência com commit, caminho, mantenedor do projeto e hash da
evidência de licença. A árvore verificada de cada pacote e da cópia
materializada bateu com a árvore original.

O lote persistente local, separado dos repositórios, está em
J:/Lia/migration/agent-hub/studio-4e10327. Reúne os 16 pacotes, os manifestos
individuais e de conjunto, a base SQLite da oficina, LICENSE e
THIRD_PARTY_NOTICES.md copiados da revisão estudada. A base e os pacotes
servem ao ensaio privado.

Retirei as 16 pastas versionadas de duas exportações isoladas do Studio.
A primeira usou os manifestos individuais; a segunda usou
scripts/bootstrap_studio_library.ps1 e o lote persistente. Em cada uma,
os 3 testes de test_skills_progressive.py e TestSkillReuse passaram. O
leitor e o bootstrap leram 16 Skills e os 5 templates, glossário e
instruções de teste. Na primeira, o build desktop real incluiu a árvore
de Skills byte a byte, incluindo os anexos. O checkout principal de
trabalho do Studio permaneceu limpo.

Para repetir no diretório de ensaio, com as pastas das Skills ausentes:
scripts/bootstrap_studio_library.ps1 -StudioRoot CAMINHO -ManifestPath
CAMINHO/studio-skills.json -PythonExe PYTHON_COM_HUB. O script prepara a
biblioteca a partir dos arquivos ao lado do manifesto. Se falhar depois
de iniciar a materialização, pode restar um subconjunto já verificado.
O carregamento da aplicação completa, a entrega autorizada do lote ao
mantenedor e a retirada das cópias do repositório continuam pendentes.

## Execução · lote do Studio, piloto Forge e histórico Model Lab

O bootstrap do Studio agora verifica e materializa o lote em preparação
separada antes de mover qualquer Skill para .agents/skills. Se a publicação
falhar durante a movimentação, tenta devolver as pastas já movidas à
preparação. Na falha, informa o caminho dos arquivos de diagnóstico.
O teste trocou o treeSha256 da última Skill, mantendo o pacote intacto.
O materializador recusou a árvore divergente e .agents/skills ficou
ausente. A nova tentativa com o manifesto íntegro materializou 16 Skills.

No Forge 2.0, a Skill de desenvolvimento encontrada no snapshot examinado
foi recriada num host isolado a partir do pacote privado, usando o perfil
lia-forge. git hash-object --no-filters confirmou igualdade com o blob
original. A CLI consumiu o pacote sem criar a raiz de dados do Hub. Os
artefatos e a evidência de licença ficaram no workspace local. A auditoria
do Forge identifica a Skill como instrução de desenvolvimento, sem um leitor
da biblioteca no runtime do app. Ainda falta validar a adoção no host de
desenvolvimento e o procedimento de corte com o mantenedor. O checkout
do Forge 2.0 em main ficou limpo.

O Lia-Research em 33074e280cb557ac23537eac9a6883a0b89d0283, arquivo
data/inventory/lia-all-files.tsv.gz, registra 9 SKILL.md por branch de
Model Lab em 6 branches históricas, incluindo main e arena/skills-model-lab.
Essa contagem é histórica. Não substitui um checkout auditável, e a
API do repositório continua indisponível nesta sessão.

## Execução · Lia-Project no registro central

O inventário de referência foi gerado da árvore Git
9778ffb83611eecfd2fecdd8ba8b046b344b2ad3 (arena/7fa837f0-lia-project).
São 22 caminhos sob .agents e 29 sob airi. Cada registro recebeu um ID
alocado, a revisão, o caminho/alias de origem, o blob Git e os candidatos
a anexos. O gerador conserva os IDs de caminhos conhecidos quando recebe
o inventário anterior. Mudança de caminho precisa de revisão de alias.

A simulação retornou zero achados e não gravou recibo. O recebimento
efetivo pelo CLI do Hub gravou o recibo rec-3ad852118a31329d e o estado
ficou com 51 identidades inventoried. A repetição gravou um recibo de
auditoria adicional sem nova identidade. Regenerar o manifesto com o
mesmo snapshot e o inventário anterior produziu SHA-256 idêntico.
A biblioteca e a quarentena de conteúdo ficaram vazias.

Arquivo local: J:/Lia/migration/agent-hub/project-9778ffb.
O gerador está em docs/operations/evidence/project-reference-inventory.py.
O recebimento é de metadados. Licenças e autorização por componente
continuam pendentes. O commit examinado não possui LICENSE na raiz.
Os caminhos sob airi preservam a classificação de upstream. As 51
cópias de origem ainda permanecem no Lia-Project.

## Execução · registro local unificado

O diretório local J:/Lia/migration/agent-hub/registry/hub recebeu os
inventários do Project, Studio e Forge 2.0 na mesma instância. A consulta
de estado confirmou 68 identidades inventoried: 51, 16 e 1, respectivamente.
Os três recebimentos retornaram zero achados. Os manifestos e recibos
ficaram em J:/Lia/migration/agent-hub/registry.

Para Studio e Forge, packaged-skill-inventory.py conferiu o SHA-256 do
pacote, a árvore verificada, o manifesto v1 e o vínculo entre procedência
e revisão da oficina. Preservou os 17 IDs da oficina, os caminhos Git,
a atribuição disponível e a referência à evidência de licença. Repetir
a geração para o mesmo manifesto manteve o arquivo byte a byte.

Esse registro local reúne metadados. A biblioteca e a quarentena de
payload ficaram vazias. Os pacotes continuam nos lotes privados e as
bases de edição ainda ficam separadas. As cópias versionadas nos
projetos seguem pendentes de corte e o Model Lab continua sem uma
árvore atual acessível.
