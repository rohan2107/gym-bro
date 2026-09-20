# ADR-0007: Knowledge corpus selection

- **Status**: Proposed
- **Date**: 2026-09-20

## Context

Retrieval quality can only be measured if the corpus has stable, citable documents and a
licence that permits redistribution in a public repository. Evaluation also needs the ground
truth to be checkable against a named source, so scraped text of unclear origin is unsuitable.

## Decision (proposed)

Select the corpus against these criteria:

1. **Licence**: redistributable in a public repository, verified per source, not assumed
2. **Provenance**: every chunk carries source, section, URL, retrieval date and licence
3. **Stability**: documents that change rarely, or are pinned by version or date
4. **Size**: small enough for the database's free-tier storage (limit to be confirmed) and for
   a hand-authored golden set to cover meaningfully
5. **Fit**: nutrition and training guidance that the app's users would plausibly ask about

Candidates to evaluate first are United States government publications, which are generally
public domain: the Dietary Guidelines for Americans and the NIH Office of Dietary Supplements
fact sheets. Licence terms must be confirmed for each before any text is committed.

## Consequences

- A small, well-provenanced corpus makes the golden set achievable and the evaluation
  meaningful, at the cost of narrower coverage.
- Ingestion stores licence and source with each chunk, so attribution requirements can be met
  and a source can be removed cleanly.

## Alternatives considered

- **Web scraping or general encyclopaedia text.** Rejected as a starting point: unclear
  redistribution terms, and content that changes under the evaluation.
- **Model-generated documents.** Rejected: they have no independent ground truth.
