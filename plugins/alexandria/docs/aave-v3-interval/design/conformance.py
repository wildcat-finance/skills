"""Run the named assertions before emitting a conformance report.

The fifteen conformance criteria of the Aave V3 interval design record are
resolved here and nowhere else.  Each one names the exact test identifiers that
would establish it, in the suite module the runbook step that owns the
criterion creates or extends.  Loading is half the check: an identifier that
does not resolve, a run that executed fewer assertions than it required, a
skip, a failure or an error each refuse, so a criterion cannot be reported
before the code those identifiers name exists.

Only the selected candidate carries cases.  A resolver naming any other
candidate refuses by name, because the design checker consults a later
transition's evidence for the selected candidate alone.

Nothing read from a report on disk is parsed, dispatched on or executed.  The
report path is built from the fixed candidate below and from a criterion the
parser has already restricted to CASES, and an existing report is only ever
compared byte for byte against freshly executed evidence.  The script reads no
controller state and writes nothing outside `.hexaemeron/reports/conformance/`.
"""

import argparse
import io
import json
from pathlib import Path
import stat
import sys
import unittest


CANDIDATE = "segmented-proxy-set-venue"

# The identifier a loader gives a name it could not import or attribute.
FAILED = "unittest.loader._FailedTest"

CASES = {
    "registry-reproduces-recorded-subject-set": (
        "tests.test_aave_v3_registry.AaveRegistryConformanceTests"
        ".test_registry_reproduces_the_recorded_subject_set_digest",
        "tests.test_aave_v3_registry.AaveRegistryConformanceTests"
        ".test_listed_contracts_match_the_merged_row",
    ),
    "registry-pin-change-refuses": (
        "tests.test_aave_v3_registry.AaveRegistryConformanceTests"
        ".test_changed_registry_pin_refuses_by_name",
        "tests.test_aave_v3_registry.AaveRegistryConformanceTests"
        ".test_changed_source_row_refuses_by_name",
    ),
    "per-subject-proxy-epochs-derived": (
        "tests.test_aave_v3_venue.AaveEpochConformanceTests"
        ".test_proxy_epochs_follow_upgrade_positions",
        "tests.test_aave_v3_venue.AaveEpochConformanceTests"
        ".test_pre_interval_subject_opens_at_interval_start",
        "tests.test_aave_v3_venue.AaveEpochConformanceTests"
        ".test_proxy_created_in_interval_opens_at_its_creation_block",
    ),
    "unsupported-upgrade-shapes-refuse": (
        "tests.test_aave_v3_venue.AaveUpgradeRefusalTests"
        ".test_upgrade_in_opening_block_refuses",
        "tests.test_aave_v3_venue.AaveUpgradeRefusalTests"
        ".test_two_upgrades_of_one_subject_in_one_block_refuse",
        "tests.test_aave_v3_venue.AaveUpgradeRefusalTests"
        ".test_slot_disagreeing_with_announcement_refuses",
        "tests.test_aave_v3_venue.AaveUpgradeRefusalTests"
        ".test_unrecorded_implementation_refuses",
    ),
    "other-venues-keep-upgrade-transaction-refusal": (
        "tests.test_aave_v3_venue.OtherVenueCompatibilityTests"
        ".test_compound_still_refuses_an_ordinary_log_in_its_upgrade_transaction",
        "tests.test_aave_v3_venue.OtherVenueCompatibilityTests"
        ".test_wildcat_venues_still_read_no_upgrade_topic",
    ),
    "wrong-chain-or-market-refuses": (
        "tests.test_aave_v3_collector.AaveScopeRefusalTests"
        ".test_wrong_chain_refuses",
        "tests.test_aave_v3_collector.AaveScopeRefusalTests"
        ".test_wrong_market_refuses",
    ),
    "collection-refusal-battery": (
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_foreign_emitter_refuses",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_incomplete_page_refuses",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_missing_journal_refuses",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_corrupt_journal_refuses",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_provider_failure_records_a_receipt",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_provider_disagreement_is_disputed",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_interrupted_resume_is_byte_identical",
        "tests.test_aave_v3_collector.AaveCollectionRefusalTests"
        ".test_changed_boundary_hash_refuses",
    ),
    "transaction-index-only-disagreement-declared": (
        "tests.test_aave_v3_collector.TransactionIndexSpecimenTests"
        ".test_index_only_difference_still_records_agreed",
        "tests.test_aave_v3_collector.TransactionIndexSpecimenTests"
        ".test_release_declares_the_positional_verification_limit",
        "tests.test_aave_v3_collector.TransactionIndexSpecimenTests"
        ".test_check_refuses_a_release_without_the_limit",
    ),
    "credential-absent-from-artefacts": (
        "tests.test_aave_v3_collector.AaveCredentialTests"
        ".test_bearer_credential_absent_from_every_artefact",
        "tests.test_aave_v3_collector.AaveCredentialTests"
        ".test_transport_error_text_names_no_endpoint",
    ),
    "segment-plans-tile-the-interval": (
        "tests.test_aave_v3_segments.SegmentTableTests"
        ".test_segments_tile_the_ruled_interval",
        "tests.test_aave_v3_segments.SegmentTableTests"
        ".test_every_segment_plan_validates_and_is_pinned",
    ),
    "segment-budget-within-ceilings": (
        "tests.test_aave_v3_segments.SegmentBudgetTests"
        ".test_every_segment_estimate_fits_its_component_ceiling",
        "tests.test_aave_v3_segments.SegmentBudgetTests"
        ".test_every_fixture_component_and_journal_is_under_the_ceiling",
    ),
    "preflight-measurement-recorded": (
        "tests.test_aave_v3_segments.PreflightRecordTests"
        ".test_preflight_record_counts_every_sampled_window",
        "tests.test_aave_v3_segments.PreflightRecordTests"
        ".test_shard_width_and_concurrency_derive_from_the_record",
    ),
    "production-segments-preserved-and-rebuilt": (
        "tests.test_aave_v3_interval_demo.PreservedArtefactsTests"
        ".test_verify_preserved_passes_against_the_committed_artefacts",
        "tests.test_aave_v3_interval_demo.PreservedArtefactsTests"
        ".test_every_segment_rebuild_record_agrees_with_its_pin",
        "tests.test_aave_v3_interval_demo.PreservedArtefactsTests"
        ".test_every_segment_counts_every_shard_and_class",
    ),
    "existing-release-identities-retained": (
        "tests.test_usdc_interval_live_demo.DemoReproducesReleaseIdTests"
        ".test_the_rebuild_reproduces_the_pinned_identifier",
        "tests.test_epoch_positions_demo.LiteralOwnershipTests"
        ".test_the_live_rebuild_has_its_own_recorded_identifier",
        "tests.test_wildcat_v1_interval_demo.PreservedArtefactsTests"
        ".test_verify_preserved_passes_against_the_committed_artefacts",
        "tests.test_wildcat_v2_interval_demo.PreservedArtefactsTests"
        ".test_verify_preserved_passes_against_the_committed_artefacts",
    ),
    "aave-fixture-rebuilds-offline-without-sockets": (
        "tests.test_aave_v3_interval_demo.OfflineDemoTests"
        ".test_build_and_verify_agree_without_a_socket",
        "tests.test_aave_v3_interval_demo.OfflineDemoTests"
        ".test_fixture_release_declares_constructed_staging",
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
