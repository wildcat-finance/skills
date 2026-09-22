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
    "source.json": "1d88fdb5bca293995fd02e5a59f060d74541c80405e7bf1987544e5f334a8744",
    "capture.json": "3cd14d1852561ec2aa9f498f37d6156b74ce321ec0965e81264925c4ba2e24ee",
    "events.jsonl": "490d3f6399f84af8a81a5401b3cc92bf7ecfbe98a6bb02f07215b9099625ccf7",
    "coverage.json": "b1538b633f1dfcfcc493afd033a52b4b199350b3a2221afb3c627a289d9de793",
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
        self.assertEqual(coverage["coverage"]["unsupported_events"], {})

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
        self.assertIn("the consensus log, unchanged", dictionary)

    def test_release_docs_state_counts_and_semantic_limits(self):
        prose = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (RELEASE / "README.md", RELEASE / "DATA-DICTIONARY.md")
        )
        prose = " ".join(prose.split())
        for phrase in (
            "282 `borrowing`",
            "218 `repayment`",
            "native-log",
            "not publisher identity or authenticity",
            "does not independently prove the chain boundary",
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
        """The roster moved, so the claim this guards moved with it.

        This case read the root README's `### Lending and credit records`
        entry. The front-door change removed the inlined roster: `README.md`
        now links `FUTUREPROOFING.md`, which holds the one complete catalogue,
        and neither the section nor the one-line entry exists any more.

        The interest is unchanged: the public claim about what Tabularium does
        must stay coverage-qualified rather than reading as a venue list, and a
        venue that is not covered must be named as missing rather than left to
        look covered. Both are checked against the entry that now carries them.
        """
        catalogue = (support.REPO_ROOT / "FUTUREPROOFING.md").read_text()
        plugin = (support.PLUGIN_ROOT / "README.md").read_text()
        skill = (support.PLUGIN_ROOT / "skills/tabularium/SKILL.md").read_text()
        for prose in (plugin, skill):
            self.assertIn("aave-v4-v0", prose)
        self.assertIn("[Tabularium](./plugins/tabularium)", catalogue)
        entry = catalogue.split("### TABULARIUM", 1)[1].split("\n### ", 1)[0]
        today, _, open_work = " ".join(entry.split()).partition("**Open work.**")
        self.assertIn("supported preserved venue records", today)
        self.assertIn("Compound Phase 1", open_work)


class PublishedBytesTests(unittest.TestCase):
    """The published v0 data files keep the digests they were published with.

    The superseding-releases design was chosen over migrating the three v0
    directories in place, and the whole value of that choice is that published
    bytes never move.  Nothing else in the suite would notice a v1 build that
    wrote one file into a v0 directory: every v0 case would be re-derived from
    the rewritten bytes and pass.  These twelve digests are the ones recorded
    at `1d131b98a78c888b571f302e5b4c899aa2e47caf`, the commit the releases were
    published at, and they are the assertion that would fail.
    """

    def test_the_twelve_published_v0_data_files_keep_their_digests(self):
        self.assertEqual(len(support.PUBLISHED_V0_DIGESTS), 12)
        self.assertEqual(
            support.PUBLISHED_COMMIT, "1d131b98a78c888b571f302e5b4c899aa2e47caf"
        )
        for relative, expected in sorted(support.PUBLISHED_V0_DIGESTS.items()):
            path = support.EXAMPLES / relative
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, relative)

    def test_the_recorded_digests_cover_every_legacy_release_data_file(self):
        """A digest the table forgets is a file nothing pins.

        The table is written out rather than derived, so the guard it provides
        is only as wide as its key set.  Binding that key set to the declared
        legacy releases and their data files keeps a forgotten entry visible.
        """
        expected = {
            "%s/%s" % (release, name)
            for release in support.LEGACY_RELEASES
            for name in support.RELEASE_DATA_FILES
        }
        self.assertEqual(set(support.PUBLISHED_V0_DIGESTS), expected)


class LedgerVersionTests(unittest.TestCase):
    """The evolution ledger and the skill frontmatter state one version."""

    LEDGER = support.PLUGIN_ROOT / "skills/tabularium/EVOLUTION.md"
    SKILL = support.PLUGIN_ROOT / "skills/tabularium/SKILL.md"

    def ledger_rows(self):
        text = self.LEDGER.read_text(encoding="utf-8")
        return [
            line
            for line in text.splitlines()
            if line.startswith("| `tabularium-v")
        ]

    def test_the_ledger_row_and_the_skill_version_agree(self):
        rows = self.ledger_rows()
        self.assertTrue(rows)
        latest = rows[-1].split("|")[1].strip().strip("`")
        self.assertTrue(latest.startswith("tabularium-v"), latest)
        version = latest[len("tabularium-v"):]
        text = self.LEDGER.read_text(encoding="utf-8")
        self.assertIn("- Current version: `%s`" % latest, text)
        self.assertIn('  version: "%s"' % version, self.SKILL.read_text(encoding="utf-8"))

    def test_the_new_generation_row_keeps_the_held_frontier_byte_for_byte(self):
        """A generation bump may not move the target the ledger holds.

        The contract at `skills/VERSIONING.md` allows only a completed frontier
        job to replace `Next Fiat job`, and binds each row to the SHA-256 of
        `{status}|{revision}|{current frontier}|{next job}`.  This step ships a
        schema and three releases; the held Compound v3 Phase 1 job is not its
        to alter, so the last two rows must carry the same revision and digest.
        """
        rows = self.ledger_rows()
        self.assertGreaterEqual(len(rows), 2)
        previous, latest = (
            [field.strip() for field in row.split("|")] for row in rows[-2:]
        )
        self.assertEqual(latest[2], "generation")
        self.assertEqual(latest[3], previous[3])
        self.assertEqual(latest[4], previous[4])
        text = self.LEDGER.read_text(encoding="utf-8")
        recorded = {}
        for line in text.splitlines():
            if line.startswith("- ") and ": " in line:
                name, _, value = line[2:].partition(": ")
                recorded.setdefault(name, value)
        canonical = "%s|%s|%s|%s\n" % (
            recorded["Frontier status"].strip("`"),
            recorded["Frontier revision"].strip("`"),
            recorded["Current frontier"],
            recorded["Next Fiat job"],
        )
        self.assertEqual(
            hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            latest[4].strip("`"),
        )


