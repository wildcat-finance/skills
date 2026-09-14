"""The harness names its protocol source by identity and refuses other bytes.

`plugins/hexaemeron/harness/PROVENANCE.json` names eleven files of
`wildcat-finance/v2-protocol` at one commit, with each file's size and
SHA-256. The files themselves are not committed here: `fetch_protocol.py`
materialises them under `src/vendor/` and refuses bytes that differ from the
record. These tests hold the record's shape, prove the verifier rejects a
wrong, short or missing file, and, when the files have been fetched, check
them. Nothing here fetches or writes outside a temporary directory.
"""

import importlib.util
import json
import os
import re
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, os.pardir, "harness"))
RECORD = os.path.join(HARNESS, "PROVENANCE.json")
IGNORE = os.path.join(HARNESS, ".gitignore")
FETCHER = os.path.join(HARNESS, "fetch_protocol.py")
PROTOCOL_REF = "f5a26146987926f4811b72a795d662813dedfe85"
EXPECTED_FILES = 11
EXPECTED_TOTAL_BYTES = 46799


def load_fetcher():
    spec = importlib.util.spec_from_file_location("harness_fetch_protocol", FETCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_record():
    with open(RECORD, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def fetched():
    return all(
        os.path.isfile(os.path.join(HARNESS, entry["path"])) for entry in load_record()["files"]
    )


class HarnessProvenanceRecordTests(unittest.TestCase):
    def test_record_names_the_pinned_repository_and_commit(self):
        record = load_record()
        self.assertEqual(record["schema"], "wildcat.hexaemeron-harness-source.v1")
        self.assertEqual(record["repository"], "wildcat-finance/v2-protocol")
        self.assertEqual(record["ref"], PROTOCOL_REF)
        self.assertEqual(record["destination"], "src/vendor")
        self.assertTrue(record["source_url_template"].startswith("https://raw.githubusercontent.com/"))

    def test_every_entry_is_a_digest_under_the_destination_mirroring_upstream(self):
        record = load_record()
        self.assertEqual(len(record["files"]), EXPECTED_FILES)
        paths = [entry["path"] for entry in record["files"]]
        self.assertEqual(len(paths), len(set(paths)))
        for entry in record["files"]:
            with self.subTest(path=entry["path"]):
                self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(entry["bytes"], 0)
                self.assertTrue(entry["path"].startswith("src/vendor/"))
                self.assertEqual(entry["path"], "src/vendor/" + entry["upstream_path"][len("src/"):])
        self.assertEqual(sum(entry["bytes"] for entry in record["files"]), EXPECTED_TOTAL_BYTES)
        self.assertEqual(record["total_bytes"], EXPECTED_TOTAL_BYTES)

    def test_the_fetched_directory_is_never_committed(self):
        with open(IGNORE, "rb") as fh:
            lines = fh.read().decode("utf-8").splitlines()
        self.assertIn("/src/vendor/", lines)


class FetchVerifierTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = load_fetcher()
        self.root = tempfile.TemporaryDirectory(prefix="harness-fetch-")
        self.addCleanup(self.root.cleanup)
        data = b"pragma solidity 0.8.25;\n"
        self.data = data
        self.record = {
            "destination": "src/vendor",
            "files": [
                {
                    "path": "src/vendor/libraries/Probe.sol",
                    "upstream_path": "src/libraries/Probe.sol",
                    "bytes": len(data),
                    "sha256": __import__("hashlib").sha256(data).hexdigest(),
                }
            ],
        }
        self.path = os.path.join(self.root.name, "src", "vendor", "libraries", "Probe.sol")

    def write(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "wb") as fh:
            fh.write(data)

    def test_recorded_bytes_verify(self):
        self.write(self.data)
        self.assertEqual(self.fetcher.check(self.record, self.root.name), [])

    def test_a_missing_file_is_refused(self):
        problems = self.fetcher.check(self.record, self.root.name)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing", problems[0])

    def test_a_changed_byte_is_refused(self):
        self.write(self.data[:-2] + b"X\n")
        problems = self.fetcher.check(self.record, self.root.name)
        self.assertEqual(len(problems), 1)
        self.assertIn("sha256", problems[0])

    def test_a_short_file_is_refused(self):
        self.write(self.data[:-1])
        problems = self.fetcher.check(self.record, self.root.name)
        self.assertEqual(len(problems), 1)
        self.assertIn("bytes", problems[0])

    def test_a_record_path_outside_the_destination_is_refused(self):
        for bad in ("../outside.sol", "src/other/Probe.sol", "/abs/Probe.sol"):
            record = dict(self.record, files=[dict(self.record["files"][0], path=bad)])
            path = os.path.join(self.root.name, "record.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(record, fh)
            with self.subTest(path=bad), self.assertRaises(ValueError):
                self.fetcher.load_record(path)

    def test_the_https_source_is_pinned_to_one_host(self):
        self.assertEqual(self.fetcher.ALLOWED_HOST, "raw.githubusercontent.com")
        with self.assertRaises(self.fetcher.SourceError):
            self.fetcher.from_https(
                {"source_url_template": "https://example.com/{repository}/{ref}/{upstream_path}",
                 "repository": "r", "ref": "0" * 40},
                self.record["files"][0],
            )


@unittest.skipUnless(fetched(), "protocol source not fetched; run plugins/hexaemeron/harness/fetch_protocol.py")
class FetchedSourceTests(unittest.TestCase):
    def test_every_fetched_file_carries_its_recorded_bytes(self):
        fetcher = load_fetcher()
        self.assertEqual(fetcher.check(fetcher.load_record(), HARNESS), [])


if __name__ == "__main__":
    unittest.main()
