"""Receipt witnesses prove consensus bytes without promoting RPC decorations."""

import copy
from pathlib import Path
import socket
import unittest
from unittest import mock

from eth_hash.auto import keccak
from trie import HexaryTrie

from lazarus_lib.canonical import load
from lazarus_lib.errors import FormatError, IntegrityError, ResourceLimitError
from lazarus_lib.hexvalue import address_bytes, encode_hex
from lazarus_lib.manifest import build_manifest
from lazarus_lib.receipts import (
    _filtered_projection,
    _matches_filter,
    encode_receipt,
    receipt_trie_root,
    verify_receipt_relation,
)
from lazarus_lib.rlp import encode as rlp_encode
from lazarus_lib.records import loads_rpc_records, request_key
from lazarus_lib.rlp import encode_uint
from lazarus_lib.trieproof import EMPTY_TRIE_ROOT, trie_root
from lazarus_lib.verifier import verify_fixture

from . import support


FIXTURE = support.FIXTURES / "receipt-proof-v1"
FIXED_ROOT = "0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e"
SMALL_ROOT = "0x19d164adced738c05eb7a37ae987233ccd63f4a3f754042b27a13a929050278b"


def verify_material(material):
    return verify_receipt_relation(
        material["receipt_witness"],
        header=material["header"],
        plan=material["plan"],
        rpc_records=material["rpc_records"],
    )


def named_record(material, name):
    return next(record for record in material["rpc_records"] if record["name"] == name)


def fixed_material():
    return {
        "plan": load(FIXTURE / "plan.json"),
        "header": load(FIXTURE / "header.json"),
        "receipt_witness": load(FIXTURE / "receipt-witness.json"),
        "rpc_records": loads_rpc_records((FIXTURE / "rpc.jsonl").read_bytes()),
    }


def rewrite_target_hash(material, transaction_hash):
    """Rewrite every recorded target attribution, but no consensus receipt byte."""

    index = int(material["plan"]["receipt_witness"]["target_transaction_index"], 16)
    relation = material["plan"]["receipt_witness"]
    material["header"]["rpc_result"]["transactions"][index] = transaction_hash
    request = next(
        item
        for item in material["plan"]["requests"]
        if item["name"] == relation["target_receipt_lookup_request"]
    )
    request["params"] = [transaction_hash]
    target_record = named_record(material, relation["target_receipt_lookup_request"])
    target_record["params"] = [transaction_hash]
    target_record["request_key"] = request_key(target_record["method"], target_record["params"])

    block_receipts = named_record(
        material, relation["block_receipts_request"]
    )["outcome"]["result"]
    sources = [block_receipts[index], target_record["outcome"]["result"]]
    for receipt in sources:
        receipt["transactionHash"] = transaction_hash
        for log in receipt["logs"]:
            log["transactionHash"] = transaction_hash
    for log in named_record(material, relation["filtered_logs_request"])["outcome"]["result"]:
        if int(log["transactionIndex"], 16) == index:
            log["transactionHash"] = transaction_hash


