"""Hold the #1963 V1 bundle checker to one failure mechanism per test."""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    # Registered first: dataclasses resolve their annotations through sys.modules,
    # and the CLI's own import of the implementation must reuse this module.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


v1 = load("kickoff_xray_1963_bundle", "scripts/kickoff_xray_1963_bundle.py")
cli = load("kickoff_xray_1963", "scripts/kickoff_xray_1963.py")
reporter = load("emit_kickoff_xray_1963_report", "tests/emit_kickoff_xray_1963_report.py")


def edit(root: Path, name: str, change) -> None:
    value = json.loads((root / name).read_bytes())
    change(value)
    (root / name).write_bytes(v1.encode(value))


class SyntheticSpecimenTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="issue-1963-test-")
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name) / "bundle"
        self.root.mkdir()
        self.profile = v1.synthetic_bundle(self.root)

    def refusal(self) -> dict:
        try:
            result = v1.check_bundle(self.root, self.profile)
        except Exception as exc:  # the contract is a returned refusal, never a raised exception
            self.fail(f"check_bundle raised {type(exc).__name__} instead of returning a refusal")
        self.assertEqual(result["status"], "failed", result)
        return result["findings"][0]

    def change(self, name: str, change) -> dict:
        edit(self.root, name, change)
        v1.write_manifest(self.root, self.profile)
        return self.refusal()

    def test_complete_specimen_passes(self):
        result = v1.check_bundle(self.root, self.profile)
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["actions"], {"read": 4, "state-changing": 5, "creation": 4})

    def test_altered_input_digest_refuses(self):
        def alter(value):
            value["inputs"][0]["sha256"] = "0" * 64
        self.assertEqual(self.change("sources.json", alter)["code"], "source-identity")

    def test_compiler_identity_with_a_numeric_boolean_refuses(self):
        def renumber(value):
            value["compiler"]["via_ir"] = 1
        self.assertEqual(self.change("sources.json", renumber)["code"], "compiler")

    def test_non_finite_number_refuses_at_decoding(self):
        data = (self.root / "execution.json").read_bytes()
        self.assertEqual(data.count(b'"exit": 1,'), 1)
        (self.root / "execution.json").write_bytes(data.replace(b'"exit": 1,', b'"exit": 1e999,'))
        v1.write_manifest(self.root, self.profile)
        finding = self.refusal()
        self.assertEqual((finding["code"], finding["path"]), ("json", "execution.json"))

    def test_dropped_source_file_refuses_against_the_pinned_projection(self):
        def drop(value):
            value["inputs"][0]["files"].pop()
        self.assertEqual(self.change("sources.json", drop)["code"], "source-membership")

    def test_changed_line_count_refuses_against_the_pinned_projection(self):
        def lengthen(value):
            value["inputs"][0]["files"][0]["lines"] += 1
        self.assertEqual(self.change("sources.json", lengthen)["code"], "source-membership")

    def test_context_bound_to_another_input_refuses(self):
        def rebind(value):
            value["contexts"][0]["input"] = "SyntheticLens"
        self.assertEqual(self.change("sources.json", rebind)["code"], "source-context")

    def test_unbound_context_disposition_refuses(self):
        def mark(value):
            for row in value["inputs"][0]["files"]:
                if row["disposition"] == "support":
                    row["disposition"] = "context"
                    return
        self.assertEqual(self.change("sources.json", mark)["code"], "source-context")

    def test_duplicate_json_key_refuses(self):
        data = (self.root / "linkage.json").read_bytes()
        (self.root / "linkage.json").write_bytes(data.replace(b"{", b'{"schema": "x", ', 1))
        v1.write_manifest(self.root, self.profile)
        self.assertEqual(self.refusal()["code"], "json")

    def test_duplicate_key_detail_stays_bounded(self):
        key = "k" * 10000
        data = (self.root / "actions.json").read_bytes()
        (self.root / "actions.json").write_bytes(data.replace(b"{", f'{{"{key}": 1, "{key}": 2, '.encode(), 1))
        v1.write_manifest(self.root, self.profile)
        finding = self.refusal()
        self.assertEqual(finding["code"], "json")
        self.assertLessEqual(len(finding["detail"]), 128)

    def test_escaping_manifest_path_refuses(self):
        def escape(value):
            value["artifacts"][0]["path"] = "../outside.json"
        edit(self.root, "manifest.json", escape)
        self.assertEqual(self.refusal()["code"], "unsafe-path")

    def test_linked_artifact_refuses(self):
        (self.root / "README.md").unlink()
        (self.root / "README.md").symlink_to("study.md")
        self.assertEqual(self.refusal()["code"], "unsafe-path")

    def test_oversized_artifact_refuses_before_hashing(self):
        with (self.root / "README.md").open("ab") as stream:
            stream.truncate(v1.MAX_FILE_BYTES + 1)
        self.assertEqual(self.refusal()["code"], "limit")

    def test_identity_whose_id_disagrees_with_its_fields_refuses(self):
        def mislabel(value):
            row = next(row for row in value["identities"] if row["kind"] == "read")
            row["kind"] = "state-changing"
            row["mutability"] = "nonpayable"
        self.assertEqual(self.change("denominator-inputs.json", mislabel)["code"], "action-identity")

    def test_non_canonical_signature_refuses(self):
        def widen(value):
            row = next(row for row in value["identities"] if row["signature"] == "deposit(uint256)")
            row["signature"] = "deposit(uint)"
            row["selector"] = v1.selector("deposit(uint)")
            row["id"] = v1.action_id(row)
        self.assertEqual(self.change("denominator-inputs.json", widen)["code"], "signature")

    def test_identity_context_of_the_wrong_type_refuses(self):
        def confuse(value):
            value["identities"][0]["context"] = ["Pool"]
        self.assertEqual(self.change("denominator-inputs.json", confuse)["code"], "action-identity")

    def test_identity_mutability_of_the_wrong_type_refuses(self):
        def confuse(value):
            value["identities"][0]["mutability"] = ["nonpayable"]
        self.assertEqual(self.change("denominator-inputs.json", confuse)["code"], "action-identity")

    def test_selector_that_differs_from_its_signature_refuses(self):
        def reselect(value):
            row = next(row for row in value["identities"] if row["signature"] == "deposit(uint256)")
            row["selector"] = "0x00000000"
        self.assertEqual(self.change("denominator-inputs.json", reselect)["code"], "signature")

    def test_lost_implicit_creation_path_refuses(self):
        # An ABI-only pin can itself lack the implicit creation path, so the pin is rebound to the reduced set.
        def drop(value):
            value["identities"] = [row for row in value["identities"] if row["signature"] != "constructor()"]
        edit(self.root, "denominator-inputs.json", drop)
        identities = json.loads((self.root / "denominator-inputs.json").read_bytes())["identities"]
        projection = [{key: row[key] for key in ("id", "selector", "mutability", "declared_in", "origin")}
                      for row in sorted(identities, key=lambda row: row["id"])]
        self.profile = dataclasses.replace(
            self.profile, denominator=(len(identities), v1.digest(v1.canonical(projection))))
        v1.write_manifest(self.root, self.profile)
        finding = self.refusal()
        self.assertEqual((finding["code"], finding["detail"]),
                         ("denominator", "each context needs exactly one creation path: Pool"))

    def test_joint_omission_refuses_against_the_denominator_pin(self):
        v1._omit_identity_everywhere(self.root, self.profile)
        self.assertEqual(self.refusal()["code"], "denominator")

    def test_action_signature_that_differs_from_the_denominator_refuses(self):
        def rename(value):
            row = next(row for row in value["actions"] if row["signature"] == "deposit(uint256)")
            row["signature"] = "depositFor(uint256)"
        self.assertEqual(self.change("actions.json", rename)["code"], "signature")

    def test_action_missing_from_the_inventory_refuses(self):
        def omit(value):
            value["actions"] = [row for row in value["actions"] if row["kind"] != "read"]
        self.assertEqual(self.change("actions.json", omit)["code"], "action-membership")

    def test_uncovered_flow_family_refuses(self):
        def narrow(value):
            for row in value["actions"]:
                if "escrow-release" in row["families"]:
                    row["families"] = ["administration"]
        self.assertEqual(self.change("actions.json", narrow)["code"], "families")

    def test_missing_disposition_refuses(self):
        def strip(value):
            del value["actions"][0]["disposition"]
        self.assertEqual(self.change("linkage.json", strip)["code"], "disposition")

    def test_unresolved_action_without_a_gap_refuses(self):
        def hide(value):
            row = next(row for row in value["actions"] if row["disposition"] == "unresolved")
            row["gaps"] = []
        self.assertEqual(self.change("linkage.json", hide)["code"], "disposition")

    def test_unknown_marked_eventless_refuses(self):
        def flatten(value):
            row = next(row for row in value["actions"] if row["disposition"] == "unresolved")
            row["disposition"] = "eventless"
        self.assertEqual(self.change("linkage.json", flatten)["code"], "disposition")

    def test_stale_source_reference_refuses(self):
        def stale(value):
            value["actions"][0]["source_refs"] = ["src/Pool.sol:121"]
        self.assertEqual(self.change("linkage.json", stale)["code"], "source-reference")

    def test_reference_into_another_input_needs_that_inputs_file(self):
        def cross(value):
            value["actions"][0]["source_refs"] = ["SyntheticLens@src/Vault.sol:1"]
        self.assertEqual(self.change("linkage.json", cross)["code"], "source-reference")

    def test_semantic_edit_after_review_refuses(self):
        def amend(value):
            value["actions"][0]["reason"] = "changed after the review was bound"
        self.assertEqual(self.change("linkage.json", amend)["code"], "review-binding")

    def test_producer_reviewing_their_own_record_refuses(self):
        def same(value):
            value["reviewer"] = " Synthetic-Producer "
        self.assertEqual(self.change("review.json", same)["code"], "review-independence")

    def test_open_review_finding_refuses(self):
        def reopen(value):
            value["findings"][0]["status"] = "open"
        self.assertEqual(self.change("review.json", reopen)["code"], "review-findings")

    def test_review_that_skips_an_action_refuses(self):
        def skip(value):
            value["reviewed_actions"].pop()
        self.assertEqual(self.change("review.json", skip)["code"], "review-coverage")

    def test_stale_visual_inspection_refuses(self):
        (self.root / "architecture.svg").write_text("<svg>" + " ".join(self.profile.contexts) + "<g/></svg>\n")
        fresh = v1.digest((self.root / "architecture.svg").read_bytes())

        def rebind_reviewed_artifact(value):
            for row in value["artifacts"]:
                if row["path"] == "architecture.svg":
                    row["sha256"] = fresh
        finding = self.change("review.json", rebind_reviewed_artifact)
        self.assertEqual((finding["code"], finding["path"]), ("review-binding", "review.visual_inspection"))

    def test_architecture_edge_endpoint_of_the_wrong_type_refuses(self):
        def confuse(value):
            value["edges"][0]["from"] = ["factory"]
        finding = self.change("architecture.json", confuse)
        self.assertEqual((finding["code"], finding["path"]), ("report", "architecture.json"))

    def test_architecture_node_label_outside_the_schema_refuses(self):
        def confuse(value):
            value["nodes"][0]["label"] = {"nested": ["label"]}
        self.assertEqual(self.change("architecture.json", confuse)["code"], "shape")

    def test_rebound_manifest_does_not_hide_an_omitted_artifact(self):
        (self.root / "invariants.md").unlink()
        v1.write_manifest(self.root, self.profile)
        finding = self.refusal()
        self.assertEqual((finding["code"], finding["path"]), ("inventory", "manifest.artifacts"))

    def test_failed_attempt_recorded_as_passing_refuses(self):
        def relabel(value):
            row = next(row for row in value["records"] if row["exit"] != 0)
            row["status"] = "passed"
        self.assertEqual(self.change("execution.json", relabel)["code"], "execution")

    def test_entry_point_view_missing_an_action_refuses(self):
        body = (self.root / "entry-points.md").read_text()
        (self.root / "entry-points.md").write_text(body.replace("release()", "release"))
        v1.write_manifest(self.root, self.profile)
        self.assertEqual(self.refusal()["code"], "report")


