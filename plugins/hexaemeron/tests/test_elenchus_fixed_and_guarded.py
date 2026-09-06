"""The emitter writes one closed record, or refuses and writes nothing.

Every case here drives the command-line entry point against a real temporary
git repository, because two of the nine fields are derived from git and the
write boundary is a refusal set over a real worktree. The closed key set, each
refusal the runbook step names, the staged rename under an interrupted write
and one accepted record are all covered below.
"""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "elenchus" / "scripts" / "fixed_and_guarded.py"
ELENCHUS = ROOT / "skills" / "elenchus" / "scripts" / "elenchus.py"

spec = importlib.util.spec_from_file_location("elenchus_fixed_and_guarded", SCRIPT)
emitter = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = emitter
spec.loader.exec_module(emitter)

GUARD_FILE = "tests/test_widget.py"
GUARD_TEST = "WidgetRegression.test_negative_width_is_refused"
OUTPUT = "a stack trace nobody should copy into a record\n"

EVIDENCE_FIELDS = (
    "reproduction", "causal_mechanism", "minimal_case", "repair", "guard",
    "unfixed_parent", "fixed_tree", "suites", "verdict",
)

# The scratch repository the end-to-end case builds: one real defect, the
# regression test that catches it, and the repair that closes it.
DEFECTIVE_WIDGET = '''\
"""A widget with a width."""


class Widget:
    def __init__(self, width):
        self.width = width
        if width is None:
            raise ValueError("width is required")

    def area(self, height):
        return self.width * height
'''

REPAIRED_WIDGET = '''\
"""A widget with a width."""


class Widget:
    def __init__(self, width):
        if width is None:
            raise ValueError("width is required")
        if width < 0:
            raise ValueError("width must not be negative")
        self.width = width

    def area(self, height):
        return self.width * height
'''

REGRESSION_TEST = '''\
import unittest

from src.widget import Widget


class WidgetRegression(unittest.TestCase):
    def test_negative_width_is_refused(self):
        with self.assertRaises(ValueError):
            Widget(width=-1)
'''

# The scratch repository owns its runner, because `elenchus.py` classifies from
# a report the runner writes rather than from an exit code.
SCRATCH_RUNNER = '''\
"""Run the suite and write the report the declared runner contract names."""
import json
import sys
import unittest
from pathlib import Path

suite = unittest.defaultTestLoader.discover(".", pattern="test_*.py")
outcome = unittest.TextTestRunner(verbosity=1).run(suite)
target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({
    "schema": "elenchus.unittest.v1",
    "complete": True,
    "testsRun": outcome.testsRun,
    "failures": len(outcome.failures),
    "errors": len(outcome.errors),
    "skipped": len(outcome.skipped),
    "expectedFailures": len(outcome.expectedFailures),
    "unexpectedSuccesses": len(outcome.unexpectedSuccesses),
}), encoding="utf-8")
raise SystemExit(not outcome.wasSuccessful())
'''

SCRATCH_IGNORES = "__pycache__/\n.elenchus/\ninputs/\nrecords/\n"

# The line the mechanism starts on, read from the source rather than counted by
# hand, so the record's `site` stays true if the defective source moves.
DEFECT_LINE = DEFECTIVE_WIDGET.splitlines().index("        self.width = width") + 1

MECHANISM = (
    "Widget.__init__ assigns self.width before any bound is checked, so a "
    "negative width is stored and reaches area()."
)


def normalised(report):
    """The five counters `elenchus.py` derives from a unittest report.

    The record carries normalised counts on both sides, so the fixed tree's
    own report is reduced the same way the parent's already was.
    """
    return {
        "complete": report["complete"],
        "executed": report["testsRun"] - report["skipped"] - report["expectedFailures"],
        "assertion_failures": report["failures"],
        "errors": report["errors"] + report["unexpectedSuccesses"],
        "skipped": report["skipped"] + report["expectedFailures"],
    }


