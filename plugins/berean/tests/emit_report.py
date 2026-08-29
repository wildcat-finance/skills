#!/usr/bin/env python3
"""Run the Berean suite and emit one fresh Elenchus report.

The confined single-target write path is not reimplemented here. It is the
hardened one in the repository's tests/emit_run_observation_report.py, which
several audit rounds shaped, and a second copy would be a second thing to
harden. Only the suite differs: the discover command the Berean runner
contract names.
"""

import importlib.util
from pathlib import Path
import sys
import unittest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import tests.support  # noqa: E402,F401

# Berean's tests import `tests.support`, so the name `tests` must stay bound to
# this plugin's package for the whole run. The shared writer is a module of the
# repository-root `tests` package, and importing it under that name would bind
# `tests` to the wrong package, so it is loaded by file path under a private
# module name instead.
WRITER = REPOSITORY_ROOT / "tests" / "emit_run_observation_report.py"
_specification = importlib.util.spec_from_file_location("_berean_report_writer", WRITER)
_writer = importlib.util.module_from_spec(_specification)
_specification.loader.exec_module(_writer)
report_target = _writer.report_target
result_payload = _writer.result_payload
write_report = _writer.write_report


def main(argv=None):
    target = report_target(sys.argv[1:] if argv is None else argv)
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(PLUGIN_ROOT / "tests"), top_level_dir=str(PLUGIN_ROOT)
    )
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("emit_report.py: report write failed", file=sys.stderr)
        return 2
    failed = len(result.failures) + len(result.errors)
    print(f"{result.testsRun - failed}/{result.testsRun} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
