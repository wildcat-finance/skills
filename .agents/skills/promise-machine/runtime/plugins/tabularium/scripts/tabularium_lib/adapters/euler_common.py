"""Shared validation and result types for the Euler release adapters."""

from dataclasses import dataclass
import re

from ..core import MAX_SAFE_INTEGER, TabulariumError, ensure_finite_tree


ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH = re.compile(r"^0x[0-9a-fA-F]{64}$")
DECIMAL = re.compile(r"^(0|[1-9][0-9]*)$")


@dataclass(frozen=True)
class MappingResult:
    events: tuple
    mapped_counts: dict
    unmapped_counts: dict


def object_(value, where):
    if not isinstance(value, dict):
        raise TabulariumError("%s is not an object" % where)
    ensure_finite_tree(value, where)
    return value


def list_(value, where):
    if not isinstance(value, list):
        raise TabulariumError("%s is not an array" % where)
    return value


def required(mapping, key, where):
    mapping = object_(mapping, where)
    if key not in mapping:
        raise TabulariumError("%s has no %r" % (where, key))
    return mapping[key]


def text(mapping, key, where):
    value = required(mapping, key, where)
    if not isinstance(value, str) or not value:
        raise TabulariumError("%s.%s is not a non-empty string" % (where, key))
    return value


def address(mapping, key, where):
    value = text(mapping, key, where)
    if not ADDRESS.fullmatch(value):
        raise TabulariumError("%s.%s is not an Ethereum address" % (where, key))
    return value.lower()


def hash_(mapping, key, where):
    value = text(mapping, key, where)
    if not HASH.fullmatch(value):
        raise TabulariumError("%s.%s is not a 32-byte hash" % (where, key))
    return value.lower()


def integer(mapping, key, where, maximum=MAX_SAFE_INTEGER):
    value = required(mapping, key, where)
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise TabulariumError("%s.%s is not a safe unsigned integer" % (where, key))
    return value


def decimal(mapping, key, where):
    value = text(mapping, key, where)
    if not DECIMAL.fullmatch(value):
        raise TabulariumError("%s.%s is not an unsigned decimal string" % (where, key))
    return value


def bounded_decimal_integer(mapping, key, where, maximum=MAX_SAFE_INTEGER):
    value = decimal(mapping, key, where)
    limit = str(maximum)
    if len(value) > len(limit) or (len(value) == len(limit) and value > limit):
        raise TabulariumError("%s.%s is outside the safe integer range" % (where, key))
    return int(value)


def hex_integer(value, where):
    if not isinstance(value, str) or not value.startswith("0x") or not value[2:]:
        raise TabulariumError("%s is not a JSON-RPC hex integer" % where)
    try:
        result = int(value[2:], 16)
    except ValueError as error:
        raise TabulariumError("%s is not hexadecimal" % where) from error
    if result > MAX_SAFE_INTEGER:
        raise TabulariumError("%s is outside the safe integer range" % where)
    return result


def topic_address(value, where):
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        raise TabulariumError("%s is not a 32-byte topic" % where)
    if value[2:26] != "0" * 24:
        raise TabulariumError("%s is not a zero-padded address topic" % where)
    candidate = "0x" + value[-40:]
    if not ADDRESS.fullmatch(candidate):
        raise TabulariumError("%s does not contain an address" % where)
    return candidate.lower()


def abi_words(value, count, where):
    if not isinstance(value, str) or len(value) != 2 + 64 * count or not value.startswith("0x"):
        raise TabulariumError("%s is not exactly %d ABI word(s)" % (where, count))
    try:
        return [int(value[2 + 64 * index:2 + 64 * (index + 1)], 16) for index in range(count)]
    except ValueError as error:
        raise TabulariumError("%s is not hexadecimal" % where) from error


def word_address(value, where):
    if value >> 160:
        raise TabulariumError("%s is not a zero-padded address word" % where)
    return "0x%040x" % value
