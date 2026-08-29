#!/usr/bin/env python3
"""Elenchus guard check.

A fix is guarded when its changed test records an assertion failure against
the parent tree. The runner writes a declared structured report; process text
and ordinary exit codes remain diagnostic evidence and never decide whether a
test asserted, passed, or broke before assertion.

Exit 0 unless ``--require-guard`` is set and the result is not ``guarded``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import xml.etree.ElementTree as ET

TEST_NAMES = ("test_", "_test.", ".test.", ".spec.", ".t.sol")
TEST_DIRS = ("test", "tests", "spec", "__tests__")
REPORT_FORMATS = ("unittest-json-v1", "forge-junit-v1", "node-test-json-v1")
REPORT_PLACEHOLDER = "{report}"
MAX_REPORT_BYTES = 1024 * 1024
MAX_DIAGNOSTIC_CHARS = 4000


class ReportError(ValueError):
    """A runner report failed the declared structural contract."""


@dataclass(frozen=True)
class RunnerReport:
    complete: bool
    executed: int
    assertion_failures: int
    errors: int
    skipped: int


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def is_test(path: str) -> bool:
    name = Path(path).name
    if any(marker in name for marker in TEST_NAMES):
        return True
    return any(part in TEST_DIRS for part in Path(path).parts[:-1])


def changed_tests(repo: Path, ref: str) -> list[str]:
    out = git(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--diff-filter=AM",
        "-r",
        ref,
    )
    return sorted(path for path in out.splitlines() if path and is_test(path))


def parent_of(repo: Path, ref: str) -> str | None:
    try:
        return git(repo, "rev-parse", f"{ref}^").strip()
    except RuntimeError:
        return None


def _integer(value, name: str) -> int:
    if type(value) is not int or value < 0:
        raise ReportError(f"{name} must be a non-negative integer")
    return value


def _normalised(complete, executed, failures, errors, skipped) -> RunnerReport:
    if complete is not True:
        raise ReportError("the report is incomplete")
    report = RunnerReport(
        complete=True,
        executed=_integer(executed, "executed"),
        assertion_failures=_integer(failures, "assertion_failures"),
        errors=_integer(errors, "errors"),
        skipped=_integer(skipped, "skipped"),
    )
    if report.assertion_failures + report.errors > report.executed:
        raise ReportError("outcome counts exceed executed tests")
    return report


def _json_object(raw: bytes) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ReportError("the report is not valid UTF-8 JSON") from err
    if type(value) is not dict:
        raise ReportError("the report root must be an object")
    return value


def parse_unittest_report(raw: bytes) -> RunnerReport:
    value = _json_object(raw)
    required = {
        "schema", "complete", "testsRun", "failures", "errors", "skipped",
        "expectedFailures", "unexpectedSuccesses",
    }
    if set(value) != required or value.get("schema") != "elenchus.unittest.v1":
        raise ReportError("the unittest report schema is not supported")
    tests_run = _integer(value["testsRun"], "testsRun")
    failures = _integer(value["failures"], "failures")
    errors = _integer(value["errors"], "errors")
    skipped = _integer(value["skipped"], "skipped")
    expected = _integer(value["expectedFailures"], "expectedFailures")
    unexpected = _integer(value["unexpectedSuccesses"], "unexpectedSuccesses")
    if failures + errors + skipped + expected + unexpected > tests_run:
        raise ReportError("unittest categories exceed testsRun")
    executed = tests_run - skipped - expected
    return _normalised(
        value["complete"], executed, failures, errors + unexpected, skipped + expected
    )


def parse_node_report(raw: bytes) -> RunnerReport:
    value = _json_object(raw)
    required = {
        "schema", "complete", "executed", "assertionFailures", "errors", "skipped",
    }
    if set(value) != required or value.get("schema") != "elenchus.node-test.v1":
        raise ReportError("the Node report schema is not supported")
    return _normalised(
        value["complete"], value["executed"], value["assertionFailures"],
        value["errors"], value["skipped"],
    )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_forge_report(raw: bytes) -> RunnerReport:
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ReportError("XML declarations with entities are not accepted")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as err:
        raise ReportError("the report is not valid XML") from err
    if _local_name(root.tag) != "testsuites":
        raise ReportError("the Forge JUnit root must be testsuites")
    cases = [node for node in root.iter() if _local_name(node.tag) == "testcase"]
    failures = errors = skipped = 0
    for case in cases:
        children = {_local_name(child.tag) for child in case}
        failures += "failure" in children
        errors += "error" in children
        skipped += "skipped" in children
        if len(children & {"failure", "error", "skipped"}) > 1:
            raise ReportError("a Forge testcase has contradictory outcomes")
    for attribute, observed in (
        ("tests", len(cases)), ("failures", failures), ("errors", errors)
    ):
        declared = root.attrib.get(attribute)
        if declared is None or not declared.isascii() or not declared.isdecimal():
            raise ReportError(f"the Forge report lacks a valid {attribute} total")
        if int(declared) != observed:
            raise ReportError(f"the Forge {attribute} total contradicts its cases")
    return _normalised(True, len(cases) - skipped, failures, errors, skipped)


def _verify_report_location(tree: Path, candidate: Path) -> None:
    root = tree.resolve()
    current = candidate
    while current != tree:
        if current.is_symlink():
            raise ReportError("the report path cannot contain a symlink")
        current = current.parent
    try:
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, ValueError) as err:
        raise ReportError("the report path escapes the worktree") from err


def read_report(
    path: Path, report_format: str, started_ns: int, tree: Path | None = None
) -> RunnerReport:
    if tree is not None:
        _verify_report_location(tree, path)
    try:
        stat = path.stat()
    except OSError as err:
        raise ReportError("the runner did not create its report") from err
    if not path.is_file() or path.is_symlink():
        raise ReportError("the runner report is not a regular file")
    if stat.st_mtime_ns < started_ns:
        raise ReportError("the runner report is stale")
    try:
        with path.open("rb") as source:
            raw = source.read(MAX_REPORT_BYTES + 1)
    except OSError as err:
        raise ReportError("the runner report could not be read") from err
    if len(raw) > MAX_REPORT_BYTES:
        raise ReportError("the runner report exceeds the size limit")
    parsers = {
        "unittest-json-v1": parse_unittest_report,
        "forge-junit-v1": parse_forge_report,
        "node-test-json-v1": parse_node_report,
    }
    parser = parsers.get(report_format)
    if parser is None:
        raise ReportError("the declared report format is not supported")
    return parser(raw)


def classify(report: RunnerReport) -> tuple[str, str]:
    if report.executed == 0:
        return "inconclusive", "the runner report records no executed tests"
    if report.errors > 0:
        return "inconclusive", "the runner report records an infrastructure error"
    if report.assertion_failures > 0:
        return "guarded", "the runner report records a parent assertion failure"
    return "passed", "the runner report records that the guard passed on the parent"


def _tracked(tree: Path, relative: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(tree), "ls-files", "--error-unmatch", "--", str(relative)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def prepare_report_path(tree: Path, raw_path: str) -> Path:
    relative = Path(raw_path)
    if not raw_path or relative.is_absolute() or ".." in relative.parts:
        raise ReportError("the report path must be a relative worktree descendant")
    candidate = tree / relative
    _verify_report_location(tree, candidate)
    if _tracked(tree, relative):
        raise ReportError("the report path names a tracked file")
    if candidate.exists():
        if not candidate.is_file() or candidate.is_symlink():
            raise ReportError("the stale report path is not a regular file")
        candidate.unlink()
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def _base_result(ref: str, status: str, tests: list[str], detail: str) -> dict:
    return {"ref": ref, "status": status, "tests": tests, "detail": detail}


def check(
    repo: Path,
    ref: str,
    command: list[str],
    timeout: int = 900,
    report_format: str | None = None,
    report_file: str | None = None,
) -> dict:
    tests = changed_tests(repo, ref)
    if not tests:
        return _base_result(ref, "unguarded", [], "the commit changed no test files")
    if not report_format or not report_file:
        return _base_result(
            ref, "inconclusive", tests, "declare both --report-format and --report-file"
        )
    if not command:
        return _base_result(
            ref, "inconclusive", tests, "the test command is empty"
        )
    parent = parent_of(repo, ref)
    if parent is None:
        return _base_result(
            ref, "inconclusive", tests, "the commit has no parent to compare against"
        )

    workdir = Path(tempfile.mkdtemp(prefix="elenchus-"))
    tree = workdir / "tree"
    try:
        git(repo, "worktree", "add", "--quiet", "--detach", str(tree), parent)
        for relative in tests:
            blob = git(repo, "show", f"{ref}:{relative}")
            target = tree / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(blob, encoding="utf-8")
        try:
            report_path = prepare_report_path(tree, report_file)
        except ReportError as err:
            return _base_result(ref, "inconclusive", tests, str(err))

        if command.count(REPORT_PLACEHOLDER) != 1:
            return _base_result(
                ref,
                "inconclusive",
                tests,
                "the test command must contain one exact {report} argument",
            )
        resolved_command = [
            str(report_path) if argument == REPORT_PLACEHOLDER else argument
            for argument in command
        ]
        environment = os.environ.copy()
        environment.pop("ELENCHUS_REPORT_FILE", None)
        started_ns = time.time_ns()
        try:
            run = subprocess.run(
                resolved_command, cwd=tree, capture_output=True, text=True, check=False,
                timeout=timeout, env=environment,
            )
        except subprocess.TimeoutExpired:
            return _base_result(
                ref, "inconclusive", tests, f"the run did not finish inside {timeout}s"
            )
        except OSError:
            return _base_result(
                ref, "inconclusive", tests, "the test command could not be started"
            )

        output = (run.stdout + run.stderr)[-MAX_DIAGNOSTIC_CHARS:]
        if run.returncode < 0:
            result = _base_result(
                ref, "inconclusive", tests, "the test command was interrupted"
            )
        else:
            try:
                report = read_report(report_path, report_format, started_ns, tree)
                status, detail = classify(report)
                result = _base_result(ref, status, tests, detail)
                result["report"] = {
                    "complete": report.complete,
                    "executed": report.executed,
                    "assertion_failures": report.assertion_failures,
                    "errors": report.errors,
                    "skipped": report.skipped,
                }
            except ReportError as err:
                result = _base_result(ref, "inconclusive", tests, str(err))
        result.update({"exit_code": run.returncode, "output": output})
        return result
    finally:
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(tree)],
            capture_output=True,
            check=False,
        )
        shutil.rmtree(workdir, ignore_errors=True)


def audit_line(result: dict) -> str:
    """The line to carry into the audit file's leads-not-pursued list."""
    return (
        f"Guard check on `{result['ref'][:12]}`: {result['status']} "
        f"-- {result['detail']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Elenchus guard check.")
    parser.add_argument("--repo", default=".", help="repository to inspect")
    parser.add_argument("--ref", default="HEAD", help="commit carrying the fix")
    parser.add_argument(
        "--test-command", required=True,
        help="how to run the tests, with quoting interpreted by shlex",
    )
    parser.add_argument("--report-format", choices=REPORT_FORMATS)
    parser.add_argument("--report-file")
    parser.add_argument(
        "--require-guard", action="store_true", help="exit 1 unless the fix is guarded"
    )
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        result = check(
            Path(args.repo).resolve(), args.ref, shlex.split(args.test_command),
            args.timeout, args.report_format, args.report_file,
        )
    except (RuntimeError, ValueError) as err:
        print(f"could not inspect the repository: {err}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(audit_line(result))
        for path in result["tests"]:
            print(f"  test: {path}")
    return 1 if args.require_guard and result["status"] != "guarded" else 0


if __name__ == "__main__":
    sys.exit(main())
