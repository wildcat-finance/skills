#!/usr/bin/env python3
"""Assemble the issue-1480 design record from the reports beside it.

usage: build_record.py --reports DIR --out PATH

Reads every `protasis-design-report/v1` report the resolver wrote under
`--reports`, binds each by path and SHA-256, adds the one pending conformance
cell per candidate, and writes the closed `protasis-design-evidence/v1` record
to `--out`. The record path must be new; report paths are recorded relative to
the record's directory. Nothing else is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

RECORD_SCHEMA = "protasis-design-evidence/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
CONTROLLER_FILES = frozenset({"state.json", "ledger.jsonl", "lock"})
MAX_REPORT_BYTES = 64 * 1024

CANDIDATES = [
    {
        "id": "gained-range-ownership",
        "summary": (
            "For every unmerged step whose remote tip left its receipted head, "
            "enumerate the gained range once natively and refuse when it holds a "
            "commit another step's push receipt owns."
        ),
    },
    {
        "id": "owned-commit-ancestry",
        "summary": (
            "For every unmerged lower step, ask native ancestry once per commit "
            "owned by every higher step's push receipt against the lower tip."
        ),
    },
    {
        "id": "pull-request-merge-state",
        "summary": (
            "Read each unmerged step's pull request from GitHub and refuse when "
            "it reports merged into a base that is not the run branch."
        ),
    },
    {
        "id": "merge-time-only",
        "summary": (
            "Leave next unchanged and refuse at done merge-step when the exact "
            "repaired range holds a commit another step's receipt owns."
        ),
    },
]

GATE = "gate"
METRIC = "metric"
CRITERIA = [
    ("refuses-whole-carry", "correctness", GATE, "boolean", "equals", True, "elenchus", "selection", "design-lock"),
    ("refuses-partial-carry", "correctness", GATE, "boolean", "equals", True, "elenchus", "selection", "design-lock"),
    ("admits-honest-extension", "correctness", GATE, "boolean", "equals", True, "elenchus", "selection", "design-lock"),
    ("admits-adopted-early-merge", "compatibility", GATE, "boolean", "equals", True, "fiat", "selection", "design-lock"),
    ("no-new-github-reads", "compatibility", GATE, "boolean", "equals", True, "phylax", "selection", "design-lock"),
    ("added-native-processes-per-next", "time", METRIC, "count", "minimise", None, "metron", "selection", "design-lock"),
    ("max-child-output-bytes", "space", GATE, "bytes", "at-most", 2097152, "metron", "selection", "design-lock"),
    ("unknown-refuses-as-unknown", "recovery", GATE, "boolean", "equals", True, "elenchus", "selection", "design-lock"),
    ("product-refuses-specimen-stack", "correctness", GATE, "boolean", "equals", True, "elenchus", "conformance", "step:4"),
]
CONFORMANCE = "product-refuses-specimen-stack"


def checked_out(path_text: str) -> Path:
    path = Path(path_text)
    if path.suffix != ".json" or path.name in CONTROLLER_FILES:
        raise SystemExit("--out must name a new .json record, not a controller file")
    if path.exists() or path.is_symlink():
        raise SystemExit("--out must not already exist")
    if not path.parent.is_dir():
        raise SystemExit("--out parent directory does not exist")
    return path


def read_report(path: Path) -> tuple[dict, str]:
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f"report {path} is not a regular file")
    data = path.read_bytes()
    if len(data) > MAX_REPORT_BYTES:
        raise SystemExit(f"report {path} exceeds {MAX_REPORT_BYTES} bytes")
    report = json.loads(data)
    if not isinstance(report, dict) or report.get("schema") != REPORT_SCHEMA:
        raise SystemExit(f"report {path} is not one {REPORT_SCHEMA} object")
    return report, hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--reports", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = checked_out(args.out)
    reports_dir = Path(args.reports)
    if reports_dir.is_symlink() or not reports_dir.is_dir():
        raise SystemExit("--reports must name a directory")
    record_dir = out.parent.resolve()
    criteria = []
    for identifier, concern, kind, unit, comparator, threshold, owner, stage, blocks in CRITERIA:
        criteria.append({
            "id": identifier,
            "concern": concern,
            "kind": kind,
            "stage": stage,
            "owner": owner,
            "unit": unit,
            "comparator": comparator,
            "threshold": threshold,
            "blocks": blocks,
        })
    results = []
    for candidate in CANDIDATES:
        for criterion in criteria:
            name = f"{candidate['id']}-{criterion['id']}.json"
            relative = os.path.relpath((reports_dir / name).resolve(), record_dir)
            if criterion["id"] == CONFORMANCE:
                results.append({
                    "candidate": candidate["id"],
                    "criterion": criterion["id"],
                    "state": "pending",
                    "resolver": (
                        "python3 .hexaemeron/design/conform_carry.py --candidate "
                        f"{candidate['id']} --out .hexaemeron/{relative}"
                    ),
                    "report": relative,
                    "blocks": criterion["blocks"],
                })
                continue
            report, digest = read_report(reports_dir / name)
            if report["candidate"] != candidate["id"] or report["criterion"] != criterion["id"]:
                raise SystemExit(f"report {name} names another cell")
            value = report["value"]
            comparator = criterion["comparator"]
            if criterion["kind"] == GATE:
                if comparator == "equals":
                    passed = value == criterion["threshold"]
                elif comparator == "at-most":
                    passed = value <= criterion["threshold"]
                else:
                    passed = value >= criterion["threshold"]
                state = "pass" if passed else "fail"
            else:
                state = "pass"
            results.append({
                "candidate": candidate["id"],
                "criterion": criterion["id"],
                "state": state,
                "report": {"path": relative, "sha256": digest},
            })
    record = {
        "schema": RECORD_SCHEMA,
        "candidates": CANDIDATES,
        "criteria": criteria,
        "results": results,
        "selection": {
            "candidate": "gained-range-ownership",
            "rule": "unique-frontier",
            "policy_ref": None,
        },
    }
    data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("ascii")
    with open(out, "xb") as handle:
        handle.write(data)
    print(f"{out} {hashlib.sha256(data).hexdigest()} results={len(results)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
