# Contrato de inventário de capacidades Lia v1

**Proposta técnica.** Documento UTF-8 com objeto JSON. `inventoryVersion: 1`
identifica o intercâmbio proposto. `schemaVersion: 1` da biblioteca e do índice,
o manifesto complementar `.lia/capability.json` e `formatVersion` do pacote
mantêm seus significados. A primeira implementação deve ler o v1 existente
por adaptador, sem regravar o catálogo ou alterar o índice dos hosts.

## Envelope

| Campo | Regra |
| --- | --- |
| `inventoryVersion` | Inteiro obrigatório, igual a 1. Versão desconhecida é rejeitada sem gravação |
| `inventoryId` | Identidade opaca do feed, estável por emissor |
| `revision` | Identificador opaco obrigatório, único por feed. Mesmo valor e digest diferente é conflito |
| `generatedAt` | Instante RFC 3339 com fuso |
| `issuer` | Objeto obrigatório com `project`, `repository` e `maintainer`. O projeto emissor pode diferir da origem |
| `records` | Lista de registros distintos por par `id` e `revisionId`. Lista vazia é válida |
| `evidence` | Lista opcional de evidências. Cada `id` é único no envelope e referências precisam resolver |
| `complete` | Booleano obrigatório que identifica declaração de snapshot completo. Omissões nunca apagam registros |

`issuer.project` usa `lia-project`, `lia-forge`, `lia-studio`,
`lia-model-lab` ou `lia-agent-hub`. Lia Desktop é o host do projeto
`lia-project`. Origem aceita também `external` ou `null` quando indeterminada.
Campos desconhecidos exigem revisão de contrato e são preservados no
inventário recebido, após sanitização, sem efeito na admissão ou nos estados.
O importador futuro deve rejeitar chaves JSON duplicadas e aplicar limites de
bytes, registros e referências antes de processar o documento.

## Registro

| Campo | Regra |
| --- | --- |
| `id` | ID estável do registro central. Usar `urn:lia:cap:<uuid>` atribuído pelo Hub ou reservado para origem autorizada. Não derivar de nome, localização, versão ou hash |
| `revisionId`, `version` | Identificador imutável dentro de `id` e versão declarada pelo mantenedor ou `null`. Preservar sufixos e a grafia original. Aplicar comparação semântica só quando o esquema for declarado |
| `kind`, `name`, `description` | Tipo controlado, nome não vazio e descrição textual. Descrição desconhecida usa `null` |
| `origins` | Lista não vazia de `project`, `repository`, `path`, `branch`, `commit`, `author`, `maintainer` e `evidenceIds`. Campos desconhecidos usam `null`. Repositório remoto sanitizado e caminho relativo POSIX verificável. Commit completo fixa a revisão quando conhecido. Branch é metadado e pode mover |
| `aliases` | Lista de pares `scheme` e `value`, com escopo `authority`. IDs locais v1, namespaces upstream e nomes anteriores permanecem rastreáveis |
| `license` | `declared` com expressão declarada ou `null`, `components` com escopos de código, documentação, assets, pesos e serviço, e `redistribution` com `status` e `authorizationIds`. Cada autorização referencia versão, hash, escopo, canal, titular ou decisão e obrigações |
| `integrity` | Lista de objetos `algorithm`, `scope`, `digest`, `evidenceIds`. Para SHA-256, digest são 64 caracteres hexadecimais. Escopo distingue arquivo recebido, conteúdo, árvore, pacote e descritor. Ausência usa lista vazia. Hash não prova autoria |
| `dependencies` | Lista de relações com `targetId` ou referência externa sanitizada, restrição de versão, obrigatoriedade e fase de uso. Declarar sistema de versões. Referências não resolvidas viram lacunas |
| `environment` | Objeto ou `null`. Quando conhecidos, registrar OS, arquitetura, runtime, versão, hardware e requisitos de conta. Segredos entram apenas como nomes ou referências ao cofre do host |
| `offers` | Lista de referências a tools e recursos, com identificador estável e revisão quando conhecidos. MCP tool aponta ao servidor e ao nome protocolar. Lista vazia significa nenhum item declarado |
| `compatibility` | Lista por host, perfil e versão. Para cada alvo, registrar requisitos, evidência e resultado `unknown`, `declared`, `contract-checked`, `host-verified` ou `incompatible` |
| `details` | Objeto específico do tipo ou `null`, conforme tabela abaixo. Metadados são passivos |
| `observations` | Lista de fatos com `state`, `actor`, `at`, `evidenceIds` e escopo de revisão, hash, host ou canal conforme o estado. Observação importada é declaração até revisão da autoridade competente |
| `history` | Lista append-only de eventos com ID, ação, data, autor, escopo e referências. Retificações referenciam o evento anterior |

Listas vazias registram ausência de informação fornecida. `null` distingue
desconhecido de vazio, falso ou zero. Campos de identificação, revisão, tipo,
origens e escopo do inventário são obrigatórios. Os demais campos da tabela
devem aparecer nos registros normalizados pelo futuro leitor.

### Tipos

