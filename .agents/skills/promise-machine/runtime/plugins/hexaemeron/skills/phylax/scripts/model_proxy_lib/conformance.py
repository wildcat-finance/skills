"""Closed hostile-conformance runner for the version-1 model proxy."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import secrets
import struct
import tempfile
from types import MappingProxyType
from typing import Callable

from .canonical import (
    MAX_JSON_MEMBERS,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
    sha256_bytes,
)
from .errors import PolicyError, refuse
from .framing import REQUEST_SCHEMA, TEXT_OPERATION, FramingCore
from .lifecycle import LifecycleController, ModelProxyRuntime
from .operator import render_operator_text
from .policy import CompiledPolicy, compile_policy_file
from .profiles import ProviderProfile, resolve_profile
from .provider import ProviderEvent, ProviderSession
from .transport import (
    READ_CHUNK_BYTES,
    HTTPSConnector,
    HTTPSRequest,
    HTTPSResponse,
)


CONFORMANCE_MANIFEST_SCHEMA = "model-proxy-conformance-manifest/v1"
CONFORMANCE_RESULT_SCHEMA = "model-proxy-conformance-result/v1"
MAX_CONFORMANCE_MANIFEST_BYTES = 128 * 1024

_MANIFEST_FIELDS = frozenset(
    {
        "schema",
        "accepted_job",
        "jobspec_sha256",
        "policy_sha256",
        "manifest_sha256",
        "rows",
    }
)
_DIGESTED_MANIFEST_FIELDS = (
    "schema",
    "accepted_job",
    "jobspec_sha256",
    "policy_sha256",
    "rows",
)
_ROW_FIELDS = frozenset({"id", "expected_outcome"})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")

# This is the complete issue-700 acceptance order. The manifest may neither
# select a subset nor introduce a runner name through external input.
EXPECTED_ROWS = (
    ("positive", "MP000", "provider-only"),
    ("arbitrary-url", "MP207", "not-read"),
    ("dns-rebinding", "MP304", "provider-only"),
    ("redirect", "MP307", "provider-only"),
    ("credential-header", "MP207", "not-read"),
    ("unsupported-method", "MP207", "not-read"),
    ("unsupported-model", "MP207", "not-read"),
    ("oversized", "MP201", "not-read"),
    ("nested", "MP104", "not-read"),
    ("request-flood", "MP217", "not-read"),
    ("response-flood", "MP310", "provider-only"),
    ("cross-job", "MP401", "not-read"),
    ("replay-after-expiry", "MP404", "not-read"),
    ("call-after-cancellation", "MP406", "not-read"),
)

DEPENDENCY_BOUNDARIES = MappingProxyType(
    {
        "issue_698_acceptance_receipt": "not-established",
        "issue_699_launch_receipt": "not-established",
        "live_provider": "not-established",
        "public_pilot": "not-established",
        "end_to_end_digest_join": "not-established",
    }
)

POSITIVE_SURFACES = frozenset(
    {
        "guest_frames",
        "receipts",
        "events",
        "diagnostics",
        "argv",
        "environment_fixture",
        "produced_tree",
    }
)


@dataclass(frozen=True, slots=True)
class ConformanceRowResult:
    """One content-free, bounded conformance outcome."""

    identifier: str
    outcome: str
    disclosure_state: str
    requests: int
    request_bytes: int
    response_bytes: int
    guest_bytes: int
    receipts: int
    duration_ns: int
    cleanup_state: str
    executed: bool = True

    def document(self) -> dict[str, object]:
        return {
            "id": self.identifier,
            "outcome": self.outcome,
            "disclosure_state": self.disclosure_state,
            "requests": self.requests,
            "request_bytes": self.request_bytes,
            "response_bytes": self.response_bytes,
            "guest_bytes": self.guest_bytes,
            "receipts": self.receipts,
            "duration_ns": str(self.duration_ns),
            "executed": self.executed,
            "cleanup_state": self.cleanup_state,
        }


@dataclass(frozen=True, slots=True)
class ConformanceManifestResult:
    """Safe aggregate from one complete, exact conformance execution."""

    manifest_sha256: str
    jobspec_sha256: str
    policy_sha256: str
    rows: tuple[ConformanceRowResult, ...]

    def document(self) -> dict[str, object]:
        return {
            "schema": CONFORMANCE_RESULT_SCHEMA,
            "outcome": "conformance_checked",
            "manifest_schema": CONFORMANCE_MANIFEST_SCHEMA,
            "digests": {
                "manifest_sha256": self.manifest_sha256,
                "jobspec_sha256": self.jobspec_sha256,
                "policy_sha256": self.policy_sha256,
            },
            "counts": {
                "rows": len(self.rows),
                "positive": 1,
                "hostile": len(self.rows) - 1,
                "executed": sum(row.executed for row in self.rows),
                "requests": sum(row.requests for row in self.rows),
                "receipts": sum(row.receipts for row in self.rows),
            },
            "sizes": {
                "request_bytes": sum(row.request_bytes for row in self.rows),
                "response_bytes": sum(row.response_bytes for row in self.rows),
                "guest_bytes": sum(row.guest_bytes for row in self.rows),
            },
            "timings": {
                "duration_ns": str(sum(row.duration_ns for row in self.rows)),
            },
            "proofs": {
                "policy_jobspec_binding": "established",
                "loopback_credential_injection": "established",
                "normalised_response": "established",
                "bounded_receipts": "established",
                "operator_disclosure": "established",
                "canary_content_absence": "established",
            },
            "cleanup_state": (
                "complete"
                if self.rows
                and all(row.executed and row.cleanup_state == "complete" for row in self.rows)
                else "incomplete"
            ),
            "dependencies": dict(DEPENDENCY_BOUNDARIES),
            "rows": [row.document() for row in self.rows],
        }


class _SequenceClock:
    """Return deterministic values, then hold the final value."""

    def __init__(self, *values: int):
        self._values = values
        self._position = 0

    def __call__(self) -> int:
        position = min(self._position, len(self._values) - 1)
        self._position += 1
        return self._values[position]


class _MutableClock:
    def __init__(self, value: int):
        self.value = value

    def __call__(self) -> int:
        return self.value


class _Response:
    """In-process response with explicit bounded reads and close evidence."""

    def __init__(
        self,
        body: bytes,
        *,
        status: int = 200,
        headers: tuple[tuple[str, str], ...] | None = None,
        peer_address: str = "8.8.8.8",
    ):
        self.status = status
        self.headers = (
            (
                ("Content-Length", str(len(body))),
                ("Content-Type", "application/json"),
            )
            if headers is None
            else headers
        )
        self.peer_address = peer_address
        self._body = body
        self._position = 0
        self.read_sizes: list[int] = []
        self.closed = False

    def read(self, size: int) -> bytes:
        self.read_sizes.append(size)
        chunk = self._body[self._position : self._position + size]
        self._position += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


def conformance_manifest_digest(value: dict[str, object]) -> str:
    """Digest the closed manifest authority while excluding its digest field."""

    try:
        projected = {field: value[field] for field in _DIGESTED_MANIFEST_FIELDS}
    except (KeyError, TypeError):
        refuse("MP500", "conformance.manifest")
    return sha256_bytes(canonical_json(projected))


def _request_frame(
    input_text: str,
    *,
    operation: str = TEXT_OPERATION,
    extra: dict[str, object] | None = None,
) -> bytes:
    value: dict[str, object] = {
        "schema": REQUEST_SCHEMA,
        "operation": operation,
        "input": input_text,
    }
    if extra is not None:
        value.update(extra)
    payload = canonical_json(value)
    return struct.pack(">I", len(payload)) + payload


def _fixed_wall_ns() -> int:
    return 1_787_918_401 * 1_000_000_000


def _ensure_absent(surface: bytes, forbidden: tuple[bytes, ...]) -> None:
    if any(value in surface for value in forbidden):
        refuse("MP501", "conformance.content_absence")


def _complete_cleanup(established: bool) -> str:
    """Return the safe claim only after a state predicate establishes it."""

    if established is not True:
        refuse("MP501", "conformance.row.cleanup")
    return "complete"


def _scan_positive_surfaces(
    surfaces: dict[str, bytes],
    *,
    credential: bytes,
    input_content: bytes,
    output_content: bytes,
) -> None:
    """Keep authority and model content out of their forbidden surfaces."""

    if frozenset(surfaces) != POSITIVE_SURFACES:
        refuse("MP501", "conformance.content_absence")
    _ensure_absent(surfaces["guest_frames"], (credential, input_content))
    for name in (
        "receipts",
        "events",
        "diagnostics",
        "argv",
        "produced_tree",
    ):
        _ensure_absent(
            surfaces[name], (credential, input_content, output_content)
        )
    # The environment fixture is the one authorised home for the credential;
    # it must not acquire either model-content value.
    _ensure_absent(
        surfaces["environment_fixture"], (input_content, output_content)
    )


def _event_bytes(events: tuple[object, ...]) -> bytes:
    documents: list[dict[str, object]] = []
    for event in events:
        document = getattr(event, "document", None)
        if not callable(document):
            refuse("MP501", "conformance.events")
        value = document()
        if not isinstance(value, dict):
            refuse("MP501", "conformance.events")
        documents.append(value)
    return canonical_json(documents)


def _positive(policy: CompiledPolicy) -> ConformanceRowResult:
    profile = resolve_profile(policy.profile)
    credential = secrets.token_urlsafe(32)
    input_text = "input-" + secrets.token_urlsafe(18)
    output_text = "output-" + secrets.token_urlsafe(18)
    credential_bytes = credential.encode("ascii")
    input_bytes = input_text.encode("ascii")
    output_bytes = output_text.encode("ascii")
    response_body = canonical_json(
        {
            "schema": profile.provider_response_schema,
            "output": output_text,
            "usage": {
                "input_tokens": len(input_text),
                "output_tokens": len(output_text),
            },
        }
    )
    response = _Response(response_body)
    observed: list[HTTPSRequest] = []
    io_closed = False

    def close_io() -> None:
        nonlocal io_closed
        io_closed = True

    def exchange(
        request: HTTPSRequest, _context, _timeout: float
    ) -> HTTPSResponse:
        observed.append(request)
        mapped = parse_json_bytes(request.body, max_bytes=65_536)
        if (
            mapped
            != {
                "schema": profile.provider_request_schema,
                "model": profile.model,
                "input": input_text,
            }
            or request.scheme != profile.scheme
            or request.hostname != profile.hostname
            or request.port != profile.port
            or request.method != profile.method
            or request.path != profile.path_family
            or request.header("Authorization") != f"Bearer {credential}"
        ):
            refuse("MP501", "conformance.positive.mapping")
        return response

    connector = HTTPSConnector(
        profile,
        resolver=lambda _hostname, _port: ("8.8.8.8",),
        exchange=exchange,
        clock=_SequenceClock(10_000_000, 11_000_000),
    )
    environment_fixture = {profile.credential_environment: credential}
    argv_fixture = ("model_proxy.py", "conformance", "--manifest", "manifest.json")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        receipt_path = root / "receipts.jsonl"
        runtime = ModelProxyRuntime(
            policy,
            connector,
            receipt_path,
            credential_source=lambda name: environment_fixture[name],
            monotonic_clock=_MutableClock(1_000_000_000),
            wall_clock=_MutableClock(_fixed_wall_ns()),
            io_closer=close_io,
        )
        admitted = runtime.feed(_request_frame(input_text))
        runtime.finish_input()
        if len(admitted) != 1:
            refuse("MP501", "conformance.positive.admission")
        guest = runtime.generate(admitted[0], final=True)
        terminal = runtime.terminal
        provider_events = runtime.provider_events
        framing_events = runtime.framing_events
        receipt_bytes = read_bounded_file(receipt_path, 64 * 1024)
        produced_tree = b"".join(
            child.read_bytes() for child in sorted(root.iterdir()) if child.is_file()
        )
        operator_text = runtime.operator_text()

    expected_payload = canonical_json(
        {
            "schema": "model-response/v1",
            "sequence": 1,
            "output": output_text,
        }
    )
    expected_guest = struct.pack(">I", len(expected_payload)) + expected_payload
    lines = receipt_bytes.splitlines()
    receipt_records = [parse_json_bytes(line, max_bytes=4_096) for line in lines]
    diagnostics = canonical_json(
        {
            "schema": CONFORMANCE_RESULT_SCHEMA,
            "outcome": "positive_checked",
            "jobspec_sha256": policy.jobspec_sha256,
            "policy_sha256": policy.policy_sha256,
        }
    )
    surfaces = {
        "guest_frames": guest,
        "receipts": receipt_bytes,
        "events": _event_bytes(provider_events) + _event_bytes(framing_events),
        "diagnostics": diagnostics,
        "argv": canonical_json(list(argv_fixture)),
        "environment_fixture": canonical_json(environment_fixture),
        "produced_tree": produced_tree,
    }
    _scan_positive_surfaces(
        surfaces,
        credential=credential_bytes,
        input_content=input_bytes,
        output_content=output_bytes,
    )
    if (
        guest != expected_guest
        or len(observed) != 1
        or not response.closed
        or terminal is None
        or terminal.code != "MP000"
        or terminal.disclosure_state != "provider-only"
        or len(lines) != 3
        or [record.get("event") for record in receipt_records]
        != ["activation", "request", "terminal"]
        or any(len(line) > policy.document["limits"]["max_receipt_bytes"] for line in lines)
        or operator_text != render_operator_text(policy)
        or "do not prove" not in operator_text
        or policy.document["job"]["jobspec_sha256"] != policy.jobspec_sha256
        or credential not in environment_fixture.values()
        or input_text in environment_fixture.values()
        or output_text in environment_fixture.values()
    ):
        refuse("MP501", "conformance.positive.result")
    event = provider_events[-1] if provider_events else None
    if not isinstance(event, ProviderEvent) or event.code != "MP000":
        refuse("MP501", "conformance.positive.events")
    return ConformanceRowResult(
        identifier="positive",
        outcome="MP000",
        disclosure_state=event.disclosure_state,
        requests=1,
        request_bytes=event.request_bytes,
        response_bytes=event.response_bytes,
        guest_bytes=len(guest),
        receipts=len(lines),
        duration_ns=event.duration_ns,
        cleanup_state=_complete_cleanup(runtime.cleanup_complete and io_closed),
    )


def _framing_refusal(
    identifier: str,
    expected: str,
    policy: CompiledPolicy,
    data: bytes,
) -> ConformanceRowResult:
    core = FramingCore(policy)
    try:
        core.feed(data)
    except PolicyError as error:
        if error.code != expected:
            refuse("MP501", "conformance.row.outcome")
    else:
        refuse("MP501", "conformance.row.unexecuted")
    events = core.events
    accepted = sum(
        event.stage == "request" and event.outcome == "accepted" for event in events
    )
    if not events or events[-1].code != expected:
        refuse("MP501", "conformance.row.events")
    core.close()
    cleanup_state = _complete_cleanup(core.cleanup_complete)
    return ConformanceRowResult(
        identifier=identifier,
        outcome=expected,
        disclosure_state="not-read",
        requests=accepted,
        request_bytes=0,
        response_bytes=0,
        guest_bytes=0,
        receipts=0,
        duration_ns=0,
        cleanup_state=cleanup_state,
    )


def _provider_refusal(
    identifier: str,
    expected: str,
    policy: CompiledPolicy,
    *,
    resolver: Callable[[str, int], tuple[str, ...]],
    response: _Response | None,
) -> ConformanceRowResult:
    profile = resolve_profile(policy.profile)
    credential = secrets.token_urlsafe(32)
    input_text = "hostile-" + secrets.token_urlsafe(12)

    def exchange(
        _request: HTTPSRequest, _context, _timeout: float
    ) -> HTTPSResponse:
        if response is None:
            refuse("MP501", "conformance.row.exchange")
        return response

    connector = HTTPSConnector(
        profile,
        resolver=resolver,
        exchange=exchange,
        clock=_SequenceClock(20_000_000, 21_000_000),
    )
    session = ProviderSession(
        policy,
        connector,
        credential_source=lambda _name: credential,
    )
    request = session.feed(_request_frame(input_text))[0]
    session.finish()
    try:
        session.generate(request)
    except PolicyError as error:
        if error.code != expected:
            refuse("MP501", "conformance.row.outcome")
    else:
        refuse("MP501", "conformance.row.unexecuted")
    events = session.events
    if not events or events[-1].code != expected:
        refuse("MP501", "conformance.row.events")
    event = events[-1]
    session.close()
    if response is not None and not response.closed:
        refuse("MP501", "conformance.row.cleanup")
    cleanup_state = _complete_cleanup(session.cleanup_complete)
    _ensure_absent(_event_bytes(events), (credential.encode("ascii"), input_text.encode("ascii")))
    return ConformanceRowResult(
        identifier=identifier,
        outcome=expected,
        disclosure_state=event.disclosure_state,
        requests=1,
        request_bytes=event.request_bytes,
        response_bytes=event.response_bytes,
        guest_bytes=0,
        receipts=0,
        duration_ns=event.duration_ns,
        cleanup_state=cleanup_state,
    )


def _controller_refusal(
    identifier: str,
    expected: str,
    action: Callable[[LifecycleController], None],
    policy: CompiledPolicy,
) -> ConformanceRowResult:
    controller = LifecycleController(
        policy,
        monotonic_clock=_MutableClock(1_000_000_000),
        wall_clock=_MutableClock(_fixed_wall_ns()),
    )
    try:
        action(controller)
    except PolicyError as error:
        if error.code != expected:
            refuse("MP501", "conformance.row.outcome")
    else:
        refuse("MP501", "conformance.row.unexecuted")
    terminal = controller.terminal
    if terminal is None or terminal.code != expected:
        refuse("MP501", "conformance.row.terminal")
    cleanup_state = _complete_cleanup(controller.cleanup_complete)
    return ConformanceRowResult(
        identifier=identifier,
        outcome=expected,
        disclosure_state=terminal.disclosure_state,
        requests=terminal.counts["requests"],
        request_bytes=terminal.counts["request_bytes"],
        response_bytes=terminal.counts["response_bytes"],
        guest_bytes=0,
        receipts=0,
        duration_ns=terminal.duration_ns,
        cleanup_state=cleanup_state,
    )


def _execute_case(identifier: str, policy: CompiledPolicy) -> ConformanceRowResult:
    input_text = "hostile-input"
    if identifier == "positive":
        return _positive(policy)
    if identifier == "arbitrary-url":
        return _framing_refusal(
            identifier,
            "MP207",
            policy,
            _request_frame(input_text, extra={"url": "https://example.invalid"}),
        )
    if identifier == "dns-rebinding":
        return _provider_refusal(
            identifier,
            "MP304",
            policy,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            response=_Response(b"", peer_address="1.1.1.1"),
        )
    if identifier == "redirect":
        return _provider_refusal(
            identifier,
            "MP307",
            policy,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            response=_Response(b"", status=302),
        )
    if identifier == "credential-header":
        return _framing_refusal(
            identifier,
            "MP207",
            policy,
            _request_frame(
                input_text,
                extra={"headers": {"Authorization": "guest-selected"}},
            ),
        )
    if identifier == "unsupported-method":
        return _framing_refusal(
            identifier,
            "MP207",
            policy,
            _request_frame(input_text, extra={"method": "GET"}),
        )
    if identifier == "unsupported-model":
        return _framing_refusal(
            identifier,
            "MP207",
            policy,
            _request_frame(input_text, extra={"model": "guest-model"}),
        )
    if identifier == "oversized":
        declared = policy.document["limits"]["max_request_bytes"] + 1
        return _framing_refusal(
            identifier, "MP201", policy, struct.pack(">I", declared)
        )
    if identifier == "nested":
        nested: object = "leaf"
        for _ in range(policy.document["limits"]["max_json_depth"] + 1):
            nested = [nested]
        return _framing_refusal(
            identifier,
            "MP104",
            policy,
            _request_frame(input_text, extra={"nested": nested}),
        )
    if identifier == "request-flood":
        count = policy.document["limits"]["max_requests"] + 1
        data = b"".join(_request_frame(input_text) for _ in range(count))
        return _framing_refusal(identifier, "MP217", policy, data)
    if identifier == "response-flood":
        maximum = policy.document["limits"]["max_response_bytes"]
        response = _Response(
            b"x" * (maximum + 1),
            headers=(
                ("Content-Type", "application/json"),
                ("Transfer-Encoding", "chunked"),
            ),
        )
        result = _provider_refusal(
            identifier,
            "MP310",
            policy,
            resolver=lambda _hostname, _port: ("8.8.8.8",),
            response=response,
        )
        remaining = maximum + 1
        expected_reads: list[int] = []
        while remaining:
            size = min(READ_CHUNK_BYTES, remaining)
            expected_reads.append(size)
            remaining -= size
        if response.read_sizes != expected_reads:
            refuse("MP501", "conformance.row.response_flood")
        return result
    if identifier == "cross-job":
        return _controller_refusal(
            identifier,
            "MP401",
            lambda controller: controller.reserve(
                sequence=1,
                request_bytes=1,
                input_text=input_text,
                job_id=controller.job_id + "-foreign",
                jobspec_sha256=controller.jobspec_sha256,
            ),
            policy,
        )
    if identifier == "replay-after-expiry":
        monotonic = _MutableClock(1_000_000_000)
        wall = _MutableClock(_fixed_wall_ns())
        controller = LifecycleController(
            policy,
            monotonic_clock=monotonic,
            wall_clock=wall,
        )
        first = controller.reserve(
            sequence=1,
            request_bytes=1,
            input_text=input_text,
            job_id=controller.job_id,
            jobspec_sha256=controller.jobspec_sha256,
        )
        wall.value = controller.absolute_expiry_ns
        try:
            controller.reserve(
                sequence=1,
                request_bytes=1,
                input_text=input_text,
                job_id=controller.job_id,
                jobspec_sha256=controller.jobspec_sha256,
            )
        except PolicyError as error:
            if error.code != "MP404":
                refuse("MP501", "conformance.row.outcome")
        else:
            refuse("MP501", "conformance.row.unexecuted")
        terminal = controller.terminal
        if terminal is None or terminal.code != "MP404":
            refuse("MP501", "conformance.row.terminal")
        winner = controller.fail(first, "MP404")
        if winner is not terminal:
            refuse("MP501", "conformance.row.cleanup")
        cleanup_state = _complete_cleanup(controller.cleanup_complete)
        return ConformanceRowResult(
            identifier=identifier,
            outcome="MP404",
            disclosure_state=terminal.disclosure_state,
            requests=terminal.counts["requests"],
            request_bytes=terminal.counts["request_bytes"],
            response_bytes=terminal.counts["response_bytes"],
            guest_bytes=0,
            receipts=0,
            duration_ns=terminal.duration_ns,
            cleanup_state=cleanup_state,
        )
    if identifier == "call-after-cancellation":
        def cancelled(controller: LifecycleController) -> None:
            controller.cancel()
            controller.reserve(
                sequence=1,
                request_bytes=1,
                input_text=input_text,
                job_id=controller.job_id,
                jobspec_sha256=controller.jobspec_sha256,
            )

        return _controller_refusal(
            identifier, "MP406", cancelled, policy
        )
    refuse("MP500", "conformance.manifest.row")


def _manifest_object(
    value: object, fields: frozenset[str], field: str
) -> dict[str, object]:
    if not isinstance(value, dict) or frozenset(value) != fields:
        refuse("MP500", field)
    return value


def check_conformance_manifest(path: str | Path) -> ConformanceManifestResult:
    """Run every exact issue-700 row from one digest-bound local manifest."""

    try:
        manifest_path = Path(path)
        value = parse_json_bytes(
            read_bounded_file(manifest_path, MAX_CONFORMANCE_MANIFEST_BYTES),
            max_bytes=MAX_CONFORMANCE_MANIFEST_BYTES,
            max_members=MAX_JSON_MEMBERS,
        )
    except PolicyError:
        refuse("MP500", "conformance.manifest")
    except (OSError, TypeError, ValueError):
        refuse("MP500", "conformance.manifest.path")
    manifest = _manifest_object(value, _MANIFEST_FIELDS, "conformance.manifest")
    claimed_digest = manifest["manifest_sha256"]
    expected_jobspec = manifest["jobspec_sha256"]
    expected_policy = manifest["policy_sha256"]
    rows = manifest["rows"]
    if (
        manifest["schema"] != CONFORMANCE_MANIFEST_SCHEMA
        or manifest["accepted_job"] != "accepted-job.json"
        or not isinstance(claimed_digest, str)
        or _SHA256.fullmatch(claimed_digest) is None
        or not isinstance(expected_jobspec, str)
        or _SHA256.fullmatch(expected_jobspec) is None
        or not isinstance(expected_policy, str)
        or _SHA256.fullmatch(expected_policy) is None
        or not isinstance(rows, list)
        or len(rows) != len(EXPECTED_ROWS)
        or conformance_manifest_digest(manifest) != claimed_digest
    ):
        refuse("MP500", "conformance.manifest")

    seen: set[str] = set()
    for raw, expected in zip(rows, EXPECTED_ROWS, strict=True):
        row = _manifest_object(raw, _ROW_FIELDS, "conformance.manifest.row")
        identifier, expected_outcome, _disclosure = expected
        if (
            row["id"] != identifier
            or row["expected_outcome"] != expected_outcome
            or not isinstance(row["id"], str)
            or row["id"] in seen
        ):
            refuse("MP500", "conformance.manifest.row")
        seen.add(row["id"])

    try:
        policy = compile_policy_file(manifest_path.parent / "accepted-job.json")
    except PolicyError:
        refuse("MP500", "conformance.manifest.policy")
    if (
        policy.jobspec_sha256 != expected_jobspec
        or policy.policy_sha256 != expected_policy
    ):
        refuse("MP500", "conformance.manifest.policy")
    executed: list[ConformanceRowResult] = []
    for identifier, expected_outcome, disclosure_state in EXPECTED_ROWS:
        result = _execute_case(identifier, policy)
        if (
            not isinstance(result, ConformanceRowResult)
            or not result.executed
            or result.identifier != identifier
            or result.outcome != expected_outcome
            or result.disclosure_state != disclosure_state
            or result.cleanup_state != "complete"
        ):
            refuse("MP501", "conformance.row.unexecuted")
        executed.append(result)
    if len(executed) != len(EXPECTED_ROWS):
        refuse("MP501", "conformance.row.unexecuted")

    result = ConformanceManifestResult(
        manifest_sha256=claimed_digest,
        jobspec_sha256=policy.jobspec_sha256,
        policy_sha256=policy.policy_sha256,
        rows=tuple(executed),
    )
    safe_output = canonical_json(result.document())
    if len(safe_output) > 32 * 1024:
        refuse("MP501", "conformance.result")
    return result
