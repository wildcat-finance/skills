"""Small Ethereum Keccak-256 implementation for storage-slot derivation."""

from .core import TabulariumError


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


def _rotate(value, amount):
    if amount == 0:
        return value
    return ((value << amount) | (value >> (64 - amount))) & _MASK


def _permutation(state):
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


def keccak256(data):
    """Return legacy Keccak-256, with Ethereum's 0x01 domain suffix."""
    if not isinstance(data, bytes):
        raise TabulariumError("Keccak input must be bytes")
    rate = 136
    padded = bytearray(data)
    padded.append(0x01)
    padded.extend(b"\x00" * ((rate - len(padded) % rate - 1) % rate))
    padded.append(0x80)
    state = [0] * 25
    for offset in range(0, len(padded), rate):
        block = padded[offset:offset + rate]
        for lane in range(rate // 8):
            state[lane] ^= int.from_bytes(block[lane * 8:lane * 8 + 8], "little")
        _permutation(state)
    output = b"".join(lane.to_bytes(8, "little") for lane in state[:rate // 8])
    return output[:32]


def mapping_slot(address, slot):
    if not isinstance(address, str) or not address.startswith("0x") or len(address) != 42:
        raise TabulariumError("mapping account must be a 20-byte hexadecimal address")
    try:
        account = bytes.fromhex(address[2:])
    except ValueError as error:
        raise TabulariumError("mapping account is not hexadecimal") from error
    if not isinstance(slot, int) or not 0 <= slot < 1 << 256:
        raise TabulariumError("mapping slot is outside uint256")
    return "0x" + keccak256(account.rjust(32, b"\x00") + slot.to_bytes(32, "big")).hex()
