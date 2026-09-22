#!/usr/bin/env python3
"""Exercise implemented conformance operations; refuse pending operations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import stat
import sys
import tempfile
import time
import tracemalloc
import unittest


CANDIDATES = ("process-parent-runner", "manual-conformance", "typed-applicability")
OPERATIONS = {
    "applicability-parser": 2,
    "bounded-reader": 2,
    "frozen-controller-join": 3,
    "native-execution": 4,
    "bounded-execution": 4,
    "legacy-and-hostile-replay": 4,
}


class Refusal(Exception):
    """Carry a fixed refusal code without caller data or filesystem details."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("invalid-arguments")


def check_report_slot(raw: str, root: Path) -> None:
    """Check a JSON operand under root/.hexaemeron/reports without writing it.

    Refuse occupied leaves, linked ancestors and unsupported path spellings.
    The writer separately uses exclusive leaves and held directory descriptors.
    """
    if (
        len(raw) > 1024
        or "\\" in raw
        or any(part in (".", "..") for part in raw.split("/"))
        or any(ord(char) < 32 or ord(char) > 126 for char in raw)
    ):
        raise Refusal("report-path-invalid")
    path = Path(raw)
    if path.is_absolute():
        try:
            path = path.relative_to(root)
        except ValueError:
            raise Refusal("report-path-invalid") from None
    parts = path.parts
    if (
        len(parts) < 3
        or parts[:2] != (".hexaemeron", "reports")
        or path.suffix != ".json"
        or any(re.fullmatch(r"[A-Za-z0-9_.-]+", part) is None for part in parts)
    ):
        raise Refusal("report-path-invalid")
    cursor = root
    for index, part in enumerate(parts):
        cursor = cursor / part
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            return
        except OSError:
            raise Refusal("report-path-unavailable") from None
        if index == len(parts) - 1:
            raise Refusal("report-exists")
        if not stat.S_ISDIR(mode):
            raise Refusal("report-path-invalid")


