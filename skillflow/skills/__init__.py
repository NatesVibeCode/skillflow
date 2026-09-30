"""Bundled skill store: validate and install the shipped skills."""

import os
import hashlib
import json
import re
import shutil

SKILL_IDS = ("brainstorm", "debate", "reframe", "review", "skill-dag", "repo-discover")
SHARED_FILES = ("panel.md", "running-on-skillflow.md", "run.py", "authoring.md")
SHAPES = ("prose", "single", "setup-execute")
DEFAULT_SHAPE = "prose"
DATA_DIR = os.path.dirname(os.path.abspath(__file__))
PANELISTS = os.path.join(DATA_DIR, "..", "panel", "panelists.json")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _frontmatter(path: str):
    """Parse SKILL.md frontmatter into a dict, or None if absent."""
    with open(path) as handle:
        text = handle.read()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    front = match.group(1)
    fields = {}
    for key in ("name", "description", "shape"):
        found = re.search(rf"^{key}:\s*(.+)", front, re.M)
        if found:
            value = found.group(1).strip()
            if value.startswith('"'):
                try:
                    value = json.loads(value)
                except ValueError:
                    return None
                if not isinstance(value, str):
                    return None
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1].replace("''", "'")
            fields[key] = value
    return fields


def read_shape(skill_id: str, skills_dir: str):
    """Return (shape, error). Missing file or shape falls back or errors."""
    path = os.path.join(skills_dir, skill_id, "SKILL.md")
    if not os.path.isfile(path):
        return None, f"{skill_id}: missing SKILL.md"
    fields = _frontmatter(path)
    if fields is None:
        return None, f"{skill_id}: missing frontmatter"
    shape = fields.get("shape")
    projection = os.path.join(skills_dir, skill_id, "projection.json")
    if shape is None and os.path.isfile(projection):
        try:
            with open(projection) as handle:
                receipt = json.load(handle)
            if "shape" in receipt:
                with open(path, "rb") as handle:
                    actual = hashlib.sha256(handle.read()).hexdigest()
                expected = receipt["files"]["SKILL.md"]["projected_sha256"]
                if receipt.get("skill") != skill_id or actual != expected:
                    return None, f"{skill_id}: projection entrypoint changed; refresh the native projection"
                shape = receipt["shape"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            return None, f"{skill_id}: invalid projection: {error}"
    shape = shape or DEFAULT_SHAPE
    if shape not in SHAPES:
        return None, (f"{skill_id}: unknown shape {shape!r} "
                      f"(expected one of: {', '.join(SHAPES)})")
    return shape, None


def check(skill_id: str, skills_dir: str) -> list:
    """Portable shape check for one skill directory. Returns error strings."""
    errors = []
    if not ID_RE.match(skill_id):
        errors.append(f"{skill_id}: bad id charset")
    path = os.path.join(skills_dir, skill_id, "SKILL.md")
    if not os.path.isfile(path):
        return errors + [f"{skill_id}: missing SKILL.md"]
    fields = _frontmatter(path)
    if fields is None:
        return errors + [f"{skill_id}: missing frontmatter"]
    if "name" not in fields:
        errors.append(f"{skill_id}: frontmatter has no name")
    elif fields["name"] != skill_id:
        errors.append(
            f"{skill_id}: frontmatter name {fields['name']!r} != directory")
    if not fields.get("description"):
        errors.append(f"{skill_id}: frontmatter has no description")
    _, shape_error = read_shape(skill_id, skills_dir)
    if shape_error:
        errors.append(shape_error)
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


def _template(skill_id: str, shape: str, description: str) -> str:
    title = skill_id.replace("-", " ").replace("_", " ").title()
    head = (f"---\nname: {skill_id}\ndescription: {description}\n"
            f"shape: {shape}\n---\n\n# {title}\n")
    launcher = (f'```sh\npython3 "<skills-root>/_shared/run.py" {skill_id} '
                f'"<subject>" "<session-dir>"\n```\n')
    if shape == "prose":
        return (head + "\nWhat this guide covers and when to reach for it.\n"
                "\n## Guide\n\nStep-by-step prose. No launcher: the session "
                "reads this file and follows it.\n"
                "\n## Record\n\nWhat to write down when done (if anything) "
                "and where it lives.\n")
    if shape == "single":
        return (head + "\nWhat one unit of work this skill gates. A local DAG "
                "enforces the single boundary; the prose work stays in the session.\n"
                f"\n{launcher}\nResolve `<skills-root>` from this skill's directory. "
                "After the `PAUSE`, do the work, write `final.md`, and resume "
                "in this same conversation.\n"
                "\n## Do\n\nHow to do the work: inputs to read, judgment to "
                "apply, shape of `final.md`.\n")
    return (head + "\nWhat this skill aligns then executes. A local DAG enforces "
            "the two boundaries; the prose work stays in the session.\n"
            f"\n{launcher}\nResolve `<skills-root>` from this skill's directory. "
            "After each `PAUSE`, do that phase's work, write its artifact, and "
            "resume in this same conversation.\n"
            "\n## Setup\n\nHow to levelset: what to read, what the "
            "goal/constraints/plan cover, shape of `levelset.md`.\n"
            "\n## Execute\n\nHow to execute the plan and what the complete "
            "`final.md` contains.\n")


def scaffold(skill_id: str, target, shape: str, description: str) -> str:
    """Write a new skill from a shape template. Returns the SKILL.md path."""
    if not ID_RE.match(skill_id):
        raise ValueError(f"bad skill id {skill_id!r}: use lowercase ASCII, "
                         "digits, hyphens")
    if shape not in SHAPES:
        raise ValueError(f"unknown shape {shape!r} "
                         f"(expected one of: {', '.join(SHAPES)})")
    target = os.path.abspath(os.path.expanduser(target))
    dest = os.path.join(target, skill_id)
    path = os.path.join(dest, "SKILL.md")
    if os.path.exists(path):
        raise ValueError(f"skill {skill_id!r} already exists in {target}")
    if not os.path.isfile(os.path.join(target, "_shared", "run.py")):
        init_shared(target)
    os.makedirs(dest, exist_ok=True)
    with open(path, "w") as handle:
        handle.write(_template(skill_id, shape, description))
    errors = check(skill_id, target)
    if errors:
        raise ValueError("; ".join(errors))
    return path


def init_shared(target) -> None:
    """Copy the shared launcher, prose, and panel data into target/_shared."""
    shared = os.path.join(target, "_shared")
    os.makedirs(shared, exist_ok=True)
    for name in SHARED_FILES:
        shutil.copy2(os.path.join(DATA_DIR, "_shared", name),
                     os.path.join(shared, name))
    shutil.copy2(PANELISTS, os.path.join(shared, "panelists.json"))


def init_dir(target) -> list:
    """Copy the shipped skills and shared files into target. Returns ids."""
    target = os.path.abspath(os.path.expanduser(target))
    if os.path.abspath(DATA_DIR) == target:
        raise ValueError("install destination must differ from the source skills tree")
    for skill_id in SKILL_IDS:
        dest = os.path.join(target, skill_id)
        shutil.copytree(os.path.join(DATA_DIR, skill_id), dest, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "local.json", "projection.json"))
    init_shared(target)
    return list(SKILL_IDS)
