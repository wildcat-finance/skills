#!/usr/bin/env python3
"""Conformance resolver for the issue-1480 carry guard.

usage: conform_carry.py --candidate ID --out PATH

Runs the focused product regression module for the carry guard,
`plugins.hexaemeron.tests.test_carried_step_commits`, with the repository's
Python and no shell, and writes one `protasis-design-report/v1` report whose
boolean value is true only when the module ran at least one test and exited
zero. It executes nothing else, reads no controller state, and writes only the
new `--out` file. A missing module, a red run, a timeout or an oversized child
stream all record `false`; they are a scheduled refusal at the transition this
cell blocks, not a guess.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "protasis-design-report/v1"
CONTROLLER_FILES = frozenset({"state.json", "ledger.jsonl", "lock"})
MODULE = "plugins.hexaemeron.tests.test_carried_step_commits"
TIMEOUT = 1800
OUTPUT_MAX = 8 * 1024 * 1024
RAN = re.compile(rb"^Ran (\d+) tests? in ", re.M)
CANDIDATES = (
    "gained-range-ownership",
    "owned-commit-ancestry",
    "pull-request-merge-state",
    "merge-time-only",
)


def checked_out(path_text: str) -> Path:
    path = Path(path_text)
    if path.suffix != ".json" or path.name in CONTROLLER_FILES:
        raise SystemExit("--out must name a new .json report, not a controller file")
    if path.exists() or path.is_symlink():
        raise SystemExit("--out must not already exist")
    if not path.parent.is_dir():
        raise SystemExit("--out parent directory does not exist")
    return path


def module_green(root: Path) -> bool:
    try:
        done = subprocess.run(
            [sys.executable, "-m", "unittest", MODULE],
            cwd=root,
            env={
                "PATH": os.defpath,
                "LANG": "C",
                "LC_ALL": "C",
                "HOME": os.environ.get("HOME", str(root)),
                "NO_COLOR": "1",
            },
            capture_output=True,
            timeout=TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    stream = done.stdout + done.stderr
    if len(stream) > OUTPUT_MAX or done.returncode != 0:
        return False
    match = RAN.search(stream)
    return match is not None and int(match.group(1)) > 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = checked_out(args.out)
    root = Path.cwd()
    value = module_green(root)
    report = {
        "schema": SCHEMA,
        "candidate": args.candidate,
        "criterion": "product-refuses-specimen-stack",
        "value": value,
        "unit": "boolean",
        "command": f"python3 {sys.argv[0]} --candidate {args.candidate} --out {args.out}",
        "exit": 0,
    }
    data = (json.dumps(report, sort_keys=True) + "\n").encode("ascii")
    with open(out, "xb") as handle:
        handle.write(data)
    print(f"{out} {hashlib.sha256(data).hexdigest()} value={value!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
