# Contributing to Gym Bro

Thanks for your interest in contributing! This document outlines the basics to keep contributions smooth and consistent.

## Workflow
- Create a feature branch from `main`: `feat/<short-topic>` or `fix/<short-topic>`
- Keep PRs small and focused; include a clear description of changes
- Update documentation when relevant (README or API docs)
- Link issues if applicable

## Development
- Backend (API): FastAPI + SQLModel in `gymbro-api/`
- Use a virtual environment: `python -m venv .venv` and `pip install -r requirements.txt`
- Run locally: `uvicorn app.main:app --reload`
- Tests: (to be added) — CI runs lint and tests in GitHub Actions

## Code Style
- Follow `.editorconfig`
- Prefer clear naming; avoid one-letter variables
- Keep changes minimal and focused on the task

## Commit Messages
- Use conventional style where practical:
  - `feat(api): add food log endpoints`
  - `fix(db): correct foreign key reference`
  - `docs(readme): add badges and quickstart`

## Reporting Issues
- Provide steps to reproduce, expected behavior, and environment details
- Include logs or screenshots when helpful
