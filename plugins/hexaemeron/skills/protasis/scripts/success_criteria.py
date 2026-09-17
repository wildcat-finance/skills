#!/usr/bin/env python3
"""Parse the study's declared success criteria and bind them to runbook Exits.

The declaration is deliberately a small, inert interface.  It names what a
study expects to settle, and the runbook join names the one effective Exit
command that can settle each row.  This module never imports a target module,
executes a command, or reads a path selected by a declaration.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path


SCHEMA = "protasis-success-criteria/v1"
JOIN_SCHEMA = "protasis-success-criteria-join/v1"
FENCE_INFO = "success-criteria"
MAX_DOCUMENT_BYTES = 256 * 1024
MAX_CRITERIA = 128
MAX_ID_BYTES = 128
MAX_CLAIM_BYTES = 4096
MAX_COMMAND_BYTES = 64 * 1024
MAX_STEP = 4095
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FENCE = re.compile(r"^(?P<mark>`{3,}|~{3,})(?P<tail>[^\n]*)$")


class Refusal(ValueError):
    """A declaration or join cannot be admitted."""


class DuplicateKey(Refusal):
    """A JSON object contains the same member more than once."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey("duplicate-key")
        result[key] = value
    return result


def _canonical(value) -> bytes:
    try:
        return (
            json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n"
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise Refusal("unsupported-json-value") from exc


def canonical_bytes(record: dict) -> bytes:
    """Return the stable bytes used for a declaration digest."""
    return _canonical(record)


def descriptor_bytes(descriptor: dict) -> bytes:
    """Return stable bytes for one criterion descriptor."""
    if not isinstance(descriptor, dict):
        raise Refusal("descriptor-not-object")
    return _canonical(descriptor)


def descriptor_sha256(descriptor: dict) -> str:
    return digest(descriptor_bytes(descriptor))


def _bounded_text(value, maximum: int, reason: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise Refusal(reason)
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise Refusal(reason) from exc
    if size > maximum or any(not character.isprintable() for character in value):
        raise Refusal(reason)
    return value


def _read_path(path: Path) -> bytes:
    """Read one bounded regular file without following the final symlink."""
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            raise Refusal("input-not-bounded-regular-file")
        if before.st_size > MAX_DOCUMENT_BYTES:
            raise Refusal("input-too-large")
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode) or opened.st_size > MAX_DOCUMENT_BYTES:
                raise Refusal("input-not-bounded-regular-file")
            chunks = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(64 * 1024,
                                                MAX_DOCUMENT_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_DOCUMENT_BYTES:
                    raise Refusal("input-too-large")
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        named = path.lstat()
        identity = lambda item: (
            item.st_dev, item.st_ino, item.st_mode, item.st_nlink,
            item.st_size, item.st_mtime_ns, item.st_ctime_ns,
        )
        if identity(before) != identity(opened) or identity(opened) != identity(after):
            raise Refusal("input-changed-during-read")
        if identity(after) != identity(named):
            raise Refusal("input-changed-during-read")
        return b"".join(chunks)
    except OSError as exc:
        raise Refusal("input-unavailable") from exc


def _source_bytes(source) -> bytes:
    if isinstance(source, Path):
        return _read_path(source)
    if isinstance(source, bytes):
        data = source
    elif isinstance(source, str):
        try:
            data = source.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise Refusal("input-encoding") from exc
    else:
        raise Refusal("input-type")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise Refusal("input-too-large")
    return data


def _fence_candidates(text: str):
    """Yield (opening line, payload) for top-level success-criteria fences."""
    open_mark = None
    open_length = None
    open_info = None
    opening_line = 0
    body = []
    found = []
    for number, raw in enumerate(text.splitlines(keepends=True), start=1):
        line = raw.rstrip("\r\n")
        match = _FENCE.fullmatch(line)
        if open_mark is None:
            # The declaration is column-zero.  An indented candidate is named
            # rather than silently treated as ordinary prose.
            indented = re.match(r"^ {1,3}(?P<mark>`{3,}|~{3,})(?P<tail>.*)$", line)
            if indented:
                words = indented.group("tail").strip().split()
                if words and words[0] == FENCE_INFO:
                    raise Refusal("success-criteria-fence-not-column-zero")
            if match is None:
                continue
            sequence = match.group("mark")
            tail = match.group("tail").strip()
            words = tail.split()
            if words and words[0] == FENCE_INFO and tail != FENCE_INFO:
                raise Refusal("success-criteria-fence-info")
            open_mark = sequence[0]
            open_length = len(sequence)
            open_info = tail
            opening_line = number
            body = []
            continue
        # A closing marker must use the opening character, be at least as
        # long, and have no trailing bytes.  Short or mixed markers remain
        # payload, which keeps an outer fence from donating a nested decoy.
        if (
            match is not None
            and match.group("mark")[0] == open_mark
            and len(match.group("mark")) >= open_length
            and not match.group("tail").strip()
        ):
            if open_info == FENCE_INFO:
                found.append((opening_line, "".join(body)))
            open_mark = open_length = open_info = None
            opening_line = 0
            body = []
        else:
            body.append(raw)
    if open_mark is not None:
        if open_info == FENCE_INFO:
            raise Refusal("success-criteria-fence-unclosed")
        # An unrelated unclosed fence is a runbook/study concern owned by the
        # existing parser; it cannot turn a declaration into one.
    if len(found) > 1:
        raise Refusal("success-criteria-fence-ambiguous")
    return found


def _decode_payload(payload: str) -> dict:
    try:
        value = json.loads(
            payload.encode("utf-8").decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite-{token}")
            ),
        )
    except DuplicateKey as exc:
        raise Refusal("success-criteria-duplicate-key") from exc
    except (UnicodeDecodeError, ValueError, TypeError, RecursionError, MemoryError) as exc:
        raise Refusal("success-criteria-invalid-json") from exc
    if not isinstance(value, dict):
        raise Refusal("success-criteria-root-not-object")
    if set(value) != {"schema", "criteria"}:
        raise Refusal("success-criteria-fields")
    if value.get("schema") != SCHEMA:
        raise Refusal("success-criteria-schema")
    rows = value.get("criteria")
    if not isinstance(rows, list) or not rows:
        raise Refusal("success-criteria-empty")
    if len(rows) > MAX_CRITERIA:
        raise Refusal("success-criteria-count")
    result = {"schema": SCHEMA, "criteria": []}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "claim", "step", "command"}:
            raise Refusal("success-criteria-row-fields")
        identifier = _bounded_text(row["id"], MAX_ID_BYTES, "success-criteria-id")
        if ID.fullmatch(identifier) is None:
            raise Refusal("success-criteria-id")
        if identifier in seen:
            raise Refusal("success-criteria-duplicate-id")
        seen.add(identifier)
        claim = _bounded_text(row["claim"], MAX_CLAIM_BYTES, "success-criteria-claim")
        step = row["step"]
        if type(step) is not int or step < 1 or step > MAX_STEP:
            raise Refusal("success-criteria-step")
        command = _bounded_text(row["command"], MAX_COMMAND_BYTES,
                                "success-criteria-command")
        if "\n" in command or "\r" in command:
            raise Refusal("success-criteria-command")
        result["criteria"].append({
            "id": identifier,
            "claim": claim,
            "step": step,
            "command": command,
        })
    return result


