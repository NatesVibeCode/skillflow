#!/usr/bin/env python3
"""Locate the local pause runner without assuming the caller's cwd."""
import json
import os
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
env = dict(os.environ, SKILLFLOW_SKILLS_ROOT=str(here.parent))
runner = here.parent.parent / 'panel' / 'run.sh'
if not runner.is_file():
    location = here / 'runner.json'
    if location.is_file():
        runner = Path(json.loads(location.read_text())['runner'])
    else:
        # Installed skills with no checkout: use the packaged runner.
        raise SystemExit(subprocess.call(
            [sys.executable, '-m', 'skillflow.checkpoints', *sys.argv[1:]],
            env=env))
if not runner.is_file():
    sys.exit(f'Pause runner moved or missing: {runner}. Reinstall from the current skillflow checkout.')
raise SystemExit(subprocess.call(['bash', str(runner), *sys.argv[1:]], env=env))
