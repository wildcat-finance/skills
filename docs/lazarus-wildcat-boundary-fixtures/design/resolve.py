#!/usr/bin/env python3
"""Resolve the #1384 design-record cells from the recorded probe measurements.

Each selection cell reads `probe-v1.json`, `probe-v2.json`, the generated plan
summaries and `candidates.json` in this directory and writes one closed
`protasis-design-report/v1` object to the caller-named `--report` path, which
must not exist yet. The two conformance cells run the example's demonstration
against the local release trees named by environment variables once those
exist; until then they refuse. `--all` resolves every selection cell into
`--reports-dir` and writes the `protasis-design-evidence/v1` record to
`--record`, both caller-named.

Nothing here reaches a network. A report records a measurement or a check; it
proves no fixture relation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPORT_SCHEMA = "protasis-design-report/v1"
RECORD_SCHEMA = "protasis-design-evidence/v1"
GENERATIONS = ("v1", "v2")
GUARD_TESTS = (
    "CaptureTests.test_interrupted_finalisation_leaves_no_fixture_or_staging_directory",
    "CaptureTests.test_elapsed_time_limit_leaves_no_output",
    "ReceiptCaptureTests.test_plan_v3_interruption_after_staging_removes_the_stage",
)
ACCOUNT_PROOF_BYTES = 7_800  # measured account-only eth_getProof answer, both boundaries
SLOT_PROOF_BYTES = 2_755  # measured marginal bytes per storage proof at depth 3 to 5

CRITERIA = [
    {"id": "mapped-words-proved", "concern": "correctness", "kind": "gate", "stage": "selection",
     "owner": "lazarus", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "design-lock"},
    {"id": "unexplained-getter-mismatches", "concern": "correctness", "kind": "gate", "stage": "selection",
     "owner": "lazarus", "unit": "count", "comparator": "equals", "threshold": 0, "blocks": "design-lock"},
    {"id": "capture-route-serves-boundary", "concern": "compatibility", "kind": "gate", "stage": "selection",
     "owner": "lazarus", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "design-lock"},
    {"id": "plan-validates", "concern": "compatibility", "kind": "gate", "stage": "selection",
     "owner": "lazarus", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "design-lock"},
    {"id": "no-provider-coordinate-in-plan", "concern": "compatibility", "kind": "gate", "stage": "selection",
     "owner": "phylax", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "design-lock"},
    {"id": "projected-capture-milliseconds", "concern": "time", "kind": "gate", "stage": "selection",
     "owner": "metron", "unit": "milliseconds", "comparator": "at-most", "threshold": 86_400_000, "blocks": "design-lock"},
    {"id": "in-tree-bytes-within-margin", "concern": "space", "kind": "gate", "stage": "selection",
     "owner": "metron", "unit": "bytes", "comparator": "at-most", "threshold": 2_256_023, "blocks": "design-lock"},
    {"id": "in-tree-bytes", "concern": "space", "kind": "metric", "stage": "selection",
     "owner": "metron", "unit": "bytes", "comparator": "minimise", "threshold": None, "blocks": "design-lock"},
    {"id": "interrupted-capture-leaves-nothing", "concern": "recovery", "kind": "gate", "stage": "selection",
     "owner": "elenchus", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "design-lock"},
    {"id": "altered-bytes-refused", "concern": "recovery", "kind": "gate", "stage": "conformance",
     "owner": "elenchus", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "integration"},
    {"id": "state-fixture-v2-binds", "concern": "compatibility", "kind": "gate", "stage": "conformance",
     "owner": "ariadne", "unit": "boolean", "comparator": "equals", "threshold": True, "blocks": "integration"},
]
CONFORMANCE = {"altered-bytes-refused": "mutations", "state-fixture-v2-binds": "verify-releases"}


def load_json(name: str):
    return json.loads((HERE / name).read_text())


def inputs():
    return {
        "candidates": load_json("candidates.json"),
        "probe": {g: load_json(f"probe-{g}.json") for g in GENERATIONS},
        "summary": {
            (g, m): load_json(f"plans/{g}-{m}.summary.json")
            for g in GENERATIONS for m in ("full", "state-only")
        },
    }


def population_counts(generation: str) -> dict[str, int]:
    population = json.loads(Path("docs/kickoff/1384/population.json").read_text())[generation]
    return {
        "markets": len(population),
        "accounts": sum(len(m["accounts"]) for m in population.values()),
        "batches": 2 * sum(len(m["batch_expiries"]) for m in population.values()),
        "statuses": sum(len(m["account_batches"]) for m in population.values()),
    }


def mapped_words_proved(data, candidate) -> bool:
    mode = data["candidates"]["candidates"][candidate]["map"]
    for g in GENERATIONS:
        words = data["summary"][(g, mode)]["words"]
        need = population_counts(g)
        probe = data["probe"][g]
        fifo_entries = sum(v["entries"] for v in probe["fifo"].values())
        required = {
            "state": 4 * need["markets"], "fifo_head": need["markets"], "fifo_data": fifo_entries,
            "accounts": need["accounts"], "batches": need["batches"], "statuses": need["statuses"],
            "balances": need["markets"],
        }
        if any(words.get(k, 0) != v for k, v in required.items()):
            return False
    return True


def unexplained_mismatches(data, candidate) -> int:
    mode = data["candidates"]["candidates"][candidate]["map"]
    count = 0
    for g in GENERATIONS:
        probe = data["probe"][g]
        agreement = probe["agreement"]
        count += len(agreement["state_mismatch"]) + len(agreement["fifo_mismatch"])
        if mode == "state-only":
            continue
        count += len(agreement["accounts_mismatch"]) + len(agreement["statuses_mismatch"])
        for item in agreement["batches_mismatch"]:
            state = probe["state_decoded"][item["market"]]
            # A batch whose expiry is the market's pending expiry and has passed
            # is simulated as paid by the getter; the stored word is the fact.
            explained = (
                item["expiry"] == state["pendingWithdrawalExpiry"]
                and item["expiry"] <= probe["header"]["timestamp"]
            )
            count += 0 if explained else 1
    return count


def route_serves(data) -> bool:
    for g in GENERATIONS:
        probe = data["probe"][g]
        gateway = probe["routes"]["gateway"]
        if any(gateway[m]["outcome"] != "served" for m in ("eth_getProof", "eth_getBlockReceipts", "eth_getCode")):
            return False
        if probe["proof_set"]["proof_calls"] != probe["proof_set"]["targets"]:
            return False
    return True


def plan_validates(data, candidate) -> bool:
    mode = data["candidates"]["candidates"][candidate]["map"]
    sys.path.insert(0, str(Path("plugins/lazarus/scripts").resolve()))
    from lazarus_lib.capture import _validate_capture_plan  # noqa: E402
    from lazarus_lib.errors import LazarusError  # noqa: E402
    from lazarus_lib.schemas import validate_document  # noqa: E402

    for g in GENERATIONS:
        try:
            plan = json.loads((HERE / "plans" / f"{g}-{mode}.json").read_text())
            validate_document("plan", plan)
            _validate_capture_plan(plan)
        except (OSError, ValueError, LazarusError):
            return False
    return True


def no_provider_coordinate(data, candidate) -> bool:
    mode = data["candidates"]["candidates"][candidate]["map"]
    for g in GENERATIONS:
        raw = (HERE / "plans" / f"{g}-{mode}.json").read_bytes()
        if b"http" in raw or b"://" in raw or b"bearer" in raw.lower():
            return False
    return True


def projected_milliseconds(data, candidate) -> int:
    mode = data["candidates"]["candidates"][candidate]["map"]
    total = 0.0
    for g in GENERATIONS:
        probe = data["probe"][g]
        per_request = probe["throughput"]["milliseconds_per_request"]
        requests = data["summary"][(g, mode)]["requests"] + 2 * data["summary"][(g, mode)]["proof_targets"]
        proof_seconds = probe["proof_set"]["proof_route_seconds"]
        if mode == "state-only":
            full_slots = max(1, data["summary"][(g, "full")]["slots"])
            proof_seconds *= data["summary"][(g, mode)]["slots"] / full_slots
        total += requests * per_request + proof_seconds * 1000
    return int(total)


def estimated_fixture_bytes(data, generation: str, mode: str) -> int:
    probe = data["probe"][generation]
    if mode == "full":
        return probe["estimated_fixture_bytes"]
    summary = data["summary"][(generation, mode)]
    proofs = (
        summary["proof_targets"] * ACCOUNT_PROOF_BYTES
        + summary["slots"] * SLOT_PROOF_BYTES
        + 2 * probe["proof_set"]["code_bytes_raw"]
    )
    inventory = probe["inventory"]
    return (
        proofs
        + inventory["estimated_rpc_record_bytes_without_recorded_proofs"]
        + inventory["eth_getProof_recorded"] * ACCOUNT_PROOF_BYTES
        + probe["receipts"]["rpc_json_bytes"] + probe["receipts"]["consensus_json_bytes"]
        + probe["header"]["json_bytes"] + summary["bytes"]
    )


def in_tree_bytes(data, candidate) -> int:
    spec = data["candidates"]["candidates"][candidate]
    base = sum((HERE / name).stat().st_size for name in data["candidates"]["committed_design_files"])
    if spec["home"] != "in-tree":
        return base
    # A preservation release carries a second copy of the fixture beside the
    # statement and binding document, as the Aave v4 example does.
    return base + 2 * sum(estimated_fixture_bytes(data, g, spec["map"]) for g in GENERATIONS)


def interrupted_capture_leaves_nothing() -> bool:
    argv = [sys.executable, "-m", "unittest", "plugins.lazarus.tests.test_capture"]
    for name in GUARD_TESTS:
        argv += ["-k", name.split(".", 1)[1]]
    completed = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=600)
    return completed.returncode == 0 and "Ran 3 tests" in completed.stderr


def conformance(data, criterion: str) -> bool:
    demo = Path(data["candidates"]["example_dir"]) / "demo.py"
    if not demo.is_file():
        raise SystemExit(f"{criterion}: {demo} does not exist yet; this cell is due at integration")
    for name in data["candidates"]["release_env"]:
        if not os.environ.get(name):
            raise SystemExit(f"{criterion}: {name} is unset; name the local release tree it should read")
    argv = [sys.executable, str(demo), CONFORMANCE[criterion]]
    completed = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=3600)
    return completed.returncode == 0


def resolve(data, candidate: str, criterion: str):
    if candidate not in data["candidates"]["candidates"]:
        raise SystemExit(f"unknown candidate {candidate}")
    if criterion == "mapped-words-proved":
        return mapped_words_proved(data, candidate)
    if criterion == "unexplained-getter-mismatches":
        return unexplained_mismatches(data, candidate)
    if criterion == "capture-route-serves-boundary":
        return route_serves(data)
    if criterion == "plan-validates":
        return plan_validates(data, candidate)
    if criterion == "no-provider-coordinate-in-plan":
        return no_provider_coordinate(data, candidate)
    if criterion == "projected-capture-milliseconds":
        return projected_milliseconds(data, candidate)
    if criterion in ("in-tree-bytes-within-margin", "in-tree-bytes"):
        return in_tree_bytes(data, candidate)
    if criterion == "interrupted-capture-leaves-nothing":
        return interrupted_capture_leaves_nothing()
    if criterion in CONFORMANCE:
        return conformance(data, criterion)
    raise SystemExit(f"unknown criterion {criterion}")


def command_for(candidate: str, criterion: str, report: Path) -> str:
    return (
        f"python3 .hexaemeron/design/resolve.py --candidate {candidate} "
        f"--criterion {criterion} --report {report.as_posix()}"
    )


def write_report(candidate: str, criterion: str, value, report: Path) -> bytes:
    if os.path.lexists(report):
        raise SystemExit(f"refusing to overwrite {report}")
    unit = next(c["unit"] for c in CRITERIA if c["id"] == criterion)
    body = {
        "schema": REPORT_SCHEMA,
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": command_for(candidate, criterion, report),
        "exit": 0,
    }
    encoded = json.dumps(body, indent=1, sort_keys=True).encode() + b"\n"
    report.parent.mkdir(parents=True, exist_ok=True)
    with open(report, "xb") as handle:
        handle.write(encoded)
    print(encoded.decode(), end="")
    return encoded


def passes(criterion: dict, value) -> bool:
    if criterion["kind"] == "metric":
        return True
    threshold = criterion["threshold"]
    if criterion["comparator"] == "equals":
        return value == threshold
    if criterion["comparator"] == "at-most":
        return value <= threshold
    return value >= threshold


def write_record(data, reports_dir: Path, record: Path, report_digests: dict) -> None:
    if os.path.lexists(record):
        raise SystemExit(f"refusing to overwrite {record}")
    record_dir = record.resolve().parent
    results = []
    for candidate in data["candidates"]["candidates"]:
        for criterion in CRITERIA:
            report = reports_dir / f"{candidate}-{criterion['id']}.json"
            relative = report.resolve().relative_to(record_dir).as_posix()
            if criterion["stage"] == "conformance":
                results.append({
                    "candidate": candidate, "criterion": criterion["id"], "state": "pending",
                    "resolver": command_for(candidate, criterion["id"], report),
                    "report": relative, "blocks": criterion["blocks"],
                })
                continue
            digest, value = report_digests[(candidate, criterion["id"])]
            results.append({
                "candidate": candidate, "criterion": criterion["id"],
                "state": "pass" if passes(criterion, value) else "fail",
                "report": {"path": relative, "sha256": digest},
            })
    body = {
        "schema": RECORD_SCHEMA,
        "candidates": [
            {"id": cid, "summary": spec["summary"]}
            for cid, spec in data["candidates"]["candidates"].items()
        ],
        "criteria": CRITERIA,
        "results": results,
        "selection": data["candidates"]["selection"],
    }
    with open(record, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(body, indent=1) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate")
    parser.add_argument("--criterion")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--all", action="store_true", help="resolve every selection cell")
    parser.add_argument("--reports-dir", type=Path)
    parser.add_argument("--record", type=Path)
    args = parser.parse_args()
    data = inputs()
    if args.all:
        if not args.reports_dir or not args.record:
            parser.error("--all needs --reports-dir and --record")
        digests = {}
        for candidate in data["candidates"]["candidates"]:
            for criterion in CRITERIA:
                if criterion["stage"] != "selection":
                    continue
                report = args.reports_dir / f"{candidate}-{criterion['id']}.json"
                value = resolve(data, candidate, criterion["id"])
                encoded = write_report(candidate, criterion["id"], value, report)
                digests[(candidate, criterion["id"])] = (hashlib.sha256(encoded).hexdigest(), value)
        write_record(data, args.reports_dir, args.record, digests)
        return 0
    if not (args.candidate and args.criterion and args.report):
        parser.error("--candidate, --criterion and --report are required")
    value = resolve(data, args.candidate, args.criterion)
    write_report(args.candidate, args.criterion, value, args.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
