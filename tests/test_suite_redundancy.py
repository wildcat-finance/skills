"""The suite-redundancy report classifies coverage without claiming authority.

The report's value is its negative half: a file that uniquely covers a line
cannot be removed without losing that line.  These tests hold the classifier to
that reading, and hold the duplicate finder to needing both an identical
covered-line set and an identical body before it names two methods the same.
"""

from pathlib import Path
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import suite_redundancy  # noqa: E402


class MeasuredUniverseTests(unittest.TestCase):
    """Only repository source outside a test tree enters the universe."""

    def setUp(self):
        self.root = os.path.realpath("/repo") + os.sep

    def measured(self, path):
        return suite_redundancy.measured(self.root, path, {})

    def test_a_source_file_under_the_root_is_measured(self):
        self.assertEqual(self.measured("/repo/scripts/thing.py"), "scripts/thing.py")

    def test_a_file_outside_the_root_is_ignored(self):
        self.assertFalse(self.measured("/elsewhere/thing.py"))

    def test_a_file_inside_a_tests_directory_is_ignored(self):
        self.assertFalse(self.measured("/repo/plugins/p/tests/helper.py"))

    def test_a_test_module_is_ignored_wherever_it_sits(self):
        self.assertFalse(self.measured("/repo/scripts/test_thing.py"))

    def test_a_dot_directory_is_ignored(self):
        self.assertFalse(self.measured("/repo/.venv/lib/thing.py"))

    def test_a_non_python_file_is_ignored(self):
        self.assertFalse(self.measured("/repo/scripts/thing.json"))

    def test_the_analyser_never_measures_itself(self):
        self.assertFalse(
            suite_redundancy.measured(
                os.path.realpath(suite_redundancy.SELF).rsplit(os.sep, 3)[0] + os.sep,
                suite_redundancy.SELF, {})
        )

    def test_a_verdict_is_cached_rather_than_recomputed(self):
        cache = {}
        suite_redundancy.measured(self.root, "/repo/scripts/thing.py", cache)
        self.assertEqual(cache["/repo/scripts/thing.py"], "scripts/thing.py")


class SignatureTests(unittest.TestCase):
    """A covered-line set hashes the same wherever it was collected."""

    def test_an_empty_set_has_no_signature(self):
        self.assertEqual(suite_redundancy.signature(set()), "")

    def test_the_signature_ignores_insertion_order(self):
        first = suite_redundancy.signature({"a.py:1", "a.py:2"})
        second = suite_redundancy.signature({"a.py:2", "a.py:1"})
        self.assertEqual(first, second)

    def test_a_different_set_has_a_different_signature(self):
        self.assertNotEqual(suite_redundancy.signature({"a.py:1"}),
                            suite_redundancy.signature({"a.py:2"}))


class ClassifyTests(unittest.TestCase):
    """Three categories, and only one of them is a review candidate."""

    def setUp(self):
        self.files = {
            "tests/test_alone.py": {"a.py:1", "a.py:2"},
            "tests/test_shared.py": {"a.py:1"},
            "tests/test_prose.py": set(),
        }
        self.tests = {"tests/test_alone.py": 3, "tests/test_shared.py": 2,
                      "tests/test_prose.py": 1}

    def rows(self):
        rows, _ = suite_redundancy.classify(self.files, self.tests)
        return {row["file"]: row for row in rows}

    def test_a_file_covering_a_line_alone_has_unique_coverage(self):
        row = self.rows()["tests/test_alone.py"]
        self.assertEqual(row["category"], "unique-coverage")
        self.assertEqual(row["unique"], 1)

    def test_a_file_whose_lines_are_all_shared_has_no_unique_coverage(self):
        row = self.rows()["tests/test_shared.py"]
        self.assertEqual(row["category"], "no-unique-coverage")
        self.assertEqual(row["unique"], 0)

    def test_a_file_covering_nothing_is_reported_separately(self):
        self.assertEqual(self.rows()["tests/test_prose.py"]["category"],
                         "no-measured-source")

    def test_a_shared_file_names_what_else_covers_its_lines(self):
        row = self.rows()["tests/test_shared.py"]
        self.assertEqual(row["covered_also_by"], [("tests/test_alone.py", 1)])

    def test_the_owner_map_records_every_file_covering_a_line(self):
        _, owners = suite_redundancy.classify(self.files, self.tests)
        self.assertEqual(owners["a.py:1"],
                         {"tests/test_alone.py", "tests/test_shared.py"})

    def test_the_test_count_is_carried_through(self):
        self.assertEqual(self.rows()["tests/test_alone.py"]["tests"], 3)


