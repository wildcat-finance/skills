"""Whole-fixture offline verification and evidence accounting."""

from __future__ import annotations

import hashlib
from typing import Any

from .canonical import MAX_JSON_BYTES, MAX_JSONL_BYTES, loads
from .errors import FormatError, IntegrityError
from .header import verify_header
from .hexvalue import hash32_bytes, hex_bytes, quantity
from .manifest import validate_anchor_records, verify_manifest
from .paths import FixtureRoot, read_confined_bytes
from .proofs import verify_proof_record
from .records import (
    loads_anchor_records,
    loads_proof_records,
    loads_receipt_witness,
    loads_rpc_records,
    request_key,
)
from .receipts import verify_receipt_relation
from .schemas import validate_document
from .text import listed


REQUIRED_COMPONENTS = {"plan.json", "header.json", "rpc.jsonl", "proofs.jsonl"}


def verify_fixture(root: FixtureRoot) -> dict[str, Any]:
    """Verify a whole fixture offline and account for its evidence.

    The report carries the manifest its numbers were computed from. A caller that
    needs both -- binding a statement to the fixture needs the component list and
    the recomputed counts together -- must take the manifest from here rather
    than reading the directory a second time. Two reads are two states, and
    nothing after the first would notice a component changing between them.
    """
    manifest = verify_manifest(root)
    paths = {item["path"] for item in manifest["components"]}
    missing = sorted(REQUIRED_COMPONENTS - paths)
    if missing:
        raise IntegrityError(f"fixture is missing required components: {', '.join(missing)}")
    claims = {item["path"]: item for item in manifest["components"]}
    plan = validate_document(
        "plan", loads(_read_bound(root, "plan.json", claims, MAX_JSON_BYTES))
    )
    header = validate_document(
        "header", loads(_read_bound(root, "header.json", claims, MAX_JSON_BYTES))
    )
    header_report = verify_header(header)
    anchor_records: list[dict[str, Any]] = []
    has_anchor_component = "anchors.jsonl" in paths
    if plan["schema_version"] == 1:
        if has_anchor_component:
            raise IntegrityError("plan-v1 refuses anchors.jsonl")
    else:
        if not has_anchor_component:
            raise IntegrityError("plan-v2 requires anchors.jsonl")
        anchor_records = loads_anchor_records(
            _read_bound(root, "anchors.jsonl", claims, MAX_JSONL_BYTES),
            max_bytes=MAX_JSONL_BYTES,
        )
        validate_anchor_records(
            plan,
            anchor_records,
            chain_id=manifest["chain_id"],
            block_number=header_report["number"],
            block_hash=header_report["hash"],
        )
    rpc_records = loads_rpc_records(
        _read_bound(root, "rpc.jsonl", claims, MAX_JSONL_BYTES)
    )
    proof_records = loads_proof_records(
        _read_bound(root, "proofs.jsonl", claims, MAX_JSONL_BYTES)
    )
    _verify_rpc_coverage(plan, rpc_records, manifest)
    targets = {item["address"].lower(): item for item in plan["proof_targets"]}
    proofs = {item["address"].lower(): item for item in proof_records}
    if set(targets) != set(proofs):
        missing_targets = sorted(set(targets) - set(proofs))
        extra_targets = sorted(set(proofs) - set(targets))
        detail = []
        if missing_targets:
            detail.append("missing " + listed(missing_targets))
        if extra_targets:
            detail.append("extra " + listed(extra_targets))
        raise IntegrityError("proof targets do not match the capture plan: " + "; ".join(detail))
    state_root = hash32_bytes(header_report["state_root"], label="state root")
    account_included = 0
    account_absent = 0
    storage_included = 0
    storage_absent = 0
    for address in sorted(targets):
        result = verify_proof_record(
            proofs[address],
            state_root=state_root,
            expected_block_hash=header_report["hash"],
            expected_slots=targets[address]["slots"],
        )
        if result["account_included"]:
            account_included += 1
        else:
            account_absent += 1
        storage_included += result["storage_included"]
        storage_absent += result["storage_absent"]
    _verify_rpc_outcomes(
        rpc_records,
        proofs,
        block_number=header_report["number"],
        block_hash=header_report["hash"],
    )
    receipt_report = None
    if plan["schema_version"] == 3:
        if "receipt-witness.json" not in paths:
            raise IntegrityError("plan-v3 requires receipt-witness.json")
        witness = loads_receipt_witness(
            _read_bound(root, "receipt-witness.json", claims, MAX_JSON_BYTES)
        )
        receipt_report = verify_receipt_relation(
            witness,
            header=header,
            plan=plan,
            rpc_records=rpc_records,
        )
    counts = {
        "proof_backed": len(proof_records) + storage_included + storage_absent,
        "header_bound": 1,
        "recorded_rpc": len(rpc_records),
    }
    if receipt_report is not None:
        counts["receipt_trie_proved"] = receipt_report["relations"]
    if counts != manifest["evidence_counts"]:
        raise IntegrityError("manifest evidence counts do not match verified contents")
    report = {
        "manifest": manifest,
        "fixture_digest": manifest["fixture_digest"],
        "block_hash": header_report["hash"],
        "block_number": header_report["number"],
        "state_root": header_report["state_root"],
        "evidence_counts": counts,
        "proof_backed": {
            "accounts_included": account_included,
            "accounts_absent": account_absent,
            "storage_included": storage_included,
            "storage_absent": storage_absent,
        },
        "header_bound": {"headers": 1, "canonical_chain_claim": False},
        "chain_anchors": {
            "records": len(anchor_records),
            "canonical_chain_claim": False,
            "provider_independence_claim": False,
        },
        "recorded_rpc": {
            "records": len(rpc_records),
            "optional_failures": len(manifest["optional_failures"]),
        },
    }
    if receipt_report is not None:
        report["receipts_root"] = receipt_report["computed_root"]
        report["receipt_trie_proved"] = receipt_report
    return report


