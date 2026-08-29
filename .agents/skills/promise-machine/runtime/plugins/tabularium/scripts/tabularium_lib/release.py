"""Coverage manifest v1 and capture-manifest binding."""

import re

from . import ADAPTER_VERSION, EVENT_SCHEMA_VERSION
from .adapters.goldfinch import CHAIN, MAPPINGS
from .core import MAX_SAFE_INTEGER, TabulariumError, safe_integer, sha256_bytes


MANIFEST_SCHEMA_VERSION = 1
EVIDENCE_CLASS = "hosted-indexer-reported-block"
SUPPORTED_MAPPING_RULES = tuple(sorted(mapping.rule for mapping in MAPPINGS.values()))
INCLUDED_KEYS = ("borrows", "repays")
UNSUPPORTED_KEYS = ("_meta", "callableLoans", "creditLines", "tranchedPools")
KNOWN_GAPS = (
    "source boundary is a hosted indexer's reported block, not an independently verified chain proof",
    "events do not carry an independently verified per-event block number or block hash",
    "creditLines, tranchedPools, callableLoans and _meta are not mapped as canonical events",
    "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _object(value, where):
    if not isinstance(value, dict):
        raise TabulariumError("%s is not an object" % where)
    return value


def _exact_keys(value, expected, where):
    value = _object(value, where)
    extra = sorted(set(value) - set(expected))
    missing = sorted(set(expected) - set(value))
    if extra:
        raise TabulariumError("%s has extra field(s): %s" % (where, ", ".join(extra)))
    if missing:
        raise TabulariumError("%s is missing field(s): %s" % (where, ", ".join(missing)))
    return value


def _string(value, where):
    if not isinstance(value, str) or not value:
        raise TabulariumError("%s is not a non-empty string" % where)
    return value


def _digest(value, where):
    value = _string(value, where)
    if not HEX64.fullmatch(value):
        raise TabulariumError("%s is not a lowercase SHA-256 digest" % where)
    return value


def _count_map(value, keys, where):
    value = _exact_keys(value, keys, where)
    return {key: safe_integer(value[key], "%s.%s" % (where, key)) for key in keys}


def validate_capture(capture, capture_bytes, source, source_bytes):
    """Check the preserved capture's claims against the raw source bytes."""
    capture = _object(capture, "capture manifest")
    for key in ("source", "captured", "entities", "sha256", "bytes"):
        if key not in capture:
            raise TabulariumError("capture manifest has no %r" % key)
    source_claim = _object(capture["source"], "capture manifest.source")
    captured = _object(capture["captured"], "capture manifest.captured")
    entities = _exact_keys(
        capture["entities"],
        ("borrows", "repays", "creditLines", "tranchedPools", "callableLoans"),
        "capture manifest.entities",
    )
    if source_claim.get("chain") != CHAIN:
        raise TabulariumError("capture manifest source chain is unsupported")
    source_digest = _digest(capture["sha256"], "capture manifest.sha256")
    if source_digest != sha256_bytes(source_bytes):
        raise TabulariumError("capture manifest source digest does not match source bytes")
    if safe_integer(capture["bytes"], "capture manifest.bytes") != len(source_bytes):
        raise TabulariumError("capture manifest byte count does not match source bytes")
    indexed_block = safe_integer(
        captured.get("indexed_block"), "capture manifest.captured.indexed_block"
    )
    meta = _object(source.get("_meta"), "source._meta")
    block = _object(meta.get("block"), "source._meta.block")
    if safe_integer(block.get("number"), "source._meta.block.number") != indexed_block:
        raise TabulariumError("capture manifest indexed block does not match source metadata")
    indexed_timestamp = safe_integer(
        captured.get("indexed_block_timestamp"),
        "capture manifest.captured.indexed_block_timestamp",
    )
    if (
        safe_integer(block.get("timestamp"), "source._meta.block.timestamp")
        != indexed_timestamp
    ):
        raise TabulariumError(
            "capture manifest indexed block timestamp does not match source metadata"
        )
    deployment = _string(
        captured.get("deployment"), "capture manifest.captured.deployment"
    )
    if _string(meta.get("deployment"), "source._meta.deployment") != deployment:
        raise TabulariumError(
            "capture manifest deployment does not match source metadata"
        )
    for key in ("borrows", "repays", "creditLines", "tranchedPools", "callableLoans"):
        rows = source.get(key)
        if not isinstance(rows, list):
            raise TabulariumError("source.%s is not an array" % key)
        if safe_integer(entities[key], "capture manifest.entities.%s" % key) != len(rows):
            raise TabulariumError("capture manifest %s count does not match source" % key)
    return indexed_block


def make_manifest(
    release,
    source_path,
    source_bytes,
    capture_path,
    capture_bytes,
    canonical_path,
    canonical_bytes,
    indexed_block,
    mapped,
):
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "release": _string(release, "release"),
        "source": {
            "path": source_path,
            "sha256": sha256_bytes(source_bytes),
            "bytes": len(source_bytes),
            "evidence_class": EVIDENCE_CLASS,
            "indexed_block": indexed_block,
        },
        "capture_manifest": {
            "path": capture_path,
            "sha256": sha256_bytes(capture_bytes),
            "bytes": len(capture_bytes),
        },
        "canonical": {
            "path": canonical_path,
            "sha256": sha256_bytes(canonical_bytes),
            "bytes": len(canonical_bytes),
            "rows": len(mapped.events),
        },
        "coverage": {
            "included_entities": {
                "borrows": mapped.mapped_counts["borrowing"],
                "repays": mapped.mapped_counts["repayment"],
            },
            "unsupported_entities": {
                key: mapped.unmapped_counts[key] for key in UNSUPPORTED_KEYS
            },
        },
        "versions": {
            "event_schema": EVENT_SCHEMA_VERSION,
            "adapter": {"name": "goldfinch", "version": ADAPTER_VERSION},
            "mapping_rules": list(SUPPORTED_MAPPING_RULES),
        },
        "known_gaps": list(KNOWN_GAPS),
    }


