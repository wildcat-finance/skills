"""Hold the issue 1355 inventory checker to its refusals.

The committed inventory, document copies and profile-invariance evidence must
pass `check`. Each mutation case copies the committed inputs into a scratch
root, breaks one thing, and asserts the refusal names the record and field that
failed, so a checker that accepted everything would fail here.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "kickoff_hermes_1355.py"


def load_module():
    spec = importlib.util.spec_from_file_location("kickoff_hermes_1355", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = load_module()
INPUTS = (
    checker.DOCS,
    checker.REGISTRY_PATH,
    checker.SOURCIFY_PATH,
    checker.HERMES,
    # The rule corpus the Hermes baseline records and the checker re-hashes.
    checker.CORPUS,
    # The registry evidence the role provider's source override is bound to.
    "docs/kickoff/1359/evidence/source-match-1590.json",
    # The recorded inputs the fixture, release and owner-handoff records bind.
    checker.OBSERVATIONS_PATH,
    checker.SCOPE_PATH,
)
ROLE_PROVIDER = "open-access-role-provider"


def canonical(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


class CommittedEvidenceTests(unittest.TestCase):
    def test_committed_tree_passes_check(self):
        result = checker.check(ROOT)
        self.assertEqual(result["addresses"], 137)
        self.assertEqual(result["types"], 17)
        self.assertEqual(result["exclusions"], 8)
        invariance = result["profile_invariance"]
        self.assertEqual(invariance["types"], 17)
        self.assertEqual(invariance["invariant"], invariance["comparisons"])
        self.assertGreaterEqual(invariance["comparisons"], 17)
        chain = result["chain_evidence"]
        self.assertEqual(chain["fixture"]["proved"], 137)
        self.assertEqual(chain["fixture"]["recorded_registry_equal_to_proved"], 137)
        self.assertEqual(chain["fixture"]["recorded_observation_equal_to_proved"], 137)
        self.assertEqual(chain["release"]["components"], 8)
        self.assertEqual(chain["handoffs"]["handed_off"], 7)
        self.assertEqual(chain["handoffs"]["complete"], 6)
        self.assertEqual(chain["handoffs"]["review_outstanding"], 1)

    def test_inventory_handoff_states_its_maintainer_review_is_outstanding(self):
        record = json.loads((ROOT / checker.HANDOFFS_RECORD).read_text(encoding="utf-8"))
        inventory = [row for row in record["rows"] if row["handoff"] == "inventory"]
        self.assertEqual([row["status"] for row in inventory], ["target-maintainer-review-outstanding"])


class ScratchCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in INPUTS:
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)

    def load(self, relative):
        return json.loads((self.root / relative).read_text(encoding="utf-8"))

    def save(self, relative, value):
        (self.root / relative).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def edit_inventory(self, change):
        value = self.load(checker.INVENTORY)
        change(value)
        self.save(checker.INVENTORY, value)

    def edit_evidence(self, change):
        value = self.load(checker.PROFILE_EVIDENCE)
        change(value)
        self.save(checker.PROFILE_EVIDENCE, value)

    def refused(self, *needles, call=None):
        with self.assertRaises(checker.Refusal) as caught:
            (call or (lambda: checker.check(self.root)))()
        joined = "\n".join(caught.exception.findings)
        for needle in needles:
            self.assertIn(needle, joined)
        return joined


class InventoryRefusalTests(ScratchCase):
    def test_scratch_copy_passes(self):
        self.assertEqual(checker.check(self.root)["status"], "ok")

    def test_missing_address_is_named(self):
        removed = {}

        def change(value):
            removed["address"] = value["addresses"].pop(5)["address"]

        self.edit_inventory(change)
        self.refused(f"record=inventory.addresses.{removed['address']} field=address registry contract is missing",
                     "maps 136 addresses")

    def test_duplicate_address_is_refused(self):
        self.edit_inventory(lambda value: value["addresses"].append(copy.deepcopy(value["addresses"][0])))
        self.refused("field=address is duplicated")

    def test_address_outside_the_registry_is_refused(self):
        def change(value):
            value["addresses"][0]["address"] = "0x" + "ab" * 20

        self.edit_inventory(change)
        self.refused("is not a wildcat-v2-ethereum-mainnet registry contract", checker.REGISTRY_SHA256)

    def test_address_mapped_to_the_wrong_type_is_refused(self):
        def change(value):
            market = next(a for a in value["addresses"] if a["role"] == "market")
            market["type"] = "open-term-hooks"

        self.edit_inventory(change)
        self.refused("field=type is open-term-hooks, the registry role and source make it wildcat-market")

    def test_type_whose_anchor_is_not_an_anchor_tree_is_refused(self):
        def change(value):
            item = next(t for t in value["types"] if t["id"] == "hooks-factory")
            item["anchor"] = "v2-a70f"

        self.edit_inventory(change)
        self.refused("record=inventory.types.hooks-factory field=anchor v2-a70f is not an anchor tree")

    def test_type_without_anchor_or_coverage_mode_is_refused(self):
        def change(value):
            del value["types"][0]["anchor"]
            del value["types"][1]["coverage"]

        self.edit_inventory(change)
        joined = self.refused("field=anchor missing", "field=coverage missing")
        self.assertIn("record=inventory.types[0]", joined)

    def test_coverage_mode_must_follow_the_anchor(self):
        def change(value):
            item = next(t for t in value["types"] if t["id"] == "wildcat-market")
            item["coverage"] = "native"

        self.edit_inventory(change)
        self.refused("record=inventory.types.wildcat-market field=coverage is native")

    def test_unowned_exclusion_is_refused(self):
        def change(value):
            value["exclusions"][2]["owner"] = ""

        self.edit_inventory(change)
        self.refused("record=inventory.exclusions[2] field=owner", "differs from the registry's protected_set_exclusions")

    def test_dropped_exclusion_is_refused(self):
        self.edit_inventory(lambda value: value["exclusions"].pop())
        self.refused("keeps 7 exclusions")

    def test_tree_commit_must_match_the_study(self):
        def change(value):
            value["trees"]["v2-c7be"]["zero_loss_exclusions"].append("test/market/WildcatMarket.t.sol")

        self.edit_inventory(change)
        self.refused("record=inventory.trees.v2-c7be field=zero_loss_exclusions")

    def test_deployed_profile_must_match_the_registry_and_sourcify(self):
        def change(value):
            item = next(t for t in value["types"] if t["id"] == "wrapper-factory")
            item["deployed_profile"] = "solc-0.8.25-cancun-ir-200"
            wrapper = next(t for t in value["types"] if t["id"] == "wrapper")
            wrapper["deployed_profile"] = "solc-0.8.25-cancun-ir-200"

        self.edit_inventory(change)
        self.refused("record=inventory.types.wrapper-factory field=deployed_profile",
                     "disagrees with sourcify 0xea6de11f8f3f83c79bd9d8db5517fcfdf2bb148a")

    def test_non_string_fields_refuse_rather_than_crash(self):
        def change(value):
            value["addresses"][0]["type"] = ["wildcat-market"]
            value["types"][0]["anchor"] = {"tree": "v2-c7be"}

        self.edit_inventory(change)
        self.refused("must be strings", "must be a string")


class DigestRefusalTests(ScratchCase):
    def test_study_copy_digest_mismatch_is_named(self):
        path = self.root / checker.DOCS / "study.md"
        path.write_bytes(path.read_bytes() + b"\n")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        self.refused("record=inventory.documents.study field=sha256", f"digest={actual}")

    def test_design_report_digest_mismatch_is_named(self):
        path = self.root / checker.DOCS / "design-reports" / "anchor-and-inspect-gate1-runs.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        value["value"] = 4
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.refused("record=design-evidence.anchor-and-inspect/gate1-runs field=report.sha256")

    def test_unlisted_design_report_is_refused(self):
        (self.root / checker.DOCS / "design-reports" / "extra.json").write_text("{}\n", encoding="utf-8")
        self.refused("design-reports/extra.json is not a resolved cell")

    def test_registry_digest_mismatch_is_refused(self):
        path = self.root / checker.REGISTRY_PATH
        path.write_bytes(path.read_bytes().replace(b'"resolved"', b'"resolvedx"', 1))
        self.refused("record=registry field=sha256")


class CustodyRefusalTests(ScratchCase):
    def test_path_escape_is_refused(self):
        self.refused("path escapes the repository",
                     call=lambda: checker.read_bytes(self.root, "docs/../../outside.json", "probe"))

    def test_symlinked_inventory_is_refused(self):
        inventory = self.root / checker.INVENTORY
        moved = self.root / "inventory-real.json"
        inventory.rename(moved)
        os.symlink(moved, inventory)
        self.refused("record=inventory field=path")

    def test_symlink_under_docs_tree_is_refused(self):
        os.symlink(self.root / checker.REGISTRY_PATH, self.root / checker.DOCS / "evidence" / "linked.json")
        self.refused("record=custody field=path docs/kickoff/1355/evidence/linked.json is a symlink")

    def test_target_source_under_docs_tree_is_refused(self):
        (self.root / checker.DOCS / "evidence" / "HooksFactory.sol").write_text(
            "// SPDX-License-Identifier: MIT\npragma solidity 0.8.25;\n", encoding="utf-8")
        (self.root / checker.DOCS / "evidence" / "copied.json").write_text(
            '{"x": 1}\npragma solidity ^0.8.0;\n', encoding="utf-8")
        (self.root / checker.DOCS / "baseline-sources").mkdir()
        joined = self.refused("HooksFactory.sol has suffix .sol", "copied.json carries Solidity source text",
                              "baseline-sources is a target or Hermes source directory name")
        self.assertIn("record=custody", joined)

    def test_solidity_inside_a_json_string_is_refused(self):
        # A standard-JSON input escapes each source into one string, so no
        # line of the raw bytes starts with the pragma and no SPDX line is needed.
        planted = {"language": "Solidity",
                   "sources": {"src/X.sol": {"content": "pragma solidity 0.8.25;\ncontract X { uint256 a; }\n"}}}
        (self.root / checker.DOCS / "evidence" / "standard-input.json").write_text(json.dumps(planted), encoding="utf-8")
        self.refused("record=custody field=path docs/kickoff/1355/evidence/standard-input.json carries Solidity source text")

    def test_escaped_solidity_inside_a_markdown_file_is_refused(self):
        # A standard-JSON input pasted into Markdown keeps its escaped newlines,
        # so no line of the file starts with the pragma.
        (self.root / checker.DOCS / "evidence" / "notes.md").write_text(
            'Input: `{"content": "pragma solidity 0.8.25;\\ncontract X {}\\n"}`\n', encoding="utf-8")
        self.refused("record=custody field=path docs/kickoff/1355/evidence/notes.md carries Solidity source text")

    def test_prose_naming_the_pragma_keyword_is_not_source(self):
        (self.root / checker.DOCS / "evidence" / "notes.md").write_text(
            "The custody scan looks for a `pragma solidity` line.\n", encoding="utf-8")
        self.assertEqual(checker.check(self.root)["status"], "ok")

    def test_private_source_digest_under_docs_tree_is_refused(self):
        planted = self.root / checker.DOCS / "evidence" / "notes.md"
        planted.write_text("private body\n", encoding="utf-8")
        digest = hashlib.sha256(planted.read_bytes()).hexdigest()
        findings = checker.validate_custody(self.root, {digest})
        self.assertEqual(len(findings), 1)
        self.assertIn(f"is a private-repository source file digest={digest}", findings[0])

    def test_registry_private_build_inputs_feed_the_custody_digests(self):
        registry = json.loads((ROOT / checker.REGISTRY_PATH).read_text(encoding="utf-8"))
        row = next(r for r in registry["targets"] if r["id"] == checker.REGISTRY_ROW)
        digests = checker.private_digests(row)
        self.assertIn("07bc4c91edb64b1255d61173c35e0523ee33f12f49a59d320834256f510e3b9d", digests)
        self.assertIn("6357b167846ba49110ede1a76ad7fa5fc85beec5f8ba5f0e4be8da6fc319d35d", digests)


class RegistrySourceOverrideTests(ScratchCase):
    def edit_override(self, change):
        def edit(value):
            item = next(t for t in value["types"] if t["id"] == ROLE_PROVIDER)
            change(item["registry_source_override"])

        self.edit_inventory(edit)

    def test_override_digest_must_match_the_registry_sourcify_evidence(self):
        self.edit_override(lambda override: override.update(sourcify_source_sha256="0" * 64))
        self.refused(f"record=inventory.types.{ROLE_PROVIDER}.registry_source_override "
                     f"field=sourcify_source_sha256 is '{'0' * 64}', the registry's Sourcify evidence records "
                     "'7a5b57852f433b876f0b43048c74158a740ce0f2708587b31eb682a7c390f84f'")

    def test_override_without_a_sourcify_digest_is_refused(self):
        self.edit_override(lambda override: override.pop("sourcify_source_sha256", None))
        self.refused(f"record=inventory.types.{ROLE_PROVIDER}.registry_source_override field=sourcify_source_sha256 missing")


class ProfileInvarianceRefusalTests(ScratchCase):
    def test_profiles_that_disagree_are_refused_with_both_digests(self):
        state = {}

        def change(value):
            record = next(r for r in value["records"] if r["type"] == "wildcat-market" and r["state"] == "anchor")
            original = value["blobs"][record["deployed"]["storage_layout_sha256"]]
            altered = copy.deepcopy(original)
            altered["storage"][0]["slot"] = "99"
            digest = hashlib.sha256(canonical(altered).encode("utf-8")).hexdigest()
            value["blobs"][digest] = altered
            state["default"] = record["default"]["storage_layout_sha256"]
            state["deployed"] = digest
            record["deployed"]["storage_layout_sha256"] = digest

        self.edit_evidence(change)
        self.refused("record=profile-invariance.records.wildcat-market/anchor field=storage_layout_sha256",
                     f"default profile {state['default']}",
                     f"deployed profile solc-0.8.25-cancun-ir-50000 {state['deployed']}")

    def test_map_content_is_checked_not_only_its_digest(self):
        def change(value):
            key = next(iter(value["blobs"]))
            if isinstance(value["blobs"][key], dict) and "storage" in value["blobs"][key]:
                value["blobs"][key]["storage"] = []
            else:
                value["blobs"][key]["tampered()"] = "00000000"

        self.edit_evidence(change)
        self.refused("field=sha256 the canonical content does not hash to its key")

    def test_missing_comparison_is_refused(self):
        def change(value):
            value["records"] = [r for r in value["records"] if r["type"] != "fee-recipient"]

        self.edit_evidence(change)
        self.refused("record=profile-invariance.records.fee-recipient/deployed field=type no profile comparison")

    def test_deployed_build_that_did_not_resolve_the_profile_is_refused(self):
        def change(value):
            build = next(b for b in value["builds"] if b["id"] == "v2-a70f/solc-0.8.25-cancun-ir-50000")
            build["resolved_config"]["via_ir"] = False

        self.edit_evidence(change)
        self.refused("record=profile-invariance.builds.v2-a70f/solc-0.8.25-cancun-ir-50000 field=resolved_config")

    def test_compiled_settings_must_match_the_build(self):
        def change(value):
            record = next(r for r in value["records"] if r["type"] == "arch-controller" and r["state"] == "deployed")
            record["deployed"]["compiled_settings"]["optimizer_runs"] = 999

        self.edit_evidence(change)
        self.refused("record=profile-invariance.records.arch-controller/deployed.deployed field=compiled_settings")

    def test_changed_canonicaliser_is_refused(self):
        path = self.root / checker.HERMES
        path.write_bytes(path.read_bytes() + b"\n")
        self.refused("field=canonicaliser.sha256")


class ConformanceTests(ScratchCase):
    report = ".hexaemeron/design-reports/anchor-and-inspect-profile-invariance.json"

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = checker.main(list(argv), root=self.root)
        return code, out.getvalue(), err.getvalue()

    def test_profile_invariance_report_is_written_once(self):
        code, out, _ = self.run_main("conformance", "--criterion", "profile-invariance",
                                     "--candidate", "anchor-and-inspect", "--report", self.report)
        self.assertEqual(code, 0)
        report = json.loads((self.root / self.report).read_text(encoding="utf-8"))
        self.assertEqual(report, {
            "schema": "protasis-design-report/v1", "candidate": "anchor-and-inspect",
            "criterion": "profile-invariance", "value": True, "unit": "boolean", "exit": 0,
            "command": ("python3 scripts/kickoff_hermes_1355.py conformance --criterion profile-invariance "
                        "--candidate anchor-and-inspect --report " + self.report),
        })
        self.assertEqual(json.loads(out)["value"], True)
        code, _, err = self.run_main("conformance", "--criterion", "profile-invariance",
                                     "--candidate", "anchor-and-inspect", "--report", self.report)
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)

    def test_disagreeing_profiles_write_no_report(self):
        def change(value):
            record = value["records"][0]
            record["deployed"]["method_identifiers_sha256"] = record["default"]["storage_layout_sha256"]

        self.edit_evidence(change)
        code, _, err = self.run_main("conformance", "--criterion", "profile-invariance",
                                     "--candidate", "anchor-and-inspect", "--report", self.report)
        self.assertEqual(code, 1)
        self.assertIn("refused: record=profile-invariance", err)
        self.assertFalse((self.root / self.report).exists())

    def test_evidence_custody_without_retained_payloads_writes_no_report(self):
        report = ".hexaemeron/design-reports/anchor-and-inspect-evidence-custody.json"
        code, _, err = self.run_main("conformance", "--criterion", "evidence-custody",
                                     "--candidate", "anchor-and-inspect", "--report", report)
        self.assertEqual(code, 1)
        self.assertIn("(the named restricted payload is not present)", err)
        self.assertFalse((self.root / report).exists())

    def test_unselected_candidate_and_wrong_path_are_refused(self):
        code, _, err = self.run_main("conformance", "--criterion", "profile-invariance",
                                     "--candidate", "every-deployed-state", "--report",
                                     ".hexaemeron/design-reports/every-deployed-state-profile-invariance.json")
        self.assertEqual(code, 1)
        self.assertIn("was not selected", err)
        code, _, err = self.run_main("conformance", "--criterion", "profile-invariance",
                                     "--candidate", "anchor-and-inspect", "--report", "../escape.json")
        self.assertEqual(code, 1)
        self.assertIn("the path the design record names", err)

    def test_symlinked_report_directory_is_refused(self):
        (self.root / ".hexaemeron").mkdir()
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        os.symlink(elsewhere, self.root / ".hexaemeron" / "design-reports")
        code, _, err = self.run_main("conformance", "--criterion", "profile-invariance",
                                     "--candidate", "anchor-and-inspect", "--report", self.report)
        self.assertEqual(code, 1)
        self.assertIn("is a symlink or not a directory", err)
        self.assertEqual(list(elsewhere.iterdir()), [])


class ChainEvidenceRefusalTests(ScratchCase):
    """Step 2: the fixture, release and owner-handoff records."""

    def edit(self, relative, change):
        value = self.load(relative)
        change(value)
        self.save(relative, value)

    def row(self, value, index=3):
        return value["addresses"][index]

    def test_wrong_chain_block_or_hash_is_refused(self):
        original = (self.root / checker.FIXTURE_RECORD).read_bytes()
        for field, wrong in (("chain_id", 5), ("block_number", checker.BLOCK_NUMBER - 1),
                             ("block_hash", "0x" + "11" * 32)):
            with self.subTest(field=field):
                (self.root / checker.FIXTURE_RECORD).write_bytes(original)
                self.edit(checker.FIXTURE_RECORD, lambda value: value.update({field: wrong}))
                self.refused(f"record=fixture field={field} is {wrong!r}, the study fixes")

    def test_inventory_code_hash_absent_from_the_fixture_is_refused(self):
        removed = {}

        def change(value):
            row = value["addresses"].pop(7)
            removed.update(row)
            value["totals"] = {key: count - 1 for key, count in value["totals"].items()}

        self.edit(checker.FIXTURE_RECORD, change)
        self.refused(f"record=fixture.addresses.{removed['address']} field=address inventory code hash "
                     f"{removed['recorded_registry']['code_keccak256']} is absent from the fixture")

    def test_inventory_code_hash_different_to_the_fixture_is_refused(self):
        state = {}

        def change(value):
            row = self.row(value)
            state["address"] = row["address"]
            row["proved"]["code_hash"] = "0x" + "ab" * 32

        self.edit(checker.FIXTURE_RECORD, change)
        self.refused(f"record=fixture.addresses.{state['address']} field=code_hash inventory code hash",
                     "differs from the fixture's proved code hash 0x" + "ab" * 32)

    def test_recorded_value_presented_as_proved_is_refused(self):
        def change(value):
            self.row(value)["recorded_registry"]["evidence"] = "proof-backed"

        self.edit(checker.FIXTURE_RECORD, change)
        self.refused("field=evidence a recorded value is presented as proved: evidence 'proof-backed'")

    def test_proved_value_taken_from_the_registry_is_refused(self):
        def change(value):
            self.row(value)["proved"]["source"] = checker.REGISTRY_PATH

        self.edit(checker.FIXTURE_RECORD, change)
        self.refused(f"a value from '{checker.REGISTRY_PATH}' labelled 'proof-backed' is presented as proved")

    def test_unverified_fixture_is_refused(self):
        self.edit(checker.FIXTURE_RECORD, lambda value: value["verification"].update(exit=1))
        self.refused("record=fixture field=verification.exit the fixture is not verified: lazarus.py verify exit 1")

    def test_undeclared_capture_limit_is_refused(self):
        self.edit(checker.FIXTURE_RECORD, lambda value: value["plan"]["limits"].pop("max_elapsed_seconds"))
        self.refused("record=fixture field=plan must carry")

    def test_capture_over_a_declared_limit_is_refused(self):
        self.edit(checker.FIXTURE_RECORD, lambda value: value["capture"].update(requests=10**6))
        self.refused("record=fixture field=capture the recorded capture exceeds a declared limit")

    def test_unverified_release_is_refused(self):
        self.edit(checker.RELEASE_RECORD, lambda value: value["verification"].update(exit=2))
        self.refused("record=release field=verification.exit the release is not verified: alexandria.py verify exit 2")

    def test_release_input_digest_is_recomputed_from_its_bytes(self):
        path = self.root / checker.SOURCE_MATCH_PATH
        path.write_bytes(path.read_bytes() + b"\n")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        self.refused(f"record=release.inputs[1] field=sha256 states", f"its bytes hash to {actual}")

    def test_release_must_bind_the_fixture_record(self):
        self.edit(checker.RELEASE_RECORD, lambda value: value["fixture"].update(fixture_digest="0" * 64))
        self.refused("record=release field=fixture must bind the fixture record's digest")

    def test_incomplete_handoff_row_is_refused(self):
        def change(value):
            value["rows"][4]["reviewer"] = ""
            value["rows"] = [row for row in value["rows"] if row["handoff"] != "inventory"]

        self.edit(checker.HANDOFFS_RECORD, change)
        self.refused("record=owner-handoffs.fixture field=reviewer the handoff row is incomplete",
                     "record=owner-handoffs.inventory field=handoff has no row")

    def test_handoff_artefact_digest_is_recomputed(self):
        self.edit(checker.HANDOFFS_RECORD, lambda value: value["rows"][0]["artefact"].update(sha256="0" * 64))
        self.refused("record=owner-handoffs.scope field=artefact.sha256 states '" + "0" * 64 + "'")

    def test_pending_handoff_is_refused(self):
        self.edit(checker.HANDOFFS_RECORD, lambda value: value["rows"][5].update(status="pending"))
        self.refused("record=owner-handoffs.release field=status is 'pending', not complete")

    def test_review_outstanding_is_refused_outside_the_inventory(self):
        self.edit(checker.HANDOFFS_RECORD,
                  lambda value: value["rows"][4].update(status="target-maintainer-review-outstanding"))
        self.refused("record=owner-handoffs.fixture field=status is 'target-maintainer-review-outstanding'; "
                     "only ['inventory'] may be handed on with its target-maintainer review outstanding")


class OwnerHandoffsConformanceTests(ScratchCase):
    report = ".hexaemeron/design-reports/anchor-and-inspect-owner-handoffs.json"

    def conformance(self, verifiers):
        return checker.conformance(self.root, "owner-handoffs", "anchor-and-inspect", self.report, verifiers)

    def test_missing_payload_writes_no_report(self):
        never = {"fixture": lambda path: self.fail("verifier ran"), "release": lambda path: self.fail("verifier ran")}
        self.refused("record=fixture-payload field=path", call=lambda: self.conformance(never))
        self.assertFalse((self.root / self.report).exists())

    def test_sibling_verifier_refusal_writes_no_report(self):
        for relative in (checker.FIXTURE_PAYLOAD, checker.RELEASE_PAYLOAD):
            (self.root / relative).mkdir(parents=True)
            (self.root / relative / "manifest.json").write_text("{}\n", encoding="utf-8")

        def refuse(path):
            raise ValueError("planted refusal")

        joined = self.refused("Lazarus verify refused the retained fixture: ValueError: planted refusal",
                              "Alexandria verify refused the retained release: ValueError: planted refusal",
                              call=lambda: self.conformance({"fixture": refuse, "release": refuse}))
        self.assertIn("record=fixture-payload field=manifest.sha256", joined)
        self.assertFalse((self.root / self.report).exists())


SELECTOR = checker.REJECTION_RECORDS["selector"]
LAYOUT = checker.REJECTION_RECORDS["layout"]
SELECTOR_RUN = "docs/kickoff/1355/rejections/selector/attempts/selector-mem16/run"
BASELINE_RUN = f"{checker.BASELINE_DIRS['v2-c7be']}/run"
V1_RECORD = checker.BASELINE_RECORDS["v1-488b"]
V1_RUN = f"{checker.BASELINE_DIRS['v1-488b']}/run"
LAYOUT_ATTEMPT = "docs/kickoff/1355/rejections/layout/attempts/layout-b1-sto04"
SENTINEL = "src/WildcatSanctionsSentinel.sol:WildcatSanctionsSentinel"
WRAPPER = "src/vault/Wildcat4626Wrapper.sol:Wildcat4626Wrapper"


class HermesEvidenceCase(ScratchCase):
    """Mutations of the committed baseline and rejection records.

    A mutation of a committed Hermes file also re-pins its digest in the record, so
    the refusal asserted is the one the case names rather than a digest mismatch.
    """

    def rewrite_run(self, record, run, relative, change, attempt=None):
        value = self.load(f"{run}/{relative}")
        change(value)
        path = self.root / run / relative
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        def repin(data):
            holder = data if attempt is None else data["attempts"][attempt]
            holder["run_files"][relative] = digest

        self.edit(record, repin)

    def edit(self, relative, change):
        value = self.load(relative)
        change(value)
        self.save(relative, value)

    def selector_result(self, **fields):
        """Rewrite the selector attempt's Hermes result, state and record consistently."""
        def result(value):
            value.update(fields)

        self.rewrite_run(SELECTOR, SELECTOR_RUN, "result.json", result, attempt=0)
        final = self.load(f"{SELECTOR_RUN}/result.json")

        def state(value):
            value["result"] = final

        self.rewrite_run(SELECTOR, SELECTOR_RUN, "state.json", state, attempt=0)

        def record(value):
            attempt = value["attempts"][0]
            attempt["gate_reached"] = final["failed_gate"]
            attempt["verify_exit"] = final["exit_code"]
            attempt["reason"] = final["reason"]
            attempt["output"]["verify_stderr_last_line"] = f"Hermes rejected at Gate {final['failed_gate']}: {final['reason']}"

        self.edit(SELECTOR, record)


