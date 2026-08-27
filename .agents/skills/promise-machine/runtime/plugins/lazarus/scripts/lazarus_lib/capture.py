"""Finite, bracketed and atomic Lazarus fixture capture."""

from __future__ import annotations

import ctypes
from datetime import datetime, timezone
import errno
import hashlib
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
from .hexvalue import encode_hex, hash32_bytes, hex_bytes, quantity
from .limits import (
    MAX_RECEIPT_FIELDS,
    MAX_RECEIPT_LOG_FIELDS,
    CaptureLimits,
)
from .manifest import build_manifest, write_manifest
from .proofs import verify_proof_record
from .records import (
    make_rpc_record,
    write_anchor_records,
    write_proof_records,
    write_receipt_witness,
    write_rpc_records,
)
from .receipts import (
    MAX_LOGS,
    MAX_RECEIPTS,
    MAX_TOPICS,
    _rpc_receipt,
    verify_receipt_relation,
)
from .rpc import JsonRpcClient
from .schemas import validate_document
from .scrub import (
    assert_no_secret_bytes,
    assert_no_secrets,
    provider_secret_union,
    redact_text,
)
from .verifier import verify_fixture


COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
ANCHOR_COMPONENT = "anchors.jsonl"
RECEIPT_COMPONENT = "receipt-witness.json"
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
    terminal_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = validate_document("plan", load(plan_path))
    if terminal_context is not None:
        terminal_context.clear()
    receipt_terminal = _receipt_terminal_context(plan)
    if terminal_context is not None and receipt_terminal is not None:
        terminal_context.update(receipt_terminal)
    _validate_capture_plan(plan)
    _set_terminal_stage(terminal_context, "anchor-mapping")
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
    limits = CaptureLimits(plan["limits"], clock=clock)
    secret_mapping_limit = False
    secret_mapping_failed = False
    try:
        secrets = provider_secret_union(
            ((rpc_url, headers), *((url, None) for url in anchor_urls.values())),
            check_time=limits.check_time,
        )
    except ResourceLimitError:
        secret_mapping_limit = True
    except Exception:
        secret_mapping_failed = True
    if secret_mapping_limit:
        limits.check_time()
        raise ResourceLimitError("provider mapping exceeds capture resource limits")
    if secret_mapping_failed:
        raise CaptureError("provider secrets failed at mapping")
    limits.check_time()
    _set_terminal_safe_identities(terminal_context, plan, secrets)
    _set_terminal_stage(terminal_context, "output-check")
    destination = Path(output)
    if destination.exists() or destination.is_symlink():
        raise PathError("capture output already exists")
    parent = destination.parent
    if not parent.is_dir() or parent.is_symlink():
        raise PathError("capture output parent must be an existing real directory")
    client = client_factory(rpc_url, limits, headers=headers)
    anchor_clients: dict[str, JsonRpcClient] = {}
    for source_id, url in anchor_urls.items():
        try:
            anchor_clients[source_id] = client_factory(url, limits)
        except Exception:
            raise CaptureError(
                f"anchor source {source_id} failed at mapping"
            ) from None
    _set_terminal_stage(terminal_context, "staging")
    try:
        stage = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.lazarus-", dir=parent)
        )
    except OSError:
        raise CaptureError("capture failed at staging") from None
    finalised = False
    unexpected_failure = False
    captured_error_type: type[LazarusError] | None = None
    captured_error_message: str | None = None
    try:
        report = _capture_into(
            stage,
            plan,
            client,
            limits,
            anchor_clients=anchor_clients,
            wall_clock=wall_clock or _utc_now,
            terminal_context=terminal_context,
            terminal_secrets=secrets,
        )
        try:
            _set_terminal_stage(terminal_context, "secret-scan")
            assert_no_secrets(stage, secrets, check_time=limits.check_time)
            terminal = report.get("terminal_result")
            if terminal is not None:
                assert_no_secret_bytes(
                    dumps(terminal),
                    secrets,
                    label="capture terminal result",
                    check_time=limits.check_time,
                )
        except IntegrityError:
            raise IntegrityError("capture failed at secret scan") from None
        _set_terminal_stage(terminal_context, "finalisation")
        limits.check_time()
        (finalizer or _atomic_no_replace)(stage, destination)
        finalised = True
        return report
    except LazarusError as error:
        captured_error_type = type(error)
        captured_error_message = redact_text(str(error), secrets=secrets)
    except Exception:
        unexpected_failure = True
    finally:
        _update_terminal_limit_counts(terminal_context, limits)
        if not finalised:
            shutil.rmtree(stage, ignore_errors=True)
    if captured_error_type is not None:
        raise captured_error_type(captured_error_message)
    if unexpected_failure:
        raise CaptureError("capture failed before fixture finalisation")


