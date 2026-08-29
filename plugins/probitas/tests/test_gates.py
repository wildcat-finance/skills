"""The five gates, each proved to fail on its own breach.

A gate that passes a good document proves nothing on its own. What matters is
that it fails the bad one, so every gate here gets a targeted breach and the
test asserts which gate caught it.
"""

import copy
import os
import unittest

from . import support

from probitas_lib import gates, render  # noqa: E402
from probitas_lib.evidence import Coverage, Evidence, Gap, Record  # noqa: E402
from probitas_lib.adapters import run_adapter  # noqa: E402
from probitas_lib.adapters.wildcat import adapter  # noqa: E402
from probitas_lib import registry  # noqa: E402

FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
DECLARED = "0x" + "a1" * 20
INFERRED = "0x" + "b2" * 20


def evidence(case="defaulted", inferred=False):
    addresses = [(DECLARED, "declared")]
    if inferred:
        addresses.append((INFERRED, "inferred"))
    subject = Evidence(entity="Acme Trading Ltd", addresses=addresses, run_id="test")

    records, coverage = run_adapter(
        "wildcat", adapter, dict(subject.addresses),
        {"fixtures": os.path.join(FIXTURES, case)},
    )
    for record in records:
        subject.add_record(record)
    subject.add_coverage(coverage)

    for venue in registry.all_venues():
        if venue.id == "wildcat":
            continue
        subject.add_coverage(Coverage(venue.id, "unimplemented", note=venue.note, source="none"))
        subject.add_gap(Gap(f"{venue.id} borrowing history", venue.note))

    return subject.to_dict()


def with_an_inferred_finding():
    """Evidence carrying one record against an address nobody declared."""
    subject = Evidence(
        entity="Acme Trading Ltd",
        addresses=[(DECLARED, "declared"), (INFERRED, "inferred")],
        run_id="test",
    )
    records, coverage = run_adapter(
        "wildcat", adapter, {DECLARED: "declared"},
        {"fixtures": os.path.join(FIXTURES, "defaulted")},
    )
    for record in records:
        subject.add_record(record)
    subject.add_record(
        Record(
            venue="wildcat",
            address=INFERRED,
            provenance="inferred",
            claim="borrow",
            values={"market": "0x" + "7" * 40, "amount": 4200000000},
            source="0x" + "f7" * 32,
            observed_at=1740500000,
            block=21950000,
        )
    )
    subject.add_coverage(coverage)
    for venue in registry.all_venues():
        if venue.id != "wildcat":
            subject.add_coverage(Coverage(venue.id, "unimplemented", note=venue.note, source="none"))
            subject.add_gap(Gap(f"{venue.id} borrowing history", venue.note))
    return subject.to_dict()


def dossier(payload):
    return render.render(payload)


def failures(document, payload):
    return [g for g in gates.check(document, payload) if not g.passed]


def caught_by(document, payload):
    breached = failures(document, payload)
    return breached[0].number if breached else None


class TestAGoodDossierPasses(unittest.TestCase):
    def test_all_five_gates_pass_on_each_fixture(self):
        for case in ("clean", "cured", "defaulted", "empty"):
            with self.subTest(case=case):
                payload = evidence(case)
                results = gates.check(dossier(payload), payload)
                self.assertEqual(len(results), 5)
                self.assertEqual(
                    [g.number for g in results if not g.passed],
                    [],
                    [g.line() for g in results],
                )

    def test_every_gate_prints_a_line(self):
        payload = evidence()
        for gate in gates.check(dossier(payload), payload):
            self.assertIn(gate.name, gate.line())
            self.assertIn("pass", gate.line())


class TestGateOneProvenance(unittest.TestCase):
    def test_an_inferred_address_outside_its_section_fails(self):
        payload = evidence(inferred=True)
        document = dossier(payload)
        broken = document.replace(
            "## Coverage", f"## Coverage\n\nAlso seen at `{INFERRED}`.", 1
        )
        self.assertEqual(caught_by(broken, payload), 1)

    def test_a_declared_address_inside_the_inferred_section_fails(self):
        payload = evidence(inferred=True)
        document = dossier(payload)
        broken = document.replace(
            "## Addresses not declared",
            f"## Addresses not declared\n\nPossibly `{DECLARED}`.",
            1,
        )
        self.assertEqual(caught_by(broken, payload), 1)

    def test_losing_the_section_entirely_fails(self):
        payload = evidence(inferred=True)
        broken = dossier(payload).replace("## Addresses not declared", "## Other")
        self.assertEqual(caught_by(broken, payload), 1)

    def test_no_inferred_addresses_is_a_pass_not_a_skip(self):
        payload = evidence()
        gate = gates.check(dossier(payload), payload)[0]
        self.assertTrue(gate.passed)
        self.assertIn("no inferred addresses", gate.detail)


