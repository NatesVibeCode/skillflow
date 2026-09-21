# Skillflow

A minimal SQLite-backed DAG runner. Define nodes (shell commands) and
dependency edges, then run the graph in topological order. Every run and
per-node result is recorded in a plain SQLite file — no servers, no
background services, no external dependencies beyond the Python standard
library.

## Install
Requires Python 3.10+.

```sh
pip install skill-dag
# with the MCP server:
pip install "skill-dag[mcp]"
```

Or from a checkout (needed for the panel skills and `panel/run.sh`):

```sh
pip install .
pip install ".[mcp]"
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

- `--db PATH` (before the subcommand, e.g. `skillflow --db demo.db run`)
  or `SKILLFLOW_DB` selects the SQLite file. Defaults to `./skillflow.db`.
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

Debate, brainstorm, review, and reframe run in the active conversation. Their
prose methods do the intellectual work; a local skillflow DAG enforces the order
and makes the session pause before moving on. Nothing launches another model.

- **Debate:** ground → activate → crossfire → continue/finish → final.
- **Brainstorm:** ground → activate → divergent field → activate → develop field →
  final.
- **Review:** ground → activate → intent → activate → evidence/deltas → final.
- **Reframe:** ground → activate → stronger-shape field → lineup → continue/finish
  → final. Generation and lineup have separate pauses.

The session selects and activates lenses from the roster, shows the prose in the
conversation, and authors every result. The DAG does not select the room, extract
semantic tensions, decide whether an argument is good, or synthesize the answer.
When prior decisions, corrections, rejections, or failures matter, the active
session uses bounded semantic work-history recall during grounding. The current
instruction and live sources govern. `rewind` archives affected artifacts and
invalidates their dependent checkpoints when later evidence changes an earlier
phase. A debate/reframe refusal still requires an honest final answer.

```sh
bash panel/run.sh debate "ship it friday" 3 /tmp/my-debate
# PAUSE ground: do the grounding in the current conversation; write ground.md.
bash panel/run.sh resume /tmp/my-debate
# PAUSE activate-1: perform that phase, save it, then resume again.
```

Each new checkpoint returns control before accepting its artifact, even if a file
was prefilled. Exit 1 with `PAUSE` means the current session should do the named
work and resume, not ask a human to fill a file or approve the next phase. Do not
batch-author future phases. `final.md` is session-authored, never a machine
concatenation. The receipts prove sequence, not quality. The final output is the
complete useful room, not a checklist of its conclusions.

Brainstorm/review have two mandatory phases. Debate/reframe accept a 1–8 round
ceiling (default 3); the session decides whether further rounds are worthwhile.
Full method and recovery instructions are in
[the shared protocol](skills/_shared/running-on-skillflow.md).

Install the four skills **with their shared prose and launcher**:

```sh
python3 scripts/install_panel_skills.py --skills-dir ~/.codex/skills
# Another local skill root can be passed instead, or with another --skills-dir.
```

The installed launcher resolves the checkout from a local location file, so it
works from any repo. Reinstall if the checkout moves. No harness settings, other
skills, or authentication are modified. Copying a lone SKILL.md is insufficient.

Existing session DBs retain their graphs and can still use `skillflow run` from
that session directory. `add-skill` remains a separate authoring workflow on its
legacy graph. The selector and seed tools remain available for explicit standalone
use and old sessions; the four conversational skills no longer depend on them.

## MCP server

Everything above is also an MCP server (stdio). Eight tools: `skillflow_init`,
`skillflow_add_node`, `skillflow_add_edge`, `skillflow_show`, `skillflow_run`,
`skillflow_status`, `panel_seed`, `panel_select_room`.

```sh
pip install "skill-dag[mcp]"
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
working.

## Develop

```sh
python -m unittest discover -t . -s tests -v
cd panel && python -m unittest test_select -v
```

## License

MIT. See [LICENSE](LICENSE).
