# Roadmap

**Last updated**: September 20, 2026
**Status**: Phase 0 (foundation) is largely complete. Phase 1 has not started.

This is the single forward-looking plan for Gym-Bro. Completed work is recorded in the
[changelog](../CHANGELOG.md), the September 2026 audit that shaped this plan is in
[AUDIT_2026-09.md](AUDIT_2026-09.md), and individual technical decisions are in [adr/](adr/).

## Goal

Extend Gym-Bro from a fitness tracker with one AI feature into a system whose LLM behaviour is
**measured, observable and resilient**: retrieval whose groundedness is scored, an agent whose
tool trajectories are checked, and model calls that are traced, bounded and costed like any
other production dependency.

The app is a deliberately good host for this: it has real per-user data, authentication and
isolation, a relational schema under migration control, CI/CD, and an AI feature already in
place. The plan adds capability to that foundation rather than starting beside it.

## Principles

1. **Evaluation leads.** The harness that measures a feature is designed before the feature is
   tuned, and the retrieval implementation is fitted to it, not the reverse. The failure worth
   designing against is the *right answer for the wrong reason*: correct macros from a
   retrieval step that fetched the wrong document. Accuracy scoring passes that; groundedness
   scoring catches it. See [EVALUATION.md](EVALUATION.md).
2. **Hard-capped, zero-spend providers.** Every external service must stop at its limit rather
   than bill. Budgets are alerts, not caps, so they do not count. See
   [ADR-0003](adr/0003-hard-capped-providers-only.md).
3. **Reproducible by construction.** LLM calls are recorded and replayed, so CI makes no
   network calls, spends nothing, and is deterministic. See
   [ADR-0004](adr/0004-record-replay-for-llm-calls.md).
4. **Models are dependencies behind interfaces.** Providers are swappable, configured through
   `Settings`, and never called directly from routers.
5. **Incremental.** Each milestone is one pull request, independently reviewable and
   revertible, and leaves the system working.
6. **Honest reporting.** Metrics ship with the model, date, sample size and commit that
   produced them. Null results and known limits are reported, not omitted.

## Where things stand

