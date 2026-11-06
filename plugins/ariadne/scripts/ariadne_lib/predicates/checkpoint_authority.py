"""Bind closed checkpoint authority records without signature or live-authority claims.

The local schema is a release copy of the owner's nineteen closed record
shapes. A checkout parity test compares the parsed copy with the owner's
projection, and the authority-replay manifest binds the copy's bytes by
digest; an isolated Ariadne install imports no sibling plugin and reads only
this directory. Every check here is a fact about one record's own bytes and the
statement around it. Signatures, native execution, storage observations,
complete journal replay and current eligibility stay outside this predicate
and are reported unchecked.
"""
import datetime
import hashlib
import json
from pathlib import Path
import re

from ..gates import Gate

TYPE = "https://wildcat.finance/attestations/checkpoint-authority/v1"
SUMMARY = "checkpoint authority records: explicit identities and typed evidence"
CORE_BLOCKS = "checkpoint-authority-record/v1"
EXPECTED_RESULTS = (
    (2, "environment"),
    (5, "comparison"),
    (None, "predicate-fields"),
    (None, "subject-roles"),
    (None, "evidence-references"),
    (None, "required-coverage"),
)
UNCHECKED = (
    "checkpoint signatures and issuer authority were not authenticated by Ariadne",
    "native execution, storage observations and complete journal replay were not checked by Ariadne",
    "current eligibility, object availability and gateway cancellation remain unknown to Ariadne",
)
RESULTS = {
    "historical": ("valid",),
    "publication": ("complete", "incomplete", "authorized-absence", "unexplained-absence"),
    "current_eligibility": ("eligible", "denied", "unavailable", "unknown"),
}
"""The owner's closed replay result vocabulary, copied for parity tests.

Ariadne never produces one of these values. A replay result is established by
the authority verifier; this table lets a reader check that a carried result
uses the vocabulary and nothing outside it.
"""
IDENTITY_ROLES = ("snapshot_id", "controller_manifest_sha256", "outer_sha256")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
MAX_RECORD_BYTES = 65536
SCHEMA_PATH = Path(__file__).resolve().parents[3] / "schemas" / "checkpoint-authority-v1.json"
SCHEMA = json.loads(SCHEMA_PATH.read_bytes())
RECORDS = {row["properties"]["type"]["enum"][0]: row for row in SCHEMA["oneOf"]}
PREDICATE_FIELDS = tuple(sorted({key for row in SCHEMA["oneOf"] for key in row["properties"]}))
"""Every top-level field any of the nineteen record types carries."""


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode()


def valid(value, shape):
    """The owner's fixed schema dialect: closed objects, exact scalar types."""
    if "oneOf" in shape or "anyOf" in shape:
        return sum(valid(value, child) for child in shape.get("oneOf", shape.get("anyOf", ()))) == 1
    if "enum" in shape:
        return any(type(value) is type(item) and value == item for item in shape["enum"])
    kind = shape["type"]
    expected = {"object": dict, "array": list, "string": str, "integer": int,
                "boolean": bool, "null": type(None)}[kind]
    if type(value) is not expected:
        return False
    if kind == "object":
        return set(value) == set(shape["required"]) and all(
            valid(value[key], child) for key, child in shape["properties"].items()
        )
    if kind == "array":
        return shape["minItems"] <= len(value) <= shape["maxItems"] and all(
            item not in value[:i] and valid(item, shape["items"]) for i, item in enumerate(value)
        )
    if kind == "string":
        return shape["minLength"] <= len(value) <= shape["maxLength"] and (
            "pattern" not in shape or re.fullmatch(shape["pattern"], value, re.ASCII) is not None
        )
    if kind == "integer":
        return shape["minimum"] <= value <= shape["maximum"]
    return True


def shaped(value):
    """Whether the body is one closed record type within the byte cap."""
    kind = value.get("type") if type(value) is dict else None
    if type(kind) is not str or kind not in RECORDS or not valid(value, RECORDS[kind]):
        return False
    return len(canonical(value)) <= MAX_RECORD_BYTES