class HermesBaselineTests(HermesEvidenceCase):
    def test_committed_evidence_is_summarised(self):
        hermes = checker.check(self.root)["hermes"]
        for tree, protected, passed in (("v2-c7be", 7, 795), ("v1-488b", 3, 348), ("col-46db", 3, 48),
                                        ("fee-ac73", 1, 19), ("rp-5d7f", 1, 5)):
            baseline = hermes["baselines"][tree]
            self.assertEqual((baseline["status"], baseline["protected"], baseline["tests_passed"]),
                             ("baseline_ready", protected, passed))
        coverage = hermes["coverage"]
        self.assertEqual((coverage["covered_types"], coverage["native"], coverage["equivalent"], coverage["covered_addresses"]),
                         (17, 6, 11, 137))
        self.assertEqual((hermes["equivalence"]["types"], hermes["equivalence"]["equal"]), (11, 11))
        self.assertEqual(hermes["rejections"]["selector"]["selected"], "selector-mem16")
        layout = hermes["rejections"]["layout"]
        self.assertEqual(layout["selected"], "layout-b1-sto04")
        self.assertIsNone(layout["blocker"])
        self.assertEqual([a["status"] for a in layout["attempts"]],
                         ["stopped-at-gate-3"] * 3 + ["rejected-at-gate-5"])

    def test_baseline_not_at_baseline_ready_is_refused(self):
        self.rewrite_run(checker.BASELINE_RECORDS["v2-c7be"], BASELINE_RUN, "state.json",
                         lambda value: value.update(status="baseline_running"))
        self.refused("record=baseline.v2-c7be.state field=status is 'baseline_running'")

    def test_missing_protected_contract_is_refused(self):
        def drop(value):
            value["protected_contracts"] = [c for c in value["protected_contracts"] if c["identifier"] != WRAPPER]
            value["layout_contracts"] = [c for c in value["layout_contracts"] if c["identifier"] != WRAPPER]

        self.rewrite_run(checker.BASELINE_RECORDS["v2-c7be"], BASELINE_RUN, "state.json", drop)
        self.refused("record=baseline.v2-c7be.state field=protected_contracts", f"missing ['{WRAPPER}']")

    def test_committed_layout_digest_is_recomputed(self):
        path = self.root / BASELINE_RUN / "storage-layout" / "HooksFactory.before.json"
        path.write_bytes(path.read_bytes().replace(b'"_hooksTemplates"', b'"_hooksTemplatez"', 1))
        self.refused("record=baseline.v2-c7be field=run_files.storage-layout/HooksFactory.before.json recorded")

    def test_layout_not_canonical_for_its_raw_output_is_refused(self):
        def rename(value):
            value["storage"][0]["label"] = "_renamed"

        self.rewrite_run(checker.BASELINE_RECORDS["v2-c7be"], BASELINE_RUN, "storage-layout/HooksFactory.before.json", rename)
        self.refused("storage-layout/HooksFactory.before.json is not Hermes's canonical form",
                     "baseline.artifact_hashes.storage-layout/HooksFactory.before.json does not recompute")

    def test_undeclared_file_beside_the_run_is_refused(self):
        (self.root / BASELINE_RUN / "extra.json").write_text("{}\n", encoding="utf-8")
        self.refused("run/extra.json is committed but not declared")


