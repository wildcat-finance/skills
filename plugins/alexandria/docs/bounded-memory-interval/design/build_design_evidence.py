#!/usr/bin/env python3
"""Compose the issue 1891 design record from the selection reports on disk.

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
HOST_BYTES = 137_438_953_472
# The acceptance peak the study states, for build and for check, each measured
# as /usr/bin/time -l maximum resident set size.
STATED_PEAK = 4_294_967_296
# Half the median base check peak on the preserved V2 release (1,240,547,328).
V2_PEAK_CEILING = 620_273_664
# Twice the median base check CPU time (user plus system) on the V2 release.
V2_CPU_CEILING_MS = 9_400

CANDIDATES = [
    {"id": "plan-sized-releases", "summary": (
        "No code change. Build and check keep today's memory model, about 5.11 times a "
        "release's bytes on Wildcat V2, and a venue ships as many releases as the host can "
        "check, joined later by the collection manifest issue 1373 owns.")},
    {"id": "stream-bytes-hold-logs", "summary": (
        "Build writes and check reads one component at a time and drops its bytes and parsed "
        "document afterwards, but both still hold every parsed log and every attribution row, "
        "as today, for the opening replay and the row comparison.")},
    {"id": "compact-log-index", "summary": (
        "One component at a time, plus a compact in-memory index of every preserved log "
        "(position, subject, shared block and transaction hashes, first topic) that the "
        "opening replay, the epochs and the row derivation read after the journal pass.")},
    {"id": "range-streamed-logs", "summary": (
        "One component at a time. A shared log walk validates positions and derives rows "
        "range by range with bounded state and an 8-byte key per transaction; venues see only "
        "the logs whose topic they declare; check attributes each range with the receipt's "
        "epochs and holds any refusal until today's point; build reads staged logs twice.")},
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


def conformance(identifier, concern, owner, unit, comparator, threshold, blocks):
    return gate(identifier, concern, owner, unit, comparator, threshold,
                stage="conformance", blocks=blocks)


CRITERIA = [
    gate("aave-interval-checks-on-host", "space", "metron", "bytes", "at-most", HOST_BYTES),
    gate("format-limit-release-checks-on-host", "space", "metron", "bytes", "at-most", HOST_BYTES),
    gate("one-component-at-a-time", "space", "metron", "bytes", "at-most", 16),
    metric("extra-journal-bytes-read", "time", "metron", "bytes"),
    metric("edit-sites", "time", "protasis", "count"),
    metric("sites-shared-with-1872", "compatibility", "protasis", "count"),
    conformance("todays-model-projects-past-the-host", "space", "metron", "bytes",
                "at-least", HOST_BYTES, "step:2"),
    conformance("walk-matches-whole-list-derivation", "correctness", "elenchus", "boolean",
                "equals", True, "step:3"),
    conformance("streamed-check-keeps-every-refusal", "correctness", "elenchus", "boolean",
                "equals", True, "step:4"),
    conformance("check-peak-independent-of-size", "space", "metron", "boolean",
                "equals", True, "step:4"),
    conformance("build-peak-independent-of-size", "space", "metron", "boolean",
                "equals", True, "step:5"),
    conformance("killed-build-installs-nothing", "recovery", "elenchus", "boolean",
                "equals", True, "step:5"),
    conformance("acceptance-release-within-stated-peak", "space", "metron", "bytes",
                "at-most", STATED_PEAK, "integration"),
    conformance("v2-check-peak-halved", "space", "metron", "bytes",
                "at-most", V2_PEAK_CEILING, "integration"),
    conformance("v2-check-cpu-within-budget", "time", "metron", "milliseconds",
                "at-most", V2_CPU_CEILING_MS, "integration"),
    conformance("pinned-release-identities-reproduce", "compatibility", "protasis", "boolean",
                "equals", True, "integration"),
]
SELECTION = {"candidate": "range-streamed-logs", "rule": "unique-frontier", "policy_ref": None}


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
