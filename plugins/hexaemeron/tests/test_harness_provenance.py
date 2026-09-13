"""The vendored protocol closure matches its provenance record, byte for byte.

`plugins/hexaemeron/harness/src/vendor/PROVENANCE.json` pins eleven files from
`wildcat-finance/v2-protocol` at one ref. A Solidity test cannot read those
files without a filesystem permission the harness profile forbids, so the
digest check lives here, in the suite the root check map already runs. Drift
fails; nothing here re-baselines or writes.
"""

import hashlib
import json
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, os.pardir, "harness"))
VENDOR = os.path.join(HARNESS, "src", "vendor")
RECORD = os.path.join(VENDOR, "PROVENANCE.json")
PROTOCOL_REF = "f5a26146987926f4811b72a795d662813dedfe85"
EXPECTED_FILES = 11
EXPECTED_TOTAL_BYTES = 46799


def load_record():
    with open(RECORD, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def vendored_sources():
    found = []
    for base, _dirs, names in os.walk(VENDOR):
        for name in names:
            path = os.path.join(base, name)
            if path == RECORD:
                continue
            found.append(os.path.relpath(path, HARNESS).replace(os.sep, "/"))
    return sorted(found)


class HarnessProvenanceTests(unittest.TestCase):
    def test_record_parses_and_names_the_pinned_ref(self):
        record = load_record()
        self.assertEqual(record["repository"], "wildcat-finance/v2-protocol")
        self.assertEqual(record["ref"], PROTOCOL_REF)
        self.assertEqual(len(record["files"]), EXPECTED_FILES)

    def test_every_recorded_digest_matches_the_file_on_disk(self):
        for entry in load_record()["files"]:
            path = os.path.join(HARNESS, entry["vendored_path"])
            with self.subTest(path=entry["vendored_path"]):
                with open(path, "rb") as fh:
                    data = fh.read()
                self.assertEqual(len(data), entry["bytes"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), entry["sha256"])

    def test_every_vendored_file_is_recorded_and_nothing_else_is_present(self):
        recorded = sorted(entry["vendored_path"] for entry in load_record()["files"])
        self.assertEqual(vendored_sources(), recorded)

    def test_the_byte_total_is_the_pinned_closure_size(self):
        record = load_record()
        total = sum(entry["bytes"] for entry in record["files"])
        self.assertEqual(total, EXPECTED_TOTAL_BYTES)
        self.assertEqual(record["total_bytes"], EXPECTED_TOTAL_BYTES)

    def test_upstream_paths_sit_under_the_same_layout(self):
        for entry in load_record()["files"]:
            with self.subTest(path=entry["vendored_path"]):
                self.assertEqual(
                    entry["vendored_path"], "src/vendor/" + entry["upstream_path"][len("src/"):]
                )


if __name__ == "__main__":
    unittest.main()
