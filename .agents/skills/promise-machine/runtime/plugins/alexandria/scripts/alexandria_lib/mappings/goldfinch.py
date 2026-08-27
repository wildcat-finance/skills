"""Goldfinch Tabularium mapping for events and credit-line observations."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from ..errors import AlexandriaError
from ..rows import event_row, observation_row, provenance
from .common import (
    coverage_declaration,
    decimal,
    enforce_subject_scope,
    integer,
    list_value,
    load_source,
    object_value,
    require_coverage,
    required,
    string,
)


ADAPTER = "goldfinch"
ADAPTER_VERSION = "1.0.0"
MAPPING_REVISION = "goldfinch.credit.v1"
CHAIN = "eip155:1"
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
TX_HASH = re.compile(r"^0x[0-9a-f]{64}$")
SOURCE_ID = re.compile(r"^(0x[0-9a-f]{64})-((?:0|[1-9][0-9]*))$")
RULES = (
    "goldfinch.borrow.v1",
    "goldfinch.credit-line-balance.v1",
    "goldfinch.repay.v1",
)


def map_capture(capture, data, source_release_id):
    if (
        capture["chain"] != CHAIN
        or capture["evidence_class"] != "hosted-indexer"
        or capture["source"]["kind"] != "hosted-indexer"
        or capture["scope"]["interval"]["kind"] != "snapshot"
    ):
        raise AlexandriaError(
            "Goldfinch mapping requires an eip155:1 hosted-indexer snapshot"
        )
    source = object_value(load_source(data, capture), "Goldfinch source")
    expected_keys = {"_meta", "borrows", "repays", "creditLines", "callableLoans", "tranchedPools"}
    if set(source) != expected_keys:
        raise AlexandriaError("Goldfinch source collections do not match the registered mapping")
    collections = {
        name: list_value(source[name], f"Goldfinch {name}")
        for name in expected_keys - {"_meta"}
    }
    require_coverage(capture, {f"/{name}": len(rows) for name, rows in collections.items()})
    meta = object_value(source["_meta"], "Goldfinch _meta")
    block = object_value(required(meta, "block", "Goldfinch _meta"), "Goldfinch _meta.block")
    block_number = integer(block, "number", "Goldfinch _meta.block")
    block_timestamp = integer(block, "timestamp", "Goldfinch _meta.block")
    observed_at = datetime.fromisoformat(
        capture["scope"]["interval"]["observed_at"].removesuffix("Z") + "+00:00"
    ).astimezone(timezone.utc)
    if block_timestamp > int(observed_at.timestamp()):
        raise AlexandriaError("Goldfinch source block is later than its capture time")
    interval = capture["scope"]["interval"]
    if "block_number" in interval and int(interval["block_number"]) != block_number:
        raise AlexandriaError("Goldfinch source block disagrees with its snapshot boundary")

    events = []
    observations = []
    identities = set()
    for collection, family, action, rule in (
        ("borrows", "borrowing", "goldfinch.borrow", "goldfinch.borrow.v1"),
        ("repays", "repayment", "goldfinch.repay", "goldfinch.repay.v1"),
    ):
        for index, native in enumerate(collections[collection]):
            where = f"Goldfinch {collection}[{index}]"
            native = object_value(native, where)
            tx_hash = string(native, "hash", where)
            if not TX_HASH.fullmatch(tx_hash):
                raise AlexandriaError(f"{where}.hash is not a lowercase transaction hash")
            source_identity = string(native, "id", where)
            match = SOURCE_ID.fullmatch(source_identity)
            if (
                match is None
                or match.group(1) != tx_hash
                or len(match.group(2)) > 78
                or (len(match.group(2)) > 1 and match.group(2).startswith("0"))
            ):
                raise AlexandriaError(f"{where}.id is not its transaction hash and log index")
            if source_identity in identities:
                raise AlexandriaError(f"duplicate Goldfinch source identity {source_identity}")
            identities.add(source_identity)
            account = _address(required(native, "account", where), "id", f"{where}.account")
            market = _address(required(native, "market", where), "id", f"{where}.market")
            asset = object_value(required(native, "asset", where), f"{where}.asset")
            symbol = string(asset, "symbol", f"{where}.asset")
            decimals = integer(asset, "decimals", f"{where}.asset", maximum=255)
            amount = decimal(native, "amount", where)
            timestamp = decimal(native, "timestamp", where)
            if int(timestamp) > block_timestamp:
                raise AlexandriaError(f"{where}.timestamp is later than the source snapshot")
            prov = provenance(
                source_release_id=source_release_id,
                component=capture["component"],
                component_sha256=capture["component_sha256"],
                capture_id=capture["id"],
                source_selector=f"/{collection}/{index}",
                source_identity=source_identity,
                mapping_rule=rule,
                adapter=ADAPTER,
                adapter_version=ADAPTER_VERSION,
                evidence_class=capture["evidence_class"],
            )
            events.append(event_row(
                identity=f"{CHAIN}:{source_identity}",
                chain=CHAIN,
                venue=ADAPTER,
                subject=f"{CHAIN}:{account}",
                deployment=capture["scope"]["deployment"],
                facility={"kind": "goldfinch-market", "id": market},
                event_family=family,
                action=action,
                amounts=[{
                    "asset": {"chain": CHAIN, "decimals": decimals, "symbol": symbol},
                    "base_units": amount,
                    "role": "source-amount",
                }],
                transaction={
                    "hash": tx_hash,
                    "log_index": match.group(2),
                    "timestamp": timestamp,
                },
                provenance=prov,
            ))

    for index, native in enumerate(collections["creditLines"]):
        where = f"Goldfinch creditLines[{index}]"
        native = object_value(native, where)
        credit_line = _address(native, "id", where)
        borrower = _address(native, "borrower", where)
        source_identity = credit_line
        identity_key = "credit-line:" + source_identity
        if identity_key in identities:
            raise AlexandriaError(f"duplicate Goldfinch credit-line identity {source_identity}")
        identities.add(identity_key)
        balance = decimal(native, "balance", where)
        maturity = decimal(native, "termEndTime", where)
        rule = "goldfinch.credit-line-balance.v1"
        prov = provenance(
            source_release_id=source_release_id,
            component=capture["component"],
            component_sha256=capture["component_sha256"],
            capture_id=capture["id"],
            source_selector=f"/creditLines/{index}",
            source_identity=source_identity,
            mapping_rule=rule,
            adapter=ADAPTER,
            adapter_version=ADAPTER_VERSION,
            evidence_class=capture["evidence_class"],
            context_selectors=("/_meta",),
        )
        observations.append(observation_row(
            identity=(
                f"{CHAIN}:{identity_key}:"
                f"{block_number}:{block_timestamp}"
            ),
            chain=CHAIN,
            venue=ADAPTER,
            subject=f"{CHAIN}:{borrower}",
            deployment=capture["scope"]["deployment"],
            facility={"kind": "goldfinch-credit-line", "id": credit_line},
            observation={
                "at": {"block_number": str(block_number), "timestamp": str(block_timestamp)},
                "evidence_class": capture["evidence_class"],
                "method": "hosted-indexer-snapshot",
                "property": "goldfinch.credit-line-balance",
                "unit": "base-units",
                "value": balance,
            },
            terms={"maturity_timestamp": maturity},
            provenance=prov,
        ))

    all_rows = events + observations
    enforce_subject_scope(capture, all_rows)
    declaration = {
        "adapter": ADAPTER,
        "adapter_version": ADAPTER_VERSION,
        "capture_id": capture["id"],
        "coverage": coverage_declaration(
            capture,
            mapped={
                "borrows": len(collections["borrows"]),
                "creditLines": len(collections["creditLines"]),
                "repays": len(collections["repays"]),
            },
            context={},
            unsupported={
                "callableLoans": len(collections["callableLoans"]),
                "tranchedPools": len(collections["tranchedPools"]),
            },
        ),
        "mapping_revision": MAPPING_REVISION,
        "rules": list(RULES),
    }
    return events, observations, declaration


def _address(mapping, key, where):
    value = string(object_value(mapping, where), key, where)
    if not ADDRESS.fullmatch(value):
        raise AlexandriaError(f"{where}.{key} is not a lowercase EVM address")
    return value
