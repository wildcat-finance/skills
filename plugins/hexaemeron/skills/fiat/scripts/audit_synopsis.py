#!/usr/bin/env python3
"""Render and check bounded, deterministic views of Fiat audit logs."""

import argparse
import contextlib
import datetime
import hashlib
import io
import os
import posixpath
import re
import secrets
import stat
import sys


SYNOPSIS_SCHEMA = "fiat-audit-synopsis/v1"
AUDIT_SCHEMA = "fiat-audit-round/v1"
AUDIT_SCHEMAS = (AUDIT_SCHEMA, "fiat-audit-round/v2")
SOURCE_NAME = "AUDIT.md"
SYNOPSIS_NAME = "AUDIT_SYNOPSIS.md"
ROUND_SOURCE_DIRECTORY = "audit/rounds"
PRODUCT_SOURCE = (
    "audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md"
)
SYNOPSIS_SEPARATOR = "<br>"
SYNOPSIS_ESCAPE = "%"
SYNOPSIS_ESCAPED_SEPARATOR = "%b"
SYNOPSIS_ESCAPED_ESCAPE = "%%"
SYNOPSIS_SEPARATOR_BYTES = len(SYNOPSIS_SEPARATOR.encode("utf-8"))
SOURCE_BYTES_MAX = 16 * 1024 * 1024
SYNOPSIS_BYTES_MAX = 16 * 1024 * 1024
ROLLBACK_BYTES_MAX = 2 * SYNOPSIS_BYTES_MAX
H2_RECORDS_MAX = 10_000
PHYSICAL_LINE_BYTES_MAX = 1024 * 1024
FINDINGS_HEADER = "| id | severity | file | finding | status |"
FINDINGS_SEPARATOR = "| --- | --- | --- | --- | --- |"
ZERO_FINDING_ROW = "| -- | -- | -- | none | -- |"
ELENCHUS_VERDICTS = ("guarded", "unguarded", "passed", "inconclusive", "null")
COVERAGE_VALUES = ("reviewed", "not-applicable")
LEGACY_SCHEMA_DRAFT_H3 = ("### Coverage", "### Findings", "### Leads")
PINNED_LEGACY_SCHEMA_DRAFTS = {
    1: "761253edc37e6262d87f032e870c9aa084f8e5361dcfe08f46ea2c4a3858e6a1",
    2: "b519682b4ab8687dfab790f44db6fedc1ed1dc8ca40b40b6b53c4d2bf9311666",
    3: "c52a85e933edf9b4489a5bea522986be165c78df3e72029769283ff8064c1ce9",
    4: "e854ba720e8df264aa23f9c1bfe0351eb3b68cdccc8f9d7b9f1939331c9444be",
    5: "c1226d85df510c3c9d7fee9788ebcf99b621ee73627e2962c974be89a47673c5",
    6: "8e3d0d4670f693361872715c2d8002b72295c625c2e1a475b7c9de25d9ce8f2c",
    7: "f80d1e83bfcfa4d0ba893a3fa08383310cc82a90b92ca8a224bf73404513aade",
    8: "6a7d2652b1b1d72586eb2da78fc5dd1a9ca60d49c123a587b255e9696743a237",
    9: "5679164692620843043cacd7d86266113a0aa94b260f8ff39ef7eeb910846788",
    10: "339531852f52439befb1410a0b72230f623cbd9cd08be6f777fb20f4b3ef19e1",
}
V1_HEADING_RE = re.compile(
    r"## .+, step [1-9][0-9]*, round [1-9][0-9]* -- "
    r"(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z)",
    re.ASCII,
)
V2_HEADING_RE = re.compile(
    r"## Step [1-9][0-9]*, round [1-9][0-9]* -- "
    r"(?P<timestamp>[0-9]{4}-[0-9]{2}-[0-9]{2}T"
    r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z)",
    re.ASCII,
)
STRICT_HEADING_RES = {
    "fiat-audit-round/v1": V1_HEADING_RE,
    "fiat-audit-round/v2": V2_HEADING_RE,
}
OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
UNLINK_SUPPORTS_DIR_FD = os.unlink in os.supports_dir_fd


class SynopsisError(Exception):
    """A bounded refusal safe to show without source content."""


def encode_synopsis_physical_line(line):
    """Encode one retained physical line for a one-line synopsis record."""
    if not isinstance(line, str):
        raise SynopsisError("synopsis physical line must be text")
    return line.replace(
        SYNOPSIS_ESCAPE, SYNOPSIS_ESCAPED_ESCAPE
    ).replace(SYNOPSIS_SEPARATOR, SYNOPSIS_ESCAPED_SEPARATOR)


