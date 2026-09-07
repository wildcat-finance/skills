"""Exclusive empty and scoped receipt-witness shapes."""

from __future__ import annotations

import copy
from contextlib import ExitStack
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from lazarus_lib.canonical import dump, load
from lazarus_lib.capture import (
    _derive_receipt_witness,
    capture_fixture,
)
from lazarus_lib.errors import FormatError, IntegrityError, PathError, ResourceLimitError
from lazarus_lib.header import compute_header_hash
from lazarus_lib.hexvalue import encode_hex
from lazarus_lib.limits import CaptureLimits
from lazarus_lib.manifest import fixture_digest
from lazarus_lib.receipts import receipt_trie_root, verify_receipt_relation
from lazarus_lib.records import read_rpc_records, request_key
from lazarus_lib.release import verify_release, write_release
from lazarus_lib.schemas import validate_document
from lazarus_lib.trieproof import EMPTY_TRIE_ROOT
from lazarus_lib.verifier import verify_fixture

from . import support
from .fake_rpc import FakeRpc


EMPTY_ROOT = encode_hex(EMPTY_TRIE_ROOT)
GENESIS_HASH = "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
GENESIS_FIXTURE = Path(__file__).resolve(strict=True).parent / "fixtures" / (
    "ethereum-genesis-empty-receipts-v1"
)
GENESIS_DEMO = GENESIS_FIXTURE / "demo.py"


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
    def test_shipped_study_binds_the_selected_shape_to_its_decision(self):
        root = Path(__file__).resolve(strict=True).parents[3]
        study = (
            root / "docs" / "lazarus-empty-block-receipt-witness" / "study.md"
        ).read_text(encoding="utf-8")
        bridge = (
            "```design-bridge\n"
            "schema | hypomnema-design-bridge/v1\n"
            "decision | shape-discriminated\n"
            "record | docs/decisions/drafts/empty-receipt-witness-shapes.md\n"
            "```"
        )
        self.assertEqual(study.count(bridge), 1)

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


