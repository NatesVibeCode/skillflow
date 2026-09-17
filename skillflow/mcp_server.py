"""Skillflow MCP server: DAG runner + panel room selection as MCP tools.

Run with:  python -m skillflow.mcp_server
 exposure: stdio transport.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "panel"))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from .dag import Flow, FlowError  # noqa: E402

mcp = FastMCP("skillflow")


def _err(exc: Exception) -> dict:
    return {"ok": False, "error": str(exc)}


@mcp.tool()
def skillflow_init(db: str = "skillflow.db") -> dict:
    """Create a skillflow SQLite database (idempotent)."""
    try:
        with Flow(db):
            pass
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "db": db}


@mcp.tool()
def skillflow_add_node(db: str = "skillflow.db", name: str = "",
                       cmd: str = "") -> dict:
    """Add a node (a shell command) to the DAG."""
    try:
        with Flow(db) as flow:
            node_id = flow.add_node(name, cmd)
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "id": node_id, "name": name}


@mcp.tool()
def skillflow_add_edge(db: str = "skillflow.db", from_node: str = "",
                       to_node: str = "") -> dict:
    """Add a dependency edge (from_node runs before to_node). Rejects cycles."""
    try:
        with Flow(db) as flow:
            flow.add_edge(from_node, to_node)
    except FlowError as exc:
        return _err(exc)
    return {"ok": True, "from": from_node, "to": to_node}


@mcp.tool()
def skillflow_show(db: str = "skillflow.db") -> dict:
    """Show the DAG's nodes and edges."""
    with Flow(db) as flow:
        return {"ok": True, "nodes": flow.nodes(), "edges": flow.edges()}


@mcp.tool()
def skillflow_run(db: str = "skillflow.db") -> dict:
    """Execute the DAG in topological order. First failure stops downstream.
    Gate nodes needing a terminal fail closed without one."""
    try:
        with Flow(db) as flow:
            run_id = flow.run()
            result = flow.status(run_id)
    except FlowError as exc:
        return _err(exc)
    result["ok"] = True
    return result


@mcp.tool()
def skillflow_status(db: str = "skillflow.db", run: int | None = None) -> dict:
    """Show the latest run (or the given run id) with per-node results."""
    try:
        with Flow(db) as flow:
            result = flow.status(run)
    except FlowError as exc:
        return _err(exc)
    result["ok"] = True
    return result


@mcp.tool()
def panel_seed(db: str = "skillflow.db") -> dict:
    """Seed the panelists table in a session DB. Run once before selecting."""
    import seed as seed_mod

    try:
        count = seed_mod.seed(db, os.path.join(REPO_ROOT, "panel",
                                               "panelists.json"))
    except Exception as exc:  # noqa: BLE001 - surfaced as tool error
        return _err(exc)
    return {"ok": True, "panelists": count, "db": db}


@mcp.tool()
def panel_select_room(db: str = "skillflow.db", tensions: str = "",
                      size: int = 4, exclude_ids: list[str] | None = None) -> dict:
    """Seat a panel room: semantic match on comma-separated tensions with
    enforced diversity (one per family, 3-5 seats). Optionally excludes ids."""
    import select_room as selector

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
             "lens": p["lens"], "score": selector.score(parsed, p)}
            for p in room
        ],
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
