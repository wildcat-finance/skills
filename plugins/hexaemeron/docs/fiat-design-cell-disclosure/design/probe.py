#!/usr/bin/env python3
"""Measure the four skills#1524 candidates on a synthetic controller state.

Each candidate answers one situation: a `protasis-design-evidence/v1` record
receipted at design lock carries one conformance cell due at `integration`,
and the data the run collects fails it (the skills#1298 shape: threshold 2,
observed 0 or 1). The probe builds that state in a fresh temporary directory,
applies the candidate's operation, and measures one criterion. It runs the
repository's own `design_evidence.py` for every transition verdict and never
touches a live run: it reads the checker below `--root` and writes one report
to `--out`, which must not exist.

The probe models controller state as three files, `state.json`, `ledger.jsonl`
and the record with its reports. It does not run `hexctl`, so it measures the
candidates' mechanisms, not the controller that the runbook must build.

Candidates:

  halt-as-today         the cell refuses D008; the operator halts with a reason.
  threshold-amendment   an append-only sidecar lowers the threshold and the cell
                        is re-resolved against the lowered value.
  floor-then-tighten    the record locks a floor of 1; a later step appends a
                        tighten to 2; the transition judges against the tighter.
  disclosed-refusal     a closed disclosure binds the failing report and the
                        locked threshold; the transition admits the cell as
                        disclosed, and integration requires a matching row in
                        the run pull request body.

Criteria (all selection, measured over datasets 0 and 1 where stated):

  record-and-reports-unchanged  receipted record and report digests hold.
  locked-threshold-governs      every verdict is computed against the locked threshold.
  failed-cell-on-ledger         a structured ledger entry names the cell, report
                                digest, value and threshold.
  integrate-reachable           the modelled `done integrate` admission is reached.
  legacy-state-untouched        a state without the contract is left byte-identical.
  ledger-bytes-added            bytes the operation adds (dataset 0).
  operation-ms                  median wall time of the operation (dataset 0).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CANDIDATES = (
    "halt-as-today",
    "threshold-amendment",
    "floor-then-tighten",
    "disclosed-refusal",
)
CRITERIA = {
    "record-and-reports-unchanged": "boolean",
    "locked-threshold-governs": "boolean",
    "failed-cell-on-ledger": "boolean",
    "integrate-reachable": "boolean",
    "legacy-state-untouched": "boolean",
    "ledger-bytes-added": "bytes",
    "operation-ms": "milliseconds",
}
DATASETS = (0, 1)
CELL = ("jsonl-fixture", "two-independent-specimens")
DESIGN_THRESHOLD = 2
FLOOR_THRESHOLD = 1
CHECKER = "plugins/hexaemeron/skills/protasis/scripts/design_evidence.py"
REPORT_SCHEMA = "protasis-design-report/v1"
RECORD_SCHEMA = "protasis-design-evidence/v1"
DISCLOSURE_SCHEMA = "protasis-design-disclosure/v1"
DISCLOSURE_HEADING = "## Design evidence"
TIMEOUT_SECONDS = 60
OUTPUT_CAP = 1 << 20
CREATED: list[Path] = []


class Refusal(RuntimeError):
    """The probe could not establish the requested measurement."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True) + "\n").encode("utf-8")


