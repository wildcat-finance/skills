"""The archive boundary: what the reader accepts, and how it refuses."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import xlsx  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "dokimasia_workbook_fixtures", PLUGIN / "tests" / "fixtures" / "workbooks" / "build.py"
)
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.made = build.build_all(Path(self.tmp.name))


class ReadingTests(FixtureCase):
    def test_shared_and_inline_strings_both_resolve(self):
        sheets = xlsx.read_sheets(self.made["benign.xlsx"])
        self.assertEqual(sorted(sheets), ["1 Admin", "Defect Log"])
        self.assertIn("ADM-01", [cell for row in sheets["1 Admin"] for cell in row])
        self.assertIn("DEF-001", [cell for row in sheets["Defect Log"] for cell in row])

    def test_an_empty_cell_reads_as_an_empty_string_not_a_missing_column(self):
        sheets = xlsx.read_sheets(self.made["benign.xlsx"])
        header = next(r for r in sheets["1 Admin"] if r and r[0] == "ID")
        row = next(r for r in sheets["1 Admin"] if r and r[0] == "ADM-02")
        self.assertEqual(len(row), len(header))
        self.assertEqual(row[header.index("Tester")], "")

    def test_multiple_sheets_keep_the_workbook_order(self):
        self.assertEqual(list(xlsx.read_sheets(self.made["benign.xlsx"])), ["1 Admin", "Defect Log"])

    def test_a_package_absolute_relationship_target_resolves(self):
        # The real reviewed workbook uses this form; the first draft of the
        # reader prepended `xl/` to it and could not find any sheet.
        sheets = xlsx.read_sheets(self.made["absolute-targets.xlsx"])
        self.assertEqual(list(sheets), ["1 Admin"])

    def test_a_cached_formula_value_is_read_and_nothing_is_evaluated(self):
        sheets = xlsx.read_sheets(self.made["cached-formula.xlsx"])
        cells = [cell for row in sheets["1 Admin"] for cell in row]
        self.assertIn("ADM-01", cells)
        self.assertNotIn("EVAL-99", cells)


class RefusalTests(FixtureCase):
    def test_a_zip_bomb_refuses_on_its_expansion_ratio(self):
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["zip-bomb.xlsx"])
        self.assertIn("ratio cap", str(caught.exception))

    def test_a_traversal_member_name_refuses_by_name(self):
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["traversal-member.xlsx"])
        self.assertIn("parent-directory segment", str(caught.exception))

    def test_an_over_count_archive_refuses_by_name(self):
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["too-many-members.xlsx"])
        self.assertIn("over the", str(caught.exception))

    def test_a_file_that_is_not_an_archive_refuses_by_name(self):
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["not-a-spreadsheet.xlsx"])
        self.assertIn("not a spreadsheet archive", str(caught.exception))

    def test_an_over_size_member_refuses_before_it_is_read(self):
        original = xlsx.MAX_MEMBER_BYTES
        xlsx.MAX_MEMBER_BYTES = 16
        self.addCleanup(setattr, xlsx, "MAX_MEMBER_BYTES", original)
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["benign.xlsx"])
        self.assertIn("over the", str(caught.exception))

    def test_a_shared_string_index_that_is_absent_refuses(self):
        import zipfile
        target = Path(self.tmp.name) / "bad-index.xlsx"
        with zipfile.ZipFile(self.made["benign.xlsx"]) as source:
            members = {m.filename: source.read(m.filename) for m in source.infolist()}
        members["xl/worksheets/sheet1.xml"] = (
            b'<?xml version="1.0"?><worksheet xmlns="'
            + build.MAIN.encode()
            + b'"><sheetData><row r="1"><c r="A1" t="s"><v>999</v></c></row>'
            b"</sheetData></worksheet>"
        )
        with zipfile.ZipFile(target, "w") as out:
            for name, payload in members.items():
                out.writestr(name, payload)
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(target)
        self.assertIn("is absent", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
