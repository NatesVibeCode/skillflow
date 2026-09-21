#!/usr/bin/env bash
# 02-parallel: independent branches run together with --jobs.
set -euo pipefail
DB="$(mktemp -t parallel-XXXXXX.db)"
trap 'rm -f "$DB"' EXIT
export SKILLFLOW_DB="$DB"

skillflow init >/dev/null
skillflow add-node lint --cmd "sleep 1; echo lint-ok"
skillflow add-node test --cmd "sleep 1; echo test-ok"
skillflow add-node ship --cmd "echo shipped"
skillflow add-edge lint ship
skillflow add-edge test ship
echo "--- plan ---"
skillflow run --dry-run
echo "--- run (jobs=2) ---"
skillflow run --jobs 2 >/dev/null
skillflow status
