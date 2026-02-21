#!/usr/bin/env pwsh
# Quick test to time backend tests

$ErrorActionPreference = "Stop"

Write-Host "Timing backend tests..." -ForegroundColor Cyan

Push-Location gymbro-api

$env:JWT_SECRET_KEY = "test-secret-key"

$timer = [Diagnostics.Stopwatch]::StartNew()
.venv/Scripts/python.exe -m pytest -q --tb=short
$exitCode = $LASTEXITCODE
$timer.Stop()

Remove-Item env:JWT_SECRET_KEY -ErrorAction SilentlyContinue

Pop-Location

Write-Host "`nTotal time: $($timer.Elapsed.TotalSeconds) seconds" -ForegroundColor $(if ($exitCode -eq 0) { "Green" } else { "Red" })

exit $exitCode
