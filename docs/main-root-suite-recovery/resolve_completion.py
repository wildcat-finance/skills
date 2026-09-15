#!/usr/bin/env python3
"""Run the completion checks named by the issue 1538 design record."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "scripts/agent_instruction.py").is_file())
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()


def command(argv, name, timeout=1800, env=None):
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout, env=env)
    (HERE / (name + ".stdout")).write_bytes(result.stdout)
    (HERE / (name + ".stderr")).write_bytes(result.stderr)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("absolute-refresh", "relative-schema"), required=True)
    parser.add_argument("--criterion", choices=("active-root-green", "full-checks-green", "corpus-check-accepted", "package-headroom", "required-invariants"), required=True)
    args = parser.parse_args()
    criterion = args.criterion
    if criterion == "active-root-green":
        # The tracked gate runs the exact active root suite and records its
        # staged tree only after success. Keep python3 on this pinned runtime.
        environment = dict(os.environ)
        environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + environment.get("PATH", "")
        result = command(["/bin/sh", ".githooks/greenlight"], criterion, env=environment)
        value, unit = result.returncode == 0, "boolean"
    elif criterion == "full-checks-green":
        result = command([sys.executable, "scripts/run_checks.py", "--full", "--jobs", "12", "--format", "json", "--report", ".hexaemeron/full-completion-checks.json"], criterion)
        value, unit = result.returncode == 0, "boolean"
    elif criterion == "corpus-check-accepted":
        result = command([sys.executable, "scripts/agent_instruction.py", "check", "--manifest", "tests/fixtures/agent-instruction-v1/manifest.json"], criterion)
        records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        summary = records[-1] if records else {}
        value = result.returncode == 0 and summary.get("event") == "run.summary" and summary.get("outcome") == "accepted" and summary.get("fixture_count") == 3 and all(summary.get(key) == 0 for key in ("failed", "refused", "unknown"))
        unit = "boolean"
    elif criterion == "package-headroom":
        destination = HERE / "completion-package"
        result = command([sys.executable, "scripts/portable_promise_machine.py", "package", "--out", str(destination)], criterion)
        if result.returncode:
            raise SystemExit("package generation refused; no design report written")
        manifest = json.loads((destination / ".agents/skills/promise-machine/runtime/MANIFEST.json").read_bytes())
        complete_bytes = sum(path.stat().st_size for path in destination.rglob("*") if path.is_file())
        value, unit = 26214400 - complete_bytes, "bytes"
        (HERE / "completion-package-measurement.json").write_text(json.dumps({
            "runtime_payload_bytes": manifest["total_bytes"],
            "complete_package_bytes": complete_bytes,
            "cap_bytes": 26214400,
            "complete_package_headroom": value,
        }, indent=2, sort_keys=True) + "\n")
    else:
        result = command(["gh", "api", "repos/wildcat-finance/skills/branches/main/protection"], criterion, 60)
        if result.returncode:
            raise SystemExit("required-check protection unavailable; no design report written")
        protection = json.loads(result.stdout)
        status = protection.get("required_status_checks") or {}
        checks = status.get("checks") or []
        value = status.get("strict") is True and protection.get("enforce_admins", {}).get("enabled") is True and {"context": "invariants", "app_id": 15368} in checks
        unit = "boolean"
    report = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
              "criterion": criterion, "value": value, "unit": unit,
              "command": f"python3 {SELF} --candidate {args.candidate} --criterion {criterion}", "exit": 0}
    destination = HERE / "reports" / f"{args.candidate}-{criterion}.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_bytes(json.dumps(report, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
