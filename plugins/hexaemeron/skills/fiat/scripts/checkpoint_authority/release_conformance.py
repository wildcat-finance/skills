"""Source-bound evidence for released interoperability: the corpus, the demonstration and its limits."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import statistics
import time

from . import conformance as owner, demo, native_io as io, network, release
from .canonical import Refusal as ReleaseRefusal

CRITERION = "released-interoperability"
WORKLOAD = demo.BUNDLE + "study-workload.json"
WORKLOAD_METADATA = demo.BUNDLE + "study-workload-metadata.json"
STUDY_SHA = "cf56704482a20f2d7d7d03d26c1eed8f54d9bf9d5d2d45bb64c18c1d3e8474ae"
PROJECTION_SHA = "3e51e417e044849260c320091812df58257cdf79ce112470e16eca2c3e2e54f8"
MANIFEST = demo.BUNDLE + "interoperability-manifest.json"
MODULES = ("test_checkpoint_authority_release", "test_checkpoint_authority_release_conformance",
           "test_checkpoint_network")
BUNDLE_FILES = (demo.HISTORY, demo.BOOTSTRAP, demo.NATIVE, demo.FRESHNESS, demo.PRESENCE,
                demo.EXPECTED, demo.HOSTILE)
SIGNATURE_FILES = (demo.COSIGN_ENVELOPE, demo.COSIGN_DOUBLE, demo.COSIGN_BLOB,
                   demo.TRUSTED_KEY, demo.WRONG_KEY)
FILES = tuple(sorted((*BUNDLE_FILES, *SIGNATURE_FILES, WORKLOAD, WORKLOAD_METADATA,
                      release.CORPUS + "fixtures/replay-history.json",
                      release.CORPUS + "fixtures/replay-budget.json",
                      release.DOCS + "release.md")))
"""The consumer lock is absent by construction: it is derived from the manifest this binds."""
MAX_FILE_BYTES = 1024 * 1024
SOURCES = tuple("plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/" + name + ".py"
                for name in ("canonical", "schema", "signatures", "network", "network_policy", "trust", "replay", "verifier",
                             "release", "demo", "release_conformance", "conformance")) + (
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority.py",
    "plugins/hexaemeron/tests/checkpoint_authority_conformance.py",
    "plugins/hexaemeron/tests/checkpoint_authority_release_corpus.py",
    "plugins/hexaemeron/tests/checkpoint_authority_release_suite.py",
    "plugins/hexaemeron/tests/checkpoint_network_design_report.py",
    "plugins/hexaemeron/tests/checkpoint_authority_release_workload.py",
    "plugins/hexaemeron/tests/checkpoint_authority_replay_fixture.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_records.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_release.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_release_conformance.py",
    "plugins/hexaemeron/tests/test_checkpoint_network.py",
    "plugins/hexaemeron/tests/test_checkpoint_network_reports.py",
    ".python-version")
CASE = re.compile(r"(?:" + "|".join(MODULES) + r")\.[A-Za-z]+\.test_[a-z0-9_]+\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
DEMONSTRATION_KEYS = ("manifest_sha256", "reproducible_rebuilds", "history_sha256", "head_sha256",
                      "records", "accepted", "eligible", "hostile_refused", "interoperability_cases",
                      "network_boundary", "current_eligibility_withheld", "wall_ms", "json_decodes",
                      "tracemalloc_peak_bytes", "peak_rss_bytes")


def _hash(root, path):
    try:
        return io.hash_file(root / path, release.FILE_MAX if path == WORKLOAD else MAX_FILE_BYTES)[0]
    except ReleaseRefusal:
        raise owner.Refusal("release-fixture-unavailable") from None


def inputs(root):
    payload = owner._read(root, MANIFEST)
    try:
        value = json.loads(payload, object_pairs_hook=owner._unique_object)
    except (ValueError, UnicodeError):
        raise owner.Refusal("release-manifest") from None
    if (type(value) is not dict or set(value) != {"schema", "criterion", "cases", "files"}
            or value["schema"] != "checkpoint-authority-interoperability-corpus/v1"
            or value["criterion"] != CRITERION or type(value["cases"]) is not list
            or not 1 <= len(value["cases"]) <= 100
            or any(type(case) is not str or CASE.fullmatch(case) is None for case in value["cases"])
            or value["cases"] != sorted(set(value["cases"]))
            or not all(any(case.startswith(module + ".") for case in value["cases"])
                       for module in MODULES)
            or type(value["files"]) is not list or len(value["files"]) != len(FILES)):
        raise owner.Refusal("release-manifest")
    for row, path in zip(value["files"], FILES):
        if (type(row) is not dict or set(row) != {"path", "sha256"} or row["path"] != path
                or row["sha256"] != _hash(root, path)):
            raise owner.Refusal("release-fixture-drift")
    return {"cases": value["cases"],
            "source": [{"path": path, "sha256": hashlib.sha256(owner._read(root, path)).hexdigest()}
                       for path in SOURCES],
            "release_manifest": {"path": release.MANIFEST,
                                 "sha256": _hash(root, release.MANIFEST)},
            "fixture_manifest": {"path": MANIFEST,
                                 "sha256": hashlib.sha256(payload).hexdigest()}}


def execute(root):
    boundary = network.prepare()
    expected_boundary = boundary.expected()
    python = Path(sys.executable).resolve(strict=True)
    tool = io.NativeTool("python", str(python), io.hash_file(python, 268435456)[0])
    try:
        result = io.execute(tool, [str(root / "plugins/hexaemeron/tests/checkpoint_authority_release_suite.py")],
                            root, dict(os.environ), stage=CRITERION, attempt_id="release-conformance",
                            input_sha256=hashlib.sha256(owner._read(root, MANIFEST)).hexdigest(),
                            deadline=time.monotonic() + 1800)
        value = json.loads(result.stdout, object_pairs_hook=owner._unique_object)
    except (ReleaseRefusal, ValueError, UnicodeError):
        raise owner.Refusal("release-execution-unavailable") from None
    _validate(value, root, expected_boundary)
    if network.prepare().expected() != expected_boundary:
        raise owner.Refusal("release-network-changed")
    return value, result.exit, hashlib.sha256(result.stdout).hexdigest(), hashlib.sha256(result.stderr).hexdigest()


def _validate(value, root, expected_boundary):
    counters = ("tests_run", "subtests_run", "failures", "errors", "skips", "expected_failures",
                "unexpected_successes")
    fields = {"schema", "complete", "passed", "started", "completed", "failure_cases", "error_cases",
              "output_sha256", "demonstration", "workload", "python", *counters}
    if (type(value) is not dict or set(value) != fields
            or value["schema"] != "checkpoint-authority-release-execution/v1"
            or any(type(value[key]) is not bool for key in ("complete", "passed"))
            or any(type(value[key]) is not int or not 0 <= value[key] <= 1000000 for key in counters)
            or type(value["output_sha256"]) is not str or HEX.fullmatch(value["output_sha256"]) is None
            or value["python"] != owner._read(root, ".python-version").decode().strip()):
        raise owner.Refusal("release-execution-report")
    for field in ("started", "completed", "failure_cases", "error_cases"):
        if (type(value[field]) is not list or len(value[field]) > 100
                or any(type(case) is not str or CASE.fullmatch(case) is None for case in value[field])
                or len(set(value[field])) != len(value[field])):
            raise owner.Refusal("release-execution-report")
    for field, counter in (("failure_cases", "failures"), ("error_cases", "errors")):
        if bool(value[field]) != bool(value[counter]) or not set(value[field]) <= set(value["started"]):
            raise owner.Refusal("release-execution-report")
    if value["workload"] is not None:
        _validate_workload(value["workload"], root)
    demonstration = value["demonstration"]
    if demonstration is None:
        return
    if (type(demonstration) is not dict or set(demonstration) != set(DEMONSTRATION_KEYS)
            or demonstration["manifest_sha256"] != _hash(root, release.MANIFEST)
            or demonstration["reproducible_rebuilds"] != 2
            or any(type(demonstration[key]) is not int or demonstration[key] < 1 for key in
                   ("records", "accepted", "eligible", "hostile_refused", "interoperability_cases"))
            or demonstration["current_eligibility_withheld"] is not True
            or any(HEX.fullmatch(demonstration[key]) is None for key in
                   ("manifest_sha256", "history_sha256", "head_sha256"))
            or type(demonstration["wall_ms"]) not in (int, float) or demonstration["wall_ms"] < 0
            or any(type(demonstration[key]) is not int or demonstration[key] < 1 for key in
                   ("json_decodes", "tracemalloc_peak_bytes", "peak_rss_bytes"))
            or demonstration["peak_rss_bytes"] >= release.RESOURCE_LIMITS["declared_peak_rss_ceiling_bytes"]):
        raise owner.Refusal("release-execution-report")
    expected = json.loads(owner._read(root, demo.EXPECTED), object_pairs_hook=owner._unique_object)
    if any(demonstration[key] != expected[key] for key in ("history_sha256", "head_sha256", "records")):
        raise owner.Refusal("release-execution-report")
    try:
        network.validate_observation(demonstration["network_boundary"], expected_boundary)
    except ReleaseRefusal:
        raise owner.Refusal("release-execution-report") from None


def _validate_workload(value, root):
    """Admit exact study correspondence and observations from all three fresh processes."""
    try:
        expected = json.loads(owner._read(root, WORKLOAD_METADATA), object_pairs_hook=owner._unique_object)
    except (ValueError, UnicodeError):
        raise owner.Refusal("release-execution-report") from None
    hashes = ("workload_sha256", "study_corpus_sha256", "projection_sha256")
    numbers = ("model_events", "model_decisions", "records", "bytes", "accepted", "denied",
               "cancelled", "historical_permits")
    if (type(expected) is not dict or set(expected) != {"schema", *hashes, *numbers}
            or expected["schema"] != "checkpoint-authority-study-workload-metadata/v1"
            or any(type(expected[key]) is not str or HEX.fullmatch(expected[key]) is None for key in hashes)
            or any(type(expected[key]) is not int or expected[key] <= 0 for key in numbers)
            or expected["records"] > release.RESOURCE_LIMITS["history_entries"]
            or expected["bytes"] > release.RESOURCE_LIMITS["history_bytes"]):
        raise owner.Refusal("release-execution-report")
    fixed = {key: val for key, val in expected.items() if key != "schema"}
    fields = {*fixed, "schema", "decodes", "journal_body_decodes", "json_decodes_total",
              "retained_body_nodes", "samples", "repetitions",
              "wall_ms_median", "wall_ms_p95", "percentile_method", "warmup_repetitions", "environment"}
    if (type(value) is not dict or set(value) != fields
            or value["schema"] != "checkpoint-authority-release-workload-measurement/v1"
            or any(type(value[key]) is not type(val) or value[key] != val for key, val in fixed.items())
            or fixed["workload_sha256"] != _hash(root, WORKLOAD)
            or fixed["study_corpus_sha256"] != STUDY_SHA or fixed["projection_sha256"] != PROJECTION_SHA
            or fixed["model_events"] != 1280 or fixed["model_decisions"] != 512
            or any(fixed[key] != 256 for key in ("accepted", "denied", "cancelled", "historical_permits"))
            or type(value["retained_body_nodes"]) is not int or value["retained_body_nodes"] != 0
            or type(value["repetitions"]) is not int or value["repetitions"] != 3
            or type(value["warmup_repetitions"]) is not int or value["warmup_repetitions"] != 0
            or value["percentile_method"] != "nearest-rank"):
        raise owner.Refusal("release-execution-report")
    counts = value["decodes"]
    if (type(counts) is not dict or set(counts) != {"carrier", "signed_statement", "additional_record_body",
                                                 "native_result", "producer_ledger_line", "other"}
            or any(type(count) is not int or count < 0 for count in counts.values())
            or counts["carrier"] != fixed["records"] or counts["signed_statement"] != fixed["records"]
            or type(value["journal_body_decodes"]) is not int or value["journal_body_decodes"] != fixed["records"]
            or value["journal_body_decodes"] != counts["signed_statement"] + counts["additional_record_body"]
            or type(value["json_decodes_total"]) is not int or value["json_decodes_total"] != sum(counts.values())):
        raise owner.Refusal("release-execution-report")
    samples = value["samples"]
    if type(samples) is not list or len(samples) != 3:
        raise owner.Refusal("release-execution-report")
    for row in samples:
        if (type(row) is not dict or set(row) != {"wall_ms", "tracemalloc_peak_bytes", "peak_rss_bytes"}
                or type(row["wall_ms"]) not in (int, float) or not math.isfinite(row["wall_ms"]) or row["wall_ms"] <= 0
                or any(type(row[key]) is not int or row[key] <= 0 for key in ("tracemalloc_peak_bytes", "peak_rss_bytes"))
                or row["peak_rss_bytes"] >= release.RESOURCE_LIMITS["declared_peak_rss_ceiling_bytes"]):
            raise owner.Refusal("release-execution-report")
    walls = [row["wall_ms"] for row in samples]
    if (type(value["wall_ms_median"]) not in (int, float) or value["wall_ms_median"] != statistics.median(walls)
            or type(value["wall_ms_p95"]) not in (int, float) or value["wall_ms_p95"] != max(walls)):
        raise owner.Refusal("release-execution-report")
    env = value["environment"]
    if (type(env) is not dict or set(env) != {"python", "platform", "machine", "processor", "logical_cpus", "measurement", "contention"}
            or any(type(env[key]) is not str or not 1 <= len(env[key]) <= 256 for key in env if key != "logical_cpus")
            or env["python"] != owner._read(root, ".python-version").decode().strip()
            or type(env["logical_cpus"]) is not int or not 1 <= env["logical_cpus"] <= 4096
            or env["measurement"] != "fresh-process-per-repetition"):
        raise owner.Refusal("release-execution-report")


def run(root, report):
    before = inputs(root)
    execution, runner_exit, stdout_hash, stderr_hash = execute(root)
    passed = (runner_exit == 0 and execution["complete"] is True and execution["passed"] is True
              and execution["demonstration"] is not None and execution["workload"] is not None
              and sorted(execution["started"]) == before["cases"]
              and execution["started"] == execution["completed"]
              and execution["tests_run"] == len(before["cases"])
              and all(execution[key] == 0 for key in
                      ("failures", "errors", "skips", "expected_failures", "unexpected_successes")))
    if inputs(root) != before:
        raise owner.Refusal("source-changed")
    report.update(value=passed, exit=0 if passed else 1)
    return {"schema": "checkpoint-authority-conformance-evidence/v1",
            "event": "checkpoint_authority_conformance_complete" if passed
                     else "checkpoint_authority_conformance_refused",
            "stage": CRITERION, "code": "cases-passed" if passed else "cases-failed",
            "status": "passed" if passed else "failed", "candidate": owner.CANDIDATE,
            "criterion": CRITERION, "complete": passed, "exit": report["exit"],
            "source": before["source"], "fixture_manifest": before["fixture_manifest"],
            "release_manifest": before["release_manifest"],
            "executed_cases": execution["completed"],
            "execution": {key: value for key, value in execution.items()
                          if key not in ("started", "completed")},
            "runner_exit": runner_exit, "stdout_sha256": stdout_hash, "stderr_sha256": stderr_hash,
            "boundary": "One machine, one committed synthetic history and one pinned independent "
                        "verifier. No production issuer root, cloud retention, live storage "
                        "independence, service runtime enforcement, latency or throughput follows.",
            "design_report_sha256": hashlib.sha256(owner._json_bytes(report)).hexdigest()}
