"""Versioned Aave v4 and Clearpool Tabularium derivation tests."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from unittest import mock
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
FIXTURE_DECLARATION = PLUGIN_ROOT / "tests" / "fixtures" / "credit-view-sources.json"
COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib import derivation  # noqa: E402
from alexandria_lib.derivation import component_reader, derive  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.mappings import aave_v4 as aave_v4_mapping  # noqa: E402
from alexandria_lib.release import ingest, sha256, verify  # noqa: E402
from alexandria_lib.rows import validate_event, validate_observation  # noqa: E402


class DerivationTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir()
        declaration = json.loads(FIXTURE_DECLARATION.read_text(encoding="utf-8"))
        self.plan = {
            "format": "alexandria-capture-plan/v1",
            "release": declaration["release"],
            "components": [],
            "captures": declaration["captures"],
        }
        for component in declaration["components"]:
            component = deepcopy(component)
            source = REPO_ROOT / component.pop("repository_path")
            shutil.copy2(source, self.inputs / component["path"])
            self.plan["components"].append(component)
        self.plan_path = self.inputs / "capture-plan.json"
        self._write_plan()
        self.raw_release = self.root / "raw-release"
        self.derived_release = self.root / "derived-release"

    def tearDown(self):
        self.temporary.cleanup()

    def _write_plan(self):
        self.plan_path.write_bytes(canonical_bytes(self.plan))

    def source_path(self, name):
        component = next(item for item in self.plan["components"] if item["name"] == name)
        return self.inputs / component["path"]

    def source_json(self, name):
        return json.loads(self.source_path(name).read_text(encoding="utf-8"))

    def write_source(self, name, value):
        self.source_path(name).write_bytes(canonical_bytes(value))

    def build_raw(self):
        return ingest(self.plan_path, self.raw_release)

    def build_derived(self):
        self.raw_id = self.build_raw()
        self.derived_id = derive(self.raw_release, self.derived_release)
        return self.derived_id

    def manifest(self, derived=True):
        release = self.derived_release if derived else self.raw_release
        return json.loads((release / "manifest.json").read_text(encoding="utf-8"))

    def write_manifest(self, value):
        unsigned = deepcopy(value)
        unsigned.pop("release_id", None)
        value["release_id"] = sha256(canonical_bytes(unsigned))
        (self.derived_release / "manifest.json").write_bytes(canonical_bytes(value))

    def rows(self, observations=False):
        name = "credit-observations.jsonl" if observations else "credit-events.jsonl"
        data = (self.derived_release / name).read_text(encoding="utf-8")
        return [json.loads(line) for line in data.splitlines()]


    def synthetic_observation(self):
        """A position-observation row built by hand.

        No shipped mapping emits one: the Aave v4 log mapping states events
        only. The observation schema is still enforced, so these guards build
        their subject rather than deriving it.
        """
        from alexandria_lib.rows import observation_row, provenance

        return observation_row(
            identity="eip155:1:synthetic-observation",
            chain="eip155:1",
            venue="aave-v4",
            subject="eip155:1:0x" + "ab" * 20,
            deployment="aave-v4-mainnet",
            facility={"kind": "aave-v4-spoke", "id": "0x" + "bb" * 20},
            observation={
                "property": "aave-v4.credit-line-balance",
                "value": "1",
                "unit": "base-units",
                "at": {"block_number": "25870892", "timestamp": "1788106427"},
                "method": "recorded-read",
                "evidence_class": "archive-log",
            },
            provenance=provenance(
                source_release_id="sha256:" + "0" * 64,
                component="aave-v4-source",
                component_sha256="sha256:" + "0" * 64,
                capture_id="aave-v4-window",
                source_selector="/logs/0",
                source_identity="synthetic",
                mapping_rule="aave-v4.borrow.v1",
                adapter="aave-v4",
                adapter_version="1.0.0",
                evidence_class="archive-log",
            ),
        )

class DeriveIntegrationTests(DerivationTestCase):
    def test_derive_prints_and_verifies_new_release_id(self):
        expected = self.build_derived()
        self.assertEqual(verify(self.derived_release), expected)
        self.assertNotEqual(expected, self.raw_id)

    def test_cli_derives_verified_release(self):
        self.build_raw()
        result = subprocess.run(
            [sys.executable, str(COMMAND), "derive", str(self.raw_release), "--output", str(self.derived_release)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^sha256:[0-9a-f]{64}\n$")

    def test_aave_v4_and_clearpool_event_counts(self):
        self.build_derived()
        events = self.rows()
        by_venue = {venue: sum(row["venue"] == venue for row in events) for venue in ("aave-v4", "clearpool")}
        self.assertEqual(by_venue, {"aave-v4": 500, "clearpool": 11})

    def test_event_family_counts_reconcile(self):
        self.build_derived()
        counts = self.manifest()["derivation"]["counts"]
        self.assertEqual(counts["event_families"], {"borrowing": 287, "repayment": 224})
        self.assertEqual(counts["event_rows"], 511)

    def test_aave_v4_logs_state_events_and_no_position(self):
        self.build_derived()
        self.assertEqual(self.rows(observations=True), [])
        for row in self.rows():
            if row["venue"] != "aave-v4":
                continue
            asset = row["amounts"][0]["asset"]
            self.assertRegex(asset["address"], r"^0x[0-9a-f]{40}$")
            self.assertTrue(asset["symbol"])
            self.assertIsInstance(asset["decimals"], int)

    def test_clearpool_emits_no_position_observation(self):
        self.build_derived()
        self.assertFalse(any(row["venue"] == "clearpool" for row in self.rows(observations=True)))

    def test_events_retain_source_evidence_classes(self):
        self.build_derived()
        evidence = {(row["venue"], row["provenance"]["evidence_class"]) for row in self.rows()}
        self.assertEqual(evidence, {("aave-v4", "archive-log"), ("clearpool", "archive-log")})

    def test_amounts_stay_exact_decimal_strings(self):
        self.build_derived()
        events = self.rows()
        self.assertTrue(all(isinstance(row["amounts"][0]["base_units"], str) for row in events))
        clearpool = next(row for row in events if row["venue"] == "clearpool")
        self.assertEqual(clearpool["amounts"][0]["asset"]["address"], "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
        self.assertEqual(clearpool["amounts"][0]["asset"]["decimals"], 6)
        self.assertTrue(
            all(row["amounts"][0]["role"] == "source-amount" for row in events)
        )

    def test_repayment_amount_does_not_claim_a_principal_split(self):
        self.build_derived()
        repayments = [row for row in self.rows() if row["event_family"] == "repayment"]
        self.assertTrue(repayments)
        self.assertTrue(all(len(row["amounts"]) == 1 for row in repayments))
        self.assertTrue(
            all(row["amounts"][0]["role"] == "source-amount" for row in repayments)
        )

    def test_credit_event_schema_admits_multiple_amount_legs(self):
        self.build_derived()
        row = deepcopy(self.rows()[0])
        row["amounts"].append({
            "role": "collateral", "base_units": "7",
            "asset": {"chain": "eip155:1", "address": "0x" + "2" * 40, "decimals": 18},
        })
        self.assertIs(validate_event(row), row)

    def test_repeat_derivation_is_byte_identical(self):
        first_id = self.build_derived()
        second = self.root / "derived-second"
        second_id = derive(self.raw_release, second)
        self.assertEqual(first_id, second_id)
        for name in ("manifest.json", "credit-events.jsonl", "credit-observations.jsonl"):
            self.assertEqual((self.derived_release / name).read_bytes(), (second / name).read_bytes())

    def test_derive_does_not_change_raw_release(self):
        self.build_raw()
        before = {path.relative_to(self.raw_release): path.read_bytes() for path in self.raw_release.rglob("*") if path.is_file()}
        derive(self.raw_release, self.derived_release)
        after = {path.relative_to(self.raw_release): path.read_bytes() for path in self.raw_release.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_row_provenance_binds_raw_release_and_component(self):
        self.build_derived()
        for row in self.rows() + self.rows(observations=True):
            self.assertEqual(row["provenance"]["source_release_id"], self.raw_id)
            self.assertRegex(row["provenance"]["component_sha256"], r"^sha256:[0-9a-f]{64}$")

    def test_every_primary_selector_resolves(self):
        self.build_derived()
        sources = {name: self.source_json(name) for name in ("aave-v4-source", "clearpool-source")}
        for row in self.rows() + self.rows(observations=True):
            current = sources[row["provenance"]["component"]]
            for token in row["provenance"]["source_selector"].split("/")[1:]:
                token = token.replace("~1", "/").replace("~0", "~")
                current = current[int(token)] if isinstance(current, list) else current[token]
            self.assertIsInstance(current, dict)

    def test_context_selectors_cover_joined_source_values(self):
        self.build_derived()
        clearpool = next(row for row in self.rows() if row["venue"] == "clearpool")
        self.assertEqual(len(clearpool["provenance"]["context_selectors"]), 3)
        aave = next(row for row in self.rows() if row["venue"] == "aave-v4")
        self.assertEqual(
            aave["provenance"]["context_selectors"], ["/reserve_reads", "/token_reads"]
        )

    def test_manifest_binds_both_output_digests(self):
        self.build_derived()
        outputs = self.manifest()["derivation"]["outputs"]
        for key in ("credit_events", "credit_observations"):
            descriptor = outputs[key]
            data = (self.derived_release / descriptor["path"]).read_bytes()
            self.assertEqual(descriptor["sha256"], sha256(data))
            self.assertEqual(descriptor["bytes"], len(data))

    def test_manifest_names_registered_mapping_revisions(self):
        self.build_derived()
        mappings = {item["adapter"]: item for item in self.manifest()["derivation"]["mappings"]}
        self.assertEqual(mappings["aave-v4"]["mapping_revision"], "aave-v4.credit.v1")
        self.assertEqual(mappings["clearpool"]["mapping_revision"], "clearpool.credit.v1")

    def test_mapping_revision_change_changes_release_identity(self):
        first = self.build_derived()
        first_events = (self.derived_release / "credit-events.jsonl").read_bytes()
        second = self.root / "derived-new-revision"
        with mock.patch.object(aave_v4_mapping, "MAPPING_REVISION", "aave-v4.credit.v2"):
            second_id = derive(self.raw_release, second)
        self.assertNotEqual(first, second_id)
        self.assertEqual(first_events, (second / "credit-events.jsonl").read_bytes())

    def test_source_window_must_match_its_capture_interval(self):
        source = self.source_json("aave-v4-source")
        source["_meta"]["window"]["last_block"] += 1
        self.write_source("aave-v4-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "window does not match"):
            derive(self.raw_release, self.derived_release)

    def test_row_identity_does_not_depend_on_capture_name(self):
        self.build_derived()
        first_events = [row["id"] for row in self.rows()]
        first_observations = [row["id"] for row in self.rows(observations=True)]
        self.plan["captures"][0]["id"] = "renamed-aave-v4-capture"
        self.plan["captures"][1]["id"] = "renamed-clearpool-capture"
        self._write_plan()
        self.raw_release = self.root / "renamed-raw"
        self.derived_release = self.root / "renamed-derived"
        self.build_derived()
        self.assertEqual(first_events, [row["id"] for row in self.rows()])
        self.assertEqual(first_observations, [row["id"] for row in self.rows(observations=True)])

    def test_clearpool_identity_ignores_provider_metadata(self):
        self.build_derived()
        first = {
            row["id"]
            for row in self.rows()
            if row["venue"] == "clearpool"
        }
        source = self.source_json("clearpool-source")
        pool = next(iter(source["pool_logs"]))
        source["pool_logs"][pool][0]["provider_metadata"] = "ignored-by-mapping"
        self.write_source("clearpool-source", source)
        self.raw_release = self.root / "metadata-raw"
        self.derived_release = self.root / "metadata-derived"
        self.build_derived()
        second = {
            row["id"]
            for row in self.rows()
            if row["venue"] == "clearpool"
        }
        self.assertEqual(first, second)

    def test_mapping_coverage_exposes_unsupported_aave_v4_collections(self):
        self.build_derived()
        aave_v4 = next(item for item in self.manifest()["derivation"]["mappings"] if item["adapter"] == "aave-v4")
        self.assertEqual(aave_v4["coverage"]["unsupported_collections"], {})
        self.assertEqual(aave_v4["coverage"]["mapped_records"], 500)
        self.assertEqual(
            aave_v4["coverage"]["context_collections"],
            {"reserve-reads": 35, "token-reads": 10},
        )
        self.assertEqual(aave_v4["coverage"]["source_records"], 545)

    def test_clearpool_coverage_keeps_factory_as_context(self):
        self.build_derived()
        clearpool = next(item for item in self.manifest()["derivation"]["mappings"] if item["adapter"] == "clearpool")
        self.assertEqual(clearpool["coverage"]["context_collections"], {"factory-pools": 1})
        self.assertEqual(clearpool["coverage"]["mapped_records"], 11)

    def test_subject_counts_reconcile_to_rows(self):
        self.build_derived()
        counts = self.manifest()["derivation"]["counts"]
        self.assertEqual(sum(item["events"] for item in counts["subjects"].values()), 511)
        self.assertEqual(sum(item["observations"] for item in counts["subjects"].values()), 0)

    def test_output_classification_inherits_strictest_input(self):
        self.plan["components"][0].update(access="private", redistribution="prohibited")
        self._write_plan()
        self.build_derived()
        for output in self.manifest()["derivation"]["outputs"].values():
            self.assertEqual((output["access"], output["redistribution"]), ("private", "prohibited"))

    def test_unknown_redistribution_is_not_relaxed_to_restricted(self):
        self.plan["components"][0]["redistribution"] = "restricted"
        self.plan["components"][1]["redistribution"] = "unknown"
        self._write_plan()
        self.build_derived()
        for output in self.manifest()["derivation"]["outputs"].values():
            self.assertEqual(output["redistribution"], "unknown")

    def test_existing_derived_release_is_idempotent(self):
        expected = self.build_derived()
        before = (self.derived_release / "manifest.json").stat().st_mtime_ns
        self.assertEqual(derive(self.raw_release, self.derived_release), expected)
        self.assertEqual((self.derived_release / "manifest.json").stat().st_mtime_ns, before)

    def test_derive_refuses_already_derived_input(self):
        self.build_derived()
        with self.assertRaisesRegex(AlexandriaError, "raw release"):
            derive(self.derived_release, self.root / "third")


class MappingRefusalTests(DerivationTestCase):
    def test_duplicate_capture_cannot_duplicate_economic_rows(self):
        duplicate = deepcopy(self.plan["captures"][0])
        duplicate["id"] = "second-name-for-same-aave-v4-capture"
        self.plan["captures"].append(duplicate)
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "duplicate derived row identity"):
            derive(self.raw_release, self.derived_release)

    def test_duplicate_aave_v4_record_identity_is_rejected(self):
        source = self.source_json("aave-v4-source")
        source["logs"].append(deepcopy(source["logs"][0]))
        self.write_source("aave-v4-source", source)
        coverage = self.plan["captures"][0]["coverage"]
        coverage["collections"][0]["record_count"] += 1
        coverage["record_count"] += 1
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "repeats the source identity"):
            derive(self.raw_release, self.derived_release)

    def test_duplicate_clearpool_log_identity_is_rejected(self):
        source = self.source_json("clearpool-source")
        pool = next(iter(source["pool_logs"]))
        source["pool_logs"][pool].append(deepcopy(source["pool_logs"][pool][0]))
        self.write_source("clearpool-source", source)
        coverage = self.plan["captures"][1]["coverage"]
        coverage["collections"][1]["record_count"] += 1
        coverage["record_count"] += 1
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "duplicate Clearpool"):
            derive(self.raw_release, self.derived_release)

    def test_duplicate_clearpool_log_with_extra_metadata_is_rejected(self):
        source = self.source_json("clearpool-source")
        pool = next(iter(source["pool_logs"]))
        duplicate = deepcopy(source["pool_logs"][pool][0])
        duplicate["provider_metadata"] = "does-not-create-a-new-log"
        source["pool_logs"][pool].append(duplicate)
        self.write_source("clearpool-source", source)
        coverage = self.plan["captures"][1]["coverage"]
        coverage["collections"][1]["record_count"] += 1
        coverage["record_count"] += 1
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "duplicate Clearpool"):
            derive(self.raw_release, self.derived_release)

    def test_corrupted_aave_v4_native_shape_is_rejected(self):
        source = self.source_json("aave-v4-source")
        del source["logs"][0]["topics"]
        self.write_source("aave-v4-source", source)
        self.build_raw()
        with self.assertRaises(AlexandriaError):
            derive(self.raw_release, self.derived_release)

    def test_unknown_clearpool_action_is_rejected(self):
        source = self.source_json("clearpool-source")
        pool = next(iter(source["pool_logs"]))
        source["pool_logs"][pool][0]["topics"][0] = "0x" + "f" * 64
        self.write_source("clearpool-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "unknown Clearpool action"):
            derive(self.raw_release, self.derived_release)

    def test_clearpool_log_outside_capture_range_is_rejected(self):
        source = self.source_json("clearpool-source")
        pool = next(iter(source["pool_logs"]))
        source["pool_logs"][pool][0]["blockNumber"] = "0x1"
        self.write_source("clearpool-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "outside the capture range"):
            derive(self.raw_release, self.derived_release)

    def test_clearpool_requires_a_block_range_capture(self):
        self.plan["captures"][1]["scope"]["interval"] = {
            "kind": "snapshot",
            "observed_at": "2026-08-16T12:00:00Z",
        }
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "block range"):
            derive(self.raw_release, self.derived_release)

    def test_aave_v4_log_outside_the_capture_interval_is_rejected(self):
        source = self.source_json("aave-v4-source")
        source["logs"][0]["blockNumber"] = "0x1"
        self.write_source("aave-v4-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "outside the capture interval"):
            derive(self.raw_release, self.derived_release)

    def test_aave_v4_reserve_read_contradicting_its_bytes_is_rejected(self):
        source = self.source_json("aave-v4-source")
        source["reserve_reads"][0]["underlying"] = "0x" + "ab" * 20
        self.write_source("aave-v4-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "underlying disagrees"):
            derive(self.raw_release, self.derived_release)

    def test_malformed_aave_v4_log_index_is_rejected_before_row_identity(self):
        source = self.source_json("aave-v4-source")
        source["logs"][0]["logIndex"] = "not-a-quantity"
        self.write_source("aave-v4-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "not a hex quantity"):
            derive(self.raw_release, self.derived_release)

    def test_overlong_clearpool_hex_quantity_is_rejected(self):
        source = self.source_json("clearpool-source")
        pool = next(iter(source["pool_logs"]))
        source["pool_logs"][pool][0]["blockNumber"] = "0x" + "1" * 65
        self.write_source("clearpool-source", source)
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "canonical hex quantity"):
            derive(self.raw_release, self.derived_release)

    def test_subject_scoped_mapping_refuses_out_of_scope_manager(self):
        self.plan["captures"][1]["scope"]["subjects"] = ["eip155:1:0x" + "1" * 40]
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "out-of-scope"):
            derive(self.raw_release, self.derived_release)

    def test_missing_source_collection_is_rejected(self):
        source = self.source_json("aave-v4-source")
        del source["token_reads"]
        self.write_source("aave-v4-source", source)
        coverage = self.plan["captures"][0]["coverage"]
        removed = next(item for item in coverage["collections"]
                       if item["selector"] == "/token_reads")
        coverage["collections"].remove(removed)
        coverage["record_count"] -= removed["record_count"]
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "source collections"):
            derive(self.raw_release, self.derived_release)

    def test_uncovered_source_collection_is_rejected(self):
        coverage = self.plan["captures"][0]["coverage"]
        removed = coverage["collections"].pop()
        coverage["record_count"] -= removed["record_count"]
        coverage["status"] = "partial"
        coverage["unsupported_collections"] = ["tranched-pools"]
        self._write_plan()
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "coverage does not match"):
            derive(self.raw_release, self.derived_release)

    def test_event_schema_refuses_universal_default_conclusion(self):
        self.build_derived()
        row = self.rows()[0]
        row["defaulted"] = True
        with self.assertRaises(AlexandriaError):
            validate_event(row)

    def test_observation_schema_refuses_current_balance_conclusion(self):
        self.build_derived()
        row = self.synthetic_observation()
        row["current_balance"] = row["observation"]["value"]
        with self.assertRaises(AlexandriaError):
            validate_observation(row)

    def test_observation_does_not_claim_default_or_full_repayment(self):
        self.build_derived()
        forbidden = {"defaulted", "fully_repaid", "current_balance"}
        for row in self.rows(observations=True):
            self.assertTrue(forbidden.isdisjoint(row))
            self.assertTrue(forbidden.isdisjoint(row["observation"]))

    def test_observation_property_must_match_venue(self):
        self.build_derived()
        row = self.synthetic_observation()
        row["observation"]["property"] = "clearpool.credit-line-balance"
        with self.assertRaisesRegex(AlexandriaError, "match its venue"):
            validate_observation(row)

    def test_malformed_row_enums_are_controlled(self):
        self.build_derived()
        event = self.rows()[0]
        event["event_family"] = []
        with self.assertRaises(AlexandriaError):
            validate_event(event)
        event = self.rows()[0]
        event["provenance"]["evidence_class"] = {}
        with self.assertRaises(AlexandriaError):
            validate_event(event)
        observation = self.synthetic_observation()
        observation["observation"]["evidence_class"] = []
        with self.assertRaises(AlexandriaError):
            validate_observation(observation)


class DerivedVerificationTests(DerivationTestCase):
    def test_output_byte_tamper_is_rejected(self):
        self.build_derived()
        path = self.derived_release / "credit-events.jsonl"
        path.write_bytes(path.read_bytes() + b"{}\n")
        with self.assertRaises(AlexandriaError):
            verify(self.derived_release)

    def test_mapping_revision_tamper_is_rejected(self):
        self.build_derived()
        manifest = self.manifest()
        manifest["derivation"]["mappings"][0]["mapping_revision"] = "clearpool.credit.v2"
        self.write_manifest(manifest)
        with self.assertRaisesRegex(AlexandriaError, "registered mappings"):
            verify(self.derived_release)

    def test_source_release_identity_tamper_is_rejected(self):
        self.build_derived()
        manifest = self.manifest()
        manifest["derivation"]["source_release_id"] = "sha256:" + "0" * 64
        self.write_manifest(manifest)
        with self.assertRaisesRegex(AlexandriaError, "source release identity"):
            verify(self.derived_release)

    def test_missing_derived_output_is_rejected(self):
        self.build_derived()
        (self.derived_release / "credit-observations.jsonl").unlink()
        with self.assertRaises(AlexandriaError):
            verify(self.derived_release)

    def test_extra_derived_file_is_rejected(self):
        self.build_derived()
        (self.derived_release / "unbound.jsonl").write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "undeclared"):
            verify(self.derived_release)

    def test_output_path_traversal_is_rejected(self):
        self.build_derived()
        manifest = self.manifest()
        manifest["derivation"]["outputs"]["credit_events"]["path"] = "../events.jsonl"
        self.write_manifest(manifest)
        with self.assertRaises(AlexandriaError):
            verify(self.derived_release)

    def test_malformed_output_classification_is_controlled(self):
        self.build_derived()
        manifest = self.manifest()
        manifest["derivation"]["outputs"]["credit_events"]["access"] = []
        self.write_manifest(manifest)
        result = subprocess.run(
            [sys.executable, str(COMMAND), "verify", str(self.derived_release)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("classification", result.stderr)

    def test_component_loader_does_not_cache_raw_bytes(self):
        self.build_raw()
        manifest = self.manifest(derived=False)
        original = derivation.read_confined_file
        with mock.patch.object(derivation, "read_confined_file", wraps=original) as read:
            load = component_reader(self.raw_release, manifest)
            name = manifest["components"][0]["name"]
            self.assertEqual(load(name), load(name))
        self.assertEqual(read.call_count, 2)

    def test_derived_row_limit_fails_before_writing_output(self):
        self.build_raw()
        with mock.patch.object(derivation, "MAX_DERIVED_ROWS", 1):
            with self.assertRaisesRegex(AlexandriaError, "row limit"):
                derive(self.raw_release, self.derived_release)
        self.assertFalse(self.derived_release.exists())

    def test_derived_byte_limit_fails_before_writing_output(self):
        self.build_raw()
        with mock.patch.object(derivation, "MAX_DERIVED_BYTES", 1):
            with self.assertRaisesRegex(AlexandriaError, "byte limit"):
                derive(self.raw_release, self.derived_release)
        self.assertFalse(self.derived_release.exists())

    def test_verify_does_not_use_network(self):
        expected = self.build_derived()
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            self.assertEqual(verify(self.derived_release), expected)

    def test_verify_accepts_read_only_derived_tree(self):
        expected = self.build_derived()
        paths = sorted(self.derived_release.rglob("*"), reverse=True) + [self.derived_release]
        modes = {path: stat.S_IMODE(path.stat().st_mode) for path in paths}
        try:
            for path in paths:
                path.chmod(0o555 if path.is_dir() else 0o444)
            self.assertEqual(verify(self.derived_release), expected)
        finally:
            for path in reversed(paths):
                path.chmod(modes[path])

    def test_no_index_or_database_is_created(self):
        self.build_derived()
        names = {path.name for path in self.derived_release.rglob("*") if path.is_file()}
        self.assertFalse(any(name.endswith((".sqlite", ".db")) for name in names))


if __name__ == "__main__":
    unittest.main()
