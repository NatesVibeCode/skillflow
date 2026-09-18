import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "panel"))

import stage  # noqa: E402


class StageRoundTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = self.tmp.name
        self.artifact = os.path.join(self.session, "field.md")

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_response_is_a_stage_boundary(self):
        rc = stage.store_round(
            self.session, "brainstorm", 1, "field.md", "Open the field."
        )
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(stage.notes_path(self.session, 1)))

    def test_empty_response_is_a_stage_boundary(self):
        open(self.artifact, "w").close()
        rc = stage.store_round(
            self.session, "brainstorm", 1, "field.md", "Open the field."
        )
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(stage.notes_path(self.session, 1)))

    def test_response_is_stored_internally(self):
        with open(self.artifact, "w") as fh:
            fh.write("Approach A\n")
        rc = stage.store_round(
            self.session, "brainstorm", 1, "field.md", "Open the field."
        )
        self.assertEqual(rc, 0)
        with open(stage.notes_path(self.session, 1)) as fh:
            self.assertEqual(fh.read(), "Approach A\n")


class StageFinalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = self.tmp.name
        with open(os.path.join(self.session, "subject.txt"), "w") as fh:
            fh.write("name the engine\n")

    def tearDown(self):
        self.tmp.cleanup()

    def _store(self, round_no, artifact, text):
        with open(os.path.join(self.session, artifact), "w") as fh:
            fh.write(text)
        self.assertEqual(
            stage.store_round(self.session, "brainstorm", round_no, artifact,
                              "prompt"),
            0,
        )

    def test_final_section_collects_rounds_in_order(self):
        self._store(1, "field.md", "approach one")
        self._store(2, "record.md", "survivor: approach one")
        rc = stage.write_final(self.session, "brainstorm")
        self.assertEqual(rc, 0)
        with open(os.path.join(self.session, "final.md")) as fh:
            final = fh.read()
        self.assertIn("final section", final)
        self.assertIn("Subject: name the engine", final)
        self.assertLess(final.index("## Round 1"), final.index("## Round 2"))
        self.assertIn("approach one", final)
        self.assertIn("survivor: approach one", final)

    def test_final_without_responses_fails(self):
        self.assertEqual(stage.write_final(self.session, "brainstorm"), 1)
        self.assertFalse(
            os.path.exists(os.path.join(self.session, "final.md"))
        )


class StageActivateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = self.tmp.name
        with open(os.path.join(self.session, "room-1.json"), "w") as fh:
            json.dump({"room": [
                {"name": "Ada Cone", "id": "ada_cone"},
                {"name": "Bram Oz", "id": "bram_oz"},
            ]}, fh)

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_worksheet_is_a_boundary(self):
        rc = stage.run_activate(self.session, "debate", 1, "room-1.json",
                                "activation-1.md")
        self.assertEqual(rc, 1)

    def test_worksheet_must_name_every_seated_panelist(self):
        with open(os.path.join(self.session, "activation-1.md"), "w") as fh:
            fh.write("Ada Cone: first irritation — the field is thin.\n")
        rc = stage.run_activate(self.session, "debate", 1, "room-1.json",
                                "activation-1.md")
        self.assertEqual(rc, 1)

    def test_full_worksheet_passes(self):
        with open(os.path.join(self.session, "activation-1.md"), "w") as fh:
            fh.write("Ada Cone: irritation.\nBram Oz (bram_oz): irritation.\n")
        rc = stage.run_activate(self.session, "debate", 1, "room-1.json",
                                "activation-1.md")
        self.assertEqual(rc, 0)


class StageValidityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def _record(self, text):
        with open(os.path.join(self.session, "record-1.md"), "w") as fh:
            fh.write(text)

    def test_missing_readback_fails(self):
        self._record("a collision happened\n")
        self.assertEqual(stage.run_validity(self.session, "record-1.md"), 1)

    def test_empty_field_fails(self):
        self._record(
            "## Validity Readback\n"
            "- collision_that_changed_answer: the exchange\n"
            "- claim_or_option_killed: the claim\n"
            "- persona_flattening_check: voices forced deaths\n"
            "- giggle_or_wince_line: the line\n"
            "- survivor_provenance:\n")
        self.assertEqual(stage.run_validity(self.session, "record-1.md"), 1)

    def test_full_readback_passes(self):
        self._record(
            "## Validity Readback\n"
            "- collision_that_changed_answer: the exchange\n"
            "- claim_or_option_killed: the claim\n"
            "- persona_flattening_check: voices forced deaths\n"
            "- giggle_or_wince_line: the line\n"
            "- survivor_provenance: the objection\n")
        self.assertEqual(stage.run_validity(self.session, "record-1.md"), 0)


class StageTensionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_initial_rejects_raw_subject(self):
        with open(os.path.join(self.session, "tensions.txt"), "w") as fh:
            fh.write("the stage-boundary rewrite is worse than the original\n")
        self.assertEqual(stage.run_tensions_initial(self.session, 2, 5), 1)

    def test_initial_accepts_distilled_tensions(self):
        with open(os.path.join(self.session, "tensions.txt"), "w") as fh:
            fh.write("independence of the checker, legitimate stopping\n")
        self.assertEqual(stage.run_tensions_initial(self.session, 2, 5), 0)

    def test_missing_section_carries_tensions_forward(self):
        with open(os.path.join(self.session, "tensions.txt"), "w") as fh:
            fh.write("independence, stopping\n")
        with open(os.path.join(self.session, "record-1.md"), "w") as fh:
            fh.write("a record without new tensions\n")
        self.assertEqual(
            stage.run_tensions_extract(self.session, "record-1.md", 1), 0)
        self.assertFalse(stage.is_converged(self.session))
        with open(os.path.join(self.session, "tensions.txt")) as fh:
            self.assertEqual(fh.read().strip(), "independence, stopping")

    def test_unchanged_tensions_converge(self):
        with open(os.path.join(self.session, "tensions.txt"), "w") as fh:
            fh.write("independence, stopping\n")
        with open(os.path.join(self.session, "record-1.md"), "w") as fh:
            fh.write("## New tensions\n- independence\n- stopping\n")
        self.assertEqual(
            stage.run_tensions_extract(self.session, "record-1.md", 1), 0)
        self.assertTrue(stage.is_converged(self.session))

    def test_new_tensions_are_written_by_machine(self):
        with open(os.path.join(self.session, "tensions.txt"), "w") as fh:
            fh.write("independence, stopping\n")
        with open(os.path.join(self.session, "record-1.md"), "w") as fh:
            fh.write("## New tensions\n- refusal affordance\n- weak material\n")
        self.assertEqual(
            stage.run_tensions_extract(self.session, "record-1.md", 1), 0)
        with open(os.path.join(self.session, "tensions.txt")) as fh:
            self.assertEqual(
                fh.read().strip(),
                "refusal affordance, weak material")

    def test_convergence_is_measured_against_the_rounds_baseline(self):
        # On a rerun, the round's own previous output must not count as
        # "unchanged": convergence means the record moved nothing relative
        # to what its room was seated on.
        with open(os.path.join(self.session, "tensions.txt"), "w") as fh:
            fh.write("refusal affordance, weak material\n")
        with open(os.path.join(self.session, "used-1.txt"), "w") as fh:
            fh.write("independence, stopping\n")
        with open(os.path.join(self.session, "record-1.md"), "w") as fh:
            fh.write("## New tensions\n- refusal affordance\n"
                     "- weak material\n")
        self.assertEqual(
            stage.run_tensions_extract(self.session, "record-1.md", 1,
                                       baseline="used-1.txt"), 0)
        self.assertFalse(stage.is_converged(self.session))


class StageRefusalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.session = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_refusal_is_a_legitimate_stop(self):
        with open(os.path.join(self.session, "refusal.md"), "w") as fh:
            fh.write("the room refuses: the work is not ready\n")
        rc = stage.store_round(self.session, "debate", 2, "record-2.md",
                               "Collide.")
        self.assertEqual(rc, 0)
        with open(stage.notes_path(self.session, 2)) as fh:
            self.assertIn("REFUSED", fh.read())
        self.assertTrue(stage.is_converged(self.session))
        self.assertIn("refused at round 2",
                      open(stage.converged_path(self.session)).read())

    def test_refusal_is_not_hidden_behind_a_record(self):
        with open(os.path.join(self.session, "record-2.md"), "w") as fh:
            fh.write("the claim moved\n")
        rc = stage.store_round(self.session, "debate", 2, "record-2.md",
                               "Collide.")
        self.assertEqual(rc, 0)
        self.assertFalse(stage.is_converged(self.session))

    def test_converged_round_drains(self):
        stage.mark_converged(self.session, "round 1 left tensions unchanged")
        rc = stage.store_round(self.session, "debate", 2, "record-2.md",
                               "Collide.")
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(stage.notes_path(self.session, 2)))


if __name__ == "__main__":
    unittest.main()
