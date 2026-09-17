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

The DAG runs the procedure: seed the panel, then per round select a room,
collide over the claim, write the record, and gate on a person's approval.
What survives, in smaller and harder form, is the outcome.

## Record

Each round writes `record-N.md`: where the claim moved, what died, what is
still standing, and the new tensions for the next round. A stranger reads it
in under a minute.
