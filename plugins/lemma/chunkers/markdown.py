#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""
Lemma Markdown chunker

Chunks markdown on heading boundaries, emitting the shared schema.

    python3 chunkers/markdown.py --root docs \
        --manifest manifest.yaml --summary SUMMARY.md --out docs.jsonl

`display_text` is a byte-exact slice of the source file, same promise as the
Solidity chunker, so a citation quotes what is actually in the file. Everything
here works on bytes and slices by byte offset.

Structure is resolved by a single line-state machine that tracks code fences,
HTML comments, raw HTML blocks and open paragraphs together, because they
interact: a heading inside a fence is not a heading, a heading inside an HTML
comment or a `<div>` block is not a heading either, and whether `---` is a
heading underline or a thematic break depends on whether a paragraph is open
above it. The single pass is not an optimisation: it has to know most of
CommonMark's block grammar before its output can be trusted.

Anchors follow the GitBook renderer's algorithm, fitted against the heading
ids a rendered GitBook site actually serves, renderer artifacts included,
rather than guessed from a slug library; `tools/verify_anchors.py` re-checks the whole
fit against a live site. A citation URL built from an anchor is a promise the
same way a quoted byte range is.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import pathlib
import re
import shlex
import sys

_spec = importlib.util.spec_from_file_location(
    "lemma_schema", pathlib.Path(__file__).resolve().parent.parent / "schema.py")
_schema = importlib.util.module_from_spec(_spec)
sys.modules["lemma_schema"] = _schema
_spec.loader.exec_module(_schema)
Chunk = _schema.Chunk


class ChunkError(Exception):
    """Raised for conditions that must stop a build rather than warn."""


