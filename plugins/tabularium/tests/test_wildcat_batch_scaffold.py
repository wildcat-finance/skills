"""Exercise the batch runner interfaces, their refusals and the public bundle."""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import emit_wildcat_batch_report as emitter
import prove_wildcat_batches as proof
import wildcat_batch_reports as reports

BUNDLE = ROOT / "docs/kickoff/2087"
# The receipted study, runbook and design record the bundle copies byte for byte.
RECEIPTED = {
    "study.md": "2726baaa8e4cb92b24ecb0c53041d81d524543e76a124d0781556a53845b3a8b",
    "runbook.md": "73ddc0fbc7683689f92c743b8ab4d7e9ab72c1e36b34ebabaa65eec3b7bcf415",
    "design-evidence.json": "d13ace405808ba920cc911b4578ef133b88d7103244cbb9cf1c794478432bc6a",
}
PROBES = ("design/batch_join_probe.py", "design/retained_join_probe.py")
UNITTEST_V1_KEYS = {"schema", "complete", "testsRun", "failures", "errors", "skipped",
                    "expectedFailures", "unexpectedSuccesses"}
DESIGN_REPORT_KEYS = {"schema", "candidate", "criterion", "value", "unit", "command", "exit"}
DRAFT_SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")


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


def design_record():
    return json.loads((BUNDLE / "design-evidence.json").read_bytes())


def pending_pairs():
    return {(row["candidate"], row["criterion"]) for row in design_record()["results"]
            if row["state"] == "pending"}


