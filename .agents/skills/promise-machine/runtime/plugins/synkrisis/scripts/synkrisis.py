#!/usr/bin/env python3
"""Checked cohort construction over validated Promise Machine run observations.

This is the runbook's Step 2 surface. `cohort` reads an operator-declared
manifest of run-observation records and one comparison policy, checks
producer identity, declared validation, redaction and binding results,
digests, caps, path form and equality dimensions, and classifies every
declared run as included, excluded or unknown with the exact policy field
responsible. The diagnose, render and verify operations stay specified and
refuse with a stable code naming the runbook step that lands each. Nothing
here calls a model, fetches a URL, executes observed content, files an
issue, edits a repository, or dispatches another skill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

PRODUCER_CONTRACT = "promise-machine-run-observation/v1"
CAPTURE_PROFILE = "promise-machine-run-observation-capture/v1"
MANIFEST_SCHEMA = "synkrisis-manifest/v1"
POLICY_SCHEMA = "synkrisis-policy/v1"
COHORT_SCHEMA = "synkrisis-cohort/v1"

MAX_RUNS = 100
MAX_EVENTS = 100_000
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_INPUT_BYTES = 64 * 1024 * 1024
MAX_LINE_BYTES = 65_536
MAX_STRING_CHARS = 4_096
MAX_PATH_CHARS = 512

EVENT_TYPES = frozenset(
    {
        "run.started",
        "run.finished",
        "capability.started",
        "capability.finished",
        "transition.refused",
        "retry.scheduled",
        "handoff.recorded",
    }
)
CONTEXT_FIELDS = (
    "issue_or_topic",
    "promise_id",
    "role",
    "selected_skill",
    "step",
)
POLICY_DIMENSIONS = tuple(f"context.{name}" for name in CONTEXT_FIELDS)
TOKEN_ACCOUNTING_MODES = frozenset({"require-equal", "ignore"})
BINDING_STATUSES = frozenset({"bound", "unavailable"})
DIGEST_RE = re.compile(r"[0-9a-f]{64}")
IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}")


class Refusal(Exception):
    """One stable finding: code, fault class, safe path, recovery."""

    def __init__(self, code, fault, path, message, recovery):
        super().__init__(message)
        self.code = code
        self.fault = fault
        self.path = path
        self.message = message
        self.recovery = recovery


@dataclass(frozen=True)
class RunRecord:
    """One declared run after manifest checks, before any event is read."""

    run_id: str
    record: str
    sha256: str
    bytes: int
    validation: dict
    redaction: dict
    binding: dict


def canonical_bytes(document) -> bytes:
    return (
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def digest_of(document) -> str:
    return hashlib.sha256(canonical_bytes(document)).hexdigest()


def shown_path(value) -> str:
    text = str(value)
    if len(text) <= MAX_PATH_CHARS:
        return text
    suffix = hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]
    return text[: MAX_PATH_CHARS - 17] + "#" + suffix


def confined_relative(raw, root: Path, *, label: str) -> Path:
    """Resolve one declared repository-relative path fail-closed.

    Absolute paths, parent traversal, symlinked components, and escapes from
    the working root all refuse before a byte is read.
    """
    if not isinstance(raw, str) or not raw or len(raw) > MAX_PATH_CHARS:
        raise Refusal(
            "SK001",
            "identity",
            label,
            "declared path is absent, empty or over the length ceiling",
            "declare one repository-relative path of at most 512 characters",
        )
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or ".." in candidate.parts or raw.startswith("~"):
        raise Refusal(
            "SK001",
            "identity",
            shown_path(raw),
            "declared path is absolute or traverses a parent directory",
            "declare the path relative to the working repository root",
        )
    target = root / candidate
    probe = root
    for part in candidate.parts:
        probe = probe / part
        if probe.is_symlink():
            raise Refusal(
                "SK001",
                "identity",
                shown_path(raw),
                "declared path crosses a symlink",
                "replace the symlinked component with a regular path",
            )
    if not target.resolve(strict=False).is_relative_to(root):
        raise Refusal(
            "SK001",
            "identity",
            shown_path(raw),
            "declared path resolves outside the working repository root",
            "declare a path confined beneath the working repository root",
        )
    return target


def bounded_read(target: Path, shown: str, cap: int) -> bytes:
    """Read one regular file through a single descriptor, capped."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(target, flags)
    except OSError:
        raise Refusal(
            "SK001",
            "identity",
            shown,
            "input is absent, unreadable or not a followable regular path",
            "restore a readable regular file at the declared path",
        ) from None
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise Refusal(
                "SK001",
                "identity",
                shown,
                "input is not a regular file",
                "declare a regular file rather than a directory or device",
            )
        if info.st_size > cap:
            raise Refusal(
                "SK002",
                "limit",
                shown,
                f"input is {info.st_size} bytes; the ceiling is {cap}",
                "shrink the input or split the declaration; raising a cap needs a study amendment",
            )
        chunks = []
        remaining = info.st_size
        while remaining > 0:
            chunk = os.read(descriptor, min(remaining, 1 << 20))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        tail = os.read(descriptor, 1)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    if tail or len(payload) != info.st_size:
        raise Refusal(
            "SK001",
            "drift",
            shown,
            "input changed size while it was being read",
            "rerun against a quiescent copy of the declared file",
        )
    return payload


