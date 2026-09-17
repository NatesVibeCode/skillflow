# Running on skillflow

Each skill IS a skillflow graph. The procedure lives in the DAG — seed the
panel, select rooms, collide, gate — not in prose. One command builds and
runs the whole session:

```sh
panel/run.sh debate "<claim>" [rounds] [session-dir]
panel/run.sh brainstorm "<goal>" [session-dir]
panel/run.sh reframe "<current frame>" [rounds] [session-dir]
panel/run.sh review "<work under review>" [session-dir]
```

## Graph shape

- `seed-panel` loads the `panelists` table into the session DB.
- Per round: `select-N` seats the room from the tensions file
  (`panel/select_room.py`: semantic match, diversity enforced, previous
  rooms excluded), then `round-N` gates.
- Each gate stops until a person has done the round's work, written its
  record, and updated the tensions for the next round's selection.

## Rules

- The selector seats every room. Nobody hand-picks panelists in prose.
- One gate per round. No round starts until the previous record is read.
- A failed gate is a verdict, not an error: read the record, fix the work,
  run again.
- Every record, room file, and the DB land in the session directory, so
  `skillflow status` always shows what the person approved and what stopped.
