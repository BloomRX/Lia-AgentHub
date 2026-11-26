# Lia Agent Hub · contrato de execução supervisionada v1

O contrato permite ao Lia-Project solicitar uma operação de primeira parte do
Hub. Nesta versão, `skill.validate` faz validação estática do texto autorizado
de uma Skill e devolve contagens. A validação não interpreta as instruções do
texto como comandos. D-05 e D-18 continuam em aberto para Skills, MCPs, scripts
e outros artefatos externos executáveis. O catálogo segue disponível
independentemente da autorização para abrir tarefas.

## Transporte e autoridade

Use a CLI local existente com uma raiz de dados por instalação do operador.
O protocolo usa JSON no stdin e stdout. Cada chamada abre um processo e
termina após uma resposta. Descoberta, solicitação, cancelamento e consultas
partilham o estado entre processos via SQLite. O HTTP da janela do Hub é
interno à sua sessão. O CLI evita transformar aquele servidor de UI em
serviço externo ou misturar o token de sessão da janela com permissões de
tarefa. O índice de distribuição em arquivos continua sendo a fonte de
descoberta de artefatos importados.

O operador que controla a raiz inicializa a autoridade uma vez com
`execution init`. A resposta contém o `operatorToken`. As chamadas
`execution provision CONSUMER` e `execution grant CONSUMER --ttl SECONDS`
exigem esse token num objeto JSON no stdin. O token de consumidor emitido
por `provision` só permite as ações da interface de tarefas.
Cada grant vale para o consumidor identificado e para `skill.validate`,
pode abrir uma única solicitação e expira em até 3.600 segundos. O prazo
`expiresAt` usa segundos desde a época Unix. Mantenha os tokens fora
de `context`, logs e argumentos do processo. As respostas de tarefas e
a trilha de auditoria omitem tokens e identificadores de grants.

Proteja a raiz do operador com permissões do sistema operacional. O acesso
ao CLI de administração e ao arquivo SQLite deve ficar com a conta
autorizada. O isolamento por token é uma fronteira do protocolo entre
clientes cooperativos. Processos hostis com a mesma autoridade de acesso
ao sistema de arquivos estão fora desse modelo. Um consumidor que precisa
de isolamento desse tipo deve falar com um adaptador do operador sob
outra conta. A v1 não oferece um serviço exposto em rede.

## Chamadas

`lia-agenthub --home ROOT execution call` recebe, até o EOF, um objeto JSON
UTF-8 com `schemaVersion: 1`, `token` e `action`. O limite do envelope
é de 524.288 bytes, incluindo a serialização do JSON. Chaves duplicadas
são recusadas. Consulte `contextMaxBytes` na descoberta para o limite
do texto UTF-8 já decodificado. A resposta é um único
objeto JSON UTF-8 com `schemaVersion: 1` e `ok`. Em sucesso, leia
`result`. Em erro, leia `error.code` e trate `error.message` como texto
para diagnóstico. O [schema v1](../schemas/supervised-execution-v1.schema.json)
define o formato de intercâmbio.
A CLI retorna 0 para um envelope `ok: true` e 1 para um envelope
`ok: false`. Uma tarefa `failed` pode estar num envelope de sucesso:
ela corresponde a uma consulta ou transição aceita pelo transporte.

| Ação | Campos além do envelope | Uso |
| --- | --- | --- |
| `discover` | Nenhum | Lista as operações despacháveis pelo contrato e seus requisitos. A presença não concede autorização. |
| `submit` | `requestId`, `grantId`, `capability`, `context.text` | Registra a solicitação com uma chave de repetição por consumidor. Envie somente o texto autorizado que será validado. |
| `start` | `taskId` | Inicia a tarefa registrada mediante grant válido e aguarda a operação local. |
| `status` | `taskId` | Retorna o estado da tarefa e, quando disponível, seu resultado estruturado. |
| `events` | `taskId` | Lê o histórico de progresso da tarefa. O consumidor consulta novamente para acompanhar mudanças. |
| `cancel` | `taskId` | Solicita cancelamento de uma tarefa ainda não finalizada. Envie em outro processo se `start` ainda estiver em andamento. |
| `audit` | `taskId` | Lê a trilha de eventos da tarefa, sem texto recebido, tokens ou erros internos brutos. |

Ao repetir `submit`, reutilize `requestId` apenas para o mesmo pedido.
Uma repetição idêntica devolve a tarefa existente. Uma repetição que
altere o texto ou o grant resulta em `conflict`. Reutilizar um grant em
outro pedido resulta em `forbidden`.
Guarde `taskId`, não o contexto, para consultar ou cancelar a tarefa.
Um texto de Skill estruturalmente inválido é um resultado da operação de
validação. Uma falha ao executar a operação deve ser tratada separadamente.

## Estados, eventos e erros

`submit` cria a tarefa em `queued`. `start` revalida a autorização e
registra `running`. Os estados finais são `completed`, `failed` e
`cancelled`. `progress` é 0 enquanto pendente ou em execução, e 100
quando a tarefa termina. O valor 100 sozinho não implica êxito. Uma tarefa
`completed` traz `result.counts` para `error`, `warning`, `info` e
`review`. Use `counts.error` para distinguir um texto aprovado de um
texto com erros de validação.

Eventos e auditoria retornam a mesma sequência persistida por tarefa,
ordenada por `sequence`. `at` usa segundos desde a época Unix. Um
`code` pode indicar `grant-expired`, `execution-timeout`,
`execution-failed` ou `cancelled`. Estados sem erro têm `code: null`.
A auditoria v1 é um registro local de transições, sem proteção contra
adulteração por quem controla o SQLite.

