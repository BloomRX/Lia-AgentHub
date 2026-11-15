# Validação e build no Windows — plano de execução

**Para:** Codex, executando em uma máquina Windows real.
**Objetivo:** validar o MVP do Lia Agent Hub no Windows, corrigir defeitos
concretos que só aparecem lá, gerar o `.exe` e provar que ele funciona numa
máquina sem Python instalado.
**Data de preparação:** 2026-11-15 (UTC).
**Preparado em:** Linux. **Nada neste documento foi executado no Windows.**

---

## 0. Leia isto antes de qualquer comando

### 0.1 O que foi executado e o que foi apenas inspecionado

Esta distinção é a espinha dorsal do documento. Não a colapse.

| Marcador | Significa |
|---|---|
| **[EXECUTADO]** | Rodou de verdade, neste repositório, no Linux. O resultado está registrado. |
| **[INSPECIONADO]** | O código foi lido e a conclusão vem da leitura. Não houve execução do caminho Windows. |
| **[A VALIDAR]** | **Ninguém executou.** Depende de Windows real. É o seu trabalho. |

Repetindo, porque é a instrução mais importante: **este documento não contém
nenhuma evidência de funcionamento no Windows.** Tudo que depende de Windows
está marcado **[A VALIDAR]**. Se você vir um resultado marcado como
[EXECUTADO] e [A VALIDAR] ao mesmo tempo, é erro de redação — reporte.

### 0.2 Estado Git no momento em que este documento foi escrito

Verificado por comando, não por memória:

| Item | Valor |
|---|---|
| Branch | `arena/a92004be-lia-agenthub` |
| Commit de referência | o commit que introduziu este documento — obtenha com `git log --oneline -1 -- docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md` |
| Base da branch em `main` | `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` |
| `main` (local e remoto) | `34a27f48` — **intacta** |
| Upstream configurado | **nenhum** para a branch de trabalho |
| PR / merge | nenhum |
| Suíte de testes | 284 passando **[EXECUTADO]** |

`main` não é tocada por este trabalho e você não deve tocá-la.

### 0.3 Onde cada validação pode rodar

| Validação | Linux (feito) | Windows real (você) |
|---|---|---|
| Suíte automatizada (284 testes) | sim, executada | **sim, [A VALIDAR]** |
| Detecção de WebView2 | impossível (só existe no Windows) | **[A VALIDAR]** |
| Janela nativa (pywebview) | impossível (sem display) | **[A VALIDAR]** |
| Build do `.exe` | impossível | **[A VALIDAR]** |
| Execução em máquina sem Python | impossível | **[A VALIDAR]** |
| Escrita atômica sob antivírus | impossível | **[A VALIDAR]** |
| Caminhos longos, nomes reservados | parcial (ver §5) | **[A VALIDAR]** |

### 0.4 Limitações conhecidas deste plano

1. **Nenhum script PowerShell foi executado.** Não há PowerShell no ambiente de
   preparação. `scripts/build_windows.ps1` foi escrito e revisado por leitura;
   a sintaxe não foi compilada. Se ele falhar na primeira linha, é isso.
2. **Nenhuma simulação de sistema de arquivos Windows.** As regras de nome
   reservado (`CON`, `aux`), fluxo NTFS (`arquivo:fluxo`) e separador `\` são
   testadas por *string*, não por comportamento real do NTFS.
3. **A UI nunca foi vista.** Não há navegador nem display no ambiente de
   preparação. Os 42 testes de interface verificam estrutura e contrato HTTP,
   não aparência.
4. **`.exe` nunca existiu.** Nenhum artefato Windows foi publicado. Se você
   encontrar um `dist/LiaAgentHub.exe` em algum lugar, ele não veio daqui.

---

## 1. O produto, em uma página

Entender isto evita metade das investigações erradas.

**O que é.** Um acervo local de "capacidades" (Agent Skills, pacotes
`.lia-capability`, MCPs descritos). O usuário importa arquivos, o Hub analisa,
descreve e guarda. O usuário consulta depois.

**O que ele faz.** Lê arquivos. Calcula hash. Escreve JSON. Serve uma interface
numa porta local. Nada mais.

**O que ele não faz.** Não executa o que importa. Não abre conexão externa. Não
pede conta. Não guarda credencial. Não envia telemetria. Não atualiza sozinho.

**A regra de ouro:** *o Hub nunca executa conteúdo importado.* Não é uma
limitação a contornar, é o produto. Toda a arquitetura existe para tornar isso
verdade por construção, não por disciplina.

### 1.1 Arquitetura em quatro camadas

```
interface/       HTTP local + UI estática. Fala JSON.
   |
app.py           Caso de uso: importar, promover, validar, exportar.
   |
domain/          Regras puras: skills, paths, risk, integrity, unicode_policy.
   |
adapters/        Efeito real: disco, ZIP, registro do Windows, atomicidade.
```

`domain/` não conhece `adapters/`. Isso é testado.

### 1.2 Onde os dados ficam (Windows, instalado)

| O quê | Caminho | Criado por |
|---|---|---|
| Biblioteca | `%USERPROFILE%\Lia\AgentHub\Biblioteca` | `Locations.ensure()` |
| Quarentena | `%USERPROFILE%\Lia\AgentHub\Quarentena` | idem |
| Exportados | `%USERPROFILE%\Lia\AgentHub\Exportados` | idem |
| Coleções | `%USERPROFILE%\Lia\AgentHub\Colecoes` | idem |
| Índice comum | `%USERPROFILE%\Lia\Comum\Capacidades\index.json` | `publish_index()` |
| Config | `%APPDATA%\Lia\AgentHub\config` | `paths_resolver` (frozen) |
| Logs | `%LOCALAPPDATA%\Lia\AgentHub\logs\agenthub.log` | `_setup_logging` |
| Recursos | `%TEMP%\_MEIxxxxxx\lia_agenthub\resources` | PyInstaller, onefile |

**Nenhum dado do usuário fica dentro da pasta do programa.** Um `uninstall`
que apaga a pasta do `.exe` não toca no acervo. Isso é decisão de produto, não
acidente — e você deve confirmar que continua verdade no build (§7.9).

---

## 2. Comandos verificados

Todos abaixo foram rodados neste repositório **[EXECUTADO]**, exceto onde
marcado. Copie como está.

### 2.1 Ambiente

```bat
:: conferir versão — precisa estar entre 3.11 e 3.15
py -3.12 -c "import sys; print(sys.version)"

:: criar venv
py -3.12 -m venv .venv

:: ativar (cmd)
.venv\Scripts\activate.bat

:: ativar (PowerShell)
.venv\Scripts\Activate.ps1
```

Se `py` não existir, use `python`. Se `python` abrir a Microsoft Store, você
está usando o stub — instale o Python de python.org.

### 2.2 Instalar

```bat
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pip install "pywebview>=6.2"
```

O `pyproject.toml` declara `dependencies = []`. As dependências de runtime são
zero. `pywebview` é extra (`.[webview]`), e só é necessário para a janela
nativa; sem ele o Hub abre no navegador. **Isso é intencional** e você não deve
"corrigir".

Confira:

```bat
python -c "import webview; print(webview.__version__)"
python -c "import PyInstaller; print(PyInstaller.__version__)"
```

### 2.3 Testes

```bat
:: suíte completa — a partir da RAIZ do repositório
python -m pytest -q

