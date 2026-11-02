"""Exercise the four batch meanings and the adjacent-market-burn join on constructed logs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))
import support
from tabularium_lib import builder, verifier
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes
from tabularium_lib.wildcat_release import build_wildcat_canonical
from tabularium_lib.wildcat_rows import map_records
from tabularium_lib.wildcat_rules import BURN_JOIN_RULE, RULES
from tabularium_lib.wildcat_validation import validate_row
from test_wildcat_v3_release import constructed_release
from wildcat_batch_fixtures import (
    BATCH_SIGNATURES, CLOSED, CREATED, EXPIRED, HOSTILE_SPECIMENS, PAYMENT, SECOND_MARKET,
    SOURCE_SPECIMENS, TRANSFER, batch_records, burn_rows, hostile, mapping_for, raws_for, row,
    rows, specimen, step_log, wrapper_burn_then_payment,
)
from wildcat_v3_fixtures import (
    ACCOUNT, ASSET, BATCH_ACTIONS, MARKET, ZERO, all_primary_events, batch_inputs, constructed_inputs,
    log, record, word,
)
from wildcat_v3_public_fixtures import build_pair, compare_pair

VENUES = ("wildcat-v1", "wildcat-v2")
EMPTY_AMOUNT_ACTIONS = ("market-closed", "withdrawal-batch-created", "withdrawal-batch-closed")
BURN_GAP = "attribution:withdrawal-batch-payment:burn"
UNCLAIMED_GAP = "attribution:transfer:unclaimed-burn"
# The schema 2 documents, pinned so a change to them fails here by name.
SCHEMA_2_DIGESTS = {
    "canonical-event-v2.json": "9ea081cf1cf89a1c0c81c2189767fd9bc69f1b65f24f19e3bab829e8948d65e8",
    "coverage-manifest-v2.json": "7756a58f9da49a852a418a200254e99a96105d9f7b461862b6db51302f07582b",
}
LIMITATIONS = {
    "withdrawal-batch-created": ["The expiry is native batch state; no request in the same transaction is named as the batch's cause."],
    "withdrawal-batch-payment": ["Reserved assets are set aside in the market for the batch; they are not received, spendable or executed."],
    "withdrawal-batch-expired": ["Amounts are cumulative at expiry; expiry does not establish later unpaid status.",
                                 "Any burn in the transaction belongs to the adjacent payment, not to this event."],
    "withdrawal-batch-closed": ["Closure means the batch is fully burned; it does not establish that any lender was paid."],
}


def mapped(venue, name):
    return map_records(venue, *specimen(venue, name))


def hostile_mapped(venue, name):
    return map_records(venue, *hostile(venue, name))


def joined(result, payment):
    """The burn row a payment joined, read from the join record both rows carry."""
    join = mapping_for(result, payment)["join"]
    return next(event for event in result["events"]
                if event["provenance"]["source_selector"] == join["companion_selector"])


def batch_release(base, venue, transactions):
    """Ingest batch logs through the real raw-release API and build a canonical release."""
    raws = raws_for(transactions)

    def replace(document, journal, plan):
        response = json.loads(journal["records"][0]["response"])
        response["result"] = raws
        journal["records"][0]["response"] = canonical_json(response).decode()

    raw = constructed_release(base, venue, replace)
    target = base / "canonical"
    build_wildcat_canonical(raw, target, "constructed-batches-" + venue)
    return target


class BatchMappingTests(unittest.TestCase):
    def test_created_rows_carry_pool_only_exit_queue_and_no_amounts(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                event = row(map_records(venue, *batch_inputs(venue)), "withdrawal-batch-created")
                self.assertEqual(event["event_family"], "exit-queue")
                self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
                self.assertEqual(event["amounts"], [])
                self.assertEqual(event["instrument"], {"type": venue + "-market", "id": MARKET})
                self.assertEqual(event["provenance"]["mapping_rule"], venue + ".withdrawal-batch-created.v1")
                self.assertEqual(event["provenance"]["source_entity"], CREATED)

    def test_payment_rows_carry_burned_scaled_claims_and_reserved_assets(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                event = row(map_records(venue, *batch_inputs(venue)), "withdrawal-batch-payment")
                self.assertEqual(event["event_family"], "exit-queue")
                self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
                self.assertEqual(event["amounts"], [{"kind": "burned-scaled-claims", "base_units": "35", "asset": None},
                                                    {"kind": "reserved-assets", "base_units": "40", "asset": ASSET}])
                self.assertEqual(event["provenance"]["source_entity"], PAYMENT)

    def test_expired_rows_carry_cumulative_totals_in_three_units(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                event = row(map_records(venue, *batch_inputs(venue)), "withdrawal-batch-expired")
                self.assertEqual(event["event_family"], "exit-queue")
                self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
                self.assertEqual(event["amounts"], [{"kind": "scaled-claims", "base_units": "70", "asset": None},
                                                    {"kind": "burned-scaled-claims", "base_units": "35", "asset": None},
                                                    {"kind": "reserved-assets", "base_units": "40", "asset": ASSET}])
                self.assertEqual(event["provenance"]["source_entity"], EXPIRED)

    def test_closed_rows_carry_pool_only_and_no_amounts(self):
        for venue in VENUES:
            with self.subTest(venue=venue):
                event = row(map_records(venue, *batch_inputs(venue)), "withdrawal-batch-closed")
                self.assertEqual(event["event_family"], "exit-queue")
                self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
                self.assertEqual(event["amounts"], [])
                self.assertEqual(event["provenance"]["source_entity"], CLOSED)

    def test_every_batch_row_is_primary_with_an_actor_gap_and_no_canonical_gap(self):
        for venue in VENUES:
            result = map_records(venue, *batch_inputs(venue))
            self.assertEqual({d["disposition"] for d in result["dispositions"]}, {"primary"})
            for action in BATCH_ACTIONS:
                self.assertEqual(result["included_counts"][action], 1)
                self.assertEqual(result["unsupported_counts"]["attribution:%s:actor" % action], 1)
            self.assertFalse([key for key in result["unsupported_counts"] if key.startswith("canonical:")])
            self.assertFalse([key for key in result["unsupported_counts"] if "WithdrawalBatch" in key])

    def test_expiry_stays_a_decoded_native_field_and_never_a_party_amount_or_row_field(self):
        for venue in VENUES:
            result = map_records(venue, *batch_inputs(venue))
            for action in BATCH_ACTIONS:
                event = row(result, action)
                evidence = mapping_for(result, event)
                self.assertEqual(evidence["decoded"]["expiry"], "1700000000")
                self.assertEqual(event["native_record"]["topics"][1], "0x" + word(1700000000))
                self.assertEqual(set(event), {"schema_version", "id", "event_family", "action", "venue", "chain",
                                              "transaction", "parties", "instrument", "amounts", "provenance",
                                              "native_record"})
                self.assertEqual([party["role"] for party in event["parties"]], ["pool"])
                self.assertNotIn("expiry", [amount["kind"] for amount in event["amounts"]])

    def test_reserved_assets_name_the_underlying_asset_or_stay_null_with_a_gap(self):
        for venue in VENUES:
            contexts, records = batch_inputs(venue)
            contexts[MARKET]["asset"] = None
            result = map_records(venue, contexts, records)
            for action in ("withdrawal-batch-payment", "withdrawal-batch-expired"):
                reserved = next(a for a in row(result, action)["amounts"] if a["kind"] == "reserved-assets")
                self.assertIsNone(reserved["asset"])
                self.assertEqual(result["unsupported_counts"]["attribution:%s:asset" % action], 1)
            for event in result["events"]:
                for amount in event["amounts"]:
                    if amount["kind"] in ("scaled-claims", "burned-scaled-claims"):
                        self.assertIsNone(amount["asset"])

    def test_batch_limitations_read_reserved_as_reserved_and_name_no_cause(self):
        for venue in VENUES:
            result = map_records(venue, *batch_inputs(venue))
            for action, expected in LIMITATIONS.items():
                evidence = mapping_for(result, row(result, action))
                expected = list(expected)
                if action == "withdrawal-batch-payment":
                    expected.append("The market burn at the previous log index is joined; both rows carry each other's selector.")
                if action == "withdrawal-batch-closed" and venue == "wildcat-v2":
                    expected.append("A V2 market closure also closes its pending batch; this row does not name which path closed it.")
                self.assertEqual(evidence["limitations"], expected, (venue, action))
                text = " ".join(evidence["limitations"] + evidence["supporting_selectors"] + list(evidence["decoded"]))
                for phrase in ("lender receipt", "spendable cash", "caused by", "because of"):
                    self.assertNotIn(phrase, text)

    def test_v1_queue_emission_order_joins_the_payment_to_its_burn(self):
        result = mapped("wildcat-v1", "v1-queue-first-batch")
        self.assertEqual([e["action"].split(".", 1)[1] for e in result["events"]],
                         ["transfer", "withdrawal-batch-created", "withdrawal-queued", "transfer", "withdrawal-batch-payment"])
        payment = row(result, "withdrawal-batch-payment")
        burn = joined(result, payment)
        self.assertEqual(burn["transaction"]["log_index"], payment["transaction"]["log_index"] - 1)
        self.assertNotIn(BURN_GAP, result["unsupported_counts"])
        self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])

    def test_v2_queue_emission_order_joins_the_payment_to_its_burn(self):
        result = mapped("wildcat-v2", "v2-queue-first-batch")
        self.assertEqual([e["action"].split(".", 1)[1] for e in result["events"]],
                         ["withdrawal-batch-created", "transfer", "withdrawal-queued", "transfer", "withdrawal-batch-payment"])
        payment = row(result, "withdrawal-batch-payment")
        burn = joined(result, payment)
        self.assertEqual(burn["transaction"]["log_index"], payment["transaction"]["log_index"] - 1)
        self.assertNotIn(BURN_GAP, result["unsupported_counts"])
        self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])

    def test_joined_rows_carry_each_others_selector_and_the_same_join_record(self):
        for venue in VENUES:
            result = map_records(venue, *batch_inputs(venue))
            payment = row(result, "withdrawal-batch-payment")
            burn = joined(result, payment)
            self.assertEqual(payment["provenance"]["supporting_selectors"][-1], burn["provenance"]["source_selector"])
            self.assertEqual(burn["provenance"]["supporting_selectors"][-1], payment["provenance"]["source_selector"])
            payment_evidence, burn_evidence = mapping_for(result, payment), mapping_for(result, burn)
            self.assertEqual(payment_evidence["join"], burn_evidence["join"])
            self.assertEqual(payment_evidence["join"]["evidence_class"], "join-inference")
            self.assertEqual(payment_evidence["join"]["rule"], BURN_JOIN_RULE)
            self.assertEqual(payment_evidence["join"]["primary_selector"], payment["provenance"]["source_selector"])
            self.assertEqual(payment_evidence["join"]["companion_selector"], burn["provenance"]["source_selector"])
            self.assertEqual(payment_evidence["supporting_selectors"][-1], burn["provenance"]["source_selector"])
            self.assertEqual(burn_evidence["supporting_selectors"][-1], payment["provenance"]["source_selector"])
            self.assertEqual(burn["amounts"], [{"kind": "market-token-claims", "base_units": "40", "asset": MARKET}])
            self.assertEqual(burn["action"], venue + ".transfer")

    def test_join_conditions_record_market_transaction_indices_endpoints_and_value(self):
        result = mapped("wildcat-v2", "expired-paid-closed")
        payment = row(result, "withdrawal-batch-payment")
        join = mapping_for(result, payment)["join"]
        self.assertEqual(join["conditions"], {
            "market": MARKET, "transaction_hash": payment["transaction"]["hash"],
            "burn_log_index": 0, "payment_log_index": 1, "from": MARKET, "to": ZERO, "value": "25"})

    def test_two_payments_with_equal_amounts_in_one_transaction_each_join_their_own_burn(self):
        for venue in VENUES:
            result = mapped(venue, "repay-two-unpaid-equal-amounts")
            payments = rows(result, "withdrawal-batch-payment")
            self.assertEqual(len(payments), 2)
            burns = [joined(result, payment) for payment in payments]
            self.assertEqual([b["transaction"]["log_index"] for b in burns], [1, 4])
            self.assertEqual([p["transaction"]["log_index"] for p in payments], [2, 5])
            self.assertEqual(len({b["provenance"]["source_selector"] for b in burns}), 2)
            self.assertEqual([mapping_for(result, p)["decoded"]["expiry"] for p in payments], ["100", "200"])
            self.assertNotIn(BURN_GAP, result["unsupported_counts"])
            self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])
            self.assertEqual(row(result, "debt-repaid")["parties"][0]["role"], "payer")

    def test_same_expiry_paid_twice_in_one_transaction_joins_both_burns(self):
        result = mapped("wildcat-v2", "queue-double-payment-same-expiry")
        payments = rows(result, "withdrawal-batch-payment")
        self.assertEqual([mapping_for(result, p)["decoded"]["expiry"] for p in payments], ["300", "300"])
        self.assertEqual([joined(result, p)["transaction"]["log_index"] for p in payments], [0, 4])
        self.assertEqual(len(burn_rows(result)), 2)
        self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])
        self.assertNotIn(BURN_GAP, result["unsupported_counts"])

    def test_expired_and_closed_rows_carry_no_join(self):
        for venue, name in (("wildcat-v1", "expired-paid-closed"), ("wildcat-v2", "v2-close-market")):
            result = mapped(venue, name)
            for action in ("withdrawal-batch-expired", "withdrawal-batch-closed", "withdrawal-batch-created"):
                for event in rows(result, action):
                    evidence = mapping_for(result, event)
                    self.assertIsNone(evidence["join"])
                    self.assertEqual(len(event["provenance"]["supporting_selectors"]), 1)
            self.assertEqual(len([m for m in result["mapping_records"] if m["join"]]), 2)

    def test_reordered_burn_after_payment_leaves_both_gaps_and_no_join(self):
        for venue in VENUES:
            result = hostile_mapped(venue, "burn-after-payment")
            self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
            self.assertEqual(result["unsupported_counts"][UNCLAIMED_GAP], 1)
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))
            self.assertTrue(all(len(e["provenance"]["supporting_selectors"]) == 1 for e in result["events"]))

    def test_changed_burn_value_leaves_both_gaps_and_no_join(self):
        for venue in VENUES:
            result = hostile_mapped(venue, "burn-value-changed")
            self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
            self.assertEqual(result["unsupported_counts"][UNCLAIMED_GAP], 1)
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))

    def test_burn_without_payment_is_an_unclaimed_gap(self):
        for venue in VENUES:
            result = hostile_mapped(venue, "burn-without-payment")
            self.assertEqual(result["unsupported_counts"][UNCLAIMED_GAP], 1)
            self.assertNotIn(BURN_GAP, result["unsupported_counts"])
            self.assertEqual(len(burn_rows(result)), 1)
            self.assertEqual(len(rows(result, "transfer")), 2)
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))

    def test_two_burns_before_one_payment_join_only_the_adjacent_burn(self):
        for venue in VENUES:
            result = hostile_mapped(venue, "two-burns-one-payment")
            payment = row(result, "withdrawal-batch-payment")
            self.assertEqual(joined(result, payment)["transaction"]["log_index"], 1)
            self.assertEqual(result["unsupported_counts"][UNCLAIMED_GAP], 1)
            self.assertNotIn(BURN_GAP, result["unsupported_counts"])
            first = next(b for b in burn_rows(result) if b["transaction"]["log_index"] == 0)
            self.assertIsNone(mapping_for(result, first)["join"])
            self.assertIn(UNCLAIMED_GAP, next(d for d in result["dispositions"]
                                              if d["source_selector"] == first["provenance"]["source_selector"])["gaps"])

    def test_payment_without_burn_records_the_burn_gap(self):
        for venue in VENUES:
            result = hostile_mapped(venue, "payment-without-burn")
            self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
            self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])
            payment = row(result, "withdrawal-batch-payment")
            self.assertIsNone(mapping_for(result, payment)["join"])
            self.assertEqual(payment["provenance"]["supporting_selectors"][-1][:16], "wildcat-context:")
            self.assertEqual(row(result, "withdrawal-queued")["parties"][0]["role"], "withdrawing-account")

    def test_a_burn_is_never_claimed_twice(self):
        result = map_records("wildcat-v2", *batch_records("wildcat-v2", [[("burn", 40), ("payment", 100, 40, 40),
                                                                           ("payment", 200, 40, 40)]]))
        payments = rows(result, "withdrawal-batch-payment")
        self.assertIsNotNone(mapping_for(result, payments[0])["join"])
        self.assertIsNone(mapping_for(result, payments[1])["join"])
        self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
        companions = [m["join"]["companion_selector"] for m in result["mapping_records"] if m["join"]]
        self.assertEqual(len(companions), 2)
        self.assertEqual(len(set(companions)), 1)
        self.assertEqual(len(burn_rows(result)[0]["provenance"]["supporting_selectors"]), 2)

    def test_burn_from_another_market_a_lender_or_a_wrapper_does_not_join(self):
        contexts, _ = batch_records("wildcat-v2", [], SECOND_MARKET)
        other = step_log(("burn", 40), 0, SECOND_MARKET)
        payment = step_log(("payment", 100, 40, 40), 1)
        result = map_records("wildcat-v2", contexts, [record(other), record(payment)])
        self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
        self.assertEqual(result["unsupported_counts"][UNCLAIMED_GAP], 1)
        self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))
        contexts, _ = constructed_inputs("wildcat-v2")
        lender = log(TRANSFER, (ACCOUNT, ZERO), (40,), index=0)
        result = map_records("wildcat-v2", contexts, [record(lender), record(payment)])
        self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
        self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])
        self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))
        result = map_records("wildcat-v2", *wrapper_burn_then_payment())
        self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
        self.assertNotIn(UNCLAIMED_GAP, result["unsupported_counts"])
        self.assertEqual(row(result, "wrapper-transfer")["parties"][1]["address"], ZERO)
        self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))

    def test_adjacent_block_index_in_another_transaction_does_not_join(self):
        for venue in VENUES:
            result = map_records(venue, *batch_records(venue, [[("burn", 40)], [("payment", 100, 40, 40)]]))
            burn, payment = burn_rows(result)[0], row(result, "withdrawal-batch-payment")
            self.assertEqual((burn["transaction"]["log_index"], payment["transaction"]["log_index"]), (0, 1))
            self.assertNotEqual(burn["transaction"]["hash"], payment["transaction"]["hash"])
            self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
            self.assertEqual(result["unsupported_counts"][UNCLAIMED_GAP], 1)
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))

    def test_payment_at_log_index_zero_has_no_predecessor(self):
        for venue in VENUES:
            result = map_records(venue, *batch_records(venue, [[("payment", 100, 40, 40)]]))
            self.assertEqual(row(result, "withdrawal-batch-payment")["transaction"]["log_index"], 0)
            self.assertEqual(result["unsupported_counts"][BURN_GAP], 1)
            self.assertTrue(all(m["join"] is None for m in result["mapping_records"]))

    def test_join_is_independent_of_record_order(self):
        for venue in VENUES:
            contexts, records = specimen(venue, "repay-two-unpaid-equal-amounts")
            forward = map_records(venue, contexts, records)
            backward = map_records(venue, contexts, list(reversed(records)))
            self.assertEqual(forward, backward)

    def test_coverage_counts_burn_and_unclaimed_burn_gaps_per_release(self):
        transactions = [HOSTILE_SPECIMENS["payment-without-burn"], HOSTILE_SPECIMENS["burn-without-payment"],
                        SOURCE_SPECIMENS["expired-paid-closed"], HOSTILE_SPECIMENS["burn-value-changed"]]
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                target = batch_release(Path(temporary).resolve(), venue, transactions)
                coverage = json.loads((target / "coverage.json").read_bytes())
                unsupported = coverage["coverage"]["unsupported_events"]
                self.assertEqual(unsupported[BURN_GAP], 2)
                self.assertEqual(unsupported[UNCLAIMED_GAP], 2)
                self.assertEqual(coverage["coverage"]["included_events"]["withdrawal-batch-payment"], 3)
                self.assertFalse([key for key in unsupported if key.startswith("canonical:")])
                self.assertEqual([r for r in coverage["versions"]["mapping_rules"] if "batch" in r],
                                 sorted(venue + "." + action + ".v1" for action in
                                        ("withdrawal-batch-closed", "withdrawal-batch-expired", "withdrawal-batch-payment")))
                self.assertEqual(verifier.verify(target / "coverage.json").rows,
                                 sum(coverage["coverage"]["included_events"].values()))

    def test_malformed_batch_logs_refuse(self):
        contexts, _ = constructed_inputs("wildcat-v2")
        mutations = (
            lambda r: r.update(data="0x" + word(40)),                       # payment with one data word
            lambda r: r.update(data=r["data"] + word(9)),                  # payment with a trailing word
            lambda r: r["topics"].append("0x" + word(7)),                  # payment with an extra topic
            lambda r: r["topics"].pop(),                                   # payment without its expiry topic
            lambda r: r.update(data="0x" + "zz" * 64),                    # non-hex payment data
        )
        for mutate in mutations:
            raw = step_log(("payment", 100, 40, 40), 0)
            mutate(raw)
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [record(raw)])
        for raw in (log(CREATED, (100,), (1,), index=0), log(CLOSED, (), (), index=0),
                    log(EXPIRED, (100,), (70, 35), index=0), log(EXPIRED, (100, 1), (70, 35, 40), index=0)):
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [record(raw)])

    def test_only_created_closed_and_market_closed_admit_empty_amounts(self):
        events = all_primary_events()
        self.assertEqual(len(events), 29)
        for event in events:
            action = event["action"].split(".", 1)[1]
            empty = deepcopy(event)
            empty["amounts"] = []
            if action in EMPTY_AMOUNT_ACTIONS:
                validate_row(empty, event["venue"], 3)
            else:
                with self.assertRaisesRegex(TabulariumError, "amounts", msg=action):
                    validate_row(empty, event["venue"], 3)

    def test_all_eight_batch_rules_exist_in_the_twenty_nine_rule_set(self):
        self.assertEqual(len(RULES), 29)
        for venue in VENUES:
            for action in BATCH_ACTIONS:
                rule = RULES[(venue, action)]
                self.assertEqual(rule["rule"], "%s.%s.v1" % (venue, action))
                self.assertEqual((rule["role"], rule["family"], rule["party_roles"]), ("market", "exit-queue", ("pool",)))
                self.assertEqual(rule["instrument_type"], venue + "-market")
        self.assertEqual(RULES[("wildcat-v2", "withdrawal-batch-payment")]["amount_kinds"],
                         ("burned-scaled-claims", "reserved-assets"))
        self.assertEqual(RULES[("wildcat-v1", "withdrawal-batch-expired")]["amount_kinds"],
                         ("scaled-claims", "burned-scaled-claims", "reserved-assets"))
        self.assertEqual(RULES[("wildcat-v1", "withdrawal-batch-created")]["amount_kinds"], ())
        self.assertEqual(RULES[("wildcat-v2", "withdrawal-batch-closed")]["amount_kinds"], ())
        self.assertEqual({r["signature"] for k, r in RULES.items() if k[1] in BATCH_ACTIONS}, set(BATCH_SIGNATURES))

    def test_batch_release_builds_verifies_and_moves(self):
        transactions = [SOURCE_SPECIMENS["repay-two-unpaid-equal-amounts"], SOURCE_SPECIMENS["v2-close-market"]]
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                base = Path(temporary).resolve()
                target = batch_release(base, venue, transactions)
                report = verifier.verify(target / "coverage.json")
                self.assertEqual(report.rows, 12)
                shutil.rmtree(base / "raw")
                moved = base / "moved"
                shutil.move(str(target), str(moved))
                self.assertEqual(verifier.verify(moved / "coverage.json").rows, 12)
                source = json.loads((moved / "source.json").read_bytes())
                joins = [m["join"] for m in source["mapping_records"] if m["join"]]
                self.assertEqual(len(joins), 6)
                self.assertEqual({j["rule"] for j in joins}, {BURN_JOIN_RULE})

    def test_verify_refuses_edited_batch_events_selectors_join_records_and_coverage(self):
        transactions = [SOURCE_SPECIMENS["expired-paid-closed"], HOSTILE_SPECIMENS["burn-without-payment"]]

        def edit_events(rows_, coverage):
            payment = next(r for r in rows_ if r["action"].endswith(".withdrawal-batch-payment"))
            payment["amounts"][1]["base_units"] = "26"

        def edit_selectors(rows_, coverage):
            payment = next(r for r in rows_ if r["action"].endswith(".withdrawal-batch-payment"))
            payment["provenance"]["supporting_selectors"].pop()

        def edit_join(source, coverage):
            join = next(m for m in source["mapping_records"] if m["join"])
            join["join"]["rule"] = "unique-value-burn"

        def edit_join_companion(source, coverage):
            join = next(m for m in source["mapping_records"] if m["join"])
            join["join"]["companion_selector"] = "wildcat-journal:" + "cd" * 32

        def edit_coverage(source, coverage):
            del coverage["coverage"]["unsupported_events"][UNCLAIMED_GAP]

        def edit_coverage_included(source, coverage):
            coverage["coverage"]["included_events"]["withdrawal-batch-payment"] += 1

        for name, edit in (("events.jsonl", edit_events), ("events.jsonl", edit_selectors),
                           ("source.json", edit_join), ("source.json", edit_join_companion),
                           ("coverage.json", edit_coverage), ("coverage.json", edit_coverage_included)):
            with self.subTest(edit=edit.__name__), tempfile.TemporaryDirectory() as temporary:
                target = batch_release(Path(temporary).resolve(), "wildcat-v2", transactions)
                coverage_path = target / "coverage.json"
                coverage = json.loads(coverage_path.read_bytes())
                path = target / name
                if name == "events.jsonl":
                    rows_ = [json.loads(line) for line in path.read_text().splitlines()]
                    edit(rows_, coverage)
                    data = b"".join(canonical_json(r) + b"\n" for r in rows_)
                    coverage["canonical"].update(sha256=sha256_bytes(data), bytes=len(data))
                    path.write_bytes(data)
                elif name == "source.json":
                    source = json.loads(path.read_bytes())
                    edit(source, coverage)
                    data = canonical_json(source) + b"\n"
                    coverage["source"].update(sha256=sha256_bytes(data), bytes=len(data))
                    path.write_bytes(data)
                else:
                    edit(None, coverage)
                coverage_path.write_bytes(canonical_json(coverage) + b"\n")
                with self.assertRaises(TabulariumError):
                    verifier.verify(coverage_path)

    def test_published_wildcat_specimens_rebuild_byte_identical(self):
        for venue in VENUES:
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                published = support.EXAMPLES / (venue + "-v0")
                expected = json.loads((published / "expected.json").read_bytes())
                rebuilt = Path(temporary).resolve() / "rebuilt"
                rebuilt.mkdir()
                self.assertEqual(build_pair(rebuilt, venue), expected)
                compare_pair(published, rebuilt)
                for root in ("release", "registry-context/release"):
                    coverage = json.loads((published / root / "coverage.json").read_bytes())
                    self.assertFalse([r for r in coverage["versions"]["mapping_rules"] if "batch" in r])
                    self.assertFalse([k for k in coverage["coverage"]["unsupported_events"] if "burn" in k])

    def test_six_aave_and_euler_releases_and_schema_2_rebuild_byte_identical(self):
        for name, digest in SCHEMA_2_DIGESTS.items():
            self.assertEqual(hashlib.sha256((support.SCHEMAS / name).read_bytes()).hexdigest(), digest, name)
        for name in support.SHIPPED_RELEASES:
            with self.subTest(release=name), tempfile.TemporaryDirectory() as temporary:
                source = support.EXAMPLES / name
                destination = Path(temporary).resolve()
                for filename in ("source.json", "capture.json"):
                    (destination / filename).write_bytes((source / filename).read_bytes())
                manifest, rows_ = support.release_documents(name)
                builder.build(destination / "source.json", destination / "capture.json", destination / "events.jsonl",
                              destination / "coverage.json", manifest["release"],
                              adapter=manifest["versions"]["adapter"]["name"], event_schema=manifest["schema_version"])
                self.assertEqual(verifier.verify(destination / "coverage.json").rows, len(rows_))
                for filename in support.RELEASE_DATA_FILES:
                    self.assertEqual((destination / filename).read_bytes(), (source / filename).read_bytes(), filename)
                for file_name, digest in support.release_published_digests(name).items():
                    self.assertEqual(hashlib.sha256((source / file_name).read_bytes()).hexdigest(), digest, file_name)


if __name__ == "__main__":
    unittest.main()
