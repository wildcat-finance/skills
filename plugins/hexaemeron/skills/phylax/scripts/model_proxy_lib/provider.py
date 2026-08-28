"""Admission-bound provider mapping for one model proxy text operation."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import secrets
import threading
from types import MappingProxyType
from typing import Any, Callable, Mapping

from .canonical import (
    MAX_JSON_MEMBERS,
    MAX_JSON_SCALARS,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
)
from .errors import PolicyError, refuse
from .framing import FramingCore, TextRequest
from .policy import CompiledPolicy, compile_policy, compile_policy_file
from .profiles import ProviderProfile, resolve_profile
from .transport import (
    HTTPSConnector,
    HTTPSRequest,
    HTTPSResponse,
    TransportRefusal,
    TransportResult,
)


PROVIDER_EVENT_SCHEMA = "model-proxy-provider-event/v1"
PROVIDER_MANIFEST_SCHEMA = "model-proxy-provider-cases/v1"
MAX_PROVIDER_MANIFEST_BYTES = 128 * 1024

_CASE_ID = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?\Z")
_LOWER_HEX = re.compile(r"(?:[0-9a-f]{2})+\Z")
_PROVIDER_REQUEST_FIELDS = frozenset({"schema", "model", "input"})
_PROVIDER_RESPONSE_FIELDS = frozenset({"schema", "output", "usage"})
_USAGE_FIELDS = frozenset({"input_tokens", "output_tokens"})
_MANIFEST_FIELDS = frozenset({"schema", "accepted_job", "cases"})
_CASE_FIELDS = frozenset(
    {
        "id",
        "guest_frame_hex",
        "provider_request",
        "provider_response",
        "guest_response_hex",
    }
)

CredentialSource = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class ProviderEvent:
    """One fixed, content-free observation of the provider boundary."""

    profile: str
    disclosure_state: str
    outcome_family: str
    code: str
    request_bytes: int
    response_bytes: int
    input_tokens: int
    output_tokens: int
    duration_ns: int

    def document(self) -> dict[str, str | int]:
        return {
            "schema": PROVIDER_EVENT_SCHEMA,
            "profile": self.profile,
            "disclosure_state": self.disclosure_state,
            "outcome_family": self.outcome_family,
            "code": self.code,
            "request_bytes": self.request_bytes,
            "response_bytes": self.response_bytes,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "duration_ns": self.duration_ns,
        }


@dataclass(frozen=True, slots=True)
class ProviderManifestResult:
    """Counts and policy identity from the injected provider component vectors."""

    cases: int
    requests: int
    policy_sha256: str


def environment_credential(name: str) -> str:
    """Read one code-owned environment name without retaining a snapshot."""

    if not isinstance(name, str):
        refuse("MP321", "provider.credential")
    try:
        return os.environ[name]
    except (KeyError, TypeError):
        refuse("MP321", "provider.credential")


def _object(value: Any, fields: frozenset[str], code: str, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != fields:
        refuse(code, field_name)
    return value


def provider_request_bytes(profile: ProviderProfile, request: TextRequest) -> bytes:
    """Return the exact mapped input bytes counted by lifecycle admission."""

    if not isinstance(profile, ProviderProfile) or not isinstance(request, TextRequest):
        refuse("MP322", "provider.request")
    return canonical_json(
        {
            "schema": profile.provider_request_schema,
            "model": profile.model,
            "input": request.input_text,
        }
    )


def _contains_secret(value: Any, credential: str) -> bool:
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, str) and credential in current:
            return True
        if isinstance(current, dict):
            pending.extend(current.keys())
            pending.extend(current.values())
        elif isinstance(current, list):
            pending.extend(current)
    return False


def _parse_provider_response(
    raw: bytes,
    profile: ProviderProfile,
    limits: Mapping[str, int],
    request: TextRequest,
    credential: str,
) -> tuple[str, int, int]:
    if credential.encode("ascii") in raw:
        refuse("MP327", "provider.response.secret")
    try:
        value = parse_json_bytes(
            raw,
            max_bytes=limits["max_response_bytes"],
            max_depth=limits["max_json_depth"],
            max_members=limits["max_json_members"],
            max_scalars=min(MAX_JSON_SCALARS, limits["max_json_members"]),
            max_string_bytes=limits["max_string_bytes"],
        )
    except PolicyError:
        refuse("MP323", "provider.response")
    response = _object(
        value,
        _PROVIDER_RESPONSE_FIELDS,
        "MP323",
        "provider.response",
    )
    if response["schema"] != profile.provider_response_schema:
        refuse("MP324", "provider.response.schema")
    output = response["output"]
    if not isinstance(output, str):
        refuse("MP325", "provider.response.output")
    if (
        len(output) > limits["max_output_tokens"]
        or len(output.encode("utf-8")) > limits["max_string_bytes"]
    ):
        refuse("MP325", "provider.response.output")
    usage = _object(
        response["usage"],
        _USAGE_FIELDS,
        "MP323",
        "provider.response.usage",
    )
    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in (input_tokens, output_tokens)
    ):
        refuse("MP325", "provider.response.usage")
    if input_tokens != len(request.input_text) or output_tokens != len(output):
        refuse("MP326", "provider.response.usage")
    if _contains_secret(response, credential):
        refuse("MP327", "provider.response.secret")
    return output, input_tokens, output_tokens


def _outcome_family(code: str) -> str:
    if code == "MP000":
        return "accepted"
    if code == "MP321":
        return "credential"
    if code.startswith("MP30") or code.startswith("MP31"):
        return "transport"
    if code == "MP320":
        return "admission"
    return "provider-response"


class ProviderSession:
    """Own framing admission, provider disclosure, and guest normalisation."""

    def __init__(
        self,
        policy: CompiledPolicy,
        connector: HTTPSConnector,
        *,
        credential_source: CredentialSource = environment_credential,
    ):
        self._framing = FramingCore(policy)
        activation = compile_policy(policy.accepted_job_bytes)
        self._profile = resolve_profile(activation.profile)
        if connector.profile_identifier != self._profile.identifier:
            refuse("MP300", "provider.profile")
        if not callable(credential_source):
            refuse("MP321", "provider.credential")
        self._limits = MappingProxyType(dict(activation.document["limits"]))
        self._state_lock = threading.Lock()
        self._connector: HTTPSConnector | None = connector
        self._credential_source: CredentialSource | None = credential_source
        self._admitted: dict[int, TextRequest] = {}
        self._next_provider_sequence = 1
        self._events: list[ProviderEvent] = []
        self._inflight: TextRequest | None = None
        self._failed = False

    @property
    def events(self) -> tuple[ProviderEvent, ...]:
        with self._state_lock:
            return tuple(self._events)

    @property
    def framing_events(self):
        with self._state_lock:
            return self._framing.events

    def _record_locked(
        self,
        code: str,
        disclosure_state: str,
        *,
        request_bytes: int = 0,
        response_bytes: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        duration_ns: int = 0,
    ) -> None:
        if len(self._events) < self._limits["max_requests"] + 1:
            self._events.append(
                ProviderEvent(
                    profile=self._profile.identifier,
                    disclosure_state=disclosure_state,
                    outcome_family=_outcome_family(code),
                    code=code,
                    request_bytes=request_bytes,
                    response_bytes=response_bytes,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ns=duration_ns,
                )
            )

    def _poison_locked(self) -> None:
        self._failed = True
        self._admitted.clear()
        self._inflight = None

    def feed(self, data: bytes) -> tuple[TextRequest, ...]:
        """Admit guest frames before any credential source can be consulted."""

        with self._state_lock:
            if self._failed:
                refuse("MP320", "provider.session")
            try:
                requests = self._framing.feed(data)
            except PolicyError:
                self._poison_locked()
                raise
            for request in requests:
                self._admitted[request.sequence] = request
            return requests

    def finish(self) -> None:
        with self._state_lock:
            if self._failed:
                refuse("MP320", "provider.session")
            try:
                self._framing.finish()
            except PolicyError:
                self._poison_locked()
                raise

    def generate(self, request: TextRequest, *, timeout_ns: int | None = None) -> bytes:
        """Map one exact admitted request and return one closed guest frame."""

        with self._state_lock:
            if (
                self._failed
                or self._inflight is not None
                or not isinstance(request, TextRequest)
                or self._admitted.get(request.sequence) is not request
                or request.sequence != self._next_provider_sequence
            ):
                self._poison_locked()
                self._record_locked("MP320", "not-read")
                refuse("MP320", "provider.admission")
            if timeout_ns is not None and (
                isinstance(timeout_ns, bool)
                or not isinstance(timeout_ns, int)
                or timeout_ns < 1
            ):
                self._poison_locked()
                self._record_locked("MP320", "not-read")
                refuse("MP320", "provider.deadline")
            credential_source = self._credential_source
            if credential_source is None:
                self._poison_locked()
                self._record_locked("MP320", "not-read")
                refuse("MP320", "provider.session")
            self._inflight = request

        try:
            try:
                credential = credential_source(
                    self._profile.credential_environment
                )
            except Exception:
                with self._state_lock:
                    code = (
                        "MP320"
                        if self._inflight is not request
                        or self._credential_source is None
                        else "MP321"
                    )
                    self._poison_locked()
                    self._record_locked(
                        code, "not-read", input_tokens=len(request.input_text)
                    )
                refuse(code, "provider.credential")

            with self._state_lock:
                connector = self._connector
                if (
                    self._failed
                    or self._inflight is not request
                    or connector is None
                ):
                    self._poison_locked()
                    self._record_locked(
                        "MP320", "not-read", input_tokens=len(request.input_text)
                    )
                    refuse("MP320", "provider.session")

            try:
                body = provider_request_bytes(self._profile, request)
                if len(body) > self._limits["max_request_bytes"]:
                    refuse("MP322", "provider.request.bytes")
                result = connector.send(
                    body,
                    credential,
                    max_response_bytes=self._limits["max_response_bytes"],
                    timeout_seconds=(
                        None if timeout_ns is None else timeout_ns / 1_000_000_000
                    ),
                )
                output, input_tokens, output_tokens = _parse_provider_response(
                    result.body,
                    self._profile,
                    self._limits,
                    request,
                    credential,
                )
            except PolicyError as error:
                transport = locals().get("result")
                if isinstance(error, TransportRefusal):
                    request_bytes = error.request_bytes
                    response_bytes = error.response_bytes
                    duration_ns = error.duration_ns
                elif isinstance(transport, TransportResult):
                    request_bytes = transport.request_bytes
                    response_bytes = transport.response_bytes
                    duration_ns = transport.duration_ns
                else:
                    request_bytes = 0
                    response_bytes = 0
                    duration_ns = 0
                with self._state_lock:
                    self._poison_locked()
                    self._record_locked(
                        error.code,
                        "provider-only",
                        request_bytes=request_bytes,
                        response_bytes=response_bytes,
                        input_tokens=len(request.input_text),
                        duration_ns=duration_ns,
                    )
                raise

            with self._state_lock:
                if (
                    self._failed
                    or self._inflight is not request
                    or self._admitted.get(request.sequence) is not request
                ):
                    self._poison_locked()
                    self._record_locked(
                        "MP320",
                        "provider-only",
                        request_bytes=result.request_bytes,
                        response_bytes=result.response_bytes,
                        input_tokens=input_tokens,
                        duration_ns=result.duration_ns,
                    )
                    refuse("MP320", "provider.session")
                try:
                    guest_response = self._framing.encode_response(request, output)
                except PolicyError as error:
                    self._poison_locked()
                    self._record_locked(
                        error.code,
                        "provider-only",
                        request_bytes=result.request_bytes,
                        response_bytes=result.response_bytes,
                        input_tokens=input_tokens,
                        duration_ns=result.duration_ns,
                    )
                    raise
                del self._admitted[request.sequence]
                self._inflight = None
                self._next_provider_sequence += 1
                self._record_locked(
                    "MP000",
                    "provider-only",
                    request_bytes=result.request_bytes,
                    response_bytes=result.response_bytes,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ns=result.duration_ns,
                )
                return guest_response
        finally:
            if "credential" in locals():
                credential = ""

    def close(self) -> None:
        """Erase provider authority and make every later operation refuse."""

        with self._state_lock:
            self._failed = True
            self._admitted.clear()
            self._inflight = None
            self._credential_source = None
            self._connector = None


class _BufferedResponse:
    def __init__(
        self,
        body: bytes,
        *,
        peer_address: str,
        status: int = 200,
    ):
        self.status = status
        self.headers = (
            ("Content-Length", str(len(body))),
            ("Content-Type", "application/json"),
        )
        self.peer_address = peer_address
        self._body = body
        self._position = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        chunk = self._body[self._position : self._position + size]
        self._position += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class _FixtureExchange:
    def __init__(
        self,
        profile: ProviderProfile,
        credential: str,
        expected_body: bytes,
        response_body: bytes,
        address: str,
    ):
        self._profile = profile
        self._credential = credential
        self._expected_body = expected_body
        self._response_body = response_body
        self._address = address
        self.seen = False
        self.response: _BufferedResponse | None = None

    def __call__(self, request: HTTPSRequest, _context, _timeout) -> HTTPSResponse:
        if (
            request.scheme != self._profile.scheme
            or request.hostname != self._profile.hostname
            or request.port != self._profile.port
            or request.address != self._address
            or request.path != self._profile.path_family
            or request.method != self._profile.method
            or request.body != self._expected_body
            or request.header("Authorization")
            != f"{self._profile.authorization_scheme} {self._credential}"
            or request.header("Accept") != "application/json"
            or request.header("Content-Encoding") != "identity"
            or request.header("Content-Type") != "application/json"
        ):
            refuse("MP328", "provider.manifest.request")
        self.seen = True
        self.response = _BufferedResponse(
            self._response_body, peer_address=self._address
        )
        return self.response


def _hex_bytes(value: Any, field_name: str) -> bytes:
    if not isinstance(value, str) or _LOWER_HEX.fullmatch(value) is None:
        refuse("MP328", field_name)
    try:
        return bytes.fromhex(value)
    except ValueError:
        refuse("MP328", field_name)


def check_provider_manifest(path: str | Path) -> ProviderManifestResult:
    """Exercise exact provider mappings through an injected in-process exchange."""

    try:
        manifest_path = Path(path)
    except (OSError, TypeError, ValueError):
        refuse("MP328", "provider.manifest.path")
    try:
        value = parse_json_bytes(
            read_bounded_file(manifest_path, MAX_PROVIDER_MANIFEST_BYTES),
            max_bytes=MAX_PROVIDER_MANIFEST_BYTES,
            max_members=MAX_JSON_MEMBERS,
        )
    except PolicyError:
        refuse("MP328", "provider.manifest")
    manifest = _object(
        value, _MANIFEST_FIELDS, "MP328", "provider.manifest"
    )
    if (
        manifest["schema"] != PROVIDER_MANIFEST_SCHEMA
        or manifest["accepted_job"] != "accepted-job.json"
    ):
        refuse("MP328", "provider.manifest")
    cases = manifest["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 16:
        refuse("MP328", "provider.manifest.cases")

    policy = compile_policy_file(str(manifest_path.parent / "accepted-job.json"))
    profile = resolve_profile(policy.profile)
    address = "8.8.8.8"
    seen_ids: set[str] = set()
    requests = 0
    for case_value in cases:
        case = _object(
            case_value, _CASE_FIELDS, "MP328", "provider.manifest.case"
        )
        identifier = case["id"]
        if (
            not isinstance(identifier, str)
            or _CASE_ID.fullmatch(identifier) is None
            or identifier in seen_ids
        ):
            refuse("MP328", "provider.manifest.case")
        seen_ids.add(identifier)
        guest_frame = _hex_bytes(
            case["guest_frame_hex"], "provider.manifest.guest_frame"
        )
        expected_guest = _hex_bytes(
            case["guest_response_hex"], "provider.manifest.guest_response"
        )
        expected_request = _object(
            case["provider_request"],
            _PROVIDER_REQUEST_FIELDS,
            "MP328",
            "provider.manifest.provider_request",
        )
        provider_response = _object(
            case["provider_response"],
            _PROVIDER_RESPONSE_FIELDS,
            "MP328",
            "provider.manifest.provider_response",
        )
        expected_request_bytes = canonical_json(expected_request)
        response_bytes = canonical_json(provider_response)
        credential = secrets.token_urlsafe(32)
        reads = 0

        def source(name: str) -> str:
            nonlocal reads
            if name != profile.credential_environment:
                refuse("MP328", "provider.manifest.credential")
            reads += 1
            return credential

        exchange = _FixtureExchange(
            profile,
            credential,
            expected_request_bytes,
            response_bytes,
            address,
        )
        connector = HTTPSConnector(
            profile,
            resolver=lambda _hostname, _port: (address,),
            exchange=exchange,
            clock=iter((1_000_000, 2_000_000)).__next__,
        )
        session = ProviderSession(
            policy, connector, credential_source=source
        )
        admitted = session.feed(guest_frame)
        session.finish()
        if len(admitted) != 1:
            refuse("MP328", "provider.manifest.admission")
        guest_response = session.generate(admitted[0])
        rendered_events = canonical_json(
            [event.document() for event in session.events]
            + [event.document() for event in session.framing_events]
        )
        if (
            guest_response != expected_guest
            or reads != 1
            or not exchange.seen
            or exchange.response is None
            or not exchange.response.closed
            or credential.encode("ascii") in guest_frame
            or credential.encode("ascii") in guest_response
            or credential.encode("ascii") in rendered_events
        ):
            refuse("MP328", "provider.manifest.result")
        requests += 1
    return ProviderManifestResult(
        cases=len(cases), requests=requests, policy_sha256=policy.policy_sha256
    )
