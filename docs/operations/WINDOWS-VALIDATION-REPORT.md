# Relatório de validação Windows do Lia Agent Hub

**15 de novembro de 2026 · Windows 11 Home x64, build 26200**

> **Adendo de 2026-11-15 — investigação de D-09.** Este relatório é a medição
> original e não foi alterado no conteúdo. A investigação posterior separou o
> que a medição já sustentava do que continuava indeterminado, e implementou o
> controle que faltava. **D-09 continua aberto**: o controle está implementado,
> a medição com o controle aplicado não foi feita. Ver
> `FUNCTIONAL-COMPLETION-REPORT.md` §4 para a análise completa e
> `tests/security/test_network_boundary.py` para a prova de que o **aplicativo**
> não abre conexão.

**MVP não validado no Windows pelos critérios da seção 6 do plano.** A aplicação e o executável abriram em WebView2, importaram uma Skill real de teste e encerraram corretamente. A validação de distribuição em uma máquina sem Python ficou bloqueada. Na execução local do executável houve conexões externas em processos filhos do WebView2.

## Git, ambiente e alterações

- Repositório `BloomRX/Lia-AgentHub`, branch `arena/a92004be-lia-agenthub`, árvore inicial limpa. HEAD de referência `7cec491a563de8a75abe56d5aad1b115fec9db44`.
- Commit de código do build: `42d39b7a163f7be7c0966004f47d3516eccb2046`. Este relatório fica no commit seguinte. O push usa apenas a branch autorizada.
- `git log origin/main -1 --oneline`: `34a27f4 Kit Marca Lia`. O remoto retornou `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` para `refs/heads/main`.
- `src/lia_agenthub/interface/server.py` desativa as opções herdadas de reuso do TCPServer. O Windows continua com `SO_EXCLUSIVEADDRUSE` e o caminho POSIX continua configurando `SO_REUSEADDR` explicitamente.
- `scripts/build_windows.ps1` resolve o executável Python por `sys.executable`, grava em UTF-8 com BOM para o Windows PowerShell e delega limpeza e sobrescrita ao PyInstaller sem apagar os diretórios inteiros.
- `docs/operations/WINDOWS-VALIDATION-REPORT.md` registra a execução, os limites e o artefato.
- Python 3.12.10 AMD64 e WebView2 157.0.4341.46 já presentes. Venv local criado com `py -3.12 -m venv .venv`. Instalados via pip o pacote em modo editável, Pytest 9.2.0, PyInstaller 6.22.3, pywebview 6.2.1, pythonnet 3.2.1 e dependências. Git 2.52.0.windows.1. O valor `pv` consultado em HKLM coincidiu com o retorno de `detect_webview2()`.

## Matriz com resultados reais

