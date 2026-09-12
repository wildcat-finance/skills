#!/usr/bin/env python3
"""Ephoros signal lint.

The mechanical subset of the skill: the rules a parser can settle without
reading intent. Everything else in SKILL.md stays a judgement.

  E001  a log message assembled by formatting, so its values cannot be queried
  E002  a metric label drawn from an unbounded source
  E003  a duration summarised as a mean
  E004  a supported YAML alert entry has no local runbook annotation
  E005  telemetry keyed by wallet address: a metric label, dashboard key or log index

Exit 0 clean, 1 findings, 2 bad invocation.

Deliberate exceptions state a reason: `# ephoros: allow <why>` in Python and
YAML, `// ephoros: allow <why>` in TypeScript.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from bisect import bisect_left
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from lib.typescript_lexer import lex  # noqa: E402

LOG_METHODS = {"debug", "info", "warning", "warn", "error", "critical", "exception", "log"}
# A logger, not any object with an `info` method, and deliberately not `print`:
# command-line output is not telemetry, and this marketplace writes plenty of it.
LOGGER_NAME = re.compile(r"(?:^|_|\.)(?:log|logger|logging)$", re.IGNORECASE)

LABEL_KWARGS = {"labels", "labelnames", "label_names", "tags", "attributes"}
UNBOUNDED = re.compile(
    r"(?:^|_)(?:address|wallet|hash|tx|txid|txhash|nonce|url|uri|path|email|user"
    r"|userid|account|request_?id|run_?id|trace_?id|session|error|message|id)s?(?:_|$)",
    re.IGNORECASE,
)

# One concern, one code: E005 claims the address-shaped labels, E002 keeps
# every other unbounded fragment.
ADDRESS_KEY = re.compile(r"(?:^|_)(?:address|wallet|addr)s?(?:_|$)", re.IGNORECASE)
HEX_ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
DASHBOARD_NAME = re.compile(r"(?:^|_|\.)(?:dashboard|panel)s?$", re.IGNORECASE)

DURATION = re.compile(
    r"(?:^|_)(?:duration|latency|elapsed|seconds|secs|millis|ms|runtime|response_?time"
    r"|took|wait|time)s?(?:_|$)",
    re.IGNORECASE,
)
MEAN_FUNCS = {"mean", "fmean", "average", "avg"}

# The pragma grammar is gated by surface: `#` belongs to Python and YAML,
# `//` to TypeScript, where it is read from genuine line-comment spans only.
ALLOW = re.compile(r"#\s*ephoros:\s*allow\s+(?P<reason>\S.*)$")
TS_ALLOW = re.compile(r"//\s*ephoros:\s*allow\s+(?P<reason>\S.*)$", re.MULTILINE)
YAML_SUFFIXES = {".yaml", ".yml"}
TYPESCRIPT_SUFFIXES = {".ts", ".tsx"}
TYPESCRIPT_MAX_BYTES = 1 << 20

# The TypeScript surface, read through the shared masked lexer the way phylax
# reads it. Recognition splits identifiers on underscore and camel-case
# boundaries, so `walletAddress` and `wallet_address` name the same key.
TS_IDENTIFIER = r"[A-Za-z_$][\w$]*"
TS_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")
# `?.` separates a chain the way `.` does: optional chaining names the same sink.
TS_SEPARATOR = r"\s*\??\.\s*"
TS_IDENT = re.compile(TS_IDENTIFIER)
TS_SEP = re.compile(TS_SEPARATOR)
TS_OPEN = re.compile(r"[\[(]")
TS_INTEREST = re.compile(r"[()\[\]{}:,]")
TS_IDENT_CHAR = re.compile(r"[\w$]")
TS_IDENT_START = re.compile(r"[A-Za-z_$]")
TS_LABEL_PROPERTY = re.compile(
    r"(?<![\w$])(?:labels|labelNames|labelnames|label_names|tags|attributes)"
    r"\s*:\s*(?P<open>[\[{])")
# No trailing `\s*`: a blanked string in the mask is spaces, and the value
# span must start at the colon so the raw literal can be read back.
TS_INDEX_PROPERTY = re.compile(r"(?<![\w$])index\s*:")
TS_ADDRESS_WORDS = frozenset({"address", "addresses", "addr", "addrs",
                              "wallet", "wallets"})
# The E002 vocabulary on this surface: the Python UNBOUNDED fragments, read
# as whole words after the same camel-case and underscore split E005 uses, so
# `requestId` and `request_id` name the same key. Each plural is listed as a
# word of its own rather than reached through an `s?` suffix, which is why
# `hashes` fires here where the Python rule passes it. The address-shaped
# words stay out: E005 claims those first, so one key reports one code.
TS_UNBOUNDED_WORDS = frozenset({
    "hash", "hashes", "tx", "txs", "txid", "txids", "txhash", "txhashes",
    "nonce", "nonces", "url", "urls", "uri", "uris", "path", "paths",
    "email", "emails", "user", "users", "userid", "userids",
    "account", "accounts", "requestid", "requestids", "runid", "runids",
    "traceid", "traceids", "session", "sessions", "error", "errors",
    "message", "messages", "id", "ids"})
# The E003 vocabulary on this surface: the Python DURATION fragments as whole
# words after the same split, so `avgWait`, `avg_wait` and `waits.length` all
# carry `wait`. Each plural is a word of its own, so `latencies` fires here
# where the Python `s?` suffix passes it.
TS_DURATION_WORDS = frozenset({
    "duration", "durations", "latency", "latencies", "elapsed", "seconds",
    "secs", "millis", "ms", "runtime", "runtimes", "responsetime",
    "responsetimes", "took", "wait", "waits", "time", "times"})
# What may follow a whole right-hand side: the statement ends, or the
# enclosing bracket or item does. Anything else means the mean was an operand.
TS_RHS_TERMINATORS = frozenset(";,)}]\n\r")
TS_METRIC_WORDS = frozenset({"metric", "metrics", "counter", "counters",
                             "gauge", "gauges", "histogram", "histograms",
                             "analytics", "telemetry", "statsd"})
TS_DASHBOARD_WORDS = frozenset({"dashboard", "dashboards", "panel", "panels"})
TS_LOG_WORDS = frozenset({"log", "logs", "logger", "logging"})
MAX_YAML_BYTES = 1 << 20
ALERT = re.compile(r"^-\s+alert\s*:")
ANNOTATIONS = re.compile(r"^annotations\s*:\s*$")
LABELS = re.compile(r"^labels\s*:\s*$")
YAML_KEY = re.compile(r"^(?P<key>[^\s:#-][^:]*?)\s*:")
RUNBOOK = re.compile(r"^runbook\s*:\s*(?P<path>.+?)\s*$", re.DOTALL)
BLOCK_SCALAR = re.compile(
    r"^(?:[^:#][^:]*:\s*|-\s+)[|>](?:[+-]?\d?|\d[+-]?)\s*$")


def suppressed(text: str, line: int) -> bool:
    lines = text.splitlines()
    for number in (line, line - 1):
        if 1 <= number <= len(lines) and ALLOW.search(lines[number - 1]):
            return True
    return False


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def as_dict(self) -> dict:
        return {"path": str(self.path), "line": self.line, "code": self.code,
                "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_of(node.value)}.{node.attr}".lstrip(".")
    return ""


def _is_str_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _address_key(label: str) -> bool:
    return bool(ADDRESS_KEY.search(label) or HEX_ADDRESS.fullmatch(label))


def _address_shaped(node: ast.AST) -> str:
    """Return the address-shaped name or literal in a key position, or ""."""
    if isinstance(node, ast.Name) and ADDRESS_KEY.search(node.id):
        return node.id
    if isinstance(node, ast.Attribute) and ADDRESS_KEY.search(node.attr):
        return node.attr
    if _is_str_literal(node) and _address_key(node.value):
        return node.value
    return ""


def _built_by_formatting(node: ast.AST) -> bool:
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return any(_is_str_literal(s) or isinstance(s, ast.JoinedStr)
                   for s in (node.left, node.right))
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
        and node.func.attr == "format" and _is_str_literal(node.func.value)


def _is_mean_call(node: ast.AST) -> bool:
    """statistics.mean(x), np.average(x), or the sum(x) / len(x) idiom."""
    if isinstance(node, ast.Call):
        func = node.func
        attr = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        return attr in MEAN_FUNCS
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left, right = node.left, node.right
        return (isinstance(left, ast.Call) and getattr(left.func, "id", "") == "sum"
                and isinstance(right, ast.Call) and getattr(right.func, "id", "") == "len")
    return False


def _mentions_duration(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and DURATION.search(child.id):
            return True
        if isinstance(child, ast.Attribute) and DURATION.search(child.attr):
            return True
        if _is_str_literal(child) and DURATION.search(child.value):
            return True
    return False


class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[Finding] = []

    def _add(self, node: ast.AST, code: str, message: str) -> None:
        self.findings.append(Finding(self.path, node.lineno, code, message))

    def _keyed_by_address(self, node: ast.AST, position: str, key: str) -> None:
        self._add(node, "E005",
                  f"{position} `{key}` keys telemetry by wallet address; "
                  "put it in an event")

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS \
                and LOGGER_NAME.search(_name_of(func.value)):
            if node.args and _built_by_formatting(node.args[0]):
                self._add(node, "E001",
                          "log message built by formatting; use a stable name and fields")

        if isinstance(func, ast.Attribute):
            if func.attr == "labels":
                for keyword in node.keywords:
                    if keyword.arg and ADDRESS_KEY.search(keyword.arg):
                        self._keyed_by_address(node, "metric label", keyword.arg)
                for arg in node.args:
                    if _is_str_literal(arg) and HEX_ADDRESS.fullmatch(arg.value):
                        self._keyed_by_address(node, "metric label", arg.value)
            if LOGGER_NAME.search(_name_of(func.value)):
                for keyword in node.keywords:
                    if keyword.arg == "index":
                        key = _address_shaped(keyword.value)
                        if key:
                            self._keyed_by_address(node, "log index", key)

        for keyword in node.keywords:
            if keyword.arg in LABEL_KWARGS:
                for label in self._label_names(keyword.value):
                    if _address_key(label):
                        self._keyed_by_address(node, "metric label", label)
                    elif UNBOUNDED.search(label):
                        self._add(node, "E002",
                                  f"metric label `{label}` is unbounded; put it in an event")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        key = _address_shaped(node.slice)
        if key:
            target = _name_of(node.value)
            if DASHBOARD_NAME.search(target):
                self._keyed_by_address(node, "dashboard key", key)
            elif LOGGER_NAME.search(target):
                self._keyed_by_address(node, "log index", key)
        self.generic_visit(node)

    @staticmethod
    def _label_names(node: ast.AST) -> list[str]:
        if isinstance(node, ast.Dict):
            return [k.value for k in node.keys if _is_str_literal(k)]
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return [e.value for e in node.elts if _is_str_literal(e)]
        return []

    def visit_Assign(self, node: ast.Assign) -> None:
        if _is_mean_call(node.value):
            names = [_name_of(t) for t in node.targets]
            if any(DURATION.search(n) for n in names if n) or _mentions_duration(node.value):
                self._add(node, "E003",
                          "duration summarised as a mean; record a histogram and read p95")
        self.generic_visit(node)


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


def _split_yaml_comment(
        line: str, quote: str | None = None) -> tuple[str, str, str | None]:
    """Split YAML content and comment while carrying a quoted scalar."""
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
            return line[:index], line[index:], None
    return line, "", active


def _yaml_allow_lines(lines: list[str]) -> set[int]:
    """Return reasoned pragma lines that are actual YAML comments."""
    allowed: set[int] = set()
    scalar_indent: int | None = None
    plain_indent: int | None = None
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
                continue
            if not raw.lstrip().startswith("#"):
                raw_indent = len(raw) - len(raw.lstrip(" "))
                if raw_indent > plain_indent:
                    continue
            plain_indent = None
        started_in_quote = quote is not None
        content, comment, quote = _split_yaml_comment(raw, quote)
        if started_in_quote:
            if quote is None and ALLOW.search(comment):
                allowed.add(number)
            continue
        content = content.rstrip()
        if not content.strip():
            if not comment:
                continue
            if ALLOW.search(comment):
                allowed.add(number)
            continue
        indent = len(content) - len(content.lstrip(" "))
        if ALLOW.search(comment):
            allowed.add(number)
        if BLOCK_SCALAR.match(content[indent:]):
            scalar_indent = indent
        else:
            plain_indent = _yaml_plain_scalar_indent(content)
    return allowed


def _yaml_lines(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return significant block-YAML lines, excluding block scalar bodies."""
    out: list[tuple[int, int, str]] = []
    scalar_indent: int | None = None
    plain_indent: int | None = None
    plain_out_index: int | None = None
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
                            out[plain_out_index] = (
                                first[0], first[1],
                                f"{first[2]}{separator}{continuation}")
                            plain_breaks = 0
                    continue
            plain_indent = None
            plain_out_index = None
            plain_breaks = 0
        started_in_quote = quote is not None
        content, _, quote = _split_yaml_comment(raw, quote)
        if started_in_quote:
            continue
        content = content.rstrip()
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        stripped = content[indent:]
        out.append((number, indent, stripped))
        if BLOCK_SCALAR.match(stripped):
            scalar_indent = indent
        else:
            plain_indent = _yaml_plain_scalar_indent(content)
            if plain_indent is not None and RUNBOOK.match(stripped):
                plain_out_index = len(out) - 1
    return out