class ReceiptEncodingTests(unittest.TestCase):
    def test_transaction_indices_use_canonical_rlp_keys(self):
        self.assertEqual(
            [encode_uint(value).hex() for value in (0, 1, 127, 128, 191, 1024)],
            ["80", "01", "7f", "8180", "81bf", "820400"],
        )

    def test_legacy_and_typed_receipts_have_exact_consensus_bytes(self):
        material = support.receipt_fixture_material()
        legacy, typed = material["receipt_witness"]["receipts"]
        self.assertEqual(
            encode_receipt(legacy).hex(),
            "f901060101b90100" + "00" * 256 + "c0",
        )
        self.assertEqual(
            encode_receipt(typed).hex(),
            "02f901430102b90100"
            + "00" * 256
            + "f83cf83a945555555555555555555555555555555555555555e1"
            + "a06666666666666666666666666666666666666666666666666666666666666666"
            + "821234",
        )
        type_one = copy.deepcopy(typed)
        type_one["receipt_type"] = "0x1"
        self.assertEqual(encode_receipt(type_one)[0], 1)

    def test_blob_and_set_code_receipts_reuse_the_typed_payload(self):
        material = support.receipt_fixture_material()
        _, typed = material["receipt_witness"]["receipts"]
        payload = encode_receipt(typed)[1:]
        for receipt_type, prefix in (("0x3", 3), ("0x4", 4)):
            widened = copy.deepcopy(typed)
            widened["receipt_type"] = receipt_type
            encoded = encode_receipt(widened)
            self.assertEqual(encoded[0], prefix)
            self.assertEqual(encoded[1:], payload)

    def test_unallocated_receipt_type_is_still_refused(self):
        material = support.receipt_fixture_material()
        _, typed = material["receipt_witness"]["receipts"]
        widened = copy.deepcopy(typed)
        widened["receipt_type"] = "0x5"
        with self.assertRaisesRegex(FormatError, "unsupported receipt type"):
            encode_receipt(widened)

    def test_pre_byzantium_root_is_legacy_only(self):
        receipt = copy.deepcopy(support.sample_receipt_witness()["receipts"][0])
        receipt.pop("status")
        receipt["root"] = support.hash32("7a")
        self.assertTrue(encode_receipt(receipt).startswith(bytes.fromhex("f90126a0")))
        receipt["receipt_type"] = "0x2"
        with self.assertRaisesRegex(FormatError, "typed receipt"):
            encode_receipt(receipt)

    def test_small_root_is_fixed_and_matches_an_independent_trie(self):
        receipts = support.receipt_fixture_material()["receipt_witness"]["receipts"]
        root = receipt_trie_root(receipts)
        independent = HexaryTrie({})
        for index, receipt in enumerate(receipts):
            independent[encode_uint(index)] = encode_receipt(receipt)
        self.assertEqual(encode_hex(root), SMALL_ROOT)
        self.assertEqual(root, independent.root_hash)

    def test_empty_and_embedded_node_vectors_match_the_independent_trie(self):
        self.assertEqual(trie_root([]), EMPTY_TRIE_ROOT)
        for items in (
            [(b"a", b"b")],
            [(b"a", b"b"), (b"ab", b"c")],
            [(b"\x01", b"x"), (b"\x02", b"y"), (b"\x10", b"z")],
        ):
            with self.subTest(items=items):
                independent = HexaryTrie({})
                for key, value in items:
                    independent[key] = value
                self.assertEqual(trie_root(items), independent.root_hash)

    def test_receipt_and_trie_work_are_bounded(self):
        receipt = support.sample_receipt_witness()["receipts"][0]
        with mock.patch("lazarus_lib.receipts.MAX_RECEIPTS", 1):
            with self.assertRaisesRegex(ResourceLimitError, "receipt count"):
                receipt_trie_root([receipt, receipt])
        hostile = copy.deepcopy(receipt)
        hostile["logs"] = [
            {"address": support.address(), "topics": [], "data": "0x"}
        ]
        with mock.patch("lazarus_lib.receipts.MAX_LOGS", 0):
            with self.assertRaisesRegex(ResourceLimitError, "log count"):
                encode_receipt(hostile)
        with mock.patch("lazarus_lib.receipts.MAX_ENCODED_BLOCK_BYTES", 1):
            with self.assertRaisesRegex(ResourceLimitError, "encoded receipt set"):
                receipt_trie_root([receipt])
        with self.assertRaisesRegex(FormatError, "duplicate keys"):
            trie_root([(b"a", b"x"), (b"a", b"y")])
        with self.assertRaisesRegex(FormatError, "must not be empty"):
            trie_root([(b"a", b"")])

    def test_log_data_limit_is_checked_before_hex_allocation(self):
        receipt = copy.deepcopy(support.sample_receipt_witness()["receipts"][1])

        def guarded_hex(value, *, label="hex value", length=None):
            if label == "receipt log data":
                raise AssertionError("oversized log data reached hex decoding")
            from lazarus_lib.hexvalue import hex_bytes

            return hex_bytes(value, label=label, length=length)

        with mock.patch(
            "lazarus_lib.receipts.MAX_LOG_DATA_BYTES", 1
        ), mock.patch(
            "lazarus_lib.receipts.hex_bytes", side_effect=guarded_hex
        ):
            with self.assertRaisesRegex(ResourceLimitError, "log data"):
                encode_receipt(receipt)

    def test_receipt_size_limit_is_checked_before_full_rlp_allocation(self):
        receipt = copy.deepcopy(support.sample_receipt_witness()["receipts"][1])

        def guarded_encode(value):
            if isinstance(value, list) and len(value) == 4:
                raise AssertionError("oversized receipt reached full RLP allocation")
            return rlp_encode(value)

        with mock.patch(
            "lazarus_lib.receipts.MAX_ENCODED_RECEIPT_BYTES", 1
        ), mock.patch(
            "lazarus_lib.receipts.encode", side_effect=guarded_encode
        ):
            with self.assertRaisesRegex(ResourceLimitError, "encoded receipt"):
                encode_receipt(receipt)


