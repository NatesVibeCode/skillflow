import json
import os
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "ui-crawl-dag.sh")


class UiCrawlDagTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.crawl = os.path.join(self.tmp.name, "ui-crawl")
        os.makedirs(self.crawl)
        open(os.path.join(self.crawl, "package.json"), "w").close()
        shim = os.path.join(self.tmp.name, "bin", "skillflow")
        os.makedirs(os.path.dirname(shim))
        with open(shim, "w") as fh:
            fh.write(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} -m skillflow \"$@\"\n")
        os.chmod(shim, os.stat(shim).st_mode | stat.S_IXUSR | stat.S_IXGRP)
        self.env = dict(
            os.environ, PATH=os.path.dirname(shim) + os.pathsep + os.environ["PATH"]
        )
        self.db = os.path.join(self.tmp.name, "crawl.db")

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

    def test_help(self):
        result = self.run_script("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--ui-crawl-dir", result.stdout)

    def test_builds_single_node_dag(self):
        result = self.run_script(
            "--db", self.db, "--ui-crawl-dir", self.crawl,
            "--base-url", "http://localhost:3000", "--routes", "/,/health",
            "--no-run",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        dag = json.loads(result.stdout[result.stdout.index("{"):])
        self.assertEqual([n["name"] for n in dag["nodes"]], ["ui-crawl"])
        self.assertIn("--base-url", dag["nodes"][0]["cmd"])
        self.assertEqual(dag["edges"], [])

    def test_missing_checkout_fails(self):
        result = self.run_script(
            "--db", self.db, "--ui-crawl-dir", os.path.join(self.tmp.name, "nope")
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
