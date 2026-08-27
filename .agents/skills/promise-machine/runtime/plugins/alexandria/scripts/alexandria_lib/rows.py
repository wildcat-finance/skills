"""Protocol-neutral Tabularium credit rows for Alexandria releases."""

from __future__ import annotations

from copy import deepcopy
import re

from .canonical import canonical_bytes
from .errors import AlexandriaError
from .release import (
    ACCOUNT_RE,
    BLOCK_HASH_RE,
    CHAIN_RE,
    DECIMAL_RE,
    DIGEST_RE,
    EVIDENCE_CLASSES,
    MAX_INTEGER_DIGITS,
    NAME_RE,
    sha256,
)


EVENT_SCHEMA = "alexandria-credit-event/v1"
OBSERVATION_SCHEMA = "alexandria-position-observation/v1"
ROW_ID_RE = DIGEST_RE
ADDRESS_RE = re.compile(r"^0x[0-9a-f]{40}$")
TX_HASH_RE = re.compile(r"^0x[0-9a-f]{64}$")
ACTION_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.[a-z0-9][a-z0-9._-]*$")
EVENT_FAMILIES = {"borrowing", "repayment", "liquidation"}


def event_row(*, identity, chain, venue, subject, deployment, facility,
              event_family, action, amounts, provenance, transaction=None):
    row = {
        "action": action,
        "amounts": deepcopy(amounts),
        "chain": chain,
        "deployment": deployment,
        "event_family": event_family,
        "facility": deepcopy(facility),
        "provenance": deepcopy(provenance),
        "row_kind": "credit-event",
        "schema": EVENT_SCHEMA,
        "subject": subject,
        "venue": venue,
    }
    if transaction is not None:
        row["transaction"] = deepcopy(transaction)
    row["id"] = row_id("credit-event", identity, provenance["mapping_rule"])
    validate_event(row)
    return row


def observation_row(*, identity, chain, venue, subject, deployment, facility,
                    observation, provenance, terms=None):
    row = {
        "chain": chain,
        "deployment": deployment,
        "facility": deepcopy(facility),
        "observation": deepcopy(observation),
        "provenance": deepcopy(provenance),
        "row_kind": "position-observation",
        "schema": OBSERVATION_SCHEMA,
        "subject": subject,
        "venue": venue,
    }
    if terms is not None:
        row["terms"] = deepcopy(terms)
    row["id"] = row_id("position-observation", identity, provenance["mapping_rule"])
    validate_observation(row)
    return row


def row_id(kind, identity, mapping_rule):
    if not isinstance(identity, str) or not identity:
        raise AlexandriaError("row source identity must be non-empty")
    return sha256(canonical_bytes({
        "kind": kind,
        "mapping_rule": mapping_rule,
        "source_identity": identity,
    }))


def provenance(*, source_release_id, component, component_sha256, capture_id,
               source_selector, source_identity, mapping_rule, adapter,
               adapter_version, evidence_class, context_selectors=()):
    value = {
        "adapter": adapter,
        "adapter_version": adapter_version,
        "capture_id": capture_id,
        "component": component,
        "component_sha256": component_sha256,
        "evidence_class": evidence_class,
        "mapping_rule": mapping_rule,
        "source_identity": source_identity,
        "source_release_id": source_release_id,
        "source_selector": source_selector,
    }
    if context_selectors:
        value["context_selectors"] = list(context_selectors)
    _validate_provenance(value)
    return value


def validate_event(row):
    required = {
        "schema", "id", "row_kind", "chain", "venue", "subject",
        "deployment", "facility", "event_family", "action", "amounts",
        "provenance",
    }
    _keys(row, required, "credit event", allowed=required | {"transaction"})
    if row["schema"] != EVENT_SCHEMA or row["row_kind"] != "credit-event":
        raise AlexandriaError("credit event has the wrong schema or row kind")
    _common(row)
    if not isinstance(row["event_family"], str) or row["event_family"] not in EVENT_FAMILIES:
        raise AlexandriaError("credit event has an unknown event family")
    if not isinstance(row["action"], str) or not ACTION_RE.fullmatch(row["action"]):
        raise AlexandriaError("credit event action must be venue-qualified")
    if not row["action"].startswith(row["venue"] + "."):
        raise AlexandriaError("credit event action must match its venue")
    amounts = row["amounts"]
    if not isinstance(amounts, list) or not amounts:
        raise AlexandriaError("credit event requires at least one amount leg")
    if len(amounts) > 16:
        raise AlexandriaError("credit event has too many amount legs")
    for amount in amounts:
        _validate_amount(amount)
    if "transaction" in row:
        _validate_transaction(row["transaction"])
    return row


