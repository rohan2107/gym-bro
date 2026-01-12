param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$webDir = Join-Path $scriptDir "..\gymbro-web"

Push-Location $webDir
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing frontend dependencies..."
        npm install
    }

    if ($Build) {
        npm run build
    } else {
        npm run dev
    }
}
finally {
    Pop-Location
}
