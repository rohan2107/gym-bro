# ADR-0008: Embedding model

- **Status**: Proposed
- **Date**: 2026-09-20

## Context

Retrieval requires embedding the corpus once and embedding every query at request time.
Vercel functions cannot run a local model such as one served by Ollama, so query-time
embedding in production needs a hosted API. Vectors from different models are not comparable,
so using a local model for development and a hosted one in production would silently break
retrieval and invalidate the evaluation.

## Decision (proposed)

Use **one hosted embedding model** for corpus indexing, query time, development and
evaluation. It must satisfy [ADR-0003](0003-hard-capped-providers-only.md), so it comes from a
free tier that stops at its limit. Candidates are the Gemini embedding models and the
embedding models on Cloudflare Workers AI; their limits are to be confirmed before choosing.

Record the model identifier and vector dimension in configuration, and assert the dimension in
a test.

## Consequences

- Changing the embedding model means re-embedding the corpus, a new migration if the dimension
  changes, and a new evaluation baseline.
- Embedding calls go through the record/replay layer
  ([ADR-0004](0004-record-replay-for-llm-calls.md)), so CI needs no network.
- A free-tier rate limit constrains ingestion throughput; ingestion must batch and back off.

## Alternatives considered

- **A local model everywhere.** Rejected: it cannot run on Vercel.
- **Local for development, hosted for production.** Rejected: the vector spaces differ.
- **Storing only precomputed query vectors.** Rejected: real queries are unbounded.
