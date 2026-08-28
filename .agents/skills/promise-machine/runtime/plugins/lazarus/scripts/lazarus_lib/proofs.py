"""EIP-1186 account, storage and code verification."""

from __future__ import annotations

from typing import Any

from eth_hash.auto import keccak

from .errors import FormatError, IntegrityError
from .hexvalue import (
    address_bytes,
    encode_hex,
    hash32_bytes,
    hex_bytes,
    quantity,
    slot_bytes,
    uint_from_rlp,
)
from .rlp import decode
from .schemas import validate_document
from .trieproof import EMPTY_TRIE_ROOT, verify_proof


EMPTY_CODE_HASH = keccak(b"")


def decode_account(value: bytes) -> dict[str, Any]:
    decoded = decode(value)
    if not isinstance(decoded, list) or len(decoded) != 4:
        raise FormatError("account leaf must be an RLP list of four fields")
    nonce_raw, balance_raw, storage_root, code_hash = decoded
    if not all(isinstance(item, bytes) for item in decoded):
        raise FormatError("account leaf fields must be RLP byte strings")
    if len(storage_root) != 32:
        raise FormatError("account storage root must be 32 bytes")
    if len(code_hash) != 32:
        raise FormatError("account code hash must be 32 bytes")
    return {
        "nonce": uint_from_rlp(nonce_raw, label="account nonce"),
        "balance": uint_from_rlp(balance_raw, label="account balance"),
        "storage_root": storage_root,
        "code_hash": code_hash,
    }


def decode_storage(value: bytes) -> int:
    decoded = decode(value)
    if not isinstance(decoded, bytes):
        raise FormatError("storage leaf must contain an RLP byte string")
    return uint_from_rlp(decoded, label="storage value")


def proof_nodes(values: list[str]) -> list[bytes]:
    return [hex_bytes(value, label="proof node") for value in values]


def verify_proof_record(
    record: dict[str, Any],
    *,
    state_root: bytes,
    expected_block_hash: str,
    expected_slots: list[str],
) -> dict[str, Any]:
    document = validate_document("proof-record", record)
    if document["block_hash"].lower() != expected_block_hash.lower():
        raise IntegrityError("proof record block hash does not match the fixture")
    address = address_bytes(document["address"])
    account_value = verify_proof(
        state_root,
        keccak(address),
        proof_nodes(document["account_proof"]),
    )
    if account_value is None:
        account = {
            "nonce": 0,
            "balance": 0,
            "storage_root": EMPTY_TRIE_ROOT,
            "code_hash": EMPTY_CODE_HASH,
        }
        account_included = False
    else:
        account = decode_account(account_value)
        account_included = True
    if quantity(document["nonce"], label="account nonce") != account["nonce"]:
        raise IntegrityError("account nonce does not match the proved leaf")
    if quantity(document["balance"], label="account balance") != account["balance"]:
        raise IntegrityError("account balance does not match the proved leaf")
    if hash32_bytes(document["storage_hash"], label="storage hash") != account["storage_root"]:
        raise IntegrityError("storage hash does not match the proved account leaf")
    if hash32_bytes(document["code_hash"], label="code hash") != account["code_hash"]:
        raise IntegrityError("code hash does not match the proved account leaf")
    code = hex_bytes(document["code"], label="captured code")
    if keccak(code) != account["code_hash"]:
        raise IntegrityError("captured code does not match the proved code hash")
    actual_slots = [item["key"].lower() for item in document["storage_proof"]]
    planned_slots = [slot.lower() for slot in expected_slots]
    if actual_slots != planned_slots:
        raise IntegrityError("storage proof keys do not match the capture plan")
    included = 0
    absent = 0
    for item in document["storage_proof"]:
        raw = verify_proof(
            account["storage_root"],
            keccak(slot_bytes(item["key"])),
            proof_nodes(item["proof"]),
        )
        proved = 0 if raw is None else decode_storage(raw)
        if quantity(item["value"], label="storage value") != proved:
            raise IntegrityError(f"storage value does not match proved slot {item['key']}")
        if raw is None:
            absent += 1
        else:
            included += 1
    return {
        "address": encode_hex(address),
        "account_included": account_included,
        "storage_included": included,
        "storage_absent": absent,
    }
