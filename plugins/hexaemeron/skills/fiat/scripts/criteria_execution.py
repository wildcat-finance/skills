#!/usr/bin/env python3
"""Controller-owned execution and bounded result custody for study criteria.

The declaration and runbook adapters are deliberately inert.  This module is
the small boundary that turns one already-admitted Exit command into an
observation.  It never accepts a caller supplied verdict: a criterion settles
only from a child process which this module launched, on a clean signed
implementation commit, with the exact command and source bindings recorded in
the returned attempt.

The module is usable on its own by tests and by ``hexctl``.  All public
functions raise :class:`Refusal` rather than silently weakening a binding.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import time
import uuid


SCHEMA = "protasis-success-criteria-execution/v1"
ADMISSION_SCHEMA = "protasis-success-criteria-admission/v1"
RESULT_SCHEMA = "protasis-success-criteria-result/v1"
ATTEMPT_SCHEMA = "protasis-success-criteria-attempt/v1"
MAX_CRITERIA = 128
MAX_ATTEMPTS = 512
MAX_RESULT_BYTES = 4 * 1024 * 1024
MAX_STREAM_BYTES = 4 * 1024 * 1024
MAX_ATTEMPT_SECONDS = 1800.0
READ_CHUNK = 64 * 1024
SHA256 = __import__("re").compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class Refusal(ValueError):
    """An execution request or recorded result cannot be admitted."""


def as_dict(value) -> dict:
    """Treat optional receipt sections as empty mappings at the boundary."""
    return value if isinstance(value, dict) else {}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    except (RecursionError, TypeError, ValueError, UnicodeEncodeError) as exc:
        raise Refusal("unsupported-json-value") from exc


def _sha(value, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise Refusal(label)
    return value


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Refusal(f"{name}-unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def adapters(root: Path) -> tuple[object, object]:
    """Load the two reviewed, sibling adapters without importing a target."""
    root = Path(root).resolve(strict=True)
    base = Path(__file__).resolve().parents[2]
    criteria = _module("fiat_success_criteria_execution", base / "protasis" / "scripts" / "success_criteria.py")
    gate = _module("fiat_gate_commands_execution", base / "protasis" / "scripts" / "gate_commands.py")
    return criteria, gate


def _git(root: Path, argv: list[str], *, label: str, check: bool = True) -> str:
    try:
        process = subprocess.run(
            ["git", "-C", str(root), *argv],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=_closed_environment(),
        )
    except OSError as exc:
        raise Refusal(f"{label}-unavailable") from exc
    if check and process.returncode != 0:
        raise Refusal(label)
    return process.stdout.strip()


def _closed_environment() -> dict[str, str]:
    """Return the small inherited environment allowed to a declared command."""
    result: dict[str, str] = {}
    for key in ("PATH", "HOME", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT"):
        value = os.environ.get(key)
        if isinstance(value, str) and value and "\x00" not in value:
            result[key] = value
    result.update({
        "LC_ALL": "C",
        "LANG": "C",
        "PYTHONUNBUFFERED": "1",
        "PYTHONHASHSEED": "0",
    })
    return result


def source_snapshot(root: str | os.PathLike[str], *, require_signed: bool = True) -> dict:
    """Capture the clean committed product identity used by one attempt."""
    root = Path(root).resolve(strict=True)
    if not root.is_dir() or (root / ".git").is_symlink():
        raise Refusal("source-root")
    status = _git(root, ["status", "--porcelain=v1", "--untracked-files=all"],
                  label="source-status")
    if status:
        raise Refusal("source-dirty")
    reported_root = _git(root, ["rev-parse", "--show-toplevel"],
                          label="source-root")
    if os.path.realpath(reported_root) != str(root):
        raise Refusal("source-root")
    commit = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"],
                  label="source-commit")
    tree = _git(root, ["rev-parse", "--verify", "HEAD^{tree}"],
                label="source-tree")
    if GIT_OBJECT_ID.fullmatch(commit) is None or GIT_OBJECT_ID.fullmatch(tree) is None:
        raise Refusal("source-identity")
    verified = False
    if require_signed:
        try:
            process = subprocess.run(
                ["git", "-C", str(root), "verify-commit", "--raw", commit],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                env=_closed_environment(),
            )
        except OSError as exc:
            raise Refusal("source-signature-unavailable") from exc
        if process.returncode != 0:
            raise Refusal("source-unsigned")
        verified = True
    return {
        "root": str(root),
        "commit": commit,
        "tree": tree,
        "status": "clean",
        "signed": verified,
    }


def _source_observation(root: Path) -> dict:
    """Read Git identity after a child, retaining dirty/drifted evidence."""
    try:
        status = _git(root, ["status", "--porcelain=v1", "--untracked-files=all"], label="source-status", check=False)
        commit = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"], label="source-commit")
        tree = _git(root, ["rev-parse", "--verify", "HEAD^{tree}"], label="source-tree")
    except Refusal:
        return {"root": str(root), "commit": "0" * 64, "tree": "0" * 64, "status": "unavailable", "signed": False}
    return {"root": str(root), "commit": commit, "tree": tree,
            "status": "clean" if not status else "dirty", "signed": False}


def _descriptor_group(join: dict, criterion_id: str) -> list[dict]:
    if not isinstance(join, dict) or join.get("schema") != "protasis-success-criteria-join/v1":
        raise Refusal("join-schema")
    rows = join.get("criteria")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_CRITERIA:
        raise Refusal("join-criteria")
    if any(not isinstance(row, dict) for row in rows):
        raise Refusal("join-descriptor")
    ids = [row.get("id") for row in rows]
    if any(not isinstance(value, str) or not value for value in ids):
        raise Refusal("join-id")
    if len(ids) != len(set(ids)):
        raise Refusal("join-duplicate-id")
    selected = [row for row in rows if row.get("id") == criterion_id]
    if len(selected) != 1:
        raise Refusal("criterion-unknown")
    row = selected[0]
    command = row.get("command")
    step = row.get("step")
    if not isinstance(command, str) or type(step) is not int or step < 1:
        raise Refusal("criterion-binding")
    group = [candidate for candidate in rows
             if isinstance(candidate, dict)
             and candidate.get("step") == step
             and candidate.get("command") == command]
    if not group:
        raise Refusal("criterion-group")
    # A group is the one observation named by every descriptor sharing an Exit.
    return sorted(group, key=lambda item: item.get("id", ""))


def descriptor_group(join: dict, criterion_id: str) -> list[dict]:
    """Public alias used by proof code and tests."""
    return _descriptor_group(join, criterion_id)


def validate_admission(root: Path, study: bytes, runbook: bytes, admission: dict) -> dict:
    """Replay an inert admission and ensure its source bytes still agree."""
    if not isinstance(admission, dict) or admission.get("schema") != ADMISSION_SCHEMA:
        raise Refusal("admission-schema")
    criteria, gate = adapters(root)
    record = criteria.parse(study)
    if record is None:
        raise Refusal("success-criteria-missing")
    current = gate.validate_with_criteria(Path(root).resolve(), study, runbook)
    comparable = {
        key: value for key, value in admission.items()
        if key not in {"attempts", "study_sha256", "runbook_sha256"}
    }
    if current != comparable or admission.get("operation_ran") is not False:
        raise Refusal("admission-drift")
    if admission.get("study_sha256") not in (None, digest(study)):
        raise Refusal("admission-study")
    if admission.get("runbook_sha256") not in (None, digest(runbook)):
        raise Refusal("admission-runbook")
    return current


def admit(root: Path, study: bytes, runbook: bytes) -> dict:
    """Build the inert declaration/command admission used by ``run-exit``."""
    criteria, gate = adapters(root)
    try:
        admission = gate.validate_with_criteria(Path(root).resolve(), study, runbook)
    except (gate.Refusal, criteria.Refusal, OSError, ValueError) as exc:
        raise Refusal(str(exc)) from exc
    if admission.get("schema") != ADMISSION_SCHEMA or admission.get("operation_ran") is not False:
        raise Refusal("admission-operation")
    _sha(admission.get("declaration_sha256"), "admission-declaration-digest")
    return admission


def _resolved_argv(invocation: dict) -> tuple[list[str], list[str], dict, dict]:
    original = invocation.get("argv")
    execution = invocation.get("execution_argv")
    cli = invocation.get("cli")
    if not isinstance(original, list) or not original or not all(isinstance(v, str) and v for v in original):
        raise Refusal("argv-original")
    if not isinstance(execution, list) or len(execution) != len(original) or not all(isinstance(v, str) and v for v in execution):
        raise Refusal("argv-expanded")
    if original[0] != "python3":
        raise Refusal("unregistered-executable")
    executable = shutil.which(original[0])
    if executable is None:
        raise Refusal("interpreter-unavailable")
    executable = os.path.realpath(executable)
    # The inert adapter deliberately retains the portable spelling ``python3``
    # in ``execution_argv``.  Resolve it only at the launch boundary and keep
    # the original spelling in the receipt beside the absolute executable.
    if execution[0] not in ("python3", executable) and os.path.realpath(execution[0]) != executable:
        raise Refusal("interpreter-binding")
    if not isinstance(cli, dict) or not isinstance(cli.get("sha256"), str):
        raise Refusal("cli-binding")
    try:
        executable_bytes = Path(executable).read_bytes()
    except OSError as exc:
        raise Refusal("interpreter-unavailable") from exc
    return list(original), list(execution), cli, {"path": executable, "sha256": digest(executable_bytes)}


def _kill_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.terminate()
        except (ProcessLookupError, OSError):
            pass
    try:
        process.wait(timeout=1)
    except (subprocess.TimeoutExpired, OSError):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                process.kill()
            except (ProcessLookupError, OSError):
                pass
        try:
            process.wait(timeout=1)
        except (subprocess.TimeoutExpired, OSError):
            pass


def _stream_record(hasher, count: int, data: bytes, cap: int) -> tuple[int, bool]:
    remaining = max(0, cap - count)
    prefix = data[:remaining]
    hasher.update(prefix)
    count += len(prefix)
    return count, len(prefix) != len(data)


def execute_argv(argv: list[str], root: str | os.PathLike[str], *, timeout: float = MAX_ATTEMPT_SECONDS,
                 stream_cap: int = MAX_STREAM_BYTES, env: dict[str, str] | None = None) -> dict:
    """Launch one exact argv and capture bounded stdout/stderr incrementally."""
    if type(timeout) not in (int, float) or timeout <= 0 or timeout > MAX_ATTEMPT_SECONDS:
        raise Refusal("attempt-deadline")
    if type(stream_cap) is not int or stream_cap < 1 or stream_cap > MAX_STREAM_BYTES:
        raise Refusal("stream-cap")
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
        raise Refusal("argv")
    root = Path(root).resolve(strict=True)
    started = time.monotonic()
    output = {
        "stdout": {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest(), "truncated": False},
        "stderr": {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest(), "truncated": False},
    }
    hashers = {name: hashlib.sha256() for name in ("stdout", "stderr")}
    counts = {"stdout": 0, "stderr": 0}
    process = None
    status = "completed"
    reason = "zero-exit"
    returncode = None
    try:
        process = subprocess.Popen(
            argv,
            cwd=str(root),
            # ``env`` is accepted for backwards-compatible test call sites but
            # never grants a caller an environment variable.  Production
            # execution always receives the closed allow-list above.
            env=dict(_closed_environment()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            start_new_session=True,
            close_fds=True,
        )
    except (OSError, ValueError) as exc:
        return {
            "status": "launch-failed",
            "reason": "launch-failed",
            "failure": "launch",
            "returncode": None,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "stdout": output["stdout"],
            "stderr": output["stderr"],
        }
    selector = selectors.DefaultSelector()
    try:
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        while selector.get_map():
            if time.monotonic() - started > timeout:
                status, reason = "timeout", "attempt-deadline"
                _kill_group(process)
                break
            try:
                ready = selector.select(min(0.1, max(0.001, timeout - (time.monotonic() - started))))
            except KeyboardInterrupt:
                status, reason = "interrupted", "interrupted-before-result"
                _kill_group(process)
                break
            if not ready:
                if process.poll() is not None:
                    # Drain both descriptors before leaving the selector loop.
                    ready = [(key, selectors.EVENT_READ) for key in list(selector.get_map().values())]
                else:
                    continue
            for key, _ in ready:
                name = key.data
                try:
                    chunk = os.read(key.fileobj.fileno(), READ_CHUNK)
                except OSError:
                    status, reason = "stream-read-failed", f"{name}-stream-read"
                    _kill_group(process)
                    break
                if not chunk:
                    try:
                        selector.unregister(key.fileobj)
                    except Exception:
                        pass
                    continue
                counts[name], overflow = _stream_record(hashers[name], counts[name], chunk, stream_cap)
                if overflow:
                    output[name]["truncated"] = True
                    status, reason = "stream-overflow", f"{name}-stream-cap"
                    _kill_group(process)
                    break
            if status != "completed":
                break
        try:
            returncode = process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            _kill_group(process)
            returncode = process.returncode
    except KeyboardInterrupt:
        status, reason = "interrupted", "interrupted-before-result"
        _kill_group(process)
    finally:
        try:
            selector.close()
        except Exception:
            pass
        if process is not None:
            for stream in (process.stdout, process.stderr):
                try:
                    if stream:
                        stream.close()
                except OSError:
                    pass
    if status == "completed":
        if returncode == 0:
            reason = "zero-exit"
        elif returncode is None:
            status, reason = "interrupted", "interrupted-before-result"
        elif returncode < 0:
            status, reason = "interrupted", f"signal-{abs(returncode)}"
        else:
            reason = "nonzero-exit"
    for name in ("stdout", "stderr"):
        output[name] = {"bytes": counts[name], "sha256": hashers[name].hexdigest(),
                        "truncated": bool(output[name]["truncated"])}
    failure_class = None
    if status != "completed":
        failure_class = status
    elif returncode not in (None, 0):
        failure_class = "exit"
    return {
        "status": status,
        "reason": reason,
        "failure": failure_class,
        "returncode": returncode,
        "elapsed_ms": int((time.monotonic() - started) * 1000),
        "stdout": output["stdout"],
        "stderr": output["stderr"],
    }


def _result_size(result: dict) -> int:
    return len(canonical(result))


def execute(root: Path, join: dict, criterion_id: str, *, run_id: str,
            init_id: str, step: int | None = None, require_signed: bool = True,
            timeout: float = MAX_ATTEMPT_SECONDS, stream_cap: int = MAX_STREAM_BYTES,
            study_sha256: str | None = None, runbook_sha256: str | None = None) -> dict:
    """Observe one descriptor group and return an append-only attempt record."""
    if not isinstance(run_id, str) or not run_id.strip():
        raise Refusal("run-id")
    if not isinstance(init_id, str) or not init_id.strip():
        raise Refusal("init-id")
    root = Path(root).resolve(strict=True)
    group = _descriptor_group(join, criterion_id)
    first = group[0]
    expected_step = first.get("step")
    if step is not None and step != expected_step:
        raise Refusal("criterion-step")
    exit_record = first.get("exit")
    if (
        not isinstance(exit_record, dict)
        or exit_record.get("command") != first.get("command")
        or exit_record.get("command_sha256") != digest(first["command"].encode("utf-8"))
    ):
        raise Refusal("criterion-exit-binding")
    source_before = source_snapshot(root, require_signed=require_signed)
    source_root = Path(source_before["root"])
    command = first["command"]
    criteria, gate = adapters(source_root)
    try:
        expanded = gate.expand(command)
    except (gate.Refusal, ValueError, RecursionError) as exc:
        raise Refusal("command-expansion") from exc
    if not expanded or len(expanded) > 256:
        raise Refusal("expanded-command-bound")
    invocations = []
    for original in expanded:
        # Re-admit the exact command and take its registered CLI binding.  The
        # command records in the join carry this same data from the runbook.
        try:
            validated = gate.validate_command(source_root, command)
        except (gate.Refusal, ValueError, RecursionError) as exc:
            raise Refusal("command-admission") from exc
        invocation = next((item for item in validated["invocations"] if item["argv"] == original), None)
        if invocation is None:
            raise Refusal("invocation-binding")
        original_argv, _, cli, executable = _resolved_argv(invocation)
        resolved = list(invocation["execution_argv"])
        resolved[0] = executable["path"]
        invocations.append({"original_argv": original_argv, "resolved_argv": resolved,
                            "cli": cli, "executable": executable})
    attempt_id = str(uuid.uuid4())
    results = []
    for invocation in invocations:
        results.append(execute_argv(invocation["resolved_argv"], source_root,
                                    timeout=timeout, stream_cap=stream_cap))
        if results[-1]["status"] != "completed" or results[-1].get("returncode") != 0:
            # A failed invocation does not start another one in a loop. An
            # explicit retry is a new attempt and remains visible.
            break
    source_after = None
    source_drift = False
    try:
        source_after = source_snapshot(source_root, require_signed=require_signed)
    except Refusal:
        source_drift = True
        source_after = _source_observation(source_root)
    if source_before.get("commit") != source_after.get("commit") or source_before.get("tree") != source_after.get("tree") or source_after.get("status") != "clean":
        source_drift = True
    if source_drift:
        for result in results:
            result["status"] = "source-drift"
            result["reason"] = "source-drift-after-launch"
            result["failure"] = "source-drift"
    settled = bool(results) and all(item["status"] == "completed" and item.get("returncode") == 0 for item in results) and not source_drift
    result = {
        "schema": RESULT_SCHEMA,
        "attempt_schema": ATTEMPT_SCHEMA,
        "attempt_id": attempt_id,
        "run_id": run_id,
        "init_id": init_id,
        "criterion_ids": [item["id"] for item in group],
        "step": expected_step,
        "cwd": str(source_root),
        "command": command,
        "command_sha256": digest(command.encode("utf-8")),
        "declaration_sha256": join.get("declaration_sha256"),
        "runbook_sha256": runbook_sha256 or join.get("runbook_sha256"),
        "study_sha256": study_sha256,
        "adapter_sha256": join.get("adapter_sha256"),
        "descriptors": [dict(item) for item in group],
        "invocations": invocations,
        "outcomes": results,
        "source_before": source_before,
        "source_after": source_after,
        "operation_ran": True,
        "observed": True,
        "settled": settled,
        "status": "settled" if settled else (results[-1]["status"] if results else "launch-failed"),
    }
    if _result_size(result) > MAX_RESULT_BYTES:
        raise Refusal("result-data-cap")
    return result


def validate_result(result: dict, join: dict, *, run_id: str | None = None,
                    init_id: str | None = None, step: int | None = None,
                    criterion_id: str | None = None,
                    study_sha256: str | None = None) -> dict:
    """Validate stored evidence without executing or trusting its verdict."""
    if (not isinstance(result, dict)
            or result.get("schema") != RESULT_SCHEMA
            or result.get("attempt_schema") != ATTEMPT_SCHEMA):
        raise Refusal("result-schema")
    if result.get("operation_ran") is not True or result.get("observed") is not True:
        raise Refusal("result-not-observed")
    if run_id is not None and result.get("run_id") != run_id:
        raise Refusal("result-run")
    if init_id is not None and result.get("init_id") != init_id:
        raise Refusal("result-init")
    if step is not None and result.get("step") != step:
        raise Refusal("result-step")
    ids = result.get("criterion_ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(v, str) for v in ids):
        raise Refusal("result-criteria")
    expected = _descriptor_group(join, criterion_id or ids[0])
    if ids != [item["id"] for item in expected]:
        raise Refusal("result-descriptor-group")
    descriptors = result.get("descriptors")
    if not isinstance(descriptors, list) or descriptors != expected:
        raise Refusal("result-descriptor-bytes")
    if (not isinstance(result.get("command"), str)
            or result.get("command") != expected[0].get("command")
            or result.get("step") != expected[0].get("step")):
        raise Refusal("result-command")
    if result.get("command_sha256") != digest(result["command"].encode("utf-8")):
        raise Refusal("result-command-digest")
    if result.get("declaration_sha256") != join.get("declaration_sha256"):
        raise Refusal("result-declaration")
    if result.get("runbook_sha256") != join.get("runbook_sha256"):
        raise Refusal("result-runbook")
    expected_adapter = join.get("adapter_sha256")
    if expected_adapter is not None:
        _sha(expected_adapter, "result-adapter")
        if result.get("adapter_sha256") != expected_adapter:
            raise Refusal("result-adapter")
    if result.get("study_sha256") is not None:
        _sha(result.get("study_sha256"), "result-study")
        # The runbook join has no study bytes of its own; callers that retain
        # an admission metadata digest must compare it before replay.
    if study_sha256 is not None and result.get("study_sha256") != study_sha256:
        raise Refusal("result-study")
    for name in ("attempt_id", "run_id", "init_id"):
        if not isinstance(result.get(name), str) or not result[name].strip():
            raise Refusal(f"result-{name}")
    invocations = result.get("invocations")
    outcomes = result.get("outcomes")
    if not isinstance(invocations, list) or not invocations or not isinstance(outcomes, list) or len(outcomes) != len(invocations):
        raise Refusal("result-invocations")
    admitted_source = as_dict(expected[0].get("exit")).get("source")
    admitted_invocations = as_dict(admitted_source).get("invocations")
    if not isinstance(admitted_invocations, list) or len(admitted_invocations) != len(invocations):
        raise Refusal("result-invocation-binding")
    for observed, admitted in zip(invocations, admitted_invocations):
        if not isinstance(observed, dict) or not isinstance(admitted, dict):
            raise Refusal("result-invocation-binding")
        if observed.get("original_argv") != admitted.get("argv") or observed.get("cli") != admitted.get("cli"):
            raise Refusal("result-argv-binding")
        resolved = observed.get("resolved_argv")
        admitted_execution = admitted.get("execution_argv")
        if (not isinstance(resolved, list) or not isinstance(admitted_execution, list)
                or len(resolved) != len(admitted_execution)
                or resolved[1:] != admitted_execution[1:]):
            raise Refusal("result-expanded-argv")
        executable = observed.get("executable")
        if (not isinstance(executable, dict)
                or not isinstance(executable.get("path"), str)
                or not executable["path"].startswith("/")
                or os.path.realpath(executable["path"]) != executable["path"]
                or SHA256.fullmatch(executable.get("sha256", "")) is None
                or not resolved or resolved[0] != executable["path"]):
            raise Refusal("result-executable")
        try:
            if not os.path.isfile(executable["path"]) or os.path.islink(executable["path"]):
                raise Refusal("result-executable")
            if digest(Path(executable["path"]).read_bytes()) != executable["sha256"]:
                raise Refusal("result-executable")
        except OSError as exc:
            raise Refusal("result-executable") from exc
    for outcome in outcomes:
        if not isinstance(outcome, dict) or outcome.get("status") not in {
            "completed", "launch-failed", "timeout", "stream-overflow",
            "interrupted", "stream-read-failed", "source-drift",
        }:
            raise Refusal("result-outcome")
        for stream in ("stdout", "stderr"):
            record = outcome.get(stream)
            if not isinstance(record, dict) or type(record.get("bytes")) is not int or record["bytes"] < 0 or record["bytes"] > MAX_STREAM_BYTES or SHA256.fullmatch(record.get("sha256", "")) is None or type(record.get("truncated")) is not bool:
                raise Refusal("result-stream")
    for source_name in ("source_before", "source_after"):
        source = result.get(source_name)
        if (not isinstance(source, dict)
                or not isinstance(source.get("root"), str)
                or not source["root"].startswith("/")
                or os.path.realpath(source["root"]) != source["root"]
                or source.get("status") not in {"clean", "dirty", "unavailable"}
                or type(source.get("signed")) is not bool
                or GIT_OBJECT_ID.fullmatch(source.get("commit", "")) is None
                or GIT_OBJECT_ID.fullmatch(source.get("tree", "")) is None):
            raise Refusal("result-source")
    if result.get("cwd") != result["source_before"].get("root") or result["source_before"].get("root") != result["source_after"].get("root"):
        raise Refusal("result-context")
    if result.get("settled") is True:
        if (result.get("status") != "settled"
                or result["source_before"].get("status") != "clean"
                or result["source_after"].get("status") != "clean"
                or not result["source_before"].get("signed")
                or not result["source_after"].get("signed")
                or result["source_before"].get("commit") != result["source_after"].get("commit")
                or result["source_before"].get("tree") != result["source_after"].get("tree")):
            raise Refusal("result-source-signature")
        if not outcomes or any(item.get("status") != "completed" or item.get("returncode") != 0 for item in outcomes):
            raise Refusal("result-forged-success")
    elif result.get("status") == "settled":
        raise Refusal("result-settled-status")
    if _result_size(result) > MAX_RESULT_BYTES:
        raise Refusal("result-data-cap")
    return result


def replay(result: dict, join: dict, **kwargs) -> dict:
    """Read-only result replay alias."""
    return validate_result(result, join, **kwargs)


def result_data_size(result: dict) -> int:
    return _result_size(result)


# Descriptive aliases keep the adapter usable by proof code that speaks in
# terms of an attempt or a capture while retaining one implementation path.
capture = execute_argv
run = execute
validate_attempt = validate_result
