import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run_selector(db, *args):
    env = dict(os.environ, SKILLFLOW_DB=db)
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "select_room.py"), *args],
        capture_output=True, text=True, env=env,
    )
    return proc


class SelectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = os.path.join(cls.tmp.name, "test.db")
        env = dict(os.environ, SKILLFLOW_DB=cls.db)
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "seed.py")],
            capture_output=True, text=True, env=env,
        )
        assert proc.returncode == 0, proc.stderr

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_roster_loads(self):
        import sqlite3
        conn = sqlite3.connect(self.db)
        (count,) = conn.execute("SELECT COUNT(*) FROM panelists").fetchone()
        conn.close()
        self.assertGreater(count, 100)

    def test_matching_tensions_win(self):
        proc = run_selector(self.db, "--tensions", "threat,model,attacker")
        self.assertEqual(proc.returncode, 0)
        room = json.loads(proc.stdout)["room"]
        self.assertEqual(room[0]["name"], "Aisha Rahman")
        self.assertGreater(room[0]["score"], 0)

    def test_lens_text_scores(self):
        # "ruin" appears in a lens, not a tag list.
        proc = run_selector(self.db, "--tensions", "ruin")
        self.assertEqual(proc.returncode, 0)
        room = json.loads(proc.stdout)["room"]
        self.assertEqual(room[0]["name"], "Oscar Quintana")
        self.assertGreater(room[0]["score"], 0)

    def test_same_tensions_same_room(self):
        first = run_selector(self.db, "--tensions", "risk,measurement")
        second = run_selector(self.db, "--tensions", "measurement,risk")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(
            [p["id"] for p in json.loads(first.stdout)["room"]],
            [p["id"] for p in json.loads(second.stdout)["room"]])

    def test_fill_varies_by_tensions(self):
        first = run_selector(self.db, "--tensions", "risk")
        second = run_selector(self.db, "--tensions", "pricing,economics")
        room_a = {p["id"] for p in json.loads(first.stdout)["room"]}
        room_b = {p["id"] for p in json.loads(second.stdout)["room"]}
        self.assertNotEqual(room_a, room_b)

    def test_exclude_removes_members(self):
        first = run_selector(self.db, "--tensions", "risk")
        room_path = os.path.join(self.tmp.name, "room-1.json")
        with open(room_path, "w") as fh:
            fh.write(first.stdout)
        seated = {p["id"] for p in json.loads(first.stdout)["room"]}
        second = run_selector(
            self.db, "--tensions", "risk", "--exclude", room_path)
        self.assertEqual(second.returncode, 0)
        reseated = {p["id"] for p in json.loads(second.stdout)["room"]}
        self.assertTrue(seated.isdisjoint(reseated))

    def test_exclude_missing_file_rejected(self):
        proc = run_selector(self.db, "--tensions", "risk",
                            "--exclude", os.path.join(self.tmp.name, "nope.json"))
        self.assertEqual(proc.returncode, 2)

    def test_near_duplicates_not_seated_together(self):
        sys.path.insert(0, HERE)
        from select_room import select
        try:
            roster = [
                {"id": "a", "family": "risk", "lens": "", "attributes": [],
                 "tags": ["threat", "model", "attacker"]},
                {"id": "b", "family": "human", "lens": "", "attributes": [],
                 "tags": ["threat", "model", "stranger"]},
                {"id": "c", "family": "clarity", "lens": "", "attributes": [],
                 "tags": ["docs", "wording"]},
                {"id": "d", "family": "measure", "lens": "", "attributes": [],
                 "tags": ["metrics", "proof"]},
            ]
            room = select(roster, ["threat", "model"], 3)
            ids = [p["id"] for p in room]
            self.assertIn("a", ids)
            self.assertNotIn("b", ids)
        finally:
            sys.path.remove(HERE)

    def test_diversity_one_per_family(self):
        proc = run_selector(self.db, "--tensions", "risk", "--size", "5")
        self.assertEqual(proc.returncode, 0)
        room = json.loads(proc.stdout)["room"]
        families = [p["family"] for p in room]
        self.assertEqual(len(families), len(set(families)))

    def test_diversity_fills_beyond_matches(self):
        proc = run_selector(self.db, "--tensions", "threat,model,attacker",
                            "--size", "4")
        self.assertEqual(proc.returncode, 0)
        room = json.loads(proc.stdout)["room"]
        self.assertEqual(len(room), 4)
        self.assertEqual(len({p["family"] for p in room}), 4)

    def test_size_bounds_rejected(self):
        self.assertEqual(
            run_selector(self.db, "--tensions", "x", "--size", "2").returncode, 2)
        self.assertEqual(
            run_selector(self.db, "--tensions", "x", "--size", "6").returncode, 2)

    def test_out_file(self):
        out = os.path.join(self.tmp.name, "room.json")
        proc = run_selector(self.db, "--tensions", "risk", "--out", out)
        self.assertEqual(proc.returncode, 0)
        with open(out) as fh:
            room = json.load(fh)["room"]
        self.assertTrue(room)
        self.assertIn("name", room[0])

    def test_unseeded_db_rejected(self):
        empty = os.path.join(self.tmp.name, "empty.db")
        open(empty, "w").close()
        proc = run_selector(empty, "--tensions", "risk")
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