# CommonMark allows up to three leading spaces before an ATX marker, and a
# closing hash sequence only when it is preceded by a space.
ATX = re.compile(rb"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
FENCE = re.compile(rb"^( {0,3})(`{3,}|~{3,})(.*)$")
SETEXT = re.compile(rb"^ {0,3}(=+|-+)[ \t]*$")
CLOSING_HASHES = re.compile(r"[ \t]+#+[ \t]*$")

# A setext underline of dashes is also a valid thematic break; which one it is
# depends on whether a paragraph is open, which is why the scanner tracks one.
THEMATIC = re.compile(rb"^ {0,3}((\*[ \t]*){3,}|(-[ \t]*){3,}|(_[ \t]*){3,})$")
BLOCKQUOTE = re.compile(rb"^ {0,3}>")
LIST_ITEM = re.compile(rb"^ {0,3}(?:[-+*]|\d{1,9}[.)])(?:[ \t]|$)")
TEMPLATE_LINE = re.compile(rb"^ {0,3}\{%")        # GitBook {% hint %} etc.
# A complete GitBook template tag anywhere on a line. GitBook's templating
# runs before rendering, so tag bytes never reach the published page. This also
# holds when a tag shares its line with visible prose, which is how a live corpus
# chunk carried `{% hint style="info" %} **prose** … {% endhint %}` into an
# answer. An unclosed `{%` matches nothing and stays literal text: the
# fail-safe direction, matching the code-span rule above.
TEMPLATE_TAG = re.compile(rb"\{%.*?%\}")
INDENTED_CODE = re.compile(rb"^(?: {4}|\t)")

# CommonMark HTML blocks. Type 1 runs to an explicit closing tag; types 3-5 to
# their own terminators; types 6 and 7 to the next blank line. While one is
# open, nothing inside it is a heading. Under an earlier version `# Not a
# heading` inside a <div> became one, corrupting every breadcrumb after it.
# An *opening* tag only. A lone `</script>` does not begin a type-1 block. It is
# inline text, and treating it as a block opener silently swallowed the
# paragraph it was sitting in. HTML1_CLOSE still terminates an open block.
HTML1_OPEN = re.compile(rb"^ {0,3}<(script|pre|style|textarea)(?=[ \t>/]|$)", re.I)
HTML1_CLOSE = re.compile(rb"</(?:script|pre|style|textarea)>", re.I)
HTML_PI_OPEN = re.compile(rb"^ {0,3}<\?")
HTML_DECL_OPEN = re.compile(rb"^ {0,3}<![A-Za-z]")
HTML_CDATA_OPEN = re.compile(rb"^ {0,3}<!\[CDATA\[")
HTML6_OPEN = re.compile(rb"^ {0,3}</?([A-Za-z][A-Za-z0-9-]*)(?=[ \t/>]|$)")
HTML6_TAGS = {
    b"address", b"article", b"aside", b"base", b"basefont", b"blockquote",
    b"body", b"caption", b"center", b"col", b"colgroup", b"dd", b"details",
    b"dialog", b"dir", b"div", b"dl", b"dt", b"fieldset", b"figcaption",
    b"figure", b"footer", b"form", b"frame", b"frameset", b"h1", b"h2", b"h3",
    b"h4", b"h5", b"h6", b"head", b"header", b"hr", b"html", b"iframe",
    b"legend", b"li", b"link", b"main", b"menu", b"menuitem", b"nav",
    b"noframes", b"ol", b"optgroup", b"option", b"p", b"param", b"search",
    b"section", b"summary", b"table", b"tbody", b"td", b"tfoot", b"th",
    b"thead", b"title", b"tr", b"track", b"ul",
}
_HTML1_TAGS = {b"script", b"pre", b"style", b"textarea"}
# Type 7: one complete open or closing tag, alone on its line. It may not
# interrupt a paragraph, which scan_structure enforces.
_ATTR = (rb"[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*"
         rb"(?:[ \t]*=[ \t]*(?:[^ \t\"'=<>`]+|'[^']*'|\"[^\"]*\"))?")
HTML7_LINE = re.compile(
    rb"^ {0,3}(?:<([A-Za-z][A-Za-z0-9-]*)(?:" + _ATTR + rb")*[ \t]*/?>"
    rb"|</([A-Za-z][A-Za-z0-9-]*)[ \t]*>)[ \t]*$")
CODE_SPAN = re.compile(rb"(`+)(.+?)\1")
# Some pinned protocol notes use a standalone strong paragraph as a visible
# section title instead of a Markdown heading. GitBook renders no anchor for
# it, but treating six such titles as one section created a multi-topic
# citation chunk. Keep this deliberately narrow: one complete strong span,
# alone in a top-level paragraph, with no nested emphasis marker.
STRONG_SECTION = re.compile(
    rb"^ {0,3}(?:\*\*([^*\r\n][^*\r\n]*?)\*\*"
    rb"|__([^_\r\n][^_\r\n]*?)__)[ \t]*$")

MAX_HEADING_LEVEL = 4          # H5/H6 stay inside their parent section


# --------------------------------------------------------------------------
# line handling: LF, CRLF and lone CR are all line terminators
# --------------------------------------------------------------------------

LINE_END = re.compile(rb"\r\n|\n|\r")


def iter_lines(blob: bytes, start: int = 0):
    """Yield (offset, line_without_terminator) over any line ending."""
    pos = start
    n = len(blob)
    while pos < n:
        m = LINE_END.search(blob, pos)
        if m is None:
            yield pos, blob[pos:]
            return
        yield pos, blob[pos:m.start()]
        pos = m.end()


def line_number(blob: bytes, offset: int) -> int:
    return len(LINE_END.split(blob[:offset]))


# --------------------------------------------------------------------------
# frontmatter
# --------------------------------------------------------------------------

def split_frontmatter(blob: bytes) -> tuple[dict, int]:
    """
    Return (fields, byte offset where the body starts).

    Deliberately not a YAML parser: frontmatter here is a handful of scalar
    fields, and pulling in a parser to read `description:` would mean a
    malformed document could abort a build over metadata nobody retrieves.
    Unparseable frontmatter yields no fields and is skipped, not fatal.
    """
    lines = list(iter_lines(blob))
    if not lines or lines[0][1].strip() != b"---":
        return {}, 0
    for offset, line in lines[1:]:
        if line.strip() == b"---":
            body_start = offset + len(line)
            m = LINE_END.match(blob, body_start)
            if m:
                body_start = m.end()
            fields: dict[str, str] = {}
            raw = blob[len(lines[0][1]):offset].decode("utf-8", "replace")
            for fl in raw.split("\n"):
                fl = fl.rstrip("\r")
                if ":" in fl and not fl.startswith((" ", "\t", "-")):
                    k, _, v = fl.partition(":")
                    fields[k.strip()] = v.strip().strip('"').strip("'")
            return fields, body_start
    return {}, 0


# --------------------------------------------------------------------------
# structure scan: a line state machine over fences, comments, raw HTML,
# paragraphs and headings
# --------------------------------------------------------------------------

def _tick_runs(line: bytes) -> list[tuple[int, int, bool]]:
    """
    Every backtick run as (start, end, escaped), where `escaped` marks a run
    whose first backtick is preceded by an odd number of backslashes. Such a
    backtick is literal text and cannot begin a delimiter; the rest of the run,
    if any, still can.
    """
    runs: list[tuple[int, int, bool]] = []
    i, n = 0, len(line)
    while i < n:
        if line[i:i + 1] != b"`":
            i += 1
            continue
        j = i
        while j < n and line[j:j + 1] == b"`":
            j += 1
        back, k = 0, i - 1
        while k >= 0 and line[k:k + 1] == b"\\":
            back += 1
            k -= 1
        runs.append((i, j, back % 2 == 1))
        i = j
    return runs


def _code_span_ranges(line: bytes, open_ticks: int = 0, lookahead: bytes = b""
                      ) -> tuple[list[tuple[int, int]], int]:
    """
    Byte ranges of inline code on this line, and the length of any backtick run
    still open at end of line.

    CommonMark closes a code span on a run of exactly the opening length, and a
    span may cross soft line breaks — but a run with no matching closer *is not
    a delimiter at all*, it is a literal backtick. An earlier version assumed any
    unclosed run opened a span running to end of line, so a stray or
    backslash-escaped backtick masked the rest of the line and any HTML comment
    after it stopped being recognised as a comment. That is the dangerous
    direction: text the reader never sees reaching `model_text`.

    `lookahead` is the remainder of the current block, so a closer on a later
    line of the same paragraph counts and one past a block boundary does not.
    Where the two readings are genuinely ambiguous this errs toward *not* code,
    which costs a visible backtick its formatting and never hides anything.
    """
    ranges: list[tuple[int, int]] = []
    runs = _tick_runs(line)
    i = 0

    if open_ticks:
        # a closer is matched on its full length; escapes do not apply inside
        # a code span, so `escaped` is ignored here
        while i < len(runs):
            start, end, _ = runs[i]
            if end - start == open_ticks:
                ranges.append((0, end))
                i += 1
                open_ticks = 0
                break
            i += 1
        else:
            return [(0, len(line))], open_ticks   # still inside the span

    while i < len(runs):
        start, end, escaped = runs[i]
        opener = start + 1 if escaped else start
        length = end - opener
        if length <= 0:                            # fully escaped single tick
            i += 1
            continue
        close_at = None
        for j in range(i + 1, len(runs)):
            c_start, c_end, _ = runs[j]
            if c_end - c_start == length:
                close_at = (j, c_end)
                break
        if close_at is not None:
            ranges.append((opener, close_at[1]))
            i = close_at[0] + 1
            continue
        if any(e - s == length for s, e, _ in _tick_runs(lookahead)):
            ranges.append((opener, len(line)))     # closes on a later line
            return ranges, length
        i += 1                                     # no closer: literal text
    return ranges, 0


def _scan_comments(line: bytes, offset: int, in_comment: bool,
                   comment_start: int, comments: list[tuple[int, int]],
                   open_ticks: int = 0, lookahead: bytes = b""
                   ) -> tuple[bytes, bool, int, int]:
    """
    Find HTML comments on one line, appending completed (start, end) byte
    spans to `comments` and returning (structure_line, in_comment,
    comment_start). structure_line is the input with comment bytes — and only
    comment bytes — blanked, so `# Visible <!-- hidden --> title` is still an
    ATX heading afterwards. An earlier version blanked everything up to a
    comment's close, which deleted the `# ` and turned the heading into stray
    prose.

    A `<!--` inside a code span is literal text, per CommonMark inline
    precedence, and is neither an opener nor stripped. `open_ticks` carries an
    unclosed backtick run in from the previous line, so spans that cross soft
    line breaks are respected too; it is returned for the next line.
    """
    buf = bytearray(line)
    spans, open_ticks = ((_code_span_ranges(line, open_ticks, lookahead))
                         if not in_comment else ([], open_ticks))
    pos, n = 0, len(line)
    while True:
        if in_comment:
            end = line.find(b"-->", pos)
            if end == -1:
                for i in range(pos, n):
                    buf[i] = 0x20
                return bytes(buf), True, comment_start, open_ticks
            comments.append((comment_start, offset + end + 3))
            for i in range(pos, end + 3):
                buf[i] = 0x20
            in_comment, comment_start = False, -1
            pos = end + 3
            spans, open_ticks = _code_span_ranges(line[pos:], 0, lookahead)
            spans = [(a + pos, b + pos) for a, b in spans]
        else:
            begin = line.find(b"<!--", pos)
            while begin != -1 and any(a <= begin < b for a, b in spans):
                begin = line.find(b"<!--", begin + 1)
            if begin == -1:
                return bytes(buf), False, -1, open_ticks
            in_comment, comment_start = True, offset + begin
            for i in range(begin, begin + 4):    # the opener is comment too
                buf[i] = 0x20
            pos = begin + 4


def _scan_templates(line: bytes, offset: int,
                    templates: list[tuple[int, int]],
                    code_ranges: list[tuple[int, int]]) -> None:
    """
    Record complete GitBook template tags on one line as (start, end) byte
    spans. `line` is the structure line with comment bytes already blanked,
    so a tag inside a comment is never recorded twice, and a tag inside a
    valid code span is visible example markup and is skipped.
    """
    for m in TEMPLATE_TAG.finditer(line):
        if any(a <= m.start() < b for a, b in code_ranges):
            continue
        templates.append((offset + m.start(), offset + m.end()))


def _inline_lookahead(lines: list[tuple[int, bytes]], idx: int) -> bytes:
    """
    The rest of the current block, for deciding whether a backtick delimiter
    ever finds its closer. Inline state does not survive a block boundary, so
    this stops at a blank line, a fence, a heading, a thematic break or the
    start of a raw-HTML block — not merely at the blank line.
    """
    out: list[bytes] = []
    for _, nxt in lines[idx + 1:]:
        if not nxt.strip():
            break
        if (FENCE.match(nxt) or ATX.match(nxt) or THEMATIC.match(nxt)
                or HTML1_OPEN.match(nxt) or HTML7_LINE.match(nxt)):
            break
        m = HTML6_OPEN.match(nxt)
        if m and m.group(1).lower() in HTML6_TAGS:
            break
        out.append(nxt)
    return b"\n".join(out)


def scan_structure(blob: bytes, start: int,
                   strong_sections: list[tuple[int, bytes]] | None = None):
    """
    Return (headings, invisible_spans).

    headings: [(offset, level, text)] for every heading that is genuinely a
    heading — outside fences, comments and raw HTML blocks — at every level 1
    through 6. Callers decide which levels become chunk boundaries; anchors
    must be counted over all of them, because the renderer numbers duplicates
    over what it renders, not over what this chunker later keeps.

    invisible_spans: sorted [(start, end)] byte ranges that a reader of the
    rendered page cannot see, for removal from model_text by span: HTML
    comments, and complete GitBook `{% … %}` template tags, whose bytes the
    templating pass consumes before the page renders — wherever they sit on a
    line, not only when they open it. Either kind inside fenced code or a
    valid code span is visible example markup and is not recorded; both kinds
    inside type 6/7 raw-HTML blocks are invisible in exactly the way bare
    ones are, so they are.

    When `strong_sections` is supplied, it receives standalone bold paragraph
    boundaries found by this same state machine. The optional output preserves
    the long-standing two-value return contract for callers that only need
    renderer headings and invisible spans.
    """
    headings: list[tuple[int, int, bytes]] = []
    comments: list[tuple[int, int]] = []
    templates: list[tuple[int, int]] = []

    fence_char, fence_len = b"", 0
    in_comment, comment_start = False, -1
    html_end = None            # regex closing an explicit raw-HTML block
    html_until_blank = False   # inside a type 6/7 block
    para: list[tuple[int, bytes]] = []
    open_ticks = 0             # backtick run left open by the previous line
    # A list item holds an open paragraph that unindented following lines
    # continue lazily. Those continuations belong to the item, so a setext
    # underline cannot attach to them: `- foo\nbar\n---` is a list and a
    # thematic break, but an earlier version emitted an H2 called "bar" with
    # a `#bar` fragment the rendered page does not have.
    # A blockquote holds an open paragraph exactly as a list item does, and
    # CommonMark's lazy-continuation rule is the same for both: an unindented
    # line after either continues the container's paragraph rather than
    # starting a new one. Modelling only the list case left `> quoted / lazy
    # continuation / ---` producing a phantom H2 and a citation fragment the
    # rendered page does not have.
    container_open = False
    container_blank = False    # a blank line has been seen inside it

    lines = list(iter_lines(blob, start))
    for idx, (offset, line) in enumerate(lines):
        # only paid for when the line could actually carry a delimiter
        ahead = _inline_lookahead(lines, idx) if b"`" in line else b""
        # -- a multi-line comment consumes everything until it closes -------
        if in_comment:
            _, in_comment, comment_start, open_ticks = _scan_comments(
                line, offset, True, comment_start, comments, open_ticks, ahead)
            continue

        # -- fenced code: only the closing fence matters ---------------------
        if fence_char:
            m = FENCE.match(line)
            if (m and m.group(2)[:1] == fence_char
                    and len(m.group(2)) >= fence_len
                    and m.group(3).strip() == b""):
                fence_char, fence_len = b"", 0
            continue

        # -- explicit raw HTML (types 1, 3, 4, 5): runs to its terminator ---
        if html_end is not None:
            if html_end.search(line):
                html_end = None
            continue

        # -- type 6/7 raw HTML: runs to the next blank line ------------------
        if html_until_blank:
            if not line.strip():
                html_until_blank = False
                continue
            # comments and template tags inside the block are invisible text;
            # markdown inline rules do not apply here, so no code spans shield
            sline, in_comment, comment_start, open_ticks = _scan_comments(
                line, offset, False, comment_start, comments, open_ticks, ahead)
            _scan_templates(sline, offset, templates, [])
            continue

        # -- normal state -----------------------------------------------------
        prev_ticks = open_ticks
        sline, in_comment, comment_start, open_ticks = _scan_comments(
            line, offset, False, comment_start, comments, open_ticks, ahead)
        _scan_templates(sline, offset, templates,
                        _code_span_ranges(sline, prev_ticks, ahead)[0])

        if not sline.strip():
            para = []
            open_ticks = 0          # a code span cannot cross a blank line
            if container_open:
                container_blank = True
            continue

        m = FENCE.match(sline)
        if m:
            marker, rest = m.group(2), m.group(3)
            # an opening backtick fence may not contain a backtick in its info
            if not (marker[:1] == b"`" and b"`" in rest):
                fence_char, fence_len = marker[:1], len(marker)
                para, container_open, open_ticks = [], False, 0
                continue

        m = HTML1_OPEN.match(sline)
        if m:
            para = []
            if not HTML1_CLOSE.search(sline, m.end()):
                html_end = HTML1_CLOSE
            continue
        if HTML_CDATA_OPEN.match(sline):        # before DECL: <![ is not <!x
            para = []
            if b"]]>" not in sline:
                html_end = re.compile(rb"\]\]>")
            continue
        if HTML_PI_OPEN.match(sline):
            para = []
            if b"?>" not in sline[sline.find(b"<?") + 2:]:
                html_end = re.compile(rb"\?>")
            continue
        if HTML_DECL_OPEN.match(sline):
            para = []
            if b">" not in sline:
                html_end = re.compile(rb">")
            continue
        m = HTML6_OPEN.match(sline)
        if m and m.group(1).lower() in HTML6_TAGS:
            para = []
            html_until_blank = True
            continue
        m = HTML7_LINE.match(sline)
        if m and not para:
            tag = (m.group(1) or m.group(2) or b"").lower()
            if tag not in _HTML1_TAGS:
                html_until_blank = True
                continue

        atx = ATX.match(sline)
        if atx:
            # An ATX heading interrupts anything, including a list item's
            # paragraph. It is never a lazy continuation.
            headings.append((offset, len(atx.group(1)), atx.group(2) or b""))
            para = []
            container_open = False
            continue

        st = SETEXT.match(sline)
        if st and para:
            # An underline after an open paragraph makes the whole paragraph a
            # heading, rather than only its last line.
            level = 1 if st.group(1)[:1] == b"=" else 2
            text = b" ".join(l.strip() for _, l in para)
            headings.append((para[0][0], level, text))
            para = []
            continue

        if THEMATIC.match(sline):
            # `---` with no paragraph above it is a thematic break. The old
            # scanner made it a heading of whatever non-paragraph line came
            # before, including `> quoted text`.
            para = []
            container_open = False
            continue

        # a lone `===` with no paragraph above is just text, and falls through

        if LIST_ITEM.match(sline) or BLOCKQUOTE.match(sline):
            container_open, container_blank, para = True, False, []
            continue
        if TEMPLATE_LINE.match(sline):
            container_open, para = False, []
            continue
        if INDENTED_CODE.match(sline):
            # inside a container this is its content; outside one it is code
            if container_open or not para:
                continue
        if container_open:
            if not container_blank:
                continue          # lazy continuation of the container's paragraph
            container_open = False  # blank line then unindented text ends it

        # A complete strong span at the start of a top-level paragraph is a
        # reviewed pseudo-heading convention in the pinned protocol notes.
        # It is tested here, after fences/comments/HTML/containers have been
        # excluded, so examples and list emphasis cannot become boundaries.
        if strong_sections is not None and not para:
            strong = STRONG_SECTION.match(sline)
            if strong:
                strong_sections.append((offset,
                                        strong.group(1) or strong.group(2)))
                continue

        para.append((offset, sline))

    if in_comment:
        # unterminated: everything from the opener onward is comment
        comments.append((comment_start, len(blob)))
    return headings, sorted(comments + templates)


def strip_invisible_spans(blob: bytes, chunk_start: int, chunk_end: int,
                          spans) -> str:
    """
    Remove reader-invisible bytes — HTML comments and GitBook template tags —
    from a chunk using spans found by the structural scan.

    A regex over the chunk cannot do this: a comment opening before the chunk
    and closing inside it leaves an orphan `-->` and, worse, leaves the comment
    body looking like ordinary prose. Spans inside fenced code are not in
    `spans` at all, so example markup shown to a reader survives intact.
    """
    keep: list[bytes] = []
    cursor = chunk_start
    for c_start, c_end in spans:
        if c_end <= chunk_start or c_start >= chunk_end:
            continue
        s = max(c_start, chunk_start)
        e = min(c_end, chunk_end)
        keep.append(blob[cursor:s])
        cursor = e
    keep.append(blob[cursor:chunk_end])
    return b"".join(keep).decode("utf-8", "replace")


# --------------------------------------------------------------------------
# heading text and anchors
# --------------------------------------------------------------------------

_ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\]\\^_`{|}~])")
_CODESPAN_TXT = re.compile(r"(`+)(.+?)\1")
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_REFLINK = re.compile(r"\[([^\]]*)\]\[[^\]]*\]")
_TAG = re.compile(r"</?[a-zA-Z][^>]*>")


