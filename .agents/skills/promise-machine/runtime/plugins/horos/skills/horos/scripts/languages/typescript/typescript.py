"""TypeScript outline extraction for Horos's map verb.

This module lexes rather than parses. The lexer classifies every character
of the source into code, comments, strings, template literals and regex
literals; the outliner (a later step) works only over the code spans. It
never imports or executes what it reads.
"""

# Tokens after which a slash starts a regex literal rather than division.
# After an identifier, a number, or a closing ) ] } the slash divides.
REGEX_ALLOWED_AFTER = frozenset(
    {
        "",
        "(",
        "[",
        "{",
        "}",
        ",",
        ";",
        ":",
        "=",
        "=>",
        "==",
        "===",
        "!",
        "!=",
        "!==",
        "&",
        "&&",
        "|",
        "||",
        "?",
        "??",
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
        "<=",
        ">=",
        "~",
        "^",
        "return",
        "case",
        "typeof",
        "instanceof",
        "in",
        "of",
        "new",
        "delete",
        "void",
        "do",
        "else",
        "yield",
        "await",
        "throw",
    }
)

WORD_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$"
)


def lex(source):
    """Classify the whole source into spans; fail-open on what it cannot end.

    Returns (spans, errors). Each span is (kind, start, end) with kind one
    of code, line_comment, block_comment, string, template, regex; spans
    cover the source in order. Each error is (offset, reason) for a
    construct that never terminated; the span still covers the remainder so
    the caller can confess it.
    """
    spans = []
    errors = []
    n = len(source)
    i = 0
    code_start = 0
    prev = ""  # last significant code token, for the regex decision

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
            i = end
            code_start = i
            continue

        if c == "/" and i + 1 < n and source[i + 1] == "*":
            flush_code(i)
            end = source.find("*/", i + 2)
            if end == -1:
                errors.append((i, "unterminated block comment"))
                spans.append(("block_comment", i, n))
                return spans, errors
            spans.append(("block_comment", i, end + 2))
            i = end + 2
            code_start = i
            continue

        if c in "'\"":
            flush_code(i)
            end = _scan_string(source, i)
            if end is None:
                errors.append((i, "unterminated string"))
                spans.append(("string", i, n))
                return spans, errors
            spans.append(("string", i, end))
            i = end
            code_start = i
            prev = "string"
            continue

        if c == "`":
            flush_code(i)
            end = _scan_template(source, i)
            if end is None:
                errors.append((i, "unterminated template literal"))
                spans.append(("template", i, n))
                return spans, errors
            spans.append(("template", i, end))
            i = end
            code_start = i
            prev = "template"
            continue

        if c == "/" and prev in REGEX_ALLOWED_AFTER:
            end = _scan_regex(source, i)
            if end is not None:
                flush_code(i)
                spans.append(("regex", i, end))
                i = end
                code_start = i
                prev = "regex"
                continue
            # A regex cannot hold an unescaped newline; the scan failing
            # means this slash divides after all, so fall through as code.

        if c in WORD_CHARS:
            j = i
            while j < n and source[j] in WORD_CHARS:
                j += 1
            prev = source[i:j]
            i = j
            continue

        if not c.isspace():
            # Fold repeated operator characters so `=>` and `===` count as
            # one significant token for the regex decision.
            if prev and prev[-1] == c and (prev + c) in REGEX_ALLOWED_AFTER:
                prev += c
            elif c == ">" and prev == "=":
                prev = "=>"
            else:
                prev = c
        i += 1

    flush_code(n)
    return spans, errors


def _scan_string(source, start):
    """From the opening quote past the closing one; None if it never closes.

    An escape consumes the next character, which legally includes a newline
    (line continuation); a raw newline ends the literal unterminated.
    """
    quote = source[start]
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


def _scan_template(source, start):
    """From the opening backtick past its match, through nested ${...}
    expressions that may themselves hold strings, templates and comments.
    None if it never closes."""
    n = len(source)
    i = start + 1
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == "`":
            return i + 1
        if c == "$" and i + 1 < n and source[i + 1] == "{":
            i = _scan_template_expression(source, i + 2)
            if i is None:
                return None
            continue
        i += 1
    return None


def _scan_template_expression(source, start):
    """From just after `${` past the balancing `}`; None if unbalanced."""
    n = len(source)
    depth = 1
    i = start
    while i < n:
        c = source[i]
        if c in "'\"":
            i = _scan_string(source, i)
            if i is None:
                return None
            continue
        if c == "`":
            i = _scan_template(source, i)
            if i is None:
                return None
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "/":
            end = source.find("\n", i)
            if end == -1:
                return None
            i = end
            continue
        if c == "/" and i + 1 < n and source[i + 1] == "*":
            end = source.find("*/", i + 2)
            if end == -1:
                return None
            i = end + 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


OPENERS = "([{"
CLOSERS = ")]}"

MODIFIERS = frozenset(
    {
        "export",
        "default",
        "declare",
        "abstract",
        "async",
        "public",
        "private",
        "protected",
        "static",
        "readonly",
        "override",
        "accessor",
        "get",
        "set",
    }
)

# Keywords whose declaration head runs to the body brace.
HEADED = frozenset({"function", "class", "interface", "enum", "namespace", "module"})

# Keywords whose declaration is quoted as its first line.
SIMPLE = frozenset({"import", "type", "const", "let", "var"})

# Statement-final characters that suppress the newline statement end: a line
# ending in one of these still owes the next line something. A bare `>` is
# not here: it ends a generic or a JSX tag. The arrow survives as the
# two-character token the scanner folds it into.
CONTINUERS = frozenset(",=&|+-*/?:.([{") | {"=>"}


def _line_of(source, offset):
    return source.count("\n", 0, offset) + 1


