#!/usr/bin/env bash
# The five panel skills think in-session; the DAG enforces their phase boundaries.
set -euo pipefail
PANEL_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$PANEL_DIR/checkpoints.py" "$@"
