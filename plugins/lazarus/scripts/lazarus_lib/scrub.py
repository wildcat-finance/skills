"""Provider-secret extraction, error sanitising and output scanning."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, unquote, urlsplit

from .errors import IntegrityError


URL = re.compile(r"(?i)https?://[^\s\"'<>]+")
BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
COOKIE = re.compile(r"(?i)\b(?:set-cookie|cookie)\s*:\s*[^\r\n]+")
SCAN_CHUNK_BYTES = 64 * 1024


def provider_secrets(url: str, headers: Mapping[str, str] | None = None) -> set[str]:
    values: set[str] = {url}
    parsed = urlsplit(url)
    for value in (parsed.username, parsed.password):
        if value:
            values.add(unquote(value))
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key:
            values.add(unquote(key))
        if value:
            values.add(unquote(value))
    for name, value in (headers or {}).items():
        if value:
            values.add(value)
        lowered = name.lower()
        if lowered in {"authorization", "proxy-authorization", "cookie", "set-cookie"}:
            values.add(value)
            if lowered.endswith("authorization") and value.lower().startswith("bearer "):
                values.add(value[7:].strip())
            if "cookie" in lowered:
                for part in value.split(";"):
                    if "=" in part:
                        values.add(part.split("=", 1)[1].strip())
    return {value for value in values if len(value) >= 4}


def provider_secret_union(
    providers: Iterable[tuple[str, Mapping[str, str] | None]],
) -> set[str]:
    secrets: set[str] = set()
    for url, headers in providers:
        secrets.update(provider_secrets(url, headers))
    return secrets


def redact_text(text: str, *, secrets: set[str] | None = None) -> str:
    result = URL.sub("[redacted-url]", text)
    result = BEARER.sub("Bearer [redacted]", result)
    result = COOKIE.sub("Cookie: [redacted]", result)
    for secret in sorted(secrets or (), key=len, reverse=True):
        result = result.replace(secret, "[redacted]")
    return result


def sanitised_rpc_error(error: Any) -> dict[str, Any]:
    code = -32000
    if isinstance(error, dict):
        candidate = error.get("code")
        if isinstance(candidate, int) and not isinstance(candidate, bool):
            code = candidate
    return {"code": code, "message": "provider request failed"}


def assert_no_secrets(root: str | Path, secrets: set[str]) -> None:
    encoded = [secret.encode("utf-8") for secret in secrets if secret]
    if not encoded:
        return
    overlap = max(len(secret) for secret in encoded) - 1
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue
        tail = b""
        with path.open("rb") as handle:
            while chunk := handle.read(SCAN_CHUNK_BYTES):
                window = tail + chunk
                if any(secret in window for secret in encoded):
                    raise IntegrityError(
                        f"provider secret reached fixture component {path.name}"
                    )
                tail = window[-overlap:] if overlap else b""