class HermesRejectionTests(HermesEvidenceCase):
    def test_rejection_that_stopped_before_gate5_is_refused(self):
        def drop_gate4(value):
            value["gates"] = [g for g in value["gates"] if g["id"] != 4]

        self.rewrite_run(SELECTOR, SELECTOR_RUN, "state.json", drop_gate4, attempt=0)
        self.selector_result(failed_gate=4, exit_code=40, reason="full forge test re-run exited 1")
        self.refused("record=rejection.selector field=selected 'selector-mem16' did not exit 50 at Gate 5")

    def test_exit_other_than_50_is_refused(self):
        self.edit(SELECTOR, lambda value: value["attempts"][0].update(verify_exit=30))
        self.refused("record=rejection.selector.selector-mem16 field=gate_reached gate, exit and reason differ",
                     "'selector-mem16' did not exit 50 at Gate 5")

    def test_reason_naming_the_wrong_contract_is_refused(self):
        self.selector_result(reason="public method identifiers changed: src/market/WildcatMarket.sol:WildcatMarket")
        self.refused("'selector-mem16' did not exit 50 at Gate 5 naming its intended contract")

    def test_patch_touching_a_test_file_is_refused(self):
        hunk = ("diff --git a/test/HooksFactory.t.sol b/test/HooksFactory.t.sol\n--- a/test/HooksFactory.t.sol\n"
                "+++ b/test/HooksFactory.t.sol\n@@ -1,1 +1,0 @@\n-    address hooksInstance\n")

        def change(value):
            attempt = value["attempts"][0]
            attempt["patch"] += hunk
            attempt["patch_sha256"] = hashlib.sha256(attempt["patch"].encode("utf-8")).hexdigest()

        self.edit(SELECTOR, change)
        self.refused("field=patch changes test sources ['test/HooksFactory.t.sol']")

    def test_hunk_outside_the_rule_mixes_classes(self):
        hunk = "@@ -500,1 +500,1 @@\n-    uint256 numMarkets = 0;\n+    uint256 numMarkets;\n"

        def change(value):
            attempt = value["attempts"][0]
            attempt["patch"] += hunk
            attempt["patch_sha256"] = hashlib.sha256(attempt["patch"].encode("utf-8")).hexdigest()
            attempt["candidate_solidity_diff"] += hunk

        self.edit(SELECTOR, change)
        self.refused("changes nothing the MEM-16 candidate names; the classes are mixed",
                     "MEM-16 removes the overload only; 1 line(s) are added")

    def test_patch_and_hermes_diff_must_agree(self):
        def change(value):
            value["attempts"][0]["candidate_solidity_diff"] = value["attempts"][0]["candidate_solidity_diff"].replace(
                "-    return _marketsByHooksInstance[hooksInstance];\n", "", 1)

        self.edit(SELECTOR, change)
        self.refused("Hermes's recorded diff and the patch change different lines")

    def test_unrestored_copy_is_refused(self):
        for field, value in (("status_after", " M src/HooksFactory.sol\n"), ("head_after", "0" * 40)):
            with self.subTest(field=field):
                original = self.load(SELECTOR)
                self.edit(SELECTOR, lambda data: data["attempts"][0]["restoration"].update({field: value}))
                self.refused("field=restoration the copy must show a clean status at c7be4039")
                self.save(SELECTOR, original)

    def test_gate5_method_diff_is_recomputed(self):
        self.edit(SELECTOR, lambda value: value["attempts"][0].update(
            hermes_method_identifiers_diff=value["attempts"][0]["hermes_method_identifiers_diff"].replace("4bd1acf3", "00000000")))
        self.refused("field=hermes_method_identifiers_diff does not recompute from the committed before and after maps")

    def test_copy_gate1_must_match_the_sealed_anchor(self):
        def change(value):
            value["baseline"]["artifact_hashes"]["storage-layout/WildcatMarket.before.json"] = "0" * 64

        self.rewrite_run(SELECTOR, SELECTOR_RUN, "state.json", change, attempt=0)
        self.refused("the copy's Gate 1 maps, toolchain or sources differ from the sealed anchor")

    def test_blocked_record_must_state_its_blocker(self):
        self.edit(LAYOUT, lambda value: value.update(selected=None, blocker=None))
        self.refused("record=rejection.layout field=selected is null although layout-b1-sto04 reached Gate 5",
                     "record=rejection.layout field=blocker a record with no selected attempt must state its blocker")

    def test_selected_attempt_that_stopped_at_gate3_is_refused(self):
        self.edit(LAYOUT, lambda value: value.update(selected="layout-a1-sto18"))
        self.refused("'layout-a1-sto18' did not exit 50 at Gate 5 naming its intended contract on a sealed anchor")

    def test_blocker_beside_a_selected_attempt_is_refused(self):
        self.edit(LAYOUT, lambda value: value.update(blocker="stale blocker"))
        self.refused("record=rejection.layout field=blocker must be null once an attempt reached Gate 5")

    def test_layout_attempts_follow_the_study_order(self):
        self.edit(LAYOUT, lambda value: value["attempts"].reverse())
        self.refused("record=rejection.layout field=study_order attempts must follow the study's candidate order")