def validate_manifest(manifest):
    """Validate coverage manifest v1 without an external schema library."""
    manifest = _exact_keys(
        manifest,
        (
            "schema_version", "release", "source", "capture_manifest",
            "canonical", "coverage", "versions", "known_gaps",
        ),
        "coverage manifest",
    )
    if safe_integer(manifest["schema_version"], "coverage manifest.schema_version") != MANIFEST_SCHEMA_VERSION:
        raise TabulariumError("unsupported coverage manifest schema version")
    _string(manifest["release"], "coverage manifest.release")
    source = _exact_keys(
        manifest["source"],
        ("path", "sha256", "bytes", "evidence_class", "indexed_block"),
        "coverage manifest.source",
    )
    capture = _exact_keys(
        manifest["capture_manifest"],
        ("path", "sha256", "bytes"),
        "coverage manifest.capture_manifest",
    )
    canonical = _exact_keys(
        manifest["canonical"],
        ("path", "sha256", "bytes", "rows"),
        "coverage manifest.canonical",
    )
    for where, artifact in (
        ("source", source), ("capture_manifest", capture), ("canonical", canonical)
    ):
        _string(artifact["path"], "coverage manifest.%s.path" % where)
        _digest(artifact["sha256"], "coverage manifest.%s.sha256" % where)
        safe_integer(artifact["bytes"], "coverage manifest.%s.bytes" % where)
    if source["evidence_class"] != EVIDENCE_CLASS:
        raise TabulariumError("unsupported source evidence class")
    safe_integer(source["indexed_block"], "coverage manifest.source.indexed_block")
    safe_integer(canonical["rows"], "coverage manifest.canonical.rows")

    coverage = _exact_keys(
        manifest["coverage"],
        ("included_entities", "unsupported_entities"),
        "coverage manifest.coverage",
    )
    _count_map(coverage["included_entities"], INCLUDED_KEYS, "included_entities")
    _count_map(coverage["unsupported_entities"], UNSUPPORTED_KEYS, "unsupported_entities")

    versions = _exact_keys(
        manifest["versions"],
        ("event_schema", "adapter", "mapping_rules"),
        "coverage manifest.versions",
    )
    if safe_integer(versions["event_schema"], "versions.event_schema") != EVENT_SCHEMA_VERSION:
        raise TabulariumError("unsupported event schema version")
    adapter = _exact_keys(versions["adapter"], ("name", "version"), "versions.adapter")
    if adapter != {"name": "goldfinch", "version": ADAPTER_VERSION}:
        raise TabulariumError("unsupported adapter version")
    if versions["mapping_rules"] != list(SUPPORTED_MAPPING_RULES):
        raise TabulariumError("unsupported mapping-rule versions")
    if manifest["known_gaps"] != list(KNOWN_GAPS):
        raise TabulariumError("known semantic gaps are incomplete or unsupported")
    return manifest
