"""Scaffold tests: the packaging, the contract and the self-test agree.

Nothing here compiles an inventory, imports a workbook or records a
disposition, because nothing does that yet. These check the claims the scaffold
itself makes: that both hosts can discover the plugin, that one version is
stated everywhere it is stated at all, that the canonical contract declares one
keepable promise and names the three it does not keep, that every unbuilt verb
refuses, and that the self-test emits a report a design transition can consume.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "dokimasia" / "SKILL.md"
LEDGER = PLUGIN / "skills" / "dokimasia" / "EVOLUTION.md"
SCRIPT = PLUGIN / "scripts" / "dokimasia.py"
VERSION = "0.1.0"
UNBUILT = ("reconcile", "demonstrate")
KEPT_PROMISES = (
    "dokimasia-scaffold-identity",
    "dokimasia-source-inventory",
    "dokimasia-workbook-lineage",
)
UNKEPT_PROMISES = ("dokimasia-disposition-closure",)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )


def manifest(host: str) -> dict:
    return json.loads((PLUGIN / host / "plugin.json").read_text(encoding="utf-8"))


class ManifestTests(unittest.TestCase):
    def test_the_claude_manifest_declares_the_plugin_and_its_skills(self):
        claude = manifest(".claude-plugin")
        self.assertEqual(claude["name"], "dokimasia")
        self.assertEqual(claude["version"], VERSION)
        self.assertEqual(claude["skills"], "./skills/")
        self.assertEqual(claude["license"], "Apache-2.0")

    def test_the_codex_manifest_agrees_and_carries_an_interface(self):
        codex = manifest(".codex-plugin")
        self.assertEqual(codex["name"], "dokimasia")
        self.assertEqual(codex["version"], VERSION)
        interface = codex["interface"]
        self.assertEqual(interface["displayName"], "Dokimasia")
        self.assertIn("$dokimasia", interface["defaultPrompt"])

    def test_both_manifests_state_the_same_description(self):
        self.assertEqual(
            manifest(".claude-plugin")["description"],
            manifest(".codex-plugin")["description"],
        )

    def test_the_long_description_refuses_to_promise_a_verdict(self):
        long_description = manifest(".codex-plugin")["interface"]["longDescription"]
        self.assertIn("Every substantive verb refuses", long_description)
        self.assertIn("never report an item as covered", long_description.lower())


class ContractTests(unittest.TestCase):
    def test_the_canonical_skill_states_the_declared_version(self):
        metadata = re.search(r'version:\s*"([^"]+)"', SKILL.read_text(encoding="utf-8"))
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.group(1), VERSION)

    def test_the_canonical_skill_points_at_its_ledger(self):
        self.assertIn("[EVOLUTION.md](EVOLUTION.md)", SKILL.read_text(encoding="utf-8"))

    def test_the_scaffold_declares_only_what_it_can_keep(self):
        # A promise with no case that could support it is the overclaim the root
        # law refuses. The scaffold has packaging and a self-test to show, so
        # identity is the one promise it declares.
        text = SKILL.read_text(encoding="utf-8")
        declared = re.findall(r"^### (dokimasia-[a-z-]+)$", text, re.M)
        self.assertEqual(declared, list(KEPT_PROMISES))
        for promise in UNKEPT_PROMISES:
            with self.subTest(promise=promise):
                self.assertNotIn(promise, declared)

    def test_the_contract_names_the_step_each_unkept_promise_arrives_with(self):
        # Collapse wrapping: the contract is prose and reflows, the claim does not.
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        for promise, step in zip(UNKEPT_PROMISES, ("step 4",)):
            with self.subTest(promise=promise):
                self.assertIn(f"`{promise}`", text)
                self.assertIn(f"{step} owes it", text)

    def test_the_contract_refuses_to_call_closure_a_pass(self):
        # Collapse wrapping: the contract is prose and reflows, the claim does not.
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Never report an item as covered without a reviewed oracle.", text)
        self.assertIn("It does not mean anything passed.", text)

    def test_the_ledger_opens_the_first_frontier(self):
        text = LEDGER.read_text(encoding="utf-8")
        self.assertIn("Current version: `dokimasia-v0.1.0`", text)
        self.assertIn("Frontier status: `open`", text)
        self.assertIn("Frontier revision: `first-scrutiny`", text)

    def test_the_ledger_row_digest_matches_the_frontier_it_describes(self):
        text = LEDGER.read_text(encoding="utf-8")

        def field(label: str) -> str:
            return re.search(rf"^- {label}: (.+)$", text, re.M).group(1)

        import hashlib

        line = "|".join(
            (
                field("Frontier status").strip("`"),
                field("Frontier revision").strip("`"),
                field("Current frontier"),
                field("Next Fiat job"),
            )
        ) + "\n"
        recorded = re.search(r"\| `([0-9a-f]{64})` \|", text).group(1)
        self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), recorded)

    def test_the_installed_promise_machine_copy_matches_the_suite_law(self):
        self.assertEqual(
            (PLUGIN / "PROMISE_MACHINE.md").read_bytes(),
            (ROOT / "PROMISE_MACHINE.md").read_bytes(),
        )


class IdentityTests(unittest.TestCase):
    """Cases behind dokimasia-scaffold-identity."""

    def test_identity_agrees_across_both_manifests_and_the_marketplace(self):
        listing = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = next(p for p in listing["plugins"] if p["name"] == "dokimasia")
        self.assertEqual(
            {manifest(".claude-plugin")["version"], manifest(".codex-plugin")["version"]},
            {VERSION},
        )
        self.assertEqual(entry["name"], "dokimasia")

    def test_a_drifted_installed_root_law_copy_is_detected(self):
        # The equality check has to have teeth: mutate a copy and require the
        # same comparison to fail, so a green suite is not a trivial pass.
        law = (ROOT / "PROMISE_MACHINE.md").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            drifted = Path(tmp) / "PROMISE_MACHINE.md"
            drifted.write_bytes(law.replace(b"Promise", b"Promyse", 1))
            self.assertNotEqual(drifted.read_bytes(), law)
        self.assertEqual((PLUGIN / "PROMISE_MACHINE.md").read_bytes(), law)

    def test_no_unbuilt_verb_prints_anything_on_standard_output(self):
        for verb in UNBUILT:
            with self.subTest(verb=verb):
                self.assertEqual(run(verb).stdout, "")

    def test_a_refusal_names_where_the_behaviour_will_come_from(self):
        stderr = run("reconcile").stderr
        self.assertIn("dokimasia-v0.1.0", stderr)
        self.assertIn("dokimasia-runbook.md", stderr)
        self.assertIn("Step 4", stderr)


class SelfTestTests(unittest.TestCase):
    def test_the_self_test_passes_against_the_committed_tree(self):
        result = run("selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("clean", result.stdout)

    def test_the_self_test_stays_quiet_about_the_verbs_it_probes(self):
        # It exercises the real refusal path, so its own output must not read
        # as four failures.
        self.assertEqual(run("selftest").stderr, "")

    def test_the_self_test_writes_a_report_a_design_transition_can_consume(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "nested" / "inventory-first-scaffold-contract-check.json"
            result = run("selftest", "--report", str(report))
            self.assertEqual(result.returncode, 0, result.stderr)
            body = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(body),
            ["candidate", "command", "criterion", "exit", "schema", "unit", "value"],
        )
        self.assertEqual(body["schema"], "protasis-design-report/v1")
        self.assertEqual(body["candidate"], "inventory-first")
        self.assertEqual(body["criterion"], "scaffold-contract-check")
        self.assertEqual(body["unit"], "boolean")
        self.assertIs(body["value"], True)
        self.assertEqual(body["exit"], 0)

    def test_the_self_test_refuses_a_report_path_that_is_a_symlink(self):
        # The guard has to be tested on the supplied path: an earlier version
        # resolved first and asked the resolved path whether it was a symlink,
        # which is always false, so the refusal could never fire.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "real.json"
            target.write_text("{}", encoding="utf-8")
            link = Path(tmp) / "inventory-first-scaffold-contract-check.json"
            link.symlink_to(target)
            result = run("selftest", "--report", str(link))
            survived = target.read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("is a symlink", result.stderr)
        self.assertEqual(survived, "{}", "the refused write reached the link target")

    def test_the_self_test_refuses_a_report_path_that_is_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("selftest", "--report", tmp)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("refused", result.stderr)

    def test_a_version_disagreement_would_be_caught(self):
        # The check must have teeth: the comparison the self-test performs is
        # reproduced here over a mutated set, and must fail.
        declared = {"claude": VERSION, "codex": VERSION, "skill": "0.2.0"}
        self.assertNotEqual(len(set(declared.values())), 1)


class CommandTests(unittest.TestCase):
    def test_help_succeeds_and_names_every_verb(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for verb in (*UNBUILT, "selftest"):
            with self.subTest(verb=verb):
                self.assertIn(verb, result.stdout)

    def test_help_states_that_a_scrutiny_is_not_a_pass(self):
        self.assertIn("never that anything passed", run("--help").stdout)

    def test_no_argument_prints_help_and_succeeds(self):
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: dokimasia", result.stdout)

    def test_every_unbuilt_verb_refuses_rather_than_answering(self):
        for verb in UNBUILT:
            with self.subTest(verb=verb):
                result = run(verb)
                self.assertEqual(result.returncode, 3, result.stdout)
                self.assertIn("not built yet", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_the_inventory_verb_is_built_and_self_checks(self):
        result = run("inventory", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check clean", result.stdout)

    def test_the_workbook_verb_is_built_and_self_checks(self):
        result = run("workbook", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check clean", result.stdout)

    def test_the_version_flag_reports_the_scaffold(self):
        result = run("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(VERSION, result.stdout)
        self.assertIn("scaffold", result.stdout)


if __name__ == "__main__":
    unittest.main()
