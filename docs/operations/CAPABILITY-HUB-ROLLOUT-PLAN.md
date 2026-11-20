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

## Execução · oficina central e reempacotamento

A instância local em J:/Lia/migration/agent-hub/registry/hub passou a
conter também a oficina consolidada. consolidate-skill-workshops.py
copiou as bases locais de ensaio de Studio e Forge como dados, recusou
IDs duplicados, verificou procedência e SHA-256 de cada revisão contra
seu manifesto fixado e publicou a base em um destino novo. As bases
originais continuam disponíveis para recuperação.

O comando python -m lia_agenthub --home CAMINHO skill list lista
rascunhos, nomes, procedência e a última revisão. Os 17 IDs da oficina
resolvem no catálogo local de 68 identidades. Os 51 registros do
Project seguem por referência. Reempacotei a Skill de bootstrap do
Studio a partir da oficina unificada. O pacote foi materializado em
pasta vazia com 8 arquivos e o digest de árvore
60fd56bd587a53bdb6983bb46bf16854b9a73dc8bb4e114db685bd7612457882.
A identidade, a procedência e os anexos atravessaram a consolidação.
O novo ZIP tem seu próprio manifesto de consumo.

O ensaio usa uma raiz local explícita. Os projetos ainda precisam
consumir de forma verificável as revisões selecionadas antes do
corte das cópias versionadas.

Uma tentativa com hash de árvore alterado foi recusada antes da
publicação da base. A suíte Windows registrou 839 aprovados e um skip
de symlink.

## Execução · derivação autorizada na oficina

O comando python -m lia_agenthub skill fork ID REVISAO --copy-evidence
ARQUIVO cria um rascunho com identidade própria. O Hub exige um documento
local de evidência de cópia e registra seu SHA-256 sem guardar o documento.
A origem do derivado conserva o ID, a revisão e a árvore da Skill original
e sua atribuição. Editar ou empacotar o derivado conserva essa cadeia.
O documento fornecido continua sujeito à revisão humana. A operação não
marca a licença como redistribuível.

O teste do fluxo recusou evidência vazia, publicou a derivação com anexo,
empacotou e conferiu a atribuição, os hashes e a restrição de redistribuição.

Olhando a árvore do Project em 9778ffb, há LICENSE e UPSTREAM.md junto à
Skill Alethe e um LICENSE sob airi. A raiz do Project continua sem LICENSE.
O achado separa os documentos que precisam de revisão. A evidência de
licença do repositório vendorizado tem escopo a confirmar por componente,
como mostra LR-LIC-003.

## Execução · dependências fixadas e evidência Alethe

No consumo de Skills, pack --profile PERFIL --requires LOCK vincula
ID, revisão e hash da árvore de uma dependência. Pode ser repetido.
Materialize --dependency LOCK DIRETORIO recebe explicitamente os
manifestos e diretórios locais das dependências e verifica a cadeia
transitiva, o perfil e os hashes antes de materializar o destino.
Dependência ausente, alvo divergente, repetição e ciclo são recusados.
O teste materializou uma cadeia de três Skills, recusou a ausência
da folha e a alteração do arquivo dessa folha e passou após restaurá-lo.
A CLI valida o conjunto local. Cada integração de host ainda precisa
escolher onde prepara suas dependências e em que ordem as materializa.

No Project, o recibo local rec-e5e8eaf29e6f9960 adicionou uma revisão de
evidência à identidade existente da Alethe. O catálogo continuou com
68 identidades. O registro distingue MIT declarado para software e
documentação dos cinco ativos de marca com escopo ainda sem verificação.
Referências e hashes dos documentos LICENSE e UPSTREAM.md foram
preservados. O UPSTREAM declara upstream v19 e patches locais. A
Alethe segue por referência enquanto o pacote completo exigir revisão
dos componentes. Nenhuma cópia atribuída à Alethe foi admitida na oficina.

## Execução · Lia Studio como consumidor do build

Na branch de desenvolvimento do Studio, e570426fecbe42428bd84b6cde844cb089f00bac
adicionou -SkillsDirectory ao build desktop. O operador agora pode selecionar
uma biblioteca previamente materializada pelo Hub. O caminho empacotado
continua .agents/skills. O checkout convencional continua utilizável sem
o parâmetro.

Ensaiada a receita publicada com PyInstaller a partir de uma árvore isolada
do Studio em b099c4a, com a pasta versionada .agents/skills retirada dessa
cópia, e a biblioteca externa das 16 Skills fornecida por -SkillsDirectory.
O LiaStudio.exe foi gerado. A entrada externa e .agents/skills no pacote
conferiram byte a byte, incluindo os anexos. O build não recriou a pasta
de Skills na origem do Studio. A janela do executável ficou fora do ensaio.