class BatchScaffoldTests(unittest.TestCase):
    def test_parser_accepts_exactly_the_pending_pairs(self):
        pending = pending_pairs()
        self.assertEqual(len(pending), 12)
        self.assertEqual(pending, set(reports.PENDING_PAIRS))
        parser = proof.build_parser()
        for candidate, criterion in sorted(pending):
            with self.subTest(candidate=candidate, criterion=criterion):
                args = parser.parse_args(["--candidate", candidate, "--criterion", criterion,
                                          "--report", ".hexaemeron/r.json"])
                self.assertEqual((args.candidate, args.criterion), (candidate, criterion))
        for candidate, criterion in (("role-qualified", "schema-parity"),
                                     ("adjacent-burn", "single-claim"),
                                     ("adjacent-burn", "retained-join-closure"),
                                     ("adjacent-burn-", "schema-parity")):
            with self.subTest(candidate=candidate, criterion=criterion), \
                    redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                parser.parse_args(["--candidate", candidate, "--criterion", criterion,
                                   "--report", ".hexaemeron/r.json"])
            self.assertEqual(raised.exception.code, 2)

    def test_every_unbuilt_conformance_criterion_refuses_with_exit_2_and_no_report(self):
        self.assertEqual(set(reports.CONFORMANCE), {("adjacent-burn", "semantic-conformance"),
                                                    ("adjacent-burn", "schema-parity"),
                                                    ("adjacent-burn", "retained-conformance")})
        for candidate, criterion in sorted(reports.PENDING_PAIRS - set(reports.CONFORMANCE)):
            with self.subTest(candidate=candidate, criterion=criterion), temporary_cwd() as root, \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", candidate, "--criterion", criterion,
                                "--report", ".hexaemeron/design-reports/" + candidate + "-" + criterion + ".json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("EvidenceUnavailable", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_malformed_arguments_create_no_report(self):
        for runner, arguments in (
                (proof.main, ["--candidate", "unknown", "--criterion", "schema-parity", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "adjacent-burn", "--criterion", "unknown", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "adjacent-burn", "--criterion", "schema-parity"]),
                (proof.main, ["--candidate", "adjacent-burn", "--criterion", "schema-parity", "--report", "reports/r.json"]),
                (emitter.main, ["--step", "5", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "one", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "1"])):
            with self.subTest(arguments=arguments), temporary_cwd() as root, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    runner(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(list(root.iterdir()), [])

    def test_pass_fail_error_counters_are_distinct_unittest_v1(self):
        for kind, failures, errors, status in (
                ("pass", 0, 0, 0), ("fail", 1, 0, 1), ("error", 0, 1, 2)):
            with self.subTest(kind=kind):
                result = observed(kind)
                payload = reports.result_payload(result)
                self.assertEqual(set(payload), UNITTEST_V1_KEYS)
                self.assertEqual(payload, {
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
                with mock.patch.object(reports, "run_cases", return_value=result), \
                        redirect_stderr(io.StringIO()):
                    actual = emitter.main(["--step", "1", "--report", ".elenchus/2087-step-1.json"])
                self.assertEqual(actual, status)
                self.assertEqual(json.loads((root / ".elenchus/2087-step-1.json").read_bytes()),
                                 reports.result_payload(result))

    def test_step_selection_runs_only_its_declared_classes(self):
        self.assertEqual(reports.STEP_CASES[1], (("test_wildcat_batch_scaffold", "BatchScaffoldTests"),))
        for step, selected in reports.STEP_CASES.items():
            with self.subTest(step=step), temporary_cwd(), \
                    mock.patch.object(reports, "run_cases", return_value=observed("pass")) as runner, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", str(step), "--report", ".elenchus/r.json"]), 0)
                runner.assert_called_once_with(selected)

    def test_undeclared_step_refuses_without_report(self):
        # Every parser-accepted Step now declares classes, so withdraw one at a
        # time and require the refusal the scaffold promised while they were absent.
        self.assertEqual(sorted(reports.STEP_CASES), [1, 2, 3, 4])
        for step in (1, 2, 3, 4):
            declared = {other: cases for other, cases in reports.STEP_CASES.items() if other != step}
            with self.subTest(step=step), temporary_cwd() as root, \
                    mock.patch.dict(reports.STEP_CASES, declared, clear=True), \
                    mock.patch.object(reports, "run_cases") as runner, redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", str(step), "--report", ".elenchus/r.json"])
                self.assertEqual(raised.exception.code, 2)
                runner.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_declared_step_one_classes_resolve_in_process(self):
        for module_name, class_name in reports.STEP_CASES[1]:
            source = HERE / (module_name + ".py")
            self.assertTrue(source.is_file() and not source.is_symlink())
            tree = ast.parse(source.read_bytes())
            classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
            self.assertIn(class_name, classes)

    def test_report_path_refuses_existing_file_and_symlinked_parent(self):
        with temporary_cwd() as root, mock.patch.object(reports, "run_cases", return_value=observed("pass")), \
                redirect_stderr(io.StringIO()):
            (root / ".elenchus").mkdir()
            (root / ".elenchus/r.json").write_bytes(b"unchanged")
            with self.assertRaises(SystemExit) as raised:
                emitter.main(["--step", "1", "--report", ".elenchus/r.json"])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual((root / ".elenchus/r.json").read_bytes(), b"unchanged")
            (root / "target").mkdir()
            (root / ".hexaemeron").symlink_to(root / "target", target_is_directory=True)
            with self.assertRaises(SystemExit) as raised:
                emitter.main(["--step", "1", "--report", ".hexaemeron/steps/1/focused.json"])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(list((root / "target").iterdir()), [])
            (root / ".hexaemeron").unlink()
            (root / ".hexaemeron").mkdir()
            (root / ".hexaemeron/r.json").symlink_to(root / ".elenchus/r.json")
            with self.assertRaises(SystemExit) as raised:
                emitter.main(["--step", "1", "--report", ".hexaemeron/r.json"])
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual((root / ".elenchus/r.json").read_bytes(), b"unchanged")

    def test_report_creates_missing_parents_as_fresh_bounded_json(self):
        with temporary_cwd() as root, mock.patch.object(reports, "run_cases", return_value=observed("pass")), \
                redirect_stderr(io.StringIO()):
            self.assertEqual(emitter.main(["--step", "1", "--report", ".hexaemeron/steps/1/focused.json"]), 0)
            path = root / ".hexaemeron/steps/1/focused.json"
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / ".hexaemeron/steps").stat().st_mode & 0o777, 0o700)
            self.assertEqual(json.loads(path.read_bytes())["testsRun"], 1)
            with self.assertRaises(ValueError):
                reports.write_report(".hexaemeron/large.json", {"x": "x" * reports.REPORT_CAP})
            self.assertFalse((root / ".hexaemeron/large.json").exists())

    def test_implemented_criterion_writes_one_closed_design_report(self):
        for value, status in ((True, 0), (False, 1)):
            resolver = mock.Mock(return_value=(value, {"result": {"testsRun": 1}}))
            with self.subTest(value=value), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("adjacent-burn", "semantic-conformance"): resolver}), \
                    redirect_stderr(io.StringIO()):
                arguments = ["--candidate", "adjacent-burn", "--criterion", "semantic-conformance",
                             "--report", ".hexaemeron/design-reports/adjacent-burn-semantic-conformance.json"]
                self.assertEqual(proof.main(arguments), status)
                path = root / ".hexaemeron/design-reports/adjacent-burn-semantic-conformance.json"
                payload = json.loads(path.read_bytes())
                self.assertEqual(set(payload), DESIGN_REPORT_KEYS)
                self.assertEqual(payload["schema"], "protasis-design-report/v1")
                self.assertEqual((payload["candidate"], payload["criterion"]), ("adjacent-burn", "semantic-conformance"))
                self.assertIs(payload["value"], value)
                self.assertEqual((payload["unit"], payload["exit"]), ("boolean", status))
                self.assertEqual(payload["command"], "python3 " + reports.PROOF_REPORTER + " " + " ".join(arguments))
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                sidecar = json.loads((path.with_suffix(".observations.json")).read_bytes())
                self.assertEqual(sidecar["schema"], reports.OBSERVATIONS_SCHEMA)
                self.assertEqual(sidecar["observations"], {"result": {"testsRun": 1}})
                resolver.assert_called_once_with()
                with self.assertRaises(SystemExit) as raised:
                    proof.main(arguments)
                self.assertEqual(raised.exception.code, 2)
                self.assertEqual(json.loads(path.read_bytes()), payload)
                self.assertIn(("adjacent-burn", "semantic-conformance"), reports.CONFORMANCE)
        for cases_kind in ("pass", "fail"):
            with self.subTest(focused=cases_kind), mock.patch.object(reports, "run_cases", return_value=observed(cases_kind)):
                value, observations = reports.focused_resolver((("module", "Class"),))()
                self.assertIs(value, cases_kind == "pass")
                self.assertEqual(observations["result"]["testsRun"], 1)
                self.assertEqual(len(observations["executed_ids"]), 1)

    def test_existing_report_or_sidecar_leaf_refuses_before_the_resolver_runs(self):
        report = ".hexaemeron/design-reports/adjacent-burn-schema-parity.json"
        sidecar = ".hexaemeron/design-reports/adjacent-burn-schema-parity.observations.json"
        for existing, absent in ((report, sidecar), (sidecar, report)):
            resolver = mock.Mock(return_value=(True, {"result": {"testsRun": 1}}))
            with self.subTest(existing=existing), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("adjacent-burn", "schema-parity"): resolver}), \
                    redirect_stderr(io.StringIO()) as error:
                (root / ".hexaemeron/design-reports").mkdir(parents=True)
                (root / existing).write_bytes(b"unchanged")
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "adjacent-burn", "--criterion", "schema-parity", "--report", report])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("EvidenceUnavailable", error.getvalue())
                resolver.assert_not_called()
                self.assertEqual((root / existing).read_bytes(), b"unchanged")
                self.assertFalse((root / absent).exists())
                self.assertEqual(sorted(path.name for path in (root / ".hexaemeron/design-reports").iterdir()),
                                 [Path(existing).name])

    def test_step_two_declares_the_mapping_and_parity_classes(self):
        self.assertEqual(reports.STEP_CASES[2], (("test_wildcat_batch_mapping", "BatchMappingTests"),
                                                 ("test_wildcat_batch_parity", "BatchSchemaParityTests")))
        self.assertEqual(reports.MAPPING_CASES + reports.PARITY_CASES, reports.STEP_CASES[2])
        for module_name, class_name in reports.STEP_CASES[2]:
            source = HERE / (module_name + ".py")
            self.assertTrue(source.is_file() and not source.is_symlink())
            tree = ast.parse(source.read_bytes())
            self.assertIn(class_name, [node.name for node in tree.body if isinstance(node, ast.ClassDef)])

    def test_resolver_error_or_non_boolean_refuses_without_report(self):
        for resolver in (mock.Mock(side_effect=RuntimeError("injected bug")),
                         mock.Mock(return_value=("true", None)),
                         mock.Mock(return_value=(1, None))):
            with self.subTest(resolver=resolver), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("adjacent-burn", "schema-parity"): resolver}), \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "adjacent-burn", "--criterion", "schema-parity",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertNotIn("injected bug", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])
        with mock.patch.object(reports, "run_cases", return_value=observed("error")):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.focused_resolver((("module", "Class"),))()

    def test_runners_launch_no_subprocess_and_use_no_discovery(self):
        for name in ("wildcat_batch_reports.py", "prove_wildcat_batches.py", "emit_wildcat_batch_report.py"):
            tree = ast.parse((HERE / name).read_bytes())
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any((getattr(node, "module", "") or "").startswith(("subprocess", "os"))
                                 or any(alias.name in ("subprocess", "os") for alias in node.names)
                                 for node in imports), name)
            calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)]
            self.assertNotIn("discover", calls)
            self.assertNotIn("loadTestsFromNames", calls)
            self.assertNotIn("system", calls)

    def test_registered_interfaces_are_thin_and_delegate(self):
        for name, delegate in (("prove_wildcat_batches.py", "execute_proof"),
                               ("emit_wildcat_batch_report.py", "execute_report")):
            with self.subTest(name=name):
                tree = ast.parse((HERE / name).read_bytes())
                functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
                self.assertEqual(set(functions), {"build_parser", "main"})
                body = functions["build_parser"].body
                self.assertIsInstance(body[0], ast.Assign)
                self.assertEqual(ast.unparse(body[0].value.func), "argparse.ArgumentParser")
                for statement in body[1:-1]:
                    self.assertIsInstance(statement, ast.Expr)
                    self.assertEqual(ast.unparse(statement.value.func), "parser.add_argument")
                    for keyword in statement.value.keywords:
                        if keyword.arg != "type":
                            ast.literal_eval(keyword.value)
                self.assertIsInstance(body[-1], ast.Return)
                self.assertEqual(ast.unparse(body[-1].value), "parser")
                imported = [node for node in ast.walk(functions["main"]) if isinstance(node, ast.ImportFrom)]
                self.assertEqual([(node.module, node.names[0].name) for node in imported],
                                 [("wildcat_batch_reports", delegate)])

    def test_registered_interface_bytes_remain_frozen(self):
        for name, digest in (
                ("prove_wildcat_batches.py", "fd5cc18405c074ed696172297fad91250bfb5328b246b205e2cfc7c32a2db038"),
                ("emit_wildcat_batch_report.py", "6aea002365b1985d27126f2dc8e30e9a2d2235c88d59a7a3d6db6a461c98f1df")):
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), digest, name)

    def test_public_bundle_copies_equal_the_receipted_artefacts(self):
        for name, digest in RECEIPTED.items():
            with self.subTest(name=name):
                path = BUNDLE / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        record = design_record()
        expected = set(RECEIPTED) | {"README.md", "reproduction.md", *PROBES}
        for row in record["results"]:
            if isinstance(row["report"], dict):
                path = BUNDLE / row["report"]["path"]
                self.assertFalse(path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["report"]["sha256"],
                                 row["report"]["path"])
                expected.add(row["report"]["path"])
                if row["criterion"] == "retained-join-closure":
                    sidecar = row["report"]["path"].replace(".json", ".observations.json")
                    self.assertTrue((BUNDLE / sidecar).is_file(), sidecar)
                    expected.add(sidecar)
            else:
                self.assertEqual(row["state"], "pending")
                self.assertFalse((BUNDLE / row["report"]).exists(), row["report"])
        actual = {str(path.relative_to(BUNDLE)) for path in BUNDLE.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertEqual(len(expected), 43)

    def test_public_bundle_carries_no_private_or_retained_material(self):
        for path in sorted(path for path in BUNDLE.rglob("*") if path.is_file()):
            content = path.read_bytes()
            with self.subTest(path=str(path.relative_to(BUNDLE))):
                self.assertFalse(path.is_symlink())
                self.assertLessEqual(len(content), 256 * 1024)
                self.assertNotIn(b"/tmp/fiat/", content)
                self.assertNotIn(b'"response_body"', content)
                self.assertNotIn(b'"eth_getLogs"', content)
                self.assertNotIn(b'"jsonrpc"', content)
                self.assertNotIn(b"-----BEGIN", content)
                self.assertEqual(re.findall(rb"0x[0-9a-fA-F]{40}", content), [])
        self.assertFalse((BUNDLE / "private").exists())
        self.assertFalse((BUNDLE / "__pycache__").exists())

    def test_decision_draft_is_the_study_bridge_record(self):
        study = (BUNDLE / "study.md").read_text(encoding="utf-8")
        fence = re.search(r"```design-bridge\n(.*?)```", study, re.DOTALL)
        rows = dict(line.split(" | ", 1) for line in fence.group(1).strip().splitlines())
        self.assertEqual(rows["schema"], "hypomnema-design-bridge/v1")
        self.assertEqual(rows["decision"], design_record()["selection"]["candidate"])
        self.assertEqual(rows["record"], "docs/decisions/drafts/give-wildcat-withdrawal-batch-events-native-meaning.md")
        draft = (ROOT / rows["record"]).read_text(encoding="utf-8")
        self.assertTrue(draft.startswith("# Decision: "))
        headings = re.findall(r"^## (.+)$", draft, re.MULTILINE)
        self.assertEqual(tuple(headings), DRAFT_SECTIONS)
        status = draft.split("## Status", 1)[1].split("## Context", 1)[0].strip()
        self.assertRegex(status, r"^[A-Za-z]+, \d{4}-\d{2}-\d{2}")
        for term in ("adjacent", "exit-queue", "pool", "burned-scaled-claims", "reserved-assets",
                     "expiry", "1.0.0"):
            self.assertIn(term, draft)
        self.assertNotIn("ADR-NNN", draft)