def authorship_projection(value):
    """Rename closed external-evidence fields before the core authorship scan.

    `signer_policy_identity`, `verifier_sha256`, `verified` and `verified_at`
    name evidence that external verifiers produced and that this predicate
    reports unchecked; they are not the payload vouching for itself. Only a
    record that is already shaped is projected, so an invalid record keeps
    every original key for the generic scan.
    """
    if not shaped(value):
        return value
    names = {"signer_policy_identity": "policy_digest", "verifier_sha256": "tool_digest",
             "verified": "coverage_evidence", "verified_at": "observation_time"}

    def project(node):
        if type(node) is dict:
            return {names.get(key, key): project(child) for key, child in node.items()}
        if type(node) is list:
            return [project(child) for child in node]
        return node

    return project(value)


def refs(value):
    """Every typed `{type, sha256}` evidence reference, in wire order."""
    if type(value) is dict:
        if set(value) == {"type", "sha256"}:
            yield value
        else:
            for child in value.values():
                yield from refs(child)
    elif type(value) is list:
        for child in value:
            yield from refs(child)


def instant(value):
    try:
        return datetime.datetime.strptime(value, TIME_FORMAT).replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def times_recoverable(value):
    """Every timestamp names a real UTC instant and sits inside its interval.

    The published pattern admits `2026-02-30T00:00:00Z`; a record dated at no
    instant cannot be placed in the policy or key history it claims to belong
    to. Interval rules mirror the owner's record-local joins.
    """
    def walk(node):
        if type(node) is dict:
            for name, child in node.items():
                if name.endswith("_at") or name in ("not_before", "not_after"):
                    if instant(child) is None:
                        return False
                elif not walk(child):
                    return False
        elif type(node) is list:
            return all(walk(child) for child in node)
        return True

    if not walk(value):
        return False
    issued = instant(value["issued_at"])
    if "not_before" in value and not (
        instant(value["not_before"]) <= issued < instant(value["not_after"])
    ):
        return False
    if "expires_at" in value:
        seconds = (instant(value["expires_at"]) - issued).total_seconds()
        if not 0 < seconds <= (60 if value["type"] == "stream-permit" else 300):
            return False
    if value["type"] == "authority-policy" and any(
        instant(row["not_before"]) >= instant(row["not_after"]) for row in value["authorities"]
    ):
        return False
    if value["type"] == "storage-copy" and instant(value["verified_at"]) > issued:
        return False
    if value["type"] == "validation" and not (
        instant(value["started_at"]) <= instant(value["ended_at"]) <= issued
    ):
        return False
    if value["type"] in ("denial", "key-revocation") and instant(value["effective_at"]) > issued:
        return False
    return True


def both_sides_named(value):
    """Predecessor, parent and head relations name both of their sides."""
    kind = value["type"]
    ok = (value["sequence"] == 1) == (value["previous"] is None)
    if kind == "acceptance":
        transition = value["transition"]
        ok &= (transition["kind"] == "registered-root") == (not value["parent_acceptance_ids"])
        if transition["kind"] == "continuation":
            ok &= transition["initial_base"] == value["initial_base"]
    elif kind == "parent-link":
        ok &= not value["parents"] or value["parents"][0] in value["prior_receipts"]
    elif kind == "run-registration":
        ok &= value["root_authorized"] == (value["initial_parent"] is None)
    elif kind == "journal-entry":
        ok &= (value["sequence"] == 1) == (value["previous_commitment"] is None)
    elif kind == "authority-head":
        ok &= all(
            (value[field]["count"] == 0) == (value[field]["tail"] is None)
            for field in ("policy_history", "decisions")
        )
    return bool(ok)


