#!/usr/bin/env python3
"""Execute a separately frozen four-input Wildcat CLI reproduction matrix."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import threading
import time


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import wildcat_v3_custody as evidence
from wildcat_v3_execution import (
    MUTATIONS, canonical, digest, inventory, mutate, ref, save_inventory,
    summary, write_new,
)


ENTRY = "plugins/tabularium/scripts/tabularium.py"
GUARD = "plugins/tabularium/tests/wildcat_v3_offline_cli.py"
EXECUTOR = "plugins/tabularium/tests/execute_wildcat_v3_reproduction.py"
STREAM_CAP = 1024 * 1024
TIMEOUT = 900
PLAN_CAP = 2 * 1024 * 1024
INPUTS = (
    ("public-v1", "wildcat-v1", "78531eabca0d8b9cbfd92ab382575645db5f9505d9ff51362bcf25edec8faa68"),
    ("public-v2", "wildcat-v2", "bfb2d4fe388fb4f803edda4613c305b1f36514ed6611b193095309ceed61c263"),
    ("retained-v1", "wildcat-v1", "eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69"),
    ("retained-v2", "wildcat-v2", "2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3"),
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def _loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate execution JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite execution JSON")))


def git(repo, *args):
    command = ["git", "--no-replace-objects", "-C", str(repo), *args]
    result = subprocess.run(command, capture_output=True, check=True, timeout=20)
    return result.stdout.decode().strip()


def _path_operand(raw, field):
    """Reject lexical and filesystem aliases before using a caller's path."""
    if not isinstance(raw, str):
        raise ValueError(field + " must be a path string")
    if Path(raw).is_absolute():
        evidence.absolute(raw, field)
        path = Path(raw)
    else:
        evidence.relative(raw, field)
        path = Path.cwd() / raw
    if str(path.resolve()) != str(path):
        raise ValueError(field + " has a linked or noncanonical component")
    return path


def _plan_shape(plan):
    """Admit the closed plan vocabulary before any child or custody write."""
    evidence.closed(plan, ("schema", "source", "code_pins", "runtime", "guard", "executor", "inputs"), "plan")
    if plan["schema"] != "wildcat-v3-execution-plan/v1":
        raise ValueError("execution plan schema differs")
    source = evidence.closed(plan["source"], ("root", "head", "tree", "fingerprint"), "plan.source")
    evidence.absolute(source["root"], "plan.source.root")
    root = _path_operand(source["root"], "plan.source.root")
    if not root.is_absolute() or root != HERE.parents[2]:
        raise ValueError("execution plan source differs from the executor owner")
    for name in ("head", "tree"):
        if type(source[name]) is not str or re.fullmatch(r"[0-9a-f]{40}", source[name]) is None:
            raise ValueError("execution plan Git provenance differs")
    evidence.text(source["fingerprint"], "plan.source.fingerprint", 128)
    runtime = evidence.closed(plan["runtime"], ("executable", "version", "pins"), "plan.runtime")
    evidence.absolute(runtime["executable"], "plan.runtime.executable")
    _path_operand(runtime["executable"], "plan.runtime.executable")
    if runtime["version"] != "3.14.6":
        raise ValueError("execution plan runtime version differs")
    for name, absolute in (("code_pins", False), ("runtime", True)):
        rows = runtime["pins"] if absolute else plan[name]
        if type(rows) is not list or not 0 < len(rows) <= evidence.ITEM_CAP:
            raise ValueError("execution plan pin count differs")
        names = []
        for row in rows:
            evidence.closed(row, ("path", "bytes", "sha256"), "plan.pin")
            (evidence.absolute if absolute else evidence.relative)(row["path"], "plan.pin.path")
            evidence.byte_claim({key: row[key] for key in ("bytes", "sha256")}, "plan.pin")
            names.append(row["path"])
        if names != sorted(set(names)):
            raise ValueError("execution plan pin paths differ")
    code = {row["path"]: {key: row[key] for key in ("bytes", "sha256")} for row in plan["code_pins"]}
    for name, owner in (("guard", GUARD), ("executor", EXECUTOR)):
        row = evidence.closed(plan[name], ("path", "bytes", "sha256"), "plan." + name)
        if row["path"] != owner or code.get(owner) != {key: row[key] for key in ("bytes", "sha256")}:
            raise ValueError("execution plan owner pin differs")
    inputs = plan["inputs"]
    if type(inputs) is not list or len(inputs) != len(INPUTS):
        raise ValueError("execution plan input count differs")
    roots = []
    for row, identity in zip(inputs, INPUTS):
        evidence.closed(row, ("label", "adapter", "raw_release_id", "root", "inventory"), "plan.input")
        if (row["label"], row["adapter"], row["raw_release_id"]) != identity:
            raise ValueError("execution plan input identity differs")
        evidence.absolute(row["root"], "plan.input.root")
        original = _path_operand(row["root"], "plan.input.root")
        if not original.is_dir():
            raise ValueError("execution plan input root is unavailable")
        if identity[0].startswith("public") and original != root / (
                "plugins/tabularium/examples/" + identity[1] + "-v0/release/source/raw-release"):
            raise ValueError("execution plan public input owner differs")
        evidence.inventory_shape(row["inventory"])
        if row["inventory"]["root"] != str(original) or any(
                original == previous or original.is_relative_to(previous) or previous.is_relative_to(original)
                for previous in roots):
            raise ValueError("execution plan input roots alias")
        roots.append(original)


