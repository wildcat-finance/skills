"""Map preserved Goldfinch Graph entities to canonical event v1."""

from copy import deepcopy
from dataclasses import dataclass
import re

from .. import ADAPTER_VERSION, EVENT_SCHEMA_VERSION
from ..core import MAX_SAFE_INTEGER, TabulariumError, ensure_finite_tree, safe_integer


CHAIN = "ethereum-mainnet"
VENUE = "goldfinch"
MAPPED_COLLECTIONS = ("borrows", "repays")
UNMAPPED_COLLECTIONS = ("creditLines", "tranchedPools", "callableLoans")
EXPECTED_TOP_LEVEL = frozenset(MAPPED_COLLECTIONS + UNMAPPED_COLLECTIONS + ("_meta",))

DECIMAL = re.compile(r"^(0|[1-9][0-9]*)$")
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
TX_HASH = re.compile(r"^0x[0-9a-f]{64}$")
SOURCE_ID = re.compile(r"^(0x[0-9a-f]{64})-([0-9]+)$")


@dataclass(frozen=True)
class Mapping:
    family: str
    action: str
    rule: str


MAPPINGS = {
    "borrows": Mapping("borrowing", "goldfinch.borrow", "goldfinch.borrow.v1"),
    "repays": Mapping("repayment", "goldfinch.repay", "goldfinch.repay.v1"),
}


@dataclass(frozen=True)
class MappingResult:
    events: tuple
    mapped_counts: dict
    unmapped_counts: dict


def _object(value, where):
    if not isinstance(value, dict):
        raise TabulariumError("%s is not an object" % where)
    return value


def _required(mapping, key, where):
    mapping = _object(mapping, where)
    if key not in mapping:
        raise TabulariumError("%s has no %r" % (where, key))
    return mapping[key]


def _string(mapping, key, where):
    value = _required(mapping, key, where)
    if not isinstance(value, str) or not value:
        raise TabulariumError("%s.%s is not a non-empty string" % (where, key))
    return value


def _decimal(mapping, key, where):
    value = _string(mapping, key, where)
    if not DECIMAL.fullmatch(value):
        raise TabulariumError("%s.%s is not a base-10 unsigned decimal string" % (where, key))
    return value


def _safe_decimal_integer(value, where):
    if not isinstance(value, str) or not DECIMAL.fullmatch(value):
        raise TabulariumError("%s is not an unsigned decimal string" % where)
    maximum = str(MAX_SAFE_INTEGER)
    if len(value) > len(maximum) or (len(value) == len(maximum) and value > maximum):
        raise TabulariumError("%s is outside the safe integer range" % where)
    integer = int(value)
    return integer


def _address(mapping, key, where):
    value = _string(mapping, key, where)
    if not ADDRESS.fullmatch(value):
        raise TabulariumError("%s.%s is not a lowercase Ethereum address" % (where, key))
    return value


def _transaction_hash(row, where):
    value = _string(row, "hash", where)
    if not TX_HASH.fullmatch(value):
        raise TabulariumError("%s.hash is not a lowercase transaction hash" % where)
    return value


def _source_parts(row, where, transaction_hash):
    source_id = _string(row, "id", where)
    match = SOURCE_ID.fullmatch(source_id)
    if not match:
        raise TabulariumError("%s.id does not contain a transaction hash and log index" % where)
    if match.group(1) != transaction_hash:
        raise TabulariumError("%s.id transaction hash does not match %s.hash" % (where, where))
    log_index = _safe_decimal_integer(match.group(2), "%s.id log index" % where)
    return source_id, log_index


def map_entity(collection, row):
    """Map one native entity without changing the native object it retains."""
    if collection not in MAPPINGS:
        raise TabulariumError("unsupported Goldfinch entity collection %r" % collection)
    where = "%s entity" % collection
    row = _object(row, where)
    ensure_finite_tree(row, where)
    transaction_hash = _transaction_hash(row, where)
    source_id, log_index = _source_parts(row, where, transaction_hash)
    timestamp = _decimal(row, "timestamp", where)
    _safe_decimal_integer(timestamp, "%s.timestamp" % where)
    amount = _decimal(row, "amount", where)

    account = _object(_required(row, "account", where), "%s.account" % where)
    borrower = _address(account, "id", "%s.account" % where)
    market = _object(_required(row, "market", where), "%s.market" % where)
    market_id = _address(market, "id", "%s.market" % where)
    asset = _object(_required(row, "asset", where), "%s.asset" % where)
    symbol = _string(asset, "symbol", "%s.asset" % where)
    decimals = safe_integer(_required(asset, "decimals", "%s.asset" % where), "%s.asset.decimals" % where)

    mapping = MAPPINGS[collection]
    source_selector = "%s[id=%s]" % (collection, source_id)
    event_id = "tabularium:%s:%s:%s:%s" % (
        CHAIN,
        VENUE,
        source_id,
        mapping.rule,
    )
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "id": event_id,
        "event_family": mapping.family,
        "action": mapping.action,
        "venue": VENUE,
        "chain": CHAIN,
        "transaction": {
            "hash": transaction_hash,
            "log_index": log_index,
            "timestamp": timestamp,
        },
        "parties": [{"role": "borrower", "address": borrower}],
        "instrument": {"type": "goldfinch-market", "id": market_id},
        "asset": {"symbol": symbol, "decimals": decimals},
        "amount": {"base_units": amount},
        "provenance": {
            "source_kind": "the-graph-entity",
            "source_contract": market_id,
            "source_entity": collection,
            "source_id": source_id,
            "source_selector": source_selector,
            "mapping_rule": mapping.rule,
            "adapter": VENUE,
            "adapter_version": ADAPTER_VERSION,
        },
        "native_record": deepcopy(row),
    }


def _collection(snapshot, name):
    value = _required(snapshot, name, "snapshot")
    if not isinstance(value, list):
        raise TabulariumError("snapshot.%s is not an array" % name)
    return value


def map_snapshot(snapshot):
    snapshot = _object(snapshot, "snapshot")
    unknown = sorted(set(snapshot) - EXPECTED_TOP_LEVEL)
    missing = sorted(EXPECTED_TOP_LEVEL - set(snapshot))
    if unknown:
        raise TabulariumError("snapshot has unsupported top-level field(s): %s" % ", ".join(unknown))
    if missing:
        raise TabulariumError("snapshot is missing top-level field(s): %s" % ", ".join(missing))
    _object(snapshot["_meta"], "snapshot._meta")

    events = []
    source_ids = set()
    mapped_counts = {}
    for collection in MAPPED_COLLECTIONS:
        rows = _collection(snapshot, collection)
        mapped_counts[MAPPINGS[collection].family] = len(rows)
        for row in rows:
            event = map_entity(collection, row)
            source_id = event["provenance"]["source_id"]
            if source_id in source_ids:
                raise TabulariumError("duplicate source identifier %s" % source_id)
            source_ids.add(source_id)
            events.append(event)

    unmapped_counts = {
        name: len(_collection(snapshot, name)) for name in UNMAPPED_COLLECTIONS
    }
    unmapped_counts["_meta"] = 1
    events.sort(
        key=lambda event: (
            int(event["transaction"]["timestamp"]),
            event["transaction"]["hash"],
            event["transaction"]["log_index"],
            event["event_family"],
            event["id"],
        )
    )
    return MappingResult(tuple(events), mapped_counts, unmapped_counts)
