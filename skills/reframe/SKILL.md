---
name: reframe
description: Restate the problem in rounds until the shape of the work changes. Use when the team is solving hard and the problem might be wrong.
---

# Reframe

**Requires:** [skillflow](https://github.com/NatesVibeCode/skillflow) — run via `panel/run.sh`.

The work is stuck or swelling. Instead of pushing harder, restate the problem
until a different shape of work appears — then check whether the new shape is
smaller, kinder, or truer than the old one.

## Run

```sh
panel/run.sh reframe "<current frame>" [rounds] [session-dir]
```

The DAG runs the passes: per round select a room, offer new frames, keep at
most two, kill the rest out loud. A gate stops each round until a person
approves the record.

## Record

Each pass writes `frames-N.md`: the candidates in one paragraph each, what
was killed and why, and the new tensions. The final record names the
surviving frame and what changes because of it. A stranger reads it in under
a minute and can explain the turn to someone else.