:: só os de segurança
python -m pytest tests/security -q

:: só os de prontidão Windows
python -m pytest tests/integration/test_windows_readiness.py -v
python -m pytest tests/integration/test_packaging.py -v
```

Resultado esperado: **284 passed**. No Linux leva ~15 s **[EXECUTADO]**.
No Windows, espere mais (antivírus e disco), mas a contagem deve ser a mesma.

Consistência documental:

```bat
python docs\research\verify-consistency.py
```

Esperado: `44/44` **[EXECUTADO] no Linux**.

### 2.4 Rodar sem janela (o testador mais útil)

```bat
python -m lia_agenthub --diagnostico
python -m lia_agenthub --no-window --home %TEMP%\lia-teste
```

`--no-window` imprime a URL e o token e **fica servindo até ser morto** — não
retorna. Use outro terminal, ou `Start-Process` (roteiro na §3.B.1). É assim
que você valida backend sem depender de a janela abrir.

A saída tem exatamente duas linhas, verificada aqui **[EXECUTADO]**:

```
http://127.0.0.1:39935/
TOKEN=<43 caracteres url-safe, diferente a cada execucao>
```

O token muda a cada execução, e a porta é efêmera. Nada disso é configurável
pelo usuário — de propósito.

`--diagnostico` **funciona** e imprime os caminhos resolvidos **[EXECUTADO]**:

```
home         /tmp/lh3
library      /tmp/lh3/Biblioteca
...
python       3.11.2
```

### 2.5 Rodar com janela

```bat
python -m lia_agenthub
```

Comportamento, em ordem: tenta `pywebview` (WebView2); se falhar, cai para o
navegador padrão. Mensagem na tela diz qual dos dois aconteceu. Nunca baixa
nada.

### 2.6 Empacotar

```bat
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Ou, manualmente:

```bat
python -m PyInstaller --noconfirm --clean packaging\lia_agenthub.spec
```

Artefato: `dist\LiaAgentHub.exe`.

**Aviso:** `build_windows.ps1` nunca foi executado (§0.4, item 1). Ele roda a
suíte antes de empacotar e aborta se algo falhar. Se o script quebrar por
sintaxe, o build manual acima é equivalente.

---

## 3. Auditoria dirigida — o que já se sabe

Cada seção traz a conclusão e, onde houver, o que você precisa confirmar.
**Não repita o que está resolvido.** O objetivo é que você gaste tempo no que
só Windows pode responder.

### 3.A Python e dependências

| Item | Conclusão | Estado |
|---|---|---|
| Versão mínima | 3.11 | **[INSPECIONADO]** `requires-python = ">=3.11"` |
| Faixa suportada | 3.11 – 3.15 | **[INSPECIONADO]** interseção de `pythonnet` (`<3.16,>=3.11`) e `PyInstaller` (`<3.16`) |
| Recomendada | 3.12 ou 3.13 | recomendação, não requisito |
| Arquitetura | x64 | `pyinstaller` publica wheel `win_amd64`; 32 bits não é suportado |
| Deps de runtime | **zero** | `dependencies = []` |
| Dep de janela | `pywebview>=6.2` | extra opcional |
| O que `pywebview` puxa | `pythonnet` (só win32), `bottle`, `proxy-tools`, `typing_extensions` | **[INSPECIONADO]** metadata do pacote |
| Deps de dev | `pytest>=8.0` | não vão para o `.exe` |

**Por que nenhuma dependência foi atualizada:** nenhuma está incompatível.
Atualizar por estar "velho" não é motivo — quebra reprodutibilidade sem ganho.

**O que confirmar no Windows:**

```bat
python -c "import sys,platform;print(sys.version, platform.machine())"
python -c "import pythonnet; print(pythonnet.__version__)"
```

`platform.machine()` deve ser `AMD64`. Se for `x86`, pare: o wheel do
PyInstaller não existe para 32 bits.

### 3.B WebView2

O caminho é: `__main__.main()` → `detect_webview2()` → se disponível,
`pywebview.create_window()` + `webview.start()`; senão, aviso e
`webbrowser.open()`.

**Detecção** **[INSPECIONADO]**, verificada contra a documentação da Microsoft:

| Onde | Chave |
|---|---|
| HKLM (WOW6432Node) | `SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}` |
| HKLM (64-bit) | `SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}` |
| HKCU | `software\Microsoft\EdgeUpdate\Clients\{F3017226-...}` |

Valor `pv` (`REG_SZ`) maior que `0.0.0.0` significa instalado. `pv` vazio ou
`0.0.0.0` significa **não instalado**. O código trata os dois como ausência,
corretamente. Há ainda fallback por pasta em `C:\Program Files (x86)\Microsoft\EdgeWebView\Application`.

**Ponto frágil [INSPECIONADO]:** a função lê HKLM e HKCU dentro do mesmo laço,
para cada chave. Isso funciona, mas o acesso a HKCU com uma chave HKLM-only
levanta `OSError`, tratado. Sem problema.

**Instalar o runtime é requisito?** Não. O produto funciona sem ele, no
navegador. É requisito apenas para **janela nativa**. O Hub não baixa nem
instala WebView2 — decisão deliberada, porque baixar runtime silenciosamente é
exatamente o comportamento que o produto promete não ter.

**O que confirmar [A VALIDAR]:**

```bat
python -c "from lia_agenthub.adapters.platform_check import detect_webview2 as d; s=d(); print(s.available, s.version, s.reason)"
```

Registre a saída. Se `available=False` numa máquina que você sabe ter WebView2,
é bug de detecção — investigue com `reg query`:

```bat
reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv
reg query "HKCU\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" /v pv
```

**A validação do token não é a validação da janela.** Ver §3.B.1.

#### 3.B.1 Como o frontend fala com o backend

Isto é o que mais se confunde, então seja literal.

1. `create_server()` gera `token = secrets.token_urlsafe(32)` e faz bind em
   `127.0.0.1:0` (porta efêmera).
2. `serve_in_thread()` devolve `"http://127.0.0.1:<porta>/"`.
3. Quando o navegador pede `/`, o handler serve `index.html` substituindo a
   string literal `__LIA_TOKEN__` pelo token real.
4. O JavaScript lê esse valor e manda em `X-Lia-Token` em toda chamada `/api/`.

Consequências que importam para você:

- O token **nunca** aparece numa URL, num log de servidor ou em disco. Só no
  HTML servido para `127.0.0.1`.
- `ALLOWED_HOSTS = {"127.0.0.1", "localhost"}`. Requisição com outro `Host` ou
  `Origin` recebe 403.
- A porta é efêmera por padrão, então **a URL muda a cada execução**. Você não
  pode "decorar" a porta.

**Validar por HTTP prova o backend. Não prova a janela.** São afirmações
diferentes e você deve reportá-las separadamente:

| Afirmação | Como se prova |
|---|---|
| Backend responde e autentica | `curl`/Invoke-WebRequest com e sem token |
| A janela nativa abriu | olhar a tela; processo filho do WebView2 existe |
| O frontend dentro da janela carregou | ver a UI renderizada, com dados |
| O frontend *consegue* chamar a API | ver dados reais na tela, não placeholder |

Quatro linhas, quatro evidências distintas. Não escreva "UI validada" se você
só fez `curl`.