| `kind` | Informação específica quando disponível |
| --- | --- |
| `agent-skill` | Ponto de entrada `SKILL.md`, namespace, ferramentas permitidas declaradas e compatibilidade Agent Skills |
| `mcp-server` | Transporte, versão de protocolo/contrato, endpoint ou referência ao launcher, tools, recursos, riscos por regra, egress, nomes de credenciais e suporte offline declarado |
| `mcp-tool` | ID e revisão do servidor, nome no protocolo, esquema de entrada/saída, escopo e efeito declarado |
| `cli` | Nome, executável ou artefato referenciado, interface e plataformas |
| `plugin` | API do host e faixa de versões suportada |
| `package` | Ecossistema, coordenada e versão de biblioteca ou pacote |
| `agent-profile` | Perfil, host, ferramentas e modelo referenciados, política declarada |
| `model-provider` | Subtipo `model` ou `provider`, revisões, API/backend e evidências de avaliação |
| `workflow` | Formato, engine, entradas, saídas e dependências declaradas |
| `resource` | Tipo de recurso ou dependência, origem e versão de artefato quando aplicável |

Uma dependência é uma relação em qualquer tipo. Se possui identidade própria,
pode ser catalogada separadamente com seu tipo real. Uma tool MCP pode ter
registro próprio sem se tornar instalável fora do servidor associado.

## Evidência e estados

Evidência tem `id`, `kind`, `locator`, `recordedAt`, `recordedBy` e
`subject`. O sujeito identifica o registro e revisão e, conforme a prova,
hash, host, perfil, versão ou canal. IDs LR-* e DR-* são referências à pesquisa
ou decisão, não substitutos de comprovação. Histórico e observações são
multidimensionais. Cada linha abaixo tem sua própria autoridade e escopo.

| Estado | Condição mínima | Autoridade |
| --- | --- | --- |
| `inventoried` · Inventariado | Recebimento com revisão e origem declarada | Origem e Hub |
| `cataloged` · Catalogado | Metadados admitidos; pode ser apenas referência | Hub |
| `imported` · Importado | Payload admitido e gravado no Hub; quarentena válida | Hub |
| `validated` · Validado | Resultado de método identificado com revisão, escopo e resultado. Validação estrutural não evidencia operação | Hub ou avaliador identificado |
| `approved-for-distribution` · Aprovado para distribuição | Parecer humano sobre versão, hash, escopo, canal, autorização e obrigações | Responsável autorizado |
| `available-for-configuration` · Disponível para configuração | Artefato revisável gerado para um perfil declarado. Requisitos pendentes aparecem separadamente | Hub |
| `configured` · Configurado no host | Evidência do operador para a revisão, host, instância ou ambiente e data | Host |
| `operational` · Operacional | Evidência de operação no host com data, revisão, ambiente e escopo do teste | Host |
| `blocked` · Bloqueado | Ação específica, motivo, escopo, responsável e condição de resolução | Autoridade da ação |

Um estado não promove o próximo. Mudança de revisão ou hash exige nova
evidência ou vínculo explícito verificável. A revogação não apaga histórico.
Ausência, expiração ou divergência de evidência deixa a projeção como
desconhecida ou bloqueada conforme a ação. `active`, trust, licença declarada
e `connectivityVerified: false` do modelo v1 não são aprovação, configuração
nem evidência operacional.

Estado de instalação e configuração pertence ao host. Uma observação do host
pode incluir `installation` (`unknown`, `not-installed`, `installed`,
`not-applicable`) e `configuration` (`unknown`, `not-configured`,
`configured`, `disabled`, `not-applicable`). Esses campos usam a mesma
chave de host, perfil, ambiente e revisão da evidência. Material de
configuração produzido pelo Hub não preenche nenhum deles.

## Compatibilidade com v1

- Vincular `Capability.id` como alias local; um mapa persistente liga esse ID
  ao registro. Preservar `versionOf` para linhagem e o pacote/índice v1 para
  consumo. Não adicionar novos valores ao enum do índice v1.
- Mapear `agent-skill` e `mcp-server` diretamente. `cli-tool` mapeia para
  `cli`, `provider-model` para `model-provider`. `api-service`, `framework`,
  `template`, `reference` e `unknown` preservam seu tipo legado como alias
  de classificação. Classificar em `resource` somente se a origem sustentar
  a classificação. Caso contrário, ficam na fila de recebimento com tipo pendente e fora dos registros normalizados.
- Reusar `Source`, `License`, requisitos, hashes, histórico e metadados
  laterais. Um caminho absoluto v1 é referência local, nunca origem a publicar.
  Namespace, autoria, origem, commit e licença do catálogo Stitch podem estar
  no bloco de proveniência. Divergência entre campos fica explícita.
- `quarantined` pode comprovar importação local quando acompanhado de
  evidência. `active` ou `superseded` serve para o ciclo da biblioteca.
  O inventário não publica quarentena nem infere aprovação de redistribuição.
- Sanitizar antes de gravar ou reportar. Recusar valores de credencial,
  URLs com usuário/senha ou tokens, segredos em valores de cabeçalho,
  comandos gerados a partir de conteúdo de origem e cópias de configurações
  privadas. Tratar caminho, URL e conteúdo textual como dados.

## Exemplo e convenções de intercâmbio

O [exemplo sintético](../examples/central-capability-inventory.v1.json) é uma
declaração de workflow com evidências vazias. Um emissor de inventário não
precisa fabricar uma observação para tornar um registro legível.

`license.redistribution.status` aceita `unknown`, `pending`, `allowed` e
`denied`. `allowed` exige autorização comprovada e seu escopo é a interseção
dos documentos aplicáveis ao componente e à ação. `evidenceIds` e
`authorizationIds` referenciam a lista `evidence`. Referências entre
capacidades usam `id` e podem fixar `revisionId`. Uma dependência externa
sem ID central mantém seu identificador próprio. Compatibilidade declarada
sem teste permanece `declared`, como no exemplo.
