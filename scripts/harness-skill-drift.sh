#!/bin/sh
# harness-skill-drift.sh — skillflow DAG for skill drift between harnesses.
#
# Three nodes, one fan-in:
#   handoff-build-check  regenerates nothing; fails if a checked-in skill
#                        tree is stale against skills-src/
#   fleet-self           fleet's own shared-file + route-policy contract
#                        check (CI mode for the fleet checkout)
#   harness-contracts    each of the seven generated handoff contract.json
#                        files validated against the fleet providers'
#                        HarnessSpec + argv builder; runs only when both
#                        preconditions above pass (skillflow skips
#                        downstream nodes after a failure)
#
# Sibling checkouts are argv (explicit scope), never probed.
#
# Usage:
#   scripts/harness-skill-drift.sh
#   SKILLFLOW=/tmp/sfvenv/bin/skillflow scripts/harness-skill-drift.sh --no-run
set -eu

DB="./harness-skill-drift.skillflow.db"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FLEET="$ROOT/../harness-fleet"
HANDOFF="$ROOT/../harness-handoff"
RUN=1
FRESH=1
NOTESTS=0
SKILLFLOW="${SKILLFLOW:-skillflow}"
HARNESSES="antigravity claude codex cursor grok muse opencode"

usage() {
  cat <<USAGE
usage: harness-skill-drift.sh [--db FILE] [--harness-fleet-dir DIR]
       [--harness-handoff-dir DIR] [--no-tests] [--keep] [--no-run] [--help]
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --db) DB="${2:?--db needs a value}"; shift 2 ;;
    --harness-fleet-dir) FLEET="${2:?--harness-fleet-dir needs a value}"; shift 2 ;;
    --harness-handoff-dir) HANDOFF="${2:?--harness-handoff-dir needs a value}"; shift 2 ;;
    --no-tests) NOTESTS=1; shift ;;
    --keep) FRESH=0; shift ;;
    --no-run) RUN=0; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "error: unknown flag $1" >&2; usage >&2; exit 1 ;;
  esac
done

for dir in "$FLEET" "$HANDOFF"; do
  if [ ! -d "$dir" ]; then
    echo "error: not a directory: $dir" >&2
    exit 1
  fi
done
if [ ! -f "$HANDOFF/scripts/build_skills.py" ]; then
  echo "error: missing skill builder: $HANDOFF/scripts/build_skills.py" >&2
  exit 1
fi
if [ ! -f "$FLEET/scripts/check_harness_drift.py" ]; then
  echo "error: missing drift check: $FLEET/scripts/check_harness_drift.py" >&2
  exit 1
fi
for harness in $HARNESSES; do
  if [ ! -f "$HANDOFF/${harness}-harness-handoff/contract.json" ]; then
    echo "error: missing contract: $HANDOFF/${harness}-harness-handoff/contract.json" >&2
    exit 1
  fi
done

if [ "$FRESH" -eq 1 ]; then
  rm -f "$DB"
fi

CHECK_CMD="python3 \"$HANDOFF/scripts/build_skills.py\" --check"

if [ "$NOTESTS" -eq 1 ]; then
  SELF_CMD="python3 \"$FLEET/scripts/check_harness_drift.py\" --self --no-tests"
else
  SELF_CMD="python3 \"$FLEET/scripts/check_harness_drift.py\" --self"
fi

CONTRACTS_CMD="fail=0;"
for harness in $HARNESSES; do
  CONTRACTS_CMD="$CONTRACTS_CMD python3 \"$FLEET/scripts/check_harness_drift.py\" --repo \"$FLEET\" --handoff-contract \"$HANDOFF/${harness}-harness-handoff/contract.json\" --no-tests || fail=1;"
done
CONTRACTS_CMD="$CONTRACTS_CMD exit \$fail"

"$SKILLFLOW" --db "$DB" init
"$SKILLFLOW" --db "$DB" add-node handoff-build-check --cmd "$CHECK_CMD"
"$SKILLFLOW" --db "$DB" add-node fleet-self --cmd "$SELF_CMD"
"$SKILLFLOW" --db "$DB" add-node harness-contracts --cmd "$CONTRACTS_CMD"
"$SKILLFLOW" --db "$DB" add-edge handoff-build-check harness-contracts
"$SKILLFLOW" --db "$DB" add-edge fleet-self harness-contracts

if [ "$RUN" -eq 1 ]; then
  "$SKILLFLOW" --db "$DB" run
else
  "$SKILLFLOW" --db "$DB" show
fi
