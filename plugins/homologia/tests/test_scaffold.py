"""Packaging and contract tests for the checked-input generation.

Nothing here compares an implementation to a mirror, because nothing does that
yet. These check that both hosts discover one version, the canonical contract
declares only shipped promises, and every later verb still refuses.
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
SKILL = PLUGIN / "skills" / "homologia" / "SKILL.md"
LEDGER = PLUGIN / "skills" / "homologia" / "EVOLUTION.md"
SCRIPT = PLUGIN / "scripts" / "homologia.py"
VERSION = "1.1.0"
DEFERRED_PROMISES = (
    "homologia-mirror-execution",
    "homologia-parity-verdict",
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )


class ManifestTests(unittest.TestCase):
    def test_the_claude_manifest_declares_the_plugin_and_its_skills(self):
        manifest = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "homologia")
        self.assertEqual(manifest["version"], VERSION)
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["license"], "Apache-2.0")

    def test_the_codex_manifest_agrees_and_carries_an_interface(self):
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "homologia")
        self.assertEqual(manifest["version"], VERSION)
        interface = manifest["interface"]
        self.assertEqual(interface["displayName"], "Homologia")
        self.assertIn("$homologia", interface["defaultPrompt"])

    def test_both_manifests_state_the_same_description(self):
        claude = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(claude["description"], codex["description"])


class ContractTests(unittest.TestCase):
    def test_the_canonical_skill_states_the_declared_version(self):
        metadata = re.search(r'version:\s*"([^"]+)"', SKILL.read_text(encoding="utf-8"))
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.group(1), VERSION)

    def test_the_canonical_skill_points_at_its_ledger(self):
        self.assertIn("[EVOLUTION.md](EVOLUTION.md)", SKILL.read_text(encoding="utf-8"))

    def test_the_contract_declares_only_the_two_shipped_promises(self):
        declared = re.findall(r"^### (homologia-[a-z-]+)$", SKILL.read_text(encoding="utf-8"), re.M)
        self.assertEqual(
            declared,
            ["homologia-scaffold-identity", "homologia-expected-answer-provenance"],
        )
        for promise in DEFERRED_PROMISES:
            with self.subTest(promise=promise):
                self.assertNotIn(promise, declared)

    def test_the_contract_names_the_step_each_promise_arrives_with(self):
        text = SKILL.read_text(encoding="utf-8")
        for promise in DEFERRED_PROMISES:
            with self.subTest(promise=promise):
                self.assertIn(f"`{promise}`", text)

    def test_the_contract_refuses_to_call_agreement_correctness(self):
        # Collapse wrapping: the contract is prose and reflows, the claim does not.
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("never states that either implementation is correct", text)
        self.assertIn("Never report agreement as correctness.", text)

    def test_the_ledger_advances_to_mirror_execution(self):
        text = LEDGER.read_text(encoding="utf-8")
        self.assertIn("Current version: `homologia-v1.1.0`", text)
        self.assertIn("Frontier status: `open`", text)
        self.assertIn("Frontier revision: `mirror-execution`", text)

    def test_the_installed_promise_machine_copy_matches_the_suite_law(self):
        self.assertEqual(
            (PLUGIN / "PROMISE_MACHINE.md").read_bytes(),
            (ROOT / "PROMISE_MACHINE.md").read_bytes(),
        )


class IdentityTests(unittest.TestCase):
    """Cases behind homologia-scaffold-identity."""

    def test_identity_agrees_across_both_manifests_and_the_marketplace(self):
        claude = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        listing = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = next(p for p in listing["plugins"] if p["name"] == "homologia")
        self.assertEqual({claude["version"], codex["version"], entry["version"]}, {VERSION})
        self.assertEqual({claude["name"], codex["name"], entry["name"]}, {"homologia"})

    def test_a_drifted_installed_root_law_copy_is_detected(self):
        # The equality check has to have teeth: mutate a copy and require the
        # same comparison to fail, so a green suite is not a trivial pass.
        law = (ROOT / "PROMISE_MACHINE.md").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            drifted = Path(tmp) / "PROMISE_MACHINE.md"
            drifted.write_bytes(law.replace(b"Promise", b"Promyse", 1))
            self.assertNotEqual(drifted.read_bytes(), law)
        self.assertEqual((PLUGIN / "PROMISE_MACHINE.md").read_bytes(), law)

    def test_no_verb_prints_a_verdict_on_standard_output(self):
        for verb in ("check", "run-mirror", "compare", "render", "verify"):
            with self.subTest(verb=verb):
                self.assertEqual(run(verb).stdout, "")

    def test_a_refusal_names_where_the_behaviour_will_come_from(self):
        stderr = run("compare").stderr
        self.assertIn("homologia-v1.1.0", stderr)
        self.assertIn("homologia-runbook.md", stderr)


class CommandTests(unittest.TestCase):
    def test_help_succeeds_and_names_every_verb(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for verb in ("check", "run-mirror", "compare", "render", "verify"):
            with self.subTest(verb=verb):
                self.assertIn(verb, result.stdout)

    def test_help_states_that_a_verdict_is_not_correctness(self):
        self.assertIn("never correctness", run("--help").stdout)

    def test_no_argument_prints_help_and_succeeds(self):
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: homologia", result.stdout)

    def test_every_later_verb_refuses_rather_than_answering(self):
        for verb in ("run-mirror", "compare", "render", "verify"):
            with self.subTest(verb=verb):
                result = run(verb)
                self.assertEqual(result.returncode, 3, result.stdout)
                self.assertIn("not built yet", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_check_requires_explicit_manifest_and_output_paths(self):
        result = run("check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--manifest", result.stderr)
        self.assertIn("--out", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_the_version_flag_reports_the_checked_input_generation(self):
        result = run("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(VERSION, result.stdout)
        self.assertNotIn("scaffold", result.stdout)


if __name__ == "__main__":
    unittest.main()
