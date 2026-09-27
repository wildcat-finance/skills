#!/usr/bin/env python3
"""Resolve the pending conformance cells of the skills#1944 design record.

Run from the repository root with the exact resolver a cell names:

    python3 docs/deferred-runner-binding/proof.py --candidate creating-step-binding \
        --criterion <criterion> \
        --report .hexaemeron/reports/creating-step-binding-<criterion>.json

The step that builds a criterion's product adds its handler to HANDLERS.
Until then the criterion refuses with a named reason and writes nothing. A
handler returns one typed value; this script wraps it in one closed
protasis-design-report/v1 object and creates the report exclusively, so an
existing entry at the report path is never replaced.

Step 2 adds three handlers, each an executed check of the checked-in adapter:
the adapter test module run in this process, a replay of receipts captured by
each admitted released adapter read from Git, and the median of five timed
validations of the committed success-criteria runbook.

Step 3 adds the controller-binding-custody handler. It runs the controller
test module in this process; each case drives the checked-in controller
through a disposable Git fixture with fake delivery tools, never a live run.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest


PACKAGE = "docs/deferred-runner-binding"
SELF = PACKAGE + "/proof.py"
RECORD = PACKAGE + "/design-evidence.json"
RECORD_SHA256 = "2ee92a4119378e5cfd8e7a6455ceebe850cd222f821fd6c75fd98d194c3aba22"
REPORT_SCHEMA = "protasis-design-report/v1"
SELECTED = "creating-step-binding"
CANDIDATES = (
    "creating-step-binding",
    "reviewed-stdlib-runner",
    "runbook-embedded-source",
    "pre-placed-untracked",
)
# The runbook step that adds each criterion's handler. The record's stop point
# is one step later, because a step:N cell is due when step N-1 pushes.
CRITERIA = {
    "validator-deferred-contract": 2,
    "released-adapter-replay": 2,
    "successor-replay-milliseconds": 2,
    "controller-binding-custody": 3,
    "joined-demonstration": 4,
}
# criterion -> callable(root: Path) returning the value for the criterion's unit.
HANDLERS: dict = {}
FLAGS = ("--candidate", "--criterion", "--report")
USAGE = ("usage: python3 " + SELF + " --candidate <candidate> --criterion <criterion>"
         " --report .hexaemeron/reports/<candidate>-<criterion>.json")
EVENT = "deferred-runner-proof-refused"
REPORT_DIRECTORY = (".hexaemeron", "reports")
MAX_RECORD_BYTES = 256 * 1024
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC

ADAPTER = "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
VALIDATOR_TESTS = "plugins/hexaemeron/tests/test_gate_deferred_registration.py"
# The evidence validator-deferred-contract names, one test each. Every other
# test in the module must pass as well.
CONTRACT_TESTS = (
    "AbsentPathWalkTests.test_missing_component_or_leaf_is_absent_and_never_read",
    "UnboundCommandTests.test_unbound_invocations_record_the_deferred_result_without_reading",
    "AbsentPathWalkTests.test_existing_leaf_of_each_type_is_present",
    "AbsentPathWalkTests.test_linked_or_non_directory_parent_is_unsafe",
    "DeferredRowGrammarTests.test_step_one_is_the_only_deferred_value",
    "PlacementTests.test_deferred_row_added_after_step_one_starts_refuses",
    "PlacementTests.test_deferred_row_after_binding_refuses_until_a_digest_row_replaces_it",
    "DeferredRowGrammarTests.test_escaping_paths_overrides_and_bounds_refuse_for_deferred_rows",
    "BindingTests.test_binding_yields_the_pinned_interface_result",
    "BindingTests.test_changed_bound_file_refuses_source_drift",
)
CONTROLLER_TESTS = "plugins/hexaemeron/tests/test_gate_deferred_binding.py"
# The evidence controller-binding-custody names, one test each. Every other
# test in the module must pass as well.
CUSTODY_TESTS = (
    "Unbound.test_awaiting_binding",
    "Binding.test_push_binds_blob",
    "Refusal.test_present_at_base",
    "Refusal.test_absent_at_head",
    "Refusal.test_link",
    "Refusal.test_submodule",
    "Refusal.test_worktree_mismatch",
    "Verify.test_later_edit",
    "Checkpoint.test_after_binding",
    "Checkpoint.test_before_binding",
    "Verify.test_digest_amendment",
    "Legacy.test_unmarked_run",
)
STARTING_COMMIT = "e992a54b4e3e4671bae98b448d57690de8dfa044"
# Each admitted released adapter with the commit that shipped it.
RELEASED_ADAPTERS = (
    (STARTING_COMMIT, "14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad"),
    ("6f4312c3ba706c1df88f535967d2d59e184c1f79",
     "6f50cd844a3543aa7ef05fc6631c72ba2fd91aab44ad3f06d62bb4f7312682de"),
)
MAX_SOURCE_BYTES = 2 * 1024 * 1024
GIT_SECONDS = 60
TIMED_RUNBOOK = "docs/protasis-success-criteria/runbook.md"
TIMED_SAMPLES = 5
LOCAL_CLI = "scripts/verify.py"
LOCAL_PROGRAM = b"""import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--count', type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    return args
"""
# Every built-in the admitted adapters pin alike, and one pinned local row.
# No Ephoros command: the 1.6.84 adapter pins a later ephoros.py.
REPLAY_COMMANDS = (
    "python3 scripts/run_checks.py --base main --scope root --format json",
    "for file in README.md AGENTS.md; do python3 "
    "plugins/brevitas/skills/brevitas/scripts/brevitas.py \"$file\"; done",
    "python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py runbook.md --gate-root .",
    "python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py README.md",
    "python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests",
    "python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md",
    "python3 " + LOCAL_CLI + " --root . --count 2",
)


class Refusal(Exception):
    """Carry one fixed reason token; never input text or exception detail."""


def parse(argv):
    """Accept exactly the three flags, each once, each followed by its value."""
    if len(argv) != 2 * len(FLAGS):
        raise Refusal("argument-not-closed")
    values = {}
    for flag, value in zip(argv[0::2], argv[1::2]):
        if flag not in FLAGS or flag in values:
            raise Refusal("argument-not-closed")
        values[flag] = value
    return values["--candidate"], values["--criterion"], values["--report"]


def report_name(candidate, criterion):
    return candidate + "-" + criterion + ".json"


def resolver(candidate, criterion):
    """Return the exact resolver string the design record holds for the cell."""
    return ("python3 " + SELF + " --candidate " + candidate + " --criterion " + criterion
            + " --report " + "/".join(REPORT_DIRECTORY) + "/" + report_name(candidate, criterion))


def check_cell(candidate, criterion, report):
    if candidate not in CANDIDATES:
        raise Refusal("unknown-candidate")
    if criterion not in CRITERIA:
        raise Refusal("unknown-criterion")
    if candidate != SELECTED:
        raise Refusal("candidate-not-selected")
    if report != "/".join(REPORT_DIRECTORY) + "/" + report_name(candidate, criterion):
        raise Refusal("report-not-cell-path")


def open_report_directory(root, *, create):
    """Walk .hexaemeron/reports without following links; None when absent."""
    descriptor = os.open(root, DIRECTORY_FLAGS)
    try:
        for part in REPORT_DIRECTORY:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            try:
                following = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            except FileNotFoundError:
                if create:
                    raise
                os.close(descriptor)
                return None
            except OSError:
                raise Refusal("report-directory-unsafe") from None
            os.close(descriptor)
            descriptor = following
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def require_absent(root, name):
    """Refuse when any entry, a link included, already holds the report path."""
    directory = open_report_directory(root, create=False)
    if directory is None:
        return
    try:
        os.stat(name, dir_fd=directory, follow_symlinks=False)
    except FileNotFoundError:
        return
    finally:
        os.close(directory)
    raise Refusal("report-already-exists")


def write_exclusive(root, name, data):
    directory = open_report_directory(root, create=True)
    try:
        try:
            descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                                 | os.O_CLOEXEC, 0o644, dir_fd=directory)
        except FileExistsError:
            raise Refusal("report-already-exists") from None
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            # The exclusive create made this entry ours, so a partial report goes.
            os.unlink(name, dir_fd=directory)
            raise
    finally:
        os.close(directory)


def read_record(root):
    """Read the committed design record, bounded and without following links."""
    *parents, leaf = RECORD.split("/")
    try:
        directory = os.open(root, DIRECTORY_FLAGS)
        try:
            for part in parents:
                following = os.open(part, DIRECTORY_FLAGS, dir_fd=directory)
                os.close(directory)
                directory = following
            descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                                 | os.O_CLOEXEC, dir_fd=directory)
        finally:
            os.close(directory)
    except OSError:
        raise Refusal("design-record-unavailable") from None
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise Refusal("design-record-not-regular-file")
        data = stream.read(MAX_RECORD_BYTES + 1)
    if hashlib.sha256(data).hexdigest() != RECORD_SHA256:
        raise Refusal("design-record-digest-mismatch")
    return json.loads(data)


def pending_unit(record, candidate, criterion):
    """Return the unit of the one pending cell whose resolver this run is."""
    rows = [row for row in record["results"]
            if row["candidate"] == candidate and row["criterion"] == criterion]
    definitions = [item for item in record["criteria"] if item["id"] == criterion]
    if (len(rows) != 1 or len(definitions) != 1 or rows[0].get("state") != "pending"
            or rows[0].get("resolver") != resolver(candidate, criterion)
            or rows[0].get("report") != "reports/" + report_name(candidate, criterion)
            or definitions[0]["stage"] != "conformance"):
        raise Refusal("design-record-cell-mismatch")
    return definitions[0]["unit"]


def value_matches(value, unit):
    if unit == "boolean":
        return type(value) is bool
    if unit == "milliseconds":
        return type(value) is int and value >= 0
    return False


def resolve(root, candidate, criterion, report):
    """Check the cell, run its handler and create its report, or refuse."""
    check_cell(candidate, criterion, report)
    name = report_name(candidate, criterion)
    require_absent(root, name)
    handler = HANDLERS.get(criterion)
    if handler is None:
        raise Refusal("operation-not-implemented:" + criterion + ":step-" + str(CRITERIA[criterion]))
    unit = pending_unit(read_record(root), candidate, criterion)
    value = handler(root)
    if not value_matches(value, unit):
        raise Refusal("handler-value-outside-unit")
    result = {"schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion,
              "value": value, "unit": unit, "command": resolver(candidate, criterion), "exit": 0}
    write_exclusive(root, name, (json.dumps(result, indent=2, sort_keys=True) + "\n").encode())
    return result


def regular_path(root, relative):
    """Return root/relative only when no component is a link and the leaf is a file."""
    current = Path(root)
    parts = relative.split("/")
    for index, part in enumerate(parts):
        current = current / part
        try:
            mode = os.lstat(current).st_mode
        except OSError:
            raise Refusal("source-unavailable") from None
        expected = stat.S_ISREG if index == len(parts) - 1 else stat.S_ISDIR
        if not expected(mode):
            raise Refusal("source-unavailable")
    return current


def read_tree_file(root, relative, cap=MAX_SOURCE_BYTES):
    path = regular_path(root, relative)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    except OSError:
        raise Refusal("source-unavailable") from None
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise Refusal("source-unavailable")
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise Refusal("source-over-cap")
    return data


def load_path(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise Refusal("module-unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_tree_module(root, relative, name):
    return load_path(regular_path(root, relative), name)


def git_blob(root, commit, relative):
    """Read one blob by a fixed full commit and path; argv only, bounded, no shell."""
    environment = {"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C"}
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "cat-file", "blob", commit + ":" + relative],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=environment, timeout=GIT_SECONDS, check=False)
    except (OSError, subprocess.SubprocessError):
        raise Refusal("released-adapter-unavailable") from None
    if completed.returncode != 0 or len(completed.stdout) > MAX_SOURCE_BYTES:
        raise Refusal("released-adapter-unavailable")
    return completed.stdout


def released_adapter(root, scratch, commit, expected):
    """Load a released adapter from Git only after its bytes match the reviewed digest."""
    data = git_blob(root, commit, ADAPTER)
    if hashlib.sha256(data).hexdigest() != expected:
        raise Refusal("released-adapter-digest-mismatch")
    path = Path(scratch) / ("released-" + expected[:12]) / "gate_commands.py"
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    return load_path(path, "deferred_runner_released_" + expected[:12])


class ContractResult(unittest.TestResult):
    """Record the id of each test that passed outright."""

    def __init__(self):
        super().__init__()
        self.passed = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed.append(test.id().split(".", 1)[1])


def module_passed(module, contract):
    """True only when every test ran and passed, the named contract tests included."""
    result = ContractResult()
    unittest.defaultTestLoader.loadTestsFromModule(module).run(result)
    return (result.testsRun > 0 and result.wasSuccessful() and not result.skipped
            and not result.expectedFailures and len(result.passed) == result.testsRun
            and set(contract) <= set(result.passed))


def validator_deferred_contract(root):
    """Run the adapter test module; true only when every test, the contract's included, passed."""
    module = load_tree_module(root, VALIDATOR_TESTS, "deferred_runner_validator_tests")
    return module_passed(module, CONTRACT_TESTS)


