"""Regression coverage for native projections and resumable discovery surfaces."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import io
from contextlib import redirect_stdout
from types import SimpleNamespace

from skillflow import checkpoints, discovery
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
        self.source = self.root / 'source.py'
        self.source.write_text('original source')
        self.config = {'agent_orient': str(self.root / 'agent-orient'), 'dictionary_directory': str(self.root / 'dictionary')}
        self.plan = dict(schema='skillflow.discovery.v1', config=self.config,
                         target=str(self.root), roots=[str(self.root)], evidence_roots=[],terms=['Symbol'], limit=10,
                         jobs=1, dispatcher=str(self.root / 'dispatch.py'),
                         runner=str(ROOT / 'skillflow/discovery.py'),
                         inputs={str(self.source): discovery.sha(self.source)}, nodes=discovery.STEPS, edges=discovery.EDGES)
        discovery.write(self.session / 'workflow.json', self.plan)
        (self.session / '.workflow.sha256').write_text(discovery.sha(self.session / 'workflow.json') + '\n')
        discovery.write(self.session / 'local.json', self.config)
        discovery.write(self.session / 'checkpoints.json', {'skill': 'repo-discover', 'stages': [
            {'name': 'decide', 'artifact': 'decision.json', 'prompt': 'decide'},
            {'name': 'finalize', 'artifact': 'final.md', 'prompt': 'finish'}]})

    def test_dispatch_refuses_changed_local_configuration(self):
        changed = dict(self.config, agent_orient=str(self.root / 'different-owner'))
        discovery.write(self.session / 'local.json', changed)
        with patch('skillflow.discovery.subprocess.run') as launch:
            launch.return_value.returncode = 0
            launch.return_value.stdout = '{}'
            with self.assertRaisesRegex(ValueError, 'config'):
                discovery.call(self.session, self.plan, ['map', '--json'])
            launch.assert_not_called()

    def test_cached_evidence_refuses_source_change_before_judgment(self):
        discovery.write(self.session / 'artifacts/evidence.json', {'rows': [
            {'path': str(self.source), 'current_sha256': discovery.sha(self.source)}]})
        self.source.write_text('later source')
        # Source evidence is separate from implementation/input pins.
        self.plan['inputs'] = {}
        discovery.write(self.session / 'workflow.json', self.plan)
        (self.session / '.workflow.sha256').write_text(discovery.sha(self.session / 'workflow.json') + '\n')
        with patch('skillflow.checkpoints.gate', return_value=0):
            with self.assertRaisesRegex(ValueError, 'evidence'):
                discovery.node(self.session, 'decide')

    def test_search_home_relative_roots_are_checked_for_freshness(self):
        dictionary = {key: {'rows': []} for key in ['models', 'capabilities', 'processes']}
        dictionary['declarations'] = []
        dictionary['terms']={'rows':[]}
        dictionary['contracts']={'rows':[]}
        discovery.write(self.session / 'artifacts/dictionary.json', dictionary)
        discovery.write(self.session / 'artifacts/links.json', {'relationships': [],'scenarios':[]})
        discovery.write(self.session / 'artifacts/search.json', [{'result': [
            {'root_path': '~/selected', 'path': 'source.py', 'line': 7}]}])
        original = Path.expanduser
        def expand(path):
            return self.root if str(path) == '~/selected' else original(path)
        with patch.object(Path, 'expanduser', expand), patch('skillflow.discovery.query_module', return_value=SimpleNamespace(rows=lambda *args: [])):
            result = discovery.execute(self.session, 'evidence', self.plan)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['path'], str(self.source))
        self.assertEqual(result['rows'][0]['lines'], [7])
        self.assertEqual(result['rows'][0]['current_sha256'], discovery.sha(self.source))

    def test_native_receipt_pin_refuses_even_if_gathered_bytes_are_stable(self):
        discovery.write(self.session / 'artifacts/evidence.json', {'rows': [
            {'path':str(self.source),'current_sha256':discovery.sha(self.source),'reference_sha256':'0'*64}]})
        with self.assertRaisesRegex(ValueError,'native reference'):
            discovery.validate_evidence(self.session,self.plan)

    def test_explicit_evidence_root_does_not_widen_code_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt=Path(directory)/'receipt.json';receipt.write_text('{}')
            row={'path':str(receipt),'current_sha256':discovery.sha(receipt),'reference_sha256':discovery.sha(receipt)}
            discovery.write(self.session/'artifacts/evidence.json',{'rows':[row]})
            with self.assertRaisesRegex(ValueError,'scope'):
                discovery.validate_evidence(self.session,self.plan)
            scoped=dict(self.plan,evidence_roots=[directory])
            discovery.validate_evidence(self.session,scoped)
            self.assertEqual(scoped['roots'],self.plan['roots'])

    def test_rewind_invalidates_sealed_delivery(self):
        for name in ['artifacts/deliver.json', 'node-receipts/deliver.json', 'receipt.json', '.decision-sources.json']:
            discovery.write(self.session / name, {'old': True})
        state = {'accepted': {}, 'waiting': None}
        checkpoints.rewind(self.session, 'decide', state)
        for name in ['artifacts/deliver.json', 'node-receipts/deliver.json', 'receipt.json', '.decision-sources.json']:
            self.assertFalse((self.session / name).exists(), name)
        self.assertTrue(list((self.session / 'revisions').rglob('deliver.json')))

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
