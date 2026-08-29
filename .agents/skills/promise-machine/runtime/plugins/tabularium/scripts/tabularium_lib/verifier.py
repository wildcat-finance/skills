"""Fail-closed, fully offline verification of a Tabularium release."""

from dataclasses import dataclass
from pathlib import Path

from . import ADAPTER_VERSION, EVENT_SCHEMA_VERSION
from .adapters.goldfinch import MAPPINGS, map_snapshot
from .core import TabulariumError, jsonl_bytes, loads_json, sha256_bytes
from .paths import resolve_artifact_path
from .release import (
    UNSUPPORTED_KEYS,
    validate_capture,
    validate_manifest,
)
from .release_v2 import (
    validate_capture as validate_capture_v2,
    validate_manifest as validate_manifest_v2,
)


EVENT_KEYS = frozenset(
    {
        "schema_version", "id", "event_family", "action", "venue", "chain",
        "transaction", "parties", "instrument", "asset", "amount",
        "provenance", "native_record",
    }
)
PROVENANCE_KEYS = frozenset(
    {
        "source_kind", "source_contract", "source_entity", "source_id",
        "source_selector", "mapping_rule", "adapter", "adapter_version",
    }
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


def _validate_event_versions(row, index):
    where = "canonical row %d" % index
    if not isinstance(row, dict) or set(row) != EVENT_KEYS:
        raise TabulariumError("%s does not match canonical event schema v1" % where)
    if type(row["schema_version"]) is not int or row["schema_version"] != EVENT_SCHEMA_VERSION:
        raise TabulariumError("%s uses an unsupported event schema version" % where)
    provenance = row.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != PROVENANCE_KEYS:
        raise TabulariumError("%s provenance does not match canonical event schema v1" % where)
    for key in (
        "adapter", "adapter_version", "source_entity", "source_id",
        "source_selector", "mapping_rule",
    ):
        if not isinstance(provenance[key], str):
            raise TabulariumError("%s provenance field %s is not a string" % (where, key))
    if provenance["adapter"] != "goldfinch" or provenance["adapter_version"] != ADAPTER_VERSION:
        raise TabulariumError("%s uses an unsupported adapter version" % where)
    collection = provenance["source_entity"]
    if collection not in MAPPINGS:
        raise TabulariumError("%s names an unsupported source entity" % where)
    mapping = MAPPINGS[collection]
    if provenance["mapping_rule"] != mapping.rule:
        raise TabulariumError("%s uses an unsupported mapping-rule version" % where)
    if row["event_family"] != mapping.family or row["action"] != mapping.action:
        raise TabulariumError("%s does not match its mapping rule" % where)
    expected_selector = "%s[id=%s]" % (collection, provenance["source_id"])
    if provenance["source_selector"] != expected_selector:
        raise TabulariumError("%s source selector does not match its source identifier" % where)
    return provenance["source_selector"]


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


def _verify_v1(manifest_path, raw_manifest):
    manifest = validate_manifest(raw_manifest)
    source_bytes, capture_bytes, canonical_bytes = _release_artifacts(
        manifest_path, manifest
    )

    source = loads_json(source_bytes, "source")
    capture = loads_json(capture_bytes, "capture manifest")
    indexed_block = validate_capture(capture, capture_bytes, source, source_bytes)
    if indexed_block != manifest["source"]["indexed_block"]:
        raise TabulariumError("coverage indexed block does not match capture manifest")

    mapped = map_snapshot(source)
    included = manifest["coverage"]["included_entities"]
    expected_included = {
        "borrows": mapped.mapped_counts["borrowing"],
        "repays": mapped.mapped_counts["repayment"],
    }
    if included != expected_included:
        raise TabulariumError("included entity counts do not match source")
    unsupported = manifest["coverage"]["unsupported_entities"]
    expected_unsupported = {
        key: mapped.unmapped_counts[key] for key in UNSUPPORTED_KEYS
    }
    if unsupported != expected_unsupported:
        raise TabulariumError("unsupported entity counts do not match source")

    rows = _parse_jsonl(canonical_bytes)
    if len(rows) != manifest["canonical"]["rows"]:
        raise TabulariumError("canonical row count does not match coverage manifest")
    selectors = [
        _validate_event_versions(row, index)
        for index, row in enumerate(rows, start=1)
    ]
    if len(selectors) != len(set(selectors)):
        raise TabulariumError("canonical ledger has duplicate source selectors")
    expected_selectors = [
        event["provenance"]["source_selector"] for event in mapped.events
    ]
    if set(selectors) != set(expected_selectors):
        raise TabulariumError("canonical source selectors do not trace one-to-one to source")
    if selectors != expected_selectors:
        raise TabulariumError("canonical rows are not in deterministic order")

    expected_bytes = jsonl_bytes(mapped.events)
    if canonical_bytes != expected_bytes:
        raise TabulariumError("canonical bytes do not match an offline source rebuild")
    if manifest["canonical"]["sha256"] != sha256_bytes(expected_bytes):
        raise TabulariumError("canonical digest does not match the offline rebuild")
    return VerificationReport(
        release=manifest["release"],
        rows=len(rows),
        sha256=sha256_bytes(canonical_bytes),
    )


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
    if version == 1:
        return _verify_v1(manifest_path, raw_manifest)
    if version == 2:
        return _verify_v2(manifest_path, raw_manifest)
    raise TabulariumError("unsupported coverage manifest schema version")
