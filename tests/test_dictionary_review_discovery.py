"""Exercise scoped review/exclusion discovery through the real dispatcher."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from skillflow import discovery

ROOT = Path(__file__).resolve().parents[1]
DISPATCH = ROOT / 'skillflow/skills/repo-discover/scripts/discover.py'


class ReviewDiscoveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.first = self.root / 'first'
        self.second = self.root / 'second'
        self.first.mkdir()
        self.second.mkdir()
        dictionary = self.root / 'dictionary'
        (dictionary / 'tools').mkdir(parents=True)
        (dictionary / 'data').mkdir()
        # A small SQLite-backed query fixture keeps dispatcher boundary tests
        # portable; the real owner query module is checked separately on its DB.
        (dictionary / 'tools/queries.py').write_text('''
import sqlite3
def rows(sql, parameters=(), database=None):
    with sqlite3.connect(database) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(sql, parameters)]
def repositories(database=None):
    return rows('SELECT * FROM repository_comparison', database=database)
def research_reviews(checkout_id, database=None):
    return rows('SELECT * FROM research_review WHERE checkout_id=?', (checkout_id,), database)
def source_exclusions(checkout_id, database=None):
    return rows('SELECT * FROM source_exclusion WHERE checkout_id=?', (checkout_id,), database)
''')
        self.config = self.root / 'local.json'
        self.config.write_text(json.dumps({'agent_orient': str(self.first),
                                          'dictionary_directory': str(dictionary)}))
        with sqlite3.connect(dictionary / 'data/dictionary.sqlite') as db:
            db.executescript('''
                CREATE TABLE metadata(key TEXT, value TEXT);
                CREATE TABLE repository_comparison(id TEXT, path TEXT, collection TEXT, name TEXT);
                CREATE TABLE research_review(checkout_id TEXT, followup_reviews_json TEXT);
                CREATE TABLE source_exclusion(checkout_id TEXT, path TEXT);
            ''')
            db.execute('INSERT INTO metadata VALUES (?,?)', ('snapshot_at', 'test-epoch'))
            for identity, path in [('first', self.first), ('second', self.second)]:
                db.execute('INSERT INTO repository_comparison VALUES (?,?,?,?)',
                           (identity, str(path), 'test', identity))
                db.execute('INSERT INTO research_review VALUES (?,?)',
                           (identity, json.dumps([{'interpretation': identity + ' checked follow-up'}])))
                db.execute('INSERT INTO source_exclusion VALUES (?,?)',
                           (identity, str(path / 'retired')))

    def call(self, operation, *arguments):
        return subprocess.run([sys.executable, str(DISPATCH), '--config', str(self.config),
                               'dictionary', operation, *arguments, '--root', str(self.first)],
                              text=True, capture_output=True)

    def test_reviews_preserve_followups_and_select_only_requested_root(self):
        result = self.call('research-reviews')
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)['rows']
        self.assertEqual([row['checkout_id'] for row in rows], ['first'])
        self.assertEqual(json.loads(rows[0]['followup_reviews_json'])[0]['interpretation'],
                         'first checked follow-up')

    def test_exclusions_select_only_requested_root(self):
        result = self.call('source-exclusions')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['rows'],
                         [{'checkout_id': 'first', 'path': str(self.first / 'retired')}])

    def test_review_value_cannot_widen_selected_scope(self):
        for operation in ['research-reviews', 'source-exclusions']:
            with self.subTest(operation=operation):
                result = self.call(operation, 'second')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('outside selected scope', result.stderr)
                self.assertEqual(result.stdout, '')

    def test_dag_gathers_reviews_and_exclusions(self):
        calls = []
        def gather(session, plan, operation, value=None):
            calls.append(operation)
            return {'rows': []}
        with patch('skillflow.discovery.dictionary_call', side_effect=gather):
            result = discovery.execute(self.root, 'dictionary', {'terms': []})
        self.assertIn('research-reviews', calls)
        self.assertIn('source-exclusions', calls)
        self.assertIn('research-reviews', result)
        self.assertIn('source-exclusions', result)


if __name__ == '__main__':
    unittest.main()
