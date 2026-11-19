param([string]$OutputPath = (Join-Path $env:TEMP 'lia-skills-source-inventory.json'))

$ErrorActionPreference = 'Stop'
$sources = @(
    @{ Name = 'Lia-AgentHub'; Ref = '7eb65a48a7ecdea91ec000c7916d3b96872bf726' }
    @{ Name = 'Lia-Project'; Ref = '9778ffb83611eecfd2fecdd8ba8b046b344b2ad3' }
    @{ Name = 'Lia-Studio'; Ref = 'b099c4ad6b1d26b7e857290fcb333e311b8ae515' }
    @{ Name = 'Lia-Forge-2.0'; Ref = '4b4c7146464cc98e9432468d2334eb67e1a506f2' }
    @{ Name = 'Lia-Model-Lab'; Ref = $null }
    @{ Name = 'Lia-Go'; Ref = 'be218893a5da3094417fe162675f013302500e41' }
    @{ Name = 'Lia-Research'; Ref = '33074e280cb557ac23537eac9a6883a0b89d0283' }
)

$result = foreach ($source in $sources) {
    if (!$source.Ref) {
        [pscustomobject]@{ project = $source.Name; commit = $null; status = 'revision-unresolved'; skills = $null }
        continue
    }

    $endpoint = "repos/BloomRX/$($source.Name)/git/trees/$($source.Ref)?recursive=1"
    $json = gh api $endpoint 2>$null
    if ($LASTEXITCODE -ne 0) {
        [pscustomobject]@{ project = $source.Name; commit = $source.Ref; status = 'tree-unavailable'; skills = $null }
        continue
    }
    $tree = $json | ConvertFrom-Json
    if ($tree.truncated) {
        [pscustomobject]@{ project = $source.Name; commit = $source.Ref; status = 'tree-truncated'; skills = $null }
        continue
    }

    $skills = @(
        foreach ($entry in $tree.tree) {
            if ($entry.type -ne 'blob' -or $entry.path -cnotmatch '(^|/)SKILL\.md$') { continue }
            $directory = $entry.path -replace '(^|/)SKILL\.md$', ''
            $files = @($tree.tree | Where-Object {
                $_.type -eq 'blob' -and ($_.path -eq $entry.path -or
                    ($directory -ne '' -and $_.path.StartsWith("$directory/", [StringComparison]::Ordinal)))
            } | Select-Object path, sha, mode)
            [pscustomobject]@{ path = $entry.path; blob = $entry.sha; files = $files; disposition = 'review-pending' }
        }
    )
    [pscustomobject]@{ project = $source.Name; commit = $source.Ref; status = 'tree-inventoried'; skills = $skills }
}

ConvertTo-Json -InputObject @($result) -Depth 10 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$result | Select-Object project, commit, status, @{n='count';e={if ($null -ne $_.skills) { $_.skills.Count }}} | Format-Table