def decode_synopsis_record(record):
    """Decode one canonical synopsis record into its exact physical lines."""
    if not isinstance(record, str) or "\n" in record or "\r" in record:
        raise SynopsisError("synopsis record must be one physical text line")
    physical = []
    decoded = []
    index = 0
    while index < len(record):
        if record.startswith(SYNOPSIS_SEPARATOR, index):
            physical.append("".join(decoded))
            decoded = []
            index += len(SYNOPSIS_SEPARATOR)
            continue
        character = record[index]
        if character != SYNOPSIS_ESCAPE:
            decoded.append(character)
            index += 1
            continue
        if record.startswith(SYNOPSIS_ESCAPED_ESCAPE, index):
            decoded.append(SYNOPSIS_ESCAPE)
            index += len(SYNOPSIS_ESCAPED_ESCAPE)
            continue
        if record.startswith(SYNOPSIS_ESCAPED_SEPARATOR, index):
            decoded.append(SYNOPSIS_SEPARATOR)
            index += len(SYNOPSIS_ESCAPED_SEPARATOR)
            continue
        raise SynopsisError("synopsis record has malformed escape framing")
    physical.append("".join(decoded))
    return physical


def _root_path(supplied):
    try:
        lexical = os.path.abspath(os.fspath(supplied))
        os.fsencode(lexical)
        info = os.lstat(lexical)
    except (OSError, TypeError, ValueError, UnicodeError):
        raise SynopsisError("repository root is not a readable directory") from None
    if stat.S_ISLNK(info.st_mode):
        raise SynopsisError("repository root is a symlink")
    if not stat.S_ISDIR(info.st_mode):
        raise SynopsisError("repository root is not a directory")
    real = os.path.realpath(lexical)
    try:
        current = os.lstat(lexical)
        resolved = os.lstat(real)
    except OSError:
        raise SynopsisError("repository root changed during access") from None
    identities = {
        (entry.st_dev, entry.st_ino)
        for entry in (info, current, resolved)
        if stat.S_ISDIR(entry.st_mode)
    }
    if (
        stat.S_ISLNK(current.st_mode)
        or stat.S_ISLNK(resolved.st_mode)
        or len(identities) != 1
        or not stat.S_ISDIR(current.st_mode)
        or not stat.S_ISDIR(resolved.st_mode)
    ):
        raise SynopsisError("repository root changed during access")
    return real


def _relative_path(relative):
    if not isinstance(relative, str) or not relative:
        raise SynopsisError("path must be a non-empty repository-relative string")
    try:
        relative.encode("utf-8")
    except UnicodeError:
        raise SynopsisError(
            f"path has unsafe synopsis framing: {relative!r}"
        ) from None
    if (
        any(not character.isprintable() for character in relative)
        or any(character in "|<>" for character in relative)
    ):
        raise SynopsisError(f"path has unsafe synopsis framing: {relative!r}")
    if os.path.isabs(relative) or "\\" in relative:
        raise SynopsisError(f"path escapes repository: {relative!r}")
    normal = posixpath.normpath(relative)
    if normal in ("", ".", "..") or normal.startswith("../"):
        raise SynopsisError(f"path escapes repository: {relative!r}")
    if normal != relative:
        raise SynopsisError(f"path is not canonical: {relative!r}")
    return normal


