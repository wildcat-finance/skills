#!/usr/bin/env python3
"""Assemble the run #2093 Protasis design record from the probe's reports.

Reads every selection report under ``design/reports/selection/`` beside the
record, derives each cell's state from its value and the criterion's
comparison, adds one pending conformance cell per candidate and conformance
criterion, and writes ``--out`` only when that path does not already exist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


CANDIDATES = [
    {
        "id": "credential-scope-projection",
        "summary": (
            "Keep the native ls-remote; read the caller's credential.* entries "
            "(every scope but command) with the caller's Git, replay them in "
            "command scope after one empty helper reset, and add HOME. Local "
            "relation reads keep the unchanged native environment."
        ),
    },
    {
        "id": "github-rest-tip",
        "summary": (
            "For a GitHub origin, read the branch tip over GitHub REST through "
            "the caller's gh as pull requests are read today; any other origin "
            "keeps the unchanged native ls-remote."
        ),
    },
    {
        "id": "credential-fill-relay",
        "summary": (
            "Run git credential fill in the caller's environment for the native "
            "origin host, then relay the returned username and password to the "
            "native ls-remote through a controller-owned helper and two "
            "environment variables."
        ),
    },
    {
        "id": "native-unchanged",
        "summary": (
            "Baseline: keep today's native environment and wording; an operator "
            "adds a repository-local credential helper around one call, as the "
            "2026-10-13 MR-03 receipt did."
        ),
    },
]

SELECTION = [
    ("global-credential-read", "correctness", "gate", "protasis", "boolean", "equals", True),
    ("moved-tip-detected", "correctness", "gate", "protasis", "boolean", "equals", True),
    ("global-insteadof-inert", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("ambient-substitution-inert", "compatibility", "gate", "phylax", "boolean", "equals", True),
    ("controller-holds-no-credential", "correctness", "gate", "phylax", "boolean", "equals", True),
    ("authentication-refusal-named", "recovery", "gate", "elenchus", "boolean", "equals", True),
    ("child-processes-per-read", "time", "metric", "metron", "count", "minimise", None),
    ("buffered-bytes-per-read", "space", "metric", "metron", "bytes", "minimise", None),
    ("helper-shapes-authenticated", "compatibility", "metric", "protasis", "count", "maximise", None),
]

CONFORMANCE = [
    ("seam-reads-credentialed-remote", "correctness", "protasis", "boolean", "equals", True),
    ("sync-run-module-passes", "correctness", "elenchus", "boolean", "equals", True),
    ("local-reads-stay-native", "compatibility", "phylax", "boolean", "equals", True),
    ("projection-cap-refuses", "space", "phylax", "boolean", "equals", True),
    ("authentication-refusal-fixed", "recovery", "elenchus", "boolean", "equals", True),
    ("remote-read-children", "time", "metron", "count", "at-most", 2),
]

SELECTED = "credential-scope-projection"


def derived(kind: str, comparator: str, threshold, value) -> str:
    if kind == "metric":
        return "pass"
    if comparator == "equals":
        return "pass" if value == threshold else "fail"
    if comparator == "at-most":
        return "pass" if value <= threshold else "fail"
    return "pass" if value >= threshold else "fail"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if os.path.lexists(out):
        parser.error("--out must not already exist")
    base = out.parent

    criteria = []
    for criterion, concern, kind, owner, unit, comparator, threshold in SELECTION:
        criteria.append({
            "id": criterion, "concern": concern, "kind": kind, "stage": "selection",
            "owner": owner, "unit": unit, "comparator": comparator,
            "threshold": threshold, "blocks": "design-lock",
        })
    for criterion, concern, owner, unit, comparator, threshold in CONFORMANCE:
        criteria.append({
            "id": criterion, "concern": concern, "kind": "gate", "stage": "conformance",
            "owner": owner, "unit": unit, "comparator": comparator,
            "threshold": threshold, "blocks": "integration",
        })

    results = []
    for candidate in CANDIDATES:
        cid = candidate["id"]
        for criterion, _, kind, _, unit, comparator, threshold in SELECTION:
            relative = f"design/reports/selection/{cid}-{criterion}.json"
            data = (base / relative).read_bytes()
            report = json.loads(data)
            if (
                report.get("candidate") != cid
                or report.get("criterion") != criterion
                or report.get("unit") != unit
                or report.get("exit") != 0
            ):
                raise SystemExit(f"build_record: {relative} does not match its cell")
            results.append({
                "candidate": cid,
                "criterion": criterion,
                "state": derived(kind, comparator, threshold, report["value"]),
                "report": {"path": relative, "sha256": hashlib.sha256(data).hexdigest()},
            })
        for criterion, *_ in CONFORMANCE:
            relative = f"design/reports/conformance/{cid}-{criterion}.json"
            results.append({
                "candidate": cid,
                "criterion": criterion,
                "state": "pending",
                "resolver": (
                    f"python3 .hexaemeron/design/probe.py conform --candidate {cid} "
                    f"--criterion {criterion} --root . --out .hexaemeron/{relative}"
                ),
                "report": relative,
                "blocks": "integration",
            })

    record = {
        "schema": "protasis-design-evidence/v1",
        "candidates": CANDIDATES,
        "criteria": criteria,
        "results": results,
        "selection": {"candidate": SELECTED, "rule": "unique-frontier", "policy_ref": None},
    }
    data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with open(out, "xb") as handle:
        handle.write(data)
    print(f"wrote {out} sha256 {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