def reject_duplicate_keys(pairs):
    document = dict(pairs)
    if len(document) != len(pairs):
        raise ValueError("duplicate object key")
    return document


def parse_json_document(payload: bytes, shown: str):
    try:
        return json.loads(payload, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, ValueError) as error:
        raise Refusal(
            "SK003",
            "structural",
            shown,
            f"input is not one well-formed UTF-8 JSON document: {error}",
            "repair the document encoding or structure and rerun",
        ) from None


def require_string(document, key, shown, *, pattern=None, code="SK004"):
    value = document.get(key)
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_STRING_CHARS
        or (pattern is not None and pattern.fullmatch(value) is None)
    ):
        raise Refusal(
            code,
            "structural",
            shown,
            f"field {key!r} is absent, empty, over the ceiling or malformed",
            f"provide one bounded well-formed string for {key!r}",
        )
    return value


def require_int(document, key, shown, *, minimum=0, code="SK004"):
    value = document.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise Refusal(
            code,
            "structural",
            shown,
            f"field {key!r} is absent or not an integer of at least {minimum}",
            f"provide one non-negative integer for {key!r}",
        )
    return value


def require_keys(document, required, optional, shown, *, code="SK004"):
    if not isinstance(document, dict):
        raise Refusal(
            code,
            "structural",
            shown,
            "value is not an object",
            "provide one JSON object with the documented fields",
        )
    unknown = sorted(set(document) - set(required) - set(optional))
    missing = sorted(set(required) - set(document))
    if unknown or missing:
        raise Refusal(
            code,
            "structural",
            shown,
            f"object fields diverge from the schema: missing={missing!r} unknown={unknown!r}",
            "use exactly the documented fields for this schema version",
        )


class InputBudget:
    """Aggregate ceiling over every declared byte the command reads."""

    def __init__(self):
        self.spent = 0

    def charge(self, amount, shown):
        self.spent += amount
        if self.spent > MAX_INPUT_BYTES:
            raise Refusal(
                "SK002",
                "limit",
                shown,
                f"declared inputs exceed the {MAX_INPUT_BYTES}-byte aggregate ceiling",
                "reduce the declared inputs; raising a cap needs a study amendment",
            )


