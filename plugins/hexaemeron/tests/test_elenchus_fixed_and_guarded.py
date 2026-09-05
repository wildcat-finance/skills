"""The emitter writes one closed record, or refuses and writes nothing.

Every case here drives the command-line entry point against a real temporary
git repository, because two of the nine fields are derived from git and the
write boundary is a refusal set over a real worktree. The closed key set, each
refusal the runbook step names, the staged rename under an interrupted write
and one accepted record are all covered below.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "elenchus" / "scripts" / "fixed_and_guarded.py"

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


if __name__ == "__main__":
    unittest.main()
