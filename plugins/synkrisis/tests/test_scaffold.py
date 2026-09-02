"""Step 5 scaffold contract: manifests, marketplace, router, ledger, promises, examples."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest

from tests import support

sys.path.insert(0, str(support.REPO_ROOT))
from repo_contract import (  # noqa: E402  (repository-root shared assertions)
    assert_host_descriptions_agree,
    assert_marketplace_source_path,
    assert_router_reaches,
    assert_version_agreement,
)

PLUGIN = support.PLUGIN_ROOT
SKILL = PLUGIN / "skills" / "synkrisis" / "SKILL.md"
LEDGER = PLUGIN / "skills" / "synkrisis" / "EVOLUTION.md"


class HostSurfaceTests(unittest.TestCase):
    def test_manifest_versions_agree_across_hosts_and_marketplace(self):
        assert_version_agreement(self, "synkrisis", expected="0.5.1")

    def test_host_descriptions_agree(self):
        assert_host_descriptions_agree(self, "synkrisis")

    def test_router_reaches_the_runtime_contract(self):
        assert_router_reaches(self, "synkrisis")

    def test_marketplace_source_paths_are_local(self):
        assert_marketplace_source_path(self, "synkrisis")

    def test_canonical_skill_names_its_parent_directory(self):
        text = SKILL.read_text(encoding="utf-8")
        match = re.search(r"(?m)^name:\s*(\S+)$", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "synkrisis")

    def test_skill_metadata_version_matches_the_ledger(self):
        text = SKILL.read_text(encoding="utf-8")
        metadata = re.search(r'(?m)^  version: "(\d+\.\d+\.\d+)"$', text)
        self.assertIsNotNone(metadata)
        ledger = LEDGER.read_text(encoding="utf-8")
        self.assertIn(f"- Current version: `synkrisis-v{metadata.group(1)}`", ledger)

    def test_promise_machine_copy_is_byte_identical_to_the_root_law(self):
        self.assertEqual(
            (PLUGIN / "PROMISE_MACHINE.md").read_bytes(),
            (support.REPO_ROOT / "PROMISE_MACHINE.md").read_bytes(),
        )

    def test_licence_is_byte_identical_to_the_root_licence(self):
        self.assertEqual(
            (PLUGIN / "LICENSE").read_bytes(),
            (support.REPO_ROOT / "LICENSE").read_bytes(),
        )

    def test_package_and_skill_versions_are_independently_declared(self):
        package = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
        ledger = LEDGER.read_text(encoding="utf-8")
        skill = re.search(r"- Current version: `synkrisis-v(\d+\.\d+\.\d+)`", ledger)
        self.assertRegex(package, r"^\d+\.\d+\.\d+$")
        self.assertIsNotNone(skill)

    def test_contract_section_declares_exactly_the_three_promises(self):
        text = SKILL.read_text(encoding="utf-8")
        contract = text.split("## Promise Machine contract", 1)[1]
        declared = {
            line.removeprefix("### ")
            for line in contract.splitlines()
            if line.startswith("### ")
        }
        self.assertEqual(
            declared,
            {
                "synkrisis-cohort-construction",
                "synkrisis-bounded-diagnosis",
                "synkrisis-report-verification",
            },
        )


class SpecificationTests(unittest.TestCase):
    def test_specification_and_decision_records_are_committed(self):
        for path in (
            support.REPO_ROOT / "docs" / "synkrisis" / "study.md",
            support.REPO_ROOT / "docs" / "synkrisis" / "runbook.md",
            PLUGIN / "docs" / "decisions"
            / "ADR-001-keep-cross-run-diagnosis-separate.md",
            PLUGIN / "docs" / "decisions"
            / "ADR-002-declare-cohort-comparability.md",
            PLUGIN / "docs" / "decisions"
            / "ADR-003-use-checked-diagnostic-rules.md",
            PLUGIN / "docs" / "decisions"
            / "ADR-004-separate-run-and-reachability-evidence.md",
            PLUGIN / "docs" / "schema-compatibility.md",
        ):
            with self.subTest(path=path.relative_to(support.REPO_ROOT)):
                self.assertTrue(path.is_file())

    def test_the_skill_links_resolve_to_the_committed_specification(self):
        text = SKILL.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(((?:\.\./)+[^)]+)\)", text):
            with self.subTest(link=link):
                self.assertTrue((SKILL.parent / link).resolve().is_file())

    def test_the_runbook_records_every_step_delivered_and_none_held(self):
        """The runbook is complete, and this is the check that says so.

        Counting the held markers rather than only the delivered ones keeps a
        step that was flipped in one place and not the other from passing: a
        heading left at `(held)` fails here even though five delivered
        markers would be present elsewhere.
        """
        runbook = (support.REPO_ROOT / "docs" / "synkrisis" / "runbook.md").read_text(
            encoding="utf-8"
        )
        for heading in ("Step 1", "Step 2", "Step 3", "Step 4", "Step 5"):
            self.assertIn(f"## {heading}:", runbook)
        self.assertEqual(runbook.count("(delivered)"), 5)
        self.assertEqual(runbook.count("(held)"), 0)


class CommandSurfaceTests(unittest.TestCase):
    def run_cli(self, *arguments, cwd=None):
        return subprocess.run(  # phylax: allow subprocess: fixed argv local script, no shell
            [sys.executable, str(support.SCRIPTS / "synkrisis.py"), *arguments],
            capture_output=True,
            text=True,
            cwd=cwd or support.REPO_ROOT,
        )

    def test_cli_help_runs_without_writing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as scratch:
            completed = self.run_cli("--help", cwd=scratch)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for command in ("cohort", "diagnose", "render", "verify"):
                self.assertIn(command, completed.stdout)
            self.assertEqual(os.listdir(scratch), [])

    def test_bench_help_runs(self):
        completed = subprocess.run(  # phylax: allow subprocess: fixed argv local script, no shell
            [sys.executable, str(support.SCRIPTS / "bench_synkrisis.py"), "--help"],
            capture_output=True,
            text=True,
            cwd=support.REPO_ROOT,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--max-rss-mib", completed.stdout)

    def test_refusal_output_names_code_producer_path_and_recovery(self):
        completed = self.run_cli(
            "cohort",
            "--manifest",
            "absent.json",
            "--policy",
            "absent.json",
            "--out",
            "out/cohort.json",
            "--json",
            cwd=str(support.REPO_ROOT / "plugins" / "synkrisis"),
        )
        self.assertEqual(completed.returncode, 1)
        document = json.loads(completed.stdout)
        self.assertEqual(
            sorted(document),
            ["code", "fault", "message", "path", "producer", "recovery"],
        )
        self.assertEqual(document["producer"], "promise-machine-run-observation/v1")


class ReferenceSurfaceTests(unittest.TestCase):
    def test_reference_schemas_parse_and_declare_their_identities(self):
        expected = {
            "policy-v1.schema.json": "synkrisis-policy/v1",
            "cohort-v1.schema.json": "synkrisis-cohort/v1",
            "rule-v1.schema.json": "synkrisis-rules/v1",
            "findings-v1.schema.json": "synkrisis-findings/v1",
        }
        for name, identity in expected.items():
            with self.subTest(schema=name):
                document = support.read_json(PLUGIN / "references" / name)
                self.assertEqual(
                    document["properties"]["schema"]["const"], identity
                )

    def test_rule_catalogue_loads_under_the_shipped_validator(self):
        synkrisis = support.synkrisis()
        budget = synkrisis.InputBudget()
        document, _ = synkrisis.load_rules(
            support.REPO_ROOT, "plugins/synkrisis/references/rules-v1.json", budget
        )
        self.assertEqual(
            [rule["rule_id"] for rule in document["rules"]],
            ["late-boundary-consultation/v1", "unchanged-retry-before-handoff/v1"],
        )

    def test_example_records_pass_the_producer_validator(self):
        for record in sorted((support.EXAMPLE / "records").glob("*.jsonl")):
            with self.subTest(record=record.name):
                completed = subprocess.run(  # phylax: allow subprocess: fixed argv local checker, no shell
                    [
                        sys.executable,
                        str(support.REPO_ROOT / "scripts" / "run_observation.py"),
                        "check",
                        str(record.relative_to(support.REPO_ROOT)),
                    ],
                    capture_output=True,
                    text=True,
                    cwd=support.REPO_ROOT,
                )
                self.assertEqual(
                    completed.returncode, 0, completed.stdout + completed.stderr
                )

    def test_committed_example_artefacts_verify_from_their_inputs(self):
        result = support.run_verify(
            support.REPO_ROOT,
            manifest="plugins/synkrisis/examples/cross-run-v0/manifest.json",
            policy="plugins/synkrisis/examples/cross-run-v0/policy.json",
            cohort="plugins/synkrisis/examples/cross-run-v0/expected/cohort.json",
            rules="plugins/synkrisis/references/rules-v1.json",
            findings="plugins/synkrisis/examples/cross-run-v0/expected/findings.json",
            report="plugins/synkrisis/examples/cross-run-v0/expected/report.md",
        )
        self.assertEqual(result["status"], "verified")


if __name__ == "__main__":
    unittest.main()
