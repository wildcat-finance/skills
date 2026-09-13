#!/usr/bin/env python3
"""Resolve one pending conformance criterion of the alexandria-1 design record.

Each criterion names the tests that earn it. This script runs exactly those,
writes one closed `protasis-design-report/v1` object to
`<record directory>/reports/conformance/<candidate>-<criterion>.json`, and
exits zero only when the named tests passed, so a criterion whose step has not
landed leaves a failing report and a non-zero exit rather than nothing.

The same bytes live at `.hexaemeron/design/conformance.py` and under the
committed record directory; both resolve the repository root by walking up to
the checkout that holds the Alexandria suite.

One criterion, `live-interval-reconciled`, is not earned by tests. It is the
run's single network gate, and this script is the only thing that opens it: it
runs the collector's `collect` against the primary provider and its
`reconcile` against the second transport, times both against the study's
120,000 ms budget and passes only when the reconciliation record says `agreed`.
Each endpoint reaches exactly one child process, through the collector's own
`ALEXANDRIA_COMPOUND_RPC_URL` and nothing else, and no endpoint is written to
the report, the measurement or any other file. Every other criterion runs
tests under the suite's socket denial with both endpoint variables stripped
from the child's environment, so no endpoint reaches a test.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
RECORD_DIR = HERE.parent
REPORTS = RECORD_DIR / "reports" / "conformance"
CANDIDATE = "opening-reads-in-collect"
SCHEMA = "protasis-design-report/v1"
SUITE = Path("plugins") / "alexandria" / "tests" / "run_tests.py"
ENDPOINT_ENV = "ALEXANDRIA_COMPOUND_RPC_URL"
TIMEOUT_SECONDS = 1_800

# The live criterion. `SECOND_ENDPOINT_ENV` is read by this harness only and is
# handed to the reconcile child as ENDPOINT_ENV, so the collector still knows
# exactly one endpoint variable and no second variable exists inside it.
LIVE_CRITERION = "live-interval-reconciled"
SECOND_ENDPOINT_ENV = "ALEXANDRIA_CONFORMANCE_SECOND_RPC_URL"
LIVE_BUDGET_MS = 120_000
LIVE_TIMEOUT_SECONDS = 900
COLLECTOR = Path("plugins") / "alexandria" / "scripts" / "usdc_interval.py"
LIVE_EXAMPLE = Path("plugins") / "alexandria" / "examples" / "usdc-interval-live-v0"
SECOND_PROVIDER_CLASS = "public relay endpoint, archive logs and state, no trace methods"
RECONCILIATION_RECORD = Path("reconciliation") / "reconciliation.json"
LIVE_COMMAND = (
    "python3 plugins/alexandria/scripts/usdc_interval.py collect "
    "--plan plugins/alexandria/examples/usdc-interval-live-v0/plan.json "
    "--staging plugins/alexandria/examples/usdc-interval-live-v0/staging"
    " && python3 plugins/alexandria/scripts/usdc_interval.py reconcile "
    "--plan plugins/alexandria/examples/usdc-interval-live-v0/plan.json "
    "--staging plugins/alexandria/examples/usdc-interval-live-v0/staging "
    f"--provider-class \"{SECOND_PROVIDER_CLASS}\""
)

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


def write_report(criterion: str, command: str, exit_code: int, value: bool) -> Path:
    """Write the one closed report object the design record consumes."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    target = REPORTS / f"{CANDIDATE}-{criterion}.json"
    if target.is_symlink():
        raise SystemExit(f"conformance: {target} must not be a symlink")
    target.write_text(canonical({
        "candidate": CANDIDATE,
        "command": command,
        "criterion": criterion,
        "exit": exit_code,
        "schema": SCHEMA,
        "unit": "boolean",
        "value": value,
    }), encoding="utf-8")
    return target


def _endpoint_environment(name: str) -> dict:
    """The child's environment: one endpoint under the collector's own variable.

    The harness variable never reaches a child, so a collector process can only
    ever see the single endpoint variable its transport documents.
    """
    endpoint = os.environ.get(name, "")
    if not endpoint:
        raise SystemExit(f"conformance: {name} is not set")
    environment = {
        key: value for key, value in os.environ.items()
        if key not in (ENDPOINT_ENV, SECOND_ENDPOINT_ENV)
    }
    environment[ENDPOINT_ENV] = endpoint
    return environment


