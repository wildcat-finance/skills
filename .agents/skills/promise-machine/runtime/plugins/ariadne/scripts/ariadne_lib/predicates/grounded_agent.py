"""A grounded-agent release, split into inputs, outputs and their byte subjects.

This predicate binds a ``berean-release/v1`` document without importing Berean
or copying its evaluation conclusions into Ariadne.  The semantic release digest
is recomputed from the projected release identity.  Every file digest names exact
bytes and must occur in the surrounding in-toto subject set.
"""

import hashlib
import json
import ntpath
import posixpath
import re
import unicodedata

from .. import core_predicate, digests
from ..gates import Gate

TYPE = "https://ariadne.wildcat.finance/grounded-agent/v1"
SUMMARY = "a grounded-agent release: pinned inputs, produced answers and policy"
EXPECTED_RESULTS = (
    (2, "environment"),
    (5, "comparison"),
    (None, "predicate-fields"),
    (None, "components"),
    (None, "release-digest"),
    (None, "optional-evidence"),
    (None, "evidence-boundary"),
    (None, "subject-names"),
)

# Public Berean wire constants are copied deliberately.  Ariadne has no runtime
# dependency on a sibling plugin; a checkout-only drift test compares these with
# Berean when that plugin is present.
BEREAN_FORMAT = "berean-release/v1"
BEREAN_RELEASE_FIELDS = (
    "format",
    "release_version",
    "corpus",
    "reads",
    "answers",
    "question_families",
    "refusal_conditions",
    "rules",
    "allowlists",
    "evals",
    "retention",
    "release_digest",
)
BEREAN_IDENTITY_FIELDS = tuple(
    field for field in BEREAN_RELEASE_FIELDS if field != "release_digest"
)
BEREAN_CORPUS_FIELDS = (
    "path",
    "manifest",
    "manifest_sha256",
    "corpus_version",
    "corpus_digest",
)
BEREAN_READS_FIELDS = (
    "path",
    "sha256",
    "chain_id",
    "block_number",
    "block_hash",
    "source",
)
BEREAN_ANSWER_FIELDS = ("path", "sha256")
BEREAN_RULES_FIELDS = ("source_classes", "evidence_classes")
BEREAN_ALLOWLIST_FIELDS = ("chains", "contracts")
BEREAN_EVALS_FIELDS = ("cases", "cases_sha256", "report", "report_sha256")
BEREAN_RETENTION = ("none", "answers-only")
BEREAN_SOURCE_CLASSES = (
    "document",
    "chain_read",
    "calculation",
    "user_supplied",
)
BEREAN_EVIDENCE_CLASSES = ("proof-backed", "header-bound", "recorded-rpc")
BEREAN_RELEASE_DOCUMENT = "release.json"
BEREAN_PROMOTIONS_FILE = "promotions.jsonl"
BEREAN_PROMOTION_FORMAT = "berean-promotion/v1"
BEREAN_PROMOTION_ACTIONS = ("promote", "rollback")
BEREAN_MAX_PROMOTION_RECORDS = 1000
BEREAN_EVALUATION_RESULT_FIELDS = (
    "thresholds",
    "cases",
    "passed",
    "failed",
)
BEREAN_EVALUATION_REPORT_ONLY_FIELDS = ("failures",)
BEREAN_THRESHOLD_FIELDS = ("failures_allowed",)
FORBIDDEN_BEREAN_RESULT_KEYS = frozenset(
    BEREAN_EVALUATION_RESULT_FIELDS
    + BEREAN_EVALUATION_REPORT_ONLY_FIELDS
    + BEREAN_THRESHOLD_FIELDS
)
FORBIDDEN_BEREAN_RESULT_KEYS_BY_NORMAL = {
    core_predicate.compatibility_key(key): key for key in FORBIDDEN_BEREAN_RESULT_KEYS
}

COMPONENT_FIELDS = ("name", "path", "sha256", "bytes")
RELEASE_FIELDS = ("format", "release_version", "release_digest", "document")
GIVEN_FIELDS = ("corpus", "reads", "reads_absence_reason")
CORPUS_FIELDS = (
    "path",
    "corpus_version",
    "corpus_digest",
    "manifest",
    "components",
)
READS_FIELDS = ("component", "chain_id", "block_number", "block_hash", "source")
PRODUCED_FIELDS = (
    "answers",
    "evaluations",
    "evaluations_absence_reason",
    "promotion",
    "promotion_absence_reason",
)
EVALUATIONS_FIELDS = ("cases", "report")
PROMOTION_FIELDS = ("component", "format", "terminal")
PROMOTION_TERMINAL_FIELDS = ("sequence", "action", "target_release_digest")
POLICY_FIELDS = (
    "question_families",
    "refusal_conditions",
    "rules",
    "allowlists",
    "retention",
)
RULES_FIELDS = ("source_classes", "evidence_classes")
ALLOWLIST_FIELDS = ("chains", "contracts")
ADAPTER_FIELDS = ("tool", "tool_version", "command", "parameters_digest")
COMPARISON_FIELDS = ("baseline", "current", "first_capture_reason")
COMPARISON_SIDE_FIELDS = ("name", "release_digest")

PREDICATE_FIELDS = (
    "release",
    "given",
    "produced",
    "policy",
    "adapter",
    "comparison",
    "claims",
    "commands",
)
REQUIRED_FIELDS = PREDICATE_FIELDS

