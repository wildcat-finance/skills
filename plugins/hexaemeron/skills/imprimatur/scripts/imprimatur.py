#!/usr/bin/env python3
"""Imprimatur-lexicon lint.

Three passes over a draft:

  hard        banned outright; any hit is a defect
  gated       terms of art; permitted against a concrete referent, flagged as ornament
  structural  formulae that survive any vocabulary ban

Exit 0 clean, 1 defects at or above the fail threshold, 2 bad invocation.

Absorbs the lexicons of slopbeth deslop_lint.py and slopgent comms_lint.py
(ehmo/slopkit, MIT). See NOTICE.md.
"""

from __future__ import annotations

import argparse
import ast
from bisect import bisect_right
import errno
import io
import json
import math
import os
import re
import stat
import sys
import tokenize as py_tokenize
from pathlib import Path

LEXICON_DIR = Path(__file__).resolve().parent.parent / "lexicon"
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from lib.typescript_lexer import comment_spans as typescript_comment_spans  # noqa: E402

SEVERITY_WEIGHT = {"critical": 5, "high": 3, "medium": 2, "low": 1}
DEFAULT_SEVERITY = {"hard": "high", "gated": "medium", "structural": "medium"}
SOURCE_SUFFIXES = frozenset({".sol", ".py", ".ts", ".tsx"})
MAX_SOURCE_BYTES = 1 << 20
TYPESCRIPT_LINE_TERMINATORS = frozenset("\r\n\u2028\u2029")
SOLIDITY_LINE_BREAKS = frozenset("\n\v\f\r\x85\u2028\u2029")
SOLIDITY_INVALID_LINE_BREAKS = frozenset("\x85\u2028\u2029")
PYTHON_LINE_TERMINATORS = frozenset("\r\n")

# Evidence that licenses a gated term.
RE_BACKTICK = re.compile(r"`[^`\n]+`")
RE_PATH = re.compile(r"\b[\w./-]+\.(?:sol|py|ts|tsx|js|md|json|yaml|yml|toml|hs|agda|lean|rs|go)\b")
RE_HEX = re.compile(r"\b0x[0-9a-fA-F]{4,}\b")
RE_NUMERAL = re.compile(r"\b\d[\d,._]*\b|\b\d+%")
RE_CAMEL = re.compile(r"\b[a-z]+[A-Z]\w+\b|\b[A-Z][a-z]+[A-Z]\w+\b")
RE_WORD = re.compile(r"[\w''-]+")


def load_lexicons() -> tuple[dict, dict, dict]:
    def rd(name: str) -> dict:
        p = LEXICON_DIR / name
        if not p.exists():
            sys.stderr.write(f"imprimatur: missing lexicon {p}\n")
            raise SystemExit(2)
        return json.loads(p.read_text(encoding="utf-8"))

    return rd("hard.json"), rd("gated.json"), rd("structural.json")


def read_text(path: str | None, *, preserve_newlines: bool = False) -> str:
    if not path or path == "-":
        return sys.stdin.read()
    p = Path(path)
    if preserve_newlines:
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        if not no_follow:
            raise SourceExtractionError(
                1,
                1,
                "source path no-follow open is unavailable",
            )
        flags = os.O_RDONLY
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        flags |= no_follow
        descriptor = -1
        try:
            try:
                descriptor = os.open(p, flags)
            except FileNotFoundError:
                sys.stderr.write(f"imprimatur: no such file {path}\n")
                raise SystemExit(2)
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise SourceExtractionError(
                        1,
                        1,
                        "source path is not a regular file",
                    ) from exc
                raise

            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise SourceExtractionError(
                    1,
                    1,
                    "source path is not a regular file",
                )
            if opened.st_size > MAX_SOURCE_BYTES:
                raise SourceExtractionError(
                    1,
                    1,
                    f"source exceeds {MAX_SOURCE_BYTES}-byte analysis cap",
                )
            source = os.fdopen(descriptor, "rb")
            descriptor = -1
            with source:
                raw = source.read(MAX_SOURCE_BYTES + 1)
            if len(raw) > MAX_SOURCE_BYTES:
                raise SourceExtractionError(
                    1,
                    1,
                    f"source exceeds {MAX_SOURCE_BYTES}-byte analysis cap",
                )
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            prefix = exc.object[: exc.start].decode("utf-8")
            suffix = p.suffix.lower()
            line_terminators = {
                ".py": PYTHON_LINE_TERMINATORS,
                ".sol": SOLIDITY_LINE_BREAKS,
                ".ts": TYPESCRIPT_LINE_TERMINATORS,
                ".tsx": TYPESCRIPT_LINE_TERMINATORS,
            }.get(suffix, frozenset("\n"))
            line, col = line_col(
                prefix,
                len(prefix),
                line_terminators,
            )
            raise SourceExtractionError(
                line,
                col,
                "source is not valid UTF-8",
            ) from exc
        except OSError as exc:
            reason = exc.strerror or type(exc).__name__
            raise SourceExtractionError(
                1,
                1,
                f"source path could not be read: {reason}",
            ) from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
    if not p.exists():
        sys.stderr.write(f"imprimatur: no such file {path}\n")
        raise SystemExit(2)
    with p.open("r", encoding="utf-8", errors="replace") as source:
        return source.read()


