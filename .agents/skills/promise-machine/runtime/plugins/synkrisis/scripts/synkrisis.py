#!/usr/bin/env python3
"""Refusing scaffold for specified cross-run observation comparison.

This is the runbook's Step 1 scaffold. The command declares the complete
specified surface, four operations over one declared cohort of
`promise-machine-run-observation/v1` records, and refuses each one with a
stable code naming the runbook step that implements it. Nothing here reads a
record, writes an artefact, calls a model, fetches a URL, executes observed
content, files an issue, edits a repository, or dispatches another skill.
"""

from __future__ import annotations

import argparse
import json

PRODUCER_CONTRACT = "promise-machine-run-observation/v1"

# The specified operations and the committed runbook step that lands each one.
PENDING_STEPS = {
    "cohort": "Step 2",
    "diagnose": "Step 3",
    "render": "Step 4",
    "verify": "Step 4",
}


class Refusal(Exception):
    """One stable finding: code, fault class, safe path, recovery."""

    def __init__(self, code, fault, path, message, recovery):
        super().__init__(message)
        self.code = code
        self.fault = fault
        self.path = path
        self.message = message
        self.recovery = recovery


def scaffold_refusal(operation: str) -> Refusal:
    step = PENDING_STEPS[operation]
    return Refusal(
        "SK000",
        "structural",
        operation,
        f"operation {operation!r} is specified and not yet implemented",
        f"build {step} of docs/synkrisis/runbook.md, then rerun the operation",
    )


def emit_refusal(refusal: Refusal, as_json: bool) -> None:
    document = {
        "code": refusal.code,
        "fault": refusal.fault,
        "path": refusal.path,
        "producer": PRODUCER_CONTRACT,
        "message": refusal.message,
        "recovery": refusal.recovery,
    }
    if as_json:
        print(json.dumps(document, sort_keys=True, separators=(",", ":")))
    else:
        print(
            f"{refusal.code} fault={refusal.fault} path={refusal.path} "
            f"producer={PRODUCER_CONTRACT}: {refusal.message}; "
            f"recovery: {refusal.recovery}"
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="synkrisis", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    cohort_parser = subparsers.add_parser(
        "cohort",
        help="specified cohort classifier; this scaffold currently refuses",
    )
    cohort_parser.add_argument("--manifest", required=True)
    cohort_parser.add_argument("--policy", required=True)
    cohort_parser.add_argument("--out", required=True)
    cohort_parser.add_argument("--json", action="store_true")

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="specified rule-catalogue pass; this scaffold currently refuses",
    )
    diagnose_parser.add_argument("--cohort", required=True)
    diagnose_parser.add_argument("--rules", required=True)
    diagnose_parser.add_argument("--out", required=True)
    diagnose_parser.add_argument("--json", action="store_true")

    render_parser = subparsers.add_parser(
        "render",
        help="specified fixed-template renderer; this scaffold currently refuses",
    )
    render_parser.add_argument("findings")
    render_parser.add_argument("--out", required=True)
    render_parser.add_argument("--json", action="store_true")

    verify_parser = subparsers.add_parser(
        "verify",
        help="specified whole-path verifier; this scaffold currently refuses",
    )
    verify_parser.add_argument("--manifest", required=True)
    verify_parser.add_argument("--policy", required=True)
    verify_parser.add_argument("--cohort", required=True)
    verify_parser.add_argument("--rules", required=True)
    verify_parser.add_argument("--findings", required=True)
    verify_parser.add_argument("--report", required=True)
    verify_parser.add_argument("--json", action="store_true")

    arguments = parser.parse_args(argv)
    emit_refusal(scaffold_refusal(arguments.command), arguments.json)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
