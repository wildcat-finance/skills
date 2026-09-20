#!/usr/bin/env python3
"""Measure the declared study models; this is not product conformance."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).with_name("candidate-models.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text())
    candidate = catalog["candidates"][args.candidate]
    rows = catalog["sample_sources"]
    if candidate["classification"] == "all-regressions":
        projected = [dict(row, declared_current_obligation="local-regression") for row in rows]
    else:
        projected = [dict(row, declared_current_obligation=row["reviewed_applicability"]) for row in rows]
    values = {
        "source-state-distinction": (all(row["declared_current_obligation"] == row["reviewed_applicability"] for row in projected), "boolean"),
        "controller-owned-observation": (candidate["execution_owner"] == "existing-criteria-execution", "boolean"),
        "unchanged-parent-boundary": (not candidate["changes_elenchus_runner"], "boolean"),
        "new-execution-engines": (candidate["new_execution_engines"], "count"),
        "sample-representation-bytes": (len(json.dumps(projected, sort_keys=True, separators=(",", ":")).encode()), "bytes"),
    }
    value, unit = values[args.criterion]
    report = {
        "schema": "protasis-design-report/v1", "candidate": args.candidate,
        "criterion": args.criterion, "value": value, "unit": unit,
        "command": f"python3 .hexaemeron/research/design_probe.py --candidate {args.candidate} --criterion {args.criterion} --report {args.report}",
        "exit": 0,
    }
    target = ROOT / args.report
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"candidate": args.candidate, "criterion": args.criterion, "value": value, "unit": unit, "report_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
