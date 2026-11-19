[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$StudioRoot,
    [Parameter(Mandatory)][string]$ManifestPath,
    [Parameter(Mandatory)][string]$PythonExe
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$studio = (Resolve-Path -LiteralPath $StudioRoot).Path
$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$runner = (Resolve-Path -LiteralPath $PythonExe).Path
$manifest = Get-Content -Raw -LiteralPath $manifestFile -Encoding utf8 | ConvertFrom-Json
if ($manifest.manifestVersion -ne 1 -or $manifest.profile -cne 'lia-studio' -or !$manifest.skills.Count) {
    throw 'Manifesto de biblioteca Studio inválido.'
}
if (!(Test-Path -LiteralPath (Join-Path $studio 'app/lia/skills.py') -PathType Leaf)) {
    throw "Leitor de Skills do Lia Studio ausente em $studio."
}
$skillDirectory = Join-Path $studio '.agents/skills'
foreach ($directory in @((Split-Path -Parent $skillDirectory),$skillDirectory)) {
    if (Test-Path -LiteralPath $directory) {
        $item = Get-Item -LiteralPath $directory -Force
        if (!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Diretório de Skills inválido: $directory"
        }
    }
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
    if ($pin.profile -cne 'lia-studio' -or $pin.capabilityId -cnotmatch ("^" + [regex]::Escape($entry.name) + "-[a-f0-9]{8}$")) {
        throw "Manifesto incompatível com a Skill: $($entry.name)"
    }
    $target = Join-Path $skillDirectory $entry.name
    if (Test-Path -LiteralPath $target) {
        throw "Destino já existe: $target"
    }
    if ((Get-FileHash -LiteralPath $packageFile).Hash -ine $pin.packageSha256) {
        throw "Pacote diverge do manifesto: $($entry.name)"
    }
    $entries[$entry.name] = @{
        lock=$lockFile; package=$packageFile; target=$target
    }
}

$stagePath = Join-Path $studio ".lia-studio-skills-$([guid]::NewGuid())"
$names = @($entries.Keys | Sort-Object)
$moved = [Collections.Generic.List[string]]::new()
New-Item -ItemType Directory -Path $stagePath | Out-Null
try {
    foreach ($name in $names) {
        $entry = $entries[$name]
        $staged = Join-Path $stagePath $name
        & $runner -m lia_agenthub skill materialize $entry.lock $entry.package $staged | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Pacote recusado: $name (código $LASTEXITCODE)." }
    }

    New-Item -ItemType Directory -Path $skillDirectory -Force | Out-Null
    try {
        foreach ($name in $names) {
            [IO.Directory]::Move((Join-Path $stagePath $name), $entries[$name].target)
            $moved.Add($name)
        }
    } catch {
        foreach ($name in $moved) {
            [IO.Directory]::Move($entries[$name].target, (Join-Path $stagePath $name))
        }
        throw
    }
} catch {
    Write-Warning "Arquivos preparados para diagnóstico em $stagePath"
    throw
}
[IO.Directory]::Delete($stagePath)
[pscustomobject]@{profile='lia-studio'; skills=$names; directory=$skillDirectory}
