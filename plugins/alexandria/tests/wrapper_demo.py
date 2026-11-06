#!/usr/bin/env python3
"""Run the constructed #2092 wrapper specimen through `usdc_interval.py`'s CLI.

The specimen is `test_wildcat_wrappers.wrapper_state()`: the constructed V2
fixture with wrappers A and B declared in `wildcat_v2_wrappers`, each named by
one constructed `WrapperDeployed` log from the registry's wrapper factory.
Every record was constructed; none was observed on a chain.

`run` calls `usdc_interval.main` in this process for every command, with
`transport_from_environment` replaced by the fake transport from
`test_wildcat_venue.py` and socket construction refused, so collect and
reconcile reach no network. It has three parts:

1. collect, reconcile, build and check over the specimen, keeping build's
   release identifier and the `wrappers` listing check prints;
2. for each of the four refusal cases, collect, reconcile, build and check
   over the specimen changed to carry the case, stopping at the first
   command that exits non-zero; and
3. for each case, check over a copy of the specimen release in which one
   journal record is edited to carry the case. The copy is re-sealed, each
   object moved to the path its new digest names, so `verify` accepts it and
   the refusal is check's own.

The transcript keeps every command's argv, with paths relative to the run's
root, and its exit code, plus the `usdc-interval:` stderr lines of each
command that refuses; collect's progress lines carry timings and are
dropped. So the transcript is the same bytes on every run. `main` runs it in
a fresh temporary directory, which it removes, and prints it as JSON. It
exits 0 only when every specimen command exits 0 and every case refuses in
parts 2 and 3 with no release written in part 2. Any argument exits 2.
"""

from __future__ import annotations

from contextlib import ExitStack
import hashlib
import io
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
# Run as a script under `python3 -I` or PYTHONSAFEPATH=1, this file's
# directory is not on sys.path, and `tests.<name>` needs the plugin root.
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))

from tests import test_usdc_interval as existing  # noqa: E402
from tests import test_wildcat_venue as venue  # noqa: E402
from tests import test_wildcat_wrappers as wrappers  # noqa: E402
from alexandria_lib import release  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import OPENING_CLASS  # noqa: E402
import usdc_interval  # noqa: E402

TRANSCRIPT_FORMAT = "alexandria-2092-wrapper-demonstration/v1"
STAGES = ("collect", "reconcile", "build", "check")
CASES = (
    "unknown-market",
    "wrapper-without-code",
    "wrapper-log-before-its-epoch",
    "declared-wrapper-without-deployment",
)


class NoCodeTransport(venue.WildcatTransport):
    """The fake transport, answering every code read for wrapper A with empty code."""

    def code(self, address, number):
        return "0x" if address == wrappers.WRAPPER_A else super().code(address, number)


def case_state(case: str) -> tuple[dict, type]:
    """The specimen changed to carry one refusal case, and the transport class to answer it."""
    specimen = wrappers.wrapper_state()
    if case == "unknown-market":
        moved = wrappers.deployed(
            specimen, wrappers.STRANGER, wrappers.WRAPPER_A, wrappers.BLOCK_A, 2, 5,
        )
        state = wrappers.wrapper_state(drop={(wrappers.BLOCK_A, 5)}, extra=[moved])
        return state, venue.WildcatTransport
    if case == "wrapper-without-code":
        return specimen, NoCodeTransport
    if case == "wrapper-log-before-its-epoch":
        early = wrappers.native(specimen, wrappers.WRAPPER_A, wrappers.EARLY_BLOCK, 0, 0)
        return wrappers.wrapper_state(extra=[early]), venue.WildcatTransport
    if case == "declared-wrapper-without-deployment":
        return wrappers.wrapper_state(drop={(wrappers.BLOCK_B, 9)}), venue.WildcatTransport
    raise ValueError("unknown case: " + case)


def once(match):
    """A journal edit that applies `match(envelope, request)` until it first changes a record."""
    done = []

    def change(envelope, request):
        if done or not match(envelope, request):
            return False
        done.append(True)
        return True

    return change