MAX_COMPONENTS = 1024
# Two bounded collections plus the release document, corpus manifest, optional
# reads, two evaluation files and a promotion chain.  The outer subject ceiling
# must cover every body the schema admits rather than silently lowering one of
# the two published collection limits.
MAX_SUBJECTS = 2 * MAX_COMPONENTS + 6
MAX_COMPONENT_BYTES = 536870912
MAX_PATH = 1024
MAX_NAME = 256
MAX_TEXT = 4096
MAX_POLICY_ITEMS = 256
MAX_COMMAND_WORDS = 128
MAX_CLAIMS = 1024
MAX_COMMANDS = 1024
# Digest maps stay extensible without letting each claim-by-subject comparison
# multiply an input-sized algorithm list.  Three slots cover every algorithm
# Ariadne currently proves; five remain for transition metadata.
MAX_DIGEST_ALGORITHMS = 8

CLAIM_REQUIRED_FIELDS = ("name", "subject", "disposition")
COMMAND_REQUIRED_FIELDS = ("name", "argv", "determinism")
CORE_LIMITS = {
    "subjects": MAX_SUBJECTS,
    "claims": MAX_CLAIMS,
    "commands": MAX_COMMANDS,
    "command_words": MAX_COMMAND_WORDS,
    "digest_algorithms": MAX_DIGEST_ALGORITHMS,
}

SHA256 = re.compile(r"^[0-9a-f]{64}$")
HASH32 = re.compile(r"^0x[0-9a-f]{64}$")
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]")
SURROGATE = re.compile(r"[\ud800-\udfff]")
PREDICATE_WHITESPACE = frozenset(
    "\t\n\v\f\r\x1c\x1d\x1e\x1f \x85\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
    "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000\ufeff"
)
ZERO_HASH = "0x" + "0" * 64


def whole_number(value):
    """True for an integer count or boundary; booleans are not integers here."""
    return isinstance(value, int) and not isinstance(value, bool)


def stated(value, limit=MAX_TEXT):
    return (
        isinstance(value, str)
        and 0 < len(value) <= limit
        and any(char not in PREDICATE_WHITESPACE for char in value)
    )


def portable_name(value):
    """A bounded label with an ASCII graphic and no control or line separator."""
    if (
        not stated(value, MAX_NAME)
        or value != value.strip()
        # JSON Schema patterns use ECMA-262, whose whitespace set includes the
        # byte-order mark. Python's strip does not, so name and path edges must
        # refuse it explicitly to keep the two public validators aligned.
        or value.startswith("\ufeff")
        or value.endswith("\ufeff")
    ):
        return False
    if not any("!" <= char <= "~" for char in value):
        return False
    return CONTROL.search(value) is None and SURROGATE.search(value) is None


def usable_path(value):
    """A bounded portable relative path with one visible graphic per segment."""
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_PATH
        or "\\" in value
        or "\x00" in value
        or value.startswith("/")
        or ntpath.isabs(value)
        or posixpath.isabs(value)
    ):
        return False
    drive, _ = ntpath.splitdrive(value)
    if drive:
        return False
    parts = value.split("/")
    return all(part not in ("", ".", "..") and portable_name(part) for part in parts)


def sha256(value):
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def hash32(value):
    return (
        isinstance(value, str)
        and bool(HASH32.fullmatch(value))
        and value != ZERO_HASH
    )


def _shape(value, label, fields, faults):
    """Append closed-object shape faults and return whether fields can be read."""
    if not isinstance(value, dict):
        faults.append("%s must be an object" % label)
        return False
    missing = [field for field in fields if field not in value]
    if missing:
        faults.append("%s is missing %s" % (label, ", ".join(missing)))
    unknown = sorted(set(value) - set(fields))
    if unknown:
        faults.append(
            "%s carries fields this type does not define: %s"
            % (label, ", ".join(unknown))
        )
    return not missing


def _record_shape(value, label, required, allowed, faults):
    """Append faults for a closed record with optional allowed fields."""
    if not isinstance(value, dict):
        faults.append("%s must be an object" % label)
        return False
    missing = [field for field in required if field not in value]
    if missing:
        faults.append("%s is missing %s" % (label, ", ".join(missing)))
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        faults.append(
            "%s carries fields this type does not define: %s"
            % (label, ", ".join(unknown))
        )
    return not missing


def _bounded_list(value, label, maximum, faults, nonempty=False):
    if not isinstance(value, list):
        faults.append("%s must be an array" % label)
        return False
    if nonempty and not value:
        faults.append("%s must be a non-empty array" % label)
    if len(value) > maximum:
        faults.append("%s has %d entries; this type reads at most %d" % (label, len(value), maximum))
    return bool(value) if nonempty else True


def _component_shapes(value, label, faults):
    _shape(value, label, COMPONENT_FIELDS, faults)