class TestGateTwoCoverage(unittest.TestCase):
    def test_a_venue_missing_from_coverage_fails(self):
        payload = copy.deepcopy(evidence())
        payload["coverage"] = [c for c in payload["coverage"] if c["venue"] != "maple"]
        self.assertEqual(caught_by(dossier(payload), payload), 2)

    def test_a_queried_venue_with_no_block_range_fails(self):
        payload = copy.deepcopy(evidence())
        for row in payload["coverage"]:
            if row["venue"] == "wildcat":
                row["block_range"] = None
        self.assertEqual(caught_by(dossier(payload), payload), 2)

    def test_a_row_with_no_status_fails(self):
        payload = copy.deepcopy(evidence())
        payload["coverage"][0]["status"] = ""
        self.assertEqual(caught_by(dossier(payload), payload), 2)

    def test_a_second_row_for_one_venue_and_source_fails(self):
        """The collapse this gate used to do silently, now named."""
        payload = copy.deepcopy(evidence())
        wildcat = next(c for c in payload["coverage"] if c["venue"] == "wildcat")
        payload["coverage"].append(copy.deepcopy(wildcat))
        breached = failures(dossier(payload), payload)
        self.assertEqual(breached[0].number, 2)
        self.assertIn("two fixtures rows", breached[0].detail)

    def test_a_row_that_names_no_source_fails(self):
        payload = copy.deepcopy(evidence())
        payload["coverage"][0]["source"] = None
        breached = failures(dossier(payload), payload)
        self.assertEqual(breached[0].number, 2)
        self.assertIn("names no source", breached[0].detail)

    def test_an_archive_row_that_names_no_release_fails(self):
        payload = copy.deepcopy(evidence())
        wildcat = next(c for c in payload["coverage"] if c["venue"] == "wildcat")
        wildcat["source"] = "archive"
        wildcat["releases"] = None
        breached = failures(dossier(payload), payload)
        self.assertEqual(breached[0].number, 2)
        self.assertIn("names no release", breached[0].detail)

    def test_two_routes_over_one_venue_are_both_counted(self):
        """A union run answers for a venue twice, and both answers survive."""
        payload = copy.deepcopy(evidence())
        wildcat = next(c for c in payload["coverage"] if c["venue"] == "wildcat")
        archive = copy.deepcopy(wildcat)
        archive["source"] = "archive"
        archive["releases"] = "sha256:" + "ab" * 32
        archive["endpoint"] = "Alexandria index"
        payload["coverage"].append(archive)
        result = gates.check(dossier(payload), payload)[1]
        self.assertTrue(result.passed, result.detail)
        self.assertIn("15 venue(s) accounted for over 16 row(s)", result.detail)

    def test_a_row_whose_venue_is_not_a_name_fails_rather_than_crashing(self):
        """`verify` is pointed at files it did not write, so it may not raise."""
        payload = copy.deepcopy(evidence())
        stray = copy.deepcopy(payload["coverage"][0])
        stray["venue"] = None
        payload["coverage"].append(stray)
        document = dossier(evidence())
        breached = failures(document, payload)
        self.assertEqual(breached[0].number, 2)
        self.assertIn("names no venue", breached[0].detail)

    def test_an_empty_archive_row_needs_a_release_too(self):
        """Empty is the answer a reader is most likely to over-trust."""
        payload = copy.deepcopy(evidence())
        wildcat = next(c for c in payload["coverage"] if c["venue"] == "wildcat")
        wildcat["source"] = "archive"
        wildcat["status"] = "empty"
        wildcat["releases"] = None
        breached = failures(dossier(payload), payload)
        self.assertEqual(breached[0].number, 2)
        self.assertIn("names no release", breached[0].detail)

    def test_a_release_identity_is_a_permitted_figure(self):
        """Gate 3 rebuilds its allowed set from the fields, this one included."""
        payload = copy.deepcopy(evidence())
        wildcat = next(c for c in payload["coverage"] if c["venue"] == "wildcat")
        wildcat["source"] = "archive"
        wildcat["releases"] = "sha256:" + "ab" * 32
        self.assertIn("0x" + "ab" * 32, gates.known_tokens(payload))

    def test_an_unchecked_venue_needs_no_range(self):
        """It never queried anything, so a range would be a claim it cannot make."""
        payload = evidence()
        unchecked = [c for c in payload["coverage"] if c["status"] == "unimplemented"]
        self.assertTrue(unchecked)
        self.assertTrue(all(c["block_range"] is None for c in unchecked))
        self.assertTrue(gates.check(dossier(payload), payload)[1].passed)


