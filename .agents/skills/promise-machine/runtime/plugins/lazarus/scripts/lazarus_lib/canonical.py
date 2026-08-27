"""Strict JSON input and deterministic JSON/JSONL output."""

from __future__ import annotations

import json
from itertools import islice
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any, Callable, Iterable, Sequence

from .errors import FormatError, ResourceLimitError


MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_JSONL_BYTES = 512 * 1024 * 1024
MAX_RECORD_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 100_000
MAX_DEPTH = 64
MAX_CONTAINER_ITEMS = 100_000
_SURROGATE_CODE_POINT = re.compile(r"[\ud800-\udfff]")


def _reject_duplicate_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise FormatError("duplicate JSON key")
        result[key] = value
    return result


def _reject_number(value: str) -> None:
    raise FormatError("non-integer JSON number is not allowed")


def _check_shape(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise ResourceLimitError(f"JSON nesting exceeds {MAX_DEPTH}")
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, str):
        if _SURROGATE_CODE_POINT.search(value) is not None:
            raise FormatError("JSON string contains a surrogate code point")
        return
    if isinstance(value, float):
        raise FormatError("floating-point values are not allowed")
    if isinstance(value, dict):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise ResourceLimitError("JSON object has too many members")
        for key, item in value.items():
            if not isinstance(key, str):
                raise FormatError("JSON object keys must be strings")
            if _SURROGATE_CODE_POINT.search(key) is not None:
                raise FormatError("JSON object key contains a surrogate code point")
            _check_shape(item, depth=depth + 1)
        return
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise ResourceLimitError("JSON array has too many items")
        for item in value:
            _check_shape(item, depth=depth + 1)
        return
    raise FormatError(f"unsupported JSON value: {type(value).__name__}")


def loads(data: bytes | str, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    """Parse strict UTF-8 JSON, rejecting duplicate keys and non-integers."""

    encoding_failure = False
    try:
        raw = data.encode("utf-8") if isinstance(data, str) else data
    except UnicodeEncodeError:
        encoding_failure = True
    if encoding_failure:
        raise FormatError("JSON input cannot be encoded as UTF-8")
    if len(raw) > max_bytes:
        raise ResourceLimitError(f"JSON input exceeds {max_bytes} bytes")
    decoding_failure = False
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        decoding_failure = True
    if decoding_failure:
        raise FormatError("JSON input is not UTF-8")
    parse_failure = None
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except FormatError:
        raise
    except json.JSONDecodeError as exc:
        parse_failure = f"invalid JSON at line {exc.lineno} column {exc.colno}"
    except (RecursionError, ValueError):
        parse_failure = "invalid JSON"
    if parse_failure is not None:
        raise FormatError(parse_failure)
    _check_shape(value)
    return value


def load(path: str | Path, *, max_bytes: int = MAX_JSON_BYTES) -> Any:
    file_path = Path(path)
    data = _read_regular(file_path, max_bytes=max_bytes, label="JSON input")
    return loads(data, max_bytes=max_bytes)


def dumps(value: Any) -> bytes:
    """Return compact, key-sorted UTF-8 JSON without a trailing newline."""

    _check_shape(value)
    try:
        text = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise FormatError(f"value is not canonical JSON: {exc}") from exc
    return text.encode("utf-8")


def dump(
    path: str | Path,
    value: Any,
    *,
    max_bytes: int = MAX_JSON_BYTES,
) -> bytes:
    data = dumps(value) + b"\n"
    if len(data) > max_bytes:
        raise ResourceLimitError(f"JSON output exceeds {max_bytes} bytes")
    _atomic_write(Path(path), data)
    return data


def dump_jsonl(
    path: str | Path,
    records: Iterable[Any],
    *,
    sort_key: Callable[[Any], Any] | None = None,
    max_bytes: int = MAX_JSONL_BYTES,
    max_record_bytes: int = MAX_RECORD_BYTES,
    max_records: int = MAX_RECORDS,
) -> bytes:
    materialised = list(islice(records, max_records + 1))
    if len(materialised) > max_records:
        raise ResourceLimitError(f"JSONL record count exceeds {max_records}")
    if sort_key is not None:
        materialised.sort(key=sort_key)
    encoded: list[bytes] = []
    total = 0
    for number, record in enumerate(materialised, 1):
        line = dumps(record) + b"\n"
        if len(line) > max_record_bytes:
            raise ResourceLimitError(
                f"JSONL record {number} exceeds {max_record_bytes} bytes"
            )
        total += len(line)
        if total > max_bytes:
            raise ResourceLimitError(f"JSONL output exceeds {max_bytes} bytes")
        encoded.append(line)
    data = b"".join(encoded)
    _atomic_write(Path(path), data)
    return data


def loads_jsonl(
    data: bytes,
    *,
    max_bytes: int = MAX_JSONL_BYTES,
    max_record_bytes: int = MAX_RECORD_BYTES,
    max_records: int = MAX_RECORDS,
) -> list[Any]:
    if len(data) > max_bytes:
        raise ResourceLimitError(f"JSONL input exceeds {max_bytes} bytes")
    records: list[Any] = []
    for line_number, line in enumerate(data.splitlines(keepends=True), 1):
        if line_number > max_records:
            raise ResourceLimitError(f"JSONL record count exceeds {max_records}")
        if len(line) > max_record_bytes:
            raise ResourceLimitError(
                f"JSONL record {line_number} exceeds {max_record_bytes} bytes"
            )
        if not line.endswith(b"\n"):
            raise FormatError(f"JSONL record {line_number} has no trailing newline")
        if not line.strip():
            raise FormatError(f"JSONL record {line_number} is empty")
        records.append(loads(line, max_bytes=max_record_bytes))
    return records


def load_jsonl(
    path: str | Path,
    *,
    max_bytes: int = MAX_JSONL_BYTES,
    max_record_bytes: int = MAX_RECORD_BYTES,
    max_records: int = MAX_RECORDS,
) -> list[Any]:
    file_path = Path(path)
    data = _read_regular(file_path, max_bytes=max_bytes, label="JSONL input")
    return loads_jsonl(
        data,
        max_bytes=max_bytes,
        max_record_bytes=max_record_bytes,
        max_records=max_records,
    )


def _read_regular(path: Path, *, max_bytes: int, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise FormatError(f"cannot open {label} {path}: {exc}") from exc
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode):
            raise FormatError(f"{label} is not a regular file: {path}")
        if details.st_size > max_bytes:
            raise ResourceLimitError(f"{label} exceeds {max_bytes} bytes")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ResourceLimitError(f"{label} exceeds {max_bytes} bytes")
        after = os.fstat(descriptor)
        if (details.st_size, details.st_mtime_ns, details.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise FormatError(f"{label} changed while it was read: {path}")
        return data
    except OSError as exc:
        raise FormatError(f"cannot read {label} {path}: {exc}") from exc
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, data: bytes) -> None:
    parent = path.parent
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=parent
        )
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    except OSError as exc:
        raise FormatError(f"cannot write {path}: {exc}") from exc
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
