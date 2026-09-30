#!/usr/bin/env python3
"""Project a Skillflow skill bundle into a native skill directory, with a receipt."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import os
import tempfile


def safe_destination(path):
    """Refuse linked output paths before replacing any installed resource."""
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f'projection destination is symlinked: {candidate}')


def atomic_file(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

SOURCE = Path(__file__).resolve().parents[1] / 'skillflow/skills'


def native_frontmatter(front):
    lines = front.decode('utf-8').replace('\r\n', '\n').splitlines()
    result = []
    for line in lines:
        key, separator, value = line.partition(':')
        if key == 'shape':
            continue
        if separator and key in ('name', 'description'):
            value = value.strip()
            if value not in ('>', '>-', '|', '|-'):
                if value.startswith('"'):
                    value = json.loads(value)
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1].replace("''", "'")
                # JSON strings are valid YAML scalars, including colons/quotes.
                line = key + ': ' + json.dumps(value, ensure_ascii=False)
        result.append(line)
    return '\n'.join(result).encode('utf-8')


def project(skill, target, config=None):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill):
        raise ValueError('invalid skill ID')
    source = SOURCE / skill
    # Resolve existing parent aliases (such as macOS /var), but retain the
    # actual target component so an installed directory symlink cannot vanish.
    target = target.expanduser().absolute()
    if target.is_symlink():
        raise ValueError('projection target is symlinked')
    target = target.parent.resolve() / target.name
    if target == SOURCE.resolve() or SOURCE.resolve() in target.parents:
        raise ValueError('projection must be outside the canonical skill store')
    files = sorted(p for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in ('local.json', 'projection.json'))
    if not (source / 'SKILL.md').is_file():
        raise ValueError('missing source SKILL.md')
    entrypoint = (source / 'SKILL.md').read_bytes()
    match = re.match(rb'\A---\r?\n(.*?)\r?\n---\r?\n', entrypoint, re.S)
    if not match:
        raise ValueError('missing source frontmatter')
    shape_field = re.search(rb'^shape:\s*([^\n]+)', match.group(1), re.M)
    shape = shape_field.group(1).decode().strip() if shape_field else 'prose'
    if shape not in ('prose', 'single', 'setup-execute'):
        raise ValueError('invalid source shape')
    shared = target.parent / '_shared'
    outputs = [target / file.relative_to(source) for file in files] + [target / 'local.json', target / 'projection.json', shared / 'runner.json', shared / 'panelists.json']
    outputs += [shared / p.name for p in (SOURCE / '_shared').iterdir() if p.is_file()]
    for destination in outputs:
        safe_destination(destination)
    target.mkdir(parents=True, exist_ok=True)
    receipt = {'schema': 'skillflow.projection.v1', 'skill': skill, 'shape': shape, 'source': str(source), 'files': {}, 'shared_files': {}}
    for file in files:
        relative = file.relative_to(source)
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = file.read_bytes()
        projected = data
        if relative == Path('SKILL.md'):
            # Native harness frontmatter does not know Skillflow's shape key.
            match = re.match(rb'\A---\r?\n(.*?)\r?\n---\r?\n', data, re.S)
            if not match:
                raise ValueError('missing source frontmatter')
            front = native_frontmatter(match.group(1))
            projected = b'---\n' + front + b'\n---\n' + data[match.end():]
        atomic_file(destination, projected, file.stat().st_mode & 0o777)
        receipt['files'][str(relative)] = {'source_sha256': hashlib.sha256(data).hexdigest(), 'projected_sha256': hashlib.sha256(projected).hexdigest()}
    if config is not None:
        local = (json.dumps(config, indent=2) + '\n').encode()
        atomic_file(target / 'local.json', local)
        receipt['local_sha256'] = hashlib.sha256(local).hexdigest()
    # Panel and functional skills share the native pause launcher. An explicit
    # checkout pointer lets installed bundles run without installing a package.
    shared.mkdir(parents=True, exist_ok=True)
    for path in sorted((SOURCE / '_shared').iterdir()):
        if path.is_file():
            data = path.read_bytes()
            atomic_file(shared / path.name, data, path.stat().st_mode & 0o777)
            receipt['shared_files'][path.name] = hashlib.sha256(data).hexdigest()
    roster = (SOURCE.parent / 'panel/panelists.json').read_bytes()
    atomic_file(shared / 'panelists.json', roster)
    receipt['shared_files']['panelists.json'] = hashlib.sha256(roster).hexdigest()
    runner = (json.dumps({'runner': str(SOURCE.parents[1] / 'panel/run.sh')}, indent=2) + '\n').encode()
    atomic_file(shared / 'runner.json', runner)
    receipt['shared_files']['runner.json'] = hashlib.sha256(runner).hexdigest()
    atomic_file(target / 'projection.json', (json.dumps(receipt, indent=2) + '\n').encode())
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill', required=True)
    parser.add_argument('--target', type=Path, required=True, help='complete destination skill directory')
    parser.add_argument('--config-json', type=Path, help='local location config; never added to portable source')
    args = parser.parse_args()
    config = json.loads(args.config_json.read_text()) if args.config_json else None
    receipt = project(args.skill, args.target, config)
    print(json.dumps({'skill': args.skill, 'target': str(args.target), 'files': len(receipt['files'])}))


if __name__ == '__main__':
    main()
