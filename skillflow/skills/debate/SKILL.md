---
name: debate
description: Pressure-test a claim or approach through source-grounded crossfire in the current conversation. Use when a decision matters and competing objections should change the answer.
---

# Debate

Produce collision clarity: what claim fails, what judgment changes, what survives,
and what remains unresolved. You are doing the debate in this session. A local
DAG enforces phase breaks; the prose work stays here.

Read [the room method](../_shared/panel.md) and
[the pause loop](../_shared/running-on-skillflow.md), then start:

```sh
python3 "<skills-root>/_shared/run.py" debate "<claim or approach>" 3 "<session-dir>"
```

Resolve `<skills-root>` from this skill's directory, not the current repo.
After every `PAUSE`, do the work, write that artifact, and resume in this same
conversation. It is not a permission question, another agent's job, or a reason
to end the turn.

## Ground and choose the kind of debate

Read the actual proposal and relevant sources. Identify the live claim and two
to five tensions. If following a prior answer, identify what that answer's method
missed. Keep the user's selected target and full requested scope.

During grounding, recover prior decisions, implementation history, session
evidence, failed approaches, or constraints only when they could materially
change this claim. Use bounded semantic work-history recall if it is available;
otherwise use the supplied local evidence. Let it inform the room rather than
becoming a separate report. Current operator instruction and live sources outrank
history.

For architecture, approach, taste, or hidden-failure questions, seek sharper
judgment; do not force a build packet. For a concrete change or ordering decision,
leave a defensible change set or sequence. For product questions, pressure-test
what the customer can actually do and which evidence supports the promise.
Do not import customer-copy or market checklists into an internal architecture
question that does not need them.

## Activate, then collide

Choose contrasting lenses in-session and activate them against the sources.
Start with the irritation, not introductions or the conclusion. One voice makes
a substantive claim; another attacks its assumption, evidence, cost, or practical
consequence. The first must answer. Let realistic alternatives enter the room.

No synthesis before an exchange changes or kills a claim. A useful objection may
stay unresolved. Following brainstorm, consider preserve, reject, replace, and
hybridize; do not simply shred the strange ideas back into the obvious answer.
Do not invent consensus or falsely claim an objection was defeated.

Write `record-N.md` with the useful crossfire, the claim's before/after, what died
and why, survivors, evidence limits, and remaining tensions. Use `forced_by` or
`objected_by` only if it makes causal provenance clearer, never as decoration.

## Let the crossfire change the next move

Put changed claims beside relevant earlier decisions, rejections, or failure
modes in the exchange itself. A past answer does not win by being old: preserve
its lesson only when it fits the current evidence. If the room is flat or the
answer arrived before the exchange, say that plainly and reopen the affected work
with `rewind`; never manufacture a kill or joke to make the process look active.

Use `decision-N.json` to choose `continue` only for a tension another round can
usefully move; otherwise `finish` or `refuse`, with your reason. The runner must
not infer this for you.

## Deliver

Write `final.md` yourself and record it through the final pause. Give the useful
argument as the room: distinct contributions, the collisions that mattered, and
the judgment or residual question they earned. Let the ending follow the exchange
instead of appending a generic survivor list. For a whole-path request, account
for every material part; do not silently reduce it to one first move. Show
implementation ordering only when the user asked for that decision. Do not
substitute a link, a roll call, or a DAG completion report for the debate.