| ID | Estado | Evidência |
| --- | --- | --- |
| A-01 | PASS | `284 passed, 1 skipped`. Skip de criação de symlink, previsto pelo plano. |
| A-02 | PASS | `75 passed, 1 skipped`. Mesmo teste de symlink. |
| A-03 | PASS | `14 passed`, inclusive bind local e liberação da porta. |
| A-04 | PASS | `13 passed`, inclusive launcher e geração de fixtures. |
| A-05 | PASS | `44/44 PASS`. |
| A-06 | PASS | `nenhum segredo encontrado`, pelo script de validação em Git Bash. |
| M-01 | PASS | Janela nativa observada, com processo filho `msedgewebview2.exe`. |
| M-02 | BLOQUEADO | O runtime estava presente. O cenário de ausência requer outro ambiente ou alteração do registro de instalação. |
| M-03 | PASS | Interface renderizada com seis destinos de navegação e estados reais da Biblioteca, Importar e Quarentena. |
| M-04 | PASS | Importação pelo formulário retornou `skill-valida-c32ec27a` e a lista de Quarentena mostrou `skill-valida v1.0.0`. |
| M-05 | PASS | Fechamento pela janela encerrou o PID do servidor e liberou a porta. |
| M-06 | PASS | Processo filho WebView2 do teste terminou. |
| M-07 | PASS | Duas instâncias simultâneas escutaram em portas distintas, com tokens distintos. |
| M-08 | PASS | `--diagnostico` retornou caminhos Windows, recursos, logs e Python 3.12.10. Usei raiz temporária. |
| F-01 | PASS | Skill importada com licença MIT declarada. |
| F-02 | PASS | Skill importada com licença desconhecida. |
| F-03 | PASS | `containsScripts=true`. A busca recursiva no checkout e na pasta de evidências encontrou zero `PWNED.txt`. |
| F-04 | PASS | Frontmatter inválido recusado. |
| F-05 | PASS | Código `REFERENCE_MISSING` retornado. |
| F-06 | PASS | `requiresReview=true` para bidi em prosa. |
| F-07 | PASS | Bidi em código recusado. |
| F-08 | PASS | ZIP com caminho proibido recusado. |
| F-09 | PASS | ZIP aninhado recusado. |
| F-10 | PASS | CRC inválido recusado. |
| F-11 | PASS | Arquivo descompactado de 65 MB recusado. |
| F-12 | PASS | Pacote íntegro verificado e importado. |
| F-13 | PASS | O comando de verificação retornou `ok=false`, com divergência de hash no arquivo de licença da fixture. O fluxo separado de importação aceitou o item em quarentena. |
| F-14 | PASS | Documento avulso importado. |
| I-01 | PASS | Promoção criou o diretório do item na Biblioteca. |
| I-02 | PASS | Índice em `Comum\Capacidades\index.json` incluiu o ID promovido. |
| I-03 | PASS | Busca por nome retornou o item. |
| I-04 | PASS | Item promovido retornou após iniciar outro processo com a mesma raiz. |
| I-05 | PASS | Detalhes retornaram autor, versão, licença e confiança. Validação estrutural retornou 0 erros e 1 aviso. |
| I-06 | PASS | F-04 recusado sem nova entrada na quarentena. |
| I-07 | PASS | Exportação privada gerou o pacote. |
| I-08 | PASS | Pacote exportado retornou `ok=true` e `treeHashOk=true`. |
| I-09 | PASS | Cópia externa manteve somente o executável na pasta do programa e criou os dados sob `%USERPROFILE%\Lia` em perfil de teste. |
| I-10 | PASS | `ação.md` preservado no disco e no JSON. |
| D-01 | BLOQUEADO | Windows sem Python indisponível. A cópia local abriu sem Python no PATH do processo. |
| D-02 | BLOQUEADO | Ambiente de distribuição indisponível. Cópia executada fora do checkout e com cwd externo no host atual. |
| D-03 | BLOQUEADO | Ambiente de distribuição indisponível. WebView2 funcionou na cópia local. |
| D-04 | BLOQUEADO | Ambiente de distribuição indisponível. Biblioteca, Quarentena, Exportados e Coleções foram criados no perfil isolado local. |
| D-05 | BLOQUEADO | Ambiente de distribuição indisponível. Importação pela UI da cópia local criou `Quarentena 1`. |
| D-06 | BLOQUEADO | Ambiente de distribuição indisponível. Item apareceu na UI após fechar e reabrir a cópia local. |
| D-07 | BLOQUEADO | Ambiente de distribuição indisponível. Cópia local encerrou os processos e liberou a porta. |
| D-08 | BLOQUEADO | Execução formal em máquina limpa indisponível. Varredura local do executável e dos arquivos descomprimidos encontrou zero correspondências para os quatro padrões. |
| D-09 | BLOQUEADO | Ambiente de distribuição indisponível. O critério de zero egress **falhou no host atual**. A amostra viu três conexões TCP externas de processos WebView2 da árvore do Hub. |

## Comandos e evidência