def _relative_markdown(value: str) -> bool:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        value = value[1:-1].strip()
    return bool(value and value.lower().endswith(".md")
                and "\n" not in value and "\r" not in value
                and not value.startswith(("/", "\\"))
                and "://" not in value)


def _alert_label_findings(
        path: Path, significant: list[tuple[int, int, str]], allowed: set[int],
        index: int, end: int, child_indent: int | None) -> list[Finding]:
    """Return E005 findings for address-named keys under one alert's labels."""
    findings: list[Finding] = []
    cursor = index + 1
    while cursor < end:
        _, labels_indent, nested = significant[cursor]
        cursor += 1
        if labels_indent != child_indent or not LABELS.match(nested):
            continue
        key_child_indent = significant[cursor][1] if cursor < end else None
        while cursor < end:
            number, key_indent, candidate = significant[cursor]
            if key_indent <= labels_indent:
                break
            match = YAML_KEY.match(candidate)
            if key_indent == key_child_indent and match \
                    and _address_key(match.group("key")) \
                    and number not in allowed and number - 1 not in allowed:
                findings.append(Finding(
                    path, number, "E005",
                    f"alert label `{match.group('key')}` keys telemetry by "
                    "wallet address; put it in an event"))
            cursor += 1
    return findings


def _yaml_findings(path: Path, text: str) -> list[Finding]:
    lines = text.splitlines()
    significant = _yaml_lines(lines)
    allowed = _yaml_allow_lines(lines)
    findings: list[Finding] = []
    for index, (number, alert_indent, content) in enumerate(significant):
        if not ALERT.match(content):
            continue
        end = len(significant)
        for cursor in range(index + 1, len(significant)):
            _, indent, later = significant[cursor]
            if indent < alert_indent or (indent == alert_indent and later.startswith("-")):
                end = cursor
                break

        alert_child_indent = (significant[index + 1][1]
                              if index + 1 < end else None)
        findings.extend(_alert_label_findings(
            path, significant, allowed, index, end, alert_child_indent))
        annotated = False
        cursor = index + 1
        while cursor < end:
            _, annotations_indent, nested = significant[cursor]
            if (annotations_indent == alert_child_indent
                    and ANNOTATIONS.match(nested)):
                cursor += 1
                annotation_child_indent = (significant[cursor][1]
                                           if cursor < end else None)
                while cursor < end:
                    _, runbook_indent, candidate = significant[cursor]
                    if runbook_indent <= annotations_indent:
                        break
                    match = RUNBOOK.match(candidate)
                    if (runbook_indent == annotation_child_indent and match
                            and _relative_markdown(match.group("path"))):
                        annotated = True
                        break
                    cursor += 1
            if annotated:
                break
            cursor += 1

        if not annotated and number not in allowed and number - 1 not in allowed:
            findings.append(Finding(
                path, number, "E004",
                "alert entry has no nested `annotations.runbook` Markdown path"))
    return findings

