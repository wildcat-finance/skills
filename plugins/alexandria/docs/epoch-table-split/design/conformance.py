#!/usr/bin/env python3
"""Resolve one conformance cell of the issue 1888 design record.

Run from the root of the run worktree, after the step that owns the cell:

    python3 .hexaemeron/design/conformance.py <criterion> --candidate split-attribution-parts

Three cells name exact test identifiers that Steps 2 and 3 create or re-derive.
Loading is half the check: an identifier that does not resolve, a run that
executes fewer tests than it names, a skip, a failure or an error each refuse,
so a cell cannot pass before the code its tests exercise exists.

The fourth cell rebuilds every pinned interval demonstration, including both
Wildcat estates from the staging trees `ALEXANDRIA_WILDCAT_V1_STAGING` and
`ALEXANDRIA_WILDCAT_V2_STAGING` name, and verifies the two committed releases.
Each identifier is compared with the constant below, never with a file a step
could edit.

Only the selected candidate carries cases; any other refuses by name. On
success the script writes one `protasis-design-report/v1` object to
`.hexaemeron/design/reports/conformance/<candidate>-<criterion>.json`, unless
`--no-report` asks for the observation alone. An existing report is compared
byte for byte and never replaced. Nothing read
from a report is parsed or executed, and no controller state is read.
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest

CANDIDATE = "split-attribution-parts"
FAILED = "unittest.loader._FailedTest"
PARTS = "tests.test_log_attribution_parts"
LIMITS = "tests.test_release_limits"
CASES = {
    "split-parts-rederive-and-refuse": (
        f"{PARTS}.AttributionPartBuildTests.test_a_split_plan_writes_one_part_per_journal_range",
        f"{PARTS}.AttributionPartBuildTests.test_a_plan_without_the_field_builds_todays_bytes",
        f"{PARTS}.AttributionPartCheckTests.test_check_rederives_every_part_from_its_own_shards",
        f"{PARTS}.AttributionPartCheckTests.test_a_missing_part_refuses_by_name",
        f"{PARTS}.AttributionPartCheckTests.test_an_extra_part_refuses_by_name",
        f"{PARTS}.AttributionPartCheckTests.test_reordered_parts_refuse_by_name",
        f"{PARTS}.AttributionPartCheckTests.test_an_altered_part_refuses_by_name",
    ),
    "release-limits-hold-at-the-cap": (
        f"{LIMITS}.ReleaseCapTests.test_the_component_cap_admits_its_value_and_refuses_one_more",
        f"{LIMITS}.ReleaseCapTests.test_the_capture_cap_admits_its_value_and_refuses_one_more",
        f"{LIMITS}.ManifestLimitTests.test_every_manifest_reader_admits_the_limits_and_refuses_above",
        f"{LIMITS}.CheckpointLimitTests.test_a_checkpoint_for_the_largest_admitted_plan_round_trips",
        "tests.test_usdc_interval.JournalSplitTests"
        ".test_a_split_beyond_the_release_component_limit_refuses_before_any_request",
    ),
    "split-release-over-128-components": (
        f"{LIMITS}.SplitReleaseTests.test_a_release_over_128_components_builds_checks_and_verifies_offline",
    ),
}
PINNED_DEMOS = {
    "usdc-interval-v0": {
        "sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa",
    },
    "usdc-interval-epochs-v0": {
        "sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036",
        "sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
        "sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
    },
    "usdc-interval-live-v0": {
        "sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
    },
    "wildcat-estates-interval-v0": {
        "sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69",
        "sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3",
        "sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
    },
}
PINNED_RELEASES = {
    "compound-v3-phase0-v0":
        "sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab",
    "proof-backed-state-v0":
        "sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f",
}
STAGING = ("ALEXANDRIA_WILDCAT_V1_STAGING", "ALEXANDRIA_WILDCAT_V2_STAGING")
IDENTIFIER = re.compile(r"sha256:[0-9a-f]{64}")
PINNED_CELL = "pinned-release-identities-reproduce"


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def execute(criterion: str) -> tuple[bool, dict]:
    names = list(CASES[criterion])
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(names)
    missing = sorted({case.id() for case in flatten(suite) if case.id().startswith(FAILED)})
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    observed = {
        "criterion": criterion, "required": len(names), "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
        "loader_errors": len(loader.errors), "unresolved": missing,
    }
    passed = (not missing and not loader.errors and result.testsRun == len(names)
              and result.wasSuccessful() and not result.skipped
              and not result.expectedFailures)
    if not passed:
        observed["detail"] = stream.getvalue()[-4000:]
    return passed, observed


def run(argv: list[str], environment: dict) -> tuple[int, str]:
    result = subprocess.run(  # phylax: allow subprocess: fixed interpreter and repository demo argv
        argv, capture_output=True, timeout=3600, env=environment, cwd=str(Path.cwd()),
    )
    return result.returncode, result.stdout.decode("utf-8", "replace") + result.stderr.decode(
        "utf-8", "replace")


def reproduce() -> tuple[bool, dict]:
    for variable in STAGING:
        if not os.environ.get(variable):
            return False, {"refused": f"{variable} is not set; it names an unpacked staging tree"}
    environment = {key: os.environ[key] for key in ("PATH", "HOME", *STAGING) if key in os.environ}
    environment.update(PYTHONDONTWRITEBYTECODE="1", NO_COLOR="1")
    observed = {"demos": {}, "releases": {}}
    passed = True
    with tempfile.TemporaryDirectory(prefix="fiat-1888-pinned-") as name:
        for demo, expected in PINNED_DEMOS.items():
            script = f"plugins/alexandria/examples/{demo}/demo.py"
            output = str(Path(name) / demo)
            built, built_text = run([sys.executable, script, "build", "--output", output], environment)
            checked, checked_text = run([sys.executable, script, "verify", output], environment)
            found = set(IDENTIFIER.findall(built_text)) & expected
            ok = built == 0 and checked == 0 and found == expected
            observed["demos"][demo] = {"build": built, "verify": checked,
                                       "identifiers": sorted(found)}
            passed = passed and ok
    for example, expected in PINNED_RELEASES.items():
        code, text = run([sys.executable, "plugins/alexandria/scripts/alexandria.py", "verify",
                          f"plugins/alexandria/examples/{example}/release"], environment)
        ok = code == 0 and text.strip() == expected
        observed["releases"][example] = {"exit": code, "identifier": text.strip()[:80]}
        passed = passed and ok
    return passed, observed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("criterion", choices=sorted([*CASES, PINNED_CELL]))
    parser.add_argument("--candidate", default=CANDIDATE)
    parser.add_argument("--no-report", action="store_true",
                        help="print the observation and write no report")
    args = parser.parse_args(argv)
    if args.candidate != CANDIDATE:
        parser.error("only the selected candidate " + CANDIDATE
                     + " carries conformance cases; refusing " + args.candidate)
    repository = Path.cwd()
    package = repository / "plugins/alexandria"
    if not package.is_dir():
        parser.error("run this from the repository root; plugins/alexandria is absent")
    if args.criterion == PINNED_CELL:
        passed, observed = reproduce()
    else:
        sys.path.insert(0, str(package))
        passed, observed = execute(args.criterion)
    print(json.dumps({"passed": passed, **observed}, sort_keys=True))
    if not passed:
        return 1
    if args.no_report:
        return 0
    directory = repository / ".hexaemeron/design/reports/conformance"
    for part in (repository / ".hexaemeron", repository / ".hexaemeron/design",
                 directory.parent, directory):
        if part.is_symlink():
            parser.error(f"{part} must not be a symlink")
    directory.mkdir(parents=True, exist_ok=True)
    report = {"candidate": CANDIDATE, "command": (
        "python3 .hexaemeron/design/conformance.py " + args.criterion + " --candidate "
        + CANDIDATE), "criterion": args.criterion, "exit": 0,
        "schema": "protasis-design-report/v1", "unit": "boolean", "value": True}
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path = directory / f"{CANDIDATE}-{args.criterion}.json"
    if os.path.lexists(path):
        if (path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode)
                or path.read_bytes() != data):
            parser.error("an existing conformance report differs from fresh evidence")
    else:
        with open(path, "xb") as handle:
            handle.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
