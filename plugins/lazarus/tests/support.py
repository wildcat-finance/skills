"""Shared paths and small parsers for Lazarus tests."""

import json
from pathlib import Path
import re
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
SKILL = PLUGIN_ROOT / "skills" / "lazarus" / "SKILL.md"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
RECEIPT_CAPTURE_FIXTURE = FIXTURES / "receipt-capture-v1"
RECEIPT_PROOF_FIXTURE = FIXTURES / "receipt-proof-v1"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def load_json(relative):
    return json.loads((PLUGIN_ROOT / relative).read_text(encoding="utf-8"))


def skill_version():
    text = SKILL.read_text(encoding="utf-8")
    match = re.search(r'(?m)^\s+version:\s+"([^"]+)"$', text)
    if match is None:
        raise AssertionError("canonical skill has no metadata version")
    return match.group(1)


def hash32(byte="11"):
    return "0x" + byte * 32


def address(byte="22"):
    return "0x" + byte * 20


def slot(byte="00"):
    return "0x" + byte * 32


def digest(byte="33"):
    return byte * 32


def sample_release():
    """A well-formed release document, for the schema tests to damage.

    The counts are the ones the shipped Goldfinch fixture verifies to, so a
    reader comparing this against the example is not comparing invented numbers
    against real ones.
    """
    return {
        "schema_version": 1,
        "tool_version": "0.1.0",
        "fixture": {"path": "fixture", "fixture_digest": digest("44")},
        "statement": {
            "path": "statement.json",
            "sha256": digest("55"),
            "predicate_type": "https://ariadne.wildcat.finance/state-fixture/v1",
        },
        "verified": {
            "block_hash": hash32("41"),
            "evidence_counts": {
                "proof_backed": 2,
                "header_bound": 1,
                "recorded_rpc": 4,
            },
            "canonical_chain_claim": False,
        },
        "binding": {"checks": ["predicate-type", "block-hash", "evidence-counts"]},
        "release_digest": digest("66"),
    }


def sample_release_v2():
    """A receipt-aware release whose extra authority is explicit and closed."""
    release = sample_release()
    release["schema_version"] = 2
    release["statement"]["predicate_type"] = (
        "https://ariadne.wildcat.finance/state-fixture/v2"
    )
    release["verified"]["receipts_root"] = hash32("22")
    release["verified"]["evidence_counts"]["receipt_trie_proved"] = 2
    return release


def sample_plan():
    return {
        "schema_version": 1,
        "chain": {"chain_id": "0x1", "network": "ethereum-mainnet"},
        "block": {
            "number": "0x10",
            "hash": hash32("11"),
            "hash_source": "release fixture",
        },
        "requests": [
            {
                "name": "chain-id",
                "method": "eth_chainId",
                "params": [],
                "required": True,
                "evidence": "recorded-rpc",
            }
        ],
        "proof_targets": [{"address": address(), "slots": [slot()]}],
        "limits": {
            "max_requests": 10,
            "max_component_bytes": 1048576,
            "max_total_bytes": 4194304,
        },
    }


def sample_plan_v2(source_ids=("archive-a",)):
    plan = sample_plan()
    plan["schema_version"] = 2
    plan["anchor_sources"] = [{"source_id": source_id} for source_id in source_ids]
    return plan


def sample_plan_v3():
    plan = sample_plan_v2()
    plan["schema_version"] = 3
    plan["requests"].extend(
        [
            {
                "name": "block-receipts",
                "method": "eth_getBlockReceipts",
                "params": [plan["block"]["hash"]],
                "required": True,
                "evidence": "recorded-rpc",
            },
            {
                "name": "target-receipt",
                "method": "eth_getTransactionReceipt",
                "params": [hash32("44")],
                "required": True,
                "evidence": "recorded-rpc",
            },
            {
                "name": "filtered-logs",
                "method": "eth_getLogs",
                "params": [
                    {
                        "blockHash": plan["block"]["hash"],
                        "address": address("55"),
                    }
                ],
                "required": True,
                "evidence": "recorded-rpc",
            },
        ]
    )
    plan["receipt_witness"] = {
        "block_receipts_request": "block-receipts",
        "target_receipt_lookup_request": "target-receipt",
        "target_transaction_index": "0x1",
        "filtered_logs_request": "filtered-logs",
    }
    return plan


