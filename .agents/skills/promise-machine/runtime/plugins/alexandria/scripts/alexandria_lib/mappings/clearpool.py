"""Clearpool Tabularium mapping for pool borrow and repayment logs."""

from __future__ import annotations

import re

from ..canonical import canonical_bytes
from ..errors import AlexandriaError
from ..rows import event_row, provenance
from ..release import sha256
from .common import (
    coverage_declaration,
    enforce_subject_scope,
    integer,
    list_value,
    load_source,
    object_value,
    pointer_escape,
    require_coverage,
    required,
    string,
)


ADAPTER = "clearpool"
ADAPTER_VERSION = "1.0.0"
MAPPING_REVISION = "clearpool.credit.v1"
CHAIN = "eip155:1"
FACTORY = "0x969d7ddbe3b6f8b51e26d8473aaac1a9f4a6b47b"
POOL_CREATED = "0x2f50e78ec41ff359ae53695bfffb5c9bae020d7db3779e5f666a3a020ef062b4"
BORROWED = "0x84d6fc9f7244aba67b2ad2bfc67d8d3ed92b7e4932a482888bac6a4595019a15"
REPAID = "0x33a382daad6aace935340a474d09fec82af4bec7e2b69518d283231b03a65f24"
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
HASH = re.compile(r"^0x[0-9a-f]{64}$")
RULES = ("clearpool.borrow.v1", "clearpool.repay-pool-manager.v1")


