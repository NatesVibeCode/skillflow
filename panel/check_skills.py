"""Offline shape check for skillflow/skills/*/SKILL.md (runs in CI and locally).

Validates the source tree, including the repo-only authoring skill.
Installed stores are validated by `skillflow init-skills` via the same rules.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from skillflow.skills import check  # noqa: E402

SKILLS_DIR = os.path.join(HERE, "..", "skillflow", "skills")


def main() -> int:
    skills = sorted(d for d in os.listdir(SKILLS_DIR)
                    if not d.startswith(("_", ".")))
    if not skills:
        print("error: no skills found", file=sys.stderr)
        return 1
    errors = []
    for skill_id in skills:
        errors.extend(check(skill_id, SKILLS_DIR))
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    if not errors:
        print(f"ok: {len(skills)} skills ({', '.join(skills)})")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
