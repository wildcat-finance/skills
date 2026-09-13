"""Three reading strategies for a TypeScript E001 recogniser, for comparison.

Each returns the offsets of log-call sites whose first argument is a message
built by formatting.  The strategies differ only in how they read the file:
`span_index` reuses the checker's masked lexer and bracket tables,
`unmasked_regex` scans the raw text, and `forward_scan` masks the text but
walks chains forward from every identifier instead of backwards from brackets.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "plugins" / "hexaemeron" / "skills" / "ephoros" / "scripts"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "ephoros_lint",
    ROOT / "plugins" / "hexaemeron" / "skills" / "ephoros" / "scripts" / "ephoros.py")
ephoros = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ephoros)

LOG_METHODS = ephoros.LOG_METHODS
TS_LOG_WORDS = ephoros.TS_LOG_WORDS


def _formatted(text, mask, start, end):
    """First argument is an interpolated template or a literal concatenation."""
    raw = text[start:end]
    stripped = raw.strip()
    if not stripped:
        return False
    if stripped[0] == "`" and "${" in stripped:
        return True
    if "+" in mask[start:end] and ('"' in stripped or "'" in stripped or "`" in stripped):
        return True
    return False


def span_index(text):
    spans, errors = ephoros.lex(text)
    if errors:
        return []
    mask = ephoros._masked(text, spans)
    matches = ephoros._bracket_matches(mask)
    index = ephoros._TsSpanIndex(Path("probe.ts"), text, mask,
                                 ephoros._newline_offsets(text), matches)
    out = []
    for bracket in ephoros.TS_OPEN.finditer(mask):
        opening = bracket.start()
        if mask[opening] != "(":
            continue
        segments = ephoros._ts_chain_before(mask, opening)
        if not segments or segments[0] == "console" or len(segments) < 2:
            continue
        if segments[-1] not in LOG_METHODS:
            continue
        if not (ephoros._ts_words(segments[-2]) & TS_LOG_WORDS):
            continue
        closing = matches.get(opening)
        if closing is None:
            continue
        first = index.ranges(opening, closing)[0]
        if _formatted(text, mask, *first):
            out.append(opening)
    return out


RAW_CALL = re.compile(
    r"(?<![\w$.])(?:log|logs|logger|logging)\s*\??\.\s*"
    r"(?:" + "|".join(sorted(LOG_METHODS)) + r")\s*\(")


def _paren_span(text, open_index):
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return len(text)


def unmasked_regex(text):
    out = []
    for match in RAW_CALL.finditer(text):
        opening = match.end() - 1
        closing = _paren_span(text, opening)
        if _formatted(text, text, opening + 1, closing):
            out.append(opening)
    return out


CHAIN = re.compile(r"[A-Za-z_$][\w$]*(?:\s*\??\.\s*[A-Za-z_$][\w$]*)*")


def forward_scan(text):
    """An independent second pass: walk every chain forward to its bracket."""
    spans, errors = ephoros.lex(text)
    if errors:
        return []
    mask = ephoros._masked(text, spans)
    out = []
    for match in CHAIN.finditer(mask):
        cursor = match.end()
        while cursor < len(mask) and mask[cursor].isspace():
            cursor += 1
        if cursor >= len(mask) or mask[cursor] != "(":
            continue
        segments = [s.strip() for s in re.split(r"\??\.", match.group())]
        segments = [s for s in segments if s]
        if len(segments) < 2 or segments[0] == "console":
            continue
        if segments[-1] not in LOG_METHODS:
            continue
        if not (ephoros._ts_words(segments[-2]) & TS_LOG_WORDS):
            continue
        closing = _paren_span(mask, cursor)
        if _formatted(text, mask, cursor + 1, closing):
            out.append(cursor)
    return out


STRATEGIES = {"span-index": span_index,
              "unmasked-regex": unmasked_regex,
              "forward-scan": forward_scan}
