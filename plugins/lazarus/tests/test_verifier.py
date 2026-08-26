"""The fixture command joins digest, header and proof checks offline."""

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from lazarus_lib.canonical import dump, dumps, load
from lazarus_lib.errors import FormatError, IntegrityError
from lazarus_lib.manifest import (
    build_manifest,
    component_claim,
    fixture_digest,
    write_manifest,
)
from lazarus_lib.records import (
    make_rpc_record,
    write_anchor_records,
    write_proof_records,
    write_rpc_records,
)
from lazarus_lib.verifier import verify_fixture

from . import support


COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
ANCHORED_COMPONENTS = (*COMPONENTS, "anchors.jsonl")


def write_fixture(
    root: Path,
    material=None,
    *,
    counts=None,
    anchor_source_ids=None,
    anchor_records=None,
):
    material = material or support.synthetic_fixture_material()
    components = COMPONENTS
    if anchor_source_ids is not None:
        material["plan"]["schema_version"] = 2
        material["plan"]["anchor_sources"] = [
            {"source_id": source_id} for source_id in anchor_source_ids
        ]
        if anchor_records is None:
            anchor_records = [
                support.sample_anchor_record(
                    source_id,
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                )
                for source_id in anchor_source_ids
            ]
        components = ANCHORED_COMPONENTS
    dump(root / "plan.json", material["plan"])
    dump(root / "header.json", material["header"])
    write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
    write_proof_records(root / "proofs.jsonl", material["proof_records"])
    if anchor_source_ids is not None:
        write_anchor_records(root / "anchors.jsonl", anchor_records)
    manifest = build_manifest(
        root,
        components,
        chain_id="0x1",
        block_number=material["header"]["number"],
        block_hash=material["header"]["hash"],
        evidence_counts=counts
        or {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
    )
    write_manifest(root, manifest)
    return material


def rebind_component(root: Path, relative: str) -> None:
    manifest = load(root / "manifest.json")
    replacement = component_claim(root, relative)
    manifest["components"] = [
        replacement if item["path"] == relative else item
        for item in manifest["components"]
    ]
    manifest["fixture_digest"] = fixture_digest(manifest)
    dump(root / "manifest.json", manifest)


def replace_anchor_records(root: Path, records) -> None:
    (root / "anchors.jsonl").write_bytes(
        b"".join(dumps(record) + b"\n" for record in records)
    )
    rebind_component(root, "anchors.jsonl")


class VerifierTests(unittest.TestCase):
    def test_anchor_reports_are_separate_counts_with_no_chain_claims(self):
        for count in (1, 32):
            source_ids = tuple(f"source-{index:02d}" for index in range(count))
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_fixture(root, anchor_source_ids=source_ids)
                report = verify_fixture(root)
                self.assertIn("chain_anchors", report)
                self.assertEqual(
                    report["chain_anchors"],
                    {
                        "records": count,
                        "canonical_chain_claim": False,
                        "provider_independence_claim": False,
                    },
                )
                self.assertEqual(
                    report["evidence_counts"],
                    {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
                )

    def test_legacy_plan_reports_zero_anchors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            report = verify_fixture(root)
            self.assertIn("chain_anchors", report)
            self.assertEqual(report["chain_anchors"]["records"], 0)
            self.assertIs(report["chain_anchors"]["canonical_chain_claim"], False)
            self.assertIs(
                report["chain_anchors"]["provider_independence_claim"], False
            )

    def test_anchor_sources_must_exactly_cover_the_plan(self):
        cases = (
            (
                ("archive-a", "archive-b"),
                [support.sample_anchor_record("archive-a")],
                "missing archive-b",
            ),
            (
                ("archive-a",),
                [
                    support.sample_anchor_record("archive-a"),
                    support.sample_anchor_record("archive-b"),
                ],
                "extra archive-b",
            ),
        )
        for source_ids, records, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                material = write_fixture(root, anchor_source_ids=source_ids)
                adjusted = [
                    support.sample_anchor_record(
                        record["source_id"],
                        block_number=material["header"]["number"],
                        block_hash=material["header"]["hash"],
                    )
                    for record in records
                ]
                replace_anchor_records(root, adjusted)
                with self.assertRaisesRegex(IntegrityError, message):
                    verify_fixture(root)

    def test_duplicate_reordered_and_malformed_anchor_records_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = write_fixture(
                root, anchor_source_ids=("archive-a", "archive-b")
            )
            records = [
                support.sample_anchor_record(
                    source_id,
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                )
                for source_id in ("archive-a", "archive-b")
            ]
            hostile = (
                ([records[0], records[0]], "duplicate anchor source ID"),
                ([records[1], records[0]], "not sorted by source_id"),
                ([{"schema_version": 1}], "anchor-record"),
            )
            for candidate, message in hostile:
                with self.subTest(message=message):
                    replace_anchor_records(root, candidate)
                    with self.assertRaisesRegex(FormatError, message):
                        verify_fixture(root)

    def test_wrong_chain_height_and_header_hash_are_refused(self):
        mutations = (
            (
                "wrong-chain",
                lambda record: record["returned"].__setitem__("chain_id", "0x2"),
                FormatError,
                "returned.chain_id",
            ),
            (
                "request-return-height-disagreement",
                lambda record: record["returned"].__setitem__("number", "0x1"),
                FormatError,
                "anchor returned number disagrees with requested block number",
            ),
            (
                "wrong-height",
                lambda record: (
                    record["params"].__setitem__(0, "0x1"),
                    record["returned"].__setitem__("number", "0x1"),
                ),
                IntegrityError,
                "anchor source archive-a names another block number",
            ),
            (
                "header-disagreement",
                lambda record: record["returned"].__setitem__(
                    "hash", support.hash32("ff")
                ),
                IntegrityError,
                "anchor source archive-a disagrees with the verified header",
            ),
        )
        for name, mutate, error, message in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                material = write_fixture(root, anchor_source_ids=("archive-a",))
                record = support.sample_anchor_record(
                    "archive-a",
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                )
                mutate(record)
                replace_anchor_records(root, [record])
                with self.assertRaisesRegex(error, message):
                    verify_fixture(root)

    def test_anchor_component_is_read_once_through_its_manifest_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, anchor_source_ids=("archive-a",))
            from lazarus_lib import verifier as verifier_module

            original_read = verifier_module._read_bound
            reads = []

            def counted_read(fixture, relative, claims, max_bytes):
                reads.append(relative)
                return original_read(fixture, relative, claims, max_bytes)

            with mock.patch(
                "lazarus_lib.verifier._read_bound", side_effect=counted_read
            ):
                report = verify_fixture(root)
            self.assertIn("chain_anchors", report)
            self.assertEqual(reads.count("anchors.jsonl"), 1)

    def test_anchor_mutation_after_manifest_verification_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root, anchor_source_ids=("archive-a",))
            from lazarus_lib import verifier as verifier_module

            original_verify = verifier_module.verify_manifest

            def verify_then_mutate(fixture):
                manifest = original_verify(fixture)
                path = root / "anchors.jsonl"
                data = path.read_bytes()
                path.write_bytes(data.replace(b'"archive-a"', b'"archive-z"', 1))
                return manifest

            with mock.patch(
                "lazarus_lib.verifier.verify_manifest",
                side_effect=verify_then_mutate,
            ):
                with self.assertRaisesRegex(
                    IntegrityError,
                    "component changed after manifest verification: anchors.jsonl",
                ):
                    verify_fixture(root)

    def test_whole_fixture_reports_each_evidence_class_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            report = verify_fixture(root)
            self.assertEqual(
                report["evidence_counts"],
                {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
            )
            self.assertEqual(report["proof_backed"]["accounts_included"], 1)
            self.assertEqual(report["proof_backed"]["storage_included"], 1)
            self.assertEqual(report["proof_backed"]["storage_absent"], 1)
            self.assertFalse(report["header_bound"]["canonical_chain_claim"])

    def test_cli_verify_runs_the_full_verifier_and_prints_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "verify",
                    str(root),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("proof-backed: 3", result.stdout)
            self.assertIn("header-bound: 1", result.stdout)
            self.assertIn("recorded-rpc: 1", result.stdout)
            self.assertIn("chain-anchor-records: 0", result.stdout)

    def test_cli_prints_the_verified_anchor_record_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(
                root, anchor_source_ids=("archive-a", "archive-b")
            )
            result = subprocess.run(
                [sys.executable, str(support.SCRIPTS / "lazarus.py"), "verify", str(root)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("chain-anchor-records: 2", result.stdout)

    def test_raw_component_mutation_fails_before_interpretation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            with (root / "proofs.jsonl").open("ab") as handle:
                handle.write(b"\n")
            with self.assertRaisesRegex(IntegrityError, "size mismatch"):
                verify_fixture(root)

    def test_proof_mutation_fails_even_after_manifest_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = write_fixture(root)
            changed = copy.deepcopy(material["proof_records"])
            node = changed[0]["account_proof"][0]
            changed[0]["account_proof"][0] = node[:-1] + ("0" if node[-1] != "0" else "1")
            write_proof_records(root / "proofs.jsonl", changed)
            rebuilt = build_manifest(
                root,
                COMPONENTS,
                chain_id="0x1",
                block_number=material["header"]["number"],
                block_hash=material["header"]["hash"],
                evidence_counts={"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
            )
            write_manifest(root, rebuilt)
            with self.assertRaisesRegex(IntegrityError, "root"):
                verify_fixture(root)

    def test_proved_rpc_results_cannot_disagree_after_manifest_rebinding(self):
        base = support.synthetic_fixture_material()
        proof = base["proof_records"][0]
        account = proof["address"]
        block = base["header"]["number"]
        present_slot = proof["storage_proof"][0]["key"]
        get_proof_result = {
            "address": account,
            "balance": proof["balance"],
            "nonce": proof["nonce"],
            "codeHash": proof["code_hash"],
            "storageHash": proof["storage_hash"],
            "accountProof": proof["account_proof"],
            "storageProof": [
                {
                    "key": proof["storage_proof"][0]["key"],
                    "value": proof["storage_proof"][0]["value"],
                    "proof": proof["storage_proof"][0]["proof"],
                }
            ],
        }
        changed_get_proof = copy.deepcopy(get_proof_result)
        changed_get_proof["balance"] = "0x3"
        cases = (
            ("eth_getBalance", [account, block], proof["balance"], "0x3"),
            ("eth_getTransactionCount", [account, block], proof["nonce"], "0x2"),
            ("eth_getCode", [account, block], proof["code"], "0x6001"),
            (
                "eth_getProof",
                [account, [present_slot], block],
                get_proof_result,
                changed_get_proof,
            ),
            (
                "eth_getStorageAt",
                [account, present_slot, block],
                "0x" + "00" * 31 + "38",
                "0x" + "00" * 32,
            ),
        )
        for method, params, correct, changed in cases:
            with self.subTest(method=method), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                material = copy.deepcopy(base)
                name = f"proved-{method.lower()}"
                material["plan"]["requests"] = [
                    {
                        "name": name,
                        "method": method,
                        "params": params,
                        "required": True,
                        "evidence": "recorded-rpc",
                    }
                ]
                material["rpc_records"] = [
                    make_rpc_record(
                        method,
                        params,
                        required=True,
                        evidence="recorded-rpc",
                        result=correct,
                        name=name,
                    )
                ]
                write_fixture(root, material)
                verify_fixture(root)
                material["rpc_records"][0]["outcome"]["result"] = changed
                write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
                rebuilt = build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                    evidence_counts={
                        "proof_backed": 3,
                        "header_bound": 1,
                        "recorded_rpc": 1,
                    },
                )
                write_manifest(root, rebuilt)
                with self.assertRaisesRegex(IntegrityError, "proof-backed RPC"):
                    verify_fixture(root)

    def test_proved_rpc_selector_must_name_the_fixture_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            proof = material["proof_records"][0]
            params = [proof["address"], proof["storage_proof"][0]["key"], "0x1"]
            material["plan"]["requests"] = [
                {
                    "name": "wrong-block-slot",
                    "method": "eth_getStorageAt",
                    "params": params,
                    "required": True,
                    "evidence": "recorded-rpc",
                }
            ]
            material["rpc_records"] = [
                make_rpc_record(
                    "eth_getStorageAt",
                    params,
                    required=True,
                    evidence="recorded-rpc",
                    result="0x" + "00" * 31 + "38",
                    name="wrong-block-slot",
                )
            ]
            write_fixture(root, material)
            with self.assertRaisesRegex(IntegrityError, "selector names another block"):
                verify_fixture(root)

    def test_recorded_block_fields_remain_header_bound_after_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            transaction = support.hash32("77")
            params = [transaction]
            result = {
                "transactionHash": transaction,
                "blockHash": material["header"]["hash"],
                "blockNumber": material["header"]["number"],
            }
            material["plan"]["requests"] = [
                {
                    "name": "receipt",
                    "method": "eth_getTransactionReceipt",
                    "params": params,
                    "required": True,
                    "evidence": "recorded-rpc",
                }
            ]
            material["rpc_records"] = [
                make_rpc_record(
                    "eth_getTransactionReceipt",
                    params,
                    required=True,
                    evidence="recorded-rpc",
                    result=result,
                    name="receipt",
                )
            ]
            write_fixture(root, material)
            verify_fixture(root)
            material["rpc_records"][0]["outcome"]["result"]["blockHash"] = (
                support.hash32("99")
            )
            write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
            rebuilt = build_manifest(
                root,
                COMPONENTS,
                chain_id="0x1",
                block_number=material["header"]["number"],
                block_hash=material["header"]["hash"],
                evidence_counts={
                    "proof_backed": 3,
                    "header_bound": 1,
                    "recorded_rpc": 1,
                },
            )
            write_manifest(root, rebuilt)
            with self.assertRaisesRegex(IntegrityError, "another block hash"):
                verify_fixture(root)

    def test_manifest_counts_and_rpc_coverage_are_not_trusted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(IntegrityError, "evidence counts"):
                write_fixture(
                    root,
                    counts={"proof_backed": 2, "header_bound": 1, "recorded_rpc": 1},
                )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            material["plan"]["requests"][0]["method"] = "eth_blockNumber"
            dump(root / "plan.json", material["plan"])
            dump(root / "header.json", material["header"])
            write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
            write_proof_records(root / "proofs.jsonl", material["proof_records"])
            with self.assertRaisesRegex(IntegrityError, "requests are missing"):
                build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                    evidence_counts={
                        "proof_backed": 3,
                        "header_bound": 1,
                        "recorded_rpc": 1,
                    },
                )

    def test_missing_or_extra_proof_targets_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            material = support.synthetic_fixture_material()
            material["plan"]["proof_targets"] = []
            with self.assertRaisesRegex(IntegrityError, "unplanned proof targets"):
                write_fixture(root, material)

    def test_components_remain_digest_bound_after_manifest_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_fixture(root)
            from lazarus_lib import verifier as verifier_module

            original_verify = verifier_module.verify_manifest

            def verify_then_mutate(fixture):
                manifest = original_verify(fixture)
                path = root / "rpc.jsonl"
                data = path.read_bytes()
                path.write_bytes(data.replace(b'"0x1"', b'"0x2"', 1))
                return manifest

            with mock.patch(
                "lazarus_lib.verifier.verify_manifest",
                side_effect=verify_then_mutate,
            ):
                with self.assertRaisesRegex(IntegrityError, "changed after"):
                    verify_fixture(root)


if __name__ == "__main__":
    unittest.main()
