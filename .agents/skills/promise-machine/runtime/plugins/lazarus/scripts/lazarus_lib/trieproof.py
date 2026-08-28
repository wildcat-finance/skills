"""Offline Merkle Patricia inclusion and absence proof traversal."""

from __future__ import annotations

from eth_hash.auto import keccak

from .errors import FormatError, IntegrityError, ResourceLimitError
from .rlp import RLP, decode, encode


EMPTY_TRIE_ROOT = keccak(b"\x80")
MAX_PROOF_NODES = 2048
MAX_NODE_BYTES = 1024 * 1024
MAX_TRIE_ITEMS = 100_000
MAX_TRIE_KEY_BYTES = 64
MAX_TRIE_VALUE_BYTES = 16 * 1024 * 1024
MAX_TRIE_INPUT_BYTES = 16 * 1024 * 1024


def bytes_to_nibbles(value: bytes) -> list[int]:
    result: list[int] = []
    for byte in value:
        result.extend((byte >> 4, byte & 0x0F))
    return result


def compact_path(value: bytes) -> tuple[list[int], bool]:
    nibbles = bytes_to_nibbles(value)
    if not nibbles:
        raise FormatError("compact trie path is empty")
    flag = nibbles[0]
    if flag > 3:
        raise FormatError("compact trie path has invalid flags")
    leaf = bool(flag & 2)
    odd = bool(flag & 1)
    if odd:
        path = nibbles[1:]
    else:
        if len(nibbles) < 2 or nibbles[1] != 0:
            raise FormatError("compact trie path has non-zero even padding")
        path = nibbles[2:]
    if not leaf and not path:
        raise FormatError("extension trie path is empty")
    return path, leaf


def trie_root(items: list[tuple[bytes, bytes]]) -> bytes:
    """Build the canonical hexary trie root for bounded unique byte keys.

    Production verification constructs the trie locally rather than trusting a
    dependency's database or node encoding. Tests compare this builder with the
    already pinned ``trie`` package as an independent implementation.
    """

    if not isinstance(items, list):
        raise FormatError("trie items must be a list")
    if len(items) > MAX_TRIE_ITEMS:
        raise ResourceLimitError(f"trie item count exceeds {MAX_TRIE_ITEMS}")
    entries: list[tuple[tuple[int, ...], bytes]] = []
    seen: set[bytes] = set()
    total = 0
    for key, value in items:
        if not isinstance(key, bytes) or not isinstance(value, bytes):
            raise FormatError("trie keys and values must be bytes")
        if not value:
            raise FormatError("trie values must not be empty")
        if len(key) > MAX_TRIE_KEY_BYTES:
            raise ResourceLimitError(
                f"trie key exceeds {MAX_TRIE_KEY_BYTES} bytes"
            )
        if len(value) > MAX_TRIE_VALUE_BYTES:
            raise ResourceLimitError(
                f"trie value exceeds {MAX_TRIE_VALUE_BYTES} bytes"
            )
        total += len(key) + len(value)
        if total > MAX_TRIE_INPUT_BYTES:
            raise ResourceLimitError(
                f"trie input exceeds {MAX_TRIE_INPUT_BYTES} bytes"
            )
        if key in seen:
            raise FormatError("trie contains duplicate keys")
        seen.add(key)
        entries.append((tuple(bytes_to_nibbles(key)), value))
    if not entries:
        return EMPTY_TRIE_ROOT
    entries.sort(key=lambda item: item[0])
    return keccak(encode(_build_node(entries)))


def _build_node(entries: list[tuple[tuple[int, ...], bytes]]) -> list[RLP]:
    if len(entries) == 1:
        key, value = entries[0]
        return [_encode_compact(key, leaf=True), value]

    prefix_length = _common_prefix(entries)
    if prefix_length:
        child_entries = [
            (key[prefix_length:], value) for key, value in entries
        ]
        return [
            _encode_compact(entries[0][0][:prefix_length], leaf=False),
            _node_reference(_build_node(child_entries)),
        ]

    branch: list[RLP] = [b""] * 17
    groups: list[list[tuple[tuple[int, ...], bytes]]] = [[] for _ in range(16)]
    for key, value in entries:
        if not key:
            if branch[16] != b"":
                raise FormatError("trie contains duplicate branch values")
            branch[16] = value
        else:
            groups[key[0]].append((key[1:], value))
    for nibble, group in enumerate(groups):
        if group:
            branch[nibble] = _node_reference(_build_node(group))
    return branch


