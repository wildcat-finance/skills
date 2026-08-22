#!/usr/bin/env python3
"""Run named unittest selectors and atomically write an Elenchus report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


SCHEMA = "elenchus.unittest.v1"
MAX_REPORT_BYTES = 1024 * 1024


class ReportWriteError(ValueError):
    """The requested report target or encoded payload is unsafe."""


class RecordingRunner(unittest.TextTestRunner):
    """Keep the result available if a test interrupts the runner."""

    result: unittest.TestResult | None = None

    def _makeResult(self) -> unittest.TestResult:
        self.result = super()._makeResult()
        return self.result


def _report_target(raw: str, *, root: Path | None = None) -> Path:
    if not raw:
        raise ReportWriteError("the report path is empty")
    supplied = Path(raw)
    if ".." in supplied.parts:
        raise ReportWriteError("the report path must stay inside the worktree")

    root = (root or Path.cwd()).resolve()
    lexical = supplied if supplied.is_absolute() else root / supplied

    def inside_root(path: Path) -> bool:
        try:
            path.relative_to(root)
        except ValueError:
            return False
        return True

    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current /= part
        if current.is_symlink() and (
            inside_root(current.parent.resolve())
            or inside_root(current.resolve(strict=False))
        ):
            raise ReportWriteError("the report path cannot contain a symlink")

    target = lexical.resolve(strict=False)
    try:
        relative = target.relative_to(root)
    except ValueError as error:
        raise ReportWriteError("the report path must stay inside the worktree") from error
    if not relative.parts:
        raise ReportWriteError("the report path must name a file")

    current = root
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink():
            raise ReportWriteError("the report path cannot contain a symlink")
        try:
            current.mkdir(exist_ok=True)
        except OSError as error:
            raise ReportWriteError("the report directory could not be created") from error
        if not current.is_dir():
            raise ReportWriteError("the report parent is not a directory")

    target = current / relative.parts[-1]
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ReportWriteError("the report path must be a regular file")
    return target


def _payload(result: unittest.TestResult, complete: bool) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "complete": complete,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def _write_report(
    raw_target: str,
    payload: dict[str, object],
    *,
    root: Path | None = None,
) -> None:
    target = _report_target(raw_target, root=root)
    encoded = (
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_REPORT_BYTES:
        raise ReportWriteError("the report exceeds the size limit")

    handle = tempfile.NamedTemporaryFile(
        mode="wb",
        dir=target.parent,
        prefix=".unittest-report-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, target)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run named unittest selectors and write unittest-json-v1."
    )
    parser.add_argument("report", help="report path inside the current worktree")
    parser.add_argument("selectors", nargs="+", help="named unittest selectors")
    args = parser.parse_args(argv)

    invocation_root = Path.cwd().resolve()
    sys.path.insert(0, str(invocation_root))
    runner = RecordingRunner(verbosity=1)
    interrupted = False
    try:
        suite = unittest.defaultTestLoader.loadTestsFromNames(args.selectors)
        result = runner.run(suite)
    except BaseException:
        interrupted = True
        result = runner.result or unittest.TestResult()

    try:
        _write_report(
            args.report,
            _payload(result, complete=not interrupted),
            root=invocation_root,
        )
    except (OSError, ReportWriteError) as error:
        print(f"could not write unittest report: {error}", file=sys.stderr)
        return 2

    if interrupted:
        return 130
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