def load_manifest(root: Path, raw_path: str, budget: InputBudget):
    target = confined_relative(raw_path, root, label="manifest")
    shown = shown_path(raw_path)
    payload = bounded_read(target, shown, MAX_FILE_BYTES)
    budget.charge(len(payload), shown)
    document = parse_json_document(payload, shown)
    require_keys(document, ("schema", "producer_contract", "runs"), (), shown)
    if document["schema"] != MANIFEST_SCHEMA:
        raise Refusal(
            "SK004",
            "identity",
            shown,
            "manifest schema identity is unsupported",
            f"declare schema {MANIFEST_SCHEMA!r}",
        )
    if document["producer_contract"] != PRODUCER_CONTRACT:
        raise Refusal(
            "SK008",
            "identity",
            shown,
            "manifest names an unsupported producer contract",
            f"declare producer contract {PRODUCER_CONTRACT!r} records only",
        )
    runs = document["runs"]
    if not isinstance(runs, list) or not runs:
        raise Refusal(
            "SK004",
            "structural",
            shown,
            "manifest declares no runs",
            "declare every run in the comparison universe, at least one",
        )
    if len(runs) > MAX_RUNS:
        raise Refusal(
            "SK002",
            "limit",
            shown,
            f"manifest declares {len(runs)} runs; the ceiling is {MAX_RUNS}",
            "split the universe into separate cohorts",
        )
    records = []
    seen_ids = set()
    seen_paths = set()
    for index, entry in enumerate(runs):
        entry_shown = f"{shown}#runs[{index}]"
        require_keys(
            entry,
            ("run_id", "record", "sha256", "bytes", "validation", "redaction", "binding"),
            (),
            entry_shown,
        )
        run_id = require_string(entry, "run_id", entry_shown, pattern=IDENTIFIER_RE)
        if run_id in seen_ids:
            raise Refusal(
                "SK004",
                "identity",
                entry_shown,
                "manifest declares one run id twice",
                "declare each run exactly once",
            )
        seen_ids.add(run_id)
        record = require_string(entry, "record", entry_shown)
        if record in seen_paths:
            raise Refusal(
                "SK004",
                "identity",
                entry_shown,
                "manifest declares one record path twice",
                "declare each record path exactly once",
            )
        seen_paths.add(record)
        declared_digest = require_string(entry, "sha256", entry_shown, pattern=DIGEST_RE)
        declared_bytes = require_int(entry, "bytes", entry_shown, minimum=1)
        validation = entry["validation"]
        require_keys(validation, ("tool", "status"), (), f"{entry_shown}.validation")
        require_string(validation, "tool", f"{entry_shown}.validation")
        redaction = entry["redaction"]
        require_keys(redaction, ("profile", "status"), (), f"{entry_shown}.redaction")
        if redaction["profile"] != CAPTURE_PROFILE:
            raise Refusal(
                "SK008",
                "identity",
                f"{entry_shown}.redaction",
                "redaction names an unsupported capture profile",
                f"declare capture profile {CAPTURE_PROFILE!r}",
            )
        for gate, name in ((validation, "validation"), (redaction, "redaction")):
            if gate["status"] != "accepted":
                raise Refusal(
                    "SK008",
                    "policy",
                    f"{entry_shown}.{name}",
                    f"declared {name} result is not an accepted status",
                    f"produce an accepted {name} result upstream before declaring the run",
                )
        binding = entry["binding"]
        binding_shown = f"{entry_shown}.binding"
        status = require_string(binding, "status", binding_shown, code="SK008")
        if status not in BINDING_STATUSES:
            raise Refusal(
                "SK008",
                "policy",
                binding_shown,
                "binding status is outside the supported set",
                "declare the binding as bound or unavailable with its evidence",
            )
        if status == "bound":
            require_keys(
                binding,
                ("status", "receipt", "bound_bytes", "bound_events", "sha256"),
                (),
                binding_shown,
                code="SK008",
            )
            require_string(binding, "receipt", binding_shown, code="SK008")
            require_string(binding, "sha256", binding_shown, pattern=DIGEST_RE, code="SK008")
            bound_bytes = require_int(binding, "bound_bytes", binding_shown, minimum=1, code="SK008")
            require_int(binding, "bound_events", binding_shown, minimum=1, code="SK008")
            if bound_bytes > declared_bytes:
                raise Refusal(
                    "SK009",
                    "relational",
                    binding_shown,
                    "bound prefix is longer than the declared record",
                    "restore the record bytes the receipt bound or redeclare the binding",
                )
        else:
            require_keys(binding, ("status", "reason"), (), binding_shown, code="SK008")
            require_string(binding, "reason", binding_shown, code="SK008")
        records.append(
            RunRecord(
                run_id=run_id,
                record=record,
                sha256=declared_digest,
                bytes=declared_bytes,
                validation=dict(validation),
                redaction=dict(redaction),
                binding=dict(binding),
            )
        )
    return document, records, payload


