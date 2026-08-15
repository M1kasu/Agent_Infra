param(
    [string]$ManagerWorkspace = (Join-Path $env:USERPROFILE "agentteams-manager")
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$policyPath = Join-Path $projectRoot "agentteams\manager-officeops-policy.md"
$policy = (Get-Content -LiteralPath $policyPath -Raw).Trim()
$beginMarker = "<!-- officeops-policy-begin -->"
$endMarker = "<!-- officeops-policy-end -->"
$block = "$beginMarker`r`n$policy`r`n$endMarker"

function Sync-Policy {
    param([string]$Target)

    if (-not (Test-Path -LiteralPath $Target)) {
        throw "Manager SOUL.md not found: $Target"
    }

    $content = Get-Content -LiteralPath $Target -Raw
    $start = $content.IndexOf($beginMarker, [StringComparison]::Ordinal)
    if ($start -ge 0) {
        $end = $content.IndexOf($endMarker, $start, [StringComparison]::Ordinal)
        if ($end -lt 0) {
            throw "Incomplete OfficeOps policy markers in $Target"
        }
        $end += $endMarker.Length
        $content = $content.Remove($start, $end - $start).Insert($start, $block)
    }
    elseif ($content.Contains("### OfficeOps 固定协同协议")) {
        Write-Host "OfficeOps policy already present: $Target"
        return
    }
    else {
        $anchor = "<!-- agentteams-builtin-end -->"
        $index = $content.IndexOf($anchor, [StringComparison]::Ordinal)
        if ($index -ge 0) {
            $content = $content.Insert($index, "$block`r`n`r`n")
        }
        else {
            $content = "$($content.TrimEnd())`r`n`r`n$block`r`n"
        }
    }

    [IO.File]::WriteAllText($Target, $content, [Text.UTF8Encoding]::new($false))
    Write-Host "OfficeOps policy synchronized: $Target"
}

Sync-Policy -Target (Join-Path $ManagerWorkspace "SOUL.md")
Sync-Policy -Target (Join-Path $ManagerWorkspace ".qwenpaw\workspaces\default\SOUL.md")
