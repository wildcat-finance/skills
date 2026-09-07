"""Rebuild the alexandria-1 design record and its selection reports.

Every selection value is read from a candidate's declared artefact under
`candidates/` rather than typed into the record, so the record regenerates
byte for byte. Nothing here opens a socket or runs the collector: the
conformance evidence stays pending until the runbook step that earns it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD_DIR = HERE.parent
CANDIDATES = (
    "opening-reads-in-collect",
    "epochs-subcommand",
    "operator-supplied-evidence",
    "trace-mandatory",
)
SELECTED = "opening-reads-in-collect"

GATES = (
    ("start-hash-from-collector-read", "correctness", "protasis", "start_hash_from_collector_read"),
    ("code-read-journaled", "correctness", "phylax", "code_read_journaled"),
    ("code-rechecked-offline", "correctness", "protasis", "code_rechecked_offline"),
    ("reachable-provider-pair", "compatibility", "phylax", "reachable_provider_pair"),
    ("resume-safe-after-kill", "recovery", "elenchus", "resume_safe_after_kill"),
)
METRICS = (
    ("network-commands", "time", "metron", "count", "network_commands"),
    ("new-release-components", "space", "metron", "count", "new_release_components"),
)
CONFORMANCE = (
    ("finality-rebinds-after-tag-advance", "recovery", "elenchus", "step:2",
     "python3 .hexaemeron/design/conformance.py finality-rebinds-after-tag-advance"),
    ("opening-reads-resumable", "recovery", "elenchus", "step:3",
     "python3 .hexaemeron/design/conformance.py opening-reads-resumable"),
    ("scope-binds-both-hashes", "correctness", "protasis", "step:4",
     "python3 .hexaemeron/design/conformance.py scope-binds-both-hashes"),
    ("code-hash-rechecked-from-component", "correctness", "protasis", "step:4",
     "python3 .hexaemeron/design/conformance.py code-hash-rechecked-from-component"),
    ("live-interval-reconciled", "compatibility", "phylax", "step:5",
     "python3 .hexaemeron/design/conformance.py live-interval-reconciled"),
    ("demo-reproduces-live-release-id", "correctness", "protasis", "integration",
     "python3 .hexaemeron/design/conformance.py demo-reproduces-live-release-id"),
)
REPORT_COMMAND = "python3 .hexaemeron/design/build_design_evidence.py"


def canonical(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_report(reports_dir: Path, candidate: str, criterion: str, unit: str, value) -> dict:
    body = canonical({
        "candidate": candidate,
        "command": REPORT_COMMAND,
        "criterion": criterion,
        "exit": 0,
        "schema": "protasis-design-report/v1",
        "unit": unit,
        "value": value,
    })
    relative = f"reports/selection/{candidate}-{criterion}.json"
    (reports_dir / f"{candidate}-{criterion}.json").write_text(body, "utf-8")
    state = "fail" if unit == "boolean" and value is not True else "pass"
    return {
        "candidate": candidate,
        "criterion": criterion,
        "state": state,
        "report": {"path": relative, "sha256": digest(body)},
    }


def main() -> int:
    reports_dir = RECORD_DIR / "reports" / "selection"
    reports_dir.mkdir(parents=True, exist_ok=True)
    declared = {
        name: json.loads((HERE / "candidates" / f"{name}.json").read_text("utf-8"))
        for name in CANDIDATES
    }
    results = []
    for name in CANDIDATES:
        spec = declared[name]
        for criterion, _concern, _owner, field in GATES:
            results.append(write_report(reports_dir, name, criterion, "boolean", bool(spec[field])))
        for criterion, _concern, _owner, unit, field in METRICS:
            results.append(write_report(reports_dir, name, criterion, unit, len(spec[field])))
        for criterion, _concern, _owner, blocks, resolver in CONFORMANCE:
            results.append({
                "candidate": name,
                "criterion": criterion,
                "state": "pending",
                "resolver": resolver,
                "report": f"reports/conformance/{name}-{criterion}.json",
                "blocks": blocks,
            })
    criteria = []
    for criterion, concern, owner, _field in GATES:
        criteria.append({
            "id": criterion, "concern": concern, "kind": "gate", "stage": "selection",
            "owner": owner, "unit": "boolean", "comparator": "equals", "threshold": True,
            "blocks": "design-lock",
        })
    for criterion, concern, owner, unit, _field in METRICS:
        criteria.append({
            "id": criterion, "concern": concern, "kind": "metric", "stage": "selection",
            "owner": owner, "unit": unit, "comparator": "minimise", "threshold": None,
            "blocks": "design-lock",
        })
    for criterion, concern, owner, blocks, _resolver in CONFORMANCE:
        criteria.append({
            "id": criterion, "concern": concern, "kind": "gate", "stage": "conformance",
            "owner": owner, "unit": "boolean", "comparator": "equals", "threshold": True,
            "blocks": blocks,
        })
    record = {
        "schema": "protasis-design-evidence/v1",
        "candidates": [{"id": name, "summary": declared[name]["summary"]} for name in CANDIDATES],
        "criteria": criteria,
        "results": results,
        "selection": {"candidate": SELECTED, "rule": "unique-frontier", "policy_ref": None},
    }
    (RECORD_DIR / "design-evidence.json").write_text(canonical(record), "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
