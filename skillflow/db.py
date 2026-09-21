"""SQLite schema and connection handling for skillflow."""

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    cmd      TEXT NOT NULL DEFAULT '',
    timeout_s REAL,
    env      TEXT,
    cwd      TEXT
);
CREATE TABLE IF NOT EXISTS edges (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_id   INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    UNIQUE (from_id, to_id),
    CHECK (from_id != to_id)
);
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    status      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS node_results (
    run_id      INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    node_id     INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    status      TEXT NOT NULL,
    exit_code   INTEGER,
    output      TEXT NOT NULL DEFAULT '',
    started_at  TEXT,
    finished_at TEXT,
    PRIMARY KEY (run_id, node_id)
);
"""


#: Columns added after 0.1.0; existing databases gain them on connect.
MIGRATIONS = (
    ("nodes", "timeout_s", "REAL"),
    ("nodes", "env", "TEXT"),
    ("nodes", "cwd", "TEXT"),
)


def _migrate(conn: sqlite3.Connection) -> None:
    for table, column, decltype in MIGRATIONS:
        names = [row["name"] for row in
                 conn.execute(f"PRAGMA table_info({table})")]
        if column not in names:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decltype}")


def connect(path: str, timeout: float = 30.0) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()
    return conn
