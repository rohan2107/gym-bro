# Testing Guide

Quick reference for running tests in the Gym Bro project.

## Quick Commands

### Backend (FastAPI + pytest)

```bash
# Navigate to backend
cd gymbro-api

# Activate virtual environment (Windows)
.\.venv\Scripts\Activate.ps1

# Run all tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=term

# Quiet mode (summary only)
pytest -q

# Run specific test file
pytest tests/test_food_logs.py -v

# Run specific test
pytest tests/test_food_logs.py::test_create_food_log -v
```

### Frontend (React + Vitest)

```bash
# Navigate to frontend
cd gymbro-web

# Run all tests (single run)
npm test -- --run

# Watch mode (re-runs on file changes)
npm test

# With coverage
npm test -- --run --coverage

# Visual UI
npm run test:ui

# Verbose output
npm test -- --run --reporter=verbose
```

### Run Everything

```bash
# From project root (Windows PowerShell)
cd gymbro-api; pytest -v; cd ..\gymbro-web; npm test -- --run
```

## Test Structure

### Backend Tests (`gymbro-api/tests/`)

- `test_auth_utils.py` - JWT token creation and validation (6 tests)
- `test_deps.py` - Dependency injection and user ID extraction (6 tests)
- `test_daily_checkins.py` - Daily check-in operations (6 tests)
- `test_food_logs.py` - Food log CRUD operations (10 tests)
- `test_workouts.py` - Workout CRUD operations (11 tests)
- `test_weight_entries.py` - Weight entry CRUD operations (8 tests)

**Total: 47 tests**

### Frontend Tests (`gymbro-web/src/test/`)

- `utils.test.ts` - Utility functions (12 tests)
- `BottomNav.test.tsx` - Navigation component (8 tests)
- `OfflineIndicator.test.tsx` - Offline indicator (7 tests)

**Total: 27 tests**

## Coverage Reports

### Backend Coverage

```bash
cd gymbro-api
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

### Frontend Coverage

```bash
cd gymbro-web
npm test -- --run --coverage
# Open coverage/index.html in browser
```

## Common Issues

### Backend

**Issue**: `pytest: command not found`
```bash
# Make sure virtual environment is activated
.\.venv\Scripts\Activate.ps1
```

**Issue**: `ImportError: cannot import name...`
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend

**Issue**: `vitest: command not found`
```bash
# Make sure dependencies are installed
npm install
```

**Issue**: Tests fail with module errors
```bash
# Clear cache and reinstall
rm -r node_modules
npm install
```

## Test Database

Backend tests use an in-memory SQLite database. No setup required - each test gets a fresh database automatically.

## CI/CD

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request

See `.github/workflows/ci.yml` for pipeline configuration.

## Writing New Tests

### Backend Example

```python
def test_my_feature(client: TestClient):
    headers = {"X-User-Id": "1"}
    
    resp = client.post("/my-endpoint", json={
        "field": "value"
    }, headers=headers)
    
    assert resp.status_code == 201
    assert resp.json()["field"] == "value"
```

### Frontend Example

```typescript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MyComponent from '../components/MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

## Performance

- Backend tests: ~11 seconds for 47 tests
- Frontend tests: ~1.5 seconds for 27 tests
- Total: ~13 seconds for full test suite (74 tests)

## Next Steps

- Add E2E tests with Playwright (Phase 4)
- Increase coverage to >90%
- Add performance benchmarks
- Add integration tests with real database
