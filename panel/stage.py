"""Stage boundaries and machine nodes for the panel DAGs.

One session runs the whole graph. Nothing here prompts a person or waits on
another session: a boundary node checks that the round's response artifact
exists, copies it into the session's internal store (`notes/round-N.md`) and
prints it so skillflow records the response on the node result.

A missing artifact is the stage boundary, not an error to hide: the run stops
with the round's instruction, the active session writes that response, and
reruns the DAG. The lens work stays staged without an `echo y` workaround.

A refusal is a legitimate stop with a trace: if the round's record is missing
but `refusal.md` exists, the refusal is stored, `converged.txt` records it,
and the rest of the graph drains as no-ops. Refusing is an output, not an
error.

Machine nodes (no session authorship):

- `activate` checks the round's activation worksheet exists and names every
  seated panelist — evidence the hydration pass happened before the room ran.
- `validity` checks the record carries a Validity Readback with every field
  non-empty. Setup is not success; the readback is the proof.
- `tensions --initial` checks the session distilled two to five tensions
  before the first seat — selection reads distilled tensions, never the raw
  subject.
- `tensions --record` extracts the record's `## New tensions` section and
  writes `tensions.txt` itself. The session never rewrites the material the
  chooser reads. Empty, missing, or unchanged tensions mean the round changed
  nothing: `converged.txt` records the stop, and the remaining graph drains.

`final` (the DAG's last node) collects every stored round response into
`final.md` — the final section — and prints it.

Usage:
    python3 panel/stage.py activate --skill debate --round 1 \\
        --room room-1.json --artifact activation-1.md --dir ./session1
    python3 panel/stage.py round --skill debate --round 2 \\
        --artifact record-2.md --refusal refusal.md \\
        --prompt "..." --dir ./session1
    python3 panel/stage.py validity --record record-2.md --dir ./session1
    python3 panel/stage.py tensions --initial --min 2 --max 5 --dir ./session1
    python3 panel/stage.py tensions --record record-2.md --dir ./session1
    python3 panel/stage.py final --skill debate --dir ./session1
"""

import argparse
import json
import os
import re
import sys

READBACK_FIELDS = [
    "collision_that_changed_answer",
    "claim_or_option_killed",
    "persona_flattening_check",
    "giggle_or_wince_line",
    "survivor_provenance",
]


def converged_path(session: str) -> str:
    return os.path.join(session, "converged.txt")


def is_converged(session: str) -> bool:
    return os.path.isfile(converged_path(session))


def mark_converged(session: str, reason: str) -> None:
    with open(converged_path(session), "w") as fh:
        fh.write(reason.rstrip() + "\n")


def notes_path(session: str, round_no: int) -> str:
    return os.path.join(session, "notes", f"round-{round_no}.md")


def store_round(session: str, skill: str, round_no: int, artifact: str,
                prompt: str, refusal: str = "refusal.md") -> int:
    if is_converged(session):
        print(f"converged; round {round_no} drained: "
              f"{open(converged_path(session)).read().strip()}")
        return 0
    path = os.path.join(session, artifact)
    text = None
    if os.path.isfile(path):
        with open(path) as fh:
            text = fh.read().strip()
        if not text:
            text = None
    if text is None:
        refusal_path = os.path.join(session, refusal) if refusal else None
        if refusal_path and os.path.isfile(refusal_path):
            with open(refusal_path) as fh:
                body = fh.read().strip()
            if body:
                store = os.path.join(session, "notes")
                os.makedirs(store, exist_ok=True)
                with open(notes_path(session, round_no), "w") as fh:
                    fh.write(f"REFUSED — round {round_no} of {skill}\n\n"
                             f"{body}\n")
                mark_converged(
                    session, f"refused at round {round_no} ({refusal})")
                print(f"round {round_no} refused; refusal stored in "
                      f"notes/round-{round_no}.md")
                print(body)
                return 0
        print(f"stage boundary: round {round_no} of {skill} has no response "
              f"yet", file=sys.stderr)
        print(f"missing: {path}", file=sys.stderr)
        if prompt:
            print(prompt, file=sys.stderr)
        print("write the response (or refusal.md to stop with a trace), "
              "then rerun the DAG in this same session", file=sys.stderr)
        return 1
    store = os.path.join(session, "notes")
    os.makedirs(store, exist_ok=True)
    with open(notes_path(session, round_no), "w") as fh:
        fh.write(text + "\n")
    # Printed so skillflow stores the response on the node result too.
    print(f"round {round_no} ({artifact}) stored in "
          f"notes/round-{round_no}.md")
    print(text)
    return 0