Verify_alpha.py --part 10 passou nas verificações de Skills, shell
desktop simulada e UI. A parte como um todo falhou no backup HTTP por
CRLF/LF. Test_integrated_flow.py reproduziu a mesma falha em uma exportação
limpa de b099c4a sem a alteração de build. O corte das fontes versionadas
continua pendente. O perfil de consumo do build já está disponível na
branch de desenvolvimento.

## Execução · regressão Windows e consumo do Studio empacotado

A correção 38a48d9 na branch do Studio mantém os bytes originais no
backup e grava o arquivo aplicado com os mesmos bytes UTF-8 usados
no hash da proposta. O teste integrado agora compara também o hash
do arquivo aplicado. Verify_alpha.py --part 10 passou no Windows
depois da correção.

Recompilei o executável com a biblioteca externa de 16 Skills,
conferi os arquivos empacotados byte a byte e iniciei LiaStudio.exe
com diretório temporário para os projetos e PATH restrito ao Windows.
A API local do processo listou 16 Skills e abriu
lia-game-project-bootstrap como builtin. A captura do identificador
da janela não foi possível em duas execuções em modo oculto. Encerrei
os processos de teste. O resultado comprova consumo de Skills pelo
executável, mas o fechamento pela janela fica sem validação.

## Execução · patch de corte do Studio para revisão

O patch local J:/Lia/migration/agent-hub/studio-cut-38a48d9/studio-agent-hub-cut.patch
tem SHA-256 AEE952B03B43D6B64623E32EDAD020D95259C0127EA0C120B928E7950AE22AB4
e base 38a48d9e7cfd526a22ffacb60bf322c3a15847d9. Retira do Git 16 SKILL.md
e 7 anexos, preserva o README do diretório, ignora cópias materializadas
e adiciona o bootstrap e as travas de SHA-256 do manifesto do lote e dos
16 manifestos individuais. Os arquivos de conteúdo continuam disponíveis
no lote privado já preparado. A aplicação do patch foi conferida contra
o checkout atual e executada somente na exportação isolada.

Com o patch aplicado e os diretórios gerados ausentes, prepare_hub_skills.ps1
recriou 16 Skills. Passaram 3 testes do leitor e TestSkillReuse. O build
padrão do Studio gerou LiaStudio.exe e incluiu a árvore materializada byte
a byte. Antes de testar a reconstrução, a reversão do patch restaurou
as 16 fontes versionadas e os 3 testes do leitor passaram novamente.
O patch está pronto para a revisão de corte prevista no plano. O Studio
ainda precisa dispor do lote em um local aprovado para os consumidores
do repositório após o corte.

Rechecagem das branches remotas confirmou 0 SKILL.md em Lia Go
(be218893a5da3094417fe162675f013302500e41) e Lia-Research
(33074e280cb557ac23537eac9a6883a0b89d0283). Nessas revisões não há
arquivos de Skill a retirar. O Model Lab voltou a retornar HTTP 404.

## Execução · evidências por componente do Project

A leitura direta conferiu o Git blob e registrou SHA-256 de cada um dos
50 SKILL.md ainda sem revisão individual de evidência. Alethe conserva
a revisão própria. A auditoria encontrou 6 declarações MIT no frontmatter
atual: uma em .agents (lia-eventa-ipc) e cinco no acervo vendorizado. Nos
outros 44 registros, o escopo permanece desconhecido. Vinte e um nomes
corresponderam ao histórico de LR-LIC-003. Correspondência por nome
registra a pista histórica sem atribuir o conteúdo atual ao mesmo autor.

O recebimento no Hub foi aceito com zero achados no recibo
rec-c91aa29963609a42. A consulta manteve 68 identidades, incluindo 51
do Project com duas revisões de metadados. Os hashes e a evidência
local ficam no diretório registry. As declarações MIT não foram
registradas como autorizações de redistribuição. O comando auditou
metadados sem copiar nem executar as Skills.

## Execução · CLI Windows para os hosts

O build produz LiaAgentHub.exe para a janela e LiaAgentHubCli.exe com
console e saída utilizável em scripts. Ambos são onefile. A CLI usa
o mesmo despacho do código-fonte e funciona com um diretório de dados
explícito. Scripts de bootstrap do Studio aceitam -HubCli como alternativa
a -PythonExe. Os pacotes e manifestos ainda são fornecidos localmente.

