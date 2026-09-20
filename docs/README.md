# Documentation

## Start here

- [Architecture](ARCHITECTURE.md): how the system is built today
- [Roadmap](ROADMAP.md): what is planned, in what order, and how each step is judged done

## Design and decisions

- [Architecture decision records](adr/README.md): what was decided, why, and what it costs
- [Evaluation design](EVALUATION.md): how LLM-backed features are measured
- [Photo analysis](PHOTO_ANALYSIS.md): the meal-photo pipeline, failure behaviour and limits
- [Authentication](AUTHENTICATION.md): Google OAuth setup, the session model and known gaps
- [Energy balance](ENERGY_BALANCE.md): design of the planned analytics endpoints

## Operations

- [Deployment and operations](DEPLOYMENT.md): configuration, CI/CD, releasing, rollback, cost
  controls and secrets

## History

- [September 2026 audit](AUDIT_2026-09.md): what was found when development resumed, and how
  each finding was resolved
- [Changelog](../CHANGELOG.md)

## Conventions

Contribution conventions and the quality gates are in [AGENTS.md](../AGENTS.md).
Documents are kept short and single-purpose; where two would overlap, one links to the other
rather than repeating it.
