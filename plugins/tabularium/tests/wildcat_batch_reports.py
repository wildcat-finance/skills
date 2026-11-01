"""Bounded report creation, Step selection and conformance dispatch for #2087.

Both registered interfaces delegate here, so every later choice lives in this
module and in focused test modules while the interface bytes stay fixed.
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
# The retained criterion reads the environment and directories, so it lives in
# a sibling module; this one stays free of `os` and launches nothing.
from wildcat_batch_retained import retained_resolver

PROOF_REPORTER = "plugins/tabularium/tests/prove_wildcat_batches.py"
OBSERVATIONS_SCHEMA = "wildcat-batch-conformance-observations/v1"
CANDIDATES = ("adjacent-burn", "unique-value-burn", "all-batch-events",
              "envelope-batch-field")
CRITERIA = ("semantic-conformance", "schema-parity", "retained-conformance")
# The twelve pairs that carry a pending resolver in the design record.
PENDING_PAIRS = frozenset((candidate, criterion)
                          for candidate in CANDIDATES for criterion in CRITERIA)

# Step number to the exact focused classes it runs; later Steps add their rows.
MAPPING_CASES = (("test_wildcat_batch_mapping", "BatchMappingTests"),)
PARITY_CASES = (("test_wildcat_batch_parity", "BatchSchemaParityTests"),)
SPECIMEN_CASES = (("test_wildcat_batch_specimens", "BatchSpecimenTests"),)
RETAINED_CASES = (("test_wildcat_batch_retained", "BatchRetainedTests"),)
STEP_CASES = {
    1: (("test_wildcat_batch_scaffold", "BatchScaffoldTests"),),
    2: MAPPING_CASES + PARITY_CASES,
    3: SPECIMEN_CASES,
    4: RETAINED_CASES,
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


# (candidate, criterion) to a resolver returning (bool, observations or None).
# Only the selected design's three criteria resolve; the other nine pairs
# refuse. The retained one needs both staging trees and refuses by variable
# name without them.
CONFORMANCE = {
    ("adjacent-burn", "semantic-conformance"): focused_resolver(MAPPING_CASES),
    ("adjacent-burn", "schema-parity"): focused_resolver(PARITY_CASES),
    ("adjacent-burn", "retained-conformance"): retained_resolver(),
}


def require_fresh(raw: str) -> None:
    """Refuse before any write when a declared output leaf already exists.

    The create-only writer refuses an existing leaf on its own, but the sidecar
    is written before the report, so without this check a rerun whose report
    exists leaves a fresh sidecar behind its exit 2.
    """
    path = Path(*report_parts(raw, Path.cwd()))
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise EvidenceUnavailable("report leaf already exists")


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
