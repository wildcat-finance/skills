#!/usr/bin/env python3
"""Check a target's assembly event emitters against their declarations.

`build` regenerates the emitter table and `check` compares a regenerated
table with the committed one. Both refuse with exit 2 until the scanner
lands; this module carries the argument parser and the Keccak-256 core.
"""

from __future__ import annotations

import argparse
import sys


# Keccak-256 permutation copied from
# plugins/tabularium/scripts/tabularium_lib/keccak.py; the padding differs
# from that copy at len % 136 == 135 (S1-R1-01). A root script does not import
# a plugin's private library, so the logic is carried here and pinned by
# tests/test_emitter_declarations.py.
_ROTATION = (
    0, 1, 62, 28, 27,
    36, 44, 6, 55, 20,
    3, 10, 43, 25, 39,
    41, 45, 15, 21, 8,
    18, 2, 61, 56, 14,
)
_ROUND = (
    0x0000000000000001, 0x0000000000008082,
    0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088,
    0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B,
    0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080,
    0x0000000080000001, 0x8000000080008008,
)
_MASK = (1 << 64) - 1
_RATE = 136


def _rotate(value: int, amount: int) -> int:
    if amount == 0:
        return value
    return ((value << amount) | (value >> (64 - amount))) & _MASK


def _permutation(state: list[int]) -> None:
    for constant in _ROUND:
        columns = [
            state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
            for x in range(5)
        ]
        deltas = [columns[(x - 1) % 5] ^ _rotate(columns[(x + 1) % 5], 1) for x in range(5)]
        for y in range(5):
            for x in range(5):
                state[x + 5 * y] ^= deltas[x]
        moved = [0] * 25
        for y in range(5):
            for x in range(5):
                moved[y % 5 + 5 * ((2 * x + 3 * y) % 5)] = _rotate(
                    state[x + 5 * y], _ROTATION[x + 5 * y]
                )
        for y in range(5):
            row = moved[5 * y:5 * y + 5]
            for x in range(5):
                state[x + 5 * y] = row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5])
        state[0] ^= constant


def _sponge(data: bytes, suffix: int) -> bytes:
    """Absorb data under a domain suffix and squeeze 32 bytes.

    pad10*1 appends the suffix and a final 0x80 bit. When one byte of the
    block remains they share it, so that byte is ``suffix | 0x80``.
    """
    padded = bytearray(data)
    remaining = _RATE - len(padded) % _RATE
    if remaining == 1:
        padded.append(suffix | 0x80)
    else:
        padded.append(suffix)
        padded.extend(b"\x00" * (remaining - 2))
        padded.append(0x80)
    state = [0] * 25
    for offset in range(0, len(padded), _RATE):
        block = padded[offset:offset + _RATE]
        for lane in range(_RATE // 8):
            state[lane] ^= int.from_bytes(block[lane * 8:lane * 8 + 8], "little")
        _permutation(state)
    output = b"".join(lane.to_bytes(8, "little") for lane in state[:_RATE // 8])
    return output[:32]


def keccak256(data: bytes) -> bytes:
    """Return legacy Keccak-256, with Ethereum's 0x01 domain suffix."""
    if not isinstance(data, bytes):
        raise TypeError("Keccak input must be bytes")
    return _sponge(data, 0x01)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="regenerate the emitter table")
    subparsers.add_parser("check", help="compare a regenerated table with the committed one")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"emitter_declarations.py: {args.command} is not implemented yet", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
