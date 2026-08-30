#!/usr/bin/env python3
"""Bounded entrypoint for the Noema version 1 shadow prototype."""

from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import unicodedata
import zipfile


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

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNIMPLEMENTED = (
    "parse",
    "format",
    "project",
    "semantic-diff",
    "select",
    "check",
    "next",
    "literal",
    "explain",
    "verify",
    "mutations",
    "measure",
    "emit-evaluation",
    "tally-evaluation",
    "self-test",
    "runtime-self-test",
)
ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}


class Refusal(ValueError):
    """One stable, bounded refusal without untrusted payload bytes."""

    def __init__(self, code: str, field: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.field = field
        self.message = message


def refuse(code: str, field: str, message: str) -> None:
    raise Refusal(code, field, message)


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
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            refuse("NOE-E-PATH.REGULAR", field, "opened input is not a regular file")
        if (before.st_dev, before.st_ino) != (before_path.st_dev, before_path.st_ino):
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
    finally:
        os.close(descriptor)

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
    return b"".join(chunks)


def _exact_keys(value: object, expected: set[str], field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        refuse("NOE-E-TYPE.OBJECT", field, "expected an object")
    actual = set(value)
    if actual != expected:
        refuse("NOE-E-TYPE.KEYS", field, "object keys do not match the closed shape")
    return value


def _bounded_string(value: object, field: str, limit: int) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > limit:
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
    except (OSError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile):
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
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    subparsers.add_parser("about", help="print the bounded contract identity")
    seed = subparsers.add_parser("verify-seed", help="verify an archive against its exact inventory")
    seed.add_argument("--archive", required=True, type=Path)
    seed.add_argument("--inventory", required=True, type=Path)
    for command in UNIMPLEMENTED:
        subparsers.add_parser(command, help="reserved by the receipted runbook")
    return root


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    command = arguments.command
    try:
        if command == "about":
            payload = about()
        elif command == "verify-seed":
            payload = verify_seed(arguments.archive, arguments.inventory)
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
