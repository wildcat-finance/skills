"""Aave v4 Tabularium mapping for spoke borrow and repayment logs."""

from __future__ import annotations

import re

from ..errors import AlexandriaError
from ..rows import event_row, provenance
from .common import (
    coverage_declaration,
    enforce_subject_scope,
    integer,
    list_value,
    load_source,
    object_value,
    require_coverage,
    required,
    string,
)


ADAPTER = "aave-v4"
ADAPTER_VERSION = "1.0.0"
MAPPING_REVISION = "aave-v4.credit.v1"
CHAIN = "eip155:1"
BORROW_TOPIC = "0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"
REPAY_TOPIC = "0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd"
MAPPINGS = {
    BORROW_TOPIC: ("borrowing", "aave-v4.borrow", "aave-v4.borrow.v1"),
    REPAY_TOPIC: ("repayment", "aave-v4.repay", "aave-v4.repay.v1"),
}
RULES = ("aave-v4.borrow.v1", "aave-v4.repay.v1")
# A borrow states two data words and a repay five. Only the first two are
# established in the preserved capture, so this mapping reads no further.
DATA_WORDS = {BORROW_TOPIC: 2, REPAY_TOPIC: 5}
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
HASH = re.compile(r"^0x[0-9a-f]{64}$")
EXPECTED_KEYS = {"_meta", "logs", "reserve_reads", "token_reads"}


def _address(value, where):
    if not isinstance(value, str) or not ADDRESS.fullmatch(value):
        raise AlexandriaError(f"{where} is not a lowercase EVM address")
    return value


def _hash(value, where):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise AlexandriaError(f"{where} is not a lowercase 32-byte hash")
    return value


def _quantity(value, where):
    if not isinstance(value, str) or not value.startswith("0x") or len(value) < 3:
        raise AlexandriaError(f"{where} is not a hex quantity")
    try:
        return int(value, 16)
    except ValueError as error:
        raise AlexandriaError(f"{where} is not a hex quantity") from error


def _topic_address(topic, where):
    if not isinstance(topic, str) or len(topic) != 66 or topic[2:26] != "0" * 24:
        raise AlexandriaError(f"{where} is not a left-padded address topic")
    return "0x" + topic[26:].lower()


def _word(data, index, where):
    body = data[2:]
    chunk = body[index * 64 : (index + 1) * 64]
    if len(chunk) != 64:
        raise AlexandriaError(f"{where} has no data word {index}")
    try:
        return int(chunk, 16)
    except ValueError as error:
        raise AlexandriaError(f"{where} data word {index} is not hexadecimal") from error


def _reserves(source):
    """Index the preserved reads that name each reserve's underlying token."""

    index = {}
    for position, record in enumerate(
        list_value(source["reserve_reads"], "Aave v4 reserve_reads")
    ):
        where = f"Aave v4 reserve_reads[{position}]"
        record = object_value(record, where)
        spoke = _address(string(record, "spoke", where), f"{where}.spoke")
        asset_id = integer(record, "asset_id", where)
        underlying = _address(string(record, "underlying", where), f"{where}.underlying")
        result = string(record, "result", where)
        # The recorded call result is the authority; a convenience field that
        # disagrees with the bytes it came from is refused.
        if _topic_address("0x" + result[2:66], f"{where}.result") != underlying:
            raise AlexandriaError(f"{where} underlying disagrees with its recorded result")
        if (spoke, asset_id) in index:
            raise AlexandriaError(f"{where} repeats a spoke and asset pair")
        index[(spoke, asset_id)] = underlying
    return index


def _tokens(source):
    index = {}
    for position, record in enumerate(
        list_value(source["token_reads"], "Aave v4 token_reads")
    ):
        where = f"Aave v4 token_reads[{position}]"
        record = object_value(record, where)
        token = _address(string(record, "token", where), f"{where}.token")
        decimals = integer(record, "decimals", where)
        symbol = string(record, "symbol", where)
        if int(string(record, "decimals_result", where), 16) != decimals:
            raise AlexandriaError(f"{where} decimals disagree with its recorded result")
        if token in index:
            raise AlexandriaError(f"{where} repeats a token")
        index[token] = (symbol, decimals)
    return index


