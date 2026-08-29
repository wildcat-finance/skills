"""Bounded strict JSON parsing and the policy's canonical JSON subset."""

from __future__ import annotations

import json
import os
import stat
import unicodedata
from typing import Any

from .errors import PolicyError, refuse


MAX_SAFE_INTEGER = 9_007_199_254_740_991
MAX_ACCEPTED_JOB_BYTES = 96 * 1024
MAX_JOBSPEC_BYTES = 32 * 1024
MAX_JSON_DEPTH = 12
MAX_JSON_MEMBERS = 512
MAX_JSON_SCALARS = 1_024
MAX_JSON_STRING_BYTES = 64 * 1024

_OPENING = {0x7B, 0x5B}  # { [
_CLOSING = {0x7D, 0x5D}  # } ]
_QUOTE = 0x22
_BACKSLASH = 0x5C
_FORBIDDEN_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})


def read_bounded_file(path: str | os.PathLike[str], max_bytes: int) -> bytes:
    """Read one stable regular file without following its final symlink."""

    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
        refuse("MP101", "read.limit")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(os.fspath(path), flags)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            refuse("MP100", "accepted_job.path")
        if before.st_size > max_bytes:
            refuse("MP101", "accepted_job.bytes")
        chunks: list[bytes] = []
        total = 0
        while total <= max_bytes:
            block = os.read(descriptor, min(65_536, max_bytes + 1 - total))
            if not block:
                break
            chunks.append(block)
            total += len(block)
        if total > max_bytes:
            refuse("MP101", "accepted_job.bytes")
        after = os.fstat(descriptor)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after or total != after.st_size:
            refuse("MP100", "accepted_job.stability")
        return b"".join(chunks)
    except PolicyError:
        raise
    except (OSError, TypeError, ValueError):
        refuse("MP100", "accepted_job.path")
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _check_depth(data: bytes, maximum: int) -> None:
    depth = 0
    in_string = False
    escaped = False
    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == _BACKSLASH:
                escaped = True
            elif byte == _QUOTE:
                in_string = False
            continue
        if byte == _QUOTE:
            in_string = True
        elif byte in _OPENING:
            depth += 1
            if depth > maximum:
                refuse("MP104", "json.depth")
        elif byte in _CLOSING:
            depth -= 1


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            refuse("MP105", "json.object")
        result[key] = value
    return result


def _integer(raw: str) -> int:
    if len(raw.lstrip("-")) > 16:
        refuse("MP109", "json.number")
    value = int(raw)
    if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
        refuse("MP109", "json.number")
    return value


def _floating(_raw: str) -> float:
    refuse("MP109", "json.number")


def _constant(_raw: str) -> None:
    refuse("MP109", "json.number")


def _check_string(value: str, field: str, maximum: int) -> None:
    if not isinstance(value, str):
        refuse("MP109", field)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        refuse("MP106", field)
    if len(encoded) > maximum:
        refuse("MP101", field)
    if unicodedata.normalize("NFC", value) != value:
        refuse("MP106", field)
    if any(unicodedata.category(character) in _FORBIDDEN_CATEGORIES for character in value):
        refuse("MP106", field)


def _check_tree(
    value: Any,
    *,
    max_members: int,
    max_scalars: int,
    max_string_bytes: int,
) -> None:
    pending: list[tuple[Any, str]] = [(value, "json")]
    members = 0
    scalars = 0
    while pending:
        current, field = pending.pop()
        if isinstance(current, dict):
            members += len(current)
            if members > max_members:
                refuse("MP101", "json.members")
            for key, child in current.items():
                _check_string(key, "json.key", max_string_bytes)
                pending.append((child, field))
            continue
        if isinstance(current, list):
            members += len(current)
            if members > max_members:
                refuse("MP101", "json.members")
            pending.extend((child, field) for child in current)
            continue
        scalars += 1
        if scalars > max_scalars:
            refuse("MP101", "json.scalars")
        if isinstance(current, str):
            _check_string(current, field, max_string_bytes)
        elif isinstance(current, float) or (
            isinstance(current, int)
            and not isinstance(current, bool)
            and not -MAX_SAFE_INTEGER <= current <= MAX_SAFE_INTEGER
        ):
            refuse("MP109", "json.number")
        elif current is not None and not isinstance(current, (bool, int)):
            refuse("MP109", "json.value")


def parse_json_bytes(
    data: bytes,
    *,
    max_bytes: int,
    max_depth: int = MAX_JSON_DEPTH,
    max_members: int = MAX_JSON_MEMBERS,
    max_scalars: int = MAX_JSON_SCALARS,
    max_string_bytes: int = MAX_JSON_STRING_BYTES,
) -> Any:
    """Parse strict UTF-8 JSON under limits applied before and after parsing."""

    if not isinstance(data, bytes):
        refuse("MP102", "json.encoding")
    if len(data) > max_bytes:
        refuse("MP101", "json.bytes")
    _check_depth(data, max_depth)
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        refuse("MP102", "json.encoding")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_int=_integer,
            parse_float=_floating,
            parse_constant=_constant,
        )
    except PolicyError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError):
        refuse("MP103", "json.document")
    _check_tree(
        value,
        max_members=max_members,
        max_scalars=max_scalars,
        max_string_bytes=max_string_bytes,
    )
    return value


def canonical_json(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes with no trailing newline."""

    _check_tree(
        value,
        max_members=MAX_JSON_MEMBERS,
        max_scalars=MAX_JSON_SCALARS,
        max_string_bytes=MAX_JSON_STRING_BYTES,
    )
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError):
        refuse("MP109", "canonical_json")


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase SHA-256 digest of exact bytes."""

    import hashlib

    return hashlib.sha256(data).hexdigest()
