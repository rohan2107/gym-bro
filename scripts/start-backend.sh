#!/usr/bin/env bash
# Start the FastAPI backend with reload.
#
# Usage: ./scripts/start-backend.sh [host] [port]
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

API_HOST="${1:-127.0.0.1}"
PORT="${2:-8000}"

if [ ! -x "$API_DIR/.venv/bin/python" ]; then
  echo "No venv at gymbro-api/.venv. Create it with:" >&2
  echo "  cd gymbro-api && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

cd "$API_DIR"
exec .venv/bin/python -m uvicorn app.main:app --reload --host "$API_HOST" --port "$PORT"
