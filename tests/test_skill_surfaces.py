"""Regression coverage for native projections and resumable discovery surfaces."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io
from contextlib import redirect_stdout

from skillflow.dag import Flow
from skillflow.session import status_summary
from skillflow.skills import read_shape

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('skill_projector', ROOT / 'scripts/project_skill.py')
projector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projector)


class SurfaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.session = self.root / 'session'
        self.session.mkdir()
        (self.session / 'artifacts').mkdir()
        (self.session / 'node-receipts').mkdir()
        self.config = {'agent_orient': str(self.root / 'agent-orient'), 'dictionary_directory': str(self.root / 'dictionary')}
        (self.session / 'local.json').write_text(json.dumps(self.config))
        (self.session / 'checkpoints.json').write_text(json.dumps({'skill': 'sample', 'stages': []}))

    def test_status_exposes_failed_function_before_any_gate(self):
        with Flow(str(self.session / 'skillflow.db')) as flow:
            flow.add_node('scope', 'true')
            flow.add_node('map', 'false')
            flow.add_edge('scope', 'map')
            flow.run()
        summary = status_summary(self.session)
        self.assertEqual(summary['execution']['status'], 'failed')
        self.assertEqual(summary['execution']['failed_tasks'], ['map'])

    def make_store(self):
        store = self.root / 'store/skills'
        (store / 'sample').mkdir(parents=True)
        (store / '_shared').mkdir()
        (store / 'sample/SKILL.md').write_text('---\nname: sample\ndescription: Example\nshape: setup-execute\n---\nGuide\n')
        (store / '_shared/run.py').write_text('# shared runner\n')
        (store.parent / 'panel').mkdir()
        (store.parent / 'panel/panelists.json').write_text('{"panelists": []}')
        return store

    def test_native_projection_retains_executable_shape(self):
        store = self.make_store()
        target = self.root / 'native/sample'
        with patch.object(projector, 'SOURCE', store):
            projector.project('sample', target)
        shape, error = read_shape('sample', str(target.parent))
        self.assertIsNone(error)
        self.assertEqual(shape, 'setup-execute')

    def test_prose_projection_does_not_copy_pause_runtime(self):
        store = self.make_store()
        (store / 'sample/SKILL.md').write_text('---\nname: sample\ndescription: Guide\nshape: prose\n---\nGuide\n')
        target = self.root / 'native/sample'
        with patch.object(projector, 'SOURCE', store):
            receipt = projector.project('sample', target)
        self.assertEqual(read_shape('sample', str(target.parent)), ('prose', None))
        self.assertEqual(receipt['shared_files'], {})
        self.assertFalse((target.parent / '_shared').exists())

    def test_projected_description_with_colon_is_quoted(self):
        store = self.make_store()
        (store / 'sample/SKILL.md').write_text('---\nname: sample\ndescription: Native guide: collect and decide\nshape: single\n---\nGuide\n')
        target = self.root / 'native/sample'
        with patch.object(projector, 'SOURCE', store):
            projector.project('sample', target)
        text = (target / 'SKILL.md').read_text()
        self.assertIn('description: "Native guide: collect and decide"', text)
        self.assertEqual(read_shape('sample', str(target.parent)), ('single', None))

    def test_projector_refuses_any_destination_in_canonical_store(self):
        store = self.make_store()
        with patch.object(projector, 'SOURCE', store):
            with self.assertRaises(ValueError):
                projector.project('sample', store / 'another')

    def test_projector_refuses_symlinked_destination_file(self):
        store = self.make_store()
        outside = self.root / 'untouched'
        outside.write_text('do not overwrite')
        target = self.root / 'native/sample'
        target.mkdir(parents=True)
        (target / 'SKILL.md').symlink_to(outside)
        with patch.object(projector, 'SOURCE', store):
            with self.assertRaises(ValueError):
                projector.project('sample', target)
        self.assertEqual(outside.read_text(), 'do not overwrite')

    def test_native_projection_shape_is_bound_to_entrypoint_bytes(self):
        store = self.make_store()
        target = self.root / 'native/sample'
        with patch.object(projector, 'SOURCE', store):
            projector.project('sample', target)
        (target / 'SKILL.md').write_text('---\nname: sample\ndescription: Changed\n---\nGuide\n')
        shape, error = read_shape('sample', str(target.parent))
        self.assertIsNone(shape)
        self.assertIn('projection', error)

    def test_declaration_limit_reports_hidden_rows_at_maximum(self):
        dictionary = self.root / 'dictionary'
        (dictionary / 'tools').mkdir(parents=True)
        (dictionary / 'tools/queries.py').write_text('''
def rows(sql, parameters=(), database=None):
    if 'COUNT(*)' in sql: return [{'n': 10001}]
    return [{'key': 'snapshot_at', 'value': 'snapshot'}]
def repositories(database=None):
    return [{'id': 'checkout', 'path': ''' + repr(str(self.root)) + '''}]
def declarations(name, checkout_id=None, limit=100, database=None):
    return [{'path': '/recorded/source', 'line': i} for i in range(min(limit, 10000))]
''')
        spec = importlib.util.spec_from_file_location('dictionary_dispatcher', ROOT / 'skillflow/skills/repo-discover/scripts/discover.py')
        dispatcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dispatcher)
        out = io.StringIO()
        args = ['discover.py', '--config', str(self.session / 'local.json'), 'dictionary', 'declarations', 'Symbol', '--root', str(self.root), '--limit', '10000']
        with patch('sys.argv', args), redirect_stdout(out):
            self.assertEqual(dispatcher.main(), 0)
        result = json.loads(out.getvalue())
        self.assertTrue(result['truncated'])
        self.assertEqual(len(result['rows']), 10000)
