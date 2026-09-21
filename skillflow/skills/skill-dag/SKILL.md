---
name: skill-dag
description: Bring an existing skill into a store or make a new one correctly. Use when adding any skill: intake decides import, create, or decline, then shape, build, and proof follow.
---

# Skill Dag

You are the intake concierge for this skill store. The human brings an
existing skill or a new idea; you fit it into the store correctly or tell
them plainly why no skill is needed. A local DAG enforces the phase
boundaries; the prose work stays here.

Read [the shared protocol](../_shared/authoring.md), then start:

```sh
python3 "<skills-root>/_shared/run.py" skill-dag "<skill idea, or path to the existing skill>" "<session-dir>"
```

Resolve `<skills-root>` from this skill's directory, not the current repo.
After every `PAUSE`, do the work, write that artifact, and resume in this same
conversation.

## Intake

Read the request, any existing skill text, and the current store layout.
Check for overlap: a skill that already covers this job wins over a new one.
Apply the fit criteria — order matters, each phase leaves an artifact,
someone would otherwise rush, the procedure is fixed but the thinking is
open, the method is reusable. Write `intake.md` with the survey and your
recommendation: import the existing skill, create a new one, or decline.
A decline must name what to do instead: the existing skill to use, or the
one-off path when nothing reusable is there.

## Shape

Deliberate in writing; do not default. Argue prose, single, and
setup-execute against this skill, then argue the single-vs-two question in
both directions: what breaks if it runs as one node, and what levelset
actually buys. Record the choice and its reason in `shape.md`. If nothing
below a custom ladder fits, stop here and point at the repo authoring flow
instead of inventing phases.

## Build

Write the new `SKILL.md`, or the reshaped one plus notes on what changed,
into `draft.md`. Keep the body thin: what it is, the launcher command
unless prose, and the record format. The procedure lives in the phases,
never in prose. Frontmatter is exactly `name` plus one-sentence
`description` plus `shape`.

## Prove

Validate with the store checker, walk a DAG skill's gates in a scratch
session, and grep the draft for leaks of private systems, people, or
history. Write `record.md` with all three results. All three must pass
before finalizing. A declined intake skips here with its reason intact.

## Deliver

Write `final.md` yourself and record it through the final pause: the skill,
its wiring, and its proof — or the decline with its guidance. Give the
useful result inline, not a link to the session directory.
