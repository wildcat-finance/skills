"""Build and verify deterministic Tabularium credit views."""

from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import shutil
import tempfile

from .canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes
from .errors import AlexandriaError
from .mappings import map_capture
from .mappings.common import load_source, resolve_selector
from .paths import read_confined_file, validate_relative_path
from .release import (
    ACCOUNT_RE,
    DIGEST_RE,
    MAX_RAW_COMPONENT_BYTES,
    _require_keys,
    sha256,
    verify,
)
from .rows import EVENT_FAMILIES, EVENT_SCHEMA, OBSERVATION_SCHEMA, jsonl_bytes


DERIVATION_FORMAT = "alexandria-tabularium-view/v1"
EVENTS_PATH = "credit-events.jsonl"
OBSERVATIONS_PATH = "credit-observations.jsonl"
MAX_DERIVED_BYTES = 64 * 1024 * 1024
MAX_DERIVED_ROWS = 100_000
ACCESS_ORDER = {"public": 0, "restricted": 1, "private": 2}
REDISTRIBUTION_ORDER = {"permitted": 0, "restricted": 1, "unknown": 2, "prohibited": 3}


def derive(source_release: Path, output: Path) -> str:
    """Create a new derived release without changing the verified raw release."""
    source_release = source_release.absolute()
    source_release_id = verify(source_release)
    manifest = _read_manifest(source_release)
    if "derivation" in manifest:
        raise AlexandriaError("derive requires a raw release, not an already derived release")
    read_component = component_reader(source_release, manifest)
    files, declaration = build_view(manifest, read_component, source_release_id)

    output = output.absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise AlexandriaError("output must not be a symlink")
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        for component in manifest["components"]:
            destination = temporary.joinpath(*component["object_path"].split("/"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(read_component(component["name"]))
        for path, data in files.items():
            (temporary / path).write_bytes(data)
        derived_manifest = deepcopy(manifest)
        derived_manifest.pop("release_id")
        derived_manifest["derivation"] = declaration
        release_id = sha256(canonical_bytes(derived_manifest))
        derived_manifest["release_id"] = release_id
        (temporary / "manifest.json").write_bytes(canonical_bytes(derived_manifest))
        verify(temporary)
        if output.exists():
            existing_id = verify(output)
            if existing_id != release_id:
                raise AlexandriaError("output already contains a different release")
            shutil.rmtree(temporary)
            return release_id
        os.replace(temporary, output)
        return release_id
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def build_view(manifest, read_component, source_release_id):
    events = []
    observations = []
    mappings = []
    for capture in sorted(manifest["captures"], key=lambda item: item["id"]):
        if capture["coverage"]["status"] in {"failed", "unsupported"}:
            raise AlexandriaError(f"capture {capture['id']} has no records to derive")
        data = read_component(capture["component"])
        result = map_capture(capture, data, source_release_id)
        source = load_source(data, capture)
        for row in result.events + result.observations:
            _resolve_row_selectors(row, source)
        events.extend(result.events)
        observations.extend(result.observations)
        if len(events) + len(observations) > MAX_DERIVED_ROWS:
            raise AlexandriaError(
                f"derived rows exceed the {MAX_DERIVED_ROWS}-row limit"
            )
        mappings.append(result.declaration)
    _unique_row_ids(events + observations)
    events.sort(key=_event_sort_key)
    observations.sort(key=_observation_sort_key)
    event_bytes = jsonl_bytes(events, max_bytes=MAX_DERIVED_BYTES)
    observation_bytes = jsonl_bytes(observations, max_bytes=MAX_DERIVED_BYTES)
    access = max(
        (item["access"] for item in manifest["components"]),
        key=ACCESS_ORDER.__getitem__,
    )
    redistribution = max(
        (item["redistribution"] for item in manifest["components"]),
        key=REDISTRIBUTION_ORDER.__getitem__,
    )
    outputs = {
        "credit_events": _output_descriptor(
            EVENTS_PATH, EVENT_SCHEMA, event_bytes, len(events), access, redistribution
        ),
        "credit_observations": _output_descriptor(
            OBSERVATIONS_PATH,
            OBSERVATION_SCHEMA,
            observation_bytes,
            len(observations),
            access,
            redistribution,
        ),
    }
    family_counts = {}
    subject_counts = {}
    for event in events:
        family_counts[event["event_family"]] = family_counts.get(event["event_family"], 0) + 1
        subject_counts.setdefault(event["subject"], {"events": 0, "observations": 0})["events"] += 1
    for observation in observations:
        subject_counts.setdefault(observation["subject"], {"events": 0, "observations": 0})["observations"] += 1
    declaration = {
        "counts": {
            "event_families": dict(sorted(family_counts.items())),
            "event_rows": len(events),
            "observation_rows": len(observations),
            "subjects": dict(sorted(subject_counts.items())),
        },
        "format": DERIVATION_FORMAT,
        "mappings": mappings,
        "outputs": outputs,
        "source_release_id": source_release_id,
    }
    return {EVENTS_PATH: event_bytes, OBSERVATIONS_PATH: observation_bytes}, declaration


def validate_derivation(value):
    _require_keys(
        value,
        {"format", "source_release_id", "mappings", "outputs", "counts"},
        "derivation",
    )
    if value["format"] != DERIVATION_FORMAT:
        raise AlexandriaError("derivation format is unknown")
    if not isinstance(value["source_release_id"], str) or not DIGEST_RE.fullmatch(value["source_release_id"]):
        raise AlexandriaError("derivation source_release_id must be a SHA-256 identifier")
    if not isinstance(value["mappings"], list) or not value["mappings"]:
        raise AlexandriaError("derivation mappings must be a non-empty list")
    if len(value["mappings"]) > 1024:
        raise AlexandriaError("derivation mappings exceed the 1024-item limit")
    capture_ids = []
    for mapping in value["mappings"]:
        _validate_mapping_declaration(mapping)
        capture_ids.append(mapping["capture_id"])
    if value["mappings"] != sorted(value["mappings"], key=lambda item: item["capture_id"]):
        raise AlexandriaError("derivation mappings are not in capture order")
    if len(capture_ids) != len(set(capture_ids)):
        raise AlexandriaError("derivation contains duplicate capture mappings")
    outputs = value["outputs"]
    _require_keys(outputs, {"credit_events", "credit_observations"}, "derivation outputs")
    _validate_output(outputs["credit_events"], EVENTS_PATH, EVENT_SCHEMA)
    _validate_output(outputs["credit_observations"], OBSERVATIONS_PATH, OBSERVATION_SCHEMA)
    counts = value["counts"]
    _require_keys(counts, {"event_families", "event_rows", "observation_rows", "subjects"}, "derivation counts")
    for key in ("event_rows", "observation_rows"):
        _nonnegative(counts[key], f"derivation {key}")
    if outputs["credit_events"]["rows"] != counts["event_rows"]:
        raise AlexandriaError("event output row count disagrees with derivation counts")
    if outputs["credit_observations"]["rows"] != counts["observation_rows"]:
        raise AlexandriaError("observation output row count disagrees with derivation counts")
    if not isinstance(counts["event_families"], dict) or not all(
        isinstance(key, str) and isinstance(item, int) and not isinstance(item, bool) and item >= 0
        for key, item in counts["event_families"].items()
    ):
        raise AlexandriaError("derivation event family counts are malformed")
    if not set(counts["event_families"]).issubset(EVENT_FAMILIES):
        raise AlexandriaError("derivation event family counts name an unknown family")
    if sum(counts["event_families"].values()) != counts["event_rows"]:
        raise AlexandriaError("derivation event family counts do not reconcile")
    if not isinstance(counts["subjects"], dict):
        raise AlexandriaError("derivation subject counts must be an object")
    total_events = 0
    total_observations = 0
    for subject, item in counts["subjects"].items():
        if not isinstance(subject, str) or not ACCOUNT_RE.fullmatch(subject):
            raise AlexandriaError("derivation subject key is malformed")
        _require_keys(item, {"events", "observations"}, "derivation subject count")
        _nonnegative(item["events"], "subject event count")
        _nonnegative(item["observations"], "subject observation count")
        total_events += item["events"]
        total_observations += item["observations"]
    if total_events != counts["event_rows"] or total_observations != counts["observation_rows"]:
        raise AlexandriaError("derivation subject counts do not reconcile")
    mapped_records = sum(item["coverage"]["mapped_records"] for item in value["mappings"])
    if mapped_records != counts["event_rows"] + counts["observation_rows"]:
        raise AlexandriaError("mapping coverage does not reconcile to derived rows")


def verify_derivation(release_root, manifest, read_component):
    derivation = manifest["derivation"]
    raw_body = deepcopy(manifest)
    raw_body.pop("release_id")
    raw_body.pop("derivation")
    source_release_id = sha256(canonical_bytes(raw_body))
    if derivation["source_release_id"] != source_release_id:
        raise AlexandriaError("derivation source release identity does not match the raw manifest")
    expected_files, expected = build_view(raw_body, read_component, source_release_id)
    if derivation != expected:
        raise AlexandriaError("derivation manifest does not match the registered mappings")
    for key, path in (("credit_events", EVENTS_PATH), ("credit_observations", OBSERVATIONS_PATH)):
        descriptor = derivation["outputs"][key]
        data = read_confined_file(release_root, path, path, max_bytes=MAX_DERIVED_BYTES)
        if len(data) != descriptor["bytes"] or sha256(data) != descriptor["sha256"]:
            raise AlexandriaError(f"derived output {path} size or digest does not match")
        if data != expected_files[path]:
            raise AlexandriaError(f"derived output {path} does not rebuild byte-for-byte")


def output_paths(derivation):
    return {item["path"] for item in derivation["outputs"].values()}


def _read_manifest(release_root):
    data = read_confined_file(release_root, "manifest.json", "manifest", max_bytes=MAX_CONTROL_BYTES)
    return load_bytes(data, "manifest")


def component_reader(release_root, manifest):
    """Return a digest-checking loader that does not cache component bytes."""
    components = {item["name"]: item for item in manifest["components"]}

    def read_component(name):
        item = components.get(name)
        if item is None:
            raise AlexandriaError(f"unknown component {name}")
        data = read_confined_file(
            release_root,
            item["object_path"],
            f"component {item['name']}",
            max_bytes=MAX_RAW_COMPONENT_BYTES,
        )
        if len(data) != item["bytes"] or sha256(data) != item["sha256"]:
            raise AlexandriaError(f"component {item['name']} changed while it was read")
        return data

    return read_component


def _resolve_row_selectors(row, source):
    provenance = row["provenance"]
    selectors = [provenance["source_selector"], *provenance.get("context_selectors", [])]
    for selector in selectors:
        resolve_selector(source, selector)


def _unique_row_ids(rows):
    seen = set()
    for row in rows:
        if row["id"] in seen:
            raise AlexandriaError(f"duplicate derived row identity {row['id']}")
        seen.add(row["id"])


def _event_sort_key(row):
    transaction = row.get("transaction", {})
    return (
        int(transaction.get("timestamp", "0")),
        int(transaction.get("block_number", "0")),
        transaction.get("hash", ""),
        int(transaction.get("log_index", "0")),
        row["venue"],
        row["action"],
        row["id"],
    )


def _observation_sort_key(row):
    at = row["observation"]["at"]
    return (
        int(at.get("timestamp", "0")),
        int(at.get("block_number", "0")),
        row["venue"],
        row["subject"],
        row["id"],
    )


def _output_descriptor(path, schema, data, rows, access, redistribution):
    return {
        "access": access,
        "bytes": len(data),
        "media_type": "application/x-ndjson",
        "path": path,
        "redistribution": redistribution,
        "rows": rows,
        "schema": schema,
        "sha256": sha256(data),
    }


def _validate_output(value, path, schema):
    required = {"path", "schema", "media_type", "sha256", "bytes", "rows", "access", "redistribution"}
    _require_keys(value, required, "derivation output")
    if value["path"] != path or str(validate_relative_path(value["path"], "derived output path")) != path:
        raise AlexandriaError("derived output path is not the registered path")
    if value["schema"] != schema or value["media_type"] != "application/x-ndjson":
        raise AlexandriaError("derived output schema or media type is unknown")
    if not isinstance(value["sha256"], str) or not DIGEST_RE.fullmatch(value["sha256"]):
        raise AlexandriaError("derived output digest is malformed")
    _nonnegative(value["bytes"], "derived output bytes")
    _nonnegative(value["rows"], "derived output rows")
    if (
        not isinstance(value["access"], str)
        or value["access"] not in ACCESS_ORDER
        or not isinstance(value["redistribution"], str)
        or value["redistribution"] not in REDISTRIBUTION_ORDER
    ):
        raise AlexandriaError("derived output classification is unknown")


def _validate_mapping_declaration(value):
    required = {"capture_id", "adapter", "adapter_version", "mapping_revision", "rules", "coverage"}
    _require_keys(value, required, "mapping declaration")
    for key in ("capture_id", "adapter", "adapter_version", "mapping_revision"):
        if not isinstance(value[key], str) or not value[key]:
            raise AlexandriaError(f"mapping {key} must be non-empty")
    if (
        not isinstance(value["rules"], list)
        or not value["rules"]
        or not all(isinstance(item, str) and item for item in value["rules"])
        or len(value["rules"]) != len(set(value["rules"]))
    ):
        raise AlexandriaError("mapping rules must be a non-empty unique list")
    coverage = value["coverage"]
    required_coverage = {
        "source_records", "mapped_records", "context_records", "unsupported_records",
        "mapped_collections", "context_collections", "unsupported_collections",
    }
    _require_keys(coverage, required_coverage, "mapping coverage")
    for key in ("source_records", "mapped_records", "context_records", "unsupported_records"):
        _nonnegative(coverage[key], f"mapping coverage {key}")
    for key in ("mapped_collections", "context_collections", "unsupported_collections"):
        if not isinstance(coverage[key], dict) or not all(
            isinstance(name, str) and name and isinstance(count, int)
            and not isinstance(count, bool) and count >= 0
            for name, count in coverage[key].items()
        ):
            raise AlexandriaError(f"mapping coverage {key} is malformed")
    if coverage["mapped_records"] != sum(coverage["mapped_collections"].values()):
        raise AlexandriaError("mapped collection counts do not reconcile")
    if coverage["context_records"] != sum(coverage["context_collections"].values()):
        raise AlexandriaError("context collection counts do not reconcile")
    if coverage["unsupported_records"] != sum(coverage["unsupported_collections"].values()):
        raise AlexandriaError("unsupported collection counts do not reconcile")
    if coverage["source_records"] != coverage["mapped_records"] + coverage["context_records"] + coverage["unsupported_records"]:
        raise AlexandriaError("mapping coverage does not reconcile to source records")


def _nonnegative(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AlexandriaError(f"{label} must be a non-negative integer")
