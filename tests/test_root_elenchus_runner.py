"""The root Elenchus runner contains its report path and writes one schema.

`tests/run_tests.py` accepts a filesystem write path from the command line,
which is a boundary this repository did not previously open under `tests/`.
The containment it ports from `plugins/hexaemeron/tests/run_tests.py` is the
control that closes it, so the refusals are covered here rather than only the
path that writes a file. Each case also reads the diagnostic, because a later
audit round scores a missing or malformed report `inconclusive` and needs the
message to name which precondition failed.
"""

from pathlib import Path
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tests" / "run_tests.py"

SCHEMA = "elenchus.unittest.v1"
SCHEMA_KEYS = {
    "schema",
    "complete",
    "testsRun",
    "failures",
    "errors",
    "skipped",
    "expectedFailures",
    "unexpectedSuccesses",
}


def load_runner():
    """Load the runner by path so every invocation reaches the same file."""
    spec = importlib.util.spec_from_file_location("root_run_tests", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_tests = load_runner()


@contextlib.contextmanager
def worktree():
    """Bind one disposable directory as the worktree the runner resolves."""
    previous = os.getcwd()
    with tempfile.TemporaryDirectory() as directory:
        os.chdir(directory)
        try:
            yield Path(os.getcwd())
        finally:
            os.chdir(previous)


def refusal(*argv):
    """Return the diagnostic printed while one report path is refused."""
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        try:
            run_tests.report_target(list(argv))
        except SystemExit:
            return stderr.getvalue()
    raise AssertionError(f"report path was accepted: {argv}")


def written_payload(relative):
    """Write one report through the runner and return what it left on disk."""
    with worktree():
        target = run_tests.report_target(["--elenchus-report", relative])
        run_tests.write_report(target, run_tests.result_payload(unittest.TestResult()))
        return json.loads(Path(relative).read_text(encoding="utf-8"))


class ReportPathContainmentTests(unittest.TestCase):
    def test_a_parent_traversal_component_is_refused(self):
        with worktree():
            message = refusal("--elenchus-report", "../escape.json")
        self.assertIn("must stay inside the current worktree", message)

    def test_an_absolute_path_outside_the_worktree_is_refused(self):
        with worktree(), tempfile.TemporaryDirectory() as outside:
            message = refusal(
                "--elenchus-report", str(Path(outside) / "escape.json")
            )
        self.assertIn("must stay inside the current worktree", message)

    def test_an_existing_regular_file_is_refused(self):
        with worktree() as root:
            (root / "report.json").write_text("{}\n", encoding="utf-8")
            message = refusal("--elenchus-report", "report.json")
        self.assertIn("target must not already exist", message)

    def test_an_existing_symlink_is_refused(self):
        with worktree() as root:
            os.symlink("elsewhere.json", root / "report.json")
            message = refusal("--elenchus-report", "report.json")
        self.assertIn("target must not already exist", message)

    def test_a_parent_component_that_is_a_regular_file_is_refused(self):
        with worktree() as root:
            (root / "elenchus").write_text("not a directory\n", encoding="utf-8")
            message = refusal("--elenchus-report", "elenchus/report.json")
        self.assertIn("parent is not a directory", message)

    def test_two_report_paths_in_one_invocation_are_refused(self):
        with worktree():
            message = refusal(
                "--elenchus-report", "first.json", "--elenchus-report", "second.json"
            )
        self.assertIn("name one report path", message)

    def test_v3_without_a_report_path_is_refused(self):
        with worktree():
            message = refusal("--elenchus-report-format", "unittest-json-v3")
        self.assertIn("requires a report path", message)


class ReportPayloadTests(unittest.TestCase):
    def test_the_written_report_carries_every_schema_key(self):
        self.assertEqual(set(written_payload(".elenchus/report.json")), SCHEMA_KEYS)

    def test_the_written_report_declares_the_elenchus_schema(self):
        self.assertEqual(written_payload(".elenchus/report.json")["schema"], SCHEMA)

    def test_v3_report_names_the_failed_method_and_preserves_subtest_counts(self):
        class Cases(unittest.TestCase):
            def test_guard(self):
                for value in (1, 2):
                    with self.subTest(value=value):
                        self.fail("private assertion detail")

            def test_unrelated_pass(self):
                pass

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Cases)
        with worktree(), mock.patch.object(
            run_tests.unittest.defaultTestLoader, "discover", return_value=suite
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = run_tests.main([
                "--elenchus-report-format", "unittest-json-v3",
                "--elenchus-report", ".elenchus/report.json",
            ])
            raw = Path(".elenchus/report.json").read_text(encoding="utf-8")
        payload = json.loads(raw)
        self.assertEqual(status, 1)
        self.assertEqual(payload["schema"], "elenchus.unittest.v3")
        self.assertEqual((payload["testsRun"], payload["failures"]), (2, 2))
        self.assertEqual(
            [(row["test"], row["outcome"], row["failures"]) for row in payload["cases"]],
            [(Cases("test_guard").id(), "failed", 2),
             (Cases("test_unrelated_pass").id(), "passed", 0)],
        )
        self.assertNotIn("private assertion detail", raw)

    def test_v3_positional_report_retains_error_identity(self):
        class Broken(unittest.TestCase):
            def test_fixture(self):
                raise RuntimeError("private exception detail")

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Broken)
        with worktree(), mock.patch.object(
            run_tests.unittest.defaultTestLoader, "discover", return_value=suite
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = run_tests.main([
                "--elenchus-report-format", "unittest-json-v3", "report.json",
            ])
            raw = Path("report.json").read_text(encoding="utf-8")
        payload = json.loads(raw)
        self.assertEqual(status, 1)
        self.assertEqual(payload["cases"][0]["test"], Broken("test_fixture").id())
        self.assertEqual(payload["cases"][0]["outcome"], "error")
        self.assertNotIn("private exception detail", raw)

    def test_v3_unexpected_success_retains_identity_and_exits_nonzero(self):
        class Unexpected(unittest.TestCase):
            @unittest.expectedFailure
            def test_unexpected(self):
                pass

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(Unexpected)
        with worktree(), mock.patch.object(
            run_tests.unittest.defaultTestLoader, "discover", return_value=suite
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            status = run_tests.main([
                "--elenchus-report-format", "unittest-json-v3", "report.json",
            ])
            payload = json.loads(Path("report.json").read_text(encoding="utf-8"))
        self.assertEqual(status, 1)
        self.assertEqual(payload["cases"][0]["test"], Unexpected("test_unexpected").id())
        self.assertEqual(payload["cases"][0]["outcome"], "unexpected-success")


if __name__ == "__main__":
    unittest.main()
