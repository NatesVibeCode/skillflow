# Skillflow

A minimal SQLite-backed DAG runner. Define nodes (shell commands) and
dependency edges, then run the graph in topological order. Every run and
per-node result is recorded in a plain SQLite file — no servers, no
background services, no external dependencies beyond the Python standard
library.

## Install

```sh
pip install .
```

## Use

```sh
skillflow init
skillflow add-node fetch --cmd "curl -s https://example.com -o page.html"
skillflow add-node parse --cmd "python parse.py page.html"
skillflow add-edge fetch parse
skillflow run
skillflow status
```

Options:

- `--db PATH` (or `SKILLFLOW_DB`) selects the SQLite file. Defaults to
  `./skillflow.db`.
- `show` prints the DAG as JSON.
- `status [--run ID] [--json]` shows the latest run (or a given one).
- `run` exits nonzero if any node fails; downstream nodes do not execute
  after a failure.

## How it works

Four tables: `nodes`, `edges`, `runs`, `node_results`. Execution order is
computed with Kahn's algorithm; cycles are rejected when an edge is added
(and re-checked at run time). Node output (stdout + stderr), exit codes,
and timestamps are stored per run.

## Panel skills

Ships with four skills that run as skillflow DAGs: **debate**,
**brainstorm**, **reframe**, **review**. Each session seats its rooms from a
128-person panelist roster (semantic match, enforced diversity) and gates
every round on a person's approval.

```sh
panel/run.sh debate "ship it friday" 3 ./session1
panel/run.sh brainstorm "<goal>" [session-dir]
panel/run.sh reframe "<current frame>" [rounds] [session-dir]
panel/run.sh review "<work under review>" [session-dir]
```

Skills live in `skills/` (one `SKILL.md` each plus
`skills/_shared/`); the roster, selector, seeder, and runner live in
`panel/`. Copy a skill directory into your agent's skills folder, or install
directly if your harness supports it (`muse skills install skills/debate`).

Use a fresh session directory per run (`panel/run.sh` refuses to rebuild
into an existing one). If a run stops at a gate, fix the inputs and restart
the run in place — seeding is idempotent and selection is deterministic:

```sh
cd ./session1 && skillflow run
```

## MCP server

Everything above is also an MCP server (stdio). Eight tools: `skillflow_init`,
`skillflow_add_node`, `skillflow_add_edge`, `skillflow_show`, `skillflow_run`,
`skillflow_status`, `panel_seed`, `panel_select_room`.

```sh
pip install ".[mcp]"
python -m skillflow.mcp_server
```

Example client config (stdio):

```json
{
  "mcpServers": {
    "skillflow": {
      "command": "python3",
      "args": ["-m", "skillflow.mcp_server"],
      "cwd": "/path/to/skillflow"
    }
  }
}
```

Run the server from a repo checkout: the panel tools need `panel/` next to
the engine, and pip installs ship the engine only. (The six `skillflow_*`
tools work fine from an installed copy.)

Note: gate nodes that prompt on a terminal fail closed without one — a `run`
containing an unanswered gate stops there, by design.

## Develop

```sh
python -m unittest discover -t . -s tests -v
cd panel && python -m unittest test_select -v
```

## License

MIT. See [LICENSE](LICENSE).
