#!/usr/bin/env python3
"""Check inert audit obligations against their original bytes and owned routes.

A000 is an input/read refusal; A001 a fence; A002 JSON/schema; A003 the
inventory; A004 source equality; A005 row shape; A006 source/span/status;
A007 regression routing; A008 criterion routing; A009 final input stability.
Codes and numeric row locations expose no source content. No command runs and
no controller or report file is written by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

SCHEMA = "protasis-audit-applicability/v1"
CAPTURE_SCHEMA = "protasis-audit-applicability-capture/v1"
MAX_DOCUMENT_BYTES = 256 * 1024
MAX_SOURCE_VIEWS = 32
MAX_ENTRIES = 128
MAX_TEXT_BYTES = 4096
MAX_STATUS_BYTES = 1024
MAX_TRACKING = 8
MAX_SPAN_BYTES = 64 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_AGGREGATE_BYTES = 16 * 1024 * 1024
FENCE_INFO = "audit-applicability"
FIELDS = frozenset({"schema", "source_views", "entries"})
ENTRY_FIELDS = frozenset({"id", "source_ref", "source_span", "source_status",
                          "disposition", "rationale", "finding_id", "criterion_id", "tracking"})
SPAN_FIELDS = frozenset({"start_byte", "end_byte", "sha256"})
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ISSUE = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*\Z")
FENCE = re.compile(r"(?P<mark>`{3,}|~{3,})(?P<info>[^\r\n]*)\Z")
SURROUNDING_FENCE = re.compile(r" {0,3}(?P<mark>`{3,}|~{3,})(?P<info>[^\r\n]*)\Z")
ATTEMPT = re.compile(r"^\s*(?:>[ \t]*)?(?:[-+*][ \t]+|[0-9]+\.[ \t]+)?"
                     r"[`~]{2,}[ \t]*audit-applicability", re.I)


def _module(name):
    key = "_audit_applicability_" + name
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(key, Path(__file__).with_name(name + ".py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[key] = module
        spec.loader.exec_module(module)
    return sys.modules[key]


inventory = _module("known_failure_inventory")
criteria = _module("success_criteria")


def canonical_bytes(value) -> bytes:
    """Return sorted ASCII JSON and one LF, the applicability digest encoding."""
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class Finding:
    code: str
    field: str
    row: int | None = None

    def as_dict(self):
        return {"code": self.code, "field": self.field, "row": self.row}


@dataclass(frozen=True, slots=True)
class ApplicabilityLoadResult:
    """Immutable result; capture returns a fresh JSON projection on each access."""
    status: str
    capture_bytes: bytes | None
    findings: tuple[Finding, ...]

    def __post_init__(self):
        if self.status not in {"absent", "refused", "clean"}:
            raise ValueError("invalid applicability result status")
        if self.status == "clean":
            if type(self.capture_bytes) is not bytes or self.findings:
                raise ValueError("clean result requires only canonical capture bytes")
        elif self.capture_bytes is not None or bool(self.findings) != (self.status == "refused"):
            raise ValueError("invalid absent or refused result")

    @property
    def capture(self):
        return None if self.capture_bytes is None else json.loads(self.capture_bytes)


class Refusal(ValueError):
    def __init__(self, code, field, row=None):
        self.finding = Finding(code, field, row)
        super().__init__(code + ":" + field)


def _fence(text):
    """Return a payload or true absence; attempted declarations never disappear."""
    lines = [line.rstrip("\r\n") for line in inventory._markdown_physical_lines(text)]
    attempts = [i for i, line in enumerate(lines) if ATTEMPT.search(line)]
    if not attempts:
        return None
    if len(attempts) != 1:
        raise Refusal("A001", "fence-count")
    target = attempts[0]
    opened = None
    for index, line in enumerate(lines):
        match = FENCE.fullmatch(line)
        if index == target:
            if opened is not None or match is None or match["info"] != FENCE_INFO:
                raise Refusal("A001", "fence-opening")
            if index and lines[index - 1].strip():
                raise Refusal("A001", "fence-isolation")
            mark = match["mark"]
            for end in range(index + 1, len(lines)):
                close = FENCE.fullmatch(lines[end])
                if (close and close["mark"][0] == mark[0]
                        and len(close["mark"]) >= len(mark) and not close["info"]):
                    if end + 1 < len(lines) and lines[end + 1].strip():
                        raise Refusal("A001", "fence-isolation")
                    return "\n".join(lines[index + 1:end])
            raise Refusal("A001", "fence-unterminated")
        surrounding = SURROUNDING_FENCE.fullmatch(line)
        if surrounding:
            if opened is None:
                opened = surrounding["mark"]
            elif (surrounding["mark"][0] == opened[0] and len(surrounding["mark"]) >= len(opened)
                  and not surrounding["info"].strip()):
                opened = None
    raise Refusal("A001", "fence-opening")


def _json(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Refusal("A002", "duplicate-key")
            result[key] = value
        return result

    def constant(value):
        raise Refusal("A002", "non-finite")

    try:
        value = json.loads(payload, object_pairs_hook=pairs, parse_constant=constant)
        pending = [(value, 1)]
        while pending:
            node, depth = pending.pop()
            if depth > 32:
                raise Refusal("A002", "depth")
            if isinstance(node, dict):
                pending.extend((item, depth + 1) for item in node.values())
            elif isinstance(node, list):
                pending.extend((item, depth + 1) for item in node)
            elif isinstance(node, float):
                raise Refusal("A002", "number")
        if not isinstance(value, dict) or set(value) != FIELDS or value["schema"] != SCHEMA:
            raise Refusal("A002", "schema")
        return value
    except (ValueError, RecursionError) as error:
        if isinstance(error, Refusal):
            raise
        raise Refusal("A002", "json") from None


def _text(value, maximum):
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        return len(value.encode("utf-8")) <= maximum
    except UnicodeError:
        return False


def _views(value):
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_SOURCE_VIEWS:
        raise Refusal("A004", "source-views")
    ids, aliases = set(), set()
    for index, row in enumerate(value):
        if not isinstance(row, dict) or set(row) != inventory.SOURCE_VIEW_FIELDS:
            raise Refusal("A004", "source-view-fields", index)
        identifier = row["id"]
        path = inventory._portable_path(row["path"])
        if (not isinstance(identifier, str) or not KEBAB.fullmatch(identifier)
                or identifier in ids or path is None
                or inventory._portable_alias(path) in aliases
                or any(not isinstance(row[k], str) or not SHA256.fullmatch(row[k])
                       for k in ("source_sha256", "view_sha256"))):
            raise Refusal("A004", "source-view-binding", index)
        ids.add(identifier)
        aliases.add(inventory._portable_alias(path))
    return value


def _rows(value, sources, known, joined):
    if not isinstance(value, list) or len(value) > MAX_ENTRIES:
        raise Refusal("A005", "entries")
    ids, regressions, routes = set(), set(), []
    findings = {row["id"]: row for row in known["findings"]}
    descriptors = {} if joined is None else {row["id"]: row for row in joined["criteria"]}
    for index, row in enumerate(value):
        if not isinstance(row, dict) or set(row) != ENTRY_FIELDS:
            raise Refusal("A005", "entry-fields", index)
        identifier = row["id"]
        if not isinstance(identifier, str) or not KEBAB.fullmatch(identifier) or identifier in ids:
            raise Refusal("A005", "entry-id", index)
        ids.add(identifier)
        if not _text(row["rationale"], MAX_TEXT_BYTES) or not _text(row["source_ref"], MAX_TEXT_BYTES):
            raise Refusal("A005", "entry-text", index)
        source_id, colon, detail = row["source_ref"].partition(":")
        if not colon or not detail.strip() or source_id not in sources:
            raise Refusal("A006", "source-ref", index)
        source = sources[source_id]
        span = row["source_span"]
        if not isinstance(span, dict) or set(span) != SPAN_FIELDS:
            raise Refusal("A006", "source-span", index)
        start, end = span["start_byte"], span["end_byte"]
        if (type(start) is not int or type(end) is not int
                or not 0 <= start < end <= len(source) or end - start > MAX_SPAN_BYTES
                or not isinstance(span["sha256"], str) or not SHA256.fullmatch(span["sha256"])):
            raise Refusal("A006", "span-bounds", index)
        raw = source[start:end]
        try:
            witness = raw.decode("utf-8")
        except UnicodeError:
            raise Refusal("A006", "span-encoding", index) from None
        if digest(raw) != span["sha256"]:
            raise Refusal("A006", "span-digest", index)
        status = row["source_status"]
        if status is not None and (not _text(status, MAX_STATUS_BYTES) or status not in witness):
            raise Refusal("A006", "status-witness", index)
        tracking = row["tracking"]
        if (not isinstance(tracking, list) or len(tracking) > MAX_TRACKING
                or any(not isinstance(url, str) or not ISSUE.fullmatch(url) for url in tracking)
                or len(set(tracking)) != len(tracking)):
            raise Refusal("A005", "tracking", index)
        disposition = row["disposition"]
        owner, binding = None, None
        if disposition == "local-regression":
            target = row["finding_id"]
            if (not isinstance(target, str) or target not in findings or target in regressions
                    or row["criterion_id"] is not None):
                raise Refusal("A007", "regression-target", index)
            regressions.add(target)
            owner, binding = "known-failure", findings[target]
        elif disposition == "integration-requirement":
            target = row["criterion_id"]
            if not isinstance(target, str) or target not in descriptors or row["finding_id"] is not None:
                raise Refusal("A008", "criterion-target", index)
            owner, binding = "success-criteria", descriptors[target]
        elif disposition in ("historical", "out-of-scope"):
            if row["finding_id"] is not None or row["criterion_id"] is not None:
                raise Refusal("A005", "inert-target", index)
        else:
            raise Refusal("A005", "disposition", index)
        routes.append({"entry_id": identifier, "owner": owner, "binding": binding,
                       "binding_sha256": None if binding is None else digest(canonical_bytes(binding))})
    if regressions != set(findings):
        raise Refusal("A007", "regression-set")
    return routes


def load_checked_applicability(study_path, runbook_path, repository_root) -> ApplicabilityLoadResult:
    """Read exact documents and sources; return absent, refused or a clean capture.

    Paths are trusted caller operands, never taken from a declaration. The
    checked inventory owns source discovery and regression semantics; the
    success-criteria parser owns descriptor/Exit joins. Capture bytes are
    immutable and their optional dict projection is defensive. Refusals carry
    only A000--A009, fixed field names and numeric row indexes. A clean result
    grants no execution, judgment, controller mutation or success claim.
    """
    study, runbook = Path(study_path), Path(runbook_path)
    limits = inventory.InventoryReadLimits(MAX_DOCUMENT_BYTES, MAX_SOURCE_VIEWS, MAX_AGGREGATE_BYTES)
    reads = inventory._CapturedReads(Path(repository_root), limits)
    try:
        if not inventory._secure_read_primitives():
            raise Refusal("A000", "secure-read-primitives")
        try:
            study_bytes = reads.document(study)
            runbook_bytes = reads.document(runbook)
            study_text, runbook_text = study_bytes.decode("utf-8"), runbook_bytes.decode("utf-8")
        except (OSError, UnicodeError):
            raise Refusal("A000", "documents") from None
        payload = _fence(study_text)
        if _fence(runbook_text) is not None:
            raise Refusal("A001", "runbook-declaration")
        if payload is None:
            reads.document(study)
            reads.document(runbook)
            return ApplicabilityLoadResult("absent", None, ())
        declaration = _json(payload)
        _views(declaration["source_views"])
        checked = inventory.load_checked_inventory_sources(study, runbook, repository_root, limits=limits)
        if checked.result.status != "clean":
            raise Refusal("A003", "known-failure-inventory")
        known = checked.result.capture
        if study_bytes != checked.study_bytes or runbook_bytes != checked.runbook_bytes:
            raise Refusal("A009", "document-drift")
        for path, identity in checked.identities:
            if reads.identities.setdefault(path, identity) != identity:
                raise Refusal("A009", "input-identity")
        if declaration["source_views"] != known["source_views"]:
            raise Refusal("A004", "source-view-equality")
        sources = {}
        for identifier, _, _, _, _, data, _ in checked.sources:
            try:
                data.decode("utf-8")
            except UnicodeError:
                raise Refusal("A006", "source-encoding") from None
            sources[identifier] = data
        try:
            joined = criteria.join(criteria.parse(study_bytes), runbook_bytes)
        except criteria.Refusal:
            raise Refusal("A008", "success-criteria-join") from None
        routes = _rows(declaration["entries"], sources, known, joined)
        # Recheck the whole consumed set after spans and target joins, preserving
        # the stronger identities held by the inventory's opt-in read session.
        for _, view_path, view_bytes, _, source_path, source_bytes, _ in checked.sources:
            if (reads.source(Path(repository_root), view_path) != view_bytes
                    or reads.source(Path(repository_root), source_path) != source_bytes):
                raise Refusal("A009", "source-drift")
        reads.document(study)
        reads.document(runbook)
        capture = {"schema": CAPTURE_SCHEMA,
                   "study_sha256": digest(study_bytes), "runbook_sha256": digest(runbook_bytes),
                   "declaration_sha256": digest(canonical_bytes(declaration)),
                   "inventory_sha256": known["inventory_sha256"],
                   "success_criteria_sha256": None if joined is None else digest(canonical_bytes(joined)),
                   "source_views": declaration["source_views"],
                   "entries": declaration["entries"], "routes": routes}
        return ApplicabilityLoadResult("clean", canonical_bytes(capture), ())
    except OSError:
        return ApplicabilityLoadResult("refused", None, (Finding("A009", "input-stability"),))
    except Refusal as error:
        return ApplicabilityLoadResult("refused", None, (error.finding,))