class V1AnchorAndLayoutTests(HermesEvidenceCase):
    def test_unsealed_v1_anchor_leaves_no_selected_layout(self):
        self.rewrite_run(V1_RECORD, V1_RUN, "state.json", lambda value: value.update(status="baseline_running"))
        self.refused("record=baseline.v1-488b.state field=status is 'baseline_running'",
                     "'layout-b1-sto04' did not exit 50 at Gate 5 naming its intended contract on a sealed anchor")

    def test_v1_anchor_missing_the_escrow_is_refused(self):
        escrow = "src/WildcatSanctionsEscrow.sol:WildcatSanctionsEscrow"

        def drop(value):
            value["protected_contracts"] = [c for c in value["protected_contracts"] if c["identifier"] != escrow]

        self.rewrite_run(V1_RECORD, V1_RUN, "state.json", drop)
        self.refused("record=baseline.v1-488b.state field=protected_contracts", f"missing ['{escrow}']")

    def test_v1_anchor_compiler_pin_is_checked(self):
        self.edit(V1_RECORD, lambda value: value["invocation"]["environment"].pop("FOUNDRY_SOLC"))
        self.refused("record=baseline.v1-488b field=invocation")

    def test_layout_copy_gate1_must_match_the_sealed_v1_anchor(self):
        def change(value):
            value["baseline"]["artifact_hashes"]["storage-layout/WildcatArchController.before.json"] = "0" * 64

        self.rewrite_run(LAYOUT, f"{LAYOUT_ATTEMPT}/run", "state.json", change, attempt=3)
        self.refused("record=rejection.layout.layout-b1-sto04 field=state.baseline the copy's Gate 1 maps")

    def test_sto04_hunk_outside_the_packed_params_mixes_classes(self):
        hunk = "@@ -90,1 +90,1 @@\n-    return sanctionOverrides[borrower][account];\n+    return !sanctionOverrides[borrower][account];\n"

        def change(value):
            attempt = value["attempts"][3]
            attempt["patch"] += hunk
            attempt["patch_sha256"] = hashlib.sha256(attempt["patch"].encode("utf-8")).hexdigest()
            attempt["candidate_solidity_diff"] += hunk

        self.edit(LAYOUT, change)
        self.refused("record=rejection.layout.layout-b1-sto04 field=patch.hunk[3] changes nothing the STO-04 candidate names")

    def test_method_identifier_check_equality_is_recomputed(self):
        self.edit(LAYOUT, lambda value: value["attempts"][3]["method_identifier_check"].update(equal=False))
        self.refused("method_identifier_check field=equal records False but the committed maps say True")

    def test_method_identifier_check_after_map_digest_is_recomputed(self):
        path = self.root / LAYOUT_ATTEMPT / "supplementary" / "WildcatSanctionsSentinel.methods.after.json"
        path.write_bytes(path.read_bytes().replace(b'"isSanctioned(address,address)"', b'"isSanctionedX(address,address)"', 1))
        self.refused("method_identifier_check field=after.sha256 does not hash the committed after map",
                     "method_identifier_check field=equal records True but the committed maps say False")

    def test_method_identifier_check_after_path_must_be_the_supplementary_map(self):
        before = "run/method-identifiers/WildcatSanctionsSentinel.before.json"
        (self.root / LAYOUT_ATTEMPT / "supplementary" / "WildcatSanctionsSentinel.methods.after.json").unlink()
        self.edit(LAYOUT, lambda value: value["attempts"][3]["method_identifier_check"]["after"].update(path=before))
        self.refused("method_identifier_check field=after must name supplementary/WildcatSanctionsSentinel.methods.after.json")

    def test_method_identifier_check_before_map_is_the_sealed_one(self):
        name = "method-identifiers/WildcatSanctionsSentinel.before.json"
        planted = b'{\n  "isSanctioned(address,address)": "06e74444"\n}\n'
        (self.root / LAYOUT_ATTEMPT / "run" / name).write_bytes(planted)
        (self.root / LAYOUT_ATTEMPT / "supplementary" / "WildcatSanctionsSentinel.methods.after.json").write_bytes(planted)

        def repin(value):
            attempt = value["attempts"][3]
            attempt["run_files"][name] = hashlib.sha256(planted).hexdigest()
            attempt["method_identifier_check"]["after"]["sha256"] = hashlib.sha256(planted).hexdigest()

        self.edit(LAYOUT, repin)
        self.refused(f"record=rejection.layout.layout-b1-sto04 field={name} is not the map the attempt's Gate 1 sealed",
                     "method_identifier_check field=before the committed run/method-identifiers/"
                     "WildcatSanctionsSentinel.before.json is not the map the attempt's Gate 1 sealed")

    def test_undeclared_file_beside_an_attempt_run_is_refused(self):
        path = self.root / "docs/kickoff/1355/rejections/selector/attempts/selector-mem16/notes.json"
        path.write_text("{}\n", encoding="utf-8")
        self.refused("rejections/selector/attempts/selector-mem16/notes.json is committed but not declared")

    def test_malformed_attempt_refuses_by_name(self):
        def change(value):
            argv = value["attempts"][0]["invocation"]["verify_argv"]
            index = argv.index("--rule")
            del argv[index:index + 2]

        self.edit(SELECTOR, change)
        self.refused("record=rejection.selector.selector-mem16 field=invocation.verify_argv must name the record's rule")
        self.rewrite_run(SELECTOR, SELECTOR_RUN, "state.json", lambda value: value.update(gates=7), attempt=0)
        self.refused("record=rejection.selector field=attempts[0] is malformed: TypeError")

    def test_runbook_copy_is_pinned_to_the_amended_runbook(self):
        path = self.root / checker.DOCS / "runbook.md"
        path.write_bytes(path.read_bytes() + b"\n")
        self.refused(f"record=inventory.documents.runbook field=sha256 {checker.DOCS}/runbook.md does not match "
                     f"the receipted {checker.RUNBOOK_SHA256}")


