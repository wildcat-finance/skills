"""Map preserved Aave v4 consensus logs to canonical event schema v2."""

from collections import Counter
from copy import deepcopy

from ..core import TabulariumError
from .euler_common import (
    MappingResult,
    address,
    hash_,
    integer,
    list_,
    object_,
    required,
    text,
)


ADAPTER = "aave-v4"
ADAPTER_VERSION = "2.0.0"
PROTOCOL_GENERATION = "aave-v4"
SOURCE_API = "ethereum-json-rpc"
CHAIN = "ethereum-mainnet"
CHAIN_ID = 1

BORROW_TOPIC = "0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"
REPAY_TOPIC = "0xd765a0263e8a360da8dd4fdb8c0dc5553adec12a96f29a462cdb45e5bea407dd"
MAPPINGS = {
    BORROW_TOPIC: ("borrowing", "aave-v4.borrow", "aave-v4.borrow.v2"),
    REPAY_TOPIC: ("repayment", "aave-v4.repay", "aave-v4.repay.v2"),
}
# Every log of both kinds carries four topics. A borrow states two data words
# and a repay five, of which only the first two are established: the last
# three were zero in every preserved log, so this adapter never names them and
# the raw log is retained instead.
TOPIC_COUNT = 4
DATA_WORDS = {BORROW_TOPIC: 2, REPAY_TOPIC: 5}
ASSET_KIND = {BORROW_TOPIC: "assets_drawn", REPAY_TOPIC: "assets_repaid"}
EXPECTED_TOP_LEVEL = frozenset(("_meta", "logs", "reserve_reads", "token_reads"))


def _word(data, index, where):
    body = data[2:]
    start = index * 64
    chunk = body[start : start + 64]
    if len(chunk) != 64:
        raise TabulariumError("%s data has no word %d" % (where, index))
    try:
        return int(chunk, 16)
    except ValueError as error:
        raise TabulariumError("%s data word %d is not hexadecimal" % (where, index)) from error


def _topic_address(topic, where):
    if not isinstance(topic, str) or len(topic) != 66 or not topic.startswith("0x"):
        raise TabulariumError("%s is not a 32-byte topic" % where)
    if topic[2:26] != "0" * 24:
        raise TabulariumError("%s is not a left-padded address" % where)
    return "0x" + topic[26:].lower()


def _reserve_index(source):
    """Map (spoke, assetId) to the underlying and hub the chain reported."""

    index = {}
    for position, record in enumerate(
        list_(source["reserve_reads"], "Aave v4 source.reserve_reads")
    ):
        where = "reserve_reads[%d]" % position
        record = object_(record, where)
        spoke = address(record, "spoke", where)
        asset_id = integer(record, "asset_id", where)
        underlying = address(record, "underlying", where)
        hub = address(record, "hub", where)
        result = text(record, "result", where)
        # The recorded call result is the authority; the convenience fields
        # must agree with the bytes it returned.
        if _topic_address("0x" + result[2:66], "%s.result word 0" % where) != underlying:
            raise TabulariumError("%s underlying disagrees with its recorded result" % where)
        if _topic_address("0x" + result[66:130], "%s.result word 1" % where) != hub:
            raise TabulariumError("%s hub disagrees with its recorded result" % where)
        if (spoke, asset_id) in index:
            raise TabulariumError("%s repeats a spoke and asset pair" % where)
        index[(spoke, asset_id)] = (underlying, hub)
    return index


def _token_index(source):
    index = {}
    for position, record in enumerate(
        list_(source["token_reads"], "Aave v4 source.token_reads")
    ):
        where = "token_reads[%d]" % position
        record = object_(record, where)
        token = address(record, "token", where)
        decimals = integer(record, "decimals", where, maximum=255)
        symbol = text(record, "symbol", where)
        declared = int(text(record, "decimals_result", where), 16)
        if declared != decimals:
            raise TabulariumError("%s decimals disagree with its recorded result" % where)
        if token in index:
            raise TabulariumError("%s repeats a token" % where)
        index[token] = (symbol, decimals)
    return index


