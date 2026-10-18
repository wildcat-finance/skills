"""Bounded report creation and explicit in-process Step selection for #2092.

`emit_wrapper_report.py` delegates here, so later Steps extend this module
while the registered interface bytes stay fixed after Step 1's push binding.

A focused run loads only the classes `STEP_CASES` names for the Step, runs
them in this process and writes one fresh `unittest-json-v1` report with the
actual counters. A retained run loads the three preserved-rebuild modules
whole, refuses before any test when either staging variable is unset, and
counts a skip as a non-zero exit, so a rebuild cannot pass by skipping.

Exit 0 means every selected test ran and passed. Exit 1 means a failure, a
skip, an expected failure or an unexpected success. Exit 2 means an error,
an empty run, or a refusal before any report was written. No subprocess is
launched, and nothing is written except the one report file.
"""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import stat
import sys
import unittest

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
# The test modules import each other as `tests.<name>`, as the suite's own
# `discover -t plugins/alexandria` does, so the package parent must resolve.
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))

PACKAGE = "tests"
REPORT_SCHEMA = "elenchus.unittest.v1"
REPORT_CAP = 1024 * 1024
TEST_CAP = 1000
STAGING_VARIABLES = ("ALEXANDRIA_WILDCAT_V1_STAGING", "ALEXANDRIA_WILDCAT_V2_STAGING")

# Step number to the exact focused classes it runs; later Steps add rows.
STEP_CASES = {
    1: (
        ("test_wildcat_wrappers", "LegacyIdentityTests"),
        ("test_wrapper_report_runner", "WrapperReportRunnerTests"),
        ("test_wrapper_report_runner", "RunRecordBundleTests"),
    ),
}
# The preserved-rebuild modules, each run whole; `None` selects every class.
RETAINED_CASES = (
    ("test_wildcat_v2_interval_demo", None),
    ("test_wildcat_v1_interval_demo", None),
    ("test_wildcat_estates_interval_demo", None),
)


class EvidenceUnavailable(ValueError):
    """The declared tests, variables or report path cannot be used."""


def load_cases(cases) -> unittest.TestSuite:
    """Resolve each named module from this directory and each named class in it."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for module_name, class_name in cases:
        source = HERE / (module_name + ".py")
        if source.is_symlink() or not source.is_file():
            raise EvidenceUnavailable("test source unavailable: " + module_name)
        module = importlib.import_module(PACKAGE + "." + module_name)
        if Path(module.__file__).resolve() != source:
            raise EvidenceUnavailable("test source differs: " + module_name)
        if class_name is None:
            suite.addTests(loader.loadTestsFromModule(module))
            continue
        case = getattr(module, class_name, None)
        if not isinstance(case, type) or not issubclass(case, unittest.TestCase):
            raise EvidenceUnavailable("test class unavailable: " + class_name)
        suite.addTests(loader.loadTestsFromTestCase(case))
    if loader.errors:
        raise EvidenceUnavailable("test loading reported errors")
    if not 0 < suite.countTestCases() <= TEST_CAP:
        raise EvidenceUnavailable("test count outside declared bounds")
    return suite


def result_payload(result: unittest.TestResult) -> dict:
    """Elenchus's closed `unittest-json-v1` counter set, read from the run."""
    return {
        "schema": REPORT_SCHEMA,
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def result_status(result: unittest.TestResult) -> int:
    """Errors and empty runs exit 2, kept apart from failures and skips at 1."""
    if result.errors or not result.testsRun:
        return 2
    if (result.failures or result.skipped or result.expectedFailures
            or result.unexpectedSuccesses):
        return 1
    return 0


def report_parts(raw: str, root: Path) -> tuple[str, ...]:
    """The report's path below `root`, confined to `.elenchus` or `.hexaemeron`."""
    if not isinstance(raw, str) or not raw or len(raw.encode("utf-8")) > 4096:
        raise EvidenceUnavailable("report path outside declared bounds")
    if "\\" in raw or any(ord(char) < 32 for char in raw):
        raise EvidenceUnavailable("report path has unsafe characters")
    path = Path(raw)
    if ".." in path.parts:
        raise EvidenceUnavailable("report path escapes its worktree")
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
            raise EvidenceUnavailable("report path escapes its worktree")
    parts = path.parts
    if (not 2 <= len(parts) <= 12 or parts[0] not in (".elenchus", ".hexaemeron")
            or path.suffix != ".json"):
        raise EvidenceUnavailable("report must be JSON under .elenchus or .hexaemeron")
    return parts


def refuse_unusable_report(parts: tuple[str, ...], root: Path) -> None:
    """Refuse an existing report or a symlinked or non-directory parent before any test runs."""
    current = root
    for index, part in enumerate(parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            return
        if index == len(parts) - 1:
            raise EvidenceUnavailable("report path already exists")
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise EvidenceUnavailable("report parent is a symlink or not a directory")


def write_report(parts: tuple[str, ...], root: Path, payload: dict) -> None:
    """Create the report once, following no symlink and replacing nothing."""
    encoded = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(encoded) > REPORT_CAP:
        raise EvidenceUnavailable("report exceeds byte cap")
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


def selected_cases(args, environ) -> tuple:
    """The Step's focused classes, or the retained modules once both variables are set."""
    if args.retained:
        unset = [name for name in STAGING_VARIABLES if not environ.get(name)]
        if unset:
            raise EvidenceUnavailable("retained run needs " + " and ".join(unset))
        return RETAINED_CASES
    cases = STEP_CASES.get(args.step)
    if not cases:
        raise EvidenceUnavailable("Step has no declared focused classes")
    return cases


def execute_report(parser, argv: list[str] | None = None, *, root: Path | None = None,
                   environ=None) -> int:
    """Parse, select, run in process and write one fresh report; see the module docstring."""
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    root = Path.cwd() if root is None else Path(root)
    environ = os.environ if environ is None else environ
    try:
        parts = report_parts(args.report, root)
        refuse_unusable_report(parts, root)
        suite = load_cases(selected_cases(args, environ))
        result = unittest.TestResult()
        suite.run(result)
        payload = result_payload(result)
        status = result_status(result)
        write_report(parts, root, payload)
    except Exception as exc:
        parser.exit(2, "wrapper report unavailable: " + type(exc).__name__ + ": " + str(exc) + "\n")
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    return status
