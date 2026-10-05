"""Exercise report truth, bounded writes and the frozen public specification."""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import emit_wildcat_v3_report as emitter
import prove_wildcat_v3 as proof
import wildcat_v3_proofs as proofs
import wildcat_v3_reports as reports


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
                self.fail("deliberate assertion specimen")
            if kind == "error":
                raise RuntimeError("deliberate infrastructure specimen")
            if kind == "skip":
                self.skipTest("deliberate skipped specimen")
    result = reports.ObservedResult()
    unittest.TestSuite([Specimen()]).run(result)
    return result


class ScaffoldTests(unittest.TestCase):
    def test_real_pass_fail_error_counters_are_distinct(self):
        for kind, failures, errors, status in (
                ("pass", 0, 0, 0), ("fail", 1, 0, 1), ("error", 0, 1, 2)):
            with self.subTest(kind=kind):
                result = observed(kind)
                self.assertEqual(reports.result_payload(result), {
                    "schema": "elenchus.unittest.v1", "complete": True,
                    "testsRun": 1, "failures": failures, "errors": errors,
                    "skipped": 0, "expectedFailures": 0, "unexpectedSuccesses": 0})
                self.assertEqual(reports.result_status(result), status)
                self.assertEqual(len(result.executed_ids), 1)

    def test_skipped_or_empty_suite_never_passes(self):
        self.assertEqual(reports.result_status(observed("skip")), 1)
        self.assertEqual(reports.result_status(reports.ObservedResult()), 2)

    def test_focused_emitter_preserves_error_classification(self):
        for kind, status in (("pass", 0), ("fail", 1), ("error", 2)):
            with self.subTest(kind=kind), temporary_cwd() as root:
                result = observed(kind)
                with mock.patch.object(reports, "run_cases", return_value=result), redirect_stderr(io.StringIO()):
                    actual = emitter.main(["--step", "1", "--report", ".elenchus/result.json"])
                self.assertEqual(actual, status)
                self.assertEqual(json.loads((root/".elenchus/result.json").read_bytes()),
                                 reports.result_payload(result))

    def test_step_selection_names_only_its_declared_cases(self):
        for step, selected in reports.STEP_CASES.items():
            with self.subTest(step=step), temporary_cwd(), \
                    mock.patch.object(reports, "run_cases", return_value=observed("pass")) as runner, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", str(step), "--report", ".elenchus/r.json"]), 0)
                runner.assert_called_once_with(selected)
        self.assertEqual(reports.STEP_CASES[1], (("test_wildcat_v3_scaffold", "ScaffoldTests"),))

    def test_no_discovery_hooks_or_subprocesses_in_focused_runner(self):
        for path in (HERE/"wildcat_v3_reports.py", HERE/"wildcat_v3_proofs.py"):
            tree = ast.parse(path.read_text())
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any((getattr(node,"module","") or "").startswith("subprocess")
                                 or any(alias.name == "subprocess" for alias in node.names) for node in imports))
            calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)]
            self.assertNotIn("discover", calls)
            self.assertNotIn("loadTestsFromNames", calls)

    def test_exact_test_class_ignores_module_load_tests(self):
        class Selected(unittest.TestCase):
            def test_selected(self):
                self.assertTrue(True)
        def forbidden(*args):
            raise AssertionError("module-wide load hook was invoked")
        module = SimpleNamespace(__file__=str(HERE/"test_wildcat_v3_scaffold.py"),
                                 Selected=Selected, load_tests=forbidden)
        with mock.patch.object(reports.importlib, "import_module", return_value=module):
            result = reports.run_cases((("test_wildcat_v3_scaffold", "Selected"),))
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(reports.result_status(result), 0)

    def test_unavailable_source_and_class_refuse(self):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(reports, "HERE", Path(temporary)):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.run_cases((("test_wildcat_v3_semantics", "SemanticConformanceTests"),))
        with self.assertRaises(reports.EvidenceUnavailable):
            reports.run_cases((("test_wildcat_v3_scaffold", "MissingClass"),))

    def test_import_origin_substitution_refuses(self):
        module = SimpleNamespace(__file__=str(ROOT/"repo_contract.py"), ScaffoldTests=ScaffoldTests)
        with mock.patch.object(reports.importlib, "import_module", return_value=module):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.run_cases((("test_wildcat_v3_scaffold", "ScaffoldTests"),))

    def test_report_is_fresh_bounded_json(self):
        with temporary_cwd() as root:
            reports.write_report(".elenchus/r.json", {"tests": 1})
            path=root/".elenchus/r.json"
            self.assertEqual(json.loads(path.read_bytes()), {"tests": 1})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            before=path.read_bytes()
            with self.assertRaises(FileExistsError):
                reports.write_report(".elenchus/r.json", {"tests": 2})
            self.assertEqual(path.read_bytes(), before)
            with self.assertRaises(ValueError):
                reports.write_report(".elenchus/large.json", {"x": "x"*reports.REPORT_CAP})
            self.assertFalse((root/".elenchus/large.json").exists())

    def test_path_traversal_external_root_and_source_tree_refuse(self):
        with temporary_cwd() as root:
            for path in ("../r.json", "plugins/r.json", ".elenchus/r.txt", ".elenchus/../r.json",
                         "/tmp/outside-wildcat-proof.json", ".elenchus/line\nbreak.json"):
                with self.subTest(path=path), self.assertRaises(ValueError):
                    reports.write_report(path, {})
            reports.write_report(str(root/".hexaemeron/reports/r.json"), {})

    def test_symlink_parent_leaf_and_fifo_are_preserved(self):
        with temporary_cwd() as root:
            (root/"target").mkdir()
            (root/".elenchus").symlink_to(root/"target", target_is_directory=True)
            with self.assertRaises(OSError):
                reports.write_report(".elenchus/r.json", {})
            self.assertFalse((root/"target/r.json").exists())
            (root/".elenchus").unlink();(root/".elenchus").mkdir()
            (root/"target/original").write_bytes(b"unchanged")
            (root/".elenchus/r.json").symlink_to(root/"target/original")
            with self.assertRaises(FileExistsError):
                reports.write_report(".elenchus/r.json", {})
            self.assertEqual((root/"target/original").read_bytes(), b"unchanged")
            os.mkfifo(root/".elenchus/fifo.json")
            with self.assertRaises(FileExistsError):
                reports.write_report(".elenchus/fifo.json", {})

    def test_malformed_command_arguments_create_no_report(self):
        for parser, arguments in (
                (proof.main, ["--candidate", "unknown", "--criterion", "schema-parity", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "role-qualified", "--criterion", "unknown", "--report", ".hexaemeron/r.json"]),
                (emitter.main, ["--step", "5", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "one", "--report", ".elenchus/r.json"]),
                (proof.main, ["--candidate", "role-qualified"])):
            with self.subTest(arguments=arguments), temporary_cwd() as root, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    parser(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(list(root.iterdir()), [])

    def test_unimplemented_conformance_refuses_without_scalar_report(self):
        for criterion in proofs.CONFORMANCE_CASES:
            with self.subTest(criterion=criterion), temporary_cwd() as root, \
                    mock.patch.object(reports, "HERE", root), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "role-qualified", "--criterion", criterion,
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertFalse((root/".hexaemeron/r.json").exists())

    def test_known_unimplemented_candidate_refuses(self):
        for candidate in ("view-projection", "topic-only"):
            with self.subTest(candidate=candidate), temporary_cwd() as root, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", candidate, "--criterion", "schema-parity",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(list(root.iterdir()), [])

    def test_proof_pass_or_fail_requires_observed_tests(self):
        for kind, status, value in (("pass", 0, True), ("fail", 1, False)):
            with self.subTest(kind=kind), temporary_cwd() as root, \
                    mock.patch.object(proofs, "run_cases", return_value=observed(kind)), redirect_stderr(io.StringIO()):
                actual=proof.main(["--candidate", "role-qualified", "--criterion", "semantic-conformance",
                                   "--report", ".hexaemeron/r.json"])
                self.assertEqual(actual,status)
                payload=json.loads((root/".hexaemeron/r.json").read_bytes())
                self.assertEqual(payload["schema"], "protasis-design-report/v1")
                self.assertEqual(payload["value"],value)
                self.assertEqual(payload["exit"],status)
                observations=json.loads((root/".hexaemeron/r.observations.json").read_bytes())
                self.assertEqual(observations["result"]["testsRun"],1)
                self.assertEqual(observations["result"]["failures"],status)
                self.assertEqual(len(observations["executed_ids"]),1)

    def test_infrastructure_error_never_produces_boolean_proof(self):
        with temporary_cwd() as root, mock.patch.object(proofs, "run_cases", return_value=observed("error")), \
                redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                proof.main(["--candidate", "role-qualified", "--criterion", "schema-parity",
                            "--report", ".hexaemeron/r.json"])
            self.assertEqual(raised.exception.code,2)
            self.assertFalse((root/".hexaemeron/r.json").exists())
            self.assertFalse((root/".hexaemeron/r.observations.json").exists())

    def test_unexpected_failure_refuses_without_report(self):
        with temporary_cwd() as root, mock.patch.object(proofs, "run_cases", side_effect=RuntimeError("injected bug")), \
                redirect_stderr(io.StringIO()) as error:
            with self.assertRaises(SystemExit) as raised:
                proof.main(["--candidate", "role-qualified", "--criterion", "schema-parity",
                            "--report", ".hexaemeron/r.json"])
            self.assertEqual(raised.exception.code,2)
            self.assertIn("RuntimeError",error.getvalue())
            self.assertNotIn("injected bug",error.getvalue())
            self.assertFalse((root/".hexaemeron/r.json").exists())

    def test_public_bundle_matches_every_declared_digest(self):
        bundle=ROOT/"docs/kickoff/1378"
        manifest=json.loads((bundle/"bundle.json").read_bytes())
        self.assertEqual(manifest["schema"],"fiat-1378-public-specification/v1")
        names=set()
        for row in manifest["files"]:
            path=Path(row["path"])
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..",path.parts)
            self.assertNotIn(row["path"],names);names.add(row["path"])
            self.assertFalse((bundle/path).is_symlink())
            content=(bundle/path).read_bytes()
            self.assertEqual(len(content),row["bytes"])
            self.assertEqual(hashlib.sha256(content).hexdigest(),row["sha256"])
        self.assertTrue({"study.md","runbook.md","design-evidence.json","source-pins.json",
                         "capture-admission-summary.json","audit-reading-index.json","README.md"} <= names)
        expected={
            "study.md":"a590d9c3661fe74f9ce53726a49c8fe6b214a4f08add183377d73cbefb3a1d6f",
            "runbook.md":"be8c3e2da17548418046e1bf1b3547889384437f186d97e99c342e6eec1c9fbb",
            "design-evidence.json":"80282666266db259f1afb600ee981f28928fde0b077cf333967501672a04bb50"}
        for name,digest in expected.items():
            self.assertEqual(hashlib.sha256((bundle/name).read_bytes()).hexdigest(),digest)
        pins=json.loads((bundle/"source-pins.json").read_bytes())["specification"]["study"]
        content=(bundle/"study.md").read_bytes()
        self.assertEqual(pins["original"],{
            "bytes":45419,
            "sha256":"f7956d890d7bab59b75ae6e511624e997e6dc815ea558cff64bb4c1e09d75f1a"})
        self.assertEqual(hashlib.sha256(content[:45419]).hexdigest(),pins["original"]["sha256"])
        self.assertEqual(len(content),pins["effective"]["bytes"])
        self.assertEqual(hashlib.sha256(content).hexdigest(),pins["effective"]["sha256"])
        self.assertTrue(pins["original_prefix_preserved"])

    def test_registered_parser_bytes_remain_frozen(self):
        for name,digest in (
                ("prove_wildcat_v3.py","f4fa83f22d7db99b48399936e7d1c41ef3d89795a544f895265bfedbe42d45a2"),
                ("emit_wildcat_v3_report.py","dcc1b6679b799965067e6d224016dd04f03ec348cb46d3807333b2f72634b4e1")):
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),digest)

    def test_public_bundle_does_not_embed_recovered_payloads(self):
        bundle=ROOT/"docs/kickoff/1378"
        manifest=json.loads((bundle/"bundle.json").read_bytes())
        actual={str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file()}
        self.assertEqual(actual,{row["path"] for row in manifest["files"]}|{"bundle.json"})
        for row in manifest["files"]:
            content=(bundle/row["path"]).read_bytes()
            self.assertLessEqual(len(content),2*1024*1024)
            self.assertNotIn(b'"response_body"',content)
            self.assertNotIn(b'"eth_getLogs"',content)
            self.assertNotIn(b'"jsonrpc"',content)
            self.assertNotIn(b'-----BEGIN PRIVATE KEY-----',content)
            self.assertNotIn(b'-----BEGIN OPENSSH PRIVATE KEY-----',content)
