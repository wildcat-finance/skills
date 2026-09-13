#!/usr/bin/env python3
"""Execute due native specimens; refuse every pending criterion."""

import argparse
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
import worker_exec


CANDIDATES = ("whole-worker-sandbox", "optional-tool-mediation")
CRITERIA = (
    "whole-launch-dispatch", "worker-deadline", "worker-output-cap",
    "origin-drift-recovery", "single-cumulative-reconstruction",
    "executed-inoculation-guards", "carryover-lineage-recovery",
    "source-owned-report-compatibility", "gate-parser-no-execution",
    "gate-receipt-replay", "whole-path-demonstration",
)


IMPLEMENTED = frozenset({("whole-worker-sandbox", "worker-deadline"),
                         ("whole-worker-sandbox", "worker-output-cap")})


def require(condition, code):
    if not condition:
        raise worker_exec.Refusal(code)


def execute(criterion, root):
    """Observe real native processes; no assertion supplied by the caller passes."""
    python = str(Path(sys.executable).resolve())
    observations = []

    def run(code, **kwargs):
        capture = worker_exec.run_worker(root, [python, "-I", "-c", code], **kwargs)
        observations.append(capture.record)
        return capture

    if criterion == "worker-deadline":
        child = ("import os,time,pathlib\nos.setsid()\nprint('ready',flush=True)\n"
                 "until=time.monotonic()+6\n"
                 "while time.monotonic()<until and not pathlib.Path('stop').exists(): time.sleep(.02)\n"
                 "pathlib.Path('stopped').write_text('ack')\n")
        code = ("import subprocess,time; "
                f"subprocess.Popen([{python!r},'-I','-c',{child!r}]); time.sleep(30)")
        capture = run(code, deadline_seconds=2)
        try:
            require(capture.record["code"] == "deadline", "deadline-specimen-did-not-time-out")
            require(capture.record["deadline_seconds"] == 2 and capture.record["elapsed_seconds"] < 10,
                    "deadline-return-bound")
            require(capture.record["snapshot"] is None and not capture.record["artifacts"],
                    "timeout-admitted-output")
            require(not capture.record["scratch_reusable"] and
                    capture.record["cleanup"].endswith("-retired"), "uncertain-cleanup-reused")
            require(capture.stdout == b"ready\n", "detached-specimen-not-started")
        finally:
            scratch = Path(capture.record["scratch_root"])
            (scratch / "stop").write_text("stop")
            until = time.monotonic() + 2
            while time.monotonic() < until and not (scratch / "stopped").exists():
                time.sleep(.02)
            require((scratch / "stopped").exists(), "detached-specimen-ack-missing")
    elif criterion == "worker-output-cap":
        cap = worker_exec.DEFAULT_CAP
        for artifact in (False, True):
            for excess in (0, 1):
                if artifact:
                    code = ("import os; open(os.environ['FIAT_OUTPUT_DIR']+'/x','wb').write("
                            f"b'x'*{cap + excess})")
                else:
                    code = f"import os; os.write(1,b'x'*{cap + excess})"
                capture = run(code, outputs=["x"] if artifact else [],
                              deadline_seconds=5, output_cap_bytes=cap)
                record = capture.record
                require(record["stream_bytes"] + record["artifact_bytes"] <= cap and
                        len(capture.stdout) + len(capture.stderr) <= cap, "retained-buffer-excess")
                if excess:
                    require(record["status"] == "refused" and record["code"] == "output-cap"
                            and record["snapshot"] is None, "first-excess-admitted")
                else:
                    require(record["status"] == "captured" and
                            record["stream_bytes"] + record["artifact_bytes"] == cap,
                            "exact-cap-not-captured")
    else:
        raise worker_exec.Refusal("executor-unimplemented")
    inventory = json.loads((Path(__file__).parent / "fixtures/issue508/criteria.json").read_text())
    names = next(item["specimens"] for item in inventory["criteria"] if item["id"] == criterion)
    expected = {
        "worker-deadline": ["two-second-deadline", "ten-second-return-bound",
                            "timeout-admission-refused", "uncertain-cleanup-no-reuse"],
        "worker-output-cap": ["one-mib-stream", "first-stream-excess", "one-mib-artifact",
                              "first-artifact-excess", "bounded-retained-buffer"],
    }
    require(names == expected[criterion], "specimen-inventory-drift")
    return {"criterion": criterion, "specimens": names, "captures": observations}


def main(argv=None):
    """Publish a boolean only after the complete due native specimen set."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=CRITERIA)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    if (args.candidate, args.criterion) in IMPLEMENTED:
        try:
            with tempfile.TemporaryDirectory(prefix="fiat-native-conformance-") as temp:
                evidence = execute(args.criterion, Path(temp).resolve())
            report = Path(args.report)
            command = shlex.join(["python3", "plugins/hexaemeron/tests/prove_issue_508.py",
                                  "--candidate", args.candidate, "--criterion", args.criterion,
                                  "--report", args.report])
            payload = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
                       "criterion": args.criterion, "value": True, "unit": "boolean",
                       "command": command, "exit": 0}
            report.parent.mkdir(parents=True, exist_ok=True)
            report.with_suffix(".observations.json").write_text(json.dumps(evidence, indent=2) + "\n")
            report.write_text(json.dumps(payload, indent=2) + "\n")
            return 0
        except (worker_exec.Refusal, OSError, ValueError) as exc:
            print(json.dumps({"schema": "issue508-conformance-refusal/v1",
                              "code": str(exc), "criterion": args.criterion}))
            return 1
    print(json.dumps({
        "schema": "issue508-conformance-refusal/v1",
        "event": "issue508_conformance_refused",
        "code": "executor-unimplemented",
        "promise": "protasis-runbook-readiness",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "consequence": 2,
        "blocked_transition": "criterion-acceptance",
        "recovery": "Implement and execute the complete declared specimen set, then rerun.",
    }, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
