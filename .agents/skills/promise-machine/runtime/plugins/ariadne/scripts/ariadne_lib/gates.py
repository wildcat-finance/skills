"""The five core gates, run over any statement whatever its predicate.

These are the part a bare in-toto statement does not carry. A statement can be
well formed, correctly signed, and still say nothing a reader can rely on: a
result attached to a branch rather than to bytes, a check that quietly vanished
when it failed, a verdict dressed as a measurement, a command nobody could
re-run, or a payload asserting its own trustworthiness.

Gates 2 and 5 are not here. They are shape a predicate fills in, and the
verifier reports that it could not check them when the predicate type is one it
does not know.

Every gate returns rather than raises. A verifier's job is to report all five
lines, not to stop at the first thing it disliked.
"""

from . import core_predicate, digests

CONCLUSION_KEYS = frozenset(
    {
        "safe",
        "secure",
        "verdict",
        "conclusion",
        "approved",
        "approval",
        "certified",
        "guarantee",
        "guaranteed",
        "riskfree",
        "trusted",
        "rating",
        "score",
        "grade",
        "assurance",
        "recommendation",
    }
)
"""Gate 4. Normalised, so `risk_free` and `riskFree` are the same key."""

AUTHORSHIP_KEYS = frozenset(
    {
        "signedby",
        "verifiedby",
        "attestedby",
        "verified",
        "author",
        "authors",
        "authenticated",
        "notarised",
        "notarized",
    }
)
"""Gate 7. Authorship comes from a signature somebody checked, or from nowhere."""


def scanned(statement):
    """Every key inside a statement that a producer chooses the content of.

    The predicate, and also each subject's annotations and other descriptor
    fields. A verdict smuggled into `subject[0].annotations` is the same
    smuggling as one in the predicate, and scanning only the predicate would
    have left the shorter route open.
    """
    for pair in core_predicate.walk(statement.predicate):
        yield pair
    for subject in statement.subjects:
        for pair in core_predicate.walk(subject.extra):
            yield pair


