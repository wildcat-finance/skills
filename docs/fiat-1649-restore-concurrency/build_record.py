#!/usr/bin/env python3
"""Assemble .hexaemeron/design-evidence.json from the selection reports (skills#1649).

Reads every selection report under .hexaemeron/design/reports/selection/,
derives each cell's state from its value and the criterion's comparison, and
names the exact resolver, future report path and stop point for every
conformance cell. Writes only to an --out path that must not exist.
"""
import argparse
import hashlib
import json
import os
import sys

CANDIDATES = [
    ("mutating-set", "Add cmd_checkpoint_restore to MUTATING and keep held_lock unchanged: the run lock is taken only where the --dir already has a state root."),
    ("destination-kernel-lock", "Create and flock the run lock at <destination>/.hexaemeron/lock through the admitted descriptor right after admission, re-scan, carry a lock in the private stage, and close held_lock's absent-root window."),
    ("exclusive-entry", "Create one O_EXCL entry relative to the admitted descriptor after admission, re-scan, reclaim it when its recorded holder is dead, carry a lock in the private stage, and close held_lock's absent-root window."),
    ("admitted-fd-flock", "flock the admitted (or --from origin) directory descriptor before the emptiness scan, take the origin's run lock inside the marker transaction, carry a lock in the private stage through publication, and close held_lock's absent-root window."),
]
SELECTION = [
    ("uncontended-restore-completes", "compatibility", "gate", "protasis", "boolean", "equals", True),
    ("competing-restores-one-winner", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("live-resume-refused", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("killed-holder-resumes", "recovery", "gate", "elenchus", "boolean", "equals", True),
    ("killed-before-write-readmits", "recovery", "gate", "elenchus", "boolean", "equals", True),
    ("imported-state-excluded", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("origin-init-excluded", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("concurrent-holders-after-crash", "correctness", "metric", "phylax", "count", "minimise", None),
    ("lock-acquisitions-per-restore", "time", "metric", "metron", "count", "minimise", None),
    ("entries-left-after-early-kill", "space", "metric", "metron", "count", "minimise", None),
]
CONFORMANCE = [
    ("restore-contention-guarded", "correctness", "elenchus"),
    ("imported-state-guarded", "correctness", "elenchus"),
    ("killed-restore-recovers", "recovery", "elenchus"),
    ("existing-restores-unchanged", "compatibility", "protasis"),
]
SELECTED = "admitted-fd-flock"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if os.path.lexists(args.out):
        sys.exit("refusing to replace an existing record")
    base = os.path.dirname(os.path.abspath(args.out))
    criteria, results = [], []
    for cid, concern, kind, owner, unit, comparator, threshold in SELECTION:
        criteria.append({"id": cid, "concern": concern, "kind": kind, "stage": "selection",
                         "owner": owner, "unit": unit, "comparator": comparator,
                         "threshold": threshold, "blocks": "design-lock"})
    for cid, concern, owner in CONFORMANCE:
        criteria.append({"id": cid, "concern": concern, "kind": "gate", "stage": "conformance",
                         "owner": owner, "unit": "boolean", "comparator": "equals",
                         "threshold": True, "blocks": "integration"})
    for candidate, _ in CANDIDATES:
        for cid, concern, kind, owner, unit, comparator, threshold in SELECTION:
            rel = f"design/reports/selection/{candidate}-{cid}.json"
            with open(os.path.join(base, rel), "rb") as handle:
                data = handle.read()
            report = json.loads(data)
            if report["candidate"] != candidate or report["criterion"] != cid or report["exit"] != 0:
                sys.exit(f"report {rel} does not match its cell")
            value = report["value"]
            state = "pass" if kind == "metric" or value == threshold else "fail"
            results.append({"candidate": candidate, "criterion": cid, "state": state,
                            "report": {"path": rel, "sha256": hashlib.sha256(data).hexdigest()}})
        for cid, concern, owner in CONFORMANCE:
            rel = f"design/reports/conformance/{candidate}-{cid}.json"
            results.append({"candidate": candidate, "criterion": cid, "state": "pending",
                            "resolver": f"python3 .hexaemeron/design/probe.py conform --candidate {candidate} --criterion {cid} --root . --out .hexaemeron/{rel}",
                            "report": rel, "blocks": "integration"})
    record = {"schema": "protasis-design-evidence/v1",
              "candidates": [{"id": c, "summary": s} for c, s in CANDIDATES],
              "criteria": criteria, "results": results,
              "selection": {"candidate": SELECTED, "rule": "unique-frontier", "policy_ref": None}}
    with open(args.out, "x") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