def _capture_into(
    stage: Path,
    plan: dict[str, Any],
    client: JsonRpcClient,
    limits: CaptureLimits,
    *,
    anchor_clients: Mapping[str, JsonRpcClient],
    wall_clock: Callable[[], datetime],
    terminal_context: dict[str, Any] | None = None,
    terminal_secrets: set[str] | None = None,
) -> dict[str, Any]:
    expected_number = plan["block"]["number"]
    expected_hash = plan["block"]["hash"]
    _set_terminal_stage(terminal_context, "transport")
    chain_id = client.call("eth_chainId", [])
    if chain_id != plan["chain"]["chain_id"]:
        raise IntegrityError("provider chain ID does not match the capture plan")
    first_header = _fetch_header(client, expected_number, expected_hash)
    if terminal_context:
        expected_root = first_header["rpc_result"].get("receiptsRoot")
        if isinstance(expected_root, str):
            terminal_context["expected_receipts_root"] = _safe_terminal_text(
                expected_root, terminal_secrets or set()
            )
    _set_terminal_stage(terminal_context, "rpc-capture")
    rpc_records = _capture_requests(client, plan, expected_number, expected_hash)
    receipt_witness = None
    receipt_report = None
    if plan["schema_version"] == 3:
        _set_terminal_stage(terminal_context, "receipt-set-binding")
        receipt_witness, receipt_report = _derive_receipt_witness(
            plan,
            first_header,
            rpc_records,
            limits,
            terminal_context=terminal_context,
        )
    _set_terminal_stage(terminal_context, "state-proof")
    proof_records = [
        _capture_proof(client, target, first_header, expected_number, expected_hash)
        for target in plan["proof_targets"]
    ]
    _set_terminal_stage(terminal_context, "block-bracket")
    second_header = _fetch_header(client, expected_number, expected_hash)
    if dumps(first_header["rpc_result"]) != dumps(second_header["rpc_result"]):
        raise IntegrityError("provider returned different header data across capture")
    _set_terminal_stage(terminal_context, "chain-anchor")
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
    if terminal_context is not None and receipt_report is not None:
        terminal_context["counts"]["anchor_records"] = len(anchor_records)
    limits.check_time()
    _set_terminal_stage(terminal_context, "component-write")
    component_bytes = [
        _checked_component(
            limits, "plan.json", dump(stage / "plan.json", plan)
        ),
        _checked_component(
            limits, "header.json", dump(stage / "header.json", first_header)
        ),
        _checked_component(
            limits,
            "rpc.jsonl",
            write_rpc_records(stage / "rpc.jsonl", rpc_records),
        ),
        _checked_component(
            limits,
            "proofs.jsonl",
            write_proof_records(stage / "proofs.jsonl", proof_records),
        ),
    ]
    components = COMPONENTS
    if plan["schema_version"] in (2, 3):
        component_bytes.append(
            _checked_component(
                limits,
                ANCHOR_COMPONENT,
                write_anchor_records(stage / ANCHOR_COMPONENT, anchor_records),
            )
        )
        components = (*COMPONENTS, ANCHOR_COMPONENT)
    if receipt_witness is not None:
        component_bytes.append(
            _checked_component(
                limits,
                RECEIPT_COMPONENT,
                write_receipt_witness(stage / RECEIPT_COMPONENT, receipt_witness),
            )
        )
        components = (*components, RECEIPT_COMPONENT)
    optional_failures = sorted(
        record["request_key"]
        for record in rpc_records
        if "error" in record["outcome"]
    )
    proof_count = len(proof_records) + sum(
        len(record["storage_proof"]) for record in proof_records
    )
    evidence_counts = {
        "proof_backed": proof_count,
        "header_bound": 1,
        "recorded_rpc": len(rpc_records),
    }
    if receipt_report is not None:
        evidence_counts["receipt_trie_proved"] = receipt_report["relations"]
    manifest = build_manifest(
        stage,
        components,
        chain_id=plan["chain"]["chain_id"],
        block_number=expected_number,
        block_hash=expected_hash,
        evidence_counts=evidence_counts,
        optional_failures=optional_failures,
    )
    manifest_size = len(dumps(manifest)) + 1
    limits.check_component_bytes(manifest_size, label="manifest.json")
    limits.check_fixture_bytes(sum(component_bytes) + manifest_size)
    write_manifest(stage, manifest)
    _set_terminal_stage(terminal_context, "final-verification")
    verification_failed = False
    try:
        report = verify_fixture(stage)
    except LazarusError:
        verification_failed = True
    if verification_failed:
        raise CaptureError("capture failed at final verification")
    limits.check_time()
    if receipt_report is not None:
        report["terminal_result"] = _receipt_terminal_result(
            plan,
            report,
            limits,
            terminal_context=terminal_context,
            terminal_secrets=terminal_secrets,
        )
    return report


