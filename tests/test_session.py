"""Session views: status summaries and artifact reads over a live session."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "panel/run.sh"

sys.path.insert(0, str(ROOT))
from skillflow.session import (  # noqa: E402
    format_status,
    read_artifact,
    status_summary,
)


class SessionViewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = Path(self.tmp.name) / "session1"
        result = subprocess.run(
            ["bash", str(RUNNER), "review", "Inspect a change",
             str(self.session)],
            capture_output=True, text=True, timeout=180,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def test_status_names_waiting_gate(self):
        summary = status_summary(self.session)
        self.assertEqual(summary["skill"], "review")
        self.assertEqual(summary["waiting"]["name"], "ground")
        self.assertEqual(summary["waiting"]["artifact"], "ground.md")
        self.assertIn("ground", format_status(summary))

    def test_status_advances_with_acceptance(self):
        (self.session / "ground.md").write_text(
            "Scope, sources, and open questions.\n")
        result = subprocess.run(
            ["bash", str(RUNNER), "resume", str(self.session)],
            capture_output=True, text=True, timeout=180,
        )
        self.assertEqual(result.returncode, 1)
        summary = status_summary(self.session)
        self.assertEqual(summary["accepted"], 1)
        self.assertEqual(summary["waiting"]["name"], "activate-1")
        states = {g["name"]: g["state"] for g in summary["gates"]}
        self.assertEqual(states["ground"], "accepted")
        self.assertEqual(states["activate-1"], "waiting")

    def test_artifact_read_prefers_working_copy(self):
        (self.session / "ground.md").write_text("working draft\n")
        self.assertEqual(
            read_artifact(self.session, "ground.md"), "working draft\n")
        with self.assertRaises(ValueError):
            read_artifact(self.session, "../escape.md")
        with self.assertRaises(ValueError):
            read_artifact(self.session, "missing.md")
        with self.assertRaises(ValueError):
            read_artifact(self.session, ".checkpoints.json")

    def test_non_session_refuses(self):
        with self.assertRaises(ValueError):
            status_summary(self.tmp.name)


if __name__ == "__main__":
    unittest.main()
