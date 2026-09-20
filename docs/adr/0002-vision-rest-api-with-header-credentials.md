# ADR-0002: Call Google Cloud Vision over REST with a header credential

- **Status**: Accepted
- **Date**: 2026-09-16

## Context

The photo pipeline needed Google Cloud Vision. The `google-cloud-vision` client library
authenticates with service-account credentials, but the app is deployed with an API key. The
library also pulls gRPC and protobuf into a serverless function for what is one HTTP POST. A
first implementation that passed the key as a `?key=` query parameter leaked it: `httpx`
includes the full URL in `HTTPStatusError`, and the endpoint logs that exception.

## Decision

Call `images:annotate` directly with `httpx`, authenticating with an `X-Goog-Api-Key` header.
Google documents the header as the recommended form and warns that the query parameter exposes
the key in URLs.

## Consequences

- No client-library dependency; the code is a small, fully testable HTTP call.
- The key never appears in a URL, so it cannot reach logs through exception messages.
- Request and response handling is ours to maintain, including the fact that Vision reports
  per-image errors inside a `200` response.
- Vision requires a billing account, which conflicts with
  [ADR-0003](0003-hard-capped-providers-only.md). It therefore becomes an optional provider
  under [ADR-0005](0005-food-recognition-providers.md) rather than the primary one.

## Alternatives considered

- **The client library.** Rejected for the reasons above.
- **The `?key=` query parameter.** Rejected: it leaked the credential into logs.
