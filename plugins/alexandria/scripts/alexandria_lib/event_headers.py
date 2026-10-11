"""Bounded provider-reported headers for the four legacy Wildcat archive families."""

import re
from .errors import AlexandriaError

FIELD = "wildcat_event_headers"
RULE = "selected-event-blocks/v1"
CLASS = "event-block-headers"
MAX_HEADERS = 100_000
QUANTITY = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]*)\Z")
HASH = re.compile(r"0x[0-9a-f]{64}\Z")
TOPICS = frozenset({
    "0xb848ae6b1253b6cb77e81464128ce8bd94d3d524fea54e801e0da869784dca33",
    "0xe8b606ac1e5df7657db58d297ca8f41c090fc94c5fd2d6958f043e41736e9fa6",
    "0x9dc30b8eda31a6a144e092e5de600955523a6a925cc15cc1d1b9b4872cfa6155",
})
DEPLOY = {
    "wildcat-v1": "0xc2a417fb64d0098a8c5f3710eebbd2fc79c00dfd5b87ad224d689fc5b70a6df4",
    "wildcat-v2": "0x6f8c7c94fc16393d1ebec38de9899ba8c6bd860a025aa60063b7cf4c40a16c09",
}


def enabled(plan):
    return FIELD in plan


def validate_marker(plan):
    if not enabled(plan):
        return
    if plan.get(FIELD) != RULE or plan.get("venue") not in DEPLOY or "logs" not in plan.get("evidence_classes", []):
        raise AlexandriaError("wildcat_event_headers requires selected-event-blocks/v1 on a Wildcat log plan")


def quantity(value, label):
    if not isinstance(value, str) or len(value) > 66 or QUANTITY.fullmatch(value) is None:
        raise AlexandriaError(label + " is not a bounded canonical hexadecimal quantity")
    return int(value, 16)


def identities(plan, logs, registry):
    """Derive sorted number/hash pairs only from selected subjects and archive roles."""
    entries = {row["address"]: row for row in registry["entries"]}
    subjects = set(plan.get("subjects", [plan.get("proxy")]))
    pairs = {}
    for log in logs:
        if not isinstance(log, dict):
            raise AlexandriaError("event header source log is not an object")
        address = log.get("address")
        topics = log.get("topics")
        if address not in subjects or not isinstance(topics, list) or not topics:
            continue
        role = entries.get(address, {}).get("role")
        selected = (topics[0] in TOPICS and role == "market") or (
            topics[0] == DEPLOY[plan["venue"]] and role == ("controller" if plan["venue"] == "wildcat-v1" else "factory")
        )
        if not selected:
            continue
        number = quantity(log.get("blockNumber"), "selected event block number")
        block_hash = log.get("blockHash")
        if not isinstance(block_hash, str) or HASH.fullmatch(block_hash) is None:
            raise AlexandriaError("selected event block hash is malformed")
        if not int(plan["interval"]["start"]) <= number <= int(plan["interval"]["end"]):
            raise AlexandriaError("selected event block is outside its interval")
        if number in pairs and pairs[number] != block_hash:
            raise AlexandriaError("selected events disagree about their block hash")
        pairs[number] = block_hash
        if len(pairs) > MAX_HEADERS:
            raise AlexandriaError("selected event header request limit exceeded")
    return sorted(pairs.items())


def accept(header, identity):
    """Check the response's exact event identity and supplied timestamp, including zero."""
    number, block_hash = identity
    if not isinstance(header, dict) or quantity(header.get("number"), "event header number") != number or header.get("hash") != block_hash:
        raise AlexandriaError("event header does not match its selected event number and hash")
    quantity(header.get("timestamp"), "event header timestamp")
