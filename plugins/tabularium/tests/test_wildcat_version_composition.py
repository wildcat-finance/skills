"""Check fee/native composition against independent landed-parent controls."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import support

from tabularium_lib.core import canonical_json
from tabularium_lib.release_v2 import make_manifest
from tabularium_lib.adapters.euler_common import MappingResult
from tabularium_lib.wildcat_release import build_wildcat_canonical, verify_wildcat_canonical
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_rules import rules, rules_for
from tabularium_lib.wildcat_validation import tuples
from tabularium_lib.wildcat_versions import SUPPORTED_VERSIONS
from wildcat_fee_fixtures import fee_records
from wildcat_parameter_fixtures import inputs, raw_release

ROOT = Path(__file__).resolve().parents[3]
CONTROL = ROOT / "tests/fixtures/wildcat-parameter-fee-parent.json"


class VersionCompositionTests(unittest.TestCase):
    def test_exact_landed_fee_parent_mapping_and_release_bytes(self):
        control = json.loads(CONTROL.read_bytes())
        self.assertEqual(control["parent"], "8228f0d73ad74f957589051ce4b6563f6f3a8441")
        self.assertEqual(len(control["cases"]), 4)
        for case in control["cases"]:
            with self.subTest(case=case["key"]):
                contexts, records, _ = inputs(case["venue"], case["group"])
                data = canonical_json({"contexts": contexts, "records": records}) + b"\n"
                self.assertEqual(hashlib.sha256(data).hexdigest(), case["input_sha256"])
                mapped = map_records(case["venue"], contexts, records, "1.1.0")
                self.assertEqual(hashlib.sha256(canonical_json(mapped)).hexdigest(), case["mapping_sha256"])
                with tempfile.TemporaryDirectory() as temporary:
                    base = Path(temporary).resolve()
                    raw = raw_release(base, case["venue"], case["group"])
                    target = base / "release"
                    build_wildcat_canonical(raw, target, "g4-compatibility-" + case["key"], "1.1.0")
                    verify_wildcat_canonical(target / "coverage.json")
                    for name, expected in case["release_sha256"].items():
                        self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), expected, name)

    def test_feature_matrix_and_registry_projections(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            for version in SUPPORTED_VERSIONS:
                with self.subTest(venue=venue, version=version):
                    contexts, records = fee_records(venue)
                    mapped = map_records(venue, contexts, records, version)
                    fees = [e for e in mapped["events"] if e["action"].endswith(".fees-collected")]
                    self.assertEqual(bool(fees), version != "1.0.0")
                    contexts, records, _ = inputs(venue)
                    mapped = map_records(venue, contexts, records, version)
                    self.assertEqual(len(mapped["events"]), len(records) if version in ("1.2.0", "1.3.0") else 0)
                    selected = rules_for(version)
                    projection = rules(version)
                    self.assertEqual({v["rule"] for v in selected.values()}, {v["rule"] for v in projection.values()})
                    admitted = {v["action"].split(".", 1)[1] for v in selected.values() if v["venue"] == venue}
                    self.assertEqual(admitted, set(tuples(venue, version)))

    def test_manifest_default_preserves_recorded_version_and_explicit_override(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            contexts, records = fee_records(venue)
            mapped = map_records(venue, contexts, records, "1.1.0")
            result = MappingResult(mapped["events"], mapped["included_counts"], mapped["unsupported_counts"])
            capture = {"adapter": {"name": venue, "version": "1.1.0"},
                       "scope": {"chain": "ethereum-mainnet"}}
            args = ("constructed-manifest-control", venue, "source.json", b"{}",
                    "capture.json", b"{}", "events.jsonl", b"", capture, result, 3)
            default = make_manifest(*args)
            explicit = make_manifest(*args, adapter_version="1.2.0")
            self.assertEqual(default["versions"]["adapter"]["version"], "1.1.0")
            self.assertEqual(explicit["versions"]["adapter"]["version"], "1.2.0")

    def test_latest_native_changes_do_not_rewrite_fee_only_unsupported_reasons(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            contexts, records, _ = inputs(venue, "last_group")
            old = map_records(venue, contexts, records, "1.1.0")
            new = map_records(venue, contexts, records, "1.2.0")
            self.assertEqual(old["events"], new["events"])
            self.assertNotEqual(old["mapping_records"], new["mapping_records"])
            for record in old["mapping_records"]:
                self.assertEqual(record["limitations"], ["The concrete ABI is decoded; no canonical meaning is admitted for this event."])


if __name__ == "__main__":
    unittest.main()
