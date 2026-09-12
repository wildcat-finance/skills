"""Hold the kickoff target-input registry to the two properties issue 1482 asked for.

The registry at ``docs/kickoff/1359/targets.json`` is a record of observations
made once, with the commands its Markdown twin names. Nothing here re-observes
the chain. What is held is mechanical: the committed registry passes its own
checker, every consumer maps to a row, every evidence file still hashes to the
digest the registry recorded, and a specimen carrying the wrong generation, the
wrong code hash or the wrong chain is rejected while the recorded one is
accepted.

The mutation cases copy the registry into scratch and break one thing at a
time, so a checker that passed everything would fail here for the right
reason. The command-line cases run the script with a fixed argv and no shell,
which is the boundary the repository's off-chain surface rule requires.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "kickoff_targets.py"
REGISTRY = ROOT / "docs" / "kickoff" / "1359" / "targets.json"
SPECIMENS = ROOT / "docs" / "kickoff" / "1359" / "specimens"
RECORD = ROOT / "docs" / "kickoff" / "1359" / "targets.md"
CONSUMERS = (1354, 1355, 1359, 1361, 1363)


def load_module():
    spec = importlib.util.spec_from_file_location("kickoff_targets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*arguments: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=str(ROOT), capture_output=True, text=True, timeout=120, check=False,
    )


def copy_registry_tree(destination: Path) -> Path:
    """Copy the registry, its evidence and the checker into a scratch root."""
    (destination / "docs" / "kickoff").mkdir(parents=True)
    shutil.copytree(REGISTRY.parent, destination / "docs" / "kickoff" / "1359")
    return destination / "docs" / "kickoff" / "1359" / "targets.json"


class CommittedRegistryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def test_the_committed_registry_is_clean(self):
        result = run("check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("kickoff-targets: clean", result.stdout)

    def test_every_kickoff_consumer_maps_to_a_row(self):
        by_issue = {c["issue"]: c for c in self.registry["consumers"]}
        ids = {t["id"] for t in self.registry["targets"]}
        for issue in CONSUMERS:
            with self.subTest(issue=issue):
                self.assertIn(issue, by_issue)
                self.assertTrue(by_issue[issue]["targets"])
                self.assertTrue(set(by_issue[issue]["targets"]) <= ids)

    def test_the_record_names_the_registry_and_the_check(self):
        text = RECORD.read_text(encoding="utf-8")
        self.assertIn("targets.json", text)
        self.assertIn("scripts/kickoff_targets.py check", text)
        for issue in CONSUMERS:
            self.assertIn(f"#{issue}", text)

    def test_every_pending_decision_is_visible_in_the_record(self):
        text = RECORD.read_text(encoding="utf-8")
        for decision in self.registry["decisions"]:
            with self.subTest(decision=decision["id"]):
                self.assertIn(decision["id"], text)

    def test_a_resolved_row_needs_a_recorded_decision(self):
        decisions = {d["id"]: d for d in self.registry["decisions"]}
        for target in self.registry["targets"]:
            if target["status"] == "resolved":
                with self.subTest(target=target["id"]):
                    self.assertEqual(decisions[target["decision"]]["status"], "recorded")

    def test_evidence_digests_recompute(self):
        for relative, digest in self.registry["evidence_digests"].items():
            with self.subTest(path=relative):
                self.assertEqual(self.module.sha256_of(ROOT / relative), digest)

    def test_every_identifier_the_record_quotes_is_in_the_registry_or_evidence(self):
        """A hash typed into prose by hand is the transcription error this guards."""
        text = RECORD.read_text(encoding="utf-8")
        corpus = REGISTRY.read_text(encoding="utf-8").lower()
        for path in sorted((REGISTRY.parent / "evidence").rglob("*")):
            if path.is_file():
                corpus += path.read_text(encoding="utf-8", errors="replace").lower()
        tokens = set()
        for pattern in (r"\b0x[0-9a-fA-F]{40}\b", r"\b0x[0-9a-fA-F]{64}\b", r"\b[0-9a-f]{40}\b", r"\b[0-9a-f]{64}\b"):
            tokens.update(re.findall(pattern, text))
        self.assertGreater(len(tokens), 100)
        missing = sorted(token for token in tokens if token.lower() not in corpus)
        self.assertEqual(missing, [])


class SpecimenTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))

    def specimen(self, name: str) -> dict:
        return json.loads((SPECIMENS / name).read_text(encoding="utf-8"))

    def test_the_recorded_market_init_code_is_accepted(self):
        reasons = self.module.judge_specimen(self.registry, self.specimen("accepted-v2-market-init-code.json"))
        self.assertEqual(reasons, [])
        result = run("specimen", "--specimen", str(SPECIMENS / "accepted-v2-market-init-code.json"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(result.stdout.startswith("accepted:"))

    def test_a_wrong_generation_is_rejected(self):
        reasons = self.module.judge_specimen(self.registry, self.specimen("wrong-generation.json"))
        self.assertTrue(any("generation" in reason for reason in reasons), reasons)

    def test_a_wrong_code_hash_is_rejected(self):
        reasons = self.module.judge_specimen(self.registry, self.specimen("wrong-code-hash.json"))
        self.assertTrue(any("code hash" in reason for reason in reasons), reasons)

    def test_the_two_fixed_term_templates_are_told_apart(self):
        reasons = self.module.judge_specimen(self.registry, self.specimen("wrong-template-source.json"))
        self.assertTrue(any("code hash" in reason for reason in reasons), reasons)

    def test_a_reused_address_on_the_wrong_chain_is_rejected(self):
        reasons = self.module.judge_specimen(self.registry, self.specimen("wrong-chain.json"))
        self.assertTrue(any("chain" in reason for reason in reasons), reasons)

    def test_every_committed_specimen_exits_as_its_note_says(self):
        for path in sorted(SPECIMENS.glob("*.json")):
            with self.subTest(specimen=path.name):
                expected = 0 if path.name.startswith("accepted") else 1
                result = run("specimen", "--specimen", str(path))
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_an_unknown_target_and_a_missing_field_are_rejected(self):
        self.assertEqual(self.module.judge_specimen(self.registry, {"target": "nowhere", "generation": "V2", "chain_id": 1, "address": "0x" + "0" * 40, "code_keccak256": "0x" + "0" * 64}), ["unknown target 'nowhere'"])
        self.assertTrue(self.module.judge_specimen(self.registry, {"target": "wildcat-v2-ethereum-mainnet"}))
        self.assertEqual(self.module.judge_specimen(self.registry, []), ["specimen is not an object"])


class MutationTests(unittest.TestCase):
    """Break one thing in a scratch copy and require the checker to name it."""

    def setUp(self):
        self.module = load_module()
        self.scratch = Path(tempfile.mkdtemp(prefix="kickoff-targets-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.path = copy_registry_tree(self.scratch)
        self.registry = json.loads(self.path.read_text(encoding="utf-8"))

    def findings(self) -> list[str]:
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")
        return self.module.Checker(self.registry, self.scratch, self.path).run()

    def test_the_copy_starts_clean(self):
        self.assertEqual(self.findings(), [])

    def test_a_moved_evidence_byte_is_named(self):
        evidence = self.scratch / "docs" / "kickoff" / "1359" / "evidence" / "ethereum-mainnet.json"
        evidence.write_bytes(evidence.read_bytes() + b" ")
        findings = self.findings()
        self.assertTrue(any("ethereum-mainnet.json" in f and "differs from recorded" in f for f in findings), findings)

    def test_a_consumer_without_a_row_is_named(self):
        self.registry["consumers"][0]["targets"] = []
        findings = self.findings()
        self.assertTrue(any("maps to no target row" in f for f in findings), findings)

    def test_a_consumer_naming_an_unknown_row_is_named(self):
        self.registry["consumers"][0]["targets"] = ["no-such-row"]
        findings = self.findings()
        self.assertTrue(any("unknown target 'no-such-row'" in f for f in findings), findings)

    def test_a_row_that_forgets_its_consumer_is_named(self):
        consumer = self.registry["consumers"][0]
        target = next(t for t in self.registry["targets"] if t["id"] == consumer["targets"][0])
        target["consumers"] = [n for n in target["consumers"] if n != consumer["issue"]]
        findings = self.findings()
        self.assertTrue(any("does not list it back" in f for f in findings), findings)

    def test_resolved_on_a_pending_decision_is_named(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        target["status"] = "resolved"
        target["decision"] = "kickoff-consumer-target"
        findings = self.findings()
        self.assertTrue(any("still pending" in f for f in findings), findings)

    def test_resolved_on_a_recorded_decision_passes(self):
        decision = next(d for d in self.registry["decisions"] if d["id"] == "kickoff-consumer-target")
        decision["status"] = "recorded"
        decision["decision_maker"] = {"name": "A Maintainer", "role": "target maintainer", "date": "2026-09-12", "reference": "https://github.com/wildcat-finance/skills/pull/0"}
        decision["selection"] = "ethereum-only"
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        target["status"] = "resolved"
        target["decision"] = "kickoff-consumer-target"
        self.assertEqual(self.findings(), [])

    def test_a_recorded_decision_without_a_reference_is_named(self):
        decision = self.registry["decisions"][0]
        decision["status"] = "recorded"
        decision["decision_maker"] = {"name": "A Maintainer", "role": "target maintainer", "date": "2026-09-12", "reference": ""}
        decision["selection"] = "ethereum-only"
        findings = self.findings()
        self.assertTrue(any("decision_maker.reference is empty" in f for f in findings), findings)

    def test_a_contract_hash_that_disagrees_with_the_evidence_is_named(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        contract = target["deployment"]["contracts"][2]
        contract["code_keccak256"] = "0x" + "1" * 64
        findings = self.findings()
        self.assertTrue(any(contract["address"] in f and "disagrees with the evidence" in f for f in findings), findings)

    def test_a_contract_absent_from_the_evidence_is_named(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        target["deployment"]["contracts"].append({"role": "ghost", "name": "Ghost", "address": "0x" + "9" * 40, "code_keccak256": "0x" + "9" * 64, "code_match": {"method": "none"}})
        findings = self.findings()
        self.assertTrue(any("has no code observation" in f for f in findings), findings)

    def test_a_blocked_row_needs_a_recovery_issue(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "aave-v3")
        target["status"] = "blocked"
        target["blocker"] = "no deployment pin"
        findings = self.findings()
        self.assertTrue(any("without a recovery issue URL" in f for f in findings), findings)
        target["recovery"] = "https://github.com/wildcat-finance/skills/issues/1139"
        self.assertEqual(self.findings(), [])

    def test_a_candidate_needs_a_known_pending_decision(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "aave-v3")
        target["pending_on"] = ["nobody-decides-this"]
        findings = self.findings()
        self.assertTrue(any("unknown decision 'nobody-decides-this'" in f for f in findings), findings)

    def test_a_duplicate_target_id_is_named(self):
        self.registry["targets"].append(dict(self.registry["targets"][-1]))
        findings = self.findings()
        self.assertTrue(any("duplicate target id" in f for f in findings), findings)

    def test_the_command_line_reports_findings_with_exit_one(self):
        self.registry["consumers"][0]["targets"] = []
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")
        result = run("--root", str(self.scratch), "check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("maps to no target row", result.stdout)

    def test_an_unreadable_registry_exits_two(self):
        self.path.write_text("{not json", encoding="utf-8")
        result = run("--root", str(self.scratch), "check")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("not JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
