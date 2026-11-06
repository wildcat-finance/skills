#!/usr/bin/env python3
"""Check the published design home and replay its bounded selection specimens."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile


PACKAGE = "docs/protasis-success-criteria"
SELF = PACKAGE + "/proof.py"
CANDIDATES = ("controller-capture", "producer-report", "terminal-replay")
SELECTED = "controller-capture"
FUTURE = {
    "declaration-contract": 2,
    "execution-custody": 3,
    "terminal-compatibility": 4,
    "joined-demonstration": 5,
}
CRITERIA = ("design-home", *FUTURE)
SLUG = "settle-study-criteria-from-recorded-execution"
SELECTOR = "adr/" + SLUG
DRAFT = "docs/decisions/drafts/" + SLUG + ".md"
DECISION_SHA256 = "a6ec5f13bbdba6e96fea4025b5aa80f707d9285b809ccae12e7420a96b1f9c7b"
FROZEN = {
    "study.md": "2ff25685ea7e4f0c00b27f529ce901886156d46a5582ab7987c126105c64f3d4",
    "runbook.md": "bb36b579fe02a406519afd640e52d35d1c3583c5827cca790609933527ba6651",
    "design-evidence.json": "89938e2d649d73c98298ea70823282ed83d397b2e21c9b79cdd01e35184944f7",
    "selection_probe.py": "3f4b3c3de29084aa0accb047919cbfc7f7c4cb12c2d7118d3490cb48dac2bc8b",
    "evidence/opening-study.md": "4a572737afa69d9a24c5923a828b68398c3e1bb9d85045b1488d7b8a87e13e92",
}
DESIGN_CHECKER = "plugins/hexaemeron/skills/protasis/scripts/design_evidence.py"
BRIDGE_CHECKER = "plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py"
DECLARATION_SOURCE = "plugins/hexaemeron/skills/protasis/scripts/success_criteria.py"
PROTASIS_SOURCE = "plugins/hexaemeron/skills/protasis/scripts/protasis.py"
GATE_SOURCE = "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
STUDY_SOURCE = PACKAGE + "/study.md"
RUNBOOK_SOURCE = PACKAGE + "/runbook.md"
MAX_INPUT_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class Refusal(Exception):
    """Carry a bounded reason without copying input or exception text."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def relative_parts(value):
    if not isinstance(value, str) or len(value.encode("utf-8")) > 512:
        raise Refusal("unsafe-path")
    parts = PurePosixPath(value).parts
    if (not parts or value.startswith("/") or PurePosixPath(value).as_posix() != value
            or any(part in (".", "..") for part in parts)
            or re.fullmatch(r"[A-Za-z0-9_./-]+", value) is None):
        raise Refusal("unsafe-path")
    return parts


def open_directory(root, parts, *, create=False):
    descriptor = os.open(root, DIRECTORY_FLAGS)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            following = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def read_file(root, relative):
    parts = relative_parts(relative)
    directory = open_directory(root, parts[:-1])
    try:
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=directory)
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_INPUT_BYTES:
                raise Refusal("input-not-bounded-regular-file")
            data = stream.read(MAX_INPUT_BYTES + 1)
            after = os.fstat(stream.fileno())
            named = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
            identity = lambda item: (item.st_dev, item.st_ino, item.st_size,
                                     item.st_mtime_ns, item.st_ctime_ns)
            if (len(data) > MAX_INPUT_BYTES or identity(before) != identity(after)
                    or identity(after) != identity(named)):
                raise Refusal("input-changed-during-read")
            return data
    finally:
        os.close(directory)


class Inputs:
    def __init__(self, root):
        self.root = root
        self.bytes = {}

    def read(self, path, expected=None):
        data = read_file(self.root, path)
        if expected is not None and digest(data) != expected:
            raise Refusal("source-digest-mismatch")
        if path in self.bytes and self.bytes[path] != data:
            raise Refusal("source-changed")
        self.bytes[path] = data
        if sum(map(len, self.bytes.values())) > MAX_TOTAL_BYTES:
            raise Refusal("source-inventory-too-large")
        return data

    def recheck(self):
        for path, data in self.bytes.items():
            if read_file(self.root, path) != data:
                raise Refusal("source-changed")

    def inventory(self):
        return [{"path": path, "sha256": digest(data), "bytes": len(data)}
                for path, data in sorted(self.bytes.items())]


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check_design_home(root):
    """Return executed checks and their inputs; raise Refusal for an unmet join."""
    inputs = Inputs(root)
    inputs.read(SELF)
    python_version = inputs.read(".python-version").decode("ascii").strip()
    if python_version != ".".join(map(str, sys.version_info[:3])):
        raise Refusal("interpreter-version-mismatch")
    frozen = {name: inputs.read(PACKAGE + "/" + name, expected)
              for name, expected in FROZEN.items()}
    if not frozen["study.md"].startswith(frozen["evidence/opening-study.md"]):
        raise Refusal("opening-study-prefix-mismatch")
    inputs.read(DESIGN_CHECKER)
    inputs.read(BRIDGE_CHECKER)
    design = load_module(root / DESIGN_CHECKER, "criteria_design_checker")
    bridge = load_module(root / BRIDGE_CHECKER, "criteria_bridge_checker")
    findings = bridge.check_design_bridge(PACKAGE + "/study.md",
                                         PACKAGE + "/design-evidence.json", root)
    if findings:
        raise Refusal("design-home-join-refused:" + findings[0].code)
    home, home_path, error = bridge._read_stable_adr(root, SELECTOR)
    if home is None:
        raise Refusal("design-home-unavailable")
    relative = home_path.as_posix()
    home = inputs.read(relative)
    if relative == DRAFT:
        normalised = home
    elif re.fullmatch(r"docs/decisions/ADR-[0-9]{3}-" + SLUG + r"\.md", relative):
        normalised = re.sub(rb"\A# ADR-[0-9]{3}: ", b"# Decision: ", home, count=1)
    else:
        raise Refusal("design-home-outside-canonical-location")
    if digest(normalised) != DECISION_SHA256:
        raise Refusal("decision-content-drift")
    findings, record, consumed = design.evaluate(root / PACKAGE / "design-evidence.json",
                                                "design-lock")
    if findings:
        raise Refusal("selection-check-refused:" + findings[0].code)
    if record["selection"]["candidate"] != SELECTED:
        raise Refusal("selection-changed")
    selection_ids = {item["id"] for item in record["criteria"] if item["stage"] == "selection"}
    selection = [item for item in consumed if item["criterion"] in selection_ids]
    if len(selection) != 18:
        raise Refusal("selection-coverage-mismatch")
    reports = {}
    for row in selection:
        data = inputs.read(PACKAGE + "/" + row["path"], row["sha256"])
        reports[(row["candidate"], row["criterion"])] = json.loads(data)
    observations = []
    with tempfile.TemporaryDirectory(prefix="criteria-selection-") as scratch:
        directory = Path(scratch).resolve()
        probe_path = directory / "selection_probe.py"
        with probe_path.open("xb") as stream:
            stream.write(frozen["selection_probe.py"])
        (directory / "probe-tmp").mkdir()
        probe = load_module(probe_path, "criteria_selection_specimens")
        for candidate in CANDIDATES:
            actual = probe.specimens(candidate)
            if set(actual) != selection_ids:
                raise Refusal("selection-replay-coverage-mismatch")
            for criterion, (value, unit) in sorted(actual.items()):
                report = reports[(candidate, criterion)]
                if (type(value) is not type(report["value"]) or value != report["value"]
                        or unit != report["unit"]):
                    raise Refusal("selection-replay-mismatch")
                observations.append({"candidate": candidate, "criterion": criterion,
                                     "value": value, "unit": unit})
    inputs.recheck()
    return inputs, {
        "schema": "success-criteria-scaffold-evidence/v1",
        "scope": "Design-home join and policy specimens; later controller conformance remains separate.",
        "interpreter": {"path": sys.executable, "version": python_version},
        "sources": inputs.inventory(),
        "checks": [
            {"name": "hypomnema-design-bridge", "record": relative, "findings": []},
            {"name": "protasis-design-selection", "selected": SELECTED, "consumed": selection},
            {"name": "policy-specimen-replay", "observations": observations},
        ],
    }


