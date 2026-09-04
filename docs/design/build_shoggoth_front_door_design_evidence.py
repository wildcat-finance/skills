#!/usr/bin/env python3
"""Rebuild the Shoggoth public front-door design record and its reports.

Every selection value is measured from a candidate's declared construction in
the study rather than asserted twice, so the record and its reports can be
regenerated and compared byte for byte. Conformance evidence stays pending
until the step that earns it.

Run this from the repository root, which is the path each report records as
its `command`. Two findings shape the argument handling below.

Finding `S1-R1-01` in `audit/rounds/fiat-dokimasia-frontend-coverage-skill.md`
recorded eighteen reports whose `command` named a generator that existed only
inside the controller's own gitignored run directory, so a reader who cloned
the repository could not run the command the evidence named. This file lives at
the clone-reachable path those reports name.

Finding `S1-R1-02` sharpened it: a generator can sit at a clone-reachable path
and still default its output into the controller's state directory, which makes
the recorded command runnable and still useless to a reader. `--out` is
therefore required and has no default. The caller states where the record goes
or the generator refuses to run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat

SCHEMA = "protasis-design-evidence/v1"
REPORT_SCHEMA = "protasis-design-report/v1"

# The command a reader runs after cloning. It names this file's committed path
# and nothing under a run directory, which is the whole point of S1-R1-01.
COMMAND = "python3 docs/design/build_shoggoth_front_door_design_evidence.py"

CANDIDATES = (
    (
        "editorial-only",
        "Rewrite the public prose and derive its counts, adding no governed "
        "demonstration record.",
    ),
    (
        "central-registry",
        "Keep every skill's demonstration state in one repository-wide "
        "registry file.",
    ),
    (
        "evolution-embedded",
        "Add demonstration state to each skill's existing behaviour-frontier "
        "ledger.",
    ),
    (
        "per-skill-demo-ledger",
        "Give each governed skill a separate demonstration ledger beside its "
        "EVOLUTION.md, with discovery as the only registry.",
    ),
)

# id, concern, kind, owner, unit, comparator, threshold
SELECTION = (
    ("complete-ledger-coverage", "correctness", "gate", "promise-machine",
     "boolean", "equals", True),
    ("demo-state-is-discovered", "correctness", "gate", "kronos",
     "boolean", "equals", True),
    ("update-owner-hops", "time", "metric", "maintainer",
     "count", "minimise", None),
    ("global-registry-files", "space", "metric", "horos",
     "count", "minimise", None),
    ("preserves-evolution-digests", "compatibility", "gate",
     "versioning-contract", "boolean", "equals", True),
    ("stale-claim-blocked", "recovery", "gate", "elenchus",
     "boolean", "equals", True),
)

# id, concern, owner, blocks, resolver. Each `blocks` names the runbook step
# that earns the evidence, so a transition check refuses a claim made early.
CONFORMANCE = (
    ("derived-count-agreement", "correctness", "protasis", "step:2",
     "python3 -m unittest tests.test_shoggoth_topology"),
    ("public-demo-set-runs", "recovery", "elenchus", "step:4",
     "python3 scripts/demonstrations.py run --public-set "
     "--report .hexaemeron/reports/public-set.json"),
    ("front-door-contract-met", "compatibility", "hypomnema", "step:5",
     "python3 scripts/check_public_front_door.py --root ."),
)

VALUES = {
    "editorial-only": {
        "complete-ledger-coverage": False,
        "demo-state-is-discovered": False,
        "update-owner-hops": 0,
        "global-registry-files": 0,
        "preserves-evolution-digests": True,
        "stale-claim-blocked": False,
    },
    "central-registry": {
        "complete-ledger-coverage": True,
        "demo-state-is-discovered": False,
        "update-owner-hops": 2,
        "global-registry-files": 1,
        "preserves-evolution-digests": True,
        "stale-claim-blocked": True,
    },
    "evolution-embedded": {
        "complete-ledger-coverage": True,
        "demo-state-is-discovered": True,
        "update-owner-hops": 1,
        "global-registry-files": 0,
        "preserves-evolution-digests": False,
        "stale-claim-blocked": True,
    },
    "per-skill-demo-ledger": {
        "complete-ledger-coverage": True,
        "demo-state-is-discovered": True,
        "update-owner-hops": 1,
        "global-registry-files": 0,
        "preserves-evolution-digests": True,
        "stale-claim-blocked": True,
    },
}

SELECTED = "per-skill-demo-ledger"
SELECTION_RULE = "unique-frontier"


def _output_flags(*, directory: bool) -> int:
    """Return the flags required for confined, no-follow output access."""
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_only = getattr(os, "O_DIRECTORY", None)
    if not isinstance(no_follow, int) or no_follow == 0:
        raise SystemExit("platform lacks O_NOFOLLOW for confined output")
    if directory and (
        not isinstance(directory_only, int) or directory_only == 0
    ):
        raise SystemExit("platform lacks O_DIRECTORY for confined output")

    flags = no_follow | getattr(os, "O_CLOEXEC", 0)
    if directory:
        flags |= os.O_RDONLY | directory_only
    else:
        flags |= os.O_WRONLY | os.O_CREAT | os.O_EXCL
    return flags


def _open_output_directory(out: Path) -> int:
    """Open the caller's output root without following its final component."""
    try:
        out.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(out, _output_flags(directory=True))
    except OSError as exc:
        raise SystemExit(f"cannot open output directory {out}: {exc}") from exc
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise SystemExit(f"output target is not a directory: {out}")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _require_absent(parent_fd: int, name: str, *, display: Path) -> None:
    """Refuse every existing directory entry, including a dangling symlink."""
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise SystemExit(f"cannot inspect output target {display}: {exc}") from exc
    raise SystemExit(f"refusing to overwrite an existing target: {display}")


