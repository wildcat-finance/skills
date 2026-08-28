"""Rendering: fixed templates, findings-only content, refused strengthening."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from tests import support


class RenderCase(unittest.TestCase):
    def setUp(self):
        self._scratch = tempfile.TemporaryDirectory()
        self.root = Path(self._scratch.name).resolve()
        self.addCleanup(self._scratch.cleanup)
        self.synkrisis = support.synkrisis()

    def refusal(self, code, callable_, *args, **kwargs):
        with self.assertRaises(self.synkrisis.Refusal) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        return caught.exception

    def stage_findings(self, mutate=None):
        support.copy_example_into(self.root)
        support.run_cohort(self.root)
        support.run_diagnose(self.root)
        if mutate is not None:
            findings = support.read_json(self.root / "out/findings.json")
            mutate(findings)
            (self.root / "out/findings.json").unlink()
            support.write(
                self.root, "out/findings.json", support.canonical(findings)
            )


class RenderTests(RenderCase):
    def test_example_report_recomputes_byte_identically(self):
        scratch = f"build/synkrisis-render-test-{os.getpid()}"
        out = f"{scratch}/report.md"
        self.addCleanup(support.clean_tree, support.REPO_ROOT / scratch)
        support.run_render(
            support.REPO_ROOT,
            findings="plugins/synkrisis/examples/cross-run-v0/expected/findings.json",
            out=out,
        )
        expected = (support.EXAMPLE / "expected" / "report.md").read_bytes()
        self.assertEqual((support.REPO_ROOT / out).read_bytes(), expected)

    def test_report_carries_only_findings_content(self):
        self.stage_findings()
        support.run_render(self.root)
        report = (self.root / "out/report.md").read_text(encoding="utf-8")
        self.assertIn("late-boundary-consultation/v1", report)
        self.assertIn("run-gamma (evt-4, evt-7, evt-10)", report)
        self.assertNotIn("run-delta", report)

    def test_report_narrative_stays_inside_the_allowlist(self):
        self.stage_findings()
        support.run_render(self.root)
        report = (self.root / "out/report.md").read_text(encoding="utf-8").lower()
        for phrase in ("caused", "because", "model quality", "smarter"):
            self.assertNotIn(phrase, report)

    def test_causal_strengthening_in_findings_is_refused(self):
        def mutate(findings):
            findings["findings"][0]["observed_relation"] = (
                "The late consultation caused the higher token use."
            )

        self.stage_findings(mutate)
        self.refusal("SK014", support.run_render, self.root)

    def test_evidence_class_strengthening_in_findings_is_refused(self):
        def mutate(findings):
            findings["findings"][0]["evidence_class"] = "measured"

        self.stage_findings(mutate)
        self.refusal("SK014", support.run_render, self.root)

    def test_unknown_finding_field_is_refused(self):
        def mutate(findings):
            findings["findings"][0]["issue_url"] = "https://github.com/example/1"

        self.stage_findings(mutate)
        self.refusal("SK014", support.run_render, self.root)

    def test_unsupported_findings_schema_is_refused(self):
        def mutate(findings):
            findings["schema"] = "synkrisis-findings/v2"

        self.stage_findings(mutate)
        self.refusal("SK014", support.run_render, self.root)

    def test_render_refuses_a_different_existing_report(self):
        self.stage_findings()
        support.write(self.root, "out/report.md", b"# stale\n")
        self.refusal("SK013", support.run_render, self.root)

    def test_render_reruns_cleanly_over_its_own_output(self):
        self.stage_findings()
        first = support.run_render(self.root)
        second = support.run_render(self.root)
        self.assertEqual(first["report_sha256"], second["report_sha256"])

    def test_empty_findings_render_names_the_absence(self):
        def mutate(findings):
            findings["findings"] = []

        self.stage_findings(mutate)
        support.run_render(self.root)
        report = (self.root / "out/report.md").read_text(encoding="utf-8")
        self.assertIn("No shipped rule matched the checked cohort.", report)


if __name__ == "__main__":
    unittest.main()
