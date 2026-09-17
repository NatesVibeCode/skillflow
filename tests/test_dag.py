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


if __name__ == "__main__":
    unittest.main()
