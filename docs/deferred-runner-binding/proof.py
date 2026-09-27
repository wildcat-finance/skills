#!/usr/bin/env python3
"""Resolve the pending conformance cells of the skills#1944 design record.

Run from the repository root with the exact resolver a cell names:

    python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding \
        --criterion <criterion> \
        --report .hexaemeron/reports/creating-step-binding-<criterion>.json

The step that builds a criterion's product adds its handler to HANDLERS.
Until then the criterion refuses with a named reason and writes nothing. A
handler returns one typed value; this script wraps it in one closed
protasis-design-report/v1 object and creates the report exclusively, so an
existing entry at the report path is never replaced.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys


PACKAGE = "docs/deferred-runner-binding"
SELF = PACKAGE + "/proof.py"
RECORD = PACKAGE + "/design-evidence.json"
RECORD_SHA256 = "2ee92a4119378e5cfd8e7a6455ceebe850cd222f821fd6c75fd98d194c3aba22"
REPORT_SCHEMA = "protasis-design-report/v1"
SELECTED = "creating-step-binding"
CANDIDATES = (
    "creating-step-binding",
    "reviewed-stdlib-runner",
    "runbook-embedded-source",
    "pre-placed-untracked",
)
# The runbook step that adds each criterion's handler. The record's stop point
# is one step later, because a step:N cell is due when step N-1 pushes.
CRITERIA = {
    "validator-deferred-contract": 2,
    "released-adapter-replay": 2,
    "successor-replay-milliseconds": 2,
    "controller-binding-custody": 3,
    "joined-demonstration": 4,
}
# criterion -> callable(root: Path) returning the value for the criterion's unit.
HANDLERS: dict = {}
FLAGS = ("--candidate", "--criterion", "--report")
USAGE = ("usage: python3 " + SELF + " --candidate <candidate> --criterion <criterion>"
         " --report .hexaemeron/reports/<candidate>-<criterion>.json")
EVENT = "deferred-runner-proof-refused"
REPORT_DIRECTORY = (".hexaemeron", "reports")
MAX_RECORD_BYTES = 256 * 1024
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class Refusal(Exception):
    """Carry one fixed reason token; never input text or exception detail."""


def parse(argv):
    """Accept exactly the three flags, each once, each followed by its value."""
    if len(argv) != 2 * len(FLAGS):
        raise Refusal("argument-not-closed")
    values = {}
    for flag, value in zip(argv[0::2], argv[1::2]):
        if flag not in FLAGS or flag in values:
            raise Refusal("argument-not-closed")
        values[flag] = value
    return values["--candidate"], values["--criterion"], values["--report"]


def report_name(candidate, criterion):
    return candidate + "-" + criterion + ".json"


def resolver(candidate, criterion):
    """Return the exact resolver string the design record holds for the cell."""
    return ("python3 " + SELF + " --candidate " + candidate + " --criterion " + criterion
            + " --report " + "/".join(REPORT_DIRECTORY) + "/" + report_name(candidate, criterion))


def check_cell(candidate, criterion, report):
    if candidate not in CANDIDATES:
        raise Refusal("unknown-candidate")
    if criterion not in CRITERIA:
        raise Refusal("unknown-criterion")
    if candidate != SELECTED:
        raise Refusal("candidate-not-selected")
    if report != "/".join(REPORT_DIRECTORY) + "/" + report_name(candidate, criterion):
        raise Refusal("report-not-cell-path")


def open_report_directory(root, *, create):
    """Walk .hexaemeron/reports without following links; None when absent."""
    descriptor = os.open(root, DIRECTORY_FLAGS)
    try:
        for part in REPORT_DIRECTORY:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            try:
                following = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            except FileNotFoundError:
                if create:
                    raise
                os.close(descriptor)
                return None
            except OSError:
                raise Refusal("report-directory-unsafe") from None
            os.close(descriptor)
            descriptor = following
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def require_absent(root, name):
    """Refuse when any entry, a link included, already holds the report path."""
    directory = open_report_directory(root, create=False)
    if directory is None:
        return
    try:
        os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return
    finally:
        os.close(directory)
    raise Refusal("report-already-exists")


def write_exclusive(root, name, data):
    directory = open_report_directory(root, create=True)
    try:
        try:
            descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                                 | os.O_CLOEXEC, 0o644, dir_fd=directory)
        except FileExistsError:
            raise Refusal("report-already-exists") from None
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            # The exclusive create made this entry ours, so a partial report goes.
            os.unlink(name, dir_fd=directory)
            raise
    finally:
        os.close(directory)


def read_record(root):
    """Read the committed design record, bounded and without following links."""
    *parents, leaf = RECORD.split("/")
    try:
        directory = os.open(root, DIRECTORY_FLAGS)
        try:
            for part in parents:
                following = os.open(part, DIRECTORY_FLAGS, dir_fd=directory)
                os.close(directory)
                directory = following
            descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                                 | os.O_CLOEXEC, dir_fd=directory)
        finally:
            os.close(directory)
    except OSError:
        raise Refusal("design-record-unavailable") from None
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise Refusal("design-record-not-regular-file")
        data = stream.read(MAX_RECORD_BYTES + 1)
    if hashlib.sha256(data).hexdigest() != RECORD_SHA256:
        raise Refusal("design-record-digest-mismatch")
    return json.loads(data)


def pending_unit(record, candidate, criterion):
    """Return the unit of the one pending cell whose resolver this run is."""
    rows = [row for row in record["results"]
            if row["candidate"] == candidate and row["criterion"] == criterion]
    definitions = [item for item in record["criteria"] if item["id"] == criterion]
    if (len(rows) != 1 or len(definitions) != 1 or rows[0].get("state") != "pending"
            or rows[0].get("resolver") != resolver(candidate, criterion)
            or rows[0].get("report") != "reports/" + report_name(candidate, criterion)
            or definitions[0]["stage"] != "conformance"):
        raise Refusal("design-record-cell-mismatch")
    return definitions[0]["unit"]


def value_matches(value, unit):
    if unit == "boolean":
        return type(value) is bool
    if unit == "milliseconds":
        return type(value) is int and value >= 0
    return False


def resolve(root, candidate, criterion, report):
    """Check the cell, run its handler and create its report, or refuse."""
    check_cell(candidate, criterion, report)
    name = report_name(candidate, criterion)
    require_absent(root, name)
    handler = HANDLERS.get(criterion)
    if handler is None:
        raise Refusal("operation-not-implemented:" + criterion + ":step-" + str(CRITERIA[criterion]))
    unit = pending_unit(read_record(root), candidate, criterion)
    value = handler(root)
    if not value_matches(value, unit):
        raise Refusal("handler-value-outside-unit")
    result = {"schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion,
              "value": value, "unit": unit, "command": resolver(candidate, criterion), "exit": 0}
    write_exclusive(root, name, (json.dumps(result, indent=2, sort_keys=True) + "\n").encode())
    return result


def main(argv=None, root=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    root = Path(__file__).absolute().parents[2] if root is None else Path(root)
    named = {"candidate": None, "criterion": None}
    try:
        candidate, criterion, report = parse(argv)
        # Echo only values from the closed sets, never arbitrary input.
        named["candidate"] = candidate if candidate in CANDIDATES else None
        named["criterion"] = criterion if criterion in CRITERIA else None
        result = resolve(root, candidate, criterion, report)
    except Refusal as error:
        reason = str(error)
    except (OSError, ValueError):
        reason = "input-unavailable"
    else:
        print(json.dumps(result, sort_keys=True))
        return 0
    print(json.dumps({"event": EVENT, "reason": reason, **named}, sort_keys=True))
    if reason == "argument-not-closed":
        print(USAGE, file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