def _external_custody(raw, plan):
    evidence.absolute(raw, "custody.path")
    root = _path_operand(raw, "custody.path")
    protected = [Path(plan["source"]["root"]), *(Path(row["root"]) for row in plan["inputs"])]
    if os.path.lexists(root) or any(root.is_relative_to(path) or path.is_relative_to(root) for path in protected):
        raise ValueError("custody must be a fresh external directory disjoint from all inputs")
    return root


def _operation_identity(identifier, label, kind):
    if type(identifier) is not str or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identifier) is None or len(identifier) > 128:
        raise ValueError("operation identifier must be one safe path component")
    if label == "guard":
        expected = {"guard-" + name for name in ("compatibility", "socket", "dns", "connect")} if kind == "diagnostic" else set()
    elif type(label) is str and label in {row[0] for row in INPUTS}:
        if kind in ("build", "verify", "moved-verify"):
            expected = {label + "-" + kind}
        elif kind in ("pristine-control", "mutation-verify"):
            suffix = "control" if kind == "pristine-control" else "refusal"
            expected = {label + "-" + mutation + "-" + suffix for mutation in MUTATIONS}
        else:
            expected = set()
    else:
        expected = set()
    if identifier not in expected:
        raise ValueError("operation identity differs from the closed matrix")


def code_pins(repo):
    paths = set()
    for family in ("plugins/tabularium/scripts", "plugins/alexandria/scripts"):
        paths.update(path.relative_to(repo).as_posix() for path in (repo / family).rglob("*.py")
                     if "__pycache__" not in path.parts)
    paths.add("plugins/alexandria/.claude-plugin/plugin.json")
    paths.update("plugins/tabularium/tests/" + name for name in (
        "execute_wildcat_v3_reproduction.py", "wildcat_v3_offline_cli.py", "wildcat_v3_execution.py",
        "wildcat_v3_custody.py", "test_wildcat_v3_reproduction.py", "emit_wildcat_v3_report.py",
        "prove_wildcat_v3.py", "wildcat_v3_proofs.py", "wildcat_v3_reports.py",
        "support.py", "__init__.py"))
    return [{"path": path, **digest(repo / path)} for path in sorted(paths)]


def runtime_pins(runtime):
    """Bind the distribution's noncache resources, excluding unused site packages."""
    paths = [path for path in runtime.rglob("*")
             if path.is_file() and not path.is_symlink() and path.suffix != ".pyc"
             and "__pycache__" not in path.parts and "site-packages" not in path.parts]
    return [{"path": str(path.resolve()), **digest(path)}
            for path in sorted(paths, key=lambda item: str(item).encode())]


