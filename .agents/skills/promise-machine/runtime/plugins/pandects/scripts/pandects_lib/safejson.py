"""JSON parsing with the bounds a document read from disk should have.

Deliberately duplicated rather than imported from a sibling plugin. Each plugin
in this repository is distributed on its own, so a dependency between two of
them is a dependency a user cannot satisfy by installing the one they wanted.
Thirty lines is the price of that.

Three things the standard parser does that a checker should not accept. It
reads a file of any size. It recurses until the stack gives out, which surfaces
as a crash rather than a refusal. And it keeps the last value for a repeated
key, so a catalogue carrying two `laws` entries parses as one and two readers
disagree about what it says.
"""

import json

DEFAULT_MAX_BYTES = 4 * 1024 * 1024
DEFAULT_MAX_DEPTH = 32

OPENING = {0x7B, 0x5B}  # { [
CLOSING = {0x7D, 0x5D}  # } ]
QUOTE = 0x22
BACKSLASH = 0x5C


class InputError(ValueError):
    """A document refused before it was parsed."""


def check_depth(data, max_depth):
    depth = 0
    in_string = False
    escaped = False
    for byte in bytearray(data):
        if in_string:
            if escaped:
                escaped = False
            elif byte == BACKSLASH:
                escaped = True
            elif byte == QUOTE:
                in_string = False
            continue
        if byte == QUOTE:
            in_string = True
        elif byte in OPENING:
            depth += 1
            if depth > max_depth:
                raise InputError(
                    "nested deeper than %d levels; refused before parsing" % max_depth
                )
        elif byte in CLOSING:
            depth -= 1


def no_duplicate_keys(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise InputError(
                "duplicate key %r; two readers of this document would disagree "
                "about what it says" % key
            )
        seen.add(key)
    return dict(pairs)


def loads(data, max_bytes=DEFAULT_MAX_BYTES, max_depth=DEFAULT_MAX_DEPTH):
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, bytes):
        raise InputError("expected bytes")
    if len(data) > max_bytes:
        raise InputError("%d bytes, over the %d byte cap" % (len(data), max_bytes))
    check_depth(data, max_depth)
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_keys)
    except UnicodeDecodeError as error:
        raise InputError("not UTF-8: %s" % error)
    except json.JSONDecodeError as error:
        raise InputError("not valid JSON: %s" % error)


def load_file(path, max_bytes=DEFAULT_MAX_BYTES, max_depth=DEFAULT_MAX_DEPTH):
    import os

    if not os.path.isfile(path):
        raise InputError("%s is not a regular file" % path)
    with open(path, "rb") as handle:
        return loads(handle.read(max_bytes + 1), max_bytes, max_depth)
