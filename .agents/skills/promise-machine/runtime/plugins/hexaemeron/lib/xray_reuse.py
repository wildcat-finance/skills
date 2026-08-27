#!/usr/bin/env python3
"""Reuse bounded per-source preparation facts between complete X-Ray runs.

The adapter owns three transitions: ``plan`` determines which declared sources
need fresh extraction, ``assemble`` combines those fresh entries with still
valid cache entries and rebuilds global synthesis inputs, and ``promote``
replaces the cache only after all four X-Ray outputs can be digest-bound.

JSON and source bytes are untrusted. Every accepted object has a closed schema,
every collection and string is capped, duplicate JSON keys are refused, source
paths stay beneath a symlink-free project root, and durable replacement uses a
same-directory temporary file plus ``os.replace``. Invalid cache bytes are a
named full-recompute reason; invalid current scope or fresh model output is a
hard refusal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


SCOPE_SCHEMA = "hexaemeron.xray.scope.v1"
ENTRY_SCHEMA = "hexaemeron.xray.preparation-entry.v2"
PLAN_SCHEMA = "hexaemeron.xray.reuse-plan.v1"
CANDIDATE_SCHEMA = "hexaemeron.xray.candidate.v2"
CACHE_SCHEMA = "hexaemeron.xray.cache.v2"
OUTPUT_MANIFEST_SCHEMA = "hexaemeron.xray.output-manifest.v1"
RESULT_SCHEMA = "hexaemeron.xray.reuse-result.v1"

FINAL_OUTPUTS = (
    "architecture.json",
    "entry-points.md",
    "invariants.md",
    "x-ray.md",
)
OUTPUT_MANIFEST_NAME = "xray-output-manifest.json"
FACT_KEYS = (
    "access",
    "calls",
    "declarations",
    "entry_points",
    "fund_flows",
    "guards",
    "imports",
    "inheritance",
    "invariant_inputs",
    "key_logic",
    "roles",
    "state_facts",
    "transitions",
    "types",
    "value_facts",
    "writes",
)

MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_TOTAL_FRESH_JSON_BYTES = MAX_JSON_BYTES
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_SOURCE_BYTES = 32 * 1024 * 1024
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
MAX_SOURCES = 512
MAX_DEPENDENCIES = 512
MAX_FACTS_PER_KIND = 4096
MAX_TEXT_BYTES = 8192
MAX_IDENTITY_BYTES = 256
SHA256_HEX_LENGTH = 64
FULL_RECOMPUTE_REASONS = frozenset(
    {
        "cache-invalid",
        "cache-missing",
        "dependency-cycle",
        "identity-drift",
        "scope-mismatch",
    }
)
PLAN_REASONS = FULL_RECOMPUTE_REASONS | frozenset(
    {
        "scope-unchanged",
        "source-drift",
    }
)


class ReuseError(ValueError):
    """A bounded refusal carrying a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _refuse(code: str, message: str) -> None:
    raise ReuseError(code, message)


def _filesystem_path(
    value: os.PathLike[str] | str,
    label: str,
    *,
    code: str = "unsafe-path",
) -> Path:
    """Return one representable, NUL-free filesystem path."""
    try:
        found = Path(value)
        encoded = os.fsencode(found)
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        _refuse(code, f"{label} is not a valid filesystem path: {exc}")
    if b"\x00" in encoded:
        _refuse(code, f"{label} contains a NUL byte")
    return found


def _reject_constant(token: str) -> None:
    _refuse("invalid-json", f"non-standard JSON constant {token!r} is not permitted")


def _unique_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    found: dict[str, Any] = {}
    for key, value in pairs:
        if key in found:
            _refuse("duplicate-json-key", f"JSON key {key!r} appears twice")
        found[key] = value
    return found


