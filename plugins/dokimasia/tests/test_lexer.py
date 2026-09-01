"""The scanner exists so a comment cannot become an inventory item."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from dokimasia_lib import lexer  # noqa: E402


class DecoyTests(unittest.TestCase):
    """Every place a false export can hide."""

    def test_a_line_comment_does_not_export(self):
        self.assertEqual(lexer.exported_names(lexer.tokenize("// export const GET = 1")), set())

    def test_a_block_comment_does_not_export(self):
        source = "/*\nexport async function POST() {}\n*/\n"
        self.assertEqual(lexer.exported_names(lexer.tokenize(source)), set())

    def test_a_string_does_not_export(self):
        source = 'const s = "export const DELETE = 1"\n'
        self.assertEqual(lexer.exported_names(lexer.tokenize(source)), set())

    def test_a_template_literal_does_not_export(self):
        source = "const s = `export const PATCH = 1`\n"
        self.assertEqual(lexer.exported_names(lexer.tokenize(source)), set())

    def test_a_regular_expression_body_does_not_export(self):
        source = "const r = /export const PUT/g\n"
        self.assertEqual(lexer.exported_names(lexer.tokenize(source)), set())

    def test_division_is_not_read_as_a_regular_expression(self):
        # If `/` after a value opened a regex, everything to the next slash
        # would vanish and the export below it would be lost.
        source = "const ratio = covered / scoped\nexport const GET = 1\n"
        self.assertEqual(lexer.exported_names(lexer.tokenize(source)), {"GET"})


class ExportTests(unittest.TestCase):
    def test_each_export_form_is_recognised(self):
        source = (
            "export const GET = 1\n"
            "export function HEAD() {}\n"
            "export async function POST() {}\n"
            "export class Thing {}\n"
            "export default function Page() {}\n"
            "export { PUT }\n"
        )
        self.assertEqual(
            lexer.exported_names(lexer.tokenize(source)),
            {"GET", "HEAD", "POST", "Thing", "default", "PUT"},
        )

    def test_an_aliased_export_records_both_names(self):
        # A stated limit: the scanner does not resolve aliases, so both the
        # local and the exported name are recorded.
        names = lexer.exported_names(lexer.tokenize("export { DELETE as REMOVE }"))
        self.assertIn("DELETE", names)
        self.assertIn("REMOVE", names)


class DirectiveTests(unittest.TestCase):
    def test_a_prologue_directive_is_found(self):
        self.assertIn("use server", lexer.directive_prologue(lexer.tokenize('"use server"\nexport function a() {}')))

    def test_a_string_after_a_statement_is_not_a_directive(self):
        source = 'export function a() {}\nconst s = "use server"\n'
        self.assertNotIn("use server", lexer.directive_prologue(lexer.tokenize(source)))

    def test_a_commented_directive_is_not_a_directive(self):
        self.assertEqual(lexer.directive_prologue(lexer.tokenize('// "use server"\n')), set())


class BoundsTests(unittest.TestCase):
    def test_an_unterminated_block_comment_ends_the_scan_rather_than_looping(self):
        self.assertEqual(lexer.tokenize("/* never closed"), [])

    def test_an_unterminated_string_ends_the_scan_rather_than_looping(self):
        tokens = lexer.tokenize('const s = "never closed')
        self.assertTrue(any(token.kind == "string" for token in tokens))

    def test_line_numbers_survive_a_multiline_comment(self):
        tokens = lexer.tokenize("/*\n\n\n*/\nexport const GET = 1\n")
        self.assertEqual([t.line for t in tokens if t.value == "GET"], [5])


if __name__ == "__main__":
    unittest.main()
