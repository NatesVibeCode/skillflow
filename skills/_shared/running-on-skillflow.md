# Prose work inside a process-enforcing DAG

The prose skill tells the session how to think. The local DAG makes the method
harder to skip: it stops at grounding, activation, and each substantive phase.
The session recovers relevant history and does all of the intellectual work in
visible prose. The DAG records order only; it never scores or validates the
quality of the discussion.

Use the launcher beside this file from any working directory:

```sh
python3 "<skills-root>/_shared/run.py" debate "<claim>" 3 "<session-dir>"
python3 "<skills-root>/_shared/run.py" brainstorm "<goal>" "<session-dir>"
python3 "<skills-root>/_shared/run.py" review "<work under review>" "<session-dir>"
python3 "<skills-root>/_shared/run.py" reframe "<current approach>" 3 "<session-dir>"
python3 "<skills-root>/_shared/run.py" resume "<session-dir>"
```

`<skills-root>` is the parent of the invoked skill directory. In a checkout,
`bash panel/run.sh ...` is equivalent. Use a fresh session directory outside
product source. Debate/reframe accept a round ceiling of 1–8 (default 3), not a
quota to fill. Brainstorm/review retain their two substantive phases.

## The same-session loop

1. Run the launcher. Read the checkpoint it reports and the exit status.
2. Do only that phase's work yourself in this conversation, using the skill's
   prose. Show the substantive phase prose in the conversation and save the
   requested artifact after the pause. Do not replace discussion with a status
   update or ask another agent to write it.
3. Run `resume` on the same directory. The runner records that artifact and
   yields at the next checkpoint. Continue without asking the user to approve
   routine pauses. Never yield the final answer merely because a file is missing.
4. At `finalize`, write `final.md` yourself. Resume once to record it, then give
   the user the answer inline. A link is supplementary, not a replacement.

A normal `PAUSE` exits 1 and returns control to you immediately. It is neither
a terminal prompt nor a need for a human reply. Do not loop or sleep waiting for
someone else to write your work. Errors are distinct: fix the local runner issue
without bypassing it or claiming the checkpoint passed. If the runner is truly
unavailable, state that pause enforcement is unavailable; you may still perform
the prose skill with explicit phase breaks and label it as an ungated run.

## Artifacts and order

- `ground.md` records the live request, sources, evidence, unknowns, and tensions.
  When history can materially change the room, recover it here with bounded
  semantic work-history recall or supplied evidence. Show why it matters, but do
  not turn it into an authority, a scorecard, or a new deliverable.
- All four then use session-authored `activation-N.md` and substantive prose.
- Debate: `record-N.md` holds crossfire; `decision-N.json` holds the session's
  reflection and continue/finish/refuse decision.
- Brainstorm: `field.md` first, then after a pause `record.md` develops it.
  Missing or unchanged tensions never skip the development phase.
- Review: `intent.md` first, then after a pause `verdict.md` holds per-intent
  deltas. The filename does not require a single overall verdict.
- Reframe: `frames-N.md` generates alternatives; a separate pause precedes
  `lineup-N.md`; then `decision-N.json` records continuation, finish, or refusal.
- Every path ends at a separate `final.md` checkpoint, including refusal.

A decision has exactly this small control shape (the reason is your judgment):

```json
{"action":"finish","reason":"The remaining objection needs new evidence, not another round."}
```

Use `continue`, `finish`, or `refuse`. Finish/refuse skip later optional rounds,
never the final answer. At the round ceiling, report unresolved issues honestly;
reaching the ceiling does not prove convergence. If evidence is absent, a
debate/reframe decision may refuse; final prose names the missing evidence
without inventing later work.

Each newly reached gate always returns before accepting work. Do not batch-write
future artifacts or final conclusions. A prefilled file must be reconsidered and
revised after its gate opens. Accepted artifacts are saved under `notes/` and
checked for later changes; corrections after acceptance use `rewind` so dependent work cannot silently
survive. The runner archives the affected work instead of deleting it:

```sh
python3 "<skills-root>/_shared/run.py" rewind "<session-dir>" ground
```

Then resume to reopen the checkpoint. Use manual rewind when new evidence, a user
correction, or recalled history changes an earlier phase. You may revise the
currently open artifact freely before resuming.

The DB and checkpoint receipts show sequence, not whether the reasoning was good.
The full prose remains the user-facing work. The final output is the complete
useful room, not a list reporting what the room did.

Old session databases keep their original graph. Resume them with their original
`skillflow run`, or start a fresh hybrid session using the old work as evidence.
The separate `add-skill` authoring workflow still uses its legacy graph.