class ScaffoldMatrixTests(unittest.TestCase):
    def test_every_named_hostile_specimen_refuses_with_its_code(self):
        result = v1.scaffold_matrix()
        self.assertEqual(result["positive"]["status"], "passed", result["positive"])
        unexpected = [row for row in result["specimens"] if row["status"] != "refused-as-expected"]
        self.assertEqual(unexpected, [])
        self.assertEqual(len(result["specimens"]), len(v1.SCAFFOLD))

    def test_demonstration_set_names_the_study_refusals(self):
        self.assertEqual([name for name, _, _ in v1.DEMONSTRATION], [
            "altered-source-identity", "omitted-action", "mismatched-signature", "missing-disposition",
            "stale-source-reference", "stale-review-digest", "incomplete-review"])


class SignatureTests(unittest.TestCase):
    def test_canonical_forms_are_accepted(self):
        for value in ("totalSupply()", "deposit(uint256)", "f((uint128,uint16)[],bytes32[2],address)",
                      "constructor()", "g(((bool)[3])[])"):
            with self.subTest(value=value):
                self.assertTrue(v1.canonical_signature(value))

    def test_non_canonical_forms_are_refused(self):
        for value in ("deposit(uint)", "deposit(uint256 amount)", "f(uint7)", "f(bytes33)", "f(uint256[01])",
                      "f(uint256,)", "f(", "1f()", "f() ", "f(byte)"):
            with self.subTest(value=value):
                self.assertFalse(v1.canonical_signature(value))

    def test_selector_is_legacy_keccak(self):
        self.assertEqual(v1.selector("transfer(address,uint256)"), "0xa9059cbb")