def validate_observation(row):
    required = {
        "schema", "id", "row_kind", "chain", "venue", "subject",
        "deployment", "facility", "observation", "provenance",
    }
    _keys(row, required, "position observation", allowed=required | {"terms"})
    if row["schema"] != OBSERVATION_SCHEMA or row["row_kind"] != "position-observation":
        raise AlexandriaError("position observation has the wrong schema or row kind")
    _common(row)
    observation = row["observation"]
    _keys(
        observation,
        {"property", "value", "unit", "at", "method", "evidence_class"},
        "observation",
    )
    _qualified(observation["property"], "observation property")
    if not observation["property"].startswith(row["venue"] + "."):
        raise AlexandriaError("observation property must match its venue")
    _decimal(observation["value"], "observation value")
    _stable_name(observation["unit"], "observation unit")
    _stable_name(observation["method"], "observation method")
    if (
        not isinstance(observation["evidence_class"], str)
        or observation["evidence_class"] not in EVIDENCE_CLASSES
    ):
        raise AlexandriaError("observation evidence class is unknown")
    if observation["evidence_class"] != row["provenance"]["evidence_class"]:
        raise AlexandriaError("observation evidence class disagrees with provenance")
    at = observation["at"]
    _keys(at, set(), "observation boundary", allowed={"block_number", "block_hash", "timestamp"})
    if not at:
        raise AlexandriaError("observation boundary cannot be empty")
    for key in ("block_number", "timestamp"):
        if key in at:
            _decimal(at[key], f"observation {key}")
    if "block_hash" in at and (
        not isinstance(at["block_hash"], str) or not BLOCK_HASH_RE.fullmatch(at["block_hash"])
    ):
        raise AlexandriaError("observation block hash is malformed")
    if "terms" in row:
        _keys(row["terms"], {"maturity_timestamp"}, "observation terms")
        _decimal(row["terms"]["maturity_timestamp"], "observation maturity")
    return row


def _common(row):
    if not isinstance(row["id"], str) or not ROW_ID_RE.fullmatch(row["id"]):
        raise AlexandriaError("row id must be a SHA-256 identifier")
    if not isinstance(row["chain"], str) or not CHAIN_RE.fullmatch(row["chain"]):
        raise AlexandriaError("row chain must be a canonical eip155 id")
    for key in ("venue", "deployment"):
        _stable_name(row[key], f"row {key}")
    if not isinstance(row["subject"], str) or not ACCOUNT_RE.fullmatch(row["subject"]):
        raise AlexandriaError("row subject must be a lowercase CAIP-10 EVM account")
    if not row["subject"].startswith(row["chain"] + ":"):
        raise AlexandriaError("row subject must be on its declared chain")
    facility = row["facility"]
    _keys(facility, {"kind", "id"}, "row facility")
    _stable_name(facility["kind"], "facility kind")
    if not isinstance(facility["id"], str) or not facility["id"]:
        raise AlexandriaError("facility id must be non-empty")
    _validate_provenance(row["provenance"])
    if row["provenance"]["adapter"] != row["venue"]:
        raise AlexandriaError("row venue disagrees with its provenance adapter")
    if not row["provenance"]["mapping_rule"].startswith(row["venue"] + "."):
        raise AlexandriaError("row mapping rule must match its venue")


def _validate_amount(amount):
    _keys(amount, {"role", "asset", "base_units"}, "amount leg")
    _stable_name(amount["role"], "amount role")
    _decimal(amount["base_units"], "amount base_units")
    asset = amount["asset"]
    _keys(asset, {"chain", "decimals"}, "amount asset", allowed={"chain", "address", "symbol", "decimals"})
    if not isinstance(asset["chain"], str) or not CHAIN_RE.fullmatch(asset["chain"]):
        raise AlexandriaError("asset chain must be a canonical eip155 id")
    if "address" not in asset and "symbol" not in asset:
        raise AlexandriaError("asset needs an address or source symbol")
    if "address" in asset and (
        not isinstance(asset["address"], str) or not ADDRESS_RE.fullmatch(asset["address"])
    ):
        raise AlexandriaError("asset address must be lowercase")
    if "symbol" in asset and (
        not isinstance(asset["symbol"], str) or not asset["symbol"] or len(asset["symbol"]) > 32
    ):
        raise AlexandriaError("asset symbol is malformed")
    decimals = asset["decimals"]
    if isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= 255:
        raise AlexandriaError("asset decimals must be an integer from 0 to 255")


