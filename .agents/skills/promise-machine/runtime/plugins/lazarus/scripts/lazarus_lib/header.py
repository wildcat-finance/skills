"""Fork-aware Ethereum execution block-header hashing."""

from __future__ import annotations

from typing import Any

from eth_hash.auto import keccak

from .errors import FormatError, IntegrityError
from .hexvalue import encode_hex, hex_bytes, quantity_bytes
from .rlp import encode
from .schemas import validate_document


def header_fields(header: dict[str, Any]) -> list[bytes]:
    document = validate_document("header", header)
    block = document["rpc_result"]
    fields = [
        _fixed(block, "parentHash", 32),
        _fixed(block, "sha3Uncles", 32),
        _fixed(block, "miner", 20),
        _fixed(block, "stateRoot", 32),
        _fixed(block, "transactionsRoot", 32),
        _fixed(block, "receiptsRoot", 32),
        _fixed(block, "logsBloom", 256),
        _quantity(block, "difficulty"),
        _quantity(block, "number"),
        _quantity(block, "gasLimit"),
        _quantity(block, "gasUsed"),
        _quantity(block, "timestamp"),
        _extra_data(block),
        _fixed(block, "mixHash", 32),
        _fixed(block, "nonce", 8),
    ]
    has_base_fee = "baseFeePerGas" in block
    has_withdrawals = "withdrawalsRoot" in block
    cancun = ("blobGasUsed", "excessBlobGas", "parentBeaconBlockRoot")
    cancun_count = sum(name in block for name in cancun)
    has_requests = "requestsHash" in block
    if has_withdrawals and not has_base_fee:
        raise FormatError("withdrawalsRoot requires baseFeePerGas")
    if cancun_count not in (0, len(cancun)):
        raise FormatError("Cancun header fields must appear together")
    if cancun_count and not has_withdrawals:
        raise FormatError("Cancun header fields require withdrawalsRoot")
    if has_requests and not cancun_count:
        raise FormatError("requestsHash requires Cancun header fields")
    if has_base_fee:
        fields.append(_quantity(block, "baseFeePerGas"))
    if has_withdrawals:
        fields.append(_fixed(block, "withdrawalsRoot", 32))
    if cancun_count:
        fields.extend(
            (
                _quantity(block, "blobGasUsed"),
                _quantity(block, "excessBlobGas"),
                _fixed(block, "parentBeaconBlockRoot", 32),
            )
        )
    if has_requests:
        fields.append(_fixed(block, "requestsHash", 32))
    return fields


def compute_header_hash(header: dict[str, Any]) -> bytes:
    return keccak(encode(header_fields(header)))


def verify_header(header: dict[str, Any]) -> dict[str, Any]:
    document = validate_document("header", header)
    computed = encode_hex(compute_header_hash(document))
    expected = document["hash"].lower()
    if computed != expected:
        raise IntegrityError(
            f"block header hash mismatch: computed {computed}, expected {expected}"
        )
    state_root = encode_hex(_fixed(document["rpc_result"], "stateRoot", 32))
    if state_root != document["state_root"].lower():
        raise IntegrityError("block header stateRoot disagrees with header document")
    return {
        "hash": computed,
        "number": document["number"],
        "state_root": state_root,
        "field_count": len(header_fields(document)),
    }


def _fixed(block: dict[str, Any], name: str, length: int) -> bytes:
    if name not in block:
        raise FormatError(f"block header is missing {name}")
    return hex_bytes(block[name], label=name, length=length)


def _quantity(block: dict[str, Any], name: str) -> bytes:
    if name not in block:
        raise FormatError(f"block header is missing {name}")
    return quantity_bytes(block[name], label=name)


def _extra_data(block: dict[str, Any]) -> bytes:
    if "extraData" not in block:
        raise FormatError("block header is missing extraData")
    value = hex_bytes(block["extraData"], label="extraData")
    if len(value) > 32:
        raise FormatError("extraData exceeds 32 bytes")
    return value
