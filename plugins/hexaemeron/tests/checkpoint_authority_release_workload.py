#!/usr/bin/env python3
"""Replay the study's exact event schedule through signed protocol records.

The old unsigned model and its measurements remain unchanged. This fixture
maps every one of its 1,280 events to a signed protocol event, adds required
protocol evidence, and measures three fresh processes over the same bytes.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/hexaemeron/skills/fiat/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_authority.canonical import canonical, digest
from checkpoint_authority.replay import Replay, RETAIN, TRUST_TYPES
import checkpoint_authority_replay_fixture as fixture
from test_checkpoint_authority_records import tools

RELATIVE = "plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/study-workload.json"
PATH = ROOT / RELATIVE
METADATA = PATH.with_name("study-workload-metadata.json")
STUDY_SHA = "cf56704482a20f2d7d7d03d26c1eed8f54d9bf9d5d2d45bb64c18c1d3e8474ae"
PROJECTION_SHA = "3e51e417e044849260c320091812df58257cdf79ce112470e16eca2c3e2e54f8"
ACTIONS = {"acceptance": "authorize", "publication-finalization": "finalize",
           "stream-permit": "permit", "denial": "deny", "cancellation": "cancel"}
REPETITIONS = 3


def study_rows(decisions=512):
    """Reproduce the immutable research corpus, including its evidence padding."""
    rows = []
    previous = "0" * 64
    for decision in range(decisions):
        for action in (("authorize", "finalize", "permit", "deny") if decision % 2 == 0 else ("cancel",)):
            value = {"schema": "p862-study-journal/v0", "environment": "test:surveyor-1676",
                     "sequence": len(rows) + 1, "previous": previous, "kind": action,
                     "decision": str(decision), "evidence": [digest(f"{decision}:{i}".encode()) for i in range(16)]}
            raw = canonical(value)
            rows.append((value, raw))
            previous = digest(b"p862-study-journal-v0\0" + raw)
    return rows


class WorkloadHistory(fixture.History):
    """Independent synthetic roots keep the model's decisions independent."""
    def __init__(self, signer):
        self.model_decision = 0
        self.copy_cache = {}
        self.mapping = []
        super().__init__(signer)

    def _producer(self):
        old = json.loads(self.producer.splitlines()[-1])["hash"] if self.producer else "genesis"
        row = {"ts": "2026-09-16T00:00:00Z", "event": "init" if not self.producer else "done:push",
               "data": {"synthetic_model_decision": self.model_decision}, "prev": old, "state": "2" * 64}
        row["hash"] = digest(canonical(row))
        self.producer += canonical(row) + b"\n"

    def copies(self, artifact):
        key = (artifact["sha256"], artifact["length"])
        if key not in self.copy_cache:
            self.copy_cache[key] = super().copies(artifact)
        return self.copy_cache[key]

    def event(self, value, decision=None):
        reference = super().event(value, decision)
        self.mapping.append({"sequence": len(self.mapping) + 1,
                             "decision": str(self.model_decision), "action": ACTIONS[value["type"]],
                             "envelope_sha256": reference["sha256"]})
        return reference


def build(decisions=512):
    rows = study_rows(decisions)
    fixture.Signer.setUpClass()
    try:
        history = WorkloadHistory(fixture.Signer())
        for number in range(decisions):
            history.model_decision = number
            name = "study-%d" % number
            if number % 2:
                record = history.body("cancellation")
                decision = digest(name.encode())
                record.update(candidate_id=name, decision_id=decision)
                history.event(record, decision)
                history.head()
            else:
                history.parents = []
                history.producer = b""
                history._producer()
                receipt, acceptance = history.accept(name)
                history.permit(receipt, acceptance, nonce=name, session=name)
                history.deny(receipt, poison=False)
        exported = fixture.export(history)
        for (model, _), mapped in zip(rows, history.mapping, strict=True):
            assert (model["sequence"], model["decision"], model["kind"]) == (
                mapped["sequence"], mapped["decision"], mapped["action"])
        return {"schema": "checkpoint-authority-study-workload/v1",
                "study_corpus_sha256": digest(b"\n".join(raw for _, raw in rows) + b"\n"),
                "model_events": len(rows), "model_decisions": decisions,
                "mapping": history.mapping, "history": exported}
    finally:
        fixture.Signer.tearDownClass()


