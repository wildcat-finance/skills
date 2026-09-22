"""Run the named production assertions before emitting a conformance report.

The eight conformance criteria of the venue-dispatch design record are resolved
here and nowhere else.  Each one names the exact test identifiers that would
establish it, in the suite module the runbook step that owns the criterion
extends.  Loading is half the check: an identifier that does not resolve, a run
that executed fewer assertions than it required, a skip, a failure or an error
each refuse, so a criterion cannot be reported before the venue code those
identifiers name exists.

Only the selected candidate carries cases.  A resolver naming any other
candidate refuses by name, because the design checker consults a later
transition's evidence for the selected candidate alone and a report written for
a rejected model would assert something nobody intends to build.

Every refusal names the criterion and the counts it observed, because a
refusal with no reason cannot be triaged from a report tree months later.

Nothing read from a report on disk is parsed, dispatched on or executed.  The
report path is built from the fixed candidate below and from a criterion the
parser has already restricted to CASES, and an existing report is only ever
compared byte for byte against freshly executed evidence.
"""

import argparse
import io
import json
from pathlib import Path
import stat
import sys
import unittest


CANDIDATE = "venue-module-registry"

# The identifier a loader gives a name it could not import or attribute.
FAILED = "unittest.loader._FailedTest"

CASES = {
    "compound-path-still-builds": (
        "tests.test_usdc_interval.WildcatConformanceTests"
        ".test_compound_demonstration_builds_and_checks",
        "tests.test_usdc_interval.WildcatConformanceTests"
        ".test_compound_registry_refusals_still_fire",
    ),
    "wildcat-v2-plan-builds-and-checks": (
        "tests.test_wildcat_venue.WildcatV2ConformanceTests"
        ".test_wildcat_v2_plan_builds_a_release",
        "tests.test_wildcat_venue.WildcatV2ConformanceTests"
        ".test_wildcat_v2_release_checks",
    ),
    "wildcat-v1-plan-builds-and-checks": (
        "tests.test_wildcat_venue.WildcatV1ConformanceTests"
        ".test_wildcat_v1_plan_builds_a_release",
        "tests.test_wildcat_venue.WildcatV1ConformanceTests"
        ".test_wildcat_v1_release_checks",
    ),
    "shared-subject-attributed-per-venue": (
        "tests.test_wildcat_venue.SharedSubjectTests"
        ".test_arch_controller_is_a_subject_of_both_venues",
        "tests.test_wildcat_venue.SharedSubjectTests"
        ".test_neither_venue_attributes_the_other_venues_subject",
    ),
    "v1-source-gap-declared": (
        "tests.test_wildcat_venue.WildcatV1ConformanceTests"
        ".test_unreproduced_source_subjects_carry_a_declared_gap",
        "tests.test_wildcat_venue.WildcatV1ConformanceTests"
        ".test_v1_release_claims_no_source_identity_it_cannot_support",
    ),
    "constructed-staging-declared-in-coverage": (
        "tests.test_wildcat_venue.ConstructedStagingTests"
        ".test_constructed_staging_gap_present_for_fixture_deployment",
        "tests.test_wildcat_venue.ConstructedStagingTests"
        ".test_constructed_staging_gap_absent_for_admitted_deployment",
    ),
    "undeclared-venue-refuses": (
        "tests.test_usdc_interval.WildcatConformanceTests"
        ".test_unregistered_venue_refuses_by_name",
        "tests.test_usdc_interval.WildcatConformanceTests"
        ".test_registry_format_disagreement_refuses_by_name",
    ),
    "component-budget-respected": (
        "tests.test_usdc_interval.WildcatConformanceTests"
        ".test_release_components_stay_under_their_ceiling",
        "tests.test_usdc_interval.WildcatConformanceTests"
        ".test_staging_journals_stay_under_their_ceiling",
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
    """Name what the loader turned into a failure stub rather than a test.

    Read this before the suite runs.  A suite frees each test as it executes
    it, leaving `None` behind, so the same walk afterwards reads nothing.
    """
    return sorted({case.id() for case in flatten(suite)
                   if case.id().startswith(FAILED)})


def reason(observed):
    """Say in one phrase why a criterion refused, for triage from the report."""
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
    """Execute fixed test IDs; missing, skipped or empty tests cannot pass."""
    names = list(CASES[criterion])
    loader = loader or unittest.TestLoader()
    suite = loader.loadTestsFromNames(names)
    missing = unresolved(suite)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    observed = {"criterion": criterion, "tests_run": result.testsRun,
                "required": len(names), "failures": len(result.failures),
                "errors": len(result.errors), "skipped": len(result.skipped),
                "expected_failures": len(result.expectedFailures),
                "loader_errors": len(loader.errors),
                "unresolved": missing}
    passed = (not observed["loader_errors"] and not observed["unresolved"]
              and result.testsRun == len(names) and result.testsRun > 0
              and result.wasSuccessful() and not result.skipped
              and not result.expectedFailures)
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
    package = repo / "plugins/alexandria"
    # A working directory that is not the repository root leaves every
    # identifier unresolvable, which refuses on its own.  Report which of the
    # two it was rather than leaving a reader to infer it from a traceback.
    found = package.is_dir()
    if found:
        sys.path.insert(0, str(package))
    passed, observed, detail = execute(args.criterion)
    print(json.dumps({"passed": passed, "package_found": found, **observed},
                     sort_keys=True))
    if not passed:
        print(detail, file=sys.stderr)
        return 1
    # Reports are immutable; a successful rerun cannot replace earlier evidence.
    report_dir = repo / ".hexaemeron/reports/conformance"
    if any(path.is_symlink() for path in (repo / ".hexaemeron", report_dir.parent, report_dir)):
        parser.error("conformance report directory must not be a symlink")
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "protasis-design-report/v1", "candidate": CANDIDATE,
              "criterion": args.criterion, "value": True, "unit": "boolean",
              "command": ("python3 .hexaemeron/design/conformance.py "
                          + args.criterion + " --candidate " + CANDIDATE),
              "exit": 0}
    path = report_dir / (CANDIDATE + "-" + args.criterion + ".json")
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size != len(data):
            parser.error("existing conformance report is unsafe or differs from fresh evidence")
        if path.read_bytes() != data:
            parser.error("existing conformance report differs from fresh evidence")
    else:
        with path.open("xb") as handle:
            handle.write(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
