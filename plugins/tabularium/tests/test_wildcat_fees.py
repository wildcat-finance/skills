"""Fee semantics, closed version tuples and starting-runtime byte controls."""

from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

if __package__:
    from . import support
else:
    import support
from wildcat_fee_fixtures import FEES, BIPS, VENUES, MARKET, fee_records, fee_raw_release
from wildcat_v3_fixtures import ASSET, WRAPPER, log, record, constructed_inputs
from test_wildcat_v3_schema_parity import locked_oracle
from wildcat_v3_public_fixtures import inventory, build_pair, compare_pair
from wildcat_batch_public_fixtures import build_specimen, compare_specimen
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_release import build_wildcat_canonical, RELEASE_FILES
from tabularium_lib import release_v2, verifier
import tabularium

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent / "examples"


def mapped(venue, version="1.1.0", missing_asset=False):
    return map_records(venue, *fee_records(venue, missing_asset), adapter_version=version)


class FeeSemanticsTests(unittest.TestCase):
    def test_collections_have_native_assets_pool_and_recipient_gap(self):
        for venue in VENUES:
            result = mapped(venue)
            row = next(r for r in result["events"] if r["action"] == venue + ".fees-collected")
            self.assertEqual(row["event_family"], "fee-collection")
            self.assertEqual(row["parties"], [{"role": "pool", "address": MARKET}])
            self.assertEqual(row["amounts"], [{"kind": "assets", "base_units": "73", "asset": ASSET}])
            self.assertEqual(row["provenance"]["mapping_rule"], venue + ".fees-collected.v1")
            self.assertEqual(row["provenance"]["adapter_version"], "1.1.0")
            self.assertEqual(result["unsupported_counts"]["attribution:fees-collected:recipient"], 1)
            mapping = next(m for m in result["mapping_records"] if m["signature"] == FEES)
            self.assertEqual(mapping["decoded"], {"assets": "73"})
            self.assertIsNone(mapping["join"])
            self.assertEqual(mapping["native_record"], row["native_record"])

    def test_bips_retains_native_integer_string_and_has_no_amount(self):
        result = mapped("wildcat-v2")
        row = next(r for r in result["events"] if r["action"].endswith(".protocol-fee-bips-updated"))
        self.assertEqual(row["event_family"], "pool-state")
        self.assertEqual(row["amounts"], [])
        self.assertEqual(row["parties"], [{"role": "pool", "address": MARKET}])
        mapping = next(m for m in result["mapping_records"] if m["signature"] == BIPS)
        self.assertEqual(mapping["decoded"], {"protocolFeeBips": "125"})
        self.assertEqual(result["unsupported_counts"]["attribution:protocol-fee-bips-updated:actor"], 1)

    def test_missing_asset_stays_null_and_named(self):
        for venue in VENUES:
            result = mapped(venue, missing_asset=True)
            row = next(r for r in result["events"] if r["action"].endswith(".fees-collected"))
            self.assertIsNone(row["amounts"][0]["asset"])
            self.assertEqual(result["unsupported_counts"]["attribution:fees-collected:asset"], 1)

    def test_missing_asset_release_rebuilds_with_explicit_attribution_gap(self):
        for venue in VENUES:
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); raw = fee_raw_release(base, venue, missing_asset=True)
                target = base / "release"; build_wildcat_canonical(raw, target, "constructed-missing-asset")
                self.assertEqual(verifier.verify(target / "coverage.json").rows, 3 if venue == "wildcat-v1" else 4)
                coverage = json.loads((target / "coverage.json").read_bytes())
                self.assertEqual(coverage["coverage"]["unsupported_events"]["attribution:fees-collected:asset"], 1)

    def test_equal_amount_actions_remain_independent_and_input_order_does_not_join(self):
        for venue in VENUES:
            contexts, records = fee_records(venue)
            result = map_records(venue, contexts, records)
            self.assertEqual(result, map_records(venue, contexts, list(reversed(records))))
            self.assertEqual(result["included_counts"]["fees-collected"], 1)
            self.assertEqual(result["included_counts"]["debt-repaid"], 1)
            self.assertEqual(result["included_counts"]["withdrawal-executed"], 1)
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))

    def test_legacy_version_decodes_fees_without_promoting_them(self):
        for venue in VENUES:
            result = mapped(venue, "1.0.0")
            self.assertEqual(set(result["included_counts"]), {"debt-repaid", "withdrawal-executed"})
            self.assertTrue(all(m["disposition"] == "unsupported-canonical-meaning"
                                for m in result["mapping_records"] if m["signature"] in (FEES, BIPS)))
            self.assertTrue(all(r["provenance"]["adapter_version"] == "1.0.0" for r in result["events"]))

    def test_unknown_versions_refuse_before_any_output(self):
        for version in ("1.2.0", "2.0.0", "1.1", "", None, True, {}, []):
            for venue in VENUES:
                with self.subTest(version=version, venue=venue), self.assertRaises(TabulariumError):
                    mapped(venue, version)
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                with self.assertRaises(TabulariumError):
                    build_wildcat_canonical(base / "absent", base / "out", "unknown", version)
                self.assertFalse((base / "out").exists())

    def test_malformed_accepted_fee_logs_refuse(self):
        for venue, signature in (("wildcat-v1", FEES), ("wildcat-v2", FEES), ("wildcat-v2", BIPS)):
            contexts, _ = fee_records(venue)
            for kind in ("truncated", "extra-word", "indexed", "removed", "duplicate", "conflicting-position"):
                raw = log(signature, (), (73,), MARKET, 0)
                raws = [raw]
                if kind == "truncated": raw["data"] = "0x01"
                elif kind == "extra-word": raw["data"] += "00" * 32
                elif kind == "indexed": raw["topics"].append("0x" + "00" * 32)
                elif kind == "removed": raw["removed"] = True
                else:
                    other = deepcopy(raw)
                    if kind == "conflicting-position": other["transactionHash"] = "0x" + "ab" * 32
                    raws.append(other)
                with self.subTest(kind=kind, venue=venue, signature=signature), self.assertRaises(TabulariumError):
                    map_records(venue, contexts, [record(r) for r in raws])

    def test_native_uint256_limits_are_preserved(self):
        for venue, signature in (("wildcat-v1", FEES), ("wildcat-v2", FEES), ("wildcat-v2", BIPS)):
            contexts, _ = fee_records(venue)
            for value in (0, (1 << 256) - 1):
                result = map_records(venue, contexts, [record(log(signature, (), (value,), MARKET, 0))])
                self.assertEqual(len(result["events"]), 1)
                mapping = result["mapping_records"][0]
                self.assertEqual(list(mapping["decoded"].values()), [str(value)])

    def test_generation_and_emitter_roles_cannot_promote_fee_actions(self):
        contexts, _ = constructed_inputs("wildcat-v2")
        result = map_records("wildcat-v2", contexts, [record(log(FEES, (), (1,), WRAPPER, 0))])
        self.assertEqual(result["events"], ())
        self.assertEqual(result["dispositions"][0]["disposition"], "unsupported-decode")
        contexts, _ = fee_records("wildcat-v1")
        result = map_records("wildcat-v1", contexts, [record(log(BIPS, (), (1,), MARKET, 0))])
        self.assertEqual(result["events"], ())
        contexts[MARKET]["abi_variant"] = "not-a-variant"
        with self.assertRaises(TabulariumError):
            map_records("wildcat-v1", contexts, [])

    def test_future_parameter_and_sanctions_rules_remain_unsupported(self):
        for venue in VENUES:
            contexts, _ = fee_records(venue)
            signatures = ("AnnualInterestBipsUpdated(uint256)", "ReserveRatioBipsUpdated(uint256)")
            raws = [log(signature, (), (9,), MARKET, i) for i, signature in enumerate(signatures)]
            result = map_records(venue, contexts, [record(r) for r in raws])
            self.assertEqual(result["events"], ())
            self.assertTrue(all(m["disposition"].startswith("unsupported-") for m in result["mapping_records"]))

    def test_only_three_fee_capabilities_extend_the_starting_rule_set(self):
        from tabularium_lib.wildcat_rules import rules_for
        old, new = rules_for("1.0.0"), rules_for("1.1.0")
        self.assertEqual(len(old), 25)
        self.assertEqual({key: new[key] for key in old}, old)
        self.assertEqual(set(new) - set(old), {
            ("wildcat-v1", "market", FEES), ("wildcat-v2", "market", FEES), ("wildcat-v2", "market", BIPS)})
        for venue in VENUES:
            contexts, _ = fee_records(venue)
            raws = [log("SanctionedAccountAssetsSentToEscrow(address,address,uint256)",
                        (MARKET,), (WRAPPER, 9), MARKET, 0)]
            result = map_records(venue, contexts, [record(r) for r in raws])
            self.assertEqual(result["events"], ())
            self.assertEqual(result["mapping_records"][0]["disposition"], "unsupported-canonical-meaning")

    def test_cli_version_reaches_capture_provenance_and_coverage(self):
        for version in ("1.0.0", "1.1.0"):
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); raw = fee_raw_release(base, "wildcat-v2"); out = base / "release"
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(tabularium.main(["wildcat-canonical", "--alexandria-release", str(raw),
                        "--release", "constructed-cli", "--out", str(out), "--adapter-version", version]), 0)
                self.assertEqual(verifier.verify(out / "coverage.json").rows, 2 if version == "1.0.0" else 4)
                self.assertEqual(json.loads((out / "capture.json").read_bytes())["adapter"]["version"], version)
                self.assertEqual(json.loads((out / "coverage.json").read_bytes())["versions"]["adapter"]["version"], version)


class FeeSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        oracle = locked_oracle()
        cls.event = oracle.Draft202012Validator(support.event_schema(3))
        cls.coverage = oracle.Draft202012Validator(support.coverage_schema(3))
        oracle.Draft202012Validator.check_schema(support.event_schema(3))
        oracle.Draft202012Validator.check_schema(support.coverage_schema(3))

    def parity(self, value, accepted, coverage=False):
        validator = self.coverage if coverage else self.event
        self.assertEqual(validator.is_valid(value), accepted)
        try:
            if coverage: release_v2.validate_manifest(value, 3)
            else: release_v2.validate_event_row(value, release_v2.ADAPTERS[value["venue"]], 3)
        except TabulariumError:
            self.assertFalse(accepted)
        else:
            self.assertTrue(accepted)

    def test_fee_rows_and_every_old_row_validate_under_exact_versions(self):
        for venue in VENUES:
            for version in ("1.0.0", "1.1.0"):
                for row in mapped(venue, version)["events"]:
                    self.parity(row, True)
                for row in mapped(venue, version, True)["events"]:
                    self.parity(row, True)

    def test_fee_tuples_refuse_version_rule_generation_role_and_amount_confusion(self):
        for venue in VENUES:
            for original in mapped(venue)["events"]:
                if not original["action"].endswith((".fees-collected", ".protocol-fee-bips-updated")): continue
                for mutate in (
                    lambda r: r["provenance"].update(adapter_version="1.0.0"),
                    lambda r: r["provenance"].update(adapter_version="1.2.0"),
                    lambda r: r["provenance"].update(mapping_rule=venue + ".debt-repaid.v1"),
                    lambda r: r["provenance"].update(source_entity="Borrow(uint256)"),
                    lambda r: r.update(event_family="repayment"),
                    lambda r: r.update(event_family="exit-execute"),
                    lambda r: r.update(action="wildcat-v1.protocol-fee-bips-updated"),
                    lambda r: r["instrument"].update(type="wildcat-v2-wrapper"),
                    lambda r: r["parties"][0].update(role="recipient"),
                    lambda r: r["parties"].append({"role": "pool", "address": MARKET}),
                    lambda r: r["amounts"].append({"kind": "assets", "base_units": "1", "asset": ASSET}),
                    lambda r: r["provenance"].update(mapping_rule=venue + ".reserve-ratio-bips-updated.v1")):
                    row = deepcopy(original); mutate(row)
                    with self.subTest(action=original["action"], row=row): self.parity(row, False)
                if original["amounts"]:
                    for value in ("-1", "01", "1.0", str(1 << 256), True, 3, None):
                        row = deepcopy(original); row["amounts"][0]["base_units"] = value; self.parity(row, False)
                    row = deepcopy(original); row["amounts"] = []; self.parity(row, False)
                    row = deepcopy(original); row["amounts"][0]["kind"] = "reserved-assets"; self.parity(row, False)

    def test_manifest_rules_are_version_qualified(self):
        for venue in VENUES:
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); raw = fee_raw_release(base, venue)
                for version in ("1.0.0", "1.1.0"):
                    target = base / version; build_wildcat_canonical(raw, target, "constructed-parity", version)
                    original = json.loads((target / "coverage.json").read_bytes()); self.parity(original, True, True)
                    for version_bad, rule in (("1.0.0", venue + ".fees-collected.v1"), ("1.2.0", venue + ".borrow.v1"),
                                              ("1.1.0", venue + ".reserve-ratio-bips-updated.v1"),
                                              ("1.1.0", "wildcat-v1.protocol-fee-bips-updated.v1")):
                        value = deepcopy(original); value["versions"]["adapter"]["version"] = version_bad
                        value["versions"]["mapping_rules"] = [rule]; self.parity(value, False, True)


