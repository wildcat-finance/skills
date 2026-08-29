"""Read a Foundry build into a Solidity release statement.

Everything the predicate needs about the build is already on disk. `forge`
writes solc's full standard-JSON input and output to `out/build-info/*.json`,
which carries the compiler version, the optimiser settings, the EVM target and
the source list, and one artefact per contract to `out/<file>.sol/<Name>.json`,
which carries the ABI, both bytecodes, the method identifiers and the storage
layout.

What capture will not do is decide anything it did not read. It does not run
the tests and then report on them: a test result arrives as a stated
disposition, and the default is `skipped` with a reason saying nothing was
supplied. It reaches no chain, so a deployment it records says nothing
confirmed it. Both of those are the spec's gate 3 in the one place a capture
tool is most tempted to fill a gap with an assumption.
"""

import json
import os

from .. import core_predicate
from .. import deltas as deltas_module
from .. import digests, safejson, scrub
from ..predicates import solidity_release

BUILD_INFO = os.path.join("out", "build-info")
OUT = "out"

MAX_ARTEFACT_BYTES = 64 * 1024 * 1024
"""Build artefacts are the tool's own output rather than a stranger's, but a
cap keeps a runaway file from being read into memory whole."""

MAX_ARTEFACT_DEPTH = 4096
"""An artefact carries a syntax tree, which nests as deeply as the source did.
The fixture reaches 19; a real contract with long chains of expressions goes
much further, and a cap that refused those would be refusing ordinary builds."""


class CaptureError(ValueError):
    """A project that cannot be captured, with the reason a caller can act on."""


def confined(path, what):
    """Resolve a project directory, refusing anything that leaves itself.

    `realpath` collapses `..` and follows symlinks, so comparing the resolved
    output directory against the resolved project is what catches an `out`
    pointing somewhere else entirely.
    """
    if not path:
        raise CaptureError("%s is required" % what)
    resolved = os.path.realpath(path)
    if not os.path.isdir(resolved):
        raise CaptureError("%s %s is not a directory" % (what, path))
    out = os.path.realpath(os.path.join(resolved, OUT))
    if not os.path.isdir(out):
        raise CaptureError(
            "%s %s has no out/ directory; run forge build first" % (what, path)
        )
    try:
        shared = os.path.commonpath([resolved, out])
    except ValueError as error:
        # Different drives on Windows, or one of the two not absolute. Either
        # way the containment cannot be established, so it is not established.
        raise CaptureError("%s %s: cannot place out/ inside it (%s)" % (what, path, error))
    if shared != resolved:
        raise CaptureError(
            "%s %s has an out/ that resolves outside it" % (what, path)
        )
    return resolved


def read_json(path):
    size = os.path.getsize(path)
    if size > MAX_ARTEFACT_BYTES:
        raise CaptureError("%s is %d bytes, over the artefact cap" % (path, size))
    with open(path, "rb") as handle:
        data = handle.read()
    try:
        return safejson.loads(
            data, max_bytes=MAX_ARTEFACT_BYTES, max_depth=MAX_ARTEFACT_DEPTH
        )
    except safejson.InputError as error:
        raise CaptureError("%s: %s" % (path, error))


def build_info(project):
    """The newest build-info file, and the reason when there is none."""
    directory = os.path.join(project, BUILD_INFO)
    if not os.path.isdir(directory):
        raise CaptureError(
            "no out/build-info in %s; set build_info = true in foundry.toml "
            "and build again" % project
        )
    found = sorted(
        name for name in os.listdir(directory) if name.endswith(".json")
    )
    if not found:
        raise CaptureError(
            "out/build-info in %s holds no build; set build_info = true in "
            "foundry.toml and build again" % project
        )
    newest = max(
        found, key=lambda name: os.path.getmtime(os.path.join(directory, name))
    )
    return read_json(os.path.join(directory, newest))


def artefacts(project):
    """Every compiled contract: (source file, contract name, artefact)."""
    out = os.path.join(project, OUT)
    found = []
    for entry in sorted(os.listdir(out)):
        directory = os.path.join(out, entry)
        if not entry.endswith(".sol") or not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(directory, name)
            if os.path.islink(path):
                raise CaptureError("%s is a symlink" % path)
            found.append((entry, name[: -len(".json")], read_json(path)))
    return found


def bytecode(artefact, key):
    body = artefact.get(key) or {}
    return body.get("object") or ""