class SupersedingReleaseTests(unittest.TestCase):
    """`aave-v4-v1` restates the v0 release under schema 3 from its own bytes.

    The design this release implements keeps published bytes where they are, so
    what matters is not only that the v1 release is internally consistent but
    that it was built from the v0 source, byte for byte, and that its capture
    differs from the v0 capture in one field.  A v1 release built from a
    re-fetched source would verify perfectly and prove nothing about the v0
    release it claims to supersede.
    """

    V1 = support.PLUGIN_ROOT / "examples" / "aave-v4-v1"
    EXPECTED_HASHES = {
        "source.json": "1d88fdb5bca293995fd02e5a59f060d74541c80405e7bf1987544e5f334a8744",
        "capture.json": "c5ea81d7c065792498f9b7359f30a8a6a9d0c5a587bc7bfdf81cee60365ca89a",
        "events.jsonl": "81d416a10b70ab0f3d9a3bd41c0680e235b3b64f4f06cc36b4f4292c81136492",
        "coverage.json": "fb2d96db06d1ebf9b1e89529ddaa7dfbf7931960dd57745dde166dc73089d49b",
    }

    def test_all_four_release_hashes_are_fixed(self):
        for name, expected in self.EXPECTED_HASHES.items():
            actual = hashlib.sha256((self.V1 / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_the_source_bytes_are_the_v0_source_bytes(self):
        self.assertEqual((self.V1 / "source.json").read_bytes(), SOURCE.read_bytes())
        self.assertEqual(
            self.EXPECTED_HASHES["source.json"], EXPECTED_HASHES["source.json"]
        )

    def test_the_capture_differs_from_the_v0_capture_in_release_alone(self):
        v0 = json.loads(CAPTURE.read_text(encoding="utf-8"))
        v1 = json.loads((self.V1 / "capture.json").read_text(encoding="utf-8"))
        differing = sorted(
            key for key in set(v0) | set(v1) if v0.get(key) != v1.get(key)
        )
        self.assertEqual(differing, ["release"])
        self.assertEqual(v0["release"], "aave-v4-mainnet-credit-window-v0")
        self.assertEqual(v1["release"], "aave-v4-mainnet-credit-window-v1")
        self.assertEqual(v1["request"], v0["request"])

    def test_coverage_names_the_v1_release_and_schema_three(self):
        manifest = json.loads((self.V1 / "coverage.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"], "aave-v4-mainnet-credit-window-v1")
        self.assertEqual(manifest["schema_version"], 3)
        self.assertEqual(manifest["versions"]["event_schema"], 3)
        self.assertEqual(manifest["canonical"]["rows"], 500)

    def test_every_canonical_row_carries_schema_version_three(self):
        rows = [
            json.loads(line)
            for line in (self.V1 / "events.jsonl").read_text().splitlines()
            if line
        ]
        self.assertEqual(len(rows), 500)
        self.assertEqual({row["schema_version"] for row in rows}, {3})

    def test_the_committed_release_verifies_offline_as_schema_three(self):
        paths = tuple(self.V1 / name for name in self.EXPECTED_HASHES)
        before = {path: path.read_bytes() for path in paths}
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            report = verify(self.V1 / "coverage.json")
        self.assertEqual(report.schema_version, 3)
        self.assertEqual(report.release, "aave-v4-mainnet-credit-window-v1")
        self.assertEqual(report.rows, 500)
        self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_documented_demo_rebuilds_and_compares_in_a_fresh_directory(self):
        result = subprocess.run(
            [sys.executable, str(self.V1 / "rebuild.py")],
            cwd=support.REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "verified aave-v4-mainnet-credit-window-v1 offline", result.stdout
        )
        self.assertIn(self.EXPECTED_HASHES["events.jsonl"], result.stdout)

    def test_each_release_readme_names_the_other(self):
        """On-call question 4 of the study: which release replaced this one.

        A reader who arrives at a release directory has no other way to learn
        that a newer interpretation exists or that an older one was preserved,
        so the link is checked in both directions rather than only forwards.
        """
        v0_readme = (RELEASE / "README.md").read_text(encoding="utf-8")
        v1_readme = (self.V1 / "README.md").read_text(encoding="utf-8")
        self.assertIn("aave-v4-mainnet-credit-window-v1", v0_readme)
        self.assertIn("../aave-v4-v1/README.md", v0_readme)
        self.assertIn("aave-v4-mainnet-credit-window-v0", v1_readme)
        self.assertIn("../aave-v4-v0/README.md", v1_readme)


if __name__ == "__main__":
    unittest.main()