def _directory_descriptor(root, components, label):
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory_only = getattr(os, "O_DIRECTORY", 0)
    if not no_follow or not directory_only or not OPEN_SUPPORTS_DIR_FD:
        raise SynopsisError(f"platform cannot safely access {label}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | no_follow | directory_only
    descriptor = None
    try:
        descriptor = os.open(root, flags)
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise SynopsisError("repository root changed kind during access")
        for component in components:
            child = None
            try:
                child = os.open(component, flags, dir_fd=descriptor)
                if not stat.S_ISDIR(os.fstat(child).st_mode):
                    raise SynopsisError(f"{label} has a non-directory component")
                os.close(descriptor)
                descriptor = child
                child = None
            finally:
                if child is not None:
                    with contextlib.suppress(OSError):
                        os.close(child)
        return descriptor
    except OSError:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        raise SynopsisError(f"{label} cannot be accessed") from None
    except Exception:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        raise


def _inode_identity(info):
    return info.st_dev, info.st_ino


def _file_identity(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _directory_still_at_path(root, components, descriptor):
    current = None
    try:
        current = _directory_descriptor(root, components, "directory")
        return _inode_identity(os.fstat(current)) == _inode_identity(
            os.fstat(descriptor)
        )
    except (OSError, SynopsisError):
        return False
    finally:
        if current is not None:
            with contextlib.suppress(OSError):
                os.close(current)


def _file_still_at_path(root, components, parent, expected):
    current_parent = None
    current_file = None
    try:
        current_parent = _directory_descriptor(root, components[:-1], "file")
        if _inode_identity(os.fstat(current_parent)) != _inode_identity(
            os.fstat(parent)
        ):
            return False
        current_file = os.open(
            components[-1],
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0),
            dir_fd=current_parent,
        )
        current = os.fstat(current_file)
        return stat.S_ISREG(current.st_mode) and _file_identity(
            current
        ) == _file_identity(expected)
    except (OSError, SynopsisError):
        return False
    finally:
        if current_file is not None:
            with contextlib.suppress(OSError):
                os.close(current_file)
        if current_parent is not None:
            with contextlib.suppress(OSError):
                os.close(current_parent)


def read_regular_bytes(
    root, relative, label, *, missing_ok=False, bytes_max=SOURCE_BYTES_MAX
):
    """Read one contained regular file once through a no-follow descriptor walk."""
    root = _root_path(root)
    relative = _relative_path(relative)
    components = relative.split("/")
    lexical = os.path.join(root, *components)
    try:
        info = os.lstat(lexical)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise SynopsisError(f"{label} is missing: {relative}") from None
    except OSError:
        raise SynopsisError(f"{label} cannot be inspected: {relative}") from None
    if stat.S_ISLNK(info.st_mode):
        raise SynopsisError(f"{label} is a symlink: {relative}")
    if not stat.S_ISREG(info.st_mode):
        raise SynopsisError(f"{label} is not a regular file: {relative}")
    if os.path.realpath(lexical) != lexical:
        raise SynopsisError(f"{label} traverses a symlink: {relative}")

    no_follow = getattr(os, "O_NOFOLLOW", 0)
    non_blocking = getattr(os, "O_NONBLOCK", 0)
    if not no_follow or not non_blocking:
        raise SynopsisError(f"platform cannot safely read {label}")
    parent = _directory_descriptor(root, components[:-1], label)
    descriptor = None
    try:
        descriptor = os.open(
            components[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | no_follow | non_blocking,
            dir_fd=parent,
        )
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise SynopsisError(f"{label} is not a regular file: {relative}")
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise SynopsisError(f"{label} changed during access: {relative}")
        chunks = []
        remaining = bytes_max + 1
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        finished = os.fstat(descriptor)
        if (
            _file_identity(opened) != _file_identity(finished)
            or (len(data) <= bytes_max and len(data) != finished.st_size)
            or not _file_still_at_path(root, components, parent, finished)
        ):
            raise SynopsisError(f"{label} changed during read: {relative}")
    except OSError:
        raise SynopsisError(f"{label} cannot be read: {relative}") from None
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        with contextlib.suppress(OSError):
            os.close(parent)
    if len(data) > bytes_max:
        raise SynopsisError(
            f"{label} exceeds {bytes_max:,}-byte cap: {relative}"
        )
    return data


def _physical_text(source_path, data):
    if len(data) > SOURCE_BYTES_MAX:
        raise SynopsisError(
            f"{source_path}: source exceeds {SOURCE_BYTES_MAX:,}-byte cap"
        )
    if b"\r" in data:
        raise SynopsisError(f"{source_path}: source must use LF line endings")

    line_count = 0
    cursor = 0
    while cursor < len(data):
        end = data.find(b"\n", cursor)
        if end < 0:
            end = len(data)
            following = len(data)
        else:
            following = end + 1
        line_count += 1
        if end - cursor > PHYSICAL_LINE_BYTES_MAX:
            raise SynopsisError(
                f"{source_path}: physical line {line_count} exceeds "
                f"{PHYSICAL_LINE_BYTES_MAX:,}-byte cap"
            )
        cursor = following

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise SynopsisError(f"{source_path}: source is not UTF-8") from None
    return text, line_count


def _iter_line_spans(text, start=0, stop=None):
    """Yield physical lines lazily as character offsets and text."""
    if stop is None:
        stop = len(text)
    cursor = start
    while cursor < stop:
        end = text.find("\n", cursor, stop)
        if end < 0:
            yield cursor, stop, text[cursor:stop]
            return
        yield cursor, end, text[cursor:end]
        cursor = end + 1


def _iter_lines(text, start, stop):
    for _start, _end, line in _iter_line_spans(text, start, stop):
        yield line


def _is_h2(line):
    return line == "##" or line.startswith("## ")


def _table_cells(line):
    trailing_slashes = len(line) - 1 - len(line[:-1].rstrip("\\"))
    if (
        len(line) < 2
        or not line.startswith("|")
        or not line.endswith("|")
        or trailing_slashes % 2
    ):
        return []
    cells = []
    start = 1
    slashes = 0
    for index, character in enumerate(line[1:-1], 1):
        if character == "|" and slashes % 2 == 0:
            cells.append(line[start:index].strip())
            start = index + 1
        slashes = slashes + 1 if character == "\\" else 0
    cells.append(line[start:-1].strip())
    return cells


def _field(line, label, record_number, source_path):
    prefix = f"{label}: "
    if not line.startswith(prefix):
        raise SynopsisError(
            f"{source_path}: strict record {record_number} is missing {label}"
        )
    value = line[len(prefix):]
    if not value or value != value.strip():
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed {label}"
        )
    return value


def _pinned_legacy_schema_draft(record, record_number, source_path, h3_headings):
    """Recognise only the ten immutable pre-cutover root records."""
    if source_path != PRODUCT_SOURCE or h3_headings != LEGACY_SCHEMA_DRAFT_H3:
        return False
    expected = PINNED_LEGACY_SCHEMA_DRAFTS.get(record_number)
    if expected is None:
        return False
    raw_record = ("\n".join(record) + "\n").encode("utf-8")
    return hashlib.sha256(raw_record).hexdigest() == expected


def _strict_candidate(text, start, stop, record_number, source_path):
    lines = _iter_lines(text, start, stop)
    try:
        heading = next(lines)
    except StopIteration:
        return False

    pinned = (
        source_path == PRODUCT_SOURCE
        and record_number in PINNED_LEGACY_SCHEMA_DRAFTS
    )
    digest = hashlib.sha256() if pinned else None
    if digest is not None:
        digest.update(heading.encode("utf-8"))
        digest.update(b"\n")
    has_schema = False
    h3_headings = []
    h3_count = 0
    for line in lines:
        if digest is not None:
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
        if line.startswith("Audit schema: "):
            has_schema = True
        if line.startswith("###"):
            h3_count += 1
            if len(h3_headings) < len(LEGACY_SCHEMA_DRAFT_H3) + 1:
                h3_headings.append(line)

    if pinned:
        exact_draft = (
            h3_count == len(LEGACY_SCHEMA_DRAFT_H3)
            and tuple(h3_headings) == LEGACY_SCHEMA_DRAFT_H3
            and digest.hexdigest() == PINNED_LEGACY_SCHEMA_DRAFTS[record_number]
        )
        return not exact_draft
    if h3_count:
        return has_schema
    return has_schema or any(
        pattern.fullmatch(heading) is not None
        for pattern in STRICT_HEADING_RES.values()
    )


def _strict_record(
    text, start, stop, record_number, source_path, *, at_eof, source_ends_lf
):
    if at_eof and not source_ends_lf:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has no terminal LF"
        )

    lines = _iter_lines(text, start, stop)
    retained = []

    def take():
        try:
            return next(lines)
        except StopIteration:
            raise SynopsisError(
                f"{source_path}: strict record {record_number} is truncated"
            ) from None

    def exact(expected, label):
        line = take()
        if line != expected:
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed {label}"
            )
        retained.append(line)

    def field(label):
        line = take()
        value = _field(line, label, record_number, source_path)
        retained.append(line)
        return value

    heading = take()
    retained.append(heading)
    exact("", "heading separator")
    schema = field("Audit schema")
    if schema not in AUDIT_SCHEMAS:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has unsupported schema"
        )
    match = STRICT_HEADING_RES[schema].fullmatch(heading)
    if match is None:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed heading"
        )
    timestamp = match.group("timestamp")
    try:
        parsed = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has invalid UTC timestamp"
        ) from None
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != timestamp:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has non-canonical timestamp"
        )
    exact("", "Audit schema separator")
    covered = field("Covered")
    dispositions = {}
    for raw in covered.split(";"):
        item = raw.strip()
        if item.count("=") != 1:
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed Covered"
            )
        risk_id, value = (part.strip() for part in item.split("=", 1))
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9-]*", risk_id)
            or risk_id in dispositions
            or value not in COVERAGE_VALUES
        ):
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed Covered"
            )
        dispositions[risk_id] = value
    if not dispositions:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed Covered"
        )
    exact("", "Covered separator")
    field("Not checked")
    exact("", "Not checked separator")
    verdict = field("Elenchus verdict")
    if verdict not in ELENCHUS_VERDICTS:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has invalid Elenchus verdict"
        )
    exact("", "Elenchus verdict separator")
    exact(FINDINGS_HEADER, "findings header")
    exact(FINDINGS_SEPARATOR, "findings separator")

    row_count = 0
    zero_row = False
    while True:
        line = take()
        if line == "":
            retained.append(line)
            break
        cells = _table_cells(line)
        if len(cells) != 5 or any(not cell for cell in cells):
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has malformed findings row"
            )
        retained.append(line)
        row_count += 1
        zero_row = zero_row or line == ZERO_FINDING_ROW
    if not row_count or (zero_row and row_count != 1):
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed findings table"
        )
    field("Leads not pursued")

    sentinel = object()
    trailing = next(lines, sentinel)
    if at_eof:
        if trailing is not sentinel:
            if trailing == "" and next(lines, sentinel) is sentinel:
                raise SynopsisError(
                    f"{source_path}: strict record {record_number} has a trailing blank line"
                )
            raise SynopsisError(
                f"{source_path}: strict record {record_number} has trailing content"
            )
    elif trailing != "" or next(lines, sentinel) is not sentinel:
        raise SynopsisError(
            f"{source_path}: strict record {record_number} has malformed record separator"
        )
    return retained


