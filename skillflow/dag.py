"""Core DAG operations: nodes, edges, topological run, status."""

import subprocess
from datetime import datetime, timezone

from . import db as _db


class FlowError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Flow:
    def __init__(self, path: str):
        self.path = path
        self.conn = _db.connect(path)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- definition --------------------------------------------------------

    def add_node(self, name: str, cmd: str = "") -> int:
        if not name:
            raise FlowError("node name must not be empty")
        try:
            cur = self.conn.execute(
                "INSERT INTO nodes (name, cmd) VALUES (?, ?)", (name, cmd)
            )
        except Exception as exc:
            raise FlowError(f"cannot add node {name!r}: {exc}") from exc
        self.conn.commit()
        return cur.lastrowid

    def _node_id(self, name: str) -> int:
        row = self.conn.execute(
            "SELECT id FROM nodes WHERE name = ?", (name,)
        ).fetchone()
        if row is None:
            raise FlowError(f"unknown node {name!r}")
        return row["id"]

    def _reachable(self, start_id: int, goal_id: int) -> bool:
        seen = {start_id}
        stack = [start_id]
        while stack:
            current = stack.pop()
            if current == goal_id:
                return True
            for row in self.conn.execute(
                "SELECT to_id FROM edges WHERE from_id = ?", (current,)
            ):
                if row["to_id"] not in seen:
                    seen.add(row["to_id"])
                    stack.append(row["to_id"])
        return False

    def add_edge(self, from_name: str, to_name: str) -> None:
        from_id = self._node_id(from_name)
        to_id = self._node_id(to_name)
        if from_id == to_id:
            raise FlowError("a node cannot depend on itself")
        if self._reachable(to_id, from_id):
            raise FlowError(
                f"edge {from_name!r} -> {to_name!r} would create a cycle"
            )
        try:
            self.conn.execute(
                "INSERT INTO edges (from_id, to_id) VALUES (?, ?)",
                (from_id, to_id),
            )
        except Exception as exc:
            raise FlowError(f"cannot add edge: {exc}") from exc
        self.conn.commit()

    def nodes(self) -> list:
        return [
            dict(row)
            for row in self.conn.execute("SELECT id, name, cmd FROM nodes ORDER BY name")
        ]

    def edges(self) -> list:
        return [
            dict(row)
            for row in self.conn.execute(
                """SELECT f.name AS from_name, t.name AS to_name
                   FROM edges e
                   JOIN nodes f ON f.id = e.from_id
                   JOIN nodes t ON t.id = e.to_id
                   ORDER BY from_name, to_name"""
            )
        ]

    # -- execution ----------------------------------------------------------

    def order(self) -> list:
        nodes = {row["id"]: row for row in self.conn.execute("SELECT * FROM nodes")}
        indegree = {nid: 0 for nid in nodes}
        outgoing: dict = {nid: [] for nid in nodes}
        for row in self.conn.execute("SELECT from_id, to_id FROM edges"):
            outgoing[row["from_id"]].append(row["to_id"])
            indegree[row["to_id"]] += 1
        queue = sorted(n for n, d in indegree.items() if d == 0)
        result = []
        while queue:
            nid = queue.pop(0)
            result.append(nodes[nid])
            for nxt in sorted(outgoing[nid]):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if len(result) != len(nodes):
            raise FlowError("graph contains a cycle")
        return [dict(r) for r in result]

    def run(self) -> int:
        ordered = self.order()
        started = _now()
        cur = self.conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'running')", (started,)
        )
        run_id = cur.lastrowid
        self.conn.commit()
        overall = "ok"
        for node in ordered:
            node_started = _now()
            self.conn.execute(
                """INSERT INTO node_results
                   (run_id, node_id, status, started_at)
                   VALUES (?, ?, 'running', ?)""",
                (run_id, node["id"], node_started),
            )
            self.conn.commit()
            try:
                proc = subprocess.run(
                    node["cmd"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=3600,
                )
                status = "ok" if proc.returncode == 0 else "failed"
                output = (proc.stdout or "") + (proc.stderr or "")
                exit_code = proc.returncode
            except Exception as exc:
                status = "failed"
                output = str(exc)
                exit_code = None
            self.conn.execute(
                """UPDATE node_results
                   SET status = ?, exit_code = ?, output = ?, finished_at = ?
                   WHERE run_id = ? AND node_id = ?""",
                (status, exit_code, output, _now(), run_id, node["id"]),
            )
            self.conn.commit()
            if status != "ok":
                overall = "failed"
                break
        self.conn.execute(
            "UPDATE runs SET status = ?, finished_at = ? WHERE id = ?",
            (overall, _now(), run_id),
        )
        self.conn.commit()
        return run_id

    def status(self, run_id: int | None = None) -> dict:
        if run_id is None:
            row = self.conn.execute(
                "SELECT id FROM runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                raise FlowError("no runs yet")
            run_id = row["id"]
        run = self.conn.execute(
            "SELECT * FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        if run is None:
            raise FlowError(f"unknown run {run_id}")
        results = [
            dict(r)
            for r in self.conn.execute(
                """SELECT n.name, r.status, r.exit_code, r.output,
                          r.started_at, r.finished_at
                   FROM node_results r
                   JOIN nodes n ON n.id = r.node_id
                   WHERE r.run_id = ?
                   ORDER BY r.started_at""",
                (run_id,),
            )
        ]
        return {"run": dict(run), "nodes": results}
