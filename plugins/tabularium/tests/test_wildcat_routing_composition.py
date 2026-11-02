"""Check older selectors against the actual landed native-state runtime."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from . import support
from tabularium_lib.core import canonical_json
from tabularium_lib.wildcat_source import load_raw
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_release import build_wildcat_canonical, verify_wildcat_canonical
from .wildcat_fee_fixtures import fee_records
from .wildcat_parameter_fixtures import inputs

ROOT = Path(__file__).resolve().parents[3]
CONTROL = ROOT / "tests/fixtures/wildcat-routing-native-parent.json"


class RoutingCompositionTests(unittest.TestCase):
    def test_exact_landed_parent_outputs_for_all_older_selectors(self):
        control = json.loads(CONTROL.read_bytes())
        self.assertEqual(control["parent"], "87142b40decb64f1c430847838ee8b5c1ab5475f")
        self.assertEqual(len(control["cases"]), 6)
        for case in control["cases"]:
            with self.subTest(case=case["key"]):
                raw = ROOT / case["raw"]
                self.assertEqual(hashlib.sha256((raw / "manifest.json").read_bytes()).hexdigest(), case["raw_manifest_sha256"])
                admitted = load_raw(raw)
                mapped = map_records(case["venue"], admitted["contexts"], admitted["records"], case["version"])
                self.assertEqual(hashlib.sha256(canonical_json(mapped)).hexdigest(), case["mapping_sha256"])
                self.assertTrue(all("routing_joins" not in m for m in mapped["mapping_records"]))
                with tempfile.TemporaryDirectory() as temporary:
                    target = Path(temporary).resolve() / "release"
                    build_wildcat_canonical(raw, target, case["release"], case["version"])
                    verify_wildcat_canonical(target / "coverage.json")
                    for name, digest in case["files"].items():
                        self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), digest, name)

    def test_new_selector_retains_fee_and_native_meanings_with_empty_routing(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            for kind in ("fees", "native"):
                contexts, records = fee_records(venue) if kind == "fees" else inputs(venue)[:2]
                old = map_records(venue, contexts, records, "1.2.0")
                new = map_records(venue, contexts, records, "1.3.0")
                self.assertEqual(len(old["events"]), len(new["events"]))
                self.assertTrue(all(e["provenance"]["adapter_version"] == "1.3.0" for e in new["events"]))
                for before, after in zip(old["events"], new["events"]):
                    expected = json.loads(canonical_json(before))
                    expected["provenance"]["adapter_version"] = "1.3.0"
                    self.assertEqual(after, expected)
                for mapping in new["mapping_records"]:
                    self.assertEqual(mapping["routing_joins"], [])


if __name__ == "__main__":
    unittest.main()
