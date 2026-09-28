#!/usr/bin/env python3
"""Assemble the #1963 X-Ray outputs and execution records into docs/kickoff/1963.

    python3 docs/kickoff/1963/evidence/producers/assemble_bundle.py --xray XRAY_DIR

XRAY_DIR holds the five X-Ray outputs and evidence/commands.json with the
X-Ray commands' logs. The script copies the outputs, appends a generated
index of every scoped action id to entry-points.md, copies each nonempty
command log or output file to evidence/, noting a renamed output in its
record's observation, and writes execution.json from the recorded argv,
exit and status of every command, including superseded attempts and this
run's own producer commands. Local path prefixes are shown as <scratch> and
<skills>. It edits no record it did not generate and never runs a command.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[5]
BUNDLE = ROOT / "docs/kickoff/1963"
sys.path.insert(0, str(ROOT / "scripts"))
import kickoff_xray_1963_bundle as v1  # noqa: E402

REPORTS = ("x-ray.md", "entry-points.md", "invariants.md", "architecture.json", "architecture.svg")
# Command outputs that are files rather than logs: the git analysis writes JSON, the final render a PNG.
OUTPUTS = {"xray-git-analysis": "git-security-analysis.json",
           "xray-svg-render-review-fix-3": "xray-svg-render-review-fix-3.png"}
PREFIXES = (("/private/tmp/claude-501/-Users-c0rtexzer0-Projects-wildcat-skills/9e45ca8f-9cd5-40a0-9eaa-7bbcd823fbe5/scratchpad",
             "<scratch>"), ("/Users/c0rtexzer0/.codex/worktrees/f1ac/Wildcat Skills", "<skills>"))


def plain(value):
    """Replace this machine's scratch and checkout prefixes in recorded text."""
    if isinstance(value, list):
        return [plain(item) for item in value]
    if isinstance(value, str):
        for prefix, label in PREFIXES:
            value = value.replace(prefix, label)
    return value
# This run's own producer commands; each log is retained verbatim beside the bundle.
OWN = (
    ("derive", "derive the callable denominator and ABI event catalogue from the four accepted inputs",
     ["python3", "scripts/kickoff_xray_1963.py", "derive", "--inputs", ".hexaemeron/research/accepted-corpus",
      "--out", "docs/kickoff/1963/denominator-inputs.json"], "evidence/derive.log"),
    ("build-sources", "bind each input file's digest, size and lines to the public Git objects",
     ["python3", "docs/kickoff/1963/evidence/producers/build_sources.py", "--corpus",
      ".hexaemeron/research/accepted-corpus", "--protocol", "<wildcat-protocol clone>", "--out",
      "docs/kickoff/1963/sources.json"], "evidence/build-sources.log"),
    ("build-linkage", "build actions.json and linkage.json from anchored public source locations",
     ["python3", "docs/kickoff/1963/evidence/producers/build_linkage.py", "--protocol", "<wildcat-protocol clone>",
      "--denominator", "docs/kickoff/1963/denominator-inputs.json", "--out", "<scratch>"],
     "evidence/build-linkage.log"),
)


def action_index(linkage: dict) -> str:
    lines = ["", "## Action index", "",
             "Generated from `linkage.json` by `evidence/producers/assemble_bundle.py`. One row per scoped "
             "state-changing or creation action; the 148 read paths are listed in `actions.json`.", "",
             "| Action id | Disposition | Events |", "| --- | --- | --- |"]
    for row in sorted(linkage["actions"], key=lambda item: item["id"]):
        lines.append(f"| `{row['id']}` | {row['disposition']} | {len(row['events'])} |")
    return "\n".join(lines) + "\n"


def logged_exit(log: Path) -> int:
    last = log.read_text().rstrip("\n").splitlines()[-1]
    if not last.startswith("exit "):
        raise SystemExit(f"{log} does not end with its exit line")
    return int(last.split()[1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xray", type=Path, required=True)
    arguments = parser.parse_args()
    source = arguments.xray
    for name in REPORTS:
        shutil.copyfile(source / name, BUNDLE / name)
    linkage = json.loads((BUNDLE / "linkage.json").read_bytes())
    with (BUNDLE / "entry-points.md").open("a", encoding="utf-8") as stream:
        stream.write(action_index(linkage))
    commands = json.loads((source / "evidence/commands.json").read_bytes())
    records = []
    for identifier, purpose, argv, log in OWN:
        code = logged_exit(BUNDLE / log)
        records.append({"id": identifier, "purpose": purpose, "argv": argv, "exit": code,
                        "status": "passed" if code == 0 else "failed", "log": log,
                        "observation": (BUNDLE / log).read_text().splitlines()[0][:400]})
    for row in commands:
        identifier = row["id"]
        origin = source / "evidence" / (OUTPUTS.get(identifier) or Path(row["log"]).name)
        target = None
        if origin.stat().st_size:
            target = f"evidence/{identifier}{origin.suffix}"
            data = origin.read_bytes()
            if origin.suffix in (".log", ".json"):
                data = plain(data.decode("utf-8")).encode("utf-8")
            (BUNDLE / target).write_bytes(data)
        observation = plain(row["observation"])
        if target and origin.name != Path(target).name and identifier in OUTPUTS:
            observation += f" Retained in the bundle as {target}."
        records.append({"id": identifier, "purpose": plain(row["purpose"]), "argv": plain(row["argv"]),
                        "exit": row["exit"], "status": row["status"], "log": target,
                        "observation": observation})
    for record in records:
        if record["log"] is not None:
            data = (BUNDLE / record["log"]).read_bytes()
            record["log"] = {"path": record["log"], "sha256": v1.digest(data)}
    (BUNDLE / "execution.json").write_bytes(v1.encode({"schema": "issue-1963-execution/v1", "records": records}))
    print(json.dumps({"records": len(records), "failed": [r["id"] for r in records if r["status"] != "passed"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
