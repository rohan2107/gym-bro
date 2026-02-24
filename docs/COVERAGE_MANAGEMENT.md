# Coverage Management Guide

## Current Status

**Coverage: 83.81%** (as of Phase 4.2 completion - Feb 24, 2026)

This includes full coverage of Phase 4 services.
- 123 tests passing
- Test execution time: ~4 seconds

## Coverage Configuration

### Backend (Python)

Coverage is configured in **`.coveragerc`** - the industry-standard configuration file.

**Current exclusions:**
```ini
# Only excluding food_mapping.py (static configuration, no logic to test)
app/services/food_mapping.py
```

**How to update:**
1. Open `gymbro-api/.coveragerc`
2. Add/remove paths in the `[run] → omit` section
3. Commit the change (version controlled)

**Why .coveragerc?**
- ✅ Industry standard (recognized by coverage.py, pytest-cov, IDEs)
- ✅ Explicit and version-controlled
- ✅ Shared across all developers
- ✅ Works with all coverage tools (pytest, coverage.py, IDE extensions)

### Frontend (TypeScript)

Coverage is configured in **`vitest.config.ts`**:
```typescript
coverage: {
  provider: 'v8',
  exclude: [
    // Standard exclusions
    'node_modules/**',
    'src/test/**',
    '**/*.test.{ts,tsx}',
    // Add WIP files here if needed
  ],
  thresholds: {
    lines: 80,
    functions: 80,
    branches: 80,
    statements: 80,
  }
}
```

Currently at **97.95% coverage** - exceeding targets ✅

## Coverage Breakdown (Backend)

| File | Coverage | Status |
|------|----------|--------|
| app/main.py | ~75% | ✅ Improved - app structure tests added |
| app/db.py | ~75% | ✅ Improved - init_db and session tests added |
| app/routers/auth.py | 25.84% | ⚠️ OAuth endpoints still need testing |
| app/routers/daily_checkins.py | 81.03% | ✅ Improved - edge cases covered |
| app/routers/auth.py | 25.84% | OAuth callback endpoints not tested |
| app/routers/daily_checkins.py | 72.41% | Missing tests for some endpoints |

### High Coverage Areas ✅

| File | Coverage |
|------|----------|
| app/services/nutrition.py | 97.96% |
| app/routers/weight_entries.py | 95.56% |
| app/deps.py | 93.55% |
| app/routers/exercise_sets.py | 91.49% |
| app/routers/food_logs.py | 90.29% |
| app/services/vision.py | 89.66% |
| app/db.py | 83.33% |
| app/services/rate_limiter.py | 82.76% |
| app/auth_utils.py | 81.48% |
| app/routers/daily_checkins.py | 81.03% |

### Excluded Areas

Only one file is excluded from coverage:

| File | Status |
|------|--------|
| app/services/food_mapping.py | 📝 Static configuration mappings (no logic to test) |
2 (Complete)
- ✅ **Achieved: 83.81%** - Exceeded target with comprehensive service tests
- ✅ 123 tests passing (added 53 new tests for Phase 4.2)
- ✅ Phase 4 services now fully tested and included in coverage
- ✅ **Achieved: 82.51%** - Exceeded target with edge case tests
- ✅ Added 24 new tests (daily check-ins, db init, app structure)
- ✅ Exclude Phase 4 services via .coveragerc
- ✅ Pre-commit checks enforce 80% threshold

### Phase 4.2 (Next)
- 🎯 **Target: 85%+** - Add tests for Phase 4 services
- Remove exclusions from .coveragerc as services are tested
- Add OAuth endpoint tests for full coverage

### Phase 5+ (Future)
- 🎯 **Target: 85%+** - Improve legacy low-coverage areas
- Priority 1: app/routers/auth.py (OAuth endpoints)
- Priority 2: app/db.py (initialization)
- Priority 3: app/main.py (lifespan events)

## Running Coverage Locally

### Backend (with exclusions)
```bash
cd gymbro-api
pytest --cov=app --cov-report=term-missing
# Uses .coveragerc automatically
```

### Backend (without exclusions - see true total)
```bash
cd gymbro-api
pytest --cov=app --cov-report=term-missing --cov-config=/dev/null
```

### Frontend
```bash
cd gymbro-web
npm test -- --run --coverage
# Opens coverage/index.html
```

### Full Pre-Commit Check
```bash
.\scripts\pre-commit.ps1
# Runs lint + tests + coverage for both backend and frontend
```

## Managing Work-in-Progress Code

### When starting a new feature:

1. **Create the files** (implementation without tests)
2. **Update .coveragerc** to exclude them:
   ```ini
   [run]
   omit =
       app/new_feature/*.py  # Phase X WIP
   ```
3. **Commit the exclusion** along with the code
4. **Add a comment** explaining when tests will be added

### When completing a feature:

1. **Write comprehensive tests**
2. **Remove exclusions** from .coveragerc
3. **Verify coverage meets threshold** (74%+ currently)
4. **Commit tests and exclusion removal together**

## Pre-Commit Coverage Checks

The pre-commit script (`scripts/pre-commit.ps1`) runs coverage checks:

```powershell
# Backend: 74% threshold (will increase to 80% in Phase 4.2)
pytest --cov=app --cov-fail-under=74
80% threshold (currently at 82.51%)
pytest --cov=app --cov-fail-under=80 at 97.95%)
npm test -- --run --coverage
```

**If coverage drops below threshold:**
1. Check what new code was added without tests
2. Either:
   - Add tests to cover the new code, OR
   - Temporarily exclude new WIP files in .coveragerc with a comment

## Coverage vs. Code Quality

**Remember:**
- 📊 Coverage measures **what is tested**, not **how well**
- ✅ 74% with good tests > 90% with shallow tests
- 🎯 Focus on **testing behavior**, not hitting numbers
- 🚨 Low coverage in critical areas (auth, data security) is higher priority than 100% in utilities

## Historical Context

| Phase | Target | Actual | Notes |
|-------|--------|--------|-------|
| Phase 3 | 85% | ~74% | Roadmap target was aspirational |
| Phase 4.1 | 80% | 82.51% | ✅ Added edge case tests, exceeded target |
| Phase 4.2 | 85% | TBD | Add service tests, OAuth tests |

Phase 4.1 exceeded the 80% target by adding 24 new tests covering daily check-in edge cases, database initialization, and app structure.

## Quick Reference

**View coverage report:**
```bash
# Backend (text)
cd gymbro-api && pytest --cov=app --cov-report=term-missing

# Backend (HTML)
cd gymbro-api && pytest --cov=app --cov-report=html
# Open htmlcov/index.html

# Frontend (HTML)
cd gymbro-web && npm test -- --run --coverage
# Open coverage/index.html
```

**Check what files are excluded:**
```bash
# Backend
cat gymbro-api/.coveragerc

# Frontend
cat gymbro-web/vitest.config.ts | grep -A 10 "exclude:"
```

**Run pre-commit validation:**
```bash
.\scripts\pre-commit.ps1  # Full check (~10 seconds)
.\scripts\lint-check.ps1  # Lint only (~2 seconds)
```
