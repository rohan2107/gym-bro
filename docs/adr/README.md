# Architecture Decision Records

Each file records one decision: the context that forced it, what was decided, and what that
costs. They are short on purpose and are not edited after acceptance except to change their
status. To reverse a decision, write a new ADR that supersedes the old one.

## Statuses

- **Proposed**: under consideration; the decision is not yet made or awaits an experiment
- **Accepted**: decided and in force
- **Superseded**: replaced by a later ADR, which is named in the status line

## Index

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-alembic-owns-the-schema.md) | Alembic owns the database schema | Accepted |
| [0002](0002-vision-rest-api-with-header-credentials.md) | Call Vision over REST with a header credential | Accepted |
| [0003](0003-hard-capped-providers-only.md) | Use only providers that stop at their limit | Accepted |
| [0004](0004-record-replay-for-llm-calls.md) | Record and replay LLM calls for tests and evaluation | Accepted |
| [0005](0005-food-recognition-providers.md) | Food recognition behind a provider interface | Accepted |
| [0006](0006-streaming-on-vercel.md) | Streaming responses on Vercel | Proposed |
| [0007](0007-knowledge-corpus.md) | Knowledge corpus selection | Proposed |
| [0008](0008-embedding-model.md) | Embedding model | Proposed |
| [0009](0009-judge-model-and-validation.md) | Evaluation judge model and its validation | Proposed |
| [0010](0010-usda-as-a-local-reference.md) | USDA FoodData Central as a local reference dataset, not a live dependency | Proposed |

## Writing a new ADR

Copy [0000-template.md](0000-template.md), take the next number, and add a row to the index.
Write one when a choice is hard to reverse, when a reasonable engineer would have chosen
differently, or when the reasoning would otherwise be lost. Do not write one for routine
implementation detail.
