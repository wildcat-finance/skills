"""The TypeScript lexer classifies every character and never guesses long."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

from languages.typescript import typescript as ts  # noqa: E402


def kinds(source):
    spans, _ = ts.lex(source)
    return [(kind, source[start:end]) for kind, start, end in spans]


def only(source, kind):
    return [text for k, text in kinds(source) if k == kind]


class LexerTests(unittest.TestCase):
    def test_spans_cover_the_source_in_order(self):
        source = 'const a = "x"; // done\nconst b = 2;\n'
        spans, errors = ts.lex(source)
        self.assertEqual(errors, [])
        joined = "".join(source[start:end] for _, start, end in spans)
        self.assertEqual(joined, source)

    def test_a_string_with_escapes_is_one_span(self):
        self.assertEqual(only(r'const s = "a\"b\\";', "string"), [r'"a\"b\\"'])

    def test_a_class_keyword_inside_a_string_is_not_code(self):
        source = 'const s = "class X {";\n'
        code = "".join(only(source, "code"))
        self.assertNotIn("class X", code)

    def test_templates_nest_two_deep(self):
        source = "const t = `a${ {b: `c${d}e`} }f`;\n"
        templates = only(source, "template")
        self.assertEqual(templates, ["`a${ {b: `c${d}e`} }f`"])

    def test_line_and_block_comments_are_classified(self):
        source = "// line\n/* block\nstill */ const x = 1;\n"
        self.assertEqual(only(source, "line_comment"), ["// line"])
        self.assertEqual(only(source, "block_comment"), ["/* block\nstill */"])

    def test_regex_after_assignment_paren_return_and_comma(self):
        for source in (
            "const r = /ab+c/g;\n",
            "match(/ab+c/)\n",
            "return /ab+c/;\n",
            "f(x, /ab+c/)\n",
        ):
            with self.subTest(source=source):
                self.assertEqual(only(source, "regex"), ["/ab+c/g"] if "g;" in source else ["/ab+c/"])

    def test_division_after_parens_identifiers_and_numbers(self):
        for source in ("const x = (a + b) / c;\n", "const y = total / 2;\n", "const z = 10 / 5;\n"):
            with self.subTest(source=source):
                self.assertEqual(only(source, "regex"), [])

    def test_a_regex_containing_quotes_braces_and_a_class_slash(self):
        source = "const r = /[\"'{}/]+/;\n"
        self.assertEqual(only(source, "regex"), ["/[\"'{}/]+/"])

    def test_the_newline_guard_reclassifies_a_false_regex(self):
        source = "const a = x /\n  y;\nconst s = 'safe';\n"
        _spans, errors = ts.lex(source)
        self.assertEqual(errors, [])
        self.assertEqual(only(source, "regex"), [])
        self.assertEqual(only(source, "string"), ["'safe'"])

    def test_an_unterminated_string_confesses_the_remainder(self):
        source = "const s = 'no end\nconst x = 1;\n"
        spans, errors = ts.lex(source)
        self.assertEqual(len(errors), 1)
        self.assertIn("unterminated string", errors[0][1])
        self.assertEqual(spans[-1][0], "string")
        self.assertEqual(spans[-1][2], len(source))

    def test_an_unterminated_template_confesses_the_remainder(self):
        source = "const t = `open ${a};\n"
        _, errors = ts.lex(source)
        self.assertEqual(len(errors), 1)
        self.assertIn("unterminated template", errors[0][1])

    def test_a_comment_inside_a_template_expression_is_contained(self):
        source = "const t = `a${ b /* } */ + c }d`;\n"
        self.assertEqual(only(source, "template"), ["`a${ b /* } */ + c }d`"])


if __name__ == "__main__":
    unittest.main()
