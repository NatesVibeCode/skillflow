---
name: debate
description: Attack a claim from five sides in rounds until only what survives stands. Use when a decision matters and someone should try to break it first.
---

# Debate

**Requires:** [skillflow](https://github.com/NatesVibeCode/skillflow) — run via `panel/run.sh`.

Put one claim in the room and let the panel try to break it. What survives,
in smaller and harder form, is the outcome.

## Run

```sh
panel/run.sh debate "<claim>" [rounds] [session-dir]
```

The DAG runs the procedure, and the DAG is what keeps the room honest:

- `distill` gates two to five distilled tensions before any seat — the
  selector reads distilled tensions, never the raw subject.
- Per round the machine seats the room from those tensions (rooms are
  immutable once seated; earlier rooms excluded), checks your activation
  worksheet names every seated panelist, then gates the crossfire record.
- `validity` rejects a record without a live Validity Readback:
  `collision_that_changed_answer`, `claim_or_option_killed`,
  `persona_flattening_check`, `giggle_or_wince_line`,
  `survivor_provenance`. Mechanical setup is not success.
- `tensions` extracts the record's `## New tensions` section into
  `tensions.txt` itself — you never rewrite the material the chooser reads.
  Empty or unchanged tensions end the session: a round that moves nothing
  is the stop.
- `refusal.md` is a legitimate stop with a trace: refusing is an output,
  not an error.

A boundary stops the run and names the file to write — write it and rerun
in the same session. What survives, in smaller and harder form, is the
outcome.

## Record

Each round writes `record-N.md`: where the claim moved, what died, what is
still standing, and the new tensions for the next round. A stranger reads it
in under a minute.
