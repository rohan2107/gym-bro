# Photo analysis

Photograph a meal, get food predictions and macros, review and edit them, then save. This
document describes the pipeline as built, its failure behaviour, its limits, and the planned
change of provider. The original plan this replaces is in the git history.

## User flow

1. On the Meals page the user taps **Log from photo**. On a phone this opens the camera; on a
   desktop it opens the file picker.
2. The client checks the file (image type, not HEIC, at most 10MB) and uploads it.
3. The server returns predictions, each with nutrition per 100g, and the user's remaining
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
  Google Cloud Vision: label + web detection
      generic labels dropped, duplicates merged, top 3 kept          -> 503 on failure, quota refunded
      nothing left                                                   -> 404, quota refunded
  map each label to a USDA query, look up nutrition per item
      nothing found                                                  -> 404, quota refunded
  return predictions, quota state, image info
```

Quota is reserved before the expensive calls and refunded when detection or lookup fails, so a
failed request never costs the user a photo. The limit is 30 per user per day, enforced by
[rate_limiter.py](../gymbro-api/app/services/rate_limiter.py) with `SELECT ... FOR UPDATE`.

### Components

| Component | Responsibility |
|---|---|
| `VisionService` | Calls Vision's `images:annotate` over REST and filters and ranks the result |
| `NutritionService` | USDA FoodData Central lookup, 10s timeout, per-item |
| `food_mapping` | Maps Vision labels to USDA search queries |
| `RateLimiter` | Atomic per-user daily quota |
| `PhotoCapture`, `MealReview` | The capture and review components in the frontend |

All services are injected as dependencies, so tests replace them and no test calls a real
service. See [ADR-0002](adr/0002-vision-rest-api-with-header-credentials.md).

### Scores

Vision label scores are probabilities in [0, 1] and are thresholded at 0.70. Web-entity scores
are unbounded relevance values that routinely exceed 1.0; they are thresholded at 0.60 on the
raw value and clamped to 1.0 before being reported as a confidence.

## Configuration and mock mode

`GOOGLE_VISION_API_KEY` and `USDA_API_KEY` enable the two services. Without a key a service
runs in **mock mode** and returns fixed sample data (always "pizza").

- Locally and in tests, mock mode is expected and useful.
- On a Vercel deployment the endpoint refuses instead, with a `503` and a message pointing to
  manual entry, because fabricated nutrition presented as an analysis of the user's photo is
  worse than no analysis.

## Failure behaviour

| Condition | Response | Quota | User sees |
|---|---|---|---|
| Not a valid image, or unsupported format | 400 | Not spent | The reason, with what to upload instead |
| HEIC photo | 400 (client blocks it first) | Not spent | How to get a JPEG on iPhone and on a Mac |
| Larger than 10MB | 413 (client blocks it first) | Not spent | A size message |
| Daily limit reached | 429 | n/a | Limit reached, log manually |
| Vision unavailable or erroring | 503 | Refunded | Try again, or log manually |
| No food recognised | 404 | Refunded | Try a clearer photo, or log manually |
| Food found but no nutrition match | 404 | Refunded | Log manually |
| No provider configured on a deployment | 503 | Not spent | Log manually |

## Limits

- **Nutrition is per 100g.** Vision returns labels, which carry no portion size, so the review
  screen states the basis and lets the user edit every value.
- **HEIC is not supported.** macOS Photos exports it and Pillow cannot decode it without an
  extra native library. iOS Safari normally converts to JPEG before upload, but this has not
  been confirmed on a device.
- **Vision has not been run against the live API.** It needs a billing account, which conflicts
  with [ADR-0003](adr/0003-hard-capped-providers-only.md). The label filter and mapping were
  written from expected output and will need adjusting against real output.
- **The Vision request body is capped at about 10MB** by Google, and base64 inflates an image by
  roughly a third, so an image between about 7.5MB and 10MB could pass local validation and be
  rejected upstream. Phone photos are normally smaller. This limit is from Google's
  documentation and has not been reproduced.

## Planned: provider interface

[M0.3](ROADMAP.md#m03-food-recognition-providers) replaces label recognition with a provider
interface ([ADR-0005](adr/0005-food-recognition-providers.md)). The target contract:

```
FoodRecognizer.recognize(image) -> [ { name, estimated_grams, confidence } ]
```

Each item is looked up in USDA by name and scaled to the estimated grams, so the review screen
shows macros for the portion rather than for 100g. Providers are chosen by configuration:

- a multimodal model on a free tier that stops at its limit (leading candidate: the Gemini API)
- Google Cloud Vision, kept as an optional provider
- mock, for development and tests

Tests run against recorded provider responses ([ADR-0004](adr/0004-record-replay-for-llm-calls.md)),
and every failure continues to degrade to manual entry.

## Testing

- Vision parsing, filtering, thresholds, clamping, deduplication and error handling against a
  mocked `images:annotate` endpoint
- Credential handling: the key is asserted to appear in neither the request URL nor the raised
  exception
- The endpoint end to end with services replaced, including every failure row above
- Mock-mode refusal on a deployment, and that it spends no quota
- Frontend: capture validation (type, HEIC, size, quota display) and the review form
