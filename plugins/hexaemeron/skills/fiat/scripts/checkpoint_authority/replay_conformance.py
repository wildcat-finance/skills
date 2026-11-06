"""Source-bound evidence for complete authority replay and the Ariadne evidence gates."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

from . import conformance as owner, native_io as io
from .canonical import Refusal as ReplayRefusal

CRITERION = "authority-replay"
MANIFEST = owner.CORPUS_ROOT + "fixtures/replay-manifest.json"
HISTORY = owner.CORPUS_ROOT + "fixtures/replay-history.json"
HOSTILE = owner.CORPUS_ROOT + "fixtures/replay-hostile.json"
BUDGET = owner.CORPUS_ROOT + "fixtures/replay-budget.json"
ARIADNE_MODULE = "checkpoint_ariadne_cases"
ARIADNE_FIXTURES = (
    "pass-checkpoint-authority-acceptance.json", "pass-checkpoint-authority-head.json",
    "fail-gate2-checkpoint-authority-calendar-instant.json",
    "fail-gate5-checkpoint-authority-orphan-predecessor.json",
    "fail-check-predicate-fields-checkpoint-authority-unknown-field.json",
    "fail-check-subject-roles-checkpoint-authority-swapped-roles.json",
    "fail-check-evidence-references-checkpoint-authority-identity-as-evidence.json",
    "fail-check-required-coverage-checkpoint-authority-copy-length.json",
)
FILES = (HISTORY, HOSTILE, BUDGET,
    "plugins/ariadne/schemas/checkpoint-authority-v1.json",
    "plugins/ariadne/tests/fixtures/checkpoint-authority-acceptance.json",
    *("plugins/ariadne/tests/fixtures/conformance/" + name for name in ARIADNE_FIXTURES))
MAX_FILE_BYTES = 1024 * 1024
SOURCES = tuple("plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/" + name + ".py"
    for name in ("canonical", "schema", "records", "signatures", "trust", "eligibility", "parents",
                 "replay", "wire", "replay_conformance", "conformance")) + (
    "plugins/hexaemeron/tests/checkpoint_authority_conformance.py",
    "plugins/hexaemeron/tests/checkpoint_authority_replay_fixture.py",
    "plugins/hexaemeron/tests/checkpoint_authority_replay_suite.py",
    "plugins/hexaemeron/tests/checkpoint_authority_replay_corpus.py",
    "plugins/hexaemeron/tests/checkpoint_authority_replay_budget.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_records.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_replay.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_replay_conformance.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_ariadne.py",
    "plugins/ariadne/scripts/ariadne_lib/predicates/checkpoint_authority.py",
    "plugins/ariadne/scripts/ariadne_lib/verify.py",
    "plugins/ariadne/tests/test_checkpoint_authority.py", ".python-version")
CASE = re.compile(r"(?:test_checkpoint_authority_replay(?:_conformance)?\.[A-Za-z]+|" + ARIADNE_MODULE
                  + r"\.[A-Za-z]+)\.test_[a-z0-9_]+\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")


def _hash(root, path):
    try:
        return io.hash_file(root / path, MAX_FILE_BYTES)[0]
    except ReplayRefusal:
        raise owner.Refusal("replay-fixture-unavailable") from None


def inputs(root):
    payload = owner._read(root, MANIFEST)
    try: value = json.loads(payload, object_pairs_hook=owner._unique_object)
    except (ValueError, UnicodeError): raise owner.Refusal("replay-manifest") from None
    if (type(value) is not dict or set(value) != {"schema", "criterion", "cases", "files"}
        or value["schema"] != "checkpoint-authority-replay-corpus/v1" or value["criterion"] != CRITERION
        or type(value["cases"]) is not list or not 1 <= len(value["cases"]) <= 100
        or any(type(case) is not str or CASE.fullmatch(case) is None for case in value["cases"])
        or value["cases"] != sorted(set(value["cases"]))
        or not any(case.startswith(ARIADNE_MODULE + ".") for case in value["cases"])
        or type(value["files"]) is not list or len(value["files"]) != len(FILES)):
        raise owner.Refusal("replay-manifest")
    for row, path in zip(value["files"], FILES):
        if (type(row) is not dict or set(row) != {"path", "sha256"} or row["path"] != path
            or row["sha256"] != _hash(root, path)):
            raise owner.Refusal("replay-fixture-drift")
    return {"cases": value["cases"],
        "source": [{"path": path, "sha256": hashlib.sha256(owner._read(root, path)).hexdigest()} for path in SOURCES],
        "fixture_manifest": {"path": MANIFEST, "sha256": hashlib.sha256(payload).hexdigest()}}


def expected_history(root):
    try:
        with io.regular(root / HISTORY, MAX_FILE_BYTES) as (descriptor, size, check):
            data = os.read(descriptor, MAX_FILE_BYTES + 1)
            check()
        if len(data) != size:
            raise owner.Refusal("replay-fixture-unavailable")
        history = json.loads(data, object_pairs_hook=owner._unique_object)
        hostile = json.loads(owner._read(root, HOSTILE), object_pairs_hook=owner._unique_object)
    except (ReplayRefusal, OSError, ValueError, UnicodeError):
        raise owner.Refusal("replay-fixture-unavailable") from None
    if (type(history) is not dict or history.get("schema") != "checkpoint-authority-replay-history/v1"
        or type(history.get("expected")) is not dict or type(hostile) is not dict
        or hostile.get("schema") != "checkpoint-authority-replay-hostile/v1" or type(hostile.get("cases")) is not list):
        raise owner.Refusal("replay-fixture-unavailable")
    return history["expected"], len(hostile["cases"])


def execute(root):
    python = Path(sys.executable).resolve(strict=True)
    tool = io.NativeTool("python", str(python), io.hash_file(python, 268435456)[0])
    try:
        result = io.execute(tool, [str(root / "plugins/hexaemeron/tests/checkpoint_authority_replay_suite.py")],
            root, dict(os.environ), stage=CRITERION, attempt_id="replay-conformance",
            input_sha256=hashlib.sha256(owner._read(root, MANIFEST)).hexdigest(), deadline=time.monotonic() + 1800)
        value = json.loads(result.stdout, object_pairs_hook=owner._unique_object)
    except (ReplayRefusal, ValueError, UnicodeError):
        raise owner.Refusal("replay-execution-unavailable") from None
    counters = ("tests_run", "subtests_run", "failures", "errors", "skips", "expected_failures", "unexpected_successes")
    fields = {"schema", "complete", "passed", "started", "completed", "failure_cases", "error_cases", "output_sha256", "replay", "python", *counters}
    if (type(value) is not dict or set(value) != fields or value["schema"] != "checkpoint-authority-replay-execution/v1"
        or any(type(value[key]) is not bool for key in ("complete", "passed"))
        or any(type(value[key]) is not int or not 0 <= value[key] <= 1000000 for key in counters)
        or type(value["output_sha256"]) is not str or HEX.fullmatch(value["output_sha256"]) is None
        or value["python"] != owner._read(root, ".python-version").decode().strip()):
        raise owner.Refusal("replay-execution-report")
    for field in ("started", "completed", "failure_cases", "error_cases"):
        if (type(value[field]) is not list or len(value[field]) > 100
            or any(type(case) is not str or CASE.fullmatch(case) is None for case in value[field])
            or len(set(value[field])) != len(value[field])):
            raise owner.Refusal("replay-execution-report")
    for field, counter in (("failure_cases", "failures"), ("error_cases", "errors")):
        if bool(value[field]) != bool(value[counter]) or not set(value[field]) <= set(value["started"]):
            raise owner.Refusal("replay-execution-report")
    replay = value["replay"]
    if replay is not None:
        expected, hostile_count = expected_history(root)
        keys = {"history_sha256", "records", "bytes", "head_sha256", "policy_history", "decisions", "accepted",
                "historical_permits", "hostile_refused", "current_eligibility", "ariadne_cases"}
        if (type(replay) is not dict or set(replay) != keys
            or replay["history_sha256"] != _hash(root, HISTORY)
            or any(replay[key] != expected[key] for key in ("records", "bytes", "head_sha256", "policy_history", "decisions", "accepted", "historical_permits"))
            or replay["hostile_refused"] != hostile_count or hostile_count < 1
            or replay["current_eligibility"] != ["eligible"] * len(expected["accepted"])
            or replay["ariadne_cases"] != sum(case.startswith(ARIADNE_MODULE + ".") for case in value["completed"])
            or replay["ariadne_cases"] < 1):
            raise owner.Refusal("replay-execution-report")
    return value, result.exit, hashlib.sha256(result.stdout).hexdigest(), hashlib.sha256(result.stderr).hexdigest()


def run(root, report):
    before = inputs(root)
    execution, runner_exit, stdout_hash, stderr_hash = execute(root)
    passed = (runner_exit == 0 and execution["complete"] is True and execution["passed"] is True
        and execution["replay"] is not None and sorted(execution["started"]) == before["cases"]
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