def controller_binding_custody(root):
    """Run the controller test module; true only when every test, the custody's included, passed.

    The module imports its sibling fixture harness, so its directory joins the
    import path while it loads and runs, and leaves it afterwards.
    """
    path = regular_path(root, CONTROLLER_TESTS)
    directory = str(path.parent)
    sys.path.insert(0, directory)
    try:
        module = load_path(path, "deferred_runner_controller_tests")
        return module_passed(module, CUSTODY_TESTS)
    finally:
        sys.path.remove(directory)


def replay_runbook(local_digest):
    """A runbook with no deferred row, a pinned local row and one superseded Exit."""
    exits = " and ".join("`" + command + "`" for command in REPLAY_COMMANDS)
    return ("```command-interfaces\nschema | protasis-command-interfaces/v1\n"
            + LOCAL_CLI + " | main | " + local_digest + "\n```\n\n"
            "## Step 1: Gate\n\n**Exit.** " + exits + "\n\n"
            "**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 "
            "--elenchus-report {report}`; format: `unittest-json-v1`; "
            "report file: `.hexaemeron/reports/step-1-guard.json`.\n\n"
            "## Step 2: Later\n\n**Exit.** `python3 " + LOCAL_CLI + " --root .`\n"
            "\n### Amendment -- 2026-09-27\n\n**What changed.** Complete replacement Exit: "
            "`python3 " + LOCAL_CLI + " --root . --count 1`\n\n**Why.** Fixture.\n\n"
            "**Steps touched.** Step 2.\n\n"
            "**Still holding.** Step 2: entry holds; exit holds.\n").encode()


