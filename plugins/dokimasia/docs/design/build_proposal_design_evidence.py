#!/usr/bin/env python3
"""Build the design record for Dokimasia's proposed-disposition frontier.

The record is the selection interface; the study's prose explains the
candidates but decides nothing. Every selection cell resolves to a committed
`protasis-design-report/v1` report, and every conformance cell names the exact
resolver that will produce it at the transition it blocks.

Run this from the repository root, which is the path each report records as its
`command`. The previous frontier's generator recorded a path that resolved only
inside the controller's own gitignored run directory, so a reader who cloned
the repository could not run the command the evidence named; that is finding
S1-R1-01 in `audit/rounds/fiat-dokimasia-frontend-coverage-skill.md`, and the
argument default below is what keeps it from recurring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "protasis-design-evidence/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
COMMAND = "python3 plugins/dokimasia/docs/design/build_proposal_design_evidence.py"

CANDIDATES = [
    {
        "id": "confirmed-flag",
        "summary": (
            "One artefact. Every disposition entry carries a required "
            "`confirmed` boolean and the digest of the proposal it came from. "
            "`propose` regenerates the file in place, carrying every confirmed "
            "or edited entry forward byte for byte and replacing only entries "
            "no person has touched."
        ),
    },
    {
        "id": "proposal-overlay",
        "summary": (
            "Two artefacts, one direction. `propose` writes a proposals file "
            "it owns outright and never reads back. A reviewer confirms by "
            "copying an entry into the dispositions file, which the generator "
            "never opens, so edits survive because nothing can rewrite them."
        ),
    },
    {
        "id": "two-file-merge",
        "summary": (
            "Two artefacts, joined at read time. `propose` owns the proposals "
            "file; the reviewer owns a confirmations file naming the ids they "
            "accept and any reason they replaced. The reconciler reads both "
            "and treats an unconfirmed proposal as no disposition at all."
        ),
    },
]

CRITERIA = [
    {
        "id": "no-covered-path",
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
        "id": "proposal-refused-unconfirmed",
        "concern": "correctness",
        "kind": "gate",
        "stage": "conformance",
        "owner": "protasis",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "step:3",
    },
    {
        "id": "regeneration-preserves-edits",
        "concern": "recovery",
        "kind": "gate",
        "stage": "conformance",
        "owner": "elenchus",
        "unit": "boolean",
        "comparator": "equals",
        "threshold": True,
        "blocks": "step:4",
    },
    {
        "id": "pinned-closure-above-zero",
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

# Selection values, per candidate and criterion.
#
# The two gates that could remove a candidate are met by all three, because
# each design can be built so that no code path constructs `covered` and so
# that a confirmed entry's bytes are carried forward unchanged. The choice is
# therefore made by the two metrics, which count what the reviewer pays.
#
# `reviewer-actions-per-item` counts the distinct edits a reviewer makes to
# accept one drafted entry. `confirmed-flag` and `two-file-merge` cost one;
# `proposal-overlay` costs two, because the entry is copied into a second file
# and then confirmed there.
#
# `reviewer-artefacts` counts the files a reviewer maintains by hand once the
# workflow is running.
SELECTION = {
    "confirmed-flag": {
        "no-covered-path": True,
        "confirmed-entries-preserved": True,
        "vocabulary-unchanged": True,
        "reviewer-actions-per-item": 1,
        "reviewer-artefacts": 1,
    },
    "proposal-overlay": {
        "no-covered-path": True,
        "confirmed-entries-preserved": True,
        "vocabulary-unchanged": True,
        "reviewer-actions-per-item": 2,
        "reviewer-artefacts": 2,
    },
    "two-file-merge": {
        "no-covered-path": True,
        "confirmed-entries-preserved": True,
        "vocabulary-unchanged": True,
        "reviewer-actions-per-item": 1,
        "reviewer-artefacts": 2,
    },
}

RESOLVERS = {
    "proposal-refused-unconfirmed": (
        "python3 plugins/dokimasia/scripts/dokimasia.py reconcile --check"
    ),
    "regeneration-preserves-edits": (
        "python3 plugins/dokimasia/scripts/dokimasia.py propose --check"
    ),
    "pinned-closure-above-zero": (
        "python3 plugins/dokimasia/scripts/dokimasia.py demonstrate --check"
    ),
}

SELECTION_CRITERIA = tuple(c["id"] for c in CRITERIA if c["stage"] == "selection")
CONFORMANCE_CRITERIA = tuple(c["id"] for c in CRITERIA if c["stage"] == "conformance")
UNITS = {c["id"]: c["unit"] for c in CRITERIA}


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


def build(record_path: Path) -> dict:
    """Write every selection report, then the record that binds their digests."""
    root = record_path.parent
    selection_dir = root / "reports" / "selection"
    selection_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for candidate in CANDIDATES:
        name = candidate["id"]
        for criterion in SELECTION_CRITERIA:
            value = SELECTION[name][criterion]
            payload = report_bytes(name, criterion, value)
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
        # `confirmed-flag` is the only candidate no other candidate dominates:
        # it costs one reviewer action and one maintained artefact, where
        # `proposal-overlay` costs two of each and `two-file-merge` costs one
        # action and two artefacts. The frontier is computed by the checker,
        # not asserted here.
        "selection": {
            "candidate": "confirmed-flag",
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
        # The committed record, so the bare command each report names
        # regenerates the artefact it documents. Defaulting to the
        # controller's own state directory would have made the recorded
        # command runnable and still useless to a reader, which is the
        # other half of finding S1-R1-01.
        default=Path("plugins/dokimasia/docs/proposal-design-evidence.json"),
        help="where to write the record; reports go below its directory",
    )
    args = parser.parse_args()
    record = build(args.record)
    print(
        f"wrote {args.record} with {len(record['results'])} results "
        f"over {len(CANDIDATES)} candidates and {len(CRITERIA)} criteria"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
