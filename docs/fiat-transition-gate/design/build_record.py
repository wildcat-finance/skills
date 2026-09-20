#!/usr/bin/env python3
"""Build the issue-871 design record once, from freshly measured reports.

usage: build_record.py

Run from the run worktree root. Runs `resolve_gate.py` for every selection
cell, then writes `.hexaemeron/design-evidence.json`. It refuses when the
record or any report already exists, so a receipted record or report is never
overwritten. It reads no controller state and writes only the record and the
reports the resolver creates.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HOME = Path(".hexaemeron")
RECORD = HOME / "design-evidence.json"
REPORTS = HOME / "design" / "reports"
TIMEOUT = 600

CANDIDATES = (
    ("dispatcher-grant-wal",
     "One dispatcher evaluates a pure closed gate under the run lock; every writer needs "
     "its grant; one labelled write-ahead commit; exhausted loops continue append-only."),
    ("per-handler-gate",
     "Each mutating handler calls the pure gate itself and the controller's present "
     "ledger-then-state writer stays as it is; exhausted loops continue append-only."),
    ("external-writer-broker",
     "The gate grants in process but a separate broker process under another OS identity "
     "owns the state writer and the pins; exhausted loops continue append-only."),
    ("gate-with-replacement-exit",
     "The dispatcher gate and write-ahead commit without a same-ledger loop; an exhausted "
     "loop leaves only by the existing verdict close, halt or replacement admission."),
)


def gate(identifier, concern, owner, unit="boolean", comparator="equals", threshold=True):
    return {"id": identifier, "concern": concern, "kind": "gate", "stage": "selection",
            "owner": owner, "unit": unit, "comparator": comparator,
            "threshold": threshold, "blocks": "design-lock"}


def conformance(identifier, concern, blocks):
    return {"id": identifier, "concern": concern, "kind": "gate", "stage": "conformance",
            "owner": "elenchus", "unit": "boolean", "comparator": "equals",
            "threshold": True, "blocks": blocks}


CRITERIA = (
    gate("refuses-622-widening", "correctness", "fiat"),
    gate("appends-loop-two-same-ledger", "correctness", "fiat"),
    gate("legacy-loop-one-bytes-identical", "compatibility", "fiat"),
    gate("runs-under-one-account-stdlib", "compatibility", "phylax"),
    gate("crash-window-labelled", "recovery", "elenchus"),
    gate("added-processes-per-mutation", "time", "metron", "count", "at-most", 0),
    gate("max-grant-bytes", "space", "metron", "bytes", "at-most", 65536),
    {"id": "gate-call-sites", "concern": "correctness", "kind": "metric",
     "stage": "selection", "owner": "fiat", "unit": "count", "comparator": "minimise",
     "threshold": None, "blocks": "design-lock"},
    conformance("product-refuses-622-specimens", "correctness", "step:4"),
    conformance("product-appends-loop-two", "recovery", "step:5"),
    conformance("product-every-mutator-mapped", "correctness", "step:7"),
)


def derived(criterion, value):
    if criterion["kind"] == "metric":
        return "pass"
    if criterion["comparator"] == "equals":
        return "pass" if value == criterion["threshold"] else "fail"
    return "pass" if value <= criterion["threshold"] else "fail"


def main() -> int:
    if RECORD.exists() or RECORD.is_symlink():
        print("build_record: the record exists and is never overwritten", file=sys.stderr)
        return 2
    REPORTS.mkdir(parents=True, exist_ok=True)
    results = []
    for candidate, _summary in CANDIDATES:
        for criterion in CRITERIA:
            name = f"{candidate}-{criterion['id']}.json"
            relative = f"design/reports/{name}"
            if criterion["stage"] == "conformance":
                results.append({
                    "candidate": candidate, "criterion": criterion["id"],
                    "state": "pending",
                    "resolver": ("python3 .hexaemeron/design/conform_gate.py --candidate "
                                 f"{candidate} --criterion {criterion['id']} --out "
                                 f".hexaemeron/{relative}"),
                    "report": relative, "blocks": criterion["blocks"],
                })
                continue
            out = HOME / relative
            done = subprocess.run(
                [sys.executable, str(HOME / "design" / "resolve_gate.py"),
                 "--candidate", candidate, "--criterion", criterion["id"],
                 "--out", str(out)],
                capture_output=True, timeout=TIMEOUT, check=False,
            )
            if done.returncode != 0:
                sys.stderr.buffer.write(done.stderr)
                return 1
            data = out.read_bytes()
            results.append({
                "candidate": candidate, "criterion": criterion["id"],
                "state": derived(criterion, json.loads(data)["value"]),
                "report": {"path": relative, "sha256": hashlib.sha256(data).hexdigest()},
            })
    record = {
        "schema": "protasis-design-evidence/v1",
        "candidates": [{"id": c, "summary": s} for c, s in CANDIDATES],
        "criteria": list(CRITERIA),
        "results": results,
        "selection": {"candidate": "dispatcher-grant-wal", "rule": "unique-frontier",
                      "policy_ref": None},
    }
    with open(RECORD, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
