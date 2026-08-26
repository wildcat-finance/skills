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
import unittest

from lazarus_lib.binding import CHECKS
from lazarus_lib.canonical import loads
from lazarus_lib.release import (
    FIXTURE_DIRECTORY,
    RELEASE_NAME,
    STATEMENT_NAME,
    release_digest,
    verify_release,
)
from lazarus_lib.verifier import verify_fixture

from . import support

FIXTURE = support.PLUGIN_ROOT / "examples" / "goldfinch-v0"
SHIPPED = support.PLUGIN_ROOT / "examples" / "goldfinch-v0-release"
DEMONSTRATION = (
    support.PLUGIN_ROOT / "examples" / "preservation-release-demo.py"
)


def document():
    return loads((SHIPPED / RELEASE_NAME).read_bytes())


class ShippedReleaseTests(unittest.TestCase):
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