class RejectionConformanceTests(HermesEvidenceCase):
    def run_main(self, criterion):
        report = f".hexaemeron/design-reports/anchor-and-inspect-{criterion}.json"
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = checker.main(["conformance", "--criterion", criterion, "--candidate", "anchor-and-inspect",
                                 "--report", report], root=self.root)
        return code, out.getvalue(), err.getvalue(), self.root / report

    def test_selector_rejection_report_is_written(self):
        code, out, _, report = self.run_main("selector-rejection")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["reason"],
                         "public method identifiers changed: src/HooksFactory.sol:HooksFactory")
        value = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual((value["criterion"], value["value"], value["exit"]), ("selector-rejection", True, 0))

    def test_layout_rejection_report_is_written(self):
        code, out, _, report = self.run_main("layout-rejection")
        self.assertEqual(code, 0)
        result = json.loads(out)
        self.assertEqual(result["reason"], f"protected storage layout changed: {SENTINEL}")
        self.assertEqual(result["evidence"]["baseline"]["path"], V1_RECORD)
        value = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual((value["criterion"], value["value"], value["exit"]), ("layout-rejection", True, 0))

    def test_layout_rejection_without_a_sealed_v1_anchor_writes_no_report(self):
        self.rewrite_run(V1_RECORD, V1_RUN, "state.json", lambda value: value.update(status="rejected"))
        code, _, err, report = self.run_main("layout-rejection")
        self.assertEqual(code, 1)
        self.assertIn("record=baseline.v1-488b.state field=status is 'rejected'", err)
        self.assertFalse(report.exists())

    def test_selector_rejection_with_a_broken_record_writes_no_report(self):
        self.edit(SELECTOR, lambda value: value["attempts"][0]["restoration"].update(status_after="?? .gas-snapshot\n"))
        code, _, err, report = self.run_main("selector-rejection")
        self.assertEqual(code, 1)
        self.assertIn("field=restoration", err)
        self.assertFalse(report.exists())


EQUIVALENCE = checker.EQUIVALENCE_RECORD
EXCLUSIONS = checker.EXCLUSIONS_RECORD
FEE_RECORD = checker.BASELINE_RECORDS["fee-ac73"]
FEE_RUN = f"{checker.BASELINE_DIRS['fee-ac73']}/run"
RP_RECORD = checker.BASELINE_RECORDS["rp-5d7f"]
SEALED_COVERAGE = ".hexaemeron/design-reports/anchor-and-inspect-sealed-coverage.json"


class EquivalenceTests(HermesEvidenceCase):
    def equivalence_file(self, type_id, name):
        return self.root / checker.EQUIVALENCE_DIR / type_id / name

    def rewrite_equivalence(self, type_id, name, old, new):
        """Change one committed equivalence file and re-pin its digest, so the byte comparison is what refuses."""
        path = self.equivalence_file(type_id, name)
        raw = path.read_bytes()
        self.assertIn(old, raw)
        path.write_bytes(raw.replace(old, new, 1))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        def repin(value):
            entry = [e for e in value["types"] if e["type"] == type_id][0]
            entry["files"][name] = digest

        self.edit(EQUIVALENCE, repin)
        return digest

    def test_layout_one_byte_different_from_the_anchor_is_refused(self):
        for name in ("storage-layout.raw.json", "storage-layout.json"):
            digest = self.rewrite_equivalence("hooks-factory", name, b'"_hooksTemplates"', b'"_hooksTemplatez"')
        joined = self.refused("record=equivalence.hooks-factory field=storage-layout.json differs from the sealed v2-c7be map "
                              "storage-layout/HooksFactory.before.json")
        self.assertIn(f"digest={digest}", joined)

    def test_method_map_one_byte_different_from_the_anchor_is_refused(self):
        path = self.equivalence_file("arch-controller", "method-identifiers.json")
        value = json.loads(path.read_text(encoding="utf-8"))
        name, selector = sorted(value.items())[0]
        changed = selector[:-1] + ("0" if selector[-1] != "0" else "1")
        self.rewrite_equivalence("arch-controller", "method-identifiers.json",
                                 f'"{selector}"'.encode(), f'"{changed}"'.encode())
        self.refused("record=equivalence.arch-controller field=method-identifiers.json differs from the sealed v1-488b map")

    def test_equivalence_resting_on_an_unsealed_anchor_is_refused(self):
        self.edit(RP_RECORD, lambda value: value["tests"].update(passed=4))
        self.refused("record=baseline.rp-5d7f field=tests",
                     "record=equivalence.open-access-role-provider field=anchor rp-5d7f is not a sealed anchor")

    def test_capture_pin_that_differs_from_the_tree_is_refused(self):
        def change(value):
            capture = [c for c in value["captures"] if c["tree"] == "v1-da74"][0]
            capture["environment"]["FOUNDRY_SOLC"] = "0.8.24"

        self.edit(EQUIVALENCE, change)
        self.refused("record=equivalence.captures.v1-da74 field=environment")

    def test_capture_compiler_that_differs_from_the_anchor_run_is_refused(self):
        def change(value):
            capture = [c for c in value["captures"] if c["tree"] == "v2-e1f7"][0]
            capture["compiler"]["solc"] = "0.8.26"

        self.edit(EQUIVALENCE, change)
        joined = self.refused("record=equivalence.open-access-role-provider field=compiler the capture at v2-e1f7 resolved")
        self.assertIn("record=equivalence.market-lens-app field=compiler", joined)

    def test_equivalence_file_digest_is_recomputed(self):
        path = self.equivalence_file("wildcat-market", "method-identifiers.json")
        path.write_bytes(path.read_bytes() + b"\n")
        self.refused("record=equivalence.wildcat-market field=files.method-identifiers.json recorded")

    def test_layout_not_canonical_for_its_raw_output_is_refused(self):
        self.rewrite_equivalence("open-term-hooks", "storage-layout.json", b'"label"', b'"labe1"')
        self.refused("record=equivalence.open-term-hooks field=storage-layout.json is not Hermes's canonical form")

    def test_claimed_anchor_digest_must_equal_the_sealed_hash(self):
        def change(value):
            entry = [e for e in value["types"] if e["type"] == "sanctions-escrow"][0]
            entry["anchor_maps"]["method_identifiers"]["sha256"] = "0" * 64

        self.edit(EQUIVALENCE, change)
        self.refused("record=equivalence.sanctions-escrow field=anchor_maps.method_identifiers.sha256 is 000")

    def test_missing_equivalence_type_is_refused(self):
        self.edit(EQUIVALENCE, lambda value: value.update(types=[e for e in value["types"] if e["type"] != "market-lens-app"]))
        joined = self.refused("record=equivalence.market-lens-app field=type no equivalence record for this type",
                              "equivalence/market-lens-app is not a recorded equivalence type")
        with self.assertRaises(checker.Refusal):
            checker.conformance(self.root, "sealed-coverage", "anchor-and-inspect", SEALED_COVERAGE)
        self.assertFalse((self.root / SEALED_COVERAGE).exists())
        self.assertIn("digest=", joined)

    def test_malformed_equivalence_record_refuses_by_name(self):
        self.edit(EQUIVALENCE, lambda value: value["types"].__setitem__(0, {**value["types"][0], "files": ["x"], "argv": None}))
        self.refused("record=equivalence.hooks-factory field=files must name exactly")
        self.edit(EQUIVALENCE, lambda value: value.update(captures="broken", types={"x": 1}))
        self.refused("record=equivalence.captures.v2-a70f field=tree no capture is recorded")


