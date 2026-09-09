#!/usr/bin/env python3
"""Measure the built payload's headroom under the skills CLI extract cap.

This is the step:3 conformance resolver for the issue #1467 design record.  It
builds the package the repository actually generates at the commit it is run
from and reports the bytes left under 25 MiB.  Unlike the selection resolver it
models nothing: the value is the manifest's own `total_bytes` subtracted from
the cap, so it can only pass once the chosen omission has landed.

Prints one `protasis-design-report/v1` object.  With `--out` it also writes
those exact bytes to the named path and to nothing else.  It writes no
controller state and reads nothing under `.hexaemeron/`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(
    p for p in HERE.parents if (p / "scripts" / "portable_promise_machine.py").is_file()
)
GENERATOR = ROOT / "scripts" / "portable_promise_machine.py"
# The report's `command` names the path this file occupies, relative to the
# repository root, so a report written from the committed location does not
# claim the controller copy under `.hexaemeron/` ran. The same source placed
# at `.hexaemeron/` yields the exact string the 35 receipted reports carry.
SELF = Path(__file__).resolve().relative_to(ROOT).as_posix()
EXTRACT_CAP = 25 * 1024 * 1024

CANDIDATES = (
    "omission-class",
    "omission-class-with-reference-repair",
    "second-package",
    "route-restriction",
    "warning-gate",
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="fiat-1467-conformance.") as raw:
        out = Path(raw) / "package"
        result = subprocess.run(  # phylax: allow subprocess: fixed local generator argv
            [sys.executable, str(GENERATOR), "package", "--out", str(out)],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout + result.stderr)
            return 1
        manifest = json.loads(
            (out / ".agents/skills/promise-machine/runtime/MANIFEST.json")
            .read_text(encoding="utf-8")
        )

    report = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": "built-payload-margin",
        "value": max(0, EXTRACT_CAP - manifest["total_bytes"]),
        "unit": "bytes",
        "command": (
            f"python3 {SELF} "
            f"--candidate {args.candidate}"
        ),
        "exit": 0,
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    sys.stdout.write(encoded)
    if args.out:
        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
