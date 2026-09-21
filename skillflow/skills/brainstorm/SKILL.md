---
name: brainstorm
description: Generate surprising, concrete approaches through contrasting lenses in the current conversation. Use when the field needs opening before choosing a direction.
---

# Brainstorm

Divergence is the scarce resource. Produce a field of non-obvious mechanisms,
not approval of the seed and not a prematurely ranked action list. You do all the
work in this session; the DAG enforces generation before development without
judging the result for you.

Read [the room method](../_shared/panel.md) and
[the pause loop](../_shared/running-on-skillflow.md), then start:

```sh
python3 "<skills-root>/_shared/run.py" brainstorm "<goal or seed>" "<session-dir>"
```

Resolve `<skills-root>` from this skill's directory. At each `PAUSE`, do the work,
write the requested artifact, and resume yourself in this conversation. Do not
wait for a person or another model to do it.

## Ground without caging the field

Read what exists, what the user wants to make possible, relevant corrections,
and the constraints that actually bind. Distinguish known facts from assumptions.
The seed is launch material, not an answer to defend. If a previous attempt was
ordinary, name the constraint or premature judgment that made it ordinary.

When earlier decisions, rejected ideas, failed attempts, or session history can
open a better field, recover them with bounded semantic work-history recall or
the supplied evidence. Bring their reasons into the room as raw material; do not
make a history summary or treat them as a veto on a changed situation.

Choose the form the request needs: an architecture room, concrete product ideas,
transfer of a useful mechanism to another domain, or a thought experiment. Do not
force market sizing or shipping plans onto an exploratory conversation.

## First phase: generate away from the obvious answer

Choose and activate contrasting lenses yourself. Start from a specific obsession,
strange analogy, inversion, forbidden interface, or hidden assumption. Let voices
build on and mutate each other's moves. Do not distribute generic ideas among
names after inventing them alone.

Ask midway: **What becomes possible if we refuse the obvious interface or the
seed's hidden constraint?** Follow the answer into a mechanism, not a catchy name.
Explore materially different approaches; do not satisfy a quota with cosmetic
variants. Preserve unresolved strangeness long enough to learn from it.

Write `field.md` before choosing favorites. Each developed idea explains:

- the concrete move and how it works;
- what becomes possible, and where it touches the system or human workflow;
- the cheapest observation, example, prototype, or test that would give it teeth;
- the assumption the ordinary answer missed.

For a thought experiment, the first proof can be what we would observe if it were
true. A metaphor without a mechanism is raw material, not a finished idea.

## Pause, then develop the field

Only after the field checkpoint, revisit it with fresh objections or lenses.
Combine promising ideas, make mechanisms clearer, and remove empty labels or
true duplicates. Do not turn this phase into full adversarial elimination;
usefulness includes expanding the search space and exposing a hidden question.

Write `record.md` with the developed field, the exchange that changed a move,
what was dropped and why, and what later debate or experimentation must check.
No claim/no-claim lineup or Must/Should/Can table here: that belongs to reframe.
Do not silently choose and implement a winner.

## Deliver the field, not a report about it

Write `final.md` yourself after the final pause. Give the generative room in full:
the strange move, the response that mutated it, the mechanism that made it real,
and the question it leaves open. Let one turn land hard enough to change the
reader's picture of the problem. Use headings only if they keep the room legible;
do not compress it into a safe inventory of ideas or a final ranking.

If the output is merely the safest version of the seed, an interchangeable panel,
or a clever concept list without mechanisms, repair once from the strangest missed
connection. If it still fails, explain the limit; do not dress a generic answer
as a successful brainstorm. A completed DAG is not evidence of originality, and
an artifact is not the deliverable in place of the visible conversation.