class _RecordBuffer:
    """Accumulate retained text without one live object per source line."""

    def __init__(self, source_path):
        self.source_path = source_path
        self.buffer = io.StringIO()
        self.lines = 0
        self.bytes = 0

    def _reserve(self, addition):
        if self.bytes + addition > SYNOPSIS_BYTES_MAX:
            raise SynopsisError(
                f"{self.source_path}: synopsis exceeds "
                f"{SYNOPSIS_BYTES_MAX:,}-byte cap"
            )
        self.bytes += addition

    def append(self, line):
        line = encode_synopsis_physical_line(line)
        encoded_size = len(line.encode("utf-8"))
        self._reserve(
            encoded_size + (SYNOPSIS_SEPARATOR_BYTES if self.lines else 0)
        )
        if self.lines:
            self.buffer.write(SYNOPSIS_SEPARATOR)
        self.buffer.write(line)
        self.lines += 1

    def append_empty_run(self, count):
        if not count:
            return
        separators = count if self.lines else count - 1
        self._reserve(separators * SYNOPSIS_SEPARATOR_BYTES)
        if separators:
            self.buffer.write(SYNOPSIS_SEPARATOR * separators)
        self.lines += count

    def value(self):
        return self.buffer.getvalue()


def _legacy_record(text, start, stop, source_path):
    lines = _iter_lines(text, start, stop)
    try:
        heading = next(lines)
    except StopIteration:
        raise SynopsisError(f"{source_path}: source has an empty H2 record") from None

    fields = (
        ("audit-schema", "Audit schema: "),
        ("covered", "Covered: "),
        ("not-checked", "Not checked: "),
        ("elenchus-verdict", "Elenchus verdict: "),
    )
    found = set()
    selected = _RecordBuffer(source_path)
    leads_seen = "Leads not pursued" in heading
    trailing_blanks = 0
    table_mode = False
    pending_header = None

    for line in lines:
        matching_field = False
        for slug, prefix in fields:
            if line.startswith(prefix):
                found.add(slug)
                matching_field = True

        if leads_seen:
            if line == "":
                trailing_blanks += 1
            else:
                selected.append_empty_run(trailing_blanks)
                trailing_blanks = 0
                selected.append(line)
            continue

        if "Leads not pursued" in line:
            leads_seen = True
            pending_header = None
            selected.append(line)
            continue

        if table_mode:
            if line.startswith("|"):
                selected.append(line)
                continue
            table_mode = False

        if pending_header is not None:
            header, columns, canonical = pending_header
            if canonical:
                separator = line == FINDINGS_SEPARATOR
            else:
                cells = _table_cells(line)
                separator = len(cells) == columns and all(
                    re.fullmatch(r":?-{3,}:?", cell) for cell in cells
                )
            pending_header = None
            if separator:
                selected.append(header)
                selected.append(line)
                table_mode = True
                continue

        if matching_field:
            selected.append(line)
            continue
        if line == FINDINGS_HEADER:
            pending_header = (line, 5, True)
            continue
        cells = _table_cells(line)
        if cells and cells[0].strip("` ").lower() == "risk id":
            pending_header = (line, len(cells), False)

    missing = [
        f"[missing legacy field: {slug}]"
        for slug, _prefix in fields
        if slug not in found
    ]
    if not leads_seen:
        missing.append("[missing legacy field: leads-not-pursued]")

    prefix = SYNOPSIS_SEPARATOR.join(
        encode_synopsis_physical_line(line) for line in [heading, *missing]
    )
    tail = selected.value()
    retained = prefix + (SYNOPSIS_SEPARATOR + tail if tail else "")
    if len(retained.encode("utf-8")) > SYNOPSIS_BYTES_MAX:
        raise SynopsisError(
            f"{source_path}: synopsis exceeds {SYNOPSIS_BYTES_MAX:,}-byte cap"
        )
    return retained


