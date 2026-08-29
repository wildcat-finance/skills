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

import re
import unicodedata

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

CONCLUSION_COMPOUND_SUFFIXES = frozenset(
    {"level", "outcome", "result", "state", "status", "value"}
)
CONCLUSION_COMPOUND_KEYS = frozenset(
    root + suffix
    for root in CONCLUSION_KEYS
    for suffix in CONCLUSION_COMPOUND_SUFFIXES
)
CONCLUSION_CONTEXT_TOKENS = frozenset({"audit", "risk", "safety", "security"})

AUTHORSHIP_KEYS = frozenset(
    {
        "signed",
        "signedby",
        "signer",
        "signatory",
        "verifiedby",
        "verifier",
        "attestedby",
        "attester",
        "verified",
        "author",
        "authors",
        "creator",
        "publisher",
        "authenticated",
        "authenticatedby",
        "signatureverified",
        "signaturevalid",
        "notarised",
        "notarisedby",
        "notarized",
        "notarizedby",
        "notary",
    }
)
"""Gate 7. Authorship comes from a signature somebody checked, or from nowhere."""

AUTHORSHIP_COMPOUND_ROOTS = frozenset(
    {
        "author",
        "authorship",
        "authenticated",
        "authentication",
        "creator",
        "publisher",
        "signed",
        "signer",
        "signing",
        "signature",
        "signatory",
        "verified",
        "verifier",
        "verification",
        "attested",
        "attester",
        "attestation",
        "notarised",
        "notarisation",
        "notarized",
        "notarization",
        "notary",
    }
)
AUTHORSHIP_COMPOUND_SUFFIXES = ("identity", "status")
AUTHORSHIP_COMPOUND_KEYS = frozenset(
    root + suffix
    for root in AUTHORSHIP_COMPOUND_ROOTS
    for suffix in AUTHORSHIP_COMPOUND_SUFFIXES
)
"""Direct authorship and verification compounds after key normalisation.

`signature_status` and `signerIdentity` make the same self-authentication claim
as `signature_verified` and `signer`. The roots and suffixes stay finite so a
generic business `status` or `identity` field is not reclassified by accident.
"""

AUTHORSHIP_DIRECT_TOKENS = frozenset(
    {
        "author",
        "authors",
        "authorship",
        "authenticated",
        "attested",
        "attester",
        "creator",
        "notarised",
        "notarized",
        "notary",
        "publisher",
        "signed",
        "signatory",
        "signer",
        "verified",
        "verifier",
    }
)
AUTHORSHIP_RELATION_TOKENS = frozenset(
    {
        "attestation",
        "authentication",
        "notarisation",
        "notarization",
        "signature",
        "signing",
        "verification",
    }
)
AUTHORSHIP_ASSERTION_TOKENS = frozenset(
    {"actor", "by", "identity", "name", "status", "valid", "validity", "verified"}
)
AUTHORSHIP_LINK_TOKENS = frozenset({"is", "validation"})
KEY_TOKEN = re.compile(
    r"[A-Z]+(?=[A-Z][a-z]|[0-9]|[^A-Za-z0-9]|$)|[A-Z]?[a-z]+|[0-9]+"
)

TOKEN_CONTEXT = 1
TOKEN_CONCLUSION = 2
TOKEN_SUFFIX = 4
TOKEN_AUTHORSHIP_DIRECT = 1
TOKEN_AUTHORSHIP_RELATION = 2
TOKEN_AUTHORSHIP_ASSERTION = 4
TOKEN_AUTHORSHIP_LINK = 8


def compile_vocabulary(*groups):
    """A finite ASCII vocabulary as bounded-memory trie tables."""
    transitions = [{}]
    terminals = [0]
    for flag, words in groups:
        for word in words:
            node = 0
            for character in word:
                child = transitions[node].get(character)
                if child is None:
                    child = len(transitions)
                    transitions[node][character] = child
                    transitions.append({})
                    terminals.append(0)
                node = child
            terminals[node] |= flag
    return tuple(transitions), tuple(terminals)


CONCLUSION_VOCABULARY = compile_vocabulary(
    (TOKEN_CONTEXT, CONCLUSION_CONTEXT_TOKENS),
    (TOKEN_CONCLUSION, CONCLUSION_KEYS),
    (TOKEN_SUFFIX, CONCLUSION_COMPOUND_SUFFIXES),
)
AUTHORSHIP_VOCABULARY = compile_vocabulary(
    (TOKEN_AUTHORSHIP_DIRECT, AUTHORSHIP_DIRECT_TOKENS),
    (TOKEN_AUTHORSHIP_RELATION, AUTHORSHIP_RELATION_TOKENS),
    (TOKEN_AUTHORSHIP_ASSERTION, AUTHORSHIP_ASSERTION_TOKENS),
    (TOKEN_AUTHORSHIP_LINK, AUTHORSHIP_LINK_TOKENS),
)


