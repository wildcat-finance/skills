"""Project one measured research result into a closed Protasis report."""
from pathlib import Path
import argparse
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EXPECTED_OUTPUT = "ipv4-bind-denied\nipv6-bind-denied\nipv4-connect-denied\nipv6-connect-denied\n"

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", choices=("bubblewrap-netns", "bubblewrap-seccomp"), required=True)
parser.add_argument("--criterion", choices=("network-four-operations", "launch-wall-ms", "policy-bytes", "native-verifier-agreement", "bounded-cleanup"), required=True)
parser.add_argument("--report", required=True)
args = parser.parse_args()
pins = json.loads((HERE / "selection-inputs.json").read_bytes())
for row in pins["files"]:
    if hashlib.sha256((REPO / row["path"]).read_bytes()).hexdigest() != row["sha256"]:
        raise SystemExit("selection evidence changed: " + row["path"])
observations = json.loads((HERE / "selection-probe.json").read_bytes())["observations"]
row = next(item for item in observations if item["candidate"] == args.candidate)
values = {
    "network-four-operations": (all(row[key].get("exit") == 0 and row[key].get("stdout") == EXPECTED_OUTPUT for key in ("direct", "descendant")), "boolean"),
    "launch-wall-ms": (math.ceil(row["launch_median_ms"]), "milliseconds"),
    "policy-bytes": (row["policy_bytes"], "bytes"),
    "native-verifier-agreement": (row["interoperability"]["passed"], "boolean"),
    "bounded-cleanup": (row["leader_exit"].get("exit") == 0 and row["leader_exit"]["descendant_lock_released"] and row["timeout"].get("refusal") == "tool-timeout" and row["timeout"]["elapsed_ms"] < 3000 and row["timeout"]["descendant_lock_released"] and row["output_limit"].get("refusal") == "tool-output-limit", "boolean"),
}
for sample in row["launch_samples"]:
    if sample.get("exit") != 0 or sample.get("stdout") != "ready\n":
        raise SystemExit("launch sample failed")
value, unit = values[args.criterion]
command = "python3 .hexaemeron/sources/study/design_report.py --candidate " + args.candidate + " --criterion " + args.criterion + " --report " + args.report
report = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
          "criterion": args.criterion, "value": value, "unit": unit, "command": command, "exit": 0}
destination = REPO / args.report
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, sort_keys=True))
