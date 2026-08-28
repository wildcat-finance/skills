"""Pinned standard-library HTTPS transport for the model proxy provider boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
import http.client
import ipaddress
import itertools
import math
import re
import socket
import ssl
import threading
import time
from typing import Callable, Iterable, Protocol
from urllib.parse import urlsplit

from .errors import PolicyError, refuse
from .profiles import ProviderProfile, resolve_profile


HTTPS_PORT = 443
MAX_CREDENTIAL_BYTES = 512
MAX_HEADER_BYTES = 16 * 1024
MAX_HEADER_FIELDS = 32
READ_CHUNK_BYTES = 8 * 1024
TRANSPORT_TIMEOUT_SECONDS = 30.0

_CREDENTIAL = re.compile(r"[A-Za-z0-9._~-]{16,512}\Z")
_HEADER_NAME = re.compile(r"[A-Za-z0-9!#$%&'*+.^_`|~-]+\Z")
_CONTENT_LENGTH = re.compile(r"0|[1-9][0-9]*\Z")
_EXPECTED_RESPONSE_HEADERS = frozenset(
    {"content-encoding", "content-length", "content-type", "transfer-encoding"}
)


def _bounded_timeout(value: int | float | None, ceiling: float) -> float:
    if value is None:
        return ceiling
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        refuse("MP300", "provider.request")
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        refuse("MP300", "provider.request")
    if converted <= 0 or not math.isfinite(converted):
        refuse("MP300", "provider.request")
    return min(ceiling, converted)


@dataclass(frozen=True, slots=True)
class HTTPSRequest:
    """One code-owned request with authority-bearing fields hidden from repr."""

    scheme: str
    hostname: str
    port: int
    address: str
    method: str
    path: str
    headers: tuple[tuple[str, str], ...] = field(repr=False)
    body: bytes = field(repr=False)

    def header(self, name: str) -> str | None:
        """Return one internally constructed header without accepting guest names."""

        lowered = name.lower()
        for field_name, value in self.headers:
            if field_name.lower() == lowered:
                return value
        return None


class HTTPSResponse(Protocol):
    """Minimum streaming response surface accepted from an exchange adapter."""

    status: int
    headers: tuple[tuple[str, str], ...]
    peer_address: str

    def read(self, size: int) -> bytes: ...

    def close(self) -> None: ...


Resolver = Callable[[str, int], Iterable[str]]
Exchange = Callable[[HTTPSRequest, ssl.SSLContext, float], HTTPSResponse]
Clock = Callable[[], int]


@dataclass(frozen=True, slots=True)
class TransportResult:
    """Bounded body and content-free measurements from one HTTPS exchange."""

    body: bytes = field(repr=False)
    request_bytes: int
    response_bytes: int
    duration_ns: int


@dataclass(frozen=True, slots=True)
class TransportRefusal(PolicyError):
    """A value-free refusal with confirmed content-free transport progress."""

    request_bytes: int
    response_bytes: int
    duration_ns: int


def system_resolver(hostname: str, port: int) -> tuple[str, ...]:
    """Resolve one fixed hostname without carrying aliases into the connector."""

    records = socket.getaddrinfo(
        hostname,
        port,
        family=socket.AF_UNSPEC,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    return tuple(record[4][0] for record in records)


def _strict_context() -> ssl.SSLContext:
    # create_default_context honours SSLKEYLOGFILE, which would let ambient
    # process state select an output path for provider traffic secrets.
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.verify_flags |= (
        ssl.VERIFY_X509_PARTIAL_CHAIN | ssl.VERIFY_X509_STRICT
    )
    context.load_default_certs(ssl.Purpose.SERVER_AUTH)
    return context


def _safe_address(value: object) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if not isinstance(value, str):
        refuse("MP302", "provider.address")
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        refuse("MP302", "provider.address")
    if (
        not address.is_global
        or address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        refuse("MP302", "provider.address")
    return address


def _resolve_one(
    resolver: Resolver, hostname: str, port: int
) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        answers = resolver(hostname, port)
        if isinstance(answers, (str, bytes)):
            refuse("MP301", "provider.resolution")
        bounded = tuple(itertools.islice(iter(answers), 3))
    except PolicyError:
        raise
    except Exception:
        refuse("MP301", "provider.resolution")
    if not bounded:
        refuse("MP301", "provider.resolution")
    addresses = {_safe_address(answer) for answer in bounded}
    if len(bounded) > 2 or len(addresses) != 1:
        refuse("MP303", "provider.resolution")
    return next(iter(addresses))


def _validate_profile(profile: ProviderProfile) -> None:
    if type(profile) is not ProviderProfile:
        refuse("MP300", "provider.profile")
    try:
        canonical = resolve_profile(profile.identifier)
    except PolicyError:
        refuse("MP300", "provider.profile")
    if profile != canonical:
        refuse("MP300", "provider.profile")
    origin = urlsplit(profile.origin_family)
    if (
        profile.scheme != "https"
        or profile.port != HTTPS_PORT
        or origin.scheme != profile.scheme
        or origin.hostname != profile.hostname
        or origin.port not in (None, HTTPS_PORT)
        or origin.username is not None
        or origin.password is not None
        or origin.path not in ("", "/")
        or origin.query
        or origin.fragment
        or profile.method != "POST"
        or not profile.path_family.startswith("/")
        or profile.path_family.startswith("//")
        or "?" in profile.path_family
        or "#" in profile.path_family
        or profile.authorization_scheme != "Bearer"
    ):
        refuse("MP300", "provider.profile")


def _request_headers(profile: ProviderProfile, credential: str) -> tuple[tuple[str, str], ...]:
    if (
        not isinstance(credential, str)
        or len(credential.encode("utf-8", errors="ignore")) > MAX_CREDENTIAL_BYTES
        or _CREDENTIAL.fullmatch(credential) is None
    ):
        refuse("MP321", "provider.credential")
    return (
        ("Accept", "application/json"),
        ("Authorization", f"{profile.authorization_scheme} {credential}"),
        ("Content-Encoding", "identity"),
        ("Content-Type", "application/json"),
    )


def _response_headers(
    values: object, max_response_bytes: int
) -> tuple[int | None, bool]:
    if not isinstance(values, tuple) or len(values) > MAX_HEADER_FIELDS:
        refuse("MP309", "provider.response.headers")
    parsed: dict[str, str] = {}
    total = 0
    for item in values:
        if not isinstance(item, tuple) or len(item) != 2:
            refuse("MP309", "provider.response.headers")
        name, value = item
        if (
            not isinstance(name, str)
            or not isinstance(value, str)
            or _HEADER_NAME.fullmatch(name) is None
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
        ):
            refuse("MP309", "provider.response.headers")
        lowered = name.lower()
        if lowered in parsed or lowered not in _EXPECTED_RESPONSE_HEADERS:
            refuse("MP309", "provider.response.headers")
        parsed[lowered] = value
        total += len(name.encode("ascii")) + len(value.encode("utf-8")) + 4
        if total > MAX_HEADER_BYTES:
            refuse("MP309", "provider.response.headers")

    if parsed.get("content-type") != "application/json":
        refuse("MP311", "provider.response.content_type")
    if parsed.get("content-encoding", "identity") != "identity":
        refuse("MP311", "provider.response.content_encoding")
    transfer = parsed.get("transfer-encoding")
    if transfer not in (None, "chunked"):
        refuse("MP311", "provider.response.transfer_encoding")
    raw_length = parsed.get("content-length")
    if raw_length is not None and transfer is not None:
        refuse("MP309", "provider.response.headers")
    declared: int | None = None
    if raw_length is not None:
        if _CONTENT_LENGTH.fullmatch(raw_length) is None:
            refuse("MP309", "provider.response.content_length")
        declared = int(raw_length)
        if declared > max_response_bytes:
            refuse("MP310", "provider.response.bytes")
    return declared, transfer == "chunked"


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Connect to one resolved address while retaining the fixed TLS hostname."""

    def __init__(
        self,
        hostname: str,
        port: int,
        address: str,
        *,
        timeout: float,
        context: ssl.SSLContext,
    ):
        super().__init__(hostname, port=port, timeout=timeout, context=context)
        self._pinned_address = address

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._pinned_address, self.port), self.timeout, self.source_address
        )
        try:
            self.sock = self._context.wrap_socket(
                raw_socket, server_hostname=self.host
            )
        except BaseException:
            raw_socket.close()
            raise