def conclusion_chain(value):
    """A whole finite-vocabulary conclusion chain with no separators.

    The trie keeps work linear in the key length and memory bounded by the
    vocabulary.  Requiring a complete chain avoids finding ``score`` inside an
    unrelated key such as ``underscorestatus``.
    """
    transitions, terminals = CONCLUSION_VOCABULARY
    # State zero accepts context words; state one accepts state suffixes after
    # exactly one conclusion word. A root-trie entry marks a word boundary.
    active = {(0, 0)}
    for character in value:
        following = set()
        for node, state in active:
            child = transitions[node].get(character)
            if child is None:
                continue
            following.add((child, state))
            flags = terminals[child]
            if state == 0:
                if flags & TOKEN_CONTEXT:
                    following.add((0, 0))
                if flags & TOKEN_CONCLUSION:
                    following.add((0, 1))
            elif flags & TOKEN_SUFFIX:
                following.add((0, 1))
        active = following
        if not active:
            return False
    return (0, 1) in active


def authorship_chain(value):
    """A whole unseparated chain made only from finite authorship words."""
    transitions, terminals = AUTHORSHIP_VOCABULARY
    active = {(0, 0)}
    for character in value:
        following = set()
        for node, claims in active:
            child = transitions[node].get(character)
            if child is None:
                continue
            following.add((child, claims))
            flags = terminals[child]
            if flags:
                following.add((0, claims | flags))
        active = following
        if not active:
            return False
    return any(
        node == 0
        and (
            claims & TOKEN_AUTHORSHIP_DIRECT
            or (
                claims & TOKEN_AUTHORSHIP_RELATION
                and claims & TOKEN_AUTHORSHIP_ASSERTION
            )
        )
        for node, claims in active
    )


def key_tokens(key):
    """ASCII identifier words without confusing a substring for a claim."""
    if (
        not isinstance(key, str)
        or len(key) > core_predicate.MAX_STRUCTURED_KEY_CHARACTERS
    ):
        return ()
    key = unicodedata.normalize("NFKC", key)
    return tuple(found.group(0).lower() for found in KEY_TOKEN.finditer(key))


def tokenised_conclusion(tokens):
    """A conclusion at the semantic end of a separated identifier."""
    if not tokens:
        return False
    index = len(tokens) - 1
    if tokens[index] in CONCLUSION_KEYS:
        return True
    if tokens[index] not in CONCLUSION_COMPOUND_SUFFIXES:
        return False
    while index >= 0 and tokens[index] in CONCLUSION_COMPOUND_SUFFIXES:
        index -= 1
    return index >= 0 and tokens[index] in CONCLUSION_KEYS


def tokenised_authorship(tokens):
    """An ordered separated authorship or verification assertion."""
    relation = False
    for token in tokens:
        if token in AUTHORSHIP_DIRECT_TOKENS:
            return True
        if token in AUTHORSHIP_RELATION_TOKENS:
            relation = True
            continue
        if token in AUTHORSHIP_LINK_TOKENS:
            continue
        if token in AUTHORSHIP_ASSERTION_TOKENS:
            if relation:
                return True
            continue
        relation = False
    return False


def conclusion_key(key):
    """A direct conclusion key or a structured conclusion compound."""
    try:
        normal = core_predicate.normalise_key(key)
    except (TypeError, ValueError):
        return False
    letters = "".join(character for character in normal if not character.isdigit())
    if any(
        candidate in CONCLUSION_KEYS
        or candidate in CONCLUSION_COMPOUND_KEYS
        or conclusion_chain(candidate)
        for candidate in (normal, letters)
    ):
        return True
    return tokenised_conclusion(key_tokens(key))


def authorship_key(key):
    try:
        normal = core_predicate.normalise_key(key)
    except (TypeError, ValueError):
        return False
    letters = "".join(character for character in normal if not character.isdigit())
    if any(
        candidate in AUTHORSHIP_KEYS
        or candidate in AUTHORSHIP_COMPOUND_KEYS
        or authorship_chain(candidate)
        for candidate in (normal, letters)
    ):
        return True
    return tokenised_authorship(key_tokens(key))


