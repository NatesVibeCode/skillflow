"""Skillflow MCP server: DAG runner + panel room selection as MCP tools.

Run with:  python -m skillflow.mcp_server
 exposure: stdio transport.
"""

import sys
from importlib import resources

try:
    from mcp.server.fastmcp import FastMCP  # noqa: E402
    from mcp.types import ToolAnnotations  # noqa: E402
except ImportError:
    print("error: the 'mcp' package is not installed.",
          "Install the server extra: pip install 'skill-dag[mcp]',",
          file=sys.stderr)
    raise SystemExit(2)

from .dag import Flow, FlowError  # noqa: E402
from .panel import seed as seed_mod  # noqa: E402
from .panel import select_room as selector  # noqa: E402
from .session import read_artifact, status_summary  # noqa: E402

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                            idempotentHint=True, openWorldHint=False)
WRITE_SAFE = ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                             idempotentHint=False, openWorldHint=False)
WRITE_IDEMPOTENT = ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                                   idempotentHint=True, openWorldHint=False)
EXECUTES_SHELL = ToolAnnotations(readOnlyHint=False, destructiveHint=True,
                                 idempotentHint=False, openWorldHint=False)


def _panelists_source():
    """Roster data shipped in the wheel; works installed or in checkout."""
    return resources.files("skillflow.panel").joinpath("panelists.json")


mcp = FastMCP("skillflow")


OUTPUT_LIMIT = 2000

HINTS = [
    ("would create a cycle", "Use skillflow_show to see the current edges."),
    ("unknown node", "Use skillflow_show to list node names."),
    ("unknown run", "Call skillflow_status without a run id for the latest."),
    ("no runs yet", "Call skillflow_run first."),
    ("cannot open database", "Check the db path; use skillflow_init to create it."),
    ("recorded results", "Pass force=true to delete the node with its history."),
    ("no edge", "Use skillflow_show to list current edges."),
]


def _err(exc: Exception) -> dict:
    message = str(exc)
    for needle, hint in HINTS:
        if needle in message:
            return {"ok": False, "error": message, "hint": hint}
    return {"ok": False, "error": message}


def _trim_run(result: dict) -> dict:
    for node in result.get("nodes", []):
        output = node.get("output") or ""
        if len(output) > OUTPUT_LIMIT:
            node["output"] = output[:OUTPUT_LIMIT]
            node["truncated"] = True
    return result


@mcp.tool(annotations=WRITE_IDEMPOTENT)
def skillflow_init(db: str = "skillflow.db") -> dict:
    """Create a skillflow SQLite database (idempotent)."""
    try:
        with Flow(db):
            pass
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "db": db}


@mcp.tool(annotations=WRITE_SAFE)
def skillflow_add_node(db: str = "skillflow.db", name: str = "",
                       cmd: str = "", timeout_s: float | None = None,
                       env: dict | None = None,
                       cwd: str | None = None) -> dict:
    """Add a node (a shell command) to the DAG.

    timeout_s kills a slow command, env adds environment variables, and
    cwd sets the working directory. All three are optional.
    """
    try:
        with Flow(db) as flow:
            node_id = flow.add_node(name, cmd, timeout_s=timeout_s,
                                    env=env, cwd=cwd)
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "id": node_id, "name": name}


@mcp.tool(annotations=WRITE_SAFE)
def skillflow_add_edge(db: str = "skillflow.db", from_node: str = "",
                       to_node: str = "") -> dict:
    """Add a dependency edge (from_node runs before to_node). Rejects cycles."""
    try:
        with Flow(db) as flow:
            flow.add_edge(from_node, to_node)
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "from": from_node, "to": to_node}


@mcp.tool(annotations=READ_ONLY)
def skillflow_show(db: str = "skillflow.db") -> dict:
    """Show the DAG's nodes and edges."""
    with Flow(db) as flow:
        return {"ok": True, "nodes": flow.nodes(), "edges": flow.edges()}


@mcp.tool(annotations=WRITE_SAFE)
def skillflow_remove_node(db: str = "skillflow.db", name: str = "",
                          force: bool = False) -> dict:
    """Delete a node and its edges. Refuses when results exist unless force."""
    try:
        with Flow(db) as flow:
            removed = flow.remove_node(name, force)
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "name": name, **removed}


@mcp.tool(annotations=WRITE_SAFE)
def skillflow_remove_edge(db: str = "skillflow.db", from_node: str = "",
                          to_node: str = "") -> dict:
    """Delete one edge (from_node runs before to_node)."""
    try:
        with Flow(db) as flow:
            flow.remove_edge(from_node, to_node)
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "from": from_node, "to": to_node}


@mcp.tool(annotations=READ_ONLY)
def skillflow_runs(db: str = "skillflow.db") -> dict:
    """List recorded runs with per-run node counts."""
    with Flow(db) as flow:
        return {"ok": True, "runs": flow.runs()}


