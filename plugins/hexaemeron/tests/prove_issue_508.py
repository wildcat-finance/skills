#!/usr/bin/env python3
"""Refuse unimplemented issue 508 conformance without producing evidence."""

import argparse
import json


CANDIDATES = ("whole-worker-sandbox", "optional-tool-mediation")
CRITERIA = (
    "whole-launch-dispatch", "worker-deadline", "worker-output-cap",
    "origin-drift-recovery", "single-cumulative-reconstruction",
    "executed-inoculation-guards", "carryover-lineage-recovery",
    "source-owned-report-compatibility", "gate-parser-no-execution",
    "gate-receipt-replay", "whole-path-demonstration",
)


def main(argv=None):
    """Accept a declared resolver call; return 1 until its executor exists.

    No report path is opened, even when it already holds a report. Callers
    must require this process to exit zero before consuming report bytes.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=CRITERIA)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    print(json.dumps({
        "schema": "issue508-conformance-refusal/v1",
        "event": "issue508_conformance_refused",
        "code": "executor-unimplemented",
        "promise": "protasis-runbook-readiness",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "consequence": 2,
        "blocked_transition": "criterion-acceptance",
        "recovery": "Implement and execute the complete declared specimen set, then rerun.",
    }, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
