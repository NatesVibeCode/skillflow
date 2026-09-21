"""Skill store tests: install, validate, and run the shipped skills."""

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from skillflow.cli import _choose_shape, main
from skillflow.skills import SHAPES, SKILL_IDS, check_dir, init_dir


class TestSkillStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = os.path.join(self.tmp.name, "skills")

    def test_init_installs_four_skills_and_shared(self):
        installed = init_dir(self.store)
        self.assertEqual(installed, list(SKILL_IDS))
        for skill_id in SKILL_IDS:
            path = os.path.join(self.store, skill_id, "SKILL.md")
            self.assertTrue(os.path.isfile(path), path)
        for name in ("panel.md", "running-on-skillflow.md", "run.py",
                     "authoring.md", "panelists.json"):
            path = os.path.join(self.store, "_shared", name)
            self.assertTrue(os.path.isfile(path), path)
        self.assertFalse(os.path.islink(
            os.path.join(self.store, "_shared", "panelists.json")))
        self.assertFalse(os.path.exists(os.path.join(self.store, "add-skill")))

    def test_init_merges_and_revalidates(self):
        init_dir(self.store)
        custom = os.path.join(self.store, "mine")
        os.makedirs(custom)
        with open(os.path.join(custom, "SKILL.md"), "w") as handle:
            handle.write("---\nname: mine\ndescription: custom skill\n---\n\n# Mine\n")
        init_dir(self.store)
        self.assertTrue(os.path.isfile(os.path.join(custom, "SKILL.md")))
        self.assertEqual(check_dir(self.store), [])

    def test_check_catches_bad_skill(self):
        init_dir(self.store)
        bad = os.path.join(self.store, "debate", "SKILL.md")
        with open(bad, "w") as handle:
            handle.write("no frontmatter here\n")
        errors = check_dir(self.store)
        self.assertTrue(any("debate" in err for err in errors), errors)

    def test_run_py_works_without_checkout(self):
        init_dir(self.store)
        session = os.path.join(self.tmp.name, "session")
        result = subprocess.run(
            [sys.executable, os.path.join(self.store, "_shared", "run.py"),
             "review", "Inspect a change", session],
            cwd=self.tmp.name, capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("PAUSE ground", result.stdout)
        self.assertTrue(os.path.isfile(os.path.join(session, "checkpoints.json")))

    def test_cli_init_skills(self):
        self.assertEqual(main(["init-skills", "--dir", self.store]), 0)
        self.assertEqual(check_dir(self.store), [])

    def _write_skill(self, skill_id, shape=None):
        dest = os.path.join(self.store, skill_id)
        os.makedirs(dest, exist_ok=True)
        shape_line = f"\nshape: {shape}" if shape else ""
        with open(os.path.join(dest, "SKILL.md"), "w") as handle:
            handle.write(f"---\nname: {skill_id}\ndescription: custom{shape_line}\n---\n")

    def test_shape_validation(self):
        init_dir(self.store)
        for shape in SHAPES:
            self._write_skill(f"good-{shape}", shape)
        self._write_skill("defaulted")
        self._write_skill("bad-shape", "ladder")
        errors = check_dir(self.store)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("bad-shape", errors[0])
        self.assertIn("unknown shape", errors[0])

    def test_new_skill_scaffolds_all_shapes(self):
        for shape in SHAPES:
            skill_id = f"made-{shape}"
            result = main(["new-skill", skill_id, "--dir", self.store,
                           "--shape", shape, "--description", "scaffolded"])
            self.assertEqual(result, 0)
            path = os.path.join(self.store, skill_id, "SKILL.md")
            with open(path) as handle:
                self.assertIn(f"shape: {shape}", handle.read())
        self.assertTrue(os.path.isfile(
            os.path.join(self.store, "_shared", "run.py")))
        self.assertEqual(check_dir(self.store), [])

    def test_new_skill_refuses_overwrite_and_bad_id(self):
        init_dir(self.store)
        self.assertEqual(main(["new-skill", "debate", "--dir", self.store,
                               "--shape", "prose"]), 1)
        self.assertEqual(main(["new-skill", "Bad Id!", "--dir", self.store,
                               "--shape", "prose"]), 1)

    def test_choose_shape_menu(self):
        with redirect_stdout(io.StringIO()):
            with patch("builtins.input", side_effect=["bogus", "single"]):
                self.assertEqual(_choose_shape(), "single")
            with patch("builtins.input", side_effect=EOFError):
                self.assertEqual(_choose_shape(), "prose")

    def _run_py(self, *args):
        return subprocess.run(
            [sys.executable, os.path.join(self.store, "_shared", "run.py"),
             *args],
            cwd=self.tmp.name, capture_output=True, text=True, timeout=180)

    def _write(self, session, name, text="done"):
        with open(os.path.join(session, name), "w") as handle:
            handle.write(text + "\n")

    def test_custom_single_runs_one_gate(self):
        init_dir(self.store)
        self.assertEqual(main(["new-skill", "triage", "--dir", self.store,
                               "--shape", "single"]), 0)
        session = os.path.join(self.tmp.name, "session")
        started = self._run_py("triage", "a subject", session)
        self.assertEqual(started.returncode, 1, started.stderr)
        self.assertIn("PAUSE do", started.stdout)
        self._write(session, "final.md")
        finished = self._run_py("resume", session)
        self.assertEqual(finished.returncode, 0, finished.stdout)
        self.assertIn("Complete", finished.stdout)

    def test_custom_setup_execute_runs_two_gates(self):
        init_dir(self.store)
        self.assertEqual(main(["new-skill", "migrate", "--dir", self.store,
                               "--shape", "setup-execute"]), 0)
        session = os.path.join(self.tmp.name, "session")
        started = self._run_py("migrate", "a subject", session)
        self.assertEqual(started.returncode, 1, started.stderr)
        self.assertIn("PAUSE setup", started.stdout)
        self._write(session, "levelset.md")
        middle = self._run_py("resume", session)
        self.assertEqual(middle.returncode, 1, middle.stdout)
        self.assertIn("PAUSE execute", middle.stdout)
        self._write(session, "final.md")
        finished = self._run_py("resume", session)
        self.assertEqual(finished.returncode, 0, finished.stdout)
        self.assertIn("Complete", finished.stdout)

    def test_prose_skill_has_no_phases(self):
        init_dir(self.store)
        self.assertEqual(main(["new-skill", "guide", "--dir", self.store,
                               "--shape", "prose"]), 0)
        session = os.path.join(self.tmp.name, "session")
        result = self._run_py("guide", "a subject", session)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("prose guide", result.stdout)
        self.assertFalse(os.path.exists(session))


if __name__ == "__main__":
    unittest.main()
