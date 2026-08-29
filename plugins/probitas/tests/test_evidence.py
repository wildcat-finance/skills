"""The evidence file has to refuse what the gates would otherwise have to catch."""

import os
import unittest

from . import support  # noqa: F401

from probitas_lib.evidence import (  # noqa: E402
    EVIDENCE_SCHEMA,
    Coverage,
    Evidence,
    EvidenceError,
    Gap,
    Record,
    classify_source,
)
from probitas_lib.adapters import run_adapter  # noqa: E402
from probitas_lib.adapters.morpho_midnight import adapter as midnight_adapter  # noqa: E402

ADDRESS = "0x00000000000000000000000000000000000000a1"
TX = "0x" + "ab" * 32


def a_record(**overrides):
    kwargs = dict(
        venue="wildcat",
        address=ADDRESS,
        provenance="declared",
        claim="market_delinquent",
        values={"market": "0xdead", "seconds": 4200},
        source=TX,
    )
    kwargs.update(overrides)
    return Record(**kwargs)


class TestSourceIsRequired(unittest.TestCase):
    def test_missing_source_raises(self):
        with self.assertRaises(TypeError):
            Record(
                venue="wildcat",
                address=ADDRESS,
                provenance="declared",
                claim="x",
                values={},
            )

    def test_none_source_raises(self):
        with self.assertRaises(EvidenceError):
            a_record(source=None)

    def test_empty_source_raises(self):
        with self.assertRaises(EvidenceError):
            a_record(source="")

    def test_whitespace_source_raises(self):
        with self.assertRaises(EvidenceError):
            a_record(source="   \t  ")

    def test_source_that_is_not_a_citation_raises(self):
        for bad in ("see the docs", "0xnothash", "ftp://x", "doc:", "tx 123"):
            with self.subTest(source=bad):
                with self.assertRaises(EvidenceError):
                    a_record(source=bad)

    def test_the_three_permitted_kinds(self):
        self.assertEqual(classify_source(TX), "transaction")
        self.assertEqual(classify_source("https://example.com/x"), "url")
        self.assertEqual(classify_source("doc:court filing 2024/117"), "document")

    def test_a_source_cannot_break_out_of_a_markdown_link(self):
        for attempt in (
            "https://example.com/x)](https://evil.example/x",
            "https://example.com/<script>",
            "https://example.com/`x`",
            "https://example.com/x|y",
            "doc:filing [see here](https://evil.example)",
        ):
            with self.subTest(source=attempt):
                with self.assertRaises(EvidenceError):
                    a_record(source=attempt)

    def test_an_absurdly_long_source_is_refused(self):
        with self.assertRaises(EvidenceError):
            a_record(source="https://example.com/" + "a" * 500)

    def test_a_source_may_not_hide_a_control_or_format_character(self):
        for hidden in ("\u200b", "\u202e", "\ufeff", "\x00", "\U000e0001"):
            with self.subTest(hidden=repr(hidden)):
                with self.assertRaises(EvidenceError) as caught:
                    a_record(source=f"https://example.com/a{hidden}b")
                self.assertIn("control or format character", str(caught.exception))

    def test_surrounding_whitespace_is_still_forgiven(self):
        self.assertEqual(
            a_record(source=f"  {TX}  ").source_kind, "transaction"
        )


