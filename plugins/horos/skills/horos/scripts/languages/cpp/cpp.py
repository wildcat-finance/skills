"""C++ outline extraction for Horos's map verb.

The extractor shape fixed by TypeScript and Go, sized for the hardest
lexing target of the four: raw strings with custom delimiters, digit
separators inside numbers, and preprocessor directives that are lexed as
their own span kind and removed from the structural mask entirely. It
lexes, slices verbatim, confesses what it does not recognise, and never
imports or executes what it reads.
"""

WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
)
OPENERS = "([{"
CLOSERS = ")]}"

# A line ending in one of these still owes the next line something.
CONTINUERS = frozenset(",=&|+-*/?:.([{<>!%^~")

TYPE_KEYWORDS = frozenset({"class", "struct", "union", "enum"})
ACCESS_LABELS = frozenset({"public", "protected", "private"})

# Statement-position words that can never head a declaration; anything they
# lead is confessed rather than sliced as a counterfeit function.
CONFESS_KEYWORDS = frozenset(
    {
        "for",
        "while",
        "if",
        "else",
        "do",
        "switch",
        "return",
        "goto",
        "case",
        "default",
        "break",
        "continue",
        "try",
        "catch",
        "throw",
        "delete",
    }
)


def lex(source):
    """Classify the source into spans of code, line_comment, block_comment,
    string, char, raw and directive. Returns (spans, errors); an
    unterminated construct's span covers the remainder."""
    spans = []
    errors = []
    n = len(source)
    i = 0
    code_start = 0
    line_start = True  # only whitespace seen since the last newline

    def flush_code(end):
        if end > code_start:
            spans.append(("code", code_start, end))

    while i < n:
        c = source[i]

        if c == "#" and line_start:
            flush_code(i)
            end = _scan_directive(source, i)
            spans.append(("directive", i, end))
            i = code_start = end
            line_start = True
            continue

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
            raw = _raw_prefix(source, i)
            flush_code(i)
            if raw:
                end = _scan_raw(source, i)
                if end is None:
                    errors.append((i, "unterminated raw string"))
                    spans.append(("raw", i, n))
                    return spans, errors
                spans.append(("raw", i, end))
            else:
                end = _scan_quoted(source, i, '"')
                if end is None:
                    errors.append((i, "unterminated string"))
                    spans.append(("string", i, n))
                    return spans, errors
                spans.append(("string", i, end))
            i = code_start = end
            line_start = False
            continue

        if c == "'":
            # A quote between alphanumerics is a digit separator (1'000'000),
            # not a character literal.
            before = source[i - 1] if i > 0 else ""
            after = source[i + 1] if i + 1 < n else ""
            if before.isalnum() and (after.isalnum() or after == "_"):
                i += 1
                line_start = False
                continue
            flush_code(i)
            end = _scan_quoted(source, i, "'")
            if end is None:
                errors.append((i, "unterminated character literal"))
                spans.append(("char", i, n))
                return spans, errors
            spans.append(("char", i, end))
            i = code_start = end
            line_start = False
            continue

        if c == "\n":
            line_start = True
        elif not c.isspace():
            line_start = False
        i += 1

    flush_code(n)
    return spans, errors


def _scan_directive(source, start):
    """One preprocessor line including backslash continuations."""
    n = len(source)
    i = start
    while i < n:
        end = source.find("\n", i)
        if end == -1:
            return n
        j = end - 1
        if j >= 0 and source[j] == "\r":
            j -= 1
        if j >= start and source[j] == "\\":
            i = end + 1
            continue
        return end
    return n


def _raw_prefix(source, quote_index):
    """True when the quote at quote_index opens a raw string: preceded by R
    with at most an encoding prefix (u8, u, U, L) before it."""
    i = quote_index
    if i < 1 or source[i - 1] != "R":
        return False
    j = i - 2
    prefix = ""
    while j >= 0 and source[j] in WORD_CHARS and len(prefix) < 2:
        prefix = source[j] + prefix
        j -= 1
    if j >= 0 and source[j] in WORD_CHARS:
        return False
    return prefix in ("", "u", "U", "L", "u8")