def field_faults(predicate):
    """All closed shapes, including explicit nullable evidence blocks."""
    faults = []
    if not _shape(predicate, "predicate", REQUIRED_FIELDS, faults):
        return faults

    release = predicate.get("release")
    if _shape(release, "release", RELEASE_FIELDS, faults):
        _component_shapes(release.get("document"), "release document", faults)

    given = predicate.get("given")
    if _shape(given, "given", GIVEN_FIELDS, faults):
        corpus = given.get("corpus")
        if _shape(corpus, "given corpus", CORPUS_FIELDS, faults):
            _component_shapes(corpus.get("manifest"), "corpus manifest", faults)
            components = corpus.get("components")
            if _bounded_list(
                components, "corpus components", MAX_COMPONENTS, faults, nonempty=True
            ):
                for index, component in enumerate(components[:MAX_COMPONENTS]):
                    _component_shapes(component, "corpus component %d" % (index + 1), faults)
        reads = given.get("reads")
        if reads is not None and _shape(reads, "given reads", READS_FIELDS, faults):
            _component_shapes(reads.get("component"), "reads component", faults)

    produced = predicate.get("produced")
    if _shape(produced, "produced", PRODUCED_FIELDS, faults):
        answers = produced.get("answers")
        if _bounded_list(answers, "produced answers", MAX_COMPONENTS, faults, nonempty=True):
            for index, component in enumerate(answers[:MAX_COMPONENTS]):
                _component_shapes(component, "answer component %d" % (index + 1), faults)
        evaluations = produced.get("evaluations")
        if evaluations is not None and _shape(
            evaluations, "produced evaluations", EVALUATIONS_FIELDS, faults
        ):
            _component_shapes(evaluations.get("cases"), "evaluation cases", faults)
            _component_shapes(evaluations.get("report"), "evaluation report", faults)
        promotion = produced.get("promotion")
        if promotion is not None and _shape(
            promotion, "produced promotion", PROMOTION_FIELDS, faults
        ):
            _component_shapes(promotion.get("component"), "promotion chain", faults)
            _shape(
                promotion.get("terminal"),
                "promotion terminal",
                PROMOTION_TERMINAL_FIELDS,
                faults,
            )

    policy = predicate.get("policy")
    if _shape(policy, "policy", POLICY_FIELDS, faults):
        _shape(policy.get("rules"), "policy rules", RULES_FIELDS, faults)
        _shape(policy.get("allowlists"), "policy allowlists", ALLOWLIST_FIELDS, faults)
    _shape(predicate.get("adapter"), "adapter", ADAPTER_FIELDS, faults)

    comparison = predicate.get("comparison")
    if _shape(comparison, "comparison", COMPARISON_FIELDS, faults):
        _shape(comparison.get("current"), "comparison current", COMPARISON_SIDE_FIELDS, faults)
        if comparison.get("baseline") is not None:
            _shape(
                comparison.get("baseline"),
                "comparison baseline",
                COMPARISON_SIDE_FIELDS,
                faults,
            )

    claims = predicate.get("claims")
    if _bounded_list(claims, "claims", MAX_CLAIMS, faults):
        for index, claim in enumerate(claims[:MAX_CLAIMS]):
            _record_shape(
                claim,
                "claim %d" % (index + 1),
                CLAIM_REQUIRED_FIELDS,
                core_predicate.CLAIM_FIELDS,
                faults,
            )
    commands = predicate.get("commands")
    if _bounded_list(commands, "commands", MAX_COMMANDS, faults):
        for index, command in enumerate(commands[:MAX_COMMANDS]):
            _record_shape(
                command,
                "command %d" % (index + 1),
                COMMAND_REQUIRED_FIELDS,
                core_predicate.COMMAND_FIELDS,
                faults,
            )
    return faults


def components(predicate):
    """Yield the bounded component slots the predicate makes subjects."""
    if not isinstance(predicate, dict):
        return
    release = predicate.get("release")
    if isinstance(release, dict):
        yield "release document", release.get("document")
    given = predicate.get("given")
    if isinstance(given, dict):
        corpus = given.get("corpus")
        if isinstance(corpus, dict):
            yield "corpus manifest", corpus.get("manifest")
            entries = corpus.get("components")
            if isinstance(entries, list):
                for index, entry in enumerate(entries[:MAX_COMPONENTS]):
                    yield "corpus component %d" % (index + 1), entry
        reads = given.get("reads")
        if isinstance(reads, dict):
            yield "reads component", reads.get("component")
    produced = predicate.get("produced")
    if isinstance(produced, dict):
        answers = produced.get("answers")
        if isinstance(answers, list):
            for index, entry in enumerate(answers[:MAX_COMPONENTS]):
                yield "answer component %d" % (index + 1), entry
        evaluations = produced.get("evaluations")
        if isinstance(evaluations, dict):
            yield "evaluation cases", evaluations.get("cases")
            yield "evaluation report", evaluations.get("report")
        promotion = produced.get("promotion")
        if isinstance(promotion, dict):
            yield "promotion chain", promotion.get("component")


