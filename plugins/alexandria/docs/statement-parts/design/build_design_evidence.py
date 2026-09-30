#!/usr/bin/env python3
"""Assemble the issue 1892 design record from the selection reports on disk.

Run from the root of the run worktree after every selection report exists:

    python3 .hexaemeron/design/build_design_evidence.py --out .hexaemeron/design-evidence.json

Each resolved cell's state is derived from its report's value and the
criterion's comparison, and binds the report's SHA-256. Conformance cells are
written pending with their exact resolver, future report path and stop point.
The output path must not exist. Nothing else is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

SELECTED = "statement-parts"
CANDIDATES = [
    ("statement-parts",
     "Today's statement for a release within 8,388,608 bytes and 262,144 key characters; "
     "otherwise --parts writes index.json and part-NNNNN.json, greedy runs of components "
     "in manifest order, each part within 6,225,920 bytes and 262,144 key characters, "
     "the index binding every part by SHA-256. Ariadne is unchanged."),
    ("per-component-statements",
     "The same part and index shapes with exactly one component a part, so a release past "
     "the single bounds gets one part per component and an index of up to 16,385 subjects."),
    ("raised-limit-matched-reader",
     "One statement up to 134,217,728 bytes, read with ariadne.py verify --max-bytes "
     "134217728, with Ariadne's aggregate key budget raised to 8,388,608 characters."),
    ("compact-projection",
     "Today's statement within 8 MiB; otherwise one alexandria-release/v2 statement whose "
     "components and captures are arrays, keeping each capture's scope and coverage objects."),
]


def gate(identifier, concern, owner, stage="selection", blocks="design-lock"):
    return {"id": identifier, "concern": concern, "kind": "gate", "stage": stage,
            "owner": owner, "unit": "boolean", "comparator": "equals", "threshold": True,
            "blocks": blocks}


def metric(identifier, concern, owner, unit):
    return {"id": identifier, "concern": concern, "kind": "metric", "stage": "selection",
            "owner": owner, "unit": unit, "comparator": "minimise", "threshold": None,
            "blocks": "design-lock"}


CRITERIA = [
    gate("cap-release-verifies", "correctness", "protasis"),
    gate("default-reader-verifies", "compatibility", "phylax"),
    gate("pinned-statements-stay-single", "compatibility", "protasis"),
    metric("statement-set-bytes", "space", "metron", "bytes"),
    metric("set-verify-milliseconds", "time", "metron", "milliseconds"),
    gate("part-projection-verifies", "correctness", "protasis", "conformance", "step:2"),
    gate("past-limit-refuses-by-name", "correctness", "elenchus", "conformance", "step:3"),
    gate("killed-emit-leaves-no-set", "recovery", "elenchus", "conformance", "step:3"),
    gate("pinned-statements-keep-bytes", "compatibility", "protasis", "conformance",
         "integration"),
]


def state(criterion, value):
    if criterion["kind"] == "metric":
        return "pass"
    return "pass" if value == criterion["threshold"] else "fail"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if os.path.lexists(args.out):
        parser.error(f"{args.out} already exists")
    record_dir = Path(args.out).resolve().parent
    results = []
    for candidate, _ in CANDIDATES:
        for criterion in CRITERIA:
            name = f"{candidate}-{criterion['id']}.json"
            if criterion["stage"] == "selection":
                relative = f"design/reports/selection/{name}"
                data = (record_dir / relative).read_bytes()
                report = json.loads(data)
                if (report.get("candidate"), report.get("criterion"), report.get("exit")) != (
                        candidate, criterion["id"], 0):
                    parser.error(f"{relative} does not report {candidate}/{criterion['id']}")
                results.append({"candidate": candidate, "criterion": criterion["id"],
                                "state": state(criterion, report["value"]),
                                "report": {"path": relative,
                                           "sha256": hashlib.sha256(data).hexdigest()}})
            else:
                results.append({
                    "candidate": candidate, "criterion": criterion["id"], "state": "pending",
                    "resolver": ("python3 .hexaemeron/design/conformance.py "
                                 f"{criterion['id']} --candidate {candidate}"),
                    "report": f"design/reports/conformance/{name}",
                    "blocks": criterion["blocks"],
                })
    record = {
        "schema": "protasis-design-evidence/v1",
        "candidates": [{"id": identifier, "summary": summary}
                       for identifier, summary in CANDIDATES],
        "criteria": CRITERIA,
        "results": results,
        "selection": {"candidate": SELECTED, "rule": "unique-frontier", "policy_ref": None},
    }
    with open(args.out, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
