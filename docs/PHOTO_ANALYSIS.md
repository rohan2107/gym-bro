# Photo analysis

Photograph a meal, get food predictions and macros, review and edit them, then save. This
document describes the pipeline as built, its failure behaviour and its limits. The original
plan this replaces is in the git history.

## User flow

1. On the Meals page the user taps **Log from photo**. On a phone this opens the camera; on a
   desktop it opens the file picker.
2. The client checks the file (image type, not HEIC, at most 30MB), scales it down to at most
   1600px and re-encodes it as JPEG in the browser, then uploads it. A typical result is a few
   hundred KB.
3. The server returns predictions, each with nutrition for an estimated portion (or per 100g
   when no portion was estimated) and the source of the numbers, plus the user's remaining
   daily quota.
4. The user reviews the predictions, picks between detected foods, edits any value, and saves
   or discards. Nothing is written until they save.

If any step fails, the manual meal form is still available on the same page.

## Pipeline as built

```
POST /api/food-logs/from-photo          (multipart, authenticated)
  refuse if on a deployment and a service is in mock mode           -> 503, no quota spent
  content type must be image/*                                       -> 400
  stream the body in 64KB chunks, cap at 10MB                        -> 413
  validate with Pillow: format, minimum 200x200, not HEIC            -> 400
  reserve one unit of the user's daily quota (row-locked, atomic)    -> 429 if none left
  configured provider: names the foods in the photo (top 3)
      provider failure, quota or block                               -> 503, quota refunded
      nothing recognised                                             -> 404, quota refunded
  ground each food in USDA, concurrently, each lookup time-boxed to 10s
      USDA value found                       -> scaled to the estimated portion (source: usda)
      USDA failed or no match, model estimate -> the model's estimate (source: ai_estimate)
      neither                                -> 404 if USDA had no match, 503 if it errored;
                                                quota refunded
  return predictions, quota state, image info
```

Quota is reserved before the expensive calls and refunded when detection or lookup fails, so a
failed request never costs the user a photo. The limit is 30 per user per day, enforced by
[rate_limiter.py](../gymbro-api/app/services/rate_limiter.py) with `SELECT ... FOR UPDATE`.

### Components

| Component | Responsibility |
|---|---|
| `FoodRecognizer` | The interface every provider implements; the endpoint depends only on this |
| `GeminiRecognizer` | Default provider. Asks a Gemini model for the foods as schema-constrained JSON |
| `VisionService` | Optional provider. Calls Vision's `images:annotate` over REST and filters and ranks labels |
| `image_validation` | Local checks shared by all providers: format, size, dimensions, HEIC |
| `NutritionService` | USDA FoodData Central lookup: header credential, retry, result filtering and ranking |
| `food_mapping` | Maps a few common names to better USDA queries; other names are searched as given |
| `RateLimiter` | Atomic per-user daily quota |
| `PhotoCapture`, `MealReview` | The capture and review components in the frontend |

All services are injected as dependencies, so tests replace them and no test calls a real
service. The provider is chosen by configuration
([ADR-0005](adr/0005-food-recognition-providers.md)); Vision's REST integration is described in
[ADR-0002](adr/0002-vision-rest-api-with-header-credentials.md).

### Gemini provider

The request asks for the distinct foods in the photo, with an estimate of each portion in grams
and the calories and macros for it, and constrains the reply to a JSON schema
(`{"foods": [{"name", "confidence", "estimated_grams", "calories", "protein_g", "carbs_g",
"fat_g"}]}`) at temperature 0. The estimate fields are optional. The credential is sent in an
`x-goog-api-key` header, never in the URL, because httpx puts the URL in its exception
messages and this app logs them.

The reply is untrusted input. Names are lower-cased, whitespace-collapsed and limited to 60
characters; confidences are clamped to [0, 1]; items of the wrong type are dropped; duplicates
keep the highest confidence; at most three are returned. The portion must be between 0 and
3,000g and the calories between 0 and 5,000 with each macro between 0 and 500g, otherwise it
is dropped: a confident 40,000 kcal is worse than no number. The grams stand alone (they scale
USDA's values); the macro estimate needs every field, and a partial one is discarded whole. A response with no candidates (a
safety block, for example) is a provider failure, not "no food", so it returns `503` and
refunds the quota. The prompt also tells the model to ignore instructions inside the image;
that is a mitigation, not a guarantee, and the worst a hostile image can do here is change
which food name is searched.

