"""The evidence file: the dossier's only permitted source of fact.

A record cannot exist without a source. That is enforced here, at
construction, rather than checked later, because a claim that can be
represented without a citation is a claim that will eventually ship without
one.

Amounts stay strings on the wire. Subgraphs return token amounts as decimal
strings of arbitrary size, and Python integers are unbounded, so the danger is
not overflow but a `float` somewhere quietly rounding a balance.
"""

import json
import re
import unicodedata

PROVENANCE_TIERS = ("declared", "linked", "inferred")

COVERAGE_STATUSES = (
    "checked",  # the adapter ran and returned what it found
    "empty",  # the adapter ran and this address has no history here
    "error",  # the adapter ran and failed; this is not a clean record
    "unimplemented",  # no adapter exists yet
    "unconfigured",  # an adapter exists but the operator supplied no credential
)

_TX_HASH = re.compile(r"\A0x[0-9a-fA-F]{64}\Z")

# No brackets, parentheses, angle brackets, backticks or pipes. A source is
# written into a Markdown link inside a Markdown table, so a closing paren
# escapes the link and takes the rest of the document with it, and a pipe
# escapes the cell and invents a column.
_URL = re.compile(r"\Ahttps?://[^\s()\[\]<>`\\|]+\Z")

MAX_SOURCE_LENGTH = 400
MAX_VALUE_LENGTH = 400

# Names that belong to a thing rather than to a person. Checked first, because
# the guard below is deliberately broad and a market has a name like anything
# else does. Extend this list rather than loosening the guard.
_ENTITY_KEYS = frozenset(
    {
        "market_name",
        "market_symbol",
        "token_name",
        "token_symbol",
        "asset_name",
        "asset_symbol",
        "venue_name",
        "entity_name",
        "market_age",
        "position_age",
    }
)

# Keys naming a person rather than an entity or a position. The specification
# draws this line and the study puts it in the tool rather than in whoever is
# operating it at two in the morning, so it lives here, where a record is made,
# and not in a review checklist. Broad on purpose: a false positive costs one
# line in the list above, and a false negative puts a person in a dossier.
_PERSONAL_KEYS = re.compile(
    r"\A(.*_)?(name|firstname|lastname|surname|fullname|email|phone|telephone"
    r"|dob|birth|birthdate|age|gender|nationality|passport|ssn|nino|address_line"
    r"|street|postcode|zip|employer|employment|job|title|linkedin|twitter"
    r"|telegram|discord|handle|username|ip|geo|location)(_.*)?\Z"
)

_VALUE_KEY = re.compile(r"\A[a-z][a-z0-9_]{0,63}\Z")


class EvidenceError(ValueError):
    """Raised when something tries to enter the evidence file that may not."""


def _require_text(value, field):
    if value is None:
        raise EvidenceError(f"{field} is required and was None")
    if not isinstance(value, str):
        raise EvidenceError(f"{field} must be a string, got {type(value).__name__}")
    stripped = value.strip()
    if not stripped:
        raise EvidenceError(f"{field} is required and was empty")
    return stripped


def classify_source(source):
    """Name the kind of citation this is, or raise.

    Three kinds are allowed, from the specification: a transaction hash, a URL,
    or a document reference. The third is deliberately loose, because a court
    filing or a signed attestation has no canonical form, but it still has to
    be something a reader could go and look at, so it carries a `doc:` prefix
    to mark that a human chose it rather than a machine found it.
    """
    text = _require_text(source, "source")
    # Refused rather than stripped. A source is a citation, and quietly
    # rewriting one is worse than rejecting it: a bidi override inside a URL
    # makes it display as a different address than the one it points at, and a
    # zero-width space hides a character a reader is checking by eye.
    for character in text:
        if unicodedata.category(character).startswith("C"):
            raise EvidenceError(
                "source carries a control or format character "
                f"({character!r}); a citation has to be exactly what it says"
            )
    if len(text) > MAX_SOURCE_LENGTH:
        raise EvidenceError(
            f"source is {len(text)} characters, over the {MAX_SOURCE_LENGTH} limit"
        )
    if _TX_HASH.match(text):
        return "transaction"
    if _URL.match(text):
        return "url"
    if text.startswith("doc:") and len(text) > len("doc:"):
        if any(character in text for character in "()[]<>`\\|"):
            raise EvidenceError(
                "a doc: reference may not carry Markdown punctuation: "
                f"{text!r}"
            )
        return "document"
    raise EvidenceError(
        "source must be a 0x transaction hash, an http(s) URL, "
        f"or a doc: reference; got {text!r}"
    )


