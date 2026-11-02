"""Exercise sanctions report boundaries before the product join exists."""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import emit_wildcat_sanctions_report as emitter
import prove_wildcat_sanctions as proof
import wildcat_sanctions_reports as reports

BUNDLE = ROOT / "docs/kickoff/2091"
RECEIPTED = {
    "study.md": "2349910298c95851a8361c25ed049cb87bb4e184ab4d57485658aa069f6b200f",
    "runbook.md": "1df40311137df5546e3c134f90305e6752f231805153223ea50724badd81c242",
    "design-evidence.json": "18208292de324173e9885a6abc6efa208d679e95eea02e13b617e303de6843e9",
}


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


class SanctionsScaffoldTests(unittest.TestCase):
    def _checked_source_interface(self, filename, arguments):
        owner = ROOT / "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
        spec = importlib.util.spec_from_file_location("sanctions_gate_interface", owner)
        gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate)
        relative = "plugins/tabularium/tests/" + filename
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        try:
            parser, record = gate.interface(
                ROOT, relative, {relative: ("parser", digest)})
        except gate.Refusal as exc:
            self.fail(f"source interface refused: {exc}")
        self.assertEqual(record["sha256"], digest)
        return vars(parser.parse_args(arguments))

    def test_proof_interface_is_admitted_by_source_bridge(self):
        parsed = self._checked_source_interface("prove_wildcat_sanctions.py", [
            "--candidate", "unique-key", "--criterion", "semantic-conformance",
            "--report", ".hexaemeron/proof.json"])
        self.assertEqual(parsed, {"candidate": "unique-key",
                                 "criterion": "semantic-conformance",
                                 "report": ".hexaemeron/proof.json"})

    def test_report_interface_is_admitted_by_source_bridge(self):
        parsed = self._checked_source_interface("emit_wildcat_sanctions_report.py", [
            "--step", "1", "--report", ".elenchus/report.json"])
        self.assertEqual(parsed, {"step": 1, "report": ".elenchus/report.json"})

    def test_package_version_reaches_both_marketplaces_and_manifests(self):
        tree = ast.parse((ROOT / "tests/test_version_propagation.py").read_text())
        declarations = [
            node.value for node in tree.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name)
                    and target.id == "DELIVERY_PACKAGE_VERSIONS"
                    for target in node.targets)
        ]
        self.assertEqual(len(declarations), 1)
        expected = ast.literal_eval(declarations[0])["tabularium"]
        actual = {}
        for host in (".claude-plugin", ".codex-plugin"):
            path = f"plugins/tabularium/{host}/plugin.json"
            actual[path] = json.loads((ROOT / path).read_bytes())["version"]
        for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
            listing = json.loads((ROOT / path).read_bytes())["plugins"]
            entries = [item for item in listing if item["name"] == "tabularium"]
            self.assertEqual(len(entries), 1, path)
            actual[path] = entries[0]["version"]
        self.assertEqual(actual, dict.fromkeys(actual, expected))

    def test_parser_choices_equal_design_pending_pairs(self):
        design = json.loads((BUNDLE / "design-evidence.json").read_bytes())
        pairs = {(row["candidate"], row["criterion"]) for row in design["results"]
                 if row["state"] == "pending"}
        self.assertEqual(pairs, reports.PENDING_PAIRS)
        self.assertEqual(len(pairs), 9)
        for candidate, criterion in sorted(pairs):
            args = proof.parser().parse_args([
                "--candidate", candidate, "--criterion", criterion,
                "--report", ".hexaemeron/r.json"])
            self.assertEqual((args.candidate, args.criterion), (candidate, criterion))
        for step in (1, 2, 3):
            self.assertEqual(emitter.parser().parse_args([
                "--step", str(step), "--report", ".elenchus/r.json"]).step, step)

    def test_invalid_arguments_refuse_without_output(self):
        for runner, arguments in (
                (proof.main, ["--candidate", "unknown", "--criterion", "semantic-conformance",
                              "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "unique-key", "--criterion", "unknown",
                              "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "unique-key"]),
                (emitter.main, ["--step", "4", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "one", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "1"])):
            with self.subTest(arguments=arguments), temporary_cwd() as root, \
                    redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    runner(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(list(root.iterdir()), [])

    def test_unimplemented_criteria_refuse_without_report(self):
        with mock.patch.dict(reports.CONFORMANCE, {}, clear=True):
            for candidate, criterion in reports.PENDING_PAIRS:
                with self.subTest(pair=(candidate, criterion)), temporary_cwd() as root, \
                        redirect_stderr(io.StringIO()) as error:
                    with self.assertRaises(SystemExit) as raised:
                        proof.main(["--candidate", candidate, "--criterion", criterion,
                                    "--report", ".hexaemeron/r.json"])
                    self.assertEqual(raised.exception.code, 2)
                    self.assertIn("criterion implementation absent", error.getvalue())
                    self.assertEqual(list(root.iterdir()), [])

    def test_pass_assertion_error_and_skip_counters_stay_distinct(self):
        for kind, expected, status in (("pass", (0, 0, 0), 0), ("fail", (1, 0, 0), 1),
                                       ("error", (0, 1, 0), 2), ("skip", (0, 0, 1), 1)):
            with self.subTest(kind=kind):
                result = observed(kind)
                self.assertEqual(reports.result_payload(result), {
                    "schema": "elenchus.unittest.v1", "complete": True, "testsRun": 1,
                    "failures": expected[0], "errors": expected[1], "skipped": expected[2],
                    "expectedFailures": 0, "unexpectedSuccesses": 0})
                self.assertEqual(reports.result_status(result), status)
                self.assertEqual(len(result.executed_ids), 1)
        self.assertEqual(reports.result_status(reports.ObservedResult()), 2)

    def test_focused_report_uses_observed_execution(self):
        for kind, expected in (("pass", 0), ("fail", 1), ("error", 2), ("skip", 1)):
            with self.subTest(kind=kind), temporary_cwd() as root, \
                    mock.patch.object(reports, "run_cases", return_value=observed(kind)) as run, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main([
                    "--step", "1", "--report", ".elenchus/r.json"]), expected)
                run.assert_called_once_with(reports.STEP_CASES[1])
                self.assertEqual(json.loads((root / ".elenchus/r.json").read_bytes()),
                                 reports.result_payload(observed(kind)))

    def test_undeclared_step_refuses_before_running(self):
        for step in (1, 2, 3):
            with temporary_cwd() as root, mock.patch.dict(reports.STEP_CASES, {}, clear=True), \
                    mock.patch.object(reports, "run_cases") as run, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", str(step), "--report", ".elenchus/r.json"])
                self.assertEqual(raised.exception.code, 2)
                run.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_report_paths_refuse_escape_and_outside_names(self):
        for raw in ("../r.json", "reports/r.json", ".hexaemeron/../r.json",
                    ".hexaemeron/r.txt", ".hexaemeron/line\nr.json", "/tmp/r.json"):
            with self.subTest(path=raw), temporary_cwd() as root, \
                    mock.patch.object(reports, "run_cases") as run, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", "1", "--report", raw])
                self.assertEqual(raised.exception.code, 2)
                run.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_occupied_report_and_sidecar_refuse_before_proof_execution(self):
        for occupied in (".hexaemeron/r.json", ".hexaemeron/r.observations.json"):
            with temporary_cwd() as root:
                path = root / occupied
                path.parent.mkdir()
                path.write_bytes(b"unchanged")
                resolver = mock.Mock(return_value=(True, {}))
                with mock.patch.dict(reports.CONFORMANCE, {
                        ("unique-key", "semantic-conformance"): resolver}), \
                        redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "unique-key", "--criterion", "semantic-conformance",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                resolver.assert_not_called()
                self.assertEqual(path.read_bytes(), b"unchanged")
                self.assertEqual(len(list(path.parent.iterdir())), 1)

    def test_writer_refuses_symlink_parent_and_leaf(self):
        with temporary_cwd() as root:
            (root / "target").mkdir()
            (root / ".hexaemeron").symlink_to(root / "target", target_is_directory=True)
            with self.assertRaises(OSError):
                reports.write_report(".hexaemeron/r.json", {})
            self.assertEqual(list((root / "target").iterdir()), [])
            (root / ".hexaemeron").unlink()
            (root / ".hexaemeron").mkdir()
            (root / "target/keep.json").write_bytes(b"unchanged")
            (root / ".hexaemeron/r.json").symlink_to(root / "target/keep.json")
            with self.assertRaises(OSError):
                reports.write_report(".hexaemeron/r.json", {})
            self.assertEqual((root / "target/keep.json").read_bytes(), b"unchanged")

    def test_writer_is_create_only_and_bounded(self):
        with temporary_cwd() as root:
            reports.write_report(".elenchus/step/r.json", {"value": 1})
            path = root / ".elenchus/step/r.json"
            original = path.read_bytes()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                reports.write_report(".elenchus/step/r.json", {"value": 2})
            self.assertEqual(path.read_bytes(), original)
            with self.assertRaises(ValueError):
                reports.write_report(".elenchus/large.json", {"value": "x" * reports.REPORT_CAP})
            self.assertFalse((root / ".elenchus/large.json").exists())

    def test_proof_report_records_boolean_and_observations(self):
        for value in (True, False):
            with temporary_cwd() as root, mock.patch.dict(reports.CONFORMANCE, {
                    ("unique-key", "semantic-conformance"): lambda: (value, {"checked": True})}), \
                    redirect_stderr(io.StringIO()):
                args = ["--candidate", "unique-key", "--criterion", "semantic-conformance",
                        "--report", ".hexaemeron/r.json"]
                self.assertEqual(proof.main(args), 0 if value else 1)
                report = json.loads((root / ".hexaemeron/r.json").read_bytes())
                self.assertEqual(set(report), {"schema", "candidate", "criterion", "value",
                                               "unit", "command", "exit"})
                self.assertIs(report["value"], value)
                self.assertEqual(report["exit"], 0 if value else 1)
                sidecar = json.loads((root / ".hexaemeron/r.observations.json").read_bytes())
                self.assertEqual(sidecar["observations"], {"checked": True})

    def test_non_boolean_and_infrastructure_refuse_without_report(self):
        for resolver in (lambda: (1, None), mock.Mock(side_effect=RuntimeError("private detail"))):
            with temporary_cwd() as root, mock.patch.dict(reports.CONFORMANCE, {
                    ("unique-key", "semantic-conformance"): resolver}), \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "unique-key", "--criterion", "semantic-conformance",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertNotIn("private detail", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_retained_absence_is_separate_from_positive_and_missing_custody(self):
        classify = reports.retained_classification
        self.assertEqual(classify(verified=True, present=0, joined=0, unmatched=0, ambiguous=0), "absent")
        self.assertEqual(classify(verified=True, present=2, joined=2, unmatched=0, ambiguous=0), "exercised")
        for fields in ({"verified": False, "present": 0, "joined": 0, "unmatched": 0, "ambiguous": 0},
                       {"verified": True, "present": 1, "joined": 0, "unmatched": 1, "ambiguous": 0},
                       {"verified": True, "present": 1, "joined": 0, "unmatched": 0, "ambiguous": 1},
                       {"verified": True, "present": 1, "joined": 0, "unmatched": 0, "ambiguous": 0},
                       {"verified": True, "present": 0, "joined": 1, "unmatched": 0, "ambiguous": 0},
                       {"verified": True, "present": True, "joined": 1, "unmatched": 0, "ambiguous": 0}):
            with self.subTest(fields=fields), self.assertRaises(reports.EvidenceUnavailable):
                classify(**fields)

    def test_entrypoints_import_with_reduced_paths_and_foreign_cwd(self):
        with temporary_cwd() as root:
            (root / "wildcat_sanctions_reports.py").write_text("raise RuntimeError('cwd shadow')\n")
            standard_paths = [path for path in sys.path
                              if path not in ("", str(HERE), str(ROOT), str(root))]
            for script, arguments, expected in (
                    ("prove_wildcat_sanctions.py", ["--candidate", "first-match", "--criterion",
                                                     "semantic-conformance", "--report", ".hexaemeron/r.json"], 2),
                    ("emit_wildcat_sanctions_report.py", ["--help"], 0)):
                for foreign_cwd in (False, True):
                    paths = ([str(root)] if foreign_cwd else []) + standard_paths
                    with mock.patch.object(sys, "path", paths), mock.patch.dict(sys.modules), \
                            mock.patch.object(sys, "argv", [str(HERE / script), *arguments]), \
                            redirect_stderr(io.StringIO()) as error, redirect_stdout(io.StringIO()) as output:
                        for module in ("wildcat_sanctions_reports", "wildcat_v3_reports"):
                            sys.modules.pop(module, None)
                        with self.assertRaises(SystemExit) as raised:
                            runpy.run_path(str(HERE / script), run_name="__main__")
                    self.assertEqual(raised.exception.code, expected, error.getvalue())
                    if expected:
                        self.assertIn("unavailable", error.getvalue())
                    else:
                        self.assertIn("--step", output.getvalue())
                    self.assertNotIn("ModuleNotFoundError", error.getvalue())
                    self.assertNotIn("cwd shadow", error.getvalue())
                    self.assertFalse((root / ".hexaemeron/r.json").exists())

    def test_report_dispatch_runs_in_process_when_process_helpers_are_forbidden(self):
        with temporary_cwd() as root, \
                mock.patch.object(subprocess, "run", side_effect=AssertionError("child creation forbidden")), \
                mock.patch.object(subprocess, "Popen", side_effect=AssertionError("child creation forbidden")), \
                mock.patch.object(reports, "run_cases", return_value=observed("pass")), \
                mock.patch.dict(reports.CONFORMANCE, {
                    ("unique-key", "semantic-conformance"): reports.focused_resolver(reports.STEP_CASES[1])}), \
                redirect_stderr(io.StringIO()):
            self.assertEqual(emitter.main([
                "--step", "1", "--report", ".elenchus/no-child.json"]), 0)
            self.assertEqual(proof.main([
                "--candidate", "unique-key", "--criterion", "semantic-conformance",
                "--report", ".hexaemeron/no-child.json"]), 0)
            self.assertEqual(json.loads((root / ".elenchus/no-child.json").read_bytes())["testsRun"], 1)
            self.assertIs(json.loads((root / ".hexaemeron/no-child.json").read_bytes())["value"], True)

    def test_fixed_import_refuses_foreign_cached_module_and_missing_source(self):
        foreign = mock.Mock(__file__="/tmp/foreign.py")
        with mock.patch.dict(sys.modules, {"wildcat_v3_reports": foreign}), self.assertRaises(ValueError):
            reports.fixed_module("wildcat_v3_reports")
        with self.assertRaises(ValueError):
            reports.fixed_module("missing_sanctions_source")

    def test_public_bundle_preserves_receipted_sources_and_selection_reports(self):
        for name, digest in RECEIPTED.items():
            self.assertEqual(hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest(), digest)
        design = json.loads((BUNDLE / "design-evidence.json").read_bytes())
        resolved = [row for row in design["results"] if row["state"] != "pending"]
        self.assertEqual(len(resolved), 15)
        for row in resolved:
            self.assertEqual(hashlib.sha256((BUNDLE / row["report"]["path"]).read_bytes()).hexdigest(),
                             row["report"]["sha256"])
        draft = (ROOT / "docs/decisions/drafts/join-wildcat-sanctioned-account-assets.md").read_text()
        for section in ("Status", "Context", "Decision", "Alternatives", "Consequences"):
            self.assertIn("## " + section, draft)

    def test_public_model_recomputes_selection_values(self):
        source = BUNDLE / "design/sanctions_model.py"
        specification = importlib.util.spec_from_file_location("sanctions_selection_model", source)
        model = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(model)
        for candidate in reports.CANDIDATES:
            computed = model.checks(candidate)
            for criterion, value in computed.items():
                report = json.loads((BUNDLE / "reports" / (candidate + "-" + criterion + ".json")).read_bytes())
                self.assertEqual(report["value"], value)

    def test_retained_study_report_exposes_only_digest_identity_and_absence(self):
        report = json.loads((BUNDLE / "reports/retained-inventory.json").read_bytes())
        self.assertEqual(len(report["inputs"]), 2)
        for row in report["inputs"]:
            self.assertEqual(set(row), {"generation", "raw_release_id", "manifest_sha256",
                                       "target_signature_present", "verified"})
            self.assertIs(row["verified"], True)
            self.assertEqual(set(row["target_signature_present"].values()), {False})


if __name__ == "__main__":
    unittest.main()
