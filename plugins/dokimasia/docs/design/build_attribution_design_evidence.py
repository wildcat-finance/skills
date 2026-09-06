#!/usr/bin/env python3
"""Build the design record for Dokimasia's attributed-confirmation frontier.

The record is the selection interface; the study's prose explains the
candidates but decides nothing. Every selection cell resolves to a committed
`protasis-design-report/v1` report, and every conformance cell names the exact
resolver that will produce it at the transition it blocks.

Run this from the repository root, which is the path each report records as its
`command`. The `--record` default is the committed record, so the bare command
each report names regenerates the artefact it documents; findings S1-R1-01 of
the first Dokimasia run and S1-R1-02 of the second both recorded a command
whose default wrote somewhere else.

One metric is measured rather than declared. `rule-statements-on-pinned-set`
builds each candidate's attribution shape over the committed disposition set
at `docs/evidence/wildcat-app-v2.dispositions.json`, applying the one stated
rule under which its 202 confirmed entries were confirmed, and counts how many
places the rule's text is written. That count is how many copies can drift
when a rule is reworded, and it is a property of the shape, not of prose.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "protasis-design-evidence/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
COMMAND = "python3 plugins/dokimasia/docs/design/build_attribution_design_evidence.py"
PINNED_SET = Path("plugins/dokimasia/docs/evidence/wildcat-app-v2.dispositions.json")

# The one rule the pinned confirmations were made under, as the run that made
# them recorded it. The generator uses it only to measure a shape.
RULE_ID = "row-author-owns-walking-it"
RULE_TEXT = (
    "the reviewer who wrote a row owns walking it, which holds by "
    "construction of the workbook"
)
PERSON = "Laurence Day"

CANDIDATES = [
    {
        "id": "rule-table",
        "summary": (
            "One artefact. A confirmed entry carries `confirmed_by`, a "
            "person, and may carry `rule`, an id into a set-level `rules` "
            "table that holds each rule's text and who stated it. The "
            "reconciler refuses a confirmed entry with no person, a rule id "
            "the table does not hold, and an unconfirmed entry carrying "
            "either field."
        ),
    },
    {
        "id": "inline-attribution",
        "summary": (
            "One artefact. A confirmed entry carries `confirmed_by`, a "
            "person, and `rule_text`, the rule's wording written out on the "
            "entry itself. No table: every entry is self-contained and every "
            "entry confirmed under one rule repeats its text."
        ),
    },
    {
        "id": "attestation-ledger",
        "summary": (
            "Two artefacts. Entries keep the `confirmed` boolean; a separate "
            "confirmations file holds attestations, each naming a person, a "
            "rule and the items it covers. The reconciler joins the two and "
            "refuses a confirmed entry no attestation names."
        ),
    },
]

CRITERIA = [
    {
        "id": "no-attribution-drafted",
        "concern": "correctness",
        "kind": "gate",
        "stage": "selection",
        "owner": "protasis",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "design-lock",
    },
    {
        "id": "vocabulary-unchanged",
        "concern": "compatibility",
        "kind": "gate",
        "stage": "selection",
        "owner": "protasis",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "design-lock",
    },
    {
        "id": "prior-sets-refuse-by-name",
        "concern": "compatibility",
        "kind": "gate",
        "stage": "selection",
        "owner": "elenchus",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "design-lock",
    },
    {
        "id": "confirmed-entries-preserved",
        "concern": "recovery",
        "kind": "gate",
        "stage": "selection",
        "owner": "elenchus",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "design-lock",
    },
    {
        "id": "reviewer-actions-per-item",
        "concern": "time",
        "kind": "metric",
        "stage": "selection",
        "owner": "metron",
        "unit": "count",
        "comparator": "minimise",
        "threshold": None,
        "blocks": "design-lock",
    },
    {
        "id": "reviewer-artefacts",
        "concern": "space",
        "kind": "metric",
        "stage": "selection",
        "owner": "metron",
        "unit": "count",
        "comparator": "minimise",
        "threshold": None,
        "blocks": "design-lock",
    },
    {
        "id": "rule-statements-on-pinned-set",
        "concern": "space",
        "kind": "metric",
        "stage": "selection",
        "owner": "metron",
        "unit": "count",
        "comparator": "minimise",
        "threshold": None,
        "blocks": "design-lock",
    },
    {
        "id": "unattributed-confirmation-refused",
        "concern": "correctness",
        "kind": "gate",
        "stage": "conformance",
        "owner": "protasis",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "step:2",
    },
    {
        "id": "attribution-preserved-on-regeneration",
        "concern": "recovery",
        "kind": "gate",
        "stage": "conformance",
        "owner": "elenchus",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "step:3",
    },
    {
        "id": "pinned-confirmations-attributed",
        "concern": "correctness",
        "kind": "gate",
        "stage": "conformance",
        "owner": "phylax",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "integration",
    },
]

# Declared selection values, per candidate and criterion.
#
# The four gates are met by all three candidates because each can be built
# that way: a generator that writes no attribution, ADR-001's three states
# untouched, a set confirmed before attribution existed refusing by name, and
# a confirmed entry's bytes carried forward unchanged.
#
# `reviewer-actions-per-item` counts the distinct edits a reviewer makes to
# confirm one entry with its attribution. `rule-table` and
# `inline-attribution` cost one edit on the entry. `attestation-ledger` costs
# two: the entry's boolean and the attestation naming the item.
#
# `reviewer-artefacts` counts the files a reviewer maintains by hand.
#
# `rule-statements-on-pinned-set` is measured below, not declared.
DECLARED = {
    "rule-table": {
        "no-attribution-drafted": True,
        "vocabulary-unchanged": True,
        "prior-sets-refuse-by-name": True,
        "confirmed-entries-preserved": True,
        "reviewer-actions-per-item": 1,
        "reviewer-artefacts": 1,
    },
    "inline-attribution": {
        "no-attribution-drafted": True,
        "vocabulary-unchanged": True,
        "prior-sets-refuse-by-name": True,
        "confirmed-entries-preserved": True,
        "reviewer-actions-per-item": 1,
        "reviewer-artefacts": 1,
    },
    "attestation-ledger": {
        "no-attribution-drafted": True,
        "vocabulary-unchanged": True,
        "prior-sets-refuse-by-name": True,
        "confirmed-entries-preserved": True,
        "reviewer-actions-per-item": 2,
        "reviewer-artefacts": 2,
    },
}

RESOLVERS = {
    "unattributed-confirmation-refused": (
        "python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check"
    ),
    "attribution-preserved-on-regeneration": (
        "python3 plugins/dokimasia/scripts/dokimasia.py propose --check"
    ),
    "pinned-confirmations-attributed": (
        "python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check"
    ),
}

SELECTION_CRITERIA = tuple(c["id"] for c in CRITERIA if c["stage"] == "selection")
CONFORMANCE_CRITERIA = tuple(c["id"] for c in CRITERIA if c["stage"] == "conformance")
UNITS = {c["id"]: c["unit"] for c in CRITERIA}


def shape(candidate: str, entries: list[dict]) -> list[dict]:
    """Every artefact a candidate would hold for the pinned set, as objects.

    Each shape attributes the confirmed entries to the one person under the
    one rule, which is what the run that confirmed them recorded.
    """
    confirmed = [e for e in entries if e.get("confirmed")]
    if candidate == "rule-table":
        body = [
            {**e, "confirmed_by": PERSON, "rule": RULE_ID} if e.get("confirmed") else e
            for e in entries
        ]
        return [{
            "dispositions": body,
            "rules": {RULE_ID: {"stated_by": PERSON, "text": RULE_TEXT}},
        }]
    if candidate == "inline-attribution":
        body = [
            {**e, "confirmed_by": PERSON, "rule_text": RULE_TEXT} if e.get("confirmed") else e
            for e in entries
        ]
        return [{"dispositions": body}]
    if candidate == "attestation-ledger":
        return [
            {"dispositions": entries},
            {"attestations": [{
                "by": PERSON,
                "rule": RULE_TEXT,
                "items": [e["item"] for e in confirmed],
            }]},
        ]
    raise ValueError(candidate)


def rule_statements(candidate: str, entries: list[dict]) -> int:
    """How many places the rule's text is written across the shape."""
    total = 0
    for artefact in shape(candidate, entries):
        total += json.dumps(artefact).count(json.dumps(RULE_TEXT)[1:-1])
    return total