def component_faults(statement):
    """Validate component bytes, uniqueness and two-way subject coverage."""
    found = list(components(statement.predicate) or [])
    faults = []
    if len(statement.subjects) > MAX_SUBJECTS:
        faults.append(
            "statement names %d subjects; this type reads at most %d"
            % (len(statement.subjects), MAX_SUBJECTS)
        )

    # `Statement.covers` scans the complete subject list.  Once the public
    # ceiling is exceeded, calling it once per component would let a refused
    # statement turn a count bound into component-by-subject work.  Build the
    # only relation this predicate accepts from the bounded prefix instead.
    bounded_subjects = statement.subjects[:MAX_SUBJECTS]
    subject_sha256 = {
        subject.digest.get("sha256")
        for subject in bounded_subjects
        if isinstance(subject.digest, dict)
    }

    # sha256 is the component identity in this predicate. Subject aliases may
    # add algorithms, but they cannot attach two values to one identity or let
    # one supported digest stand for two sha256 identities. Without this join,
    # a later claim could select a different alias for the same component.
    aliases_by_sha256 = {}
    supported_digest_owners = {}
    for index, subject in enumerate(bounded_subjects):
        identity = subject.digest.get("sha256")
        if not sha256(identity):
            continue
        aliases = aliases_by_sha256.setdefault(identity, {})
        contradicts_identity = False
        conflicts_with_identity = False
        for position, (algorithm, value) in enumerate(subject.digest.items()):
            if position >= MAX_DIGEST_ALGORITHMS:
                break
            if algorithm in aliases and aliases[algorithm] != value:
                contradicts_identity = True
            else:
                aliases[algorithm] = value
            if algorithm in digests.ALGORITHMS:
                key = (algorithm, value)
                owner = supported_digest_owners.get(key)
                if owner is not None and owner != identity:
                    conflicts_with_identity = True
                else:
                    supported_digest_owners[key] = identity
        if contradicts_identity:
            faults.append(
                "statement subject %d contradicts another digest alias for its sha256 identity"
                % (index + 1)
            )
        if conflicts_with_identity:
            faults.append(
                "statement subject %d maps a supported digest to conflicting sha256 identities"
                % (index + 1)
            )

    # A claim can carry more than one algorithm. Gate 1 accepts it when one
    # statement subject agrees on every shared algorithm, which deliberately
    # permits transition metadata that the matching subject does not yet carry.
    # It must not, however, bridge two identities already established by this
    # statement: that would make one claim about two different byte subjects.
    claims = core_predicate.claims(statement.predicate) or []
    for index, claim in enumerate(claims[:MAX_CLAIMS]):
        claim_digest = claim.get("subject") if isinstance(claim, dict) else None
        if not isinstance(claim_digest, dict):
            continue
        owners = set()
        for position, (algorithm, value) in enumerate(claim_digest.items()):
            if position >= MAX_DIGEST_ALGORITHMS:
                break
            owner = supported_digest_owners.get((algorithm, value))
            if owner is not None:
                owners.add(owner)
        if len(owners) > 1:
            faults.append(
                "claim %d maps supported digests to conflicting sha256 identities"
                % (index + 1)
            )
        elif len(owners) == 1:
            owner = next(iter(owners))
            aliases = aliases_by_sha256.get(owner, {})
            contradicts_alias = False
            for position, (algorithm, value) in enumerate(claim_digest.items()):
                if position >= MAX_DIGEST_ALGORITHMS:
                    break
                if algorithm in aliases and aliases[algorithm] != value:
                    contradicts_alias = True
                    break
            if contradicts_alias:
                faults.append(
                    "claim %d contradicts a known digest alias for its sha256 identity"
                    % (index + 1)
                )

    names = {}
    paths = {}
    valid_digests = set()
    digest_bytes = {}
    total_bytes = 0
    for label, entry in found:
        if not isinstance(entry, dict):
            faults.append("%s must be an object" % label)
            continue
        if any(field not in entry for field in COMPONENT_FIELDS):
            continue
        name = entry.get("name")
        path = entry.get("path")
        digest = entry.get("sha256")
        byte_count = entry.get("bytes")
        if not portable_name(name):
            faults.append("%s name is not a portable bounded label" % label)
        else:
            settled = unicodedata.normalize("NFC", name)
            if settled in names:
                faults.append(
                    "%s name collides after Unicode normalisation with %s"
                    % (label, names[settled])
                )
            names[settled] = label
        if not usable_path(path):
            faults.append("%s path is not a portable release-relative path" % label)
        else:
            settled_path = unicodedata.normalize("NFC", path)
            if settled_path in paths:
                faults.append("%s repeats component path %s" % (label, path))
            paths[settled_path] = label
        if not sha256(digest):
            faults.append("%s sha256 is not 64 lowercase hex characters" % label)
        else:
            valid_digests.add(digest)
            if digest not in subject_sha256:
                faults.append("%s is not a subject of this statement" % label)
        if not whole_number(byte_count) or not 0 <= byte_count <= MAX_COMPONENT_BYTES:
            faults.append(
                "%s bytes must be a whole number from 0 to %d, not %r"
                % (label, MAX_COMPONENT_BYTES, byte_count)
            )
        else:
            total_bytes += byte_count
            if sha256(digest):
                if digest in digest_bytes and digest_bytes[digest] != byte_count:
                    faults.append(
                        "%s bytes disagree with another component carrying the same sha256"
                        % label
                    )
                else:
                    digest_bytes[digest] = byte_count

    for index, subject in enumerate(bounded_subjects):
        if subject.digest.get("sha256") not in valid_digests:
            faults.append(
                "statement subject %d does not name a declared component"
                % (index + 1)
            )
    return faults, len(found), total_bytes