class Record:
    """One sourced assertion.

    Construction is the gate. Everything a record needs to be citable is
    required here, so an unsourced or unattributed claim never becomes an
    object in the first place.
    """

    __slots__ = (
        "venue",
        "address",
        "provenance",
        "claim",
        "values",
        "source",
        "source_kind",
        "observed_at",
        "block",
    )

    def __init__(
        self,
        venue,
        address,
        provenance,
        claim,
        values,
        source,
        observed_at=None,
        block=None,
    ):
        self.venue = _require_text(venue, "venue")
        self.address = _require_text(address, "address").lower()
        self.provenance = _require_text(provenance, "provenance")
        if self.provenance not in PROVENANCE_TIERS:
            raise EvidenceError(
                f"provenance must be one of {PROVENANCE_TIERS}, "
                f"got {self.provenance!r}"
            )
        self.claim = _require_text(claim, "claim")
        if not isinstance(values, dict):
            raise EvidenceError("values must be a mapping")
        self.values = {_value_key(k): _wire(v) for k, v in values.items()}
        self.source = _require_text(source, "source")
        self.source_kind = classify_source(self.source)
        self.observed_at = observed_at
        self.block = block

    def to_dict(self):
        out = {
            "venue": self.venue,
            "address": self.address,
            "provenance": self.provenance,
            "claim": self.claim,
            "values": dict(sorted(self.values.items())),
            "source": self.source,
            "source_kind": self.source_kind,
        }
        if self.observed_at is not None:
            out["observed_at"] = int(self.observed_at)
        if self.block is not None:
            out["block"] = int(self.block)
        return out

    def sort_key(self):
        return (
            self.venue,
            self.address,
            self.observed_at if self.observed_at is not None else -1,
            self.block if self.block is not None else -1,
            self.claim,
            self.source,
        )

    def __repr__(self):
        return f"Record({self.venue}, {self.claim}, {self.source})"


def _value_key(key):
    """Vet a value key before it can carry anything into the dossier.

    Two jobs. Keep keys to a boring shape so a rendered table stays a table,
    and refuse the ones that name a person. The evidence file has no field a
    human identity fits in, and this is what makes that true rather than
    merely intended.
    """
    if not isinstance(key, str):
        raise EvidenceError(f"value keys must be strings, got {type(key).__name__}")
    key = key.strip().lower()
    if not _VALUE_KEY.match(key):
        raise EvidenceError(
            f"value key {key!r} is not lowercase alphanumeric with underscores"
        )
    if key in _ENTITY_KEYS:
        return key
    if _PERSONAL_KEYS.match(key):
        raise EvidenceError(
            f"value key {key!r} names a person. Probitas covers entities and "
            "addresses; a dossier that starts profiling people is a different "
            "product and a worse one."
        )
    return key


