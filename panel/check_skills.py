"""Offline shape check for skills/*/SKILL.md (runs in CI and locally).

Mirrors the portable rules without needing a harness validator:
frontmatter name matches the directory, description is one line,
id charset is portable.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(HERE, "..", "skills")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def check(skill_id: str) -> list:
    errors = []
    if not ID_RE.match(skill_id):
        errors.append(f"{skill_id}: bad id charset")
    path = os.path.join(SKILLS_DIR, skill_id, "SKILL.md")
    if not os.path.isfile(path):
        return errors + [f"{skill_id}: missing SKILL.md"]
    text = open(path).read()
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


def main() -> int:
    skills = sorted(d for d in os.listdir(SKILLS_DIR)
                    if not d.startswith(("_", ".")))
    if not skills:
        print("error: no skills found", file=sys.stderr)
        return 1
    errors = []
    for skill_id in skills:
        errors.extend(check(skill_id))
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    if not errors:
        print(f"ok: {len(skills)} skills ({', '.join(skills)})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
