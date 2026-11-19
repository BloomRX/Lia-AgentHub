<#
Materializa uma Skill fixada para o leitor e o build do Lia Studio.
O pacote e o manifesto devem estar disponíveis localmente.
#>
[CmdletBinding(DefaultParameterSetName='Python')]
param(
    [Parameter(Mandatory)][string]$StudioRoot,
    [Parameter(Mandatory)][ValidatePattern('^lia-(?!user-)[a-z0-9-]+$')][string]$SkillName,
    [Parameter(Mandatory)][string]$LockPath,
    [Parameter(Mandatory)][string]$PackagePath,
    [Parameter(Mandatory,ParameterSetName='Python')][string]$PythonExe,
    [Parameter(Mandatory,ParameterSetName='Packaged')][string]$HubCli,
    [string]$Revocations
)

$ErrorActionPreference = 'Stop'
$studio = (Resolve-Path -LiteralPath $StudioRoot).Path
$lockFile = (Resolve-Path -LiteralPath $LockPath).Path
$packageFile = (Resolve-Path -LiteralPath $PackagePath).Path
$prefix = @()
if ($PSCmdlet.ParameterSetName -eq 'Packaged') {
    $runner = (Resolve-Path -LiteralPath $HubCli).Path
} else {
    $runner = (Resolve-Path -LiteralPath $PythonExe).Path
    $prefix = @('-m','lia_agenthub')
}
if (!(Test-Path -LiteralPath (Join-Path $studio 'app/lia/skills.py') -PathType Leaf)) {
    throw "Leitor de Skills do Lia Studio ausente em $studio."
}
$pin = Get-Content -Raw -LiteralPath $lockFile -Encoding utf8 | ConvertFrom-Json
if ($pin.profile -cne 'lia-studio' -or $pin.capabilityId -cnotmatch ("^" + [regex]::Escape($SkillName) + "-[a-f0-9]{8}$")) {
    throw 'O manifesto precisa fixar esta Skill para o perfil lia-studio.'
}
$target = Join-Path $studio ".agents/skills/$SkillName"
$policyArgs = @()
if ($Revocations) {
    $policyArgs = @('--revocations',(Resolve-Path -LiteralPath $Revocations).Path)
}
& $runner @prefix skill materialize $lockFile $packageFile $target @policyArgs
if ($LASTEXITCODE -ne 0) { throw "Materialização recusada (código $LASTEXITCODE)." }