def _wire(value):
    """Put a value on the wire without letting a float near an amount."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        raise EvidenceError(
            "float values are refused; amounts stay integers or strings so "
            "nothing rounds a balance on the way through"
        )
    if value is None:
        return None
    if not isinstance(value, str):
        raise EvidenceError(
            "values must be strings, integers, booleans or None; got "
            f"{type(value).__name__}. A nested structure would reach the "
            "dossier as a Python repr."
        )
    if len(value) > MAX_VALUE_LENGTH:
        raise EvidenceError(
            f"value is {len(value)} characters, over the {MAX_VALUE_LENGTH} limit"
        )
    return value


class Coverage:
    """One row of the coverage table: what happened when a venue was checked."""

    __slots__ = ("venue", "status", "endpoint", "block_range", "note", "records")

    def __init__(
        self, venue, status, endpoint=None, block_range=None, note=None, records=0
    ):
        self.venue = _require_text(venue, "venue")
        self.status = _require_text(status, "status")
        if self.status not in COVERAGE_STATUSES:
            raise EvidenceError(
                f"status must be one of {COVERAGE_STATUSES}, got {self.status!r}"
            )
        self.endpoint = endpoint
        self.block_range = block_range
        self.note = note
        self.records = int(records)

    def to_dict(self):
        return {
            "venue": self.venue,
            "status": self.status,
            "endpoint": self.endpoint,
            "block_range": self.block_range,
            "note": self.note,
            "records": self.records,
        }


class Gap:
    """Something the run could not establish. The negative space, itemised."""

    __slots__ = ("subject", "reason")

    def __init__(self, subject, reason):
        self.subject = _require_text(subject, "subject")
        self.reason = _require_text(reason, "reason")

    def to_dict(self):
        return {"subject": self.subject, "reason": self.reason}


class Evidence:
    """Everything one run gathered, in a form the renderer and gates can read."""

    def __init__(self, entity, addresses, run_id=None, collected_at=None):
        self.entity = _require_text(entity, "entity")
        self.addresses = {}
        for address, provenance in addresses:
            text = _require_text(address, "address").lower()
            if provenance not in PROVENANCE_TIERS:
                raise EvidenceError(
                    f"provenance must be one of {PROVENANCE_TIERS}, got {provenance!r}"
                )
            existing = self.addresses.get(text)
            if existing is not None and existing != provenance:
                # Gate 1. Silently keeping the last tier would let an inferred
                # address be read as declared, or the reverse, and the whole
                # point of the tiers is that they never blur.
                raise EvidenceError(
                    f"{text} was given as both {existing} and {provenance}; "
                    "an address holds one provenance tier"
                )
            self.addresses[text] = provenance
        if not self.addresses:
            raise EvidenceError("at least one address is required")
        self.run_id = run_id
        self.collected_at = collected_at
        self.records = []
        self.coverage = []
        self.gaps = []

    def declared(self):
        return sorted(a for a, p in self.addresses.items() if p == "declared")

    def by_tier(self, tier):
        return sorted(a for a, p in self.addresses.items() if p == tier)

    def add_record(self, record):
        if not isinstance(record, Record):
            raise EvidenceError("only Record instances may enter the evidence file")
        if record.address not in self.addresses:
            raise EvidenceError(
                f"record cites {record.address}, which is not a subject address"
            )
        self.records.append(record)

    def add_coverage(self, coverage):
        self.coverage.append(coverage)

    def add_gap(self, gap):
        self.gaps.append(gap)

    def to_dict(self):
        """Serialise deterministically.

        Two runs over the same findings have to produce the same bytes, or the
        output cannot be diffed and a reader cannot tell a real change from a
        reordering.
        """
        return {
            "schema": 1,
            "run": {"id": self.run_id, "collected_at": self.collected_at},
            "subject": {
                "entity": self.entity,
                "addresses": [
                    {"address": a, "provenance": self.addresses[a]}
                    for a in sorted(self.addresses)
                ],
            },
            "records": [r.to_dict() for r in sorted(self.records, key=Record.sort_key)],
            "coverage": [
                c.to_dict() for c in sorted(self.coverage, key=lambda c: c.venue)
            ],
            "gaps": [
                g.to_dict()
                for g in sorted(self.gaps, key=lambda g: (g.subject, g.reason))
            ],
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, sort_keys=False) + "\n"
