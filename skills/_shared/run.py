#!/usr/bin/env python3
"""Locate the local pause runner without assuming the caller's cwd."""
import json
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
runner = here.parent.parent / 'panel' / 'run.sh'
if not runner.is_file():
    location = here / 'runner.json'
    if not location.is_file():
        sys.exit('Pause runner not installed. Run skillflow/scripts/install_panel_skills.py --skills-dir <skills-root>.')
    runner = Path(json.loads(location.read_text())['runner'])
if not runner.is_file():
    sys.exit(f'Pause runner moved or missing: {runner}. Reinstall from the current skillflow checkout.')
raise SystemExit(subprocess.call(['bash', str(runner), *sys.argv[1:]]))