def load_policy(root: Path, raw_path: str, budget: InputBudget):
    target = confined_relative(raw_path, root, label="policy")
    shown = shown_path(raw_path)
    payload = bounded_read(target, shown, MAX_FILE_BYTES)
    budget.charge(len(payload), shown)
    document = parse_json_document(payload, shown)
    require_keys(
        document,
        ("schema", "name", "dimensions", "token_accounting"),
        (),
        shown,
        code="SK005",
    )
    if document["schema"] != POLICY_SCHEMA:
        raise Refusal(
            "SK005",
            "identity",
            shown,
            "policy schema identity is unsupported",
            f"declare schema {POLICY_SCHEMA!r}",
        )
    require_string(document, "name", shown, pattern=IDENTIFIER_RE, code="SK005")
    dimensions = document["dimensions"]
    if not isinstance(dimensions, dict) or set(dimensions) != set(POLICY_DIMENSIONS):
        raise Refusal(
            "SK005",
            "structural",
            shown,
            "policy must classify every run-context dimension exactly once",
            f"classify exactly these dimensions: {sorted(POLICY_DIMENSIONS)!r}",
        )
    for name in POLICY_DIMENSIONS:
        entry = dimensions[name]
        entry_shown = f"{shown}#dimensions.{name}"
        rule = entry.get("rule") if isinstance(entry, dict) else None
        if rule == "match":
            require_keys(entry, ("rule", "value"), (), entry_shown, code="SK005")
            require_string(entry, "value", entry_shown, code="SK005")
        elif rule == "differ":
            require_keys(entry, ("rule",), (), entry_shown, code="SK005")
        else:
            raise Refusal(
                "SK005",
                "structural",
                entry_shown,
                "dimension rule is outside the supported set",
                "declare rule match with an expected value, or rule differ",
            )
    mode = document["token_accounting"]
    if mode not in TOKEN_ACCOUNTING_MODES:
        raise Refusal(
            "SK005",
            "structural",
            shown,
            "token accounting mode is outside the supported set",
            f"declare one of {sorted(TOKEN_ACCOUNTING_MODES)!r}",
        )
    return document, payload


