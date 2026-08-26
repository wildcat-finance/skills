"""Guard Imprimatur's offset-preserving source-prose boundary."""

from pathlib import Path
import io
import inspect
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PLUGIN_ROOT / "skills" / "imprimatur" / "scripts"
SCRIPT = SCRIPT_DIR / "imprimatur.py"
sys.path.insert(0, str(SCRIPT_DIR))

import imprimatur as imprimatur_module  # noqa: E402


build = imprimatur_module.build
read_text = imprimatur_module.read_text
SourceExtractionError = getattr(imprimatur_module, "SourceExtractionError", ValueError)
extract_source_prose = getattr(imprimatur_module, "extract_source_prose", None)
SOURCE_MODE = (
    extract_source_prose is not None
    and "source_suffix" in inspect.signature(build).parameters
)


def term_hits(source: str, suffix: str, term: str = "leverage") -> list[dict]:
    if not SOURCE_MODE:
        raise AssertionError("Imprimatur has no source-prose mode")
    try:
        report = build(source, source_suffix=suffix)
    except SourceExtractionError as exc:
        raise AssertionError(
            f"valid {suffix} source was refused: {exc}"
        ) from exc
    return [
        hit
        for hit in report["hits"]
        if hit["term"] == term
    ]


class CharacterCountingText(str):
    def __new__(cls, value):
        instance = super().__new__(cls, value)
        instance.character_reads = 0
        return instance

    def __getitem__(self, key):
        if isinstance(key, int):
            self.character_reads += 1
        return super().__getitem__(key)


