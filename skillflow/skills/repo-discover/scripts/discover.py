#!/usr/bin/env python3
"""Dispatch existing repository discovery and scoped read-only dictionary queries."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sqlite3
import sys


def inside(path, root):
    return path == root or root in path.parents


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'local.json')
    parser.add_argument('command', choices=['map', 'where', 'search', 'dictionary'])
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if not isinstance(config, dict):
        parser.error('local config must be a JSON object')
    for key in ('agent_orient', 'dictionary_directory'):
        if not isinstance(config.get(key), str) or not config[key].strip():
            parser.error(f'local config requires {key}')
        path = Path(config[key]).expanduser()
        if not path.is_absolute():
            path = args.config.expanduser().resolve().parent / path
        config[key] = str(path.resolve())
    if args.command != 'dictionary':
        cli = Path(config['agent_orient']) / 'scripts/repo-discover'
        return subprocess.call([str(cli), args.command, *args.arguments])

    query = argparse.ArgumentParser(prog='discover.py dictionary')
    query.add_argument('operation', choices=['status', 'repositories', 'models', 'capabilities', 'processes', 'process-steps', 'declarations', 'neighbors', 'same-source', 'evidence'])
    query.add_argument('value', nargs='?')
    query.add_argument('--root', type=Path, action='append')
    query.add_argument('--limit', type=int, default=100)
    selected = query.parse_args(args.arguments)
    if not 1 <= selected.limit <= 10000:
        query.error('--limit must be between 1 and 10000')
    directory = Path(config['dictionary_directory']).expanduser().resolve()
    spec = importlib.util.spec_from_file_location('development_dictionary_queries', directory / 'tools/queries.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    database = directory / 'data/dictionary.sqlite'
    snapshot = {row['key']: row['value'] for row in module.rows('SELECT * FROM metadata', database=database)}
    roots = [path.expanduser().resolve() for path in selected.root or [Path.cwd()]]
    checkouts = module.repositories(database=database)
    ids = [row['id'] for row in checkouts if any(
        inside(Path(row['path']).resolve(), root) or
        (not selected.root and inside(root, Path(row['path']).resolve())) for root in roots)]
    result = []
    total_matches = None
    operation = selected.operation
    if operation == 'status':
        result = [{'dictionary_directory': str(directory), 'database': str(database), 'selected_checkouts': len(ids)}]
    elif not ids:
        query.error('no recorded checkout matches this scope; map current roots and check snapshot coverage')
    elif operation == 'repositories':
        result = [row for row in checkouts if row['id'] in ids]
    elif operation in ('models', 'capabilities', 'processes'):
        table = {'models': 'data_model', 'capabilities': 'capability', 'processes': 'process'}[operation]
        marks = ','.join('?' for _ in ids)
        result = module.rows(f'SELECT * FROM {table} WHERE checkout_id IN ({marks}) ORDER BY checkout_id,name LIMIT ?', (*ids, selected.limit + 1), database)
    else:
        if not selected.value:
            query.error(f'{operation} requires a value')
        if operation == 'declarations':
            marks = ','.join('?' for _ in ids)
            total_matches = module.rows(f'''SELECT COUNT(*) AS n FROM declaration d JOIN source_file s ON s.id=d.source_id
                WHERE d.name=? AND s.checkout_id IN ({marks})''', (selected.value, *ids), database)[0]['n']
            result = [row for checkout_id in ids for row in module.declarations(
                selected.value, checkout_id=checkout_id, limit=min(selected.limit + 1, 10000), database=database)]
            result.sort(key=lambda row: (row['path'], row['line']))
        elif operation == 'neighbors':
            if selected.value not in ids:
                query.error('checkout ID is outside selected scope')
            result = module.neighbors(selected.value, database=database)
        elif operation == 'process-steps':
            owner = module.rows('SELECT checkout_id FROM process WHERE id=?', (selected.value,), database)
            if not owner or owner[0]['checkout_id'] not in ids:
                query.error('process is missing or outside selected scope')
            result = module.process_steps(selected.value, database=database)
        elif operation in ('same-source', 'evidence'):
            path = str(Path(selected.value).expanduser().resolve())
            # Evidence may reference a document not captured as a parsed source.
            if not any(inside(Path(path), Path(row['path']).resolve()) for row in checkouts if row['id'] in ids):
                query.error('source path is outside selected scope')
            if operation == 'same-source':
                result = [row for row in module.same_source(path, database=database) if row['checkout_id'] in ids]
            else:
                result = module.evidence_for_path(path, database=database)
    print(json.dumps({'operation': operation, 'roots': list(map(str, roots)), 'metadata': snapshot,
                      'truncated': (total_matches if total_matches is not None else len(result)) > selected.limit, 'limit': selected.limit,
                      'rows': result[:selected.limit]}, indent=2))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, ImportError, sqlite3.Error) as error:
        print(f'repo-discover: {error}', file=sys.stderr)
        sys.exit(1)
