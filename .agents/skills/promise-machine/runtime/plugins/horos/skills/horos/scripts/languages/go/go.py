"""Go outline extraction for Horos's map verb.

The TypeScript extractor's shape, sized for a kinder language: no regex
ambiguity, raw strings without escapes, and keyword-led declarations. It
lexes, slices verbatim, confesses what it does not recognise, and never
imports or executes what it reads.
"""

WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)
OPENERS = "([{"
CLOSERS = ")]}"

# A line ending in one of these still owes the next line something, which
# mirrors Go's own semicolon-insertion rule closely enough for slicing.
CONTINUERS = frozenset(",=&|+-*/?:.([{<>!%^")

DECL_KEYWORDS = frozenset({"package", "import", "func", "type", "const", "var"})
GROUPABLE = frozenset({"import", "type", "const", "var"})


def lex(source):
    """Classify the source into spans of code, line_comment, block_comment,
    string (interpreted), raw (backtick) and rune. Returns (spans, errors);
    an unterminated construct's span covers the remainder."""
    spans = []
    errors = []
    n = len(source)
    i = 0
    code_start = 0

    def flush_code(end):
        if end > code_start:
            spans.append(("code", code_start, end))

    while i < n:
        c = source[i]
        if c == "/" and i + 1 < n and source[i + 1] == "/":
            flush_code(i)
            end = source.find("\n", i)
            end = n if end == -1 else end
            spans.append(("line_comment", i, end))
            i = code_start = end
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "*":
            flush_code(i)
            end = source.find("*/", i + 2)
            if end == -1:
                errors.append((i, "unterminated block comment"))
                spans.append(("block_comment", i, n))
                return spans, errors
            spans.append(("block_comment", i, end + 2))
            i = code_start = end + 2
            continue
        if c == '"':
            flush_code(i)
            end = _scan_interpreted(source, i)
            if end is None:
                errors.append((i, "unterminated string"))
                spans.append(("string", i, n))
                return spans, errors
            spans.append(("string", i, end))
            i = code_start = end
            continue
        if c == "`":
            flush_code(i)
            end = source.find("`", i + 1)
            if end == -1:
                errors.append((i, "unterminated raw string"))
                spans.append(("raw", i, n))
                return spans, errors
            spans.append(("raw", i, end + 1))
            i = code_start = end + 1
            continue
        if c == "'":
            flush_code(i)
            end = _scan_rune(source, i)
            if end is None:
                errors.append((i, "unterminated rune literal"))
                spans.append(("rune", i, n))
                return spans, errors
            spans.append(("rune", i, end))
            i = code_start = end
            continue
        i += 1

    flush_code(n)
    return spans, errors


def _scan_interpreted(source, start):
    n = len(source)
    i = start + 1
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == '"':
            return i + 1
        if c == "\n":
            return None
        i += 1
    return None


def _scan_rune(source, start):
    n = len(source)
    i = start + 1
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == "'":
            return i + 1
        if c == "\n":
            return None
        i += 1
    return None


def _line_of(source, offset):
    return source.count("\n", 0, offset) + 1


def _masked(source, spans):
    """Non-code spans blanked, newlines kept; value literals get a sentinel
    first character so a line ending in one still ends its statement."""
    parts = []
    for kind, start, end in spans:
        segment = source[start:end]
        if kind == "code":
            parts.append(segment)
            continue
        blank = "".join(ch if ch == "\n" else " " for ch in segment)
        if kind in ("string", "raw", "rune") and blank[:1] == " ":
            blank = "#" + blank[1:]
        parts.append(blank)
    return "".join(parts)


def _statement_end(mask, i, end):
    depth = 0
    last = ""
    while i < end:
        c = mask[i]
        if c in OPENERS:
            depth += 1
            last = c
        elif c in CLOSERS:
            depth -= 1
            if depth < 0:
                return i
            last = c
        elif depth == 0 and c == ";":
            return i + 1
        elif depth == 0 and c == "\n":
            if last and last not in CONTINUERS:
                return i + 1
        elif not c.isspace():
            last = c
        i += 1
    return end


def _find_at_depth(mask, start, stop, target):
    depth = 0
    i = start
    while i < stop:
        c = mask[i]
        if c in OPENERS:
            if c == target and depth == 0:
                return i
            depth += 1
        elif c in CLOSERS:
            depth -= 1
        elif c == target and depth == 0:
            return i
        i += 1
    return -1


def _matching_brace(mask, open_index, end):
    depth = 0
    i = open_index
    while i < end:
        c = mask[i]
        if c in OPENERS:
            depth += 1
        elif c in CLOSERS:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return end


def _first_word(mask, i, end):
    while i < end and mask[i] in " \t":
        i += 1
    j = i
    while j < end and mask[j] in WORD_CHARS:
        j += 1
    return mask[i:j], i


