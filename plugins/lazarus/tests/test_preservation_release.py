"""The release that ships in this repository, held to the fixture beside it.

A shipped release is a claim made once and read later. These tests are what stops
it going stale quietly: recapture the fixture without writing a new release, or
change what the binding checks, and the suite says so rather than the release
sitting there describing a fixture nobody has any more.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lazarus_lib.binding import CHECKS
from lazarus_lib.canonical import loads
from lazarus_lib.release import (
    FIXTURE_DIRECTORY,
    RELEASE_NAME,
    STATEMENT_NAME,
    release_digest,
    verify_release,
    write_release,
)
from lazarus_lib.verifier import verify_fixture

from . import support

FIXTURE = support.PLUGIN_ROOT / "examples" / "goldfinch-v0"
SHIPPED = support.PLUGIN_ROOT / "examples" / "goldfinch-v0-release"
RECEIPT_FIXTURE = support.PLUGIN_ROOT / "examples" / "goldfinch-v1"
RECEIPT_SHIPPED = support.PLUGIN_ROOT / "examples" / "goldfinch-v1-release"
DEMONSTRATION = (
    support.PLUGIN_ROOT / "examples" / "preservation-release-demo.py"
)

LEGACY_DIGESTS = {
    FIXTURE / "manifest.json": "c37cd789e5386a1347abd4dff24c8b1db96cdab771df4eb4d63056ba56145fa9",
    SHIPPED / STATEMENT_NAME: "d8b262278ffd4db76e449a2bfce4629903a70e7f4ad7c1f3a6ebbfb1f112555e",
    SHIPPED / RELEASE_NAME: "ec5c9b8091286de8713b6daf6cfdeaa7e9cfa6177b96c10a2ed20ffd6654bcff",
}


def document():
    return loads((SHIPPED / RELEASE_NAME).read_bytes())


def receipt_document():
    return loads((RECEIPT_SHIPPED / RELEASE_NAME).read_bytes())


def tree_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


class ShippedReleaseTests(unittest.TestCase):
    def test_the_legacy_manifest_statement_and_release_bytes_are_unchanged(self):
        for path, expected in LEGACY_DIGESTS.items():
            with self.subTest(path=path.name):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), expected
                )

    def test_the_legacy_fixture_has_no_anchor_records_or_new_release_fields(self):
        report = verify_fixture(FIXTURE)
        self.assertIn("chain_anchors", report)
        self.assertEqual(
            report["chain_anchors"],
            {
                "records": 0,
                "canonical_chain_claim": False,
                "provider_independence_claim": False,
            },
        )
        self.assertNotIn(
            "anchors.jsonl",
            {component["path"] for component in report["manifest"]["components"]},
        )
        self.assertEqual(
            set(document()["verified"]),
            {"block_hash", "evidence_counts", "canonical_chain_claim"},
        )

    def test_the_shipped_release_verifies(self):
        report = verify_release(SHIPPED)
        self.assertEqual(report["release_digest"], document()["release_digest"])

    def test_its_digest_covers_it(self):
        held = document()
        self.assertEqual(held["release_digest"], release_digest(held))

    def test_it_describes_the_fixture_checked_in_beside_it(self):
        """The test that stops a recapture shipping a stale release."""
        checked_in = verify_fixture(FIXTURE)
        held = document()
        self.assertEqual(
            held["fixture"]["fixture_digest"], checked_in["fixture_digest"]
        )
        self.assertEqual(held["verified"]["block_hash"], checked_in["block_hash"])
        self.assertEqual(
            held["verified"]["evidence_counts"], checked_in["evidence_counts"]
        )

    def test_its_fixture_copy_is_the_checked_in_fixture_byte_for_byte(self):
        copy = SHIPPED / FIXTURE_DIRECTORY
        held = {
            path.relative_to(copy).as_posix(): path.read_bytes()
            for path in copy.rglob("*")
            if path.is_file()
        }
        beside = {
            path.relative_to(FIXTURE).as_posix(): path.read_bytes()
            for path in FIXTURE.rglob("*")
            if path.is_file()
        }
        self.assertEqual(sorted(held), sorted(beside))
        for relative in sorted(beside):
            with self.subTest(component=relative):
                self.assertEqual(held[relative], beside[relative])

    def test_its_statement_digest_is_the_bytes_it_ships(self):
        written = (SHIPPED / STATEMENT_NAME).read_bytes()
        self.assertEqual(
            document()["statement"]["sha256"], hashlib.sha256(written).hexdigest()
        )

    def test_its_statement_declares_the_type_the_release_records(self):
        statement = json.loads((SHIPPED / STATEMENT_NAME).read_bytes())
        self.assertEqual(
            statement["predicateType"], document()["statement"]["predicate_type"]
        )

    def test_it_records_the_checks_this_binding_makes(self):
        """The test that stops a binding change shipping a release claiming
        checks nothing makes any more."""
        self.assertEqual(document()["binding"]["checks"], list(CHECKS))

    def test_it_claims_nothing_about_the_canonical_chain(self):
        self.assertIs(document()["verified"]["canonical_chain_claim"], False)

    def test_it_holds_nothing_but_the_three_parts(self):
        held = sorted(path.name for path in SHIPPED.iterdir())
        self.assertEqual(held, [FIXTURE_DIRECTORY, RELEASE_NAME, STATEMENT_NAME])


class ShippedReceiptReleaseTests(unittest.TestCase):
    def test_the_receipt_release_verifies_with_exact_pinned_digests(self):
        report = verify_release(RECEIPT_SHIPPED)
        self.assertEqual(
            report["fixture_digest"],
            "06043f4c4e7f62701d55cc0acb948f9330ec218ae50d786daa43ffefb6079eb2",
        )
        self.assertEqual(
            report["statement_sha256"],
            "8c1571c67953e0b2df7808e506c1eee0b3f63bfdcc9290877c3d1c7eb67d0bc1",
        )
        self.assertEqual(
            report["release_digest"],
            "c6b170ff7b93eb5e2e751f65ca85f3b937005c91fa633cecd801939637c258dc",
        )
        self.assertEqual(
            hashlib.sha256(
                (RECEIPT_SHIPPED / STATEMENT_NAME).read_bytes()
            ).hexdigest(),
            report["statement_sha256"],
        )
        self.assertEqual(
            receipt_document()["release_digest"], report["release_digest"]
        )
        self.assertEqual(
            release_digest(receipt_document()), report["release_digest"]
        )

    def test_the_receipt_release_carries_only_the_scoped_v2_authority(self):
        held = receipt_document()
        report = verify_release(RECEIPT_SHIPPED)
        self.assertEqual(held["schema_version"], 2)
        self.assertEqual(held["tool_version"], "0.2.0")
        self.assertEqual(
            report["predicate_type"],
            "https://ariadne.wildcat.finance/state-fixture/v2",
        )
        self.assertEqual(
            report["receipts_root"],
            "0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e",
        )
        self.assertEqual(report["evidence_counts"]["receipt_trie_proved"], 2)
        self.assertFalse(held["verified"]["canonical_chain_claim"])
        self.assertNotIn("transaction_hash", held["verified"])
        statement = loads((RECEIPT_SHIPPED / STATEMENT_NAME).read_bytes())
        self.assertEqual(
            statement["predicate"]["capture"]["command"],
            [
                "python3",
                "plugins/lazarus/examples/goldfinch-v1/demo.py",
                "build-fixture",
                "--out",
                "tmp/goldfinch-v1-rebuild",
            ],
        )
        skipped = {
            claim["name"]: claim.get("reason", "")
            for claim in statement["predicate"]["claims"]
            if claim["disposition"] == "skipped"
        }
        self.assertIn("transaction hash attributed by the receipt trie", skipped)
        self.assertIn(
            "recorded RPC decorations",
            skipped["transaction hash attributed by the receipt trie"],
        )

    def test_the_receipt_release_fixture_copy_is_exact(self):
        self.assertEqual(
            tree_bytes(RECEIPT_SHIPPED / FIXTURE_DIRECTORY),
            tree_bytes(RECEIPT_FIXTURE),
        )

    def test_the_receipt_release_rebuild_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            rebuilt = Path(directory) / "release"
            write_release(
                RECEIPT_FIXTURE,
                RECEIPT_SHIPPED / STATEMENT_NAME,
                rebuilt,
            )
            self.assertEqual(tree_bytes(rebuilt), tree_bytes(RECEIPT_SHIPPED))

    def test_the_legacy_and_receipt_formats_coexist(self):
        self.assertEqual(document()["schema_version"], 1)
        self.assertEqual(receipt_document()["schema_version"], 2)
        self.assertNotIn("receipts_root", document()["verified"])
        self.assertIn("receipts_root", receipt_document()["verified"])
        self.assertEqual(
            verify_fixture(FIXTURE)["manifest"]["tool_version"], "0.1.0"
        )
        self.assertEqual(
            verify_fixture(RECEIPT_FIXTURE)["manifest"]["tool_version"], "0.2.0"
        )


class DemonstrationTests(unittest.TestCase):
    def test_the_demonstration_runs_offline_and_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(DEMONSTRATION)],
            capture_output=True,
            text=True,
            cwd=str(support.PLUGIN_ROOT.parents[1]),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("both refusals held", result.stdout)

    def test_it_leaves_the_checked_in_release_alone(self):
        before = verify_release(SHIPPED)
        subprocess.run(
            [sys.executable, str(DEMONSTRATION)],
            capture_output=True,
            text=True,
            cwd=str(support.PLUGIN_ROOT.parents[1]),
        )
        self.assertEqual(verify_release(SHIPPED), before)


if __name__ == "__main__":
    unittest.main()
