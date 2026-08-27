"""Small strict Recursive Length Prefix codec for proof and header checks."""

from __future__ import annotations

from typing import TypeAlias

from .errors import FormatError


RLP: TypeAlias = bytes | list["RLP"]
MAX_DEPTH = 64


def encode(value: RLP) -> bytes:
    if isinstance(value, bytes):
        if len(value) == 1 and value[0] < 0x80:
            return value
        return _prefix(0x80, 0xB7, len(value)) + value
    if isinstance(value, list):
        payload = b"".join(encode(item) for item in value)
        return _prefix(0xC0, 0xF7, len(payload)) + payload
    raise FormatError(f"RLP value must be bytes or list, not {type(value).__name__}")


def encode_uint(value: int) -> bytes:
    """Encode one unsigned 256-bit integer as a canonical RLP string."""

    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise FormatError("RLP integer must be a non-negative whole number")
    if value.bit_length() > 256:
        raise FormatError("RLP integer exceeds 256 bits")
    raw = b"" if value == 0 else value.to_bytes((value.bit_length() + 7) // 8, "big")
    return encode(raw)


def _prefix(short_base: int, long_base: int, length: int) -> bytes:
    if length < 56:
        return bytes([short_base + length])
    encoded_length = length.to_bytes((length.bit_length() + 7) // 8, "big")
    if len(encoded_length) > 8:
        raise FormatError("RLP payload length is too large")
    return bytes([long_base + len(encoded_length)]) + encoded_length


def decode(data: bytes) -> RLP:
    if not isinstance(data, bytes):
        raise FormatError("RLP input must be bytes")
    try:
        value, offset = _decode_at(data, 0, len(data), 0)
    except RecursionError as exc:
        raise FormatError("RLP nesting is too deep") from exc
    if offset != len(data):
        raise FormatError("RLP input has trailing bytes")
    return value


def _decode_at(
    data: bytes,
    offset: int,
    boundary: int,
    depth: int,
) -> tuple[RLP, int]:
    if depth > MAX_DEPTH:
        raise FormatError("RLP nesting is too deep")
    if offset >= boundary:
        raise FormatError("truncated RLP item")
    prefix = data[offset]
    if prefix <= 0x7F:
        return bytes([prefix]), offset + 1
    if prefix <= 0xB7:
        length = prefix - 0x80
        start = offset + 1
        end = start + length
        _bounded(end, boundary)
        payload = data[start:end]
        if length == 1 and payload[0] < 0x80:
            raise FormatError("non-canonical single-byte RLP string")
        return payload, end
    if prefix <= 0xBF:
        length, start = _long_length(data, offset, boundary, 0xB7)
        if length < 56:
            raise FormatError("non-canonical long RLP string")
        end = start + length
        _bounded(end, boundary)
        return data[start:end], end
    if prefix <= 0xF7:
        length = prefix - 0xC0
        start = offset + 1
        end = start + length
        _bounded(end, boundary)
        return _decode_list(data, start, end, depth), end
    length, start = _long_length(data, offset, boundary, 0xF7)
    if length < 56:
        raise FormatError("non-canonical long RLP list")
    end = start + length
    _bounded(end, boundary)
    return _decode_list(data, start, end, depth), end


def _long_length(
    data: bytes,
    offset: int,
    boundary: int,
    base: int,
) -> tuple[int, int]:
    length_of_length = data[offset] - base
    start = offset + 1
    end = start + length_of_length
    _bounded(end, boundary)
    encoded = data[start:end]
    if not encoded or encoded[0] == 0:
        raise FormatError("non-canonical RLP length")
    return int.from_bytes(encoded, "big"), end


def _decode_list(data: bytes, start: int, end: int, depth: int) -> list[RLP]:
    values: list[RLP] = []
    offset = start
    while offset < end:
        value, offset = _decode_at(data, offset, end, depth + 1)
        values.append(value)
    if offset != end:
        raise FormatError("RLP list length does not match its payload")
    return values


def _bounded(end: int, boundary: int) -> None:
    if end > boundary:
        raise FormatError("truncated RLP payload")
