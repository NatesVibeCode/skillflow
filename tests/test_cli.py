"""CLI smoke tests."""

import io
import unittest
from contextlib import redirect_stdout

from skillflow import __version__
from skillflow.cli import main


class TestCli(unittest.TestCase):
    def test_version_flag(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            with self.assertRaises(SystemExit) as ctx:
                main(["--version"])
        self.assertEqual(ctx.exception.code, 0)
        self.assertEqual(buf.getvalue().strip(), __version__)
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
