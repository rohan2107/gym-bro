# Agent Instructions — Gym Bro

Conventions for AI coding agents working in this repo. Human contributors should find them
useful too.

## What this project is

Fitness PWA. FastAPI + SQLModel backend, React/TypeScript frontend, deployed on Vercel with
Neon PostgreSQL. Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design and
[docs/IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) for where development stands.

## Quality gates

All of these must pass before claiming work is done:

```bash
./scripts/pre-commit.sh     # backend tests + coverage, ruff, ESLint, tsc, frontend tests
git status --short          # no unintended files
```

Or individually:

```bash
cd gymbro-api && JWT_SECRET_KEY=test-secret .venv/bin/pytest -q
cd gymbro-api && .venv/bin/ruff check app/ tests/
cd gymbro-web && npm run lint && npm run type-check && npm run test:run
```

Test count must not decrease. Add tests for all new behaviour.

## Python conventions

**Type hints**: `Any` not `any`. Return types on all functions.

**Error handling**:

```python
except ValueError as e:
    logger.warning(f"Context: {e}")
    raise HTTPException(400, "User-friendly message.")   # ends with a period
except Exception as e:
    logger.error(f"Context: {e}", exc_info=True)
    raise HTTPException(503, "Try again later.")
```

**Never** use `print()` — use `logger.warning()` / `logger.error()`.

**Async**: `async def` for all I/O. Every `httpx.AsyncClient` call gets a timeout. Do not call
blocking I/O from an async endpoint.

**Configuration**: every environment variable is declared on `Settings` in
[gymbro-api/app/config.py](gymbro-api/app/config.py). Do not read `os.getenv` directly in
services — it splits the environment contract across files and nothing then enforces it.

**Linting**: the rule set is pinned in [gymbro-api/ruff.toml](gymbro-api/ruff.toml) and ruff is
version-pinned in CI. Both are deliberate: an unpinned linter once failed the lint job on code
nobody had changed. Do not widen the rule selection as a side effect of another change.

## Database

**Alembic owns the schema.** The app does not create tables at startup, and
`SQLModel.metadata.create_all()` must not be reintroduced into the application path.

When autogenerating a migration, generate it against a database **built by migrations**
(`alembic upgrade head` on an empty database), never against one created by `create_all()`.
Autogenerating against a `create_all()` database is how this project ended up with an "initial
schema" migration that created no tables — see F11 in
[docs/AI_ROADMAP.md](docs/AI_ROADMAP.md).

Always review generated migrations. Use `server_default` for new NOT NULL columns. Use
transactions for multi-step operations and `with_for_update()` where a read-modify-write can
race. `tests/test_migrations.py` asserts a fresh `alembic upgrade head` reproduces the models'
schema; keep it passing.

## Dependencies

Two requirements files, and they must stay in step:

- `api/requirements.txt` — what Vercel installs for the serverless function
- `gymbro-api/requirements.txt` — that set plus test tooling

A dependency added to only the second one passes CI and breaks production.
`tests/test_requirements_parity.py` enforces this.

## Documentation

These must stay accurate, especially test counts and status:

| Doc | Update when |
|---|---|
| `README.md` | Test counts change, features added, stack changes |
| `docs/ARCHITECTURE.md` | New endpoints, models, services, security changes, test counts |
| `docs/IMPLEMENTATION_ROADMAP.md` | A phase completes or starts |
| `docs/AI_ROADMAP.md` | AI/retrieval/eval work progresses |

If you add or remove tests, re-count and update the numbers before committing. Do not document
behaviour that is not implemented — a README claim the code does not support is a bug.

## Security

- The `X-User-Id` header is a development convenience that impersonates any user. Never widen
  the conditions under which `dev_auth_enabled()` returns true, and keep the default deny.
- A security-relevant default must be the safe one. An unset variable should never enable
  something dangerous; production once ran with the header open for exactly that reason.
- Credentials go in headers, never URLs, because httpx puts the URL in exception messages.

## Anti-patterns

- `print()` anywhere — use the logger
- Catching `Exception` without `exc_info=True` and context
- Dead or commented-out code, including "implementation to uncomment later"
- Claiming done without running the quality gates
- Stale doc numbers
- Committing generated files (coverage reports, `*.tsbuildinfo`, `vite.config.js`)
- Committing temporary planning or summary markdown
- Absolute paths in code

## Git

- Branches: `feature/name`, `fix/name`, `phase0/name`
- Verify with `git status --short` before every commit