def render_source(source_path, data):
    """Render one source from captured bytes without touching the filesystem."""
    source_path = _relative_path(source_path)
    text, source_lines = _physical_text(source_path, data)

    starts = []
    previous_empty = False
    before_previous_empty = False
    for line_number, (start, _end, line) in enumerate(_iter_line_spans(text)):
        if _is_h2(line):
            starts.append(
                (start, line_number, previous_empty, before_previous_empty)
            )
            if len(starts) > H2_RECORDS_MAX:
                raise SynopsisError(
                    f"{source_path}: source exceeds "
                    f"{H2_RECORDS_MAX:,} H2 record cap"
                )
        before_previous_empty = previous_empty
        previous_empty = line == ""
    if not starts:
        raise SynopsisError(f"{source_path}: source has no raw H2 records")
    if text.find("Leads not pursued", 0, starts[0][0]) >= 0:
        raise SynopsisError(
            f"{source_path}: Leads not pursued occurs outside a raw H2 record"
        )

    source_digest = hashlib.sha256(data).hexdigest()
    metadata = (
        f"Synopsis schema={SYNOPSIS_SCHEMA} | source={source_path} | "
        f"source_sha256={source_digest} | h2_count={len(starts)}"
    )
    rendered = bytearray()

    def append_output(line):
        encoded = line.encode("utf-8")
        if len(rendered) + len(encoded) + 1 > SYNOPSIS_BYTES_MAX:
            raise SynopsisError(
                f"{source_path}: synopsis exceeds "
                f"{SYNOPSIS_BYTES_MAX:,}-byte cap"
            )
        rendered.extend(encoded)
        rendered.append(10)

    append_output(metadata)
    for index, (start, line_number, leading_blank, extra_blank) in enumerate(starts):
        number = index + 1
        stop = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        strict = _strict_candidate(text, start, stop, number, source_path)
        if strict and line_number and (not leading_blank or extra_blank):
            raise SynopsisError(
                f"{source_path}: strict record {number} has malformed "
                "record separator"
            )
        if strict:
            retained = SYNOPSIS_SEPARATOR.join(
                encode_synopsis_physical_line(line)
                for line in _strict_record(
                    text,
                    start,
                    stop,
                    number,
                    source_path,
                    at_eof=index + 1 == len(starts),
                    source_ends_lf=data.endswith(b"\n"),
                )
            )
        else:
            retained = _legacy_record(text, start, stop, source_path)
        append_output(retained)

    synopsis_lines = len(starts) + 1
    if synopsis_lines * 100 >= source_lines * 15:
        raise SynopsisError(
            f"{source_path}: 15% line budget failed "
            f"(source_lines={source_lines}, synopsis_lines={synopsis_lines})"
        )
    rendered = bytes(rendered)
    return {
        "source": source_path,
        "bytes": rendered,
        "source_lines": source_lines,
        "synopsis_lines": synopsis_lines,
        "h2_count": len(starts),
        "source_sha256": source_digest,
        "synopsis_sha256": hashlib.sha256(rendered).hexdigest(),
        "budget": "pass",
    }