class TestGateThreeSourcing(unittest.TestCase):
    def test_an_invented_transaction_hash_fails(self):
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary", "## Summary\n\nAlso 0x" + "de" * 32 + " repaid late.", 1
        )
        self.assertEqual(caught_by(broken, payload), 3)

    def test_a_rounded_amount_fails(self):
        payload = evidence()
        document = dossier(payload)
        self.assertIn("9,000,000.000000", document)
        self.assertEqual(
            caught_by(document.replace("9,000,000.000000", "9,100,000.000000"), payload),
            3,
        )

    def test_an_invented_market_fails(self):
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary", "## Summary\n\nAlso ran market 0x" + "9" * 40 + ".", 1
        )
        self.assertEqual(caught_by(broken, payload), 3)

    def test_a_citation_to_a_url_in_no_record_fails(self):
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary", "## Summary\n\nSee [the filing](https://evil.example/x).", 1
        )
        self.assertEqual(caught_by(broken, payload), 3)

    def test_a_record_with_a_blank_source_fails(self):
        payload = copy.deepcopy(evidence())
        payload["records"][0]["source"] = "   "
        self.assertEqual(caught_by(dossier(payload), payload), 3)

    def test_prose_without_figures_is_left_alone(self):
        """The sieve looks at figures, not at sentences."""
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary",
            "## Summary\n\nThe counterparty was slow to answer and quick to draw.",
            1,
        )
        self.assertEqual(failures(broken, payload), [])


class TestGateFourNegativeSpace(unittest.TestCase):
    def test_a_missing_section_fails(self):
        payload = evidence()
        broken = dossier(payload).replace("## What could not be established", "## Notes")
        self.assertEqual(caught_by(broken, payload), 4)

    def test_a_summary_above_it_fails(self):
        payload = evidence()
        document = dossier(payload)
        head, tail = document.split("## What could not be established", 1)
        broken = (
            head
            + "## Summary\n\nA clean counterparty.\n\n"
            + "## What could not be established"
            + tail
        )
        self.assertEqual(caught_by(broken, payload), 4)

    def test_an_empty_section_fails(self):
        payload = evidence()
        document = dossier(payload)
        start = document.index("## What could not be established")
        end = document.index("## Borrowing history")
        broken = (
            document[:start] + "## What could not be established\n\n" + document[end:]
        )
        self.assertEqual(caught_by(broken, payload), 4)


class TestGateFiveRating(unittest.TestCase):
    def test_a_rating_with_no_rubric_fails(self):
        payload = evidence()
        for verdict in (
            "Credit rating: B+",
            "Score: 72",
            "Overall grade: C",
            "This counterparty is rated B",
            "Risk score = 4 out of 5",
        ):
            with self.subTest(verdict=verdict):
                broken = dossier(payload).replace(
                    "## Summary", f"## Summary\n\n{verdict}\n", 1
                )
                self.assertEqual(caught_by(broken, payload), 5)

    def test_a_rating_beside_a_rubric_passes(self):
        payload = evidence()
        document = dossier(payload).replace(
            "## Summary",
            "## Summary\n\nCredit rating: B+\n\nRubric: repayment timeliness only.\n",
            1,
        )
        self.assertEqual(failures(document, payload), [])

    def test_saying_it_emits_no_rating_is_not_a_rating(self):
        """A gate that fires on its own boilerplate is one people learn to ignore."""
        payload = evidence()
        self.assertTrue(gates.check(dossier(payload), payload)[4].passed)

    def test_the_shipped_template_does_not_trip_its_own_gate(self):
        with open(render.TEMPLATE, encoding="utf-8") as handle:
            template = handle.read()
        self.assertIsNone(
            next(
                (
                    m
                    for m in gates.RATING.finditer(template)
                    if not gates.NEGATED.search(template[max(0, m.start() - 40) : m.start()])
                ),
                None,
            )
        )


