"""The shared lexer retains the Horos TypeScript lexical boundary."""

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import typescript_lexer as ts  # noqa: E402


def kinds(source):
    spans, _ = ts.lex(source)
    return [(kind, source[start:end]) for kind, start, end in spans]


def only(source, kind):
    return [text for current, text in kinds(source) if current == kind]


def comments(source, *, tsx=False):
    classify = getattr(ts, "comment_spans", None)
    if classify is None:
        raise AssertionError("the shared lexer has no comment-span entry point")
    spans, errors = classify(source, tsx=tsx)
    if errors:
        raise AssertionError(f"unexpected comment-span errors: {errors}")
    return [source[start:end] for _, start, end in spans]


class SliceCountingSource(str):
    """Expose suffix copies made by a scanner without timing assertions."""

    def __new__(cls, value):
        instance = super().__new__(cls, value)
        instance.suffix_slice_count = 0
        return instance

    def __getitem__(self, key):
        if isinstance(key, slice) and key.stop is None:
            self.suffix_slice_count += 1
        return super().__getitem__(key)


class CharacterCountingSource(str):
    """Count scanner character reads without a wall-clock assertion."""

    def __new__(cls, value):
        instance = super().__new__(cls, value)
        instance.character_reads = 0
        return instance

    def __getitem__(self, key):
        if isinstance(key, int):
            self.character_reads += 1
        return super().__getitem__(key)