def sample_manifest_v2():
    return {
        "schema_version": 2,
        "tool_version": "0.1.0",
        "chain_id": "0x1",
        "block": {"number": "0x10", "hash": hash32("11")},
        "receipts_root": hash32("22"),
        "components": [
            {"path": "header.json", "bytes": 1, "sha256": digest("33")},
            {"path": "plan.json", "bytes": 1, "sha256": digest("44")},
            {
                "path": "receipt-witness.json",
                "bytes": 1,
                "sha256": digest("55"),
            },
        ],
        "evidence_counts": {
            "proof_backed": 2,
            "header_bound": 1,
            "recorded_rpc": 4,
            "receipt_trie_proved": 2,
        },
        "optional_failures": [],
        "fixture_digest": digest("66"),
    }


def sample_receipt_witness():
    block_hash = hash32("11")
    block_number = "0x10"
    return {
        "schema_version": 1,
        "header": {
            "number": block_number,
            "hash": block_hash,
            "receipts_root": hash32("22"),
        },
        "receipts": [
            {
                "transaction_index": "0x0",
                "receipt_type": "legacy",
                "status": "0x1",
                "cumulative_gas_used": "0x1",
                "logs_bloom": "0x" + "00" * 256,
                "logs": [],
            },
            {
                "transaction_index": "0x1",
                "receipt_type": "0x2",
                "status": "0x1",
                "cumulative_gas_used": "0x2",
                "logs_bloom": "0x" + "00" * 256,
                "logs": [
                    {
                        "address": address("55"),
                        "topics": [hash32("66")],
                        "data": "0x1234",
                    }
                ],
            },
        ],
        "target_receipt": {
            "transaction_index": "0x1",
        },
        "filtered_logs": {
            "filter": {"blockHash": block_hash, "address": address("55")},
        },
    }


def sample_anchor_record(
    source_id="archive-a",
    *,
    chain_id="0x1",
    block_number="0x10",
    block_hash=None,
):
    block_hash = hash32("11") if block_hash is None else block_hash
    return {
        "schema_version": 1,
        "source_id": source_id,
        "observed_at": "2026-08-25T08:30:45.123456Z",
        "method": "eth_getBlockByNumber",
        "params": [block_number, False],
        "returned": {
            "chain_id": chain_id,
            "number": block_number,
            "hash": block_hash,
        },
    }


def sample_header():
    return {
        "schema_version": 1,
        "chain_id": "0x1",
        "number": "0x10",
        "hash": hash32("11"),
        "parent_hash": hash32("12"),
        "state_root": hash32("13"),
        "rpc_result": {
            "number": "0x10",
            "hash": hash32("11"),
            "parentHash": hash32("12"),
            "stateRoot": hash32("13"),
        },
    }


def genesis_header():
    rpc = {
        "difficulty": "0x400000000",
        "extraData": "0x11bbe8db4e347b4e8c937c1c8370e4b5ed33adb3db69cbdb7a38e1e50b1b82fa",
        "gasLimit": "0x1388",
        "gasUsed": "0x0",
        "hash": "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3",
        "logsBloom": "0x" + "00" * 256,
        "miner": "0x" + "00" * 20,
        "mixHash": "0x" + "00" * 32,
        "nonce": "0x0000000000000042",
        "number": "0x0",
        "parentHash": "0x" + "00" * 32,
        "receiptsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
        "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
        "stateRoot": "0xd7f8974fb5ac78d9ac099b9ad5018bedc2ce0a72dad1827a1709da30580f0544",
        "timestamp": "0x0",
        "transactionsRoot": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
    }
    return {
        "schema_version": 1,
        "chain_id": "0x1",
        "number": rpc["number"],
        "hash": rpc["hash"],
        "parent_hash": rpc["parentHash"],
        "state_root": rpc["stateRoot"],
        "rpc_result": rpc,
    }