def line_col(
    text: str,
    idx: int,
    line_terminators: frozenset[str] = frozenset("\n"),
) -> tuple[int, int]:
    line = 1
    line_start = 0
    cursor = 0
    while cursor < idx:
        char = text[cursor]
        if char in line_terminators:
            if (
                char == "\r"
                and "\n" in line_terminators
                and cursor + 1 < idx
                and text[cursor + 1] == "\n"
            ):
                cursor += 1
            line += 1
            line_start = cursor + 1
        cursor += 1
    return line, idx - line_start + 1


def _coordinate_line_starts(
    text: str,
    line_terminators: frozenset[str],
) -> list[int]:
    starts = [0]
    cursor = 0
    while cursor < len(text):
        char = text[cursor]
        if char in line_terminators:
            if (
                char == "\r"
                and "\n" in line_terminators
                and cursor + 1 < len(text)
                and text[cursor + 1] == "\n"
            ):
                cursor += 1
            starts.append(cursor + 1)
        cursor += 1
    return starts


def _indexed_line_col(starts: list[int], idx: int) -> tuple[int, int]:
    line_index = bisect_right(starts, idx) - 1
    return line_index + 1, idx - starts[line_index] + 1


def excerpt(text: str, start: int, end: int, pad: int = 38) -> str:
    a = max(0, start - pad)
    b = min(len(text), end + pad)
    frag = text[a:b].replace("\n", " ")
    return ("…" if a > 0 else "") + re.sub(r"\s+", " ", frag).strip() + ("…" if b < len(text) else "")


def _quoted_pattern(line_terminators: frozenset[str]) -> re.Pattern[str]:
    excluded = re.escape("".join(sorted(line_terminators)))
    return re.compile(
        rf"`[^`{excluded}]+`"  # inline code
        rf"|\"[^\"{excluded}]{{1,120}}\""  # double quotes
        rf"|\u201c[^\u201d{excluded}]{{1,120}}\u201d"  # smart quotes
        rf"|(?<![\w'])'[^'{excluded}]{{1,120}}'(?![\w])"  # not apostrophes
    )


RE_QUOTED = _quoted_pattern(frozenset("\n"))
SOURCE_QUOTED_PATTERNS = {
    TYPESCRIPT_LINE_TERMINATORS: _quoted_pattern(TYPESCRIPT_LINE_TERMINATORS),
    SOLIDITY_LINE_BREAKS: _quoted_pattern(SOLIDITY_LINE_BREAKS),
    PYTHON_LINE_TERMINATORS: _quoted_pattern(PYTHON_LINE_TERMINATORS),
}


def mask_quoted(
    text: str,
    *,
    line_terminators: frozenset[str] = frozenset("\n"),
) -> str:
    """Blank quoted spans.

    A banned term inside quotation marks is being mentioned, not used. Style
    guides, lexicon docs, and postmortems all need to cite the thing they are
    banning. Masking preserves offsets so line and column stay correct.
    """
    pattern = SOURCE_QUOTED_PATTERNS.get(line_terminators, RE_QUOTED)
    return pattern.sub(lambda m: " " * len(m.group(0)), text)


def strip_code_blocks(text: str) -> str:
    """Blank fenced code and inline code so prose rules do not fire on source."""
    out = re.sub(r"```.*?```", lambda m: " " * len(m.group(0)), text, flags=re.S)
    out = re.sub(r"^(?: {4}|\t).*$", lambda m: " " * len(m.group(0)), out, flags=re.M)
    return out


class SourceExtractionError(ValueError):
    """A supported source file could not be classified without guessing."""

    def __init__(self, line: int, col: int, reason: str) -> None:
        super().__init__(reason)
        self.line = line
        self.col = col
        self.reason = reason


