"""Euler v1 and Euler V2 mappings keep source meaning and provenance."""

from copy import deepcopy
import json
import unittest

from . import support
from tabularium_lib.adapters import euler_v1, euler_v2
from tabularium_lib import CURRENT_EVENT_SCHEMA
from tabularium_lib.core import TabulariumError


EXAMPLES = support.PLUGIN_ROOT / "examples"


def load_release(name):
    root = EXAMPLES / name
    return json.loads((root / "source.json").read_text()), json.loads((root / "capture.json").read_text())


class EulerV1AdapterTests(unittest.TestCase):
    def setUp(self):
        self.source, self.capture = load_release("euler-v1-v0")

    def test_checked_in_borrow_keeps_exact_log_and_amount(self):
        mapped = euler_v1.map_source(self.source, self.capture, CURRENT_EVENT_SCHEMA)
        self.assertEqual(len(mapped.events), 1)
        event = mapped.events[0]
        self.assertEqual(event["event_family"], "borrowing")
        self.assertEqual(event["action"], "euler-v1.borrow")
        self.assertEqual(event["amounts"], [{
            "kind": "assets",
            "base_units": str(int(self.source["result"][0]["data"], 16)),
            "asset": "0x1a7e4e63778b4f12a199c062f3efdd288afcbce8",
        }])
        self.assertEqual(event["native_record"], self.source["result"][0])
        self.assertEqual(event["transaction"]["block_hash"], self.source["result"][0]["blockHash"])

    def test_repay_has_a_venue_qualified_repayment_rule(self):
        source = deepcopy(self.source)
        source["result"][0]["topics"][0] = euler_v1.REPAY_TOPIC
        event = euler_v1.map_source(source, self.capture, CURRENT_EVENT_SCHEMA).events[0]
        self.assertEqual((event["event_family"], event["action"]), ("repayment", "euler-v1.repay"))

    def test_liquidation_keeps_debt_and_collateral_legs_separate(self):
        source = deepcopy(self.source)
        row = source["result"][0]
        borrower = row["topics"][2]
        underlying = row["topics"][1]
        liquidator = "0x" + "0" * 24 + "11" * 20
        row["topics"] = [euler_v1.LIQUIDATION_TOPIC, liquidator, borrower, underlying]
        words = [int("22" * 20, 16), 7, 9, 10, 11, 12]
        row["data"] = "0x" + "".join("%064x" % word for word in words)
        event = euler_v1.map_source(source, self.capture, CURRENT_EVENT_SCHEMA).events[0]
        self.assertEqual(event["event_family"], "debt-resolution")
        self.assertEqual([leg["kind"] for leg in event["amounts"]], ["debt_repaid", "collateral_seized"])
        self.assertEqual([leg["base_units"] for leg in event["amounts"]], ["7", "9"])

    def test_wrong_borrower_fails_closed(self):
        source = deepcopy(self.source)
        source["result"][0]["topics"][2] = "0x" + "0" * 24 + "33" * 20
        with self.assertRaisesRegex(TabulariumError, "different borrower"):
            euler_v1.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_one_block_cannot_have_conflicting_hashes(self):
        source = deepcopy(self.source)
        duplicate = deepcopy(source["result"][0])
        duplicate["blockHash"] = "0x" + "44" * 32
        duplicate["logIndex"] = "0x210"
        source["result"].append(duplicate)
        with self.assertRaisesRegex(TabulariumError, "conflicting hashes"):
            euler_v1.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)


