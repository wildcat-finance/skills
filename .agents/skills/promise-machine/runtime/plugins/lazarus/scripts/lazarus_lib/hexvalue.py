"""Strict Ethereum hex bytes and quantity conversions."""

from __future__ import annotations

import re

from .errors import FormatError


QUANTITY = re.compile(r"^0x(?:0|[1-9a-f][0-9a-f]{0,63})$")
HEX_BYTES = re.compile(r"^0x(?:[0-9a-fA-F]{2})*$")


def hex_bytes(value: str, *, label: str = "hex value", length: int | None = None) -> bytes:
    if not isinstance(value, str) or HEX_BYTES.fullmatch(value) is None:
        raise FormatError(f"{label} must be 0x-prefixed, even-length hex bytes")
    raw = bytes.fromhex(value[2:])
    if length is not None and len(raw) != length:
        raise FormatError(f"{label} must be exactly {length} bytes")
    return raw


def quantity(value: str, *, label: str = "quantity") -> int:
    if not isinstance(value, str) or QUANTITY.fullmatch(value) is None:
        raise FormatError(f"{label} is not a canonical unsigned 256-bit quantity")
    return int(value[2:], 16)


def quantity_bytes(value: str, *, label: str = "quantity") -> bytes:
    number = quantity(value, label=label)
    if number == 0:
        return b""
    return number.to_bytes((number.bit_length() + 7) // 8, "big")


def uint_from_rlp(value: bytes, *, label: str = "integer") -> int:
    if not isinstance(value, bytes):
        raise FormatError(f"{label} must be an RLP byte string")
    if len(value) > 32:
        raise FormatError(f"{label} exceeds 256 bits")
    if value.startswith(b"\x00"):
        raise FormatError(f"{label} has a leading zero byte")
    return int.from_bytes(value, "big")


def address_bytes(value: str) -> bytes:
    return hex_bytes(value, label="address", length=20)


def slot_bytes(value: str) -> bytes:
    return hex_bytes(value, label="storage key", length=32)


def hash32_bytes(value: str, *, label: str = "hash") -> bytes:
    return hex_bytes(value, label=label, length=32)


def encode_hex(value: bytes) -> str:
    return "0x" + value.hex()
