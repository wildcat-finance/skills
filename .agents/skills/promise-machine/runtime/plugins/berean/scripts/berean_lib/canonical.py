"""Canonical JSON for digested documents.

One spelling per document: sorted keys, compact separators, UTF-8 without
escaping, no trailing newline. Floats are refused rather than serialised,
because two runtimes disagree about their text long before they disagree
about anything else, and a digest over disagreeing bytes pins nothing.
"""

import json
import math

from . import BereanError


def _refuse_floats(value, path):
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise BereanError(f"non-finite number at {path}")
        raise BereanError(f"float at {path}; canonical documents carry integers and strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise BereanError(f"non-string key at {path}")
            _refuse_floats(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _refuse_floats(item, f"{path}[{index}]")
    elif value is not None and not isinstance(value, (str, int, bool)):
        raise BereanError(f"unserialisable value at {path}: {type(value).__name__}")


def dumps(value):
    """Serialise to the one canonical spelling, refusing floats."""
    _refuse_floats(value, "$")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def encode(value):
    """Canonical bytes for digesting."""
    return dumps(value).encode("utf-8")