def parse_record_events(payload: bytes, record: RunRecord, shown: str, event_budget):
    """Stream one record's events with bounded per-line parsing.

    This is Synkrisis's own admission check, not a rerun of the producer's
    validator: it holds identity, lifecycle, order and the closed event union,
    and keeps only the compact per-run features cohort construction reads, so
    one run's raw events are in memory at a time.
    """
    if not payload.endswith(b"\n"):
        raise Refusal(
            "SK006",
            "structural",
            shown,
            "record does not end with one newline",
            "restore the exact validated record bytes",
        )
    features = {
        "context": None,
        "events": 0,
        "token_totals": {},
    }
    sequence = 0
    seen_event_ids = set()
    closed = False
    last_type = None
    for line_number, raw_line in enumerate(payload.split(b"\n")[:-1], start=1):
        if len(raw_line) > MAX_LINE_BYTES:
            raise Refusal(
                "SK002",
                "limit",
                shown,
                f"line {line_number} exceeds the {MAX_LINE_BYTES}-byte ceiling",
                "restore the validated record; raising a cap needs a study amendment",
            )
        if not raw_line:
            raise Refusal(
                "SK006",
                "structural",
                shown,
                f"line {line_number} is empty",
                "restore the exact validated record bytes",
            )
        event = parse_json_document(raw_line, f"{shown}:{line_number}")
        if not isinstance(event, dict):
            raise Refusal(
                "SK006",
                "structural",
                f"{shown}:{line_number}",
                "event line is not one JSON object",
                "restore the exact validated record bytes",
            )
        event_budget.charge(1, shown)
        if event.get("schema_id") != PRODUCER_CONTRACT:
            raise Refusal(
                "SK006",
                "identity",
                f"{shown}:{line_number}",
                "event does not carry the supported producer contract identity",
                f"declare only {PRODUCER_CONTRACT!r} records in the manifest",
            )
        if event.get("run_id") != record.run_id:
            raise Refusal(
                "SK006",
                "identity",
                f"{shown}:{line_number}",
                "event run id differs from the manifest declaration",
                "declare the record under the run id its events carry",
            )
        sequence += 1
        if event.get("sequence") != sequence:
            raise Refusal(
                "SK006",
                "relational",
                f"{shown}:{line_number}",
                "event sequence is not contiguous from one",
                "restore the exact validated record bytes",
            )
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not event_id or event_id in seen_event_ids:
            raise Refusal(
                "SK006",
                "identity",
                f"{shown}:{line_number}",
                "event id is absent or repeated",
                "restore the exact validated record bytes",
            )
        seen_event_ids.add(event_id)
        event_type = event.get("type")
        if event_type not in EVENT_TYPES:
            raise Refusal(
                "SK006",
                "structural",
                f"{shown}:{line_number}",
                "event type is outside the closed producer union",
                "restore the exact validated record bytes",
            )
        if line_number == 1 and event_type != "run.started":
            raise Refusal(
                "SK006",
                "relational",
                f"{shown}:{line_number}",
                "record does not open with run.started",
                "restore the exact validated record bytes",
            )
        if line_number > 1 and event_type == "run.started":
            raise Refusal(
                "SK006",
                "relational",
                f"{shown}:{line_number}",
                "record opens a second run",
                "restore the exact validated record bytes",
            )
        if closed:
            raise Refusal(
                "SK006",
                "relational",
                shown,
                "record closes more than once",
                "restore the exact validated record bytes",
            )
        if event_type == "run.started":
            context = event.get("context")
            if not isinstance(context, dict):
                raise Refusal(
                    "SK006",
                    "structural",
                    shown,
                    "run.started carries no opening context",
                    "restore the exact validated record bytes",
                )
            for field in CONTEXT_FIELDS:
                value = context.get(field)
                if not isinstance(value, str) or not value:
                    raise Refusal(
                        "SK006",
                        "structural",
                        shown,
                        f"opening context field {field!r} is absent or empty",
                        "restore the exact validated record bytes",
                    )
            features["context"] = {field: context[field] for field in CONTEXT_FIELDS}
        elif event_type == "run.finished":
            closed = True
        usage = event.get("token_usage")
        if isinstance(usage, dict):
            accounting = usage.get("accounting_id")
            if isinstance(accounting, str) and accounting:
                bucket = features["token_totals"].setdefault(
                    accounting, {"input_tokens": 0, "output_tokens": 0}
                )
                for key in ("input_tokens", "output_tokens"):
                    value = usage.get(key)
                    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                        bucket[key] += value
        last_type = event_type
    if last_type != "run.finished":
        raise Refusal(
            "SK006",
            "relational",
            shown,
            "record does not close with run.finished",
            "restore the exact validated record bytes",
        )
    features["events"] = sequence
    return features


def read_declared_record(root: Path, record: RunRecord, budget: InputBudget):
    target = confined_relative(record.record, root, label=f"runs.{record.run_id}.record")
    shown = shown_path(record.record)
    payload = bounded_read(target, shown, MAX_FILE_BYTES)
    budget.charge(len(payload), shown)
    if len(payload) != record.bytes:
        raise Refusal(
            "SK007",
            "drift",
            shown,
            f"record is {len(payload)} bytes; the manifest declares {record.bytes}",
            "restore the declared record bytes or redeclare the manifest row",
        )
    actual = hashlib.sha256(payload).hexdigest()
    if actual != record.sha256:
        raise Refusal(
            "SK007",
            "drift",
            shown,
            "record digest differs from the manifest declaration",
            "restore the declared record bytes or redeclare the manifest row",
        )
    if record.binding["status"] == "bound":
        bound_bytes = record.binding["bound_bytes"]
        prefix = payload[:bound_bytes]
        if hashlib.sha256(prefix).hexdigest() != record.binding["sha256"]:
            raise Refusal(
                "SK009",
                "drift",
                shown,
                "bound prefix digest does not recompute from the record bytes",
                "restore the receipt-bound prefix bytes or redeclare the binding",
            )
        if not prefix.endswith(b"\n") or prefix.count(b"\n") != record.binding["bound_events"]:
            raise Refusal(
                "SK009",
                "relational",
                shown,
                "bound prefix does not close exactly its declared event count",
                "redeclare the binding with the receipt's exact byte and event counts",
            )
    return payload