class ExclusionEvidenceTests(HermesEvidenceCase):
    def edit_run(self, tree, side, **fields):
        def change(value):
            run = [r for r in value["rows"] if r["tree"] == tree][0][side]
            run.update(fields)
            run["summary"] = (f"Ran 1 test suite in 1ms (1ms CPU time): {run['passed']} tests passed, "
                              f"{run['failed']} failed, {run['skipped']} skipped")

        self.edit(EXCLUSIONS, change)

    def test_excluded_file_that_runs_a_passing_test_is_refused(self):
        self.edit_run("v2-c7be", "excluded", passed=1, failed=1)
        self.refused("record=exclusions.v2-c7be:test/vault/Wildcat4626WrapperStandard.t.sol.excluded field=passed "
                     "the excluded file runs 1 passing tests")

    def test_exclusion_that_drops_passing_tests_is_refused(self):
        self.edit_run("v1-488b", "unexcluded", passed=349)
        self.refused("record=exclusions.v1-488b:test/market/WildcatMarketToken.t.sol.unexcluded field=passed "
                     "the unexcluded suite passes 349 but the sealed Gate 1 passes 348")

    def test_exclusion_without_evidence_is_refused(self):
        self.edit(EXCLUSIONS, lambda value: value.update(rows=value["rows"][:1]))
        self.refused("record=exclusions.v1-488b:test/market/WildcatMarketToken.t.sol field=file the exclusion has no zero-loss evidence")

    def test_summary_must_state_the_recorded_counts(self):
        def change(value):
            value["rows"][0]["excluded"]["passed"] = 0
            value["rows"][0]["excluded"]["summary"] = "Ran 1 test suite: 3 tests passed, 0 failed, 0 skipped"

        self.edit(EXCLUSIONS, change)
        self.refused("field=argv must be ['forge', 'test', '--match-path'")


class RestrictedBaselineTests(HermesEvidenceCase):
    def test_withheld_private_file_in_the_public_tree_is_refused(self):
        (self.root / FEE_RUN / "state.json").write_text("{}\n", encoding="utf-8")
        self.refused(f"record=baseline.fee-ac73 field=run_files {FEE_RUN}/state.json is a withheld Hermes file of a private repository")

    def test_withheld_private_file_beside_the_run_directory_is_refused(self):
        directory = checker.BASELINE_DIRS["fee-ac73"]
        (self.root / directory / "state.json").write_text("{}\n", encoding="utf-8")
        nested = self.root / checker.BASELINE_DIRS["rp-5d7f"] / "gate1"
        nested.mkdir()
        (nested / "result.json").write_text("{}\n", encoding="utf-8")
        self.refused(f"record=baseline.fee-ac73 field=path {directory}/state.json is a withheld Hermes file of a private repository",
                     f"record=baseline.rp-5d7f field=path {checker.BASELINE_DIRS['rp-5d7f']}/gate1 is not the record or its run directory")

    def test_file_beside_a_public_anchor_run_directory_is_refused(self):
        directory = checker.BASELINE_DIRS["v2-c7be"]
        (self.root / directory / "extra.json").write_text("{}\n", encoding="utf-8")
        self.refused(f"record=baseline.v2-c7be field=path {directory}/extra.json is not the record or its run directory")

    def test_declared_private_payload_is_refused(self):
        (self.root / FEE_RUN / "baseline-source-manifest.json").write_text("{}\n", encoding="utf-8")

        def declare(value):
            value["run_files"]["baseline-source-manifest.json"] = hashlib.sha256(b"{}\n").hexdigest()

        self.edit(FEE_RECORD, declare)
        self.refused("record=baseline.fee-ac73 field=run_files.baseline-source-manifest.json is a withheld Hermes file")

    def test_private_source_copy_under_docs_is_refused(self):
        target = self.root / checker.BASELINE_DIRS["rp-5d7f"] / "baseline-sources"
        target.mkdir()
        (target / "notes.md").write_text("copy\n", encoding="utf-8")
        self.refused("record=custody field=path docs/kickoff/1355/baselines/role-provider-5d7f/baseline-sources is a target or Hermes source directory name")

    def test_restricted_compiler_pin_that_differs_from_the_run_is_refused(self):
        self.edit(FEE_RECORD, lambda value: value["state"]["forge_config"].update(solc="0.8.26"))
        joined = self.refused("record=baseline.fee-ac73.state field=forge_config is")
        self.assertIn("'solc': '0.8.25'", joined)
        self.edit(FEE_RECORD, lambda value: value["invocation"]["environment"].update(FOUNDRY_SOLC="0.8.26"))
        self.refused("record=baseline.fee-ac73 field=invocation")

    def test_restricted_map_hash_is_recomputed_from_the_committed_map(self):
        def change(value):
            value["state"]["map_hashes"]["storage-layout/OpenAccessRoleProvider.before.json"] = "1" * 64

        self.edit(RP_RECORD, change)
        self.refused("record=baseline.rp-5d7f.state field=map_hashes.storage-layout/OpenAccessRoleProvider.before.json "
                     "does not hash the committed map")

    def test_restricted_record_missing_a_field_refuses_by_name(self):
        self.edit(FEE_RECORD, lambda value: value.pop("restricted"))
        self.refused("record=baseline.fee-ac73 field=restricted missing")


FAKE_FORGE_VERSION = f"forge Version: 1.7.1\nCommit SHA: {checker.FORGE['commit']}\n"