def _event(raw, position, window, reserves, tokens):
    where = "logs[%d]" % position
    raw = object_(raw, where)
    if raw.get("removed") is not False:
        raise TabulariumError("%s is not a settled log" % where)
    topics = list_(required(raw, "topics", where), "%s.topics" % where)
    if len(topics) != TOPIC_COUNT:
        raise TabulariumError("%s does not carry four topics" % where)
    topic = text({"t": topics[0]}, "t", where)
    if topic not in MAPPINGS:
        raise TabulariumError("%s is not an Aave v4 credit topic" % where)

    spoke = address(raw, "address", where)
    asset_id = int(topics[1], 16)
    user = _topic_address(topics[2], "%s.topics[2]" % where)
    caller = _topic_address(topics[3], "%s.topics[3]" % where)
    block_number = int(text(raw, "blockNumber", where), 16)
    if not window[0] <= block_number <= window[1]:
        raise TabulariumError("%s block is outside the captured window" % where)
    block_hash = hash_(raw, "blockHash", where)
    transaction_hash = hash_(raw, "transactionHash", where)
    transaction_index = int(text(raw, "transactionIndex", where), 16)
    log_index = int(text(raw, "logIndex", where), 16)
    timestamp = str(int(text(raw, "blockTimestamp", where), 16))

    data = text(raw, "data", where)
    if (len(data) - 2) // 64 != DATA_WORDS[topic]:
        raise TabulariumError("%s data word count does not match its topic" % where)
    shares = _word(data, 0, where)
    assets = _word(data, 1, where)

    key = (spoke, asset_id)
    if key not in reserves:
        raise TabulariumError("%s names a reserve this capture never read" % where)
    underlying, hub = reserves[key]
    if underlying not in tokens:
        raise TabulariumError("%s underlying has no recorded token metadata" % where)

    family, action, rule = MAPPINGS[topic]
    parties = [{"role": "borrower", "address": user}]
    if caller != user:
        parties.append({"role": "caller", "address": caller})
    return {
        "schema_version": 2,
        "id": "tabularium:%s:%s:%s:%d:%s"
        % (CHAIN, ADAPTER, transaction_hash, log_index, rule),
        "event_family": family,
        "action": action,
        "venue": ADAPTER,
        "chain": CHAIN,
        "transaction": {
            "hash": transaction_hash,
            "block_number": block_number,
            "block_hash": block_hash,
            "transaction_index": transaction_index,
            "log_index": log_index,
            "timestamp": timestamp,
        },
        "parties": parties,
        "instrument": {"type": "aave-v4-spoke", "id": spoke},
        "amounts": [
            {"kind": ASSET_KIND[topic], "base_units": str(assets), "asset": underlying},
            {"kind": "shares", "base_units": str(shares), "asset": None},
        ],
        "provenance": {
            "source_kind": "consensus-log",
            "source_contract": spoke,
            "source_entity": "logs",
            "source_id": "%s:%d" % (transaction_hash, log_index),
            "source_selector": "eth_getLogs[transactionHash=%s,logIndex=%d]"
            % (transaction_hash, log_index),
            "supporting_selectors": [
                "eth_call[to=%s,getReserve(%d)]" % (spoke, asset_id),
                "eth_call[to=%s,symbol()]" % underlying,
                "eth_call[to=%s,decimals()]" % underlying,
            ],
            "mapping_rule": rule,
            "adapter": ADAPTER,
            "adapter_version": ADAPTER_VERSION,
            "protocol_generation": PROTOCOL_GENERATION,
            "source_api": SOURCE_API,
        },
        "native_record": deepcopy(raw),
    }


def _window(capture, source):
    scope = object_(
        required(capture, "scope", "capture manifest"), "capture manifest.scope"
    )
    if text(scope, "chain", "capture manifest.scope") != CHAIN:
        raise TabulariumError("capture manifest scope names another chain")
    first = integer(scope, "from_block", "capture manifest.scope")
    last = integer(scope, "to_block", "capture manifest.scope")
    if first > last:
        raise TabulariumError("capture manifest scope window is inverted")
    meta = object_(source["_meta"], "Aave v4 source._meta")
    declared = object_(required(meta, "window", "Aave v4 source._meta"), "window")
    if (
        integer(declared, "first_block", "window") != first
        or integer(declared, "last_block", "window") != last
    ):
        raise TabulariumError("source window does not match the capture scope")
    topics = object_(required(meta, "topics", "Aave v4 source._meta"), "topics")
    if (
        text(topics, "borrow", "topics") != BORROW_TOPIC
        or text(topics, "repay", "topics") != REPAY_TOPIC
    ):
        raise TabulariumError("source topics are not the Aave v4 credit topics")
    return first, last


def map_source(source, capture):
    source = object_(source, "Aave v4 source")
    unknown = sorted(set(source) - EXPECTED_TOP_LEVEL)
    missing = sorted(EXPECTED_TOP_LEVEL - set(source))
    if unknown:
        raise TabulariumError(
            "Aave v4 source has unsupported top-level field(s): %s" % ", ".join(unknown)
        )
    if missing:
        raise TabulariumError(
            "Aave v4 source is missing top-level field(s): %s" % ", ".join(missing)
        )
    window = _window(capture, source)
    reserves = _reserve_index(source)
    tokens = _token_index(source)

    logs = list_(source["logs"], "Aave v4 source.logs")
    if not logs:
        raise TabulariumError("Aave v4 source maps no credit event")
    events = []
    seen = set()
    for position, raw in enumerate(logs):
        event = _event(raw, position, window, reserves, tokens)
        selector = event["provenance"]["source_selector"]
        if selector in seen:
            raise TabulariumError("Aave v4 source repeats the selector %s" % selector)
        seen.add(selector)
        events.append(event)

    block_hashes = {}
    for event in events:
        transaction = event["transaction"]
        number = transaction["block_number"]
        if block_hashes.setdefault(number, transaction["block_hash"]) != transaction["block_hash"]:
            raise TabulariumError("Aave v4 source gives one block conflicting hashes")

    events.sort(
        key=lambda item: (
            item["transaction"]["block_number"],
            item["transaction"]["log_index"],
            item["id"],
        )
    )
    counts = Counter(event["action"].split(".")[-1] for event in events)
    return MappingResult(tuple(events), dict(sorted(counts.items())), {})
