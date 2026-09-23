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
    # The registry evidence the role provider's source override is bound to.
    "docs/kickoff/1359/evidence/source-match-1590.json",
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

    def test_later_criteria_refuse_by_name(self):
        for criterion, stop in (("owner-handoffs", "step:3"), ("selector-rejection", "step:4"),
                                ("layout-rejection", "step:4"), ("sealed-coverage", "step:5"),
                                ("evidence-custody", "integration")):
            report = f".hexaemeron/design-reports/anchor-and-inspect-{criterion}.json"
            code, _, err = self.run_main("conformance", "--criterion", criterion,
                                         "--candidate", "anchor-and-inspect", "--report", report)
            self.assertEqual(code, 1, criterion)
            self.assertIn(f"{criterion} is not implemented yet; it blocks {stop}", err)
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


if __name__ == "__main__":
    unittest.main()
