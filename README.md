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

## Develop

```sh
python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
