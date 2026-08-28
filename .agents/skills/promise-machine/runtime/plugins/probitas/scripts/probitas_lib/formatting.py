"""Shared formatting, so the renderer and the gate checker agree.

Gate 3 works by recomputing, from the evidence alone, every number and hash a
truthful dossier could contain, and then failing the document if it contains
one that is not in that set. That only works if both halves format a value the
same way, so both halves call these functions and neither formats anything on
its own.

All arithmetic here is integer arithmetic. Scaling a token amount by its
decimals is a digit shift, so it stays exact, and a float would put a rounding
error into a document about money.
"""

import datetime
import re

# Grouping marks only. A space must not be here: with it, "held 9,000,000.00
# USDC" collapses into one token that is neither a number nor a hash, the
# sieve finds nothing to look at, and gate 3 passes everything.
SEPARATORS = ",._"


def timestamp(seconds):
    """A unix timestamp as an ISO date in UTC."""
    if seconds is None:
        return ""
    moment = datetime.datetime.fromtimestamp(int(seconds), datetime.timezone.utc)
    return moment.strftime("%Y-%m-%d")


def duration(seconds):
    """A span in whole days and hours. Never a float."""
    seconds = int(seconds)
    if seconds < 0:
        return "0h"
    days, remainder = divmod(seconds, 86400)
    hours = remainder // 3600
    if days and hours:
        return f"{days}d {hours}h"
    if days:
        return f"{days}d"
    return f"{hours}h"


def amount(raw, decimals=None, symbol=None):
    """A token amount, scaled exactly and grouped for reading.

    With no decimals the raw integer is printed and labelled as raw, because a
    number in an underwriting document that might be off by six orders of
    magnitude is worse than one a reader has to divide themselves.
    """
    value = int(raw)
    if decimals is None:
        printed = f"{value:,}"
        return f"{printed} raw units" + (f" of {symbol}" if symbol else "")

    decimals = int(decimals)
    if decimals == 0:
        printed = f"{value:,}"
    else:
        whole, fraction = divmod(abs(value), 10**decimals)
        sign = "-" if value < 0 else ""
        printed = f"{sign}{whole:,}.{str(fraction).zfill(decimals)}"
    return printed + (f" {symbol}" if symbol else "")


def bips(value):
    """Basis points, printed as both, because a reader wants the percentage."""
    value = int(value)
    whole, fraction = divmod(value, 100)
    return f"{whole}.{str(fraction).zfill(2)}% ({value} bips)"


def short(text, width=10):
    """An address or hash, shortened for a table cell."""
    if len(text) <= width * 2:
        return text
    return f"{text[:width]}...{text[-4:]}"


# A number whose groups are spaced rather than punctuated. "9 000 000" walks
# past a sieve that treats a space as a word boundary, and an amount is just
# as wrong written that way.
_SPACED_NUMBER = re.compile(r"\d[\d\s,._]*\d")

# A hash or address written without its 0x. Sixteen hex characters in a row is
# not something prose does by accident.
_BARE_HEX = re.compile(r"\b[0-9a-fA-F]{16,}\b")


def numeric_tokens(text):
    """Every number and hex string a document contains, separators removed.

    This is the sieve gate 3 runs over a dossier. A hash, an address, or any
    run of four or more digits is something the document is asserting, and it
    has to have come from the evidence rather than from a model filling in a
    plausible-looking gap.

    Three passes, because one is not enough. The first splits on word
    boundaries. The second catches numbers grouped with spaces. The third
    catches hex written without its prefix. Anything that gets past all three
    and is still wrong is a claim in words, which is the operator's to check.
    """
    tokens = set()
    current = []
    for character in text + " ":
        if character.isalnum() or character in SEPARATORS:
            current.append(character)
            continue
        tokens.update(_split(current))
        current = []
    tokens.update(_split(current))

    for match in _SPACED_NUMBER.finditer(text):
        tokens.update(_split(list(match.group(0).replace(" ", ""))))
    for match in _BARE_HEX.finditer(text):
        tokens.add("0x" + match.group(0).lower())

    return {t for t in tokens if _interesting(t)}


def _split(characters):
    word = "".join(characters)
    for separator in SEPARATORS:
        word = word.replace(separator, "")
    return {word.lower()} if word else set()


def _interesting(token):
    if token.startswith("0x") and len(token) > 8:
        return True
    return token.isdigit() and len(token) >= 4