def prepare(args):
    repo, runtime = Path(args.repo).resolve(), Path(sys.executable).resolve().parents[1]
    if platform.python_version() != "3.14.6":
        raise ValueError("demonstration requires the owned Python 3.14.6")
    info = repo.stat()
    roots = {}
    for label, adapter, _ in INPUTS:
        if label.startswith("public"):
            roots[label] = str(repo / ("plugins/tabularium/examples/" + adapter + "-v0/release/source/raw-release"))
        else:
            roots[label] = str(Path(args.retained_inputs).resolve() / ("v1-demo/release" if adapter == "wildcat-v1" else "v2-demo/release"))
    plan = {"schema": "wildcat-v3-execution-plan/v1",
            "source": {"root": str(repo), "head": git(repo, "rev-parse", "HEAD"),
                       "tree": git(repo, "rev-parse", "HEAD^{tree}"),
                       "fingerprint": "issue/" + str(info.st_dev) + "-" + str(info.st_ino)},
            "code_pins": code_pins(repo),
            "runtime": {"executable": str(Path(sys.executable).resolve()), "version": platform.python_version(),
                        "pins": runtime_pins(runtime)},
            "guard": {"path": GUARD, **digest(repo / GUARD)},
            "executor": {"path": EXECUTOR, **digest(repo / EXECUTOR)},
            "inputs": [{"label": label, "adapter": adapter, "raw_release_id": release_id,
                        "root": roots[label], "inventory": inventory(roots[label])}
                       for label, adapter, release_id in INPUTS]}
    _plan_shape(plan)
    output = _path_operand(args.output, "plan.output")
    if any(output.is_relative_to(Path(row["root"])) for row in plan["inputs"]):
        raise ValueError("plan output aliases preserved input")
    encoded = canonical(plan)
    if len(encoded) > PLAN_CAP:
        raise ValueError("execution plan exceeds byte cap")
    write_new(output, encoded)
    print(json.dumps({"event": "wildcat-execution-plan-created", "code_files": len(plan["code_pins"]),
                      "runtime_files": len(plan["runtime"]["pins"]), **digest(args.output)}, sort_keys=True))


def pins_current(plan):
    _plan_shape(plan)
    repo = Path(plan["source"]["root"])
    info = repo.stat()
    if plan["source"]["fingerprint"] != "issue/" + str(info.st_dev) + "-" + str(info.st_ino):
        raise ValueError("execution worktree fingerprint changed")
    if code_pins(repo) != plan["code_pins"]:
        raise ValueError("frozen code or consumed resource changed")
    runtime = Path(plan["runtime"]["executable"]).parents[1]
    if str(Path(sys.executable).resolve()) != plan["runtime"]["executable"] or platform.python_version() != plan["runtime"]["version"]:
        raise ValueError("execution interpreter differs from frozen runtime")
    if runtime_pins(runtime) != plan["runtime"]["pins"]:
        raise ValueError("frozen runtime resource changed")
    for row in plan["inputs"]:
        if inventory(row["root"]) != row["inventory"]:
            raise ValueError("admitted input bytes changed")


