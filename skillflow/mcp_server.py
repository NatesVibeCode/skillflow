"""Skillflow MCP server: DAG runner + panel room selection as MCP tools.

Run with:  python -m skillflow.mcp_server
 exposure: stdio transport.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PANEL_DIR = os.path.join(REPO_ROOT, "panel")
sys.path.insert(0, PANEL_DIR)

try:
    from mcp.server.fastmcp import FastMCP  # noqa: E402
    from mcp.types import ToolAnnotations  # noqa: E402
except ImportError:
    print("error: the 'mcp' package is not installed.",
          "Install the server extra: pip install '.[mcp]'",
          file=sys.stderr)
    raise SystemExit(2)

from .dag import Flow, FlowError  # noqa: E402

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False,
                            idempotentHint=True, openWorldHint=False)
WRITE_SAFE = ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                             idempotentHint=False, openWorldHint=False)
WRITE_IDEMPOTENT = ToolAnnotations(readOnlyHint=False, destructiveHint=False,
                                   idempotentHint=True, openWorldHint=False)
EXECUTES_SHELL = ToolAnnotations(readOnlyHint=False, destructiveHint=True,
                                 idempotentHint=False, openWorldHint=False)


def _panel_file(name: str) -> str:
    path = os.path.join(PANEL_DIR, name)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"panel data missing at {path}; the panel tools need a repo "
            f"checkout (pip installs ship the engine only)")
    return path

mcp = FastMCP("skillflow")


OUTPUT_LIMIT = 2000

HINTS = [
    ("would create a cycle", "Use skillflow_show to see the current edges."),
    ("unknown node", "Use skillflow_show to list node names."),
    ("unknown run", "Call skillflow_status without a run id for the latest."),
    ("no runs yet", "Call skillflow_run first."),
    ("cannot open database", "Check the db path; use skillflow_init to create it."),
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
                       cmd: str = "") -> dict:
    """Add a node (a shell command) to the DAG."""
    try:
        with Flow(db) as flow:
            node_id = flow.add_node(name, cmd)
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


def _run_common(db: str, run: int | None, execute: bool) -> dict:
    try:
        with Flow(db) as flow:
            run_id = flow.run() if execute else run
            result = flow.status(run_id)
    except FlowError as exc:
        return _err(exc)
    result["ok"] = True
    return _trim_run(result)


@mcp.tool(annotations=EXECUTES_SHELL)
def skillflow_run(db: str = "skillflow.db") -> dict:
    """Execute the DAG in topological order and return the run record.

    Use after defining nodes and edges with skillflow_add_node /
    skillflow_add_edge. The first failing node stops downstream nodes;
    the returned record shows per-node status, exit codes, and output
    (trimmed to 2000 chars per node). Gate nodes that prompt on a
    terminal fail closed without one — a run containing an unanswered
    gate stops there, which is the correct outcome, not an error.
    """
    return _run_common(db, None, execute=True)


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
        source = _panel_file("panelists.json")
        _panel_file("seed.py")
        import seed as seed_mod
        count = seed_mod.seed(db, source)
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
    3-5 seats, near-duplicate tag sets skipped. Pass `exclude_ids` with
    earlier rooms' member ids to keep later rounds fresh. Requires
    panel_seed to have run once on this DB.
    """
    if not 3 <= size <= 5:
        return {"ok": False, "error": "--size must be 3-5"}
    try:
        _panel_file("select_room.py")
        import select_room as selector
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
             "lens": p["lens"], "score": selector.score(parsed, p)}
            for p in room
        ],
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
