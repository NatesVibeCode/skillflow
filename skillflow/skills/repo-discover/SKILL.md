---
name: repo-discover
description: Find existing implementations, data models, process steps, ownership evidence, and repository relationships before development; use bounded local discovery and dictionary tables to decide reuse, extend, build, or unknown.
shape: setup-execute
---

# Outcome-led repository discovery and development dictionary

Native dictionary functions expose term identities and conflicts, versioned
contract-copy ownership, and process-linked Virtual Lab scenarios and receipts.
The DAG gathers these tables and checks selected source/receipt pins before its
judgment and delivery gates. A changed native pin refuses delivery.

Use before development that could duplicate a capability or lose its data and
process contracts, and when asked where an implementation or relationship lives.
Begin with the operator's requested outcome and the checkout they selected. For
business work, state the obligation to satisfy, affected business objects and
resources, required action, accepted outcome, and evidence that would prove it.
Keep participant identity and authorization separate from the work being
coordinated. If the terms or acceptance conditions are unknown, record the gap;
do not let a repository map, harness, session, or invocation model choose the
product shape.

Then use the dictionary as a development index: it helps locate native data
models, implementations, process contracts, owners, and evidence. It is not a
canonical business-domain dictionary, policy engine, resource lock, migration
authority, or proof that a listed capability is ready. Resolve business terms
and resource ownership from their selected authoritative sources. ABAC may
decide whether a caller is eligible; the resource owner must enforce current
state, versions, capacity, and effect identity, and the owning Process defines
acceptance and recovery.

The runnable DAG gathers evidence through the existing discovery CLI and
read-only dictionary functions. Resolve resource paths from this installed skill:

```sh
python3 "<skills-root>/_shared/run.py" repo-discover "<topic>" "<session-dir>" --target "<selected-checkout>" --root "<selected-root>" --term "<literal-variant>"
```

Repeat `--root` and `--term` when the request selects additional roots or terms.
Use `--evidence-root <directory>` for explicitly selected Lab receipt directories
outside the code roots. This authorizes artifact freshness checks for that scope;
it never widens code search. Unselected external receipts stay visibly unverified.
Omit roots to search only the selected target. The DAG runs scope, map, lookup,
search, dictionary, relationships, source freshness, and packet assembly functions
automatically, with independent work in parallel and JSON artifacts plus SQLite
execution records. Treat these as bounded evidence gathering for the stated
outcome, not as an organization or architecture decision. It then pauses for
your judgment in this conversation.
The dictionary stage also gathers native versioned terms and unresolved naming
conflicts. The links stage gathers source-pinned Virtual Lab scenarios and native
receipt references for the selected processes. Scenario labels distinguish local
components, simulation, and live provider evidence; no label grants admission.

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

Include the requested outcome, searched scope/terms, snapshot time, paths/lines,
native data/process contracts, relationships, the reuse decision, and
freshness/coverage gaps. For business work, trace the contract from dictionary
terms and trusted inputs through the governing predicate, typed decision,
enforcing consumer, and accepted outcome/evidence. Preserve native repository,
resource-owner, policy, and Process authority; never turn the shared map into a
shared runtime or shared business schema.
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

## Captured inventory and evidence helpers

`repository_observe` reads an explicitly captured Agent Orient inventory; the
native `repo-discover` CLI gathers live navigation evidence. Use the installed
Tool when the requested outcome concerns that captured format, with request
examples from the `session-tools` skill. `evidence_inspect` and
`provenance_trace` can support captured reference/provenance questions. They
never select a checkout, resolve dictionary naming conflicts by assumption, or
establish that a listed implementation is ready.