Roteiro de HTTP (PowerShell, com o Hub em `--no-window`):

O Hub fica servindo até ser morto — `--no-window` **bloqueia**. Escreva a
saída num arquivo e leia de lá:

```powershell
# 1. subir em background, capturando as duas linhas
$proc = Start-Process python -ArgumentList "-u","-m","lia_agenthub","--no-window","--home","$env:TEMP\lia-h" `
        -RedirectStandardOutput "$env:TEMP\hub.txt" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

# 2. ler URL e token
$linhas = Get-Content "$env:TEMP\hub.txt"
$url = ($linhas[0] -split '\s+')[0]          # http://127.0.0.1:PORTA/
$tok = ($linhas[1] -replace '^TOKEN=','')     # token de sessão

# 3. sem token → deve ser 403
try { Invoke-WebRequest "$url/api/items" -UseBasicParsing } catch { $_.Exception.Response.StatusCode.value__ }

# 4. com token → deve ser 200
(Invoke-WebRequest "$url/api/items" -Headers @{"X-Lia-Token"=$tok} -UseBasicParsing).Content

# 5. Host estranho → deve ser 403
try { Invoke-WebRequest "$url/api/items" -Headers @{"X-Lia-Token"=$tok; "Host"="evil.example"} -UseBasicParsing } catch { $_.Exception.Response.StatusCode.value__ }

# 6. encerrar
Stop-Process -Id $proc.Id
```

Esperado: `403`, `{"items": []}` ou lista, `403`.

A forma exata das duas linhas foi verificada aqui **[EXECUTADO]**:
`http://127.0.0.1:39935/` seguida de `TOKEN=...`. Se o seu `$linhas[1]` não
começar com `TOKEN=`, algo mudou — inspecione o arquivo antes de continuar.

Este roteiro é derivado de um teste que **passou no Linux** com `GET /api/items`
+ `X-Lia-Token` → `200 {"items": []}` **[EXECUTADO]**. Repetir no Windows é
[A VALIDAR].

**Encerramento limpo [A VALIDAR no Windows]** — Linux provou que funciona
**[EXECUTADO]**: `shutdown()` + `server_close()` deixa a thread morta e a porta
livre (`connect_ex` → 111). No Windows, confirme que **não sobram processos**:

```powershell
# antes de abrir e depois de fechar
Get-Process LiaAgentHub, python*, msedgewebview2 -ErrorAction SilentlyContinue |
    Select-Object ProcessName, Id
```

Depois de fechar a janela: nenhum `LiaAgentHub`, nenhum `msedgewebview2`
órfão, e `Get-NetTCPConnection -LocalPort <porta>` vazio.

### 3.C PyInstaller

| Item | Decisão | Estado |
|---|---|---|
| Entry point | `packaging/launcher.py` | **[EXECUTADO]** — o antigo quebrava |
| Modo | onefile | recomendação mantida |
| `console` | `False` | decisão de produto |
| `upx` | `False` | UPX gera falso positivo de antivírus |
| UI estática | `datas` em `lia_agenthub/resources/static` | **[INSPECIONADO]** |
| hiddenimports | `lia_agenthub.resources`, `webview`, `webview.platforms.edgechromium`, `webview.platforms.winforms` | **[INSPECIONADO]** |
| excludes | qt/gtk/cef/pyside, tkinter, pytest, setuptools, pip | **[INSPECIONADO]** |

**Por que `launcher.py` e não `__main__.py`.** Isto era um defeito real, agora
corrigido. O PyInstaller executa o script de entrada como `__main__`, sem
contexto de pacote. `lia_agenthub/__main__.py` começa com `from . import APP_NAME`.
Resultado: `ImportError: attempted relative import with no known parent package`
**[EXECUTADO — reproduzido]**. O bundle nunca teria funcionado.

`packaging/launcher.py` importa o pacote pelo nome absoluto e funciona nos dois
modos. `lia_agenthub/__main__.py` **deve continuar** com import relativo para que
`python -m lia_agenthub` funcione. Há testes guardando as duas coisas.

**onefile vs onefolder.** Mantenha onefile. O produto promete "baixe e rode":
um arquivo, sem pasta para o usuário gerenciar. O custo é extração para
`%TEMP%` a cada inicialização (mais lento, e antivírus olha com mais atenção),
mas é o trade-off certo para o público. **Não mude a estratégia sem um motivo
que os testes revelem.**

**Indícios de que os excludes estão corretos [INSPECIONADO]:** `webview/` e
`bottle.py` não usam `pkg_resources`, então excluir `setuptools` é seguro. O
pywebview documenta que o PyInstaller empacota todos os backends instalados,
mesmo sem uso — daí a lista.

**O que confirmar no Windows [A VALIDAR]:**

```bat
python -m PyInstaller --noconfirm --clean packaging\lia_agenthub.spec
dir dist
```

Esperado: `dist\LiaAgentHub.exe`, ordem de 15–40 MB. Se passar de 100 MB, algum
backend gráfico entrou — veja `build\lia_agenthub\warn-lia_agenthub.txt`.

### 3.D Armazenamento e portabilidade

| Afirmação | Como foi verificado | Estado |
|---|---|---|
| Escrita atômica | `os.replace` + temp no mesmo diretório | **[INSPECIONADO]** |
| Retry no Windows | 5 tentativas, backoff 0.05→0.8 s | **[EXECUTADO no Linux, com mock]** |
| SHA-256 do conteúdo | `integrity.py` | **[INSPECIONADO]** |
| Índice sem caminho local | `common/index.json` não tem `/` nem `C:` | **[EXECUTADO]** |
| Sem dependência do cwd | app rodou de `/tmp` e achou os recursos | **[EXECUTADO]** |
| Unicode em nomes | `skïll-ção` importou | **[EXECUTADO]** |
| Caminho longo | 215 chars recusado com `C8` | **[EXECUTADO]** |
| Nome reservado / fluxo NTFS / UNC / drive letter | recusados por regra de string | **[EXECUTADO por string]** |

**O retry de escrita.** `os.replace` no Windows levanta `PermissionError`
quando antivírus, indexador de busca ou editor seguram o destino por
milissegundos. Os dados **nunca corriam risco** — o arquivo antigo sobrevive e
não sobra `.part` órfão — mas a escrita falhava. Agora repete com backoff,
**apenas no Windows**; em POSIX continua uma tentativa só. Falha permanente
continua propagando.

Confirmar no Windows **[A VALIDAR]**: importe, promova, e logo em seguida
importe de novo várias vezes, com o Windows Defender ativo. Nenhuma exceção
`PermissionError` deve vazar para a UI.

