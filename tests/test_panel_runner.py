"""Behavioral checks for the hybrid: real DAG subprocesses, no model calls."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'panel/run.sh'


class HybridPanelTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        # Exercise shell-safe paths, not just convenient /tmp ASCII names.
        self.session = Path(self.tmp.name) / "session's $notes `literal`"

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, *args):
        return subprocess.run(['bash', str(RUNNER), *map(str, args)],
                              cwd=self.tmp.name, capture_output=True,
                              text=True, timeout=180)

    def start(self, skill='debate', rounds=2):
        args = [skill, 'the actual subject']
        if skill in ('debate', 'reframe'): args.append(str(rounds))
        result = self.call(*args, self.session)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('PAUSE ground', result.stdout)
        return self.plan()

    def plan(self):
        return json.loads((self.session / 'checkpoints.json').read_text())['stages']

    def state(self):
        return json.loads((self.session / '.checkpoints.json').read_text())

    def current(self):
        name = self.state()['waiting']['name']
        return next(s for s in self.plan() if s['name'] == name)

    def submit(self, body=None):
        step = self.current()
        if body is None:
            if step.get('decision'):
                body = json.dumps(dict(action='continue', reason='A distinct open tension remains.'))
            else:
                body = f'Session-authored work for {step["name"]}; no required magic headings.\n'
        (self.session / step['artifact']).write_text(body)
        return self.call('resume', self.session)

    def advance_to(self, name):
        for _ in range(70):
            if self.current()['name'] == name: return
            result = self.submit()
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.fail(f'never reached {name}')

    def test_all_four_complete_in_session_with_phase_boundaries_and_final(self):
        for skill in ('debate', 'brainstorm', 'review', 'reframe'):
            with self.subTest(skill=skill):
                self.session = Path(self.tmp.name) / skill
                plan = self.start(skill, 1)
                visited = []
                for step in plan:
                    self.assertEqual(self.current()['name'], step['name'])
                    visited.append(step['name'])
                    result = self.submit()
                    self.assertEqual(result.returncode, 0 if step['name'] == 'finalize' else 1,
                                     result.stdout + result.stderr)
                self.assertIn('ground', visited)
                self.assertIn('activate-1', visited)
                self.assertEqual(visited[-1], 'finalize')
                self.assertEqual((self.session / 'final.md').read_bytes(),
                                 (self.session / 'notes/final.md').read_bytes())
                self.assertIsNone(self.state()['waiting'])
                with sqlite3.connect(self.session / 'skillflow.db') as db:
                    cmds = '\n'.join(r[0] for r in db.execute('select cmd from nodes'))
                for forbidden in ('select_room', 'seed.py', 'stage.py', 'read -p'):
                    self.assertNotIn(forbidden, cmds)

    def test_add_skill_walks_draft_record_finalize(self):
        self.session = Path(self.tmp.name) / "add-skill"
        plan = self.start("add-skill", 1)
        self.assertEqual(
            [s["name"] for s in plan],
            ["ground", "draft", "record", "finalize"],
        )
        visited = []
        for step in plan:
            self.assertEqual(self.current()["name"], step["name"])
            visited.append(step["name"])
            result = self.submit()
            self.assertEqual(result.returncode, 0 if step["name"] == "finalize" else 1,
                             result.stdout + result.stderr)
        self.assertEqual(visited[-1], "finalize")
        self.assertIsNone(self.state()["waiting"])

    def test_chain_carries_final_into_next_skill(self):
        self.session = Path(self.tmp.name) / "prior"
        plan = self.start("debate", 1)
        for step in plan:
            result = self.submit()
            self.assertEqual(result.returncode, 0 if step["name"] == "finalize" else 1,
                             result.stdout + result.stderr)
        chained = Path(self.tmp.name) / "next"
        result = self.call("chain", self.session, "review", chained)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("PAUSE ground", result.stdout)
        self.assertEqual(
            (chained / "prior-final.md").read_bytes(),
            (self.session / "notes/final.md").read_bytes(),
        )
        doc = json.loads((chained / "checkpoints.json").read_text())
        self.assertEqual(doc["prior"], str(self.session.resolve()))
        self.assertIn("prior-final.md", doc["stages"][0]["prompt"])

    def test_chain_refuses_incomplete_or_unknown(self):
        self.session = Path(self.tmp.name) / "open"
        self.start("debate", 1)
        result = self.call("chain", self.session, "review",
                           Path(self.tmp.name) / "next")
        self.assertEqual(result.returncode, 2)
        self.assertIn("no recorded final.md", result.stderr)
        result = self.call("chain", self.session, "nope",
                           Path(self.tmp.name) / "next2")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown skill", result.stderr)

    def test_reframe_field_cannot_jump_to_lineup_and_final_cannot_be_prefilled(self):
        self.start('reframe', 1)
        self.advance_to('field-1')
        (self.session / 'lineup-1.md').write_text('Premature winner')
        result = self.submit('Alternatives without a winner')
        self.assertIn('PAUSE lineup-1', result.stdout)
        result = self.call('resume', self.session)
        self.assertIn('prefilled artifact has not been revised', result.stdout)
        self.assertNotIn('lineup-1', self.state()['accepted'])
        self.submit('Lineup reconsidered against the actual field')
        self.advance_to('finalize')
        self.assertNotIn('finalize', self.state()['accepted'])

    def test_brainstorm_and_review_do_not_converge_on_missing_tensions(self):
        for skill in ('brainstorm', 'review'):
            self.session = Path(self.tmp.name) / skill
            self.start(skill)
            self.advance_to('round-1')
            self.submit('Useful first phase with no tension heading.')
            self.assertEqual(self.current()['name'], 'activate-2')
            self.assertFalse((self.session / 'final.md').exists())

    def test_session_finish_skips_optional_rounds_but_not_final(self):
        self.start(rounds=3)
        self.advance_to('reflect-1')
        result = self.submit('{"action":"finish","reason":"A new experiment is needed."}')
        self.assertIn('PAUSE finalize', result.stdout)
        self.assertFalse((self.session / 'activation-2.md').exists())
        self.assertEqual(self.submit('Final authored judgment.').returncode, 0)

    def test_refusal_from_decision_preserves_trace_and_requires_final(self):
        self.start('debate')
        self.advance_to('reflect-1')
        result = self.submit('{"action":"refuse","reason":"The target evidence is unavailable; a result would be invented."}')
        self.assertIn('PAUSE finalize', result.stdout)
        self.assertFalse((self.session / 'activation-2.md').exists())
        self.assertEqual(self.state()['stop']['action'], 'refuse')
        self.assertEqual(self.submit('Cannot establish alignment; missing evidence named.').returncode, 0)
        self.assertIn('unavailable', (self.session / 'notes/decision-1.json').read_text())

    def test_manual_rewind_archives_work_and_reopens_required_phase(self):
        self.start(rounds=1)
        self.advance_to('round-1')
        self.submit('The answer precedes the crossfire.')
        result = self.call('rewind', self.session, 'round-1')
        self.assertIn('REOPENED:', result.stdout)
        self.assertNotIn('round-1', self.state()['accepted'])
        self.assertIn('ground', self.state()['accepted'])
        self.assertFalse((self.session / 'record-1.md').exists())
        self.assertTrue(list((self.session / 'revisions').glob('*/artifacts/record-1.md')))
        self.call('resume', self.session)
        self.assertEqual(self.current()['name'], 'round-1')

    def test_runner_does_not_parse_or_score_session_prose(self):
        self.start(rounds=1)
        self.advance_to('round-1')
        result = self.submit('Status: magic\nNo scorecard grammar belongs here.')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(self.current()['name'], 'reflect-1')

    def test_changed_accepted_evidence_blocks_until_rewind(self):
        self.start()
        self.submit('Original ground evidence')
        (self.session / 'ground.md').write_text('Corrected ground evidence')
        result = self.call('resume', self.session)
        self.assertIn('accepted artifact changed', result.stdout)
        self.assertNotIn('activate-1', self.state()['accepted'])
        result = self.call('rewind', self.session, 'ground')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.call('resume', self.session)
        self.assertEqual(self.current()['name'], 'ground')
        self.assertEqual(self.state()['accepted'], {})

    def test_invalid_decisions_do_not_release_the_next_phase(self):
        self.start(rounds=1)
        self.advance_to('reflect-1')
        for body in ('broken', '[]', '{"action":"finish","reason":""}', '{"action":"maybe","reason":"x"}'):
            self.assertEqual(self.submit(body).returncode, 1)
            self.assertEqual(self.current()['name'], 'reflect-1')

    def test_existing_session_and_invalid_rounds_are_rejected(self):
        self.start()
        result = self.call('debate', 'new target', '2', self.session)
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.session / 'subject.txt').read_text(), 'the actual subject\n')
        for rounds in ('0', '9', 'nonsense'):
            result = self.call('debate', 'subject', rounds, Path(self.tmp.name) / 'invalid')
            self.assertEqual(result.returncode, 2)

    def test_installed_skills_have_working_links_and_launcher_from_any_cwd(self):
        destination = Path(self.tmp.name) / 'installed skills'
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/install_panel_skills.py'),
                                 '--skills-dir', str(destination)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for skill in ('debate', 'brainstorm', 'review', 'reframe',
                      'add-skill'):
            self.assertEqual((destination / skill / 'SKILL.md').read_bytes(),
                             (ROOT / 'skillflow' / 'skills' / skill / 'SKILL.md').read_bytes())
        for name in ('panel.md', 'panelists.json', 'running-on-skillflow.md', 'run.py', 'authoring.md', 'runner.json'):
            self.assertTrue((destination / '_shared' / name).exists())
        result = subprocess.run([sys.executable, str(destination / '_shared/run.py'),
                                 'review', 'Inspect a change', str(self.session)],
                                cwd=self.tmp.name, capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('PAUSE ground', result.stdout)


if __name__ == '__main__':
    unittest.main()
