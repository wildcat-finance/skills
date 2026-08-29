"""Exact JSON-RPC request keys and versioned JSONL record helpers."""

from __future__ import annotations

import hashlib
from itertools import islice
from pathlib import Path
from typing import Any, Iterable

from .canonical import (
    MAX_JSON_BYTES,
    dump,
    dumps,
    dump_jsonl,
    load,
    load_jsonl,
    loads,
    loads_jsonl,
)
from .errors import FormatError, ResourceLimitError
from .schemas import validate_document


def request_key(method: str, params: list[Any] | dict[str, Any]) -> str:
    if not isinstance(method, str) or not method:
        raise FormatError("RPC method must be a non-empty string")
    if not isinstance(params, (list, dict)):
        raise FormatError("RPC params must be an array or object")
    request = {"method": method, "params": params}
    return hashlib.sha256(dumps(request)).hexdigest()


def make_rpc_record(
    method: str,
    params: list[Any] | dict[str, Any],
    *,
    required: bool,
    evidence: str,
    result: Any = None,
    error: dict[str, Any] | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    if error is not None and result is not None:
        raise FormatError("RPC record cannot carry both result and error")
    outcome = {"error": error} if error is not None else {"result": result}
    record: dict[str, Any] = {
        "schema_version": 1,
        "request_key": request_key(method, params),
        "method": method,
        "params": params,
        "required": required,
        "evidence": evidence,
        "outcome": outcome,
    }
    if name is not None:
        record["name"] = name
    return validate_document("rpc-record", record)


def write_rpc_records(path: str | Path, records: Iterable[dict[str, Any]]) -> bytes:
    checked = [validate_document("rpc-record", record) for record in records]
    _unique(checked, "request_key", "RPC request key")
    return dump_jsonl(path, checked, sort_key=lambda item: item["request_key"])


def read_rpc_records(path: str | Path, **limits: int) -> list[dict[str, Any]]:
    return _check_rpc_records(load_jsonl(path, **limits))


def loads_rpc_records(data: bytes, **limits: int) -> list[dict[str, Any]]:
    return _check_rpc_records(loads_jsonl(data, **limits))


def _check_rpc_records(records: list[Any]) -> list[dict[str, Any]]:
    checked = [validate_document("rpc-record", record) for record in records]
    _unique(checked, "request_key", "RPC request key")
    if checked != sorted(checked, key=lambda item: item["request_key"]):
        raise FormatError("RPC records are not sorted by request_key")
    return checked


MAX_ANCHOR_RECORDS = 32


def write_anchor_records(path: str | Path, records: Iterable[dict[str, Any]]) -> bytes:
    materialised = list(islice(records, MAX_ANCHOR_RECORDS + 1))
    if len(materialised) > MAX_ANCHOR_RECORDS:
        raise ResourceLimitError(
            f"anchor record count exceeds {MAX_ANCHOR_RECORDS}"
        )
    checked = [validate_document("anchor-record", record) for record in materialised]
    _unique(checked, "source_id", "anchor source ID")
    return dump_jsonl(
        path,
        checked,
        sort_key=lambda item: item["source_id"],
        max_records=MAX_ANCHOR_RECORDS,
    )


def read_anchor_records(path: str | Path, **limits: int) -> list[dict[str, Any]]:
    limits["max_records"] = min(
        limits.get("max_records", MAX_ANCHOR_RECORDS), MAX_ANCHOR_RECORDS
    )
    return _check_anchor_records(load_jsonl(path, **limits))


def loads_anchor_records(data: bytes, **limits: int) -> list[dict[str, Any]]:
    limits["max_records"] = min(
        limits.get("max_records", MAX_ANCHOR_RECORDS), MAX_ANCHOR_RECORDS
    )
    return _check_anchor_records(loads_jsonl(data, **limits))


def _check_anchor_records(records: list[Any]) -> list[dict[str, Any]]:
    checked = [validate_document("anchor-record", record) for record in records]
    _unique(checked, "source_id", "anchor source ID")
    if checked != sorted(checked, key=lambda item: item["source_id"]):
        raise FormatError("anchor records are not sorted by source_id")
    return checked


MAX_RECEIPT_WITNESS_BYTES = MAX_JSON_BYTES


def write_receipt_witness(path: str | Path, witness: dict[str, Any]) -> bytes:
    """Validate and atomically write one canonical receipt witness."""

    checked = validate_document("receipt-witness", witness)
    return dump(path, checked, max_bytes=MAX_RECEIPT_WITNESS_BYTES)


def read_receipt_witness(path: str | Path) -> dict[str, Any]:
    """Read one regular, no-follow receipt witness within the format cap."""

    return validate_document(
        "receipt-witness", load(path, max_bytes=MAX_RECEIPT_WITNESS_BYTES)
    )


def loads_receipt_witness(data: bytes | str) -> dict[str, Any]:
    """Parse one bounded in-memory receipt witness."""

    return validate_document(
        "receipt-witness", loads(data, max_bytes=MAX_RECEIPT_WITNESS_BYTES)
    )


def write_proof_records(path: str | Path, records: Iterable[dict[str, Any]]) -> bytes:
    checked = [validate_document("proof-record", record) for record in records]
    _unique_normalised_addresses(checked)
    return dump_jsonl(path, checked, sort_key=lambda item: item["address"].lower())


def read_proof_records(path: str | Path, **limits: int) -> list[dict[str, Any]]:
    return _check_proof_records(load_jsonl(path, **limits))


def loads_proof_records(data: bytes, **limits: int) -> list[dict[str, Any]]:
    return _check_proof_records(loads_jsonl(data, **limits))


def _check_proof_records(records: list[Any]) -> list[dict[str, Any]]:
    checked = [validate_document("proof-record", record) for record in records]
    _unique_normalised_addresses(checked)
    if checked != sorted(checked, key=lambda item: item["address"].lower()):
        raise FormatError("proof records are not sorted by address")
    return checked


def _unique(records: list[dict[str, Any]], field: str, label: str) -> None:
    values = [record[field] for record in records]
    if len(values) != len(set(values)):
        raise FormatError(f"duplicate {label}")


def _unique_normalised_addresses(records: list[dict[str, Any]]) -> None:
    values = [record["address"].lower() for record in records]
    if len(values) != len(set(values)):
        raise FormatError("duplicate proof record address")
