"""Source-bound Step selection, observed counters and sanctions proof dispatch."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shlex
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def fixed_module(name: str):
    """Load a declared local source, refusing links and cached foreign modules."""
    source = HERE / (name + ".py")
    if source.is_symlink() or not source.is_file():
        raise ValueError("declared source unavailable")
    existing = sys.modules.get(name)
    if existing is not None:
        if Path(existing.__file__).resolve() != source:
            raise ValueError("declared source differs")
        return existing
    specification = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        del sys.modules[name]
        raise
    return module


_common = fixed_module("wildcat_v3_reports")
EvidenceUnavailable = _common.EvidenceUnavailable
ObservedResult = _common.ObservedResult
REPORT_CAP = _common.REPORT_CAP
report_parts = _common.report_parts
result_payload = _common.result_payload
result_status = _common.result_status
write_report = _common.write_report

CANDIDATES = ("unique-key", "first-match", "adjacent-only")
CRITERIA = ("semantic-conformance", "release-compatibility", "retained-coverage")
PENDING_PAIRS = frozenset((candidate, criterion)
                          for candidate in CANDIDATES for criterion in CRITERIA)
PROOF_REPORTER = "plugins/tabularium/tests/prove_wildcat_sanctions.py"
OBSERVATIONS_SCHEMA = "wildcat-sanctions-conformance-observations/v1"
STEP_CASES = {1: (("test_wildcat_sanctions_scaffold", "SanctionsScaffoldTests"),),
              2: (("test_wildcat_sanctions_semantics", "SanctionsSemanticTests"),
                  ("test_wildcat_sanctions_releases", "SanctionsReleaseTests"))}
CONFORMANCE = {}


def run_cases(cases):
    """Run only declared local unittest classes, with a nonempty bounded suite."""
    import unittest
    suite = unittest.TestSuite()
    for module_name, class_name in cases:
        module = fixed_module(module_name)
        case = getattr(module, class_name, None)
        if not isinstance(case, type) or not issubclass(case, unittest.TestCase):
            raise EvidenceUnavailable("declared test class unavailable")
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(case))
    if not 0 < suite.countTestCases() <= 1000:
        raise EvidenceUnavailable("focused test count outside bounds")
    result = ObservedResult()
    suite.run(result)
    return result


def retained_classification(*, verified, present, joined, unmatched, ambiguous):
    """Classify verified observations; presence requires every target to join."""
    if type(verified) is not bool or not verified:
        raise EvidenceUnavailable("retained custody unavailable")
    for value in (present, joined, unmatched, ambiguous):
        if type(value) is not int or value < 0:
            raise EvidenceUnavailable("retained counters invalid")
    if joined + unmatched + ambiguous != present:
        raise EvidenceUnavailable("retained target accounting differs")
    if not present:
        return "absent"
    if unmatched or ambiguous:
        raise EvidenceUnavailable("present retained target unexercised")
    return "exercised"


def require_fresh(raw):
    """Refuse occupied leaves before execution or sidecar publication."""
    path = Path(*report_parts(raw, Path.cwd()))
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise EvidenceUnavailable("report leaf already exists")


def focused_resolver(cases):
    """Build a proof resolver from observed focused tests."""
    def resolve():
        result = run_cases(cases)
        status = result_status(result)
        if status == 2:
            raise EvidenceUnavailable("conformance execution inconclusive")
        return status == 0, {"result": result_payload(result),
                             "executed_ids": result.executed_ids}
    return resolve


CONFORMANCE.update({
    ("unique-key", "semantic-conformance"): focused_resolver((STEP_CASES[2][0],)),
    ("unique-key", "release-compatibility"): focused_resolver((STEP_CASES[2][1],)),
})


def execute_proof(parser, argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(arguments)
    try:
        report_parts(args.report, Path.cwd())
        sidecar = str(Path(args.report).with_suffix(".observations.json"))
        require_fresh(args.report)
        require_fresh(sidecar)
        pair = (args.candidate, args.criterion)
        resolver = CONFORMANCE.get(pair)
        if pair not in PENDING_PAIRS or resolver is None:
            raise EvidenceUnavailable("criterion implementation absent")
        value, observations = resolver()
        if type(value) is not bool:
            raise EvidenceUnavailable("resolver returned no boolean")
        payload = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
                   "criterion": args.criterion, "value": value, "unit": "boolean",
                   "command": shlex.join(["python3", PROOF_REPORTER, *arguments]),
                   "exit": 0 if value else 1}
        if observations is not None:
            write_report(sidecar, {"schema": OBSERVATIONS_SCHEMA,
                                   "candidate": args.candidate, "criterion": args.criterion,
                                   "observations": observations})
        write_report(args.report, payload)
    except Exception as exc:
        reason = type(exc).__name__
        if isinstance(exc, EvidenceUnavailable):
            reason += ": " + str(exc)
        parser.exit(2, "conformance unavailable: " + reason + "\n")
    print(json.dumps({"exit": payload["exit"], "value": payload["value"]}), file=sys.stderr)
    return payload["exit"]


def execute_report(parser, argv=None):
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report_parts(args.report, Path.cwd())
        require_fresh(args.report)
        cases = STEP_CASES.get(args.step)
        if not cases:
            raise EvidenceUnavailable("Step has no declared focused classes")
        result = run_cases(cases)
        payload = result_payload(result)
        status = result_status(result)
        write_report(args.report, payload)
    except Exception as exc:
        parser.exit(2, "focused report unavailable: " + type(exc).__name__ + "\n")
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    return status