| Area | State |
|---|---|
| Core app (check-ins, meals, workouts, OAuth, PWA) | Shipped |
| Schema management | Alembic is the sole owner; a fresh `alembic upgrade head` reproduces the models |
| Photo analysis | Working on the live site (photo of bananas checked on a phone, 2026-09-21): a Gemini free-tier provider behind an interface, USDA for grounding with the model's own estimate as fallback, Vision optional. Portions and macros are estimates whose accuracy is unmeasured |
| CI/CD | 8 required gates on every PR; migrations applied on merge to `main` |
| Tests | Backend and frontend suites, each gated at 80% coverage in CI |
| Audit | 16 findings fixed; 7 open, tracked in the [audit](AUDIT_2026-09.md#open-findings) |

Production auth was verified after the fix: the `X-User-Id` impersonation header that
previously returned `200` now returns `401`.

## Phase order

The order is chosen so a production-shaped system exists early. Reliability and observability
are weighted alongside agents, and the project stays backend-shaped.

```
Phase 0  Foundation             finish the existing AI feature; remove blockers
Phase 1  Retrieval & evaluation retrieval with citations; the evaluation harness; tracing
Phase 2  Resilience             timeouts, retries, fallbacks, structured outputs, caching
Phase 3  Agents & tools         async data layer; analytics; agent; trajectory evals; MCP
Phase 4  Hardening              injection defences; load test and SLOs; scheduled evals
```

Earlier drafts numbered these differently. Old "Phase 3-lite" is now Phase 2, old "Phase 2"
(agents) is now Phase 3, and the rest of old "Phase 3" is Phase 4.

Sizes are rough: **S** is a day or two, **M** roughly a week, **L** longer. There are no fixed
dates. Work is sequenced by dependency, and a slipped milestone slips everything after it.

---

## Phase 0: Foundation

**Goal**: a working, honestly documented base to build on.

| ID | Increment | Size | State |
|---|---|---|---|
| M0.1 | Documentation restructure and this roadmap | S | Done |
| M0.2 | Runtime alignment | S | Done |
| M0.3a | Food-recognition providers | M | Done |
| M0.3b | Portions and a graceful fallback | M | Done |
| M0.4 | Stale frontend after a deploy (service worker) | S | Done |
| M0.3c | Portion editing | S | Done |
| M0.3d | iPhone device check (HEIC, camera) | S | Not started |

### M0.1: Documentation restructure

Consolidates the two overlapping roadmaps, records decisions as ADRs, replaces three stale
design documents, and adds operations and evaluation documentation.

### M0.2: Runtime alignment

Vercel deployed on versions CI never tested: Python 3.12 (no version was specified, so Vercel
picked its default) against CI's 3.11, and Node 24 against CI's 20.

- Pin the Python version for Vercel (`.python-version`) and make CI match it
- Pin the Node version (`engines` and CI already say 20; make Vercel honour it)
- Remove the unused `mangum` dependency from both requirements files and the parity test's
  runtime-critical list. The handler exposes the ASGI app directly and never imports it.

**Done when**: CI and Vercel run the same Python and Node versions, and the docs say so.

### M0.3a: Food-recognition providers

The photo pipeline was Vision labels → label mapping → USDA. Vision needs a billing account,
which conflicts with principle 2. This increment replaces it with a provider interface and a
provider that needs no billing account ([ADR-0005](adr/0005-food-recognition-providers.md)).

- A `FoodRecognizer` interface; providers selected through `Settings`, an unknown one failing
  at startup
- A Gemini provider on the free tier: schema-constrained JSON, pinned model ids, a fallback
  model, output treated as untrusted, failing closed with the quota refunded
- Vision kept as an optional provider; mock mode kept for development
- Image validation moved out of Vision so every provider shares it
- Tests run against responses recorded from the live API, not live calls
- A data-use notice where the photo is taken

**Done when**: the provider is swappable by configuration alone, every failure degrades to
manual entry, and photo analysis works on the live site with no billing account attached. The
last part needs `GEMINI_API_KEY` set in Vercel and is checked after merge.

### M0.3b: Portions and a graceful fallback

Names alone carry no portion size, and USDA failing ended the request. This increment makes
the flow work when USDA does not, and gives the numbers a portion.

- The model also estimates the portion in grams and the macros for it; both are optional and
  validated against plausible bounds, and a partial estimate is discarded whole
- USDA per-100g values are scaled to the estimated portion
- Lookups run concurrently and each is time-boxed; when USDA fails or has no match, the model's
  own estimate is used and marked `ai_estimate`, so a USDA problem lowers accuracy instead of
  ending the request
- The review screen says which it is: USDA per 100g, USDA scaled to a portion, or an AI
  estimate that is not from a nutrition database
- Per-model Gemini timeout cut to 12 seconds so a hanging model does not hold the user before
  the fallback model is tried
- Decision recorded in [ADR-0010](adr/0010-usda-as-a-local-reference.md)

**Done when**: a photo on the live site returns usable numbers with USDA unavailable, and the
source of each number is stated.

### M0.4: Stale frontend after a deploy

The service worker (`gymbro-web/public/sw.js`) served the page itself, `/` and `/index.html`,
**cache-first for up to 24 hours**, and never changed its cache name, so browsers saw no reason
to replace it. After a deploy a device could keep running the old frontend, which loads the old
JavaScript, against the new API, which is not cached that way.

Seen on 2026-09-21: the review screen showed numbers scaled to a portion (exactly 3.6 times
USDA's per-100g values for a banana) under the old note "Nutrition is per 100g from USDA". The
mechanism is reproduced by the tests below, which fail against the old worker; it has not been
confirmed on the device itself.

- Navigation requests (`/`, any route) are **network-first**, falling back to the cached shell
  when offline or when the network takes longer than four seconds, so a poor connection does
  not hang the app. A late response still refreshes the cache
- Content-hashed assets under `/assets/` stay **cache-first** and never expire: their filenames
  change with every build, so a cached copy cannot be stale
- The cache name is bumped (`gymbro-v3`), so activation drops the shell cached by the old
  worker, and `sw.js` itself changed, so browsers install the new worker
- API and auth requests are unchanged
- Tests run `sw.js` against a fake cache and fetch (`src/test/serviceWorker.test.ts`): a deploy
  shows on the next load, offline and slow-network fallbacks, hashed assets, and requests the
  worker must leave alone. The stale-page tests fail against the previous worker

**Done when**: after a deploy, reloading the app shows the new frontend without clearing site
data, and the app still opens offline from the last cached shell. Confirmed on a phone on
2026-09-22: a photo taken the next day, with no site data cleared, showed the current note
("Estimated for about 250g, from USDA values scaled to the portion.").

### M0.3c: Portion editing

Every USDA and AI-estimate result now carries a numeric `portion_g`, defaulting to 100 for a
plain per-100g result, so this applies uniformly regardless of source.

- The review screen has an editable "Portion (g)" field
- Changing it rescales calories and every macro, re-derived from the API's original values each
  time so repeated edits do not compound rounding error
- The basis note updates to the edited portion, not just the one the API returned
- The portion itself is not sent when saving; only the resulting macros are, matching what the
  food log already stores

**Done when**: changing the portion updates the macros. Done in this increment; not yet
confirmed on a device (see [M0.3d](#m03d-iphone-device-check-heic-camera)).

### M0.3d: iPhone device check (HEIC, camera)

Live camera capture already works: confirmed on an iPhone with three photos (bananas, eggs,
chicken), all correctly analysed, and a photo from a Mac browser upload (MPO format) was
accepted correctly too.

Checking an existing HEIC photo from the library turned out not to be possible as scoped:
[O10](AUDIT_2026-09.md#open-findings) found that `PhotoCapture` opens the camera directly on
iOS with no library option at all, so there is currently no way to select an existing photo -
HEIC or otherwise - on a phone. That check is blocked on O10, not merely undone, and is removed
from this milestone's scope until O10 has a fix to build on.

What is still achievable and not yet done:

- The portion field ([M0.3c](#m03c-portion-editing)) on a touchscreen, including its numeric
  keyboard, using a photo taken with the live camera

**Done when**: editing the portion on the device works as it does in tests. The HEIC-from-library
check moves to whatever increment fixes O10.

---

## Phase 1: Retrieval and evaluation

**Goal**: a retrieval feature whose quality is measured, gated in CI, and traceable.

| ID | Increment | Size | Depends on |
|---|---|---|---|
| M1.0 | USDA reference dataset in Postgres, replacing the live API | M | Done |
| M1.1 | Knowledge corpus and retrieval with citations | L | M0.3a (provider pattern) |
| M1.2 | LLM record/replay layer | M | M1.1 |
| M1.3 | Golden set and evaluation harness, gated in CI | L | M1.2 |
| M1.4 | Tracing and cost/latency tracking | M | M1.2 |
| M1.5 | Planted cases, judge validation, retrieval ablation | M | M1.3, M1.4 |

### M1.0: USDA reference dataset

Decided in [ADR-0010](adr/0010-usda-as-a-local-reference.md) (accepted): the app owns the
reference data instead of calling the API per request.

- Gates cleared: licence confirmed CC0 from the API guide; Neon storage checked (31.55MB used
  of 500MB free tier); trigram search (`pg_trgm`) was prototyped and then dropped in favour of
  a plain substring prefilter, because `pg_trgm` is Postgres-only and this project's tests run
  migrations against SQLite for speed - see ADR-0010's "What building it found"
- `scripts/build_usda_dataset.py`: downloads Foundation, Survey (FNDDS) and SR Legacy, trims to
  name/data type/macros, writes `data/usda_foods.json` (13,545 foods, 2.6MB), records the
  releases used and the licence
- Alembic migration creates `usda_food` and loads that file, the same way every other table is
  created
- `NutritionService.search_food` queries the local table; the request path makes no USDA call;
  nutrition lookup has no mock mode any more (no key to be missing)
- Household portions and a genuinely improved match ranking are not in this increment - see the
  backlog

**Done when**: photo analysis makes no USDA request, the migration is applied by CI, and search
results for a fixed set of queries are covered by tests. Confirmed 2026-09-22: the merge to
`main` ran `Apply DB Migrations` (not skipped, as it is on a PR's own CI) and it succeeded, so
the live table is populated. A live request has not yet reached the nutrition-lookup step
itself to confirm a real hit end to end, because both Gemini models were briefly down at the
same time on the one attempt made so far (unrelated - see the backlog item on retrying a
transient Gemini failure).

### M1.1: Knowledge corpus and retrieval

- **Gate first**: confirm `pgvector` is available on the Neon instance
  (`SELECT * FROM pg_available_extensions WHERE name = 'vector';`). If it is not, the design
  changes and [ADR-0008](adr/0008-embedding-model.md) is revisited.
- Choose a corpus with redistributable licences and citable provenance
  ([ADR-0007](adr/0007-knowledge-corpus.md))
- Ingestion: fetch, clean, chunk, embed, store, with source, section, URL and licence on every
  chunk
- Alembic migration for the document/chunk tables and vector index
- Authenticated search endpoint returning ranked chunks with citation metadata

**Done when**: search returns cited chunks in production, the migration is applied by CI, and
a test asserts the stored embedding dimension matches the configured model.

### M1.2: LLM record/replay layer

- One client interface for generation and embeddings, with three modes: **replay** (default in
  CI; a cache miss fails loudly), **record** (explicit, writes cassettes) and **passthrough**
- Cassette key is a hash of provider, model, parameters and full input
- Model calls made anywhere in the app go through it

**Done when**: the entire test suite runs with the network disabled, and a changed prompt
fails with a message that says how to re-record.

### M1.3: Evaluation harness

- Golden set v1 of 50–100 questions with reference answers and gold citations, split without
  leakage (see [EVALUATION.md](EVALUATION.md))
- Retrieval metrics (recall@k, MRR, context precision) and generation metrics (answer
  correctness, groundedness, citation accuracy)
- A runner that emits a machine-readable report, and a committed baseline
- A CI gate that fails when a tracked metric falls below baseline minus a stated tolerance

**Done when**: a change that degrades retrieval or groundedness fails CI, and the report
regenerates from cassettes with no network.

### M1.4: Tracing and cost

- OpenTelemetry spans following the GenAI semantic conventions on every model and retrieval
  call, exported to one backend (chosen at implementation, recorded as an ADR)
- Per-call latency, token counts and estimated cost. Free-tier calls cost nothing, so cost is
  computed from list prices and labelled as an estimate.
- Trace IDs attached to evaluation results so a bad score links to the call that produced it

**Done when**: an evaluation run produces inspectable traces and a report of latency and
estimated cost per stage.

### M1.5: Planted cases, judge validation, ablation

- The planted right-answer-wrong-reason set, and a reproducible demonstration that
  accuracy-only scoring passes it while groundedness scoring fails it
- Judge validation: a hand-labelled subset, agreement reported with its uncertainty
  ([ADR-0009](adr/0009-judge-model-and-validation.md))
- A small retrieval ablation (chunk size, hybrid BM25 + vector, reranking), reported honestly
  including null results

**Done when**: one command regenerates every table in the README, and Phase 1 is tagged.

---

## Phase 2: Resilience

**Goal**: treat model calls as the unreliable network dependencies they are.

| ID | Increment | Size | Depends on |
|---|---|---|---|
| M2.1 | Resilience layer | M | Phase 1 |

### M2.1: Resilience layer

- Timeouts on every model call, and retries with exponential backoff and jitter
- Fallback to a second provider or model, and a circuit breaker
- Structured outputs with schema validation and a bounded repair attempt
- Response caching keyed by content hash
- A streaming decision, settled by an experiment
  ([ADR-0006](adr/0006-streaming-on-vercel.md))

**Done when**: fault-injection tests (timeout, `429`, malformed output, provider outage) pass,
and the behaviour of each failure mode is documented.

---

## Phase 3: Agents and tools

**Goal**: an agent that answers multi-step questions over the user's own data, safely.

| ID | Increment | Size | Depends on |
|---|---|---|---|
| M3.0 | Async data layer | M | Phase 2 |
| M3.1 | Analytics endpoints | M | M3.0 |
| M3.2 | Agent loop and tools | L | M3.1 |
| M3.3 | Trajectory evaluation and safe mutation | M | M3.2 |
| M3.4 | MCP server with authentication | S | M3.3 |

### M3.0: Async data layer

Every router uses synchronous SQLModel sessions inside `async def` handlers, so database
latency occupies the event loop. An agent turn that makes several tool calls will make that
matter. It is its own milestone because it touches every router and most tests, with no
behaviour change.

**Done when**: no blocking database call runs inside an async handler and the suite is green.

### M3.1: Analytics endpoints

Energy balance, adaptive TDEE and consistency analysis as backend endpoints only, per
[ENERGY_BALANCE.md](ENERGY_BALANCE.md). There is no dashboard; these exist to be called as
tools. Tested against synthetic trajectories with planted intake bias, so the expected answer
is known.

### M3.2: Agent loop and tools

- Provider-native tool calling, a tool registry, step and budget limits
- Tools: query the user's logs, look up food, retrieve from the corpus, run analytics
- **The user id is injected from the authenticated session and never accepted from the model**

**Done when**: the agent answers a question needing at least three tool calls including
retrieval, and every step is traced.

### M3.3: Trajectory evaluation and safe mutation

- Trajectory scoring: right tool, right arguments, right order, no forbidden calls
- Write tools require confirmation, carry idempotency keys, and are permission-scoped
- Trajectory cases gated in CI

### M3.4: MCP server

Expose the tools over MCP with authentication, tested against a real client.

---

## Phase 4: Hardening

| ID | Increment | Size | Depends on |
|---|---|---|---|
| M4.1 | Prompt-injection defences | M | Phase 3 |
| M4.2 | LLM-path load test and SLOs | M | Phase 3 |
| M4.3 | Scheduled full evaluation | S | M1.3 |

- **M4.1**: retrieved text and tool output are untrusted input to an agent that can mutate
  user data. Adversarial corpus items and tool outputs are added to the evaluation, and the
  defences are tested against them.
- **M4.2**: a load test that exercises the LLM path, and one or two stated latency and
  availability objectives for the assistant endpoint, with measurements.
- **M4.3**: the full judged evaluation runs on a schedule or a label rather than every push,
  with judge outputs cached, to control cost.

---

## Milestone definition of done

Every milestone, regardless of phase:

- Tests for new behaviour; test counts in the docs updated
- `./scripts/pre-commit.sh` passes and CI is green
- Any decision recorded or updated as an ADR
- User-facing or operational changes reflected in [ARCHITECTURE.md](ARCHITECTURE.md) and
  [DEPLOYMENT.md](DEPLOYMENT.md)
- For evaluated features: numbers in the README with how to reproduce them, and a committed
  baseline
- [CHANGELOG.md](../CHANGELOG.md) updated, and the state column above updated

## Risks and open questions

| Risk | Effect | Mitigation |
|---|---|---|
| pgvector unavailable or constrained on Neon's free tier | Retrieval design changes | Gated at the start of M1.1, before any other work |
| Free-tier limits are unpublished or change | Evaluation or the feature throttles | Record/replay keeps CI off the network; pin model ids in config; fallback provider |
| Free tiers may train on submitted content | Privacy of user photos and queries | State it in the docs; keep sensitive paths off free tiers ([ADR-0005](adr/0005-food-recognition-providers.md)) |
| A weak local judge | Misleading evaluation scores | Validate against human labels and publish the agreement ([ADR-0009](adr/0009-judge-model-and-validation.md)) |
| Evaluating a different model from the one shipped | Numbers describe the wrong system | Record generation with the production model; label every metric with its model ([ADR-0004](adr/0004-record-replay-for-llm-calls.md)) |
| Query-time embedding cannot run locally on Vercel | Dev and prod vectors differ | One hosted embedding model everywhere ([ADR-0008](adr/0008-embedding-model.md)) |
| Golden-set authoring effort | Stalls Phase 1 | Budget it as its own work item, not setup |
| Async migration blast radius | Regressions across every router | Its own milestone, no behaviour change, existing suite as the safety net |
| Model ids and free tiers churn quickly | Silent behaviour change | Model ids pinned in config and recorded in every cassette and report |
| Neon scale-to-zero cold starts | Added retrieval latency | Measure in M1.4; report it separately from model latency |

## Backlog

Unscheduled, in rough priority order. Open audit findings are described in
[AUDIT_2026-09.md](AUDIT_2026-09.md#open-findings).

- OAuth hardening: `state` parameter, `email_verified` check, no raw provider errors to clients
- Callback page double-fires its effect in development
- Camera-only photo capture on mobile ([O10](AUDIT_2026-09.md#open-findings)): offer a way to
  choose an existing photo, not only the live camera - most simply, drop `capture="environment"`
  and let the OS's own action sheet offer the choice, at the cost of the direct-to-camera
  one-tap convenience that was the point of using it
- HEIC support server-side, only if device testing shows iOS delivers HEIC
- Widen the lint rule set (`UP`, `DTZ`, `I`) as its own change
- Gemini resilience: both free-tier models returned 503 within 4 seconds of each other on
  2026-09-22 (Google-side capacity, not a bug - the fallback ran correctly and failed closed
  with a clear message, no quota spent). Two small, low-cost improvements: swap which model is
  primary (config only, no code change) as a hedge against one model seeing disproportionate
  load; add a single short backoff-and-retry after both models fail once, since "high demand"
  503s are typically transient. Cheap enough to do alongside M0.3d rather than treat as its own
  milestone
- Offline writes in the service worker
- End-to-end browser tests (Playwright)
- USDA household portions, imported alongside the macros already in `usda_food`, to turn a
  model's portion description ("a slice", "a cup") into grams instead of relying only on the
  model's own gram estimate
- Re-run `_best_match`'s ranking against the full local dataset with real queries and measure
  it, rather than the dozen or so spot-checks so far (Phase 1's evaluation harness is the
  proper place for this, once it exists)

## Deferred or dropped

| Item | Decision |
|---|---|
| Energy-balance dashboard, setup wizard and charts | Dropped. The endpoints stay as agent tools (M3.1) |
| Strong CSV import, Apple Health, Strava, Garmin, MyFitnessPal | Deferred. Reconsider only if one becomes a useful agent tool |
| Lighthouse CI | Dropped |
| Sentry | Subsumed by tracing (M1.4) |
| Model fine-tuning | Not planned |
| Front-end polish beyond the minimum the features need | Deprioritised |
