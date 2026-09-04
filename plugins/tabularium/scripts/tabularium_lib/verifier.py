"""Fail-closed, fully offline verification of a Tabularium release."""

from dataclasses import dataclass
from pathlib import Path

from .core import TabulariumError, jsonl_bytes, loads_json, sha256_bytes
from .paths import resolve_artifact_path
from .release_v2 import (
    validate_capture as validate_capture_v2,
    validate_manifest as validate_manifest_v2,
)


@dataclass(frozen=True)
class VerificationReport:
    release: str
    rows: int
    sha256: str


def _artifact_bytes(path, claim, where):
    data = path.read_bytes()
    if sha256_bytes(data) != claim["sha256"]:
        raise TabulariumError("%s digest does not match its bytes" % where)
    if len(data) != claim["bytes"]:
        raise TabulariumError("%s byte count does not match its bytes" % where)
    return data


def _parse_jsonl(data):
    if not data or not data.endswith(b"\n"):
        raise TabulariumError("canonical JSONL has no final newline")
    lines = data.split(b"\n")[:-1]
    if any(not line for line in lines):
        raise TabulariumError("canonical JSONL contains an empty row")
    return [loads_json(line, "canonical row %d" % (index + 1)) for index, line in enumerate(lines)]


def _refuse_artifact_aliases(manifest_path, artifacts):
    paths = [manifest_path, *artifacts]
    for index, left in enumerate(paths):
        for right in paths[index + 1:]:
            if left.samefile(right):
                raise TabulariumError("release artefact paths alias each other")


def _release_artifacts(manifest_path, manifest):
    release_root = manifest_path.parent.resolve(strict=True)
    source_path = resolve_artifact_path(
        release_root, manifest["source"]["path"], "source path"
    )
    capture_path = resolve_artifact_path(
        release_root,
        manifest["capture_manifest"]["path"],
        "capture manifest path",
    )
    canonical_path = resolve_artifact_path(
        release_root, manifest["canonical"]["path"], "canonical path"
    )
    _refuse_artifact_aliases(
        manifest_path.resolve(strict=True),
        (source_path, capture_path, canonical_path),
    )
    source_bytes = _artifact_bytes(source_path, manifest["source"], "source")
    capture_bytes = _artifact_bytes(
        capture_path, manifest["capture_manifest"], "capture manifest"
    )
    canonical_bytes = _artifact_bytes(
        canonical_path, manifest["canonical"], "canonical ledger"
    )
    return source_bytes, capture_bytes, canonical_bytes


def _verify_v2(manifest_path, raw_manifest):
    manifest = validate_manifest_v2(raw_manifest)
    source_bytes, capture_bytes, canonical_bytes = _release_artifacts(
        manifest_path, manifest
    )
    source = loads_json(source_bytes, "source")
    capture = loads_json(capture_bytes, "capture manifest")
    adapter_name = manifest["versions"]["adapter"]["name"]
    _, mapped = validate_capture_v2(
        capture, source, source_bytes, expected_adapter=adapter_name
    )
    if capture["release"] != manifest["release"]:
        raise TabulariumError("capture release does not match coverage manifest")
    if capture["scope"] != manifest["source"]["scope"]:
        raise TabulariumError("capture scope does not match coverage manifest")
    if manifest["coverage"]["included_events"] != mapped.mapped_counts:
        raise TabulariumError("included event counts do not match source")
    if manifest["coverage"]["unsupported_events"] != mapped.unmapped_counts:
        raise TabulariumError("unsupported event counts do not match source")
    expected_rules = sorted(
        {event["provenance"]["mapping_rule"] for event in mapped.events}
    )
    if manifest["versions"]["mapping_rules"] != expected_rules:
        raise TabulariumError("mapping-rule versions do not match source")
    rows = _parse_jsonl(canonical_bytes)
    if len(rows) != manifest["canonical"]["rows"]:
        raise TabulariumError("canonical row count does not match coverage manifest")
    selectors = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get("schema_version") != 2:
            raise TabulariumError(
                "canonical row %d does not match canonical event schema v2" % index
            )
        provenance = row.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("adapter") != adapter_name:
            raise TabulariumError(
                "canonical row %d provenance does not match its adapter" % index
            )
        selector = provenance.get("source_selector")
        if not isinstance(selector, str) or not selector:
            raise TabulariumError(
                "canonical row %d has no source selector" % index
            )
        selectors.append(selector)
    if len(selectors) != len(set(selectors)):
        raise TabulariumError("canonical ledger has duplicate source selectors")
    expected_selectors = [
        event["provenance"]["source_selector"] for event in mapped.events
    ]
    if set(selectors) != set(expected_selectors):
        raise TabulariumError(
            "canonical source selectors do not trace one-to-one to source"
        )
    if selectors != expected_selectors:
        raise TabulariumError("canonical rows are not in deterministic order")
    expected_bytes = jsonl_bytes(mapped.events)
    if canonical_bytes != expected_bytes:
        raise TabulariumError(
            "canonical bytes do not match an offline source rebuild"
        )
    if manifest["canonical"]["sha256"] != sha256_bytes(expected_bytes):
        raise TabulariumError(
            "canonical digest does not match the offline rebuild"
        )
    return VerificationReport(
        release=manifest["release"],
        rows=len(rows),
        sha256=sha256_bytes(canonical_bytes),
    )


def verify(manifest_path):
    """Verify a release from local bytes only and never write to it."""
    manifest_path = Path(manifest_path)
    if manifest_path.is_symlink():
        raise TabulariumError("coverage manifest path is a symlink")
    if not manifest_path.is_file():
        raise TabulariumError("coverage manifest is not a regular file")
    raw_manifest = loads_json(manifest_path.read_bytes(), "coverage manifest")
    if not isinstance(raw_manifest, dict):
        raise TabulariumError("coverage manifest is not an object")
    version = raw_manifest.get("schema_version")
    if version == 2:
        return _verify_v2(manifest_path, raw_manifest)
    raise TabulariumError("unsupported coverage manifest schema version")