def replay_refusal(successor, target, data, receipt):
    """Return the successor's refusal for this receipt, or None when it replays."""
    try:
        successor.replay(target, data, receipt)
    except successor.Refusal as error:
        return str(error)
    return None


def released_adapter_replay(root):
    """Receipts from each admitted released adapter replay; changed evidence refuses."""
    successor = load_tree_module(root, ADAPTER, "deferred_runner_successor_replay")
    observations = []
    with tempfile.TemporaryDirectory(prefix="deferred-runner-replay-") as scratch:
        target = Path(scratch).resolve() / "target"
        for relative in sorted(successor.REGISTRY):
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(read_tree_file(root, relative))
        (target / LOCAL_CLI).parent.mkdir(parents=True, exist_ok=True)
        (target / LOCAL_CLI).write_bytes(LOCAL_PROGRAM)
        data = replay_runbook(hashlib.sha256(LOCAL_PROGRAM).hexdigest())
        for commit, expected in RELEASED_ADAPTERS:
            released = released_adapter(root, scratch, commit, expected)
            try:
                receipt = released.validate(target, data)
            except released.Refusal:
                raise Refusal("released-capture-refused") from None
            try:
                fresh = successor.validate(target, data)
            except successor.Refusal:
                fresh = None
            before = copy.deepcopy(receipt)
            observations += [
                receipt["adapter_sha256"] == expected,
                "superseded-source" in [item.get("result") for item in receipt["commands"]],
                fresh is not None and fresh == {**receipt, "adapter_sha256": fresh["adapter_sha256"]},
                replay_refusal(successor, target, data, receipt) is None,
                receipt == before,
            ]
            forged = copy.deepcopy(receipt)
            forged["commands"][0]["command"] += " --changed"
            observations.append(replay_refusal(successor, target, data, forged) == "gate-receipt-drift")
            for adapter in ("0" * 64, None):
                unknown = dict(receipt, adapter_sha256=adapter)
                observations.append(replay_refusal(successor, target, data, unknown) == "gate-receipt-drift")
            for relative, reason in ((LOCAL_CLI, "registered-source-drift"),
                                     ("plugins/brevitas/skills/brevitas/scripts/brevitas.py",
                                      "gate-receipt-drift")):
                original = (target / relative).read_bytes()
                (target / relative).write_bytes(original + b"# changed after capture\n")
                try:
                    observations.append(replay_refusal(successor, target, data, receipt) == reason)
                finally:
                    (target / relative).write_bytes(original)
    return bool(observations) and all(observations)


