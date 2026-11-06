#!/usr/bin/env python3
"""Measure one-body-at-a-time replay against the study's declared budget.

`--write` signs a workload of at least 1,280 protocol records with ephemeral
keys, replays it three times in fresh processes, and records the decode
counts, peak process RSS, traced allocation and wall time beside the budget
the study declared. `--measure <dir>` is the child that replays one exported
history and prints its own observations. The record is an observation on one
machine; it is not a production latency or throughput claim.
"""
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/hexaemeron/skills/fiat/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

BUDGET = {"records_minimum": 1280, "signed_body_decodes_per_record_maximum": 1,
          "carrier_decodes_per_record_maximum": 1, "peak_rss_bytes_maximum": 512 * 1024 * 1024,
          "retained_body_collection": False}
STUDY = {"decode_work": 1280, "resident_memory_traced_bytes": 266697,
         "corpus_sha256": "cf56704482a20f2d7d7d03d26c1eed8f54d9bf9d5d2d45bb64c18c1d3e8474ae",
         "note": "The study measured a closed synthetic journal model with bare JSON records and no signatures; "
                 "this record measures the protocol replay over signed DSSE envelopes with real public-key verification."}
OUT = ROOT / "plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/replay-budget.json"


def rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def measure(directory):
    import checkpoint_authority_replay_fixture as fixture
    from test_checkpoint_authority_records import tools
    history = fixture.load_history(directory / "history.json")
    counts = {"carrier": 0, "signed_body": 0, "native_result": 0, "producer_ledger_line": 0, "other": 0}
    original = json.loads

    def observe(raw, *args, **kwargs):
        value = original(raw, *args, **kwargs)
        if isinstance(value, dict) and "payloadType" in value: counts["carrier"] += 1
        elif isinstance(value, dict) and "predicateType" in value: counts["signed_body"] += 1
        elif isinstance(value, dict) and value.get("schema") == "checkpoint-authority-native-result/v1": counts["native_result"] += 1
        elif isinstance(value, dict) and "prev" in value and "hash" in value: counts["producer_ledger_line"] += 1
        else: counts["other"] += 1
        return value

    json.loads = observe
    try:
        tracemalloc.start()
        started = time.perf_counter_ns()
        reader = fixture.replay_history(history, tools(), with_freshness=True)
        result = reader.finish(presence={(sha, role): True for sha, _ in reader.copies for role in ("primary", "recovery")})
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        _, traced_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    finally:
        json.loads = original
    retained = [node for node in reader.nodes.values() if isinstance(node["value"], (bytes, bytearray))]
    print(json.dumps({"records": result["records"], "bytes": result["bytes"], "decisions": len(reader.decisions),
        "accepted": len(result["accepted"]), "decodes": counts, "wall_ms": elapsed_ms,
        "tracemalloc_peak_bytes": traced_peak, "peak_rss_bytes": rss_bytes(), "retained_body_nodes": len(retained),
        "eligible": sum(row["current_eligibility"] == "eligible" for row in result["accepted"])}))


def workload():
    import checkpoint_authority_replay_fixture as fixture
    fixture.Signer.setUpClass()
    try:
        built = fixture.History(fixture.Signer())
        acceptances = 0
        while len(built.envelopes) < BUDGET["records_minimum"]:
            receipt, acceptance_id = built.accept("workload-%d" % acceptances)
            built.permit(receipt, acceptance_id, nonce="nonce-%d" % acceptances, session="session-%d" % acceptances)
            acceptances += 1
        exported = fixture.export(built)
    finally:
        fixture.Signer.tearDownClass()
    return exported, acceptances


def write():
    exported, acceptances = workload()
    with tempfile.TemporaryDirectory(prefix="checkpoint-replay-budget-") as temporary:
        directory = Path(temporary)
        (directory / "history.json").write_bytes(json.dumps(exported, sort_keys=True, separators=(",", ":")).encode())
        samples = []
        for _ in range(3):
            child = subprocess.run([sys.executable, __file__, "--measure", str(directory)], capture_output=True,
                                   check=True, cwd=ROOT, timeout=1800, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            samples.append(json.loads(child.stdout))
    first = samples[0]
    records = first["records"]
    measured = {
        "records": records, "envelope_bytes": first["bytes"], "decisions": first["decisions"], "acceptances": acceptances,
        "signed_body_decodes": first["decodes"]["signed_body"], "carrier_decodes": first["decodes"]["carrier"],
        "native_result_decodes": first["decodes"]["native_result"],
        "producer_ledger_line_decodes": first["decodes"]["producer_ledger_line"], "other_decodes": first["decodes"]["other"],
        "retained_body_nodes": first["retained_body_nodes"], "eligible": first["eligible"],
        "peak_rss_bytes": {"samples": [row["peak_rss_bytes"] for row in samples], "max": max(row["peak_rss_bytes"] for row in samples)},
        "tracemalloc_peak_bytes": {"samples": [row["tracemalloc_peak_bytes"] for row in samples], "max": max(row["tracemalloc_peak_bytes"] for row in samples)},
        "wall_ms": {"samples": [round(row["wall_ms"], 3) for row in samples], "median": round(statistics.median(row["wall_ms"] for row in samples), 3)},
    }
    assert all(row["records"] == records and row["decodes"] == first["decodes"] for row in samples), samples
    verdict = {
        "records_at_least_minimum": records >= BUDGET["records_minimum"],
        "one_signed_body_decode_per_record": measured["signed_body_decodes"] == records,
        "one_carrier_decode_per_record": measured["carrier_decodes"] == records,
        "no_retained_body_collection": measured["retained_body_nodes"] == 0,
        "peak_rss_under_budget": measured["peak_rss_bytes"]["max"] < BUDGET["peak_rss_bytes_maximum"],
        "every_acceptance_eligible_under_fresh_head": measured["eligible"] == measured["acceptances"] == first["accepted"],
    }
    record = {"schema": "checkpoint-authority-replay-budget/v1", "discipline": "metron", "candidate": "ordered-replay",
        "command": "python3 plugins/hexaemeron/tests/checkpoint_authority_replay_budget.py --write",
        "budget": BUDGET, "measured": measured, "verdict": verdict, "passed": all(verdict.values()),
        "study_comparison": STUDY,
        "environment": {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine(),
                        "repetitions": len(samples), "measurement": "fresh child process per repetition; ru_maxrss covers the whole child",
                        "signature_verification": "real pinned openssl, ssh-keygen and gpg subprocesses per envelope; timing includes them"},
        "limits": "One machine, one synthetic workload signed with ephemeral test keys and unexecuted synthetic native attestations. "
                  "No production latency, archive validation time, filesystem overhead or provider cost is established."}
    OUT.write_bytes((json.dumps(record, sort_keys=True, indent=2) + "\n").encode())
    print(json.dumps({"records": records, "peak_rss_bytes": measured["peak_rss_bytes"]["max"],
                      "wall_ms_median": measured["wall_ms"]["median"], "passed": record["passed"]}))
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    if sys.argv[1:2] == ["--measure"] and len(sys.argv) == 3:
        measure(Path(sys.argv[2]))
    elif sys.argv[1:] == ["--write"]:
        raise SystemExit(write())
    else:
        raise SystemExit("use --write or --measure <dir>")
