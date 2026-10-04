"""Conformance gates consume executed focused tests, never asserted scores."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import sys

from wildcat_v3_reports import (
    EvidenceUnavailable, report_parts, result_payload, result_status, run_cases,
    write_report,
)


REPORTER = "plugins/tabularium/tests/prove_wildcat_v3.py"
CONFORMANCE_CASES = {
    "semantic-conformance": (("test_wildcat_v3_semantics", "SemanticConformanceTests"),),
    "schema-parity": (("test_wildcat_v3_schema_parity", "SchemaParityTests"),),
    "release-reproduction": (("test_wildcat_v3_reproduction", "ReleaseReproductionTests"),),
}


def execute(parser, argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(arguments)
    try:
        report_parts(args.report, Path.cwd())
        if args.candidate != "role-qualified":
            raise EvidenceUnavailable("candidate has no implemented conformance path")
        result = run_cases(CONFORMANCE_CASES[args.criterion])
        status = result_status(result)
        counters = result_payload(result)
        if status == 2:
            print(json.dumps(counters, sort_keys=True), file=sys.stderr)
            raise EvidenceUnavailable("conformance execution inconclusive")
        payload = {
            "schema": "protasis-design-report/v1",
            "candidate": args.candidate,
            "criterion": args.criterion,
            "command": shlex.join(["python3", REPORTER, *arguments]),
            "exit": status,
            "unit": "boolean",
            "value": status == 0,
        }
        observations = {
            "schema": "wildcat-v3-conformance-observations/v1",
            "candidate": args.candidate,
            "criterion": args.criterion,
            "result": counters,
            "executed_ids": result.executed_ids,
        }
        sidecar = str(Path(args.report).with_suffix(".observations.json"))
        write_report(sidecar, observations)
        write_report(args.report, payload)
    except Exception as exc:
        parser.exit(2, "conformance unavailable: " + type(exc).__name__ + "\n")
    print(json.dumps(counters, sort_keys=True), file=sys.stderr)
    return status
