"""Every example script runs green, plus the demo command."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.dirname(sys.executable)


class ExamplesTest(unittest.TestCase):
    def run_script(self, name):
        env = dict(os.environ, PATH=BIN + os.pathsep + os.environ["PATH"])
        return subprocess.run(
            ["bash", os.path.join(ROOT, "examples", name)],
            capture_output=True, text=True, env=env, timeout=180,
        )

    def test_hello(self):
        result = self.run_script("01-hello.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run 1: ok", result.stdout)

    def test_parallel(self):
        result = self.run_script("02-parallel.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run 1: ok", result.stdout)

    def test_retry(self):
        result = self.run_script("03-retry.sh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run 2: ok", result.stdout)

    def test_demo(self):
        result = subprocess.run(
            [sys.executable, "-m", "skillflow", "demo"],
            capture_output=True, text=True, timeout=180,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("run 1: ok", result.stdout)
        self.assertIn("fetch: ok", result.stdout)


if __name__ == "__main__":
    unittest.main()
