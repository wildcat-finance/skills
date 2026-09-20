#!/usr/bin/env python3
"""Conformance resolver for the issue-871 transition gate.

usage: conform_gate.py --candidate ID --criterion ID --out PATH

Runs the one focused product test module bound to the criterion, from the
current directory, with the repository's Python and no shell. It writes one
`protasis-design-report/v1` report with value true only when the module ran at
least one test and exited zero. A missing module, a red run, a timeout or an
oversized child stream writes nothing and exits 1, so a failure is repaired and
the resolver rerun instead of a false value being pinned at a path that may
never be overwritten. It reads no controller state, and it writes only the new
`--out` file, which must not exist and may not name a controller file.
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
TIMEOUT = 1800
OUTPUT_MAX = 8 * 1024 * 1024
RAN = re.compile(rb"^Ran (\d+) tests? in ", re.M)
CANDIDATES = (
    "dispatcher-grant-wal",
    "per-handler-gate",
    "external-writer-broker",
    "gate-with-replacement-exit",
)
MODULES = {
    "product-refuses-622-specimens": "plugins.hexaemeron.tests.test_transition_gate_wiring",
    "product-appends-loop-two": "plugins.hexaemeron.tests.test_audit_loop_continuation",
    "product-every-mutator-mapped": "plugins.hexaemeron.tests.test_transition_gate_discovery",
}


def checked_out(path_text: str) -> Path:
    path = Path(path_text)
    if path.suffix != ".json" or path.name in CONTROLLER_FILES:
        raise SystemExit("--out must name a new .json report, not a controller file")
    if path.exists() or path.is_symlink():
        raise SystemExit("--out must not already exist")
    if not path.parent.is_dir():
        raise SystemExit("--out parent directory does not exist")
    return path


def module_green(root: Path, module: str) -> bool:
    try:
        done = subprocess.run(
            [sys.executable, "-m", "unittest", module],
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
    parser.add_argument("--criterion", required=True, choices=sorted(MODULES))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = checked_out(args.out)
    if not module_green(Path.cwd(), MODULES[args.criterion]):
        print(f"conform_gate: {MODULES[args.criterion]} is not green; no report written",
              file=sys.stderr)
        return 1
    report = {
        "schema": SCHEMA,
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": True,
        "unit": "boolean",
        "command": (f"python3 .hexaemeron/design/conform_gate.py --candidate "
                    f"{args.candidate} --criterion {args.criterion} --out {args.out}"),
        "exit": 0,
    }
    data = (json.dumps(report, sort_keys=True) + "\n").encode("ascii")
    with open(out, "xb") as handle:
        handle.write(data)
    print(f"{out} {hashlib.sha256(data).hexdigest()} value=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
