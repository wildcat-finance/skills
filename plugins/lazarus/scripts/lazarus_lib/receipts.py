"""Offline reconstruction of Ethereum's ordered consensus receipt trie."""

from __future__ import annotations

import hashlib
from typing import Any

from .canonical import MAX_JSON_BYTES
from .errors import FormatError, IntegrityError, ResourceLimitError
from .header import verify_header
from .hexvalue import (
    address_bytes,
    encode_hex,
    hash32_bytes,
    hex_bytes,
    quantity,
    quantity_bytes,
)
from .rlp import encode, encode_uint
from .schemas import validate_document
from .trieproof import trie_root


MAX_RECEIPTS = 100_000
MAX_LOGS = 100_000
MAX_TOPICS = 4
MAX_LOG_DATA_BYTES = 65_536
MAX_ENCODED_RECEIPT_BYTES = MAX_JSON_BYTES
MAX_ENCODED_BLOCK_BYTES = MAX_JSON_BYTES


def encode_receipt(receipt: dict[str, Any]) -> bytes:
    """Return the consensus trie value for one validated witness receipt."""

    if not isinstance(receipt, dict):
        raise FormatError("receipt must be an object")
    receipt_type = receipt.get("receipt_type")
    if receipt_type not in {"legacy", "0x1", "0x2"}:
        raise FormatError("unsupported receipt type")
    has_status = "status" in receipt
    has_root = "root" in receipt
    if has_status == has_root:
        raise FormatError("receipt must carry exactly one of status or root")
    if receipt_type != "legacy" and has_root:
        raise FormatError("typed receipt cannot carry a pre-Byzantium root")

    if has_status:
        status = quantity_bytes(receipt["status"], label="receipt status")
        if status not in {b"", b"\x01"}:
            raise FormatError("receipt status must be zero or one")
        outcome = status
    else:
        outcome = hash32_bytes(receipt["root"], label="receipt root")

    cumulative_gas = quantity_bytes(
        receipt.get("cumulative_gas_used"), label="receipt cumulative gas used"
    )
    bloom = hex_bytes(receipt.get("logs_bloom"), label="receipt logs bloom", length=256)
    logs = receipt.get("logs")
    if not isinstance(logs, list):
        raise FormatError("receipt logs must be an array")
    if len(logs) > MAX_LOGS:
        raise ResourceLimitError(f"receipt log count exceeds {MAX_LOGS}")
    encoded_logs = []
    encoded_log_bytes = 0
    for log in logs:
        encoded_log = _encode_log(log)
        encoded_log_bytes += len(encode(encoded_log))
        if encoded_log_bytes > MAX_ENCODED_RECEIPT_BYTES:
            raise ResourceLimitError(
                f"encoded receipt exceeds {MAX_ENCODED_RECEIPT_BYTES} bytes"
            )
        encoded_logs.append(encoded_log)
    payload = encode([outcome, cumulative_gas, bloom, encoded_logs])
    if len(payload) > MAX_ENCODED_RECEIPT_BYTES:
        raise ResourceLimitError(
            f"encoded receipt exceeds {MAX_ENCODED_RECEIPT_BYTES} bytes"
        )
    if receipt_type == "legacy":
        return payload
    return bytes([int(receipt_type, 16)]) + payload


def receipt_trie_root(receipts: list[dict[str, Any]]) -> bytes:
    """Reconstruct a bounded receipt trie at keys ``rlp(transactionIndex)``."""

    if not isinstance(receipts, list):
        raise FormatError("receipt set must be an array")
    if not receipts:
        raise FormatError("receipt set must not be empty")
    if len(receipts) > MAX_RECEIPTS:
        raise ResourceLimitError(f"receipt count exceeds {MAX_RECEIPTS}")
    items: list[tuple[bytes, bytes]] = []
    total = 0
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            raise FormatError("receipt entry must be an object")
        found = quantity(receipt.get("transaction_index"), label="transaction index")
        if found != index:
            raise FormatError("receipt indices must be unique and contiguous from zero")
        value = encode_receipt(receipt)
        total += len(value)
        if total > MAX_ENCODED_BLOCK_BYTES:
            raise ResourceLimitError(
                f"encoded receipt set exceeds {MAX_ENCODED_BLOCK_BYTES} bytes"
            )
        items.append((encode_uint(index), value))
    return trie_root(items)