class Fixture:
    """A real temporary git history: a base, then the repair on top of it."""

    def __init__(self):
        self.path = Path(tempfile.mkdtemp(prefix="fixed-and-guarded-"))
        self.run("init", "--quiet", "-b", "main")
        self.run("config", "--local", "commit.gpgsign", "false")
        self.run("config", "user.email", "fixture@example.org")
        self.run("config", "user.name", "Fixture")
        self.base = self.commit("base", {GUARD_FILE: "# no guard yet\n"})
        self.repair = self.commit(
            "repair the mechanism",
            {GUARD_FILE: "# the guard\n", "src/widget.py": "# the fix\n"},
        )
        # F018 binds `guard.test` to the guard file's blob at the repair commit
        # and not to the worktree copy, so the repair is amended to commit the
        # regression test itself while the worktree keeps the two-word body
        # the write-boundary cases read back.
        (self.path / GUARD_FILE).write_text(REGRESSION_TEST, encoding="utf-8")
        self.run("add", "-A")
        self.run("-c", "commit.gpgsign=false", "commit", "--quiet", "--amend", "--no-edit")
        self.repair = self.run("rev-parse", "HEAD").strip()
        (self.path / GUARD_FILE).write_text("# the guard\n", encoding="utf-8")
        self.inputs = self.path / "inputs"
        self.inputs.mkdir()

    def run(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def commit(self, message, files):
        for name, body in files.items():
            target = self.path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        self.run("add", "-A")
        self.run("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", message)
        return self.run("rev-parse", "HEAD").strip()

    def write(self, name, value):
        target = self.inputs / name
        target.write_text(json.dumps(value), encoding="utf-8")
        return target

    def remove(self):
        shutil.rmtree(self.path, ignore_errors=True)


class Scratch(Fixture):
    """A scratch repository holding a real defect, before it is repaired.

    Everything the end-to-end case writes lives under this temporary
    directory, including the inputs the emitter reads and the records it
    writes. The one path outside it belongs to `elenchus.py`, which stages
    its detached parent worktree under a temporary directory of its own and
    removes it when the comparison ends.
    """

    def __init__(self):
        self.path = Path(tempfile.mkdtemp(prefix="fixed-and-guarded-demo-"))
        self.run("init", "--quiet", "-b", "main")
        self.run("config", "--local", "commit.gpgsign", "false")
        self.run("config", "user.email", "fixture@example.org")
        self.run("config", "user.name", "Fixture")
        self.base = self.commit("base", {
            ".gitignore": SCRATCH_IGNORES,
            "src/__init__.py": "",
            "src/widget.py": DEFECTIVE_WIDGET,
            "tests/__init__.py": "",
            "runner.py": SCRATCH_RUNNER,
        })
        self.inputs = self.path / "inputs"
        self.inputs.mkdir()


def draft_for(fixture, **overrides):
    draft = {
        "reproduction": {
            "command": "python3 -m unittest tests.test_widget",
            "output_sha256": hashlib.sha256(OUTPUT.encode("utf-8")).hexdigest(),
            "output_bytes": len(OUTPUT.encode("utf-8")),
        },
        "causal_mechanism": {
            "account": "Widget.__init__ stores width before validating it, so a "
                       "negative width reaches the area computation.",
            "site": "src/widget.py:14",
        },
        "minimal_case": {
            "description": "Widget(width=-1).area() raises rather than refusing.",
            "path": "tests/test_widget.py",
        },
        "repair": {"commit": fixture.repair, "files": ["src/widget.py", GUARD_FILE]},
        "guard": {"file": GUARD_FILE, "test": GUARD_TEST},
        "fixed_tree": {
            "commit": fixture.repair,
            "report": {
                "complete": True, "executed": 12, "assertion_failures": 0,
                "errors": 0, "skipped": 0,
            },
        },
        "suites": [
            {"command": "python3 -m unittest tests.test_widget", "exit_code": 0},
            {"command": "python3 tests/run_tests.py", "exit_code": 0},
        ],
    }
    draft.update(overrides)
    return draft


def result_for(fixture, **overrides):
    result = {
        "ref": fixture.repair,
        "status": "guarded",
        "tests": [GUARD_FILE],
        "detail": "the runner report records a parent assertion failure",
        "report": {
            "complete": True, "executed": 12, "assertion_failures": 1,
            "errors": 0, "skipped": 0,
        },
        "exit_code": 1,
        "output": OUTPUT,
    }
    result.update(overrides)
    return result


class Harness(unittest.TestCase):
    """One fixture per case, and one place that runs the command."""

    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.remove)

    def emit(self, draft=None, result=None, out="records/fixed-and-guarded.json",
             repo=None):
        draft_path = self.fixture.write(
            "draft.json", draft_for(self.fixture) if draft is None else draft)
        result_path = self.fixture.write(
            "result.json", result_for(self.fixture) if result is None else result)
        return self.invoke([
            "--repo", str(self.fixture.path if repo is None else repo),
            "--draft", str(draft_path),
            "--result", str(result_path),
            "--out", out,
        ])

    def invoke(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = emitter.main(argv)
        return code, out.getvalue(), err.getvalue()

    def accepted_record(self, out="records/fixed-and-guarded.json"):
        code, _, err = self.emit(out=out)
        self.assertEqual(code, 0, err)
        return json.loads((self.fixture.path / out).read_text(encoding="utf-8"))

    def assertRefused(self, outcome, expected_code, expected_field):
        """A refusal exits non-zero and names its rule and its field."""
        code, _stdout, err = outcome
        self.assertEqual(code, 1, err)
        self.assertIn(expected_code, err)
        self.assertIn(expected_field, err)


class AcceptedRecord(Harness):
    def test_the_emitter_writes_a_record_the_checker_accepts(self):
        out = "records/fixed-and-guarded.json"
        record = self.accepted_record(out)
        self.assertEqual(record["schema"], emitter.SCHEMA)
        code, stdout, err = self.invoke(["--check", str(self.fixture.path / out)])
        self.assertEqual(code, 0, err)
        self.assertIn("clean", stdout)

    def test_the_record_holds_the_schema_and_the_nine_fields_and_no_more(self):
        record = self.accepted_record()
        self.assertEqual(set(record), {"schema", *EVIDENCE_FIELDS})

    def test_the_parent_is_re_derived_rather_than_supplied(self):
        record = self.accepted_record()
        self.assertEqual(record["unfixed_parent"]["commit"], self.fixture.base)
        self.assertNotEqual(record["unfixed_parent"]["commit"], record["repair"]["commit"])

    def test_the_two_result_derived_fields_are_taken_without_translation(self):
        record = self.accepted_record()
        result = result_for(self.fixture)
        self.assertEqual(record["verdict"]["status"], result["status"])
        self.assertEqual(record["verdict"]["detail"], result["detail"])
        self.assertEqual(record["unfixed_parent"]["report"], result["report"])

    def test_the_reproduction_output_reaches_the_record_only_as_a_digest(self):
        out = "records/fixed-and-guarded.json"
        self.accepted_record(out)
        written = (self.fixture.path / out).read_text(encoding="utf-8")
        self.assertNotIn(OUTPUT.strip(), written)
        record = json.loads(written)
        self.assertEqual(
            record["reproduction"]["output_sha256"],
            hashlib.sha256(OUTPUT.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            record["reproduction"]["output_bytes"], len(OUTPUT.encode("utf-8")))

    def test_a_useless_minimal_case_is_recorded_as_null(self):
        code, _, err = self.emit(draft=draft_for(self.fixture, minimal_case=None))
        self.assertEqual(code, 0, err)
        record = json.loads(
            (self.fixture.path / "records/fixed-and-guarded.json").read_text("utf-8"))
        self.assertIsNone(record["minimal_case"])


class ClosedKeySet(Harness):
    def test_an_unknown_draft_key_is_refused(self):
        draft = draft_for(self.fixture)
        draft["recurrence_of"] = "some other record"
        self.assertRefused(
            self.emit(draft=draft), "F005", "draft")

    def test_a_missing_draft_key_is_refused(self):
        draft = draft_for(self.fixture)
        del draft["suites"]
        self.assertRefused(
            self.emit(draft=draft), "F005", "draft")

    def test_an_unknown_result_key_is_refused(self):
        result = result_for(self.fixture)
        result["corpus"] = "anamnesis"
        self.assertRefused(
            self.emit(result=result), "F006", "result")

    def test_a_result_with_no_report_is_refused(self):
        result = result_for(self.fixture)
        del result["report"]
        self.assertRefused(
            self.emit(result=result), "F006", "result.report")

    def test_a_duplicate_key_in_the_draft_is_refused(self):
        path = self.fixture.inputs / "duplicate.json"
        path.write_text('{"suites": [], "suites": []}', encoding="utf-8")
        result_path = self.fixture.write("result.json", result_for(self.fixture))
        self.assertRefused(self.invoke([
            "--repo", str(self.fixture.path), "--draft", str(path),
            "--result", str(result_path), "--out", "records/r.json",
        ]), "F000", "--draft")

    def test_a_record_carrying_a_cross_record_identifier_is_refused(self):
        out = "records/fixed-and-guarded.json"
        record = self.accepted_record(out)
        record["recurrence_of"] = "elenchus-fixed-and-guarded/v1:other"
        path = self.fixture.inputs / "linked.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertRefused(self.invoke(["--check", str(path)]), "F001", "schema")

    def test_every_evidence_field_is_required(self):
        record = self.accepted_record()
        for field in EVIDENCE_FIELDS:
            with self.subTest(field=field):
                short = {key: value for key, value in record.items() if key != field}
                path = self.fixture.inputs / f"without-{field}.json"
                path.write_text(json.dumps(short), encoding="utf-8")
                self.assertRefused(
                    self.invoke(["--check", str(path)]), "F001", "schema")

    def test_a_record_under_another_schema_is_refused(self):
        record = self.accepted_record()
        record["schema"] = "elenchus-fixed-and-guarded/v2"
        path = self.fixture.inputs / "future.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertRefused(self.invoke(["--check", str(path)]), "F001", "schema")

    def test_bytes_that_are_not_one_json_object_are_refused(self):
        path = self.fixture.inputs / "prose.md"
        path.write_text("The fix is guarded. Trust me.\n", encoding="utf-8")
        self.assertRefused(self.invoke(["--check", str(path)]), "F000", "--check")


class TextBounds(Harness):
    def test_an_over_cap_text_field_is_refused(self):
        draft = draft_for(self.fixture)
        draft["causal_mechanism"]["account"] = "a" * (emitter.MAX_TEXT_BYTES + 1)
        self.assertRefused(
            self.emit(draft=draft), "F003", "causal_mechanism.account")

    def test_a_non_printable_text_field_is_refused(self):
        draft = draft_for(self.fixture)
        draft["causal_mechanism"]["account"] = "the mechanism\nand its second line"
        self.assertRefused(
            self.emit(draft=draft), "F003", "causal_mechanism.account")

    def test_an_empty_text_field_is_refused(self):
        draft = draft_for(self.fixture)
        draft["reproduction"]["command"] = ""
        self.assertRefused(
            self.emit(draft=draft), "F003", "reproduction.command")

    def test_a_reproduction_digest_that_is_not_a_sha_256_is_refused(self):
        draft = draft_for(self.fixture)
        draft["reproduction"]["output_sha256"] = OUTPUT
        self.assertRefused(
            self.emit(draft=draft), "F002", "reproduction.output_sha256")

    def test_an_input_over_the_byte_cap_is_refused(self):
        path = self.fixture.inputs / "huge.json"
        path.write_text(
            json.dumps({"pad": "x" * (emitter.MAX_INPUT_BYTES + 16)}), encoding="utf-8")
        self.assertRefused(self.invoke(["--check", str(path)]), "F000", "--check")

    def test_a_nested_input_past_the_depth_cap_is_refused(self):
        path = self.fixture.inputs / "deep.json"
        depth = emitter.MAX_JSON_DEPTH + 4
        path.write_text("[" * depth + "]" * depth, encoding="utf-8")
        self.assertRefused(self.invoke(["--check", str(path)]), "F000", "--check")


class GuardBinding(Harness):
    def test_a_guard_outside_the_repairs_changed_tests_is_refused(self):
        draft = draft_for(self.fixture)
        draft["guard"]["file"] = "tests/test_something_else.py"
        self.assertRefused(
            self.emit(draft=draft), "F007", "guard.file")

    def test_a_guard_file_that_escapes_the_repository_is_refused(self):
        draft = draft_for(self.fixture)
        draft["guard"]["file"] = "../tests/test_widget.py"
        self.assertRefused(
            self.emit(draft=draft), "F002", "guard.file")

    def test_the_named_guard_test_is_carried_into_the_record(self):
        record = self.accepted_record()
        self.assertEqual(record["guard"], {"file": GUARD_FILE, "test": GUARD_TEST})

    def test_a_guard_test_absent_from_the_guard_file_at_the_repair_is_refused(self):
        """Step 3 round 2 of the #1275 run emitted this draft at exit 0.

        F018 reads the guard file's blob at the repair commit, so the refusal
        names the first absent segment, the file and the commit, and it runs
        before the output path is prepared, so no directory is created.
        """
        draft = draft_for(self.fixture)
        draft["guard"]["test"] = "NoSuchClass.test_this_test_does_not_exist_anywhere"
        out = "records/guard-test-absent.json"
        outcome = self.emit(draft=draft, out=out)
        self.assertRefused(outcome, "F018", "guard.test")
        _code, _stdout, err = outcome
        self.assertIn("NoSuchClass does not occur", err)
        self.assertIn(GUARD_FILE, err)
        self.assertIn(self.fixture.repair, err)
        self.assertFalse((self.fixture.path / out).exists())
        self.assertFalse((self.fixture.path / "records").exists())

    def test_a_module_qualified_name_whose_module_segments_are_absent_is_refused(self):
        """The operator drops the prefix; the file never spells its own module."""
        draft = draft_for(self.fixture)
        draft["guard"]["test"] = f"tests.test_widget.{GUARD_TEST}"
        out = "records/module-qualified.json"
        outcome = self.emit(draft=draft, out=out)
        self.assertRefused(outcome, "F018", "guard.test")
        self.assertIn("tests does not occur", outcome[2])
        self.assertFalse((self.fixture.path / out).exists())

    def test_a_name_whose_every_segment_occurs_as_a_whole_word_emits(self):
        for index, name in enumerate((
            GUARD_TEST,
            "test_negative_width_is_refused",
            "WidgetRegression:test_negative_width_is_refused",
        )):
            with self.subTest(name=name):
                draft = draft_for(self.fixture)
                draft["guard"]["test"] = name
                out = f"records/whole-word-{index}.json"
                code, _stdout, err = self.emit(draft=draft, out=out)
                self.assertEqual(code, 0, err)
                record = json.loads(
                    (self.fixture.path / out).read_text(encoding="utf-8"))
                self.assertEqual(record["guard"]["test"], name)

    def test_a_segment_occurring_only_inside_a_longer_identifier_is_refused(self):
        """Whole-word occurrence: a prefix of the real test name is not the name."""
        draft = draft_for(self.fixture)
        draft["guard"]["test"] = "WidgetRegression.test_negative_width"
        out = "records/prefix-only.json"
        outcome = self.emit(draft=draft, out=out)
        self.assertRefused(outcome, "F018", "guard.test")
        self.assertIn("test_negative_width does not occur", outcome[2])
        self.assertFalse((self.fixture.path / out).exists())

    def test_a_guard_file_blob_over_the_input_cap_is_refused(self):
        """`git cat-file -s` bounds the read before `git cat-file blob` runs."""
        big = REGRESSION_TEST + "# " + "x" * emitter.MAX_INPUT_BYTES + "\n"
        repair = self.fixture.commit("a guard too large to bind", {GUARD_FILE: big})
        draft = draft_for(self.fixture)
        draft["repair"]["commit"] = repair
        draft["fixed_tree"]["commit"] = repair
        result = result_for(self.fixture, ref=repair)
        out = "records/oversized-guard.json"
        argv_seen = []
        original = emitter.subprocess.run

        def observe(argv, **kwargs):
            argv_seen.append(list(argv))
            return original(argv, **kwargs)

        with mock.patch.object(emitter.subprocess, "run", observe):
            outcome = self.emit(draft=draft, result=result, out=out)
        self.assertRefused(outcome, "F018", "guard.test")
        self.assertIn(str(emitter.MAX_INPUT_BYTES), outcome[2])
        self.assertFalse((self.fixture.path / out).exists())
        cat_file = [argv[argv.index("cat-file") + 1] for argv in argv_seen if "cat-file" in argv]
        self.assertEqual(cat_file, ["-s"])

    def test_a_guard_file_absent_or_not_a_blob_at_the_repair_is_refused(self):
        """A path the result names is not thereby a blob the emitter can bind."""
        for shape, guard_file in (
            ("absent from the commit", "tests/test_missing.py"),
            ("a directory", "tests"),
        ):
            with self.subTest(shape=shape):
                draft = draft_for(self.fixture)
                draft["guard"]["file"] = guard_file
                draft["repair"]["files"] = ["src/widget.py", guard_file]
                result = result_for(self.fixture, tests=[guard_file])
                out = f"records/{guard_file.replace('/', '-')}.json"
                outcome = self.emit(draft=draft, result=result, out=out)
                self.assertRefused(outcome, "F018", "guard.test")
                self.assertIn(guard_file, outcome[2])
                self.assertFalse((self.fixture.path / out).exists())


class Verdicts(Harness):
    def test_each_state_other_than_guarded_is_refused_at_emission(self):
        for status in ("passed", "unguarded", "inconclusive"):
            with self.subTest(status=status):
                out = f"records/{status}.json"
                self.assertRefused(
                    self.emit(result=result_for(self.fixture, status=status), out=out),
                    "F004", "result.status")
                self.assertFalse((self.fixture.path / out).exists())

    def test_a_state_outside_the_four_is_refused(self):
        result = result_for(self.fixture, status="probably-fine")
        self.assertRefused(
            self.emit(result=result), "F006", "result.status")

    def test_a_record_whose_verdict_is_not_guarded_is_refused_on_its_own(self):
        record = self.accepted_record()
        record["verdict"]["status"] = "inconclusive"
        path = self.fixture.inputs / "inconclusive.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertRefused(self.invoke(["--check", str(path)]), "F004", "verdict.status")


class RecordRelations(Harness):
    """The refusals decided from fields the record already carries."""

    def test_a_record_naming_one_commit_as_both_trees_is_refused(self):
        record = self.accepted_record()
        record["unfixed_parent"]["commit"] = record["fixed_tree"]["commit"]
        path = self.fixture.inputs / "one-commit.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertRefused(
            self.invoke(["--check", str(path)]), "F011", "unfixed_parent.commit")

    def test_a_guarded_record_whose_parent_report_never_failed_is_refused(self):
        record = self.accepted_record()
        record["unfixed_parent"]["report"]["assertion_failures"] = 0
        record["unfixed_parent"]["report"]["errors"] = 0
        path = self.fixture.inputs / "never-failed.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertRefused(
            self.invoke(["--check", str(path)]), "F012", "verdict.status")

    def test_a_guarded_record_whose_parent_report_errored_is_refused(self):
        record = self.accepted_record()
        record["unfixed_parent"]["report"]["errors"] = 1
        self.assertGreater(record["unfixed_parent"]["report"]["assertion_failures"], 0)
        path = self.fixture.inputs / "parent-errored.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        self.assertRefused(
            self.invoke(["--check", str(path)]), "F013", "verdict.status")

    def test_a_guarded_record_whose_fixed_tree_report_failed_is_refused(self):
        for counter in ("assertion_failures", "errors"):
            with self.subTest(counter=counter):
                record = self.accepted_record(out=f"records/{counter}.json")
                record["fixed_tree"]["report"][counter] = 2
                path = self.fixture.inputs / f"fixed-tree-{counter}.json"
                path.write_text(json.dumps(record), encoding="utf-8")
                self.assertRefused(
                    self.invoke(["--check", str(path)]), "F014", "verdict.status")

    def test_a_record_whose_fixed_tree_is_not_the_repair_is_refused(self):
        """The fixed tree is the tree the repair produced, and no other.

        This one reaches the emit path as well: the emitter took
        `fixed_tree.commit` straight from the draft and bound it to nothing,
        so a genuine producer could write a record asserting its guard passed
        on a tree unrelated to the fix, and exit zero doing it.
        """
        unrelated = self.fixture.commit("unrelated", {"src/other.py": "# later\n"})
        with self.subTest(path="emit"):
            draft = draft_for(self.fixture)
            draft["fixed_tree"]["commit"] = unrelated
            out = "records/wrong-fixed-tree.json"
            self.assertRefused(
                self.emit(draft=draft, out=out), "F015", "fixed_tree.commit")
            self.assertFalse((self.fixture.path / out).exists())
        with self.subTest(path="check"):
            record = self.accepted_record(out="records/genuine.json")
            record["fixed_tree"]["commit"] = unrelated
            path = self.fixture.inputs / "wrong-fixed-tree.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertRefused(
                self.invoke(["--check", str(path)]), "F015", "fixed_tree.commit")

    def test_a_record_whose_guard_is_absent_from_the_repairs_files_is_refused(self):
        """A guard the repair did not touch is not the Boundary's named guard.

        F007 settles this on the emit path against the result's changed test
        files.  `--check` has no result beside the record, so the record's own
        account of those files, `repair.files`, is what decides it there.
        """
        with self.subTest(path="check"):
            record = self.accepted_record()
            record["repair"]["files"] = ["src/widget.py"]
            path = self.fixture.inputs / "guard-outside-the-repair.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertRefused(
                self.invoke(["--check", str(path)]), "F016", "guard.file")
        with self.subTest(path="emit"):
            draft = draft_for(self.fixture)
            draft["repair"]["files"] = ["src/widget.py"]
            out = "records/guard-outside-the-repair.json"
            self.assertRefused(
                self.emit(draft=draft, out=out), "F016", "guard.file")
            self.assertFalse((self.fixture.path / out).exists())

    def test_a_guarded_record_whose_fixed_tree_executed_no_tests_is_refused(self):
        """A comparison that ran no test is not a guard, on either path.

        F014 reads only counters above zero, so nothing read the executed
        count at all.  `classify` calls a report recording no executed tests
        `inconclusive`, and the Boundary names a zero-test comparison
        explicitly.  Like F015 this reaches emission, because `fixed_tree`
        is the operator's own rerun the emitter never checks.
        """
        empty = {
            "complete": True, "executed": 0, "assertion_failures": 0,
            "errors": 0, "skipped": 0,
        }
        with self.subTest(path="emit"):
            draft = draft_for(self.fixture)
            draft["fixed_tree"]["report"] = dict(empty)
            out = "records/no-tests-executed.json"
            self.assertRefused(
                self.emit(draft=draft, out=out), "F017", "verdict.status")
            self.assertFalse((self.fixture.path / out).exists())
        with self.subTest(path="check"):
            record = self.accepted_record(out="records/genuine-executed.json")
            record["fixed_tree"]["report"] = dict(empty)
            path = self.fixture.inputs / "no-tests-executed.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertRefused(
                self.invoke(["--check", str(path)]), "F017", "verdict.status")

    def test_a_parent_report_executing_no_tests_needs_no_eleventh_counterpart(self):
        """The parent side is already closed, checked rather than assumed.

        `executed` 0 forces both parent counters to 0, because the count rule
        refuses outcomes above `executed`; F012 then settles the record.  A
        parent claiming a failure it never executed is refused earlier still.
        """
        with self.subTest(shape="zero counters"):
            record = self.accepted_record()
            record["unfixed_parent"]["report"] = {
                "complete": True, "executed": 0, "assertion_failures": 0,
                "errors": 0, "skipped": 0,
            }
            path = self.fixture.inputs / "parent-executed-none.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertRefused(
                self.invoke(["--check", str(path)]), "F012", "verdict.status")
        with self.subTest(shape="a failure it never executed"):
            record = self.accepted_record(out="records/parent-impossible.json")
            record["unfixed_parent"]["report"] = {
                "complete": True, "executed": 0, "assertion_failures": 1,
                "errors": 0, "skipped": 0,
            }
            path = self.fixture.inputs / "parent-impossible.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            self.assertRefused(
                self.invoke(["--check", str(path)]),
                "F002", "unfixed_parent.report")

    def test_a_record_whose_two_trees_differ_and_whose_parent_failed_is_accepted(self):
        """The seven above must not refuse the record the emitter actually writes."""
        record = self.accepted_record()
        self.assertNotEqual(
            record["unfixed_parent"]["commit"], record["fixed_tree"]["commit"])
        self.assertGreater(
            record["unfixed_parent"]["report"]["assertion_failures"], 0)
        self.assertEqual(record["unfixed_parent"]["report"]["errors"], 0)
        self.assertEqual(
            record["fixed_tree"]["report"]["assertion_failures"]
            + record["fixed_tree"]["report"]["errors"], 0)
        self.assertGreater(record["fixed_tree"]["report"]["executed"], 0)
        self.assertEqual(
            record["fixed_tree"]["commit"], record["repair"]["commit"])
        self.assertIn(record["guard"]["file"], record["repair"]["files"])
        path = self.fixture.inputs / "genuine.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        code, out, err = self.invoke(["--check", str(path)])
        self.assertEqual(code, 0, err)
        self.assertIn("clean", out)

    def test_a_malformed_record_is_not_also_charged_the_relation_refusals(self):
        """A shape the per-field rules already refuse names those rules only."""
        record = self.accepted_record()
        record["unfixed_parent"]["commit"] = "not-a-commit"
        record["unfixed_parent"]["report"]["assertion_failures"] = "none"
        path = self.fixture.inputs / "malformed.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        code, _out, err = self.invoke(["--check", str(path)])
        self.assertEqual(code, 1, err)
        self.assertIn("F002", err)
        for code in ("F011", "F012", "F013", "F014", "F015", "F016", "F017"):
            self.assertNotIn(code, err)

    def test_a_repair_omitting_a_changed_test_file_is_refused_at_emit(self):
        """Step 1 round 6 of the #1275 run, S1-R6-02, emitted this draft at exit 0.

        F019 reads `result["tests"]` against `repair.files` directly after
        F007, names every missing path, and runs before the output path is
        prepared, so no directory is created.
        """
        result = result_for(
            self.fixture,
            tests=[GUARD_FILE, "tests/test_other.py", "tests/test_third.py"],
        )
        out = "records/repair-files-short.json"
        outcome = self.emit(result=result, out=out)
        self.assertRefused(outcome, "F019", "repair.files")
        _code, _stdout, err = outcome
        self.assertIn("tests/test_other.py", err)
        self.assertIn("tests/test_third.py", err)
        self.assertNotIn(GUARD_FILE, err)
        self.assertFalse((self.fixture.path / out).exists())
        self.assertFalse((self.fixture.path / "records").exists())

    def test_check_still_accepts_an_unbound_guard_test_and_a_short_repair_files(self):
        """The stated boundary, not a defect: `--check` runs no emit-path rule.

        F018 needs the guard file's blob and F019 needs `result["tests"]`,
        and a record carries neither, so `clean` excludes both by
        construction.  A record whose `guard.test` no file holds and whose
        `repair.files` omits a test file the comparison used reads `clean`,
        exactly as it did before the two rules existed.
        """
        result = result_for(self.fixture, tests=[GUARD_FILE, "tests/test_other.py"])
        draft = draft_for(self.fixture)
        draft["repair"]["files"] = ["src/widget.py", GUARD_FILE, "tests/test_other.py"]
        out = "records/genuine-two-tests.json"
        code, _stdout, err = self.emit(draft=draft, result=result, out=out)
        self.assertEqual(code, 0, err)
        record = json.loads((self.fixture.path / out).read_text(encoding="utf-8"))
        record["guard"]["test"] = "NoSuchClass.test_this_test_does_not_exist_anywhere"
        record["repair"]["files"] = ["src/widget.py", GUARD_FILE]
        path = self.fixture.inputs / "unbound-but-clean.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        code, stdout, err = self.invoke(["--check", str(path)])
        self.assertEqual(code, 0, err)
        self.assertIn("clean", stdout)
        self.assertNotIn("F018", err)
        self.assertNotIn("F019", err)


