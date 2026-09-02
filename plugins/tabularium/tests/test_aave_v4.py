"""The Aave v4 mapping keeps source meaning, provenance and its boundary."""

from copy import deepcopy
import json
import unittest

from . import support
from tabularium_lib.adapters import aave_v4
from tabularium_lib.core import TabulariumError


RELEASE = support.PLUGIN_ROOT / "examples" / "aave-v4-v0"


def load_release():
    return (
        json.loads((RELEASE / "source.json").read_text()),
        json.loads((RELEASE / "capture.json").read_text()),
    )


def first_of(rows, kind):
    return next(row for row in rows if row["type"] == kind)


class AaveV4AdapterTests(unittest.TestCase):
    def setUp(self):
        self.source, self.capture = load_release()
        self.rows = self.source["useractivities"]

    def map(self, source=None):
        return aave_v4.map_source(source or self.source, self.capture)

    def test_checked_in_window_maps_only_the_credit_types(self):
        mapped = self.map()
        self.assertEqual(len(mapped.events), 500)
        self.assertEqual(mapped.mapped_counts, {"borrow": 282, "repay": 218})
        self.assertEqual(
            mapped.unmapped_counts,
            {"SET_COLLATERAL": 111, "SUPPLY": 376, "WITHDRAW": 264},
        )

    def test_borrow_reads_the_drawn_amount_and_repay_reads_the_repaid_total(self):
        events = {event["action"]: event for event in self.map().events}
        borrow = events["aave-v4.borrow"]
        repay = events["aave-v4.repay"]
        self.assertEqual(
            [leg["kind"] for leg in borrow["amounts"]], ["assets_drawn", "shares"]
        )
        self.assertEqual(
            [leg["kind"] for leg in repay["amounts"]], ["assets_repaid", "shares"]
        )
        self.assertEqual(
            borrow["amounts"][0]["base_units"], borrow["native_record"]["amount"]
        )
        self.assertEqual(
            repay["amounts"][0]["base_units"],
            repay["native_record"]["totalAmountRepaid"],
        )
        self.assertIsNone(repay["native_record"]["amount"])

    def test_no_amount_leg_claims_an_underlying_token(self):
        for event in self.map().events:
            for leg in event["amounts"]:
                self.assertIsNone(leg["asset"])

    def test_provenance_names_the_spoke_and_the_exact_source_row(self):
        event = self.map().events[0]
        provenance = event["provenance"]
        self.assertEqual(provenance["source_kind"], "the-graph-entity")
        self.assertEqual(provenance["source_entity"], "useractivities")
        self.assertEqual(provenance["source_contract"], event["instrument"]["id"])
        self.assertEqual(
            provenance["source_selector"],
            "useractivities[id=%s]" % provenance["source_id"],
        )
        self.assertEqual(provenance["supporting_selectors"], [])
        self.assertEqual(provenance["adapter"], "aave-v4")
        self.assertEqual(provenance["protocol_generation"], "aave-v4")
        self.assertEqual(provenance["source_api"], "the-graph")

    def test_native_record_is_retained_unchanged(self):
        mapped = self.map()
        by_id = {event["provenance"]["source_id"]: event for event in mapped.events}
        for row in self.rows:
            if row["type"] in aave_v4.MAPPINGS:
                self.assertEqual(by_id[row["id"]]["native_record"], row)

    def test_rows_sort_by_block_then_log_index(self):
        events = self.map().events
        keys = [
            (e["transaction"]["block_number"], e["transaction"]["log_index"])
            for e in events
        ]
        self.assertEqual(keys, sorted(keys))

    def test_an_unknown_activity_type_is_refused(self):
        source = deepcopy(self.source)
        source["useractivities"][0]["type"] = "FLASHLOAN"
        with self.assertRaisesRegex(TabulariumError, "unsupported activity type"):
            self.map(source)

    def test_a_borrow_reporting_a_repaid_total_is_refused(self):
        source = deepcopy(self.source)
        row = first_of(source["useractivities"], "BORROW")
        row["totalAmountRepaid"] = "1"
        with self.assertRaisesRegex(TabulariumError, "BORROW that reports a repaid"):
            self.map(source)

    def test_a_repay_reporting_a_drawn_amount_is_refused(self):
        source = deepcopy(self.source)
        row = first_of(source["useractivities"], "REPAY")
        row["amount"] = "1"
        with self.assertRaisesRegex(TabulariumError, "REPAY that reports a drawn"):
            self.map(source)

    def test_a_row_outside_the_captured_window_is_refused(self):
        source = deepcopy(self.source)
        row = first_of(source["useractivities"], "BORROW")
        row["block"] = "1"
        with self.assertRaisesRegex(TabulariumError, "outside the captured window"):
            self.map(source)

    def test_a_reserve_from_another_spoke_is_refused(self):
        source = deepcopy(self.source)
        row = first_of(source["useractivities"], "BORROW")
        row["reserve"] = {"id": "0x" + "ab" * 20 + "07"}
        with self.assertRaisesRegex(TabulariumError, "does not belong to its spoke"):
            self.map(source)

    def test_an_id_that_disowns_its_transaction_is_refused(self):
        source = deepcopy(self.source)
        row = first_of(source["useractivities"], "BORROW")
        row["id"] = "0x" + "cd" * 32 + "00"
        with self.assertRaisesRegex(TabulariumError, "does not begin with its transaction"):
            self.map(source)

    def test_a_duplicate_source_row_is_refused(self):
        source = deepcopy(self.source)
        row = first_of(source["useractivities"], "BORROW")
        source["useractivities"].append(deepcopy(row))
        with self.assertRaisesRegex(TabulariumError, "repeats the selector"):
            self.map(source)

    def test_an_unexpected_top_level_field_is_refused(self):
        source = deepcopy(self.source)
        source["reserves"] = []
        with self.assertRaisesRegex(TabulariumError, "unsupported top-level field"):
            self.map(source)

    def test_a_missing_top_level_field_is_refused(self):
        source = deepcopy(self.source)
        del source["_meta"]
        with self.assertRaisesRegex(TabulariumError, "missing top-level field"):
            self.map(source)

    def test_a_window_with_no_credit_event_is_refused(self):
        source = deepcopy(self.source)
        source["useractivities"] = [
            row for row in source["useractivities"] if row["type"] not in aave_v4.MAPPINGS
        ]
        with self.assertRaisesRegex(TabulariumError, "maps no credit event"):
            self.map(source)

    def test_an_inverted_capture_window_is_refused(self):
        capture = deepcopy(self.capture)
        capture["scope"]["from_block"], capture["scope"]["to_block"] = (
            capture["scope"]["to_block"],
            capture["scope"]["from_block"],
        )
        with self.assertRaisesRegex(TabulariumError, "window is inverted"):
            aave_v4.map_source(self.source, capture)

    def test_a_capture_scope_naming_another_chain_is_refused(self):
        capture = deepcopy(self.capture)
        capture["scope"]["chain"] = "base-mainnet"
        with self.assertRaisesRegex(TabulariumError, "names another chain"):
            aave_v4.map_source(self.source, capture)


if __name__ == "__main__":
    unittest.main()