def _line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(match.end() for match in re.finditer(r"\r\n?|\n", text))
    return starts


def _source_line_end(
    text: str,
    start: int,
    line_terminators: frozenset[str],
) -> int:
    cursor = start
    while cursor < len(text) and text[cursor] not in line_terminators:
        cursor += 1
    return cursor


def _position_offset(text: str, starts: list[int], line: int, col: int) -> int:
    if line < 1 or line > len(starts):
        raise SourceExtractionError(max(line, 1), col + 1, "source position is outside the file")
    offset = starts[line - 1] + col
    line_limit = starts[line] if line < len(starts) else len(text)
    if offset < starts[line - 1] or offset > line_limit:
        raise SourceExtractionError(line, col + 1, "source column is outside the line")
    return offset


def _ast_position_offset(
    text: str, starts: list[int], line: int, byte_col: int
) -> int:
    if line < 1 or line > len(starts):
        raise SourceExtractionError(max(line, 1), byte_col + 1, "AST position is outside the file")
    start = starts[line - 1]
    end = _source_line_end(text, start, PYTHON_LINE_TERMINATORS)
    raw = text[start:end].encode("utf-8")
    try:
        prefix = raw[:byte_col].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceExtractionError(line, byte_col + 1, "AST column splits a UTF-8 character") from exc
    if byte_col > len(raw):
        raise SourceExtractionError(line, byte_col + 1, "AST column is outside the line")
    return start + len(prefix)


def _masked_spans(
    text: str,
    spans: list[tuple[int, int]],
    *,
    line_terminators: frozenset[str],
) -> str:
    """Retain selected bytes in place so every source coordinate stays valid."""
    out = [char if char in line_terminators else " " for char in text]
    previous_end = 0
    for start, end in sorted(spans):
        if start < previous_end or end < start or end > len(text):
            line, col = line_col(
                text,
                max(0, min(start, len(text))),
                line_terminators,
            )
            raise SourceExtractionError(line, col, "source spans overlap or escape the file")
        out[start:end] = text[start:end]
        previous_end = end
    return "".join(out)


def _comment_contents(spans: list[tuple[str, int, int]]) -> list[tuple[int, int]]:
    contents: list[tuple[int, int]] = []
    for kind, start, end in spans:
        if kind == "line_comment":
            contents.append((start + 2, end))
        elif kind == "block_comment":
            contents.append((start + 2, end - 2))
    return contents


def _typescript_prose(text: str, *, tsx: bool = False) -> list[tuple[int, int]]:
    spans, errors = typescript_comment_spans(text, tsx=tsx)
    if errors:
        offset, reason = errors[0]
        line, col = line_col(text, offset, TYPESCRIPT_LINE_TERMINATORS)
        raise SourceExtractionError(line, col, reason)
    return _comment_contents(spans)


