#!/usr/bin/env python3
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).parent
spec = importlib.util.spec_from_file_location("noema_validate", ROOT / "validate.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["noema_validate"] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)


def parse_record(line: str):
    tokens = line.split(" ")
    node, end = mod.parse(tokens)
    if end != len(tokens) or node.kind not in mod.ROOT_KINDS:
        raise mod.Refusal("record did not close")
    return node


def key(node) -> str:
    return " ".join(node.tokens())


def truth(node, facts: dict[str, bool]):
    if node.op == "~":
        value = truth(node.args[0], facts)
        return None if value is None else not value
    if node.op.startswith("&"):
        values = [truth(x, facts) for x in node.args]
        if False in values:
            return False
        return None if None in values else True
    if node.op.startswith("|"):
        values = [truth(x, facts) for x in node.args]
        if True in values:
            return True
        return None if None in values else False
    return facts.get(key(node))


def effects(node, facts: dict[str, bool]):
    if node.op in {"!", "-", "+"}:
        return [(node.op, key(node.args[0]))]
    if node.op == "^":
        return [("^", key(node.args[0]), key(node.args[1]))]
    if node.op == ";2" or node.op.startswith(";"):
        out = []
        for arg in node.args:
            out.extend(effects(arg, facts))
        return out
    if node.op in {"?", "/"}:
        value = truth(node.args[0], facts)
        enabled = value if node.op == "?" else (None if value is None else not value)
        if enabled is None:
            return [("BLOCKED_UNKNOWN", key(node.args[0]))]
        return effects(node.args[1], facts) if enabled else []
    raise AssertionError(node)


for tape in sorted(ROOT.glob("demo-*.nt")):
    mod.validate(tape)
mod.validate(ROOT / "reachable-defs.nt")

for bad in (
    "? receipt.fail Phase - advance",
    "? receipt.fail Phase - advance Phase extra",
    "% receipt.fail Phase - advance Phase",
):
    try:
        parse_record(bad)
    except mod.Refusal:
        pass
    else:
        raise AssertionError(f"accepted malformed record: {bad}")

for line, kind in (
    ("R r1 - effect", "rule"),
    ("O U high low session evidence", "override"),
    ("> t1 machine s0 event guard s1 *1 effect", "transition"),
    ("H h1 producer consumer subject scope *1 evidence *1 checked time transform *1 gap", "handoff"),
    ("X x1 U gate subject scope record expiry recovery", "exception"),
    ("I core deadbeef", "import"),
):
    assert parse_record(line).kind == kind

original = parse_record("? receipt.fail Phase - advance Phase")
flipped = parse_record("? receipt.fail Phase + advance Phase")
assert effects(original, {"receipt.fail Phase": True}) == [("-", "advance Phase")]
assert effects(flipped, {"receipt.fail Phase": True}) == [("+", "advance Phase")]

negated = parse_record("? ~ occurred Run - claim_occurred Run")
dropped = parse_record("? occurred Run - claim_occurred Run")
assert effects(negated, {"occurred Run": False}) == [("-", "claim_occurred Run")]
assert effects(dropped, {"occurred Run": False}) == []
assert effects(negated, {}) == [("BLOCKED_UNKNOWN", "~ occurred Run")]

owner_c = parse_record("^ C branch.name")
owner_u = parse_record("^ U branch.name")
assert effects(owner_c, {}) == [("^", "C", "branch.name")]
assert effects(owner_u, {}) == [("^", "U", "branch.name")]

base = (ROOT / "demo-fiat-hard.nt").read_bytes()
for mutation in (
    base.replace(b"- advance Phase", b"+ advance Phase", 1),
    base.replace(b"^ C branch.name", b"^ U branch.name", 1),
    base.replace(b"- git.bypass_gate\n", b"", 1),
):
    assert sha256(mutation).digest() != sha256(base).digest()

literal_base = (ROOT / "brevitas-answer-literals.txt").read_bytes()
literal_mutation = literal_base.replace(b"counterexample", b"counter-example", 1)
assert sha256(literal_mutation).digest() != sha256(literal_base).digest()

print("OK roundtrip=4 structures=6 malformed=3 semantic=7 digest-mutations=4")
