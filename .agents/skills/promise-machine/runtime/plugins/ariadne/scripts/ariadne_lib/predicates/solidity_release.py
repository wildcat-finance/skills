"""The Solidity release predicate: the first shape on the artefact-neutral core.

Its subject is compiled bytecode. What it adds to the core block is the part
that makes a contract release checkable rather than merely signed: which source
produced the bytecode, under which compiler and settings, what the interface and
storage did against the release before it, what the audits covered, and where
the thing was deployed.

Two gates belong here. Gate 2 holds that the environment is recoverable, which
is why a compiler version on its own fails: without the optimiser settings, the
EVM target and the dependency lock nobody gets the same bytes back. Gate 5 holds
that a comparison names both sides, so a delta against a release that cannot be
identified fails rather than quietly reporting no changes.

The other absence rule is the spec's gate 3 applied here: a first release
records `"baseline": null` with a reason rather than leaving the block out, and
a deployment says whether anything confirmed it against a chain. This build
reaches no network, so every deployment it writes says nothing did.
"""

import re

from .. import deltas as deltas_module
from .. import digests
from ..core_predicate import check_side, missing
from ..gates import Gate

REVISION = re.compile(r"^[0-9a-f]{40}$|^[0-9a-f]{64}$")
"""A git object id, sha1 or sha256. A branch or a tag is a moving pointer, and
gate 1 exists to refuse exactly that kind of name."""

TYPE = "https://ariadne.wildcat.finance/solidity-release/v1"
SUMMARY = "a Solidity release: source, build, bytecode, deltas, audits, deployments"
EXPECTED_RESULTS = (
    (2, "environment"),
    (5, "deltas"),
    (None, "predicate-fields"),
    (None, "audits"),
    (None, "deployments"),
)

SOURCE_REQUIRED = ("repository", "commit", "tree_digest")
BUILD_REQUIRED = (
    "compiler",
    "compiler_version",
    "optimizer",
    "evm_version",
    "dependency_lock_digest",
    "command",
)
OPTIMIZER_REQUIRED = ("enabled", "runs")
RELEASE_SUBJECT_REQUIRED = ("name", "source_path", "creation_digest", "runtime_digest")
DELTA_SECTIONS = ("contracts", "abi", "method_identifiers", "storage")
DEPLOYMENT_REQUIRED = ("chain_id", "address", "creation_tx", "confirmed_against_chain")
AUDIT_REQUIRED = ("report_digest", "covered_revision", "scope")

PREDICATE_FIELDS = (
    "source",
    "build",
    "release_subjects",
    "deltas",
    "audits",
    "deployments",
    "claims",
    "commands",
)
"""Everything this predicate carries, the last two inherited from the core."""

REQUIRED_FIELDS = (
    "source",
    "build",
    "release_subjects",
    "deltas",
    "claims",
    "commands",
)
"""What a statement of this type cannot leave out. `audits` and `deployments`
are absent when there are none, and a release that was audited records the audit
rather than the absence of one."""


