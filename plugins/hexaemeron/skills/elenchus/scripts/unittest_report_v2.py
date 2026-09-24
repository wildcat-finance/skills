#!/usr/bin/env python3
"""Run named stdlib unittest modules and write an ``elenchus.unittest.v2`` report.

The v2 report carries the v1 counters plus one ``errorDetails`` row per error:
the erroring test's id, the repository-relative path of the module that defines
it, the exception type, and the missing name an ``AttributeError``,
``KeyError`` or ``NameError`` carries. Elenchus reads those rows only to decide
whether an error is a changed test reading a name its fix introduces; the rows
never turn an error into an assertion failure.

    python3 unittest_report_v2.py --report {report} tests/test_feature.py

Each test path is relative to the working directory, which is the detached
parent worktree when Elenchus runs this. Its directory goes first on
``sys.path`` while the module loads, so sibling imports resolve as they would
under discovery. Tests run in this process, because the Elenchus runner
boundary refuses child processes.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest

NAMED_EXCEPTIONS = (AttributeError, KeyError, NameError)


def missing_name(error: BaseException) -> str | None:
    if isinstance(error, KeyError):
        key = error.args[0] if len(error.args) == 1 else None
        return key if isinstance(key, str) else None
    if isinstance(error, (AttributeError, NameError)):
        name = getattr(error, "name", None)
        return name if isinstance(name, str) else None
    return None


class DetailedResult(unittest.TextTestResult):
    """Record one detail row for every error unittest counts."""

    modules: dict[str, str] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_details = []

    def _detail(self, test, err):
        kind, value = err[0], err[1]
        module = self.modules.get(type(test).__module__)
        name = missing_name(value) if isinstance(value, NAMED_EXCEPTIONS) else None
        self.error_details.append({
            "test": test.id(),
            "module": module,
            "exception": kind.__name__,
            "name": name,
        })

    def addError(self, test, err):
        super().addError(test, err)
        self._detail(test, err)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None and not issubclass(err[0], test.failureException):
            self._detail(subtest, err)


def load(paths: list[str]) -> unittest.TestSuite:
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for raw in paths:
        path = Path(raw)
        if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
            raise SystemExit(f"test path must be a relative .py file: {raw}")
        name = path.stem
        sys.path.insert(0, str(path.parent.resolve()))
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"cannot load test module: {raw}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        DetailedResult.modules[name] = path.as_posix()
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


def write_report(target: Path, payload: dict) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    descriptor = os.open(target, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=False) as out:
            json.dump(payload, out, sort_keys=True)
        if os.utime in os.supports_fd:
            os.utime(descriptor)
    finally:
        os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--report", required=True, help="the {report} path")
    parser.add_argument("tests", nargs="+", help="test module paths to run")
    args = parser.parse_args(argv)
    target = Path(args.report)
    result = unittest.TextTestRunner(
        stream=sys.stderr, resultclass=DetailedResult, verbosity=1
    ).run(load(args.tests))
    write_report(target, {
        "schema": "elenchus.unittest.v2",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
        "errorDetails": result.error_details,
    })
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
