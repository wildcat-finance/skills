"""Source-bound evidence for actual native execution and hostile boundary cases."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

from . import conformance as owner, native_io as io
from .canonical import Refusal as NativeRefusal

CRITERION = "native-boundary-coverage"
MANIFEST = owner.CORPUS_ROOT + "native-manifest.json"
FILES = tuple(owner.CORPUS_ROOT + name for name in (
    "native-capabilities.json", "native-fixture/checkpoint.zip", "native-fixture/fixture.json",
    "native-fixture/independent-public-key.gpg", "native-profile.json"))
SOURCES = tuple("plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/" + name + ".py"
    for name in ("canonical", "schema", "records", "signatures", "native_io", "native_records",
                 "coverage", "native", "native_conformance", "conformance")) + (
    "plugins/hexaemeron/tests/checkpoint_authority_conformance.py",
    "plugins/hexaemeron/tests/checkpoint_authority_native_fixture.py",
    "plugins/hexaemeron/tests/checkpoint_authority_native_probe.py",
    "plugins/hexaemeron/tests/checkpoint_authority_native_suite.py",
    "plugins/hexaemeron/tests/checkpoint_authority_native_corpus.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_native.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_native_conformance.py", ".python-version")
CASE = re.compile(r"(?:test_checkpoint_authority_native(?:_conformance)?\.[A-Za-z]+|native_integration|test_hexctl_checkpoint_archive\.CheckpointArchiveInspectTests)\.test_[a-z0-9_]+\Z")


def inputs(root):
    payload = owner._read(root, MANIFEST)
    try: value = json.loads(payload, object_pairs_hook=owner._unique_object)
    except (ValueError, UnicodeError): raise owner.Refusal("native-manifest") from None
    if (type(value) is not dict or set(value) != {"schema", "criterion", "cases", "files"}
        or value["schema"] != "checkpoint-authority-native-corpus/v1" or value["criterion"] != CRITERION
        or type(value["cases"]) is not list or not 1 <= len(value["cases"]) <= 100
        or any(type(case) is not str or CASE.fullmatch(case) is None for case in value["cases"])
        or value["cases"] != sorted(set(value["cases"]))
        or type(value["files"]) is not list or len(value["files"]) != len(FILES)):
        raise owner.Refusal("native-manifest")
    for row, path in zip(value["files"], FILES):
        if (type(row) is not dict or set(row) != {"path", "sha256"} or row["path"] != path
            or row["sha256"] != hashlib.sha256(owner._read(root, path)).hexdigest()):
            raise owner.Refusal("native-fixture-drift")
    return {"cases": value["cases"],
        "source": [{"path": path, "sha256": hashlib.sha256(owner._read(root, path)).hexdigest()} for path in SOURCES],
        "fixture_manifest": {"path": MANIFEST, "sha256": hashlib.sha256(payload).hexdigest()}}


def execute(root):
    python = Path(sys.executable).resolve(strict=True)
    tool = io.NativeTool("python", str(python), io.hash_file(python, 268435456)[0])
    try:
        result = io.execute(tool, [str(root / "plugins/hexaemeron/tests/checkpoint_authority_native_suite.py")],
            root, dict(os.environ), stage=CRITERION, attempt_id="native-conformance",
            input_sha256=hashlib.sha256(owner._read(root, MANIFEST)).hexdigest(), deadline=time.monotonic() + 1800)
        value = json.loads(result.stdout, object_pairs_hook=owner._unique_object)
    except (NativeRefusal, ValueError, UnicodeError):
        raise owner.Refusal("native-execution-unavailable") from None
    counters = ("tests_run", "subtests_run", "failures", "errors", "skips", "expected_failures", "unexpected_successes")
    fields = {"schema", "complete", "passed", "started", "completed", "failure_cases", "error_cases", "output_sha256", "native", "python", *counters}
    if (type(value) is not dict or set(value) != fields or value["schema"] != "checkpoint-authority-native-execution/v1"
        or any(type(value[key]) is not bool for key in ("complete", "passed"))
        or any(type(value[key]) is not int or not 0 <= value[key] <= 1000000 for key in counters)
        or type(value["output_sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", value["output_sha256"]) is None
        or value["python"] != owner._read(root, ".python-version").decode().strip()):
        raise owner.Refusal("native-execution-report")
    for field in ("started", "completed", "failure_cases", "error_cases"):
        if (type(value[field]) is not list or len(value[field]) > 100
            or any(type(case) is not str or CASE.fullmatch(case) is None for case in value[field])
            or len(set(value[field])) != len(value[field])):
            raise owner.Refusal("native-execution-report")
    for field, counter in (("failure_cases", "failures"), ("error_cases", "errors")):
        if bool(value[field]) != bool(value[counter]) or not set(value[field]) <= set(value["started"]):
            raise owner.Refusal("native-execution-report")
    native = value["native"]
    if native is not None:
        if (type(native) is not dict or set(native) != {"result_sha256", "source_profile_sha256", "source_commit", "native_results", "required", "historical_required", "verified_count", "capability_sha256"}
            or type(native["native_results"]) is not list or len(native["native_results"]) != 4):
            raise owner.Refusal("native-execution-report")
        from .native import LAYOUT_SHA256
        from .native_records import NATIVE_COMMIT
        if (native["source_commit"] != NATIVE_COMMIT or native["source_profile_sha256"] != LAYOUT_SHA256
            or native["capability_sha256"] != hashlib.sha256(owner._read(root, FILES[0])).hexdigest()
            or type(native["result_sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", native["result_sha256"]) is None):
            raise owner.Refusal("native-execution-report")
        for stage, row in zip(("inspect", "restore", "verify", "identity"), native["native_results"]):
            if (type(row) is not dict or set(row) != {"stage", "attempt_id", "input_sha256", "exit", "output_sha256", "log_sha256", "output_bytes", "log_bytes", "duration_ms"}
                or row.get("stage") != stage or row.get("exit") != 0
                or type(row.get("exit")) is not int or row.get("attempt_id") != "native-positive"):
                raise owner.Refusal("native-execution-report")
            for key in ("input_sha256", "output_sha256", "log_sha256"):
                if type(row[key]) is not str or re.fullmatch(r"[0-9a-f]{64}", row[key]) is None:
                    raise owner.Refusal("native-execution-report")
            for key, maximum in (("output_bytes", 65536), ("log_bytes", 16384), ("duration_ms", 900000)):
                if type(row[key]) is not int or not 0 <= row[key] <= maximum:
                    raise owner.Refusal("native-execution-report")
        fixture = json.loads(owner._read(root, owner.CORPUS_ROOT + "native-fixture/fixture.json"))
        if (native["required"] != sorted(fixture["required"]) or native["historical_required"] != sorted(fixture["historical_required"])
            or type(native["verified_count"]) is not int or native["verified_count"] != len(fixture["required"])
            or any(row.get("input_sha256") != fixture["outer_sha256"] for row in native["native_results"])):
            raise owner.Refusal("native-execution-report")
    return value, result.exit, hashlib.sha256(result.stdout).hexdigest(), hashlib.sha256(result.stderr).hexdigest()


def run(root, report):
    before = inputs(root)
    execution, runner_exit, stdout_hash, stderr_hash = execute(root)
    passed = (runner_exit == 0 and execution["complete"] is True and execution["passed"] is True
        and execution["native"] is not None and sorted(execution["started"]) == before["cases"]
        and execution["started"] == execution["completed"] and execution["tests_run"] == len(before["cases"])
        and all(execution[key] == 0 for key in ("failures", "errors", "skips", "expected_failures", "unexpected_successes")))
    if inputs(root) != before: raise owner.Refusal("source-changed")
    report.update(value=passed, exit=0 if passed else 1)
    return {"schema": "checkpoint-authority-conformance-evidence/v1",
        "event": "checkpoint_authority_conformance_complete" if passed else "checkpoint_authority_conformance_refused",
        "stage": CRITERION, "code": "cases-passed" if passed else "cases-failed",
        "status": "passed" if passed else "failed", "candidate": owner.CANDIDATE,
        "criterion": CRITERION, "complete": passed, "exit": report["exit"],
        "source": before["source"], "fixture_manifest": before["fixture_manifest"],
        "executed_cases": execution["completed"],
        "execution": {key: value for key, value in execution.items() if key not in ("started", "completed")},
        "runner_exit": runner_exit, "stdout_sha256": stdout_hash, "stderr_sha256": stderr_hash,
        "design_report_sha256": hashlib.sha256(owner._json_bytes(report)).hexdigest()}
