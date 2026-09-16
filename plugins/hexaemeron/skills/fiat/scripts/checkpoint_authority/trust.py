"""Authenticate a supplied policy/key prefix from explicit external roots.

Completeness, publication and current eligibility require the later replay gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from .canonical import MAX_ENTRIES, MAX_TOTAL_BYTES, Refusal, canonical, decode
from .records import references, time_value
from .schema import ID, SCOPE, validate
from .signatures import (MAX_ENVELOPE_BYTES, b64decode, public_key, verify_envelope,
                         verify_signature)

TRUST_TYPES = frozenset({"authority-policy", "enrollment-challenge", "key-enrollment",
    "key-rotation", "key-revocation", "run-grant", "run-registration"})
ROLE = {"authority-policy": "policy", "enrollment-challenge": "operator",
    "key-enrollment": "operator", "key-rotation": "operator", "key-revocation": "operator",
    "run-grant": "operator", "run-registration": "operator", "validation": "validator",
    "storage-copy": "copy-verifier", "parent-link": "signer", "acceptance": "signer",
    "cancellation": "signer", "publication-finalization": "signer", "denial": "operator",
    "authorized-removal": "operator", "journal-entry": "journal", "authority-head": "journal",
    "stream-permit": "journal"}


@dataclass(frozen=True)
class Bootstrap:
    """Trusted caller configuration, never extracted from an envelope."""
    environment: str
    service: str
    repository_id: int
    run_id: str
    roots: tuple[bytes, ...]

    @property
    def scope(self):
        return (self.environment, self.service, {"repository_id": self.repository_id, "run_id": self.run_id})


def proof_message(challenge):
    return b"wildcat/checkpoint-authority/enrollment-proof/v1\x00" + canonical(challenge)


@dataclass(frozen=True)
class _Retained:
    """Only state needed by later entries; not a complete verified payload."""
    projection: bytes
    envelope_sha256: str

    @property
    def record(self):
        return decode(self.projection, require_canonical=True)


def _retain(record, identity):
    kind = record["type"]
    fields = {
        "key-enrollment": ("actor_id", "key", "not_before", "not_after"),
        "key-rotation": ("actor_id", "key", "not_before", "not_after"),
        "run-grant": ("actor_id", "enrollment", "permissions", "not_before", "not_after"),
    }.get(kind, ())
    projection = record if kind == "enrollment-challenge" else {"type": kind, **{key: record[key] for key in fields}}
    return _Retained(canonical(projection), identity)


class TrustPrefix:
    """A checked prefix, with immutable verified payloads and visible prefix limits."""
    def __init__(self, bootstrap, tools):
        if not isinstance(bootstrap, Bootstrap) or bootstrap.environment not in ("test", "production") or type(bootstrap.roots) is not tuple or not bootstrap.roots or len(bootstrap.roots) > 32:
            raise Refusal("bootstrap-required", "trust")
        validate(bootstrap.service, ID)
        validate(bootstrap.scope[2], SCOPE)
        self.bootstrap, self.tools = bootstrap, dict(tools)
        self.roots = {}
        for encoded in bootstrap.roots:
            root = decode(encoded, require_canonical=True)
            if type(root) is not dict or set(root) != {"environment", "key"} or root["environment"] != bootstrap.environment:
                raise Refusal("test-production-separation", "trust")
            key = root["key"]
            public_key(key)
            if key["format"] != "spki-p256" or key["fingerprint"] in self.roots:
                raise Refusal("bootstrap-key", "trust")
            self.roots[key["fingerprint"]] = key
        self.records = {}
        self.authorities = {}
        self.policy = None
        self.tail = None
        self.count = self.total_bytes = 0
        self.last_time = None
        self.enrollments = {}
        self.revoked = set()
        self.consumed_challenges = set()

    def _peek(self, envelope):
        outer = decode(envelope, limit=MAX_ENVELOPE_BYTES)
        if type(outer) is not dict or "payload" not in outer:
            raise Refusal("envelope-fields", "trust")
        statement = decode(b64decode(outer["payload"]), require_canonical=True)
        if type(statement) is not dict or type(statement.get("predicate")) is not dict:
            raise Refusal("statement-fields", "trust")
        return statement["predicate"]

    def authenticate(self, envelope):
        """Verify one record with already trusted authority; never install carried keys."""
        record = self._peek(envelope)
        kind, issuer = record.get("type"), record.get("issuer")
        if type(issuer) is not str or type(kind) is not str:
            raise Refusal("issuer-untrusted", "trust")
        if self.policy is None:
            if kind != "authority-policy" or issuer not in self.roots:
                raise Refusal("bootstrap-required", "trust")
            key = self.roots[issuer]
        elif kind == "upload-endorsement":
            reference = record.get("enrollment")
            if type(reference) is not dict or type(reference.get("sha256")) is not str:
                raise Refusal("enrollment-required", "trust")
            enrollment = self.enrollments.get(reference["sha256"])
            if enrollment is None or reference["sha256"] in self.revoked:
                raise Refusal("enrollment-inactive", "trust")
            key = enrollment.record["key"]
        else:
            authority = self.authorities.get(issuer)
            if authority is None or ROLE.get(kind) not in authority["roles"]:
                raise Refusal("issuer-untrusted", "trust")
            instant = time_value(record.get("issued_at"))
            if not time_value(authority["not_before"]) <= instant < time_value(authority["not_after"]):
                raise Refusal("issuer-expired", "trust")
            key = authority["key"]
        verified = verify_envelope(envelope, key, self.tools, scope=self.bootstrap.scope)
        record = verified.record
        if self.policy is not None:
            if kind != "authority-policy" and record.get("policy") != {"type": "authority-policy", "sha256": self.policy.envelope_sha256}:
                raise Refusal("policy-predecessor", "trust")
        if kind == "upload-endorsement":
            self._endorsement(record)
        return verified

    def _reference(self, reference, *kinds):
        found = self.records.get(reference["sha256"])
        if found is None or found.record["type"] != reference["type"] or reference["type"] not in kinds:
            raise Refusal("trust-reference", "trust")
        return found.record

    def _active_enrollment(self, reference, actor, instant):
        enrollment = self._reference(reference, "key-enrollment", "key-rotation")
        if reference["sha256"] in self.revoked or enrollment["actor_id"] != actor:
            raise Refusal("enrollment-inactive", "trust")
        if not time_value(enrollment["not_before"]) <= instant < time_value(enrollment["not_after"]):
            raise Refusal("enrollment-expired", "trust")
        return enrollment

    def _endorsement(self, record):
        instant = time_value(record["issued_at"])
        self._active_enrollment(record["enrollment"], record["actor_id"], instant)
        grant = self._reference(record["grant"], "run-grant")
        if grant["actor_id"] != record["actor_id"] or grant["enrollment"] != record["enrollment"] or "upload" not in grant["permissions"]:
            raise Refusal("grant-scope", "trust")
        if not time_value(grant["not_before"]) <= instant < time_value(grant["not_after"]):
            raise Refusal("grant-expired", "trust")

    def append(self, envelope):
        """Append only after all structural, signature and predecessor checks pass."""
        if type(envelope) is not bytes:
            raise Refusal("invalid-bytes", "trust")
        if self.count >= MAX_ENTRIES or self.total_bytes + len(envelope) > MAX_TOTAL_BYTES:
            raise Refusal("aggregate-limit", "trust")
        verified = self.authenticate(envelope)
        record = verified.record
        kind, identity = record["type"], verified.envelope_sha256
        if kind not in TRUST_TYPES:
            raise Refusal("trust-record-type", "trust")
        previous = None if self.tail is None else {"type": self.records[self.tail].record["type"], "sha256": self.tail}
        if record["sequence"] != self.count + 1 or record["previous"] != previous:
            raise Refusal("trust-predecessor", "trust")
        if identity in self.records:
            raise Refusal("duplicate-record", "trust")
        instant = time_value(record["issued_at"])
        if self.last_time is not None and instant < self.last_time:
            raise Refusal("trust-time-order", "trust")
        for reference in references(record):
            if reference["sha256"] == identity:
                raise Refusal("self-reference", "trust")
            if reference["sha256"] not in self.records or self.records[reference["sha256"]].record["type"] != reference["type"]:
                raise Refusal("trust-reference", "trust")
        if kind == "authority-policy":
            for authority in record["authorities"]:
                public_key(authority["key"])
        elif kind in ("key-enrollment", "key-rotation"):
            public_key(record["key"])
            proof = record["proof"]
            challenge = self._reference(proof["challenge"], "enrollment-challenge")
            if proof["challenge"]["sha256"] in self.consumed_challenges:
                raise Refusal("challenge-used", "trust")
            if challenge["actor_id"] != record["actor_id"] or challenge["key"] != record["key"]:
                raise Refusal("challenge-scope", "trust")
            if not time_value(challenge["issued_at"]) <= instant < time_value(challenge["expires_at"]):
                raise Refusal("challenge-expired", "trust")
            verify_signature(proof_message(challenge), b64decode(proof["signature"], maximum=16384), record["key"], self.tools)
            if kind == "key-rotation":
                self._active_enrollment(record["replaces"], record["actor_id"], instant)
                if record["key"] == self.enrollments[record["replaces"]["sha256"]].record["key"]:
                    raise Refusal("rotation-same-key", "trust")
        elif kind in ("key-revocation", "run-grant"):
            self._active_enrollment(record["enrollment"], record["actor_id"], instant)
        # Mutations follow validation so a refused record cannot advance the prefix.
        if kind == "authority-policy":
            self.authorities = {row["key"]["fingerprint"]: row for row in record["authorities"]}
            self.policy = verified
        elif kind in ("key-enrollment", "key-rotation"):
            self.enrollments[identity] = _retain(record, identity)
            challenge_identity = record["proof"]["challenge"]["sha256"]
            self.consumed_challenges.add(challenge_identity)
            self.records[challenge_identity] = _Retained(canonical({"type": "enrollment-challenge"}), challenge_identity)
            if kind == "key-rotation":
                self.revoked.add(record["replaces"]["sha256"])
        elif kind == "key-revocation":
            self.revoked.add(record["enrollment"]["sha256"])
        self.records[identity] = _retain(record, identity)
        self.tail, self.last_time = identity, instant
        self.count += 1
        self.total_bytes += len(envelope)
        return verified


def verify_trust_prefix(envelopes, bootstrap, tools):
    result = TrustPrefix(bootstrap, tools)
    for envelope in envelopes:
        result.append(envelope)
    if result.policy is None:
        raise Refusal("bootstrap-required", "trust")
    return result
