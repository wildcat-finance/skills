"""The dataset predicate: a released set of data files, and what it leaves out.

Its subject is a released file rather than compiled bytecode. What it adds to the
core block is the part that makes a dataset release checkable rather than merely
published: which inputs it was derived from, which tool turned them into the
released files, what interval it claims to describe, and where inside that
interval it describes nothing.

Two gates belong here, as they do for any predicate. Gate 2 holds that the
environment is recoverable, which is why a tool name and a version on their own
fail: without the parameters and the input digests nobody produces the same
files. Gate 5 holds that a comparison names both sides, so a delta against a
release that cannot be identified fails rather than quietly reporting no change.

Two further checks are this predicate's own, in the same sense that `audits` and
`deployments` belong to the Solidity release predicate. The coverage check is
gate 3's rule applied to the field a dataset can most easily use to mislead: an
interval printed with no gaps reads as complete. The inputs check refuses an
input that carries neither a digest nor a recorded reason for not having one,
because a locator on its own records nothing about what was read.

Coverage bounds are integers. Block heights are integers, timestamps are not
necessarily, and comparing across the two representations is how an interval
check comes to pass on values it never really ordered. A producer with
timestamps records them as integers or uses a different dimension.
"""

import ntpath
import posixpath

from .. import deltas as deltas_module
from .. import digests
from ..core_predicate import NEEDS_REASON, check_side, missing
from ..gates import Gate

TYPE = "https://ariadne.wildcat.finance/dataset/v1"
SUMMARY = "a dataset release: inputs, producer, released files, coverage and gaps"

PRODUCER_REQUIRED = ("tool", "tool_version", "command", "parameters_digest")
INPUT_REQUIRED = ("name", "locator")
DATASET_SUBJECT_REQUIRED = ("name", "path", "digest", "record_count")
COVERAGE_REQUIRED = ("dimension", "start", "end")
COVERAGE_KEYS = COVERAGE_REQUIRED + ("gaps",)
"""Every key coverage carries. `gaps` is held apart from `COVERAGE_REQUIRED`
because `missing()` reads an empty list as absent, and an empty gap list is the
answer this predicate most wants a producer to be able to give."""
GAP_REQUIRED = ("start", "end", "reason")
DELTA_SECTIONS = ("records",)

PREDICATE_FIELDS = (
    "producer",
    "inputs",
    "dataset_subjects",
    "coverage",
    "deltas",
    "claims",
    "commands",
)
"""Everything this predicate carries, the last two inherited from the core."""

REQUIRED_FIELDS = PREDICATE_FIELDS
"""Nothing here is optional. A release derived from nothing upstream records an
empty `inputs` array, which says the question was asked and answered; leaving the
block out would leave it open."""

RECORD_KEYS = ("added", "removed", "changed")
"""What a `records` section may carry. Unknown sections at the `deltas` level are
refused, so an unknown key one level down cannot pass either: both are undeclared
content sitting inside a digested comparison."""

BOTH_SIDED = ("changed",)
"""Sections whose entries describe a change rather than a name, so each entry
carries what it was and what it became."""

INPUT_FIELDS = frozenset({"name", "locator", "digest", "disposition", "reason"})

INPUT_DISPOSITIONS = NEEDS_REASON
"""What an input may say instead of carrying a digest.

`passed` is not on this list. An input that was read has a digest, so `passed`
with no digest is a one-word way around the rule this check exists for: it would
assert the input was read while recording nothing about what was read. The
remaining dispositions are the ones that describe an absence, and each needs a
reason.
"""
GAP_FIELDS = frozenset({"start", "end", "reason"})


