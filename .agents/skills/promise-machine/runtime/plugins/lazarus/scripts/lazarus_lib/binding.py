"""Whether a statement describes this fixture, and whether it claims more.

Something else writes the statement. Ariadne's `capture-state-fixture` is the
one this was built against, but nothing here imports it, runs it, or assumes it
produced the document: a statement is JSON somebody handed over, and it gets the
treatment every other document from outside gets.

The check that matters is the evidence one, and it is worth saying exactly why it
cannot be skipped.

Lazarus recomputes the three counts from the proof and RPC records and refuses a
manifest that disagrees with them. Ariadne reads the counts from the manifest and
does not re-derive them, deliberately: re-deriving would mean reimplementing
Lazarus's judgement about which records were checked against the state root, and
a capture that arrived at a larger number would perform the upgrade it exists to
prevent. Both choices are right on their own.

The consequence is a gap neither tool can close alone. Edit one integer in a
manifest, recompute the fixture digest so the document is entirely
self-consistent, and `lazarus verify` refuses it while `ariadne
capture-state-fixture` accepts it and writes a statement that verifies clean,
reporting six proof-backed records where two exist. Four recorded RPC responses
presented as proved state.

So the numbers a statement is held to here come from `verify_fixture`, never from
the manifest. The manifest is the part a producer can edit; the verified report is
what the records actually support.

Every other field the statement states about this capture is compared too. A
field nothing compares is a field a producer writes freely, and a reader has no
way to tell which half of a bound document was checked.
"""

from __future__ import annotations

import ntpath
import unicodedata
from typing import Any

from .errors import FormatError, IntegrityError, ResourceLimitError
from .manifest import MAX_COMPONENTS
from .text import listed, visible

IN_TOTO_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
"""The envelope the predicate is read inside.

A predicate type says how to read `predicate`; the statement type says the
document is the kind of thing that has one. Without it a bare object carrying the
right two strings binds as though it were an attestation.
"""

STATE_FIXTURE_TYPE = "https://ariadne.wildcat.finance/state-fixture/v1"
"""The predicate this binding understands.

Named rather than accepted from the statement, because a binding that took
whichever type it was handed would bind a fixture to a document making claims in
a vocabulary nothing here has read.
"""

STATE_FIXTURE_TYPE_V2 = "https://ariadne.wildcat.finance/state-fixture/v2"
"""The receipt-trie-aware predicate understood by release-v2."""

STATE_FIXTURE_TYPES = {
    1: STATE_FIXTURE_TYPE,
    2: STATE_FIXTURE_TYPE_V2,
}
"""Manifest/release versions map explicitly to predicate versions."""

EVIDENCE_CLASSES = ("proof_backed", "header_bound", "recorded_rpc")
"""The three classes, spelled as this plugin spells them everywhere else."""

EVIDENCE_CLASSES_V2 = EVIDENCE_CLASSES + ("receipt_trie_proved",)
"""The fourth class is limited to the receipt and log-projection relations."""

EVIDENCE_CLASSES_BY_VERSION = {
    1: EVIDENCE_CLASSES,
    2: EVIDENCE_CLASSES_V2,
}

REPLAY_CLAIMS = ("reaches_network", "canonical_chain_claim")
"""The two things verification does not do, which the statement must not say it does."""

REPLAY_CLAIMS_V2 = REPLAY_CLAIMS + ("provider_independence_claim",)
REPLAY_CLAIMS_BY_VERSION = {
    1: REPLAY_CLAIMS,
    2: REPLAY_CLAIMS_V2,
}

MAX_FIXTURE_SUBJECTS = MAX_COMPONENTS
"""A statement cannot describe more components than a fixture can hold.

Taken from the manifest's own limit rather than restated, so the two cannot
drift apart into a statement this accepts and no fixture can satisfy.
"""

MAX_SUBJECTS = 2 * MAX_COMPONENTS
"""The in-toto subject list may name more than the fixture's components.

The capture itself is one, and a producer may have others. The cap is a bound on
work rather than a claim about what belongs there.
"""

CHECKS = (
    "statement-type",
    "predicate-type",
    "chain-and-block",
    "evidence-counts",
    "replay-claims",
    "components-declared",
    "components-complete",
    "subjects-cover-components",
)
"""Every check this module makes, in the order it makes them.

The names go into the release document, so a reader knows which questions were
asked rather than inferring them from the release existing.
"""

