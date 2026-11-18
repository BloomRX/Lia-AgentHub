# Recebimento de inventários de capacidades (v1)

**Implementação do P0 de [Prontidão do registro central](CAPABILITY-REGISTRY-READINESS.md).**
Este documento descreve o que o intake faz, o que ele recusa e — o mais
importante — o que ele **não** faz.

O contrato é o [CAPABILITY-INVENTORY-CONTRACT.md](../architecture/CAPABILITY-INVENTORY-CONTRACT.md);
as regras de convivência entre registros estão em
[CENTRAL-CAPABILITY-GOVERNANCE.md](../architecture/CENTRAL-CAPABILITY-GOVERNANCE.md).

## Fronteira

O intake recebe **metadados e referências**. Ele não é um instalador, não é um
executor, não é um cliente de rede e não é uma autorização.

| O intake faz | O intake NÃO faz |
| --- | --- |
| Lê um arquivo JSON e valida o envelope | Executar Skills, MCPs, CLIs, scripts, plugins ou código importado |
| Preserva proveniência, licença declarada, referências, hashes e evidências | Instalar dependências de terceiros |
| Classifica contra o que já foi recebido | Importar payload executável |
| Grava recibo com origem, momento e digest | Conectar serviço externo ou pedir credencial |
| Retém conflito e downgrade em quarentena real | Copiar segredo ou `.env` |
| Mantém o registro como `inventoried` | Aprovar licença, redistribuição, confiança ou operação |
| Aponta erro ao registro que o causou | Converter `planned`/`proposed`/`partial`/`unknown` em `implemented` |
| | Contornar D-05, D-16 ou D-18, ou alterar a política de confiança humana |

`inventoried` é o **teto** do intake. Nenhum estado posterior do contrato —
`validated`, `approved-for-distribution`, `available-for-configuration`,
`configured`, `operational` — é alcançável por aqui. Presença no acervo não é
prova de instalação, configuração ou operação.

## Uso

### Interface

A aba **Inventário** tem dois botões: **Simular** (dry-run) e **Receber**.
A simulação não grava nada. O recebimento grava recibo e mostra a lista de
já recebidos, com detalhe do recibo por item.

### CLI

```bash
# simular — NÃO grava nada (padrão)
python -m lia_agenthub.cli inventory preview inventario.json

# receber — grava recibo e índice
python -m lia_agenthub.cli inventory receive inventario.json --commit

# consultas
python -m lia_agenthub.cli inventory state
python -m lia_agenthub.cli inventory receipts
python -m lia_agenthub.cli inventory receipt rec-0123456789abcdef
```

`--json` em qualquer subcomando devolve o objeto completo, para automação.

Códigos de saída: `0` recebido ou simulação válida, `1` recusado (erro
bloqueante), `2` uso incorreto ou arquivo ilegível.

Sem `--commit` nada é gravado. Isso não é ergonomia: um comando errado não
pode deixar recibo nem índice.

### Rotas HTTP

| Rota | Método | Efeito |
| --- | --- | --- |
| `/api/inventory/preview` | POST | Simula; não grava |
| `/api/inventory/receive` | POST | Efetiva; grava recibo |
| `/api/inventory` | GET | Identidades conhecidas (teto `inventoried`) |
| `/api/inventory/receipts` | GET | Lista de recibos |
| `/api/inventory/receipt?id=` | GET | Um recibo |

## O que é validado

### Envelope

- `inventoryVersion` deve ser `1`. Versão desconhecida é **rejeitada sem
  gravação** — ignorar o campo seria aceitar contrato que o leitor não sabe ler.
- `inventoryId`, `revision` obrigatórios e não vazios; `generatedAt` em RFC 3339
  **com fuso**; `issuer` com `project`, `repository` e `maintainer`.
- `issuer.project` limitado aos projetos conhecidos (ou `external`).
  `lia-model-lab` é aceito e marcado como **inativo**: a referência histórica
  fica preservada, mas o relatório diz que não é fonte ativa nesta fase.
- `complete` obrigatório e booleano. Omissão (`false`) **nunca apaga** registro.
- `records` e `evidence` são listas; par (`id`, `revisionId`) distinto no envelope.
- Limites aplicados **antes** de processar: 8 MB, 5 000 registros, 20 000
  evidências, 2 000 referências por registro.
- Chaves JSON duplicadas são recusadas. `json.loads` padrão manteria a última
  em silêncio — num inventário, isso é ou erro de geração ou tentativa de
  confundir o leitor.
- `NaN` e `Infinity` são recusados: não são JSON.

### Registro

- `id` é `urn:lia:cap:<uuid>` ou identificador com escopo declarado. O prefixo
  `urn:lia:cap:` é reservado: com ele, só UUID passa. ID derivado de nome,
  local, versão ou hash é rejeitado — o contrato proíbe.
- `revisionId` imutável dentro do `id`; `kind` do enum do contrato; `name` não
  vazio; `origins` lista **não vazia** com caminho relativo POSIX.
  Caminho absoluto é recusado: publicá-lo vazaria a árvore de diretórios do emissor.
- `license.redistribution.status` ∈ {`unknown`, `pending`, `allowed`, `denied`}.
  `allowed` **exige** `authorizationIds` que resolvam para evidência do envelope;
  sem isso, é rejeitado — é exatamente a promoção automática que o contrato proíbe.
- `integrity` com `sha256` exige 64 hexadecimais minúsculos.
- `compatibility[].result` ∈ {`unknown`, `declared`, `contract-checked`,
  `host-verified`, `incompatible`}. `host-verified` é declaração do emissor,
  não verificação do Hub.