**Caminho longo.** `MAX_PATH_LEN = 200` recusa antes de o NTFS reclamar. A
margem existe porque o caminho final inclui a raiz da biblioteca. **Não aumente
esse número** sem medir: o limite clássico do Windows é 260, e o prefixo `\\?\`
não é usado pelo produto. Se um usuário legítimo bater no limite, o problema é
de UX (mensagem clara), não de constante.

### 3.E Segurança — o que preserva e o que você retesta

**Princípios que o build não pode violar.** Se um teste seu falhar contra
qualquer um destes, o teste está errado, não o produto:

1. O Hub nunca executa Skill, MCP ou CLI importado.
2. Nenhuma credencial de terceiro é pedida ou guardada.
3. Nenhuma conexão externa automática. Toda egress é opt-in e declarada.
4. Hash **não é** assinatura. O produto nunca diz "assinado".
5. Não existe score de risco automático. Risco é regra transparente, com
   limites documentados.
6. Sem marketplace, sem sincronização em nuvem.
7. Sem execução, sem sandbox, sem Test Lab (preservado para o futuro, não
   implementado).

**Superfície de importação [INSPECIONADO]:** `safe_extract.py` valida caminho
relativo (`check_relative_path`), recusa `..`, recusa absoluto, recusa UNC,
recusa drive letter, recusa nome reservado, recusa ponto/espaço final, recusa
fluxo NTFS, detecta colisão por maiúsculas, recusa ZIP aninhado, verifica CRC,
limita tamanho por arquivo e total, e recusa symlink.

**Testes que precisam rodar no Windows** — não são opcionais:

```bat
python -m pytest tests/security -q
```

| Arquivo | Testes | Por que importa no Windows |
|---|---|---|
| `test_path_traversal.py` | 15 | separador `\`, nome reservado, drive letter, UNC, fluxo NTFS |
| `test_archives.py` | 17 | CRC, aninhado, traversal, tamanho — comportamento de ZIP idêntico, mas caminho não |
| `test_integrity_and_packages.py` | 19 | hash, pacote adulterado, verificação |

Um teste de symlink (`test_path_traversal.py:145`) faz `pytest.skip` no
Windows sem privilégio de administrador. **Skip não é falha**, mas registre o
skip no relatório — não é o mesmo que "passou".

---

## 4. Riscos identificados

Classificação: **P0** bloqueia execução ou fere segurança/dados; **P1** bloqueia
funcionalidade essencial; **P2** relevante com contorno; **P3** não bloqueia.

| ID | Risco | Nível | Estado |
|---|---|---|---|
| R-01 | Entry point relativo quebrava o bundle | **P0** | **corrigido** `[EXECUTADO]` |
| R-02 | `SO_REUSEADDR` permite sequestro de porta no Windows | **P1** | **corrigido** `[EXECUTADO por teste]` |
| R-03 | `os.replace` sem retry falha sob antivírus | **P1** | **corrigido** `[EXECUTADO por teste]` |
| R-04 | `build_windows.ps1` nunca executado | **P1** | aberto **[A VALIDAR]** |
| R-05 | `print()` é no-op sob `console=False` | P2 | aberto **[A VALIDAR]** |
| R-06 | `dir_lock` é código morto | P3 | aberto |
| R-07 | `seed_demo.py` tem laço morto | P3 | aberto |
| R-08 | Detecção de WebView2 não validada em máquina real | **P1** | aberto **[A VALIDAR]** |
| R-09 | Assinatura de código ausente → SmartScreen | P2 | decisão aberta (D-16) |
| R-10 | Suíte nunca rodou no Windows | **P1** | aberto **[A VALIDAR]** |

Detalhamento dos abertos na §8.

---

## 5. O que testar, e como saber que passou

> **Atenção a uma colisão de nomes.** Dois prefixos parecidos convivem neste
> documento e significam coisas diferentes:
>
> - **`D-01` … `D-09`** aqui na §5 são **testes de distribuição**.
> - **`D-01`, `D-05`, `D-16`, `D-18`** na §9 são **decisões de produto** do
>   `docs/DECISION-REGISTER.md`.
>
> Mesmo texto, assuntos distintos. Quando houver dúvida, o contexto diz: testes
> aparecem em tabela com coluna "Esperado"; decisões aparecem na §9 com estado
> `OPEN`/`RECOMMENDED`. Se você for reportar "D-01 falhou", diga **"teste D-01"**
> para não parecer que uma decisão de produto foi reprovada.

Cada linha é uma afirmação verificável. **Não marque PASS sem rodar.** O
vocabulário é rígido:

| Estado | Significado |
|---|---|
| `PLANEJADO` | escrito neste documento, nada executado |
| `TESTE ESCRITO` | existe teste automatizado, nunca rodou no Windows |
| `EXECUTADO` | rodou, resultado registrado |
| `PASS` | rodou **e** o resultado bateu com o esperado |
| `FAIL` | rodou e não bateu |
| `BLOQUEADO` | não foi possível rodar; diga por quê |

### 5.1 Automatizados — nada a escrever, tudo a rodar

| ID | Funcionalidade | Comando | Esperado | Evidência |
|---|---|---|---|---|
| A-01 | Suíte completa | `python -m pytest -q` | `284 passed` | saída colada |
| A-02 | Segurança | `python -m pytest tests/security -q` | `76 passed` | saída |
| A-03 | Prontidão Windows | `python -m pytest tests/integration/test_windows_readiness.py -v` | `13 passed` | saída |
| A-04 | Empacotamento | `python -m pytest tests/integration/test_packaging.py -v` | `13 passed` | saída |
| A-05 | Consistência doc | `python docs\research\verify-consistency.py` | `44/44` | saída |
| A-06 | Sem segredos | `scripts\validate.sh` ou equivalente | sem segredos | saída |

`scripts/validate.sh` é bash. No Windows, rode via Git Bash ou `wsl`, ou aceite
que A-06 fica `BLOQUEADO` e registre.

### 5.2 Manual — a janela e o que só humano vê

| ID | Funcionalidade | Procedimento | Esperado | Crítico |
|---|---|---|---|---|
| M-01 | Janela nativa abre | `python -m lia_agenthub` | janela com a UI, sem terminal preto | sim |
| M-02 | Aviso de WebView2 | renomear/negar a chave, rodar | aviso claro + abre no navegador | não |
| M-03 | UI renderiza | olhar a tela | 6 visões, sem placeholder quebrado | sim |
| M-04 | UI fala com backend | importar pela UI | lista atualiza com o item | **sim** |
| M-05 | Encerramento limpo | fechar a janela | processo sai, porta liberada | sim |
| M-06 | Sem processo órfão | `Get-Process msedgewebview2` | nenhum após fechar | sim |
| M-07 | Segunda instância | abrir o Hub duas vezes | portas distintas, sem conflito | não |
| M-08 | Diagnóstico | `--diagnostico` | caminhos corretos do Windows | sim |

M-04 é o teste que separa "backend ok" de "produto ok". Faça-o com arquivo
real, não com `curl`.

### 5.3 Funcionais com arquivos reais

Gere as fixtures primeiro:

```bat
python scripts\make_fixtures.py %TEMP%\lia-fx
```

São 14, sintéticas, e cada uma tem comportamento esperado **verificado no
Linux** **[EXECUTADO]**: 0 divergências.

| ID | Fixture | Esperado |
|---|---|---|
| F-01 | `01-skill-valida` | importa, licença MIT detectada |
| F-02 | `02-skill-sem-licenca` | importa, licença **desconhecida** (não "livre") |
| F-03 | `03-skill-com-scripts` | importa, `containsScripts=true`, **nada executado** |
| F-04 | `04-skill-invalida` | **recusa** (frontmatter fora da spec) |
| F-05 | `05-skill-referencia-quebrada` | importa com aviso `REFERENCE_MISSING` |
| F-06 | `06-skill-bidi-prosa` | importa com `requiresReview=true` |
| F-07 | `07-skill-bidi-codigo` | **recusa** (bidi em bloco de código) |
| F-08 | `08-zip-traversal.zip` | **recusa** (`..` no caminho) |
| F-09 | `09-zip-aninhado.zip` | **recusa** (ZIP dentro de ZIP) |
| F-10 | `10-zip-crc-invalido.zip` | **recusa** (CRC) |
| F-11 | `11-zip-arquivo-grande.zip` | **recusa** (65 MB) |
| F-12 | `12-pacote-valido.lia-capability` | verifica OK, importa |
| F-13 | `13-pacote-adulterado.lia-capability` | **falha na verificação de hash** |
| F-14 | `14-documento-solto/notas.md` | importa (documento sem SKILL.md) |

**F-03 é a prova de não-execução.** O script dentro dela cria `PWNED.txt` se
rodar. Depois de importar F-03:

```bat
dir /s /b PWNED.txt
python -c "import pathlib,sys; print(list(pathlib.Path('.').rglob('PWNED.txt')))"
```

Esperado: **nenhum resultado**. Se `PWNED.txt` aparecer, o produto executa
conteúdo importado e isso é **P0 de segurança** — pare tudo e reporte.

### 5.4 Integração e persistência

| ID | Funcionalidade | Procedimento | Esperado | Crítico |
|---|---|---|---|---|
| I-01 | Importar → promover | importar F-01, promover | arquivo em `Biblioteca\<id>` | sim |
| I-02 | Índice criado | após promover | `Comum\Capacidades\index.json` existe | sim |
| I-03 | Consulta | buscar por nome | item retorna com metadados | sim |
| I-04 | Persistência | fechar, reabrir | item continua lá | sim |
| I-05 | Metadados | inspecionar item | autor, versão, licença, trust | sim |
| I-06 | Quarentena | importar F-04 | vazio (recusa não enfileira) | não |
| I-07 | Exportar | exportar item promovido | `.lia-capability` gerado | sim |
| I-08 | Integridade | `verify-package` no export | OK | sim |
| I-09 | Dados fora do app | comparar pastas | dados em `%USERPROFILE%\Lia`, não em `dist\` | **sim** |
| I-10 | Unicode | nome com acento | preservado em disco e no JSON | sim |

### 5.5 Distribuição — a máquina limpa

Faça isto numa máquina **sem Python** (ou uma VM limpa). É a única forma de
provar que o `.exe` é autossuficiente.

| ID | Funcionalidade | Procedimento | Esperado | Crítico |
|---|---|---|---|---|
| D-01 | Inicia sem Python | duplo clique | UI abre; sem prompt de instalação | **sim** |
| D-02 | Sem pasta de projeto | mover `.exe` para `C:\teste\` e rodar | funciona; não procura o repo | **sim** |
| D-03 | WebView2 ou fallback | rodar | janela nativa **ou** navegador, com aviso | sim |
| D-04 | Biblioteca criada | primeira execução | `%USERPROFILE%\Lia\AgentHub\*` aparece | sim |
| D-05 | Importar real | importar F-01 pela UI | funciona | **sim** |
| D-06 | Persistência | fechar, reabrir | item continua | sim |
| D-07 | Encerrar | fechar | processo sai; sem órfão | sim |
| D-08 | Sem segredo no pacote | `strings`/`Select-String` no `.exe` | nenhum token, senha, chave | **sim** |
| D-09 | Sem telemetria | monitorar rede | nenhuma conexão de saída | **sim** |

D-08 na prática:

```powershell
Select-String -Path dist\LiaAgentHub.exe -Pattern "sk-","ghp_","BEGIN PRIVATE","password=" -SimpleMatch
```

Esperado: nada. (Um `.exe` onefile é comprimido; se o teste der falso negativo,
unpack com `pyinstxtractor` e repita.)

D-09: use o Monitor de Recursos → aba Rede, ou `netstat -anob | findstr LiaAgentHub`.

---

## 6. Critério objetivo de "MVP validado no Windows"

Diga "validado" somente se **todos** forem verdade:

1. A-01, A-02, A-03, A-04: `PASS`, com saída colada.
2. M-01, M-04, M-05, M-06: `PASS`.
3. F-01, F-03, F-04, F-08, F-10, F-13: `PASS`; F-03 sem `PWNED.txt`.
4. I-01, I-02, I-04, I-09: `PASS`.
5. D-01, D-02, D-05, D-08, D-09: `PASS` em máquina sem Python.
6. Nenhum P0 aberto. P1 abertos documentados com contorno.
7. Nenhum teste de segurança com resultado diferente do Linux, **ou**
   diferença explicada e aceita por escrito.

Se qualquer item falhar, o veredito é **"MVP não validado no Windows"**, com a
lista do que falhou. Não existe "validado com ressalvas" para segurança;
existe para P2/P3.

---

## 7. Sequência de execução

Seis estágios. Rode em ordem. Cada um tem critério de saída — não avance com
critério pendente, exceto para trabalho independente (§7.7).

Antes do estágio 1, registre o estado:

```bat
git branch --show-current
git rev-parse HEAD
git status --short
git log --oneline -1
```

Esperado: `arena/a92004be-lia-agenthub`, árvore limpa, e `main` em
`34a27f48`. O HEAD deve ser o commit que trouxe este documento, ou um
descendente dele — confira com o comando acima. Se divergir, **pare e
reporte**: pode haver trabalho paralelo.

### Estágio 1 — Ambiente

```bat
py -3.12 -c "import sys;print(sys.version)"
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pip install "pywebview>=6.2"
python -c "import webview,PyInstaller,lia_agenthub;print('ok')"
git --version
```

Critério de saída: os quatro imports funcionam; `python --version` entre 3.11 e
3.15; `platform.machine()` é `AMD64`.

Registre também:

```bat
python -c "from lia_agenthub.adapters.platform_check import detect_webview2 as d;s=d();print(s.available,s.version,s.reason)"
```

### Estágio 2 — Testes base

```bat
python -m pytest -q
```

Critério de saída: `284 passed` (ou `283 passed, 1 skipped` — o skip de symlink
é legítimo; registre qual).

**Distinguir falha de ambiente de falha real** — a parte que mais importa:

| Sintoma | Provável causa | Como confirmar |
|---|---|---|
| Todos os testes falham ao importar | pacote não instalado | `python -c "import lia_agenthub"` |
| `ModuleNotFoundError: pytest` | venv errado | `where python` |
| Falha em `test_packaging.py` sobre paths | separador `\` | leia a asserção |
| Falha só em `test_windows_readiness.py` | comportamento Windows real | **é achado, não ambiente** |
| `PermissionError` em tmp | antivírus | repita; se persistir, achado |
| Timeout generalizado | disco lento | aumente e repita |

Falha de *ambiente* você corrige no ambiente. Falha *real* você registra e
conserta (§8).

### Estágio 3 — Execução nativa

```bat
python -m lia_agenthub --diagnostico
python -m lia_agenthub
```

`--no-window` **bloqueia** (fica servindo). Use num terminal separado, ou pelo
roteiro em background da §3.B.1.

Critério de saída: janela abre, UI renderiza, fechar não deixa processo, porta
libera. Rode o roteiro HTTP da §3.B.1 para provar o backend separadamente.
Faça M-01, M-03, M-04, M-05, M-06, M-08.

### Estágio 4 — Funcional com arquivos reais

```bat
python scripts\make_fixtures.py %TEMP%\lia-fx
```

Rode F-01..F-14 (tabela §5.3). Depois I-01..I-10 (§5.4).

**Prova de não-execução (F-03)** é obrigatória. Sem ela, o relatório não vale.

### Estágio 5 — Build

```bat
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

