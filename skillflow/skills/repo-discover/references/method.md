# Method

1. Preserve the directly selected development target. Read its repository
   instructions and owner boundaries. Keep same-named checkouts, worktrees,
   snapshots, and archived donors distinct by full path.
2. Map the current checkout, or explicitly selected collection roots. Use
   `map`, `where`, and literal `search` to find capabilities and old/new naming
   variants. Search code, tests, readmes, agents, decisions, docs, config, and
   skills. Default discovery search has 50 total hits and five hits per
   repository/group: narrow or split when truncated. For broad searches, use
   at least `5 × map entry count × selected group count`. A no-match result is
   bounded by the exact roots, groups, terms, and limits used.
3. Query dictionary tables for native data fields, capabilities, process inputs
   and outputs, steps, effects, failures, and repository relationships. Check
   recorded snapshot time with `dictionary status`. Query names and declaration
   paths before adding fields, functions, Nodes, Blocks, or Processes. Query
   `same-source` for exact byte duplicates; identical bytes show duplication,
   and do not establish current ownership or semantic equivalence.
4. Follow evidence to current source and repository instructions. Recorded
   fields, process descriptions, uniqueness ratings, lifecycle labels, and
   relationships are evidence with dates and scope. They do not prove runtime
   readiness, compatible contracts, a migration, or admission. Verify current
   source hashes and material contracts before acting. Missing registry cards,
   failed parsing, excluded checkouts, scan caps, and unreadable files are gaps.
5. Decide `reuse` when a current owner implementation fits; `extend` when its
   documented boundary supports the change; `build` when useful variants found
   no fitting implementation in selected scope and the target/owner are clear;
   `unknown` when identity, ownership, evidence, or scope is unresolved. Resolve
   that gap before dependent edits. Never silently switch the selected target.
6. Maintain typed dictionary records and evidence links through the owner's
   existing generation functions. Keep documentation a generated view. Describe
   native contracts faithfully; a common dictionary is a shared description,
   not a shared runtime or authority to unify incompatible repositories.
   Process maps must include inputs, outputs, exact dependencies, effects,
   failures, recovery, and evidence. Lab references point to actual definitions
   and verification receipts; diagrams alone do not admit capabilities.

## Commands

Set `SKILL_DIR` to this skill's installed directory. The dispatcher reads
`local.json` with `agent_orient` and `dictionary_directory` absolute paths, or
accepts `--config` before the command. It invokes the existing implementation;
it does not copy dictionary data or build a second query engine.

```sh
python3 "$SKILL_DIR/scripts/discover.py" map --json
python3 "$SKILL_DIR/scripts/discover.py" where "capability" --json
python3 "$SKILL_DIR/scripts/discover.py" search "term" --group code,tests,docs,readmes,agents,decisions,config,skills --json
python3 "$SKILL_DIR/scripts/discover.py" dictionary status
python3 "$SKILL_DIR/scripts/discover.py" dictionary repositories --root "/explicit/collection"
python3 "$SKILL_DIR/scripts/discover.py" dictionary models --root "/explicit/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary capabilities --root "/explicit/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary processes --root "/explicit/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary process-steps "process-id" --root "/explicit/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary declarations "ExactSymbol" --root "/explicit/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary neighbors "checkout-id" --root "/explicit/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary same-source "/explicit/source/file" --root "/explicit/collection"
python3 "$SKILL_DIR/scripts/discover.py" dictionary evidence "/explicit/source/file" --root "/explicit/checkout"
```

Pass discovery's native `--root` explicitly for cross-repository map/where/search.
Dictionary commands accept repeated `--root`; without it, they select the
current checkout or current directory's descendants. Results include scope,
snapshot provenance, and truncation. Related paths outside scope are leads for
separately authorized discovery. Rebuild the SQLite view with the owner's
`tools/build_tables.py` if missing, under the task's write authorization.

Local config paths may be absolute, use `~`, or be relative to `local.json`.
The DAG normalizes and pins its copied config. Source evidence is checked again
on resume; it cannot silently reuse an old freshness result after source edits.
Native projections retain the declared Skillflow shape in a receipt bound to
the installed entrypoint bytes. Refresh a changed projection from its source.