def _newline_offsets(text: str) -> list[int]:
    """Offsets of every newline, built once per file so lookups can bisect.

    Counting from the top of the file for every finding cost quadratic time
    on findings-saturated files; one table and a bisection keep it linear.
    """
    offsets = []
    index = text.find("\n")
    while index != -1:
        offsets.append(index)
        index = text.find("\n", index + 1)
    return offsets


def _line_of(newlines: list[int], offset: int) -> int:
    return bisect_left(newlines, offset) + 1


def _masked(text: str, spans) -> str:
    """Blank comments, strings and other non-code while preserving offsets."""
    parts = []
    for kind, start, end in spans:
        segment = text[start:end]
        if kind == "code":
            parts.append(segment)
        else:
            parts.append("".join(ch if ch == "\n" else " " for ch in segment))
    return "".join(parts)


def _bracket_matches(mask: str) -> dict[int, int]:
    """Map every opening bracket's offset to its closing offset, or nothing.

    One linear stack pass per file: a closer pops only the innermost opener
    it actually pairs with, and a mismatched closer is inert, exactly as the
    old per-bracket forward scan behaved.  That scan restarted at every
    bracket with a chain before it, so fully overlapping nested spans cost
    quadratic time; the table answers every lookup in constant time.
    """
    pairs = {"(": ")", "[": "]", "{": "}"}
    matches: dict[int, int] = {}
    stack: list[tuple[int, str]] = []
    for index, current in enumerate(mask):
        if current in pairs:
            stack.append((index, pairs[current]))
        elif stack and current == stack[-1][1]:
            matches[stack.pop()[0]] = index
    return matches


