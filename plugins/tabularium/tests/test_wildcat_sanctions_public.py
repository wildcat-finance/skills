"""Reproduce public constructed routing and reject changed preserved bytes."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wildcat_sanctions_public as public
from tabularium_lib import verifier
from tabularium_lib.core import TabulariumError


class SanctionsPublicTests(unittest.TestCase):
    def test_each_generation_rebuilds_every_byte_and_verifies_after_move(self):
        for venue in public.VENUES:
            with self.subTest(venue=venue):
                self.assertEqual(public.rebuild_example(venue), 0)

    def test_public_release_exercises_positive_and_both_cardinality_refusals(self):
        for venue in public.VENUES:
            root = public.EXAMPLES / (venue + "-sanctions-v0") / "release"
            source = json.loads((root / "source.json").read_bytes())
            coverage = json.loads((root / "coverage.json").read_bytes())
            self.assertEqual(coverage["versions"]["adapter"]["version"], "1.3.0")
            companions = [row for row in source["mapping_records"]
                          if row["signature"] and "SanctionedAccountAssets" in row["signature"]]
            self.assertTrue(any(row["routing_joins"] for row in companions))
            self.assertTrue(all(row["disposition"] == "supporting-routing" for row in companions))
            gaps = coverage["coverage"]["unsupported_events"]
            self.assertTrue(any(key.endswith(":missing-primary") for key in gaps))
            self.assertTrue(any(key.endswith(":ambiguous-match") for key in gaps))
            transfers = [row for row in source["mapping_records"]
                         if row.get("join") and row["routing_joins"]]
            self.assertTrue(transfers)
            if venue == "wildcat-v2":
                self.assertTrue(any(row["routing_joins"] and "QueuedForWithdrawal" in row["signature"]
                                    for row in companions))

    def test_changed_raw_object_refuses_even_with_original_canonical_bytes(self):
        root = public.EXAMPLES / "wildcat-v2-sanctions-v0" / "release"
        with tempfile.TemporaryDirectory() as temporary:
            changed = Path(temporary).resolve() / "changed"
            shutil.copytree(root, changed)
            obj = next((changed / "source/raw-release/objects").rglob("*.json"), None)
            if obj is None:
                obj = next(path for path in (changed / "source/raw-release/objects").rglob("*") if path.is_file())
            obj.write_bytes(obj.read_bytes() + b" ")
            with self.assertRaises(TabulariumError):
                verifier.verify(changed / "coverage.json")

    def test_all_historical_native_and_batch_release_bytes_still_reproduce(self):
        from wildcat_v3_public_fixtures import rebuild_example as native
        from wildcat_batch_public_fixtures import rebuild_example as batches
        for venue in public.VENUES:
            with self.subTest(venue=venue), redirect_stdout(io.StringIO()):
                self.assertEqual(native(venue), 0)
                self.assertEqual(batches(venue), 0)