def release_subjects(project, wanted=None):
    """One entry per compiled contract with real bytecode.

    An interface or an abstract contract compiles to nothing, and a release
    subject with no creation bytecode would be a claim about an artefact that
    does not exist.
    """
    subjects = []
    for source, name, artefact in artefacts(project):
        if wanted and name not in wanted:
            continue
        creation = bytecode(artefact, "bytecode")
        runtime = bytecode(artefact, "deployedBytecode")
        if not creation or creation == "0x":
            continue
        subjects.append(
            {
                "name": name,
                "source_path": source_path(artefact, source),
                "creation_digest": digests.of_bytes(creation.encode("ascii")),
                "runtime_digest": digests.of_bytes(runtime.encode("ascii")),
                "abi_digest": digests.of_bytes(
                    json.dumps(artefact.get("abi") or [], sort_keys=True).encode(
                        "utf-8"
                    )
                ),
                "_artefact": artefact,
            }
        )
    if wanted:
        found = {entry["name"] for entry in subjects}
        for name in wanted:
            if name not in found:
                raise CaptureError(
                    "%s has no compiled contract named %s" % (project, name)
                )
    if not subjects:
        raise CaptureError("%s compiled no contract with bytecode" % project)
    return subjects


def source_path(artefact, fallback):
    target = (artefact.get("metadata") or {}).get("settings", {}).get(
        "compilationTarget"
    ) or {}
    for path in target:
        return path
    return fallback


def environment(info):
    """The build record gate 2 wants, from solc's own input."""
    settings = (info.get("input") or {}).get("settings") or {}
    optimizer = settings.get("optimizer") or {}
    if "enabled" not in optimizer or "runs" not in optimizer:
        raise CaptureError(
            "build-info records no optimiser settings; a build description "
            "without them is not recoverable"
        )
    version = info.get("solcLongVersion") or info.get("solcVersion")
    if not version:
        raise CaptureError("build-info records no compiler version")
    return {
        "compiler": "solc",
        "compiler_version": version,
        "optimizer": {
            "enabled": bool(optimizer["enabled"]),
            "runs": int(optimizer["runs"]),
        },
        "evm_version": settings.get("evmVersion") or "unset",
        "via_ir": bool(settings.get("viaIR", False)),
    }


def lock_digest(project):
    """A digest over whatever pins the dependencies, or over the sources.

    A project with no lock file still has to answer gate 2, so the source tree
    stands in and the statement says which it was through the file name.
    """
    for name in ("foundry.lock", "soldeer.lock", "package-lock.json", "yarn.lock"):
        path = os.path.join(project, name)
        if os.path.isfile(path):
            return name, digests.of_file(path)
    source = os.path.join(project, "src")
    if os.path.isdir(source):
        return "src/", digests.of_tree(source)
    return "foundry.toml", digests.of_file(os.path.join(project, "foundry.toml"))


def layout(artefact):
    return (artefact.get("storageLayout") or {}).get("storage") or []


def bundle(subjects):
    """One digest over a whole build's output.

    Both sides of a delta name this rather than one contract's bytecode. With
    more than one contract, picking the first would name an artefact the
    comparison is only partly about.
    """
    return digests.of_bytes(
        json.dumps(
            [
                [entry["name"], entry["creation_digest"], entry["runtime_digest"]]
                for entry in sorted(subjects, key=lambda e: e["name"])
            ],
            sort_keys=True,
        ).encode("utf-8")
    )


def compare(current, previous):
    """The deltas between two capture results, by contract name.

    A contract that was in the previous build and is gone from this one is a
    change nobody would find in an ABI diff, because there is no ABI left to
    diff. It goes in its own section rather than nowhere.
    """
    old = {entry["name"]: entry["_artefact"] for entry in previous}
    new = {entry["name"] for entry in current}
    contracts = {
        "added": sorted(new - set(old)),
        "removed": sorted(set(old) - new),
    }
    abi = {"added": [], "removed": [], "changed": []}
    identifiers = {"added": [], "removed": [], "moved": []}
    storage = {"added": [], "removed": [], "moved": [], "retyped": []}

    for entry in current:
        before = old.get(entry["name"])
        if before is None:
            continue
        after = entry["_artefact"]
        merge(abi, deltas_module.abi_delta(before.get("abi"), after.get("abi")))
        merge(
            identifiers,
            deltas_module.method_identifier_delta(
                before.get("methodIdentifiers"), after.get("methodIdentifiers")
            ),
        )
        merge(storage, deltas_module.storage_delta(layout(before), layout(after)))
    return {
        "contracts": contracts,
        "abi": abi,
        "method_identifiers": identifiers,
        "storage": storage,
    }


