"""Shared fixtures for the Synkrisis suite: loaders, builders, tiny universes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SCRIPTS = PLUGIN_ROOT / "scripts"
EXAMPLE = PLUGIN_ROOT / "examples" / "cross-run-v0"

_MODULES = {}


def load_module(name, path):
    key = (name, str(path))
    if key not in _MODULES:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        _MODULES[key] = module
    return _MODULES[key]


def synkrisis():
    return load_module("synkrisis_under_test", SCRIPTS / "synkrisis.py")


def namespace(**values):
    values.setdefault("json", False)
    return argparse.Namespace(**values)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write(root: Path, relative: str, payload: bytes) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return target


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(document) -> bytes:
    return synkrisis().canonical_bytes(document)


def example_policy() -> dict:
    return read_json(EXAMPLE / "policy.json")


def example_manifest() -> dict:
    return read_json(EXAMPLE / "manifest.json")


def stage_example(root: Path) -> tuple[dict, dict]:
    """Copy the example universe into a scratch root with local paths."""
    manifest = example_manifest()
    for row in manifest["runs"]:
        source = REPO_ROOT / row["record"]
        local = f"records/{Path(row['record']).name}"
        write(root, local, source.read_bytes())
        row["record"] = local
    policy = example_policy()
    return manifest, policy


def stage_inputs(root: Path, manifest: dict, policy: dict):
    write(root, "manifest.json", canonical(manifest))
    write(root, "policy.json", canonical(policy))


def run_cohort(root: Path, out="out/cohort.json", **overrides):
    arguments = namespace(
        manifest=overrides.pop("manifest", "manifest.json"),
        policy=overrides.pop("policy", "policy.json"),
        out=out,
        **overrides,
    )
    return synkrisis().command_cohort(root, arguments)


def event(run_id, seq, typ, second, corr, **extra):
    document = {
        "schema_id": "promise-machine-run-observation/v1",
        "run_id": run_id,
        "sequence": seq,
        "event_id": f"evt-{seq}",
        "time": f"2026-08-27T12:{second // 60:02d}:{second % 60:02d}Z",
        "type": typ,
        "correlation_id": corr,
    }
    if seq > 1:
        document["parent_event_id"] = f"evt-{seq - 1}"
    document.update(extra)
    return document


def encode(events) -> bytes:
    return "".join(
        json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n"
        for item in events
    ).encode("ascii")


def simple_record(
    run_id,
    *,
    skill="mason",
    accounting="demo-host-usage",
    output_tokens=25,
    boundary_at=None,
    status="success",
):
    """A minimal record accepted by Synkrisis's admission checks."""
    corr = f"corr-{run_id}"
    events = [
        event(
            run_id,
            1,
            "run.started",
            0,
            corr,
            context={
                "issue_or_topic": f"fixture-{run_id}",
                "promise_id": "synkrisis-fixture",
                "role": "worker",
                "selected_skill": skill,
                "step": "fixture-step",
            },
            scope="synkrisis fixture",
            subject=run_id,
        )
    ]
    sequence = 2
    if boundary_at == "early":
        events.append(
            event(
                run_id,
                sequence,
                "capability.started",
                sequence,
                corr,
                capability="repository.boundary.read",
                capability_id="cap-b",
                metadata={"path": ".horos/boundary.json"},
            )
        )
        sequence += 1
    for index in range(3):
        events.append(
            event(
                run_id,
                sequence,
                "capability.started",
                sequence,
                corr,
                capability="target.tests.run",
                capability_id=f"cap-{index}",
                metadata={"selector": "test_demo"},
            )
        )
        sequence += 1
        events.append(
            event(
                run_id,
                sequence,
                "capability.finished",
                sequence,
                corr,
                capability_id=f"cap-{index}",
                started_event_id=f"evt-{sequence - 1}",
                status="success",
                duration_ms=2,
                token_usage={
                    "accounting_id": accounting,
                    "input_tokens": output_tokens,
                    "output_tokens": output_tokens,
                    "scope": "capability",
                    "source": "fixture-host",
                },
            )
        )
        sequence += 1
    if boundary_at == "late":
        events.append(
            event(
                run_id,
                sequence,
                "capability.started",
                sequence,
                corr,
                capability="repository.boundary.read",
                capability_id="cap-b",
                metadata={"path": ".horos/boundary.json"},
            )
        )
        sequence += 1
    events.append(
        event(
            run_id,
            sequence,
            "run.finished",
            sequence,
            corr,
            status=status,
            started_event_id="evt-1",
            outcome={"subject": run_id, "summary": "fixture run recorded"},
        )
    )
    return encode(events)


def manifest_row(run_id, record_path, payload, *, binding=None):
    digest = sha256(payload)
    if binding is None:
        binding = {
            "status": "bound",
            "receipt": f"fixture-receipt-{run_id}",
            "bound_bytes": len(payload),
            "bound_events": payload.count(b"\n"),
            "sha256": digest,
        }
    return {
        "run_id": run_id,
        "record": record_path,
        "sha256": digest,
        "bytes": len(payload),
        "validation": {"tool": "scripts/run_observation.py", "status": "accepted"},
        "redaction": {
            "profile": "promise-machine-run-observation-capture/v1",
            "status": "accepted",
        },
        "binding": binding,
    }


def fixture_manifest(rows):
    return {
        "schema": "synkrisis-manifest/v1",
        "producer_contract": "promise-machine-run-observation/v1",
        "runs": rows,
    }


def fixture_policy(**overrides):
    policy = {
        "schema": "synkrisis-policy/v1",
        "name": "fixture-policy",
        "dimensions": {
            "context.issue_or_topic": {"rule": "differ"},
            "context.promise_id": {"rule": "differ"},
            "context.role": {"rule": "match", "value": "worker"},
            "context.selected_skill": {"rule": "match", "value": "mason"},
            "context.step": {"rule": "differ"},
        },
        "token_accounting": "require-equal",
    }
    policy.update(overrides)
    return policy


def stage_pair(root: Path, records: dict[str, bytes], *, policy=None,
               bindings: dict | None = None):
    """Write records, a matching manifest and a policy into a root."""
    rows = []
    for run_id, payload in records.items():
        relative = f"records/{run_id}.jsonl"
        write(root, relative, payload)
        rows.append(
            manifest_row(
                run_id,
                relative,
                payload,
                binding=(bindings or {}).get(run_id),
            )
        )
    manifest = fixture_manifest(rows)
    stage_inputs(root, manifest, policy or fixture_policy())
    return manifest


def copy_example_into(root: Path):
    manifest, policy = stage_example(root)
    stage_inputs(root, manifest, policy)
    return manifest, policy


def clean_tree(path: Path):
    if path.exists():
        shutil.rmtree(path)
