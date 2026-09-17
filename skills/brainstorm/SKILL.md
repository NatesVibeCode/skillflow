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
five), gate, then thin it. A gate stops each round until a person approves
the record.

## Record

`field.md` holds every approach; `record.md` holds the survivors with one
paragraph each — what it is, what it costs a person, how its success would
show — plus what was killed and why. A stranger reads it in under a minute
and can pick from it without asking questions.