def _policy_faults(predicate):
    faults = []
    policy = predicate.get("policy") if isinstance(predicate, dict) else None
    if not isinstance(policy, dict):
        return ["policy must be an object"]
    for field in ("question_families", "refusal_conditions"):
        values = policy.get(field)
        if not _bounded_list(values, "policy %s" % field, MAX_POLICY_ITEMS, faults, nonempty=True):
            continue
        seen = set()
        for index, value in enumerate(values[:MAX_POLICY_ITEMS]):
            if not stated(value):
                faults.append("policy %s[%d] must state a bounded string" % (field, index))
                continue
            settled = unicodedata.normalize("NFC", value)
            if settled in seen:
                faults.append("policy %s repeats an entry after Unicode normalisation" % field)
            seen.add(settled)
    rules = policy.get("rules")
    if isinstance(rules, dict):
        source_classes = rules.get("source_classes")
        if (
            not isinstance(source_classes, list)
            or tuple(source_classes) != BEREAN_SOURCE_CLASSES
        ):
            faults.append("policy source_classes would change the Berean evidence vocabulary")
        evidence_classes = rules.get("evidence_classes")
        if (
            not isinstance(evidence_classes, list)
            or tuple(evidence_classes) != BEREAN_EVIDENCE_CLASSES
        ):
            faults.append("policy evidence_classes would upgrade or change recorded evidence")
    allowlists = policy.get("allowlists")
    if isinstance(allowlists, dict):
        chains = allowlists.get("chains")
        if not _bounded_list(chains, "policy allowlists.chains", MAX_POLICY_ITEMS, faults):
            chains = []
        for chain in chains[:MAX_POLICY_ITEMS]:
            if not whole_number(chain) or chain < 0:
                faults.append("policy allowlisted chain must be a non-negative whole number")
        contracts = allowlists.get("contracts")
        if not _bounded_list(contracts, "policy allowlists.contracts", MAX_POLICY_ITEMS, faults):
            contracts = []
        for contract in contracts[:MAX_POLICY_ITEMS]:
            if not isinstance(contract, str) or not ADDRESS.fullmatch(contract):
                faults.append("policy allowlisted contract is not a lowercase address")
    if policy.get("retention") not in BEREAN_RETENTION:
        faults.append("policy retention is outside %s" % ", ".join(BEREAN_RETENTION))
    return faults


def _berean_result_keys(value, budget):
    """The closed Berean result vocabulary projected through an open object.

    Compatibility normalisation and case folding map identifier spellings that
    they make equivalent to the same finite wire key. Oversized keys are
    refused by core gates 4 and 7 before either classifier normalises them.
    """
    found = set()
    pending = [value]
    while pending:
        current = pending.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                normal = (
                    core_predicate.compatibility_key(key)
                    if budget.accept(key)
                    else None
                )
                if normal in FORBIDDEN_BEREAN_RESULT_KEYS_BY_NORMAL:
                    found.add(FORBIDDEN_BEREAN_RESULT_KEYS_BY_NORMAL[normal])
                pending.append(child)
        elif isinstance(current, list):
            pending.extend(current)
    return found


def _result_projection_faults(statement):
    """Refuse Berean thresholds and result counts on open extension surfaces."""
    surfaces = []
    predicate = statement.predicate
    if isinstance(predicate, dict):
        adapter = predicate.get("adapter")
        if isinstance(adapter, dict):
            surfaces.append(adapter.get("parameters_digest"))
        for field, limit in (("claims", MAX_CLAIMS), ("commands", MAX_COMMANDS)):
            entries = predicate.get(field)
            if not isinstance(entries, list):
                continue
            for entry in entries[:limit]:
                if not isinstance(entry, dict):
                    continue
                surfaces.append(entry.get("detail"))
                surfaces.append(
                    entry.get("subject")
                    if field == "claims"
                    else entry.get("output_digest")
                )
    for subject in statement.subjects[:MAX_SUBJECTS]:
        surfaces.append(subject.digest)
        surfaces.append(subject.extra)

    found = set()
    budget = core_predicate.StructuredKeyBudget()
    for surface in surfaces:
        found.update(_berean_result_keys(surface, budget))
    faults = []
    if budget.refused:
        faults.append(
            "statement carries %d evidence key(s) outside the %d-character "
            "scan limit or %d-character aggregate scan budget"
            % (
                budget.refused,
                core_predicate.MAX_STRUCTURED_KEY_CHARACTERS,
                core_predicate.MAX_STRUCTURED_KEY_CHARACTERS_TOTAL,
            )
        )
    if found:
        faults.append(
            "statement projects Berean evaluation threshold or result key(s): %s"
            % ", ".join(sorted(found))
        )
    if not faults:
        return []
    return faults


def _adapter_faults(predicate):
    adapter = predicate.get("adapter") if isinstance(predicate, dict) else None
    if not isinstance(adapter, dict):
        return ["adapter must be an object"]
    faults = []
    for field in ("tool", "tool_version"):
        if not portable_name(adapter.get(field)):
            faults.append("adapter %s must be a portable bounded name" % field)
    command = adapter.get("command")
    if not isinstance(command, list) or not command or len(command) > MAX_COMMAND_WORDS:
        faults.append("adapter command must be 1 to %d argv strings" % MAX_COMMAND_WORDS)
    elif not all(stated(word) for word in command):
        faults.append("adapter command entries must be non-blank bounded strings")
    _bounded_digest(
        adapter.get("parameters_digest"), "adapter parameters_digest", faults
    )
    return faults


