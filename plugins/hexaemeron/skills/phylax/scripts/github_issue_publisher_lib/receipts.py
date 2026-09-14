"""Content-free retained events and terminal publication receipts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import Protocol

from .canonical import canonical_json, parse_json_bytes
from .errors import DIAGNOSTIC_SCHEMA, PublisherError, refuse


EVENT_SCHEMA = "github-issue-publisher-event/v1"
RESULT_SCHEMA = "github-issue-publication-result/v1"
MAX_EVENTS = 16
MAX_RESULT_BYTES = 4_096
MAX_ISSUE_NUMBER = (1 << 63) - 1
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
CODE_RE = re.compile(r"GIP[0-9]{3}\Z")
FIELD_RE = re.compile(r"[a-z][a-z0-9.-]{0,127}\Z")
STAGES = frozenset(
    {
        "admission",
        "signer",
        "token",
        "create",
        "readback-authenticated",
        "readback-anonymous",
        "receipt",
        "cleanup",
    }
)
EVENT_OUTCOMES = frozenset({"accepted", "refused", "confirmed", "indeterminate"})
RESULT_OUTCOMES = frozenset(
    {
        "refused",
        "published",
        "create-indeterminate",
        "created-but-unverified",
        "receipt-failed",
        "cleanup-failed",
    }
)
COUNT_FIELDS = (
    "signer_attempts",
    "token_attempts",
    "post_attempts",
    "authenticated_readbacks",
    "anonymous_readbacks",
)


class ReceiptSink(Protocol):
    def write(self, payload: bytes) -> None: ...

    def close(self) -> None: ...


def _counts(values: Mapping[str, int]) -> dict[str, int]:
    copied = dict(values)
    if set(copied) != set(COUNT_FIELDS):
        refuse("GIP400", "receipt.counts")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 1
        for value in copied.values()
    ):
        refuse("GIP400", "receipt.counts")
    return {name: copied[name] for name in COUNT_FIELDS}


def _result_semantics(
    *,
    outcome: str,
    issue_known: bool,
    counts: Mapping[str, int],
    readback: str,
    cleanup_complete: bool,
    code: str,
) -> None:
    """Reject field combinations the publication lifecycle cannot emit."""

    signer = counts["signer_attempts"]
    token = counts["token_attempts"]
    post = counts["post_attempts"]
    authenticated = counts["authenticated_readbacks"]
    anonymous = counts["anonymous_readbacks"]
    if not (anonymous <= authenticated <= post <= token <= signer):
        refuse("GIP400", "receipt.value")
    if issue_known != (post == 1 and readback in {"matched", "failed"}):
        refuse("GIP400", "receipt.value")
    if readback == "not-run" and (authenticated != 0 or anonymous != 0):
        refuse("GIP400", "receipt.value")
    if readback == "matched" and (authenticated != 1 or anonymous != 1):
        refuse("GIP400", "receipt.value")
    if readback == "failed" and not issue_known:
        refuse("GIP400", "receipt.value")

    if outcome == "published":
        valid = issue_known and readback == "matched" and cleanup_complete and code == "GIP000"
    elif outcome == "refused":
        valid = (
            post == 0
            and not issue_known
            and readback == "not-run"
            and cleanup_complete
            and code not in {"GIP000", "GIP501", "GIP402"}
        )
    elif outcome == "create-indeterminate":
        valid = (
            post == 1
            and not issue_known
            and readback == "not-run"
            and (
                (cleanup_complete and code not in {"GIP000", "GIP501", "GIP402"})
                or (not cleanup_complete and code in {"GIP501", "GIP402"})
            )
        )
    elif outcome == "created-but-unverified":
        valid = (
            post == 1
            and issue_known
            and readback == "failed"
            and (
                (cleanup_complete and code not in {"GIP000", "GIP501", "GIP402"})
                or (not cleanup_complete and code in {"GIP501", "GIP402"})
            )
        )
    elif outcome == "cleanup-failed":
        valid = (
            not cleanup_complete
            and code == "GIP501"
            and (
                (not issue_known and post == 0 and readback == "not-run")
                or (issue_known and post == 1 and readback == "matched")
            )
        )
    else:
        valid = (
            outcome == "receipt-failed"
            and not cleanup_complete
            and code == "GIP402"
            and (
                (not issue_known and post == 0 and readback == "not-run")
                or (issue_known and post == 1 and readback == "matched")
            )
        )
    if not valid or (code == "GIP000") != (outcome == "published"):
        refuse("GIP400", "receipt.value")


class RetainedEvents:
    """Keep a bounded sequence of content-free correlated stage events."""

    def __init__(self) -> None:
        self._events: list[dict[str, object]] = []

    @property
    def documents(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                **event,
                "counts": dict(event["counts"]),
            }
            for event in self._events
        )

    def emit(
        self,
        *,
        correlation_sha256: str,
        stage: str,
        outcome: str,
        code: str,
        counts: Mapping[str, int],
        elapsed_ms: int,
    ) -> None:
        if len(self._events) >= MAX_EVENTS:
            refuse("GIP401", "events.count")
        if (
            SHA256_RE.fullmatch(correlation_sha256) is None
            or stage not in STAGES
            or outcome not in EVENT_OUTCOMES
            or CODE_RE.fullmatch(code) is None
            or isinstance(elapsed_ms, bool)
            or not isinstance(elapsed_ms, int)
            or elapsed_ms < 0
            or elapsed_ms > 60_000
        ):
            refuse("GIP401", "events.value")
        self._events.append(
            {
                "schema": EVENT_SCHEMA,
                "correlation_sha256": correlation_sha256,
                "stage": stage,
                "outcome": outcome,
                "code": code,
                "counts": _counts(counts),
                "elapsed_ms": elapsed_ms,
            }
        )


def result_document(
    *,
    outcome: str,
    request_sha256: str,
    final_sha256: str,
    correlation_sha256: str,
    issue_number: int | None,
    issue_url: str | None,
    counts: Mapping[str, int],
    readback: str,
    cleanup_complete: bool,
    code: str,
) -> dict[str, object]:
    if outcome not in RESULT_OUTCOMES:
        refuse("GIP400", "receipt.outcome")
    if any(
        not isinstance(value, str) or SHA256_RE.fullmatch(value) is None
        for value in (request_sha256, final_sha256, correlation_sha256)
    ) or not isinstance(code, str) or CODE_RE.fullmatch(code) is None:
        refuse("GIP400", "receipt.digest")
    if readback not in {"not-run", "matched", "failed"}:
        refuse("GIP400", "receipt.readback")
    if not isinstance(cleanup_complete, bool):
        refuse("GIP400", "receipt.cleanup")
    if issue_number is None:
        if issue_url is not None:
            refuse("GIP400", "receipt.issue")
    elif (
        isinstance(issue_number, bool)
        or not isinstance(issue_number, int)
        or issue_number < 1
        or issue_number > MAX_ISSUE_NUMBER
        or issue_url
        != f"https://github.com/wildcat-finance/skills/issues/{issue_number}"
    ):
        refuse("GIP400", "receipt.issue")
    safe_counts = _counts(counts)
    _result_semantics(
        outcome=outcome,
        issue_known=issue_number is not None,
        counts=safe_counts,
        readback=readback,
        cleanup_complete=cleanup_complete,
        code=code,
    )
    return {
        "schema": RESULT_SCHEMA,
        "outcome": outcome,
        "request_sha256": request_sha256,
        "final_sha256": final_sha256,
        "correlation_sha256": correlation_sha256,
        "issue_number": issue_number,
        "issue_url": issue_url,
        "counts": safe_counts,
        "readback": readback,
        "cleanup_complete": cleanup_complete,
        "code": code,
    }


def result_bytes(document: Mapping[str, object]) -> bytes:
    payload = canonical_json(dict(document))
    if len(payload) > MAX_RESULT_BYTES:
        refuse("GIP400", "receipt.bytes")
    return payload


def parse_closed_result(raw: bytes) -> dict[str, object]:
    """Validate the only result and diagnostic forms accepted by the client."""

    if not isinstance(raw, bytes) or len(raw) > MAX_RESULT_BYTES:
        refuse("GIP400", "receipt.bytes")
    document = parse_json_bytes(raw)
    if document.get("schema") == DIAGNOSTIC_SCHEMA:
        expected = {
            "schema",
            "outcome",
            "code",
            "field",
            "mint_attempts",
            "post_attempts",
        }
        if (
            set(document) != expected
            or document.get("outcome") != "refused"
            or not isinstance(document.get("field"), str)
            or FIELD_RE.fullmatch(document["field"]) is None
            or CODE_RE.fullmatch(str(document.get("code"))) is None
            or document["code"] == "GIP000"
            or type(document.get("mint_attempts")) is not int
            or document["mint_attempts"] not in (0, 1)
            or type(document.get("post_attempts")) is not int
            or document["post_attempts"] not in (0, 1)
            or document["post_attempts"] > document["mint_attempts"]
        ):
            refuse("GIP400", "receipt.diagnostic")
        return document
    expected = {
        "schema",
        "outcome",
        "request_sha256",
        "final_sha256",
        "correlation_sha256",
        "issue_number",
        "issue_url",
        "counts",
        "readback",
        "cleanup_complete",
        "code",
    }
    if set(document) != expected or document.get("schema") != RESULT_SCHEMA:
        refuse("GIP400", "receipt.schema")
    try:
        replayed = result_document(
            outcome=document["outcome"],
            request_sha256=document["request_sha256"],
            final_sha256=document["final_sha256"],
            correlation_sha256=document["correlation_sha256"],
            issue_number=document["issue_number"],
            issue_url=document["issue_url"],
            counts=document["counts"],
            readback=document["readback"],
            cleanup_complete=document["cleanup_complete"],
            code=document["code"],
        )
    except (AttributeError, TypeError, ValueError) as exc:
        raise PublisherError("GIP400", "receipt.value") from exc
    if replayed != document:
        refuse("GIP400", "receipt.value")
    return document


@dataclass
class MemoryReceiptSink:
    """Injected component-test sink; production deployment supplies the file sink."""

    payload: bytes | None = None
    closed: bool = False

    def write(self, payload: bytes) -> None:
        if self.closed or self.payload is not None:
            refuse("GIP402", "receipt.state")
        if not isinstance(payload, bytes) or len(payload) > MAX_RESULT_BYTES:
            refuse("GIP402", "receipt.write")
        self.payload = bytes(payload)

    def close(self) -> None:
        self.closed = True