- `python -m pytest -q` inicialmente registrou `WinError 10022` na configuração de `SO_REUSEADDR`. Após corrigir o bind, `python -m pytest -o addopts= --strict-markers -q -r s` registrou `284 passed, 1 skipped`. O build voltou a executar a suíte inteira após as alterações no script.
- `python -m pytest tests/security -q`, `python -m pytest tests/integration/test_windows_readiness.py -v` e `python -m pytest tests/integration/test_packaging.py -v` produziram os totais A-02 a A-04. `python docs/research/verify-consistency.py` e `bash scripts/validate.sh` produziram A-05 e A-06. O Git Bash usou o Python do venv.
- `python -m lia_agenthub --diagnostico`, `python -m lia_agenthub` e `python -m lia_agenthub --no-window` foram executados com raízes descartáveis. O roteiro HTTP obteve `403 / 200 / 403 / 403` para ausência de token, token válido, Host externo e Origin externo. O token permaneceu fora dos logs de evidência. A UI nativa foi observada e operada por captura da janela e árvore de acessibilidade.
- `python scripts/make_fixtures.py <pasta-temporária>` gerou 14 fixtures. Um cliente HTTP local as submeteu ao servidor real e checou as respostas, o estado no disco e a persistência. `dir /s /b PWNED.txt` no checkout e uma busca recursiva no diretório de testes não retornaram nenhum marcador.
- `powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1` inicialmente falhou com `CommandNotFoundException` para `py -3.14`. Após corrigir o detector, o script passou pelos seis estágios com testes habilitados. O processo do executável com `--version` retornou 0.
- `python -m PyInstaller.utils.cliutils.archive_viewer dist\LiaAgentHub.exe -r -b` listou Lia Agent Hub, recursos estáticos, Bottle e WebView2. A busca por PyQt, PySide, gtk e tkinter retornou zero. A varredura dos bytes brutos e das entradas descomprimidas de CArchive e PYZ retornou zero correspondências para os quatro padrões do plano.
- `Start-Process` iniciou uma cópia do binário de um diretório temporário contendo somente o executável, com perfil temporário, `PATH` restrito ao Windows e sem `PYTHONHOME` ou `PYTHONPATH`. O log confirmou `frozen=True`, servidor local, importação e encerramento. `Get-Process` e `Get-NetTCPConnection` verificaram o fechamento.
- `Get-NetTCPConnection -OwningProcess` foi amostrado na árvore do executável, incluindo processos WebView2. Foram observados três destinos externos estabelecidos, todos em processos WebView2 filhos. A repetição com a versão final registrou dois destinos externos em WebView2. A coleta mediu conexões e propriedade por PID. A finalidade do tráfego ficou indeterminada.

## Artefato e pendências

- `dist\LiaAgentHub.exe`, tamanho e SHA-256 registrados abaixo. `Get-AuthenticodeSignature`: `NotSigned`. O tamanho ficou abaixo dos 15–40 MB estimados no plano. A listagem e a execução confirmaram que os componentes necessários estavam presentes.
- **P0:** nenhum marcador de execução apareceu no cenário F-03. A primeira falha de arranque do servidor foi corrigida e verificada com execução nativa.
- **P1:** zero egress permanece aberto. A execução local observou conexões iniciadas por filhos WebView2. A garantia para a janela nativa requer isolamento comprovado ou uma decisão de produto quanto ao runtime. A validação formal também depende de Windows limpo e sem Python. Nenhuma VM Windows limpa foi encontrada e o executável do Windows Sandbox estava ausente neste host Home.
- **P2:** o comportamento do SmartScreen em um download real e a mensagem de fallback com WebView2 ausente ficaram sem evidência. A assinatura e o licenciamento dependem de decisão humana. A importação e a verificação de hash são fluxos separados no MVP. Um pacote com hash divergente entrou em quarentena e foi detectado pelo verificador, portanto a presença em quarentena não demonstra integridade.
- **P3:** código morto listado no plano ficou apenas inspecionado. O retry de escrita passou pelos testes existentes. Contenção causada por antivírus durante uso real não foi induzida.
- Diferenças frente às evidências Linux do plano: combinação de opções de socket rejeitada no Windows antes da correção, skip de symlink no host, detecção via registro, janela WebView2 e executável onefile executados no Windows. A comparação usa os resultados Linux registrados no plano.
- Logs locais: diretório `%TEMP%\LiaAgentHub-Windows-7cec491`, incluindo `A-01.log`, `A-01-after-bind.log`, `A-02.log` a `A-06.log`, `native.stderr.log`, `functional-final.log`, `build-before.log`, `build-final.log`, `contents.txt`, `scan-package.log` e os CSVs `standalone-tcp.csv` e `standalone-final-network.csv`.

**Tamanho final:** 11608725 bytes

**SHA-256 final:** `AA0B302AC1D8B68F6DB8F68577A8B6F4C4DB149F0BFA1AA08C6AE1CAD3E91785`