def _timed(argv, root: Path, endpoint_name: str) -> tuple[int, int]:
    """Run one network command against one endpoint and return its exit and elapsed ms."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            argv, cwd=root, env=_endpoint_environment(endpoint_name),
            timeout=LIVE_TIMEOUT_SECONDS, check=False, stdout=subprocess.DEVNULL,
        )
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    return exit_code, round((time.monotonic() - started) * 1000)


def run_live(criterion: str) -> int:
    """Collect and reconcile the live interval, and time both against the budget.

    The two commands are the run's only network reads. `collect` resumes from
    the staging checkpoint, so a rerun after a refusal re-reads nothing already
    committed. The gate passes only when both commands exit zero, the
    reconciliation record says `agreed` with no dispute, and the two commands
    together stay inside the study's budget.
    """
    root = repository_root()
    plan = root / LIVE_EXAMPLE / "plan.json"
    staging = root / LIVE_EXAMPLE / "staging"
    collector = root / COLLECTOR
    collect_exit, collect_ms = _timed(
        [sys.executable, str(collector), "collect", "--plan", str(plan), "--staging", str(staging)],
        root, ENDPOINT_ENV,
    )
    reconcile_exit, reconcile_ms = -1, 0
    if collect_exit == 0:
        reconcile_exit, reconcile_ms = _timed(
            [
                sys.executable, str(collector), "reconcile", "--plan", str(plan),
                "--staging", str(staging), "--provider-class", SECOND_PROVIDER_CLASS,
            ],
            root, SECOND_ENDPOINT_ENV,
        )
    elapsed_ms = collect_ms + reconcile_ms

    record = {}
    path = staging / RECONCILIATION_RECORD
    if path.is_file() and not path.is_symlink():
        document = json.loads(path.read_text(encoding="utf-8"))
        record = document.get("reconciliation", {}) if isinstance(document, dict) else {}
    status = record.get("status")
    disputed = record.get("disputed") or []
    within_budget = elapsed_ms <= LIVE_BUDGET_MS
    value = (
        collect_exit == 0 and reconcile_exit == 0
        and status == "agreed" and not disputed and within_budget
    )
    exit_code = 0 if value else (reconcile_exit if reconcile_exit else collect_exit) or 1

    measurement = {
        "budget_ms": LIVE_BUDGET_MS,
        "candidate": CANDIDATE,
        "collect_exit": collect_exit,
        "collect_ms": collect_ms,
        "compared": record.get("compared"),
        "criterion": criterion,
        "disputed": list(disputed),
        "elapsed_ms": elapsed_ms,
        "matched": record.get("matched"),
        "provider_class": record.get("provider_class"),
        "reconcile_exit": reconcile_exit,
        "reconcile_ms": reconcile_ms,
        "reconciliation": status,
        "schema": "alexandria-live-interval-measurement/v1",
        "within_budget": within_budget,
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{CANDIDATE}-{criterion}.measurement.json").write_text(
        canonical(measurement), encoding="utf-8"
    )
    target = write_report(criterion, LIVE_COMMAND, exit_code, value)
    print(
        f"{criterion}: {'pass' if value else 'fail'} (exit {exit_code}) -> {target}\n"
        f"  elapsed {elapsed_ms} ms of {LIVE_BUDGET_MS} ms budget; "
        f"reconciliation {status}; compared {record.get('compared')}; "
        f"disputed {len(disputed)}"
    )
    return 0 if value else 1


def run(criterion: str) -> int:
    if criterion == LIVE_CRITERION:
        return run_live(criterion)
    targets = CRITERIA.get(criterion)
    if targets is None:
        print(
            "conformance: unknown criterion; one of "
            + ", ".join(sorted([*CRITERIA, LIVE_CRITERION])),
            file=sys.stderr,
        )
        return 2
    root = repository_root()
    argv = [sys.executable, "-m", "unittest", *targets]
    # Both endpoint variables are stripped, not only the collector's own. The
    # harness variable is set on the same command line as the collector's, so
    # leaving it in place handed every test child the second endpoint under its
    # own name -- an endpoint reaching a test, which `endpoint-leak` refuses.
    environment = {
        key: value for key, value in os.environ.items()
        if key not in (ENDPOINT_ENV, SECOND_ENDPOINT_ENV)
    }
    try:
        completed = subprocess.run(
            argv, cwd=root / "plugins" / "alexandria", env=environment,
            timeout=TIMEOUT_SECONDS, check=False,
        )
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_code = 124
    value = exit_code == 0
    target = write_report(
        criterion, "python3 -m unittest " + " ".join(targets), exit_code, value
    )
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