class TestRecordFields(unittest.TestCase):
    def test_provenance_must_be_a_known_tier(self):
        with self.assertRaises(EvidenceError):
            a_record(provenance="probably")

    def test_address_is_lowercased(self):
        self.assertEqual(a_record(address=ADDRESS.upper()).address, ADDRESS)

    def test_integers_survive_as_strings(self):
        record = a_record(values={"amount": 2**200})
        self.assertEqual(record.values["amount"], str(2**200))

    def test_floats_are_refused(self):
        with self.assertRaises(EvidenceError):
            a_record(values={"amount": 1.5})

    def test_values_must_be_a_mapping(self):
        with self.assertRaises(EvidenceError):
            a_record(values=[("amount", 1)])

    def test_a_key_naming_a_person_is_refused(self):
        for key in (
            "name",
            "full_name",
            "director_name",
            "email",
            "phone",
            "dob",
            "passport",
            "employer",
            "telegram_handle",
            "linkedin",
            "ip",
        ):
            with self.subTest(key=key):
                with self.assertRaises(EvidenceError) as caught:
                    a_record(values={key: "whoever"})
                self.assertIn("names a person", str(caught.exception))

    def test_entity_shaped_keys_still_pass(self):
        record = a_record(
            values={"market": "0xdead", "borrower": ADDRESS, "amount": 12}
        )
        self.assertEqual(sorted(record.values), ["amount", "borrower", "market"])

    def test_a_thing_may_have_a_name_even_though_a_person_may_not(self):
        """A market has a name. The guard is broad, so the exceptions are listed."""
        record = a_record(
            values={
                "market_name": "Acme USD Coin",
                "token_symbol": "USDC",
                "market_age": 900,
            }
        )
        self.assertEqual(record.values["market_name"], "Acme USD Coin")
        self.assertEqual(record.values["market_age"], "900")

    def test_a_doc_reference_cannot_break_a_table_cell(self):
        with self.assertRaises(EvidenceError):
            a_record(source="doc:filing | injected column")

    def test_a_key_that_is_not_a_plain_identifier_is_refused(self):
        for key in ("Market Name", "market-name", "", "_x", "0x", "a" * 100):
            with self.subTest(key=key):
                with self.assertRaises(EvidenceError):
                    a_record(values={key: "x"})

    def test_a_nested_structure_is_refused(self):
        with self.assertRaises(EvidenceError):
            a_record(values={"batch": {"expiry": 1}})

    def test_an_absurdly_long_value_is_refused(self):
        with self.assertRaises(EvidenceError):
            a_record(values={"market": "x" * 500})