def report_bytes(candidate: str, criterion: str, value) -> bytes:
    """One closed report object, serialised exactly as it is written."""
    body = {
        "candidate": candidate,
        "command": COMMAND,
        "criterion": criterion,
        "exit": 0,
        "schema": REPORT_SCHEMA,
        "unit": UNITS[criterion],
        "value": value,
    }
    return (json.dumps(body, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build(record_path: Path, pinned: Path) -> dict:
    """Write every selection report, then the record that binds their digests."""
    entries = json.loads(pinned.read_text(encoding="utf-8"))["dispositions"]
    root = record_path.parent
    selection_dir = root / "reports" / "selection"
    selection_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for candidate in CANDIDATES:
        name = candidate["id"]
        values = dict(DECLARED[name])
        values["rule-statements-on-pinned-set"] = rule_statements(name, entries)
        for criterion in SELECTION_CRITERIA:
            payload = report_bytes(name, criterion, values[criterion])
            relative = f"reports/selection/{name}-{criterion}.json"
            (root / relative).write_bytes(payload)
            results.append({
                "candidate": name,
                "criterion": criterion,
                "state": "pass",
                "report": {
                    "path": relative,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                },
            })
        for criterion in CONFORMANCE_CRITERIA:
            blocks = next(c["blocks"] for c in CRITERIA if c["id"] == criterion)
            results.append({
                "candidate": name,
                "criterion": criterion,
                "state": "pending",
                "resolver": RESOLVERS[criterion],
                "report": f"reports/conformance/{name}-{criterion}.json",
                "blocks": blocks,
            })

    record = {
        "schema": SCHEMA,
        "candidates": CANDIDATES,
        "criteria": CRITERIA,
        "results": results,
        # `rule-table` is the only candidate no other candidate dominates: it
        # ties `inline-attribution` on actions and artefacts and states the
        # rule once where inline states it once per confirmed entry, and it
        # ties `attestation-ledger` on rule statements while costing one
        # action and one artefact against two of each. The frontier is
        # computed by the checker, not asserted here.
        "selection": {
            "candidate": "rule-table",
            "rule": "unique-frontier",
            "policy_ref": None,
        },
    }
    record_path.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--record",
        type=Path,
        default=Path("plugins/dokimasia/docs/attribution-design-evidence.json"),
        help="where to write the record; reports go below its directory",
    )
    parser.add_argument(
        "--pinned-set",
        type=Path,
        default=PINNED_SET,
        help="the committed disposition set the measured metric is taken over",
    )
    args = parser.parse_args()
    record = build(args.record, args.pinned_set)
    print(
        f"wrote {args.record} with {len(record['results'])} results "
        f"over {len(CANDIDATES)} candidates and {len(CRITERIA)} criteria"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