---

## Adendo — o que foi apurado sobre as conexões externas (2026-11-15)

O corpo deste relatório registra, corretamente, que a finalidade do tráfego
ficou indeterminada. A investigação posterior não mudou esse fato; separou o
que era atribuível a quê.

| Pergunta | Resposta | Como se sabe |
|---|---|---|
| As conexões eram do aplicativo? | **Não** | `tests/security/test_network_boundary.py` proíbe `socket.connect`, `connect_ex`, `create_connection` e `getaddrinfo` durante importação, promoção, validação, exportação, publicação de índice e diagnóstico. Tudo passa. O Hub não tem cliente HTTP |
| Eram do runtime do navegador? | **Sim** | A medição original atribuiu cada conexão a um PID, e os PIDs eram `msedgewebview2.exe` |
| Qual componente iniciava? | O Chromium embutido | A UI é estática, servida de `127.0.0.1`, com CSP `connect-src 'self'` |
| Dava para controlar? | **Parcialmente** | `aplicar_controle_de_rede()` define `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` antes de a janela abrir |
| O destino foi identificado? | **Não** | Nenhuma captura de pacote ou de SNI foi feita |

### Por que a variável de ambiente, e não a API do pywebview

O pywebview 6.2.1 **fixa** `AdditionalBrowserArguments = '--disable-features=ElasticOverscroll'`
em `webview/platforms/edgechromium.py` e não expõe parâmetro para acrescentar
argumentos em `create_window` nem em `start`. A documentação da Microsoft
(`CreateCoreWebView2EnvironmentWithOptions`) diz que a variável
`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` é **anexada** aos argumentos do host.
É o único caminho que não exige fork do pywebview.

### O que fica desligado, e o custo

Background networking, component update, domain reliability, sync, telemetria
(`MetricsReportingEnabled`), Safe Browsing, Translate, OptimizationHints e as
barras do Edge (`msWebOOUI`/`msPdfOOUI`).

**Custo declarado:** sem Safe Browsing, a janela não consulta listas de
reputação. O Hub só carrega a própria UI de `127.0.0.1` e não navega para fora —
logo o risco é baixo, mas é uma escolha registrada, não um efeito colateral
escondido.

### O que continua faltando para fechar D-09

Procedimento reproduzível, em ordem:

**Passo 1 — medir com o controle aplicado.**

```powershell
# com o Hub aberto (o controle é aplicado no boot, antes da janela)
$raiz = (Get-Process LiaAgentHub).Id
Get-NetTCPConnection -State Established |
  Where-Object { $_.RemoteAddress -notin @('127.0.0.1','::1','0.0.0.0','::') } |
  Select-Object LocalPort, RemoteAddress, RemotePort,
    @{n='Pid';e={$_.OwningProcess}},
    @{n='Nome';e={(Get-Process -Id $_.OwningProcess).ProcessName}}
```

**Passo 2 — comparar com a linha de base deste relatório:** 3 destinos
externos na primeira amostra, 2 na versão final, todos em `msedgewebview2.exe`.

**Passo 3 — se sobrar tráfego, identificar o destino em vez de supor.**
`--log-net-log` **é** um browser flag suportado do WebView2 (documentado em
*WebView2 browser flags*). O caminho sem alterar código é o mesmo mecanismo
que o Hub já usa:

```powershell
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = "--log-net-log=$env:USERPROFILE\Desktop
etlog.json --net-log-capture-mode=Everything"
# abrir o Hub, aguardar a janela, fechar
# netlog.json permite ver a URL/SNI de cada requisição
```

**Atenção:** o Hub **preserva** um valor já definido em
`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` em vez de sobrescrevê-lo (decisão
registrada em `platform_check.aplicar_controle_de_rede`). Definir a variável
manualmente **desativa o controle embutido** naquela execução — o que é
exatamente o que se quer ao medir a linha de base sem controle. Para medir
**com** controle, remova a variável e confie no que o Hub define.

**D-09 permanece BLOCKED até esse passo ser executado.** O critério de aceite
não foi alterado.

---

## Homologação Windows de 18 de novembro de 2026

