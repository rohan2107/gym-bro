# Pre-Commit Checklist

Use this checklist before committing code to ensure quality and avoid CI failures.

## 🎯 Modus Operandi (Standard Workflow)

**Daily Development Cycle:**

1. **While Coding** → Run quick lint check frequently:
   ```powershell
   .\scripts\lint-check.ps1
   ```
   - Catches syntax errors immediately
   - Takes ~10 seconds
   - Run after every significant change

2. **Before Committing** → Run full validation:
   ```powershell
   .\scripts\pre-commit.ps1
   ```
   - Runs all tests + linting + type checking
   - Takes ~30-60 seconds
   - Catches 99% of CI failures
   - **Only commit if this passes**

3. **After Committing** → Monitor CI pipeline:
   - GitHub Actions runs automatically
   - Should pass if pre-commit passed
   - If CI fails, fix immediately and force-push

**Why This Matters:**
- ❌ **Bad**: Commit → Push → CI fails → Fix → Commit → Push (wastes time)
- ✅ **Good**: Lint check → Pre-commit → Commit → Push → CI passes (efficient)

---

## ✅ Quick Checklist

```bash
# 1. Run all tests
cd gymbro-api && pytest -q && cd ..\gymbro-web && npm test -- --run

# 2. Check backend linting (if ruff installed)
cd gymbro-api && ruff check app/ tests/

# 3. Check frontend linting
cd gymbro-web && npm run lint

# 4. Type check frontend
cd gymbro-web && npm run type-check

# 5. Verify build succeeds
cd gymbro-web && npm run build
```

## 📋 Detailed Checklist

### Before Every Commit

- [ ] **All tests pass**
  - Backend: `pytest -v` (47 tests)
  - Frontend: `npm run test:run` (27 tests)

- [ ] **No linting errors**
  - Backend: `ruff check app/ tests/` (optional)
  - Frontend: `npm run lint`

- [ ] **Type checking passes**
  - Frontend: `npm run type-check`

- [ ] **Code builds successfully**
  - Frontend: `npm run build`

- [ ] **No sensitive data committed**
  - Check for API keys, passwords, tokens
  - Review `.env` files (should not be committed)

- [ ] **Remove debug code**
  - Remove `console.log()` statements
  - Remove commented-out code blocks
  - Remove test data/debugging endpoints

### Before Pull Request

- [ ] **Branch is up to date**
  ```bash
  git fetch origin
  git rebase origin/main
  ```

- [ ] **Commit messages are clear**
  - Use conventional format: `feat:`, `fix:`, `test:`, `docs:`, `chore:`
  - Example: `feat(auth): add JWT token refresh`

- [ ] **Documentation updated**
  - README if adding features
  - API docs if changing endpoints
  - Comments for complex logic

- [ ] **Tests cover new code**
  - Add unit tests for new functions
  - Add integration tests for new endpoints
  - Update existing tests if changing behavior

- [ ] **No breaking changes** (or documented)
  - Check if API changes affect frontend
  - Check if model changes require migration

### Before Merge to Main

- [ ] **All CI checks pass**
  - Backend tests ✓
  - Backend linting ✓
  - Frontend tests ✓
  - Frontend linting ✓
  - Frontend type check ✓
  - Frontend build ✓

- [ ] **Code reviewed**
  - At least one approval (if team)
  - Address all review comments

- [ ] **Conflicts resolved**
  - Rebase on latest main
  - Resolve any merge conflicts

- [ ] **Deployment plan ready** (if needed)
  - Database migrations prepared
  - Environment variables documented
  - Rollback plan documented

## 🚀 Automated Pre-Commit Scripts

Two scripts are available in `scripts/`:

### Quick Lint Check (Recommended for Frequent Use)
**Run this after every code change:**
```powershell
.\scripts\lint-check.ps1
```

- ✅ Fast (~10 seconds)
- ✅ Catches 80% of CI failures
- ✅ Runs ruff + ESLint only

### Full Pre-Commit Validation (Before Committing)
**Run this before every commit:**
```powershell
.\scripts\pre-commit.ps1
```

