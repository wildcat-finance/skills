"""Read a dataset release on disk into a statement.

A capture reads what is already there rather than producing it, so what ends up
in the statement is what the release actually contains. Nothing here reaches a
network, and nothing here guesses.

Three things the caller has to supply, because the files cannot answer them:

- **Coverage.** A directory of records does not say which interval it was meant
  to describe, so it cannot say where it falls short of one. Both bounds and
  every gap come from the caller.
- **Inputs.** What a release was derived from is not recoverable from the
  release. An input is named with a digest, or recorded absent with a reason.
- **Record counts, except for line-delimited JSON.** One record per line is
  unambiguous, so `.jsonl` and `.ndjson` are counted here. Every other format
  needs the count stated, and a file whose count is neither derivable nor stated
  is refused rather than guessed at.
- **The producer.** Ariadne read the release; it did not produce it. The tool, its
  version and the argv that ran all come from the caller, and none of them has a
  default. A default would put this tool's own name in the field gate 2 reads as
  the thing that made the files.

Record-level deltas are never computed here. Telling which records changed
between two releases needs a record identity this tool does not have, and
inventing one would put a difference in the statement that nobody established.
With `--previous`, both sides are identified and the comparison records no
differences, and a skipped claim says why.
"""

import json
import os
import tempfile

from .. import digests
from ..predicates import dataset as predicate
from . import tree

MAX_RELEASE_FILES = tree.MAX_FILES
"""Kept as a name because the tests and the document both cite it. The cap itself
lives with the walk, which is the code that enforces it."""

LINE_DELIMITED = (".jsonl", ".ndjson")
"""Formats where one record per line is the format, not an assumption."""

REFUSED_NAMES = tree.REFUSED_NAMES

CaptureError = tree.CaptureError
"""The same class the walk raises.

It used to be a separate class defined here, and `capture/foundry.py` still defines
its own, so a caller catching one does not catch the other. Sharing it means a
caller can catch `CaptureError` from either capture that walks a tree.
"""

confined = tree.confined


def inside(root, path, what):
    return tree.inside(root, path, what, "release")


def files(root):
    """Every file in the release, as (relative path, absolute path), sorted.

    The walk is shared, because it was written twice before this and the second
    copy of a path helper in this package was where a traversal defect had already
    been found.
    """
    return tree.files(root, "release")


def line_count(path):
    """Non-empty lines in a file, read in blocks rather than whole.

    A release file is larger than a build artefact, sometimes by orders of
    magnitude, so nothing here holds one in memory.
    """
    total = 0
    partial = False
    try:
        with open(path, "rb") as handle:
            for block in iter(lambda: handle.read(65536), b""):
                total += block.count(b"\n")
                partial = not block.endswith(b"\n")
    except OSError as error:
        raise CaptureError("cannot read %s: %s" % (path, error))
    if partial:
        # A final record with no trailing newline is still a record.
        total += 1
    return total


def unused_counts(stated, entries):
    """Stated counts naming a file the release does not hold.

    A typo in `--record-count events.jsnol=5` would otherwise pass unremarked, and
    the count the caller believed they supplied would not be the one in the
    statement.
    """
    return sorted(set(stated) - {relative for relative, _ in entries})


def record_count(relative, absolute, stated):
    """The count for one file: stated by the caller, or derived where it can be."""
    if relative in stated:
        return stated[relative]
    if os.path.splitext(relative)[1].lower() in LINE_DELIMITED:
        return line_count(absolute)
    raise CaptureError(
        "%s is not line-delimited JSON, so its record count cannot be derived; "
        "state it with --record-count %s=<n>" % (relative, relative)
    )


def subjects(root, stated_counts):
    """One entry per released file, digested and counted."""
    entries = files(root)
    stray = unused_counts(stated_counts, entries)
    if stray:
        raise CaptureError(
            "--record-count names %s, which the release does not hold; check the "
            "path" % ", ".join(stray)
        )
    out = []
    for relative, absolute in entries:
        out.append(
            {
                "name": relative,
                "path": relative,
                "digest": digests.of_file(absolute),
                "record_count": record_count(relative, absolute, stated_counts),
            }
        )
    return out


def bundle(entries):
    """One digest over a whole release.

    Both sides of a delta name this rather than one file's digest. With more than
    one file, picking the first would name an artefact the comparison is only
    partly about.
    """
    return digests.of_bytes(
        json.dumps(
            [[entry["name"], entry["digest"]] for entry in sorted(entries, key=lambda e: e["name"])],
            sort_keys=True,
        ).encode("utf-8")
    )


def parameters_digest(parameters):
    """A digest over the producer's parameters, canonically serialised.

    Sorted keys, so the same parameters give the same digest whatever order they
    arrived in.
    """
    return digests.of_bytes(
        json.dumps(dict(parameters or {}), sort_keys=True).encode("utf-8")
    )


def mapping(value, what):
    """A caller-supplied mapping, or a refusal naming the flag.

    A library caller can pass a list of pairs where a mapping belongs, and the
    `dict()` that used to be here raised a bare ValueError from inside the capture.
    A capture reports what is wrong with its arguments the same way it reports what
    is wrong with a release.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    raise CaptureError("%s must be a mapping, got %s" % (what, type(value).__name__))


def counts(value):
    """The stated record counts, each a whole number of records."""
    found = mapping(value, "--record-count")
    for path, count in sorted(found.items()):
        if not predicate.whole_number(count) or count < 0:
            raise CaptureError(
                "--record-count %s must be a whole number of records, got %r"
                % (path, count)
            )
    return found


def entries_of(value, what):
    """A caller-supplied list of objects, or a refusal naming the flag."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise CaptureError("%s must be a list, got %s" % (what, type(value).__name__))
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise CaptureError(
                "%s entry %d must be an object, got %s"
                % (what, index + 1, type(entry).__name__)
            )
    return list(value)


