"""Map preserved Euler V2 activity from the Euler V3 API to event schema v2."""

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone

from ..core import TabulariumError
from .euler_common import (
    MappingResult,
    address,
    bounded_decimal_integer,
    decimal,
    hash_,
    integer,
    list_,
    object_,
    required,
    text,
)


ADAPTER = "euler-v2"
ADAPTER_VERSION = "1.0.0"
PROTOCOL_GENERATION = "euler-v2"
SOURCE_API = "euler-v3"
CHAIN = "ethereum-mainnet"
CHAIN_ID = 1
MAPPINGS = {
    "borrow": ("borrowing", "euler-v2.borrow", "euler-v2.borrow.v1"),
    "repay": ("repayment", "euler-v2.repay", "euler-v2.repay.v1"),
    "liquidation": ("debt-resolution", "euler-v2.liquidation", "euler-v2.liquidation.v1"),
    "debt_socialized": ("debt-resolution", "euler-v2.debt-socialized", "euler-v2.debt-socialized.v1"),
    "pull_debt": ("debt-transfer", "euler-v2.pull-debt", "euler-v2.pull-debt.v1"),
    "interest_accrued": ("interest-accrual", "euler-v2.interest-accrued", "euler-v2.interest-accrued.v1"),
}
EXPECTED_CATEGORIES = {
    "borrow": "borrowing",
    "repay": "borrowing",
    "interest_accrued": "borrowing",
    "debt_socialized": "borrowing",
    "pull_debt": "borrowing",
    "liquidation": "liquidations",
}


def _subaccount(owner, account, index, where):
    expected = owner[2:40] + "%02x" % index
    if account[2:] != expected:
        raise TabulariumError("%s account does not match its EVC owner and sub-account index" % where)


def _amounts(row, event_kind, where):
    raw = list_(required(row, "assets", where), "%s.assets" % where)
    amounts = []
    seen = set()
    for index, item in enumerate(raw):
        item_where = "%s.assets[%d]" % (where, index)
        item = object_(item, item_where)
        kind = text(item, "kind", item_where)
        if kind in seen:
            raise TabulariumError("%s repeats amount kind %r" % (where, kind))
        seen.add(kind)
        asset = item.get("address")
        if asset is not None:
            asset = address(item, "address", item_where)
        if event_kind == "liquidation" and kind == "collateral" and asset is None:
            raise TabulariumError("%s collateral leg has no vault address" % where)
        amounts.append({
            "kind": kind,
            "base_units": decimal(item, "amountRaw", item_where),
            "asset": asset,
        })
    if not amounts:
        raise TabulariumError("%s has no exact amount legs" % where)
    expected = {"assets", "collateral"} if event_kind == "liquidation" else {"assets"}
    if seen != expected:
        raise TabulariumError("%s amount legs do not match event type %r" % (where, event_kind))
    return amounts


def _event(raw, requested_owner, first_timestamp, last_timestamp,
           indexed_from, indexed_to, index):
    where = "Euler V3 response.data[%d]" % index
    row = object_(raw, where)
    if integer(row, "chainId", where) != CHAIN_ID:
        raise TabulariumError("%s is not on Ethereum mainnet" % where)
    kind = text(row, "type", where)
    if kind not in MAPPINGS:
        raise TabulariumError("%s has unknown event type %r" % (where, kind))
    if text(row, "category", where) != EXPECTED_CATEGORIES[kind]:
        raise TabulariumError("%s category does not match its event type" % where)
    if text(row, "source", where) != "v3-ponder":
        raise TabulariumError("%s source is not v3-ponder" % where)
    owner = address(row, "owner", where)
    if owner != requested_owner:
        raise TabulariumError("%s belongs to another EVC owner" % where)
    account = address(row, "account", where)
    sub_index = integer(row, "subAccountIndex", where, maximum=255)
    _subaccount(owner, account, sub_index, where)
    vault = address(row, "vault", where)
    if text(row, "vaultType", where) != "evk":
        raise TabulariumError("%s is not an EVK vault event" % where)
    transaction_hash = hash_(row, "txHash", where)
    block_number = bounded_decimal_integer(row, "blockNumber", where)
    if not indexed_from <= block_number <= indexed_to:
        raise TabulariumError("%s block is outside the reported indexed range" % where)
    log_index = integer(row, "logIndex", where)
    source_id = text(row, "id", where)
    timestamp = text(row, "timestamp", where)
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as error:
        raise TabulariumError("%s timestamp is not ISO-8601" % where) from error
    if parsed_timestamp.tzinfo is None or parsed_timestamp.utcoffset() != timezone.utc.utcoffset(parsed_timestamp):
        raise TabulariumError("%s timestamp is not UTC" % where)
    timestamp_second = int(parsed_timestamp.timestamp())
    if not first_timestamp <= timestamp_second <= last_timestamp:
        raise TabulariumError("%s timestamp is outside the captured query scope" % where)
    family, action, rule = MAPPINGS[kind]
    parties = [
        {"role": "owner", "address": owner},
        {"role": "account", "address": account},
    ]
    if isinstance(row.get("actor"), str):
        parties.append({"role": "actor", "address": address(row, "actor", where)})
    if isinstance(row.get("counterparty"), str):
        parties.append({"role": "counterparty", "address": address(row, "counterparty", where)})
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
            "block_hash": None,
            "transaction_index": None,
            "log_index": log_index,
            "timestamp": timestamp,
        },
        "parties": parties,
        "instrument": {"type": "euler-vault", "id": vault},
        "amounts": _amounts(row, kind, where),
        "provenance": {
            "source_kind": "hosted-indexer-event",
            "source_contract": vault,
            "source_entity": kind,
            "source_id": source_id,
            "source_selector": "data[id=%s]" % source_id,
            "supporting_selectors": [],
            "mapping_rule": rule,
            "adapter": ADAPTER,
            "adapter_version": ADAPTER_VERSION,
            "protocol_generation": PROTOCOL_GENERATION,
            "source_api": SOURCE_API,
        },
        "native_record": deepcopy(row),
    }