def stored_rounds(session: str) -> list:
    store = os.path.join(session, "notes")
    if not os.path.isdir(store):
        return []
    found = []
    for name in os.listdir(store):
        match = re.fullmatch(r"round-(\d+)\.md", name)
        if match:
            found.append((int(match.group(1)), os.path.join(store, name)))
    return sorted(found)


def write_final(session: str, skill: str) -> int:
    rounds = stored_rounds(session)
    if not rounds:
        print(f"error: no stored round responses for {skill} in {session}",
              file=sys.stderr)
        return 1
    lines = [f"# {skill} — final section", ""]
    subject_path = os.path.join(session, "subject.txt")
    if os.path.isfile(subject_path):
        with open(subject_path) as fh:
            subject = fh.read().strip()
        if subject:
            lines += [f"Subject: {subject}", ""]
    for round_no, path in rounds:
        with open(path) as fh:
            body = fh.read().strip()
        lines += [f"## Round {round_no}", "", body, ""]
    if is_converged(session):
        lines += [f"Stopped: {open(converged_path(session)).read().strip()}",
                  ""]
    final = "\n".join(lines).rstrip() + "\n"
    out_path = os.path.join(session, "final.md")
    with open(out_path, "w") as fh:
        fh.write(final)
    print(f"final section written to {out_path}")
    print(final)
    return 0


def seated_ids(session: str, room_file: str) -> list:
    if not os.path.isabs(room_file):
        room_file = os.path.join(session, room_file)
    with open(room_file) as fh:
        room = json.load(fh)["room"]
    return [(p["name"], p["id"]) for p in room]


def run_activate(session: str, skill: str, round_no: int, room: str,
                 artifact: str) -> int:
    if is_converged(session):
        print(f"converged; activation for round {round_no} drained")
        return 0
    worksheet = os.path.join(session, artifact)
    if not os.path.isfile(worksheet):
        print(f"stage boundary: round {round_no} of {skill} has no activation "
              f"worksheet yet", file=sys.stderr)
        print(f"missing: {worksheet}", file=sys.stderr)
        print("activate the seated room before it speaks: per panelist, "
              "history with the current state, first irritation, fault line, "
              "evidence standard, claim they would kill", file=sys.stderr)
        return 1
    with open(worksheet) as fh:
        text = fh.read()
    missing = [f"{name} ({pid})" for name, pid in seated_ids(session, room)
               if pid not in text and name not in text]
    if missing:
        print(f"stage boundary: activation worksheet does not name every "
              f"seated panelist", file=sys.stderr)
        print("missing: " + ", ".join(missing), file=sys.stderr)
        return 1
    print(f"round {round_no} activation checked against {room}: all seated "
          f"panelists present")
    return 0


def run_validity(session: str, record: str) -> int:
    if is_converged(session):
        print("converged; validity drained")
        return 0
    path = os.path.join(session, record)
    if not os.path.isfile(path):
        print(f"stage boundary: validity cannot read {record} — no record "
              f"yet", file=sys.stderr)
        return 1
    with open(path) as fh:
        text = fh.read()
    if "Validity Readback" not in text:
        print("stage boundary: record has no Validity Readback", file=sys.stderr)
        print("mechanical setup is not success: show the readback — "
              + ", ".join(READBACK_FIELDS), file=sys.stderr)
        return 1
    section = text.split("Validity Readback", 1)[1]
    missing = []
    for field in READBACK_FIELDS:
        m = re.search(rf"{field}\s*[=:]\s*(.+)", section)
        if not m or not m.group(1).strip(" -*:"):
            missing.append(field)
    if missing:
        print("stage boundary: Validity Readback fields empty: "
              + ", ".join(missing), file=sys.stderr)
        return 1
    print("validity readback present: all fields non-empty")
    return 0