class Run:
    """One synthetic run under a fresh directory."""

    def __init__(self, root: Path, checker: Path, threshold: int, legacy: bool = False):
        self.root = root
        self.checker = checker
        self.state_dir = root / ".hexaemeron"
        self.record_path = self.state_dir / "design-evidence.json"
        self.state_path = self.state_dir / "state.json"
        self.ledger_path = self.state_dir / "ledger.jsonl"
        (self.state_dir / "design-reports").mkdir(parents=True)
        (self.state_dir / "reports").mkdir()
        self.threshold = threshold
        self.legacy = legacy
        self.report_digests: dict[str, str] = {}
        self.write_record(threshold)
        self.write_receipts()

    # -- construction -----------------------------------------------------

    def write_record(self, threshold: int) -> None:
        candidates = (("jsonl-fixture", "Ship the fixture as JSONL."),
                      ("sqlite-fixture", "Ship the fixture as one database."))
        selection = (
            ("works", "correctness", "gate", "boolean", "equals", True),
            ("warm-time", "time", "metric", "milliseconds", "minimise", None),
            ("peak-space", "space", "metric", "bytes", "minimise", None),
            ("plugin-safe", "compatibility", "gate", "boolean", "equals", True),
            ("restart-safe", "recovery", "gate", "boolean", "equals", True),
        )
        criteria = [
            {"id": cid, "concern": concern, "kind": kind, "stage": "selection",
             "owner": "probe", "unit": unit, "comparator": comparator,
             "threshold": thr, "blocks": "design-lock"}
            for cid, concern, kind, unit, comparator, thr in selection
        ]
        criteria.append({
            "id": CELL[1], "concern": "correctness", "kind": "gate",
            "stage": "conformance", "owner": "probe", "unit": "count",
            "comparator": "at-least", "threshold": threshold,
            "blocks": "integration",
        })
        results = []
        for cand, _ in candidates:
            for cid, _, kind, unit, _, _ in selection:
                value = True if kind == "gate" else (10 if cand == "jsonl-fixture" else 20)
                payload = {"schema": REPORT_SCHEMA, "candidate": cand, "criterion": cid,
                           "value": value, "unit": unit,
                           "command": f"probe measure {cand} {cid}", "exit": 0}
                data = canonical(payload)
                name = f"design-reports/{cand}-{cid}.json"
                (self.state_dir / name).write_bytes(data)
                self.report_digests[name] = sha256(data)
                results.append({"candidate": cand, "criterion": cid, "state": "pass",
                                "report": {"path": name, "sha256": sha256(data)}})
            results.append({
                "candidate": cand, "criterion": CELL[1], "state": "pending",
                "resolver": f"python3 probe resolve {cand} {CELL[1]}",
                "report": f"reports/{cand}-{CELL[1]}.json",
                "blocks": "integration",
            })
        record = {"schema": RECORD_SCHEMA,
                  "candidates": [{"id": c, "summary": s} for c, s in candidates],
                  "criteria": criteria, "results": results,
                  "selection": {"candidate": CELL[0], "rule": "unique-frontier",
                                "policy_ref": None}}
        self.record_path.write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())

    def write_receipts(self) -> None:
        lock = self.check("design-lock", self.record_path)
        if lock["findings"]:
            raise Refusal(f"synthetic record does not lock: {lock['findings'][0]}")
        design = {"schema": RECORD_SCHEMA, "artifact": ".hexaemeron/design-evidence.json",
                  "sha256": sha256(self.record_path.read_bytes()),
                  "selected": lock["selected"],
                  "transitions": [{"transition": "design-lock", "reports": lock["consumed"]}]}
        state = {"version": 1, "phase": "integrate", "halted": None,
                 "receipts": {"study": {"artifact": ".hexaemeron/study.md",
                                        "sha256": "0" * 64}},
                 "integrate": {"merged": [1, 2, 3], "merges": {}}}
        if not self.legacy:
            state["contracts"] = {"design_evidence": RECORD_SCHEMA}
            state["receipts"]["study"]["design_evidence"] = design
        self.state = state
        self.save_state()
        self.ledger_path.write_bytes(b"")
        self.ledger("done:study", {"design_evidence": design} if not self.legacy else {})

    def save_state(self) -> None:
        self.state_path.write_bytes(canonical(self.state))

    def ledger(self, event: str, data: dict) -> None:
        with self.ledger_path.open("ab") as handle:
            handle.write(canonical({"event": event, "data": data}))

    def ledger_entries(self) -> list[dict]:
        return [json.loads(line) for line in self.ledger_path.read_bytes().splitlines() if line.strip()]

    # -- the data step ----------------------------------------------------

    def collect(self, value: int, exit_code: int) -> Path:
        """Write the resolver's closed report for the selected candidate."""
        payload = {"schema": REPORT_SCHEMA, "candidate": CELL[0], "criterion": CELL[1],
                   "value": value, "unit": "count",
                   "command": f"probe resolve {CELL[0]} {CELL[1]}", "exit": exit_code}
        path = self.state_dir / f"reports/{CELL[0]}-{CELL[1]}.json"
        path.write_bytes(canonical(payload))
        return path

    # -- the checker ------------------------------------------------------

    def check(self, transition: str, record: Path) -> dict:
        argv = [sys.executable, str(self.checker), str(record), "--transition", transition,
                "--format", "receipt"]
        completed = subprocess.run(argv, capture_output=True, timeout=TIMEOUT_SECONDS, check=False)
        if len(completed.stdout) > OUTPUT_CAP:
            raise Refusal("checker output exceeds the probe's cap")
        try:
            return json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise Refusal(f"checker returned no receipt: {exc}") from exc

    def derived_record(self, threshold: int) -> Path:
        """A copy of the record with the cell's threshold replaced, beside it."""
        record = json.loads(self.record_path.read_bytes())
        for criterion in record["criteria"]:
            if criterion["id"] == CELL[1]:
                criterion["threshold"] = threshold
        path = self.state_dir / f"derived-record-{threshold}.json"
        path.write_bytes((json.dumps(record, indent=2, sort_keys=True) + "\n").encode())
        return path

    # -- measurement helpers ---------------------------------------------

    def footprint(self) -> int:
        total = 0
        for path in sorted(self.state_dir.rglob("*")):
            if path.is_file() and "design-reports" not in path.parts and path.name != "design-evidence.json":
                if not path.name.startswith("derived-record-"):
                    total += path.stat().st_size
        return total

    def receipted_digests_hold(self) -> bool:
        design = self.state["receipts"]["study"].get("design_evidence")
        if design is None:
            return True
        if sha256(self.record_path.read_bytes()) != design["sha256"]:
            return False
        for transition in design["transitions"]:
            for report in transition["reports"]:
                if sha256((self.state_dir / report["path"]).read_bytes()) != report["sha256"]:
                    return False
        return True