O build com testes completos passou e o verificador de arquivo listou os
módulos de oficina e consumo nos dois binários. LiaAgentHub.exe tem
12 640 635 bytes, SHA-256
BE44839CB102F5B7F8071E1EC0029D40F2924D65C5D022BC1C2D4D96FD6D3A55.
LiaAgentHubCli.exe tem 9 583 233 bytes, SHA-256
BD13647B669C482E0A900C822B73FF4CB85764A28A7272150456B87B9A974693.
O smoke externo removeu Python do PATH do processo e executou uma cópia
da CLI fora do checkout. Leu 17 Skills da oficina e 68 registros do
catálogo e materializou as 16 Skills do Studio pelo parâmetro -HubCli.
Esta máquina ainda tem Python instalado. A homologação em Windows limpo
e os bloqueios de distribuição pública continuam separados.

## Execução · patch de corte do Forge 2.0 para revisão

O patch foi preparado em diretório local de migração. Ele retira do Git a
Skill de desenvolvimento da revisão examinada e acrescenta o manifesto
fixado, o comando de preparação via LiaAgentHubCli.exe e as instruções de
reversão. O conteúdo materializado fica no caminho que os hosts de
desenvolvimento usam e é ignorado pelo Git.

Verifiquei a aplicação do patch contra a árvore original. No snapshot
isolado, a CLI empacotada recriou o arquivo e git hash-object --no-filters
confirmou o mesmo blob. Após afastar o diretório gerado, a reversão
restaurou a fonte original com o mesmo blob novamente. O Forge 2.0 tem
somente main no remoto. A árvore real permaneceu limpa e o patch, o
manifesto e o pacote privado permanecem no workspace.

## Execução · revogação de revisões

Skill revoke ID REVISAO --reason MOTIVO registra a revogação local com
data e hash de árvore. Consultar a revisão e seu histórico continua
possível. A revisão revogada fica indisponível para empacotar, derivar ou
restaurar. Um novo pedido de revogação conserva o primeiro registro.

Skill revocations exporta a lista sem os motivos internos. Materialize
--revocations ARQUIVO verifica a revisão principal e suas dependências.
Os scripts de bootstrap do Studio aceitam -Revocations para aplicar a
mesma lista antes de expor a biblioteca. O ensaio recusou a última
revisão de um lote de 16 Skills quando ela constava da lista de teste,
sem expor o diretório ativo. A oficina central de migração não foi
alterada por esse teste.

O host precisa receber uma lista atual de uma fonte confiável.
A verificação offline não consulta rede e não invalida automaticamente
cópias que o host já materializou. O operador decide quando trocar
a referência ativa.

### Build Windows com revogação

Em `458d5f8`, `powershell -NoProfile -ExecutionPolicy Bypass -File
scripts/build_windows.ps1` executou a suíte completa e gerou os dois
binários. O log local está em
`J:/Lia/migration/agent-hub/windows-build-458d5f8.log`.

| Artefato | SHA-256 |
| --- | --- |
| LiaAgentHub.exe | `1c1d9b1b548cbf1423da36e42d13ece3593738c4ac6d06fe52f06dd8ae376545` |
| LiaAgentHubCli.exe | `65ad25a297b54d4784b7cdea5316cc6e082b434c443fde74225cc66c6cf40325` |

No diretório isolado
`J:/Lia/migration/agent-hub/smoke-458d5f8-56b8d84e5f7944fe98199cdca755f105`,
com o PATH restrito ao Windows, `LiaAgentHub.exe --version` saiu com
código 0. `LiaAgentHubCli.exe skill materialize` materializou a revisão
1 de `lia-task-handoff` e retornou o hash de árvore do manifesto. A mesma
operação com `--revocations revocations.json` retornou código 1 e recusou
a revisão antes de criar o destino. A cópia de controle permaneceu intacta.
A lista foi criada só para o teste. Ambos os binários retornaram
`NotSigned` em `Get-AuthenticodeSignature`. A janela nativa e uma
instalação Windows sem Python permanecem fora deste ensaio.

### Janela nativa no binário recompilado

Em um segundo ensaio fora do checkout, `LiaAgentHub.exe --home PASTA
--verbose` abriu a janela `Lia Agent Hub` (PID 19808, handle 329556).
O WebView2 157.0.4341.60 iniciou sob o processo da janela (PID 18656).
A linha de comando do runtime mostrou `--disable-background-networking`,
`--disable-component-update` e `--disable-sync`.
O log HTTP registrou respostas 200 para o HTML, CSS, JavaScript,
`/api/items?lifecycle=active` e `/api/quarantine` em loopback.
`CloseMainWindow()` encerrou o executável com código 0 e os PIDs
observados da árvore deixaram de existir.