def usable_path(value):
    """True for a release-relative path a reader can resolve safely.

    A consumer resolves `path` against a release directory. An absolute path or one
    carrying a `..` segment resolves somewhere else, so a statement using either
    describes a file the release does not hold and points a careless reader out of
    the tree. The capture path never produces one; a statement written by hand can.
    """
    if not isinstance(value, str) or not value.strip():
        return False
    # A single backslash separates path segments on Windows, so it is normalised
    # before anything looks for a traversal. An earlier version replaced only a
    # doubled backslash, which left "a\\..\\..\\b" reaching a POSIX consumer as one
    # odd filename and a Windows consumer as a traversal out of the tree. A UNC
    # prefix survives the change: it normalises to a leading slash, which the next
    # test refuses.
    normalised = value.replace("\\", "/")
    if normalised.startswith("/"):
        return False
    if ntpath.isabs(value) or posixpath.isabs(value):
        return False
    parts = normalised.split("/")
    return ".." not in parts and "" not in parts[1:]


def stated(value):
    """True for a non-blank string.

    Used for the fields whose only job is to let a reader find something again. A
    field holding `"   "` or a number satisfies a presence check while naming
    nothing, which is the shape this predicate spends its gates refusing.
    """
    return isinstance(value, str) and bool(value.strip())


def whole_number(value):
    """True for an integer this predicate will order. `bool` is not one.

    Python makes `True` an integer and `True < 5` an answer. A coverage bound of
    `true` is a producer error, and silently ordering it would hide that.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def gate_2_environment(statement):
    """A tool name is not a build description.

    Recoverable means somebody else can produce the same files: the tool and its
    version, the argv that ran, a digest over the parameters it was given, and a
    digest or a recorded absence for every input. Each released file must also be
    a subject of the statement, so the predicate cannot describe files the
    statement does not cover.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(2, "environment", False, "no predicate to describe a producer")

    faults = []

    producer = predicate.get("producer")
    absent = missing(producer, PRODUCER_REQUIRED)
    if absent:
        faults.append("producer is missing %s" % ", ".join(absent))
    else:
        for field in ("tool", "tool_version"):
            if not stated(producer.get(field)):
                faults.append("producer %s must name something" % field)
        command = producer.get("command")
        if not isinstance(command, list) or not all(stated(word) for word in command):
            faults.append(
                "producer command must be an argv of non-empty strings; a word that "
                "is empty or only whitespace is not what ran"
            )
        try:
            digests.check(producer["parameters_digest"])
        except digests.DigestError as error:
            faults.append("producer parameters_digest: %s" % error)

    inputs = predicate.get("inputs")
    if not isinstance(inputs, list):
        faults.append("inputs must be an array")
    else:
        for index, entry in enumerate(inputs):
            label = entry.get("name") if isinstance(entry, dict) else None
            label = label or "input %d" % (index + 1)
            absent = missing(entry, INPUT_REQUIRED)
            if absent:
                faults.append("%s is missing %s" % (label, ", ".join(absent)))
                continue
            for field in INPUT_REQUIRED:
                if not stated(entry.get(field)):
                    faults.append("%s %s must name something" % (label, field))

    subjects = predicate.get("dataset_subjects")
    if not isinstance(subjects, list) or not subjects:
        faults.append("dataset_subjects must be a non-empty array")
    else:
        seen = {}
        for index, entry in enumerate(subjects):
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                if entry["path"] in seen:
                    faults.append(
                        "path %s is listed twice; one file cannot carry two "
                        "digests, and the release digest is over this listing"
                        % entry["path"]
                    )
                seen[entry["path"]] = index
        for index, entry in enumerate(subjects):
            label = entry.get("name") if isinstance(entry, dict) else None
            label = label or "dataset subject %d" % (index + 1)
            absent = missing(entry, DATASET_SUBJECT_REQUIRED)
            # A file with no records is a real thing to release, and `0` lands
            # in `missing` as though the count were absent.
            if "record_count" in absent and isinstance(entry, dict):
                if entry.get("record_count") == 0:
                    absent = [f for f in absent if f != "record_count"]
            if absent:
                faults.append("%s is missing %s" % (label, ", ".join(absent)))
                continue
            if not stated(entry["name"]):
                faults.append("dataset subject %d has no name" % (index + 1))
            if not whole_number(entry["record_count"]) or entry["record_count"] < 0:
                faults.append(
                    "%s record_count must be a whole number of records, not %r"
                    % (label, entry["record_count"])
                )
            if not usable_path(entry["path"]):
                faults.append(
                    "%s path %r is not a release-relative path; a reader resolving "
                    "it against the release would land outside it"
                    % (label, entry["path"])
                )
            try:
                digests.check(entry["digest"])
            except digests.DigestError as error:
                faults.append("%s digest: %s" % (label, error))
                continue
            if not statement.covers(entry["digest"]):
                faults.append(
                    "%s is not a subject of this statement" % label
                )

    if faults:
        return Gate(2, "environment", False, "; ".join(faults))
    return Gate(
        2,
        "environment",
        True,
        "%s %s, %d input(s), %d released file(s)"
        % (
            predicate["producer"]["tool"],
            predicate["producer"]["tool_version"],
            len(predicate["inputs"]),
            len(predicate["dataset_subjects"]),
        ),
    )