def _ts_words(name: str) -> set[str]:
    return {word.lower() for word in TS_WORD.findall(name)}


def _skip_ws(mask: str, index: int) -> int:
    while index and mask[index - 1].isspace():
        index -= 1
    return index


def _ts_chain_ending(mask: str, index: int) -> tuple[int, list[str]] | None:
    """Parse the dotted chain whose last identifier ends at `index`.

    Returns (start offset, segments in source order), or None where no
    identifier ends there or the chain is a trailing property of something
    that is not a name. `?.` separates segments the way `.` does.
    """
    segments: list[str] = []
    while True:
        end = index
        while index and TS_IDENT_CHAR.match(mask[index - 1]):
            index -= 1
        if end == index or not TS_IDENT_START.match(mask[index]):
            # No identifier here: the chain ends at the last good segment,
            # and a separator already consumed is not part of it.
            if not segments:
                return None
            index = start
            break
        segments.append(mask[index:end])
        start = index
        after = _skip_ws(mask, index)
        if after and mask[after - 1] == ".":
            dot = after - 1
            if dot and mask[dot - 1] == "?":
                dot -= 1
            index = _skip_ws(mask, dot)
            continue
        break
    if index and mask[index - 1] == ".":
        return None  # a trailing property of something that is not a name
    segments.reverse()
    return index, segments


def _ts_chain_span(mask: str, opening: int) -> tuple[int, list[str]] | None:
    """The dotted chain ending at the bracket at `opening`, with its start.

    Scanning is anchored to the brackets: a chain is only ever read once,
    backwards from its own bracket, so a dotted expression that never reaches
    a bracket costs nothing.  A forward chain regex paid quadratically there --
    every admitted start position rescanned the whole remaining chain before
    failing at the bracket class.  `?.` separates segments the way `.` does,
    including the bracket form `?.[` and `?.(`.
    """
    index = _skip_ws(mask, opening)
    if mask[index - 2:index] == "?.":
        index = _skip_ws(mask, index - 2)
    return _ts_chain_ending(mask, index)


def _ts_chain_before(mask: str, opening: int) -> list[str] | None:
    """The segments of the chain ending at the bracket at `opening`, or None."""
    chain = _ts_chain_span(mask, opening)
    return chain[1] if chain is not None else None


def _ts_address_name(name: str) -> bool:
    return bool(_ts_words(name) & TS_ADDRESS_WORDS)


def _ts_keyed_by_address(path: Path, newlines: list[int], offset: int,
                         position: str, key: str) -> Finding:
    return Finding(path, _line_of(newlines, offset), "E005",
                   f"{position} `{key}` keys telemetry by wallet address; "
                   "put it in an event")


def _ts_unbounded_label(path: Path, newlines: list[int], offset: int,
                        key: str) -> Finding:
    return Finding(path, _line_of(newlines, offset), "E002",
                   f"metric label `{key}` is unbounded; put it in an event")


def _ts_mean_duration(path: Path, newlines: list[int], offset: int) -> Finding:
    return Finding(path, _line_of(newlines, offset), "E003",
                   "duration summarised as a mean; record a histogram and read p95")


def _ts_label_code(words: set[str]) -> str:
    """One concern, one code: the address subset is E005's before E002's."""
    if words & TS_ADDRESS_WORDS:
        return "E005"
    if words & TS_UNBOUNDED_WORDS:
        return "E002"
    return ""


