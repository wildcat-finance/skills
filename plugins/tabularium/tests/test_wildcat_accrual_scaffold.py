"""Exercise the accrual runner interfaces, their refusals and the public bundle.

`AccrualScaffoldTests` is the Step 1 focused selection and runs in process.
`AccrualSafePathTests` starts each runner in a child process under `python3 -P`
and `PYTHONSAFEPATH=1`, the way Elenchus starts it. It stays outside every
Step's selection: its emitter child runs the Step 1 classes, so selecting it
there would start it again, and the selection runs without subprocesses.
"""

from __future__ import annotations

import ast
from contextlib import contextmanager, redirect_stderr
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))

import emit_wildcat_accrual_report as emitter
import prove_wildcat_accrual as proof
import wildcat_accrual_reports as reports
import wildcat_v3_reports

BUNDLE = ROOT / "docs/kickoff/2088"
# The receipted study, runbook and design record the bundle copies byte for byte.
RECEIPTED = {
    "study.md": "86bfb87324bb2e3292de19b6821c11b73292fe07d5d27a31769687342f326d85",
    "runbook.md": "3685f911e93084e43e0cc3c93cf2431626f8a56b2b7d842f5995bc98addadb2f",
    "design-evidence.json": "0b1f75f607b65713394d90fc75be442bf946e0cf3b0c243c5318550914936bbc",
}
# The probe that wrote every selection report, as the run held it at Step 1.
PROBE = ("design/accrual_probe.py",
         "eb0ef4ab0ccbc978ca716a258f72b9fe938fc709d938f80fcd447ce658c053f4")
RUNNERS = (("prove_wildcat_accrual.py", "execute_proof"),
           ("emit_wildcat_accrual_report.py", "execute_report"))
UNITTEST_V1_KEYS = {"schema", "complete", "testsRun", "failures", "errors", "skipped",
                    "expectedFailures", "unexpectedSuccesses"}
DESIGN_REPORT_KEYS = {"schema", "candidate", "criterion", "value", "unit", "command", "exit"}
DRAFT_SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")
DRAFT_TERMS = ("interest-and-fees-accrued", "state-updated", "interest-accrual", "pool-state",
               "`pool`", "scale-factor", "base-interest-ray", "delinquency-fee-ray",
               "protocol-fees", "fromTimestamp", "toTimestamp", "isDelinquent",
               "field order", "1.0.0")


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


