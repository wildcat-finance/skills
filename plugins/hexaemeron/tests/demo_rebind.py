#!/usr/bin/env python3
"""Demonstrate that a runbook amendment survives unrelated study amendments.

The demo path from study item 1 of `docs/fiat-rebind-runbook-amendments-study.md`:
drive the checked-in `hexctl.py` on a scratch run through init, study,
runbook, one runbook amendment touching the current step, then two unrelated
study amendments whose verdicts all hold. Print the amendment digest the
`next` packet carries afterwards and the two `retained` records the
`amend:study` ledger events wrote. Exit non-zero with a plain message if the
packet lost the amendment or either record is missing.

This is a demonstration script, not a test: no `unittest` class lives here
and the file name does not match `test*.py`, so discovery ignores it. It
reuses the fixture `hexctl_harness.HexctlCase` builds (a real repository
under the given root, a fake `git` and `gh` on `PATH`) so the demo does not
invent a second run grammar. `hexctl` runs as a subprocess with an argument
list and no shell, inside the `--root` directory only.

    python3 plugins/hexaemeron/tests/demo_rebind.py --root .hexaemeron/demo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from hexctl_harness import HexctlCase, make_origin_checkout  # noqa: E402

RETAINED_KEYS = frozenset(
    {"amendment_sha256", "from_study_sha256", "to_study_sha256", "decision"}
)


def fail(message: str) -> int:
    print(f"demo_rebind: {message}", file=sys.stderr)
    return 1


def prepare_root(root: str) -> str | None:
    """Create `root` fresh; refuse a path that already holds anything."""
    if os.path.lexists(root):
        if os.path.islink(root) or not os.path.isdir(root):
            return f"--root {root} exists and is not a directory"
        if os.listdir(root):
            return f"--root {root} exists and is not empty; remove it first"
    else:
        os.makedirs(root)
    return None


def build_case(root: str) -> HexctlCase:
    """The harness fixture anchored at `root` instead of a temporary directory."""
    case = HexctlCase(methodName="runTest")
    case.tmp = None
    case.dir = root
    case.processes = []
    case.env = os.environ.copy()
    case.fake_refs = {}
    case.fake_prs = {}
    case.fake_parents = {}
    case.install_fake_delivery_tools()
    make_origin_checkout(case.dir)
    return case


def ledger_events(case: HexctlCase, event: str) -> list[dict]:
    path = os.path.join(case.target, ".hexaemeron", "ledger.jsonl")
    with open(path, encoding="utf-8") as handle:
        entries = [json.loads(line) for line in handle if line.strip()]
    return [entry for entry in entries if entry.get("event") == event]


def run_demo(root: str) -> int:
    case = build_case(root)
    try:
        # 1. init, study, runbook: a source-bound run at its first step.
        study_text, runbook_text = case.to_runbook_amendable_steps()
        study_digest_0 = case.state()["receipts"]["study"]["sha256"]

        # 2. One runbook amendment touching the current step.
        suffix = case.runbook_amendment()
        amendment_sha256 = hashlib.sha256(suffix.encode("utf-8")).hexdigest()
        candidate = case.write("runbook-candidate.md", runbook_text + suffix)
        case.run_ctl("amend", "runbook", "--artifact", candidate)
        before = case.next_json()["brief"]["runbook_step"]["amendments"]
        if [item["sha256"] for item in before] != [amendment_sha256]:
            return fail(
                "the packet did not carry the runbook amendment before any "
                "study amendment"
            )

        # 3. Two unrelated study amendments, every verdict holding.
        first_text = study_text + case.amendment()
        study_digest_1 = hashlib.sha256(first_text.encode("utf-8")).hexdigest()
        case.run_ctl(
            "amend", "study", "--artifact", case.write("study-1.md", first_text)
        )
        second_text = first_text + case.amendment(
            date="2026-08-23", what="A second baseline fact changed."
        )
        study_digest_2 = hashlib.sha256(second_text.encode("utf-8")).hexdigest()
        case.run_ctl(
            "amend", "study", "--artifact", case.write("study-2.md", second_text)
        )

        # 4. The packet after both, and the two ledger records.
        after = case.next_json()["brief"]["runbook_step"]["amendments"]
        if [item["sha256"] for item in after] != [amendment_sha256]:
            return fail(
                "the next packet lost the runbook amendment: expected "
                f"[{amendment_sha256}], found {[item['sha256'] for item in after]}"
            )
        events = ledger_events(case, "amend:study")
        if len(events) != 2:
            return fail(f"expected 2 amend:study ledger events, found {len(events)}")
        expected = [
            {
                "amendment_sha256": amendment_sha256,
                "from_study_sha256": study_digest_0,
                "to_study_sha256": study_digest_1,
                "decision": "retained",
            },
            {
                "amendment_sha256": amendment_sha256,
                "from_study_sha256": study_digest_1,
                "to_study_sha256": study_digest_2,
                "decision": "retained",
            },
        ]
        records = []
        for index, (event, want) in enumerate(zip(events, expected), 1):
            rebinds = (event.get("data") or {}).get("runbook_rebinds")
            if not isinstance(rebinds, list) or len(rebinds) != 1:
                return fail(
                    f"amend:study event {index} carries no single retained record"
                )
            record = rebinds[0]
            if set(record) != RETAINED_KEYS or record != want:
                return fail(
                    f"amend:study event {index} record differs: "
                    f"{json.dumps(record, sort_keys=True)}"
                )
            records.append(record)
        case.run_ctl("verify")

        print(f"packet amendment sha256: {after[0]['sha256']}")
        for index, record in enumerate(records, 1):
            print(f"retained {index}: {json.dumps(record, sort_keys=True)}")
        return 0
    finally:
        for process in case.processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        required=True,
        help="scratch directory for the demo run; created fresh, refused if non-empty",
    )
    args = parser.parse_args(argv)
    root = os.path.abspath(args.root)
    problem = prepare_root(root)
    if problem is not None:
        return fail(problem)
    return run_demo(root)


if __name__ == "__main__":
    sys.exit(main())
