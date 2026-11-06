"""Exercise the source-bound successor-controller demonstration."""

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
PROOF_PATH = ROOT / "docs" / "protasis-success-criteria" / "proof.py"


def load_proof(path: Path):
    spec = importlib.util.spec_from_file_location(
        "fiat_criteria_demonstration_proof", path
    )
    if spec is None or spec.loader is None:
        raise AssertionError("joined demonstration proof is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FiatCriteriaDemonstrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run the published proof once from a clean clone."""
        with tempfile.TemporaryDirectory(prefix="fiat-criteria-demo-test-") as name:
            fixture = Path(name) / "fixture"
            cloned = subprocess.run(
                ["git", "clone", "--shared", "--no-tags", str(ROOT), str(fixture)],
                cwd=ROOT,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if cloned.returncode != 0:
                raise AssertionError(cloned.stderr)
            proof = load_proof(fixture / "docs" / "protasis-success-criteria" / "proof.py")
            report_path = ".hexaemeron/reports/controller-capture-joined-demonstration.json"
            report = proof.run(fixture, "controller-capture", "joined-demonstration", report_path)
            if not report["value"]:
                raise AssertionError("joined demonstration did not pass")
            report_file = fixture / report_path
            evidence_file = report_file.with_name(
                report_file.name[:-5] + ".evidence.json"
            )
            evidence = json.loads(evidence_file.read_bytes())
            if evidence["schema"] != "success-criteria-joined-demonstration-evidence/v1":
                raise AssertionError("unexpected joined demonstration schema")
            if evidence["report"]["sha256"] != hashlib.sha256(report_file.read_bytes()).hexdigest():
                raise AssertionError("report digest is not source-bound")
            cls.evidence = evidence

    def test_joined_positive_result_is_source_bound(self):
        evidence = self.evidence
        self.assertEqual(evidence["controller"]["path"],
                         "plugins/hexaemeron/skills/fiat/scripts/hexctl.py")
        self.assertTrue(evidence["controller"]["sha256"])
        self.assertEqual(evidence["actual_counts"]["execution_invocations"], 1)

    def test_joined_refusals_preserve_the_declared_boundary(self):
        checks = {case["case"] for case in self.evidence["checks"]}
        self.assertTrue({"wrong-step", "wrong-command", "wrong-source"}.issubset(checks))
        self.assertTrue({"nonzero-exit", "timeout", "stream-overflow", "interrupted"}.issubset(checks))

    def test_joined_vacuous_result_keeps_semantic_sufficiency_unclaimed(self):
        vacuous = next(
            case for case in self.evidence["checks"] if case["case"] == "vacuous-success"
        )
        self.assertFalse(vacuous["semantic_sufficiency"])

    def test_joined_terminal_replay_launches_no_inspection_operation(self):
        self.assertEqual(self.evidence["terminal"]["operation_ran"], False)
        self.assertEqual(self.evidence["inspection_launches"], 0)

    def test_joined_shared_descriptors_settle_once(self):
        shared = next(
            case for case in self.evidence["checks"] if case["case"] == "shared-descriptors"
        )
        self.assertEqual(
            shared["criterion_ids"], ["demo-positive", "demo-shared", "demo-vacuous"]
        )


if __name__ == "__main__":
    unittest.main()
