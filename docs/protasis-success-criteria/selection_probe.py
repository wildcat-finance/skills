#!/usr/bin/env python3
"""Run bounded design specimens; this is not the product controller."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


CANDIDATES = ("controller-capture", "producer-report", "terminal-replay")
CRITERIA = (
    "unexecuted-result-refused", "descriptor-mismatch-refused",
    "settlement-invocations", "sample-record-bytes",
    "legacy-no-backfill", "failed-result-unmet",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def specimens(candidate):
    """Observe three policy models over the same command and descriptor."""
    descriptor = {
        "criterion": "sample", "step": 2,
        "command": [sys.executable, "specimen.py", "0"],
        "study": "a" * 64, "runbook": "b" * 64,
        "source": "c" * 40,
    }
    owned = []
    launches = []
    with tempfile.TemporaryDirectory(prefix="selection-", dir=Path(__file__).parent / "probe-tmp") as scratch:
        place = Path(scratch)
        child = place / "specimen.py"
        child.write_text("import sys\nfrom pathlib import Path\nPath('executed').write_text('yes')\nraise SystemExit(int(sys.argv[1]))\n")

        def execute(exit_code=0):
            values = [sys.executable, str(child), str(exit_code)]
            result = subprocess.run(values, cwd=place, capture_output=True, timeout=5, env={"PATH": "/usr/bin:/bin"})
            launches.append(result.returncode)
            record = {
                "descriptor_sha256": fingerprint(descriptor),
                "operation_ran": True, "exit": result.returncode,
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
                "source": descriptor["source"], "step": descriptor["step"],
            }
            owned.append(canonical(record))
            assert (place / "executed").read_text() == "yes"
            return record

        def accept(record, expected=descriptor):
            if record is None:
                return False
            if candidate != "producer-report" and canonical(record) not in owned:
                return False
            return (
                record.get("descriptor_sha256") == fingerprint(expected)
                and record.get("operation_ran") is True
                and type(record.get("exit")) is int
                and record["exit"] == 0
            )

        forged = {
            "descriptor_sha256": fingerprint(descriptor),
            "operation_ran": True, "exit": 0,
            "stdout_sha256": hashlib.sha256(b"").hexdigest(),
            "stderr_sha256": hashlib.sha256(b"").hexdigest(),
            "source": descriptor["source"], "step": descriptor["step"],
        }
        unexecuted_refused = not accept(forged)
        assert not (place / "executed").exists()
        failed = execute(7)
        failed_unmet = not accept(failed)
        success = execute(0)
        assert accept(success)
        assert not accept(None)
        different = dict(descriptor, step=3)
        mismatched_refused = not accept(success, different)
        recorded_size = max(len(canonical(item)) for item in (failed, success))
        starts_before_legacy = len(launches)
        legacy_state = {"contracts": {}, "receipts": {}}
        legacy_bytes = canonical(legacy_state)
        # Every candidate keeps the explicit unmarked route without a new row.
        if legacy_state["contracts"].get("success_criteria"):
            execute()
        legacy_unchanged = canonical(legacy_state) == legacy_bytes and len(launches) == starts_before_legacy
        starts = len(launches)
        # One build check, then two inspections of the proposed terminal state.
        latest = execute(0)
        for _ in range(2):
            if candidate == "terminal-replay":
                latest = execute(0)
            assert accept(latest)
        settling_starts = len(launches) - starts
        # A deliberately empty successful command still meets this boundary.
        vacuous = subprocess.run([sys.executable, "-c", "pass"], cwd=place, capture_output=True, timeout=5, env={"PATH": "/usr/bin:/bin"})
        assert vacuous.returncode == 0
    return {
        "unexecuted-result-refused": (unexecuted_refused, "boolean"),
        "descriptor-mismatch-refused": (mismatched_refused, "boolean"),
        "settlement-invocations": (settling_starts, "count"),
        "sample-record-bytes": (recorded_size, "bytes"),
        "legacy-no-backfill": (legacy_unchanged, "boolean"),
        "failed-result-unmet": (failed_unmet, "boolean"),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=CANDIDATES, required=True)
    parser.add_argument("--criterion", choices=CRITERIA, required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    supplied = Path(args.report)
    if supplied.is_absolute() or ".." in supplied.parts or not supplied.parts or supplied.parts[0] != "reports":
        parser.error("report must be a new path under reports")
    destination = root / supplied
    destination.parent.mkdir(parents=True, exist_ok=True)
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        parser.error("report path is linked")
    (root / "probe-tmp").mkdir(exist_ok=True)
    # Fetch the named observation only after all the policy specimens ran.
    value, unit = specimens(args.candidate)[args.criterion]
    command = "python3 selection_probe.py --candidate " + args.candidate + " --criterion " + args.criterion + " --report " + args.report
    report = {
        "schema": "protasis-design-report/v1", "candidate": args.candidate,
        "criterion": args.criterion, "value": value, "unit": unit,
        "command": command, "exit": 0,
    }
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
