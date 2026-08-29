#!/usr/bin/env python3
"""Run the complete capture-profile test surface and emit one bounded report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MODULES = (
    "tests.test_run_observation_capture",
    "tests.test_run_observation_capture_inoculation",
    "tests.test_promise_machine_contract",
)
REQUIRED_SURFACE = (
    Path("schemas/promise-machine-run-observation-capture-v1.schema.json"),
    Path("scripts/run_observation_capture.py"),
    Path("tests/test_run_observation_capture.py"),
    Path("tests/test_run_observation_capture_inoculation.py"),
    Path("docs/promise-machine/run-observation-capture-v1.md"),
)


def build_suite() -> unittest.TestSuite:
    """Load exactly the complete #435 capture surface, not three wrapper tests."""
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromName(
        "tests.test_run_observation_capture.CaptureSurfaceGuardTests"
    ))
    if not all((ROOT / path).is_file() for path in REQUIRED_SURFACE):
        return suite
    for module in MODULES:
        suite.addTests(loader.loadTestsFromName(module))
    return suite


def target(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", metavar="REPORT")
    value = parser.parse_args(argv).report
    supplied = Path(value)
    root = Path.cwd().resolve(strict=True)
    if not supplied.is_absolute() or ".." in supplied.parts:
        parser.error("REPORT must be an absolute descendant of the current worktree")
    try:
        resolved = supplied.resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        parser.error("REPORT must stay inside the current worktree")
    current = root
    for part in resolved.relative_to(root).parts[:-1]:
        current /= part
        if current.exists() and (current.is_symlink() or not current.is_dir()):
            parser.error("REPORT parent must be a real directory")
    if resolved.exists() or resolved.is_symlink():
        parser.error("REPORT target must be new")
    return resolved


def write_new(path: Path, payload: bytes) -> None:
    root = Path.cwd().resolve(strict=True)
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ValueError("REPORT must stay inside the current worktree") from error
    if len(relative.parts) < 2:
        raise ValueError("REPORT must be a descendant of the current worktree")
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        directory_flags |= os.O_NOFOLLOW
    directory = os.open(root, directory_flags)
    try:
        for part in relative.parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=directory)
            except FileExistsError:
                pass
            next_directory = os.open(part, directory_flags, dir_fd=directory)
            os.close(directory)
            directory = next_directory
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(relative.name, flags, stat.S_IRUSR | stat.S_IWUSR, dir_fd=directory)
    except OSError as error:
        raise ValueError("REPORT parent must be a real directory and target must be new") from error
    finally:
        os.close(directory)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    output = target(argv)
    suite = build_suite()
    expected_tests = suite.countTestCases()
    if expected_tests == 0:
        raise SystemExit("capture report surface resolved no tests")
    result = unittest.TestResult()
    suite.run(result)
    payload = {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }
    write_new(output, (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"))
    return 0 if not (result.failures or result.errors or result.unexpectedSuccesses) else 1


if __name__ == "__main__":
    raise SystemExit(main())
