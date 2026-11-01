"""Guard fee runner refusals, observed counters and source-bound specification."""

from __future__ import annotations

import ast
from contextlib import redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import emit_wildcat_fee_report as emitter
import prove_wildcat_fees as proof
import wildcat_fee_reports as reports
from test_wildcat_batch_scaffold import temporary_cwd, observed

BUNDLE = ROOT / "docs/kickoff/2089"
RECEIPTED = {
    "study.md": "cc2389b716988716375aa6fe62d94a54a21f0e46f7c4fb1f246bc8c77cc82d6d",
    "runbook.md": "dd9a70de30a18a5f259cdef2ef44be55a93a8996b4b531ec10b37ab458e14689",
    "design-evidence.json": "741975cb879ab744283f579160a84cb2b6e74b308204fb3c7e7900878a0a0c2f",
}


class FeeScaffoldTests(unittest.TestCase):
    def test_parser_accepts_exactly_pending_candidate_criterion_pairs(self):
        record = json.loads((BUNDLE / "design-evidence.json").read_bytes())
        pending = {(row["candidate"], row["criterion"]) for row in record["results"]
                   if row["state"] == "pending"}
        self.assertEqual(len(pending), 12)
        self.assertEqual(pending, set(reports.PENDING_PAIRS))
        for candidate, criterion in sorted(pending):
            args = proof.parser().parse_args(["--candidate", candidate, "--criterion", criterion,
                                              "--report", ".hexaemeron/r.json"])
            self.assertEqual((args.candidate, args.criterion), (candidate, criterion))

    def test_malformed_choices_refuse_without_output(self):
        for main, arguments in (
                (proof.main, ["--candidate", "unknown", "--criterion", "schema-parity"]),
                (proof.main, ["--candidate", "versioned-native", "--criterion", "unknown"]),
                (emitter.main, ["--step", "4"]),
                (emitter.main, ["--step", "one"])):
            with self.subTest(arguments=arguments), temporary_cwd() as root, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    main([*arguments, "--report", ".elenchus/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(list(root.iterdir()), [])

    def test_absent_proof_implementation_never_guesses_success(self):
        for candidate, criterion in sorted(reports.PENDING_PAIRS):
            with self.subTest(candidate=candidate, criterion=criterion), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {}, clear=True), redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", candidate, "--criterion", criterion,
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("criterion implementation absent", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_pass_fail_error_counters_come_from_actual_execution(self):
        for kind, failures, errors, status in (("pass", 0, 0, 0), ("fail", 1, 0, 1), ("error", 0, 1, 2)):
            with self.subTest(kind=kind):
                result = observed(kind)
                self.assertEqual(reports.result_payload(result), {
                    "schema": "elenchus.unittest.v1", "complete": True, "testsRun": 1,
                    "failures": failures, "errors": errors, "skipped": 0,
                    "expectedFailures": 0, "unexpectedSuccesses": 0})
                self.assertEqual(reports.result_status(result), status)
                self.assertEqual(len(result.executed_ids), 1)
        self.assertEqual(reports.result_status(observed("skip")), 1)
        self.assertEqual(reports.result_status(reports.ObservedResult()), 2)

    def test_step_selection_runs_only_declared_classes(self):
        self.assertEqual(reports.STEP_CASES[1], (("test_wildcat_fee_scaffold", "FeeScaffoldTests"),))
        for step, selected in reports.STEP_CASES.items():
            with self.subTest(step=step), temporary_cwd() as root, \
                    mock.patch.object(reports, "run_cases", return_value=observed("pass")) as runner, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", str(step), "--report", ".elenchus/r.json"]), 0)
                runner.assert_called_once_with(selected)
                self.assertEqual(json.loads((root / ".elenchus/r.json").read_bytes())["testsRun"], 1)

    def test_undeclared_step_refuses_without_running(self):
        with temporary_cwd() as root, mock.patch.dict(reports.STEP_CASES, {}, clear=True), \
                mock.patch.object(reports, "run_cases") as runner, redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                emitter.main(["--step", "2", "--report", ".elenchus/r.json"])
            self.assertEqual(raised.exception.code, 2)
            runner.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])

    def test_emitter_preserves_assertion_and_infrastructure_outcomes(self):
        for kind, status in (("pass", 0), ("fail", 1), ("error", 2)):
            with self.subTest(kind=kind), temporary_cwd() as root, \
                    mock.patch.object(reports, "run_cases", return_value=observed(kind)), redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", "1", "--report", ".elenchus/r.json"]), status)
                payload = json.loads((root / ".elenchus/r.json").read_bytes())
                self.assertEqual((payload["failures"], payload["errors"]),
                                 (int(kind == "fail"), int(kind == "error")))

    def test_proof_pass_fail_reports_include_observed_test_counters(self):
        for kind, status, value in (("pass", 0, True), ("fail", 1, False)):
            resolver = reports.focused_resolver((("unused", "Unused"),))
            with self.subTest(kind=kind), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("versioned-native", "schema-parity"): resolver}), \
                    mock.patch.object(reports, "run_cases", return_value=observed(kind)), redirect_stderr(io.StringIO()):
                self.assertEqual(proof.main(["--candidate", "versioned-native", "--criterion", "schema-parity",
                                             "--report", ".hexaemeron/r.json"]), status)
                payload = json.loads((root / ".hexaemeron/r.json").read_bytes())
                self.assertEqual(payload["schema"], "protasis-design-report/v1")
                self.assertEqual((payload["value"], payload["exit"]), (value, status))
                self.assertIn("prove_wildcat_fees.py", payload["command"])
                sidecar = json.loads((root / ".hexaemeron/r.observations.json").read_bytes())
                self.assertEqual(sidecar["observations"]["result"]["testsRun"], 1)
                self.assertEqual(sidecar["observations"]["result"]["failures"], status)

    def test_error_and_nonboolean_proof_results_refuse(self):
        for resolver in (mock.Mock(side_effect=RuntimeError("private value")),
                         mock.Mock(return_value=("true", None)), mock.Mock(return_value=(1, None))):
            with temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("versioned-native", "schema-parity"): resolver}), \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "versioned-native", "--criterion", "schema-parity",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertNotIn("private value", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])
        with mock.patch.object(reports, "run_cases", return_value=observed("error")):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.focused_resolver((("unused", "Unused"),))()

    def test_occupied_report_or_sidecar_refuses_before_execution(self):
        for leaf in ("r.json", "r.observations.json"):
            with self.subTest(leaf=leaf), temporary_cwd() as root, \
                    mock.patch.object(reports, "run_cases") as runner, redirect_stderr(io.StringIO()):
                directory = root / ".hexaemeron"
                directory.mkdir()
                (directory / leaf).write_bytes(b"preserved")
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "versioned-native", "--criterion", "schema-parity",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual((directory / leaf).read_bytes(), b"preserved")
                self.assertEqual(sorted(path.name for path in directory.iterdir()), [leaf])
                runner.assert_not_called()

    def test_unsafe_paths_and_symlink_parent_never_write(self):
        with temporary_cwd() as root, redirect_stderr(io.StringIO()):
            for value in ("../r.json", "reports/r.json", ".elenchus/../r.json", ".elenchus/r.txt"):
                with self.subTest(value=value), self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", "1", "--report", value])
                self.assertEqual(raised.exception.code, 2)
            (root / "target").mkdir()
            (root / ".elenchus").symlink_to(root / "target", target_is_directory=True)
            with mock.patch.object(reports, "run_cases", return_value=observed("pass")):
                with self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", "1", "--report", ".elenchus/r.json"])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(list((root / "target").iterdir()), [])

    def test_safe_path_and_isolated_mode_pin_local_sibling_imports(self):
        # Model the import-path effects in process; real -P/-I executions are
        # separate observations so the focused reporter needs no child process.
        for mode in ("safe-path", "isolated"):
            for name in ("prove_wildcat_fees.py", "emit_wildcat_fee_report.py"):
                with self.subTest(mode=mode, runner=name), temporary_cwd() as directory:
                    marker = directory / "executed"
                    (directory / "wildcat_fee_reports.py").write_text(
                        "from pathlib import Path\nPath('executed').write_text('hostile')\n")
                    paths = [entry for entry in sys.path
                             if entry and not Path(entry).resolve().is_relative_to(ROOT)]
                    if mode == "isolated":
                        paths = [entry for entry in paths if "site-packages" not in entry]
                    with mock.patch.object(sys, "path", [*paths, str(directory)]), \
                            mock.patch.dict(sys.modules), redirect_stderr(io.StringIO()):
                        for module in ("wildcat_fee_reports", "wildcat_v3_reports"):
                            sys.modules.pop(module, None)
                        namespace = runpy.run_path(str(HERE / name), run_name="fee_import_probe")
                        arguments = (["--candidate", "in-place-native", "--criterion", "schema-parity"]
                                     if name.startswith("prove_") else ["--step", "99"])
                        with self.assertRaises(SystemExit) as raised:
                            namespace["main"]([*arguments, "--report", ".hexaemeron/r.json"])
                        self.assertEqual(raised.exception.code, 2)
                        origin = Path(sys.modules["wildcat_fee_reports"].__file__).resolve()
                        self.assertEqual(origin, HERE / "wildcat_fee_reports.py")
                        self.assertEqual(Path(sys.path[0]), HERE)
                    self.assertFalse(marker.exists())
                    self.assertFalse((directory / ".hexaemeron").exists())

    def test_registered_interfaces_are_thin_with_literal_parser_builders(self):
        for name, delegate in (("prove_wildcat_fees.py", "execute_proof"),
                               ("emit_wildcat_fee_report.py", "execute_report")):
            tree = ast.parse((HERE / name).read_bytes())
            functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
            self.assertEqual(set(functions), {"parser", "main"})
            body = functions["parser"].body
            self.assertEqual(ast.unparse(body[0].targets[0]), "parser")
            self.assertEqual(ast.unparse(body[0].value.func), "argparse.ArgumentParser")
            self.assertEqual(ast.unparse(body[-1].value), "parser")
            for statement in body[1:-1]:
                self.assertEqual(ast.unparse(statement.value.func), "parser.add_argument")
            self.assertEqual(functions["main"].body[0].module, "wildcat_fee_reports")
            self.assertEqual(functions["main"].body[0].names[0].name, delegate)

    def test_report_module_launches_nothing_and_uses_no_discovery(self):
        tree = ast.parse((HERE / "wildcat_fee_reports.py").read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(any(alias.name in ("subprocess", "os") for alias in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith(("subprocess", "os")))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                self.assertNotIn(node.func.attr, ("discover", "loadTestsFromNames", "system"))

    def test_public_bundle_copies_match_receipted_bytes(self):
        for name, expected in RECEIPTED.items():
            self.assertEqual(hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest(), expected, name)
        record = json.loads((BUNDLE / "design-evidence.json").read_bytes())
        for row in record["results"]:
            if isinstance(row["report"], dict):
                source = BUNDLE / row["report"]["path"]
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), row["report"]["sha256"])
            else:
                self.assertFalse((BUNDLE / row["report"]).exists())
        self.assertTrue((BUNDLE / "design/fee_probe.py").is_file())

    def test_public_bundle_has_no_private_payload_or_custody_path(self):
        for path in BUNDLE.rglob("*"):
            if not path.is_file():
                continue
            with self.subTest(path=str(path.relative_to(BUNDLE))):
                self.assertFalse(path.is_symlink())
                data = path.read_bytes()
                self.assertLessEqual(len(data), 256 * 1024)
                self.assertNotIn(b"/tmp/fiat/", data)
                self.assertNotIn(b'"response_body"', data)
                self.assertNotIn(b"-----BEGIN", data)
                # The selection model uses a constructed fixture identifier.
                self.assertEqual(re.findall(rb"0x[0-9a-fA-F]{40}", data), [])
        self.assertFalse((BUNDLE / "private").exists())

    def test_decision_record_preserves_native_version_and_absence_limits(self):
        home = ROOT / "docs/decisions/drafts/version-wildcat-fee-native-events.md"
        if not home.exists():
            homes = list((ROOT / "docs/decisions").glob("ADR-*-version-wildcat-fee-native-events.md"))
            self.assertEqual(len(homes), 1)
            home = homes[0]
        text = home.read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.MULTILINE),
                         ["Status", "Context", "Decision", "Alternatives", "Consequences"])
        for term in ("1.0.0", "1.1.0", "fee-collection", "pool-state", "recipient", "absent", "unsupported"):
            self.assertIn(term, text)

    def test_registered_interface_bytes_remain_frozen(self):
        for name, expected in (('prove_wildcat_fees.py', '2b430b707584e8fa3d1eb6b206a4c9eaf4fc2817ba63ee95e7f5e586a5bc0cbf'), ('emit_wildcat_fee_report.py', 'b890abacc8d44b0d4385a29b1be92fd2feae194096a6b63344f99ef5db2fad5a')):
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), expected, name)
