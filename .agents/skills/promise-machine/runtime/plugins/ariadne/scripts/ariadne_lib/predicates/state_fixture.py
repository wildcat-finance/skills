"""The state-fixture predicate: a pinned block, and how much of it was proved.

Its subject is a component of a captured fixture -- a manifest, a header, a proof
record, a recorded response -- rather than compiled bytecode or a released data
file. What it adds to the core block is the part that decides whether a fixture
can stand in for an archive node: the pin somebody else can find the same state
from, and the split between evidence that was proved against that pin and
evidence that was merely written down.

That split is the whole reason this predicate exists. Lazarus records three
classes of evidence and its skill forbids describing one as another: `proof_backed`
was checked against the pinned block's state root, `header_bound` is tied to the
captured header without a trie proof, and `recorded_rpc` is a response an endpoint
gave that nothing verified. A statement that moves a count between those columns,
or omits a column, claims more than the tool that produced it did. The evidence
check refuses the shapes that would let it.

Two gates belong here, as they do for any predicate. Gate 2 holds that the
environment is recoverable, which for a fixture means the pin: a chain, a block
number, a block hash and a state root, plus the tool that captured it. Gate 5
holds that a comparison names both sides.

Two further checks are this predicate's own. The evidence check is where the
class split is enforced, including the rule this type would be worthless without:
a proof-backed count above zero needs a state root to have been proved against.
The replay check refuses a fixture whose replay reaches a network, because a
boundary that falls back to an endpoint is not the closed one Lazarus describes,
and refuses a canonical-chain claim, because nothing in either tool establishes
that the pinned block is on the canonical chain.

Numbers are integers here. A Lazarus manifest writes a block number as the hex
quantity string `"0xc7da16"`, which is the right thing on the wire and the wrong
thing to compare: `"0xc7da16" < "0x2"` is true, because that orders text. The
capture path converts, and a statement carrying the wire form is refused rather
than ordered as a string. The same choice applies to the chain id, which the
Solidity release predicate already carries as an integer.
"""

import ntpath
import posixpath
import re
import unicodedata

from .. import deltas as deltas_module
from .. import digests
from ..core_predicate import check_side, missing
from ..gates import Gate

TYPE = "https://ariadne.wildcat.finance/state-fixture/v1"
SUMMARY = "a state fixture: the pinned block, its components, and what was proved"
EXPECTED_RESULTS = (
    (2, "environment"),
    (5, "deltas"),
    (None, "predicate-fields"),
    (None, "evidence"),
    (None, "replay"),
)

TYPE_V2 = "https://ariadne.wildcat.finance/state-fixture/v2"
SUMMARY_V2 = (
    "a state fixture: independently proved state and consensus-receipt evidence"
)

EVIDENCE_CLASSES = ("proof_backed", "header_bound", "recorded_rpc")
"""The three classes, spelled as Lazarus spells them in its manifest schema.

Copied rather than imported: Ariadne reads statements and depends on no other
plugin at run time. A test reads the names out of
`plugins/lazarus/schemas/manifest-v1.json` and fails if they drift, so the copy
is checked rather than trusted.
"""

PROVED = "proof_backed"
"""The one class that requires a state root. Named, because the rule reads better
than the index and a rename here is a one-line change."""

CHAIN_REQUIRED = ("chain_id", "block_number", "block_hash")
"""The pin: which chain, which height, which of the blocks at that height.

`state_root` is not here, and leaving it out was a correction rather than an
oversight. Requiring it unconditionally made the evidence check's central rule
unreachable: a statement with no state root already failed gate 2, so the rule
refusing a proof-backed count without one could only ever fire beside a gate that
had refused the statement anyway. It read as the safeguard this type exists for
and guarded nothing.

It also refused an honest fixture. A capture that recorded a header and some
responses and proved nothing against the trie has no use for a state root, and a
pin without one still identifies exactly one block.

So the root is required by what a statement claims rather than by its shape, and
the evidence check owns that rule. Lazarus writes a state root into every header
its schema accepts, so every fixture it produces still carries one.
"""