def render_inline(text: str) -> str:
    """
    The reader-visible text of an inline run: escapes resolved, code spans
    unwrapped, links and images reduced to their labels, HTML tags removed,
    entities decoded. This — not the raw markup — is what the renderer slugs,
    which is why `[some\\_user](https://x.com/some_user)` must become
    `some_user` before an anchor is derived from it, and not
    `some-userhttpsxcomsome-user`, which is what slugging the raw markup gives.
    """
    text = _ESCAPE.sub(r"\1", text)
    text = _CODESPAN_TXT.sub(r"\2", text)
    text = _IMAGE.sub(r"\1", text)
    text = _LINK.sub(r"\1", text)
    text = _REFLINK.sub(r"\1", text)
    text = _TAG.sub("", text)
    return html.unescape(text)


def heading_text(raw: bytes) -> str:
    """
    Rendered heading text, for breadcrumbs, indexes and anchors. Byte-exact
    quoting is display_text's job; this one's job is to read the way the
    published page reads.
    """
    text = raw.decode("utf-8", "replace").strip()
    text = CLOSING_HASHES.sub("", text)
    return " ".join(render_inline(text).split())


# A heading that is nothing but a GitBook page-mention link renders with no
# literal text at slug time, and GitBook's slugger emits the string
# "undefined" for it, literally String(undefined), numbered like any other
# duplicate. Seven live headings do this, all on one navigation page, one of
# them behind a stray backslash-space the renderer also ignores. Matching the
# renderer means matching its artifacts; a citation fragment that does not
# say "undefined" does not resolve.
MENTION_ONLY = re.compile(rb'^\s*(?:\\\s+)*\[[^\]]+\]\([^)"]*"mention"\)\s*$')