def operation(plan, custody, operation_id, label, kind, cli):
    """Retain every closed child observation, including failed infrastructure."""
    _operation_identity(operation_id, label, kind)
    folder = custody / "operations" / operation_id
    folder.mkdir(parents=True, mode=0o700)
    cache = folder / "pycache"
    # The exclusive operation parent owns an absent lookup prefix. -B keeps
    # it absent, so no previous cache can supply executed bytes.
    if os.path.lexists(cache):
        raise ValueError("fresh bytecode-cache prefix is occupied")
    guard_path, modules_path = folder / "network.json", folder / "modules.json"
    argv = [plan["runtime"]["executable"], "-I", "-S", "-B", "-X", "pycache_prefix=" + str(cache),
            str(Path(plan["source"]["root"]) / GUARD), "--repo", plan["source"]["root"],
            "--guard-report", str(guard_path), "--modules-report", str(modules_path), "--", *cli]
    started, tick = utc(), time.monotonic()
    timed_out, exception = False, None
    truncated, errors = {"stdout": False, "stderr": False}, []
    streams = {"stdout": folder / "stdout", "stderr": folder / "stderr"}
    process = None

    def retain(name, source):
        try:
            with streams[name].open("xb") as target:
                count = 0
                while block := source.read(65536):
                    permitted = max(0, STREAM_CAP - count)
                    target.write(block[:permitted])
                    count += len(block)
                    if count > STREAM_CAP:
                        truncated[name] = True
                        process.kill()
        except BaseException as error:
            errors.append(type(error).__name__)
            if process is not None:
                process.kill()
        finally:
            source.close()

    try:
        process = subprocess.Popen(argv, cwd=plan["source"]["root"], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        readers = [threading.Thread(target=retain, args=(name, getattr(process, name)))
                   for name in ("stdout", "stderr")]
        for reader in readers:
            reader.start()
        try:
            exit_code = process.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            exit_code = process.wait()
        for reader in readers:
            reader.join(timeout=5)
            if reader.is_alive():
                raise RuntimeError("child stream did not close")
        if errors:
            exception = errors[0]
    except BaseException as error:
        exception = type(error).__name__
        exit_code = -1
        for path in streams.values():
            if not path.exists():
                write_new(path, b"")
    if os.path.lexists(cache):
        exception = exception or "OccupiedBytecodeCachePrefix"
    finished, duration = utc(), time.monotonic() - tick
    try:
        guard = _loads(guard_path.read_bytes()) if guard_path.is_file() else None
    except (OSError, ValueError, TypeError) as error:
        guard = None
        exception = exception or type(error).__name__
    observation = {"schema": "wildcat-v3-cli-observation/v1", "id": operation_id,
                   "label": label, "kind": kind, "process_argv": argv, "cli_argv": cli,
                   "started_at_utc": started, "finished_at_utc": finished,
                   "duration_seconds": duration, "exit": exit_code, "timed_out": timed_out,
                   "stdout_truncated": truncated["stdout"], "stderr_truncated": truncated["stderr"],
                   "exception": exception, "network_attempts": guard["attempts"] if guard else -1,
                   "guard_report": ref(custody, guard_path) if guard else None,
                   "loaded_modules": ref(custody, modules_path) if modules_path.is_file() else None}
    receipt = folder / "receipt.json"
    write_new(receipt, canonical(observation))
    value = {"id": operation_id, "label": label, "kind": kind,
             "receipt": ref(custody, receipt), "stdout": ref(custody, streams["stdout"]),
             "stderr": ref(custody, streams["stderr"])}
    print(json.dumps({"event": "wildcat-cli-observed", "id": operation_id, "exit": exit_code,
                      "network_attempts": observation["network_attempts"],
                      "duration_seconds": duration}, sort_keys=True), flush=True)
    if timed_out or exception or any(truncated.values()) or guard is None or not modules_path.is_file():
        raise ValueError("actual CLI infrastructure was unavailable: " + operation_id)
    pins = {str(Path(plan["source"]["root"]) / row["path"]): (row["bytes"], row["sha256"])
            for row in plan["code_pins"]}
    pins.update({row["path"]: (row["bytes"], row["sha256"]) for row in plan["runtime"]["pins"]})
    for row in _loads(modules_path.read_bytes())["modules"]:
        if pins.get(row["path"]) != (row["bytes"], row["sha256"]):
            raise ValueError("executed module escaped frozen closure: " + row["name"])
    return value, observation, guard


def _require(operation_result, expected_exit, attempts=0, guard_exception=None):
    value, observed, guard = operation_result
    if observed["exit"] != expected_exit or guard["cli_exit"] != expected_exit:
        raise ValueError("actual CLI exit differed: " + value["id"])
    if observed["network_attempts"] != attempts or guard["exception"] != guard_exception:
        raise ValueError("actual guarded operation differed: " + value["id"])
    return value, observed


def execute(args):
    plan_path = _path_operand(args.plan, "execution.plan")
    captured_plan, plan_claim = evidence.read_file(plan_path, PLAN_CAP)
    plan = evidence.parse_json(captured_plan)
    pins_current(plan)
    custody = _external_custody(args.custody, plan)
    custody.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    custody.mkdir(mode=0o700)
    free = os.statvfs(custody)
    write_new(custody / "preflight.json", canonical({"schema": "wildcat-v3-execution-preflight/v1",
               "observed_at_utc": utc(), "available_bytes": free.f_bavail * free.f_frsize,
               "plan": plan_claim, "runtime_files": len(plan["runtime"]["pins"]),
               "code_files": len(plan["code_pins"])}))
    write_new(custody / "plan.json", captured_plan)
    result = {key: plan[key] for key in ("source", "code_pins", "runtime", "guard", "executor")}
    result.update({"schema": "wildcat-v3-execution-custody/v1", "inputs": [], "operations": [],
                   "mutations": [], "guard_diagnostics": []})
    try:
        for diagnostic in ("compatibility", "socket", "dns", "connect"):
            actual = operation(plan, custody, "guard-" + diagnostic, "guard", "diagnostic", ["diagnostic", diagnostic])
            _require(actual, 0 if diagnostic == "compatibility" else 1,
                     attempts=0 if diagnostic == "compatibility" else 1,
                     guard_exception=None if diagnostic == "compatibility" else "NetworkDenied")
            if (custody / actual[0]["stdout"]["path"]).read_bytes() or (custody / actual[0]["stderr"]["path"]).read_bytes():
                raise ValueError("diagnostic emitted unexpected output")
            result["guard_diagnostics"].append(actual[0])
        entry = str(Path(plan["source"]["root"]) / ENTRY)
        for original in plan["inputs"]:
            label = original["label"]
            base = custody / "payloads" / label
            base.mkdir(parents=True, mode=0o700)
            built, moved = base / "built", base / "moved"
            original_ref, original_inventory = save_inventory(custody, original["root"], label + "-original")
            if original_inventory != original["inventory"]:
                raise ValueError("original input changed before actual build")
            release = "wildcat-reproduction-" + label
            actual = operation(plan, custody, label + "-build", label, "build", [entry, "wildcat-canonical", "--alexandria-release", original["root"], "--release", release, "--out", str(built)])
            _require(actual, 0)
            if (custody / actual[0]["stderr"]["path"]).read_bytes():
                raise ValueError("positive build emitted stderr")
            built_stdout = _loads((custody / actual[0]["stdout"]["path"]).read_bytes())
            if built_stdout["event"] != "wildcat-canonical-built" or built_stdout["release"] != release:
                raise ValueError("actual build report identity differs")
            result["operations"].append(actual[0])
            built_ref, built_inventory = save_inventory(custody, built, label + "-built")
            for operation_kind, root in (("verify", built), ("moved-verify", moved)):
                if operation_kind == "moved-verify":
                    shutil.copytree(built, moved, copy_function=shutil.copyfile)
                    if inventory(moved)["files"] != built_inventory["files"]:
                        raise ValueError("whole moved release copy differs")
                actual = operation(plan, custody, label + "-" + operation_kind, label, operation_kind, [entry, "verify", str(root / "coverage.json")])
                _require(actual, 0)
                if (custody / actual[0]["stderr"]["path"]).read_bytes():
                    raise ValueError("positive verify emitted stderr")
                positive = _loads((custody / actual[0]["stdout"]["path"]).read_bytes())
                if positive["event"] != "wildcat-canonical-verified" or positive["rows"] != built_stdout["rows"] or positive["canonical_sha256"] != built_stdout["canonical_sha256"]:
                    raise ValueError("actual verify report differs from build")
                result["operations"].append(actual[0])
            moved_ref, moved_inventory = save_inventory(custody, moved, label + "-moved")
            input_row = {"label": label, "raw_release_id": original["raw_release_id"], "adapter": original["adapter"],
                         "original_root": original["root"], "original_inventory": original_ref,
                         "built_root": built.relative_to(custody).as_posix(), "moved_root": moved.relative_to(custody).as_posix(),
                         "built_inventory": built_ref, "moved_inventory": moved_ref,
                         "summary": summary(moved, built_stdout["rows"], built_stdout["canonical_sha256"])}
            raw_manifest = _loads((moved / "source/raw-release/manifest.json").read_bytes())
            if raw_manifest["release_id"] != "sha256:" + original["raw_release_id"]:
                raise ValueError("admitted raw release ID differs")
            result["inputs"].append(input_row)
            for kind in MUTATIONS:
                mutant = base / ("mutation-" + kind)
                shutil.copytree(moved, mutant, copy_function=shutil.copyfile)
                mutant.chmod(0o700)
                for path in mutant.rglob("*"):
                    if path.is_dir():
                        path.chmod(0o700)
                    elif path.is_file():
                        path.chmod(0o600)
                pristine_ref, pristine = save_inventory(custody, mutant, label + "-" + kind + "-pristine")
                if pristine["files"] != moved_inventory["files"]:
                    raise ValueError("pristine mutation control copy differs")
                control_id, verify_id = label + "-" + kind + "-control", label + "-" + kind + "-refusal"
                control = operation(plan, custody, control_id, label, "pristine-control", [entry, "verify", str(mutant / "coverage.json")])
                _require(control, 0)
                if (custody / control[0]["stderr"]["path"]).read_bytes():
                    raise ValueError("pristine control emitted stderr")
                result["operations"].append(control[0])
                reason = mutate(mutant, kind)
                mutated_ref, mutated = save_inventory(custody, mutant, label + "-" + kind + "-mutated")
                before, after = ({row["path"]: row for row in value["files"]} for value in (pristine, mutated))
                if set(before) != set(after):
                    raise ValueError("mutation changed release path set")
                changes = [{"path": path, "before": {key: before[path][key] for key in ("bytes", "sha256")},
                            "after": {key: after[path][key] for key in ("bytes", "sha256")}}
                           for path in sorted(before) if before[path] != after[path]]
                actual = operation(plan, custody, verify_id, label, "mutation-verify", [entry, "verify", str(mutant / "coverage.json")])
                _require(actual, 1)
                if (custody / actual[0]["stdout"]["path"]).read_bytes() or (custody / actual[0]["stderr"]["path"]).read_bytes() != ("tabularium: verification failed: " + reason + "\n").encode():
                    raise ValueError("actual mutation was not the intended semantic refusal")
                if inventory(mutant) != mutated:
                    raise ValueError("read-only refusal changed mutant output")
                result["operations"].append(actual[0])
                result["mutations"].append({"label": label, "kind": kind, "root": mutant.relative_to(custody).as_posix(),
                                           "control_id": control_id, "verify_id": verify_id,
                                           "pristine_inventory": pristine_ref, "mutated_inventory": mutated_ref,
                                           "changes": changes, "expected_reason": reason})
            if inventory(original["root"]) != original_inventory or inventory(built) != built_inventory or inventory(moved) != moved_inventory:
                raise ValueError("original or accepted release changed during demonstration")
        pins_current(plan)
        write_new(custody / "inventory.json", canonical(result))
        print(json.dumps({"event": "wildcat-reproduction-executed", "custody": str(custody),
                          "inputs": len(result["inputs"]), "operations": len(result["operations"]),
                          "mutation_refusals": len(result["mutations"]),
                          "inventory": digest(custody / "inventory.json")}, sort_keys=True))
    except BaseException as error:
        write_new(custody / "failed-attempt.json", canonical({"schema": "wildcat-v3-execution-failure/v1",
                  "finished_at_utc": utc(), "exception": type(error).__name__, "reason": str(error),
                  "partial": result}))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preparation = commands.add_parser("prepare", help="freeze local code/runtime/input bytes without executing the matrix")
    preparation.add_argument("--repo", required=True)
    preparation.add_argument("--retained-inputs", required=True)
    preparation.add_argument("--output", required=True)
    execution = commands.add_parser("execute", help="run the separately frozen literal owner CLI matrix")
    execution.add_argument("--plan", required=True)
    execution.add_argument("--custody", required=True)
    args = parser.parse_args(argv)
    try:
        prepare(args) if args.command == "prepare" else execute(args)
    except Exception as error:
        print(json.dumps({"event": "wildcat-reproduction-unavailable", "error_class": type(error).__name__,
                          "reason": str(error)}, sort_keys=True), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
