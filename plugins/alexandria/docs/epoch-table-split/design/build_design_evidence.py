#!/usr/bin/env python3
"""Compose the issue 1888 design record from the selection reports on disk.

Run from the root of the run worktree:

    python3 .hexaemeron/design/build_design_evidence.py --out .hexaemeron/design-evidence.json

Each resolved cell binds one report under `.hexaemeron/design/reports/selection/`
by path and SHA-256, and its state is derived from the report's value and the
criterion's comparator rather than written by hand. Each conformance cell stays
pending with its exact resolver, future report path and stop point. The output
path must not exist, so a receipted record is never replaced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD_DIR = HERE.parent

CANDIDATES = [
    {"id": "split-attribution-parts", "summary": (
        "A v2 plan field log_attribution_parts, value journal-ranges, moves log_attributions "
        "into log-attributions.<k> components at the plan's journal ranges under receipt v4; "
        "check compares each part with the rows attribute_logs derives for its shards. "
        "MAX_COMPONENTS and MAX_CAPTURES rise to 16,384; manifests and capture plans read "
        "under 128 MiB and 2,000,000 nodes; the collector checkpoint under 2,000,000 nodes.")},
    {"id": "compact-attribution-rows", "summary": (
        "One epoch table whose rows drop block_hash and transaction_hash, which check "
        "re-derives from the logs journal, declared by a plan field under a new receipt "
        "format. The component and capture caps and the manifest limits rise as in the "
        "split, so journals can grow.")},
    {"id": "raised-epoch-table-ceiling", "summary": (
        "One epoch table as today, with that component's own ceiling raised to 8 GiB and "
        "200,000,000 nodes while every other component keeps 64 MiB. The component and "
        "capture caps and the manifest limits rise as in the split.")},
    {"id": "plan-sized-releases", "summary": (
        "No format change. Every plan stays under about 202,000 preserved logs so its one "
        "epoch table fits 64 MiB, and a venue ships as many releases, joined later by the "
        "collection manifest issue 1373 owns.")},
]


def gate(identifier, concern, owner, unit, comparator, threshold, stage="selection",
         blocks="design-lock"):
    return {"id": identifier, "concern": concern, "kind": "gate", "stage": stage,
            "owner": owner, "unit": unit, "comparator": comparator,
            "threshold": threshold, "blocks": blocks}


def metric(identifier, concern, owner, unit):
    return {"id": identifier, "concern": concern, "kind": "metric", "stage": "selection",
            "owner": owner, "unit": unit, "comparator": "minimise", "threshold": None,
            "blocks": "design-lock"}


CRITERIA = [
    gate("fitting-plans-keep-todays-path", "compatibility", "protasis", "boolean", "equals", True),
    gate("older-verifier-refuses-by-name", "compatibility", "phylax", "boolean", "equals", True),
    gate("component-ceiling-kept", "space", "metron", "bytes", "at-most", 67_108_864),
    gate("aave-interval-in-one-release", "space", "metron", "count", "at-most", 1),
    gate("attribution-bound-fixed-by-the-plan", "recovery", "elenchus", "boolean", "equals", True),
    metric("edit-sites", "time", "protasis", "count"),
    metric("sites-shared-with-1872", "compatibility", "protasis", "count"),
    metric("manifest-bytes-at-cap", "space", "metron", "bytes"),
    metric("aave-release-check-peak", "space", "metron", "bytes"),
    gate("split-parts-rederive-and-refuse", "correctness", "elenchus", "boolean", "equals", True,
         stage="conformance", blocks="step:3"),
    gate("release-limits-hold-at-the-cap", "correctness", "protasis", "boolean", "equals", True,
         stage="conformance", blocks="step:4"),
    gate("split-release-over-128-components", "correctness", "protasis", "boolean", "equals",
         True, stage="conformance", blocks="step:4"),
    gate("pinned-release-identities-reproduce", "compatibility", "protasis", "boolean",
         "equals", True, stage="conformance", blocks="integration"),
]
SELECTION = {"candidate": "split-attribution-parts", "rule": "unique-frontier",
             "policy_ref": None}


def derived_state(criterion, value) -> str:
    if criterion["kind"] == "metric":
        return "pass"
    threshold = criterion["threshold"]
    if criterion["comparator"] == "equals":
        return "pass" if value == threshold else "fail"
    if criterion["comparator"] == "at-most":
        return "pass" if value <= threshold else "fail"
    return "pass" if value >= threshold else "fail"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    results = []
    for candidate in CANDIDATES:
        for criterion in CRITERIA:
            name = f"{candidate['id']}-{criterion['id']}.json"
            if criterion["stage"] == "conformance":
                results.append({
                    "blocks": criterion["blocks"], "candidate": candidate["id"],
                    "criterion": criterion["id"],
                    "report": f"design/reports/conformance/{name}",
                    "resolver": (f"python3 .hexaemeron/design/conformance.py {criterion['id']} "
                                 f"--candidate {candidate['id']}"),
                    "state": "pending",
                })
                continue
            relative = f"design/reports/selection/{name}"
            data = (RECORD_DIR / relative).read_bytes()
            report = json.loads(data)
            if (report["candidate"], report["criterion"]) != (candidate["id"], criterion["id"]):
                raise SystemExit(f"{relative} names another cell")
            results.append({
                "candidate": candidate["id"], "criterion": criterion["id"],
                "report": {"path": relative, "sha256": hashlib.sha256(data).hexdigest()},
                "state": derived_state(criterion, report["value"]),
            })
    record = {"candidates": CANDIDATES, "criteria": CRITERIA, "results": results,
              "schema": "protasis-design-evidence/v1", "selection": SELECTION}
    data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    target = Path(args.out)
    if os.path.lexists(target):
        raise SystemExit(f"{target} already exists; the record is never replaced")
    with open(target, "xb") as handle:
        handle.write(data)
    print(hashlib.sha256(data).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
