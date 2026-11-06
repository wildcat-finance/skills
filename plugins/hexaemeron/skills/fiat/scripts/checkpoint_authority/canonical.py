"""Bounded protocol JSON; canonical bytes have no trailing newline."""
from __future__ import annotations

import hashlib
import json

MAX_RECORD_BYTES = 65536
MAX_DEPTH = 32
MAX_ENTRIES = 65536
MAX_TOTAL_BYTES = 256 * 1024 * 1024
MAX_INTEGER = 2**63 - 1


class Refusal(ValueError):
    """Expose a fixed code and stage, never input values or child diagnostics."""

    def __init__(self, code: str, stage: str = "record"):
        self.code = code
        self.stage = stage
        super().__init__(code)

    def event(self):
        return {"event": "checkpoint_authority_refused", "stage": self.stage,
                "code": self.code, "complete": False}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("duplicate-key")
        result[key] = value
    return result


def _noninteger(value):
    raise Refusal("noninteger-number")


def _integer(value):
    if len(value) > 20:
        raise Refusal("integer-limit")
    number = int(value)
    if not -MAX_INTEGER <= number <= MAX_INTEGER:
        raise Refusal("integer-limit")
    return number


def _walk(value, depth=0, active=None):
    if depth > MAX_DEPTH:
        raise Refusal("depth-limit")
    if active is None:
        active = set()
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -MAX_INTEGER <= value <= MAX_INTEGER:
            raise Refusal("integer-limit")
        return
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeError:
            raise Refusal("invalid-unicode") from None
        return
    if type(value) not in (dict, list):
        raise Refusal("invalid-json-type")
    if id(value) in active:
        raise Refusal("cyclic-json")
    active.add(id(value))
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise Refusal("invalid-json-key")
            _walk(key, depth + 1, active)
            _walk(child, depth + 1, active)
    else:
        for child in value:
            _walk(child, depth + 1, active)
    active.remove(id(value))


def canonical(value, *, limit=MAX_RECORD_BYTES) -> bytes:
    """Encode exact JSON types as sorted, compact ASCII-escaped UTF-8."""
    _walk(value)
    data = json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")
    if len(data) > limit:
        raise Refusal("byte-limit")
    return data


def decode(data: bytes, *, require_canonical=False, limit=MAX_RECORD_BYTES):
    """Read bounded strict UTF-8; reject duplicate keys and noninteger numbers."""
    if type(data) is not bytes:
        raise Refusal("bytes-required")
    if len(data) > limit:
        raise Refusal("byte-limit")
    try:
        text = data.decode("utf-8")
        # Bound nesting before the native JSON parser consumes the input.
        depth = 0
        quoted = escaped = False
        for char in text:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > MAX_DEPTH:
                    raise Refusal("depth-limit")
            elif char in "]}":
                depth -= 1
        value = json.loads(text, object_pairs_hook=_pairs, parse_int=_integer,
                           parse_float=_noninteger, parse_constant=_noninteger)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise Refusal("invalid-json") from None
    encoded = canonical(value, limit=limit)
    if require_canonical and encoded != data:
        raise Refusal("noncanonical-json")
    return value