class EmptyReceiptCaptureTests(unittest.TestCase):
    def setUp(self):
        try:
            self.derive(self.fixture_material())
        except (KeyError, FormatError, IntegrityError) as error:
            self.fail(f"empty receipt capture precondition failed: {type(error).__name__}")

    def fixture_material(self):
        return {
            "plan": load(GENESIS_FIXTURE / "plan.json"),
            "header": load(GENESIS_FIXTURE / "header.json"),
            "rpc_records": read_rpc_records(GENESIS_FIXTURE / "rpc.jsonl"),
        }

    def derive(self, material):
        return _derive_receipt_witness(
            material["plan"],
            material["header"],
            material["rpc_records"],
            CaptureLimits(material["plan"]["limits"]),
        )

    def dispatch(self, material, receipt_result):
        def answer(method, params, server):
            if method == "eth_chainId":
                return "0x1"
            if method == "eth_getBlockByNumber":
                return copy.deepcopy(material["header"]["rpc_result"])
            if method == "eth_getBlockReceipts":
                return copy.deepcopy(receipt_result)
            raise AssertionError(f"unexpected method {method}")

        return answer

    def test_empty_capture_derives_only_the_exclusive_empty_witness(self):
        material = self.fixture_material()
        witness, report = self.derive(material)
        self.assertEqual(
            witness,
            {
                "schema_version": 1,
                "header": {
                    "number": "0x0",
                    "hash": GENESIS_HASH,
                    "receipts_root": EMPTY_ROOT,
                },
                "receipts": [],
            },
        )
        self.assertEqual(report["mode"], "empty")
        self.assertEqual(report["relations"], 0)

    def test_empty_capture_refuses_missing_null_nonarray_nonempty_and_oversized_results(self):
        oversized = [{}] * 100_001
        cases = (
            ("missing", "missing", IntegrityError),
            ("null", None, IntegrityError),
            ("non-array", {}, IntegrityError),
            ("non-empty", [{}], IntegrityError),
            ("oversized", oversized, ResourceLimitError),
        )
        for label, result, error in cases:
            material = self.fixture_material()
            if result == "missing":
                material["rpc_records"] = []
            else:
                material["rpc_records"][0]["outcome"]["result"] = result
            with self.subTest(label=label), self.assertRaises(error) as raised:
                self.derive(material)
            self.assertLessEqual(len(str(raised.exception)), 1200)

    def test_empty_capture_refuses_header_cardinality_disagreement(self):
        material = self.fixture_material()
        material["header"]["rpc_result"]["transactions"] = [support.hash32("01")]
        with self.assertRaisesRegex(IntegrityError, "cover every header slot"):
            self.derive(material)

    def test_full_capture_makes_one_named_receipt_call_and_finalises_atomically(self):
        material = self.fixture_material()
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            output = root / "fixture"
            primary = stack.enter_context(FakeRpc(self.dispatch(material, [])))
            anchor = stack.enter_context(FakeRpc(self.dispatch(material, [])))
            report = capture_fixture(
                GENESIS_FIXTURE / "plan.json",
                primary.url,
                output,
                anchor_rpc_env=("publicnode-observation=GENESIS_ANCHOR",),
                environment={"GENESIS_ANCHOR": anchor.url},
            )
            receipt_calls = [
                request
                for request in primary.requests
                if request["method"] == "eth_getBlockReceipts"
            ]
            self.assertEqual(
                [(item["params"], item["id"]) for item in receipt_calls],
                [([GENESIS_HASH], 3)],
            )
            self.assertEqual(report["terminal_result"]["mode"], "empty")
            self.assertEqual(
                report["terminal_result"]["relation_scope"]["receipt_trie_proved"],
                [],
            )
            self.assertEqual(report["terminal_result"]["counts"]["receipts"], 0)
            self.assertEqual(report["terminal_result"]["counts"]["selected_logs"], 0)
            self.assertTrue(output.is_dir())
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])

    def test_failed_finalisation_leaves_no_destination_or_stage(self):
        material = self.fixture_material()

        def refuse_finalisation(source, destination):
            raise PathError("test finalisation refusal")

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            output = root / "fixture"
            primary = stack.enter_context(FakeRpc(self.dispatch(material, [])))
            anchor = stack.enter_context(FakeRpc(self.dispatch(material, [])))
            with self.assertRaisesRegex(PathError, "finalisation refusal"):
                capture_fixture(
                    GENESIS_FIXTURE / "plan.json",
                    primary.url,
                    output,
                    anchor_rpc_env=("publicnode-observation=GENESIS_ANCHOR",),
                    environment={"GENESIS_ANCHOR": anchor.url},
                    finalizer=refuse_finalisation,
                )
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])


