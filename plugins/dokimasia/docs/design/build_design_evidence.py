"""Rebuild the Dokimasia design record and its selection reports.

Every selection value is measured from a candidate's declared artefact rather
than asserted in the record, so the record can be regenerated and compared byte
for byte. Nothing here runs the skill: conformance evidence stays pending until
the step that earns it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CANDIDATES = ("inventory-first", "harness-emitter", "resident-driver")

GATES = (
    ("source-and-oracle-bound", "correctness", "protasis", "closes_the_coverage_question"),
    ("browser-free-check", "correctness", "protasis", "checkable_without_a_browser"),
    ("no-signer-authority", "compatibility", "phylax", "no_signer_authority"),
    ("kill-resumable", "recovery", "elenchus", "resumable_after_a_kill"),
)
METRICS = (
    ("runbook-step-count", "time", "metron", "count", "steps"),
    ("new-runtime-dependencies", "space", "metron", "count", "runtime_dependencies"),
)
CONFORMANCE = (
    ("scaffold-contract-check", "correctness", "protasis", "step:2",
     "python3 scripts/run_checks.py --scope dokimasia"),
    ("inventory-determinism", "recovery", "elenchus", "step:3",
     "python3 plugins/dokimasia/scripts/dokimasia.py inventory --check"),
    ("workbook-roundtrip", "correctness", "elenchus", "step:4",
     "python3 plugins/dokimasia/scripts/dokimasia.py workbook --check"),
    ("disposition-closure", "correctness", "protasis", "step:5",
     "python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check"),
    ("pinned-demonstration", "compatibility", "phylax", "integration",
     "python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check"),
)

REPORT_COMMAND = (
    "python3 .hexaemeron/design/build_design_evidence.py"
)


def canonical(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    reports_dir = HERE.parent / "reports" / "selection"
    reports_dir.mkdir(parents=True, exist_ok=True)
    declared = {
        name: json.loads((HERE / "candidates" / f"{name}.json").read_text("utf-8"))
        for name in CANDIDATES
    }

    results = []
    for name in CANDIDATES:
        spec = declared[name]
        for criterion, _concern, _owner, field in GATES:
            value = bool(spec[field])
            results.append(write_report(reports_dir, name, criterion, "boolean", value))
        for criterion, _concern, _owner, unit, field in METRICS:
            value = len(spec[field])
            results.append(write_report(reports_dir, name, criterion, unit, value))
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
            "id": criterion, "concern": concern, "kind": "gate",
            "stage": "selection", "owner": owner, "unit": "boolean",
            "comparator": "equals", "threshold": True, "blocks": "design-lock",
        })
    for criterion, concern, owner, unit, _field in METRICS:
        criteria.append({
            "id": criterion, "concern": concern, "kind": "metric",
            "stage": "selection", "owner": owner, "unit": unit,
            "comparator": "minimise", "threshold": None, "blocks": "design-lock",
        })
    for criterion, concern, owner, blocks, _resolver in CONFORMANCE:
        criteria.append({
            "id": criterion, "concern": concern, "kind": "gate",
            "stage": "conformance", "owner": owner, "unit": "boolean",
            "comparator": "equals", "threshold": True, "blocks": blocks,
        })

    record = {
        "schema": "protasis-design-evidence/v1",
        "candidates": [
            {"id": name, "summary": declared[name]["summary"]} for name in CANDIDATES
        ],
        "criteria": criteria,
        "results": results,
        "selection": {
            "candidate": "inventory-first",
            "rule": "unique-frontier",
            "policy_ref": None,
        },
    }
    (HERE.parent / "design-evidence.json").write_text(canonical(record), "utf-8")
    return 0


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
    state = "pass"
    if unit == "boolean" and value is not True:
        state = "fail"
    return {
        "candidate": candidate,
        "criterion": criterion,
        "state": state,
        "report": {"path": relative, "sha256": digest(body)},
    }


if __name__ == "__main__":
    raise SystemExit(main())