CHAIN_FIELDS = CHAIN_REQUIRED + ("state_root",)
"""Every key the pin may carry."""
RECEIPT_PROVED = "receipt_trie_proved"
EVIDENCE_CLASSES_V2 = EVIDENCE_CLASSES + (RECEIPT_PROVED,)
CHAIN_FIELDS_V2 = CHAIN_FIELDS + ("receipts_root",)
CAPTURE_REQUIRED = ("tool", "tool_version", "command", "parameters_digest")
FIXTURE_SUBJECT_REQUIRED = ("name", "path", "digest", "bytes")
REPLAY_REQUIRED = ("reaches_network", "canonical_chain_claim")
"""Both must be present and both must be false.

These cannot go through `missing()`, which reads `False` as absent -- the value
this predicate demands. Membership is tested directly.
"""

DELTA_SECTIONS = ("components",)
COMPONENT_KEYS = ("added", "removed", "changed")
BOTH_SIDED = ("changed",)

PREDICATE_FIELDS = (
    "chain",
    "capture",
    "fixture_subjects",
    "evidence",
    "replay",
    "deltas",
    "claims",
    "commands",
)
"""Everything this predicate carries, the last two inherited from the core."""

REQUIRED_FIELDS = PREDICATE_FIELDS
"""Nothing here is optional. A fixture that proved nothing records a zero in each
evidence class, which says the question was asked and answered; leaving the block
out would leave it open."""

HASH32 = re.compile(r"^0x[0-9a-f]{64}$")
"""A block hash or a state root, lowercase.

Lazarus's own schema accepts either case for a block hash. This predicate does
not, for the reason `digests.check` does not: two spellings of one value compare
unequal, and a statement is a thing other implementations compare.
"""

ZERO_HASH = "0x" + "0" * 64
"""The unset value, refused wherever a hash is required.

It matches `HASH32` and identifies nothing. A proof-backed count above zero beside
this state root is the shape this repository keeps meeting: a field that satisfies
a presence and a shape check while carrying no evidence. It is not the empty trie
root, which is a real keccak digest; it is what a producer writes when the value
was never filled in.
"""

MAX_BYTES = 536870912
"""One component's byte count, matching the ceiling Lazarus's manifest schema
sets. A larger number describes a file neither tool would have written."""

MAX_PATH = 1024
"""The component-path ceiling published by the v2 schema."""

MAX_FIXTURE_SUBJECTS_V2 = 1024
"""The v2 component ceiling published by the schema and Lazarus manifest."""

MAX_COUNT = 100000
"""One evidence class's count, matching the ceiling Lazarus's manifest schema sets.

Both ceilings come from that schema rather than from an opinion here, so a fixture
Lazarus would accept is one this predicate accepts. The count ceiling was in the
published schema before it was in this module, which is drift of exactly the kind
the schema exists to prevent: a statement with a larger count passed the verifier
and was refused by the schema the verifier ships beside. A sweep found it and the
drift tests now compare the bounds rather than only the field names.
"""