- ✅ Complete (~30-60 seconds)
- ✅ Runs all CI checks locally
- ✅ Backend linting + tests
- ✅ Frontend linting + type check + tests

### Manual Commands (If Scripts Fail)

If you need to run checks manually:

```powershell
# Backend linting only
cd gymbro-api
python -m ruff check app/ tests/ --output-format=github

# Backend linting with auto-fix
python -m ruff check app/ tests/ --fix

# Frontend linting
cd gymbro-web
npm run lint

# Frontend linting with auto-fix
npm run lint -- --fix
```

## 🔧 Git Hooks (Optional)

Set up automatic pre-commit checks:

Create `.git/hooks/pre-commit` (no extension):

```bash
#!/bin/sh
# Run tests before allowing commit

echo "Running pre-commit checks..."

# Backend tests
cd gymbro-api
pytest -q || exit 1

# Frontend tests
cd ../gymbro-web
npm test -- --run || exit 1

echo "✅ All checks passed"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## 📝 Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding/updating tests
- `docs`: Documentation only
- `chore`: Maintenance (dependencies, configs)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `style`: Formatting, missing semicolons, etc.
- `perf`: Performance improvements

**Examples:**
```
feat(auth): add Google OAuth login

Implement OAuth 2.0 flow with JWT tokens.
Users can now sign in with their Google accounts.

Closes #42

---

fix(meals): correct calorie calculation for imperial units

The calorie calculation was using metric values for imperial inputs.
Now correctly converts before calculation.

Fixes #38

---

test(workouts): add CRUD operation tests

Add comprehensive test coverage for workout endpoints.
Includes user isolation and error handling tests.

Coverage: 47 tests passing
```

## 🐛 Common Issues

**Tests pass locally but fail in CI:**
- Check if `.env` variables are set in CI
- Verify dependencies are locked (package-lock.json committed)
- Check for platform-specific code (Windows vs Linux)

**Type errors in CI but not locally:**
- Run `npm run type-check` locally
- Update TypeScript: `npm install -D typescript@latest`

**Build succeeds locally but fails in CI:**
- Clear node_modules and reinstall: `rm -r node_modules && npm install`
- Check for missing files in .gitignore

## � Common Lint Errors & Quick Fixes

### Backend (Ruff)

**F401: Module imported but unused**
```python
# ❌ Bad
from datetime import date, datetime  # datetime unused
from sqlmodel import Session, select  # select unused

# ✅ Good - Only import what you use
from datetime import date
from sqlmodel import Session
```

**F841: Local variable assigned but never used**
```python
# ❌ Bad
result = calculate_tdee()  # Never used

# ✅ Good - Remove or use it
_ = calculate_tdee()  # If intentionally ignored
```

**E501: Line too long**
```python
# ❌ Bad (>88 chars)
def very_long_function_name_with_many_parameters(param1, param2, param3, param4, param5):

# ✅ Good - Break into multiple lines
def very_long_function_name_with_many_parameters(
    param1, param2, param3, param4, param5
):
```

**I001: Import block is un-sorted**
```python
# ❌ Bad - imports not sorted
from typing import Dict
from datetime import date
import os

# ✅ Good - standard lib → third party → local
import os
from datetime import date
from typing import Dict

from fastapi import APIRouter
from sqlmodel import Session

from ..models import User
```

### Frontend (ESLint)

**Unused imports**
```typescript
// ❌ Bad
import { useState, useEffect } from 'react'  // useEffect unused

// ✅ Good
import { useState } from 'react'
```

**Missing dependency in useEffect**
```typescript
// ❌ Bad
useEffect(() => {
  fetchData(userId)
}, [])  // Missing userId dependency

// ✅ Good
useEffect(() => {
  fetchData(userId)
}, [userId])
```

### Auto-Fix Commands

```powershell
# Backend - auto-fix most issues
python -m ruff check app/ tests/ --fix

# Frontend - auto-fix most issues
npm run lint -- --fix
```

## �📚 Resources

- [Testing Guide](TESTING_GUIDE.md) - Detailed testing documentation
- [Architecture](ARCHITECTURE.md) - System design and patterns
- [CI/CD Pipeline](../.github/workflows/ci.yml) - Automation configuration