class _TsSpanIndex:
    """Per-file tables that keep sink-named overlapping spans near-linear.

    Once a nested bracket chain named a sink, every enclosing bracket paid
    its full span for the property scans, the comma splits and the key
    expression reads, and fully overlapping spans made that quadratic --
    about 77 minutes at the 1 MiB cap.  Each table here is built in one
    pass over the file and consulted by bisection, so the total work
    across all spans stays near-linear in the file plus the findings
    actually reported.

    Every table keys events by the innermost *matched* bracket pair around
    them, which reproduces the old local scans exactly: inside a matched
    pair every opener is itself matched, so a scan's private stack mirrors
    the file-wide one, and an inert closer is inert to both.
    """

    def __init__(self, path: Path, text: str, mask: str,
                 newlines: list[int], matches: dict[int, int],
                 spans=None) -> None:
        self.path = path
        self.text = text
        self.mask = mask
        self.newlines = newlines
        self.matches = matches
        self.spans = spans if spans is not None else [("code", 0, len(text))]
        self._duration_starts: list[int] | None = None
        self._commas: dict[int, list[int]] | None = None
        self._colons: dict[int, list[int]] = {}
        self._inerts: dict[int, list[int]] = {}
        self._label_starts: list[int] = []
        self._label_rows: list[list[Finding]] = []
        self._index_starts: list[int] = []
        self._index_rows: list[Finding] = []
        self._word_starts: list[int] | None = None
        self._unbounded_starts: list[int] | None = None
        self._interp_starts: list[int] | None = None
        self._plus_offsets: list[int] | None = None
        self._quote_offsets: list[int] | None = None

    def _build(self) -> None:
        """One pass over the punctuation, then one pass over the sinks."""
        if self._commas is not None:
            return
        commas: dict[int, list[int]] = {}
        self._commas = commas
        colons, inerts = self._colons, self._inerts
        mask, matches = self.mask, self.matches
        index_matches = list(TS_INDEX_PROPERTY.finditer(mask))
        queries = sorted({match.end() for match in index_matches})
        enclosing: dict[int, int] = {}
        stack: list[int] = []
        cursor, total = 0, len(queries)
        for event in TS_INTEREST.finditer(mask):
            position = event.start()
            while cursor < total and queries[cursor] <= position:
                enclosing[queries[cursor]] = stack[-1] if stack else -1
                cursor += 1
            current = event.group()
            if current in "([{":
                if position in matches:
                    stack.append(position)
            elif current in ")]}":
                if stack and matches[stack[-1]] == position:
                    stack.pop()
                else:
                    inerts.setdefault(
                        stack[-1] if stack else -1, []).append(position)
            elif current == ",":
                commas.setdefault(
                    stack[-1] if stack else -1, []).append(position)
            else:
                colons.setdefault(
                    stack[-1] if stack else -1, []).append(position)
        while cursor < total:
            enclosing[queries[cursor]] = stack[-1] if stack else -1
            cursor += 1
        # The property regexes run once over the whole mask, each closed
        # container or value is analysed once, and only productive rows
        # are kept: a span later collects its rows by position, so nested
        # sinks still repeat findings the way the per-span scans did,
        # without repeating the work.  Neither property can straddle a
        # span boundary, because neither matches a closing bracket.
        for match in TS_LABEL_PROPERTY.finditer(mask):
            opening = match.start("open")
            closing = matches.get(opening)
            if closing is None:
                continue
            row = self._label_container(opening, closing)
            if row:
                self._label_starts.append(match.start())
                self._label_rows.append(row)
        for match in index_matches:
            begin = match.end()
            value_end = self._value_end(enclosing[begin], begin)
            key = self.address_expression(begin, value_end)
            if key:
                self._index_starts.append(match.start())
                self._index_rows.append(_ts_keyed_by_address(
                    self.path, self.newlines, match.start(),
                    "log index", key))

    def _value_end(self, opener: int, begin: int) -> int:
        """Where an `index:` value ends: the old forward scan, replayed.

        From `begin`, that scan's private stack saw exactly the depth-zero
        commas and inert closers of the innermost enclosing pair, and then
        the pair's own closer, whichever came first.
        """
        end = self.matches[opener] if opener != -1 else len(self.mask)
        for positions in (self._commas.get(opener, []),
                          self._inerts.get(opener, [])):
            found = bisect_left(positions, begin)
            if found < len(positions) and positions[found] < end:
                end = positions[found]
        return end

    def ranges(self, opening: int, closing: int) -> list[tuple[int, int]]:
        """Split one matched span at its depth-zero commas."""
        self._build()
        ranges = []
        item = opening + 1
        for comma in self._commas.get(opening, []):
            ranges.append((item, comma))
            item = comma + 1
        ranges.append((item, closing))
        return ranges

    def _first_colon(self, opening: int, start: int, end: int) -> int:
        positions = self._colons.get(opening, [])
        found = bisect_left(positions, start)
        if found < len(positions) and positions[found] < end:
            return positions[found]
        return end

    def _object_keys(self, opening: int,
                     closing: int) -> list[tuple[int, str, str]]:
        """(offset, code, key) for each reportable key of one object literal."""
        keys = []
        for start, end in self.ranges(opening, closing):
            key_end = self._first_colon(opening, start, end)
            offset, code, key = self.label_key(start, key_end)
            if code:
                keys.append((offset, code, key))
        return keys

    def _label_finding(self, offset: int, code: str, key: str) -> Finding:
        if code == "E005":
            return _ts_keyed_by_address(
                self.path, self.newlines, offset, "metric label", key)
        return _ts_unbounded_label(self.path, self.newlines, offset, key)

    def _label_container(self, opening: int, closing: int) -> list[Finding]:
        """E005 and E002 findings for the keys of one label set container.

        An object literal's keys and an array literal's string elements are
        the label names; an address-shaped one is E005's, any other
        unbounded one is E002's, exactly as the Python visitor splits them.
        """
        findings = []
        if self.mask[opening] == "{":
            for offset, code, key in self._object_keys(opening, closing):
                findings.append(self._label_finding(offset, code, key))
        else:
            for start, end in self.ranges(opening, closing):
                bounds = self._string_bounds(start, end)
                if bounds is None:
                    continue
                code = self._string_label_code(*bounds)
                if code:
                    findings.append(self._label_finding(
                        bounds[0] - 1, code, self.text[bounds[0]:bounds[1]]))
        return findings

    def label_findings(self, start: int, end: int) -> list[Finding]:
        """Label/tag/attribute sets inside one telemetry sink call."""
        self._build()
        findings: list[Finding] = []
        found = bisect_left(self._label_starts, start)
        while found < len(self._label_starts) \
                and self._label_starts[found] < end:
            findings.extend(self._label_rows[found])
            found += 1
        return findings

    def index_findings(self, start: int, end: int) -> list[Finding]:
        """`index:` properties inside one logger or log-store call."""
        self._build()
        found = bisect_left(self._index_starts, start)
        findings: list[Finding] = []
        while found < len(self._index_starts) \
                and self._index_starts[found] < end:
            findings.append(self._index_rows[found])
            found += 1
        return findings

    def labels_call(self, opening: int, closing: int) -> list[Finding]:
        """The Prometheus instance style: `.labels({...})` or a literal."""
        findings = []
        mask = self.mask
        for arg_start, arg_end in self.ranges(opening, closing):
            first = arg_start
            while first < arg_end and mask[first].isspace():
                first += 1
            if first < arg_end and mask[first] == "{":
                inner = self.matches.get(first)
                if inner is not None:
                    for offset, code, key in self._object_keys(first, inner):
                        findings.append(self._label_finding(offset, code, key))
            else:
                bounds = self._string_bounds(arg_start, arg_end)
                if bounds is not None and bounds[1] - bounds[0] == 42 \
                        and HEX_ADDRESS.fullmatch(
                            self.text, bounds[0], bounds[1]):
                    findings.append(_ts_keyed_by_address(
                        self.path, self.newlines, bounds[0] - 1,
                        "metric label", self.text[bounds[0]:bounds[1]]))
        return findings

    def _key_chain(self, start: int, end: int) -> tuple[int, str] | None:
        """The dotted chain in a key position as (offset, last identifier).

        Reads a bounded window instead of slicing the span: the dotted
        chain is parsed forward from the key's own start and stops at the
        first character outside the chain grammar, so fully overlapping
        spans no longer pay their whole width for every key. The offset is
        the chain's first character in the mask, past the separator's
        whitespace and past any comment, which the mask blanks; a finding
        reported there lands on the key's own line, so a pragma beside the
        key excuses it and a multi-line container reads as written.
        """
        mask = self.mask
        first, last = start, end
        while first < last and mask[first].isspace():
            first += 1
        while last > first and mask[last - 1].isspace():
            last -= 1
        ident = TS_IDENT.match(mask, first, last) if first < last else None
        while ident is not None and ident.end() < last:
            separator = TS_SEP.match(mask, ident.end(), last)
            ident = TS_IDENT.match(mask, separator.end(), last) \
                if separator is not None else None
        return (first, ident.group()) if ident is not None else None

    def _key_name(self, start: int, end: int) -> str | None:
        """The last identifier of the dotted chain in a key position, or None."""
        chain = self._key_chain(start, end)
        return chain[1] if chain is not None else None

    def address_expression(self, start: int, end: int) -> str:
        """The address-shaped name or literal in a key position, or ""."""
        name = self._key_name(start, end)
        if name is not None:
            return name if _ts_address_name(name) else ""
        bounds = self._string_bounds(start, end)
        if bounds is not None and self._address_value(*bounds):
            return self.text[bounds[0]:bounds[1]]
        return ""

    def label_key(self, start: int, end: int) -> tuple[int, str, str]:
        """(offset, code, key) for a label name in a key position.

        The same bounded read as `address_expression`, with the E002
        vocabulary consulted only once the address words have not claimed
        the key, so the split E005 already draws is inherited rather than
        reopened. The offset is the key's own first character, the chain
        start or the opening quote, rather than the item's separator, so
        the finding is reported on the key's line. An unrecognised key is
        (start, "", "").
        """
        chain = self._key_chain(start, end)
        if chain is not None:
            offset, name = chain
            return offset, _ts_label_code(_ts_words(name)), name
        bounds = self._string_bounds(start, end)
        if bounds is None:
            return start, "", ""
        code = self._string_label_code(*bounds)
        return (bounds[0] - 1, code,
                self.text[bounds[0]:bounds[1]] if code else "")

    def formatted_message(self, start: int, end: int) -> bool:
        """Is this argument a message built by formatting?

        An interpolated template literal, or a concatenation involving a
        string literal. Both answers come from tables built once per file
        and read by bisection, so an argument span costs its own bounds
        rather than its own width: the enclosing spans of a nested log
        call each pay a lookup, not a rescan.
        """
        self._build()
        text = self.text
        first, last = start, end
        while first < last and text[first].isspace():
            first += 1
        while last > first and text[last - 1].isspace():
            last -= 1
        if first >= last:
            return False
        if text[first] == "`" and self._interpolated(first, last):
            return True
        return self._has("_plus_offsets", self.mask, "+", first, last) \
            and self._has("_quote_offsets", text, "'\"`", first, last)

    def _has(self, cache_name: str, subject: str, wanted: str,
             start: int, end: int) -> bool:
        """Does `subject` carry one of `wanted` inside [start, end)?

        The offsets are found once for the whole file and then bisected.
        """
        offsets = getattr(self, cache_name)
        if offsets is None:
            offsets = [index for index, character in enumerate(subject)
                       if character in wanted]
            setattr(self, cache_name, offsets)
        found = bisect_left(offsets, start)
        return found < len(offsets) and offsets[found] < end

    def _string_bounds(self, start: int, end: int) -> tuple[int, int] | None:
        """Value bounds of a constant string literal, without slicing.

        A template literal with no `${}` interpolation is a constant
        string; an interpolated one is not, and stays out of key
        recognition.
        """
        text = self.text
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        if end - start < 2 or text[start] != text[end - 1]:
            return None
        if text[start] in "'\"":
            return start + 1, end - 1
        if text[start] == "`" and not self._interpolated(start + 1, end - 1):
            return start + 1, end - 1
        return None

    def _interpolated(self, start: int, end: int) -> bool:
        if self._interp_starts is None:
            starts = []
            found = self.text.find("${")
            while found != -1:
                starts.append(found)
                found = self.text.find("${", found + 1)
            self._interp_starts = starts
        starts = self._interp_starts
        found = bisect_left(starts, start)
        return found < len(starts) and starts[found] + 2 <= end

    def _address_value(self, start: int, end: int) -> bool:
        """An address-shaped string value, judged without slicing it.

        The value sits between two quote characters, which no word token
        can cross, so its word tokens are exactly the file's word tokens
        inside it: found once for the whole file, then bisected.
        """
        if end - start == 42 and HEX_ADDRESS.fullmatch(self.text, start, end):
            return True
        return self._word_between("_word_starts", TS_ADDRESS_WORDS, start, end)

    def _string_label_code(self, start: int, end: int) -> str:
        """E005, E002 or "" for one string-literal label name, address first."""
        if self._address_value(start, end):
            return "E005"
        if self._word_between("_unbounded_starts", TS_UNBOUNDED_WORDS,
                              start, end):
            return "E002"
        return ""

    def _word_between(self, cache_name: str, words: frozenset[str],
                      start: int, end: int) -> bool:
        """Does one of `words` start inside [start, end)?

        Each vocabulary's word starts are found once for the whole file and
        then bisected, the same table shape `_has` uses for E001.
        """
        starts = getattr(self, cache_name)
        if starts is None:
            starts = [match.start() for match in TS_WORD.finditer(self.text)
                      if match.group().lower() in words]
            setattr(self, cache_name, starts)
        found = bisect_left(starts, start)
        return found < len(starts) and starts[found] < end

    def mean_duration(self, opening: int, closing: int, chain_start: int,
                      segments: list[str]) -> list[Finding]:
        """E003 for one mean-shaped call: the whole right-hand side of an
        assignment, under a duration word in the target or the expression.

        The call is one bracket the walk already visited, so the pass is
        keyed to the bracket table rather than scanning forward for `=`.
        Each admitted bracket then pays a bounded read on either side: the
        assignment target backwards from the chain start, the `/ xs.length`
        tail and the terminator forwards from the closer, and one bisection
        into the duration word table. A nested `mean(mean(...))` rejects
        every inner bracket at its first character, because `(` is not `=`.
        """
        mask = self.mask
        end = closing + 1
        if segments[-1] == "reduce":
            end = self._reduce_over_length_end(end)
            if end is None:
                return []
        if not self._terminated(end):
            return []
        target = self._assignment_target(chain_start)
        if target is None:
            return []
        target_start, target_segments = target
        words = set().union(*(_ts_words(name) for name in target_segments))
        if not (words & TS_DURATION_WORDS
                or self._duration_between(chain_start, end)):
            return []
        return [_ts_mean_duration(self.path, self.newlines, target_start)]

    def _reduce_over_length_end(self, index: int) -> int | None:
        """The end of `/ xs.length` after a `reduce(...)` closer, or None."""
        mask = self.mask
        while index < len(mask) and mask[index].isspace():
            index += 1
        if index >= len(mask) or mask[index] != "/":
            return None
        index += 1
        while index < len(mask) and mask[index].isspace():
            index += 1
        ident = TS_IDENT.match(mask, index)
        segments = []
        while ident is not None:
            segments.append(ident.group())
            separator = TS_SEP.match(mask, ident.end())
            if separator is None:
                break
            ident = TS_IDENT.match(mask, separator.end())
        if ident is None or len(segments) < 2 or segments[-1] != "length":
            return None
        return ident.end()

    def _terminated(self, index: int) -> bool:
        """Does the right-hand side end at `index`, give or take blanks?"""
        mask = self.mask
        while index < len(mask) and mask[index] in " \t":
            index += 1
        return index >= len(mask) or mask[index] in TS_RHS_TERMINATORS

    def _assignment_target(self, chain_start: int) -> tuple[int, list[str]] | None:
        """(start, segments) of the name assigned at `chain_start`, or None.

        A plain `=` must sit before the expression: `==`, `!=`, `<=`, `>=`
        and the compound assignments are comparisons or accumulations, not
        the assignment the rule names, and Python's `Assign` excludes them
        too. A simple or dotted type annotation between the name and the
        `=` is stepped over; any other annotation shape is left alone.
        """
        mask = self.mask
        index = _skip_ws(mask, chain_start)
        if not index or mask[index - 1] != "=":
            return None
        equals = index - 1
        if equals and mask[equals - 1] in "=!<>+-*/%&|^":
            return None
        chain = _ts_chain_ending(mask, _skip_ws(mask, equals))
        if chain is None:
            return None
        before = _skip_ws(mask, chain[0])
        if before and mask[before - 1] == ":":
            chain = _ts_chain_ending(mask, _skip_ws(mask, before - 1))
        return chain

    def _duration_between(self, start: int, end: int) -> bool:
        """Does a duration word start inside [start, end), outside comments?

        The table is built once per file from the code, string and template
        spans, so a word inside a comment never counts and a word inside a
        string literal does, as the Python rule reads `ast` names and string
        constants alike.
        """
        starts = self._duration_starts
        if starts is None:
            starts = []
            for kind, span_start, span_end in self.spans:
                if kind in ("code", "string", "template"):
                    starts.extend(
                        match.start() for match in TS_WORD.finditer(
                            self.text, span_start, span_end)
                        if match.group().lower() in TS_DURATION_WORDS)
            self._duration_starts = starts
        found = bisect_left(starts, start)
        return found < len(starts) and starts[found] < end


