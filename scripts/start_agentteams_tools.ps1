param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeDir = Join-Path $projectRoot "artifacts\runtime"
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

function Test-LocalPort {
    param([int]$Port)
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $client.Connect("127.0.0.1", $Port)
        return $true
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Start-OfficeOpsProcess {
    param(
        [string]$Name,
        [int]$Port,
        [string[]]$Arguments
    )
    if (Test-LocalPort -Port $Port) {
        Write-Host "$Name already listening on $Port"
        return $null
    }
    $stdout = Join-Path $runtimeDir "$Name.stdout.log"
    $stderr = Join-Path $runtimeDir "$Name.stderr.log"
    $process = Start-Process `
        -FilePath $Python `
        -ArgumentList $Arguments `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    Write-Host "$Name started (pid=$($process.Id), port=$Port)"
    return $process
}

$processes = @()
$processes += Start-OfficeOpsProcess `
    -Name "sandbox-api" `
    -Port 18100 `
    -Arguments @("-m", "uvicorn", "sandbox.api:app", "--host", "0.0.0.0", "--port", "18100")
$processes += Start-OfficeOpsProcess `
    -Name "mcp-readonly" `
    -Port 18101 `
    -Arguments @("-m", "sandbox.mcp_server", "--profile", "readonly", "--port", "18101")
$processes += Start-OfficeOpsProcess `
    -Name "mcp-remediation" `
    -Port 18102 `
    -Arguments @("-m", "sandbox.mcp_server", "--profile", "remediation", "--port", "18102")

$deadline = (Get-Date).AddSeconds(30)
do {
    $ready = (@(18100, 18101, 18102) | Where-Object { -not (Test-LocalPort -Port $_) }).Count -eq 0
    if ($ready) { break }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

if (-not $ready) {
    throw "OfficeOps services did not become ready; inspect $runtimeDir"
}

$health = Invoke-RestMethod -Uri "http://127.0.0.1:18100/apps/docs/health"
if ($health.status -ne "healthy") {
    throw "Sandbox health probe failed"
}

Write-Host "OfficeOps sandbox and role-scoped MCP services are ready."