def assign_anchors(headings) -> dict[int, str | None]:
    """
    Anchor per heading offset, exactly as the renderer assigns them: over
    every rendered heading in order, duplicates suffixed -1, -2, ...; None
    for level-1 headings (the page title carries no id) and for headings that
    slug to nothing. The single authority — chunk_file and tools/verify_anchors.py
    both call this, so the corpus and the checker cannot drift apart.
    """
    anchor_of: dict[int, str | None] = {}
    seen: dict[str, int] = {}
    for off, level, raw in headings:
        if level < 2:
            anchor_of[off] = None
            continue
        if MENTION_ONLY.match(raw):
            base = "undefined"
        else:
            text = heading_text(raw)
            base = gitbook_id(text) if text else ""
        if not base:
            anchor_of[off] = None
            continue
        n = seen.get(base, 0)
        seen[base] = n + 1
        anchor_of[off] = base if n == 0 else f"{base}-{n}"
    return anchor_of


def gitbook_id(text: str) -> str:
    """
    The anchor the GitBook renderer derives from a heading's rendered text.

    Fitted empirically against every heading id a rendered GitBook site
    serves, and re-verified by `tools/verify_anchors.py` — not taken from a slug
    library, because no library surveyed reproduces this exact behaviour. The observed rules: lowercase; `&` -> `and`; `$` -> `usd`;
    apostrophes vanish without a separator; every other run outside
    `[a-z0-9_.]` collapses to one `-`; leading and trailing `-` are trimmed;
    an id starting with a digit is prefixed `id-`; the result is cut at 100
    characters and any `-` or `.` left dangling by the cut is trimmed.
    Duplicates within a page are suffixed `-1`, `-2`, ... in render order —
    the caller counts them, over every rendered heading, not merely over the
    ones that survive chunking.
    """
    s = text.lower()
    s = s.replace("&", "and").replace("$", "usd")
    s = s.replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9_.]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    if s[:1].isdigit():
        s = "id-" + s
    return s[:100].rstrip("-.")


# --------------------------------------------------------------------------
# SUMMARY.md cross-document hierarchy
# --------------------------------------------------------------------------

SUMMARY_ENTRY = re.compile(r"^(\s*)\*\s+\[([^\]]*)\]\(([^)]+)\)")
SUMMARY_PART = re.compile(r"^##\s+(.*)$")


def parse_summary(path: pathlib.Path) -> dict[str, list[str]]:
    """
    Map each document path to the titles of its ancestors in the GitBook nav.

    Without this a page knows its own headings and nothing else, so
    `day-to-day-usage/deposits.md` has no idea it sits under "User Guide".
    """
    hierarchy: dict[str, list[str]] = {}
    stack: list[tuple[int, str]] = []
    part: str | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").split("\n"):
        p = SUMMARY_PART.match(line)
        if p:
            part = p.group(1).strip()
            stack = []
            continue
        m = SUMMARY_ENTRY.match(line)
        if not m:
            continue
        indent, title, target = len(m.group(1)), m.group(2).strip(), m.group(3)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        ancestors = ([part] if part else []) + [t for _, t in stack]
        target = target.split("#")[0].strip()
        if target.endswith(".md"):
            hierarchy[target] = ancestors
        stack.append((indent, title))
    return hierarchy


# --------------------------------------------------------------------------
# chunking
# --------------------------------------------------------------------------

