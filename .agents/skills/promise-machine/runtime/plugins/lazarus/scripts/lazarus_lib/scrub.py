"""Provider-secret extraction, error sanitising and output scanning."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qsl, unquote, urlsplit

from .canonical import dumps
from .errors import FormatError, IntegrityError, ResourceLimitError


URL = re.compile(r"(?i)https?://[^\s\"'<>]+")
BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
COOKIE = re.compile(r"(?i)\b(?:set-cookie|cookie)\s*:\s*[^\r\n]+")
PERCENT_ESCAPE = re.compile(r"%[0-9A-Fa-f]{2}")
PERCENT_ESCAPE_BYTES = re.compile(rb"%[0-9A-Fa-f]{2}")
URL_MATERIAL_SEPARATOR = re.compile(r"[\s/?:@&=;#.,'\"\\]+")
MAX_PERCENT_DECODE_ROUNDS = 8
MAX_PROVIDER_URL_CHARS = 65_536
MAX_PROVIDER_HEADER_COUNT = 64
MAX_PROVIDER_HEADER_CHARS = 65_536
MAX_PROVIDER_SECRET_VALUES = 1_024
SCAN_CHUNK_BYTES = 64 * 1024
REDACTION = "[x]"


def provider_secrets(
    url: str,
    headers: Mapping[str, str] | None = None,
    *,
    check_time: Callable[[], None] | None = None,
) -> set[str]:
    if check_time is not None:
        check_time()
    if not isinstance(url, str) or len(url) > MAX_PROVIDER_URL_CHARS:
        raise ResourceLimitError("provider URL exceeds the secret-classifier limit")
    header_items: list[tuple[str, str]] = []
    header_chars = 0
    for name, value in (() if headers is None else headers.items()):
        if check_time is not None:
            check_time()
        if len(header_items) >= MAX_PROVIDER_HEADER_COUNT:
            raise ResourceLimitError(
                "provider headers exceed the secret-classifier limit"
            )
        if not isinstance(name, str) or not isinstance(value, str):
            raise FormatError("provider headers must contain text names and values")
        header_chars += len(name) + len(value)
        if header_chars > MAX_PROVIDER_HEADER_CHARS:
            raise ResourceLimitError(
                "provider headers exceed the secret-classifier character limit"
            )
        header_items.append((name, value))
    values: set[str] = {url}
    credential_values: set[str] = set()
    parsed = urlsplit(url)
    if check_time is not None:
        check_time()
    # Keep the complete authority, including its port, but do not split that
    # public transport coordinate into a standalone numeric pattern. Ephemeral
    # ports are four or five digits and collide readily with ordinary fixture
    # bytes. The hostname is classified separately below, while user
    # information remains credential-bearing and is split by its own path.
    _add_url_spellings(values, parsed.netloc, check_time=check_time)
    if parsed.hostname:
        _add_url_material(values, parsed.hostname, check_time=check_time)
    for value in (parsed.username, parsed.password):
        if value:
            _add_credential_material(
                values, credential_values, value, check_time=check_time
            )
    _add_url_material(values, parsed.path, check_time=check_time)
    _add_url_material(values, parsed.query, check_time=check_time)
    _add_url_material(values, parsed.fragment, check_time=check_time)
    for pair in parsed.query.split("&"):
        if check_time is not None:
            check_time()
        raw_key, separator, raw_value = pair.partition("=")
        if raw_key:
            _add_url_material(values, raw_key, check_time=check_time)
        if separator and raw_value:
            _add_credential_material(
                values, credential_values, raw_value, check_time=check_time
            )
    if check_time is not None:
        check_time()
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if check_time is not None:
            check_time()
        if key:
            _add_url_material(values, key, check_time=check_time)
        if value:
            _add_credential_material(
                values, credential_values, value, check_time=check_time
            )
    for name, value in header_items:
        if check_time is not None:
            check_time()
        if value:
            _add_credential_material(
                values, credential_values, value, check_time=check_time
            )
        lowered = name.lower()
        if lowered in {"authorization", "proxy-authorization", "cookie", "set-cookie"}:
            if lowered.endswith("authorization"):
                parts = value.split(None, 1)
                if len(parts) == 2 and parts[1].strip():
                    payload = parts[1].strip()
                    _add_credential_material(
                        values,
                        credential_values,
                        payload,
                        check_time=check_time,
                    )
                    if parts[0].lower() == "basic":
                        _add_basic_authorization(
                            values,
                            credential_values,
                            payload,
                            check_time=check_time,
                        )
            if "cookie" in lowered:
                for part in value.split(";"):
                    if check_time is not None:
                        check_time()
                    if "=" in part:
                        _add_credential_material(
                            values,
                            credential_values,
                            part.split("=", 1)[1].strip(),
                            check_time=check_time,
                        )
    if any(0 < len(value) < 4 for value in credential_values):
        raise ResourceLimitError(
            "provider credential is shorter than the secret-classifier minimum"
        )
    secrets = {value for value in values if len(value) >= 4}
    if len(secrets) > MAX_PROVIDER_SECRET_VALUES:
        raise ResourceLimitError(
            "provider URL has too many secret-classifier components"
        )
    return secrets


def _add_url_spellings(
    values: set[str],
    value: str,
    *,
    check_time: Callable[[], None] | None = None,
) -> None:
    """Classify raw, decoded, and normalised percent spellings of URL material."""

    if not value:
        return
    current = value
    for _ in range(MAX_PERCENT_DECODE_ROUNDS + 1):
        if check_time is not None:
            check_time()
        values.add(current)
        if PERCENT_ESCAPE.search(current) is not None:
            values.add(
                PERCENT_ESCAPE.sub(lambda match: match.group(0).upper(), current)
            )
            values.add(
                PERCENT_ESCAPE.sub(lambda match: match.group(0).lower(), current)
            )
        decoded = unquote(current)
        if decoded == current:
            return
        current = decoded
    raise ValueError("URL percent encoding exceeds the supported nesting limit")


def _add_url_material(
    values: set[str],
    value: str,
    *,
    credential_values: set[str] | None = None,
    check_time: Callable[[], None] | None = None,
) -> None:
    """Classify a URL component and delimiter-separated material within it."""

    spellings: set[str] = set()
    _add_url_spellings(spellings, value, check_time=check_time)
    values.update(spellings)
    if credential_values is not None:
        credential_values.update(item for item in spellings if item)
    for spelling in spellings:
        if check_time is not None:
            check_time()
        for component in URL_MATERIAL_SEPARATOR.split(spelling):
            component_spellings: set[str] = set()
            _add_url_spellings(
                component_spellings, component, check_time=check_time
            )
            values.update(component_spellings)
            if credential_values is not None:
                credential_values.update(
                    item for item in component_spellings if item
                )


def _add_credential_material(
    values: set[str],
    credential_values: set[str],
    value: str,
    *,
    check_time: Callable[[], None] | None = None,
) -> None:
    """Retain every spelling when its source is credential-bearing."""

    _add_url_material(
        values,
        value,
        credential_values=credential_values,
        check_time=check_time,
    )


def _add_basic_authorization(
    values: set[str],
    credential_values: set[str],
    payload: str,
    *,
    check_time: Callable[[], None] | None = None,
) -> None:
    """Classify the decoded Basic user-password material when it is well formed."""

    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError):
        return
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError:
        decoded = raw.decode("latin-1")
    _add_credential_material(
        values, credential_values, decoded, check_time=check_time
    )
    username, separator, password = decoded.partition(":")
    if separator:
        for value in (username, password):
            if value:
                _add_credential_material(
                    values, credential_values, value, check_time=check_time
                )


def provider_secret_union(
    providers: Iterable[tuple[str, Mapping[str, str] | None]],
    *,
    check_time: Callable[[], None] | None = None,
) -> set[str]:
    secrets: set[str] = set()
    for url, headers in providers:
        if check_time is not None:
            check_time()
        secrets.update(provider_secrets(url, headers, check_time=check_time))
        if len(secrets) > MAX_PROVIDER_SECRET_VALUES:
            raise ResourceLimitError(
                "provider mappings have too many secret-classifier components"
            )
    return secrets


def redact_text(text: str, *, secrets: set[str] | None = None) -> str:
    result = URL.sub(REDACTION, text)
    result = BEARER.sub(REDACTION, result)
    result = COOKIE.sub(REDACTION, result)
    for secret in sorted(secrets or (), key=len, reverse=True):
        result = result.replace(secret, REDACTION)
        if PERCENT_ESCAPE.search(secret) is not None:
            result = _percent_equivalent_pattern(secret).sub(REDACTION, result)
    try:
        if secrets and _contains_secret_bytes(
            result.encode("utf-8"), _secret_byte_patterns(secrets)
        ):
            return REDACTION
    except UnicodeEncodeError:
        return REDACTION
    return result


def _percent_equivalent_pattern(value: str) -> re.Pattern[str]:
    """Match a spelling while ignoring only percent-escape hex digit case."""

    pieces: list[str] = []
    offset = 0
    for match in PERCENT_ESCAPE.finditer(value):
        pieces.append(re.escape(value[offset : match.start()]))
        escaped = match.group(0)
        digits = "".join(
            f"[{digit.lower()}{digit.upper()}]" if digit.isalpha() else digit
            for digit in escaped[1:]
        )
        pieces.append("%" + digits)
        offset = match.end()
    pieces.append(re.escape(value[offset:]))
    return re.compile("".join(pieces))


def sanitised_rpc_error(error: Any) -> dict[str, Any]:
    code = -32000
    if isinstance(error, dict):
        candidate = error.get("code")
        if isinstance(candidate, int) and not isinstance(candidate, bool):
            code = candidate
    return {"code": code, "message": "provider request failed"}


def assert_no_secrets(
    root: str | Path,
    secrets: set[str],
    *,
    check_time: Callable[[], None] | None = None,
) -> None:
    encoded = _secret_byte_patterns(secrets, check_time=check_time)
    if not encoded:
        return
    for path in sorted(Path(root).rglob("*")):
        if check_time is not None:
            check_time()
        if not path.is_file():
            continue
        scanner = _SecretByteScanner(encoded, check_time=check_time)
        with path.open("rb") as handle:
            while chunk := handle.read(SCAN_CHUNK_BYTES):
                if scanner.feed(chunk):
                    raise IntegrityError(
                        f"provider secret reached fixture component {path.name}"
                    )
        if scanner.finish():
            raise IntegrityError(
                f"provider secret reached fixture component {path.name}"
            )
        if check_time is not None:
            check_time()


def assert_no_secret_bytes(
    data: bytes,
    secrets: set[str],
    *,
    label: str,
    check_time: Callable[[], None] | None = None,
) -> None:
    """Apply the provider-secret union to bytes emitted outside the fixture."""

    if _contains_secret_bytes(
        data,
        _secret_byte_patterns(secrets, check_time=check_time),
        check_time=check_time,
    ):
        raise IntegrityError(f"provider secret reached {label}")


def _secret_byte_patterns(
    secrets: set[str],
    *,
    check_time: Callable[[], None] | None = None,
) -> list[bytes]:
    """Return raw and canonical-JSON spellings of every scannable secret."""

    patterns: set[bytes] = set()
    for secret in secrets:
        if check_time is not None:
            check_time()
        if not secret:
            continue
        try:
            patterns.add(_normalise_percent_bytes(secret.encode("utf-8")))
            patterns.add(_normalise_percent_bytes(dumps(secret)[1:-1]))
        except (FormatError, UnicodeEncodeError):
            continue
    result = sorted(patterns, key=len, reverse=True)
    if check_time is not None:
        check_time()
    return result


def _normalise_percent_bytes(data: bytes) -> bytes:
    """Canonicalise percent-escape case without changing byte offsets or length."""

    return PERCENT_ESCAPE_BYTES.sub(lambda match: match.group(0).upper(), data)


def _contains_secret_bytes(
    data: bytes,
    patterns: list[bytes],
    *,
    check_time: Callable[[], None] | None = None,
) -> bool:
    scanner = _SecretByteScanner(patterns, check_time=check_time)
    return scanner.feed(data) or scanner.finish()


class _PercentDecoder:
    """Incrementally decode one percent-encoding layer across chunk boundaries."""

    def __init__(self) -> None:
        self.pending = b""

    def feed(self, data: bytes, *, final: bool) -> bytes:
        source = self.pending + data
        self.pending = b""
        decoded = bytearray()
        offset = 0
        while offset < len(source):
            if source[offset] != ord("%"):
                decoded.append(source[offset])
                offset += 1
                continue
            remaining = len(source) - offset
            if remaining >= 3:
                digits = source[offset + 1 : offset + 3]
                if all(value in b"0123456789abcdefABCDEF" for value in digits):
                    decoded.append(int(digits, 16))
                    offset += 3
                    continue
                decoded.append(source[offset])
                offset += 1
                continue
            suffix = source[offset:]
            could_complete = all(
                value in b"0123456789abcdefABCDEF" for value in suffix[1:]
            )
            if not final and could_complete:
                self.pending = suffix
                break
            decoded.extend(suffix)
            break
        return bytes(decoded)


class _SecretByteScanner:
    """Scan raw and recursively percent-decoded streams with bounded state."""

    def __init__(
        self,
        patterns: list[bytes],
        *,
        check_time: Callable[[], None] | None = None,
    ) -> None:
        self.patterns = patterns
        self.overlap = max((len(pattern) for pattern in patterns), default=1) - 1
        self.tails = [b""] * (MAX_PERCENT_DECODE_ROUNDS + 1)
        self.decoders = [
            _PercentDecoder() for _ in range(MAX_PERCENT_DECODE_ROUNDS)
        ]
        self.check_time = check_time

    def feed(self, data: bytes, *, final: bool = False) -> bool:
        level = data
        for depth in range(MAX_PERCENT_DECODE_ROUNDS + 1):
            if self.check_time is not None:
                self.check_time()
            window = self.tails[depth] + _normalise_percent_bytes(level)
            if any(pattern in window for pattern in self.patterns):
                return True
            self.tails[depth] = window[-self.overlap :] if self.overlap else b""
            if depth < MAX_PERCENT_DECODE_ROUNDS:
                level = self.decoders[depth].feed(level, final=final)
            elif PERCENT_ESCAPE_BYTES.search(window) is not None:
                return True
        return False

    def finish(self) -> bool:
        return self.feed(b"", final=True)