def discover_sources(root):
    """Discover legacy and direct per-run sources without following links."""
    root = _root_path(root)
    discovered = []

    def refuse_walk_error(_error):
        raise SynopsisError("repository discovery cannot read a directory") from None

    for directory, names, files in os.walk(
        root,
        topdown=True,
        followlinks=False,
        onerror=refuse_walk_error,
    ):
        if directory != root and (".git" in names or ".git" in files):
            names[:] = []
            continue
        kept = []
        for name in sorted(names):
            if directory == root and name == "tmp":
                continue
            candidate = os.path.join(directory, name)
            try:
                info = os.lstat(candidate)
            except OSError:
                raise SynopsisError("repository discovery cannot inspect a directory") from None
            if os.path.basename(directory) == "audit" and name == SOURCE_NAME:
                relative = _relative_path(
                    os.path.relpath(candidate, root).replace(os.sep, "/")
                )
                if stat.S_ISLNK(info.st_mode):
                    raise SynopsisError(f"audit source is a symlink: {relative}")
                if not stat.S_ISREG(info.st_mode):
                    raise SynopsisError(
                        f"audit source is not a regular file: {relative}"
                    )
                raise SynopsisError(
                    f"audit source changed kind during discovery: {relative}"
                )
            candidate_relative = os.path.relpath(candidate, root).replace(os.sep, "/")
            if stat.S_ISLNK(info.st_mode):
                if candidate_relative == ROUND_SOURCE_DIRECTORY:
                    raise SynopsisError(
                        f"audit directory is a symlink: {candidate_relative}"
                    )
                if name == "audit":
                    relative = os.path.relpath(candidate, root).replace(os.sep, "/")
                    relative = _relative_path(relative)
                    raise SynopsisError(f"audit directory is a symlink: {relative}")
                continue
            if name in (".git", ".hexaemeron"):
                continue
            kept.append(name)
        names[:] = kept
        if os.path.basename(directory) == "audit" and SOURCE_NAME in files:
            candidate = os.path.join(directory, SOURCE_NAME)
            relative = _relative_path(
                os.path.relpath(candidate, root).replace(os.sep, "/")
            )
            try:
                info = os.lstat(candidate)
            except OSError:
                raise SynopsisError(
                    f"audit source cannot be inspected: {relative}"
                ) from None
            if stat.S_ISLNK(info.st_mode):
                raise SynopsisError(f"audit source is a symlink: {relative}")
            if not stat.S_ISREG(info.st_mode):
                raise SynopsisError(f"audit source is not a regular file: {relative}")
            discovered.append(_relative_path(relative))

        relative_directory = os.path.relpath(directory, root).replace(os.sep, "/")
        if relative_directory == ROUND_SOURCE_DIRECTORY:
            for name in sorted(files):
                if not name.endswith(".md") or name.endswith(".synopsis.md"):
                    continue
                candidate = os.path.join(directory, name)
                relative = _relative_path(
                    os.path.relpath(candidate, root).replace(os.sep, "/")
                )
                try:
                    info = os.lstat(candidate)
                except OSError:
                    raise SynopsisError(
                        f"audit source cannot be inspected: {relative}"
                    ) from None
                if stat.S_ISLNK(info.st_mode):
                    raise SynopsisError(f"audit source is a symlink: {relative}")
                if not stat.S_ISREG(info.st_mode):
                    raise SynopsisError(
                        f"audit source is not a regular file: {relative}"
                    )
                discovered.append(relative)
    discovered.sort()
    if not discovered:
        raise SynopsisError("repository contains no supported audit source")
    return discovered


def _output_path(source):
    source = _relative_path(source)
    directory = posixpath.dirname(source)
    name = posixpath.basename(source)
    if name == SOURCE_NAME and posixpath.basename(directory) == "audit":
        return posixpath.join(directory, SYNOPSIS_NAME)
    if (
        directory == ROUND_SOURCE_DIRECTORY
        and name.endswith(".md")
        and not name.endswith(".synopsis.md")
    ):
        return posixpath.join(directory, name[:-3] + ".synopsis.md")
    raise SynopsisError(f"unsupported audit source path: {source}")


