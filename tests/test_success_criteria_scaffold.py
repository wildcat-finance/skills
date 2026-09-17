"""Exercise the published Step 1 joins, replay, refusals and report custody."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "docs/protasis-success-criteria"
SPEC = importlib.util.spec_from_file_location("success_criteria_proof", ROOT / PACKAGE / "proof.py")
PROOF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROOF
SPEC.loader.exec_module(PROOF)


class SuccessCriteriaScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix="criteria-scaffold-test-")
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        bridge = PROOF.load_module(ROOT / PROOF.BRIDGE_CHECKER, "scaffold_fixture_bridge")
        home, home_path, error = bridge._read_stable_adr(ROOT, PROOF.SELECTOR)
        self.assertIsNotNone(home, error)
        self.decision = home_path.as_posix()
        files = [".python-version", PROOF.SELF, PROOF.DESIGN_CHECKER,
                 PROOF.BRIDGE_CHECKER, self.decision]
        files += [
            "plugins/hexaemeron/skills/protasis/scripts/success_criteria.py",
            "plugins/hexaemeron/skills/protasis/scripts/protasis.py",
            "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py",
        ]
        gate = PROOF.load_module(
            ROOT / "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py",
            "scaffold_fixture_gate_commands",
        )
        files += list(gate.REGISTRY)
        files += [PACKAGE + "/" + name for name in PROOF.FROZEN]
        design = json.loads((ROOT / PACKAGE / "design-evidence.json").read_bytes())
        files += [PACKAGE + "/" + row["report"]["path"] for row in design["results"]
                  if isinstance(row["report"], dict)]
        for relative in files:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        self.report = ".hexaemeron/reports/design-home.json"
        self.output = self.root / self.report
        self.evidence = self.output.with_suffix(".evidence.json")

    def run_proof(self, candidate="controller-capture", criterion="design-home"):
        return PROOF.run(self.root, candidate, criterion, self.report)

    def assert_no_reports(self):
        self.assertFalse(self.output.exists())
        self.assertFalse(self.evidence.exists())

    def test_actual_bridge_selection_and_specimens_are_bound_to_report(self):
        report = self.run_proof()
        self.assertEqual(set(report), {"schema", "candidate", "criterion", "value",
                                      "unit", "command", "exit"})
        self.assertIs(report["value"], True)
        evidence = json.loads(self.evidence.read_bytes())
        self.assertEqual(evidence["report"]["sha256"],
                         hashlib.sha256(self.output.read_bytes()).hexdigest())
        checks = {row["name"]: row for row in evidence["checks"]}
        self.assertEqual(checks["hypomnema-design-bridge"]["record"], self.decision)
        self.assertEqual(checks["protasis-design-selection"]["selected"], "controller-capture")
        self.assertEqual(len(checks["protasis-design-selection"]["consumed"]), 18)
        observed = {(row["candidate"], row["criterion"]): row["value"]
                    for row in checks["policy-specimen-replay"]["observations"]}
        self.assertEqual(len(observed), 18)
        self.assertEqual(observed[("controller-capture", "settlement-invocations")], 1)
        self.assertEqual(observed[("terminal-replay", "settlement-invocations")], 3)
        self.assertIs(observed[("producer-report", "unexecuted-result-refused")], False)
        self.assertEqual(observed[("controller-capture", "sample-record-bytes")], 345)
        for source in evidence["sources"]:
            data = (self.root / source["path"]).read_bytes()
            self.assertEqual(source["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(source["bytes"], len(data))
        self.assertIn(PROOF.SELF, {row["path"] for row in evidence["sources"]})

    def test_earned_report_satisfies_the_due_design_home_cell(self):
        checker = PROOF.load_module(self.root / PROOF.DESIGN_CHECKER, "scaffold_design_before")
        path = self.root / PACKAGE / "design-evidence.json"
        self.assertTrue(checker.evaluate(path, "step:2")[0])
        self.run_proof()
        destination = self.root / PACKAGE / "reports/controller-capture-design-home.json"
        shutil.copyfile(self.output, destination)
        findings, _, consumed = checker.evaluate(path, "step:2")
        self.assertEqual(findings, [])
        self.assertIn("design-home", {row["criterion"] for row in consumed})

    def test_frozen_selection_reports_keep_all_eighteen_original_digests(self):
        record = json.loads((self.root / PACKAGE / "design-evidence.json").read_bytes())
        reports = [row["report"] for row in record["results"] if isinstance(row["report"], dict)]
        self.assertEqual(len(reports), 18)
        for row in reports:
            self.assertEqual(hashlib.sha256((self.root / PACKAGE / row["path"]).read_bytes()).hexdigest(),
                             row["sha256"])

    def test_opening_study_is_the_bound_prefix_of_the_current_accepted_study(self):
        opening = (self.root / PACKAGE / "evidence/opening-study.md").read_bytes()
        current = (self.root / PACKAGE / "study.md").read_bytes()
        self.assertEqual(hashlib.sha256(opening).hexdigest(),
                         "4a572737afa69d9a24c5923a828b68398c3e1bb9d85045b1488d7b8a87e13e92")
        self.assertEqual(hashlib.sha256(current).hexdigest(),
                         "2ff25685ea7e4f0c00b27f529ce901886156d46a5582ab7987c126105c64f3d4")
        self.assertTrue(current.startswith(opening))
        self.assertIn(b"operating boundaries", current[len(opening):])

    def test_prepared_status_spelling_is_rejected_by_the_actual_bridge(self):
        draft = self.root / self.decision
        published = draft.read_bytes()
        old = b"Accepted for the #1273 study, 2026-09-16."
        new = b"Accepted, 2026-09-16, for the #1273 study."
        self.assertEqual(published.count(new), 1)
        draft.write_bytes(published.replace(new, old))
        with self.assertRaisesRegex(PROOF.Refusal, "design-home-join-refused:H008"):
            self.run_proof()
        self.assert_no_reports()

    def test_missing_decision_home_refuses_without_report(self):
        (self.root / self.decision).unlink()
        with self.assertRaisesRegex(PROOF.Refusal, "design-home-join-refused:H008"):
            self.run_proof()
        self.assert_no_reports()

    def test_duplicate_draft_and_numbered_home_refuse(self):
        home = self.root / self.decision
        if self.decision == PROOF.DRAFT:
            duplicate = self.root / "docs/decisions" / ("ADR-999-" + PROOF.SLUG + ".md")
            content = home.read_bytes().replace(b"# Decision: ", b"# ADR-999: ", 1)
        else:
            duplicate = self.root / PROOF.DRAFT
            content = re.sub(rb"\A# ADR-[0-9]{3}: ", b"# Decision: ", home.read_bytes(), count=1)
        duplicate.parent.mkdir(parents=True, exist_ok=True)
        duplicate.write_bytes(content)
        with self.assertRaisesRegex(PROOF.Refusal, "design-home-join-refused:H008"):
            self.run_proof()
        self.assert_no_reports()

    def test_stable_home_survives_only_the_number_assignment_transform(self):
        draft = self.root / self.decision
        numbered = self.root / "docs/decisions" / ("ADR-999-" + PROOF.SLUG + ".md")
        content = re.sub(rb"\A# (?:Decision|ADR-[0-9]{3}): ", b"# ADR-999: ", draft.read_bytes(), count=1)
        draft.unlink()
        numbered.write_bytes(content)
        self.assertIs(self.run_proof()["value"], True)
        evidence = json.loads(self.evidence.read_bytes())
        self.assertEqual(evidence["checks"][0]["record"], numbered.relative_to(self.root).as_posix())

    def test_shape_valid_decision_content_drift_refuses(self):
        draft = self.root / self.decision
        draft.write_bytes(draft.read_bytes().replace(b"128 criteria", b"129 criteria"))
        with self.assertRaisesRegex(PROOF.Refusal, "decision-content-drift"):
            self.run_proof()
        self.assert_no_reports()

    def test_fixture_reads_the_actual_numbered_home_after_assignment(self):
        draft = self.root / PROOF.DRAFT
        numbered = self.root / "docs/decisions" / ("ADR-999-" + PROOF.SLUG + ".md")
        if draft.exists():
            numbered.write_bytes(draft.read_bytes().replace(b"# Decision: ", b"# ADR-999: ", 1))
            draft.unlink()
        nested = type(self)("test_actual_bridge_selection_and_specimens_are_bound_to_report")
        self.addCleanup(nested.doCleanups)
        with mock.patch.object(sys.modules[__name__], "ROOT", self.root):
            nested.setUp()
        self.assertFalse((nested.root / PROOF.DRAFT).exists())
        nested.test_actual_bridge_selection_and_specimens_are_bound_to_report()

    def test_changed_selection_report_refuses(self):
        path = self.root / PACKAGE / "reports/controller-capture-settlement-invocations.json"
        record = json.loads(path.read_bytes())
        record["value"] = 0
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(PROOF.Refusal, "selection-check-refused:D005"):
            self.run_proof()
        self.assert_no_reports()

    def test_missing_selection_report_refuses(self):
        (self.root / PACKAGE / "reports/producer-report-unexecuted-result-refused.json").unlink()
        with self.assertRaisesRegex(PROOF.Refusal, "selection-check-refused:D005"):
            self.run_proof()
        self.assert_no_reports()

    def test_rewritten_selected_design_cannot_rebind_frozen_evidence(self):
        path = self.root / PACKAGE / "design-evidence.json"
        record = json.loads(path.read_bytes())
        record["selection"]["candidate"] = "terminal-replay"
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(PROOF.Refusal, "source-digest-mismatch"):
            self.run_proof()
        self.assert_no_reports()

    def test_later_operations_refuse_by_name_before_writing(self):
        for criterion, step in PROOF.FUTURE.items():
            if criterion == "declaration-contract":
                continue
            with self.subTest(criterion=criterion):
                with self.assertRaisesRegex(PROOF.Refusal, "operation-not-implemented:" + criterion + ":step-" + str(step)):
                    self.run_proof(criterion=criterion)
                self.assert_no_reports()

    def test_declaration_contract_report_is_bound_to_the_actual_adapter(self):
        report_path = ".hexaemeron/reports/controller-capture-declaration-contract.json"
        report = PROOF.run(self.root, "controller-capture", "declaration-contract", report_path)
        self.assertEqual(set(report), {"schema", "candidate", "criterion", "value",
                                       "unit", "command", "exit"})
        self.assertEqual(report["schema"], "protasis-design-report/v1")
        self.assertIs(report["value"], True)
        evidence = json.loads((self.root / (report_path[:-5] + ".evidence.json")).read_bytes())
        self.assertEqual(evidence["schema"], "success-criteria-declaration-evidence/v1")
        checks = {row["case"]: row for row in evidence["checks"]}
        self.assertEqual(checks["adapter-admission"]["criteria"], 8)
        self.assertFalse(checks["adapter-admission"]["operation_ran"])
        self.assertIn("superseded-exit", checks)

    def test_execution_custody_report_uses_real_child_observations(self):
        executor = ROOT / "plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py"
        controller = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
        for source in (executor, controller):
            relative = source.relative_to(ROOT)
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        report_path = ".hexaemeron/reports/controller-capture-execution-custody.json"
        report = PROOF.run(self.root, "controller-capture", "execution-custody", report_path)
        self.assertTrue(report["value"])
        evidence = json.loads((self.root / (report_path[:-5] + ".evidence.json")).read_bytes())
        self.assertEqual(evidence["schema"], "success-criteria-execution-evidence/v1")
        self.assertEqual({row["case"] for row in evidence["checks"]}, {
            "completed-zero", "completed-exit-seven", "incremental-stream-overflow",
        })
        self.assertEqual(evidence["controller"]["path"],
                         "plugins/hexaemeron/skills/fiat/scripts/hexctl.py")
        self.assertGreater(evidence["controller"]["bytes"], 1_000_000)

    def test_losing_candidates_do_not_receive_conformance_reports(self):
        for candidate in ("producer-report", "terminal-replay"):
            with self.subTest(candidate=candidate):
                with self.assertRaisesRegex(PROOF.Refusal, "candidate-not-selected"):
                    self.run_proof(candidate=candidate)
                self.assert_no_reports()

    def test_existing_report_is_preserved_without_reexecuting_specimens(self):
        self.output.parent.mkdir(parents=True)
        self.output.write_bytes(b"previous report\n")
        with mock.patch.object(PROOF, "check_design_home") as check:
            with self.assertRaisesRegex(PROOF.Refusal, "report-already-exists"):
                self.run_proof()
            check.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"previous report\n")
        self.assertFalse(self.evidence.exists())

    def test_existing_companion_is_preserved_without_a_new_report(self):
        self.evidence.parent.mkdir(parents=True)
        self.evidence.write_bytes(b"previous evidence\n")
        with self.assertRaisesRegex(PROOF.Refusal, "report-already-exists"):
            self.run_proof()
        self.assertFalse(self.output.exists())
        self.assertEqual(self.evidence.read_bytes(), b"previous evidence\n")

    def test_linked_report_cannot_overwrite_its_target(self):
        target = self.root / "keep.json"
        target.write_bytes(b"keep\n")
        self.output.parent.mkdir(parents=True)
        self.output.symlink_to(target)
        with self.assertRaisesRegex(PROOF.Refusal, "report-already-exists"):
            self.run_proof()
        self.assertEqual(target.read_bytes(), b"keep\n")
        self.assertFalse(self.evidence.exists())

    def test_linked_input_is_not_followed(self):
        study = self.root / PACKAGE / "study.md"
        target = self.root / "study.md"
        study.rename(target)
        study.symlink_to(target)
        with self.assertRaises(OSError):
            self.run_proof()
        self.assert_no_reports()

    def test_special_input_is_refused_without_blocking(self):
        study = self.root / PACKAGE / "study.md"
        study.unlink()
        os.mkfifo(study)
        with self.assertRaisesRegex(PROOF.Refusal, "input-not-bounded-regular-file"):
            self.run_proof()
        self.assert_no_reports()

    def test_oversized_input_refuses(self):
        (self.root / PACKAGE / "study.md").write_bytes(b"x" * (1024 * 1024 + 1))
        with self.assertRaisesRegex(PROOF.Refusal, "input-not-bounded-regular-file"):
            self.run_proof()
        self.assert_no_reports()

    def test_report_path_cannot_escape_or_select_another_directory(self):
        for path in ("/tmp/criteria.json", "../criteria.json", ".hexaemeron/reports/../criteria.json",
                     "docs/criteria.json", ".hexaemeron/reports/more/criteria.json"):
            with self.subTest(path=path):
                with self.assertRaises(PROOF.Refusal):
                    PROOF.run(self.root, "controller-capture", "design-home", path)
                self.assert_no_reports()

    def test_drift_between_checks_and_publication_prevents_a_report(self):
        check = PROOF.check_design_home

        def change_after_check(root):
            result = check(root)
            path = root / PACKAGE / "study.md"
            path.write_bytes(path.read_bytes() + b"changed\n")
            return result

        with mock.patch.object(PROOF, "check_design_home", side_effect=change_after_check):
            with self.assertRaisesRegex(PROOF.Refusal, "source-changed"):
                self.run_proof()
        self.assert_no_reports()

    def test_cli_emits_the_closed_report_after_actual_checks(self):
        result = subprocess.run([sys.executable, str(self.root / PROOF.SELF),
                                 "--candidate", "controller-capture", "--criterion", "design-home",
                                 "--report", self.report], cwd=self.root, capture_output=True,
                                text=True, timeout=30, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), json.loads(self.output.read_bytes()))
        self.assertIn(" --criterion design-home --report " + self.report,
                      json.loads(result.stdout)["command"])

    def test_cli_unavailable_operation_has_a_bounded_named_reason(self):
        result = subprocess.run([sys.executable, str(self.root / PROOF.SELF),
                                 "--candidate", "controller-capture", "--criterion", "execution-custody",
                                 "--report", self.report], cwd=self.root, capture_output=True,
                                text=True, timeout=10, env={"PATH": "/usr/bin:/bin"})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["reason"],
                         "operation-not-implemented:execution-custody:step-3")
        self.assertEqual(result.stderr, "")
        self.assert_no_reports()


if __name__ == "__main__":
    unittest.main()