def scanned(statement):
    """Every key inside a statement that a producer chooses the content of.

    The predicate, and also each subject's digest algorithms, annotations and
    other descriptor fields. A verdict smuggled into a subject digest or
    `subject[0].annotations` is the same smuggling as one in the predicate, and
    scanning only the predicate would have left the shorter route open.
    """
    for pair in core_predicate.walk(statement.predicate):
        yield pair
    for subject in statement.subjects:
        for pair in core_predicate.walk(subject.digest):
            yield pair
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
        return "%s %s: %s -- %s" % (
            label,
            one_line(self.name),
            mark,
            one_line(self.detail),
        )

    def to_dict(self):
        return {
            "gate": self.number,
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }


def one_line(value):
    """Render an untrusted diagnostic value without terminal line injection."""
    out = []
    for character in str(value):
        if character.isprintable():
            out.append(character)
        else:
            out.append(character.encode("unicode_escape").decode("ascii"))
    return "".join(out)


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
    faults = []
    found = core_predicate.claims(statement.predicate)
    claim_limit = _limit(limits, "claims")
    subject_limit = _limit(limits, "subjects")
    digest_algorithm_limit = _limit(limits, "digest_algorithms")
    if found is not None and claim_limit is not None and len(found) > claim_limit:
        faults.append(
            "claims has %d entries; this predicate reads at most %d"
            % (len(found), claim_limit)
        )
    checked_claims = (
        found[:claim_limit]
        if found is not None and claim_limit is not None
        else (found or [])
    )
    checked_subjects = (
        statement.subjects[:subject_limit]
        if subject_limit is not None
        else statement.subjects
    )
    comparable_subjects = []
    oversized_subjects = []
    for index, entry in enumerate(checked_subjects):
        if (
            digest_algorithm_limit is not None
            and len(entry.digest) > digest_algorithm_limit
        ):
            oversized_subjects.append((index, len(entry.digest)))
        else:
            comparable_subjects.append(entry)
    if oversized_subjects:
        first_index, first_count = oversized_subjects[0]
        faults.append(
            "%d statement subject digest set(s) exceed the %d-algorithm "
            "limit; subject %d has %d"
            % (
                len(oversized_subjects),
                digest_algorithm_limit,
                first_index + 1,
                first_count,
            )
        )
    if found is None:
        # Whether the block has to be there is gate 3's question. Failing here
        # as well would report one fault twice and tell a reader that two
        # separate things went wrong. Predicate-owned subject bounds still
        # apply because the subjects exist independently of the claims block.
        if faults:
            return Gate(1, "subject-naming", False, "; ".join(faults))
        return Gate(1, "subject-naming", True, "no claims block; gate 3 covers that")
    if not found:
        if faults:
            return Gate(1, "subject-naming", False, "; ".join(faults))
        return Gate(1, "subject-naming", True, "no claims recorded")

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
        if (
            digest_algorithm_limit is not None
            and len(subject) > digest_algorithm_limit
        ):
            faults.append(
                "%s digest set has %d algorithms; this predicate reads at most %d"
                % (name, len(subject), digest_algorithm_limit)
            )
            continue
        if not any(
            digests.agree(entry.digest, subject) for entry in comparable_subjects
        ):
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
    budget = core_predicate.StructuredKeyBudget()
    for key, _ in scanned(statement):
        if not budget.accept(key):
            continue
        elif conclusion_key(key):
            faults.append(key)
    if faults or budget.refused:
        details = []
        if budget.refused:
            details.append(
                "statement carries %d structured key(s) outside the %d-character "
                "scan limit or %d-character aggregate scan budget"
                % (
                    budget.refused,
                    core_predicate.MAX_STRUCTURED_KEY_CHARACTERS,
                    core_predicate.MAX_STRUCTURED_KEY_CHARACTERS_TOTAL,
                )
            )
        if faults:
            details.append(
                "statement carries verdict key(s): %s"
                % ", ".join(sorted(set(faults)))
            )
        return Gate(
            4,
            "no-conclusions",
            False,
            "; ".join(details),
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
    budget = core_predicate.StructuredKeyBudget()
    for key, _ in scanned(statement):
        if not budget.accept(key):
            continue
        elif authorship_key(key):
            faults.append(key)
    if faults or budget.refused:
        details = []
        if budget.refused:
            details.append(
                "statement carries %d structured key(s) outside the %d-character "
                "scan limit or %d-character aggregate scan budget"
                % (
                    budget.refused,
                    core_predicate.MAX_STRUCTURED_KEY_CHARACTERS,
                    core_predicate.MAX_STRUCTURED_KEY_CHARACTERS_TOTAL,
                )
            )
        if faults:
            details.append(
                "statement asserts its own authorship or verification: %s"
                % ", ".join(sorted(set(faults)))
            )
        return Gate(
            7,
            "authorship",
            False,
            "; ".join(details),
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
