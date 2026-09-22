# ADR-0010: USDA FoodData Central as a local reference dataset, not a live dependency

- **Status**: Accepted
- **Date**: 2026-09-21
- **Accepted**: 2026-09-22

## Context

Photo analysis takes a food name from a model and looks its nutrition up in USDA FoodData
Central through the search API. In the first days of live use this was the weakest part of the
product:

- **Reliability.** Any search filter containing `Survey (FNDDS)` failed with `400` about half
  the time, at random (measured 2026-09-21; [AUDIT F16](../AUDIT_2026-09.md)). Unfiltered
  search succeeded 45 of 45, but responses run to several hundred KB and a slow lookup holds
  the user up.
- **Match quality.** USDA's own first hit is often wrong ("Dessert pizza" for pizza, "Apple,
  candied" for apples, a chicken lunchmeat with no macro data). The service now filters and
  ranks results with a heuristic whose accuracy is unmeasured.
- **Limits.** The documented default is 1,000 requests an hour per IP address, and exceeding it
  blocks the key for an hour. One user would not reach it, but serverless functions share
  outbound IP addresses, so how the limit behaves on Vercel is unverified.
- **Undocumented header.** The API guide documents the key only as a query parameter. The
  `X-Api-Key` header works today (checked live) but is not in that guide.

The alternative of relying on the model alone was considered. Published evidence is against it:

- A study of three multimodal models on 52 standardised meal photographs found energy errors
  of about 36% for the two best and 64% for Gemini 1.5 Pro (an older model than the one used
  here), with all of them underestimating more as portions grew
  ([Performance Evaluation of 3 Large Language Models for Nutritional Content Estimation from
  Food Images](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12513282/)).
- DietAI24 grounded a multimodal model in the FNDDS database by retrieval and reported a 63%
  reduction in mean absolute error against the ungrounded model, while noting that it cannot
  handle foods absent from FNDDS and was tested only on GPT models and mostly American foods
  ([DietAI24](https://pmc.ncbi.nlm.nih.gov/articles/PMC12589391/)).

Portion size, not the per-100g density that USDA supplies, is the largest source of error.
USDA data helps with the second and, through its household portion weights, could help with the
first in a later increment.

## Decision

USDA data is a **reference dataset the app owns**, not a service it calls per request.

1. **M0.3b (done first).** Kept the API on the request path, but as a helper: each lookup was
   time-boxed, and when USDA failed or had no match the model's own estimate was used and
   labelled as an AI estimate. This absorbed the reliability problem while the rest of this
   decision was built.
2. **M1.0 (this decision, done).** `scripts/build_usda_dataset.py` downloads USDA's Foundation,
   Survey (FNDDS) and SR Legacy bulk JSON releases (Branded excluded - its names are brand text
   and its values are label claims), trims each food to name, data type and the four macros,
   and writes `data/usda_foods.json`, committed to the repository. An Alembic migration loads
   it into a `usda_food` table the same way every other table is created - once, automatically,
   on merge to `main`. `NutritionService.search_food` now queries this table. The request path
   makes no USDA call.
3. **M1.3 (future).** Compare, on a golden set of the author's own meals with known weights:
   the model alone, the model with local lookup, and the model choosing among locally retrieved
   candidates. Choose from the results, not from preference.

## What building it found

- **Real counts.** Foundation (2026-04-30 release): 395 foods, of which **32 entries in the raw
  JSON array are literally `null`** - not missing fields, the array itself contains nulls - and
  42 more have no kcal energy value at all, leaving 321 usable. Survey/FNDDS (2024-10-31): 5,432,
  one without usable energy. SR Legacy (2018-04, its final release): 7,793, all usable. **13,545
  foods after trimming, 2.6MB** as JSON, with no `fdc_id` collisions across the three releases.
- **Energy needs the same care at ingestion that the old query-time code took.** Foundation and
  SR Legacy list Energy in both kJ and kcal; Foundation sometimes carries only a computed
  Atwater value (`Energy (Atwater General Factors)`, `...Specific Factors`) instead of a
  directly measured one. `build_usda_dataset.py` resolves this once, offline, rather than on
  every query.
- **Licence:** confirmed via the [FoodData Central API guide](http://fdc.nal.usda.gov/api-guide/) -
  public domain (CC0), crediting FoodData Central as the source is requested, not required. The
  bulk downloads themselves need no API key.
- **Storage:** checked against the actual Neon project (2026-09-22): 31.55MB used of the 500MB
  free-tier limit, so the ~2.6MB table fits with room to spare.
- **Search plan changed while building it.** The plan going in was Postgres trigram search
  (`pg_trgm`). Building it surfaced a reason not to: this project's tests run migrations against
  a fresh SQLite database for speed (`test_migrations.py`), and `pg_trgm`/GIN indexes are
  Postgres-only, which would have forced either a Postgres-only test path or skipping trigram
  search in tests. A plain case-insensitive substring prefilter needs no extension, works
  identically on SQLite and Postgres, and loses nothing at this size: an unfiltered scan for
  even a common single word ("chicken": ~800 of 13,545 rows) took single-digit milliseconds in
  testing, and the real ranking already happens in Python over whatever the SQL query returns
  (unchanged from the heuristic used against USDA's own search results - more matching words, a
  name starting with a query word, fewer qualifiers, "raw", the better data type, then the
  shorter name). No index was added for the same reason: correct first, and "add one if this
  ever gets slow" is more honest than indexing against no measurement.

## Consequences

- The request path loses its flakiest dependency: nutrition lookup makes no external call and
  needs no API key, in every environment. There is no longer a "mock mode" for it to have.
- Matching can be improved and measured offline, against a golden set, instead of guessed at
  against a moving API.
- The app takes on refresh: FNDDS is updated every two years and Foundation twice a year;
  `scripts/build_usda_dataset.py` is re-run and the migration re-generated when that happens.
  This is a smaller version of the corpus work [M1.1](../ROADMAP.md#m11-knowledge-corpus-and-retrieval)
  needs anyway, done first on this more concrete case.
- Coverage is limited to what USDA lists, which is mostly American foods, and the trimmed data
  drops household portions and footnotes along with everything else not currently used. The
  AI-estimate fallback remains for anything the table does not cover.
- A future data refresh replaces the whole table (the migration is not incremental), which is
  fine for reference data with no user records in it.

## Alternatives considered

- **Keep calling the API on every request.** Rejected as the end state: reliability, latency
  and an unverified shared-IP limit, for a step a local copy does better.
- **Model only.** Rejected: unsourced numbers with published error of tens of percent, and no
  way to evaluate them against a reference.
- **Model estimate first, local lookup as a background check.** Not pursued now; possible later
  since the data is already local and cheap to query, but it does not need to block a response.
- **Postgres trigram search (`pg_trgm`).** Rejected after prototyping it, for the test-portability
  and unnecessary-at-this-size reasons above. Revisit only if the dataset grows enough that a
  full scan measurably matters.
- **A commercial nutrition API.** Rejected under [ADR-0003](0003-hard-capped-providers-only.md).
