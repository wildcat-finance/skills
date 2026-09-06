#!/usr/bin/env python3
"""Hypomnema record lint.

A record that points at something absent is worse than no record: it reads as
though the reason exists and was checked. This settles the part a parser can.

  H001  a relative link that resolves to nothing
  H002  a superseding pointer naming a record that does not exist
  H003  an alert naming a runbook file that is not there
  H004  a decision record missing one of the template's five sections
  H005  a decision record whose status is not dated
  H006  a source comment citing a record that does not exist
  H007  an alert runbook missing one of its three required answers
  H008  an explicit study design bridge that does not bind one selected design
        to one established numbered ADR, numberless draft, or skill-ledger home
  H009  a stable decision identity is malformed, misplaced, or duplicated
  H010  a stable decision reference names no draft or final record

Exit 0 clean, 1 findings, 2 bad invocation.

Source files are walked beside the markdown: `#` comments in Python and
shell, `//` comments and `/* */` blocks in Solidity, JavaScript and
TypeScript. A marker counts only at the start of a line's stripped text
or preceded by whitespace, so a marker inside a string literal or a
URL's double slash earns no scan; that boundary is deliberate and a
reference the rule cannot see stays unchecked. References found in
comment text are resolved against the numeric and stable-slug indexes the
markdown pass builds from record file names. In source files the pragma is the bare
`hypomnema: allow <why>` after a comment marker, on the finding's line
or the one above it.

A decision record is a markdown file named `ADR-<number>...` inside a
directory named `decisions`. The shape codes hold it to the template the
SKILL states: a Status whose first line is a status word, a comma and an
ISO date, and the five sections Status, Context, Decision, Alternatives
and Consequences. Directory walks skip `fixtures` and `specimens`
directories relative to the walked root, because a specimen documenting a
fault is not a record and a preserved source carries its origin's links;
naming either path directly still reads it.

In Markdown, a `runbook:` keyword inside an inline code span is a quoted
specimen rather than a live pointer, so H003 passes over it. The keyword's
own position decides that: `runbook: ` followed by a backticked path is
still read and still resolved. Spans are paired per line, an unmatched
backtick run stays literal text, and a backtick escaped by an odd number of
backslashes opens nothing. A relative link inside a span is read the same
way, so H001 passes over it.

The Markdown keyword starts at the beginning of a line or after a character
other than a word character or hyphen. Word suffixes such as `myrunbook:` and
hyphenated tokens such as `sub-runbook:` are not pointers; list items and
dotted forms such as `annotations.runbook:` remain recognised.

An alert runbook is a Markdown file below a directory named `runbooks`.
It carries non-empty `## What fired`, `## First check` and `## Who to wake`
sections outside fenced examples. A reasoned pragma suppresses H007 only on
the file's first line or on the relevant heading.

Deliberate exceptions state a reason: `<!-- hypomnema: allow <why> -->`,
for a shape finding on the record's first line or the status heading.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

LINK = re.compile(r"(?<!!)\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
SUPERSEDE = re.compile(r"superseded\s+by\s+(?P<ref>ADR-\d+)", re.IGNORECASE)
ADR_NUMBER = re.compile(r"ADR-(\d+)", re.IGNORECASE)
# A bounded keyword and a path, not a word suffix or whatever follows a colon.
RUNBOOK = re.compile(r"(?<![\w-])runbook:\s*[`\"']?(?P<path>[\w./-]+\.md|[\w./-]+/[\w./-]+)[`\"']?",
                     re.IGNORECASE)
# A quoted specimen is a mention, not a promise that the target exists. The
# lexicon pass next door already draws this line for a banned term inside
# quotation marks; the append-only audit ledger is where a record lint needs it.
BACKTICK_RUN = re.compile(r"`+")
YAML_RUNBOOK = re.compile(r"^runbook\s*:\s*(?P<path>.+?)\s*$", re.DOTALL)
YAML_SUFFIXES = {".yaml", ".yml"}
MAX_YAML_BYTES = 1 << 20
BLOCK_SCALAR = re.compile(
    r"^(?:[^:#][^:]*:\s*|-\s+)[|>](?:[+-]?\d?|\d[+-]?)\s*$")
ALLOW = re.compile(r"<!--\s*hypomnema:\s*allow\s+(?P<reason>\S[^>]*?)\s*-->")
SKIP_SCHEME = ("http", "https", "mailto", "tel", "ftp")
# The record template the SKILL states, held mechanically since the first
# four records stated their status in three shapes within a day.
RECORD_NAME = re.compile(r"^ADR-\d+.*\.md$", re.IGNORECASE)
FINAL_NAME = re.compile(
    r"^ADR-(?P<number>[0-9]{3})-(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
STABLE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_SLUG_BYTES = 96
STABLE_PREFIX = "adr/"
STABLE_TRAILING = ".,;:!?)]}"
SECTION = re.compile(r"^##\s+(?P<name>\S.*?)\s*$")
SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")
RUNBOOK_SECTIONS = ("What fired", "First check", "Who to wake")
DATED = re.compile(r"^[A-Za-z]+, \d{4}-\d{2}-\d{2}")
# One marker family per suffix; the // family also reads /* */ blocks.
COMMENT_MARKERS = {".py": "#", ".sh": "#", ".sol": "//", ".js": "//",
                   ".ts": "//", ".tsx": "//", ".jsx": "//"}
SOURCE_ALLOW = re.compile(r"hypomnema:\s*allow\s+\S")
# The bundled Pashov suite is vendored, keeps no ledger, and documents files it
# generates in the target repository rather than files that live here.
VENDORED = {"fizz", "x-ray", "solidity-auditor"}

DESIGN_BRIDGE_SCHEMA = "hypomnema-design-bridge/v1"
DESIGN_EVIDENCE_SCHEMA = "protasis-design-evidence/v1"
MAX_STUDY_BYTES = 2 * 1024 * 1024
MAX_DESIGN_BYTES = 2 * 1024 * 1024
MAX_RECORD_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_PORTABLE_PATH_BYTES = 4096
MAX_CANDIDATES = 4
MAX_CRITERIA = 32
DESIGN_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DESIGN_DIGEST = re.compile(r"^[0-9a-f]{64}$")
DESIGN_FENCE = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
)
DESIGN_TOP_KEYS = frozenset(
    {"schema", "candidates", "criteria", "results", "selection"}
)
DESIGN_CANDIDATE_KEYS = frozenset({"id", "summary"})
DESIGN_SELECTION_KEYS = frozenset({"candidate", "rule", "policy_ref"})
DESIGN_SELECTION_RULES = frozenset(
    {"unique-frontier", "exact-tie-simplicity", "user-policy"}
)


class DuplicateKey(ValueError):
    """A JSON object repeated a key and is not one closed value."""


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKey("duplicate object key")
        value[key] = item
    return value


def _stat_identity(value: os.stat_result) -> tuple:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _portable_relative(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    parts = value.split("/")
    return not (
        len(encoded) > MAX_PORTABLE_PATH_BYTES
        or value.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:", value)
        or "\\" in value
        or any(part in ("", ".", "..") for part in parts)
        or any(not character.isprintable() for character in value)
    )


def _relative_input(root: Path, supplied: Path | str) -> Path | None:
    """Bind one caller path lexically below the already resolved root."""
    candidate = Path(supplied)
    try:
        if candidate.is_absolute():
            # Canonicalise only the containing directory. The final component
            # stays unopened until the descriptor-relative no-follow read.
            lexical = candidate.parent.resolve(strict=True) / candidate.name
            relative = lexical.relative_to(root)
        else:
            relative = candidate
    except (OSError, RuntimeError, ValueError):
        return None
    value = relative.as_posix()
    return relative if _portable_relative(value) else None


def _read_repo_file(
    root: Path,
    supplied: Path | str,
    maximum: int,
) -> tuple[bytes | None, Path | None, str | None]:
    """Read one bounded stable ordinary file without following a path symlink."""
    relative = _relative_input(root, supplied)
    if relative is None:
        return None, None, "path is not a portable repository-relative path"

    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptors: list[int] = []
    file_descriptor: int | None = None
    try:
        current = os.open(root, directory_flags)
        descriptors.append(current)
        parts = relative.parts
        for part in parts[:-1]:
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        name = parts[-1]
        before = os.stat(name, dir_fd=current, follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode):
            return None, relative, "is not an ordinary non-symlink file"
        if before.st_size > maximum:
            return None, relative, f"exceeds the {maximum}-byte input limit"
        file_descriptor = os.open(name, file_flags, dir_fd=current)
        opened = os.fstat(file_descriptor)
        chunks: list[bytes] = []
        total = 0
        while total <= maximum:
            chunk = os.read(file_descriptor, min(64 * 1024, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        after = os.fstat(file_descriptor)
        named = os.stat(name, dir_fd=current, follow_symlinks=False)
        identities = {
            _stat_identity(before),
            _stat_identity(opened),
            _stat_identity(after),
            _stat_identity(named),
        }
        data = b"".join(chunks)
        if len(data) > maximum:
            return None, relative, f"exceeds the {maximum}-byte input limit"
        if len(identities) != 1 or len(data) != before.st_size:
            return None, relative, "changed while being read"
        return data, relative, None
    except (OSError, ValueError):
        return None, relative, "is unavailable or not an ordinary non-symlink file"
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _json_depth_within_limit(data: bytes) -> bool:
    depth = 0
    quoted = False
    escaped = False
    for byte in data:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                quoted = False
            continue
        if byte == 0x22:
            quoted = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return False
        elif byte in (0x5D, 0x7D) and depth:
            depth -= 1
    return True


def _bounded_design_text(value, maximum=4096) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return len(encoded) <= maximum and all(character.isprintable() for character in value)


def _selected_design(data: bytes) -> tuple[str | None, str | None]:
    """Return the selected candidate from one closed selection envelope."""
    if not _json_depth_within_limit(data):
        return None, "design evidence is not one bounded strict JSON object"
    try:
        raw = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number {token}")
            ),
        )
    except (
        DuplicateKey, MemoryError, RecursionError, UnicodeDecodeError, ValueError
    ):
        return None, "design evidence is not one bounded strict JSON object"
    if not isinstance(raw, dict) or set(raw) != DESIGN_TOP_KEYS:
        return None, "design evidence has an unsupported closed field set"
    if raw.get("schema") != DESIGN_EVIDENCE_SCHEMA:
        return None, f"design evidence is not {DESIGN_EVIDENCE_SCHEMA}"

    candidates = raw.get("candidates")
    if not isinstance(candidates, list) or not 2 <= len(candidates) <= MAX_CANDIDATES:
        return None, "design evidence has an invalid candidate set"
    candidate_ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != DESIGN_CANDIDATE_KEYS:
            return None, "design evidence has a malformed candidate"
        candidate_id = candidate.get("id")
        if (
            not isinstance(candidate_id, str)
            or DESIGN_ID.fullmatch(candidate_id) is None
            or candidate_id in candidate_ids
            or not _bounded_design_text(candidate.get("summary"), 512)
        ):
            return None, "design evidence has a malformed candidate"
        candidate_ids.add(candidate_id)

    # Protasis owns the complete candidate/criterion/result semantics, including
    # pending conformance cells after design-lock. Hypomnema consumes only the
    # already checked selection envelope, so it bounds those arrays without
    # maintaining a partial second copy of Protasis's evolving matrix rules.
    criteria = raw.get("criteria")
    results = raw.get("results")
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= MAX_CRITERIA:
        return None, "design evidence has an invalid bounded criterion envelope"
    if not isinstance(results, list) or len(results) > MAX_CANDIDATES * MAX_CRITERIA:
        return None, "design evidence has an invalid bounded result envelope"

    selection = raw.get("selection")
    if not isinstance(selection, dict) or set(selection) != DESIGN_SELECTION_KEYS:
        return None, "design evidence has a malformed selection"
    selected = selection.get("candidate")
    rule = selection.get("rule")
    policy_ref = selection.get("policy_ref")
    if selected not in candidate_ids or rule not in DESIGN_SELECTION_RULES:
        return None, "design evidence has no supported selected candidate"
    if (rule == "user-policy") != (policy_ref is not None):
        return None, "design evidence has a malformed selection policy"
    if policy_ref is not None and not _bounded_design_text(policy_ref):
        return None, "design evidence has a malformed selection policy"
    return selected, None


def _design_bridge_block(lines: list[str]) -> tuple[dict | None, int, str | None]:
    """Read exactly one closed, ordered three-row block outside examples."""
    active: tuple[str, int, bool, int] | None = None
    rows: list[tuple[int, str]] = []
    blocks: list[tuple[int, list[tuple[int, str]], bool]] = []
    for number, line in enumerate(lines, start=1):
        match = DESIGN_FENCE.match(line)
        if active is None:
            if match is None:
                continue
            marker = match.group("marker")
            info = match.group("info").strip()
            target = info == "design-bridge" or info.startswith("design-bridge ")
            active = (marker[0], len(marker), target, number)
            rows = []
            if target and info != "design-bridge":
                rows.append((number, "<malformed-header>"))
            continue

        marker_character, marker_length, target, opened = active
        if match is not None:
            marker = match.group("marker")
            closes = (
                marker[0] == marker_character
                and len(marker) >= marker_length
                and not match.group("info").strip()
            )
            if closes:
                if target:
                    blocks.append((opened, rows, True))
                active = None
                rows = []
                continue
        if target:
            rows.append((number, line))

    if active is not None and active[2]:
        return None, active[3], "design bridge block is not closed"
    if not blocks:
        return None, 1, "study has no design bridge block"
    if len(blocks) != 1:
        return None, blocks[1][0], "study declares more than one design bridge home"
    opened, rows, _closed = blocks[0]
    if len(rows) != 3:
        return None, opened, "design bridge must have exactly three rows"
    parsed: dict[str, str] = {}
    expected = ("schema", "decision", "record")
    for position, (number, row) in enumerate(rows):
        parts = row.split("|")
        if len(parts) != 2:
            return None, number, "design bridge rows must have exactly two fields"
        key, value = (part.strip() for part in parts)
        if key != expected[position]:
            return None, number, "design bridge rows are not ordered schema, decision, record"
        if not value or key in parsed:
            return None, number, "design bridge has an empty or repeated row"
        parsed[key] = value
    if parsed["schema"] != DESIGN_BRIDGE_SCHEMA:
        return None, rows[0][0], f"design bridge schema is not {DESIGN_BRIDGE_SCHEMA}"
    if DESIGN_ID.fullmatch(parsed["decision"]) is None:
        return None, rows[1][0], "design bridge decision is not a bounded candidate id"
    if not _portable_relative(parsed["record"]):
        return None, rows[2][0], "design bridge record is not a portable repository-relative path"
    parsed["record_line"] = str(rows[2][0])
    return parsed, opened, None


def _governed_skill_name(data: bytes) -> str | None:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return None
    if not lines or lines[0] != "---":
        return None
    names = []
    for line in lines[1:]:
        if line == "---":
            break
        match = re.fullmatch(r"name:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*", line)
        if match:
            names.append(match.group(1))
    return names[0] if len(names) == 1 else None


def check_design_bridge(
    study_path: Path | str,
    design_evidence_path: Path | str,
    repo_root: Path | str,
) -> list[Finding]:
    """Bind one checked study selection to one standing record as H008."""
    supplied_root = Path(repo_root)
    try:
        if supplied_root.is_symlink():
            raise OSError
        root = supplied_root.resolve(strict=True)
        if not root.is_dir():
            raise OSError
    except (OSError, RuntimeError):
        return [Finding(supplied_root, 1, "H008", "repository root is unavailable or unsafe")]

    study, study_relative, error = _read_repo_file(root, study_path, MAX_STUDY_BYTES)
    if study is None:
        return [Finding(Path(study_path), 1, "H008", f"study {error}")]
    try:
        lines = study.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return [Finding(root / study_relative, 1, "H008", "study is not UTF-8 text")]
    bridge, line, error = _design_bridge_block(lines)
    if bridge is None:
        return [Finding(root / study_relative, line, "H008", error)]

    evidence, evidence_relative, error = _read_repo_file(
        root, design_evidence_path, MAX_DESIGN_BYTES
    )
    if evidence is None:
        return [Finding(Path(design_evidence_path), 1, "H008", f"design evidence {error}")]
    selected, error = _selected_design(evidence)
    if selected is None:
        return [Finding(root / evidence_relative, 1, "H008", error)]
    if bridge["decision"] != selected:
        return [Finding(
            root / study_relative,
            line,
            "H008",
            f"design bridge decision `{bridge['decision']}` does not match selected candidate `{selected}`",
        )]

    record = bridge["record"]
    record_data, record_relative, error = _read_repo_file(root, record, MAX_RECORD_BYTES)
    record_line = int(bridge["record_line"])
    if record_data is None:
        return [Finding(
            root / study_relative,
            record_line,
            "H008",
            f"record `{record}` {error}",
        )]

    is_adr = (
        RECORD_NAME.fullmatch(record_relative.name) is not None
        and "decisions" in record_relative.parts[:-1]
    )
    is_draft = (
        len(record_relative.parts) == 4
        and record_relative.parts[:3] == ("docs", "decisions", "drafts")
        and record_relative.suffix == ".md"
    )
    if is_draft:
        try:
            record_lines = record_data.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            return [Finding(
                root / study_relative,
                record_line,
                "H008",
                f"draft record `{record}` is not UTF-8 text",
            )]
        draft_findings = (
            _stable_record_findings(record_relative, record_lines)
            + _record_findings(record_relative, record_lines)
        )
        if draft_findings:
            return [Finding(
                root / study_relative,
                record_line,
                "H008",
                f"draft record `{record}` is malformed: "
                f"{draft_findings[0].message}",
            )]
    is_ledger = record_relative.name == "EVOLUTION.md"
    if is_ledger:
        skill_relative = record_relative.parent / "SKILL.md"
        skill_data, _skill_relative, skill_error = _read_repo_file(
            root, skill_relative, MAX_RECORD_BYTES
        )
        governed = (
            skill_data is not None
            and "plugins" == record_relative.parts[0]
            and "skills" in record_relative.parts[1:-1]
            and _governed_skill_name(skill_data) == record_relative.parent.name
        )
        if not governed:
            return [Finding(
                root / study_relative,
                record_line,
                "H008",
                f"record `{record}` is not a governed skill ledger"
                + (f": {skill_error}" if skill_error else ""),
            )]
    if not is_adr and not is_draft and not is_ledger:
        return [Finding(
            root / study_relative,
            record_line,
            "H008",
            f"record `{record}` is outside an established ADR, numberless draft, or governed-skill-ledger home",
        )]
    return []


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def as_dict(self) -> dict:
        return {"path": str(self.path), "line": self.line, "code": self.code,
                "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def suppressed(lines: list[str], line: int) -> bool:
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


def _external(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme) and parsed.scheme in SKIP_SCHEME


def _yaml_quote_starts(line: str, index: int) -> bool:
    """Return whether a quote occupies a supported quoted-scalar start."""
    prefix = line[:index]
    stripped = prefix.strip()
    separated = bool(prefix) and prefix[-1] in " \t"
    return not stripped or (separated and (
        stripped == "-" or prefix.rstrip().endswith(":")))


def _yaml_plain_scalar_indent(content: str) -> int | None:
    """Return the key indent for a supported inline plain scalar."""
    indent = len(content) - len(content.lstrip(" "))
    stripped = content[indent:]
    sequence = stripped.startswith("- ")
    if sequence:
        stripped = stripped[2:]
    match = re.match(r"^[^:#][^:]*:[ \t]+(?P<value>\S.*)$", stripped)
    if not match or match.group("value")[0] in "'\"|>[{&*!%@`":
        return None
    return indent + 2 if sequence else indent


def _yaml_plain_continuation(line: str) -> str:
    """Return folded plain-scalar text before a separated YAML comment."""
    for index, character in enumerate(line):
        if character == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[:index].strip()
    return line.strip()


def _yaml_target(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1].strip()
    return value


def _code_spans(line: str) -> list[tuple[int, int]]:
    """Half-open offsets of every inline code span on one line.

    CommonMark pairs a backtick run with the next run of the same length and
    leaves an unmatched run as literal text, so an odd backtick cannot open a
    span that swallows the rest of a line. Pairing is one pass keyed by run
    length rather than a search for a partner: this plugin's own adversarial
    sweep uses 60k-character lines and 30k backticks, and a pair search over
    those is quadratic in the runs that never match.

    A run whose first backtick carries an odd number of preceding backslashes
    starts one character later, because that backtick is literal text. Without
    it an escaped pair would open a span and hide a live pointer, which is the
    one direction this check must not fail in.
    """
    pending: dict[int, int] = {}
    spans: list[tuple[int, int]] = []
    for match in BACKTICK_RUN.finditer(line):
        start, end = match.start(), match.end()
        # Counted backwards from the run rather than over a prefix slice: a
        # slice per run is linear in the line and turns 30k runs quadratic
        # again, which is the cost this pairing exists to avoid.
        backslashes = 0
        cursor = start - 1
        while cursor >= 0 and line[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2:
            start += 1
            if start == end:
                continue
        length = end - start
        opened = pending.pop(length, None)
        if opened is None:
            pending[length] = start
        else:
            spans.append((opened, end))
    return spans


def _within(spans, index: int) -> bool:
    """Whether one offset falls inside any span."""
    return any(start <= index < end for start, end in spans)


def _relative_markdown(value: str) -> bool:
    return bool(value and value.lower().endswith(".md")
                and not value.startswith(("/", "\\"))
                and not _external(value))


def _strip_yaml_comment(
        line: str, quote: str | None = None) -> tuple[str, str | None]:
    """Remove a YAML comment while carrying a quoted scalar."""
    active = quote
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if active == '"':
            if character == "\\":
                escaped = True
            elif character == '"':
                active = None
            continue
        if active == "'":
            if character == "'" and index + 1 < len(line) \
                    and line[index + 1] == "'":
                escaped = True
            elif character == "'":
                active = None
            continue
        if character in "'\"" and _yaml_quote_starts(line, index):
            active = character
        elif (character == "#"
              and (index == 0 or line[index - 1] in " \t")):
            return line[:index], None
    return line, active


def _yaml_lines(lines: list[str]) -> list[tuple[int, str, bool]]:
    """Return logical YAML lines, folding supported plain runbook values."""
    out: list[tuple[int, str, bool]] = []
    scalar_indent: int | None = None
    plain_indent: int | None = None
    plain_out_index: int | None = None
    plain_candidate = False
    plain_breaks = 0
    quote: str | None = None
    for number, raw in enumerate(lines, start=1):
        if scalar_indent is not None:
            if not raw.strip():
                continue
            raw_indent = len(raw) - len(raw.lstrip(" "))
            if raw_indent > scalar_indent:
                continue
            scalar_indent = None
        if plain_indent is not None:
            if not raw.strip():
                if plain_out_index is not None:
                    plain_breaks += 1
                continue
            if not raw.lstrip().startswith("#"):
                raw_indent = len(raw) - len(raw.lstrip(" "))
                if raw_indent > plain_indent:
                    if plain_out_index is not None:
                        continuation = _yaml_plain_continuation(raw)
                        if continuation:
                            first = out[plain_out_index]
                            separator = "\n" * plain_breaks if plain_breaks else " "
                            logical = f"{first[1]}{separator}{continuation}"
                            match = YAML_RUNBOOK.match(logical)
                            spaced_candidate = bool(match and _relative_markdown(
                                _yaml_target(match.group("path")).replace("\n", " ")))
                            out[plain_out_index] = (
                                first[0], logical,
                                first[2] or plain_candidate or spaced_candidate)
                            plain_breaks = 0
                    continue
            plain_indent = None
            plain_out_index = None
            plain_candidate = False
            plain_breaks = 0
        started_in_quote = quote is not None
        content, quote = _strip_yaml_comment(raw, quote)
        if started_in_quote:
            continue
        content = content.rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        stripped = content[indent:]
        if BLOCK_SCALAR.match(stripped):
            scalar_indent = indent
            continue
        plain_indent = _yaml_plain_scalar_indent(content)
        out.append((number, stripped, False))
        match = YAML_RUNBOOK.match(stripped)
        if plain_indent is not None and match:
            plain_out_index = len(out) - 1
            plain_candidate = _relative_markdown(
                _yaml_target(match.group("path")))
    return out


def _yaml_findings(path: Path, lines: list[str]) -> list[Finding]:
    """Resolve generic block-YAML runbook keys without classifying alerts."""
    findings: list[Finding] = []
    for number, content, folded_candidate in _yaml_lines(lines):
        match = YAML_RUNBOOK.match(content)
        if not match:
            continue
        target = _yaml_target(match.group("path"))
        if not _relative_markdown(target) and not folded_candidate:
            continue
        if not (path.parent / target).exists():
            findings.append(Finding(
                path, number, "H003",
                f"runbook `{target}` resolves to nothing"))
    return findings


def _record_findings(path: Path, lines: list[str]) -> list[Finding]:
    """The template shape: a dated status and the five sections.

    Section headings are read outside fences only, so a record quoting the
    template in an example neither gains nor loses a section.
    """
    headings: dict[str, int] = {}
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = SECTION.match(line)
        if match:
            # A pragma on the heading is a suppression, not part of the name.
            name = ALLOW.sub("", match.group("name")).strip()
            if name in SECTIONS:
                headings.setdefault(name, number)

    findings = [Finding(path, 1, "H004",
                        f"decision record is missing its `## {name}` section")
                for name in SECTIONS if name not in headings]

    status_line = headings.get("Status")
    if status_line is not None:
        first = ""
        for line in lines[status_line:]:
            if SECTION.match(line) or line.startswith("#"):
                break
            if line.strip():
                first = line.strip()
                break
        if not DATED.match(first):
            findings.append(Finding(
                path, status_line, "H005",
                "status is not dated; the shape is a status word, a comma "
                "and an ISO date"))
    return findings


def _runbook_findings(path: Path, lines: list[str]) -> list[Finding]:
    """Require the three operator answers outside fenced examples."""
    headings: dict[str, int] = {}
    content: set[str] = set()
    current: str | None = None
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = SECTION.match(line)
        if match:
            name = ALLOW.sub("", match.group("name")).strip()
            current = name if name in RUNBOOK_SECTIONS else None
            if current is not None:
                headings.setdefault(current, number)
            continue
        if line.startswith("#"):
            current = None
            continue
        if current is not None and line.strip() and not ALLOW.fullmatch(line.strip()):
            content.add(current)

    findings: list[Finding] = []
    for name in RUNBOOK_SECTIONS:
        line = headings.get(name, 1)
        if name not in headings:
            message = f"alert runbook is missing its `## {name}` answer"
        elif name not in content:
            message = f"alert runbook has an empty `## {name}` answer"
        else:
            continue
        finding = Finding(path, line, "H007", message)
        first_line_allows = bool(lines and ALLOW.search(lines[0]))
        heading_allows = bool(
            name in headings and ALLOW.search(lines[headings[name] - 1]))
        if not first_line_allows and not heading_allows:
            findings.append(finding)
    return findings


def _marker_index(text: str, marker: str) -> int:
    """Where a comment marker starts, or -1.

    A marker counts at the start of the stripped text or preceded by
    whitespace, so a marker inside a string literal or a URL's double slash
    earns no scan.
    """
    if text.lstrip().startswith(marker):
        return text.index(marker)
    start = 0
    while True:
        found = text.find(marker, start)
        if found == -1:
            return -1
        if found > 0 and text[found - 1] in " \t":
            return found
        start = found + len(marker)


def _comment_segments(lines: list[str], marker: str):
    """Yield (1-indexed line number, comment text) for every comment span."""
    in_block = False
    for number, line in enumerate(lines, start=1):
        rest = line
        while rest:
            if in_block:
                end = rest.find("*/")
                if end == -1:
                    yield number, rest
                    rest = ""
                else:
                    yield number, rest[:end]
                    in_block = False
                    rest = rest[end + 2:]
                continue
            line_at = _marker_index(rest, marker)
            block_at = _marker_index(rest, "/*") if marker == "//" else -1
            if block_at != -1 and (line_at == -1 or block_at < line_at):
                in_block = True
                rest = rest[block_at + 2:]
                continue
            if line_at != -1:
                yield number, rest[line_at + len(marker):]
            rest = ""


def _stable_references(
        path: Path,
        number: int,
        line: str,
        adr_slugs: set[str] | None) -> list[Finding]:
    """Read stable references, including identifiers quoted in code spans."""
    findings: list[Finding] = []
    cursor = 0
    while True:
        start = line.find(STABLE_PREFIX, cursor)
        if start < 0:
            break
        cursor = start + len(STABLE_PREFIX)
        if start and (line[start - 1].isalnum() or line[start - 1] in "_-/"):
            continue
        # This exact token documents the grammar; it is not a live identity.
        if line.startswith("<slug>", cursor):
            cursor += len("<slug>")
            continue
        end = cursor
        while (
                end < len(line)
                and not line[end].isspace()
                and line[end] not in "`\"'"):
            end += 1
        token = line[cursor:end].rstrip(STABLE_TRAILING)
        cursor = max(end, cursor + 1)
        try:
            encoded = token.encode("ascii")
        except UnicodeEncodeError:
            encoded = b""
        if (
                not token
                or len(encoded) > MAX_SLUG_BYTES
                or STABLE_SLUG.fullmatch(token) is None):
            findings.append(Finding(
                path, number, "H008",
                "stable decision reference has an invalid slug"))
        elif adr_slugs is not None and token not in adr_slugs:
            findings.append(Finding(
                path, number, "H009",
                f"stable decision reference `adr/{token}` has no record"))
    return findings


def _source_findings(
        path: Path,
        adr_numbers: set[str] | None,
        adr_slugs: set[str] | None) -> list[Finding]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "H000", f"unreadable: {err}")]

    lines = text.splitlines()
    marker = COMMENT_MARKERS[path.suffix]
    findings: list[Finding] = []
    for number, comment in _comment_segments(lines, marker):
        for match in ADR_NUMBER.finditer(comment):
            reference = f"ADR-{match.group(1)}"
            if adr_numbers is not None and reference not in adr_numbers:
                findings.append(Finding(
                    path, number, "H006",
                    f"comment cites `{reference}`, which does not exist"))
        findings.extend(_stable_references(path, number, comment, adr_slugs))

    def allowed(line: int) -> bool:
        for number in (line, line - 1):
            if 1 <= number <= len(lines) and SOURCE_ALLOW.search(lines[number - 1]):
                return True
        return False

    return [f for f in findings if not allowed(f.line)]


def _stable_record_findings(path: Path, lines: list[str]) -> list[Finding]:
    """Hold prospective draft/final placement and first headings together."""
    positions = [index for index, part in enumerate(path.parts)
                 if part == "decisions"]
    if not positions:
        return []
    tail = path.parts[positions[-1] + 1:]
    findings: list[Finding] = []
    first = lines[0] if lines else ""
    if len(tail) == 2 and tail[0] == "drafts" and path.suffix == ".md":
        slug = path.stem
        if (
                len(slug.encode("utf-8")) > MAX_SLUG_BYTES
                or STABLE_SLUG.fullmatch(slug) is None):
            findings.append(Finding(
                path, 1, "H008",
                "draft path has an invalid stable decision slug"))
        if not first.startswith("# Decision: ") or first == "# Decision: ":
            findings.append(Finding(
                path, 1, "H008",
                "draft first heading is not `# Decision: <title>`"))
    elif len(tail) == 1 and path.suffix == ".md":
        match = FINAL_NAME.fullmatch(path.name)
        if path.name.startswith("ADR-"):
            if match is not None:
                slug = match.group("slug")
                if len(slug.encode("ascii")) > MAX_SLUG_BYTES:
                    findings.append(Finding(
                        path, 1, "H008",
                        "final path has an oversized stable decision slug"))
                expected = f"# ADR-{match.group('number')}: "
                if not first.startswith(expected) or first == expected:
                    findings.append(Finding(
                        path, 1, "H008",
                        "final path and first heading disagree"))
        elif first.startswith("# Decision:"):
            findings.append(Finding(
                path, 1, "H008",
                "unnumbered decision is outside `decisions/drafts`"))
    elif tail and tail[0] == "drafts" and path.suffix == ".md":
        findings.append(Finding(
            path, 1, "H008",
            "draft is not directly below `decisions/drafts`"))
    return findings


def check(
        path: Path,
        adr_numbers: set[str] | None = None,
        adr_slugs: set[str] | None = None) -> list[Finding]:
    if path.suffix in COMMENT_MARKERS:
        return _source_findings(path, adr_numbers, adr_slugs)
    if path.suffix in YAML_SUFFIXES:
        try:
            with path.open("rb") as source:
                raw = source.read(MAX_YAML_BYTES + 1)
            if len(raw) > MAX_YAML_BYTES:
                return [Finding(path, 1, "H000", "unreadable: YAML exceeds 1 MiB")]
            lines = raw.decode("utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as err:
            return [Finding(path, 1, "H000", f"unreadable: {err}")]
        return _yaml_findings(path, lines)
    if path.suffix != ".md":
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "H000", f"unreadable: {err}")]

    lines = text.splitlines()
    findings: list[Finding] = []
    findings.extend(_stable_record_findings(path, lines))
    if RECORD_NAME.match(path.name) and "decisions" in path.parts:
        findings.extend(_record_findings(path, lines))
    if "runbooks" in path.parts[:-1]:
        findings.extend(_runbook_findings(path, lines))
    in_fence = False

    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        links = list(LINK.finditer(line))
        # A link inside an inline code span is a quoted specimen, the reading
        # H003 gives a `runbook:` keyword there. Only a line carrying a link
        # pays for the span scan.
        link_spans = _code_spans(line) if links else ()
        for match in links:
            if _within(link_spans, match.start()):
                continue
            target = match.group("target")
            if target.startswith("#") or _external(target):
                continue
            relative = unquote(target.split("#", 1)[0])
            if not relative:
                continue
            if not (path.parent / relative).exists():
                findings.append(Finding(path, number, "H001",
                                        f"link `{target}` resolves to nothing"))

        for match in SUPERSEDE.finditer(line):
            reference = match.group("ref").upper()
            if adr_numbers is not None and reference not in adr_numbers:
                findings.append(Finding(path, number, "H002",
                                        f"superseded by `{reference}`, which does not exist"))

        pointers = list(RUNBOOK.finditer(line))
        # Only a line carrying a pointer pays for the span scan, which keeps the
        # cost off the other 1,375 files in a tree walk.
        spans = _code_spans(line) if pointers else ()
        for match in pointers:
            if _within(spans, match.start()):
                continue
            target = match.group("path").strip("`\"'")
            if not _external(target) and not (path.parent / target).exists():
                findings.append(Finding(path, number, "H003",
                                        f"alert names runbook `{target}`, which is not there"))

        findings.extend(_stable_references(path, number, line, adr_slugs))

    return [f for f in findings
            if f.code == "H007" or not suppressed(lines, f.line)]


def adr_index(paths: list[Path]) -> set[str]:
    found = set()
    for path in paths:
        match = ADR_NUMBER.search(path.name)
        if match:
            found.add(f"ADR-{match.group(1)}")
    return found


def stable_index(paths: list[Path]) -> tuple[set[str], list[Finding]]:
    """Index one prospective draft or final path per stable slug."""
    indexed: dict[str, list[Path]] = {}
    findings: list[Finding] = []
    seen_paths: set[Path] = set()
    for path in paths:
        if path in seen_paths or path.suffix != ".md":
            continue
        seen_paths.add(path)
        positions = [index for index, part in enumerate(path.parts)
                     if part == "decisions"]
        if not positions:
            continue
        tail = path.parts[positions[-1] + 1:]
        slug: str | None = None
        if len(tail) == 2 and tail[0] == "drafts":
            candidate = path.stem
            if (
                    len(candidate.encode("utf-8")) > MAX_SLUG_BYTES
                    or STABLE_SLUG.fullmatch(candidate) is None):
                continue
            slug = candidate
        elif len(tail) == 1 and path.name.startswith("ADR-"):
            match = FINAL_NAME.fullmatch(path.name)
            if match is None:
                # Pre-existing numbered records remain legacy numeric
                # identities when their suffix predates the stable grammar.
                continue
            candidate = match.group("slug")
            if len(candidate.encode("ascii")) > MAX_SLUG_BYTES:
                continue
            slug = candidate
        if slug is not None:
            indexed.setdefault(slug, []).append(path)
    for slug, records in indexed.items():
        # Two numbered records that share a slug are legacy numeric
        # identities the repository already carries; the allocator tolerates
        # them while they are inherited unchanged and refuses a draft that
        # takes the slug, so only a draft makes the duplication a finding.
        if len(records) > 1 and any(
                path.parent.name == "drafts" for path in records):
            for path in records:
                findings.append(Finding(
                    path, 1, "H008",
                    f"stable decision identity `adr/{slug}` is duplicated"))
    return set(indexed), findings


def walk(paths: list[str], include_vendored: bool = False) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        root = Path(raw)
        if root.is_dir():
            suffixes = (".md", *COMMENT_MARKERS, *sorted(YAML_SUFFIXES))
            found = (child for suffix in suffixes
                     for child in root.rglob(f"*{suffix}"))
            for child in sorted(set(found)):
                if not child.is_file():
                    continue
                if ".git" in child.parts:
                    continue
                if not include_vendored and VENDORED & set(child.parts):
                    continue
                # A specimen documenting a fault is not a record, and neither
                # is a preserved source: its links belong to wherever it came
                # from, and repointing one changes the bytes something else
                # pins. Relative to the walked root, so naming the path still
                # reads it.
                skipped = {"fixtures", "specimens"}
                if skipped & set(child.relative_to(root).parts[:-1]):
                    continue
                out.append(child)
        else:
            out.append(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hypomnema record lint.")
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--include-vendored", action="store_true",
                        help="also check the bundled third-party skills")
    parser.add_argument("--study", help="check one study's explicit design bridge")
    parser.add_argument(
        "--design-evidence",
        help="the checked protasis-design-evidence/v1 record for --study",
    )
    parser.add_argument(
        "--repo-root",
        help="the repository root containing --study and --design-evidence",
    )
    args = parser.parse_args(argv)

    study_mode = any((args.study, args.design_evidence, args.repo_root))
    if study_mode:
        if not all((args.study, args.design_evidence, args.repo_root)):
            parser.error(
                "--study, --design-evidence and --repo-root must be supplied together"
            )
        if args.paths != ["."] or args.include_vendored:
            parser.error("study mode does not accept walk paths or --include-vendored")
        findings = check_design_bridge(
            args.study,
            args.design_evidence,
            args.repo_root,
        )
    else:
        files = walk(args.paths or ["."], include_vendored=args.include_vendored)
        index = adr_index(files)
        slug_index, identity_findings = stable_index(files)
        findings = list(identity_findings)
        for path in files:
            findings.extend(check(path, index, slug_index))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
