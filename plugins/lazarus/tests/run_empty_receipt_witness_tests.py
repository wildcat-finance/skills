#!/usr/bin/env python3
"""Run the empty receipt-witness suite and write one Elenchus report."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

try:
    from . import run_tests as source_runner
except ImportError:  # Direct execution from this file's directory.
    import run_tests as source_runner


def focused_suite(loader: unittest.TestLoader | None = None) -> unittest.TestSuite:
    """Discover only the source-bound empty receipt-witness tests."""

    root = Path(__file__).resolve(strict=True).parents[3]
    scripts = root / "plugins" / "lazarus" / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    loader = loader or unittest.defaultTestLoader
    return loader.discover(
        str(root / "plugins" / "lazarus" / "tests"),
        pattern="test_empty_receipts.py",
        top_level_dir=str(root / "plugins" / "lazarus"),
    )


def main(argv: list[str] | None = None) -> int:
    """Run focused tests, emit the declared report, and preserve their exit."""

    target = source_runner.report_target(sys.argv[1:] if argv is None else argv)
    result = unittest.TextTestRunner(verbosity=1).run(focused_suite())
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
            print("run_empty_receipt_witness_tests.py: report write failed", file=sys.stderr)
            return 2
    print(f"{result.testsRun - not_passed}/{result.testsRun} tests passed")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