def _ts_allow_lines(text: str, spans, newlines: list[int]) -> set[int]:
    """Return reasoned pragma lines that are genuine `//` line comments.

    The documented grammar is a `//` line comment, so block comments are
    inert for suppression: `/* // ephoros: allow why */` states no reason
    at the site it would excuse.
    """
    allowed: set[int] = set()
    for kind, start, end in spans:
        if kind != "line_comment":
            continue
        for match in TS_ALLOW.finditer(text, start, end):
            allowed.add(_line_of(newlines, match.start()))
    return allowed


def check_typescript(path: Path, text: str) -> list[Finding]:
    # The lexer boundary fails closed per file: a construct it cannot
    # terminate reports E000 here rather than crashing the whole run, and
    # E000 bypasses suppression, matching the Python and YAML semantics.
    try:
        spans, errors = lex(text)
    except RecursionError:
        return [Finding(path, 1, "E000", "could not lex: recursion limit")]
    except Exception as err:  # noqa: BLE001 -- any lexer failure fails closed
        return [Finding(path, 1, "E000", f"could not lex: {err}")]
    newlines = _newline_offsets(text)
    if errors:
        return [Finding(path, _line_of(newlines, offset), "E000",
                        f"could not lex: {reason}")
                for offset, reason in errors]
    allowed = _ts_allow_lines(text, spans, newlines)
    mask = _masked(text, spans)
    matches = _bracket_matches(mask)
    span_index = _TsSpanIndex(path, text, mask, newlines, matches, spans)
    findings: list[Finding] = []
    for bracket in TS_OPEN.finditer(mask):
        opening = bracket.start()
        chain = _ts_chain_span(mask, opening)
        if chain is None or not chain[1]:
            continue
        chain_start, segments = chain
        if segments[0] == "console":
            continue  # command-line output is not telemetry
        # The cheap sink-name gates come before any per-bracket span work:
        # a bracket whose chain names no sink costs nothing further.
        last_words = _ts_words(segments[-1])
        if mask[opening] == "[":
            if not last_words & (TS_DASHBOARD_WORDS | TS_LOG_WORDS):
                continue
            closing = matches.get(opening)
            if closing is None:
                continue
            key = span_index.address_expression(opening + 1, closing)
            if key and last_words & TS_DASHBOARD_WORDS:
                findings.append(_ts_keyed_by_address(
                    path, newlines, opening + 1, "dashboard key", key))
            elif key and last_words & TS_LOG_WORDS:
                findings.append(_ts_keyed_by_address(
                    path, newlines, opening + 1, "log index", key))
            continue
        chain_words = set().union(*(_ts_words(s) for s in segments))
        metric_sink = bool(chain_words & TS_METRIC_WORDS)
        labels_call = len(segments) >= 2 and segments[-1] == "labels"
        log_call = len(segments) >= 2 and bool(
            _ts_words(segments[-2]) & TS_LOG_WORDS)
        mean_call = segments[-1] in MEAN_FUNCS or segments[-1] == "reduce"
        if not (metric_sink or labels_call or log_call or mean_call):
            continue
        closing = matches.get(opening)
        if closing is None:
            continue
        if mean_call:
            findings.extend(span_index.mean_duration(
                opening, closing, chain_start, segments))
        if metric_sink:
            findings.extend(span_index.label_findings(opening + 1, closing))
        if labels_call:
            findings.extend(span_index.labels_call(opening, closing))
        if log_call:
            findings.extend(span_index.index_findings(opening + 1, closing))
            # E001 wants the method too: `logger.debug(...)` is a log write,
            # `logger.child(...)` is not. The first argument comes from the
            # span index's comma table rather than a forward scan of the span.
            if segments[-1] in LOG_METHODS and span_index.formatted_message(
                    *span_index.ranges(opening, closing)[0]):
                findings.append(Finding(
                    path, _line_of(newlines, opening), "E001",
                    "log message built by formatting; "
                    "use a stable name and fields"))
    return [finding for finding in findings
            if finding.line not in allowed and finding.line - 1 not in allowed]


