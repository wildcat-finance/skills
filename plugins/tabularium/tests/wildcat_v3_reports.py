"""Bounded report creation and explicit in-process Step test selection."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
STEP_CASES = {
    1: (("test_wildcat_v3_scaffold", "ScaffoldTests"),),
    2: (("test_wildcat_v3_semantics", "SemanticConformanceTests"),
        ("test_wildcat_v3_schema_parity", "SchemaParityTests")),
    3: (("test_wildcat_v3_releases", "ReleaseSpecimenTests"),),
    4: (("test_wildcat_v3_reproduction", "ReleaseReproductionTests"),),
}
REPORT_CAP = 1024 * 1024
TEST_CAP = 1000


class EvidenceUnavailable(ValueError):
    """The declared source or evidence has not been supplied."""


class ObservedResult(unittest.TestResult):
    def __init__(self) -> None:
        super().__init__()
        self.executed_ids: list[str] = []

    def startTest(self, test: unittest.TestCase) -> None:
        self.executed_ids.append(test.id())
        super().startTest(test)


def result_payload(result: unittest.TestResult) -> dict:
    return {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def result_status(result: unittest.TestResult) -> int:
    if result.errors or not result.testsRun:
        return 2
    if (not result.wasSuccessful() or result.skipped
            or result.expectedFailures or result.unexpectedSuccesses):
        return 1
    return 0


def run_cases(cases: tuple[tuple[str, str], ...]) -> ObservedResult:
    suite = unittest.TestSuite()
    for module_name, class_name in cases:
        source = HERE / (module_name + ".py")
        if source.is_symlink() or not source.is_file():
            raise EvidenceUnavailable("focused test source unavailable: " + module_name)
        module = importlib.import_module(module_name)
        if Path(module.__file__).resolve() != source:
            raise EvidenceUnavailable("focused test source differs: " + module_name)
        case = getattr(module, class_name, None)
        if not isinstance(case, type) or not issubclass(case, unittest.TestCase):
            raise EvidenceUnavailable("focused test class unavailable: " + class_name)
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(case))
    count = suite.countTestCases()
    if not 0 < count <= TEST_CAP:
        raise EvidenceUnavailable("focused test count outside declared bounds")
    result = ObservedResult()
    suite.run(result)
    return result


def report_parts(raw: str, root: Path) -> tuple[str, ...]:
    if not isinstance(raw, str) or not raw or len(raw.encode("utf-8")) > 4096:
        raise ValueError("report path outside declared bounds")
    if "\\" in raw or any(ord(char) < 32 for char in raw):
        raise ValueError("report path has unsafe characters")
    path = Path(raw)
    if ".." in path.parts:
        raise ValueError("report path escapes its worktree")
    if path.is_absolute():
        for ancestor in path.parents:
            try:
                same_root = ancestor.samefile(root)
            except OSError:
                same_root = False
            if same_root:
                path = path.relative_to(ancestor)
                break
        else:
            raise ValueError("report path escapes its worktree")
    parts = path.parts
    if (not 2 <= len(parts) <= 12 or parts[0] not in (".elenchus", ".hexaemeron")
            or path.suffix != ".json"):
        raise ValueError("report must be JSON under .elenchus or .hexaemeron")
    return parts


def write_report(raw: str, payload: dict) -> None:
    """Create a fresh bounded JSON report; preserve every existing leaf."""
    encoded = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(encoded) > REPORT_CAP:
        raise ValueError("report exceeds byte cap")
    root = Path.cwd()
    parts = report_parts(raw, root)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent = os.open(root, flags)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, 0o700, dir_fd=parent)
            except FileExistsError:
                pass
            child = os.open(part, flags, dir_fd=parent)
            os.close(parent)
            parent = child
        leaf_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open(parts[-1], leaf_flags, 0o600, dir_fd=parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
    finally:
        os.close(parent)


def execute(parser, argv: list[str] | None = None) -> int:
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report_parts(args.report, Path.cwd())
        result = run_cases(STEP_CASES[args.step])
        payload = result_payload(result)
        status = result_status(result)
        write_report(args.report, payload)
    except Exception as exc:
        parser.exit(2, "focused report unavailable: " + type(exc).__name__ + "\n")
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    return status
