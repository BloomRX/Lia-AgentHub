# Build do executável do Lia Agent Hub (Windows).
# Uso:  powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

Write-Host "== Lia Agent Hub: build ==" -ForegroundColor Cyan

$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "py" }
$ver = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python: $ver"
if ([version]$ver -lt [version]"3.11") {
    throw "Python 3.11 ou superior é necessário. Encontrado: $ver"
}

if (-not (Test-Path ".venv")) {
    Write-Host "Criando ambiente virtual..."
    & $py -m venv .venv
}
$vpy = ".\.venv\Scripts\python.exe"

& $vpy -m pip install --quiet --upgrade pip
& $vpy -m pip install --quiet "pyinstaller>=6.0" "pywebview>=6.2"
& $vpy -m pip install --quiet -e .

Write-Host "Rodando testes antes de empacotar..."
& $vpy -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Os testes falharam. Build abortado." }

Write-Host "Gerando executável..."
& $vpy -m PyInstaller --noconfirm --clean packaging\lia_agenthub.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou." }

$exe = "dist\LiaAgentHub.exe"
if (-not (Test-Path $exe)) { throw "Executável não foi gerado." }
$mb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
Write-Host "OK: $exe ($mb MB)" -ForegroundColor Green
Write-Host ""
Write-Host "O executável NÃO é assinado digitalmente. O Windows pode mostrar" -ForegroundColor Yellow
Write-Host "'SmartScreen protegeu o computador'. Isso é esperado para builds" -ForegroundColor Yellow
Write-Host "sem certificado de assinatura de código." -ForegroundColor Yellow
