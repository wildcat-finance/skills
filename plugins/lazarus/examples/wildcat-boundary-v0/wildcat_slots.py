"""Storage-slot derivation for the Wildcat V1 and V2 market contracts.

The slot numbers come from `forge inspect src/market/WildcatMarket.sol:WildcatMarket
storageLayout` run with Foundry 1.7.1 over the pinned public sources named in
`docs/kickoff/1384/evidence/sources.json`: `wildcat-finance/wildcat-protocol`
at `da74452aa7d1a0f024d99efd22cc6d950a8116b7` and `wildcat-finance/v2-protocol`
at `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`. A compiled layout describes the
source, not a deployed account; the probe in this directory checks every derived
word against the deployed getter at the boundary block before a plan uses it.

Nothing here reaches a network or proves anything. Lazarus `verify` proves.
"""

from __future__ import annotations

from Crypto.Hash import keccak  # eth-hash[pycryptodome], pinned by plugins/lazarus

# Fields are (name, byte offset from the low end of the word, byte size).
STATE_WORD_0 = (("isClosed", 0, 1), ("maxTotalSupply", 1, 16))
STATE_WORD_1 = (("accruedProtocolFees", 0, 16), ("normalizedUnclaimedWithdrawals", 16, 16))
STATE_WORD_2 = (
    ("scaledTotalSupply", 0, 13),
    ("scaledPendingWithdrawals", 13, 13),
    ("pendingWithdrawalExpiry", 26, 4),
    ("isDelinquent", 30, 1),
)

LAYOUTS = {
    "v1": {
        "state": (3, 4, 5, 6),
        "accounts": 7,
        "fifo_head": 8,
        "fifo_data": 9,
        "batches": 10,
        "statuses": 11,
        "account_scaled_offset": 1,  # `AuthRole approval` occupies byte 0
        "state_word_3": (
            ("timeDelinquent", 0, 4),
            ("annualInterestBips", 4, 2),
            ("reserveRatioBips", 6, 2),
            ("scaleFactor", 8, 14),
            ("lastInterestAccruedTimestamp", 22, 4),
        ),
    },
    "v2": {
        "state": (0, 1, 2, 3),
        "accounts": 4,
        "fifo_head": 5,
        "fifo_data": 6,
        "batches": 7,
        "statuses": 8,
        "account_scaled_offset": 0,
        "state_word_3": (
            ("timeDelinquent", 0, 4),
            ("protocolFeeBips", 4, 2),
            ("annualInterestBips", 6, 2),
            ("reserveRatioBips", 8, 2),
            ("scaleFactor", 10, 14),
            ("lastInterestAccruedTimestamp", 24, 4),
        ),
    },
}

# Storage words that hold a proxy's implementation pointer, read where present.
POINTER_SLOTS = {
    "eip1967-implementation": "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
    "eip1967-beacon": "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50",
    "zeppelinos-implementation": "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3",
}
SOLADY_BALANCE_SEED = bytes.fromhex("87a211a2")


def kec(data: bytes) -> bytes:
    return keccak.new(digest_bits=256, data=data).digest()


def pad(value: int | str) -> bytes:
    if isinstance(value, str):
        value = int(value, 16)
    return value.to_bytes(32, "big")


def slot_hex(value: bytes | int) -> str:
    if isinstance(value, int):
        value = value.to_bytes(32, "big")
    return "0x" + value.hex()


def mapping_slot(key: int | str, base: int | bytes) -> bytes:
    """Solidity `mapping` word: keccak256(pad32(key) ++ pad32(base))."""
    base_bytes = base if isinstance(base, bytes) else pad(base)
    return kec(pad(key) + base_bytes)


def erc7201_base(namespace: str) -> int:
    """ERC-7201 namespaced root: keccak256(keccak256(id) - 1) & ~0xff."""
    seed = int.from_bytes(kec(namespace.encode()), "big") - 1
    return int.from_bytes(kec(pad(seed)), "big") & ~0xFF


def balance_slot(holder: str, layout: dict) -> bytes:
    """The word that stores `balanceOf(holder)` under a recognised layout."""
    order = layout["order"]
    base = layout["base"]
    if order == "solidity":
        return mapping_slot(holder, base)
    if order == "vyper":
        return kec(pad(base) + pad(holder))
    if order.startswith("erc7201:"):
        return mapping_slot(holder, erc7201_base(order.split(":", 1)[1]) + int(base))
    if order == "solady":
        return kec(bytes.fromhex(holder[2:]) + bytes(8) + SOLADY_BALANCE_SEED)
    raise ValueError(f"unknown balance layout {order!r}")


def market_words(generation: str, members: dict, fifo: dict) -> dict[str, list[str]]:
    """Every storage word behind a mapped number for one market.

    `members` is the market's entry in `docs/kickoff/1384/population.json` and
    `fifo` carries the unpaid-batch queue's `start_index` and `next_index` read
    at the boundary, because the queue's live entries are not in the value map.
    """
    layout = LAYOUTS[generation]
    words = {
        "state": [slot_hex(s) for s in layout["state"]],
        "fifo_head": [slot_hex(layout["fifo_head"])],
        "fifo_data": [
            slot_hex(mapping_slot(index, layout["fifo_data"]))
            for index in range(int(fifo["start_index"]), int(fifo["next_index"]))
        ],
        "accounts": [slot_hex(mapping_slot(a, layout["accounts"])) for a in members["accounts"]],
        "batches": [],
        "statuses": [],
    }
    for expiry in members["batch_expiries"]:
        base = mapping_slot(expiry, layout["batches"])
        words["batches"].append(slot_hex(base))
        words["batches"].append(slot_hex(int.from_bytes(base, "big") + 1))
    for pair in members["account_batches"]:
        inner = mapping_slot(pair["expiry"], layout["statuses"])
        words["statuses"].append(slot_hex(mapping_slot(pair["account"], inner)))
    return words


def unpack(word: int, fields) -> dict[str, int]:
    return {
        name: (word >> (8 * offset)) & ((1 << (8 * size)) - 1)
        for name, offset, size in fields
    }


def decode_state(generation: str, words: list[int]) -> dict[str, int]:
    """Decode the four `_state` words into the `MarketState` fields."""
    layout = LAYOUTS[generation]
    decoded = {}
    decoded.update(unpack(words[0], STATE_WORD_0))
    decoded.update(unpack(words[1], STATE_WORD_1))
    decoded.update(unpack(words[2], STATE_WORD_2))
    decoded.update(unpack(words[3], layout["state_word_3"]))
    return decoded
