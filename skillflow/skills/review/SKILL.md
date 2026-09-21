---
name: review
description: Compare actual work with the user's intent through evidence and contrasting lenses in the current conversation. Use to identify aligned changes, misses, and unproven claims.
---

# Review

The change must defend itself against the user's intent. Produce an alignment
delta: what was wanted, what exists, where those differ, and what evidence or
repair closes each gap. You do the review in-session; the DAG ensures intent
is reconstructed before findings; it does not rate the review itself.

Read [the room method](../_shared/panel.md) and
[the pause loop](../_shared/running-on-skillflow.md), then start:

```sh
python3 "<skills-root>/_shared/run.py" review "<work under review>" "<session-dir>"
```

Resolve `<skills-root>` from this skill's directory. A `PAUSE` returns work to you,
not to another agent or the user. Write its artifact and resume in the same session.

## First phase: reconstruct intent

Read the user's request, corrections, rejected outputs, taste signals, and hard
boundaries. Then inspect the actual change, code, plan, answer, and relevant proof.
A source file proves an implementation exists; it does not by itself prove live
behavior. Distinguish observed results, assertions, and missing evidence.

When earlier corrections, rejected outputs, decisions, or incidents can explain
the intended shape, recover them through bounded semantic work-history recall or
the supplied evidence. Let that context change the reading of the work in the
room. Do not turn it into an intent scorecard or let it override an explicit
current correction.

Choose and activate lenses that disagree usefully about intent and evidence.
Write `intent.md` with explicit asks, implied quality bar, hard constraints, and
later corrections that changed the target. Semantic intent matters more than
matching words, unless exact wording was itself the request. Never let inferred
intent override an explicit correction.

## Pause, then compare

After the intent checkpoint, let the lenses challenge one another's reading of
what the user wanted and what the work proves. Use exact examples and relevant
checks. Do not decide all findings first and assign voices to endorse them.

Write `verdict.md` as a concrete review conversation. Keep the useful deltas
legible, but let the exchange lead rather than emitting a compliance list:

- `aligned`: matches intent and has supporting evidence;
- `intentional_change`: differs from an earlier ask because of a later user
  correction or explicit decision;
- `miss`: fails the intended behavior or boundary;
- `unproven`: might align but the necessary evidence is missing.

Each material delta names the intent, actual behavior, evidence, and the smallest
proof, repair, or decision needed. Name the owner when known; do not invent one.
A review can contain all four categories. A single “holds/fails” verdict must not
hide their differences. If the user needs a shipping decision, derive it from the
specific blockers and say which proof remains missing.

Working but uninspired is not a defect unless the user asked for that quality
bar. Better architectural possibilities belong to reframe; do not silently switch
skills or expand the review into a redesign. Do not invent findings to make the
panel useful. Honest agreement supported by evidence is allowed.

## Deliver the review as an argument

After the final pause, write `final.md` yourself. Give the consequential exchange
over intent and evidence, then let the findings appear where the exchange earned
them. A compact table is useful only when it makes several comparable deltas
clearer; it must not replace the review. Include important evidence limits in the
answer itself, not only in a linked record.

Check whether challenging another lens changed a classification, its confidence,
or the next proof. If not, explain why the evidence supported agreement; never
stage a fake reversal. Reopen the affected phase if the review became generic
findings, taste criticism, or unsupported reassurance. The DAG validates sequence,
not correctness.
