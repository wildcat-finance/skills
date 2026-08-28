"""JSON parsing for documents that arrived from somebody else.

Three things the standard parser will do that a verifier should not. It will
read a file of any size into memory. It will recurse until the stack gives out,
which surfaces as a crash rather than a refusal. And it keeps the last value
for a repeated key, so a document carrying two `predicateType` entries parses as
one and two readers can disagree about which.

The depth check runs over the bytes before parsing rather than catching the
overflow afterwards, because by the time the stack is gone there is no room left
to report anything useful.
"""

import json
import math
from decimal import Decimal, DecimalException

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
DEFAULT_MAX_DEPTH = 64

OPENING = {0x7B: 0x7D, 0x5B: 0x5D}  # { [
CLOSING = {0x7D, 0x5D}  # } ]
QUOTE = 0x22
BACKSLASH = 0x5C


class InputError(ValueError):
    """A document refused before it was parsed."""


def check_depth(data, max_depth=DEFAULT_MAX_DEPTH):
    """Refuse nesting past max_depth, counting brackets outside strings."""
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
                    "nested deeper than %d levels; refused before parsing"
                    % max_depth
                )
        elif byte in CLOSING:
            depth -= 1


def no_duplicate_keys(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise InputError(
                "duplicate key %r; two readers of this document would disagree "
                "about which value it holds" % key
            )
        seen.add(key)
    return dict(pairs)


def no_non_json_constant(value):
    """Refuse Python's NaN and infinity extensions to the JSON grammar."""
    raise InputError("non-JSON numeric constant %s" % value)


def finite_json_float(value):
    """Refuse float overflow and preserve exact integral JSON numbers."""
    try:
        parsed = float(value)
    except (OverflowError, ValueError):
        raise InputError("JSON number is outside the finite float range")
    if not math.isfinite(parsed):
        raise InputError("JSON number is outside the finite float range")
    try:
        exact = Decimal(value)
        if exact == exact.to_integral_value():
            return int(exact)
    except (DecimalException, OverflowError, ValueError):
        raise InputError("JSON number is outside the supported decimal range")
    return parsed


def bounded_json_integer(value):
    """Turn Python's integer digit ceiling into an ordinary input refusal."""
    try:
        return int(value)
    except ValueError:
        raise InputError("JSON integer exceeds the parser's digit bound")


def loads(data, max_bytes=DEFAULT_MAX_BYTES, max_depth=DEFAULT_MAX_DEPTH):
    if max_bytes < 1 or max_depth < 1:
        raise InputError(
            "bounds must be positive, got max_bytes=%r max_depth=%r"
            % (max_bytes, max_depth)
        )
    if isinstance(data, str):
        data = data.encode("utf-8")
    if not isinstance(data, bytes):
        raise InputError("expected bytes")
    if len(data) > max_bytes:
        raise InputError(
            "%d bytes, over the %d byte cap" % (len(data), max_bytes)
        )
    check_depth(data, max_depth)
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=no_duplicate_keys,
            parse_constant=no_non_json_constant,
            parse_float=finite_json_float,
            parse_int=bounded_json_integer,
        )
    except UnicodeDecodeError as error:
        raise InputError("not UTF-8: %s" % error)
    except json.JSONDecodeError as error:
        raise InputError("not valid JSON: %s" % error)


def loader(max_bytes=DEFAULT_MAX_BYTES, max_depth=DEFAULT_MAX_DEPTH):
    """A one-argument loads, for passing to a parser that takes one."""

    def load(data):
        return loads(data, max_bytes, max_depth)

    return load