class ParentDerivation(Harness):
    def test_a_commit_with_no_parent_is_refused(self):
        result = result_for(self.fixture, ref=self.fixture.base)
        draft = draft_for(self.fixture)
        draft["repair"]["commit"] = self.fixture.base
        self.assertRefused(
            self.emit(draft=draft, result=result), "F008", "unfixed_parent.commit")

    def test_a_ref_no_repository_resolves_is_refused(self):
        result = result_for(self.fixture, ref="no-such-ref")
        self.assertRefused(
            self.emit(result=result), "F008", "unfixed_parent.commit")

    def test_a_ref_that_is_not_the_drafted_repair_is_refused(self):
        """Otherwise the parent belongs to some other commit than the repair."""
        unrelated = self.fixture.commit("unrelated", {"src/other.py": "# later\n"})
        out = "records/mismatch.json"
        self.assertRefused(
            self.emit(result=result_for(self.fixture, ref=unrelated), out=out),
            "F010", "unfixed_parent.commit")
        self.assertFalse((self.fixture.path / out).exists())

    def test_a_ref_beginning_with_a_dash_is_refused(self):
        """A ref beginning with a dash is an option, not a name."""
        self.assertRefused(
            self.emit(result=result_for(self.fixture, ref="--since=2020-01-01")),
            "F006", "result.ref")

    def test_an_annotated_tag_naming_the_repair_is_accepted(self):
        """`git rev-parse <tag>` names the tag object, not the commit.

        `elenchus.py` takes any ref and echoes it into its result unresolved,
        and its own `diff-tree` and `<ref>^` reads peel a tag for themselves.
        Comparing the unpeeled object against the drafted repair refused a
        record whose parent was correct all along.
        """
        self.fixture.run("tag", "-a", "the-repair", "-m", "the repair",
                         self.fixture.repair)
        out = "records/annotated-tag.json"
        code, _stdout, err = self.emit(
            result=result_for(self.fixture, ref="the-repair"), out=out)
        self.assertEqual(code, 0, err)
        record = json.loads(
            (self.fixture.path / out).read_text(encoding="utf-8"))
        self.assertEqual(record["unfixed_parent"]["commit"], self.fixture.base)
        self.assertNotEqual(
            record["unfixed_parent"]["commit"], record["fixed_tree"]["commit"])


