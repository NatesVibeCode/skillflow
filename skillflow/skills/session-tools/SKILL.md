---
name: session-tools
description: Use installed sealed tools to inspect or compare local evidence, retrieve exact source bytes, trace recorded provenance, assess patches, inspect captured factory diagnostics, or rehearse supported failure specimens.
shape: prose
---

# Session tools

Use a matching existing Tool to deliver the requested scoped report. Each Tool
runs a complete Forge-built Process: source acquisition, exact reference
binding, reporting, a second capture, and currentness checks. The Process owns
these stages. This guide supplies selection and inputs; it creates no new
runtime workflow, permission, factory admission, or model loop.

## Select the supported outcome

| Need | Tool | Input boundary |
|---|---|---|
| Inspect captured evidence | `evidence_inspect` | Exact local source records; native Mdview captures when supplied |
| Retrieve source bytes | `evidence_source` | Captured source reference and byte window; optional native Mdview retrieval record |
| Compare evidence | `evidence_compare` | Declared source/dependency relationships; proof validity remains with its owner |
| Trace recorded work | `provenance_trace` | Semantic-work-history operation projections; current producers cover Codex/OpenCode |
| Assess a patch | `patch_assess` | Explicit source, patch and required checks; candidate stays in memory |
| Read repository inventory | `repository_observe` | Captured Agent Orient inventory; use its discovery CLI for live navigation |
| Profile recorded AOA work | `work_trace` | AOA/harness-sdk spans and supported OE command records |
| Inspect composition | `composition_inspect` | Captured native Forge diagnostics |
| Inspect factory readiness records | `factory_preflight` | Captured native Forge checks; the native factory owns live decisions |
| Prepare/replay a failure specimen | `specimen_prepare`, `specimen_replay` | Supported deterministic Lab scenarios; rehearsal confers no admission |

General sessions normally expose the first six tools. AOA's session profile
adds `work_trace`. Factory authoring/release sessions may select the final four.
Use the current native menu as the availability source; installing instructions
never enables a Tool or widens workspace access.

## Call and interpret

Read only the selected operation's example in
[request examples](references/requests.md). Supply `path`, `patterns`,
`include_excluded`, and the exact operation-specific JSON string `request_json`.
Bind source paths to the already-selected workspace, with an explicit scope ID,
source IDs, owners and evidence categories. These labels are assertions and
correlation fields, not authenticated identities. Keep the requested read scope
explicit. Include optional expected hashes when the task supplies authoritative
pins; do not invent them.

Invoke the matching native Tool. If the CLI is the configured surface, inspect
`session-tools --list` or the selected `--profile factory|aoa`, then pass the JSON
input on stdin with `--operation TOOL --workspace SELECTED_DIRECTORY`.
A missing operation or unsupported record format remains an explicit gap; use
the owner's native producer where the task authorizes it.

Read the returned `report_json`, its exact references, full captured read set,
missing/unchecked coverage, and second-capture currentness. `stale` or
`unchecked` does not prove current absence or readiness. Keep conversation,
local checks, factory proof, execution receipts and Lab rehearsal distinct.
Retain the original receipt reference; retrieve retained output pages through
the native result reader before claiming complete output. A known refusal
remains a refusal. An uncertain dispatched outcome requires inspection of its
original receipt rather than an automatic resend.

Explain the requested result and its coverage limits. Compare calls, bytes or
time only across equivalent answer coverage and receipt semantics. Discovery,
local execution and simulated rehearsal do not confer owner verification.