def _checked_component(limits: CaptureLimits, label: str, data: bytes) -> int:
    limits.check_component_bytes(len(data), label=label)
    return len(data)


def _derive_receipt_witness(
    plan: dict[str, Any],
    header: dict[str, Any],
    rpc_records: list[dict[str, Any]],
    limits: CaptureLimits,
    *,
    terminal_context: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Project one full recorded response into consensus-only witness bytes."""

    relation = plan["receipt_witness"]
    named_records = {
        record.get("name"): record
        for record in rpc_records
        if isinstance(record.get("name"), str)
    }
    block_record = named_records.get(relation["block_receipts_request"])
    if block_record is None:
        raise IntegrityError("receipt capture has no recorded block receipts result")
    outcome = block_record.get("outcome")
    raw_receipts = outcome.get("result") if isinstance(outcome, dict) else None
    if not isinstance(raw_receipts, list):
        raise IntegrityError("recorded block receipts result is not an array")
    limits.check_allocation(
        len(raw_receipts), maximum=MAX_RECEIPTS, label="receipt count"
    )
    if terminal_context is not None:
        terminal_context["counts"]["returned_receipts"] = len(raw_receipts)
    target_result = _recorded_result(
        named_records,
        relation["target_receipt_lookup_request"],
        label="target receipt",
    )
    _check_raw_receipt_shape(target_result, limits, label="target receipt")
    filtered_result = _recorded_result(
        named_records,
        relation["filtered_logs_request"],
        label="filtered logs",
    )
    if not isinstance(filtered_result, list):
        raise IntegrityError("recorded filtered logs result is not an array")
    limits.check_allocation(
        len(filtered_result), maximum=MAX_LOGS, label="filtered log count"
    )
    if terminal_context is not None:
        terminal_context["counts"]["selected_logs"] = len(filtered_result)
    for raw_log in filtered_result:
        _check_raw_log_shape(raw_log, limits, label="filtered log")

    transaction_hashes = header["rpc_result"].get("transactions")
    if not isinstance(transaction_hashes, list):
        raise IntegrityError("recorded header transaction list is not an array")
    limits.check_allocation(
        len(transaction_hashes),
        maximum=MAX_RECEIPTS,
        label="header transaction count",
    )
    if terminal_context is not None:
        terminal_context["counts"]["header_transactions"] = len(
            transaction_hashes
        )
    if len(raw_receipts) != len(transaction_hashes):
        raise IntegrityError("recorded block receipts do not cover every header slot")
    receipts: list[dict[str, Any]] = []
    total_logs = 0
    block_number = header["number"]
    block_hash = header["hash"]
    _set_terminal_stage(terminal_context, "receipt-encoding")
    for index, raw_receipt in enumerate(raw_receipts):
        raw_logs = _check_raw_receipt_shape(
            raw_receipt, limits, label="block receipt"
        )
        if total_logs + len(raw_logs) > MAX_LOGS:
            raise ResourceLimitError(f"block log count exceeds {MAX_LOGS}")
        projected = _rpc_receipt(
            raw_receipt,
            index=index,
            first_log_index=total_logs,
            block_number=block_number,
            block_hash=block_hash,
            expected_transaction_hash=hash32_bytes(
                transaction_hashes[index], label="recorded header transaction hash"
            ),
        )
        total_logs += len(projected["logs"])
        receipts.append(projected)
        if terminal_context is not None:
            terminal_context["counts"]["encoded_receipts"] = len(receipts)
            terminal_context["counts"]["logs"] = total_logs
    if terminal_context is not None:
        terminal_context["counts"].update(
            {
                "encoded_receipts": len(receipts),
                "logs": total_logs,
            }
        )

    target_index = quantity(
        relation["target_transaction_index"], label="target transaction index"
    )
    if target_index >= len(receipts):
        raise IntegrityError("target receipt is absent from the recorded receipt set")
    filtered_request = next(
        item
        for item in plan["requests"]
        if item["name"] == relation["filtered_logs_request"]
    )
    witness = validate_document(
        "receipt-witness",
        {
            "schema_version": 1,
            "header": {
                "number": block_number,
                "hash": block_hash,
                "receipts_root": header["rpc_result"].get("receiptsRoot"),
            },
            "receipts": receipts,
            "target_receipt": {"transaction_index": hex(target_index)},
            "filtered_logs": {"filter": filtered_request["params"][0]},
        },
    )
    _set_terminal_stage(terminal_context, "receipt-relation")
    try:
        relation_report = verify_receipt_relation(
            witness,
            header=header,
            plan=plan,
            rpc_records=rpc_records,
        )
    except LazarusError as exc:
        _set_terminal_stage(terminal_context, _receipt_relation_failure_stage(exc))
        raise
    if terminal_context is not None:
        terminal_context["counts"]["receipt_trie_proved"] = relation_report[
            "relations"
        ]
    return witness, relation_report


def _recorded_result(
    records: Mapping[str, dict[str, Any]], name: str, *, label: str
) -> Any:
    record = records.get(name)
    outcome = record.get("outcome") if isinstance(record, dict) else None
    if not isinstance(outcome, dict) or "result" not in outcome:
        raise IntegrityError(f"recorded {label} result is absent")
    return outcome["result"]


def _check_raw_receipt_shape(
    value: Any, limits: CaptureLimits, *, label: str
) -> list[Any]:
    if not isinstance(value, dict):
        raise IntegrityError(f"recorded {label} is not an object")
    limits.check_allocation(
        len(value), maximum=MAX_RECEIPT_FIELDS, label=f"{label} field count"
    )
    logs = value.get("logs")
    if not isinstance(logs, list):
        raise IntegrityError(f"recorded {label} logs are not an array")
    limits.check_allocation(
        len(logs), maximum=MAX_LOGS, label=f"{label} log count"
    )
    for log in logs:
        _check_raw_log_shape(log, limits, label=f"{label} log")
    return logs


def _check_raw_log_shape(
    value: Any, limits: CaptureLimits, *, label: str
) -> None:
    if not isinstance(value, dict):
        raise IntegrityError(f"recorded {label} is not an object")
    limits.check_allocation(
        len(value), maximum=MAX_RECEIPT_LOG_FIELDS, label=f"{label} field count"
    )
    topics = value.get("topics")
    if not isinstance(topics, list):
        raise IntegrityError(f"recorded {label} topics are not an array")
    limits.check_allocation(
        len(topics), maximum=MAX_TOPICS, label=f"{label} topic count"
    )


def _receipt_terminal_context(plan: dict[str, Any]) -> dict[str, Any] | None:
    """Build the safe context shared by successful and failed plan-v3 output."""

    if plan["schema_version"] != 3:
        return None
    return {
        "correlation_id": None,
        "stage": "plan-validation",
        "block": {
            "number": None,
            "hash": None,
        },
        "recorded_target_selector": {
            "value": None,
            "evidence": "recorded_rpc",
            "transaction_index": None,
        },
        "counts": {
            "rpc_requests": 0,
            "rpc_response_bytes": 0,
            "header_transactions": 0,
            "returned_receipts": 0,
            "encoded_receipts": 0,
            "logs": 0,
            "selected_logs": 0,
            "anchor_records": 0,
            "receipt_trie_proved": 0,
        },
        "versions": {
            "plan": 3,
            "receipt_witness": 1,
        },
    }


def _set_terminal_safe_identities(
    terminal_context: dict[str, Any] | None,
    plan: dict[str, Any],
    secrets: set[str],
) -> None:
    if terminal_context is None or not terminal_context:
        return
    relation = plan["receipt_witness"]
    terminal_context["correlation_id"] = _safe_terminal_text(
        _receipt_correlation_id(plan), secrets
    )
    target_request = next(
        item
        for item in plan["requests"]
        if item["name"] == relation["target_receipt_lookup_request"]
    )
    terminal_context["block"] = {
        "number": _safe_terminal_text(plan["block"]["number"], secrets),
        "hash": _safe_terminal_text(plan["block"]["hash"], secrets),
    }
    terminal_context["recorded_target_selector"].update(
        {
            "value": _safe_terminal_text(target_request["params"][0], secrets),
            "transaction_index": _safe_terminal_text(
                relation["target_transaction_index"], secrets
            ),
        }
    )


def _safe_terminal_text(value: str, secrets: set[str]) -> str | None:
    redacted = redact_text(value, secrets=secrets)
    return value if redacted == value else None


def _receipt_correlation_id(plan: dict[str, Any]) -> str:
    return "lazarus-capture:" + hashlib.sha256(dumps(plan)).hexdigest()


def _set_terminal_stage(
    terminal_context: dict[str, Any] | None, stage: str
) -> None:
    if terminal_context is not None and terminal_context:
        terminal_context["stage"] = stage


def _update_terminal_limit_counts(
    terminal_context: dict[str, Any] | None, limits: CaptureLimits
) -> None:
    if terminal_context is not None and terminal_context:
        terminal_context["counts"]["rpc_requests"] = limits.requests
        terminal_context["counts"]["rpc_response_bytes"] = limits.response_bytes


def _receipt_relation_failure_stage(error: LazarusError) -> str:
    message = str(error).lower()
    if "filtered log" in message or "projection" in message:
        return "filtered-log-equality"
    if "root" in message:
        return "receipts-root-equality"
    if "transaction hash" in message or "block" in message:
        return "recorded-identity"
    if "encode" in message or "type" in message or "bloom" in message:
        return "receipt-encoding"
    return "receipt-set-binding"


def capture_failure_terminal_result(
    terminal_context: Mapping[str, Any], error: LazarusError
) -> dict[str, Any] | None:
    """Return one value-free plan-v3 failure event, or ``None`` without context."""

    if not terminal_context:
        return None
    if isinstance(error, ResourceLimitError):
        failure = "resource-limit"
    elif isinstance(error, PathError):
        failure = "path"
    elif isinstance(error, IntegrityError):
        failure = "integrity"
    elif isinstance(error, FormatError):
        failure = "format"
    elif isinstance(error, CaptureError):
        failure = "capture"
    else:
        failure = "transport"
    result = {
        "schema": "lazarus-capture-terminal/v1",
        "event": "lazarus.capture.failed",
        "correlation_id": terminal_context["correlation_id"],
        "stage": terminal_context["stage"],
        "block": terminal_context["block"],
        "recorded_target_selector": terminal_context[
            "recorded_target_selector"
        ],
        "counts": terminal_context["counts"],
        "versions": terminal_context["versions"],
        "failure": failure,
    }
    expected_root = terminal_context.get("expected_receipts_root")
    if isinstance(expected_root, str):
        result["roots"] = {"expected_receipts_root": expected_root}
    return result


def _receipt_terminal_result(
    plan: dict[str, Any],
    report: dict[str, Any],
    limits: CaptureLimits,
    *,
    terminal_context: Mapping[str, Any] | None = None,
    terminal_secrets: set[str] | None = None,
) -> dict[str, Any]:
    relation = report["receipt_trie_proved"]
    relation_plan = plan["receipt_witness"]
    target_request = next(
        item
        for item in plan["requests"]
        if item["name"] == relation_plan["target_receipt_lookup_request"]
    )
    correlation_id = (
        terminal_context.get("correlation_id")
        if terminal_context is not None
        else _safe_terminal_text(
            _receipt_correlation_id(plan), terminal_secrets or set()
        )
    )
    return {
        "schema": "lazarus-capture-terminal/v1",
        "event": "lazarus.capture.completed",
        "correlation_id": correlation_id,
        "stage": "fixture-finalised",
        "block": {
            "number": report["block_number"],
            "hash": report["block_hash"],
        },
        "recorded_target_selector": {
            "value": target_request["params"][0],
            "evidence": "recorded_rpc",
            "transaction_index": relation["target_transaction_index"],
        },
        "counts": {
            "rpc_requests": limits.requests,
            "rpc_response_bytes": limits.response_bytes,
            "recorded_rpc": report["recorded_rpc"]["records"],
            "anchor_records": report["chain_anchors"]["records"],
            "header_transactions": relation["receipt_count"],
            "returned_receipts": relation["receipt_count"],
            "encoded_receipts": relation["receipt_count"],
            "receipts": relation["receipt_count"],
            "logs": relation["log_count"],
            "selected_logs": relation["filtered_log_count"],
            "receipt_trie_proved": relation["relations"],
        },
        "versions": {
            "tool": report["manifest"]["tool_version"],
            "plan": plan["schema_version"],
            "manifest": report["manifest"]["schema_version"],
            "receipt_witness": 1,
        },
        "roots": {
            "expected_receipts_root": relation["expected_root"],
            "computed_receipts_root": relation["computed_root"],
        },
        "relation_scope": {
            "receipt_trie_proved": [
                "consensus_receipt_payload_at_trie_index",
                "consensus_log_projection",
            ],
            "transaction_hash_attribution": "recorded_rpc",
        },
        "fixture_digest": report["fixture_digest"],
    }


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
    block_receipt_calls = 0
    for item in plan["requests"]:
        if _contains_tag(item["params"]):
            raise FormatError(
                f"effective request {item['name']} contains a moving block tag"
            )
        method = item["method"].lower()
        if method == "eth_getblockreceipts":
            block_receipt_calls += 1
        if method not in READ_ONLY_METHODS:
            raise FormatError(
                f"capture refuses method not in the read-only set: {item['method']}"
            )
        if item["evidence"] != "recorded-rpc":
            raise FormatError(
                f"declared request {item['name']} must be recorded-rpc evidence"
            )
    if plan["schema_version"] == 3:
        if block_receipt_calls != 1:
            raise FormatError(
                "plan-v3 capture requires exactly one eth_getBlockReceipts request"
            )
    elif block_receipt_calls:
        raise FormatError(
            "eth_getBlockReceipts capture requires plan-v3"
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
