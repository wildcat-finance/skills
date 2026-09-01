"""A bounded scanner for the TypeScript surface this inventory reads.

It exists so the compiler is not a set of regular expressions run over raw
bytes. A comment that mentions `export const GET`, or a string holding
`"use server"`, must not become an inventory item, and only a scanner that
knows where comments and strings begin and end can tell the difference.

It is deliberately not a parser. It produces identifiers, punctuation and
string values in order, which is enough to recognise a directive prologue and
an exported binding, and it makes no attempt at types, JSX structure or scope.
`docs/inventory-rules.md` states what that costs.
"""

from __future__ import annotations

from typing import Iterator, NamedTuple

IDENTIFIER_START = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_$")
IDENTIFIER_PART = IDENTIFIER_START | set("0123456789")
# A `/` opens a regular expression only where a value cannot already have
# ended. After an identifier, a literal or a closing bracket it is division.
VALUE_ENDING = {")", "]", "}"}


class Token(NamedTuple):
    kind: str  # "name", "string", "punct"
    value: str
    line: int


def tokenize(source: str) -> list[Token]:
    """Return every name, string value and punctuation mark, comments dropped."""
    return list(_scan(source))


def _scan(source: str) -> Iterator[Token]:
    index = 0
    line = 1
    length = len(source)
    previous: Token | None = None
    while index < length:
        char = source[index]
        if char == "\n":
            line += 1
            index += 1
            continue
        if char in " \t\r\f\v":
            index += 1
            continue
        if source.startswith("//", index):
            index = source.find("\n", index)
            if index == -1:
                return
            continue
        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end == -1:
                return
            line += source.count("\n", index, end)
            index = end + 2
            continue
        if char in "'\"":
            value, index, line = _string(source, index, line, char)
            previous = Token("string", value, line)
            yield previous
            continue
        if char == "`":
            value, index, line = _template(source, index, line)
            previous = Token("string", value, line)
            yield previous
            continue
        if char == "/" and _regex_can_start(previous):
            index, line = _regex(source, index, line)
            previous = Token("punct", "/regex/", line)
            continue
        if char in IDENTIFIER_START:
            start = index
            while index < length and source[index] in IDENTIFIER_PART:
                index += 1
            previous = Token("name", source[start:index], line)
            yield previous
            continue
        previous = Token("punct", char, line)
        yield previous
        index += 1


def _regex_can_start(previous: Token | None) -> bool:
    if previous is None:
        return True
    if previous.kind == "string":
        return False
    if previous.kind == "name":
        # A keyword may be followed by a regular expression; a value may not.
        return previous.value in {"return", "case", "typeof", "in", "of", "do", "else"}
    return previous.value not in VALUE_ENDING


def _string(source: str, index: int, line: int, quote: str) -> tuple[str, int, int]:
    index += 1
    out: list[str] = []
    while index < len(source):
        char = source[index]
        if char == "\\":
            out.append(source[index:index + 2])
            index += 2
            continue
        if char == quote:
            return "".join(out), index + 1, line
        if char == "\n":
            line += 1
        out.append(char)
        index += 1
    return "".join(out), index, line


def _template(source: str, index: int, line: int) -> tuple[str, int, int]:
    index += 1
    out: list[str] = []
    depth = 0
    while index < len(source):
        char = source[index]
        if char == "\\":
            out.append(source[index:index + 2])
            index += 2
            continue
        if source.startswith("${", index):
            depth += 1
            index += 2
            continue
        if char == "}" and depth:
            depth -= 1
            index += 1
            continue
        if char == "`" and not depth:
            return "".join(out), index + 1, line
        if char == "\n":
            line += 1
        if not depth:
            out.append(char)
        index += 1
    return "".join(out), index, line


def _regex(source: str, index: int, line: int) -> tuple[int, int]:
    index += 1
    in_class = False
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            in_class = True
        elif char == "]":
            in_class = False
        elif char == "/" and not in_class:
            index += 1
            while index < len(source) and source[index] in IDENTIFIER_PART:
                index += 1
            return index, line
        elif char == "\n":
            # An unterminated regular expression is a lexing error in the
            # source, not something to guess past.
            return index, line
        index += 1
    return index, line


def directive_prologue(tokens: list[Token]) -> set[str]:
    """The string directives at the head of a module, before any statement."""
    directives: set[str] = set()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.kind == "string":
            directives.add(token.value)
            index += 1
            if index < len(tokens) and tokens[index] == Token("punct", ";", tokens[index].line):
                index += 1
            continue
        if token.kind == "punct" and token.value == ";":
            index += 1
            continue
        break
    return directives


def exported_names(tokens: list[Token]) -> set[str]:
    """Every identifier bound by an `export` at this module's top level.

    Covers `export const X`, `export function X`, `export async function X`,
    `export class X` and `export { X, Y }`. It does not resolve re-exports or
    aliases, which `docs/inventory-rules.md` records as a stated limit.
    """
    names: set[str] = set()
    for position, token in enumerate(tokens):
        if token.kind != "name" or token.value != "export":
            continue
        rest = tokens[position + 1:position + 6]
        if not rest:
            continue
        if rest[0].kind == "punct" and rest[0].value == "{":
            for candidate in tokens[position + 2:]:
                if candidate.kind == "punct" and candidate.value == "}":
                    break
                if candidate.kind == "name" and candidate.value != "as":
                    names.add(candidate.value)
            continue
        for candidate in rest:
            if candidate.kind != "name":
                break
            if candidate.value in {"const", "let", "var", "function", "class", "async"}:
                continue
            if candidate.value == "default":
                names.add("default")
                break
            names.add(candidate.value)
            break
    return names