def _common_prefix(entries: list[tuple[tuple[int, ...], bytes]]) -> int:
    shortest = min(len(key) for key, _ in entries)
    first = entries[0][0]
    length = 0
    while length < shortest and all(key[length] == first[length] for key, _ in entries):
        length += 1
    return length


def _encode_compact(path: tuple[int, ...], *, leaf: bool) -> bytes:
    if any(not isinstance(nibble, int) or not 0 <= nibble <= 15 for nibble in path):
        raise FormatError("trie path contains an invalid nibble")
    flag = 2 if leaf else 0
    if len(path) % 2:
        packed = (flag + 1, *path)
    else:
        packed = (flag, 0, *path)
    return bytes(
        (packed[index] << 4) | packed[index + 1]
        for index in range(0, len(packed), 2)
    )


def _node_reference(node: list[RLP]) -> RLP:
    raw = encode(node)
    return node if len(raw) < 32 else keccak(raw)


def verify_proof(root_hash: bytes, key: bytes, proof: list[bytes]) -> bytes | None:
    """Return the trie value or ``None`` for a proved absence.

    A hashed child consumes the next proof item. An embedded child is traversed
    directly from its parent; proof producers may include or omit its repeated
    encoding, and both forms remain bound by the parent bytes.
    """

    if len(root_hash) != 32:
        raise FormatError("trie root must be 32 bytes")
    if len(proof) > MAX_PROOF_NODES:
        raise ResourceLimitError(f"trie proof exceeds {MAX_PROOF_NODES} nodes")
    if len(set(proof)) != len(proof):
        raise FormatError("trie proof contains duplicate nodes")
    if any(len(node) > MAX_NODE_BYTES for node in proof):
        raise ResourceLimitError(f"trie proof node exceeds {MAX_NODE_BYTES} bytes")
    if not proof:
        if root_hash == EMPTY_TRIE_ROOT:
            return None
        raise IntegrityError("trie proof is missing its root node")
    raw = proof[0]
    if keccak(raw) != root_hash:
        raise IntegrityError("trie proof root does not match the expected root")
    node = _node(raw)
    index = 1
    remaining = bytes_to_nibbles(key)
    while True:
        if len(node) == 17:
            if not remaining:
                value = _bytes(node[16], "branch value")
                _no_extra(index, proof)
                return value if value else None
            child = node[remaining[0]]
            remaining = remaining[1:]
            next_node, index = _child(child, proof, index)
            if next_node is None:
                _no_extra(index, proof)
                return None
            node = next_node
            continue
        if len(node) == 2:
            encoded_path = _bytes(node[0], "leaf or extension path")
            path, leaf = compact_path(encoded_path)
            if remaining[: len(path)] != path:
                _no_extra(index, proof)
                return None
            remaining = remaining[len(path) :]
            if leaf:
                _no_extra(index, proof)
                if remaining:
                    return None
                return _bytes(node[1], "leaf value")
            next_node, index = _child(node[1], proof, index)
            if next_node is None:
                raise FormatError("extension node has an empty child")
            node = next_node
            continue
        raise FormatError(f"trie node has {len(node)} items; expected 2 or 17")


def _node(raw: bytes) -> list[RLP]:
    decoded = decode(raw)
    if not isinstance(decoded, list):
        raise FormatError("trie node must be an RLP list")
    return decoded


def _child(
    child: RLP,
    proof: list[bytes],
    index: int,
) -> tuple[list[RLP] | None, int]:
    if isinstance(child, list):
        raw = encode(child)
        if len(raw) >= 32:
            raise FormatError("embedded trie child is 32 bytes or longer")
        if index < len(proof) and proof[index] == raw:
            index += 1
        return child, index
    if not isinstance(child, bytes):
        raise FormatError("trie child is neither bytes nor a node")
    if not child:
        return None, index
    if len(child) != 32:
        raise FormatError("hashed trie child reference must be 32 bytes")
    if index >= len(proof):
        raise IntegrityError("trie proof is missing a referenced node")
    raw = proof[index]
    if keccak(raw) != child:
        raise IntegrityError("trie proof node does not match its parent reference")
    return _node(raw), index + 1


def _bytes(value: RLP, label: str) -> bytes:
    if not isinstance(value, bytes):
        raise FormatError(f"{label} must be an RLP byte string")
    return value


def _no_extra(index: int, proof: list[bytes]) -> None:
    if index != len(proof):
        raise FormatError("trie proof contains unreferenced trailing nodes")
