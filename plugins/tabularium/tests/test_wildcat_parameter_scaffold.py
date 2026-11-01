"""Check parameter runner boundaries and the immutable public design bundle."""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import emit_wildcat_parameter_report as emitter
import prove_wildcat_parameters as proof
import wildcat_parameter_reports as reports

BUNDLE = ROOT / "docs/kickoff/2090"
RECEIPTED = {
    "study.md": "77b19078e72ab16d0635cbe8ef67e465d352ddbe59bce56770972ebf80c0f021",
    "runbook.md": "099d3fd4ceb17d0c37daaa44b9fbb7d0ab80b76a307e669c258bcff9cfbbc1ca",
    "design-evidence.json": "ad3ebdac8a3fc69c2a9d2d7f2a4f194ee1ca70327ef00619a099a67c8866ae68",
}
INTERFACES = {'prove_wildcat_parameters.py': '966b9e1334cd9c21a2d75438fbd79be87131c03e9f33be3830753828e20d14c6', 'emit_wildcat_parameter_report.py': 'd0ad1b17a36b360eea1a76717a458de36110ae8701f8319bbb8990b3657efd58'}


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


class ParameterScaffoldTests(unittest.TestCase):
    def test_parser_choices_match_all_design_pending_pairs(self):
        record = json.loads((BUNDLE / "design-evidence.json").read_bytes())
        pending = {(row["candidate"], row["criterion"]) for row in record["results"]
                   if row["state"] == "pending"}
        self.assertEqual(len(pending), 6)
        self.assertEqual(pending, reports.PENDING_PAIRS)
        for candidate, criterion in sorted(pending):
            args = proof.parser().parse_args(["--candidate", candidate, "--criterion", criterion,
                                              "--report", ".hexaemeron/r.json"])
            self.assertEqual((args.candidate, args.criterion), (candidate, criterion))

    def test_invalid_arguments_refuse_without_outputs(self):
        for runner, args in (
                (proof.main, ["--candidate", "unknown", "--criterion", "mapping-conformance", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "native-fields", "--criterion", "unknown", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "native-fields", "--criterion", "mapping-conformance"]),
                (emitter.main, ["--step", "4", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "one", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "1", "--report", "../r.json"]),
                (emitter.main, ["--step", "1", "--report", "reports/r.json"]),
                (emitter.main, ["--step", "1"])):
            with self.subTest(args=args), temporary_cwd() as root, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    runner(args)
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(list(root.iterdir()), [])

    def test_unimplemented_criteria_refuse_without_evidence(self):
        for candidate, criterion in sorted(reports.PENDING_PAIRS - set(reports.CONFORMANCE)):
            with self.subTest(candidate=candidate, criterion=criterion), temporary_cwd() as root, \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", candidate, "--criterion", criterion,
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("criterion implementation absent", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_unimplemented_steps_refuse_before_running(self):
        for step in set((1, 2, 3)) - set(reports.STEP_CASES):
            with temporary_cwd() as root, mock.patch.object(reports, "run_cases") as runner, \
                    redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", str(step), "--report", ".elenchus/r.json"])
                self.assertEqual(raised.exception.code, 2)
                runner.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_exact_pass_assertion_and_error_counters(self):
        for kind, failures, errors, status in (("pass", 0, 0, 0), ("fail", 1, 0, 1), ("error", 0, 1, 2)):
            with self.subTest(kind=kind):
                result = observed(kind)
                self.assertEqual(reports.result_payload(result), {
                    "schema": "elenchus.unittest.v1", "complete": True, "testsRun": 1,
                    "failures": failures, "errors": errors, "skipped": 0,
                    "expectedFailures": 0, "unexpectedSuccesses": 0})
                self.assertEqual(reports.result_status(result), status)
                self.assertEqual(len(result.executed_ids), 1)

    def test_skips_and_empty_runs_never_pass(self):
        self.assertEqual(reports.result_status(observed("skip")), 1)
        self.assertEqual(reports.result_status(reports.ObservedResult()), 2)

    def test_emitter_records_the_observed_result(self):
        for kind, status in (("pass", 0), ("fail", 1), ("error", 2)):
            with self.subTest(kind=kind), temporary_cwd() as root, \
                    mock.patch.object(reports, "run_cases", return_value=observed(kind)), \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", "1", "--report", ".elenchus/r.json"]), status)
                payload = json.loads((root / ".elenchus/r.json").read_bytes())
                self.assertEqual((payload["testsRun"], payload["failures"], payload["errors"]),
                                 (1, int(kind == "fail"), int(kind == "error")))

    def test_exact_classes_are_selected_without_discovery(self):
        self.assertEqual(reports.STEP_CASES[1], (("test_wildcat_parameter_scaffold", "ParameterScaffoldTests"),))
        for step, cases in reports.STEP_CASES.items():
            with temporary_cwd(), mock.patch.object(reports, "run_cases", return_value=observed("pass")) as runner, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", str(step), "--report", ".elenchus/r.json"]), 0)
                runner.assert_called_once_with(cases)

    def test_fresh_bounded_private_report(self):
        with temporary_cwd() as root, mock.patch.object(reports, "run_cases", return_value=observed("pass")), \
                redirect_stderr(io.StringIO()):
            self.assertEqual(emitter.main(["--step", "1", "--report", ".hexaemeron/steps/1/check.json"]), 0)
            self.assertEqual((root / ".hexaemeron/steps/1/check.json").stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / ".hexaemeron/steps").stat().st_mode & 0o777, 0o700)
            with self.assertRaises(ValueError):
                reports.write_report(".hexaemeron/large.json", {"x": "x" * reports.REPORT_CAP})
            self.assertFalse((root / ".hexaemeron/large.json").exists())

    def test_existing_report_refuses_before_tests(self):
        with temporary_cwd() as root, mock.patch.object(reports, "run_cases") as runner, redirect_stderr(io.StringIO()):
            (root / ".elenchus").mkdir()
            leaf = root / ".elenchus/r.json"
            leaf.write_bytes(b"unchanged")
            with self.assertRaises(SystemExit) as raised:
                emitter.main(["--step", "1", "--report", ".elenchus/r.json"])
            self.assertEqual(raised.exception.code, 2)
            runner.assert_not_called()
            self.assertEqual(leaf.read_bytes(), b"unchanged")

    def test_linked_ancestors_and_leaves_refuse_before_resolution(self):
        for mode in ("ancestor", "leaf", "dangling-leaf"):
            with self.subTest(mode=mode), temporary_cwd() as root, redirect_stderr(io.StringIO()), \
                    mock.patch.dict(reports.CONFORMANCE, {("native-fields", "mapping-conformance"): mock.Mock()}) as table:
                (root / "target").mkdir()
                if mode == "ancestor":
                    (root / ".hexaemeron").symlink_to(root / "target", target_is_directory=True)
                else:
                    (root / ".hexaemeron").mkdir()
                    target = root / "target/retained.json"
                    if mode == "leaf":
                        target.write_bytes(b"unchanged")
                    (root / ".hexaemeron/r.json").symlink_to(target)
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "native-fields", "--criterion", "mapping-conformance",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                table[("native-fields", "mapping-conformance")].assert_not_called()
                self.assertFalse((root / "target/r.observations.json").exists())

    def test_occupied_sidecar_or_report_refuses_before_resolver(self):
        for leaf in ("r.json", "r.observations.json"):
            resolver = mock.Mock(return_value=(True, {}))
            with self.subTest(leaf=leaf), temporary_cwd() as root, redirect_stderr(io.StringIO()), \
                    mock.patch.dict(reports.CONFORMANCE, {("native-fields", "mapping-conformance"): resolver}):
                (root / ".hexaemeron").mkdir()
                (root / ".hexaemeron" / leaf).write_bytes(b"unchanged")
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "native-fields", "--criterion", "mapping-conformance",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                resolver.assert_not_called()
                self.assertEqual([p.name for p in (root / ".hexaemeron").iterdir()], [leaf])

    def test_closed_proof_payload_and_observations(self):
        for value in (True, False):
            with self.subTest(value=value), temporary_cwd() as root, redirect_stderr(io.StringIO()), \
                    mock.patch.dict(reports.CONFORMANCE, {("native-fields", "mapping-conformance"):
                                                         lambda: (value, {"exercised": True})}):
                arguments = ["--candidate", "native-fields", "--criterion", "mapping-conformance",
                             "--report", ".hexaemeron/r.json"]
                self.assertEqual(proof.main(arguments), 0 if value else 1)
                self.assertEqual(json.loads((root / ".hexaemeron/r.json").read_bytes()), {
                    "schema": "protasis-design-report/v1", "candidate": "native-fields",
                    "criterion": "mapping-conformance", "value": value, "unit": "boolean",
                    "command": "python3 " + reports.PROOF_REPORTER + " " + " ".join(arguments),
                    "exit": 0 if value else 1})
                payload = json.loads((root / ".hexaemeron/r.observations.json").read_bytes())
                self.assertEqual(payload["observations"], {"exercised": True})

    def test_bad_resolver_never_writes_or_reveals_private_exception(self):
        for resolver in (mock.Mock(side_effect=RuntimeError("private path secret")),
                         mock.Mock(return_value=(1, None)), mock.Mock(return_value=("true", None))):
            with temporary_cwd() as root, redirect_stderr(io.StringIO()) as error, \
                    mock.patch.dict(reports.CONFORMANCE, {("native-fields", "mapping-conformance"): resolver}):
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "native-fields", "--criterion", "mapping-conformance",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertNotIn("private path secret", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_focused_resolver_refuses_infrastructure_error(self):
        with mock.patch.object(reports, "run_cases", return_value=observed("error")):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.focused_resolver((("module", "Class"),))()

    def test_safe_path_and_isolated_entrypoints_import_siblings(self):
        for name in INTERFACES:
            for option in ("-P", "-I"):
                result = subprocess.run([sys.executable, option, str(HERE / name), "--help"],
                                        capture_output=True, text=True, timeout=15, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--report", result.stdout)

    def test_interfaces_and_parsers_remain_frozen(self):
        for name, digest in INTERFACES.items():
            raw = (HERE / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, name)
            tree = ast.parse(raw)
            functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
            self.assertEqual(set(functions), {"parser", "main"})
            self.assertEqual(ast.unparse(functions["parser"].body[0].value.func), "argparse.ArgumentParser")
            self.assertEqual(ast.unparse(functions["parser"].body[-1].value), "parser")

    def test_exact_bundle_membership_and_receipted_bytes(self):
        expected = set(RECEIPTED) | {"README.md", "design/event-inventory.json", "design/selection_probe.py"}
        for name, digest in RECEIPTED.items():
            self.assertEqual(hashlib.sha256((BUNDLE / name).read_bytes()).hexdigest(), digest, name)
        record = json.loads((BUNDLE / "design-evidence.json").read_bytes())
        for row in record["results"]:
            if isinstance(row["report"], dict):
                path = row["report"]["path"]
                expected.add(path)
                self.assertEqual(hashlib.sha256((BUNDLE / path).read_bytes()).hexdigest(), row["report"]["sha256"])
            else:
                self.assertFalse((BUNDLE / row["report"]).exists())
        actual = {str(p.relative_to(BUNDLE)) for p in BUNDLE.rglob("*") if p.is_file()}
        self.assertEqual(actual, expected)

    def test_public_bundle_excludes_private_material(self):
        for path in BUNDLE.rglob("*"):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            self.assertFalse(path.is_symlink())
            self.assertLessEqual(len(raw), 256 * 1024)
            for forbidden in (b"/tmp/fiat/", b'"response_body"', b'"eth_getLogs"', b'"jsonrpc"', b"-----BEGIN"):
                self.assertNotIn(forbidden, raw, str(path))
            self.assertEqual(re.findall(rb"0x[0-9a-fA-F]{40}", raw), [])
        self.assertFalse((BUNDLE / "private").exists())
        self.assertFalse((BUNDLE / "__pycache__").exists())

    def test_inventory_covers_the_declared_concrete_contexts(self):
        inventory = json.loads((BUNDLE / "design/event-inventory.json").read_bytes())
        required = inventory["required"]
        self.assertEqual(len(required), 58)
        self.assertEqual(len({(r["generation"], r["role"], r["signature"]) for r in required}), 29)
        self.assertTrue(any(any(f["name"] == "" for f in r["fields"]) for r in required))

    def test_decision_bridge_has_one_standing_home(self):
        slug = "keep-wildcat-parameter-events-as-native-state.md"
        path = ROOT / "docs/decisions/drafts" / slug
        if not path.exists():
            finals = list((ROOT / "docs/decisions").glob("ADR-*-" + slug))
            self.assertEqual(len(finals), 1)
            path = finals[0]
        text = path.read_text()
        self.assertEqual(re.findall(r"^## (.+)$", text, re.MULTILINE),
                         ["Status", "Context", "Decision", "Alternatives", "Consequences"])
        for term in ("native-fields", "1.2.0", "1.0.0", "marketless", "empty", "contextual-projection"):
            self.assertIn(term, text)
