import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "harness-skill-drift.sh")
HARNESSES = [
    "antigravity",
    "claude",
    "codex",
    "cursor",
    "grok",
    "muse",
    "opencode",
]


class HarnessSkillDriftTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fleet = os.path.join(self.tmp.name, "fleet")
        self.handoff = os.path.join(self.tmp.name, "handoff")
        os.makedirs(os.path.join(self.fleet, "scripts"))
        os.makedirs(os.path.join(self.handoff, "scripts"))
        open(os.path.join(self.fleet, "scripts", "check_harness_drift.py"), "w").close()
        open(os.path.join(self.handoff, "scripts", "build_skills.py"), "w").close()
        for harness in HARNESSES:
            tree = os.path.join(self.handoff, f"{harness}-harness-handoff")
            os.makedirs(tree)
            open(os.path.join(tree, "contract.json"), "w").close()
        shim = os.path.join(self.tmp.name, "bin", "skillflow")
        os.makedirs(os.path.dirname(shim))
        with open(shim, "w") as fh:
            fh.write(f"#!/bin/sh\nexec {sys.executable} -m skillflow \"$@\"\n")
        os.chmod(shim, os.stat(shim).st_mode | stat.S_IXUSR | stat.S_IXGRP)
        self.env = dict(
            os.environ, PATH=os.path.dirname(shim) + os.pathsep + os.environ["PATH"]
        )
        self.db = os.path.join(self.tmp.name, "drift.db")

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *args):
        return subprocess.run(
            [SCRIPT, *args],
            cwd=ROOT,
            env=self.env,
            capture_output=True,
            text=True,
        )

    def base_args(self):
        return [
            "--db",
            self.db,
            "--harness-fleet-dir",
            self.fleet,
            "--harness-handoff-dir",
            self.handoff,
        ]

    def test_help_names_the_nodes(self):
        result = self.run_script("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--harness-fleet-dir", result.stdout)
        self.assertIn("--harness-handoff-dir", result.stdout)

    def test_builds_fan_in_dag(self):
        result = self.run_script(*self.base_args(), "--no-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        dag = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual(
            sorted(n["name"] for n in dag["nodes"]),
            ["fleet-self", "handoff-build-check", "harness-contracts"],
        )
        self.assertEqual(
            sorted(
                (e["from_name"], e["to_name"]) for e in dag["edges"]
            ),
            [
                ("fleet-self", "harness-contracts"),
                ("handoff-build-check", "harness-contracts"),
            ],
        )

    def test_missing_checkout_fails(self):
        result = self.run_script(
            *self.base_args(), "--harness-fleet-dir", os.path.join(self.tmp.name, "nope")
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