def gate_2_environment(statement):
    """A bare tool version is not a build description.

    Recoverable means somebody else can get the same bytes back. That takes the
    compiler and its version, the optimiser settings, the EVM target, a digest
    over the dependency lock and the command that was run, plus the commit and
    tree the sources came from.
    """
    predicate = statement.predicate
    if not isinstance(predicate, dict):
        return Gate(2, "environment", False, "no predicate to describe a build")

    faults = []

    source = predicate.get("source")
    absent = missing(source, SOURCE_REQUIRED)
    if absent:
        faults.append("source is missing %s" % ", ".join(absent))
    elif not isinstance(source.get("commit"), str):
        faults.append("source commit must be a string")
    elif not REVISION.fullmatch(source["commit"]):
        faults.append(
            "source commit %r is not a git object id; a branch or a tag names "
            "something that moves" % source["commit"]
        )
    else:
        try:
            digests.check(source["tree_digest"])
        except digests.DigestError as error:
            faults.append("source tree_digest: %s" % error)

    build = predicate.get("build")
    absent = missing(build, BUILD_REQUIRED)
    if absent:
        faults.append("build is missing %s" % ", ".join(absent))
    else:
        for field in ("compiler", "compiler_version", "evm_version"):
            if not isinstance(build.get(field), str):
                faults.append("build %s must be a string" % field)
        optimizer = build.get("optimizer")
        if not isinstance(optimizer, dict):
            faults.append("build optimizer must be an object")
        else:
            gaps = [f for f in OPTIMIZER_REQUIRED if optimizer.get(f) is None]
            if gaps:
                faults.append("build optimizer is missing %s" % ", ".join(gaps))
        command = build.get("command")
        if not isinstance(command, list) or not all(
            isinstance(word, str) for word in command
        ):
            faults.append("build command must be an argv of strings")
        else:
            commands = predicate.get("commands")
            if isinstance(commands, list) and commands and not any(
                isinstance(entry, dict)
                and entry.get("determinism") == "exact"
                and entry.get("argv") == command
                for entry in commands
            ):
                faults.append(
                    "recorded exact commands do not match the build command"
                )
        try:
            digests.check(build["dependency_lock_digest"])
        except digests.DigestError as error:
            faults.append("build dependency_lock_digest: %s" % error)

    subjects = predicate.get("release_subjects")
    if not isinstance(subjects, list) or not subjects:
        faults.append("release_subjects must be a non-empty array")
    else:
        for index, entry in enumerate(subjects):
            label = entry.get("name") if isinstance(entry, dict) else None
            label = label or "release subject %d" % (index + 1)
            absent = missing(entry, RELEASE_SUBJECT_REQUIRED)
            if absent:
                faults.append("%s is missing %s" % (label, ", ".join(absent)))
                continue
            for field in ("creation_digest", "runtime_digest"):
                try:
                    digests.check(entry[field])
                except digests.DigestError as error:
                    faults.append("%s %s: %s" % (label, field, error))
                    continue
                if not statement.covers(entry[field]):
                    faults.append(
                        "%s %s is not a subject of this statement" % (label, field)
                    )

    if faults:
        return Gate(2, "environment", False, "; ".join(faults))
    return Gate(
        2,
        "environment",
        True,
        "%s %s, optimiser %s, evm %s, %d release subject(s)"
        % (
            predicate["build"]["compiler"],
            predicate["build"]["compiler_version"],
            "on" if predicate["build"]["optimizer"].get("enabled") else "off",
            predicate["build"]["evm_version"],
            len(predicate["release_subjects"]),
        ),
    )


BOTH_SIDED = ("changed", "moved", "retyped")
"""Sections whose entries describe a change rather than a name, so each entry
carries what it was and what it became."""


def section_faults(section, body):
    """Gate 5 inside a section: a listed change names both of its sides."""
    faults = []
    for key, entries in body.items():
        if not isinstance(entries, list):
            faults.append("deltas %s.%s must be an array" % (section, key))
            continue
        if key not in BOTH_SIDED:
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
    return faults


