"""Core DAG operations: nodes, edges, topological run, status."""

import hashlib
import json
import os
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import db as _db

#: Maximum stored output per node result. Full fidelity is the caller's job
#: (files); the database keeps enough to diagnose a failure.
OUTPUT_STORE_LIMIT = 256 * 1024


class FlowError(Exception):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _store_output(text: str) -> str:
    if len(text) <= OUTPUT_STORE_LIMIT:
        return text
    return (
        text[:OUTPUT_STORE_LIMIT]
        + f"\n[truncated: showing first {OUTPUT_STORE_LIMIT} "
        + f"of {len(text)} chars]"
    )


class Flow:
    def __init__(self, path: str):
        self.path = path
        try:
            self.conn = _db.connect(path)
        except (sqlite3.Error, OSError) as exc:
            raise FlowError(f"cannot open database {path!r}: {exc}") from exc

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- definition --------------------------------------------------------

    def add_node(self, name: str, cmd: str = "", timeout_s=None,
                 env=None, cwd: str | None = None) -> int:
        if not name:
            raise FlowError("node name must not be empty")
        if timeout_s is not None and (
                isinstance(timeout_s, bool)
                or not isinstance(timeout_s, (int, float))
                or timeout_s <= 0):
            raise FlowError("timeout_s must be a positive number of seconds")
        if env is not None and (
                not isinstance(env, dict)
                or not all(isinstance(k, str) and isinstance(v, str)
                           for k, v in env.items())):
            raise FlowError("env must be a dict of string to string")
        if cwd is not None and not cwd:
            raise FlowError("cwd must not be empty")
        try:
            cur = self.conn.execute(
                "INSERT INTO nodes (name, cmd, timeout_s, env, cwd) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, cmd, timeout_s,
                 json.dumps(env) if env is not None else None, cwd),
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

    def remove_node(self, name: str, force: bool = False) -> dict:
        node_id = self._node_id(name)
        recorded = self.conn.execute(
            "SELECT COUNT(*) AS n FROM node_results WHERE node_id = ?",
            (node_id,),
        ).fetchone()["n"]
        if recorded and not force:
            raise FlowError(
                f"node {name!r} has {recorded} recorded results; "
                "pass force=True to delete it with its history"
            )
        edges = self.conn.execute(
            "SELECT COUNT(*) AS n FROM edges "
            "WHERE from_id = ? OR to_id = ?",
            (node_id, node_id),
        ).fetchone()["n"]
        self.conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        self.conn.commit()
        return {"nodes": 1, "edges": edges, "results": recorded}

    def remove_edge(self, from_name: str, to_name: str) -> None:
        from_id = self._node_id(from_name)
        to_id = self._node_id(to_name)
        cur = self.conn.execute(
            "DELETE FROM edges WHERE from_id = ? AND to_id = ?",
            (from_id, to_id),
        )
        self.conn.commit()
        if cur.rowcount == 0:
            raise FlowError(f"no edge {from_name!r} -> {to_name!r}")

    def nodes(self) -> list:
        out = []
        for row in self.conn.execute(
                "SELECT id, name, cmd, timeout_s, env, cwd FROM nodes "
                "ORDER BY name"):
            node = dict(row)
            node["env"] = json.loads(node["env"]) if node["env"] else None
            out.append(node)
        return out

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

    DEFAULT_TIMEOUT_S = 3600

    @staticmethod
    def _execute_node(node: dict):
        """Run one node's command. Pure compute; touches no database."""
        environment = None
        if node.get("env"):
            environment = dict(os.environ)
            environment.update(json.loads(node["env"])
                               if isinstance(node["env"], str)
                               else node["env"])
        try:
            proc = subprocess.run(
                node["cmd"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=node.get("timeout_s") or Flow.DEFAULT_TIMEOUT_S,
                env=environment,
                cwd=node.get("cwd") or None,
            )
            status = "ok" if proc.returncode == 0 else "failed"
            output = _store_output((proc.stdout or "") + (proc.stderr or ""))
            return status, output, proc.returncode
        except Exception as exc:
            return "failed", str(exc), None

    def _begin_run(self) -> int:
        started = _now()
        # Runs left behind by a killed process never finish on their own;
        # mark them interrupted so they stop masquerading as the latest run.
        self.conn.execute(
            "UPDATE runs SET status = 'interrupted', finished_at = ? "
            "WHERE status = 'running'",
            (started,),
        )
        self.conn.execute(
            """UPDATE node_results SET status = 'interrupted', finished_at = ?
               WHERE status = 'running'""",
            (started,),
        )
        self.conn.commit()
        cur = self.conn.execute(
            "INSERT INTO runs (started_at, status) VALUES (?, 'running')", (started,)
        )
        run_id = cur.lastrowid
        self.conn.commit()
        return run_id

    def _finish_run(self, run_id: int, overall: str) -> None:
        self.conn.execute(
            "UPDATE runs SET status = ?, finished_at = ? WHERE id = ?",
            (overall, _now(), run_id),
        )
        self.conn.commit()

    def _record_running(self, run_id: int, node_id: int) -> None:
        self.conn.execute(
            """INSERT INTO node_results
               (run_id, node_id, status, started_at)
               VALUES (?, ?, 'running', ?)""",
            (run_id, node_id, _now()),
        )
        self.conn.commit()

    def _record_done(self, run_id: int, node_id: int, status: str,
                     output: str, exit_code) -> None:
        self.conn.execute(
            """UPDATE node_results
               SET status = ?, exit_code = ?, output = ?, finished_at = ?
               WHERE run_id = ? AND node_id = ?""",
            (status, exit_code, output, _now(), run_id, node_id),
        )
        self.conn.commit()

    def run(self, jobs: int = 1, from_node: str | None = None) -> int:
        if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1:
            raise FlowError("jobs must be a positive integer")
        try:
            if from_node is not None:
                return self.run_from(from_node, jobs)
            if jobs == 1:
                return self._run_ordered(self.order())
            levels = self.plan()
            by_name = {n["name"]: n for n in self.order()}
            return self._run_levels(
                [[by_name[name] for name in level["nodes"]]
                 for level in levels], jobs)
        except sqlite3.Error as exc:
            raise FlowError(f"database is busy or locked: {exc}") from exc

    def run_from(self, name: str, jobs: int = 1) -> int:
        """Run a node and everything downstream as a fresh run."""
        ordered = self.order()
        ids = {n["name"] for n in ordered}
        if name not in ids:
            raise FlowError(f"unknown node {name!r}")
        downstream = {name}
        changed = True
        edges = [(e["from_name"], e["to_name"]) for e in self.edges()]
        while changed:
            changed = False
            for src, dst in edges:
                if src in downstream and dst not in downstream:
                    downstream.add(dst)
                    changed = True
        by_name = {n["name"]: n for n in ordered}
        subset = [[by_name[nm] for nm in level["nodes"]
                   if nm in downstream]
                  for level in self.plan()]
        if jobs == 1:
            try:
                return self._run_ordered(
                    [n for level in subset for n in level])
            except sqlite3.Error as exc:
                raise FlowError(f"database is busy or locked: {exc}") from exc
        try:
            return self._run_levels(subset, jobs)
        except sqlite3.Error as exc:
            raise FlowError(f"database is busy or locked: {exc}") from exc

    def retry(self, jobs: int = 1) -> int:
        """Re-run from the first non-ok node of the latest run."""
        try:
            latest = self.status(None)
        except FlowError as exc:
            raise FlowError(f"nothing to retry: {exc}") from exc
        if latest["run"]["status"] == "ok":
            raise FlowError("latest run already ok; nothing to retry")
        for node in latest["nodes"]:
            if node["status"] != "ok":
                return self.run_from(node["name"], jobs)
        raise FlowError("latest run has no recorded nodes")

    def _run_ordered(self, ordered: list) -> int:
        run_id = self._begin_run()
        overall = "ok"
        for node in ordered:
            self._record_running(run_id, node["id"])
            status, output, exit_code = self._execute_node(node)
            self._record_done(run_id, node["id"], status, output, exit_code)
            if status != "ok":
                overall = "failed"
                break
        self._finish_run(run_id, overall)
        return run_id

    def _run_levels(self, levels: list, jobs: int) -> int:
        run_id = self._begin_run()
        overall = "ok"
        for level in levels:
            if not level:
                continue
            for node in level:
                self._record_running(run_id, node["id"])
            with ThreadPoolExecutor(max_workers=min(jobs, len(level))) as pool:
                outcomes = list(pool.map(self._execute_node, level))
            for node, (status, output, exit_code) in zip(level, outcomes):
                self._record_done(run_id, node["id"], status, output,
                                  exit_code)
            if any(status != "ok" for status, _, _ in outcomes):
                overall = "failed"
                break
        self._finish_run(run_id, overall)
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
                   ORDER BY r.rowid""",
                (run_id,),
            )
        ]
        return {"run": dict(run), "nodes": results}

    def runs(self) -> list:
        return [
            dict(row)
            for row in self.conn.execute(
                """SELECT r.id, r.started_at, r.finished_at, r.status,
                          COUNT(nr.node_id) AS nodes,
                          SUM(nr.status = 'ok') AS ok,
                          SUM(nr.status = 'failed') AS failed
                   FROM runs r
                   LEFT JOIN node_results nr ON nr.run_id = r.id
                   GROUP BY r.id
                   ORDER BY r.id"""
            )
        ]

    def diff(self, run_a: int, run_b: int) -> dict:
        records = {}
        for run_id in (run_a, run_b):
            try:
                records[run_id] = self.status(run_id)["nodes"]
            except FlowError as exc:
                raise FlowError(f"cannot diff: {exc}") from exc
        by_name = {}
        for run_id, nodes in records.items():
            for node in nodes:
                entry = by_name.setdefault(node["name"], {})
                entry[run_id] = {
                    "status": node["status"],
                    "exit_code": node["exit_code"],
                    "output_digest": hashlib.sha256(
                        (node["output"] or "").encode("utf-8")
                    ).hexdigest(),
                }
        compared = []
        for name in sorted(by_name):
            sides = by_name[name]
            compared.append({
                "name": name,
                "a": sides.get(run_a),
                "b": sides.get(run_b),
                "changed": sides.get(run_a) != sides.get(run_b),
            })
        return {"a": run_a, "b": run_b, "nodes": compared}

    def plan(self) -> list:
        """Execution levels: nodes in one level share no dependency."""
        nodes = {row["id"]: row["name"]
                 for row in self.conn.execute("SELECT id, name FROM nodes")}
        indegree = {nid: 0 for nid in nodes}
        outgoing: dict = {nid: [] for nid in nodes}
        for row in self.conn.execute("SELECT from_id, to_id FROM edges"):
            outgoing[row["from_id"]].append(row["to_id"])
            indegree[row["to_id"]] += 1
        level_of = {}
        queue = sorted(n for n, d in indegree.items() if d == 0)
        for nid in queue:
            level_of[nid] = 0
        while queue:
            nid = queue.pop(0)
            for nxt in sorted(outgoing[nid]):
                level_of[nxt] = max(level_of.get(nxt, 0), level_of[nid] + 1)
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if len(level_of) != len(nodes):
            raise FlowError("graph contains a cycle")
        levels: dict = {}
        for nid, level in level_of.items():
            levels.setdefault(level, []).append(nodes[nid])
        return [{"level": level, "nodes": sorted(names)}
                for level, names in sorted(levels.items())]
