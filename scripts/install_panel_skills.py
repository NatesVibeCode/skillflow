#!/usr/bin/env python3
"""Install the five panel skills plus their shared prose and local launcher."""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ('debate', 'brainstorm', 'review', 'reframe', 'add-skill')


def install(destination):
    destination = destination.expanduser().resolve()
    source = ROOT / 'skills'
    if destination == source:
        raise ValueError('install destination must differ from the source skills tree')
    for name in SKILLS:
        target = destination / name
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name / 'SKILL.md', target / 'SKILL.md')
    shared = destination / '_shared'
    shared.mkdir(parents=True, exist_ok=True)
    for name in ('panel.md', 'running-on-skillflow.md', 'run.py'):
        shutil.copy2(source / '_shared' / name, shared / name)
    shutil.copy2(ROOT / 'skillflow/panel/panelists.json', shared / 'panelists.json')
    (shared / 'runner.json').write_text(json.dumps({'runner': str(ROOT / 'panel/run.sh')}, indent=2) + '\n')
    print(f'Installed {", ".join(SKILLS)} and shared prose into {destination}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skills-dir', type=Path, action='append', required=True)
    args = parser.parse_args()
    for destination in args.skills_dir:
        install(destination)


if __name__ == '__main__':
    main()