def map_capture(capture, data, source_release_id):
    if (
        capture["chain"] != CHAIN
        or capture["evidence_class"] != "archive-log"
        or capture["source"]["kind"] != "ethereum-logs"
        or capture["scope"]["interval"]["kind"] != "block-range"
    ):
        raise AlexandriaError(
            "Aave v4 mapping requires an eip155:1 archive-log block range"
        )
    interval_start = int(capture["scope"]["interval"]["start"])
    interval_end = int(capture["scope"]["interval"]["end"])
    source = object_value(load_source(data, capture), "Aave v4 source")
    if set(source) != EXPECTED_KEYS:
        raise AlexandriaError("Aave v4 source collections do not match the registered mapping")

    logs = list_value(source["logs"], "Aave v4 logs")
    reserves = _reserves(source)
    tokens = _tokens(source)
    require_coverage(capture, {"/logs": len(logs),
                               "/reserve_reads": len(reserves),
                               "/token_reads": len(tokens)})

    meta = object_value(source["_meta"], "Aave v4 _meta")
    window = object_value(required(meta, "window", "Aave v4 _meta"), "Aave v4 _meta.window")
    if (
        integer(window, "first_block", "Aave v4 _meta.window") != interval_start
        or integer(window, "last_block", "Aave v4 _meta.window") != interval_end
    ):
        raise AlexandriaError("Aave v4 source window does not match its capture interval")

    events = []
    identities = set()
    for position, raw in enumerate(logs):
        where = f"Aave v4 logs[{position}]"
        raw = object_value(raw, where)
        if raw.get("removed") is not False:
            raise AlexandriaError(f"{where} is not a settled log")
        topics = list_value(required(raw, "topics", where), f"{where}.topics")
        if len(topics) != 4:
            raise AlexandriaError(f"{where} does not carry four topics")
        topic = topics[0]
        if topic not in MAPPINGS:
            raise AlexandriaError(f"{where} is not an Aave v4 credit topic")
        family, action, rule = MAPPINGS[topic]

        spoke = _address(string(raw, "address", where), f"{where}.address")
        asset_id = _quantity(topics[1], f"{where}.topics[1]")
        user = _topic_address(topics[2], f"{where}.topics[2]")
        block_number = _quantity(string(raw, "blockNumber", where), f"{where}.blockNumber")
        if not interval_start <= block_number <= interval_end:
            raise AlexandriaError(f"{where} block is outside the capture interval")
        block_hash = _hash(string(raw, "blockHash", where), f"{where}.blockHash")
        tx_hash = _hash(string(raw, "transactionHash", where), f"{where}.transactionHash")
        log_index = _quantity(string(raw, "logIndex", where), f"{where}.logIndex")
        timestamp = _quantity(string(raw, "blockTimestamp", where), f"{where}.blockTimestamp")

        data_field = string(raw, "data", where)
        if (len(data_field) - 2) // 64 != DATA_WORDS[topic]:
            raise AlexandriaError(f"{where} data word count does not match its topic")
        amount = _word(data_field, 1, where)

        underlying = reserves.get((spoke, asset_id))
        if underlying is None:
            raise AlexandriaError(f"{where} names a reserve this capture never read")
        if underlying not in tokens:
            raise AlexandriaError(f"{where} underlying has no recorded token metadata")
        symbol, decimals = tokens[underlying]

        source_identity = f"{tx_hash}:{log_index}"
        if source_identity in identities:
            raise AlexandriaError(f"{where} repeats the source identity {source_identity}")
        identities.add(source_identity)
        prov = provenance(
            source_release_id=source_release_id,
            component=capture["component"],
            component_sha256=capture["component_sha256"],
            capture_id=capture["id"],
            source_selector=f"/logs/{position}",
            source_identity=source_identity,
            mapping_rule=rule,
            adapter=ADAPTER,
            adapter_version=ADAPTER_VERSION,
            evidence_class=capture["evidence_class"],
            context_selectors=("/reserve_reads", "/token_reads"),
        )
        events.append(event_row(
            identity=f"{CHAIN}:{source_identity}",
            chain=CHAIN,
            venue=ADAPTER,
            subject=f"{CHAIN}:{user}",
            deployment=capture["scope"]["deployment"],
            facility={"kind": "aave-v4-spoke", "id": spoke},
            event_family=family,
            action=action,
            amounts=[{
                "asset": {
                    "address": underlying,
                    "chain": CHAIN,
                    "decimals": decimals,
                    "symbol": symbol,
                },
                "base_units": str(amount),
                "role": "source-amount",
            }],
            transaction={
                "block_number": str(block_number),
                "block_hash": block_hash,
                "hash": tx_hash,
                "log_index": str(log_index),
                "timestamp": str(timestamp),
            },
            provenance=prov,
        ))

    enforce_subject_scope(capture, events)
    declaration = {
        "adapter": ADAPTER,
        "adapter_version": ADAPTER_VERSION,
        "capture_id": capture["id"],
        "coverage": coverage_declaration(
            capture,
            mapped={"logs": len(events)},
            context={"reserve-reads": len(reserves), "token-reads": len(tokens)},
            unsupported={},
        ),
        "mapping_revision": MAPPING_REVISION,
        "rules": list(RULES),
    }
    return events, [], declaration