def _subject():
    root = Path(__file__).resolve().parents[2]
    path = root / "plugins/hexaemeron/tests/test_audit_applicability.py"
    spec = importlib.util.spec_from_file_location("native_admission_parser_proof", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return root, module


def _sources(root):
    paths = ["docs/native-guard-admission/proof.py",
             "plugins/hexaemeron/tests/test_audit_applicability.py",
             "plugins/hexaemeron/tests/run_tests.py"]
    paths += ["plugins/hexaemeron/skills/protasis/scripts/" + name + ".py"
              for name in ("audit_applicability", "known_failure_inventory", "success_criteria",
                           "protasis", "gate_commands")]
    return [{"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
            for path in sorted(paths)]


def _execute(criterion):
    root, subject = _subject()
    source_before = _sources(root)
    suite = unittest.TestSuite()
    classes = [subject.ApplicabilityReaderTests]
    if criterion == "applicability-parser":
        classes.insert(0, subject.ApplicabilityParserTests)
    for test_class in classes:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_class))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    evidence = {"schema": "native-guard-admission-parser-proof/v1",
                "criterion": criterion, "sources": source_before,
                "tests": result.testsRun, "failures": len(result.failures),
                "errors": len(result.errors), "skips": len(result.skipped),
                "expected_failures": len(result.expectedFailures),
                "unexpected_successes": len(result.unexpectedSuccesses),
                "operation_ran": True, "declared_command_launches": 0,
                "budget": None,
                "boundary": "Authored synthetic parser inputs; no controller admission, execution or host isolation claim."}
    passed = (result.wasSuccessful() and result.testsRun > 0 and not result.skipped
              and not result.expectedFailures)
    if passed and criterion == "bounded-reader":
        with tempfile.TemporaryDirectory(prefix="applicability-budget-") as directory:
            fixture = subject.maximum_fixture(Path(directory))
            inputs = [{"path": str(path.relative_to(directory)), "bytes": path.stat().st_size,
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                      for path in sorted(Path(directory).rglob("*")) if path.is_file()]
            observations = []
            for _ in range(3):
                tracemalloc.start()
                started = time.monotonic()
                loaded = fixture.load()
                elapsed = time.monotonic() - started
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                observations.append({"seconds": elapsed, "peak_traced_bytes": peak,
                                     "status": loaded.status})
            passed = all(row["status"] == "clean" and row["seconds"] <= 30
                         and row["peak_traced_bytes"] <= 64 * 1024 * 1024 for row in observations)
            evidence["budget"] = {"method": "Three loads of the same prebuilt maximum fixture; tracing covers each load only.",
                                  "host": platform.platform(), "machine": platform.machine(),
                                  "interpreter": sys.version, "executable": sys.executable,
                                  "inputs": inputs,
                                  "input_sha256": hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                                  "document_bytes": fixture.study.stat().st_size,
                                  "source_view_pairs": 32, "entries": 128,
                                  "source_view_bytes": 16 * 1024 * 1024,
                                  "seconds_limit": 30, "traced_bytes_limit": 64 * 1024 * 1024,
                                  "observations": observations,
                                  "p95_seconds": max(row["seconds"] for row in observations),
                                  "max_traced_bytes": max(row["peak_traced_bytes"] for row in observations),
                                  "passed": passed, "speedup_claim": False}
    if _sources(root) != source_before:
        raise Refusal("proof-source-drift")
    return passed, evidence


def _write_pair(root, report, report_bytes, evidence_bytes):
    """Publish evidence first, report last; retain partial output after refusal."""
    relative = Path(report)
    if relative.is_absolute():
        relative = relative.relative_to(root)
    descriptors, links = [], []
    try:
        current = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(current)
        for part in relative.parts[:-1]:
            try:
                os.mkdir(part, 0o700, dir_fd=current)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            links.append((current, part, child))
            descriptors.append(child)
            current = child
        for name, data in ((relative.stem + ".evidence.json", evidence_bytes), (relative.name, report_bytes)):
            for parent, part, child in links:
                named, opened = os.stat(part, dir_fd=parent, follow_symlinks=False), os.fstat(child)
                if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
                    raise Refusal("report-path-changed")
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=current)
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.fsync(current)
        for parent, part, child in links:
            named, opened = os.stat(part, dir_fd=parent, follow_symlinks=False), os.fstat(child)
            if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
                raise Refusal("report-path-changed")
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    """Run a landed resolver; exit 2 without a report for a pending operation."""
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=tuple(OPERATIONS))
    parser.add_argument("--report", required=True)
    result = {
        "schema": "native-guard-admission-refusal/v1",
        "candidate": None,
        "criterion": None,
        "available_step": None,
        "report_written": False,
        "code": "invalid-arguments",
    }
    try:
        args = parser.parse_args(argv)
        result.update(
            candidate=args.candidate,
            criterion=args.criterion,
            available_step=OPERATIONS[args.criterion],
        )
        check_report_slot(args.report, Path.cwd())
        if args.candidate != "typed-applicability" or OPERATIONS[args.criterion] != 2:
            raise Refusal("operation-unavailable")
        check_report_slot(str(Path(args.report).with_suffix(".evidence.json")), Path.cwd())
        passed, evidence = _execute(args.criterion)
        command = ("python3 docs/native-guard-admission/proof.py --candidate " + args.candidate
                   + " --criterion " + args.criterion + " --report " + args.report)
        record = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
                  "criterion": args.criterion, "value": passed, "unit": "boolean",
                  "command": command, "exit": 0 if passed else 1}
        report_bytes = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode()
        evidence.update(command=command, design_report_sha256=hashlib.sha256(report_bytes).hexdigest())
        evidence_bytes = (json.dumps(evidence, sort_keys=True, indent=2) + "\n").encode()
        _write_pair(Path.cwd(), args.report, report_bytes, evidence_bytes)
        print(json.dumps({"schema": "native-guard-admission-proof/v1", "criterion": args.criterion,
                          "report_written": True, "passed": passed,
                          "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
                          "evidence_sha256": hashlib.sha256(evidence_bytes).hexdigest()}, sort_keys=True))
        return 0 if passed else 1
    except Refusal as error:
        result["code"] = str(error)
    except OSError:
        result["code"] = "report-path-unavailable"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
