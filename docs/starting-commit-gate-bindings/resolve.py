#!/usr/bin/env python3
"""Resolve one selection cell of the #2042 design record on a replica of run #1872.

Each invocation rebuilds a disposable copy of the #1872 Step 7 tree from Git,
places the pinned state snapshot beside it, builds the candidate's controller
from this worktree's `plugins/hexaemeron`, measures one criterion and writes one
`protasis-design-report/v1` report to a path that must not exist. It writes
nothing under this run's `.hexaemeron/` except that report and one evidence
sidecar, and it never opens the live #1872 worktree.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "run-1872"
ADAPTER = "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
HEXCTL = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
PROTASIS = "plugins/hexaemeron/skills/protasis/scripts/protasis.py"
RUN_HEAD = "5d5ec5e142d83140a0967fe13ad3498df3df2015"
FIXTURE_DIGESTS = {"state.json": "95cb93ecf2070f4e823819463704798084b3eb439f180026f8f6e96c0381a6f0", "ledger.jsonl": "499080ad61bc1217009ccb4a056837c5bc7843106d858c92370d190148487916"}
STUDY_BASE = {HEXCTL: "e07e2c0065f6f2b18c01a29a312a5034889c417b8702ef25b3bdf028ee6d89ce", ADAPTER: "90ad7967e44a583fa5be15f15b804cccdfbd74750e1da19adaae00959dc055f7"}
BASE_CONTROLLER = {
    HEXCTL: "fa2cfc3dda1e3cef1a8a1829dbebee7e17cdd1887e0ee54e38e1c38fa2ea35f3",
    ADAPTER: "ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119",
}
# reviewed-prior-pins types these three values by hand, as a release review would.
LITERAL_ADAPTER = "ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119"
LITERAL_ROWS = ((PROTASIS,
                 "0d3742b85957171503269e60397d8829459f08eac21cf6b4d50f55c44fc602d5",
                 "4173755991c975f8914c02eaa57fe22c3b36880f7f65b10cb3c20e7ea8b4542a"),)
CANDIDATES = ("base-commit-bindings", "reviewed-prior-pins",
              "runbook-scoped-pins", "recorded-controller-fork")
CRITERIA = {
    "main-controller-replays-1872": "boolean",
    "edited-module-refuses": "boolean",
    "unknown-adapter-refuses": "boolean",
    "verify-writes-no-state": "bytes",
    "verify-wall-ms": "milliseconds",
    "reviewed-rows-per-release": "count",
}
TIMEOUT = 300


class Refusal(Exception):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(cwd: Path, *argv: str) -> bytes:
    completed = subprocess.run(["git", "-C", str(cwd), *argv], stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=TIMEOUT)
    if completed.returncode != 0:
        raise Refusal("git-" + argv[0] + ": " + completed.stderr.decode(errors="replace")[:200])
    return completed.stdout


def git_blob(cwd: Path, spec: str) -> bytes | None:
    completed = subprocess.run(["git", "-C", str(cwd), "cat-file", "-p", spec], stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=TIMEOUT)
    return completed.stdout if completed.returncode == 0 else None


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_digests(root: Path, expected: dict, reason: str) -> None:
    for relative, digest in expected.items():
        actual = sha((root / relative).read_bytes())
        if actual != digest:
            raise Refusal(f"{reason}:{relative}:{actual[:12]}")


def build_replica(tmp: Path) -> tuple[Path, dict]:
    check_digests(FIXTURE, FIXTURE_DIGESTS, "fixture-differs-from-study-snapshot")
    state = json.loads((FIXTURE / "state.json").read_text())
    origin = state["config"]["git"]["origin"]
    if not os.path.isdir(os.path.join(origin, ".git")):
        raise Refusal("origin-unavailable")
    replica = tmp / "replica"
    subprocess.run(["git", "clone", "--quiet", "--no-checkout", origin, str(replica)],
                   check=True, stdin=subprocess.DEVNULL, capture_output=True, timeout=TIMEOUT)
    git(replica, "checkout", "--quiet", "--detach", RUN_HEAD)
    target = replica / ".hexaemeron"
    target.mkdir()
    for name in ("state.json", "ledger.jsonl", "runbook.md", "study.md", "design-evidence.json"):
        shutil.copyfile(FIXTURE / name, target / name)
    shutil.copytree(FIXTURE / "reports", target / "reports")
    return replica, state


def copy_controller(tmp: Path, name: str) -> Path:
    check_digests(ROOT, STUDY_BASE, "controller-differs-from-study-base")
    destination = tmp / name / "plugins" / "hexaemeron"
    shutil.copytree(ROOT / "plugins" / "hexaemeron", destination)
    return tmp / name


def base_controller(tmp: Path, replica: Path, base: str) -> Path:
    destination = tmp / "base-controller"
    destination.mkdir()
    archive = git(replica, "archive", base, "plugins/hexaemeron")
    subprocess.run(["tar", "-x", "-C", str(destination)], input=archive, check=True, timeout=TIMEOUT)
    check_digests(destination, BASE_CONTROLLER, "base-controller-differs-from-record")
    return destination


def module_binding(adapter, data: bytes, builder: str, path: str) -> str:
    tree = ast.parse(data, filename=path)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == builder]
    if len(functions) != 1:
        raise Refusal("ambiguous-builder:" + path)
    functions[0].body = []
    return adapter.digest(ast.dump(tree, include_attributes=False).encode())


def derive_rows(adapter, replica: Path, base: str) -> tuple[str, list[tuple[str, str, str]]]:
    """The rule base-commit-bindings applies: pins and adapter from the starting commit."""
    blob = git_blob(replica, base + ":" + ADAPTER)
    if blob is None:
        raise Refusal("base-adapter-unavailable")
    tree = ast.parse(blob, filename=ADAPTER)
    literals = [ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "MODULE_BINDINGS" for t in node.targets)]
    if len(literals) != 1 or not isinstance(literals[0], dict):
        raise Refusal("base-module-bindings-unreadable")
    rows = []
    for path, builder in sorted(adapter.REGISTRY.items()):
        pin = literals[0].get(path)
        recorded = git_blob(replica, base + ":" + path)
        current = replica / path
        if pin is None or recorded is None or not current.is_file():
            continue
        data = current.read_bytes()
        if data != recorded:
            continue
        actual = module_binding(adapter, data, builder, path)
        if actual == pin:
            rows.append((path, actual, sha(data)))
    return sha(blob), rows


def patch_adapter(controller: Path, adapters: list[str], rows: list[tuple[str, str, str]]) -> None:
    path = controller / ADAPTER
    text = path.read_text()
    tail = "    '550ac4def7d019213a345d1ddf348d3ff263118dc90a425ec091c4fcd47007cf',\n})"
    anchor = "MODULE_BINDINGS = {"
    clause = "    if actual != MODULE_BINDINGS[path] and not prior_runner_bindings:\n"
    if text.count(tail) != 1 or text.count(anchor) != 1 or text.count(clause) != 1:
        raise Refusal("adapter-anchors-moved")
    added = "".join(f"    '{digest}',\n" for digest in adapters)
    text = text.replace(tail, tail[:-2] + added + "})")
    literal = "PRIOR_MODULE_BINDINGS = frozenset({" + ", ".join(repr(row) for row in rows) + "})\n"
    text = text.replace(anchor, literal + anchor, 1)
    text = text.replace(clause, "    if actual != MODULE_BINDINGS[path] and not prior_runner_bindings and (path, actual, source_sha) not in PRIOR_MODULE_BINDINGS:\n")
    path.write_text(text)


def verify(controller: Path, replica: Path) -> tuple[int, str, int]:
    started = time.perf_counter_ns()
    completed = subprocess.run([sys.executable, str(controller / HEXCTL), "--dir", str(replica), "verify"],
                               stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT)
    elapsed = (time.perf_counter_ns() - started) // 1_000_000
    return completed.returncode, (completed.stdout + completed.stderr), elapsed


def state_digests(replica: Path) -> dict:
    return {name: sha((replica / ".hexaemeron" / name).read_bytes()) for name in ("state.json", "ledger.jsonl")}


def latest_gate_record(state: dict) -> dict:
    receipt = state["receipts"]["runbook"]
    amendments = receipt.get("amendments") or []
    return amendments[-1]["gate_commands"] if amendments else receipt["gate_commands"]


def unknown_adapter_refuses(controller: Path, replica: Path, state: dict, evidence: dict) -> bool:
    adapter = load(controller / ADAPTER, "resolve_adapter_" + controller.name.replace("-", "_"))
    data = (replica / ".hexaemeron" / "runbook.md").read_bytes()
    if sha(data) != state["receipts"]["runbook"]["sha256"]:
        raise Refusal("runbook-fixture-digest")
    forged = copy.deepcopy(latest_gate_record(state))
    forged["adapter_sha256"] = "0" * 64
    try:
        adapter.replay(replica.resolve(), data, forged)
    except adapter.Refusal as exc:
        evidence["refusal"] = str(exc)
        return True
    return False


def resolve(candidate: str, criterion: str, evidence: dict) -> object:
    with tempfile.TemporaryDirectory(prefix="fiat-2042-resolve-") as scratch:
        tmp = Path(scratch)
        replica, state = build_replica(tmp)
        base = state["base"]
        main = copy_controller(tmp, "main")
        current_adapter = load(main / ADAPTER, "resolve_current_adapter")
        rows_typed = 0
        if candidate == "base-commit-bindings":
            under_test = copy_controller(tmp, "candidate")
            base_adapter, rows = derive_rows(current_adapter, replica, base)
            latest = latest_gate_record(state)["adapter_sha256"]
            admitted = [base_adapter] if base_adapter == latest else []
            evidence["derived"] = {"base_adapter_sha256": base_adapter, "receipt_adapter_sha256": latest,
                                   "rows": rows}
            patch_adapter(under_test, admitted, rows)
        elif candidate == "reviewed-prior-pins":
            under_test = copy_controller(tmp, "candidate")
            rows_typed = 1 + len(LITERAL_ROWS)
            patch_adapter(under_test, [LITERAL_ADAPTER], list(LITERAL_ROWS))
        elif candidate == "runbook-scoped-pins":
            under_test = main
        else:
            under_test = base_controller(tmp, replica, base)
        evidence["controllers"] = {
            "main": {k: sha((main / k).read_bytes()) for k in (HEXCTL, ADAPTER)},
            "under_test": {k: sha((under_test / k).read_bytes()) for k in (HEXCTL, ADAPTER)},
        }
        if criterion == "reviewed-rows-per-release":
            return rows_typed
        if criterion == "main-controller-replays-1872":
            controller = main if candidate == "recorded-controller-fork" else under_test
            code, output, elapsed = verify(controller, replica)
            evidence["verify"] = {"exit": code, "output": output[-400:], "ms": elapsed}
            return code == 0 and output.startswith("ok:")
        if criterion in ("verify-writes-no-state", "verify-wall-ms"):
            before = state_digests(replica)
            code, output, elapsed = verify(under_test, replica)
            after = state_digests(replica)
            evidence["verify"] = {"exit": code, "output": output[-400:], "ms": elapsed}
            if criterion == "verify-wall-ms":
                return elapsed
            changed = 0
            for name, digest in before.items():
                if after[name] != digest:
                    changed += (replica / ".hexaemeron" / name).stat().st_size
            return changed
        if criterion == "edited-module-refuses":
            module = replica / PROTASIS
            module.write_bytes(module.read_bytes() + b"\nFIXTURE_EDIT = 1\n")
            code, output, elapsed = verify(under_test, replica)
            git(replica, "checkout", "--quiet", "--", PROTASIS)
            evidence["verify"] = {"exit": code, "output": output[-400:], "ms": elapsed}
            return code != 0 and "gate source stale or invalid" in output
        if criterion == "unknown-adapter-refuses":
            return unknown_adapter_refuses(under_test, replica, state, evidence)
    raise Refusal("unknown-criterion")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    report = Path(args.report)
    if os.path.lexists(report):
        print("report-already-exists", file=sys.stderr)
        return 1
    evidence: dict = {"candidate": args.candidate, "criterion": args.criterion, "run_head": RUN_HEAD,
                      "fixture": FIXTURE_DIGESTS}
    try:
        value = resolve(args.candidate, args.criterion, evidence)
    except (Refusal, subprocess.SubprocessError, OSError, ValueError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    evidence["value"] = value
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence" / f"{args.candidate}-{args.criterion}.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    payload = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": value,
        "unit": CRITERIA[args.criterion],
        "command": (f"python3 .hexaemeron/design/resolve.py --candidate {args.candidate} "
                    f"--criterion {args.criterion} --report {args.report}"),
        "exit": 0,
    }
    report.parent.mkdir(parents=True, exist_ok=True)
    with open(report, "x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"{args.candidate}/{args.criterion} = {value!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