A captura de processos e logs está em
`J:/Lia/migration/agent-hub/windows-native-458d5f8.log`.
O ensaio confirma a inicialização nativa e a comunicação HTTP inicial.
A avaliação visual, a medição de egress D-09 e o Windows sem Python
instalado seguem com seus critérios próprios.

### Forge legado no inventário central

O checkout local `J:/Lia/Lia-Forge-Workspace/windows-validation`, na
branch `codex/windows-stability-fixes` e no commit
`f94d8b1bb5119a16c03b03cb595d94ccf0a32c4d`, contém um
`SKILL.md` versionado em `.agents/skills/lia-brand-check/`.
`git ls-tree` identificou o blob `2a9be442e47466c832604f283f141394bc652f5c`.
O caminho coincide com o do Forge 2.0, que tem blob
`74e3d8e85981f2ee0e9f80123d2a9d81df8fa43f`.

O manifesto local `J:/Lia/migration/agent-hub/registry/forge-legacy.inventory.json`
preserva o hash SHA-256 do arquivo e do documento de licença de origem.
`LiaAgentHubCli.exe inventory preview` classificou o registro como
`overlap`. `inventory receive --commit` gravou o recibo
`rec-161098d0d01684f4`, e `inventory state --json` confirmou 69
identidades. A revisão legada tem identidade própria por referência e
permanece com redistribuição pendente.

O remoto `BloomRX/Lia-Forge` retornou `Repository not found` para
`git ls-remote --heads origin`. Os dois checkouts do Forge permaneceram
limpos. O ensaio de corte do Forge 2.0 continua restrito à revisão para a
qual foi preparado.

### Atualização e reversão com a CLI empacotada

Em um diretório fora do checkout, com Python fora do PATH, o
`LiaAgentHubCli.exe` do build `458d5f8` criou e publicou uma Skill
sintética de perfil `lia-studio`. A sequência foi `create`, `publish`,
`pack --profile lia-studio`, `materialize`, `edit` e nova publicação.
Cada revisão teve seu próprio pacote e manifesto. O consumidor
materializou as revisões 1 e 2 em diretórios novos a partir dos arquivos
locais, sem criar a raiz de dados do Hub indicada no lado do host.

A reversão do consumidor reutilizou o manifesto e o pacote da revisão 1.
No lado da oficina, `restore ID 2 1` seguido de `publish ID 3` publicou a
revisão 3 com a mesma árvore da revisão 1. O SHA-256 de SKILL.md na
revisão 2 divergiu do inicial, e as duas formas de reversão reproduziram
o SHA-256 inicial. O histórico retornou `[3, 2, 1]`.

Manifestos e resultados estão em
`J:/Lia/migration/agent-hub/update-rollback-025eec71ed2b4c458269eb066c40d644/evidence.json`
e nos arquivos ao lado. O ensaio cobre a oficina e o contrato de consumo
na CLI. O corte e a regressão de cada repositório continuam sujeitos aos
critérios por host da seção 5.

### Lia-Project · pontos de integração antes do corte

A branch remota `arena/7fa837f0-lia-project` ainda aponta para
`9778ffb83611eecfd2fecdd8ba8b046b344b2ad3`. A leitura usou uma
clonagem bare isolada com `--single-branch --depth 1 --filter=blob:none`.
O gitdir do worktree local existente não estava disponível.
`git ls-tree -r`, `git show` e `git grep` na árvore fixada
confirmaram os pontos de integração abaixo.

| Consumidor | Dependência observada | Verificação no corte |
| --- | --- | --- |
| CI DevFlow | `.github/workflows/devflow-ci.yml` executa `tools/test_agent_skills.py`, cujo caminho é `.agents/skills`. Também exige nomes, orçamento de descoberta e referências ao catálogo e aos documentos | Preparar o conteúdo fixado antes do passo existente e executar a validação integral num checkout sem a cópia versionada |
| Testes da Alethe | `Tests/tools/alethe-budget.test.py` referencia `.agents/skills/alethe/scripts/orchestrate.py`. `Tests/tools/alethe-editor.browser.mjs` usa a mesma raiz de conteúdo | Preservar os caminhos de anexos para os fluxos existentes após aprovação por componente |
| Instruções do AIRI | `airi/AGENTS.md` referencia Skills relativas sob `airi/.agents/skills`. `airi/skills-lock.json` registra origem, caminho e hash de entradas de upstream | Preservar a resolução relativa e reconciliar cada pin do Hub com o registro de upstream antes de retirar cópias do AIRI |

