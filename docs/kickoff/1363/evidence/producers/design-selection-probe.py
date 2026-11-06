"""Measure two preservation choices over the issue's exact source pair."""

import argparse
import hashlib
import io
import json
import math
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path


PINS = {
    "deployed": "f5a26146987926f4811b72a795d662813dedfe85",
    "candidate": "bea503c2736d47de7fd34130c64f10783dc35b39",
}
CRITERIA = {
    "source-identity": "boolean",
    "packaging-time": "milliseconds",
    "preserved-bytes": "bytes",
    "format-compatibility": "boolean",
    "source-recovery": "boolean",
}


def git(root, *args, data=None):
    return subprocess.run(
        ["git", "-C", str(root), *args], input=data,
        capture_output=True, check=True, timeout=30,
    ).stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, choices=("source-bound-reports", "reports-and-source-archive"))
    parser.add_argument("--criterion", required=True, choices=tuple(CRITERIA))
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    report = (root / args.report).resolve()
    assert report.is_relative_to(root / ".hexaemeron")
    rows = []
    originals = {}
    recovered = {}
    for role, commit in PINS.items():
        source = root / ".hexaemeron" / "sources" / role
        assert git(source, "rev-parse", "HEAD").decode().strip() == commit
        entries = git(source, "ls-tree", "-rz", commit, "--", "src").split(b"\0")
        for entry in entries:
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, oid = metadata.split()
            path = raw_path.decode()
            if not path.endswith(".sol"):
                continue
            assert kind == b"blob" and mode in (b"100644", b"100755")
            payload = (source / path).read_bytes()
            native = git(source, "cat-file", "blob", oid.decode())
            assert payload == native
            key = role + "/" + path
            originals[key] = payload
            recovered[key] = native
            rows.append({"role": role, "commit": commit, "path": path,
                         "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    assert len(rows) == 170
    manifest = json.dumps({"schema": "issue-1363-design-source-probe/v1", "sources": rows}, sort_keys=True, indent=2).encode() + b"\n"
    start = time.perf_counter_ns()
    with tempfile.TemporaryDirectory(prefix="packaging-", dir=root / ".hexaemeron") as temporary:
        directory = Path(temporary)
        (directory / "sources.json").write_bytes(manifest)
        if args.candidate == "reports-and-source-archive":
            with tarfile.open(directory / "sources.tar", "w") as archive:
                for key, payload in sorted(originals.items()):
                    info = tarfile.TarInfo(key)
                    info.size = len(payload)
                    info.mtime = 0
                    archive.addfile(info, io.BytesIO(payload))
        elapsed_ms = math.ceil((time.perf_counter_ns() - start) / 1_000_000)
        measured_bytes = sum(path.stat().st_size for path in directory.iterdir())
        loaded = json.loads((directory / "sources.json").read_bytes())
        identity_ok = loaded["sources"] == rows
        compatibility_ok = {path.suffix for path in directory.iterdir()} <= {".json", ".tar"}
        if args.candidate == "reports-and-source-archive":
            with tarfile.open(directory / "sources.tar", "r") as archive:
                recovery_ok = all(archive.extractfile(key).read() == payload for key, payload in originals.items())
        else:
            recovery_ok = recovered == originals
    values = {"source-identity": identity_ok, "packaging-time": elapsed_ms,
              "preserved-bytes": measured_bytes, "format-compatibility": compatibility_ok,
              "source-recovery": recovery_ok}
    result = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
              "criterion": args.criterion, "value": values[args.criterion],
              "unit": CRITERIA[args.criterion],
              "command": shlex.join(["python3", ".hexaemeron/design-selection/probe.py", *sys.argv[1:]]),
              "exit": 0}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"candidate": args.candidate, "criterion": args.criterion, "value": values[args.criterion]}))


if __name__ == "__main__":
    main()