def usable_path(value):
    """True for a fixture-relative path a reader can resolve safely.

    A consumer resolves `path` against a fixture directory. An absolute path or
    one carrying a `..` segment resolves somewhere else, so a statement using
    either describes a file the fixture does not hold and points a careless
    reader out of the tree.
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


def portable_name_v2(value):
    """True when a v2 machine-read name contains one portable graphic.

    JSON Schema regular expressions have no portable spelling for every Unicode
    control, format, private-use and unassigned category.  Requiring one ASCII
    graphic is exact in the schema and in Python, still permits surrounding
    Unicode, and keeps a name made entirely of invisible code points from passing
    one reader and failing another.
    """
    return isinstance(value, str) and any("!" <= char <= "~" for char in value)


def subject_names_v2(statement):
    """Refuse unreadable or normalisation-colliding v2 subject names.

    Lazarus release binding identifies subjects for a reader as well as by
    digest. Apply its name boundary to both the predicate's component list and
    the in-toto subject list so a hand-authored statement cannot bypass the
    capture adapter and reach a later release refusal.
    """
    groups = (
        (
            "fixture subject",
            statement.predicate.get("fixture_subjects", [])
            if isinstance(statement.predicate, dict)
            else [],
            lambda entry: entry.get("name") if isinstance(entry, dict) else None,
        ),
        ("statement subject", statement.subjects, lambda entry: entry.name),
    )
    faults = []
    for label, entries, name_of in groups:
        if not isinstance(entries, list):
            continue
        seen = set()
        for index, entry in enumerate(entries):
            name = name_of(entry)
            if not portable_name_v2(name):
                faults.append("%s %d has no portable name" % (label, index + 1))
                continue
            settled = unicodedata.normalize("NFC", name)
            if settled in seen:
                faults.append(
                    "%s %d repeats a name after Unicode normalisation"
                    % (label, index + 1)
                )
            seen.add(settled)
    return Gate(
        None,
        "subject-names",
        not faults,
        "; ".join(faults) if faults else "subject names are portable and unique",
    )


def usable_path_v2(value):
    """The portable component path published by the v2 schema.

    Version 1 retains its historical POSIX backslash behaviour. Version 2 is a
    new contract and refuses a backslash, which another host can interpret as a
    separator, paths beyond its explicit schema ceiling, and a segment with no
    portable graphic and therefore no cross-reader visible name.
    """
    if (
        not usable_path(value)
        or "\\" in value
        or "\x00" in value
        or len(value) > MAX_PATH
    ):
        return False
    # `C:component.json` is drive-relative on Windows even though ntpath does
    # not call it absolute. Dot segments likewise give multiple spellings of
    # one component, and a trailing slash names a directory rather than a file.
    # Every segment must also contain one printable ASCII graphic. Surrounding
    # Unicode is retained, while a segment made only of control, format or
    # private-use code points cannot look empty to one reader and named to
    # another. Version 2 is the portable contract, so refuse these forms here.
    drive, _ = ntpath.splitdrive(value)
    parts = value.split("/")
    return not drive and all(
        part not in ("", ".", "..") and portable_name_v2(part) for part in parts
    )


def stated(value):
    """True for a non-blank string.

    A field holding `"   "` satisfies a presence check while naming nothing,
    which is the shape this predicate spends its checks refusing.
    """
    return isinstance(value, str) and bool(value.strip())


def whole_number(value):
    """True for an integer this predicate will order or count. `bool` is not one.

    Python makes `True` an integer and `True > 0` an answer. An evidence count of
    `true` is a producer error, and reading it as one proof-backed record would
    turn a mistake into a claim.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def hash32(value):
    """True for a lowercase 0x-prefixed 32-byte hash that identifies something.

    The all-zero hash is refused. It satisfies the pattern and names nothing, and
    accepting it would let a proof-backed count sit beside a state root that was
    never filled in.
    """
    if not isinstance(value, str) or not HASH32.fullmatch(value):
        return False
    return value != ZERO_HASH


def exactly_false(record, field):
    """True when the field is present and is the boolean `False`.

    `0` is not accepted. The field records a decision somebody made, and a
    producer writing `0` has not made it in the vocabulary the field is in.
    """
    return field in record and record[field] is False


