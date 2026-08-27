"""Canonical JSON, bounded integer rules and SHA-256 helpers."""

import hashlib
import json
import math
import os
from pathlib import Path
import tempfile


MAX_SAFE_INTEGER = 9_007_199_254_740_991


class TabulariumError(ValueError):
    """Input or event data that cannot safely enter a release."""


def _no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TabulariumError("duplicate JSON key %r" % key)
        result[key] = value
    return result


def _reject_constant(value):
    raise TabulariumError("non-finite JSON number %s" % value)


def load_json(path):
    """Read UTF-8 JSON without accepting duplicate keys or non-finite numbers."""
    return loads_json(Path(path).read_bytes(), str(path))


def loads_json(data, where="document"):
    """Parse JSON bytes without accepting duplicate keys or non-finite numbers."""
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except TabulariumError:
        raise
    except UnicodeDecodeError as error:
        raise TabulariumError("%s is not UTF-8: %s" % (where, error)) from error
    except (json.JSONDecodeError, ValueError, RecursionError) as error:
        raise TabulariumError("%s is not valid JSON: %s" % (where, error)) from error


def canonical_json(value):
    """Return explicit canonical UTF-8 JSON bytes with no trailing newline."""
    try:
        ensure_finite_tree(value)
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise TabulariumError("value cannot be canonical JSON: %s" % error) from error


def jsonl_bytes(rows):
    """One canonical JSON value and one newline per row, in caller order."""
    return b"".join(canonical_json(row) + b"\n" for row in rows)


def write_jsonl(rows, path):
    data = jsonl_bytes(rows)
    write_bytes_atomic(data, path)
    return data


def write_bytes_atomic(data, path):
    """Replace one file without following a last-moment output symlink."""
    target = Path(path)
    temporary = None
    descriptor = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=target.parent,
            prefix=".%s." % target.name,
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_integer(value, where):
    """Accept an actual JSON integer only when other JSON readers preserve it."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TabulariumError("%s is not an integer: %r" % (where, value))
    if not 0 <= value <= MAX_SAFE_INTEGER:
        raise TabulariumError("%s is outside the safe integer range: %r" % (where, value))
    return value


def ensure_finite_tree(value, where="value"):
    """Reject floats that canonical JSON would otherwise serialise imprecisely."""
    pending = [(value, where)]
    while pending:
        current, current_where = pending.pop()
        if isinstance(current, float):
            if not math.isfinite(current):
                raise TabulariumError(
                    "%s contains a non-finite number" % current_where
                )
            raise TabulariumError(
                "%s contains a floating-point number" % current_where
            )
        if isinstance(current, int) and not isinstance(current, bool):
            if not -MAX_SAFE_INTEGER <= current <= MAX_SAFE_INTEGER:
                raise TabulariumError(
                    "%s contains an integer outside the safe range" % current_where
                )
        if isinstance(current, dict):
            pending.extend(
                (child, "%s.%s" % (current_where, key))
                for key, child in current.items()
            )
        elif isinstance(current, list):
            pending.extend(
                (child, "%s[%d]" % (current_where, index))
                for index, child in enumerate(current)
            )
