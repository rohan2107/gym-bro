# ADR-0006: Streaming responses on Vercel

- **Status**: Proposed
- **Date**: 2026-09-20

## Context

LLM responses take seconds, and streaming is the expected experience. An earlier assumption,
recorded in these docs, was that the app is "Mangum-wrapped" and that a Lambda-style adapter
would buffer responses. That was wrong: `api/handler.py` exposes the ASGI app directly, `mangum`
is never imported, and the deployment shows Fluid Compute enabled. Whether streaming works
through this runtime is therefore **unknown**, not ruled out.

## Decision (proposed)

Decide by experiment, not by assumption. Deploy a minimal server-sent-events endpoint to a
preview deployment and observe whether chunks arrive incrementally, and what duration limit
applies on the free plan.

- If it streams: stream, and record the limits.
- If it does not: ship non-streaming responses and record that as the decision. This is
  acceptable at zero spend.
- Moving the API to a long-running host is a last resort, because it adds infrastructure and
  possibly cost.

## Consequences

- The decision is deferred to [Phase 2](../ROADMAP.md#phase-2-resilience) and does not block
  Phase 1, whose retrieval endpoint is not streamed.
- The experiment is small and its result is cheap to record.

## Alternatives considered

- **Assume it cannot stream and skip the experiment.** Rejected: the assumption was built on a
  mistaken premise.
- **Move off Vercel now.** Rejected as premature.
