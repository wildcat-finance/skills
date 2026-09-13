"""Pinned standard-library HTTPS operations for one GitHub issue create."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import http.client
import json
import math
import re
import ssl
from typing import Any, Protocol

from .canonical import MAX_REQUEST_BYTES, canonical_json
from .errors import PublisherError, refuse


GITHUB_API_HOST = "api.github.com"
GITHUB_WEB_ORIGIN = "https://github.com"
GITHUB_REPOSITORY = "wildcat-finance/skills"
INSTALLATION_ID = "157591976"
API_VERSION = "2022-11-28"
HTTPS_PORT = 443
MAX_REMOTE_RESPONSE_BYTES = 8_192
MAX_REMOTE_HEADER_BYTES = 16_384
MAX_REMOTE_MEMBERS = 256
MAX_REMOTE_DEPTH = 8
MAX_REMOTE_STRING_BYTES = 262_144
TOKEN_TIMEOUT_SECONDS = 15.0
CREATE_TIMEOUT_SECONDS = 20.0
READBACK_TIMEOUT_SECONDS = 10.0
TOKEN_ROUTE = f"/app/installations/{INSTALLATION_ID}/access_tokens"
ISSUES_ROUTE = f"/repos/{GITHUB_REPOSITORY}/issues"
ISSUE_ROUTE_RE = re.compile(rf"{re.escape(ISSUES_ROUTE)}/([1-9][0-9]*)\Z")
JWT_RE = re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\Z")
TOKEN_RE = re.compile(r"[!-~]{16,4096}\Z")
EXPIRES_AT_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z"
)


@dataclass(frozen=True, slots=True)
class HTTPSRequest:
    """One request whose authority-bearing values stay out of repr."""

    method: str
    path: str
    headers: tuple[tuple[str, str], ...] = field(repr=False)
    body: bytes = field(repr=False)
    timeout_seconds: float
    max_response_bytes: int


class HTTPSResponse(Protocol):
    status: int
    headers: tuple[tuple[str, str], ...]

    def read(self, size: int) -> bytes: ...

    def close(self) -> None: ...


class Exchange(Protocol):
    def __call__(self, request: HTTPSRequest, context: ssl.SSLContext) -> HTTPSResponse: ...


@dataclass(frozen=True, slots=True)
class TokenGrant:
    token: str = field(repr=False)
    expires_at: int


@dataclass(frozen=True, slots=True)
class IssueRecord:
    number: int
    url: str
    title: str = field(repr=False)
    body: str = field(repr=False)


class _BoundedHeaderReader:
    """Limit response-header bytes before the stdlib parser retains them."""

    def __init__(self, stream: Any):
        self._stream = stream
        self._header_bytes = 0
        self._counting = True
        self._expect_status = True

    def readline(self, size: int = -1) -> bytes:
        if not self._counting:
            line = self._stream.readline(size)
            return line
        if self._expect_status:
            bounded_size = MAX_REMOTE_HEADER_BYTES + 1
            if isinstance(size, int) and size >= 0:
                bounded_size = min(size, bounded_size)
            line = self._stream.readline(bounded_size)
            if len(line) > MAX_REMOTE_HEADER_BYTES:
                refuse("GIP302", "transport.headers")
            self._expect_status = False
            return line
        remaining = MAX_REMOTE_HEADER_BYTES - self._header_bytes
        bounded_size = remaining + 1
        if isinstance(size, int) and size >= 0:
            bounded_size = min(size, bounded_size)
        line = self._stream.readline(bounded_size)
        self._header_bytes += len(line)
        if self._header_bytes > MAX_REMOTE_HEADER_BYTES:
            refuse("GIP302", "transport.headers")
        if line in (b"\r\n", b"\n", b""):
            self._expect_status = True
        return line

    def stop_counting(self) -> None:
        self._counting = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self._stream, name)


class _BoundedHTTPResponse(http.client.HTTPResponse):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.fp = _BoundedHeaderReader(self.fp)

    def begin(self) -> None:
        reader = self.fp
        try:
            super().begin()
        finally:
            reader.stop_counting()


class _LiveResponse:
    def __init__(
        self,
        response: http.client.HTTPResponse,
        connection: http.client.HTTPSConnection,
    ):
        self.status = response.status
        self.headers = tuple(response.getheaders())
        self._response = response
        self._connection = connection

    def read(self, size: int) -> bytes:
        return self._response.read(size)

    def close(self) -> None:
        try:
            self._response.close()
        finally:
            self._connection.close()


def _live_exchange(request: HTTPSRequest, context: ssl.SSLContext) -> HTTPSResponse:
    connection = http.client.HTTPSConnection(
        GITHUB_API_HOST,
        HTTPS_PORT,
        timeout=request.timeout_seconds,
        context=context,
    )
    connection.response_class = _BoundedHTTPResponse
    try:
        connection.request(
            request.method,
            request.path,
            body=request.body,
            headers=dict(request.headers),
        )
        return _LiveResponse(connection.getresponse(), connection)
    except Exception:
        connection.close()
        raise


def _timeout(value: float, ceiling: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or value <= 0
        or value > ceiling
        or not math.isfinite(value)
    ):
        refuse("GIP300", "transport.timeout")
    return float(value)


def _headers(values: tuple[tuple[str, str], ...]) -> None:
    if not isinstance(values, tuple) or len(values) > 32:
        refuse("GIP302", "transport.headers")
    seen: set[str] = set()
    total = 0
    for pair in values:
        if not isinstance(pair, tuple) or len(pair) != 2:
            refuse("GIP302", "transport.headers")
        name, value = pair
        if not isinstance(name, str) or not isinstance(value, str):
            refuse("GIP302", "transport.headers")
        lowered = name.casefold()
        if not name or lowered in seen or any(char in "\r\n" for char in name + value):
            refuse("GIP302", "transport.headers")
        seen.add(lowered)
        try:
            total += len(name.encode("ascii", "strict")) + len(
                value.encode("ascii", "strict")
            )
        except UnicodeEncodeError:
            refuse("GIP302", "transport.headers")
    if total > MAX_REMOTE_HEADER_BYTES:
        refuse("GIP302", "transport.headers")


def _shape(value: Any, *, depth: int = 0) -> int:
    if depth > MAX_REMOTE_DEPTH:
        refuse("GIP307", "transport.response")
    if value is None or isinstance(value, (bool, int)):
        return 0
    if isinstance(value, float):
        refuse("GIP307", "transport.response")
    if isinstance(value, str):
        if len(value.encode("utf-8")) > MAX_REMOTE_STRING_BYTES:
            refuse("GIP307", "transport.response")
        return 0
    if isinstance(value, list):
        if len(value) > MAX_REMOTE_MEMBERS:
            refuse("GIP307", "transport.response")
        return len(value) + sum(_shape(item, depth=depth + 1) for item in value)
    if isinstance(value, dict):
        if len(value) > MAX_REMOTE_MEMBERS:
            refuse("GIP307", "transport.response")
        return len(value) + sum(_shape(item, depth=depth + 1) for item in value.values())
    refuse("GIP307", "transport.response")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            refuse("GIP303", "transport.response.duplicate")
        result[key] = value
    return result


def _json_document(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=lambda _value: refuse("GIP307", "transport.response"),
            parse_constant=lambda _value: refuse("GIP307", "transport.response"),
        )
    except PublisherError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PublisherError("GIP307", "transport.response") from exc
    if not isinstance(value, dict) or _shape(value) > MAX_REMOTE_MEMBERS:
        refuse("GIP307", "transport.response")
    return value


def _read_response(
    response: HTTPSResponse,
    *,
    expected_status: int,
    max_bytes: int,
) -> bytes:
    failure: PublisherError | None = None
    body = b""
    try:
        status = response.status
        if isinstance(status, bool) or not isinstance(status, int):
            refuse("GIP305", "transport.status")
        _headers(response.headers)
        if 300 <= status <= 399:
            refuse("GIP304", "transport.redirect")
        if status != expected_status:
            refuse("GIP305", "transport.status")
        lengths = [
            value
            for name, value in response.headers
            if name.casefold() == "content-length"
        ]
        if lengths:
            try:
                declared = int(lengths[0], 10)
            except ValueError:
                refuse("GIP302", "transport.content-length")
            if declared < 0 or declared > max_bytes:
                refuse("GIP306", "transport.response.bytes")
        chunks: list[bytes] = []
        length = 0
        while True:
            chunk = response.read(min(4_096, max_bytes - length + 1))
            if not isinstance(chunk, bytes):
                refuse("GIP307", "transport.response")
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
            if length > max_bytes:
                refuse("GIP306", "transport.response.bytes")
        body = b"".join(chunks)
        if not body:
            refuse("GIP307", "transport.response")
    except PublisherError as exc:
        failure = exc
    except (OSError, TimeoutError, http.client.HTTPException):
        failure = PublisherError("GIP301", "transport.read")
    except Exception:
        failure = PublisherError("GIP301", "transport.read")
    finally:
        try:
            response.close()
        except Exception:
            failure = PublisherError("GIP309", "transport.response.close")
    if failure is not None:
        raise failure
    return body


class PinnedGitHubTransport:
    """Reach only the code-owned GitHub API host, routes, and TLS context."""

    def __init__(self, exchange: Exchange = _live_exchange):
        if not callable(exchange):
            refuse("GIP300", "transport.exchange")
        self._exchange = exchange
        self._context = ssl.create_default_context()

    def request(
        self,
        *,
        method: str,
        path: str,
        headers: tuple[tuple[str, str], ...],
        body: bytes,
        timeout_seconds: float,
        max_response_bytes: int = MAX_REMOTE_RESPONSE_BYTES,
    ) -> dict[str, Any]:
        allowed = (
            (method == "POST" and path in {TOKEN_ROUTE, ISSUES_ROUTE})
            or (method == "GET" and ISSUE_ROUTE_RE.fullmatch(path) is not None)
        )
        if not allowed:
            refuse("GIP300", "transport.destination")
        if (
            not isinstance(body, bytes)
            or len(body) > MAX_REQUEST_BYTES
            or isinstance(max_response_bytes, bool)
            or not isinstance(max_response_bytes, int)
            or max_response_bytes < 1
            or max_response_bytes > MAX_REMOTE_RESPONSE_BYTES
        ):
            refuse("GIP300", "transport.request")
        _headers(headers)
        request = HTTPSRequest(
            method=method,
            path=path,
            headers=headers,
            body=body,
            timeout_seconds=_timeout(
                timeout_seconds,
                {
                    TOKEN_ROUTE: TOKEN_TIMEOUT_SECONDS,
                    ISSUES_ROUTE: CREATE_TIMEOUT_SECONDS,
                }.get(path, READBACK_TIMEOUT_SECONDS),
            ),
            max_response_bytes=max_response_bytes,
        )
        try:
            response = self._exchange(request, self._context)
        except PublisherError:
            raise
        except (OSError, TimeoutError, http.client.HTTPException, ssl.SSLError) as exc:
            raise PublisherError("GIP301", "transport.exchange") from exc
        except Exception as exc:
            raise PublisherError("GIP301", "transport.exchange") from exc
        expected_status = 201 if method == "POST" else 200
        return _json_document(
            _read_response(
                response,
                expected_status=expected_status,
                max_bytes=max_response_bytes,
            )
        )

    def close(self) -> None:
        """Each request owns and closes its own connection."""


def _base_headers(authorization: str | None) -> tuple[tuple[str, str], ...]:
    values = [
        ("Accept", "application/vnd.github+json"),
        ("User-Agent", "wildcat-github-issue-publisher/1"),
        ("X-GitHub-Api-Version", API_VERSION),
    ]
    if authorization is not None:
        values.append(("Authorization", authorization))
    return tuple(values)


def exchange_installation_token(
    jwt: str,
    transport: PinnedGitHubTransport,
    *,
    now: int,
    timeout_seconds: float,
) -> TokenGrant:
    if not isinstance(jwt, str) or JWT_RE.fullmatch(jwt) is None:
        refuse("GIP310", "token.jwt")
    body = canonical_json(
        {"permissions": {"issues": "write"}, "repositories": ["skills"]}
    )
    document = transport.request(
        method="POST",
        path=TOKEN_ROUTE,
        headers=_base_headers(f"Bearer {jwt}") + (("Content-Type", "application/json"),),
        body=body,
        timeout_seconds=timeout_seconds,
    )
    token = document.get("token")
    expires_at = document.get("expires_at")
    permissions = document.get("permissions")
    selection = document.get("repository_selection")
    repositories = document.get("repositories")
    if not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None:
        refuse("GIP310", "token.value")
    if not isinstance(expires_at, str) or EXPIRES_AT_RE.fullmatch(expires_at) is None:
        refuse("GIP310", "token.expiry")
    try:
        expiry = int(datetime.fromisoformat(expires_at.replace("Z", "+00:00")).timestamp())
    except (OverflowError, ValueError):
        refuse("GIP310", "token.expiry")
    if expiry <= now + 30 or expiry > now + 3_660:
        refuse("GIP310", "token.expiry")
    if permissions != {"issues": "write"} or selection != "selected":
        refuse("GIP311", "token.scope")
    if (
        not isinstance(repositories, list)
        or len(repositories) != 1
        or not isinstance(repositories[0], dict)
        or repositories[0].get("full_name") != GITHUB_REPOSITORY
    ):
        refuse("GIP311", "token.repository")
    return TokenGrant(token=token, expires_at=expiry)


def _issue(document: dict[str, Any], title: str, body: str) -> IssueRecord:
    number = document.get("number")
    url = document.get("html_url")
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        refuse("GIP320", "issue.number")
    expected_url = f"{GITHUB_WEB_ORIGIN}/{GITHUB_REPOSITORY}/issues/{number}"
    if url != expected_url:
        refuse("GIP320", "issue.origin")
    if document.get("title") != title or document.get("body") != body:
        refuse("GIP321", "issue.bytes")
    return IssueRecord(number=number, url=expected_url, title=title, body=body)


def create_issue(
    token: str,
    *,
    title: str,
    body: str,
    labels: tuple[str, ...],
    transport: PinnedGitHubTransport,
    timeout_seconds: float,
) -> IssueRecord:
    if not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None:
        refuse("GIP310", "token.value")
    request_body = canonical_json({"body": body, "labels": list(labels), "title": title})
    document = transport.request(
        method="POST",
        path=ISSUES_ROUTE,
        headers=_base_headers(f"token {token}") + (("Content-Type", "application/json"),),
        body=request_body,
        timeout_seconds=timeout_seconds,
    )
    return _issue(document, title, body)


def read_issue(
    issue: IssueRecord,
    *,
    title: str,
    body: str,
    token: str | None,
    transport: PinnedGitHubTransport,
    timeout_seconds: float,
) -> IssueRecord:
    if token is not None and (not isinstance(token, str) or TOKEN_RE.fullmatch(token) is None):
        refuse("GIP310", "token.value")
    document = transport.request(
        method="GET",
        path=f"{ISSUES_ROUTE}/{issue.number}",
        headers=_base_headers(None if token is None else f"token {token}"),
        body=b"",
        timeout_seconds=timeout_seconds,
    )
    observed = _issue(document, title, body)
    if observed.number != issue.number or observed.url != issue.url:
        refuse("GIP320", "issue.identity")
    return observed
