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

    def test_an_over_size_member_refuses_by_name(self):
        # The cap is a parameter, so lowering it for one call cannot leak into
        # any other test the way a mutated module global would.
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["benign.xlsx"], max_member_bytes=16)
        self.assertIn("over the", str(caught.exception))

    def test_the_size_cap_holds_when_the_declared_size_understates_the_member(self):
        """The cap must bind to bytes delivered, not to a number the archive wrote.

        `file_size` comes from the container, so an archive that understates it
        walks past a check made only against the declaration. Reading one byte
        past the cap catches it whatever the header says.
        """
        import zipfile
        target = Path(self.tmp.name) / "understated.xlsx"
        with zipfile.ZipFile(self.made["benign.xlsx"]) as source:
            members = {m.filename: source.read(m.filename) for m in source.infolist()}
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as out:
            for name, payload in members.items():
                info = zipfile.ZipInfo(name)
                out.writestr(info, payload)
        # Rewrite every declared size to zero, leaving the payloads intact.
        raw = bytearray(target.read_bytes())
        with zipfile.ZipFile(target) as check:
            sizes = {m.file_size for m in check.infolist() if m.file_size}
        import struct
        for size in sizes:
            raw = raw.replace(struct.pack("<I", size), struct.pack("<I", 0))
        target.write_bytes(bytes(raw))
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(target, max_member_bytes=8)
        message = str(caught.exception)
        self.assertTrue(
            "delivered more than" in message or "not readable" in message,
            f"a lying archive must refuse, not import: {message}",
        )

    def test_a_far_right_cell_refuses_rather_than_deciding_a_row_width(self):
        """A sparse sheet must not let one cell size the row it sits in.

        The bytes are small and compress normally, so no archive cap sees the
        cost; it is paid when the grid is materialised.
        """
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["far-right-cell.xlsx"])
        self.assertIn("column cap", str(caught.exception))

    def test_a_cell_reference_with_no_column_refuses_instead_of_vanishing(self):
        # A reference with no letters used to index at -1, which then fell out
        # of the row being built and lost the value without a word.
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["unanchored-cell.xlsx"])
        self.assertIn("names no column", str(caught.exception))

    def test_a_sheet_within_the_column_cap_still_reads(self):
        sheets = xlsx.read_sheets(self.made["benign.xlsx"])
        widest = max(len(row) for rows in sheets.values() for row in rows)
        self.assertLessEqual(widest, xlsx.MAX_COLUMNS)
        self.assertTrue(
            any(any(cell for cell in row) for rows in sheets.values() for row in rows)
        )

    def test_an_entity_declaration_refuses_before_the_parser_expands_it(self):
        with self.assertRaises(xlsx.XlsxRefusal) as caught:
            xlsx.read_sheets(self.made["entity-declaration.xlsx"])
        self.assertIn("entity declaration", str(caught.exception))

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
