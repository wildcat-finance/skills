"""Checked-in Aave v4 release, documentation and demonstration gates."""

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


RELEASE = support.PLUGIN_ROOT / "examples" / "aave-v4-v0"
SOURCE = RELEASE / "source.json"
CAPTURE = RELEASE / "capture.json"
EVENTS = RELEASE / "events.jsonl"
COVERAGE = RELEASE / "coverage.json"
DEMO = RELEASE / "rebuild.py"
EXPECTED_HASHES = {
    "source.json": "af6255d371efe1cffe527053f9e7d25adce961bb7f1faa8774706ad51eeafb4d",
    "capture.json": "49bf9a366c3c68aab797b6e22568955a63476dd2043eb67f53cbf363ca06aef0",
    "events.jsonl": "a54a7ff15cfe9aa43639b00bb07036f0ebc2e832ac37f44fcee2b0dd0684daa4",
    "coverage.json": "91939a61f51df015e6a1a653a4eda290e762dd81004c9e95528923bf9b0c5c66",
}


class CheckedInReleaseTests(unittest.TestCase):
    def test_preserved_source_matches_the_capture_claim(self):
        capture = json.loads(CAPTURE.read_text(encoding="utf-8"))
        self.assertEqual(capture["source"]["sha256"], EXPECTED_HASHES["source.json"])
        self.assertEqual(capture["source"]["bytes"], len(SOURCE.read_bytes()))

    def test_all_four_release_hashes_are_fixed(self):
        for name, expected in EXPECTED_HASHES.items():
            actual = hashlib.sha256((RELEASE / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_coverage_binds_the_named_release_and_safe_local_paths(self):
        manifest = json.loads(COVERAGE.read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"], "aave-v4-mainnet-credit-window-v0")
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
        self.assertEqual(len(rows), 500)
        self.assertEqual(Counter(row["event_family"] for row in rows), {
            "borrowing": 282,
            "repayment": 218,
        })
        coverage = json.loads(COVERAGE.read_text())
        self.assertEqual(coverage["coverage"]["included_events"], {
            "borrow": 282,
            "repay": 218,
        })
        self.assertEqual(coverage["coverage"]["unsupported_events"], {
            "SET_COLLATERAL": 111,
            "SUPPLY": 376,
            "WITHDRAW": 264,
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
        self.assertEqual(report.release, "aave-v4-mainnet-credit-window-v0")
        self.assertEqual(report.rows, 500)
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
        self.assertIn("verified aave-v4-mainnet-credit-window-v0 offline", result.stdout)
        self.assertIn(EXPECTED_HASHES["events.jsonl"], result.stdout)

    def test_data_dictionary_names_every_canonical_top_level_field(self):
        dictionary = (RELEASE / "DATA-DICTIONARY.md").read_text(encoding="utf-8")
        fields = json.loads(EVENTS.read_text().splitlines()[0]).keys()
        for field in fields:
            self.assertIn("`%s`" % field, dictionary)
        self.assertIn("the venue row, unchanged", dictionary)

    def test_release_docs_state_counts_and_semantic_limits(self):
        prose = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (RELEASE / "README.md", RELEASE / "DATA-DICTIONARY.md")
        )
        prose = " ".join(prose.split())
        for phrase in (
            "282 `borrowing`",
            "218 `repayment`",
            "hosted indexer",
            "not publisher identity or authenticity",
            "no drawn value is reconstructed",
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
            self.assertIn("aave-v4-v0", prose)
        self.assertIn("[Tabularium](./plugins/tabularium)", root)
        commons = root.split("### Lending and credit records", 1)[1].split("\n### ", 1)[0]
        for protocol in ("Compound", "Euler", "Aave"):
            self.assertNotIn(protocol, commons)


if __name__ == "__main__":
    unittest.main()
