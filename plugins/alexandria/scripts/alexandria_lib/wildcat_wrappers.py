"""Wildcat V2 wrapper subjects, derived from preserved `WrapperDeployed` logs.

An `alexandria-interval-plan/v2` plan for venue `wildcat-v2` may declare
wrapper instances in `wildcat_v2_wrappers`. `interval.validate_plan` checks
the field's closed shape. This module holds the checks that need the pinned
deployment registry or the preserved logs, and builds the `wrapper-subjects`
component, format `alexandria-wildcat-v2-wrapper-subjects/v1`, that lists the
derived wrapper set. Every function is pure over its arguments: nothing here
reads a chain, opens a file or writes one.

Discovery reads only the logs whose emitter is the registry's one
`wrapper-factory` entry and whose first topic is the `WrapperDeployed` topic,
both compared without regard to case. Each such log must carry exactly three topics, each a lowercase 32-byte word:
the `WrapperDeployed` topic, then the market and the wrapper as zero-padded
addresses, the order the factory source declares them. A log naming a market the
registry does not list, a wrapper equal to a registry entry, or a wrapper
another log also names refuses by name, as does a declared wrapper no log
names. A discovered wrapper the plan does not declare is listed as
undeclared.

Each `WrapperDeployed` log is read on its own. Nothing here infers why a
wrapper was deployed from other logs in the same transaction. Two things stay
unknown: whether every wrapper comes from this one factory, and whether a
wrapper's runtime code can change.
"""

from __future__ import annotations

import re

from .canonical import canonical_bytes
from .errors import AlexandriaError
from .interval import (
    ADDRESS_RE,
    HASH_RE,
    MAX_POSITION_INDEX,
    MAX_SUBJECTS,
    WRAPPERS_FIELD,
    validate_plan,
)
from .wildcat_registry import subject_entries, validate_registry

FORMAT = "alexandria-wildcat-v2-wrapper-subjects/v1"
COMPONENT = "wrapper-subjects"
FACTORY_ROLE = "wrapper-factory"
MARKET_ROLE = "market"
# `WrapperDeployed(address,address)`, `market` indexed first and `wrapper`
# second, as `src/vault/Wildcat4626WrapperFactory.sol` declares it at
# v2-protocol commit c7be4039f8f383a9dda4e45f63331c17d63f9ed9.
WRAPPER_DEPLOYED_TOPIC = "0x317d343bad96f4924450e809267dcfa70e37270e3bb036b5d6d04e3befd47a64"
# The most wrappers one component lists, declared or not; past it the
# derivation refuses rather than writing an unbounded component.
MAX_WRAPPERS = MAX_SUBJECTS
QUANTITY_RE = re.compile(r"0x(?:0|[1-9a-f][0-9a-f]*)\Z")
DECIMAL_RE = re.compile(r"(?:0|[1-9][0-9]{0,18})\Z")
ADDRESS_WORD_RE = re.compile(r"0x0{24}[0-9a-f]{40}\Z")
DOCUMENT_KEYS = frozenset({"factory", "format", "topic", "window", "wrappers"})
ROW_KEYS = frozenset({"declared", "deployment", "market", "wrapper"})
DEPLOYMENT_KEYS = frozenset({"block_number", "log_index", "transaction_hash", "transaction_index"})


def factory(registry) -> str:
    """The address of the registry's one wrapper-factory entry."""
    found = [entry["address"] for entry in registry["entries"] if entry["role"] == FACTORY_ROLE]
    if len(found) != 1:
        raise AlexandriaError("the Wildcat V2 registry does not list exactly one wrapper factory")
    return found[0]


def validate_wrapper_plan(plan, registry) -> list:
    """The plan's declared wrappers, once the plan and the registry admit them.

    The plan passes `validate_plan` and carries the field, and the registry is
    the pinned one. The wrapper factory is a declared subject, because the
    `WrapperDeployed` logs that admit each wrapper are its logs, and no
    declared wrapper is a registry entry of any role.
    """
    validate_plan(plan)
    if WRAPPERS_FIELD not in plan:
        raise AlexandriaError(f"the interval plan declares no {WRAPPERS_FIELD}")
    validate_registry(registry)
    if plan["chain"] != f"eip155:{registry['chain_id']}":
        raise AlexandriaError("the plan's chain is not the chain the wildcat-v2 registry describes")
    address = factory(registry)
    if address not in plan["subjects"]:
        raise AlexandriaError(
            f"interval plan {WRAPPERS_FIELD} requires the wrapper factory {address} as a "
            "declared subject, because its WrapperDeployed logs admit each wrapper"
        )
    entries = subject_entries(registry)
    wrappers = list(plan[WRAPPERS_FIELD]["subjects"])
    for wrapper in wrappers:
        if wrapper in entries:
            entry = entries[wrapper]
            raise AlexandriaError(
                f"declared wrapper {wrapper} is the registry's {entry['role']} entry "
                f"{entry['name']}, not a wrapper instance"
            )
    return wrappers