class TestEvidenceFile(unittest.TestCase):
    def evidence(self):
        return Evidence(
            entity="Acme Trading Ltd",
            addresses=[(ADDRESS, "declared"), ("0x" + "b" * 40, "inferred")],
        )

    def test_at_least_one_address_is_required(self):
        with self.assertRaises(EvidenceError):
            Evidence(entity="Acme", addresses=[])

    def test_a_record_must_cite_a_subject_address(self):
        with self.assertRaises(EvidenceError):
            self.evidence().add_record(a_record(address="0x" + "c" * 40))

    def test_only_records_may_enter(self):
        with self.assertRaises(EvidenceError):
            self.evidence().add_record({"venue": "wildcat"})

    def test_an_address_cannot_hold_two_provenance_tiers(self):
        with self.assertRaises(EvidenceError) as caught:
            Evidence(
                entity="Acme",
                addresses=[(ADDRESS, "declared"), (ADDRESS, "inferred")],
            )
        self.assertIn("one provenance tier", str(caught.exception))

    def test_the_same_address_twice_in_the_same_tier_is_fine(self):
        evidence = Evidence(
            entity="Acme", addresses=[(ADDRESS, "declared"), (ADDRESS, "declared")]
        )
        self.assertEqual(evidence.declared(), [ADDRESS])

    def test_tiers_stay_separated(self):
        evidence = self.evidence()
        self.assertEqual(evidence.by_tier("declared"), [ADDRESS])
        self.assertEqual(evidence.by_tier("inferred"), ["0x" + "b" * 40])

    def test_serialisation_is_deterministic(self):
        first, second = self.evidence(), self.evidence()
        for evidence, order in ((first, [3, 1, 2]), (second, [2, 3, 1])):
            for n in order:
                evidence.add_record(
                    a_record(claim=f"claim_{n}", source="0x" + f"{n:02x}" * 32)
                )
            evidence.add_coverage(Coverage("wildcat", "checked", source="live"))
            evidence.add_coverage(Coverage("maple", "unimplemented", source="none"))
            evidence.add_gap(Gap("maple history", "no adapter"))
        self.assertEqual(first.to_json(), second.to_json())

    def test_coverage_status_must_be_known(self):
        with self.assertRaises(EvidenceError):
            Coverage("wildcat", "fine")

    def test_coverage_source_must_be_known(self):
        with self.assertRaises(EvidenceError):
            Coverage("wildcat", "checked", source="somewhere")

    def test_a_row_with_no_source_cannot_enter_the_evidence_file(self):
        """A row that does not say how a venue was checked reads as checked."""
        evidence = self.evidence()
        with self.assertRaises(EvidenceError) as caught:
            evidence.add_coverage(Coverage("wildcat", "checked"))
        self.assertIn("names no source", str(caught.exception))

    def test_only_an_archive_row_may_name_releases(self):
        with self.assertRaises(EvidenceError):
            Coverage("wildcat", "checked", source="live", releases=["sha256:aa"])

    def test_releases_are_sorted_and_deduplicated(self):
        row = Coverage(
            "clearpool",
            "checked",
            source="archive",
            releases=["sha256:bb", "sha256:aa", "sha256:bb"],
        )
        self.assertEqual(row.releases, "sha256:aa,sha256:bb")

    def test_a_release_that_would_break_a_table_cell_is_refused(self):
        """The same shape as finding S2-R1-01, arriving from another plugin."""
        with self.assertRaises(EvidenceError):
            Coverage(
                "clearpool", "checked", source="archive", releases=["a](https://evil/"]
            )

    def test_releases_refuse_anything_that_is_not_a_string_or_a_sequence(self):
        """`list()` took a mapping's keys and turned an integer into a crash."""
        for value in (5, {"sha256:aa": 1}, b"sha256:aa"):
            with self.subTest(value=value):
                with self.assertRaises(EvidenceError):
                    Coverage("clearpool", "checked", source="archive", releases=value)

    def test_the_wire_carries_schema_two_and_names_every_source(self):
        evidence = self.evidence()
        evidence.add_coverage(Coverage("wildcat", "checked", source="fixtures"))
        payload = evidence.to_dict()
        self.assertEqual(payload["schema"], 2)
        for row in payload["coverage"]:
            self.assertIn("source", row)
            self.assertIn("releases", row)

    def test_two_rows_for_one_venue_sort_by_source(self):
        """Determinism has to survive a venue two routes both answered."""
        evidence = self.evidence()
        evidence.add_coverage(
            Coverage("wildcat", "checked", source="live", block_range="1-2")
        )
        evidence.add_coverage(
            Coverage(
                "wildcat",
                "checked",
                source="archive",
                block_range="1-2",
                releases=["sha256:aa"],
            )
        )
        sources = [row["source"] for row in evidence.to_dict()["coverage"]]
        self.assertEqual(sources, ["archive", "live"])

    def test_a_gap_needs_a_reason(self):
        with self.assertRaises(EvidenceError):
            Gap("maple history", "")

    def test_midnight_outcome_values_survive_serialisation(self):
        subject = "0x535690cb1330232dd4f2ac5b724040751bdf4c91"
        fixture = os.path.join(
            support.PLUGIN_ROOT, "tests", "fixtures", "midnight-late"
        )
        records, coverage = run_adapter(
            "morpho-midnight", midnight_adapter, {subject: "declared"}, {"fixtures": fixture}
        )
        evidence = Evidence(entity="Midnight Borrower", addresses=[(subject, "declared")])
        for record in records:
            evidence.add_record(record)
        evidence.add_coverage(coverage)

        payload = evidence.to_dict()
        outcome = next(
            record
            for record in payload["records"]
            if record["claim"] == "maturity_outcome"
        )
        self.assertEqual(payload["schema"], EVIDENCE_SCHEMA)
        self.assertEqual(outcome["values"]["obligation_state"], "outstanding_at_maturity")
        self.assertEqual(outcome["values"]["observation_state"], "settled_late")
        self.assertEqual(outcome["values"]["settlement_mode"], "liquidation")
        self.assertEqual(outcome["values"]["debt_units_at_maturity"], "136075232067")
        self.assertEqual(outcome["values"]["debt_units_at_observation"], "0")


if __name__ == "__main__":
    unittest.main()
