"""The registry drives the coverage table, so it has to stay honest."""

import unittest
import tempfile

from . import support  # noqa: F401

from probitas_lib import registry  # noqa: E402
from probitas_lib.adapters import run_adapter, unchecked_coverage  # noqa: E402
from probitas_lib.adapters.morpho_midnight import adapter as midnight_adapter  # noqa: E402
from probitas_lib.evidence import Coverage, EvidenceError  # noqa: E402

EXPECTED = {
    "wildcat",
    "morpho-blue",
    "euler-v1",
    "euler",
    "metamorpho",
    "morpho-vaults-v2",
    "morpho-midnight",
    "maple",
    "aave-v3",
    "aave-v4",
    "compound-v3",
    "goldfinch",
    "truefi",
    "clearpool",
    "centrifuge",
}


class TestRegistry(unittest.TestCase):
    def test_every_expected_venue_is_listed(self):
        self.assertEqual({v.id for v in registry.all_venues()}, EXPECTED)

    def test_ids_are_unique_and_sorted(self):
        ids = [v.id for v in registry.all_venues()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))

    def test_implemented_flags_match_the_adapters_that_exist(self):
        """The registry may not claim coverage the tool does not have.

        This is the check that keeps gate 2 meaningful across the remaining
        steps: flipping a flag without shipping an adapter fails here.
        """
        import probitas

        claimed = {v.id for v in registry.implemented()}
        self.assertEqual(claimed, set(probitas.ADAPTERS))

    def test_every_venue_carries_a_note(self):
        for venue in registry.all_venues():
            with self.subTest(venue=venue.id):
                self.assertTrue(venue.note.strip())

    def test_midnight_is_a_distinct_implemented_base_venue(self):
        venue = registry.BY_ID["morpho-midnight"]
        self.assertTrue(venue.implemented)
        self.assertEqual(venue.chain, "base")
        self.assertNotEqual(venue.id, "morpho-blue")


class TestCoverageForUncheckedVenues(unittest.TestCase):
    def test_a_venue_with_no_adapter_says_unimplemented(self):
        coverage = unchecked_coverage(registry.BY_ID["maple"], ("live",))
        self.assertEqual(coverage.status, "unimplemented")
        self.assertIn("introspection", coverage.note)


class TestAdapterFailures(unittest.TestCase):
    def test_a_raising_adapter_yields_an_error_row_and_no_records(self):
        def explode(addresses, config):
            raise RuntimeError("subgraph returned 502")

        records, coverage = run_adapter("wildcat", explode, {}, {})
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertIn("502", coverage.note)

    def test_an_error_row_is_not_a_clean_row(self):
        def explode(addresses, config):
            raise ValueError("boom")

        _, coverage = run_adapter("wildcat", explode, {}, {})
        self.assertNotIn(coverage.status, ("checked", "empty"))

    def test_record_count_comes_from_the_records(self):
        def quiet(addresses, config):
            return [], Coverage("wildcat", "empty")

        records, coverage = run_adapter("wildcat", quiet, {}, {})
        self.assertEqual(coverage.records, 0)
        self.assertEqual(coverage.status, "empty")

    def test_the_route_stamps_the_source_rather_than_the_adapter(self):
        """Four adapters would otherwise each read the same config key."""
        def quiet(addresses, config):
            return [], Coverage("wildcat", "empty", block_range="1-2")

        _, live = run_adapter("wildcat", quiet, {}, {})
        _, fixture = run_adapter("wildcat", quiet, {}, {"fixtures": "/somewhere"})
        self.assertEqual(live.source, "live")
        self.assertEqual(fixture.source, "fixtures")

    def test_an_error_row_still_names_the_route_that_failed(self):
        def explode(addresses, config):
            raise ValueError("boom")

        _, coverage = run_adapter("wildcat", explode, {}, {"fixtures": "/somewhere"})
        self.assertEqual(coverage.status, "error")
        self.assertEqual(coverage.source, "fixtures")

    def test_a_venue_nobody_checked_names_none(self):
        for venue in registry.all_venues():
            with self.subTest(venue=venue.id):
                self.assertEqual(unchecked_coverage(venue, ("live",)).source, "none")

    def test_an_adapter_returning_no_coverage_is_a_bug_not_a_silence(self):
        def sloppy(addresses, config):
            return [], None

        with self.assertRaises(ValueError):
            run_adapter("wildcat", sloppy, {}, {})

    def test_a_venue_no_route_reached_names_every_route_that_missed_it(self):
        """"unconfigured" alone cannot say which route came up short."""
        venue = registry.BY_ID["goldfinch"]
        both = unchecked_coverage(venue, ("fixtures", "archive"))
        self.assertEqual(both.source, "none")
        self.assertIn("no adapter ships for it", both.note)
        self.assertIn("not harvested into the selected Alexandria index", both.note)

    def test_a_union_note_keeps_the_venue_description(self):
        """Gate 4 reads this note as the gap's reason.

        A union dossier whose negative space said only "no adapter ships for
        it" would tell a reader less about the hole than a single-route one.
        """
        venue = registry.BY_ID["goldfinch"]
        note = unchecked_coverage(venue, ("fixtures", "archive")).note
        self.assertTrue(note.startswith(venue.note), note[:80])
        self.assertIn("Not reached by this run:", note)

    def test_unchecked_coverage_will_not_guess_a_route(self):
        """The note is provenance, and a default would invent some."""
        with self.assertRaises(TypeError):
            unchecked_coverage(registry.BY_ID["maple"])

    def test_a_single_route_run_keeps_the_sentence_it_always_printed(self):
        """An existing dossier's reader already knows these words."""
        venue = registry.BY_ID["goldfinch"]
        self.assertEqual(unchecked_coverage(venue, ("fixtures",)).note, venue.note)
        self.assertEqual(unchecked_coverage(venue, ("live",)).note, venue.note)
        archive_only = unchecked_coverage(venue, ("archive",))
        self.assertEqual(
            archive_only.note,
            "venue was not harvested into the selected Alexandria index",
        )

    def test_unknown_status_cannot_be_invented(self):
        with self.assertRaises(EvidenceError):
            Coverage("wildcat", "probably fine")

    def test_a_midnight_refusal_becomes_shared_error_coverage(self):
        subject = "0x" + "a1" * 20
        with tempfile.TemporaryDirectory() as directory:
            records, coverage = run_adapter(
                "morpho-midnight",
                midnight_adapter,
                {subject: "declared"},
                {"fixtures": directory},
            )
        self.assertEqual(records, [])
        self.assertEqual(coverage.status, "error")
        self.assertIn("no records emitted", coverage.note)
        self.assertNotIn(subject, coverage.note)


if __name__ == "__main__":
    unittest.main()
