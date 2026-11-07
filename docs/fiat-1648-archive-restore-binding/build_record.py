#!/usr/bin/env python3
"""Assemble .hexaemeron/design-evidence.json from the selection reports.

Reads every selection report under .hexaemeron/design/reports/selection/,
derives each cell's state from its value and the criterion's comparison, and
names the exact resolver, future report path and stop point for every
conformance cell. Writes only to an --out path that must not exist.
"""
import argparse, hashlib, json, os, sys

CANDIDATES = [
    ("path-unchanged", "Today's restore: every operation after admission resolves the destination by its absolute path; the admission descriptor is held unused."),
    ("identity-recheck", "Keep absolute paths and re-prove before and after every operation and Git child that the destination name still names the admitted inode."),
    ("anchored-cwd", "fchdir to the admitted descriptor after the inspector; every controller operation is cwd- or dir_fd-relative, every Git child inherits that cwd, and identity seals bracket each Git child and each name-dependent step."),
    ("private-build-adopt", "Build repository, capsule, marker and worktree in a private scratch directory, then adopt each entry into the admitted directory by descriptor-relative rename and repoint Git's worktree links."),
]
SELECTION = [
    ("unswapped-restore-completes", "compatibility", "gate", "protasis", "boolean", "equals", True),
    ("directory-swap-writes-nothing", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("symlink-swap-writes-nothing", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("interrupted-cleanup-stays-bound", "recovery", "gate", "elenchus", "boolean", "equals", True),
    ("residue-follows-reference", "compatibility", "gate", "protasis", "boolean", "equals", True),
    ("transaction-race-leaked-trials", "correctness", "metric", "phylax", "count", "minimise", None),
    ("name-resolving-writes", "correctness", "metric", "phylax", "count", "minimise", None),
    ("identity-probes-per-restore", "time", "metric", "metron", "count", "minimise", None),
    ("bytes-built-outside-destination", "space", "metric", "metron", "bytes", "minimise", None),
]
CONFORMANCE = [
    ("replacement-regression-guarded", "correctness", "elenchus"),
    ("nonempty-symlink-still-refuse", "compatibility", "protasis"),
    ("interrupted-restore-stays-bound", "recovery", "elenchus"),
    ("from-mode-unchanged", "compatibility", "protasis"),
]

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
            data = open(os.path.join(base, rel), "rb").read()
            report = json.loads(data)
            assert report["candidate"] == candidate and report["criterion"] == cid and report["exit"] == 0
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
              "selection": {"candidate": "anchored-cwd", "rule": "unique-frontier", "policy_ref": None}}
    with open(args.out, "x") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")

if __name__ == "__main__":
    main()
