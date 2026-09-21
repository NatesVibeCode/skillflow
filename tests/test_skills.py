"""Skill store tests: install, validate, and run the shipped skills."""

import os
import subprocess
import sys
import tempfile
import unittest

from skillflow.cli import main
from skillflow.skills import SKILL_IDS, check_dir, init_dir


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
                     "panelists.json"):
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


if __name__ == "__main__":
    unittest.main()
