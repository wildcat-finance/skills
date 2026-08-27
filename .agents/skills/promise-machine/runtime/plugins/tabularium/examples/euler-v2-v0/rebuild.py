#!/usr/bin/env python3
"""Rebuild and verify the Euler V2 v0 release in a temporary directory."""

from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


RELEASE = Path(__file__).resolve().parent
PLUGIN_ROOT = RELEASE.parents[1]
COMMAND = PLUGIN_ROOT / "scripts" / "tabularium.py"
RELEASE_ID = "euler-v2-owner-activity-1786933919-v0"


def run(*arguments):
    subprocess.run([sys.executable, str(COMMAND), *map(str, arguments)], check=True)


def main():
    with tempfile.TemporaryDirectory(prefix="tabularium-euler-v2-v0-") as directory:
        rebuilt = Path(directory)
        for name in ("source.json", "capture.json"):
            shutil.copyfile(RELEASE / name, rebuilt / name)
        run(
            "build", "--adapter", "euler-v2",
            "--source", rebuilt / "source.json",
            "--capture-manifest", rebuilt / "capture.json",
            "--out", rebuilt / "events.jsonl",
            "--manifest", rebuilt / "coverage.json",
            "--release", RELEASE_ID,
        )
        for name in ("source.json", "capture.json", "events.jsonl", "coverage.json"):
            (rebuilt / name).chmod(0o444)
        run("verify", rebuilt / "coverage.json")
        for name in ("events.jsonl", "coverage.json"):
            if (rebuilt / name).read_bytes() != (RELEASE / name).read_bytes():
                raise SystemExit("rebuilt %s differs from the committed release" % name)
        print("rebuild matches %s: %s" % (RELEASE_ID, sha256((rebuilt / "events.jsonl").read_bytes()).hexdigest()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
