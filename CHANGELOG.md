# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). There are no version numbers yet;
entries are grouped by milestone and dated.

## [Unreleased]

### Removed

- Unused code: `NutritionService.batch_search`, `lookup_by_fdc_id` and `get_food_mapping`, and
  the empty `FDC_ID_MAPPING` with its accessor. Only tests called them
- The PowerShell scripts, which duplicated the shell scripts, were untested, and are not used
  on the project's platform. Windows users can use WSL
- The Codecov upload and the unused frontend build-artifact upload in CI. Coverage is enforced
  by the 80% gate in each suite, not by an external service. The frontend suite no longer runs
  twice
- Hard-coded test counts in the documentation, which had already drifted

### Changed

- Production no longer installs `uvicorn`, `httptools`, `watchfiles`, `websockets`, `PyYAML`,
  `click` or `colorama`. The deployed handler never imports them; they remain in the
  development requirements for the local server, and a test keeps the two sets apart. Checked
  by importing the handler and calling `/health` in a clean environment built from the
  production requirements alone
- Photo analysis estimates the portion in grams and scales USDA's per-100g values to it. When
  USDA errors, times out or has no match, the model's own estimate is returned, labelled as an
  AI estimate, instead of failing the request; the review screen states which it is
  ([ADR-0010](docs/adr/0010-usda-as-a-local-reference.md), proposed)
- The per-model Gemini timeout is 12 seconds, so a hanging model does not hold the user long
  before the fallback model is tried
- Photo analysis recognises foods with the Gemini API free tier (no billing account) through a
  `FoodRecognizer` interface; Google Cloud Vision is now an optional provider, chosen by
  `FOOD_RECOGNITION_PROVIDER` ([ADR-0005](docs/adr/0005-food-recognition-providers.md),
  accepted). Image validation is shared by every provider
- The capture screen states that photos are sent to Google and are not stored
- Python 3.12 and Node 24 are pinned (`.python-version`, `.nvmrc`, `engines`) and CI runs the
  same versions Vercel builds with; a test fails if they drift
- Documentation restructured: the two overlapping roadmaps are consolidated into one
  ([ROADMAP.md](docs/ROADMAP.md)), decisions are recorded as ADRs ([docs/adr/](docs/adr/README.md)),
  and the September 2026 audit is kept as its own record
  ([AUDIT_2026-09.md](docs/AUDIT_2026-09.md))
- The three design documents that described plans rather than the built system were replaced by
  accurate ones: [PHOTO_ANALYSIS.md](docs/PHOTO_ANALYSIS.md),
  [AUTHENTICATION.md](docs/AUTHENTICATION.md) and [ENERGY_BALANCE.md](docs/ENERGY_BALANCE.md)

### Added

- `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL` and `FOOD_RECOGNITION_PROVIDER`
  settings; the Gemini provider falls back to a second model on `429` and `5xx` and otherwise
  fails closed with the user's quota refunded
- Tests against Gemini responses recorded from the live API
- [EVALUATION.md](docs/EVALUATION.md): the design of the evaluation harness, ahead of its
  implementation
- [DEPLOYMENT.md](docs/DEPLOYMENT.md): configuration, CI/CD, release, rollback, cost controls
  and secrets handling

### Fixed

- **Security:** the USDA API key was sent in the URL and written to production logs. It is now a
  header, logs carry status codes only, and the `httpx` logger is quieted at startup. Rotate
  any key that has appeared in a log
- Photos of common foods failed with "Could not find nutrition data" because USDA answered `400`
  to about half of searches that used a `dataType` filter, and the service reported every error
  as "no match". The filter is gone, transient errors are retried, and a failed lookup is now a
  `503` with the quota refunded, distinct from a real `404`
- Nutrition extraction could report kilojoules as calories for Foundation and SR Legacy foods;
  energy is now matched by unit
- USDA results are filtered (no branded products, no entries without macro data) and ranked, so
  "apples" no longer returns candied apple and no match is preferred to a wrong one
- Photo upload failed with "Load failed" for any photo over about 4.5MB, because Vercel rejects
  larger request bodies before the API runs. The browser now shrinks the photo (1600px, JPEG)
  before uploading, and a dropped connection shows a clear message
- Frontend dependencies: `npm audit` went from 23 vulnerabilities (3 critical) to none,
  including two high-severity advisories in the production `react-router` dependency. Vite is
  now on 8, which Vitest 4 already required
- ESLint moved from 8 (end of life) to 10 with a flat config (`eslint.config.js`); the newer
  React Hooks rules flagged an effect that called a function declared after it, now reordered
- Removed the unused `mangum` dependency
- Documentation claimed the API was "Mangum-wrapped" and could not stream; the handler exposes
  the ASGI app directly and `mangum` is never imported
- Documentation listed `VITE_GOOGLE_CLIENT_ID` as a frontend variable; nothing reads it

## Phase 0: Foundation, 2026-09-20

[Pull request #16](https://github.com/rohan2107/gym-bro/pull/16). Details of each finding are
in the [audit](docs/AUDIT_2026-09.md).

### Security

- Closed an impersonation hole: production accepted an `X-User-Id` header as authentication
  because `ENVIRONMENT` was unset and defaulted to `development`. The header is now default-deny
  and never accepted on Vercel
- Stopped sending the Vision API key in the request URL, where exception logging would have
  recorded it
- Replaced a CORS rule that admitted every `*.vercel.app` origin with credentials by an explicit
  allow-list

### Added

- Google Cloud Vision integration over its REST API, replacing a stub that always returned
  "pizza"
- Meal photo capture and review UI: native camera on mobile, every predicted value editable,
  quota display, and fallback to manual entry on any failure
- HEIC detection with an actionable message
- Shell equivalents of the Windows-only developer scripts
- Tests that prevent recurrence: dependency parity between production and CI, migrations that
  build the schema from empty, CORS origin rejection, and credential handling

### Changed

- Alembic is the sole owner of the schema; the baseline migration was rewritten to create the
  schema, keeping its revision id so an already-migrated database is unaffected
- All configuration is declared on `Settings`
- Photo analysis refuses to serve mock data on a deployment
- Ruff is configured and pinned

### Fixed

- The photo endpoint would have failed in production: `pillow` was missing from the deployed
  dependencies while CI stayed green
- A placeholder user was written to the production database on every cold start
- No migration had ever created a table
- The lint job failed on an untouched `main` because the linter was unpinned
- Validation errors exposed Python object reprs to users

### Removed

- Fourteen progress-tracking documents, a one-shot `create_all()` script, and generated files
  that had been committed

Tests: 133 backend and 27 frontend before, 175 and 50 after.
