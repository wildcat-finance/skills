"""The report wrapper runs a resolver once and never shares a path with it."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import mock
import hashlib
import importlib.util
import json
import os
import shlex
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "protasis" / "scripts"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wrapper = _load("protasis_design_report", "design_report.py")
design = _load("protasis_design_evidence_for_report", "design_evidence.py")

CANDIDATE = "streaming"
CRITERION = "restart-safe"
REPORT_NAME = f"{CANDIDATE}-{CRITERION}.json"
CHILD = [sys.executable, "-c"]


class DesignReportCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(os.path.realpath(self.temporary.name))
        self.reports = self.root / "reports"
        self.reports.mkdir()
        self.pending_dir = self.root / "design" / "reports"
        self.pending_dir.mkdir(parents=True)
        self.record_path = self.root / "design-evidence.json"
        self.out = self.pending_dir / REPORT_NAME
        self.write_record()

    def tearDown(self):
        self.temporary.cleanup()

    # -- fixture ---------------------------------------------------------

    def resolved_report(self, candidate, criterion, value, unit):
        path = self.reports / f"{candidate}-{criterion}.json"
        payload = {
            "schema": design.REPORT_SCHEMA,
            "candidate": candidate,
            "criterion": criterion,
            "value": value,
            "unit": unit,
            "command": f"measure {candidate} {criterion}",
            "exit": 0,
        }
        data = (json.dumps(payload, sort_keys=True) + "\n").encode()
        path.write_bytes(data)
        return {"path": f"reports/{path.name}", "sha256": hashlib.sha256(data).hexdigest()}

    def write_record(self):
        def criterion(cid, concern, kind, unit, comparator, threshold, stage, blocks):
            return {
                "id": cid, "concern": concern, "kind": kind, "stage": stage,
                "owner": "protasis", "unit": unit, "comparator": comparator,
                "threshold": threshold, "blocks": blocks,
            }

        criteria = [
            criterion("prototype-works", "correctness", "gate", "boolean", "equals", True,
                      "selection", "design-lock"),
            criterion("warm-time", "time", "metric", "milliseconds", "minimise", None,
                      "selection", "design-lock"),
            criterion("peak-rss", "space", "metric", "bytes", "minimise", None,
                      "selection", "design-lock"),
            criterion("plugin-compatible", "compatibility", "gate", "boolean", "equals",
                      True, "selection", "design-lock"),
            criterion(CRITERION, "recovery", "gate", "boolean", "equals", True,
                      "conformance", "step:2"),
        ]
        observed = {
            CANDIDATE: {
                "prototype-works": (True, "boolean"),
                "warm-time": (100, "milliseconds"),
                "peak-rss": (100, "bytes"),
                "plugin-compatible": (True, "boolean"),
            },
            "buffered": {
                "prototype-works": (True, "boolean"),
                "warm-time": (200, "milliseconds"),
                "peak-rss": (200, "bytes"),
                "plugin-compatible": (True, "boolean"),
                CRITERION: (True, "boolean"),
            },
        }
        results = [
            {
                "candidate": candidate,
                "criterion": cid,
                "state": "pass",
                "report": self.resolved_report(candidate, cid, value, unit),
            }
            for candidate, cells in observed.items()
            for cid, (value, unit) in cells.items()
        ]
        results.append({
            "candidate": CANDIDATE,
            "criterion": CRITERION,
            "state": "pending",
            "resolver": "python3 design_report.py ... -- python3 -m unittest guard",
            "report": f"design/reports/{REPORT_NAME}",
            "blocks": "step:2",
        })
        record = {
            "schema": design.SCHEMA,
            "candidates": [
                {"id": CANDIDATE, "summary": "Process one bounded window."},
                {"id": "buffered", "summary": "Hold the whole interval in memory."},
            ],
            "criteria": criteria,
            "results": results,
            "selection": {"candidate": CANDIDATE, "rule": "unique-frontier", "policy_ref": None},
        }
        self.record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")

    # -- helpers ---------------------------------------------------------

    def run_wrapper(self, child, *, out=None, unit="boolean", source=("--value-from-exit",),
                    extra=()):
        argv = [
            "--candidate", CANDIDATE, "--criterion", CRITERION, "--unit", unit,
            "--out", str(out if out is not None else self.out), *source, *extra, "--", *child,
        ]
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = wrapper.main(argv)
        summary = json.loads(stdout.getvalue()) if code == 0 else None
        return code, summary, stderr.getvalue()

    def marker_child(self, marker, exit_code=0):
        """A child that proves it ran by creating `marker`."""
        return [*CHILD, f"import pathlib, sys; pathlib.Path({str(marker)!r}).touch(); "
                        f"sys.exit({exit_code})"]

    def read_report(self, path=None):
        data = (path or self.out).read_bytes()
        return json.loads(data), data

    def checker(self, transition="step:2"):
        findings, _, consumed = design.evaluate(self.record_path, transition)
        return [finding.code for finding in findings], consumed

    # -- cases -----------------------------------------------------------

    def test_passing_child_writes_a_closed_report_with_exit_zero_and_the_quoted_command(self):
        child = [*CHILD, "import sys; print('two words'); sys.exit(0)"]
        code, summary, _ = self.run_wrapper(child)
        self.assertEqual(code, 0)
        report, data = self.read_report()
        self.assertEqual(set(report), design.REPORT_KEYS)
        self.assertEqual(report, {
            "schema": design.REPORT_SCHEMA,
            "candidate": CANDIDATE,
            "criterion": CRITERION,
            "value": True,
            "unit": "boolean",
            "command": " ".join(shlex.quote(element) for element in child),
            "exit": 0,
        })
        self.assertEqual(data, (json.dumps(report, sort_keys=True) + "\n").encode())
        self.assertEqual(summary["exit"], 0)
        self.assertEqual(summary["report"], f"design/reports/{REPORT_NAME}")

    def test_the_written_report_is_admitted_by_the_checker_for_a_boolean_gate_cell(self):
        self.assertEqual(self.checker(), (["D008"], []))
        code, _, _ = self.run_wrapper([*CHILD, "raise SystemExit(0)"])
        self.assertEqual(code, 0)
        codes, consumed = self.checker()
        self.assertEqual(codes, [])
        self.assertEqual(consumed, [{
            "candidate": CANDIDATE,
            "criterion": CRITERION,
            "path": f"design/reports/{REPORT_NAME}",
            "sha256": hashlib.sha256(self.out.read_bytes()).hexdigest(),
        }])

    def test_failing_child_records_its_exit_and_the_checker_reads_a_fail(self):
        code, summary, _ = self.run_wrapper([*CHILD, "raise SystemExit(3)"])
        self.assertEqual(code, 0, "the wrapper records the exit and does not judge it")
        report, _ = self.read_report()
        self.assertEqual((report["exit"], report["value"]), (3, False))
        self.assertEqual(summary["exit"], 3)
        findings, _, consumed = design.evaluate(self.record_path, "step:2")
        self.assertEqual([finding.code for finding in findings], ["D008"])
        self.assertIn(f"{CANDIDATE}/{CRITERION}", findings[0].message)
        self.assertEqual(consumed, [])

    def test_value_from_exit_yields_only_a_boolean(self):
        code, _, stderr = self.run_wrapper([*CHILD, "pass"], unit="count")
        self.assertEqual(code, 2)
        self.assertIn("must be boolean", stderr)
        self.assertFalse(self.out.exists())

    def test_value_is_taken_from_a_named_key_of_a_child_written_json_file(self):
        inner = self.root / "inner.json"
        child = [*CHILD, f"import json, pathlib; pathlib.Path({str(inner)!r}).write_text("
                         f"json.dumps({{'passed': 7, 'failed': 0}}))"]
        code, summary, _ = self.run_wrapper(
            child, unit="count",
            source=("--value-json", str(inner), "--value-key", "passed"),
        )
        self.assertEqual(code, 0)
        report, _ = self.read_report()
        self.assertEqual((report["value"], report["unit"], report["exit"]), (7, "count", 0))
        self.assertEqual(summary["value"], 7)

    def test_a_value_key_missing_or_off_unit_refuses_without_a_report(self):
        inner = self.root / "inner.json"
        for document in ('{"passed": "seven"}', '{"other": 7}', '{"passed": 7, "passed": 8}'):
            if inner.exists():
                inner.unlink()
            child = [*CHILD, f"import pathlib; pathlib.Path({str(inner)!r}).write_text({document!r})"]
            code, _, stderr = self.run_wrapper(
                child, unit="count",
                source=("--value-json", str(inner), "--value-key", "passed"),
            )
            self.assertEqual(code, 2, document)
            self.assertIn("refused", stderr)
            self.assertFalse(self.out.exists(), document)

    def test_an_output_path_equal_to_any_argv_element_refuses_before_the_child_runs(self):
        marker = self.root / "ran"
        for spelling in (str(self.out), os.path.relpath(self.out)):
            child = [*self.marker_child(marker), "--report", spelling]
            code, _, stderr = self.run_wrapper(child)
            self.assertEqual(code, 2, spelling)
            self.assertIn("equals child argv element", stderr)
            self.assertFalse(marker.exists(), "the child must not have run")
            self.assertFalse(self.out.exists())
        inner = self.out
        code, _, stderr = self.run_wrapper(
            self.marker_child(marker), unit="count",
            source=("--value-json", str(inner), "--value-key", "passed"),
        )
        self.assertEqual(code, 2)
        self.assertIn("--value-json must not equal --out", stderr)
        self.assertFalse(marker.exists())

    def test_an_existing_output_refuses_and_keeps_its_bytes(self):
        self.out.write_bytes(b"receipted\n")
        marker = self.root / "ran"
        code, _, stderr = self.run_wrapper(self.marker_child(marker))
        self.assertEqual(code, 2)
        self.assertIn("already exists", stderr)
        self.assertEqual(self.out.read_bytes(), b"receipted\n")
        self.assertFalse(marker.exists())

    def test_a_symlink_output_or_a_symlinked_directory_refuses(self):
        target = self.root / "target.json"
        self.out.symlink_to(target)
        marker = self.root / "ran"
        code, _, stderr = self.run_wrapper(self.marker_child(marker))
        self.assertEqual(code, 2)
        self.assertIn("is a symlink", stderr)
        self.assertFalse(target.exists())
        self.assertFalse(marker.exists())
        self.out.unlink()

        outside = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))
        linked = self.root / "design" / "linked"
        linked.symlink_to(outside, target_is_directory=True)
        code, _, stderr = self.run_wrapper(
            self.marker_child(marker), out=linked / "escape.json", extra=("--record", str(self.record_path)),
        )
        self.assertEqual(code, 2)
        self.assertIn("crosses a symlink", stderr)
        self.assertFalse((outside / "escape.json").exists())
        self.assertFalse(marker.exists())

    def test_an_output_outside_the_record_directory_refuses(self):
        marker = self.root / "ran"
        outside = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(lambda: __import__("shutil").rmtree(outside, ignore_errors=True))

        code, _, stderr = self.run_wrapper(
            self.marker_child(marker), out=outside / "report.json",
            extra=("--record", str(self.record_path)),
        )
        self.assertEqual(code, 2)
        self.assertIn("lies outside the record directory", stderr)

        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        code, _, stderr = self.run_wrapper(self.marker_child(marker), out=elsewhere / "report.json")
        self.assertEqual(code, 2)
        self.assertIn("<record dir>/design/reports/<file>", stderr)

        orphan = outside / "design" / "reports"
        orphan.mkdir(parents=True)
        code, _, stderr = self.run_wrapper(self.marker_child(marker), out=orphan / "report.json")
        self.assertEqual(code, 2)
        self.assertIn("no design-evidence.json", stderr)

        self.assertFalse(marker.exists(), "no refusal may run the child")
        self.assertEqual(sorted(p.name for p in outside.rglob("*") if p.is_file()), [])

    def test_a_child_exceeding_the_timeout_is_recorded_as_a_non_zero_exit(self):
        child = [*CHILD, "import time; print('started', flush=True); time.sleep(30)"]
        with mock.patch.object(wrapper, "TIMEOUT_SECONDS", 1):
            code, summary, stderr = self.run_wrapper(child)
        self.assertEqual(code, 0)
        report, _ = self.read_report()
        self.assertNotEqual(report["exit"], 0)
        self.assertIsInstance(report["exit"], int)
        self.assertFalse(report["value"])
        self.assertTrue(summary["timed_out"])
        self.assertEqual(summary["timeout_seconds"], 1)
        self.assertEqual(summary["output_cap_bytes"], 1 << 20)
        self.assertIn("exceeded the 1 s timeout", stderr)
        self.assertIn("not judged", stderr)
        self.assertEqual(self.checker()[0], ["D008"])

    def test_captured_output_above_one_mebibyte_is_truncated_and_marked(self):
        emitted = (1 << 20) + 4096
        child = [*CHILD, f"import sys; sys.stdout.write('x' * {emitted}); sys.stdout.flush()"]
        code, summary, stderr = self.run_wrapper(child)
        self.assertEqual(code, 0)
        self.assertTrue(summary["truncated"])
        self.assertEqual(summary["captured_bytes"], 1 << 20)
        self.assertEqual(summary["output_bytes"], emitted)
        self.assertIn(f"truncated at the {1 << 20} byte cap", stderr)
        self.assertIn(f"emitted {emitted} bytes", stderr)
        report, _ = self.read_report()
        self.assertEqual((report["exit"], report["value"]), (0, True))
        self.assertLess(self.out.stat().st_size, 64 * 1024)

    def test_the_child_argv_is_run_as_a_list_without_a_shell(self):
        echo = self.root / "argv.json"
        child = [*CHILD, f"import json, pathlib, sys; pathlib.Path({str(echo)!r}).write_text("
                         f"json.dumps(sys.argv[1:]))", "$HOME", "a; touch shell-ran", "two words"]
        code, _, _ = self.run_wrapper(child)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(echo.read_text()), ["$HOME", "a; touch shell-ran", "two words"])
        self.assertFalse((self.root / "shell-ran").exists())
        self.assertFalse(Path("shell-ran").exists())

    def test_a_missing_separator_or_empty_child_argv_refuses(self):
        for argv in (
            ["--candidate", CANDIDATE, "--criterion", CRITERION, "--unit", "boolean",
             "--out", str(self.out), "--value-from-exit"],
            ["--candidate", CANDIDATE, "--criterion", CRITERION, "--unit", "boolean",
             "--out", str(self.out), "--value-from-exit", "--"],
        ):
            stderr = StringIO()
            with redirect_stdout(StringIO()), redirect_stderr(stderr):
                code = wrapper.main(argv)
            self.assertEqual(code, 2)
            self.assertIn("refused", stderr.getvalue())
            self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
