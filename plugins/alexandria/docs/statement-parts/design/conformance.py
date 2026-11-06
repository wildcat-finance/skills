#!/usr/bin/env python3
"""Resolve one conformance cell of the issue 1892 design record.

Run from the root of the run worktree, after the step that owns the cell:

    python3 .hexaemeron/design/conformance.py <criterion> --candidate statement-parts

Three cells name exact test identifiers that Steps 2 and 3 create. Loading is
half the check: an identifier that does not resolve, a run that executes fewer
tests than it names, a skip, a failure or an error each refuse, so a cell
cannot pass before the code its tests exercise exists.

The fourth cell, due at integration, emits the statement of every pinned
release with the tree's own `alexandria.py statement` and compares each
statement's SHA-256 with the digest the base commit wrote. The four
demonstrations build into a temporary directory, the test fixture is ingested
there, the two committed releases are read in place, and the two preserved
Wildcat releases are read from `ALEXANDRIA_WILDCAT_V1_RELEASE` and
`ALEXANDRIA_WILDCAT_V2_RELEASE`. No Wildcat staging tree is rebuilt. Each
identifier and digest is compared with a constant below, never with a file a
step could edit.

Only the selected candidate carries cases; any other refuses by name. On
success the script writes one `protasis-design-report/v1` object to
`.hexaemeron/design/reports/conformance/<candidate>-<criterion>.json`, unless
`--no-report` asks for the observation alone. An existing report is compared
byte for byte and never replaced. No controller state is read.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

CANDIDATE = "statement-parts"
FAILED = "unittest.loader._FailedTest"
PARTS = "tests.test_statement_parts"
PROJECTION = f"{PARTS}.StatementPartProjectionTests"
COMMAND = f"{PARTS}.StatementPartsCommandTests"
CASES = {
    "part-projection-verifies": (
        f"{PROJECTION}.test_a_release_past_the_limit_projects_into_parts_ariadne_verifies",
        f"{PROJECTION}.test_every_component_and_capture_lands_in_exactly_one_part_in_order",
        f"{PROJECTION}.test_each_part_stays_within_the_part_limit_and_key_budget",
        f"{PROJECTION}.test_the_index_binds_every_part_by_digest",
        f"{PROJECTION}.test_a_release_within_both_bounds_keeps_one_statement",
    ),
    "past-limit-refuses-by-name": (
        f"{COMMAND}.test_a_component_past_the_part_limit_refuses_by_name",
        f"{COMMAND}.test_output_refuses_a_release_past_the_single_bounds_naming_parts",
        f"{COMMAND}.test_parts_refuses_a_release_that_fits_one_statement",
    ),
    "killed-emit-leaves-no-set": (
        f"{COMMAND}.test_an_interrupted_write_leaves_no_output_directory",
        f"{COMMAND}.test_an_existing_output_is_refused_unchanged",
        f"{COMMAND}.test_output_inside_or_through_a_symlink_into_the_release_is_refused",
    ),
}
PINNED_CELL = "pinned-statements-keep-bytes"
# Label -> (release identifier, SHA-256 of its base statement), as resolve.py pins them.
PINNED = {
    "fixture": ("sha256:e86550e59baba75258093ed4b67c144d1dd520c68f0411d23ba59af050f3fed6",
                "041c699bdefc8be359c88d738a8c5b45002e044b6226534d52bace7c09796c43"),
    "credit-history-raw": ("sha256:6117658c59c96e9ca32594ffe09e994d478dc7d9f2d3799c64bb25050c7fe0e2",
                           "d4846fd64852e5a8e34615679a252a7729976d1278b3be1ec177e1bc2da92fd2"),
    "credit-history-derived": ("sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec",
                               "3b12aa332fcf45cff14fb9a7d1c5f379852d3858c6cf56dcea57c26fc78523e6"),
    "usdc-interval-v0": ("sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa",
                         "c92e6cbb3b953acc3ad11e456cf5ca4715b5b2e8dbc98872a15e0c7c455716cf"),
    "usdc-interval-live-v0": ("sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
                              "64df112deab0c91fe3da1aef1196a3a9226adee0cebc977468b3a609b4bc921f"),
    "usdc-interval-epochs-synthetic": ("sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036",
                                       "656e225fbd67321230f58ff943a9dea3fc6ac265af8dc88beacbae2ba8b81bdd"),
    "usdc-interval-epochs-live": ("sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
                                  "76334510a1434645e0f249f4015c0c5d0065c17d0eea5f9814a7c9d12cc53527"),
    "compound-v3-phase0": ("sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab",
                           "4ebe969c40dbe77eacbe8848e530454596ecbb8ba9a07b3e6c49b11b41ca7a93"),
    "proof-backed-state": ("sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f",
                           "faaff30f38025379781f35a7289af80cb0e15c9c0ff9c3efd0b9c09f1c77efa5"),
    "wildcat-v1": ("sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69",
                   "679277a2a3367d16a4cb462a12c805c6580291bbaaf7c3a6aa5b4d4e177c00ca"),
    "wildcat-v2": ("sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3",
                   "c891c9d510da6cf02136b082766792d520823beb98b79781c4f8cbcbaec7feae"),
}
DEMOS = {
    "credit-history-v0": {"raw-release": "credit-history-raw",
                          "derived-release": "credit-history-derived"},
    "usdc-interval-v0": {"release": "usdc-interval-v0"},
    "usdc-interval-live-v0": {"release": "usdc-interval-live-v0"},
    "usdc-interval-epochs-v0": {"synthetic-release": "usdc-interval-epochs-synthetic",
                                "live-release": "usdc-interval-epochs-live"},
}
WILDCAT = {"wildcat-v1": "ALEXANDRIA_WILDCAT_V1_RELEASE",
           "wildcat-v2": "ALEXANDRIA_WILDCAT_V2_RELEASE"}


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


def child_environment() -> dict:
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1"}


def run(argv: list[str]) -> tuple[int, str]:
    result = subprocess.run(  # phylax: allow subprocess: fixed interpreter and repository argv
        argv, capture_output=True, timeout=3600, env=child_environment(), cwd=str(Path.cwd()),
    )
    return result.returncode, result.stdout.decode("utf-8", "replace")


def pinned_releases(scratch: Path) -> tuple[dict, dict]:
    package = Path.cwd() / "plugins/alexandria"
    releases, failures = {}, {}
    for demo, outputs in DEMOS.items():
        output = scratch / demo
        code, _ = run([sys.executable, str(package / "examples" / demo / "demo.py"), "build",
                       "--output", str(output)])
        if code != 0:
            failures[demo] = f"build exited {code}"
            continue
        for directory, label in outputs.items():
            releases[label] = output / directory
    inputs = scratch / "fixture-inputs"
    shutil.copytree(package / "tests" / "fixtures", inputs)
    code, _ = run([sys.executable, str(package / "scripts/alexandria.py"), "ingest",
                   "--plan", str(inputs / "capture-plan.json"),
                   "--output", str(scratch / "fixture-release")])
    if code != 0:
        failures["fixture"] = f"ingest exited {code}"
    releases["fixture"] = scratch / "fixture-release"
    releases["compound-v3-phase0"] = package / "examples/compound-v3-phase0-v0/release"
    releases["proof-backed-state"] = package / "examples/proof-backed-state-v0/release"
    for label, variable in WILDCAT.items():
        if not os.environ.get(variable):
            failures[label] = f"{variable} is not set; it names the preserved release"
        else:
            releases[label] = Path(os.environ[variable])
    return releases, failures


def reproduce() -> tuple[bool, dict]:
    command = Path.cwd() / "plugins/alexandria/scripts/alexandria.py"
    observed: dict = {"statements": {}}
    with tempfile.TemporaryDirectory(prefix="fiat-1892-pinned-") as name:
        scratch = Path(name).resolve()
        releases, failures = pinned_releases(scratch)
        observed["failures"] = failures
        passed = not failures
        for label, (release_id, digest) in sorted(PINNED.items()):
            if label not in releases:
                passed = False
                continue
            output = scratch / f"{label}.statement.json"
            code, text = run([sys.executable, str(command), "statement", str(releases[label]),
                              "--output", str(output)])
            try:
                receipt = json.loads(text)
            except ValueError:
                receipt = {}
            found = hashlib.sha256(output.read_bytes()).hexdigest() if output.is_file() else None
            ok = code == 0 and receipt.get("release_id") == release_id and found == digest
            observed["statements"][label] = {"exit": code, "matches": ok}
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