def map_capture(capture, data, source_release_id):
    if (
        capture["chain"] != CHAIN
        or capture["evidence_class"] != "archive-log"
        or capture["source"]["kind"] != "ethereum-logs"
        or capture["scope"]["interval"]["kind"] != "block-range"
    ):
        raise AlexandriaError(
            "Clearpool mapping requires an eip155:1 archive-log block range"
        )
    interval_start = int(capture["scope"]["interval"]["start"])
    interval_end = int(capture["scope"]["interval"]["end"])
    source = object_value(load_source(data, capture), "Clearpool source")
    expected_keys = {"factory_pools", "pool_logs", "currencies", "block_times"}
    if set(source) != expected_keys:
        raise AlexandriaError("Clearpool source collections do not match the registered mapping")
    factory_logs = list_value(source["factory_pools"], "Clearpool factory_pools")
    pool_logs = object_value(source["pool_logs"], "Clearpool pool_logs")
    currencies = object_value(source["currencies"], "Clearpool currencies")
    block_times = object_value(source["block_times"], "Clearpool block_times")
    expected_coverage = {"/factory_pools": len(factory_logs)}
    for pool, logs in pool_logs.items():
        _address(pool, "Clearpool pool_logs key")
        expected_coverage[f"/pool_logs/{pointer_escape(pool)}"] = len(
            list_value(logs, f"Clearpool pool_logs[{pool}]")
        )
    require_coverage(capture, expected_coverage)

    pools = {}
    for index, log in enumerate(factory_logs):
        where = f"Clearpool factory_pools[{index}]"
        log = object_value(log, where)
        if _address(string(log, "address", where), f"{where}.address") != FACTORY:
            raise AlexandriaError(f"{where} is not emitted by the Clearpool factory")
        _require_block_in_range(log, where, interval_start, interval_end)
        topics = list_value(required(log, "topics", where), f"{where}.topics")
        if len(topics) != 4 or topics[0] != POOL_CREATED:
            raise AlexandriaError(f"{where} is not a PoolCreated log")
        pool = _topic_address(topics[1], f"{where}.pool")
        manager = _topic_address(topics[2], f"{where}.manager")
        currency = _topic_address(topics[3], f"{where}.currency")
        if pool in pools:
            raise AlexandriaError(f"Clearpool pool {pool} is declared more than once")
        if capture["scope"]["kind"] == "subject-scoped":
            subject = f"{CHAIN}:{manager}"
            if subject not in capture["scope"]["subjects"]:
                raise AlexandriaError(f"Clearpool factory context names out-of-scope manager {manager}")
        pools[pool] = (manager, currency, f"/factory_pools/{index}")
    if set(pool_logs) != set(pools):
        raise AlexandriaError("Clearpool pool_logs keys do not match PoolCreated context")
    if set(currencies) != set(pools):
        raise AlexandriaError("Clearpool currency keys do not match PoolCreated context")

    events = []
    fingerprints = set()
    borrow_count = 0
    repay_count = 0
    for pool in sorted(pools):
        manager, currency, factory_selector = pools[pool]
        currency_meta = object_value(currencies[pool], f"Clearpool currencies[{pool}]")
        symbol = string(currency_meta, "symbol", f"Clearpool currencies[{pool}]")
        decimals = integer(currency_meta, "decimals", f"Clearpool currencies[{pool}]", maximum=255)
        logs = list_value(pool_logs[pool], f"Clearpool pool_logs[{pool}]")
        for index, log in enumerate(logs):
            where = f"Clearpool pool_logs[{pool}][{index}]"
            log = object_value(log, where)
            if _address(string(log, "address", where), f"{where}.address") != pool:
                raise AlexandriaError(f"{where} address does not match its pool")
            topics = list_value(required(log, "topics", where), f"{where}.topics")
            if not topics or not isinstance(topics[0], str):
                raise AlexandriaError(f"{where} carries no event topic")
            topic0 = topics[0]
            if topic0 == BORROWED:
                if len(topics) != 2:
                    raise AlexandriaError(f"{where} Borrowed topics are malformed")
                borrower = _topic_address(topics[1], f"{where}.borrower")
                if borrower != manager:
                    raise AlexandriaError(f"{where} borrower is not the pool manager")
                family = "borrowing"
                action = "clearpool.borrow"
                rule = "clearpool.borrow.v1"
                borrow_count += 1
            elif topic0 == REPAID:
                if len(topics) != 1:
                    raise AlexandriaError(f"{where} Repaid topics are malformed")
                family = "repayment"
                action = "clearpool.repay"
                rule = "clearpool.repay-pool-manager.v1"
                repay_count += 1
            else:
                raise AlexandriaError(f"{where} has an unknown Clearpool action topic {topic0}")
            amount = _uint256(string(log, "data", where), f"{where}.data")
            tx_hash = string(log, "transactionHash", where)
            if not HASH.fullmatch(tx_hash):
                raise AlexandriaError(f"{where}.transactionHash is malformed")
            block_number = _hex_quantity(string(log, "blockNumber", where), f"{where}.blockNumber")
            if not interval_start <= block_number <= interval_end:
                raise AlexandriaError(f"{where}.blockNumber is outside the capture range")
            timestamp = block_times.get(str(block_number))
            if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
                raise AlexandriaError(f"{where} has no valid captured block timestamp")
            fingerprint = sha256(canonical_bytes({
                "address": pool,
                "data": log["data"],
                "topics": topics,
                "transaction_hash": tx_hash,
            }))
            if fingerprint in fingerprints:
                raise AlexandriaError(f"duplicate Clearpool log identity {fingerprint}")
            fingerprints.add(fingerprint)
            selector = f"/pool_logs/{pointer_escape(pool)}/{index}"
            prov = provenance(
                source_release_id=source_release_id,
                component=capture["component"],
                component_sha256=capture["component_sha256"],
                capture_id=capture["id"],
                source_selector=selector,
                source_identity=fingerprint,
                mapping_rule=rule,
                adapter=ADAPTER,
                adapter_version=ADAPTER_VERSION,
                evidence_class=capture["evidence_class"],
                context_selectors=(
                    factory_selector,
                    f"/currencies/{pointer_escape(pool)}",
                    f"/block_times/{block_number}",
                ),
            )
            transaction = {
                "block_number": str(block_number),
                "hash": tx_hash,
                "timestamp": str(timestamp),
            }
            if "logIndex" in log:
                transaction["log_index"] = str(_hex_quantity(log["logIndex"], f"{where}.logIndex"))
            events.append(event_row(
                identity=f"{CHAIN}:{fingerprint}",
                chain=CHAIN,
                venue=ADAPTER,
                subject=f"{CHAIN}:{manager}",
                deployment=capture["scope"]["deployment"],
                facility={"kind": "clearpool-pool", "id": pool},
                event_family=family,
                action=action,
                amounts=[{
                    "asset": {
                        "address": currency,
                        "chain": CHAIN,
                        "decimals": decimals,
                        "symbol": symbol,
                    },
                    "base_units": str(amount),
                    "role": "source-amount",
                }],
                transaction=transaction,
                provenance=prov,
            ))

    enforce_subject_scope(capture, events)
    declaration = {
        "adapter": ADAPTER,
        "adapter_version": ADAPTER_VERSION,
        "capture_id": capture["id"],
        "coverage": coverage_declaration(
            capture,
            mapped={"pool-logs": borrow_count + repay_count},
            context={"factory-pools": len(factory_logs)},
            unsupported={},
        ),
        "mapping_revision": MAPPING_REVISION,
        "rules": list(RULES),
    }
    return events, [], declaration


def _address(value, where):
    if not isinstance(value, str) or not ADDRESS.fullmatch(value):
        raise AlexandriaError(f"{where} is not a lowercase EVM address")
    return value


def _topic_address(value, where):
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-f]{64}", value):
        raise AlexandriaError(f"{where} is not a 32-byte topic")
    if value[2:26] != "0" * 24:
        raise AlexandriaError(f"{where} is not a padded address topic")
    return "0x" + value[-40:]


def _uint256(value, where):
    if not isinstance(value, str) or not re.fullmatch(r"0x[0-9a-f]{64}", value):
        raise AlexandriaError(f"{where} is not one encoded uint256")
    return int(value, 16)


def _hex_quantity(value, where):
    if (
        not isinstance(value, str)
        or len(value) > 66
        or not re.fullmatch(r"0x(?:0|[1-9a-f][0-9a-f]*)", value)
    ):
        raise AlexandriaError(f"{where} is not a canonical hex quantity")
    return int(value, 16)


def _require_block_in_range(log, where, start, end):
    block_number = _hex_quantity(
        string(log, "blockNumber", where),
        f"{where}.blockNumber",
    )
    if not start <= block_number <= end:
        raise AlexandriaError(f"{where}.blockNumber is outside the capture range")
    return block_number
