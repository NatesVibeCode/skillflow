import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER = os.path.join(ROOT, "panel", "legacy-run.sh")

READBACK = """## Validity Readback

- collision_that_changed_answer: the exchange that mutated the answer
- claim_or_option_killed: what died and why
- persona_flattening_check: why voices could not be job labels
- giggle_or_wince_line: the line that landed
- survivor_provenance: where the objection changed the survivor
"""


class PanelRunnerTest(unittest.TestCase):
    """The panel DAG must never block on a terminal prompt."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = os.path.join(self.tmp.name, "session1")
        self.env = dict(
            os.environ,
            PYTHONPATH=ROOT,
            SKILLFLOW_CMD=f"{sys.executable} -m skillflow.cli",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def run_runner(self, *args):
        return subprocess.run(
            ["bash", RUNNER, *args],
            cwd=ROOT,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=180,
        )

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "skillflow.cli", *args],
            cwd=self.session,
            env=dict(self.env, SKILLFLOW_DB=os.path.join(
                self.session, "skillflow.db")),
            capture_output=True,
            text=True,
            timeout=180,
        )

    def dag(self):
        conn = sqlite3.connect(os.path.join(self.session, "skillflow.db"))
        try:
            conn.row_factory = sqlite3.Row
            nodes = [dict(r) for r in conn.execute(
                "SELECT name, cmd FROM nodes ORDER BY name")]
        finally:
            conn.close()
        return {n["name"]: n["cmd"] for n in nodes}

    def write(self, name, text):
        with open(os.path.join(self.session, name), "w") as fh:
            fh.write(text)

    def test_no_node_prompts_and_missing_tensions_stop_first(self):
        result = self.run_runner("debate", "ship it friday", "1", self.session)
        # The run stops at the distill boundary instead of prompting.
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stage boundary", result.stdout + result.stderr)
        nodes = self.dag()
        self.assertNotIn("read -p", json.dumps(nodes))
        for name in ("distill", "activate-1", "validity-1", "tensions-1",
                     "finalize"):
            self.assertIn(name, nodes)
        self.assertIn("stage.py", nodes["round-1"])
        self.assertIn("stage.py", nodes["activate-1"])

    def _distill(self):
        self.write("tensions.txt",
                   "independence of the checker, legitimate stopping\n")

    def _activate(self, room_file="room-1.json", artifact="activation-1.md"):
        room = json.load(open(os.path.join(self.session, room_file)))
        lines = [f"{p['name']} ({p['id']}): first irritation, evidence "
                 f"standard, claim to kill.\n" for p in room["room"]]
        self.write(artifact, "".join(lines))

    def test_written_round_completes_and_writes_final_section(self):
        self.run_runner("debate", "ship it friday", "1", self.session)
        self._distill()
        result = self.cli("run")  # stops at activate-1
        self.assertNotEqual(result.returncode, 0)
        self._activate()
        self.write("record-1.md",
                   "where the claim moved\n\n" + READBACK)
        result = self.cli("run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(os.path.join(self.session, "final.md")) as fh:
            final = fh.read()
        self.assertIn("## Round 1", final)
        self.assertIn("where the claim moved", final)
        self.assertTrue(os.path.isfile(
            os.path.join(self.session, "notes", "round-1.md")))

    def test_rerun_does_not_reseat_a_seated_room(self):
        # A seated room is the lens work that produced the round's record.
        # Rerunning the DAG must keep it: the room on disk is what the
        # record answers to and what later rounds exclude. Re-seating from
        # updated tensions would let the newest tensions rewrite the panel
        # retroactively.
        self.run_runner("debate", "ship it friday", "2", self.session)
        self._distill()
        result = self.cli("run")  # select-1 seats; activate-1 stops
        self.assertNotEqual(result.returncode, 0)
        self._activate()
        self.write(
            "record-1.md",
            "where the claim moved\n\n## New tensions\n"
            "- refusal affordance\n- weak material\n\n" + READBACK)
        room_before = json.load(
            open(os.path.join(self.session, "room-1.json")))
        result = self.cli("run")  # select-2 seats; activate-2 stops
        self.assertNotEqual(result.returncode, 0)
        room_after = json.load(open(os.path.join(self.session, "room-1.json")))
        self.assertEqual(room_before["room"], room_after["room"])
        room2 = json.load(open(os.path.join(self.session, "room-2.json")))
        seated = {p["id"] for p in room_before["room"]}
        overlap = seated & {p["id"] for p in room2["room"]}
        self.assertEqual(overlap, set(),
                         f"round 2 re-seated round 1 panelists: {overlap}")

    def test_unchanged_tensions_end_the_session(self):
        # A round that moves nothing is the stop: the machine converges the
        # session and the remaining graph drains instead of polishing.
        self.run_runner("debate", "ship it friday", "3", self.session)
        self._distill()
        self.cli("run")
        self._activate()
        self.write(
            "record-1.md",
            "the claim moved nowhere\n\n## New tensions\n"
            "- independence of the checker\n- legitimate stopping\n\n"
            + READBACK)
        result = self.cli("run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(stage := os.path.isfile(
            os.path.join(self.session, "converged.txt")))
        with open(os.path.join(self.session, "final.md")) as fh:
            self.assertIn("Stopped:", fh.read())

    def test_refusal_stops_with_a_trace(self):
        self.run_runner("debate", "ship it friday", "2", self.session)
        self._distill()
        self.cli("run")
        self._activate()
        self.write("refusal.md", "the room refuses: the work is not ready\n")
        result = self.cli("run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with open(os.path.join(self.session, "final.md")) as fh:
            final = fh.read()
        self.assertIn("REFUSED", final)
        self.assertIn("the work is not ready", final)


if __name__ == "__main__":
    unittest.main()
