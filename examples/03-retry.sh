#!/usr/bin/env bash
# 03-retry: a failing run, a fix, then --retry resumes from the failure.
set -euo pipefail
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export SKILLFLOW_DB="$WORK/retry.db"

skillflow init >/dev/null
skillflow add-node build --cmd "echo built"
skillflow add-node deploy --cmd "test -f $WORK/approved"
skillflow add-edge build deploy
if skillflow run >/dev/null 2>&1; then
  echo "expected the first run to fail" >&2
  exit 1
fi
echo "--- first run failed as expected; approving ---"
touch "$WORK/approved"
skillflow run --retry >/dev/null
skillflow status