Se o script falhar por sintaxe (nunca foi executado — §0.4), use:

```bat
python -m PyInstaller --noconfirm --clean packaging\lia_agenthub.spec
```

Critério de saída: `dist\LiaAgentHub.exe` existe, 15–40 MB, inicia com
`--version` e sai com código 0.

Verificação de conteúdo:

```bat
python -m PyInstaller.utils.cliutils.archive_viewer dist\LiaAgentHub.exe -l > build\contents.txt
findstr /i "webview bottle lia_agenthub" build\contents.txt
```

Esperado: `webview`, `bottle`, `lia_agenthub` presentes; `PyQt`, `gtk`,
`pyside` **ausentes** (se presentes, `excludes` falhou).

### Estágio 6 — Distribuição

Copie o `.exe` para uma máquina sem Python (ou VM limpa). Rode D-01..D-09.

Se não houver máquina limpa disponível, **registre como BLOQUEADO**. Não
declare validado. Uma máquina com Python não prova autossuficiência.

### 7.7 Trabalho independente quando algo trava

Se um estágio bloquear, não pare. Este bloco existe para você continuar:

| Bloqueado | Continue com |
|---|---|
| Sem WebView2 na máquina | Rode tudo com `--browser`; marque M-01/M-06 `BLOQUEADO` |
| Sem máquina limpa | Faça estágios 1–5; D-* `BLOQUEADO` |
| `build_windows.ps1` quebrado | Build manual; registre o conserto no script |
| Um teste falha | Isole com `pytest -k`, conserte ou documente; siga os outros |
| Sem rede para `pip` | Use wheels locais; registre |

