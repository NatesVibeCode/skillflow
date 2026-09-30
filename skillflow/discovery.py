"""Functional repository-discovery DAG; semantic decisions stay in the session."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skillflow.dag import Flow, FlowError
from skillflow import checkpoints

STEPS = ['scope', 'map', 'lookup', 'search', 'dictionary', 'links', 'evidence', 'assemble', 'decide', 'finalize', 'deliver']
EDGES = [('scope', n) for n in ('map', 'lookup', 'search', 'dictionary')] + [
    ('dictionary', 'links'), ('links', 'evidence'), ('search', 'evidence'),
    ('map', 'assemble'), ('lookup', 'assemble'), ('dictionary', 'assemble'),
    ('evidence', 'assemble'), ('assemble', 'decide'), ('decide', 'finalize'),
    ('finalize', 'deliver')]


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    checkpoints.write_json(Path(path), value)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for data in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def within(path, root):
    return path == root or root in path.parents


def query_module(plan):
    spec = importlib.util.spec_from_file_location('dictionary_queries', Path(plan['config']['dictionary_directory']) / 'tools/queries.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def start(args):
    parser = argparse.ArgumentParser(prog='repo-discover DAG')
    parser.add_argument('subject')
    parser.add_argument('session', type=Path)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--root', type=Path, action='append')
    parser.add_argument('--term', action='append')
    parser.add_argument('--limit', type=int, default=1000)
    parser.add_argument('--jobs', type=int, default=4)
    parser.add_argument('--config', type=Path)
    options = parser.parse_args(args)
    root = Path(os.environ.get('SKILLFLOW_SKILLS_ROOT', Path(__file__).resolve().parent / 'skills'))
    skill = root / 'repo-discover'
    config_path = options.config or skill / 'local.json'
    config = read(config_path)
    if not isinstance(config, dict):
        raise ValueError('local config must be a JSON object')
    for key in ('agent_orient', 'dictionary_directory'):
        if not isinstance(config.get(key), str) or not config[key].strip():
            raise ValueError(f'local config requires {key}')
        path = Path(config[key]).expanduser()
        if not path.is_absolute():
            path = config_path.expanduser().resolve().parent / path
        config[key] = str(path.resolve())
    target = options.target.expanduser().resolve()
    roots = [p.expanduser().resolve() for p in options.root or [target]]
    if not options.subject.strip() or not target.is_dir() or not all(p.is_dir() for p in roots):
        raise ValueError('subject and existing target/root directories are required')
    if not any(within(target, p) for p in roots):
        raise ValueError('selected target must be inside a selected discovery root')
    if not 1 <= options.jobs <= 8 or not 1 <= options.limit <= 10000:
        raise ValueError('jobs must be 1..8 and limit 1..10000')
    terms = list(dict.fromkeys(options.term or [options.subject]))
    if not all(term.strip() for term in terms) or len(terms) > 20:
        raise ValueError('select 1..20 nonempty literal search variants')
    session = options.session.expanduser().resolve()
    if session.exists() and any(session.iterdir()):
        raise ValueError('session is not empty; resume it or choose a fresh directory')
    cli = Path(config['agent_orient']).resolve() / 'scripts/repo-discover'
    directory = Path(config['dictionary_directory']).resolve()
    engine = Path(__file__).resolve().parent
    inputs = [Path(__file__), engine / 'dag.py', engine / 'db.py', engine / 'checkpoints.py',
              engine / 'skills/__init__.py', skill / 'scripts/discover.py', skill / 'SKILL.md',
              skill / 'references/method.md',
              directory / 'tools/queries.py', directory / 'data/dictionary.sqlite', cli]
    # The wrapper compiles this implementation; bind its current source too.
    inputs += sorted((Path(config['agent_orient']) / 'go').rglob('*.go'))
    inputs += [p for p in (Path(config['agent_orient']) / 'go/go.mod', Path(config['agent_orient']) / 'go/go.sum') if p.is_file()]
    pinned = {str(p.resolve()): sha(p) for p in inputs}
    session.mkdir(parents=True)
    (session / 'artifacts').mkdir()
    (session / 'node-receipts').mkdir()
    (session / 'subject.txt').write_text(options.subject + '\n')
    write(session / 'local.json', config)
    plan = dict(schema='skillflow.discovery.v1', subject=options.subject,
                target=str(target), roots=list(map(str, roots)), terms=terms,
                limit=options.limit, jobs=options.jobs, config=config,
                dispatcher=str(skill / 'scripts/discover.py'), runner=str(Path(__file__).resolve()), inputs=pinned,
                nodes=STEPS, edges=EDGES)
    write(session / 'workflow.json', plan)
    (session / '.workflow.sha256').write_text(sha(session / 'workflow.json') + '\n')
    write(session / 'checkpoints.json', dict(skill='repo-discover', stages=[
        dict(name='decide', artifact='decision.json', round=0,
             prompt='Read packet.json and current source evidence. Decide reuse/extend/build/unknown for the selected target; write target, decision, reason, evidence paths, and gaps. This is session judgment, not human approval.'),
        dict(name='finalize', artifact='final.md', round=0,
             prompt='Write the complete useful result with exact paths, contracts, relationships, decision and scope/freshness limits. Resume to seal the receipt.')]))
    with Flow(str(session / 'skillflow.db')) as flow:
        for name in STEPS:
            command = shlex.join([sys.executable, str(Path(__file__).resolve()), '_node', str(session), name])
            flow.add_node(name, command, timeout_s=300, cwd=str(target))
        for before, after in EDGES:
            flow.add_edge(before, after)
    return resume(session)


def validate_inputs(plan):
    for path, expected in plan['inputs'].items():
        if not Path(path).is_file() or sha(path) != expected:
            raise ValueError(f'pinned input changed or missing: {path}; restore it or start a fresh session')


def validate_session(session, plan):
    anchor = session / '.workflow.sha256'
    if not anchor.is_file() or anchor.read_text().strip() != sha(session / 'workflow.json'):
        raise ValueError('workflow plan changed or is missing its pin; start a fresh session')
    if read(session / 'local.json') != plan['config']:
        raise ValueError('local config changed after discovery started; restore it or start a fresh session')


def validate_evidence(session, plan):
    path = session / 'artifacts/evidence.json'
    if not path.is_file():
        return
    for row in read(path)['rows']:
        resolved = Path(row['path']).resolve()
        if not any(within(resolved, Path(root).resolve()) for root in plan['roots']):
            raise ValueError(f'cached source evidence is outside selected scope: {row["path"]}')
        try:
            current = sha(row['path'])
        except OSError:
            current = None
        if current != row['current_sha256']:
            raise ValueError(f'cached source evidence changed: {row["path"]}; start a fresh discovery session')


def invalidate_delivery(session, archive, target):
    """A reopened semantic gate must produce a new receipt, retaining the old one."""
    names = ['artifacts/deliver.json', 'node-receipts/deliver.json', 'receipt.json']
    if target == 'decide':
        names.append('.decision-sources.json')
    for name in names:
        source = session / name
        if source.exists():
            destination = archive / 'delivery' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.replace(destination)


def resume(session):
    session = Path(session).resolve()
    plan = read(session / 'workflow.json')
    validate_session(session, plan)
    validate_inputs(plan)
    validate_evidence(session, plan)
    with Flow(str(session / 'skillflow.db')) as flow:
        status = flow.status(flow.run(jobs=plan['jobs']))
    validate_inputs(plan)
    for node in status['nodes']:
        if node['output']:
            print(node['output'].rstrip())
    if status['run']['status'] == 'ok':
        print(f'Complete: {session / "final.md"}; sealed receipt: {session / "receipt.json"}')
        return 0
    print('Resume: ' + shlex.join([sys.executable, plan['runner'], 'resume', str(session)]))
    return 1


def call(session, plan, arguments):
    if read(session / 'local.json') != plan['config']:
        raise ValueError('local config changed after discovery started')
    command = [sys.executable, plan['dispatcher'], '--config', str(session / 'local.json'), *arguments]
    result = subprocess.run(command, capture_output=True, text=True, timeout=240, cwd=plan['target'])
    if result.returncode:
        raise ValueError(f'command failed ({result.returncode}): {shlex.join(arguments)}\n{result.stderr}\n{result.stdout}')
    return json.loads(result.stdout)


def dictionary_call(session, plan, operation, value=None):
    args = ['dictionary', operation] + ([value] if value else [])
    for root in plan['roots']:
        args += ['--root', root]
    args += ['--limit', str(plan['limit'])]
    return call(session, plan, args)


def decision(session, plan):
    value = read(session / 'decision.json')
    if value.get('target') != plan['target'] or value.get('decision') not in ('reuse', 'extend', 'build', 'unknown'):
        raise ValueError('decision must retain exact selected target and use reuse/extend/build/unknown')
    if not isinstance(value.get('reason'), str) or not value['reason'].strip():
        raise ValueError('decision requires a reason')
    if not all(isinstance(value.get(key), list) and all(isinstance(x, str) for x in value[key]) for key in ('evidence', 'gaps')):
        raise ValueError('decision evidence and gaps must be string lists')
    if value['decision'] == 'unknown' and not value['gaps']:
        raise ValueError('unknown requires a specific gap')
    if value['decision'] in ('reuse', 'extend') and not value['evidence']:
        raise ValueError('reuse/extend require exact source evidence paths')
    for path in value['evidence']:
        if not Path(path).is_absolute():
            raise ValueError('decision evidence paths must be absolute')
        source = Path(path).resolve()
        if not source.is_file() or not any(within(source, Path(root)) for root in plan['roots']):
            raise ValueError(f'decision evidence must exist within selected roots: {path}')
    return value


def execute(session, name, plan):
    artifacts = session / 'artifacts'
    if name == 'scope':
        return {key: plan[key] for key in ('target', 'roots', 'terms', 'limit', 'inputs')}
    if name in ('map', 'lookup', 'search'):
        roots = ['--root', *plan['roots']]
        if name == 'map':
            return call(session, plan, ['map', *roots, '--all', '--json'])
        return [{'term': term, 'result': call(session, plan,
                 (['where', term] if name == 'lookup' else ['search', term, '--group', 'code,tests,docs,readmes,agents,decisions,config,skills', '--limit', str(plan['limit'])]) + roots + ['--json'])}
                for term in plan['terms']]
    if name == 'dictionary':
        result = {operation: dictionary_call(session, plan, operation) for operation in ('status', 'repositories', 'models', 'capabilities', 'processes')}
        result['declarations'] = [dictionary_call(session, plan, 'declarations', term) for term in plan['terms']]
        return result
    if name == 'links':
        dictionary = read(artifacts / 'dictionary.json')
        return dict(relationships=[dictionary_call(session, plan, 'neighbors', r['id']) for r in dictionary['repositories']['rows']],
                    process_steps=[dictionary_call(session, plan, 'process-steps', p['id']) for p in dictionary['processes']['rows']])
    if name == 'evidence':
        module = query_module(plan)
        database = Path(plan['config']['dictionary_directory']) / 'data/dictionary.sqlite'
        dictionary = read(artifacts / 'dictionary.json')
        ids = [r['id'] for key in ('models', 'capabilities', 'processes') for r in dictionary[key]['rows']]
        ids += [r['id'] for result in read(artifacts / 'links.json')['relationships'] for r in result['rows']]
        rows = module.rows('SELECT * FROM evidence WHERE record_id IN (' + ','.join('?' for _ in ids) + ') ORDER BY path,line LIMIT ?', (*ids, plan['limit'] + 1), database) if ids else []
        sources = {r['path']: {'path': r['path'], 'lines': []} for r in rows}
        for row in rows:
            sources[row['path']]['lines'].append(row['line'])
        def collect(value):
            if isinstance(value, dict):
                path = value.get('path')
                if isinstance(path, str) and value.get('line'):
                    full = Path(path)
                    if not full.is_absolute() and value.get('root_path'):
                        full = Path(value['root_path']).expanduser() / full
                    if full.is_absolute():
                        sources.setdefault(str(full), {'path': str(full), 'lines': []})['lines'].append(value['line'])
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)
        collect(read(artifacts / 'search.json'))
        collect(dictionary['declarations'])
        checked = []
        for source in list(sources.values())[:plan['limit']]:
            path = Path(source['path']).resolve()
            if not any(within(path, Path(root)) for root in plan['roots']):
                continue
            recorded = module.rows('SELECT sha256 FROM source_file WHERE path=?', (str(path),), database)
            try:
                current = sha(path)
                state = 'current' if recorded and recorded[0]['sha256'] == current else 'changed' if recorded else 'not-in-snapshot'
                diagnostic = None
            except OSError as error:
                current, state, diagnostic = None, 'unreadable-or-missing', str(error)
            checked.append(dict(source, lines=sorted(set(source['lines'])), recorded_sha256=recorded[0]['sha256'] if recorded else None, current_sha256=current, freshness=state, diagnostic=diagnostic))
        return dict(rows=checked, truncated=len(sources) > plan['limit'] or len(rows) > plan['limit'], limit=plan['limit'])
    if name == 'assemble':
        records = {p.stem: {'path': str(p), 'sha256': sha(p)} for p in sorted(artifacts.glob('*.json')) if p.stem != 'assemble'}
        packet = dict(schema='skillflow.discovery.packet.v1', subject=plan['subject'], target=plan['target'], roots=plan['roots'], terms=plan['terms'], artifacts=records,
                      snapshot=read(artifacts / 'dictionary.json')['status']['metadata'],
                      limits='Bounded local source evidence; registry and dictionary descriptions do not establish ownership or runtime readiness.')
        write(session / 'packet.json', packet)
        return packet
    if name == 'deliver':
        validate_evidence(session, plan)
        chosen = decision(session, plan)
        bound = read(session / '.decision-sources.json')
        if bound['decision_sha256'] != sha(session / 'decision.json') or any(sha(path) != digest for path, digest in bound['sources'].items()):
            raise ValueError('accepted decision source evidence changed; start a fresh discovery session')
        sealed = {str(p.relative_to(session)): sha(p) for folder in ('artifacts', 'node-receipts') for p in sorted((session / folder).glob('*.json')) if p.name != 'deliver.json'}
        sealed.update({p: sha(session / p) for p in ('workflow.json', '.workflow.sha256', 'local.json', '.decision-sources.json', 'packet.json', 'decision.json', 'final.md')})
        result = dict(schema='skillflow.discovery.receipt.v1', target=plan['target'], decision=chosen,
                      artifacts=sealed, source_hashes=bound['sources'],
                      inputs=plan['inputs'], runtime='local Skillflow DAG; no inference launched')
        write(session / 'receipt.json', result)
        return result
    raise ValueError(f'unknown function {name}')


def node(session, name):
    session = Path(session).resolve()
    plan = read(session / 'workflow.json')
    validate_session(session, plan)
    if name in ('decide', 'finalize'):
        validate_evidence(session, plan)
        if (session / 'decision.json').is_file():
            decision(session, plan)
        bound = session / '.decision-sources.json'
        if bound.is_file():
            snapshot = read(bound)
            if snapshot['decision_sha256'] != sha(session / 'decision.json') or any(sha(path) != digest for path, digest in snapshot['sources'].items()):
                raise ValueError('accepted decision source evidence changed; start a fresh discovery session')
        if name == 'decide' and (session / 'decision.json').is_file():
            decision(session, plan)
        result = checkpoints.gate(session, name)
        if result == 0 and name == 'decide' and not bound.is_file():
            chosen = decision(session, plan)
            write(bound, {'decision_sha256': sha(session / 'decision.json'), 'sources': {path: sha(path) for path in chosen['evidence']}})
        return result
    output = session / 'artifacts' / f'{name}.json'
    receipt = session / 'node-receipts' / f'{name}.json'
    if receipt.is_file():
        record = read(receipt)
        if record['plan_sha256'] != sha(session / 'workflow.json') or not output.is_file() or sha(output) != record['output_sha256']:
            raise ValueError(f'recorded function output changed: {output}; start a fresh session')
        alias = {'assemble': 'packet.json', 'deliver': 'receipt.json'}.get(name)
        if alias and (not (session / alias).is_file() or sha(session / alias) != sha(output)):
            raise ValueError(f'recorded output changed: {session / alias}; start a fresh session')
        print(f'{name}: retained {output}')
        return 0
    result = execute(session, name, plan)
    validate_inputs(plan)
    write(output, result)
    write(receipt, dict(schema='skillflow.function.receipt.v1', function=name, output=str(output), output_sha256=sha(output), plan_sha256=sha(session / 'workflow.json')))
    print(f'{name}: wrote {output}')
    return 0


def main(args=None):
    args = list(sys.argv[1:] if args is None else args)
    try:
        if len(args) == 3 and args[0] == '_node':
            return node(args[1], args[2])
        if len(args) == 2 and args[0] == 'resume':
            return resume(args[1])
        return start(args)
    except (ValueError, OSError, KeyError, FlowError, subprocess.TimeoutExpired) as error:
        print(f'repo-discover DAG: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
