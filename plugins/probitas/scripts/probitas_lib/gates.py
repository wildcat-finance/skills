"""The five gates, run over a dossier and its evidence together.

This is the half that matters. The model writes the narrative and this runs
afterwards, because a model asked to cite its sources produces citation-shaped
sentences at some rate above zero and nothing inside the model catches them.

Gate 3 is the interesting one. It does not merely check that evidence records
carry sources, which the schema already guarantees. It recomputes, from the
evidence alone, every number and hash a truthful dossier could contain, then
fails the document on any it contains that is not in that set. A model that
invents a transaction hash, rounds an amount, or adds a plausible extra market
gets caught by arithmetic rather than by reading.
"""

import re

from . import formatting, registry
from .evidence import COVERAGE_SOURCES

SECTION = re.compile(r"^##\s+(.*)$", re.MULTILINE)

NEGATIVE_SPACE_HEADING = "What could not be established"
INFERRED_HEADING = "Addresses not declared"
SUMMARY_HEADING = "Summary"

# A rating is a word for a verdict followed by the verdict itself. The word
# alone is not one: a document saying it emits no score is doing the opposite
# of taking a view, and a gate that fires on its own boilerplate is a gate
# people learn to ignore.
RATING = re.compile(
    r"\b(rating|score|grade|creditworthiness|tier)\b\s*[:=]\s*"
    r"(?:[A-Fa-f][+-]?\b|\d{1,3}(?:\.\d+)?\s*(?:/|out of)\s*\d{1,3}"
    r"|\d{1,3}(?:\.\d+)?\b)"
    r"|\b(?:rated|scored|graded)\s+(?:[A-Fa-f][+-]?|\d{1,3})\b",
    re.IGNORECASE,
)
RUBRIC = re.compile(r"\brubric\b", re.IGNORECASE)

# "no rating", "without a score", "never graded": a denial, not a verdict.
NEGATED = re.compile(r"\b(no|not|never|without|neither|nor)\b[^.]{0,30}$", re.IGNORECASE)


class Gate:
    def __init__(self, number, name, passed, detail):
        self.number = number
        self.name = name
        self.passed = passed
        self.detail = detail

    def line(self):
        mark = "pass" if self.passed else "FAIL"
        return f"gate {self.number} {self.name}: {mark} -- {self.detail}"


def sections(dossier):
    """Heading text to (start, end) character offsets of its body."""
    found = list(SECTION.finditer(dossier))
    out = {}
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(dossier)
        heading = match.group(1).strip()
        # First occurrence wins. A second section with the same heading is a
        # document doing something odd, and taking the later one would let a
        # summary planted near the top hide behind a real one at the bottom.
        out.setdefault(heading, (match.end(), end))
    return out


def body(dossier, blocks, heading):
    span = blocks.get(heading)
    return dossier[span[0] : span[1]] if span else None


def gate_1_provenance(dossier, payload, blocks):
    """Declared, linked and inferred never blur into one another."""
    tiers = {a["address"]: a["provenance"] for a in payload["subject"]["addresses"]}
    inferred = {a for a, tier in tiers.items() if tier == "inferred"}
    on_record = {a for a, tier in tiers.items() if tier != "inferred"}

    if not inferred:
        return Gate(1, "provenance", True, "no inferred addresses in this run")

    span = blocks.get(INFERRED_HEADING)
    if span is None:
        return Gate(
            1,
            "provenance",
            False,
            f"{len(inferred)} inferred address(es) but no {INFERRED_HEADING!r} section",
        )

    lowered = dossier.lower()
    for address in inferred:
        for match in re.finditer(re.escape(address), lowered):
            if not span[0] <= match.start() < span[1]:
                return Gate(
                    1,
                    "provenance",
                    False,
                    f"inferred address {address} appears outside its own section",
                )

    inferred_body = dossier[span[0] : span[1]].lower()
    for address in on_record:
        if address in inferred_body:
            return Gate(
                1,
                "provenance",
                False,
                f"declared address {address} appears in the inferred section",
            )

    # An address is not the only thing that leaks. A row moved out of the
    # inferred section takes its citation with it and reads as part of the
    # record, so each finding's source has to stay where its tier put it.
    tier_of = {a["address"]: a["provenance"] for a in payload["subject"]["addresses"]}
    for record in payload["records"]:
        citation = formatting.short(record["source"]).lower()
        belongs_inferred = tier_of.get(record["address"]) == "inferred"
        for match in re.finditer(re.escape(citation), lowered):
            inside = span[0] <= match.start() < span[1]
            if belongs_inferred and not inside:
                return Gate(
                    1,
                    "provenance",
                    False,
                    f"a finding against an inferred address ({citation}) "
                    "appears outside its own section",
                )
            if not belongs_inferred and inside:
                return Gate(
                    1,
                    "provenance",
                    False,
                    f"a finding on the record ({citation}) appears in the "
                    "inferred section",
                )

    return Gate(
        1,
        "provenance",
        True,
        f"{len(inferred)} inferred address(es), all held apart",
    )


