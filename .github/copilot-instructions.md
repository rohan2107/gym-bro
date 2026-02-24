# GitHub Copilot Agent Instructions - Gym Bro Project

## Project Overview
**Gym Bro** is a production-ready fitness PWA with React/TypeScript frontend and FastAPI/SQLModel backend. Deployed on Vercel with PostgreSQL on Neon. Currently in Phase 4.2 (AI Meal Photo Logging - Backend Complete).

## Core Principles

### 1. **Systematic, Phase-Based Development**
- Work follows structured phases documented in `docs/IMPLEMENTATION_ROADMAP.md`
- Each phase has a completion doc: `docs/PHASE_X.Y_COMPLETE.md`
- Update roadmap when phases complete
- Break large work into logical phases

### 2. **Documentation First, Always Current**
- Keep all docs in sync with code (especially after changes)
- Create `PHASE_X_COMPLETE.md` only when phase truly complete
- Update `IMPLEMENTATION_ROADMAP.md` to reflect current status
- Minimal fluff - direct, technical communication
- Delete temporary tracking docs before commit (PR_REVIEW_FIXES.md, etc.)
- Archive old planning docs to `docs/archive/` for historical reference

### 3. **Test-Driven Quality**
- **All tests must pass before claiming completion**: `pytest tests/ -q --tb=no`
- **Current test count**: 123 tests (must remain at or increase)
- Add tests for all new features (integration + unit)
- Zero skipped tests in final commits
- Run tests after every significant change

### 4. **Linting is Non-Negotiable**
- **Zero linting errors before commit**: `ruff check app/ tests/`
- Use auto-fix: `ruff check --fix .` or `.\scripts\lint-check.ps1 -Fix`
- Frontend: `cd gymbro-web && npm run lint -- --fix`
- Scripts available: `.\scripts\lint-check.ps1` (with optional `-Fix`)

### 5. **Git Workflow**
- Create feature branches: `phase4.x/feature-name` or `fix/issue-name`
- Never commit tracking/planning docs (PR_REVIEW_FIXES.md, COMMIT_SUMMARY.md)
- Descriptive commit messages with context (see examples in PHASE4.2_COMPLETE.md)
- Verify with `git status --short` before committing

## Code Quality Standards

### Python Backend (FastAPI/SQLModel)

**Type Hints**:
- Use `Any` (capital A) not `any`
- Return types on all functions
- Import from `typing` module

**Error Handling**:
```python
try:
    result = service.method()
except ValueError as e:
    # User input errors - log with context
    logger.warning(f"Context: {e}")
    raise HTTPException(400, "User-friendly message.")
except Exception as e:
    # Unexpected errors - generic user message
    logger.error(f"Context: {e}", exc_info=True)
    raise HTTPException(503, "Generic message. Try again.")
```

**Error Messages**:
- Always end with period
- Sentence case
- User-friendly, no internal details
- Helpful guidance when possible

**Logging**:
- **Never use `print()`** - always use `logger.warning()` or `logger.error()`
- Include context in log messages
- Use `exc_info=True` for exceptions

**Code Organization**:
- Dependency injection via FastAPI `Depends()`
- Services in `app/services/` with proper initialization
- No dead code (remove unused functions)
- Clean comments (no confusing commented-out code)

**Database**:
- Use transactions for multi-step operations
- Row-level locking (`with_for_update()`) for race conditions
- Alembic migrations with `server_default` for NOT NULL columns
- Test migrations on SQLite (dev) but document Postgres behavior

**Async**:
- Use `async def` for I/O operations (HTTP, database)
- Configure pytest-asyncio properly (`pytest.ini`)
- HTTP timeouts on all AsyncClient (10s default)

### TypeScript Frontend (React/Vite)

**Component Structure**:
- Functional components with hooks
- TypeScript interfaces for props
- Tailwind CSS for styling

**Testing**:
- Vitest for unit tests
- Test user interactions, not implementation

## Development Workflow

