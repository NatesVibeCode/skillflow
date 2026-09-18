# Running on skillflow

Each skill IS a skillflow graph. The procedure lives in the DAG — seed the
panel, distill tensions, seat rooms, activate them, collide, check the
work, extract tensions, finalize — not in prose. One command builds and
runs the whole session:

```sh
panel/run.sh debate "<claim>" [rounds] [session-dir]
panel/run.sh brainstorm "<goal>" [session-dir]
panel/run.sh reframe "<current frame>" [rounds] [session-dir]
panel/run.sh review "<work under review>" [session-dir]
panel/run.sh add-skill "<new skill idea>" [session-dir]
```

## Graph shape

    seed-panel -> distill -> select-1 -> activate-1 -> round-1
      [-> validity-1 (debate)] -> tensions-1 -> select-2 -> ... -> finalize

- `seed-panel` loads the `panelists` table into the session DB.
- `distill` gates two to five distilled tensions before the first seat: the
  session writes `tensions.txt` from the subject, and the selector never
  reads the raw subject.
- Per round: `select-N` seats the room from the tensions file
  (`panel/select_room.py`: semantic match, diversity enforced, previous
  rooms excluded). A seated room is immutable — reruns never re-seat it,
  so the lenses that chose the round stay the lenses that answer for it.
- `activate-N` checks the round's activation worksheet exists and names
  every seated panelist: per panelist, first irritation, fault line,
  evidence standard, claim they would kill. The room earns its voice
  before it speaks.
- `round-N` is a stage boundary that stores the response for that round.
- `validity-N` (debate only) rejects a record without a live Validity
  Readback: `collision_that_changed_answer`, `claim_or_option_killed`,
  `persona_flattening_check`, `giggle_or_wince_line`,
  `survivor_provenance` — all non-empty.
- `tensions-N` is a machine node: it extracts the record's
  `## New tensions` section and writes `tensions.txt` itself. The session
  never rewrites the material the chooser reads. Empty or unchanged
  tensions mark the session converged and the rest of the graph drains —
  a round that moves nothing is the stop.
- `finalize` collects every stored round response into `final.md`, the
  final section.

## One session

You are the panel. Run the DAG, author each round's response, rerun — all in
the same session. Nothing prompts for a person and nothing is handed to
another session:

- No terminal prompt. `round-N` never blocks on a TTY and never reads
  `y/N`.
- A missing response is the stage boundary. The run stops at that node,
  names the file to write (`tensions.txt`, `activation-N.md`, `field.md`,
  `record-N.md`, `frames-N.md`, `intent.md`, `verdict.md`, `draft.md`),
  and you write it and rerun.
- `refusal.md` is a legitimate stop with a trace: the refusal is stored,
  the run ends, and `final.md` records where it stopped. Refusing is an
  output, not an error.
- Each response is stored internally: `notes/round-N.md` plus the node
  result in the session DB.

## Rules

- The selector seats every room. Nobody hand-picks panelists in prose.
- Tensions are distilled before the first seat and extracted by machine
  after every round. Do not edit `tensions.txt` mid-session; the chooser
  reads what the record said, not what you summarize.
- Activate the room before it speaks: a worksheet that skips a seated
  panelist fails the boundary.
- Claims die because a panelist's evidence standard forced the death —
  not because the scribe decided. Run the delete-the-personas test: if
  removing every persona line leaves the judgment intact, rerun from
  first irritation.
- Mechanical setup is not success. Resolving the DAG, seating rooms, and
  writing records only prove the room was authorized. The readback is the
  proof a debate happened.
- Do not claim a round is done while its stage boundary is unmet, and do
  not paper over a failed node by writing the record yourself out of
  order.
- Do not pipe the runner through `tail` or similar; that hides a stopped
  round. Read its exit code.
- A stopped run is a verdict, not an error: read the boundary message,
  write the response, run again. A refusal is a verdict too, with a
  trace.
- Every response, room file, and the DB land in the session directory, so
  `skillflow status` always shows what is stored and where the run
  stopped.
