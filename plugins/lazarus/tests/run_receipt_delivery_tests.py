#!/usr/bin/env python3
"""Run the Lazarus and Ariadne suites under one structured audit report."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

try:
    from . import run_tests as source_runner
except ImportError:  # Direct execution from this file's directory.
    import run_tests as source_runner


def worktree_root() -> Path:
    """Resolve the repository worktree that owns this runner."""

    return Path(__file__).resolve(strict=True).parents[3]


def combined_suite(loader: unittest.TestLoader | None = None) -> unittest.TestSuite:
    """Discover both plugin suites under distinct repository-qualified names."""

    root = worktree_root()
    for path in (
        root,
        root / "plugins" / "lazarus" / "scripts",
        root / "plugins" / "ariadne" / "scripts",
    ):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)
    loader = loader or unittest.defaultTestLoader
    suites = [
        loader.discover(
            str(root / "plugins" / plugin / "tests"),
            pattern="test_*.py",
            top_level_dir=str(root),
        )
        for plugin in ("lazarus", "ariadne")
    ]
    return unittest.TestSuite(suites)


def main(argv: list[str] | None = None) -> int:
    """Run both suites, write one fresh report, and preserve their joint exit."""

    target = source_runner.report_target(sys.argv[1:] if argv is None else argv)
    result = unittest.TextTestRunner(verbosity=1).run(combined_suite())
    not_passed = sum(
        len(outcomes)
        for outcomes in (
            result.failures,
            result.errors,
            result.skipped,
            result.expectedFailures,
            result.unexpectedSuccesses,
        )
    )
    if target is not None:
        try:
            source_runner.write_report(target, source_runner.result_payload(result))
        except OSError:
            print(
                "run_receipt_delivery_tests.py: report write failed",
                file=sys.stderr,
            )
            return 2
    print(f"{result.testsRun - not_passed}/{result.testsRun} tests passed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
