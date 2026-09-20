#!/usr/bin/env bash
# Start the Vite dev server, or build for production with --build.
set -euo pipefail

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require_node

cd "$WEB_DIR"

if [ ! -d node_modules ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

if [ "${1:-}" = "--build" ]; then
  exec npm run build
fi

exec npm run dev