def _bounded_digest(value, label, faults):
    """Validate one digest map and retain the predicate's work ceiling."""
    try:
        digests.check(value)
    except digests.DigestError as error:
        faults.append("%s: %s" % (label, error))
        return False
    if len(value) > MAX_DIGEST_ALGORITHMS:
        faults.append(
            "%s has %d algorithms; at most %d are accepted"
            % (label, len(value), MAX_DIGEST_ALGORITHMS)
        )
        return False
    return True


def _core_block_faults(predicate):
    """Hold this predicate's core blocks to its published bounded schema."""
    if not isinstance(predicate, dict):
        return ["predicate must be an object"]
    faults = []
    claims = predicate.get("claims")
    if isinstance(claims, list):
        for index, claim in enumerate(claims[:MAX_CLAIMS]):
            label = "claim %d" % (index + 1)
            if not isinstance(claim, dict):
                continue
            if not portable_name(claim.get("name")):
                faults.append("%s name is not a portable bounded label" % label)
            _bounded_digest(claim.get("subject"), "%s subject" % label, faults)
            disposition = claim.get("disposition")
            if disposition not in core_predicate.DISPOSITIONS:
                faults.append("%s disposition is outside the core vocabulary" % label)
            reason = claim.get("reason")
            if "reason" in claim and (
                not isinstance(reason, str) or len(reason) > MAX_TEXT
            ):
                faults.append("%s reason must be a bounded string when present" % label)
            if disposition in core_predicate.NEEDS_REASON and not stated(reason):
                faults.append("%s disposition needs a stated bounded reason" % label)
            detail = claim.get("detail")
            if "detail" in claim and not isinstance(detail, dict):
                faults.append("%s detail must be an object when present" % label)

    commands = predicate.get("commands")
    if isinstance(commands, list):
        for index, command in enumerate(commands[:MAX_COMMANDS]):
            label = "command %d" % (index + 1)
            if not isinstance(command, dict):
                continue
            if not portable_name(command.get("name")):
                faults.append("%s name is not a portable bounded label" % label)
            argv = command.get("argv")
            if (
                not isinstance(argv, list)
                or not argv
                or len(argv) > MAX_COMMAND_WORDS
            ):
                faults.append(
                    "%s argv must carry 1 to %d entries"
                    % (label, MAX_COMMAND_WORDS)
                )
            elif not all(stated(word) for word in argv):
                faults.append("%s argv entries must be bounded stated strings" % label)
            determinism = command.get("determinism")
            if determinism not in core_predicate.DETERMINISM:
                faults.append("%s determinism is outside the core vocabulary" % label)
            output = command.get("output_digest")
            if "output_digest" in command:
                _bounded_digest(output, "%s output_digest" % label, faults)
            elif determinism == "exact":
                faults.append("%s exact command needs an output_digest" % label)
            detail = command.get("detail")
            if "detail" in command and not isinstance(detail, dict):
                faults.append("%s detail must be an object when present" % label)
    return faults


def _release_value_faults(predicate):
    faults = []
    release = predicate.get("release") if isinstance(predicate, dict) else None
    if not isinstance(release, dict):
        return ["release must be an object"]
    if release.get("format") != BEREAN_FORMAT:
        faults.append("release format is not %s" % BEREAN_FORMAT)
    if not portable_name(release.get("release_version")):
        faults.append("release release_version must be a portable bounded name")
    if not sha256(release.get("release_digest")):
        faults.append("release release_digest is not 64 lowercase hex characters")
    document = release.get("document")
    if isinstance(document, dict) and document.get("path") != BEREAN_RELEASE_DOCUMENT:
        faults.append("release document path must be %s" % BEREAN_RELEASE_DOCUMENT)
    return faults


def _given_faults(predicate):
    faults = []
    given = predicate.get("given") if isinstance(predicate, dict) else None
    if not isinstance(given, dict):
        return ["given must be an object"]
    corpus = given.get("corpus")
    if isinstance(corpus, dict):
        if not usable_path(corpus.get("path")):
            faults.append("given corpus path is not portable and release-relative")
        if not portable_name(corpus.get("corpus_version")):
            faults.append("given corpus_version must be a portable bounded name")
        if not sha256(corpus.get("corpus_digest")):
            faults.append("given corpus_digest is not 64 lowercase hex characters")
        prefix = "%s/" % corpus.get("path") if usable_path(corpus.get("path")) else None
        entries = corpus.get("components")
        if prefix and isinstance(entries, list):
            for index, entry in enumerate(entries[:MAX_COMPONENTS]):
                if isinstance(entry, dict) and usable_path(entry.get("path")):
                    if not entry["path"].startswith(prefix):
                        faults.append("corpus component %d is outside the corpus path" % (index + 1))
    reads = given.get("reads")
    if reads is not None and isinstance(reads, dict):
        for field in ("chain_id", "block_number"):
            value = reads.get(field)
            if not whole_number(value) or value < 0:
                faults.append("given reads %s must be a non-negative whole number" % field)
        if not hash32(reads.get("block_hash")):
            faults.append("given reads block_hash must be a non-zero lowercase 32-byte hash")
        if not stated(reads.get("source")):
            faults.append("given reads source must state its provenance")
    return faults


