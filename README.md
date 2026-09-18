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

Ships with five skills that run as skillflow DAGs: **debate**,
**brainstorm**, **reframe**, **review**, **add-skill**.
Each session seats its rooms from a
128-person panelist roster (semantic match, enforced diversity), stores each
round's response, and writes the final section.

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

One session runs the whole DAG and authors every response — there is no
terminal prompt and no handoff to another session. A `round-N` node is a
machine-checked stage boundary: it stores the response you wrote for that
round in `notes/round-N.md` and on the node result, and the run stops with
the round's instruction when that response is missing. Write it and rerun;
`finalize` then writes `final.md`, the final section with every stored
response.

Use a fresh session directory per run (`panel/run.sh` refuses to rebuild
into an existing one). After a stopped round, write the response and restart
the run in place — seeding is idempotent and selection is deterministic:

```sh
cd ./session1 && skillflow run
```

Do not pipe the runner through `tail` or similar: that hides a stopped round
and its nonzero exit code.

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

Note: panel round nodes never prompt. A round with no response stops the run
at that stage boundary — a `run` containing an unwritten round stops there,
by design, and resumes when the response is written.

Trust boundary: this server executes arbitrary shell commands from the DAGs
you define (`skillflow_run` is annotated destructive for exactly that
reason). Run it locally, for your own agents only — do not expose it to
untrusted clients or networks.

### Client wiring: Codex + Muse

Codex (`~/.codex/config.toml`, TOML):

```toml
[mcp_servers.skillflow]
command = "python3"
args = ["-m", "skillflow.mcp_server"]
cwd = "/path/to/skillflow"
```

Muse (`~/.config/muse/settings.json`, JSON under `mcpServers`):

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

Point `cwd` at a repo checkout (panel tools need `panel/` beside the
engine), or `pip install` the package and drop `cwd` for engine-only use.
Muse documents streamable-HTTP entries; the stdio entry above is confirmed
live before relying on it.

## Develop

```sh
python -m unittest discover -t . -s tests -v
cd panel && python -m unittest test_select -v
```

## License

MIT. See [LICENSE](LICENSE).