class Outcome:
    def __init__(self) -> None:
        self.integrate_reached = False
        self.structured_entry = False
        self.governing_thresholds: list[int] = []
        self.locked_threshold = DESIGN_THRESHOLD


def d008_cells(receipt: dict) -> set[tuple[str, str]]:
    cells = set()
    for finding in receipt["findings"]:
        if finding["code"] == "D008":
            head = finding["message"].split(" ", 1)[0]
            cells.add(tuple(head.split("/", 1)))
    return cells


def integrate_body_admits(rows: list[str], disclosures: list[dict]) -> bool:
    """Model `done integrate` reading the run pull request body section."""
    expected = {f"{d['candidate']}/{d['criterion']} | {d['value']} {d['unit']} against "
                f"{d['comparator']} {d['threshold']} | {d['report']['sha256']} | {d['reason']}"
                for d in disclosures}
    return set(rows) == expected and len(rows) == len(disclosures)


# -- candidate operations -------------------------------------------------

def op_halt(run: Run, value: int, outcome: Outcome) -> None:
    run.collect(value, 1)
    receipt = run.check("integration", run.record_path)
    outcome.governing_thresholds.append(run.threshold)
    if CELL in d008_cells(receipt):
        run.state["halted"] = {"reason": "integration design cell fails on evidence", "ts": "T"}
        run.save_state()
        run.ledger("halt", {"reason": "integration design cell fails on evidence"})
        return
    outcome.integrate_reached = True


def op_threshold_amendment(run: Run, value: int, outcome: Outcome) -> None:
    report = run.collect(value, 1)
    receipt = run.check("integration", run.record_path)
    if CELL not in d008_cells(receipt):
        outcome.governing_thresholds.append(run.threshold)
        outcome.integrate_reached = True
        return
    new_threshold = value
    amendment = {"schema": "probe-design-amendment/v1", "candidate": CELL[0],
                 "criterion": CELL[1], "prior_threshold": run.threshold,
                 "new_threshold": new_threshold,
                 "record_sha256": run.state["receipts"]["study"]["design_evidence"]["sha256"],
                 "report": {"path": f"reports/{CELL[0]}-{CELL[1]}.json",
                            "sha256": sha256(report.read_bytes())},
                 "value": value, "reason": "the universe holds fewer positives than the study assumed"}
    (run.state_dir / "design-amendments.json").write_bytes(canonical([amendment]))
    run.ledger("amend:design", amendment)
    run.collect(value, 0)  # re-resolved against the lowered threshold
    derived = run.derived_record(new_threshold)
    receipt = run.check("integration", derived)
    outcome.governing_thresholds.append(new_threshold)
    outcome.structured_entry = True
    if not receipt["findings"]:
        run.state["receipts"]["study"]["design_evidence"]["transitions"].append(
            {"transition": "integration", "reports": receipt["consumed"]})
        run.save_state()
        run.ledger("done:merge-step", {"design_transition": receipt["consumed"]})
        outcome.integrate_reached = True