def measure(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    history = value["history"]
    expected_rows = study_rows()
    expected_sha = digest(b"\n".join(raw for _, raw in expected_rows) + b"\n")
    assert value["study_corpus_sha256"] == expected_sha == STUDY_SHA
    assert value["model_events"] == len(expected_rows) == 1280 and value["model_decisions"] == 512
    assert len(value["mapping"]) == 1280
    for (expected, _), mapped in zip(expected_rows, value["mapping"], strict=True):
        assert set(mapped) == {"sequence", "decision", "action", "envelope_sha256"}
        assert (mapped["sequence"], mapped["decision"], mapped["action"]) == (
            expected["sequence"], expected["decision"], expected["kind"])
    pinned_tools = tools()
    bootstrap, native, fresh = fixture.bootstrap_of(history), fixture.native_of(history), fixture.freshness_of(history)
    counts = {"carrier": 0, "signed_statement": 0, "additional_record_body": 0,
              "native_result": 0, "producer_ledger_line": 0, "other": 0}
    original = json.loads

    def observe(data, *args, **kwargs):
        parsed = original(data, *args, **kwargs)
        if isinstance(parsed, dict) and "payloadType" in parsed: counts["carrier"] += 1
        elif isinstance(parsed, dict) and "predicateType" in parsed: counts["signed_statement"] += 1
        elif isinstance(parsed, dict) and parsed.get("protocol") == "checkpoint-authority/v1": counts["additional_record_body"] += 1
        elif isinstance(parsed, dict) and parsed.get("schema") == "checkpoint-authority-native-result/v1": counts["native_result"] += 1
        elif isinstance(parsed, dict) and "prev" in parsed and "hash" in parsed: counts["producer_ledger_line"] += 1
        else: counts["other"] += 1
        return parsed

    reader = Replay(bootstrap, pinned_tools, native_evidence=native, freshness=fresh)
    mapped_index = 0
    decision_keys = {}
    json.loads = observe
    tracemalloc.start()
    started = time.perf_counter_ns()
    try:
        for encoded in history["envelopes"]:
            envelope = base64.b64decode(encoded, validate=True)
            identity = reader.append(envelope)
            if reader.pending is None:
                continue
            _, record = reader.pending
            mapped = value["mapping"][mapped_index]
            mapped_index += 1
            number = mapped["decision"]
            assert identity == mapped["envelope_sha256"] and ACTIONS[record["type"]] == mapped["action"]
            if record["type"] == "acceptance":
                key = record["identities"]["snapshot_id"]
                endorsement = reader.record(record["endorsement"], "upload-endorsement")
                assert endorsement["candidate_id"] == "study-" + number
                decision_keys[number] = key
            elif record["type"] == "cancellation":
                key = record["decision_id"]
                assert key == digest(("study-" + number).encode()) and record["candidate_id"] == "study-" + number
                decision_keys[number] = key
            elif record["type"] == "denial":
                assert record["target"] == {"kind": "snapshot", "snapshot_id": decision_keys[number]}
            else:
                assert reader.acceptances[record["acceptance_id"]] == decision_keys[number]
        result = reader.finish(presence={(sha, role): True for sha, _ in reader.copies for role in ("primary", "recovery")})
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        _, traced = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
        json.loads = original
    assert mapped_index == 1280 and len(decision_keys) == 512
    projection = {number: reader.index.states[key] for number, key in decision_keys.items()}
    assert digest(canonical(projection)) == PROJECTION_SHA
    # Only declared projections may survive. Trust history has its own bounded custody.
    retained = sum(1 for node in reader.nodes.values()
                   if type(node["value"]) in (bytes, bytearray) or
                   (node["type"] not in TRUST_TYPES and
                    set(node["value"]) - {"type", *RETAIN.get(node["type"], ())}))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"workload_sha256": digest(raw), "study_corpus_sha256": STUDY_SHA,
            "projection_sha256": digest(canonical(projection)), "model_events": mapped_index,
            "model_decisions": len(projection), "records": result["records"], "bytes": result["bytes"],
            "accepted": len(result["accepted"]), "cancelled": result["cancelled"],
            "denied": sum(row["current_eligibility"] == "denied" for row in result["accepted"]),
            "historical_permits": result["historical_permits"], "decodes": counts,
            "journal_body_decodes": counts["signed_statement"] + counts["additional_record_body"],
            "json_decodes_total": sum(counts.values()),
            "retained_body_nodes": retained, "wall_ms": round(elapsed_ms, 3),
            "tracemalloc_peak_bytes": traced, "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024}


def benchmark():
    samples = []
    for _ in range(REPETITIONS):
        result = subprocess.run([sys.executable, __file__, "--measure", str(PATH)], capture_output=True,
                                check=True, cwd=ROOT, timeout=600,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        samples.append(json.loads(result.stdout))
    stable = {key: value for key, value in samples[0].items()
              if key not in ("wall_ms", "tracemalloc_peak_bytes", "peak_rss_bytes")}
    assert all({key: row[key] for key in stable} == stable for row in samples)
    walls = [row["wall_ms"] for row in samples]
    processor = platform.processor() or "unknown"
    if sys.platform == "darwin":
        processor = subprocess.run(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"],
                                   capture_output=True, text=True, check=True, timeout=5).stdout.strip()
    return {"schema": "checkpoint-authority-release-workload-measurement/v1", **stable,
            "samples": [{key: row[key] for key in ("wall_ms", "tracemalloc_peak_bytes", "peak_rss_bytes")}
                        for row in samples],
            "repetitions": REPETITIONS, "wall_ms_median": statistics.median(walls),
            "wall_ms_p95": sorted(walls)[math.ceil(0.95 * len(walls)) - 1],
            "percentile_method": "nearest-rank", "warmup_repetitions": 0,
            "environment": {"python": sys.version.split()[0], "platform": platform.platform(),
                            "machine": platform.machine(), "processor": processor,
                            "logical_cpus": os.cpu_count(), "measurement": "fresh-process-per-repetition",
                            "contention": "uncontrolled host activity; no latency or throughput claim"}}


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        data = build()
        assert data["study_corpus_sha256"] == STUDY_SHA
        PATH.write_text(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")
        expected = data["history"]["expected"]
        metadata = {"schema": "checkpoint-authority-study-workload-metadata/v1",
                    "workload_sha256": digest(PATH.read_bytes()), "study_corpus_sha256": STUDY_SHA,
                    "projection_sha256": PROJECTION_SHA, "model_events": 1280, "model_decisions": 512,
                    "records": expected["records"], "bytes": expected["bytes"], "accepted": 256,
                    "denied": 256, "cancelled": 256, "historical_permits": 256}
        METADATA.write_text(json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n")
        print(json.dumps({"bytes": PATH.stat().st_size, "sha256": digest(PATH.read_bytes()),
                          "model_events": data["model_events"], "records": data["history"]["expected"]["records"]}))
    elif len(sys.argv) == 3 and sys.argv[1] == "--measure":
        print(json.dumps(measure(Path(sys.argv[2])), sort_keys=True))
    elif sys.argv[1:] == ["--benchmark"]:
        print(json.dumps(benchmark(), sort_keys=True))
    else:
        raise SystemExit("use --write, --measure <path> or --benchmark")