class FeeLegacyTests(unittest.TestCase):
    def test_starting_runtime_fee_controls_reconstruct_every_byte(self):
        frozen = json.loads((HERE / "fixtures/wildcat-fee-legacy.json").read_bytes())
        self.assertEqual(frozen["starting_commit"], "8b4e137917d754a7b7c3d5e74d141c0bedf70aa2")
        self.assertEqual(len(frozen["runtime_sha256"]), 24)
        for venue in VENUES:
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); raw = fee_raw_release(base, venue); target = base / "legacy"
                build_wildcat_canonical(raw, target, venue + "-constructed-fee-legacy-control", "1.0.0")
                self.assertEqual(inventory(target), frozen["releases"][venue])
                newer = base / "new"; build_wildcat_canonical(raw, newer, venue + "-constructed-fee-legacy-control", "1.1.0")
                self.assertNotEqual(inventory(newer), frozen["releases"][venue])

    def test_all_old_committed_wildcat_roots_verify_and_rebuild_identically(self):
        for venue in VENUES:
            published = EXAMPLES / (venue + "-v0")
            for suffix in ("release", "registry-context/release"):
                self.assertEqual(json.loads((published / suffix / "coverage.json").read_bytes())["versions"]["adapter"]["version"], "1.0.0")
                verifier.verify(published / suffix / "coverage.json")
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); build_pair(base, venue); compare_pair(published, base)
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); build_specimen(base, venue)
                compare_specimen(EXAMPLES / (venue + "-batches-v0"), base)

    def test_every_committed_non_wildcat_release_still_verifies(self):
        for name in ("aave-v4-v0", "aave-v4-v1", "euler-v1-v0", "euler-v1-v1", "euler-v2-v0", "euler-v2-v1"):
            verifier.verify(EXAMPLES / name / "coverage.json")

    def test_rebinding_generated_digests_cannot_bless_changed_bytes(self):
        for changed in ("source.json", "capture.json", "events.jsonl", "coverage.json"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); raw = fee_raw_release(base, "wildcat-v2"); target = base / "release"
                build_wildcat_canonical(raw, target, "constructed-tamper")
                path = target / changed
                if changed == "events.jsonl":
                    rows = [json.loads(line) for line in path.read_text().splitlines()]
                    rows[0]["amounts"][0]["base_units"] = "74"
                    path.write_bytes(b"".join(canonical_json(r) + b"\n" for r in rows))
                else:
                    value = json.loads(path.read_bytes())
                    if changed == "source.json": value["mapping_records"][0]["decoded"]["assets"] = "74"
                    elif changed == "capture.json": value["adapter"]["version"] = "1.0.0"
                    else: value["release"] = "altered-name"
                    path.write_bytes(canonical_json(value) + b"\n")
                coverage = json.loads((target / "coverage.json").read_bytes())
                key = {"source.json": "source", "capture.json": "capture_manifest", "events.jsonl": "canonical"}.get(changed)
                if key:
                    data = path.read_bytes(); coverage[key].update(sha256=sha256_bytes(data), bytes=len(data))
                    (target / "coverage.json").write_bytes(canonical_json(coverage) + b"\n")
                with self.assertRaises(TabulariumError): verifier.verify(target / "coverage.json")


class FeePublicTests(unittest.TestCase):
    def test_both_constructed_specimens_rebuild_all_bytes_and_verify_after_move(self):
        from wildcat_fee_public_fixtures import rebuild_fee_example
        for venue in VENUES:
            self.assertEqual(rebuild_fee_example(venue), 0)

    def test_public_specimens_are_explicit_constructed_fee_evidence(self):
        for venue in VENUES:
            root = EXAMPLES / (venue + "-fees-v0") / "release"
            source = json.loads((root / "source.json").read_bytes())
            self.assertEqual(source["scope"]["kind"], "constructed-fixture")
            rows = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
            self.assertEqual(sum(r["action"] == venue + ".fees-collected" for r in rows), 1)
            self.assertEqual(sum(r["action"] == venue + ".protocol-fee-bips-updated" for r in rows), int(venue == "wildcat-v2"))
            self.assertTrue(all(r["provenance"]["adapter_version"] == "1.1.0" for r in rows))
