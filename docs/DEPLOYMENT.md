# Deployment and operations

How the app is built, configured, released and verified, and the rules that keep it safe to
operate. For system design see [ARCHITECTURE.md](ARCHITECTURE.md).

## Environments

| Environment | Where | Database | Notes |
|---|---|---|---|
| Local | Developer machine | SQLite (default) or a local Postgres | `./scripts/start-all.sh`; mock mode for external services unless keys are set |
| Preview | Vercel, one per pull request | As configured for the Preview environment | Smoke-tested by CI; Vercel sets `VERCEL=1` |
| Production | Vercel, from `main` | Neon PostgreSQL | Migrations applied by CI on merge |

The frontend is a static build served by Vercel. The API is a single Python function
(`api/handler.py`) that exposes the FastAPI app directly, with `/api/*` routed to it by
[vercel.json](../vercel.json).

## Configuration

All backend configuration is declared on `Settings` in
[gymbro-api/app/config.py](../gymbro-api/app/config.py); that file is the contract. Set these
in Vercel for the environment concerned.

| Variable | Required | Purpose |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string. Defaults to local SQLite, which is wrong for a deployment |
| `JWT_SECRET_KEY` | Yes | Signs session tokens. Unset, token creation raises rather than signing with an empty key |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client |
| `FRONTEND_URL` | Yes | The deployed origin. The OAuth callback is derived from it as `<FRONTEND_URL>/auth/callback`, and cookies are marked `Secure` when it is `https` |
| `GOOGLE_VISION_API_KEY` | No | Enables the Vision provider. See the cost rules below |
| `USDA_API_KEY` | No | Enables nutrition lookup |
| `CORS_ALLOWED_ORIGINS` | No | Extra allowed origins, comma-separated |
| `CORS_PREVIEW_ORIGIN_REGEX` | No | Extra allowed origins by pattern. Empty by default; see [AUDIT F6](AUDIT_2026-09.md) before setting it |
| `ENVIRONMENT` | No | **Do not set to `development` on a deployment.** It defaults to `production`, and the `X-User-Id` development header is disabled on Vercel regardless |

Provided by Vercel: `VERCEL` (and related). The application uses it to disable development
behaviour on any deployment.

The frontend reads one optional build-time variable, `VITE_API_URL`; without it the client uses
`/api`. It needs no Google client id, because sign-in redirects through the backend.

Without the two optional keys the affected services run in **mock mode**, which returns fixed
sample data. On a deployment the photo endpoint refuses to serve mock data and returns `503`.

## CI/CD

Defined in [.github/workflows/ci.yml](../.github/workflows/ci.yml).

| Job | Runs on | In the gate |
|---|---|---|
| Backend tests (with coverage) | Push, PR | Yes |
| Backend lint (ruff, pinned) | Push, PR | Yes |
| Frontend tests | Push, PR | Yes |
| Frontend lint | Push, PR | Yes |
| Frontend type check | Push, PR | Yes |
| Frontend build | Push, PR | Yes |
| Verify deployment config | Push, PR | Yes |
| Apply DB migrations | Push to `main` only | Yes (skipped counts as passing) |
| Preview smoke test (polls the preview's `/api/health`) | PR only | No |

`All Checks Passed` aggregates the gated jobs. The preview smoke test is informative but does
not block a merge.

**Runtime versions.** Python 3.12 and Node 24, pinned in `.python-version` and
`.nvmrc`, with `engines.node` in `gymbro-web/package.json`. Vercel reads the Python pin from
`api/.python-version` (next to the function; a copy at the repo root serves local tools) and
Node from `engines`; CI's `PYTHON_VERSION` and `NODE_VERSION` must match them, which
`tests/test_runtime_versions.py` enforces. Change all of them together.

## Releasing

1. Open a pull request; CI runs and Vercel builds a preview.
2. Before merging any change that includes a migration, check what production is stamped at
   (see below) so the `db-migrate` job is not a surprise.
3. Merge. Vercel deploys `main`, and the `db-migrate` job runs `alembic upgrade head` against
   production.
4. Run the post-deploy checks.

### Checking the production schema version

```bash
cd gymbro-api
read -s "DBURL?Paste DATABASE_URL: "; echo        # zsh; avoids shell history
DATABASE_URL="$DBURL" JWT_SECRET_KEY=x .venv/bin/alembic current
unset DBURL
```

Use the `postgresql://` scheme; SQLAlchemy 2 rejects `postgres://`. The command only reads.
The result should be the latest revision. If it is behind, or empty, stop and reconcile before
merging: a database built outside migrations must be stamped, not upgraded.

### Post-deploy checks

```bash
curl -s https://<host>/api/health                       # {"status":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://<host>/api/food-logs/    # 401
curl -s -o /dev/null -w '%{http_code}\n' \
  -H 'X-User-Id: 999999999' https://<host>/api/food-logs/               # 401
```

The last check confirms the impersonation header is rejected ([AUDIT F12](AUDIT_2026-09.md)).
Then sign in through the browser and load each page. Use an id that cannot exist for the probe.

### Rolling back

Vercel can promote a previous deployment instantly. **Schema changes are not rolled back with
it**, so every migration must remain compatible with the previous deployment's code: add
columns as nullable or with a server default, and remove them only in a later release.

## Cost controls

The project's rule is zero spend ([ADR-0003](adr/0003-hard-capped-providers-only.md)).

- Use only services that stop at their limit rather than bill.
- **A budget is an alert, not a cap.** Google's documentation states that budgets do not
  automatically cap usage, and alerts lag actual spend.
- Google Cloud Vision requires a billing account and has no daily quota cap by default, so it
  is an optional provider, not a required one. If it is ever enabled: use a free-trial billing
  account if eligible (it is not charged unless upgraded), lower the per-minute quota,
  restrict the API key to the Vision API, and unlink billing when not testing.
- Prepaid and many virtual cards are not accepted by Google Cloud, and a declined payment
  suspends every project on the account without cancelling the debt. Do not rely on a
  low-limit card as a control.

## Secrets

- Secrets live in Vercel environment variables and in gitignored local `.env` files. Never in
  the repository, in URLs, or in logs.
- Send credentials in headers. `httpx` includes the request URL in exception messages, and the
  photo endpoint logs exceptions with tracebacks.
- Restrict every API key to the single API it is for. Rotate a key immediately if it is ever
  exposed.
- A local `.env` must never point at the production database.

## Database

Neon PostgreSQL. Migrations are the only schema mechanism
([ADR-0001](adr/0001-alembic-owns-the-schema.md)). The free tier scales compute to zero, so
the first request after idle pays a cold start; Phase 1 measures this
([M1.4](ROADMAP.md#m14-tracing-and-cost)).
