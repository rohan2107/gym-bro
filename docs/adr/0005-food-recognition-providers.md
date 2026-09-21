# ADR-0005: Food recognition behind a provider interface

- **Status**: Accepted
- **Date**: 2026-09-20
- **Accepted**: 2026-09-21

## Context

Photo analysis currently uses Google Cloud Vision, which requires a billing account and so
conflicts with [ADR-0003](0003-hard-capped-providers-only.md). It also returns labels, which
cannot express portion size, so nutrition is reported per 100g. A multimodal model can return
structured items with estimated portions.

Checked against provider documentation on 2026-09-20:

| Option | Stops at its limit? | Notes |
|---|---|---|
| Gemini API free tier | Yes: `429` beyond limits; billing must be set up deliberately to go further | Free-tier content is used to improve Google products; limits are only visible in the console; the pricing page does not say whether a card is required |
| Cloudflare Workers AI, free plan | Yes: 10,000 neurons a day, then operations fail | A Llama 3.2 vision model is available; cost of one image in neurons is unknown |
| OpenRouter `:free` models | Yes: 20 requests a minute, 50 a day below $10 purchased | The free model list rotates; which accept images is unverified |
| Vercel AI Gateway, prepaid credits | Yes: prepaid balance and budgets that return `402` | Not free; buying credits ends the monthly free credit |
| Hugging Face Inference Providers | Yes | $0.10 a month for free users, too little to use |

## Decision

Introduce a `FoodRecognizer` interface. The primary implementation is the Gemini API on its
free tier; Google Cloud Vision stays as an optional provider, and mock mode serves development.
The provider is chosen by `FOOD_RECOGNITION_PROVIDER`, an unknown value fails at startup, and
each provider falls back to mock mode when its credentials are missing (which the endpoint
refuses on a deployment).

Models are pinned by id, never a `-latest` alias, because an alias changes under the app and
makes any measured accuracy unrepeatable. The primary is `gemini-3.5-flash-lite` and the
fallback `gemini-3.1-flash-lite`. A `429` or `5xx` from the primary is retried once on the
fallback, which has its own quota; other client errors are not retried. When both fail the
request fails closed and the user's quota is refunded.

The model's output is treated as untrusted: it is constrained to a JSON schema, then each name
is normalised and length-limited before it becomes a nutrition search term.

Each recognised item is looked up in USDA by name. Scaling to an estimated portion is
[M0.3b](../ROADMAP.md#m03b-portions-and-a-graceful-fallback), not part of this decision's first increment.

## Verification

Checked on 2026-09-21 with a key created in Google AI Studio:

| Question | Observed |
|---|---|
| Card or billing account requested? | No. The key page shows **Free tier**; no billing account is linked |
| Limits | 15 requests a minute, 250K tokens a minute and 500 requests a day, per model |
| Cost of one photo | About 1,100 input tokens, of which 1,080 are the image |
| Works on a real meal photo? | Yes: a pizza photo returned `pizza` at 0.99 from both stable lite models, in 1.7s and 3.5s |
| Blank image | Returned an empty list, not an invented food |
| `gemini-2.5-flash-lite` | `403`: not available to a new project, so not used |

One easy photo is a smoke test, not an accuracy result. Accuracy is measured by the evaluation
harness in [Phase 1](../ROADMAP.md#phase-1-retrieval-and-evaluation).

## Consequences

- Names from a model are more specific than Vision's labels, so much of the label filtering and
  mapping is no longer on the critical path. Portion estimates, which fix the per-100g
  limitation, follow in M0.3b.
- Less heuristic code: no label filter, and much less label-to-query mapping.
- Model output is non-deterministic and can be wrong, so tests use responses recorded from the
  live API ([ADR-0004](0004-record-replay-for-llm-calls.md) describes the fuller mechanism) and
  the review UI keeps every value editable.
- Free-tier content may be used to improve Google's products. Meal photos are low sensitivity,
  and the app says so where the photo is taken. The app itself never stores the photo. A
  different provider can be selected by configuration.
- Pinned model ids can be retired. The fallback model is the mitigation; a retired primary shows
  up as a failure rate in the logs and is fixed by changing one setting.

## Alternatives considered

Each row above. Keeping Vision as the only provider was rejected because it needs a billing
account.
