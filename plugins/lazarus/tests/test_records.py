"""Request keys and JSONL records preserve exact request semantics."""

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
import unittest

from lazarus_lib.canonical import dumps
from lazarus_lib.errors import FormatError, ResourceLimitError
from lazarus_lib.records import (
    MAX_RECEIPT_WITNESS_BYTES,
    loads_anchor_records,
    loads_receipt_witness,
    make_rpc_record,
    read_anchor_records,
    read_proof_records,
    read_receipt_witness,
    read_rpc_records,
    request_key,
    write_anchor_records,
    write_proof_records,
    write_receipt_witness,
    write_rpc_records,
)

from . import support


class RecordTests(unittest.TestCase):
    def test_request_key_ignores_object_order_but_preserves_exact_values(self):
        left = request_key("eth_call", [{"to": support.address(), "data": "0x"}, "0x0"])
        reordered = request_key("eth_call", [{"data": "0x", "to": support.address()}, "0x0"])
        self.assertEqual(left, reordered)
        self.assertNotEqual(left, request_key("eth_call", [{"to": support.address(), "data": "0x"}, "0x00"]))
        self.assertNotEqual(request_key("m", [1, 2]), request_key("m", [2, 1]))
        expected = dumps({"method": "eth_chainId", "params": []})
        import hashlib
        self.assertEqual(request_key("eth_chainId", []), hashlib.sha256(expected).hexdigest())

    def test_rpc_writes_sort_records_and_repeat_byte_for_byte(self):
        first = make_rpc_record(
            "eth_chainId", [], required=True, evidence="recorded-rpc", result="0x1"
        )
        second = make_rpc_record(
            "eth_blockNumber", [], required=True, evidence="header-bound", result="0x10"
        )
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory) / "left.jsonl"
            right = Path(directory) / "right.jsonl"
            self.assertEqual(
                write_rpc_records(left, [first, second]),
                write_rpc_records(right, [second, first]),
            )
            self.assertEqual(read_rpc_records(left), sorted([first, second], key=lambda row: row["request_key"]))

    def test_rpc_record_rejects_wrong_keys_duplicates_and_required_errors(self):
        record = make_rpc_record(
            "eth_chainId", [], required=True, evidence="recorded-rpc", result="0x1"
        )
        wrong = copy.deepcopy(record)
        wrong["request_key"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rpc.jsonl"
            with self.assertRaisesRegex(FormatError, "request_key"):
                write_rpc_records(path, [wrong])
            with self.assertRaisesRegex(FormatError, "duplicate"):
                write_rpc_records(path, [record, record])
        with self.assertRaisesRegex(FormatError, "required"):
            make_rpc_record(
                "eth_call",
                [],
                required=True,
                evidence="recorded-rpc",
                error={"code": -32000, "message": "failed"},
            )

    def test_optional_sanitised_error_is_a_valid_record(self):
        record = make_rpc_record(
            "debug_traceCall",
            [],
            required=False,
            evidence="recorded-rpc",
            error={"code": -32601, "message": "method unavailable"},
        )
        self.assertIn("error", record["outcome"])

    def test_jsonl_duplicate_keys_fail_before_record_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rpc.jsonl"
            path.write_bytes(b'{"schema_version":1,"schema_version":1}\n')
            with self.assertRaisesRegex(FormatError, "duplicate JSON key"):
                read_rpc_records(path)

    def test_proof_records_sort_and_reject_duplicate_addresses(self):
        first = support.sample_proof_record()
        second = copy.deepcopy(first)
        second["address"] = support.address("11")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proofs.jsonl"
            write_proof_records(path, [first, second])
            self.assertEqual(
                [row["address"] for row in read_proof_records(path)],
                sorted([first["address"], second["address"]], key=str.lower),
            )
            with self.assertRaisesRegex(FormatError, "duplicate"):
                write_proof_records(path, [first, first])

    def test_anchor_records_have_exact_canonical_bytes_and_source_order(self):
        first = support.sample_anchor_record("a")
        second = support.sample_anchor_record("z")
        expected = dumps(first) + b"\n" + dumps(second) + b"\n"
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory) / "left.jsonl"
            right = Path(directory) / "right.jsonl"
            self.assertEqual(write_anchor_records(left, [second, first]), expected)
            self.assertEqual(write_anchor_records(right, [first, second]), expected)
            self.assertEqual(left.read_bytes(), expected)
            self.assertEqual(read_anchor_records(left), [first, second])
            self.assertEqual(loads_anchor_records(expected), [first, second])

    def test_anchor_records_refuse_duplicates_and_noncanonical_order(self):
        first = support.sample_anchor_record("a")
        second = support.sample_anchor_record("z")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "anchors.jsonl"
            with self.assertRaisesRegex(FormatError, "duplicate anchor source ID"):
                write_anchor_records(path, [first, first])
            path.write_bytes(dumps(second) + b"\n" + dumps(first) + b"\n")
            with self.assertRaisesRegex(FormatError, "not sorted by source_id"):
                read_anchor_records(path)

    def test_anchor_record_count_and_jsonl_shape_are_bounded(self):
        records = [
            support.sample_anchor_record(f"source-{index:02d}")
            for index in range(33)
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "anchors.jsonl"
            with self.assertRaisesRegex(ResourceLimitError, "exceeds 32"):
                write_anchor_records(path, records)
            path.write_bytes(b'{"schema_version":1,"schema_version":1}\n')
            with self.assertRaisesRegex(FormatError, "duplicate JSON key"):
                read_anchor_records(path)

    def test_cli_validates_anchor_record_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "anchors.jsonl"
            write_anchor_records(path, [support.sample_anchor_record()])
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "validate",
                    "anchor-records",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "valid anchor-records\n")

    def test_receipt_witness_round_trip_is_canonical_and_bounded(self):
        witness = support.sample_receipt_witness()
        expected = dumps(witness) + b"\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt-witness.json"
            self.assertEqual(write_receipt_witness(path, witness), expected)
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual(read_receipt_witness(path), witness)
            self.assertEqual(loads_receipt_witness(expected), witness)

    def test_receipt_witness_reader_refuses_depth_bytes_and_non_files(self):
        too_deep = b'{"x":' * 65 + b"null" + b"}" * 65
        with self.assertRaisesRegex(ResourceLimitError, "nesting"):
            loads_receipt_witness(too_deep)
        with self.assertRaisesRegex(ResourceLimitError, "exceeds"):
            loads_receipt_witness(b" " * (MAX_RECEIPT_WITNESS_BYTES + 1))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            write_receipt_witness(target, support.sample_receipt_witness())
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaisesRegex(FormatError, "cannot open"):
                read_receipt_witness(link)
            with self.assertRaisesRegex(FormatError, "not a regular file"):
                read_receipt_witness(root)

    def test_receipt_witness_parse_refusals_are_value_free_and_bounded(self):
        prefix = "PRIVATE_PROVIDER_VALUE_"
        for marker in (prefix + "SECRET", prefix + "x" * 200_000):
            cases = (
                f'{{"{marker}":0,"{marker}":1}}'.encode("utf-8"),
                f'{{"value":"{marker}'.encode("utf-8"),
                b'{"value":"' + marker.encode("utf-8") + b'\xff"}',
            )
            for source in cases:
                with self.subTest(size=len(marker), source_bytes=len(source)), self.assertRaises(
                    FormatError
                ) as raised:
                    loads_receipt_witness(source)
                error = raised.exception
                surfaces = {
                    "message": str(error),
                    "args": repr(error.args),
                    "repr": repr(error),
                    "cause": repr(error.__cause__),
                    "context": repr(error.__context__),
                    "traceback": "".join(
                        traceback.format_exception(
                            type(error), error, error.__traceback__
                        )
                    ),
                }
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
                for name, rendered in surfaces.items():
                    with self.subTest(surface=name):
                        self.assertNotIn(prefix, rendered)
                        self.assertLessEqual(len(rendered.encode("utf-8")), 4096)

    def test_cli_validates_one_receipt_witness(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt-witness.json"
            write_receipt_witness(path, support.sample_receipt_witness())
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "validate",
                    "receipt-witness",
                    str(path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "valid receipt-witness\n")


if __name__ == "__main__":
    unittest.main()
