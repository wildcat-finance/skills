"""Compare declared projections against the issue's native-state constraints."""

import argparse
import json
from pathlib import Path

POLICIES = {
    "native-fields": {"reinterpret_role": False, "invent_market": False,
                      "convert_values": False,
                      "legacy_version": "1.0.0", "new_version": "1.2.0", "fresh": True},
    "contextual-projection": {"reinterpret_role": True, "invent_market": True,
                              "convert_values": True,
                              "legacy_version": "1.0.0", "new_version": "1.2.0", "fresh": True},
}


def project(policy):
    native = {"role": "2", "reserveRatioBipsUpdated": "1000"}
    output = {"decoded": dict(native), "parties": [], "amounts": []}
    searches = 0
    indexes = []
    if policy["invent_market"]:
        indexes.append({"fixture-hooks": {"market": "fixture-market", "role": "lender"}})
        context = indexes[0].get("fixture-hooks")
        searches += 1
        output["parties"].append(context["market"])
    if policy["reinterpret_role"]:
        output["decoded"]["role"] = context["role"]
    if policy["convert_values"]:
        output["decoded"]["reserveRatioBipsUpdated"] = "0.1"
    preserved = output["decoded"] == native and output["parties"] == [] and output["amounts"] == []
    return preserved, searches, len(indexes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=tuple(POLICIES), required=True)
    parser.add_argument("--criterion", choices=("source-bound-fields", "unbounded-lookups", "auxiliary-state", "legacy-replay-plan", "fresh-output"), required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    policy = POLICIES[args.candidate]
    preserved, searches, indexes = project(policy)
    values = {
        "source-bound-fields": preserved,
        "unbounded-lookups": searches,
        "auxiliary-state": indexes,
        "legacy-replay-plan": policy["legacy_version"] == "1.0.0" and policy["new_version"] != "1.0.0",
        "fresh-output": policy["fresh"],
    }
    value = values[args.criterion]
    path = Path(args.report)
    root = Path(__file__).resolve().parents[2]
    absolute = path.absolute()
    if not absolute.is_relative_to(root / ".hexaemeron/design-reports"):
        parser.error("report must stay in the design report directory")
    if path.is_symlink() or path.exists():
        parser.error("report must be fresh")
    report = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
              "criterion": args.criterion, "value": value,
              "unit": "boolean" if type(value) is bool else "count",
              "command": "python3 .hexaemeron/design/selection_probe.py --candidate " + args.candidate + " --criterion " + args.criterion + " --report " + args.report,
              "exit": 0}
    with path.open("x") as handle:
        json.dump(report, handle, sort_keys=True, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
