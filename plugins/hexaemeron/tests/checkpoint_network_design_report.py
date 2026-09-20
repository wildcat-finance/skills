#!/usr/bin/env python3
"""Resolve the selected checkpoint network design from executed, source-bound evidence."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/hexaemeron/skills/fiat/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_authority import conformance as owner, release_conformance
from checkpoint_authority.canonical import Refusal as NetworkRefusal

CANDIDATE = "bubblewrap-seccomp"
CRITERIA = ("product-linux", "hostile-evidence", "hosted-linux", "hosted-macos")
DIRECTORY = (".hexaemeron", "reports", "conformance")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--evidence")
    return parser


def available(root, name):
    """Refuse either occupied leaf before executing; publication rechecks the pair."""
    with owner._directory(root, DIRECTORY, create=True) as (parent, check):
        for member in (name, name[:-5] + ".evidence.json"):
            try:
                os.stat(member, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise owner.Refusal("report-exists")
        check()


def publish(root, name, report, evidence):
    """Create bounded evidence first, report last, with no replacement or link traversal."""
    available(root, name)
    with owner._directory(root, DIRECTORY, create=True) as (parent, check):
        owner._create(parent, name[:-5] + ".evidence.json", owner._json_bytes(evidence))
        check()
        owner._create(parent, name, owner._json_bytes(report))
        check()


def hostile(root, report):
    """Execute the actual network cases; test fixtures alone cannot create this result."""
    import test_checkpoint_network as cases
    import test_checkpoint_network_reports as reports
    from checkpoint_authority_release_suite import Result
    before = release_conformance.inputs(root)
    suite = unittest.defaultTestLoader.loadTestsFromModule(cases)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(reports))
    expected = [test.id() for group in suite for test in group]
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(suite)
    complete = (len(set(expected)) == len(expected) == result.testsRun > 0
                and sorted(result.started) == sorted(expected)
                and result.started == result.completed)
    passed = bool(complete and result.wasSuccessful() and not
                  (result.skipped or result.expectedFailures or result.unexpectedSuccesses))
    if release_conformance.inputs(root) != before:
        raise owner.Refusal("source-changed")
    report.update(value=passed, exit=0 if passed else 1)
    return {"schema": "checkpoint-network-design-execution/v1", "complete": complete,
            "passed": passed, "tests_run": result.testsRun, "subtests_run": result.subtests,
            "started": result.started, "completed": result.completed,
            "failures": len(result.failures), "errors": len(result.errors),
            "skips": len(result.skipped), "expected_failures": len(result.expectedFailures),
            "unexpected_successes": len(result.unexpectedSuccesses),
            "output_sha256": hashlib.sha256(output.getvalue().encode()).hexdigest(),
            **{key: value for key, value in before.items() if key != "cases"},
            "design_report_sha256": hashlib.sha256(owner._json_bytes(report)).hexdigest()}


def main(argv=None, *, root=ROOT):
    args = build_parser().parse_args(argv)
    try:
        if args.candidate != CANDIDATE:
            raise owner.Refusal("unsupported-candidate")
        if args.criterion not in CRITERIA:
            raise owner.Refusal("unknown-criterion")
        if args.criterion.startswith("hosted-"):
            raise owner.Refusal("criterion-not-implemented")
        if args.evidence is not None:
            raise owner.Refusal("unexpected-evidence")
        name = CANDIDATE + "-" + args.criterion + ".json"
        if args.report != "/".join((*DIRECTORY, name)):
            raise owner.Refusal("unsafe-report-path")
        available(root, name)
        command = ("python3 plugins/hexaemeron/tests/checkpoint_network_design_report.py"
                   " --candidate " + CANDIDATE + " --criterion " + args.criterion
                   + " --report " + args.report)
        report = {"schema": "protasis-design-report/v1", "candidate": CANDIDATE,
                  "criterion": args.criterion, "value": False, "unit": "boolean",
                  "command": command, "exit": 1}
        if args.criterion == "product-linux":
            if sys.platform != "linux" or platform.machine() != "x86_64":
                raise owner.Refusal("unsupported-host-profile")
            evidence = release_conformance.run(root, report)
        else:
            evidence = hostile(root, report)
        publish(root, name, report, evidence)
        print(json.dumps({"criterion": args.criterion, "passed": report["value"],
                          "report": args.report, "exit": report["exit"]}, sort_keys=True))
        return report["exit"]
    except (owner.Refusal, NetworkRefusal, OSError) as error:
        code = error.code if isinstance(error, NetworkRefusal) else (
            str(error) if isinstance(error, owner.Refusal) else "unsafe-or-unavailable-file")
        print(json.dumps({"event": "checkpoint_network_design_refused", "code": code,
                          "complete": False, "exit": 2}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
