"""The Markdown outliner slices headings and fences and confesses the rest."""

from pathlib import Path
import io
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "horos" / "scripts"))  # noqa: E402  (locates horos.py)

from languages.markdown import markdown  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
FIXTURE = PLUGIN / "examples" / "fixture-md" / "GUIDE.md"

EXPECTED = """module: Market guide
front matter: lines 1-4
# Market guide  (line 6)
    ## Opening a market  (line 12)
        ``` bash  (lines 16-19)
        ### Parameters  (line 21)
            ``` solidity  (lines 26-28)
        ### Quoted note  (line 32)
    Closing a market  (setext h2)  (line 36)
    ## Appendix  (line 45)
declarations: 8
unparsed: 1 region(s): lines 39-41
"""


def run(source):
    out = io.StringIO()
    code = markdown.outline("test.md", source, out)
    return code, out.getvalue()


def headings(output):
    """The heading lines of an outline, stripped of their indent."""
    return [
        line.strip()
        for line in output.splitlines()
        if "  (line " in line
    ]


class MarkdownOutlineTests(unittest.TestCase):
    def test_the_fixture_outline_is_pinned(self):
        source = FIXTURE.read_text(encoding="utf-8")
        out = io.StringIO()
        code = markdown.outline(str(FIXTURE), source, out)
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), EXPECTED)

    def test_the_md_suffix_dispatches_through_the_registry(self):
        import horos  # noqa: E402  (registry dispatch under test)

        out = io.StringIO()
        self.assertEqual(horos.map_file(str(FIXTURE), out=out), 0)
        self.assertEqual(out.getvalue(), EXPECTED)
        self.assertIn(".md", __import__("languages").supported())

    def test_the_markdown_suffix_is_refused(self):
        import horos  # noqa: E402  (registry dispatch under test)

        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "notes.markdown")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("# a\n")
            out = io.StringIO()
            self.assertEqual(horos.map_file(path, out=out), 2)
        self.assertIn("map supports", out.getvalue())
        self.assertNotIn(".markdown", __import__("languages").supported())

    # fence-shadowed-heading
    def test_a_hash_line_inside_a_fence_is_never_a_heading(self):
        for opener, closer in (("```", "```"), ("~~~", "~~~"), ("   ```", "```"), ("  ~~~", " ~~~")):
            with self.subTest(opener=opener):
                code, output = run(f"{opener}\n# shadowed\n{closer}\n# real\n")
                self.assertEqual(code, 0)
                self.assertEqual(headings(output), ["# real  (line 4)"])
                self.assertIn("```  (lines 1-3)", output)

    def test_a_fence_closes_only_at_a_bare_closer_of_its_length(self):
        code, output = run("````\n```\n# shadowed\n``` text\n# still shadowed\n````\n# real\n")
        self.assertEqual(code, 0)
        self.assertEqual(headings(output), ["# real  (line 7)"])
        self.assertIn("```  (lines 1-6)", output)

    # html-hidden-heading
    def test_a_heading_inside_an_html_block_is_confessed_not_outlined(self):
        code, output = run("<div>\n# hidden\n</div>\n\n# shown\n")
        self.assertEqual(code, 0)
        self.assertEqual(headings(output), ["# shown  (line 5)"])
        self.assertIn("unparsed: 1 region(s): lines 1-3", output)
        _, output = run("<!--\n# hidden\n-->\n# shown\n")
        self.assertEqual(headings(output), ["# shown  (line 4)"])
        self.assertIn("unparsed: 1 region(s): lines 1-3", output)

    def test_a_type_seven_html_line_cannot_interrupt_a_paragraph(self):
        code, output = run("para\n<span>\n# shown\n")
        self.assertEqual(code, 0)
        self.assertEqual(headings(output), ["# shown  (line 3)"])
        self.assertIn("unparsed: none", output)

    # setext-under-lazy-line
    def test_a_dash_line_under_a_lazy_continuation_is_not_a_heading(self):
        for source in ("- foo\nbar\n---\n", "> quoted\nlazy\n---\n"):
            with self.subTest(source=source):
                code, output = run(source)
                self.assertEqual(code, 0)
                self.assertEqual(headings(output), [])
                self.assertIn("declarations: 0", output)

    def test_a_dash_line_under_an_open_paragraph_is_a_setext_h2(self):
        code, output = run("para one\npara two\n---\n\nTitle\n===\n")
        self.assertEqual(code, 0)
        self.assertEqual(
            headings(output),
            ["para one  (setext h2)  (line 1)", "Title  (setext h1)  (line 5)"],
        )
        self.assertIn("module: Title", output)

    # container-prefix
    def test_a_heading_behind_quote_markers_is_seen_at_its_level(self):
        code, output = run("> # Quoted\n> text\n\n> > ## Deep\n\n- ### In item\n")
        self.assertEqual(code, 0)
        self.assertEqual(
            output.splitlines()[1:4],
            ["# Quoted  (line 1)", "    ## Deep  (line 4)", "        ### In item  (line 6)"],
        )
        self.assertIn("declarations: 3", output)

    def test_a_fence_inside_a_list_item_closes_with_the_item(self):
        code, output = run("- a\n\n  ```py\n  code\nout\n# h\n")
        self.assertEqual(code, 0)
        self.assertIn("``` py  (lines 3-4)", output)
        self.assertEqual(headings(output), ["# h  (line 6)"])
        self.assertNotIn("lexer:", output)

    # front-matter-phantom
    def test_a_line_one_dash_block_is_front_matter_not_a_setext_heading(self):
        code, output = run("---\ntitle: x\n---\n\n# Real\n")
        self.assertEqual(code, 0)
        self.assertEqual(output.splitlines()[:3], ["module: Real", "front matter: lines 1-3", "# Real  (line 5)"])
        self.assertIn("declarations: 1", output)
        _, output = run("text\n---\ntitle: x\n---\n")
        self.assertNotIn("front matter", output)

    # unterminated-fence
    def test_an_unterminated_fence_confesses_the_remainder_and_exits_1(self):
        code, output = run("# a\n```\n# not\nmore\n")
        self.assertEqual(code, 1)
        self.assertEqual(headings(output), ["# a  (line 1)"])
        self.assertIn("lexer: unterminated fence at line 2", output)
        self.assertIn("unparsed: 1 region(s): lines 2-4", output)
        self.assertIn("declarations: 1", output)

    # hostile-input
    def test_an_empty_file_and_a_cr_only_file_exit_0_without_exception(self):
        code, output = run("")
        self.assertEqual(code, 0)
        self.assertEqual(output, "module: (no title)\ndeclarations: 0\nunparsed: none\n")
        code, output = run("# a\r```\rcode\r```\r## b\r")
        self.assertEqual(code, 0)
        self.assertNotIn("lexer:", output)

    # no-execution
    def test_a_file_whose_body_is_python_is_outlined_and_never_run(self):
        with tempfile.TemporaryDirectory() as root:
            marker = os.path.join(root, "executed")
            path = os.path.join(root, "trap.md")
            body = (
                "# Trap\n\n"
                f"open({marker!r}, 'w').close()\n"
                "raise RuntimeError('the outliner executed its input')\n"
            )
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(body)
            out = io.StringIO()
            code = markdown.outline(path, body, out)
            self.assertEqual(code, 0)
            self.assertFalse(os.path.exists(marker))
        self.assertIn("module: Trap", out.getvalue())
        self.assertIn("declarations: 1", out.getvalue())

    def test_module_title_falls_back_when_no_h1_exists(self):
        code, output = run("## only an h2\n")
        self.assertEqual(code, 0)
        self.assertIn("module: (no title)", output)

    # hostile-input: S2-R1-01
    def test_a_long_line_of_markers_and_spaces_is_outlined_in_linear_time(self):
        # Each case took 5 s or more before the fix and takes milliseconds
        # after it; the bound leaves room for a loaded host.
        markers, spaces = 20_000, 30_000
        cases = (
            ("* " * markers + "x\n", [], "declarations: 0"),
            ("# a" + " " * spaces + "b\n", ["# a" + " " * spaces + "b  (line 1)"], "module: a" + " " * spaces + "b"),
            ("# a" + " " * spaces + "b #\n", ["# a" + " " * spaces + "b #  (line 1)"], "module: a" + " " * spaces + "b"),
        )
        for source, heads, expected in cases:
            with self.subTest(source=source[:12]):
                started = time.perf_counter()
                code, output = run(source)
                elapsed = time.perf_counter() - started
                self.assertLess(elapsed, 2.0, f"{elapsed:.1f} s on one line of {len(source)} bytes")
                self.assertEqual(code, 0)
                self.assertEqual(headings(output), heads)
                self.assertIn(expected, output)

    # container-prefix, html-hidden-heading, setext-under-lazy-line: S2-R1-02
    def test_a_container_closing_closes_the_html_block_or_fence_it_holds(self):
        code, output = run("> <!--\n# h\n")
        self.assertEqual(code, 0)
        self.assertEqual(headings(output), ["# h  (line 2)"])
        self.assertIn("unparsed: 1 region(s): line 1", output)
        code, output = run("> ```\n\n> ```\n# h\n")
        self.assertEqual(code, 0)
        self.assertIn("```  (lines 1-1)", output)
        self.assertIn("```  (lines 3-3)", output)
        self.assertEqual(headings(output), ["# h  (line 4)"])
        self.assertNotIn("lexer:", output)

    def test_an_underline_at_the_paragraph_depth_after_a_lazy_line_is_a_heading(self):
        for source, head in (
            ("> Foo\nbar\n> ===\n", "Foo  (setext h1)  (line 1)"),
            ("- foo\nbar\n  ---\n", "foo  (setext h2)  (line 1)"),
        ):
            with self.subTest(source=source):
                code, output = run(source)
                self.assertEqual(code, 0)
                self.assertEqual(headings(output), [head])


if __name__ == "__main__":
    unittest.main()