class Gate(object):
    def __init__(self, number, name, passed, detail):
        self.number = number
        self.name = name
        self.passed = passed
        self.detail = detail

    def line(self):
        mark = "pass" if self.passed else "FAIL"
        label = "gate %d" % self.number if self.number else "check"
        return "%s %s: %s -- %s" % (label, self.name, mark, self.detail)

    def to_dict(self):
        return {
            "gate": self.number,
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


def _limit(limits, name):
    """One positive predicate-owned core-work limit, or no extra limit."""
    if not isinstance(limits, dict):
        return None
    value = limits.get(name)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def gate_1_subjects(statement, limits=None):
    """Every claim names the exact digest it covers.

    A result tied to a repository or a branch is the thing this gate exists to
    refuse. Those move. A digest does not.
    """
    found = core_predicate.claims(statement.predicate)
    if found is None:
        # Whether the block has to be there is gate 3's question. Failing here
        # as well would report one fault twice and tell a reader that two
        # separate things went wrong.
        return Gate(1, "subject-naming", True, "no claims block; gate 3 covers that")
    if not found:
        return Gate(1, "subject-naming", True, "no claims recorded")

    faults = []
    claim_limit = _limit(limits, "claims")
    subject_limit = _limit(limits, "subjects")
    if claim_limit is not None and len(found) > claim_limit:
        faults.append(
            "claims has %d entries; this predicate reads at most %d"
            % (len(found), claim_limit)
        )
    checked_claims = found[:claim_limit] if claim_limit is not None else found
    checked_subjects = (
        statement.subjects[:subject_limit]
        if subject_limit is not None
        else statement.subjects
    )
    for index, claim in enumerate(checked_claims):
        name = core_predicate.label(claim, index, "claim")
        if not isinstance(claim, dict):
            faults.append("%s is not an object" % name)
            continue
        subject = claim.get("subject")
        if subject is None:
            faults.append("%s names no subject" % name)
            continue
        if not isinstance(subject, dict):
            faults.append(
                "%s names %r rather than a digest set" % (name, subject)
            )
            continue
        try:
            digests.check(subject)
        except digests.DigestError as error:
            faults.append("%s: %s" % (name, error))
            continue
        if not any(digests.agree(entry.digest, subject) for entry in checked_subjects):
            faults.append(
                "%s names %s, which is not a subject of this statement"
                % (name, digests.short(subject))
            )

    if faults:
        return Gate(1, "subject-naming", False, "; ".join(faults))
    return Gate(
        1,
        "subject-naming",
        True,
        "%d claim(s), each naming a subject of this statement" % len(found),
    )


def gate_3_absence(statement, limits=None):
    """Skipped, failed, timed-out and redacted work stays in the record.

    The block itself is required. A predicate that omits `claims` has not
    recorded that nothing was checked; it has left the question open, which is
    the silence this gate exists to close.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(3, "absence", False, "no predicate to carry a record")
    for key in (core_predicate.CLAIMS, core_predicate.COMMANDS):
        if key not in predicate:
            return Gate(
                3,
                "absence",
                False,
                "predicate has no %s block; an absent record is not an empty "
                "one" % key,
            )
        if not isinstance(predicate[key], list):
            return Gate(3, "absence", False, "%s must be an array" % key)

    faults = []
    counts = {}
    claims = predicate[core_predicate.CLAIMS]
    claim_limit = _limit(limits, "claims")
    if claim_limit is not None and len(claims) > claim_limit:
        faults.append(
            "claims has %d entries; this predicate reads at most %d"
            % (len(claims), claim_limit)
        )
    checked_claims = claims[:claim_limit] if claim_limit is not None else claims
    for index, claim in enumerate(checked_claims):
        name = core_predicate.label(claim, index, "claim")
        if not isinstance(claim, dict):
            faults.append("%s is not an object" % name)
            continue
        unknown = sorted(set(claim) - core_predicate.CLAIM_FIELDS)
        if unknown:
            faults.append("%s carries unknown fields: %s" % (name, ", ".join(unknown)))
        disposition = claim.get("disposition")
        if disposition is None:
            faults.append("%s has no disposition" % name)
            continue
        if disposition not in core_predicate.DISPOSITIONS:
            faults.append(
                "%s has disposition %r, outside %s"
                % (name, disposition, ", ".join(core_predicate.DISPOSITIONS))
            )
            continue
        counts[disposition] = counts.get(disposition, 0) + 1
        if disposition in core_predicate.NEEDS_REASON:
            reason = claim.get("reason")
            if not isinstance(reason, str) or not reason.strip():
                faults.append(
                    "%s is %s with no reason; the reason is the record"
                    % (name, disposition)
                )

    if faults:
        return Gate(3, "absence", False, "; ".join(faults))
    if not counts:
        return Gate(3, "absence", True, "no claims recorded, and the block says so")
    tally = ", ".join("%d %s" % (counts[k], k) for k in sorted(counts))
    return Gate(3, "absence", True, tally)


def gate_4_conclusions(statement):
    """A result records what ran, not what it means.

    Passing a property records the property and the run. It does not record
    that the artefact is safe, and a statement that says so is doing the reader
    a disservice this gate declines to carry.

    The check is over keys, not prose. A `reason` reading "we think it's fine"
    passes, and no wordlist over free text would catch that without failing
    honest sentences ten times as often. What the gate buys is that a verdict
    cannot become a field another tool reads as structured data.
    """
    faults = []
    for key, _ in scanned(statement):
        if core_predicate.normalise_key(key) in CONCLUSION_KEYS:
            faults.append(key)
    if faults:
        return Gate(
            4,
            "no-conclusions",
            False,
            "statement carries verdict key(s): %s" % ", ".join(sorted(set(faults))),
        )
    return Gate(4, "no-conclusions", True, "no verdict keys in the statement")


def gate_6_determinism(statement, limits=None):
    """Replay separates what must match byte for byte from what cannot.

    Bytecode and unit-test output can require an exact match. Timing and fuzz
    coverage cannot. A command that declares neither cannot be replayed by
    anyone but its author.
    """
    found = core_predicate.commands(statement.predicate)
    if found is None:
        return Gate(6, "determinism", True, "no commands block; gate 3 covers that")
    if not found:
        return Gate(6, "determinism", True, "no commands recorded")

    faults = []
    counts = {}
    command_limit = _limit(limits, "commands")
    word_limit = _limit(limits, "command_words")
    if command_limit is not None and len(found) > command_limit:
        faults.append(
            "commands has %d entries; this predicate reads at most %d"
            % (len(found), command_limit)
        )
    checked_commands = found[:command_limit] if command_limit is not None else found
    for index, command in enumerate(checked_commands):
        name = core_predicate.label(command, index, "command")
        if not isinstance(command, dict):
            faults.append("%s is not an object" % name)
            continue
        unknown = sorted(set(command) - core_predicate.COMMAND_FIELDS)
        if unknown:
            faults.append("%s carries unknown fields: %s" % (name, ", ".join(unknown)))
        argv = command.get("argv")
        if not isinstance(argv, list) or not argv:
            faults.append("%s has no argv; nobody else could run it" % name)
        elif word_limit is not None and len(argv) > word_limit:
            faults.append(
                "%s has %d argv entries; this predicate reads at most %d"
                % (name, len(argv), word_limit)
            )
        elif not all(
            isinstance(word, str)
            for word in (argv[:word_limit] if word_limit is not None else argv)
        ):
            faults.append("%s has an argv entry that is not a string" % name)
        determinism = command.get("determinism")
        if determinism is None:
            faults.append("%s declares no determinism class" % name)
            continue
        if determinism not in core_predicate.DETERMINISM:
            faults.append(
                "%s declares %r, outside %s"
                % (name, determinism, ", ".join(core_predicate.DETERMINISM))
            )
            continue
        counts[determinism] = counts.get(determinism, 0) + 1
        if determinism == "exact":
            output = command.get("output_digest")
            if output is None:
                faults.append(
                    "%s is exact with no output digest; there would be nothing "
                    "to compare a replay against" % name
                )
                continue
            try:
                digests.check(output)
            except digests.DigestError as error:
                faults.append("%s output digest: %s" % (name, error))

    if faults:
        return Gate(6, "determinism", False, "; ".join(faults))
    tally = ", ".join("%d %s" % (counts[k], k) for k in sorted(counts))
    return Gate(6, "determinism", True, tally)


def gate_7_authorship(statement):
    """A payload may not vouch for itself.

    Signing is optional and verification is not. A statement that carries its
    own author, or says inside the signed bytes that it was verified, is the
    badge this whole project exists to replace.
    """
    faults = []
    for key, _ in scanned(statement):
        if core_predicate.normalise_key(key) in AUTHORSHIP_KEYS:
            faults.append(key)
    if faults:
        return Gate(
            7,
            "authorship",
            False,
            "statement asserts its own authorship or verification: %s"
            % ", ".join(sorted(set(faults))),
        )
    return Gate(
        7,
        "authorship",
        True,
        "the payload claims no author of its own",
    )


CORE_GATES = (
    (1, gate_1_subjects),
    (3, gate_3_absence),
    (4, gate_4_conclusions),
    (6, gate_6_determinism),
    (7, gate_7_authorship),
)

PREDICATE_GATES = (2, 5)
"""Owned by a predicate: the environment is recoverable, deltas name both sides."""


def run(statement, limits=None):
    """Every core gate, in order, whatever the predicate type."""
    return [
        gate_1_subjects(statement, limits),
        gate_3_absence(statement, limits),
        gate_4_conclusions(statement),
        gate_6_determinism(statement, limits),
        gate_7_authorship(statement),
    ]
