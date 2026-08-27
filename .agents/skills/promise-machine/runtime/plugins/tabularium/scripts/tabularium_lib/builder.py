"""Build deterministic canonical JSONL from a preserved source snapshot."""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .adapters.goldfinch import map_snapshot
from .core import (
    TabulariumError,
    canonical_json,
    jsonl_bytes,
    loads_json,
    sha256_bytes,
    write_bytes_atomic,
)
from .paths import relative_artifact_path
from .release import make_manifest, validate_capture, validate_manifest
from .release_v2 import (
    adapter_module,
    make_manifest as make_manifest_v2,
    validate_capture as validate_capture_v2,
    validate_manifest as validate_manifest_v2,
)


@dataclass(frozen=True)
class BuildReport:
    rows: int
    families: dict
    unmapped_counts: dict
    sha256: str
    manifest_sha256: str


def _refuse_aliases(inputs, outputs):
    """Keep build targets from following or sharing any input or each other."""
    inputs = [Path(path) for path in inputs]
    outputs = [Path(path) for path in outputs]
    resolved_outputs = []
    for output in outputs:
        if output.is_symlink():
            raise TabulariumError("output path is a symlink; refusing to overwrite evidence")
        resolved = output.parent.resolve(strict=True) / output.name
        if resolved in resolved_outputs:
            raise TabulariumError("build outputs alias each other")
        resolved_outputs.append(resolved)
        if output.exists():
            for source in inputs:
                if source.samefile(output):
                    raise TabulariumError(
                        "output path aliases preserved input; refusing to overwrite evidence"
                    )
            for earlier in outputs:
                if earlier == output:
                    break
                if earlier.exists() and earlier.samefile(output):
                    raise TabulariumError("build outputs alias each other")


def build(source_path, capture_manifest_path, out_path, manifest_path, release, adapter="goldfinch"):
    _refuse_aliases(
        (source_path, capture_manifest_path),
        (out_path, manifest_path),
    )
    release_root = Path(manifest_path).parent.resolve(strict=True)
    source_relative = relative_artifact_path(
        release_root, source_path, "source path", must_exist=True
    )
    capture_relative = relative_artifact_path(
        release_root, capture_manifest_path, "capture manifest path", must_exist=True
    )
    canonical_relative = relative_artifact_path(
        release_root, out_path, "canonical path", must_exist=False
    )

    source_bytes = Path(source_path).read_bytes()
    capture_bytes = Path(capture_manifest_path).read_bytes()
    source = loads_json(source_bytes, "source")
    capture = loads_json(capture_bytes, "capture manifest")
    if adapter == "goldfinch":
        indexed_block = validate_capture(
            capture, capture_bytes, source, source_bytes
        )
        mapped = map_snapshot(source)
    else:
        module = adapter_module(adapter)
        _, mapped = validate_capture_v2(
            capture, source, source_bytes, expected_adapter=adapter
        )
        if capture["release"] != release:
            raise TabulariumError("capture release does not match requested release")
    data = jsonl_bytes(mapped.events)
    if adapter == "goldfinch":
        manifest = make_manifest(
            release,
            source_relative,
            source_bytes,
            capture_relative,
            capture_bytes,
            canonical_relative,
            data,
            indexed_block,
            mapped,
        )
        validate_manifest(manifest)
    else:
        manifest = make_manifest_v2(
            release,
            module.ADAPTER,
            source_relative,
            source_bytes,
            capture_relative,
            capture_bytes,
            canonical_relative,
            data,
            capture,
            mapped,
        )
        validate_manifest_v2(manifest)
    manifest_bytes = canonical_json(manifest) + b"\n"
    write_bytes_atomic(data, out_path)
    write_bytes_atomic(manifest_bytes, manifest_path)
    families = dict(Counter(event["event_family"] for event in mapped.events))
    return BuildReport(
        rows=len(mapped.events),
        families=families,
        unmapped_counts=mapped.unmapped_counts,
        sha256=sha256_bytes(data),
        manifest_sha256=sha256_bytes(manifest_bytes),
    )