class ProductionPinTests(unittest.TestCase):
    def test_specification_copies_match_the_receipts(self):
        for name, expected in v1.PRODUCTION.specifications.items():
            data = (v1.DEFAULT_BUNDLE / name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, name)

    def test_selection_report_copies_match_the_design_record(self):
        design = json.loads((v1.DEFAULT_BUNDLE / "design-evidence.json").read_bytes())
        resolved = {row["report"]["path"]: row["report"]["sha256"] for row in design["results"]
                    if row["state"] == "pass"}
        self.assertEqual(set(resolved), set(v1.V1_SELECTION_REPORTS))
        for path, expected in resolved.items():
            self.assertEqual(hashlib.sha256((v1.DEFAULT_BUNDLE / path).read_bytes()).hexdigest(), expected, path)

    def test_input_and_commit_pins_match_the_receipted_study(self):
        study = (v1.DEFAULT_BUNDLE / "study.md").read_text()
        for name, pin in v1.V1_INPUTS.items():
            self.assertIn(f"`{name}` | `{pin.sha256}`", study)
        for commit in (v1.CORE_COMMIT, v1.SENTINEL_COMMIT, v1.LENS_CLOSEST_COMMIT, v1.SKILLS_START):
            self.assertIn(commit, study)
        self.assertEqual({pin.input for pin in v1.V1_CONTEXTS.values()}, set(v1.V1_INPUTS))
        self.assertEqual(len(v1.V1_CONTEXTS), 7)

    def test_anchor_digests_match_the_committed_records(self):
        for anchor in v1.V1_ANCHORS.values():
            data = (ROOT / anchor["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), anchor["sha256"], anchor["path"])



def production_record(name: str) -> dict:
    return json.loads((v1.DEFAULT_BUNDLE / name).read_bytes())


class ProductionBundleTests(unittest.TestCase):
    """The committed V1 map, read as data; hostile edits run on a copy."""

    def test_committed_bundle_passes(self):
        result = v1.check_bundle()
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["actions"], {"read": 148, "state-changing": 62, "creation": 7})

    def test_denominator_keeps_inherited_overloaded_and_implicit_identities(self):
        rows = {row["id"]: row for row in production_record("denominator-inputs.json")["identities"]}
        market = "WildcatMarketControllerFactory:WildcatMarket"
        self.assertEqual(rows[f"{market}:creation:constructor()"]["origin"], "ast")
        self.assertEqual(rows[f"{market}:creation:constructor()"]["declared_in"], "WildcatMarketBase")
        self.assertEqual(rows[f"{market}:state-changing:approve(address,uint256)"]["declared_in"], "WildcatMarketToken")
        controller = "WildcatMarketControllerFactory:WildcatMarketController:read:"
        self.assertIn(f"{controller}getAuthorizedLenders()", rows)
        self.assertIn(f"{controller}getAuthorizedLenders(uint256,uint256)", rows)

    def test_arch_controller_links_name_only_emitted_variants(self):
        catalogue = set(production_record("denominator-inputs.json")["events"]["WildcatArchController"])
        self.assertIn("AssetBlacklisted(address)", catalogue)
        self.assertNotIn("AssetBlacklisted()", catalogue)
        for row in production_record("linkage.json")["actions"]:
            for event in row["events"]:
                if event["emitter"] == "WildcatArchController":
                    self.assertIn(event["event"], catalogue, row["id"])

    def test_interface_only_arch_variant_refuses(self):
        def interface_variant(value):
            for row in value["actions"]:
                for event in row["events"]:
                    if event["event"] == "AssetBlacklisted(address)":
                        event["event"] = "AssetBlacklisted()"
        finding = mutated_production("linkage.json", interface_variant)
        self.assertEqual((finding["code"], finding["detail"]),
                         ("signature", "event is absent from the emitting context's compiler ABI"))

    def test_interface_named_emitter_refuses(self):
        # S2-R1-03: naming the interface as emitter used to skip the ABI catalogue entirely.
        def interface_emitter(value):
            for row in value["actions"]:
                for event in row["events"]:
                    if event["event"] == "AssetBlacklisted(address)":
                        event["event"], event["emitter"] = "AssetBlacklisted()", "IWildcatArchController"
        finding = mutated_production("linkage.json", interface_emitter)
        self.assertEqual((finding["code"], finding["detail"]), ("signature", "emitter is not a scoped context"))

    def test_emit_site_in_another_inputs_copy_refuses(self):
        # S2-R1-03: the factory input carries its own copy of the sentinel source, so an unprefixed
        # reference resolves there although the sentinel context is bound to its own input.
        def rehome(value):
            for row in value["actions"]:
                for event in row["events"]:
                    if event["source_ref"] == "WildcatSanctionsSentinel@src/WildcatSanctionsSentinel.sol:135":
                        event["source_ref"] = "src/WildcatSanctionsSentinel.sol:135"
                        return
            raise AssertionError("no transitive NewSanctionsEscrow emit site to rehome")
        finding = mutated_production("linkage.json", rehome)
        self.assertEqual((finding["code"], finding["detail"]),
                         ("source-reference", "emit site lies outside the emitter's input"))

    def test_source_exceptions_stay_recorded(self):
        inputs = {row["id"]: row for row in production_record("sources.json")["inputs"]}
        self.assertEqual(inputs["MarketLensMixed"]["differing_files"], list(v1.LENS_DIFFERING))
        self.assertEqual(inputs["WildcatMarketControllerFactory"]["commits"], list(v1.CORE_EQUIVALENTS))
        self.assertEqual(inputs["WildcatSanctionsSentinel"]["commits"], [v1.SENTINEL_COMMIT])
        self.assertIsNotNone(inputs["MarketLensMixed"]["binding_limit"])

    def test_every_scoped_action_has_one_disposition(self):
        rows = production_record("linkage.json")["actions"]
        scoped = [row for row in production_record("denominator-inputs.json")["identities"] if row["kind"] != "read"]
        self.assertEqual(sorted(row["id"] for row in rows), sorted(row["id"] for row in scoped))
        self.assertTrue(all(row["disposition"] in v1.DISPOSITIONS for row in rows))

    def test_repayment_events_name_a_payer_not_a_debtor(self):
        for row in production_record("linkage.json")["actions"]:
            if any(event["event"] == "DebtRepaid(address,uint256)" for event in row["events"]):
                self.assertTrue(any("payer" in note for note in row["attribution"]), row["id"])

    def test_producer_argv_names_the_output_its_log_printed(self):
        # S2-R1-01: derive and build-sources recorded the bundle as --out while their logs printed a scratch path.
        checked = set()
        for record in production_record("execution.json")["records"]:
            if record["log"] is None or "--out" not in record["argv"]:
                continue
            first = (v1.DEFAULT_BUNDLE / record["log"]["path"]).read_text(encoding="utf-8").splitlines()[0]
            if not first.startswith("{"):
                continue
            argv = record["argv"]
            self.assertEqual(argv[argv.index("--out") + 1], json.loads(first)["out"], record["id"])
            checked.add(record["id"])
        self.assertEqual(checked, {"derive", "build-sources"})

    def test_close_market_rows_keep_the_unprocessed_expired_batch(self):
        # S2-R1-02: closeMarket checks unpaidBatches before _getUpdatedState(), so an expired batch that no state
        # update has processed is recorded unpaid after the check and stays unpaid once the market is closed.
        rows = {row["id"]: row for row in production_record("linkage.json")["actions"]}
        market = rows["WildcatMarketControllerFactory:WildcatMarket:state-changing:closeMarket()"]
        controller = rows["WildcatMarketControllerFactory:WildcatMarketController:state-changing:closeMarket(address)"]
        self.assertNotIn("reverts while any withdrawal batch is unpaid", market["guards"])
        self.assertTrue(any("precedes _getUpdatedState()" in guard for guard in market["guards"]))
        self.assertTrue(any("RepayToClosedMarket" in effect for effect in market["state_effects"]))
        self.assertTrue(any("no state update has processed yet is not checked" in guard
                            for guard in controller["guards"]))
        invariants = (v1.DEFAULT_BUNDLE / "invariants.md").read_text(encoding="utf-8")
        self.assertNotIn("Closure cannot strand", invariants)

    def test_dropping_a_denominator_identity_from_every_record_refuses(self):
        def drop(value):
            value["identities"] = [row for row in value["identities"]
                                   if not row["signature"].startswith("getAuthorizedLendersCount")]
        self.assertEqual(mutated_production("denominator-inputs.json", drop)["code"], "denominator")


def mutated_production(name: str, change) -> dict:
    """Copy the committed bundle, apply one edit, rebind its manifest and return the refusal."""
    with tempfile.TemporaryDirectory(prefix="issue-1963-production-") as scratch:
        root = Path(scratch) / "bundle"
        shutil.copytree(v1.DEFAULT_BUNDLE, root)
        edit(root, name, change)
        v1.write_manifest(root, v1.PRODUCTION)
        result = v1.check_bundle(root)
    assert result["status"] == "failed", result
    return result["findings"][0]


derivation = load("kickoff_xray_1963_derive", "scripts/kickoff_xray_1963_derive.py")


class DerivationTests(unittest.TestCase):
    """The ABI/AST projection, on a hand-built compiler output; no compiler runs."""

    SOURCE = "contract Base {\n  constructor() {}\n  function f(uint256) external {}\n}\ncontract A is Base {\n  uint256 public x;\n}\n"

    def output(self, abi):
        def at(text):
            return f"{self.SOURCE.index(text)}:1:0"
        selector = lambda signature: v1.selector(signature)[2:]  # noqa: E731
        base = {"nodeType": "ContractDefinition", "id": 1, "name": "Base", "linearizedBaseContracts": [1], "nodes": [
            {"nodeType": "FunctionDefinition", "kind": "constructor", "implemented": True, "src": at("constructor()")},
            {"nodeType": "FunctionDefinition", "kind": "function", "name": "f", "implemented": True,
             "functionSelector": selector("f(uint256)"), "src": at("function f")}]}
        child = {"nodeType": "ContractDefinition", "id": 2, "name": "A", "linearizedBaseContracts": [2, 1], "nodes": [
            {"nodeType": "VariableDeclaration", "name": "x", "functionSelector": selector("x()"), "src": at("uint256 public x")}]}
        return {"sources": {"src/A.sol": {"id": 0, "ast": {"nodeType": "SourceUnit", "nodes": [base, child]}}},
                "contracts": {"src/A.sol": {"A": {"abi": abi}}}}

    ABI = [{"type": "function", "name": "f", "inputs": [{"type": "uint256"}], "stateMutability": "nonpayable"},
           {"type": "function", "name": "x", "inputs": [], "stateMutability": "view"},
           {"type": "event", "name": "E", "inputs": [{"type": "address"}], "anonymous": False},
           {"type": "error", "name": "Bad", "inputs": []}]

    def test_projection_resolves_inheritance_getters_and_the_implicit_constructor(self):
        rows, events = derivation.project("A", "src/A.sol", "In", {"src/A.sol": {"content": self.SOURCE}}, self.output(self.ABI))
        found = {row["signature"]: (row["kind"], row["declared_in"], row["source_ref"], row["origin"]) for row in rows}
        self.assertEqual(found, {
            "f(uint256)": ("state-changing", "Base", "src/A.sol:3", "abi"),
            "x()": ("read", "A", "src/A.sol:6", "abi"),
            "constructor()": ("creation", "Base", "src/A.sol:2", "ast")})
        self.assertEqual(events, ["E(address)"])

    def test_a_tuple_parameter_takes_its_canonical_form(self):
        abi = [{"type": "function", "name": "f", "stateMutability": "nonpayable",
                "inputs": [{"type": "tuple[]", "components": [{"type": "uint128"}, {"type": "uint16"}]}]}]
        self.assertEqual(derivation.abi_type(abi[0]["inputs"][0]), "(uint128,uint16)[]")

    def test_a_declaration_missing_from_the_linearization_refuses(self):
        abi = [{"type": "function", "name": "g", "inputs": [], "stateMutability": "nonpayable"}]
        with self.assertRaises(derivation.DeriveError) as raised:
            derivation.project("A", "src/A.sol", "In", {"src/A.sol": {"content": self.SOURCE}}, self.output(abi))
        self.assertEqual(raised.exception.finding["code"], "derivation")

    def test_a_compiler_file_with_another_digest_is_refused_before_it_runs(self):
        with self.assertRaises(derivation.DeriveError) as raised:
            derivation.compile_input(Path("."), b"{}", lambda relative: b"not the pinned wrapper", "0" * 64)
        self.assertEqual(raised.exception.finding, {"code": "compiler", "path": derivation.WRAPPER,
                                                    "detail": "compiler wrapper digest differs"})


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="issue-1963-admit-")
        self.addCleanup(scratch.cleanup)
        self.directory = Path(scratch.name)
        (self.directory / v1.ACCEPTED_INPUTS).mkdir(parents=True)
        self.value = {"language": "Solidity", "sources": {"src/A.sol": {"content": "contract A {}\n"},
                                                          "src/B.sol": {"content": "contract B {}"}},
                      "settings": {"evmVersion": "shanghai", "viaIR": True, "metadata": {"bytecodeHash": "none"},
                                   "optimizer": {"enabled": True, "runs": 200}}}
        self.write(self.value)

    def write(self, value, raw=None):
        data = raw if raw is not None else json.dumps(value).encode()
        (self.directory / v1.ACCEPTED_INPUTS / "Synthetic.json").write_bytes(data)
        projection = v1.source_projection(value, "Synthetic")
        pin = v1.InputPin(hashlib.sha256(data).hexdigest(), "synthetic", "https://example.invalid", len(projection),
                          v1.digest(v1.canonical(projection)))
        self.profile = dataclasses.replace(v1.PRODUCTION, inputs={"Synthetic": pin})

    def admit(self):
        return v1.admit_inputs(self.directory, self.profile)

    def test_matching_input_is_admitted_without_payload(self):
        result = self.admit()
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["inputs"][0]["files"], 2)
        self.assertNotIn("contract A", json.dumps(result))

    def test_changed_input_byte_refuses(self):
        (self.directory / v1.ACCEPTED_INPUTS / "Synthetic.json").write_bytes(json.dumps(self.value).encode() + b" ")
        self.assertEqual(self.admit()["inputs"][0]["finding"]["code"], "source-identity")

    def test_changed_compiler_setting_refuses(self):
        value = json.loads(json.dumps(self.value))
        value["settings"]["viaIR"] = False
        self.write(value)
        self.assertEqual(self.admit()["inputs"][0]["finding"]["code"], "compiler")

    def test_duplicate_key_in_an_input_refuses(self):
        raw = json.dumps(self.value).encode().replace(b"{", b'{"language": "Solidity", ', 1)
        self.write(self.value, raw)
        self.assertEqual(self.admit()["inputs"][0]["finding"]["code"], "json")


class CommandTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="issue-1963-cli-")
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_parser_accepts_the_runbook_and_resolver_commands(self):
        parser = cli.build_parser()
        demo = parser.parse_args(["demo", "--bundle", "docs/kickoff/1963", "--report", ".hexaemeron/v1-demo.json"])
        self.assertEqual((demo.command, demo.bundle, demo.report),
                         ("demo", Path("docs/kickoff/1963"), Path(".hexaemeron/v1-demo.json")))
        design = json.loads((v1.DEFAULT_BUNDLE / "design-evidence.json").read_bytes())
        for row in design["results"]:
            if row["state"] == "pending":
                with self.subTest(resolver=row["resolver"]):
                    parser.parse_args(row["resolver"].split()[2:])

    def test_checked_scaffold_report_is_one_closed_passing_record(self):
        report = self.scratch / "scaffold.json"
        code, _, _ = self.run_cli("design-report", "--candidate", "shared-input-index",
                                  "--criterion", "checked-scaffold", "--report", str(report))
        self.assertEqual(code, 0)
        value = json.loads(report.read_bytes())
        self.assertEqual(set(value), {"schema", "candidate", "criterion", "value", "unit", "command", "exit"})
        self.assertEqual((value["value"], value["exit"], value["unit"]), (True, 0, "boolean"))

    def test_existing_report_path_is_refused(self):
        report = self.scratch / "exists.json"
        report.write_bytes(b"{}\n")
        code, _, err = self.run_cli("design-report", "--candidate", "shared-input-index",
                                    "--criterion", "reviewed-map", "--report", str(report))
        self.assertEqual((code, report.read_bytes()), (2, b"{}\n"))
        self.assertIn("report-write", err)

    def test_unselected_candidate_is_refused(self):
        code, _, err = self.run_cli("design-report", "--candidate", "component-copies",
                                    "--criterion", "checked-scaffold", "--report", str(self.scratch / "c.json"))
        self.assertEqual(code, 2)
        self.assertFalse((self.scratch / "c.json").exists())
        self.assertIn("candidate", err)

    def test_demonstration_of_the_unfinished_bundle_fails_offline(self):
        # The committed bundle without its review and manifest is the unfinished bundle.
        root = self.scratch / "unfinished"
        shutil.copytree(v1.DEFAULT_BUNDLE, root)
        (root / "review.json").unlink()
        (root / "manifest.json").unlink()
        report = self.scratch / "demo.json"
        code, _, _ = self.run_cli("demo", "--bundle", str(root), "--report", str(report))
        value = json.loads(report.read_bytes())
        self.assertEqual((code, value["status"], value["network"]), (1, "failed", "disabled"))
        self.assertEqual(value["specimens"], [])

    def test_network_is_refused_during_the_demonstration(self):
        # A closed local port also raises OSError, so the refusal is identified by its own message.
        originals = (socket.socket, socket.create_connection, socket.getaddrinfo)
        with v1.network_disabled():
            with self.assertRaisesRegex(OSError, "network use is disabled"):
                socket.create_connection(("127.0.0.1", 9))
        self.assertEqual((socket.socket, socket.create_connection, socket.getaddrinfo), originals)

    def test_manifest_of_a_linked_bundle_is_a_json_refusal(self):
        root = self.scratch / "bundle"
        root.mkdir()
        (root / "study.md").write_bytes(b"# study\n")
        (root / "README.md").symlink_to("study.md")
        try:
            code, _, err = self.run_cli("manifest", "--bundle", str(root))
        except Exception as exc:  # the contract is an exit code and a JSON finding, never a raised exception
            self.fail(f"manifest raised {type(exc).__name__} instead of refusing")
        self.assertEqual((code, json.loads(err)["code"]), (1, "unsafe-path"))
        self.assertFalse((root / "manifest.json").exists())

    def test_missing_command_arguments_are_a_usage_error(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            cli.main(["demo"])
        self.assertEqual(raised.exception.code, 2)


# The V2 map and emitter records at the run base 1f772fc0: file count and the SHA-256 of the sorted
# [path, SHA-256] list, computed from that commit's Git objects.
V2_RECORDS = ("docs/kickoff/1363", "docs/kickoff/1361")
V2_RECORDS_AT_BASE = (110, "a3bcf621fb12290bb909c1a52b65cbfdaceaaf79aa4fc894c3318d6a49a8d798")
PAYLOAD_MARKERS = (b"pragma solidity", b"SPDX-License-Identifier", b"```solidity")
COMPILER_KEYS = {"abi", "ast", "bytecode", "content", "deployedBytecode", "evm", "language", "metadata", "settings",
                 "sources"}
DEMO_COMMAND = ("python3 scripts/kickoff_xray_1963.py demo --bundle docs/kickoff/1963 "
                "--report docs/kickoff/1963/demonstration.json")
ADMIT_COMMAND = ("python3 scripts/kickoff_xray_1963.py admit --inputs .hexaemeron/research/accepted-corpus "
                 "--report docs/kickoff/1963/admission.json")


class ObservationRecordTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="issue-1963-records-")
        self.addCleanup(scratch.cleanup)
        self.scratch = Path(scratch.name)

    # S3-R1-01: the checker never reads either record, so these two tests close their keys.
    def test_committed_demonstration_matches_a_fresh_offline_run(self):
        record = json.loads((v1.DEFAULT_BUNDLE / "demonstration.json").read_bytes())
        fresh = v1.demonstrate(v1.DEFAULT_BUNDLE)
        self.assertEqual(set(record), set(fresh) | {"command", "exit"})
        for key in ("schema", "status", "network", "manifest_sha256", "positive", "specimens", "counts", "boundary"):
            self.assertEqual(record[key], fresh[key], key)
        manifest = hashlib.sha256((v1.DEFAULT_BUNDLE / "manifest.json").read_bytes()).hexdigest()
        self.assertEqual((record["manifest_sha256"], record["status"], record["exit"], record["command"]),
                         (manifest, "passed", 0, DEMO_COMMAND))
        self.assertEqual(record["counts"], {"expected": 7, "refused_as_expected": 7})
        self.assertIs(type(record["duration_ms"]), int)
        self.assertGreaterEqual(record["duration_ms"], 0)

    def test_committed_admission_reports_every_pinned_input_by_identity_only(self):
        record = json.loads((v1.DEFAULT_BUNDLE / "admission.json").read_bytes())
        shape = v1.admit_inputs(self.scratch)  # an empty corpus: every input refused, the envelope unchanged
        self.assertEqual(set(record), set(shape) | {"command", "exit"})
        self.assertEqual((record["schema"], record["boundary"]), (shape["schema"], shape["boundary"]))
        self.assertEqual((record["status"], record["exit"], record["command"]), ("passed", 0, ADMIT_COMMAND))
        self.assertIs(type(record["duration_ms"]), int)
        self.assertGreaterEqual(record["duration_ms"], 0)
        self.assertEqual(len(record["inputs"]), len(v1.PRODUCTION.inputs))
        rows = {row["id"]: row for row in record["inputs"]}
        self.assertEqual(set(rows), set(v1.PRODUCTION.inputs))
        for name, pin in v1.PRODUCTION.inputs.items():
            row = rows[name]
            self.assertEqual(set(row), {"id", "expected_sha256", "sha256", "files", "projection", "status"})
            self.assertEqual((row["expected_sha256"], row["sha256"], row["files"], row["projection"], row["status"]),
                             (pin.sha256, pin.sha256, pin.files, pin.projection, "admitted"))

    def test_observation_records_stay_outside_the_fixed_inventory(self):
        root = self.scratch / "bundle"
        shutil.copytree(v1.DEFAULT_BUNDLE, root)
        self.assertEqual(v1.check_bundle(root)["status"], "passed")
        (root / "demonstration.json").unlink()
        (root / "admission.json").unlink()
        self.assertEqual(v1.check_bundle(root)["status"], "passed")
        (root / "demonstration.json").symlink_to(root / "README.md")
        self.assertEqual(v1.check_bundle(root)["findings"][0]["code"], "unsafe-path")
        (root / "demonstration.json").unlink()
        (root / "stray.json").write_bytes(b"{}\n")
        self.assertEqual(v1.check_bundle(root)["findings"][0]["code"], "inventory")

    def test_unexpected_acceptance_fails_the_demonstration(self):
        accepting = (("accepted-edit", "signature", lambda root, profile: None),)
        with mock.patch.object(v1, "DEMONSTRATION", accepting):
            result = v1.demonstrate(v1.DEFAULT_BUNDLE)
        self.assertEqual((result["status"], result["specimens"][0]["status"]), ("failed", "unexpected"))

    def test_specimen_error_fails_the_demonstration(self):
        def broken(root, profile):
            raise OSError("infrastructure failure")
        with mock.patch.object(v1, "DEMONSTRATION", (("broken-edit", "signature", broken),)):
            result = v1.demonstrate(v1.DEFAULT_BUNDLE)
        self.assertEqual((result["status"], result["specimens"][0]["observed"]), ("failed", "specimen-error"))

    def test_every_demonstration_check_runs_with_the_network_refused(self):
        # S3-R1-02: the record's "network" value is fixed text, so this binds it to the guard around each check.
        # A closed local port also raises OSError, so the refusal is identified by its own message.
        refusals, check = [], v1.check_bundle

        def probing(root, profile=v1.PRODUCTION):
            try:
                socket.create_connection(("127.0.0.1", 9), timeout=1)
            except OSError as exc:
                refusals.append(str(exc))
            return check(root, profile)

        with mock.patch.object(v1, "check_bundle", probing):
            result = v1.demonstrate(v1.DEFAULT_BUNDLE)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(refusals, ["network use is disabled during the #1963 demonstration"]
                         * (1 + len(v1.DEMONSTRATION)))