- Toda `evidenceIds` precisa resolver: `origins`, `integrity`, `compatibility`
  e `authorizationIds`.

### Tipos v1 sem correspondência

`cli-tool` → `cli` e `provider-model` → `model-provider` são mapeados, com o
valor original preservado como alias de classificação.

`api-service`, `framework`, `template`, `reference` e `unknown` **não têm**
`kind` no contrato. Ficam como **tipo pendente**, fora dos registros
normalizados, com achado de revisão. O intake não inventa `kind` para eles.

### Campos desconhecidos

Preservados integralmente, sem efeito na admissão. Um campo que parece comando
(`installCommand`, `postinstall`, `entrypoint`) é **dado**, nunca instrução.

### Segredos

O documento inteiro é recusado quando encontra credencial, em qualquer campo:
chave de API, token, chave privada, credencial AWS, cabeçalho de autorização,
URL com `user:senha`. A varredura olha **valores** e **nomes de chave**, e
ignora referência a cofre (`vault://`, `secret://`), placeholder (`${VAR}`) e
valor vazio — sem isso o intake seria inútil para quem usa cofre.

## Classificação

Cada registro recebido é classificado contra o que já foi recebido, na ordem
de gravidade:

| Situação | Classe | Admissão |
| --- | --- | --- |
| id desconhecido | `new` | admitido |
| mesmo id + revisão + digest | `exact-duplicate` | admitido (idempotente) |
| mesmo id + revisão, digest diferente | `identity-conflict` | **retido em quarentena** |
| mesmo id, revisão diferente | `update` | admitido; anterior preservada |
| mesma identidade, versão declarada menor | `downgrade` | **retido em quarentena** |
| mesmo digest, id diferente | `same-content` | admitido, com relação registrada |
| mesmo nome, conteúdo diferente | `overlap` | admitido, registros separados |
| tipo v1 sem `kind` | `pending-type` | **não normalizado** |

Downgrade só é afirmado quando **os dois lados** usam `N.N.N` numérico. Sem
esquema reconhecível, a grafia é preservada e a classe fica `update` — o
intake não arrisca dizer que é downgrade.

Conflito de identidade **não sobrescreve**. O relato que já estava comprovado
continua com o digest original, e o novo vai para quarentena. Sobrescrever
perderia um dos dois relatos, e o Hub não decide qual é verdadeiro.

## Conflito de feed

`revision` é único por feed. Se o mesmo `inventoryId` publicar a mesma
`revision` com digest diferente, o documento é rejeitado com a explicação de
que o emissor precisa publicar uma revisão nova. Mesma revisão com mesmo
digest é idempotente e passa.

## Quarentena

Quarentena é **estado real**, não etiqueta de tela. Registros não admitidos
vão para `Quarentena/Inventarios/<receiptId>/retencao.json`, fora do acervo,
com o motivo e a classificação. O payload não é copiado: só o metadado.

O registro em quarentena **não** entra no índice de identidade — quando o
mesmo par (`id`, `revisão`) for decidido, ele será recebido de novo.

## Persistência

Em `Comum/Capacidades/Inventarios/`, compartilhado entre os projetos:

```
recibos/<receiptId>.json        prova: origem, momento, digest, achados, classificação
recebidos/<sha256(inventoryId)>.jsonl   feed append-only por emissor
estado.json                     índice de id → revisões conhecidas
```

O recibo é imutável por convenção e por código: gravar o mesmo `receiptId`
de novo é recusado. Recibo é prova; reescrever apagaria o que foi de fato visto.

Um `estado.json` ilegível é **erro explícito**. Tratá-lo como vazio faria o
próximo inventário "atualizar" tudo e perder o histórico.

## Exemplos

Arquivos sintéticos em [`docs/examples/intake/`](../examples/intake/):

| Arquivo | Demonstra |
| --- | --- |
| `demo-lia-studio.valid.json` | Envelope válido, dois registros, evidência resolvida |
| `demo-lia-forge.api-service.json` | Tipo v1 sem `kind` → fila de tipo pendente |
| `demo-conflict-same-revision.json` | Mesma revisão com conteúdo divergente → quarentena |

Todos usam `example.invalid` e autoria fictícia. Nenhum tem payload.

## Testes

| Arquivo | Cobre |
| --- | --- |
| `tests/unit/test_inventory_domain.py` | Leitura, validação e classificação (domínio puro) |
| `tests/integration/test_inventory_intake.py` | Fluxo, dry-run, recibos, quarentena, CLI, rotas |
| `tests/security/test_inventory_boundary.py` | Prova por dublê: não executa, não instala, não conecta |

Os testes de fronteira substituem `subprocess`, `socket` e afins por funções
que **falham quando chamadas**. Se o intake executar qualquer coisa, o teste
diz qual chamada foi feita.

## Limites conhecidos

- O intake lê **um** arquivo. Referência dentro do inventário não vira leitura
  de outro arquivo.
- Não há interface para **decidir** o que está em quarentena. Isso é do P1
  (fluxo de decisão humana por registro), e D-16 continua aberta.
- Comparação de downgrade cobre `N.N.N`. Outros esquemas são preservados sem
  julgamento de ordem.
- O leitor não valida o conteúdo semântico de `dependencies`, `environment` e
  `offers`; preserva e relaciona.
- A suíte local não mede host instalado. Testes verdes não são homologação.