def merge(into, found):
    for key, value in found.items():
        into.setdefault(key, [])
        into[key].extend(value)


def claim(name, subject, disposition, reason=None, detail=None):
    out = {"name": name, "subject": subject, "disposition": disposition}
    if reason:
        out["reason"] = reason
    if detail:
        out["detail"] = detail
    return out


def capture(
    project,
    repository,
    commit,
    previous=None,
    previous_name=None,
    contracts=None,
    build_command=None,
    tests=None,
    fuzz=None,
    audits=None,
    deployments=None,
    first_release_reason=None,
):
    """A Solidity release statement, read from a Foundry project on disk."""
    project = confined(project, "--project")
    info = build_info(project)
    subjects = release_subjects(project, contracts)

    build = environment(info)
    lock_source, lock = lock_digest(project)
    command = list(build_command or ["forge", "build"])
    redacted = scrub.redacted(command)
    build["dependency_lock_digest"] = lock
    build["dependency_lock_source"] = lock_source
    build["command"] = scrub.argv(command)

    statement_subjects = []
    predicate_subjects = []
    build_output = bundle(subjects)
    for entry in subjects:
        statement_subjects.append(
            {"name": "%s (creation)" % entry["name"], "digest": entry["creation_digest"]}
        )
        statement_subjects.append(
            {"name": "%s (runtime)" % entry["name"], "digest": entry["runtime_digest"]}
        )
        predicate_subjects.append(
            {k: v for k, v in entry.items() if not k.startswith("_")}
        )
    statement_subjects.append(
        {"name": "release bundle (every compiled artefact)", "digest": build_output}
    )

    if previous:
        previous_project = confined(previous, "--previous")
        before = release_subjects(previous_project, contracts)
        found = compare(subjects, before)
        deltas = {
            "baseline": {
                "name": previous_name or os.path.basename(previous_project),
                "digest": bundle(before),
            },
            "current": {
                "name": os.path.basename(project),
                "digest": build_output,
            },
        }
        deltas.update(found)
    else:
        deltas = {
            "baseline": None,
            "reason": first_release_reason
            or "no previous build was supplied to capture, so nothing was compared",
        }

    primary = subjects[0]["runtime_digest"]
    claims = [
        claim(
            "compiled artefacts read from the build",
            primary,
            "passed",
            detail={
                "contracts": len(subjects),
                "dependency_lock": lock_source,
                "build_info_sources": sorted(
                    (info.get("input") or {}).get("sources") or {}
                ),
            },
        ),
        stated_claim("unit tests", primary, tests, "no test result was supplied to capture"),
        stated_claim(
            "fuzz campaign", primary, fuzz, "no fuzz result was supplied to capture"
        ),
    ]

    commands = [
        {
            "name": "build",
            "argv": build["command"],
            "determinism": "exact",
            "output_digest": build_output,
            "detail": {"redacted_arguments": redacted},
        }
    ]

    predicate = {
        "source": {
            "repository": scrub.credentials(repository),
            "commit": commit,
            "tree_digest": digests.of_tree(os.path.join(project, "src"))
            if os.path.isdir(os.path.join(project, "src"))
            else digests.of_tree(project),
        },
        "build": build,
        "release_subjects": predicate_subjects,
        "deltas": deltas,
        "claims": claims,
        "commands": commands,
    }
    if audits:
        predicate["audits"] = list(audits)
    if deployments:
        predicate["deployments"] = [
            dict(entry, confirmed_against_chain=False) for entry in deployments
        ]

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": statement_subjects,
        "predicateType": solidity_release.TYPE,
        "predicate": predicate,
    }


def stated_claim(name, subject, stated, default_reason):
    """A claim from what the caller stated, or a recorded absence.

    The default is the point. A capture tool that wrote `passed` for a run it
    never saw would be the thing this project exists to replace.
    """
    if not stated:
        return claim(name, subject, "skipped", default_reason)
    disposition, _, reason = stated.partition(":")
    disposition = disposition.strip()
    reason = reason.strip()
    if disposition not in core_predicate.DISPOSITIONS:
        # Refusing here beats writing a statement whose own verifier will
        # reject it, which would send somebody looking for the fault in the
        # gates rather than in the argument they typed.
        raise CaptureError(
            "%r is not a disposition; use one of %s"
            % (disposition, ", ".join(core_predicate.DISPOSITIONS))
        )
    if disposition != "passed" and not reason:
        reason = "no reason was supplied to capture"
    return claim(name, subject, disposition, reason or None)
