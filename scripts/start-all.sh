#!/usr/bin/env bash
# Start backend and frontend together, streaming both logs into this terminal.
# Ctrl-C stops both.
set -uo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

API_HOST="${1:-127.0.0.1}"
PORT="${2:-8000}"

pids=()
cleanup() {
  trap - INT TERM EXIT
  for pid in "${pids[@]:-}"; do
    [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

"$REPO_ROOT/scripts/start-backend.sh" "$API_HOST" "$PORT" 2>&1 | sed 's/^/[api] /' &
pids+=($!)

"$REPO_ROOT/scripts/start-frontend.sh" 2>&1 | sed 's/^/[web] /' &
pids+=($!)

printf '\nBackend: http://%s:%s  (docs at /docs)\nFrontend: http://localhost:5173\n\n' "$API_HOST" "$PORT"

wait