class MethodBodyTests(unittest.TestCase):
    """A body shape ignores the docstring and nothing else."""

    def write(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
        self.addCleanup(os.unlink, handle.name)
        handle.write(text)
        handle.close()
        return handle.name

    def test_two_bodies_differing_only_by_docstring_hash_alike(self):
        first = self.write("def a():\n    'one'\n    return 1\n")
        second = self.write("def a():\n    'another'\n    return 1\n")
        self.assertEqual(suite_redundancy.method_bodies(first)["a"],
                         suite_redundancy.method_bodies(second)["a"])

    def test_a_different_statement_changes_the_shape(self):
        first = self.write("def a():\n    return 1\n")
        second = self.write("def a():\n    return 2\n")
        self.assertNotEqual(suite_redundancy.method_bodies(first)["a"],
                            suite_redundancy.method_bodies(second)["a"])

    def test_an_unreadable_file_yields_no_shapes(self):
        self.assertEqual(suite_redundancy.method_bodies("/no/such/file.py"), {})

    def test_a_file_that_does_not_parse_yields_no_shapes(self):
        self.assertEqual(suite_redundancy.method_bodies(self.write("def (\n")), {})


class DuplicateTests(unittest.TestCase):
    """Both the covered lines and the body must match before a pair is named."""

    def setUp(self):
        self.source = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
        self.addCleanup(os.unlink, self.source.name)
        self.source.write(
            "class T:\n"
            "    def test_one(self):\n        return 1\n"
            "    def test_two(self):\n        return 1\n"
            "    def test_three(self):\n        return 9\n"
        )
        self.source.close()

    def method(self, name, lines):
        return {"file": self.source.name, "id": f"m.T.{name}",
                "covered": len(lines), "signature": suite_redundancy.signature(lines),
                "suite_unique": sorted(lines)}

    def test_identical_coverage_and_body_group_together(self):
        groups = suite_redundancy.duplicates(
            [self.method("test_one", {"a.py:1"}), self.method("test_two", {"a.py:1"})],
            {})
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 2)

    def test_identical_coverage_with_a_different_body_is_not_a_duplicate(self):
        groups = suite_redundancy.duplicates(
            [self.method("test_one", {"a.py:1"}),
             self.method("test_three", {"a.py:1"})], {})
        self.assertEqual(groups, [])

    def test_an_identical_body_over_different_lines_is_not_a_duplicate(self):
        groups = suite_redundancy.duplicates(
            [self.method("test_one", {"a.py:1"}), self.method("test_two", {"a.py:2"})],
            {})
        self.assertEqual(groups, [])

    def test_a_method_covering_nothing_never_groups(self):
        groups = suite_redundancy.duplicates(
            [self.method("test_one", set()), self.method("test_two", set())], {})
        self.assertEqual(groups, [])

    def test_sole_coverage_counts_only_lines_no_other_file_covers(self):
        records = [self.method("test_one", {"a.py:1", "a.py:2"})]
        suite_redundancy.duplicates(
            records, {"a.py:1": {self.source.name}, "a.py:2": {"other.py", self.source.name}})
        self.assertEqual(records[0]["sole_coverage"], 1)