def check_declaration_contract(root):
    """Exercise the pure declaration contract and the real inert adapter.

    Every source used by the adapter is read into the companion inventory. The
    checks operate on bytes and temporary Markdown specimens only; no target
    module is imported by the adapter and no registered command is launched.
    """
    inputs = Inputs(root)
    inputs.read(SELF)
    python_version = inputs.read(".python-version").decode("ascii").strip()
    if python_version != ".".join(map(str, sys.version_info[:3])):
        raise Refusal("interpreter-version-mismatch")
    study = inputs.read(STUDY_SOURCE)
    runbook = inputs.read(RUNBOOK_SOURCE)
    inputs.read(DECLARATION_SOURCE)
    inputs.read(PROTASIS_SOURCE)
    inputs.read(GATE_SOURCE)
    gates = load_module(root / GATE_SOURCE, "criteria_gate_commands")
    parser = load_module(root / DECLARATION_SOURCE, "criteria_success_criteria")
    for relative in gates.REGISTRY:
        inputs.read(relative)
    record = parser.parse(study)
    if record is None or len(record["criteria"]) != 8:
        raise Refusal("declaration-record-missing-or-incomplete")
    admission = gates.validate_with_criteria(root, study, runbook)
    joined = admission.get("join")
    if (not isinstance(joined, dict) or joined.get("schema") != parser.JOIN_SCHEMA
            or len(joined.get("criteria", [])) != len(record["criteria"])
            or admission.get("operation_ran") is not False):
        raise Refusal("adapter-declaration-join-invalid")

    observations = []
    malformed = b"```success-criteria\n{\"schema\":\"" + parser.SCHEMA.encode()
    malformed += b"\",\"criteria\":[]}\n```\n"
    try:
        parser.parse(malformed)
    except parser.Refusal as error:
        observations.append({"case": "empty-criteria", "reason": str(error)})
    else:
        raise Refusal("malformed-declaration-accepted")

    # A descriptor must name the active Exit field, not a Tests-only command or
    # the wrong consuming step.
    first = dict(record["criteria"][0])
    wrong_step = dict(first)
    wrong_step["step"] = 1 if first["step"] != 1 else 2
    try:
        parser.join({"schema": parser.SCHEMA, "criteria": [wrong_step]}, runbook)
    except parser.Refusal as error:
        observations.append({"case": "wrong-step", "reason": str(error)})
    else:
        raise Refusal("wrong-step-join-accepted")

    # The current runbook has accepted amendments. Prove that the latest
    # replacement is active and the previous literal is no longer admitted.
    amended = (
        "## Step 1: Amendment specimen\n\n"
        "**Goal.** Check.\n**Entry.** Clean.\n"
        "**Exit.** Run `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py old.md`.\n"
        "**Files.** `old.md`.\n**Tests.** Parser.\n**Disciplines.** none.\n\n"
        "### Amendment -- 2026-09-16\n\n"
        "**What changed.** Complete replacement Exit: Run `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py new.md`.\n"
        "**Why.** The fixture changed.\n**Steps touched.** Step 1.\n"
        "**Still holding.** Step 1: entry holds; exit holds.\n"
    )
    old = {"schema": parser.SCHEMA, "criteria": [{
        "id": "amended-old", "claim": "old", "step": 1,
        "command": "python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py old.md",
    }]}
    new = {"schema": parser.SCHEMA, "criteria": [{
        "id": "amended-new", "claim": "new", "step": 1,
        "command": "python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py new.md",
    }]}
    try:
        parser.join(old, amended)
    except parser.Refusal as error:
        observations.append({"case": "superseded-exit", "reason": str(error)})
    else:
        raise Refusal("superseded-exit-accepted")
    if len(parser.join(new, amended)["criteria"]) != 1:
        raise Refusal("amended-exit-not-effective")
    observations.append({
        "case": "adapter-admission",
        "criteria": len(joined["criteria"]),
        "commands": len(admission["gate_commands"]["commands"]),
        "declaration_sha256": admission["declaration_sha256"],
        "runbook_sha256": joined["runbook_sha256"],
        "adapter_sha256": admission["gate_commands"]["adapter_sha256"],
        "operation_ran": False,
    })
    inputs.recheck()
    return inputs, {
        "schema": "success-criteria-declaration-evidence/v1",
        "scope": "Pure bounded declaration parsing and inert effective-Exit admission.",
        "interpreter": {"path": sys.executable, "version": python_version},
        "sources": inputs.inventory(),
        "checks": observations,
    }


