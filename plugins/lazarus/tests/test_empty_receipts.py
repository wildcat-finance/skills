"""Exclusive empty and scoped receipt-witness shapes."""

from __future__ import annotations

import copy
import unittest

from lazarus_lib.errors import FormatError, IntegrityError
from lazarus_lib.header import compute_header_hash
from lazarus_lib.hexvalue import encode_hex
from lazarus_lib.receipts import receipt_trie_root, verify_receipt_relation
from lazarus_lib.records import request_key
from lazarus_lib.schemas import validate_document
from lazarus_lib.trieproof import EMPTY_TRIE_ROOT

from . import support


EMPTY_ROOT = encode_hex(EMPTY_TRIE_ROOT)


def verify_material(material):
    return verify_receipt_relation(
        material["receipt_witness"],
        header=material["header"],
        plan=material["plan"],
        rpc_records=material["rpc_records"],
    )


def empty_material():
    """Return a valid synthetic empty witness with a verified header."""

    material = support.receipt_fixture_material()
    plan = material["plan"]
    relation = plan["receipt_witness"]
    block_name = relation["block_receipts_request"]
    plan["receipt_witness"] = {"block_receipts_request": block_name}
    plan["requests"] = [
        request
        for request in plan["requests"]
        if request["name"] in {"chain-id", block_name}
    ]

    header = material["header"]
    header["rpc_result"]["receiptsRoot"] = EMPTY_ROOT
    header["rpc_result"]["transactions"] = []
    header_hash = encode_hex(compute_header_hash(header))
    header["hash"] = header["rpc_result"]["hash"] = header_hash
    plan["block"]["hash"] = header_hash

    block_request = next(
        request for request in plan["requests"] if request["name"] == block_name
    )
    block_request["params"] = [header_hash]
    material["receipt_witness"] = {
        "schema_version": 1,
        "header": {
            "number": header["number"],
            "hash": header_hash,
            "receipts_root": EMPTY_ROOT,
        },
        "receipts": [],
    }
    material["rpc_records"] = [
        record
        for record in material["rpc_records"]
        if record["name"] in {"chain-id", block_name}
    ]
    block_record = next(
        record for record in material["rpc_records"] if record["name"] == block_name
    )
    block_record["params"] = [header_hash]
    block_record["request_key"] = request_key(block_record["method"], [header_hash])
    block_record["outcome"]["result"] = []
    return material


class ExclusiveShapeTests(unittest.TestCase):
    def test_plan_v3_accepts_only_empty_or_complete_scoped_relation(self):
        scoped = support.sample_plan_v3()
        validate_document("plan", scoped)
        empty = copy.deepcopy(scoped)
        empty["receipt_witness"] = {"block_receipts_request": "block-receipts"}
        validate_document("plan", empty)

        for field in (
            "target_receipt_lookup_request",
            "target_transaction_index",
            "filtered_logs_request",
        ):
            mixed = copy.deepcopy(scoped)
            del mixed["receipt_witness"][field]
            with self.subTest(field=field), self.assertRaisesRegex(
                FormatError, "invalid plan"
            ):
                validate_document("plan", mixed)

    def test_witness_accepts_only_empty_or_complete_scoped_shape(self):
        scoped = support.sample_receipt_witness()
        validate_document("receipt-witness", scoped)
        empty = {
            "schema_version": 1,
            "header": copy.deepcopy(scoped["header"]),
            "receipts": [],
        }
        validate_document("receipt-witness", empty)

        mixed_shapes = []
        for field in ("target_receipt", "filtered_logs"):
            mixed = copy.deepcopy(scoped)
            del mixed[field]
            mixed_shapes.append(mixed)
        mixed = copy.deepcopy(scoped)
        mixed["receipts"] = []
        mixed_shapes.append(mixed)
        for mixed in mixed_shapes:
            with self.subTest(keys=sorted(mixed)), self.assertRaisesRegex(
                FormatError, "invalid receipt-witness"
            ):
                validate_document("receipt-witness", mixed)

    def test_schema_diagnostics_are_bounded_and_do_not_echo_values(self):
        hostile = "do-not-echo-" + "x" * 4096
        plan = support.sample_plan_v3()
        plan["receipt_witness"] = {
            "block_receipts_request": "block-receipts",
            "target_receipt_lookup_request": hostile,
        }
        with self.assertRaises(FormatError) as raised:
            validate_document("plan", plan)
        message = str(raised.exception)
        self.assertLessEqual(len(message), 1200)
        self.assertNotIn(hostile, message)


