#!/usr/bin/env python3
"""Bounded entrypoint for the Noema version 1 shadow prototype."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import heapq
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile
import zlib


CONTRACT = "noema/v1"
SOURCE_MAGIC = "NOE1"
PROJECTION_MAGIC = "NT1"
RESULT_SCHEMA = "noema-result/v1"
INVENTORY_SCHEMA = "noema-seed-inventory/v1"

MAX_ARCHIVE_BYTES = 1_048_576
MAX_MEMBERS = 64
MAX_MEMBER_BYTES = 1_048_576
MAX_TOTAL_MEMBER_BYTES = 1_048_576
MAX_PATH_BYTES = 512
MAX_JSON_BYTES = 1_048_576
MAX_INPUT_BYTES = 1_048_576
MAX_LINE_BYTES = 65_536
MAX_RECORDS = 16_384
MAX_GRAPH_NODES = 16_384
MAX_IMPORTS = 64
MAX_DEPTH = 64
MAX_LITERAL_BYTES = 65_000
MAX_LITERAL_TOTAL_BYTES = 786_432
MAX_EXPANDED_NODES = 65_536
MAX_SET_MEMBERS = 4_096
MAX_OUTPUT_BYTES = 1_048_576
MAX_IDENTIFIER_BYTES = 128
MAX_ATOM_BYTES = 65_000

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
ALIAS_RE = re.compile(r"^[A-Za-z0-9!#$%&*+./:<=>?@^_|~-]{1,16}$")
DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")
SEED_RELATIVE_PATH_RE = re.compile(
    r"^(?!.*//)(?!.*(?:^|/)\.{1,2}(?:/|$))[A-Za-z0-9]"
    r"(?:[A-Za-z0-9._/-]*[A-Za-z0-9._-])?$"
)
SEED_ROOT_PATH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/$")
UNIMPLEMENTED = (
    "select",
    "check",
    "next",
    "literal",
    "explain",
    "mutations",
    "measure",
    "emit-evaluation",
    "tally-evaluation",
    "runtime-self-test",
)
IMPLEMENTED = (
    "about",
    "verify-seed",
    "parse",
    "format",
    "project",
    "semantic-diff",
    "verify",
    "self-test",
)
KNOWN_COMMANDS = frozenset((*IMPLEMENTED, *UNIMPLEMENTED))
ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}

CORE_TYPES = frozenset(
    "actor artifact action claim command effect event evidence literal operation "
    "path predicate promise repository rule scope state transition type value".split()
)
LITERAL_KINDS = frozenset(
    {"id", "path", "sha256", "command", "number", "date", "url", "quote", "text", "bytes"}
)
LITERAL_TYPES = {
    "id": "value",
    "path": "path",
    "sha256": "value",
    "command": "command",
    "number": "value",
    "date": "value",
    "url": "value",
    "quote": "literal",
    "text": "literal",
    "bytes": "literal",
}
RECORD_FORMS = (
    "import",
    "literal",
    "definition",
    "rule",
    "precedence",
    "override",
    "transition",
    "promise",
    "handoff",
    "exception",
)
RECORD_RANK = {form: index for index, form in enumerate(RECORD_FORMS)}
OPERATORS = frozenset(
    {"!", "-", "+", "?", "/", "@", "^", ";", "&", "|", "~", "=", "=>", "<",
     "all", "any", "one", "in", "subset", "lt", "le", "gt", "ge", "count"}
)
DIRECTIVE_OPERATORS = frozenset({"!", "-", "+", "?", "/", "@", "^", ";"})
TERM_TAGS = frozenset({"$", "%", ":", "{}"})
RESERVED_SYMBOLS = frozenset({SOURCE_MAGIC, PROJECTION_MAGIC, *RECORD_FORMS, *OPERATORS, *TERM_TAGS, "src"})
PROFILE_SCHEMA = "noema-profile/v1"
MODULE_SCHEMA = "noema-module/v1"
GRAPH_SCHEMA = "noema-graph/v1"
BUILD_SCHEMA = "noema-build/v1"
PROJECTION_SCHEMA = "noema-projection/v1"
PROJECTION_MANIFEST_SCHEMA = "noema-projection-manifest/v1"
DIFF_SCHEMA = "noema-semantic-diff/v1"


class Refusal(ValueError):
    """One stable, bounded refusal without untrusted payload bytes."""

    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message


def refuse(code: str, field: str, message: str) -> None:
    raise Refusal(code, field, message)


class _BoundedArgumentParser(argparse.ArgumentParser):
    """Turn malformed argument vectors into the same bounded refusal channel."""

    def error(self, _message: str) -> None:
        refuse(
            "NOE-E-TYPE.ARGUMENTS",
            "command",
            "command arguments do not match the closed interface",
        )


def _correlation(command: str, *values: str) -> str:
    digest = sha256()
    digest.update(b"noema-result/v1\x00")
    for value in (command, *values):
        encoded = value.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
    return digest.hexdigest()


def _result(
    command: str,
    verdict: str,
    code: str,
    *,
    correlation_values: tuple[str, ...] = (),
    field: str | None = None,
    message: str | None = None,
    digests: dict[str, str] | None = None,
    counts: dict[str, int] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": RESULT_SCHEMA,
        "command": command,
        "correlation_id": _correlation(command, *correlation_values),
        "verdict": verdict,
        "code": code,
        "digests": digests or {},
        "counts": counts or {},
    }
    if field is not None:
        payload["field"] = field
    if message is not None:
        payload["message"] = message
    return payload


def emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            refuse("NOE-E-SYNTAX.DUPLICATE_KEY", "inventory", "duplicate JSON key")
        result[key] = value
    return result


def _read_open_regular(
    descriptor: int,
    field: str,
    limit: int,
    expected_identity: tuple[int, int] | None = None,
) -> tuple[bytes, tuple[int, int]]:
    close_failed = False
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            refuse("NOE-E-PATH.REGULAR", field, "opened input is not a regular file")
        if expected_identity is not None and (before.st_dev, before.st_ino) != expected_identity:
            refuse("NOE-E-PATH.IDENTITY", field, "input identity changed before read")
        if before.st_size > limit:
            refuse("NOE-E-BOUNDS.FILE", field, "input exceeds its byte limit")

        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                refuse("NOE-E-BOUNDS.FILE", field, "input exceeds its byte limit")
        after = os.fstat(descriptor)
    except Refusal:
        raise
    except OSError:
        refuse("NOE-E-IO.READ", field, "regular input failed during descriptor read")
    finally:
        try:
            os.close(descriptor)
        except OSError:
            close_failed = True

    if close_failed:
        refuse("NOE-E-IO.READ", field, "regular input descriptor could not be closed")

    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_identity != after_identity or total != after.st_size:
        refuse("NOE-E-IO.CHANGED", field, "input changed during read")
    return b"".join(chunks), (before.st_dev, before.st_ino)


def _read_regular(path: Path, field: str, limit: int) -> bytes:
    if not hasattr(os, "O_NOFOLLOW"):
        refuse("NOE-E-PATH.PLATFORM", field, "no-follow file reads are unavailable")
    try:
        before_path = path.lstat()
    except OSError:
        refuse("NOE-E-IO.READ", field, "regular input cannot be inspected")
    if not stat.S_ISREG(before_path.st_mode):
        refuse("NOE-E-PATH.REGULAR", field, "input must be a regular file")
    if before_path.st_size > limit:
        refuse("NOE-E-BOUNDS.FILE", field, "input exceeds its byte limit")

    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError:
        refuse("NOE-E-IO.READ", field, "regular input cannot be opened")
    payload, _identity = _read_open_regular(
        descriptor,
        field,
        limit,
        (before_path.st_dev, before_path.st_ino),
    )
    return payload


def _read_repository_regular(
    root: Path,
    relative: str,
    field: str,
    limit: int,
) -> tuple[bytes, tuple[int, int]]:
    if (
        not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
        or os.open not in os.supports_dir_fd
    ):
        refuse("NOE-E-PATH.PLATFORM", field, "confined no-follow reads are unavailable")
    relative = _relative_path(relative, field)
    components = PurePosixPath(relative).parts
    directory_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC

    directories: list[int] = []
    close_failed = False
    try:
        current = os.open(root, directory_flags)
        directories.append(current)
        if not stat.S_ISDIR(os.fstat(current).st_mode):
            refuse("NOE-E-PATH.DIRECTORY", field, "repository root is not one real directory")
        for component in components[:-1]:
            current = os.open(component, directory_flags, dir_fd=current)
            directories.append(current)
            if not stat.S_ISDIR(os.fstat(current).st_mode):
                refuse("NOE-E-PATH.DIRECTORY", field, "source ancestor is not one real directory")
        descriptor = os.open(components[-1], file_flags, dir_fd=current)
        payload, identity = _read_open_regular(descriptor, field, limit)
    except Refusal:
        raise
    except OSError:
        refuse("NOE-E-PATH.CONFINEMENT", field, "source path is absent, linked or escaping")
    finally:
        for descriptor in reversed(directories):
            try:
                os.close(descriptor)
            except OSError:
                close_failed = True
    if close_failed:
        refuse("NOE-E-IO.READ", field, "source directory descriptor could not be closed")
    return payload, identity


def _exact_keys(value: object, expected: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        refuse("NOE-E-TYPE.OBJECT", field, "expected an object")
    actual = set(value)
    if actual != expected:
        refuse("NOE-E-TYPE.KEYS", field, "object keys do not match the closed shape")
    return value


def _bounded_string(value: object, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value:
        refuse("NOE-E-TYPE.STRING", field, "expected one bounded non-empty string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        refuse("NOE-E-SYNTAX.UNICODE", field, "string must contain Unicode scalar values")
    if len(encoded) > limit:
        refuse("NOE-E-TYPE.STRING", field, "expected one bounded non-empty string")
    if unicodedata.normalize("NFC", value) != value:
        refuse("NOE-E-SYNTAX.UNICODE", field, "string must be NFC")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        refuse("NOE-E-SYNTAX.CONTROL", field, "control characters are forbidden")
    return value


def _bounded_integer(value: object, field: str, maximum: int, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        refuse("NOE-E-BOUNDS.INTEGER", field, "integer is outside its closed range")
    return value


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        refuse("NOE-E-TYPE.SHA256", field, "expected one lowercase SHA-256 value")
    return value


def _relative_path(value: object, field: str) -> str:
    text = _bounded_string(value, field, MAX_PATH_BYTES)
    if "\\" in text or text.startswith("/") or text.endswith("/"):
        refuse("NOE-E-PATH.RELATIVE", field, "expected one file path below the archive root")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        refuse("NOE-E-PATH.TRAVERSAL", field, "path must stay below the archive root")
    if path.as_posix() != text:
        refuse("NOE-E-PATH.RELATIVE", field, "archive member path must be canonical POSIX")
    if SEED_RELATIVE_PATH_RE.fullmatch(text) is None:
        refuse("NOE-E-PATH.RELATIVE", field, "archive member path is outside the seed alphabet")
    return text


def _root_path(value: object, field: str) -> str:
    text = _bounded_string(value, field, 256)
    if "\\" in text or not text.endswith("/") or text.startswith("/"):
        refuse("NOE-E-PATH.ROOT", field, "archive root must be one relative directory")
    root = text[:-1]
    path = PurePosixPath(root)
    if (
        len(path.parts) != 1
        or path.parts[0] in {"", ".", ".."}
        or path.as_posix() != root
        or SEED_ROOT_PATH_RE.fullmatch(text) is None
    ):
        refuse("NOE-E-PATH.ROOT", field, "archive root must be one relative directory")
    return text


def load_inventory(path: Path) -> tuple[dict[str, object], bytes]:
    raw = _read_regular(path, "inventory", MAX_JSON_BYTES)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        refuse("NOE-E-SYNTAX.UTF8", "inventory", "inventory must be UTF-8")
    if text.startswith("\ufeff"):
        refuse("NOE-E-SYNTAX.BOM", "inventory", "inventory must not carry a BOM")
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicates)
    except Refusal:
        raise
    except (ValueError, RecursionError):
        refuse("NOE-E-SYNTAX.JSON", "inventory", "inventory is not bounded JSON")

    inventory = _exact_keys(value, {"schema", "archive", "files"}, "inventory")
    if inventory["schema"] != INVENTORY_SCHEMA:
        refuse("NOE-E-TYPE.VERSION", "inventory.schema", "unsupported inventory schema")

    archive = _exact_keys(
        inventory["archive"],
        {"name", "url", "bytes", "sha256", "root"},
        "inventory.archive",
    )
    if _bounded_string(archive["name"], "inventory.archive.name", 256) != "noema-v0-evidence.zip":
        refuse("NOE-E-TYPE.ARCHIVE_NAME", "inventory.archive.name", "unexpected archive name")
    url = _bounded_string(archive["url"], "inventory.archive.url", 2048)
    if not url.startswith("https://"):
        refuse("NOE-E-TYPE.URL", "inventory.archive.url", "archive URL must use HTTPS")
    _bounded_integer(archive["bytes"], "inventory.archive.bytes", MAX_ARCHIVE_BYTES, minimum=1)
    _digest(archive["sha256"], "inventory.archive.sha256")
    _root_path(archive["root"], "inventory.archive.root")

    files = inventory["files"]
    if not isinstance(files, list) or not files or len(files) > MAX_MEMBERS:
        refuse("NOE-E-BOUNDS.MEMBERS", "inventory.files", "file inventory count is outside its limit")
    paths: list[str] = []
    total = 0
    for index, item in enumerate(files):
        entry = _exact_keys(item, {"path", "bytes", "sha256"}, f"inventory.files[{index}]")
        paths.append(_relative_path(entry["path"], f"inventory.files[{index}].path"))
        total += _bounded_integer(
            entry["bytes"],
            f"inventory.files[{index}].bytes",
            MAX_MEMBER_BYTES,
        )
        _digest(entry["sha256"], f"inventory.files[{index}].sha256")
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        refuse("NOE-E-REFERENCE.FILE_ORDER", "inventory.files", "file paths must be unique and sorted")
    if total > MAX_TOTAL_MEMBER_BYTES:
        refuse("NOE-E-BOUNDS.TOTAL", "inventory.files", "inventoried bytes exceed the aggregate limit")
    return inventory, raw


def _member_kind(info: zipfile.ZipInfo) -> str:
    mode = (info.external_attr >> 16) & 0xFFFF
    kind = stat.S_IFMT(mode)
    if info.is_dir():
        return "directory" if kind in {0, stat.S_IFDIR} else "special"
    return "file" if kind in {0, stat.S_IFREG} else "special"


def verify_seed(archive_path: Path, inventory_path: Path) -> dict[str, object]:
    inventory, inventory_raw = load_inventory(inventory_path)
    archive_record = inventory["archive"]
    assert isinstance(archive_record, dict)
    archive_raw = _read_regular(archive_path, "archive", MAX_ARCHIVE_BYTES)
    archive_digest = sha256(archive_raw).hexdigest()
    expected_archive_digest = archive_record["sha256"]
    if len(archive_raw) != archive_record["bytes"]:
        refuse("NOE-E-DIGEST.ARCHIVE_SIZE", "archive", "archive size does not match inventory")
    if archive_digest != expected_archive_digest:
        refuse("NOE-E-DIGEST.ARCHIVE", "archive", "archive digest does not match inventory")

    files = inventory["files"]
    assert isinstance(files, list)
    expected = {entry["path"]: entry for entry in files}
    root = archive_record["root"]
    assert isinstance(root, str)
    seen_names: set[str] = set()
    seen_files: set[str] = set()
    seen_offsets: set[int] = set()
    total = 0
    saw_root = False

    try:
        with zipfile.ZipFile(io.BytesIO(archive_raw), "r") as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_MEMBERS:
                refuse("NOE-E-BOUNDS.MEMBERS", "archive", "archive member count is outside its limit")
            for index, info in enumerate(members):
                field = f"archive.member[{index}]"
                if info.orig_filename != info.filename or "\x00" in info.filename:
                    refuse("NOE-E-PATH.NAME", field, "archive member name is ambiguous")
                if info.filename in seen_names:
                    refuse("NOE-E-REFERENCE.DUPLICATE_MEMBER", field, "archive member name is duplicated")
                seen_names.add(info.filename)
                if info.header_offset < 0 or info.header_offset >= len(archive_raw):
                    refuse("NOE-E-SYNTAX.ZIP_OFFSET", field, "archive member offset is invalid")
                if info.header_offset in seen_offsets:
                    refuse("NOE-E-SYNTAX.ZIP_OFFSET", field, "archive members share one header offset")
                seen_offsets.add(info.header_offset)
                if info.flag_bits & 0x1:
                    refuse("NOE-E-SYNTAX.ENCRYPTED", field, "encrypted archive members are unsupported")
                if info.compress_type not in ALLOWED_COMPRESSION:
                    refuse("NOE-E-SYNTAX.COMPRESSION", field, "archive compression method is unsupported")
                if _member_kind(info) == "special":
                    refuse("NOE-E-PATH.SPECIAL", field, "links and special archive members are forbidden")

                if info.is_dir():
                    if info.filename != root:
                        refuse("NOE-E-PATH.DIRECTORY", field, "only the declared root directory is allowed")
                    saw_root = True
                    continue

                if not info.filename.startswith(root):
                    refuse("NOE-E-PATH.ROOT", field, "archive member is outside the declared root")
                relative = _relative_path(info.filename[len(root):], field)
                if relative not in expected:
                    refuse("NOE-E-REFERENCE.EXTRA_MEMBER", field, "archive contains an unlisted file")
                if relative in seen_files:
                    refuse("NOE-E-REFERENCE.DUPLICATE_MEMBER", field, "archive file is duplicated")
                record = expected[relative]
                if info.file_size > MAX_MEMBER_BYTES:
                    refuse("NOE-E-BOUNDS.MEMBER", field, "archive member exceeds its byte limit")
                if info.file_size != record["bytes"]:
                    refuse("NOE-E-DIGEST.MEMBER_SIZE", field, "archive member size does not match inventory")
                total += info.file_size
                if total > MAX_TOTAL_MEMBER_BYTES:
                    refuse("NOE-E-BOUNDS.TOTAL", "archive", "archive members exceed the aggregate limit")
                with archive.open(info, "r") as source:
                    payload = source.read(MAX_MEMBER_BYTES + 1)
                    remainder = source.read(1)
                if len(payload) > MAX_MEMBER_BYTES or remainder:
                    refuse("NOE-E-BOUNDS.MEMBER", field, "archive member exceeds its byte limit")
                if len(payload) != record["bytes"]:
                    refuse("NOE-E-DIGEST.MEMBER_SIZE", field, "decoded member size does not match inventory")
                if sha256(payload).hexdigest() != record["sha256"]:
                    refuse("NOE-E-DIGEST.MEMBER", field, "archive member digest does not match inventory")
                seen_files.add(relative)
    except Refusal:
        raise
    except (
        OSError,
        RuntimeError,
        UnicodeError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
        zlib.error,
    ):
        refuse("NOE-E-SYNTAX.ZIP", "archive", "archive is malformed or failed integrity checking")

    if not saw_root:
        refuse("NOE-E-REFERENCE.ROOT", "archive", "declared archive root entry is missing")
    missing = set(expected) - seen_files
    if missing:
        refuse("NOE-E-REFERENCE.MISSING_MEMBER", "archive", "archive is missing an inventoried file")
    if total != sum(entry["bytes"] for entry in files):
        refuse("NOE-E-DIGEST.TOTAL", "archive", "archive decoded-byte total does not match inventory")

    inventory_digest = sha256(inventory_raw).hexdigest()
    return _result(
        "verify-seed",
        "ok",
        "NOE-OK",
        correlation_values=(archive_digest, inventory_digest),
        message="seed inventory matched exact archive bytes",
        digests={"archive": archive_digest, "inventory": inventory_digest},
        counts={"bytes": len(archive_raw), "members": len(seen_files)},
    )


def _canonical_json(value: object) -> bytes:
    """Encode one canonical JSON value with its governing final LF."""
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError):
        refuse("NOE-E-SYNTAX.JSON", "output", "value cannot be encoded as bounded canonical JSON")
    if len(encoded) > MAX_OUTPUT_BYTES:
        refuse("NOE-E-BOUNDS.OUTPUT", "output", "derived output exceeds its byte limit")
    return encoded


def _json_pairs(field: str):
    def pairs_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                refuse("NOE-E-SYNTAX.DUPLICATE_KEY", field, "duplicate JSON key")
            value[key] = item
        return value

    return pairs_hook


def _decode_json(raw: bytes, field: str, *, canonical: bool) -> object:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        refuse("NOE-E-SYNTAX.UTF8", field, "input must be UTF-8")
    if text.startswith("\ufeff"):
        refuse("NOE-E-SYNTAX.BOM", field, "input must not carry a BOM")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_json_pairs(field),
            parse_constant=lambda _value: refuse(
                "NOE-E-SYNTAX.JSON", field, "non-finite JSON numbers are forbidden"
            ),
        )
    except Refusal:
        raise
    except (ValueError, RecursionError):
        refuse("NOE-E-SYNTAX.JSON", field, "input is not bounded JSON")
    _bounded_value_depth(value, field)
    if canonical and raw != _canonical_json(value):
        refuse("NOE-E-SYNTAX.CANONICAL", field, "JSON bytes are not the singular canonical spelling")
    return value


def _bounded_value_depth(value: object, field: str) -> None:
    stack: list[tuple[object, int]] = [(value, 1)]
    while stack:
        current, depth = stack.pop()
        if depth > MAX_DEPTH:
            refuse("NOE-E-BOUNDS.DEPTH", field, "value nesting exceeds the graph depth limit")
        if isinstance(current, dict):
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            stack.extend((item, depth + 1) for item in current)


def _safe_text(value: object, field: str, limit: int, *, controls: bool = False) -> str:
    if not isinstance(value, str):
        refuse("NOE-E-TYPE.STRING", field, "expected one UTF-8 string")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        refuse("NOE-E-SYNTAX.UNICODE", field, "string must contain Unicode scalar values")
    if len(encoded) > limit:
        refuse("NOE-E-BOUNDS.STRING", field, "string exceeds its UTF-8 byte limit")
    if unicodedata.normalize("NFC", value) != value:
        refuse("NOE-E-SYNTAX.UNICODE", field, "string must be NFC")
    for character in value:
        point = ord(character)
        category = unicodedata.category(character)
        if 0xD800 <= point <= 0xDFFF or point & 0xFFFF in {0xFFFE, 0xFFFF}:
            refuse("NOE-E-SYNTAX.UNICODE", field, "unsafe Unicode scalar value")
        if category == "Cf" or (not controls and category in {"Cc", "Cs"}):
            refuse("NOE-E-SYNTAX.UNICODE", field, "unsafe Unicode control character")
    return value


def _identifier(value: object, field: str, *, qualified: bool = False) -> str:
    text = _safe_text(value, field, MAX_IDENTIFIER_BYTES)
    if IDENTIFIER_RE.fullmatch(text) is None or ".." in text:
        refuse("NOE-E-TYPE.IDENTIFIER", field, "identifier is outside the closed alphabet")
    if qualified and "." not in text:
        refuse("NOE-E-TYPE.QUALIFIED", field, "name must be module-qualified")
    return text


def _exact_list(value: object, length: int, field: str) -> list[object]:
    if not isinstance(value, list) or len(value) != length:
        refuse("NOE-E-TYPE.ARITY", field, "record or term has the wrong fixed arity")
    return value


def _canonical_source(records: list[object]) -> bytes:
    output = bytearray(SOURCE_MAGIC.encode("ascii") + b"\n")
    for record in records:
        output.extend(_canonical_json(record))
        if len(output) > MAX_OUTPUT_BYTES:
            refuse("NOE-E-BOUNDS.OUTPUT", "source", "formatted source exceeds its byte limit")
    return bytes(output)


def _parse_source_lines(raw: bytes) -> list[object]:
    if len(raw) > MAX_INPUT_BYTES:
        refuse("NOE-E-BOUNDS.FILE", "source", "source exceeds its byte limit")
    if not raw.endswith(b"\n"):
        refuse("NOE-E-SYNTAX.FINAL_LF", "source", "source must end with exactly one LF")
    if raw.endswith(b"\n\n") or b"\r" in raw:
        refuse("NOE-E-SYNTAX.LINES", "source", "blank lines and CR bytes are forbidden")
    physical = raw.splitlines(keepends=True)
    if not physical or physical[0] != SOURCE_MAGIC.encode("ascii") + b"\n":
        refuse("NOE-E-SYNTAX.MAGIC", "source", "source must begin with the exact NOE1 record")
    for index, line in enumerate(physical):
        if len(line) > MAX_LINE_BYTES:
            refuse("NOE-E-BOUNDS.LINE", f"source.line[{index}]", "physical line exceeds its byte limit")
    if len(physical) - 1 > MAX_RECORDS:
        refuse("NOE-E-BOUNDS.RECORDS", "source", "source record count exceeds its limit")
    records: list[object] = []
    for index, line in enumerate(physical[1:], 1):
        records.append(_decode_json(line, f"source.line[{index}]", canonical=True))
    return records


class _Budget:
    def __init__(self) -> None:
        self.nodes = 0
        self.literal_bytes = 0

    def node(self, field: str) -> None:
        self.nodes += 1
        if self.nodes > MAX_GRAPH_NODES:
            refuse("NOE-E-BOUNDS.NODES", field, "graph node count exceeds its limit")

    def literal(self, count: int, field: str) -> None:
        self.literal_bytes += count
        if self.literal_bytes > MAX_LITERAL_TOTAL_BYTES:
            refuse("NOE-E-BOUNDS.LITERAL_TOTAL", field, "decoded literal bytes exceed their aggregate limit")


def _literal_value(kind: str, value: object, field: str) -> str:
    controls = kind in {"quote", "text", "bytes"}
    text = _safe_text(value, field, MAX_LITERAL_BYTES, controls=controls)
    if kind == "id":
        _identifier(text, field)
    elif kind == "path":
        _relative_path(text, field)
    elif kind == "sha256":
        _digest(text, field)
    elif kind == "number" and DECIMAL_RE.fullmatch(text) is None:
        refuse("NOE-E-TYPE.DECIMAL", field, "number literal must use canonical unsigned decimal")
    elif kind == "date":
        try:
            if date.fromisoformat(text).isoformat() != text:
                raise ValueError
        except ValueError:
            refuse("NOE-E-TYPE.DATE", field, "date literal must be a real YYYY-MM-DD date")
    elif kind == "url" and not text.startswith("https://"):
        refuse("NOE-E-TYPE.URL", field, "URL literal must use HTTPS")
    elif kind == "bytes" and (len(text) % 2 or re.fullmatch(r"[0-9a-f]*", text) is None):
        refuse("NOE-E-TYPE.BYTES", field, "bytes literal must use even-length lowercase hexadecimal")
    return text


def _read_canonical_json(path: Path, field: str) -> tuple[object, bytes]:
    raw = _read_regular(path, field, MAX_INPUT_BYTES)
    return _decode_json(raw, field, canonical=True), raw


def _module_path(directory: Path, module_id: str) -> Path:
    try:
        status = directory.lstat()
    except OSError:
        refuse("NOE-E-IO.READ", "modules", "module directory cannot be inspected")
    if not stat.S_ISDIR(status.st_mode) or stat.S_ISLNK(status.st_mode):
        refuse("NOE-E-PATH.DIRECTORY", "modules", "modules must be one real directory")
    leaf = f"{module_id}.json"
    if len(leaf.encode("utf-8")) > 255:
        refuse("NOE-E-PATH.LEAF", "modules", "module filename exceeds the leaf-name limit")
    return directory / leaf


def _validate_type(value: object, known_types: dict[str, str], field: str) -> str:
    name = _identifier(value, field, qualified=isinstance(value, str) and "." in value)
    if name not in known_types:
        refuse("NOE-E-TYPE.UNKNOWN", field, "unknown nominal type")
    return name


def _load_module_value(raw: bytes, expected_id: str, field: str) -> dict[str, object]:
    value = _decode_json(raw, field, canonical=True)
    module = _exact_keys(
        value,
        {"schema", "id", "imports", "types", "signatures", "definitions"},
        field,
    )
    if module["schema"] != MODULE_SCHEMA:
        refuse("NOE-E-TYPE.VERSION", f"{field}.schema", "unsupported module schema")
    module_id = _identifier(module["id"], f"{field}.id")
    if module_id != expected_id:
        refuse("NOE-E-REFERENCE.MODULE_ID", f"{field}.id", "module bytes carry a different identity")
    if module_id == "local" or module_id.startswith("local."):
        refuse(
            "NOE-E-REFERENCE.MODULE_NAMESPACE",
            f"{field}.id",
            "the local namespace is reserved for source definitions",
        )
    for key, limit in (("imports", MAX_IMPORTS), ("types", MAX_RECORDS), ("signatures", MAX_RECORDS), ("definitions", MAX_RECORDS)):
        if not isinstance(module[key], list) or len(module[key]) > limit:
            refuse("NOE-E-BOUNDS.MODULE", f"{field}.{key}", "module collection exceeds its limit")
    return module


def _load_modules(directory: Path, requested: list[tuple[str, str]]) -> dict[str, dict[str, object]]:
    loaded: dict[str, dict[str, object]] = {}
    visiting: set[str] = set()

    def visit(module_id: str, expected_digest: str) -> None:
        if module_id in visiting:
            refuse("NOE-E-REFERENCE.IMPORT_CYCLE", "modules", "module import graph contains a cycle")
        if module_id in loaded:
            if loaded[module_id]["sha256"] != expected_digest:
                refuse("NOE-E-DIGEST.MODULE", module_id, "one module identity binds multiple byte strings")
            return
        if len(loaded) + len(visiting) >= MAX_IMPORTS:
            refuse("NOE-E-BOUNDS.IMPORTS", "modules", "transitive module count exceeds its limit")
        visiting.add(module_id)
        path = _module_path(directory, module_id)
        raw = _read_regular(path, f"module.{module_id}", MAX_INPUT_BYTES)
        actual_digest = sha256(raw).hexdigest()
        if actual_digest != expected_digest:
            refuse("NOE-E-DIGEST.MODULE", module_id, "module digest does not match its import")
        module = _load_module_value(raw, module_id, f"module.{module_id}")
        imports: list[tuple[str, str]] = []
        previous = ""
        for index, item in enumerate(module["imports"]):
            entry = _exact_list(item, 2, f"module.{module_id}.imports[{index}]")
            child = _identifier(entry[0], f"module.{module_id}.imports[{index}].id")
            digest = _digest(entry[1], f"module.{module_id}.imports[{index}].sha256")
            if child <= previous:
                refuse("NOE-E-SYNTAX.ORDER", f"module.{module_id}.imports", "module imports must be unique and sorted")
            previous = child
            imports.append((child, digest))
        for child, digest in imports:
            visit(child, digest)
        loaded[module_id] = {"id": module_id, "sha256": actual_digest, "value": module}
        visiting.remove(module_id)

    for module_id, digest in requested:
        visit(module_id, digest)
    return loaded


def _validate_profile_value(
    value: object,
    expected_kernel_sha256: str | None,
) -> dict[str, object]:
    profile = _exact_keys(
        value,
        {"schema", "id", "alphabet", "tokenizer", "vocabulary_sha256", "kernel_sha256", "reserved", "aliases"},
        "profile",
    )
    if profile["schema"] != PROFILE_SCHEMA:
        refuse("NOE-E-TYPE.VERSION", "profile.schema", "unsupported projection profile")
    _identifier(profile["id"], "profile.id")
    if profile["alphabet"] != "ascii-printable-v1":
        refuse("NOE-E-TYPE.ALPHABET", "profile.alphabet", "unsupported projection alphabet")
    if not _safe_text(profile["tokenizer"], "profile.tokenizer", 256):
        refuse("NOE-E-TYPE.TOKENIZER", "profile.tokenizer", "tokenizer identity must not be empty")
    _digest(profile["vocabulary_sha256"], "profile.vocabulary_sha256")
    kernel_digest = _digest(profile["kernel_sha256"], "profile.kernel_sha256")
    if expected_kernel_sha256 is not None and kernel_digest != expected_kernel_sha256:
        refuse("NOE-E-DIGEST.KERNEL", "profile.kernel_sha256", "profile binds different kernel bytes")
    if not isinstance(profile["reserved"], list) or profile["reserved"] != sorted(RESERVED_SYMBOLS):
        refuse("NOE-E-REFERENCE.RESERVED", "profile.reserved", "profile must bind the exact reserved symbol set")
    aliases = profile["aliases"]
    if not isinstance(aliases, list) or len(aliases) > MAX_RECORDS:
        refuse("NOE-E-BOUNDS.ALIASES", "profile.aliases", "alias collection exceeds its limit")
    prior = ""
    targets: set[str] = set()
    for index, item in enumerate(aliases):
        if not isinstance(item, list) or len(item) != 2:
            refuse("NOE-E-ALIAS.SHAPE", f"profile.aliases[{index}]", "alias must be one source-target pair")
        source = _safe_text(item[0], f"profile.aliases[{index}].source", MAX_IDENTIFIER_BYTES)
        target = _safe_text(item[1], f"profile.aliases[{index}].target", 16)
        if not source or not target:
            refuse("NOE-E-ALIAS.SHAPE", f"profile.aliases[{index}]", "alias strings must not be empty")
        if source <= prior:
            refuse("NOE-E-SYNTAX.ORDER", "profile.aliases", "aliases must be unique and source-sorted")
        if ALIAS_RE.fullmatch(target) is None:
            refuse("NOE-E-ALIAS.ALPHABET", f"profile.aliases[{index}]", "alias is outside the profile alphabet")
        if target in targets or target in RESERVED_SYMBOLS:
            refuse("NOE-E-ALIAS.COLLISION", f"profile.aliases[{index}]", "alias target is not injective")
        prior = source
        targets.add(target)
    return profile


def _load_profile(path: Path, kernel_raw: bytes) -> tuple[dict[str, object], bytes, str]:
    value, raw = _read_canonical_json(path, "profile")
    profile = _validate_profile_value(value, sha256(kernel_raw).hexdigest())
    return profile, raw, sha256(raw).hexdigest()


def _bounded_decimal(value: object, field: str, maximum: int) -> int:
    text = _safe_text(value, field, 20)
    if DECIMAL_RE.fullmatch(text) is None:
        refuse("NOE-E-TYPE.DECIMAL", field, "expected canonical unsigned decimal text")
    if len(text) > len(str(maximum)) or (len(text) == len(str(maximum)) and text > str(maximum)):
        refuse("NOE-E-BOUNDS.INTEGER", field, "decimal value exceeds its closed limit")
    return int(text)


def _record_key(record: list[object], field: str) -> tuple[int, str]:
    if not record or not isinstance(record[0], str) or record[0] not in RECORD_RANK:
        refuse("NOE-E-TYPE.RECORD", field, "unknown record form")
    form = record[0]
    if form == "precedence":
        if len(record) < 3:
            refuse("NOE-E-TYPE.ARITY", field, "precedence record has the wrong fixed arity")
        return RECORD_RANK[form], f"{record[1]}\x00{record[2]}"
    if len(record) < 2 or not isinstance(record[1], str):
        refuse("NOE-E-TYPE.IDENTIFIER", field, "record identity is absent")
    return RECORD_RANK[form], record[1]


def _source_binding(value: object, field: str) -> list[object]:
    binding = _exact_list(value, 5, field)
    if binding[0] != "src":
        refuse("NOE-E-TYPE.SOURCE", field, "source binding must use the src tag")
    _relative_path(binding[1], f"{field}.path")
    _digest(binding[2], f"{field}.sha256")
    start = _bounded_decimal(binding[3], f"{field}.start", MAX_INPUT_BYTES)
    end = _bounded_decimal(binding[4], f"{field}.end", MAX_INPUT_BYTES)
    if end <= start:
        refuse("NOE-E-REFERENCE.SPAN", field, "source span must be non-empty and ordered")
    return binding


class _TypeContext:
    """One closed type environment; it never executes a graph definition."""

    def __init__(
        self,
        known_types: dict[str, str],
        signatures: dict[str, tuple[list[str], str]],
        definitions: dict[str, tuple[list[tuple[str, str]], object]],
        literals: dict[str, tuple[str, str]],
        budget: _Budget,
        type_owners: dict[str, str],
        symbol_owners: dict[str, str | None],
        definition_access: dict[str, set[str] | None],
    ) -> None:
        self.known_types = known_types
        self.signatures = signatures
        self.definitions = definitions
        self.literals = literals
        self.budget = budget
        self.type_owners = type_owners
        self.symbol_owners = symbol_owners
        self.definition_access = definition_access
        self.definition_returns: dict[str, str] = {}
        self.resolving_definitions = False
        self.active_modules: set[str] | None = None

    def compatible(self, actual: str, expected: str) -> bool:
        return actual == expected or self.known_types.get(actual) == expected

    def require(self, actual: str, expected: str, field: str) -> None:
        if not self.compatible(actual, expected):
            refuse("NOE-E-TYPE.MISMATCH", field, "term type does not match its closed position")

    def type_name(self, value: object, field: str) -> str:
        name = _validate_type(value, self.known_types, field)
        owner = self.type_owners.get(name)
        if self.active_modules is not None and owner is not None and owner not in self.active_modules:
            refuse(
                "NOE-E-REFERENCE.MODULE_AMBIENT",
                field,
                "module term uses a type outside its declared import closure",
            )
        return name

    def admit_symbol(self, name: str, field: str) -> None:
        if self.active_modules is None:
            return
        owner = self.symbol_owners.get(name)
        if owner is None or owner not in self.active_modules:
            refuse(
                "NOE-E-REFERENCE.MODULE_AMBIENT",
                field,
                "module term uses a symbol outside its declared import closure",
            )

    def definition_type(self, name: str) -> str:
        if name in self.definition_returns:
            return self.definition_returns[name]
        if name not in self.definitions:
            refuse("NOE-E-REFERENCE.DEFINITION", name, "definition is unresolved")
        if self.resolving_definitions:
            refuse("NOE-E-REFERENCE.DEFINITION_CYCLE", name, "definition graph contains a cycle")
        self.resolve_definitions()
        return self.definition_returns[name]

    def resolve_definitions(self) -> None:
        if len(self.definition_returns) == len(self.definitions):
            return
        if self.resolving_definitions:
            refuse("NOE-E-REFERENCE.DEFINITION_CYCLE", "definitions", "definition graph contains a cycle")
        self.resolving_definitions = True
        try:
            for name in _definition_order(self.definitions):
                if name in self.definition_returns:
                    continue
                parameters, body = self.definitions[name]
                previous_access = self.active_modules
                self.active_modules = self.definition_access[name]
                try:
                    result = self.term(
                        body,
                        dict(parameters),
                        f"definition.{name}.body",
                        pure=True,
                    )
                finally:
                    self.active_modules = previous_access
                if result == "directive":
                    refuse("NOE-E-TYPE.PURITY", name, "pure definition cannot produce a directive")
                self.definition_returns[name] = result
        finally:
            self.resolving_definitions = False

    def numeric(self, term: object) -> bool:
        if isinstance(term, list) and term:
            if term[0] == "$" and len(term) == 2 and term[1] in self.literals:
                return self.literals[term[1]][0] == "number"
            if term[0] == ":" and len(term) == 3 and term[1] == "value":
                return isinstance(term[2], str) and DECIMAL_RE.fullmatch(term[2]) is not None
        return False

    def term(
        self,
        value: object,
        variables: dict[str, str],
        field: str,
        *,
        pure: bool = False,
        depth: int = 1,
    ) -> str:
        if depth > MAX_DEPTH:
            refuse("NOE-E-BOUNDS.DEPTH", field, "term depth exceeds its limit")
        self.budget.node(field)
        if not isinstance(value, list) or not value or not isinstance(value[0], str):
            refuse("NOE-E-TYPE.TERM", field, "term must be one non-empty prefix array")
        tag = value[0]
        if tag == "$":
            term = _exact_list(value, 2, field)
            if self.active_modules is not None:
                refuse(
                    "NOE-E-REFERENCE.MODULE_AMBIENT",
                    field,
                    "module definition cannot bind a source-local literal",
                )
            literal_id = _identifier(term[1], f"{field}.literal")
            if literal_id not in self.literals:
                refuse("NOE-E-REFERENCE.LITERAL", field, "literal reference is unresolved")
            return LITERAL_TYPES[self.literals[literal_id][0]]
        if tag == "%":
            term = _exact_list(value, 2, field)
            name = _identifier(term[1], f"{field}.variable")
            if name not in variables:
                refuse("NOE-E-REFERENCE.VARIABLE", field, "variable reference is unbound")
            return variables[name]
        if tag == ":":
            term = _exact_list(value, 3, field)
            type_name = self.type_name(term[1], f"{field}.type")
            text = _safe_text(term[2], f"{field}.value", MAX_ATOM_BYTES)
            if type_name == "value" and len(text) > MAX_LITERAL_BYTES:
                refuse("NOE-E-BOUNDS.STRING", field, "typed atom exceeds its byte limit")
            return type_name
        if tag == "{}":
            if len(value) < 2:
                refuse("NOE-E-TYPE.ARITY", field, "finite set is missing its element type")
            if len(value) - 2 > MAX_SET_MEMBERS:
                refuse("NOE-E-BOUNDS.SET", field, "finite set exceeds its member limit")
            element_type = self.type_name(value[1], f"{field}.type")
            previous_member: bytes | None = None
            for index, member in enumerate(value[2:]):
                actual = self.term(member, variables, f"{field}[{index}]", pure=pure, depth=depth + 1)
                self.require(actual, element_type, f"{field}[{index}]")
                canonical_member = _canonical_json(member)
                if previous_member is not None and canonical_member <= previous_member:
                    refuse("NOE-E-SYNTAX.SET_ORDER", field, "finite set members must be unique and canonically sorted")
                previous_member = canonical_member
            return f"set:{element_type}"
        if tag in OPERATORS:
            if pure and tag in DIRECTIVE_OPERATORS:
                refuse("NOE-E-TYPE.PURITY", field, "pure definition contains a directive operator")
            return _term_operator(self, value, variables, field, pure=pure, depth=depth)
        if tag in self.signatures:
            self.admit_symbol(tag, field)
            parameters, result = self.signatures[tag]
            if len(value) - 1 != len(parameters):
                refuse("NOE-E-TYPE.ARITY", field, "predicate call has the wrong declared arity")
            for index, (argument, expected) in enumerate(zip(value[1:], parameters, strict=True)):
                actual = self.term(argument, variables, f"{field}[{index}]", pure=pure, depth=depth + 1)
                self.require(actual, expected, f"{field}[{index}]")
            return result
        if tag in self.definitions:
            self.admit_symbol(tag, field)
            parameters, _body = self.definitions[tag]
            if len(value) - 1 != len(parameters):
                refuse("NOE-E-TYPE.ARITY", field, "definition call has the wrong declared arity")
            for index, (argument, (_name, expected)) in enumerate(zip(value[1:], parameters, strict=True)):
                actual = self.term(argument, variables, f"{field}[{index}]", pure=pure, depth=depth + 1)
                self.require(actual, expected, f"{field}[{index}]")
            return self.definition_type(tag)
        if "." in tag:
            _identifier(tag, f"{field}.predicate", qualified=True)
            refuse("NOE-E-REFERENCE.PREDICATE", field, "qualified predicate is unresolved")
        refuse("NOE-E-TYPE.OPERATOR", field, "unknown structural operator")


def _term_operator(
    context: _TypeContext,
    value: list[object],
    variables: dict[str, str],
    field: str,
    *,
    pure: bool,
    depth: int,
) -> str:
    tag = value[0]

    def child(index: int) -> str:
        return context.term(
            value[index], variables, f"{field}[{index - 1}]", pure=pure, depth=depth + 1
        )

    if tag in {"!", "-", "+"}:
        _exact_list(value, 2, field)
        actual = child(1)
        if actual not in {"proposition", "effect"}:
            refuse("NOE-E-TYPE.MISMATCH", field, "directive operand must be proposition or effect")
        return "directive"
    if tag in {"?", "/"}:
        _exact_list(value, 3, field)
        context.require(child(1), "proposition", field)
        context.require(child(2), "directive", field)
        return "directive"
    if tag == "@":
        _exact_list(value, 3, field)
        context.require(child(1), "scope", field)
        context.require(child(2), "directive", field)
        return "directive"
    if tag == "^":
        _exact_list(value, 3, field)
        context.require(child(1), "actor", field)
        context.require(child(2), "directive", field)
        return "directive"
    if tag == ";":
        if len(value) < 2:
            refuse("NOE-E-TYPE.ARITY", field, "ordered directive sequence cannot be empty")
        for index in range(1, len(value)):
            context.require(child(index), "directive", field)
        return "directive"
    if tag in {"&", "|"}:
        if len(value) < 2:
            refuse("NOE-E-TYPE.ARITY", field, "boolean fold cannot be empty")
        for index in range(1, len(value)):
            context.require(child(index), "proposition", field)
        return "proposition"
    if tag == "~":
        _exact_list(value, 2, field)
        context.require(child(1), "proposition", field)
        return "proposition"
    if tag == "=":
        _exact_list(value, 3, field)
        left = child(1)
        right = child(2)
        if not (context.compatible(left, right) or context.compatible(right, left)):
            refuse("NOE-E-TYPE.MISMATCH", field, "equality operands have unlike types")
        return "proposition"
    if tag == "=>":
        _exact_list(value, 3, field)
        context.require(child(1), "proposition", field)
        context.require(child(2), "proposition", field)
        return "proposition"
    if tag == "<":
        _exact_list(value, 3, field)
        left = child(1)
        right = child(2)
        if not (context.compatible(left, right) or context.compatible(right, left)):
            refuse("NOE-E-TYPE.MISMATCH", field, "relation operands have unlike types")
        return "relation"
    if tag in {"all", "any", "one"}:
        _exact_list(value, 4, field)
        binder = _exact_list(value[1], 2, f"{field}.binder")
        name = _identifier(binder[0], f"{field}.binder.name")
        type_name = context.type_name(binder[1], f"{field}.binder.type")
        collection = child(2)
        if collection != f"set:{type_name}":
            refuse("NOE-E-TYPE.MISMATCH", field, "quantifier binder and finite set differ")
        nested = dict(variables)
        nested[name] = type_name
        body = context.term(value[3], nested, f"{field}.body", pure=pure, depth=depth + 1)
        context.require(body, "proposition", field)
        return "proposition"
    if tag == "in":
        _exact_list(value, 3, field)
        item_type = child(1)
        set_type = child(2)
        if set_type != f"set:{item_type}":
            refuse("NOE-E-TYPE.MISMATCH", field, "membership operands have unlike element types")
        return "proposition"
    if tag == "subset":
        _exact_list(value, 3, field)
        left = child(1)
        right = child(2)
        if left != right or not left.startswith("set:"):
            refuse("NOE-E-TYPE.MISMATCH", field, "subset operands must be like finite sets")
        return "proposition"
    if tag in {"lt", "le", "gt", "ge"}:
        _exact_list(value, 3, field)
        child(1)
        child(2)
        if not context.numeric(value[1]) or not context.numeric(value[2]):
            refuse("NOE-E-TYPE.DECIMAL", field, "comparison operands must be canonical decimal values")
        return "proposition"
    if tag == "count":
        _exact_list(value, 2, field)
        if not child(1).startswith("set:"):
            refuse("NOE-E-TYPE.MISMATCH", field, "count operand must be one finite set")
        return "value"
    refuse("NOE-E-TYPE.OPERATOR", field, "unknown structural operator")


def _parameters(value: object, known_types: dict[str, str], field: str) -> list[tuple[str, str]]:
    if not isinstance(value, list) or len(value) > 64:
        refuse("NOE-E-BOUNDS.PARAMETERS", field, "parameter list exceeds its limit")
    result: list[tuple[str, str]] = []
    names: set[str] = set()
    for index, item in enumerate(value):
        pair = _exact_list(item, 2, f"{field}[{index}]")
        name = _identifier(pair[0], f"{field}[{index}].name")
        if name in names:
            refuse("NOE-E-REFERENCE.DUPLICATE_ID", field, "parameter name is duplicated")
        names.add(name)
        result.append((name, _validate_type(pair[1], known_types, f"{field}[{index}].type")))
    return result


def _module_closures(modules: dict[str, dict[str, object]]) -> dict[str, set[str]]:
    direct: dict[str, set[str]] = {}
    for module_id in sorted(modules):
        module = modules[module_id]["value"]
        assert isinstance(module, dict)
        children: set[str] = set()
        for index, item in enumerate(module["imports"]):
            entry = _exact_list(item, 2, f"module.{module_id}.imports[{index}]")
            child = _identifier(entry[0], f"module.{module_id}.imports[{index}].id")
            if child not in modules:
                refuse(
                    "NOE-E-REFERENCE.MODULE_AMBIENT",
                    f"module.{module_id}.imports[{index}]",
                    "module import is absent from the loaded registry",
                )
            children.add(child)
        direct[module_id] = children

    closures: dict[str, set[str]] = {}
    for module_id in sorted(modules):
        closure = {module_id}
        pending = list(direct[module_id])
        while pending:
            child = pending.pop()
            if child in closure:
                continue
            closure.add(child)
            pending.extend(direct[child])
        closures[module_id] = closure
    return closures


def _module_type(
    value: object,
    known_types: dict[str, str],
    type_owners: dict[str, str],
    allowed_modules: set[str],
    field: str,
) -> str:
    name = _validate_type(value, known_types, field)
    owner = type_owners.get(name)
    if owner is not None and owner not in allowed_modules:
        refuse(
            "NOE-E-REFERENCE.MODULE_AMBIENT",
            field,
            "module declaration uses a type outside its declared import closure",
        )
    return name


def _build_registry(
    modules: dict[str, dict[str, object]],
    source_definitions: list[list[object]],
    literals: dict[str, tuple[str, str]],
    budget: _Budget,
) -> _TypeContext:
    known_types = {name: name for name in CORE_TYPES}
    known_types.update({name: name for name in ("proposition", "directive", "relation")})
    type_owners: dict[str, str] = {}
    module_closures = _module_closures(modules)

    for module_id in sorted(modules):
        module = modules[module_id]["value"]
        assert isinstance(module, dict)
        previous = ""
        for index, item in enumerate(module["types"]):
            pair = _exact_list(item, 2, f"module.{module_id}.types[{index}]")
            name = _identifier(pair[0], f"module.{module_id}.types[{index}].name", qualified=True)
            parent = _identifier(pair[1], f"module.{module_id}.types[{index}].parent")
            if not name.startswith(module_id + ".") or parent not in CORE_TYPES:
                refuse("NOE-E-TYPE.SUBTYPE", f"module.{module_id}.types[{index}]", "nominal subtype escapes its module or core parent")
            if name <= previous or name in known_types:
                refuse("NOE-E-REFERENCE.DUPLICATE_ID", f"module.{module_id}.types", "module types must be unique and sorted")
            previous = name
            known_types[name] = parent
            type_owners[name] = module_id

    signatures: dict[str, tuple[list[str], str]] = {}
    definitions: dict[str, tuple[list[tuple[str, str]], object]] = {}
    symbol_owners: dict[str, str | None] = {}
    definition_access: dict[str, set[str] | None] = {}
    for module_id in sorted(modules):
        module = modules[module_id]["value"]
        assert isinstance(module, dict)
        allowed_modules = module_closures[module_id]
        previous = ""
        for index, item in enumerate(module["signatures"]):
            entry = _exact_list(item, 3, f"module.{module_id}.signatures[{index}]")
            name = _identifier(entry[0], f"module.{module_id}.signatures[{index}].name", qualified=True)
            if not name.startswith(module_id + ".") or name <= previous or name in signatures:
                refuse("NOE-E-REFERENCE.DUPLICATE_ID", f"module.{module_id}.signatures", "signatures must be namespaced, unique and sorted")
            if not isinstance(entry[1], list) or len(entry[1]) > 64:
                refuse("NOE-E-BOUNDS.PARAMETERS", f"module.{module_id}.signatures[{index}]", "signature arity exceeds its limit")
            parameters = [
                _module_type(
                    item_type,
                    known_types,
                    type_owners,
                    allowed_modules,
                    f"module.{module_id}.signatures[{index}].parameters",
                )
                for item_type in entry[1]
            ]
            result = _module_type(
                entry[2],
                known_types,
                type_owners,
                allowed_modules,
                f"module.{module_id}.signatures[{index}].result",
            )
            previous = name
            signatures[name] = (parameters, result)
            symbol_owners[name] = module_id
        previous = ""
        for index, item in enumerate(module["definitions"]):
            entry = _exact_list(item, 3, f"module.{module_id}.definitions[{index}]")
            name = _identifier(entry[0], f"module.{module_id}.definitions[{index}].name", qualified=True)
            if not name.startswith(module_id + ".") or name <= previous or name in definitions or name in signatures:
                refuse("NOE-E-REFERENCE.DUPLICATE_ID", f"module.{module_id}.definitions", "definitions must be namespaced, unique and sorted")
            parameters = _parameters(entry[1], known_types, f"module.{module_id}.definitions[{index}].parameters")
            for parameter_index, (_parameter, parameter_type) in enumerate(parameters):
                owner = type_owners.get(parameter_type)
                if owner is not None and owner not in allowed_modules:
                    refuse(
                        "NOE-E-REFERENCE.MODULE_AMBIENT",
                        f"module.{module_id}.definitions[{index}].parameters[{parameter_index}]",
                        "module definition uses a type outside its declared import closure",
                    )
            previous = name
            definitions[name] = (parameters, entry[2])
            symbol_owners[name] = module_id
            definition_access[name] = allowed_modules

    for index, record in enumerate(source_definitions):
        name = _identifier(record[1], f"source.definition[{index}].name", qualified=True)
        if not name.startswith("local.") or name in definitions or name in signatures:
            refuse("NOE-E-REFERENCE.DUPLICATE_ID", f"source.definition[{index}]", "source definition must be unique in the local namespace")
        definitions[name] = (
            _parameters(record[2], known_types, f"source.definition[{index}].parameters"),
            record[3],
        )
        symbol_owners[name] = None
        definition_access[name] = None

    context = _TypeContext(
        known_types,
        signatures,
        definitions,
        literals,
        budget,
        type_owners,
        symbol_owners,
        definition_access,
    )
    context.resolve_definitions()
    return context


def _term_children(value: object) -> list[object]:
    if not isinstance(value, list) or not value:
        return []
    if value[0] in {"$", "%", ":"}:
        return []
    if value[0] == "{}":
        return value[2:]
    if value[0] in {"all", "any", "one"}:
        return value[2:]
    return value[1:]


def _definition_dependencies(
    value: object,
    definitions: dict[str, tuple[list[tuple[str, str]], object]],
) -> set[str]:
    found: set[str] = set()
    pending = [value]
    while pending:
        current = pending.pop()
        if not isinstance(current, list) or not current:
            continue
        tag = current[0]
        if isinstance(tag, str) and tag in definitions:
            found.add(tag)
        pending.extend(_term_children(current))
    return found


def _definition_order(
    definitions: dict[str, tuple[list[tuple[str, str]], object]],
) -> list[str]:
    dependencies = {
        name: _definition_dependencies(body, definitions)
        for name, (_parameters, body) in definitions.items()
    }
    dependents = {name: set() for name in definitions}
    for name, required in dependencies.items():
        for dependency in required:
            dependents[dependency].add(name)
    remaining = {name: len(required) for name, required in dependencies.items()}
    ready = [name for name, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        name = heapq.heappop(ready)
        ordered.append(name)
        for dependent in sorted(dependents[name]):
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(ordered) != len(definitions):
        refuse(
            "NOE-E-REFERENCE.DEFINITION_CYCLE",
            "definitions",
            "definition graph contains a cycle",
        )
    return ordered


def _expanded_term_size(
    value: object,
    definitions: dict[str, tuple[list[tuple[str, str]], object]],
    memo: dict[str, int],
) -> int:
    total = 0
    pending = [value]
    while pending:
        current = pending.pop()
        total += 1
        if total > MAX_EXPANDED_NODES:
            refuse("NOE-E-BOUNDS.EXPANSION", "graph", "macro expansion exceeds its node limit")
        if not isinstance(current, list) or not current:
            continue
        tag = current[0]
        if isinstance(tag, str) and tag in definitions:
            if tag not in memo:
                refuse("NOE-E-REFERENCE.DEFINITION", tag, "definition expansion order is incomplete")
            total += memo[tag]
            if total > MAX_EXPANDED_NODES:
                refuse("NOE-E-BOUNDS.EXPANSION", "graph", "macro expansion exceeds its node limit")
        pending.extend(_term_children(current))
    return total


def _expanded_size(
    value: object,
    definitions: dict[str, tuple[list[tuple[str, str]], object]],
    memo: dict[str, int],
) -> int:
    roots = _definition_dependencies(value, definitions)
    active: set[str] = set()
    for root in sorted(roots):
        if root in memo:
            continue
        pending: list[tuple[str, bool]] = [(root, False)]
        while pending:
            name, leaving = pending.pop()
            if name in memo:
                continue
            if leaving:
                memo[name] = _expanded_term_size(definitions[name][1], definitions, memo)
                active.remove(name)
                continue
            if name in active:
                refuse("NOE-E-REFERENCE.DEFINITION_CYCLE", name, "definition graph contains a cycle")
            active.add(name)
            pending.append((name, True))
            for dependency in sorted(
                _definition_dependencies(definitions[name][1], definitions),
                reverse=True,
            ):
                if dependency in active:
                    refuse(
                        "NOE-E-REFERENCE.DEFINITION_CYCLE",
                        dependency,
                        "definition graph contains a cycle",
                    )
                if dependency not in memo:
                    pending.append((dependency, False))
    return _expanded_term_size(value, definitions, memo)


def _assert_term(
    context: _TypeContext,
    value: object,
    expected: str,
    field: str,
) -> None:
    context.require(context.term(value, {}, field), expected, field)


def _acyclic_edges(edges: dict[str, set[str]], field: str) -> None:
    state: dict[str, int] = {}
    for root in sorted(edges):
        if state.get(root) == 2:
            continue
        pending: list[tuple[str, bool]] = [(root, False)]
        while pending:
            node, leaving = pending.pop()
            if leaving:
                state[node] = 2
                continue
            status = state.get(node, 0)
            if status == 2:
                continue
            if status == 1:
                refuse(
                    "NOE-E-REFERENCE.RELATION_CYCLE",
                    field,
                    "governing relation contains a cycle",
                )
            state[node] = 1
            pending.append((node, True))
            for child in sorted(edges.get(node, set()), reverse=True):
                child_status = state.get(child, 0)
                if child_status == 1:
                    refuse(
                        "NOE-E-REFERENCE.RELATION_CYCLE",
                        field,
                        "governing relation contains a cycle",
                    )
                if child_status == 0:
                    pending.append((child, False))


def _preflight_records(records: list[object]) -> tuple[list[tuple[str, str]], list[list[object]]]:
    imports: list[tuple[str, str]] = []
    definitions: list[list[object]] = []
    previous_key: tuple[int, str] | None = None
    lengths = {
        "import": 3,
        "literal": 5,
        "definition": 4,
        "rule": 4,
        "precedence": 6,
        "override": 7,
        "transition": 8,
        "promise": 11,
        "handoff": 11,
        "exception": 9,
    }
    for index, item in enumerate(records):
        if not isinstance(item, list) or not item or item[0] not in lengths:
            refuse("NOE-E-TYPE.RECORD", f"source.record[{index}]", "unknown record form")
        record = _exact_list(item, lengths[item[0]], f"source.record[{index}]")
        key = _record_key(record, f"source.record[{index}]")
        if previous_key is not None and key <= previous_key:
            refuse("NOE-E-SYNTAX.ORDER", f"source.record[{index}]", "records must be unique and in canonical form/id order")
        previous_key = key
        if record[0] == "import":
            module_id = _identifier(record[1], f"source.record[{index}].id")
            imports.append((module_id, _digest(record[2], f"source.record[{index}].sha256")))
        elif record[0] == "definition":
            definitions.append(record)
    if len(imports) > MAX_IMPORTS:
        refuse("NOE-E-BOUNDS.IMPORTS", "source", "import count exceeds its limit")
    return imports, definitions


def _compile_records(
    records: list[object],
    modules: dict[str, dict[str, object]],
    source_raw: bytes,
) -> dict[str, object]:
    budget = _Budget()
    for module_id in sorted(modules):
        budget.node(f"module.{module_id}")
        module_value = modules[module_id]["value"]
        assert isinstance(module_value, dict)
        for collection in ("imports", "types", "signatures", "definitions"):
            for index, _item in enumerate(module_value[collection]):
                budget.node(f"module.{module_id}.{collection}[{index}]")
    literals: dict[str, tuple[str, str]] = {}
    rules: set[str] = set()
    node_ids: set[str] = set()
    source_definitions: list[list[object]] = []
    precedence_edges: dict[str, set[str]] = {}
    source_spans: dict[str, tuple[str, list[tuple[int, int]]]] = {}
    source_payloads: dict[str, bytes] = {}
    source_boundaries: dict[str, set[int]] = {}
    source_identities: dict[tuple[int, int], str] = {}
    repository_root = Path(__file__).resolve().parents[1]

    for index, value in enumerate(records):
        assert isinstance(value, list)
        record = value
        form = record[0]
        field = f"source.record[{index}]"
        budget.node(field)
        if form == "import":
            continue
        if form == "literal":
            literal_id = _identifier(record[1], f"{field}.id")
            kind = _safe_text(record[2], f"{field}.kind", 16)
            if kind not in LITERAL_KINDS:
                refuse("NOE-E-TYPE.LITERAL_KIND", field, "unknown literal kind")
            value_text = _literal_value(kind, record[4], f"{field}.value")
            byte_count = _bounded_decimal(record[3], f"{field}.bytes", MAX_LITERAL_BYTES)
            if byte_count != len(value_text.encode("utf-8")):
                refuse("NOE-E-DIGEST.LITERAL_SIZE", field, "literal byte count does not match exact UTF-8")
            if literal_id in literals or literal_id in node_ids:
                refuse("NOE-E-REFERENCE.DUPLICATE_ID", field, "record id is duplicated")
            literals[literal_id] = (kind, value_text)
            node_ids.add(literal_id)
            budget.literal(byte_count, field)
        elif form == "definition":
            definition_id = _identifier(record[1], f"{field}.id", qualified=True)
            if definition_id in node_ids:
                refuse("NOE-E-REFERENCE.DUPLICATE_ID", field, "record id is duplicated")
            node_ids.add(definition_id)
            source_definitions.append(record)
        elif form == "precedence":
            continue
        else:
            record_id = _identifier(record[1], f"{field}.id")
            if record_id in node_ids:
                refuse("NOE-E-REFERENCE.DUPLICATE_ID", field, "record id is duplicated")
            node_ids.add(record_id)
            if form == "rule":
                rules.add(record_id)

    context = _build_registry(modules, source_definitions, literals, budget)

    terms: list[object] = []
    for index, value in enumerate(records):
        assert isinstance(value, list)
        record = value
        form = record[0]
        field = f"source.record[{index}]"
        if form in {"import", "literal", "definition"}:
            continue
        if form == "rule":
            _assert_term(context, record[2], "directive", f"{field}.directive")
            terms.append(record[2])
            binding = _source_binding(record[3], f"{field}.source")
            path = binding[1]
            digest = binding[2]
            start = int(binding[3])
            end = int(binding[4])
            assert isinstance(path, str) and isinstance(digest, str)
            prior_digest, spans = source_spans.setdefault(path, (digest, []))
            if prior_digest != digest:
                refuse("NOE-E-REFERENCE.SOURCE_ID", field, "one source path binds multiple blob identities")
            if path not in source_payloads:
                payload, identity = _read_repository_regular(
                    repository_root,
                    path,
                    f"{field}.source",
                    MAX_INPUT_BYTES,
                )
                if identity in source_identities and source_identities[identity] != path:
                    refuse("NOE-E-REFERENCE.SOURCE_ALIAS", field, "one source file is named by multiple paths")
                source_identities[identity] = path
                if sha256(payload).hexdigest() != digest:
                    refuse("NOE-E-DIGEST.SOURCE", field, "bound source digest differs from repository bytes")
                try:
                    source_text = payload.decode("utf-8")
                except UnicodeDecodeError:
                    refuse("NOE-E-SYNTAX.SOURCE_UTF8", field, "bound source must be valid UTF-8")
                boundaries = {0}
                offset = 0
                for character in source_text:
                    offset += len(character.encode("utf-8"))
                    boundaries.add(offset)
                source_payloads[path] = payload
                source_boundaries[path] = boundaries
            if end > len(source_payloads[path]):
                refuse("NOE-E-REFERENCE.SPAN", field, "source span exceeds the bound file")
            if start not in source_boundaries[path] or end not in source_boundaries[path]:
                refuse("NOE-E-REFERENCE.SPAN_UTF8", field, "source span splits one UTF-8 scalar value")
            if any(start < old_end and old_start < end for old_start, old_end in spans):
                refuse("NOE-E-REFERENCE.SPAN", field, "source spans overlap")
            spans.append((start, end))
        elif form == "precedence":
            higher = _identifier(record[1], f"{field}.higher")
            lower = _identifier(record[2], f"{field}.lower")
            if higher not in rules or lower not in rules or higher == lower:
                refuse("NOE-E-REFERENCE.RULE", field, "precedence names absent or identical rules")
            precedence_edges.setdefault(higher, set()).add(lower)
            _assert_term(context, record[3], "actor", f"{field}.authority")
            _assert_term(context, record[4], "scope", f"{field}.scope")
            _assert_term(context, record[5], "evidence", f"{field}.evidence")
            terms.extend(record[3:6])
        elif form == "override":
            _assert_term(context, record[2], "actor", f"{field}.authority")
            high = _identifier(record[3], f"{field}.high")
            low = _identifier(record[4], f"{field}.low")
            if high not in rules or low not in rules or high == low:
                refuse("NOE-E-REFERENCE.RULE", field, "override names absent or identical rules")
            precedence_edges.setdefault(high, set()).add(low)
            _assert_term(context, record[5], "scope", f"{field}.scope")
            _assert_term(context, record[6], "evidence", f"{field}.evidence")
            terms.extend((record[2], record[5], record[6]))
        elif form == "transition":
            for position, expected in ((2, "state"), (3, "state"), (4, "event"), (5, "proposition"), (6, "state"), (7, "directive")):
                _assert_term(context, record[position], expected, f"{field}[{position}]")
                terms.append(record[position])
        elif form == "promise":
            expected = ("actor", "claim", "evidence", "set:evidence", "scope", "directive", "directive", "directive", "value")
            for position, kind in enumerate(expected, 2):
                _assert_term(context, record[position], kind, f"{field}[{position}]")
                terms.append(record[position])
        elif form == "handoff":
            expected = ("actor", "actor", "artifact", "scope", "evidence", "set:evidence", "value", "action", "set:evidence")
            for position, kind in enumerate(expected, 2):
                _assert_term(context, record[position], kind, f"{field}[{position}]")
                terms.append(record[position])
        elif form == "exception":
            expected = ("actor", "proposition", "effect", "scope", "evidence", "value", "directive")
            for position, kind in enumerate(expected, 2):
                _assert_term(context, record[position], kind, f"{field}[{position}]")
                terms.append(record[position])

    _acyclic_edges(precedence_edges, "precedence")
    expansion = 0
    memo: dict[str, int] = {}
    for term in terms:
        expansion += _expanded_size(term, context.definitions, memo)
        if expansion > MAX_EXPANDED_NODES:
            refuse("NOE-E-BOUNDS.EXPANSION", "graph", "macro expansion exceeds its node limit")

    module_values = [modules[name] for name in sorted(modules)]
    return {
        "schema": GRAPH_SCHEMA,
        "source_sha256": sha256(source_raw).hexdigest(),
        "records": records,
        "modules": module_values,
    }


def compile_source(
    source_raw: bytes,
    modules_directory: Path,
    profile_path: Path,
    kernel_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    records = _parse_source_lines(source_raw)
    imports, _definitions = _preflight_records(records)
    modules = _load_modules(modules_directory, imports)
    graph = _compile_records(records, modules, source_raw)
    graph_raw = _canonical_json(graph)
    graph_digest = sha256(graph_raw).hexdigest()
    kernel_raw = _read_regular(kernel_path, "kernel", MAX_INPUT_BYTES)
    _profile, profile_raw, profile_digest = _load_profile(profile_path, kernel_raw)
    compiler_raw = _read_regular(Path(__file__).resolve(), "compiler", MAX_INPUT_BYTES)
    lock = {
        "schema": "noema-lock/v1",
        "source_sha256": sha256(source_raw).hexdigest(),
        "graph_sha256": graph_digest,
        "compiler_sha256": sha256(compiler_raw).hexdigest(),
        "kernel_sha256": sha256(kernel_raw).hexdigest(),
        "profile_sha256": profile_digest,
        "modules": [
            {"id": name, "sha256": modules[name]["sha256"]}
            for name in sorted(modules)
        ],
    }
    build = {"schema": BUILD_SCHEMA, "graph": graph, "lock": lock}
    build_raw = _canonical_json(build)
    return build, {
        "source": source_raw,
        "graph": graph_raw,
        "build": build_raw,
        "profile": profile_raw,
        "kernel": kernel_raw,
    }


def _verify_build_value(
    value: object,
    modules_directory: Path,
    profile_path: Path,
    kernel_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    build = _exact_keys(value, {"schema", "graph", "lock"}, "build")
    if build["schema"] != BUILD_SCHEMA:
        refuse("NOE-E-TYPE.VERSION", "build.schema", "unsupported build schema")
    graph = _exact_keys(build["graph"], {"schema", "source_sha256", "records", "modules"}, "build.graph")
    if graph["schema"] != GRAPH_SCHEMA or not isinstance(graph["records"], list):
        refuse("NOE-E-TYPE.GRAPH", "build.graph", "build does not carry one closed version-1 graph")
    source_raw = _canonical_source(graph["records"])
    expected, artifacts = compile_source(source_raw, modules_directory, profile_path, kernel_path)
    if build != expected:
        refuse("NOE-E-DIGEST.BUILD", "build", "build graph or lock is stale")
    return build, artifacts


def load_build(
    path: Path,
    modules_directory: Path,
    profile_path: Path,
    kernel_path: Path,
) -> tuple[dict[str, object], bytes, dict[str, object]]:
    value, raw = _read_canonical_json(path, "build")
    build, artifacts = _verify_build_value(value, modules_directory, profile_path, kernel_path)
    return build, raw, artifacts


def _atomic_write(path: Path, payload: bytes) -> None:
    if len(payload) > MAX_OUTPUT_BYTES:
        refuse("NOE-E-BOUNDS.OUTPUT", "output", "derived output exceeds its byte limit")
    if path.name in {"", ".", ".."} or len(path.name.encode("utf-8")) > 255:
        refuse("NOE-E-PATH.LEAF", "output", "output leaf name is invalid")
    parent = path.parent
    try:
        parent_status = parent.lstat()
    except OSError:
        refuse("NOE-E-IO.WRITE", "output", "output directory cannot be inspected")
    if not stat.S_ISDIR(parent_status.st_mode) or stat.S_ISLNK(parent_status.st_mode):
        refuse("NOE-E-PATH.DIRECTORY", "output", "output parent must be one real directory")
    try:
        target_status = path.lstat()
    except FileNotFoundError:
        target_status = None
    except OSError:
        refuse("NOE-E-IO.WRITE", "output", "output target cannot be inspected")
    if target_status is not None and not stat.S_ISREG(target_status.st_mode):
        refuse("NOE-E-PATH.REGULAR", "output", "existing output must be a regular file")

    descriptor = -1
    directory_descriptor = -1
    temporary_name: str | None = None
    replaced = False
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".noema-write-", dir=parent)
        os.fchmod(descriptor, 0o600)
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("short atomic write")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary_name, path)
        replaced = True
        temporary_name = None
        flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        directory_descriptor = os.open(parent, flags)
        os.fsync(directory_descriptor)
        os.close(directory_descriptor)
        directory_descriptor = -1
    except OSError:
        refuse(
            "NOE-E-IO.SYNC" if replaced else "NOE-E-IO.WRITE",
            "output",
            "atomic output could not be durably completed",
        )
    finally:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if directory_descriptor >= 0:
            try:
                os.close(directory_descriptor)
            except OSError:
                pass
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass


def _strings(value: object) -> set[str]:
    result: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            result.add(current)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, dict):
            stack.extend(current.keys())
            stack.extend(current.values())
    return result


def _replace_strings(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_replace_strings(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            replacements.get(key, key): _replace_strings(item, replacements)
            for key, item in value.items()
        }
    return value


def _projection_namespaces(graph: dict[str, object]) -> dict[str, set[str]]:
    namespaces: dict[str, set[str]] = {}

    def bind(value: object, namespace: str) -> None:
        if isinstance(value, str):
            namespaces.setdefault(value, set()).add(namespace)

    for symbol in RESERVED_SYMBOLS:
        bind(symbol, "reserved")
    modules = graph.get("modules")
    if isinstance(modules, list):
        for module in modules:
            if not isinstance(module, dict):
                continue
            value = module.get("value")
            if not isinstance(value, dict):
                continue
            signatures = value.get("signatures")
            if isinstance(signatures, list):
                for signature in signatures:
                    if isinstance(signature, list) and signature:
                        bind(signature[0], "predicate")
            definitions = value.get("definitions")
            if isinstance(definitions, list):
                for definition in definitions:
                    if isinstance(definition, list) and definition:
                        bind(definition[0], "definition")
    records = graph.get("records")
    if isinstance(records, list):
        for record in records:
            if not isinstance(record, list) or len(record) < 2:
                continue
            if record[0] == "definition":
                bind(record[1], "definition")
            elif record[0] == "literal" and len(record) == 5:
                bind(record[1], "literal-id")
                bind(record[4], "literal-value")
    return namespaces


def _projection_aliases(profile: dict[str, object], graph: dict[str, object]) -> dict[str, str]:
    visible = _strings(graph)
    namespaces = _projection_namespaces(graph)
    aliases: dict[str, str] = {}
    targets: set[str] = set()
    for index, item in enumerate(profile["aliases"]):
        assert isinstance(item, list)
        source, target = item
        assert isinstance(source, str) and isinstance(target, str)
        if len(namespaces.get(source, ())) > 1:
            refuse("NOE-E-ALIAS.OVERLOAD", f"profile.aliases[{index}]", "alias source occupies multiple semantic namespaces")
        if target in visible or target in RESERVED_SYMBOLS or target in targets:
            refuse("NOE-E-ALIAS.COLLISION", f"profile.aliases[{index}]", "alias collides with visible graph text")
        aliases[source] = target
        targets.add(target)
    return aliases


def _projection_lock(value: object) -> dict[str, object]:
    lock = _exact_keys(
        value,
        {"schema", "source_sha256", "graph_sha256", "compiler_sha256", "kernel_sha256", "profile_sha256", "modules"},
        "projection.lock",
    )
    if lock["schema"] != "noema-lock/v1":
        refuse("NOE-E-TYPE.VERSION", "projection.lock.schema", "unsupported lock schema")
    for key in ("source_sha256", "graph_sha256", "compiler_sha256", "kernel_sha256", "profile_sha256"):
        _digest(lock[key], f"projection.lock.{key}")
    modules = lock["modules"]
    if not isinstance(modules, list) or len(modules) > MAX_IMPORTS:
        refuse("NOE-E-BOUNDS.IMPORTS", "projection.lock.modules", "lock module count exceeds its limit")
    previous = ""
    for index, value in enumerate(modules):
        module = _exact_keys(value, {"id", "sha256"}, f"projection.lock.modules[{index}]")
        module_id = _identifier(module["id"], f"projection.lock.modules[{index}].id")
        _digest(module["sha256"], f"projection.lock.modules[{index}].sha256")
        if module_id <= previous:
            refuse("NOE-E-SYNTAX.ORDER", "projection.lock.modules", "lock modules must be unique and sorted")
        previous = module_id
    return lock


def project_build(
    build: dict[str, object],
    profile: dict[str, object],
    profile_digest: str,
) -> dict[str, object]:
    profile = _validate_profile_value(profile, None)
    graph = build["graph"]
    lock = build["lock"]
    assert isinstance(graph, dict) and isinstance(lock, dict)
    aliases = _projection_aliases(profile, graph)
    graph_digest = sha256(_canonical_json(graph)).hexdigest()
    projected_graph = _replace_strings(graph, aliases)
    projected_line = _canonical_json(projected_graph)
    header = f"{PROJECTION_MAGIC} {profile_digest} {graph_digest}\n".encode("ascii")
    projection = header + projected_line
    if len(projection) > MAX_OUTPUT_BYTES:
        refuse("NOE-E-BOUNDS.OUTPUT", "projection", "projection exceeds its byte limit")
    projection_digest = sha256(projection).hexdigest()
    manifest = {
        "schema": PROJECTION_MANIFEST_SCHEMA,
        "graph_sha256": graph_digest,
        "lock_sha256": sha256(_canonical_json(lock)).hexdigest(),
        "profile_sha256": profile_digest,
        "aliases_sha256": sha256(_canonical_json(profile["aliases"])).hexdigest(),
        "projection_sha256": projection_digest,
    }
    bundle = {
        "schema": PROJECTION_SCHEMA,
        "lock": lock,
        "manifest": manifest,
        "text": projection.decode("utf-8"),
    }
    recovered = recover_projection(bundle, profile)
    if recovered != graph:
        refuse("NOE-E-DIGEST.RECOVERY", "projection", "projection does not recover the same graph")
    _canonical_json(bundle)
    return bundle


def recover_projection(bundle_value: object, profile: dict[str, object]) -> dict[str, object]:
    profile = _validate_profile_value(profile, None)
    bundle = _exact_keys(bundle_value, {"schema", "lock", "manifest", "text"}, "projection")
    if bundle["schema"] != PROJECTION_SCHEMA:
        refuse("NOE-E-TYPE.VERSION", "projection.schema", "unsupported projection bundle")
    manifest = _exact_keys(
        bundle["manifest"],
        {"schema", "graph_sha256", "lock_sha256", "profile_sha256", "aliases_sha256", "projection_sha256"},
        "projection.manifest",
    )
    if manifest["schema"] != PROJECTION_MANIFEST_SCHEMA:
        refuse("NOE-E-TYPE.VERSION", "projection.manifest.schema", "unsupported projection manifest")
    for key in ("graph_sha256", "lock_sha256", "profile_sha256", "aliases_sha256", "projection_sha256"):
        _digest(manifest[key], f"projection.manifest.{key}")
    lock = _projection_lock(bundle["lock"])
    if sha256(_canonical_json(lock)).hexdigest() != manifest["lock_sha256"]:
        refuse("NOE-E-DIGEST.LOCK", "projection", "projection manifest binds different lock bytes")
    if lock["graph_sha256"] != manifest["graph_sha256"] or lock["profile_sha256"] != manifest["profile_sha256"]:
        refuse("NOE-E-DIGEST.LOCK", "projection", "projection lock and manifest identities differ")
    if sha256(_canonical_json(profile)).hexdigest() != manifest["profile_sha256"]:
        refuse("NOE-E-DIGEST.PROFILE", "projection", "projection manifest binds different profile bytes")
    aliases = profile.get("aliases")
    if not isinstance(aliases, list) or sha256(_canonical_json(aliases)).hexdigest() != manifest["aliases_sha256"]:
        refuse("NOE-E-DIGEST.PROFILE", "projection", "projection manifest binds a different alias dictionary")
    text = _safe_text(bundle["text"], "projection.text", MAX_OUTPUT_BYTES, controls=True)
    raw = text.encode("utf-8")
    if sha256(raw).hexdigest() != manifest["projection_sha256"]:
        refuse("NOE-E-DIGEST.PROJECTION", "projection", "projection bytes do not match the manifest")
    lines = raw.split(b"\n")
    if len(lines) != 3 or lines[-1] != b"":
        refuse("NOE-E-SYNTAX.PROJECTION", "projection", "projection must contain one header and one graph line")
    try:
        header = lines[0].decode("ascii").split(" ")
    except UnicodeDecodeError:
        refuse("NOE-E-SYNTAX.PROJECTION", "projection", "projection header must be ASCII")
    if len(header) != 3 or header[0] != PROJECTION_MAGIC:
        refuse("NOE-E-SYNTAX.PROJECTION", "projection", "projection header is malformed")
    if header[1] != manifest["profile_sha256"] or header[2] != manifest["graph_sha256"]:
        refuse("NOE-E-DIGEST.PROJECTION", "projection", "projection header and manifest differ")
    projected = _decode_json(lines[1] + b"\n", "projection.graph", canonical=True)
    inverse = {item[1]: item[0] for item in aliases}
    graph = _replace_strings(projected, inverse)
    graph_object = _exact_keys(graph, {"schema", "source_sha256", "records", "modules"}, "projection.graph")
    if graph_object["schema"] != GRAPH_SCHEMA:
        refuse("NOE-E-TYPE.GRAPH", "projection.graph", "projection recovered an unknown graph")
    if sha256(_canonical_json(graph_object)).hexdigest() != manifest["graph_sha256"]:
        refuse("NOE-E-DIGEST.RECOVERY", "projection", "recovered graph digest differs")
    return graph_object


def _walk_tag(value: object, tag: str) -> list[object]:
    found: list[object] = []
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, list) and current:
            if current[0] == tag:
                found.append(current)
            stack.extend(reversed(_term_children(current)))
    return found


def _semantic_facets(graph: dict[str, object]) -> dict[tuple[str, str], object]:
    facets: dict[tuple[str, str], object] = {}
    records = graph["records"]
    assert isinstance(records, list)
    for index, value in enumerate(records):
        assert isinstance(value, list)
        record = value
        form = record[0]
        if form == "precedence":
            node = f"precedence:{record[1]}>{record[2]}"
        else:
            node = f"{form}:{record[1]}"
        if form == "import":
            facets[(node, "module")] = record[2]
        elif form == "literal":
            facets[(node, "literal")] = record[2:]
        elif form == "definition":
            facets[(node, "definition")] = record[2:]
        elif form == "rule":
            facets[(node, "effect")] = record[2]
            facets[(node, "gate")] = _walk_tag(record[2], "?") + _walk_tag(record[2], "/")
            facets[(node, "authority")] = _walk_tag(record[2], "^")
            facets[(node, "scope")] = _walk_tag(record[2], "@")
            facets[(node, "source_binding")] = record[3]
        elif form == "precedence":
            facets[(node, "precedence")] = record[1:3]
            facets[(node, "authority")] = record[3]
            facets[(node, "scope")] = record[4]
            facets[(node, "evidence_class")] = record[5]
        elif form == "override":
            facets[(node, "precedence")] = record[3:5]
            facets[(node, "authority")] = record[2]
            facets[(node, "scope")] = record[5]
            facets[(node, "evidence_class")] = record[6]
        elif form == "transition":
            facets[(node, "transition")] = record[2:7]
            facets[(node, "gate")] = record[5]
            facets[(node, "effect")] = record[7]
        elif form == "promise":
            facets[(node, "promise")] = record[2:]
            facets[(node, "evidence_class")] = [record[4], record[5]]
            facets[(node, "scope")] = record[6]
            facets[(node, "effect")] = record[7:10]
        elif form == "handoff":
            facets[(node, "handoff")] = record[2:]
            facets[(node, "scope")] = record[5]
            facets[(node, "evidence_class")] = [record[6], record[7], record[10]]
        elif form == "exception":
            facets[(node, "exception")] = record[2:]
            facets[(node, "authority")] = record[2]
            facets[(node, "gate")] = record[3]
            facets[(node, "scope")] = record[5]
            facets[(node, "evidence_class")] = record[6]
            facets[(node, "effect")] = record[8]
        else:
            refuse("NOE-E-TYPE.RECORD", f"graph.records[{index}]", "unknown record in semantic diff")
    modules = graph["modules"]
    assert isinstance(modules, list)
    for module in modules:
        assert isinstance(module, dict)
        facets[(f"module:{module['id']}", "module")] = module
    return facets


def semantic_diff(before: dict[str, object], after: dict[str, object]) -> dict[str, object]:
    before_graph = before["graph"]
    after_graph = after["graph"]
    assert isinstance(before_graph, dict) and isinstance(after_graph, dict)
    left = _semantic_facets(before_graph)
    right = _semantic_facets(after_graph)
    entries: list[dict[str, object]] = []
    for node, kind in sorted(set(left) | set(right)):
        old = left.get((node, kind))
        new = right.get((node, kind))
        if old == new:
            continue
        entries.append(
            {
                "node": node,
                "kind": kind,
                "change": "added" if old is None else "removed" if new is None else "modified",
                "before": None if old is None else sha256(_canonical_json(old)).hexdigest(),
                "after": None if new is None else sha256(_canonical_json(new)).hexdigest(),
            }
        )
    result = {
        "schema": DIFF_SCHEMA,
        "before_graph_sha256": sha256(_canonical_json(before_graph)).hexdigest(),
        "after_graph_sha256": sha256(_canonical_json(after_graph)).hexdigest(),
        "entries": entries,
    }
    _canonical_json(result)
    return result


def _common_paths(command: argparse.ArgumentParser, *, build: str = "--build") -> None:
    command.add_argument(build, required=True, type=Path)
    command.add_argument("--modules", required=True, type=Path)
    command.add_argument("--profile", required=True, type=Path)
    command.add_argument("--kernel", required=True, type=Path)


def _parse_command(arguments: argparse.Namespace) -> dict[str, object]:
    source_raw = _read_regular(arguments.source, "source", MAX_INPUT_BYTES)
    build, artifacts = compile_source(source_raw, arguments.modules, arguments.profile, arguments.kernel)
    _atomic_write(arguments.output, artifacts["build"])
    lock = build["lock"]
    graph = build["graph"]
    assert isinstance(lock, dict) and isinstance(graph, dict)
    return _result(
        "parse",
        "ok",
        "NOE-OK",
        correlation_values=(lock["source_sha256"], lock["graph_sha256"]),
        message="canonical source compiled to one locked graph",
        digests={"source": lock["source_sha256"], "graph": lock["graph_sha256"], "build": sha256(artifacts["build"]).hexdigest()},
        counts={"records": len(graph["records"]), "modules": len(graph["modules"]), "bytes": len(artifacts["build"])},
    )


def _format_command(arguments: argparse.Namespace) -> dict[str, object]:
    build, _raw, artifacts = load_build(arguments.build, arguments.modules, arguments.profile, arguments.kernel)
    source_raw = artifacts["source"]
    _atomic_write(arguments.output, source_raw)
    lock = build["lock"]
    assert isinstance(lock, dict)
    return _result(
        "format", "ok", "NOE-OK", correlation_values=(lock["graph_sha256"],),
        message="locked graph formatted to canonical source",
        digests={"source": sha256(source_raw).hexdigest(), "graph": lock["graph_sha256"]},
        counts={"bytes": len(source_raw)},
    )


def _project_command(arguments: argparse.Namespace) -> dict[str, object]:
    build, _raw, artifacts = load_build(arguments.build, arguments.modules, arguments.profile, arguments.kernel)
    profile = _decode_json(artifacts["profile"], "profile", canonical=True)
    assert isinstance(profile, dict)
    profile_digest = sha256(artifacts["profile"]).hexdigest()
    bundle = project_build(build, profile, profile_digest)
    output = _canonical_json(bundle)
    _atomic_write(arguments.output, output)
    manifest = bundle["manifest"]
    assert isinstance(manifest, dict)
    return _result(
        "project", "ok", "NOE-OK", correlation_values=(manifest["graph_sha256"], manifest["projection_sha256"]),
        message="graph projected and recovered under one exact profile",
        digests={"graph": manifest["graph_sha256"], "projection": manifest["projection_sha256"], "profile": manifest["profile_sha256"]},
        counts={"bytes": len(bundle["text"].encode("utf-8")), "aliases": len(profile["aliases"])},
    )


def _diff_command(arguments: argparse.Namespace) -> dict[str, object]:
    before, _left_raw, _left_artifacts = load_build(arguments.before, arguments.modules, arguments.profile, arguments.kernel)
    after, _right_raw, _right_artifacts = load_build(arguments.after, arguments.modules, arguments.profile, arguments.kernel)
    result = semantic_diff(before, after)
    output = _canonical_json(result)
    _atomic_write(arguments.output, output)
    return _result(
        "semantic-diff", "ok", "NOE-OK",
        correlation_values=(result["before_graph_sha256"], result["after_graph_sha256"]),
        message="semantic graph changes classified",
        digests={"before": result["before_graph_sha256"], "after": result["after_graph_sha256"], "diff": sha256(output).hexdigest()},
        counts={"entries": len(result["entries"]), "bytes": len(output)},
    )


def _verify_command(arguments: argparse.Namespace) -> dict[str, object]:
    build, raw, _artifacts = load_build(arguments.build, arguments.modules, arguments.profile, arguments.kernel)
    lock = build["lock"]
    graph = build["graph"]
    assert isinstance(lock, dict) and isinstance(graph, dict)
    return _result(
        "verify", "ok", "NOE-OK", correlation_values=(lock["graph_sha256"],),
        message="build graph, lock and dependency bytes match",
        digests={"build": sha256(raw).hexdigest(), "graph": lock["graph_sha256"]},
        counts={"records": len(graph["records"]), "modules": len(graph["modules"])},
    )


def self_test() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    fixture = root / "tests" / "fixtures" / "noema-v1"
    source_path = fixture / "codec" / "complete.noe"
    modules = fixture / "modules"
    profile_path = fixture / "profiles" / "ascii-baseline.json"
    kernel_path = fixture / "profiles" / "kernel.noe"
    source_raw = _read_regular(source_path, "source", MAX_INPUT_BYTES)
    build, artifacts = compile_source(source_raw, modules, profile_path, kernel_path)
    if artifacts["source"] != source_raw:
        refuse("NOE-E-DIGEST.RECOVERY", "self-test", "source did not round trip")
    profile = _decode_json(artifacts["profile"], "profile", canonical=True)
    assert isinstance(profile, dict)
    projection = project_build(build, profile, sha256(artifacts["profile"]).hexdigest())
    recovered = recover_projection(projection, profile)
    if recovered != build["graph"] or semantic_diff(build, build)["entries"]:
        refuse("NOE-E-DIGEST.RECOVERY", "self-test", "graph projection or semantic identity failed")
    lock = build["lock"]
    graph = build["graph"]
    assert isinstance(lock, dict) and isinstance(graph, dict)
    return _result(
        "self-test", "ok", "NOE-OK", correlation_values=(lock["graph_sha256"],),
        message="canonical graph, module lock, projection recovery and no-op diff passed",
        digests={"source": lock["source_sha256"], "graph": lock["graph_sha256"], "projection": projection["manifest"]["projection_sha256"]},
        counts={"records": len(graph["records"]), "modules": len(graph["modules"]), "aliases": len(profile["aliases"])},
    )


def about() -> dict[str, object]:
    return _result(
        "about",
        "ok",
        "NOE-I-ABOUT",
        correlation_values=(CONTRACT, SOURCE_MAGIC, PROJECTION_MAGIC),
        message=f"{CONTRACT} shadow prototype; source={SOURCE_MAGIC}; projection={PROJECTION_MAGIC}",
    )


def unimplemented(command: str) -> dict[str, object]:
    refuse(
        "NOE-E-UNIMPLEMENTED",
        "command",
        f"{command} is reserved for a later receipted prototype step",
    )


def parser() -> argparse.ArgumentParser:
    root = _BoundedArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    subparsers.add_parser("about", help="print the bounded contract identity")
    seed = subparsers.add_parser("verify-seed", help="verify an archive against its exact inventory")
    seed.add_argument("--archive", required=True, type=Path)
    seed.add_argument("--inventory", required=True, type=Path)
    compile_parser = subparsers.add_parser("parse", help="compile canonical source to one locked graph")
    compile_parser.add_argument("--source", required=True, type=Path)
    compile_parser.add_argument("--modules", required=True, type=Path)
    compile_parser.add_argument("--profile", required=True, type=Path)
    compile_parser.add_argument("--kernel", required=True, type=Path)
    compile_parser.add_argument("--output", required=True, type=Path)
    format_parser = subparsers.add_parser("format", help="recover canonical source from one locked graph")
    _common_paths(format_parser)
    format_parser.add_argument("--output", required=True, type=Path)
    project_parser = subparsers.add_parser("project", help="emit one reversible tokenizer-profile projection")
    _common_paths(project_parser)
    project_parser.add_argument("--output", required=True, type=Path)
    diff_parser = subparsers.add_parser("semantic-diff", help="classify changes between two locked graphs")
    diff_parser.add_argument("--before", required=True, type=Path)
    diff_parser.add_argument("--after", required=True, type=Path)
    diff_parser.add_argument("--modules", required=True, type=Path)
    diff_parser.add_argument("--profile", required=True, type=Path)
    diff_parser.add_argument("--kernel", required=True, type=Path)
    diff_parser.add_argument("--output", required=True, type=Path)
    verify_parser = subparsers.add_parser("verify", help="verify graph, lock and dependency identities")
    _common_paths(verify_parser)
    subparsers.add_parser("self-test", help="run the bounded codec/module/profile round trip")
    for command in UNIMPLEMENTED:
        subparsers.add_parser(command, help="reserved by the receipted runbook")
    return root


def main(argv: list[str] | None = None) -> int:
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    command = (
        raw_arguments[0]
        if raw_arguments and raw_arguments[0] in KNOWN_COMMANDS
        else "invalid"
    )
    try:
        arguments = parser().parse_args(raw_arguments)
        command = arguments.command
        if command == "about":
            payload = about()
        elif command == "verify-seed":
            payload = verify_seed(arguments.archive, arguments.inventory)
        elif command == "parse":
            payload = _parse_command(arguments)
        elif command == "format":
            payload = _format_command(arguments)
        elif command == "project":
            payload = _project_command(arguments)
        elif command == "semantic-diff":
            payload = _diff_command(arguments)
        elif command == "verify":
            payload = _verify_command(arguments)
        elif command == "self-test":
            payload = self_test()
        else:
            payload = unimplemented(command)
    except Refusal as error:
        payload = _result(
            command,
            "refuse",
            error.code,
            correlation_values=(error.code, error.field),
            field=error.field,
            message=error.message,
        )
        emit(payload)
        return 2
    emit(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