STATEMENT_FIELDS = frozenset({"_type", "subject", "predicateType", "predicate"})
RESOURCE_DESCRIPTOR_FIELDS = frozenset(
    {
        "name",
        "uri",
        "digest",
        "content",
        "downloadLocation",
        "mediaType",
        "annotations",
    }
)
V2_PREDICATE_FIELDS = frozenset(
    {
        "chain",
        "capture",
        "fixture_subjects",
        "evidence",
        "replay",
        "deltas",
        "claims",
        "commands",
    }
)
V2_CAPTURE_FIELDS = frozenset(
    {"tool", "tool_version", "command", "parameters_digest"}
)
V2_CHAIN_FIELDS = frozenset(
    {"chain_id", "block_number", "block_hash", "state_root", "receipts_root"}
)
V2_EVIDENCE_FIELDS = frozenset(EVIDENCE_CLASSES_V2)
V2_REPLAY_FIELDS = frozenset(REPLAY_CLAIMS_V2)
V2_FIXTURE_SUBJECT_FIELDS = frozenset({"name", "path", "digest", "bytes"})
V2_DELTA_FIELDS = frozenset(
    {"baseline", "current", "reason", "components"}
)
V2_DELTA_SIDE_FIELDS = frozenset({"name", "digest"})
V2_COMPONENT_DELTA_FIELDS = frozenset({"added", "removed", "changed"})
V2_CHANGED_FIELDS = frozenset({"baseline", "current"})
V2_CLAIM_FIELDS = frozenset(
    {"name", "subject", "disposition", "reason", "detail"}
)
V2_DISPOSITIONS = frozenset(
    {"passed", "failed", "skipped", "timed_out", "redacted"}
)
DIGEST_LENGTHS = {"sha256": 64, "sha384": 96, "sha512": 128}
MAX_V2_PATH = 1024


def _portable_v2(value: Any) -> bool:
    """The exact printable-name rule published by state-fixture/v2."""
    return isinstance(value, str) and any("!" <= char <= "~" for char in value)


def _portable_path_v2(value: Any) -> bool:
    """The exact component-path grammar published by state-fixture/v2."""
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_V2_PATH
        or "\\" in value
        or "\x00" in value
    ):
        return False
    drive, _ = ntpath.splitdrive(value)
    parts = value.split("/")
    return not drive and all(
        part not in ("", ".", "..") and _portable_v2(part) for part in parts
    )


def _closed(
    node: dict[str, Any],
    fields: frozenset[str],
    what: str,
    *,
    required: frozenset[str] | None = None,
) -> None:
    """Hold one v2 object to its published vocabulary without echoing input keys."""
    unknown = set(node) - fields
    if unknown:
        raise IntegrityError(
            f"{what} carries {len(unknown)} field(s) outside its vocabulary"
        )
    missing = (required if required is not None else fields) - set(node)
    if missing:
        raise FormatError(f"{what} is missing {len(missing)} required field(s)")