### 7.8 Após qualquer correção

```bat
python -m pytest -q
```

Se a contagem mudar, diga por quê (teste novo? removido?). Não deixe a suíte
menor sem explicar.

### 7.9 Confirmar separação de dados do app

```powershell
Get-ChildItem dist\ | Select-Object Name      # só o .exe
Get-ChildItem $env:USERPROFILE\Lia -Recurse -Depth 1 | Select-Object FullName
```

Os dados devem estar em `%USERPROFILE%\Lia`, nunca em `dist\`.

---

## 8. Bloqueadores e correções

Para cada problema: sintoma → causa → onde → como confirmar → correção →
risco → como retestar.

### R-04 — `build_windows.ps1` nunca foi executado (P1, aberto)

- **Sintoma provável:** erro de parser na primeira linha, ou falha ao achar
  Python.
- **Causa:** não há PowerShell no ambiente de preparação.
- **Arquivo:** `scripts/build_windows.ps1`.
- **Confirmar:** `powershell -NoProfile -Command "& { . .\scripts\build_windows.ps1 -SkipTests }"`
- **Correção:** consertar a linha que falhar. A estrutura (6 etapas, `Fail()`,
  detecção de Python via `py -3.x`) está correta por leitura; o que pode
  quebrar é sintaxe de string aqui-documentada (`@"..."@`) e o `continue`
  dentro de `foreach` em `Find-Python`.
- **Risco:** baixo — script, não produto.
- **Retestar:** rodar de novo; o script deve chegar ao PyInstaller.

### R-08 — Detecção de WebView2 não validada (P1, aberto)

- **Sintoma:** `detect_webview2()` retorna `False` em máquina com WebView2, ou
  `True` sem ele.
- **Causa:** as chaves foram conferidas contra a documentação, não contra um
  registro real.
- **Arquivos:** `src/lia_agenthub/adapters/platform_check.py`.
- **Confirmar:** comparar `reg query` (§3.B) com o retorno da função.
- **Correção:** se divergir, ajustar `WV2_REGISTRY_KEYS`.
- **Caso `pv` como `REG_DWORD` (testado por simulação [EXECUTADO]):** não é
  problema. `if valor and valor != "0.0.0.0"` trata int `0` como ausente
  (falsy) e int `120` como presente, devolvendo `"120"` — versão imprecisa,
  detecção correta. A documentação da Microsoft diz `REG_SZ`; se você encontrar
  `REG_DWORD` numa máquina real, registre, não conserte na pressa.
- **Risco:** baixo; a detecção só decide janela vs navegador.
- **Retestar:** A-03 + M-01 + M-02.

### R-05 — `print()` silencioso sob `console=False` (P2, aberto)

- **Sintoma:** mensagens de aviso (ex.: "WebView2 ausente") não aparecem.
- **Causa:** sob `console=False`, `sys.stdout` é `None` ou inválido. Verificado
  no Linux que `print()` com `sys.stdout=None` **não levanta** — é no-op
  silencioso.
- **Arquivo:** `src/lia_agenthub/__main__.py` (todos os `print`).
- **Impacto:** o usuário não vê o motivo do fallback. Não perde dados.
- **Correção sugerida:** quando `is_frozen()`, mostrar o aviso na própria UI em
  vez de `print`. Não remova os `print` — em modo fonte eles são úteis.
- **Risco:** baixo.
- **Retestar:** M-02 no `.exe`.

### R-06 — `dir_lock` é código morto (P3)

- **Sintoma:** nenhum. `grep` não achou chamador.
- **Arquivo:** `src/lia_agenthub/adapters/atomic.py:77`.
- **Por que não é urgente [EXECUTADO]:** duas instâncias do `AgentHub` no mesmo
  `home` não se corrompem. `build_index()` percorre o repositório em disco
  (`repo.list_all()`), não um cache em memória. Testado: 2 capacidades
  promovidas pela instância 1, `publish_index()` chamado por uma instância 2
  recém-criada → mesmas 2 capacidades, mesmos ids. **Não há perda de dados por
  concorrência de índice.**
- **Correção:** remover. Se um dia for usada, note que a implementação atual
  tem defeito: lock obsoleto (processo morto) nunca é liberado, e
  `FileExistsError` faz `yield False` sem esperar nem tentar de novo.
- **Risco de remover:** nenhum.
- **Risco de *usar* sem consertar:** um travamento deixa o Hub permanentemente
  sem escrever. Se for usar, conserte antes.

### R-07 — laço morto em `seed_demo.py` (P3)

- **Sintoma:** `for …: pass` sem efeito.
- **Correção:** remover.
- **Risco:** nenhum.

### R-09 — Sem assinatura de código (P2, decisão aberta)

- **Sintoma:** SmartScreen mostra "O Windows protegeu o computador".
- **Causa:** não há certificado. D-16 está `OPEN` e **não bloqueia** o MVP
  local.
- **O que **não** fazer:** comprar certificado, assinar, ou escrever que o
  binário é assinado. Não escolha licença. Não crie `LICENSE`.
- **Contorno:** documentar para o usuário ("Mais informações" → "Executar
  assim mesmo"). É o comportamento esperado de build sem certificado.
- **Risco:** de reputação, não técnico.

### R-10 — Suíte nunca rodou no Windows (P1, aberto)

- **Sintoma:** falhas desconhecidas.
- **Correção:** é o estágio 2. Corrija o que aparecer; **não relaxe asserção de
  segurança** para ficar verde. Se um teste de segurança falhar no Windows,
  isso é achado de segurança, não bug do teste.
- **Retestar:** A-01.

### Regra de conserto

Conserte o defeito concreto. **Não** reescreva a arquitetura para facilitar o
empacotamento. Se a correção exigir mudança estrutural, **pare e reporte** —
provavelmente é sinal de que o diagnóstico está errado.

---

## 9. Decisões de produto — não mexa

| ID | Assunto | Estado | Efeito sobre este trabalho |
|---|---|---|---|
| D-01 | Nome e posicionamento | `OPEN` | Não renomeie nada. "Lia Agent Hub" fica. |
| D-05 | Teste e isolamento | `OPEN` | Não implemente sandbox nem Test Lab. |
| D-16 | Licença do repositório | `OPEN` | **Não crie `LICENSE`.** Não escolha licença. Não bloqueia o Windows. |
| D-18 | Risco aceitável | `OPEN` | Não crie score automático. |
| D-03 | — | `RECOMMENDED` | Adotada para implementação, **não aprovada**. |
| D-06 | — | `RECOMMENDED` | idem |
| D-13 | — | `RECOMMENDED` | idem |
| D-14 | — | `RECOMMENDED` | idem |
| D-27 | — | `RECOMMENDED` | idem |

**Adotado ≠ aprovado.** Nenhuma decisão está `APPROVED`. Não promova estado de
decisão no `docs/DECISION-REGISTER.md` — nem para "resolvida", nem para
"aprovada". Se uma tarefa parecer exigir uma decisão, registre a pergunta e
siga com o que já está adotado.

O `LICENSE` merece ênfase: criar o arquivo, mesmo com texto genérico, é escolher
uma licença. Não faça, mesmo que o build pareça precisar. Não precisa.

---

## 10. Regras de conduta

1. **Não invente resultado.** Se não rodou, escreva `BLOQUEADO` e o motivo.
2. **Não toque em `main`.** Trabalhe só na branch autorizada.
3. **Não escolha licença. Não crie `LICENSE`.**
4. **Não mude arquitetura** para facilitar empacotamento.
5. **Não relaxe teste de segurança** para a suíte ficar verde.
6. **Não declare validado** sem os critérios da §6.
7. **Não pare por detalhe técnico pequeno.** Resolva e siga.
8. **Bloqueio isolado não para o resto.** Use §7.7.
9. **Commit e push** na branch autorizada quando o trabalho estiver coerente.
   Sem merge, sem PR, sem force push.
10. **Relate o que só você pode ver.** A janela, o SmartScreen, o
    comportamento do antivírus — ninguém mais vai reportar.

---

## 11. Relatório final que você deve entregar

1. Estado Git antes (branch, HEAD, árvore) e depois (HEAD, commits, push).
2. Commit de referência e commit final.
3. Arquivos criados e alterados, com uma linha de motivo cada.
4. Componentes inspecionados, e o que a inspeção concluiu.
5. Comandos executados, com saída relevante colada.
6. Pré-requisitos de ambiente que você teve de instalar.
7. Matriz de testes preenchida (§5) com o estado real de cada um.
8. Bloqueadores por nível (P0/P1/P2/P3) e o que você fez com cada.
9. Riscos que precisam de decisão humana.
10. O que foi só inspecionado.
11. O que foi executado e validado de fato.
12. O que continua dependendo de humano.
13. A lista de diferenças entre o comportamento no Windows e no Linux.
14. Confirmação de que `main` ficou intacta (`git log origin/main -1`).

---

## Apêndice A — Solução de problemas

| Sintoma | Causa | Solução |
|---|---|---|
| `python` abre a Store | stub da Microsoft | instalar de python.org, marcar "Add to PATH" |
| `py` não encontrado | launcher não instalado | usar `python`, ou instalar Python pelo instalador oficial |
| `Activate.ps1` bloqueado | ExecutionPolicy | `Set-ExecutionPolicy -Scope Process RemoteSigned` |
| `ModuleNotFoundError: webview` | extra não instalado | `pip install "pywebview>=6.2"` |
| Janela não abre, sem erro | console suprimido | rodar `python -m lia_agenthub --browser` |
| Porta em uso | outra instância | é efêmera; feche a outra instância |
| `.exe` some ao abrir | antivírus | adicionar exclusão ou assinar (D-16) |
| SmartScreen bloqueia | sem assinatura | "Mais informações" → "Executar assim mesmo" |
| PyInstaller: `Permission denied` | `.exe` em execução | fechar o processo e refazer |
| Build > 100 MB | backend gráfico entrou | conferir `excludes` no spec |
| `ImportError: relative import` | entry point errado | spec deve apontar para `packaging/launcher.py` |
| Teste de symlink skipado | sem privilégio | esperado; registrar |
| `PermissionError` ao salvar | antivírus | retry já cobre; se persistir, reportar |
| Acento quebrado no terminal | code page | `chcp 65001`; não é bug do produto |

---

## Apêndice B — Mapa do repositório

```
src/lia_agenthub/
  __init__.py          APP_NAME, APP_ID, __version__
  __main__.py          CLI: argparse, logging, crash handler, janela
  app.py               AgentHub — casos de uso
  domain/
    skills.py          parsing de SKILL.md, frontmatter
    paths.py           MAX_PATH_LEN=200, check_relative_path
    unicode_policy.py  bidi/invisíveis: prosa vs código
    integrity.py       SHA-256, treeHash
    risk.py            regras transparentes, sem score
    model.py errors.py
  adapters/
    paths_resolver.py  ÚNICO lugar que monta caminho
    atomic.py          escrita atômica + retry (Windows)
    safe_extract.py    ZIP seguro
    repository.py importer.py packager.py index_builder.py
    platform_check.py  WebView2 via registro
    settings.py
  interface/
    server.py          HTTP local, token, CSP, _LocalServer
  resources/static/    index.html, app.css, app.js

