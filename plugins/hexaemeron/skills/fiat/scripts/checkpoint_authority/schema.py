"""Authoritative closed record shapes and their JSON Schema projection."""
from __future__ import annotations

import re
from .canonical import MAX_INTEGER, Refusal

PROTOCOL = "checkpoint-authority/v1"
PREDICATE = "https://wildcat.finance/attestations/checkpoint-authority/v1"
STATEMENT = "https://in-toto.io/Statement/v1"
PROFILE = "dsse-p256-sha256-der/v1"


def obj(**fields):
    return {"type": "object", "properties": fields, "required": list(fields),
            "additionalProperties": False}


def string(pattern=None, maximum=128):
    result = {"type": "string", "minLength": 1, "maxLength": maximum}
    if pattern:
        # JSON Schema searches, while Python fullmatch does not admit the final
        # newline exception of $. This portable lookahead closes that gap.
        result["pattern"] = pattern.removesuffix("$") + r"(?![\s\S])"
    return result


def enum(*values):
    return {"enum": list(values)}


def array(item, maximum=64, minimum=0):
    return {"type": "array", "items": item, "minItems": minimum,
            "maxItems": maximum, "uniqueItems": True}


def nullable(value):
    return {"anyOf": [{"type": "null"}, value]}


ID = string(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
HASH = string(r"^[0-9a-f]{64}$", 64)
COMMIT = string(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$", 64)
TIME = string(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", 20)
UINT = {"type": "integer", "minimum": 0, "maximum": MAX_INTEGER}
POSITIVE = {"type": "integer", "minimum": 1, "maximum": MAX_INTEGER}
BOOL = {"type": "boolean"}
SCOPE = obj(repository_id=POSITIVE, run_id=ID)
IDENTITIES = obj(snapshot_id=HASH, controller_manifest_sha256=HASH, outer_sha256=HASH)
PERMISSIONS = array(enum("announce", "upload", "read_status", "read_receipt", "download"), 5, 1)
ROLES = array(enum("policy", "operator", "validator", "copy-verifier", "signer", "journal"), 6, 1)
RECORD_TYPES = (
    "authority-policy", "enrollment-challenge", "key-enrollment", "key-rotation",
    "key-revocation", "run-grant", "run-registration", "upload-endorsement",
    "validation", "storage-copy", "parent-link", "acceptance", "cancellation",
    "publication-finalization", "denial", "authorized-removal", "journal-entry",
    "authority-head", "stream-permit",
)


def ref(*types):
    return obj(type=enum(*(types or RECORD_TYPES)), sha256=HASH)


KEY = {"oneOf": [
    obj(format=enum("spki-p256"), algorithm=enum("ecdsa-p256-sha256"),
        public=string(maximum=256), fingerprint=HASH),
    obj(format=enum("ssh-ed25519"), algorithm=enum("ed25519"),
        public=string(maximum=512), fingerprint=string(r"^SHA256:[A-Za-z0-9+/]{43}$", 50)),
    obj(format=enum("ssh-p256"), algorithm=enum("ecdsa-p256-sha256"),
        public=string(maximum=512), fingerprint=string(r"^SHA256:[A-Za-z0-9+/]{43}$", 50)),
    obj(format=enum("openpgp-v4"), algorithm=enum("openpgp"),
        public=string(maximum=8192), fingerprint=string(r"^[0-9A-F]{40}$", 40)),
]}
AUTHORITY = obj(key=KEY, roles=ROLES, not_before=TIME, not_after=TIME)
ARTIFACT = obj(sha256=HASH, length=POSITIVE)
LOCATION = obj(role=enum("primary", "recovery"), location_id=ID,
               object_key=string(r"^sha256/[0-9a-f]{64}$", 71), object=ARTIFACT,
               evidence=ref("storage-copy"))
NATIVE_PIN = obj(source_commit=COMMIT, executable_sha256=HASH, profile=ID)
RELEASE_PIN = obj(source_commit=COMMIT, artifact_sha256=HASH, schema_set_sha256=HASH,
                  verifier_sha256=HASH, fixture_corpus_sha256=HASH)
POP = obj(challenge=ref("enrollment-challenge"), signature=string(maximum=16384))
TARGET = {"oneOf": [obj(kind=enum(kind), **{field: schema}) for kind, field, schema in (
    ("snapshot", "snapshot_id", HASH), ("representation", "outer_sha256", HASH),
    ("run", "run_id", ID), ("key", "enrollment", ref("key-enrollment", "key-rotation")),
)]}
TRANSITION = {"oneOf": [
    obj(kind=enum("registered-root"), registration=ref("run-registration")),
    obj(kind=enum("continuation"), parent=ref("parent-link"),
        producer_prefix_sha256=HASH, initial_base=COMMIT),
]}

_COMMON = dict(protocol=enum(PROTOCOL), environment=enum("test", "production"),
               service=ID, scope=SCOPE, type=enum(*RECORD_TYPES), sequence=POSITIVE,
               previous=nullable(ref()), issued_at=TIME, issuer={"oneOf": [HASH, string(r"^SHA256:[A-Za-z0-9+/]{43}$", 50), string(r"^[0-9A-F]{40}$", 40)]})


def record(kind, **fields):
    return obj(**(_COMMON | {"type": enum(kind)} | fields))


SCHEMAS = {
    "authority-policy": record("authority-policy", authorities=array(AUTHORITY, 32, 1),
        allowed_protocols=array(enum(PROTOCOL), 1, 1), signature_profile=enum(PROFILE),
        native=NATIVE_PIN, release=RELEASE_PIN, storage_policy_sha256=HASH,
        locations=array(obj(role=enum("primary", "recovery"), location_id=ID,
                            account_id=ID, jurisdiction=enum("EU")), 2, 2),
        max_head_age_seconds={"type": "integer", "minimum": 1, "maximum": 300}),
    "enrollment-challenge": record("enrollment-challenge", policy=ref("authority-policy"),
        actor_id=POSITIVE, key=KEY, nonce=ID, expires_at=TIME),
    "key-enrollment": record("key-enrollment", policy=ref("authority-policy"),
        actor_id=POSITIVE, key=KEY, proof=POP, not_before=TIME, not_after=TIME),
    "key-rotation": record("key-rotation", policy=ref("authority-policy"),
        actor_id=POSITIVE, key=KEY, proof=POP, replaces=ref("key-enrollment", "key-rotation"),
        not_before=TIME, not_after=TIME),
    "key-revocation": record("key-revocation", policy=ref("authority-policy"),
        actor_id=POSITIVE, enrollment=ref("key-enrollment", "key-rotation"),
        effective_at=TIME, reason=enum("compromise", "retired", "permission-removed")),
    "run-grant": record("run-grant", policy=ref("authority-policy"), actor_id=POSITIVE,
        enrollment=ref("key-enrollment", "key-rotation"), permissions=PERMISSIONS,
        not_before=TIME, not_after=TIME),
    "run-registration": record("run-registration", policy=ref("authority-policy"),
        native_anchor_sha256=HASH, initial_base=COMMIT, source=NATIVE_PIN,
        owner_id=POSITIVE, permitted_protocols=array(enum(PROTOCOL), 1, 1),
        initial_parent=nullable(ref("acceptance")), root_authorized=BOOL),
    "upload-endorsement": record("upload-endorsement", policy=ref("authority-policy"),
        actor_id=POSITIVE, enrollment=ref("key-enrollment", "key-rotation"),
        grant=ref("run-grant"), candidate_id=ID, nonce=ID, expires_at=TIME,
        identities=IDENTITIES, carrier_length=POSITIVE, parent=ref("parent-link")),
    "validation": record("validation", policy=ref("authority-policy"), candidate_id=ID,
        attempt_id=ID, lease_id=ID, identities=IDENTITIES, carrier_length=POSITIVE,
        native=NATIVE_PIN, release=RELEASE_PIN, input_sha256=HASH, output_sha256=HASH,
        started_at=TIME, ended_at=TIME,
        native_results=array(obj(stage=enum("inspect", "restore", "verify", "identity"),
            exit=enum(0), output_sha256=HASH, log_sha256=HASH), 4, 4),
        coverage=obj(required=array(COMMIT), verified=array(obj(commit=COMMIT,
            enrollment=ref("key-enrollment", "key-rotation"),
            evidence_class=enum("local-signature", "platform-signature")))),
        authorization=ref("run-grant"), parent=ref("parent-link"),
        resources=obj(input_bytes=POSITIVE, output_bytes=UINT, duration_ms=UINT, peak_rss_bytes=UINT)),
    "storage-copy": record("storage-copy", policy=ref("authority-policy"),
        role=enum("primary", "recovery"), location_id=ID, object=ARTIFACT,
        object_key=string(r"^sha256/[0-9a-f]{64}$", 71),
        operation=enum("created", "existing-matched"),
        get_sha256=HASH, get_length=POSITIVE, configuration_policy_sha256=HASH,
        verified_at=TIME),
    "parent-link": record("parent-link", policy=ref("authority-policy"),
        registration=ref("run-registration"), initial_base=COMMIT,
        parents=array(ref("acceptance"), 1), prior_receipts=array(ref("acceptance")),
        producer_prefix_sha256=HASH, native=NATIVE_PIN),
    "acceptance": record("acceptance", policy=ref("authority-policy"),
        repository_slug=string(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", 201),
        issue=POSITIVE, initial_base=COMMIT, identities=IDENTITIES, carrier_length=POSITIVE,
        accepted_representation=ARTIFACT, semantic_subject=enum("snapshot_id"),
        native=NATIVE_PIN, release=RELEASE_PIN, actor_id=POSITIVE,
        endorsement=ref("upload-endorsement"), contributor_key=KEY,
        enrollment=ref("key-enrollment", "key-rotation"),
        signing_history=array(ref("key-enrollment", "key-rotation", "key-revocation"), 64, 1),
        grant=ref("run-grant"), validation=ref("validation"),
        parent_acceptance_ids=array(HASH, 1), transition=TRANSITION,
        copies=array(LOCATION, 2, 2), signer_policy_identity=HASH),
    "cancellation": record("cancellation", policy=ref("authority-policy"),
        decision_id=HASH, candidate_id=ID, reason=enum("expired-before-authorization", "operator-cancelled")),
    "publication-finalization": record("publication-finalization", policy=ref("authority-policy"),
        acceptance_id=HASH, acceptance=ref("acceptance"),
        authorization_head=ref("authority-head"), archives=array(LOCATION, 2, 2),
        receipts=array(LOCATION, 2, 2)),
    "denial": record("denial", policy=ref("authority-policy"), target=TARGET,
        reason=enum("compromise", "invalid-evidence", "operator-revoked", "poisoned-ancestor"),
        descendants=enum("poison", "none"), effective_at=TIME,
        policy_head=ref("authority-head")),
    "authorized-removal": record("authorized-removal", policy=ref("authority-policy"),
        denial=ref("denial"), removed=array(ARTIFACT, 64, 1), incident_sha256=HASH,
        operator_approvals=array(HASH, 2, 2), outcome=enum("removed")),
    "journal-entry": record("journal-entry", policy=ref("authority-policy"),
        stream=enum("policy", "decisions"), event=ref(),
        decision_id=nullable(HASH), payload_sha256=HASH, previous_commitment=nullable(HASH)),
    "authority-head": record("authority-head", policy=ref("authority-policy"),
        policy_history=obj(count=UINT, tail=nullable(HASH)),
        decisions=obj(count=UINT, tail=nullable(HASH)), challenge=ID, expires_at=TIME),
    "stream-permit": record("stream-permit", policy=ref("authority-policy"),
        actor_id=POSITIVE, session_id=ID, nonce=ID, expires_at=TIME,
        outer_sha256=HASH, receipt_sha256=HASH, acceptance_id=HASH,
        finalization=ref("publication-finalization"), head=ref("authority-head"),
        grant=ref("run-grant")),
}


def validate(value, schema):
    """Validate the fixed schema dialect; unknown schema keywords are not input."""
    if "oneOf" in schema or "anyOf" in schema:
        key = "oneOf" if "oneOf" in schema else "anyOf"
        successes = 0
        for branch in schema[key]:
            try:
                validate(value, branch)
                successes += 1
            except Refusal:
                pass
        if successes != 1:
            raise Refusal("schema-variant")
        return
    if "enum" in schema:
        if not any(type(value) is type(item) and value == item for item in schema["enum"]):
            raise Refusal("schema-enum")
        return
    kind = schema["type"]
    expected = {"object": dict, "array": list, "string": str, "integer": int,
                "boolean": bool, "null": type(None)}[kind]
    if type(value) is not expected:
        raise Refusal("schema-type")
    if kind == "object":
        if set(value) != set(schema["required"]):
            raise Refusal("schema-fields")
        for key, child in value.items():
            validate(child, schema["properties"][key])
    elif kind == "array":
        if not schema["minItems"] <= len(value) <= schema["maxItems"]:
            raise Refusal("schema-count")
        for index, item in enumerate(value):
            if item in value[:index]:
                raise Refusal("schema-duplicate")
            validate(item, schema["items"])
    elif kind == "string":
        if not schema["minLength"] <= len(value) <= schema["maxLength"]:
            raise Refusal("schema-length")
        if "pattern" in schema and re.fullmatch(schema["pattern"], value, re.ASCII) is None:
            raise Refusal("schema-pattern")
    elif kind == "integer" and not schema["minimum"] <= value <= schema["maximum"]:
        raise Refusal("schema-integer")


def document(kind):
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": PREDICATE + "/" + kind, **SCHEMAS[kind]}


def family_document():
    """One closed `oneOf` over every record type, for release copies such as Ariadne's."""
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": PREDICATE,
            "description": "Closed checkpoint authority records for " + PREDICATE
                           + "; `type` selects exactly one record shape.",
            "oneOf": [SCHEMAS[kind] for kind in RECORD_TYPES]}