def section_faults(section, body):
    """Gate 5 inside a section: a listed change names both of its sides."""
    faults = []
    unknown = sorted(set(body) - set(RECORD_KEYS))
    if unknown:
        faults.append(
            "deltas %s carries unknown keys: %s" % (section, ", ".join(unknown))
        )
    for key, entries in body.items():
        if key not in RECORD_KEYS:
            continue
        if not isinstance(entries, list):
            faults.append("deltas %s.%s must be an array" % (section, key))
            continue
        if key not in BOTH_SIDED:
            for index, entry in enumerate(entries):
                if not stated(entry):
                    faults.append(
                        "deltas %s.%s[%d] identifies no record" % (section, key, index)
                    )
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                faults.append(
                    "deltas %s.%s[%d] is not an object" % (section, key, index)
                )
                continue
            absent = [side for side in ("baseline", "current") if side not in entry]
            if absent:
                faults.append(
                    "deltas %s.%s[%d] names no %s"
                    % (section, key, index, " or ".join(absent))
                )
                continue
            for side in ("baseline", "current"):
                if not stated(entry[side]):
                    faults.append(
                        "deltas %s.%s[%d] %s identifies no record"
                        % (section, key, index, side)
                    )
    return faults


def gate_5_deltas(statement):
    """A comparison fails when either end cannot be identified exactly.

    The absent case is a claim of its own. A first release carries
    `"baseline": null` with a reason, because leaving the block out would read as
    nothing having changed rather than as there being nothing to change from.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(5, "deltas", False, "no predicate to carry a comparison")
    if "deltas" not in predicate:
        return Gate(
            5,
            "deltas",
            False,
            "predicate has no deltas block; a release with nothing to compare "
            "against says so with a null baseline and a reason",
        )

    deltas = predicate["deltas"]
    if not isinstance(deltas, dict):
        return Gate(5, "deltas", False, "deltas must be an object")

    faults = []
    content = {
        section: deltas.get(section)
        for section in DELTA_SECTIONS
        if not deltas_module.empty(deltas.get(section))
    }
    unknown = sorted(
        set(deltas) - set(DELTA_SECTIONS) - {"baseline", "current", "reason"}
    )
    if unknown:
        faults.append("deltas carries unknown sections: %s" % ", ".join(unknown))
    for section in DELTA_SECTIONS:
        if section not in deltas:
            continue
        if not isinstance(deltas[section], dict):
            # A section that is not an object reads as empty to `empty()`, so
            # without this a delta of "records": "all of them" would pass and
            # report no differences.
            faults.append("deltas %s must be an object" % section)
            continue
        faults.extend(section_faults(section, deltas[section]))

    # The current side is this release, whether or not there is a baseline. The
    # null-baseline branch used to return before reaching this, so a first release
    # could name a current side with no name and no digest and still verify.
    check_side(deltas.get("current"), "current", faults)
    if not faults and not statement.covers(deltas["current"]["digest"]):
        faults.append("delta current side is not a subject of this statement")

    if deltas.get("baseline") is None:
        reason = deltas.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            faults.append("a null baseline needs a reason")
        if content:
            faults.append(
                "deltas record %s against a null baseline" % ", ".join(sorted(content))
            )
        if faults:
            return Gate(5, "deltas", False, "; ".join(faults))
        return Gate(
            5,
            "deltas",
            True,
            "%s, no baseline: %s"
            % (deltas["current"]["name"], deltas["reason"].strip()),
        )

    check_side(deltas.get("baseline"), "baseline", faults)
    if not faults and deltas["baseline"]["digest"] == deltas["current"]["digest"]:
        # A release compared against itself reports no differences and means
        # nothing. Left unchecked it reads as a release that changed nothing.
        faults.append(
            "delta baseline and current are the same release; a comparison against "
            "itself records nothing"
        )
    if faults:
        return Gate(5, "deltas", False, "; ".join(faults))

    return Gate(
        5,
        "deltas",
        True,
        "%s against %s, %s"
        % (
            deltas["current"]["name"],
            deltas["baseline"]["name"],
            ", ".join(sorted(content)) if content else "no differences recorded",
        ),
    )


def gate_coverage(statement):
    """An interval printed with no gaps reads as complete.

    Not one of the seven. It is gate 3's rule applied to the field this predicate
    could most easily use to imply something it did not establish. An absent
    `gaps` key fails; an empty array passes and asserts that the producer looked.
    """
    predicate = statement.predicate
    coverage = predicate.get("coverage") if isinstance(predicate, dict) else None
    if coverage is None:
        return Gate(
            None,
            "coverage",
            False,
            "predicate has no coverage block; a release states the interval it "
            "describes",
        )
    if not isinstance(coverage, dict):
        return Gate(None, "coverage", False, "coverage must be an object")

    faults = []
    absent = [f for f in COVERAGE_REQUIRED if coverage.get(f) is None]
    if absent:
        faults.append("coverage is missing %s" % ", ".join(absent))
    if "gaps" not in coverage:
        faults.append(
            "coverage has no gaps block; an absent record is not an empty one"
        )

    if faults:
        return Gate(None, "coverage", False, "; ".join(faults))

    if not isinstance(coverage["dimension"], str) or not coverage["dimension"].strip():
        faults.append("coverage dimension must name something")
    for field in ("start", "end"):
        if not whole_number(coverage[field]):
            faults.append("coverage %s must be a whole number" % field)
    if faults:
        return Gate(None, "coverage", False, "; ".join(faults))

    start, end = coverage["start"], coverage["end"]
    if start > end:
        faults.append("coverage starts at %d and ends at %d" % (start, end))

    gaps = coverage["gaps"]
    if not isinstance(gaps, list):
        return Gate(None, "coverage", False, "coverage gaps must be an array")

    ranges = []
    for index, gap in enumerate(gaps):
        label = "gap %d" % (index + 1)
        absent = missing(gap, GAP_REQUIRED)
        if isinstance(gap, dict):
            for field in ("start", "end"):
                if gap.get(field) == 0 and field in absent:
                    absent = [f for f in absent if f != field]
            # `missing` reads "" as absent but not `"   "` or `1.5`. The reason is
            # the record, so neither whitespace nor a number is one, the same way
            # gate 3 treats a claim reason.
            if "reason" not in absent and not stated(gap.get("reason")):
                absent = absent + ["reason"]
            unknown = sorted(set(gap) - GAP_FIELDS)
            if unknown:
                faults.append("%s carries unknown fields: %s" % (label, ", ".join(unknown)))
        if absent:
            faults.append("%s is missing %s" % (label, ", ".join(absent)))
            continue
        if not whole_number(gap["start"]) or not whole_number(gap["end"]):
            faults.append("%s bounds must be whole numbers" % label)
            continue
        if gap["start"] > gap["end"]:
            faults.append(
                "%s starts at %d and ends at %d" % (label, gap["start"], gap["end"])
            )
            continue
        if gap["start"] < start or gap["end"] > end:
            faults.append(
                "%s runs %d to %d, outside the coverage %d to %d"
                % (label, gap["start"], gap["end"], start, end)
            )
            continue
        ranges.append((gap["start"], gap["end"], label))

    ranges.sort()
    for earlier, later in zip(ranges, ranges[1:]):
        if later[0] <= earlier[1]:
            faults.append(
                "%s and %s overlap between %d and %d"
                % (earlier[2], later[2], later[0], earlier[1])
            )

    if faults:
        return Gate(None, "coverage", False, "; ".join(faults))
    return Gate(
        None,
        "coverage",
        True,
        "%s %d to %d, %d gap(s) recorded"
        % (coverage["dimension"], start, end, len(gaps)),
    )


def gate_inputs(statement):
    """An input carries a digest, or a reason it does not.

    A locator on its own records nothing about what was read, and nothing about
    whether it could be read at all. The absence is a disposition from the core
    vocabulary with a reason, which is the same shape a skipped claim uses.
    """
    predicate = statement.predicate
    inputs = predicate.get("inputs") if isinstance(predicate, dict) else None
    if inputs is None:
        return Gate(
            None,
            "inputs",
            False,
            "predicate has no inputs block; a release derived from nothing "
            "records an empty array",
        )
    if not isinstance(inputs, list):
        return Gate(None, "inputs", False, "inputs must be an array")

    faults = []
    digested = 0
    absent = 0
    for index, entry in enumerate(inputs):
        label = "input %d" % (index + 1)
        if not isinstance(entry, dict):
            faults.append("%s is not an object" % label)
            continue
        label = entry.get("name") or label
        unknown = sorted(set(entry) - INPUT_FIELDS)
        if unknown:
            faults.append("%s carries unknown fields: %s" % (label, ", ".join(unknown)))
        has_digest = entry.get("digest") is not None
        disposition = entry.get("disposition")
        if has_digest:
            try:
                digests.check(entry["digest"])
            except digests.DigestError as error:
                faults.append("%s digest: %s" % (label, error))
                continue
            digested += 1
            continue
        if disposition is None:
            faults.append(
                "%s carries neither a digest nor a disposition; a locator alone "
                "records nothing about what was read" % label
            )
            continue
        if disposition == "passed":
            faults.append(
                "%s is passed with no digest; an input that was read has one, and "
                "passed without it records nothing about what was read" % label
            )
            continue
        if disposition not in INPUT_DISPOSITIONS:
            faults.append(
                "%s has disposition %r, outside %s"
                % (label, disposition, ", ".join(INPUT_DISPOSITIONS))
            )
            continue
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            faults.append(
                "%s is %s with no reason; the reason is the record"
                % (label, disposition)
            )
            continue
        absent += 1

    if faults:
        return Gate(None, "inputs", False, "; ".join(faults))
    return Gate(
        None,
        "inputs",
        True,
        "%d input(s), %d digested, %d recorded absent" % (len(inputs), digested, absent),
    )


def gate_fields(statement):
    """Nothing outside the shape.

    Absence is left to the gate that owns each field: gate 2 for the producer and
    the released files, gate 5 for deltas, the coverage check for coverage, gate 3
    for claims and commands.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(None, "predicate-fields", False, "predicate is not an object")
    unknown = sorted(set(predicate) - set(PREDICATE_FIELDS))
    if unknown:
        return Gate(
            None,
            "predicate-fields",
            False,
            "predicate carries fields this type does not define: %s"
            % ", ".join(unknown),
        )
    return Gate(None, "predicate-fields", True, "no fields outside the shape")


def check(statement):
    return [
        gate_2_environment(statement),
        gate_5_deltas(statement),
        gate_fields(statement),
        gate_coverage(statement),
        gate_inputs(statement),
    ]
