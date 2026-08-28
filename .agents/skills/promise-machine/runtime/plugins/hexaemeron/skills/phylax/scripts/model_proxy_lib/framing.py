"""Bounded provider-independent framing for one model proxy text operation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import struct
from typing import Any

from .canonical import (
    MAX_JSON_MEMBERS,
    MAX_JSON_SCALARS,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
)
from .errors import PolicyError, refuse
from .policy import (
    CompiledPolicy,
    LIMIT_FIELDS,
    POLICY_SCHEMA,
    compile_policy,
    compile_policy_file,
)
from .profiles import FEATURE_NAMES, resolve_profile


FRAME_PREFIX_BYTES = 4
FRAME_EVENT_SCHEMA = "model-proxy-frame-event/v1"
FRAMING_MANIFEST_SCHEMA = "model-proxy-framing-cases/v1"
REQUEST_SCHEMA = "model-request/v1"
RESPONSE_SCHEMA = "model-response/v1"
TEXT_OPERATION = "text.generate"
MAX_FRAMING_MANIFEST_BYTES = 128 * 1024

_REQUEST_FIELDS = frozenset({"schema", "operation", "input"})
_POLICY_ROOT_FIELDS = frozenset(
    {"schema", "compiler", "job", "provider", "disclosure", "limits", "receipt"}
)
_AUTHORITY_FIELDS = frozenset(
    {
        "api_key",
        "authorization",
        "base_url",
        "batch",
        "cancel",
        "channel",
        "conversation",
        "conversation_id",
        "credential",
        "endpoint",
        "expires_at",
        "headers",
        "image",
        "job",
        "job_id",
        "lifecycle",
        "method",
        "model",
        "multiplex",
        "origin",
        "path",
        "remote_reference",
        "remote_references",
        "remote_url",
        "request_id",
        "retention",
        "seq",
        "sequence",
        "stream",
        "timeout",
        "url",
    }
) | frozenset(FEATURE_NAMES)
_CASE_ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
_LOWER_HEX = re.compile(r"(?:[0-9a-f]{2})+\Z")


@dataclass(frozen=True, slots=True)
class TextRequest:
    """One admitted request with a sequence assigned by the trusted core."""

    sequence: int
    input_text: str = field(repr=False)
    _owner: object = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True)
class FrameEvent:
    """One bounded content-free observation of the framing stage."""

    stage: str
    outcome: str
    code: str

    def document(self) -> dict[str, str]:
        return {
            "schema": FRAME_EVENT_SCHEMA,
            "stage": self.stage,
            "outcome": self.outcome,
            "code": self.code,
        }


@dataclass(frozen=True, slots=True)
class FramingManifestResult:
    """Counts and policy identity established by one framing manifest check."""

    cases: int
    requests: int
    policy_sha256: str


@dataclass(frozen=True, slots=True)
class _FrameLimits:
    max_requests: int
    max_request_bytes: int
    max_response_bytes: int
    max_input_tokens: int
    max_output_tokens: int
    max_json_depth: int
    max_json_members: int
    max_string_bytes: int


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        refuse("MP204", "frame.policy")
    return value


def _validated_limits(policy: CompiledPolicy) -> _FrameLimits:
    """Validate the compiled policy identity and every code-owned ceiling."""

    if type(policy) is not CompiledPolicy:
        refuse("MP204", "frame.policy")
    document = _object(policy.document)
    if (
        frozenset(document) != _POLICY_ROOT_FIELDS
        or document.get("schema") != POLICY_SCHEMA
    ):
        refuse("MP204", "frame.policy")
    try:
        policy_bytes = canonical_json(document)
        replayed = compile_policy(policy.accepted_job_bytes)
    except (PolicyError, TypeError):
        refuse("MP204", "frame.policy")
    if (
        policy_bytes != replayed.policy_bytes
        or policy.policy_bytes != replayed.policy_bytes
        or policy.policy_sha256 != replayed.policy_sha256
        or policy.jobspec_sha256 != replayed.jobspec_sha256
        or policy.profile != replayed.profile
    ):
        refuse("MP204", "frame.policy")

    job = _object(document.get("job"))
    if job.get("jobspec_sha256") != policy.jobspec_sha256:
        refuse("MP204", "frame.policy")
    provider = _object(document.get("provider"))
    try:
        profile = resolve_profile(provider.get("id"))
    except PolicyError:
        refuse("MP204", "frame.policy")
    if (
        provider != profile.policy_fields()
        or policy.profile != profile.identifier
        or provider.get("operation") != TEXT_OPERATION
        or provider.get("request_schema") != REQUEST_SCHEMA
        or provider.get("response_schema") != RESPONSE_SCHEMA
    ):
        refuse("MP204", "frame.policy")

    limits = _object(document.get("limits"))
    if frozenset(limits) != frozenset(LIMIT_FIELDS):
        refuse("MP204", "frame.policy")
    for name in LIMIT_FIELDS:
        value = limits.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 1
            or value > profile.limit_ceilings[name]
        ):
            refuse("MP204", "frame.policy")
    relationships = (
        ("max_total_request_bytes", "max_request_bytes"),
        ("max_total_response_bytes", "max_response_bytes"),
        ("max_total_input_tokens", "max_input_tokens"),
        ("max_total_output_tokens", "max_output_tokens"),
        ("max_requests", "max_concurrency"),
    )
    if any(limits[total] < limits[single] for total, single in relationships):
        refuse("MP204", "frame.policy")
    if limits["max_receipts"] > limits["max_requests"] + 2:
        refuse("MP204", "frame.policy")
    return _FrameLimits(
        max_requests=limits["max_requests"],
        max_request_bytes=limits["max_request_bytes"],
        max_response_bytes=limits["max_response_bytes"],
        max_input_tokens=limits["max_input_tokens"],
        max_output_tokens=limits["max_output_tokens"],
        max_json_depth=limits["max_json_depth"],
        max_json_members=limits["max_json_members"],
        max_string_bytes=limits["max_string_bytes"],
    )


class FramingCore:
    """Incrementally decode ordered request frames and encode closed responses."""

    def __init__(self, policy: CompiledPolicy):
        self._limits = _validated_limits(policy)
        self._prefix = bytearray()
        self._payload = bytearray()
        self._expected_length: int | None = None
        self._next_sequence = 1
        self._owner = object()
        self._issued: dict[int, TextRequest] = {}
        self._events: list[FrameEvent] = []
        self._failed = False
        self._input_finished = False

    @property
    def events(self) -> tuple[FrameEvent, ...]:
        """Return the bounded request, response, stream, and refusal events."""

        return tuple(self._events)

    @property
    def buffered_bytes(self) -> int:
        """Expose the bounded incomplete-frame byte count for verification."""

        return len(self._prefix) + len(self._payload)

    def _record(self, stage: str, outcome: str, code: str) -> None:
        if len(self._events) < (self._limits.max_requests * 2) + 2:
            self._events.append(FrameEvent(stage=stage, outcome=outcome, code=code))

    def _discard_input(self) -> None:
        self._prefix.clear()
        self._payload.clear()
        self._expected_length = None
        self._issued.clear()

    def _refuse(self, code: str, field: str, stage: str) -> None:
        self._failed = True
        self._discard_input()
        self._record(stage, "refused", code)
        refuse(code, field)

    def _ensure_input_open(self) -> None:
        if self._failed or self._input_finished:
            refuse("MP216", "frame.state")

    def _accept_length(self) -> None:
        declared = struct.unpack(">I", self._prefix)[0]
        self._prefix.clear()
        if declared == 0:
            self._refuse("MP200", "frame.length", "length")
        if declared > self._limits.max_request_bytes:
            self._refuse("MP201", "frame.length", "length")
        self._expected_length = declared

    def _decode_request(self) -> TextRequest:
        try:
            value = parse_json_bytes(
                bytes(self._payload),
                max_bytes=self._limits.max_request_bytes,
                max_depth=self._limits.max_json_depth,
                max_members=self._limits.max_json_members,
                max_scalars=min(MAX_JSON_SCALARS, self._limits.max_json_members),
                max_string_bytes=self._limits.max_string_bytes,
            )
            if not isinstance(value, dict):
                refuse("MP205", "frame.request")
            actual = frozenset(value)
            if _REQUEST_FIELDS - actual:
                refuse("MP206", "frame.request.missing")
            extra = actual - _REQUEST_FIELDS
            if extra & _AUTHORITY_FIELDS:
                refuse("MP207", "frame.request.authority")
            if extra:
                refuse("MP208", "frame.request.extra")
            if not isinstance(value["schema"], str):
                refuse("MP209", "frame.request.schema")
            if value["schema"] != REQUEST_SCHEMA:
                refuse("MP210", "frame.request.schema")
            if not isinstance(value["operation"], str):
                refuse("MP209", "frame.request.operation")
            if value["operation"] != TEXT_OPERATION:
                refuse("MP211", "frame.request.operation")
            input_text = value["input"]
            if not isinstance(input_text, str):
                refuse("MP209", "frame.request.input")
            if len(input_text) > self._limits.max_input_tokens:
                refuse("MP212", "frame.request.input_tokens")
            if self._next_sequence > self._limits.max_requests:
                refuse("MP217", "frame.request.count")
        except PolicyError as error:
            self._failed = True
            self._discard_input()
            self._record("request", "refused", error.code)
            raise
        request = TextRequest(self._next_sequence, input_text, self._owner)
        self._issued[request.sequence] = request
        self._next_sequence += 1
        self._record("request", "accepted", "MP000")
        return request

    def feed(self, data: bytes) -> tuple[TextRequest, ...]:
        """Consume one ordered byte chunk without copying an unchecked frame."""

        self._ensure_input_open()
        if not isinstance(data, bytes):
            self._refuse("MP209", "frame.chunk", "stream")
        position = 0
        requests: list[TextRequest] = []
        while position < len(data):
            if self._expected_length is None:
                take = min(FRAME_PREFIX_BYTES - len(self._prefix), len(data) - position)
                self._prefix.extend(data[position : position + take])
                position += take
                if len(self._prefix) < FRAME_PREFIX_BYTES:
                    break
                self._accept_length()
            if self._expected_length is not None:
                remaining = self._expected_length - len(self._payload)
                take = min(remaining, len(data) - position)
                self._payload.extend(data[position : position + take])
                position += take
                if len(self._payload) < self._expected_length:
                    break
                requests.append(self._decode_request())
                self._payload.clear()
                self._expected_length = None
        return tuple(requests)

    def finish(self) -> None:
        """Close the input side, refusing any ambiguous trailing bytes."""

        self._ensure_input_open()
        if self._expected_length is not None:
            self._refuse("MP203", "frame.trailing_payload", "stream")
        if self._prefix:
            self._refuse("MP202", "frame.trailing_prefix", "stream")
        self._input_finished = True
        self._record("stream", "accepted", "MP000")

    def encode_response(self, request: TextRequest, output: str) -> bytes:
        """Encode one closed response for a sequence issued by this core."""

        if self._failed:
            refuse("MP216", "frame.state")
        if (
            not isinstance(request, TextRequest)
            or request._owner is not self._owner
            or isinstance(request.sequence, bool)
            or not isinstance(request.sequence, int)
            or request.sequence < 1
            or request.sequence >= self._next_sequence
            or self._issued.get(request.sequence) is not request
        ):
            self._refuse("MP213", "frame.response.sequence", "response")
        if not isinstance(output, str):
            self._refuse("MP214", "frame.response.output", "response")
        if len(output) > self._limits.max_output_tokens:
            self._refuse("MP215", "frame.response.output", "response")
        try:
            output_bytes = output.encode("utf-8")
        except UnicodeEncodeError:
            self._refuse("MP214", "frame.response.output", "response")
        if len(output_bytes) > self._limits.max_string_bytes:
            self._refuse("MP215", "frame.response.output", "response")
        try:
            payload = canonical_json(
                {
                    "schema": RESPONSE_SCHEMA,
                    "sequence": request.sequence,
                    "output": output,
                }
            )
        except PolicyError as error:
            self._failed = True
            self._discard_input()
            self._record("response", "refused", error.code)
            raise
        if len(payload) > self._limits.max_response_bytes:
            self._refuse("MP215", "frame.response.bytes", "response")
        del self._issued[request.sequence]
        self._record("response", "accepted", "MP000")
        return struct.pack(">I", len(payload)) + payload


def _manifest_object(
    value: Any, expected: frozenset[str], field: str
) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != expected:
        refuse("MP218", field)
    return value


def _hex_bytes(value: Any, field: str) -> bytes:
    if not isinstance(value, str) or _LOWER_HEX.fullmatch(value) is None:
        refuse("MP218", field)
    try:
        return bytes.fromhex(value)
    except ValueError:
        refuse("MP218", field)


def check_framing_manifest(path: str | Path) -> FramingManifestResult:
    """Run exact framing and response vectors from one bounded local manifest."""

    try:
        manifest_path = Path(path)
    except (OSError, TypeError, ValueError):
        refuse("MP218", "frame.manifest.path")
    value = parse_json_bytes(
        read_bounded_file(manifest_path, MAX_FRAMING_MANIFEST_BYTES),
        max_bytes=MAX_FRAMING_MANIFEST_BYTES,
        max_members=MAX_JSON_MEMBERS,
    )
    manifest = _manifest_object(
        value,
        frozenset({"schema", "accepted_job", "cases"}),
        "frame.manifest",
    )
    if manifest["schema"] != FRAMING_MANIFEST_SCHEMA:
        refuse("MP218", "frame.manifest.schema")
    if manifest["accepted_job"] != "accepted-job.json":
        refuse("MP218", "frame.manifest.accepted_job")
    cases = manifest["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 16:
        refuse("MP218", "frame.manifest.cases")

    policy = compile_policy_file(manifest_path.parent / "accepted-job.json")
    seen: set[str] = set()
    request_count = 0
    for case_value in cases:
        case = _manifest_object(
            case_value,
            frozenset({"id", "chunks_hex", "requests"}),
            "frame.manifest.case",
        )
        identifier = case["id"]
        if (
            not isinstance(identifier, str)
            or _CASE_ID.fullmatch(identifier) is None
            or identifier in seen
        ):
            refuse("MP218", "frame.manifest.case")
        seen.add(identifier)
        chunks = case["chunks_hex"]
        expected = case["requests"]
        if (
            not isinstance(chunks, list)
            or not 1 <= len(chunks) <= 512
            or not isinstance(expected, list)
            or not 1 <= len(expected) <= policy.document["limits"]["max_requests"]
        ):
            refuse("MP218", "frame.manifest.case")
        core = FramingCore(policy)
        decoded: list[TextRequest] = []
        for chunk in chunks:
            decoded.extend(core.feed(_hex_bytes(chunk, "frame.manifest.chunk")))
        core.finish()
        if len(decoded) != len(expected):
            refuse("MP218", "frame.manifest.result")
        for request, expected_value in zip(decoded, expected, strict=True):
            item = _manifest_object(
                expected_value,
                frozenset({"sequence", "input", "output", "response_hex"}),
                "frame.manifest.request",
            )
            if (
                isinstance(item["sequence"], bool)
                or not isinstance(item["sequence"], int)
                or item["sequence"] != request.sequence
                or not isinstance(item["input"], str)
                or item["input"] != request.input_text
                or not isinstance(item["output"], str)
            ):
                refuse("MP218", "frame.manifest.result")
            response = core.encode_response(request, item["output"])
            if response != _hex_bytes(item["response_hex"], "frame.manifest.response"):
                refuse("MP218", "frame.manifest.result")
            request_count += 1
    return FramingManifestResult(
        cases=len(cases),
        requests=request_count,
        policy_sha256=policy.policy_sha256,
    )
