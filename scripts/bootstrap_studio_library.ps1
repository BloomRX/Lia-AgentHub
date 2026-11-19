[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$StudioRoot,
    [Parameter(Mandatory)][string]$ManifestPath,
    [Parameter(Mandatory)][string]$PythonExe
)

$ErrorActionPreference = 'Stop'
$studio = (Resolve-Path -LiteralPath $StudioRoot).Path
$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$runner = (Resolve-Path -LiteralPath $PythonExe).Path
$manifest = Get-Content -Raw -LiteralPath $manifestFile -Encoding utf8 | ConvertFrom-Json
if ($manifest.manifestVersion -ne 1 -or $manifest.profile -cne 'lia-studio' -or !$manifest.skills.Count) {
    throw 'Manifesto de biblioteca Studio inválido.'
}
$entries = @{}
$paths = Split-Path -Parent $manifestFile
foreach ($entry in $manifest.skills) {
    if ($entry.name -cnotmatch '^lia-(?!user-)[a-z0-9-]+$' -or $entries.ContainsKey($entry.name)) {
        throw 'Nome de Skill inválido ou duplicado.'
    }
    foreach ($file in @($entry.lock,$entry.package)) {
        if ($file -cnotmatch '^[a-zA-Z0-9_-][a-zA-Z0-9_.-]*$') {
            throw 'O manifesto precisa referenciar arquivos ao lado dele, sem caminhos.'
        }
    }
    $lockFile = Join-Path $paths $entry.lock
    $packageFile = Join-Path $paths $entry.package
    $pin = Get-Content -Raw -LiteralPath $lockFile -Encoding utf8 | ConvertFrom-Json
    $target = Join-Path $studio ".agents/skills/$($entry.name)"
    if (Test-Path -LiteralPath $target) {
        throw "Destino já existe: $target"
    }
    if ((Get-FileHash -LiteralPath $packageFile).Hash -ine $pin.packageSha256) {
        throw "Pacote diverge do manifesto: $($entry.name)"
    }
    $entries[$entry.name] = @{
        StudioRoot=$studio;SkillName=$entry.name;LockPath=$lockFile
        PackagePath=$packageFile;PythonExe=$runner
    }
}

foreach ($name in ($entries.Keys | Sort-Object)) {
    $arguments = $entries[$name]
    & (Join-Path $PSScriptRoot 'bootstrap_studio_skill.ps1') @arguments
}