def chunk_file(path: pathlib.Path, root: pathlib.Path,
               min_chars: int = 40,
               hierarchy: dict[str, list[str]] | None = None) -> list[Chunk]:
    blob = path.read_bytes()
    rel = str(path.relative_to(root))
    front, body_start = split_frontmatter(blob)
    strong_sections: list[tuple[int, bytes]] = []
    headings, comments = scan_structure(blob, body_start, strong_sections)
    # Mixed documents already have authoritative renderer boundaries. A bold
    # paragraph within one of those sections may be a parameter label, callout
    # or signature field rather than a new topic. The reviewed convention is
    # limited to headingless notes whose visible structure consists of
    # repeated strong titles (Known Issues is the motivating pinned source).
    if headings:
        strong_sections = []
    ancestors = (hierarchy or {}).get(rel, [])

    # Anchors are assigned over every rendered heading, in order, before any
    # size filtering. The renderer numbers duplicates over what it renders,
    # including H5s and short sections. Both failures have been
    # observed: anchors slugged from raw markup, and duplicate numbering that
    # skipped headings the size filter later discarded.
    anchor_of = assign_anchors(headings)

    # Strong section titles have no renderer anchor. Give each one a logical
    # level immediately below the active real heading, or level 1 in a
    # headingless note. This preserves useful breadcrumbs without inventing a
    # fragment identifier that GitBook does not serve.
    boundary: list[tuple[int, int, bytes, str | None, str]] = []
    active: dict[int, str] = {}
    strong_by_offset = dict(strong_sections)
    for off, kind, payload in sorted(
            [(o, "heading", (l, r)) for o, l, r in headings
             if l <= MAX_HEADING_LEVEL]
            + [(o, "strong", raw) for o, raw in strong_sections],
            key=lambda item: item[0]):
        if kind == "heading":
            level, raw = payload
            active[level] = heading_text(raw)
            for deeper in [k for k in active if k > level]:
                active.pop(deeper)
            boundary.append((off, level, raw, anchor_of[off], "heading"))
        else:
            raw = strong_by_offset[off]
            level = min((max(active) + 1) if active else 1,
                        MAX_HEADING_LEVEL)
            boundary.append((off, level, raw, None, "strong"))

    spans: list[tuple[int, int, int, str, str | None, str]] = []
    if boundary and boundary[0][0] > body_start:
        spans.append((body_start, boundary[0][0], 0, "", None, "intro"))
    elif not boundary:
        spans.append((body_start, len(blob), 0, "", None, "intro"))
    for i, (off, level, raw, anchor, style) in enumerate(boundary):
        end = boundary[i + 1][0] if i + 1 < len(boundary) else len(blob)
        spans.append((off, end, level, heading_text(raw), anchor, style))

    # Chunk IDs are counted over the same pre-filter span list, so which ID a
    # section gets does not depend on whether its earlier namesake happened to
    # clear the size filter.
    seen_ids: dict[str, int] = {}
    uids: list[str] = []
    for start, end, level, text, anchor, style in spans:
        base = f"{rel}#{anchor or (gitbook_id(text) or 'section') if text else 'intro'}"
        n = seen_ids.get(base, 0)
        seen_ids[base] = n + 1
        uids.append(base if n == 0 else f"{base}-{n + 1}")

    chunks: list[Chunk] = []
    trail: dict[int, str] = {}

    for (start, end, level, text, anchor, style), uid in zip(spans, uids):
        # The trail is updated BEFORE the size filter. Doing it after meant a
        # heading whose own body was too short never entered the trail, so its
        # descendants inherited their grandparent instead. This gave 309 of
        # 452 live chunks the wrong ancestry.
        if level:
            trail[level] = text
            for deeper in [k for k in list(trail) if k > level]:
                trail.pop(deeper)

        body = blob[start:end].decode("utf-8", "replace")
        model = strip_invisible_spans(blob, start, end, comments)
        # A section with no visible content, such as an all-comment section,
        # quotes nothing while still taking an index slot and a citation.
        if not model.strip():
            continue
        if len(body.strip()) < min_chars:
            continue

        heading_path = [v for _, v in sorted(trail.items())]
        breadcrumb = " › ".join([rel] + ancestors + heading_path)

        chunks.append(Chunk(
            id=uid,
            kind="section",
            source_type="markdown",
            path=rel,
            line=line_number(blob, start),
            breadcrumb=breadcrumb,
            display_text=body,
            model_text=model,
            embed_text=f"{breadcrumb}\n\n{model}",
            tier="B",
            detail={
                "heading": text,
                "heading_level": level,
                "heading_path": heading_path,
                "nav_path": ancestors,
                "anchor": anchor,
                "boundary_style": style,
                "description": front.get("description"),
                "effective_date": front.get("effective_date"),
                "doc_version": front.get("doc_version"),
            },
        ))

    # A document too small to clear the section filter is still a document.
    # A short headingless note listed by the navigation file once produced nothing at
    # all, while coverage reported it as placed anyway. The size
    # filter suppresses noise chunks within a document. When no section
    # survives, the whole body becomes the chunk.
    if not chunks:
        whole = blob[body_start:].decode("utf-8", "replace")
        whole_model = strip_invisible_spans(blob, body_start, len(blob),
                                             comments)
        # A heading-only navigation stub has no evidence beyond structure. Its
        # synthesised document index preserves that structure; emitting the raw
        # heading again creates a tiny retrieval result such as ``# /market``.
        # Keep genuinely short prose documents, but do not mistake ATX headings
        # and thematic separators for prose.
        substantive = "\n".join(
            line for line in whole_model.splitlines()
            if line.strip()
            and not re.match(r"^ {0,3}#{1,6}(?:[ \t]+|$)", line)
            and not THEMATIC.match(line.encode("utf-8")))
        if substantive.strip():
            chunks.append(Chunk(
                id=f"{rel}#document",
                kind="section",
                source_type="markdown",
                path=rel,
                line=line_number(blob, body_start),
                breadcrumb=" › ".join([rel] + ancestors),
                display_text=whole,
                model_text=whole_model,
                embed_text=f"{' › '.join([rel] + ancestors)}\n\n{whole_model}",
                tier="B",
                detail={
                    "heading": "",
                    "heading_level": 0,
                    "heading_path": [],
                    "nav_path": ancestors,
                    "anchor": None,
                    "description": front.get("description"),
                    "effective_date": front.get("effective_date"),
                    "doc_version": front.get("doc_version"),
                    "whole_document": True,
                },
            ))

    # A document with headings is worth indexing even when no single section
    # clears the size filter. An earlier version dropped five navigation pages.
    if chunks or headings or strong_sections or front.get("description"):
        chunks.append(document_index(rel, front, headings, ancestors,
                                     line_number(blob, body_start),
                                     strong_sections=strong_sections))
    return chunks


def document_index(rel, front, headings, ancestors, line,
                   strong_sections=()) -> Chunk:
    """
    One synthesised chunk per document listing its headings.

    "What does the user guide cover" is not answerable from any single
    section, in the same way "what can I call on MyContract" is not
    answerable from any single function. Assembled, so it is flagged.
    """
    lines = [f"{'  ' * (lvl - 1)}{heading_text(raw)}" for _, lvl, raw in headings]
    lines.extend(heading_text(raw) for _, raw in strong_sections)
    desc = front.get("description") or ""
    nav = " › ".join(ancestors)
    body = (f"{rel} — contents\n\n"
            + (f"{nav}\n\n" if nav else "")
            + (desc + "\n\n" if desc else "")
            + "\n".join(lines))
    breadcrumb = " › ".join([rel] + ancestors + ["contents"])
    return Chunk(
        id=f"{rel}#index",
        kind="index",
        source_type="markdown",
        path=rel,
        line=line,
        breadcrumb=breadcrumb,
        display_text=body,
        model_text=body,
        embed_text=body,
        tier="B",
        synthesised=True,
        detail={"description": front.get("description"),
                "effective_date": front.get("effective_date"),
                "doc_version": front.get("doc_version"),
                "nav_path": ancestors,
                "heading_count": len(headings) + len(strong_sections),
                "strong_section_count": len(strong_sections)},
    )


_GLOB_CACHE: dict[str, re.Pattern] = {}


