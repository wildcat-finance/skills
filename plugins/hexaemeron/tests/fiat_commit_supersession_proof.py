#!/usr/bin/env python3
"""Run the #2014 conformance specimens due after each implementation step."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[3]
TEST_MODULE = "plugins.hexaemeron.tests.test_fiat_commit_supersession"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if args.candidate != "append-only-map" or args.criterion not in (
        "uid-admission", "effective-ancestry"
    ):
        parser.error("this source implements only append-only-map/uid-admission and effective-ancestry")
    command = (
        "python3 plugins/hexaemeron/tests/fiat_commit_supersession_proof.py "
        f"--candidate {args.candidate} --criterion {args.criterion} "
        f"--report {args.report}"
    )
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", TEST_MODULE, "-v"],
        cwd=ROOT, capture_output=True, timeout=60,
    )
    if tests.returncode != 0:
        print(f"{args.criterion} specimens failed; report was not written", file=sys.stderr)
        return 1
    report = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": True,
        "unit": "boolean",
        "command": command,
        "exit": 0,
    }
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report, sort_keys=True, separators=(",", ":")), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