class _Outline:
    def __init__(self, source, mask):
        self.source = source
        self.mask = mask
        self.lines = []
        self.regions = []
        self.declarations = 0

    def emit(self, text, depth=0):
        pad = "    " * depth
        for line in text.splitlines():
            self.lines.append(pad + line.strip() if depth else line.rstrip())

    def confess(self, start, stop):
        first = _line_of(self.source, start)
        last = _line_of(self.source, max(start, stop - 1))
        if self.regions and self.regions[-1][1] >= first - 1:
            self.regions[-1] = (self.regions[-1][0], max(self.regions[-1][1], last))
        else:
            self.regions.append((first, last))

    def walk(self, start, end):
        mask = self.mask
        i = start
        while i < end:
            while i < end and (mask[i].isspace() or mask[i] == ";"):
                i += 1
            if i >= end:
                break
            if mask[i] in CLOSERS:
                i += 1
                continue
            word, word_at = _first_word(mask, i, end)
            if word not in DECL_KEYWORDS:
                stop = _statement_end(mask, i, end)
                self.confess(i, stop)
                i = max(stop, i + 1)
                continue
            i = max(self._declaration(i, end, word, word_at + len(word)), i + 1)

    def _declaration(self, i, end, keyword, after_kw):
        mask = self.mask
        stmt_stop = _statement_end(mask, i, end)

        if keyword == "func":
            brace = _find_at_depth(mask, i, stmt_stop, "{")
            if brace == -1:
                self.emit(self.source[i:stmt_stop].rstrip().rstrip(";").rstrip())
                self.declarations += 1
                return stmt_stop
            self.emit(self.source[i:brace].rstrip())
            self.declarations += 1
            return _matching_brace(mask, brace, end) + 1

        if keyword in GROUPABLE:
            next_word, next_at = _first_word(mask, after_kw, stmt_stop)
            if not next_word and mask[next_at : next_at + 1] == "(":
                return self._group(i, end, keyword, next_at)

        if keyword == "package" or keyword == "import":
            self.emit(_head_line(self.source, i, stmt_stop))
            self.declarations += 1
            return stmt_stop

        # A single type, const or var declaration. A type with a body keeps
        # its head and skips the body; const and var stop before their
        # initialiser, type aliases keep their whole line.
        brace = _find_at_depth(mask, i, stmt_stop, "{")
        if keyword == "type" and brace != -1:
            self.emit(self.source[i:brace].rstrip())
            self.declarations += 1
            return _matching_brace(mask, brace, end) + 1
        head_stop = stmt_stop
        if keyword in ("const", "var"):
            equals = _find_at_depth(mask, i, stmt_stop, "=")
            if equals != -1:
                head_stop = equals
        self.emit(_head_line(self.source, i, head_stop))
        self.declarations += 1
        return stmt_stop

    def _group(self, i, end, keyword, paren):
        close = _matching_brace(self.mask, paren, end)
        self.emit(f"{keyword} (")
        self.declarations += 1
        j = paren + 1
        while j < close:
            while j < close and (self.mask[j].isspace() or self.mask[j] == ";"):
                j += 1
            if j >= close:
                break
            member_stop = min(_statement_end(self.mask, j, close), close)
            if not self.mask[j:member_stop].strip():
                j = max(member_stop, j + 1)
                continue
            brace = _find_at_depth(self.mask, j, member_stop, "{")
            if keyword == "type" and brace != -1:
                self.emit(self.source[j:brace].rstrip(), depth=1)
                self.declarations += 1
                j = _matching_brace(self.mask, brace, close if brace < close else end) + 1
                continue
            head_stop = member_stop
            if keyword in ("const", "var"):
                equals = _find_at_depth(self.mask, j, member_stop, "=")
                if equals != -1:
                    head_stop = equals
            self.emit(_head_line(self.source, j, head_stop), depth=1)
            self.declarations += 1
            j = max(member_stop, j + 1)
        return close + 1


def _head_line(source, start, stop):
    newline = source.find("\n", start, stop)
    cut = stop if newline == -1 else newline
    return source[start:cut].rstrip().rstrip(";").rstrip()


def _module_header(source, spans):
    for kind, start, end in spans:
        if kind == "code" and source[start:end].strip():
            return None
        if kind in ("line_comment", "block_comment"):
            for raw in source[start:end].splitlines():
                text = raw.strip().lstrip("/*").rstrip("*/").strip("* ").strip()
                if text:
                    return text
            return None
    return None


def outline(path, source, out):
    """Print the file's declaration outline; 0 clean, 1 when the lexer
    confessed an unterminated construct."""
    spans, errors = lex(source)
    mask = _masked(source, spans)
    header = _module_header(source, spans)
    print(f"module: {header}" if header else "module: (no header comment)", file=out)

    walker = _Outline(source, mask)
    walker.walk(0, len(source) if not errors else spans[-1][1])
    for offset, reason in errors:
        print(f"lexer: {reason} at line {_line_of(source, offset)}", file=out)
        walker.confess(offset, len(source))

    for line in walker.lines:
        print(line, file=out)
    print(f"declarations: {walker.declarations}", file=out)
    if walker.regions:
        listed = ", ".join(
            f"lines {a}-{b}" if a != b else f"line {a}" for a, b in walker.regions
        )
        print(f"unparsed: {len(walker.regions)} region(s): {listed}", file=out)
    else:
        print("unparsed: none", file=out)
    return 1 if errors else 0
