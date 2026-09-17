#!/usr/bin/env bash
# run.sh — run a panel skill as a skillflow DAG.
#
# The procedure lives in the graph, not in docs: each skill builds its own
# DAG (seed -> subject -> select -> gate -> round ...) and runs it. Gates
# stop every round until a person has done the work and approved the record.
#
# Usage: panel/run.sh <skill> "<subject>" [rounds] [session-dir]
#   skill    debate | brainstorm | reframe | review | add-skill
#   subject  claim | goal | frame | work-under-review | new skill idea
#   rounds   debate/reframe only (default 3; the rest have fixed shapes)
#
# Requires the `skillflow` CLI on PATH, or set SKILLFLOW_CMD.
set -euo pipefail

SKILL="${1:?usage: run.sh <debate|brainstorm|reframe|review> \"<subject>\" [rounds] [dir]}"
SUBJECT="${2:?usage: run.sh <debate|brainstorm|reframe|review> \"<subject>\" [rounds] [dir]}"
ROUNDS_ARG="${3:-}"
SESSION="${4:-./session-$(date +%Y%m%d-%H%M%S)}"
PANEL_DIR="$(cd "$(dirname "$0")" && pwd)"

case "$SKILL" in
  debate|reframe) ROUNDS="${ROUNDS_ARG:-3}" ;;
  brainstorm|review|add-skill)
    ROUNDS=2
    if [ "$#" -ge 3 ]; then SESSION="$ROUNDS_ARG"; fi ;;
  *) echo "error: unknown skill '$SKILL'" >&2; exit 2 ;;
esac

if [ -n "${SKILLFLOW_CMD:-}" ]; then
  # shellcheck disable=SC2206
  SF=($SKILLFLOW_CMD)
elif command -v skillflow >/dev/null; then
  SF=(skillflow)
else
  # Fall back to the bundled engine: this repo ships both.
  REPO_ROOT="$(cd "$PANEL_DIR/.." && pwd)"
  export PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  SF=(python3 -m skillflow.cli)
fi

round_prompt() {
  case "$SKILL" in
    debate)
      echo "Collide over the claim with room-$1.json. Write record-$1.md (collisions + new tensions), update tensions.txt. Continue?" ;;
    brainstorm)
      if [ "$1" = "1" ]; then
        echo "Open the field with room-1.json: one approach per lens, at least five. Write field.md, update tensions.txt. Continue?"
      else
        echo "Thin the field with room-2.json: attack each approach, kill the undefended. Write record.md. Continue?"
      fi ;;
    reframe)
      echo "Offer new frames with room-$1.json. Write frames-$1.md (candidates + kills + new tensions), update tensions.txt. Continue?" ;;
    review)
      if [ "$1" = "1" ]; then
        echo "Read back intent in three layers (explicit, implied, hard constraints). Write intent.md, update tensions.txt. Continue?"
      else
        echo "Collide intent.md with the evidence using room-2.json. Write verdict.md (one line + gaps with owners). Continue?"
      fi ;;
    add-skill)
      if [ "$1" = "1" ]; then
        echo "Draft the SKILL.md and the run.sh diff with room-1.json. Write draft.md, update tensions.txt. Continue?"
      else
        echo "Validate (muse skills validate), test end to end via run.sh, grep for leaks. Write record.md. Continue?"
      fi ;;
  esac
}

mkdir -p "$SESSION"
cd "$SESSION"
export SKILLFLOW_DB="$SESSION/skillflow.db"
if [ -f "$SKILLFLOW_DB" ]; then
  echo "error: session already exists at $SESSION;" \
    "cd into it and run 'skillflow run' to retry, or use a fresh directory" >&2
  exit 2
fi

echo "$SUBJECT" > subject.txt
echo "$SUBJECT" > tensions.txt
"${SF[@]}" init >/dev/null
"${SF[@]}" add-node seed-panel --cmd "SKILLFLOW_DB='$SESSION/skillflow.db' python3 '$PANEL_DIR/seed.py'" >/dev/null
PREV="seed-panel"
EXCLUDES=""
i=1
while [ "$i" -le "$ROUNDS" ]; do
  "${SF[@]}" add-node "select-$i" --cmd \
    "python3 '$PANEL_DIR/select_room.py' --tensions \"\$(cat tensions.txt)\" --out room-$i.json$EXCLUDES" >/dev/null
  "${SF[@]}" add-node "round-$i" --cmd \
    "read -p '$(round_prompt "$i") [y/N] ' a; [ \"\$a\" = y ]" >/dev/null
  "${SF[@]}" add-edge "$PREV" "select-$i" >/dev/null
  "${SF[@]}" add-edge "select-$i" "round-$i" >/dev/null
  PREV="round-$i"
  EXCLUDES="$EXCLUDES --exclude room-$i.json"
  i=$((i + 1))
done

"${SF[@]}" run