`.agents/skills/lia-eventa-ipc` é candidata ao piloto por conter apenas
`SKILL.md` no Git e declarar MIT no frontmatter. A escolha depende de
confirmar a base de cópia e testar a descoberta no host de desenvolvimento.
As instruções sobre IPC se aplicam quando Eventa já está presente.
Esta análise não executou conteúdo de Skills nem alterou Lia-Project.

### Descoberta de repositórios adicionais

`gh repo list BloomRX --limit 100 --json name,isArchived` não retornou
um repositório acessível do Model Lab. O repositório `localqwen`
se apresenta como projeto pessoal. Sua descrição não estabelece
continuidade com o Model Lab.

Também conferi as branches acessíveis de dois repositórios adicionais
com nome Lia. `gh api repos/BloomRX/REPO/branches` fixou os commits e
`gh api repos/BloomRX/REPO/git/trees/SHA?recursive=1` retornou as árvores
completas. Nenhuma das quatro árvores continha `SKILL.md` versionado.

| Repositório | Branch | Commit |
| --- | --- | --- |
| LiaVoiceStudio | main | `354fd61677937415282f90cb5c0915130240511f` |
| LiaVoiceStudio | arena/e6163ffc-liavoicestudio | `01c97330f05aa063f0e4237995327b3d0a8025bc` |
| AgentToLia | main | `73d06e3231aecb939603e8d3aae73dd4601e9c4c` |
| AgentToLia | arena/362d85b1-agenttolia | `186d73c799aaf1c3b83fd703758255a931cf2e13` |

O resultado se limita às branches acessíveis e às Skills versionadas.
O inventário histórico do Research continua sendo a evidência para
Model Lab até que o checkout atual possa ser identificado e lido.

### Model Lab · entrada histórica por referência

Da árvore Git do Lia-Research em `33074e280cb557ac23537eac9a6883a0b89d0283`,
li `data/inventory/lia-all-files.tsv.gz` por `git show`. As 54 linhas
relevantes preservam nove caminhos distintos em seis branches, com os
SHAs abreviados e tamanhos registrados no snapshot. O inventário
`J:/Lia/migration/agent-hub/registry/model-lab-research.inventory.json`
guarda um ID por caminho, as seis origens e o vínculo ao snapshot
auditável. A tabela não contém hashes ou conteúdo das Skills.

`LiaAgentHubCli.exe inventory preview` aceitou as nove referências.
`inventory receive --commit` gravou o recibo `rec-ae6d038ead0d7c46`.
O contrato emitiu `ISSUER_INACTIVE_PROJECT`, conforme previsto para o
Model Lab suspenso. `inventory state --json` confirmou 78 identidades
com teto `inventoried`, e `skill list` manteve 17 entradas na oficina.
As nove referências são históricas e mantêm redistribuição pendente.
A confirmação da árvore atual e qualquer piloto de consumo dependem
do acesso à origem.

### Studio · lote local para consumo

Preparei em
`J:/Lia/migration/agent-hub/studio-consumer-c8396c67631244e49bb7e605fea50bbb/bundle`
uma cópia local de 35 arquivos: manifesto do lote, 16 manifestos de
revisão, 16 pacotes, licença e avisos. A base SQLite e os arquivos
internos da oficina ficaram no lote original. Cada arquivo copiado
teve seu SHA-256 conferido contra a origem. O inventário de hashes
está no arquivo `bundle-hashes.json` ao lado.

Em uma raiz de teste com o leitor do Studio, executei
`scripts/bootstrap_studio_library.ps1 -StudioRoot PASTA -ManifestPath
bundle/studio-skills.json -HubCli CAMINHO` com a CLI do build
`458d5f8` e PATH restrito ao Windows. O bootstrap recriou as 16 Skills.
Os hashes dos arquivos materializados conferiram com a árvore do
ensaio de corte. Este lote está preparado localmente. A escolha do
canal para consumidores do Studio continua pendente antes do corte.

### Studio · ensaio de corte com a CLI Windows

Preparei uma variante do patch de corte em
`J:/Lia/migration/agent-hub/studio-cut-cli-38a48d9/studio-agent-hub-cut-cli.patch`,
SHA-256 `df25db517773f41b29145c2ee53f8e6878e7aac23513f1318b28e32717c1b021`.
A variante preserva a opção existente por Python e acrescenta
`-HubCli` e `-Revocations` ao script `desktop/prepare_hub_skills.ps1`.
O wrapper mantém a verificação dos hashes fixados no Studio.