class LoadTests(unittest.TestCase):
    """Only payloads carrying this schema are merged."""

    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def write(self, name, payload):
        path = os.path.join(self.directory, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def test_two_payloads_merge_their_line_sets(self):
        self.write("a.json", {"schema": suite_redundancy.SCHEMA,
                              "files": {"t.py": {"tests": 1, "lines": ["a.py:1"]}}})
        self.write("b.json", {"schema": suite_redundancy.SCHEMA,
                              "files": {"t.py": {"tests": 2, "lines": ["a.py:2"]}}})
        files, tests, _ = suite_redundancy.load(self.directory)
        self.assertEqual(files["t.py"], {"a.py:1", "a.py:2"})
        self.assertEqual(tests["t.py"], 3)

    def test_a_foreign_payload_is_skipped(self):
        self.write("c.json", {"schema": "something-else",
                              "files": {"t.py": {"tests": 1, "lines": ["a.py:1"]}}})
        files, _, _ = suite_redundancy.load(self.directory)
        self.assertEqual(files, {})

    def test_method_payloads_accumulate(self):
        self.write("d.json", {"schema": suite_redundancy.SCHEMA,
                              "methods": [{"file": "t.py", "id": "x", "covered": 0,
                                           "signature": "", "suite_unique": []}]})
        _, _, methods = suite_redundancy.load(self.directory)
        self.assertEqual(len(methods), 1)


class AttributeTests(unittest.TestCase):
    """One traced run attributes executed lines to the test that ran them."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.path = list(sys.path)
        self.modules = set(sys.modules)
        os.makedirs(os.path.join(self.root, "pkg"))
        os.makedirs(os.path.join(self.root, "suite"))
        self.write("pkg/__init__.py", "")
        self.write("pkg/thing.py", "def widen(value):\n    if value:\n        return 1\n    return 0\n")
        self.write("suite/__init__.py", "")
        self.write("suite/test_thing.py",
                   "import unittest\nfrom pkg.thing import widen\n\n\n"
                   "class T(unittest.TestCase):\n"
                   "    def test_true(self):\n        self.assertEqual(widen(1), 1)\n"
                   "    def test_prose(self):\n        self.assertEqual('a', 'a')\n")

    def tearDown(self):
        sys.path[:] = self.path
        for name in set(sys.modules) - self.modules:
            del sys.modules[name]

    def write(self, relative, text):
        with open(os.path.join(self.root, relative), "w", encoding="utf-8") as handle:
            handle.write(text)

    def test_a_file_level_run_records_the_lines_its_tests_executed(self):
        payload = suite_redundancy.attribute(
            os.path.join(self.root, "suite"), self.root, self.root, False)
        self.assertEqual(payload["tests_run"], 2)
        self.assertEqual(payload["failures"], 0)
        record = payload["files"]["suite/test_thing.py"]
        self.assertEqual(record["tests"], 2)
        self.assertIn("pkg/thing.py:3", record["lines"])

    def test_a_method_level_run_separates_a_test_that_executes_nothing(self):
        payload = suite_redundancy.attribute(
            os.path.join(self.root, "suite"), self.root, self.root, True)
        covered = {record["id"].rsplit(".", 1)[-1]: record["covered"]
                   for record in payload["methods"]}
        self.assertGreater(covered["test_true"], 0)
        self.assertEqual(covered["test_prose"], 0)

    def test_the_payload_names_its_schema(self):
        payload = suite_redundancy.attribute(
            os.path.join(self.root, "suite"), self.root, self.root, False)
        self.assertEqual(payload["schema"], suite_redundancy.SCHEMA)


class RenderTests(unittest.TestCase):
    """The report leads with counts and marks candidates as review, not deletion."""

    def test_the_header_counts_every_category(self):
        stream = io.StringIO()
        rows, _ = suite_redundancy.classify(
            {"t.py": {"a.py:1"}, "u.py": set()}, {"t.py": 1, "u.py": 1})
        suite_redundancy.render(rows, [], [], stream)
        text = stream.getvalue()
        self.assertIn("test files          2", text)
        self.assertIn("no-measured-source   1", text)

    def test_a_candidate_line_says_it_is_not_a_deletion(self):
        stream = io.StringIO()
        rows, _ = suite_redundancy.classify(
            {"t.py": {"a.py:1"}, "u.py": {"a.py:1"}}, {"t.py": 1, "u.py": 1})
        suite_redundancy.render(rows, [], [], stream)
        self.assertIn("review, do not delete on this alone", stream.getvalue())


class MainTests(unittest.TestCase):
    """The command refuses an empty attribution directory rather than passing."""

    def test_a_directory_with_no_payload_exits_two(self):
        directory = tempfile.mkdtemp()
        with contextlib.redirect_stderr(io.StringIO()) as captured:
            status = suite_redundancy.main(["report", "--attribution", directory])
        self.assertEqual(status, 2)
        self.assertIn("no attribution payloads found", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