def check_execution_custody(root):
    """Exercise the bounded executor with real disposable child processes.

    This proof records process observations only.  It does not turn a fixture
    command into evidence for a Fiat run, and it does not claim semantic
    sufficiency for a declared criterion.
    """
    executor_path = PACKAGE.replace("docs/protasis-success-criteria", "plugins/hexaemeron/skills/fiat/scripts") + "/criteria_execution.py"
    controller_path = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
    if not (root / executor_path).is_file() or not (root / controller_path).is_file():
        raise Refusal("operation-not-implemented:execution-custody:step-3")
    inputs = Inputs(root)
    inputs.read(SELF)
    inputs.read(executor_path)
    # The controller is intentionally larger than the proof reader's 1 MiB
    # per-input budget.  Bind its exact bytes with a separate bounded stream;
    # this keeps the proof's inventory limit while still identifying the
    # controller that the demonstration inspected.
    controller = root / controller_path
    try:
        before = controller.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2 * 1024 * 1024:
            raise Refusal("controller-source-bound")
        with controller.open("rb") as stream:
            controller_bytes = stream.read(2 * 1024 * 1024 + 1)
        after = controller.stat()
    except OSError as error:
        raise Refusal("controller-source-unavailable") from error
    if len(controller_bytes) > 2 * 1024 * 1024 or before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
        raise Refusal("controller-source-changed")
    module = load_module(root / executor_path, "criteria_execution_proof")
    child = [sys.executable, "-c", "import sys; sys.stdout.write('proof-ok')"]
    success = module.execute_argv(child, root, timeout=2, stream_cap=1024)
    if success.get("status") != "completed" or success.get("returncode") != 0:
        raise Refusal("execution-success-case-unmet")
    failed = module.execute_argv(
        [sys.executable, "-c", "import sys; sys.exit(7)"],
        root, timeout=2, stream_cap=1024,
    )
    if failed.get("status") != "completed" or failed.get("returncode") != 7:
        raise Refusal("execution-exit-case-unmet")
    overflow = module.execute_argv(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 32)"],
        root, timeout=2, stream_cap=16,
    )
    if overflow.get("status") != "stream-overflow" or not overflow["stdout"]["truncated"]:
        raise Refusal("execution-overflow-case-unmet")
    inputs.recheck()
    return inputs, {
        "schema": "success-criteria-execution-evidence/v1",
        "scope": "Real child-process observations of bounded execution outcomes.",
        "controller": {"path": controller_path, "sha256": digest(controller_bytes), "bytes": len(controller_bytes)},
        "executor": {"path": executor_path, "sha256": digest(inputs.bytes[executor_path])},
        "checks": [
            {"case": "completed-zero", "result": success},
            {"case": "completed-exit-seven", "result": failed},
            {"case": "incremental-stream-overflow", "result": overflow},
        ],
        "sources": inputs.inventory(),
    }