def _solidity_prose(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(text):
        if text.startswith("//", i):
            end = _source_line_end(text, i + 2, SOLIDITY_LINE_BREAKS)
            spans.append((i + 2, end))
            i = end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                line, col = line_col(text, i, SOLIDITY_LINE_BREAKS)
                raise SourceExtractionError(line, col, "unterminated block comment")
            spans.append((i + 2, end))
            i = end + 2
            continue
        if text[i] in SOLIDITY_INVALID_LINE_BREAKS:
            line, col = line_col(text, i, SOLIDITY_LINE_BREAKS)
            raise SourceExtractionError(
                line,
                col,
                "unsupported Solidity source line break",
            )
        if text[i] in "'\"":
            quote = text[i]
            start = i
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    i += 3 if text.startswith("\\\r\n", i) else 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                if text[i] in SOLIDITY_LINE_BREAKS:
                    line, col = line_col(text, start, SOLIDITY_LINE_BREAKS)
                    raise SourceExtractionError(line, col, "unterminated string")
                i += 1
            else:
                line, col = line_col(text, start, SOLIDITY_LINE_BREAKS)
                raise SourceExtractionError(line, col, "unterminated string")
            continue
        i += 1
    return spans


PY_STRING_OPEN = re.compile(r"(?i)^[rubf]*(?P<quote>'''|\"\"\"|'|\")")


def _python_docstring_nodes(tree: ast.AST) -> list[ast.Constant]:
    owners = [tree]
    owners.extend(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    found: list[ast.Constant] = []
    for owner in owners:
        body = getattr(owner, "body", [])
        if not body or not isinstance(body[0], ast.Expr):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            found.append(value)
    return found


def _python_prose(text: str) -> list[tuple[int, int]]:
    # ``compile(bytes, ...)`` consumes a UTF-8 BOM as an encoding marker, but
    # ``ast.parse(str)`` rejects the decoded U+FEFF.  A leading form feed is
    # same-length parser whitespace without introducing top-level indentation.
    parser_text = "\f" + text[1:] if text.startswith("\ufeff") else text
    try:
        tree = ast.parse(parser_text)
    except SyntaxError as exc:
        raise SourceExtractionError(
            exc.lineno or 1,
            exc.offset or 1,
            f"invalid Python syntax: {exc.msg}",
        ) from exc
    except (MemoryError, RecursionError) as exc:
        raise SourceExtractionError(
            1,
            1,
            "Python parser resource limit exceeded",
        ) from exc
    except UnicodeError as exc:
        raise SourceExtractionError(1, 1, "Python source is not valid Unicode") from exc

    try:
        tokens = list(
            py_tokenize.generate_tokens(
                io.StringIO(parser_text, newline="").readline
            )
        )
    except (MemoryError, RecursionError) as exc:
        raise SourceExtractionError(
            1,
            1,
            "Python parser resource limit exceeded",
        ) from exc
    except (py_tokenize.TokenError, IndentationError, SyntaxError) as exc:
        position = getattr(exc, "args", (None, (1, 0)))
        raw = position[1] if len(position) > 1 and isinstance(position[1], tuple) else (1, 0)
        line, col = raw[:2]
        raise SourceExtractionError(line, col + 1, f"Python tokenization failed: {position[0]}") from exc

    starts = _line_starts(text)
    string_spans: list[tuple[py_tokenize.TokenInfo, int, int]] = []
    prose: list[tuple[int, int]] = []
    for token in tokens:
        if token.type not in {py_tokenize.COMMENT, py_tokenize.STRING}:
            continue
        start = _position_offset(text, starts, token.start[0], token.start[1])
        end = _position_offset(text, starts, token.end[0], token.end[1])
        if token.type == py_tokenize.COMMENT:
            prose.append((start + 1, end))
        elif token.type == py_tokenize.STRING:
            string_spans.append((token, start, end))

    docstrings = sorted(
        _python_docstring_nodes(tree),
        key=lambda node: (node.lineno, node.col_offset),
    )
    string_cursor = 0
    for node in docstrings:
        if node.end_lineno is None or node.end_col_offset is None:
            raise SourceExtractionError(node.lineno, node.col_offset + 1, "docstring has no end position")
        node_start = _ast_position_offset(
            parser_text,
            starts,
            node.lineno,
            node.col_offset,
        )
        node_end = _ast_position_offset(
            parser_text,
            starts,
            node.end_lineno,
            node.end_col_offset,
        )
        while (
            string_cursor < len(string_spans)
            and string_spans[string_cursor][2] <= node_start
        ):
            string_cursor += 1
        probe = string_cursor
        strings = []
        while probe < len(string_spans) and string_spans[probe][1] < node_end:
            token, start, end = string_spans[probe]
            if node_start <= start and end <= node_end:
                strings.append((token, start, end))
            probe += 1
        string_cursor = probe
        if not strings:
            line, col = line_col(text, node_start)
            raise SourceExtractionError(line, col, "docstring source token was not found")
        for token, start, end in strings:
            opening = PY_STRING_OPEN.match(token.string)
            if opening is None:
                line, col = line_col(text, start)
                raise SourceExtractionError(line, col, "docstring delimiter was not recognized")
            quote = opening.group("quote")
            if not token.string.endswith(quote):
                line, col = line_col(text, start)
                raise SourceExtractionError(line, col, "docstring delimiter was not closed")
            if text[start:end] != token.string:
                line, col = line_col(text, start)
                raise SourceExtractionError(line, col, "docstring token does not match source bytes")
            prose.append((start + opening.end(), end - len(quote)))
    return prose


def extract_source_prose(text: str, suffix: str) -> str:
    """Return an offset-preserving prose view for one supported source suffix."""
    suffix = suffix.lower()
    if suffix == ".sol":
        spans = _solidity_prose(text)
        line_terminators = SOLIDITY_LINE_BREAKS
    elif suffix == ".py":
        try:
            spans = _python_prose(text)
        except (MemoryError, RecursionError) as exc:
            raise SourceExtractionError(
                1,
                1,
                "Python parser resource limit exceeded",
            ) from exc
        line_terminators = PYTHON_LINE_TERMINATORS
    elif suffix in {".ts", ".tsx"}:
        spans = _typescript_prose(text, tsx=suffix == ".tsx")
        line_terminators = TYPESCRIPT_LINE_TERMINATORS
    else:
        raise ValueError(f"unsupported source suffix {suffix}")
    return _masked_spans(text, spans, line_terminators=line_terminators)


# --------------------------------------------------------------------------- hard


def scan_hard(
    text: str,
    lex: dict,
    *,
    line_terminators: frozenset[str] = frozenset("\n"),
    line_starts: list[int] | None = None,
) -> list[dict]:
    hits: list[dict] = []
    coordinate_starts = (
        line_starts
        if line_starts is not None
        else _coordinate_line_starts(text, line_terminators)
    )
    lower = text.lower()
    for family, block in lex.items():
        if family.startswith("_") or not isinstance(block, dict):
            continue
        sev = block.get("severity", DEFAULT_SEVERITY["hard"])
        for term in block.get("terms", []):
            t = term.lower()
            pattern = re.compile(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])")
            for m in pattern.finditer(lower):
                ln, cl = _indexed_line_col(coordinate_starts, m.start())
                hits.append(
                    {
                        "pass": "hard",
                        "family": family,
                        "term": term,
                        "severity": sev,
                        "line": ln,
                        "col": cl,
                        "excerpt": excerpt(text, m.start(), m.end()),
                        "note": block.get("note", ""),
                    }
                )
    return hits


# --------------------------------------------------------------------------- gated


RE_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+|\n{2,}")
RE_ANAPHORA = re.compile(r"^\s*(?:it|this|that|these|those|they|which|the same)\b", re.I)

# A term that supplies its own criterion is licensed by the definition, not by
# a nearby identifier: "orthogonal in the sense that neither imports the other".
RE_DEFINITIONAL = re.compile(
    r"^[\s,]*(?:in the sense that|in that|in so far as|insofar as|namely|"
    r"meaning that|meaning|defined as|i\.e\.|specifically|:)\b",
    re.I,
)


def sentence_spans(text: str) -> list[tuple[int, int]]:
    spans, pos = [], 0
    for m in RE_SENT_SPLIT.finditer(text):
        spans.append((pos, m.start()))
        pos = m.end()
    spans.append((pos, len(text)))
    return [(a, b) for a, b in spans if b > a]


def _sentence_index(
    start: int,
    spans: list[tuple[int, int]],
    span_starts: list[int],
) -> int | None:
    index = bisect_right(span_starts, start) - 1
    if index < 0 or not (spans[index][0] <= start < spans[index][1]):
        return None
    return index


def window_tokens(
    text: str,
    start: int,
    end: int,
    n: int,
    spans: list[tuple[int, int]],
    span_starts: list[int] | None = None,
) -> str:
    """Evidence window clamped to the sentence holding the term.

    A referent two sentences away does not license the term. The one allowance
    is anaphora: when the sentence opens with a pronoun or demonstrative it is
    continuing the previous subject, so the previous sentence counts.
    """
    starts = span_starts if span_starts is not None else [a for a, _ in spans]
    idx = _sentence_index(start, spans, starts)
    if idx is None:
        a = max(0, start - n * 8)
        b = min(len(text), end + n * 8)
        return text[a:b]
    a, b = spans[idx]
    win = text[a:b]
    if idx > 0 and RE_ANAPHORA.match(win):
        pa, pb = spans[idx - 1]
        win = text[pa:pb] + " " + win
    return win


def gate_evidence(win: str, allow: list[str], require_numeric: bool) -> tuple[bool, str]:
    if RE_NUMERAL.search(win):
        return True, "numeral"
    if require_numeric:
        return False, "no magnitude stated"
    if RE_BACKTICK.search(win):
        return True, "code identifier"
    if RE_PATH.search(win):
        return True, "file path"
    if RE_HEX.search(win):
        return True, "address"
    low = win.lower()
    for name in allow:
        if re.search(r"(?<![\w-])" + re.escape(name.lower()) + r"(?![\w-])", low):
            return True, f"named system: {name}"
    if RE_CAMEL.search(win):
        return True, "identifier"
    return False, "no concrete referent"


def scan_gated(
    text: str,
    lex: dict,
    evidence_text: str | None = None,
    *,
    line_terminators: frozenset[str] = frozenset("\n"),
    line_starts: list[int] | None = None,
) -> list[dict]:
    hits: list[dict] = []
    coordinate_starts = (
        line_starts
        if line_starts is not None
        else _coordinate_line_starts(text, line_terminators)
    )
    # Term positions come from the masked text; evidence is read from the
    # original, because masking blanks inline code and inline code is exactly
    # what licenses a term of art. Both strings are the same length.
    src = evidence_text if evidence_text is not None else text
    hits_len_guard = len(src) == len(text)
    if not hits_len_guard:
        src = text
    allow = lex.get("_allowlist_named_systems", [])
    abstract = [a.lower() for a in lex.get("_abstract_nouns_that_fail_the_gate", [])]
    default_win = int(lex.get("_default_window", 12))

    spans = sentence_spans(src)
    span_starts = [start for start, _ in spans]
    window_cache: dict[int, str] = {}
    gate_cache: dict[tuple[int, bool], tuple[bool, str]] = {}
    nearest_cache: dict[int, str | None] = {}

    for family, block in lex.items():
        if family.startswith("_") or not isinstance(block, dict):
            continue
        n = int(block.get("window", default_win))
        require_numeric = block.get("requires") == "numeric"
        for term in block.get("terms", []):
            pattern = re.compile(r"(?<![\w-])" + re.escape(term.lower()) + r"(?![\w-])")
            for m in pattern.finditer(text.lower()):
                if RE_DEFINITIONAL.match(src[m.end():m.end() + 40]):
                    continue
                sentence_index = _sentence_index(
                    m.start(),
                    spans,
                    span_starts,
                )
                if sentence_index is None:
                    win = window_tokens(
                        src,
                        m.start(),
                        m.end(),
                        n,
                        spans,
                        span_starts,
                    )
                    ok, reason = gate_evidence(win, allow, require_numeric)
                    nearest = next(
                        (
                            abstract_noun
                            for abstract_noun in abstract
                            if re.search(
                                r"(?<![\w-])"
                                + abstract_noun
                                + r"(?![\w-])",
                                win.lower(),
                            )
                        ),
                        None,
                    )
                else:
                    if sentence_index not in window_cache:
                        window_cache[sentence_index] = window_tokens(
                            src,
                            m.start(),
                            m.end(),
                            n,
                            spans,
                            span_starts,
                        )
                    win = window_cache[sentence_index]
                    gate_key = (sentence_index, require_numeric)
                    if gate_key not in gate_cache:
                        gate_cache[gate_key] = gate_evidence(
                            win,
                            allow,
                            require_numeric,
                        )
                    ok, reason = gate_cache[gate_key]
                    if sentence_index not in nearest_cache:
                        lowered_window = win.lower()
                        nearest_cache[sentence_index] = next(
                            (
                                abstract_noun
                                for abstract_noun in abstract
                                if re.search(
                                    r"(?<![\w-])"
                                    + abstract_noun
                                    + r"(?![\w-])",
                                    lowered_window,
                                )
                            ),
                            None,
                        )
                    nearest = nearest_cache[sentence_index]
                if ok:
                    continue
                confidence = "high" if nearest else "medium"
                ln, cl = _indexed_line_col(coordinate_starts, m.start())
                hits.append(
                    {
                        "pass": "gated",
                        "family": family,
                        "term": term,
                        "severity": "high" if nearest else "medium",
                        "confidence": confidence,
                        "reason": f"{reason}; nearest noun '{nearest}'" if nearest else reason,
                        "line": ln,
                        "col": cl,
                        "excerpt": excerpt(text, m.start(), m.end()),
                        "note": block.get("note", ""),
                    }
                )
    return hits


# --------------------------------------------------------------------------- structural


def scan_structural(
    text: str,
    lex: dict,
    *,
    evidence_text: str | None = None,
    line_terminators: frozenset[str] = frozenset("\n"),
    line_starts: list[int] | None = None,
) -> list[dict]:
    hits: list[dict] = []
    coordinate_starts = (
        line_starts
        if line_starts is not None
        else _coordinate_line_starts(text, line_terminators)
    )
    for name, spec in lex.get("patterns", {}).items():
        flags = re.M if spec.get("case_sensitive") else (re.I | re.M)
        try:
            pattern = re.compile(spec["regex"], flags)
        except re.error as exc:  # pragma: no cover
            sys.stderr.write(f"imprimatur: bad regex {name}: {exc}\n")
            continue
        for m in pattern.finditer(text):
            if (
                spec.get("reject_masked_span")
                and evidence_text is not None
                and len(evidence_text) == len(text)
                and text[m.start():m.end()] != evidence_text[m.start():m.end()]
            ):
                continue
            if m.group(0).strip() in spec.get("allow_exact", []):
                continue
            ln, cl = _indexed_line_col(coordinate_starts, m.start())
            hits.append(
                {
                    "pass": "structural",
                    "family": name,
                    "signal_only": bool(spec.get("signal_only")),
                    "term": m.group(0)[:60].replace("\n", " "),
                    "severity": spec.get("severity", DEFAULT_SEVERITY["structural"]),
                    "line": ln,
                    "col": cl,
                    "excerpt": excerpt(text, m.start(), m.end()),
                    "note": spec.get("note", ""),
                }
            )
    return hits


def cadence_signals(text: str, lex: dict) -> dict:
    cfg = lex.get("cadence", {})
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    lengths = [len(RE_WORD.findall(s)) for s in sentences]

    openers: dict[str, int] = {}
    for s in sentences:
        w = RE_WORD.findall(s.lower())[:2]
        if len(w) == 2:
            k = " ".join(w)
            openers[k] = openers.get(k, 0) + 1
    thresh = int(cfg.get("repeated_opener_threshold", 2))
    repeated = {k: v for k, v in openers.items() if v > thresh}

    if len(lengths) > 1:
        mean = sum(lengths) / len(lengths)
        variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    else:
        mean, variance = (lengths[0] if lengths else 0), 0.0

    run, longest = 1, 1
    for i in range(1, len(lengths)):
        if abs(lengths[i] - lengths[i - 1]) <= 3:
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    return {
        "sentence_count": len(sentences),
        "mean_sentence_length": round(mean, 1),
        "length_variance": round(variance, 1),
        "variance_floor": cfg.get("sentence_length_variance_floor", 25.0),
        "variance_below_floor": variance < float(cfg.get("sentence_length_variance_floor", 25.0))
        and len(lengths) >= 5,
        "longest_similar_run": longest,
        "max_allowed_run": cfg.get("max_consecutive_similar_length", 4),
        "repeated_openers": repeated,
    }


# --------------------------------------------------------------------------- report


def build(text: str, *, hard_only: bool = False, skip_code: bool = True,
          strict: bool = False, source_suffix: str | None = None) -> dict:
    hard_lex, gated_lex, struct_lex = load_lexicons()
    suffix = source_suffix.lower() if source_suffix else None
    if suffix in {".ts", ".tsx"}:
        line_terminators = TYPESCRIPT_LINE_TERMINATORS
    elif suffix == ".sol":
        line_terminators = SOLIDITY_LINE_BREAKS
    elif suffix == ".py":
        line_terminators = PYTHON_LINE_TERMINATORS
    else:
        line_terminators = frozenset("\n")
    if skip_code and suffix in SOURCE_SUFFIXES:
        prose = extract_source_prose(text, suffix)
        evidence_text = prose
    else:
        prose = strip_code_blocks(text) if skip_code else text
        evidence_text = text
    if not strict:
        prose = mask_quoted(prose, line_terminators=line_terminators)

    coordinate_starts = _coordinate_line_starts(prose, line_terminators)
    hits = scan_hard(
        prose,
        hard_lex,
        line_terminators=line_terminators,
        line_starts=coordinate_starts,
    )
    if not hard_only:
        hits += scan_gated(
            prose,
            gated_lex,
            evidence_text=evidence_text,
            line_terminators=line_terminators,
            line_starts=coordinate_starts,
        )
        hits += scan_structural(
            prose,
            struct_lex,
            evidence_text=evidence_text,
            line_terminators=line_terminators,
            line_starts=coordinate_starts,
        )
    hits.sort(key=lambda h: (h["line"], h["col"]))

    # Signal-only patterns have known false positives on legitimate prose. They
    # are listed for a human to look at but do not score, because a rule that
    # cannot separate a rhetorical triad from a three-item list should not be
    # allowed to fail a build.
    signals = [h for h in hits if h.get("signal_only")]
    hits = [h for h in hits if not h.get("signal_only")]

    weight = sum(SEVERITY_WEIGHT.get(h["severity"], 2) for h in hits)
    words = len(RE_WORD.findall(prose)) or 1
    density = round(weight / words * 1000, 2)
    # Exponential decay: a single defect in a short passage should not read as
    # catastrophic, while sustained density still floors the score.
    score = round(100 * math.exp(-density / 70.0), 1)

    by_pass: dict[str, int] = {}
    by_family: dict[str, int] = {}
    for h in hits:
        by_pass[h["pass"]] = by_pass.get(h["pass"], 0) + 1
        key = f"{h['pass']}:{h['family']}"
        by_family[key] = by_family.get(key, 0) + 1

    out = {
        "score": score,
        "defects": len(hits),
        "weighted": weight,
        "per_1000_words": density,
        "word_count": words,
        "by_pass": by_pass,
        "by_family": dict(sorted(by_family.items(), key=lambda kv: -kv[1])),
        "hits": hits,
        "signals": signals,
    }
    if not hard_only:
        out["cadence"] = cadence_signals(prose, struct_lex)
    return out


def render_text(r: dict, verbose: bool) -> str:
    lines = []
    lines.append(f"score {r['score']}/100   defects {r['defects']}   weighted {r['weighted']}   /1k words {r['per_1000_words']}")
    if not r["hits"] and not r.get("signals"):
        lines.append("clean")
        return "\n".join(lines)
    if not r["hits"]:
        lines.append("no defects")
    lines.append("")
    for h in r["hits"]:
        tag = h["pass"][0].upper()
        loc = f"{h['line']}:{h['col']}"
        extra = f"  [{h.get('reason')}]" if h.get("reason") else ""
        lines.append(f"  {tag} {loc:>9}  {h['severity']:<8} {h['family']}: {h['term']!r}{extra}")
        if verbose:
            lines.append(f"              {h['excerpt']}")
            if h.get("note"):
                lines.append(f"              -> {h['note']}")
    if r.get("signals"):
        lines.append("")
        lines.append("signals (known false positives; look, do not obey):")
        for h in r["signals"][:12]:
            lines.append(f"  ~ {h['line']}:{h['col']}  {h['family']}: {h['term']!r}")
        if len(r["signals"]) > 12:
            lines.append(f"  ~ ... and {len(r['signals']) - 12} more")
    cad = r.get("cadence")
    if cad:
        flags = []
        if cad["variance_below_floor"]:
            flags.append(f"low length variance ({cad['length_variance']} < {cad['variance_floor']})")
        if cad["longest_similar_run"] > cad["max_allowed_run"]:
            flags.append(f"{cad['longest_similar_run']} consecutive similar-length sentences")
        if cad["repeated_openers"]:
            flags.append("repeated openers: " + ", ".join(f"{k}x{v}" for k, v in cad["repeated_openers"].items()))
        if flags:
            lines.append("")
            lines.append("cadence signals (judgement, not defects):")
            for f in flags:
                lines.append(f"  ~ {f}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files to lint; stdin when omitted")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--fail-under", type=float, default=None, help="exit 1 when score below this")
    ap.add_argument("--max-defects", type=int, default=None, help="exit 1 when defect count above this")
    ap.add_argument("--hard-only", action="store_true", help="hard pass only; fast path for hooks")
    ap.add_argument(
        "--include-code",
        action="store_true",
        help="scan all input instead of extracting source prose or blanking fenced code",
    )
    ap.add_argument("--strict", action="store_true",
                    help="count quoted mentions as uses (default: mentions are exempt)")
    ap.add_argument("-v", "--verbose", action="store_true", help="show excerpt and rationale")
    args = ap.parse_args()

    targets = args.paths or [None]
    reports, failed = {}, False

    for t in targets:
        label = t or "<stdin>"
        suffix = Path(t).suffix.lower() if t else None
        try:
            text = read_text(
                t,
                preserve_newlines=(
                    not args.include_code and suffix in SOURCE_SUFFIXES
                ),
            )
            r = build(
                text,
                hard_only=args.hard_only,
                skip_code=not args.include_code,
                strict=args.strict,
                source_suffix=suffix,
            )
        except SourceExtractionError as exc:
            sys.stderr.write(
                f"imprimatur: {label}:{exc.line}:{exc.col}: "
                f"source extraction failed: {exc.reason}\n"
            )
            return 2
        reports[label] = r
        if args.fail_under is not None and r["score"] < args.fail_under:
            failed = True
        if args.max_defects is not None and r["defects"] > args.max_defects:
            failed = True

    if args.format == "json":
        print(json.dumps(reports if len(reports) > 1 else next(iter(reports.values())), indent=2))
    else:
        for label, r in reports.items():
            if len(reports) > 1:
                print(f"\n=== {label} ===")
            print(render_text(r, args.verbose))

    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:  # piped into head/less
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(0)