class TypeScriptLexerTests(unittest.TestCase):
    def test_spans_reconstruct_the_complete_source(self):
        source = 'const a = "x"; // done\nconst b = /two/g;\n'
        spans, errors = ts.lex(source)
        self.assertEqual([], errors)
        self.assertEqual(source, "".join(source[start:end] for _, start, end in spans))

    def test_strings_and_both_comment_forms_are_separate_spans(self):
        source = '// line\n/* block\nstill */ const value = "a\\\"b";\n'
        self.assertEqual(["// line"], only(source, "line_comment"))
        self.assertEqual(["/* block\nstill */"], only(source, "block_comment"))
        self.assertEqual(['"a\\\"b"'], only(source, "string"))

    def test_templates_nest_two_deep(self):
        source = "const value = `a${ {b: `c${d}e`} }f`;\n"
        self.assertEqual(["`a${ {b: `c${d}e`} }f`"], only(source, "template"))

    def test_regex_is_distinguished_from_division(self):
        source = "const match = /[a/b]+/gi; const ratio = total / 2;\n"
        self.assertEqual(["/[a/b]+/gi"], only(source, "regex"))

    def test_unterminated_construct_reports_offset_and_covers_remainder(self):
        source = "const value = `open ${name};\n"
        spans, errors = ts.lex(source)
        self.assertEqual(1, len(errors))
        self.assertEqual(source.index("`"), errors[0][0])
        self.assertIn("unterminated template", errors[0][1])
        self.assertEqual(("template", source.index("`"), len(source)), spans[-1])

    def test_multiline_jsx_attribute_string_is_one_span(self):
        source = (
            '<Tooltip value="first line\n'
            '  second line" />\n'
        )
        spans, errors = ts.lex(source)
        self.assertEqual([], errors)
        self.assertEqual(
            ['"first line\n  second line"'],
            [source[start:end] for kind, start, end in spans if kind == "string"],
        )

    def test_comment_spans_open_template_substitutions_only(self):
        source = (
            "const raw = `// not a comment`;\n"
            "const value = `${item // line comment\n"
            "  + `${other /* nested comment */}`}`;\n"
        )
        self.assertEqual(
            ["// line comment", "/* nested comment */"],
            comments(source),
        )

    def test_comment_spans_include_the_initial_hashbang_trivia(self):
        for terminator in ("\n", "\r", "\r\n", "\u2028", "\u2029"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    "#!/usr/bin/env node Leverage"
                    + terminator
                    + "const value = 1; // trailing"
                )
                self.assertEqual(
                    ["#!/usr/bin/env node Leverage", "// trailing"],
                    comments(source),
                )

    def test_ecmascript_byte_order_mark_is_trivia_for_expression_goals(self):
        cases = {
            "file regex": ("\ufeff/[/*]raw[*/]/; // trailing\n", False),
            "return regex": (
                "function read() { return\ufeff/[/*]raw[*/]/; } "
                "// trailing\n",
                False,
            ),
            "file JSX": (
                "\ufeff<p>/* raw */</p>; // trailing\n",
                True,
            ),
            "JSX attribute": (
                "const view = <p\ufeffvalue={1}>/* raw */</p>; "
                "// trailing\n",
                True,
            ),
        }
        for label, (source, tsx) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(["// trailing"], comments(source, tsx=tsx))

    def test_tsx_comment_spans_exclude_child_text_and_keep_code_comments(self):
        source = (
            "const view = (\n"
            "  <p>// visible child text\n"
            "    <span>/* nested child text */</span>\n"
            "    {/* real JSX comment */}\n"
            "  </p>\n"
            "); // real trailing comment\n"
        )
        self.assertEqual(
            ["/* real JSX comment */", "// real trailing comment"],
            comments(source, tsx=True),
        )

    def test_tsx_unicode_element_child_text_is_not_a_comment(self):
        source = (
            "const view = <É>// visible child text</É>;\n"
            "// real trailing comment\n"
        )
        self.assertEqual(["// real trailing comment"], comments(source, tsx=True))

    def test_comment_spans_do_not_let_division_hide_a_later_comment(self):
        source = "const ratio = {} / 2; // real comment\n"
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                self.assertEqual(["// real comment"], comments(source, tsx=tsx))

    def test_tsx_generic_component_type_arguments_keep_trailing_comment(self):
        source = "const view = <Foo<Item> value={item} />; // real comment\n"
        self.assertEqual(["// real comment"], comments(source, tsx=True))

    def test_tsx_generic_arrows_accept_defaults_modifiers_and_comment_trivia(self):
        cases = {
            "default": (
                "const f = <T = unknown,>(x: T) => x; // trailing\n",
                ["// trailing"],
            ),
            "constraint comment": (
                "const f = <T /* type prose */ extends object,>(x: T) => x; "
                "// trailing\n",
                ["/* type prose */", "// trailing"],
            ),
            "default comment": (
                "const f = <T /* type prose */ = unknown,>(x: T) => x; "
                "// trailing\n",
                ["/* type prose */", "// trailing"],
            ),
            "const parameter": (
                "const f = <const T,>(x: T) => x; // trailing\n",
                ["// trailing"],
            ),
            "contextual name": (
                "const f = <out /* type prose */,>(x: out) => x; "
                "// trailing\n",
                ["/* type prose */", "// trailing"],
            ),
            "between head and parameters": (
                "const f = <T,> /* parameter prose */ (x: T) => x; "
                "// trailing\n",
                ["/* parameter prose */", "// trailing"],
            ),
        }
        for label, (source, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(expected, comments(source, tsx=True))

    def test_tsx_single_parameter_generics_follow_known_type_goals(self):
        type_positions = {
            "variable annotation": (
                "let read: <T /* type prose */>(value: T) => T; "
                "// trailing\n"
            ),
            "ambient variable annotation": (
                "declare const read: <T /* type prose */>(value: T) => T; "
                "// trailing\n"
            ),
            "parameter annotation": (
                "function use(read: <T /* type prose */>(value: T) => T) {} "
                "// trailing\n"
            ),
            "return annotation": (
                "function make(): <T /* type prose */>(value: T) => T {} "
                "// trailing\n"
            ),
            "type alias": (
                "type Read = <T /* type prose */>(value: T) => T; "
                "// trailing\n"
            ),
            "class member": (
                "class Reader { read: <T /* type prose */>(value: T) => T; } "
                "// trailing\n"
            ),
        }
        for label, source in type_positions.items():
            with self.subTest(label=label):
                self.assertEqual(
                    ["/* type prose */", "// trailing"],
                    comments(source, tsx=True),
                )

        jsx_positions = {
            "object value": (
                "const view = {read: <p>/* raw child text */</p>}; "
                "// trailing\n"
            ),
            "labelled statement": (
                "render: <p>/* raw child text */</p>; // trailing\n"
            ),
        }
        for label, source in jsx_positions.items():
            with self.subTest(label=label):
                self.assertEqual(["// trailing"], comments(source, tsx=True))

    def test_tsx_arrow_probe_does_not_consume_jsx_attributes_or_child_text(self):
        source = (
            '<Foo label="value">(// visible child text)</Foo>; '
            "// trailing\n"
        )
        self.assertEqual(["// trailing"], comments(source, tsx=True))

    def test_slash_goal_distinguishes_expression_division_and_control_regex(self):
        cases = {
            "object division": 'const ratio = {} / "a/b".length; // trailing\n',
            "postfix division": (
                'let x = 1; const ratio = x++ / "a/b".length; // trailing\n'
            ),
            "parenthesized arrow division": (
                'const ratio = (() => {}) / "a/b".length; // trailing\n'
            ),
            "generic function expression division": (
                'const ratio = function<T extends {}>() {} / "a/b".length; '
                "// trailing\n"
            ),
            "function intersection return division": (
                'const ratio = function(): Value & {} {} / "a/b".length; '
                "// trailing\n"
            ),
            "function conditional return division": (
                "const ratio = function<T>(): T extends Value ? {} : {} {} "
                '/ "a/b".length; // trailing\n'
            ),
            "non-null assertion division": (
                'const ratio = value! / "a/b".length; // trailing\n'
            ),
            "parenthesized arrow non-null division": (
                'const ratio = (() => {})! / "a/b".length; // trailing\n'
            ),
            "as type-literal division": (
                'const ratio = value as {} / "a/b".length; // trailing\n'
            ),
            "satisfies type-literal division": (
                'const ratio = value satisfies {} / "a/b".length; '
                "// trailing\n"
            ),
            "keyword-named method division": (
                'const ratio = obj.if(ok) / "a/b".length; // trailing\n'
            ),
            "label block regex": (
                "label: {} /[/*]literal/.test(value); // trailing\n"
            ),
            "case block regex": (
                "switch (value) { case 1: {} /[/*]literal/.test(value); } "
                "// trailing\n"
            ),
            "nested object division": (
                'const value = {item: {} / "a/b".length}; // trailing\n'
            ),
            "exported object division": (
                'export default {} / "a/b".length; // trailing\n'
            ),
            "function expression division": (
                'const ratio = function named() {} / "a/b".length; '
                "// trailing\n"
            ),
            "label in function expression": (
                "const fn = function () { label: {} /[/*]literal/.test(value); }; "
                "// trailing\n"
            ),
            "class expression division": (
                'const ratio = class Named {} / "a/b".length; // trailing\n'
            ),
            "class comparison heritage division": (
                'const ratio = class extends (a < b ? A : B) {} '
                '/ "a/b".length; // trailing\n'
            ),
            "default function declaration regex": (
                "export default function named() {} /[/*]literal/.test(value); "
                "// trailing\n"
            ),
            "default class declaration regex": (
                "export default class Named {} /[/*]literal/.test(value); "
                "// trailing\n"
            ),
            "template expression division": (
                'const value = `${{} / "a/b".length}`; // trailing\n'
            ),
            "JSX expression division": (
                'const view = <A value={{} / "a/b".length} />; // trailing\n'
            ),
            "if-body regex": (
                "if (ok) /[/*]literal/.test(value); // trailing\n"
            ),
            "while-body regex": (
                "while (ok) /[//]literal/.test(value); // trailing\n"
            ),
            "adjacent regex-close division": (
                "const value = /literal//2; // trailing\n"
            ),
            "adjacent regex-close comment": (
                "const value = /literal/// trailing\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                self.assertEqual(["// trailing"], comments(source, tsx=True))

    def test_type_alias_newline_restores_the_regex_goal(self):
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
            "union object": "type Alias = {} | { value: string }",
        }
        for label, alias in aliases.items():
            with self.subTest(label=label):
                source = alias + "\n/[/*]literal/.test(value); // trailing\n"
                self.assertEqual(["// trailing"], comments(source, tsx=True))

    def test_declaration_boundaries_restore_the_regex_goal(self):
        declarations = {
            "defaulted alias": "type Alias<T = string> = <U extends T = T>(value: U) => U",
            "nested alias": (
                "type Alias<T = Map<string, Array<number>>> = "
                "{ [K in keyof T]: T[K] }"
            ),
            "import equals": 'import Foo = require("foo")',
            "import qualified": "import Foo = Bar.Baz",
            "import declaration": 'import type { Foo } from "foo"',
            "export from": 'export { Foo } from "foo"',
            "export star": 'export * from "foo"',
            "export as namespace": "export as namespace Library",
            "ambient variable": "declare const value: Map<string, Array<number>>",
            "uninitialised variable": "let value: Map<string, Array<number>>",
            "final uninitialised declarator": (
                "let first = 1, value: Map<string, Array<number>>"
            ),
            "class declaration": (
                "class C<T extends Map<string, Array<number>> = "
                "Map<string, Array<number>>> extends Base<T> implements I<T> "
                "{ value!: T }"
            ),
            "interface declaration": (
                "interface I<T extends string = string> { value: T }"
            ),
            "function overload": (
                "function f<T extends string = string>(value: T): "
                "Promise<T | { value: T }>"
            ),
            "declared function": (
                "declare function f<T extends string = string>(value: T): T"
            ),
        }
        for tsx in (False, True):
            for label, declaration in declarations.items():
                with self.subTest(tsx=tsx, label=label):
                    source = (
                        declaration
                        + "\n/[/*]literal/.test(value); // trailing\n"
                    )
                    self.assertEqual(["// trailing"], comments(source, tsx=tsx))

    def test_declaration_state_does_not_leak_across_sequential_statements(self):
        source = (
            "type Alias<T = string> = T\n"
            "const template = `${value /* template comment */}`;\n"
            "declare const item: Alias\n"
            "/[/*]literal/.test(item); // trailing\n"
            'const ratio = compute()\n/ "a/b".length; // division trailing\n'
        )
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                self.assertEqual(
                    [
                        "/* template comment */",
                        "// trailing",
                        "// division trailing",
                    ],
                    comments(source, tsx=tsx),
                )

    def test_bodyless_function_declaration_state_does_not_leak(self):
        source = (
            "declare function f(): void\n"
            "/[a]/.test(value);\n"
            'const ratio = {} / "a/b".length; // trailing\n'
        )
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                self.assertEqual(["// trailing"], comments(source, tsx=tsx))

    def test_class_member_names_do_not_start_declaration_state(self):
        source = (
            "class Outer {\n"
            "  class = C\n"
            "  interface = I\n"
            "  ratio = {} / /* field comment */ 2\n"
            "}\n"
            "// trailing\n"
        )
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                self.assertEqual(
                    ["/* field comment */", "// trailing"],
                    comments(source, tsx=tsx),
                )

    def test_contextual_declaration_words_do_not_leak_expression_state(self):
        for word in ("interface", "module", "namespace"):
            source = (
                f"{word} = value\n"
                "const ratio = {} / /* expression comment */ 2\n"
                "// trailing\n"
            )
            for tsx in (False, True):
                with self.subTest(word=word, tsx=tsx):
                    self.assertEqual(
                        ["/* expression comment */", "// trailing"],
                        comments(source, tsx=tsx),
                    )

    def test_dynamic_import_keeps_expression_division_state(self):
        division = (
            'import("pkg")\n'
            "/ /* division comment */ 2; // trailing\n"
        )
        statement = (
            'import("pkg");\n'
            "/[/*]literal/.test(value); // trailing\n"
        )
        for tsx in (False, True):
            with self.subTest(tsx=tsx, form="division"):
                self.assertEqual(
                    ["/* division comment */", "// trailing"],
                    comments(division, tsx=tsx),
                )
            with self.subTest(tsx=tsx, form="statement"):
                self.assertEqual(["// trailing"], comments(statement, tsx=tsx))

    def test_declaration_following_regex_bytes_are_not_comments(self):
        source = (
            "declare const value: string\n"
            "/[/*] leverage [*/]/.test(value); // genuine trailing\n"
        )
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                self.assertEqual(
                    ["// genuine trailing"],
                    comments(source, tsx=tsx),
                )

    def test_declaration_boundaries_restore_the_jsx_goal(self):
        declarations = {
            "type alias": "type Alias = string",
            "bodyless function": "declare function read(): Value",
            "uninitialised variable": "let first: Value, second: Other",
            "side-effect import": 'import "pkg"',
            "default import": 'import value from "pkg"',
            "type import": 'import type { Value } from "pkg"',
            "re-export": 'export { value } from "pkg"',
            "export star": 'export * from "pkg"',
        }
        for label, declaration in declarations.items():
            with self.subTest(label=label):
                source = (
                    declaration
                    + "\n<div>/* raw JSX child */</div>; // trailing\n"
                )
                self.assertEqual(["// trailing"], comments(source, tsx=True))

        sequential = (
            "type Alias = string\n"
            "<div /> / /* division comment */ 2; // trailing\n"
        )
        self.assertEqual(
            ["/* division comment */", "// trailing"],
            comments(sequential, tsx=True),
        )

    def test_keyword_properties_and_contextual_identifiers_keep_slash_boundaries(self):
        property_names = {
            "await",
            "case",
            "default",
            "delete",
            "do",
            "else",
            "in",
            "instanceof",
            "new",
            "of",
            "return",
            "throw",
            "typeof",
            "void",
            "yield",
        }
        for accessor in (".", "?."):
            for name in sorted(property_names):
                with self.subTest(accessor=accessor, name=name):
                    source = (
                        f"const ratio = value{accessor}{name} "
                        "/ /* division comment */ 2; // trailing\n"
                    )
                    self.assertEqual(
                        ["/* division comment */", "// trailing"],
                        comments(source),
                    )

        identifier = (
            "const of = 2; const ratio = of / /* division comment */ 2; "
            "// trailing\n"
        )
        self.assertEqual(
            ["/* division comment */", "// trailing"],
            comments(identifier),
        )

        for name in ("await", "yield"):
            with self.subTest(contextual=name):
                source = f"const ratio = {name} / /* division comment */ 2;\n"
                _, errors = ts.comment_spans(source)
                self.assertEqual(
                    [(source.index("/"), "ambiguous slash after contextual identifier")],
                    errors,
                )

                failed_regex = (
                    f"const value = {name} /[unterminated "
                    "/* comment-shaped bytes */\n"
                )
                _, errors = ts.comment_spans(failed_regex)
                self.assertEqual(
                    [
                        (
                            failed_regex.index("/"),
                            "ambiguous slash after contextual identifier",
                        )
                    ],
                    errors,
                )

        contextual_comments = {
            "await line": (
                "async function read() { await /literal/// genuine line\n }",
                ["// genuine line"],
            ),
            "await block": (
                "async function read() { await /literal//* genuine block */ }",
                ["/* genuine block */"],
            ),
            "yield line": (
                "function* read() { yield /literal/// genuine line\n }",
                ["// genuine line"],
            ),
            "yield block": (
                "function* read() { yield /literal//* genuine block */ }",
                ["/* genuine block */"],
            ),
        }
        for label, (source, expected) in contextual_comments.items():
            with self.subTest(label=label):
                self.assertEqual(expected, comments(source))

        for keyword, wrapper in (
            ("await", "async function read() {{ const value = {body}; }}"),
            ("yield", "function* read() {{ const value = {body}; }}"),
        ):
            for operand in ("{}", "function() {}", "class {}"):
                with self.subTest(contextual=keyword, operand=operand):
                    source = wrapper.format(
                        body=(
                            f"{keyword} {operand} "
                            "/ /* division comment */ 2"
                        )
                    )
                    self.assertEqual(["/* division comment */"], comments(source))

        for_of = (
            "for (const value of /[/*]literal[*/]/) {} // trailing\n"
        )
        self.assertEqual(["// trailing"], comments(for_of))

        for binding in (
            "const await",
            "const yield",
            "const {value}",
            "const [value]",
        ):
            with self.subTest(for_of_binding=binding):
                source = (
                    f"for ({binding} of /[/*]literal[*/]/) {{}} "
                    "// trailing\n"
                )
                self.assertEqual(["// trailing"], comments(source))

    def test_expression_goal_unterminated_regex_is_a_named_error(self):
        for tsx in (False, True):
            with self.subTest(tsx=tsx):
                source = "const pattern = /unterminated"
                _, errors = ts.comment_spans(source, tsx=tsx)
                self.assertEqual(
                    [(source.index("/"), "unterminated regular expression literal")],
                    errors,
                )

    def test_expression_prefixes_keep_regex_and_jsx_bytes_out_of_comments(self):
        regex_cases = {
            "prefix increment": "const value = ++/[/*]literal[*/]/;",
            "prefix decrement": "const value = --/[/*]literal[*/]/;",
            "line-break prefix increment": (
                "let value = 1; value\n++/[/*]literal[*/]/;"
            ),
            "line-break prefix not": (
                "let value = 1; value\n!/[/*]literal[*/]/;"
            ),
            "array spread": "const value = [.../[/*]literal[*/]/];",
            "call spread": "read(.../[/*]literal[*/]/);",
            "object spread": "const value = {.../[/*]literal[*/]/};",
            "class declaration heritage": (
                "class Example extends /[/*]literal[*/]/ {}"
            ),
            "class expression heritage": (
                "const Example = class extends /[/*]literal[*/]/ {};"
            ),
            "class generic call heritage": (
                "class Example extends create<{value: string}>("
                "/[/*]literal[*/]/) {}"
            ),
            "decorator": "@/[/*]literal[*/]/ class Example {}",
        }
        for label, prefix in regex_cases.items():
            with self.subTest(label=label):
                source = prefix + " // trailing\n"
                self.assertEqual(["// trailing"], comments(source))

        postfix = (
            "let value = 1; const ratio = value++ "
            "/ /* division comment */ 2; // trailing\n"
        )
        self.assertEqual(
            ["/* division comment */", "// trailing"],
            comments(postfix),
        )

        for keyword in ("await", "yield"):
            with self.subTest(contextual_prefix=keyword):
                for operator in ("++", "--", "!"):
                    source = (
                        f"const ratio = {keyword}{operator} "
                        "/ /* division-shaped comment */ 2;\n"
                    )
                    _, errors = ts.comment_spans(source)
                    self.assertEqual(
                        [
                            (
                                source.index("/"),
                                "ambiguous slash after contextual identifier",
                            )
                        ],
                        errors,
                    )

        jsx_cases = {
            "array spread": "const value = [...<p>/* raw */</p>];",
            "call spread": "read(...<p>/* raw */</p>);",
            "class heritage": "class Example extends (<p>/* raw */</p>) {}",
        }
        for label, prefix in jsx_cases.items():
            with self.subTest(label=label):
                source = prefix + " // trailing\n"
                self.assertEqual(["// trailing"], comments(source, tsx=True))

        heritage_state = {
            "regex": (
                "class Example extends /literal/ {\n"
                "  interface = Value\n"
                "  ratio = {} / /* member division */ 2\n"
                "}\n// trailing\n"
            ),
            "JSX": (
                "class Example extends (<Base />) {\n"
                "  interface = Value\n"
                "  ratio = {} / /* member division */ 2\n"
                "}\n// trailing\n"
            ),
        }
        for label, source in heritage_state.items():
            with self.subTest(heritage_state=label):
                self.assertEqual(
                    ["/* member division */", "// trailing"],
                    comments(source, tsx=label == "JSX"),
                )

    def test_restricted_statement_asi_restores_regex_and_jsx_goals(self):
        cases = {
            "break": (
                "while (ok) { break\n/[/*]literal[*/]/.test(value); } "
                "// trailing\n",
                ["// trailing"],
                False,
            ),
            "continue": (
                "while (ok) { continue\n/[/*]literal[*/]/.test(value); } "
                "// trailing\n",
                ["// trailing"],
                False,
            ),
            "labelled break": (
                "outer: while (ok) { break /* label trivia */ outer\n"
                "/[/*]literal[*/]/.test(value); } // trailing\n",
                ["/* label trivia */", "// trailing"],
                False,
            ),
            "labelled continue": (
                "outer: while (ok) { continue outer\n"
                "/[/*]literal[*/]/.test(value); } // trailing\n",
                ["// trailing"],
                False,
            ),
            "debugger with block-comment line break": (
                "while (ok) { debugger /* retained\ntrivia */ "
                "/[/*]literal[*/]/.test(value); } // trailing\n",
                ["/* retained\ntrivia */", "// trailing"],
                False,
            ),
            "TSX after break": (
                "while (ok) { break\n<p>// raw child text</p>; } "
                "// trailing\n",
                ["// trailing"],
                True,
            ),
        }
        for label, (source, expected, tsx) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(expected, comments(source, tsx=tsx))

        for terminator in ("\r", "\r\n", "\u2028", "\u2029"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    "while (ok) { break"
                    + terminator
                    + "/[/*]literal[*/]/.test(value); } // trailing"
                )
                self.assertEqual(["// trailing"], comments(source))

    def test_declaration_boundaries_survive_several_statement_transitions(self):
        cases = {
            "generic ambient then alias": (
                "declare const item: Map<string, Array<number>>\n"
                "type Alias = string\n"
            ),
            "generic ambient then overload": (
                "declare const item: Map<string, Array<number>>\n"
                "function read<T>(value: T): T\n"
            ),
            "generic ambient then class": (
                "declare const item: Map<string, Array<number>>\n"
                "class Example {}\n"
            ),
            "generic overload then alias": (
                "function read<T>(value: T): Map<string, Array<number>>\n"
                "type Alias = string\n"
            ),
            "generic overload then class": (
                "function read<T>(value: T): Map<string, Array<number>>\n"
                "class Example {}\n"
            ),
        }
        for tsx in (False, True):
            for label, prefix in cases.items():
                with self.subTest(tsx=tsx, label=label):
                    source = (
                        prefix
                        + "/[/*]literal[*/]/.test(value); // trailing\n"
                    )
                    self.assertEqual(["// trailing"], comments(source, tsx=tsx))

        binary_expression = (
            "const result = left >\n"
            "class Named {} / /* division comment */ 2; // trailing\n"
        )
        self.assertEqual(
            ["/* division comment */", "// trailing"],
            comments(binary_expression),
        )

    def test_completed_statements_do_not_leak_into_later_declarations(self):
        cases = {
            "overload then async declaration": (
                "function read(): void\n"
                "async function write() {}\n"
                "/[/*]literal[*/]/.test(value); // trailing\n",
                False,
            ),
            "ambient overload then async generator": (
                "declare function read(): Promise<void>\n"
                "async function* write() {}\n"
                "<p>/* raw child text */</p>; // trailing\n",
                True,
            ),
            "do while then alias": (
                "do value; while (ready)\n"
                "type Alias = string\n"
                "/[/*]literal[*/]/.test(value); // trailing\n",
                False,
            ),
            "nested do while then alias": (
                "do do value; while (inner); while (outer)\n"
                "type Alias = string\n"
                "<p>/* raw child text */</p>; // trailing\n",
                True,
            ),
            "controlled do while then alias": (
                "if (enabled) do value; while (ready)\n"
                "type Alias = string\n"
                "/[/*]literal[*/]/.test(value); // trailing\n",
                False,
            ),
            "labelled do while then alias": (
                "retry: do value; while (ready)\n"
                "type Alias = string\n"
                "/[/*]literal[*/]/.test(value); // trailing\n",
                False,
            ),
            "block-bodied control in do while": (
                "do if (enabled) { value() } while (ready)\n"
                "type Alias = string\n"
                "/[/*]literal[*/]/.test(value); // trailing\n",
                False,
            ),
        }
        for label, (source, tsx) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(["// trailing"], comments(source, tsx=tsx))

        controls = {
            "async function expression": (
                "const read = async function() {}; "
                "read / /* division comment */ 2; // trailing\n",
                False,
            ),
            "while body named type": (
                "while (ready)\n"
                "  type / /* division comment */ 2; // trailing\n",
                False,
            ),
        }
        for label, (source, tsx) in controls.items():
            with self.subTest(label=label):
                self.assertEqual(
                    ["/* division comment */", "// trailing"],
                    comments(source, tsx=tsx),
                )

    def test_nested_construct_bodies_do_not_leak_across_statement_boundaries(self):
        cases = {
            "parenthesized class then block": (
                "(class {});\n"
                "{}\n"
                "/[/*]literal[*/]/.test(value); // trailing\n",
                False,
                ["// trailing"],
            ),
            "parenthesized function then control": (
                "(function() {});\n"
                "if (ready) {}\n"
                "<p>/* raw child text */</p>; // trailing\n",
                True,
                ["// trailing"],
            ),
            "nested function default then division": (
                "const ratio = function outer(arg = function inner() {}) {} "
                "/ /* division comment */ 2; // trailing\n",
                False,
                ["/* division comment */", "// trailing"],
            ),
            "nested class heritage then division": (
                "const ratio = class Outer extends (class Inner {}) {} "
                "/ /* division comment */ 2; // trailing\n",
                True,
                ["/* division comment */", "// trailing"],
            ),
        }
        for label, (source, tsx, expected) in cases.items():
            with self.subTest(label=label):
                self.assertEqual(expected, comments(source, tsx=tsx))

    def test_tsx_nested_generic_function_types_keep_the_type_goal(self):
        cases = {
            "declaration constraint": (
                "function read<T extends F<<U /* type comment */>"
                "(value: U) => U>>() {} // trailing\n"
            ),
            "interface constraint": (
                "interface Reader<T extends F<<U /* type comment */>"
                "(value: U) => U>> {} // trailing\n"
            ),
            "generic call": (
                "const read = make<<T /* type comment */>"
                "(value: T) => T>(); // trailing\n"
            ),
            "instantiation expression": (
                "const read = make<<T /* type comment */>"
                "(value: T) => T>; // trailing\n"
            ),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                self.assertEqual(
                    ["/* type comment */", "// trailing"],
                    comments(source, tsx=True),
                )

        jsx_controls = (
            "const value = left < <T>(/* raw child text */)</T>; ",
            "const value = left << <T>(/* raw child text */)</T>; ",
            "const value = left<<<T>(/* raw child text */)</T>; ",
        )
        for source in jsx_controls:
            with self.subTest(source=source):
                self.assertEqual(
                    ["// trailing"],
                    comments(source + "// trailing\n", tsx=True),
                )

    def test_nested_generic_type_goals_keep_one_forward_scan(self):
        def nested_function_type(depth):
            value = "string"
            for index in reversed(range(depth)):
                value = (
                    f"<T{index} extends F<{value}>>"
                    f"(value: T{index}) => T{index}"
                )
            return value

        source = CharacterCountingSource(
            "type Deep = " + nested_function_type(48) + "; // trailing\n"
        )
        spans, errors = ts.comment_spans(source, tsx=True)
        self.assertEqual([], errors)
        self.assertEqual(
            ["// trailing"],
            [str.__getitem__(source, slice(start, end)) for _, start, end in spans],
        )
        self.assertLess(source.character_reads, len(source) * 8)

    def test_line_comments_end_at_every_ecmascript_line_terminator(self):
        for terminator in ("\r\n", "\r", "\u2028", "\u2029"):
            with self.subTest(terminator=ascii(terminator)):
                source = (
                    "// first"
                    + terminator
                    + "const value = 1; // second"
                    + terminator
                    + "// third"
                )
                self.assertEqual(
                    ["// first", "// second", "// third"],
                    comments(source, tsx=True),
                )

    def test_tsx_unterminated_element_returns_a_named_error(self):
        _, errors = ts.comment_spans("const view = <p>", tsx=True)
        self.assertEqual(1, len(errors))
        self.assertIn("unterminated JSX element", errors[0][1])

    def test_comment_scanner_accepts_depth_64_and_refuses_depth_65(self):
        accepted = "const value = " + "{" * 64 + "0" + "}" * 64 + ";\n"
        refused = "const value = " + "{" * 65 + "0" + "}" * 65 + ";\n"
        self.assertEqual([], ts.comment_spans(accepted)[1])
        _, errors = ts.comment_spans(refused)
        self.assertEqual([(78, "nesting exceeds supported depth")], errors)

    def test_template_comment_scan_does_not_repeatedly_call_complete_lexer(self):
        source = "const value = `" + "".join("${item}" for _ in range(80)) + "`;\n"
        with mock.patch.object(ts, "lex", wraps=ts.lex) as complete_lex:
            _, errors = ts.comment_spans(source)
        self.assertEqual([], errors)
        self.assertLessEqual(complete_lex.call_count, 1)

    def test_tsx_candidates_do_not_search_the_remaining_suffix_repeatedly(self):
        source = "const value = " + " + ".join("<Name>" for _ in range(80)) + ";\n"
        with mock.patch.object(ts.re, "search", wraps=ts.re.search) as tail_search:
            ts.comment_spans(source, tsx=True)
        self.assertLessEqual(tail_search.call_count, 1)

    def test_many_valid_jsx_elements_do_not_copy_remaining_suffixes(self):
        source = SliceCountingSource(
            "const views = ["
            + ", ".join("<A>child text</A>" for _ in range(80))
            + "]; // real comment\n"
        )
        spans, errors = ts.comment_spans(source, tsx=True)
        self.assertEqual([], errors)
        self.assertEqual(0, source.suffix_slice_count)
        self.assertEqual(
            ["// real comment"],
            [str.__getitem__(source, slice(start, end)) for _, start, end in spans],
        )

    def test_many_valid_self_closing_elements_are_a_clean_linear_scan(self):
        source = SliceCountingSource(
            "const views = ["
            + ", ".join("<Name />" for _ in range(256))
            + "];\n"
        )
        spans, errors = ts.comment_spans(source, tsx=True)
        self.assertEqual([], errors)
        self.assertEqual([], spans)
        self.assertEqual(0, source.suffix_slice_count)


if __name__ == "__main__":
    unittest.main()
