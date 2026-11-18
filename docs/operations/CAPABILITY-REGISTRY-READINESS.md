# Prontidão do registro central de capacidades

**Auditoria de contrato · 18 de novembro de 2026.** Base do Hub
`202badae6888987c6fed4d82f80680d23c169a8a`, branch
`arena/a92004be-lia-agenthub`. O catálogo central e o contrato de inventário
v1 são propostas. O piloto usa o mesmo modelo de pacotes e índice já publicado.

## Matriz de compatibilidade

A matriz descreve alvos de projeto e o alcance da evidência atual.
`Contrato` significa que um teste do Hub exercitou o intercâmbio. `Declarado`
indica perfil ou uso candidato, sujeito à confirmação do mantenedor.
`Referência` significa metadados para consulta. `Fora do papel` indica
que aquele produto não assume a função de host do tipo citado. Nenhuma célula
atesta instalação, configuração ou operação.

| Capacidade | Desktop / Project | Forge | Studio | Model Lab | Agent Hub |
| --- | --- | --- | --- | --- | --- |
| Agent Skill | Contrato de pacote e verificação | Contrato de busca e licença | Contrato de pré-validação estrutural | Declarado para oficina de avaliação | Importação, validação e pacote v1 |
| Servidor MCP | Declarado, depende de transporte, autenticação e versão do host | Declarado para ferramentas de produção | Declarado para editor e projetos | Referência para avaliações | Descritor v1 e configuração revisável em formatos suportados |
| Ferramenta MCP | Declarado via servidor | Declarado via servidor | Declarado via servidor | Referência via servidor | Metadados subordinados ao descritor, sem registro próprio ainda |
| CLI | Declarado | Declarado para pipeline | Declarado para editor e automação | Declarado para avaliação | Referência. A CLI do Hub administra o próprio acervo |
| Plugin | Declarado conforme API do Desktop | Declarado conforme API de pipeline ou DCC | Declarado conforme API de editor | Referência | Referência |
| Biblioteca ou pacote | Declarado conforme dependências do host | Declarado conforme dependências do pipeline | Declarado conforme dependências da engine | Declarado conforme ambiente de avaliação | Referência. `.lia-capability` é formato de troca |
| Agente ou perfil | Declarado para perfis do Desktop | Declarado para tarefas de assets | Declarado para sessões de projeto | Declarado para experimentos | Referência. Execução fora do papel |
| Modelo ou provedor | Declarado conforme matriz LR-MODEL-005 | Declarado para backends de geração | Referência conforme integração adotada | Declarado para avaliação por backend e hardware | Referência, preservando autoria e escopo da medição |
| Workflow | Declarado para fluxos do Desktop | Declarado para pipelines de assets | Declarado para editor e gameplay | Declarado para pipelines de avaliação | Referência |
| Recurso ou dependência | Referência declarada | Referência declarada | Referência declarada | Referência declarada | Referência com relação explícita |

O contrato Model Lab atualmente testado preserva extensões dos registros v1
no roundtrip. É prova de leitura e escrita, sem afirmar consumo de modelos.
O contrato continua incluindo Lia Go. Esse host mantém seu perfil no
[contrato de distribuição existente](../architecture/CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md).
As células declaradas dependem de inventário, versão, OS, arquitetura, runtime,
formatos, dependências, licença, transporte e permissões pertinentes. A prova de
compatibilidade deve fixar esses campos na revisão validada.

## Lacunas do Agent Hub

| Lacuna | Evidência atual | Critério de fechamento |
| --- | --- | --- |
| Identidade central e inventário por origem | `Capability.id` é ID local derivado do conteúdo; `versionOf` registra linhagem | Feed versionado com IDs persistentes, mapa de aliases e histórico de revisões, sem alterar IDs v1 |
| Tipos e relações | Skill e servidor MCP têm fluxos próprios. O enum v1 é parcial e tools são itens do descritor do servidor | Importar metadados tipados e guardar relações servidor/tool, dependência e compartilhamento sem criar Skills artificiais |
| Procedência de múltiplas origens | `Source` preserva upstream, commit e extensões. Stitch usa proveniência lateral | Preservar origem, escopo e autoria por declaração e revisão. Comparar ou marcar desconhecido quando faltar prova |
| Licença por componente | Licenças declaradas e base de redistribuição são separadas. `License` v1 contempla código, conteúdo e pesos | Registrar documento, titular, escopo, canal, revisão e obrigações por componente, com decisão humana e revogação |
| Compatibilidade e dependências | `requirements` pode estar ausente. O índice v1 entrega capacidades ativas e metadados de seleção | Detectar incompatibilidades, restrições de versão e dependências não resolvidas; separar o que foi declarado do que foi verificado |
| Estado por host | `trust`, `lifecycle` e `connectivityVerified: false` têm escopos limitados | Registrar evidência de configuração e operação por host, ambiente, versão e data, sem computar avanço automático |
| Relatórios, duplicatas e conflitos | Busca, hash, auditoria de proveniência e diff por versão existem | Produzir relatórios por projeto sem consolidar origens, direitos ou versões automaticamente |
| Distribuição do aplicativo | Relatório Windows registra tráfego residual WebView2 e ausência de ambiente limpo | Encaminhar critérios de distribuição pelos processos existentes; a governança do catálogo não resolve homologação do binário |

