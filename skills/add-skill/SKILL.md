---
name: add-skill
description: Author a new skillflow panel skill end to end: draft it, wire its stages, validate it, test it. Use when adding a skill to this repo.
---

# Add Skill

Author a new skill in this session. A local DAG enforces phase breaks;
the prose work stays here.

Read [the room method](../_shared/panel.md) and
[the pause loop](../_shared/running-on-skillflow.md), then start:

```sh
python3 "<skills-root>/_shared/run.py" add-skill "<skill name: one line on what it does>" "<session-dir>"
```

Resolve `<skills-root>` from this skill's directory, not the current repo.
After every `PAUSE`, do the work, write that artifact, and resume in this same
conversation. It is not a permission question, another agent's job, or a reason
to end the turn.

## Ground in the repo

Read the request and the current `skills/` layout plus `panel/checkpoints.py`.
A new skill is three things: a thin `SKILL.md`, a stage plan registered in
`checkpoints.py`, and proof it runs. Keep the user's scope; do not redesign
sibling skills along the way.

## Draft, then prove

Write `draft.md` with the new SKILL.md text plus the `checkpoints.py` diff.
Rules for the new skill:

- Directory `skills/<id>/` with one `SKILL.md`. The id is lowercase ASCII,
  digits, hyphens only — and it must match the frontmatter `name`.
- Frontmatter is exactly `name` + one-sentence `description`.
- Body stays thin: what it is, the launcher command, and the record format.
  The procedure goes in the graph (stage prompts in `checkpoints.py`),
  never in prose.
- No terminal prompts and no handoffs: one session runs the DAG and authors
  each response. A gate is a stage boundary that records the artifact
  and stops the run when it is missing or unrevised.
- No mention of private systems, people, or history. Grep the draft for
  leaks before calling it done.
- Fixed-shape skills (like brainstorm/review) take no rounds argument;
  round-loop skills (like debate/reframe) default to 3.

Write `record.md` with the validator output (`panel/check_skills.py`), the
end-to-end test result (walk the new skill's gates in a scratch session),
and the leak-grep result. All three must pass.

## Deliver

Write `final.md` yourself and record it through the final pause: the new
skill, its wiring, and its proof. Give the useful result inline, not a link
to the session directory.