def op_floor_then_tighten(run: Run, value: int, outcome: Outcome) -> None:
    outcome.locked_threshold = FLOOR_THRESHOLD
    tighten = {"schema": "probe-design-tighten/v1", "candidate": CELL[0], "criterion": CELL[1],
               "prior_threshold": FLOOR_THRESHOLD, "new_threshold": DESIGN_THRESHOLD,
               "record_sha256": run.state["receipts"]["study"]["design_evidence"]["sha256"],
               "step": 3}
    (run.state_dir / "design-amendments.json").write_bytes(canonical([tighten]))
    run.ledger("amend:design-tighten", tighten)
    run.collect(value, 1 if value < DESIGN_THRESHOLD else 0)
    derived = run.derived_record(DESIGN_THRESHOLD)
    receipt = run.check("integration", derived)
    outcome.governing_thresholds.append(DESIGN_THRESHOLD)
    if receipt["findings"]:
        run.state["halted"] = {"reason": "tightened design cell fails on evidence", "ts": "T"}
        run.save_state()
        run.ledger("halt", {"reason": "tightened design cell fails on evidence"})
        return
    outcome.integrate_reached = True


def op_disclosed_refusal(run: Run, value: int, outcome: Outcome) -> None:
    report = run.collect(value, 1)
    receipt = run.check("integration", run.record_path)
    outcome.governing_thresholds.append(run.threshold)
    failing = d008_cells(receipt)
    if not failing:
        outcome.integrate_reached = True
        return
    if failing != {CELL}:
        return
    disclosure = {"schema": DISCLOSURE_SCHEMA, "candidate": CELL[0], "criterion": CELL[1],
                  "record_sha256": run.state["receipts"]["study"]["design_evidence"]["sha256"],
                  "report": {"path": f"reports/{CELL[0]}-{CELL[1]}.json",
                             "sha256": sha256(report.read_bytes())},
                  "value": value, "unit": "count", "comparator": "at-least",
                  "threshold": run.threshold,
                  "reason": "the pinned universe holds fewer independent positives than the threshold"}
    disclosures_dir = run.state_dir / "design-disclosures"
    disclosures_dir.mkdir(exist_ok=True)
    (disclosures_dir / f"{CELL[0]}--{CELL[1]}.json").write_bytes(canonical(disclosure))
    run.ledger("design:disclose", disclosure)
    outcome.structured_entry = True
    # The disclosure-aware transition: every D008 cell must carry a matching
    # disclosure whose record and report digests equal the current bytes.
    admitted = []
    for cell in failing:
        current = sha256((run.state_dir / disclosure["report"]["path"]).read_bytes())
        if (cell == (disclosure["candidate"], disclosure["criterion"])
                and disclosure["report"]["sha256"] == current
                and disclosure["record_sha256"] == sha256(run.record_path.read_bytes())):
            admitted.append(disclosure)
    if len(admitted) != len(failing):
        return
    transition = {"transition": "integration", "reports": receipt["consumed"],
                  "disclosed": [{"candidate": d["candidate"], "criterion": d["criterion"],
                                 "sha256": d["report"]["sha256"]} for d in admitted]}
    run.state["receipts"]["study"]["design_evidence"]["transitions"].append(transition)
    run.save_state()
    run.ledger("done:merge-step", {"design_transition": transition})
    rows = [f"{d['candidate']}/{d['criterion']} | {d['value']} {d['unit']} against "
            f"{d['comparator']} {d['threshold']} | {d['report']['sha256']} | {d['reason']}"
            for d in admitted]
    body = "# Run\n\n" + DISCLOSURE_HEADING + "\n\n" + "\n".join(rows) + "\n"
    (run.root / "run-pr.md").write_text(body, encoding="utf-8")
    section = body.split(DISCLOSURE_HEADING, 1)[1].strip().splitlines()
    outcome.integrate_reached = integrate_body_admits(section, admitted)


OPERATIONS = {
    "halt-as-today": op_halt,
    "threshold-amendment": op_threshold_amendment,
    "floor-then-tighten": op_floor_then_tighten,
    "disclosed-refusal": op_disclosed_refusal,
}
LEGACY_COMMAND = {
    "halt-as-today": None,
    "threshold-amendment": "amend design",
    "floor-then-tighten": "amend design-tighten",
    "disclosed-refusal": "disclose design",
}


def structured_failure_entry(run: Run) -> bool:
    """A ledger entry naming candidate, criterion, report digest, value, threshold."""
    for entry in run.ledger_entries():
        data = entry.get("data", {})
        if (data.get("candidate") == CELL[0] and data.get("criterion") == CELL[1]
                and isinstance(data.get("report"), dict) and "sha256" in data["report"]
                and "value" in data and ("threshold" in data or "prior_threshold" in data)):
            return True
    return False


