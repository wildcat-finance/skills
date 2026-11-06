"""Evaluate the four venue-dispatch models; production conformance stays pending.

Every selection value is computed from a declared model of each candidate, not
asserted.  Both metrics count the members of a declared list, and the three
hard gates that discriminate are derived from the candidate's declared
dispatch, pin source and entry points.

This generation differs from the retired V2-only record in one place.  The run
now admits two Wildcat venues rather than one, so `venue-coupled-edit-sites`
counts the sites each candidate needs to admit both.  The per-venue cost
doubles for every design that adds a module or an operator table and stays flat
for the design that adds a second collector, which is the only place the
restored scope could have moved the ranking.  It does not: the counts become
4, 5, 5 and 5, and the same three candidates still fail a selection gate.
Eight conformance criteria replace the earlier five, because the restored scope
owes a V1 release, a shared-subject rule and a declared V1 source gap that the
V2-only record had no cell for.

This script writes the design record and its selection reports once.  It reads
no controller state and writes none.  Do not rerun it after the study is
receipted: it would rewrite a receipted report.
"""

from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
COMMAND = "python3 .hexaemeron/design/build_design_evidence.py"

CANDIDATES = (
    "venue-module-registry",
    "registry-format-dispatch",
    "venue-parameter-table",
    "separate-wildcat-collector",
)

SUMMARIES = {
    "venue-module-registry": (
        "One VENUES table keyed by the plan's venue; each module owns its "
        "registry pin, subject set, epoch model and coverage gaps."
    ),
    "registry-format-dispatch": (
        "Dispatch on the registry document's own format string rather than on "
        "the plan's declared venue."
    ),
    "venue-parameter-table": (
        "Keep one code path and supply the subject set, epoch parameters and "
        "digest as an operator-side parameter document per estate."
    ),
    "separate-wildcat-collector": (
        "Leave usdc_interval.py untouched and ship a second collector serving "
        "both Wildcat estates."
    ),
}

SPECS = {
    "venue-module-registry": {
        "dispatch": "plan-venue",
        "pin_source": "reviewed-code",
        "entry_points": ["usdc_interval.py build", "usdc_interval.py check"],
        "dispatch_inputs": ["plan.venue"],
        "edit_sites": [
            "alexandria_lib/venues/wildcat_v1.py, a new module",
            "alexandria_lib/venues/wildcat_v2.py, a new module",
            "alexandria_lib/venues/__init__.py, the wildcat-v1 VENUES row",
            "alexandria_lib/venues/__init__.py, the wildcat-v2 VENUES row",
        ],
        "components_added": [],
    },
    "registry-format-dispatch": {
        "dispatch": "registry-format",
        "pin_source": "reviewed-code",
        "entry_points": ["usdc_interval.py build", "usdc_interval.py check"],
        "dispatch_inputs": ["registry.format"],
        "edit_sites": [
            "alexandria_lib/venues/wildcat_v1.py, a new module",
            "alexandria_lib/venues/wildcat_v2.py, a new module",
            "alexandria_lib/venues/__init__.py, the wildcat-v1 FORMATS row",
            "alexandria_lib/venues/__init__.py, the wildcat-v2 FORMATS row",
            "usdc_interval.py _gaps, the Compound-shaped registry branch",
        ],
        "components_added": [],
    },
    "venue-parameter-table": {
        "dispatch": "none",
        "pin_source": "operator-document",
        "entry_points": ["usdc_interval.py build", "usdc_interval.py check"],
        "dispatch_inputs": ["wildcat-v1-parameters.json", "wildcat-v2-parameters.json"],
        "edit_sites": [
            "wildcat-v1-parameters.json, a new operator table",
            "wildcat-v2-parameters.json, a new operator table",
            "interval.py, the epoch-derivation branch",
            "usdc_interval.py _gaps, the Compound-shaped registry branch",
            "usdc_interval.py, the plan-to-table binding check",
        ],
        "components_added": ["venue-parameters"],
    },
    "separate-wildcat-collector": {
        "dispatch": "plan-venue",
        "pin_source": "reviewed-code",
        "entry_points": [
            "usdc_interval.py build", "usdc_interval.py check",
            "wildcat_interval.py build", "wildcat_interval.py check",
        ],
        "dispatch_inputs": ["plan.venue"],
        "edit_sites": [
            "scripts/wildcat_interval.py, a new collector serving both estates",
            "tests/test_wildcat_interval.py, a new suite",
            "examples/wildcat-interval-v0, a new demonstration",
            "schemas/, a new plan and receipt schema",
            "tests/test_demonstrations.py, the demonstration registration",
        ],
        "components_added": [],
    },
}

