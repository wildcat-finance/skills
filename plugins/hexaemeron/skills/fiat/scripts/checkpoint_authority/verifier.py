"""Bounded public verification: explicit trust, declared native results, one closed result.

The caller supplies every input. Nothing here follows a locator carried in a
record, fetches, signs, or chooses a tool: the only subprocesses are the
caller-pinned public-key verifiers that `signatures` already confines.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from . import native_io as io
from .canonical import MAX_DEPTH, MAX_ENTRIES, MAX_RECORD_BYTES, MAX_TOTAL_BYTES, Refusal, decode, digest
from .eligibility import Freshness
from .native import NativeResult
from .records import time_value
from .replay import Replay
from .schema import HASH, ID, POSITIVE, UINT, enum, nullable, obj, string, validate
from .signatures import MAX_ENVELOPE_BYTES, ToolPin, b64decode
from .trust import Bootstrap

SCHEMA = "checkpoint-authority-verification/v1"
STAGE = "verifier"
TOOL_NAMES = ("openssl", "ssh-keygen", "gpg")
LIMITS = {
    "record_bytes": MAX_RECORD_BYTES, "envelope_bytes": MAX_ENVELOPE_BYTES, "json_depth": MAX_DEPTH,
    "history_entries": MAX_ENTRIES, "history_bytes": MAX_TOTAL_BYTES,
    "history_file_bytes": MAX_TOTAL_BYTES + MAX_ENTRIES,
    "bootstrap_file_bytes": 65536, "bootstrap_roots": 32, "root_bytes": 16384,
    "tools_file_bytes": 16384, "freshness_file_bytes": 4096,
    "native_file_bytes": 67108864, "native_results": 4096, "native_result_bytes": io.STDOUT_MAX,
    "producer_ledger_bytes": 16777216, "producer_ledger_entries": 100000,
    "presence_file_bytes": 67108864, "presence_rows": 2 * MAX_ENTRIES,
    "output_bytes": 4194304, "tool_timeout_seconds": 10,
    "tool_stdout_bytes": 65536, "tool_stderr_bytes": 16384,
}
BOOTSTRAP = obj(schema=enum("checkpoint-authority-bootstrap/v1"), environment=enum("test", "production"),
                service=ID, repository_id=POSITIVE, run_id=ID,
                roots={"type": "array", "items": string(maximum=21848), "minItems": 1,
                       "maxItems": LIMITS["bootstrap_roots"], "uniqueItems": True})
TOOL = obj(path=string(maximum=4096), sha256=HASH)
FRESHNESS = obj(schema=enum("checkpoint-authority-freshness/v1"), challenge=ID,
                now=string(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", 20),
                policy_count=UINT, policy_tail=nullable(HASH), decision_count=UINT, decision_tail=nullable(HASH))
NATIVE_ROW = obj(output_sha256=HASH, result=string(maximum=87384), producer=string(maximum=22369624))
PRESENCE_ROW = obj(sha256=HASH, role=enum("primary", "recovery"), present={"type": "boolean"})


def _json(data, *, limit):
    """Decode one caller file with the protocol parser; the cap is the caller's file limit."""
    return decode(data, limit=limit)


def _rows(value, schema_id, key, item, maximum):
    """Validate a row list one item at a time; duplicates are caught by the consuming table."""
    if type(value) is not dict or set(value) != {"schema", key} or value["schema"] != schema_id:
        raise Refusal(key + "-shape", STAGE)
    rows = value[key]
    if type(rows) is not list or len(rows) > maximum:
        raise Refusal(key + "-limit", STAGE)
    for row in rows:
        validate(row, item)
    return rows


def bootstrap_from(data: bytes) -> Bootstrap:
    """Explicit trust: environment, service, scope and external roots, never a carried key."""
    value = _json(data, limit=LIMITS["bootstrap_file_bytes"])
    validate(value, BOOTSTRAP)
    roots = tuple(b64decode(root, maximum=LIMITS["root_bytes"]) for root in value["roots"])
    return Bootstrap(value["environment"], value["service"], value["repository_id"], value["run_id"], roots)


def tools_from(data: bytes) -> dict:
    """Caller-pinned absolute executables; a record can never select one."""
    value = _json(data, limit=LIMITS["tools_file_bytes"])
    if (type(value) is not dict or value.get("schema") != "checkpoint-authority-tools/v1"
        or set(value) != {"schema", "tools"} or type(value["tools"]) is not dict
        or "openssl" not in value["tools"] or not set(value["tools"]) <= set(TOOL_NAMES)):
        raise Refusal("tools-shape", STAGE)
    pins = {}
    for name in TOOL_NAMES:
        if name in value["tools"]:
            validate(value["tools"][name], TOOL)
            pin = ToolPin(name, value["tools"][name]["path"], value["tools"][name]["sha256"])
            pin.check()
            pins[name] = pin
    return pins


def freshness_from(data: bytes) -> Freshness:
    """Values the caller obtained on an authenticated channel; the journal never supplies them."""
    value = _json(data, limit=LIMITS["freshness_file_bytes"])
    validate(value, FRESHNESS)
    freshness = Freshness(value["challenge"], time_value(value["now"]), value["policy_count"],
                          value["policy_tail"], value["decision_count"], value["decision_tail"])
    freshness.check()
    return freshness


