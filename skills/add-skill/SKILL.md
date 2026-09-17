---
name: add-skill
description: Author a new skillflow panel skill end to end: draft it, wire its DAG, validate it, test it. Use when adding a skill to this repo.
---

# Add Skill

**Requires:** [skillflow](https://github.com/NatesVibeCode/skillflow) — run via `panel/run.sh`.

A new skill is three things: a thin `SKILL.md`, a DAG shape in
`panel/run.sh`, and proof it runs. This skill walks all three.

## Run

```sh
panel/run.sh add-skill "<skill name: one line on what it does>" [session-dir]
```

Round 1 drafts; round 2 validates and tests. Gates stop each round until a
person approves.

## Rules for the new skill

- Directory `skills/<id>/` with one `SKILL.md`. The id is lowercase ASCII,
  digits, hyphens only — and it must match the frontmatter `name`.
- Frontmatter is exactly `name` + one-sentence `description`.
- Body stays thin: what it is, the `panel/run.sh <id>` command, and the
  record format. The procedure goes in the graph (round prompts in
  `panel/run.sh`), never in prose.
- No mention of private systems, people, or history. Grep the draft for
  leaks before calling it done.
- Fixed-shape skills (like brainstorm/review) take no rounds argument;
  round-loop skills (like debate/reframe) default to 3.

## Record

`draft.md` holds the new SKILL.md text plus the run.sh diff; `record.md`
holds the validator output, the end-to-end test result, and the leak-grep
result. Both read in under a minute.
