"""Reading untrusted JSON documents.

Size is checked before the read, depth during parsing, and duplicate keys
are refused: the second spelling of a key is how a checked value and a used
value end up being different values.
"""

import json
import os

from . import BereanError

MAX_JSON_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 32


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise BereanError(f"duplicate key: {key!r}")
        out[key] = value
    return out


def _check_depth(value, depth, path):
    if depth > MAX_DEPTH:
        raise BereanError(f"document deeper than {MAX_DEPTH} at {path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _check_depth(item, depth + 1, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _check_depth(item, depth + 1, f"{path}[{index}]")


def loads(text, what="document"):
    if len(text.encode("utf-8")) > MAX_JSON_BYTES:
        raise BereanError(f"{what} over the {MAX_JSON_BYTES} byte ceiling")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_float=_refuse_float,
            parse_constant=_refuse_float,
        )
    except BereanError:
        raise
    except ValueError as error:
        raise BereanError(f"{what} is not JSON: {error}") from error
    _check_depth(value, 0, "$")
    return value


def _refuse_float(text):
    raise BereanError(f"float in document: {text}")


def load(path, what=None):
    what = what or os.path.basename(path)
    if os.path.islink(path):
        raise BereanError(f"refusing symlink: {path}")
    if not os.path.isfile(path):
        raise BereanError(f"not a regular file: {path}")
    if os.stat(path).st_size > MAX_JSON_BYTES:
        raise BereanError(f"{what} over the {MAX_JSON_BYTES} byte ceiling")
    with open(path, "rb") as handle:
        data = handle.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BereanError(f"{what} is not UTF-8: {error}") from error
    return loads(text, what)


def require(document, fields, what):
    """Hold a document to a closed field table."""
    if not isinstance(document, dict):
        raise BereanError(f"{what} is not an object")
    missing = [name for name in fields if name not in document]
    if missing:
        raise BereanError(f"{what} is missing {', '.join(sorted(missing))}")
    unknown = [name for name in document if name not in fields]
    if unknown:
        raise BereanError(f"{what} carries undeclared fields: {', '.join(sorted(unknown))}")
    return document


def whole_number(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BereanError(f"{what} is not a whole number: {value!r}")
    return value


def stated(value, what):
    if not isinstance(value, str) or not value.strip():
        raise BereanError(f"{what} is blank or not a string")
    return value


def write_canonical(path, document, dumps):
    """Stage the canonical bytes beside the destination and land with one rename."""
    text = dumps(document) + "\n"
    directory = os.path.dirname(os.path.abspath(path)) or "."
    staging = os.path.join(directory, f".{os.path.basename(path)}.staging")
    with open(staging, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(staging, path)