def _gate_2_environment(
    statement,
    chain_fields,
    path_check=usable_path,
    max_subjects=None,
    strict_shape=False,
    name_check=stated,
):
    """A block number is not a pin.

    Recoverable means somebody else can find the same state again: the chain, the
    block number, the block hash and the state root together. Any one of them
    alone leaves a reader guessing which chain, which fork, or which of two
    blocks at the same height. The capture tool comes with it, because a fixture
    is only as reproducible as the thing that wrote it, and every component
    digest must be a subject of the statement.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(2, "environment", False, "no predicate to describe a pin")

    faults = []

    chain = predicate.get("chain")
    absent = missing(chain, CHAIN_REQUIRED)
    # A block number of 0 is genesis, a real block, and `0` lands in `missing`
    # as though the field were absent.
    if "block_number" in absent and isinstance(chain, dict):
        if chain.get("block_number") == 0:
            absent = [field for field in absent if field != "block_number"]
    if absent:
        faults.append("chain is missing %s" % ", ".join(absent))
    else:
        if not whole_number(chain["chain_id"]) or chain["chain_id"] < 1:
            faults.append(
                "chain_id must be a whole number, not %r; a hex quantity string "
                "is the wire form and does not compare as a number"
                % (chain["chain_id"],)
            )
        if not whole_number(chain["block_number"]) or chain["block_number"] < 0:
            faults.append(
                "block_number must be a whole number, not %r; a hex quantity "
                "string is the wire form and orders as text"
                % (chain["block_number"],)
            )
        if not hash32(chain["block_hash"]):
            faults.append(
                "block_hash must be a lowercase 0x-prefixed 32-byte hash, not %r"
                % (chain["block_hash"],)
            )
        # Present roots are checked here; absence is the evidence check's
        # question, because whether a fixture needs either root depends on the
        # independently counted class that claims its authority.
        for root_field in sorted(set(chain_fields) - set(CHAIN_REQUIRED)):
            if root_field in chain and not hash32(chain[root_field]):
                faults.append(
                    "%s must be a lowercase 0x-prefixed 32-byte hash, not %r"
                    % (root_field, chain[root_field])
                )
    if isinstance(chain, dict):
        unknown = sorted(set(chain) - set(chain_fields))
        if unknown:
            faults.append(
                "chain carries fields this type does not define: %s"
                % ", ".join(unknown)
            )

    capture = predicate.get("capture")
    absent = missing(capture, CAPTURE_REQUIRED)
    if absent:
        faults.append("capture is missing %s" % ", ".join(absent))
    else:
        if strict_shape:
            unknown = sorted(set(capture) - set(CAPTURE_REQUIRED))
            if unknown:
                faults.append(
                    "capture carries fields this type does not define: %s"
                    % ", ".join(unknown)
                )
        for field in ("tool", "tool_version"):
            if not name_check(capture.get(field)):
                faults.append("capture %s must name something" % field)
        command = capture.get("command")
        if not isinstance(command, list) or not all(
            name_check(word) for word in command
        ):
            faults.append(
                "capture command must be an argv of non-empty strings; a word "
                "that is empty or only whitespace is not what ran"
            )
        try:
            digests.check(capture["parameters_digest"])
        except digests.DigestError as error:
            faults.append("capture parameters_digest: %s" % error)

    subjects = predicate.get("fixture_subjects")
    if not isinstance(subjects, list) or not subjects:
        faults.append("fixture_subjects must be a non-empty array")
    elif max_subjects is not None and len(subjects) > max_subjects:
        # Refuse before walking a producer-sized list. Version 1 retains its
        # historical behavior; version 2 publishes this exact schema ceiling.
        faults.append(
            "fixture_subjects lists %d components; this type reads at most %d"
            % (len(subjects), max_subjects)
        )
    else:
        seen = set()
        for entry in subjects:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                if entry["path"] in seen:
                    faults.append(
                        "path %s is listed twice; one file cannot carry two "
                        "digests, and the fixture digest is over this listing"
                        % entry["path"]
                    )
                seen.add(entry["path"])
        for index, entry in enumerate(subjects):
            label = entry.get("name") if isinstance(entry, dict) else None
            label = label or "fixture subject %d" % (index + 1)
            absent = missing(entry, FIXTURE_SUBJECT_REQUIRED)
            # An empty component is a real thing to capture, and `0` lands in
            # `missing` as though the count were absent.
            if "bytes" in absent and isinstance(entry, dict):
                if entry.get("bytes") == 0:
                    absent = [field for field in absent if field != "bytes"]
            if absent:
                faults.append("%s is missing %s" % (label, ", ".join(absent)))
                continue
            if strict_shape:
                unknown = sorted(set(entry) - set(FIXTURE_SUBJECT_REQUIRED))
                if unknown:
                    faults.append(
                        "%s carries fields this type does not define: %s"
                        % (label, ", ".join(unknown))
                    )
            if not name_check(entry["name"]):
                faults.append("fixture subject %d has no name" % (index + 1))
            if not whole_number(entry["bytes"]) or not 0 <= entry["bytes"] <= MAX_BYTES:
                faults.append(
                    "%s bytes must be a whole number of bytes up to %d, not %r"
                    % (label, MAX_BYTES, entry["bytes"])
                )
            if not path_check(entry["path"]):
                faults.append(
                    "%s path %r is not a fixture-relative path; a reader "
                    "resolving it against the fixture would land outside it"
                    % (label, entry["path"])
                )
            try:
                digests.check(entry["digest"])
            except digests.DigestError as error:
                faults.append("%s digest: %s" % (label, error))
                continue
            if not statement.covers(entry["digest"]):
                faults.append("%s is not a subject of this statement" % label)

    if faults:
        return Gate(2, "environment", False, "; ".join(faults))
    return Gate(
        2,
        "environment",
        True,
        "chain %d block %d, %s %s, %d component(s)"
        % (
            predicate["chain"]["chain_id"],
            predicate["chain"]["block_number"],
            predicate["capture"]["tool"],
            predicate["capture"]["tool_version"],
            len(predicate["fixture_subjects"]),
        ),
    )


def gate_2_environment(statement):
    """Gate 2 for the stable state-fixture/v1 vocabulary."""
    return _gate_2_environment(statement, CHAIN_FIELDS)


def section_faults(section, body, strict_shape=False, name_check=stated):
    """Gate 5 inside a section: a listed change names both of its sides."""
    faults = []
    unknown = sorted(set(body) - set(COMPONENT_KEYS))
    if unknown:
        faults.append(
            "deltas %s carries unknown keys: %s" % (section, ", ".join(unknown))
        )
    for key, entries in body.items():
        if key not in COMPONENT_KEYS:
            continue
        if not isinstance(entries, list):
            faults.append("deltas %s.%s must be an array" % (section, key))
            continue
        if key not in BOTH_SIDED:
            for index, entry in enumerate(entries):
                if not name_check(entry):
                    faults.append(
                        "deltas %s.%s[%d] identifies no component"
                        % (section, key, index)
                    )
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                faults.append(
                    "deltas %s.%s[%d] is not an object" % (section, key, index)
                )
                continue
            if strict_shape:
                unknown = sorted(set(entry) - {"baseline", "current"})
                if unknown:
                    faults.append(
                        "deltas %s.%s[%d] carries unknown fields: %s"
                        % (section, key, index, ", ".join(unknown))
                    )
            absent = [side for side in ("baseline", "current") if side not in entry]
            if absent:
                faults.append(
                    "deltas %s.%s[%d] names no %s"
                    % (section, key, index, " or ".join(absent))
                )
                continue
            for side in ("baseline", "current"):
                if not name_check(entry[side]):
                    faults.append(
                        "deltas %s.%s[%d] %s identifies no component"
                        % (section, key, index, side)
                    )
    return faults


def _gate_5_deltas(
    statement,
    require_complete_shape=False,
    strict_shape=False,
    name_check=stated,
):
    """A comparison fails when either end cannot be identified exactly.

    The absent case is a claim of its own. A first fixture carries
    `"baseline": null` with a reason, because leaving the block out would read as
    nothing having changed rather than as there being nothing to change from.

    The current side is checked whenever it is present, on either branch. That is
    the hole step 1 of this run closed on the Solidity release predicate, and
    writing this gate over the fixed shape is why the step came first.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(5, "deltas", False, "no predicate to carry a comparison")
    if "deltas" not in predicate:
        return Gate(
            5,
            "deltas",
            False,
            "predicate has no deltas block; a fixture with nothing to compare "
            "against says so with a null baseline and a reason",
        )

    deltas = predicate["deltas"]
    if not isinstance(deltas, dict):
        return Gate(5, "deltas", False, "deltas must be an object")

    faults = []
    if require_complete_shape:
        for side in ("baseline", "current"):
            if side not in deltas:
                faults.append("deltas names no %s side" % side)
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
            faults.append("deltas %s must be an object" % section)
            continue
        faults.extend(
            section_faults(
                section,
                deltas[section],
                strict_shape=strict_shape,
                name_check=name_check,
            )
        )

    if strict_shape:
        for side in ("baseline", "current"):
            value = deltas.get(side)
            if isinstance(value, dict):
                unknown = sorted(set(value) - {"name", "digest"})
                if unknown:
                    faults.append(
                        "delta %s side carries unknown fields: %s"
                        % (side, ", ".join(unknown))
                    )
        if "reason" in deltas and not isinstance(deltas["reason"], str):
            faults.append("deltas reason must be a string")

    if "current" in deltas:
        check_side(deltas.get("current"), "current", faults)
        current = deltas.get("current")
        if (
            isinstance(current, dict)
            and stated(current.get("name"))
            and not name_check(current["name"])
        ):
            faults.append("delta current side has no portable name")
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
        elif require_complete_shape and "components" in deltas:
            faults.append("deltas carries a components section against a null baseline")
        if faults:
            return Gate(5, "deltas", False, "; ".join(faults))
        named = ""
        if isinstance(deltas.get("current"), dict) and deltas["current"].get("name"):
            named = "%s, " % deltas["current"]["name"]
        return Gate(
            5, "deltas", True, "%sno baseline: %s" % (named, deltas["reason"].strip())
        )

    check_side(deltas.get("baseline"), "baseline", faults)
    baseline = deltas.get("baseline")
    if (
        isinstance(baseline, dict)
        and stated(baseline.get("name"))
        and not name_check(baseline["name"])
    ):
        faults.append("delta baseline side has no portable name")
    if "current" not in deltas:
        faults.append("a comparison against a baseline names a current side")
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


