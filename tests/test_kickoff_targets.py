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

import hashlib
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
CONSUMERS = (1354, 1355, 1359, 1361, 1363, 1365, 1376, 1379, 1395,
             1485, 1486, 1488, 1490, 1492, 1493, 1494, 1497, 1498)


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

    def blocked(self, row_id: str = "centrifuge-v3") -> dict:
        """Put a resolved row back as it stood before its recovery: blocked on its recovery child."""
        target = next(t for t in self.registry["targets"] if t["id"] == row_id)
        target["status"] = "blocked"
        target["blocker"] = "no deployment pin"
        target["recovery"] = target.pop("recovery_completed_by")
        return target

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
        decision = next(d for d in self.registry["decisions"] if d["id"] == "kickoff-consumer-target")
        decision.update(status="pending", decision_maker=None, selection=None)
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        target["status"] = "resolved"
        target["decision"] = "kickoff-consumer-target"
        findings = self.findings()
        self.assertTrue(any("still pending" in f for f in findings), findings)

    def test_scope_approval_does_not_resolve_missing_source_evidence(self):
        target = self.blocked()
        self.assertEqual(self.findings(), [])
        target["status"] = "resolved"
        target["decision"] = "kickoff-consumer-target"
        self.assertTrue(any("resolved with unresolved evidence" in f for f in self.findings()))

    def test_a_resolved_row_cannot_keep_a_blocker(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        target["blocker"] = "a gap somebody forgot to clear"
        self.assertTrue(any("resolved with unresolved evidence" in f for f in self.findings()))

    def test_a_resolved_contract_needs_a_source_commit(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        contract = next(c for c in target["deployment"]["contracts"] if c["role"] == "hooks-instance")
        contract["code_match"]["source_commit"] = None
        findings = self.findings()
        self.assertTrue(any("resolved without a source match" in f for f in findings), findings)


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
        target = self.blocked()
        recovery = target.pop("recovery")
        findings = self.findings()
        self.assertTrue(any("without a recovery issue URL" in f for f in findings), findings)
        target["recovery"] = recovery
        self.assertEqual(self.findings(), [])

    def test_a_candidate_needs_a_known_pending_decision(self):
        target = next(t for t in self.registry["targets"] if t["id"] == "euler-v1")
        target["status"] = "candidate"
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

    def test_swapping_venues_without_approval_is_rejected(self):
        slots = self.registry["scope"]["ordered_slots"]
        slots[3], slots[4] = slots[4], slots[3]
        for position, slot in enumerate(slots, 1):
            slot["order"] = position
        findings = self.findings()
        self.assertTrue(any("ordered_slots differs from approval evidence" in f for f in findings), findings)

    def test_omitting_an_approved_maple_family_is_rejected(self):
        self.registry["scope"]["ordered_slots"][2]["targets"].pop()
        findings = self.findings()
        self.assertTrue(any("slot 3 has the wrong generation count" in f for f in findings), findings)

    def test_a_deleted_consumer_cannot_shrink_the_denominator(self):
        self.registry["consumers"] = [c for c in self.registry["consumers"] if c["issue"] != 1395]
        findings = self.findings()
        self.assertTrue(any("mapped dispositions differ" in f for f in findings), findings)

    def test_an_excluded_row_cannot_supply_a_consumer(self):
        consumer = self.registry["consumers"][0]
        consumer["targets"] = ["wildcat-v2-plasma-mainnet"]
        target = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-plasma-mainnet")
        target["consumers"] = [consumer["issue"]]
        findings = self.findings()
        self.assertTrue(any("uses excluded target" in f for f in findings), findings)

    def test_a_broad_epic_is_not_the_specific_source_recovery(self):
        target = self.blocked()
        target["recovery"] = "https://github.com/wildcat-finance/skills/issues/1142"
        findings = self.findings()
        self.assertTrue(any("not its recorded source-recovery child" in f for f in findings), findings)

    def test_an_evidence_symlink_cannot_escape_the_repository(self):
        evidence = self.scratch / "docs/kickoff/1359/evidence/scope-approval.json"
        original = evidence.read_bytes()
        with tempfile.TemporaryDirectory(prefix="kickoff-outside-") as outside:
            remote = Path(outside) / "approval.json"
            remote.write_bytes(original)
            evidence.unlink()
            evidence.symlink_to(remote)
            findings = self.findings()
        self.assertTrue(any("escapes repository root" in f for f in findings), findings)

    def test_specimen_command_refuses_a_changed_evidence_file(self):
        evidence = self.scratch / "docs/kickoff/1359/evidence/scope-approval.json"
        evidence.write_bytes(evidence.read_bytes() + b" ")
        result = run("--root", str(self.scratch), "specimen", "--specimen", str(SPECIMENS / "accepted-v2-market-init-code.json"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("registry validation failed", result.stdout)

    def test_duplicate_json_keys_and_malformed_containers_refuse(self):
        self.path.write_text('{"schema":"first","schema":"second"}')
        result = run("--root", str(self.scratch), "check")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("duplicate JSON key", result.stderr)
        self.registry["decisions"][0]["selection"] = {"unexpected": []}
        findings = self.findings()
        self.assertTrue(findings)

    def test_boolean_chain_and_unhashable_target_refuse(self):
        specimen = json.loads((SPECIMENS / "accepted-v2-market-init-code.json").read_text())
        specimen["chain_id"] = True
        self.assertEqual(self.module.judge_specimen(self.registry, specimen), ["specimen chain_id is not a positive integer"])
        specimen["target"] = []
        self.assertTrue(self.module.judge_specimen(self.registry, specimen))

    def test_bounded_file_read_refuses_oversize_and_special_files(self):
        self.path.write_bytes(b"x" * 65)
        with self.assertRaises(self.module.RegistryError):
            self.module.read_json(self.path, limit=64)
        with self.assertRaises(self.module.RegistryError):
            self.module.read_json(Path('/dev/null'))




class ScopeAmendmentTests(unittest.TestCase):
    """A later venue slot enters only on an attested record the checker can bind."""

    ROW = "testvenue-v1"

    def setUp(self):
        self.module = load_module()
        self.scratch = Path(tempfile.mkdtemp(prefix="kickoff-amendment-"))
        self.addCleanup(shutil.rmtree, self.scratch, ignore_errors=True)
        self.path = copy_registry_tree(self.scratch)
        self.registry = json.loads(self.path.read_text(encoding="utf-8"))
        self.maker = {"name": "A Maintainer", "role": "maintainer", "date": "2026-09-29",
                      "reference": "https://github.com/wildcat-finance/skills/issues/1#issuecomment-1"}
        # The synthetic venue takes the slot after any the committed registry already amends.
        self.order = 6 + len(self.registry["scope"].get("amendments", []))
        body = f"The maintainer approves slot {self.order}: Testvenue, row testvenue-v1."
        self.record = {"schema": "wildcat.kickoff-scope-amendment.v1", "decision_maker": self.maker,
                       "comment_body": body, "comment_body_sha256": hashlib.sha256(body.encode()).hexdigest(),
                       "slot": {"order": self.order, "venue": "Testvenue", "targets": [self.ROW]}}
        # The synthetic venue's row borrows a resolved row's evidence, under its own id and venue.
        row = json.loads(json.dumps(next(t for t in self.registry["targets"] if t["id"] == "centrifuge-v3")))
        row.update(id=self.ROW, venue="Testvenue", consumers=[1359])
        self.registry["targets"].append(row)
        next(c for c in self.registry["consumers"] if c["issue"] == 1359)["targets"].append(self.ROW)
        self.registry["decisions"].append({
            "id": "test-sixth-venue", "question": "Which venue fills a sixth slot?",
            "decision_maker_role": "maintainer", "options": ["Testvenue"], "status": "recorded",
            "decision_maker": self.maker, "selection": [self.ROW]})
        self.registry["scope"].setdefault("amendments", []).append({
            "order": self.order, "venue": "Testvenue", "targets": [self.ROW], "decision": "test-sixth-venue",
            "evidence": "docs/kickoff/1359/evidence/scope-amendment-test.json"})

    def findings(self) -> list[str]:
        relative = "docs/kickoff/1359/evidence/scope-amendment-test.json"
        raw = json.dumps(self.record).encode()
        (self.scratch / relative).write_bytes(raw)
        self.registry["evidence_digests"][relative] = hashlib.sha256(raw).hexdigest()
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")
        return self.module.Checker(self.registry, self.scratch, self.path).run()

    def test_a_bound_amendment_admits_its_row(self):
        self.assertEqual(self.findings(), [])

    def test_a_row_outside_every_slot_is_still_refused(self):
        self.registry["scope"]["amendments"].pop()
        self.assertTrue(any("admitted rows differ from approved slots" in f for f in self.findings()))

    def test_an_amendment_without_its_record_is_named(self):
        self.record["schema"] = "something-else"
        self.assertTrue(any("amendment evidence is absent or unverified" in f for f in self.findings()))

    def test_an_edited_comment_body_is_named(self):
        self.record["comment_body"] += " And a seventh."
        self.assertTrue(any("amendment comment body digest differs" in f for f in self.findings()))

    def test_a_slot_the_record_does_not_name_is_named(self):
        self.record["slot"]["targets"] = ["another-row"]
        self.assertTrue(any("slot differs from its amendment evidence" in f for f in self.findings()))

    def test_a_decision_by_someone_else_is_named(self):
        self.registry["decisions"][-1]["decision_maker"] = dict(self.maker, name="Somebody Else")
        self.assertTrue(any("decision lacks the recorded amendment attribution" in f for f in self.findings()))

    def test_the_approved_order_still_needs_its_five_slots(self):
        self.registry["scope"]["amendments"][-1]["order"] = 5
        self.assertTrue(any(f"amendment slot {self.order} is malformed" in f for f in self.findings()))


class EstateMapTests(unittest.TestCase):
    """The 2026-09-18 estate map (#1590) is complete and bound to the resolved row."""

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.row = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        self.estate = json.loads((REGISTRY.parent / "evidence" / "ethereum-mainnet-1590.json").read_text(encoding="utf-8"))
        self.matches = json.loads((REGISTRY.parent / "evidence" / "source-match-1590.json").read_text(encoding="utf-8"))

    def test_the_row_is_resolved_without_open_gaps(self):
        self.assertEqual(self.row["status"], "resolved")
        for key in ("blocker", "unresolved", "documentation_gap"):
            self.assertNotIn(key, self.row)
        self.assertEqual(self.row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1590")

    def test_every_instance_and_market_is_a_row_contract_with_a_source_commit(self):
        contracts = {c["address"].lower(): c for c in self.row["deployment"]["contracts"]}
        instances = self.estate["hooks_instances"]
        markets = self.estate["markets"]
        self.assertEqual(len(instances), 42)
        self.assertEqual(len(markets), 80)
        for entry in instances + markets:
            with self.subTest(address=entry["address"]):
                contract = contracts[entry["address"].lower()]
                self.assertEqual(contract["code_keccak256"], entry["code_keccak256"])
                self.assertTrue(contract["code_match"]["source_commit"])

    def test_every_instance_and_market_reproduces_modulo_immutables(self):
        for i in self.estate["hooks_instances"]:
            self.assertEqual(i["runtime_vs_template_deployed_bytecode"]["differing_bytes_outside_immutables"], 0, i["address"])
            self.assertIsNotNone(i["deployed"], i["address"])
        for m in self.estate["markets"]:
            self.assertEqual(m["runtime_vs_market_deployed_bytecode"]["differing_bytes_outside_immutables"], 0, m["address"])
            self.assertTrue(m["listed_under_instance"], m["address"])
            self.assertIsNotNone(m["deployed"], m["address"])

    def test_the_market_and_instance_maps_agree_with_the_factory_events(self):
        events = self.estate["factory_events"]
        self.assertEqual(events["by_event"]["MarketDeployed"], len(self.estate["markets"]))
        self.assertEqual(events["by_event"]["HooksInstanceDeployed"], len(self.estate["hooks_instances"]))
        self.assertEqual(events["by_event"]["HooksTemplateAdded"], len(self.estate["hooks_factory"]["templates"]))
        by_template = {t["template"]: t for t in self.estate["hooks_factory"]["templates"]}
        for i in self.estate["hooks_instances"]:
            self.assertIn(i["address"], by_template[i["template"]]["instances"])
        for m in self.estate["markets"]:
            self.assertIn(m["address"], by_template[m["template"]]["markets"])

    def test_every_role_provider_is_either_the_borrower_or_the_matched_open_access_provider(self):
        for provider in self.estate["role_providers"]:
            with self.subTest(provider=provider["address"]):
                if provider["address"] == "0x5620553d8881335f74ad19259daacd1d9b373101":
                    self.assertEqual(provider["sourcify_match"], "match")
                    self.assertEqual(self.matches["open_access_role_provider"]["reproduction"]["runtime_modulo_immutables"]["differing_bytes_outside_immutables"], 0)
                else:
                    self.assertTrue(provider["is_the_borrower_of_every_instance_using_it"])

    def test_the_located_sources_reproduce_the_chain(self):
        self.assertTrue(self.matches["wildcat_fee_recipient"]["deployed_bytecode"]["equals_onchain_runtime"])
        collateral = self.matches["collateral"]
        self.assertEqual(collateral["factory"]["runtime_modulo_immutables"]["differing_bytes_outside_immutables"], 0)
        self.assertEqual(collateral["lens"]["runtime_modulo_immutables"]["differing_bytes_outside_immutables"], 0)
        self.assertTrue(collateral["collateral_init_code_storage"]["compiled_creation_bytecode"]["keccak256_equals_stored_init_code"])
        self.assertTrue(self.matches["third_fixed_term_template"]["reproduction"]["equals_stored_init_code"])
        self.assertTrue(all(row["identical_at_all_six"] for row in self.matches["emitter_pin_binding"]["paths"] if row["path"] != "src/access/FixedTermHooks.sol"))


class V1SourceRecoveryTests(unittest.TestCase):
    """The 2026-09-19 source recovery (#1748) closes the row's unresolved list."""

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.row = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v1-ethereum-mainnet")
        self.matches = json.loads((REGISTRY.parent / "evidence" / "source-match-1748.json").read_text(encoding="utf-8"))

    def test_the_row_is_resolved_without_open_gaps(self):
        self.assertEqual(self.row["status"], "resolved")
        for key in ("blocker", "unresolved", "documentation_gap", "recovery"):
            self.assertNotIn(key, self.row)
        self.assertEqual(self.row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1748")

    def test_every_deployment_contract_carries_a_source_commit(self):
        for contract in self.row["deployment"]["contracts"]:
            with self.subTest(address=contract["address"]):
                self.assertTrue(contract["code_match"]["source_commit"], contract["name"])

    def test_the_market_and_controller_init_code_reproduce_from_source(self):
        contracts = {c["role"]: c for c in self.row["deployment"]["contracts"]}
        for role, key in (("market-init-code-storage", "market_init_code"), ("controller-init-code-storage", "controller_init_code")):
            with self.subTest(role=role):
                evidence = self.matches[key]
                self.assertTrue(evidence["result"]["equal"])
                self.assertTrue(evidence["result"]["length_matches_recorded_init_code_length"])
                commit = contracts[role]["code_match"]["source_commit"]
                self.assertEqual(commit, evidence["source_commit"])
                self.assertEqual(commit, self.row["source"]["commit"])

    def test_the_market_lens_gap_is_the_recorded_one(self):
        lens = next(c for c in self.row["deployment"]["contracts"] if c["role"] == "lens")
        best = self.matches["market_lens"]["best_single_commit_match"]
        self.assertEqual(lens["code_match"]["source_commit"], best["commit"])
        self.assertEqual(best["equal"], 40)
        self.assertEqual(best["of"], 46)
        self.assertEqual(len(best["differing_paths"]), 6)
        gap = self.matches["market_lens"]["why_no_commit_reaches_46_of_46"]
        self.assertEqual(len(gap["group_a_pre_rewrite_only"]["paths"]) + len(gap["group_b_never_in_git"]["paths"]), 6)

    def test_the_equivalent_commits_checkout_is_recorded_as_unresolvable(self):
        checkout = self.matches["equivalent_commits_deployer_checkout"]
        self.assertEqual(checkout["resolution"], "cannot select one of the five; recorded as unresolvable with the above evidence, per the issue's 'or record why one cannot be selected' acceptance path")
        self.assertEqual(len(checkout["candidates"]), len(self.row["source"]["equivalent_commits"]) + 1)

    def test_the_shared_chainalysis_oracle_is_confirmed(self):
        v2 = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v2-ethereum-mainnet")
        v2_item = next(e for e in v2["protected_set_exclusions"] if "Chainalysis" in e["item"])
        v1_item = next(e for e in self.row["protected_set_exclusions"] if "Chainalysis" in e["item"])
        self.assertEqual(v1_item["item"], v2_item["item"])
        self.assertIn("0x40c57923924b5c5c5455c48d93317139addac8fb", self.matches["protected_set_check"]["result"].lower())


class V1InstanceReadTests(unittest.TestCase):
    """The 2026-09-19 pass (#1589) reads every V1 controller and market instance."""

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.row = next(t for t in self.registry["targets"] if t["id"] == "wildcat-v1-ethereum-mainnet")
        self.matches = json.loads((REGISTRY.parent / "evidence" / "source-match-1589.json").read_text(encoding="utf-8"))
        self.observations = json.loads((REGISTRY.parent / "evidence" / "ethereum-mainnet-1589.json").read_text(encoding="utf-8"))

    def test_the_exclusion_naming_unread_instances_is_gone(self):
        for exclusion in self.row["exclusions"]:
            self.assertNotIn("was not read", exclusion)
        self.assertEqual(self.row["instance_reads_completed_by"], "https://github.com/wildcat-finance/skills/issues/1589")

    def test_every_controller_and_market_address_is_a_row_contract(self):
        contracts = {c["address"].lower(): c for c in self.row["deployment"]["contracts"]}
        controllers = self.row["deployment"]["instances"]["controllers"]
        markets = self.row["deployment"]["instances"]["markets"]
        self.assertEqual(len(controllers), 3)
        self.assertEqual(len(markets), 7)
        for address in controllers + markets:
            with self.subTest(address=address):
                contract = contracts[address.lower()]
                self.assertTrue(contract["code_match"]["source_commit"])
                self.assertEqual(contract["code_match"]["source_commit"], self.row["source"]["commit"])

    def test_every_instance_reproduces_the_single_template_modulo_immutables(self):
        for entry in self.matches["controllers"] + self.matches["markets"]:
            with self.subTest(address=entry["address"]):
                self.assertEqual(entry["differing_bytes_outside_immutables"], 0)

    def test_there_is_exactly_one_template_per_role(self):
        finding = self.matches["immutable_template_finding"]
        self.assertIn("immutable", finding["market_init_code_hash"])
        self.assertIn("immutable", finding["controller_init_code_hash"])
        self.assertEqual(self.matches["reproduction_summary"]["instances_checked"], 10)
        self.assertTrue(self.matches["reproduction_summary"]["all_zero"])

    def test_the_observations_file_covers_every_instance_with_the_row_hash(self):
        contracts = {c["address"].lower(): c for c in self.row["deployment"]["contracts"]}
        self.assertEqual(self.observations["schema"], "wildcat.kickoff-targets.observations.v1")
        self.assertEqual(self.observations["chain_id"], 1)
        self.assertEqual(len(self.observations["code"]), 10)
        for entry in self.observations["code"]:
            with self.subTest(address=entry["address"]):
                contract = contracts[entry["address"].lower()]
                self.assertEqual(contract["code_keccak256"], entry["code_keccak256"])

    def test_the_factory_deployment_timestamp_correction_is_recorded(self):
        factory_deployment = self.matches.get("correction_note") or ""
        self.assertIn("1701383255", factory_deployment + json.dumps(self.matches))
        equivalence_note = self.row["source"]["equivalence_note"]
        self.assertIn("2023-11-30T22:27:35Z", equivalence_note)
        self.assertIn("corrected 2026-09-19", equivalence_note)


class AaveV3SourceRecoveryTests(unittest.TestCase):
    """The 2026-09-23 recovery (#1591) resolves Ethereum mainnet's main Aave V3 market."""

    POOL = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    CONFIGURATOR = "0x64b761d848206f447fe2dd461b0c635ec39ebb27"

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.row = next(t for t in self.registry["targets"] if t["id"] == "aave-v3")
        evidence = REGISTRY.parent / "evidence"
        self.observations = json.loads((evidence / "ethereum-mainnet-1591.json").read_text(encoding="utf-8"))
        self.matches = json.loads((evidence / "source-match-1591.json").read_text(encoding="utf-8"))
        self.ruling = json.loads((evidence / "scope-ruling-1591.json").read_text(encoding="utf-8"))
        self.sets = {s["id"]: s for s in self.matches["source_sets"]}

    def test_the_row_is_resolved_without_open_gaps(self):
        self.assertEqual(self.row["status"], "resolved")
        for key in ("blocker", "unresolved", "documentation_gap", "recovery"):
            self.assertNotIn(key, self.row)
        self.assertEqual(self.row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1591")

    def test_the_mainnet_ruling_is_bound_by_its_comment_digest(self):
        import hashlib
        body = self.ruling["comment_body"]
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), self.ruling["comment_body_sha256"])
        self.assertIn(self.ruling["ruling_quote"], body)
        self.assertEqual(self.ruling["applies_to"], ["aave-v3"])
        self.assertEqual(self.row["scope_ruling"]["reference"], self.ruling["reference"])
        self.assertEqual(self.row["deployment"]["chain_id"], 1)

    def test_every_listed_contract_names_a_reproduced_source_set_and_a_commit(self):
        contracts = self.row["deployment"]["contracts"]
        self.assertEqual(len(contracts), 22)
        listed = {m for s in self.sets.values() for m in s["reproduction"]["listed_members"]}
        self.assertEqual(listed, {c["address"] for c in contracts})
        code = {e["address"]: e for e in self.observations["code"]}
        for contract in contracts:
            with self.subTest(address=contract["address"]):
                match = contract["code_match"]
                self.assertRegex(match["source_commit"], r"\A[0-9a-f]{40}\Z")
                source_set = self.sets[match["source_set"]]
                self.assertEqual(match["source_commit"], source_set["commit"])
                self.assertEqual(match["reproduction"], source_set["reproduction"]["result"])
                self.assertEqual(contract["code_keccak256"], code[contract["address"]]["code_keccak256"])
                self.assertTrue(self.observations["creation"][contract["address"]]["proven"])

    def test_every_listed_source_set_reproduces_and_is_a_build_input(self):
        results = {s["reproduction"]["result"] for s in self.sets.values()}
        self.assertLessEqual(results, {"exact", "equal-except-cbor-metadata"})
        inputs = {i["sha256"] for i in self.row["source"]["build_inputs"]}
        self.assertEqual(inputs, {s["build_input_sha256"] for s in self.sets.values()})
        self.assertEqual(self.matches["summary"]["reproduction_by_address"], {"exact": 294, "equal-except-cbor-metadata": 62})

    def test_the_full_records_are_bound_by_commit_and_digest(self):
        full = self.row["full_records"]
        for key, document in (("observations", self.observations), ("source_match", self.matches)):
            with self.subTest(record=key):
                self.assertEqual(full[key], document["full_record"])
                self.assertEqual(full[key]["repository"], "https://github.com/wildcat-finance/miskatonic")
                self.assertRegex(full[key]["commit"], r"\A[0-9a-f]{40}\Z")
                self.assertRegex(full[key]["sha256"], r"\A[0-9a-f]{64}\Z")
        subjects = self.row["deployment"]["full_subject_set"]
        self.assertEqual(subjects["count"], 356)
        self.assertEqual(sum(subjects["by_role"].values()), 356)
        self.assertEqual(subjects["sha256"], self.observations["full_subject_set"]["sha256"])

    def test_the_pool_and_configurator_epochs_are_contiguous_and_match_the_provider(self):
        for key, proxy, event in (("pool_implementation_epochs", self.POOL, "PoolUpdated"),
                                  ("pool_configurator_implementation_epochs", self.CONFIGURATOR, "PoolConfiguratorUpdated")):
            with self.subTest(proxy=proxy):
                epochs = self.observations[key]
                for earlier, later in zip(epochs, epochs[1:]):
                    self.assertEqual(earlier["to_block"] + 1, later["from_block"])
                    self.assertLess(earlier["revision"], later["revision"])
                self.assertIsNone(epochs[-1]["to_block"])
                announced = [e["args"][1] for e in self.observations["provider_events"] if e["event"] == event]
                self.assertEqual(announced, [e["implementation"] for e in epochs])
        self.assertEqual([e["revision"] for e in self.observations["pool_implementation_epochs"]], list(range(1, 12)))

    def test_the_source_state_gaps_are_the_recorded_ones(self):
        gaps = self.matches["source_state_gaps"]
        self.assertEqual(len(gaps["target_not_in_public_history"]), 16)
        for gap in gaps["target_not_in_public_history"]:
            with self.subTest(source_set=gap["source_set"]):
                self.assertRegex(gap["closest"]["commit"], r"\A[0-9a-f]{40}\Z")
        self.assertEqual(self.row["source_state_gaps"]["target_not_in_public_history"], 16)
        self.assertEqual(len(gaps["files_not_at_chosen_commit"]), 4)
        self.assertEqual(len(gaps["verified_text_not_aave"]), 7)


class MapleSourceRecoveryTests(unittest.TestCase):
    """The 2026-09-28 recovery (#1592) resolves Maple's three families on Ethereum mainnet."""

    ROWS = {"maple-v1": ("v1",), "maple-v2-fixed-term": ("v2-fixed-term", "v2-core"),
            "maple-v2-open-term": ("v2-open-term", "v2-core")}

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.rows = {t["id"]: t for t in self.registry["targets"] if t["id"] in self.ROWS}
        evidence = REGISTRY.parent / "evidence"
        self.observations = json.loads((evidence / "ethereum-mainnet-1592.json").read_text(encoding="utf-8"))
        self.matches = json.loads((evidence / "source-match-1592.json").read_text(encoding="utf-8"))
        self.sets = {s["id"]: s for s in self.matches["source_sets"]}
        self.subjects = {s["address"]: s for s in self.observations["subjects"]}

    def test_every_row_is_resolved_without_open_gaps(self):
        self.assertEqual(set(self.rows), set(self.ROWS))
        for row in self.rows.values():
            with self.subTest(row=row["id"]):
                self.assertEqual(row["status"], "resolved")
                for key in ("blocker", "unresolved", "documentation_gap", "recovery"):
                    self.assertNotIn(key, row)
                self.assertEqual(row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1592")
                self.assertEqual(row["deployment"]["chain_id"], 1)
                self.assertEqual(row["scope_ruling"]["reference"],
                                 "https://github.com/wildcat-finance/skills/issues/1591#issuecomment-5791252047")

    def test_every_listed_contract_is_its_row_s_and_names_a_reproduced_set_and_commit(self):
        code = {e["address"]: e for e in self.observations["code"]}
        for row_id, families in self.ROWS.items():
            for contract in self.rows[row_id]["deployment"]["contracts"]:
                with self.subTest(row=row_id, address=contract["address"]):
                    subject = self.subjects[contract["address"]]
                    self.assertIn(subject["family"], families)
                    match = contract["code_match"]
                    self.assertRegex(match["source_commit"], r"\A[0-9a-f]{40}\Z")
                    source_set = self.sets[match["source_set"]]
                    self.assertEqual(match["source_commit"], source_set["commit"])
                    self.assertIn(contract["address"], source_set["reproduction"]["listed_members"])
                    self.assertIn(match["reproduction"], ("exact", "sans-cbor", "sans-embedded-cbor"))
                    self.assertEqual(contract["code_keccak256"], code[contract["address"]]["code_keccak256"])
                    self.assertTrue(self.observations["creation"][contract["address"]]["proven"])

    def test_every_listed_set_reproduces_and_is_a_build_input_of_its_rows(self):
        self.assertNotIn("differs", self.matches["summary"]["reproduction_by_address"])
        self.assertEqual(self.matches["summary"]["reproduction_by_address"],
                         {"exact": 343, "sans-cbor": 1023, "sans-embedded-cbor": 17})
        for row in self.rows.values():
            with self.subTest(row=row["id"]):
                used = {c["code_match"]["source_set"] for c in row["deployment"]["contracts"]}
                inputs = {i["sha256"] for i in row["source"]["build_inputs"]}
                self.assertEqual(inputs, {self.sets[k]["build_input_sha256"] for k in used})

    def test_the_full_records_are_bound_by_commit_and_digest(self):
        for row in self.rows.values():
            full = row["full_records"]
            for key, document in (("observations", self.observations), ("source_match", self.matches)):
                with self.subTest(row=row["id"], record=key):
                    self.assertEqual(full[key], document["full_record"])
                    self.assertEqual(full[key]["repository"], "https://github.com/wildcat-finance/miskatonic")
                    self.assertRegex(full[key]["commit"], r"\A[0-9a-f]{40}\Z")
                    self.assertRegex(full[key]["sha256"], r"\A[0-9a-f]{64}\Z")
        self.assertEqual(self.observations["full_subject_set"]["count"], 1389)
        counts = {row_id: self.rows[row_id]["deployment"]["full_subject_set"]["count"] for row_id in self.ROWS}
        self.assertEqual(counts, {"maple-v1": 700, "maple-v2-fixed-term": 248, "maple-v2-open-term": 603})

    def test_every_listed_proxy_s_epochs_are_contiguous_and_end_at_its_slot(self):
        end = self.observations["observations"][0]["block"]["number"]
        for address, record in self.observations["implementation_epochs"].items():
            with self.subTest(proxy=address):
                epochs = record["epochs"]
                self.assertEqual(epochs[0]["from_block"], self.observations["creation"][address]["block"])
                for earlier, later in zip(epochs, epochs[1:]):
                    self.assertEqual(earlier["to_block"] + 1, later["from_block"])
                self.assertEqual(epochs[-1]["to_block"], end)
                self.assertTrue(record["slot_agrees"])

    def test_the_source_state_gaps_are_the_recorded_ones(self):
        gaps = self.matches["source_state_gaps"]
        self.assertEqual(len(gaps["no_public_source"]), 6)
        self.assertEqual(len(gaps["target_text_at_no_public_commit"]), 8)
        missing = {g["address"] for g in gaps["no_public_source"]}
        for row in self.rows.values():
            with self.subTest(row=row["id"]):
                listed = {c["address"] for c in row["deployment"]["contracts"]}
                self.assertFalse(missing & listed)
                self.assertTrue(set(row["source_state_gaps"]["no_public_source"]) <= missing)
        self.assertEqual(self.rows["maple-v1"]["source_state_gaps"]["no_public_source"], [])



class EulerSourceRecoveryTests(unittest.TestCase):
    """The 2026-09-28 recovery (#1593) resolves Euler V1 and V2 on Ethereum mainnet."""

    ROWS = {"euler-v1": "v1", "euler-v2": "v2"}

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.rows = {t["id"]: t for t in self.registry["targets"] if t["id"] in self.ROWS}
        evidence = REGISTRY.parent / "evidence"
        self.observations = json.loads((evidence / "ethereum-mainnet-1593.json").read_text(encoding="utf-8"))
        self.matches = json.loads((evidence / "source-match-1593.json").read_text(encoding="utf-8"))
        self.sets = {s["id"]: s for s in self.matches["source_sets"]}
        self.subjects = {s["address"]: s for s in self.observations["subjects"]}

    def test_both_rows_are_resolved_without_open_gaps(self):
        self.assertEqual(set(self.rows), set(self.ROWS))
        for row in self.rows.values():
            with self.subTest(row=row["id"]):
                self.assertEqual(row["status"], "resolved")
                for key in ("blocker", "unresolved", "documentation_gap", "recovery"):
                    self.assertNotIn(key, row)
                self.assertEqual(row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1593")
                self.assertEqual(row["deployment"]["chain_id"], 1)
                self.assertEqual(row["scope_ruling"]["reference"],
                                 "https://github.com/wildcat-finance/skills/issues/1591#issuecomment-5791252047")
                self.assertEqual(row["scope_decision"]["date"], "2026-09-28")

    def test_every_listed_contract_is_its_row_s_and_names_a_reproduced_set_and_commit(self):
        code = {e["address"]: e for e in self.observations["code"]}
        for row_id, family in self.ROWS.items():
            for contract in self.rows[row_id]["deployment"]["contracts"]:
                with self.subTest(row=row_id, address=contract["address"]):
                    subject = self.subjects[contract["address"]]
                    self.assertEqual(subject["family"], family)
                    match = contract["code_match"]
                    self.assertRegex(match["source_commit"], r"\A[0-9a-f]{40}\Z")
                    source_set = self.sets[match["source_set"]]
                    self.assertEqual(match["source_commit"], source_set["commit"])
                    self.assertEqual(match["commit_basis"], source_set["commit_basis"])
                    self.assertIn(contract["address"], source_set["reproduction"]["listed_members"])
                    self.assertIn(match["reproduction"], ("exact", "sans-cbor"))
                    self.assertEqual(contract["code_keccak256"], code[contract["address"]]["code_keccak256"])
                    self.assertTrue(self.observations["creation"][contract["address"]]["proven"])

    def test_every_listed_set_reproduces_and_is_a_build_input_of_its_rows(self):
        self.assertEqual(self.matches["summary"]["reproduction_by_address"], {"exact": 2684, "sans-cbor": 699})
        self.assertEqual(self.matches["summary"]["reproduced_subjects"], 3383)
        for row in self.rows.values():
            with self.subTest(row=row["id"]):
                used = {c["code_match"]["source_set"] for c in row["deployment"]["contracts"]}
                inputs = {i["sha256"] for i in row["source"]["build_inputs"]}
                self.assertEqual(inputs, {self.sets[k]["build_input_sha256"] for k in used})

    def test_the_full_records_are_bound_by_commit_and_digest(self):
        for row in self.rows.values():
            full = row["full_records"]
            for key, document in (("observations", self.observations), ("source_match", self.matches)):
                with self.subTest(row=row["id"], record=key):
                    self.assertEqual(full[key], document["full_record"])
                    self.assertEqual(full[key]["repository"], "https://github.com/wildcat-finance/miskatonic")
                    self.assertRegex(full[key]["commit"], r"\A[0-9a-f]{40}\Z")
                    self.assertRegex(full[key]["sha256"], r"\A[0-9a-f]{64}\Z")
        self.assertEqual(self.observations["full_subject_set"]["count"], 3383)
        counts = {row_id: self.rows[row_id]["deployment"]["full_subject_set"]["count"] for row_id in self.ROWS}
        self.assertEqual(counts, {"euler-v1": 324, "euler-v2": 3059})
        listed = {row_id: len(self.rows[row_id]["deployment"]["contracts"]) for row_id in self.ROWS}
        self.assertEqual(listed, {"euler-v1": 59, "euler-v2": 53})

    def test_every_listed_v1_proxy_follows_its_module_to_the_module_table(self):
        end = self.observations["observations"][0]["block"]["number"]
        proxies = self.observations["implementation_epochs"]
        self.assertEqual(len(proxies), 8)
        for address, record in proxies.items():
            with self.subTest(proxy=address):
                self.assertEqual(record["kind"], "v1-dispatcher-proxy")
                epochs = record["epochs"]
                self.assertEqual(epochs[0]["from_block"], self.observations["creation"][address]["block"])
                for earlier, later in zip(epochs, epochs[1:]):
                    self.assertEqual(earlier["to_block"] + 1, later["from_block"])
                self.assertEqual(epochs[-1]["to_block"], end)
                self.assertTrue(record["table_agrees"])
                module = self.observations["v1_module_epochs"][str(record["module_id"])]
                self.assertEqual(epochs[-1]["implementation"], module[-1]["implementation"])

    def test_the_source_state_gaps_are_the_recorded_ones(self):
        gaps = self.matches["source_state_gaps"]
        self.assertEqual(gaps["no_public_source"], [])
        self.assertEqual(len(gaps["target_text_at_no_public_commit"]), 16)
        self.assertEqual(len(gaps["chosen_commit_on_a_pull_request_only"]), 3)
        self.assertEqual(len(self.rows["euler-v1"]["source_state_gaps"]["no_commit"]), 7)
        for row in self.rows.values():
            with self.subTest(row=row["id"]):
                listed = {c["address"] for c in row["deployment"]["contracts"]}
                self.assertFalse(set(row["source_state_gaps"]["no_commit"]) & listed)


class CentrifugeSourceRecoveryTests(unittest.TestCase):
    """The 2026-09-28 recovery (#1594) resolves Centrifuge V3 on Ethereum mainnet."""

    V2_TOKENS = {"0x5a0f93d040de44e78f251b03c43be9cf317dcf64", "0x8c213ee79581ff4984583c6a801e5263418c4b86"}

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.row = next(t for t in self.registry["targets"] if t["id"] == "centrifuge-v3")
        evidence = REGISTRY.parent / "evidence"
        self.observations = json.loads((evidence / "ethereum-mainnet-1594.json").read_text(encoding="utf-8"))
        self.matches = json.loads((evidence / "source-match-1594.json").read_text(encoding="utf-8"))
        self.sets = {s["id"]: s for s in self.matches["source_sets"]}
        self.subjects = {s["address"]: s for s in self.observations["subjects"]}
        self.listed = {c["address"]: c for c in self.row["deployment"]["contracts"]}

    def test_the_row_is_resolved_without_open_gaps(self):
        self.assertEqual(self.row["status"], "resolved")
        for key in ("blocker", "unresolved", "documentation_gap", "recovery"):
            self.assertNotIn(key, self.row)
        self.assertEqual(self.row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1594")
        self.assertEqual(self.row["deployment"]["chain_id"], 1)
        self.assertEqual(self.row["scope_ruling"]["reference"],
                         "https://github.com/wildcat-finance/skills/issues/1591#issuecomment-5791252047")
        self.assertEqual(self.row["scope_decision"]["date"], "2026-09-28")
        self.assertFalse([t["id"] for t in self.registry["targets"] if t["status"] == "blocked"])

    def test_every_listed_contract_names_a_reproduced_set_and_commit(self):
        code = {e["address"]: e for e in self.observations["code"]}
        self.assertEqual(set(self.listed), set(self.subjects))
        for address, contract in self.listed.items():
            with self.subTest(address=address):
                match = contract["code_match"]
                self.assertRegex(match["source_commit"], r"\A[0-9a-f]{40}\Z")
                source_set = self.sets[match["source_set"]]
                self.assertEqual(match["source_commit"], source_set["commit"])
                self.assertEqual(match["commit_basis"], source_set["commit_basis"])
                self.assertIn(address, source_set["reproduction"]["listed_members"])
                self.assertIn(match["reproduction"], ("exact", "sans-cbor"))
                self.assertEqual(contract["code_keccak256"], code[address]["code_keccak256"])
                self.assertTrue(self.observations["creation"][address]["proven"])

    def test_every_listed_set_is_a_build_input_of_the_row(self):
        self.assertEqual(self.matches["summary"]["reproduction_by_address"], {"exact": 239, "sans-cbor": 30})
        self.assertEqual(self.matches["summary"]["reproduced_subjects"], 269)
        used = {c["code_match"]["source_set"] for c in self.listed.values()}
        inputs = {i["sha256"] for i in self.row["source"]["build_inputs"]}
        self.assertEqual(inputs, {self.sets[k]["build_input_sha256"] for k in used})

    def test_the_full_records_are_bound_by_commit_and_digest(self):
        full = self.row["full_records"]
        for key, document in (("observations", self.observations), ("source_match", self.matches)):
            with self.subTest(record=key):
                self.assertEqual(full[key], document["full_record"])
                self.assertEqual(full[key]["repository"], "https://github.com/wildcat-finance/miskatonic")
                self.assertRegex(full[key]["commit"], r"\A[0-9a-f]{40}\Z")
                self.assertRegex(full[key]["sha256"], r"\A[0-9a-f]{64}\Z")
        subject_set = self.row["deployment"]["full_subject_set"]
        self.assertEqual(subject_set["count"], 271)
        self.assertEqual(subject_set["sha256"], self.observations["full_subject_set"]["sha256"])
        self.assertEqual(subject_set["families"], {"spell": 9, "v3.0": 86, "v3.1": 164, "v3.2": 12})
        self.assertEqual(len(self.listed), 110)

    def test_jaaa_jtrsy_and_their_hooks_are_listed(self):
        self.assertLessEqual(self.V2_TOKENS, set(self.listed))
        hooks = {a for a, c in self.listed.items() if c["role"] == "hook"}
        self.assertEqual(len(hooks), 2)
        for token in self.V2_TOKENS:
            with self.subTest(token=token):
                self.assertTrue(any(any(v.endswith(f"hook():{token}") for v in self.subjects[h]["via"])
                                    for h in hooks))
        self.assertEqual(self.row["companion_repository"]["repository"], "https://github.com/centrifuge/liquidity-pools")

    def test_every_ethereum_share_token_and_vault_in_the_pool_inventory_is_a_subject(self):
        inventory = self.observations["pool_inventory"]
        self.assertEqual(inventory["summary"]["pools"], len(inventory["pools"]))
        tokens, vaults = 0, 0
        for pool_id, pool in inventory["pools"].items():
            self.assertEqual(int(pool_id) >> 48, pool["hub_centrifuge_id"])
            for share_class in pool["share_classes"].values():
                if share_class["token"]:
                    tokens += 1
                    self.assertTrue(share_class["token_is_subject"])
                for vault in share_class["vaults"]:
                    vaults += 1
                    self.assertTrue(vault["vault_is_subject"])
        self.assertEqual((tokens, vaults), (inventory["summary"]["share_classes_on_ethereum"],
                                            inventory["summary"]["vaults"]))

    def test_the_source_state_gaps_are_the_recorded_ones(self):
        gaps = self.matches["source_state_gaps"]
        self.assertEqual(len(gaps["target_text_at_no_public_commit"]), 4)
        self.assertEqual(len(gaps["chosen_commit_on_a_pull_request_only"]), 2)
        unreproduced = {g["address"] for g in gaps["no_reproduction"]}
        self.assertEqual(unreproduced, set(self.row["source_state_gaps"]["no_commit"]))
        self.assertEqual(len(unreproduced), 2)
        self.assertFalse(unreproduced & set(self.listed))


class MorphoSourceRecoveryTests(unittest.TestCase):
    """The 2026-09-29 recovery (#1996) resolves Morpho's three rows on Ethereum mainnet, in an amended sixth slot."""

    ROWS = ("morpho-optimizers", "morpho-blue", "morpho-midnight")

    def setUp(self):
        self.registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.rows = {t["id"]: t for t in self.registry["targets"] if t["id"] in self.ROWS}
        evidence = REGISTRY.parent / "evidence"
        self.observations = json.loads((evidence / "ethereum-mainnet-1996.json").read_text(encoding="utf-8"))
        self.matches = json.loads((evidence / "source-match-1996.json").read_text(encoding="utf-8"))
        self.sets = {s["id"]: s for s in self.matches["source_sets"]}
        self.subjects = {s["address"]: s for s in self.observations["subjects"]}
        self.listed = {c["address"]: (row_id, c) for row_id, row in self.rows.items()
                       for c in row["deployment"]["contracts"]}

    def test_the_rows_fill_the_amended_sixth_slot(self):
        (amendment,) = self.registry["scope"]["amendments"]
        self.assertEqual((amendment["order"], amendment["venue"], amendment["targets"]), (6, "Morpho", list(self.ROWS)))
        record = json.loads((ROOT / amendment["evidence"]).read_text(encoding="utf-8"))
        self.assertEqual(record["recorded_by"], "laurenceday")
        self.assertTrue(record["reference"].startswith("https://github.com/wildcat-finance/skills/issues/1996#issuecomment-"))
        decision = next(d for d in self.registry["decisions"] if d["id"] == amendment["decision"])
        self.assertEqual(decision["decision_maker"], record["decision_maker"])
        consumer = next(c for c in self.registry["consumers"] if c["issue"] == 1359)
        self.assertEqual(consumer["targets"][-3:], list(self.ROWS))

    def test_the_rows_are_resolved_without_open_gaps(self):
        self.assertEqual(set(self.rows), set(self.ROWS))
        for row_id, row in self.rows.items():
            with self.subTest(row=row_id):
                self.assertEqual((row["status"], row["venue"], row["decision"]), ("resolved", "Morpho", "kickoff-morpho-venue"))
                for key in ("blocker", "unresolved", "documentation_gap", "recovery"):
                    self.assertNotIn(key, row)
                self.assertEqual(row["recovery_completed_by"], "https://github.com/wildcat-finance/skills/issues/1996")
                self.assertEqual(row["deployment"]["chain_id"], 1)
                self.assertEqual(row["deployment"]["observed_block"]["number"], 26022093)
                self.assertEqual(row["scope_ruling"]["reference"],
                                 "https://github.com/wildcat-finance/skills/issues/1591#issuecomment-5791252047")
                self.assertEqual(row["scope_decision"]["date"], "2026-09-28")

    def test_every_listed_contract_names_a_reproduced_set_and_commit(self):
        code = {e["address"]: e for e in self.observations["code"]}
        self.assertEqual(set(self.listed), set(self.subjects))
        for address, (row_id, contract) in self.listed.items():
            with self.subTest(address=address):
                self.assertEqual(self.subjects[address]["registry_row"], row_id)
                match = contract["code_match"]
                self.assertRegex(match["source_commit"], r"\A[0-9a-f]{40}\Z")
                source_set = self.sets[match["source_set"]]
                self.assertEqual(match["source_commit"], source_set["commit"])
                self.assertEqual(match["commit_basis"], source_set["commit_basis"])
                self.assertIn(address, source_set["reproduction"]["listed_members"])
                self.assertIn(match["reproduction"], ("exact", "sans-cbor"))
                self.assertEqual(contract["code_keccak256"], code[address]["code_keccak256"])
                self.assertTrue(self.observations["creation"][address]["proven"])

    def test_every_listed_set_is_a_build_input_of_its_row(self):
        self.assertEqual(self.matches["summary"]["reproduction_by_address"], {"exact": 3148, "sans-cbor": 57})
        self.assertEqual(self.matches["summary"]["reproduced_subjects"], 3205)
        for row_id, row in self.rows.items():
            with self.subTest(row=row_id):
                used = {c["code_match"]["source_set"] for c in row["deployment"]["contracts"]}
                inputs = {i["sha256"] for i in row["source"]["build_inputs"]}
                self.assertEqual(inputs, {self.sets[k]["build_input_sha256"] for k in used})

    def test_the_full_records_are_bound_by_commit_and_digest(self):
        for row_id, row in self.rows.items():
            full = row["full_records"]
            for key, document in (("observations", self.observations), ("source_match", self.matches)):
                with self.subTest(row=row_id, record=key):
                    self.assertEqual(full[key], document["full_record"])
                    self.assertEqual(full[key]["repository"], "https://github.com/wildcat-finance/miskatonic")
                    self.assertRegex(full[key]["commit"], r"\A[0-9a-f]{40}\Z")
                    self.assertRegex(full[key]["sha256"], r"\A[0-9a-f]{64}\Z")
        counts = {row_id: row["deployment"]["full_subject_set"]["count"] for row_id, row in self.rows.items()}
        self.assertEqual(counts, {"morpho-optimizers": 83, "morpho-blue": 3106, "morpho-midnight": 16})
        self.assertEqual(sum(counts.values()), self.observations["full_subject_set"]["count"])
        self.assertEqual(self.rows["morpho-blue"]["deployment"]["full_subject_set"]["groups"],
                         {"A": 2, "B": 1071, "C": 477, "D": 1434, "E": 122})
        self.assertEqual({row_id: len(row["deployment"]["contracts"]) for row_id, row in self.rows.items()},
                         {"morpho-optimizers": 81, "morpho-blue": 33, "morpho-midnight": 7})

    def test_blue_matches_its_release_commit(self):
        blue = self.listed["0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb"][1]
        self.assertEqual(blue["code_match"]["source_commit"], "55d2d99304fb3fb930c688462ae2ccabb1d533ad")
        self.assertEqual(self.sets[blue["code_match"]["source_set"]]["commit_tags"], ["v1.0.0"])

    def test_every_proxy_epoch_is_contiguous_and_ends_at_its_slot(self):
        epochs = self.observations["implementation_epochs"]
        self.assertEqual((len(epochs), sum(len(p["epochs"]) for p in epochs.values())), (19, 70))
        for proxy, record in epochs.items():
            with self.subTest(proxy=proxy):
                self.assertIn(proxy, self.listed)
                spans = record["epochs"]
                self.assertEqual(spans[0]["from_block"], self.observations["creation"][proxy]["block"])
                for earlier, later in zip(spans, spans[1:]):
                    self.assertEqual(later["from_block"], earlier["to_block"] + 1)
                self.assertEqual(spans[-1]["to_block"], 26022093)
                self.assertEqual(spans[-1]["implementation"], record["slot_at_end"])

    def test_the_source_state_gaps_are_the_recorded_ones(self):
        gaps = self.matches["source_state_gaps"]
        self.assertEqual(gaps["no_reproduction"], [])
        self.assertEqual(gaps["chosen_commit_on_a_pull_request_only"], [])
        no_commit = [a for row in self.rows.values() for a in row["source_state_gaps"]["no_commit"]]
        self.assertEqual(len(no_commit), len(set(no_commit)))
        self.assertEqual(len(no_commit), 13)
        self.assertFalse(set(no_commit) & set(self.listed))


if __name__ == "__main__":
    unittest.main()