EXISTING_ENTRY_POINTS = ["usdc_interval.py build", "usdc_interval.py check"]


def values_for(candidate: str) -> dict:
    spec = SPECS[candidate]
    return {
        "existing-build-check-path": spec["entry_points"] == EXISTING_ENTRY_POINTS,
        # Only a design that takes its venue from the plan has two independent
        # declarations to compare; one that derives the venue from the registry
        # has nothing left to disagree with it.
        "venue-registry-agreement-checked": spec["dispatch"] == "plan-venue",
        "venue-pin-in-reviewed-code": spec["pin_source"] == "reviewed-code",
        "scope-decision-invariant": (
            "staging-byte-provenance" not in spec["dispatch_inputs"]
        ),
        "venue-coupled-edit-sites": len(spec["edit_sites"]),
        "new-release-components": len(spec["components_added"]),
    }


def criterion(name, concern, kind, stage, owner):
    return {
        "blocks": "integration" if stage == "conformance" else "design-lock",
        "comparator": "minimise" if kind == "metric" else "equals",
        "concern": concern,
        "id": name,
        "kind": kind,
        "owner": owner,
        "stage": stage,
        "threshold": None if kind == "metric" else True,
        "unit": "count" if kind == "metric" else "boolean",
    }


CRITERIA = [
    criterion("existing-build-check-path", "compatibility", "gate", "selection", "protasis"),
    criterion("venue-registry-agreement-checked", "correctness", "gate", "selection", "protasis"),
    criterion("venue-pin-in-reviewed-code", "recovery", "gate", "selection", "phylax"),
    criterion("scope-decision-invariant", "compatibility", "gate", "selection", "protasis"),
    criterion("venue-coupled-edit-sites", "time", "metric", "selection", "metron"),
    criterion("new-release-components", "space", "metric", "selection", "metron"),
    criterion("compound-path-still-builds", "compatibility", "gate", "conformance", "protasis"),
    criterion("wildcat-v2-plan-builds-and-checks", "correctness", "gate", "conformance", "protasis"),
    criterion("wildcat-v1-plan-builds-and-checks", "correctness", "gate", "conformance", "protasis"),
    criterion("shared-subject-attributed-per-venue", "correctness", "gate", "conformance", "protasis"),
    criterion("v1-source-gap-declared", "correctness", "gate", "conformance", "protasis"),
    criterion("constructed-staging-declared-in-coverage", "correctness", "gate", "conformance", "protasis"),
    criterion("undeclared-venue-refuses", "recovery", "gate", "conformance", "elenchus"),
    criterion("component-budget-respected", "space", "gate", "conformance", "metron"),
]


def encode(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    record = {
        "candidates": [{"id": n, "summary": SUMMARIES[n]} for n in CANDIDATES],
        "criteria": CRITERIA,
        "results": [],
        "schema": "protasis-design-evidence/v1",
        "selection": {
            "candidate": "venue-module-registry",
            "policy_ref": None,
            "rule": "unique-frontier",
        },
    }
    observations = {}
    for candidate in CANDIDATES:
        values = values_for(candidate)
        observations[candidate] = {"spec": SPECS[candidate], "values": values}
        for item in CRITERIA:
            name = item["id"]
            if item["stage"] == "conformance":
                record["results"].append({
                    "blocks": "integration",
                    "candidate": candidate,
                    "criterion": name,
                    "report": f"reports/conformance/{candidate}-{name}.json",
                    "resolver": (
                        "python3 .hexaemeron/design/conformance.py "
                        f"{name} --candidate {candidate}"
                    ),
                    "state": "pending",
                })
                continue
            value = values[name]
            payload = encode({
                "candidate": candidate,
                "command": COMMAND,
                "criterion": name,
                "exit": 0,
                "schema": "protasis-design-report/v1",
                "unit": item["unit"],
                "value": value,
            })
            relative = f"reports/selection/{candidate}-{name}.json"
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            record["results"].append({
                "candidate": candidate,
                "criterion": name,
                "report": {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()},
                "state": "fail" if value is False else "pass",
            })
    (ROOT / "design" / "model-observations.json").write_bytes(encode(observations))
    (ROOT / "design-evidence.json").write_bytes(encode(record))
    print(json.dumps({n: d["values"] for n, d in observations.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
