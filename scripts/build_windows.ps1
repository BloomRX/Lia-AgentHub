<#
.SYNOPSIS
    Gera LiaAgentHub.exe e LiaAgentHubCli.exe com validação prévia.

.DESCRIPTION
    Sequência: confere Python -> cria venv -> instala dependências ->
    RODA OS TESTES (aborta se falharem) -> empacota -> confere o artefato.

    O executável NÃO é assinado digitalmente. Isso é decisão registrada
    (D-16 aberta): não há certificado de assinatura de código no projeto.

.PARAMETER SkipTests
    Pula a suíte. Só para diagnóstico. O artefato não deve ser distribuído.

.PARAMETER PythonExe
    Interpretador a usar (padrão: detecção automática).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipTests,
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

function Write-Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "   !   $msg" -ForegroundColor Yellow }
function Fail($msg)       { Write-Host "`nFALHA: $msg" -ForegroundColor Red; exit 1 }

Write-Host "Lia Agent Hub - build Windows" -ForegroundColor Cyan
Write-Host "Raiz: $root"

# ---------------------------------------------------------------- Python
Write-Step "1/6 Python"

# O stub da Microsoft Store responde a 'python' mas não executa nada de útil.
# A ordem que funciona no Windows: py launcher (-3.13, -3.12...), depois python.
function Find-Python {
    if ($PythonExe) { return $PythonExe }

    for ($minor = 15; $minor -ge 11; $minor--) {
        try {
            $exe = & py "-3.$minor" -c "import sys;print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe) { return $exe }
        } catch { }
    }
    foreach ($c in @("python", "python3")) {
        try {
            $v = & $c -c "import sys;print('%d.%d'%sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and $v -and $v -match '^3\.\d+') {
                if ($v -eq "3.10" -or $v -match '^3\.\d$') {
                    # pode ser o stub da Store devolvendo versão falsa
                    $exe = & $c -c "import sys;print(sys.executable)" 2>$null
                    if ($exe -match 'WindowsApps') {
                        Write-Warn "$c é o stub da Microsoft Store - ignorando"
                        continue
                    }
                }
                return $c
            }
        } catch { }
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Fail @"
Python 3.11+ nao encontrado.

Instale em https://www.python.org/downloads/windows/
Marque 'Add python.exe to PATH' no instalador.
Depois reabra o terminal e rode de novo.
"@
}

$ver = & $py -c "import sys;print('%d.%d'%sys.version_info[:2])"
$verOk = ($ver -match '^3\.(1[1-5])$')
Write-Host "   Interpretador: $py"
Write-Host "   Versão: $ver"
if (-not $verOk) { Fail "Python $ver nao e suportado. Use 3.11 a 3.15." }
Write-Ok "Python $ver"

# ---------------------------------------------------------------- venv
Write-Step "2/6 Ambiente virtual"
if (-not (Test-Path ".venv")) {
    & $py -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail "nao foi possivel criar o venv" }
    Write-Ok "venv criado"
} else {
    Write-Ok "venv existente reaproveitado"
}
$vpy = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $vpy)) { Fail "python do venv nao encontrado em $vpy" }

# ---------------------------------------------------------------- deps
Write-Step "3/6 Dependencias"
& $vpy -m pip install --quiet --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { Fail "pip upgrade falhou" }

Write-Host "   instalando pywebview + pyinstaller..."
& $vpy -m pip install --quiet "pywebview>=6.2" "pyinstaller>=6.0"
if ($LASTEXITCODE -ne 0) { Fail "instalacao de pywebview/pyinstaller falhou" }

& $vpy -m pip install --quiet -e ".[dev]"
if ($LASTEXITCODE -ne 0) { Fail "instalacao do pacote falhou" }

# Confere que os módulos realmente importam (pega wheel quebrada)
& $vpy -c "import webview, PyInstaller, lia_agenthub; print('import ok')"
if ($LASTEXITCODE -ne 0) { Fail "modulos nao importam apos install" }
Write-Ok "dependencias instaladas"

# ---------------------------------------------------------------- testes
Write-Step "4/6 Testes"
if ($SkipTests) {
    Write-Warn "testes PULADOS (-SkipTests). Nao distribua este artefato."
} else {
    & $vpy -m pytest -q
    if ($LASTEXITCODE -ne 0) {
        Fail "os testes falharam. Build abortado; nada foi empacotado."
    }
    Write-Ok "suíte passou"
}

# ---------------------------------------------------------------- build
Write-Step "5/6 Empacotamento"

& $vpy -m PyInstaller --noconfirm --clean packaging\lia_agenthub.spec
if ($LASTEXITCODE -ne 0) { Fail "PyInstaller falhou (veja a saida acima)" }

$exe = "dist\LiaAgentHub.exe"
if (-not (Test-Path $exe)) { Fail "executavel nao foi gerado em $exe" }
$mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
Write-Ok "gerado: $exe ($mb MB)"

& $vpy -m PyInstaller --noconfirm --clean packaging\lia_agenthub_cli.spec
if ($LASTEXITCODE -ne 0) { Fail "PyInstaller falhou no executavel de console" }
$cliExe = "dist\LiaAgentHubCli.exe"
if (-not (Test-Path $cliExe)) { Fail "executavel de console nao foi gerado em $cliExe" }
Write-Ok "gerado: $cliExe"

# ---------------------------------------------------------------- verificacao
Write-Step "6/6 Verificacao do artefato"

# O .exe tem console=False: --version nao imprime em terminal, mas o processo
# deve sair com codigo 0. Usamos o proprio teste de fumaca abaixo.
$p = Start-Process -FilePath $exe -ArgumentList "--version" -PassThru -Wait -WindowStyle Hidden
if ($p.ExitCode -ne 0) { Fail "o executavel saiu com codigo $($p.ExitCode)" }
Write-Ok "executavel inicia e encerra com codigo 0"

$helpText = & $cliExe skill --help
if ($LASTEXITCODE -ne 0 -or -not ($helpText -match "materialize")) {
    Fail "ajuda da CLI empacotada falhou"
}
Write-Ok "CLI empacotada imprime ajuda e encerra com codigo 0"

Write-Host ""
Write-Host "Artefatos: $((Resolve-Path $exe).Path), $((Resolve-Path $cliExe).Path)" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: o executavel NAO e assinado digitalmente." -ForegroundColor Yellow
Write-Host "O Windows pode exibir 'O Windows protegeu o computador'." -ForegroundColor Yellow
Write-Host "Isso e esperado para builds sem certificado de assinatura." -ForegroundColor Yellow
Write-Host ""
Write-Host "Antes de distribuir, rode os testes de fumaca manuais:" -ForegroundColor Cyan
Write-Host "  docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md secao 7" -ForegroundColor Cyan
exit 0
