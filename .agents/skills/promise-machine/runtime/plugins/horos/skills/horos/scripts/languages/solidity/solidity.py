"""Solidity outline extraction for Horos's map verb.

The extractor shape fixed three times, sized for a language that lexes like
a small C++ without the preprocessor and declares like Go: keyword-led at
every depth. It lexes, slices verbatim, confesses what it does not
recognise, and never imports or executes what it reads.
"""

WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$"
)
OPENERS = "([{"
CLOSERS = ")]}"

# A line ending in one of these still owes the next line something; the
# two-character mapping arrow survives via the same fold TypeScript uses.
CONTINUERS = frozenset(",=&|+-*/?:.([{<>!%^") | {"=>"}

# Container declarations whose bodies are walked for members.
CONTAINER_KEYWORDS = frozenset({"contract", "interface", "library"})

# Declarations whose head runs through parameters and attributes to the
# body brace or terminating semicolon.
CALLABLE_KEYWORDS = frozenset(
    {"function", "constructor", "receive", "fallback", "modifier", "event", "error"}
)

# Declarations whose head stops at their body brace, body skipped whole.
BODIED_KEYWORDS = frozenset({"struct", "enum"})

# Single-statement declarations quoted to their semicolon.
LINE_KEYWORDS = frozenset({"pragma", "import", "using", "type"})

# Statement-position words that can never head a declaration.
CONFESS_KEYWORDS = frozenset(
    {"if", "for", "while", "do", "return", "emit", "revert", "require",
     "assembly", "unchecked", "try", "catch", "else"}
)

MODIFIER_WORDS = frozenset({"abstract"})


def lex(source):
    """Classify the source into spans of code, line_comment, block_comment
    and string. Returns (spans, errors); an unterminated construct's span
    covers the remainder."""
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
        if c in "'\"":
            flush_code(i)
            end = _scan_quoted(source, i, c)
            if end is None:
                errors.append((i, "unterminated string"))
                spans.append(("string", i, n))
                return spans, errors
            spans.append(("string", i, end))
            i = code_start = end
            continue
        i += 1

    flush_code(n)
    return spans, errors


def _scan_quoted(source, start, quote):
    n = len(source)
    i = start + 1
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == quote:
            return i + 1
        if c == "\n":
            return None
        i += 1
    return None


def _line_of(source, offset):
    return source.count("\n", 0, offset) + 1


def _masked(source, spans):
    """Non-code spans blanked, newlines kept; strings get a sentinel first
    character so a line ending in one still ends its statement."""
    parts = []
    for kind, start, end in spans:
        segment = source[start:end]
        if kind == "code":
            parts.append(segment)
            continue
        blank = "".join(ch if ch == "\n" else " " for ch in segment)
        if kind == "string" and blank[:1] == " ":
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
            last = "=>" if c == ">" and last == "=" else c
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


def _body_brace(mask, i, stmt_stop, end):
    """The declaration's body brace: inside the statement, or Allman-style
    alone on the following line."""
    brace = _find_at_depth(mask, i, stmt_stop, "{")
    if brace != -1:
        return brace
    j = stmt_stop
    while j < end and mask[j].isspace():
        j += 1
    if j < end and mask[j] == "{":
        return j
    return -1


def _first_word(mask, i, end):
    while i < end and mask[i] in " \t":
        i += 1
    j = i
    while j < end and mask[j] in WORD_CHARS:
        j += 1
    return mask[i:j], i


def _head_line(source, start, stop):
    newline = source.find("\n", start, stop)
    cut = stop if newline == -1 else newline
    return source[start:cut].rstrip().rstrip(";").rstrip()


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
            if not line.strip():
                continue
            self.lines.append(pad + line.strip() if depth else line.rstrip())

    def confess(self, start, stop):
        first = _line_of(self.source, start)
        last = _line_of(self.source, max(start, stop - 1))
        if self.regions and self.regions[-1][1] >= first - 1:
            self.regions[-1] = (self.regions[-1][0], max(self.regions[-1][1], last))
        else:
            self.regions.append((first, last))

    def walk(self, start, end, depth=0):
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
            i = max(self._statement(i, end, depth), i + 1)

    def _statement(self, i, end, depth):
        mask = self.mask
        word, word_at = _first_word(mask, i, end)

        if word in CONFESS_KEYWORDS:
            stop = _statement_end(mask, i, end)
            self.confess(i, stop)
            return stop

        if word in MODIFIER_WORDS:
            inner, _ = _first_word(mask, word_at + len(word), end)
            if inner in CONTAINER_KEYWORDS:
                word = inner

        if word in CONTAINER_KEYWORDS:
            # A container always owns a brace, and its inheritance list may
            # break lines after `is`, so the brace is found structurally:
            # the first depth-zero brace before any depth-zero semicolon.
            semi = _find_at_depth(mask, i, end, ";")
            brace = _find_at_depth(mask, i, semi if semi != -1 else end, "{")
            stmt_stop = _statement_end(mask, i, end) if brace == -1 else brace
            if brace == -1:
                self.emit(_head_line(self.source, i, stmt_stop), depth)
                self.declarations += 1
                return stmt_stop
            self.emit(self.source[i:brace].rstrip(), depth)
            self.declarations += 1
            close = _matching_brace(mask, brace, end)
            self.walk(brace + 1, close, depth + 1)
            return close + 1

        if word in BODIED_KEYWORDS:
            stmt_stop = _statement_end(mask, i, end)
            brace = _body_brace(mask, i, stmt_stop, end)
            if brace == -1:
                self.emit(_head_line(self.source, i, stmt_stop), depth)
                self.declarations += 1
                return stmt_stop
            self.emit(self.source[i:brace].rstrip(), depth)
            self.declarations += 1
            return _matching_brace(mask, brace, end) + 1

        if word in LINE_KEYWORDS:
            stmt_stop = _statement_end(mask, i, end)
            self.emit(_head_line(self.source, i, stmt_stop), depth)
            self.declarations += 1
            return stmt_stop

        if word in CALLABLE_KEYWORDS:
            return self._callable(i, end, depth)

        return self._generic(i, end, depth)

    def _callable(self, i, end, depth):
        mask = self.mask
        stmt_stop = _statement_end(mask, i, end)
        paren = _find_at_depth(mask, i, stmt_stop, "(")
        if paren == -1:
            self.emit(_head_line(self.source, i, stmt_stop), depth)
            self.declarations += 1
            return stmt_stop
        after = _matching_brace(mask, paren, end) + 1
        rest_stop = _statement_end(mask, after, end)
        body = _body_brace(mask, after, rest_stop, end)
        head_stop = body if body != -1 else rest_stop
        self.emit(self.source[i:head_stop].rstrip().rstrip(";").rstrip(), depth)
        self.declarations += 1
        if body != -1:
            return _matching_brace(mask, body, end) + 1
        return rest_stop

    def _generic(self, i, end, depth):
        mask = self.mask
        if mask[i] == "{":
            # An orphan brace block names nothing and owns nothing beyond
            # its own close; stepping over it keeps a mis-slice bounded.
            return _matching_brace(mask, i, end) + 1
        stmt_stop = _statement_end(mask, i, end)
        equals = _find_at_depth(mask, i, stmt_stop, "=")
        head_stop = equals if equals != -1 else stmt_stop
        head = _head_line(self.source, i, head_stop)
        if head.strip():
            self.emit(head, depth)
            self.declarations += 1
        return stmt_stop


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
