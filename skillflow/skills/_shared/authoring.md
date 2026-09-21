# Authoring skills

A skill is a directory with one `SKILL.md` plus frontmatter. Pick the
smallest shape that fits. Declare it in frontmatter; `prose` is the default:

```yaml
---
name: my-skill
description: One sentence on what it does.
shape: prose
---
```

## The three shapes

**prose** — a quick guide with no ladder. The session reads `SKILL.md` and
follows it; nothing runs. Use for checklists, conventions, how-tos, and
reference material. There is no launcher command.

**single** — one gated node. The runner pauses once; the session does the
work and writes `final.md`; resume accepts it. Use when the work is one
unit: triage something, write something, decide something. Launcher:

```sh
python3 "<skills-root>/_shared/run.py" my-skill "<subject>" "<session-dir>"
```

**setup-execute** — two gated nodes. Node one is setup and levelset: read
the request and sources, state the goal, constraints, and plan, and write
`levelset.md`. Node two executes the plan and writes `final.md`. Use when
acting before aligning would waste work: migrations, investigations,
multi-part builds. Same launcher as `single`.

Rule of thumb: prose until skipping steps hurts, `single` until acting
before aligning hurts, `setup-execute` after that. The five shipped skills
use custom ladders with their own phases. New skills use one of the three
shapes above — run the `skill-dag` intake skill and it walks you through
shape choice, build, and proof. To propose a new ladder, contribute
upstream instead.

## Rules for a new skill

- Directory `<id>/` with one `SKILL.md`. The id is lowercase ASCII, digits,
  hyphens only — and it must match the frontmatter `name`.
- Frontmatter is `name` + one-sentence `description` + `shape`.
- Body stays thin: what it is, the launcher command (unless `prose`), and
  the record format. The procedure lives in the phases, never in prose.
- One session runs the DAG and authors every artifact. A gate records the
  artifact and stops when it is missing or unrevised. Never batch-author
  future phases.
- No mention of private systems, people, or history. Grep the draft for
  leaks before calling it done.

## Commands

```sh
skillflow new-skill my-skill --dir ./skills   # scaffold (guided without --shape)
skillflow init-skills --dir ./skills          # install/refresh the store; validates
```

Walk a DAG skill's gates in a scratch session before calling it done.