Na exportação isolada de `38a48d9`, com as fontes antigas retiradas,
`desktop/prepare_hub_skills.ps1 -BundleDirectory LOTE -HubCheckout HUB
-HubCli EXE` reconstruiu os 16 `SKILL.md` usando o lote de consumo e
o PATH restrito ao Windows. `git apply --check` aceitou a variante
no checkout real, que permaneceu limpo. A opção de revogação no
wrapper é encaminhada ao bootstrap do Hub. O ensaio desta variante
exercitou o caminho de materialização com a CLI.

Em outra exportação da mesma base, apliquei a variante com `git apply`
e passei `-Revocations` com uma política de teste para `lia-task-handoff`
revisão 1. A CLI recusou essa revisão e zero `SKILL.md` foram expostos
no destino ativo. A preparação parcial ficou no diretório de diagnóstico
da exportação. Nenhuma revogação foi gravada na oficina.

`git apply --reverse` restaurou as 24 entradas de
`.agents/skills`, incluindo o README. `git hash-object --path` conferiu
os 24 blobs com `git ls-tree` da base. A comparação de bytes brutos
com a exportação original divergiu por causa da conversão de fins
de linha no Windows. O resultado verifica a restauração dos blobs
Git da base. Evidência em
`J:/Lia/migration/agent-hub/studio-cut-policy-11a3c5f5c5034315901c1b142c1a0ddd/evidence.json`.

### Studio · corte do piloto local aprovado

Com a aprovação do uso de `J:/Lia/migration/agent-hub/studio-4e10327`
no piloto, apliquei o corte na branch de desenvolvimento existente
`arena/01a0f4ab-lia-gamedev`. O commit local
`e3553a89bffba45f0c47a70caa8f3eb4352c8fb9` retira 16 Skills e sete
anexos do Git e fixa os manifestos de revisão. A CLI do Hub reconstruiu
as 16 Skills no destino ignorado pelo Git. A branch remota permanece
no baseline `38a48d9`, pois a aprovação se refere ao piloto local.

`verify_alpha.py --part 10` passou com `PYTHONUTF8=1`. A primeira
tentativa com saída redirecionada falhou ao imprimir uma seta em
CP1252. `desktop/build_windows.ps1` produziu `dist/LiaStudio/LiaStudio.exe`.
O SHA-256 dos 23 arquivos das Skills empacotadas conferiu com a
biblioteca materializada. Nesta rodada, a janela do novo build ficou
fora do ensaio. Os logs locais são `studio-pilot-regression-utf8.log`
e `studio-pilot-build.log` sob `J:/Lia/migration/agent-hub`.

O mantenedor informou que o Model Lab saiu de desenvolvimento.
Seu piloto de migração é **NOT APPLICABLE**. As nove referências
históricas permanecem no catálogo com o estado de projeto inativo.

### Studio · executável do piloto validado

Copiei a distribuição do commit local `e3553a8` para um diretório
fora do checkout, com `LIA_PROJECTS_DIR` isolado e PATH restrito
ao Windows. `LiaStudio.exe` (PID 22456) abriu a janela nativa
`Lia Studio` e iniciou o WebView2 filho (PID 18324).
A API em `127.0.0.1:52446` retornou 16 Skills em `GET /api/skills`
e o conteúdo de `lia-game-project-bootstrap` na consulta individual.
`CloseMainWindow()` encerrou o processo com código 0 e a porta deixou
de escutar. Evidência em
`J:/Lia/migration/agent-hub/studio-pilot-native-66f35ab83f1c4478a30e41d334ff497c/evidence.json`.
O ensaio verificou abertura, leitura pela API e encerramento.

### Forge 2.0 e Lia-Project · pilotos locais autorizados

- Forge 2.0: criei a branch local `codex/agent-hub-skills-pilot` em
  `J:/Lia/migration/agent-hub/forge-pilot`. O commit `0b0a9b6` retira
  a fonte versionada e fixa seu manifesto. `prepare_brand_skill.ps1`
  recriou a Skill com o blob original e o caminho derivado ficou
  ignorado pelo Git. O remoto só oferecia `main`, que ficou intacta.
- Lia-Project: confirmei 46 blobs do checkout local contra `9778ffb` e
  os sete testes do contrato de Skills passaram no baseline. Com a
  autorização de cópia privada, publiquei `lia-eventa-ipc` na oficina
  local (`9e5c3e96-7381-4590-99ab-a5a9d4eba543`, revisão 1), preservando
  a declaração MIT na fonte e o snapshot Git. O manifesto e o pacote
  em `J:/Lia/migration/agent-hub/project-eventa-pilot` materializaram
  bytes idênticos à fonte. O corte no checkout do Project e o teste de
  descoberta pelo host continuam pendentes.

