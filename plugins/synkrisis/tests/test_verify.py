"""Verification: every artefact recomputes from the original inputs, or refuses."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests import support


class VerifyCase(unittest.TestCase):
    def setUp(self):
        self._scratch = tempfile.TemporaryDirectory()
        self.root = Path(self._scratch.name).resolve()
        self.addCleanup(self._scratch.cleanup)
        self.synkrisis = support.synkrisis()
        support.copy_example_into(self.root)
        support.run_cohort(self.root)
        support.run_diagnose(self.root)
        support.run_render(self.root)

    def refusal(self, code, **overrides):
        with self.assertRaises(self.synkrisis.Refusal) as caught:
            support.run_verify(self.root, **overrides)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        return caught.exception

    def rewrite(self, relative, payload: bytes):
        target = self.root / relative
        target.unlink()
        support.write(self.root, relative, payload)


class VerifyTests(VerifyCase):
    def test_full_example_verifies(self):
        result = support.run_verify(self.root)
        self.assertEqual(result["status"], "verified")
        cohort = support.read_json(self.root / "out/cohort.json")
        self.assertEqual(result["cohort_digest"], cohort["cohort_digest"])

    def test_verify_is_idempotent_and_writes_nothing(self):
        before = sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        )
        support.run_verify(self.root)
        support.run_verify(self.root)
        after = sorted(
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_file()
        )
        self.assertEqual(before, after)

    def test_replaced_cohort_bytes_are_refused(self):
        cohort = support.read_json(self.root / "out/cohort.json")
        cohort["included"] = cohort["included"][:-1]
        self.rewrite("out/cohort.json", support.canonical(cohort))
        self.refusal("SK012")

    def test_truncated_findings_are_refused(self):
        payload = (self.root / "out/findings.json").read_bytes()
        self.rewrite("out/findings.json", payload[: len(payload) // 2])
        self.refusal("SK012")

    def test_wrong_run_association_is_refused(self):
        payload = (self.root / "out/findings.json").read_bytes()
        self.rewrite(
            "out/findings.json", payload.replace(b"run-gamma", b"run-alpha")
        )
        self.refusal("SK012")

    def test_stale_rule_digest_is_refused(self):
        rules = support.read_json(self.root / "rules.json")
        rules["rules"][0]["parameters"]["late_fraction"] = {
            "numerator": 1,
            "denominator": 3,
        }
        self.rewrite("rules.json", support.canonical(rules))
        self.refusal("SK012")

    def test_unsupported_producer_version_is_refused(self):
        manifest = support.read_json(self.root / "manifest.json")
        manifest["producer_contract"] = "promise-machine-run-observation/v2"
        self.rewrite("manifest.json", support.canonical(manifest))
        self.refusal("SK008")

    def test_edited_report_narrative_is_refused(self):
        payload = (self.root / "out/report.md").read_bytes()
        self.rewrite(
            "out/report.md",
            payload.replace(b"Observed relation:", b"Proven relation:"),
        )
        self.refusal("SK012")

    def test_reordered_record_events_are_refused(self):
        target = self.root / "records" / "run-alpha.jsonl"
        lines = target.read_bytes().split(b"\n")[:-1]
        reordered = b"\n".join([lines[0], lines[2], lines[1], *lines[3:]]) + b"\n"
        target.write_bytes(reordered)
        self.refusal("SK007")

    def test_symlinked_report_is_refused(self):
        (self.root / "out/report-link.md").symlink_to(self.root / "out/report.md")
        self.refusal("SK001", report="out/report-link.md")

    def test_missing_report_is_refused(self):
        os.unlink(self.root / "out/report.md")
        self.refusal("SK001")

    def test_verify_result_carries_digests_and_no_action(self):
        """The nearest overclaim: verification blessing the suggested handoff."""
        result = support.run_verify(self.root)
        self.assertEqual(
            sorted(result),
            [
                "cohort_digest",
                "command",
                "manifest_digest",
                "policy_digest",
                "report_sha256",
                "rules_digest",
                "status",
            ],
        )
        self.assertNotIn("handoff", result)

    def test_verify_recovers_after_artifact_restoration(self):
        payload = (self.root / "out/findings.json").read_bytes()
        self.rewrite(
            "out/findings.json", payload.replace(b"run-gamma", b"run-alpha")
        )
        self.refusal("SK012")
        self.rewrite("out/findings.json", payload)
        result = support.run_verify(self.root)
        self.assertEqual(result["status"], "verified")


if __name__ == "__main__":
    unittest.main()