def _digest_set(value: Any, what: str) -> dict[str, Any]:
    """The digest grammar published by state-fixture/v2, without value echo."""
    value = _object(value, what)
    if not value:
        raise FormatError(f"{what} is empty")
    supported = 0
    for algorithm, digest in value.items():
        if not isinstance(algorithm, str) or not algorithm:
            raise FormatError(f"{what} has an invalid algorithm name")
        if (
            not isinstance(digest, str)
            or not digest
            or digest != digest.lower()
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise FormatError(f"{what} has a digest value outside lowercase hex")
        expected = DIGEST_LENGTHS.get(algorithm)
        if expected is not None:
            supported += 1
            if len(digest) != expected:
                raise FormatError(
                    f"{what} has a {algorithm} value of the wrong length"
                )
    if not supported:
        raise FormatError(f"{what} carries no supported digest algorithm")
    return value


def _v2_side(value: Any, what: str) -> dict[str, Any]:
    side = _object(value, what)
    _closed(side, V2_DELTA_SIDE_FIELDS, what)
    if not _portable_v2(side["name"]):
        raise FormatError(f"{what} has no portable name")
    return _digest_set(side["digest"], f"{what} digest")


def _digests_agree(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """The state-fixture/v2 digest-set identity rule Ariadne publishes."""
    shared = set(left) & set(right)
    return bool(shared & set(DIGEST_LENGTHS)) and all(
        left[algorithm] == right[algorithm] for algorithm in shared
    )


def _covered(
    subjects: list[dict[str, Any]], digest: dict[str, Any]
) -> bool:
    return any(_digests_agree(subject, digest) for subject in subjects)


def _check_v2_deltas(
    predicate: dict[str, Any], subjects: list[dict[str, Any]]
) -> None:
    deltas = _object(_member(predicate, "deltas", "statement predicate"), "deltas")
    _closed(
        deltas,
        V2_DELTA_FIELDS,
        "state-fixture/v2 deltas",
        required=frozenset({"baseline", "current"}),
    )
    current = _v2_side(deltas["current"], "state-fixture/v2 current side")
    if not _covered(subjects, current):
        raise IntegrityError(
            "state-fixture/v2 current side is not covered by the statement "
            "subject list"
        )
    baseline = deltas["baseline"]
    if baseline is None:
        reason = deltas.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise FormatError("state-fixture/v2 null baseline has no reason")
        if "components" in deltas:
            raise IntegrityError(
                "state-fixture/v2 deltas carry components against a null baseline"
            )
    else:
        _v2_side(baseline, "state-fixture/v2 baseline side")
        if "reason" in deltas and not isinstance(deltas["reason"], str):
            raise FormatError("state-fixture/v2 deltas reason must be a string")

    if "components" not in deltas:
        return
    components = _object(
        deltas["components"], "state-fixture/v2 component deltas"
    )
    _closed(
        components,
        V2_COMPONENT_DELTA_FIELDS,
        "state-fixture/v2 component deltas",
        required=frozenset(),
    )
    for field in ("added", "removed"):
        if field not in components:
            continue
        entries = components[field]
        if not isinstance(entries, list) or not all(
            _portable_v2(entry) for entry in entries
        ):
            raise FormatError(
                f"state-fixture/v2 component deltas {field} must name components"
            )
    if "changed" in components:
        changed = components["changed"]
        if not isinstance(changed, list):
            raise FormatError("state-fixture/v2 changed components must be an array")
        for index, entry in enumerate(changed):
            what = f"state-fixture/v2 changed component {index + 1}"
            entry = _object(entry, what)
            _closed(entry, V2_CHANGED_FIELDS, what)
            if not all(
                _portable_v2(entry[field])
                for field in V2_CHANGED_FIELDS
            ):
                raise FormatError(f"{what} does not name both sides")


def _check_v2_claims(
    predicate: dict[str, Any], subjects: list[dict[str, Any]]
) -> None:
    claims = _member(predicate, "claims", "statement predicate")
    if not isinstance(claims, list):
        raise FormatError("state-fixture/v2 claims must be an array")
    for index, claim in enumerate(claims):
        what = f"state-fixture/v2 claim {index + 1}"
        claim = _object(claim, what)
        _closed(
            claim,
            V2_CLAIM_FIELDS,
            what,
            required=frozenset({"name", "subject", "disposition"}),
        )
        if not _portable_v2(claim["name"]):
            raise FormatError(f"{what} name has no portable graphic")
        subject = _digest_set(claim["subject"], f"{what} subject")
        if not _covered(subjects, subject):
            raise IntegrityError(
                f"{what} is not covered by the statement subject list"
            )
        disposition = claim["disposition"]
        if not isinstance(disposition, str) or disposition not in V2_DISPOSITIONS:
            raise FormatError(f"{what} disposition is outside the vocabulary")
        if "reason" in claim and not isinstance(claim["reason"], str):
            raise FormatError(f"{what} reason must be a string")
        if disposition != "passed" and (
            not isinstance(claim.get("reason"), str)
            or not claim["reason"].strip()
        ):
            raise FormatError(f"{what} has no reason for its disposition")
        if "detail" in claim and not isinstance(claim["detail"], dict):
            raise FormatError(f"{what} detail must be an object")


def _check_v2_vocabulary(
    statement: dict[str, Any], predicate: dict[str, Any]
) -> None:
    """Refuse a type label whose document does not implement that v2 type.

    Release cannot import Ariadne at runtime, so it carries the public structural
    vocabulary it claims to understand. Version 1 retains its historical binding;
    version 2 is new and may fail closed before a release publishes its exact bytes.
    """
    _closed(statement, STATEMENT_FIELDS, "state-fixture/v2 statement")
    _closed(predicate, V2_PREDICATE_FIELDS, "state-fixture/v2 predicate")

    # These are work limits, so enforce them before digest validation or
    # cross-list coverage.  Applying the same caps later in the semantic checks
    # still bounded what was accepted, but not the work spent reaching refusal.
    fixture_subjects = predicate["fixture_subjects"]
    if (
        isinstance(fixture_subjects, list)
        and len(fixture_subjects) > MAX_FIXTURE_SUBJECTS
    ):
        raise ResourceLimitError(
            f"statement describes {len(fixture_subjects)} components and a "
            f"fixture holds at most {MAX_FIXTURE_SUBJECTS}"
        )
    subjects = statement["subject"]
    if isinstance(subjects, list) and len(subjects) > MAX_SUBJECTS:
        raise ResourceLimitError(
            f"statement lists {len(subjects)} subjects and this reads at most "
            f"{MAX_SUBJECTS}"
        )

    capture = _object(predicate["capture"], "state-fixture/v2 capture")
    _closed(capture, V2_CAPTURE_FIELDS, "state-fixture/v2 capture")
    for field in ("tool", "tool_version"):
        if not _portable_v2(capture[field]):
            raise FormatError(
                f"state-fixture/v2 capture {field} has no portable name"
            )
    command = capture["command"]
    if (
        not isinstance(command, list)
        or not command
        or not all(_portable_v2(word) for word in command)
    ):
        raise FormatError("state-fixture/v2 capture command is not a non-empty argv")
    _digest_set(
        capture["parameters_digest"],
        "state-fixture/v2 capture parameters_digest",
    )
    _closed(
        _object(predicate["chain"], "state-fixture/v2 chain"),
        V2_CHAIN_FIELDS,
        "state-fixture/v2 chain",
        required=frozenset(),
    )
    _closed(
        _object(predicate["evidence"], "state-fixture/v2 evidence"),
        V2_EVIDENCE_FIELDS,
        "state-fixture/v2 evidence",
        required=frozenset(),
    )
    _closed(
        _object(predicate["replay"], "state-fixture/v2 replay"),
        V2_REPLAY_FIELDS,
        "state-fixture/v2 replay",
        required=frozenset(),
    )

    fixture_digests = []
    if isinstance(fixture_subjects, list):
        for index, entry in enumerate(fixture_subjects):
            what = f"state-fixture/v2 fixture subject {index + 1}"
            entry = _object(entry, what)
            _closed(entry, V2_FIXTURE_SUBJECT_FIELDS, what)
            if not _portable_v2(entry["name"]):
                raise FormatError(f"{what} has no portable name")
            if not _portable_path_v2(entry["path"]):
                raise IntegrityError(f"{what} has no portable component path")
            fixture_digests.append(
                _digest_set(entry["digest"], f"{what} digest")
            )

    if not isinstance(subjects, list) or not subjects:
        raise FormatError(
            "state-fixture/v2 subject must be a non-empty array"
        )
    subject_digests = []
    for index, entry in enumerate(subjects):
        what = f"state-fixture/v2 subject {index + 1}"
        entry = _object(entry, what)
        _closed(
            entry,
            RESOURCE_DESCRIPTOR_FIELDS,
            what,
            required=frozenset({"digest"}),
        )
        if not _portable_v2(entry.get("name")):
            raise FormatError(f"{what} has no portable name")
        subject_digests.append(_digest_set(entry["digest"], f"{what} digest"))

    if any(not _covered(subject_digests, digest) for digest in fixture_digests):
        raise IntegrityError(
            "state-fixture/v2 fixture subjects are not all covered by the "
            "statement subject list"
        )
    _check_v2_deltas(predicate, subject_digests)
    _check_v2_claims(predicate, subject_digests)
    commands = predicate["commands"]
    if not isinstance(commands, list) or commands:
        raise IntegrityError(
            "state-fixture/v2 replay is local-file verification only and carries "
            "no executable commands"
        )


def _object(value: Any, what: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FormatError(f"{what} must be an object, got {type(value).__name__}")
    return value


def _checked_v2(what: str, check: Any, *arguments: Any) -> None:
    """Run one semantic bind without retaining rejected statement values.

    The structural v2 checker above emits value-free diagnostics itself.  The
    shared semantic checks retain v1's historical, value-rich messages, so v2
    calls cross this small boundary before they reach a terminal or log.
    """
    failure = None
    try:
        check(*arguments)
    except (FormatError, IntegrityError, ResourceLimitError) as error:
        failure = type(error)
    if failure is not None:
        raise failure(f"state-fixture/v2 {what} check failed")


def _member(node: dict[str, Any], key: str, what: str) -> Any:
    if key not in node:
        raise FormatError(f"{what} has no {key}")
    return node[key]


def _whole_number(value: Any) -> bool:
    """`True` is an integer in Python and one record if nothing looks."""
    return isinstance(value, int) and not isinstance(value, bool)


def _hex_quantity(value: Any, what: str) -> int:
    """A verified hex quantity as the integer a statement writes it as."""
    if not isinstance(value, str) or not value.startswith("0x"):
        raise FormatError(f"{what} is not a hex quantity: {value!r}")
    try:
        return int(value, 16)
    except ValueError:
        raise FormatError(f"{what} is not a hex quantity: {value!r}") from None


def _named(entry: dict[str, Any], what: str, seen: set[str]) -> str:
    """A name that names something, and names it once.

    Compared in composed form. Two Unicode spellings of one name are one name to
    a reader, and a duplicate that gets past this rule by being spelled the other
    way is the ambiguity the rule exists to refuse.
    """
    name = _member(entry, "name", what)
    if not isinstance(name, str) or not visible(name):
        raise FormatError(f"{what} names nothing: {name!r}")
    settled = unicodedata.normalize("NFC", name)
    if settled in seen:
        raise IntegrityError(
            f"statement uses the name {name} twice; a reader matching a subject "
            "by name cannot tell which digest was meant"
        )
    seen.add(settled)
    return name


def _verified_manifest(manifest: Any) -> dict[str, Any]:
    """The fields this binding reads out of a manifest, present and shaped.

    Not a second verification: `verify_manifest` did that, and a caller who
    skipped it is not caught here. It is the difference between a refusal naming
    the field and a traceback out of the middle of a comparison, for a caller who
    handed over the manifest read off disk rather than the verified one.
    """
    manifest = _object(manifest, "manifest")
    version = _member(manifest, "schema_version", "manifest")
    if not _whole_number(version) or version not in STATE_FIXTURE_TYPES:
        raise FormatError(
            f"manifest schema_version {version!r} has no preservation binding"
        )
    _member(manifest, "chain_id", "manifest")
    components = _member(manifest, "components", "manifest")
    if not isinstance(components, list) or not components:
        raise FormatError("manifest components must be a non-empty array")
    for index, entry in enumerate(components):
        what = f"manifest component {index + 1}"
        entry = _object(entry, what)
        path = _member(entry, "path", what)
        if not isinstance(path, str) or not visible(path):
            raise FormatError(f"{what} path names nothing: {path!r}")
        digest = _member(entry, "sha256", what)
        if not isinstance(digest, str) or not visible(digest):
            raise FormatError(f"{what} has no sha256 digest: {digest!r}")
        size = _member(entry, "bytes", what)
        if not _whole_number(size) or size < 0:
            raise FormatError(f"{what} bytes is {size!r} rather than a byte count")
    if version == 2:
        receipts_root = _member(manifest, "receipts_root", "manifest")
        if not isinstance(receipts_root, str) or not visible(receipts_root):
            raise FormatError(
                f"manifest receipts_root names nothing: {receipts_root!r}"
            )
    return manifest


def _verified_report(report: Any, version: int) -> dict[str, Any]:
    """The fields this binding reads out of a verified report, present and shaped."""
    report = _object(report, "report")
    for field in ("block_hash", "block_number", "state_root"):
        value = _member(report, field, "report")
        if not isinstance(value, str) or not visible(value):
            raise FormatError(f"report {field} names nothing: {value!r}")
    counts = _object(
        _member(report, "evidence_counts", "report"), "report evidence_counts"
    )
    classes = EVIDENCE_CLASSES_BY_VERSION[version]
    for name in classes:
        value = _member(counts, name, "report evidence_counts")
        if not _whole_number(value) or value < 0:
            raise FormatError(
                f"report {name} count is {value!r} rather than a number of records"
            )
    if set(counts) != set(classes):
        raise IntegrityError(
            f"state-fixture/v{version} binding refuses evidence classes outside "
            "its vocabulary"
        )
    header = _object(_member(report, "header_bound", "report"), "report header_bound")
    _member(header, "canonical_chain_claim", "report header_bound")
    if version == 2:
        receipts_root = _member(report, "receipts_root", "report")
        if not isinstance(receipts_root, str) or not visible(receipts_root):
            raise FormatError(f"report receipts_root names nothing: {receipts_root!r}")
        relation = _object(
            _member(report, "receipt_trie_proved", "report"),
            "report receipt_trie_proved",
        )
        relations = _member(relation, "relations", "report receipt_trie_proved")
        if not _whole_number(relations) or relations != counts["receipt_trie_proved"]:
            raise IntegrityError(
                "report receipt-trie relation count disagrees with evidence_counts"
            )
    return report


def predicate_type_of(statement: dict[str, Any]) -> str:
    """The type a statement declares, checked for shape before it is compared."""
    found = _member(_object(statement, "statement"), "predicateType", "statement")
    if not isinstance(found, str) or not visible(found):
        raise FormatError(f"statement predicateType names nothing: {found!r}")
    return found


def _check_statement_type(statement: dict[str, Any]) -> None:
    found = _member(statement, "_type", "statement")
    if not isinstance(found, str) or not visible(found):
        raise FormatError(f"statement _type names nothing: {found!r}")
    if found != IN_TOTO_STATEMENT_TYPE:
        raise IntegrityError(
            f"statement _type is {found!r} and this binds "
            f"{IN_TOTO_STATEMENT_TYPE}; a predicate type is read inside an "
            "envelope, and there is no envelope here"
        )


def _check_predicate_type(statement: dict[str, Any], expected: str) -> None:
    found = predicate_type_of(statement)
    if found != expected:
        raise IntegrityError(
            f"statement is a {found} and this binds {expected}; a "
            "binding cannot speak for claims in a vocabulary it has not read"
        )


def _check_chain_and_block(
    predicate: dict[str, Any],
    manifest: dict[str, Any],
    report: dict[str, Any],
    version: int,
) -> None:
    """The four fields naming which capture the statement is about.

    The block hash alone would leave the other three free: a statement pinning the
    right hash while naming another chain, another height and another state root
    reads as though all four were corroborated, and one of them was.
    """
    chain = _object(_member(predicate, "chain", "statement predicate"), "statement chain")
    allowed = {"chain_id", "block_number", "block_hash", "state_root"}
    if version == 2:
        allowed.add("receipts_root")
    unknown = sorted(set(chain) - allowed)
    if unknown:
        if version == 2:
            _closed(
                chain,
                frozenset(allowed),
                "state-fixture/v2 chain",
                required=frozenset(),
            )
        raise IntegrityError(
            "state-fixture/v1 chain carries fields outside its vocabulary: "
            + listed(unknown)
        )

    def hash_agrees(found: Any, expected: str) -> bool:
        if not isinstance(found, str):
            return False
        if version == 2:
            # State-fixture/v2 publishes one lowercase spelling.  Version 1's
            # historical binding remains case-insensitive.
            return found == found.lower() and found == expected
        return found.lower() == expected

    found = _member(chain, "block_hash", "statement chain")
    expected = report["block_hash"]
    if not hash_agrees(found, expected):
        raise IntegrityError(
            f"statement pins block {found!r} and the fixture verifies to "
            f"{expected}; the statement describes a different capture"
        )

    chain_id = _member(chain, "chain_id", "statement chain")
    expected_chain = _hex_quantity(manifest["chain_id"], "manifest chain_id")
    if not _whole_number(chain_id) or chain_id != expected_chain:
        raise IntegrityError(
            f"statement names chain {chain_id!r} and the fixture is chain "
            f"{expected_chain}"
        )

    number = _member(chain, "block_number", "statement chain")
    expected_number = _hex_quantity(report["block_number"], "verified block number")
    if not _whole_number(number) or number != expected_number:
        raise IntegrityError(
            f"statement names block number {number!r} and the verified header is "
            f"block {expected_number}"
        )

    state_root = _member(chain, "state_root", "statement chain")
    expected_root = report["state_root"]
    if not hash_agrees(state_root, expected_root):
        raise IntegrityError(
            f"statement names state root {state_root!r} and the verified header "
            f"has {expected_root}; every proof in this fixture was checked "
            "against the header's root, not the statement's"
        )

    if version == 2:
        receipts_root = _member(chain, "receipts_root", "statement chain")
        expected_receipts_root = report["receipts_root"]
        if not hash_agrees(receipts_root, expected_receipts_root):
            raise IntegrityError(
                f"statement names receipts root {receipts_root!r} and the verified "
                f"receipt witness reconstructs {expected_receipts_root}; the state "
                "root grants no receipt-trie authority"
            )


def _check_evidence_counts(
    predicate: dict[str, Any], report: dict[str, Any], version: int
) -> None:
    """The rule this module exists for.

    Compared against the recomputed counts rather than the manifest's, and in
    both directions. A statement claiming fewer records than the fixture holds is
    wrong too: it describes a fixture nobody has, and the next reader cannot tell
    which of the two is the mistake.
    """
    evidence = _object(_member(predicate, "evidence", "statement predicate"), "evidence")
    verified = report["evidence_counts"]
    classes = EVIDENCE_CLASSES_BY_VERSION[version]
    unknown = sorted(set(evidence) - set(classes))
    if unknown:
        if version == 2:
            _closed(
                evidence,
                frozenset(classes),
                "state-fixture/v2 evidence",
                required=frozenset(),
            )
        raise IntegrityError(
            "statement counts evidence in classes this fixture does not have: "
            + listed(unknown)
        )
    for name in classes:
        if name not in evidence:
            raise IntegrityError(
                f"statement has no {name} count; a class left out reads as "
                "nothing of that kind rather than as nobody having said"
            )
        claimed = evidence[name]
        if not _whole_number(claimed):
            raise IntegrityError(
                f"statement {name} count is {claimed!r} rather than a whole "
                "number of records"
            )
        if claimed != verified[name]:
            direction = "more" if claimed > verified[name] else "fewer"
            raise IntegrityError(
                f"statement claims {claimed} {name} record(s) and the fixture "
                f"verifies to {verified[name]}: {direction} than the records "
                "support"
            )


def _check_replay_claims(
    predicate: dict[str, Any], report: dict[str, Any], version: int
) -> None:
    """Both of the two things a replay does not establish.

    `canonical_chain_claim` is the one that matters most: a self-consistent header
    is not proof that it belongs to Ethereum's canonical chain. `reaches_network`
    is the same shape of claim pointed the other way, and a statement saying
    verification went to a node would have a reader believe the records were
    corroborated live. Neither happened, so neither may be said.
    """
    replay = _object(_member(predicate, "replay", "statement predicate"), "statement replay")
    claims = REPLAY_CLAIMS_BY_VERSION[version]
    unknown = sorted(set(replay) - set(claims))
    if unknown:
        if version == 2:
            _closed(
                replay,
                frozenset(claims),
                "state-fixture/v2 replay",
                required=frozenset(),
            )
        raise IntegrityError(
            "state-fixture/v1 replay carries fields outside its vocabulary: "
            + listed(unknown)
        )
    for field in claims:
        claimed = _member(replay, field, "statement replay")
        if claimed is not False:
            raise IntegrityError(
                f"statement records {field} as {claimed!r}; verification reads "
                "recorded bytes offline and claims neither"
            )
    if report["header_bound"]["canonical_chain_claim"] is not False:
        raise IntegrityError(
            "the verified report claims the canonical chain, which no Lazarus "
            "build establishes"
        )
    if version == 2:
        anchors = _object(
            _member(report, "chain_anchors", "report"), "report chain_anchors"
        )
        if anchors.get("provider_independence_claim") is not False:
            raise IntegrityError(
                "the verified report claims provider independence, which matching "
                "operator-chosen source labels do not establish"
            )


def _declared_components(predicate: dict[str, Any]) -> dict[str, dict[str, Any]]:
    subjects = _member(predicate, "fixture_subjects", "statement predicate")
    if not isinstance(subjects, list) or not subjects:
        raise FormatError("statement fixture_subjects must be a non-empty array")
    if len(subjects) > MAX_FIXTURE_SUBJECTS:
        raise ResourceLimitError(
            f"statement describes {len(subjects)} components and a fixture holds "
            f"at most {MAX_FIXTURE_SUBJECTS}"
        )
    found: dict[str, dict[str, Any]] = {}
    names: set[str] = set()
    for index, entry in enumerate(subjects):
        what = f"statement fixture subject {index + 1}"
        entry = _object(entry, what)
        _named(entry, what, names)
        path = _member(entry, "path", what)
        if not isinstance(path, str) or not visible(path):
            raise FormatError(f"{what} path names nothing: {path!r}")
        if path in found:
            raise IntegrityError(
                f"statement names {path} twice; one file cannot carry two digests"
            )
        found[path] = entry
    return found


def _check_components(predicate: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Both directions, and the digests in between.

    A component the statement names and the fixture lacks is a statement about a
    file nobody has. A component the fixture holds and the statement omits is a
    file the statement's own subject list does not cover, which is the silent
    absence this plugin refuses everywhere else.
    """
    declared = _declared_components(predicate)
    held = {entry["path"]: entry for entry in manifest["components"]}

    absent = sorted(set(declared) - set(held))
    if absent:
        raise IntegrityError(
            "statement names components the fixture does not hold: "
            + listed(absent)
        )
    missing = sorted(set(held) - set(declared))
    if missing:
        raise IntegrityError(
            "statement does not name components the fixture holds: "
            + listed(missing)
        )

    for path in sorted(held):
        entry = declared[path]
        digest = _object(
            _member(entry, "digest", f"statement fixture subject {path}"),
            f"statement fixture subject {path} digest",
        )
        claimed = digest.get("sha256")
        if claimed != held[path]["sha256"]:
            raise IntegrityError(
                f"statement digests {path} as {claimed!r} and the fixture holds "
                f"{held[path]['sha256']}"
            )
        size = _member(entry, "bytes", f"statement fixture subject {path}")
        if not _whole_number(size) or size != held[path]["bytes"]:
            raise IntegrityError(
                f"statement sizes {path} at {size!r} and the fixture holds "
                f"{held[path]['bytes']} bytes"
            )


def _check_subjects(statement: dict[str, Any], manifest: dict[str, Any]) -> None:
    """The list an in-toto reader actually reads.

    `predicate.fixture_subjects` is where the detail lives, but a policy engine
    handed this statement matches on `subject`. A component described in the
    predicate and absent from the subject list is bound here and invisible there.
    """
    subjects = _member(statement, "subject", "statement")
    if not isinstance(subjects, list) or not subjects:
        raise FormatError("statement subject must be a non-empty array")
    if len(subjects) > MAX_SUBJECTS:
        raise ResourceLimitError(
            f"statement lists {len(subjects)} subjects and this reads at most "
            f"{MAX_SUBJECTS}"
        )
    digests: set[str] = set()
    names: set[str] = set()
    for index, entry in enumerate(subjects):
        what = f"statement subject {index + 1}"
        entry = _object(entry, what)
        _named(entry, what, names)
        digest = _object(_member(entry, "digest", what), f"{what} digest")
        claimed = digest.get("sha256")
        if not isinstance(claimed, str) or not visible(claimed):
            raise FormatError(f"{what} has no sha256 digest: {claimed!r}")
        digests.add(claimed.lower())
    uncovered = sorted(
        entry["path"]
        for entry in manifest["components"]
        if entry["sha256"] not in digests
    )
    if uncovered:
        raise IntegrityError(
            "statement subject list does not cover components the fixture holds: "
            + listed(uncovered)
        )


def bind(
    statement: dict[str, Any],
    manifest: dict[str, Any],
    report: dict[str, Any],
) -> list[str]:
    """Check a statement against a verified fixture; return the checks made.

    `report` is what `verify_fixture` returned, not what the manifest claims. The
    caller has to have verified the fixture, because everything the evidence check
    is worth depends on the counts having been recomputed from the records.

    Raises on the first disagreement rather than collecting them. A statement that
    disagrees about the block it pins is not a document whose component list is
    worth reading, and a release is refused whole.
    """
    statement = _object(statement, "statement")
    manifest = _verified_manifest(manifest)
    version = manifest["schema_version"]
    report = _verified_report(report, version)
    predicate = _object(
        _member(statement, "predicate", "statement"), "statement predicate"
    )
    if version == 2:
        _checked_v2("statement type", _check_statement_type, statement)
        _checked_v2(
            "predicate type",
            _check_predicate_type,
            statement,
            STATE_FIXTURE_TYPES[version],
        )
        _check_v2_vocabulary(statement, predicate)
        _checked_v2(
            "chain and receipts root",
            _check_chain_and_block,
            predicate,
            manifest,
            report,
            version,
        )
        _checked_v2(
            "evidence counts", _check_evidence_counts, predicate, report, version
        )
        _checked_v2(
            "replay provider_independence (provider independence) claims",
            _check_replay_claims,
            predicate,
            report,
            version,
        )
        _checked_v2("fixture components", _check_components, predicate, manifest)
        _checked_v2("statement subjects", _check_subjects, statement, manifest)
    else:
        _check_statement_type(statement)
        _check_predicate_type(statement, STATE_FIXTURE_TYPES[version])
        _check_chain_and_block(predicate, manifest, report, version)
        _check_evidence_counts(predicate, report, version)
        _check_replay_claims(predicate, report, version)
        _check_components(predicate, manifest)
        _check_subjects(statement, manifest)
    return list(CHECKS)