Two models are configured. A `429`, `5xx` or timeout from the primary is retried once on the
fallback, which has its own quota; other errors are not retried. Each attempt has a 12-second
timeout, so a hanging model costs at most that before the fallback starts. Model ids are pinned
in settings, and `GEMINI_MODEL` can be changed in Vercel to swap the primary without a code
change.

Latency is variable on the free tier. On 2026-09-21 `gemini-3.5-flash-lite` answered in under
2 seconds and later hung past 45 seconds, while `gemini-3.1-flash-lite` returned a `503` ("high
demand") once and then answered in about 2.5 seconds. The fallback exists for this; it is worth
watching which model actually serves requests.

### Vision provider

Vision label scores are probabilities in [0, 1] and are thresholded at 0.70. Web-entity scores
are unbounded relevance values that routinely exceed 1.0; they are thresholded at 0.60 on the
raw value and clamped to 1.0 before being reported as a confidence. It needs a billing
account, so it is optional and off by default.

## Nutrition lookup

Each food name is searched in USDA FoodData Central and the best result is returned, per 100g,
then scaled to the model's estimated portion. USDA is a grounding step, not a requirement: see
the fallback below and [ADR-0010](adr/0010-usda-as-a-local-reference.md).

- **Credential** in an `X-Api-Key` header, never the URL. Only status codes are logged, never
  exception text (an httpx error carries the URL), and the `httpx` logger is raised to WARNING
  at startup.
- **No `dataType` filter.** With any filter containing `Survey (FNDDS)`, USDA answered `400` to
  about half of requests, at random (measured 2026-09-21, 45 of 45 succeeded without one).
  Data types are selected in code instead: FNDDS, Foundation and SR Legacy are used; Branded is
  not, because its names are brand text and its values are label claims.
- **One search, widened once.** 25 results are requested; if none qualifies, 50. A response can
  be several hundred KB, so the wider page is used only when needed.
- **Retry.** A transient `400` or `5xx`, a timeout or a non-JSON body is retried once per page
  size. `401`, `403` and `429` are not retried.
- **No match and failure are different.** USDA answering with nothing usable returns `None`
  (`404`, "log manually"); USDA being unreachable raises, and the endpoint answers `503` and
  refunds the quota.
- **Energy is matched by unit.** Foundation and SR Legacy list Energy in both kJ and kcal, in
  either order; taking the wrong one reports about four times the calories.
- **Fallback.** Lookups run concurrently, each limited to 10 seconds including retries. If USDA
  errors, times out or has no match and the model gave a complete estimate with a portion, the
  model's estimate is returned with `source: ai_estimate` and low confidence. Without an
  estimate, an error is a `503` and a real no-match a `404`, both refunding the quota.
- **Ranking.** USDA's first hit is often poor, so results without macro data are dropped and
  more than half of the query's words must match. Among those it prefers more matching words, a
  description that starts with a query word, fewer qualifiers, "raw", the better data type, then
  the shorter description. No match is preferred to a wrong one: "avocado toast" returns nothing
  rather than "Avocado dressing".

## Configuration and mock mode

| Setting | Purpose |
|---|---|
| `FOOD_RECOGNITION_PROVIDER` | `gemini` (default) or `vision`. Anything else fails at startup |
| `GEMINI_API_KEY` | Enables the Gemini provider |
| `GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL` | Pinned model ids: `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` |
| `GOOGLE_VISION_API_KEY` | Enables the Vision provider |
| `USDA_API_KEY` | Enables nutrition lookup |

Without its key a provider runs in **mock mode** and returns fixed sample data (always
"pizza"), as does the nutrition service.

- Locally and in tests, mock mode is expected and useful.
- On a Vercel deployment the endpoint refuses instead, with a `503` and a message pointing to
  manual entry, because fabricated nutrition presented as an analysis of the user's photo is
  worse than no analysis.

## Failure behaviour

| Condition | Response | Quota | User sees |
|---|---|---|---|
| Not a valid image, or unsupported format | 400 | Not spent | The reason, with what to upload instead |
| HEIC photo | 400 (client blocks it first) | Not spent | How to get a JPEG on iPhone and on a Mac |
| Larger than 10MB | 413 (client resizes first; Vercel itself rejects over about 4.5MB) | Not spent | A size message |
| Connection dropped during upload | none (no response) | Not spent | "Couldn't reach the server" |
| Daily limit reached | 429 | n/a | Limit reached, log manually |
| Provider unavailable, rate limited, blocked or returning malformed output | 503 | Refunded | Try again, or log manually |
| No food recognised | 404 | Refunded | Try a clearer photo, or log manually |
| USDA has no match or fails, and the model gave an estimate | 200 | Spent | The estimate, marked as an AI estimate |
| Food found but no nutrition match, no estimate | 404 | Refunded | Log manually |
| Nutrition service unavailable or erroring, no estimate | 503 | Refunded | Try again, or log manually |
| No provider configured on a deployment | 503 | Not spent | Log manually |

## Limits

- **Portions are the model's estimate.** They come from the photo alone and are unmeasured.
  Published work finds portion size the largest source of error and reports systematic
  underestimation of large portions by ungrounded models; see
  [ADR-0010](adr/0010-usda-as-a-local-reference.md). The review screen states the basis of the
  numbers and lets the user edit every value. The portion itself becomes editable in
  [M0.3c](ROADMAP.md#m03c-portion-editing-and-device-check).
- **Accuracy is unmeasured.** The Gemini provider was smoke-tested on one clear photo (a pizza,
  identified at 0.99) and one blank image (an empty list). Mixed plates and unusual foods have
  not been measured; that is the job of the evaluation harness in Phase 1.
- **Matching is a heuristic and is unmeasured.** Live spot checks on 2026-09-21: banana, apple,
  cheeseburger, fried rice and scrambled eggs found sensible entries; `chicken breast` returns
  the *raw* entry (106 kcal per 100g) because "raw" is preferred, which understates a cooked
  portion; an unmapped `pizza` returns "Pizza rolls" (the mapping table covers it); `spaghetti
  bolognese` and `avocado toast` return nothing. Measuring and improving this is what the
  evaluation harness is for.
- **Free-tier limits.** The Gemini free tier allows 15 requests a minute and 500 a day per
  model, as observed on 2026-09-21. Beyond that it answers `429` and stops; it never bills
  because no billing account is linked to the project. Google may use free-tier content to
  improve its products, which the capture screen states.
- **HEIC is not supported.** macOS Photos exports it and Pillow cannot decode it without an
  extra native library. iOS Safari normally converts to JPEG before upload, but this has not
  been confirmed on a device.
- **Vision has not been run against the live API.** It needs a billing account, which conflicts
  with [ADR-0003](adr/0003-hard-capped-providers-only.md). Its label filter and mapping were
  written from expected output and would need adjusting against real output.
- **Request size.** Vercel rejects a request body over about 4.5MB at its edge with
  `FUNCTION_PAYLOAD_TOO_LARGE`, before the API runs; a 3MB unauthenticated upload reached the
  API and a 5MB one did not (checked 2026-09-21). A phone photo can exceed that, and Safari
  then reports a bare "Load failed". The client therefore shrinks the photo before upload
  (`gymbro-web/src/lib/image.ts`, capped at 4MB). Where the browser cannot decode a file it
  sends a small original as it is and refuses one over the cap. The server's own 10MB limit
  is unchanged and still guards direct callers.

## Next

[M0.3c](ROADMAP.md#m03c-portion-editing-and-device-check) makes the portion editable in the
review screen and covers checking HEIC and camera capture on a real iPhone.
[M1.0](ROADMAP.md#m10-usda-reference-dataset) then replaces the live USDA call with a local copy
of the data ([ADR-0010](adr/0010-usda-as-a-local-reference.md)).

## Testing

- Gemini parsing against responses **recorded from the live API** (`tests/fixtures/gemini/`),
  plus synthetic cases for blocked, malformed and hostile output; the request shape; model
  fallback for `429`, `5xx` and network errors; no fallback for client errors; failing closed
  when both models fail
- Portion and estimate parsing: a complete estimate, partial and implausible ones, grams kept
  when the macros are dropped
- The endpoint's grounding logic: USDA scaled to the portion, per 100g without one, fallback to
  the estimate on error, no match and timeout, no fallback without a portion, and mixed results
  across several foods
- USDA lookup against a search response **recorded from the live API**
  (`tests/fixtures/usda/`): header credential, no `dataType` filter, retry and widening, no
  retry for `401`/`403`/`429`, no-match versus failure, kJ-versus-kcal extraction, result
  ranking, and that no log line or error contains the key or URL
- Vision parsing, filtering, thresholds, clamping, deduplication and error handling against a
  mocked `images:annotate` endpoint
- Provider selection by configuration, and an unknown provider failing at startup
- Credential handling, for both providers: the key is asserted to appear in neither the request
  URL nor the raised exception
- The endpoint end to end with services replaced, including every failure row above
- Mock-mode refusal on a deployment, and that it spends no quota
- Frontend: capture validation (type, HEIC, size, quota display), the data-use notice, the
  review form, in-browser resizing (dimensions, no upscaling, EXIF orientation, quality
  fallback, decode failure) and the upload's error messages