def verify_receipt_relation(
    witness: dict[str, Any],
    *,
    header: dict[str, Any],
    plan: dict[str, Any],
    rpc_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify the two receipt-root relations and recorded RPC consistency.

    ``receiptsRoot`` commits consensus receipt bytes at trie indices. Transaction
    hashes and every other JSON-RPC decoration are checked only for agreement
    among recorded sources and never enter the returned proved relation.
    """

    witness = validate_document("receipt-witness", witness)
    plan = validate_document("plan", plan)
    if plan["schema_version"] != 3:
        raise FormatError("receipt verification requires plan-v3")
    header = validate_document("header", header)
    header_report = verify_header(header)
    expected_root = hash32_bytes(
        header["rpc_result"].get("receiptsRoot"), label="header receiptsRoot"
    )
    witness_root = hash32_bytes(
        witness["header"]["receipts_root"], label="witness receipts root"
    )
    if witness["header"]["number"] != header_report["number"]:
        raise IntegrityError("receipt witness names another block number")
    if witness["header"]["hash"].lower() != header_report["hash"]:
        raise IntegrityError("receipt witness names another block hash")
    if witness_root != expected_root:
        raise IntegrityError("receipt witness names another header receipts root")
    if expected_root == b"\x00" * 32:
        raise IntegrityError("receipt proof refuses a zero receipts root")

    receipts = witness["receipts"]
    computed_root = receipt_trie_root(receipts)
    if computed_root != expected_root:
        raise IntegrityError("reconstructed receipt trie root mismatch")

    relation = plan["receipt_witness"]
    target_index = quantity(
        relation["target_transaction_index"], label="plan target transaction index"
    )
    witness_target = quantity(
        witness["target_receipt"]["transaction_index"],
        label="witness target transaction index",
    )
    if target_index != witness_target:
        raise IntegrityError("plan and witness target transaction indices disagree")
    if target_index >= len(receipts):
        raise IntegrityError("target receipt is absent from the proved receipt set")

    records = _records_by_name(rpc_records)
    block_record = _named_result(records, relation["block_receipts_request"])
    target_record = _named_result(records, relation["target_receipt_lookup_request"])
    filtered_record = _named_result(records, relation["filtered_logs_request"])
    if not isinstance(block_record, list):
        raise IntegrityError("recorded block receipts result is not an array")
    if not isinstance(target_record, dict):
        raise IntegrityError("recorded target receipt result is not an object")
    if not isinstance(filtered_record, list):
        raise IntegrityError("recorded filtered logs result is not an array")

    block_request = _planned_request(plan, relation["block_receipts_request"])
    if block_request["params"] != [header_report["hash"]]:
        raise IntegrityError("recorded block receipts request names another block")
    target_request = _planned_request(plan, relation["target_receipt_lookup_request"])
    filtered_request = _planned_request(plan, relation["filtered_logs_request"])
    if filtered_request["params"] != [witness["filtered_logs"]["filter"]]:
        raise IntegrityError("recorded log filter disagrees with the receipt witness")

    header_hashes = _header_transaction_hashes(header, len(receipts))
    if len(block_record) != len(receipts):
        raise IntegrityError("recorded block receipts do not cover the witness set")

    total_logs = 0
    for index, raw_receipt in enumerate(block_record):
        projected = _rpc_receipt(
            raw_receipt,
            index=index,
            first_log_index=total_logs,
            block_number=header_report["number"],
            block_hash=header_report["hash"],
            expected_transaction_hash=header_hashes[index],
        )
        total_logs += len(projected["logs"])
        if total_logs > MAX_LOGS:
            raise ResourceLimitError(f"block log count exceeds {MAX_LOGS}")
        if encode_receipt(projected) != encode_receipt(receipts[index]):
            raise IntegrityError("recorded block receipt consensus payload disagrees")

    target_payload = encode_receipt(receipts[target_index])
    target_first_log = sum(len(receipt["logs"]) for receipt in receipts[:target_index])
    recorded_target = _rpc_receipt(
        target_record,
        index=target_index,
        first_log_index=target_first_log,
        block_number=header_report["number"],
        block_hash=header_report["hash"],
        expected_transaction_hash=header_hashes[target_index],
    )
    if encode_receipt(recorded_target) != target_payload:
        raise IntegrityError("recorded target receipt consensus payload disagrees")
    lookup = target_request["params"]
    if (
        not isinstance(lookup, list)
        or len(lookup) != 1
        or _hash_bytes(lookup[0], "recorded target lookup hash")
        != header_hashes[target_index]
    ):
        raise IntegrityError("recorded target lookup hash disagrees at target index")

    projection = _filtered_projection(
        receipts,
        witness["filtered_logs"]["filter"],
        block_number=header_report["number"],
        block_hash=header_report["hash"],
    )
    _compare_recorded_logs(
        filtered_record,
        projection,
        transaction_hashes=header_hashes,
    )

    return {
        "block_hash": header_report["hash"],
        "block_number": header_report["number"],
        "expected_root": encode_hex(expected_root),
        "computed_root": encode_hex(computed_root),
        "receipt_count": len(receipts),
        "log_count": total_logs,
        "target_transaction_index": hex(target_index),
        "target_log_count": len(receipts[target_index]["logs"]),
        "filtered_log_count": len(projection),
        "target_payload_sha256": hashlib.sha256(target_payload).hexdigest(),
        "relations": 2,
        "transaction_hash_attribution": "recorded_rpc",
    }


def _encode_log(log: Any) -> list[Any]:
    if not isinstance(log, dict):
        raise FormatError("receipt log must be an object")
    topics = log.get("topics")
    if not isinstance(topics, list):
        raise FormatError("receipt log topics must be an array")
    if len(topics) > MAX_TOPICS:
        raise ResourceLimitError(f"receipt log topic count exceeds {MAX_TOPICS}")
    data_value = log.get("data")
    if (
        isinstance(data_value, str)
        and len(data_value) > 2 + 2 * MAX_LOG_DATA_BYTES
    ):
        raise ResourceLimitError(
            f"receipt log data exceeds {MAX_LOG_DATA_BYTES} bytes"
        )
    data = hex_bytes(data_value, label="receipt log data")
    if len(data) > MAX_LOG_DATA_BYTES:
        raise ResourceLimitError(
            f"receipt log data exceeds {MAX_LOG_DATA_BYTES} bytes"
        )
    return [
        address_bytes(log.get("address")),
        [hash32_bytes(topic, label="receipt log topic") for topic in topics],
        data,
    ]


def _records_by_name(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for record in records:
        name = record.get("name")
        if isinstance(name, str):
            if name in found:
                raise IntegrityError("recorded RPC request names are not unique")
            found[name] = record
    return found


def _named_result(records: dict[str, dict[str, Any]], name: str) -> Any:
    record = records.get(name)
    if record is None:
        raise IntegrityError("receipt relation names an absent RPC record")
    outcome = record.get("outcome")
    if not isinstance(outcome, dict) or "result" not in outcome:
        raise IntegrityError("receipt relation RPC record has no result")
    return outcome["result"]


def _planned_request(plan: dict[str, Any], name: str) -> dict[str, Any]:
    for request in plan["requests"]:
        if request["name"] == name:
            return request
    raise IntegrityError("receipt relation names an absent planned request")


def _header_transaction_hashes(header: dict[str, Any], count: int) -> list[bytes]:
    values = header["rpc_result"].get("transactions")
    if not isinstance(values, list) or len(values) != count:
        raise IntegrityError("recorded header transaction list has another length")
    return [_hash_bytes(value, "recorded header transaction hash") for value in values]


def _rpc_receipt(
    value: Any,
    *,
    index: int,
    first_log_index: int,
    block_number: str,
    block_hash: str,
    expected_transaction_hash: bytes,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IntegrityError("recorded receipt is not an object")
    if quantity(value.get("transactionIndex"), label="recorded transaction index") != index:
        raise IntegrityError("recorded receipt transaction index is not contiguous")
    _recorded_block(value, block_number=block_number, block_hash=block_hash)
    transaction_hash = _hash_bytes(
        value.get("transactionHash"), "recorded receipt transaction hash"
    )
    if transaction_hash != expected_transaction_hash:
        raise IntegrityError("recorded RPC transaction hash disagreement")

    receipt_type = value.get("type", "0x0")
    if receipt_type == "0x0":
        receipt_type = "legacy"
    if receipt_type not in {"legacy", "0x1", "0x2"}:
        raise FormatError("recorded receipt has an unsupported type")
    projected: dict[str, Any] = {
        "transaction_index": hex(index),
        "receipt_type": receipt_type,
        "cumulative_gas_used": value.get("cumulativeGasUsed"),
        "logs_bloom": value.get("logsBloom"),
        "logs": [],
    }
    if "status" in value:
        projected["status"] = value["status"]
    if "root" in value:
        projected["root"] = value["root"]
    logs = value.get("logs")
    if not isinstance(logs, list):
        raise IntegrityError("recorded receipt logs are not an array")
    if len(logs) > MAX_LOGS:
        raise ResourceLimitError(f"recorded receipt log count exceeds {MAX_LOGS}")
    for offset, log in enumerate(logs):
        if not isinstance(log, dict):
            raise IntegrityError("recorded receipt log is not an object")
        _recorded_log_position(
            log,
            transaction_index=index,
            log_index=first_log_index + offset,
            block_number=block_number,
            block_hash=block_hash,
            transaction_hash=expected_transaction_hash,
        )
        projected["logs"].append(_consensus_log(log))
    encode_receipt(projected)
    return projected


def _recorded_block(value: dict[str, Any], *, block_number: str, block_hash: str) -> None:
    if value.get("blockNumber") != block_number:
        raise IntegrityError("recorded RPC result names another block number")
    if _hash_bytes(value.get("blockHash"), "recorded block hash") != hash32_bytes(
        block_hash, label="verified block hash"
    ):
        raise IntegrityError("recorded RPC result names another block hash")


def _recorded_log_position(
    log: dict[str, Any],
    *,
    transaction_index: int,
    log_index: int,
    block_number: str,
    block_hash: str,
    transaction_hash: bytes,
) -> None:
    _recorded_block(log, block_number=block_number, block_hash=block_hash)
    if (
        quantity(
            log.get("transactionIndex"), label="recorded log transaction index"
        )
        != transaction_index
    ):
        raise IntegrityError("recorded log transaction index disagrees")
    if quantity(log.get("logIndex"), label="recorded log index") != log_index:
        raise IntegrityError("recorded log index disagrees with proved order")
    if _hash_bytes(log.get("transactionHash"), "recorded log transaction hash") != transaction_hash:
        raise IntegrityError("recorded RPC transaction hash disagreement")
    if log.get("removed", False) is not False:
        raise IntegrityError("recorded log is marked removed")


def _consensus_log(value: dict[str, Any]) -> dict[str, Any]:
    projected = {
        "address": value.get("address"),
        "topics": value.get("topics"),
        "data": value.get("data"),
    }
    _encode_log(projected)
    return projected


def _filtered_projection(
    receipts: list[dict[str, Any]],
    filter_value: dict[str, Any],
    *,
    block_number: str,
    block_hash: str,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    global_index = 0
    compiled_filter = _compile_filter(filter_value)
    for transaction_index, receipt in enumerate(receipts):
        for log in receipt["logs"]:
            if _matches_compiled_filter(log, compiled_filter):
                result.append(
                    {
                        # ephoros: allow consensus receipt field, not telemetry
                        "address": log["address"],
                        "topics": log["topics"],
                        "data": log["data"],
                        "transaction_index": hex(transaction_index),
                        "log_index": hex(global_index),
                        "block_number": block_number,
                        "block_hash": block_hash,
                    }
                )
            global_index += 1
    return result


def _matches_filter(log: dict[str, Any], filter_value: dict[str, Any]) -> bool:
    return _matches_compiled_filter(log, _compile_filter(filter_value))


def _compile_filter(
    filter_value: dict[str, Any],
) -> tuple[frozenset[bytes] | None, tuple[frozenset[bytes] | None, ...]]:
    addresses = filter_value.get("address")
    expected_addresses = None
    if addresses is not None:
        if isinstance(addresses, str):
            addresses = [addresses]
        expected_addresses = frozenset(address_bytes(value) for value in addresses)

    expected_topics: list[frozenset[bytes] | None] = []
    for selector in filter_value.get("topics", []):
        if selector is None:
            expected_topics.append(None)
            continue
        choices = selector if isinstance(selector, list) else [selector]
        expected_topics.append(
            frozenset(
                hash32_bytes(choice, label="receipt filter topic")
                for choice in choices
                if choice is not None
            )
        )
    return expected_addresses, tuple(expected_topics)


def _matches_compiled_filter(
    log: dict[str, Any],
    compiled_filter: tuple[
        frozenset[bytes] | None,
        tuple[frozenset[bytes] | None, ...],
    ],
) -> bool:
    expected_addresses, expected_topics = compiled_filter
    if expected_addresses is not None:
        # ephoros: allow consensus receipt field, not telemetry
        if address_bytes(log["address"]) not in expected_addresses:
            return False
    topics = log["topics"]
    for index, expected in enumerate(expected_topics):
        if index >= len(topics):
            return False
        if not expected:
            continue
        if hash32_bytes(topics[index], label="receipt log topic") not in expected:
            return False
    return True


def _compare_recorded_logs(
    recorded: list[Any],
    projection: list[dict[str, Any]],
    *,
    transaction_hashes: list[bytes],
) -> None:
    if len(recorded) != len(projection):
        raise IntegrityError("recorded filtered logs disagree with proved projection count")
    for raw, expected in zip(recorded, projection):
        if not isinstance(raw, dict):
            raise IntegrityError("recorded filtered log is not an object")
        transaction_index = quantity(
            expected["transaction_index"], label="proved transaction index"
        )
        _recorded_log_position(
            raw,
            transaction_index=transaction_index,
            log_index=quantity(expected["log_index"], label="proved log index"),
            block_number=expected["block_number"],
            block_hash=expected["block_hash"],
            transaction_hash=transaction_hashes[transaction_index],
        )
        if encode(_encode_log(_consensus_log(raw))) != encode(
            _encode_log(
                {
                    "address": expected["address"],
                    "topics": expected["topics"],
                    "data": expected["data"],
                }
            )
        ):
            raise IntegrityError("recorded filtered log disagrees with proved consensus log")


def _hash_bytes(value: Any, label: str) -> bytes:
    if not isinstance(value, str):
        raise FormatError(f"{label} must be a 32-byte hash")
    return hash32_bytes(value, label=label)