def optional_faults(predicate):
    """Validate explicit absence and the non-conclusion promotion projection."""
    faults = []
    if not isinstance(predicate, dict):
        return ["predicate must be an object"]
    given = predicate.get("given")
    if isinstance(given, dict):
        reads = given.get("reads")
        reads_reason = given.get("reads_absence_reason")
        if reads is not None and not isinstance(reads, dict):
            faults.append("given reads must be an object or null")
        elif reads is None:
            if not stated(reads_reason):
                faults.append("null given reads need a stated reads_absence_reason")
        elif reads_reason is not None:
            faults.append("reads_absence_reason must be null when reads are present")
    produced = predicate.get("produced")
    if not isinstance(produced, dict):
        return ["produced must be an object"]
    evaluations = produced.get("evaluations")
    evaluations_reason = produced.get("evaluations_absence_reason")
    if evaluations is not None and not isinstance(evaluations, dict):
        faults.append("produced evaluations must be an object or null")
    elif evaluations is None:
        if not stated(evaluations_reason):
            faults.append(
                "null produced evaluations need a stated evaluations_absence_reason"
            )
    elif evaluations_reason is not None:
        faults.append(
            "evaluations_absence_reason must be null when evaluations are present"
        )
    promotion = produced.get("promotion")
    promotion_reason = produced.get("promotion_absence_reason")
    if promotion is not None:
        if not isinstance(promotion, dict):
            faults.append("produced promotion must be an object or null")
        else:
            if promotion.get("format") != BEREAN_PROMOTION_FORMAT:
                faults.append("promotion format is not %s" % BEREAN_PROMOTION_FORMAT)
            component = promotion.get("component")
            if isinstance(component, dict) and component.get("path") != BEREAN_PROMOTIONS_FILE:
                faults.append("promotion component path must be %s" % BEREAN_PROMOTIONS_FILE)
            terminal = promotion.get("terminal")
            if isinstance(terminal, dict):
                sequence = terminal.get("sequence")
                action = terminal.get("action")
                if (
                    not whole_number(sequence)
                    or not 1 <= sequence <= BEREAN_MAX_PROMOTION_RECORDS
                ):
                    faults.append(
                        "promotion terminal sequence must be a whole number from 1 to %d"
                        % BEREAN_MAX_PROMOTION_RECORDS
                    )
                if action not in BEREAN_PROMOTION_ACTIONS:
                    faults.append("promotion terminal action is outside promote and rollback")
                if not sha256(terminal.get("target_release_digest")):
                    faults.append("promotion terminal target_release_digest is malformed")
                release = predicate.get("release")
                if (
                    action in BEREAN_PROMOTION_ACTIONS
                    and evaluations is None
                ):
                    faults.append("a promotion terminal requires evaluations")
                if (
                    action == "promote"
                    and isinstance(release, dict)
                    and terminal.get("target_release_digest") != release.get("release_digest")
                ):
                    faults.append("a promote terminal must target this release digest")
                if (
                    action == "rollback"
                    and isinstance(release, dict)
                    and terminal.get("target_release_digest") == release.get("release_digest")
                ):
                    faults.append("a rollback terminal must target another release")
                if action == "rollback" and sequence == 1:
                    faults.append("a rollback terminal cannot be the first promotion record")
        if promotion_reason is not None:
            faults.append(
                "promotion_absence_reason must be null when promotion is present"
            )
    elif not stated(promotion_reason):
        faults.append("null produced promotion needs a stated promotion_absence_reason")
    return faults


def _identity_document(predicate):
    """Reconstruct the exact Berean identity fields projected by this body."""
    release = predicate["release"]
    corpus = predicate["given"]["corpus"]
    reads = predicate["given"]["reads"]
    produced = predicate["produced"]
    policy = predicate["policy"]
    evaluations = produced["evaluations"]
    return {
        "format": release["format"],
        "release_version": release["release_version"],
        "corpus": {
            "path": corpus["path"],
            "manifest": corpus["manifest"]["path"],
            "manifest_sha256": corpus["manifest"]["sha256"],
            "corpus_version": corpus["corpus_version"],
            "corpus_digest": corpus["corpus_digest"],
        },
        "reads": None
        if reads is None
        else {
            "path": reads["component"]["path"],
            "sha256": reads["component"]["sha256"],
            "chain_id": reads["chain_id"],
            "block_number": reads["block_number"],
            "block_hash": reads["block_hash"],
            "source": reads["source"],
        },
        "answers": [
            {"path": entry["path"], "sha256": entry["sha256"]}
            for entry in produced["answers"]
        ],
        "question_families": policy["question_families"],
        "refusal_conditions": policy["refusal_conditions"],
        "rules": policy["rules"],
        "allowlists": policy["allowlists"],
        "evals": None
        if evaluations is None
        else {
            "cases": evaluations["cases"]["path"],
            "cases_sha256": evaluations["cases"]["sha256"],
            "report": evaluations["report"]["path"],
            "report_sha256": evaluations["report"]["sha256"],
        },
        "retention": policy["retention"],
    }