def build_cohort_document(manifest_document, manifest_records, policy, runs_by_id):
    """Classify every declared run and assemble the deterministic cohort."""
    dimensions = policy["dimensions"]
    rows = []
    included = []
    excluded = []
    unknown = []
    accounting_ids = set()
    for record in manifest_records:
        features = runs_by_id[record.run_id]
        context = features["context"]
        disposition = "included"
        reason_code = None
        policy_field = None
        if record.binding["status"] == "unavailable":
            disposition = "unknown"
            reason_code = "binding-unavailable"
        else:
            for name in POLICY_DIMENSIONS:
                rule = dimensions[name]
                value = context[name.split(".", 1)[1]]
                if rule["rule"] == "match" and value != rule["value"]:
                    disposition = "excluded"
                    reason_code = "dimension-mismatch"
                    policy_field = name
                    break
        if disposition == "included":
            accounting_ids.update(features["token_totals"])
        rows.append(
            {
                "run_id": record.run_id,
                "disposition": disposition,
                "reason_code": reason_code,
                "policy_field": policy_field,
                "record": record.record,
                "sha256": record.sha256,
                "bytes": record.bytes,
                "events": features["events"],
                "binding_status": record.binding["status"],
            }
        )
        {"included": included, "excluded": excluded, "unknown": unknown}[
            disposition
        ].append(record.run_id)
    if not included:
        raise Refusal(
            "SK010",
            "policy",
            "policy",
            "the declared policy leaves no eligible run in the cohort",
            "repair the policy expectation or the declared universe and rerun",
        )
    if policy["token_accounting"] == "require-equal" and len(accounting_ids) > 1:
        raise Refusal(
            "SK010",
            "policy",
            "policy",
            "included runs carry unlike token accounting identities",
            "declare token_accounting ignore, or compare runs with one accounting identity",
        )
    matched = {
        name: dimensions[name]["value"]
        for name in POLICY_DIMENSIONS
        if dimensions[name]["rule"] == "match"
    }
    document = {
        "schema": COHORT_SCHEMA,
        "producer_contract": PRODUCER_CONTRACT,
        "manifest_digest": digest_of(manifest_document),
        "policy_digest": digest_of(policy),
        "policy_name": policy["name"],
        "dimensions": matched,
        "token_accounting": {
            "mode": policy["token_accounting"],
            "accounting_ids": sorted(accounting_ids),
        },
        "runs": rows,
        "included": included,
        "excluded": excluded,
        "unknown": unknown,
    }
    document["cohort_digest"] = digest_of(document)
    return document


class EventBudget:
    def __init__(self):
        self.spent = 0

    def charge(self, amount, shown):
        self.spent += amount
        if self.spent > MAX_EVENTS:
            raise Refusal(
                "SK002",
                "limit",
                shown,
                f"declared records exceed the {MAX_EVENTS}-event ceiling",
                "reduce the declared universe; raising a cap needs a study amendment",
            )


def atomic_write(target: Path, payload: bytes, shown: str):
    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise Refusal(
                "SK013",
                "identity",
                shown,
                "output path exists and is not a regular file",
                "point the output at a fresh regular file path",
            )
        if target.read_bytes() == payload:
            return
        raise Refusal(
            "SK013",
            "drift",
            shown,
            "output path holds different bytes already",
            "remove the stale artefact or write the output elsewhere",
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(dir=target.parent, prefix=".synkrisis.")
    try:
        # mkstemp opens the file private to the writer; the finished artefact
        # is ordinary shared output, so give it the permissions a plain open
        # under the caller's umask would have produced.
        mask = os.umask(0)
        os.umask(mask)
        os.fchmod(descriptor, 0o666 & ~mask)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temp_name, target)
    except OSError:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise Refusal(
            "SK013",
            "structural",
            shown,
            "output could not be written atomically",
            "repair the output directory and rerun",
        ) from None


def output_path(root: Path, raw: str) -> tuple[Path, str]:
    target = confined_relative(raw, root, label="out")
    return target, shown_path(raw)


