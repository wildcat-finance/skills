"""Owned canonical JSON subset used by Alexandria control documents."""

from __future__ import annotations

import json

from .errors import AlexandriaError


MAX_CONTROL_BYTES = 8 * 1024 * 1024
MAX_INTEGER_DIGITS = 78
MAX_NESTING = 64
MAX_NODES = 200_000


def canonical_bytes(value) -> bytes:
    """Encode the owned JSON subset as UTF-8 with one trailing newline."""
    _check_tree(value)
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return (text + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise AlexandriaError("value is outside Alexandria's JSON subset") from exc


def load_bytes(data: bytes, label: str = "JSON document", *, max_bytes=MAX_CONTROL_BYTES):
    """Parse JSON while rejecting ambiguous or resource-heavy control input."""
    if max_bytes is not None and len(data) > max_bytes:
        raise AlexandriaError(f"{label} exceeds the {max_bytes}-byte limit")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AlexandriaError(f"{label} is not UTF-8") from exc
    if text.startswith("\ufeff"):
        raise AlexandriaError(f"{label} must not start with a UTF-8 BOM")

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AlexandriaError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def parse_int(value):
        digits = value.lstrip("-")
        if len(digits) > MAX_INTEGER_DIGITS:
            raise AlexandriaError(
                f"{label} contains an integer longer than {MAX_INTEGER_DIGITS} digits"
            )
        return int(value)

    def reject_float(_value):
        raise AlexandriaError(f"{label} contains a floating-point number")

    def reject_constant(_value):
        raise AlexandriaError(f"{label} contains a non-finite number")

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_int=parse_int,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except AlexandriaError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise AlexandriaError(f"{label} is not valid JSON") from exc
    _check_tree(value, label)
    return value


def load_raw_json(
    data: bytes,
    label: str,
    *,
    max_bytes: int,
    max_nodes=MAX_NODES,
    preserve_integers=False,
):
    """Parse raw JSON for collection counts without narrowing valid numbers."""
    if len(data) > max_bytes:
        raise AlexandriaError(f"{label} exceeds the {max_bytes}-byte limit")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AlexandriaError(f"{label} is not UTF-8") from exc
    if text.startswith("\ufeff"):
        raise AlexandriaError(f"{label} must not start with a UTF-8 BOM")

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise AlexandriaError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def ignore_number(_value):
        return None

    def parse_integer(value):
        digits = value.lstrip("-")
        if len(digits) > MAX_INTEGER_DIGITS:
            raise AlexandriaError(
                f"{label} contains an integer longer than {MAX_INTEGER_DIGITS} digits"
            )
        return int(value)

    def reject_float(_value):
        raise AlexandriaError(f"{label} contains a floating-point number")

    def reject_constant(_value):
        raise AlexandriaError(f"{label} contains a non-finite number")

    try:
        value = json.loads(
            text,
            object_pairs_hook=pairs_hook,
            parse_int=parse_integer if preserve_integers else ignore_number,
            parse_float=reject_float if preserve_integers else ignore_number,
            parse_constant=reject_constant,
        )
    except AlexandriaError:
        raise
    except (json.JSONDecodeError, RecursionError) as exc:
        raise AlexandriaError(f"{label} is not valid JSON") from exc
    _check_tree(value, label, max_nodes=max_nodes)
    return value


def _check_tree(value, label: str = "JSON value", *, max_nodes=MAX_NODES) -> None:
    nodes = 0
    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            raise AlexandriaError(f"{label} exceeds the {max_nodes}-node limit")
        if depth > MAX_NESTING:
            raise AlexandriaError(f"{label} exceeds the nesting limit of {MAX_NESTING}")
        if isinstance(current, float):
            raise AlexandriaError(f"{label} contains a floating-point number")
        if isinstance(current, int) and not isinstance(current, bool):
            limit = 10 ** MAX_INTEGER_DIGITS
            if current <= -limit or current >= limit:
                raise AlexandriaError(
                    f"{label} contains an integer longer than {MAX_INTEGER_DIGITS} digits"
                )
            continue
        if current is None or isinstance(current, (str, bool)):
            continue
        if isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)
            continue
        if isinstance(current, dict):
            if not all(isinstance(key, str) for key in current):
                raise AlexandriaError(f"{label} contains a non-string object key")
            stack.extend((item, depth + 1) for item in current.values())
            continue
        raise AlexandriaError(f"{label} contains unsupported type {type(current).__name__}")