def native_from(data: bytes) -> dict:
    """Declared native results keyed by the exact output digest each validation names."""
    value = _json(data, limit=LIMITS["native_file_bytes"])
    rows = _rows(value, "checkpoint-authority-native-evidence/v1", "results", NATIVE_ROW, LIMITS["native_results"])
    return native_table((row["output_sha256"], b64decode(row["result"], maximum=LIMITS["native_result_bytes"]),
                         b64decode(row["producer"], maximum=LIMITS["producer_ledger_bytes"]))
                        for row in rows)


def native_table(rows) -> dict:
    """Bind each declared result to its digest; the table is a lookup, never a locator."""
    table = {}
    for row in rows:
        if type(row) not in (tuple, list) or len(row) != 3:
            raise Refusal("native-evidence-shape", STAGE)
        output_sha256, payload, producer = row
        validate(output_sha256, HASH)
        if type(payload) is not bytes or type(producer) is not bytes:
            raise Refusal("native-evidence-shape", STAGE)
        if len(payload) > LIMITS["native_result_bytes"] or len(producer) > LIMITS["producer_ledger_bytes"]:
            raise Refusal("native-evidence-limit", STAGE)
        if digest(payload) != output_sha256:
            raise Refusal("native-evidence-binding", STAGE)
        if output_sha256 in table:
            raise Refusal("native-evidence-duplicate", STAGE)
        if len(table) >= LIMITS["native_results"]:
            raise Refusal("native-evidence-limit", STAGE)
        table[output_sha256] = (NativeResult(payload, Path("/caller-declared-native-evidence")), producer)
    return table


def presence_from(data: bytes) -> dict:
    """The caller's own scoped GET/hash observations; absent rows stay unknown."""
    value = _json(data, limit=LIMITS["presence_file_bytes"])
    rows = _rows(value, "checkpoint-authority-presence/v1", "observations", PRESENCE_ROW, LIMITS["presence_rows"])
    presence = {}
    for row in rows:
        key = (row["sha256"], row["role"])
        if key in presence:
            raise Refusal("presence-duplicate", STAGE)
        presence[key] = row["present"]
    return presence


class History:
    """Stream one caller-selected JSON Lines file, one envelope per line, without following links."""

    def __init__(self, path):
        self.path = Path(path)
        self.count = self.bytes = 0
        self.sha256 = None

    def __iter__(self):
        hasher = hashlib.sha256()
        with io.regular(self.path, LIMITS["history_file_bytes"]) as (descriptor, size, check):
            pending = b""
            seen = 0
            while True:
                chunk = os.read(descriptor, 1048576)
                if not chunk:
                    break
                seen += len(chunk)
                if seen > size:
                    raise Refusal("history-changed", STAGE)
                hasher.update(chunk)
                pending += chunk
                lines = pending.split(b"\n")
                pending = lines.pop()
                for line in lines:
                    yield self._line(line)
                if len(pending) > MAX_ENVELOPE_BYTES:
                    raise Refusal("envelope-limit", STAGE)
            if seen != size or pending:
                raise Refusal("history-transport", STAGE)
            check()
        self.sha256 = hasher.hexdigest()

    def _line(self, line):
        if not line or len(line) > MAX_ENVELOPE_BYTES:
            raise Refusal("envelope-limit", STAGE)
        if self.count >= MAX_ENTRIES or self.bytes + len(line) > MAX_TOTAL_BYTES:
            raise Refusal("aggregate-limit", STAGE)
        self.count += 1
        self.bytes += len(line)
        return line


def verify(envelopes, bootstrap, tools, *, native, freshness=None, presence=None):
    """Replay bounded envelopes from explicit roots; return the closed result or refuse.

    `native` maps each validation's `output_sha256` to its declared
    `(NativeResult, producer ledger bytes)`. Without `freshness`, every
    accepted row keeps `current_eligibility: unknown`; without `presence`, a
    complete publication is `unavailable`. Neither is ever inferred.
    """
    if not isinstance(bootstrap, Bootstrap):
        raise Refusal("bootstrap-required", STAGE)
    if type(tools) is not dict or "openssl" not in tools or any(
            name not in TOOL_NAMES or not isinstance(pin, ToolPin) for name, pin in tools.items()):
        raise Refusal("tools-shape", STAGE)
    if type(native) is not dict:
        raise Refusal("native-evidence-shape", STAGE)
    reader = Replay(bootstrap, tools, native_evidence=native.__getitem__, freshness=freshness)
    for envelope in envelopes:
        reader.append(envelope)
    result = reader.finish(presence=presence)
    summary = {state: 0 for state in ("eligible", "denied", "unavailable", "unknown")}
    for row in result["accepted"]:
        summary[row["current_eligibility"]] += 1
    return {"schema": SCHEMA, "event": "checkpoint_authority_verified", "stage": "replay",
            "code": "complete-head", "complete": True, "historical": "valid",
            "freshness_supplied": freshness is not None, "presence_supplied": presence is not None,
            "current_eligibility_established": freshness is not None,
            "eligibility_summary": summary, "result": result, "limits": LIMITS}


def refusal(error, *, stage=None, code=None):
    """One closed refusal event; no input value or child diagnostic leaves the process."""
    if isinstance(error, Refusal):
        stage, code = error.stage, error.code
    return {"schema": SCHEMA, "event": "checkpoint_authority_refused", "stage": stage or STAGE,
            "code": code or "unsafe-or-unavailable-file", "complete": False, "historical": None,
            "current_eligibility_established": False}
