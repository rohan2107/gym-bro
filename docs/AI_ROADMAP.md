# AI Roadmap

**Created**: September 16, 2026
**Status**: Phase 0 complete (code); Phase 1 not started
**Companion to**: [Implementation Roadmap](IMPLEMENTATION_ROADMAP.md) (product phases), [Architecture](ARCHITECTURE.md)

---

## Purpose

This document plans the extension of Gym-Bro into an evaluated, observable, agentic LLM
system, and folds in the defects and documentation discrepancies found during the September
2026 audit after a seven-month pause (last roadmap update: February 25, 2026).

The goal is a retrieval-and-agent layer over the existing app that is **evaluated and
observable rather than merely demonstrable** — retrieval whose groundedness is measured,
agent behaviour whose tool trajectories are checked, and model calls that are traced, retried
and costed like any other production dependency.

It starts with Phase 0 because the app's one existing AI feature was incomplete: the Vision
integration was a stub, and several production defects sat underneath it.

---

## Current state

Verified by running, not by reading docs.

| Thing | As found (audit, 16 Sep) | After Phase 0 |
|---|---|---|
| Backend tests | 133 passing in 5.5s | **160 passing** in ~4s |
| Backend coverage | 84% | **85%** |
| Frontend tests | 27 (couldn't run — no Node installed) | **46 passing** |
| Backend lint | 202 findings on untouched main (see F10) | clean, rule set pinned |
| Vision integration | stub, always returned `"pizza"` | real REST integration (unverified against live API) |
| Photo UI | none | `PhotoCapture` + `MealReview` on the Meals page |
| CI | 9 jobs, 8 required by the `all-checks-passed` gate | unchanged |
| Auth | Google OAuth 2.0 + JWT, httpOnly cookie + Bearer header | unchanged |
| DB | PostgreSQL (Neon), Alembic migrations, 2 revisions | Alembic now sole schema owner |
| Deploy | Vercel — static frontend + `api/handler.py` (Mangum-wrapped FastAPI) | unchanged |

**What is genuinely good and worth building on**: atomic rate limiting via
`SELECT FOR UPDATE` with quota refund on downstream failure, streamed uploads with a
64KB-chunk size cap, user isolation enforced at the dependency-injection layer, services
injected as dependencies (so they are mockable), 8 quality gates on every PR.

---

## Fix ledger

Defects and discrepancies found in the audit. **P0 items blocked Phase 1** — they were either
broken in production or made a public claim the code did not support.

**All items below are fixed** (Phase 0, September 16, 2026), with one caveat: F1's replacement
implementation has not been run against the live Vision API. See
[remaining Phase 0 verification](#remaining-phase-0-verification).

### P0 — correctness and credibility

**F1. Google Cloud Vision is not integrated.**
`VisionService.client` is hardcoded `None` (`app/services/vision.py:44`), the real
implementation is commented out (`vision.py:87-118`), and the `google.cloud.vision` import
is commented out at the top of the file. Behaviour today:
- mock mode (no API key present) → returns a hardcoded `{"label": "pizza", "confidence": 0.85}`
- non-mock mode → raises `RuntimeError`

So the feature always "detects" pizza. `NutritionService` (USDA) by contrast **is** fully
implemented with real `httpx` calls and only needs a key.

Meanwhile `README.md:15` claimed *"✅ AI meal logging — snap a photo, get calories & macros
via Google Vision + USDA"*. Documented behaviour and actual behaviour had diverged
completely, which made this the highest-priority item in this document.

**F2. The deployed photo endpoint would 500 even with a Vision key.**
Vercel installs `api/requirements.txt`, which does not list `pillow`. But the endpoint
calls `vision_service.validate_image()` (`app/routers/food_logs.py:134`), which does
`from PIL import Image` (`vision.py:142`) *before* its `try` block, so `ImportError`
propagates as an unhandled 500. Tests pass because they install
`gymbro-api/requirements.txt`, which does have pillow. Green CI, broken production.

**F3. The two requirements files have drifted.**
`api/requirements.txt` (what production installs) vs `gymbro-api/requirements.txt` (what
CI and local dev install):
- `alembic` pinned 1.13.1 vs 1.15.2
- `google-cloud-vision` and `pillow` present only in the latter
- `pytest-asyncio`, `pytest-cov` only in the latter (correct — test-only)

Production and CI are not installing the same dependency set. Pick one source of truth.
`gymbro-api/requirements.txt` is UTF-16LE encoded with CRLF (a PowerShell artifact); pip
reads it fine, so this is cosmetic, but normalise it to UTF-8 while touching the file.

**F4. `init_db()` seeds a phantom production user on every cold start.**
`app/db.py` `init_db()` inserts user `id=1`, `email=temp@gymbro.app`, commented
*"temporary until OAuth is implemented"* — but OAuth shipped in Phase 2 (February 2026).
This runs from the FastAPI `lifespan` hook, i.e. on every serverless cold start against
the production Neon database. Remove the seed.

**F5. `create_all()` and Alembic are competing schema owners.**
`init_db()` calls `SQLModel.metadata.create_all()` at startup while CI separately runs
`alembic upgrade head` on push to main (`.github/workflows/ci.yml`, `db-migrate` job).
Two mechanisms manage the same schema, so Alembic is not actually the source of truth.
This will bite hard the moment a migration needs a data transform — and Phase 1 adds a
migration (pgvector). Make Alembic authoritative and drop `create_all()` from the startup
path.

**F10. The ruff lint job was broken by linter version drift.**
CI installed ruff unpinned (`pip install ruff`), and there was no ruff configuration in the
repo, so the job's rule set was whatever the latest release happened to default to. On ruff
0.16.7 that produced **202 findings on an untouched main** — the lint gate would have failed
on code nobody had changed. Found while verifying Phase 0, not in the original audit.

*Fixed*: `gymbro-api/ruff.toml` states the rule set explicitly (E4, E7, E9, F — ruff's
historical default, which this codebase is clean against), and ruff is pinned to 0.16.7 in both
CI and the dev requirements. Widening the selection (`UP` for modern typing syntax, `DTZ` for
timezone-aware dates, `I` for import order) is worth doing deliberately as its own change;
it is roughly 200 stylistic findings and touches nearly every file.

**F11. No migration had ever created a table.**
`b53bda6fba5d`, the "initial schema" revision, was autogenerated against a database that
`create_all()` had already built. Alembic therefore saw no missing tables and emitted only an
index tweak — a `DROP INDEX` followed by a `CREATE INDEX`. The entire schema existed solely
because `create_all()` ran on every cold start.

This stayed invisible until F5 was fixed. With `create_all()` gone, `alembic upgrade head` on a
fresh database failed immediately: `no such index: ix_user_email`. Production was unaffected
only because its schema had been built by `create_all()` and its `alembic_version` was already
at head. Found while verifying Phase 0; it is the concrete form of the risk F5 described.

*Fixed*: `b53bda6fba5d` rewritten as a real baseline that creates all seven tables and their
indexes. The revision id is unchanged and the photo columns stay in `573ff5ce6812`, so a
database already stamped at head — production — sees no new work and needs no manual
intervention. `tests/test_migrations.py` runs `alembic upgrade head` against a fresh SQLite
database and asserts the resulting tables, columns and indexes match the models, plus that
`downgrade base` is clean. **This was the blocker for Phase 1's pgvector migration.**

### P1 — hardening and hygiene

**F6. CORS admits any `*.vercel.app` origin with credentials.**
`app/main.py` sets `allow_origin_regex=r"https://.*\.vercel\.app"` together with
`allow_credentials=True`, so any site deployed to `vercel.app` is an allowed credentialed
origin. Practical impact is limited because the JWT cookie is `samesite="lax"`
(`app/routers/auth.py:215`), which withholds it from cross-site XHR — so this is a
defence-in-depth weakness, not a known exploitable hole. But `ARCHITECTURE.md` claims
*"CORS configured for production domain"*, which is not what the code does. Pin the
production origin explicitly and match preview deployments by the project's own
deployment-URL prefix rather than the whole `vercel.app` namespace.

**F7. Service config bypasses `Settings`.**
`VisionService` and `NutritionService` read `GOOGLE_VISION_API_KEY` / `USDA_API_KEY` via
`os.getenv` directly, and neither key (nor `GOOGLE_REDIRECT_URI`) is declared on the
`Settings` model in `app/config.py`. So the documented environment contract lives in three
places and is enforced in none. Declare all keys on `Settings` and inject.

**F8. Docs state stale numbers.**
- `README.md` and `ARCHITECTURE.md` say *"7 parallel jobs"* / *"7 required jobs"*. CI now
  defines 9 jobs and the `all-checks-passed` gate requires 8 (the `db-migrate` job was
  added in commit `94e42f9`, after the docs were last written). The Vercel preview smoke
  test is **not** in the gate, though the README implies it is.
- `ARCHITECTURE.md` and `IMPLEMENTATION_ROADMAP.md` are both dated February 25, 2026 and
  describe Phase 4.2 as the head of development.

**F9. Tooling is Windows-only.**
All six scripts in `scripts/` are PowerShell (`.ps1`) and unusable on the current macOS
machine, including the `pre-commit` and `lint-check` workflows the README instructs you to
run. Port to shell scripts or a `Makefile`.

### How each was fixed

| Item | Resolution |
|---|---|
| **F1** Vision stub | Implemented against the Vision REST API (`images:annotate`) with an API key over `httpx`, rather than the `google-cloud-vision` client library — the library wants service-account credentials, not the API key this app is deployed with, and would ship gRPC/protobuf into a serverless function for one POST. `detect_food` is now `async`, matching `NutritionService` and no longer blocking the event loop. Added generic-label filtering (`NON_FOOD_LABELS`), deduplication, ranking, and score clamping for web entities (whose scores are unbounded relevance values, not probabilities — the original commented-out code treated them as confidences). 15 new tests against a mocked endpoint. |
| **F2** pillow ImportError | `pillow` added to `api/requirements.txt`; PIL imports moved to module scope in `vision.py` so a missing dependency fails at import, not per-request |
| **F3** requirements drift | Both files rewritten as UTF-8, pins aligned, `google-cloud-vision` dropped entirely (the REST approach makes it unnecessary). New `tests/test_requirements_parity.py` fails CI on any future drift |
| **F4** phantom seed user | `init_db()` replaced by `check_db_connection()`, which only reads. Tests assert startup neither creates tables nor writes rows |
| **F5** competing schema owners | `create_all()` removed from the startup path; Alembic is now the only schema owner |
| **F6** CORS | Explicit allow-list from `Settings` plus a preview regex anchored to this project's deployment prefix. Test asserts `attacker.vercel.app`, a different project slug, a suffix-appended host and plain `http://` are all rejected |
| **F7** config bypass | All keys declared on `Settings`; services read from it. An autouse test fixture forces mock mode so a developer with real keys in `.env` cannot make the suite issue live billable calls |
| **F8** stale docs | README, ARCHITECTURE and IMPLEMENTATION_ROADMAP corrected |
| **F9** Windows-only tooling | Shell equivalents added for all five scripts (`scripts/*.sh`, sharing `lib.sh`); `.ps1` files kept as the Windows versions |
| **F10** ruff drift | `ruff.toml` added, ruff pinned in CI and requirements |
| **F11** fictional migration history | Real baseline migration written; `tests/test_migrations.py` asserts a fresh `alembic upgrade head` reproduces the models' schema |

### Remaining Phase 0 verification

Phase 0 is code-complete but **not** verified end to end. The Vision implementation has only
ever run against a mocked endpoint. To close it out:

1. Set `GOOGLE_VISION_API_KEY` and `USDA_API_KEY` locally and on Vercel.
2. Photograph a real meal through the deployed app and confirm real labels and macros come back.
3. Expect to extend `NON_FOOD_LABELS` and `FOOD_MAPPING` once the real label vocabulary is
   visible — the filter list was written from expected Vision output, not observed output.
4. Confirm the `db-migrate` CI job still succeeds against production. Expected to be a no-op:
   production should already be stamped at `573ff5ce6812`. If it is stamped lower, check before
   letting it run — its schema was built by `create_all()`, not by migrations. `alembic current`
   against the production `DATABASE_URL` answers this in one command.

---

## Strategy

The work splits into three capabilities — **retrieval**, **agents**, and **evaluation** —
none of which the app currently has:

| Capability | Status |
|---|---|
| Evaluation | Not present |
| RAG / retrieval | Not present |
| Agents / tool-calling / MCP | Not present |
| Vector store / embeddings | Not present |
| LLM observability / tracing | Not present |

### The central idea: evaluation leads

Retrieval over a document corpus is straightforward to build and hard to trust. The part that
decides whether the feature is shippable is the harness that measures it, so evaluation is
designed first and the retrieval implementation is fitted to it — not the other way round.

The failure mode worth designing against is the **right answer for the wrong reason**: the
assistant returns correct macros while having retrieved the wrong document or fabricated its
citation. Answer-accuracy scoring passes that case; groundedness scoring catches it. A suite
that only measures final-answer correctness will report a healthy number for a system that is
not actually grounded — the same way a headline success metric can mask a model depending on a
spurious signal.

So the golden set deliberately includes planted right-answer-wrong-reason cases, and the suite
demonstrates both halves:

1. answer-accuracy-only evaluation **passing** them, and
2. groundedness / faithfulness evaluation **catching** them.

Building a benchmark where the correct answer is known by construction, then showing which
class of method can and cannot recover it, is what makes the rest of the quality claims in
this roadmap checkable.

### Sequencing decisions

- **Observability moves earlier.** Tracing was slated for Phase 3, but an eval story with
  no trace data underneath it is not credible, and wiring Langfuse or OTel-GenAI spans is
  hours, not a phase. A thin version lands in Phase 1.
- **The MCP server moves earlier.** It was slated late in Phase 2. It is roughly a day's
  work over tools that will already exist, and it is the cheapest high-signal artifact in
  the plan. It should not sit behind the full agent build.
- **The golden set is the real bottleneck in Phase 1**, not the code. Authoring 50–100
  questions with ground-truth citations is days of work. Budget it explicitly.
- **Phase 5 of the product roadmap is repurposed, not dropped.** See
  [disposition of the old roadmap](#disposition-of-the-old-roadmap).

---

## Phases

### Phase 0 — Make the existing AI feature real

**Why first**: the README documented a feature the code did not implement, and the defects
underneath it — a broken migration chain, a dependency missing from production, a startup path
that wrote to the production database — would have been inherited by everything built on top.

**Work**

- Implement `VisionService.detect_food` for real — uncomment and finish the label +
  web-entity detection path, keep mock mode as an explicit test seam (F1)
- Add `pillow` and `google-cloud-vision` to the production requirements, or consolidate to
  one requirements file (F2, F3)
- Wrap `validate_image`'s imports, or move them to module scope so failures surface at
  deploy time rather than per-request (F2)
- Remove the `temp@gymbro.app` seed; make Alembic the only schema owner (F4, F5)
- Build the photo capture UI — **Phase 4.3, descoped**: camera/file input, a review screen
  to edit predictions before saving, quota indicator, graceful fallback to manual entry.
  Drop Vercel Blob (the endpoint already takes bytes in-request) and drop the crop UI. The
  original 16-day estimate does not survive that descoping.
- Pin CORS origins; move API keys onto `Settings` (F6, F7)
- Port `scripts/*.ps1` to shell or a `Makefile` (F9)
- Correct `README.md` / `ARCHITECTURE.md` / `IMPLEMENTATION_ROADMAP.md` (F8)

**Done when**: a real photo of real food, taken on a phone against the deployed app,
produces real Vision labels and real USDA macros, saved to the food log — and every claim
in the README is true.

---

### Phase 1 — RAG + evaluation harness

The foundation for everything after it. Worth shipping before it is perfect.

**Work**

*Retrieval*
- Nutrition/training knowledge corpus with **real provenance** — sourced documents with
  citable identity, not scraped blog text, so groundedness is actually checkable
- Ingestion + chunking pipeline, embeddings, `pgvector` on the existing Neon Postgres (no
  new infrastructure), retrieval with citations returned alongside every answer
- An Alembic migration for the vector column/index — the first real test of F5 being fixed

*Evaluation*
- A golden Q&A set with ground-truth answers **and** ground-truth source citations
- Planted right-answer-wrong-reason cases (see [strategy](#the-central-idea-lead-with-evaluation))
- RAG metrics: groundedness / faithfulness, context precision and recall (ragas-style)
- An LLM-as-judge scorer, with the judge itself checked against human labels on a subset —
  an unvalidated judge is the same unevaluated-feature problem one level up
- Regression tests wired into CI as a new gate, with recorded baselines, so a retrieval
  change that degrades groundedness fails the build rather than shipping quietly

*Observability (thin slice, pulled forward)*
- Tracing on every model and retrieval call (Langfuse or OTel-GenAI spans), so eval results
  are attributable to concrete traces

**Done when**: `pytest` fails CI if retrieval quality regresses past a recorded baseline,
and the planted-case demonstration runs as a reproducible script.

**Delivers**: retrieval over pgvector with citations, a golden-set evaluation harness with
groundedness and context metrics, evals gating CI, and tracing on every model call.

---

### Phase 2 — Agent + tools + MCP

**Work**

*Analytics endpoints as agent tools (repurposed Phase 5)*
- Energy balance, adaptive TDEE, and the predicted-vs-actual validation endpoints — backend
  only, no dashboard. These exist to be *called by the agent*: "am I actually in a deficit
  this week?" is a genuine multi-step tool-calling question over a real schema with real
  per-user isolation, which a general-purpose chatbot surface would not exercise.
- Spec already drafted: [ENERGY_BALANCE_SPEC.md](ENERGY_BALANCE_SPEC.md)

*Agent*
- Multi-step tool-calling agent over: the user's own logged data, the food database, the
  analytics endpoints, and the Phase 1 retriever
- Provider-native tool use as the primary implementation (clean and current); optionally
  add LangGraph for keyword coverage, but not at the cost of clarity
- Extend the eval harness to trajectory evaluation — did the agent call the right tools in
  a sensible order, not merely end up with the right answer. This is the same
  right-answer-wrong-reason principle applied one level up, and it is the natural
  continuation of the Phase 1 story.
- Auth is the hard part and the differentiating part: tools must execute inside the calling
  user's isolation boundary. The existing `get_user_id` DI pattern is the right foundation.

*MCP server*
- Expose Gym-Bro's tools over MCP (log meal, query history, nutrition lookup, energy
  balance) so the app is usable from any MCP client

**Done when**: the agent answers a question that requires at least three tool calls
including retrieval, with trajectory evaluation in CI, and the MCP server works against a
real client.

**Delivers**: tool-calling agent scoped to the caller's isolation boundary, trajectory
evaluation, and an MCP server exposing the app's tools.

---

### Phase 3 — Production hardening

Treating the model as a production dependency: something that fails, costs money, and needs
timeouts and fallbacks like any other network call.

**Work**
- Retries with backoff, fallbacks across providers/models, timeouts on every model call
- Streaming responses — **see the serverless constraint below**
- Structured outputs and schema validation on model responses
- Cost and latency tracking per request and per user; caching (retrieval and response)
- Guardrails: input validation, output filtering, prompt-injection considerations for
  retrieved content (an agent that reads a corpus and calls tools that mutate user data is
  an injection surface — worth treating seriously and writing up)
- Full observability build-out on top of the Phase 1 thin slice

**Delivers**: retries, fallbacks and timeouts on model calls, structured outputs, cost and
latency accounting, caching, and guardrails over retrieved content.

---

## Known constraints and risks

**The serverless streaming problem.** The API runs as a Mangum-wrapped FastAPI app in a
Vercel serverless function (`api/handler.py`), on top of the ~1–2s cold starts
`ARCHITECTURE.md` already documents. LLM calls take seconds, streaming is expected UX, and
serverless functions have execution-time limits. This will need either moving the API off
Vercel functions to a long-running host, or accepting non-streaming responses. **Decide it
before Phase 1 rather than discovering it mid-implementation**, and record the reasoning
whichever way it goes.

**The data layer is synchronous.** Every router uses blocking SQLModel sessions inside
`async def` endpoints, so database latency occupies the event loop. It is tolerable today
because queries are small and per-instance concurrency is low, but an agent turn that makes
several tool calls against Postgres will make it matter. Moving to async SQLAlchemy belongs in
Phase 2, before the agent starts issuing multi-step tool calls — not bolted on during Phase 3.

**No real users, therefore no organic eval data.** The golden set has to be authored by
hand — 50–100 questions with ground-truth citations. This is the Phase 1 bottleneck and the
most likely reason for it to stall; budget it explicitly rather than treating it as setup.

**Cost.** Embedding a corpus is cheap; LLM-as-judge over a golden set on every CI run is
not. Cache judge results keyed by content hash and run the full suite on a schedule or on
label, not on every push.

## Open questions

- **pgvector on this Neon instance** — unverified. Confirm before committing to it:
  `SELECT * FROM pg_available_extensions WHERE name = 'vector';`
- Which corpus, specifically, with what licence for redistribution in a public repo
- Judge model choice and its cost per full eval run
- Whether to keep Vercel for the API (see the serverless constraint)

---

## Disposition of the old roadmap

| Old item | Disposition |
|---|---|
| **Phase 4.3** — photo frontend | **Promoted to Phase 0**, descoped (no Vercel Blob, no crop UI) |
| **Phase 5** — TDEE / energy balance | **Endpoints kept** as Phase 2 agent tools. Dashboard, setup wizard and charts **dropped**: 2–3 weeks of UI work that adds no capability the agent layer needs |
| E2E tests (Playwright) | Deferred |
| Lighthouse CI | Dropped |
| Error tracking (Sentry) | **Subsumed** by Phase 3 observability |
| Strong / Apple Health / Strava / MyFitnessPal integrations | Dropped for now. Reconsider if one becomes a useful agent tool |

---

## Environment setup (macOS)

The project was developed on Windows; this machine is macOS. Current state:

- **`python3` is 3.9.6** — too old. A venv exists at `gymbro-api/.venv` (gitignored) built on
  `/opt/homebrew/bin/python3.11`. `scripts/lib.sh` resolves an interpreter automatically.
- **Node** — installed during Phase 0 (v26 via Homebrew; the project requires `>=20`, CI uses 20).
- **Shell scripts** — `scripts/*.sh` added in Phase 0; the `.ps1` files remain for Windows.

```bash
# Everything CI runs, in one go
./scripts/pre-commit.sh

# Or individually
cd gymbro-api && JWT_SECRET_KEY=test-secret .venv/bin/pytest -q
cd gymbro-web && npm ci && npm run test:run

# Run the app
./scripts/start-all.sh
```