def _is_output_path(relative):
    directory = posixpath.dirname(relative)
    name = posixpath.basename(relative)
    return (
        name == SYNOPSIS_NAME and posixpath.basename(directory) == "audit"
    ) or (
        directory == ROUND_SOURCE_DIRECTORY
        and name.endswith(".synopsis.md")
        and name != ".synopsis.md"
    )


def _write_all(descriptor, data):
    view = memoryview(data)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("zero-byte temporary write")
        view = view[written:]


def _atomic_replace(root, relative, data):
    """Flush and replace one sibling through its directory descriptor."""
    root = _root_path(root)
    relative = _relative_path(relative)
    components = relative.split("/")
    if not _is_output_path(relative):
        raise SynopsisError(f"output is not a supported synopsis sibling: {relative}")
    lexical = os.path.join(root, *components)
    mode = 0o644
    try:
        current = os.lstat(lexical)
    except FileNotFoundError:
        current = None
    except OSError:
        raise SynopsisError(f"synopsis output cannot be inspected: {relative}") from None
    if current is not None:
        if stat.S_ISLNK(current.st_mode):
            raise SynopsisError(f"synopsis output is a symlink: {relative}")
        if not stat.S_ISREG(current.st_mode):
            raise SynopsisError(f"synopsis output is not a regular file: {relative}")
        mode = stat.S_IMODE(current.st_mode)
    if not UNLINK_SUPPORTS_DIR_FD:
        raise SynopsisError("platform cannot safely replace a synopsis")

    parent = _directory_descriptor(root, components[:-1], "synopsis directory")
    temporary = None
    descriptor = None
    try:
        for _ in range(128):
            candidate = f".{components[-1]}.{secrets.token_hex(8)}.tmp"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent,
                )
                temporary = candidate
                break
            except FileExistsError:
                continue
        if descriptor is None:
            raise SynopsisError(f"synopsis temporary name exhausted: {relative}")
        try:
            os.fchmod(descriptor, mode)
            _write_all(descriptor, data)
            os.fsync(descriptor)
        except OSError:
            raise SynopsisError(f"synopsis temporary write failed: {relative}") from None
        finally:
            with contextlib.suppress(OSError):
                os.close(descriptor)
            descriptor = None
        try:
            if not _directory_still_at_path(root, components[:-1], parent):
                raise SynopsisError(
                    f"synopsis directory changed during write: {relative}"
                )
            os.replace(
                temporary,
                components[-1],
                src_dir_fd=parent,
                dst_dir_fd=parent,
            )
            temporary = None
            os.fsync(parent)
        except OSError:
            raise SynopsisError(f"synopsis atomic replacement failed: {relative}") from None
    finally:
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        if temporary is not None:
            with contextlib.suppress(OSError):
                os.unlink(temporary, dir_fd=parent)
        with contextlib.suppress(OSError):
            os.close(parent)

    committed = read_regular_bytes(
        root,
        relative,
        "synopsis output",
        bytes_max=max(SOURCE_BYTES_MAX, len(data)),
    )
    if committed != data:
        raise SynopsisError(
            f"synopsis post-write bytes differ: {relative}; "
            f"expected_sha256={hashlib.sha256(data).hexdigest()}; "
            f"actual_sha256={hashlib.sha256(committed).hexdigest()}"
        )


def atomic_replace(root, relative, data):
    """Replace one sibling; kept separate so refusal races remain injectable."""
    _atomic_replace(root, relative, data)


def _remove_replaced_output(root, relative, expected):
    """Remove a newly-created output only while it still has our exact bytes."""
    root = _root_path(root)
    relative = _relative_path(relative)
    if not _is_output_path(relative):
        raise SynopsisError(f"output is not a supported synopsis sibling: {relative}")
    current = read_regular_bytes(
        root,
        relative,
        "synopsis rollback output",
        missing_ok=True,
        bytes_max=ROLLBACK_BYTES_MAX,
    )
    if current is None:
        return
    if current != expected:
        raise SynopsisError(f"synopsis changed before rollback: {relative}")
    components = relative.split("/")
    parent = _directory_descriptor(root, components[:-1], "synopsis directory")
    try:
        if not _directory_still_at_path(root, components[:-1], parent):
            raise SynopsisError(
                f"synopsis directory changed before rollback: {relative}"
            )
        os.unlink(components[-1], dir_fd=parent)
        os.fsync(parent)
    except OSError:
        raise SynopsisError(f"synopsis rollback removal failed: {relative}") from None
    finally:
        with contextlib.suppress(OSError):
            os.close(parent)
    if read_regular_bytes(
        root,
        relative,
        "synopsis rollback output",
        missing_ok=True,
        bytes_max=ROLLBACK_BYTES_MAX,
    ) is not None:
        raise SynopsisError(f"synopsis rollback removal failed: {relative}")


