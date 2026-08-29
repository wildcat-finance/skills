#!/usr/bin/env python3
"""Run the Janus forge suite and write its JUnit XML report to one path.

The single positional argument is the report path. The launcher runs
``forge test --junit`` with a pinned argv and no shell, from the harness
directory resolved relative to this file, and writes forge's stdout to the
report path only when forge exits 0 and that stdout parses as XML -- a
compile failure or malformed output leaves no report file behind. The
launcher's exit code is forge's exit code.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent.parent / "harness"

FORGE_ARGV = ["forge", "test", "--junit"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report", type=Path, help="path the JUnit XML report is written to")
    args = parser.parse_args(argv)

    completed = subprocess.run(
        FORGE_ARGV,
        cwd=HARNESS_DIR,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.buffer.write(completed.stderr)
        return completed.returncode

    try:
        ET.fromstring(completed.stdout)
    except ET.ParseError as error:
        print(f"forge exited 0 but its stdout is not XML: {error}", file=sys.stderr)
        return 1

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_bytes(completed.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