O ensaio de corte do Lia-Project usou um worktree isolado de `9778ffb`.
Os sete testes de `tools/test_agent_skills.py` passaram antes da
mudança, depois de retirar a fonte do índice e materializar a revisão do
Hub no caminho esperado, e após restaurar o original com `git restore`.
`git hash-object --no-filters` confirmou o blob Git da cópia derivada.
A árvore isolada voltou a ficar limpa. O ensaio confirma o contrato de
descoberta por caminho e catálogo. O carregamento pelo Desktop e o
corte na branch publicada ainda precisam de validação.

A revisão `private-workshop-1` do registro já existente de
`lia-eventa-ipc` vincula o manifesto da oficina e os hashes de pacote
e árvore, preservando a origem e a redistribuição pendente. A CLI
verificou o pacote e a cópia materializada, classificou o inventário
como atualização e gravou o recibo `rec-6110c71429b8ebee`.
O catálogo manteve 78 identidades e a oficina passou a 18 entradas.
Manifesto local: `J:/Lia/migration/agent-hub/registry/project-eventa-private-pilot.inventory.json`.

A verificação de escopo do piloto Eventa usou controle negativo:
com `lia-eventa-ipc` temporariamente ausente na exportação isolada,
os sete testes ainda passaram. Eles verificam a integridade das Skills
presentes, mas não exigem a presença desta Skill. A identidade da
cópia derivada foi comprovada separadamente pelo blob Git.

A configuração fixada de empacotamento do launcher em
`airi/apps/lia-app/electron-builder.config.ts` lista `out/**`,
`package.json` e recursos explícitos do stage e licenças. A busca por
`.agents/skills`, `SKILL.md` e `lia-eventa-ipc` no código do checkout
local encontrou o validador de desenvolvimento, testes de Alethe e
o lock de upstream AIRI. A evidência disponível aponta Eventa como
Skill de desenvolvimento. O próximo teste de descoberta deve usar
esse host e exigir especificamente o nome fixado antes do corte.

Preparei o patch local `J:/Lia/migration/agent-hub/project-eventa-pilot/project-eventa-agent-hub-cut.patch`
(SHA-256 `1dc8ae385c3fb6037cedd0f6e9a4cc5bbbdc3264286cbb761838f32b3ebb6f7`).
No worktree isolado, o patch retira o SKILL.md do índice, fixa o lock,
ignora a cópia derivada e inclui `tools/prepare_eventa_skill.ps1`.
Com a fonte ausente, esse comando recriou o blob original. O Git ignorou
a cópia e os sete testes existentes passaram. A branch publicada do
Project conserva o baseline. O pacote e o patch são do piloto privado.

O host de desenvolvimento também passou no piloto. O Codex CLI
`0.164.0`, em app-server local via stdio e com diretório de configuração
isolado, retornou exatamente uma entrada habilitada para `lia-eventa-ipc`
em `skills/list`, apontando para o SKILL.md materializado no worktree.
Ao afastar a cópia derivada, a mesma consulta retornou zero entradas
com esse nome. O arquivo foi recolocado após o controle. A consulta
apenas enumerou metadados da Skill e não iniciou uma sessão de agente.
Evidência: `J:/Lia/migration/agent-hub/project-eventa-pilot/codex-discovery-evidence.json`.

O corte Eventa foi registrado na branch local existente
`arena/7fa837f0-lia-project` no commit `08bf697`. Após o commit,
afastei a cópia derivada e repeti o bootstrap. O checkout esparso
precisou incluir o novo script e o manifesto em seu filtro.
A rematerialização conferiu com o blob de `9778ffb`, os sete testes
passaram e a árvore ficou limpa. O remoto permanece em `9778ffb`.

No Forge 2.0, o Codex app-server local confirmou a descoberta de
`lia-brand-check` na branch `codex/agent-hub-skills-pilot` (`0b0a9b6`).
`skills/list` retornou exatamente uma entrada habilitada, no caminho
materializado pelo Hub. Afastar a cópia produziu zero entradas para
o mesmo nome. A cópia foi recolocada e a árvore ficou limpa.
O teste listou metadados sem invocar a Skill. Evidência:
`J:/Lia/migration/agent-hub/forge-pilot-discovery.json`.

### Estado dos cortes locais e publicação

O Codex app-server também listou as 16 Skills do Studio habilitadas
nos caminhos gerados pelo Hub no checkout `e3553a8`. A lista coincide
com o manifesto do lote. A consulta apenas leu metadados. Evidência:
`J:/Lia/migration/agent-hub/studio-pilot-codex-discovery.json`.

