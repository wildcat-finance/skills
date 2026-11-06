"""Run the named Alexandria assertions before emitting a conformance report.

The four conformance criteria of the wrapper-subject design record are
resolved here and nowhere else. Each names the exact test identifiers that
establish it, in `plugins/alexandria/tests/test_wildcat_wrappers.py`, the
module the runbook's steps create and extend. An identifier that does not
resolve, a run that executes fewer assertions than it names, a skip, a
failure or an error each refuse, so no criterion reports before the code its
identifiers exercise exists.

Only the selected candidate carries cases. A resolver naming another
candidate refuses by name: the design checker consults later transitions for
the selected candidate alone, and a report for a rejected model would assert
something nobody intends to build.

Run from the target root. Nothing read from a report on disk is parsed,
dispatched on or executed. An existing report is only compared byte for byte
with fresh evidence and never replaced. The script reads no controller state
and writes nothing outside `.hexaemeron/design/reports/conformance/`.
"""

import argparse
import io
import json
from pathlib import Path
import stat
import sys
import unittest

CANDIDATE = "declared-wrapper-subjects"
FAILED = "unittest.loader._FailedTest"
MODULE = "tests.test_wildcat_wrappers."

CASES = {
    "legacy-identities-hold": (
        MODULE + "LegacyIdentityTests.test_constructed_v2_release_identifier_is_frozen",
        MODULE + "LegacyIdentityTests.test_constructed_v1_release_identifier_is_frozen",
        MODULE + "LegacyIdentityTests.test_registry_digest_constants_are_unchanged",
    ),
    "wrapper-release-builds-and-checks": (
        MODULE + "WrapperReleaseTests.test_wrapper_release_builds_and_checks",
        MODULE + "WrapperReleaseTests.test_check_lists_each_wrapper_with_epoch_and_journal",
        MODULE + "WrapperReleaseTests.test_check_rederives_the_wrapper_subjects_component",
    ),
    "wrapper-refusals-fire": (
        MODULE + "WrapperRefusalTests.test_unknown_market_refuses",
        MODULE + "WrapperRefusalTests.test_wrapper_without_code_refuses",
        MODULE + "WrapperRefusalTests.test_wrapper_log_outside_its_epoch_refuses",
        MODULE + "WrapperRefusalTests.test_declared_wrapper_without_deployment_refuses",
    ),
    "portable-payload-within-budget": (
        MODULE + "PortableBudgetTests.test_run_adds_at_most_five_payload_files_and_100000_bytes",
    ),
}


def flatten(suite):
    """Yield each test case a suite holds, however deeply it is nested."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def unresolved(suite):
    """Name what the loader turned into a failure stub, read before the run."""
    return sorted({case.id() for case in flatten(suite) if case.id().startswith(FAILED)})


def reason(observed):
    """One phrase saying why a criterion refused, for triage from the output."""
    if observed["unresolved"] or observed["loader_errors"]:
        return "assertions-unresolved"
    if observed["tests_run"] == 0:
        return "no-assertions-executed"
    if observed["tests_run"] != observed["required"]:
        return "assertion-count-mismatch"
    if observed["errors"]:
        return "assertions-errored"
    if observed["failures"]:
        return "assertions-failed"
    if observed["skipped"]:
        return "assertions-skipped"
    if observed["expected_failures"]:
        return "assertions-expected-to-fail"
    return "unaccounted-refusal"


def execute(criterion, loader=None):
    """Execute fixed test identifiers; missing, skipped or empty runs cannot pass."""
    names = list(CASES[criterion])
    loader = loader or unittest.TestLoader()
    suite = loader.loadTestsFromNames(names)
    missing = unresolved(suite)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    observed = {
        "criterion": criterion, "tests_run": result.testsRun, "required": len(names),
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "expected_failures": len(result.expectedFailures),
        "loader_errors": len(loader.errors), "unresolved": missing,
    }
    passed = (
        not observed["loader_errors"] and not missing and result.testsRun == len(names)
        and result.testsRun > 0 and result.wasSuccessful() and not result.skipped
        and not result.expectedFailures
    )
    observed["reason"] = None if passed else reason(observed)
    return passed, observed, stream.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("criterion", choices=CASES)
    parser.add_argument("--candidate", default=CANDIDATE)
    args = parser.parse_args(argv)
    if args.candidate != CANDIDATE:
        parser.error(
            "only the selected candidate " + CANDIDATE
            + " carries conformance cases; refusing " + args.candidate
        )
    repo = Path.cwd()
    package = repo / "plugins" / "alexandria"
    found = package.is_dir()
    if found:
        sys.path.insert(0, str(package))
    passed, observed, detail = execute(args.criterion)
    print(json.dumps({"passed": passed, "package_found": found, **observed}, sort_keys=True))
    if not passed:
        print(detail, file=sys.stderr)
        return 1
    report_dir = repo / ".hexaemeron" / "design" / "reports" / "conformance"
    for path in (repo / ".hexaemeron", report_dir.parent.parent, report_dir.parent, report_dir):
        if path.is_symlink():
            parser.error("conformance report directory must not be a symlink")
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "candidate": CANDIDATE, "command": (
            "python3 .hexaemeron/design/conformance.py " + args.criterion
            + " --candidate " + CANDIDATE
        ),
        "criterion": args.criterion, "exit": 0, "schema": "protasis-design-report/v1",
        "unit": "boolean", "value": True,
    }
    path = report_dir / (CANDIDATE + "-" + args.criterion + ".json")
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not stat.S_ISREG(path.lstat().st_mode) or path.read_bytes() != data:
            parser.error("existing conformance report is unsafe or differs from fresh evidence")
    else:
        with path.open("xb") as handle:
            handle.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