class OutputBoundary(Harness):
    def test_an_absolute_output_path_is_refused(self):
        target = self.fixture.path / "records/absolute.json"
        self.assertRefused(self.emit(out=str(target)), "F009", "--out")
        self.assertFalse(target.exists())

    def test_a_traversing_output_path_is_refused(self):
        self.assertRefused(self.emit(out="../escaped.json"), "F009", "--out")
        self.assertFalse((self.fixture.path.parent / "escaped.json").exists())

    def test_a_symlinked_parent_component_is_refused(self):
        outside = Path(tempfile.mkdtemp(prefix="fixed-and-guarded-outside-"))
        self.addCleanup(shutil.rmtree, outside, True)
        os.symlink(outside, self.fixture.path / "records")
        self.assertRefused(self.emit(out="records/fixed-and-guarded.json"), "F009", "--out")
        self.assertFalse((outside / "fixed-and-guarded.json").exists())

    def test_an_existing_destination_is_refused(self):
        out = "records/fixed-and-guarded.json"
        self.accepted_record(out)
        before = (self.fixture.path / out).read_bytes()
        self.assertRefused(self.emit(out=out), "F009", "--out")
        self.assertEqual((self.fixture.path / out).read_bytes(), before)

    def test_a_tracked_destination_is_refused(self):
        self.assertRefused(self.emit(out=GUARD_FILE), "F009", "--out")
        self.assertEqual(
            (self.fixture.path / GUARD_FILE).read_text(encoding="utf-8"), "# the guard\n")

    def test_a_parent_component_that_is_a_regular_file_is_refused(self):
        self.assertRefused(self.emit(out="src/widget.py/record.json"), "F009", "--out")