def gate_2_coverage(dossier, payload, blocks):
    """Every venue is accounted for, and every row says which route answered.

    Rows are counted on the venue and the source together. Keying on the venue
    alone used to collapse two rows into one and keep whichever came last, so a
    run that consulted two routes could lose one route's answer without saying
    anything -- the same silent-overwrite shape as the provenance-tier bug that
    finding S2-R1-02 closed.
    """
    expected = {venue.id for venue in registry.all_venues()}

    seen = {}
    for row in payload["coverage"]:
        venue = row.get("venue")
        source = row.get("source")
        if not row.get("status"):
            return Gate(2, "coverage", False, f"{venue} has no status")
        if source not in COVERAGE_SOURCES:
            return Gate(
                2,
                "coverage",
                False,
                f"{venue} names no source, so the row does not say how it was checked",
            )
        if (venue, source) in seen:
            return Gate(
                2,
                "coverage",
                False,
                f"{venue} carries two {source} rows and one of them would be lost",
            )
        seen[(venue, source)] = row
        # A venue that was actually queried has to say over what range. One
        # that was never queried cannot, and saying otherwise would be worse
        # than the gap it is already declaring.
        if row["status"] in ("checked", "empty") and not row.get("block_range"):
            return Gate(2, "coverage", False, f"{venue} was queried but names no range")
        # An archive row stands on a release. Without one a reader cannot tell
        # which preserved capture answered, and the note that used to carry
        # that identity is prose no gate can hold to it.
        if (
            source == "archive"
            and row["status"] in ("checked", "empty")
            and not row.get("releases")
        ):
            return Gate(
                2,
                "coverage",
                False,
                f"{venue} was read from the archive but names no release",
            )

    venues = {venue for venue, _ in seen}
    missing = sorted(expected - venues)
    if missing:
        return Gate(
            2,
            "coverage",
            False,
            "no coverage row for " + ", ".join(missing),
        )

    span = blocks.get("Coverage")
    if span is None:
        return Gate(2, "coverage", False, "the dossier has no Coverage section")

    # The evidence being complete is not the same as the document saying so.
    # A row deleted from the rendered table would otherwise pass on the
    # strength of a file the reader never sees.
    printed = dossier[span[0] : span[1]].lower()
    # Anchored to the start of a table row rather than looked for anywhere in
    # the section. A venue named in another venue's note would otherwise stand
    # in for its own missing row.
    listed = {
        line.split("|")[1].strip()
        for line in printed.splitlines()
        if line.startswith("|") and line.count("|") >= 2
    }
    names = {v.id: v.name for v in registry.all_venues()}
    for venue in sorted(venues):
        label = names.get(venue, venue).lower()
        if label not in listed and venue.lower() not in listed:
            return Gate(
                2,
                "coverage",
                False,
                f"{venue} has a coverage row but no row of its own in the table",
            )

    checked = sum(1 for r in seen.values() if r["status"] in ("checked", "empty"))
    return Gate(
        2,
        "coverage",
        True,
        f"{len(venues)} venue(s) accounted for over {len(seen)} row(s), "
        f"{checked} queried",
    )


