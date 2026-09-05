"""Markdown outline extraction for Horos's map verb.

The extractor shape fixed five times, sized for prose: a line-oriented
scanner over CommonMark's block rules, never its inline ones. It slices
verbatim, confesses what it does not read, and never imports or executes
what it reads. Stdlib only.

What "outline" means for a Markdown file, for an agent orienting in a prose
file: its headings with level, line and verbatim text; its fenced code
blocks with info string and line range; a front-matter block by line
range; and a confession, by line range, of every region the outliner did
not read, which is each raw HTML block and the remainder after a fence that
never closes. A "declaration" is a heading or a fence. Link reference
definitions are not outlined.

Rules applied per line, with open containers (blockquote markers and
list-item content indents) stripped first so a heading or fence inside a
container is still seen:

- ATX headings, one to six `#` then a space, indented up to three spaces;
  closing hashes dropped. Setext headings: an open paragraph followed by
  `=` (h1) or `-` (h2) underline at the same container depth; a lazy
  continuation line never takes an underline.
- Fenced code blocks, backtick or tilde, three or more characters, indented
  up to three spaces; a backtick fence's info string may not hold a
  backtick; the closer is the same character at least as long with nothing
  after it. A fence inside a container closes when the container does.
- Front matter: `---` on line 1 closed by `---` or `...`, named by range.
- Raw HTML blocks of the seven CommonMark start kinds are confessed by
  line range; the seventh kind cannot interrupt a paragraph.
- Indented code and thematic breaks are skipped; everything else is
  paragraph text.

The register, pinned by plugins/horos/examples/fixture-md/GUIDE.md:

    module: <text of the first h1, or (no title)>
    front matter: lines 1-N            (only when present)
    # Title  (line 12)
        ## Section  (line 17)
            ``` bash  (lines 37-39)
        Setext title  (setext h2)  (line 40)
    lexer: unterminated fence at line N (only when one never closed)
    declarations: N
    unparsed: K region(s): lines a-b, line c

A heading is its verbatim line indented four spaces per level below one; a
fence sits one level under the heading above it with its info string and
line range; a setext heading prints its paragraph's first line with the
marker. Exit 1 only for an unterminated fence.
"""

import re

# Greedy, so one pass over the line: a lazy `.*?` before a trailing
# `[ \t]*$` re-scans the tail at every step and goes quadratic on a long
# heading line of interior spaces.
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*))?$")
FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
# Matched at a position inside the line, so unanchored: `match(line, pos)`
# never lets `^` match there.
QUOTE = re.compile(r" {0,3}>")
LIST_ITEM = re.compile(r"( {0,3})([-+*]|\d{1,9}[.)])([ \t]+|$)")
SPACES = re.compile(r" *")
INDENTED = re.compile(r"^(?: {4}|\t)")

# List markers that may interrupt a paragraph (a bullet, or an ordered item
# starting at 1).
INTERRUPTING_MARKERS = frozenset({"-", "+", "*", "1.", "1)"})

HTML_BLOCK_NAMES = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|"
    "colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|"
    "footer|form|frame|frameset|h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|"
    "legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|"
    "param|search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|"
    "track|ul"
)

# The seven CommonMark HTML block starts: (start, end-condition or None for
# "ends at a blank line", may interrupt a paragraph). An end condition is a
# literal string where CommonMark gives one, and a pattern only where the
# condition really is a pattern.
HTML_STARTS = (
    (re.compile(r"^ {0,3}<(?:script|pre|style|textarea)(?:[ \t>]|$)", re.I),
     re.compile(r"</(?:script|pre|style|textarea)>", re.I), True),
    (re.compile(r"^ {0,3}<!--"), "-->", True),
    (re.compile(r"^ {0,3}<\?"), "?>", True),
    (re.compile(r"^ {0,3}<![A-Za-z]"), ">", True),
    (re.compile(r"^ {0,3}<!\[CDATA\["), "]]>", True),
    (re.compile(r"^ {0,3}</?(?:" + HTML_BLOCK_NAMES + r")(?:[ \t]|/?>|$)", re.I),
     None, True),
    (re.compile(
        r"^ {0,3}(?:<[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[A-Za-z_:][A-Za-z0-9_.:-]*"
        r"(?:[ \t]*=[ \t]*(?:[^ \t\"'=<>`]+|'[^']*'|\"[^\"]*\"))?)*[ \t]*/?>"
        r"|</[A-Za-z][A-Za-z0-9-]*[ \t]*>)[ \t]*$"), None, False),
)



def _html_block_ends(line, end):
    """True when this line carries the open HTML block's end condition.

    CommonMark states four of the five conditions as literal strings, and a
    pattern object around `-->` says nothing the substring does not. Carrying
    them as strings also stops a static analyser reading the block scanner as
    an HTML sanitiser: a filter that ends a comment at `-->` and not at `--!>`
    can be bypassed, but CommonMark ends a type 2 block at `-->` alone, and
    the differential oracle agrees. See skills#1258.
    """
    if isinstance(end, str):
        return end in line
    return end.search(line) is not None


