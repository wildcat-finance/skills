"""Map preserved Aave v4 user activity from The Graph to event schema v2."""

from collections import Counter
from copy import deepcopy

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


ADAPTER = "aave-v4"
ADAPTER_VERSION = "1.0.0"
PROTOCOL_GENERATION = "aave-v4"
SOURCE_API = "the-graph"
CHAIN = "ethereum-mainnet"
MAPPINGS = {
    "BORROW": ("borrowing", "aave-v4.borrow", "aave-v4.borrow.v1"),
    "REPAY": ("repayment", "aave-v4.repay", "aave-v4.repay.v1"),
}
# Present in the captured window and deliberately left unmapped: they move
# liquidity or collateral flags rather than debt.
UNMAPPED_TYPES = ("SET_COLLATERAL", "SUPPLY", "WITHDRAW")
EXPECTED_TYPES = frozenset(tuple(MAPPINGS) + UNMAPPED_TYPES)
EXPECTED_TOP_LEVEL = frozenset(("_meta", "useractivities"))


def _nested_address(row, key, where):
    nested = object_(required(row, key, where), "%s.%s" % (where, key))
    return address(nested, "id", "%s.%s" % (where, key))


def _amounts(row, kind, where):
    """Return the debt legs this row actually reports.

    A BORROW states the assets drawn. A REPAY leaves ``amount`` null and
    states ``totalAmountRepaid`` instead, so the asset leg reads that field
    and no value is reconstructed for the other. Neither row names the
    underlying token, so every leg's asset stays null.
    """

    shares = decimal(row, "shares", where)
    if kind == "BORROW":
        if row.get("totalAmountRepaid") is not None:
            raise TabulariumError("%s is a BORROW that reports a repaid total" % where)
        assets = decimal(row, "amount", where)
        asset_kind = "assets_drawn"
    else:
        if row.get("amount") is not None:
            raise TabulariumError("%s is a REPAY that reports a drawn amount" % where)
        assets = decimal(row, "totalAmountRepaid", where)
        asset_kind = "assets_repaid"
    return [
        {"kind": asset_kind, "base_units": assets, "asset": None},
        {"kind": "shares", "base_units": shares, "asset": None},
    ]


def _event(row, index, first_block, last_block):
    where = "useractivities[%d]" % index
    row = object_(row, where)
    kind = text(row, "type", where)
    if kind not in MAPPINGS:
        raise TabulariumError("%s is not a mapped Aave v4 activity type" % where)
    transaction_hash = hash_(row, "txHash", where)
    block_number = bounded_decimal_integer(row, "block", where)
    if not first_block <= block_number <= last_block:
        raise TabulariumError("%s block is outside the captured window" % where)
    log_index = bounded_decimal_integer(row, "logIndex", where)
    timestamp = decimal(row, "timestamp", where)
    source_id = text(row, "id", where)
    if not source_id.startswith(transaction_hash):
        raise TabulariumError("%s id does not begin with its transaction hash" % where)
    spoke = _nested_address(row, "spoke", where)
    user = _nested_address(row, "user", where)
    caller = address(row, "caller", where)
    reserve = object_(required(row, "reserve", where), "%s.reserve" % where)
    reserve_id = text(reserve, "id", "%s.reserve" % where)
    if not reserve_id.startswith(spoke):
        raise TabulariumError("%s reserve does not belong to its spoke" % where)

    family, action, rule = MAPPINGS[kind]
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
            "block_hash": None,
            "transaction_index": None,
            "log_index": log_index,
            "timestamp": timestamp,
        },
        "parties": parties,
        "instrument": {"type": "aave-v4-spoke", "id": spoke},
        "amounts": _amounts(row, kind, where),
        "provenance": {
            "source_kind": "the-graph-entity",
            "source_contract": spoke,
            "source_entity": "useractivities",
            "source_id": source_id,
            "source_selector": "useractivities[id=%s]" % source_id,
            "supporting_selectors": [],
            "mapping_rule": rule,
            "adapter": ADAPTER,
            "adapter_version": ADAPTER_VERSION,
            "protocol_generation": PROTOCOL_GENERATION,
            "source_api": SOURCE_API,
        },
        "native_record": deepcopy(row),
    }


def _window(capture):
    scope = object_(
        required(capture, "scope", "capture manifest"), "capture manifest.scope"
    )
    if text(scope, "chain", "capture manifest.scope") != CHAIN:
        raise TabulariumError("capture manifest scope names another chain")
    first_block = integer(scope, "from_block", "capture manifest.scope")
    last_block = integer(scope, "to_block", "capture manifest.scope")
    if first_block > last_block:
        raise TabulariumError("capture manifest scope window is inverted")
    return first_block, last_block


def map_source(source, capture):
    source = object_(source, "Aave v4 snapshot")
    unknown = sorted(set(source) - EXPECTED_TOP_LEVEL)
    missing = sorted(EXPECTED_TOP_LEVEL - set(source))
    if unknown:
        raise TabulariumError(
            "Aave v4 snapshot has unsupported top-level field(s): %s"
            % ", ".join(unknown)
        )
    if missing:
        raise TabulariumError(
            "Aave v4 snapshot is missing top-level field(s): %s" % ", ".join(missing)
        )
    object_(source["_meta"], "Aave v4 snapshot._meta")
    rows = list_(source["useractivities"], "Aave v4 snapshot.useractivities")
    first_block, last_block = _window(capture)

    events = []
    unmapped = Counter()
    seen = set()
    for index, row in enumerate(rows):
        kind = text(object_(row, "useractivities[%d]" % index), "type", "useractivities[%d]" % index)
        if kind not in EXPECTED_TYPES:
            raise TabulariumError(
                "useractivities[%d] has an unsupported activity type %r" % (index, kind)
            )
        if kind not in MAPPINGS:
            unmapped[kind] += 1
            continue
        event = _event(row, index, first_block, last_block)
        selector = event["provenance"]["source_selector"]
        if selector in seen:
            raise TabulariumError("Aave v4 snapshot repeats the selector %s" % selector)
        seen.add(selector)
        events.append(event)

    if not events:
        raise TabulariumError("Aave v4 snapshot maps no credit event")
    events.sort(
        key=lambda item: (
            item["transaction"]["block_number"],
            item["transaction"]["log_index"],
            item["id"],
        )
    )
    counts = Counter(event["action"].split(".")[-1] for event in events)
    return MappingResult(
        tuple(events), dict(sorted(counts.items())), dict(sorted(unmapped.items()))
    )
