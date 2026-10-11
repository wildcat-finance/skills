"""Exercise timestamp proof controls and unchanged constructed legacy releases."""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
# Establish sibling imports before loading SafePath-sensitive release code.
sys.path.insert(0, str(ROOT / "plugins/alexandria/scripts"))
sys.path.insert(0, str(ROOT / "plugins/tabularium/scripts"))

import prove_wildcat_timestamps as proof
import wildcat_timestamp_reports as reports


@contextmanager
def temporary_cwd():
    old = Path.cwd()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        os.chdir(root)
        try:
            yield root
        finally:
            os.chdir(old)


def observed(kind):
    class Specimen(unittest.TestCase):
        def runTest(self):
            if kind == "fail":
                self.fail("deliberate assertion control")
            if kind == "error":
                raise RuntimeError("deliberate error control")
            if kind == "skip":
                self.skipTest("deliberate skip control")
    result = reports.ObservedResult()
    unittest.TestSuite([Specimen()]).run(result)
    return result


class TimestampScaffoldTests(unittest.TestCase):
    def test_parser_has_exact_cases_and_required_report(self):
        for case in ("scaffold", "capture", "mapping", "demonstration", "integration"):
            parsed = proof.build_parser().parse_args(["--case", case, "--report", ".elenchus/r.json"])
            self.assertEqual(parsed.case, case)
        for argv in ([], ["--case", "unknown", "--report", ".elenchus/r.json"],
                     ["--case", "scaffold"], ["--report", ".elenchus/r.json"]):
            with self.subTest(argv=argv), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                proof.build_parser().parse_args(argv)
            self.assertEqual(exc.exception.code, 2)

    def test_real_pass_fail_error_counters_and_exits(self):
        for kind, failures, errors, status in (("pass", 0, 0, 0), ("fail", 1, 0, 1), ("error", 0, 1, 2)):
            with self.subTest(kind=kind), temporary_cwd() as root:
                result = observed(kind)
                with mock.patch.object(reports, "run_cases", return_value=result), redirect_stderr(io.StringIO()):
                    actual = proof.main(["--case", "scaffold", "--report", ".elenchus/r.json"])
                self.assertEqual(actual, status)
                self.assertEqual(json.loads((root / ".elenchus/r.json").read_bytes()), {
                    "schema": "elenchus.unittest.v1", "complete": True, "testsRun": 1,
                    "failures": failures, "errors": errors, "skipped": 0,
                    "expectedFailures": 0, "unexpectedSuccesses": 0})
                self.assertEqual(len(result.executed_ids), 1)

    def test_skipped_and_empty_suites_never_pass(self):
        self.assertEqual(reports.result_status(observed("skip")), 1)
        self.assertEqual(reports.result_status(reports.ObservedResult()), 2)

    def test_expected_failures_and_unexpected_successes_never_pass(self):
        class Controls(unittest.TestCase):
            @unittest.expectedFailure
            def test_expected_failure(self):
                self.fail("expected failure control")

            @unittest.expectedFailure
            def test_unexpected_success(self):
                self.assertTrue(True)

        result = reports.ObservedResult()
        unittest.TestLoader().loadTestsFromTestCase(Controls).run(result)
        payload = reports.result_payload(result)
        self.assertEqual(payload["testsRun"], 2)
        self.assertEqual(payload["expectedFailures"], 1)
        self.assertEqual(payload["unexpectedSuccesses"], 1)
        self.assertEqual(reports.result_status(result), 1)

    def test_absent_or_substituted_test_source_refuses(self):
        from types import SimpleNamespace
        import wildcat_v3_reports as shared
        with self.assertRaises(reports.EvidenceUnavailable):
            reports.run_cases((("absent_timestamp_case", "MissingTests"),))
        replacement = SimpleNamespace(__file__=str(ROOT / "repo_contract.py"),
                                      TimestampScaffoldTests=TimestampScaffoldTests)
        with mock.patch.object(shared.importlib, "import_module", return_value=replacement):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.run_cases(reports.CASE_TESTS["scaffold"])

    def test_unavailable_product_refuses_without_conformance_report(self):
        for case in ("mapping", "demonstration", "integration"):
            with self.subTest(case=case), temporary_cwd() as root, redirect_stderr(io.StringIO()) as stderr:
                with self.assertRaises(SystemExit) as exc:
                    proof.main(["--case", case, "--report", ".hexaemeron/r.json"])
                self.assertEqual(exc.exception.code, 2)
                self.assertIn("timestamp case not implemented: " + case, stderr.getvalue())
                self.assertFalse((root / ".hexaemeron/r.json").exists())

    def test_unexpected_errors_do_not_publish_exception_contents(self):
        with temporary_cwd() as root, mock.patch.object(reports, "run_cases", side_effect=RuntimeError("private content")), redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as exc:
                proof.main(["--case", "scaffold", "--report", ".elenchus/r.json"])
            self.assertEqual(exc.exception.code, 2)
            self.assertIn("RuntimeError", stderr.getvalue())
            self.assertNotIn("private content", stderr.getvalue())
            self.assertFalse((root / ".elenchus/r.json").exists())

    def test_report_reexecution_admits_identical_bytes_only(self):
        with temporary_cwd() as root:
            payload = reports.result_payload(observed("pass"))
            reports.write_report(".elenchus/r.json", payload)
            target = root / ".elenchus/r.json"
            before = target.stat()
            reports.write_report(".elenchus/r.json", payload)
            self.assertEqual(target.stat().st_ino, before.st_ino)
            self.assertEqual(target.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ValueError):
                reports.write_report(".elenchus/r.json", reports.result_payload(observed("fail")))
            self.assertEqual(json.loads(target.read_bytes()), payload)

    def test_source_output_separation_and_path_bounds(self):
        with temporary_cwd() as root:
            for raw in ("plugins/tabularium/source.json", "../outside.json", "/tmp/outside.json",
                        ".elenchus/../source.json", ".elenchus/r.txt", ".elenchus/a\nb.json",
                        ".elenchus/" + "x" * 4096 + ".json"):
                with self.subTest(raw=raw), self.assertRaises(ValueError):
                    reports.write_report(raw, {})
            reports.write_report(str(root / ".hexaemeron/reports/absolute.json"), {})

    def test_symlink_directory_leaf_hardlink_and_fifo_preserve_sources(self):
        with temporary_cwd() as root:
            source = root / "source.json"
            source.write_bytes(b"source")
            (root / ".elenchus").symlink_to(root, target_is_directory=True)
            with self.assertRaises(OSError):
                reports.write_report(".elenchus/new.json", {})
            self.assertFalse((root / "new.json").exists())
            (root / ".elenchus").unlink()
            (root / ".elenchus").mkdir()
            (root / ".elenchus/link.json").symlink_to(source)
            os.link(source, root / ".elenchus/hard.json")
            os.mkfifo(root / ".elenchus/fifo.json")
            for leaf in ("link", "hard", "fifo"):
                with self.subTest(leaf=leaf), self.assertRaises((OSError, ValueError)):
                    reports.write_report(".elenchus/" + leaf + ".json", {})
            self.assertEqual(source.read_bytes(), b"source")

    def test_oversized_output_is_refused_before_creation(self):
        with temporary_cwd() as root, self.assertRaises(ValueError):
            reports.write_report(".elenchus/large.json", {"value": "x" * reports.REPORT_CAP})
        self.assertFalse((root / ".elenchus/large.json").exists())

    def test_runner_and_reporter_use_explicit_inprocess_tests(self):
        self.assertEqual(reports.CASE_TESTS["scaffold"], (("test_wildcat_timestamps", "TimestampScaffoldTests"),))
        for name in ("prove_wildcat_timestamps.py", "wildcat_timestamp_reports.py"):
            tree = ast.parse((HERE / name).read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    self.assertFalse((getattr(node, "module", "") or "").startswith("subprocess"))
                    self.assertFalse(any(alias.name == "subprocess" for alias in node.names))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, ("discover", "loadTestsFromNames"))

    def test_public_bundle_binds_source_and_portable_bytes(self):
        bundle = ROOT / "docs/kickoff/1997"
        manifest = json.loads((bundle / "bundle.json").read_bytes())
        self.assertEqual(manifest["schema"], "fiat-1997-public-specification/v1")
        names = set()
        for row in manifest["files"]:
            name = Path(row["path"])
            self.assertFalse(name.is_absolute())
            self.assertNotIn("..", name.parts)
            self.assertNotIn(row["path"], names)
            names.add(row["path"])
            content = (bundle / name).read_bytes()
            self.assertEqual(len(content), row["bytes"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), row["sha256"])
            self.assertNotIn(b"/Users/", content)
            self.assertNotIn(b'"response_body"', content)
        self.assertEqual({str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file()}, names | {"bundle.json"})
        pins = json.loads((bundle / "source-pins.json").read_bytes())["specification"]
        for name, pin in pins.items():
            content = (bundle / name).read_bytes()
            self.assertTrue(pin["source_prefix_preserved"])
            self.assertEqual(hashlib.sha256(content[:pin["source_bytes"]]).hexdigest(), pin["source_sha256"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), pin["public_sha256"])
        self.assertEqual(pins["runbook.md"]["source_sha256"], "fa333058f76f483f64467ab469ba36695da2643054714c6d7cd2dea7459de976")
        self.assertEqual(pins["design-evidence.json"]["source_sha256"], "fad03e94e38ba874d9ad8a47e815433d232ba550f2772a1052fd50f96281c4e3")

    def test_selection_reports_are_complete_and_digest_bound(self):
        bundle = ROOT / "docs/kickoff/1997"
        design = json.loads((bundle / "design-evidence.json").read_bytes())
        self.assertEqual(design["selection"]["candidate"], "collector-journal")
        executed = 0
        for result in design["results"]:
            if result["state"] == "pending":
                continue
            content = (bundle / result["report"]["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(), result["report"]["sha256"])
            payload = json.loads(content)
            self.assertEqual(payload["candidate"], result["candidate"])
            self.assertEqual(payload["criterion"], result["criterion"])
            self.assertEqual(payload["exit"], 0)
            executed += 1
        self.assertEqual(executed, 18)

    def test_legacy_v1_release_verifies_offline(self):
        self._legacy_roundtrip("wildcat-v1")

    def test_legacy_v2_release_verifies_offline(self):
        self._legacy_roundtrip("wildcat-v2")

    def _legacy_roundtrip(self, generation):
        from test_wildcat_view import release_fixture, view
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
            root = Path(temporary).resolve()
            release = release_fixture(root / generation, generation)
            result = view.make_wildcat_view(release)
            self.assertEqual({row["claim"] for row in result["records"]},
                             {"market_terms", "market_closed", "borrow", "repayment"})
            output = root / "view.json"
            built = view.build_wildcat_view(release, output)
            self.assertEqual(view.verify_wildcat_view(release, output), built)
            self.assertEqual(json.loads(output.read_bytes()), result)


if __name__ == "__main__":
    unittest.main()