def _uniform_start(line):
    """The index from which the line holds one non-blank character and
    blanks only, and that character; (0, "") for a blank line."""
    end = len(line.rstrip(" \t"))
    if end == 0:
        return 0, ""
    char = line[end - 1]
    k = end - 1
    while k > 0 and line[k - 1] in (char, " ", "\t"):
        k -= 1
    return k, char


def _thematic(line, pos=0, uniform=None):
    """Whether the line from `pos` is a thematic break: three or more of
    one of `*`, `-` or `_`, blanks between them, indented up to three
    spaces. Not a regex, and answered from the line's uniform tail: the
    repeated-group form backtracks quadratically, and a line of a million
    list markers asks this once per marker."""
    indent = 0
    while indent < 4 and line.startswith(" ", pos + indent):
        indent += 1
    body = pos + indent
    if indent > 3 or body >= len(line) or line[body] not in "*-_":
        return False
    start, char = uniform if uniform is not None else _uniform_start(line)
    if line[body] != char or body < start:
        return False
    return line.count(char, body) >= 3


def _atx_text(content):
    """The heading text after the marker, closing hashes dropped when they
    follow a space or make up the whole text."""
    text = content.strip(" \t")
    core = text.rstrip("#")
    if core != text and (core == "" or core[-1] in " \t"):
        text = core.rstrip(" \t")
    return text


def _strip_containers(line, stack, blank):
    """Strip the open containers' prefixes from the line. Returns
    (remainder, matched_depth): how many of the open containers this line
    continued."""
    pos = 0
    depth = 0
    run_end = -1             # end of the space run starting at pos, once measured
    for kind, indent in stack:
        if kind == "quote":
            m = QUOTE.match(line, pos)
            if not m:
                break
            pos = m.end()
            if line.startswith(" ", pos):
                pos += 1
            run_end = -1
        elif not blank:
            if run_end < pos:
                run_end = SPACES.match(line, pos).end()
            if run_end - pos >= indent:
                pos += indent
            else:
                break
        depth += 1
    return line[pos:], depth