class _HTTPResponseHandle:
    def __init__(
        self,
        response: http.client.HTTPResponse,
        connection: _PinnedHTTPSConnection,
        peer_address: str,
    ):
        self.status = response.status
        self.headers = tuple(response.headers.raw_items())
        self.peer_address = peer_address
        self._response = response
        self._connection = connection

    def read(self, size: int) -> bytes:
        return self._response.read(size)

    def close(self) -> None:
        try:
            self._response.close()
        finally:
            self._connection.close()


def stdlib_exchange(
    request: HTTPSRequest, context: ssl.SSLContext, timeout: float
) -> HTTPSResponse:
    """Perform one direct POST with no proxy, CONNECT, or redirect machinery."""

    connection = _PinnedHTTPSConnection(
        request.hostname,
        request.port,
        request.address,
        timeout=timeout,
        context=context,
    )
    try:
        connection.putrequest(
            request.method,
            request.path,
            skip_host=True,
            skip_accept_encoding=True,
        )
        connection.putheader("Host", request.hostname)
        for name, value in request.headers:
            connection.putheader(name, value)
        connection.putheader("Content-Length", str(len(request.body)))
        connection.endheaders(request.body)
        response = connection.getresponse()
        if connection.sock is None:
            raise OSError("connection unavailable")
        peer = connection.sock.getpeername()[0]
        return _HTTPResponseHandle(response, connection, peer)
    except BaseException:
        connection.close()
        raise


