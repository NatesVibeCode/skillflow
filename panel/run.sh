#!/usr/bin/env bash
# The four panel skills think in-session; the DAG enforces their phase boundaries.
set -euo pipefail
PANEL_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "${1:-}" = add-skill ]; then
  exec bash "$PANEL_DIR/legacy-run.sh" "$@"
fi
exec python3 "$PANEL_DIR/checkpoints.py" "$@"
