#!/usr/bin/env python3
"""Rebuild and verify the Goldfinch v0 example without touching its files."""

from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


RELEASE = Path(__file__).resolve().parent
PLUGIN_ROOT = RELEASE.parents[1]
COMMAND = PLUGIN_ROOT / "scripts" / "tabularium.py"


def run(*arguments):
    subprocess.run(
        [sys.executable, str(COMMAND), *map(str, arguments)],
        check=True,
    )


def main():
    with tempfile.TemporaryDirectory(prefix="tabularium-goldfinch-v0-") as directory:
        rebuilt = Path(directory)
        source = rebuilt / "source.json"
        capture = rebuilt / "capture.json"
        events = rebuilt / "events.jsonl"
        coverage = rebuilt / "coverage.json"
        shutil.copyfile(RELEASE / "source.json", source)
        shutil.copyfile(RELEASE / "capture.json", capture)

        run(
            "build",
            "--source", source,
            "--capture-manifest", capture,
            "--out", events,
            "--manifest", coverage,
            "--release", "goldfinch-borrower-record-v0",
        )
        for path in (source, capture, events, coverage):
            path.chmod(0o444)
        run("verify", coverage)

        for name in ("events.jsonl", "coverage.json"):
            expected = (RELEASE / name).read_bytes()
            actual = (rebuilt / name).read_bytes()
            if actual != expected:
                raise SystemExit("rebuilt %s differs from the committed release" % name)

        print(
            "rebuild matches goldfinch-borrower-record-v0: %s"
            % sha256(events.read_bytes()).hexdigest()
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
