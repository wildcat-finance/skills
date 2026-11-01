"""Bounded report creation, Step selection and conformance dispatch for #2090.

Both registered interfaces delegate here. Later Steps extend this helper and
focused test modules while keeping the interface bytes fixed.
"""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Reuse the existing create-only, no-follow writer and the observed unittest
# counters; their own guards already run under the 1378 scaffold.
from wildcat_v3_reports import (EvidenceUnavailable, ObservedResult, REPORT_CAP,
                                report_parts, result_payload, result_status,
                                run_cases, write_report)
PROOF_REPORTER = "plugins/tabularium/tests/prove_wildcat_parameters.py"
OBSERVATIONS_SCHEMA = "wildcat-parameter-conformance-observations/v1"
CANDIDATES = ("native-fields", "contextual-projection")
CRITERIA = ("mapping-conformance", "schema-compatibility", "retained-conformance")
PENDING_PAIRS = frozenset((candidate, criterion)
                          for candidate in CANDIDATES for criterion in CRITERIA)
STEP_CASES = {
    1: (("test_wildcat_parameter_scaffold", "ParameterScaffoldTests"),),
}


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


# Product conformance remains unavailable until its implementing Step lands.
CONFORMANCE = {}


def require_fresh(raw: str) -> None:
    """Validate existing ancestors and refuse an occupied leaf before resolving."""
    import os
    parts = report_parts(raw, Path.cwd())
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent = os.open(Path.cwd(), flags)
    try:
        for part in parts[:-1]:
            try:
                child = os.open(part, flags, dir_fd=parent)
            except FileNotFoundError:
                return
            os.close(parent)
            parent = child
        try:
            os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return
        raise EvidenceUnavailable("report leaf already exists")
    finally:
        os.close(parent)


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
        # Only this module's own refusals carry their text; they name a
        # variable or a check, never a path, and any other error stays a class.
        reason = type(exc).__name__
        if isinstance(exc, EvidenceUnavailable):
            reason += ": " + str(exc)
        parser.exit(2, "conformance unavailable: " + reason + "\n")
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
        parser.exit(2, "focused report unavailable: " + type(exc).__name__ + "\n")
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    return status
