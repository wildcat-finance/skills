#!/usr/bin/env python3
"""Hold the complete Synkrisis path to its declared work budget.

The committed scale fixture is a small deterministic specification; this
command materialises the full 100-run, 100,000-event universe from it into a
private temporary directory, runs cohort construction, diagnosis and
verification over that universe, and refuses when the slowest repetition
exceeds the budget. The result is a bounded implementation budget on the
recorded interpreter and platform, not a claim about other machines or larger
cohorts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import shutil
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import synkrisis  # noqa: E402  (sibling module, loaded by fixed path)

SPEC_SCHEMA = "synkrisis-scale-fixture/v1"


def load_spec(path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    expected = {"schema", "runs", "events_per_run", "seed"}
    if set(document) != expected or document["schema"] != SPEC_SCHEMA:
        raise SystemExit(f"unsupported scale fixture specification: {path}")
    return document


def synthetic_run(run_id: str, index: int, events_per_run: int):
    """One deterministic synthetic record; content varies only with index."""
    lines = []
    correlation = f"corr-{run_id}"

    def stamp(sequence):
        minute, second = divmod(sequence % 3_600, 60)
        return f"2026-08-27T{11 + (index % 12):02d}:{minute:02d}:{second:02d}Z"

    def emit(sequence, event_type, **extra):
        document = {
            "schema_id": synkrisis.PRODUCER_CONTRACT,
            "run_id": run_id,
            "sequence": sequence,
            "event_id": f"evt-{sequence}",
            "time": stamp(sequence),
            "type": event_type,
            "correlation_id": correlation,
        }
        document.update(extra)
        lines.append(
            json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
        )

    emit(
        1,
        "run.started",
        context={
            "issue_or_topic": f"scale-{run_id}",
            "promise_id": "synkrisis-scale",
            "role": "worker",
            "selected_skill": "mason",
            "step": f"step-{index}",
        },
        scope="synkrisis scale fixture",
        subject=run_id,
    )
    boundary_at = 2 if index % 2 == 0 else events_per_run - 4
    sequence = 2
    capability_counter = 0
    while sequence < events_per_run:
        capability_counter += 1
        capability_id = f"cap-{capability_counter}"
        if sequence == boundary_at:
            capability = "repository.boundary.read"
            metadata = {"path": ".horos/boundary.json"}
        else:
            capability = "target.tests.run"
            metadata = {"selector": f"case-{sequence % 97}"}
        emit(
            sequence,
            "capability.started",
            capability=capability,
            capability_id=capability_id,
            metadata=metadata,
        )
        sequence += 1
        if sequence >= events_per_run:
            break
        emit(
            sequence,
            "capability.finished",
            capability_id=capability_id,
            started_event_id=f"evt-{sequence - 1}",
            status="success",
            duration_ms=3,
            token_usage={
                "accounting_id": "scale-usage",
                "input_tokens": 6,
                "output_tokens": 4 + (index % 7) + (2 if boundary_at != 2 else 0),
                "scope": "capability",
                "source": "scale-host",
            },
        )
        sequence += 1
    emit(
        sequence,
        "run.finished",
        status="success",
        started_event_id="evt-1",
        outcome={"subject": run_id, "summary": "scale fixture run accepted"},
    )
    return "".join(lines).encode("ascii")


def materialise(spec, workspace: Path):
    records = workspace / "records"
    records.mkdir(parents=True)
    manifest_runs = []
    for index in range(spec["runs"]):
        run_id = f"run-{index:03d}"
        payload = synthetic_run(run_id, index, spec["events_per_run"])
        path = records / f"{run_id}.jsonl"
        path.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        manifest_runs.append(
            {
                "run_id": run_id,
                "record": f"records/{run_id}.jsonl",
                "sha256": digest,
                "bytes": len(payload),
                "validation": {"tool": "constructed-scale-fixture", "status": "accepted"},
                "redaction": {
                    "profile": "promise-machine-run-observation-capture/v1",
                    "status": "accepted",
                },
                "binding": {
                    "status": "bound",
                    "receipt": f"scale-receipt-{run_id}",
                    "bound_bytes": len(payload),
                    "bound_events": payload.count(b"\n"),
                    "sha256": digest,
                },
            }
        )
    manifest = {
        "schema": "synkrisis-manifest/v1",
        "producer_contract": synkrisis.PRODUCER_CONTRACT,
        "runs": manifest_runs,
    }
    (workspace / "manifest.json").write_bytes(synkrisis.canonical_bytes(manifest))
    policy = {
        "schema": "synkrisis-policy/v1",
        "name": "scale-fixture",
        "dimensions": {
            "context.issue_or_topic": {"rule": "differ"},
            "context.promise_id": {"rule": "differ"},
            "context.role": {"rule": "match", "value": "worker"},
            "context.selected_skill": {"rule": "match", "value": "mason"},
            "context.step": {"rule": "differ"},
        },
        "token_accounting": "require-equal",
    }
    (workspace / "policy.json").write_bytes(synkrisis.canonical_bytes(policy))


def run_path(workspace: Path, rules: Path):
    shutil.copyfile(rules, workspace / "rules.json")
    arguments = argparse.Namespace(
        manifest="manifest.json",
        policy="policy.json",
        out="out/cohort.json",
        json=False,
    )
    synkrisis.command_cohort(workspace, arguments)
    arguments = argparse.Namespace(
        cohort="out/cohort.json",
        rules="rules.json",
        out="out/findings.json",
        json=False,
    )
    synkrisis.command_diagnose(workspace, arguments)
    arguments = argparse.Namespace(
        manifest="manifest.json",
        policy="policy.json",
        cohort="out/cohort.json",
        rules="rules.json",
        findings="out/findings.json",
        report="out/report.md",
        json=False,
    )
    render = argparse.Namespace(
        findings="out/findings.json", out="out/report.md", json=False
    )
    synkrisis.command_render(workspace, render)
    synkrisis.command_verify(workspace, arguments)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, help="scale fixture directory")
    parser.add_argument("--max-seconds", type=float, required=True)
    parser.add_argument("--max-rss-mib", type=int, required=True)
    parser.add_argument("--repetitions", type=int, default=1)
    arguments = parser.parse_args(argv)

    fixture = Path(arguments.fixture)
    spec_path = fixture / "spec.json"
    spec = load_spec(spec_path)
    spec_digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    rules = SCRIPTS.parent / "references" / "rules-v1.json"

    durations = []
    for _ in range(max(1, arguments.repetitions)):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw).resolve()
            materialise(spec, workspace)
            started = time.monotonic()
            run_path(workspace, rules)
            durations.append(time.monotonic() - started)
    peak_rss_mib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024

    result = {
        "fixture_spec_sha256": spec_digest,
        "runs": spec["runs"],
        "events_per_run": spec["events_per_run"],
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repetitions": len(durations),
        "max_seconds_observed": round(max(durations), 3),
        "max_seconds_budget": arguments.max_seconds,
        "peak_rss_mib": peak_rss_mib,
        "max_rss_mib_budget": arguments.max_rss_mib,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    if max(durations) > arguments.max_seconds or peak_rss_mib > arguments.max_rss_mib:
        print("refused: the recorded budget was exceeded")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
