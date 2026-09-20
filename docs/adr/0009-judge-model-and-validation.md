# ADR-0009: Evaluation judge model and its validation

- **Status**: Proposed
- **Date**: 2026-09-20

## Context

Groundedness and answer correctness are judged by a model, which is itself unevaluated: an
unvalidated judge reintroduces the problem the harness exists to remove. Under
[ADR-0003](0003-hard-capped-providers-only.md), judging cannot rely on a paid API, and running
it on every CI push against a rate-limited free tier is impractical.

## Decision (proposed)

Run the judge as a **local open model**, offline, and cache its verdicts keyed by content hash
([ADR-0004](0004-record-replay-for-llm-calls.md)). Because a small local judge can be weak,
validate it before trusting it:

- hand-label a subset of judged items
- report agreement with the human labels (percent agreement and Cohen's kappa), a confusion
  matrix, and where the judge fails
- report the sample size and the uncertainty of the estimate; kappa on a small sample has a
  wide interval, and the report says so

Scores from the judge are published together with that agreement figure.

## Consequences

- The evaluation states its own limits, which makes its claims checkable.
- Hand-labelling is real work and is budgeted in
  [M1.5](../ROADMAP.md#m15-planted-cases-judge-validation-ablation).
- CI replays cached verdicts and never runs the judge. Re-judging happens locally and on the
  scheduled evaluation ([M4.3](../ROADMAP.md#phase-4-hardening)).

## Alternatives considered

- **A hosted judge on a free tier.** Rejected as the default: rate limits, and outputs that
  can change silently when the provider updates a model.
- **No judge, using string and embedding similarity.** Rejected: it cannot assess whether an
  answer is supported by its cited context.