packaging/
  launcher.py          entry point do bundle
  lia_agenthub.spec    receita PyInstaller

scripts/
  build_windows.ps1    build completo
  make_fixtures.py     14 fixtures sintéticas
  validate.sh test.sh dev.sh seed_demo.py run_dev.py

tests/                 284 testes
  unit/                73
  security/            76
  integration/         135
```

---

## PROMPT DE EXECUÇÃO PARA O CODEX

Copie o bloco abaixo inteiro. Ele é autossuficiente.

---

```text
MISSÃO: validar o MVP do Lia Agent Hub em Windows real, corrigir defeitos
concretos e produzir um .exe que funcione numa máquina sem Python.

Você está numa máquina Windows. O repositório é BloomRX/Lia-AgentHub.
Leia docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md antes de qualquer
comando. Ele é o plano; este prompt é a ordem. Em conflito, o documento vence
em detalhe técnico e este prompt vence em prioridade.

== REGRAS INEGOCIÁVEIS ==

1. Branch: arena/a92004be-lia-agenthub. NUNCA toque em main. Sem merge, sem
   PR, sem force push, sem trocar de branch.
2. Antes de começar, registre: git branch --show-current, git rev-parse HEAD,
   git status --short. Esperado: arena/a92004be-lia-agenthub, árvore limpa.
   O HEAD deve ser o commit que trouxe este documento ou descendente dele;
   obtenha-o com: git log --oneline -1 -- docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md
   Se divergir, PARE e reporte. Pode haver trabalho paralelo.