class SealedCoverageTests(HermesEvidenceCase):
    """sealed-coverage over synthetic retained runs; the private payloads never enter the test tree."""

    def plant(self, tree):
        """A synthetic Hermes Gate 1 directory whose state projects to the public record, re-pinned into it."""
        relative = checker.BASELINE_RECORDS[tree]
        record = self.load(relative)
        run = self.root / checker.BASELINE_DIRS[tree] / "run"
        files = {name: (run / name).read_bytes() for name in record["run_files"]}
        source = b"// synthetic source copy\n"
        manifest = {"src/Synthetic.sol": hashlib.sha256(source).hexdigest()}
        config = canonical({**record["state"]["forge_config"], "optimizer": False}).encode()
        files["baseline-source-manifest.json"] = canonical(manifest).encode()
        files["baseline.forge-config.json"] = config
        files["baseline.forge-version.txt"] = FAKE_FORGE_VERSION.encode()
        passed = record["tests"]["passed"]
        files["logs/gate1.forge-test.log"] = (f"Ran 1 test suite in 1ms (1ms CPU time): {passed} tests passed, "
                                              "0 failed, 0 skipped\n").encode()
        files["baseline-sources/src/Synthetic.sol"] = source
        projection = record["state"]
        hashes = {name: hashlib.sha256(files[name]).hexdigest()
                  for name in files if not name.startswith(("logs/", "baseline-sources/")) and not name.endswith(".raw.json")}
        state = {
            "schema": projection["schema"], "status": projection["status"], "run_dir": "/synthetic/run",
            "execution": projection["execution"], "protected_contracts": projection["protected_contracts"],
            "layout_contracts": projection["layout_contracts"],
            "asserted_no_protected_contracts": projection["asserted_no_protected_contracts"],
            "gates": [{**gate, "name": "baseline"} for gate in projection["gates"]],
            "baseline": {"git_head": projection["git_head"], "corpus_sha256": projection["corpus_sha256"],
                         "forge_config": projection["forge_config"], "artifact_hashes": hashes,
                         "source_manifest": manifest, "forge_config_sha256": hashlib.sha256(config).hexdigest(),
                         "forge_version_sha256": hashlib.sha256(FAKE_FORGE_VERSION.encode()).hexdigest()},
        }
        self.assertEqual(checker.state_projection(state), projection)
        state_raw = canonical(state).encode()
        result_raw = canonical({"schema": "hermes/v1", "skill": "hermes", "status": "baseline_ready", "exit_code": 0,
                                "run_dir": "/synthetic/run"}).encode()
        digest = hashlib.sha256(state_raw).hexdigest()
        base = self.root / checker.RESTRICTED_RUNS / digest
        for name, raw in {**files, "state.json": state_raw, "result.json": result_raw}.items():
            (base / name).parent.mkdir(parents=True, exist_ok=True)
            (base / name).write_bytes(raw)

        def repin(value):
            value["restricted"] = {"path": f"{checker.RESTRICTED_RUNS}/{digest}", "state_sha256": digest,
                                   "result_sha256": hashlib.sha256(result_raw).hexdigest()}

        self.edit(relative, repin)
        return base

    def conformance(self):
        return checker.conformance(self.root, "sealed-coverage", "anchor-and-inspect", SEALED_COVERAGE)

    def test_sealed_coverage_report_is_written_once(self):
        for tree in checker.RESTRICTED_TREES:
            self.plant(tree)
        result = self.conformance()
        self.assertEqual((result["value"], result["types"], result["addresses"], result["native"], result["equivalent"]),
                         (True, 17, 137, 6, 11))
        report = json.loads((self.root / SEALED_COVERAGE).read_text(encoding="utf-8"))
        self.assertEqual((report["criterion"], report["value"], report["exit"]), ("sealed-coverage", True, 0))
        self.refused("already exists; a retry uses a fresh path", call=self.conformance)

    def test_missing_retained_run_writes_no_report(self):
        self.plant("fee-ac73")
        self.refused("record=restricted.rp-5d7f field=path missing directory", "(the retained run is not present)",
                     call=self.conformance)
        self.assertFalse((self.root / SEALED_COVERAGE).exists())

    def test_retained_source_copy_is_recomputed(self):
        self.plant("fee-ac73")
        base = self.plant("rp-5d7f")
        (base / "baseline-sources/src/Synthetic.sol").write_bytes(b"// changed\n")
        self.refused("record=restricted.rp-5d7f field=source_manifest.src/Synthetic.sol does not hash the retained source copy",
                     call=self.conformance)
        self.assertFalse((self.root / SEALED_COVERAGE).exists())

    def test_retained_map_that_differs_from_the_committed_map_is_refused(self):
        self.plant("rp-5d7f")
        base = self.plant("fee-ac73")
        path = base / "storage-layout/WildcatFeeRecipient.before.raw.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.refused("record=restricted.fee-ac73 field=storage-layout/WildcatFeeRecipient.before.raw.json "
                     "the committed map differs from the retained file", call=self.conformance)

    def test_retained_state_that_moved_is_refused(self):
        self.plant("rp-5d7f")
        base = self.plant("fee-ac73")
        (base / "state.json").write_bytes((base / "state.json").read_bytes() + b"\n")
        self.refused("record=restricted.fee-ac73 field=state_sha256", call=self.conformance)

    def test_retained_test_log_must_report_the_recorded_count(self):
        self.plant("fee-ac73")
        base = self.plant("rp-5d7f")
        (base / "logs/gate1.forge-test.log").write_bytes(b"Ran 1 test suite in 1ms: 4 tests passed, 0 failed, 0 skipped\n")
        self.refused("record=restricted.rp-5d7f field=tests the retained Gate 1 test log does not report 5 passed",
                     call=self.conformance)

    def test_every_conformance_cell_of_the_design_record_has_a_resolver(self):
        design = self.load(checker.DESIGN_EVIDENCE)
        cells = {r["criterion"]: r["blocks"] for r in design["results"]
                 if r["candidate"] == "anchor-and-inspect" and r["state"] == "pending"}
        self.assertEqual(cells, checker.CONFORMANCE)


RETAINED_HERMES = ROOT / checker.RESTRICTED_RUNS


@unittest.skipUnless(RETAINED_HERMES.is_dir(), "the private Hermes runs are retained only in the run worktree")
class RetainedSealedCoverageTests(HermesEvidenceCase):
    def test_sealed_coverage_holds_over_the_retained_private_runs(self):
        shutil.copytree(RETAINED_HERMES, self.root / checker.RESTRICTED_RUNS)
        result = checker.conformance(self.root, "sealed-coverage", "anchor-and-inspect", SEALED_COVERAGE)
        self.assertEqual((result["value"], result["types"], result["addresses"]), (True, 17, 137))


RETAINED = ROOT / checker.RESTRICTED


@unittest.skipUnless((RETAINED / "fixture-26006289" / "manifest.json").is_file(),
                     "the retained payloads live only in the run worktree's ignored restricted directory")
class RetainedPayloadTests(ScratchCase):
    """Runs where the payloads are retained; the committed-record cases above run everywhere."""

    report = OwnerHandoffsConformanceTests.report

    def setUp(self):
        super().setUp()
        shutil.copytree(RETAINED, self.root / checker.RESTRICTED)
        self.verifiers = checker.sibling_verifiers(ROOT)

    def test_owner_handoffs_report_is_written_from_the_retained_payload(self):
        result = checker.conformance(self.root, "owner-handoffs", "anchor-and-inspect", self.report, self.verifiers)
        self.assertEqual(result["value"], True)
        report = json.loads((self.root / self.report).read_text(encoding="utf-8"))
        self.assertEqual((report["criterion"], report["value"], report["exit"]), ("owner-handoffs", True, 0))

    def test_changed_proof_record_is_refused(self):
        path = self.root / checker.PROOFS_SOURCE
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'"nonce":"0x1"', b'"nonce":"0x2"', 1))
        self.assertNotEqual(path.read_bytes(), raw)
        self.refused("Lazarus verify refused the retained fixture",
                     call=lambda: checker.conformance(self.root, "owner-handoffs", "anchor-and-inspect",
                                                      self.report, self.verifiers))
        self.assertFalse((self.root / self.report).exists())


REPRODUCTION = checker.REPRODUCTION_RECORD
EVIDENCE_CUSTODY = ".hexaemeron/design-reports/anchor-and-inspect-evidence-custody.json"


class ReproductionTests(HermesEvidenceCase):
    """The Step 5 reproduction record against the sealed records it re-ran."""

    def anchor(self, value, tree):
        return [item for item in value["anchors"] if item["tree"] == tree][0]

    def test_committed_reproduction_is_summarised(self):
        reproduction = checker.check(self.root)["hermes"]["reproduction"]
        self.assertEqual(reproduction["anchors"], {tree: "reproduced" for tree in checker.BASELINE_TREES})
        self.assertEqual(reproduction["rejections"], {"selector": "reproduced", "layout": "reproduced"})
        self.assertNotIn("_retained", reproduction)

    def test_reproduction_digest_that_differs_from_the_sealed_record_is_refused(self):
        name = "storage-layout/HooksFactory.before.json"

        def change(value):
            self.anchor(value, "v2-c7be")["maps"][name] = "0" * 64

        self.edit(REPRODUCTION, change)
        self.refused(f"record=reproduction.v2-c7be field=maps.{name} differs from the sealed record's",
                     "record=reproduction.v2-c7be field=verdict records 'reproduced' but the fields recompute 'differs'")

    def test_private_reproduction_digest_that_differs_is_refused(self):
        name = "storage-layout/WildcatFeeRecipient.before.raw.json"

        def change(value):
            item = self.anchor(value, "fee-ac73")
            item["maps"][name] = "1" * 64
            item["verdict"] = "differs"

        self.edit(REPRODUCTION, change)
        joined = self.refused(f"record=reproduction.fee-ac73 field=maps.{name} differs from the sealed record's")
        self.assertNotIn("field=verdict", joined)

    def test_reproduction_of_another_invocation_or_count_is_refused(self):
        def change(value):
            item = self.anchor(value, "v1-488b")
            item["invocation_sha256"] = "2" * 64
            item["tests"]["passed"] = 347

        self.edit(REPRODUCTION, change)
        self.refused("record=reproduction.v1-488b field=invocation_sha256 does not reproduce the sealed record",
                     "record=reproduction.v1-488b field=tests does not reproduce the sealed record")

    def test_missing_anchor_reproduction_is_refused(self):
        self.edit(REPRODUCTION, lambda value: value["anchors"].pop())
        self.refused("record=reproduction field=anchors must reproduce exactly")

    def test_rejection_that_no_longer_exits_50_is_refused(self):
        def change(value):
            row = value["rejections"][0]
            row.update(verify_exit=30, gate_reached=3, gates_passed=[1, 2])

        self.edit(REPRODUCTION, change)
        self.refused("record=reproduction.selector field=verify_exit does not reproduce the sealed selector-mem16 rejection",
                     "record=reproduction.selector field=gate_reached",
                     "record=reproduction.selector field=gates_passed",
                     "record=reproduction.selector field=verdict records 'reproduced' but the fields recompute 'differs'")

    def test_rejection_reason_naming_another_contract_is_refused(self):
        def change(value):
            row = value["rejections"][1]
            row["reason"] = f"protected storage layout changed: {WRAPPER}"

        self.edit(REPRODUCTION, change)
        self.refused("record=reproduction.layout field=reason does not reproduce the sealed layout-b1-sto04 rejection")

    def test_unrestored_rejection_copy_or_other_after_map_is_refused(self):
        def change(value):
            row = value["rejections"][1]
            row["restoration"]["status_after"] = " M src/WildcatSanctionsSentinel.sol\n"
            row["after_maps"] = {name: "3" * 64 for name in row["after_maps"]}

        self.edit(REPRODUCTION, change)
        self.refused("record=reproduction.layout field=restoration", "record=reproduction.layout field=after_maps")

    def test_malformed_reproduction_refuses_by_name(self):
        self.edit(REPRODUCTION, lambda value: value["rejections"][0].pop("gate1_maps"))
        self.refused("record=reproduction.selector field=gate1_maps missing")


