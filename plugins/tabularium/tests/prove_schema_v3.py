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

Four criteria are resolved here, one per run.

`rejection-parity` holds when every committed rejection fixture is refused by
`jsonschema` and by `validate_event_row`, and both name the one field the
fixture is named for.  A fixture either validator admits is a disagreement.

`shipped-ledgers-validate-v3` holds when every shipped release built under
canonical event schema 3 has a `coverage.json` the v3 manifest schema admits
and an `events.jsonl` whose every row the v3 event schema and
`validate_event_row` both admit.

`legacy-v0-verify` holds when every release published under schema 2 still
verifies offline through the retained v2 read path and still carries the bytes
it was published with.  That is the recovery half of the superseding design:
the newer envelope is worth nothing if reading the older releases stops
working, and it is worth less than nothing if their bytes moved.

`suite-wall-time` is the one criterion whose unit is not boolean.  It times
`python3 -m unittest discover -s plugins/tabularium/tests -t plugins/tabularium`
in a subprocess, the way the study declares it, and records the elapsed
milliseconds.  The subprocess is what keeps the measurement out of the calling
process's own timing and what makes the guard below meaningful: the timed suite
must never be the suite that asked for the measurement, so a run that finds
`TABULARIUM_SUITE_WALL_TIME` already set collects no observation at all rather
than forking another suite under itself.

A criterion that disagrees anywhere makes the value false, the report record
exit 1, and the process exit 1.  So does a criterion whose evidence collection
is empty: `all(())` is true, and a closed `protasis-design-report/v1` object
has nowhere to record that it attested nothing, so an empty collection is
refused here rather than reported as a pass.  A boolean criterion records that
refusal as `"value": false` with exit 1.  A millisecond criterion cannot: every
number it could write is a duration nothing measured, and a small one would
read as a pass.  It therefore writes no report at all and exits 1, which is the
same refusal one step stronger.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

from tests import support  # noqa: E402


REPORT_SCHEMA = "protasis-design-report/v1"
CRITERIA = {
    "legacy-v0-verify": "boolean",
    "rejection-parity": "boolean",
    "shipped-ledgers-validate-v3": "boolean",
    "suite-wall-time": "milliseconds",
}
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
EVENT_PREFIX = "tabularium.schema-v3."
EMPTY_EVIDENCE = "%s was resolved over no observations"

# The budget the design record states for `suite-wall-time`, in milliseconds,
# and the suite the study names as the thing it measures.  The record lives
# under `.hexaemeron/`, which Git ignores, so the number is repeated here
# rather than read from a file no checkout carries.
SUITE_BUDGET_MS = 60000
SUITE_ARGUMENTS = (
    "-m", "unittest", "discover",
    "-s", "plugins/tabularium/tests",
    "-t", "plugins/tabularium",
)
SUITE_GUARD = "TABULARIUM_SUITE_WALL_TIME"
RAN_TESTS = re.compile(r"^Ran (?P<tests>\d+) tests? in ", re.MULTILINE)


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
    """Write one report whole, or leave what was already there untouched.

    Staged in the report's own directory and renamed into place, the way
    `write_bytes_atomic` already writes a release, so an interrupted run
    leaves no half-written report and destroys no earlier one.  Opening the
    report itself with `O_TRUNC` emptied it before the first byte was written:
    a failure anywhere after that left zero bytes where a valid report had
    been.  `O_EXCL` refuses a staged path that already exists or is a symlink,
    and the final component is checked again here, so the refusal
    `report_path` makes survives the change of writer.
    """
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    staged = path.parent / ("%s.%d.tmp" % (path.name, os.getpid()))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        handle = os.open(str(staged), flags, 0o644)
    except OSError as exc:
        raise ReportRefused("report path is not writable: %s: %s" % (staged, exc))
    try:
        try:
            os.write(handle, payload)
            os.fsync(handle)
        finally:
            os.close(handle)
        if path.is_symlink():
            raise ReportRefused("report path component is a symlink: %s" % path)
        os.replace(str(staged), str(path))
    except OSError as exc:
        raise ReportRefused("report path is not writable: %s: %s" % (path, exc))
    finally:
        if staged.exists():
            staged.unlink()


