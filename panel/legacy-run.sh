#!/usr/bin/env bash
# run.sh — run a panel skill as a skillflow DAG.
#
# One session runs the whole graph. The procedure lives in the DAG, not in
# docs: each skill builds its own DAG and runs it.
#
#   seed-panel -> distill -> select-N -> activate-N -> round-N
#     [-> validity-N (debate)] -> tensions-N -> select-N+1 ... -> finalize
#
# The machine chooses: distill gates the session's distilled tensions before
# any seat; select seats rooms from those tensions (rooms are immutable once
# seated; earlier rooms excluded); activate checks the round's worksheet
# names every seated panelist; tensions extracts the record's `## New
# tensions` section into tensions.txt itself — the session never rewrites
# the material the chooser reads. The session authors: the worksheet, the
# round's crossfire record, and nothing else. A round node is a
# machine-checked stage boundary, not a prompt: a run stops with the round's
# instruction when the response is not written yet; the active session
# writes it and reruns. refusal.md is a legitimate stop with a trace. Empty
# or unchanged tensions mark the session converged and the rest of the
# graph drains. `finalize` writes final.md, the final section with every
# stored response.
#
# Usage: panel/run.sh <skill> "<subject>" [rounds] [session-dir]
#   skill    debate | brainstorm | reframe | review | add-skill
#   subject  claim | goal | frame | work-under-review | new skill idea
#   rounds   debate/reframe only (default 3; the rest have fixed shapes)
#
# Requires the `skillflow` CLI on PATH, or set SKILLFLOW_CMD.
set -euo pipefail

SKILL="${1:?usage: run.sh <debate|brainstorm|reframe|review|add-skill> \"<subject>\" [rounds] [dir]}"
SUBJECT="${2:?usage: run.sh <debate|brainstorm|reframe|review|add-skill> \"<subject>\" [rounds] [dir]}"
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

case "$ROUNDS" in
  ''|*[!0-9]*)
    echo "error: rounds must be a number 1-8, got '$ROUNDS'" >&2; exit 2 ;;
esac
if [ "$ROUNDS" -lt 1 ] || [ "$ROUNDS" -gt 8 ]; then
  echo "error: rounds must be 1-8, got '$ROUNDS'" >&2; exit 2
fi

# The file the session writes for a given round, per skill shape.
artifact_for() {
  case "$SKILL:$1" in
    debate:*)        echo "record-$1.md" ;;
    brainstorm:1)    echo "field.md" ;;
    brainstorm:*)    echo "record.md" ;;
    reframe:*)       echo "frames-$1.md" ;;
    review:1)        echo "intent.md" ;;
    review:*)        echo "verdict.md" ;;
    add-skill:1)     echo "draft.md" ;;
    add-skill:*)     echo "record.md" ;;
  esac
}

# What the round node tells the session to do when its response is missing.
round_prompt() {
  case "$SKILL" in
    debate)
      echo "Collide over the claim with room-$1.json, then write record-$1.md: the crossfire that changed the answer, what died, a Validity Readback, and a '## New tensions' section. Tensions are extracted by machine; do not edit tensions.txt." ;;
    brainstorm)
      if [ "$1" = "1" ]; then
        echo "Open the field with room-1.json: one approach per lens, at least five. Write field.md."
      else
        echo "Thin the field with room-2.json: attack each approach, kill the undefended. Write record.md with a '## New tensions' section."
      fi ;;
    reframe)
      echo "Offer new frames with room-$1.json, then write frames-$1.md (candidates + kills) with a '## New tensions' section." ;;
    review)
      if [ "$1" = "1" ]; then
        echo "Read back intent in three layers (explicit, implied, hard constraints). Write intent.md."
      else
        echo "Collide intent.md with the evidence using room-2.json. Write verdict.md (one line + gaps with owners) with a '## New tensions' section."
      fi ;;
    add-skill)
      if [ "$1" = "1" ]; then
        echo "Draft the SKILL.md and the run.sh diff with room-1.json. Write draft.md with a '## New tensions' section."
      else
        echo "Validate (muse skills validate), test end to end via run.sh, grep for leaks. Write record.md."
      fi ;;
  esac
}

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

