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

Run it as one session: you run the DAG, and you author every response.
Nothing waits on a person or another session — there is no terminal prompt
and no handoff.

Round 1 drafts; round 2 validates and tests. Each round node is a stage
boundary: it stores that round's response in `notes/round-N.md` and on the
node result. `finalize` writes `final.md`, the final section with every
stored response. A round with no response stops the run and names the file to
write — write it and rerun in the same session.

## Rules for the new skill

- Directory `skills/<id>/` with one `SKILL.md`. The id is lowercase ASCII,
  digits, hyphens only — and it must match the frontmatter `name`.
- Frontmatter is exactly `name` + one-sentence `description`.
- Body stays thin: what it is, the `panel/run.sh <id>` command, and the
  record format. The procedure goes in the graph (round prompts in
  `panel/run.sh`), never in prose.
- No terminal prompts and no handoffs: one session runs the DAG and authors
  each response. A round node is a stage boundary that stores the response
  and stops the run when it is missing.
- No mention of private systems, people, or history. Grep the draft for
  leaks before calling it done.
- Fixed-shape skills (like brainstorm/review) take no rounds argument;
  round-loop skills (like debate/reframe) default to 3.

## Record

`draft.md` holds the new SKILL.md text plus the run.sh diff; `record.md`
holds the validator output, the end-to-end test result, and the leak-grep
result. Both read in under a minute.