def known_tokens(payload):
    """Every number and hash a truthful dossier could carry.

    Built from the evidence and from the same formatting helpers the renderer
    uses, so the two halves agree without the checker having to trust the
    renderer's output.
    """
    tokens = set()

    def note(text):
        tokens.update(formatting.numeric_tokens(str(text)))

    run = payload.get("run") or {}
    note(run.get("id") or "")
    note(payload["subject"]["entity"])
    for entry in payload["subject"]["addresses"]:
        note(entry["address"])

    for row in payload["coverage"]:
        for key in (
            "venue",
            "status",
            "source",
            "endpoint",
            "block_range",
            "note",
            "records",
            "releases",
        ):
            note(row.get(key) or "")

    for gap in payload["gaps"]:
        note(gap["subject"])
        note(gap["reason"])

    decimals = {}
    for record in payload["records"]:
        values = record["values"]
        market = values.get("market")
        if record["claim"] == "market_terms" and market and "token_decimals" in values:
            decimals[market] = values["token_decimals"]

    for record in payload["records"]:
        note(record["source"])
        note(formatting.short(record["source"]))
        note(record["address"])
        note(record["claim"])
        for key in ("observed_at", "block"):
            if record.get(key) is not None:
                note(record[key])
        if record.get("observed_at") is not None:
            note(formatting.timestamp(record["observed_at"]))

        scale = decimals.get(record["values"].get("market"))
        for value in record["values"].values():
            note(value)
            if isinstance(value, str) and value.lstrip("-").isdigit():
                note(formatting.amount(value))
                note(formatting.bips(value))
                note(formatting.duration(value))
                if scale is not None:
                    note(formatting.amount(value, scale))

    return tokens


def gate_3_sourcing(dossier, payload, blocks):
    """Every assertion traces back to a record, and every record to a citation."""
    for index, record in enumerate(payload["records"]):
        if not str(record.get("source", "")).strip():
            return Gate(3, "sourcing", False, f"record {index} carries no source")

    sources = {record["source"].lower() for record in payload["records"]}
    for match in re.finditer(r"\]\((https?://[^)]+)\)", dossier):
        if match.group(1).lower() not in sources:
            return Gate(
                3,
                "sourcing",
                False,
                f"the dossier cites {match.group(1)}, which is in no record",
            )

    unknown = sorted(formatting.numeric_tokens(dossier) - known_tokens(payload))
    if unknown:
        shown = ", ".join(unknown[:3])
        return Gate(
            3,
            "sourcing",
            False,
            f"{len(unknown)} figure(s) in the dossier trace to no record: {shown}",
        )

    return Gate(
        3,
        "sourcing",
        True,
        f"{len(payload['records'])} record(s) sourced, no unsupported figure",
    )


def gate_4_negative_space(dossier, payload, blocks):
    """What could not be established comes before anything that reads as a verdict."""
    span = blocks.get(NEGATIVE_SPACE_HEADING)
    if span is None:
        return Gate(
            4,
            "negative space",
            False,
            f"no {NEGATIVE_SPACE_HEADING!r} section",
        )
    printed = dossier[span[0] : span[1]]
    if not printed.strip():
        return Gate(4, "negative space", False, "the section is empty")

    # Present but silent is the same as absent. Every gap the run recorded has
    # to be named where a reader will see it.
    lowered_section = printed.lower()
    for gap in payload["gaps"]:
        if gap["subject"].lower() not in lowered_section:
            return Gate(
                4,
                "negative space",
                False,
                f"the run could not establish {gap['subject']!r} and the "
                "section does not say so",
            )

    summary = blocks.get(SUMMARY_HEADING)
    if summary and summary[0] < span[0]:
        return Gate(
            4,
            "negative space",
            False,
            "the summary comes before what could not be established",
        )

    return Gate(
        4,
        "negative space",
        True,
        f"{len(payload['gaps'])} gap(s) stated ahead of the summary",
    )


def gate_5_rating(dossier, payload, blocks):
    """No score without the rubric printed beside it."""
    match = None
    for candidate in RATING.finditer(dossier):
        preceding = dossier[max(0, candidate.start() - 40) : candidate.start()]
        if NEGATED.search(preceding):
            continue
        match = candidate
        break
    if match is None:
        return Gate(5, "rating", True, "no rating emitted")
    if RUBRIC.search(dossier) is None:
        return Gate(
            5,
            "rating",
            False,
            f"the dossier reads as a rating ({match.group(0).strip()!r}) "
            "with no rubric beside it",
        )
    return Gate(5, "rating", True, "a rating is present and a rubric is printed")


GATES = (
    gate_1_provenance,
    gate_2_coverage,
    gate_3_sourcing,
    gate_4_negative_space,
    gate_5_rating,
)


def check(dossier, payload):
    blocks = sections(dossier)
    return [gate(dossier, payload, blocks) for gate in GATES]