def glob_match(rel: str, pattern: str) -> bool:
    """
    Path-aware glob matching: `**` spans directory separators, `*` does not.

    `fnmatch` does not make that distinction — its `*` happily crosses `/`, so
    an include of `*.md` also selects `elsewhere/other.md`, and a manifest that
    means "the markdown at the root of this repo" quietly means "all of it".
    A trailing `/**` also matches the directory itself, which is what an
    exclusion like `skills/**` is understood to mean.
    """
    rx = _GLOB_CACHE.get(pattern)
    if rx is None:
        out, i, n = [], 0, len(pattern)
        while i < n:
            if pattern.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif pattern.startswith("**", i):
                out.append(".*")
                i += 2
            elif pattern[i] == "*":
                out.append("[^/]*")
                i += 1
            elif pattern[i] == "?":
                out.append("[^/]")
                i += 1
            else:
                out.append(re.escape(pattern[i]))
                i += 1
        rx = _GLOB_CACHE[pattern] = re.compile("^" + "".join(out) + r"/?$")
    return rx.match(rel) is not None


def _reject_symlink(path: pathlib.Path, base: pathlib.Path) -> None:
    """
    A symlinked Markdown file reads bytes the pinned ref does not describe.

    `source_ref` pins the link's *target string*, not the content behind it, so
    the same corpus build on another machine can produce different text under
    the same citation. Pointing `terms.md` at a file outside the tree yields a
    clean chunk with a byte-exact promise attached to it.
    """
    if path.is_symlink():
        raise ChunkError(
            f"{path} is a symlink. Its bytes are not pinned by the corpus ref, "
            "so a citation to it is not reproducible. Replace it with the file "
            "itself, or exclude it.")
    try:
        path.resolve().relative_to(base.resolve())
    except ValueError:
        raise ChunkError(
            f"{path} resolves to {path.resolve()}, outside the corpus root "
            f"{base.resolve()} — most likely through a symlinked directory.")


def chunk_tree(root: str, excludes: list[str],
               summary: str | None = None,
               includes: list[str] | None = None) -> list[Chunk]:
    """
    `includes` is the allowlist half of the filter: include, then exclude.
    Without it this chunker takes every `*.md` under the root and cannot express
    a source list that names specific documents, so in-scope files scattered
    among out-of-scope ones go unchunked with nothing to show for it. Empty
    means everything, and a glob that matches nothing is fatal, on the same
    reasoning as the Solidity side: a silently-empty selection is how a rename
    removes half a corpus.
    """
    base = pathlib.Path(root)
    if not base.is_dir():
        raise ChunkError(f"--root {root} is not a directory")

    hierarchy: dict[str, list[str]] = {}
    if summary:
        sp = pathlib.Path(summary)
        if not sp.is_absolute():
            sp = base / summary
        if sp.exists():
            _reject_symlink(sp, base)
        if not sp.exists():
            # Requested navigation that cannot be read is a broken build, not
            # a degraded one. An earlier version warned and carried on, so a
            # typo'd path silently produced a corpus where no document knew
            # where it sat. Building without a hierarchy remains available by
            # passing --summary ''.
            raise ChunkError(
                f"{sp} not found — the SUMMARY hierarchy was requested and is "
                "missing. Pass --summary '' to build without one, deliberately.")
        hierarchy = parse_summary(sp)
        print(f"  {len(hierarchy)} document(s) in {sp.name}")

    out: list[Chunk] = []
    included: list[str] = []
    skipped = 0
    glob_hits: dict[str, int] = {g: 0 for g in (includes or [])}
    for path in sorted(base.rglob("*.md")):
        rel = str(path.relative_to(base))
        if includes:
            matched = [g for g in includes if glob_match(rel, g)]
            if not matched:
                skipped += 1
                continue
            for g in matched:
                glob_hits[g] += 1
        if any(glob_match(rel, g) or rel.startswith(g.rstrip("*"))
               for g in excludes):
            skipped += 1
            continue
        _reject_symlink(path, base)
        included.append(rel)
        out.extend(chunk_file(path, base, hierarchy=hierarchy))
    print(f"  skipped {skipped} excluded file(s)")
    unmatched = [g for g, n in glob_hits.items() if n == 0]
    if unmatched:
        raise ChunkError(
            "include pattern(s) matched no markdown under "
            f"{root}: {', '.join(repr(g) for g in unmatched)}")

    # Coverage is computed from documents that actually produced chunks, not
    # from filenames discovered before chunking. The latter certified a file as
    # placed in the navigation while emitting nothing for it.
    emitted = {c.path for c in out}
    dropped = [r for r in included if r not in emitted]
    if dropped:
        print(f"  DROPPED       : {len(dropped)} included file(s) produced no "
              "chunks — no reader-visible content:")
        for r in dropped[:10]:
            print(f"      {r}")

    if hierarchy:
        placed = [r for r in included if r in hierarchy and r in emitted]
        unplaced = [r for r in included if r not in hierarchy and r in emitted]
        dangling = [t for t in hierarchy if t not in emitted]
        if not placed:
            raise ChunkError(
                "the SUMMARY hierarchy placed zero of the included documents "
                "— wrong summary for this tree, or wrong --root")
        print(f"  hierarchy     : {len(placed)}/{len(emitted)} emitted "
              f"document(s) placed ({len(included)} included)")
        if unplaced:
            print(f"  unplaced      : {len(unplaced)} included file(s) not in "
                  "the SUMMARY nav — indexed without ancestry:")
            for r in unplaced[:5]:
                print(f"      {r}")
        if dangling:
            print(f"  dangling nav  : {len(dangling)} SUMMARY entr(ies) point "
                  "at files that are excluded, missing or emitted nothing:")
            for t in dangling[:5]:
                print(f"      {t}")

    if not out:
        raise ChunkError(f"zero chunks from {root} — refusing to call an "
                         "empty corpus a successful build")
    return out


# --------------------------------------------------------------------------

def excludes_from_manifest(manifest_path: str, source_id: str) -> list[str]:
    """
    Read the exclude list out of a YAML source list rather than taking it on
    the command line.

    Hand-passed excludes are how `AGENTS.md` ends up in a corpus: omit it once
    and agent-directed instructions go straight in. Exclusion lists rot
    silently, and a list that has to be retyped at every invocation rots faster
    than most. The file needs a `sources:` list whose entries carry an `id` and
    an `exclude` list; nothing else in it is read.
    """
    try:
        import yaml
    except ImportError:
        sys.exit("--manifest needs pyyaml (pip install pyyaml)")
    doc = yaml.safe_load(open(manifest_path))
    for src in doc.get("sources", []):
        if src.get("id") == source_id:
            return list(src.get("exclude", []))
    sys.exit(f"no source {source_id!r} in {manifest_path}")


# --------------------------------------------------------------------------
# corpus provenance: what the pipeline records beside the chunks
# --------------------------------------------------------------------------

PROVENANCE_FILENAME = "provenance.jsonl"
# Every markdown file under --root is a candidate; --exclude narrows it. This
# is the pattern that selection actually is, not a label for it.
INCLUDE_PATTERN = "**/*.md"
# The two fields stamp() writes onto every chunk. The build identifier digests
# everything else, because an identifier that is stamped onto the chunks it
# digests cannot also cover itself.
_STAMPED = ("source_ref", "corpus_build_id")