def semantic_release_digest(predicate):
    """Berean's canonical digest over its named identity fields."""
    body = json.dumps(
        _identity_document(predicate),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def gate_2_environment(statement):
    """Recover the producer format, component bytes, policy and adapter."""
    predicate = statement.predicate
    faults = field_faults(predicate)
    faults.extend(_release_value_faults(predicate))
    faults.extend(_given_faults(predicate))
    faults.extend(_policy_faults(predicate))
    faults.extend(_adapter_faults(predicate))
    faults.extend(_core_block_faults(predicate))
    component_errors, count, _ = component_faults(statement)
    faults.extend(component_errors)
    faults.extend(optional_faults(predicate))
    if faults:
        return Gate(2, "environment", False, "; ".join(faults))
    return Gate(
        2,
        "environment",
        True,
        "%s %s, %d byte component(s), closed policy and adapter parameters"
        % (
            predicate["release"]["format"],
            predicate["release"]["release_version"],
            count,
        ),
    )


def gate_5_comparison(statement):
    """Name the current release and either a baseline or first-capture reason."""
    predicate = statement.predicate
    comparison = predicate.get("comparison") if isinstance(predicate, dict) else None
    if not isinstance(comparison, dict):
        return Gate(5, "comparison", False, "comparison must be an object")
    faults = []
    _shape(comparison, "comparison", COMPARISON_FIELDS, faults)
    current = comparison.get("current")
    if _shape(current, "comparison current", COMPARISON_SIDE_FIELDS, faults):
        if not portable_name(current.get("name")):
            faults.append("comparison current name is not portable")
        if not sha256(current.get("release_digest")):
            faults.append("comparison current release_digest is malformed")
        release = predicate.get("release")
        if isinstance(release, dict) and current.get("release_digest") != release.get("release_digest"):
            faults.append("comparison current does not name this semantic release digest")

    baseline = comparison.get("baseline")
    reason = comparison.get("first_capture_reason")
    if baseline is None:
        if not stated(reason):
            faults.append("a null baseline needs a stated first_capture_reason")
    else:
        if _shape(baseline, "comparison baseline", COMPARISON_SIDE_FIELDS, faults):
            if not portable_name(baseline.get("name")):
                faults.append("comparison baseline name is not portable")
            if not sha256(baseline.get("release_digest")):
                faults.append("comparison baseline release_digest is malformed")
            if isinstance(current, dict) and baseline.get("release_digest") == current.get("release_digest"):
                faults.append("comparison baseline and current are the same release")
        if reason is not None:
            faults.append("first_capture_reason must be null when a baseline exists")
    if faults:
        return Gate(5, "comparison", False, "; ".join(faults))
    if baseline is None:
        detail = "%s, first capture reason recorded" % current["name"]
    else:
        detail = "%s against %s" % (current["name"], baseline["name"])
    return Gate(5, "comparison", True, detail)


def gate_fields(statement):
    faults = field_faults(statement.predicate)
    faults.extend(_core_block_faults(statement.predicate))
    return Gate(
        None,
        "predicate-fields",
        not faults,
        "; ".join(faults) if faults else "top-level and nested fields are closed",
    )


def gate_components(statement):
    faults, count, total = component_faults(statement)
    return Gate(
        None,
        "components",
        not faults,
        "; ".join(faults)
        if faults
        else "%d unique component(s), %d declared byte(s), all subjects covered"
        % (count, total),
    )


def gate_release_digest(statement):
    predicate = statement.predicate
    try:
        expected = semantic_release_digest(predicate)
        actual = predicate["release"]["release_digest"]
    except (KeyError, TypeError, ValueError):
        return Gate(
            None,
            "release-digest",
            False,
            "semantic release identity cannot be reconstructed from the predicate",
        )
    if not sha256(actual):
        return Gate(None, "release-digest", False, "release_digest is malformed")
    if actual != expected:
        return Gate(
            None,
            "release-digest",
            False,
            "release_digest does not match the projected berean-release/v1 identity",
        )
    document = predicate.get("release", {}).get("document")
    if isinstance(document, dict) and actual == document.get("sha256"):
        return Gate(
            None,
            "release-digest",
            False,
            "semantic release_digest was replaced with the release.json byte sha256",
        )
    return Gate(
        None,
        "release-digest",
        True,
        "semantic release digest is distinct from and consistent with release.json bytes",
    )


def gate_optional_evidence(statement):
    faults = optional_faults(statement.predicate)
    return Gate(
        None,
        "optional-evidence",
        not faults,
        "; ".join(faults)
        if faults
        else "reads, evaluations and promotion evidence are explicit objects or null",
    )


def gate_evidence_boundary(statement):
    faults = _policy_faults(statement.predicate)
    faults.extend(_result_projection_faults(statement))
    return Gate(
        None,
        "evidence-boundary",
        not faults,
        "; ".join(faults)
        if faults
        else "Berean source and evidence classes are preserved without upgrade or result projection",
    )


def gate_subject_names(statement):
    faults = []
    seen = set()
    for index, subject in enumerate(statement.subjects[:MAX_SUBJECTS]):
        if not portable_name(subject.name):
            faults.append("statement subject %d has no portable name" % (index + 1))
            continue
        settled = unicodedata.normalize("NFC", subject.name)
        if settled in seen:
            faults.append("statement subject %d repeats a name after Unicode normalisation" % (index + 1))
        seen.add(settled)
    return Gate(
        None,
        "subject-names",
        not faults,
        "; ".join(faults) if faults else "statement subject names are portable and unique",
    )


def check(statement):
    return [
        gate_2_environment(statement),
        gate_5_comparison(statement),
        gate_fields(statement),
        gate_components(statement),
        gate_release_digest(statement),
        gate_optional_evidence(statement),
        gate_evidence_boundary(statement),
        gate_subject_names(statement),
    ]