def check_terminal_compatibility(root):
    """Exercise completion, amendment and read-only historical replay.

    The specimens use the real receipt adapter and a no-op result validator;
    they never invoke a registered Exit.  That distinction is recorded in the
    evidence so this resolver cannot accidentally claim a production run.
    """
    executor_path = "plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py"
    receipts_path = "plugins/hexaemeron/skills/fiat/scripts/criteria_receipts.py"
    controller_path = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
    if not all((root / path).is_file() for path in (executor_path, receipts_path, controller_path)):
        raise Refusal("operation-not-implemented:terminal-compatibility:step-4")
    inputs = Inputs(root)
    inputs.read(SELF)
    inputs.read(executor_path)
    inputs.read(receipts_path)
    controller = root / controller_path
    try:
        before = controller.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2 * 1024 * 1024:
            raise Refusal("controller-source-bound")
        with controller.open("rb") as stream:
            controller_bytes = stream.read(2 * 1024 * 1024 + 1)
        after = controller.stat()
    except OSError as error:
        raise Refusal("controller-source-unavailable") from error
    if (len(controller_bytes) > 2 * 1024 * 1024
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns):
        raise Refusal("controller-source-changed")
    receipts = load_module(root / receipts_path, "criteria_receipts_terminal_proof")
    command = "python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json"
    row = lambda identifier, claim, step, cmd: {
        "id": identifier, "claim": claim, "step": step, "command": cmd,
        "descriptor_sha256": "1" * 64,
        "exit": {"step": step, "command": cmd,
                 "command_sha256": hashlib.sha256(cmd.encode()).hexdigest()},
    }
    joined = {"schema": receipts.JOIN_SCHEMA, "declaration_sha256": "2" * 64,
              "runbook_sha256": "b" * 64,
              "criteria": [row("completed", "already observed", 4, command),
                           row("unbuilt", "still due", 4, command)]}
    admission = {"join": joined, "study_sha256": "a" * 64,
                 "runbook_sha256": "b" * 64}
    custody = receipts.new(admission)
    settled = {"attempt_id": "attempt-completed", "study_sha256": "a" * 64,
               "runbook_sha256": "b" * 64, "criterion_ids": ["completed"],
               "settled": True, "status": "settled"}
    checks = []
    try:
        receipts.require_complete(custody, [settled])
    except receipts.Refusal as error:
        checks.append({"case": "completion-refuses-gaps", "reason": str(error)})
    else:
        raise Refusal("completion-gap-accepted")
    changed = json.loads(json.dumps(joined))
    changed["criteria"][0]["command"] = command + " --changed"
    changed["criteria"][0]["exit"]["command"] = changed["criteria"][0]["command"]
    changed["criteria"][0]["exit"]["command_sha256"] = hashlib.sha256(
        changed["criteria"][0]["command"].encode()
    ).hexdigest()
    try:
        receipts.amend(custody, changed, study_sha256="a" * 64,
                       runbook_sha256="c" * 64, amendment_sha256="3" * 64,
                       attempts=[settled])
    except receipts.Refusal as error:
        checks.append({"case": "completed-descriptor-frozen", "reason": str(error)})
    else:
        raise Refusal("completed-descriptor-change-accepted")
    unrelated = json.loads(json.dumps(joined))
    unrelated["criteria"][1]["claim"] = "updated unbuilt claim"
    unrelated["criteria"][1]["descriptor_sha256"] = "4" * 64
    amended = receipts.amend(custody, unrelated, study_sha256="a" * 64,
                             runbook_sha256="c" * 64, amendment_sha256="3" * 64,
                             attempts=[settled])
    checks.append({"case": "unrelated-amendment-preserved", "versions": len(amended["versions"])})
    try:
        receipts.amend(amended, unrelated, study_sha256="a" * 64,
                       runbook_sha256="d" * 64, amendment_sha256="3" * 64,
                       attempts=[settled])
    except receipts.Refusal as error:
        checks.append({"case": "duplicate-amendment-refused", "reason": str(error)})
    else:
        raise Refusal("duplicate-amendment-accepted")
    launches = []
    def validator(attempt, historical_join, **kwargs):
        launches.append(attempt["attempt_id"])
        if historical_join["schema"] != receipts.JOIN_SCHEMA:
            raise Refusal("replay-join")
        return attempt
    complete = dict(settled)
    complete["attempt_id"] = "attempt-unbuilt"
    complete["criterion_ids"] = ["unbuilt"]
    complete["study_sha256"] = "a" * 64
    complete["runbook_sha256"] = "c" * 64
    terminal = receipts.terminal(amended, [settled, complete],
                                 run_id="run-proof", validator=validator)
    receipts.validate_terminal(terminal, amended, [settled, complete],
                               validator=validator)
    if len(launches) != 4:
        raise Refusal("replay-validator-count")
    checks.append({"case": "replay-preserves-bindings", "validator_calls": len(launches),
                   "operation_ran": terminal["operation_ran"]})
    wrong = dict(complete)
    wrong["runbook_sha256"] = "e" * 64
    try:
        receipts.version_for_attempt(amended, wrong)
    except receipts.Refusal as error:
        checks.append({"case": "wrong-source-refused", "reason": str(error)})
    else:
        raise Refusal("wrong-source-accepted")
    # A legacy receipt has no declaration or history and remains outside this
    # adapter; there is deliberately no conversion path here.
    try:
        receipts.history({"schema": "legacy"})
    except receipts.Refusal as error:
        checks.append({"case": "legacy-no-backfill", "reason": str(error)})
    else:
        raise Refusal("legacy-backfill-accepted")
    inputs.recheck()
    return inputs, {
        "schema": "success-criteria-terminal-evidence/v1",
        "scope": "Read-only completion and historical receipt compatibility specimens.",
        "controller": {"path": controller_path, "sha256": digest(controller_bytes),
                       "bytes": len(controller_bytes)},
        "executor": {"path": executor_path, "sha256": digest(inputs.bytes[executor_path])},
        "receipts": {"path": receipts_path, "sha256": digest(inputs.bytes[receipts_path])},
        "inspection_launches": 0,
        "checks": checks,
        "sources": inputs.inventory(),
    }


