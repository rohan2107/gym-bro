# ADR-0005: Food recognition behind a provider interface

- **Status**: Proposed
- **Date**: 2026-09-20

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

## Decision (proposed)

Introduce a `FoodRecognizer` interface. Make a multimodal-model provider the primary
implementation, with the Gemini free tier as the leading candidate. Keep the Vision
implementation as an optional provider and mock mode for development. Look up each recognised
item in USDA by name and scale to the estimated portion.

Before this is accepted, confirm in the provider console that the free tier works without a
card, and record the observed limits.

## Consequences

- Portion estimates fix the per-100g limitation.
- Less heuristic code: no label filter, and much less label-to-query mapping.
- Model output is non-deterministic and can be wrong, so tests use recorded responses
  ([ADR-0004](0004-record-replay-for-llm-calls.md)) and the review UI keeps every value
  editable.
- If the free tier trains on submitted content, user photos leave the app's control. The
  privacy cost is stated in the docs, and an alternative provider can be selected without code
  changes.

## Alternatives considered

Each row above. Keeping Vision as the only provider was rejected because it needs a billing
account.
