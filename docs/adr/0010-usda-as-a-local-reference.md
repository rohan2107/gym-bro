# ADR-0010: USDA FoodData Central as a local reference dataset, not a live dependency

- **Status**: Proposed
- **Date**: 2026-09-21

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
USDA data helps with the second and, through its household portion weights, with the first.

## Decision (proposed)

Treat USDA data as a **reference dataset the app owns**, not a service it calls per request.

1. **Now (done in M0.3b).** Keep the API on the request path, but as a helper: each lookup is
   time-boxed, and when USDA fails or has no match the model's own estimate is used and
   labelled as an AI estimate. A USDA problem lowers accuracy; it no longer ends the request.
2. **Next (M1.0).** Import the FNDDS, Foundation and SR Legacy releases into Postgres through
   an Alembic migration and a reproducible import script, trimmed to identifiers, descriptions,
   macros and household portions. Search them locally. The request path then makes no USDA
   call.
3. **Measure (M1.3).** Compare, on a golden set of the author's own meals with known weights:
   the model alone, the model with USDA lookup, and the model choosing among locally retrieved
   candidates. Choose from the results, not from preference.

The datasets are downloadable ([FoodData Central downloads](http://fdc.nal.usda.gov/download-datasets/)):
FNDDS is 3.7MB zipped as JSON (64MB unzipped) and Foundation 459KB, both as of their latest
releases; SR Legacy is 12MB zipped and will not be updated again. The API guide states the data
is CC0 and asks that FoodData Central be credited as the source
([API guide](http://fdc.nal.usda.gov/api-guide/)); the download page itself states no licence,
so this should be confirmed against the release notes before the data is committed or served.

## Consequences

- The request path loses its flakiest dependency, and search becomes fast and deterministic.
- Matching can be improved and measured offline, against a golden set, instead of guessed at
  against a moving API.
- USDA's household portions (a slice, a cup, with gram weights) give portion estimates real
  data to draw on.
- The app takes on ingestion, a schema and refresh: FNDDS is updated every two years and
  Foundation twice a year. This is the corpus work that [M1.1](../ROADMAP.md#m11-knowledge-corpus-and-retrieval)
  needs anyway.
- Coverage is limited to what USDA lists, which is mostly American foods. The AI-estimate
  fallback remains for anything it does not.
- Storage use on the free-tier database is small once trimmed, but the free-tier limit has not
  been checked.

## To verify before accepting

- Postgres search quality on Neon (trigram or full-text; embeddings only if measured to help),
  and which extensions the instance offers
- The licence, from the release notes, and the attribution wording
- That the trimmed data fits comfortably in the database's storage limit

## Alternatives considered

- **Keep calling the API on every request.** Rejected as the end state: reliability, latency
  and an unverified shared-IP limit, for a step that a local copy does better.
- **Model only.** Rejected: unsourced numbers with published error of tens of percent, and no
  way to evaluate them against a reference.
- **Model estimate first, USDA as a background check.** Kept as a possible use of the local
  copy: cheap once the data is local, and useful as a disagreement signal, but it does not
  need to block a response.
- **A commercial nutrition API.** Rejected under [ADR-0003](0003-hard-capped-providers-only.md).
