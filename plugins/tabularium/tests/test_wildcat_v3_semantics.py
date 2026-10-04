"""Exercise native Wildcat meanings with labelled constructed source contexts."""

from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "scripts"))
from tabularium_lib.core import TabulariumError
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_abi import VARIANTS, abi_variant_for, decode_log
from tabularium_lib.wildcat_rows import context_selector, map_records, selector
from wildcat_v3_fixtures import (
    ACCOUNT, ASSET, DEBTOR, ESCROW, MARKET, OTHER, PAYER, V1_COMMIT, V2_COMMIT,
    WRAPPER, WRAPPER_COMMIT, ZERO, all_primary_events, constructed_inputs, log, record, word,
)
from test_wildcat_v3_release import ReleaseBoundaryCases


def mapped(venue="wildcat-v2", routing=False):
    return map_records(venue, *constructed_inputs(venue, routing))


def row(result, action):
    return next(event for event in result["events"] if event["action"].endswith("." + action))


def encode_abi(definition, index):
    """Independent ABI specimen construction, including canonical string tails."""
    abi = definition["abi"]
    signature = abi["name"] + "(" + ",".join(p["type"] for p in abi["inputs"]) + ")"
    indexed = []
    plain = []
    expected = {}
    for parameter in abi["inputs"]:
        kind = parameter["type"]
        if kind == "address":
            value, encoded = ACCOUNT, word(ACCOUNT)
        elif kind == "bool":
            value, encoded = True, word(1)
        elif kind == "string":
            value, encoded = "constructed", None
        else:
            value, encoded = "17", word(17)
        expected[parameter["name"]] = value
        if parameter["indexed"]:
            indexed.append("0x" + encoded)
        else:
            plain.append((kind, encoded))
    tails = b""
    heads = []
    for kind, encoded in plain:
        if kind == "string":
            heads.append(word(len(plain) * 32 + len(tails)))
            text = b"constructed"
            tails += len(text).to_bytes(32, "big") + text + b"\0" * (32 - len(text))
        else:
            heads.append(encoded)
    raw = log(signature, index=index)
    raw["topics"].extend(indexed)
    raw["data"] = "0x" + "".join(heads) + tails.hex()
    return raw, expected


