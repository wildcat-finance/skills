"""Parse closed records and preserve digest roles before authority replay."""
from __future__ import annotations

from datetime import datetime, timezone
from .canonical import (MAX_ENTRIES, MAX_TOTAL_BYTES, Refusal, canonical, decode, digest)
from .schema import HASH, SCHEMAS, PROTOCOL, validate


def time_value(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        raise Refusal("invalid-time") from None


def references(value):
    """Yield only the closed typed envelope references, in wire traversal order."""
    if type(value) is dict:
        if set(value) == {"type", "sha256"}:
            yield value
        else:
            for child in value.values():
                yield from references(child)
    elif type(value) is list:
        for child in value:
            yield from references(child)


def _times(value):
    if type(value) is dict:
        for name, child in value.items():
            if name.endswith("_at") or name in ("not_before", "not_after"):
                time_value(child)
            else:
                _times(child)
    elif type(value) is list:
        for child in value:
            _times(child)


def _copies(copies, *, artifact=None):
    if [x["role"] for x in copies] != ["primary", "recovery"]:
        raise Refusal("copy-roles")
    if copies[0]["location_id"] == copies[1]["location_id"]:
        raise Refusal("copy-location")
    for item in copies:
        if item["object_key"] != "sha256/" + item["object"]["sha256"]:
            raise Refusal("object-key")
        if artifact is not None and item["object"] != artifact:
            raise Refusal("copy-object")


def parse_record(data: bytes, *, scope=None):
    """Return a new parsed value; this alone establishes no signature or authority."""
    record = decode(data, require_canonical=True)
    if type(record) is not dict or type(record.get("type")) is not str or record["type"] not in SCHEMAS:
        raise Refusal("unsupported-record-type")
    if record.get("protocol") != PROTOCOL:
        raise Refusal("unsupported-protocol")
    validate(record, SCHEMAS[record["type"]])
    _times(record)
    if scope is not None and (record["environment"], record["service"], record["scope"]) != scope:
        raise Refusal("foreign-scope")
    if (record["sequence"] == 1) != (record["previous"] is None):
        raise Refusal("predecessor-shape")
    for reference in references(record):
        if reference["sha256"] == digest(data):
            raise Refusal("self-reference")
    if "not_before" in record:
        if not time_value(record["not_before"]) <= time_value(record["issued_at"]) < time_value(record["not_after"]):
            raise Refusal("validity-interval")
    if "expires_at" in record:
        seconds = (time_value(record["expires_at"]) - time_value(record["issued_at"])).total_seconds()
        maximum = 60 if record["type"] == "stream-permit" else 300
        if not 0 < seconds <= maximum:
            raise Refusal("expiry-interval")
    kind = record["type"]
    if kind == "authority-policy":
        locations = record["locations"]
        if [x["role"] for x in locations] != ["primary", "recovery"]:
            raise Refusal("copy-roles")
        if locations[0]["location_id"] == locations[1]["location_id"] or locations[0]["account_id"] == locations[1]["account_id"]:
            raise Refusal("storage-independence")
        fingerprints = [x["key"]["fingerprint"] for x in record["authorities"]]
        if len(set(fingerprints)) != len(fingerprints):
            raise Refusal("duplicate-authority")
        for row in record["authorities"]:
            if row["key"]["format"] != "spki-p256":
                raise Refusal("authority-key-format")
            if time_value(row["not_before"]) >= time_value(row["not_after"]):
                raise Refusal("validity-interval")
    elif kind == "run-registration":
        if record["root_authorized"] != (record["initial_parent"] is None):
            raise Refusal("root-permission")
    elif kind == "parent-link":
        if record["parents"] and record["parents"][0] not in record["prior_receipts"]:
            raise Refusal("parent-omitted")
    elif kind == "storage-copy":
        artifact = record["object"]
        if record["object_key"] != "sha256/" + artifact["sha256"]:
            raise Refusal("object-key")
        if (record["get_sha256"], record["get_length"]) != (artifact["sha256"], artifact["length"]):
            raise Refusal("copy-readback")
        if time_value(record["verified_at"]) > time_value(record["issued_at"]):
            raise Refusal("future-observation")
    elif kind == "acceptance":
        artifact = record["accepted_representation"]
        if (artifact["sha256"], artifact["length"]) != (record["identities"]["outer_sha256"], record["carrier_length"]):
            raise Refusal("representation-binding")
        _copies(record["copies"], artifact=artifact)
        if (record["transition"]["kind"] == "registered-root") != (not record["parent_acceptance_ids"]):
            raise Refusal("parent-transition")
        if record["transition"]["kind"] == "continuation" and record["transition"]["initial_base"] != record["initial_base"]:
            raise Refusal("initial-base")
    elif kind == "publication-finalization":
        _copies(record["archives"])
        _copies(record["receipts"])
        if any(x["object"]["sha256"] != record["acceptance"]["sha256"] for x in record["receipts"]):
            raise Refusal("receipt-binding")
    elif kind == "validation":
        if [x["stage"] for x in record["native_results"]] != ["inspect", "restore", "verify", "identity"]:
            raise Refusal("native-stage-order")
        if record["input_sha256"] != record["identities"]["outer_sha256"] or record["resources"]["input_bytes"] != record["carrier_length"]:
            raise Refusal("input-binding")
        if time_value(record["started_at"]) > time_value(record["ended_at"]) or time_value(record["ended_at"]) > time_value(record["issued_at"]):
            raise Refusal("observation-interval")
        required = record["coverage"]["required"]
        covered = [row["commit"] for row in record["coverage"]["verified"]]
        if not required or required != sorted(set(required)) or covered != required:
            raise Refusal("coverage-shape")
    elif kind == "authority-head":
        for key in ("policy_history", "decisions"):
            head = record[key]
            if (head["count"] == 0) != (head["tail"] is None):
                raise Refusal("head-shape")
    elif kind == "journal-entry":
        if (record["sequence"] == 1) != (record["previous_commitment"] is None):
            raise Refusal("journal-predecessor")
    elif kind in ("denial", "key-revocation"):
        if time_value(record["effective_at"]) > time_value(record["issued_at"]):
            raise Refusal("future-effective-time")
    return record


def acceptance_id(payload: bytes) -> str:
    record = parse_record(payload)
    if record["type"] != "acceptance":
        raise Refusal("acceptance-required")
    return digest(b"wildcat/checkpoint-authority/acceptance/v1\x00" + payload)


def check_reference_order(items, *, external=(), scope=None):
    """Check supplied digests/types in order; authentication remains the caller's job.

    Items are exact (envelope digest, canonical record bytes) pairs. Only a
    typed identity index survives each body, bounding retained body storage.
    """
    seen = {}
    for item in external:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise Refusal("reference-pair")
        identity, kind = item
        validate(identity, HASH)
        if type(kind) is not str or kind not in SCHEMAS or identity in seen:
            raise Refusal("external-reference")
        seen[identity] = kind
        if len(seen) > MAX_ENTRIES:
            raise Refusal("count-limit")
    total = count = 0
    for item in items:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise Refusal("reference-pair")
        identity, data = item
        validate(identity, HASH)
        if type(data) is not bytes:
            raise Refusal("invalid-bytes")
        count += 1
        total += len(data)
        if count > MAX_ENTRIES or len(seen) >= MAX_ENTRIES or total > MAX_TOTAL_BYTES:
            raise Refusal("aggregate-limit")
        record = parse_record(data, scope=scope)
        if identity in seen:
            raise Refusal("duplicate-record")
        for reference in references(record):
            if reference["sha256"] == identity:
                raise Refusal("self-reference")
            if seen.get(reference["sha256"]) != reference["type"]:
                raise Refusal("missing-or-forward-reference")
        seen[identity] = record["type"]
    return {"count": count, "bytes": total, "identities": seen}
