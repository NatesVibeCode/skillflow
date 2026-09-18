---
name: brainstorm
description: Open the field of approaches with the panel before committing to one. Use when several ways forward exist and picking too early would be the mistake.
---

# Brainstorm

**Requires:** [skillflow](https://github.com/NatesVibeCode/skillflow) — run via `panel/run.sh`.

Generate the field before choosing the path. The panel produces approaches,
then kills the weak ones — choosing happens elsewhere, after the field is
visible.

## Run

```sh
panel/run.sh brainstorm "<goal>" [session-dir]
```

The DAG runs two rounds: open the field (one approach per lens, at least
five), then thin it. Tensions are distilled before the first seat; the
machine seats each room from them and checks your activation worksheet
names every seated panelist. `tensions` extracts each record's
`## New tensions` section into `tensions.txt` itself; empty or unchanged
tensions end the session early. A boundary stops the run and names the
file — write it and rerun in the same session.

## Record

`field.md` holds every approach; `record.md` holds the survivors with one
paragraph each — what it is, what it costs a person, how its success would
show — plus what was killed and why. A stranger reads it in under a minute
and can pick from it without asking questions.
