"""The Aave v4 mapping reads consensus logs and keeps its asset boundary."""

from collections import Counter
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


def first_log(source, topic):
    return next(
        log for log in source["logs"] if log["topics"][0] == topic
    )


class AaveV4AdapterTests(unittest.TestCase):
    def setUp(self):
        self.source, self.capture = load_release()

    def map(self, source=None):
        return aave_v4.map_source(source or self.source, self.capture)

    def test_checked_in_window_maps_every_captured_log(self):
        mapped = self.map()
        self.assertEqual(len(mapped.events), 500)
        self.assertEqual(mapped.mapped_counts, {"borrow": 282, "repay": 218})
        self.assertEqual(mapped.unmapped_counts, {})

    def test_borrow_and_repay_read_the_established_data_words(self):
        events = {event["action"]: event for event in self.map().events}
        borrow = events["aave-v4.borrow"]
        repay = events["aave-v4.repay"]
        self.assertEqual(
            [leg["kind"] for leg in borrow["amounts"]], ["assets_drawn", "shares"]
        )
        self.assertEqual(
            [leg["kind"] for leg in repay["amounts"]], ["assets_repaid", "shares"]
        )
        for event in (borrow, repay):
            body = event["native_record"]["data"][2:]
            self.assertEqual(event["amounts"][1]["base_units"], str(int(body[0:64], 16)))
            self.assertEqual(event["amounts"][0]["base_units"], str(int(body[64:128], 16)))

    def test_every_asset_leg_names_a_token_and_every_share_leg_does_not(self):
        for event in self.map().events:
            assets, shares = event["amounts"]
            self.assertRegex(assets["asset"], r"^0x[0-9a-f]{40}$")
            self.assertIsNone(shares["asset"])

    def test_consensus_position_is_carried_rather_than_dropped(self):
        for event in self.map().events:
            transaction = event["transaction"]
            self.assertRegex(transaction["block_hash"], r"^0x[0-9a-f]{64}$")
            self.assertIsInstance(transaction["transaction_index"], int)
            self.assertIsInstance(transaction["block_number"], int)

    def test_provenance_names_the_log_and_the_reads_it_depended_on(self):
        event = self.map().events[0]
        provenance = event["provenance"]
        self.assertEqual(provenance["source_kind"], "consensus-log")
        self.assertEqual(provenance["source_entity"], "logs")
        self.assertEqual(provenance["source_contract"], event["instrument"]["id"])
        self.assertEqual(provenance["source_api"], "ethereum-json-rpc")
        self.assertEqual(len(provenance["supporting_selectors"]), 3)
        self.assertTrue(
            any("getReserve" in item for item in provenance["supporting_selectors"])
        )

    def test_native_log_is_retained_unchanged(self):
        mapped = self.map()
        by_id = {
            (e["native_record"]["transactionHash"], e["native_record"]["logIndex"]): e
            for e in mapped.events
        }
        for log in self.source["logs"]:
            event = by_id[(log["transactionHash"], log["logIndex"])]
            self.assertEqual(event["native_record"], log)

    def test_rows_sort_by_block_then_log_index(self):
        keys = [
            (e["transaction"]["block_number"], e["transaction"]["log_index"])
            for e in self.map().events
        ]
        self.assertEqual(keys, sorted(keys))

    def test_a_foreign_topic_is_refused(self):
        source = deepcopy(self.source)
        source["logs"][0]["topics"][0] = "0x" + "ab" * 32
        with self.assertRaisesRegex(TabulariumError, "not an Aave v4 credit topic"):
            self.map(source)

    def test_a_log_with_the_wrong_topic_count_is_refused(self):
        source = deepcopy(self.source)
        source["logs"][0]["topics"] = source["logs"][0]["topics"][:3]
        with self.assertRaisesRegex(TabulariumError, "does not carry four topics"):
            self.map(source)

    def test_a_data_word_count_that_disagrees_with_its_topic_is_refused(self):
        source = deepcopy(self.source)
        log = first_log(source, aave_v4.BORROW_TOPIC)
        log["data"] = log["data"] + "00" * 32
        with self.assertRaisesRegex(TabulariumError, "data word count"):
            self.map(source)

    def test_a_removed_log_is_refused(self):
        source = deepcopy(self.source)
        source["logs"][0]["removed"] = True
        with self.assertRaisesRegex(TabulariumError, "not a settled log"):
            self.map(source)

    def test_a_log_outside_the_captured_window_is_refused(self):
        source = deepcopy(self.source)
        source["logs"][0]["blockNumber"] = "0x1"
        with self.assertRaisesRegex(TabulariumError, "outside the captured window"):
            self.map(source)

    def test_a_reserve_the_capture_never_read_is_refused(self):
        source = deepcopy(self.source)
        source["logs"][0]["topics"][1] = "0x" + "00" * 31 + "ff"
        with self.assertRaisesRegex(TabulariumError, "never read"):
            self.map(source)

    def test_a_reserve_read_that_disagrees_with_its_own_bytes_is_refused(self):
        source = deepcopy(self.source)
        source["reserve_reads"][0]["underlying"] = "0x" + "ab" * 20
        with self.assertRaisesRegex(TabulariumError, "underlying disagrees"):
            self.map(source)

    def test_a_reserve_read_naming_another_hub_than_its_bytes_is_refused(self):
        source = deepcopy(self.source)
        source["reserve_reads"][0]["hub"] = "0x" + "ab" * 20
        with self.assertRaisesRegex(TabulariumError, "hub disagrees"):
            self.map(source)

    def test_token_decimals_that_disagree_with_their_own_result_are_refused(self):
        source = deepcopy(self.source)
        source["token_reads"][0]["decimals"] = 7
        with self.assertRaisesRegex(TabulariumError, "decimals disagree"):
            self.map(source)

    def test_a_duplicate_log_selector_is_refused(self):
        source = deepcopy(self.source)
        source["logs"].append(deepcopy(source["logs"][0]))
        with self.assertRaisesRegex(TabulariumError, "repeats the selector"):
            self.map(source)

    def test_one_block_with_two_hashes_is_refused(self):
        source = deepcopy(self.source)
        counts = Counter(log["blockNumber"] for log in source["logs"])
        shared = next(block for block, seen in counts.items() if seen > 1)
        first = next(log for log in source["logs"] if log["blockNumber"] == shared)
        first["blockHash"] = "0x" + "cd" * 32
        with self.assertRaisesRegex(TabulariumError, "conflicting hashes"):
            self.map(source)

    def test_an_unexpected_top_level_field_is_refused(self):
        source = deepcopy(self.source)
        source["receipts"] = []
        with self.assertRaisesRegex(TabulariumError, "unsupported top-level field"):
            self.map(source)

    def test_a_missing_top_level_field_is_refused(self):
        source = deepcopy(self.source)
        del source["token_reads"]
        with self.assertRaisesRegex(TabulariumError, "missing top-level field"):
            self.map(source)

    def test_a_source_window_that_disagrees_with_the_capture_is_refused(self):
        source = deepcopy(self.source)
        source["_meta"]["window"]["last_block"] += 1
        with self.assertRaisesRegex(TabulariumError, "window does not match"):
            self.map(source)

    def test_source_topics_that_are_not_the_credit_topics_are_refused(self):
        source = deepcopy(self.source)
        source["_meta"]["topics"]["borrow"] = "0x" + "ab" * 32
        with self.assertRaisesRegex(TabulariumError, "not the Aave v4 credit topics"):
            self.map(source)

    def test_a_capture_scope_naming_another_chain_is_refused(self):
        capture = deepcopy(self.capture)
        capture["scope"]["chain"] = "base-mainnet"
        with self.assertRaisesRegex(TabulariumError, "names another chain"):
            aave_v4.map_source(self.source, capture)


if __name__ == "__main__":
    unittest.main()