Os gaps de pesquisa carregam a revisão em que foram constatados. Por exemplo,
a ausência de catálogo de servidores em LR-MCP-002 já não descreve a branch
do Hub: ela contém descritores e oficina MCP. Continuam abertos o inventário
multi-origem, o status por host e a identidade central proposta. A evidência
de licença AIRI/Alethe e o catálogo de modelos são referências de pesquisa,
com seus próprios limites e sem revalidação nesta rodada.

## Implementação priorizada

| Prioridade | Entrega | Critério para avançar |
| --- | --- | --- |
| P0 ✅ | Congelar amostras v1 e implementar leitor de inventário em modo somente leitura. Validar envelopes, limites, origem, referências e saneamento local | **Entregue** em [INVENTORY-INTAKE.md](INVENTORY-INTAKE.md). Fixture v1 legível sem achado, erros apontam o registro (`records[0]`), dry-run não grava, executa ou conecta — provado por dublê em `tests/security/test_inventory_boundary.py` |
| P0 ✅ | Persistir identidade central, revisões imutáveis, aliases e recibos de inventário | **Entregue**. Reimportação idempotente (`exact-duplicate`), divergência de hash vira conflito de identidade retido em quarentena, nenhum ID ou hash v1 é reescrito. Recibo imutável e feed append-only |
| P1 | Implementar tipos, relações, matriz por alvo e evidência de licença | Servidor/tool, workflow, pacote, perfil e modelos conservam tipo e proveniência; revisões bloqueadas não aparecem como autorizadas |
| P1 | Piloto de metadados com um snapshot voluntário por projeto. Gerar relatório de cobertura, dependências e conflitos | Cada projeto revisa os próprios resultados. Casos de duplicação ficam rastreáveis sem perda de autoria |
| P2 | Projetar saídas aprovadas para o índice e pacotes v1, complementar com configurações revisáveis e confirmar com os mantenedores | Leitor independente continua aceitando as saídas v1. Quarentena e segredos ficam de fora. O host pode usar os arquivos com Hub fechado |
| P2 | Receber evidência sanitizada de configuração e operação emitida pelos hosts | Evidência vinculada à revisão e ao alvo. Ausência, revogação ou expiração não contam como operação |

D-05 e D-18 limitam todos os estágios. D-16 e o escopo jurídico de
redistribuição continuam sob decisão humana. A equipe de cada host valida
seu consumidor. O Hub pode rodar testes de contrato com arquivos sintéticos.
Telas e fluxos visuais permanecem sob o Stitch.

## Verificação de compatibilidade executada

- `python docs/operations/evidence/inventory-compatibility.py` verificou o
  exemplo de intercâmbio e releu os **17 registros v1 existentes**, sendo
  16 Skills e 1 servidor MCP. Todos fizeram roundtrip campo a campo.
  Os IDs, os hashes e a quarentena foram preservados. Todos têm referência
  upstream lateral e nenhum tem commit preenchido dentro de `Capability.source`.
  A leitura manteve a distinção entre licença e redistribuição.
- `python -m pytest -o addopts= --strict-markers -q -r s tests/integration/test_host_contracts.py tests/integration/test_stitch_integration.py tests/integration/test_independent_reader.py tests/integration/test_mcp_workshop.py tests/security/test_network_boundary.py`
  retornou **126 aprovados**. Exercitou pacote, índice, descritor, preservação
  de metadados e fronteiras do Hub com as fixtures existentes.
- A suíte completa no Windows retornou **673 aprovados e 1 skip**. O skip
  corresponde à criação de symlink sem privilégio nesta sessão.
- `python docs/research/verify-consistency.py` retornou **44/44**.
- A suíte local não mede hosts instalados. O contrato já tem leitor e
  recebimento implementados (P0 acima); os consumidores da nova projeção e o
  piloto de metadados por projeto continuam como entregas posteriores (P1).

## Intake de inventários — o que passou a existir

O leitor somente-leitura e a persistência de identidade/recibos do P0 estão
implementados em `src/lia_agenthub/domain/inventory.py` (domínio puro) e
`src/lia_agenthub/adapters/inventory_intake.py` (arquivo e recibos), expostos
na CLI (`inventory preview|receive|state|receipts|receipt`), na interface
(aba **Inventário**) e em cinco rotas HTTP.

O que isso **não** muda:

- `inventoried` continua sendo o teto. Nenhum registro avança de estado.
- D-05, D-16 e D-18 seguem abertas. O intake não escolhe licença global nem
  aprova redistribuição.
- Lia Model Lab continua suspenso: é aceito para preservar histórico e é
  marcado como inativo no relatório.
- O Hub **não** fica pronto para distribuição pública por causa desta entrega.
  Homologação Windows e a decisão de licença continuam sendo os gates reais.

Ver [INVENTORY-INTAKE.md](INVENTORY-INTAKE.md) para a fronteira completa.