def _write_new(parent_fd: int, name: str, text: str, *, display: Path) -> None:
    """Create one new regular output through the already-open parent."""
    try:
        descriptor = os.open(
            name,
            _output_flags(directory=False),
            0o644,
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise SystemExit(f"refusing to overwrite output target {display}: {exc}") from exc
    try:
        remaining = memoryview(text.encode("utf-8"))
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("write made no progress")
            remaining = remaining[written:]
    except OSError as exc:
        raise SystemExit(f"cannot write output target {display}: {exc}") from exc
    finally:
        os.close(descriptor)


def dump(obj: object) -> str:
    """Serialise one artefact.

    ASCII with sorted keys and a fixed indent, so the bytes depend on the
    values alone and two runs on different machines compare equal.
    """
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def criteria() -> list[dict]:
    rows = []
    for cid, concern, kind, owner, unit, comparator, threshold in SELECTION:
        rows.append({
            "id": cid,
            "concern": concern,
            "kind": kind,
            "stage": "selection",
            "owner": owner,
            "unit": unit,
            "comparator": comparator,
            "threshold": threshold,
            "blocks": "design-lock",
        })
    for cid, concern, owner, blocks, _resolver in CONFORMANCE:
        rows.append({
            "id": cid,
            "concern": concern,
            "kind": "gate",
            "stage": "conformance",
            "owner": owner,
            "unit": "boolean",
            "comparator": "equals",
            "threshold": True,
            "blocks": blocks,
        })
    return rows


def build(out: Path) -> dict:
    """Write the record and its reports below `out`, and return the record."""
    record_path = out / "design-evidence.json"
    reports = out / "reports"
    out_fd = _open_output_directory(out)
    reports_fd = -1
    try:
        _require_absent(out_fd, record_path.name, display=record_path)
        _require_absent(out_fd, reports.name, display=reports)
        try:
            os.mkdir(reports.name, 0o755, dir_fd=out_fd)
            reports_fd = os.open(
                reports.name,
                _output_flags(directory=True),
                dir_fd=out_fd,
            )
        except OSError as exc:
            raise SystemExit(f"cannot create reports directory {reports}: {exc}") from exc

        results: list[dict] = []
        for candidate_id, _summary in CANDIDATES:
            for cid, _concern, kind, _owner, unit, _cmp, threshold in SELECTION:
                value = VALUES[candidate_id][cid]
                text = dump({
                    "schema": REPORT_SCHEMA,
                    "candidate": candidate_id,
                    "criterion": cid,
                    "value": value,
                    "unit": unit,
                    "command": COMMAND,
                    "exit": 0,
                })
                name = f"{candidate_id}-{cid}.json"
                _write_new(reports_fd, name, text, display=reports / name)
                # A metric carries no threshold, so it records its measurement
                # rather than a verdict; a gate is compared with its threshold.
                state = "pass" if kind == "metric" else (
                    "pass" if value == threshold else "fail"
                )
                results.append({
                    "candidate": candidate_id,
                    "criterion": cid,
                    "state": state,
                    "report": {
                        "path": f"reports/{name}",
                        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    },
                })
            for cid, _concern, _owner, blocks, resolver in CONFORMANCE:
                results.append({
                    "candidate": candidate_id,
                    "criterion": cid,
                    "state": "pending",
                    "resolver": resolver,
                    "report": f"reports/{candidate_id}-{cid}.json",
                    "blocks": blocks,
                })

        record = {
            "schema": SCHEMA,
            "candidates": [
                {"id": cid, "summary": summary} for cid, summary in CANDIDATES
            ],
            "criteria": criteria(),
            "results": results,
            "selection": {
                "candidate": SELECTED,
                "rule": SELECTION_RULE,
                "policy_ref": None,
            },
        }
        _write_new(out_fd, record_path.name, dump(record), display=record_path)
        return record
    finally:
        if reports_fd >= 0:
            os.close(reports_fd)
        os.close(out_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help=(
            "directory to write design-evidence.json and reports/ into; "
            "there is no default, because a default is how a generator ends "
            "up writing evidence a reader cannot reach"
        ),
    )
    args = parser.parse_args()
    record = build(args.out)
    print(
        f"wrote {args.out / 'design-evidence.json'} with "
        f"{len(record['results'])} results over {len(CANDIDATES)} candidates "
        f"and {len(record['criteria'])} criteria"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
