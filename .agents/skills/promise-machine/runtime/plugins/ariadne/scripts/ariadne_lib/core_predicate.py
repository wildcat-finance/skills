"""The block every predicate carries, whatever its artefact.

Two lists. `claims` are the things that were checked, each naming the subject
digest it covers and what happened to it. `commands` are the things that were
run, each declaring whether its output has to match byte for byte on a replay.

A dataset predicate and a contract release predicate fill these in differently
and inherit the same five core gates, which is the whole reason the split
exists.

The vocabularies are closed. A disposition outside this list is a producer
inventing a state the verifier cannot reason about, and `passed` is the only one
that needs no reason attached.
"""

import unicodedata

CLAIMS = "claims"
COMMANDS = "commands"

DISPOSITIONS = ("passed", "failed", "skipped", "timed_out", "redacted")
NEEDS_REASON = tuple(d for d in DISPOSITIONS if d != "passed")

DETERMINISM = ("exact", "nondeterministic")

CLAIM_FIELDS = frozenset({"name", "subject", "disposition", "reason", "detail"})
COMMAND_FIELDS = frozenset(
    {"name", "argv", "determinism", "output_digest", "detail"}
)

MAX_STRUCTURED_KEY_CHARACTERS = 4096
"""Largest producer-chosen key the semantic gates compatibility-fold.

NFKC can expand one input scalar into many output scalars.  Keeping the source
key bounded before normalisation prevents a parser-bounded statement from
turning one compatibility key into an allocation many times its input size.
"""
MAX_STRUCTURED_KEY_CHARACTERS_TOTAL = 262144
"""Aggregate source-key budget for one semantic scan."""


class StructuredKeyBudget(object):
    """Admit keys only while both compatibility-scan bounds hold."""

    def __init__(self):
        self.characters = 0
        self.refused = 0
        self.exhausted = False

    def accept(self, key):
        if self.exhausted or not isinstance(key, str):
            self.refused += 1
            return False
        if len(key) > MAX_STRUCTURED_KEY_CHARACTERS:
            self.refused += 1
            return False
        if self.characters + len(key) > MAX_STRUCTURED_KEY_CHARACTERS_TOTAL:
            self.exhausted = True
            self.refused += 1
            return False
        self.characters += len(key)
        return True


def block(predicate, key):
    """The named list from a predicate, or None when it is absent or wrong.

    Returning None for both cases is deliberate: the gate that cares about the
    difference reports it, and every other caller wants the same answer, which
    is that there is nothing here to read.
    """
    if not isinstance(predicate, dict):
        return None
    found = predicate.get(key)
    if not isinstance(found, list):
        return None
    return found


def claims(predicate):
    return block(predicate, CLAIMS)


def commands(predicate):
    return block(predicate, COMMANDS)


def label(entry, index, kind):
    """A name for an entry that may not have one, for use in a gate message."""
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        return entry["name"]
    return "%s %d" % (kind, index + 1)


def walk(value):
    """Every (key, value) pair anywhere inside a parsed predicate.

    Used by the gates that have to hold wherever in the predicate a producer
    puts something, rather than only at the top level.
    """
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            for pair in walk(child):
                yield pair
    elif isinstance(value, list):
        for child in value:
            for pair in walk(child):
                yield pair


def compatibility_key(key):
    """Compatibility- and case-fold one bounded producer-chosen key."""
    if not isinstance(key, str):
        raise TypeError("structured key must be a string")
    if len(key) > MAX_STRUCTURED_KEY_CHARACTERS:
        raise ValueError(
            "structured key exceeds the %d-character scan limit"
            % MAX_STRUCTURED_KEY_CHARACTERS
        )
    return unicodedata.normalize("NFKC", key).casefold()


def normalise_key(key):
    """Compatibility-fold a key, then drop case and separators."""
    folded = compatibility_key(key)
    return "".join(character for character in folded if character.isalnum())


def missing(record, required):
    """The required fields a record leaves absent, empty, or blank.

    Absent and empty are one answer here on purpose. A producer that writes
    `"commit": ""` has recorded no commit, and a gate that accepted it would be
    reading the key rather than the value. A field that is legitimately false
    has to be checked separately, because `False` lands in this list.
    """
    if not isinstance(record, dict):
        return list(required)
    return [field for field in required if record.get(field) in (None, "", [], {})]


def check_side(side, which, faults):
    """One side of a comparison: a name, and a digest that parses.

    Shared by every predicate whose deltas name a baseline and a current, so the
    rule that an unidentifiable side fails is written once.
    """
    from . import digests

    if not isinstance(side, dict):
        faults.append("delta %s side is not an object" % which)
        return
    name = side.get("name")
    # A blank name is refused, not merely an absent one. `"   "` is truthy, so a
    # bare truthiness test let a side identify nothing while passing the check that
    # exists to make both ends identifiable. Every other name field in these
    # predicates already required a non-blank string; this one, shared by all three,
    # did not.
    if not isinstance(name, str) or not name.strip():
        faults.append("delta %s side has no name" % which)
    try:
        digests.check(side.get("digest"))
    except digests.DigestError as error:
        faults.append("delta %s side: %s" % (which, error))
