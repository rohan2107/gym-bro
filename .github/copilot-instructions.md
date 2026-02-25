# GitHub Copilot Instructions — Gym Bro

## What This Project Is
Production fitness PWA. FastAPI + SQLModel backend, React/TypeScript frontend, deployed Vercel + Neon PostgreSQL. See `docs/IMPLEMENTATION_ROADMAP.md` for current phase status — read it before starting any work session.

---

## Quality Gates (all required before claiming done)
```
cd gymbro-api && pytest tests/ -q --tb=no     # must show 0 failed, 0 skipped
cd gymbro-api && ruff check app/ tests/        # must show 0 errors
cd gymbro-web && npm run lint -- --fix
git status --short                              # no unintended files
```
Test count must not decrease. Add tests for all new behaviour.

---

## Python Conventions

**Type hints**: `Any` not `any`. Return types on all functions. Import from `typing`.

**Error handling pattern**:
```python
except ValueError as e:
    logger.warning(f"Context: {e}")
    raise HTTPException(400, "User-friendly message.")   # ends with period
except Exception as e:
    logger.error(f"Context: {e}", exc_info=True)
    raise HTTPException(503, "Try again later.")
```

**Never** use `print()` — always `logger.warning()` / `logger.error()`.

**Database**: transactions for multi-step ops, `with_for_update()` for race conditions, `server_default` in Alembic migrations for NOT NULL columns.

**Async**: `async def` for all I/O, 10s timeout on all `AsyncClient` calls.

---

## Communication Style
- Simple task → implement it, one-line confirmation
- No "Here's what I found..." framing
- Link files as [filename.py](../path/to/filename.py#L10), not backtick paths, include line numbers
- Don't create markdown summaries unless explicitly asked

---

## Workflow Rules
1. Read context before writing — don't guess at file contents
2. Batch independent file reads in parallel
3. Test immediately after each significant change, not at the end
4. For multi-step work, maintain a visible todo list
5. Delete temporary tracking files (PR_REVIEW_FIXES.md, COMMIT_SUMMARY.md) before commit
6. Archive old phase planning docs to `docs/archive/`

---

## Docs That Must Stay Current
Only 3 active docs exist (everything else is in `docs/archive/`). Update these when your changes affect what they describe:

| Doc | Update when… |
|-----|-------------|
| `README.md` | Test counts change, features added, stack changes |
| `docs/ARCHITECTURE.md` | New endpoints, models, services, security changes, test counts |
| `docs/IMPLEMENTATION_ROADMAP.md` | Phase completed, new phase started, test counts change |

**Rule**: if you add/remove tests, update the counts in all three files before committing.

---

## Anti-Patterns
❌ `print()` anywhere — use logger  
❌ `any` (lowercase) — use `Any`  
❌ Claiming done without running pytest + ruff  
❌ Catching `Exception` without `exc_info=True` and context  
❌ Leaving dead or commented-out code  
❌ Committing temporary tracking docs  
❌ Absolute paths in code  
❌ Skipping test updates when changing existing behaviour  
❌ Stale doc numbers — always re-count tests before commit

---

## Git
- Branches: `phase4.x/feature-name` or `fix/issue-name`
- Never commit: `PR_REVIEW_FIXES.md`, `COMMIT_SUMMARY.md`, or similar planning artefacts
- Verify with `git status --short` before every commit