#!/usr/bin/env bash
# Roda a suíte inteira. Falha se algum teste falhar.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m pytest "$@"
