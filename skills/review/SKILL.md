---
name: review
description: Read back intent, check what was built against it, and give a verdict with the panel. Use when work claims to be done and someone should verify that.
---

# Review

**Requires:** [skillflow](https://github.com/NatesVibeCode/skillflow) — run via `panel/run.sh`.

Work says it is done. The panel reads back what was asked, looks at what was
built, and gives a verdict: holds, holds with gaps named, or fails. Soft
passes are lies about ownership — a gap named is a gap ownable; a gap
smoothed over is a debt with no owner.

## Run

```sh
panel/run.sh review "<work under review>" [session-dir]
```

The DAG runs two rounds: read back intent in three layers (explicit,
implied, hard constraints), then collide intent with evidence and give the
verdict. Tensions are distilled before the first seat; the machine seats
each room and checks your activation worksheet names every seated
panelist. `tensions` extracts each record's `## New tensions` section into
`tensions.txt` itself; empty or unchanged tensions end the session early.
A boundary stops the run and names the file — write it and rerun in the
same session.

## Record

`intent.md` holds the three-layer readback; `verdict.md` holds the one-line
verdict with named gaps and owners. A stranger reads them in under a minute
and knows exactly what is done and what is not.