def _quantity(record, field: str, block, wrapper=None) -> int:
    value = record.get(field)
    if (
        not isinstance(value, str) or QUANTITY_RE.fullmatch(value) is None
        or int(value, 16) > MAX_POSITION_INDEX
    ):
        where = "" if block is None else f" at block {block}"
        whose = "" if wrapper is None else f" for wrapper {wrapper}"
        raise AlexandriaError(
            f"a preserved WrapperDeployed log{where}{whose} carries no canonical {field}"
        )
    return int(value, 16)


def _deployment(record, start: int, end: int) -> tuple:
    """One selected log's market, wrapper and log identity, each field checked."""
    block = _quantity(record, "blockNumber", None)
    if not start <= block <= end:
        raise AlexandriaError(
            f"a preserved WrapperDeployed log at block {block} is outside the interval, "
            f"blocks {start} to {end}"
        )
    topics = record["topics"]
    if len(topics) != 3:
        raise AlexandriaError(
            f"a preserved WrapperDeployed log at block {block} carries {len(topics)} topics, "
            "not the three that name its market and its wrapper"
        )
    if any(not isinstance(topic, str) or HASH_RE.fullmatch(topic) is None for topic in topics):
        raise AlexandriaError(
            f"a preserved WrapperDeployed log at block {block} carries a topic that is not a "
            "lowercase 32-byte word"
        )
    for index, label in ((1, "market"), (2, "wrapper")):
        if ADDRESS_WORD_RE.fullmatch(topics[index]) is None:
            raise AlexandriaError(
                f"a preserved WrapperDeployed log at block {block} does not carry a "
                f"zero-padded {label} address in topic {index + 1}"
            )
    market = "0x" + topics[1][26:]
    wrapper = "0x" + topics[2][26:]
    transaction = record.get("transactionHash")
    if not isinstance(transaction, str) or HASH_RE.fullmatch(transaction) is None:
        raise AlexandriaError(
            f"a preserved WrapperDeployed log at block {block} for wrapper {wrapper} carries "
            "no lowercase 32-byte transaction hash"
        )
    identity = {
        "block_number": str(block),
        "log_index": _quantity(record, "logIndex", block, wrapper),
        "transaction_hash": transaction,
        "transaction_index": _quantity(record, "transactionIndex", block, wrapper),
    }
    return market, wrapper, identity


def discover(plan, registry, logs) -> list:
    """Every wrapper the preserved `WrapperDeployed` logs name, ascending by address.

    Each row is `{"wrapper", "market", "deployment"}`, where `deployment` is
    the log's block, transaction hash, transaction index and log index. Only
    logs the wrapper factory emitted under the `WrapperDeployed` topic are
    read; every other log is passed over unread. The plan and registry are
    checked first by `validate_wrapper_plan`.
    """
    validate_wrapper_plan(plan, registry)
    if not isinstance(logs, (list, tuple)):
        raise AlexandriaError("the preserved logs are not a list")
    start = int(plan["interval"]["start"])
    end = int(plan["interval"]["end"])
    emitter = factory(registry)
    entries = subject_entries(registry)
    markets = {address for address, entry in entries.items() if entry["role"] == MARKET_ROLE}
    found = {}
    for record in logs:
        # A provider-returned JSON-RPC log; `address` is the emitting contract.
        if not isinstance(record, dict):
            raise AlexandriaError("a preserved log record is not an object")
        address = record.get("address")
        topics = record.get("topics")
        if (
            not isinstance(address, str) or address.lower() != emitter
            or not isinstance(topics, list) or not topics
            or not isinstance(topics[0], str) or topics[0].lower() != WRAPPER_DEPLOYED_TOPIC
        ):
            continue
        market, wrapper, identity = _deployment(record, start, end)
        block = identity["block_number"]
        if market not in markets:
            raise AlexandriaError(
                f"a preserved WrapperDeployed log at block {block} names market {market}, which "
                f"is not one of the {len(markets)} markets the registry declares, for wrapper "
                f"{wrapper}"
            )
        if wrapper in entries:
            raise AlexandriaError(
                f"a preserved WrapperDeployed log at block {block} names wrapper {wrapper}, "
                f"which the registry lists as its {entries[wrapper]['role']} entry "
                f"{entries[wrapper]['name']}"
            )
        if wrapper in found:
            raise AlexandriaError(
                f"wrapper {wrapper} is named by two preserved WrapperDeployed logs, at block "
                f"{found[wrapper]['deployment']['block_number']} and block {block}"
            )
        if len(found) == MAX_WRAPPERS:
            raise AlexandriaError(
                f"the wrapper factory {emitter} deployed more than {MAX_WRAPPERS} wrappers "
                f"inside the interval, blocks {start} to {end}; declare a shorter interval"
            )
        found[wrapper] = {"deployment": identity, "market": market, "wrapper": wrapper}
    return [found[wrapper] for wrapper in sorted(found)]