O checkout limpo foi atualizado por fast-forward de `b4eb85f` para o HEAD
publicado do Arena, `b7df471abad3a939906a9c571e0f873f99e685bf`, na branch
`arena/a92004be-lia-agenthub`. Consultei o relatório de conclusão funcional, o
checklist e o adendo de rede acima. A execução usou Windows 11 Home x64 26200,
Python 3.12.10, PyInstaller 6.22.3, pywebview 6.2.1 e WebView2 157.0.4341.60.

| Critério | Estado | Evidência |
| --- | --- | --- |
| Suíte Windows | PASS | 673 aprovados e 1 skip. Novos testes cobrem dois casos de junction e falha imediata na criação de temporário. |
| Segurança e especificação de build | PASS | 108 aprovados e 1 skip. Consistência documental 44/44. |
| D-09 — argumentos no runtime | PASS | Linha de comando do WebView2 confirmou os argumentos. O build final também os aplicou automaticamente. |
| D-09 — zero egress | PARTIAL | O critério de zero tráfego externo falhou. As duas execuções registraram DNS sobre HTTPS externo. |
| M4 — junction NTFS | PASS | Recusada dentro da pasta e como entrada selecionada. A junction exercitou um reparse point real. |
| M4 — symlink NTFS | BLOCKED | A sessão não tinha privilégio de criação de symlink. O teste pulou. |
| M4 — demais tipos de reparse point | PARTIAL | A checagem usa o atributo de reparse point. A execução real cobriu junction. |
| M4 — caminhos em arquivo importado | PASS | Traversal, ZIP Slip, entradas absolutas e UNC, nomes reservados e colisões por case passaram nos testes. |
| M4 — diretórios protegidos | PASS | ACL NTFS negou leitura e escrita. O Hub retornou recusa explícita. Quarentena e destino foram conferidos após a operação. |
| Build e fluxos empacotados | PASS | Onefile x64, executado fora do checkout. Janela nativa, diagnóstico, importação, validação, quarentena, promoção, exportação, reimportação, persistência e encerramento. |
| Inspeção de pacote e logs | PASS | Zero correspondências nos padrões de credenciais do plano. |
| Windows limpo sem Python instalado | BLOCKED | Nenhum Windows limpo disponível. A cópia externa rodou com PATH restrito ao Windows. |
| Distribuição pública | BLOCKED | Egress residual, validação em Windows limpo e decisões humanas de distribuição. |

### D-09 — TCP e DNS antes e depois

O mesmo executável de `b7df471` rodou com perfis WebView2 novos e separados
por 25 segundos por condição. Em ambos os casos, defini
`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` no processo. A linha de base recebeu
`--log-net-log=<arquivo>`. A execução controlada recebeu a string integral de
`argumentos_windows_rede()` e o mesmo flag de captura, com outro arquivo.
`Get-CimInstance Win32_Process` encontrou a árvore e registrou os argumentos.
`netstat -ano` amostrou TCP com PID. O NetLog registrou eventos DNS, TCP e
origens HTTP do runtime. O canal operacional DNS do Windows estava desativado.
Os timestamps abaixo usam UTC−03.

| Condição | PID navegador / NetworkService | Primeiro TCP observado | Destino | Resultado |
| --- | --- | --- | --- | --- |
| Base | 23636 / 20148 | 18:50:55.154 | `150.171.22.17:443` | ESTABLISHED. NetLog associou ao host `config.edge.skype.com`. |
| Base | 23636 / 20148 | 18:51:03.104 | `8.8.4.4:443` | ESTABLISHED. `dns.google/dns-query`. |
| Base | 23636 / 20148 | 18:51:14.543 | `8.8.8.8:443` | ESTABLISHED. `dns.google/dns-query`. |
| Controle | 18308 / 14028 | 18:51:25.967 | `8.8.4.4:443` | ESTABLISHED. `dns.google/dns-query`. |
| Controle | 18308 / 14028 | 18:51:27.764 | `8.8.8.8:443` | ESTABLISHED. `dns.google/dns-query`. |

