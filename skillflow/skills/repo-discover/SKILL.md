---
name: repo-discover
description: Find existing implementations, data models, process steps, ownership evidence, and repository relationships before development; use bounded local discovery and dictionary tables to decide reuse, extend, build, or unknown.
shape: setup-execute
---

# Repository discovery and development dictionary

Use before development that could duplicate a capability or lose its data and
process contracts, and when asked where an implementation or relationship lives.
The runnable DAG gathers evidence through the existing discovery CLI and
read-only dictionary functions. Resolve resource paths from this installed skill:

```sh
python3 "<skills-root>/_shared/run.py" repo-discover "<topic>" "<session-dir>" --target "<selected-checkout>" --root "<selected-root>" --term "<literal-variant>"
```

Repeat `--root` and `--term` when the request selects additional roots or terms.
Omit roots to search only the selected target. The DAG runs scope, map, lookup,
search, dictionary, relationships, source freshness, and packet assembly functions
automatically, with independent work in parallel and JSON artifacts plus SQLite
execution records. It then pauses for your judgment in this conversation.

The operator's direct instruction selects the target. Discovery records describe
repositories; they never select a different target or grant execution authority.
Search the current checkout or roots explicitly selected for this task. Read
`local.json` for installed tool locations; those paths are configuration, not
permission to search every collection. If configuration or evidence is missing,
record the gap and continue only within the authorized scope.

## Decision and delivery

Read `packet.json`, `artifacts/evidence.json`, and the linked artifacts at the
decision pause. Follow [the method](references/method.md) to verify ownership and
contracts. Write `decision.json` with `target`, `decision` (`reuse`, `extend`,
`build`, or `unknown`), `reason`, `evidence` (source paths), and `gaps` (a list).
Resume using the command printed by the runner. At the final pause, write the
useful complete result in `final.md`, then resume. The DAG validates the decision
fields, retains the directly selected target, and seals artifact hashes in
`receipt.json`; it does not invent semantic ownership or readiness judgments.

Include searched scope/terms, snapshot time, paths/lines, data/process contracts,
relationships, the reuse decision, and freshness/coverage gaps. Preserve native
repository ownership and process authority.
For changes to a dictionary, update its structured source through its existing
generator; generate readable documentation from that source.

For individual queries, `scripts/discover.py` remains available. Run the DAG for
the whole discovery task. Missing tools or dictionary views produce a failed
function record; resume after restoring the same pinned inputs, or start a fresh
session for changed inputs. No provider or other agent is launched by this DAG.

Use the shared runner's `status <session-dir>` to see function failures as well
as gate state. Use `rewind <session-dir> decide` or `finalize` to reconsider a
semantic gate; the old delivery receipt is archived and the new answer gets a
new receipt. The copied config and gathered source evidence are checked before
judgment and delivery. Changed evidence requires fresh discovery.
