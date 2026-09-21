"""Seed the panelists table in a skillflow session DB.

The roster lives in the DB, not in a doc: same SQLite file as the DAG,
separate table. panelists.json is only the seed source.

Usage:
    SKILLFLOW_DB=./session1/skillflow.db python3 -m skillflow.panel.seed
"""

import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

SCHEMA = """
CREATE TABLE IF NOT EXISTS panelists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    lens TEXT NOT NULL,
    attributes TEXT NOT NULL,
    family TEXT NOT NULL,
    tags TEXT NOT NULL,
    seated INTEGER NOT NULL DEFAULT 0
);
"""


def seed(db_path: str, source: str) -> int:
    with open(source) as fh:
        panelists = json.load(fh)["panelists"]
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        names = [row[1] for row in
                 conn.execute("PRAGMA table_info(panelists)")]
        if "seated" not in names:
            conn.execute("ALTER TABLE panelists "
                         "ADD COLUMN seated INTEGER NOT NULL DEFAULT 0")
        conn.executemany(
            "INSERT INTO panelists "
            "(id, name, lens, attributes, family, tags, seated) "
            "VALUES (?, ?, ?, ?, ?, ?, 0) "
            "ON CONFLICT(id) DO UPDATE SET "
            "name = excluded.name, lens = excluded.lens, "
            "attributes = excluded.attributes, family = excluded.family, "
            "tags = excluded.tags",
            [(p["id"], p["name"], p["lens"],
              json.dumps(p["attributes"]), p["family"],
              json.dumps(p["tags"])) for p in panelists],
        )
        conn.commit()
        return len(panelists)
    finally:
        conn.close()


def main(argv=None) -> int:
    db_path = os.environ.get("SKILLFLOW_DB")
    if not db_path:
        print("error: SKILLFLOW_DB is not set", file=sys.stderr)
        return 2
    source = os.path.join(HERE, "panelists.json")
    try:
        count = seed(db_path, source)
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(f"error: cannot seed panelists: {exc}", file=sys.stderr)
        return 2
    print(f"seeded {count} panelists into {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
