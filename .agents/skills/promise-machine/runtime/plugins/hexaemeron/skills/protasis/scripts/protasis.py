#!/usr/bin/env python3
"""Protasis runbook and study schema checks.

A runbook step that omits a field is not caught by reading, because the phase
that reads it carefully is the one that has already started building. The same
holds for a study missing one of its twelve items. This settles the part a
parser can.

Runbook mode (the default):

  P000  a path that cannot be read as a runbook
  P001  a step missing a required field
  P002  a step whose exit states no command
  P003  a document in which no step was found
  P004  more steps than the check will track, so the tail went unchecked
  P005  an appended runbook amendment is not one final dated four-field block
        carrying at least one complete replacement field
  P006  an optional version-relations declaration is malformed, ambiguous, or
        contradicted by a concrete version token elsewhere in the runbook

Study mode (`--study`):

  S000  a path that cannot be read as a study
  S001  one of the twelve study items is missing
  S002  an answer to items 8 through 12 is neither content nor a stated
        none carrying its reason
  S003  a document in which no study item was found
  S004  a study item number appears more than once, so no verdict on its
        answer is earned
  S005  item 5 carries no risk-register block naming a concern
  S006  a register line that does not split into the three pipe-separated
        fields the shape fixes
  S007  a register field that is malformed: an id that is not kebab-case
        or already used, or an empty boundary or check

Exit 0 clean, 1 findings, 2 bad invocation.

Deliberate exceptions state a reason: `<!-- protasis: allow <why> -->` on the
step heading line or the line above it.

What this does not do. It reads whether a field is present, not whether the
answer is any good: a Disciplines line naming the wrong gates and an Exit whose
command proves nothing both pass. Judging an answer is the reviewer's job, and
the study's non-goals say so. P002 is the closest to a judgement, and it is
still only presence: a step carrying no code at all cannot have named a command,
while a step carrying one may still have named the wrong one. P006 settles the
closed declaration shape and lexical target identity; it neither opens the
declared ledgers nor decides whether the relation is suitable or which version
it will resolve to. The study mode
holds the same line: S002 refuses silence and a bare none, never a weak reason,
and items 1 through 7 are checked for presence only, because "none, and here is
why" is a complete answer solely for items 8 through 12. The register codes
read shape alone -- the block exists, each line splits into three fields, the
id is kebab-case and unused, no field is empty -- and never whether a boundary
or a check is worth looking at, which stays with the reviewer.

The trust boundary is the argument list. Paths are read as given, so the caller
decides what is opened; the checker refuses anything that is not a regular file,
caps what it will read, and caps how many steps it will track. It starts no
subprocess and opens no socket.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# "## Step 3: Ship the checker". The number is required: a heading reading
# "## Steps" is prose about steps, not a step.
STEP = re.compile(r"^##\s+Step\s+(?P<n>\d+)\s*:\s*(?P<title>.*?)\s*$")
FIELD = re.compile(r"^\*\*(?P<name>[A-Za-z]+)\.\*\*")
HEADING = re.compile(r"^#{1,2}\s+")
# Backtick or tilde, three or more, per CommonMark. The marker is captured so a
# fence is closed only by its own kind: ``` inside a ~~~ block is content.
FENCE = re.compile(r"^ {0,3}(?P<mark>`{3,}|~{3,})")
INLINE_CODE = re.compile(r"`[^`\n]+`")
ALLOW = re.compile(r"<!--\s*protasis:\s*allow\s+(?P<reason>\S[^>]*?)\s*-->")
AMENDMENT = re.compile(r"^###\s+Amendment\s+--\s+(?P<date>\d{4}-\d{2}-\d{2})\s*$")
AMENDMENT_LIKE = re.compile(r"^###\s+Amendment(?:\s+--(?:\s+.*)?)?\s*$")
AMENDMENT_FIELDS = ("What changed", "Why", "Steps touched", "Still holding")
AMENDMENT_FIELD = re.compile(
    r"^\*\*(?P<name>What changed|Why|Steps touched|Still holding)\.\*\*"
    r"(?:\s*(?P<value>.*))?$"
)
ANY_AMENDMENT_FIELD = re.compile(r"^\*\*[^*\n]+\.\*\*(?:\s*.*)?$")
RUNBOOK_FIELD_NAMES = ("Goal", "Entry", "Exit", "Files", "Tests", "Disciplines")
COMPLETE_REPLACEMENT = re.compile(
    r"Complete replacement (?P<field>Goal|Entry|Exit|Files|Tests|Disciplines):"
    r"\s*(?P<value>.*?)"
    r"(?=(?:\s+Complete replacement "
    r"(?:Goal|Entry|Exit|Files|Tests|Disciplines):)|\Z)"
)

REQUIRED = ("Goal", "Entry", "Exit", "Files", "Tests", "Disciplines")

# "## 2. Prior art". The number is required and the dot ends it: a heading
# reading "## Sources" is prose, not an item.
ITEM = re.compile(r"^##\s+(?P<n>\d{1,3})\.\s*(?P<title>.*?)\s*$")

# The twelve items the study contract mandates, by number.
ITEMS = {
    1: "Problem statement",
    2: "Prior art",
    3: "Constraints and non-goals",
    4: "Design options",
    5: "Risk register seed",
    6: "Glossary seeds",
    7: "Sources",
    8: "Signals, and the questions behind them",
    9: "Boundaries, per capability",
    10: "The budget, or its absence",
    11: "The fail-closed posture",
    12: "Decisions and their homes",
}

# The five whose answer may be a stated none, and only with its reason.
ANSWERED = range(8, 13)

# The shape protasis-v3.4.0 fixed for item 5: a fenced block with this info
# string, one concern per line as three pipe-separated fields, the id
# kebab-case and stable within the study. Field order and separator are the
# interface audit rounds cite, so the parse follows the contract exactly.
REGISTER_ITEM = 5
REGISTER_INFO = "risk-register"
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# An answer that asserts none and stops. Punctuation-stripped, lowercased,
# whole-answer matches only: "none, and here is why: ..." carries more words
# and passes, while judging whether the reason is any good stays the
# reviewer's job.
BARE = {"none", "n/a", "na", "no", "tbd"}

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# A runbook is a document somebody handed over. Bound both axes.
MAX_BYTES = 2 * 1024 * 1024
MAX_STEPS = 500
MAX_VERSION_RELATIONS = 32
VERSION_RELATIONS_INFO = "version-relations"
VERSION_RELATION = "next-generation-after-integration-base"


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def as_dict(self) -> dict:
        return {"path": str(self.path), "line": self.line, "code": self.code,
                "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _scan(lines: list[str]):
    """Yield (1-indexed number, line, inside_a_fence) for every line.

    One tracker for all three scans. Keeping three copies is what let the tail
    scan ship without fence tracking at all, so a runbook quoting a step heading
    truncated itself.
    """
    open_mark: str | None = None
    open_length: int | None = None
    for number, line in enumerate(lines, start=1):
        match = FENCE.match(line)
        if match:
            sequence = match.group("mark")
            mark = sequence[0]
            if open_mark is None:
                open_mark = mark
                open_length = len(sequence)
                yield number, line, True
                continue
            if (
                mark == open_mark
                and len(sequence) >= open_length
                and not line[match.end():].strip()
            ):
                open_mark = None
                open_length = None
            yield number, line, True
            continue
        yield number, line, open_mark is not None


def suppressed(lines: list[str], line: int) -> bool:
    """An allow comment on the heading line or the line above it."""
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


def _read(path: Path) -> list[str] | None:
    """The document, or None when it is not one we will read."""
    try:
        if not path.is_file():
            return None
        if path.stat().st_size > MAX_BYTES:
            return None
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def _spans(lines: list[str]) -> tuple[list[tuple[int, str, int, int]], int]:
    """Steps as (heading line, title, body start, body end), and how many were
    left untracked by the cap.

    A step owns the lines after its heading up to the next step heading or the
    next heading of the same or higher level, so a trailing section does not
    get read as part of the last step.

    The cap bounds the work, and the count of what it dropped is returned rather
    than discarded: a check that stops early and still reports clean is the
    false confidence this whole module exists to avoid.
    """
    starts: list[tuple[int, str]] = []
    dropped = 0
    first_amendment = None
    for index, line, in_fence in _scan(lines):
        if in_fence:
            continue
        if AMENDMENT_LIKE.fullmatch(line):
            first_amendment = index
            break
        match = STEP.match(line)
        if match:
            if len(starts) >= MAX_STEPS:
                dropped += 1
                continue
            starts.append((index, match.group("title")))

    spans = []
    for position, (line_number, title) in enumerate(starts):
        if position + 1 < len(starts):
            end = starts[position + 1][0] - 1
        else:
            end = (first_amendment - 1) if first_amendment else len(lines)
            # Any heading of this level ends the last step, a further step
            # heading included. Excluding step headings here let a step dropped
            # by the cap donate its fields to the last tracked step, which then
            # passed while missing its own. Fenced lines are not headings, or a
            # runbook quoting a step heading would truncate itself.
            for index, line, in_fence in _scan(lines):
                if index <= line_number or index > end or in_fence:
                    continue
                if HEADING.match(line) or AMENDMENT_LIKE.fullmatch(line):
                    end = index - 1
                    break
        spans.append((line_number, title, line_number + 1, end))
    return spans, dropped


def _field_span(body: list[str], name: str) -> list[str]:
    """The lines belonging to one field: its own line up to the next field.

    Scoped deliberately. Searching the whole step for a command means any other
    field carrying backticks answers for the exit, and `**Files.** `a.py`` is
    almost universal, so a step-wide search makes P002 unfirable in practice.
    """
    start = None
    for index, line in enumerate(body):
        match = FIELD.match(line)
        if match and match.group("name") == name:
            start = index
            break
    if start is None:
        return []

    span = [body[start]]
    for index, line, in_fence in _scan(body[start + 1:]):
        if not in_fence and FIELD.match(line):
            break
        span.append(line)
    return span


def _has_command(lines: list[str]) -> bool:
    """A command is a fenced block or an inline code span."""
    for line in lines:
        if FENCE.match(line) or INLINE_CODE.search(line):
            return True
    return False


def _replacement_fields(value: str) -> tuple[list[str], str | None]:
    """Return full replacement field names, or the exact structural fault."""
    matches = list(COMPLETE_REPLACEMENT.finditer(value))
    if not matches:
        return [], (
            "What changed must restate at least one complete runbook field as "
            "'Complete replacement Exit: <full value>'"
        )
    cursor = 0
    fields = []
    for match in matches:
        if value[cursor:match.start()].strip():
            return [], "What changed must contain only complete replacement clauses"
        field = match.group("field")
        if not match.group("value").strip():
            return [], f"complete replacement {field} must not be empty"
        if field == "Exit" and not _has_command(match.group("value").splitlines()):
            return [], "complete replacement Exit must name a command"
        fields.append(field)
        cursor = match.end()
    if value[cursor:].strip():
        return [], "What changed must contain only complete replacement clauses"
    duplicates = sorted({field for field in fields if fields.count(field) > 1})
    if duplicates:
        return [], f"complete replacement fields repeat: {duplicates}"
    return fields, None


def _version_relation_blocks(
    lines: list[str],
) -> list[tuple[int, int, int, bool, bool]]:
    """Return candidate relation blocks without accepting nested decoys.

    Each tuple is opening line, first body line, last body line, exact info
    string, and closed. A near declaration such as ``version-relations extra``
    is retained so the checker refuses it instead of treating it as legacy
    prose with no declaration. Two candidates are enough: the second proves
    the closed one-block contract failed, so retaining further bodies would
    turn an already bounded refusal into attacker-chosen memory use.
    """
    blocks: list[tuple[int, int, int, bool, bool]] = []
    open_mark: str | None = None
    open_length: int | None = None
    relation_open: tuple[int, bool] | None = None
    for number, line in enumerate(lines, start=1):
        match = FENCE.match(line)
        if match is None:
            continue
        sequence = match.group("mark")
        mark = sequence[0]
        tail = line[match.end():].strip()
        if open_mark is None:
            open_mark = mark
            open_length = len(sequence)
            words = tail.split()
            relation_open = (
                (number, tail == VERSION_RELATIONS_INFO)
                if words and words[0] == VERSION_RELATIONS_INFO
                else None
            )
            continue
        if (
            mark == open_mark
            and len(sequence) >= open_length
            and not tail
        ):
            if relation_open is not None:
                opening, exact_info = relation_open
                if len(blocks) < 2:
                    blocks.append((
                        opening, opening + 1, number - 1, exact_info, True,
                    ))
            open_mark = None
            open_length = None
            relation_open = None
    if relation_open is not None:
        opening, exact_info = relation_open
        if len(blocks) < 2:
            blocks.append((opening, opening + 1, len(lines), exact_info, False))
    return blocks


def _contains_nonprinting_character(value: str) -> bool:
    """Cover C0, C1, and Unicode format controls at the text boundary."""
    return any(not character.isprintable() for character in value)


def _safe_relation_path(value: str, skill_id: str) -> str | None:
    """Return a lexical path fault without opening a runbook-controlled path."""
    parts = value.split("/")
    if (
        not value
        or value.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:", value)
        or "\\" in value
        or any(part in ("", ".", "..") for part in parts)
        or _contains_nonprinting_character(value)
    ):
        return "relation path is not a safe repository-relative path"
    if len(parts) < 2 or parts[-1] != "EVOLUTION.md":
        return "relation path must name an EVOLUTION.md file"
    if parts[-2] != skill_id:
        return "relation target id must match the skill directory before EVOLUTION.md"
    return None


def _version_relation_findings(path: Path, lines: list[str]) -> list[Finding]:
    """Check the optional closed version relation declaration."""
    blocks = _version_relation_blocks(lines)
    if not blocks:
        return []

    findings: list[Finding] = []
    if len(blocks) > 1:
        findings.append(Finding(
            path, blocks[1][0], "P006",
            "runbook carries more than one version-relations block",
        ))

    first_step = next((
        number for number, line, in_fence in _scan(lines)
        if not in_fence and STEP.match(line)
    ), None)
    declared: set[str] = set()
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    inside_relation_block = bytearray(len(lines) + 1)

    for opening, body_start, body_end, exact_info, closed in blocks[:1]:
        last_block_line = body_end + (1 if closed else 0)
        for number in range(opening, last_block_line + 1):
            inside_relation_block[number] = 1
        if not exact_info:
            findings.append(Finding(
                path, opening, "P006",
                "version-relations fence must carry only that exact info string",
            ))
        if not closed:
            findings.append(Finding(
                path, opening, "P006", "version-relations block is not closed",
            ))
            continue
        if first_step is not None and opening >= first_step:
            findings.append(Finding(
                path, opening, "P006",
                "version-relations block must occur before Step 1",
            ))

        rows = lines[body_start - 1:body_end]
        if not rows:
            findings.append(Finding(
                path, opening, "P006", "version-relations block carries no row",
            ))
            continue
        if len(rows) > MAX_VERSION_RELATIONS:
            findings.append(Finding(
                path, opening, "P006",
                f"version-relations block exceeds {MAX_VERSION_RELATIONS} rows",
            ))
        for offset, text in enumerate(rows[:MAX_VERSION_RELATIONS], start=body_start):
            if not text.strip():
                findings.append(Finding(
                    path, offset, "P006", "version-relations row must not be blank",
                ))
                continue
            if _contains_nonprinting_character(text):
                findings.append(Finding(
                    path, offset, "P006",
                    "version-relations row contains a control character",
                ))
                continue
            fields = [field.strip() for field in text.split("|")]
            if len(fields) != 3 or any(not field for field in fields):
                findings.append(Finding(
                    path, offset, "P006",
                    "version-relations row must carry three non-empty fields "
                    "(skill id | EVOLUTION.md path | relation)",
                ))
                continue
            skill_id, ledger_path, relation = fields
            if not KEBAB.fullmatch(skill_id):
                findings.append(Finding(
                    path, offset, "P006",
                    "version relation target id is not kebab-case",
                ))
                continue
            if skill_id in seen_ids:
                findings.append(Finding(
                    path, offset, "P006",
                    "version relation target id appears more than once",
                ))
            else:
                seen_ids.add(skill_id)
            if ledger_path in seen_paths:
                findings.append(Finding(
                    path, offset, "P006",
                    "version relation path appears more than once",
                ))
            else:
                seen_paths.add(ledger_path)
            path_fault = _safe_relation_path(ledger_path, skill_id)
            if path_fault:
                findings.append(Finding(path, offset, "P006", path_fault))
            if relation != VERSION_RELATION:
                findings.append(Finding(
                    path, offset, "P006",
                    f"unknown version relation; expected {VERSION_RELATION!r}",
                ))
            if path_fault is None and relation == VERSION_RELATION:
                declared.add(skill_id)

    for skill_id in sorted(declared):
        concrete = re.compile(
            rf"(?<![A-Za-z0-9-]){re.escape(skill_id)}-v"
            rf"\d+\.\d+\.\d+(?![A-Za-z0-9-])"
        )
        for number, line in enumerate(lines, start=1):
            if not inside_relation_block[number] and concrete.search(line):
                findings.append(Finding(
                    path, number, "P006",
                    "declared target has a concrete version token outside the "
                    "version-relations block",
                ))
                break
    return findings


def _runbook_amendment_findings(path: Path, lines: list[str]) -> list[Finding]:
    """Check every real appended amendment without reading fenced decoys."""
    headings = [
        (number, line)
        for number, line, in_fence in _scan(lines)
        if not in_fence and AMENDMENT_LIKE.fullmatch(line)
    ]
    findings: list[Finding] = []
    for position, (line_number, heading_line) in enumerate(headings):
        heading = AMENDMENT.fullmatch(heading_line)
        if heading is None:
            findings.append(Finding(
                path, line_number, "P005", "runbook amendment heading has an invalid date"
            ))
        else:
            try:
                datetime.date.fromisoformat(heading.group("date"))
            except ValueError:
                findings.append(Finding(
                    path, line_number, "P005",
                    "runbook amendment date is not a calendar date",
                ))
        end = headings[position + 1][0] - 1 if position + 1 < len(headings) else len(lines)
        body = lines[line_number:end]
        fields = []
        for relative, line, in_fence in _scan(body):
            offset = line_number + relative
            if in_fence:
                continue
            if re.match(r"^#{1,3}\s+", line):
                findings.append(Finding(
                    path, offset, "P005", "runbook amendment must remain a final section"
                ))
            match = AMENDMENT_FIELD.fullmatch(line)
            if match:
                fields.append((offset, match.group("name"), match.group("value") or ""))
            elif ANY_AMENDMENT_FIELD.fullmatch(line):
                findings.append(Finding(
                    path, offset, "P005", f"unexpected runbook amendment field: {line}"
                ))

        names = [field[1] for field in fields]
        if names != list(AMENDMENT_FIELDS):
            findings.append(Finding(
                path, line_number, "P005",
                "runbook amendment fields must occur once in order: "
                + ", ".join(AMENDMENT_FIELDS),
            ))
            continue

        values = {}
        for index, (field_line, name, first) in enumerate(fields):
            next_line = fields[index + 1][0] if index + 1 < len(fields) else end + 1
            continuation = lines[field_line:next_line - 1]
            value = " ".join((first + "\n" + "\n".join(continuation)).split())
            if not value:
                findings.append(Finding(
                    path, field_line, "P005", f"runbook amendment field {name!r} is empty"
                ))
            values[name] = value
        _, replacement_fault = _replacement_fields(values.get("What changed", ""))
        if replacement_fault:
            findings.append(Finding(path, fields[0][0], "P005", replacement_fault))
    return findings


def check(path: Path) -> list[Finding]:
    lines = _read(path)
    if lines is None:
        return [Finding(path, 1, "P000", "cannot be read as a runbook")]

    findings: list[Finding] = _version_relation_findings(path, lines)
    findings.extend(_runbook_amendment_findings(path, lines))
    spans, dropped = _spans(lines)
    if not spans:
        findings.append(Finding(
            path, 1, "P003", "no step found; expected a '## Step N: title' heading",
        ))
        return findings
    if dropped:
        findings.append(Finding(
            path, 1, "P004",
            f"{dropped} step(s) past the {MAX_STEPS}-step cap were not checked; "
            f"split the runbook rather than trusting this result"))

    for heading_line, title, body_start, body_end in spans:
        if suppressed(lines, heading_line):
            continue
        body = lines[body_start - 1:body_end]
        present = {match.group("name") for match in
                   (FIELD.match(line) for line in body) if match}
        for name in REQUIRED:
            if name not in present:
                findings.append(Finding(
                    path, heading_line, "P001",
                    f"step {title!r} is missing **{name}.**"))
        if "Exit" in present and not _has_command(_field_span(body, "Exit")):
            findings.append(Finding(
                path, heading_line, "P002",
                f"step {title!r} states an exit but names no command"))
    return findings


def _item_spans(lines: list[str]) -> dict[int, list[tuple[int, int, int]]]:
    """Item spans keyed by number: (heading line, body start, body end).

    A list per number, because a duplicate is a fact to report rather than a
    copy to silently prefer. An item owns the lines after its heading up to
    the next level-two heading; fenced lines are content, so a study quoting
    an item heading does not gain or truncate an item.
    """
    headings: list[tuple[int, int | None]] = []
    for index, line, in_fence in _scan(lines):
        if in_fence or not HEADING.match(line):
            continue
        match = ITEM.match(line)
        number = int(match.group("n")) if match else None
        headings.append((index, number if number in ITEMS else None))

    spans: dict[int, list[tuple[int, int, int]]] = {}
    for position, (line_number, number) in enumerate(headings):
        if number is None:
            continue
        if position + 1 < len(headings):
            end = headings[position + 1][0] - 1
        else:
            end = len(lines)
        spans.setdefault(number, []).append((line_number, line_number + 1, end))
    return spans


def _register_lines(body: list[str], offset: int) -> list[tuple[int, str]]:
    """The non-blank lines inside item 5's risk-register blocks.

    Fence state starts closed, which is sound because an item span begins at
    a heading the fence-aware scan accepted. A block opened with another info
    string is content, so a register block quoted inside a markdown example
    earns no verdict -- the false clean every recorded protasis finding
    shares.
    """
    collected: list[tuple[int, str]] = []
    open_mark: str | None = None
    collecting = False
    for number, line in enumerate(body, start=offset):
        match = FENCE.match(line)
        if match:
            mark = match.group("mark")
            if open_mark is None:
                open_mark = mark[0]
                info = line.strip()[len(mark):].strip()
                collecting = info == REGISTER_INFO
            elif mark[0] == open_mark:
                open_mark = None
                collecting = False
            continue
        if collecting and line.strip():
            collected.append((number, line.strip()))
    return collected


def _register_findings(path: Path, lines: list[str], heading_line: int,
                       body_start: int, body_end: int) -> list[Finding]:
    body = lines[body_start - 1:body_end]
    entries = _register_lines(body, body_start)
    if not entries:
        return [Finding(
            path, heading_line, "S005",
            f"item {REGISTER_ITEM} ({ITEMS[REGISTER_ITEM]}) carries no "
            f"risk-register block naming a concern")]

    findings: list[Finding] = []
    seen: set[str] = set()
    for number, text in entries:
        fields = [part.strip() for part in text.split("|")]
        if len(fields) != 3:
            findings.append(Finding(
                path, number, "S006",
                f"register line carries {len(fields)} field(s), not the three "
                f"the shape fixes (id | boundary | what the audit loop checks)"))
            continue
        concern_id, boundary, check_text = fields
        if not KEBAB.match(concern_id):
            findings.append(Finding(
                path, number, "S007",
                f"register id {concern_id!r} is not kebab-case"))
        elif concern_id in seen:
            findings.append(Finding(
                path, number, "S007",
                f"register id {concern_id!r} appears more than once, so a "
                f"round's citation is ambiguous"))
        else:
            seen.add(concern_id)
        if not boundary:
            findings.append(Finding(
                path, number, "S007", "register line carries an empty boundary field"))
        if not check_text:
            findings.append(Finding(
                path, number, "S007", "register line carries an empty check field"))
    return findings


def _answer(lines: list[str], start: int, end: int) -> str:
    """The answer's text with comments and whitespace stripped."""
    body = "\n".join(lines[start - 1:end])
    body = COMMENT.sub(" ", body)
    return " ".join(body.split())


