#!/usr/bin/env python3
"""Resolve the selected checkpoint scanner's declared conformance operations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import math
import os
from pathlib import Path
import platform
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc
import unittest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from plugins.hexaemeron.tests import test_checkpoint_marker_scan as guards
from tests.emit_run_observation_report import report_target, result_payload, write_report


BASELINE_COMMIT = "e2307ed5966e18727434b3e49bec89db736f7b17"
CONTROLLER_PATH = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
SCRIPT_PATH = "plugins/hexaemeron/tests/prove_checkpoint_marker_scan.py"


def released_controller():
    """Load the exact released Git blob in a disposable directory outside the run."""
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    })
    result = subprocess.run(
        ["git", "show", BASELINE_COMMIT + ":" + CONTROLLER_PATH],
        cwd=ROOT, env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
    )
    if result.returncode != 0 or not 0 < len(result.stdout) <= 2_097_152:
        raise ValueError("released controller blob unavailable or oversized")
    digest = hashlib.sha256(result.stdout).hexdigest()
    with tempfile.TemporaryDirectory(prefix="fiat1755-released-scanner-") as directory:
        path = Path(directory) / "hexctl.py"
        path.write_bytes(result.stdout)
        specification = importlib.util.spec_from_file_location("fiat1755_released_hexctl", path)
        if specification is None or specification.loader is None:
            raise ImportError("released scanner cannot be loaded")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
    return module, digest


def measure(predicate, workload):
    samples = []
    for _ in range(5):
        started = time.perf_counter_ns()
        for payload in workload:
            guards.streaming(predicate, payload)
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    tracemalloc.start()
    try:
        for payload in workload:
            guards.streaming(predicate, payload)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return {
        "samples_ms": samples,
        "median_ceiling_ms": math.ceil(statistics.median(samples)),
        "median_ms": statistics.median(samples),
        "traced_peak_bytes": peak,
    }


def implementation_regression():
    product = guards.controller_module()
    baseline, baseline_sha256 = released_controller()
    positive, negative = guards.material_corpus()
    matrix = []
    for expected, cases in ((True, positive), (False, negative)):
        for name, payload in cases:
            observed = guards.streaming(product._checkpoint_archive_secret_shaped, payload)
            matrix.append({
                "case": name, "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "expected_refusal": expected, "observed_refusal": observed,
            })
    boundaries = [
        {"case": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
         "expected_refusal": expected,
         "observed_refusal": guards.streaming(product._checkpoint_archive_secret_shaped, payload)}
        for name, payload, expected in guards.boundary_cases()
    ]
    output = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(guards)
    result = unittest.TextTestRunner(stream=output, verbosity=1).run(suite)
    counts = result_payload(result)
    workload = guards.measurement_workload()
    released = measure(baseline._checkpoint_archive_secret_shaped, workload)
    implemented = measure(product._checkpoint_archive_secret_shaped, workload)
    token_parity = [
        (pattern.pattern, pattern.flags) for pattern in baseline.CHECKPOINT_ARCHIVE_SECRET_TOKEN_PATTERNS
    ] == [
        (pattern.pattern, pattern.flags) for pattern in product.CHECKPOINT_ARCHIVE_SECRET_TOKEN_PATTERNS
    ]
    line_parity = (
        baseline.CHECKPOINT_ARCHIVE_SECRET_BODY.pattern == product.CHECKPOINT_ARCHIVE_SECRET_BODY.pattern
        and baseline.CHECKPOINT_ARCHIVE_SECRET_BODY.flags == product.CHECKPOINT_ARCHIVE_SECRET_BODY.flags
    )
    dimensions = ("CHECKPOINT_IO_CHUNK", "CHECKPOINT_ARCHIVE_SECRET_WINDOW",
                  "CHECKPOINT_ARCHIVE_SECRET_BLOCK_LOOKAHEAD", "CHECKPOINT_ARCHIVE_SECRET_FOOTER_LOOKAHEAD")
    bounds_parity = all(getattr(baseline, name) == getattr(product, name) for name in dimensions)
    budget_pass = (
        implemented["median_ms"] <= 4 * released["median_ms"]
        and implemented["traced_peak_bytes"] < 1_048_576
    )
    clean_counts = counts["testsRun"] > 0 and all(
        counts[field] == 0
        for field in ("failures", "errors", "skipped", "expectedFailures", "unexpectedSuccesses")
    )
    value = (
        len(positive) == 436 and len(negative) == 119 and clean_counts
        and all(row["expected_refusal"] == row["observed_refusal"] for row in matrix + boundaries)
        and token_parity and line_parity and bounds_parity and budget_pass
    )
    observed = {
        "schema": "checkpoint-marker-implementation-observation/v1",
        "controller_sha256": hashlib.sha256((ROOT / CONTROLLER_PATH).read_bytes()).hexdigest(),
        "test_sha256": hashlib.sha256(Path(guards.__file__).read_bytes()).hexdigest(),
        "resolver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "released_commit": BASELINE_COMMIT, "released_controller_sha256": baseline_sha256,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "refusal_cases": len(positive), "benign_cases": len(negative),
        "cases": matrix, "boundary_cases": boundaries,
        "boundary_provenance": "New executable inputs exercise the declared limits; historical probe construction was not retained.",
        "key_evidence": {"seeded_rsa_bits": 3072, "arithmetic_roundtrip": True,
                         "relabelled_cases": "Lexical shapes, not valid EC, DSA, SSH or PGP keys.",
                         "larger_specimens": "Geometry only; no working 16384-bit keypair claimed."},
        "unittest": counts,
        "unittest_output_sha256": hashlib.sha256(output.getvalue().encode()).hexdigest(),
        "token_patterns_unchanged": token_parity, "whole_line_pattern_unchanged": line_parity,
        "scan_bounds_unchanged": bounds_parity,
        "measurement": {
            "workload_bytes": sum(map(len, workload)), "samples_each": 5,
            "method": "Sequential same-host streaming scans; inputs and module imports excluded from traced allocations; not process RSS.",
            "released": released, "implemented": implemented,
            "median_ratio": implemented["median_ms"] / released["median_ms"],
            "median_ratio_limit": 4, "traced_peak_exclusive_limit_bytes": 1_048_576,
            "budget_pass": budget_pass,
        },
        "native_archive_roundtrip": "pending Step 3",
    }
    return value, observed


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=("bounded-material",), required=True)
    parser.add_argument("--criterion", choices=("implementation-regression", "native-archive-roundtrip"), required=True)
    parser.add_argument("--report", required=True)
    options = parser.parse_args(argv)
    if options.criterion == "native-archive-roundtrip":
        print("native-archive-roundtrip requires Step 3", file=sys.stderr)
        return 2
    target = report_target([options.report])
    observation_name = str(Path(options.report).with_suffix(".observation.json"))
    observation_target = report_target([observation_name])
    value, observation = implementation_regression()
    status = 0 if value else 1
    write_report(observation_target, observation)
    write_report(target, {
        "schema": "protasis-design-report/v1", "candidate": options.candidate,
        "criterion": options.criterion, "value": value, "unit": "boolean",
        "command": shlex.join(["python3", SCRIPT_PATH, *argv]), "exit": status,
    })
    print("implementation-regression: " + ("pass" if value else "fail"))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
