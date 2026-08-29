"""Bound and defuse anything that arrived off the network.

Market names and token symbols are borrower-chosen strings. They land in a
Markdown document that a person reads and a model may consume, so they are
attacker-influenced input to both. Three separate problems, handled here:
control characters that corrupt a terminal or a diff, Markdown that escapes its
table cell and rewrites the document around it, and text shaped like an
instruction, which is only a problem because something downstream might obey it.
"""

import re
import unicodedata

MAX_LENGTH = 200

_MARKDOWN = str.maketrans(
    {
        "|": "\\|",
        "*": "\\*",
        "_": "\\_",
        "`": "\\`",
        "[": "\\[",
        "]": "\\]",
        "<": "&lt;",
        ">": "&gt;",
        "#": "\\#",
        "\\": "\\\\",
    }
)

# Phrases whose only purpose in a market name is to be read as a directive by
# whatever consumes the dossier next.
_INSTRUCTION = re.compile(
    r"(ignore\s+(all\s+|any\s+)?(previous|prior|above|preceding)"
    r"|disregard\s+(all\s+|the\s+)?(previous|prior|above|instructions)"
    r"|system\s*(prompt|message)"
    r"|</?(system|assistant|user|instructions?)>"
    r"|you\s+are\s+now\b"
    r"|new\s+instructions?\b"
    r"|act\s+as\s+(a|an)\b)",
    re.IGNORECASE,
)

REDACTED = "[redacted: text shaped like an instruction]"


def strip_controls(text):
    """Drop control and format characters, keeping ordinary whitespace."""
    out = []
    for character in text:
        if character in ("\t", "\n"):
            out.append(" ")
            continue
        category = unicodedata.category(character)
        if category in ("Cc", "Cf", "Co", "Cs", "Cn"):
            continue
        out.append(character)
    return "".join(out)


def clean(text, max_length=MAX_LENGTH):
    """Make an untrusted string safe to put in a Markdown document.

    Order matters. Strip control characters first, so a directive cannot be
    hidden behind a zero-width joiner and survive the instruction check. Check
    for instruction shapes next, on the readable text. Escape Markdown last, so
    the escaping cannot itself hide a match.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    text = strip_controls(text)
    text = re.sub(r"\s+", " ", text).strip()

    if _INSTRUCTION.search(text):
        return REDACTED

    # Escape first, then cap, so the returned string honours the cap. Escaping
    # afterwards would push a name that was exactly at the limit past it, one
    # backslash per metacharacter.
    text = text.translate(_MARKDOWN)

    if len(text) > max_length:
        text = text[: max_length - 1].rstrip("\\").rstrip() + "…"

    return text


def address(value):
    """Normalise an address, or refuse it.

    Refusing is the point. An address is the one field the whole dossier hangs
    off, and something that is not an address should never reach a venue query
    or a document.
    """
    if not isinstance(value, str):
        raise ValueError(f"address must be a string, got {type(value).__name__}")
    text = value.strip().lower()
    if not re.fullmatch(r"0x[0-9a-f]{40}", text):
        raise ValueError(f"not a 20-byte hex address: {value!r}")
    return text


def entity_name(value):
    """An entity name is operator input, but the operator may be pasting."""
    text = clean(value, max_length=120)
    if not text:
        raise ValueError("entity name is required")
    return text
