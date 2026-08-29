"""Ingest and offline verification for Alexandria raw releases."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import shutil
import tempfile

from .canonical import (
    MAX_CONTROL_BYTES,
    MAX_INTEGER_DIGITS,
    canonical_bytes,
    load_bytes,
    load_raw_json,
)
from .errors import AlexandriaError
from .paths import read_confined_file, validate_closed_tree, validate_relative_path


PLAN_FORMAT = "alexandria-capture-plan/v1"
MANIFEST_FORMAT = "alexandria-release/v1"
DIGEST_RE = re.compile(r"^sha256:([0-9a-f]{64})$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
CHAIN_RE = re.compile(r"^eip155:(0|[1-9][0-9]*)$")
ACCOUNT_RE = re.compile(r"^(eip155:(?:0|[1-9][0-9]*)):0x[0-9a-f]{40}$")
DECIMAL_RE = re.compile(r"^(0|[1-9][0-9]*)$")
BLOCK_HASH_RE = re.compile(r"^0x[0-9a-f]{64}$")
TIMESTAMP_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")
EVIDENCE_CLASSES = {
    "archive-log",
    "header-bound",
    "hosted-indexer",
    "proof-backed-state",
    "provider-export",
    "recorded-rpc",
}
SCOPE_KINDS = {"full-dataset", "subject-scoped"}
FINALITY_CLASSES = {"unknown", "provider-reported", "safe", "finalized"}
LOCATOR_CLASSES = {
    "public-uri",
    "provider-endpoint",
    "chain-range",
    "local-fixture",
    "external-object",
    "undisclosed",
}
COVERAGE_STATUSES = {"complete", "partial", "failed", "unsupported"}
ACCESS_CLASSES = {"public", "restricted", "private"}
REDISTRIBUTION_CLASSES = {"permitted", "restricted", "prohibited", "unknown"}
MAX_RAW_COMPONENT_BYTES = 64 * 1024 * 1024
MAX_COMPONENTS = 128
MAX_CAPTURES = 1024
MAX_COLLECTIONS = 256
MAX_GAPS = 256


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def ingest(plan_path: Path, output: Path) -> str:
    """Build one release directory atomically from a declared capture plan."""
    plan_path = plan_path.absolute()
    plan_bytes = read_confined_file(
        plan_path.parent,
        plan_path.name,
        "capture plan",
        max_bytes=MAX_CONTROL_BYTES,
    )
    plan = load_bytes(plan_bytes, "capture plan")
    validate_plan(plan)
    output = output.absolute()
    parent = output.parent
    parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise AlexandriaError("output must not be a symlink")

    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=parent))
    try:
        components = []
        captures_by_component = {}
        for capture in plan["captures"]:
            captures_by_component.setdefault(capture["component"], []).append(capture)
        for declaration in sorted(plan["components"], key=lambda item: item["name"]):
            data = read_confined_file(
                plan_path.parent,
                declaration["path"],
                f"component {declaration['name']}",
                max_bytes=MAX_RAW_COMPONENT_BYTES,
            )
            for capture in captures_by_component.get(declaration["name"], []):
                _validate_coverage_against_bytes(capture, data)
            digest = sha256(data)
            hexadecimal = digest.removeprefix("sha256:")
            object_path = f"objects/sha256/{hexadecimal[:2]}/{hexadecimal}"
            destination = temporary.joinpath(*object_path.split("/"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            components.append(
                {
                    "access": declaration["access"],
                    "bytes": len(data),
                    "media_type": declaration["media_type"],
                    "name": declaration["name"],
                    "object_path": object_path,
                    "role": declaration["role"],
                    "redistribution": declaration["redistribution"],
                    "sha256": digest,
                }
            )

        captures = []
        by_name = {item["name"]: item for item in components}
        for capture in sorted(plan["captures"], key=lambda item: item["id"]):
            stored = deepcopy(capture)
            stored["component_sha256"] = by_name[capture["component"]]["sha256"]
            captures.append(stored)

        unsigned = {
            "captures": captures,
            "components": components,
            "format": MANIFEST_FORMAT,
            "release": deepcopy(plan["release"]),
        }
        release_id = sha256(canonical_bytes(unsigned))
        manifest = dict(unsigned)
        manifest["release_id"] = release_id
        (temporary / "manifest.json").write_bytes(canonical_bytes(manifest))
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


def verify(release_root: Path) -> str:
    """Verify a release using only files below its local release root."""
    release_root = release_root.absolute()
    if release_root.is_symlink() or not release_root.is_dir():
        raise AlexandriaError("release must be a local directory, not a symlink")
    manifest_bytes = read_confined_file(
        release_root,
        "manifest.json",
        "manifest",
        max_bytes=MAX_CONTROL_BYTES,
    )
    manifest = load_bytes(manifest_bytes, "manifest")
    validate_manifest(manifest)
    if canonical_bytes(manifest) != manifest_bytes:
        raise AlexandriaError("manifest is not canonical JSON")

    identity = deepcopy(manifest)
    claimed = identity.pop("release_id")
    actual = sha256(canonical_bytes(identity))
    if claimed != actual:
        raise AlexandriaError("manifest release identity does not match its content")

    digest_by_name = {}
    captures_by_component = {}
    for capture in manifest["captures"]:
        captures_by_component.setdefault(capture["component"], []).append(capture)
    for component in manifest["components"]:
        expected_path = _object_path(component["sha256"])
        if component["object_path"] != expected_path:
            raise AlexandriaError(f"component {component['name']} path does not match its digest")
        data = read_confined_file(
            release_root,
            component["object_path"],
            f"component {component['name']}",
            max_bytes=MAX_RAW_COMPONENT_BYTES,
        )
        if len(data) != component["bytes"]:
            raise AlexandriaError(f"component {component['name']} byte count does not match")
        if sha256(data) != component["sha256"]:
            raise AlexandriaError(f"component {component['name']} digest does not match")
        digest_by_name[component["name"]] = component["sha256"]
        for capture in captures_by_component.get(component["name"], []):
            _validate_coverage_against_bytes(capture, data)
    del data

    for capture in manifest["captures"]:
        if capture["component_sha256"] != digest_by_name[capture["component"]]:
            raise AlexandriaError(f"capture {capture['id']} component digest does not match")
    allowed = {"manifest.json", *(component["object_path"] for component in manifest["components"])}
    if "derivation" in manifest:
        from .derivation import component_reader, output_paths, verify_derivation

        verify_derivation(
            release_root,
            manifest,
            component_reader(release_root, manifest),
        )
        allowed.update(output_paths(manifest["derivation"]))
    validate_closed_tree(release_root, allowed)
    return claimed


def validate_plan(plan) -> None:
    _require_keys(plan, {"format", "release", "components", "captures"}, "capture plan")
    if plan["format"] != PLAN_FORMAT:
        raise AlexandriaError(f"capture plan format must be {PLAN_FORMAT}")
    _validate_release(plan["release"])
    _validate_components(plan["components"], plan=True)
    names = {item["name"] for item in plan["components"]}
    _validate_captures(plan["captures"], names, manifest=False)


def validate_manifest(manifest) -> None:
    _require_keys(
        manifest,
        {"format", "release_id", "release", "components", "captures"},
        "manifest",
        allowed={"format", "release_id", "release", "components", "captures", "derivation"},
    )
    if manifest["format"] != MANIFEST_FORMAT:
        raise AlexandriaError(f"manifest format must be {MANIFEST_FORMAT}")
    _validate_digest(manifest["release_id"], "release_id")
    _validate_release(manifest["release"], release_id=manifest["release_id"])
    _validate_components(manifest["components"], plan=False)
    names = {item["name"] for item in manifest["components"]}
    _validate_captures(manifest["captures"], names, manifest=True)
    if "derivation" in manifest:
        from .derivation import validate_derivation

        validate_derivation(manifest["derivation"])
    if manifest["components"] != sorted(manifest["components"], key=lambda item: item["name"]):
        raise AlexandriaError("manifest components are not in canonical name order")
    if manifest["captures"] != sorted(manifest["captures"], key=lambda item: item["id"]):
        raise AlexandriaError("manifest captures are not in canonical id order")


def _validate_release(release, release_id=None) -> None:
    allowed = {"name", "created_at", "correction"}
    required = {"name", "created_at"}
    _require_keys(release, required, "release", allowed=allowed)
    _name(release["name"], "release name")
    _timestamp(release["created_at"], "release created_at")
    correction = release.get("correction")
    if correction is None:
        return
    _require_keys(correction, {"supersedes", "reason"}, "release correction")
    supersedes = correction["supersedes"]
    if not isinstance(supersedes, list) or not supersedes:
        raise AlexandriaError("release correction supersedes must be a non-empty list")
    for item in supersedes:
        _validate_digest(item, "supersedes release id")
        if release_id is not None and item == release_id:
            raise AlexandriaError("a release cannot supersede itself")
    if len(supersedes) != len(set(supersedes)):
        raise AlexandriaError("release correction contains duplicate supersedes links")
    if not isinstance(correction["reason"], str) or not correction["reason"].strip():
        raise AlexandriaError("release correction reason must be non-empty")


def _validate_components(components, *, plan: bool) -> None:
    if not isinstance(components, list) or not components:
        raise AlexandriaError("components must be a non-empty list")
    if len(components) > MAX_COMPONENTS:
        raise AlexandriaError(f"components exceed the {MAX_COMPONENTS}-item limit")
    names = []
    for component in components:
        if plan:
            required = {"name", "path", "media_type", "role", "access", "redistribution"}
        else:
            required = {
                "name", "object_path", "media_type", "role", "access",
                "redistribution", "sha256", "bytes",
            }
        _require_keys(component, required, "component")
        _name(component["name"], "component name")
        names.append(component["name"])
        if not isinstance(component["media_type"], str) or "/" not in component["media_type"]:
            raise AlexandriaError("component media_type must be a media type")
        _name(component["role"], "component role")
        _choice(
            component["access"],
            ACCESS_CLASSES,
            "component access must be public, restricted or private",
        )
        _choice(
            component["redistribution"],
            REDISTRIBUTION_CLASSES,
            "component redistribution must be permitted, restricted, prohibited or unknown",
        )
        if plan:
            validate_relative_path(component["path"], "component path")
        else:
            validate_relative_path(component["object_path"], "component object_path")
            _validate_digest(component["sha256"], "component sha256")
            _nonnegative_int(component["bytes"], "component bytes")
    if len(names) != len(set(names)):
        raise AlexandriaError("component names must be unique")


def _validate_captures(captures, component_names, *, manifest: bool) -> None:
    if not isinstance(captures, list) or not captures:
        raise AlexandriaError("captures must be a non-empty list")
    if len(captures) > MAX_CAPTURES:
        raise AlexandriaError(f"captures exceed the {MAX_CAPTURES}-item limit")
    ids = []
    for capture in captures:
        required = {
            "id",
            "component",
            "venue",
            "chain",
            "evidence_class",
            "source",
            "scope",
            "coverage",
        }
        if manifest:
            required.add("component_sha256")
        _require_keys(capture, required, "capture")
        _name(capture["id"], "capture id")
        ids.append(capture["id"])
        _name(capture["component"], "capture component")
        if capture["component"] not in component_names:
            raise AlexandriaError(f"capture {capture['id']} names an unknown component")
        _name(capture["venue"], "capture venue")
        if not isinstance(capture["chain"], str) or not CHAIN_RE.fullmatch(capture["chain"]):
            raise AlexandriaError("capture chain must be a canonical eip155 CAIP-2 id")
        _choice(
            capture["evidence_class"],
            EVIDENCE_CLASSES,
            "capture has an unknown evidence_class",
        )
        _validate_source(capture["source"])
        if manifest:
            _validate_digest(capture["component_sha256"], "capture component_sha256")
        _validate_scope(capture["scope"], capture["chain"])
        _validate_coverage(capture["coverage"])
    if len(ids) != len(set(ids)):
        raise AlexandriaError("capture ids must be unique")


def _validate_source(source) -> None:
    _require_keys(source, {"kind", "locator_class", "reference"}, "capture source")
    _name(source["kind"], "capture source kind")
    _choice(
        source["locator_class"],
        LOCATOR_CLASSES,
        "capture source locator_class is unknown",
    )
    reference = source["reference"]
    if (
        not isinstance(reference, str)
        or not reference.strip()
        or reference != reference.strip()
        or len(reference) > 2048
        or any(ord(character) < 32 for character in reference)
    ):
        raise AlexandriaError(
            "capture source reference must be a trimmed non-empty string without control characters"
        )


def _validate_scope(scope, chain) -> None:
    required = {"kind", "deployment", "finality", "interval"}
    allowed = required | {"subjects"}
    _require_keys(scope, required, "capture scope", allowed=allowed)
    _choice(scope["kind"], SCOPE_KINDS, "capture scope kind is unknown")
    _name(scope["deployment"], "capture deployment")
    _choice(scope["finality"], FINALITY_CLASSES, "capture scope finality is unknown")
    subjects = scope.get("subjects")
    if scope["kind"] == "subject-scoped":
        if not isinstance(subjects, list) or not subjects:
            raise AlexandriaError("subject-scoped coverage requires subjects")
        for subject in subjects:
            match = ACCOUNT_RE.fullmatch(subject) if isinstance(subject, str) else None
            if match is None or match.group(1) != chain:
                raise AlexandriaError("capture subject must be a lowercase CAIP-10 EVM account on its chain")
        if len(subjects) != len(set(subjects)):
            raise AlexandriaError("capture subjects must be unique")
    elif subjects is not None:
        raise AlexandriaError("full-dataset coverage must not declare subjects")
    _validate_interval(scope["interval"])
    if scope["finality"] in {"safe", "finalized"}:
        interval = scope["interval"]
        hash_key = "block_hash" if interval["kind"] == "snapshot" else "end_hash"
        if hash_key not in interval:
            raise AlexandriaError(
                f"{scope['finality']} finality requires block identifiers"
            )


def _validate_interval(interval) -> None:
    if not isinstance(interval, dict) or "kind" not in interval:
        raise AlexandriaError("capture interval must be an object with a kind")
    if interval["kind"] == "snapshot":
        _require_keys(
            interval,
            {"kind", "observed_at"},
            "snapshot interval",
            allowed={"kind", "observed_at", "block_number", "block_hash"},
        )
        _timestamp(interval["observed_at"], "snapshot observed_at")
        _validate_optional_block_pair(interval, "block_number", "block_hash", "snapshot")
        return
    if interval["kind"] == "block-range":
        _require_keys(
            interval,
            {"kind", "start", "end"},
            "block-range interval",
            allowed={"kind", "start", "end", "start_hash", "end_hash"},
        )
        start = interval["start"]
        end = interval["end"]
        _decimal(start, "block-range start")
        _decimal(end, "block-range end")
        if int(start) > int(end):
            raise AlexandriaError("block-range start must not exceed end")
        _validate_optional_hash_pair(interval, "start_hash", "end_hash", "block-range")
        return
    raise AlexandriaError("capture interval kind is unknown")


def _validate_optional_block_pair(value, number_key, hash_key, label) -> None:
    has_number = number_key in value
    has_hash = hash_key in value
    if has_number != has_hash:
        raise AlexandriaError(f"{label} block number and hash must be supplied together")
    if not has_number:
        return
    number = value[number_key]
    _decimal(number, f"{label} block number")
    _block_hash(value[hash_key], f"{label} block hash")


def _validate_optional_hash_pair(value, first_key, second_key, label) -> None:
    has_first = first_key in value
    has_second = second_key in value
    if has_first != has_second:
        raise AlexandriaError(f"{label} boundary hashes must be supplied together")
    if has_first:
        _block_hash(value[first_key], f"{label} start hash")
        _block_hash(value[second_key], f"{label} end hash")


def _validate_coverage(coverage) -> None:
    required = {"status", "record_count", "collections", "unsupported_collections", "gaps"}
    _require_keys(coverage, required, "coverage")
    _choice(coverage["status"], COVERAGE_STATUSES, "coverage status is unknown")
    _nonnegative_int(coverage["record_count"], "coverage record_count")
    if not isinstance(coverage["collections"], list):
        raise AlexandriaError("coverage collections must be a list")
    if len(coverage["collections"]) > MAX_COLLECTIONS:
        raise AlexandriaError(f"coverage collections exceed the {MAX_COLLECTIONS}-item limit")
    names = []
    selectors = []
    total = 0
    for collection in coverage["collections"]:
        _require_keys(collection, {"name", "selector", "record_count"}, "coverage collection")
        _name(collection["name"], "coverage collection name")
        names.append(collection["name"])
        selector = collection["selector"]
        if not isinstance(selector, str) or not selector.startswith("/") or len(selector) > 1024:
            raise AlexandriaError("coverage selector must be an absolute JSON Pointer")
        _pointer_tokens(selector)
        selectors.append(selector)
        _nonnegative_int(collection["record_count"], "coverage collection record_count")
        total += collection["record_count"]
    if len(names) != len(set(names)):
        raise AlexandriaError("coverage collection names must be unique")
    if len(selectors) != len(set(selectors)):
        raise AlexandriaError("coverage selectors must be unique")
    if total != coverage["record_count"]:
        raise AlexandriaError("coverage record_count does not equal its collection counts")
    unsupported = coverage["unsupported_collections"]
    if not isinstance(unsupported, list):
        raise AlexandriaError("unsupported_collections must be a list of names")
    if len(unsupported) > MAX_COLLECTIONS:
        raise AlexandriaError(
            f"unsupported_collections exceed the {MAX_COLLECTIONS}-item limit"
        )
    for item in unsupported:
        _name(item, "unsupported collection")
    if len(unsupported) != len(set(unsupported)):
        raise AlexandriaError("unsupported_collections contains duplicates")
    gaps = coverage["gaps"]
    if not isinstance(gaps, list) or len(gaps) > MAX_GAPS:
        raise AlexandriaError(f"coverage gaps must be a list of at most {MAX_GAPS} reasons")
    if any(not isinstance(item, str) or not item.strip() or len(item) > 1000 for item in gaps):
        raise AlexandriaError("coverage gap reasons must be non-empty strings of at most 1000 characters")
    status = coverage["status"]
    if status == "complete":
        if not coverage["collections"]:
            raise AlexandriaError("complete coverage requires at least one counted collection")
        if unsupported or gaps:
            raise AlexandriaError("complete coverage cannot name unsupported collections or gaps")
    elif status == "partial":
        if not unsupported and not gaps:
            raise AlexandriaError("partial coverage must name an unsupported collection or gap")
    elif status in {"failed", "unsupported"}:
        if coverage["record_count"] or coverage["collections"]:
            raise AlexandriaError(f"{status} coverage cannot carry counted records")
        if not gaps:
            raise AlexandriaError(f"{status} coverage requires a gap reason")


def _validate_coverage_against_bytes(capture, data: bytes) -> None:
    coverage = capture["coverage"]
    if not coverage["collections"]:
        return
    document = load_raw_json(
        data,
        f"component {capture['component']} JSON payload",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )
    actual_total = 0
    for collection in coverage["collections"]:
        value = _resolve_pointer(document, collection["selector"])
        if not isinstance(value, list):
            raise AlexandriaError(
                f"coverage selector {collection['selector']} does not resolve to a list"
            )
        actual = len(value)
        if actual != collection["record_count"]:
            raise AlexandriaError(
                f"coverage collection {collection['name']} declares {collection['record_count']} records but found {actual}"
            )
        actual_total += actual
    if actual_total != coverage["record_count"]:
        raise AlexandriaError("coverage total is inflated or incomplete")


def _resolve_pointer(document, pointer: str):
    current = document
    for token in _pointer_tokens(pointer):
        if isinstance(current, dict):
            if token not in current:
                raise AlexandriaError(f"coverage selector {pointer} does not resolve")
            current = current[token]
        elif isinstance(current, list):
            _decimal(token, f"coverage selector {pointer} list index")
            index = int(token)
            if index >= len(current):
                raise AlexandriaError(f"coverage selector {pointer} does not resolve")
            current = current[index]
        else:
            raise AlexandriaError(f"coverage selector {pointer} does not resolve")
    return current


def _pointer_tokens(pointer: str):
    tokens = []
    for raw in pointer.split("/")[1:]:
        decoded = []
        index = 0
        while index < len(raw):
            if raw[index] != "~":
                decoded.append(raw[index])
                index += 1
                continue
            if index + 1 >= len(raw) or raw[index + 1] not in "01":
                raise AlexandriaError(f"coverage selector {pointer} has invalid escaping")
            decoded.append("~" if raw[index + 1] == "0" else "/")
            index += 2
        tokens.append("".join(decoded))
    return tokens


def _object_path(digest: str) -> str:
    match = DIGEST_RE.fullmatch(digest)
    if match is None:
        raise AlexandriaError("object digest is not a SHA-256 identifier")
    value = match.group(1)
    return f"objects/sha256/{value[:2]}/{value}"


def _require_keys(value, required, label, *, allowed=None) -> None:
    if not isinstance(value, dict):
        raise AlexandriaError(f"{label} must be an object")
    allowed = required if allowed is None else allowed
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise AlexandriaError(f"{label} is missing {sorted(missing)[0]}")
    if unknown:
        raise AlexandriaError(f"{label} contains unknown field {sorted(unknown)[0]}")


def _name(value, label) -> None:
    if not isinstance(value, str) or not NAME_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be a lowercase stable name")


def _choice(value, choices, message) -> None:
    if not isinstance(value, str) or value not in choices:
        raise AlexandriaError(message)


def _nonnegative_int(value, label) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AlexandriaError(f"{label} must be a non-negative integer")


def _decimal(value, label) -> None:
    if (
        not isinstance(value, str)
        or len(value) > MAX_INTEGER_DIGITS
        or not DECIMAL_RE.fullmatch(value)
    ):
        raise AlexandriaError(f"{label} must be a canonical decimal string")


def _validate_digest(value, label) -> None:
    if not isinstance(value, str) or not DIGEST_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be a sha256:<lowercase-hex> identifier")


def _block_hash(value, label) -> None:
    if not isinstance(value, str) or not BLOCK_HASH_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be a lowercase 32-byte hex value")


def _timestamp(value, label) -> None:
    if not isinstance(value, str) or not TIMESTAMP_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be an RFC 3339 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise AlexandriaError(f"{label} must be an RFC 3339 UTC timestamp") from exc
    if parsed.microsecond:
        raise AlexandriaError(f"{label} must use whole seconds")