def _read_bound(
    root: FixtureRoot,
    relative: str,
    claims: dict[str, dict[str, Any]],
    max_bytes: int,
) -> bytes:
    data = read_confined_bytes(root, relative, max_bytes=max_bytes)
    claim = claims[relative]
    if len(data) != claim["bytes"] or hashlib.sha256(data).hexdigest() != claim["sha256"]:
        raise IntegrityError(f"component changed after manifest verification: {relative}")
    return data


def _verify_rpc_coverage(
    plan: dict[str, Any],
    records: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> None:
    planned = {
        request_key(item["method"], item["params"]): item
        for item in plan["requests"]
    }
    recorded = {item["request_key"]: item for item in records}
    if set(planned) != set(recorded):
        raise IntegrityError("RPC records do not exactly cover the capture plan")
    failures: list[str] = []
    for key, item in planned.items():
        record = recorded[key]
        for field in ("method", "params", "required", "evidence"):
            if record[field] != item[field]:
                raise IntegrityError(f"RPC record {key} disagrees with plan field {field}")
        if record.get("name") != item["name"]:
            raise IntegrityError(f"RPC record {key} disagrees with plan field name")
        if "error" in record["outcome"]:
            failures.append(key)
    if sorted(failures) != manifest["optional_failures"]:
        raise IntegrityError("manifest optional failures do not match RPC records")


def _verify_rpc_outcomes(
    records: list[dict[str, Any]],
    proofs: dict[str, dict[str, Any]],
    *,
    block_number: str,
    block_hash: str,
) -> None:
    for record in records:
        if "result" not in record["outcome"]:
            continue
        result = record["outcome"]["result"]
        method = record["method"].lower()
        if method in {"eth_getblockbyhash", "eth_getblockbynumber"} and isinstance(
            result, dict
        ):
            candidate = result.get("hash")
            if not isinstance(candidate, str) or candidate.lower() != block_hash:
                raise IntegrityError("recorded block result names another block")
        _verify_bound_fields(result, block_number, block_hash)
        _verify_proof_backed_result(
            record,
            proofs,
            block_number=block_number,
            block_hash=block_hash,
        )


def _verify_bound_fields(value: Any, block_number: str, block_hash: str) -> None:
    if isinstance(value, list):
        for item in value:
            _verify_bound_fields(item, block_number, block_hash)
        return
    if not isinstance(value, dict):
        return
    if "blockHash" in value:
        candidate = value["blockHash"]
        if not isinstance(candidate, str) or candidate.lower() != block_hash:
            raise IntegrityError("recorded RPC result names another block hash")
    if "blockNumber" in value and value["blockNumber"] != block_number:
        raise IntegrityError("recorded RPC result names another block number")
    for item in value.values():
        _verify_bound_fields(item, block_number, block_hash)


def _verify_proof_backed_result(
    record: dict[str, Any],
    proofs: dict[str, dict[str, Any]],
    *,
    block_number: str,
    block_hash: str,
) -> None:
    method = record["method"].lower()
    expected_lengths = {
        "eth_getbalance": 2,
        "eth_getcode": 2,
        "eth_getproof": 3,
        "eth_getstorageat": 3,
        "eth_gettransactioncount": 2,
    }
    if method not in expected_lengths:
        return
    params = record["params"]
    if not isinstance(params, list) or len(params) != expected_lengths[method]:
        raise IntegrityError(f"proof-backed RPC {record['method']} has invalid params")
    address = params[0]
    if not isinstance(address, str):
        raise IntegrityError(f"proof-backed RPC {record['method']} has invalid address")
    proof = proofs.get(address.lower())
    if proof is None:
        return
    _verify_block_selector(params[-1], block_number, block_hash)
    result = record["outcome"]["result"]
    try:
        if method == "eth_getbalance":
            if quantity(result, label="eth_getBalance result") != quantity(
                proof["balance"], label="proved balance"
            ):
                raise IntegrityError("proof-backed RPC balance disagrees with proof")
        elif method == "eth_gettransactioncount":
            if quantity(result, label="eth_getTransactionCount result") != quantity(
                proof["nonce"], label="proved nonce"
            ):
                raise IntegrityError("proof-backed RPC nonce disagrees with proof")
        elif method == "eth_getcode":
            if hex_bytes(result, label="eth_getCode result") != hex_bytes(
                proof["code"], label="proved code"
            ):
                raise IntegrityError("proof-backed RPC code disagrees with proof")
        elif method == "eth_getstorageat":
            _verify_storage_result(params[1], result, proof)
        else:
            _verify_get_proof_result(params[1], result, proof)
    except FormatError as exc:
        raise IntegrityError(f"proof-backed RPC {record['method']} is malformed") from exc


def _verify_block_selector(value: Any, block_number: str, block_hash: str) -> None:
    if value == block_number:
        return
    if isinstance(value, dict):
        keys = set(value)
        if keys.issubset({"blockHash", "requireCanonical"}):
            candidate = value.get("blockHash")
            canonical = value.get("requireCanonical", False)
            if (
                isinstance(candidate, str)
                and candidate.lower() == block_hash
                and isinstance(canonical, bool)
            ):
                return
        if keys == {"blockNumber"} and value.get("blockNumber") == block_number:
            return
    raise IntegrityError("proof-backed RPC selector names another block")


def _normalise_slot(value: Any) -> bytes:
    if not isinstance(value, str):
        raise FormatError("storage key is not hex")
    try:
        return quantity(value, label="storage key").to_bytes(32, "big")
    except FormatError:
        raw = hex_bytes(value, label="storage key")
        if len(raw) > 32:
            raise FormatError("storage key exceeds 32 bytes")
        return raw.rjust(32, b"\x00")


def _verify_storage_result(slot: Any, result: Any, proof: dict[str, Any]) -> None:
    requested = _normalise_slot(slot)
    entries = {
        _normalise_slot(item["key"]): item for item in proof["storage_proof"]
    }
    entry = entries.get(requested)
    if entry is None:
        return
    observed = hex_bytes(result, label="eth_getStorageAt result", length=32)
    expected = quantity(entry["value"], label="proved storage value").to_bytes(
        32, "big"
    )
    if observed != expected:
        raise IntegrityError("proof-backed RPC storage value disagrees with proof")


def _verify_get_proof_result(
    requested_slots: Any,
    result: Any,
    proof: dict[str, Any],
) -> None:
    if not isinstance(requested_slots, list) or not isinstance(result, dict):
        raise IntegrityError("proof-backed RPC eth_getProof result is malformed")
    if not isinstance(result.get("address"), str) or (
        result["address"].lower() != proof["address"].lower()
    ):
        raise IntegrityError("proof-backed RPC proof address disagrees with proof")
    quantity_fields = (("balance", "balance"), ("nonce", "nonce"))
    for rpc_field, proof_field in quantity_fields:
        if quantity(result.get(rpc_field), label=rpc_field) != quantity(
            proof[proof_field], label=f"proved {proof_field}"
        ):
            raise IntegrityError(
                f"proof-backed RPC {rpc_field} disagrees with proof"
            )
    hash_fields = (("codeHash", "code_hash"), ("storageHash", "storage_hash"))
    for rpc_field, proof_field in hash_fields:
        if hash32_bytes(result.get(rpc_field), label=rpc_field) != hash32_bytes(
            proof[proof_field], label=f"proved {proof_field}"
        ):
            raise IntegrityError(
                f"proof-backed RPC {rpc_field} disagrees with proof"
            )
    observed_account = result.get("accountProof")
    if not isinstance(observed_account, list) or [
        hex_bytes(item, label="account proof node") for item in observed_account
    ] != [hex_bytes(item, label="proved account node") for item in proof["account_proof"]]:
        raise IntegrityError("proof-backed RPC account proof disagrees with proof")
    expected_entries = {
        _normalise_slot(item["key"]): item for item in proof["storage_proof"]
    }
    requested = {_normalise_slot(item) for item in requested_slots}
    observed_items = result.get("storageProof")
    if not isinstance(observed_items, list):
        raise IntegrityError("proof-backed RPC storage proof is malformed")
    observed_entries: dict[bytes, dict[str, Any]] = {}
    for item in observed_items:
        if not isinstance(item, dict) or "key" not in item:
            raise IntegrityError("proof-backed RPC storage proof is malformed")
        key = _normalise_slot(item["key"])
        if key in observed_entries:
            raise IntegrityError("proof-backed RPC storage proof has duplicate keys")
        observed_entries[key] = item
    if set(observed_entries) != requested:
        raise IntegrityError("proof-backed RPC storage proof disagrees with requested slots")
    for key, observed in observed_entries.items():
        expected = expected_entries.get(key)
        if expected is None:
            raise IntegrityError("proof-backed RPC storage proof is not in proof targets")
        if quantity(observed.get("value"), label="storage proof value") != quantity(
            expected["value"], label="proved storage value"
        ):
            raise IntegrityError("proof-backed RPC storage value disagrees with proof")
        nodes = observed.get("proof")
        if not isinstance(nodes, list) or [
            hex_bytes(item, label="storage proof node") for item in nodes
        ] != [hex_bytes(item, label="proved storage node") for item in expected["proof"]]:
            raise IntegrityError("proof-backed RPC storage proof disagrees with proof")