def check_study(path: Path) -> list[Finding]:
    lines = _read(path)
    if lines is None:
        return [Finding(path, 1, "S000", "cannot be read as a study")]

    spans = _item_spans(lines)
    if not spans:
        return [Finding(path, 1, "S003",
                        "no study item found; expected '## N. Title' headings, 1 to 12")]

    findings: list[Finding] = []
    for number in sorted(ITEMS):
        name = ITEMS[number]
        occurrences = spans.get(number, [])
        if not occurrences:
            findings.append(Finding(
                path, 1, "S001", f"study item {number} ({name}) is missing"))
            continue
        if len(occurrences) > 1:
            first = occurrences[0][0]
            findings.append(Finding(
                path, first, "S004",
                f"study item {number} ({name}) appears {len(occurrences)} times, "
                f"so no verdict on its answer is earned"))
            continue
        heading_line, body_start, body_end = occurrences[0]
        if suppressed(lines, heading_line):
            continue
        if number == REGISTER_ITEM:
            findings.extend(_register_findings(
                path, lines, heading_line, body_start, body_end))
        if number not in ANSWERED:
            continue
        answer = _answer(lines, body_start, body_end)
        stripped = answer.strip(" .,!:;-").lower()
        if not answer or stripped in BARE:
            findings.append(Finding(
                path, heading_line, "S002",
                f"item {number} ({name}) carries neither content nor a stated "
                f"none with its reason"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Protasis runbook and study schema checks.")
    parser.add_argument("paths", nargs="+", help="documents to check")
    parser.add_argument("--study", action="store_true",
                        help="check studies against the twelve-item contract "
                             "instead of runbooks against the step schema")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    checker = check_study if args.study else check
    findings: list[Finding] = []
    for name in args.paths:
        findings.extend(checker(Path(name)))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
