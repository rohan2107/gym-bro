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
    [ -n "${pid:-}" ] || continue
    # Kill the children first: start-frontend.sh execs npm, which spawns vite as
    # a separate process that would otherwise survive and hold port 5173.
    pkill -TERM -P "$pid" 2>/dev/null || true
    kill -TERM "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

# Prefixes are applied with process substitution rather than a pipe: in
# `cmd | sed &`, $! is the PID of sed, so cleanup would kill the prefixer and
# leave uvicorn and vite running.
"$REPO_ROOT/scripts/start-backend.sh" "$API_HOST" "$PORT" \
  > >(sed 's/^/[api] /') 2>&1 &
pids+=($!)

"$REPO_ROOT/scripts/start-frontend.sh" \
  > >(sed 's/^/[web] /') 2>&1 &
pids+=($!)

printf '\nBackend: http://%s:%s  (docs at /docs)\nFrontend: http://localhost:5173\n\n' "$API_HOST" "$PORT"

wait