def parse(source):
    """Parse one declaration, returning ``None`` when the fence is absent."""
    data = _source_bytes(source)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("success-criteria-encoding") from exc
    candidates = _fence_candidates(text)
    if not candidates:
        return None
    _, payload = candidates[0]
    return _decode_payload(payload)


def load(source):
    """Compatibility alias for callers that describe parsing as loading."""
    return parse(source)


def _validated_record(record: dict) -> dict:
    """Re-apply the closed row contract to an in-memory caller value."""
    if not isinstance(record, dict):
        raise Refusal("success-criteria-fields")
    try:
        encoded = json.dumps(record, ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise Refusal("success-criteria-invalid-record") from exc
    try:
        return _decode_payload(encoded.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise Refusal("success-criteria-invalid-record") from exc


def declaration_digest(record: dict) -> str:
    return digest(canonical_bytes(_validated_record(record)))


def _line_offsets(text: str):
    offset = 0
    for raw in text.splitlines(keepends=True):
        line = raw.rstrip("\r\n")
        yield offset, raw, line
        offset += len(raw.encode("utf-8"))


def _step_field_ranges(text: str):
    """Return baseline and amendment field ranges in UTF-8 byte offsets."""
    # This is intentionally a narrow Markdown reader.  Protasis has already
    # checked the complete runbook shape; this pass only needs field ownership
    # and amendment replacement ownership for exact command binding.
    step_heading = re.compile(r"^##\s+Step\s+([1-9][0-9]{0,3})\s*:")
    field_heading = re.compile(r"^\*\*(Goal|Entry|Exit|Files|Tests|Disciplines)\.\*\*")
    amendment_heading = re.compile(r"^###\s+Amendment\s+--\s+\d{4}-\d{2}-\d{2}\s*$")
    lines = list(_line_offsets(text))
    fields = []
    current_step = None
    current_field = None
    start = None
    for index, (offset, raw, line) in enumerate(lines):
        if amendment_heading.fullmatch(line):
            if start is not None:
                fields.append((current_step, current_field, start, offset))
            current_step = current_field = None
            start = None
            break
        step = step_heading.match(line)
        if step:
            if start is not None:
                fields.append((current_step, current_field, start, offset))
            current_step = int(step.group(1))
            current_field = None
            start = None
            continue
        field = field_heading.match(line)
        if field and current_step is not None:
            if start is not None:
                fields.append((current_step, current_field, start, offset))
            current_field = field.group(1)
            start = offset
    end = len(text.encode("utf-8"))
    if start is not None:
        fields.append((current_step, current_field, start, end))

    # Amendment replacement fields are independent byte ranges.  The
    # ``Steps touched`` line is the authority for which step they replace.
    cursor = text.find("\n### Amendment -- ")
    while cursor >= 0:
        next_cursor = text.find("\n### Amendment -- ", cursor + 1)
        section_end = next_cursor if next_cursor >= 0 else len(text)
        section = text[cursor + 1:section_end]
        touched = re.search(r"(?m)^\*\*Steps touched\.\*\*([^\n]+)", section)
        steps = [int(n) for n in re.findall(r"[0-9]+", touched.group(1))] if touched else []
        replacements = list(re.finditer(
            r"Complete replacement (Goal|Entry|Exit|Files|Tests|Disciplines):",
            section,
        ))
        section_byte = len(text[:cursor + 1].encode("utf-8"))
        for pos, replacement in enumerate(replacements):
            stop = replacements[pos + 1].start() if pos + 1 < len(replacements) else len(section)
            start_byte = section_byte + len(section[:replacement.start()].encode("utf-8"))
            stop_byte = section_byte + len(section[:stop].encode("utf-8"))
            for step in steps:
                fields.append((step, replacement.group(1), start_byte, stop_byte))
        cursor = next_cursor
    return fields


def _command_records(text: str):
    """Extract literal commands from Exit/Tests-shaped Markdown fields."""
    # The full command grammar remains in gate_commands.  This small extractor
    # is used only to associate already-admitted command records with fields;
    # callers should pass the records returned by gate_commands when they need
    # source/CLI admission as well.
    records = []
    fields = _step_field_ranges(text)
    active_ranges = effective_exit_ranges(text)
    for step, field, start, stop in fields:
        if field != "Exit":
            continue
        section = text.encode("utf-8")[start:stop].decode("utf-8", "strict")
        # Inline code is the only command form available in ordinary field
        # prose.  Fenced commands are handled by gate_commands and supplied as
        # records to ``join`` below.
        for match in re.finditer(r"`([^`\n]+)`", section):
            offset = start + len(section[:match.start(1)].encode("utf-8"))
            if any(active_start <= offset < active_stop
                   for active_step, active_start, active_stop in active_ranges
                   if active_step == step):
                records.append({
                    "step": step,
                    "field": field,
                    "offset": offset,
                    "command": match.group(1),
                })
    return records


def effective_exit_ranges(text: str):
    """Return active ``(step, start, stop)`` Exit ranges."""
    fields = _step_field_ranges(text)
    # A later replacement is active for its step; baseline is active only when
    # no replacement for the same step/field exists.
    amendment_at = text.find("\n### Amendment -- ")
    baseline_end = (
        len(text[:amendment_at].encode("utf-8"))
        if amendment_at >= 0 else len(text.encode("utf-8"))
    )
    replacements = {
        (step, field)
        for step, field, start, _ in fields
        if start >= baseline_end and field in ("Exit", "Tests")
    }
    active = []
    for step, field, start, stop in fields:
        if field != "Exit":
            continue
        if start < baseline_end and (step, field) in replacements:
            continue
        active.append((step, start, stop))
    return active


def join(record: dict | None, runbook, *, command_records=None) -> dict | None:
    """Join each declared descriptor to one effective Exit command.

    ``command_records`` may be the records from ``gate_commands.commands``;
    when omitted, inline Exit commands are read by the bounded association
    pass.  The returned object is deterministic and contains no execution
    result.
    """
    if record is None:
        return None
    record = _validated_record(record)
    data = _source_bytes(runbook)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("runbook-encoding") from exc
    ranges = effective_exit_ranges(text)
    if command_records is None:
        candidates = _command_records(text)
    else:
        candidates = []
        for item in command_records:
            if not isinstance(item, dict) or not item.get("effective", True):
                continue
            offset = item.get("offset")
            command = item.get("command")
            if type(offset) is not int or not isinstance(command, str):
                continue
            for step, start, stop in ranges:
                if start <= offset < stop:
                    candidates.append({
                        "step": step,
                        "field": "Exit",
                        "offset": offset,
                        "command": command,
                        "source": item,
                    })
                    break
    result_rows = []
    for descriptor in record["criteria"]:
        matches = [item for item in candidates
                   if item["step"] == descriptor["step"]
                   and item["command"] == descriptor["command"]]
        if not matches:
            raise Refusal("criteria-exit-missing:" + descriptor["id"])
        if len(matches) != 1:
            raise Refusal("criteria-exit-ambiguous:" + descriptor["id"])
        match = matches[0]
        row = dict(descriptor)
        row["exit"] = {
            "step": match["step"],
            "command": match["command"],
            "offset": match["offset"],
            "command_sha256": digest(match["command"].encode("utf-8")),
        }
        if "source" in match:
            row["exit"]["source"] = match["source"]
        row["descriptor_sha256"] = descriptor_sha256(descriptor)
        result_rows.append(row)
    return {
        "schema": JOIN_SCHEMA,
        "declaration_sha256": declaration_digest(record),
        "runbook_sha256": digest(data),
        "criteria": result_rows,
    }


def join_to_exits(record: dict | None, runbook, *, command_records=None):
    return join(record, runbook, command_records=command_records)


def bind(record: dict | None, runbook, *, command_records=None):
    return join(record, runbook, command_records=command_records)


def criteria_for_step(joined: dict | None, step: int) -> list[dict]:
    """Return the immutable descriptors consumed by one numbered step.

    Execution custody uses this projection to decide which rows one observed
    Exit settles.  It is deliberately read-only and preserves the join's
    descriptor order; it never infers a criterion from a command or from a
    result record.
    """
    if not isinstance(joined, dict) or joined.get("schema") != JOIN_SCHEMA:
        raise Refusal("join-schema")
    if type(step) is not int or step < 1:
        raise Refusal("join-step")
    rows = joined.get("criteria")
    if not isinstance(rows, list) or len(rows) > MAX_CRITERIA:
        raise Refusal("join-criteria")
    return [row for row in rows if isinstance(row, dict) and row.get("step") == step]


def descriptor_ids(joined: dict | None) -> list[str]:
    """Return all joined ids in their declared order for receipt readback."""
    if not isinstance(joined, dict) or joined.get("schema") != JOIN_SCHEMA:
        raise Refusal("join-schema")
    rows = joined.get("criteria")
    if not isinstance(rows, list) or len(rows) > MAX_CRITERIA:
        raise Refusal("join-criteria")
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or any(not isinstance(value, str) for value in ids):
        raise Refusal("join-id")
    if len(ids) != len(set(ids)):
        raise Refusal("join-duplicate-id")
    return ids
