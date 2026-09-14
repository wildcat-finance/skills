"""Closed JSON and byte identities for publication admission."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
import struct
import unicodedata
from typing import Any

from .errors import PublisherError, refuse


REQUEST_SCHEMA = "github-issue-publication-request/v1"
CANDIDATE_SCHEMA = "github-issue-candidate/v1"
FROZEN_SCHEMA = "github-issue-frozen-inventory/v1"
MAX_REQUEST_BYTES = 1 << 20
MAX_TITLE_BYTES = 256
MAX_BODY_BYTES = 256 << 10
MAX_STRING_BYTES = 256 << 10
MAX_JSON_DEPTH = 8
MAX_JSON_MEMBERS = 256


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    except (TypeError, ValueError, OverflowError) as exc:
        raise PublisherError("GIP103", "request.canonical") from exc


def _reject_float(_value: str) -> None:
    refuse("GIP103", "request.number")


def _reject_constant(_value: str) -> None:
    refuse("GIP103", "request.number")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            refuse("GIP102", "request.duplicate")
        result[key] = value
    return result


def _bounded_string(value: str) -> None:
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise PublisherError("GIP103", "request.string") from exc
    if len(encoded) > MAX_STRING_BYTES:
        refuse("GIP103", "request.string")


def _shape(value: Any, *, depth: int = 0) -> int:
    if depth > MAX_JSON_DEPTH:
        refuse("GIP103", "request.depth")
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return 0
    if isinstance(value, float):
        if not math.isfinite(value):
            refuse("GIP103", "request.number")
        refuse("GIP103", "request.number")
    if isinstance(value, str):
        _bounded_string(value)
        return 0
    if isinstance(value, list):
        if len(value) > MAX_JSON_MEMBERS:
            refuse("GIP103", "request.members")
        return len(value) + sum(_shape(item, depth=depth + 1) for item in value)
    if isinstance(value, dict):
        if len(value) > MAX_JSON_MEMBERS:
            refuse("GIP103", "request.members")
        count = len(value)
        for key, item in value.items():
            if not isinstance(key, str):
                refuse("GIP103", "request.key")
            _bounded_string(key)
            count += _shape(item, depth=depth + 1)
        return count
    refuse("GIP103", "request.type")


def parse_json_bytes(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_REQUEST_BYTES:
        refuse("GIP100", "request.bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PublisherError("GIP101", "request.utf8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except PublisherError:
        raise
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PublisherError("GIP101", "request.json") from exc
    if not isinstance(value, dict):
        refuse("GIP103", "request.root")
    if _shape(value) > MAX_JSON_MEMBERS:
        refuse("GIP103", "request.members")
    if raw != canonical_json(value):
        refuse("GIP104", "request.canonical")
    return value


def read_bounded_file(path: str | os.PathLike[str]) -> bytes:
    target = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    if not no_follow:
        refuse("GIP105", "request.path")
    descriptor = -1
    try:
        descriptor = os.open(target, flags | no_follow)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            refuse("GIP105", "request.path")
        if opened.st_size <= 0 or opened.st_size > MAX_REQUEST_BYTES:
            refuse("GIP100", "request.bytes")
        raw = os.read(descriptor, MAX_REQUEST_BYTES + 1)
        if len(raw) != opened.st_size or len(raw) > MAX_REQUEST_BYTES:
            refuse("GIP100", "request.bytes")
        after = os.fstat(descriptor)
        if (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            refuse("GIP105", "request.path")
        return raw
    except PublisherError:
        raise
    except OSError as exc:
        raise PublisherError("GIP105", "request.path") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def safe_text(
    value: Any,
    field: str,
    *,
    max_bytes: int,
    multiline: bool,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        refuse("GIP110", field)
    if (not value and not allow_empty) or len(value.encode("utf-8")) > max_bytes:
        refuse("GIP110", field)
    if unicodedata.normalize("NFC", value) != value:
        refuse("GIP110", field)
    for char in value:
        if char in "\n\t" and multiline:
            continue
        if (
            (not multiline and not char.isprintable())
            or char == "\r"
            or unicodedata.category(char).startswith("C")
        ):
            refuse("GIP110", field)
    return value


def candidate_identity(title: str, body: str) -> bytes:
    title_bytes = title.encode("utf-8")
    body_bytes = body.encode("utf-8")
    return (
        CANDIDATE_SCHEMA.encode("ascii")
        + b"\x00"
        + struct.pack(">I", len(title_bytes))
        + title_bytes
        + struct.pack(">I", len(body_bytes))
        + body_bytes
    )


def candidate_sha256(title: str, body: str) -> str:
    return sha256_bytes(candidate_identity(title, body))


def frozen_sha256(frozen: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json(frozen))
