"""Read-only views over a hybrid panel session directory.

The gate runner owns state transitions; this module only reports them so
agents (and MCP clients) can answer "where am I and what is next" without
parsing session files by hand.
"""

import json
from pathlib import Path


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def load_plan(session: Path) -> dict:
    plan_path = session / "checkpoints.json"
    if not plan_path.is_file():
        raise ValueError(f"not a hybrid panel session: {session}")
    return _read_json(plan_path)


def load_state(session: Path) -> dict:
    state_path = session / ".checkpoints.json"
    if not state_path.is_file():
        return {"accepted": {}, "waiting": None}
    return _read_json(state_path)


def status_summary(session: str | Path) -> dict:
    """One dict describing skill, gates, current pause, and stop state."""
    session = Path(session)
    plan = load_plan(session)
    state = load_state(session)
    stages = plan.get("stages", [])
    accepted = state.get("accepted", {})
    waiting = (state.get("waiting") or {}).get("name")
    stop = state.get("stop")
    stop_index = stop.get("index", -1) if stop else -1
    rows = []
    current = None
    for index, stage in enumerate(stages):
        name = stage.get("name", "")
        if name in accepted:
            mark = "accepted"
        elif stop and index > stop_index and name != "finalize":
            mark = "skipped"
        elif name == waiting:
            mark = "waiting"
            current = {"name": name, "artifact": stage.get("artifact"),
                       "prompt": stage.get("prompt")}
        else:
            mark = "pending"
        rows.append({"name": name, "artifact": stage.get("artifact"),
                     "state": mark})
    return {"session": str(session), "skill": plan.get("skill"),
            "prior": plan.get("prior"), "stop": stop,
            "accepted": len(accepted), "stages": len(stages),
            "waiting": current, "gates": rows}


def read_artifact(session: str | Path, name: str) -> str:
    """Read a session artifact by bare filename.

    The working copy wins; the notes/ snapshot is the fallback. Only bare
    filenames inside the session resolve; anything else refuses.
    """
    session = Path(session)
    if not name or name != Path(name).name or name.startswith("."):
        raise ValueError(f"refusing artifact path {name!r}")
    for base in (session, session / "notes"):
        candidate = base / name
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.parent != base.resolve() or not resolved.is_file():
            continue
        return resolved.read_text()
    raise ValueError(f"no such artifact in session: {name}")


def format_status(summary: dict) -> str:
    lines = [f"skill: {summary['skill']}  "
             f"accepted {summary['accepted']}/{summary['stages']}"]
    if summary.get("prior"):
        lines.append(f"prior: {summary['prior']}")
    if summary.get("stop"):
        stop = summary["stop"]
        lines.append(f"stopped: {stop['action']}: {stop['reason']}")
    waiting = summary.get("waiting")
    if waiting:
        lines.append(f"waiting: {waiting['name']} -> write {waiting['artifact']}")
    else:
        lines.append("waiting: none (session complete or untouched)")
    for gate in summary["gates"]:
        lines.append(f"  [{gate['state']}] {gate['name']} ({gate['artifact']})")
    return "\n".join(lines)