class EmptyReceiptRelationTests(unittest.TestCase):
    def test_empty_root_and_empty_witness_return_zero_relations(self):
        material = empty_material()
        report = verify_material(material)
        self.assertEqual(receipt_trie_root([]), EMPTY_TRIE_ROOT)
        self.assertEqual(report["mode"], "empty")
        self.assertEqual(report["expected_root"], EMPTY_ROOT)
        self.assertEqual(report["computed_root"], EMPTY_ROOT)
        self.assertEqual(report["receipt_count"], 0)
        self.assertEqual(report["log_count"], 0)
        self.assertEqual(report["relations"], 0)
        self.assertNotIn("target_transaction_index", report)
        self.assertNotIn("filtered_log_count", report)

    def test_nonempty_root_with_empty_witness_is_refused(self):
        material = empty_material()
        nonempty_root = support.hash32("42")
        material["header"]["rpc_result"]["receiptsRoot"] = nonempty_root
        material["receipt_witness"]["header"]["receipts_root"] = nonempty_root
        header_hash = encode_hex(compute_header_hash(material["header"]))
        material["header"]["hash"] = material["header"]["rpc_result"]["hash"] = header_hash
        material["receipt_witness"]["header"]["hash"] = header_hash
        material["plan"]["block"]["hash"] = header_hash
        block_request = material["plan"]["requests"][1]
        block_request["params"] = [header_hash]
        block_record = material["rpc_records"][1]
        block_record["params"] = [header_hash]
        block_record["request_key"] = request_key(block_record["method"], [header_hash])
        with self.assertRaisesRegex(
            IntegrityError, "reconstructed receipt trie root mismatch"
        ):
            verify_material(material)

    def test_plan_and_witness_modes_must_agree(self):
        scoped_witness = support.receipt_fixture_material()
        scoped_witness["plan"]["receipt_witness"] = {
            "block_receipts_request": "block-receipts"
        }
        with self.assertRaisesRegex(IntegrityError, "shapes disagree"):
            verify_material(scoped_witness)

        empty_witness = empty_material()
        plan = empty_witness["plan"]
        plan["requests"].extend(
            [
                {
                    "name": "target-receipt",
                    "method": "eth_getTransactionReceipt",
                    "params": [support.hash32("44")],
                    "required": True,
                    "evidence": "recorded-rpc",
                },
                {
                    "name": "filtered-logs",
                    "method": "eth_getLogs",
                    "params": [{"blockHash": empty_witness["header"]["hash"]}],
                    "required": True,
                    "evidence": "recorded-rpc",
                },
            ]
        )
        plan["receipt_witness"] = {
            "block_receipts_request": "block-receipts",
            "target_receipt_lookup_request": "target-receipt",
            "target_transaction_index": "0x0",
            "filtered_logs_request": "filtered-logs",
        }
        with self.assertRaisesRegex(IntegrityError, "shapes disagree"):
            verify_material(empty_witness)

    def test_empty_mode_requires_a_literal_empty_named_result(self):
        for result in (None, [{}]):
            material = empty_material()
            material["rpc_records"][1]["outcome"]["result"] = result
            with self.subTest(result_type=type(result).__name__):
                with self.assertRaises(IntegrityError) as raised:
                    verify_material(material)
                message = str(raised.exception)
                self.assertLessEqual(len(message), 1200)
                self.assertNotIn(repr(result), message)

    def test_existing_scoped_root_target_and_projection_are_unchanged(self):
        report = verify_material(support.receipt_fixture_material())
        self.assertEqual(report["mode"], "scoped")
        self.assertEqual(report["receipt_count"], 2)
        self.assertEqual(report["target_transaction_index"], "0x1")
        self.assertEqual(report["target_log_count"], 1)
        self.assertEqual(report["filtered_log_count"], 1)
        self.assertEqual(report["relations"], 2)


if __name__ == "__main__":
    unittest.main()
