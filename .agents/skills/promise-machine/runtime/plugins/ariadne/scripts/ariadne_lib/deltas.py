"""Comparisons between two releases, each side named.

Three kinds, because three things break differently. An ABI entry disappearing
breaks a caller at compile time. A method identifier changing breaks one at
run time, silently, which is worse. A storage slot moving breaks an upgrade,
and breaks it after the transaction has gone through.

Every function here returns both sides of what changed. A delta that says
`transfer` changed, without saying from what to what, is a diff nobody can act
on, and gate 5 refuses one whose baselines cannot be identified at all.
"""

from . import digests

ENTRY_KINDS = ("function", "event", "error", "constructor", "fallback", "receive")


def abi_signature(entry):
    """A stable name for an ABI entry: `transfer(address,uint256)`.

    Types are read from the entry rather than computed, so a tuple stays
    `(uint256,address)` as solc wrote it.
    """
    if not isinstance(entry, dict):
        return None
    kind = entry.get("type", "function")
    if kind in ("fallback", "receive"):
        return kind
    name = entry.get("name") or kind
    inputs = entry.get("inputs") or []
    types = []
    for argument in inputs:
        if not isinstance(argument, dict):
            return None
        types.append(argument_type(argument))
    return "%s(%s)" % (name, ",".join(types))


def argument_type(argument):
    """The canonical type of one ABI input, expanding tuples."""
    found = argument.get("type", "")
    if found.startswith("tuple"):
        parts = [argument_type(child) for child in argument.get("components") or []]
        return "(%s)%s" % (",".join(parts), found[len("tuple") :])
    return found


def abi_delta(baseline, current):
    """What changed between two ABIs, by signature.

    `changed` carries both sides, because an entry whose mutability or outputs
    moved is a different promise even though its signature is the same.
    """
    old = {}
    new = {}
    for source, into in ((baseline or [], old), (current or [], new)):
        for entry in source:
            signature = abi_signature(entry)
            if signature is not None:
                into[signature] = entry

    changed = []
    for signature in sorted(set(old) & set(new)):
        if old[signature] != new[signature]:
            changed.append(
                {
                    "signature": signature,
                    "baseline": old[signature],
                    "current": new[signature],
                }
            )
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "changed": changed,
    }


def method_identifier_delta(baseline, current):
    """What changed between two `methodIdentifiers` maps.

    solc keys these by signature and values them by four-byte selector, so a
    selector that moved under an unchanged signature is the interesting case:
    every existing caller now calls something else.
    """
    old = dict(baseline or {})
    new = dict(current or {})
    moved = []
    for signature in sorted(set(old) & set(new)):
        if old[signature] != new[signature]:
            moved.append(
                {
                    "signature": signature,
                    "baseline": old[signature],
                    "current": new[signature],
                }
            )
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "moved": moved,
    }


def storage_key(entry):
    if not isinstance(entry, dict):
        return None
    label = entry.get("label")
    contract = entry.get("contract")
    if label is None:
        return None
    return "%s:%s" % (contract, label) if contract else label


def storage_delta(baseline, current):
    """What moved in a storage layout, from solc's `storage` array.

    Compared by variable rather than by slot: a variable that kept its slot and
    changed type is as dangerous as one that moved, and comparing by slot would
    have reported neither.
    """
    old = {}
    new = {}
    for source, into in ((baseline or [], old), (current or [], new)):
        for entry in source:
            key = storage_key(entry)
            if key is not None:
                into[key] = entry

    moved = []
    retyped = []
    for key in sorted(set(old) & set(new)):
        before, after = old[key], new[key]
        position = (
            str(before.get("slot")),
            str(before.get("offset")),
            str(after.get("slot")),
            str(after.get("offset")),
        )
        if position[:2] != position[2:]:
            moved.append(
                {
                    "variable": key,
                    "baseline": {"slot": before.get("slot"), "offset": before.get("offset")},
                    "current": {"slot": after.get("slot"), "offset": after.get("offset")},
                }
            )
        if before.get("type") != after.get("type"):
            retyped.append(
                {
                    "variable": key,
                    "baseline": before.get("type"),
                    "current": after.get("type"),
                }
            )
    return {
        "added": sorted(set(new) - set(old)),
        "removed": sorted(set(old) - set(new)),
        "moved": moved,
        "retyped": retyped,
    }


def empty(delta):
    """True when a delta records no change at all."""
    if not isinstance(delta, dict):
        return True
    return not any(delta.get(key) for key in delta)


def side(name, digest):
    """One end of a comparison, identified the only way gate 5 accepts."""
    return {"name": name, "digest": digests.check(digest)}