def wrapper_subjects(plan, registry, logs) -> dict:
    """The `wrapper-subjects` component the plan, registry and preserved logs derive.

    It names the factory, the `WrapperDeployed` topic, the discovery window
    (the plan's interval) and every discovered wrapper with its market,
    deployment log identity and whether the plan declared it. A declared
    wrapper that no preserved `WrapperDeployed` log names refuses by name.
    """
    rows = discover(plan, registry, logs)
    named = {row["wrapper"] for row in rows}
    declared = plan[WRAPPERS_FIELD]["subjects"]
    for wrapper in declared:
        if wrapper not in named:
            raise AlexandriaError(
                f"declared wrapper {wrapper} is named by no preserved WrapperDeployed log from "
                f"the wrapper factory {factory(registry)} inside the interval, blocks "
                f"{plan['interval']['start']} to {plan['interval']['end']}"
            )
    wanted = set(declared)
    document = {
        "factory": factory(registry),
        "format": FORMAT,
        "topic": WRAPPER_DEPLOYED_TOPIC,
        "window": {"end": plan["interval"]["end"], "start": plan["interval"]["start"]},
        "wrappers": [dict(row, declared=row["wrapper"] in wanted) for row in rows],
    }
    validate_component(document)
    return document


def _integer(value, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_POSITION_INDEX:
        raise AlexandriaError(f"wrapper-subjects {label} is not a bounded non-negative integer")


def validate_component(document) -> None:
    """Check one `wrapper-subjects` document's closed shape; it re-derives nothing."""
    if not isinstance(document, dict) or set(document) != DOCUMENT_KEYS:
        raise AlexandriaError("the wrapper-subjects component has an unknown shape")
    if document["format"] != FORMAT:
        raise AlexandriaError("the wrapper-subjects component format is not recognised")
    if not isinstance(document["factory"], str) or ADDRESS_RE.fullmatch(document["factory"]) is None:
        raise AlexandriaError("the wrapper-subjects factory is not a lowercase address")
    if document["topic"] != WRAPPER_DEPLOYED_TOPIC:
        raise AlexandriaError("the wrapper-subjects topic is not the WrapperDeployed topic")
    window = document["window"]
    if (
        not isinstance(window, dict) or set(window) != {"end", "start"}
        or any(not isinstance(window[key], str) or DECIMAL_RE.fullmatch(window[key]) is None
               for key in ("end", "start"))
        or int(window["start"]) > int(window["end"])
    ):
        raise AlexandriaError("the wrapper-subjects window is not an ordered block range")
    rows = document["wrappers"]
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_WRAPPERS:
        raise AlexandriaError(
            f"the wrapper-subjects component must list from 1 to {MAX_WRAPPERS} wrappers"
        )
    previous = None
    for row in rows:
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            raise AlexandriaError("a wrapper-subjects row has an unknown shape")
        for key in ("market", "wrapper"):
            if not isinstance(row[key], str) or ADDRESS_RE.fullmatch(row[key]) is None:
                raise AlexandriaError(f"a wrapper-subjects row {key} is not a lowercase address")
        if previous is not None and row["wrapper"] <= previous:
            raise AlexandriaError(
                f"wrapper-subjects row {row['wrapper']} is duplicated or out of ascending order"
            )
        previous = row["wrapper"]
        if not isinstance(row["declared"], bool):
            raise AlexandriaError(f"wrapper-subjects row {row['wrapper']} declared is not a boolean")
        deployment = row["deployment"]
        if not isinstance(deployment, dict) or set(deployment) != DEPLOYMENT_KEYS:
            raise AlexandriaError(f"wrapper-subjects row {row['wrapper']} deployment has an unknown shape")
        block = deployment["block_number"]
        if (
            not isinstance(block, str) or DECIMAL_RE.fullmatch(block) is None
            or not int(window["start"]) <= int(block) <= int(window["end"])
        ):
            raise AlexandriaError(
                f"wrapper-subjects row {row['wrapper']} deployment block is outside its window"
            )
        if not isinstance(deployment["transaction_hash"], str) or HASH_RE.fullmatch(
            deployment["transaction_hash"]
        ) is None:
            raise AlexandriaError(
                f"wrapper-subjects row {row['wrapper']} transaction hash is not a 32-byte hash"
            )
        for key in ("log_index", "transaction_index"):
            _integer(deployment[key], f"row {row['wrapper']} {key}")


def component_bytes(document) -> bytes:
    """The component's canonical bytes, after its closed shape is checked."""
    validate_component(document)
    return canonical_bytes(document)