mkdir -p "$SESSION"
# Absolute from here on: the DAG runs with the session dir as its cwd, so a
# relative --dir would otherwise resolve a second time.
SESSION="$(cd "$SESSION" && pwd)"
cd "$SESSION"
export SKILLFLOW_DB="$SESSION/skillflow.db"
if [ -f "$SKILLFLOW_DB" ]; then
  echo "error: session already exists at $SESSION;" \
    "cd into it and run 'skillflow run' to retry, or use a fresh directory" >&2
  exit 2
fi

echo "$SUBJECT" > subject.txt
"${SF[@]}" init >/dev/null
"${SF[@]}" add-node seed-panel --cmd "SKILLFLOW_DB='$SESSION/skillflow.db' python3 '$PANEL_DIR/seed.py'" >/dev/null
# The selector reads distilled tensions, never the raw subject: the session
# distills two to five into tensions.txt before the first seat.
"${SF[@]}" add-node distill --cmd \
  "python3 '$PANEL_DIR/stage.py' tensions --initial --min 2 --max 5 --dir '$SESSION'" >/dev/null
"${SF[@]}" add-edge seed-panel distill >/dev/null
PREV="distill"
EXCLUDES=""
i=1
while [ "$i" -le "$ROUNDS" ]; do
  ARTIFACT="$(artifact_for "$i")"
  PROMPT="$(round_prompt "$i" | sed "s/'/'\\\\''/g")"
  "${SF[@]}" add-node "select-$i" --cmd \
    "[ -f converged.txt ] || [ -f room-$i.json ] || { python3 '$PANEL_DIR/select_room.py' --tensions \"\$(cat tensions.txt)\" --out room-$i.json$EXCLUDES && cp tensions.txt used-$i.txt; }" >/dev/null
  "${SF[@]}" add-node "activate-$i" --cmd \
    "[ -f converged.txt ] || python3 '$PANEL_DIR/stage.py' activate --skill '$SKILL' --round $i --room 'room-$i.json' --artifact 'activation-$i.md' --dir '$SESSION'" >/dev/null
  "${SF[@]}" add-node "round-$i" --cmd \
    "[ -f converged.txt ] || python3 '$PANEL_DIR/stage.py' round --skill '$SKILL' --round $i --artifact '$ARTIFACT' --prompt '$PROMPT' --dir '$SESSION'" >/dev/null
  "${SF[@]}" add-edge "$PREV" "select-$i" >/dev/null
  "${SF[@]}" add-edge "select-$i" "activate-$i" >/dev/null
  "${SF[@]}" add-edge "activate-$i" "round-$i" >/dev/null
  PREV="round-$i"
  if [ "$SKILL" = debate ]; then
    "${SF[@]}" add-node "validity-$i" --cmd \
      "[ -f converged.txt ] || python3 '$PANEL_DIR/stage.py' validity --record '$ARTIFACT' --dir '$SESSION'" >/dev/null
    "${SF[@]}" add-edge "round-$i" "validity-$i" >/dev/null
    PREV="validity-$i"
  fi
  "${SF[@]}" add-node "tensions-$i" --cmd \
    "[ -f converged.txt ] || python3 '$PANEL_DIR/stage.py' tensions --record '$ARTIFACT' --baseline 'used-$i.txt' --round $i --dir '$SESSION'" >/dev/null
  "${SF[@]}" add-edge "$PREV" "tensions-$i" >/dev/null
  PREV="tensions-$i"
  EXCLUDES="$EXCLUDES --exclude room-$i.json"
  i=$((i + 1))
done

"${SF[@]}" add-node finalize --cmd \
  "python3 '$PANEL_DIR/stage.py' final --skill '$SKILL' --dir '$SESSION'" >/dev/null
"${SF[@]}" add-edge "$PREV" "finalize" >/dev/null

"${SF[@]}" run