def successor_replay_milliseconds(root):
    """Median of five successor validations of the committed runbook, rounded up."""
    successor = load_tree_module(root, ADAPTER, "deferred_runner_successor_timing")
    data = read_tree_file(root, TIMED_RUNBOOK, successor.MAX_DOCUMENT)
    samples = []
    for _ in range(TIMED_SAMPLES):
        started = time.perf_counter_ns()
        try:
            result = successor.validate(root, data)
        except successor.Refusal:
            raise Refusal("timed-validation-refused") from None
        samples.append(time.perf_counter_ns() - started)
        if result.get("operation_ran") is not False or not result.get("commands"):
            raise Refusal("timed-validation-invalid")
    return math.ceil(sorted(samples)[TIMED_SAMPLES // 2] / 1_000_000)


HANDLERS.update({
    "validator-deferred-contract": validator_deferred_contract,
    "released-adapter-replay": released_adapter_replay,
    "successor-replay-milliseconds": successor_replay_milliseconds,
    "controller-binding-custody": controller_binding_custody,
})


def main(argv=None, root=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    root = Path(__file__).absolute().parents[2] if root is None else Path(root)
    named = {"candidate": None, "criterion": None}
    try:
        candidate, criterion, report = parse(argv)
        # Echo only values from the closed sets, never arbitrary input.
        named["candidate"] = candidate if candidate in CANDIDATES else None
        named["criterion"] = criterion if criterion in CRITERIA else None
        result = resolve(root, candidate, criterion, report)
    except Refusal as error:
        reason = str(error)
    except (OSError, ValueError):
        reason = "input-unavailable"
    else:
        print(json.dumps(result, sort_keys=True))
        return 0
    print(json.dumps({"event": EVENT, "reason": reason, **named}, sort_keys=True))
    if reason == "argument-not-closed":
        print(USAGE, file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
