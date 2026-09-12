#!/usr/bin/env python3
"""Run the recovery guards and emit Elenchus's closed unittest report."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MODULES = (
    "tests.test_agent_instruction",
    "tests.test_agent_instruction_corpus",
    "tests.test_skills_sh_package",
    "plugins.hexaemeron.tests.test_audit_synopsis_recovery",
    "plugins.hexaemeron.tests.test_phylax_model_proxy.ConformanceTests."
    "test_skill_package_marketplace_coverage_and_portable_versions_are_exact",
    "tests.test_promise_machine_contract.PromiseEvaluationGateTests",
    "tests.test_obligation_gate_demonstration.DemonstrationRecordTests",
)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: emit_main_root_recovery_report.py REPORT", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
