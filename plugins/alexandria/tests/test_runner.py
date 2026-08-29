"""The Alexandria unittest report stays fresh and inside its worktree."""

import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from . import run_tests as runner


class RunnerTests(unittest.TestCase):
    def test_absent_duplicate_empty_and_unknown_report_arguments_are_refused(self):
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

    def test_outside_existing_and_symlinked_report_targets_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
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
            cases = (
                str(outside),
                "../outside.json",
                str(existing),
                str(link),
                str(linked_parent / "report.json"),
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

    def test_absolute_report_below_worktree_path_alias_is_bound_to_the_root(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
            parent = Path(directory).resolve()
            root = parent / "worktree"
            root.mkdir()
            alias = parent / "worktree-alias"
            alias.symlink_to(root, target_is_directory=True)
            report = alias / "reports" / "result.json"

            with mock.patch.object(runner, "worktree_root", return_value=root):
                target = runner.report_target(["--elenchus-report", str(report)])

            self.assertEqual(target[0], root)
            self.assertEqual(target[2], ("reports", "result.json"))

    def test_symlink_below_the_worktree_root_remains_refused(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
            root = Path(directory).resolve()
            self_link = root / "self-link"
            self_link.symlink_to(root, target_is_directory=True)
            report = self_link / "report.json"

            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                SystemExit
            ) as raised:
                runner.report_target(["--elenchus-report", str(report)])

            self.assertEqual(raised.exception.code, 2)

    def test_safe_report_is_exclusive_complete_and_mode_0600(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
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
            runner.write_report(target, runner.result_payload(result))

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

    def test_target_created_after_validation_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            with mock.patch.object(runner, "worktree_root", return_value=root):
                target = runner.report_target(["--elenchus-report", str(report)])
            report.write_text("keep\n", encoding="utf-8")
            with self.assertRaises(OSError):
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
            self.assertEqual(report.read_text(encoding="utf-8"), "keep\n")

    def test_parent_replaced_by_a_symlink_after_validation_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
            root = Path(directory).resolve()
            outside = root.parent / f"{root.name}-outside"
            outside.mkdir()
            self.addCleanup(outside.rmdir)
            report = root / "reports" / "result.json"
            with mock.patch.object(runner, "worktree_root", return_value=root):
                target = runner.report_target(["--elenchus-report", str(report)])
            report.parent.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
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
            self.assertFalse((outside / "result.json").exists())

    def test_successful_and_failing_results_keep_exact_counters(self):
        passing = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])

        def fail():
            raise AssertionError("red")

        failing = unittest.TestSuite([unittest.FunctionTestCase(fail)])
        for suite, expected_exit, expected_failures in (
            (passing, 0, 0),
            (failing, 1, 1),
        ):
            with self.subTest(expected_exit=expected_exit), tempfile.TemporaryDirectory(
                prefix="alexandria-runner-"
            ) as directory:
                root = Path(directory).resolve()
                report = root / "report.json"
                with mock.patch.object(
                    runner, "worktree_root", return_value=root
                ), mock.patch.object(
                    runner.unittest.defaultTestLoader,
                    "discover",
                    return_value=suite,
                ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                    io.StringIO()
                ):
                    exit_code = runner.main(
                        ["--elenchus-report", str(report)]
                    )
                payload = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(exit_code, expected_exit)
                self.assertEqual(payload["testsRun"], 1)
                self.assertEqual(payload["failures"], expected_failures)
                self.assertEqual(payload["errors"], 0)

    def test_report_write_failure_is_distinct_and_leaves_no_file(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), mock.patch.object(
                runner.unittest.defaultTestLoader, "discover", return_value=suite
            ), mock.patch.object(
                runner, "write_report", side_effect=OSError("blocked")
            ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                exit_code = runner.main(["--elenchus-report", str(report)])
            self.assertEqual(exit_code, 2)
            self.assertFalse(report.exists())

    def test_report_inspection_failure_closes_and_removes_created_file(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            root_fd = runner.os.open(
                root,
                runner.os.O_RDONLY
                | runner.os.O_DIRECTORY
                | runner.os.O_NOFOLLOW,
            )
            descriptors = []
            original_open = runner.os.open

            def tracking_open(path, flags, mode=0o777, *, dir_fd=None):
                descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                descriptors.append(descriptor)
                return descriptor

            with mock.patch.object(
                runner, "report_root", return_value=root_fd
            ), mock.patch.object(
                runner.os, "open", side_effect=tracking_open
            ), mock.patch.object(
                runner.os, "fstat", side_effect=OSError("inspection failed")
            ), self.assertRaises(OSError):
                runner.write_report(
                    (root, (root.stat().st_dev, root.stat().st_ino), (report.name,)),
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

            self.assertEqual(len(descriptors), 1)
            self.assertFalse(report.exists())
            with self.assertRaises(OSError):
                runner.os.fstat(descriptors[0])

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


if __name__ == "__main__":
    unittest.main()
