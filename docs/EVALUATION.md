# Evaluation design

**Status**: design for [Phase 1](ROADMAP.md#phase-1-retrieval-and-evaluation); nothing here is
implemented yet.

This document specifies how LLM-backed features are measured. It is written before the
implementation so the harness shapes the features rather than being fitted to them afterwards.

## What is evaluated

| Target | Question it answers | Phase |
|---|---|---|
| Retrieval | Did the right passages come back, and in what rank? | 1 |
| Generation | Is the answer correct, and is every claim supported by the retrieved context? | 1 |
| Citations | Does each cited passage actually support the claim it is attached to? | 1 |
| Tool trajectories | Did the agent call the right tools, with the right arguments, in a sensible order? | 3 |
| Food recognition | Which foods and portions did the model identify, against known meals? | 0 (optional) |

## The failure worth designing against

**The right answer for the wrong reason.** An assistant states a correct figure while having
retrieved an irrelevant passage, citing one that does not support the claim, or answering from
its own memory while implying the corpus supports it. Answer-accuracy scoring passes all of
these. Groundedness scoring does not. A suite that measures only final-answer correctness will
report a healthy number for a system that is not grounded.

This is the same shape of failure as any headline metric that hides a spurious dependency, and
the harness is built to expose it: the golden set includes cases constructed to trigger it, and
the report shows accuracy-only scoring and groundedness scoring side by side.

## Golden set

A hand-authored set of 50–100 items for v1. Each item:

| Field | Purpose |
|---|---|
| `id` | Stable identifier |
| `question` | The user's question |
| `reference_answer` | The correct answer, with numeric tolerance where relevant |
| `gold_chunks` | The passages that support the answer (source, section) |
| `category` | Lookup, multi-passage, numeric, unanswerable, planted |
| `split` | `dev` or `test` |
| `notes` | Authoring rationale, including why a planted case is planted |

**Unanswerable questions** are included on purpose: the correct behaviour is to say the corpus
does not cover it, and the metric rewards that.

### Leakage-aware splits

Items are grouped by source document and section before splitting, so questions derived from
the same passage never straddle `dev` and `test`. Otherwise tuning on `dev` would leak into the
number reported on `test`. The `test` split is used for reporting only and is not consulted
while tuning.

## Metrics

**Retrieval**

| Metric | Meaning |
|---|---|
| recall@k | Fraction of gold chunks present in the top k |
| MRR | Mean reciprocal rank of the first gold chunk |
| Context precision | Fraction of retrieved chunks that are relevant |

**Generation**

| Metric | Meaning |
|---|---|
| Answer correctness | The answer agrees with the reference (exact or tolerance match for numbers, judged otherwise) |
| Groundedness (faithfulness) | Every claim in the answer is supported by the retrieved context |
| Citation accuracy | Each cited chunk supports the claim it is attached to |
| Abstention | Unanswerable questions are declined rather than answered |

Every reported figure carries the **model identifier, embedding model, date, sample size and
commit** that produced it.

## Planted right-answer-wrong-reason cases

Constructed cases where a correct final answer is reachable without proper grounding:

1. **Wrong citation**: the answer is right, but the cited chunk is unrelated
2. **Parametric answer**: the corpus contains no support, the model answers from memory, and
   the answer happens to be right
3. **Distractor**: a near-duplicate passage states the same figure in a different context, and
   the wrong one is retrieved

The demonstration is a 2×2 table for these cases: accuracy-only scoring against groundedness
scoring, showing the former passing what the latter fails. It is reproducible from a single
command.

## Judge validation

Groundedness and correctness are judged by a model, so the judge is evaluated too
([ADR-0009](adr/0009-judge-model-and-validation.md)):

- A subset of judged items is hand-labelled
- Report percent agreement, Cohen's kappa with a bootstrap interval, and a confusion matrix
- Report the sample size and say plainly that kappa on a small sample is imprecise
- Include a failure analysis: what kinds of items the judge gets wrong

## Record and replay

All model calls, including embeddings and the judge, go through the client described in
[ADR-0004](adr/0004-record-replay-for-llm-calls.md).

- **Key**: hash of provider, model, parameters and complete input
- **Storage**: committed under the test tree; size is monitored
- **Modes**: replay in CI, record on request, passthrough in development
- **Re-recording** is a reviewed change with a stated reason

What this guards: a change to retrieval, chunking, prompt construction, scoring or parsing
changes the inputs, misses the recording, and fails CI until re-recorded. What it does not
guard: the live model's behaviour drifting. That is checked by the scheduled evaluation
([M4.3](ROADMAP.md#phase-4-hardening)).

## Baselines and the CI gate

- A committed baseline file holds the expected value of each tracked metric per model
- CI fails when a metric falls below `baseline − tolerance`, with the tolerance stated per
  metric and justified by the metric's observed variance
- Raising a baseline is welcome. **Lowering** one requires an explanation in the pull request.

## Retrieval ablation

A deliberately small comparison of chunk size, hybrid BM25 + vector retrieval, and reranking,
using the same golden set. Results are reported as measured, including where a change made no
difference. The purpose is to show which choices matter, not to search exhaustively.

## Trajectory evaluation (Phase 3)

For the agent, the unit under test is the sequence of tool calls:

- **Expected trajectory**: tools, arguments and order for each case, with allowed alternatives
- **Forbidden calls**: calls that must never happen, such as a write without confirmation
- **Scoring**: exact and partial credit; argument checking is strict on identifiers and
  tolerant on free text
- **Mutation cases**: replayed calls must not double-apply, which exercises idempotency keys

## Food recognition (optional, Phase 0)

If provider choice for [M0.3a](ROADMAP.md#m03a-food-recognition-providers) is to be evidence
rather than preference, a small set of 20–30 meals photographed by the author gives item
precision and recall and a calorie error against known portions. Photographs must be the
author's own, to avoid redistribution problems.

## Reporting and reproducibility

- Tables in the README are generated by a script, never typed
- A run records the commit, the model identifiers and the date
- One command regenerates the full report from recordings with no network access

## Limitations to state up front

- The golden set is small and hand-written; results carry that uncertainty
- Recorded evaluation measures recorded outputs, not the live model
- A local judge is weaker than a frontier model; the validation report quantifies how much
- The corpus is narrow by design, so results do not generalise beyond it
