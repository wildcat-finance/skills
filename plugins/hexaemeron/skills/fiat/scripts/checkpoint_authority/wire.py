"""Closed private discovery and exact-object wire shapes; no HTTP server or bearer issuer."""
from __future__ import annotations

from .canonical import Refusal, canonical, decode
from .records import time_value
from .schema import (HASH, ID, IDENTITIES, POSITIVE, SCOPE, TIME, array, enum,
                     nullable, obj, ref, string, validate)

INVENTORY_BYTES = 256 * 1024
RESULTS = {"historical": ("valid",),
           "publication": ("complete", "incomplete", "authorized-absence", "unexplained-absence"),
           "current_eligibility": ("eligible", "denied", "unavailable", "unknown")}
ACCEPTED = obj(acceptance_id=HASH, identities=IDENTITIES, receipt_sha256=HASH,
               finalization_sha256=HASH)
COMMON = dict(protocol=enum("checkpoint-authority/v1"), environment=enum("test", "production"),
              service=ID, scope=SCOPE, request_id=ID)
SCHEMAS = {
    "lookup": obj(**COMMON, record=ACCEPTED, head=ref("authority-head")),
    "inventory": obj(**COMMON, inventory_sha256=HASH, cursor=nullable(ID),
        next_cursor=nullable(ID), head=ref("authority-head"), items=array(ACCEPTED, 100)),
    "status": obj(**COMMON, acceptance_id=HASH, state=enum("eligible", "denied", "unavailable"),
        head=ref("authority-head"), code=enum("eligible", "denied", "publication-incomplete", "freshness-unavailable")),
    "download-grant": obj(**COMMON, grant_id=ID, actor_id=POSITIVE, session_id=ID,
        acceptance_id=HASH, outer_sha256=HASH, receipt_sha256=HASH,
        issued_at=TIME, expires_at=TIME, head=ref("authority-head")),
    "unavailable": obj(request_id=ID, state=enum("unavailable"), code=enum("resource_unavailable")),
    "disabled": obj(request_id=ID, state=enum("unavailable"), code=enum("capability_not_enabled")),
}


def parse(kind, data):
    if type(kind) is not str or kind not in SCHEMAS:
        raise Refusal("wire-type", "wire")
    value = decode(data, require_canonical=True, limit=INVENTORY_BYTES if kind == "inventory" else 65536)
    validate(value, SCHEMAS[kind])
    if kind == "inventory":
        ids = [item["acceptance_id"] for item in value["items"]]
        if ids != sorted(set(ids)) or (value["next_cursor"] is not None and value["cursor"] == value["next_cursor"]):
            raise Refusal("inventory-order", "wire")
    if kind == "status" and ((value["state"] == "eligible") != (value["code"] == "eligible")
        or (value["state"] == "denied") != (value["code"] == "denied")):
        raise Refusal("status-binding", "wire")
    if kind == "download-grant":
        duration = (time_value(value["expires_at"])-time_value(value["issued_at"])).total_seconds()
        if not 0 < duration <= 60:
            raise Refusal("grant-expiry", "wire")
    return value


def unavailable(request_id, *, authorized=False, exists=False):
    """Public absence reveals neither existence nor authorization."""
    validate(request_id, ID)
    return canonical({"request_id": request_id, "state": "unavailable", "code": "resource_unavailable"})


def capability(name, request_id):
    if name not in ("frontier", "resolution", "public-discovery"):
        raise Refusal("capability-name", "wire")
    validate(request_id, ID)
    return 501, canonical({"request_id": request_id, "state": "unavailable", "code": "capability_not_enabled"})


def binary_headers(outer_sha256):
    validate(outer_sha256, HASH)
    return {"Cache-Control": "private, no-store", "Content-Type": "application/octet-stream",
            "Content-Disposition": 'attachment; filename="' + outer_sha256 + '.zip"'}
