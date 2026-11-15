# Registro de decisões — Lia Agent Hub

**Status inicial:** as questões abaixo estão abertas para pesquisa e proposta.  
**Regra:** Arena pode pesquisar e recomendar; decisões de produto, risco, publicação e autorização de implementação exigem aceite humano.

## Direções já estabelecidas no briefing

| Tema | Direção atual | Estado |
|---|---|---|
| Nome | Lia Agent Hub | Nome adotado para o repositório e produto de trabalho; marca final pode ser validada depois |
| Posicionamento | Produto independente e transversal | Direção proposta |
| Domínios | Não limitar a Game Development | Direção proposta |
| Local-first | Funções essenciais sem nuvem obrigatória | Princípio definido |
| Providers | Neutralidade entre opções locais, gratuitas e pagas | Princípio definido |
| Separação de responsabilidades | Hub cria/curadoria/distribui; hosts autorizam e executam | Princípio definido |
| Autonomia dos hosts | Studio, Forge e agentes externos não dependem de runtime central do Hub | Princípio definido |
| Segurança | Conteúdo externo não confiável por padrão; controle humano | Princípio definido |
| Implementação | Não autorizada durante a Fase 0 | Decisão atual |

## Decisões abertas do briefing original

| ID | Questão | Pode ser pesquisada pelo Arena? | Exige decisão humana antes da implementação? |
|---|---|---:|---:|
| D-01 | Confirmar o nome final e posicionamento da marca | Sim | Sim, se houver mudança |
| D-02 | Escopo do catálogo inicial: apenas Skills/MCPs ou catálogo amplo desde o começo | Sim | Sim |
| D-03 | Formatos canônicos de Skills e metadados, preservando formatos abertos | Sim | Sim |
| D-04 | Modelo para dependências entre Skills, MCPs, CLIs e APIs | Sim | Sim |
| D-05 | Estratégia reproduzível de teste e isolamento em Windows e Linux | Sim | Sim |
| D-06 | Armazenamento local, versionamento, backup e exportação | Sim | Sim |
| D-07 | Como Studio e Forge receberão atualizações: importação, pacote local, API ou alternativa | Sim | Sim |
| D-08 | Necessidade de SDK/CLI para aplicações e agentes externos | Sim | Sim |
| D-09 | Quais recursos serão API local e quais serão arquivos/pacotes | Sim | Sim |
| D-10 | Como impedir mudanças silenciosas de comportamento após atualização | Sim | Sim |
| D-11 | Como preservar licenças e avisos de terceiros em pacotes distribuídos | Sim | Sim |
| D-12 | Quando catálogo remoto, comunidade ou publicação pública fariam sentido | Sim | Sim |
| D-13 | Funcionalidades essenciais do MVP versus funcionalidades adiáveis | Sim | Sim |
| D-14 | Tecnologia da aplicação (Electron, web local ou outra) | Sim | Sim |

## Questões adicionais a esclarecer na pesquisa

| ID | Questão | Observação |
|---|---|---|
| D-15 | Quem é o usuário primário do MVP: criador individual, equipe, desenvolvedor de agentes ou todos? | Propor personas e priorização |
| D-16 | O Hub será inicialmente ferramenta pessoal, produto para distribuição ou projeto open-source? | Não presumir política de publicação/licença |
| D-17 | Quais sistemas operacionais precisam ser suportados no primeiro MVP? | Windows é relevante, mas a matriz final precisa ser aprovada |
| D-18 | Qual nível de risco o produto pode aceitar ao testar MCPs e código de terceiros? | A pesquisa deve apresentar limites técnicos; a política final é humana |
| D-19 | Quais dados podem sair da máquina em recursos de IA assistida ou catálogo remoto? | Local-first não resolve por si só todos os casos de egress |
| D-20 | Como tratar recursos que não podem ser redistribuídos, mas podem ser referenciados/configurados? | Separar metadados, código, conteúdo, pesos e licenças |

## Como atualizar este registro

Para cada decisão:
1. anexar evidências e fontes;
2. listar opções reais e consequências;
3. registrar recomendação do Arena separadamente da decisão humana;
4. registrar decisão aprovada, responsável e data somente após aceite;
5. não transformar recomendação ou silêncio em aprovação.

Estados permitidos: `OPEN`, `RESEARCHING`, `RECOMMENDED`, `APPROVED`, `REJECTED`, `DEFERRED`.

Nenhuma decisão aberta bloqueia o início da Fase 0. Questões de produto/risco que exigem aceite devem ser resolvidas antes da implementação que delas dependa.