class HTTPSConnector:
    """Resolve once, pin one global address, and validate one bounded response."""

    def __init__(
        self,
        profile: ProviderProfile,
        *,
        resolver: Resolver = system_resolver,
        exchange: Exchange = stdlib_exchange,
        context_factory: Callable[[], ssl.SSLContext] = _strict_context,
        clock: Clock = time.monotonic_ns,
        timeout: float = TRANSPORT_TIMEOUT_SECONDS,
    ):
        _validate_profile(profile)
        if not callable(resolver) or not callable(exchange) or not callable(clock):
            refuse("MP300", "provider.transport")
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
            refuse("MP300", "provider.transport")
        try:
            context = context_factory()
        except Exception:
            refuse("MP305", "provider.tls")
        if (
            not isinstance(context, ssl.SSLContext)
            or not context.check_hostname
            or context.verify_mode != ssl.CERT_REQUIRED
        ):
            refuse("MP305", "provider.tls")
        self._profile = profile
        self._resolver = resolver
        self._exchange = exchange
        self._context = context
        self._clock = clock
        self._timeout = float(timeout)
        self._pinned_address: ipaddress.IPv4Address | ipaddress.IPv6Address | None = None
        self._pin_lock = threading.Lock()

    @property
    def profile_identifier(self) -> str:
        return self._profile.identifier

    def _job_address(self) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        address = self._pinned_address
        if address is not None:
            return address
        with self._pin_lock:
            address = self._pinned_address
            if address is None:
                address = _resolve_one(
                    self._resolver, self._profile.hostname, self._profile.port
                )
                self._pinned_address = address
        return address

    def _failure_duration(self, started: object) -> int:
        if isinstance(started, bool) or not isinstance(started, int):
            return 0
        try:
            finished = self._clock()
        except Exception:
            return 0
        if (
            isinstance(finished, bool)
            or not isinstance(finished, int)
            or finished < started
        ):
            return 0
        return finished - started

    def send(
        self,
        body: bytes,
        credential: str,
        *,
        max_response_bytes: int,
        timeout_seconds: float | None = None,
    ) -> TransportResult:
        """Send one internally mapped request and retain no authority-bearing value."""

        if (
            not isinstance(body, bytes)
            or not body
            or isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or max_response_bytes < 1
            or max_response_bytes > self._profile.limit_ceilings["max_response_bytes"]
        ):
            refuse("MP300", "provider.request")
        request_timeout = _bounded_timeout(timeout_seconds, self._timeout)
        headers = _request_headers(self._profile, credential)
        address = self._job_address()
        request = HTTPSRequest(
            scheme=self._profile.scheme,
            hostname=self._profile.hostname,
            port=self._profile.port,
            address=str(address),
            method=self._profile.method,
            path=self._profile.path_family,
            headers=headers,
            body=body,
        )
        response: HTTPSResponse | None = None
        started: object = None
        request_handed_to_exchange = False
        length = 0
        failure: PolicyError | None = None
        failure_duration = 0
        try:
            started = self._clock()
            request_handed_to_exchange = True
            response = self._exchange(request, self._context, request_timeout)
            if (
                isinstance(response.status, bool)
                or not isinstance(response.status, int)
            ):
                refuse("MP308", "provider.response.status")
            try:
                peer = _safe_address(response.peer_address)
            except AttributeError:
                refuse("MP304", "provider.response.peer")
            if peer != address:
                refuse("MP304", "provider.response.peer")
            if 300 <= response.status <= 399:
                refuse("MP307", "provider.response.status")
            if response.status != 200:
                refuse("MP308", "provider.response.status")
            declared, _chunked = _response_headers(
                response.headers, max_response_bytes
            )
            chunks: list[bytes] = []
            while True:
                read_limit = min(
                    READ_CHUNK_BYTES, max_response_bytes - length + 1
                )
                chunk = response.read(read_limit)
                if not isinstance(chunk, bytes):
                    refuse("MP310", "provider.response.bytes")
                length += len(chunk)
                if len(chunk) > read_limit or length > max_response_bytes:
                    refuse("MP310", "provider.response.bytes")
                if not chunk:
                    break
                chunks.append(chunk)
            if declared is not None and declared != length:
                refuse("MP310", "provider.response.bytes")
            finished = self._clock()
            if (
                isinstance(started, bool)
                or isinstance(finished, bool)
                or not isinstance(started, int)
                or not isinstance(finished, int)
                or finished < started
            ):
                refuse("MP306", "provider.duration")
            return TransportResult(
                body=b"".join(chunks),
                request_bytes=len(body),
                response_bytes=length,
                duration_ns=finished - started,
            )
        except PolicyError as error:
            failure = error
            failure_duration = self._failure_duration(started)
        except (ssl.CertificateError, ssl.SSLError):
            failure = PolicyError("MP305", "provider.tls")
            failure_duration = self._failure_duration(started)
        except Exception:
            failure = PolicyError("MP306", "provider.transport")
            failure_duration = self._failure_duration(started)
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
        if failure is None:
            refuse("MP306", "provider.transport")
        if response is not None or request_handed_to_exchange:
            raise TransportRefusal(
                failure.code,
                failure.field,
                len(body),
                length,
                failure_duration,
            ) from None
        raise failure from None
