#!/bin/sh
# ui-crawl-dag.sh — canned skillflow DAG that crawls a running app with ui-crawl.
#
# One node today (`ui-crawl`), so MCP harnesses reach the crawler through
# skillflow's `run`/`status` tools instead of one long blocking call: start
# the run, poll `skillflow status`, read `findings.json` when it lands.
# Sibling checkouts are argv (explicit scope), never probed.
#
# Usage:
#   scripts/ui-crawl-dag.sh --base-url http://localhost:3000 --routes /,/health
#   SKILLFLOW=/tmp/sfvenv/bin/skillflow scripts/ui-crawl-dag.sh --no-run
set -eu

BASE_URL="http://localhost:3000"
ROUTES="/"
OUT="./ui-crawl-out"
DB="./ui-crawl.skillflow.db"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UI_CRAWL="$ROOT/../ui-crawl"
RUN=1
FRESH=1
SKILLFLOW="${SKILLFLOW:-skillflow}"

usage() {
  cat <<USAGE
usage: ui-crawl-dag.sh [--base-url URL] [--routes R1,R2] [--out DIR]
       [--db FILE] [--ui-crawl-dir DIR] [--keep] [--no-run] [--help]
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --base-url) BASE_URL="${2:?--base-url needs a value}"; shift 2 ;;
    --routes) ROUTES="${2:?--routes needs a value}"; shift 2 ;;
    --out) OUT="${2:?--out needs a value}"; shift 2 ;;
    --db) DB="${2:?--db needs a value}"; shift 2 ;;
    --ui-crawl-dir) UI_CRAWL="${2:?--ui-crawl-dir needs a value}"; shift 2 ;;
    --keep) FRESH=0; shift ;;
    --no-run) RUN=0; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "error: unknown flag $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [ ! -d "$UI_CRAWL" ]; then
  echo "error: not a directory: $UI_CRAWL" >&2
  exit 1
fi
if [ ! -f "$UI_CRAWL/package.json" ]; then
  echo "error: missing ui-crawl checkout: $UI_CRAWL/package.json" >&2
  exit 1
fi

if [ "$FRESH" -eq 1 ]; then
  rm -f "$DB"
fi

CRAWL_CMD="npm run crawl --prefix \"$UI_CRAWL\" -- --base-url \"$BASE_URL\" --routes \"$ROUTES\" --out \"$OUT\""

"$SKILLFLOW" --db "$DB" init
"$SKILLFLOW" --db "$DB" add-node ui-crawl --cmd "$CRAWL_CMD"

if [ "$RUN" -eq 1 ]; then
  "$SKILLFLOW" --db "$DB" run
else
  "$SKILLFLOW" --db "$DB" show
fi
