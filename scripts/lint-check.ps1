#!/usr/bin/env pwsh
# Quick lint check - runs just linting checks (faster than full pre-commit)
# Run this frequently during development

$ErrorActionPreference = "Stop"

Write-Host "`n🔍 Quick Lint Check`n" -ForegroundColor Cyan

$failures = @()

# Backend Linting
Write-Host "Backend (ruff)..." -ForegroundColor Yellow
Push-Location gymbro-api
try {
    # Install ruff if needed
    python -m pip install ruff --quiet 2>$null
    
    # Run ruff via Python module (works even if not in PATH)
    python -m ruff check app/ tests/ --output-format=github
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Backend lint passed" -ForegroundColor Green
    } else {
        $failures += "Backend"
    }
} finally {
    Pop-Location
}

# Frontend Linting
Write-Host "`nFrontend (ESLint)..." -ForegroundColor Yellow
Push-Location gymbro-web
try {
    npm run lint --silent
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Frontend lint passed" -ForegroundColor Green
    } else {
        $failures += "Frontend"
    }
} finally {
    Pop-Location
}

# Summary
if ($failures.Count -eq 0) {
    Write-Host "`n✅ All linting passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ Linting failed in: $($failures -join ', ')" -ForegroundColor Red
    exit 1
}
