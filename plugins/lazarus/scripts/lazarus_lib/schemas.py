"""Built-in Lazarus schema registry and semantic format checks."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from .canonical import dumps, load
from .errors import FormatError, IntegrityError


SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"
SCHEMAS: dict[tuple[str, int], tuple[str, str]] = {
    ("plan", 1): (
        "plan-v1.json",
        "f7081f2007ac8116215ffcb508a2ffc09d9c04fba512d87d1b69a885b72915de",
    ),
    ("plan", 2): (
        "plan-v2.json",
        "4130d0349c4bf91041757fb2d36854e54a6a97af7a9f1eefa5d812e792c9b9c3",
    ),
    ("header", 1): (
        "header-v1.json",
        "222e16df19169ae545e49ea423928ef63400ed078972e24734ac0697296fc9ac",
    ),
    ("rpc-record", 1): (
        "rpc-record-v1.json",
        "47c3036ab84c10cf09abc450bc7ba862d1de91d6619b5ecb46c71bc49ee9501e",
    ),
    ("proof-record", 1): (
        "proof-record-v1.json",
        "3ed92e5ebb37ca2358e3b0b28b57333cb4f6c6bc5a2e760d81f73a226c679ee7",
    ),
    ("anchor-record", 1): (
        "anchor-record-v1.json",
        "f22459e10e0e7f3736eafeb44224b92debee30daece8c12deab37e58ee76fb8e",
    ),
    ("manifest", 1): (
        "manifest-v1.json",
        "53acaefd6ddaf5648dc9d16345fc13c64c3bd7786851271ef922b67b9f423c14",
    ),
    ("release", 1): (
        "release-v1.json",
        "f7b8ce3eb37c40d79a23bdff1d88dd0e6e163c2d72ec67575b3b4e7023d5415d",
    ),
}


def _schema(kind: str, version: int) -> dict[str, Any]:
    registered = SCHEMAS.get((kind, version))
    if registered is None:
        raise FormatError(f"unsupported {kind} schema version: {version}")
    filename, expected_digest = registered
    path = SCHEMA_ROOT / filename
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise IntegrityError(f"cannot read built-in schema: {filename}") from exc
    actual_digest = hashlib.sha256(raw).hexdigest()
    if actual_digest != expected_digest:
        raise IntegrityError(f"built-in schema digest mismatch: {filename}")
    value = load(path)
    if not isinstance(value, dict):
        raise IntegrityError(f"built-in schema is not an object: {filename}")
    return value


def validate_builtin_schemas() -> None:
    for kind, version in SCHEMAS:
        schema = _schema(kind, version)
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as exc:
            raise IntegrityError(f"invalid built-in {kind} schema: {exc.message}") from exc


def validate_document(kind: str, document: Any) -> Any:
    if not isinstance(document, dict):
        raise FormatError(f"{kind} document must be an object")
    version = document.get("schema_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise FormatError(f"{kind} schema_version must be an integer")
    schema = _schema(kind, version)
    try:
        Draft202012Validator(schema).validate(document)
    except ValidationError as exc:
        location = "/".join(str(part) for part in exc.absolute_path) or "<root>"
        raise FormatError(f"invalid {kind} at {location}: {exc.message}") from exc
    # Canonical encoding also rejects floats and unsupported Python values that
    # JSON Schema deliberately permits as generic JSON instances.
    dumps(document)
    semantic = {
        "plan": _validate_plan,
        "header": _validate_header,
        "rpc-record": _validate_rpc_record,
        "proof-record": _validate_proof_record,
        "anchor-record": _validate_anchor_record,
        "manifest": _validate_manifest,
        "release": _validate_release,
    }[kind]
    semantic(document)
    return document


def _validate_release(release: dict[str, Any]) -> None:
    """What a release document must hold that JSON Schema cannot say.

    Both paths are read by whoever opens the release, so they get the same
    treatment a component path gets: relative, normalised, no backslash and no
    traversal. And the two must differ, because a release whose statement and
    fixture resolve to one path describes itself.
    """
    from .paths import validate_relative_path
    from .text import visible

    for field in ("predicate_type",):
        if not visible(release["statement"][field]):
            raise FormatError(
                f"release statement {field} shows a reader nothing: "
                f"{release['statement'][field]!r}"
            )
    for index, check in enumerate(release["binding"]["checks"]):
        if not visible(check):
            raise FormatError(
                f"release binding check {index + 1} shows a reader nothing: "
                f"{check!r}"
            )

    fixture = validate_relative_path(release["fixture"]["path"])
    statement = validate_relative_path(release["statement"]["path"])
    if fixture == statement:
        raise FormatError("release fixture and statement are the same path")
    if statement.split("/")[0] == fixture:
        raise FormatError(
            "release statement sits inside the fixture it describes; the fixture "
            "digest would cover the statement made about it"
        )


def _require_unique(values: list[str], label: str) -> None:
    if len(set(values)) != len(values):
        raise FormatError(f"duplicate {label}")


def _validate_plan(plan: dict[str, Any]) -> None:
    requests = plan["requests"]
    limit = plan["limits"]["max_requests"]
    if len(requests) > limit:
        raise FormatError("plan requests exceed max_requests")
    names = [request["name"] for request in requests]
    _require_unique(names, "request name")
    request_bytes = [dumps({"method": item["method"], "params": item["params"]}) for item in requests]
    if len(set(request_bytes)) != len(request_bytes):
        raise FormatError("duplicate exact request")
    addresses = [target["address"].lower() for target in plan["proof_targets"]]
    _require_unique(addresses, "proof target address")
    for target in plan["proof_targets"]:
        slots = [slot.lower() for slot in target["slots"]]
        if slots != sorted(slots) or len(slots) != len(set(slots)):
            raise FormatError(f"proof slots must be sorted and unique: {target['address']}")
    if plan["schema_version"] == 2:
        source_ids = [source["source_id"] for source in plan["anchor_sources"]]
        if source_ids != sorted(source_ids) or len(source_ids) != len(
            set(source_ids)
        ):
            raise FormatError("anchor sources must be sorted and unique")


def _validate_header(header: dict[str, Any]) -> None:
    rpc = header["rpc_result"]
    comparisons = {
        "number": "number",
        "hash": "hash",
        "parentHash": "parent_hash",
        "stateRoot": "state_root",
    }
    for rpc_name, header_name in comparisons.items():
        if rpc_name in rpc and rpc[rpc_name] != header[header_name]:
            raise FormatError(f"header {header_name} disagrees with rpc_result.{rpc_name}")


def _validate_rpc_record(record: dict[str, Any]) -> None:
    from .records import request_key

    expected = request_key(record["method"], record["params"])
    if record["request_key"] != expected:
        raise FormatError("RPC record request_key does not match method and params")
    if not record["required"] and "error" in record["outcome"]:
        return
    if record["required"] and "error" in record["outcome"]:
        raise FormatError("a required RPC record cannot preserve an error outcome")


def _validate_proof_record(record: dict[str, Any]) -> None:
    keys = [item["key"].lower() for item in record["storage_proof"]]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise FormatError("storage proof keys must be sorted and unique")


def _validate_anchor_record(record: dict[str, Any]) -> None:
    observed_at = record["observed_at"]
    utc_shape = (
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
        r"[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?Z"
    )
    if re.fullmatch(utc_shape, observed_at) is None:
        raise FormatError("anchor observed_at must be a UTC timestamp ending in Z")
    try:
        instant = datetime.fromisoformat(observed_at[:-1] + "+00:00")
    except ValueError:
        raise FormatError("anchor observed_at must be a valid UTC timestamp") from None
    if instant.tzinfo != timezone.utc:
        raise FormatError("anchor observed_at must be a UTC timestamp")
    if record["returned"]["number"] != record["params"][0]:
        raise FormatError("anchor returned number disagrees with requested block number")


def _validate_manifest(manifest: dict[str, Any]) -> None:
    from .paths import validate_relative_path

    paths = [validate_relative_path(item["path"]) for item in manifest["components"]]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise FormatError("manifest component paths must be sorted and unique")
    if "manifest.json" in paths:
        raise FormatError("manifest cannot list itself as a component")
    failures = manifest["optional_failures"]
    if failures != sorted(failures) or len(failures) != len(set(failures)):
        raise FormatError("optional failures must be sorted and unique")
