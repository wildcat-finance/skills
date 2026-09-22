#!/usr/bin/env python3
"""Resolve the selected checkpoint scanner's declared conformance operations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
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
import zipfile
from contextlib import contextmanager


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from plugins.hexaemeron.tests import test_checkpoint_marker_scan as guards
from tests.emit_run_observation_report import report_target, result_payload, write_report


BASELINE_COMMIT = "e2307ed5966e18727434b3e49bec89db736f7b17"
CONTROLLER_PATH = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
SCRIPT_PATH = "plugins/hexaemeron/tests/prove_checkpoint_marker_scan.py"
TEST_DIRECTORY = ROOT / "plugins/hexaemeron/tests"
sys.path.insert(0, str(TEST_DIRECTORY))

from test_hexctl_checkpoint_archive import SignedRunFixture
from test_checkpoint_signing_formats import SshSignedRunFixture


def support_module(name, relative):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    if specification is None or specification.loader is None:
        raise ImportError("checkpoint demonstration support unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@contextmanager
def signed_fixture(fixture_type):
    fixture = fixture_type(methodName="runTest")
    setup = False
    try:
        fixture_type.setUpClass()
        fixture.setUp()
        setup = True
        fixture.to_post_push()
        yield fixture
    finally:
        if setup:
            fixture.tearDown()
        fixture.doCleanups()
        fixture_type.tearDownClass()
        fixture_type.doClassCleanups()


def native_negative_cases():
    """Select native boundary probes from the separately checked scanner corpus."""
    positive, _ = guards.material_corpus()
    chosen = (
        "PRIVATE KEY/line feed, raw/complete", "RSA PRIVATE KEY/line feed, raw/no-footer",
        "EC PRIVATE KEY/line feed, raw/truncated", "DSA PRIVATE KEY/line feed, raw/complete",
        "ENCRYPTED PRIVATE KEY/line feed, raw/complete", "OPENSSH PRIVATE KEY/line feed, raw/complete",
        "PGP PRIVATE KEY BLOCK/line feed, raw/complete",
        "RSA PRIVATE KEY/numeric-uppercase-crlf/no-footer",
        "rewrapped-1/line feed, raw/no-footer", "rewrapped-8/line feed, raw/complete",
        "metadata/RSA PRIVATE KEY/8/CRLF, raw", "metadata/PGP PRIVATE KEY BLOCK/8/CRLF, raw",
        "escaped-solidus/line feed, raw", "chunk-split-1", "repeated-headers-with-material",
        "token-0", "token-1", "token-2", "token-3",
    )
    available = dict(positive)
    missing = set(chosen) - available.keys()
    if missing:
        raise ValueError("native corpus selection differs from the scanner corpus")
    cases = [(name, available[name]) for name in chosen]
    from test_hexctl_checkpoint_archive import rsa_shaped_pem
    geometry = rsa_shaped_pem(16384).encode()
    cases.append(("stripped-16384-geometry", b"".join(geometry.splitlines())))
    cases.append(("json-carried-material", json.dumps({"specimen": available[chosen[1]].decode()}).encode()))
    return tuple(cases)


def native_archive_roundtrip():
    """Exercise only disposable signed runs; retain no payload or signing material."""
    measurement = support_module("marker_checkpoint_measure", "plugins/hexaemeron/skills/fiat/scripts/checkpoint_measure.py")
    budget_path = ROOT / "plugins/hexaemeron/skills/fiat/scripts/checkpoint-archive-budgets.json"
    budgets = json.loads(budget_path.read_bytes())["budgets"]
    source_paths = (
        CONTROLLER_PATH, SCRIPT_PATH,
        "plugins/hexaemeron/tests/test_checkpoint_marker_scan.py",
        "plugins/hexaemeron/tests/test_hexctl_checkpoint_archive.py",
        "plugins/hexaemeron/tests/test_checkpoint_signing_formats.py",
        "plugins/hexaemeron/tests/hexctl_harness.py",
        "plugins/hexaemeron/tests/fixture_tools.py",
        "plugins/hexaemeron/skills/fiat/scripts/checkpoint_measure.py",
        str(budget_path.relative_to(ROOT)),
    )
    source_digests = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in source_paths}
    observation = {
        "schema": "checkpoint-marker-native-observation/v1", "complete": False,
        "environment": {"python": platform.python_version(), "platform": platform.platform()},
        "sources": source_digests,
        "fixture_boundary": {
            "signatures": "Native Git verification with disposable OpenPGP and SSH keys.",
            "delivery": "Fixture GitHub and ref observations; pre-gate fixture lifecycle.",
            "consumer": "Native inspect and restore without producer keys or fake delivery tools.",
            "service_retry": "not-run", "directive_execution": "not-run",
        },
        "commands": [], "negative_cases": [], "roundtrips": [], "tampered_carriers": [],
        "limits": {"command_timeout_seconds": 120, "combined_output_cap_bytes": measurement.OUTPUT_CAP,
                   "budgets": budgets, "timing_samples_per_format": 1,
                   "timing_boundary": "One disposable fixture per format; no production latency or historical-baseline comparison."},
    }
    clean_environment = {key: value for key, value in os.environ.items()
                         if not key.startswith(("GIT_", "FAKE_")) and key != "GNUPGHOME"}
    clean_environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                              "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1"})

    class NativeFailure(ValueError):
        pass

    def require(condition, code):
        if not condition:
            raise NativeFailure(code)

    def command(case, worktree, args, *, environment, expected=0, timed=None):
        argv = [sys.executable, str(ROOT / CONTROLLER_PATH), "--dir", str(worktree), *args]
        if timed is not None:
            argv = ["/usr/bin/time", "-l" if sys.platform == "darwin" else "-v", "-o", str(timed), *argv]
        result = measurement.command(argv, timeout=120, env=environment)
        observation["commands"].append({
            "case": case, "operation": args[:2] if args[0] == "checkpoint" else args[:1],
            "exit": result["exit"], "failure": result["failure"], "wall_ms": result["wall_ms"],
            "stdout_bytes": len(result["stdout"].encode()), "stderr_bytes": len(result["stderr"].encode()),
            "stdout_sha256": hashlib.sha256(result["stdout"].encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result["stderr"].encode()).hexdigest(),
        })
        require(result["failure"] is None and result["exit"] == expected, "command-" + case)
        return result

    def controller_hashes(fixture):
        return dict(zip(("state_sha256", "ledger_sha256"),
                        (hashlib.sha256(value).hexdigest() for value in fixture.controller_bytes())))

    try:
        git_head = measurement.command(["git", "--no-replace-objects", "-C", str(ROOT), "rev-parse", "HEAD"], timeout=30, env=clean_environment)
        require(git_head["exit"] == 0 and git_head["failure"] is None, "source-head-unavailable")
        source_commit = git_head["stdout"].strip()
        require(len(source_commit) == 40 and all(character in "0123456789abcdef" for character in source_commit), "source-head-shape")
        git_blob = measurement.command(["git", "--no-replace-objects", "-C", str(ROOT), "show", source_commit + ":" + CONTROLLER_PATH], timeout=30, env=clean_environment)
        require(git_blob["exit"] == 0 and git_blob["failure"] is None, "source-controller-unavailable")
        require(hashlib.sha256(git_blob["stdout"].encode()).hexdigest() == source_digests[CONTROLLER_PATH], "controller-differs-from-source-commit")
        observation["controller_source"] = {"commit": source_commit, "path": CONTROLLER_PATH,
                                             "sha256": source_digests[CONTROLLER_PATH]}
        negative_cases = native_negative_cases()
        require(len(negative_cases) == 21 and len({name for name, _ in negative_cases}) == 21, "native-case-inventory")
        for signature_format, fixture_type in (("openpgp", SignedRunFixture), ("ssh", SshSignedRunFixture)):
            with signed_fixture(fixture_type) as fixture:
                environment = fixture.direct_environment()
                evidence = Path(fixture.target) / ".hexaemeron" / "marker-evidence"
                evidence.mkdir()
                public_rows = []
                for specification in (guards.AUDIT_SOURCE, guards.AUDIT_SYNOPSIS):
                    relative, count, digest = specification
                    leaf = Path(relative).name
                    (evidence / leaf).write_bytes(guards.public_fixture(specification))
                    public_rows.append({"source": relative, "leaf": leaf, "bytes": count, "sha256": digest})
                if signature_format == "openpgp":
                    for name, payload in negative_cases:
                        planted = evidence / "single-negative.bin"
                        before = controller_hashes(fixture)
                        planted.write_bytes(payload)
                        try:
                            result = command(name, fixture.target, ["checkpoint", "archive"], environment=environment, expected=1)
                            exact_refusal = result["stderr"] == "secret-shaped-member\n" and result["stdout"] == ""
                            published = list(fixture.store_root().rglob("checkpoint.zip")) + list(fixture.store_root().rglob("checkpoint.zip.sha256"))
                            after = controller_hashes(fixture)
                            observation["negative_cases"].append({
                                "case": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
                                "exit": result["exit"], "refusal": "secret-shaped-member" if exact_refusal else "unexpected",
                                "published_files": len(published), "before": before, "after": after,
                                "only_planted_member": sorted(path.name for path in evidence.iterdir()) == sorted([row["leaf"] for row in public_rows] + [planted.name]),
                            })
                            require(exact_refusal and not published and before == after, "negative-" + name)
                            require(observation["negative_cases"][-1]["only_planted_member"], "negative-isolation")
                        finally:
                            planted.unlink()
                before = controller_hashes(fixture)
                next_before = json.loads(command(signature_format + "-source-next", fixture.target, ["next"], environment=environment)["stdout"])
                rss_file = Path(fixture.dir) / "producer-time.txt"
                export_result = command(signature_format + "-archive", fixture.target, ["checkpoint", "archive"], environment=environment, timed=rss_file)
                exported = json.loads(export_result["stdout"])
                archive = Path(exported["archive"])
                require(controller_hashes(fixture) == before, "producer-controller-drift")
                require(hashlib.sha256(archive.read_bytes()).hexdigest() == exported["outer_sha256"], "outer-digest")
                with zipfile.ZipFile(archive) as container:
                    expanded = sum(info.file_size for info in container.infolist())
                    proof = json.loads(container.read("proof/signatures.json"))
                    manifest = json.loads(container.read("checkpoint.json"))
                require(proof["signer"]["format"] == signature_format and proof["commits"], "signature-proof")
                require(all(row["status"] == "G" for row in proof["commits"]), "producer-signatures")
                keys = Path(fixture_type.key_root)
                hidden_keys = keys.with_name(keys.name + "-hidden")
                keys.rename(hidden_keys)
                try:
                    inspection = command(signature_format + "-inspect", fixture.target, ["checkpoint", "inspect", "--archive", str(archive), "--sha256", exported["outer_sha256"]], environment=clean_environment)
                    inspected = json.loads(inspection["stdout"])
                    require(not inspected["findings"] and len(inspected["signatures"]) == len(proof["commits"]), "inspection-signature-count")
                    require(all(row["status"] == "G" and row["fingerprint"] == fixture_type.fingerprint for row in inspected["signatures"]), "native-signatures")
                    destination = Path(fixture.dir) / "restored"
                    require(not destination.exists(), "restore-destination")
                    restoration = command(signature_format + "-restore", destination, ["checkpoint", "restore", "--archive", str(archive), "--sha256", exported["outer_sha256"]], environment=clean_environment)
                    restored = json.loads(restoration["stdout"])
                    require(restored["verify"] == "ok", "restore-verification")
                    worktree = Path(restored["restore"]["worktree"])
                    restored_controller = worktree / ".hexaemeron"
                    stable_before = {name: hashlib.sha256((restored_controller / name).read_bytes()).hexdigest() for name in ("state.json", "ledger.jsonl")}
                    command(signature_format + "-verify", worktree, ["verify"], environment=clean_environment)
                    status = json.loads(command(signature_format + "-status", worktree, ["status", "--json"], environment=clean_environment)["stdout"])
                    next_after = json.loads(command(signature_format + "-next", worktree, ["next"], environment=clean_environment)["stdout"])
                    stable_after = {name: hashlib.sha256((restored_controller / name).read_bytes()).hexdigest() for name in stable_before}
                    semantic = exported["next"]
                    require(semantic == restored["next"] == manifest["boundary"]["next"], "restored-semantic-next")
                    require(all(next_before.get(key) == value == next_after.get(key) for key, value in semantic.items()), "cli-semantic-next")
                    require(stable_before == stable_after, "inspection-mutated-controller")
                    require(status["phase"] == fixture.state()["phase"] and status["current_step"] == fixture.state()["current_step"], "restored-phase")
                    for row in public_rows:
                        data = (restored_controller / "marker-evidence" / row["leaf"]).read_bytes()
                        require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"], "restored-public-digest")
                        row["restored_sha256"] = hashlib.sha256(data).hexdigest()
                    measurements = measurement.saved_measurements(exported, rss_file.read_text(), system=sys.platform,
                        inspect_ms=inspection["wall_ms"], restore_ms=restoration["wall_ms"], expanded_bytes=expanded)
                    require(all(measurements[row["name"]] <= row["limit"] for row in budgets), "native-budget")
                    observation["roundtrips"].append({
                        "signature_format": signature_format, "verified_signatures": len(inspected["signatures"]),
                        "public_files": public_rows, "outer_sha256": exported["outer_sha256"],
                        "manifest_sha256": exported["manifest_sha256"], "bundle_sha256": exported["bundle_sha256"],
                        "snapshot_id": exported["snapshot_id"], "snapshot_id_matches": restored["snapshot_id"] == exported["snapshot_id"],
                        "semantic_next_sha256": hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                        "next_action": semantic["do"], "next_step": semantic.get("step"), "next_matches": True,
                        "producer_controller": before, "restored_before_reads": stable_before, "restored_after_reads": stable_after,
                        "measurements": measurements, "budget_pass": True, "producer_keys_unavailable": True,
                    })
                    require(restored["snapshot_id"] == exported["snapshot_id"], "snapshot-identity")
                    tampered = Path(fixture.dir) / "tampered.zip"
                    data = bytearray(archive.read_bytes())
                    data[len(data) // 2] ^= 1
                    tampered.write_bytes(data)
                    bad = command(signature_format + "-tampered-inspect", fixture.target, ["checkpoint", "inspect", "--archive", str(tampered), "--sha256", exported["outer_sha256"]], environment=clean_environment, expected=1)
                    require(bad["stderr"] == "outer-digest-mismatch\n" and bad["stdout"] == "", "tampered-refusal")
                    observation["tampered_carriers"].append({"signature_format": signature_format,
                        "exit": bad["exit"], "refusal": "outer-digest-mismatch", "changed_bytes": 1,
                        "controller_unchanged": controller_hashes(fixture) == before})
                    require(controller_hashes(fixture) == before, "tamper-controller-drift")
                finally:
                    hidden_keys.rename(keys)
        require(all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in source_digests.items()), "source-drift")
        for specification in (guards.AUDIT_SOURCE, guards.AUDIT_SYNOPSIS):
            guards.public_fixture(specification)
        observation["complete"] = True
        return True, observation
    except (AssertionError, OSError, ValueError, unittest.SkipTest) as error:
        observation["failure_type"] = type(error).__name__
        if isinstance(error, NativeFailure):
            observation["failure_code"] = str(error)
        observation["failure_sha256"] = hashlib.sha256(str(error).encode()).hexdigest()
        return False, observation


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
    suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                               for case in (guards.PublicAuditQuotationTests, guards.CheckpointMaterialTests))
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
        "native_archive_roundtrip": "not-run-by-this-operation",
    }
    return value, observed


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=("bounded-material",), required=True)
    parser.add_argument("--criterion", choices=("implementation-regression", "native-archive-roundtrip"), required=True)
    parser.add_argument("--report", required=True)
    options = parser.parse_args(argv)
    target = report_target([options.report])
    observation_name = str(Path(options.report).with_suffix(".observation.json"))
    observation_target = report_target([observation_name])
    operation = native_archive_roundtrip if options.criterion == "native-archive-roundtrip" else implementation_regression
    value, observation = operation()
    status = 0 if value else 1
    write_report(observation_target, observation)
    write_report(target, {
        "schema": "protasis-design-report/v1", "candidate": options.candidate,
        "criterion": options.criterion, "value": value, "unit": "boolean",
        "command": shlex.join(["python3", SCRIPT_PATH, *argv]), "exit": status,
    })
    print(options.criterion + ": " + ("pass" if value else "fail"))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
