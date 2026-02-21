# Pre-Commit Checklist

Use this checklist before committing code to ensure quality and avoid CI failures.

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
  - Frontend: `npm test -- --run` (34 tests)

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

## 🚀 Fast Pre-Commit Script

Create `scripts/pre-commit.ps1`:

```powershell
# Quick pre-commit check script
Write-Host "Running pre-commit checks..." -ForegroundColor Cyan

# Backend tests
Write-Host "`n📦 Backend Tests..." -ForegroundColor Yellow
cd gymbro-api
pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Backend tests failed!" -ForegroundColor Red
    exit 1
}

# Frontend tests
Write-Host "`n⚛️  Frontend Tests..." -ForegroundColor Yellow
cd ..\gymbro-web
npm test -- --run --reporter=basic
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend tests failed!" -ForegroundColor Red
    exit 1
}

# Frontend lint
Write-Host "`n🔍 Frontend Linting..." -ForegroundColor Yellow
npm run lint
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Linting failed!" -ForegroundColor Red
    exit 1
}

# Frontend type check
Write-Host "`n📘 TypeScript Check..." -ForegroundColor Yellow
npm run type-check
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Type checking failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ All checks passed! Ready to commit." -ForegroundColor Green
cd ..
```

Run before commit:
```bash
powershell -ExecutionPolicy Bypass -File scripts/pre-commit.ps1
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

## 📚 Resources

- [Testing Guide](TESTING_GUIDE.md) - Detailed testing documentation
- [Architecture](ARCHITECTURE.md) - System design and patterns
- [CI/CD Pipeline](../.github/workflows/ci.yml) - Automation configuration