class EmptyReceiptFixtureTests(unittest.TestCase):
    def setUp(self):
        try:
            verify_fixture(GENESIS_FIXTURE)
        except (FormatError, IntegrityError) as error:
            self.fail(f"empty receipt fixture precondition failed: {type(error).__name__}")

    def test_checked_in_genesis_fixture_verifies_offline_with_stable_digest(self):
        with mock.patch("socket.socket", side_effect=AssertionError("network forbidden")):
            report = verify_fixture(GENESIS_FIXTURE)
        self.assertEqual(report["fixture_digest"], fixture_digest(report["manifest"]))
        self.assertEqual(
            report["fixture_digest"],
            "da15f6d08676c826d36564e59c5ebc2e9388d7dc5bd5f8f3e5a6d31e376bd044",
        )
        self.assertEqual(report["block_hash"], GENESIS_HASH)
        self.assertEqual(report["receipts_root"], EMPTY_ROOT)
        self.assertEqual(report["receipt_trie_proved"]["mode"], "empty")
        self.assertEqual(report["receipt_trie_proved"]["receipt_count"], 0)
        self.assertEqual(report["receipt_trie_proved"]["relations"], 0)
        self.assertEqual(report["evidence_counts"]["receipt_trie_proved"], 0)

    def test_manifest_distinguishes_verified_zero_from_missing_evidence(self):
        report = verify_fixture(GENESIS_FIXTURE)
        validate_document("manifest", report["manifest"])
        missing = copy.deepcopy(report["manifest"])
        del missing["evidence_counts"]["receipt_trie_proved"]
        missing["fixture_digest"] = fixture_digest(missing)
        with self.assertRaisesRegex(FormatError, "invalid manifest"):
            validate_document("manifest", missing)

    def test_ariadne_v2_statement_and_lazarus_v2_release_preserve_verified_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            statement = root / "statement.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.REPO_ROOT / "plugins" / "ariadne" / "scripts" / "ariadne.py"),
                    "capture-state-fixture",
                    "--fixture",
                    str(GENESIS_FIXTURE),
                    "--name",
                    "ethereum-genesis-empty-receipts-v1",
                    "--capture-tool",
                    "lazarus",
                    "--capture-version",
                    "0.2.0",
                    "--capture-command",
                    "lazarus",
                    "--capture-command",
                    "capture",
                    "--first-capture-reason",
                    "first checked empty receipt fixture",
                    "--out",
                    str(statement),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            statement_document = json.loads(statement.read_text(encoding="utf-8"))
            self.assertEqual(
                statement_document["predicateType"],
                "https://ariadne.wildcat.finance/state-fixture/v2",
            )
            self.assertEqual(
                statement_document["predicate"]["evidence"]["receipt_trie_proved"],
                0,
            )
            self.assertEqual(
                statement_document["predicate"]["chain"]["receipts_root"],
                EMPTY_ROOT,
            )

            release_root = root / "release"
            release = write_release(GENESIS_FIXTURE, statement, release_root)
            self.assertEqual(release["schema_version"], 2)
            self.assertEqual(release["verified"]["evidence_counts"]["receipt_trie_proved"], 0)
            read_back = verify_release(release_root)
            self.assertEqual(read_back["evidence_counts"]["receipt_trie_proved"], 0)
            self.assertEqual(read_back["receipts_root"], EMPTY_ROOT)

    def test_missing_statement_evidence_refuses_without_release_output(self):
        from .test_release import statement_for

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            statement_path = root / "statement.json"
            statement = statement_for(GENESIS_FIXTURE)
            del statement["predicate"]["evidence"]["receipt_trie_proved"]
            statement_path.write_text(json.dumps(statement), encoding="utf-8")
            output = root / "release"
            with self.assertRaises((FormatError, IntegrityError)):
                write_release(GENESIS_FIXTURE, statement_path, output)
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".release.staged")), [])

    def test_legacy_and_scoped_fixture_dispatch_stays_unchanged(self):
        legacy = verify_fixture(support.PLUGIN_ROOT / "examples" / "aave-v4-spoke-v0")
        scoped = verify_fixture(support.RECEIPT_PROOF_FIXTURE)
        self.assertNotIn("receipt_trie_proved", legacy["evidence_counts"])
        self.assertEqual(scoped["receipt_trie_proved"]["mode"], "scoped")
        self.assertEqual(scoped["receipt_trie_proved"]["relations"], 2)


class EmptyReceiptDemonstrationTests(unittest.TestCase):
    def run_demo(self):
        result = subprocess.run(
            [sys.executable, str(GENESIS_DEMO)],
            cwd=support.REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_genesis_demonstration_verifies_fixture_statement_and_release_offline(self):
        event = self.run_demo()
        self.assertEqual(event["event"], "ethereum_genesis_empty_receipt_demo")
        self.assertEqual(event["stage"], "complete")
        self.assertEqual(event["network"], "denied")
        self.assertEqual(event["relation"]["mode"], "empty")
        self.assertEqual(event["relation"]["receipts_root"], EMPTY_ROOT)
        self.assertEqual(event["relation"]["receipt_count"], 0)
        self.assertEqual(event["relation"]["proved_relations"], 0)
        self.assertEqual(event["evidence_counts"]["receipt_trie_proved"], 0)
        self.assertEqual(event["versions"]["statement"], "https://ariadne.wildcat.finance/state-fixture/v2")
        self.assertEqual(event["versions"]["release"], 2)
        self.assertEqual(set(event["digests"]), {"fixture", "manifest", "statement", "release"})

    def test_genesis_demonstration_rejects_each_materialised_hostile_copy(self):
        event = self.run_demo()
        self.assertEqual(
            event["mutations"],
            {
                "component_digest": "rejected",
                "count_inflation": "rejected",
                "mixed_shape": "rejected",
                "nonempty_root": "rejected",
                "release": "rejected",
            },
        )


if __name__ == "__main__":
    unittest.main()
