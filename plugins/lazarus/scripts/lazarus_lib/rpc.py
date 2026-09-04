"""Small fail-closed JSON-RPC client used only by capture."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import re
import signal
from threading import current_thread, main_thread
from typing import Any, Mapping
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .canonical import dumps, loads
from .errors import FormatError, LazarusError, ResourceLimitError
from .limits import CaptureLimits
from .scrub import sanitised_rpc_error
from .version import __version__

# Public archive endpoints that serve deep state proofs cap how many calls
# one JSON-RPC batch may carry, and answer an over-long batch with a
# transport error rather than a per-call one. Capture therefore splits a
# plan into provider-sized chunks instead of posting it as a single batch.
DEFAULT_MAX_BATCH_SIZE = 3


class RpcTransportError(LazarusError):
    """A safe provider transport or protocol failure."""


class _RpcDeadlineExpired(BaseException):
    """Private cancellation signal normalised at the transport boundary."""


RESPONSE_READ_CHUNK_BYTES = 64 * 1024


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class RpcOutcome:
    result: Any = None
    error: dict[str, Any] | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


class JsonRpcClient:
    def __init__(
        self,
        url: str,
        limits: CaptureLimits,
        *,
        headers: Mapping[str, str] | None = None,
        opener: Any = None,
        max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
    ) -> None:
        if max_batch_size < 1:
            raise ValueError("max_batch_size must be positive")
        self._url = _http_rpc_url(url)
        self._limits = limits
        self._max_batch_size = max_batch_size
        # Several public archive endpoints reject urllib's default agent
        # outright, so a capture cannot reach them without naming itself.
        # The agent is a transport detail and never a fixture component.
        self._headers = {
            "Content-Type": "application/json",
            "User-Agent": f"lazarus/{__version__}",
        }
        self._headers.update(headers or {})
        self._opener = opener or build_opener(ProxyHandler({}), _RejectRedirects())
        self._next_id = 1

    def call(self, method: str, params: list[Any] | dict[str, Any]) -> Any:
        outcome = self.request_many([(method, params)])[0]
        if outcome.error is not None:
            raise RpcTransportError(f"provider rejected JSON-RPC method {method}")
        return outcome.result

    def request_many(
        self,
        calls: list[tuple[str, list[Any] | dict[str, Any]]],
    ) -> list[RpcOutcome]:
        if not calls:
            return []
        size = self._max_batch_size
        if len(calls) <= size:
            return self._request_chunk(calls)
        outcomes: list[RpcOutcome] = []
        for start in range(0, len(calls), size):
            outcomes.extend(self._request_chunk(calls[start : start + size]))
        return outcomes

    def _request_chunk(
        self,
        calls: list[tuple[str, list[Any] | dict[str, Any]]],
    ) -> list[RpcOutcome]:
        requests = []
        identifiers = []
        for method, params in calls:
            identifier = self._next_id
            self._next_id += 1
            identifiers.append(identifier)
            requests.append(
                {"jsonrpc": "2.0", "id": identifier, "method": method, "params": params}
            )
        self._limits.before_request(len(requests))
        payload: Any = requests[0] if len(requests) == 1 else requests
        parsed = self._post(dumps(payload))
        is_batch = len(requests) > 1
        if is_batch and not isinstance(parsed, list):
            raise FormatError("provider JSON-RPC batch response must be an array")
        if not is_batch and not isinstance(parsed, dict):
            raise FormatError("provider JSON-RPC single response must be an object")
        responses = parsed if is_batch else [parsed]
        identifier_set = set(identifiers)
        by_id: dict[int, RpcOutcome] = {}
        for response in responses:
            self._limits.check_time()
            if not isinstance(response, dict):
                raise FormatError("provider JSON-RPC response must be an object")
            if response.get("jsonrpc") != "2.0":
                raise FormatError("provider JSON-RPC response has the wrong version")
            identifier = response.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool):
                raise FormatError("provider JSON-RPC response has an invalid id")
            if identifier not in identifier_set or identifier in by_id:
                raise FormatError(
                    "provider JSON-RPC response has an unknown or duplicate id"
                )
            has_result = "result" in response
            has_error = "error" in response
            if has_result == has_error:
                raise FormatError("provider JSON-RPC response needs exactly one outcome")
            by_id[identifier] = (
                RpcOutcome(result=response["result"])
                if has_result
                else RpcOutcome(error=sanitised_rpc_error(response["error"]))
            )
        if set(by_id) != identifier_set:
            raise FormatError("provider JSON-RPC batch response is incomplete")
        self._limits.check_time()
        return [by_id[identifier] for identifier in identifiers]

    def _post(self, body: bytes) -> Any:
        limit = self._limits.response_read_limit()
        declared_size_value: int | None = None
        deadline_expired = False
        try:
            with _transport_deadline(self._limits):
                request = Request(
                    self._url, data=body, headers=self._headers, method="POST"
                )
                with self._opener.open(
                    request,
                    timeout=self._limits.remaining_seconds(),
                ) as response:
                    declared_size_value = _declared_content_length(response.headers)
                    if declared_size_value is not None:
                        if declared_size_value < 0 or declared_size_value > limit:
                            raise ResourceLimitError(
                                "RPC response exceeds the plan capture byte limit"
                            )
                    raw = _read_response(response, limit, self._limits)
                self._limits.after_response(len(raw))
                if declared_size_value is not None and len(raw) != declared_size_value:
                    raise RpcTransportError(
                        "provider response did not match its content length"
                    )
                if len(raw) > limit:
                    raise RpcTransportError(
                        "provider response exceeded the capture byte limit"
                    )
                parse_failed = False
                try:
                    parsed = loads(raw, max_bytes=limit)
                except FormatError:
                    parse_failed = True
                if parse_failed:
                    raise RpcTransportError("provider returned invalid JSON")
                return parsed
        except HTTPError as exc:
            try:
                exc.close()
            except Exception:
                pass
        except _RpcDeadlineExpired:
            deadline_expired = True
        except (ResourceLimitError, RpcTransportError):
            raise
        except Exception:
            pass
        if deadline_expired:
            raise ResourceLimitError(
                f"capture exceeds the plan limit of "
                f"{self._limits.max_elapsed_seconds} seconds"
            )
        raise RpcTransportError("provider transport failed")


def _declared_content_length(headers: Mapping[str, str]) -> int | None:
    lengths = _header_values(headers, "Content-Length")
    transfers = _header_values(headers, "Transfer-Encoding")
    if len(lengths) > 1 or len(transfers) > 1 or (lengths and transfers):
        raise RpcTransportError("provider returned ambiguous response framing")
    if transfers:
        if not isinstance(transfers[0], str) or transfers[0].strip().lower() != "chunked":
            raise RpcTransportError("provider returned an unsupported transfer encoding")
        return None
    if not lengths:
        return None
    declared_size = lengths[0]
    if not isinstance(declared_size, str):
        raise RpcTransportError("provider returned an invalid content length")
    digits = declared_size.strip(" \t")
    if re.fullmatch(r"[0-9]+", digits) is None:
        raise RpcTransportError("provider returned an invalid content length")
    value = None
    try:
        value = int(digits, 10)
    except ValueError:
        pass
    if value is None:
        raise RpcTransportError("provider returned an invalid content length")
    return value


@contextmanager
def _transport_deadline(limits: CaptureLimits):
    """Enforce one absolute wall deadline across the whole blocking exchange."""

    remaining = limits.remaining_seconds()
    if (
        current_thread() is not main_thread()
        or not hasattr(signal, "setitimer")
        or not hasattr(signal, "getitimer")
    ):
        raise RpcTransportError("absolute RPC deadline enforcement is unavailable")
    try:
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
    except Exception:
        raise RpcTransportError(
            "absolute RPC deadline enforcement is unavailable"
        ) from None
    if previous_handler not in {signal.SIG_DFL, signal.SIG_IGN} or any(
        value > 0 for value in previous_timer
    ):
        raise RpcTransportError("absolute RPC deadline enforcement is unavailable")

    def expired(signum, frame):
        raise _RpcDeadlineExpired

    handler_installed = False
    try:
        signal.signal(signal.SIGALRM, expired)
        handler_installed = True
        signal.setitimer(signal.ITIMER_REAL, remaining)
        yield
    finally:
        if handler_installed:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)


def _read_response(response: Any, limit: int, limits: CaptureLimits) -> bytes:
    """Read at most one byte beyond the cap while rechecking the deadline."""

    read_one = getattr(response, "read1", None)
    if not callable(read_one):
        return response.read(limit + 1)
    raw = bytearray()
    while len(raw) <= limit:
        remaining_seconds = limits.remaining_seconds()
        _set_response_timeout(response, remaining_seconds)
        chunk = read_one(
            min(RESPONSE_READ_CHUNK_BYTES, limit + 1 - len(raw))
        )
        limits.check_time()
        if not isinstance(chunk, bytes):
            raise RpcTransportError("provider returned an invalid response body")
        if not chunk:
            break
        raw.extend(chunk)
    return bytes(raw)


def _set_response_timeout(response: Any, timeout: float) -> None:
    """Refresh urllib's socket timeout to the remaining absolute budget."""

    handle = getattr(response, "fp", None)
    raw = getattr(handle, "raw", None)
    sock = getattr(raw, "_sock", None)
    settimeout = getattr(sock, "settimeout", None)
    if callable(settimeout):
        settimeout(timeout)


def _header_values(headers: Mapping[str, str], name: str) -> list[Any]:
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        values = get_all(name)
        if values is not None:
            return list(values)
    value = headers.get(name)
    return [] if value is None else [value]


def _http_rpc_url(url: str) -> str:
    """Keep urllib's non-network handlers outside the capture boundary."""

    valid = False
    try:
        if isinstance(url, str):
            parsed = urlsplit(url)
            valid = (
                parsed.scheme.lower() in {"http", "https"}
                and bool(parsed.netloc)
                and parsed.hostname is not None
            )
    except Exception:
        valid = False
    if not valid:
        raise RpcTransportError("provider URL must use HTTP or HTTPS")
    return url
