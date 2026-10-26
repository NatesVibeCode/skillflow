# Optional discovery commands

Use current source first. These existing read-only commands help when the answer
crosses repositories or needs dictionary relationships. Set `SKILL_DIR` to this
skill's directory; `local.json` points to the existing implementations.

```sh
python3 "$SKILL_DIR/scripts/discover.py" map --json
python3 "$SKILL_DIR/scripts/discover.py" where "capability" --json
python3 "$SKILL_DIR/scripts/discover.py" search "term" --group code,tests,docs --json
python3 "$SKILL_DIR/scripts/discover.py" dictionary status
python3 "$SKILL_DIR/scripts/discover.py" dictionary coverage --root "/selected/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary freshness --root "/selected/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary route "ExactSymbol" --root "/selected/checkout" --limit 0
python3 "$SKILL_DIR/scripts/discover.py" dictionary capabilities --root "/selected/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary processes --root "/selected/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary declarations "ExactSymbol" --root "/selected/checkout"
python3 "$SKILL_DIR/scripts/discover.py" dictionary neighbors "checkout-id" --root "/selected/checkout"
```

Pass native `--root` explicitly for cross-repository map/where/search. Dictionary
commands accept repeated `--root`; without it they select the current checkout
or its descendants. Inspect reported scope, snapshot time and truncation. Narrow
or expand a query as needed; no-match results describe the searched scope only.

Follow candidates to their owning source and actual consumers. Keep participants,
business meaning and resource ownership explicit. Compare typed fields, effects
and actual handoffs before adopting behavior. The dictionary describes existing
code; it is not runtime authority, a shared business schema or proof of quality.

There are no decision or delivery checkpoints for discovery. Do not invoke the
Skillflow pause runner, create a receipt, or repair stale navigation metadata as
a prerequisite for product work.

`route` joins captured definitions to Go calls/selectors and native evidence in
those same selected checkouts. It reports current file hashes, parser diagnostics,
missing reference materialization and unresolved receiver/dynamic uses. Import
selectors retain their import locator; name matches alone are target candidates.
Embedded worker templates and runtime-selected calls still require current source
inspection. `--limit 0` removes response-row limits for this scoped route.