| Projeto | Corte local | Estado remoto verificado |
| --- | --- | --- |
| Studio | `e3553a8`, 16 Skills | Branch de desenvolvimento em `38a48d9` |
| Forge 2.0 | `0b0a9b6`, 1 Skill | Branch do piloto ainda local |
| Lia-Project | `08bf697`, 1 Skill | Branch de desenvolvimento em `9778ffb` |

As três árvores locais estavam limpas. Para publicar os cortes,
os consumidores e o CI precisam de acesso autorizado aos lotes.
As outras 50 Skills do Lia-Project continuam por referência até a
confirmação do escopo de cópia por componente.

### Canal privado local dos pilotos

Consolidei os artefatos de consumo em
`J:/Lia/migration/agent-hub/private-consumption-v1`. A pasta contém
41 arquivos de três perfis, com hashes de pacote conferidos contra
os manifestos. A CLI Windows recriou as 18 Skills a partir desse
canal, com Python fora do PATH e sem criar a base do Hub no host.
`hashes.json` registra o SHA-256 de cada arquivo.

Este é o canal escolhido para os pilotos locais. O GitHub do Hub é
público. A adoção pelos consumidores remotos e pela CI depende de
um canal privado que eles possam acessar e de autorização para os
componentes envolvidos. Os cinco registros MIT restantes no Project
estão sob AIRI. A declaração, sozinha, não encerra a revisão de
proveniência e escopo desses componentes.

### AIRI · comparação de proveniência das Skills MIT

Comparei cinco Skills com declaração MIT contra as árvores Git dos
upstreams indicados em `airi/skills-lock.json`. Para `eventa`, o blob
de SKILL.md e a árvore inteira coincidiram com `moeru-ai/eventa` em
`488d14d1aed6e291168b93df4d1d697766d36a34`. A API retornou LICENSE
com SPDX MIT nesse commit. Registrei o SHA-256 da licença, o hash da
árvore e a origem externa no registro existente. Recibo:
`rec-ff933f1d2e9de4e0`. A cópia e a distribuição continuam pendentes.
As outras quatro árvores diferiram das pontas consultadas. A revisão
de origem delas precisa localizar snapshots anteriores.
Evidência: `J:/Lia/migration/agent-hub/project-9778ffb/airi-mit-upstream-comparison.json`.

O histórico Git confirmou correspondência de árvore inteira para
`simple-english` em `AminBlg/SimpleEnglish@daea7ea` e para
`vue-best-practices` e `vue-testing-best-practices` em
`antfu/skills@c35a558`. A API reportou MIT nos dois commits.
O recibo `rec-57e97951d69f95f9` atualizou os três registros existentes
com os commits completos, os hashes das licenças e as origens.
Para `vueuse-functions`, os seis commits do histórico do caminho
não forneceram blob ou árvore idênticos. As quatro Skills seguem por
referência. Evidência: `J:/Lia/migration/agent-hub/project-9778ffb/airi-mit-upstream-history.json`.

### AIRI · pacotes privados com licença conferida

Em uma oficina isolada, publiquei e materializei `eventa`,
`simple-english`, `vue-best-practices` e
`vue-testing-best-practices`. A CLI Windows recriou os 43 arquivos
originais com os mesmos SHA-256. Cada lote guarda ao lado do pacote
a licença MIT do commit de origem, com hash no manifesto de procedência.
Evidência: `J:/Lia/migration/agent-hub/project-airi-private-v1/evidence.json`.

O ensaio encontrou uma falha em saída JSON redirecionada no Windows.
A CLI antiga não conseguia representar uma seta em CP1252.
A serialização passou a usar escapes JSON para Unicode. O teste de
regressão confirmou a leitura do texto original e o binário recompilado
concluiu o fluxo com as quatro Skills. A oficina central e o checkout
do Project ainda conservam o estado anterior para essas quatro entradas.

As quatro revisões AIRI entraram na oficina central. O consolidador
verificou 22 revisões contra os manifestos antes de trocar a base.
A base anterior ficou em `J:/Lia/migration/agent-hub/registry/skills-before-airi.sqlite3`.
O inventário `project-airi-private-workshop.inventory.json` atualizou
os quatro IDs de catálogo existentes com os pins da oficina e os
hashes de árvore e pacote. Recibo `rec-df9f5d6b20602e53`.
A consulta confirmou 78 identidades e 22 entradas de oficina.
O corte das quatro cópias no checkout do Project segue pendente.