class EulerV2AdapterTests(unittest.TestCase):
    def setUp(self):
        self.source, self.capture = load_release("euler-v2-v0")

    def event_as(self, kind):
        source = deepcopy(self.source)
        row = source["data"][0]
        source["data"] = [row]
        row["type"] = kind
        row["category"] = euler_v2.EXPECTED_CATEGORIES[kind]
        row["id"] = "v3-ponder:fixture:%s" % kind
        if kind == "liquidation":
            row["assets"].append({
                "kind": "collateral",
                "amountRaw": "1000000000000000000",
                "address": "0x" + "22" * 20,
            })
        return euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA).events[0]

    def test_protocol_generation_and_source_api_are_not_conflated(self):
        event = euler_v2.map_source(self.source, self.capture, CURRENT_EVENT_SCHEMA).events[0]
        self.assertEqual(event["provenance"]["protocol_generation"], "euler-v2")
        self.assertEqual(event["provenance"]["source_api"], "euler-v3")

    def test_all_native_credit_types_keep_distinct_families(self):
        expected = {
            "borrow": "borrowing",
            "repay": "repayment",
            "liquidation": "debt-resolution",
            "debt_socialized": "debt-resolution",
            "pull_debt": "debt-transfer",
            "interest_accrued": "interest-accrual",
        }
        self.assertEqual({kind: self.event_as(kind)["event_family"] for kind in expected}, expected)

    def test_interest_is_not_flattened_into_a_draw(self):
        event = self.event_as("interest_accrued")
        self.assertEqual(event["action"], "euler-v2.interest-accrued")
        self.assertNotEqual(event["event_family"], "borrowing")

    def test_owner_subaccount_and_native_row_are_retained(self):
        event = euler_v2.map_source(self.source, self.capture, CURRENT_EVENT_SCHEMA).events[0]
        self.assertEqual([party["role"] for party in event["parties"][:2]], ["owner", "account"])
        self.assertEqual(event["native_record"], self.source["data"][1])
        self.assertIsNone(event["transaction"]["block_hash"])

    def test_unknown_type_fails_instead_of_entering_unsupported_coverage(self):
        source = deepcopy(self.source)
        source["data"][0]["type"] = "new_debt_shape"
        with self.assertRaisesRegex(TabulariumError, "unknown event type"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_bad_subaccount_relation_fails(self):
        source = deepcopy(self.source)
        source["data"][0]["subAccountIndex"] = 140
        with self.assertRaisesRegex(TabulariumError, "EVC owner"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_event_outside_timestamp_scope_fails(self):
        source = deepcopy(self.source)
        source["data"][0]["timestamp"] = "2026-08-17T02:32:00.000Z"
        with self.assertRaisesRegex(TabulariumError, "query scope"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_duplicate_transaction_log_identity_fails_even_with_distinct_ids(self):
        source = deepcopy(self.source)
        duplicate = deepcopy(source["data"][0])
        duplicate["id"] = "v3-ponder:distinct-id:same-log"
        source["data"] = [source["data"][0], duplicate]
        with self.assertRaisesRegex(TabulariumError, "transaction/log identity"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_huge_decimal_coverage_boundary_is_a_controlled_failure(self):
        source = deepcopy(self.source)
        source["meta"]["coverage"]["chains"][0]["indexedToBlock"] = "9" * 5000
        with self.assertRaisesRegex(TabulariumError, "safe integer"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_reversed_reported_coverage_fails_even_without_events(self):
        source = deepcopy(self.source)
        source["data"] = []
        chain = source["meta"]["coverage"]["chains"][0]
        chain["indexedFromBlock"], chain["indexedToBlock"] = "25774728", "20529207"
        with self.assertRaisesRegex(TabulariumError, "reversed indexed range"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_one_transaction_cannot_have_conflicting_metadata(self):
        source = deepcopy(self.source)
        source["data"][0]["blockNumber"] = "25771829"
        with self.assertRaisesRegex(TabulariumError, "conflicting metadata"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_unknown_amount_leg_fails_closed(self):
        source = deepcopy(self.source)
        source["data"][0]["assets"][0]["kind"] = "shares"
        with self.assertRaisesRegex(TabulariumError, "amount legs"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)

    def test_liquidation_requires_an_addressed_collateral_leg(self):
        source = deepcopy(self.source)
        source["data"] = [source["data"][0]]
        row = source["data"][0]
        row["type"] = "liquidation"
        row["category"] = "liquidations"
        with self.assertRaisesRegex(TabulariumError, "amount legs"):
            euler_v2.map_source(source, self.capture, CURRENT_EVENT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
