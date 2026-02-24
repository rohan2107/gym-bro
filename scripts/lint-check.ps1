#!/usr/bin/env pwsh
# Quick lint check - runs just linting checks (faster than full pre-commit)
# Run this frequently during development
#
# Usage:
#   .\scripts\lint-check.ps1        # Check only (exit 1 on errors)
#   .\scripts\lint-check.ps1 -Fix   # Auto-fix issues where possible

param(
    [switch]$Fix = $false
)

$ErrorActionPreference = "Stop"

Write-Host "`n🔍 Quick Lint Check`n" -ForegroundColor Cyan

$failures = @()

# Backend Linting
if ($Fix) {
    Write-Host "Backend (ruff --fix)..." -ForegroundColor Yellow
} else {
    Write-Host "Backend (ruff)..." -ForegroundColor Yellow
}
Push-Location gymbro-api
try {
    # Install ruff if needed
    python -m pip install ruff --quiet 2>$null
    
    # Run ruff via Python module (works even if not in PATH)
    if ($Fix) {
        python -m ruff check app/ tests/ --fix
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Backend lint fixed and passed" -ForegroundColor Green
        } else {
            $failures += "Backend"
        }
    } else {
        python -m ruff check app/ tests/ --output-format=github
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Backend lint passed" -ForegroundColor Green
        } else {
            Write-Host "   💡 Tip: Run with -Fix flag to auto-fix issues" -ForegroundColor DarkGray
            $failures += "Backend"
        }
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