def _coverage(source):
    meta = object_(required(source, "meta", "Euler V3 response"), "Euler V3 response.meta")
    if text(meta, "source", "Euler V3 response.meta") != "v3-ponder":
        raise TabulariumError("Euler V3 response meta source is not v3-ponder")
    if meta.get("hasMore") is not False or meta.get("nextCursor") is not None:
        raise TabulariumError("Euler V3 preserved response is not the last query page")
    coverage = object_(required(meta, "coverage", "Euler V3 response.meta"), "Euler V3 response.meta.coverage")
    if text(coverage, "status", "Euler V3 response.meta.coverage") != "complete":
        raise TabulariumError("Euler V3 response does not report complete indexed coverage")
    if list_(required(coverage, "missingCategories", "Euler V3 response.meta.coverage"), "missingCategories"):
        raise TabulariumError("Euler V3 response reports missing categories")
    chains = list_(required(coverage, "chains", "Euler V3 response.meta.coverage"), "coverage.chains")
    if len(chains) != 1:
        raise TabulariumError("Euler V3 response must report one chain")
    chain = object_(chains[0], "coverage.chains[0]")
    if integer(chain, "chainId", "coverage.chains[0]") != CHAIN_ID or text(chain, "status", "coverage.chains[0]") != "complete":
        raise TabulariumError("Euler V3 response does not report complete mainnet coverage")
    if list_(required(chain, "missingCategories", "coverage.chains[0]"), "coverage.chains[0].missingCategories"):
        raise TabulariumError("Euler V3 mainnet coverage reports missing categories")
    first = bounded_decimal_integer(chain, "indexedFromBlock", "coverage.chains[0]")
    last = bounded_decimal_integer(chain, "indexedToBlock", "coverage.chains[0]")
    if first > last:
        raise TabulariumError("Euler V3 response reports a reversed indexed range")
    return first, last


def map_source(source, capture):
    source = object_(source, "Euler V3 response")
    indexed_from, indexed_to = _coverage(source)
    scope = object_(required(capture, "scope", "capture manifest"), "capture manifest.scope")
    owner = str(required(scope, "owner", "capture manifest.scope")).lower()
    first_timestamp = required(scope, "from_timestamp", "capture manifest.scope")
    last_timestamp = required(scope, "to_timestamp", "capture manifest.scope")
    rows = list_(required(source, "data", "Euler V3 response"), "Euler V3 response.data")
    events = [
        _event(
            row,
            owner,
            first_timestamp,
            last_timestamp,
            indexed_from,
            indexed_to,
            index,
        )
        for index, row in enumerate(rows)
    ]
    selectors = [event["provenance"]["source_selector"] for event in events]
    if len(selectors) != len(set(selectors)):
        raise TabulariumError("Euler V3 response repeats an event id")
    identities = [
        (event["transaction"]["hash"], event["transaction"]["log_index"])
        for event in events
    ]
    if len(identities) != len(set(identities)):
        raise TabulariumError("Euler V3 response repeats a transaction/log identity")
    transactions = {}
    for event in events:
        transaction = event["transaction"]
        context = (transaction["block_number"], transaction["timestamp"])
        transaction_hash = transaction["hash"]
        if transaction_hash in transactions and transactions[transaction_hash] != context:
            raise TabulariumError("Euler V3 response gives one transaction conflicting metadata")
        transactions[transaction_hash] = context
    events.sort(key=lambda item: (
        item["transaction"]["block_number"],
        item["transaction"]["hash"],
        item["transaction"]["log_index"],
        item["id"],
    ))
    counts = Counter(event["provenance"]["source_entity"] for event in events)
    return MappingResult(tuple(events), dict(sorted(counts.items())), {})
