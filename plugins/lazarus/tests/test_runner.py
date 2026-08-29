"""The source-owned unittest report stays fresh and inside its worktree."""

import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from . import run_receipt_delivery_tests as delivery_runner
from . import run_tests as runner


class RunnerTests(unittest.TestCase):
    def test_receipt_delivery_runner_discovers_both_plugin_suites(self):
        class RecordingLoader:
            def __init__(self):
                self.calls = []

            def discover(self, start, *, pattern, top_level_dir):
                self.calls.append((start, pattern, top_level_dir))
                return unittest.TestSuite(
                    [unittest.FunctionTestCase(lambda: None)]
                )

        loader = RecordingLoader()
        root = Path("/tmp/receipt-delivery-worktree")
        with mock.patch.object(delivery_runner, "worktree_root", return_value=root):
            suite = delivery_runner.combined_suite(loader)
        self.assertEqual(suite.countTestCases(), 2)
        self.assertEqual(
            loader.calls,
            [
                (
                    str(root / "plugins" / "lazarus" / "tests"),
                    "test_*.py",
                    str(root),
                ),
                (
                    str(root / "plugins" / "ariadne" / "tests"),
                    "test_*.py",
                    str(root),
                ),
            ],
        )

    def test_receipt_delivery_runner_writes_one_complete_fresh_report(self):
        suite = unittest.TestSuite(
            [
                unittest.FunctionTestCase(lambda: None),
                unittest.FunctionTestCase(lambda: None),
            ]
        )
        with tempfile.TemporaryDirectory(prefix="receipt-delivery-") as directory:
            root = Path(directory).resolve()
            report = root / "tmp" / "elenchus" / "combined.json"
            with mock.patch.object(
                delivery_runner, "combined_suite", return_value=suite
            ), mock.patch.object(
                runner, "worktree_root", return_value=root
            ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                self.assertEqual(
                    delivery_runner.main(["--elenchus-report", str(report)]), 0
                )
            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8")),
                {
                    "schema": "elenchus.unittest.v1",
                    "complete": True,
                    "testsRun": 2,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expectedFailures": 0,
                    "unexpectedSuccesses": 0,
                },
            )
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as raised:
                delivery_runner.main(["--elenchus-report", str(report)])
            self.assertEqual(raised.exception.code, 2)

    def test_receipt_delivery_runner_preserves_joint_failure(self):
        def fail():
            raise AssertionError("joint failure")

        suite = unittest.TestSuite([unittest.FunctionTestCase(fail)])
        with mock.patch.object(
            delivery_runner, "combined_suite", return_value=suite
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            self.assertEqual(delivery_runner.main([]), 1)

    def test_bad_report_arguments_are_refused_before_a_suite_runs(self):
        cases = (
            ["--elenchus-report"],
            ["--elenchus-report", "a", "--elenchus-report", "b"],
            ["--elenchus-report", "a", "--unknown"],
            ["--elenchus-report", ""],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(
                io.StringIO()
            ), self.assertRaises(SystemExit) as raised:
                runner.report_target(arguments)
            self.assertEqual(raised.exception.code, 2)

    def test_01_hostile_report_paths_are_refused_before_a_suite_runs(self):
        with tempfile.TemporaryDirectory(prefix="lazarus-runner-") as directory:
            root = Path(directory).resolve()
            outside = root.parent / f"{root.name}-outside.json"
            existing = root / "existing.json"
            existing.write_text("keep\n", encoding="utf-8")
            target = root / "target"
            target.write_text("keep\n", encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(root.parent, target_is_directory=True)
            internal = root / "internal"
            internal.mkdir()
            internal_link = root / "internal-link"
            internal_link.symlink_to(internal, target_is_directory=True)
            cases = (
                str(outside),
                "../outside.json",
                str(existing),
                str(link),
                str(linked_parent / "report.json"),
                str(internal_link / "report.json"),
            )
            for value in cases:
                with self.subTest(value=value), mock.patch.object(
                    runner, "worktree_root", return_value=root
                ), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                    SystemExit
                ) as raised:
                    runner.report_target(["--elenchus-report", value])
                self.assertEqual(raised.exception.code, 2)
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(target.read_text(encoding="utf-8"), "keep\n")

    def test_02_safe_report_is_exclusive_complete_and_mode_0600(self):
        with tempfile.TemporaryDirectory(prefix="lazarus-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "tmp" / "elenchus" / "result.json"
            result = SimpleNamespace(
                testsRun=8,
                failures=[1],
                errors=[1],
                skipped=[1],
                expectedFailures=[1],
                unexpectedSuccesses=[1],
            )
            with mock.patch.object(runner, "worktree_root", return_value=root):
                target = runner.report_target(["--elenchus-report", str(report)])
            payload = runner.result_payload(result)
            runner.write_report(target, payload)

            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8")),
                {
                    "schema": "elenchus.unittest.v1",
                    "complete": True,
                    "testsRun": 8,
                    "failures": 1,
                    "errors": 1,
                    "skipped": 1,
                    "expectedFailures": 1,
                    "unexpectedSuccesses": 1,
                },
            )
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as raised:
                runner.report_target(["--elenchus-report", str(report)])
            self.assertEqual(raised.exception.code, 2)

    def test_report_write_failure_is_distinct_and_leaves_no_file(self):
        with tempfile.TemporaryDirectory(prefix="lazarus-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), mock.patch.object(
                runner.unittest.defaultTestLoader, "discover", return_value=suite
            ), mock.patch.object(
                runner, "write_report", side_effect=OSError("blocked")
            ), contextlib.redirect_stderr(io.StringIO()):
                exit_code = runner.main(["--elenchus-report", str(report)])
            self.assertEqual(exit_code, 2)
            self.assertFalse(report.exists())

    def test_relative_report_ignores_a_caller_cwd_outside_the_worktree(self):
        with tempfile.TemporaryDirectory(prefix="lazarus-runner-") as directory:
            root = Path(directory).resolve()
            with tempfile.TemporaryDirectory(
                prefix="lazarus-runner-cwd-"
            ) as caller_directory, mock.patch.object(
                runner, "worktree_root", return_value=root
            ), mock.patch.object(
                runner.Path, "cwd", return_value=Path(caller_directory)
            ):
                target = runner.report_target(
                    ["--elenchus-report", "tmp/elenchus/result.json"]
                )
                runner.write_report(
                    target,
                    runner.result_payload(
                        SimpleNamespace(
                            testsRun=1,
                            failures=[],
                            errors=[],
                            skipped=[],
                            expectedFailures=[],
                            unexpectedSuccesses=[],
                        )
                    ),
                )
                self.assertTrue(
                    (root / "tmp" / "elenchus" / "result.json").is_file()
                )
                self.assertFalse(
                    (
                        Path(caller_directory)
                        / "tmp"
                        / "elenchus"
                        / "result.json"
                    ).exists()
                )

    def test_runner_discovers_tests_from_the_plugin_root(self):
        suite = unittest.TestSuite()
        with mock.patch.object(
            runner.unittest.defaultTestLoader, "discover", return_value=suite
        ) as discover, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            self.assertEqual(runner.main([]), 0)
        here = str(Path(runner.__file__).resolve().parent)
        discover.assert_called_once_with(
            here, pattern="test_*.py", top_level_dir=str(Path(here).parent)
        )

    def test_unexpected_success_keeps_the_suite_exit_nonzero(self):
        class UnexpectedSuccess(unittest.TestCase):
            @unittest.expectedFailure
            def test_unexpected_success(self):
                pass

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(UnexpectedSuccess)
        with mock.patch.object(
            runner.unittest.defaultTestLoader, "discover", return_value=suite
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            self.assertEqual(runner.main([]), 1)


if __name__ == "__main__":
    unittest.main()
