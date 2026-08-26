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