def coverage(dimension, start, end, gaps):
    """The coverage block, with the gaps the caller recorded.

    An empty gap list is written rather than omitted. The predicate refuses an
    absent `gaps` key on purpose, because that is the difference between a
    producer who looked and one who did not.
    """
    if not dimension:
        raise CaptureError("a coverage dimension is required")
    for name, value in (("start", start), ("end", end)):
        if not predicate.whole_number(value):
            raise CaptureError("coverage %s must be a whole number, got %r" % (name, value))
    if start > end:
        raise CaptureError("coverage starts at %d and ends at %d" % (start, end))
    out = {"dimension": dimension, "start": start, "end": end, "gaps": []}
    for entry in entries_of(gaps, "--gap"):
        for field in ("start", "end", "reason"):
            if field not in entry:
                raise CaptureError("a gap needs %s" % field)
        if not predicate.whole_number(entry["start"]) or not predicate.whole_number(entry["end"]):
            raise CaptureError("gap bounds must be whole numbers")
        if entry["start"] > entry["end"]:
            raise CaptureError(
                "a gap starts at %d and ends at %d" % (entry["start"], entry["end"])
            )
        if entry["start"] < start or entry["end"] > end:
            raise CaptureError(
                "a gap runs %d to %d, outside the coverage %d to %d"
                % (entry["start"], entry["end"], start, end)
            )
        out["gaps"].append(
            {"start": entry["start"], "end": entry["end"], "reason": entry["reason"]}
        )
    return out


def claim(name, subject, disposition, reason=None, detail=None):
    out = {"name": name, "subject": subject, "disposition": disposition}
    if reason:
        out["reason"] = reason
    if detail:
        out["detail"] = detail
    return out


def capture(
    release,
    name,
    coverage_dimension,
    coverage_start,
    coverage_end,
    producer_tool,
    producer_version,
    producer_command,
    gaps=None,
    inputs=None,
    parameters=None,
    record_counts=None,
    previous=None,
    previous_name=None,
    first_release_reason=None,
):
    """A dataset release statement, read from a release directory on disk."""
    for label, value in (
        ("--producer-tool", producer_tool),
        ("--producer-version", producer_version),
    ):
        if not isinstance(value, str) or not value.strip():
            raise CaptureError(
                "%s is required; gate 2 reads it as what produced these files, and "
                "this tool read them rather than producing them" % label
            )
    if not producer_command or not all(
        isinstance(word, str) and word for word in producer_command
    ):
        raise CaptureError(
            "--producer-command is required, as an argv nobody has to guess at"
        )
    if not isinstance(name, str) or not name.strip():
        raise CaptureError(
            "--name is required; it identifies the current side of the comparison "
            "and names the release among the statement's subjects"
        )
    stated = counts(record_counts)
    inputs = entries_of(inputs, "--input")
    root = confined(release, "release")
    entries = subjects(root, stated)
    current = bundle(entries)

    if previous:
        if not previous_name:
            raise CaptureError("--previous needs --previous-name to identify it")
        previous_root = confined(previous, "previous release")
        if previous_root == root:
            raise CaptureError(
                "--previous is the same directory as --release; a comparison "
                "against itself records nothing"
            )
        baseline = {
            "name": previous_name,
            "digest": bundle(subjects(previous_root, stated)),
        }
        deltas = {"baseline": baseline, "current": {"name": name, "digest": current}}
    else:
        if not isinstance(first_release_reason, str) or not first_release_reason.strip():
            raise CaptureError(
                "a release with no --previous needs --first-release-reason; a null "
                "baseline carries the reason there is nothing to compare against"
            )
        deltas = {
            "baseline": None,
            "current": {"name": name, "digest": current},
            "reason": first_release_reason,
        }

    claims = [
        claim(
            "digest and record count read from the released file",
            entry["digest"],
            "passed",
            detail="%s, %d record(s)" % (entry["path"], entry["record_count"]),
        )
        for entry in entries
    ]
    if previous:
        claims.append(
            claim(
                "record-level comparison against the baseline",
                current,
                "skipped",
                reason=(
                    "telling which records changed needs a record identity this "
                    "capture does not have, so both sides are identified and no "
                    "differences are recorded"
                ),
            )
        )

    body = {
        "producer": {
            "tool": producer_tool,
            "tool_version": producer_version,
            "command": list(producer_command),
            "parameters_digest": parameters_digest(mapping(parameters, "--parameter")),
        },
        "inputs": inputs,
        "dataset_subjects": entries,
        "coverage": coverage(coverage_dimension, coverage_start, coverage_end, gaps),
        "deltas": deltas,
        "claims": claims,
        "commands": [],
    }

    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": entry["name"], "digest": entry["digest"]} for entry in entries]
        + [{"name": name, "digest": current}],
        "predicateType": predicate.TYPE,
        "predicate": body,
    }


def write(path, body):
    """Write a statement so a reader never sees half of one.

    A capture that died mid-write used to leave a truncated file where the next
    run would read it as complete. The temporary file lands in the same directory
    so the replace is on one filesystem.
    """
    directory = os.path.dirname(os.path.abspath(path)) or "."
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        dir=directory,
        prefix=".ariadne-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise
