"""Check older selectors against the actual landed routing runtime, and 1.4.0 against 1.3.0."""

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
from .wildcat_sanctions_fixtures import inputs as sanctions_inputs

ROOT = Path(__file__).resolve().parents[3]
CONTROL = ROOT / "tests/fixtures/wildcat-accrual-routing-parent.json"
ACCRUAL_ACTIONS = (".interest-and-fees-accrued", ".state-updated")
VENUES = ("wildcat-v1", "wildcat-v2")


def relabelled(value, version):
    result = json.loads(canonical_json(value))
    result["provenance"]["adapter_version"] = version
    return result


class AccrualCompositionTests(unittest.TestCase):
    def test_exact_landed_parent_outputs_for_all_older_selectors(self):
        control = json.loads(CONTROL.read_bytes())
        self.assertEqual(control["parent"], "59bef33488ce929ef625bb5fdb3e73b7bca7c5d7")
        self.assertEqual(len(control["cases"]), 8)
        self.assertEqual(sorted(case["version"] for case in control["cases"]),
                         sorted(("1.0.0", "1.1.0", "1.2.0", "1.3.0") * 2))
        for case in control["cases"]:
            with self.subTest(case=case["key"]):
                raw = ROOT / case["raw"]
                self.assertEqual(hashlib.sha256((raw / "manifest.json").read_bytes()).hexdigest(), case["raw_manifest_sha256"])
                admitted = load_raw(raw)
                mapped = map_records(case["venue"], admitted["contexts"], admitted["records"], case["version"])
                self.assertEqual(hashlib.sha256(canonical_json(mapped)).hexdigest(), case["mapping_sha256"])
                self.assertFalse(any(e["action"].endswith(ACCRUAL_ACTIONS) for e in mapped["events"]))
                with tempfile.TemporaryDirectory() as temporary:
                    target = Path(temporary).resolve() / "release"
                    build_wildcat_canonical(raw, target, case["release"], case["version"])
                    verify_wildcat_canonical(target / "coverage.json")
                    for name, digest in case["files"].items():
                        self.assertEqual(hashlib.sha256((target / name).read_bytes()).hexdigest(), digest, name)

    def test_new_selector_adds_only_accrual_rows_to_the_routing_selector(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                admitted = load_raw(ROOT / ("plugins/tabularium/examples/%s-accrual-v0/release/source/raw-release" % venue))
                old = map_records(venue, admitted["contexts"], admitted["records"], "1.3.0")
                new = map_records(venue, admitted["contexts"], admitted["records"], "1.4.0")
                added = [e for e in new["events"] if e["action"].endswith(ACCRUAL_ACTIONS)]
                kept = [e for e in new["events"] if not e["action"].endswith(ACCRUAL_ACTIONS)]
                self.assertTrue(added)
                self.assertEqual(kept, [relabelled(e, "1.4.0") for e in old["events"]])
                self.assertTrue(all(e["provenance"]["adapter_version"] == "1.4.0" for e in new["events"]))

    def test_new_selector_retains_fee_native_and_routing_meanings(self):
        for venue in VENUES:
            for kind in ("fees", "native", "routing"):
                if kind == "routing" and venue == "wildcat-v1":
                    contexts, records = sanctions_inputs("wildcat-v1")
                elif kind == "routing":
                    contexts, records = sanctions_inputs("wildcat-v2")
                else:
                    contexts, records = fee_records(venue) if kind == "fees" else inputs(venue)[:2]
                with self.subTest(venue=venue, kind=kind):
                    old = map_records(venue, contexts, records, "1.3.0")
                    new = map_records(venue, contexts, records, "1.4.0")
                    self.assertEqual(len(old["events"]), len(new["events"]))
                    self.assertEqual(list(new["events"]), [relabelled(e, "1.4.0") for e in old["events"]])
                    self.assertEqual(new["mapping_records"], old["mapping_records"])
                    self.assertEqual(new["dispositions"], old["dispositions"])


if __name__ == "__main__":
    unittest.main()
