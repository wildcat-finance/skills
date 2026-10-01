#!/usr/bin/env python3
"""Resolve the skills#2042 conformance cells that released-adapter evidence owns.

Only the selected candidate, ``base-commit-bindings``, is resolvable here.
``released-adapter-tests-green`` runs the two released-adapter test modules and
the starting-commit bindings module through ``unittest`` from the repository
root and reports ``true`` when that process exits 0. The
``older-controller-supersession-fixture`` cell refuses by name until Step 3
lands the controller half it measures. The report is created exclusively at
the caller-named path, and a refusal writes nothing.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
CANDIDATE = "base-commit-bindings"
GREEN_CRITERION = "released-adapter-tests-green"
NOT_IMPLEMENTED = {
    "older-controller-supersession-fixture": "not implemented until Step 3",
}
RELEASED_ADAPTER_MODULES = (
    "plugins.hexaemeron.tests.test_gate_commands",
    "plugins.hexaemeron.tests.test_gate_deferred_registration",
    "plugins.hexaemeron.tests.test_gate_starting_commit_bindings",
)
TEST_TIMEOUT_SECONDS = 1800


class Refusal(Exception):
    """The cell cannot be resolved; nothing is written."""


def report_path(raw: str) -> Path:
    """Admit one caller-named destination that does not exist yet."""
    if not raw or "\x00" in raw or "\\" in raw:
        raise Refusal("report-path-unsafe")
    path = Path(raw)
    if any(part in ("", ".", "..") for part in path.parts if part != path.anchor):
        raise Refusal("report-path-escape")
    if os.path.lexists(path):
        raise Refusal("report-already-exists")
    return path


def released_adapter_tests_green() -> bool:
    completed = subprocess.run(  # phylax: allow subprocess: fixed argv interpreter, no shell
        [sys.executable, "-m", "unittest", *RELEASED_ADAPTER_MODULES],
        cwd=ROOT, stdin=subprocess.DEVNULL, capture_output=True,
        timeout=TEST_TIMEOUT_SECONDS, check=False,
    )
    if completed.returncode != 0:
        raise Refusal("released-adapter-tests-red: exit %d" % completed.returncode)
    return True


def resolve(candidate: str, criterion: str) -> bool:
    if candidate != CANDIDATE:
        raise Refusal("unknown-candidate")
    if criterion in NOT_IMPLEMENTED:
        raise Refusal(criterion + ": " + NOT_IMPLEMENTED[criterion])
    if criterion != GREEN_CRITERION:
        raise Refusal("unknown-criterion")
    return released_adapter_tests_green()


def write_report(path: Path, payload: dict) -> None:
    """Create the report once; an existing file or link at the path refuses."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        destination = report_path(args.report)
        value = resolve(args.candidate, args.criterion)
    except (Refusal, subprocess.SubprocessError, OSError) as exc:
        print("refused: " + str(exc), file=sys.stderr)
        return 1
    payload = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": value,
        "unit": "boolean",
        "command": ("python3 plugins/hexaemeron/tests/fiat_starting_commit_bindings_proof.py"
                    " --candidate " + args.candidate + " --criterion " + args.criterion
                    + " --report " + args.report),
        "exit": 0,
    }
    try:
        write_report(destination, payload)
    except FileExistsError:
        print("refused: report-already-exists", file=sys.stderr)
        return 1
    except OSError as exc:
        print("refused: report-not-written: " + str(exc), file=sys.stderr)
        return 1
    print(args.candidate + "/" + args.criterion + " = " + repr(value))
    return 0


if __name__ == "__main__":
    sys.exit(main())
