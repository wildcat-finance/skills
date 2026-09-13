#!/usr/bin/env python3
"""Run both existing corpus modules and write one fresh Elenchus report."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.emit_run_observation_report import (  # noqa: E402
    report_target,
    result_payload,
    write_report,
)


MODULES = (
    "tests.test_agent_instruction",
    "tests.test_agent_instruction_corpus",
)


def main(argv=None):
    """Accept one unused worktree report path; return 0, test failure 1 or I/O 2."""
    target = report_target(sys.argv[1:] if argv is None else argv)
    suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("agent-instruction-reconciliation: report write failed", file=sys.stderr)
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