### For Multi-Step Work
1. **Create todo list** with `manage_todo_list` tool
2. Mark items in-progress before starting
3. Mark completed immediately after finishing (don't batch)
4. Keep todos visible for user tracking

### Before Claiming "Done"
✅ Run tests: `cd gymbro-api && pytest tests/ -q --tb=no`  
✅ Run linting: `cd gymbro-api && ruff check app/ tests/`  
✅ Check git status: `git status --short`  
✅ Verify docs match code  
✅ Delete temporary tracking files

### For Code Changes
1. **Read context first** - don't guess, read files
2. **Batch parallel operations** - read multiple files at once when independent
3. **Use `multi_replace_string_in_file`** for multiple edits (more efficient)
4. **Include 3-5 lines context** in replacements (before/after target)
5. **Test immediately after** - don't wait until "done"

### For Documentation
- Update `docs/IMPLEMENTATION_ROADMAP.md` when phases change
- Create `docs/PHASE_X_COMPLETE.md` only when phase done
- Keep `README.md` current with features/setup
- Archive old phase planning docs to `docs/archive/`

## Communication Style

**Be Direct**:
- Short responses for simple queries (1-3 sentences)
- Expand only for complex work
- No unnecessary framing ("Here's what I found...")
- Confirm completion briefly without explaining what was done

**Use Markdown Links for Files**:
- Always link files: `[file.py](path/file.py#L10)` not `file.py`
- Include line numbers when referencing specific code
- Never use backticks for file paths

**Response Length**:
- Simple answer: 1 line (e.g., "12" for "what's square root of 144")
- Code-only tasks: Just implement, brief confirmation
- Complex work: Structured update with progress

## Project-Specific Context

### Current Phase: 4.2 Complete (Backend)
- Photo upload endpoint implemented
- 14/14 PR review fixes complete
- 123 tests passing, zero linting errors
- Awaiting API keys (Google Vision, USDA, Vercel Blob)
- Next: Phase 4.3 (Frontend implementation)

### Test Structure
- Backend: `gymbro-api/tests/` (pytest)
- Frontend: `gymbro-web/src/test/` (Vitest)
- Integration tests in `tests/test_*_endpoint.py`
- Unit tests for services in `tests/test_*_service.py`

### Key Files
- Backend entry: `gymbro-api/app/main.py`
- Models: `gymbro-api/app/models.py`
- Routes: `gymbro-api/app/routers/*.py`
- Services: `gymbro-api/app/services/*.py`
- Frontend entry: `gymbro-web/src/main.tsx`

### Environment
- Dev: SQLite (in-memory for tests)
- Prod: PostgreSQL on Neon
- Auth: Google OAuth 2.0 + JWT
- APIs: Google Vision, USDA FoodData Central

### Scripts
- `.\scripts\lint-check.ps1` - Quick lint (add `-Fix` to auto-fix)
- `.\scripts\pre-commit.ps1` - Full quality gates
- `.\scripts\start-all.ps1` - Start frontend + backend

## Anti-Patterns (Don't Do These)

❌ Print statements (`print()`) - use logger  
❌ Claim "done" without running tests  
❌ Commit temporary tracking docs  
❌ Create markdown reports unless asked  
❌ Use `any` (lowercase) - use `Any`  
❌ Catch `Exception` without logging context  
❌ Skip test updates when changing behavior  
❌ Leave dead/commented code  
❌ Forget to update docs after code changes  
❌ Use absolute paths in code (use relative)  
❌ Create sub-shells in PowerShell unnecessarily

## When Uncertain

1. **Search first** - use grep/semantic search to understand patterns
2. **Read existing code** - follow established patterns
3. **Ask specific questions** - not "should I continue"
4. **Propose approach** - don't wait for permission
5. **Validate incrementally** - test after each major change

## Success Criteria

Every commit should have:
- ✅ All tests passing (123+)
- ✅ Zero linting errors
- ✅ Docs match code
- ✅ No temporary files
- ✅ Descriptive commit message
- ✅ Branch name follows convention

---

**Last Updated**: February 24, 2026  
**Current Phase**: 4.2 Complete (Backend) → 4.3 Planning (Frontend)
