"""Finite, bracketed and atomic Lazarus fixture capture."""

from __future__ import annotations

import ctypes
from datetime import datetime, timezone
import errno
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
from typing import Any, Callable, Iterable, Mapping

from .canonical import dump, dumps, load
from .errors import (
    FormatError,
    IntegrityError,
    LazarusError,
    PathError,
    ResourceLimitError,
)
from .header import verify_header
from .hexvalue import encode_hex, hex_bytes, quantity
from .limits import CaptureLimits
from .manifest import build_manifest, write_manifest
from .proofs import verify_proof_record
from .records import (
    make_rpc_record,
    write_anchor_records,
    write_proof_records,
    write_rpc_records,
)
from .rpc import JsonRpcClient
from .schemas import validate_document
from .scrub import assert_no_secrets, provider_secret_union
from .verifier import verify_fixture


COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
ANCHOR_COMPONENT = "anchors.jsonl"
BLOCK_TAGS = {"earliest", "finalized", "latest", "pending", "safe"}
SOURCE_ID = re.compile(r"^[a-z][a-z0-9_.-]{0,127}$")
ENVIRONMENT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
READ_ONLY_METHODS = {
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


class CaptureError(LazarusError):
    """Capture failed without finalising an output fixture."""


def capture_fixture(
    plan_path: str | Path,
    rpc_url: str,
    output: str | Path,
    *,
    headers: Mapping[str, str] | None = None,
    clock: Callable[[], float] = time.monotonic,
    wall_clock: Callable[[], datetime] | None = None,
    anchor_rpc_env: Iterable[str] = (),
    environment: Mapping[str, str] | None = None,
    client_factory: Callable[..., JsonRpcClient] = JsonRpcClient,
    finalizer: Callable[[str | Path, str | Path], Any] | None = None,
) -> dict[str, Any]:
    plan = validate_document("plan", load(plan_path))
    _validate_capture_plan(plan)
    anchor_urls = _resolve_anchor_urls(
        plan,
        anchor_rpc_env,
        os.environ if environment is None else environment,
    )
    plan_bytes = len(dumps(plan)) + 1
    if plan_bytes > plan["limits"]["max_component_bytes"]:
        raise ResourceLimitError("capture plan exceeds its max_component_bytes limit")
    if plan_bytes > plan["limits"]["max_total_bytes"]:
        raise ResourceLimitError("capture plan exceeds its max_total_bytes limit")
    destination = Path(output)
    if destination.exists() or destination.is_symlink():
        raise PathError("capture output already exists")
    parent = destination.parent
    if not parent.is_dir() or parent.is_symlink():
        raise PathError("capture output parent must be an existing real directory")
    limits = CaptureLimits(plan["limits"], clock=clock)
    client = client_factory(rpc_url, limits, headers=headers)
    anchor_clients: dict[str, JsonRpcClient] = {}
    for source_id, url in anchor_urls.items():
        try:
            anchor_clients[source_id] = client_factory(url, limits)
        except Exception:
            raise CaptureError(
                f"anchor source {source_id} failed at mapping"
            ) from None
    try:
        secrets = provider_secret_union(
            ((rpc_url, headers), *((url, None) for url in anchor_urls.values()))
        )
    except Exception:
        raise CaptureError("provider secrets failed at mapping") from None
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.lazarus-", dir=parent))
    finalised = False
    try:
        report = _capture_into(
            stage,
            plan,
            client,
            limits,
            anchor_clients=anchor_clients,
            wall_clock=wall_clock or _utc_now,
        )
        try:
            assert_no_secrets(stage, secrets)
        except IntegrityError:
            raise IntegrityError("capture failed at secret scan") from None
        (finalizer or _atomic_no_replace)(stage, destination)
        finalised = True
        return report
    except LazarusError:
        raise
    except Exception as exc:
        raise CaptureError("capture failed before fixture finalisation") from exc
    finally:
        if not finalised:
            shutil.rmtree(stage, ignore_errors=True)


def _capture_into(
    stage: Path,
    plan: dict[str, Any],
    client: JsonRpcClient,
    limits: CaptureLimits,
    *,
    anchor_clients: Mapping[str, JsonRpcClient],
    wall_clock: Callable[[], datetime],
) -> dict[str, Any]:
    expected_number = plan["block"]["number"]
    expected_hash = plan["block"]["hash"]
    chain_id = client.call("eth_chainId", [])
    if chain_id != plan["chain"]["chain_id"]:
        raise IntegrityError("provider chain ID does not match the capture plan")
    first_header = _fetch_header(client, expected_number, expected_hash)
    rpc_records = _capture_requests(client, plan, expected_number, expected_hash)
    proof_records = [
        _capture_proof(client, target, first_header, expected_number, expected_hash)
        for target in plan["proof_targets"]
    ]
    second_header = _fetch_header(client, expected_number, expected_hash)
    if dumps(first_header["rpc_result"]) != dumps(second_header["rpc_result"]):
        raise IntegrityError("provider returned different header data across capture")
    anchor_records = [
        _capture_anchor(
            source_id,
            anchor_clients[source_id],
            expected_number,
            expected_hash,
            plan["chain"]["chain_id"],
            wall_clock,
        )
        for source_id in sorted(anchor_clients)
    ]
    limits.check_time()
    dump(stage / "plan.json", plan)
    dump(stage / "header.json", first_header)
    write_rpc_records(stage / "rpc.jsonl", rpc_records)
    write_proof_records(stage / "proofs.jsonl", proof_records)
    components = COMPONENTS
    if plan["schema_version"] == 2:
        write_anchor_records(stage / ANCHOR_COMPONENT, anchor_records)
        components = (*COMPONENTS, ANCHOR_COMPONENT)
    optional_failures = sorted(
        record["request_key"]
        for record in rpc_records
        if "error" in record["outcome"]
    )
    proof_count = len(proof_records) + sum(
        len(record["storage_proof"]) for record in proof_records
    )
    manifest = build_manifest(
        stage,
        components,
        chain_id=plan["chain"]["chain_id"],
        block_number=expected_number,
        block_hash=expected_hash,
        evidence_counts={
            "proof_backed": proof_count,
            "header_bound": 1,
            "recorded_rpc": len(rpc_records),
        },
        optional_failures=optional_failures,
    )
    write_manifest(stage, manifest)
    try:
        return verify_fixture(stage)
    except LazarusError:
        raise CaptureError("capture failed at final verification") from None


def _capture_anchor(
    source_id: str,
    client: JsonRpcClient,
    block_number: str,
    block_hash: str,
    expected_chain_id: str,
    wall_clock: Callable[[], datetime],
) -> dict[str, Any]:
    try:
        chain_id = client.call("eth_chainId", [])
    except ResourceLimitError:
        raise ResourceLimitError(
            f"anchor source {source_id} failed at limit"
        ) from None
    except Exception:
        raise CaptureError(
            f"anchor source {source_id} failed at transport"
        ) from None
    if chain_id != expected_chain_id:
        raise IntegrityError(f"anchor source {source_id} failed at chain")
    try:
        header = client.call("eth_getBlockByNumber", [block_number, False])
    except ResourceLimitError:
        raise ResourceLimitError(
            f"anchor source {source_id} failed at limit"
        ) from None
    except Exception:
        raise CaptureError(
            f"anchor source {source_id} failed at transport"
        ) from None
    if not isinstance(header, dict):
        raise CaptureError(f"anchor source {source_id} failed at schema")
    if header.get("number") != block_number:
        raise IntegrityError(f"anchor source {source_id} failed at height")
    returned_hash = header.get("hash")
    if not isinstance(returned_hash, str):
        raise CaptureError(f"anchor source {source_id} failed at schema")
    try:
        hex_bytes(returned_hash, label="anchor block hash", length=32)
    except FormatError:
        raise CaptureError(f"anchor source {source_id} failed at schema") from None
    if returned_hash.lower() != block_hash.lower():
        raise IntegrityError(f"anchor source {source_id} failed at hash")
    try:
        observed_at = _utc_timestamp(wall_clock())
        return validate_document(
            "anchor-record",
            {
                "schema_version": 1,
                "source_id": source_id,
                "observed_at": observed_at,
                "method": "eth_getBlockByNumber",
                "params": [block_number, False],
                "returned": {
                    "chain_id": chain_id,
                    "number": header["number"],
                    "hash": returned_hash,
                },
            },
        )
    except Exception:
        raise CaptureError(f"anchor source {source_id} failed at schema") from None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_timestamp(instant: datetime) -> str:
    if not isinstance(instant, datetime) or instant.tzinfo is None:
        raise ValueError("wall clock must return an aware datetime")
    if instant.utcoffset() != timezone.utc.utcoffset(instant):
        raise ValueError("wall clock must return UTC")
    return instant.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _resolve_anchor_urls(
    plan: dict[str, Any],
    mappings: Iterable[str],
    environment: Mapping[str, str],
) -> dict[str, str]:
    expected = {
        item["source_id"] for item in plan.get("anchor_sources", [])
    }
    declared: dict[str, str] = {}
    for index, mapping in enumerate(mappings):
        if index >= 32:
            raise FormatError("anchor mapping count exceeds 32")
        if not isinstance(mapping, str) or "=" not in mapping:
            raise FormatError("anchor mapping must be SOURCE_ID=ENV_VAR")
        source_id, environment_name = mapping.split("=", 1)
        if SOURCE_ID.fullmatch(source_id) is None:
            raise FormatError("anchor mapping has an invalid source ID")
        if ENVIRONMENT_NAME.fullmatch(environment_name) is None:
            raise FormatError(f"anchor source {source_id} failed at mapping")
        if source_id in declared:
            raise FormatError(
                f"anchor source {source_id} failed at mapping: duplicate {source_id}"
            )
        declared[source_id] = environment_name
    missing = sorted(expected - set(declared))
    extra = sorted(set(declared) - expected)
    if missing or extra:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra " + ", ".join(extra))
        raise FormatError("anchor mapping failed: " + "; ".join(details))
    urls: dict[str, str] = {}
    for source_id in sorted(expected):
        try:
            value = environment[declared[source_id]]
        except Exception:
            raise FormatError(
                f"anchor source {source_id} failed at mapping: environment variable is absent"
            ) from None
        if not isinstance(value, str) or not value.strip():
            raise FormatError(
                f"anchor source {source_id} failed at mapping: environment variable is empty"
            )
        urls[source_id] = value
    return urls


def _fetch_header(
    client: JsonRpcClient,
    number: str,
    expected_hash: str,
) -> dict[str, Any]:
    result = client.call("eth_getBlockByNumber", [number, False])
    if not isinstance(result, dict):
        raise CaptureError("provider did not return the named block header")
    if result.get("number") != number:
        raise IntegrityError("provider block number does not match the capture plan")
    returned_hash = result.get("hash")
    if (
        not isinstance(returned_hash, str)
        or returned_hash.lower() != expected_hash.lower()
    ):
        raise IntegrityError("provider block hash does not match the capture plan")
    document = {
        "schema_version": 1,
        "chain_id": "0x1",
        "number": number,
        "hash": expected_hash,
        "parent_hash": result.get("parentHash"),
        "state_root": result.get("stateRoot"),
        "rpc_result": result,
    }
    try:
        validate_document("header", document)
        verify_header(document)
    except FormatError:
        raise CaptureError("provider returned a malformed block header") from None
    return document


def _capture_requests(
    client: JsonRpcClient,
    plan: dict[str, Any],
    expected_number: str,
    expected_hash: str,
) -> list[dict[str, Any]]:
    requested = plan["requests"]
    outcomes = client.request_many(
        [(item["method"], item["params"]) for item in requested]
    )
    records = []
    for item, outcome in zip(requested, outcomes, strict=True):
        if outcome.error is not None:
            if item["required"]:
                raise CaptureError(f"required RPC request failed: {item['name']}")
            record = make_rpc_record(
                item["method"],
                item["params"],
                required=False,
                evidence=item["evidence"],
                error=outcome.error,
                name=item["name"],
            )
        else:
            _check_result_block(
                item["method"], outcome.result, expected_number, expected_hash
            )
            record = make_rpc_record(
                item["method"],
                item["params"],
                required=item["required"],
                evidence=item["evidence"],
                result=outcome.result,
                name=item["name"],
            )
        records.append(record)
    return records


def _capture_proof(
    client: JsonRpcClient,
    target: dict[str, Any],
    header: dict[str, Any],
    number: str,
    block_hash: str,
) -> dict[str, Any]:
    address = target["address"]
    proof = _state_call(
        client,
        "eth_getProof",
        [address, target["slots"]],
        number,
        block_hash,
    )
    code = _state_call(client, "eth_getCode", [address], number, block_hash)
    if not isinstance(proof, dict):
        raise CaptureError("provider returned an invalid account proof")
    storage = proof.get("storageProof")
    if not isinstance(storage, list):
        raise CaptureError("provider returned an invalid storage proof list")
    normalised_storage = []
    for item in storage:
        if not isinstance(item, dict):
            raise CaptureError("provider returned an invalid storage proof")
        normalised_storage.append(
            {
                "key": _normalise_slot(item.get("key")),
                "value": item.get("value"),
                "proof": item.get("proof"),
            }
        )
    normalised_storage.sort(key=lambda item: item["key"].lower())
    record = {
        "schema_version": 1,
        "evidence": "proof-backed",
        "block_hash": block_hash,
        "address": proof.get("address"),
        "balance": proof.get("balance"),
        "nonce": proof.get("nonce"),
        "code_hash": proof.get("codeHash"),
        "storage_hash": proof.get("storageHash"),
        "code": code,
        "account_proof": proof.get("accountProof"),
        "storage_proof": normalised_storage,
    }
    state_root = hex_bytes(header["state_root"], label="state root", length=32)
    try:
        verify_proof_record(
            record,
            state_root=state_root,
            expected_block_hash=block_hash,
            expected_slots=target["slots"],
        )
    except FormatError:
        raise CaptureError("provider returned a malformed proof response") from None
    return record


def _state_call(
    client: JsonRpcClient,
    method: str,
    params: list[Any],
    number: str,
    block_hash: str,
) -> Any:
    selector = {"blockHash": block_hash, "requireCanonical": True}
    hash_outcome = client.request_many([(method, [*params, selector])])[0]
    if hash_outcome.succeeded:
        return hash_outcome.result
    number_outcome = client.request_many([(method, [*params, number])])[0]
    if number_outcome.error is not None:
        raise CaptureError(f"provider failed required state method {method}")
    return number_outcome.result


def _normalise_slot(value: Any) -> str:
    if not isinstance(value, str):
        raise CaptureError("provider storage proof key is not hex")
    try:
        number = quantity(value, label="provider storage proof key")
        return encode_hex(number.to_bytes(32, "big"))
    except FormatError:
        raw = hex_bytes(value, label="provider storage proof key")
        if len(raw) > 32:
            raise FormatError("provider storage proof key exceeds 32 bytes")
        return encode_hex(raw.rjust(32, b"\x00"))


def _validate_capture_plan(plan: dict[str, Any]) -> None:
    if "max_elapsed_seconds" not in plan["limits"]:
        raise FormatError("capture plan must declare max_elapsed_seconds")
    for item in plan["requests"]:
        if _contains_tag(item["params"]):
            raise FormatError(
                f"effective request {item['name']} contains a moving block tag"
            )
        method = item["method"].lower()
        if method not in READ_ONLY_METHODS:
            raise FormatError(
                f"capture refuses method not in the read-only set: {item['method']}"
            )
        if item["evidence"] != "recorded-rpc":
            raise FormatError(
                f"declared request {item['name']} must be recorded-rpc evidence"
            )


def _contains_tag(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() in BLOCK_TAGS
    if isinstance(value, list):
        return any(_contains_tag(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_tag(item) for item in value.values())
    return False


def _check_result_block(
    method: str,
    result: Any,
    expected_number: str,
    expected_hash: str,
) -> None:
    if method.lower() in {"eth_getblockbyhash", "eth_getblockbynumber"} and isinstance(
        result, dict
    ):
        candidate = result.get("hash")
        if not isinstance(candidate, str) or candidate.lower() != expected_hash.lower():
            raise IntegrityError("recorded block result names another block")
    _check_bound_fields(result, expected_number, expected_hash)


def _check_bound_fields(value: Any, number: str, block_hash: str) -> None:
    if isinstance(value, list):
        for item in value:
            _check_bound_fields(item, number, block_hash)
        return
    if not isinstance(value, dict):
        return
    if "blockHash" in value:
        candidate = value["blockHash"]
        if not isinstance(candidate, str) or candidate.lower() != block_hash.lower():
            raise IntegrityError("recorded RPC result names another block hash")
    if "blockNumber" in value:
        candidate = value["blockNumber"]
        if candidate != number:
            raise IntegrityError("recorded RPC result names another block number")
    for item in value.values():
        _check_bound_fields(item, number, block_hash)


def _atomic_no_replace(source: str | Path, destination: str | Path) -> None:
    """Atomically rename a completed directory and refuse an existing target."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if hasattr(libc, "renameat2"):
        renameat2 = libc.renameat2
        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        result = renameat2(
            -100,
            source_bytes,
            -100,
            destination_bytes,
            1,
        )
    elif hasattr(libc, "renamex_np"):
        renamex = libc.renamex_np
        renamex.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        renamex.restype = ctypes.c_int
        result = renamex(source_bytes, destination_bytes, 0x00000004)
    else:
        raise PathError("platform has no atomic no-replace directory rename")
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in (errno.EEXIST, errno.ENOTEMPTY):
        raise PathError("capture output appeared before finalisation")
    raise PathError(f"cannot finalise capture output: {os.strerror(error)}")
