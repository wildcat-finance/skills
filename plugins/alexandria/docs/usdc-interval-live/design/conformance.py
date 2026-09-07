#!/usr/bin/env python3
"""Resolve one pending conformance criterion of the alexandria-1 design record.

Each criterion names the tests that earn it. This script runs exactly those,
writes one closed `protasis-design-report/v1` object to
`<record directory>/reports/conformance/<candidate>-<criterion>.json`, and
exits zero only when the named tests passed, so a criterion whose step has not
landed leaves a failing report and a non-zero exit rather than nothing.

The same bytes live at `.hexaemeron/design/conformance.py` and under the
committed record directory; both resolve the repository root by walking up to
the checkout that holds the Alexandria suite. Nothing here opens a socket: the
tests run under the suite's own socket denial, and the endpoint variable is
removed from the child's environment before they start.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
RECORD_DIR = HERE.parent
REPORTS = RECORD_DIR / "reports" / "conformance"
CANDIDATE = "opening-reads-in-collect"
SCHEMA = "protasis-design-report/v1"
SUITE = Path("plugins") / "alexandria" / "tests" / "run_tests.py"
ENDPOINT_ENV = "ALEXANDRIA_COMPOUND_RPC_URL"
TIMEOUT_SECONDS = 1_800

# criterion id -> the unittest targets, run from `plugins/alexandria`, that earn it.
# A target that does not exist yet fails to import, which is the right answer
# until the step that writes it has landed.
CRITERIA = {
    "finality-rebinds-after-tag-advance": (
        "tests.test_usdc_interval.FinalityRebindTests",
    ),
    "opening-reads-resumable": (
        "tests.test_usdc_interval.OpeningPhaseResumeTests",
    ),
    "scope-binds-both-hashes": (
        "tests.test_usdc_interval.ScopeBindingTests",
    ),
    "code-hash-rechecked-from-component": (
        "tests.test_usdc_interval.CodeHashRecheckTests",
    ),
    "live-interval-reconciled": (
        "tests.test_usdc_interval_live_demo.LiveIntervalReconciledTests",
    ),
    "demo-reproduces-live-release-id": (
        "tests.test_usdc_interval_live_demo.DemoReproducesReleaseIdTests",
    ),
}


def repository_root() -> Path:
    for candidate in (HERE, *HERE.parents):
        if (candidate / SUITE).is_file():
            return candidate
    raise SystemExit(f"conformance: no checkout holding {SUITE} above {HERE}")


def canonical(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def run(criterion: str) -> int:
    targets = CRITERIA.get(criterion)
    if targets is None:
        print(
            "conformance: unknown criterion; one of " + ", ".join(sorted(CRITERIA)),
            file=sys.stderr,
        )
        return 2
    root = repository_root()
    argv = [sys.executable, "-m", "unittest", *targets]
    environment = {key: value for key, value in os.environ.items() if key != ENDPOINT_ENV}
    try:
        completed = subprocess.run(
            argv, cwd=root / "plugins" / "alexandria", env=environment,
            timeout=TIMEOUT_SECONDS, check=False,
        )
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    value = exit_code == 0
    report = canonical({
        "candidate": CANDIDATE,
        "command": "python3 -m unittest " + " ".join(targets),
        "criterion": criterion,
        "exit": exit_code,
        "schema": SCHEMA,
        "unit": "boolean",
        "value": value,
    })
    REPORTS.mkdir(parents=True, exist_ok=True)
    target = REPORTS / f"{CANDIDATE}-{criterion}.json"
    if target.is_symlink():
        raise SystemExit(f"conformance: {target} must not be a symlink")
    target.write_text(report, encoding="utf-8")
    print(f"{criterion}: {'pass' if value else 'fail'} (exit {exit_code}) -> {target}")
    return 0 if value else 1


def main(argv=None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("usage: conformance.py <criterion>", file=sys.stderr)
        return 2
    return run(arguments[0])


if __name__ == "__main__":
    raise SystemExit(main())