class PublicationBoundaryTests(unittest.TestCase):
    def test_published_bundle_carries_no_source_or_compiler_payload(self):
        def walk(value, where):
            if isinstance(value, dict):
                self.assertFalse(COMPILER_KEYS & set(value), where)
                for item in value.values():
                    walk(item, where)
            elif isinstance(value, list):
                for item in value:
                    walk(item, where)
            elif isinstance(value, str):
                self.assertLessEqual(len(value), 4096, where)
        files = [path for path in sorted(v1.DEFAULT_BUNDLE.rglob("*")) if path.is_file()]
        self.assertIn(v1.DEFAULT_BUNDLE / "admission.json", files)
        for path in files:
            data = path.read_bytes()
            for marker in PAYLOAD_MARKERS:
                self.assertNotIn(marker, data, path)
            if path.suffix == ".json":
                walk(json.loads(data), path)

    def test_recovery_gives_the_assembler_its_required_input(self):
        # S3-R1-03: the Recovery step named assemble_bundle.py without --xray, which its parser requires.
        readme = (v1.DEFAULT_BUNDLE / "README.md").read_text(encoding="utf-8")
        recovery = readme.split("\n## Recovery\n", 1)[1].split("\n## ", 1)[0]
        mentions = re.findall(r"`[^`]*assemble_bundle\.py[^`]*`", recovery)
        self.assertTrue(mentions)
        for mention in mentions:
            self.assertRegex(mention, r"--xray \S+`\Z", mention)

    def test_v2_map_and_emitter_records_match_the_starting_tree(self):
        rows = sorted([path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()]
                      for top in V2_RECORDS for path in (ROOT / top).rglob("*") if path.is_file())
        listing = json.dumps(rows, separators=(",", ":")).encode()
        self.assertEqual((len(rows), hashlib.sha256(listing).hexdigest()), V2_RECORDS_AT_BASE)


class ReporterTests(unittest.TestCase):
    def setUp(self):
        scratch = tempfile.TemporaryDirectory(prefix="issue-1963-report-")
        self.addCleanup(scratch.cleanup)
        previous = os.getcwd()
        os.chdir(scratch.name)
        self.addCleanup(os.chdir, previous)

    def emit(self, modules):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = reporter.main(["--report", "report.json"], modules=modules)
        return code, json.loads(Path("report.json").read_bytes())

    def test_absent_module_is_an_error_not_an_assertion_failure(self):
        code, report = self.emit(("tests.no_such_module_for_issue_1963",))
        self.assertEqual(code, 1)
        self.assertEqual((report["failures"], report["errors"], report["testsRun"]), (0, 1, 1))

    def test_passing_surface_reports_its_real_counts(self):
        code, report = self.emit(("tests.test_kickoff_xray_1963.SignatureTests",))
        self.assertEqual(code, 0)
        self.assertEqual((report["schema"], report["failures"], report["errors"], report["testsRun"]),
                         ("elenchus.unittest.v1", 0, 0, 3))


if __name__ == "__main__":
    unittest.main()