def edited_log(case: str):
    """The `logs` edit for `case`: one log changed, the first one the case matches."""
    word = wrappers.word

    def match(envelope, _request):
        for record in envelope["result"]:
            topics = record["topics"]
            if case == "unknown-market" and topics[:3] == [
                wrappers.TOPIC, word(wrappers.OTHER_MARKET), word(wrappers.WRAPPER_A),
            ]:
                topics[1] = word(wrappers.STRANGER)
                return True
            if (case == "declared-wrapper-without-deployment" and topics[:1] == [wrappers.TOPIC]
                    and topics[2] == word(wrappers.WRAPPER_B)):
                topics[0] = wrappers.OTHER_TOPIC
                return True
            if (case == "wrapper-log-before-its-epoch"
                    and int(record["blockNumber"], 16) < wrappers.BLOCK_A
                    and record["address"] != wrappers.FACTORY):
                record["address"] = wrappers.WRAPPER_A
                return True
        return False

    return once(match)


def empty_code(envelope, request):
    """Answer wrapper A's preserved code read with empty code."""
    if request["method"] == "eth_getCode" and request["params"][0] == wrappers.WRAPPER_A:
        envelope["result"] = "0x"
        return True
    return False


def check_edit(case: str):
    """The journal component one case edits, and the edit."""
    if case == "wrapper-without-code":
        return OPENING_CLASS, once(empty_code)
    return "logs", edited_log(case)


def reseal(output: Path) -> None:
    """Re-record an edited release so that `verify` accepts it.

    Each component's object moves to the path its current digest names, the
    manifest records its size and digest, every capture follows its
    component, and the release identifier is recomputed. An object no
    component still names is removed, with its directory once that is empty.
    """
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digests, moved = {}, []
    for item in manifest["components"]:
        old = item["object_path"]
        data = (output / old).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        path = f"objects/sha256/{digest[:2]}/{digest}"
        if path != old:
            target = output / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            moved.append(old)
        item.update(object_path=path, bytes=len(data), sha256="sha256:" + digest)
        digests[item["name"]] = item["sha256"]
    named = {item["object_path"] for item in manifest["components"]}
    for old in moved:
        if old not in named:
            (output / old).unlink()
            if not any((output / old).parent.iterdir()):
                (output / old).parent.rmdir()
    for capture in manifest["captures"]:
        capture["component_sha256"] = digests[capture["component"]]
    identity = {key: value for key, value in manifest.items() if key != "release_id"}
    manifest["release_id"] = "sha256:" + hashlib.sha256(
        canonical_bytes(identity, max_nodes=release.MAX_MANIFEST_NODES)
    ).hexdigest()
    manifest_path.write_bytes(canonical_bytes(manifest, max_nodes=release.MAX_MANIFEST_NODES))


def edit_component(output: Path, name: str, change) -> None:
    """Apply `change` to one journal component of a built release, then re-seal the release."""
    path = existing.component_path(output, name)
    document = json.loads(path.read_text(encoding="utf-8"))
    wrappers.edit_journal(change)(document)
    path.write_bytes(canonical_bytes(document))
    reseal(output)


def refusal_lines(stderr: str) -> str:
    """The CLI's own `usdc-interval:` lines, without collect's timed progress lines."""
    return "\n".join(line for line in stderr.splitlines() if line.startswith("usdc-interval: "))


def fake_transport(transport_class, state):
    """A stand-in for `transport_from_environment` that answers from `state`."""
    def build(_timeout, environ=None):
        return transport_class(state)
    return build


def error_codes(staging: Path) -> list[str]:
    """The `code` of each failure receipt collect recorded under `staging`."""
    path = staging / "receipts" / "errors.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line)["code"] for line in path.read_text(encoding="utf-8").splitlines() if line]


