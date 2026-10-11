"""Run explicit timestamp suites and retain truthful, confined test evidence."""

from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Reuse the existing no-follow, create-only writer and observed unittest counters.
from wildcat_v3_reports import (EvidenceUnavailable, ObservedResult, REPORT_CAP,
                                report_parts, result_payload, result_status,
                                run_cases, write_report as create_report)

CASE_TESTS = {
    "scaffold": (("test_wildcat_timestamps", "TimestampScaffoldTests"),),
    "capture": (("test_wildcat_timestamp_capture", "CaptureTests"),),
    "mapping": (("test_wildcat_timestamp_mapping", "MappingTests"),),
    "demonstration": (("test_wildcat_timestamp_demonstration", "DemonstrationTests"),),
    "integration": (("test_wildcat_timestamp_demonstration", "DemonstrationTests"),),
}


def write_report(raw: str, payload: dict) -> None:
    """Create evidence or admit identical regular bytes for repeat audit runs."""
    try:
        create_report(raw, payload)
        return
    except FileExistsError:
        pass
    expected = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    parts = report_parts(raw, Path.cwd())
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent = os.open(Path.cwd(), flags)
    try:
        for part in parts[:-1]:
            child = os.open(part, flags, dir_fd=parent)
            os.close(parent)
            parent = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > REPORT_CAP:
                raise ValueError("existing report is not bounded regular evidence")
            actual = stream.read(REPORT_CAP + 1)
            after = os.fstat(stream.fileno())
        linked = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size,
                                  value.st_mtime_ns, value.st_ctime_ns)
        if (actual != expected or identity(before) != identity(after)
                or identity(after) != identity(linked)):
            raise ValueError("existing report differs or changed during admission")
    finally:
        os.close(parent)


def execute(parser, argv: list[str] | None = None) -> int:
    """Run a named suite; unavailable production conformance never writes proof."""
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report_parts(args.report, Path.cwd())
        selected = CASE_TESTS.get(args.case, ())
        if not selected:
            raise EvidenceUnavailable("timestamp case not implemented: " + args.case)
        if args.case == "integration":
            from test_wildcat_timestamp_demonstration import DemonstrationTests
            DemonstrationTests.observations = {}
        result = run_cases(selected)
        payload = result_payload(result)
        status = result_status(result)
        if args.case == "integration":
            from test_wildcat_timestamp_demonstration import DemonstrationTests
            required = {"capture-to-dossier", "wrong-hash-refused", "incomplete-inventory-refused",
                        "legacy-mixed-dates", "legacy-absence-undated"}
            if status != 0 or set(DemonstrationTests.observations) != required:
                raise EvidenceUnavailable("executed production timestamp conformance failed")
            details = {"schema": "wildcat-timestamp-production-demonstration/v1",
                       "execution": payload, "observations": DemonstrationTests.observations,
                       "network": "socket creation denied during offline consumption",
                       "source_sha256": source_identities(),
                       "command": "python3 plugins/tabularium/tests/prove_wildcat_timestamps.py --case integration --report " + args.report}
            write_report(args.report.removesuffix(".json") + ".details.json", details)
            payload = {"schema": "protasis-design-report/v1", "candidate": "collector-journal",
                       "criterion": "timestamp-demo", "value": True, "unit": "boolean",
                       "command": details["command"], "exit": 0}
        write_report(args.report, payload)
    except EvidenceUnavailable as exc:
        parser.exit(2, str(exc) + "\n")
    except Exception as exc:
        parser.exit(2, "timestamp report unavailable: " + type(exc).__name__ + "\n")
    print(json.dumps(payload, sort_keys=True), file=sys.stderr)
    return status


def source_identities():
    """Bind executed modules and fixture bytes without inspecting Git or custody paths."""
    import hashlib
    root = HERE.parents[2]
    names = ("plugins/tabularium/tests/prove_wildcat_timestamps.py",
             "plugins/tabularium/tests/wildcat_timestamp_reports.py",
             "plugins/tabularium/tests/test_wildcat_timestamp_demonstration.py",
             "plugins/tabularium/tests/test_wildcat_timestamp_capture.py",
             "plugins/tabularium/tests/test_wildcat_timestamp_mapping.py",
             "plugins/tabularium/tests/test_wildcat_view.py",
             "plugins/tabularium/scripts/tabularium_lib/wildcat_view.py",
             "plugins/tabularium/scripts/tabularium_lib/wildcat_timestamps.py",
             "plugins/probitas/scripts/probitas_lib/wildcat_archive.py",
             "plugins/alexandria/scripts/usdc_interval.py",
             "plugins/alexandria/scripts/alexandria_lib/event_headers.py",
             "plugins/alexandria/tests/fixtures/wildcat-interval-transport.json")
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}
