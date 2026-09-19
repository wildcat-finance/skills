#!/usr/bin/env python3
"""Resolve one Protasis design criterion for the Tabularium v3 schemas.

    python3 plugins/tabularium/tests/prove_schema_v3.py \
        --candidate <id> --criterion <id> --report <path>

The reporter writes one closed `protasis-design-report/v1` object at the report
path it was given, and nothing anywhere else.  It never creates a directory,
never follows a symlink into one, and opens the report itself with `O_NOFOLLOW`
so a symlinked final component is refused by the operating system rather than
by a check that raced it.

`jsonschema` is optional here as it is in the suite.  When the import fails the
reporter writes `jsonschema is not installed` to standard error and exits 1
before touching the report path, so a host without the package leaves no report
at all rather than a passing one.  That string is the suite's only skip reason,
which is what makes a skipped parity run visibly not a pass.

`rejection-parity` is the only criterion this step resolves.  It holds when
every committed rejection fixture is refused by `jsonschema` and by
`validate_event_row`, and both name the one field the fixture is named for.  A
fixture either validator admits is a disagreement, so the value is false, the
report records exit 1, and the process exits 1.
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from tests import support  # noqa: E402


REPORT_SCHEMA = "protasis-design-report/v1"
CRITERIA = {"rejection-parity": "boolean"}
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
EVENT = "tabularium.schema-v3.rejection-parity"


class ReportRefused(Exception):
    """The report path or the supplied identity is not one this may write."""


def identifier(value):
    if IDENTIFIER.match(value) is None:
        raise argparse.ArgumentTypeError(
            "%r is not a bounded lower-case identifier" % value
        )
    return value


def report_path(value):
    """The absolute report path, refused when any component is a symlink."""
    path = Path(value)
    if not path.is_absolute():
        path = Path.cwd() / path
    for component in [path] + list(path.parents):
        if component.is_symlink():
            raise ReportRefused(
                "report path component is a symlink: %s" % component
            )
    if not path.parent.is_dir():
        raise ReportRefused("report directory does not exist: %s" % path.parent)
    return path


def write_report(path, report):
    """Write one report, refusing to follow a symlink at the final component."""
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
    try:
        handle = os.open(str(path), flags, 0o644)
    except OSError as exc:
        raise ReportRefused("report path is not writable: %s: %s" % (path, exc))
    try:
        os.write(handle, payload)
    finally:
        os.close(handle)


def rejection_parity():
    """One observation per committed rejection fixture."""
    observations = []
    for name, field in support.REJECTION_FIXTURES:
        observation = support.parity_observation(
            support.load_rejection_fixture(name), field
        )
        observation["fixture"] = name
        observations.append(observation)
    return observations


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Resolve one Tabularium v3 schema design criterion.",
    )
    parser.add_argument("--candidate", required=True, type=identifier)
    parser.add_argument(
        "--criterion", required=True, type=identifier, choices=sorted(CRITERIA)
    )
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)

    try:
        support.import_jsonschema()
    except support.JsonschemaAbsent:
        sys.stderr.write(support.JSONSCHEMA_ABSENT + "\n")
        return 1

    try:
        path = report_path(args.report)
    except ReportRefused as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2

    observations = rejection_parity()
    value = all(observation["agreed"] for observation in observations)
    code = 0 if value else 1
    report = {
        "candidate": args.candidate,
        "command": "python3 " + " ".join(sys.argv),
        "criterion": args.criterion,
        "exit": code,
        "schema": REPORT_SCHEMA,
        "unit": CRITERIA[args.criterion],
        "value": value,
    }
    try:
        write_report(path, report)
    except ReportRefused as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2

    for observation in observations:
        line = dict(observation)
        line["event"] = EVENT
        sys.stdout.write(json.dumps(line, sort_keys=True) + "\n")
    sys.stdout.write(
        json.dumps(
            {
                "candidate": args.candidate,
                "criterion": args.criterion,
                "event": EVENT + ".summary",
                "fixtures": len(observations),
                "report": str(path),
                "value": value,
            },
            sort_keys=True,
        )
        + "\n"
    )
    return code


if __name__ == "__main__":
    sys.exit(main())