class TestTheSieveCannotBeWalkedPast(unittest.TestCase):
    """Three ways to write a figure so a one-pass sieve does not see it."""

    def test_an_amount_grouped_with_spaces_still_fails(self):
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary", "## Summary\n\nDrew 9 100 000 USDC in total.", 1
        )
        self.assertEqual(caught_by(broken, payload), 3)

    def test_a_hash_written_without_its_prefix_still_fails(self):
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary", "## Summary\n\nSee transaction " + "de" * 32 + ".", 1
        )
        self.assertEqual(caught_by(broken, payload), 3)

    def test_digits_from_another_script_fail_rather_than_pass(self):
        payload = evidence()
        broken = dossier(payload).replace(
            "## Summary", "## Summary\n\nDrew \u0669\u0660\u0660\u0660\u0660\u0660\u0660.", 1
        )
        self.assertEqual(caught_by(broken, payload), 3)

    def test_regrouping_a_correct_figure_also_fails(self):
        """Failing closed on formatting the renderer did not produce.

        A right number written a way the tool never writes it is still a
        figure nobody can trace, and letting it through is how the spaced
        evasion gets back in. Cheaper to make the writer use the rendered
        form than to teach the sieve every way to group a thousand.
        """
        payload = evidence()
        document = dossier(payload)
        self.assertEqual(caught_by(document.replace("9,000,000", "9 000 000"), payload), 3)


class TestGatesReadTheDocumentNotOnlyTheEvidence(unittest.TestCase):
    def test_a_coverage_row_deleted_from_the_table_fails(self):
        payload = evidence()
        document = dossier(payload)
        lines = [
            line
            for line in document.splitlines()
            if line.startswith("| Maple Finance |")
        ]
        self.assertTrue(lines)
        self.assertEqual(caught_by(document.replace(lines[0], ""), payload), 2)

    def test_a_venue_named_only_in_another_row_note_does_not_count(self):
        """A mention is not a row."""
        payload = evidence()
        document = dossier(payload)
        lines = [
            line for line in document.splitlines() if line.startswith("| Maple Finance |")
        ]
        self.assertTrue(lines)
        smuggled = document.replace(
            lines[0], "| Aave v3 | unimplemented | -- | 0 | see Maple Finance |"
        )
        self.assertEqual(caught_by(smuggled, payload), 2)

    def test_a_gap_the_section_does_not_mention_fails(self):
        payload = evidence()
        document = dossier(payload)
        start = document.index("## What could not be established")
        end = document.index("## Borrowing history")
        gutted = (
            document[:start]
            + "## What could not be established\n\nNothing of note.\n\n"
            + document[end:]
        )
        self.assertEqual(caught_by(gutted, payload), 4)

    def test_a_finding_moved_out_of_the_inferred_section_fails(self):
        """A row dragged upward takes its citation with it and reads as record."""
        payload = with_an_inferred_finding()
        document = dossier(payload)
        start = document.index("## Addresses not declared")
        rows = [
            line
            for line in document[start:].splitlines()
            if line.startswith("|") and "wildcat" in line
        ]
        self.assertTrue(rows, "the fixture was supposed to produce an inferred finding")
        moved = document.replace("## Coverage", "## Coverage\n\n" + rows[0], 1)
        self.assertEqual(caught_by(moved, payload), 1)


class TestKnownTokens(unittest.TestCase):
    def test_a_space_does_not_swallow_a_figure(self):
        """With a space treated as a grouping mark the sieve finds nothing."""
        from probitas_lib import formatting

        tokens = formatting.numeric_tokens("held 9,000,000.000000 USDC at block 21900000")
        self.assertIn("9000000000000", tokens)
        self.assertIn("21900000", tokens)

    def test_short_words_and_small_numbers_are_ignored(self):
        from probitas_lib import formatting

        self.assertEqual(formatting.numeric_tokens("drew 12 times in 3 markets"), set())


if __name__ == "__main__":
    unittest.main()