class ReceiptRelationTests(unittest.TestCase):
    def test_small_relation_derives_root_positions_and_safe_evidence(self):
        report = verify_material(support.receipt_fixture_material())
        self.assertEqual(report["expected_root"], SMALL_ROOT)
        self.assertEqual(report["computed_root"], SMALL_ROOT)
        self.assertEqual(report["receipt_count"], 2)
        self.assertEqual(report["target_transaction_index"], "0x1")
        self.assertEqual(report["target_log_count"], 1)
        self.assertEqual(report["filtered_log_count"], 1)
        self.assertEqual(report["relations"], 2)
        self.assertEqual(report["transaction_hash_attribution"], "recorded_rpc")
        self.assertNotIn("transaction_hash", report)

    def test_every_consensus_field_and_order_is_root_bound(self):
        mutations = (
            lambda witness: witness["receipts"][0].__setitem__("status", "0x0"),
            lambda witness: witness["receipts"][0].__setitem__("cumulative_gas_used", "0x2"),
            lambda witness: witness["receipts"][0].__setitem__(
                "logs_bloom", "0x" + "01" + "00" * 255
            ),
            lambda witness: witness["receipts"][1].__setitem__("receipt_type", "0x1"),
            lambda witness: witness["receipts"][1]["logs"][0].__setitem__(
                "address", support.address("77")
            ),
            lambda witness: witness["receipts"][1]["logs"][0][
                "topics"
            ].__setitem__(0, support.hash32("77")),
            lambda witness: witness["receipts"][1]["logs"][0].__setitem__("data", "0x5678"),
            lambda witness: witness["receipts"].reverse(),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                material = support.receipt_fixture_material()
                mutate(material["receipt_witness"])
                with self.assertRaises((FormatError, IntegrityError)):
                    verify_material(material)

    def test_receipt_set_omissions_duplicates_extras_and_absent_target_fail(self):
        cases = (
            lambda witness: witness["receipts"].pop(),
            lambda witness: witness["receipts"].append(copy.deepcopy(witness["receipts"][1])),
            lambda witness: witness["receipts"].append(
                {
                    **copy.deepcopy(witness["receipts"][1]),
                    "transaction_index": "0x2",
                }
            ),
            lambda witness: witness["target_receipt"].__setitem__("transaction_index", "0x2"),
        )
        for mutate in cases:
            material = support.receipt_fixture_material()
            mutate(material["receipt_witness"])
            with self.subTest(mutation=mutate), self.assertRaises((FormatError, IntegrityError)):
                verify_material(material)

    def test_consensus_log_order_is_committed_by_the_fixed_root(self):
        material = fixed_material()
        logs = material["receipt_witness"]["receipts"][0xBF]["logs"]
        logs[0], logs[1] = logs[1], logs[0]
        with self.assertRaisesRegex(IntegrityError, "reconstructed receipt trie root"):
            verify_material(material)

    def test_recorded_receipt_omissions_duplicates_and_extras_fail(self):
        for action in ("omit", "duplicate", "extra"):
            material = support.receipt_fixture_material()
            receipts = named_record(material, "block-receipts")["outcome"]["result"]
            if action == "omit":
                receipts.pop()
            elif action == "duplicate":
                receipts[1] = copy.deepcopy(receipts[0])
            else:
                receipts.append(copy.deepcopy(receipts[-1]))
            with self.subTest(action=action), self.assertRaises(IntegrityError):
                verify_material(material)

    def test_derived_block_and_log_positions_refuse_rpc_decorations(self):
        mutations = (
            (
                "block-receipts",
                lambda result: result[1].__setitem__(
                    "blockHash", support.hash32("99")
                ),
            ),
            ("block-receipts", lambda result: result[1].__setitem__("blockNumber", "0x11")),
            ("block-receipts", lambda result: result[1].__setitem__("transactionIndex", "0x0")),
            ("block-receipts", lambda result: result[1]["logs"][0].__setitem__("logIndex", "0x1")),
            ("block-receipts", lambda result: result[1]["logs"][0].__setitem__("removed", True)),
        )
        for name, mutate in mutations:
            material = support.receipt_fixture_material()
            mutate(named_record(material, name)["outcome"]["result"])
            with self.subTest(mutation=mutate), self.assertRaises(IntegrityError):
                verify_material(material)

    def test_named_target_must_match_the_proved_payload_at_its_index(self):
        material = support.receipt_fixture_material()
        record = named_record(material, "target-receipt")
        record["outcome"]["result"] = copy.deepcopy(record["outcome"]["result"])
        target = record["outcome"]["result"]
        target["cumulativeGasUsed"] = "0x3"
        with self.assertRaisesRegex(
            IntegrityError, "target receipt consensus payload disagrees"
        ):
            verify_material(material)

    def test_filtered_projection_refuses_omission_extra_reorder_and_payload_mutation(self):
        for action in ("omit", "extra", "reorder", "payload", "position"):
            material = fixed_material()
            logs = named_record(material, "goldfinch-block-logs")["outcome"]["result"]
            if action == "omit":
                logs.pop()
            elif action == "extra":
                logs.append(copy.deepcopy(logs[-1]))
            elif action == "reorder":
                logs[0], logs[1] = logs[1], logs[0]
            elif action == "payload":
                logs[0]["data"] = "0x00"
            else:
                logs[0]["logIndex"] = "0x0"
            with self.subTest(action=action), self.assertRaises(IntegrityError):
                verify_material(material)

    def test_address_topic_or_and_wildcard_filters_are_exact(self):
        cases = (
            {"address": [support.address("55"), support.address("77")]},
            {"topics": [None]},
            {"topics": [[support.hash32("66"), support.hash32("77")]]},
        )
        for selected in cases:
            material = support.receipt_fixture_material()
            filter_value = {"blockHash": material["header"]["hash"], **selected}
            material["receipt_witness"]["filtered_logs"]["filter"] = filter_value
            request = next(
                item
                for item in material["plan"]["requests"]
                if item["name"] == "filtered-logs"
            )
            request["params"] = [filter_value]
            self.assertEqual(verify_material(material)["filtered_log_count"], 1)

    def test_topic_wildcard_requires_the_log_position_to_exist(self):
        log = {"address": support.address("55"), "topics": [], "data": "0x"}
        self.assertFalse(_matches_filter(log, {"topics": [None]}))

    def test_filtered_projection_parses_static_filter_values_once(self):
        log = {
            "address": support.address("55"),
            "topics": [support.hash32("66")],
            "data": "0x",
        }
        receipts = [{"logs": [log, log, log]}]
        with mock.patch(
            "lazarus_lib.receipts.address_bytes",
            wraps=address_bytes,
        ) as checked_address:
            projection = _filtered_projection(
                receipts,
                {"address": support.address("55")},
                block_number="0x10",
                block_hash=support.hash32("11"),
            )
        self.assertEqual(len(projection), 3)
        self.assertEqual(checked_address.call_count, 4)

    def test_coherent_hash_rewrite_changes_no_proved_relation(self):
        original = support.receipt_fixture_material()
        expected = verify_material(original)
        rewritten = copy.deepcopy(original)
        rewrite_target_hash(rewritten, support.hash32("aa"))
        self.assertEqual(verify_material(rewritten), expected)

    def test_one_source_hash_mismatch_is_only_a_recorded_rpc_failure(self):
        material = support.receipt_fixture_material()
        material["header"]["rpc_result"]["transactions"][1] = support.hash32("aa")
        with self.assertRaisesRegex(
            IntegrityError, "recorded RPC transaction hash disagreement"
        ) as raised:
            verify_material(material)
        self.assertNotIn("root", str(raised.exception).lower())
        self.assertNotIn("proved", str(raised.exception).lower())


class FixedReceiptFixtureTests(unittest.TestCase):
    def test_fixed_manifest_rebuild_is_byte_for_byte_deterministic(self):
        expected = load(FIXTURE / "manifest.json")
        rebuilt = build_manifest(
            FIXTURE,
            [item["path"] for item in expected["components"]],
            chain_id=expected["chain_id"],
            block_number=expected["block"]["number"],
            block_hash=expected["block"]["hash"],
            evidence_counts=expected["evidence_counts"],
            optional_failures=expected["optional_failures"],
        )
        self.assertEqual(rebuilt, expected)

    def test_fixed_224_receipt_vector_reconstructs_the_captured_root(self):
        witness = load(FIXTURE / "receipt-witness.json")
        receipts = witness["receipts"]
        self.assertEqual(len(receipts), 224)
        self.assertEqual(witness["target_receipt"]["transaction_index"], "0xbf")
        self.assertEqual(len(receipts[0xBF]["logs"]), 110)
        root = receipt_trie_root(receipts)
        self.assertEqual(encode_hex(root), FIXED_ROOT)
        independent = HexaryTrie({})
        for index, receipt in enumerate(receipts):
            independent[encode_uint(index)] = encode_receipt(receipt)
        self.assertEqual(independent.root_hash, root)

    def test_fixed_fixture_verifies_offline_with_stable_scoped_report(self):
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            report = verify_fixture(FIXTURE)
        self.assertEqual(
            report["evidence_counts"],
            {
                "proof_backed": 2,
                "header_bound": 1,
                "recorded_rpc": 5,
                "receipt_trie_proved": 2,
            },
        )
        relation = report["receipt_trie_proved"]
        self.assertEqual(relation["computed_root"], FIXED_ROOT)
        self.assertEqual(relation["receipt_count"], 224)
        self.assertEqual(relation["target_transaction_index"], "0xbf")
        self.assertEqual(relation["target_log_count"], 110)
        self.assertEqual(relation["filtered_log_count"], 5)
        self.assertEqual(relation["transaction_hash_attribution"], "recorded_rpc")


if __name__ == "__main__":
    unittest.main()
