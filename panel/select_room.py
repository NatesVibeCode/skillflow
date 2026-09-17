"""Select a panel room by semantic tag match with enforced diversity.

Reads the panelists table from the skillflow session DB (SKILLFLOW_DB),
ranks panelists by token-overlap between the situation's tensions and each
panelist's tags, then enforces diversity: at most one panelist per family,
three to five seats. Score proposes; diversity disposes.

Usage:
    SKILLFLOW_DB=./session1/skillflow.db python3 select_room.py --tensions risk,measurement
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys

MIN_SEATS, MAX_SEATS = 3, 5


def tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def score(tensions: list, panelist: dict) -> int:
    tension_tokens = set()
    for t in tensions:
        tension_tokens |= tokens(t)
    if not tension_tokens:
        return 0
    hits = 0
    for tag in panelist["tags"]:
        hits += 2 * len(tokens(tag) & tension_tokens)
    body = panelist["lens"] + " " + " ".join(panelist["attributes"])
    hits += len(tokens(body) & tension_tokens)
    return hits


def stable_salt(pid: str, tensions: list) -> str:
    blob = pid + "\x00" + ",".join(sorted(tensions))
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


def tag_tokens(panelist: dict) -> set:
    out = set()
    for tag in panelist["tags"]:
        out |= tokens(tag)
    return out


def select(panelists: list, tensions: list, size: int,
           excluded: set | None = None) -> list:
    excluded = excluded or set()
    scored = [(score(tensions, p), p) for p in panelists
              if p["id"] not in excluded]
    ranked = sorted(
        scored,
        key=lambda item: (-item[0], stable_salt(item[1]["id"], tensions)),
    )
    # Two passes: strict (no near-duplicate tag sets), then relaxed to fill.
    room, used_families, seated_tags = [], set(), set()
    for candidate in _pass(ranked, size, used_families, seated_tags,
                           strict=True):
        room.append(candidate)
    for candidate in _pass(ranked, size - len(room), used_families,
                           seated_tags, strict=False):
        room.append(candidate)
    return room


def _pass(ranked, size, used_families, seated_tags, strict):
    picked = []
    for _, candidate in ranked:
        if len(picked) >= size:
            break
        if candidate["family"] in used_families:
            continue
        mine = tag_tokens(candidate)
        if strict and len(mine & seated_tags) >= 2:
            continue
        picked.append(candidate)
        used_families.add(candidate["family"])
        seated_tags |= mine
    return picked


def load_panelists(db: str) -> list:
    conn = sqlite3.connect(db)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, name, lens, attributes, family, tags FROM panelists"
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        raise ValueError("panelists table is empty (run seed.py first?)")
    return [
        {"id": r["id"], "name": r["name"], "lens": r["lens"],
         "attributes": json.loads(r["attributes"]), "family": r["family"],
         "tags": json.loads(r["tags"])}
        for r in rows
    ]


def load_excluded(paths: list) -> set:
    excluded = set()
    for path in paths:
        with open(path) as fh:
            data = json.load(fh)
        room = data.get("room", data if isinstance(data, list) else [])
        for entry in room:
            if isinstance(entry, dict) and "id" in entry:
                excluded.add(entry["id"])
            elif isinstance(entry, str):
                excluded.add(entry)
    return excluded


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Select a panel room.")
    parser.add_argument("--tensions", default="",
                        help="comma-separated situation tensions")
    parser.add_argument("--size", type=int, default=4)
    parser.add_argument("--db", default=os.environ.get("SKILLFLOW_DB"),
                        help="skillflow session DB (default: $SKILLFLOW_DB)")
    parser.add_argument("--out", default=None, help="write room JSON here")
    parser.add_argument("--exclude", action="append", default=[],
                        help="room.json whose members to exclude (repeatable)")
    args = parser.parse_args(argv)

    if not (MIN_SEATS <= args.size <= MAX_SEATS):
        print(f"error: --size must be {MIN_SEATS}-{MAX_SEATS}", file=sys.stderr)
        return 2
    if not args.db:
        print("error: no session DB; set SKILLFLOW_DB or pass --db",
              file=sys.stderr)
        return 2
    try:
        panelists = load_panelists(args.db)
    except (sqlite3.Error, ValueError) as exc:
        print(f"error: cannot load panelists (run seed.py first?): {exc}",
              file=sys.stderr)
        return 2

    tensions = [t.strip() for t in args.tensions.split(",") if t.strip()]
    try:
        excluded = load_excluded(args.exclude)
    except (OSError, ValueError) as exc:
        print(f"error: cannot load --exclude file: {exc}", file=sys.stderr)
        return 2
    room = select(panelists, tensions, args.size, excluded)
    result = {
        "tensions": tensions,
        "room": [
            {"name": p["name"], "id": p["id"], "family": p["family"],
             "lens": p["lens"], "score": score(tensions, p)}
            for p in room
        ],
    }
    text = json.dumps(result, indent=2)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