def _scan_raw(source, start):
    """From the opening quote of R"delim( past )delim"; None if unclosed."""
    _n = len(source)
    open_paren = source.find("(", start + 1)
    if open_paren == -1 or open_paren - start - 1 > 16:
        return None
    delim = source[start + 1 : open_paren]
    closer = ")" + delim + '"'
    end = source.find(closer, open_paren + 1)
    if end == -1:
        return None
    return end + len(closer)


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
    """Non-code spans blanked, newlines kept; string, char and raw literals
    get a sentinel first character; directives stay fully blank so a brace
    inside a define never leaks into the structural mask."""
    parts = []
    for kind, start, end in spans:
        segment = source[start:end]
        if kind == "code":
            parts.append(segment)
            continue
        blank = "".join(ch if ch == "\n" else " " for ch in segment)
        if kind in ("string", "char", "raw") and blank[:1] == " ":
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
    return mask[i:j], i, j


def _skip_template_prefix(mask, i, end):
    """Past `template < ... >` including nested angles; i sits at 'template'."""
    j = i + len("template")
    while j < end and mask[j].isspace():
        j += 1
    if j >= end or mask[j] != "<":
        return i + len("template")
    depth = 0
    while j < end:
        c = mask[j]
        if c == "<":
            depth += 1
        elif c == ">":
            depth -= 1
            if depth == 0:
                return j + 1
        elif c in OPENERS:
            j = _matching_brace(mask, j, end)
        j += 1
    return j


def _ctor_body_brace(mask, candidate, end):
    """From the first depth-zero brace after an initialiser colon, walk
    brace groups until one is not followed by a comma or a further
    initialiser; that one is the constructor body."""
    while candidate != -1:
        close = _matching_brace(mask, candidate, end)
        j = close + 1
        while j < end and mask[j] in " \t":
            j += 1
        if j < end and (mask[j] == "," or mask[j] in WORD_CHARS):
            after_stop = _statement_end(mask, j, end)
            candidate = _find_at_depth(mask, j, after_stop, "{")
            if candidate == -1:
                candidate = _body_brace(mask, j, after_stop, end)
            continue
        return candidate
    return -1


def _body_brace(mask, i, stmt_stop, end):
    """The declaration's body brace: inside the statement, or an
    Allman-style brace alone on the following line."""
    brace = _find_at_depth(mask, i, stmt_stop, "{")
    if brace != -1:
        return brace
    j = stmt_stop
    while j < end and mask[j].isspace():
        j += 1
    if j < end and mask[j] == "{":
        return j
    return -1


def _head_line(source, start, stop):
    newline = source.find("\n", start, stop)
    cut = stop if newline == -1 else newline
    return source[start:cut].rstrip().rstrip(";").rstrip()