def skill_version() -> str:
    """The governed version of the lemma skill, read rather than repeated.

    A version copied into this file is a version that can drift from the one
    the promise machine governs, and a record carrying a drifted version is a
    guess wearing the shape of a fact. It is read from the skill's frontmatter,
    which travels beside this chunker in the plugin and in the portable
    runtime alike.
    """
    manifest = (pathlib.Path(__file__).resolve().parent.parent
                / "skills" / "lemma" / "SKILL.md")
    text = manifest.read_text(encoding="utf-8") if manifest.is_file() else ""
    found = re.search(r'^  version: "([^"]+)"$', text, re.M)
    if not found:
        raise ChunkError(
            f"no governed version in {manifest} — the record states which "
            "chunker built the corpus and there is nothing here to state")
    return found.group(1)


def corpus_build_id(records: list[dict]) -> str:
    """Digest the chunks as the chunker produced them, less the stamped pair.

    Keys are sorted so the digest survives a change in field order, and each
    record ends with a newline so two adjacent chunks cannot be reshuffled into
    the same bytes.
    """
    digest = hashlib.sha256()
    for record in records:
        bare = {k: v for k, v in record.items() if k not in _STAMPED}
        digest.update(json.dumps(bare, sort_keys=True).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _same_file(left: pathlib.Path, right: pathlib.Path) -> bool:
    """Whether two paths name one file, by inode wherever that can be known.

    resolve() settles a relative spelling, a `.` or `..` segment and every
    symlink, in either direction. It cannot settle a hard link, which is a
    second name for one inode and resolves to itself, so a corpus reachable
    under two names would be written and then overwritten by its own record.
    Where both names exist the inode answers; where one does not there is
    nothing to stat, and the path is the honest bound.
    """
    if left.resolve() == right.resolve():
        return True
    try:
        return left.samefile(right)
    except OSError:
        return False


def _records_beside(directory: pathlib.Path,
                    keep: tuple[pathlib.Path, ...]) -> list[pathlib.Path]:
    """Provenance records already in the corpus's directory, less `keep`.

    A record left in the directory of a corpus it does not describe is the
    failure this refusal exists to prevent, and the name it carries makes no
    difference to a reader who finds it there. Guarding only the default name
    would leave that failure one --provenance away.

    Bounded on purpose: regular files, their first line, and its first 4096
    bytes. The record is one line of line-delimited JSON carrying a known
    schema string, so that is enough to recognise one and cheap enough to do
    before every delivery -- two thousand neighbours cost under a tenth of a
    second. The suffix is not part of the bound, because --provenance writes
    wherever it is pointed and a record this tool put in rec.json is the same
    record to a reader who finds it beside a corpus it does not describe.

    A neighbour that cannot be read is a neighbour that cannot be ruled out,
    so it refuses rather than being passed over. Everything else here records
    what it could not establish as an absence with a reason; a scan that
    skipped what it could not open would be the one place that guessed.

    A first line that parses as JSON but is not an object is not a record and
    is not a crash either: a list, a string, a number and a bare null each
    took this function down with an AttributeError before the type was
    checked, which is the shape the validator was taught to avoid in step 1.
    """
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        return []
    spared = []
    for path in keep:
        try:
            spared.append(path.resolve())
        except OSError:
            pass
    found = []
    for entry in entries:
        try:
            if entry.resolve() in spared or not entry.is_file():
                continue
            with open(entry, "rb") as handle:
                head = handle.readline(4096)
        except OSError as problem:
            raise ChunkError(
                f"{entry} sits in the directory this corpus is delivered to "
                f"and cannot be read ({problem}), so whether it is a record "
                "of some other corpus cannot be established") from problem
        try:
            first = json.loads(head)
        except ValueError:
            continue
        if (isinstance(first, dict)
                and first.get("schema") == _schema.PROVENANCE_SCHEMA):
            found.append(entry)
    return found


def record_path(args) -> str:
    """Where the record goes, settled before anything reaches disk.

    Both refusals here describe the same outcome from two directions: a
    directory a capture reads as a whole corpus, holding a record that
    describes different chunks. Neither is caught downstream, because the
    recomputed identifier only ever compares a record with the corpus of its
    own run.

    A record written over the corpus destroys it. The digest check has already
    passed by the time the record is written, so the run reports success and
    the directory is left holding one file: a record naming a chunk count and
    an identifier for chunks that now exist nowhere.

    A record sent elsewhere while `provenance.jsonl` already sits beside
    `--out` leaves that older file describing chunks this run overwrites. It
    stays valid on its own terms — every field well formed, the identifier a
    real digest of a real corpus — so `validate_provenance` returns nothing
    and only recomputing the digest reveals it, which is the work the record
    exists to save.
    """
    out = pathlib.Path(args.out)
    default = out.parent / PROVENANCE_FILENAME
    chosen = pathlib.Path(args.provenance) if args.provenance else default
    if _same_file(chosen, out):
        raise ChunkError(
            f"--provenance {chosen} is the file --out names; the record would "
            "be written over the corpus it describes, leaving a chunk count "
            "for chunks nobody could read")
    stale = _records_beside(out.parent, keep=(chosen, out))
    if stale:
        raise ChunkError(
            f"{stale[0]} already describes a corpus in {out.parent} and this "
            f"run writes its record to {chosen}, so the older record would be "
            "left beside chunks it does not describe; remove it, or let this "
            "record go to it")
    return str(chosen)


def _pairs(flag: str, items: list[tuple[str, str]]) -> str:
    """One `key=value,key=value` flag, or a refusal printed in its place.

    `ariadne.py:132` splits these on commas and keeps the last value it sees
    for a key, so a comma inside a recorded ref, path or pattern does not
    arrive there as a key that parser rejects. It arrives as a second `name=`
    or `end=` overriding the one composed here, and the capture then succeeds
    describing a corpus other than the one on disk. That grammar has no
    escape, so the flag is refused rather than printed wrong, and the refusal
    is shaped to break the command if it is pasted anyway.
    """
    carried = [value for _, value in items if "," in value]
    if carried:
        return (f"{flag} REFUSED {shlex.quote(carried[0])} carries a comma, "
                f"which ariadne.py:132 reads as another key=value pair; "
                f"compose this {flag} by hand")
    return flag + " " + shlex.quote(
        ",".join(f"{key}={value}" for key, value in items))


def capture_flags(record: dict, out: str) -> list[str]:
    """The `capture-dataset` flags for the corpus that was just written.

    The operator's next command is Ariadne's, and every value it needs about
    this corpus is already known here. Composing the flags by hand is where
    the seam leaks: the coverage bounds are a count over a sorted list, the
    gaps are the runs that list omits, and neither is work worth doing twice.

    Everything but the release directory is read from the record, so the
    locator printed is the stripped ref rather than the one that was typed,
    and no path, pattern or version the record does not hold can appear here.
    The release is the directory `--out` names, made absolute against the
    working directory the chunker ran in. A relative `--out` would otherwise
    print a release that names whichever directory the capture is run from,
    and the capture is documented to run from `--root` rather than from here,
    so the two would be the same string and a different corpus.

    Coverage reads the source unit dimension: the bounds are the 1-based index
    range over the sorted units the input declared, and each run of excluded
    units is a gap naming the include patterns the selection was made under.
    An interval printed with no gaps reads as complete, which is the reading
    `predicates/dataset.py:385` refuses, so an excluded unit is named rather
    than dropped from an interval that would then describe the whole input.

    Neither `--release` nor the corpus filename is recorded, so nothing
    downstream compares the release this prints against the record beside the
    chunks. What that costs is in the promise's boundary rather than here.
    """
    selection = record["selection"]
    present = selection["units_present"]
    excluded = set(selection["units_excluded"])
    include = " ".join(selection["include"])

    gaps: list[list[int]] = []
    for index, unit in enumerate(present, 1):
        if unit not in excluded:
            continue
        if gaps and gaps[-1][1] == index - 1:
            gaps[-1][1] = index
        else:
            gaps.append([index, index])

    flags = [
        f"--release {shlex.quote(str(pathlib.Path(out).absolute().parent))}",
        "--producer-tool lemma",
        f"--producer-version {shlex.quote(record['chunker_version'])}",
        "--producer-command python3",
        f"--producer-command chunkers/{record['chunker']}.py",
        "--parameter " + shlex.quote(f"include={include}"),
        "--coverage-dimension 'source unit'",
        "--coverage-start 1",
        f"--coverage-end {len(present)}",
    ]
    for start, end in gaps:
        flags.append(_pairs("--gap", [
            ("start", str(start)),
            ("end", str(end)),
            ("reason", "present in the input and not selected under include "
                       f"{include}")]))
    for entry in record["inputs"]:
        flags.append(_pairs("--input", [
            ("name", entry["path"]),
            ("locator", record["source_ref"]),
            ("file", entry["path"])]))
    return flags


def deliver(chunks: list[Chunk], args) -> None:
    """Write the corpus and the record of what produced it.

    The order is the substance. The record is built and validated before
    anything reaches disk, so a run that cannot produce a complete one leaves
    no directory a capture would read as a whole corpus. The chunks are then
    stamped with the values the record carries — the stripped ref, not the raw
    one — so the two files cannot disagree about the origin. The identifier is
    recomputed from the file that was actually written, and a disagreement
    takes the corpus away rather than delivering it beside a record describing
    chunks nobody wrote.
    """
    base = pathlib.Path(args.root)
    selected = sorted({c.path for c in chunks})
    record = _schema.provenance_record(
        chunker="markdown",
        chunker_version=skill_version(),
        source_ref=args.source_ref,
        corpus_build_id=corpus_build_id([c.to_dict() for c in chunks]),
        chunk_count=len(chunks),
        inputs=[{"path": unit,
                 "sha256": hashlib.sha256(
                     (base / unit).read_bytes()).hexdigest()}
                for unit in selected],
        include=[INCLUDE_PATTERN],
        units_present=sorted(str(path.relative_to(base))
                             for path in base.rglob("*.md")),
        units_selected=selected,
        # No compiler produces a markdown corpus. Recording that as an absence
        # with a reason is the whole difference between a fact and a guess:
        # `unknown` here would be indistinguishable from a compiler by that
        # name.
        compiler=_schema.compiler_absent(
            "the markdown chunker parses text; no compiler takes part in "
            "building this corpus"))
    faults = _schema.validate_provenance(record)
    if faults:
        raise ChunkError("the provenance record is incomplete, so nothing was "
                         "written:\n  " + "\n  ".join(faults))

    path = record_path(args)
    _schema.stamp(chunks, source_ref=record["source_ref"],
                  corpus_build_id=record["corpus_build_id"])
    with open(args.out, "w") as f:
        for c in chunks:
            f.write(json.dumps(c.to_dict()) + "\n")
    print(f"  written       : {args.out}")

    with open(args.out) as f:
        on_disk = [json.loads(line) for line in f]
    if corpus_build_id(on_disk) != record["corpus_build_id"]:
        pathlib.Path(args.out).unlink()
        raise ChunkError(
            f"{args.out} does not digest to the identifier the record carries, "
            "so the corpus has been removed rather than delivered beside a "
            "record describing chunks nobody wrote")

    # The corpus is on disk and the record is not. Everything from here takes
    # the corpus with it if it fails, for the reason the unlink above exists:
    # a chunks.jsonl with nothing beside it to say what produced it is the
    # directory the pair of files was introduced to prevent.
    try:
        with open(path, "w") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as e:
        pathlib.Path(args.out).unlink()
        raise ChunkError(
            f"the record could not be written to {path} ({e}), so the corpus "
            f"at {args.out} has been removed rather than left behind with "
            "nothing beside it to say what produced it") from e
    print(f"  provenance    : {path}")
    print("  capture flags : hand these to ariadne capture-dataset")
    for flag in capture_flags(record, args.out):
        print(f"      {flag}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="markdown tree to chunk")
    ap.add_argument("--manifest", help="read excludes from manifest.yaml")
    ap.add_argument("--source", default="docs",
                    help="which manifest source to read excludes from")
    ap.add_argument("--exclude", action="append", default=[],
                    help="additional glob or path prefix; repeatable")
    ap.add_argument("--summary", default="SUMMARY.md",
                    help="GitBook nav to derive cross-document hierarchy from. "
                         "Missing is fatal; pass '' to build without one")
    ap.add_argument("--out", help="JSONL output")
    ap.add_argument("--source-ref", metavar="REF",
                    help="what was chunked: a tag, a commit or a URL. Required "
                         "with --out. Recorded as given, less any URL "
                         "userinfo; nothing resolves or checks it")
    ap.add_argument("--provenance", metavar="PATH",
                    help=f"where to write the provenance record; defaults to "
                         f"{PROVENANCE_FILENAME} beside --out")
    args = ap.parse_args()

    # Before the tree is walked and before anything is written: a corpus
    # delivered with no origin is the defect this record exists to close, and
    # refusing late would leave a directory behind.
    if args.out and not args.source_ref:
        print("\nFATAL: --out was given without --source-ref, so nothing was "
              "written.\n  A corpus with no recorded origin is one nobody can "
              "check afterwards.\n  Pass --source-ref with the tag, commit or "
              "URL that was chunked.", file=sys.stderr)
        return 1

    excludes = list(args.exclude)
    if args.manifest:
        excludes += excludes_from_manifest(args.manifest, args.source)
        print(f"  {len(excludes)} exclusion(s) from {args.manifest}")
    elif not excludes:
        print("  WARNING: no excludes and no --manifest. Everything under "
              "--root will be indexed, including any agent instruction files.",
              file=sys.stderr)

    try:
        chunks = chunk_tree(args.root, excludes, args.summary or None)
    except ChunkError as e:
        print(f"\nFATAL: {e}", file=sys.stderr)
        return 1
    problems = _schema.validate(chunks)

    docs = len({c.path for c in chunks})
    sizes = sorted(len(c.model_text) for c in chunks) or [0]
    placed = sum(1 for c in chunks if c.detail.get("nav_path"))
    print(f"{len(chunks)} chunks from {docs} document(s)")
    print(f"  synthesised   : {sum(1 for c in chunks if c.synthesised)}"
          f"  (not quotable as source)")
    print(f"  nav hierarchy : {placed} chunks placed in the SUMMARY tree")
    print(f"  size          : median {sizes[len(sizes)//2]}, "
          f"p99 {sizes[int(0.99*len(sizes))]}, max {sizes[-1]}")
    print(f"  schema        : {len(problems)} problem(s)"
          + ("  <-- FATAL" if problems else ""))
    for p in problems[:5]:
        print(f"      {p}")

    if args.out and not problems:
        try:
            deliver(chunks, args)
        except (ChunkError, ValueError, OSError) as e:
            print(f"\nFATAL: {e}", file=sys.stderr)
            return 1
    elif args.out:
        print("  NOT WRITTEN   : refusing to emit a corpus that fails its checks")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