def coverage_complete(value):
    """Copy, representation and coverage inventories are complete and bound."""
    kind = value["type"]

    def copies(rows, artifact=None):
        return (
            [row["role"] for row in rows] == ["primary", "recovery"]
            and rows[0]["location_id"] != rows[1]["location_id"]
            and all(row["object_key"] == "sha256/" + row["object"]["sha256"] for row in rows)
            and (artifact is None or all(row["object"] == artifact for row in rows))
        )

    if kind == "acceptance":
        artifact = value["accepted_representation"]
        return (
            artifact == {"sha256": value["identities"]["outer_sha256"], "length": value["carrier_length"]}
            and copies(value["copies"], artifact)
        )
    if kind == "validation":
        required = value["coverage"]["required"]
        return (
            bool(required)
            and required == sorted(set(required))
            and [row["commit"] for row in value["coverage"]["verified"]] == required
            and [row["stage"] for row in value["native_results"]] == ["inspect", "restore", "verify", "identity"]
            and value["input_sha256"] == value["identities"]["outer_sha256"]
            and value["resources"]["input_bytes"] == value["carrier_length"]
        )
    if kind == "publication-finalization":
        return (
            copies(value["archives"])
            and copies(value["receipts"])
            and all(row["object"]["sha256"] == value["acceptance"]["sha256"] for row in value["receipts"])
        )
    if kind == "storage-copy":
        artifact = value["object"]
        return (
            value["object_key"] == "sha256/" + artifact["sha256"]
            and (value["get_sha256"], value["get_length"]) == (artifact["sha256"], artifact["length"])
        )
    if kind == "authority-policy":
        locations = value["locations"]
        fingerprints = [row["key"]["fingerprint"] for row in value["authorities"]]
        return (
            [row["role"] for row in locations] == ["primary", "recovery"]
            and locations[0]["location_id"] != locations[1]["location_id"]
            and locations[0]["account_id"] != locations[1]["account_id"]
            and len(set(fingerprints)) == len(fingerprints)
            and all(row["key"]["format"] == "spki-p256" for row in value["authorities"])
        )
    return True


def references_distinct(value, encoded):
    """No typed evidence reference reuses this record's digest or an identity digest.

    The statement gives each digest one explicit role. A validation reference
    that names the snapshot digest, or a record that names its own bytes, is
    the role substitution the owner refuses.
    """
    reserved = {hashlib.sha256(encoded).hexdigest()}
    if "identities" in value:
        reserved.update(value["identities"][role] for role in IDENTITY_ROLES)
    return all(row["sha256"] not in reserved for row in refs(value))


def expected_subjects(value, encoded):
    if "identities" in value:
        return [{"name": role, "digest": {"sha256": value["identities"][role]}} for role in IDENTITY_ROLES]
    return [{"name": "record", "digest": {"sha256": hashlib.sha256(encoded).hexdigest()}}]


DETAILS = {
    "environment": ("every timestamp is a UTC instant inside its declared interval",
                    "a timestamp names no UTC instant or falls outside its declared interval"),
    "comparison": ("predecessor, parent and head relations name both sides",
                   "a predecessor, parent or head relation leaves one side unnamed"),
    "predicate-fields": ("closed record within the byte cap",
                         "closed checkpoint record required"),
    "subject-roles": ("subjects carry the record's explicit digest roles",
                      "subjects do not carry the record's explicit digest roles"),
    "evidence-references": ("typed evidence references reuse no identity or self digest",
                            "a typed evidence reference reuses an identity or self digest"),
    "required-coverage": ("copy, representation and coverage inventories are complete and bound",
                          "a copy, representation or coverage inventory is incomplete or unbound"),
}


def check(statement):
    value = statement.predicate
    if not shaped(value):
        return [Gate(number, name, False, DETAILS["predicate-fields"][1])
                for number, name in EXPECTED_RESULTS]
    encoded = canonical(value)
    subjects = [subject.to_dict() for subject in statement.subjects]
    answers = {
        "environment": times_recoverable(value),
        "comparison": both_sides_named(value),
        "predicate-fields": True,
        "subject-roles": subjects == expected_subjects(value, encoded),
        "evidence-references": references_distinct(value, encoded),
        "required-coverage": coverage_complete(value),
    }
    return [
        Gate(number, name, answers[name], DETAILS[name][0 if answers[name] else 1])
        for number, name in EXPECTED_RESULTS
    ]
