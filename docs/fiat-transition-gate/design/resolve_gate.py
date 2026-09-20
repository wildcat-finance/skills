#!/usr/bin/env python3
"""Measure one design candidate against one selection criterion.

Issue wildcat-finance/skills#871: every Fiat mutation must prove the Promise
that authorises it. Each candidate below is a reference construction for the
gate, the state and ledger writer, and the exhausted-audit-loop exit. It is
evaluated over a disposable run directory holding a synthetic preimage shaped
like the #622 incident: 43 hash-chained ledger entries, step 2 halted after
audit round 8 with 30 findings open. The exact #622 bytes are not in the
repository, so nothing here claims to replay them.

The candidate `per-handler-gate` keeps the controller's writer unchanged, so
its recovery cell drives the real `commit` function loaded from
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` in the current checkout. The
call-site metric parses the same file. Every other value is measured from the
reference procedures in this file. They model the constructions named in the
study. They are not the product controller, and a passing cell establishes only
that the construction answers the specimen as the criterion requires.

usage: resolve_gate.py --candidate ID --criterion ID --out PATH

`--out` is required, must not exist, must end in `.json`, and may not name a
controller file. Nothing else is written outside a private temporary
directory. No network is used and no shell is spawned.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "protasis-design-report/v1"
CONTROLLER_FILES = frozenset({"state.json", "ledger.jsonl", "lock"})
HEXCTL = Path("plugins/hexaemeron/skills/fiat/scripts/hexctl.py")
HEXCTL_MAX = 8 * 1024 * 1024
CHILD_TIMEOUT = 60
LOOP_MAX = 8

CANDIDATES = {
    # writer, continuation, needs a second OS identity, gate call sites
    "dispatcher-grant-wal": ("wal", True, False, "dispatcher"),
    "per-handler-gate": ("controller-commit", True, False, "handlers"),
    "external-writer-broker": ("child-wal", True, True, "dispatcher"),
    "gate-with-replacement-exit": ("wal", False, False, "dispatcher"),
}

CRITERIA = {
    "refuses-622-widening": "boolean",
    "appends-loop-two-same-ledger": "boolean",
    "legacy-loop-one-bytes-identical": "boolean",
    "runs-under-one-account-stdlib": "boolean",
    "crash-window-labelled": "boolean",
    "added-processes-per-mutation": "count",
    "max-grant-bytes": "bytes",
    "gate-call-sites": "count",
}

SPAWNED = [0]


class Refusal(Exception):
    """A stable gate refusal raised before any byte is written."""


class Crash(Exception):
    """An injected stop at one named writer boundary."""


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ------------------------------------------------------------ the specimen


def ledger_entry(event: str, data: dict, prev: str, state_hash: str) -> dict:
    entry = {"ts": "2026-08-27T18:19:23Z", "event": event, "data": data,
             "prev": prev, "state": state_hash}
    entry["hash"] = sha(canonical(entry))
    return entry


def specimen_state() -> dict:
    rounds = [{"round": n, "findings": 30 if n == LOOP_MAX else 31 + n}
              for n in range(1, LOOP_MAX + 1)]
    return {
        "version": 1,
        "phase": "steps",
        "current_step": 2,
        "config": {"audit": {"max_rounds": LOOP_MAX, "fold": False,
                             "log_path": "audit/rounds/specimen.md"},
                   "git": {"base": "main"}},
        "halted": {"reason": "audit verdict: 30 findings open", "ts": "x"},
        "steps": [{"n": 1, "phase": "done", "audit": {"rounds": []}},
                  {"n": 2, "phase": "audit", "audit": {"rounds": rounds}}],
    }


def write_specimen(root: Path) -> None:
    home = root / ".hexaemeron"
    home.mkdir()
    state = specimen_state()
    prev, lines = "genesis", []
    for index in range(43):
        entry = ledger_entry(f"specimen-{index}", {"n": index}, prev,
                             sha(canonical(state)))
        prev = entry["hash"]
        lines.append(json.dumps(entry, sort_keys=True))
    (home / "ledger.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (home / "state.json").write_text(json.dumps(state, indent=2) + "\n",
                                     encoding="utf-8")


def read_pair(root: Path) -> tuple[bytes, bytes]:
    home = root / ".hexaemeron"
    return (home / "state.json").read_bytes(), (home / "ledger.jsonl").read_bytes()


def load(root: Path) -> tuple[dict, list[dict]]:
    state_bytes, ledger_bytes = read_pair(root)
    entries = [json.loads(line) for line in ledger_bytes.decode().splitlines() if line]
    prev = "genesis"
    for entry in entries:
        body = {key: entry[key] for key in entry if key != "hash"}
        if entry["prev"] != prev or sha(canonical(body)) != entry["hash"]:
            raise Refusal("preimage-ledger-broken")
        prev = entry["hash"]
    state = json.loads(state_bytes)
    if entries[-1]["state"] != sha(canonical(state)):
        raise Refusal("preimage-state-mismatch")
    return state, entries


# ------------------------------------------------------- the reference gate


def loops_of(step: dict) -> list[list[dict]]:
    audit = step["audit"]
    return [audit["rounds"]] + [item["rounds"] for item in audit.get("continuations", [])]


def directive(state: dict) -> dict:
    if state.get("halted"):
        return {"do": "halted"}
    step = next(item for item in state["steps"] if item["n"] == state["current_step"])
    loops = loops_of(step)
    rounds = loops[-1]
    if not rounds:
        return {"do": "audit-round", "loop": len(loops), "round": 1}
    if rounds[-1]["findings"] == 0:
        return {"do": "close-audit"}
    if len(rounds) >= LOOP_MAX:
        return {"do": "audit-verdict", "loop": len(loops)}
    return {"do": "audit-round", "loop": len(loops), "round": len(rounds) + 1}


def exhausted(state: dict) -> bool:
    unhalted = dict(state, halted=None)
    return directive(unhalted)["do"] == "audit-verdict"


def gate(candidate: str, state: dict, entries: list[dict], command: dict) -> dict:
    """Return one exact grant or raise one stable refusal. Writes nothing."""
    name = command["name"]
    promise, transition = {
        "config-set": ("fiat-receipted-delivery", "config-set"),
        "resume": ("fiat-receipted-delivery", "clear-halt"),
        "start-audit-loop": ("fiat-audit-loop-continuation", "append-loop"),
        "audit-round": ("fiat-receipted-delivery", "append-round"),
    }.get(name, (None, None))
    if promise is None:
        raise Refusal("unknown-command")
    if name == "config-set":
        path = command["path"]
        if path != "audit.log_path" and path != "git" and not path.startswith("git."):
            raise Refusal("config-path-immutable")
    if name == "resume":
        if not state.get("halted"):
            raise Refusal("not-halted")
        if exhausted(state) and command.get("to") != "audit-verdict":
            raise Refusal("exhausted-loop-resume-needs-named-exit")
    if name == "start-audit-loop":
        if not CANDIDATES[candidate][1]:
            raise Refusal("transition-unsupported-by-controller")
        if not exhausted(state):
            raise Refusal("loop-not-exhausted")
        if command.get("authority") is None or command.get("checkpoint") is None:
            raise Refusal("authority-or-checkpoint-missing")
    if name == "audit-round":
        current = directive(state)
        if current["do"] != "audit-round" or command["round"] != current["round"]:
            raise Refusal("round-not-authorised")
    return {
        "schema": "fiat-transition-grant/v1",
        "promise": promise,
        "consequence": 2,
        "transition": transition,
        "directive": directive(state),
        "state_sha256": sha(canonical(state)),
        "ledger_tail": entries[-1]["hash"],
        "ledger_count": len(entries),
        "command": command,
    }


def apply(state: dict, grant: dict) -> tuple[dict, str, dict]:
    after = copy.deepcopy(state)
    command = grant["command"]
    if grant["transition"] == "append-loop":
        step = next(item for item in after["steps"] if item["n"] == after["current_step"])
        prior = loops_of(step)
        step["audit"].setdefault("continuations", []).append({
            "loop": len(prior) + 1,
            "max_rounds": LOOP_MAX,
            "rounds": [],
            "predecessor_sha256": sha(canonical(prior[-1])),
            "checkpoint": command["checkpoint"],
            "authority": command["authority"],
            "open_findings": prior[-1][-1]["findings"],
        })
        after["halted"] = None
        return after, "audit-loop-start", {"loop": len(prior) + 1}
    if grant["transition"] == "append-round":
        step = next(item for item in after["steps"] if item["n"] == after["current_step"])
        loops_of(step)[-1].append({"round": command["round"], "findings": 5})
        return after, "audit-round", {"round": command["round"]}
    if grant["transition"] == "config-set":
        node = after["config"]
        parts = command["path"].split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = command["value"]
        return after, "config-set", {"path": command["path"]}
    raise Refusal("transition-has-no-reference-effect")


# ----------------------------------------------------------- the writers


def wal_write(root: Path, after: dict, event: str, data: dict,
              entries: list[dict], grant: dict, crash_at: str | None = None) -> None:
    """Stage both postimages and one label, then publish, then retire."""
    home = root / ".hexaemeron"
    entry = ledger_entry(event, data, entries[-1]["hash"], sha(canonical(after)))
    ledger_next = (home / "ledger.jsonl").read_bytes() + (
        json.dumps(entry, sort_keys=True) + "\n").encode()
    state_next = (json.dumps(after, indent=2) + "\n").encode()
    pending = home / "pending-transition"
    staging = home / "pending-transition.staging"
    staging.mkdir()
    (staging / "state.next").write_bytes(state_next)
    (staging / "ledger.next").write_bytes(ledger_next)
    (staging / "grant.json").write_text(canonical(grant), encoding="utf-8")
    if crash_at == "staged":
        raise Crash(crash_at)
    os.replace(staging, pending)
    if crash_at == "labelled":
        raise Crash(crash_at)
    os.replace(pending / "ledger.next", home / "ledger.jsonl")
    if crash_at == "ledger-published":
        raise Crash(crash_at)
    os.replace(pending / "state.next", home / "state.json")
    if crash_at == "state-published":
        raise Crash(crash_at)
    (pending / "grant.json").unlink()
    pending.rmdir()


def wal_recover(root: Path) -> str:
    """Finish a labelled transaction or report the exact preimage."""
    home = root / ".hexaemeron"
    staging = home / "pending-transition.staging"
    pending = home / "pending-transition"
    if staging.exists():
        for child in staging.iterdir():
            child.unlink()
        staging.rmdir()
        return "preimage"
    if not pending.exists():
        return "clean"
    if (pending / "ledger.next").exists():
        os.replace(pending / "ledger.next", home / "ledger.jsonl")
    if (pending / "state.next").exists():
        os.replace(pending / "state.next", home / "state.json")
    (pending / "grant.json").unlink()
    pending.rmdir()
    return "completed"


def controller_module():
    path = repo_root() / HEXCTL
    if path.is_symlink() or not path.is_file() or path.stat().st_size > HEXCTL_MAX:
        raise SystemExit("resolve_gate: controller source is unavailable")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("hexctl_under_measure", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["hexctl_under_measure"] = module
    spec.loader.exec_module(module)
    return module


def child_wal_write(root: Path, after: dict, event: str, data: dict) -> None:
    """Stand in for a broker: the write happens in another process."""
    SPAWNED[0] += 1
    payload = canonical({"root": str(root), "after": after, "event": event, "data": data})
    code = (
        "import json,sys;sys.dont_write_bytecode=True;"
        "sys.path.insert(0,sys.argv[1]);import resolve_gate as r;"
        "from pathlib import Path;p=json.loads(sys.stdin.read());"
        "root=Path(p['root']);s,e=r.load(root);"
        "r.wal_write(root,p['after'],p['event'],p['data'],e,{'broker':True})"
    )
    done = subprocess.run(
        [sys.executable, "-c", code, str(Path(__file__).resolve().parent)],
        input=payload.encode(), capture_output=True, timeout=CHILD_TIMEOUT, check=False,
    )
    if done.returncode != 0:
        raise SystemExit("resolve_gate: broker stand-in failed")


def mutate(candidate: str, root: Path, command: dict, crash_at: str | None = None,
           writer: str | None = None) -> dict:
    state, entries = load(root)
    grant = gate(candidate, state, entries, command)
    after, event, data = apply(state, grant)
    writer = writer or CANDIDATES[candidate][0]
    if writer == "wal":
        wal_write(root, after, event, data, entries, grant, crash_at)
    elif writer == "child-wal":
        child_wal_write(root, after, event, data)
    else:
        module = controller_module()
        if crash_at is not None:
            def stop(*_args, **_kwargs):
                raise Crash(crash_at)
            module.save_state = stop
        module.commit(str(root), after, event, data)
    return grant


# -------------------------------------------------------------- criteria

START = {"name": "start-audit-loop", "authority": "user: one further bounded loop",
         "checkpoint": "0" * 64}


def with_specimen(function):
    with tempfile.TemporaryDirectory(prefix="fiat-871-design-") as raw:
        root = Path(raw).resolve()
        write_specimen(root)
        return function(root)


def refuses_widening(candidate: str) -> bool:
    def run(root: Path) -> bool:
        before = read_pair(root)
        hostile = (
            {"name": "config-set", "path": "audit.max_rounds", "value": 16},
            {"name": "config-set", "path": "audit", "value": {"max_rounds": 16}},
            {"name": "resume", "note": "the user said continue as round 9"},
            {"name": "audit-round", "round": 9},
            {"name": "widen-loop"},
        )
        for command in hostile:
            try:
                mutate(candidate, root, command)
            except Refusal:
                if read_pair(root) != before:
                    return False
                continue
            return False
        return True
    return with_specimen(run)


def loop_two(candidate: str) -> tuple[bool, bool]:
    """Return (loop 2 works on the same ledger, loop 1 bytes identical)."""
    def run(root: Path) -> tuple[bool, bool]:
        state, entries = load(root)
        legacy = canonical(state["steps"][1]["audit"]["rounds"])
        try:
            mutate(candidate, root, START)
        except Refusal:
            after, _ = load(root)
            return False, canonical(after["steps"][1]["audit"]["rounds"]) == legacy
        after, later = load(root)
        same_ledger = (len(later) == len(entries) + 1
                       and later[:len(entries)] == entries)
        opened = directive(after) == {"do": "audit-round", "loop": 2, "round": 1}
        for number in range(1, LOOP_MAX + 1):
            mutate(candidate, root, {"name": "audit-round", "round": number})
        ninth_refused = False
        try:
            mutate(candidate, root, {"name": "audit-round", "round": 9})
        except Refusal:
            ninth_refused = True
        final, _ = load(root)
        identical = canonical(final["steps"][1]["audit"]["rounds"]) == legacy
        verdict = directive(final) == {"do": "audit-verdict", "loop": 2}
        return same_ledger and opened and ninth_refused and verdict, identical
    return with_specimen(run)


def permitted(candidate: str) -> dict:
    """One command every candidate grants at the specimen."""
    if CANDIDATES[candidate][1]:
        return START
    return {"name": "config-set", "path": "audit.log_path",
            "value": "audit/rounds/specimen-2.md"}


def crash_window_labelled(candidate: str) -> bool:
    """Stop the candidate's writer at each boundary and classify the bytes."""
    writer = CANDIDATES[candidate][0]
    boundaries = ("staged", "labelled", "ledger-published", "state-published")
    if writer == "controller-commit":
        # The controller's writer has one window: ledger appended, state not.
        boundaries = ("ledger-published",)
    if writer == "child-wal":
        # The broker stand-in runs the staged writer; its windows are measured
        # in this process so a stop can be injected.
        writer = "wal"
    for boundary in boundaries:
        def run(root: Path, boundary=boundary) -> bool:
            before = read_pair(root)
            try:
                mutate(candidate, root, permitted(candidate), boundary, writer)
            except Crash:
                pass
            home = root / ".hexaemeron"
            labelled = (home / "pending-transition").exists() or (
                home / "pending-transition.staging").exists()
            if not labelled:
                return read_pair(root) == before
            wal_recover(root)
            try:
                load(root)
            except Refusal:
                return False
            return not (home / "pending-transition").exists()
        if not with_specimen(run):
            return False
    return True