def gate_5_deltas(statement):
    """Gate 5 for the stable state-fixture/v1 vocabulary."""
    return _gate_5_deltas(statement)


def _gate_evidence(statement, evidence_classes, roots):
    """Every class counted, and nothing counted as proved without a proof.

    The three classes are not interchangeable and this is the check that says so.
    All three keys have to be there, because a class left out reads as nothing of
    that kind having been captured rather than as nobody having said. Each count
    is a non-negative whole number, which is what refuses `true` -- an integer in
    Python, and one proof-backed record if nothing looks.

    The last rule is the one this predicate would be worthless without. A
    proof-backed count above zero asserts that some evidence was checked against
    the pinned block's state root. With no state root there was nothing to check
    it against, so the count is describing work that could not have happened.

    Gate 2 does not require the root, so this rule reaches statements that gate 2
    accepts. That split is deliberate: a fixture claiming no proofs needs no root,
    and a fixture claiming proofs needs one whatever else it got right.
    """
    predicate = statement.predicate
    evidence = predicate.get("evidence") if isinstance(predicate, dict) else None
    if evidence is None:
        return Gate(
            None,
            "evidence",
            False,
            "predicate has no evidence block; a fixture that proved nothing "
            "records a zero in each class",
        )
    if not isinstance(evidence, dict):
        return Gate(None, "evidence", False, "evidence must be an object")

    faults = []
    unknown = sorted(set(evidence) - set(evidence_classes))
    if unknown:
        faults.append(
            "evidence carries classes this type does not define: %s"
            % ", ".join(unknown)
        )
    for name in evidence_classes:
        if name not in evidence:
            faults.append(
                "evidence has no %s count; a class left out reads as nothing of "
                "that kind rather than as nobody having said" % name
            )
            continue
        count = evidence[name]
        if not whole_number(count) or not 0 <= count <= MAX_COUNT:
            faults.append(
                "evidence %s must be a whole number of records from 0 to %d, "
                "not %r" % (name, MAX_COUNT, count)
            )

    if faults:
        return Gate(None, "evidence", False, "; ".join(faults))

    chain = predicate.get("chain")
    chain = chain if isinstance(chain, dict) else {}
    for evidence_class, (root_field, root_label) in roots.items():
        if evidence[evidence_class] > 0 and not hash32(chain.get(root_field)):
            faults.append(
                "evidence counts %d %s record(s) with no %s to have proved "
                "them against"
                % (evidence[evidence_class], evidence_class, root_label)
            )

    if faults:
        return Gate(None, "evidence", False, "; ".join(faults))
    return Gate(
        None,
        "evidence",
        True,
        ", ".join("%d %s" % (evidence[name], name) for name in evidence_classes),
    )


