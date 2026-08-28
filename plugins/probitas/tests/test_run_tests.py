"""The Probitas audit report is complete, fresh and worktree-confined."""

import contextlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
import stat
import tempfile
import unittest
from unittest import mock

from . import run_tests as runner


def sample_result(
    tests=1, failures=0, errors=0, skips=0, expected=0, unexpected=0
):
    return SimpleNamespace(
        testsRun=tests,
        failures=[None] * failures,
        errors=[None] * errors,
        skipped=[None] * skips,
        expectedFailures=[None] * expected,
        unexpectedSuccesses=[None] * unexpected,
    )


class RunnerTests(unittest.TestCase):
    def parse_in(self, root, report):
        with mock.patch.object(runner, "worktree_root", return_value=root):
            return runner.report_target(["--elenchus-report", str(report)])

    def test_absent_duplicate_empty_and_unknown_report_arguments_are_refused(self):
        cases = (
            [],
            ["--elenchus-report"],
            ["--elenchus-report", "a", "--elenchus-report", "b"],
            ["--elenchus-report", ""],
            ["--elenchus-report", "a", "--unknown"],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(
                io.StringIO()
            ), self.assertRaises(SystemExit) as raised:
                runner.report_target(arguments)
            self.assertEqual(raised.exception.code, 2)

    def test_existing_outside_parent_escape_and_symlink_targets_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            outside = root.parent / f"{root.name}-outside.json"
            existing = root / "existing.json"
            existing.write_text("keep\n", encoding="utf-8")
            protected = root / "protected.json"
            protected.write_text("keep\n", encoding="utf-8")
            linked_target = root / "linked.json"
            linked_target.symlink_to(protected)
            linked_parent = root / "linked-parent"
            linked_parent.symlink_to(root.parent, target_is_directory=True)
            cases = (
                str(outside),
                "../outside.json",
                str(existing),
                str(linked_target),
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
            self.assertEqual(protected.read_text(encoding="utf-8"), "keep\n")

    def test_target_created_after_validation_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            target = self.parse_in(root, report)
            report.write_text("keep\n", encoding="utf-8")
            with self.assertRaises(OSError):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertEqual(report.read_text(encoding="utf-8"), "keep\n")

    def test_replaced_worktree_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            parent = Path(directory).resolve()
            root = parent / "worktree"
            root.mkdir()
            report = root / "report.json"
            target = self.parse_in(root, report)
            original = parent / "original-worktree"
            root.rename(original)
            root.mkdir()
            with self.assertRaises(OSError):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertFalse(report.exists())

    def test_secure_parent_creation_and_complete_counters(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "tmp" / "elenchus" / "result.json"
            target = self.parse_in(root, report)
            payload = runner.result_payload(
                sample_result(
                    8,
                    failures=1,
                    errors=1,
                    skips=1,
                    expected=1,
                    unexpected=1,
                )
            )
            runner.write_report(target, payload)
            self.assertEqual(
                json.loads(report.read_text(encoding="utf-8")), payload
            )
            self.assertEqual(report.stat().st_mode & 0o777, 0o600)
            for parent in (root / "tmp", root / "tmp" / "elenchus"):
                self.assertTrue(parent.is_dir())
                self.assertFalse(parent.is_symlink())
                self.assertEqual(parent.stat().st_mode & 0o077, 0)

    def test_interrupted_write_removes_only_its_incomplete_target(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            target = self.parse_in(root, report)
            original_write = runner.os.write
            calls = 0

            def interrupted(descriptor, body):
                nonlocal calls
                calls += 1
                if calls == 1:
                    midpoint = max(1, len(body) // 2)
                    return original_write(descriptor, body[:midpoint])
                raise OSError("interrupted")

            with mock.patch.object(
                runner.os, "write", side_effect=interrupted
            ), self.assertRaises(OSError):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertFalse(report.exists())

    def test_write_failure_never_removes_a_replacement_target(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            target = self.parse_in(root, report)

            def replace_then_fail(_descriptor, _body):
                if report.exists():
                    report.unlink()
                report.write_text("replacement\n", encoding="utf-8")
                raise OSError("interrupted after replacement")

            with mock.patch.object(
                runner.os, "write", side_effect=replace_then_fail
            ), self.assertRaises(OSError):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertEqual(
                report.read_text(encoding="utf-8"), "replacement\n"
            )

    def test_cleanup_never_unlinks_a_replacement_after_identity_check(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            target = self.parse_in(root, report)
            original_stat = runner.os.stat
            created = None

            def replace_then_fail(descriptor, _body):
                nonlocal created
                created = runner.os.fstat(descriptor)
                if report.exists():
                    report.unlink()
                report.write_text("replacement\n", encoding="utf-8")
                raise OSError("interrupted while another writer replaces target")

            def stale_identity(name, *, dir_fd=None, follow_symlinks=True):
                if (
                    name == report.name
                    and dir_fd is not None
                    and follow_symlinks is False
                ):
                    return created
                return original_stat(
                    name,
                    dir_fd=dir_fd,
                    follow_symlinks=follow_symlinks,
                )

            with mock.patch.object(
                runner.os, "write", side_effect=replace_then_fail
            ), mock.patch.object(
                runner.os, "stat", side_effect=stale_identity
            ), self.assertRaises(OSError):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertTrue(report.exists())
            self.assertEqual(
                report.read_text(encoding="utf-8"), "replacement\n"
            )

    def test_post_open_inspection_failure_closes_and_removes_the_stage(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            target = self.parse_in(root, report)
            original_fstat = runner.os.fstat
            opened_file = None

            def fail_file_inspection(descriptor):
                nonlocal opened_file
                inspected = original_fstat(descriptor)
                if stat.S_ISREG(inspected.st_mode):
                    opened_file = descriptor
                    raise OSError("inspection failed")
                return inspected

            with mock.patch.object(
                runner.os, "fstat", side_effect=fail_file_inspection
            ), self.assertRaises(OSError):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertEqual(list(root.iterdir()), [])
            with self.assertRaises(OSError):
                runner.os.write(opened_file, b"still open")

    def test_base_exception_during_write_closes_and_removes_the_stage(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            target = self.parse_in(root, report)
            opened_file = None

            def interrupt(descriptor, _body):
                nonlocal opened_file
                opened_file = descriptor
                raise KeyboardInterrupt

            with mock.patch.object(
                runner.os, "write", side_effect=interrupt
            ), self.assertRaises(KeyboardInterrupt):
                runner.write_report(
                    target, runner.result_payload(sample_result())
                )
            self.assertEqual(list(root.iterdir()), [])
            with self.assertRaises(OSError):
                runner.os.write(opened_file, b"still open")

    def test_passing_failure_error_and_zero_suites_write_exact_results(self):
        def assertion_failure():
            raise AssertionError("red")

        def infrastructure_error():
            raise RuntimeError("broken fixture")

        cases = (
            (
                unittest.TestSuite([unittest.FunctionTestCase(lambda: None)]),
                0,
                1,
                0,
                0,
            ),
            (
                unittest.TestSuite(
                    [unittest.FunctionTestCase(assertion_failure)]
                ),
                1,
                1,
                1,
                0,
            ),
            (
                unittest.TestSuite(
                    [unittest.FunctionTestCase(infrastructure_error)]
                ),
                1,
                1,
                0,
                1,
            ),
            (unittest.TestSuite(), 2, 0, 0, 0),
        )
        for suite, expected_exit, tests_run, failures, errors in cases:
            with self.subTest(
                expected_exit=expected_exit
            ), tempfile.TemporaryDirectory(
                prefix="probitas-runner-"
            ) as directory:
                root = Path(directory).resolve()
                report = root / "report.json"
                with mock.patch.object(
                    runner, "worktree_root", return_value=root
                ), mock.patch.object(
                    runner.unittest.defaultTestLoader,
                    "discover",
                    return_value=suite,
                ), contextlib.redirect_stdout(
                    io.StringIO()
                ), contextlib.redirect_stderr(io.StringIO()):
                    exit_code = runner.main(
                        ["--elenchus-report", str(report)]
                    )
                payload = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(exit_code, expected_exit)
                self.assertTrue(payload["complete"])
                self.assertEqual(payload["testsRun"], tests_run)
                self.assertEqual(payload["failures"], failures)
                self.assertEqual(payload["errors"], errors)

    def test_abnormal_discovery_and_run_write_an_incomplete_marker(self):
        for stage in ("discovery", "run"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(
                prefix="probitas-runner-"
            ) as directory:
                root = Path(directory).resolve()
                report = root / "report.json"
                discovery_result = (
                    KeyboardInterrupt
                    if stage == "discovery"
                    else unittest.TestSuite()
                )
                run_result = KeyboardInterrupt if stage == "run" else None
                with mock.patch.object(
                    runner, "worktree_root", return_value=root
                ), mock.patch.object(
                    runner.unittest.defaultTestLoader,
                    "discover",
                    side_effect=discovery_result
                    if stage == "discovery"
                    else None,
                    return_value=discovery_result
                    if stage == "run"
                    else None,
                ), mock.patch.object(
                    runner.unittest.TextTestRunner,
                    "run",
                    side_effect=run_result,
                ), contextlib.redirect_stdout(
                    io.StringIO()
                ), contextlib.redirect_stderr(
                    io.StringIO()
                ), self.assertRaises(KeyboardInterrupt):
                    runner.main(["--elenchus-report", str(report)])
                payload = json.loads(report.read_text(encoding="utf-8"))
                self.assertFalse(payload["complete"])
                self.assertEqual(payload["testsRun"], 0)

    def test_report_write_failure_is_distinct_and_leaves_no_file(self):
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            suite = unittest.TestSuite(
                [unittest.FunctionTestCase(lambda: None)]
            )
            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), mock.patch.object(
                runner.unittest.defaultTestLoader,
                "discover",
                return_value=suite,
            ), mock.patch.object(
                runner, "write_report", side_effect=OSError("blocked")
            ), contextlib.redirect_stdout(
                io.StringIO()
            ), contextlib.redirect_stderr(io.StringIO()):
                exit_code = runner.main(
                    ["--elenchus-report", str(report)]
                )
            self.assertEqual(exit_code, 2)
            self.assertFalse(report.exists())

    def test_runner_discovers_all_tests_from_the_plugin_root(self):
        suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        with tempfile.TemporaryDirectory(prefix="probitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "report.json"
            with mock.patch.object(
                runner, "worktree_root", return_value=root
            ), mock.patch.object(
                runner.unittest.defaultTestLoader,
                "discover",
                return_value=suite,
            ) as discover, contextlib.redirect_stdout(
                io.StringIO()
            ), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    runner.main(["--elenchus-report", str(report)]), 0
                )
            here = str(Path(runner.__file__).resolve().parent)
            discover.assert_called_once_with(
                here,
                pattern="test_*.py",
                top_level_dir=str(Path(here).parent),
            )


if __name__ == "__main__":
    unittest.main()