def _rollback_outputs(root, attempted):
    """Restore the exact destination set captured before a refused write."""
    failures = []
    for item in reversed(attempted):
        try:
            current = read_regular_bytes(
                root,
                item["output"],
                "synopsis rollback output",
                missing_ok=True,
                bytes_max=ROLLBACK_BYTES_MAX,
            )
            previous = item["committed_bytes"]
            if current == previous:
                continue
            if current != item["bytes"]:
                raise SynopsisError(
                    f"synopsis changed before rollback: {item['output']}"
                )
            if previous is None:
                _remove_replaced_output(root, item["output"], item["bytes"])
            else:
                _atomic_replace(root, item["output"], previous)
        except SynopsisError:
            failures.append(item["output"])
    if failures:
        raise SynopsisError(
            "synopsis rollback failed: " + ", ".join(sorted(failures))
        )


def validate_committed_synopsis(root, source_path, source_bytes):
    """Render captured source bytes and require its committed sibling verbatim."""
    rendered = render_source(source_path, source_bytes)
    output = _output_path(source_path)
    committed = read_regular_bytes(root, output, "audit synopsis", missing_ok=True)
    if committed is None:
        raise SynopsisError(f"audit synopsis is missing: {output}")
    actual = hashlib.sha256(committed).hexdigest()
    if committed != rendered["bytes"]:
        raise SynopsisError(
            f"audit synopsis is stale: {output}; "
            f"source_lines={rendered['source_lines']}; "
            f"synopsis_lines={rendered['synopsis_lines']}; budget=pass; "
            f"source_sha256={rendered['source_sha256']}; "
            f"fresh_sha256={rendered['synopsis_sha256']}; "
            f"committed_sha256={actual}"
        )
    return rendered["synopsis_sha256"]


def process_repository(root, *, write):
    root = _root_path(root)
    rendered = []
    sources = discover_sources(root)
    outputs = [_output_path(source) for source in sources]
    if len(set(outputs)) != len(outputs):
        raise SynopsisError("audit sources map to duplicate synopsis outputs")
    if set(sources) & set(outputs):
        raise SynopsisError("a synopsis output was rediscovered as an audit source")
    for source, output in zip(sources, outputs):
        source_bytes = read_regular_bytes(root, source, "audit source")
        item = render_source(source, source_bytes)
        item["output"] = output
        committed = read_regular_bytes(
            root,
            item["output"],
            "audit synopsis",
            missing_ok=True,
            bytes_max=ROLLBACK_BYTES_MAX if write else SOURCE_BYTES_MAX,
        )
        item["committed_bytes"] = committed
        item["committed_sha256"] = (
            hashlib.sha256(committed).hexdigest() if committed is not None else "missing"
        )
        rendered.append(item)

    if write:
        for item in rendered:
            current_source = read_regular_bytes(root, item["source"], "audit source")
            if hashlib.sha256(current_source).hexdigest() != item["source_sha256"]:
                raise SynopsisError(
                    f"audit source changed after planning: {item['source']}"
                )
        attempted = []
        try:
            for item in rendered:
                attempted.append(item)
                atomic_replace(root, item["output"], item["bytes"])
                item["committed"] = "written"
                item["committed_sha256"] = item["synopsis_sha256"]
            if discover_sources(root) != sources:
                raise SynopsisError("audit source set changed after planning")
            for item in rendered:
                current_source = read_regular_bytes(
                    root, item["source"], "audit source"
                )
                if (
                    hashlib.sha256(current_source).hexdigest()
                    != item["source_sha256"]
                ):
                    raise SynopsisError(
                        f"audit source changed after planning: {item['source']}"
                    )
                committed = read_regular_bytes(
                    root, item["output"], "audit synopsis"
                )
                if committed != item["bytes"]:
                    raise SynopsisError(
                        f"synopsis changed after replacement: {item['output']}"
                    )
        except Exception as error:
            try:
                _rollback_outputs(root, attempted)
            except SynopsisError as rollback_error:
                raise SynopsisError(f"{error}; {rollback_error}") from error
            raise
    else:
        for item in rendered:
            if item["committed_bytes"] is None:
                raise SynopsisError(f"audit synopsis is missing: {item['output']}")
            if item["committed_bytes"] != item["bytes"]:
                raise SynopsisError(
                    f"audit synopsis is stale: {item['output']}; "
                    f"source_lines={item['source_lines']}; "
                    f"synopsis_lines={item['synopsis_lines']}; budget=pass; "
                    f"source_sha256={item['source_sha256']}; "
                    f"fresh_sha256={item['synopsis_sha256']}; "
                    f"committed_sha256={item['committed_sha256']}"
                )
            item["committed"] = "match"
    for item in rendered:
        item.pop("bytes", None)
        item.pop("committed_bytes", None)
    return rendered


def _diagnostic(item):
    return (
        f"{item['source']}: source_lines={item['source_lines']} "
        f"synopsis_lines={item['synopsis_lines']} budget={item['budget']} "
        f"source_sha256={item['source_sha256']} "
        f"fresh_sha256={item['synopsis_sha256']} "
        f"committed_sha256={item['committed_sha256']} "
        f"committed={item['committed']}"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="write or check deterministic Fiat audit synopses"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("root", help="real repository root")
    args = parser.parse_args(argv)
    try:
        results = process_repository(args.root, write=args.write)
    except SynopsisError as error:
        print(f"audit_synopsis: error: {error}", file=sys.stderr)
        return 2
    for item in results:
        print(_diagnostic(item))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