def run_tensions_initial(session: str, minimum: int, maximum: int) -> int:
    if is_converged(session):
        print("converged; distill drained")
        return 0
    path = os.path.join(session, "tensions.txt")
    text = ""
    if os.path.isfile(path):
        with open(path) as fh:
            text = fh.read().strip()
    tensions = [t.strip() for t in text.split(",") if t.strip()]
    if len(tensions) < minimum or len(tensions) > maximum:
        print(f"stage boundary: tensions are not distilled yet "
              f"({len(tensions)} found, need {minimum}-{maximum})",
              file=sys.stderr)
        print(f"write {minimum}-{maximum} distilled tensions to tensions.txt "
              f"(comma-separated); the selector reads distilled tensions, "
              f"never the raw subject", file=sys.stderr)
        return 1
    print(f"tensions distilled: {len(tensions)}")
    return 0


def extract_new_tensions(text: str) -> list:
    m = re.search(r"##\s*New tensions\s*\n(.*?)(?=\n##\s|\Z)", text,
                  re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        item = line.strip(" -*").strip()
        if item:
            out.append(item)
    return out


def run_tensions_extract(session: str, record: str, round_no: int,
                         baseline: str = "tensions.txt") -> int:
    if is_converged(session):
        print(f"converged; tensions for round {round_no} drained")
        return 0
    path = os.path.join(session, record)
    if not os.path.isfile(path):
        print(f"stage boundary: cannot extract tensions from {record} — "
              f"no record yet", file=sys.stderr)
        return 1
    with open(path) as fh:
        text = fh.read()
    tensions = extract_new_tensions(text)
    if not tensions:
        print(f"round {round_no} named no new tensions; tensions carried "
              f"forward unchanged")
        return 0
    base = os.path.join(session, baseline)
    previous = ""
    if os.path.isfile(base):
        with open(base) as fh:
            previous = fh.read().strip()
    updated = ", ".join(tensions)
    if updated == previous:
        mark_converged(
            session, f"round {round_no} moved nothing its room was not "
                     f"already seated on")
        print(f"round {round_no} changed nothing; converged")
        return 0
    with open(os.path.join(session, "tensions.txt"), "w") as fh:
        fh.write(updated + "\n")
    print(f"tensions updated by machine from {record}: {updated}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage boundaries and machine nodes for panel DAGs.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("round", help="store one round's response")
    p.add_argument("--skill", required=True)
    p.add_argument("--round", type=int, required=True, dest="round_no")
    p.add_argument("--artifact", required=True,
                   help="response file the session writes for this round")
    p.add_argument("--refusal", default="refusal.md",
                   help="file that stops the debate with a trace")
    p.add_argument("--prompt", default="",
                   help="instruction shown when the response is missing")
    p.add_argument("--dir", default=".", help="session directory")

    p = sub.add_parser("final", help="write the final section of responses")
    p.add_argument("--skill", required=True)
    p.add_argument("--dir", default=".", help="session directory")

    p = sub.add_parser("activate",
                       help="check the activation worksheet seats everyone")
    p.add_argument("--skill", required=True)
    p.add_argument("--round", type=int, required=True, dest="round_no")
    p.add_argument("--room", required=True)
    p.add_argument("--artifact", required=True)
    p.add_argument("--dir", default=".", help="session directory")

    p = sub.add_parser("validity", help="check the record's Validity Readback")
    p.add_argument("--record", required=True)
    p.add_argument("--dir", default=".", help="session directory")

    p = sub.add_parser("tensions", help="check or extract tensions")
    p.add_argument("--initial", action="store_true",
                   help="check the distilled tensions before the first seat")
    p.add_argument("--record", default=None,
                   help="extract new tensions from this record")
    p.add_argument("--baseline", default="tensions.txt",
                   help="tensions file the round's room was seated on")
    p.add_argument("--round", type=int, default=None, dest="round_no")
    p.add_argument("--min", type=int, default=2, dest="minimum")
    p.add_argument("--max", type=int, default=5, dest="maximum")
    p.add_argument("--dir", default=".", help="session directory")

    args = parser.parse_args(argv)
    if args.command == "round":
        return store_round(args.dir, args.skill, args.round_no,
                           args.artifact, args.prompt, args.refusal)
    if args.command == "final":
        return write_final(args.dir, args.skill)
    if args.command == "activate":
        return run_activate(args.dir, args.skill, args.round_no, args.room,
                            args.artifact)
    if args.command == "validity":
        return run_validity(args.dir, args.record)
    if args.initial:
        return run_tensions_initial(args.dir, args.minimum, args.maximum)
    if args.record:
        return run_tensions_extract(args.dir, args.record, args.round_no or 0,
                                    args.baseline)
    print("error: tensions needs --initial or --record", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