class AccrualScaffoldTests(unittest.TestCase):
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
                                     ("abi-named-amounts", "numeric-fields-carried"),
                                     ("abi-named-amounts", "kinds-distinct"),
                                     ("abi-named-amounts-", "schema-parity"),
                                     ("adjacent-burn", "semantic-conformance")):
            with self.subTest(candidate=candidate, criterion=criterion), \
                    redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                parser.parse_args(["--candidate", candidate, "--criterion", criterion,
                                   "--report", ".hexaemeron/r.json"])
            self.assertEqual(raised.exception.code, 2)

    def test_every_conformance_criterion_refuses_with_exit_2_and_no_report(self):
        self.assertEqual(reports.CONFORMANCE, {})
        for candidate, criterion in sorted(reports.PENDING_PAIRS):
            with self.subTest(candidate=candidate, criterion=criterion), temporary_cwd() as root, \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", candidate, "--criterion", criterion,
                                "--report", ".hexaemeron/design/reports/" + candidate + "-" + criterion + ".json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("EvidenceUnavailable: criterion implementation absent", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])

    def test_malformed_arguments_create_no_report(self):
        for runner, arguments in (
                (proof.main, ["--candidate", "unknown", "--criterion", "schema-parity", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "abi-named-amounts", "--criterion", "unknown", "--report", ".hexaemeron/r.json"]),
                (proof.main, ["--candidate", "abi-named-amounts", "--criterion", "schema-parity"]),
                (proof.main, ["--candidate", "abi-named-amounts", "--criterion", "schema-parity", "--report", "reports/r.json"]),
                (proof.main, ["--candidate", "abi-named-amounts", "--criterion", "schema-parity", "--report", ".hexaemeron/../r.json"]),
                (emitter.main, ["--step", "5", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "0", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "one", "--report", ".elenchus/r.json"]),
                (emitter.main, ["--step", "1"]),
                (emitter.main, ["--step", "1", "--report", ".elenchus/r.txt"])):
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

    def test_focused_emitter_keeps_errors_apart_from_failures(self):
        for kind, status in (("pass", 0), ("fail", 1), ("error", 2)):
            with self.subTest(kind=kind), temporary_cwd() as root:
                result = observed(kind)
                with mock.patch.object(reports, "run_cases", return_value=result), \
                        redirect_stderr(io.StringIO()):
                    actual = emitter.main(["--step", "1", "--report", ".elenchus/2088-step-1.json"])
                self.assertEqual(actual, status)
                self.assertEqual(json.loads((root / ".elenchus/2088-step-1.json").read_bytes()),
                                 reports.result_payload(result))

    def test_step_selection_runs_only_its_declared_classes(self):
        self.assertEqual(reports.STEP_CASES[1], (("test_wildcat_accrual_scaffold", "AccrualScaffoldTests"),))
        for step, selected in reports.STEP_CASES.items():
            with self.subTest(step=step), temporary_cwd(), \
                    mock.patch.object(reports, "run_cases", return_value=observed("pass")) as runner, \
                    redirect_stderr(io.StringIO()):
                self.assertEqual(emitter.main(["--step", str(step), "--report", ".elenchus/r.json"]), 0)
                runner.assert_called_once_with(selected)
        selected = {name for cases in reports.STEP_CASES.values() for _module, name in cases}
        self.assertNotIn("AccrualSafePathTests", selected)

    def test_undeclared_step_refuses_without_report(self):
        # Withdraw each Step in turn, so the refusal stays proved once later
        # Steps declare their own classes.
        for step in (1, 2, 3, 4):
            declared = {other: cases for other, cases in reports.STEP_CASES.items() if other != step}
            with self.subTest(step=step), temporary_cwd() as root, \
                    mock.patch.dict(reports.STEP_CASES, declared, clear=True), \
                    mock.patch.object(reports, "run_cases") as runner, \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    emitter.main(["--step", str(step), "--report", ".elenchus/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("Step has no declared focused classes", error.getvalue())
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
        with temporary_cwd() as root, \
                mock.patch.object(reports, "run_cases", return_value=observed("pass")) as runner, \
                redirect_stderr(io.StringIO()):
            (root / ".elenchus").mkdir()
            (root / ".elenchus/r.json").write_bytes(b"unchanged")
            with self.assertRaises(SystemExit) as raised:
                emitter.main(["--step", "1", "--report", ".elenchus/r.json"])
            self.assertEqual(raised.exception.code, 2)
            runner.assert_not_called()
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
                    mock.patch.dict(reports.CONFORMANCE, {("abi-named-amounts", "semantic-conformance"): resolver}), \
                    redirect_stderr(io.StringIO()):
                arguments = ["--candidate", "abi-named-amounts", "--criterion", "semantic-conformance",
                             "--report", ".hexaemeron/design/reports/abi-named-amounts-semantic-conformance.json"]
                self.assertEqual(proof.main(arguments), status)
                path = root / ".hexaemeron/design/reports/abi-named-amounts-semantic-conformance.json"
                payload = json.loads(path.read_bytes())
                self.assertEqual(set(payload), DESIGN_REPORT_KEYS)
                self.assertEqual(payload["schema"], "protasis-design-report/v1")
                self.assertEqual((payload["candidate"], payload["criterion"]),
                                 ("abi-named-amounts", "semantic-conformance"))
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
                resolver.assert_called_once_with()
        for cases_kind in ("pass", "fail"):
            with self.subTest(focused=cases_kind), mock.patch.object(reports, "run_cases", return_value=observed(cases_kind)):
                value, observations = reports.focused_resolver((("module", "Class"),))()
                self.assertIs(value, cases_kind == "pass")
                self.assertEqual(observations["result"]["testsRun"], 1)
                self.assertEqual(len(observations["executed_ids"]), 1)

    def test_existing_report_or_sidecar_leaf_refuses_before_the_resolver_runs(self):
        report = ".hexaemeron/design/reports/abi-named-amounts-schema-parity.json"
        sidecar = ".hexaemeron/design/reports/abi-named-amounts-schema-parity.observations.json"
        for existing, absent in ((report, sidecar), (sidecar, report)):
            resolver = mock.Mock(return_value=(True, {"result": {"testsRun": 1}}))
            with self.subTest(existing=existing), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("abi-named-amounts", "schema-parity"): resolver}), \
                    redirect_stderr(io.StringIO()) as error:
                (root / ".hexaemeron/design/reports").mkdir(parents=True)
                (root / existing).write_bytes(b"unchanged")
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "abi-named-amounts", "--criterion", "schema-parity",
                                "--report", report])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("EvidenceUnavailable: report leaf already exists", error.getvalue())
                resolver.assert_not_called()
                self.assertEqual((root / existing).read_bytes(), b"unchanged")
                self.assertFalse((root / absent).exists())

    def test_resolver_error_or_non_boolean_refuses_without_report(self):
        for resolver in (mock.Mock(side_effect=RuntimeError("injected bug")),
                         mock.Mock(return_value=("true", None)),
                         mock.Mock(return_value=(1, None))):
            with self.subTest(resolver=resolver), temporary_cwd() as root, \
                    mock.patch.dict(reports.CONFORMANCE, {("abi-named-amounts", "schema-parity"): resolver}), \
                    redirect_stderr(io.StringIO()) as error:
                with self.assertRaises(SystemExit) as raised:
                    proof.main(["--candidate", "abi-named-amounts", "--criterion", "schema-parity",
                                "--report", ".hexaemeron/r.json"])
                self.assertEqual(raised.exception.code, 2)
                self.assertNotIn("injected bug", error.getvalue())
                self.assertEqual(list(root.iterdir()), [])
        with mock.patch.object(reports, "run_cases", return_value=observed("error")):
            with self.assertRaises(reports.EvidenceUnavailable):
                reports.focused_resolver((("module", "Class"),))()

    def test_runners_launch_no_subprocess_and_use_no_discovery(self):
        for name in ("wildcat_accrual_reports.py", *(runner for runner, _delegate in RUNNERS)):
            tree = ast.parse((HERE / name).read_bytes())
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            self.assertFalse(any((getattr(node, "module", "") or "").startswith(("subprocess", "os"))
                                 or any(alias.name.split(".")[0] in ("subprocess", "os") for alias in node.names)
                                 for node in imports), name)
            calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Attribute)]
            self.assertNotIn("discover", calls)
            self.assertNotIn("loadTestsFromNames", calls)
            self.assertNotIn("system", calls)

    def test_registered_interfaces_are_thin_and_resolve_their_directory_first(self):
        for name, delegate in RUNNERS:
            with self.subTest(name=name):
                tree = ast.parse((HERE / name).read_bytes())
                functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
                self.assertEqual(set(functions), {"build_parser", "main"})
                body = functions["build_parser"].body
                self.assertIsInstance(body[0], ast.Assign)
                self.assertEqual(ast.unparse(body[0]), "parser = argparse.ArgumentParser(description=__doc__)")
                for statement in body[1:-1]:
                    self.assertIsInstance(statement, ast.Expr)
                    self.assertEqual(ast.unparse(statement.value.func), "parser.add_argument")
                    for value in statement.value.args:
                        ast.literal_eval(value)
                    for keyword in statement.value.keywords:
                        if keyword.arg == "type":
                            self.assertEqual(ast.unparse(keyword.value), "int")
                        else:
                            ast.literal_eval(keyword.value)
                self.assertIsInstance(body[-1], ast.Return)
                self.assertEqual(ast.unparse(body[-1].value), "parser")
                main = functions["main"].body
                inserts = [index for index, statement in enumerate(main)
                           if "sys.path.insert(0, here)" in ast.unparse(statement)]
                imports = [index for index, statement in enumerate(main) if isinstance(statement, ast.ImportFrom)]
                self.assertEqual(len(inserts), 1)
                self.assertEqual(len(imports), 1)
                self.assertLess(inserts[0], imports[0])
                self.assertEqual(ast.unparse(main[0]), "here = str(Path(__file__).resolve().parent)")
                imported = main[imports[0]]
                self.assertEqual((imported.module, [alias.name for alias in imported.names]),
                                 ("wildcat_accrual_reports", [delegate]))

    def test_both_runners_resolve_their_own_directory_off_sys_path(self):
        """Run each script as `__main__` with its directory removed from
        `sys.path` and its implementation module unloaded, as safe-path mode
        leaves them. The emitter writes its report; the prover reaches its own
        conformance refusal, because no criterion is built at Step 1."""
        for name, arguments, expected in (
                ("emit_wildcat_accrual_report.py", ["--step", "1", "--report", ".elenchus/2088-step-1.json"], 0),
                ("prove_wildcat_accrual.py", ["--candidate", "abi-named-amounts", "--criterion",
                                              "semantic-conformance", "--report", ".hexaemeron/r.json"], 2)):
            script = str(HERE / name)
            path = [entry for entry in sys.path if entry and Path(entry).resolve() != HERE]
            with self.subTest(name=name), temporary_cwd() as root, \
                    mock.patch.object(sys, "path", path), mock.patch.dict(sys.modules), \
                    mock.patch.object(sys, "argv", [script, *arguments]), \
                    mock.patch.object(wildcat_v3_reports, "run_cases", return_value=observed("pass")), \
                    redirect_stderr(io.StringIO()) as error:
                sys.modules.pop("wildcat_accrual_reports", None)
                outcome = None
                try:
                    runpy.run_path(script, run_name="__main__")
                except SystemExit as exc:
                    outcome = exc.code
                except ImportError as exc:
                    outcome = type(exc).__name__
                self.assertEqual(outcome, expected, error.getvalue())
                loaded = sys.modules["wildcat_accrual_reports"]
                self.assertIsNot(loaded, reports)
                self.assertEqual(Path(loaded.__file__).resolve(), HERE / "wildcat_accrual_reports.py")
                self.assertEqual(sys.path[0], str(HERE))
                written = sorted(str(item.relative_to(root)) for item in root.rglob("*") if item.is_file())
                if expected == 0:
                    self.assertEqual(written, [".elenchus/2088-step-1.json"])
                    self.assertEqual(json.loads((root / written[0]).read_bytes()),
                                     reports.result_payload(observed("pass")))
                else:
                    self.assertEqual(written, [])
                    self.assertIn("EvidenceUnavailable: criterion implementation absent", error.getvalue())

    def test_registered_interface_bytes_remain_frozen(self):
        for name, digest in (
                ("prove_wildcat_accrual.py", "51e1ae4d2ad5338ef069b9205960cea0efb9eadacb0c0f621135a86553bd6413"),
                ("emit_wildcat_accrual_report.py", "2f0e04a00262f42f1160acca8da05d934d204abec8a563a4954ad4f34582672d")):
            self.assertEqual(hashlib.sha256((HERE / name).read_bytes()).hexdigest(), digest, name)

    def test_public_bundle_copies_equal_the_receipted_artefacts(self):
        for name, digest in (*RECEIPTED.items(), PROBE):
            with self.subTest(name=name):
                path = BUNDLE / name
                self.assertFalse(path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        record = design_record()
        self.assertEqual(record["selection"]["candidate"], "abi-named-amounts")
        expected = set(RECEIPTED) | {"README.md", PROBE[0]}
        for row in record["results"]:
            if isinstance(row["report"], dict):
                path = BUNDLE / row["report"]["path"]
                self.assertFalse(path.is_symlink())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row["report"]["sha256"],
                                 row["report"]["path"])
                expected.add(row["report"]["path"])
            else:
                self.assertEqual(row["state"], "pending")
                self.assertFalse((BUNDLE / row["report"]).exists(), row["report"])
        actual = {path.relative_to(BUNDLE).as_posix() for path in BUNDLE.rglob("*") if path.is_file()}
        self.assertEqual(actual, expected)
        self.assertEqual(len(expected), 33)

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
        self.assertFalse((BUNDLE / "design/__pycache__").exists())

    def test_decision_draft_is_the_study_bridge_record(self):
        study = (BUNDLE / "study.md").read_text(encoding="utf-8")
        fence = re.search(r"```design-bridge\n(.*?)```", study, re.DOTALL)
        rows = dict(line.split(" | ", 1) for line in fence.group(1).strip().splitlines())
        self.assertEqual(rows["schema"], "hypomnema-design-bridge/v1")
        self.assertEqual(rows["decision"], design_record()["selection"]["candidate"])
        self.assertEqual(rows["record"],
                         "docs/decisions/drafts/give-wildcat-accrual-and-state-update-events-native-meaning.md")
        home = ROOT / rows["record"]
        if home.exists():
            draft = home.read_text(encoding="utf-8")
            self.assertTrue(draft.startswith("# Decision: "))
        else:
            # Integration numbers the draft and moves it beside the assigned records.
            slug = home.name
            homes = sorted((ROOT / "docs/decisions").glob("ADR-*-" + slug))
            self.assertEqual(len(homes), 1, homes)
            home = homes[0]
            self.assertRegex(home.name, r"^ADR-[0-9]{3}-" + re.escape(slug) + r"$")
            draft = home.read_text(encoding="utf-8")
            self.assertTrue(draft.startswith("# ADR-" + home.name[4:7] + ": "))
        headings = re.findall(r"^## (.+)$", draft, re.MULTILINE)
        self.assertEqual(tuple(headings), DRAFT_SECTIONS)
        status = draft.split("## Status", 1)[1].split("## Context", 1)[0].strip()
        self.assertRegex(status, r"^[A-Za-z]+, \d{4}-\d{2}-\d{2}")
        for term in DRAFT_TERMS:
            self.assertIn(term, draft)
        self.assertNotIn("ADR-NNN", draft)
        self.assertNotIn("](../", draft)
        self.assertNotIn("](./", draft)