O texto fica na raiz privada enquanto o pedido está na fila. A transição
para execução ou cancelamento limpa o texto do registro ativo. A próxima
chamada autenticada trata solicitações enfileiradas cujo grant expirou.
A execução tem prazo de até 30 segundos, limitado também pela validade
do grant. A conclusão do executor ou uma consulta à tarefa pode observar
o prazo excedido. A v1 não oferece eliminação certificada de cópias
de segurança, journaling do sistema de arquivos ou dumps do processo.

O cancelamento é uma transição persistida. Se vencer a corrida com a
conclusão, descarta resultados posteriores. O validador é síncrono:
o cancelamento não garante interrupção imediata do cálculo em memória.
Repetir `start` ou `cancel` numa tarefa finalizada devolve seu estado
final sem reexecutar nem reescrever a conclusão.

Erros na chamada aparecem no envelope, com `ok: false`.

| Código | Tratamento |
| --- | --- |
| `invalid-request` | Corrija envelope, versão ou contexto. |
| `unauthorized` | Verifique a credencial da interface usada. |
| `forbidden` | Solicite ao operador um grant válido e compatível. |
| `conflict` | Compare com o registro anterior antes de tentar novamente. |
| `not-found` | Verifique o ID no escopo do consumidor. Tarefas de outro consumidor também retornam este código. |
| `unavailable` | A operação ou o serviço local está indisponível. |

## Handoff para o Lia-Project

O Stage continua consultando o catálogo publicado para inspecionar pacotes.
Para delegar a validação, o adaptador do consumidor deve escolher
`skill.validate`, pedir autorização no host, selecionar apenas o texto
relevante, guardar o token no lado confiável do host e enviar a chamada pela
entrada padrão. A atividade do Stage pode correlacionar `taskId` com a
tarefa do produto. Resultados do Hub são dados. O Stage decide como
apresentar contagens, acompanhar eventos e permitir o cancelamento.
A memória pessoal, a personalidade, a identidade e as decisões de
permissão do Lia-Project permanecem sob autoridade do host.

### Exemplo local

Use PowerShell 7 e uma raiz nova em pasta privada. Substitua `lia-agenthub` pelo executável
da CLI quando estiver trabalhando com um build empacotado. Rode a
inicialização, o registro e a concessão como operador. Mantenha os tokens
em memória.

O [exemplo em Python](../examples/supervised_execution_demo.py) automatiza
o mesmo fluxo em uma raiz temporária e registra apenas respostas de tarefa.
Execute `python docs/examples/supervised_execution_demo.py` na raiz do
checkout com o pacote instalado, ou passe `--cli CAMINHO_DA_CLI`.

```powershell
$hubRoot = Join-Path ([IO.Path]::GetTempPath()) ("lia-execution-demo-" + [guid]::NewGuid())
$operator = lia-agenthub --home $hubRoot execution init | ConvertFrom-Json
if (!$operator.ok) { throw $operator.error.code }
$authorization = @{operatorToken = $operator.result.operatorToken} | ConvertTo-Json -Compress
$consumer = $authorization |
    lia-agenthub --home $hubRoot execution provision lia-project | ConvertFrom-Json
$grant = $authorization |
    lia-agenthub --home $hubRoot execution grant lia-project --ttl 300 | ConvertFrom-Json
if (!$consumer.ok) { throw $consumer.error.code }
if (!$grant.ok) { throw $grant.error.code }

function Invoke-HubExecution([hashtable]$payload) {
    $request = @{schemaVersion = 1; token = $consumer.result.token} + $payload
    $request | ConvertTo-Json -Compress -Depth 8 |
        lia-agenthub --home $hubRoot execution call | ConvertFrom-Json
}

Invoke-HubExecution @{action = 'discover'}
$request = Invoke-HubExecution @{
    action = 'submit'; requestId = [guid]::NewGuid().ToString()
    grantId = $grant.result.grantId; capability = 'skill.validate'
    context = @{text = "---`nname: example`ndescription: Example Skill`n---`n# Example"}
}
if (!$request.ok) { throw $request.error.code }
$taskId = $request.result.taskId
Invoke-HubExecution @{action = 'start'; taskId = $taskId}
Invoke-HubExecution @{action = 'status'; taskId = $taskId}
Invoke-HubExecution @{action = 'events'; taskId = $taskId}
Invoke-HubExecution @{action = 'audit'; taskId = $taskId}
```

O texto no exemplo é uma fixture. A operação executada é o validador real
do Hub, em memória e sem baixar dependências ou chamar um serviço sintético.

## Evidência de validação

No Windows, `scripts/build_windows.ps1` executou a suíte completa e
gerou os dois executáveis. A demonstração chamou uma cópia de
`LiaAgentHubCli.exe` fora do checkout. O mesmo ID de tarefa apareceu
na resposta final e na trilha `queued → running → completed`.
O resultado trouxe as quatro contagens do validador real. SHA-256 da
CLI usada: `bae46af66f702a9698a116fbc59ed205b60e908bc6d34159d4685abecafd7c81`.

A regressão cobre recusa de autorização e isolamento entre consumidores
pela CLI, cancelamento antes de iniciar, armazenamento indisponível e
repetição idempotente. Testes controlados de adaptador usam relógio
injetado para expiração, exceção injetada para falha interna e uma
barreira de sincronização para confirmar o descarte de resultado após
cancelamento em andamento. Esses três cenários usam fixtures. Nenhum
serviço externo nem artefato executável importado participou do ensaio.
