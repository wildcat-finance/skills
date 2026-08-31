"""What an import keeps, what a split owes its source, and the round trip."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import workbook, xlsx  # noqa: E402

SCHEMA = json.loads((PLUGIN / "schemas" / "workbook-v1.json").read_text(encoding="utf-8"))
_spec = importlib.util.spec_from_file_location(
    "dokimasia_workbook_fixtures", PLUGIN / "tests" / "fixtures" / "workbooks" / "build.py"
)
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


class ImportCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.made = build.build_all(Path(self.tmp.name))
        self.cases = workbook.read_cases(self.made["benign.xlsx"])

    def case(self, identifier):
        return next(c for c in self.cases if c["id"] == identifier)


class LineageTests(ImportCase):
    def test_a_case_keeps_the_sheet_and_row_it_came_from(self):
        case = self.case("ADM-01")
        self.assertEqual(case["sheet"], "1 Admin")
        self.assertIsInstance(case["row"], int)
        self.assertGreater(case["row"], 1)

    def test_every_header_named_column_survives(self):
        fields = self.case("ADM-01")["fields"]
        for label in ("ID", "Status", "Comments / Defect ref",
                      "Tx hash / evidence", "Source"):
            with self.subTest(column=label):
                self.assertIn(label, fields)

    def test_status_comment_evidence_and_source_are_the_written_values(self):
        fields = self.case("ADM-01")["fields"]
        self.assertEqual(fields["Status"], "Pass")
        self.assertEqual(fields["Comments / Defect ref"], "clean")
        self.assertEqual(fields["Tx hash / evidence"], "0xabc")
        self.assertEqual(fields["Source"], "Requested")

    def test_an_unrecognised_status_is_kept_as_written(self):
        # Mapping it onto a known status would hide the disagreement.
        self.assertEqual(self.case("ADM-04")["fields"]["Status"], "Weird")

    def test_a_blank_cell_is_an_empty_string_and_not_a_missing_field(self):
        fields = self.case("ADM-02")["fields"]
        self.assertIn("Tester", fields)
        self.assertEqual(fields["Tester"], "")

    def test_section_headings_and_blank_rows_are_not_cases(self):
        identifiers = [case["id"] for case in self.cases]
        self.assertEqual(identifiers, ["ADM-01", "ADM-02", "M2-03", "ADM-04"])

    def test_a_second_sheet_without_an_id_header_contributes_nothing(self):
        self.assertFalse([c for c in self.cases if c["sheet"] == "Defect Log"])


class SplitTests(ImportCase):
    def setUp(self):
        super().setUp()
        self.split = workbook.read_cases(
            self.made["benign.xlsx"], splits={"M2-03": ["M2-03a", "M2-03b"]}
        )

    def test_a_declared_split_produces_the_atomic_cases(self):
        self.assertEqual(
            [c["id"] for c in self.split if c["source_id"] == "M2-03"],
            ["M2-03a", "M2-03b"],
        )

    def test_each_half_keeps_the_identifier_it_came_from(self):
        for case in self.split:
            if case["id"].startswith("M2-03"):
                with self.subTest(case=case["id"]):
                    self.assertEqual(case["source_id"], "M2-03")
                    self.assertTrue(case["split"])

    def test_both_halves_carry_the_whole_source_row(self):
        halves = [c for c in self.split if c["source_id"] == "M2-03"]
        self.assertEqual(halves[0]["fields"], halves[1]["fields"])

    def test_a_split_does_not_change_how_many_source_rows_exist(self):
        self.assertEqual(
            len(workbook.source_rows(self.split)),
            len(workbook.source_rows(self.cases)),
        )

    def test_an_identifier_used_twice_refuses(self):
        with self.assertRaises(workbook.WorkbookError) as caught:
            workbook.read_cases(self.made["benign.xlsx"],
                                splits={"M2-03": ["ADM-01", "M2-03b"]})
        self.assertIn("more than once", str(caught.exception))

    def test_nothing_is_split_unless_a_reviewer_declared_it(self):
        self.assertFalse([c for c in self.cases if c["split"]])


class RoundTripTests(ImportCase):
    def test_every_source_row_is_rebuilt_from_the_cases_alone(self):
        rebuilt = workbook.source_rows(self.cases)
        self.assertEqual(len(rebuilt), len(self.cases))
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(rebuilt[(case["sheet"], case["row"])], case["fields"])

    def test_two_imports_of_the_same_bytes_agree(self):
        again = workbook.read_cases(self.made["benign.xlsx"])
        self.assertEqual(workbook.canonical_bytes(self.cases),
                         workbook.canonical_bytes(again))

    def test_the_digest_excludes_the_subject_so_a_label_cannot_move_it(self):
        first = workbook.record(self.cases, {"label": "one"})
        second = workbook.record(self.cases, {"label": "two"})
        self.assertEqual(first["workbook_sha256"], second["workbook_sha256"])

    def test_halves_that_disagree_about_their_row_refuse(self):
        broken = [dict(c) for c in self.cases[:2]]
        broken[1]["sheet"], broken[1]["row"] = broken[0]["sheet"], broken[0]["row"]
        with self.assertRaises(workbook.WorkbookError) as caught:
            workbook.source_rows(broken)
        self.assertIn("disagree about the row", str(caught.exception))


class RecordShapeTests(ImportCase):
    def setUp(self):
        super().setUp()
        self.record = workbook.record(self.cases, {"label": "benign.xlsx"})

    def test_the_record_carries_exactly_the_declared_keys(self):
        self.assertEqual(sorted(self.record), sorted(SCHEMA["required"]))

    def test_counts_are_tallied_over_the_written_values(self):
        self.assertEqual(self.record["counts"]["cases"], len(self.cases))
        self.assertEqual(self.record["counts"]["by_status"]["Pass"], 2)
        self.assertEqual(self.record["counts"]["by_source"]["Requested"], 3)

    def test_no_case_carries_a_key_the_schema_does_not_declare(self):
        allowed = set(SCHEMA["properties"]["cases"]["items"]["properties"])
        for case in self.record["cases"]:
            with self.subTest(case=case["id"]):
                self.assertTrue(set(case) <= allowed, set(case) - allowed)


class CheckTests(unittest.TestCase):
    def test_the_check_entry_point_reports_no_failures(self):
        self.assertEqual(workbook.check(), [])


if __name__ == "__main__":
    unittest.main()
