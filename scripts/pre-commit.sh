#!/usr/bin/env bash
# Pre-commit validation - run before committing to catch CI failures early.
set -uo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

printf '\n\033[1;36m🔍 Pre-Commit Validation\033[0m\n'

PYTHON="$(resolve_python)" || exit 1
failures=()

step "1️⃣  Backend linting (ruff)..."
if (cd "$API_DIR" && "$PYTHON" -m ruff check app/ tests/); then
  ok "Backend linting passed"
else
  hint "Run ./scripts/lint-check.sh --fix to auto-fix"
  failures+=("Backend linting")
fi

step "2️⃣  Backend tests with coverage (target: 80%)..."
if (cd "$API_DIR" && JWT_SECRET_KEY=test-secret-key "$PYTHON" -m pytest -q --tb=short \
      --cov=app --cov-report=term-missing:skip-covered --cov-fail-under=80); then
  ok "Backend tests passed"
else
  failures+=("Backend tests")
fi

if require_node; then
  step "3️⃣  Frontend linting (ESLint)..."
  if (cd "$WEB_DIR" && npm run lint --silent); then
    ok "Frontend linting passed"
  else
    failures+=("Frontend linting")
  fi

  step "4️⃣  Frontend type checking..."
  if (cd "$WEB_DIR" && npm run type-check --silent); then
    ok "Frontend type checking passed"
  else
    failures+=("Frontend type checking")
  fi

  step "5️⃣  Frontend tests with coverage..."
  if (cd "$WEB_DIR" && npm test -- --run --coverage); then
    ok "Frontend tests passed"
  else
    failures+=("Frontend tests")
  fi
else
  failures+=("Frontend checks (npm missing)")
fi

printf '\n\033[1;36m%s\033[0m\n' "=================================================="
if [ "${#failures[@]}" -eq 0 ]; then
  printf '\033[0;32m✅ All checks passed! Safe to commit.\033[0m\n'
  exit 0
fi

printf '\033[0;31m❌ Pre-commit validation FAILED:\033[0m\n'
for failure in "${failures[@]}"; do
  fail_msg "$failure"
done
printf '\n\033[1;33mFix these issues before committing.\033[0m\n'
exit 1
