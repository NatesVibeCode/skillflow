"""Bundled skill store: validate and install the shipped skills."""

import os
import re
import shutil

SKILL_IDS = ("brainstorm", "debate", "reframe", "review")
SHARED_FILES = ("panel.md", "running-on-skillflow.md", "run.py")
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PANELISTS = os.path.join(DATA_DIR, "..", "panel", "panelists.json")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def check(skill_id: str, skills_dir: str) -> list:
    """Portable shape check for one skill directory. Returns error strings."""
    errors = []
    if not ID_RE.match(skill_id):
        errors.append(f"{skill_id}: bad id charset")
    path = os.path.join(skills_dir, skill_id, "SKILL.md")
    if not os.path.isfile(path):
        return errors + [f"{skill_id}: missing SKILL.md"]
    with open(path) as handle:
        text = handle.read()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return errors + [f"{skill_id}: missing frontmatter"]
    front = match.group(1)
    name = re.search(r"^name:\s*(\S+)", front, re.M)
    desc = re.search(r"^description:\s*(.+)", front, re.M)
    if not name:
        errors.append(f"{skill_id}: frontmatter has no name")
    elif name.group(1) != skill_id:
        errors.append(
            f"{skill_id}: frontmatter name {name.group(1)!r} != directory")
    if not desc or not desc.group(1).strip():
        errors.append(f"{skill_id}: frontmatter has no description")
    return errors


def check_dir(skills_dir: str) -> list:
    """Check every skill in a directory. Returns error strings."""
    skills = sorted(d for d in os.listdir(skills_dir)
                    if not d.startswith(("_", ".")))
    if not skills:
        return ["no skills found"]
    errors = []
    for skill_id in skills:
        errors.extend(check(skill_id, skills_dir))
    return errors


def init_dir(target) -> list:
    """Copy the shipped skills and shared files into target. Returns ids."""
    target = os.path.abspath(os.path.expanduser(target))
    if os.path.abspath(DATA_DIR) == target:
        raise ValueError("install destination must differ from the source skills tree")
    for skill_id in SKILL_IDS:
        dest = os.path.join(target, skill_id)
        os.makedirs(dest, exist_ok=True)
        shutil.copy2(os.path.join(DATA_DIR, skill_id, "SKILL.md"),
                     os.path.join(dest, "SKILL.md"))
    shared = os.path.join(target, "_shared")
    os.makedirs(shared, exist_ok=True)
    for name in SHARED_FILES:
        shutil.copy2(os.path.join(DATA_DIR, "_shared", name),
                     os.path.join(shared, name))
    shutil.copy2(PANELISTS, os.path.join(shared, "panelists.json"))
    return list(SKILL_IDS)
