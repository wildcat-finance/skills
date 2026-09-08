"""Run the named production assertions before emitting a conformance report."""

import argparse
import io
import json
from pathlib import Path
import sys
import unittest


CASES = {
    "production-attribution": (
        "test_before_and_after_upgrade",
        "test_upgrade_in_last_block",
        "test_first_block_upgrade_refuses",
        "test_same_transaction_before_upgrade_refuses",
        "test_same_transaction_after_upgrade_refuses",
        "test_multiple_upgrades_refuse",
        "test_malformed_coordinates_refuse",
        "test_contradictory_hash_index_pairs_refuse",
    ),
    "legacy-release-identity": (
        "test_historical_live_release_identity",
        "test_historical_synthetic_release_identity",
        "test_v1_has_no_positional_claim",
    ),
    "offline-rederivation": (
        "test_offline_rederives_attributions",
        "test_rebound_boundary_tampering_refuses",
        "test_rebound_owner_tampering_refuses",
    ),
    "resume-and-refusal": (
        "test_interrupted_collection_preserves_journals",
        "test_unsupported_positions_leave_refusal",
    ),
}


def execute(criterion, loader=None):
    """Execute fixed test IDs; missing, skipped or empty tests cannot pass."""
    names = ["tests.test_epoch_positions.ProductionConformanceTests." + name
             for name in CASES[criterion]]
    loader = loader or unittest.TestLoader()
    suite = loader.loadTestsFromNames(names)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    passed = (not loader.errors and result.testsRun == len(names)
              and result.testsRun > 0 and result.wasSuccessful()
              and not result.skipped and not result.expectedFailures)
    return passed, {"tests_run": result.testsRun, "required": len(names),
                    "failures": len(result.failures), "errors": len(result.errors),
                    "skipped": len(result.skipped),
                    "expected_failures": len(result.expectedFailures)}, stream.getvalue()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("criterion", choices=CASES)
    args = parser.parse_args(argv)
    repo = Path.cwd()
    sys.path.insert(0, str(repo / "plugins/alexandria"))
    passed, observed, detail = execute(args.criterion)
    print(json.dumps({"criterion": args.criterion, "passed": passed, **observed}, sort_keys=True))
    if not passed:
        print(detail, file=sys.stderr)
        return 1
    # Reports are immutable; a successful rerun cannot replace earlier evidence.
    report_dir = repo / ".hexaemeron/reports/conformance"
    if any(path.is_symlink() for path in (repo / ".hexaemeron", report_dir.parent, report_dir)):
        parser.error("conformance report directory must not be a symlink")
    report_dir.mkdir(parents=True, exist_ok=True)
    report = {"schema": "protasis-design-report/v1", "candidate": "position-boundary",
              "criterion": args.criterion, "value": True, "unit": "boolean",
              "command": "python3.14 .hexaemeron/design/conformance.py " + args.criterion,
              "exit": 0}
    path = report_dir / ("position-boundary-" + args.criterion + ".json")
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
