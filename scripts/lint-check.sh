#!/usr/bin/env bash
# Quick lint check - linting only, faster than the full pre-commit run.
#
# Usage:
#   ./scripts/lint-check.sh          # check only (exit 1 on errors)
#   ./scripts/lint-check.sh --fix    # auto-fix where possible
set -uo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

FIX=0
for arg in "$@"; do
  case "$arg" in
    --fix) FIX=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

printf '\n\033[1;36m🔍 Quick Lint Check\033[0m\n'

PYTHON="$(resolve_python)" || exit 1
failures=()

step "Backend (ruff)..."
if [ "$FIX" -eq 1 ]; then
  if (cd "$API_DIR" && "$PYTHON" -m ruff check app/ tests/ --fix); then
    ok "Backend lint fixed and passed"
  else
    failures+=("Backend")
  fi
else
  if (cd "$API_DIR" && "$PYTHON" -m ruff check app/ tests/); then
    ok "Backend lint passed"
  else
    hint "Run with --fix to auto-fix"
    failures+=("Backend")
  fi
fi

step "Frontend (ESLint)..."
if require_node; then
  if (cd "$WEB_DIR" && npm run lint --silent); then
    ok "Frontend lint passed"
  else
    failures+=("Frontend")
  fi
else
  failures+=("Frontend (npm missing)")
fi

if [ "${#failures[@]}" -eq 0 ]; then
  printf '\n\033[0;32m✅ All linting passed!\033[0m\n'
  exit 0
fi

printf '\n\033[0;31m❌ Linting failed in: %s\033[0m\n' "$(IFS=', '; echo "${failures[*]}")"
exit 1
