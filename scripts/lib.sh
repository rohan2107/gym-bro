#!/usr/bin/env bash
# Shared helpers for the shell scripts in this directory.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$REPO_ROOT/gymbro-api"
WEB_DIR="$REPO_ROOT/gymbro-web"

# The backend needs Python 3.11+; macOS ships 3.9 as `python3`.
resolve_python() {
  if [ -x "$API_DIR/.venv/bin/python" ]; then
    echo "$API_DIR/.venv/bin/python"
    return
  fi
  for candidate in python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1; then
      echo "$candidate"
      return
    fi
  done
  echo "No Python 3.11+ interpreter found. Create the venv first:" >&2
  echo "  cd gymbro-api && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  return 1
}

require_node() {
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm not found. Install Node 20+ (brew install node)." >&2
    return 1
  fi
}

step() { printf '\n\033[1;33m%s\033[0m\n' "$*"; }
ok() { printf '\033[0;32m  ✅ %s\033[0m\n' "$*"; }
fail_msg() { printf '\033[0;31m  ❌ %s\033[0m\n' "$*"; }
hint() { printf '\033[0;90m  💡 %s\033[0m\n' "$*"; }
