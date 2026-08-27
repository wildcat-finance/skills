"""Map a preserved Euler v1 canonical-proxy log response to event schema v2."""

from collections import Counter
from copy import deepcopy

from ..core import TabulariumError
from .euler_common import (
    MappingResult,
    abi_words,
    hash_,
    hex_integer,
    list_,
    object_,
    required,
    topic_address,
    word_address,
)


ADAPTER = "euler-v1"
ADAPTER_VERSION = "1.0.0"
PROTOCOL_GENERATION = "euler-v1"
SOURCE_API = "ethereum-json-rpc"
CHAIN = "ethereum-mainnet"
PROXY = "0x27182842e098f60e3d576794a5bffb0777e025d3"
BORROW_TOPIC = "0x312a5e5e1079f5dda4e95dbbd0b908b291fd5b992ef22073643ab691572c5b52"
REPAY_TOPIC = "0x05f2eeda0e08e4b437f487c8d7d29b14537d15e3488170dc3de5dbdf8dac4684"
LIQUIDATION_TOPIC = "0xbba0f1d6fb8b9abe2bbc543b7c13d43faba91c6f78da4700381c94041ac7267d"
MAPPINGS = {
    BORROW_TOPIC: ("borrowing", "euler-v1.borrow", "euler-v1.borrow.v1"),
    REPAY_TOPIC: ("repayment", "euler-v1.repay", "euler-v1.repay.v1"),
    LIQUIDATION_TOPIC: ("debt-resolution", "euler-v1.liquidation", "euler-v1.liquidation.v1"),
}


def _rpc_rows(source):
    source = object_(source, "Euler v1 source")
    if source.get("jsonrpc") != "2.0" or source.get("id") != 1:
        raise TabulariumError("Euler v1 source is not the requested JSON-RPC response")
    if "error" in source:
        raise TabulariumError("Euler v1 JSON-RPC source contains an error")
    return list_(required(source, "result", "Euler v1 source"), "Euler v1 source.result")


def _log(raw, borrower, first_block, last_block, index):
    where = "Euler v1 source.result[%d]" % index
    raw = object_(raw, where)
    if raw.get("address", "").lower() != PROXY:
        raise TabulariumError("%s was not emitted by the canonical proxy" % where)
    if raw.get("removed") is not False:
        raise TabulariumError("%s is removed or lacks a canonicality flag" % where)
    topics = list_(required(raw, "topics", where), "%s.topics" % where)
    if not topics or not isinstance(topics[0], str):
        raise TabulariumError("%s has no event topic" % where)
    signature = topics[0].lower()
    if signature not in MAPPINGS:
        raise TabulariumError("%s has an unrequested event topic" % where)
    expected_topics = 4 if signature == LIQUIDATION_TOPIC else 3
    if len(topics) != expected_topics:
        raise TabulariumError("%s has the wrong topic count" % where)
    account = topic_address(topics[2], "%s.topics[2]" % where)
    if account != borrower:
        raise TabulariumError("%s belongs to a different borrower" % where)
    block_number = hex_integer(required(raw, "blockNumber", where), "%s.blockNumber" % where)
    if not first_block <= block_number <= last_block:
        raise TabulariumError("%s is outside the captured block scope" % where)
    transaction_hash = hash_(raw, "transactionHash", where)
    block_hash = hash_(raw, "blockHash", where)
    transaction_index = hex_integer(required(raw, "transactionIndex", where), "%s.transactionIndex" % where)
    log_index = hex_integer(required(raw, "logIndex", where), "%s.logIndex" % where)
    underlying = topic_address(topics[3] if signature == LIQUIDATION_TOPIC else topics[1], "%s.underlying" % where)
    family, action, rule = MAPPINGS[signature]
    parties = [{"role": "borrower", "address": account}]
    amounts = []
    if signature == LIQUIDATION_TOPIC:
        parties.append({"role": "liquidator", "address": topic_address(topics[1], "%s.liquidator" % where)})
        words = abi_words(required(raw, "data", where), 6, "%s.data" % where)
        collateral = word_address(words[0], "%s.collateral" % where)
        amounts = [
            {"kind": "debt_repaid", "base_units": str(words[1]), "asset": underlying},
            {"kind": "collateral_seized", "base_units": str(words[2]), "asset": collateral},
        ]
    else:
        amount = abi_words(required(raw, "data", where), 1, "%s.data" % where)[0]
        amounts = [{"kind": "assets", "base_units": str(amount), "asset": underlying}]
    selector = "eth_getLogs[transactionHash=%s,logIndex=%d]" % (transaction_hash, log_index)
    return {
        "schema_version": 2,
        "id": "tabularium:%s:%s:%s:%d:%s" % (CHAIN, ADAPTER, transaction_hash, log_index, rule),
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
            "timestamp": None,
        },
        "parties": parties,
        "instrument": {"type": "euler-v1-proxy", "id": PROXY},
        "amounts": amounts,
        "provenance": {
            "source_kind": "ethereum-json-rpc-log",
            "source_contract": PROXY,
            "source_entity": "eth_getLogs",
            "source_id": "%s:%d" % (transaction_hash, log_index),
            "source_selector": selector,
            "supporting_selectors": [],
            "mapping_rule": rule,
            "adapter": ADAPTER,
            "adapter_version": ADAPTER_VERSION,
            "protocol_generation": PROTOCOL_GENERATION,
            "source_api": SOURCE_API,
        },
        "native_record": deepcopy(raw),
    }


def map_source(source, capture):
    scope = object_(required(capture, "scope", "capture manifest"), "capture manifest.scope")
    borrower = str(required(scope, "borrower", "capture manifest.scope")).lower()
    first_block = required(scope, "from_block", "capture manifest.scope")
    last_block = required(scope, "to_block", "capture manifest.scope")
    rows = _rpc_rows(source)
    events = [_log(row, borrower, first_block, last_block, index) for index, row in enumerate(rows)]
    selectors = [event["provenance"]["source_selector"] for event in events]
    if len(selectors) != len(set(selectors)):
        raise TabulariumError("Euler v1 source repeats a transaction/log selector")
    block_hashes = {}
    transactions = {}
    for event in events:
        transaction = event["transaction"]
        block_number = transaction["block_number"]
        block_hash = transaction["block_hash"]
        if block_number in block_hashes and block_hashes[block_number] != block_hash:
            raise TabulariumError("Euler v1 source gives one block conflicting hashes")
        block_hashes[block_number] = block_hash
        transaction_context = (
            block_number,
            block_hash,
            transaction["transaction_index"],
        )
        transaction_hash = transaction["hash"]
        if transaction_hash in transactions and transactions[transaction_hash] != transaction_context:
            raise TabulariumError("Euler v1 source gives one transaction conflicting metadata")
        transactions[transaction_hash] = transaction_context
    events.sort(key=lambda item: (
        item["transaction"]["block_number"],
        item["transaction"]["transaction_index"],
        item["transaction"]["log_index"],
        item["id"],
    ))
    counts = Counter(event["action"].split(".")[-1] for event in events)
    return MappingResult(tuple(events), dict(sorted(counts.items())), {})