def synthetic_fixture_material():
    from eth_hash.auto import keccak
    from trie import HexaryTrie

    from lazarus_lib.header import compute_header_hash
    from lazarus_lib.hexvalue import encode_hex
    from lazarus_lib.records import make_rpc_record
    from lazarus_lib.rlp import encode

    code = b"\x60\x00"
    present_slot = slot("01")
    absent_slot = slot("02")
    storage_trie = HexaryTrie({})
    storage_trie[keccak(bytes.fromhex(present_slot[2:]))] = encode(b"\x38")
    account_value = encode(
        [b"\x01", b"\x02", storage_trie.root_hash, keccak(code)]
    )
    account = address("22")
    state_trie = HexaryTrie({})
    state_trie[keccak(bytes.fromhex(account[2:]))] = account_value

    def proof_hex(trie, key):
        return [encode_hex(encode(node)) for node in trie.get_proof(key)]

    proof_record = {
        "schema_version": 1,
        "evidence": "proof-backed",
        "block_hash": hash32("00"),
        "address": account,
        "balance": "0x2",
        "nonce": "0x1",
        "code_hash": encode_hex(keccak(code)),
        "storage_hash": encode_hex(storage_trie.root_hash),
        "code": encode_hex(code),
        "account_proof": proof_hex(state_trie, keccak(bytes.fromhex(account[2:]))),
        "storage_proof": [
            {
                "key": present_slot,
                "value": "0x38",
                "proof": proof_hex(
                    storage_trie,
                    keccak(bytes.fromhex(present_slot[2:])),
                ),
            },
            {
                "key": absent_slot,
                "value": "0x0",
                "proof": proof_hex(
                    storage_trie,
                    keccak(bytes.fromhex(absent_slot[2:])),
                ),
            },
        ],
    }
    header = genesis_header()
    header["state_root"] = header["rpc_result"]["stateRoot"] = encode_hex(
        state_trie.root_hash
    )
    placeholder = hash32("00")
    header["hash"] = header["rpc_result"]["hash"] = placeholder
    block_hash = encode_hex(compute_header_hash(header))
    header["hash"] = header["rpc_result"]["hash"] = block_hash
    proof_record["block_hash"] = block_hash
    plan = sample_plan()
    plan["block"] = {
        "number": header["number"],
        "hash": block_hash,
        "hash_source": "synthetic offline test vector",
    }
    plan["proof_targets"] = [
        {"address": account, "slots": [present_slot, absent_slot]}
    ]
    rpc_record = make_rpc_record(
        "eth_chainId",
        [],
        required=True,
        evidence="recorded-rpc",
        result="0x1",
        name="chain-id",
    )
    return {
        "plan": plan,
        "header": header,
        "rpc_records": [rpc_record],
        "proof_records": [proof_record],
        "state_trie": state_trie,
        "storage_trie": storage_trie,
    }


def anchored_fixture_material(source_ids=("archive-a", "archive-b")):
    material = synthetic_fixture_material()
    material["plan"]["schema_version"] = 2
    material["plan"]["anchor_sources"] = [
        {"source_id": source_id} for source_id in source_ids
    ]
    return material


def receipt_capture_material():
    """The fixed provider material used to recapture receipt-proof-v1."""

    from lazarus_lib.canonical import load
    from lazarus_lib.records import (
        read_anchor_records,
        read_proof_records,
        read_receipt_witness,
        read_rpc_records,
    )

    return {
        "plan": load(RECEIPT_CAPTURE_FIXTURE / "plan.json"),
        "header": load(RECEIPT_PROOF_FIXTURE / "header.json"),
        "proof_records": read_proof_records(RECEIPT_PROOF_FIXTURE / "proofs.jsonl"),
        "rpc_records": read_rpc_records(RECEIPT_PROOF_FIXTURE / "rpc.jsonl"),
        "receipt_witness": read_receipt_witness(
            RECEIPT_PROOF_FIXTURE / "receipt-witness.json"
        ),
        "anchor_records": read_anchor_records(
            RECEIPT_PROOF_FIXTURE / "anchors.jsonl"
        ),
    }


def rewrite_recorded_target_hash(material, transaction_hash):
    """Rewrite recorded target identity without changing consensus receipt data."""

    from lazarus_lib.records import request_key

    relation = material["plan"]["receipt_witness"]
    index = int(relation["target_transaction_index"], 16)
    material["header"]["rpc_result"]["transactions"][index] = transaction_hash

    target_request = next(
        item
        for item in material["plan"]["requests"]
        if item["name"] == relation["target_receipt_lookup_request"]
    )
    target_request["params"] = [transaction_hash]

    records = {record["name"]: record for record in material["rpc_records"]}
    target_record = records[relation["target_receipt_lookup_request"]]
    target_record["params"] = [transaction_hash]
    target_record["request_key"] = request_key(
        target_record["method"], target_record["params"]
    )

    block_receipts = records[relation["block_receipts_request"]]["outcome"]["result"]
    for receipt in (block_receipts[index], target_record["outcome"]["result"]):
        receipt["transactionHash"] = transaction_hash
        for log in receipt["logs"]:
            log["transactionHash"] = transaction_hash
    filtered_logs = records[relation["filtered_logs_request"]]["outcome"]["result"]
    for log in filtered_logs:
        if int(log["transactionIndex"], 16) == index:
            log["transactionHash"] = transaction_hash