class Demonstration:
    """One run's root, its registry file and the CLI calls made under it."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.registry_path = self.root / "registry.json"
        self.registry_path.write_bytes(canonical_bytes(venue.registry()))

    def relative(self, argument) -> str:
        if isinstance(argument, Path):
            return argument.relative_to(self.root).as_posix()
        return str(argument)

    def call(self, arguments, transport=None) -> dict:
        """`usdc_interval.main` in process with sockets refused: argv, exit, stdout, refusal."""
        out = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        err = io.StringIO()
        refused = AlexandriaError("socket construction refused")
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "stdout", out))
            stack.enter_context(mock.patch.object(sys, "stderr", err))
            stack.enter_context(mock.patch.object(socket, "socket", side_effect=refused))
            stack.enter_context(mock.patch.object(socket, "create_connection", side_effect=refused))
            if transport is not None:
                stack.enter_context(mock.patch.object(
                    usdc_interval, "transport_from_environment", side_effect=transport,
                ))
            code = usdc_interval.main([str(argument) for argument in arguments])
            out.flush()
        return {
            "argv": [self.relative(argument) for argument in arguments],
            "exit": code,
            "stdout": out.buffer.getvalue().decode("utf-8"),
            "refusal": refusal_lines(err.getvalue()),
        }

    def stages(self, name: str, state: dict, transport_class) -> list[dict]:
        """Collect, reconcile, build and check in a new directory `name`, stopping at the first refusal."""
        directory = self.root / name
        directory.mkdir()
        plan_path = directory / "plan.json"
        plan_path.write_bytes(canonical_bytes(state["plan"]))
        staging, output = directory / "staging", directory / "release"
        commands = {
            "collect": ["collect", "--plan", plan_path, "--staging", staging,
                        "--registry", self.registry_path],
            "reconcile": ["reconcile", "--plan", plan_path, "--staging", staging,
                          "--provider-class", venue.SECOND_PROVIDER,
                          "--registry", self.registry_path],
            "build": ["build", "--plan", plan_path, "--staging", staging,
                      "--registry", self.registry_path, "--created-at", venue.CREATED_AT,
                      "--output", output],
            "check": ["check", output],
        }
        calls = []
        for stage in STAGES:
            transport = None
            if stage in ("collect", "reconcile"):
                transport = fake_transport(transport_class, state)
            result = self.call(commands[stage], transport)
            calls.append(dict(result, stage=stage))
            if result["exit"] != 0:
                break
        return calls


def specimen_part(demo: Demonstration) -> dict:
    calls = demo.stages("specimen", wrappers.wrapper_state(), venue.WildcatTransport)
    record = {"commands": [call["argv"] for call in calls],
              "exits": [call["exit"] for call in calls]}
    if record["exits"] == [0] * len(STAGES):
        summary = json.loads(calls[-1]["stdout"])
        record.update(release_id=calls[2]["stdout"].strip(), check_release_id=summary["release_id"],
                      wrappers=summary["wrappers"])
    else:
        record["refusal"] = calls[-1]["refusal"]
    return record


def refusal_part(demo: Demonstration) -> list[dict]:
    rows = []
    for case in CASES:
        state, transport_class = case_state(case)
        name = "refusal-" + case
        calls = demo.stages(name, state, transport_class)
        last = calls[-1]
        rows.append({
            "case": case,
            "commands": [call["argv"] for call in calls],
            "exits": [call["exit"] for call in calls],
            "refused_at": last["stage"] if last["exit"] else None,
            "message": last["refusal"],
            "error_receipt_codes": error_codes(demo.root / name / "staging"),
            "release_written": (demo.root / name / "release").exists(),
        })
    return rows


def check_part(demo: Demonstration) -> list[dict]:
    rows = []
    source = demo.root / "specimen" / "release"
    for case in CASES:
        output = demo.root / ("check-" + case)
        shutil.copytree(source, output)
        component, change = check_edit(case)
        edit_component(output, component, change)
        result = demo.call(["check", output])
        rows.append({
            "case": case,
            "edited_component": component,
            "argv": result["argv"],
            "exit": result["exit"],
            "message": result["refusal"],
        })
    return rows


def run(root: Path) -> dict:
    """The three parts under `root`, an existing directory each part adds to."""
    demo = Demonstration(root)
    specimen = specimen_part(demo)
    return {
        "format": TRANSCRIPT_FORMAT,
        "specimen": specimen,
        "refusals": refusal_part(demo),
        "check_refusals": check_part(demo) if "wrappers" in specimen else [],
    }


def succeeded(transcript: dict) -> bool:
    """Every specimen command exited 0 and every case refused in parts 2 and 3."""
    return (
        transcript["specimen"]["exits"] == [0] * len(STAGES)
        and len(transcript["refusals"]) == len(CASES)
        and all(row["refused_at"] and not row["release_written"] for row in transcript["refusals"])
        and len(transcript["check_refusals"]) == len(CASES)
        and all(row["exit"] == 1 for row in transcript["check_refusals"])
    )


def main(argv: list[str] | None = None) -> int:
    if argv:
        print("usage: wrapper_demo.py (takes no arguments)", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="alexandria-2092-demo.") as raw:
        transcript = run(Path(raw))
    print(json.dumps(transcript, indent=2, sort_keys=True))
    return 0 if succeeded(transcript) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