def _run_common(db: str, run: int | None, execute: bool,
                jobs: int = 1, from_node: str | None = None,
                retry: bool = False) -> dict:
    try:
        with Flow(db) as flow:
            if not execute:
                run_id = run
            elif retry:
                run_id = flow.retry(jobs)
            else:
                run_id = flow.run(jobs, from_node)
            result = flow.status(run_id)
    except FlowError as exc:
        return _err(exc)
    result["ok"] = True
    return _trim_run(result)


@mcp.tool(annotations=EXECUTES_SHELL)
def skillflow_run(db: str = "skillflow.db", jobs: int = 1,
                  from_node: str | None = None,
                  retry: bool = False) -> dict:
    """Execute the DAG in topological order and return the run record.

    Use after defining nodes and edges with skillflow_add_node /
    skillflow_add_edge. The first failing node stops downstream nodes;
    the returned record shows per-node status, exit codes, and output
    (trimmed to 2000 chars per node). Gate nodes that prompt on a
    terminal fail closed without one — a run containing an unanswered
    gate stops there, which is the correct outcome, not an error.
    jobs runs independent nodes concurrently; from_node resumes from one
    node downstream; retry re-runs from the latest run's first failure.
    """
    return _run_common(db, None, execute=True, jobs=jobs,
                       from_node=from_node, retry=retry)


@mcp.tool(annotations=READ_ONLY)
def skillflow_status(db: str = "skillflow.db", run: int | None = None) -> dict:
    """Show the latest run, or the given run id, with per-node results.

    Use to inspect a previous run without executing anything. Omit `run`
    for the latest. Returns run status plus each executed node's status,
    exit code, and trimmed output.
    """
    return _run_common(db, run, execute=False)


@mcp.tool(annotations=WRITE_IDEMPOTENT)
def panel_seed(db: str = "skillflow.db") -> dict:
    """Seed the panelists table in a session DB. Run once before selecting."""
    try:
        with resources.as_file(_panelists_source()) as source:
            count = seed_mod.seed(db, str(source))
    except Exception as exc:  # noqa: BLE001 - surfaced as tool error
        return _err(exc)
    return {"ok": True, "panelists": count, "db": db}


@mcp.tool(annotations=READ_ONLY)
def panel_select_room(db: str = "skillflow.db", tensions: str = "",
                      size: int = 4, exclude_ids: list[str] | None = None) -> dict:
    """Seat a panel room from the 128-person roster in the session DB.

    `tensions` is comma-separated situation topics (e.g.
    "risk,measurement"); panelists are ranked by token overlap with their
    tags, lens, and attributes, then diversity is enforced: one per family,
    3-5 seats, near-duplicate tag sets skipped. Score ties rotate toward
    rarely-seated panelists (see panel_record_seating). Pass `exclude_ids`
    with earlier rooms' member ids to keep later rounds fresh. Requires
    panel_seed to have run once on this DB.
    """
    if not 3 <= size <= 5:
        return {"ok": False, "error": "--size must be 3-5"}
    try:
        panelists = selector.load_panelists(db)
    except Exception as exc:  # noqa: BLE001 - surfaced as tool error
        return {"ok": False,
                "error": f"cannot load panelists (run panel_seed?): {exc}"}
    parsed = [t.strip() for t in tensions.split(",") if t.strip()]
    room = selector.select(panelists, parsed, size, set(exclude_ids or ()))
    return {
        "ok": True,
        "tensions": parsed,
        "room": [
            {"name": p["name"], "id": p["id"], "family": p["family"],
             "lens": p["lens"], "score": selector.score(parsed, p),
             "seated": p.get("seated", 0)}
            for p in room
        ],
    }


@mcp.tool(annotations=WRITE_SAFE)
def panel_record_seating(db: str = "skillflow.db",
                         ids: list[str] | None = None) -> dict:
    """Remember seated panelist ids so future rooms rotate to fresh voices."""
    try:
        count = selector.record_seating(db, list(ids or ()))
    except Exception as exc:  # noqa: BLE001 - surfaced as tool error
        return _err(exc)
    return {"ok": True, "recorded": count, "db": db}


@mcp.tool(annotations=READ_ONLY)
def skillflow_session_status(directory: str = "") -> dict:
    """Show a panel session's skill, gates, current pause, and stop state.

    Read-only: advancing the session still goes through the run.py
    launcher in the session's conversation.
    """
    try:
        summary = status_summary(directory)
    except Exception as exc:  # noqa: BLE001 - surfaced as tool error
        return _err(exc)
    summary["ok"] = True
    return summary


@mcp.tool(annotations=READ_ONLY)
def skillflow_session_artifact(directory: str = "",
                               name: str = "") -> dict:
    """Read one session artifact by bare filename (working copy first)."""
    try:
        text = read_artifact(directory, name)
    except Exception as exc:  # noqa: BLE001 - surfaced as tool error
        return _err(exc)
    return {"ok": True, "name": name, "text": text}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