def fresh_directory(prefix: str) -> Path:
    """One temporary directory under the system default, removed at exit."""
    path = Path(tempfile.mkdtemp(prefix=prefix))
    CREATED.append(path)
    return path


def run_candidate(candidate: str, checker: Path, value: int) -> tuple[Run, Outcome]:
    threshold = FLOOR_THRESHOLD if candidate == "floor-then-tighten" else DESIGN_THRESHOLD
    temp = fresh_directory("probe-1524-")
    run = Run(temp, checker, threshold)
    outcome = Outcome()
    OPERATIONS[candidate](run, value, outcome)
    return run, outcome


def measure(candidate: str, criterion: str, checker: Path):
    if criterion == "record-and-reports-unchanged":
        return all(run_candidate(candidate, checker, v)[0].receipted_digests_hold() for v in DATASETS)
    if criterion == "locked-threshold-governs":
        for value in DATASETS:
            _, outcome = run_candidate(candidate, checker, value)
            if any(t != outcome.locked_threshold for t in outcome.governing_thresholds):
                return False
        return True
    if criterion == "failed-cell-on-ledger":
        return all(structured_failure_entry(run_candidate(candidate, checker, v)[0]) for v in DATASETS)
    if criterion == "integrate-reachable":
        return all(run_candidate(candidate, checker, v)[1].integrate_reached for v in DATASETS)
    if criterion == "legacy-state-untouched":
        temp = fresh_directory("probe-1524-legacy-")
        run = Run(temp, checker, DESIGN_THRESHOLD, legacy=True)
        before = (run.state_path.read_bytes(), run.ledger_path.read_bytes(),
                  sorted(p.name for p in run.state_dir.rglob("*")))
        command = LEGACY_COMMAND[candidate]
        if command is not None:
            # Every design-specific command refuses when the state carries no
            # design contract; the refusal writes nothing.
            if "design_evidence" in run.state.get("contracts", {}):
                raise Refusal("legacy state unexpectedly carries the contract")
        after = (run.state_path.read_bytes(), run.ledger_path.read_bytes(),
                 sorted(p.name for p in run.state_dir.rglob("*")))
        return before == after
    if criterion == "ledger-bytes-added":
        temp = fresh_directory("probe-1524-bytes-")
        threshold = FLOOR_THRESHOLD if candidate == "floor-then-tighten" else DESIGN_THRESHOLD
        run = Run(temp, checker, threshold)
        before = run.footprint()
        OPERATIONS[candidate](run, DATASETS[0], Outcome())
        return run.footprint() - before
    if criterion == "operation-ms":
        samples = []
        for _ in range(5):
            threshold = FLOOR_THRESHOLD if candidate == "floor-then-tighten" else DESIGN_THRESHOLD
            run = Run(fresh_directory("probe-1524-ms-"), checker, threshold)
            started = time.perf_counter()
            OPERATIONS[candidate](run, DATASETS[0], Outcome())
            samples.append((time.perf_counter() - started) * 1000.0)
        return int(round(statistics.median(samples)))
    raise Refusal(f"unknown criterion {criterion}")


def write_report(out: Path, candidate: str, criterion: str, value, command: str) -> None:
    payload = {"schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion,
               "value": value, "unit": CRITERIA[criterion], "command": command, "exit": 0}
    if os.path.lexists(out):
        raise Refusal(f"refusing to overwrite {out}")
    descriptor = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(canonical(payload))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=".", help="repository root holding the Protasis checker")
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--out", required=True, help="closed protasis-design-report/v1 path; must not exist")
    args = parser.parse_args(argv)
    checker = Path(args.root) / CHECKER
    if not checker.is_file():
        print(f"probe: checker not found at {checker}", file=sys.stderr)
        return 2
    command = "python3 .hexaemeron/design/probe.py " + " ".join(
        shlex.quote(a) for a in (sys.argv[1:] if argv is None else argv))
    try:
        value = measure(args.candidate, args.criterion, checker)
        write_report(Path(args.out), args.candidate, args.criterion, value, command)
    except Refusal as exc:
        print(f"probe: {exc}", file=sys.stderr)
        return 1
    finally:
        for created in CREATED:
            shutil.rmtree(created, ignore_errors=True)
    print(json.dumps({"candidate": args.candidate, "criterion": args.criterion, "value": value}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
