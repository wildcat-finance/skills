"""Verify closed versioned schemas, old byte replay and hostile release edits."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_wildcat_v3_schema_parity import locked_oracle
import support
from wildcat_parameter_fixtures import EXAMPLES, build_specimen, inputs, raw_release, rebuild_example
from wildcat_v3_public_fixtures import rebuild_example as rebuild_native
from wildcat_batch_public_fixtures import rebuild_example as rebuild_batches
from tabularium_lib import builder, release_v2, verifier
from tabularium_lib.core import TabulariumError, canonical_json, jsonl_bytes, sha256_bytes
from tabularium_lib.wildcat_release import build_wildcat_canonical
from tabularium_lib.wildcat_rows import map_records

VENUES = ("wildcat-v1", "wildcat-v2")


class ParameterSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        oracle = locked_oracle()
        schemas = EXAMPLES.parent / "schemas"
        cls.event = oracle.Draft202012Validator(json.loads((schemas / "canonical-event-v3.json").read_bytes()))
        cls.coverage = oracle.Draft202012Validator(json.loads((schemas / "coverage-manifest-v3.json").read_bytes()))
        oracle.Draft202012Validator.check_schema(cls.event.schema)
        oracle.Draft202012Validator.check_schema(cls.coverage.schema)

    def assert_parity(self, row, accepted):
        self.assertEqual(self.event.is_valid(row), accepted)
        try:
            release_v2.validate_event_row(row, release_v2.ADAPTERS[row["venue"]], 3)
        except TabulariumError:
            python_valid = False
        else:
            python_valid = True
        self.assertEqual(python_valid, accepted)

    def test_all_native_rows_and_closed_party_amount_instrument_tuples(self):
        for venue in VENUES:
            for original in map_records(venue, *inputs(venue)[:2])["events"]:
                self.assert_parity(original, True)
                for field, value in (("parties", []), ("parties", original["parties"] + original["parties"][:1]),
                                     ("amounts", [{"kind": "assets", "base_units": "7", "asset": None}]),
                                     ("event_family", "repayment"), ("operator_note", "extra")):
                    row = deepcopy(original); row[field] = value
                    self.assert_parity(row, False)
                for field, value in (("adapter_version", "1.0.0"), ("adapter_version", "1.1.0"),
                                     ("adapter_version", "1.3.0"), ("adapter_version", "unknown"),
                                     ("mapping_rule", venue + ".borrow.v1"),
                                     ("source_entity", "Borrow(uint256)"), ("operator_note", "extra")):
                    row = deepcopy(original); row["provenance"][field] = value
                    self.assert_parity(row, False)
                for position in range(len(original["parties"])):
                    for change in ("role", "unknown"):
                        row = deepcopy(original)
                        row["parties"][position]["role" if change == "role" else "unknown"] = "borrower"
                        self.assert_parity(row, False)
                if len(original["parties"]) > 1:
                    row = deepcopy(original); row["parties"].reverse()
                    self.assert_parity(row, False)
                row = deepcopy(original); row["instrument"]["type"] = venue + "-wrapper"
                self.assert_parity(row, False)

    def test_coverage_version_rule_pairs_and_unknown_fields_have_parity(self):
        for venue in VENUES:
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); build_specimen(base, venue)
                original = json.loads((base / "release/coverage.json").read_bytes())
                self.assertTrue(self.coverage.is_valid(original))
                release_v2.validate_manifest(original, 3)
                for version in ("1.0.0", "1.1.0", "1.3.0", "2.0.0", None):
                    manifest = deepcopy(original); manifest["versions"]["adapter"]["version"] = version
                    self.assertFalse(self.coverage.is_valid(manifest))
                    with self.assertRaises(TabulariumError): release_v2.validate_manifest(manifest, 3)
                for change in ("unknown-rule", "unknown-key", "extra-version-key"):
                    manifest = deepcopy(original)
                    if change == "unknown-rule": manifest["versions"]["mapping_rules"] = [venue + ".fees-collected.v1"]
                    if change == "unknown-key": manifest["operator_note"] = "extra"
                    if change == "extra-version-key": manifest["versions"]["adapter"]["role"] = "market"
                    self.assertFalse(self.coverage.is_valid(manifest))
                    with self.assertRaises(TabulariumError): release_v2.validate_manifest(manifest, 3)


class ParameterCompatibilityTests(unittest.TestCase):
    def test_both_new_specimens_build_verify_and_replay_all_release_bytes(self):
        for venue in VENUES:
            self.assertEqual(rebuild_example(venue), 0)
            verified = verifier.verify(EXAMPLES / (venue + "-parameters-v0/release/coverage.json"))
            self.assertGreater(verified.rows, 0)

    def test_all_six_aave_euler_historical_releases_rebuild_and_verify(self):
        for name in support.SHIPPED_RELEASES:
            with self.subTest(release=name), tempfile.TemporaryDirectory() as temporary:
                published = EXAMPLES / name
                base = Path(temporary).resolve()
                for filename in ("source.json", "capture.json"):
                    (base / filename).write_bytes((published / filename).read_bytes())
                manifest = json.loads((published / "coverage.json").read_bytes())
                builder.build(base / "source.json", base / "capture.json", base / "events.jsonl",
                              base / "coverage.json", manifest["release"],
                              adapter=manifest["versions"]["adapter"]["name"], event_schema=manifest["schema_version"])
                verifier.verify(base / "coverage.json")
                for filename in support.RELEASE_DATA_FILES:
                    self.assertEqual((base / filename).read_bytes(), (published / filename).read_bytes())

    def test_all_old_wildcat_specimens_replay_under_qualified_starting_tree_100(self):
        for venue in VENUES:
            self.assertEqual(rebuild_native(venue), 0)
            self.assertEqual(rebuild_batches(venue), 0)

    def test_legacy_and_native_versions_rebuild_from_identical_raw_without_confusion(self):
        for venue in VENUES:
            with tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); raw = raw_release(base, venue)
                for version, count in (("1.0.0", 0), ("1.2.0", len(inputs(venue)[1]))):
                    out = base / version
                    self.assertEqual(build_wildcat_canonical(raw, out, "constructed-version", version).rows, count)
                    self.assertEqual(verifier.verify(out / "coverage.json").rows, count)
                    manifest = json.loads((out / "coverage.json").read_bytes())
                    self.assertEqual(manifest["versions"]["adapter"]["version"], version)
                for version in ("1.1.0", "1.3.0", "99", None, True):
                    out = base / "unknown"
                    with self.assertRaises(TabulariumError): build_wildcat_canonical(raw, out, "constructed-version", version)
                    self.assertFalse(out.exists())

    def test_semantic_rebuild_refuses_rebound_rows_fields_parties_rules_and_coverage(self):
        for change in ("row-order", "position", "decoded", "party", "rule", "selector", "coverage", "version"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve(); build_specimen(base, "wildcat-v2")
                release = base / "release"
                manifest = json.loads((release / "coverage.json").read_bytes())
                name = "source.json" if change == "decoded" else "coverage.json" if change in ("coverage", "version") else "events.jsonl"
                path = release / name
                if name == "events.jsonl":
                    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
                    if change == "row-order": rows.reverse()
                    if change == "position": rows[0]["transaction"]["log_index"] += 100
                    if change == "party": rows[0]["parties"][0]["address"] = "0x" + "12" * 20
                    if change == "rule": rows[0]["provenance"]["mapping_rule"] = "wildcat-v2.borrow.v1"
                    if change == "selector": rows[0]["provenance"]["source_selector"] = "wildcat-journal:" + "00" * 32
                    data = jsonl_bytes(rows)
                else:
                    document = json.loads(path.read_bytes())
                    if change == "decoded": document["mapping_records"][0]["decoded"]["role"] = "invented"
                    if change == "coverage": document["coverage"]["included_events"] = {}
                    if change == "version": document["versions"]["adapter"]["version"] = "1.0.0"
                    data = canonical_json(document) + b"\n"
                path.write_bytes(data)
                if name != "coverage.json":
                    claim = "source" if name == "source.json" else "canonical"
                    manifest[claim].update(sha256=sha256_bytes(data), bytes=len(data))
                    (release / "coverage.json").write_bytes(canonical_json(manifest) + b"\n")
                with self.assertRaises(TabulariumError): verifier.verify(release / "coverage.json")
