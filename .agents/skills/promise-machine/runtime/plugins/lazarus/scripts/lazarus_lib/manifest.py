"""Build and verify digest-bound Lazarus fixture manifests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable

from .canonical import MAX_JSON_BYTES, MAX_JSONL_BYTES, dumps, loads
from .errors import FormatError, IntegrityError, ResourceLimitError
from .paths import (
    atomic_write_confined,
    list_fixture_files,
    read_confined_bytes,
    validate_relative_path,
)
from .records import (
    loads_anchor_records,
    loads_proof_records,
    loads_receipt_witness,
    loads_rpc_records,
    request_key,
)
from .receipts import verify_receipt_relation
from .schemas import validate_document
from .version import MANIFEST_V1_WRITER_VERSION, __version__


MANIFEST_NAME = "manifest.json"
MAX_COMPONENTS = 1024
MAX_COMPONENT_BYTES = 512 * 1024 * 1024
MAX_FIXTURE_BYTES = 2 * 1024 * 1024 * 1024
REQUIRED_COMPONENTS = {"plan.json", "header.json", "rpc.jsonl", "proofs.jsonl"}


def component_claim(
    root: str | Path,
    relative: str,
    *,
    max_component_bytes: int = MAX_COMPONENT_BYTES,
) -> dict[str, Any]:
    normalised = validate_relative_path(relative)
    if normalised == MANIFEST_NAME:
        raise FormatError("manifest cannot list itself as a component")
    data = read_confined_bytes(root, normalised, max_bytes=max_component_bytes)
    return {
        "path": normalised,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def fixture_digest(manifest: dict[str, Any]) -> str:
    identity = {
        "schema_version": manifest["schema_version"],
        "tool_version": manifest["tool_version"],
        "chain_id": manifest["chain_id"],
        "block": manifest["block"],
        "components": manifest["components"],
        "evidence_counts": manifest["evidence_counts"],
        "optional_failures": manifest["optional_failures"],
    }
    if manifest["schema_version"] == 2:
        identity["receipts_root"] = manifest["receipts_root"]
    return hashlib.sha256(dumps(identity)).hexdigest()


def build_manifest(
    root: str | Path,
    component_paths: Iterable[str],
    *,
    chain_id: str,
    block_number: str,
    block_hash: str,
    evidence_counts: dict[str, int] | None = None,
    optional_failures: Iterable[str] | None = None,
    max_component_bytes: int = MAX_COMPONENT_BYTES,
    max_fixture_bytes: int = MAX_FIXTURE_BYTES,
) -> dict[str, Any]:
    paths = sorted(validate_relative_path(path) for path in component_paths)
    if not paths:
        raise FormatError("fixture must contain at least one component")
    if len(paths) > MAX_COMPONENTS:
        raise ResourceLimitError(f"component count exceeds {MAX_COMPONENTS}")
    if len(paths) != len(set(paths)):
        raise FormatError("duplicate manifest component path")
    _require_core_components(paths)
    components, observed = _inspect_components(
        root,
        paths,
        max_component_bytes=max_component_bytes,
        max_fixture_bytes=max_fixture_bytes,
        validate_formats=True,
    )
    total_bytes = sum(item["bytes"] for item in components)
    if total_bytes > max_fixture_bytes:
        raise ResourceLimitError(f"fixture components exceed {max_fixture_bytes} bytes")
    receipt_report = _receipt_report(observed)
    observed_counts, observed_failures = _coverage(observed, receipt_report)
    if evidence_counts is not None and evidence_counts != observed_counts:
        raise IntegrityError("declared evidence counts disagree with fixture records")
    if optional_failures is not None:
        failures = sorted(optional_failures)
        if len(failures) != len(set(failures)):
            raise FormatError("duplicate optional failure request key")
        if failures != observed_failures:
            raise IntegrityError("declared optional failures disagree with RPC records")
    schema_version = 2 if receipt_report is not None else 1
    manifest: dict[str, Any] = {
        "schema_version": schema_version,
        "tool_version": __version__,
        "chain_id": chain_id,
        "block": {"number": block_number, "hash": block_hash},
        "components": components,
        "evidence_counts": observed_counts,
        "optional_failures": observed_failures,
        "fixture_digest": "0" * 64,
    }
    if receipt_report is not None:
        manifest["receipts_root"] = receipt_report["computed_root"]
    manifest["fixture_digest"] = fixture_digest(manifest)
    validate_document("manifest", manifest)
    _validate_observed(observed, manifest)
    actual = list_fixture_files(root)
    allowed = set(paths) | ({MANIFEST_NAME} if MANIFEST_NAME in actual else set())
    extra = sorted(actual - allowed)
    if extra:
        raise IntegrityError(f"unlisted fixture files: {', '.join(extra)}")
    if schema_version == 1 and MANIFEST_NAME in actual:
        manifest = _preserve_exact_manifest_v1_writer(root, manifest)
    return manifest


def _preserve_exact_manifest_v1_writer(
    root: str | Path, manifest: dict[str, Any]
) -> dict[str, Any]:
    """Keep legacy provenance only when rebuilding those exact manifest bytes.

    A fresh capture has no manifest in its staging directory and therefore uses
    the current writer. An existing manifest-v1 may retain writer 0.1.0 only
    when every other field and the canonical digest already match the inspected
    components. Schema selection alone cannot establish which writer ran.
    """

    historical = dict(manifest)
    historical["tool_version"] = MANIFEST_V1_WRITER_VERSION
    historical["fixture_digest"] = "0" * 64
    historical["fixture_digest"] = fixture_digest(historical)
    existing = read_confined_bytes(root, MANIFEST_NAME, max_bytes=MAX_JSON_BYTES)
    if existing == dumps(historical) + b"\n":
        validate_document("manifest", historical)
        return historical
    return manifest


def write_manifest(root: str | Path, manifest: dict[str, Any]) -> bytes:
    checked = validate_document("manifest", manifest)
    if checked["fixture_digest"] != fixture_digest(checked):
        raise IntegrityError("fixture digest mismatch")
    data = dumps(checked) + b"\n"
    atomic_write_confined(root, MANIFEST_NAME, data)
    return data


def verify_manifest(
    root: str | Path,
    *,
    max_component_bytes: int = MAX_COMPONENT_BYTES,
    max_fixture_bytes: int = MAX_FIXTURE_BYTES,
    validate_formats: bool = True,
) -> dict[str, Any]:
    manifest_bytes = read_confined_bytes(root, MANIFEST_NAME, max_bytes=MAX_JSON_BYTES)
    manifest = loads(manifest_bytes)
    validate_document("manifest", manifest)
    expected_manifest_bytes = dumps(manifest) + b"\n"
    if manifest_bytes != expected_manifest_bytes:
        raise IntegrityError("manifest is not canonically encoded")
    declared_paths = [item["path"] for item in manifest["components"]]
    _require_core_components(declared_paths)
    _require_version_components(manifest, declared_paths)
    actual_files = list_fixture_files(root)
    expected_files = set(declared_paths) | {MANIFEST_NAME}
    extra = sorted(actual_files - expected_files)
    missing = sorted(expected_files - actual_files)
    if extra:
        raise IntegrityError(f"unlisted fixture files: {', '.join(extra)}")
    if missing:
        raise IntegrityError(f"missing fixture files: {', '.join(missing)}")
    actual_components, observed = _inspect_components(
        root,
        declared_paths,
        max_component_bytes=max_component_bytes,
        max_fixture_bytes=max_fixture_bytes,
        validate_formats=validate_formats,
        expected_components=manifest["components"],
    )
    if actual_components != manifest["components"]:
        raise IntegrityError("manifest component claims do not match fixture bytes")
    expected_digest = fixture_digest(manifest)
    if manifest["fixture_digest"] != expected_digest:
        raise IntegrityError("fixture digest mismatch")
    if validate_formats:
        _validate_observed(observed, manifest)
    return manifest


def _require_core_components(paths: list[str]) -> None:
    missing = sorted(REQUIRED_COMPONENTS - set(paths))
    if missing:
        raise IntegrityError(f"missing required fixture components: {', '.join(missing)}")


def _inspect_components(
    root: str | Path,
    paths: list[str],
    *,
    max_component_bytes: int,
    max_fixture_bytes: int,
    validate_formats: bool,
    expected_components: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    expected = (
        {item["path"]: item for item in expected_components}
        if expected_components is not None
        else {}
    )
    components: list[dict[str, Any]] = []
    observed: dict[str, Any] = {}
    total_bytes = 0
    for relative in paths:
        data = read_confined_bytes(root, relative, max_bytes=max_component_bytes)
        claim = {
            "path": relative,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        total_bytes += len(data)
        if total_bytes > max_fixture_bytes:
            raise ResourceLimitError(f"fixture components exceed {max_fixture_bytes} bytes")
        if expected_components is not None and expected.get(relative) != claim:
            declared = expected.get(relative)
            if declared is not None and declared["bytes"] != claim["bytes"]:
                raise IntegrityError(f"component size mismatch: {relative}")
            raise IntegrityError(f"component digest mismatch: {relative}")
        components.append(claim)
        if not validate_formats:
            continue
        if relative == "plan.json":
            observed["plan"] = validate_document("plan", loads(data))
        elif relative == "header.json":
            observed["header"] = validate_document("header", loads(data))
        elif relative == "rpc.jsonl":
            observed["rpc"] = loads_rpc_records(data, max_bytes=MAX_JSONL_BYTES)
        elif relative == "proofs.jsonl":
            observed["proofs"] = loads_proof_records(data, max_bytes=MAX_JSONL_BYTES)
        elif relative == "receipt-witness.json":
            observed["receipt_witness"] = loads_receipt_witness(data)
        elif relative == "anchors.jsonl":
            observed["anchors"] = loads_anchor_records(
                data, max_bytes=MAX_JSONL_BYTES
            )
    return components, observed


def _coverage(
    observed: dict[str, Any], receipt_report: dict[str, Any] | None = None
) -> tuple[dict[str, int], list[str]]:
    counts = {"proof_backed": 0, "header_bound": 0, "recorded_rpc": 0}
    if receipt_report is not None:
        counts["receipt_trie_proved"] = receipt_report["relations"]
    if "header" in observed:
        counts["header_bound"] += 1
    counts["proof_backed"] += sum(
        1 + len(record["storage_proof"])
        for record in observed.get("proofs", [])
    )
    failures: list[str] = []
    for record in observed.get("rpc", []):
        counts[record["evidence"].replace("-", "_")] += 1
        if not record["required"] and "error" in record["outcome"]:
            failures.append(record["request_key"])
    return counts, sorted(failures)


def _validate_observed(observed: dict[str, Any], manifest: dict[str, Any]) -> None:
    plan = observed["plan"]
    expected_manifest_version = 2 if plan["schema_version"] == 3 else 1
    if manifest["schema_version"] != expected_manifest_version:
        raise IntegrityError("manifest version disagrees with the capture plan")
    if plan["chain"]["chain_id"] != manifest["chain_id"]:
        raise IntegrityError("plan chain_id disagrees with manifest")
    if plan["block"]["number"] != manifest["block"]["number"]:
        raise IntegrityError("plan block number disagrees with manifest")
    if plan["block"]["hash"] != manifest["block"]["hash"]:
        raise IntegrityError("plan block hash disagrees with manifest")
    component_sizes = [item["bytes"] for item in manifest["components"]]
    if any(size > plan["limits"]["max_component_bytes"] for size in component_sizes):
        raise ResourceLimitError("component exceeds plan max_component_bytes")
    if sum(component_sizes) > plan["limits"]["max_total_bytes"]:
        raise ResourceLimitError("fixture exceeds plan max_total_bytes")
    header = observed["header"]
    if header["chain_id"] != manifest["chain_id"]:
        raise IntegrityError("header chain_id disagrees with manifest")
    if header["number"] != manifest["block"]["number"]:
        raise IntegrityError("header number disagrees with manifest")
    if header["hash"] != manifest["block"]["hash"]:
        raise IntegrityError("header hash disagrees with manifest")
    anchor_records = observed.get("anchors")
    if plan["schema_version"] == 1:
        if anchor_records is not None:
            raise IntegrityError("plan-v1 refuses anchors.jsonl")
    else:
        if anchor_records is None:
            raise IntegrityError("plan-v2 requires anchors.jsonl")
        validate_anchor_records(
            plan,
            anchor_records,
            chain_id=manifest["chain_id"],
            block_number=manifest["block"]["number"],
            block_hash=manifest["block"]["hash"],
        )
    _validate_plan_coverage(plan, observed)
    receipt_report = _receipt_report(observed)
    counts, failures = _coverage(observed, receipt_report)
    if counts != manifest["evidence_counts"]:
        raise IntegrityError("manifest evidence counts disagree with fixture records")
    if receipt_report is not None:
        if manifest["receipts_root"].lower() != receipt_report["computed_root"]:
            raise IntegrityError("manifest receipts root disagrees with verified witness")
        if counts["receipt_trie_proved"] <= 0 or manifest["receipts_root"] == "0x" + "00" * 32:
            raise IntegrityError("positive receipt proof count requires a nonzero receipts root")
    if failures != manifest["optional_failures"]:
        raise IntegrityError("manifest optional failures disagree with RPC records")


def _require_version_components(manifest: dict[str, Any], paths: list[str]) -> None:
    has_witness = "receipt-witness.json" in paths
    if manifest["schema_version"] == 1 and has_witness:
        raise IntegrityError("manifest-v1 refuses receipt-witness.json")
    if manifest["schema_version"] == 2 and not has_witness:
        raise IntegrityError("manifest-v2 requires receipt-witness.json")


def _receipt_report(observed: dict[str, Any]) -> dict[str, Any] | None:
    plan = observed["plan"]
    witness = observed.get("receipt_witness")
    if plan["schema_version"] != 3:
        if witness is not None:
            raise IntegrityError("legacy plans refuse receipt-witness.json")
        return None
    if witness is None:
        raise IntegrityError("plan-v3 requires receipt-witness.json")
    return verify_receipt_relation(
        witness,
        header=observed["header"],
        plan=plan,
        rpc_records=observed.get("rpc", []),
    )


def validate_anchor_records(
    plan: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    chain_id: str,
    block_number: str,
    block_hash: str,
) -> None:
    """Hold anchor observations to their plan and verified block identity."""
    planned = {item["source_id"] for item in plan["anchor_sources"]}
    recorded = {item["source_id"] for item in records}
    missing = sorted(planned - recorded)
    extra = sorted(recorded - planned)
    if missing or extra:
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if extra:
            detail.append("extra " + ", ".join(extra))
        raise IntegrityError(
            "anchor records do not exactly cover plan sources: "
            + "; ".join(detail)
        )
    for record in records:
        source_id = record["source_id"]
        returned = record["returned"]
        if returned["chain_id"] != chain_id:
            raise IntegrityError(f"anchor source {source_id} names another chain")
        if (
            record["params"][0] != block_number
            or returned["number"] != block_number
        ):
            raise IntegrityError(
                f"anchor source {source_id} names another block number"
            )
        if returned["hash"].lower() != block_hash.lower():
            raise IntegrityError(
                f"anchor source {source_id} disagrees with the verified header"
            )


def _validate_plan_coverage(plan: dict[str, Any], observed: dict[str, Any]) -> None:
    planned_requests = {
        request_key(item["method"], item["params"]): item
        for item in plan["requests"]
    }
    recorded_requests = {
        item["request_key"]: item for item in observed.get("rpc", [])
    }
    missing_requests = sorted(set(planned_requests) - set(recorded_requests))
    extra_requests = sorted(set(recorded_requests) - set(planned_requests))
    if missing_requests:
        raise IntegrityError(
            f"planned RPC requests are missing: {', '.join(missing_requests)}"
        )
    if extra_requests:
        raise IntegrityError(
            f"unplanned RPC requests are present: {', '.join(extra_requests)}"
        )
    for key, planned in planned_requests.items():
        recorded = recorded_requests[key]
        for field in ("name", "required", "evidence"):
            if recorded.get(field) != planned[field]:
                raise IntegrityError(
                    f"RPC record {key} {field} disagrees with the capture plan"
                )

    planned_targets = {
        item["address"].lower(): item for item in plan["proof_targets"]
    }
    recorded_proofs = {
        item["address"].lower(): item for item in observed.get("proofs", [])
    }
    missing_targets = sorted(set(planned_targets) - set(recorded_proofs))
    extra_targets = sorted(set(recorded_proofs) - set(planned_targets))
    if missing_targets:
        raise IntegrityError(
            f"planned proof targets are missing: {', '.join(missing_targets)}"
        )
    if extra_targets:
        raise IntegrityError(
            f"unplanned proof targets are present: {', '.join(extra_targets)}"
        )
    for address, target in planned_targets.items():
        proof = recorded_proofs[address]
        if proof["block_hash"] != plan["block"]["hash"]:
            raise IntegrityError(f"proof target block hash disagrees: {address}")
        planned_slots = [slot.lower() for slot in target["slots"]]
        proved_slots = [item["key"].lower() for item in proof["storage_proof"]]
        if proved_slots != planned_slots:
            raise IntegrityError(f"proof target slots disagree: {address}")
