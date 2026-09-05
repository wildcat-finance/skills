#!/usr/bin/env python3
"""Check one source-bound Protasis known-failure inventory.

The checker is read-only. It accepts one bounded inventory block from a stable
study, checks every declared audit synopsis and authoritative source by digest,
and binds each finding to a real runbook step. Exit 0 is clean, 1 is a closed
finding set, and 2 is bad invocation.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import shlex
import stat
import sys
import unicodedata
from itertools import islice
from typing import Iterable


SCHEMA = "protasis-known-failure-inventory/v1"
REPORT_SCHEMA = "protasis-known-failure-inventory-check/v1"
INVENTORY_INFO = "known-failure-inventory"
MAX_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_FINDINGS = 128
MAX_GUARD_PATHS = 4096
MAX_PATH_BYTES = 1024
MAX_SOURCE_VIEWS = 128
MAX_COMMAND_BYTES = 4096
MAX_COMMAND_ARGV = 16
MAX_TEXT_BYTES = 4096
SHELL_PATH_METACHARACTERS = frozenset("$`;&|<>*?[]{}()!~'\" \t")
ADMITTED_REPORT_FORMATS = frozenset(
    {"unittest-json-v1", "forge-junit-v1", "node-test-json-v1"}
)

FENCE = re.compile(r"^ {0,3}(?P<mark>`{3,}|~{3,})(?P<info>[^\r\n]*)$")
INDENTED_FENCE = re.compile(r"^ {1,3}(?:`{3,}|~{3,})")
STEP = re.compile(
    r"^##[ \t]+Step[ \t]+(?P<number>[1-9][0-9]{0,5})[ \t]*:[^\r\n]*$"
)
STEP_LIKE = re.compile(r"^##[ \t]+Step(?:[ \t]|$)")
KNOWN_FAILURE_ID = re.compile(r"^kf-[a-z0-9]+(?:-[a-z0-9]+)*$")
KNOWN_FAILURE_ASSIGNMENT = re.compile(
    r"^Known-failure assignment: `(?P<id>kf-[a-z0-9]+(?:-[a-z0-9]+)*)` "
    r"-> Step (?P<number>[1-9][0-9]{0,5})$"
)
ASSIGNMENT_LIKE = re.compile(r"^Known-failure assignment:")
BACKTICK_RUN = re.compile(r"`+")
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SYNOPSIS_HEADER = re.compile(
    r"^Synopsis schema=fiat-audit-synopsis/v1 \| "
    r"source=(?P<source>[^|\r\n]+?) \| "
    r"source_sha256=(?P<sha256>[0-9a-f]{64}) \| "
    r"h2_count=[0-9]+$"
)

TOP_FIELDS = frozenset({"schema", "source_views", "findings", "no_known_findings"})
SOURCE_VIEW_FIELDS = frozenset({"id", "path", "source_sha256", "view_sha256"})
FINDING_FIELDS = frozenset(
    {
        "id",
        "source_ref",
        "failure",
        "guard_paths",
        "test_command",
        "report_format",
        "report_file",
        "expected_guard_verdict",
        "green_command",
        "consuming_step",
    }
)
NO_FINDINGS_FIELDS = frozenset(
    {"source_views", "consuming_step", "surveyor_assertion"}
)
NO_FINDINGS_VIEW_FIELDS = frozenset({"id", "source_sha256", "view_sha256"})


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path = path
        self.line = line
        self.code = code
        self.message = message

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "line": self.line,
            "code": self.code,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


class _DuplicateKey(ValueError):
    pass


class _ReadRefusal(OSError):
    pass


def _one(path: Path, code: str, message: str, line: int = 1) -> list[Finding]:
    return [Finding(path, line, code, message)]


def _stable_file(path: Path, limit: int = MAX_BYTES) -> bytes:
    """Read one regular leaf without following it and verify stable identity."""
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        named_before = path.lstat()
        if not stat.S_ISREG(named_before.st_mode) or named_before.st_size > limit:
            raise _ReadRefusal("not a bounded regular file")
        descriptor = os.open(path, flags)
        try:
            opened_before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened_before.st_mode)
                or (opened_before.st_dev, opened_before.st_ino)
                != (named_before.st_dev, named_before.st_ino)
            ):
                raise _ReadRefusal("file identity changed before read")
            chunks = bytearray()
            remaining = limit + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.extend(chunk)
                remaining -= len(chunk)
            opened_after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        named_after = path.lstat()
    except (OSError, ValueError, TypeError, NotImplementedError) as error:
        if isinstance(error, _ReadRefusal):
            raise
        raise _ReadRefusal("file could not be read") from error
    if len(chunks) > limit:
        raise _ReadRefusal("file exceeds the byte cap")
    before_identity = (opened_before.st_dev, opened_before.st_ino)
    if (
        before_identity != (opened_after.st_dev, opened_after.st_ino)
        or before_identity != (named_after.st_dev, named_after.st_ino)
        or opened_before.st_size != opened_after.st_size
        or opened_after.st_size != len(chunks)
        or opened_before.st_mtime_ns != opened_after.st_mtime_ns
        or opened_before.st_ctime_ns != opened_after.st_ctime_ns
        or opened_after.st_mtime_ns != named_after.st_mtime_ns
        or opened_after.st_ctime_ns != named_after.st_ctime_ns
    ):
        raise _ReadRefusal("file changed during read")
    return bytes(chunks)


def _portable_path(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        return None
    if (
        len(encoded) > MAX_PATH_BYTES
        or "\\" in value
        or ":" in value
        or any(character in SHELL_PATH_METACHARACTERS for character in value)
    ):
        return None
    if any(
        ord(character) < 32
        or ord(character) == 127
        or character.isspace()
        for character in value
    ):
        return None
    raw_parts = value.split("/")
    if any(part in {"", ".", ".."} for part in raw_parts):
        return None
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or str(candidate) != value:
        return None
    return value


def _portable_alias(value: str) -> str:
    """Return the cross-platform key used for path-set uniqueness."""
    return unicodedata.normalize("NFC", value).casefold()


def _markdown_physical_lines(text: str):
    """Yield only LF, CRLF, and CR-delimited CommonMark physical lines."""
    start = 0
    for ending in re.finditer(r"\r\n|\r|\n", text):
        yield text[start : ending.end()]
        start = ending.end()
    if start < len(text):
        yield text[start:]


def _markdown_fence(line: str):
    """Return one CommonMark fence marker, excluding bad backtick info."""
    fence = FENCE.fullmatch(line)
    if (
        fence is not None
        and fence.group("mark").startswith("`")
        and "`" in fence.group("info")
    ):
        return None
    return fence


def _inline_code_state(line: str) -> tuple[list[tuple[int, int]], bool]:
    """Return bounded one-line CommonMark code spans.

    A delimiter escaped by an odd backslash run starts one byte later. An
    unmatched run is literal text. Multiline spans are deliberately not
    admitted at this machine-record boundary.
    """
    runs = [match.span() for match in BACKTICK_RUN.finditer(line)]

    next_same: list[int | None] = [None] * len(runs)
    next_by_length: dict[int, int] = {}
    positions_by_length: dict[int, list[int]] = {}
    for index in range(len(runs) - 1, -1, -1):
        start, end = runs[index]
        length = end - start
        next_same[index] = next_by_length.get(length)
        next_by_length[length] = index
        positions_by_length.setdefault(length, []).append(index)
    for positions in positions_by_length.values():
        positions.reverse()

    spans: list[tuple[int, int]] = []
    unmatched = False
    index = 0
    while index < len(runs):
        start, end = runs[index]
        backslashes = 0
        cursor = start - 1
        while cursor >= 0 and line[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2:
            start += 1
        if start == end:
            index += 1
            continue
        length = end - start
        raw_length = runs[index][1] - runs[index][0]
        if length == raw_length:
            closed_at = next_same[index]
        else:
            candidates = positions_by_length.get(length, [])
            candidate_at = bisect_right(candidates, index)
            closed_at = (
                candidates[candidate_at]
                if candidate_at < len(candidates)
                else None
            )
        if closed_at is None:
            unmatched = True
            index += 1
            continue
        spans.append((start, runs[closed_at][1]))
        index = closed_at + 1
    return spans, unmatched


def _inline_code_spans(line: str) -> list[tuple[int, int]]:
    """Return only the admitted spans for direct callers and tests."""
    return _inline_code_state(line)[0]


def _uncovered_token(
    line: str, token: str, spans: list[tuple[int, int]]
) -> bool:
    """Find a token outside sorted spans in one linear merge walk."""
    span_index = 0
    cursor = 0
    while True:
        index = line.find(token, cursor)
        if index < 0:
            return False
        while span_index < len(spans) and spans[span_index][1] <= index:
            span_index += 1
        if (
            span_index >= len(spans)
            or not spans[span_index][0] <= index < spans[span_index][1]
        ):
            return True
        cursor = index + len(token)


def _markdown_surface(text: str) -> tuple[str | None, str | None]:
    """Admit a record surface only when HTML cannot hide machine records.

    Fenced code and complete one-line code spans are visible examples. Any
    left-angle byte elsewhere is refused instead of being interpreted as raw
    HTML. This conservative boundary covers valid, malformed, and contextual
    CommonMark HTML without an over-mask path that can suppress a record.
    """
    open_mark: str | None = None
    open_length = 0
    for physical in _markdown_physical_lines(text):
        line = physical.rstrip("\r\n")
        if INDENTED_FENCE.match(line):
            return None, "only column-zero fences are admitted at this boundary"
        fence = _markdown_fence(line)
        if open_mark is not None:
            if fence is not None:
                sequence = fence.group("mark")
                if (
                    sequence[0] == open_mark
                    and len(sequence) >= open_length
                    and not fence.group("info").strip(" \t")
                ):
                    open_mark = None
                    open_length = 0
            continue
        if fence is not None:
            sequence = fence.group("mark")
            open_mark = sequence[0]
            open_length = len(sequence)
            continue
        spans, unmatched_ticks = _inline_code_state(line)
        if unmatched_ticks:
            return None, "multiline or unmatched inline code is unsupported"
        if "<" in line and _uncovered_token(line, "<", spans):
            return None, "raw HTML is unsupported at this machine-record boundary"
        if "![" in line and _uncovered_token(line, "![", spans):
            return None, "Markdown images are unsupported at this boundary"
    return text, None


def _confined_file(root: Path, relative: str, limit: int = MAX_BYTES) -> bytes:
    """Read a portable root-relative path through no-follow directory fds."""
    portable = _portable_path(relative)
    if portable is None:
        raise _ReadRefusal("path is not portable")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    root_fd = None
    current_fd = None
    try:
        root_named = root.lstat()
        if not stat.S_ISDIR(root_named.st_mode):
            raise _ReadRefusal("repository root is not a directory")
        root_fd = os.open(root, directory_flags)
        root_opened = os.fstat(root_fd)
        if (root_named.st_dev, root_named.st_ino) != (root_opened.st_dev, root_opened.st_ino):
            raise _ReadRefusal("repository identity changed")
        current_fd = os.dup(root_fd)
        parts = portable.split("/")
        for part in parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        descriptor = os.open(parts[-1], file_flags, dir_fd=current_fd)
        try:
            opened_before = os.fstat(descriptor)
            named_before = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(opened_before.st_mode)
                or (opened_before.st_dev, opened_before.st_ino)
                != (named_before.st_dev, named_before.st_ino)
                or opened_before.st_size > limit
            ):
                raise _ReadRefusal("source is not a bounded regular file")
            chunks = bytearray()
            remaining = limit + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.extend(chunk)
                remaining -= len(chunk)
            opened_after = os.fstat(descriptor)
            named_after = os.stat(parts[-1], dir_fd=current_fd, follow_symlinks=False)
        finally:
            os.close(descriptor)
    except (OSError, ValueError, TypeError, NotImplementedError) as error:
        if isinstance(error, _ReadRefusal):
            raise
        raise _ReadRefusal("confined source could not be read") from error
    finally:
        if current_fd is not None:
            os.close(current_fd)
        if root_fd is not None:
            os.close(root_fd)
    if len(chunks) > limit:
        raise _ReadRefusal("source exceeds the byte cap")
    identity = (opened_before.st_dev, opened_before.st_ino)
    if (
        identity != (opened_after.st_dev, opened_after.st_ino)
        or identity != (named_after.st_dev, named_after.st_ino)
        or opened_before.st_size != opened_after.st_size
        or opened_after.st_size != len(chunks)
        or opened_before.st_mtime_ns != opened_after.st_mtime_ns
        or opened_before.st_ctime_ns != opened_after.st_ctime_ns
        or opened_after.st_mtime_ns != named_after.st_mtime_ns
        or opened_after.st_ctime_ns != named_after.st_ctime_ns
    ):
        raise _ReadRefusal("source changed during read")
    return bytes(chunks)


def _inventory_block(text: str) -> tuple[str | None, int, str | None]:
    blocks: list[tuple[str, int]] = []
    open_mark: str | None = None
    open_length = 0
    wanted = False
    wanted_line = 1
    body: list[str] = []
    surface, surface_error = _markdown_surface(text)
    if surface_error is not None or surface is None:
        return None, 1, surface_error or "study surface is unavailable"
    physical_lines = list(_markdown_physical_lines(surface))
    for number, physical in enumerate(physical_lines, start=1):
        line = physical.rstrip("\r\n")
        match = _markdown_fence(line)
        if open_mark is None:
            if match is None:
                continue
            sequence = match.group("mark")
            open_mark = sequence[0]
            open_length = len(sequence)
            wanted = match.group("info").strip(" \t") == INVENTORY_INFO
            wanted_line = number
            if wanted and number > 1:
                previous = physical_lines[number - 2].rstrip("\r\n")
                if re.fullmatch(r"[ \t]*", previous) is None:
                    return None, number, "inventory fence is not blank-line isolated"
            body = []
            continue
        if match is not None:
            sequence = match.group("mark")
            if (
                sequence[0] == open_mark
                and len(sequence) >= open_length
                and not match.group("info").strip(" \t")
            ):
                if wanted:
                    if number < len(physical_lines):
                        following = physical_lines[number].rstrip("\r\n")
                        if re.fullmatch(r"[ \t]*", following) is None:
                            return None, number, "inventory fence is not blank-line isolated"
                    blocks.append(("\n".join(body), wanted_line))
                open_mark = None
                open_length = 0
                wanted = False
                body = []
                continue
        if wanted:
            body.append(line)
    if open_mark is not None:
        return None, wanted_line, "inventory or enclosing fence is not closed"
    if len(blocks) != 1:
        return None, 1, f"expected one inventory block; found {len(blocks)}"
    return blocks[0][0], blocks[0][1], None


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _reject_constant(value: str):
    raise ValueError(f"non-finite JSON constant: {value}")


def _depth(value: object) -> int:
    maximum = 0
    pending: list[tuple[object, int]] = [(value, 1)]
    while pending:
        current, depth = pending.pop()
        maximum = max(maximum, depth)
        if maximum > MAX_JSON_DEPTH:
            return maximum
        if isinstance(current, dict):
            pending.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)
    return maximum


def _json(body: str) -> dict:
    try:
        value = json.loads(
            body,
            object_pairs_hook=_pairs,
            parse_constant=_reject_constant,
        )
    except (ValueError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("inventory JSON is malformed or repeats a key") from error
    if _depth(value) > MAX_JSON_DEPTH:
        raise ValueError("inventory JSON exceeds the depth cap")
    if not isinstance(value, dict):
        raise ValueError("inventory JSON is not an object")
    return value


def _exact_fields(value: object, fields: frozenset[str]) -> bool:
    return isinstance(value, dict) and frozenset(value) == fields


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _bounded_line(value: object) -> bool:
    if not _nonempty_text(value) or "\n" in value or "\r" in value:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        return False
    return len(encoded) <= MAX_TEXT_BYTES and not any(
        ord(character) < 32
        or ord(character) == 127
        or (character != " " and character.isspace())
        for character in value
    )


def _secure_read_primitives() -> bool:
    if any(
        not hasattr(os, name)
        for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    ):
        return False
    dir_fd = getattr(os, "supports_dir_fd", ())
    follow = getattr(os, "supports_follow_symlinks", ())
    return os.open in dir_fd and os.stat in dir_fd and os.stat in follow


def _argv(command: object, *, report_placeholder: bool) -> list[str] | None:
    if not _nonempty_text(command) or "\x00" in command:
        return None
    try:
        encoded = command.encode("utf-8")
    except UnicodeError:
        return None
    if (
        len(encoded) > MAX_COMMAND_BYTES
        or any(
            ord(character) < 32
            or ord(character) == 127
            or (character != " " and character.isspace())
            for character in command
        )
    ):
        return None
    try:
        arguments = shlex.split(command, posix=True)
    except ValueError:
        return None
    if (
        not arguments
        or len(arguments) > MAX_COMMAND_ARGV
        or any(not argument for argument in arguments)
    ):
        return None
    placeholder_count = sum(argument == "{report}" for argument in arguments)
    if report_placeholder:
        return arguments if placeholder_count == 1 else None
    return arguments if placeholder_count == 0 else None


def _expected_green_report(report_file: str) -> str:
    path = PurePosixPath(report_file)
    suffix = path.suffix
    name = path.name[:-len(suffix)] if suffix else path.name
    green_name = f"{name}-green{suffix}"
    return str(path.parent / green_name)


def _commands_agree(
    finding_id: str,
    guard_paths: list[str],
    test_arguments: list[str],
    green_arguments: list[str],
    report_file: str,
) -> tuple[bool, bool]:
    """Return (test-valid, green-valid) for the closed command pair."""
    if len(test_arguments) != 6:
        return False, False
    runner = test_arguments[1]
    test_valid = test_arguments == [
        "python3",
        runner,
        "--case",
        finding_id,
        "--report",
        "{report}",
    ] and runner in guard_paths and PurePosixPath(runner).suffix == ".py"
    if not test_valid:
        return False, False

    expected_green = _expected_green_report(report_file)
    green_valid = green_arguments == [
        "python3",
        runner,
        "--case",
        finding_id,
        "--report",
        expected_green,
    ]
    return True, green_valid


def _runbook_contract(
    text: str,
) -> tuple[dict[int, set[str]] | None, set[str], str | None]:
    """Return top-level Steps and exact visible known-failure assignments."""
    step_ids: dict[int, set[str]] = {}
    open_mark: str | None = None
    open_length = 0
    assigned_ids: set[str] = set()
    assignments: list[tuple[str, int]] = []
    block_has_assignment = False
    block_has_other = False
    surface, surface_error = _markdown_surface(text)
    if surface_error is not None or surface is None:
        return None, set(), surface_error or "runbook surface is unavailable"
    for physical in _markdown_physical_lines(surface):
        line = physical.rstrip("\r\n")
        if open_mark is not None:
            fence = _markdown_fence(line)
            if fence is not None:
                sequence = fence.group("mark")
                if (
                    sequence[0] == open_mark
                    and len(sequence) >= open_length
                    and not fence.group("info").strip(" \t")
                ):
                    open_mark = None
                    open_length = 0
            continue

        fence = _markdown_fence(line)
        if fence is not None:
            sequence = fence.group("mark")
            open_mark = sequence[0]
            open_length = len(sequence)
            block_has_assignment = False
            block_has_other = False
            continue

        if re.fullmatch(r"[ \t]*", line) is not None:
            block_has_assignment = False
            block_has_other = False
            continue

        assignment = KNOWN_FAILURE_ASSIGNMENT.fullmatch(line)
        block_has_assignment = block_has_assignment or assignment is not None
        block_has_other = block_has_other or assignment is None
        if block_has_assignment and block_has_other:
            return None, set(), "a known-failure assignment shares a prose block"

        step = STEP.fullmatch(line)
        if step is not None:
            number = int(step.group("number"))
            if number in step_ids:
                return None, set(), "runbook steps are absent or duplicated"
            step_ids[number] = set()
            continue
        if STEP_LIKE.match(line):
            return None, set(), "runbook contains a malformed Step heading"
        if assignment is not None:
            finding_id = assignment.group("id")
            declared_step = int(assignment.group("number"))
            if finding_id in assigned_ids:
                return None, set(), "a known-failure assignment is misplaced or duplicated"
            assignments.append((finding_id, declared_step))
            assigned_ids.add(finding_id)
            continue
        if ASSIGNMENT_LIKE.match(line):
            return None, set(), "runbook contains a malformed known-failure assignment"

    if open_mark is not None:
        return None, set(), "runbook contains an unclosed fence"
    if not step_ids:
        return None, set(), "runbook steps are absent or duplicated"
    for finding_id, declared_step in assignments:
        if declared_step not in step_ids:
            return None, set(), "a known-failure assignment names no real Step"
        step_ids[declared_step].add(finding_id)
    return step_ids, assigned_ids, None


def _expected_id_contract(
    values: Iterable[str] | None,
    runbook_ids: set[str],
) -> tuple[set[str] | None, str | None]:
    if values is None:
        return set(runbook_ids), None
    if isinstance(values, (str, bytes)):
        return None, "the independent expected id set is malformed"
    try:
        items = list(islice(iter(values), MAX_FINDINGS + 1))
    except Exception:
        return None, "the independent expected id set is malformed"
    if (
        len(items) > MAX_FINDINGS
        or any(
            not isinstance(item, str) or KNOWN_FAILURE_ID.fullmatch(item) is None
            for item in items
        )
    ):
        return None, "the independent expected id set is malformed"
    independent_ids = set(items)
    if len(independent_ids) != len(items):
        return None, "the independent expected id set is malformed"
    return independent_ids, None


def _elenchus_report_path(value: object) -> str | None:
    portable = _portable_path(value)
    if portable is None:
        return None
    path = PurePosixPath(portable)
    if len(path.parts) < 2 or path.parts[0] != ".elenchus":
        return None
    return portable


def _revalidate_inputs(
    study: Path,
    study_bytes: bytes,
    runbook: Path,
    runbook_bytes: bytes,
    repository: Path,
    sources: list[tuple[str, str, bytes, str, str, bytes, str]],
) -> list[Finding]:
    """Reread every consumed input at the final boundary."""
    try:
        current_study = _stable_file(study)
    except OSError:
        return _one(study, "K000", "study cannot be reread at the final boundary")
    if current_study != study_bytes:
        return _one(study, "K000", "study bytes changed before the final boundary")
    try:
        current_runbook = _stable_file(runbook)
    except OSError:
        return _one(runbook, "K000", "runbook cannot be reread at the final boundary")
    if current_runbook != runbook_bytes:
        return _one(runbook, "K000", "runbook bytes changed before the final boundary")

    for (
        source_id,
        view_path,
        view_bytes,
        view_sha256,
        source_path,
        source_bytes,
        source_sha256,
    ) in sources:
        view_target = repository / view_path
        try:
            current_view = _confined_file(repository, view_path)
        except OSError:
            return _one(
                view_target,
                "K005",
                f"{source_id} view cannot be reread for view_sha256 {view_sha256}",
            )
        if current_view != view_bytes:
            actual = hashlib.sha256(current_view).hexdigest()
            return _one(
                view_target,
                "K005",
                f"{source_id} view_sha256 changed from {view_sha256} to {actual}",
            )

        source_target = repository / source_path
        try:
            current_source = _confined_file(repository, source_path)
        except OSError:
            return _one(
                source_target,
                "K005",
                f"{source_id} source cannot be reread for source_sha256 {source_sha256}",
            )
        if current_source != source_bytes:
            actual = hashlib.sha256(current_source).hexdigest()
            return _one(
                source_target,
                "K005",
                f"{source_id} source_sha256 changed from {source_sha256} to {actual}",
            )
    return []


def check(
    study_path: Path | str,
    runbook_path: Path | str,
    repository_root: Path | str,
    expected_ids: Iterable[str] | None = None,
) -> list[Finding]:
    """Return a closed list of findings without writing state or ledgers."""
    study = Path(study_path)
    runbook = Path(runbook_path)
    repository = Path(repository_root)
    if not _secure_read_primitives():
        return _one(study, "K000", "secure no-follow file reads are unavailable")
    try:
        study_bytes = _stable_file(study)
        study_text = study_bytes.decode("utf-8", errors="strict")
    except (OSError, UnicodeError):
        return _one(study, "K000", "study is not a stable bounded UTF-8 file")
    try:
        runbook_bytes = _stable_file(runbook)
        runbook_text = runbook_bytes.decode("utf-8", errors="strict")
    except (OSError, UnicodeError):
        return _one(runbook, "K000", "runbook is not a stable bounded UTF-8 file")

    body, line, fence_error = _inventory_block(study_text)
    if fence_error is not None or body is None:
        return _one(study, "K001", fence_error or "inventory block is unavailable", line)
    try:
        inventory = _json(body)
    except ValueError as error:
        return _one(study, "K002", str(error), line)
    if not _exact_fields(inventory, TOP_FIELDS) or inventory.get("schema") != SCHEMA:
        return _one(study, "K003", "inventory top level or schema is not closed", line)

    source_views = inventory["source_views"]
    if not isinstance(source_views, list) or not source_views or len(source_views) > MAX_SOURCE_VIEWS:
        return _one(study, "K004", "source_views must be one bounded non-empty list", line)
    source_ids: set[str] = set()
    source_view_paths: set[str] = set()
    checked_views: list[dict[str, str]] = []
    checked_sources: list[tuple[str, str, bytes, str, str, bytes, str]] = []
    for index, view in enumerate(source_views):
        label = f"source_views[{index}]"
        if not _exact_fields(view, SOURCE_VIEW_FIELDS):
            return _one(study, "K004", f"{label} has omitted or extra fields", line)
        source_id = view["id"]
        path = _portable_path(view["path"])
        if (
            not isinstance(source_id, str)
            or KEBAB.fullmatch(source_id) is None
            or source_id in source_ids
            or path is None
            or _portable_alias(path) in source_view_paths
            or not isinstance(view["source_sha256"], str)
            or SHA256.fullmatch(view["source_sha256"]) is None
            or not isinstance(view["view_sha256"], str)
            or SHA256.fullmatch(view["view_sha256"]) is None
        ):
            return _one(study, "K004", f"{label} has an invalid id, path, or digest", line)
        source_ids.add(source_id)
        source_view_paths.add(_portable_alias(path))
        view_target = repository / path
        try:
            view_bytes = _confined_file(repository, path)
        except OSError:
            return _one(
                view_target,
                "K005",
                f"{source_id} view path cannot be verified for view_sha256",
                line,
            )
        try:
            view_text = view_bytes.decode("utf-8", errors="strict")
            first_physical = next(_markdown_physical_lines(view_text), "")
            first_line = first_physical.rstrip("\r\n")
            header = SYNOPSIS_HEADER.fullmatch(first_line)
        except UnicodeError:
            return _one(
                view_target,
                "K005",
                f"{source_id} view is not UTF-8 for view_sha256",
                line,
            )
        if header is None:
            return _one(
                view_target,
                "K005",
                f"{source_id} view header cannot be verified for source_sha256",
                line,
            )
        source_path = _portable_path(header.group("source"))
        if source_path is None:
            return _one(
                view_target,
                "K005",
                f"{source_id} view header has a non-portable source path",
                line,
            )
        if header.group("sha256") != view["source_sha256"]:
            return _one(
                view_target,
                "K005",
                f"{source_id} source_sha256 differs between inventory and view header",
                line,
            )
        source_target = repository / source_path
        try:
            source_bytes = _confined_file(repository, source_path)
        except OSError:
            return _one(
                source_target,
                "K005",
                f"{source_id} source path cannot be verified for source_sha256",
                line,
            )
        try:
            view_again = _confined_file(repository, path)
        except OSError:
            return _one(
                view_target,
                "K005",
                f"{source_id} view path cannot be reverified for view_sha256",
                line,
            )
        if view_again != view_bytes:
            return _one(
                view_target,
                "K005",
                f"{source_id} view bytes changed during view_sha256 verification",
                line,
            )
        actual_view_sha256 = hashlib.sha256(view_bytes).hexdigest()
        if actual_view_sha256 != view["view_sha256"]:
            return _one(
                view_target,
                "K005",
                f"{source_id} view_sha256 expected {view['view_sha256']} got {actual_view_sha256}",
                line,
            )
        actual_source_sha256 = hashlib.sha256(source_bytes).hexdigest()
        if actual_source_sha256 != view["source_sha256"]:
            return _one(
                source_target,
                "K005",
                f"{source_id} source_sha256 expected {view['source_sha256']} got {actual_source_sha256}",
                line,
            )
        checked_views.append(
            {
                "id": source_id,
                "source_sha256": view["source_sha256"],
                "view_sha256": view["view_sha256"],
            }
        )
        checked_sources.append(
            (
                source_id,
                path,
                view_bytes,
                view["view_sha256"],
                source_path,
                source_bytes,
                view["source_sha256"],
            )
        )

    step_ids, runbook_ids, runbook_error = _runbook_contract(runbook_text)
    if runbook_error is not None or step_ids is None:
        return _one(runbook, "K010", runbook_error or "runbook steps are unavailable")
    independent_ids, expected_error = _expected_id_contract(expected_ids, runbook_ids)
    if expected_error is not None or independent_ids is None:
        return _one(runbook, "K006", expected_error or "the expected id set is unavailable")

    findings = inventory["findings"]
    if not isinstance(findings, list):
        return _one(study, "K006", "findings is not a list", line)
    if len(findings) > MAX_FINDINGS:
        return _one(study, "K012", "finding count exceeds 128", line)
    finding_ids: set[str] = set()
    report_paths: set[str] = set()
    guard_path_count = 0
    for index, finding in enumerate(findings):
        label = f"findings[{index}]"
        if not _exact_fields(finding, FINDING_FIELDS):
            return _one(study, "K006", f"{label} has omitted or extra fields", line)
        finding_id = finding["id"]
        source_ref = finding["source_ref"]
        if (
            not isinstance(finding_id, str)
            or KNOWN_FAILURE_ID.fullmatch(finding_id) is None
            or finding_id in finding_ids
            or not _bounded_line(finding["failure"])
            or not _bounded_line(source_ref)
            or ":" not in source_ref
        ):
            return _one(study, "K006", f"{label} has an invalid id, source_ref, or failure", line)
        source_id, source_detail = source_ref.split(":", 1)
        if source_id not in source_ids or not source_detail.strip():
            return _one(study, "K006", f"{finding_id} does not name one checked source", line)
        finding_ids.add(finding_id)

        guard_paths = finding["guard_paths"]
        if (
            not isinstance(guard_paths, list)
            or not guard_paths
            or any(_portable_path(path) is None for path in guard_paths)
            or len({_portable_alias(path) for path in guard_paths}) != len(guard_paths)
        ):
            return _one(study, "K007", f"{finding_id} guard_paths are not closed", line)
        guard_path_count += len(guard_paths)
        if guard_path_count > MAX_GUARD_PATHS:
            return _one(study, "K012", "aggregate guard path count exceeds 4096", line)

        report_file = finding["report_file"]
        report_format = finding["report_format"]
        admitted_report_file = _elenchus_report_path(report_file)
        green_report_file = (
            _expected_green_report(admitted_report_file)
            if admitted_report_file is not None
            else None
        )
        report_alias = (
            _portable_alias(admitted_report_file)
            if admitted_report_file is not None
            else None
        )
        green_report_alias = (
            _portable_alias(green_report_file)
            if green_report_file is not None
            else None
        )
        if (
            not isinstance(report_format, str)
            or report_format not in ADMITTED_REPORT_FORMATS
            or admitted_report_file is None
            or _elenchus_report_path(green_report_file) is None
            or report_alias in report_paths
            or green_report_alias in report_paths
            or report_alias == green_report_alias
            or finding["expected_guard_verdict"] != "guarded"
        ):
            return _one(study, "K009", f"{finding_id} report contract is not admitted", line)
        report_paths.update((report_alias, green_report_alias))
        test_argv = _argv(finding["test_command"], report_placeholder=True)
        if test_argv is None:
            return _one(study, "K008", f"{finding_id} test command lacks one exact report argv", line)
        green_argv = _argv(finding["green_command"], report_placeholder=False)
        if green_argv is None:
            return _one(study, "K009", f"{finding_id} green command is malformed", line)
        test_valid, green_valid = _commands_agree(
            finding_id,
            guard_paths,
            test_argv,
            green_argv,
            admitted_report_file,
        )
        if not test_valid:
            return _one(study, "K008", f"{finding_id} test command does not bind its runner and case", line)
        if not green_valid:
            return _one(study, "K009", f"{finding_id} green command or report path does not match", line)
        consuming_step = finding["consuming_step"]
        if (
            isinstance(consuming_step, bool)
            or not isinstance(consuming_step, int)
            or consuming_step not in step_ids
            or finding_id not in step_ids[consuming_step]
        ):
            return _one(
                study,
                "K010",
                f"{finding_id} has no one visible assignment to its consuming Step",
                line,
            )

    if finding_ids != independent_ids or finding_ids != runbook_ids:
        return _one(
            study,
            "K006",
            "inventory ids differ from the independent and runbook assignment id sets",
            line,
        )

    no_findings = inventory["no_known_findings"]
    if findings:
        if no_findings is not None:
            return _one(study, "K011", "non-empty findings require a null no-known-findings claim", line)
    else:
        if not _exact_fields(no_findings, NO_FINDINGS_FIELDS):
            return _one(study, "K011", "empty findings require one closed no-known-findings claim", line)
        claim_views = no_findings["source_views"]
        if (
            not isinstance(claim_views, list)
            or claim_views != checked_views
            or any(not _exact_fields(item, NO_FINDINGS_VIEW_FIELDS) for item in claim_views)
            or no_findings["surveyor_assertion"] != "no-known-findings"
            or isinstance(no_findings["consuming_step"], bool)
            or not isinstance(no_findings["consuming_step"], int)
            or no_findings["consuming_step"] not in step_ids
        ):
            return _one(study, "K011", "no-known-findings claim is stale, incomplete, or unassigned", line)

    return _revalidate_inputs(
        study,
        study_bytes,
        runbook,
        runbook_bytes,
        repository,
        checked_sources,
    )


def _arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("study", type=Path)
    parser.add_argument("runbook", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--expected-id", action="append", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    options = _arguments(sys.argv[1:] if argv is None else argv)
    found = check(
        options.study,
        options.runbook,
        options.repository,
        expected_ids=options.expected_id,
    )
    if options.format == "json":
        print(
            json.dumps(
                {
                    "schema": REPORT_SCHEMA,
                    "clean": not found,
                    "finding_count": len(found),
                    "findings": [finding.as_dict() for finding in found],
                },
                sort_keys=True,
            )
        )
    else:
        for finding in found:
            print(finding)
        print(f"known-failure-inventory: {len(found)} finding(s)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