def receipt_fixture_material():
    """A two-receipt, fully bound manifest-v2 fixture for focused tests."""

    from lazarus_lib.header import compute_header_hash
    from lazarus_lib.hexvalue import encode_hex
    from lazarus_lib.receipts import receipt_trie_root
    from lazarus_lib.records import make_rpc_record

    material = synthetic_fixture_material()
    witness = sample_receipt_witness()
    receipt_root = encode_hex(receipt_trie_root(witness["receipts"]))
    header = material["header"]
    transactions = [hash32("33"), hash32("44")]
    header["rpc_result"]["receiptsRoot"] = receipt_root
    header["rpc_result"]["transactions"] = transactions
    header["hash"] = header["rpc_result"]["hash"] = hash32("00")
    block_hash = encode_hex(compute_header_hash(header))
    header["hash"] = header["rpc_result"]["hash"] = block_hash
    material["proof_records"][0]["block_hash"] = block_hash

    witness["header"] = {
        "number": header["number"],
        "hash": block_hash,
        "receipts_root": receipt_root,
    }
    witness["filtered_logs"]["filter"]["blockHash"] = block_hash

    plan = sample_plan_v3()
    plan["block"] = {
        "number": header["number"],
        "hash": block_hash,
        "hash_source": "synthetic receipt-root vector",
    }
    plan["proof_targets"] = material["plan"]["proof_targets"]
    plan["limits"] = material["plan"]["limits"]
    plan["requests"][1]["params"] = [block_hash]
    plan["requests"][2]["params"] = [transactions[1]]
    plan["requests"][3]["params"] = [witness["filtered_logs"]["filter"]]

    global_log_index = 0
    rpc_receipts = []
    for index, receipt in enumerate(witness["receipts"]):
        transaction_hash = transactions[index]
        result = {
            "blockHash": block_hash,
            "blockNumber": header["number"],
            "transactionHash": transaction_hash,
            "transactionIndex": hex(index),
            "type": "0x0" if receipt["receipt_type"] == "legacy" else receipt["receipt_type"],
            "cumulativeGasUsed": receipt["cumulative_gas_used"],
            "logsBloom": receipt["logs_bloom"],
            "logs": [],
        }
        if "status" in receipt:
            result["status"] = receipt["status"]
        else:
            result["root"] = receipt["root"]
        for log in receipt["logs"]:
            result["logs"].append(
                {
                    **log,
                    "blockHash": block_hash,
                    "blockNumber": header["number"],
                    "transactionHash": transaction_hash,
                    "transactionIndex": hex(index),
                    "logIndex": hex(global_log_index),
                    "removed": False,
                }
            )
            global_log_index += 1
        rpc_receipts.append(result)

    relation_requests = {item["name"]: item for item in plan["requests"]}
    material["rpc_records"] = [
        make_rpc_record(
            "eth_chainId",
            [],
            required=True,
            evidence="recorded-rpc",
            result="0x1",
            name="chain-id",
        ),
        make_rpc_record(
            "eth_getBlockReceipts",
            relation_requests["block-receipts"]["params"],
            required=True,
            evidence="recorded-rpc",
            result=rpc_receipts,
            name="block-receipts",
        ),
        make_rpc_record(
            "eth_getTransactionReceipt",
            relation_requests["target-receipt"]["params"],
            required=True,
            evidence="recorded-rpc",
            result=rpc_receipts[1],
            name="target-receipt",
        ),
        make_rpc_record(
            "eth_getLogs",
            relation_requests["filtered-logs"]["params"],
            required=True,
            evidence="recorded-rpc",
            result=rpc_receipts[1]["logs"],
            name="filtered-logs",
        ),
    ]
    material.update(
        {
            "plan": plan,
            "header": header,
            "receipt_witness": witness,
            "anchor_records": [
                sample_anchor_record(
                    "archive-a",
                    block_number=header["number"],
                    block_hash=block_hash,
                )
            ],
        }
    )
    return material


def sample_proof_record():
    return {
        "schema_version": 1,
        "evidence": "proof-backed",
        "block_hash": hash32("11"),
        "address": address(),
        "balance": "0x0",
        "nonce": "0x1",
        "code_hash": hash32("33"),
        "storage_hash": hash32("44"),
        "code": "0x",
        "account_proof": ["0xc0"],
        "storage_proof": [{"key": slot(), "value": "0x0", "proof": ["0xc0"]}],
    }