def gate_5_deltas(statement):
    """A comparison fails when either end cannot be identified exactly.

    The absent case is a claim of its own. A first release carries
    `"baseline": null` with a reason, because leaving the block out would read
    as nothing having changed rather than as there being nothing to change
    from.
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
    unknown = sorted(set(deltas) - set(DELTA_SECTIONS) - {"baseline", "current", "reason"})
    if unknown:
        faults.append("deltas carries unknown sections: %s" % ", ".join(unknown))
    for section in DELTA_SECTIONS:
        if section not in deltas:
            continue
        if not isinstance(deltas[section], dict):
            # A section that is not an object reads as empty to `empty()`, so
            # without this a delta of "abi": "everything changed" would pass
            # and report no differences.
            faults.append("deltas %s must be an object" % section)
            continue
        faults.extend(section_faults(section, deltas[section]))

    # A current side that is present gets checked whether or not there is a
    # baseline. This ran only after the null-baseline branch returned, so a first
    # release could carry a current side with no name, no digest, or a digest the
    # statement does not cover, and verify clean. Recorded as S4-R6-06 by the
    # dataset run, which fixed the same shape in its own predicate and left this one
    # to the run that needed it.
    #
    # Presence is not required here. A first release omits the side entirely, which
    # is what `capture` writes and what the shipped fixture holds, and demanding one
    # would change what a released statement of this type has to say. The hole was
    # a side that was there and unexamined, not a side that was absent.
    if "current" in deltas:
        check_side(deltas.get("current"), "current", faults)
        if not faults and not statement.covers(deltas["current"]["digest"]):
            # The current side is meant to be this release. Left unchecked, a
            # statement could compare two artefacts it does not cover and present
            # the result as its own history.
            faults.append(
                "delta current side is not a subject of this statement"
            )

    if deltas.get("baseline") is None:
        reason = deltas.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            faults.append("a null baseline needs a reason")
        if content:
            faults.append(
                "deltas record %s against a null baseline"
                % ", ".join(sorted(content))
            )
        if faults:
            return Gate(5, "deltas", False, "; ".join(faults))
        named = ""
        if isinstance(deltas.get("current"), dict) and deltas["current"].get("name"):
            named = "%s, " % deltas["current"]["name"]
        return Gate(
            5, "deltas", True, "%sno baseline: %s" % (named, deltas["reason"].strip())
        )

    check_side(deltas.get("baseline"), "baseline", faults)
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


def gate_deployments(statement):
    """Deployments say whether anything checked them against a chain.

    Not one of the seven. It is the spec's gate 3 applied to the one field this
    predicate could most easily imply: an address printed with no note reads as
    a confirmed deployment, and nothing here has ever spoken to a node.
    """
    predicate = statement.predicate
    deployments = predicate.get("deployments") if isinstance(predicate, dict) else None
    if deployments is None:
        return Gate(None, "deployments", True, "no deployments recorded")
    if not isinstance(deployments, list):
        return Gate(None, "deployments", False, "deployments must be an array")

    faults = []
    unconfirmed = 0
    for index, entry in enumerate(deployments):
        label = "deployment %d" % (index + 1)
        absent = missing(entry, DEPLOYMENT_REQUIRED)
        # `confirmed_against_chain` is legitimately false, which `missing`
        # would otherwise read as absent, so check it separately.
        absent = [f for f in absent if f != "confirmed_against_chain"]
        if "confirmed_against_chain" not in (entry or {}):
            absent.append("confirmed_against_chain")
        if absent:
            faults.append("%s is missing %s" % (label, ", ".join(absent)))
            continue
        # A chain id identifies a chain, so it has to be a number. `" "` and
        # `"null"` and `true` all satisfied a presence test and named no chain.
        chain_id = entry["chain_id"]
        if not isinstance(chain_id, int) or isinstance(chain_id, bool) or chain_id < 1:
            faults.append(
                "%s chain_id must be a whole number, not %r" % (label, chain_id)
            )
            continue
        # The field records a decision somebody made, so only the two booleans are
        # in its vocabulary. Anything else was read for truthiness: `"null"` and
        # `" "` are truthy, so a deployment carrying either was counted as
        # confirmed and the line below told a reader every deployment had been
        # checked against a chain. Nothing here has ever spoken to a node.
        confirmed = entry["confirmed_against_chain"]
        if confirmed is not True and confirmed is not False:
            faults.append(
                "%s confirmed_against_chain must be true or false, not %r; the "
                "field records a decision and anything else is read as a yes"
                % (label, confirmed)
            )
            continue
        if not confirmed:
            unconfirmed += 1

    if faults:
        return Gate(None, "deployments", False, "; ".join(faults))
    return Gate(
        None,
        "deployments",
        True,
        "%d deployment(s), %d unconfirmed against a chain"
        % (len(deployments), unconfirmed),
    )


def gate_audits(statement):
    """An audit names the revision it covered, or it says nothing useful.

    A report linked beside a release, with no revision, is the gap the spec
    opens with: it does not establish that the audit covered the released
    commit.
    """
    predicate = statement.predicate
    audits = predicate.get("audits") if isinstance(predicate, dict) else None
    if audits is None:
        return Gate(None, "audits", True, "no audits recorded")
    if not isinstance(audits, list):
        return Gate(None, "audits", False, "audits must be an array")

    released = (predicate.get("source") or {}).get("commit")
    faults = []
    elsewhere = 0
    for index, entry in enumerate(audits):
        label = "audit %d" % (index + 1)
        absent = missing(entry, AUDIT_REQUIRED)
        if absent:
            faults.append("%s is missing %s" % (label, ", ".join(absent)))
            continue
        try:
            digests.check(entry["report_digest"])
        except digests.DigestError as error:
            faults.append("%s report_digest: %s" % (label, error))
        revision = entry["covered_revision"]
        if not isinstance(revision, str) or not REVISION.fullmatch(revision):
            faults.append(
                "%s covered_revision %r is not a git object id; an audit that "
                "covered a branch covered whatever it pointed at that day"
                % (label, revision)
            )
        elif released and revision != released:
            # Not a failure. An audit of an earlier revision is a normal thing
            # to have and a normal thing to say, and the reader is the one who
            # decides what it is worth.
            elsewhere += 1

    if faults:
        return Gate(None, "audits", False, "; ".join(faults))
    detail = "%d audit(s), each naming the revision it covered" % len(audits)
    if elsewhere:
        detail += "; %d covering a revision other than the released commit" % elsewhere
    return Gate(None, "audits", True, detail)


def gate_fields(statement):
    """Nothing outside the shape.

    Absence is left to the gate that owns each field: gate 2 for source and
    build, gate 5 for deltas, gate 3 for claims and commands. Reporting a
    missing `claims` here as well would tell a reader that two separate things
    went wrong.
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
        gate_audits(statement),
        gate_deployments(statement),
    ]