def _masked(source, spans):
    """The source with every non-code span blanked, newlines kept, so
    structure tracking cannot be derailed by braces inside literals.

    A string, template or regex is a value, so its first character becomes a
    sentinel: without one, a semicolon-free line like `const K = "v"` ends
    on a stale `=` and swallows the statements after it. Comments stay
    fully blank; they are not values and must not end anything."""
    parts = []
    for kind, start, end in spans:
        segment = source[start:end]
        if kind == "code":
            parts.append(segment)
            continue
        blank = "".join(ch if ch == "\n" else " " for ch in segment)
        if kind in ("string", "template", "regex") and blank[:1] == " ":
            blank = "#" + blank[1:]
        parts.append(blank)
    return "".join(parts)


def _statement_end(mask, i, end):
    """Index just past the statement starting at i: a balanced `;`, a
    newline that plausibly ends it, or the region's closing brace."""
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
    """The first target character at bracket depth zero, or -1."""
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


def _leading_words(mask, i, end):
    """The statement's leading identifier-like words, for recognition."""
    words = []
    while i < end and len(words) < 8:
        while i < end and mask[i] in " \t":
            i += 1
        j = i
        while j < end and mask[j] in WORD_CHARS:
            j += 1
        if j == i:
            break
        words.append(mask[i:j])
        i = j
    return words


def _first_line(source, start, stop):
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

    def emit(self, text, depth):
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

    def region(self, start, end, depth, in_class):
        mask = self.mask
        i = start
        while i < end:
            while i < end and (mask[i].isspace() or mask[i] == ";"):
                i += 1
            if i >= end:
                break
            if mask[i] in CLOSERS:
                # A stray closer at statement position cannot start anything;
                # stepping over it is what keeps this loop finite.
                i += 1
                continue
            if mask[i] == "@":
                stop = self._decorator_end(i, end)
                self.emit(self.source[i:stop].rstrip(), depth)
                i = max(stop, i + 1)
                continue
            if in_class:
                i = max(self._member(i, end, depth), i + 1)
                continue
            i = max(self._statement(i, end, depth), i + 1)

    def _decorator_end(self, i, end):
        j = i + 1
        while j < end and self.mask[j] in WORD_CHARS.union("."):
            j += 1
        if j < end and self.mask[j] == "(":
            return _matching_brace(self.mask, j, end) + 1
        return j

    def _statement(self, i, end, depth):
        words = _leading_words(self.mask, i, end)
        keyword = next((w for w in words if w not in MODIFIERS), None)

        if keyword in HEADED:
            return self._headed(i, end, depth, keyword)
        if keyword in SIMPLE or (words[:2] == ["export", "default"]) or (
            words and words[0] == "export" and keyword is None
        ):
            stop = _statement_end(self.mask, i, end)
            self.emit(_first_line(self.source, i, stop), depth)
            self.declarations += 1
            return stop
        stop = _statement_end(self.mask, i, end)
        self.confess(i, stop)
        return stop

    def _headed(self, i, end, depth, keyword):
        brace = self.mask.find("{", i, _statement_end(self.mask, i, end))
        if brace == -1:
            stop = _statement_end(self.mask, i, end)
            self.emit(_first_line(self.source, i, stop), depth)
            self.declarations += 1
            return stop
        self.emit(self.source[i:brace].rstrip(), depth)
        self.declarations += 1
        close = _matching_brace(self.mask, brace, end)
        if keyword == "class":
            self.region(brace + 1, close, depth + 1, in_class=True)
        elif keyword in ("namespace", "module"):
            self.region(brace + 1, close, depth + 1, in_class=False)
        return close + 1

    def _member(self, i, end, depth):
        stmt_stop = _statement_end(self.mask, i, end)
        paren = _find_at_depth(self.mask, i, stmt_stop, "(")
        equals = _find_at_depth(self.mask, i, stmt_stop, "=")
        brace = _find_at_depth(self.mask, i, stmt_stop, "{")
        first = min(x for x in (paren, equals, brace, stmt_stop) if x != -1)

        if first == paren:
            # A method: head runs from the modifiers through the parameter
            # list and any return type, up to the body brace.
            after = _matching_brace(self.mask, paren, end) + 1
            rest_stop = _statement_end(self.mask, after, end)
            body = _find_at_depth(self.mask, after, rest_stop, "{")
            head_stop = body if body != -1 else rest_stop
            self.emit(self.source[i:head_stop].rstrip().rstrip(";").rstrip(), depth)
            self.declarations += 1
            if body != -1:
                return _matching_brace(self.mask, body, end) + 1
            return rest_stop
        if first == brace:
            # A static initialiser block or similar: name it, skip its body.
            self.emit(self.source[i:brace].rstrip(), depth)
            self.declarations += 1
            return _matching_brace(self.mask, brace, end) + 1
        # A property, with or without an initialiser: quote the head only.
        head_stop = equals if first == equals else stmt_stop
        self.emit(_first_line(self.source, i, head_stop), depth)
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
    lexed_end = spans[-1][2] if errors and spans else len(source)
    walker.region(0, lexed_end if not errors else spans[-1][1], 0, in_class=False)
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


def _scan_regex(source, start):
    """From the opening slash past the closing one and its flags; None when
    a newline arrives first, which proves this slash was division."""
    n = len(source)
    i = start + 1
    in_class = False
    while i < n:
        c = source[i]
        if c == "\\":
            i += 2
            continue
        if c == "\n":
            return None
        if c == "[":
            in_class = True
        elif c == "]":
            in_class = False
        elif c == "/" and not in_class:
            i += 1
            while i < n and source[i] in "dgimsuvy":
                i += 1
            return i
        i += 1
    return None
