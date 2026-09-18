#!/usr/bin/env python3
"""Resolve one pending conformance criterion of the fiat-1053 design record.

Usage: python3 .hexaemeron/design/conformance.py <criterion> --candidate <id>

Writes one closed `protasis-design-report/v1` object to
`.hexaemeron/reports/conformance/<candidate>-<criterion>.json` with the value
actually observed, and exits zero only when the observation could be made.
The value, not the exit code, carries the verdict: a false value is an honest
failing report that the design checker refuses at the criterion's stop point.

An existing report is never overwritten. A receipted report is evidence; a
rerun that wants a fresh observation must remove the old file on purpose.
Only the selected candidate can be resolved; the other three candidates were
removed at design lock and no step of theirs will be built.

Every observation is read-only. The dispatched-run check reads GitHub through
`gh api` and never dispatches anything itself; the dispatch is the runbook
step's own action.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # phylax: allow subprocess: fixed argv, no shell, read-only git and gh calls
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD_DIR = HERE.parent
ROOT = RECORD_DIR.parent
REPORTS = RECORD_DIR / "reports" / "conformance"
SCHEMA = "protasis-design-report/v1"
SELECTED = "source-dispatch"
BASE = "9182d0adcb7e9a5330c259d9dc1e044b511711c2"
SOURCE_REPO = "wildcat-finance/skills"
DESTINATION_REPO = "wildcat-finance/skills-runtime"
SOURCE_WORKFLOW = ".github/workflows/dispatch-skills-runtime-rebuild.yml"
DESTINATION_WORKFLOW = ".github/workflows/sync.yml"
SECRET = "RUNTIME_DISPATCH_TOKEN"
CLAIM_FILES = (
    "scripts/portable_promise_machine.py",
    "docs/skills-runtime-publication.md",
    "INSTALL.md",
    "README.md",
)
STALE_CLAIMS = (re.compile(r"hourly"), re.compile(r"an hour behind"),
                re.compile(r"up to an hour"))
DISPATCH_WINDOW = timedelta(minutes=15)


def run(argv: list[str]) -> str:
    completed = subprocess.run(argv, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(argv)} exited {completed.returncode}: {completed.stderr.strip()}")
    return completed.stdout


def gh_json(path: str):
    return json.loads(run(["gh", "api", path]))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def absent_secret_fails_loudly() -> tuple[bool, dict]:
    text = (ROOT / SOURCE_WORKFLOW).read_text("utf-8")
    checks = {
        "permissions-empty": "permissions: {}" in text,
        "guarded-to-source-repository": f"if: github.repository == '{SOURCE_REPO}'" in text,
        "refuses-empty-token": bool(re.search(r'if \[ -z "\$\{GH_TOKEN\}" \]', text))
        and "::error::" in text and "exit 1" in text,
        "names-the-secret": f"secrets.{SECRET}" in text,
        "no-checkout": "actions/checkout" not in text,
        "dispatches-sync-yml": "actions/workflows/sync.yml/dispatches" in text,
        "no-github-token": "github.token" not in text and "secrets.GITHUB_TOKEN" not in text,
    }
    return all(checks.values()), checks


def readme_claims_match_trigger() -> tuple[bool, dict]:
    hits: dict[str, list[str]] = {}
    for relative in CLAIM_FILES:
        text = (ROOT / relative).read_text("utf-8")
        found = [pattern.pattern for pattern in STALE_CLAIMS if pattern.search(text)]
        if found:
            hits[relative] = found
    return not hits, {"stale-claims": hits}


def destination_workflow_untouched() -> tuple[bool, dict]:
    changed = run(["git", "-C", str(ROOT), "diff", "--name-only", f"{BASE}..HEAD", "--", "distribution/"]).split()
    canonical = hashlib.sha256((ROOT / "distribution/skills-runtime/sync.yml").read_bytes()).hexdigest()
    return not changed, {"changed-under-distribution": changed, "canonical-sha256": canonical}


def dispatched_run_succeeds() -> tuple[bool, dict]:
    """A destination run started by workflow_dispatch after the recorded marker succeeded.

    The marker is written by the runbook step at the moment the operator runs
    the exact dispatch command the source workflow carries, with the token
    they created. This resolver never dispatches; it reads the marker and
    GitHub's run list, and records the destination README's source commit
    beside the current source `main` so currency is visible in the
    observation without being the gate.
    """
    marker = json.loads((HERE / "dispatch-marker.json").read_text("utf-8"))
    dispatched_at = parse_time(marker["dispatched_at"])
    destination_runs = gh_json(
        f"repos/{DESTINATION_REPO}/actions/runs?event=workflow_dispatch&per_page=10"
    )["workflow_runs"]
    match = next((
        r for r in destination_runs
        if r["path"] == DESTINATION_WORKFLOW
        and r["conclusion"] == "success"
        and dispatched_at <= parse_time(r["created_at"]) <= dispatched_at + DISPATCH_WINDOW
    ), None)
    readme = run(["gh", "api", f"repos/{DESTINATION_REPO}/contents/README.md", "--jq", ".content"])
    import base64
    readme_text = base64.b64decode(readme).decode("utf-8", "replace")
    found = re.search(r"generated from commit `([0-9a-f]{40})`", readme_text)
    main_sha = gh_json(f"repos/{SOURCE_REPO}/commits/main")["sha"]
    observation = {
        "marker": marker,
        "destination-run": None if match is None else {
            "id": match["id"], "created_at": match["created_at"],
            "updated_at": match["updated_at"], "head_sha": match["head_sha"]},
        "published-source-commit": None if found is None else found.group(1),
        "source-main": main_sha,
        "published-matches-main": found is not None and found.group(1) == main_sha,
    }
    return match is not None, observation


CASES = {
    "absent-secret-fails-loudly": absent_secret_fails_loudly,
    "readme-claims-match-trigger": readme_claims_match_trigger,
    "destination-workflow-untouched": destination_workflow_untouched,
    "dispatched-run-succeeds": dispatched_run_succeeds,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("criterion", choices=sorted(CASES))
    parser.add_argument("--candidate", default=SELECTED)
    args = parser.parse_args(argv)
    if args.candidate != SELECTED:
        print(f"refused: {args.candidate} was removed at design lock; only {SELECTED} is built",
              file=sys.stderr)
        return 2
    target = REPORTS / f"{args.candidate}-{args.criterion}.json"
    if target.exists():
        print(f"refused: {target} exists; remove it on purpose before observing again",
              file=sys.stderr)
        return 2
    try:
        value, observation = CASES[args.criterion]()
    except (OSError, RuntimeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"observation could not be made: {exc}", file=sys.stderr)
        return 1
    command = f"python3 .hexaemeron/design/conformance.py {args.criterion} --candidate {args.candidate}"
    body = json.dumps({
        "candidate": args.candidate,
        "command": command,
        "criterion": args.criterion,
        "exit": 0,
        "schema": SCHEMA,
        "unit": "boolean",
        "value": value,
    }, indent=2, sort_keys=True) + "\n"
    REPORTS.mkdir(parents=True, exist_ok=True)
    target.write_text(body, "utf-8")
    target.with_suffix(".observation.json").write_text(
        json.dumps(observation, indent=2, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({"criterion": args.criterion, "value": value,
                      "report": str(target.relative_to(RECORD_DIR)),
                      "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                      "observation": observation}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