class StagedWrite(Harness):
    def test_an_interrupted_emit_leaves_no_file_the_checker_accepts(self):
        out = "records/fixed-and-guarded.json"
        with mock.patch.object(emitter.os, "replace", side_effect=OSError("killed")):
            self.assertRefused(self.emit(out=out), "F009", "--out")
        self.assertFalse((self.fixture.path / out).exists())
        self.assertEqual(
            sorted(p.name for p in (self.fixture.path / "records").iterdir()), [])

    def test_a_destination_that_cannot_be_written_names_its_code(self):
        """An unattended round reads a code and a field, never a traceback."""
        out = "records/fixed-and-guarded.json"
        with mock.patch.object(
            emitter.tempfile, "mkstemp", side_effect=PermissionError("read-only"),
        ):
            self.assertRefused(self.emit(out=out), "F009", "--out")
        self.assertFalse((self.fixture.path / out).exists())

    def test_the_record_is_staged_in_the_destination_directory(self):
        seen = []
        original = emitter.os.replace

        def observe(source, destination):
            seen.append((Path(source).parent, Path(destination).parent))
            return original(source, destination)

        with mock.patch.object(emitter.os, "replace", observe):
            self.accepted_record()
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], seen[0][1])


class Invocation(Harness):
    def test_check_refuses_to_share_an_invocation_with_emission(self):
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stderr(io.StringIO()):
                emitter.main(["--check", "record.json", "--out", "other.json"])
        self.assertEqual(raised.exception.code, 2)

    def test_emission_needs_all_three_of_its_paths(self):
        with self.assertRaises(SystemExit) as raised:
            with contextlib.redirect_stderr(io.StringIO()):
                emitter.main(["--draft", "draft.json"])
        self.assertEqual(raised.exception.code, 2)

    def test_the_command_runs_as_a_script(self):
        out = "records/fixed-and-guarded.json"
        draft_path = self.fixture.write("draft.json", draft_for(self.fixture))
        result_path = self.fixture.write("result.json", result_for(self.fixture))
        run = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.fixture.path),
             "--draft", str(draft_path), "--result", str(result_path), "--out", out],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        checked = subprocess.run(
            [sys.executable, str(SCRIPT), "--check", str(self.fixture.path / out)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr)


class EndToEnd(unittest.TestCase):
    """The demo path, run against a repository with a failure really in it.

    Every other case here hands the emitter a drafted result. This one earns
    the result: it reproduces a failure, repairs the mechanism, lets
    `elenchus.py` compare the guard against the detached parent, and emits the
    record from what those runs actually produced.

    `docs/elenchus-fixed-and-guarded-record/demonstration.md` records one run
    of the same path by hand, with its commands, exit codes and refusal text.
    This case drives that path under the suite, so the demonstration is
    reproduced rather than taken on trust.
    """

    def setUp(self):
        self.scratch = Scratch()
        self.addCleanup(self.scratch.remove)

    def in_scratch(self, *arguments):
        """One command in the scratch repository, argv only and no shell."""
        return subprocess.run(
            arguments, cwd=str(self.scratch.path), capture_output=True,
            text=True, check=False,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        )

    def test_the_demo_path_emits_a_record_and_refuses_the_ones_it_should(self):
        scratch = self.scratch

        # Reproduce. The guard is written but not yet committed, so it runs
        # against the defect: a guard that never went red is not a guard.
        (scratch.path / GUARD_FILE).write_text(REGRESSION_TEST, encoding="utf-8")
        reproduction = self.in_scratch(
            sys.executable, "-m", "unittest", "tests.test_widget", "-v")
        self.assertEqual(reproduction.returncode, 1, reproduction.stderr)
        self.assertIn("AssertionError: ValueError not raised", reproduction.stderr)
        observed = (reproduction.stdout + reproduction.stderr).encode("utf-8")

        # Fix the cause, and commit the repair carrying its guard.
        repair = scratch.commit(
            "fix(widget): validate the width before storing it",
            {"src/widget.py": REPAIRED_WIDGET},
        )
        touched = sorted(scratch.run(
            "diff-tree", "--no-commit-id", "--name-only", "-r", repair).split())
        self.assertEqual(touched, ["src/widget.py", GUARD_FILE])

        # Verify: the focused guard, then the suite, both on the fixed tree.
        focused = self.in_scratch(
            sys.executable, "-m", "unittest", "tests.test_widget", "-v")
        self.assertEqual(focused.returncode, 0, focused.stderr)
        suite = self.in_scratch(
            sys.executable, "runner.py", ".elenchus/fixed-tree.json")
        self.assertEqual(suite.returncode, 0, suite.stderr)
        fixed = normalised(json.loads(
            (scratch.path / ".elenchus/fixed-tree.json").read_text("utf-8")))
        self.assertGreater(fixed["executed"], 0)
        self.assertEqual(fixed["assertion_failures"] + fixed["errors"], 0)

        # The guard comparison against the detached parent, which is where the
        # verdict and the parent's report come from.
        comparison = self.in_scratch(
            sys.executable, str(ELENCHUS), "--repo", ".", "--ref", repair,
            "--test-command",
            f"{shlex.quote(sys.executable)} runner.py {{report}}",
            "--report-format", "unittest-json-v1",
            "--report-file", ".elenchus/parent.json",
            "--format", "json",
        )
        self.assertEqual(comparison.returncode, 0, comparison.stderr)
        result = json.loads(comparison.stdout)
        self.assertEqual(result["status"], "guarded", result["detail"])
        self.assertEqual(result["report"]["assertion_failures"], 1)

        # Emit. Seven fields come from the operator's draft, two from the
        # result, and the parent commit from one `git rev-parse`.
        draft = scratch.write("draft.json", {
            "reproduction": {
                "command": "python3 -m unittest tests.test_widget -v",
                "output_sha256": hashlib.sha256(observed).hexdigest(),
                "output_bytes": len(observed),
            },
            "causal_mechanism": {
                "account": MECHANISM,
                "site": f"src/widget.py:{DEFECT_LINE}",
            },
            "minimal_case": {
                "description": "Widget(width=-1) returns an instance "
                               "instead of raising ValueError.",
                "path": GUARD_FILE,
            },
            "repair": {"commit": repair, "files": touched},
            "guard": {"file": GUARD_FILE, "test": GUARD_TEST},
            "fixed_tree": {"commit": repair, "report": fixed},
            "suites": [
                {"command": "python3 -m unittest tests.test_widget -v",
                 "exit_code": focused.returncode},
                {"command": "python3 runner.py .elenchus/fixed-tree.json",
                 "exit_code": suite.returncode},
            ],
        })
        out = "records/fixed-and-guarded.json"
        emitted = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(scratch.path),
             "--draft", str(draft),
             "--result", str(scratch.write("result.json", result)),
             "--out", out],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(emitted.returncode, 0, emitted.stderr)
        self.assertIn("written", emitted.stdout)

        written = (scratch.path / out).read_text(encoding="utf-8")
        record = json.loads(written)
        self.assertEqual(record["unfixed_parent"]["commit"], scratch.base)
        self.assertEqual(record["verdict"]["status"], "guarded")
        # A real reproduction output is where a credential in a stack trace
        # would be. It reaches the record as a digest and never as bytes.
        self.assertNotIn("AssertionError", written)

        accepted = self.check(scratch.path / out)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertIn("clean", accepted.stdout)

        # The same record, each way it stops being one the Promise authorises.
        def without_an_evidence_field(one):
            del one["guard"]

        def a_verdict_other_than_guarded(one):
            one["verdict"]["status"] = "inconclusive"

        def a_parent_that_never_failed(one):
            one["unfixed_parent"]["report"]["assertion_failures"] = 0

        for name, mutate, code, field in (
            ("one evidence field removed", without_an_evidence_field,
             "F001", "schema"),
            ("a verdict other than guarded", a_verdict_other_than_guarded,
             "F004", "verdict.status"),
            ("a parent report that never failed", a_parent_that_never_failed,
             "F012", "verdict.status"),
        ):
            with self.subTest(record=name):
                mutated = copy.deepcopy(record)
                mutate(mutated)
                path = scratch.inputs / f"{code}.json"
                path.write_text(json.dumps(mutated), encoding="utf-8")
                refused = self.check(path)
                self.assertEqual(refused.returncode, 1, refused.stdout)
                self.assertIn(code, refused.stderr)
                self.assertIn(field, refused.stderr)

        # The demo path of the #1318 study, argv for argv, from inside the
        # scratch repository: the two hostile drafts the #1275 audit
        # constructed against the genuine result, then `--check` on the
        # record emitted above. Each hostile draft is the genuine one with a
        # single field changed, so the refusal is the emit path's and not a
        # malformed input's.
        genuine = json.loads(draft.read_text(encoding="utf-8"))
        guard_test_absent = copy.deepcopy(genuine)
        guard_test_absent["guard"]["test"] = (
            "NoSuchClass.test_this_test_does_not_exist_anywhere")
        scratch.write("guard-test-absent.json", guard_test_absent)
        repair_files_short = copy.deepcopy(genuine)
        repair_files_short["repair"]["files"] = ["src/widget.py"]
        scratch.write("repair-files-short.json", repair_files_short)

        for name, code, field in (
            ("guard-test-absent", "F018", "guard.test"),
            ("repair-files-short", "F019", "repair.files"),
        ):
            with self.subTest(draft=name):
                refused = self.in_scratch(
                    sys.executable, str(SCRIPT),
                    "--draft", f"inputs/{name}.json",
                    "--result", "inputs/result.json",
                    "--out", f"records/{name}.json",
                )
                self.assertEqual(refused.returncode, 1, refused.stdout)
                self.assertEqual(refused.stdout, "")
                self.assertIn(f"{code} {field}", refused.stderr)
                self.assertFalse((scratch.path / "records" / f"{name}.json").exists())

        checked = self.in_scratch(
            sys.executable, str(SCRIPT), "--check", "records/fixed-and-guarded.json")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(checked.stdout, "records/fixed-and-guarded.json: clean\n")
        self.assertEqual(checked.stderr, "")

    def check(self, path):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--check", str(path)],
            capture_output=True, text=True, check=False,
        )


if __name__ == "__main__":
    unittest.main()