class _Outline:
    def __init__(self, source):
        self.lines = source.split("\n")
        if self.lines and self.lines[-1] == "":
            self.lines.pop()
        self.items = []          # ("heading", level, line, shown) / ("fence", first, last, info)
        self.regions = []        # (first, last) confessed
        self.declarations = 0
        self.title = None
        self.front_matter = 0
        self.errors = []         # (line, reason)

    def confess(self, first, last):
        if self.regions and self.regions[-1][1] >= first - 1:
            self.regions[-1] = (self.regions[-1][0], max(self.regions[-1][1], last))
        else:
            self.regions.append((first, last))

    def run(self):
        lines = self.lines
        n = len(lines)
        i = 0
        if n and lines[0].rstrip("\r") == "---":
            for j in range(1, n):
                if lines[j].rstrip("\r") in ("---", "..."):
                    self.front_matter = j + 1
                    i = j + 1
                    break
        stack = []               # open containers: ("quote", 0) or ("item", indent)
        para = None              # (first_line, sig, text)
        fence = None             # (char, length, first_line, info)
        html = None              # (end condition or None, first_line)
        while i < n:
            raw = lines[i].rstrip("\r").expandtabs(4)
            lineno = i + 1
            blank = raw.strip() == ""
            rest, depth = _strip_containers(raw, stack, blank)
            # A container this line did not continue closes here, and takes
            # any fence or HTML block it holds with it: neither takes a lazy
            # continuation. A blank line keeps a list item open but closes
            # a blockquote it does not mark.
            closes = depth < len(stack) and (not blank or stack[depth][0] == "quote")

            if html is not None:
                end, first = html
                if closes or (end is None and blank):
                    self.confess(first, lineno - 1)
                    html = None
                    stack = stack[:depth]
                else:
                    if end is not None and _html_block_ends(rest, end):
                        self.confess(first, lineno)
                        html = None
                    i += 1
                    continue

            if fence is not None:
                char, length, first, info = fence
                if closes:
                    self.emit_fence(first, lineno - 1, info)
                    fence = None
                    stack = stack[:depth]
                else:
                    m = FENCE.match(rest)
                    if (m and m.group(2)[0] == char and len(m.group(2)) >= length
                            and m.group(3).strip() == ""):
                        self.emit_fence(first, lineno, info)
                        fence = None
                    i += 1
                    continue

            if blank:
                para = None
                # a blank line inside an item is kept; a blank line closes
                # the quotes it did not continue
                for k, (kind, _) in enumerate(stack):
                    if kind == "quote" and k >= depth:
                        stack = stack[:k]
                        break
                i += 1
                continue

            lazy = depth < len(stack)
            if lazy:
                # the line did not continue every open container: either a
                # lazy paragraph continuation or the containers close
                if para is not None and not self.starts_block(rest, True):
                    i += 1
                    continue
                stack = stack[:depth]

            # open new containers on this line, scanning by position: a
            # slice per marker is quadratic on a line of many markers
            sig_changed = lazy
            pos = 0
            end = len(rest.rstrip())
            uniform = None
            while True:
                m = QUOTE.match(rest, pos)
                if m:
                    pos = m.end()
                    if rest.startswith(" ", pos):
                        pos += 1
                    stack.append(("quote", 0))
                    sig_changed = True
                    continue
                m = LIST_ITEM.match(rest, pos)
                if m and not (para is not None and not sig_changed
                              and m.group(2) not in INTERRUPTING_MARKERS):
                    if uniform is None:
                        uniform = _uniform_start(rest)
                    if _thematic(rest, pos, uniform):
                        break
                    marker_end = m.end(2)
                    spaces = SPACES.match(rest, marker_end).end() - marker_end
                    empty = marker_end + spaces >= end
                    if empty or spaces > 4:
                        content = marker_end + 1 - pos
                    else:
                        content = marker_end + spaces - pos
                    stack.append(("item", content))
                    sig_changed = True
                    if empty:
                        pos = end
                        break
                    pos += content
                    continue
                break
            rest = rest[pos:]
            if sig_changed:
                para = None
            sig = tuple(stack)
            if rest.strip() == "":
                i += 1
                continue

            # leaf blocks
            if para is None and INDENTED.match(rest):
                i += 1
                continue

            m = FENCE.match(rest)
            if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
                fence = (m.group(2)[0], len(m.group(2)), lineno, m.group(3).strip())
                para = None
                i += 1
                continue

            m = ATX.match(rest)
            if m:
                text = _atx_text(m.group(2) or "")
                self.emit_heading(len(m.group(1)), lineno, rest.strip(), text)
                para = None
                i += 1
                continue

            # An underline at the paragraph's own depth is a setext heading
            # even after a lazy line; only a lazy underline is refused, above.
            if para is not None and para[1] == sig and SETEXT.match(rest):
                level = 1 if rest.strip()[0] == "=" else 2
                self.emit_heading(level, para[0], para[2], para[2], setext=True)
                para = None
                i += 1
                continue

            if _thematic(rest):
                para = None
                i += 1
                continue

            started = False
            for start, end, interrupts in HTML_STARTS:
                if start.match(rest) and (interrupts or para is None):
                    if end is not None and _html_block_ends(
                        rest[rest.find("<") + 1:], end
                    ):
                        self.confess(lineno, lineno)
                    else:
                        html = (end, lineno)
                    para = None
                    started = True
                    break
            if started:
                i += 1
                continue

            if para is None:
                para = (lineno, sig, rest.strip())
            i += 1

        if fence is not None:
            self.errors.append((fence[2], "unterminated fence"))
            self.confess(fence[2], n)
        if html is not None:
            self.confess(html[1], n)
        return self

    def starts_block(self, rest, para_open):
        """Whether the line would start a new block rather than lazily
        continue the open paragraph."""
        if FENCE.match(rest) or ATX.match(rest) or _thematic(rest) or QUOTE.match(rest):
            return True
        m = LIST_ITEM.match(rest)
        if m and (not para_open or m.group(2) in INTERRUPTING_MARKERS):
            return True
        for start, _, interrupts in HTML_STARTS:
            if interrupts and start.match(rest):
                return True
        return False

    def emit_heading(self, level, lineno, verbatim, text, setext=False):
        self.declarations += 1
        if self.title is None and level == 1:
            self.title = text
        shown = verbatim if not setext else f"{text}  (setext h{level})"
        self.items.append(("heading", level, lineno, shown))

    def emit_fence(self, first, last, info):
        self.declarations += 1
        self.items.append(("fence", first, last, info))


def outline(path, source, out):
    """Print the file's outline; 0 clean, 1 when a fence never closed."""
    walker = _Outline(source).run()
    print(f"module: {walker.title}" if walker.title else "module: (no title)", file=out)
    if walker.front_matter:
        print(f"front matter: lines 1-{walker.front_matter}", file=out)
    level = 0
    for item in walker.items:
        if item[0] == "heading":
            _, level, lineno, shown = item
            print(f"{'    ' * (level - 1)}{shown}  (line {lineno})", file=out)
        else:
            _, first, last, info = item
            label = f"``` {info}" if info else "```"
            print(f"{'    ' * level}{label}  (lines {first}-{last})", file=out)
    for lineno, reason in walker.errors:
        print(f"lexer: {reason} at line {lineno}", file=out)
    print(f"declarations: {walker.declarations}", file=out)
    if walker.regions:
        listed = ", ".join(
            f"lines {a}-{b}" if a != b else f"line {a}" for a, b in walker.regions
        )
        print(f"unparsed: {len(walker.regions)} region(s): {listed}", file=out)
    else:
        print("unparsed: none", file=out)
    return 1 if walker.errors else 0


def declarations(source):
    """Comparison view for a differential against a reference parser:
    headings as [level, line], fences as [first, last], confessed regions
    as [first, last], and whether a fence never closed."""
    walker = _Outline(source).run()
    heads = [[it[1], it[2]] for it in walker.items if it[0] == "heading"]
    fences = [[it[1], it[2]] for it in walker.items if it[0] == "fence"]
    return heads, fences, [list(r) for r in walker.regions], bool(walker.errors)
