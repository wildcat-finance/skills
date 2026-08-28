"""Step 1 scaffold contract: packaging, routing, ledger, spec, refusing stub."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "synkrisis" / "SKILL.md"
LEDGER = PLUGIN / "skills" / "synkrisis" / "EVOLUTION.md"
COMMAND = PLUGIN / "scripts" / "synkrisis.py"

sys.path.insert(0, str(REPO_ROOT))
from repo_contract import (  # noqa: E402  (repository-root shared assertions)
    assert_host_descriptions_agree,
    assert_marketplace_source_path,
    assert_router_reaches,
    assert_version_agreement,
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_cli(*arguments, cwd):
    return subprocess.run(  # phylax: allow subprocess: fixed argv local script, no shell
        [sys.executable, str(COMMAND), *arguments],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class HostSurfaceTests(unittest.TestCase):
    def test_manifest_versions_agree_across_hosts_and_marketplace(self):
        assert_version_agreement(self, "synkrisis", expected="0.1.0")

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
            (REPO_ROOT / "PROMISE_MACHINE.md").read_bytes(),
        )

    def test_licence_is_byte_identical_to_the_root_licence(self):
        self.assertEqual(
            (PLUGIN / "LICENSE").read_bytes(),
            (REPO_ROOT / "LICENSE").read_bytes(),
        )

    def test_package_and_skill_versions_are_independently_declared(self):
        package = read_json(PLUGIN / ".claude-plugin" / "plugin.json")["version"]
        ledger = LEDGER.read_text(encoding="utf-8")
        skill = re.search(r"- Current version: `synkrisis-v(\d+\.\d+\.\d+)`", ledger)
        self.assertRegex(package, r"^\d+\.\d+\.\d+$")
        self.assertIsNotNone(skill)

    def test_contract_section_declares_exactly_the_scaffold_promise(self):
        text = SKILL.read_text(encoding="utf-8")
        contract = text.split("## Promise Machine contract", 1)[1]
        declared = {
            line.removeprefix("### ")
            for line in contract.splitlines()
            if line.startswith("### ")
        }
        self.assertEqual(declared, {"synkrisis-scaffold-refusal"})


class SpecificationTests(unittest.TestCase):
    def test_study_runbook_and_first_decision_record_are_committed(self):
        for path in (
            REPO_ROOT / "docs" / "synkrisis" / "study.md",
            REPO_ROOT / "docs" / "synkrisis" / "runbook.md",
            PLUGIN / "docs" / "decisions"
            / "ADR-001-keep-cross-run-diagnosis-separate.md",
        ):
            with self.subTest(path=path.relative_to(REPO_ROOT)):
                self.assertTrue(path.is_file())

    def test_the_skill_links_resolve_to_the_committed_specification(self):
        text = SKILL.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(((?:\.\./)+[^)]+)\)", text):
            with self.subTest(link=link):
                self.assertTrue((SKILL.parent / link).resolve().is_file())

    def test_the_runbook_names_every_specified_operation_step(self):
        runbook = (REPO_ROOT / "docs" / "synkrisis" / "runbook.md").read_text(
            encoding="utf-8"
        )
        for heading in ("Step 1", "Step 2", "Step 3", "Step 4", "Step 5"):
            self.assertIn(f"## {heading}:", runbook)
        self.assertIn("(delivered)", runbook)
        self.assertEqual(runbook.count("(held)"), 4)


class ScaffoldRefusalTests(unittest.TestCase):
    """The stub's one promise: refuse with the step named, and write nothing."""

    def operations(self, root):
        return {
            "cohort": ("cohort", "--manifest", "manifest.json", "--policy",
                       "policy.json", "--out", "out/cohort.json"),
            "diagnose": ("diagnose", "--cohort", "cohort.json", "--rules",
                         "rules.json", "--out", "out/findings.json"),
            "render": ("render", "findings.json", "--out", "out/report.md"),
            "verify": ("verify", "--manifest", "manifest.json", "--policy",
                       "policy.json", "--cohort", "cohort.json", "--rules",
                       "rules.json", "--findings", "findings.json",
                       "--report", "report.md"),
        }

    def test_help_prints_the_specified_surface_without_writing(self):
        with tempfile.TemporaryDirectory() as scratch:
            completed = run_cli("--help", cwd=scratch)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            for operation in ("cohort", "diagnose", "render", "verify"):
                self.assertIn(operation, completed.stdout)
            self.assertEqual(os.listdir(scratch), [])

    def test_every_operation_refuses_with_the_scaffold_code(self):
        with tempfile.TemporaryDirectory() as scratch:
            for operation, arguments in self.operations(scratch).items():
                with self.subTest(operation=operation):
                    completed = run_cli(*arguments, cwd=scratch)
                    self.assertEqual(completed.returncode, 1)
                    self.assertIn("SK000", completed.stdout)
                    self.assertIn(
                        "promise-machine-run-observation/v1", completed.stdout
                    )

    def test_operations_refuse_even_with_plausible_inputs(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            for name in ("manifest.json", "policy.json", "cohort.json",
                         "rules.json", "findings.json"):
                (root / name).write_text("{}\n", encoding="utf-8")
            (root / "report.md").write_text("# report\n", encoding="utf-8")
            for operation, arguments in self.operations(scratch).items():
                with self.subTest(operation=operation):
                    completed = run_cli(*arguments, cwd=scratch)
                    self.assertEqual(completed.returncode, 1)
                    self.assertIn("SK000", completed.stdout)

    def test_no_operation_writes_an_output(self):
        with tempfile.TemporaryDirectory() as scratch:
            before = sorted(os.listdir(scratch))
            for arguments in self.operations(scratch).values():
                run_cli(*arguments, cwd=scratch)
            self.assertEqual(sorted(os.listdir(scratch)), before)

    def test_refusal_names_the_pending_runbook_step(self):
        expected = {
            "cohort": "Step 2",
            "diagnose": "Step 3",
            "render": "Step 4",
            "verify": "Step 4",
        }
        with tempfile.TemporaryDirectory() as scratch:
            for operation, arguments in self.operations(scratch).items():
                with self.subTest(operation=operation):
                    completed = run_cli(*arguments, "--json", cwd=scratch)
                    document = json.loads(completed.stdout)
                    self.assertIn(expected[operation], document["recovery"])
                    self.assertIn("docs/synkrisis/runbook.md", document["recovery"])

    def test_refusal_output_names_code_producer_path_and_recovery(self):
        with tempfile.TemporaryDirectory() as scratch:
            completed = run_cli(
                *self.operations(scratch)["cohort"], "--json", cwd=scratch
            )
            self.assertEqual(completed.returncode, 1)
            document = json.loads(completed.stdout)
            self.assertEqual(
                sorted(document),
                ["code", "fault", "message", "path", "producer", "recovery"],
            )
            self.assertEqual(document["code"], "SK000")
            self.assertEqual(
                document["producer"], "promise-machine-run-observation/v1"
            )


if __name__ == "__main__":
    unittest.main()