def _validate_transaction(transaction):
    allowed = {"hash", "log_index", "block_number", "block_hash", "timestamp"}
    _keys(transaction, set(), "event transaction", allowed=allowed)
    if not transaction:
        raise AlexandriaError("event transaction cannot be empty")
    if "hash" in transaction and (
        not isinstance(transaction["hash"], str) or not TX_HASH_RE.fullmatch(transaction["hash"])
    ):
        raise AlexandriaError("transaction hash is malformed")
    for key in ("log_index", "block_number", "timestamp"):
        if key in transaction:
            _decimal(transaction[key], f"transaction {key}")
    if "block_hash" in transaction and (
        not isinstance(transaction["block_hash"], str)
        or not BLOCK_HASH_RE.fullmatch(transaction["block_hash"])
    ):
        raise AlexandriaError("transaction block hash is malformed")


def _validate_provenance(value):
    required = {
        "source_release_id", "component", "component_sha256", "capture_id",
        "source_selector", "source_identity", "mapping_rule", "adapter",
        "adapter_version", "evidence_class",
    }
    _keys(value, required, "row provenance", allowed=required | {"context_selectors"})
    for key in ("source_release_id", "component_sha256"):
        if not isinstance(value[key], str) or not DIGEST_RE.fullmatch(value[key]):
            raise AlexandriaError(f"provenance {key} must be a SHA-256 identifier")
    for key in ("component", "capture_id", "adapter"):
        _stable_name(value[key], f"provenance {key}")
    _qualified(value["mapping_rule"], "mapping rule")
    if not isinstance(value["adapter_version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value["adapter_version"]):
        raise AlexandriaError("adapter version must be semantic version text")
    if (
        not isinstance(value["source_selector"], str)
        or not value["source_selector"].startswith("/")
        or len(value["source_selector"]) > 1024
    ):
        raise AlexandriaError("source selector must be an absolute JSON Pointer")
    contexts = value.get("context_selectors", [])
    if (
        not isinstance(contexts, list)
        or len(contexts) > 16
        or not all(
            isinstance(item, str) and item.startswith("/") and len(item) <= 1024
            for item in contexts
        )
        or len(contexts) != len(set(contexts))
    ):
        raise AlexandriaError("provenance context selectors must be unique absolute JSON Pointers")
    if not isinstance(value["source_identity"], str) or not value["source_identity"]:
        raise AlexandriaError("source identity must be non-empty")
    if (
        not isinstance(value["evidence_class"], str)
        or value["evidence_class"] not in EVIDENCE_CLASSES
    ):
        raise AlexandriaError("provenance evidence class is unknown")


def _keys(value, required, label, *, allowed=None):
    if not isinstance(value, dict):
        raise AlexandriaError(f"{label} must be an object")
    allowed = required if allowed is None else allowed
    missing = required - value.keys()
    unknown = value.keys() - allowed
    if missing:
        raise AlexandriaError(f"{label} is missing {sorted(missing)[0]}")
    if unknown:
        raise AlexandriaError(f"{label} contains unknown field {sorted(unknown)[0]}")


def _stable_name(value, label):
    if not isinstance(value, str) or not NAME_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be a lowercase stable name")


def _qualified(value, label):
    if not isinstance(value, str) or not ACTION_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be venue-qualified")


def _decimal(value, label):
    if not isinstance(value, str) or len(value) > MAX_INTEGER_DIGITS or not DECIMAL_RE.fullmatch(value):
        raise AlexandriaError(f"{label} must be a canonical decimal string")


def jsonl_bytes(rows, *, max_bytes=None):
    output = bytearray()
    for row in rows:
        encoded = canonical_bytes(row)
        if max_bytes is not None and len(output) + len(encoded) > max_bytes:
            raise AlexandriaError(f"derived JSONL exceeds the {max_bytes}-byte limit")
        output.extend(encoded)
    return bytes(output)
