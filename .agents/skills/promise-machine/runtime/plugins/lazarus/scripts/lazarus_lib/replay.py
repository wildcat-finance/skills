"""Exact, immutable JSON-RPC lookup over a verified Lazarus fixture."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .canonical import MAX_JSONL_BYTES, MAX_RECORD_BYTES, dumps, loads
from .errors import IntegrityError
from .manifest import verify_manifest
from .paths import read_confined_bytes
from .records import loads_rpc_records, request_key
from .verifier import verify_fixture


PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
MISS_ERROR = -32070

SUPPORTED_READ_METHODS = {
    "debug_executionwitness",
    "debug_executionwitnessbyblockhash",
    "debug_traceblockbyhash",
    "debug_traceblockbynumber",
    "debug_tracecall",
    "debug_tracetransaction",
    "eth_call",
    "eth_chainid",
    "eth_getbalance",
    "eth_getblockbyhash",
    "eth_getblockbynumber",
    "eth_getblockreceipts",
    "eth_getcode",
    "eth_getlogs",
    "eth_getproof",
    "eth_getstorageat",
    "eth_gettransactionbyhash",
    "eth_gettransactioncount",
    "eth_gettransactionreceipt",
    "net_version",
    "rpc_modules",
    "trace_block",
    "trace_call",
    "trace_filter",
    "trace_replaytransaction",
    "trace_transaction",
    "web3_clientversion",
}
REQUEST_KEYS = {"id", "jsonrpc", "method", "params"}
MISSING = object()


@dataclass(frozen=True)
class ReplayStore:
    outcomes: Mapping[str, bytes]
    fixture_digest: str

    @classmethod
    def from_fixture(cls, root: str | Path) -> "ReplayStore":
        manifest = verify_manifest(root)
        report = verify_fixture(root)
        if manifest["fixture_digest"] != report["fixture_digest"]:
            raise IntegrityError("fixture changed while replay was loading")
        records = _read_bound_records(root, manifest)
        outcomes = MappingProxyType(
            {
                record["request_key"]: dumps(record["outcome"])
                for record in records
            }
        )
        return cls(outcomes=outcomes, fixture_digest=report["fixture_digest"])

    def dispatch(self, request: Any) -> dict[str, Any] | None:
        identifier, method, params, notification, invalid = _request_parts(request)
        if invalid is not None:
            return invalid
        if not self._supports(method):
            response = error_response(
                identifier,
                METHOD_NOT_FOUND,
                "method is not available in Lazarus replay",
            )
            return None if notification else response
        key = request_key(method, params)
        outcome_bytes = self.outcomes.get(key)
        if outcome_bytes is None:
            response = error_response(
                identifier,
                MISS_ERROR,
                "request is outside this Lazarus fixture",
                data={
                    "method": method,
                    "params": params,
                    "capture_plan_fragment": {
                        "evidence": "recorded-rpc",
                        "method": method,
                        "name": f"replay-miss-{key[:12]}",
                        "params": params,
                        "required": True,
                    },
                },
            )
            return None if notification else response
        outcome = loads(outcome_bytes, max_bytes=MAX_RECORD_BYTES)
        response = {"jsonrpc": "2.0", "id": identifier, **outcome}
        return None if notification else response

    def _supports(self, method: str) -> bool:
        return method.lower() in SUPPORTED_READ_METHODS


def _request_parts(
    request: Any,
) -> tuple[Any, str, list[Any] | dict[str, Any], bool, dict[str, Any] | None]:
    if not isinstance(request, dict):
        return None, "", [], False, invalid_request()
    identifier = request.get("id", MISSING)
    has_method = isinstance(request.get("method"), str) and bool(request["method"])
    has_params = isinstance(request.get("params"), (list, dict))
    valid_id = identifier is MISSING or _valid_id(identifier)
    valid = (
        set(request).issubset(REQUEST_KEYS)
        and request.get("jsonrpc") == "2.0"
        and has_method
        and has_params
        and valid_id
    )
    if not valid:
        response_id = (
            identifier
            if identifier is not MISSING and _valid_id(identifier)
            else None
        )
        return response_id, "", [], False, invalid_request(response_id)
    notification = identifier is MISSING
    return (
        None if notification else identifier,
        request["method"],
        request["params"],
        notification,
        None,
    )


def _read_bound_records(
    root: str | Path,
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    claim = next(
        item for item in manifest["components"] if item["path"] == "rpc.jsonl"
    )
    raw = read_confined_bytes(root, "rpc.jsonl", max_bytes=MAX_JSONL_BYTES)
    if len(raw) != claim["bytes"] or hashlib.sha256(raw).hexdigest() != claim["sha256"]:
        raise IntegrityError("rpc.jsonl changed while replay was loading")
    return loads_rpc_records(raw)


def _valid_id(value: Any) -> bool:
    return value is None or (
        isinstance(value, (int, str)) and not isinstance(value, bool)
    )


def error_response(
    identifier: Any,
    code: int,
    message: str,
    *,
    data: Any = MISSING,
) -> dict[str, Any]:
    error = {"code": code, "message": message}
    if data is not MISSING:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": identifier, "error": error}


def invalid_request(identifier: Any = None) -> dict[str, Any]:
    return error_response(identifier, INVALID_REQUEST, "invalid JSON-RPC request")


def parse_error() -> dict[str, Any]:
    return error_response(None, PARSE_ERROR, "invalid JSON")
