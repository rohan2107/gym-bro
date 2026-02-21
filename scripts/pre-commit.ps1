#!/usr/bin/env pwsh
# Pre-commit validation script
# Run this before committing to catch CI failures early

$ErrorActionPreference = "Stop"

Write-Host "`n🔍 Pre-Commit Validation`n" -ForegroundColor Cyan

# Track failures
$failures = @()

# 1. Backend Linting
Write-Host "1️⃣  Running backend linting (ruff)..." -ForegroundColor Yellow
Push-Location gymbro-api
try {
    # Install ruff if needed
    python -m pip install ruff --quiet 2>$null
    
    # Run ruff via Python module (works even if not in PATH)
    python -m ruff check app/ tests/ --output-format=github
    if ($LASTEXITCODE -ne 0) {
        $failures += "Backend linting"
    } else {
        Write-Host "   ✅ Backend linting passed" -ForegroundColor Green
    }
} catch {
    $failures += "Backend linting (error: $_)"
} finally {
    Pop-Location
}

# 2. Backend Tests
Write-Host "`n2️⃣  Running backend tests with coverage..." -ForegroundColor Yellow
Write-Host "   Target: 80% (excluding Phase 4 services - see .coveragerc)" -ForegroundColor DarkGray
Push-Location gymbro-api
try {
    # Set env var and use venv Python
    $pythonExe = ".venv/Scripts/python.exe"
    if (Test-Path $pythonExe) {
        # Pass env var directly to the process
        $env:JWT_SECRET_KEY = "test-secret-key"
        # Coverage config in .coveragerc - excludes app/services/* (Phase 4 WIP)
        & $pythonExe -m pytest -q --tb=short --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=80
        $testResult = $LASTEXITCODE
        Remove-Item env:JWT_SECRET_KEY -ErrorAction SilentlyContinue
    } else {
        $env:JWT_SECRET_KEY = "test-secret-key"
        python -m pytest -q --tb=short -n auto --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=80
        $testResult = $LASTEXITCODE
        Remove-Item env:JWT_SECRET_KEY -ErrorAction SilentlyContinue
    }
    
    if ($testResult -ne 0) {
        $failures += "Backend tests"
    } else {
        Write-Host "   ✅ Backend tests passed" -ForegroundColor Green
    }
} catch {
    $failures += "Backend tests (error: $_)"
} finally {
    Pop-Location
    Remove-Item env:JWT_SECRET_KEY -ErrorAction SilentlyContinue
}

# 3. Frontend Linting
Write-Host "`n3️⃣  Running frontend linting (ESLint)..." -ForegroundColor Yellow
Push-Location gymbro-web
try {
    npm run lint --silent
    if ($LASTEXITCODE -ne 0) {
        $failures += "Frontend linting"
    } else {
        Write-Host "   ✅ Frontend linting passed" -ForegroundColor Green
    }
} catch {
    $failures += "Frontend linting (error: $_)"
} finally {
    Pop-Location
}

# 4. Frontend Type Checking
Write-Host "`n4️⃣  Running frontend type checking..." -ForegroundColor Yellow
Push-Location gymbro-web
try {
    npm run type-check --silent
    if ($LASTEXITCODE -ne 0) {
        $failures += "Frontend type checking"
    } else {
        Write-Host "   ✅ Frontend type checking passed" -ForegroundColor Green
    }
} catch {
    $failures += "Frontend type checking (error: $_)"
} finally {
    Pop-Location
}

# 5. Frontend Tests
Write-Host "`n5️⃣  Running frontend tests with coverage..." -ForegroundColor Yellow
Push-Location gymbro-web
try {
    npm test -- --run --coverage --reporter=verbose
    if ($LASTEXITCODE -ne 0) {
        $failures += "Frontend tests"
    } else {
        Write-Host "   ✅ Frontend tests passed" -ForegroundColor Green
    }
} catch {
    $failures += "Frontend tests (error: $_)"
} finally {
    Pop-Location
}

# Summary
Write-Host "`n" + ("="*50) -ForegroundColor Cyan
if ($failures.Count -eq 0) {
    Write-Host "✅ All checks passed! Safe to commit." -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Pre-commit validation FAILED:" -ForegroundColor Red
    foreach ($failure in $failures) {
        Write-Host "   - $failure" -ForegroundColor Red
    }
    Write-Host "`nFix these issues before committing." -ForegroundColor Yellow
    exit 1
}
