"""Checked-in Goldfinch release, documentation and demonstration gates."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import unittest
from unittest import mock

from . import support
from tabularium_lib.verifier import verify


RELEASE = support.PLUGIN_ROOT / "examples" / "goldfinch-v0"
SOURCE = RELEASE / "source.json"
CAPTURE = RELEASE / "capture.json"
EVENTS = RELEASE / "events.jsonl"
COVERAGE = RELEASE / "coverage.json"
DEMO = RELEASE / "rebuild.py"
EXPECTED_HASHES = {
    "source.json": "644b706804b6e28d69b1028b87937e0e36c882f703419d0e2bf568b056892bc9",
    "capture.json": "b8b8e46d7d688accd32826b3c228758f8fb84ed678e4c36edf228d67ce65da50",
    "events.jsonl": "751754a2f913691cf95f3e9f859b156f9ccd7963b1d72d4fc3379348924469b1",
    "coverage.json": "58184a75d8eca6ae8d9b44653c36ce8c482549c5d3cecd1a2a991b0936561f6d",
}


class CheckedInReleaseTests(unittest.TestCase):
    def test_preserved_source_matches_the_capture_claim(self):
        capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
        self.assertEqual(capture["sha256"], EXPECTED_HASHES["source.json"])
        self.assertEqual(capture["bytes"], len(SOURCE.read_bytes()))

    def test_all_four_release_hashes_are_fixed(self):
        for name, expected in EXPECTED_HASHES.items():
            actual = hashlib.sha256((RELEASE / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_coverage_binds_the_named_release_and_safe_local_paths(self):
        manifest = json.loads(COVERAGE.read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"], "goldfinch-borrower-record-v0")
        self.assertEqual(
            [manifest[key]["path"] for key in ("source", "capture_manifest", "canonical")],
            ["source.json", "capture.json", "events.jsonl"],
        )
        for key in ("source", "capture_manifest", "canonical"):
            path = manifest[key]["path"]
            self.assertNotIn("..", Path(path).parts)
            self.assertFalse(Path(path).is_absolute())

    def test_release_has_the_declared_event_and_coverage_counts(self):
        rows = [json.loads(line) for line in EVENTS.read_text().splitlines()]
        self.assertEqual(len(rows), 511)
        self.assertEqual(Counter(row["event_family"] for row in rows), {
            "borrowing": 34,
            "repayment": 477,
        })
        coverage = json.loads(COVERAGE.read_text())
        self.assertEqual(coverage["coverage"]["included_entities"], {
            "borrows": 34,
            "repays": 477,
        })
        self.assertEqual(coverage["coverage"]["unsupported_entities"], {
            "_meta": 1,
            "callableLoans": 1,
            "creditLines": 31,
            "tranchedPools": 24,
        })

    def test_committed_release_verifies_offline_and_without_rewrites(self):
        paths = (SOURCE, CAPTURE, EVENTS, COVERAGE)
        before = {path: path.read_bytes() for path in paths}
        modes = {path: path.stat().st_mode for path in paths}
        try:
            for path in paths:
                path.chmod(0o444)
            with mock.patch.object(
                socket.socket, "connect", side_effect=AssertionError("network used")
            ):
                report = verify(COVERAGE)
        finally:
            for path, mode in modes.items():
                path.chmod(mode)
        self.assertEqual(report.release, "goldfinch-borrower-record-v0")
        self.assertEqual(report.rows, 511)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_documented_demo_rebuilds_and_compares_in_a_fresh_directory(self):
        result = subprocess.run(
            [sys.executable, str(DEMO)],
            cwd=support.REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verified goldfinch-borrower-record-v0 offline", result.stdout)
        self.assertIn(EXPECTED_HASHES["events.jsonl"], result.stdout)

    def test_data_dictionary_names_every_canonical_top_level_field(self):
        dictionary = (RELEASE / "DATA-DICTIONARY.md").read_text(encoding="utf-8")
        fields = json.loads(EVENTS.read_text().splitlines()[0]).keys()
        for field in fields:
            self.assertIn("`%s`" % field, dictionary)
        self.assertIn("complete source entity retained", dictionary)

    def test_release_docs_state_counts_and_semantic_limits(self):
        prose = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (RELEASE / "README.md", RELEASE / "DATA-DICTIONARY.md")
        )
        prose = " ".join(prose.split())
        for phrase in (
            "34 `borrows`",
            "477 `repays`",
            "hosted indexer",
            "not publisher identity or authenticity",
            "does not by itself prove that the borrower's full debt was settled",
        ):
            self.assertIn(phrase, prose)

    def test_adapter_guide_covers_the_extension_contract(self):
        guide = (support.PLUGIN_ROOT / "docs/adding-an-adapter.md").read_text()
        for phrase in (
            "Validate the source",
            "Define each mapping",
            "Record provenance",
            "Declare coverage",
            "Add fixtures and tests",
        ):
            self.assertIn(phrase, guide)

    def test_release_policy_requires_immutable_supersession(self):
        policy = (support.PLUGIN_ROOT / "docs/release-policy.md").read_text()
        self.assertIn("immutable once published", policy)
        self.assertIn("new release directory", policy)
        self.assertIn("preserve the earlier source, canonical and coverage bytes", policy)

    def test_public_docs_mark_the_prototype_built_and_link_the_release(self):
        root = (support.REPO_ROOT / "README.md").read_text()
        plugin = (support.PLUGIN_ROOT / "README.md").read_text()
        skill = (support.PLUGIN_ROOT / "skills/tabularium/SKILL.md").read_text()
        for prose in (plugin, skill):
            self.assertIn("goldfinch-v0", prose)
        self.assertIn("[Tabularium](./plugins/tabularium)", root)
        commons = root.split("### Lending and credit records", 1)[1].split("\n### ", 1)[0]
        for protocol in ("Compound", "Euler", "Goldfinch"):
            self.assertNotIn(protocol, commons)


if __name__ == "__main__":
    unittest.main()