class AccrualSafePathTests(unittest.TestCase):
    """Start each registered runner in a child, as Elenchus does."""

    def run_child(self, root, name, arguments, *, safe_path_flag):
        environment = {key: value for key, value in os.environ.items()
                       if key not in ("PYTHONPATH", "PYTHONSAFEPATH", "PYTHONSTARTUP")}
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [sys.executable, str(HERE / name), *arguments]
        if safe_path_flag:
            command.insert(1, "-P")
        else:
            environment["PYTHONSAFEPATH"] = "1"
        return subprocess.run(command, cwd=root, env=environment, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=300, check=False)

    def test_emitter_writes_a_report_in_safe_path_mode(self):
        expected = unittest.TestLoader().loadTestsFromTestCase(AccrualScaffoldTests).countTestCases()
        for flag in (True, False):
            with self.subTest(safe_path_flag=flag), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                child = self.run_child(root, "emit_wildcat_accrual_report.py",
                                       ["--step", "1", "--report", ".elenchus/2088-step-1.json"],
                                       safe_path_flag=flag)
                self.assertNotIn("ModuleNotFoundError", child.stderr)
                self.assertEqual(child.returncode, 0, child.stderr[-2000:])
                payload = json.loads((root / ".elenchus/2088-step-1.json").read_bytes())
                self.assertEqual(set(payload), UNITTEST_V1_KEYS)
                self.assertEqual((payload["testsRun"], payload["failures"], payload["errors"],
                                  payload["skipped"]), (expected, 0, 0, 0))

    def test_prover_reaches_its_conformance_refusal_in_safe_path_mode(self):
        for flag in (True, False):
            with self.subTest(safe_path_flag=flag), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                child = self.run_child(root, "prove_wildcat_accrual.py",
                                       ["--candidate", "abi-named-amounts", "--criterion", "schema-parity",
                                        "--report", ".hexaemeron/r.json"], safe_path_flag=flag)
                self.assertEqual(child.returncode, 2, child.stderr[-2000:])
                self.assertEqual(child.stderr,
                                 "conformance unavailable: EvidenceUnavailable: criterion implementation absent\n")
                self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
