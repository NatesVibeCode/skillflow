---
name: reframe
description: Find and test stronger shapes for an existing build or concrete proposal in the current conversation. Use to explore better models, boundaries, algorithms, or component arrangements beyond whether the work passes.
---

# Reframe

Find the stronger shape we did not build. Something can satisfy the original ask
and still leave useful power on the table. You generate and assess alternatives
in-session; the DAG separates those activities without rating the result for you.

Read [the room method](../_shared/panel.md) and
[the pause loop](../_shared/running-on-skillflow.md), then start:

```sh
python3 "<skills-root>/_shared/run.py" reframe "<current approach>" 3 "<session-dir>"
```

Resolve `<skills-root>` from this skill's directory. Do the work at every `PAUSE`,
write that artifact, and resume yourself. Neither another model nor a human
confirmation is needed for routine phase changes.

## Ground in an actual approach

Read the build, proposal, code, plan, tests, or concrete specimen. Explain its
current shape and why that shape was reasonable. Keep user intent and hard
constraints explicit. If there is no concrete approach, identify that limitation;
ask for the missing specimen or offer brainstorm without silently replacing the
requested task. A pass/miss question belongs to review, not novelty hunting.

When earlier attempts, decisions, implementation history, or constraints explain
why this shape exists, recover them with bounded semantic work-history recall or
the supplied evidence. Bring the actual reason into the room. A past constraint
is a question to test against the current build, not a permanent veto.

Treat the current approach as assumptions to invert or stretch, not something to
protect or tear down automatically. Select and activate lenses against its actual
state, boundaries, and consequences.

## First phase of each round: stronger shapes

Ask: **If this works, what different model or arrangement could still dominate it?**
Where relevant, explore both mathematical/data-model alternatives and component/
architecture alternatives. For non-software work, use the corresponding process,
information, decision, or responsibility model. Do not force decorative math.

Let lenses generate and mutate moves before comparison with the current approach.
Write `frames-N.md` with every surfaced alternative's concrete change, mechanism,
capability gain, touchpoint, first proof, and the assumption that hid it. A grand
new name for the same refactor is not a stronger shape.

## Pause, then claim/no-claim

Only after the generation checkpoint, compare each alternative with the existing
approach. Challenge benefit, proof, transition cost, operational burden, and blast
radius. Let objections change, combine, or kill alternatives.

Write `lineup-N.md` as the room compares the alternatives. A visible comparison
can help when it clarifies a real distinction, but it is not the deliverable and
does not need to become a closing table:

| Alternative | Defensible claim? | Priority | Cheapest proof | Cost / blast radius |
| --- | --- | --- | --- | --- |

Classify after the field exists:

- **Must Do**: addresses a demonstrated correctness, authority, recovery, or
  other binding risk;
- **Should Do**: a defensible meaningful improvement beyond current correctness;
- **Can Do**: plausible, worth a prototype or experiment before adoption;
- **Not Worth It**: benefit fails the proof, cost, or disruption comparison.

No-claim alternatives should die for a reason, not to fill a required rejection
quota. Do not call a boring working choice a defect without an intent or contract
basis. Keep every surfaced alternative accounted for, including rejected ones.

## Reflect and deliver

At `decision-N.json`, decide whether another round has a real new tension, whether
the field has settled, or whether the method failed. The runner does not infer
convergence from wording. Respect the round ceiling without pretending it proves
consensus. Reopen a label-only or prematurely ranked field; if it remains empty,
say no stronger shape was established.

Write `final.md` as the complete useful room: the current shape, the move that
made another shape visible, the objection that changed it, and the proof it now
needs. Let the ending be a defensible opportunity, a residual tension, or a live
question—not a generic priority list. Do not quietly implement the redesign.
