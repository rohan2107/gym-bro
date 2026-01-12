param(
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $scriptDir "..\gymbro-api"
$pythonExe = Join-Path $apiDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw ".venv not found at $pythonExe. From gymbro-api run: python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt"
}

Push-Location $apiDir
try {
    & $pythonExe -m uvicorn app.main:app --reload --host $ApiHost --port $Port
}
finally {
    Pop-Location
}