def _read_regular(path: Path, limit: int, label: str) -> bytes:
    """Read one regular, non-symlink file through a bounded descriptor."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        _refuse("missing-file", f"{label} does not exist: {path}")
    except OSError as exc:
        _refuse("unreadable-file", f"{label} cannot be inspected: {exc}")
    if stat.S_ISLNK(info.st_mode):
        _refuse("unsafe-path", f"{label} must not be a symlink: {path}")
    if not stat.S_ISREG(info.st_mode):
        _refuse("unsafe-path", f"{label} must be a regular file: {path}")
    if info.st_size > limit:
        _refuse("size-limit", f"{label} exceeds {limit} bytes: {path}")

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        _refuse("unreadable-file", f"{label} cannot be opened: {exc}")
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            _refuse("unsafe-path", f"{label} changed type while opening: {path}")
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            _refuse("path-race", f"{label} changed while opening: {path}")
        if opened.st_size > limit:
            _refuse("size-limit", f"{label} exceeds {limit} bytes: {path}")
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                _refuse("size-limit", f"{label} exceeds {limit} bytes: {path}")
        return b"".join(chunks)
    except ReuseError:
        raise
    except OSError as exc:
        _refuse("unreadable-file", f"{label} cannot be read: {exc}")
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass


def _decode_json(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _refuse("invalid-json", f"{label} is not UTF-8 JSON")
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except ReuseError:
        raise
    except (ValueError, RecursionError) as exc:
        _refuse("invalid-json", f"{label} is not readable JSON: {exc}")


def load_json(path: os.PathLike[str] | str, label: str = "JSON") -> Any:
    """Load one bounded JSON document with duplicate-key rejection."""
    return _decode_json(
        _read_regular(
            _filesystem_path(path, f"{label} path"),
            MAX_JSON_BYTES,
            label,
        ),
        label,
    )


def _closed_object(
    value: Any,
    required: Iterable[str],
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _refuse("invalid-schema", f"{label} must be an object")
    if any(not isinstance(key, str) for key in value):
        _refuse("invalid-schema", f"{label} field names must be strings")
    expected = set(required)
    actual = set(value)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        _refuse("invalid-schema", f"{label} is missing {', '.join(missing)}")
    if extra:
        _refuse("invalid-schema", f"{label} has unknown fields: {', '.join(extra)}")
    return value


def _text(value: Any, label: str, *, maximum: int = MAX_TEXT_BYTES) -> str:
    if not isinstance(value, str) or not value.strip():
        _refuse("invalid-schema", f"{label} must be a non-empty string")
    if "\x00" in value:
        _refuse("invalid-schema", f"{label} contains a NUL byte")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        _refuse("invalid-unicode", f"{label} is not valid Unicode text")
    if len(encoded) > maximum:
        _refuse("size-limit", f"{label} exceeds {maximum} UTF-8 bytes")
    return value


def _assert_distinct_paths(
    roles: Sequence[tuple[str, os.PathLike[str] | str | None]],
) -> None:
    """Refuse one pathname or existing file identity serving two artefact roles."""
    by_path: dict[str, str] = {}
    by_inode: dict[tuple[int, int], str] = {}
    for label, raw in roles:
        if raw is None:
            continue
        supplied = _filesystem_path(raw, f"{label} path")
        if not supplied.name or supplied.name in (".", ".."):
            _refuse("unsafe-path", f"{label} path must name a file")
        try:
            resolved = supplied.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            _refuse("unsafe-path", f"{label} path cannot be resolved: {exc}")
        key = os.path.normcase(str(resolved))
        previous = by_path.get(key)
        if previous is not None:
            _refuse("path-alias", f"{label} path aliases {previous} path")
        by_path[key] = label
        try:
            info = resolved.stat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            _refuse("unsafe-path", f"{label} path cannot be inspected: {exc}")
        inode = (info.st_dev, info.st_ino)
        previous = by_inode.get(inode)
        if previous is not None:
            _refuse("path-alias", f"{label} path aliases {previous} file")
        by_inode[inode] = label


def _source_path_roles(
    project_root: os.PathLike[str] | str,
    sources: Sequence[Mapping[str, Any]],
) -> tuple[tuple[str, Path], ...]:
    root = _safe_project_root(project_root)
    return tuple(
        (
            f"source {source['path']}",
            root.joinpath(*PurePosixPath(source["path"]).parts),
        )
        for source in sources
    )


def _digest(value: Any, label: str) -> str:
    found = _text(value, label, maximum=SHA256_HEX_LENGTH)
    if len(found) != SHA256_HEX_LENGTH or any(
        char not in "0123456789abcdef" for char in found
    ):
        _refuse("invalid-schema", f"{label} must be a lowercase SHA-256 digest")
    return found


def canonical_digest(value: Any) -> str:
    """Digest one validated JSON value with a stable canonical encoding."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_path(value: Any, label: str) -> str:
    found = _text(value, label, maximum=1024)
    if "\\" in found:
        _refuse("unsafe-path", f"{label} must use POSIX separators")
    path = PurePosixPath(found)
    if path.is_absolute() or found.startswith("/"):
        _refuse("unsafe-path", f"{label} must be relative")
    if not path.parts or any(part in ("", ".", "..") for part in path.parts):
        _refuse("unsafe-path", f"{label} contains an unsafe path segment")
    if path.suffix != ".sol":
        _refuse("invalid-schema", f"{label} must name a Solidity source")
    return path.as_posix()


def _identity(value: Any, label: str = "identity") -> dict[str, str]:
    item = _closed_object(
        value,
        ("analyzer", "config_sha256", "instruction_sha256"),
        label,
    )
    return {
        "analyzer": _text(
            item["analyzer"], f"{label}.analyzer", maximum=MAX_IDENTITY_BYTES
        ),
        "config_sha256": _digest(
            item["config_sha256"], f"{label}.config_sha256"
        ),
        "instruction_sha256": _digest(
            item["instruction_sha256"], f"{label}.instruction_sha256"
        ),
    }


def validate_scope(value: Any) -> dict[str, Any]:
    """Validate and canonicalise one operator-declared scope manifest."""
    item = _closed_object(
        value,
        (
            "analyzer",
            "config_sha256",
            "instruction_sha256",
            "schema",
            "sources",
        ),
        "scope",
    )
    if item["schema"] != SCOPE_SCHEMA:
        _refuse("invalid-schema", f"scope.schema must equal {SCOPE_SCHEMA}")
    identity = _identity(
        {
            "analyzer": item["analyzer"],
            "config_sha256": item["config_sha256"],
            "instruction_sha256": item["instruction_sha256"],
        },
        "scope",
    )
    sources = item["sources"]
    if not isinstance(sources, list) or not sources:
        _refuse("invalid-schema", "scope.sources must be a non-empty array")
    if len(sources) > MAX_SOURCES:
        _refuse("size-limit", f"scope.sources exceeds {MAX_SOURCES} entries")

    normal: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(sources):
        source = _closed_object(raw, ("dependencies", "path"), f"scope.sources[{index}]")
        path = _source_path(source["path"], f"scope.sources[{index}].path")
        if path in seen:
            _refuse("duplicate-source", f"scope source appears twice: {path}")
        seen.add(path)
        dependencies = source["dependencies"]
        if not isinstance(dependencies, list):
            _refuse(
                "invalid-schema",
                f"scope.sources[{index}].dependencies must be an array",
            )
        if len(dependencies) > MAX_DEPENDENCIES:
            _refuse(
                "size-limit",
                f"scope.sources[{index}].dependencies exceeds {MAX_DEPENDENCIES}",
            )
        found_dependencies: list[str] = []
        dependency_seen: set[str] = set()
        for dependency_index, raw_dependency in enumerate(dependencies):
            dependency = _source_path(
                raw_dependency,
                f"scope.sources[{index}].dependencies[{dependency_index}]",
            )
            if dependency in dependency_seen:
                _refuse(
                    "duplicate-dependency",
                    f"scope dependency appears twice for {path}: {dependency}",
                )
            dependency_seen.add(dependency)
            found_dependencies.append(dependency)
        normal.append({"path": path, "dependencies": sorted(found_dependencies)})

    unknown = sorted(
        {
            dependency
            for source in normal
            for dependency in source["dependencies"]
            if dependency not in seen
        }
    )
    if unknown:
        _refuse(
            "unknown-dependency",
            "scope dependencies are absent from the current source set: "
            + ", ".join(unknown),
        )
    return {
        "schema": SCOPE_SCHEMA,
        **identity,
        "sources": sorted(normal, key=lambda entry: entry["path"]),
    }


def _safe_project_root(project_root: os.PathLike[str] | str) -> Path:
    supplied = _filesystem_path(
        project_root,
        "project root",
        code="unsafe-project-root",
    )
    try:
        info = supplied.lstat()
    except OSError as exc:
        _refuse("unsafe-project-root", f"project root cannot be inspected: {exc}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _refuse("unsafe-project-root", "project root must be a real directory")
    try:
        return supplied.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        _refuse("unsafe-project-root", f"project root cannot be resolved: {exc}")


def _read_source(root: Path, relative: str) -> bytes:
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = current.lstat()
        except OSError as exc:
            _refuse("unreadable-source", f"source {relative} cannot be inspected: {exc}")
        if stat.S_ISLNK(info.st_mode):
            _refuse("unsafe-path", f"source path crosses a symlink: {relative}")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            _refuse("unsafe-path", f"source parent is not a directory: {relative}")
    try:
        current.resolve(strict=True).relative_to(root)
    except (OSError, RuntimeError, ValueError):
        _refuse("unsafe-path", f"source escapes the project root: {relative}")
    return _read_regular(current, MAX_SOURCE_BYTES, f"source {relative}")


def materialize_scope(
    project_root: os.PathLike[str] | str,
    scope: Any,
) -> dict[str, Any]:
    """Validate a scope, read every declared source, and bind byte digests."""
    root = _safe_project_root(project_root)
    normal = validate_scope(scope)
    total = 0
    sources: list[dict[str, Any]] = []
    for source in normal["sources"]:
        raw = _read_source(root, source["path"])
        total += len(raw)
        if total > MAX_TOTAL_SOURCE_BYTES:
            _refuse(
                "size-limit",
                f"declared sources exceed {MAX_TOTAL_SOURCE_BYTES} total bytes",
            )
        sources.append(
            {
                "path": source["path"],
                "dependencies": source["dependencies"],
                "source_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return {
        "identity": {
            "analyzer": normal["analyzer"],
            "config_sha256": normal["config_sha256"],
            "instruction_sha256": normal["instruction_sha256"],
        },
        "sources": sources,
    }


def _snapshot(value: Any, label: str = "sources") -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        _refuse("invalid-schema", f"{label} must be a non-empty array")
    if len(value) > MAX_SOURCES:
        _refuse("size-limit", f"{label} exceeds {MAX_SOURCES} entries")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(value):
        source = _closed_object(
            raw,
            ("dependencies", "path", "source_sha256"),
            f"{label}[{index}]",
        )
        path = _source_path(source["path"], f"{label}[{index}].path")
        if path in seen:
            _refuse("duplicate-source", f"{label} repeats {path}")
        seen.add(path)
        dependencies = source["dependencies"]
        if not isinstance(dependencies, list) or len(dependencies) > MAX_DEPENDENCIES:
            _refuse("invalid-schema", f"{label}[{index}].dependencies is invalid")
        normal_dependencies = [
            _source_path(dep, f"{label}[{index}].dependencies") for dep in dependencies
        ]
        if len(set(normal_dependencies)) != len(normal_dependencies):
            _refuse("duplicate-dependency", f"{label}[{index}] repeats a dependency")
        result.append(
            {
                "path": path,
                "dependencies": sorted(normal_dependencies),
                "source_sha256": _digest(
                    source["source_sha256"], f"{label}[{index}].source_sha256"
                ),
            }
        )
    paths = {source["path"] for source in result}
    unknown = sorted(
        dependency
        for source in result
        for dependency in source["dependencies"]
        if dependency not in paths
    )
    if unknown:
        _refuse("unknown-dependency", f"{label} has unknown dependencies: {', '.join(unknown)}")
    return sorted(result, key=lambda source: source["path"])


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        _refuse("invalid-schema", f"{label} must be an array")
    if len(value) > MAX_FACTS_PER_KIND:
        _refuse("size-limit", f"{label} exceeds {MAX_FACTS_PER_KIND} entries")
    found = [_text(item, f"{label}[{index}]") for index, item in enumerate(value)]
    if len(set(found)) != len(found):
        _refuse("duplicate-fact", f"{label} contains duplicate facts")
    return sorted(found)


def validate_facts(value: Any, label: str = "facts") -> dict[str, Any]:
    """Validate every reusable source-bound input required by pinned X-Ray."""
    facts = _closed_object(value, FACT_KEYS, label)
    result: dict[str, Any] = {
        key: _string_list(facts[key], f"{label}.{key}")
        for key in FACT_KEYS
        if key != "writes"
    }
    writes = facts["writes"]
    if not isinstance(writes, list):
        _refuse("invalid-schema", f"{label}.writes must be an array")
    if len(writes) > MAX_FACTS_PER_KIND:
        _refuse("size-limit", f"{label}.writes exceeds {MAX_FACTS_PER_KIND} entries")
    normal_writes: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, raw in enumerate(writes):
        write = _closed_object(
            raw,
            ("delta", "site", "variable"),
            f"{label}.writes[{index}]",
        )
        item = (
            _text(write["variable"], f"{label}.writes[{index}].variable"),
            _text(write["site"], f"{label}.writes[{index}].site"),
            _text(write["delta"], f"{label}.writes[{index}].delta"),
        )
        if item in seen:
            _refuse("duplicate-fact", f"{label}.writes contains duplicate records")
        seen.add(item)
        normal_writes.append(
            {"variable": item[0], "site": item[1], "delta": item[2]}
        )
    result["writes"] = sorted(
        normal_writes,
        key=lambda write: (write["variable"], write["site"], write["delta"]),
    )
    return {key: result[key] for key in FACT_KEYS}


def validate_entry(
    value: Any,
    expected_identity: Mapping[str, str] | None = None,
    expected_source: Mapping[str, Any] | None = None,
    label: str = "entry",
    expected_sources: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate one source-bound, model-produced preparation entry."""
    entry = _closed_object(
        value,
        (
            "analyzer",
            "config_sha256",
            "dependency_digests",
            "dependencies",
            "facts",
            "instruction_sha256",
            "path",
            "schema",
            "source_sha256",
        ),
        label,
    )
    if entry["schema"] != ENTRY_SCHEMA:
        _refuse("invalid-schema", f"{label}.schema must equal {ENTRY_SCHEMA}")
    identity = _identity(
        {
            "analyzer": entry["analyzer"],
            "config_sha256": entry["config_sha256"],
            "instruction_sha256": entry["instruction_sha256"],
        },
        label,
    )
    path = _source_path(entry["path"], f"{label}.path")
    dependencies = entry["dependencies"]
    if not isinstance(dependencies, list) or len(dependencies) > MAX_DEPENDENCIES:
        _refuse("invalid-schema", f"{label}.dependencies must be a bounded array")
    normal_dependencies = [
        _source_path(dependency, f"{label}.dependencies")
        for dependency in dependencies
    ]
    if len(set(normal_dependencies)) != len(normal_dependencies):
        _refuse("duplicate-dependency", f"{label}.dependencies contains duplicates")
    dependency_digests = _dependency_digest_list(
        entry["dependency_digests"], f"{label}.dependency_digests"
    )
    normal = {
        "schema": ENTRY_SCHEMA,
        "path": path,
        "source_sha256": _digest(entry["source_sha256"], f"{label}.source_sha256"),
        **identity,
        "dependencies": sorted(normal_dependencies),
        "dependency_digests": dependency_digests,
        "facts": validate_facts(entry["facts"], f"{label}.facts"),
    }
    if expected_identity is not None and identity != dict(expected_identity):
        _refuse("entry-identity-mismatch", f"{label} analyzer identity is stale")
    if expected_source is not None:
        expected = {
            "path": expected_source["path"],
            "source_sha256": expected_source["source_sha256"],
            "dependencies": list(expected_source["dependencies"]),
        }
        actual = {
            "path": normal["path"],
            "source_sha256": normal["source_sha256"],
            "dependencies": normal["dependencies"],
        }
        if actual != expected:
            _refuse("entry-source-mismatch", f"{label} is not bound to the current source")
    if expected_sources is not None:
        expected_digests = dependency_digests_for(path, expected_sources)
        if dependency_digests != expected_digests:
            _refuse(
                "entry-dependency-mismatch",
                f"{label} is not bound to current transitive dependency bytes",
            )
    return normal


def _dependency_digest_list(value: Any, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > MAX_SOURCES:
        _refuse("invalid-schema", f"{label} must be a bounded array")
    found: dict[str, str] = {}
    for index, raw in enumerate(value):
        item = _closed_object(
            raw, ("path", "source_sha256"), f"{label}[{index}]"
        )
        path = _source_path(item["path"], f"{label}[{index}].path")
        if path in found:
            _refuse("duplicate-dependency", f"{label} repeats {path}")
        found[path] = _digest(
            item["source_sha256"], f"{label}[{index}].source_sha256"
        )
    return [
        {"path": path, "source_sha256": found[path]} for path in sorted(found)
    ]


def dependency_digests_for(
    path: str,
    sources: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    """Return the source digest of every transitive dependency of ``path``."""
    by_path = {source["path"]: source for source in sources}
    if path not in by_path:
        _refuse("scope-mismatch", f"dependency root is absent from scope: {path}")
    found: set[str] = set()
    frontier = list(by_path[path]["dependencies"])
    while frontier:
        dependency = frontier.pop()
        if dependency == path or dependency in found:
            continue
        source = by_path.get(dependency)
        if source is None:
            _refuse("unknown-dependency", f"dependency is absent from scope: {dependency}")
        found.add(dependency)
        frontier.extend(source["dependencies"])
    return [
        {"path": dependency, "source_sha256": by_path[dependency]["source_sha256"]}
        for dependency in sorted(found)
    ]


def rebuild_synthesis(entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Rebuild complete source-bound inputs from the exact current union."""
    ordered = sorted(entries, key=lambda entry: entry["path"])
    write_map: dict[str, list[dict[str, str]]] = {}
    property_inputs: list[dict[str, Any]] = []
    call_inputs: list[dict[str, Any]] = []
    transition_inputs: list[dict[str, Any]] = []
    for entry in ordered:
        for write in entry["facts"]["writes"]:
            write_map.setdefault(write["variable"], []).append(
                {
                    "path": entry["path"],
                    "site": write["site"],
                    "delta": write["delta"],
                }
            )
        property_inputs.append(
            {
                "path": entry["path"],
                "inputs": list(entry["facts"]["invariant_inputs"]),
            }
        )
        call_inputs.append(
            {"path": entry["path"], "calls": list(entry["facts"]["calls"])}
        )
        transition_inputs.append(
            {
                "path": entry["path"],
                "transitions": list(entry["facts"]["transitions"]),
            }
        )
    return {
        "source_inventory": [entry["path"] for entry in ordered],
        "source_inputs": [
            {"path": entry["path"], "facts": entry["facts"]}
            for entry in ordered
        ],
        "write_sites": [
            {
                "variable": variable,
                "sites": sorted(
                    sites,
                    key=lambda site: (site["path"], site["site"], site["delta"]),
                ),
            }
            for variable, sites in sorted(write_map.items())
        ],
        "property_inputs": property_inputs,
        "call_inputs": call_inputs,
        "transition_inputs": transition_inputs,
    }


def _validate_synthesis(
    value: Any,
    entries: Sequence[Mapping[str, Any]],
    label: str,
) -> dict[str, Any]:
    expected = rebuild_synthesis(entries)
    if value != expected:
        _refuse("stale-synthesis", f"{label} is not the synthesis of its current entries")
    return expected


def _validate_outputs(value: Any, label: str) -> dict[str, str]:
    outputs = _closed_object(value, FINAL_OUTPUTS, label)
    return {name: _digest(outputs[name], f"{label}.{name}") for name in FINAL_OUTPUTS}


def validate_candidate(value: Any) -> dict[str, Any]:
    candidate = _closed_object(
        value,
        ("entries", "identity", "schema", "sources", "synthesis"),
        "candidate",
    )
    if candidate["schema"] != CANDIDATE_SCHEMA:
        _refuse("invalid-schema", f"candidate.schema must equal {CANDIDATE_SCHEMA}")
    identity = _identity(candidate["identity"], "candidate.identity")
    sources = _snapshot(candidate["sources"], "candidate.sources")
    entries = _entries_for_snapshot(candidate["entries"], identity, sources, "candidate.entries")
    synthesis = _validate_synthesis(candidate["synthesis"], entries, "candidate.synthesis")
    return {
        "schema": CANDIDATE_SCHEMA,
        "identity": identity,
        "sources": sources,
        "entries": entries,
        "synthesis": synthesis,
    }


def _entries_for_snapshot(
    value: Any,
    identity: Mapping[str, str],
    sources: Sequence[Mapping[str, Any]],
    label: str,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(sources):
        _refuse("incomplete-entry-set", f"{label} must cover the exact source inventory")
    by_path = {source["path"]: source for source in sources}
    found: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(value):
        entry = validate_entry(raw, identity, None, f"{label}[{index}]")
        if entry["path"] in found:
            _refuse("duplicate-source", f"{label} repeats {entry['path']}")
        expected = by_path.get(entry["path"])
        if expected is None:
            _refuse("scope-mismatch", f"{label} contains removed source {entry['path']}")
        validate_entry(entry, identity, expected, f"{label}[{index}]", sources)
        found[entry["path"]] = entry
    missing = sorted(set(by_path) - set(found))
    if missing:
        _refuse("incomplete-entry-set", f"{label} is missing {', '.join(missing)}")
    return [found[path] for path in sorted(found)]


def validate_cache(value: Any) -> dict[str, Any]:
    cache = _closed_object(
        value,
        ("entries", "identity", "outputs", "schema", "sources", "synthesis"),
        "cache",
    )
    if cache["schema"] != CACHE_SCHEMA:
        _refuse("invalid-schema", f"cache.schema must equal {CACHE_SCHEMA}")
    identity = _identity(cache["identity"], "cache.identity")
    sources = _snapshot(cache["sources"], "cache.sources")
    entries = _entries_for_snapshot(cache["entries"], identity, sources, "cache.entries")
    synthesis = _validate_synthesis(cache["synthesis"], entries, "cache.synthesis")
    outputs = _validate_outputs(cache["outputs"], "cache.outputs")
    return {
        "schema": CACHE_SCHEMA,
        "identity": identity,
        "sources": sources,
        "entries": entries,
        "synthesis": synthesis,
        "outputs": outputs,
    }


def _has_cycle(sources: Sequence[Mapping[str, Any]]) -> bool:
    graph = {source["path"]: source["dependencies"] for source in sources}
    state: dict[str, int] = {}

    def visit(path: str) -> bool:
        marker = state.get(path, 0)
        if marker == 1:
            return True
        if marker == 2:
            return False
        state[path] = 1
        if any(visit(dependency) for dependency in graph[path]):
            return True
        state[path] = 2
        return False

    return any(visit(path) for path in sorted(graph) if state.get(path, 0) == 0)


def _reverse_closure(
    sources: Sequence[Mapping[str, Any]],
    roots: Iterable[str],
) -> set[str]:
    reverse: dict[str, set[str]] = {source["path"]: set() for source in sources}
    for source in sources:
        for dependency in source["dependencies"]:
            reverse[dependency].add(source["path"])
    found = set(roots)
    frontier = list(roots)
    while frontier:
        current = frontier.pop()
        for dependant in sorted(reverse.get(current, ())):
            if dependant not in found:
                found.add(dependant)
                frontier.append(dependant)
    return found


def _full_plan(
    current: Mapping[str, Any],
    reason: str,
    removed: Sequence[str] = (),
) -> dict[str, Any]:
    paths = [source["path"] for source in current["sources"]]
    return {
        "schema": PLAN_SCHEMA,
        "mode": "full",
        "reason": reason,
        "identity": current["identity"],
        "sources": current["sources"],
        "changed": paths,
        "dirty": paths,
        "reusable": [],
        "removed": sorted(removed),
        "reverse_invalidated": [],
    }


def plan(
    project_root: os.PathLike[str] | str,
    scope: Any,
    cache_path: os.PathLike[str] | str | None = None,
) -> dict[str, Any]:
    """Return a complete current extraction plan.

    Cache absence, corruption, incompleteness, identity drift, or a cyclic
    dependency declaration returns ``mode: full``. Unsafe or unreadable current
    scope and source input raises :class:`ReuseError` instead.
    """
    current = materialize_scope(project_root, scope)
    if _has_cycle(current["sources"]):
        return _full_plan(current, "dependency-cycle")
    if cache_path is None:
        return _full_plan(current, "cache-missing")
    cache_file = _filesystem_path(cache_path, "cache path")
    if not cache_file.exists():
        return _full_plan(current, "cache-missing")
    try:
        cache = validate_cache(load_json(cache_file, "X-Ray reuse cache"))
    except ReuseError:
        return _full_plan(current, "cache-invalid")

    old_paths = {source["path"] for source in cache["sources"]}
    current_paths = {source["path"] for source in current["sources"]}
    removed = sorted(old_paths - current_paths)
    if old_paths != current_paths:
        return _full_plan(current, "scope-mismatch", removed)
    if cache["identity"] != current["identity"]:
        return _full_plan(current, "identity-drift", removed)

    old = {source["path"]: source for source in cache["sources"]}
    changed = {
        source["path"]
        for source in current["sources"]
        if source["path"] not in old
        or source["source_sha256"] != old[source["path"]]["source_sha256"]
        or source["dependencies"] != old[source["path"]]["dependencies"]
    }
    closure = _reverse_closure(current["sources"], changed)
    reverse_invalidated = closure - changed
    reusable = current_paths - closure
    reason = "scope-unchanged" if not closure and not removed else "source-drift"
    return {
        "schema": PLAN_SCHEMA,
        "mode": "incremental",
        "reason": reason,
        "identity": current["identity"],
        "sources": current["sources"],
        "changed": sorted(changed),
        "dirty": sorted(closure),
        "reusable": sorted(reusable),
        "removed": removed,
        "reverse_invalidated": sorted(reverse_invalidated),
    }


def validate_plan(value: Any) -> dict[str, Any]:
    item = _closed_object(
        value,
        (
            "changed",
            "dirty",
            "identity",
            "mode",
            "reason",
            "removed",
            "reusable",
            "reverse_invalidated",
            "schema",
            "sources",
        ),
        "plan",
    )
    if item["schema"] != PLAN_SCHEMA:
        _refuse("invalid-schema", f"plan.schema must equal {PLAN_SCHEMA}")
    mode = _text(item["mode"], "plan.mode", maximum=16)
    if mode not in ("full", "incremental"):
        _refuse("invalid-schema", "plan.mode must be full or incremental")
    reason = _text(item["reason"], "plan.reason", maximum=128)
    if reason not in PLAN_REASONS:
        _refuse("invalid-schema", "plan.reason is not a declared planner result")
    identity = _identity(item["identity"], "plan.identity")
    sources = _snapshot(item["sources"], "plan.sources")
    current_paths = {source["path"] for source in sources}

    def paths(name: str, *, current_only: bool) -> list[str]:
        raw = item[name]
        if not isinstance(raw, list) or len(raw) > MAX_SOURCES:
            _refuse("invalid-schema", f"plan.{name} must be a bounded array")
        found = [_source_path(path, f"plan.{name}") for path in raw]
        if len(set(found)) != len(found):
            _refuse("duplicate-source", f"plan.{name} repeats a source")
        if current_only and not set(found).issubset(current_paths):
            _refuse("scope-mismatch", f"plan.{name} contains an absent source")
        return sorted(found)

    changed = paths("changed", current_only=True)
    dirty = paths("dirty", current_only=True)
    reusable = paths("reusable", current_only=True)
    removed = paths("removed", current_only=False)
    reverse_invalidated = paths("reverse_invalidated", current_only=True)
    if set(dirty) & set(reusable) or set(dirty) | set(reusable) != current_paths:
        _refuse("incomplete-plan", "plan dirty and reusable sets must partition scope")
    if not set(changed).issubset(dirty):
        _refuse("incomplete-plan", "plan.changed must be a subset of plan.dirty")
    if not set(reverse_invalidated).issubset(set(dirty) - set(changed)):
        _refuse(
            "incomplete-plan",
            "plan.reverse_invalidated must be dirty and not directly changed",
        )
    if set(removed) & current_paths:
        _refuse("scope-mismatch", "plan.removed overlaps current scope")
    if reason == "scope-unchanged" and (
        mode != "incremental"
        or changed
        or dirty
        or set(reusable) != current_paths
        or removed
        or reverse_invalidated
    ):
        _refuse(
            "incomplete-plan",
            "scope-unchanged requires the exact empty-drift incremental plan",
        )
    if reason == "source-drift":
        closure = _reverse_closure(sources, changed)
        if (
            mode != "incremental"
            or not changed
            or set(dirty) != closure
            or set(reusable) != current_paths - closure
            or removed
            or set(reverse_invalidated) != closure - set(changed)
        ):
            _refuse(
                "incomplete-plan",
                "source-drift requires the exact changed-source reverse closure",
            )
    if reason in FULL_RECOMPUTE_REASONS and (
        mode != "full"
        or set(changed) != current_paths
        or set(dirty) != current_paths
        or reusable
        or reverse_invalidated
        or (reason != "scope-mismatch" and removed)
    ):
        _refuse(
            "incomplete-plan",
            "a full-recompute reason requires the exact full plan",
        )
    if mode == "full" and (set(dirty) != current_paths or reusable):
        _refuse("incomplete-plan", "a full plan must dirty the complete scope")
    if _has_cycle(sources) and (
        mode != "full"
        or reason != "dependency-cycle"
        or set(changed) != current_paths
        or set(dirty) != current_paths
        or reusable
        or removed
        or reverse_invalidated
    ):
        _refuse(
            "incomplete-plan",
            "a cyclic scope requires the exact full-recomputation plan",
        )
    return {
        "schema": PLAN_SCHEMA,
        "mode": mode,
        "reason": reason,
        "identity": identity,
        "sources": sources,
        "changed": changed,
        "dirty": dirty,
        "reusable": reusable,
        "removed": removed,
        "reverse_invalidated": reverse_invalidated,
    }


def _fresh_entries(
    values: Sequence[Any],
    plan_document: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    dirty = set(plan_document["dirty"])
    sources = {source["path"]: source for source in plan_document["sources"]}
    if len(values) > MAX_SOURCES:
        _refuse("size-limit", f"fresh entries exceed {MAX_SOURCES}")
    found: dict[str, dict[str, Any]] = {}
    total = 0
    for index, raw in enumerate(values):
        entry = validate_entry(
            raw,
            plan_document["identity"],
            None,
            f"fresh_entries[{index}]",
        )
        total += len(
            json.dumps(entry, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        if total > MAX_TOTAL_FRESH_JSON_BYTES:
            _refuse(
                "size-limit",
                "fresh entries exceed "
                f"{MAX_TOTAL_FRESH_JSON_BYTES} aggregate bytes",
            )
        path = entry["path"]
        if path in found:
            _refuse("duplicate-source", f"fresh entry appears twice: {path}")
        if path not in dirty:
            _refuse("unexpected-fresh-entry", f"fresh entry was not requested: {path}")
        validate_entry(
            entry,
            plan_document["identity"],
            sources[path],
            f"fresh_entries[{index}]",
            plan_document["sources"],
        )
        found[path] = entry
    missing = sorted(dirty - set(found))
    if missing:
        _refuse("missing-fresh-entry", "fresh entries are missing: " + ", ".join(missing))
    return found


def _atomic_write_json(path: os.PathLike[str] | str, value: Any) -> None:
    """Atomically replace one operator-selected JSON file without symlink use."""
    target = _filesystem_path(path, "output path")
    if not target.name or target.name in (".", ".."):
        _refuse("unsafe-path", "output path must name a file")
    try:
        parent = target.parent.resolve(strict=True)
        parent_info = target.parent.lstat()
    except (OSError, RuntimeError) as exc:
        _refuse("unsafe-path", f"output parent cannot be inspected: {exc}")
    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
        _refuse("unsafe-path", "output parent must be a real directory")
    target = parent / target.name
    try:
        existing = target.lstat()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        _refuse("unsafe-path", f"output target cannot be inspected: {exc}")
    if existing is not None and (
        stat.S_ISLNK(existing.st_mode) or not stat.S_ISREG(existing.st_mode)
    ):
        _refuse("unsafe-path", "output target must be absent or a regular file")
    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > MAX_JSON_BYTES:
        _refuse("size-limit", f"encoded output exceeds {MAX_JSON_BYTES} bytes")

    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".tmp", dir=parent
        )
    except OSError as exc:
        _refuse("atomic-write-failed", f"atomic staging failed: {exc}")
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        directory_flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            directory_flags |= os.O_DIRECTORY
        directory = os.open(parent, directory_flags)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError as exc:
        _refuse("atomic-write-failed", f"atomic replacement failed: {exc}")
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass


def assemble(
    project_root: os.PathLike[str] | str,
    scope: Any,
    plan_document: Any,
    fresh_entries: Sequence[Any],
    cache_path: os.PathLike[str] | str | None = None,
    candidate_path: os.PathLike[str] | str | None = None,
) -> dict[str, Any]:
    """Assemble the exact current union and rebuild every synthesis input."""
    current = materialize_scope(project_root, scope)
    if candidate_path is not None:
        _assert_distinct_paths(
            (
                ("candidate", candidate_path),
                ("cache", cache_path),
                *_source_path_roles(project_root, current["sources"]),
            )
        )
    accepted_plan = validate_plan(plan_document)
    if (
        accepted_plan["identity"] != current["identity"]
        or accepted_plan["sources"] != current["sources"]
    ):
        _refuse("scope-drift", "source bytes or scope changed after planning")
    fresh = _fresh_entries(fresh_entries, accepted_plan)
    reused: dict[str, dict[str, Any]] = {}
    if accepted_plan["reusable"]:
        if cache_path is None:
            _refuse("missing-cache", "an incremental assembly requires its planned cache")
        cache = validate_cache(load_json(cache_path, "X-Ray reuse cache"))
        if cache["identity"] != current["identity"]:
            _refuse("cache-drift", "cache identity changed after planning")
        cache_paths = {source["path"] for source in cache["sources"]}
        current_paths = {source["path"] for source in current["sources"]}
        if cache_paths != current_paths:
            _refuse("cache-drift", "cache source inventory changed after planning")
        cache_entries = {entry["path"]: entry for entry in cache["entries"]}
        sources = {source["path"]: source for source in current["sources"]}
        for path in accepted_plan["reusable"]:
            entry = cache_entries.get(path)
            if entry is None:
                _refuse("cache-drift", f"planned reusable entry disappeared: {path}")
            reused[path] = validate_entry(
                entry,
                current["identity"],
                sources[path],
                f"cache entry {path}",
                current["sources"],
            )
    union = {**reused, **fresh}
    current_paths = {source["path"] for source in current["sources"]}
    if set(union) != current_paths:
        _refuse("incomplete-entry-set", "assembled union does not equal current scope")
    entries = [union[path] for path in sorted(union)]
    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "identity": current["identity"],
        "sources": current["sources"],
        "entries": entries,
        "synthesis": rebuild_synthesis(entries),
    }
    candidate = validate_candidate(candidate)
    if candidate_path is not None:
        _atomic_write_json(candidate_path, candidate)
    return candidate


def _output_digests(output_dir: os.PathLike[str] | str) -> dict[str, str]:
    root = _filesystem_path(output_dir, "output directory")
    try:
        info = root.lstat()
    except OSError as exc:
        _refuse("missing-output", f"output directory cannot be inspected: {exc}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        _refuse("unsafe-path", "output directory must be a real directory")
    outputs: dict[str, str] = {}
    for name in FINAL_OUTPUTS:
        path = root / name
        raw = _read_regular(path, MAX_OUTPUT_BYTES, f"X-Ray output {name}")
        if not raw:
            _refuse("missing-output", f"X-Ray output is empty: {name}")
        if name == "architecture.json":
            try:
                json.loads(
                    raw.decode("utf-8"),
                    object_pairs_hook=_unique_object,
                    parse_constant=_reject_constant,
                )
            except ReuseError:
                raise
            except (UnicodeDecodeError, ValueError, RecursionError) as exc:
                _refuse("invalid-output", f"architecture.json is not valid JSON: {exc}")
        outputs[name] = hashlib.sha256(raw).hexdigest()
    return outputs


def validate_output_manifest(
    value: Any,
    candidate: Mapping[str, Any],
    actual_outputs: Mapping[str, str],
) -> dict[str, Any]:
    """Validate exact current-scope and current-byte evidence for four outputs."""
    manifest = _closed_object(
        value,
        ("candidate_sha256", "outputs", "schema", "source_inventory"),
        "output manifest",
    )
    if manifest["schema"] != OUTPUT_MANIFEST_SCHEMA:
        _refuse(
            "invalid-schema",
            f"output manifest.schema must equal {OUTPUT_MANIFEST_SCHEMA}",
        )
    inventory = manifest["source_inventory"]
    if not isinstance(inventory, list) or len(inventory) > MAX_SOURCES:
        _refuse("invalid-schema", "output manifest.source_inventory must be bounded")
    normal_inventory = [
        _source_path(path, "output manifest.source_inventory") for path in inventory
    ]
    if len(set(normal_inventory)) != len(normal_inventory):
        _refuse("duplicate-source", "output manifest source inventory has duplicates")
    expected_inventory = candidate["synthesis"]["source_inventory"]
    if normal_inventory != expected_inventory:
        _refuse(
            "output-scope-mismatch",
            "output manifest does not cover the candidate's exact current source inventory",
        )
    candidate_sha256 = _digest(
        manifest["candidate_sha256"], "output manifest.candidate_sha256"
    )
    if candidate_sha256 != canonical_digest(candidate):
        _refuse(
            "candidate-digest-mismatch",
            "output manifest is not bound to the exact current candidate",
        )
    outputs = _validate_outputs(manifest["outputs"], "output manifest.outputs")
    if outputs != dict(actual_outputs):
        _refuse(
            "output-digest-mismatch",
            "output manifest digests do not match the current four output files",
        )
    return {
        "schema": OUTPUT_MANIFEST_SCHEMA,
        "candidate_sha256": candidate_sha256,
        "source_inventory": normal_inventory,
        "outputs": outputs,
    }


def bind_outputs(
    candidate_path: os.PathLike[str] | str,
    output_dir: os.PathLike[str] | str,
    manifest_path: os.PathLike[str] | str | None = None,
) -> dict[str, Any]:
    """Bind the exact candidate inventory to the current four output digests."""
    root = _filesystem_path(output_dir, "output directory")
    target = (
        root / OUTPUT_MANIFEST_NAME
        if manifest_path is None
        else _filesystem_path(manifest_path, "output manifest path")
    )
    _assert_distinct_paths(
        (
            ("candidate", candidate_path),
            ("output manifest", target),
            *((f"X-Ray output {name}", root / name) for name in FINAL_OUTPUTS),
        )
    )
    candidate = validate_candidate(load_json(candidate_path, "X-Ray candidate"))
    outputs = _output_digests(root)
    manifest = {
        "schema": OUTPUT_MANIFEST_SCHEMA,
        "candidate_sha256": canonical_digest(candidate),
        "source_inventory": candidate["synthesis"]["source_inventory"],
        "outputs": outputs,
    }
    _atomic_write_json(target, manifest)
    return manifest


def promote(
    candidate_path: os.PathLike[str] | str,
    output_dir: os.PathLike[str] | str,
    cache_path: os.PathLike[str] | str,
    manifest_path: os.PathLike[str] | str | None = None,
) -> dict[str, Any]:
    """Digest-bind all four outputs, then atomically replace the reusable cache."""
    root = _filesystem_path(output_dir, "output directory")
    manifest_path = (
        root / OUTPUT_MANIFEST_NAME
        if manifest_path is None
        else _filesystem_path(manifest_path, "output manifest path")
    )
    _assert_distinct_paths(
        (
            ("candidate", candidate_path),
            ("output manifest", manifest_path),
            ("cache", cache_path),
            *((f"X-Ray output {name}", root / name) for name in FINAL_OUTPUTS),
        )
    )
    candidate = validate_candidate(load_json(candidate_path, "X-Ray candidate"))
    outputs = _output_digests(root)
    manifest = validate_output_manifest(
        load_json(manifest_path, "X-Ray output manifest"),
        candidate,
        outputs,
    )
    cache = {
        "schema": CACHE_SCHEMA,
        "identity": candidate["identity"],
        "sources": candidate["sources"],
        "entries": candidate["entries"],
        "synthesis": candidate["synthesis"],
        "outputs": manifest["outputs"],
    }
    cache = validate_cache(cache)
    _atomic_write_json(cache_path, cache)
    return cache


def _load_fresh(paths: Sequence[str]) -> list[Any]:
    if len(paths) > MAX_SOURCES:
        _refuse("size-limit", f"fresh entry paths exceed {MAX_SOURCES}")
    total = 0
    documents: list[Any] = []
    for path in paths:
        label = f"fresh entry {path}"
        raw = _read_regular(
            _filesystem_path(path, f"{label} path"),
            MAX_JSON_BYTES,
            label,
        )
        total += len(raw)
        if total > MAX_TOTAL_FRESH_JSON_BYTES:
            _refuse(
                "size-limit",
                "fresh entry JSON exceeds "
                f"{MAX_TOTAL_FRESH_JSON_BYTES} aggregate bytes",
            )
        documents.append(_decode_json(raw, label))
    return documents


def _result(operation: str, document: Mapping[str, Any], path: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "operation": operation,
        "status": "ok",
    }
    if operation == "plan":
        payload.update(
            {
                "mode": document["mode"],
                "reason": document["reason"],
                "dirty": document["dirty"],
                "reusable": document["reusable"],
                "removed": document["removed"],
                "reverse_invalidated": document["reverse_invalidated"],
            }
        )
    elif operation == "assemble":
        payload.update(
            {
                "sources": document["synthesis"]["source_inventory"],
                "candidate_sha256": canonical_digest(document),
            }
        )
    else:
        payload.update({"sources": document["synthesis"]["source_inventory"], "outputs": document["outputs"]})
    if path is not None:
        payload["path"] = path
    return payload


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    planner = commands.add_parser("plan", help="plan full or incremental extraction")
    planner.add_argument("--project-root", required=True)
    planner.add_argument("--scope", required=True)
    planner.add_argument("--cache")
    planner.add_argument("--write-plan")

    assembler = commands.add_parser("assemble", help="assemble a complete current union")
    assembler.add_argument("--project-root", required=True)
    assembler.add_argument("--scope", required=True)
    assembler.add_argument("--plan", required=True)
    assembler.add_argument("--fresh-entry", action="append", default=[])
    assembler.add_argument("--cache")
    assembler.add_argument("--candidate", required=True)

    binder = commands.add_parser(
        "bind-outputs", help="bind the candidate inventory to four output digests"
    )
    binder.add_argument("--candidate", required=True)
    binder.add_argument("--outputs", required=True)
    binder.add_argument("--manifest")

    promoter = commands.add_parser("promote", help="bind four outputs and promote cache")
    promoter.add_argument("--candidate", required=True)
    promoter.add_argument("--outputs", required=True)
    promoter.add_argument("--cache", required=True)
    promoter.add_argument("--manifest")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    try:
        if arguments.command == "plan":
            scope = load_json(arguments.scope, "scope manifest")
            document = plan(arguments.project_root, scope, arguments.cache)
            if arguments.write_plan:
                _assert_distinct_paths(
                    (
                        ("plan output", arguments.write_plan),
                        ("scope manifest", arguments.scope),
                        ("cache", arguments.cache),
                        *_source_path_roles(arguments.project_root, document["sources"]),
                    )
                )
                _atomic_write_json(arguments.write_plan, document)
            payload = _result("plan", document, arguments.write_plan)
        elif arguments.command == "assemble":
            scope = load_json(arguments.scope, "scope manifest")
            plan_document = load_json(arguments.plan, "reuse plan")
            _assert_distinct_paths(
                (
                    ("candidate", arguments.candidate),
                    ("scope manifest", arguments.scope),
                    ("reuse plan", arguments.plan),
                    ("cache", arguments.cache),
                    *(
                        (f"fresh entry {index}", path)
                        for index, path in enumerate(arguments.fresh_entry)
                    ),
                )
            )
            document = assemble(
                arguments.project_root,
                scope,
                plan_document,
                _load_fresh(arguments.fresh_entry),
                arguments.cache,
                arguments.candidate,
            )
            payload = _result("assemble", document, arguments.candidate)
        elif arguments.command == "bind-outputs":
            document = bind_outputs(
                arguments.candidate,
                arguments.outputs,
                arguments.manifest,
            )
            payload = {
                "schema": RESULT_SCHEMA,
                "operation": "bind-outputs",
                "status": "ok",
                "path": arguments.manifest
                or str(Path(arguments.outputs) / OUTPUT_MANIFEST_NAME),
                "candidate_sha256": document["candidate_sha256"],
                "sources": document["source_inventory"],
                "outputs": document["outputs"],
            }
        else:
            document = promote(
                arguments.candidate,
                arguments.outputs,
                arguments.cache,
                arguments.manifest,
            )
            payload = _result("promote", document, arguments.cache)
    except ReuseError as exc:
        print(
            json.dumps(
                {
                    "schema": RESULT_SCHEMA,
                    "operation": arguments.command,
                    "status": "refused",
                    "code": exc.code,
                    "message": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
