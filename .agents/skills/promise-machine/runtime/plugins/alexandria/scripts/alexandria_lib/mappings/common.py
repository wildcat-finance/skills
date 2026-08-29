"""Shared checks for versioned venue mappings."""

from __future__ import annotations

from ..canonical import load_bytes
from ..errors import AlexandriaError
from ..release import MAX_RAW_COMPONENT_BYTES, _resolve_pointer


def load_source(data, capture):
    return load_bytes(
        data,
        f"capture {capture['id']} mapping source",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )


def object_value(value, where):
    if not isinstance(value, dict):
        raise AlexandriaError(f"{where} must be an object")
    return value


def list_value(value, where):
    if not isinstance(value, list):
        raise AlexandriaError(f"{where} must be a list")
    return value


def required(mapping, key, where):
    object_value(mapping, where)
    if key not in mapping:
        raise AlexandriaError(f"{where} is missing {key}")
    return mapping[key]


def string(mapping, key, where):
    value = required(mapping, key, where)
    if not isinstance(value, str) or not value:
        raise AlexandriaError(f"{where}.{key} must be a non-empty string")
    return value


def integer(mapping, key, where, *, minimum=0, maximum=None):
    value = required(mapping, key, where)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AlexandriaError(f"{where}.{key} must be an integer")
    if maximum is not None and value > maximum:
        raise AlexandriaError(f"{where}.{key} is above its limit")
    return value


def decimal(mapping, key, where):
    value = string(mapping, key, where)
    if not value.isdigit() or (len(value) > 1 and value.startswith("0")) or len(value) > 78:
        raise AlexandriaError(f"{where}.{key} must be a canonical decimal string")
    return value


def pointer_escape(value):
    return value.replace("~", "~0").replace("/", "~1")


def coverage_by_selector(capture):
    return {
        item["selector"]: item
        for item in capture["coverage"]["collections"]
    }


def require_coverage(capture, expected):
    """Require exact selector/count coverage for every mapping source list."""
    declared = coverage_by_selector(capture)
    if set(declared) != set(expected):
        missing = sorted(set(expected) - set(declared))
        extra = sorted(set(declared) - set(expected))
        detail = missing[0] if missing else extra[0]
        raise AlexandriaError(
            f"capture {capture['id']} coverage does not match mapping source at {detail}"
        )
    for selector, count in expected.items():
        if declared[selector]["record_count"] != count:
            raise AlexandriaError(
                f"capture {capture['id']} coverage count disagrees at {selector}"
            )
    return declared


def resolve_selector(source, selector):
    return _resolve_pointer(source, selector)


def enforce_subject_scope(capture, rows):
    if capture["scope"]["kind"] != "subject-scoped":
        return
    allowed = set(capture["scope"]["subjects"])
    actual = {row["subject"] for row in rows}
    outside = actual - allowed
    if outside:
        raise AlexandriaError(
            f"mapping produced subject {sorted(outside)[0]} outside capture scope"
        )


def coverage_declaration(capture, *, mapped, context, unsupported):
    source_records = capture["coverage"]["record_count"]
    mapped_records = sum(mapped.values())
    context_records = sum(context.values())
    unsupported_records = sum(unsupported.values())
    if mapped_records + context_records + unsupported_records != source_records:
        raise AlexandriaError(
            f"capture {capture['id']} mapping coverage does not reconcile to source coverage"
        )
    return {
        "context_collections": dict(sorted(context.items())),
        "context_records": context_records,
        "mapped_collections": dict(sorted(mapped.items())),
        "mapped_records": mapped_records,
        "source_records": source_records,
        "unsupported_collections": dict(sorted(unsupported.items())),
        "unsupported_records": unsupported_records,
    }
