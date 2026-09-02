"""One scrutiny, and a moved number that has to explain itself."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import demonstrate  # noqa: E402
from dokimasia_lib import reconcile  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "workbook_build", PLUGIN / "tests" / "fixtures" / "workbooks" / "build.py"
)
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

APPLICATION = {"label": "tests/fixtures/app", "commit": "a" * 40}
EVIDENCE = PLUGIN / "docs" / "evidence"

# The pinned inputs are deliberately not in this repository: the application is
# another repository at a pinned commit, and the reviewed workbook holds a
# reviewer's prose, which the phylax boundary keeps out of this tree. Point
# these at a checkout and a workbook to run the pinned regeneration test.
PINNED_APP = os.environ.get("DOKIMASIA_PINNED_APP")
PINNED_WORKBOOK = os.environ.get("DOKIMASIA_PINNED_WORKBOOK")
PINNED_COMMIT = "bb9685fb7dbe9cd2f5b7683a9b3f164509dc2de9"


class ScrutinyCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.made = build.build_all(Path(self.tmp.name))
        self.app = PLUGIN / "tests" / "fixtures" / "app"

    def run_one(self, workbook=None, version="0.0.0-fixture", application=None):
        return demonstrate.scrutinise(
            self.app,
            workbook or self.made["benign.xlsx"],
            version,
            application or APPLICATION,
        )


class Deterministic(ScrutinyCase):
    def test_two_scrutinies_of_the_same_inputs_agree(self):
        first, _ = self.run_one()
        second, _ = self.run_one()
        self.assertEqual(
            demonstrate.scrutiny_digest(first), demonstrate.scrutiny_digest(second)
        )
        self.assertEqual(demonstrate.causes(first, second), [])

    def test_the_digest_excludes_the_timing_because_timing_is_measured(self):
        first, _ = self.run_one()
        slower = json.loads(json.dumps(first))
        slower["timing"]["observed_ms"] = first["timing"]["observed_ms"] + 5_000
        self.assertEqual(
            demonstrate.scrutiny_digest(first), demonstrate.scrutiny_digest(slower)
        )


class MovedIdentityNamesItsCause(ScrutinyCase):
    """Study question 4: a moved number has one of three explanations."""

    def test_a_moved_application_commit_is_reported_as_its_own_cause(self):
        first, _ = self.run_one()
        moved, _ = self.run_one(
            application={**APPLICATION, "commit": "b" * 40}
        )
        found = demonstrate.causes(first, moved)
        self.assertEqual([entry["cause"] for entry in found], ["application"])
        self.assertEqual(found[0]["from"], "a" * 40)
        self.assertEqual(found[0]["to"], "b" * 40)

    def test_a_moved_workbook_is_reported_as_its_own_cause(self):
        first, _ = self.run_one()
        moved, _ = self.run_one(workbook=self.made["absolute-targets.xlsx"])
        self.assertEqual(
            [entry["cause"] for entry in demonstrate.causes(first, moved)],
            ["workbook"],
        )

    def test_a_moved_skill_version_is_reported_as_its_own_cause(self):
        first, _ = self.run_one()
        moved, _ = self.run_one(version="9.9.9-fixture")
        found = demonstrate.causes(first, moved)
        self.assertEqual([entry["cause"] for entry in found], ["skill"])
        self.assertEqual(found[0]["to"], "9.9.9-fixture")

    def test_two_identities_moving_are_reported_separately(self):
        first, _ = self.run_one()
        moved, _ = self.run_one(
            version="9.9.9-fixture", application={**APPLICATION, "commit": "c" * 40}
        )
        self.assertEqual(
            sorted(entry["cause"] for entry in demonstrate.causes(first, moved)),
            ["application", "skill"],
        )

    def test_a_result_that_moved_with_nothing_moved_is_reported_not_hidden(self):
        """A number nobody can explain is what this record exists to prevent."""
        first, _ = self.run_one()
        forged = json.loads(json.dumps(first))
        forged["examined"]["coverage_sha256"] = "f" * 64
        found = demonstrate.causes(first, forged)
        self.assertEqual([entry["cause"] for entry in found], ["unattributed"])


class MalformedRecords(ScrutinyCase):
    """Comparing scrutinies means reading one off disk, so it can be malformed.

    Every other refusal in this plugin is named. A `KeyError` here would be the
    one that is not.
    """

    def test_a_record_missing_a_field_refuses_by_name(self):
        first, _ = self.run_one()
        for field in ("skill_version", "subject", "examined"):
            with self.subTest(field=field):
                broken = json.loads(json.dumps(first))
                broken.pop(field)
                with self.assertRaises(demonstrate.DemonstrationError) as caught:
                    demonstrate.causes(first, broken)
                self.assertIn(field, str(caught.exception))
                self.assertIn("later", str(caught.exception))

    def test_a_record_with_no_application_commit_refuses_by_name(self):
        first, _ = self.run_one()
        broken = json.loads(json.dumps(first))
        broken["subject"]["application"].pop("commit")
        with self.assertRaises(demonstrate.DemonstrationError) as caught:
            demonstrate.causes(broken, first)
        self.assertIn("no commit", str(caught.exception))
        self.assertIn("earlier", str(caught.exception))

    def test_a_record_with_no_coverage_digest_refuses_by_name(self):
        first, _ = self.run_one()
        broken = json.loads(json.dumps(first))
        broken["examined"].pop("coverage_sha256")
        with self.assertRaises(demonstrate.DemonstrationError) as caught:
            demonstrate.causes(first, broken)
        self.assertIn("no coverage digest", str(caught.exception))

    def test_a_blank_identity_in_both_records_still_reports_the_move(self):
        """Degrading to unattributed is the safe direction, and is required."""
        first, _ = self.run_one()
        a = json.loads(json.dumps(first))
        b = json.loads(json.dumps(first))
        a["subject"]["workbook"]["sha256"] = ""
        b["subject"]["workbook"]["sha256"] = ""
        b["examined"]["coverage_sha256"] = "f" * 64
        self.assertEqual(
            [entry["cause"] for entry in demonstrate.causes(a, b)], ["unattributed"]
        )


class Timing(ScrutinyCase):
    def test_the_record_states_a_measured_duration_and_not_the_budget(self):
        first, _ = self.run_one()
        timing = first["timing"]
        self.assertEqual(timing["budget_ms"], demonstrate.BUDGET_MS)
        self.assertNotEqual(
            timing["observed_ms"], timing["budget_ms"],
            "the observed duration is the budget, so it was not measured",
        )
        self.assertGreaterEqual(timing["observed_ms"], 0)
        self.assertLess(timing["observed_ms"], timing["budget_ms"])
        self.assertTrue(timing["within_budget"])


class StatedFieldsAreSeparate(ScrutinyCase):
    """The runbook asks for these three as fields, not as one derived number."""

    def test_the_closure_ratio_scoped_count_and_gap_count_are_separate_fields(self):
        first, coverage = self.run_one()
        self.assertIn("closure_ratio", first)
        self.assertEqual(
            sorted(first["closure_ratio"]),
            ["closed", "denominator", "numerator", "value"],
        )
        self.assertEqual(first["examined"]["scoped"], coverage["counts"]["scoped"])
        self.assertEqual(first["gaps"], len(coverage["gaps"]))
        self.assertEqual(first["undisposed"], len(coverage["undisposed"]))

    def test_the_scrutiny_names_every_identity_a_move_could_be_blamed_on(self):
        first, _ = self.run_one()
        self.assertEqual(
            sorted(demonstrate.identity(first)), ["application", "skill", "workbook"]
        )
        for value in demonstrate.identity(first).values():
            self.assertTrue(value, "an identity is blank, so a move could not be named")

    def test_an_application_commit_that_is_not_pinned_refuses(self):
        with self.assertRaises(demonstrate.DemonstrationError) as caught:
            demonstrate.scrutinise(
                self.app, self.made["benign.xlsx"], "0.0.0-fixture",
                {"label": "x", "commit": "bb9685fb"},
            )
        self.assertIn("not a full 40-character", str(caught.exception))


class RenderedProse(ScrutinyCase):
    def test_the_prose_states_the_commit_the_denominator_and_the_boundary(self):
        first, coverage = self.run_one()
        prose = demonstrate.render(first, coverage)
        self.assertIn(APPLICATION["commit"], prose)
        self.assertIn(str(first["closure_ratio"]["denominator"]), prose)
        self.assertIn("does not", prose.split("## What was examined")[0])
        self.assertNotIn("passed the", prose)

    def test_the_prose_regenerates_byte_for_byte(self):
        first, coverage = self.run_one()
        second, coverage_two = self.run_one()
        self.assertEqual(
            demonstrate.render(first, coverage),
            demonstrate.render(second, coverage_two),
        )


class CommittedEvidence(unittest.TestCase):
    """The pinned evidence is checkable without the inputs it was made from."""

    def setUp(self):
        self.coverage_path = EVIDENCE / "wildcat-app-v2.coverage.json"
        self.prose_path = EVIDENCE / "wildcat-app-v2-scrutiny.md"

    def test_the_committed_evidence_is_present(self):
        self.assertTrue(self.coverage_path.is_file())
        self.assertTrue(self.prose_path.is_file())

    def test_the_committed_record_agrees_with_its_own_counts(self):
        record = reconcile.read_json(self.coverage_path)
        ratio = record["closure_ratio"]
        counts = record["counts"]
        self.assertEqual(ratio["denominator"], counts["scoped"])
        self.assertEqual(ratio["numerator"], counts["disposed"])
        self.assertEqual(counts["disposed"] + counts["undisposed"], counts["scoped"])
        self.assertEqual(
            counts["inventory_items"] + counts["workbook_cases"], counts["scoped"]
        )

    def test_the_committed_prose_reports_the_record_beside_it(self):
        record = reconcile.read_json(self.coverage_path)
        prose = self.prose_path.read_text(encoding="utf-8")
        self.assertIn(str(record["counts"]["scoped"]), prose)
        self.assertIn(str(record["counts"]["inventory_items"]), prose)
        self.assertIn(str(record["counts"]["workbook_cases"]), prose)
        self.assertIn(PINNED_COMMIT, prose)

    def test_the_committed_prose_names_every_digest_its_record_carries(self):
        """The renderer abbreviates each digest, so compare the same prefix."""
        record = reconcile.read_json(self.coverage_path)
        prose = self.prose_path.read_text(encoding="utf-8")
        for field in ("inventory_sha256", "workbook_sha256"):
            short = record["subject"][field][:12]
            self.assertTrue(short)
            self.assertIn(short, prose, f"the prose does not name the {field}")

    def test_the_committed_scrutiny_names_its_producer(self):
        """Study question 4, machine-readably rather than only in the prose.

        The coverage record names the two digests it was built from and nothing
        about what built it. Next release's comparison is a program reading
        these files, so the attribution has to be in one of them.
        """
        scrutiny = reconcile.read_json(EVIDENCE / "wildcat-app-v2.scrutiny.json")
        self.assertEqual(
            scrutiny["subject"]["application"]["commit"], PINNED_COMMIT
        )
        self.assertTrue(scrutiny["skill_version"])
        self.assertTrue(scrutiny["subject"]["workbook"]["sha256"])
        self.assertNotIn(
            "timing", scrutiny, "the committed scrutiny carries a measured value"
        )
        self.assertEqual(len(scrutiny["scrutiny_sha256"]), 64)

    def test_the_committed_scrutiny_agrees_with_the_coverage_beside_it(self):
        from dokimasia_lib import reconcile as reconcile_lib

        scrutiny = reconcile.read_json(EVIDENCE / "wildcat-app-v2.scrutiny.json")
        record = reconcile.read_json(self.coverage_path)
        self.assertEqual(
            scrutiny["examined"]["coverage_sha256"],
            reconcile_lib.coverage_digest(record),
        )
        self.assertEqual(scrutiny["examined"]["scoped"], record["counts"]["scoped"])

    def test_a_later_scrutiny_can_be_compared_against_the_committed_one(self):
        """The committed record is usable as the earlier side of a comparison."""
        scrutiny = reconcile.read_json(EVIDENCE / "wildcat-app-v2.scrutiny.json")
        later = json.loads(json.dumps(scrutiny))
        later["subject"]["application"]["commit"] = "d" * 40
        later["examined"]["coverage_sha256"] = "e" * 64
        found = demonstrate.causes(scrutiny, later)
        self.assertEqual([entry["cause"] for entry in found], ["application"])
        self.assertEqual(found[0]["from"], PINNED_COMMIT)

    def test_the_committed_record_carries_no_workbook_prose(self):
        """The phylax boundary: identifiers may be committed, rows may not."""
        record = reconcile.read_json(self.coverage_path)
        blob = json.dumps(record)
        for key in ("Test step", "Expected result", "Comments", "Tx hash", "Tester"):
            self.assertNotIn(key, blob, f"a workbook column name reached the record")
        for entry in record["undisposed"]:
            self.assertLess(
                len(entry), 200, "an undisposed entry is long enough to be prose"
            )

    @unittest.skipUnless(
        PINNED_APP and PINNED_WORKBOOK,
        "set DOKIMASIA_PINNED_APP and DOKIMASIA_PINNED_WORKBOOK to regenerate "
        "the pinned evidence; neither input lives in this repository",
    )
    def test_the_committed_evidence_regenerates_from_the_pinned_inputs(self):
        scrutiny, coverage = demonstrate.scrutinise(
            Path(PINNED_APP), Path(PINNED_WORKBOOK),
            "1.1.0", {"label": "wildcat-app-v2", "commit": PINNED_COMMIT},
        )
        self.assertEqual(
            json.dumps(coverage, indent=2, sort_keys=True) + "\n",
            self.coverage_path.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            demonstrate.render(scrutiny, coverage),
            self.prose_path.read_text(encoding="utf-8"),
        )


class EvidenceRootIsDeclared(ScrutinyCase):
    """A label names a file under the declared root and may not leave it."""

    def test_a_label_carrying_a_parent_reference_refuses(self):
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "dokimasia.py"), "demonstrate",
             "--app", str(self.app), "--workbook", str(self.made["benign.xlsx"]),
             "--commit", "a" * 40, "--label", "../../../../tmp/escaped",
             "--write-evidence"],
            capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("not one safe path segment", result.stderr)
        self.assertFalse(
            (PLUGIN.parents[1] / "tmp" / "escaped.coverage.json").exists()
        )

    def test_a_label_carrying_a_separator_refuses(self):
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "dokimasia.py"), "demonstrate",
             "--app", str(self.app), "--workbook", str(self.made["benign.xlsx"]),
             "--commit", "a" * 40, "--label", "nested/name", "--write-evidence"],
            capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("not one safe path segment", result.stderr)


class CommandSurface(unittest.TestCase):
    def test_the_demonstrate_verb_is_built_and_self_checks(self):
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "dokimasia.py"),
             "demonstrate", "--check"],
            capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check clean", result.stdout)

    def test_the_verb_refuses_without_its_inputs(self):
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "dokimasia.py"), "demonstrate"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("refused", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_report_timing_writes_a_measured_duration_to_standard_error(self):
        with tempfile.TemporaryDirectory() as raw:
            made = build.build_all(Path(raw))
            result = subprocess.run(
                [sys.executable, str(PLUGIN / "scripts" / "dokimasia.py"),
                 "demonstrate",
                 "--app", str(PLUGIN / "tests" / "fixtures" / "app"),
                 "--workbook", str(made["benign.xlsx"]),
                 "--commit", "a" * 40, "--label", "fixture", "--report-timing"],
                capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("timing: observed", result.stderr)
            self.assertIn(f"{demonstrate.BUDGET_MS}ms budget", result.stderr)
            self.assertIn("within budget: yes", result.stderr)


class ContractCheck(unittest.TestCase):
    def test_the_bundled_check_passes(self):
        self.assertEqual(demonstrate.check(), [])


if __name__ == "__main__":
    unittest.main()
