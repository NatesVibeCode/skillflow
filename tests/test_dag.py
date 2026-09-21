import os
import tempfile
import unittest

from skillflow.dag import Flow, FlowError


class DagTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "test.db")
        self.flow = Flow(self.db)

    def tearDown(self):
        self.flow.close()
        self.tmp.cleanup()

    def test_add_and_show(self):
        self.flow.add_node("a", "echo a")
        self.flow.add_node("b", "echo b")
        self.flow.add_edge("a", "b")
        self.assertEqual(len(self.flow.nodes()), 2)
        self.assertEqual(
            self.flow.edges(), [{"from_name": "a", "to_name": "b"}]
        )

    def test_cycle_rejected(self):
        self.flow.add_node("a")
        self.flow.add_node("b")
        self.flow.add_edge("a", "b")
        with self.assertRaises(FlowError):
            self.flow.add_edge("b", "a")

    def test_self_edge_rejected(self):
        self.flow.add_node("a")
        with self.assertRaises(FlowError):
            self.flow.add_edge("a", "a")

    def test_unknown_node(self):
        self.flow.add_node("a")
        with self.assertRaises(FlowError):
            self.flow.add_edge("a", "missing")

    def test_run_order_and_status(self):
        seen = os.path.join(self.tmp.name, "seen.txt")
        self.flow.add_node("first", f"echo one >> {seen}")
        self.flow.add_node("second", f"echo two >> {seen}")
        self.flow.add_edge("first", "second")
        run_id = self.flow.run()
        result = self.flow.status(run_id)
        self.assertEqual(result["run"]["status"], "ok")
        self.assertEqual(
            [n["name"] for n in result["nodes"]], ["first", "second"]
        )
        with open(seen) as fh:
            self.assertEqual(fh.read().split(), ["one", "two"])

    def test_run_failure_stops_downstream(self):
        self.flow.add_node("bad", "exit 3")
        self.flow.add_node("downstream", "echo hi")
        self.flow.add_edge("bad", "downstream")
        run_id = self.flow.run()
        result = self.flow.status(run_id)
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(result["nodes"][0]["status"], "failed")
        self.assertEqual(len(result["nodes"]), 1)

    def test_status_with_no_runs(self):
        with self.assertRaises(FlowError):
            self.flow.status()

    def test_run_db_error_is_flow_error(self):
        self.flow.add_node("a", "echo hi")
        self.flow.conn.execute("DROP TABLE runs")
        with self.assertRaises(FlowError):
            self.flow.run()

    def test_status_lists_nodes_in_execution_order(self):
        self.flow.add_node("first", "echo one")
        self.flow.add_node("second", "echo two")
        self.flow.add_edge("first", "second")
        result = self.flow.status(self.flow.run())
        self.assertEqual(
            [n["name"] for n in result["nodes"]], ["first", "second"]
        )

    def test_stale_running_run_marked_interrupted(self):
        self.flow.conn.execute(
            "INSERT INTO runs (started_at, status) VALUES ('stale', 'running')"
        )
        self.flow.conn.commit()
        self.flow.add_node("a", "echo hi")
        self.flow.run()
        rows = self.flow.conn.execute(
            "SELECT status FROM runs ORDER BY id"
        ).fetchall()
        self.assertEqual([r["status"] for r in rows], ["interrupted", "ok"])

    def test_unopenable_database(self):
        bad = os.path.join(self.tmp.name, "no-such-dir", "x.db")
        with self.assertRaises(FlowError):
            Flow(bad)

    def test_duplicate_node_name_refused(self):
        self.flow.add_node("a", "echo a")
        with self.assertRaises(FlowError):
            self.flow.add_node("a", "echo other")

    def test_remove_node_cascades_edges(self):
        self.flow.add_node("a", "echo a")
        self.flow.add_node("b", "echo b")
        self.flow.add_edge("a", "b")
        removed = self.flow.remove_node("a")
        self.assertEqual(removed, {"nodes": 1, "edges": 1, "results": 0})
        self.assertEqual(self.flow.edges(), [])
        with self.assertRaises(FlowError):
            self.flow.remove_node("a")

    def test_remove_node_with_results_needs_force(self):
        self.flow.add_node("a", "echo a")
        self.flow.run()
        with self.assertRaises(FlowError):
            self.flow.remove_node("a")
        removed = self.flow.remove_node("a", force=True)
        self.assertEqual(removed["results"], 1)
        self.assertEqual(self.flow.nodes(), [])

    def test_remove_edge(self):
        self.flow.add_node("a")
        self.flow.add_node("b")
        self.flow.add_edge("a", "b")
        self.flow.remove_edge("a", "b")
        self.assertEqual(self.flow.edges(), [])
        with self.assertRaises(FlowError):
            self.flow.remove_edge("a", "b")

    def test_runs_lists_every_run(self):
        self.flow.add_node("a", "echo a")
        self.flow.run()
        self.flow.run()
        runs = self.flow.runs()
        self.assertEqual([r["id"] for r in runs], [1, 2])
        self.assertTrue(all(r["status"] == "ok" for r in runs))

    def test_diff_flags_changed_nodes(self):
        out = os.path.join(self.tmp.name, "v.txt")
        with open(out, "w") as fh:
            fh.write("one")
        self.flow.add_node("read", f"cat {out}")
        first = self.flow.run()
        with open(out, "w") as fh:
            fh.write("two")
        second = self.flow.run()
        compared = self.flow.diff(first, second)
        self.assertEqual(len(compared["nodes"]), 1)
        self.assertTrue(compared["nodes"][0]["changed"])
        same = self.flow.diff(first, first)
        self.assertFalse(any(n["changed"] for n in same["nodes"]))
        with self.assertRaises(FlowError):
            self.flow.diff(first, 99)

    def test_plan_groups_independent_nodes(self):
        self.flow.add_node("a")
        self.flow.add_node("b")
        self.flow.add_node("c")
        self.flow.add_edge("a", "c")
        self.flow.add_edge("b", "c")
        self.assertEqual(
            self.flow.plan(),
            [{"level": 0, "nodes": ["a", "b"]},
             {"level": 1, "nodes": ["c"]}],
        )

    def test_huge_output_is_capped(self):
        self.flow.add_node("loud", "python3 -c \"print('x' * 1000000)\"")
        result = self.flow.status(self.flow.run())
        stored = result["nodes"][0]["output"]
        self.assertLess(len(stored), 1000000)
        self.assertIn("[truncated:", stored)

    def test_parallel_level_overlaps(self):
        import time
        self.flow.add_node("a", "sleep 2")
        self.flow.add_node("b", "sleep 2")
        started = time.monotonic()
        result = self.flow.status(self.flow.run(jobs=2))
        elapsed = time.monotonic() - started
        self.assertEqual(result["run"]["status"], "ok")
        self.assertLess(elapsed, 3.5)
        with self.assertRaises(FlowError):
            self.flow.run(jobs=0)

    def test_parallel_failure_stops_next_level(self):
        self.flow.add_node("bad", "exit 1")
        self.flow.add_node("down", "echo hi")
        self.flow.add_edge("bad", "down")
        result = self.flow.status(self.flow.run(jobs=2))
        self.assertEqual(result["run"]["status"], "failed")
        self.assertEqual(len(result["nodes"]), 1)

    def test_run_from_executes_downstream_only(self):
        out = os.path.join(self.tmp.name, "seen.txt")
        for name in ("a", "b", "c"):
            self.flow.add_node(name, f"echo {name} >> {out}")
        self.flow.add_edge("a", "b")
        self.flow.add_edge("b", "c")
        result = self.flow.status(self.flow.run_from("b"))
        self.assertEqual(
            [n["name"] for n in result["nodes"]], ["b", "c"]
        )
        with self.assertRaises(FlowError):
            self.flow.run_from("missing")

    def test_retry_repairs_failed_run(self):
        flag = os.path.join(self.tmp.name, "fixed")
        self.flow.add_node("a", "echo a")
        self.flow.add_node("b", f"test -f {flag}")
        self.flow.add_edge("a", "b")
        first = self.flow.status(self.flow.run())
        self.assertEqual(first["run"]["status"], "failed")
        open(flag, "w").close()
        second = self.flow.status(self.flow.retry())
        self.assertEqual(second["run"]["status"], "ok")
        self.assertEqual(
            [n["name"] for n in second["nodes"]], ["b"]
        )
        with self.assertRaises(FlowError):
            self.flow.retry()
        fresh = Flow(os.path.join(self.tmp.name, "empty.db"))
        try:
            with self.assertRaises(FlowError):
                fresh.retry()
        finally:
            fresh.close()

    def test_node_timeout_kills_slow_command(self):
        self.flow.add_node("slow", "sleep 30", timeout_s=1)
        result = self.flow.status(self.flow.run())
        self.assertEqual(result["nodes"][0]["status"], "failed")
        self.assertIn("timed out", result["nodes"][0]["output"])

    def test_node_env_and_cwd(self):
        sub = os.path.join(self.tmp.name, "sub")
        os.makedirs(sub)
        self.flow.add_node("env", "echo $MARK", env={"MARK": "here"})
        self.flow.add_node("dir", "pwd", cwd=sub)
        result = self.flow.status(self.flow.run())
        by_name = {n["name"]: n for n in result["nodes"]}
        self.assertIn("here", by_name["env"]["output"])
        self.assertIn("sub", by_name["dir"]["output"])

    def test_bad_node_config_refused(self):
        for kwargs in ({"timeout_s": 0}, {"timeout_s": -1},
                       {"timeout_s": "soon"}, {"env": ["A=1"]},
                       {"cwd": ""}):
            with self.assertRaises(FlowError):
                self.flow.add_node("bad", "echo hi", **kwargs)

    def test_old_database_migrates(self):
        import sqlite3
        path = os.path.join(self.tmp.name, "old.db")
        conn = sqlite3.connect(path)
        conn.executescript(
            "CREATE TABLE nodes (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL UNIQUE, cmd TEXT NOT NULL DEFAULT '');"
            "CREATE TABLE edges (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " from_id INTEGER NOT NULL, to_id INTEGER NOT NULL);"
            "CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL);"
            "CREATE TABLE node_results (run_id INTEGER NOT NULL,"
            " node_id INTEGER NOT NULL, status TEXT NOT NULL,"
            " exit_code INTEGER, output TEXT NOT NULL DEFAULT '',"
            " started_at TEXT, finished_at TEXT,"
            " PRIMARY KEY (run_id, node_id));"
        )
        conn.commit()
        conn.close()
        flow = Flow(path)
        try:
            flow.add_node("a", "echo hi", timeout_s=10,
                          env={"A": "b"}, cwd=self.tmp.name)
            result = flow.status(flow.run())
            self.assertEqual(result["run"]["status"], "ok")
        finally:
            flow.close()


if __name__ == "__main__":
    unittest.main()