def gate_evidence(statement):
    """The v1 evidence split: only state proofs require a root."""
    return _gate_evidence(
        statement,
        EVIDENCE_CLASSES,
        {PROVED: ("state_root", "state root")},
    )


REFUSALS = {
    "reaches_network": (
        "a replay that falls back to an endpoint is not a fixture, and the "
        "endpoint is the thing a fixture exists to outlive"
    ),
    "canonical_chain_claim": (
        "a block hash and a state root pin a block, not its place in a chain "
        "nothing here re-derived"
    ),
}
"""Why each field being true is refused, so the message says the reason rather
than the rule."""


REFUSALS_V2 = dict(
    REFUSALS,
    provider_independence_claim=(
        "matching operator-chosen source labels do not establish independent "
        "providers"
    ),
)


def _gate_replay(statement, replay_required, refusals, local_only=False):
    """A closed boundary, and no claim about the canonical chain.

    Both fields are required and both must be false. `reaches_network` records
    whether replay would fall back to an endpoint; one that would is not the
    fail-closed boundary Lazarus describes, and a fixture is worth having
    precisely because it does not need the endpoint to still exist.

    `canonical_chain_claim` is the assertion that the pinned block is on the
    canonical chain. Neither tool establishes it: a block hash and a state root
    pin a block, not its place in a chain nobody re-derived. False is the honest
    value and the only one this check accepts.
    """
    predicate = statement.predicate
    replay = predicate.get("replay") if isinstance(predicate, dict) else None
    if replay is None:
        return Gate(
            None,
            "replay",
            False,
            "predicate has no replay block; the boundary and the canonical-chain "
            "claim are recorded rather than assumed",
        )
    if not isinstance(replay, dict):
        return Gate(None, "replay", False, "replay must be an object")

    faults = []
    unknown = sorted(set(replay) - set(replay_required))
    if unknown:
        faults.append(
            "replay carries fields this type does not define: %s"
            % ", ".join(unknown)
        )
    for field in replay_required:
        if field not in replay:
            faults.append("replay does not record %s" % field)
            continue
        if replay[field] is True:
            faults.append(
                "replay %s is true; %s" % (field, refusals[field])
            )
            continue
        if not exactly_false(replay, field):
            faults.append(
                "replay %s must be false, not %r; the field records a decision "
                "and %r is not in its vocabulary"
                % (field, replay[field], replay[field])
            )
    commands = predicate.get("commands") if isinstance(predicate, dict) else None
    if local_only and isinstance(commands, list) and commands:
        faults.append(
            "state-fixture/v2 replay is local-file verification only and records "
            "no executable commands"
        )

    if faults:
        return Gate(None, "replay", False, "; ".join(faults))
    detail = "replay reaches no network and claims nothing about the canonical chain"
    if "provider_independence_claim" in replay_required:
        detail += " or provider independence"
    return Gate(None, "replay", True, detail)