class SourceExtractionTests(unittest.TestCase):
    def test_indented_solidity_natspec_keeps_source_coordinates(self):
        source = (
            "contract Example {\n"
            "    /// @notice Leverage the underlying primitive.\n"
            "}\n"
        )
        hits = term_hits(source, ".sol")
        self.assertEqual([(2, 17)], [(hit["line"], hit["col"]) for hit in hits])

    def test_solidity_block_comments_are_prose_but_strings_are_not(self):
        source = (
            'contract Example { string constant X = "/* Leverage only data */";\n'
            "    /** Leverage the checked primitive. */\n"
            "}\n"
        )
        hits = term_hits(source, ".sol")
        self.assertEqual([2], [hit["line"] for hit in hits])

    def test_solidity_code_does_not_license_a_gated_comment_term(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        source = "NamedIdentifier value; // Orthogonal to the framing.\n"
        hits = [
            hit
            for hit in build(source, source_suffix=".sol")["hits"]
            if hit["term"] == "orthogonal"
        ]
        self.assertEqual([(1, 27)], [(hit["line"], hit["col"]) for hit in hits])

    def test_solidity_line_comments_end_at_each_valid_line_break(self):
        for terminator in ("\r", "\v", "\f"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    "// The first comment is clean."
                    + terminator
                    + "/// Leverage the actual helper."
                )
                hits = term_hits(source, ".sol")
                self.assertEqual(
                    [(2, 5)],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_solidity_invalid_source_line_breaks_refuse_by_name(self):
        for terminator in ("\x85", "\u2028", "\u2029"):
            with self.subTest(terminator=ascii(terminator)):
                source = "// clean" + terminator + "/// Leverage the helper."
                with self.assertRaisesRegex(
                    SourceExtractionError,
                    "unsupported Solidity source line break",
                ):
                    build(source, source_suffix=".sol")

    def test_solidity_quote_mask_does_not_erase_valid_line_breaks(self):
        for terminator in ("\r", "\v", "\f"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    '// "quoted'
                    + terminator
                    + '// text"'
                    + terminator
                    + "/// Leverage the actual helper."
                )
                hits = term_hits(source, ".sol")
                self.assertEqual(
                    [(3, 5)],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_solidity_crlf_string_continuation_stays_inside_the_string(self):
        source = (
            'contract C { string x = "first\\\r\n'
            '/* Leverage is string data. */"; }\r\n'
            "/// Leverage the real helper.\r\n"
        )
        hits = term_hits(source, ".sol")
        self.assertEqual(
            [(3, 5)],
            [(hit["line"], hit["col"]) for hit in hits],
        )

    def test_python_comments_and_owned_docstrings_are_prose(self):
        source = (
            '"""Leverage the module primitive."""\n'
            'ordinary = "Leverage is only data"\n'
            '"Leverage is a later expression, not a docstring"\n'
            "class Example:\n"
            '    """Leverage the class primitive."""\n'
            "    async def run(self):\n"
            '        """Leverage the function primitive."""\n'
            "        # Leverage the comment primitive.\n"
            "        return ordinary\n"
        )
        hits = term_hits(source, ".py")
        self.assertEqual([1, 5, 7, 8], [hit["line"] for hit in hits])

    def test_python_utf8_bom_keeps_source_comments_and_coordinates(self):
        source = (
            "\ufeff# Leverage the module note.\n"
            '"""Leverage the module documentation."""\n'
        )
        try:
            prose = extract_source_prose(source, ".py")
        except BaseException as exc:
            refusal = f"{type(exc).__name__}: {exc}"
            prose = ""
        else:
            refusal = None
        self.assertIsNone(refusal, refusal)
        self.assertEqual(len(source), len(prose))
        self.assertEqual(" ", prose[0])
        expected = [
            imprimatur_module.line_col(
                source,
                offset,
                imprimatur_module.PYTHON_LINE_TERMINATORS,
            )
            for offset in (
                source.index("Leverage"),
                source.rindex("Leverage"),
            )
        ]
        self.assertEqual(
            expected,
            [
                (hit["line"], hit["col"])
                for hit in term_hits(source, ".py")
            ],
        )

    def test_python_ast_byte_columns_map_to_unicode_source_coordinates(self):
        source = (
            "# π is retained prose\n"
            "def café():\n"
            '    """Leverage the Unicode-named helper."""\n'
            "    return 1\n"
        )
        hits = term_hits(source, ".py")
        self.assertEqual([(3, 8)], [(hit["line"], hit["col"]) for hit in hits])

    def test_python_cr_lines_keep_unicode_docstring_coordinates(self):
        source = (
            '# "quoted\r'
            '# text"\r'
            "def café():\r"
            '    """Leverage the Unicode-named helper."""\r'
            "    return 1\r"
        )
        try:
            hits = term_hits(source, ".py")
        except SourceExtractionError as exc:
            self.fail(f"valid CR Python source was refused: {exc}")
        self.assertEqual([(4, 8)], [(hit["line"], hit["col"]) for hit in hits])

    def test_python_docstring_token_walk_scales_with_source_size(self):
        def traced_line_events(function_count):
            source = "".join(
                f'def f{index}():\n    """doc {index}"""\n    return {index}\n'
                for index in range(function_count)
            )
            events = 0

            def trace(frame, event, arg):
                del arg
                nonlocal events
                if event == "line" and frame.f_code.co_filename == str(SCRIPT):
                    events += 1
                return trace

            previous = sys.gettrace()
            try:
                sys.settrace(trace)
                extract_source_prose(source, ".py")
            finally:
                sys.settrace(previous)
            return events

        small = traced_line_events(40)
        large = traced_line_events(80)
        self.assertLess(large, small * 3)

    def test_python_parser_resource_limit_is_a_named_refusal(self):
        source = "value = " + "+" * 10_000 + "1\n"
        try:
            extract_source_prose(source, ".py")
        except SourceExtractionError as exc:
            observed = str(exc)
        except BaseException as exc:
            observed = f"untranslated {type(exc).__name__}: {exc}"
        else:
            observed = "accepted"
        self.assertEqual("Python parser resource limit exceeded", observed)

    def test_typescript_literals_urls_templates_and_regexes_are_not_comments(self):
        source = (
            'const url = "https://example.test/Leverage";\n'
            "const template = `// Leverage only data`;\n"
            r"const pattern = /https?:\/\/Leverage/;" "\n"
            "// Leverage the helper.\n"
        )
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                hits = term_hits(source, suffix)
                self.assertEqual([4], [hit["line"] for hit in hits])

    def test_typescript_hashbang_trivia_is_source_prose(self):
        source = "#!/usr/bin/env node Leverage the loader.\nconst value = 1;\n"
        self.assertEqual(
            [(1, source.index("Leverage") + 1)],
            [(hit["line"], hit["col"]) for hit in term_hits(source, ".ts")],
        )

    def test_typescript_byte_order_mark_keeps_the_expression_goal(self):
        for suffix, prefix in (
            (".ts", "\ufeff/[/*]Leverage[*/]/;"),
            (".tsx", "\ufeff<p>/* Leverage is raw text */</p>;"),
        ):
            with self.subTest(suffix=suffix):
                source = prefix + " // Leverage the actual helper.\n"
                self.assertEqual(1, len(term_hits(source, suffix)))

    def test_typescript_template_expression_comments_are_prose(self):
        source = (
            "const first = `${value // Leverage the line helper.\n}`;\n"
            "const second = `${value /* Leverage the block helper. */}`;\n"
            "const nested = `${`${value // Leverage the nested helper.\n}`}`;\n"
        )
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                hits = term_hits(source, suffix)
                self.assertEqual([1, 3, 4], [hit["line"] for hit in hits])

    def test_tsx_jsdoc_is_prose_but_jsx_strings_are_not(self):
        source = (
            'const view = <p title="// Leverage only data">text</p>;\n'
            "/** Leverage the rendered helper. */\n"
        )
        hits = term_hits(source, ".tsx")
        self.assertEqual([2], [hit["line"] for hit in hits])

    def test_tsx_raw_child_text_is_not_a_comment(self):
        source = (
            "const view = (\n"
            "  <>\n"
            "    <p>// Leverage is visible text</p>\n"
            "    <p>/* Leverage is visible text */</p>\n"
            "    <p>outer <b>// Leverage is nested text</b></p>\n"
            "    {/* Leverage the actual JSX comment. */}\n"
            "  </>\n"
            ");\n"
        )
        hits = term_hits(source, ".tsx")
        self.assertEqual([(6, 9)], [(hit["line"], hit["col"]) for hit in hits])

    def test_tsx_unicode_element_raw_child_text_is_not_prose(self):
        source = (
            "const view = <É>// Leverage is visible text</É>;\n"
            "// Leverage the real helper.\n"
        )
        hits = term_hits(source, ".tsx")
        self.assertEqual([(2, 4)], [(hit["line"], hit["col"]) for hit in hits])

    def test_tsx_closing_tag_does_not_hide_a_following_comment(self):
        cases = {
            "closing": (
                "const view = <p>text</p>; // Leverage the real comment.\n",
                (1, 30),
            ),
            "self-closing": (
                "const view = <P />; // Leverage the real comment.\n",
                (1, 24),
            ),
            "nested expression": (
                "const view = <p>{flag ? <span>text</span> : value}</p>; "
                "// Leverage the real comment.\n",
                (1, 60),
            ),
        }
        for label, (source, expected) in cases.items():
            with self.subTest(label=label):
                hits = term_hits(source, ".tsx")
                self.assertEqual([expected], [(hit["line"], hit["col"]) for hit in hits])

    def test_typescript_division_after_a_brace_does_not_hide_a_comment(self):
        source = "const ratio = {} / 2; // Leverage the real comment.\n"
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                hits = term_hits(source, suffix)
                self.assertEqual([(1, 26)], [(hit["line"], hit["col"]) for hit in hits])

    def test_tsx_generic_component_type_arguments_keep_trailing_comment(self):
        source = (
            "const view = <Foo<Item> value={item} />; "
            "// Leverage the real comment.\n"
        )
        hits = term_hits(source, ".tsx")
        self.assertEqual([(1, 45)], [(hit["line"], hit["col"]) for hit in hits])

    def test_tsx_generic_arrow_comments_are_prose_without_jsx_refusal(self):
        cases = {
            "default": (
                "const f = <T = unknown,>(x: T) => x; "
                "// Leverage the trailing helper.\n",
                1,
            ),
            "commented constraint": (
                "const f = <T /* Leverage the type helper. */ extends object,>"
                "(x: T) => x; // Leverage the trailing helper.\n",
                2,
            ),
            "commented default": (
                "const f = <T /* Leverage the type helper. */ = unknown,>"
                "(x: T) => x; // Leverage the trailing helper.\n",
                2,
            ),
            "const parameter": (
                "const f = <const T,>(x: T) => x; "
                "// Leverage the trailing helper.\n",
                1,
            ),
        }
        for label, (source, expected_count) in cases.items():
            with self.subTest(label=label):
                try:
                    hits = term_hits(source, ".tsx")
                except SourceExtractionError as exc:
                    self.fail(f"valid TSX generic arrow was refused: {exc}")
                self.assertEqual(expected_count, len(hits))

    def test_tsx_single_parameter_generic_type_comments_are_prose(self):
        cases = {
            "variable annotation": (
                "let read: <T /* Leverage the type helper. */>"
                "(value: T) => T; // Leverage the trailing helper.\n"
            ),
            "parameter annotation": (
                "function use(read: <T /* Leverage the type helper. */>"
                "(value: T) => T) {} // Leverage the trailing helper.\n"
            ),
            "type alias": (
                "type Read = <T /* Leverage the type helper. */>"
                "(value: T) => T; // Leverage the trailing helper.\n"
            ),
            "class member": (
                "class Reader { read: <T /* Leverage the type helper. */>"
                "(value: T) => T; } // Leverage the trailing helper.\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                try:
                    hits = term_hits(source, ".tsx")
                except SourceExtractionError as exc:
                    self.fail(f"valid TSX type annotation was refused: {exc}")
                self.assertEqual(2, len(hits))

        jsx_source = (
            "const view = {item: <p>/* Leverage is raw child text. */</p>}; "
            "// Leverage the trailing helper.\n"
        )
        self.assertEqual(1, len(term_hits(jsx_source, ".tsx")))

    def test_typescript_slash_goal_keeps_only_real_comment_prose(self):
        cases = {
            "object division": 'const ratio = {} / "a/b".length;',
            "postfix division": 'let x = 1; const ratio = x++ / "a/b".length;',
            "template division": 'const ratio = `${{} / "a/b".length}`;',
            "JSX division": 'const view = <A value={{} / "a/b".length} />;',
            "class comparison heritage division": (
                'const ratio = class extends (a < b ? A : B) {} '
                '/ "a/b".length;'
            ),
            "function intersection return division": (
                'const ratio = function(): Value & {} {} / "a/b".length;'
            ),
            "function conditional return division": (
                "const ratio = function<T>(): T extends Value ? {} : {} {} "
                '/ "a/b".length;'
            ),
            "adjacent regex-close division": "const value = /Leverage//2;",
            "control regex block marker": (
                "if (ok) /[/*]Leverage/.test(value);"
            ),
            "control regex line marker": (
                "while (ok) /[//]Leverage/.test(value);"
            ),
        }
        for label, prefix in cases.items():
            with self.subTest(label=label):
                source = prefix + " // Leverage the real helper.\n"
                try:
                    hits = term_hits(source, ".tsx")
                except SourceExtractionError as exc:
                    self.fail(f"valid TSX slash context was refused: {exc}")
                self.assertEqual(
                    [(1, source.rindex("Leverage") + 1)],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_typescript_declaration_regex_does_not_become_comment_prose(self):
        source = (
            "declare const value: string\n"
            "/[/*] Leverage hidden [*/]/.test(value); "
            "// Leverage the actual helper.\n"
        )
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                hits = term_hits(source, suffix)
                self.assertEqual(
                    [(2, source.rindex("Leverage") - source.index("\n"))],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_tsx_declaration_boundaries_exclude_raw_child_text(self):
        declarations = [
            "type Alias = string",
            "declare function read(): Value",
            "let first: Value, second: Other",
            'import "pkg"',
            'import value from "pkg"',
            'export * from "pkg"',
        ]
        for declaration in declarations:
            with self.subTest(declaration=declaration):
                source = (
                    declaration
                    + "\n<div>/* Leverage is raw child text */</div>; "
                    "// Leverage the actual helper.\n"
                )
                expected = imprimatur_module.line_col(
                    source,
                    source.rindex("Leverage"),
                    imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                )
                self.assertEqual(
                    [expected],
                    [
                        (hit["line"], hit["col"])
                        for hit in term_hits(source, ".tsx")
                    ],
                )

    def test_typescript_restricted_statement_asi_hides_regex_and_jsx_text(self):
        cases = {
            "break": (
                "while (ok) { break\n/[/*]Leverage[*/]/.test(value); } "
                "// Leverage the actual helper.\n",
                ".ts",
            ),
            "continue label": (
                "outer: while (ok) { continue /* label trivia */ outer\n"
                "/[/*]Leverage[*/]/.test(value); } "
                "// Leverage the actual helper.\n",
                ".tsx",
            ),
            "debugger": (
                "while (ok) { debugger\u2028/[/*]Leverage[*/]/.test(value); } "
                "// Leverage the actual helper.\n",
                ".ts",
            ),
            "TSX child text": (
                "while (ok) { break\n<p>// Leverage is raw child text</p>; } "
                "// Leverage the actual helper.\n",
                ".tsx",
            ),
        }
        for label, (source, suffix) in cases.items():
            with self.subTest(label=label):
                try:
                    hits = term_hits(source, suffix)
                except SourceExtractionError as exc:
                    self.fail(
                        "valid restricted-statement source was refused: "
                        f"{exc}"
                    )
                expected = imprimatur_module.line_col(
                    source,
                    source.rindex("Leverage"),
                    imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                )
                self.assertEqual(
                    [expected],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

        retained = (
            "while (ok) { break /* Leverage the ASI note.\ncontinued */ "
            "/[/*]Leverage[*/]/.test(value); } "
            "// Leverage the actual helper.\n"
        )
        try:
            hits = term_hits(retained, ".ts")
        except SourceExtractionError as exc:
            self.fail(f"valid ASI-comment source was refused: {exc}")
        expected = [
            imprimatur_module.line_col(
                retained,
                offset,
                imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
            )
            for offset in (
                retained.index("Leverage"),
                retained.rindex("Leverage"),
            )
        ]
        self.assertEqual(expected, [(hit["line"], hit["col"]) for hit in hits])

    def test_typescript_nested_construct_state_keeps_only_comment_prose(self):
        cases = {
            "parenthesized class then block": (
                "(class {});\n"
                "{}\n"
                "/[/*]Leverage[*/]/.test(value); "
                "// Leverage the actual helper.\n",
                ".ts",
            ),
            "parenthesized function then control": (
                "(function() {});\n"
                "if (ready) {}\n"
                "<p>/* Leverage is raw child text */</p>; "
                "// Leverage the actual helper.\n",
                ".tsx",
            ),
            "nested function default then division": (
                "const ratio = function outer(arg = function inner() {}) {} "
                "/ /* Leverage the actual divisor. */ 2;\n",
                ".ts",
            ),
            "nested class heritage then division": (
                "const ratio = class Outer extends (class Inner {}) {} "
                "/ /* Leverage the actual divisor. */ 2;\n",
                ".tsx",
            ),
        }
        for label, (source, suffix) in cases.items():
            with self.subTest(label=label):
                hits = term_hits(source, suffix)
                expected = imprimatur_module.line_col(
                    source,
                    source.rindex("Leverage"),
                    imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                )
                self.assertEqual(
                    [expected],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_typescript_declaration_sequences_keep_later_regex_bytes_out(self):
        prefixes = {
            "ambient alias overload": (
                "declare const item: Map<string, Array<number>>\n"
                "type Alias = string\n"
                "function read<T>(value: T): T\n"
            ),
            "ambient class": (
                "declare const item: Map<string, Array<number>>\n"
                "class Example {}\n"
            ),
            "overload alias": (
                "function read<T>(value: T): Map<string, Array<number>>\n"
                "type Alias = string\n"
            ),
        }
        for suffix in (".ts", ".tsx"):
            for label, prefix in prefixes.items():
                with self.subTest(suffix=suffix, label=label):
                    source = (
                        prefix
                        + "/[/*]Leverage[*/]/.test(value); "
                        "// Leverage the actual helper.\n"
                    )
                    try:
                        hits = term_hits(source, suffix)
                    except SourceExtractionError as exc:
                        self.fail(
                            "valid declaration sequence was refused: "
                            f"{exc}"
                        )
                    expected = imprimatur_module.line_col(
                        source,
                        source.rindex("Leverage"),
                        imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                    )
                    self.assertEqual(
                        [expected],
                        [(hit["line"], hit["col"]) for hit in hits],
                    )

    def test_typescript_completed_statement_composition_keeps_only_prose(self):
        cases = {
            ".ts overload then async": (
                "function read(): void\n"
                "async function write() {}\n"
                "/[/*]Leverage[*/]/.test(value); "
                "// Leverage the actual helper.\n"
            ),
            ".ts do while then alias": (
                "do value; while (ready)\n"
                "type Alias = string\n"
                "/[/*]Leverage[*/]/.test(value); "
                "// Leverage the actual helper.\n"
            ),
            ".tsx nested do while then alias": (
                "do do value; while (inner); while (outer)\n"
                "type Alias = string\n"
                "<p>/* Leverage is raw child text */</p>; "
                "// Leverage the actual helper.\n"
            ),
            ".ts controlled do while then alias": (
                "if (enabled) do value; while (ready)\n"
                "type Alias = string\n"
                "/[/*]Leverage[*/]/.test(value); "
                "// Leverage the actual helper.\n"
            ),
            ".ts block-bodied control in do while": (
                "do if (enabled) { value() } while (ready)\n"
                "type Alias = string\n"
                "/[/*]Leverage[*/]/.test(value); "
                "// Leverage the actual helper.\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                hits = term_hits(source, label.split()[0])
                expected = imprimatur_module.line_col(
                    source,
                    source.rindex("Leverage"),
                    imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                )
                self.assertEqual(
                    [expected],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_tsx_nested_generic_function_type_comments_are_prose(self):
        cases = (
            "function read<T extends F<<U /* Leverage the type helper. */>"
            "(value: U) => U>>() {} // ordinary trailing\n",
            "const read = make<<T /* Leverage the type helper. */>"
            "(value: T) => T>(); // ordinary trailing\n",
            "const read = make<<T /* Leverage the type helper. */>"
            "(value: T) => T>; // ordinary trailing\n",
        )
        for source in cases:
            with self.subTest(source=source):
                expected = imprimatur_module.line_col(
                    source,
                    source.index("Leverage"),
                    imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                )
                self.assertEqual(
                    [expected],
                    [
                        (hit["line"], hit["col"])
                        for hit in term_hits(source, ".tsx")
                    ],
                )

    def test_typescript_class_member_names_do_not_hide_comment_prose(self):
        source = (
            "class Outer {\n"
            "  class = C\n"
            "  ratio = {} / /* Leverage the field helper. */ 2\n"
            "}\n"
        )
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    [(3, 19)],
                    [
                        (hit["line"], hit["col"])
                        for hit in term_hits(source, suffix)
                    ],
                )

    def test_typescript_contextual_declaration_word_does_not_hide_prose(self):
        source = (
            "interface = value\n"
            "const ratio = {} / /* Leverage the expression helper. */ 2\n"
        )
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    [(2, 23)],
                    [
                        (hit["line"], hit["col"])
                        for hit in term_hits(source, suffix)
                    ],
                )

    def test_typescript_dynamic_import_division_keeps_comment_prose(self):
        source = (
            'import("pkg")\n'
            "/ /* Leverage the division helper. */ 2; // ordinary trailing\n"
        )
        for suffix in (".ts", ".tsx"):
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    [(2, 6)],
                    [
                        (hit["line"], hit["col"])
                        for hit in term_hits(source, suffix)
                    ],
                )

    def test_typescript_keyword_slash_goals_do_not_return_false_clean(self):
        for accessor in (".", "?."):
            for name in ("await", "case", "default", "of", "return", "yield"):
                with self.subTest(accessor=accessor, name=name):
                    source = (
                        f"const ratio = value{accessor}{name} "
                        "/ /* Leverage the division helper. */ 2;\n"
                    )
                    self.assertEqual(1, len(term_hits(source, ".ts")))

        source = (
            "const of = 2; const ratio = of "
            "/ /* Leverage the division helper. */ 2;\n"
        )
        self.assertEqual(1, len(term_hits(source, ".ts")))

        for name in ("await", "yield"):
            with self.subTest(contextual=name):
                source = (
                    f"const ratio = {name} "
                    "/ /* Leverage the division helper. */ 2;\n"
                )
                try:
                    build(source, source_suffix=".ts")
                except SourceExtractionError as exc:
                    observed = str(exc)
                else:
                    observed = "accepted"
                self.assertEqual(
                    "ambiguous slash after contextual identifier",
                    observed,
                )

        for binding in (
            "const await",
            "const yield",
            "const {value}",
            "const [value]",
        ):
            with self.subTest(for_of_binding=binding):
                source = (
                    f"for ({binding} of /[/*]Leverage[*/]/) {{}} "
                    "// Leverage the actual helper.\n"
                )
                self.assertEqual(1, len(term_hits(source, ".ts")))

        for keyword, wrapper in (
            ("await", "async function read() {{ {body} }}"),
            ("yield", "function* read() {{ {body} }}"),
        ):
            with self.subTest(contextual_regex_comment=keyword):
                source = wrapper.format(
                    body=(
                        f"{keyword} /literal/// "
                        "Leverage the actual helper.\n"
                    )
                )
                self.assertEqual(1, len(term_hits(source, ".ts")))

            for operand in ("{}", "function() {}", "class {}"):
                with self.subTest(contextual_operand=keyword, operand=operand):
                    source = wrapper.format(
                        body=(
                            f"const ratio = {keyword} {operand} "
                            "/ /* Leverage the division helper. */ 2;"
                        )
                    )
                    self.assertEqual(1, len(term_hits(source, ".ts")))

    def test_typescript_expression_prefixes_hide_regex_and_jsx_text(self):
        cases = {
            ".ts prefix increment": "const value = ++/[/*]Leverage[*/]/;",
            ".ts line-break prefix decrement": (
                "let value = 1; value\n--/[/*]Leverage[*/]/;"
            ),
            ".ts line-break prefix not": (
                "let value = 1; value\n!/[/*]Leverage[*/]/;"
            ),
            ".ts array spread": "const value = [.../[/*]Leverage[*/]/];",
            ".ts class heritage": (
                "class Example extends /[/*]Leverage[*/]/ {}"
            ),
            ".ts decorator": "@/[/*]Leverage[*/]/ class Example {}",
            ".tsx JSX spread": (
                "const value = [...<p>/* Leverage is raw text */</p>];"
            ),
        }
        for label, prefix in cases.items():
            suffix = label.split()[0]
            with self.subTest(label=label):
                source = prefix + " // Leverage the actual helper.\n"
                hits = term_hits(source, suffix)
                expected = imprimatur_module.line_col(
                    source,
                    source.rindex("Leverage"),
                    imprimatur_module.TYPESCRIPT_LINE_TERMINATORS,
                )
                self.assertEqual(
                    [expected],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_type_alias_newline_restores_regex_without_exposing_its_text(self):
        aliases = {
            "primitive": "type Alias = string",
            "array": "type Alias = string[]",
            "tuple": "type Alias = [string, number]",
            "generic": "type Alias = Foo<Bar>",
            "object": "type Alias = { value: string }",
            "conditional": (
                "type Alias<T> = T extends string ? First : Second"
            ),
            "function": "type Alias = (value: string) => number",
        }
        for label, alias in aliases.items():
            with self.subTest(label=label):
                source = (
                    alias
                    + "\n/[/*]Leverage/.test(value); // Leverage the helper.\n"
                )
                try:
                    hits = term_hits(source, ".tsx")
                except SourceExtractionError as exc:
                    self.fail(f"valid TSX type-alias boundary was refused: {exc}")
                self.assertEqual(
                    [(2, source.rindex("Leverage") - source.index("\n"))],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_regex_close_can_touch_a_real_line_comment(self):
        source = "const value = /Leverage/// Leverage the helper.\n"
        hits = term_hits(source, ".tsx")
        self.assertEqual([(1, 28)], [(hit["line"], hit["col"]) for hit in hits])

    def test_typescript_unicode_line_terminators_keep_code_out_of_prose(self):
        for terminator in ("\r\n", "\r", "\u2028", "\u2029"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    "// The first comment is clean."
                    + terminator
                    + "const Leverage = 1;"
                    + terminator
                    + "// Leverage the actual helper."
                )
                hits = term_hits(source, ".ts")
                self.assertEqual(
                    [(3, 4)],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_typescript_quote_mask_does_not_erase_line_terminators(self):
        for terminator in ("\r\n", "\r", "\u2028", "\u2029"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    '// "quoted'
                    + terminator
                    + '// text"'
                    + terminator
                    + "// Leverage the actual helper."
                )
                hits = term_hits(source, ".ts")
                self.assertEqual(
                    [(3, 4)],
                    [(hit["line"], hit["col"]) for hit in hits],
                )

    def test_each_mask_has_the_source_length_and_line_terminators(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        cases = {
            ".sol": "contract C {\n  // prose\n}\n",
            ".py": '"""prose\nline"""\nvalue = 1\n',
            ".ts": "const x = 1;\n/* prose\nline */\n",
            ".tsx": "const x = <p />;\n// prose\n",
        }
        for suffix, source in cases.items():
            with self.subTest(suffix=suffix):
                masked = extract_source_prose(source, suffix)
                self.assertEqual(len(source), len(masked))
                self.assertEqual(
                    [index for index, char in enumerate(source) if char in "\r\n"],
                    [index for index, char in enumerate(masked) if char in "\r\n"],
                )

    def test_many_findings_share_one_bounded_coordinate_index(self):
        hard, gated, _ = imprimatur_module.load_lexicons()
        source = CharacterCountingText(("Leverage " * 512) + "\n")
        hits = imprimatur_module.scan_hard(source, hard)
        self.assertEqual(512, len(hits))
        self.assertLess(source.character_reads, len(source) * 4)

        repeated_gate = ("orthogonal " * 512) + "to the framing."
        with mock.patch.object(
            imprimatur_module,
            "gate_evidence",
            wraps=imprimatur_module.gate_evidence,
        ) as gated_checks:
            gated_hits = imprimatur_module.scan_gated(
                repeated_gate,
                gated,
            )
        self.assertEqual(512, len(gated_hits))
        self.assertLessEqual(gated_checks.call_count, 2)

        all_passes = (
            "Leverage this helper.\n\n"
            "This approach is orthogonal to the framing.\n\n"
            "This isn't just a protocol, it's a promise.\n"
        )
        with mock.patch.object(
            imprimatur_module,
            "line_col",
            side_effect=AssertionError("per-finding coordinate rescan"),
        ):
            report = build(all_passes)
        self.assertEqual(
            {"hard", "gated", "structural"},
            {hit["pass"] for hit in report["hits"]},
        )

    def test_malformed_supported_source_refuses_a_clean_result(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        cases = {
            ".sol": "contract C { /* never closes",
            ".py": "def broken(:\n    pass\n",
            ".ts": "const value = `never closes;",
            ".tsx": "const view = <p title=\"never closes;",
            ".ts regex": "const pattern = /never closes",
        }
        for suffix, source in cases.items():
            language_suffix = suffix.split()[0]
            with self.subTest(suffix=language_suffix, case=suffix):
                with self.assertRaises(SourceExtractionError):
                    build(source, source_suffix=language_suffix)

    def test_unterminated_tsx_element_refuses_a_clean_result(self):
        with self.assertRaisesRegex(SourceExtractionError, "unterminated JSX element"):
            build("const view = <p>", source_suffix=".tsx")

    def test_typescript_nesting_boundary_is_named(self):
        accepted = "const value = " + "{" * 64 + "0" + "}" * 64 + ";\n"
        refused = "const value = " + "{" * 65 + "0" + "}" * 65 + ";\n"
        self.assertEqual(len(accepted), len(extract_source_prose(accepted, ".ts")))
        try:
            extract_source_prose(refused, ".ts")
        except BaseException as exc:  # the unfixed scanner leaked RecursionError
            refusal = exc
        else:
            refusal = None
        self.assertIsInstance(refusal, SourceExtractionError)
        self.assertEqual("nesting exceeds supported depth", str(refusal))

    def test_markdown_and_include_code_keep_their_existing_meanings(self):
        self.assertTrue(SOURCE_MODE, "Imprimatur has no source-prose mode")
        markdown = "    Leverage hidden in indented Markdown.\n"
        self.assertEqual(0, build(markdown)["defects"])
        solidity = "contract C { function leverage() external {} }\n"
        self.assertEqual(
            0,
            build(solidity, source_suffix=".sol")["defects"],
        )
        self.assertGreater(
            build(solidity, source_suffix=".sol", skip_code=False)["defects"],
            0,
        )

    def test_promise_evidence_conditions_extraction_on_default_masking(self):
        skill = (
            PLUGIN_ROOT / "skills" / "imprimatur" / "SKILL.md"
        ).read_text(encoding="utf-8")
        evidence = next(
            line
            for line in skill.splitlines()
            if line.startswith("- Evidence: The exact input bytes")
        )
        self.assertIn("when default masking selects", evidence)

    def test_cli_reports_each_path_and_original_coordinates(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            clean = root / "clean.py"
            finding = root / "finding.sol"
            clean.write_text("# The helper returns one value.\n", encoding="utf-8")
            finding.write_text(
                "contract Example {\n"
                "    /// @notice Leverage the underlying primitive.\n"
                "}\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    str(clean),
                    str(finding),
                    "--max-defects",
                    "0",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn(f"=== {clean} ===", result.stdout)
        self.assertIn(f"=== {finding} ===", result.stdout)
        self.assertIn("2:17", result.stdout)

    def test_cli_path_read_preserves_crlf_and_lone_cr(self):
        payload = b"// first\r\n// second\r// third\n"
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "terminators.ts"
            source.write_bytes(payload)
            options = (
                {"preserve_newlines": True}
                if "preserve_newlines" in inspect.signature(read_text).parameters
                else {}
            )
            observed = read_text(str(source), **options)
        self.assertEqual(payload.decode("utf-8"), observed)

    def test_cli_rejects_invalid_utf8_without_partial_output(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "invalid.ts"
            source.write_bytes(b"// valid first line\r\n// invalid byte: \xff\n")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn(f"imprimatur: {source}:2:18:", result.stderr)
        self.assertIn("source is not valid UTF-8", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "typescript-line-rules.ts"
            source.write_bytes(b"// first\v// invalid: \xff")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn(f"imprimatur: {source}:1:22:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_normalizes_supported_source_path_read_errors(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "directory.ts"
            source.mkdir()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn(f"imprimatur: {source}:1:1:", result.stderr)
        self.assertIn("source path is not a regular file", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_supported_source_fifo_is_refused_before_open(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "blocked.ts"
            os.mkfifo(source)
            with mock.patch.object(
                Path,
                "open",
                side_effect=AssertionError("non-regular source was opened"),
            ):
                with self.assertRaisesRegex(
                    SourceExtractionError,
                    "source path is not a regular file",
                ):
                    read_text(str(source), preserve_newlines=True)

    def test_supported_source_rechecks_the_open_descriptor_after_a_path_swap(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            regular = root / "regular.ts"
            source = root / "raced.ts"
            regular.write_text("// ordinary prose\n", encoding="utf-8")
            os.mkfifo(source)
            with mock.patch.object(
                Path,
                "stat",
                return_value=regular.stat(),
            ), mock.patch.object(
                Path,
                "open",
                side_effect=AssertionError("raced FIFO reached blocking open"),
            ):
                try:
                    read_text(str(source), preserve_newlines=True)
                except BaseException as exc:
                    observed = f"{type(exc).__name__}: {exc}"
                else:
                    observed = "accepted"
            self.assertEqual(
                "SourceExtractionError: source path is not a regular file",
                observed,
            )

    @unittest.skipUnless(hasattr(os, "O_NOFOLLOW"), "O_NOFOLLOW unavailable")
    def test_supported_source_symlink_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            target = root / "target.ts"
            source = root / "linked.ts"
            target.write_text("// ordinary prose\n", encoding="utf-8")
            source.symlink_to(target)
            with self.assertRaisesRegex(
                SourceExtractionError,
                "source path is not a regular file",
            ):
                read_text(str(source), preserve_newlines=True)

    def test_supported_source_refuses_when_no_follow_open_is_unavailable(self):
        with mock.patch.object(os, "O_NOFOLLOW", 0):
            try:
                read_text("source.ts", preserve_newlines=True)
            except BaseException as exc:
                observed = f"{type(exc).__name__}: {exc}"
            else:
                observed = "accepted"
        self.assertEqual(
            "SourceExtractionError: source path no-follow open is unavailable",
            observed,
        )

    def test_cli_rejects_oversized_source_before_parsing(self):
        limit = getattr(imprimatur_module, "MAX_SOURCE_BYTES", None)
        self.assertIsNotNone(limit, "Imprimatur has no source byte ceiling")
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "oversized.ts"
            source.write_bytes(b" " * (limit + 1))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn(
            f"source exceeds {limit}-byte analysis cap",
            result.stderr,
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_markdown_path_keeps_universal_newline_behavior(self):
        payload = b"first\r\nsecond\rthird\n"
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "ordinary.md"
            source.write_bytes(payload)
            observed = read_text(str(source))
        self.assertEqual("first\nsecond\nthird\n", observed)

    def test_cli_preserves_newlines_only_for_default_source_mode(self):
        cases = {
            "default source": (["sample.ts"], True),
            "include code": (["sample.ts", "--include-code"], False),
            "Markdown": (["sample.md"], False),
        }
        for label, (arguments, expected) in cases.items():
            with self.subTest(label=label):
                with mock.patch.object(
                    imprimatur_module,
                    "read_text",
                    return_value="// ordinary prose\n",
                ) as reader, mock.patch.object(
                    sys,
                    "argv",
                    [str(SCRIPT), *arguments],
                ), mock.patch.object(sys, "stdout", new=io.StringIO()):
                    self.assertEqual(0, imprimatur_module.main())
                reader.assert_called_once_with(
                    arguments[0], preserve_newlines=expected
                )

    def test_cli_returns_two_without_a_partial_clean_report_on_extraction_error(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            clean = root / "clean.sol"
            broken = root / "broken.ts"
            clean.write_text("// The helper returns one value.\n", encoding="utf-8")
            broken.write_text("const value = `never closes;", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(clean), str(broken)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn(f"imprimatur: {broken}:1:15:", result.stderr)
        self.assertIn("unterminated template literal", result.stderr)

    def test_cli_translates_overdeep_typescript_to_a_named_refusal(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "overdeep.tsx"
            source.write_text(
                "const value = " + "{" * 2000 + "0" + "}" * 2000 + ";\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertIn("nesting exceeds supported depth", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
