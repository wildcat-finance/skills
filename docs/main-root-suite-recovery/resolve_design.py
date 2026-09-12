#!/usr/bin/env python3
"""Resolve the bounded pre-build comparisons for issue 1538."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "scripts/agent_instruction.py").is_file())
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
CANDIDATES = ("absolute-refresh", "relative-schema")
CRITERIA = ("reviewed-bindings-preserved", "v1-source-binding-compatibility",
            "profile-identity-commands", "projected-representation-bytes",
            "verified-recovery-source")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode() + b"\n"


def probe(candidate):
    manifest = json.loads((ROOT / "tests/fixtures/agent-instruction-v1/manifest.json").read_bytes())
    fixture = next(x for x in manifest["fixtures"] if x["id"] == "promise-machine-router-selection")
    source = fixture["source"]
    old = subprocess.run(["git", "show", "49fc2caf^:PROMISE_MACHINE.md"], cwd=ROOT,
                         check=True, capture_output=True).stdout
    assert digest(old) == source["sha256"], "the recovery commit does not contain the pinned law"
    live = (ROOT / source["path"]).read_bytes()
    reviewed = old[int(source["start"]):int(source["end"])]
    assert digest(reviewed) == source["span_sha256"]
    assert live.count(reviewed) == 1, "reviewed source is absent or ambiguous"
    new_start = live.index(reviewed)
    delta = new_start - int(source["start"])
    model = json.loads((ROOT / fixture["artifacts"]["model"]["path"]).read_bytes())
    transformed = copy.deepcopy(model)
    transformed["sources"][0]["sha256"] = digest(live)
    preserved = 0
    compatible = 0
    for before, after in zip(model["bindings"], transformed["bindings"]):
        old_span = old[int(before["start"]):int(before["end"])]
        start, end = int(before["start"]) + delta, int(before["end"]) + delta
        assert live[start:end] == old_span
        if candidate == "relative-schema":
            start -= new_start
            end -= new_start
        after["start"], after["end"] = str(start), str(end)
        candidate_span = live[start:end] if candidate == "absolute-refresh" else live[new_start + start:new_start + end]
        preserved += candidate_span == old_span
        compatible += live[start:end] == old_span
    spec = importlib.util.spec_from_file_location("issue1538_codec", ROOT / "scripts/agent_instruction.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    compact = module.format_compact(transformed)
    candidate_manifest = copy.deepcopy(manifest)
    candidate_manifest["fixtures"][-1]["source"]["sha256"] = digest(live)
    size = sum(len(module.digest_neutral_projection(candidate_manifest, data))
               for data in (canonical(transformed), compact))
    observations = json.loads((HERE / "runtime-identity-observations.json").read_bytes())
    commands = []
    for profile in observations["profiles"]:
        assert profile["observed_blobs"] == profile["expected_blobs"]
        for kind in ("version", "identity"):
            assert profile[kind]["exit"] == 0
            commands.append(profile[kind]["argv"])
    return {
        "reviewed-bindings-preserved": (preserved, "count"),
        "v1-source-binding-compatibility": (compatible, "count"),
        "profile-identity-commands": (len(commands), "count"),
        "projected-representation-bytes": (size, "bytes"),
        "verified-recovery-source": (digest(old) == source["sha256"], "boolean"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=CANDIDATES, required=True)
    parser.add_argument("--criterion", choices=CRITERIA, required=True)
    args = parser.parse_args()
    value, unit = probe(args.candidate)[args.criterion]
    command = f"python3 {SELF} --candidate {args.candidate} --criterion {args.criterion}"
    report = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
              "criterion": args.criterion, "value": value, "unit": unit,
              "command": command, "exit": 0}
    destination = HERE / "reports" / f"{args.candidate}-{args.criterion}.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(json.dumps(report, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
