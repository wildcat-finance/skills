"""Bounded report creation, Step selection and conformance dispatch for #2088.

Both registered interfaces delegate here, so every later choice lives in this
module and in focused test modules while the interface bytes stay fixed.
"""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import sys

HERE = Path(__file__).resolve().parent
if sys.path[:1] != [str(HERE)]:
    sys.path.insert(0, str(HERE))

# Reuse the existing create-only, no-follow writer and the observed unittest
# counters; their own guards already run under the 1378 scaffold.
from wildcat_v3_reports import (EvidenceUnavailable, ObservedResult, REPORT_CAP,
                                report_parts, result_payload, result_status,
                                run_cases, write_report)

PROOF_REPORTER = "plugins/tabularium/tests/prove_wildcat_accrual.py"
OBSERVATIONS_SCHEMA = "wildcat-accrual-conformance-observations/v1"
CANDIDATES = ("abi-named-amounts", "unit-named-amounts", "native-state-only",
              "envelope-native-state")
CRITERIA = ("semantic-conformance", "schema-parity", "retained-conformance")
# The twelve pairs that carry a pending resolver in the design record.
PENDING_PAIRS = frozenset((candidate, criterion)
                          for candidate in CANDIDATES for criterion in CRITERIA)

# Step number to the exact focused classes it runs; later Steps add their rows.
# A class that starts a subprocess never joins this table: Elenchus runs the
# selection in process, and a child running Step 1 would select itself again.
STEP_CASES = {
    1: (("test_wildcat_accrual_scaffold", "AccrualScaffoldTests"),),
}

# (candidate, criterion) to a resolver returning (bool, observations or None).
# Empty at Step 1: every criterion refuses until its implementation lands.
CONFORMANCE = {}


def focused_resolver(cases):
    """A resolver over exact focused classes; an error or empty run refuses."""
    def resolve():
        result = run_cases(cases)
        status = result_status(result)
        if status == 2:
            raise EvidenceUnavailable("conformance execution inconclusive")
        return status == 0, {"result": result_payload(result),
                             "executed_ids": result.executed_ids}
    return resolve


def require_fresh(raw: str) -> None:
    """Refuse before any write when a declared output leaf already exists.

    The create-only writer refuses an existing leaf on its own, but the sidecar
    is written before the report, so without this check a rerun whose report
    exists would leave a fresh sidecar behind its exit 2.
    """
    path = Path(*report_parts(raw, Path.cwd()))
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise EvidenceUnavailable("report leaf already exists")


def refusal(exc: Exception) -> str:
    """Name the refusal class; only this module's own refusals add their text.

    Those texts name a check or a variable, never a path, and any other error
    stays a class name so no input path or payload reaches the terminal.
    """
    reason = type(exc).__name__
    if isinstance(exc, EvidenceUnavailable):
        reason += ": " + str(exc)
    return reason


def proof_payload(candidate: str, criterion: str, arguments: list[str], value: bool) -> dict:
    return {
        "schema": "protasis-design-report/v1",
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": "boolean",
        "command": shlex.join(["python3", PROOF_REPORTER, *arguments]),
        "exit": 0 if value else 1,
    }


def execute_proof(parser, argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(arguments)
    try:
        report_parts(args.report, Path.cwd())
        sidecar = str(Path(args.report).with_suffix(".observations.json"))
        require_fresh(args.report)
        require_fresh(sidecar)
        pair = (args.candidate, args.criterion)
        if pair not in PENDING_PAIRS:
            raise EvidenceUnavailable("pair carries no pending resolver")
        resolver = CONFORMANCE.get(pair)
        if resolver is None:
            raise EvidenceUnavailable("criterion implementation absent")
        value, observations = resolver()
        if type(value) is not bool:
            raise EvidenceUnavailable("resolver returned no boolean")
        payload = proof_payload(args.candidate, args.criterion, arguments, value)
        if observations is not None:
            write_report(sidecar, {"schema": OBSERVATIONS_SCHEMA, "candidate": args.candidate,
                                   "criterion": args.criterion, "observations": observations})
        write_report(args.report, payload)
    except Exception as exc:
        parser.exit(2, "conformance unavailable: " + refusal(exc) + "\n")
    print(json.dumps({"exit": payload["exit"], "value": payload["value"]}), file=sys.stderr)
    return payload["exit"]


def execute_report(parser, argv: list[str] | None = None) -> int:
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report_parts(args.report, Path.cwd())
        require_fresh(args.report)
        cases = STEP_CASES.get(args.step)
        if not cases:
            raise EvidenceUnavailable("Step has no declared focused classes")
        result = run_cases(cases)
        payload = result_payload(result)
        status = result_status(result)
        write_report(args.report, payload)
    except Exception as exc:
        parser.exit(2, "focused report unavailable: " + refusal(exc) + "\n")
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    return status
