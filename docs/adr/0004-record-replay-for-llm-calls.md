# ADR-0004: Record and replay LLM calls for tests and evaluation

- **Status**: Accepted
- **Date**: 2026-09-20

## Context

Under [ADR-0003](0003-hard-capped-providers-only.md) the project cannot spend on model calls,
and free tiers have low, sometimes unpublished, limits. An evaluation suite that calls live
models on every CI run would exhaust them, would be non-deterministic, and would make a green
build depend on a third party's availability.

## Decision

Every model call, for generation and for embeddings, goes through one client interface with
three modes:

- **replay** (the default in tests and CI): responses come from committed recordings; a
  missing recording fails the test with instructions
- **record**: an explicit, deliberate mode that calls the real provider and writes recordings
- **passthrough**: live calls for local development

A recording is keyed by a hash of the provider, model, parameters and complete input.

Recordings are made with **the model the application ships with**, and every metric is
reported with the model that produced it. Local open models are used for the judge and for
development, not to generate the outputs being scored.

## Consequences

- CI makes no network calls, spends nothing, and is deterministic.
- A recorded evaluation measures the recorded outputs. Changing a prompt or retrieval logic
  changes the key, so CI fails until it is re-recorded locally. That is deliberate, and it
  means the CI gate guards the pipeline around the model, not the model's live behaviour.
  The documentation says so.
- Recordings can go stale as providers change models. Re-recording is a reviewed change, and
  baselines only move with a written justification.
- Recordings are committed, so their size and any personal data they contain must be
  controlled.

## Alternatives considered

- **Live calls in CI.** Rejected: cost, flakiness and rate limits.
- **Hand-written mocks.** Rejected for evaluation: they test the mock, not model behaviour.
  They remain appropriate for unit tests of plumbing.
- **Generating with a local model and shipping a hosted one.** Rejected: the scores would
  describe a system that is not the one deployed.
