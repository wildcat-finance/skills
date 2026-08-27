"""The Brevitas audit runner publishes only complete, confined reports."""

from __future__ import annotations

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
    def run_suite(self, suite: unittest.TestSuite, report: Path) -> int:
        with mock.patch.object(
            runner, "worktree_root", return_value=report.parents[1]
        ), mock.patch.object(
            runner.unittest.defaultTestLoader, "discover", return_value=suite
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            return runner.main([str(report)])

    def test_complete_report_is_atomic_bounded_and_private(self) -> None:
        suite = unittest.TestSuite(
            [
                unittest.FunctionTestCase(lambda: None),
                unittest.FunctionTestCase(lambda: None),
            ]
        )
        with tempfile.TemporaryDirectory(prefix="brevitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "reports" / "result.json"
            self.assertEqual(self.run_suite(suite, report), 0)
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
            self.assertLessEqual(report.stat().st_size, runner.MAX_REPORT_BYTES)
            self.assertEqual(list(report.parent.iterdir()), [report])

    def test_assertion_failure_is_reported_as_a_failure(self) -> None:
        def fail() -> None:
            raise AssertionError("red")

        suite = unittest.TestSuite([unittest.FunctionTestCase(fail)])
        with tempfile.TemporaryDirectory(prefix="brevitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "reports" / "failure.json"
            self.assertEqual(self.run_suite(suite, report), 1)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["testsRun"], 1)
            self.assertEqual(payload["failures"], 1)
            self.assertEqual(payload["errors"], 0)

    def test_infrastructure_error_is_reported_as_an_error(self) -> None:
        def break_before_assertion() -> None:
            raise RuntimeError("infrastructure failed")

        suite = unittest.TestSuite([unittest.FunctionTestCase(break_before_assertion)])
        with tempfile.TemporaryDirectory(prefix="brevitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "reports" / "error.json"
            self.assertEqual(self.run_suite(suite, report), 1)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["testsRun"], 1)
            self.assertEqual(payload["failures"], 0)
            self.assertEqual(payload["errors"], 1)

    def test_zero_tests_remain_visible_in_a_complete_report(self) -> None:
        suite = unittest.TestSuite()
        with tempfile.TemporaryDirectory(prefix="brevitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "reports" / "zero.json"
            self.assertEqual(self.run_suite(suite, report), 0)
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(payload["complete"])
            self.assertEqual(payload["testsRun"], 0)

    def test_unsafe_output_paths_are_refused_before_the_suite_runs(self) -> None:
        with tempfile.TemporaryDirectory(prefix="brevitas-runner-") as directory:
            parent = Path(directory).resolve()
            root = parent / "worktree"
            root.mkdir()
            outside = parent / "outside"
            outside.mkdir()
            existing = root / "existing.json"
            existing.write_text("keep\n", encoding="utf-8")
            link = root / "linked-parent"
            link.symlink_to(outside, target_is_directory=True)
            cases = (
                str(outside / "report.json"),
                "../outside/report.json",
                str(existing),
                str(link / "report.json"),
            )
            for value in cases:
                with self.subTest(value=value), mock.patch.object(
                    runner, "worktree_root", return_value=root
                ), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
                    SystemExit
                ) as raised:
                    runner.report_target([value])
                self.assertEqual(raised.exception.code, 2)
            self.assertEqual(existing.read_text(encoding="utf-8"), "keep\n")
            self.assertEqual(list(outside.iterdir()), [])

    def test_interrupted_partial_write_leaves_no_report_or_temporary(self) -> None:
        result = SimpleNamespace(
            testsRun=1,
            failures=[],
            errors=[],
            skipped=[],
            expectedFailures=[],
            unexpectedSuccesses=[],
        )
        with tempfile.TemporaryDirectory(prefix="brevitas-runner-") as directory:
            root = Path(directory).resolve()
            report = root / "reports" / "partial.json"
            with mock.patch.object(runner, "worktree_root", return_value=root):
                target = runner.report_target([str(report)])

            real_write = runner.os.write
            calls = 0

            def interrupted_write(descriptor: int, body: bytes) -> int:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return real_write(descriptor, bytes(body[:5]))
                raise OSError("interrupted")

            with mock.patch.object(
                runner.os, "write", side_effect=interrupted_write
            ), self.assertRaises(OSError):
                runner.write_report(target, runner.result_payload(result))

            self.assertFalse(report.exists())
            self.assertEqual(list(report.parent.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