class _Outline:
    def __init__(self, source, mask, directives):
        self.source = source
        self.mask = mask
        self.directives = directives  # sorted (start, end), emitted in order
        self.next_directive = 0
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

    def _flush_directives(self, upto, depth):
        while self.next_directive < len(self.directives):
            start, end = self.directives[self.next_directive]
            if start >= upto:
                return
            head = _head_line(self.source, start, end).rstrip("\\").rstrip()
            if head.startswith(("#include", "#define")):
                self.emit(head, depth)
                self.declarations += 1
            self.next_directive += 1

    def walk(self, start, end, depth=0, in_class=False):
        mask = self.mask
        i = start
        while i < end:
            while i < end and (mask[i].isspace() or mask[i] == ";"):
                i += 1
            if i >= end:
                break
            if depth == 0:
                self._flush_directives(i, depth)
            if mask[i] in CLOSERS:
                i += 1
                continue
            i = max(self._statement(i, end, depth, in_class), i + 1)
        if depth == 0:
            self._flush_directives(end, depth)

    def _statement(self, i, end, depth, in_class):
        mask = self.mask
        slice_start = i
        word, word_at, word_end = _first_word(mask, i, end)

        if in_class and word in ACCESS_LABELS:
            colon = mask.find(":", word_end, _statement_end(mask, i, end))
            return colon + 1 if colon != -1 else word_end

        if word in CONFESS_KEYWORDS:
            stop = _statement_end(mask, i, end)
            self.confess(i, stop)
            return stop

        if word == "template":
            # The prefix emits as its own line, the way TypeScript emits
            # decorators; the declaration it introduces follows, and the
            # recursion must land on its first token, not on the newline.
            after = _skip_template_prefix(mask, word_at, end)
            self.emit(self.source[slice_start:after].strip(), depth)
            while after < end and mask[after].isspace():
                after += 1
            if after >= end:
                return end
            return self._statement(after, end, depth, in_class)

        if word == "namespace":
            stmt_stop = _statement_end(mask, i, end)
            brace = _body_brace(mask, i, stmt_stop, end)
            if brace == -1:
                self.emit(_head_line(self.source, i, stmt_stop), depth)
                self.declarations += 1
                return stmt_stop
            self.emit(self.source[i:brace].rstrip(), depth)
            self.declarations += 1
            close = _matching_brace(mask, brace, end)
            self.walk(brace + 1, close, depth, in_class=False)
            return close + 1

        if word == "extern":
            stmt_stop = _statement_end(mask, i, end)
            brace = _body_brace(mask, i, stmt_stop, end)
            if brace != -1 and mask.find("(", i, brace) == -1:
                self.emit(self.source[i:brace].rstrip(), depth)
                self.declarations += 1
                close = _matching_brace(mask, brace, end)
                self.walk(brace + 1, close, depth, in_class=False)
                return close + 1

        if word in TYPE_KEYWORDS or (
            word in ("typedef", "using") and self._has_type_keyword(word_end, end)
        ):
            return self._type_declaration(i, end, depth)

        if word in ("using", "typedef"):
            stmt_stop = _statement_end(mask, i, end)
            self.emit(_head_line(self.source, i, stmt_stop), depth)
            self.declarations += 1
            return stmt_stop

        return self._generic(i, end, depth)

    def _has_type_keyword(self, i, end):
        word, _, _ = _first_word(self.mask, i, end)
        return word in TYPE_KEYWORDS

    def _type_declaration(self, i, end, depth):
        mask = self.mask
        stmt_stop = _statement_end(mask, i, end)
        brace = _body_brace(mask, i, stmt_stop, end)
        if brace == -1:
            self.emit(_head_line(self.source, i, stmt_stop), depth)
            self.declarations += 1
            return stmt_stop
        self.emit(self.source[i:brace].rstrip(), depth)
        self.declarations += 1
        close = _matching_brace(mask, brace, end)
        words = set(self.mask[i:brace].split())
        if not words & {"enum"}:
            self.walk(brace + 1, close, depth + 1, in_class=True)
        tail_stop = _statement_end(mask, close + 1, end)
        tail = _head_line(self.source, close + 1, tail_stop).lstrip("} \t")
        if tail:
            self.emit(tail, depth)
        return tail_stop

    def _generic(self, i, end, depth):
        mask = self.mask
        stmt_stop = _statement_end(mask, i, end)
        paren = _find_at_depth(mask, i, stmt_stop, "(")
        equals = _find_at_depth(mask, i, stmt_stop, "=")
        brace = _find_at_depth(mask, i, stmt_stop, "{")
        if paren == equals == brace == -1:
            # An Allman-style parameter list opens on the following line;
            # the declaration continues through it.
            j = stmt_stop
            while j < end and mask[j].isspace():
                j += 1
            if j < end and mask[j] == "(":
                stmt_stop = _statement_end(mask, _matching_brace(mask, j, end) + 1, end)
                paren = j
        first = min(x for x in (paren, equals, brace, stmt_stop) if x != -1)

        if first == paren:
            after = _matching_brace(mask, paren, end) + 1
            rest_stop = _statement_end(mask, after, end)
            body = _body_brace(mask, after, rest_stop, end)
            if body != -1 and _find_at_depth(mask, after, body, ":") != -1:
                # A constructor initialiser list: brace-initialised members
                # look like bodies. The body is the brace group whose close
                # is not followed by a comma or another initialiser.
                body = _ctor_body_brace(mask, body, end)
            head_stop = body if body != -1 else rest_stop
            self.emit(
                self.source[i:head_stop].rstrip().rstrip(";").rstrip(), depth
            )
            self.declarations += 1
            if body != -1:
                # The body's closing brace ends a function outright; only
                # type declarations own a trailing declarator.
                return _matching_brace(mask, body, end) + 1
            return rest_stop
        if first == brace:
            head = self.source[i:brace].rstrip()
            close = _matching_brace(mask, brace, end)
            if not head.strip():
                # An orphan brace block names nothing and owns nothing
                # beyond its own close.
                return close + 1
            self.emit(head, depth)
            self.declarations += 1
            return _statement_end(mask, close + 1, end)
        head_stop = equals if first == equals else stmt_stop
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
        if kind == "directive":
            return None
    return None


def outline(path, source, out):
    """Print the file's declaration outline; 0 clean, 1 when the lexer
    confessed an unterminated construct."""
    spans, errors = lex(source)
    mask = _masked(source, spans)
    directives = [(s, e) for kind, s, e in spans if kind == "directive"]
    header = _module_header(source, spans)
    print(f"module: {header}" if header else "module: (no header comment)", file=out)

    walker = _Outline(source, mask, directives)
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
