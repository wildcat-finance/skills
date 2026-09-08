"""Recovery and final-green guards for issue 453 Step 4."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

try:
    from .test_hexctl import hexctl_module
except ImportError:
    from test_hexctl import hexctl_module


FIXTURE_ROOT = Path(__file__).parent / "fixtures/issue-453"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def canonical_report(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")


class RecoveryTests(unittest.TestCase):
    """kf-453-06: resume parity and the bound explicit-emptiness claim."""

    def test_kf_453_06_resume_preserves_remaining_and_no_findings(self):
        fixture = load_fixture("recovery.json")
        controller = hexctl_module()
        validate = getattr(controller, "validate_known_failure_recovery", None)
        self.assertTrue(
            callable(validate),
            "Fiat cannot reconstruct its known-failure recovery projection",
        )

        self.assertEqual(
            fixture["projection_schema"],
            getattr(controller, "RECOVERY_PROJECTION_SCHEMA", None),
        )
        self.assertEqual(
            set(fixture["suite_checks"]),
            set(getattr(controller, "FINAL_GREEN_SUITE_CHECKS", ())),
        )

        for row in fixture["accepted"]:
            with self.subTest(accepted=row["id"]):
                document = row["document"]
                checked = validate(document, capture=fixture["capture"])
                self.assertEqual(document, checked)
                self.assertEqual(fixture["projection_fields"], sorted(checked))
                self.assertEqual(
                    fixture["final_green_fields"],
                    sorted(checked["final_green"]),
                )
                self.assertEqual(
                    sorted(
                        set(checked["assigned_ids"]) - set(checked["completed_ids"])
                    ),
                    checked["remaining_ids"],
                )
                claim = checked["no_known_findings"]
                if checked["assigned_ids"]:
                    self.assertIsNone(claim)
                else:
                    self.assertEqual(
                        fixture["no_known_findings_fields"], sorted(claim)
                    )
                    self.assertEqual(
                        fixture["capture"]["inventory_sha256"],
                        claim["inventory_sha256"],
                    )

        for row in fixture["rejected"]:
            with self.subTest(rejected=row["id"]):
                with self.assertRaisesRegex(ValueError, row["error"]):
                    validate(
                        row["document"],
                        capture=row.get("capture") or fixture["capture"],
                    )


class FinalGreenTests(unittest.TestCase):
    """kf-453-07: a red guard commit becomes fixed-tree green or nothing."""

    def test_kf_453_07_red_guard_cannot_finish_without_fixed_tree_green(self):
        fixture = load_fixture("final-green.json")
        controller = hexctl_module()
        admit = getattr(controller, "final_green_admission_counters", None)
        build = getattr(controller, "build_final_green_manifest", None)
        self.assertTrue(
            callable(admit) and callable(build),
            "Fiat admits no fixed-tree final-green evidence for a red guard",
        )

        green = fixture["green"]
        raw_report = canonical_report(green["report"])
        counters = admit(
            fixture["report_format"], raw_report, green["runner_exit"]
        )
        self.assertEqual(green["counters"], counters)
        self.assertEqual(fixture["counter_fields"], sorted(counters))

        for row in fixture["rejected"]:
            with self.subTest(rejected=row["id"]):
                with self.assertRaises(ValueError):
                    admit(
                        fixture["report_format"],
                        canonical_report(row["report"]),
                        row["runner_exit"],
                    )

        inputs = fixture["manifest"]
        retained_report = {
            "path": inputs["retained_report_path"],
            "bytes": len(raw_report),
            "sha256": hashlib.sha256(raw_report).hexdigest(),
        }
        manifest = build(
            finding_id=inputs["finding_id"],
            consuming_step=inputs["consuming_step"],
            controller_run_id=inputs["controller_run_id"],
            worktree_identity=inputs["worktree_identity"],
            capture=inputs["capture"],
            final_commit=inputs["final_commit"],
            green_command=inputs["green_command"],
            green_argv=inputs["green_argv"],
            report_format=inputs["report_format"],
            report_file=inputs["report_file"],
            retained_report=retained_report,
            runner_exit=green["runner_exit"],
            counters=counters,
        )
        self.assertEqual(fixture["manifest_schema"], manifest["schema"])
        self.assertEqual(set(fixture["manifest_fields"]), set(manifest))
        self.assertEqual(fixture["admission"], manifest["admission"])
        self.assertEqual(retained_report, manifest["retained_report"])
        self.assertEqual(inputs["final_commit"], manifest["final_commit"])
        self.assertEqual(counters, manifest["counters"])


if __name__ == "__main__":
    unittest.main()