class SemanticConformanceTests(ReleaseBoundaryCases, unittest.TestCase):
    def test_all_seventeen_contexts_map_with_complete_native_records(self):
        actual = all_primary_events()
        self.assertEqual(len(actual), 17)
        self.assertEqual(Counter(r["venue"] for r in actual), {"wildcat-v1": 7, "wildcat-v2": 10})
        for venue in ("wildcat-v1", "wildcat-v2"):
            contexts, records = constructed_inputs(venue)
            result = map_records(venue, contexts, records)
            self.assertEqual(len(result["dispositions"]), len(records))
            self.assertEqual({r["disposition"] for r in result["dispositions"]}, {"primary"})
            native = {selector(ref): raw for raw, ref in records}
            for event in result["events"]:
                self.assertEqual(event["native_record"], native[event["provenance"]["source_selector"]])
                self.assertEqual(event["instrument"]["id"], event["native_record"]["address"])

    def test_deposit_assets_and_scaled_claims_are_distinct(self):
        event = row(mapped(), "deposit")
        self.assertEqual(event["parties"], [{"role": "depositor", "address": ACCOUNT},
                                            {"role": "minted-token-account", "address": ACCOUNT}])
        self.assertEqual(event["amounts"], [{"kind": "assets", "base_units": "100", "asset": ASSET},
                                            {"kind": "scaled-claims", "base_units": "90", "asset": None}])

    def test_queue_is_claims_without_a_cash_payment(self):
        event = row(mapped(), "withdrawal-queued")
        self.assertEqual(event["parties"], [{"role": "withdrawing-account", "address": ACCOUNT}])
        self.assertEqual(event["amounts"], [{"kind": "normalized-claims", "base_units": "80", "asset": MARKET},
                                            {"kind": "scaled-claims", "base_units": "70", "asset": None}])
        self.assertNotIn("assets", [amount["kind"] for amount in event["amounts"]])

    def test_execution_account_is_beneficiary_and_executor_stays_unknown(self):
        result = mapped()
        event = row(result, "withdrawal-executed")
        self.assertEqual(event["parties"], [{"role": "beneficiary", "address": ACCOUNT}])
        self.assertEqual(event["amounts"], [{"kind": "assets", "base_units": "50", "asset": ASSET}])
        self.assertEqual(result["unsupported_counts"]["attribution:withdrawal-executed:executor"], 1)
        self.assertEqual(result["unsupported_counts"]["attribution:withdrawal-executed:recipient"], 1)

    def test_amount_only_borrow_does_not_promote_contextual_debtor(self):
        result = mapped()
        event = row(result, "borrow")
        self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
        self.assertEqual(event["amounts"], [{"kind": "assets", "base_units": "75", "asset": ASSET}])
        self.assertNotIn(DEBTOR, [party["address"] for party in event["parties"]])
        evidence = next(item for item in result["mapping_records"] if item["signature"] == "Borrow(uint256)")
        self.assertEqual(evidence["context"]["borrower_context"], {"borrower": DEBTOR, "class": "registry-inferred"})
        self.assertEqual(result["unsupported_counts"]["attribution:borrow:borrower"], 1)

    def test_repayment_payer_remains_separate_from_debtor(self):
        event = row(mapped(), "debt-repaid")
        self.assertEqual(event["parties"], [{"role": "payer", "address": PAYER}, {"role": "pool", "address": MARKET}])
        self.assertNotEqual(PAYER, DEBTOR)
        self.assertEqual(event["amounts"][0]["base_units"], "25")

    def test_only_market_closure_has_empty_amounts_and_timestamp_remains_state(self):
        for venue in ("wildcat-v1", "wildcat-v2"):
            result = mapped(venue)
            event = row(result, "market-closed")
            self.assertEqual(event["amounts"], [])
            self.assertEqual(event["parties"], [{"role": "pool", "address": MARKET}])
            self.assertIsNone(event["transaction"]["timestamp"])
            evidence = next(item for item in result["mapping_records"] if item["signature"] == "MarketClosed(uint256)")
            self.assertEqual(evidence["decoded"], {"timestamp": "1730000000"})
            self.assertTrue(all(r["amounts"] for r in result["events"] if r is not event))

    def test_wrapper_deposit_uses_market_token_assets_and_wrapper_shares(self):
        event = row(mapped(), "wrapper-deposit")
        self.assertEqual(event["parties"], [{"role": "caller", "address": PAYER}, {"role": "owner", "address": ACCOUNT}])
        self.assertEqual(event["instrument"], {"type": "wildcat-v2-wrapper", "id": WRAPPER})
        self.assertEqual(event["amounts"], [{"kind": "market-token-assets", "base_units": "100", "asset": MARKET},
                                            {"kind": "wrapper-shares", "base_units": "80", "asset": WRAPPER}])
        self.assertNotIn(ASSET, [a["asset"] for a in event["amounts"]])

    def test_wrapper_withdrawal_preserves_three_native_parties(self):
        event = row(mapped(), "wrapper-withdrawal")
        self.assertEqual(event["parties"], [{"role": "caller", "address": PAYER},
                                            {"role": "receiver", "address": OTHER}, {"role": "owner", "address": ACCOUNT}])
        self.assertEqual(event["amounts"], [{"kind": "market-token-assets", "base_units": "60", "asset": MARKET},
                                            {"kind": "wrapper-shares", "base_units": "45", "asset": WRAPPER}])

    def test_same_transfer_topic_preserves_market_and_wrapper_instruments(self):
        result = mapped()
        market = row(result, "transfer")
        wrapper = row(result, "wrapper-transfer")
        self.assertEqual(market["native_record"]["topics"][0], wrapper["native_record"]["topics"][0])
        self.assertEqual(market["amounts"][0], {"kind": "market-token-claims", "base_units": "30", "asset": MARKET})
        self.assertEqual(wrapper["amounts"][0], {"kind": "wrapper-shares", "base_units": "5", "asset": WRAPPER})

    def test_mint_queue_and_burn_keep_zero_and_market_endpoints(self):
        contexts, _ = constructed_inputs()
        for index, endpoints in enumerate(((ZERO, ACCOUNT), (ACCOUNT, MARKET), (MARKET, ZERO))):
            raw = log("Transfer(address,address,uint256)", endpoints, (17,), index=index)
            result = map_records("wildcat-v2", contexts, [record(raw)])
            event = result["events"][0]
            self.assertEqual([p["address"] for p in event["parties"]], list(endpoints))
            self.assertEqual(event["action"], "wildcat-v2.transfer")
            self.assertEqual(result["included_counts"], {"transfer": 1})

    def test_unique_sanctions_join_keeps_beneficiary_escrow_and_both_selectors(self):
        contexts, records = constructed_inputs(routing=True)
        result = map_records("wildcat-v2", contexts, records)
        event = row(result, "withdrawal-executed")
        self.assertEqual(event["parties"], [{"role": "beneficiary", "address": ACCOUNT},
                                            {"role": "escrow-recipient", "address": ESCROW}])
        companion_selector = selector(records[-1][1])
        self.assertIn(companion_selector, event["provenance"]["supporting_selectors"])
        self.assertEqual(len(result["events"]), 10)
        self.assertEqual(Counter(d["disposition"] for d in result["dispositions"]), {"primary": 10, "supporting-routing": 1})
        self.assertNotIn("attribution:withdrawal-executed:recipient", result["unsupported_counts"])
        evidence = next(r for r in result["mapping_records"] if r["join"])
        self.assertEqual(evidence["join"]["evidence_class"], "join-inference")
        self.assertEqual(evidence["join"]["primary_selector"], event["provenance"]["source_selector"])
        self.assertEqual(evidence["join"]["companion_selector"], companion_selector)
        self.assertEqual(evidence["join"]["conditions"]["amount"], "50")

    def test_duplicate_routing_companions_leave_recipient_unknown(self):
        contexts, records = constructed_inputs(routing=True)
        duplicate = deepcopy(records[-1][0])
        duplicate["logIndex"] = "0xb"
        records.append(record(duplicate))
        result = map_records("wildcat-v2", contexts, records)
        self.assertEqual(row(result, "withdrawal-executed")["parties"], [{"role": "beneficiary", "address": ACCOUNT}])
        self.assertEqual(result["unsupported_counts"]["attribution:withdrawal-executed:recipient"], 1)
        self.assertEqual(Counter(d["disposition"] for d in result["dispositions"])["supporting-routing"], 2)
        self.assertTrue(all(r["join"] is None for r in result["mapping_records"]))

    def test_duplicate_execution_candidates_are_an_ambiguous_join(self):
        contexts, records = constructed_inputs(routing=True)
        duplicate = deepcopy(records[2][0])
        duplicate["logIndex"] = "0xb"
        records.append(record(duplicate))
        result = map_records("wildcat-v2", contexts, records)
        executions = [r for r in result["events"] if r["action"].endswith("withdrawal-executed")]
        self.assertEqual(len(executions), 2)
        self.assertTrue(all(len(r["parties"]) == 1 for r in executions))

    def test_routing_key_requires_account_expiry_amount_transaction_and_market(self):
        for field in ("account", "expiry", "amount", "transaction", "market"):
            with self.subTest(field=field):
                contexts, records = constructed_inputs(routing=True)
                raw = deepcopy(records[-1][0])
                if field == "account":
                    raw["topics"][1] = "0x" + word(OTHER)
                elif field == "expiry":
                    raw["data"] = "0x" + word(ESCROW) + word(124) + word(50)
                elif field == "amount":
                    raw["data"] = "0x" + word(ESCROW) + word(123) + word(51)
                elif field == "transaction":
                    raw["transactionHash"] = "0x" + "cc" * 32
                    raw["transactionIndex"] = "0x3"
                else:
                    second_market = "0x" + "99" * 20
                    contexts[second_market] = deepcopy(contexts[MARKET])
                    raw["address"] = second_market
                records[-1] = record(raw)
                result = map_records("wildcat-v2", contexts, records)
                self.assertEqual(len(row(result, "withdrawal-executed")["parties"]), 1)

    def test_primary_supporting_canonical_and_decode_dispositions_partition_logs(self):
        contexts, records = constructed_inputs(routing=True)
        records.append(record(log("Approval(address,address,uint256)", (ACCOUNT, OTHER), (42,), index=11)))
        records.append(record(log("UnreleasedEvent(uint256)", (), (19,), index=12)))
        result = map_records("wildcat-v2", contexts, records)
        self.assertEqual(Counter(d["disposition"] for d in result["dispositions"]),
                         {"primary": 10, "supporting-routing": 1, "unsupported-canonical-meaning": 1, "unsupported-decode": 1})
        self.assertEqual(result["unsupported_counts"]["canonical:market:Approval(address,address,uint256)"], 1)
        decode_key = "decode:market:" + records[-1][0]["topics"][0]
        self.assertEqual(result["unsupported_counts"][decode_key], 1)
        self.assertEqual(sum(result["included_counts"].values()), 10)
        self.assertGreater(sum(result["unsupported_counts"].values()), 2)

    def test_unknown_registered_role_does_not_dispatch_by_topic(self):
        contexts, _ = constructed_inputs()
        contexts[MARKET].update(role="unrecognised-role", abi_variant=None, concrete_contract=None)
        result = map_records("wildcat-v2", contexts, [record(log("Borrow(uint256)", (), (17,)))])
        self.assertEqual(result["events"], ())
        self.assertEqual(result["dispositions"][0]["disposition"], "unsupported-decode")

    def test_unreleased_indexed_borrower_signature_is_not_accepted(self):
        contexts, _ = constructed_inputs()
        raw = log("Borrow(address,uint256)", (DEBTOR,), (75,))
        result = map_records("wildcat-v2", contexts, [record(raw)])
        self.assertEqual(result["events"], ())
        self.assertEqual(result["dispositions"][0]["disposition"], "unsupported-decode")

    def test_generation_role_concrete_contract_and_wrapper_binding_refuse(self):
        for field, value in (("role", "factory"), ("concrete_contract", "IWildcatMarket"),
                             ("abi_variant", abi_variant_for("wildcat-v1", "market", "WildcatMarket", V1_COMMIT))):
            with self.subTest(field=field):
                contexts, records = constructed_inputs()
                contexts[MARKET][field] = value
                with self.assertRaises(TabulariumError):
                    map_records("wildcat-v2", contexts, records)
        contexts, records = constructed_inputs()
        contexts[WRAPPER]["asset"] = ASSET
        with self.assertRaises(TabulariumError):
            map_records("wildcat-v2", contexts, records)

    def test_concrete_source_variant_selection_precedes_topic_dispatch(self):
        normal = abi_variant_for("wildcat-v2", "hooks-instance", "FixedTermHooks instance: test", V2_COMMIT)
        longer = abi_variant_for("wildcat-v2", "hooks-instance", "FixedTermHooks instance: test", "5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa")
        self.assertIsNotNone(normal)
        self.assertIsNotNone(longer)
        self.assertNotEqual(normal, longer)
        self.assertIsNone(abi_variant_for("wildcat-v2", "market", "WildcatMarket", WRAPPER_COMMIT))
        self.assertIsNone(abi_variant_for("wildcat-v1", "wrapper", "Wildcat4626Wrapper", WRAPPER_COMMIT))

    def test_known_supported_topic_wrong_arity_padding_and_nonhex_are_fatal(self):
        mutations = [lambda r: r["topics"].append("0x" + word(ACCOUNT)),
                     lambda r: r.update(data="0x" + word(100)),
                     lambda r: r.update(data=r["data"] + word(9)),
                     lambda r: r["topics"].__setitem__(1, "0x" + word((1 << 200) + int(ACCOUNT, 16))),
                     lambda r: r.update(data="0x" + "z" * 128)]
        for mutate in mutations:
            contexts, records = constructed_inputs()
            raw = deepcopy(records[0][0])
            mutate(raw)
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [record(raw)])

    def test_routing_uint32_and_administrative_bool_widths_are_strict(self):
        contexts, _ = constructed_inputs()
        for raw in (log("SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)",
                        (ACCOUNT,), (ESCROW, 1 << 32, 50)),
                    log("StateUpdated(uint256,bool)", (), (17, 2))):
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [record(raw)])

    def test_all_catalogued_abi_shapes_decode_and_match_topics(self):
        tested = 0
        for variant_id, variant in VARIANTS.items():
            for topic, definition in variant["events"].items():
                with self.subTest(variant=variant_id, signature=definition["signature"]):
                    raw, expected = encode_abi(definition, tested)
                    self.assertEqual(raw["topics"][0], topic)
                    actual_definition, values = decode_log(variant_id, raw)
                    self.assertEqual(actual_definition["signature"], definition["signature"])
                    self.assertEqual(values, expected)
                    tested += 1
        self.assertEqual(tested, 156)

    def test_declared_unsigned_widths_and_address_padding_refuse_independently(self):
        checked = set()
        for variant_id, variant in VARIANTS.items():
            for definition in variant["events"].values():
                for position, parameter in enumerate(definition["abi"]["inputs"]):
                    kind = parameter["type"]
                    if kind in checked or not kind.startswith("uint") or kind == "uint256":
                        continue
                    raw, _ = encode_abi(definition, 0)
                    invalid = word(1 << int(kind[4:]))
                    if parameter["indexed"]:
                        topic_position = 1 + sum(p["indexed"] for p in definition["abi"]["inputs"][:position])
                        raw["topics"][topic_position] = "0x" + invalid
                    else:
                        data_position = sum(not p["indexed"] for p in definition["abi"]["inputs"][:position])
                        start = 2 + data_position * 64
                        raw["data"] = raw["data"][:start] + invalid + raw["data"][start + 64:]
                    with self.assertRaises(TabulariumError):
                        decode_log(variant_id, raw)
                    checked.add(kind)
        self.assertEqual(checked, {"uint8", "uint16", "uint24", "uint32", "uint80", "uint128"})

    def test_dynamic_administrative_offsets_tail_padding_utf8_and_budget_refuse(self):
        variant_id, definition = next((ident, e) for ident, v in VARIANTS.items()
                                      for e in v["events"].values() if e["signature"].startswith("MarketDeployed("))
        original, _ = encode_abi(definition, 0)
        for mutation in ("offset", "padding", "utf8", "budget", "trailing"):
            raw = deepcopy(original)
            data = bytearray.fromhex(raw["data"][2:])
            plain = [p for p in definition["abi"]["inputs"] if not p["indexed"]]
            string_head = next(i for i, p in enumerate(plain) if p["type"] == "string")
            start = int.from_bytes(data[string_head * 32:(string_head + 1) * 32], "big")
            if mutation == "offset":
                data[string_head * 32:(string_head + 1) * 32] = (start + 32).to_bytes(32, "big")
            elif mutation == "padding":
                data[start + 32 + len(b"constructed")] = 1
            elif mutation == "utf8":
                data[start + 32] = 255
            elif mutation == "budget":
                data[start:start + 32] = (513).to_bytes(32, "big")
            else:
                data.extend(b"\0" * 32)
            raw["data"] = "0x" + data.hex()
            with self.assertRaises(TabulariumError):
                decode_log(variant_id, raw)

    def test_uint256_precision_is_preserved_without_float_or_safe_integer_coercion(self):
        contexts, _ = constructed_inputs()
        value = (1 << 256) - 1
        result = map_records("wildcat-v2", contexts, [record(log("Borrow(uint256)", (), (value,)))])
        self.assertEqual(result["events"][0]["amounts"][0]["base_units"], str(value))

    def test_missing_asset_is_null_with_a_qualified_attribution_gap(self):
        contexts, records = constructed_inputs()
        contexts[MARKET]["asset"] = None
        result = map_records("wildcat-v2", contexts, records[:7])
        self.assertIsNone(row(result, "borrow")["amounts"][0]["asset"])
        self.assertEqual(result["unsupported_counts"]["attribution:borrow:asset"], 1)
        self.assertEqual(row(result, "transfer")["amounts"][0]["asset"], MARKET)

    def test_selectors_bind_complete_nested_source_and_classes(self):
        contexts, records = constructed_inputs()
        reference = records[0][1]
        primary = selector(reference)
        altered = deepcopy(reference)
        altered["selector"] = "/result/1"
        self.assertNotEqual(primary, selector(altered))
        altered = deepcopy(reference)
        altered["response_sha256"] = "sha256:" + "d" * 64
        self.assertNotEqual(primary, selector(altered))
        context = contexts[MARKET]["source"][0]
        self.assertTrue(context_selector(context).startswith("wildcat-context:"))
        result = map_records("wildcat-v2", contexts, records)
        self.assertEqual(result["mapping_records"][0]["reference"], reference)
        self.assertNotIn("source", result["mapping_records"][0]["context"])

    def test_selector_shape_and_evidence_class_strengthening_are_refused(self):
        _, records = constructed_inputs()
        for key, value in (("selector", "/logs/0"), ("journal_selector", "/records/0"),
                           ("evidence_class", "proved"), ("component_sha256", "sha256:bad")):
            reference = deepcopy(records[0][1])
            reference[key] = value
            with self.assertRaises(TabulariumError):
                selector(reference)
        with self.assertRaises(TabulariumError):
            context_selector({"class": "proved", "fixture": "unsupported-upgrade"})

    def test_repeated_log_identity_or_reference_is_fatal(self):
        contexts, records = constructed_inputs()
        for entries in ([records[0], records[0]], [(records[0][0], records[0][1]), (records[1][0], records[0][1])]):
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, entries)

    def test_conflicting_block_and_transaction_metadata_are_fatal(self):
        for field, value in (("blockHash", "0x" + "dd" * 32), ("blockNumber", "0x65"), ("transactionIndex", "0x3")):
            contexts, records = constructed_inputs()
            raw = deepcopy(records[1][0])
            raw[field] = value
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [records[0], record(raw)])

    def test_reverse_block_number_transaction_position_and_block_log_uniqueness(self):
        for contradiction in ("block-number", "transaction-position", "block-log-position"):
            with self.subTest(contradiction=contradiction):
                contexts, records = constructed_inputs()
                raw = deepcopy(records[1][0])
                raw["transactionHash"] = "0x" + "cc" * 32
                if contradiction == "block-number":
                    raw["blockNumber"] = "0x65"
                    raw["transactionIndex"] = "0x3"
                elif contradiction == "block-log-position":
                    raw["transactionIndex"] = "0x3"
                    raw["logIndex"] = "0x0"
                with self.assertRaises(TabulariumError):
                    map_records("wildcat-v2", contexts, [records[0], record(raw)])

    def test_distinct_transactions_and_blocks_keep_valid_native_positions(self):
        contexts, records = constructed_inputs()
        second = deepcopy(records[1][0])
        second.update(transactionHash="0x" + "cc" * 32, transactionIndex="0x3")
        third = deepcopy(records[0][0])
        third.update(transactionHash="0x" + "dd" * 32, blockHash="0x" + "ee" * 32,
                     blockNumber="0x65", transactionIndex="0x0")
        result = map_records("wildcat-v2", contexts, [records[0], record(second), record(third)])
        self.assertEqual(len(result["events"]), 3)

    def test_raw_quantity_types_removed_flag_and_bounds_are_fatal(self):
        for field, value in (("blockNumber", True), ("transactionIndex", "0x-1"),
                             ("logIndex", "0x00"), ("removed", True), ("blockNumber", hex(1 << 54))):
            contexts, records = constructed_inputs()
            raw = deepcopy(records[0][0])
            raw[field] = value
            with self.assertRaises(TabulariumError):
                map_records("wildcat-v2", contexts, [record(raw, 0)])

    def test_mapping_retains_original_records_without_mutating_source(self):
        contexts, records = constructed_inputs()
        before = deepcopy((contexts, records))
        result = map_records("wildcat-v2", contexts, records)
        self.assertEqual((contexts, records), before)
        records[0][0]["data"] = "0x"
        self.assertEqual(result["events"][0]["native_record"], before[1][0][0])

    def test_native_order_is_deterministic_and_unsupported_logs_remain_preserved(self):
        contexts, records = constructed_inputs()
        records.append(record(log("StateUpdated(uint256,bool)", (), (17, 1), index=10)))
        forward = map_records("wildcat-v2", contexts, records)
        backward = map_records("wildcat-v2", contexts, list(reversed(records)))
        self.assertEqual(forward, backward)
        self.assertEqual(forward["mapping_records"][-1]["decoded"], {"scaleFactor": "17", "isDelinquent": True})
        self.assertEqual(forward["mapping_records"][-1]["native_record"], records[-1][0])


if __name__ == "__main__":
    unittest.main()