def command_cohort(root: Path, arguments):
    budget = InputBudget()
    manifest_document, records, _ = load_manifest(root, arguments.manifest, budget)
    policy, _ = load_policy(root, arguments.policy, budget)
    event_budget = EventBudget()
    events_by_run = {}
    for record in records:
        payload = read_declared_record(root, record, budget)
        events_by_run[record.run_id] = parse_record_events(
            payload, record, shown_path(record.record), event_budget
        )
    cohort = build_cohort_document(manifest_document, records, policy, events_by_run)
    target, shown = output_path(root, arguments.out)
    atomic_write(target, canonical_bytes(cohort), shown)
    return {
        "command": "cohort",
        "cohort_digest": cohort["cohort_digest"],
        "included": len(cohort["included"]),
        "excluded": len(cohort["excluded"]),
        "unknown": len(cohort["unknown"]),
        "out": arguments.out,
    }


# The specified operations still held, and the runbook step that lands each.
PENDING_STEPS = {
    "diagnose": "Step 3",
    "render": "Step 4",
    "verify": "Step 4",
}


def scaffold_refusal(operation: str) -> Refusal:
    step = PENDING_STEPS[operation]
    return Refusal(
        "SK000",
        "structural",
        operation,
        f"operation {operation!r} is specified and not yet implemented",
        f"build {step} of docs/synkrisis/runbook.md, then rerun the operation",
    )


def command_held(root: Path, arguments):
    raise scaffold_refusal(arguments.command)


def working_root() -> Path:
    root = Path.cwd()
    if root.is_symlink():
        raise Refusal(
            "SK001",
            "identity",
            shown_path(root),
            "working root is a symlink",
            "run the command from a regular repository directory",
        )
    return root.resolve()


def emit(result, as_json):
    if as_json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        pairs = " ".join(f"{key}={result[key]}" for key in sorted(result))
        print(f"clean: {pairs}")


def emit_refusal(refusal: Refusal, as_json):
    document = {
        "code": refusal.code,
        "fault": refusal.fault,
        "path": refusal.path,
        "producer": PRODUCER_CONTRACT,
        "message": refusal.message,
        "recovery": refusal.recovery,
    }
    if as_json:
        print(json.dumps(document, sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"{refusal.code} fault={refusal.fault} path={refusal.path} "
            f"producer={PRODUCER_CONTRACT}: {refusal.message}; "
            f"recovery: {refusal.recovery}"
        )


def main(argv=None):
    parser = argparse.ArgumentParser(prog="synkrisis", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    cohort_parser = subparsers.add_parser(
        "cohort", help="classify every declared run under one comparison policy"
    )
    cohort_parser.add_argument("--manifest", required=True)
    cohort_parser.add_argument("--policy", required=True)
    cohort_parser.add_argument("--out", required=True)
    cohort_parser.add_argument("--json", action="store_true")

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="specified rule-catalogue pass; held until runbook Step 3 lands",
    )
    diagnose_parser.add_argument("--cohort", required=True)
    diagnose_parser.add_argument("--rules", required=True)
    diagnose_parser.add_argument("--out", required=True)
    diagnose_parser.add_argument("--json", action="store_true")

    render_parser = subparsers.add_parser(
        "render",
        help="specified fixed-template renderer; held until runbook Step 4 lands",
    )
    render_parser.add_argument("findings")
    render_parser.add_argument("--out", required=True)
    render_parser.add_argument("--json", action="store_true")

    verify_parser = subparsers.add_parser(
        "verify",
        help="specified whole-path verifier; held until runbook Step 4 lands",
    )
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument("--policy", required=True)
    verify_parser.add_argument("--cohort", required=True)
    verify_parser.add_argument("--rules", required=True)
    verify_parser.add_argument("--findings", required=True)
    verify_parser.add_argument("--report", required=True)
    verify_parser.add_argument("--json", action="store_true")

    arguments = parser.parse_args(argv)
    handlers = {
        "cohort": command_cohort,
        "diagnose": command_held,
        "render": command_held,
        "verify": command_held,
    }
    try:
        result = handlers[arguments.command](working_root(), arguments)
    except Refusal as refusal:
        emit_refusal(refusal, arguments.json)
        return 1
    emit(result, arguments.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