3. NUNCA invente resultado. Se não rodou, escreva BLOQUEADO e o motivo. Um
   relatório com três BLOQUEADOS honestos vale mais que um com trinta PASS
   inventados.
4. NUNCA crie LICENSE nem escolha licença. D-16 está aberta e isso NÃO bloqueia
   o trabalho. Não promova estado de decisão no DECISION-REGISTER.md.
5. NUNCA mude a arquitetura para facilitar o empacotamento. Conserte o defeito
   concreto. Se precisar de mudança estrutural, PARE e reporte.
6. NUNCA relaxe um teste de segurança para a suíte ficar verde. Se um teste de
   segurança falhar no Windows, isso é ACHADO DE SEGURANÇA, não bug do teste.
7. O produto NUNCA executa conteúdo importado. Se você vir isso acontecer, é
   P0 — pare tudo e reporte.

== ORDEM DE EXECUÇÃO ==

ESTÁGIO 1 — AMBIENTE
  py -3.12 -c "import sys;print(sys.version)"
  py -3.12 -m venv .venv
  .venv\Scripts\activate
  python -m pip install --upgrade pip
  python -m pip install -e ".[dev]"
  python -m pip install "pywebview>=6.2"
  python -c "import webview,PyInstaller,lia_agenthub;print('ok')"
  python -c "import platform;print(platform.machine())"
  python -c "from lia_agenthub.adapters.platform_check import detect_webview2 as d;s=d();print(s.available,s.version,s.reason)"
  SAÍDA: imports ok, Python 3.11-3.15, AMD64. Registre o estado do WebView2.

ESTÁGIO 2 — TESTES BASE
  python -m pytest -q
  SAÍDA ESPERADA: 284 passed (ou 283 passed, 1 skipped — o skip de symlink é
  legítimo; diga qual foi).
  Se falhar, classifique: falha de AMBIENTE (pacote não instalado, venv errado,
  path) ou falha REAL (comportamento Windows). Ambiente você conserta.
  Real você documenta e corrige. Use a tabela da seção 7, estágio 2.

ESTÁGIO 3 — EXECUÇÃO NATIVA
  python -m lia_agenthub --diagnostico
  python -m lia_agenthub
  (para o teste HTTP, use o roteiro em background da secao 3.B.1 --
   --no-window BLOQUEIA, nao retorna)
  PROVE quatro coisas SEPARADAMENTE (não escreva "UI validada" se só fez curl):
    a) backend responde: Invoke-WebRequest com e sem X-Lia-Token (403 / 200)
    b) janela nativa abriu: você está vendo na tela
    c) frontend carregou dentro da janela: a UI renderiza
    d) frontend chama a API: importe pela UI e veja a lista atualizar
  Feche a janela. Confirme: nenhum processo LiaAgentHub, nenhum msedgewebview2
  órfão, porta liberada.

ESTÁGIO 4 — FUNCIONAL COM ARQUIVOS REAIS
  python scripts\make_fixtures.py %TEMP%\lia-fx
  Rode F-01 a F-14 (seção 5.3). Depois I-01 a I-10 (seção 5.4).
  OBRIGATÓRIO: depois de importar a fixture 03, prove que NADA foi executado:
    dir /s /b PWNED.txt
  Vazio = correto. Se PWNED.txt aparecer, PARE: o produto executa conteúdo
  importado. É P0 de segurança.

ESTÁGIO 5 — BUILD
  powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
  (O script nunca foi executado — se quebrar por sintaxe, use:
   python -m PyInstaller --noconfirm --clean packaging\lia_agenthub.spec
   e registre o conserto que você fez no script.)
  SAÍDA: dist\LiaAgentHub.exe, 15-40 MB.
  Verifique o conteúdo:
    python -m PyInstaller.utils.cliutils.archive_viewer dist\LiaAgentHub.exe -l > build\contents.txt
    findstr /i "webview bottle lia_agenthub" build\contents.txt
  Confirmar: webview, bottle, lia_agenthub presentes; PyQt/gtk/pyside AUSENTES.

ESTÁGIO 6 — DISTRIBUIÇÃO
  Máquina SEM Python (ou VM limpa). Copie o .exe para C:\teste\. Rode D-01 a
  D-09 (seção 5.5).
  OBRIGATÓRIO: prove que nenhum segredo foi para o pacote:
    Select-String -Path dist\LiaAgentHub.exe -Pattern "sk-","ghp_","BEGIN PRIVATE","password=" -SimpleMatch
  Vazio = correto. Prove que o .exe não procura o repositório: mova-o para uma
  pasta onde o repo não exista e rode.
  Se não houver máquina limpa, marque D-* BLOQUEADO. NÃO declare validado.

== QUANDO ALGO TRAVAR ==

Bloqueio isolado não para o resto:
  Sem WebView2        -> rode tudo com --browser; M-01/M-06 BLOQUEADO
  Sem máquina limpa   -> estágios 1-5; D-* BLOQUEADO
  Script PS quebrado  -> build manual; registre o conserto
  Um teste falha      -> isole com pytest -k, conserte ou documente, siga
  Sem rede para pip   -> wheels locais; registre

Não pare por detalhe técnico pequeno. Resolva e siga.

== APÓS CADA CORREÇÃO ==
  python -m pytest -q
  Se a contagem mudar, explique (teste novo? removido?). Nunca deixe a suíte
  menor sem dizer por quê.

== COMMIT E PUSH ==
  Quando o trabalho estiver coerente, commit na branch autorizada e push.
  Sem merge, sem PR, sem force push. Se o push falhar por rede, mantenha os
  commits locais e diga por quê.

== RELATÓRIO FINAL (obrigatório, 14 itens) ==
  1.  Git antes (branch, HEAD, árvore) e depois (HEAD, commits, push)
  2.  Commit de referência e commit final
  3.  Arquivos criados/alterados, um motivo por linha
  4.  Componentes inspecionados e a conclusão de cada inspeção
  5.  Comandos executados, com a saída relevante colada
  6.  O que você teve de instalar no ambiente
  7.  Matriz de testes preenchida (seção 5) com estado REAL de cada linha
  8.  Bloqueadores P0/P1/P2/P3 e o que você fez com cada
  9.  Riscos que precisam de decisão humana
  10. O que foi só inspecionado
  11. O que foi executado e validado de fato
  12. O que continua dependendo de humano
  13. Diferenças de comportamento Windows vs Linux observadas
  14. Confirmação de que main ficou intacta (git log origin/main -1)

== CRITÉRIO DE "VALIDADO" ==
Só escreva "MVP validado no Windows" se TODOS forem verdade:
  A-01..A-04 PASS com saída colada
  M-01, M-04, M-05, M-06 PASS
  F-01, F-03, F-04, F-08, F-10, F-13 PASS (F-03 sem PWNED.txt)
  I-01, I-02, I-04, I-09 PASS
  D-01, D-02, D-05, D-08, D-09 PASS em máquina sem Python
  Nenhum P0 aberto; P1 abertos com contorno documentado
  Nenhum teste de segurança divergente sem explicação escrita

Caso contrário: "MVP NÃO validado no Windows" + a lista do que falhou. Não
existe "validado com ressalvas" para segurança.

Comece pelo Estágio 1. Não peça confirmação: o diagnóstico está no documento.
```