def check(path: Path) -> list[Finding]:
    if path.suffix in TYPESCRIPT_SUFFIXES:
        try:
            with path.open("rb") as source:
                raw = source.read(TYPESCRIPT_MAX_BYTES + 1)
            if len(raw) > TYPESCRIPT_MAX_BYTES:
                return [Finding(path, 1, "E000",
                                "unreadable: TypeScript exceeds 1 MiB")]
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as err:
            return [Finding(path, 1, "E000", f"unreadable: {err}")]
        return check_typescript(path, text)
    if path.suffix in YAML_SUFFIXES:
        try:
            with path.open("rb") as source:
                raw = source.read(MAX_YAML_BYTES + 1)
            if len(raw) > MAX_YAML_BYTES:
                return [Finding(path, 1, "E000", "unreadable: YAML exceeds 1 MiB")]
            text = raw.decode("utf-8")
        except (OSError, UnicodeDecodeError) as err:
            return [Finding(path, 1, "E000", f"unreadable: {err}")]
        return _yaml_findings(path, text)
    if path.suffix != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as err:
        return [Finding(path, 1, "E000", f"unreadable: {err}")]
    try:
        tree = ast.parse(text)
    except SyntaxError as err:
        return [Finding(path, err.lineno or 1, "E000", f"could not parse: {err.msg}")]
    visitor = Visitor(path)
    visitor.visit(tree)
    return [f for f in visitor.findings if not suppressed(text, f.line)]


def walk(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        root = Path(raw)
        if root.is_dir():
            suffixes = (".py", *sorted(TYPESCRIPT_SUFFIXES),
                        *sorted(YAML_SUFFIXES))
            found = (child for suffix in suffixes
                     for child in root.rglob(f"*{suffix}"))
            out.extend(child for child in sorted(set(found))
                       if child.is_file()
                       and "__pycache__" not in child.parts
                       and "node_modules" not in child.parts
                       and "fixtures" not in child.relative_to(root).parts[:-1])
        else:
            out.append(root)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ephoros signal lint.")
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    for path in walk(args.paths or ["."]):
        findings.extend(check(path))

    if args.format == "json":
        print(json.dumps([f.as_dict() for f in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
