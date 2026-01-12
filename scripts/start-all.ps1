# Starts backend (uvicorn) and frontend (vite dev) in separate terminals.
param(
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendScript = Join-Path $scriptDir "start-backend.ps1"
$frontendScript = Join-Path $scriptDir "start-frontend.ps1"

function Resolve-Shell {
    # Prefer pwsh if available; fall back to Windows PowerShell.
    $pwshPath = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
    if ($pwshPath) { return $pwshPath }
    return (Get-Command powershell -ErrorAction Stop).Source
}

$shell = Resolve-Shell

# Backend
Start-Process $shell -ArgumentList "-NoLogo", "-NoExit", "-File", $backendScript, "-ApiHost", $ApiHost, "-Port", $Port

# Frontend
Start-Process $shell -ArgumentList "-NoLogo", "-NoExit", "-File", $frontendScript