class EvidenceCustodyTests(HermesEvidenceCase):
    """evidence-custody over the scratch tree, with synthetic private runs where a case needs one."""

    def custody(self, summary=None):
        return checker.evidence_custody_evidence(self.root, summary or checker.check(self.root))

    def plant_private(self):
        bases = [SealedCoverageTests.plant(self, tree) for tree in checker.RESTRICTED_TREES]
        (bases[0] / "baseline.gas-snapshot").write_bytes(b"WildcatFeeRecipientTest:testWithheldBehaviour() (gas: 1)\n")
        return bases

    def test_custody_record_naming_an_absent_restricted_payload_is_refused(self):
        joined = self.refused(f"{checker.FIXTURE_PAYLOAD}/manifest.json",
                              "(the named restricted payload is not present)",
                              call=lambda: checker.conformance(self.root, "evidence-custody", "anchor-and-inspect",
                                                               EVIDENCE_CUSTODY))
        self.assertIn("record=reproduction.fee-ac73.retained", joined)
        self.assertFalse((self.root / EVIDENCE_CUSTODY).exists())

    def test_restricted_path_named_without_a_verified_payload_is_refused(self):
        readme = self.root / checker.DOCS / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nSee `.hexaemeron/restricted/unnamed-payload/run`.\n",
                          encoding="utf-8")
        self.refused("record=custody field=reference .hexaemeron/restricted/unnamed-payload/run is named under",
                     call=self.custody)

    def test_private_test_output_under_docs_is_refused(self):
        self.plant_private()
        readme = self.root / checker.DOCS / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nWildcatFeeRecipientTest:testWithheldBehaviour passed.\n",
                          encoding="utf-8")
        self.refused("README.md carries private test output ['WildcatFeeRecipientTest', "
                     "'WildcatFeeRecipientTest:testWithheldBehaviour', 'testWithheldBehaviour']",
                     call=self.custody)

    def test_private_test_name_or_log_suite_under_docs_is_refused(self):
        bases = self.plant_private()
        public = self.load(checker.BASELINE_RECORDS["v2-c7be"])["artefact_text"]["baseline.gas-snapshot"].splitlines()[0]
        (bases[0] / "baseline.gas-snapshot").write_bytes(
            f"WildcatFeeRecipientTest:testWithheldBehaviour() (gas: 1)\n{public}\n".encode())
        log = bases[0] / "logs/gate1.forge-test.log"
        log.write_bytes(b"Ran 1 test for test/Withheld.t.sol:WithheldSuite\n" + log.read_bytes())
        shared = public.split(":")[1].split("(")[0]
        readme = self.root / checker.DOCS / "README.md"
        text = readme.read_text(encoding="utf-8")
        readme.write_text(text + f"\nThe suite ran `testWithheldBehaviour` and `{shared}`.\n", encoding="utf-8")
        joined = self.refused("README.md carries private test output ['testWithheldBehaviour']", call=self.custody)
        self.assertNotIn(shared, joined)
        readme.write_text(text + "\nRan 1 test for test/Withheld.t.sol:WithheldSuite\n", encoding="utf-8")
        self.refused("README.md carries private test output ['WithheldSuite', 'test/Withheld.t.sol']", call=self.custody)

    def test_sealed_run_retained_as_its_own_reproduction_is_refused(self):
        base = SealedCoverageTests.plant(self, "fee-ac73")
        digest = base.name
        result = hashlib.sha256((base / "result.json").read_bytes()).hexdigest()

        def point(value, path, state, kept_result):
            item = [a for a in value["anchors"] if a["tree"] == "fee-ac73"][0]
            item["retained"] = {"path": path, "state_sha256": state, "result_sha256": kept_result}

        target = self.root / checker.RESTRICTED_REPRODUCTIONS / digest
        shutil.copytree(base, target)
        self.edit(REPRODUCTION, lambda value: point(value, f"{checker.RESTRICTED_REPRODUCTIONS}/{digest}", digest, result))
        self.refused("record=reproduction.fee-ac73.retained field=state_sha256 is the sealed run's state.json byte for byte",
                     call=self.custody)
        state = json.loads((target / "state.json").read_text(encoding="utf-8"))
        state["baseline"]["git_head"] = "0" * 40
        state["run_dir"] = "/synthetic/second-run"
        raw = canonical(state).encode()
        moved = self.root / checker.RESTRICTED_REPRODUCTIONS / hashlib.sha256(raw).hexdigest()
        target.rename(moved)
        (moved / "state.json").write_bytes(raw)
        self.edit(REPRODUCTION, lambda value: point(value, f"{checker.RESTRICTED_REPRODUCTIONS}/{moved.name}", moved.name, result))
        joined = self.refused("record=reproduction.fee-ac73.retained field=state the retained reproduction's state differs "
                              "from the sealed record's projection", call=self.custody)
        self.assertNotIn("byte for byte", joined)

    def test_retained_reproduction_result_for_another_run_directory_is_refused(self):
        base = SealedCoverageTests.plant(self, "fee-ac73")
        state = json.loads((base / "state.json").read_text(encoding="utf-8"))
        state["run_dir"] = "/synthetic/reproduction"
        raw = canonical(state).encode()
        target = self.root / checker.RESTRICTED_REPRODUCTIONS / hashlib.sha256(raw).hexdigest()
        shutil.copytree(base, target)
        (target / "state.json").write_bytes(raw)
        result = (target / "result.json").read_bytes()

        def point(value):
            item = [a for a in value["anchors"] if a["tree"] == "fee-ac73"][0]
            item["retained"] = {"path": f"{checker.RESTRICTED_REPRODUCTIONS}/{target.name}", "state_sha256": target.name,
                                "result_sha256": hashlib.sha256(result).hexdigest()}

        self.edit(REPRODUCTION, point)
        self.refused("record=reproduction.fee-ac73.retained field=status the retained reproduction is not baseline_ready "
                     "with exit 0", call=self.custody)

    def test_retained_private_bytes_in_a_docs_json_string_are_refused(self):
        bases = self.plant_private()
        summary = checker.check(self.root)
        log = (bases[1] / "logs/gate1.forge-test.log").read_text(encoding="utf-8")
        self.save(f"{checker.DOCS}/evidence/leak.json", {"log": log})
        self.refused("evidence/leak.json embeds a retained private file in a JSON string",
                     call=lambda: self.custody(summary))

    def test_sealed_target_source_digest_under_docs_is_refused(self):
        summary = checker.check(self.root)
        manifest = self.load(f"{BASELINE_RUN}/baseline-source-manifest.json")
        # A docs file whose bytes a sealed manifest names is target source, whatever its suffix says.
        leak = self.root / checker.DOCS / "evidence" / "leak.md"
        leak.write_bytes(b"")
        digest = hashlib.sha256(b"").hexdigest()
        manifest["src/Empty.sol"] = digest
        self.save(f"{BASELINE_RUN}/baseline-source-manifest.json", manifest)
        self.refused(f"evidence/leak.md has the digest of a sealed target source file digest={digest}",
                     call=lambda: self.custody(summary))


RETAINED_REPRODUCTIONS = ROOT / checker.RESTRICTED_REPRODUCTIONS


@unittest.skipUnless(RETAINED_REPRODUCTIONS.is_dir() and (RETAINED / "fixture-26006289" / "manifest.json").is_file(),
                     "the retained payloads live only in the run worktree's ignored restricted directory")
class RetainedEvidenceCustodyTests(ScratchCase):
    def test_evidence_custody_holds_over_the_retained_payloads(self):
        shutil.copytree(RETAINED, self.root / checker.RESTRICTED)
        result = checker.conformance(self.root, "evidence-custody", "anchor-and-inspect", EVIDENCE_CUSTODY)
        self.assertEqual((result["value"], result["private_runs"]), (True, 4))
        report = json.loads((self.root / EVIDENCE_CUSTODY).read_text(encoding="utf-8"))
        self.assertEqual((report["criterion"], report["value"], report["exit"]), ("evidence-custody", True, 0))

    def test_retained_reproduction_that_moved_is_refused(self):
        shutil.copytree(RETAINED, self.root / checker.RESTRICTED)
        base = next((self.root / checker.RESTRICTED_REPRODUCTIONS).iterdir())
        path = base / "storage-layout"
        target = sorted(path.iterdir())[0]
        target.write_bytes(target.read_bytes() + b"\n")
        self.refused("record=reproduction.", "does not recompute from the retained file",
                     call=lambda: checker.conformance(self.root, "evidence-custody", "anchor-and-inspect", EVIDENCE_CUSTODY))
        self.assertFalse((self.root / EVIDENCE_CUSTODY).exists())


if __name__ == "__main__":
    unittest.main()
