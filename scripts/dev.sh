#!/usr/bin/env bash
# Sobe o Hub para desenvolvimento. Linux/macOS e WSL.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"
exec "$PY" -m lia_agenthub "$@"
