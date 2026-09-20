# ADR-0003: Use only providers that stop at their limit

- **Status**: Accepted
- **Date**: 2026-09-20

## Context

The project's constraint is zero spend, and an accidental bill is unacceptable. Google Cloud
budgets, checked against the documentation, only send alerts: *"Setting an alerts-only budget
doesn't automatically cap Google Cloud … usage or spending."* Alerts also lag usage. Cloud
Vision's default quota is 1,800 requests per minute with no documented daily cap, so a leaked key could
in principle accrue thousands of dollars in a day before an alert arrived. Google Cloud does
not accept prepaid cards, and a declined payment suspends every project on the account without
cancelling the debt.

## Decision

Only use external services that **stop serving at their limit** rather than bill:

- free tiers that return an error when exhausted (for example `429`)
- prepaid balances with auto top-up disabled

A service that can bill beyond a limit is not used, unless a mechanism that enforces a hard
stop is in place. Where a billing account is unavoidable, a free-trial account is preferred
because it cannot be charged unless upgraded, and billing is unlinked when not in use.

## Consequences

- Provider choice is constrained to those with enforceable free tiers, which limits model
  quality and imposes rate limits that must be designed around (retries, fallbacks, caching).
- Free tiers can change or vanish. Model identifiers are pinned in configuration and recorded
  with every result, and providers sit behind interfaces so one can be replaced.
- Some free tiers use submitted content to improve their products. That is a privacy cost, and
  it is stated wherever it applies.
- Budgets are still configured, but as tripwires: expected spend is zero, so any spend is a
  signal.

## Alternatives considered

- **A budget alert only.** Rejected: it does not stop spending.
- **A budget-triggered function that unlinks billing.** Not adopted: Google's own guidance says
  it *"doesn't guarantee that you won't spend more than your budget"* because of billing delay.
  It remains the fallback if a billing account is ever required.
- **A low-limit virtual card.** Rejected: prepaid cards are not accepted, and a decline
  suspends the account without removing what is owed.