def gate_replay(statement):
    """The stable v1 replay boundary."""
    return _gate_replay(statement, REPLAY_REQUIRED, REFUSALS)


def gate_fields(statement, strict_shape=False):
    """Nothing outside the shape.

    Absence is left to the gate that owns each field: gate 2 for the pin, the
    capture record and the components, gate 5 for deltas, the evidence and replay
    checks for their own blocks, gate 3 for claims and commands.
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
    if strict_shape:
        faults = []
        claims = predicate.get("claims")
        if isinstance(claims, list):
            for index, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    continue
                label = "claim %d" % (index + 1)
                if "name" not in claim or not portable_name_v2(claim["name"]):
                    faults.append("%s name must contain a portable graphic" % label)
                if "reason" in claim and not isinstance(claim["reason"], str):
                    faults.append("%s reason must be a string" % label)
                if "detail" in claim and not isinstance(claim["detail"], dict):
                    faults.append("%s detail must be an object" % label)
        if faults:
            return Gate(None, "predicate-fields", False, "; ".join(faults))
    return Gate(None, "predicate-fields", True, "no fields outside the shape")


def check(statement):
    return [
        gate_2_environment(statement),
        gate_5_deltas(statement),
        gate_fields(statement),
        gate_evidence(statement),
        gate_replay(statement),
    ]


class _StateFixtureV2(object):
    """The separately registered receipt-aware predicate interface.

    The implementation shares the stable v1 shape machinery, but the URI,
    accepted fields and root-to-evidence rules are explicit here. Registering a
    distinct object prevents a v1 statement from acquiring v2 meaning through
    an implicit upgrade.
    """

    TYPE = TYPE_V2
    SUMMARY = SUMMARY_V2
    EVIDENCE_CLASSES = EVIDENCE_CLASSES_V2
    PROVED = PROVED
    RECEIPT_PROVED = RECEIPT_PROVED
    CHAIN_REQUIRED = CHAIN_REQUIRED
    CHAIN_FIELDS = CHAIN_FIELDS_V2
    REPLAY_REQUIRED = REPLAY_REQUIRED + ("provider_independence_claim",)
    PREDICATE_FIELDS = PREDICATE_FIELDS
    REQUIRED_FIELDS = REQUIRED_FIELDS
    MAX_PATH = MAX_PATH
    MAX_FIXTURE_SUBJECTS = MAX_FIXTURE_SUBJECTS_V2
    EXPECTED_RESULTS = (
        (2, "environment"),
        (5, "deltas"),
        (None, "predicate-fields"),
        (None, "evidence"),
        (None, "subject-names"),
        (None, "replay"),
    )

    @staticmethod
    def check(statement):
        found = [
            _gate_2_environment(
                statement,
                CHAIN_FIELDS_V2,
                path_check=usable_path_v2,
                max_subjects=MAX_FIXTURE_SUBJECTS_V2,
                strict_shape=True,
                name_check=portable_name_v2,
            ),
            _gate_5_deltas(
                statement,
                require_complete_shape=True,
                strict_shape=True,
                name_check=portable_name_v2,
            ),
            gate_fields(statement, strict_shape=True),
            _gate_evidence(
                statement,
                EVIDENCE_CLASSES_V2,
                {
                    PROVED: ("state_root", "state root"),
                    RECEIPT_PROVED: ("receipts_root", "receipts root"),
                },
            ),
            subject_names_v2(statement),
            _gate_replay(
                statement,
                REPLAY_REQUIRED + ("provider_independence_claim",),
                REFUSALS_V2,
                local_only=True,
            ),
        ]
        return [
            Gate(
                gate.number,
                gate.name,
                gate.passed,
                "state-fixture/v2 %s check %s"
                % (gate.name, "passed" if gate.passed else "failed"),
            )
            for gate in found
        ]


V2 = _StateFixtureV2()
