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
        coverage = unchecked_coverage(registry.BY_ID["maple"])
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

    def test_an_adapter_returning_no_coverage_is_a_bug_not_a_silence(self):
        def sloppy(addresses, config):
            return [], None

        with self.assertRaises(ValueError):
            run_adapter("wildcat", sloppy, {}, {})

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