def one_account(candidate: str) -> bool:
    needs_second_identity = CANDIDATES[candidate][2]
    if not needs_second_identity:
        return True
    # A broker only isolates when it runs under an identity the agent cannot
    # write as. Without privilege this process cannot obtain one.
    can_switch = hasattr(os, "geteuid") and os.geteuid() == 0
    return bool(can_switch)


def processes(candidate: str) -> int:
    SPAWNED[0] = 0
    with_specimen(lambda root: mutate(candidate, root, permitted(candidate)))
    return SPAWNED[0]


def grant_bytes(candidate: str) -> int:
    def run(root: Path) -> int:
        state, entries = load(root)
        return len(canonical(gate(candidate, state, entries, permitted(candidate))).encode())
    return with_specimen(run)


def call_sites(candidate: str) -> int:
    if CANDIDATES[candidate][3] == "dispatcher":
        return 1
    source = (repo_root() / HEXCTL).read_text(encoding="utf-8")
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and getattr(node.targets[0], "id", None) == "MUTATING"):
            names = ast.literal_eval(node.value.args[0])
            return len(names)
    raise SystemExit("resolve_gate: MUTATING was not found")


def measure(candidate: str, criterion: str):
    if criterion == "refuses-622-widening":
        return refuses_widening(candidate)
    if criterion == "appends-loop-two-same-ledger":
        return loop_two(candidate)[0]
    if criterion == "legacy-loop-one-bytes-identical":
        return loop_two(candidate)[1]
    if criterion == "runs-under-one-account-stdlib":
        return one_account(candidate)
    if criterion == "crash-window-labelled":
        return crash_window_labelled(candidate)
    if criterion == "added-processes-per-mutation":
        return processes(candidate)
    if criterion == "max-grant-bytes":
        return grant_bytes(candidate)
    return call_sites(candidate)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--candidate", required=True, choices=sorted(CANDIDATES))
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    if out.suffix != ".json" or out.name in CONTROLLER_FILES:
        print("resolve_gate: --out must be a .json report, not a controller file",
              file=sys.stderr)
        return 2
    value = measure(args.candidate, args.criterion)
    report = {
        "schema": SCHEMA,
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": value,
        "unit": CRITERIA[args.criterion],
        "command": (f"python3 .hexaemeron/design/resolve_gate.py --candidate "
                    f"{args.candidate} --criterion {args.criterion} --out {args.out}"),
        "exit": 0,
    }
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        descriptor = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    except FileExistsError:
        print("resolve_gate: --out exists; a report is never overwritten", file=sys.stderr)
        return 2
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