def resolver_command(args):
    """The command these arguments name, built from the arguments themselves.

    The design record binds each pending result to an exact resolver string and
    `design_evidence.py` compares the report's `command` against it, so the
    field is evidence rather than decoration.  Reading it from `sys.argv` would
    record whatever the host process was invoked with whenever `main` is called
    in process, which is a command that never ran and a place for an unrelated
    caller's arguments to land in a committed report.

    `shlex.join` leaves a token that needs no quoting exactly as it is, so
    every resolver string the design record declares is still reproduced byte
    for byte, while a report path carrying a space is quoted rather than
    recorded as two arguments nobody passed.
    """
    script = Path(__file__).resolve()
    try:
        script = script.relative_to(support.REPO_ROOT)
    except ValueError:
        pass
    return shlex.join(
        [
            "python3",
            str(script),
            "--candidate", args.candidate,
            "--criterion", args.criterion,
            "--report", args.report,
        ]
    )


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


def shipped_ledgers_validate_v3():
    """One observation per shipped release built under schema 3."""
    return [
        support.document_observation(name)
        for name in support.SUPERSEDING_RELEASES
    ]


def legacy_v0_verify():
    """One observation per release published under schema 2."""
    return [
        support.verification_observation(
            name, 2, support.release_published_digests(name)
        )
        for name in support.LEGACY_RELEASES
    ]


def suite_wall_time():
    """One observation: the Tabularium suite, timed in its own process.

    The clock is `time.monotonic`, which no wall-clock adjustment moves, and it
    brackets the whole subprocess, so the recorded duration is what a reader
    running the same command would wait rather than the suite's own internal
    figure.  The test count is read from the runner's summary line for the
    demonstration's benefit; a run whose output does not carry one records
    `None` rather than a number nothing printed.

    A guarded run collects nothing.  That is an empty collection, which the
    caller refuses, so a reentrant invocation fails visibly instead of forking
    the suite under itself.
    """
    if os.environ.get(SUITE_GUARD):
        return []
    argv = [sys.executable] + list(SUITE_ARGUMENTS)
    environment = dict(os.environ)
    environment[SUITE_GUARD] = "1"
    started = time.monotonic()
    completed = subprocess.run(
        argv,
        capture_output=True,
        cwd=str(support.REPO_ROOT),
        env=environment,
        text=True,
    )
    elapsed = int(round((time.monotonic() - started) * 1000))
    summary = RAN_TESTS.search(completed.stderr or "")
    return [
        {
            "agreed": completed.returncode == 0 and elapsed <= SUITE_BUDGET_MS,
            "budget_ms": SUITE_BUDGET_MS,
            "command": shlex.join(argv),
            "elapsed_ms": elapsed,
            "exit": completed.returncode,
            "tests": int(summary.group("tests")) if summary else None,
        }
    ]


OBSERVERS = {
    "legacy-v0-verify": legacy_v0_verify,
    "rejection-parity": rejection_parity,
    "shipped-ledgers-validate-v3": shipped_ledgers_validate_v3,
    "suite-wall-time": suite_wall_time,
}


def summarise(criterion, observations):
    """The value one criterion's observations attest, and its exit code.

    A boolean criterion's value is the agreement itself.  A millisecond
    criterion's value is the longest run observed, so several observations
    could never average a slow one away, and its agreement already carries the
    budget comparison the design record declares.
    """
    agreed = bool(observations) and all(
        observation["agreed"] for observation in observations
    )
    code = 0 if agreed else 1
    if CRITERIA[criterion] == "milliseconds":
        return max(
            observation["elapsed_ms"] for observation in observations
        ), code
    return agreed, code


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

    observations = OBSERVERS[args.criterion]()
    if not observations and CRITERIA[args.criterion] != "boolean":
        sys.stderr.write(EMPTY_EVIDENCE % args.criterion + "\n")
        return 1
    value, code = summarise(args.criterion, observations)
    report = {
        "candidate": args.candidate,
        "command": resolver_command(args),
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

    event = EVENT_PREFIX + args.criterion
    for observation in observations:
        line = dict(observation)
        line["event"] = event
        sys.stdout.write(json.dumps(line, sort_keys=True) + "\n")
    sys.stdout.write(
        json.dumps(
            {
                "candidate": args.candidate,
                "criterion": args.criterion,
                "event": event + ".summary",
                "observations": len(observations),
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
