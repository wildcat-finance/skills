"""Make "closed, so an unknown key is a refusal" true rather than documented.

Four committed schemas say that about the records this plugin emits, and until
this module nothing enforced any of it. A guarantee stated in a schema and
checked nowhere is a guarantee a reader will rely on and a record will quietly
break.

This is a bounded subset of JSON Schema draft-07: exactly the keywords the four
committed schemas use, and no others. An unsupported keyword is a refusal
rather than something silently ignored, because a schema quietly half-checked is
worse than one not checked at all.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SUPPORTED = frozenset({
    "$id", "$schema", "title", "description",
    "type", "const", "enum",
    "required", "properties", "additionalProperties", "definitions", "$ref",
    "items", "minItems", "maxItems",
    "minLength", "maxLength",
    "minimum", "maximum",
    "pattern",
})

TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}

MAX_DEPTH = 32


class SchemaError(Exception):
    """One named refusal while checking a record against its schema."""


def _kind(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _matches_type(value, declared) -> bool:
    names = declared if isinstance(declared, list) else [declared]
    for name in names:
        expected = TYPES.get(name)
        if expected is None:
            raise SchemaError(f"the schema declares an unknown type {name!r}")
        # A boolean is an int in Python and is not an integer in JSON Schema.
        if name in ("integer", "number") and isinstance(value, bool):
            continue
        if isinstance(value, expected):
            return True
    return False


def _resolve(node: dict, root: dict) -> dict:
    reference = node["$ref"]
    if not reference.startswith("#/definitions/"):
        raise SchemaError(f"the schema uses an unsupported reference {reference!r}")
    name = reference[len("#/definitions/"):]
    definitions = root.get("definitions", {})
    if name not in definitions:
        raise SchemaError(f"the schema references a missing definition {name!r}")
    return definitions[name]


def _check(value, node: dict, root: dict, path: str, depth: int) -> list[str]:
    if depth > MAX_DEPTH:
        raise SchemaError(f"the schema nests past the {MAX_DEPTH}-level cap at {path}")
    unsupported = sorted(set(node) - SUPPORTED)
    if unsupported:
        raise SchemaError(
            f"the schema at {path} uses unsupported keyword(s) "
            + ", ".join(repr(name) for name in unsupported)
        )
    if "$ref" in node:
        return _check(value, _resolve(node, root), root, path, depth + 1)

    findings: list[str] = []
    if "const" in node and value != node["const"]:
        findings.append(f"{path}: expected {node['const']!r}, found {value!r}")
    if "enum" in node and value not in node["enum"]:
        findings.append(
            f"{path}: {value!r} is not one of "
            + ", ".join(repr(item) for item in node["enum"])
        )
    if "type" in node and not _matches_type(value, node["type"]):
        findings.append(
            f"{path}: expected type {node['type']!r}, found {_kind(value)}"
        )
        # Every further keyword assumes the type held, so stop on this branch.
        return findings

    if isinstance(value, str):
        if "minLength" in node and len(value) < node["minLength"]:
            findings.append(
                f"{path}: {len(value)} characters, under the "
                f"{node['minLength']}-character minimum"
            )
        if "maxLength" in node and len(value) > node["maxLength"]:
            findings.append(
                f"{path}: {len(value)} characters, over the "
                f"{node['maxLength']}-character maximum"
            )
        if "pattern" in node and not re.search(node["pattern"], value):
            findings.append(f"{path}: {value!r} does not match {node['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in node and value < node["minimum"]:
            findings.append(f"{path}: {value} is under the minimum {node['minimum']}")
        if "maximum" in node and value > node["maximum"]:
            findings.append(f"{path}: {value} is over the maximum {node['maximum']}")

    if isinstance(value, list):
        if "minItems" in node and len(value) < node["minItems"]:
            findings.append(
                f"{path}: {len(value)} item(s), under the minimum {node['minItems']}"
            )
        if "maxItems" in node and len(value) > node["maxItems"]:
            findings.append(
                f"{path}: {len(value)} item(s), over the maximum {node['maxItems']}"
            )
        if "items" in node:
            for index, entry in enumerate(value):
                findings.extend(
                    _check(entry, node["items"], root, f"{path}[{index}]", depth + 1)
                )

    if isinstance(value, dict):
        properties = node.get("properties", {})
        for name in node.get("required", []):
            if name not in value:
                findings.append(f"{path}: required key {name!r} is absent")
        if node.get("additionalProperties") is False:
            for name in sorted(set(value) - set(properties)):
                findings.append(f"{path}: unknown key {name!r}")
        for name, entry in sorted(value.items()):
            if name in properties:
                findings.extend(
                    _check(
                        entry, properties[name], root,
                        f"{path}.{name}" if path else name, depth + 1,
                    )
                )
            elif isinstance(node.get("additionalProperties"), dict):
                findings.extend(
                    _check(
                        entry, node["additionalProperties"], root,
                        f"{path}.{name}" if path else name, depth + 1,
                    )
                )
    return findings


def check_record(record: dict, schema_path: Path) -> list[str]:
    """Every way `record` breaches the schema at `schema_path`, or an empty list."""
    if schema_path.is_symlink() or not schema_path.is_file():
        raise SchemaError(f"{schema_path.name} is not a regular file")
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SchemaError(f"{schema_path.name} is not readable as JSON: {error}") from error
    if not isinstance(schema, dict):
        raise SchemaError(f"{schema_path.name} is not one JSON object")
    return _check(record, schema, schema, "", 0)


def schema_for(identifier: str) -> Path:
    """The committed schema publishing `identifier`, or a named refusal."""
    root = Path(__file__).resolve().parents[2] / "schemas"
    for path in sorted(root.glob("*.json")):
        try:
            published = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        declared = published.get("properties", {}).get("schema", {}).get("const")
        if declared == identifier:
            return path
    raise SchemaError(f"no committed schema publishes {identifier!r}")


def check(record: dict) -> list[str]:
    """Check a record against whichever committed schema it declares."""
    identifier = record.get("schema")
    if not identifier:
        raise SchemaError("the record declares no schema, so none can be found")
    return check_record(record, schema_for(identifier))