O NetLog capturou 8 eventos de resposta DNS na linha de base e 6 com controle.
A origem `config.edge.skype.com` apareceu somente na primeira amostra. A
rota `/dns-query` e os IPs do Google Public DNS identificam as conexões
restantes como DoH. As duas árvores encerraram com código 0, sem processos
remanescentes. [Flags do WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/webview-features-flags)
e [transporte DoH do Google Public DNS](https://developers.google.com/speed/public-dns/docs/secure-transports).

### M4 e artefato empacotado

- A junction apontava para outro diretório temporário com dados sintéticos.
  Antes da correção, as duas formas de seleção importavam o arquivo do destino.
  A inspeção passou a consultar os atributos com `lstat` antes de descer ou abrir.
- A exportação com ACL negando escrita excedeu 15 segundos antes da correção.
  No Windows, `mkstemp` repetia a criação do temporário sob acesso negado.
  A criação agora é exclusiva e falha prontamente. Importação e exportação
  retornam o motivo da recusa. `icacls` aplicou e removeu as ACLs de teste.
  A rechecagem confirmou destino vazio, quarentena estável e pacote anterior íntegro.
- A regressão completa usou `python -m pytest -o addopts= --strict-markers -q -r s`.
  A execução dirigida usou a mesma base com `tests/security tests/integration/test_build_spec.py`.
  `python docs/research/verify-consistency.py` registrou 44/44.
- `powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1` rodou
  novamente a suíte, empacotou e confirmou código 0 para `--version`.
  `python -m PyInstaller.utils.cliutils.archive_viewer dist\LiaAgentHub.exe -r -b`
  confirmou CLI, descritor MCP, plataforma, Bottle, EdgeChromium e HTML/CSS/JS.
- `Start-Process` abriu a janela nativa no diretório externo com perfil de
  teste. O cliente chamou a API local do executável e confirmou HTTP 403 sem
  token, diagnóstico autenticado, fluxo de importação e exportação, verificação
  de hash e persistência após reabrir. As duas janelas fecharam com código 0,
  portas liberadas e processos WebView2 encerrados. A pasta do executável
  continha somente o binário. Os dados ficaram sob `%USERPROFILE%\Lia` no perfil
  temporário, com logs em `%LOCALAPPDATA%\Lia\AgentHub\logs`.
- `dist\LiaAgentHub.exe` tem 11 651 049 bytes.
  SHA-256 `72218E10412698DCA5C74D4BB544650EDAB815F95232D02C1BD7CCE964136DAF`.
  Authenticode `NotSigned`. A varredura por padrões de credencial no arquivo
  bruto, nas 101 entradas CArchive e 320 entradas PYZ descomprimidas e nos logs
  retornou zero correspondências. Os tokens efêmeros capturados nos cabeçalhos
  pelo NetLog foram suprimidos das evidências após o fechamento.
- Evidências locais em `%TEMP%\LiaHub-Homolog-b7df471`. Os diretórios
  `baseline` e `controlled` contêm NetLog, argumentos, processos e TCP por PID.
  `measure.ps1` e `netlog-summary.py` reproduzem a coleta e o resumo.
  Consulte também `m4-before.log`, `regression-final.log`, `build-release.log`,
  `smoke-release.log`, `contents.txt` e `scan-package.log`.

A distribuição continua bloqueada. O egress residual exige avaliar uma política
para o runtime, e falta executar o binário em Windows limpo. As decisões
D-01, D-05, D-16 e D-18 seguem com os estados e restrições registrados.

### Regressão e build após a correção de Unicode

A revisão `a19cfaf` passou pela suíte Windows de
`scripts/build_windows.ps1` sem `-SkipTests`. O log está em
`J:/Lia/migration/agent-hub/windows-build-a19cfaf.log`.
O script gerou os dois binários. Cópias em
`J:/Lia/migration/agent-hub/windows-smoke-a19cfaf` foram testadas
com PATH restrito ao Windows e com o programa fora do checkout.
O executável gráfico retornou 0 em `--version`. A CLI preservou
`Origem → destino.` em JSON redirecionado nos comandos
`skill preview` e `skill publish`.

| Artefato | SHA-256 |
| --- | --- |
| LiaAgentHub.exe | `1fbd116d70aa5a17ef71cf6872255fef34076b20bc99bc982d8c99b892c44ef9` |
| LiaAgentHubCli.exe | `9fffcf834a37714b812f6e2c391f1069a2a16ae46a03f6bebe1312582b9fbe14` |

Um teste direto de criação de symlink em pasta temporária retornou
WinError 1314. Essa sessão ainda não cobre a criação de symlinks
NTFS. O ensaio não reclassifica D-09 nem Windows limpo.

A cópia externa do mesmo build também passou no teste de produto
com janela nativa e perfil temporário. O cliente HTTP verificou
403 sem token, diagnóstico autenticado, importação, quarentena,
validação, promoção, exportação, hash do pacote e reimportação.
Junctions e operações sob ACL NTFS restritiva foram recusadas.
A biblioteca persistiu após reabrir. As duas janelas fecharam com
código 0, portas liberadas e processos WebView2 encerrados.
O arquivador do PyInstaller verificou os módulos de oficina,
consumo e servidor, além do frontend e do backend EdgeChromium.
Evidência: `J:/Lia/migration/agent-hub/windows-product-a19cfaf/smoke.log`
e `contents.txt` no mesmo diretório. O teste confirmou os argumentos
do runtime. A medição de egress mantém o estado anterior de D-09.

### D-09 no build atual · 20 de novembro de 2026

Medi o mesmo `LiaAgentHub.exe` de `a19cfaf` por 25 segundos em
cada condição, com perfis novos. O baseline definiu
`WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` só para NetLog. O controle
usou o mesmo NetLog e todos os argumentos de rede do Hub. A linha de
comando confirmou a diferença nos processos navegador 6760 e 11368.

| Condição | Processo de rede | Destino TCP estabelecido | Primeira amostra local |
| --- | --- | --- | --- |
| Baseline | msedgewebview2.exe 22540 | 150.171.22.17:443 | 03:05:53 |
| Baseline | msedgewebview2.exe 22540 | 8.8.4.4:443 e 8.8.8.8:443 | 03:05:58 |
| Controle | msedgewebview2.exe 14776 | 8.8.8.8:443 e 8.8.4.4:443 | 03:06:25 |

O NetLog associou o primeiro destino a `config.edge.skype.com`.
Esse destino não apareceu no controle. `dns.google/dns-query`
apareceu nas duas execuções, alinhado às conexões HTTPS observadas.
O controle continua **PARTIAL**, pois houve egress externo com
os argumentos ativos. As duas execuções fecharam com código 0 e
sem sobreviventes observados. Os tokens de sessão capturados foram
redigidos dos NetLogs. O procedimento e os arquivos por PID estão em
`J:/Lia/migration/agent-hub/windows-d09-a19cfaf`.

#### Ensaio de isolamento por argumentos do runtime

No mesmo binário, testei os argumentos atuais acrescidos de
`DnsOverHttps` em `--disable-features` e de
`--host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost"`.
A primeira tentativa, que excluía somente `localhost`, também
impediu o frontend de alcançar o servidor local. Descartei esse
resultado como candidato.

Com os dois endereços excluídos do bloqueio, o PID navegador 14864
recebeu os argumentos. Em 25 segundos, o NetLog registrou seis
requisições locais, incluindo `/api/items`, e zero eventos
`DNS_TRANSACTION`. O TCP por PID não registrou destino externo.
O aplicativo fechou com código 0 e sem os processos observados.
Evidência: `J:/Lia/migration/agent-hub/windows-d09-loopback-a19cfaf/summary.json`.

O resultado é de uma execução diagnóstica com overrides locais.
A [documentação do WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/webview-features-flags)
orienta o uso dos browser flags para desenvolvimento. D-09 continua
PARTIAL para o build padrão e a configuração de distribuição.

#### Disponibilidade de Windows limpo e varredura dos artefatos

O host desta rodada é Windows 11 Home, build 26200, com sessão
sem elevação. A checagem não encontrou Windows Sandbox, comandos
do Hyper-V, VirtualBox, VMware ou QEMU disponíveis, nem um
diretório de VM identificado no workspace. A condição Windows
limpo sem Python permanece **BLOCKED**.

A varredura do build atual examinou os dois binários brutos,
171 entradas CArchive, 472 entradas PYZ e o log de produto.
Os cinco padrões de chave e token pesquisados retornaram zero
correspondências. Os resultados guardam apenas nomes de padrões
e contagens. Evidência:
`J:/Lia/migration/agent-hub/windows-product-a19cfaf/credential-pattern-scan.json`.