def check_joined_demonstration(root):
    """Run the successor controller in a disposable Git-backed fixture.

    The earlier criteria proofs deliberately exercise inert adapters.  This
    proof crosses that boundary once: it starts the checked-in controller in
    a separate repository, records a real ``run-exit`` observation when a
    signed fixture commit is available, and keeps every refusal bounded.  A
    small unsigned fixture is used by copy-mode tests; those tests still run
    the controller's init/readback surface and use the same execution adapter
    with signature checking disabled, but cannot publish a joined proof.
    No fixture output is treated as a semantic judgement about the criterion.
    """
    controller_path = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
    executor_path = "plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py"
    receipts_path = "plugins/hexaemeron/skills/fiat/scripts/criteria_receipts.py"
    gate_path = "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
    criteria_path = "plugins/hexaemeron/skills/protasis/scripts/success_criteria.py"
    protasis_path = "plugins/hexaemeron/skills/protasis/scripts/protasis.py"
    required = (controller_path, executor_path, receipts_path, gate_path,
                criteria_path, protasis_path)
    if not all((root / path).is_file() for path in required):
        raise Refusal("operation-not-implemented:joined-demonstration:step-5")

    inputs = Inputs(root)
    inputs.read(SELF)
    for path in (executor_path, receipts_path, gate_path, criteria_path,
                 protasis_path):
        inputs.read(path)
    controller = root / controller_path
    try:
        before = controller.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 2 * 1024 * 1024:
            raise Refusal("controller-source-bound")
        with controller.open("rb") as stream:
            controller_bytes = stream.read(2 * 1024 * 1024 + 1)
        after = controller.stat()
    except OSError as error:
        raise Refusal("controller-source-unavailable") from error
    if (len(controller_bytes) > 2 * 1024 * 1024
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns):
        raise Refusal("controller-source-changed")

    executor = load_module(root / executor_path, "criteria_demonstration_execution")
    receipts = load_module(root / receipts_path, "criteria_demonstration_receipts")
    gate = load_module(root / gate_path, "criteria_demonstration_gate")

    def git_call(directory, *argv, check=False):
        try:
            return subprocess.run(
                ["git", "-C", str(directory), "-c", "commit.gpgsign=false", *argv],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=check,
                timeout=20,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise Refusal("fixture-git-unavailable") from error

    def controller_call(directory, *argv):
        command = [sys.executable, str(controller), "--dir", str(directory), *argv]
        return executor.execute_argv(command, directory, timeout=20, stream_cap=65536)

    def result_ok(value):
        return (isinstance(value, dict) and value.get("status") == "completed"
                and value.get("returncode") == 0)

    def refusal_case(name, operation):
        try:
            operation()
        except (Refusal, receipts.Refusal, executor.Refusal, ValueError, OSError) as error:
            return {"case": name, "refused": True, "reason": str(error)}
        raise Refusal(name + "-accepted")

    def copy_design_record(worktree):
        source_record = root / PACKAGE / "design-evidence.json"
        if not source_record.is_file():
            raise Refusal("fixture-design-evidence-unavailable")
        target_root = worktree / ".hexaemeron"
        target_root.mkdir(parents=True, exist_ok=True)
        record = json.loads(source_record.read_bytes())
        target_record = target_root / "design-evidence.json"
        target_record.write_bytes(encoded(record))
        for item in record.get("results", []):
            reference = item.get("report") if isinstance(item, dict) else None
            if not isinstance(reference, dict):
                continue
            relative = reference.get("path")
            if not isinstance(relative, str):
                raise Refusal("fixture-design-report-reference")
            source = source_record.parent / relative
            destination = target_record.parent / relative
            if not source.is_file():
                raise Refusal("fixture-design-report-unavailable")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

    def build_fixture(base, *, shared_clone):
        """Return a controller worktree and bounded controller readback."""
        if shared_clone:
            origin = base / "origin"
            process = git_call(origin.parent, "clone", "--shared", "--no-tags",
                               str(root), str(origin))
            if process.returncode != 0:
                raise Refusal("fixture-clone-refused")
            # A local clone made from a feature worktree need not have ``main``
            # checked out.  The branch is only a disposable integration base.
            process = git_call(origin, "branch", "-f", "main", "HEAD")
            if process.returncode != 0:
                raise Refusal("fixture-main-branch-unavailable")
        else:
            origin = base / "origin"
            origin.mkdir(parents=True, exist_ok=True)
            process = git_call(origin, "init", "-q", "-b", "main")
            if process.returncode != 0:
                raise Refusal("fixture-git-init-refused")
            for path in (controller_path, executor_path, receipts_path,
                         gate_path, criteria_path, protasis_path):
                source = root / path
                destination = origin / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            (origin / "runbook.md").write_text(
                "# Runbook\n\n## Step 1: Demonstrate\n\n"
                "**Goal.** Demonstrate.\n**Entry.** Ready.\n"
                "**Exit.** Run `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --format json runbook.md`.\n"
                "**Files.** `runbook.md`.\n**Tests.** Run `python3 -m unittest`.\n"
                "**Disciplines.** bounded fixture.\n",
                encoding="utf-8",
            )
            git_call(origin, "config", "user.name", "Fixture")
            git_call(origin, "config", "user.email", "fixture@example.invalid")
            git_call(origin, "add", ".")
            process = git_call(origin, "commit", "-q", "-m", "fixture source")
            if process.returncode != 0:
                raise Refusal("fixture-source-commit-refused")
        for name, value in (("user.name", "Fixture"),
                            ("user.email", "fixture@example.invalid"),
                            ("commit.gpgsign", "false")):
            git_call(origin, "config", "--local", name, value, check=True)
        init = controller_call(
            origin, "init", "--topic", "joined-demonstration", "--base", "main"
        )
        if not result_ok(init):
            raise Refusal("controller-init-refused")
        crumb = origin / ".hexaemeron" / "worktree"
        try:
            worktree = Path(crumb.read_text(encoding="utf-8").strip()).resolve(strict=True)
        except (OSError, ValueError) as error:
            raise Refusal("controller-worktree-readback") from error
        return origin, worktree, init

    def configure_fixture_signing(origin, base, *, shared_clone):
        """Keep the temporary signer and trust file inside fixture custody."""
        if not shared_clone:
            return False
        tool = shutil.which("ssh-keygen", path=os.pathsep.join(
            ("/usr/bin", "/bin", "/usr/local/bin", "/opt/homebrew/bin")
        ))
        if tool is None:
            return False
        key = base / "signer"
        try:
            tool = str(Path(tool).resolve(strict=True))
            generated = subprocess.run(
                [tool, "-q", "-t", "ed25519", "-N", "", "-C",
                 "fixture@example.invalid", "-f", str(key)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=False, timeout=20,
            )
            if generated.returncode != 0:
                return False
            with key.with_suffix(".pub").open("r", encoding="ascii") as stream:
                public_key = stream.read(4097)
            if len(public_key) > 4096:
                raise Refusal("fixture-public-key-bound")
            signers = base / "allowed-signers"
            signers.write_text(
                'fixture@example.invalid namespaces="git" ' + public_key,
                encoding="ascii",
            )
        except (OSError, UnicodeError, subprocess.SubprocessError):
            return False
        for name, value in (("gpg.format", "ssh"),
                            ("user.signingkey", str(key)),
                            ("gpg.ssh.program", tool),
                            ("gpg.ssh.allowedSignersFile", str(signers))):
            git_call(origin, "config", "--local", name, value, check=True)
        return True

    def create_study_and_runbook(origin, worktree, signing_ready):
        copy_design_record(worktree)
        command = (
            "python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py "
            "--format json runbook.md"
        )
        study = (
            "# Study\n\n"
            "```risk-register\n"
            "demo-boundary | execution | controller fixture\n"
            "```\n\n"
            "```success-criteria\n"
            + json.dumps({
                "schema": "protasis-success-criteria/v1",
                "criteria": [
                    {"id": "demo-positive", "claim": "controller observes the effective Exit",
                     "step": 1, "command": command},
                    {"id": "demo-shared", "claim": "a shared Exit settles each descriptor once",
                     "step": 1, "command": command},
                    {"id": "demo-vacuous", "claim": "a passing command does not prove semantic sufficiency",
                     "step": 1, "command": command},
                ],
            }, sort_keys=True)
            + "\n```\n"
        )
        (worktree / "study.md").write_text(study, encoding="utf-8")
        done_study = controller_call(
            worktree, "done", "study", "--artifact", "study.md"
        )
        if not result_ok(done_study):
            raise Refusal("controller-study-refused")
        try:
            state = json.loads((worktree / ".hexaemeron" / "state.json").read_bytes())
            design = state["receipts"]["study"]["design_evidence"]
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise Refusal("controller-study-readback") from error
        runbook = (
            "# Runbook\n\n"
            "```design-lock\n"
            f"schema | {design['schema']}\n"
            f"sha256 | {design['sha256']}\n"
            f"candidate | {design['selected']}\n"
            "```\n\n"
            "## Step 1: Demonstrate\n\n"
            "**Goal.** Demonstrate the controller.\n"
            "**Entry.** The disposable source is committed.\n"
            f"**Exit.** Run `{command}`.\n"
            "**Files.** `runbook.md`.\n"
            "**Tests.** Run `python3 -m unittest`.\n"
            "**Disciplines.** bounded fixture.\n"
        )
        (worktree / "runbook.md").write_text(runbook, encoding="utf-8")
        (worktree / "steps.json").write_text('["Demonstrate"]\n', encoding="utf-8")
        done_runbook = controller_call(
            worktree, "done", "runbook", "--artifact", "runbook.md",
            "--steps-file", "steps.json"
        )
        if not result_ok(done_runbook):
            raise Refusal("controller-runbook-refused")
        # Source snapshots require a clean tree.  The controller state is
        # ignored by the fixture, while these three source files are committed
        # as one signed (or explicitly unsigned fallback) implementation base.
        git_call(worktree, "add", "study.md", "runbook.md", "steps.json")
        signed = None
        if signing_ready:
            signed = git_call(
                worktree, "-c", "commit.gpgsign=true", "commit", "-S",
                "-m", "fixture implementation source",
            )
        if signed is None or signed.returncode != 0:
            unsigned = git_call(worktree, "commit", "--no-gpg-sign", "-m",
                                "fixture implementation source")
            if unsigned.returncode != 0:
                raise Refusal("fixture-implementation-commit-refused")
            signed_commit = False
        else:
            signed_commit = True
        head = git_call(worktree, "rev-parse", "HEAD")
        if head.returncode != 0:
            raise Refusal("fixture-head-readback")
        commit = head.stdout.strip()
        state = json.loads((worktree / ".hexaemeron" / "state.json").read_bytes())
        title = state["steps"][0]["title"]
        tail = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:32] or "untitled"
        branch = f"{state['run_branch']}-step-1-{tail}"
        if git_call(worktree, "branch", branch, commit).returncode != 0:
            raise Refusal("fixture-step-branch-refused")
        if git_call(worktree, "checkout", "-q", branch).returncode != 0:
            raise Refusal("fixture-step-checkout-refused")
        return command, state, commit, branch, signed_commit

    # A shared clone gives the real path a signed parent from the checked-in
    # tree.  Copy-mode tests do not have a Git parent to clone, so use a tiny
    # unsigned repository and keep signature absence visible in the readback.
    shared_clone = (root / ".git").exists() and (root / PACKAGE / "design-evidence.json").is_file()
    with tempfile.TemporaryDirectory(prefix="criteria-joined-") as scratch:
        base = Path(scratch).resolve()
        origin, worktree, init_result = build_fixture(base, shared_clone=shared_clone)
        signing_ready = configure_fixture_signing(origin, base, shared_clone=shared_clone)
        command, state, implementation_commit, branch, signed_commit = create_study_and_runbook(
            origin, worktree, signing_ready
        )
        calls = [{"case": "controller-init", "result": init_result}]

        missing = controller_call(worktree, "next")
        if not result_ok(missing):
            raise Refusal("controller-next-readback")
        calls.append({"case": "missing-execution-readback", "result": missing})

        withheld = controller_call(
            worktree, "done", "implement", "--branch", branch,
            "--commit", implementation_commit,
        )
        if withheld.get("returncode") == 0:
            raise Refusal("withholding-integration-accepted")
        calls.append({"case": "withholding-integration", "result": withheld})

        join = state["receipts"]["runbook"]["success_criteria"]["join"]
        run_id = state["receipts"]["runbook"]["success_criteria"].get("run_id")
        # The controller derives these two values from its immutable receipts.
        ledger = json.loads((worktree / ".hexaemeron" / "ledger.jsonl").read_text().splitlines()[0])
        init_id = "init-" + ledger["hash"]
        study_sha = state["receipts"]["study"]["sha256"]
        runbook_sha = state["receipts"]["runbook"]["sha256"]

        wrong_criterion = controller_call(worktree, "run-exit", "--criterion", "missing")
        if wrong_criterion.get("returncode") == 0:
            raise Refusal("wrong-criterion-accepted")
        calls.append({"case": "wrong-criterion", "result": wrong_criterion})

        positive = None
        if signed_commit:
            positive = controller_call(
                worktree, "run-exit", "--criterion", "demo-positive"
            )
            if not result_ok(positive):
                raise Refusal("controller-positive-execution-refused")
            state = json.loads((worktree / ".hexaemeron" / "state.json").read_bytes())
            attempts = state["receipts"]["runbook"]["success_criteria"]["attempts"]
            if len(attempts) != 1 or attempts[0].get("status") != "settled":
                raise Refusal("controller-positive-settlement-missing")
            positive_attempt = attempts[0]
            run_id = positive_attempt["run_id"]
            init_id = positive_attempt["init_id"]
            join = state["receipts"]["runbook"]["success_criteria"]["join"]
            calls.append({"case": "positive-execution", "result": positive})
        else:
            # Signature availability is a property of the disposable host,
            # never a reason to fabricate a signed receipt.  The same adapter
            # still executes the admitted command with that requirement off.
            admission = executor.admit(worktree, (worktree / "study.md").read_bytes(),
                                       (worktree / "runbook.md").read_bytes())
            admission["study_sha256"] = study_sha
            admission["runbook_sha256"] = runbook_sha
            positive_attempt = executor.execute(
                worktree, admission["join"], "demo-positive", run_id="fixture-run",
                init_id="fixture-init", step=1, require_signed=False,
                study_sha256=study_sha, runbook_sha256=runbook_sha,
            )
            if not positive_attempt.get("settled"):
                raise Refusal("adapter-positive-settlement-missing")
            # An unsigned adapter observation is not a controller settlement
            # or a replayable terminal receipt. Keep the published proof gated.
            raise Refusal("unsigned-fixture-not-admitted")

        wrong_step = refusal_case(
            "wrong-step",
            lambda: executor.execute(
                worktree, join, "demo-positive", run_id=run_id, init_id=init_id,
                step=2, require_signed=False, study_sha256=study_sha,
                runbook_sha256=runbook_sha,
            ),
        )
        wrong_command_join = json.loads(json.dumps(join))
        row = wrong_command_join["criteria"][0]
        row["command"] = row["command"] + " --changed"
        row["exit"]["command"] = row["command"]
        row["exit"]["command_sha256"] = digest(row["command"].encode())
        wrong_command = refusal_case(
            "wrong-command",
            lambda: executor.execute(
                worktree, wrong_command_join, "demo-positive", run_id=run_id,
                init_id=init_id, step=1, require_signed=False,
                study_sha256=study_sha, runbook_sha256=runbook_sha,
            ),
        )
        bad_source = json.loads(json.dumps(positive_attempt))
        bad_source["study_sha256"] = "0" * 64
        wrong_source = refusal_case(
            "wrong-source",
            lambda: executor.validate_result(
                bad_source, join, run_id=run_id, init_id=init_id,
                study_sha256=study_sha,
            ),
        )

        nonzero = executor.execute_argv(
            [sys.executable, "-c", "import sys; sys.exit(7)"],
            worktree, timeout=2, stream_cap=1024,
        )
        timeout = executor.execute_argv(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            worktree, timeout=0.1, stream_cap=1024,
        )
        overflow = executor.execute_argv(
            [sys.executable, "-c", "import sys; sys.stdout.write('x' * 2048)"],
            worktree, timeout=2, stream_cap=64,
        )
        interrupted = executor.execute_argv(
            [sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"],
            worktree, timeout=2, stream_cap=1024,
        )
        if nonzero.get("returncode") != 7 or timeout.get("status") != "timeout" \
                or overflow.get("status") != "stream-overflow" \
                or interrupted.get("returncode", 0) >= 0:
            raise Refusal("execution-negative-cases-unmet")

        stale_join = json.loads(json.dumps(join))
        stale_join["criteria"][0]["claim"] = "changed completed claim"
        stale = refusal_case(
            "stale-amendment",
            lambda: receipts.amend(
                receipts.new({"join": join, "study_sha256": study_sha,
                              "runbook_sha256": runbook_sha}),
                stale_join, study_sha256=study_sha, runbook_sha256="1" * 64,
                amendment_sha256="2" * 64, attempts=[positive_attempt],
            ),
        )
        legacy = refusal_case("legacy-receipt", lambda: receipts.history({"schema": "legacy"}))
        terminal = receipts.terminal(
            receipts.new({"join": join, "study_sha256": study_sha,
                          "runbook_sha256": runbook_sha}),
            [positive_attempt], run_id=run_id,
            validator=executor.validate_result, init_id=init_id,
        )
        receipts.validate_terminal(
            terminal,
            receipts.new({"join": join, "study_sha256": study_sha,
                          "runbook_sha256": runbook_sha}),
            [positive_attempt], validator=executor.validate_result,
            init_id=init_id,
        )
        if terminal.get("operation_ran") is not False:
            raise Refusal("checkpoint-replay-executed")

        checks = [
            {"case": "wrong-step", "result": wrong_step},
            {"case": "wrong-command", "result": wrong_command},
            {"case": "wrong-source", "result": wrong_source},
            {"case": "nonzero-exit", "result": nonzero},
            {"case": "timeout", "result": timeout},
            {"case": "stream-overflow", "result": overflow},
            {"case": "interrupted", "result": interrupted},
            {"case": "stale-amendment", "result": stale},
            {"case": "marker-present-inert", "contracts": state.get("contracts", {})},
            {"case": "legacy-receipt", "result": legacy},
            {"case": "checkpoint-replay", "operation_ran": terminal["operation_ran"],
             "attempt_count": terminal["attempt_count"]},
            {"case": "shared-descriptors", "criterion_ids": positive_attempt["criterion_ids"]},
            {"case": "vacuous-success", "controller_settled": True,
             "semantic_sufficiency": False},
        ]
        inputs.recheck()
        return inputs, {
            "schema": "success-criteria-joined-demonstration-evidence/v1",
            "scope": "Separate controller execution and bounded refusal readback in a disposable Git-backed fixture.",
            "controller": {
                "path": controller_path,
                "sha256": digest(controller_bytes),
                "bytes": len(controller_bytes),
                "source": {
                    "commit": implementation_commit,
                    "branch": branch,
                    "signed": signed_commit,
                },
                "readback": {
                    "status": init_result["status"],
                    "returncode": init_result["returncode"],
                    "stdout": init_result["stdout"],
                    "stderr": init_result["stderr"],
                },
            },
            "fixture": {
                "kind": "git-backed-disposable",
                "origin": str(origin),
                "worktree": str(worktree),
                "source_commit": implementation_commit,
                "source_signed": signed_commit,
            },
            "source_command": {
                "command": positive_attempt["command"],
                "command_sha256": positive_attempt["command_sha256"],
                "criterion_ids": positive_attempt["criterion_ids"],
                "study_sha256": positive_attempt["study_sha256"],
                "runbook_sha256": positive_attempt["runbook_sha256"],
                "source_before": positive_attempt["source_before"],
                "source_after": positive_attempt["source_after"],
            },
            "controller_calls": calls,
            "checks": checks,
            "terminal": {
                "schema": terminal["schema"],
                "operation_ran": terminal["operation_ran"],
                "attempt_count": terminal["attempt_count"],
            },
            "inspection_launches": 0,
            "actual_counts": {
                "controller_calls": len(calls),
                "execution_invocations": len(positive_attempt["invocations"]),
                "inspection_launches": 0,
            },
            "exclusions": [
                "The command result does not establish criterion sufficiency.",
                "The vacuous success case is retained as a passing observation, not a semantic grade.",
                "Remote GitHub and deployment surfaces are fixture boundaries and were not contacted.",
            ],
            "sources": inputs.inventory(),
        }


def output_paths(report):
    parts = relative_parts(report)
    if (len(parts) != 3 or parts[:2] != (".hexaemeron", "reports")
            or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,95}\.json", parts[-1]) is None):
        raise Refusal("report-outside-fixed-directory")
    return parts[-1], parts[-1][:-5] + ".evidence.json"


def require_absent(directory, names):
    for name in names:
        try:
            os.stat(name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            continue
        raise Refusal("report-already-exists")


def write_exclusive(directory, name, data):
    descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o644, dir_fd=directory)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(directory)


def run(root, candidate, criterion, report_path):
    """Write a fresh design report and companion evidence after the checks pass."""
    if criterion == "execution-custody":
        if candidate != SELECTED:
            raise Refusal("candidate-not-selected")
        names = output_paths(report_path)
        directory = open_directory(root, (".hexaemeron", "reports"), create=True)
        try:
            require_absent(directory, names)
            inputs, evidence = check_execution_custody(root)
            command = ("python3 " + SELF + " --candidate " + candidate
                       + " --criterion " + criterion + " --report " + report_path)
            report = {"schema": "protasis-design-report/v1", "candidate": candidate,
                      "criterion": criterion, "value": True, "unit": "boolean",
                      "command": command, "exit": 0}
            report_bytes = encoded(report)
            evidence["report"] = {"path": report_path, "sha256": digest(report_bytes)}
            inputs.recheck()
            require_absent(directory, names)
            write_exclusive(directory, names[1], encoded(evidence))
            inputs.recheck()
            write_exclusive(directory, names[0], report_bytes)
            return report
        finally:
            os.close(directory)
    if criterion == "terminal-compatibility":
        if candidate != SELECTED:
            raise Refusal("candidate-not-selected")
        names = output_paths(report_path)
        directory = open_directory(root, (".hexaemeron", "reports"), create=True)
        try:
            require_absent(directory, names)
            inputs, evidence = check_terminal_compatibility(root)
            command = ("python3 " + SELF + " --candidate " + candidate
                       + " --criterion " + criterion + " --report " + report_path)
            report = {"schema": "protasis-design-report/v1", "candidate": candidate,
                      "criterion": criterion, "value": True, "unit": "boolean",
                      "command": command, "exit": 0}
            report_bytes = encoded(report)
            evidence["report"] = {"path": report_path, "sha256": digest(report_bytes)}
            inputs.recheck()
            require_absent(directory, names)
            write_exclusive(directory, names[1], encoded(evidence))
            inputs.recheck()
            write_exclusive(directory, names[0], report_bytes)
            return report
        finally:
            os.close(directory)
    if criterion == "joined-demonstration":
        if candidate != SELECTED:
            raise Refusal("candidate-not-selected")
        names = output_paths(report_path)
        directory = open_directory(root, (".hexaemeron", "reports"), create=True)
        try:
            require_absent(directory, names)
            inputs, evidence = check_joined_demonstration(root)
            command = ("python3 " + SELF + " --candidate " + candidate
                       + " --criterion " + criterion + " --report " + report_path)
            report = {"schema": "protasis-design-report/v1", "candidate": candidate,
                      "criterion": criterion, "value": True, "unit": "boolean",
                      "command": command, "exit": 0}
            report_bytes = encoded(report)
            evidence["report"] = {"path": report_path, "sha256": digest(report_bytes)}
            inputs.recheck()
            require_absent(directory, names)
            write_exclusive(directory, names[1], encoded(evidence))
            inputs.recheck()
            write_exclusive(directory, names[0], report_bytes)
            return report
        finally:
            os.close(directory)
    if criterion not in ("design-home", "declaration-contract") and criterion in FUTURE:
        raise Refusal("operation-not-implemented:" + criterion + ":step-" + str(FUTURE[criterion]))
    if criterion not in ("design-home", "declaration-contract"):
        raise Refusal("unknown-operation")
    if candidate != SELECTED:
        raise Refusal("candidate-not-selected")
    names = output_paths(report_path)
    directory = open_directory(root, (".hexaemeron", "reports"), create=True)
    try:
        require_absent(directory, names)
        if criterion == "design-home":
            inputs, evidence = check_design_home(root)
        else:
            inputs, evidence = check_declaration_contract(root)
        command = ("python3 " + SELF + " --candidate " + candidate
                   + " --criterion " + criterion + " --report " + report_path)
        report = {"schema": "protasis-design-report/v1", "candidate": candidate,
                  "criterion": criterion, "value": True, "unit": "boolean",
                  "command": command, "exit": 0}
        report_bytes = encoded(report)
        evidence["report"] = {"path": report_path, "sha256": digest(report_bytes)}
        inputs.recheck()
        require_absent(directory, names)
        write_exclusive(directory, names[1], encoded(evidence))
        inputs.recheck()
        write_exclusive(directory, names[0], report_bytes)
        return report
    finally:
        os.close(directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=CANDIDATES, required=True)
    parser.add_argument("--criterion", choices=CRITERIA, required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).absolute().parents[2]
    try:
        report = run(root, args.candidate, args.criterion, args.report)
    except Refusal as error:
        reason = str(error)
    except (OSError, ValueError, KeyError, AssertionError, RuntimeError, subprocess.SubprocessError):
        reason = "input-or-execution-unavailable"
    else:
        print(json.dumps(report, sort_keys=True))
        return 0
    print(json.dumps({"event": "success-criteria-proof-refused", "candidate": args.candidate,
                      "criterion": args.criterion, "reason": reason}, sort_keys=True))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
