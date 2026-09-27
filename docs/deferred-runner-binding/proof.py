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

Step 4 adds the joined-demonstration handler. It drives the checked-in
controller once through a no-runner fixture from runbook receipt to a refused
later edit, keeps each raw observation, and derives every check from them. It
writes a companion evidence file, bound to the report's digest, before the
closed report.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
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

# The joined demonstration. It drives the checked-in controller through the
# harness's fake delivery tools; the evidence file sits beside the report.
EVIDENCED = frozenset({"joined-demonstration"})
EVIDENCE_SCHEMA = "deferred-runner-joined-demonstration-evidence/v1"
CONTROLLER = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
HARNESS = "plugins/hexaemeron/tests/hexctl_harness.py"
ELENCHUS_PARSER = "plugins/hexaemeron/skills/elenchus/scripts/elenchus.py"
DEMO_RUNNER = "tests/run_tests.py"
DEMO_ROW = DEMO_RUNNER + " | build_parser | step:1"
DEMO_TITLES = ("Scaffold", "Core")
DEMO_FILES = (DEMO_RUNNER, "src/core.py")
DEMO_EXITS = ("python3 " + DEMO_RUNNER + " --pattern test_core.py", "python3 " + DEMO_RUNNER)
DEMO_ELENCHUS = "python3 " + DEMO_RUNNER + " --elenchus-report {report}"
DEMO_GUARD_REPORT = ".hexaemeron/reports/step-1-guard.json"
DEMO_GUARD_TEST = "tests/test_network_guard.py"
DEMO_PR_URL = "https://github.com/wildcat-finance/example/pull/"
DEMO_SECONDS = 60
MAX_STATUS_ENTRIES = 32
# Refusal tokens the controller prints. The longer tokens are listed so that a
# prefix never stands in for them.
TOKENS = (
    "deferred-path-unsafe",
    "deferred-source-absent-at-head",
    "deferred-source-mode",
    "deferred-source-present",
    "deferred-source-present-at-base",
    "deferred-worktree-mismatch",
    "registered-source-drift",
    "source-unavailable",
)
# A target with product code and tests and no Python test runner.
DEMO_PRODUCT = {
    "src/__init__.py": "",
    "src/core.py": "def add(left, right):\n    return left + right\n",
    "tests/__init__.py": "",
    "tests/test_core.py": (
        "import unittest\n\nfrom src.core import add\n\n\n"
        "class CoreTests(unittest.TestCase):\n"
        "    def test_add(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n"
    ),
}
DEMO_STUDY = "# Study\n\n```risk-register\nrunner | binding | replay\n```\n"
# Step 1's runner. It runs every test in one process, denies network events
# through an audit hook and writes unittest-json-v1 for Elenchus.
RUNNER_CREATED = '''"""Run the fixture suite in one process."""
import argparse
import json
from pathlib import Path
import sys
import unittest

DENIED_EVENTS = (
    "socket.bind",
    "socket.connect",
    "socket.getaddrinfo",
    "socket.gethostbyaddr",
    "socket.gethostbyname",
    "socket.sendto",
)


def deny_network(event, args):
    if event in DENIED_EVENTS:
        raise PermissionError("network access is denied during tests: " + event)


def build_parser():
    parser = argparse.ArgumentParser(description="Run the fixture suite.")
    parser.add_argument("--elenchus-report", help="write unittest-json-v1 to this fresh path")
    parser.add_argument("--pattern", default="test_*.py", help="discovery pattern")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    sys.addaudithook(deny_network)
    root = str(Path.cwd())
    suite = unittest.defaultTestLoader.discover("tests", pattern=args.pattern, top_level_dir=root)
    result = unittest.TextTestRunner(stream=sys.stderr).run(suite)
    if args.elenchus_report is not None:
        report = {
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "expectedFailures": len(result.expectedFailures),
            "unexpectedSuccesses": len(result.unexpectedSuccesses),
        }
        with open(args.elenchus_report, "x", encoding="utf-8") as stream:
            stream.write(json.dumps(report, sort_keys=True) + "\\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''
# The audit fix inside Step 1, the analogue of miskatonic#14 finding S1-R1-01:
# reverse lookups were not denied.
RUNNER_FIXED = RUNNER_CREATED.replace(
    '    "socket.getaddrinfo",\n',
    '    "socket.getaddrinfo",\n    "socket.getnameinfo",\n')
DEMO_GUARD = (
    "import socket\nimport unittest\n\n\n"
    "class NetworkDenialTests(unittest.TestCase):\n"
    "    def test_reverse_lookup_is_denied(self):\n"
    "        # Numeric flags keep the call local if the hook lets it through.\n"
    "        with self.assertRaises(PermissionError):\n"
    "            socket.getnameinfo(('127.0.0.1', 0), "
    "socket.NI_NUMERICHOST | socket.NI_NUMERICSERV)\n"
)


class Refusal(Exception):
    """Carry one fixed reason token; never input text or exception detail."""


class Observed:
    """A handler value with the bounded evidence it was derived from."""

    def __init__(self, value, evidence):
        self.value = value
        self.evidence = evidence


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


def evidence_name(candidate, criterion):
    return candidate + "-" + criterion + ".evidence.json"


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


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
    """Check the cell, run its handler and create its report, or refuse.

    An evidenced criterion's handler returns Observed. Its evidence file is
    created first and names the report's digest, so a report never stands
    without the evidence it was derived from.
    """
    check_cell(candidate, criterion, report)
    name = report_name(candidate, criterion)
    names = [name]
    if criterion in EVIDENCED:
        names.append(evidence_name(candidate, criterion))
    for entry in names:
        require_absent(root, entry)
    handler = HANDLERS.get(criterion)
    if handler is None:
        raise Refusal("operation-not-implemented:" + criterion + ":step-" + str(CRITERIA[criterion]))
    unit = pending_unit(read_record(root), candidate, criterion)
    outcome = handler(root)
    evidence = None
    if criterion in EVIDENCED:
        if not isinstance(outcome, Observed) or not isinstance(outcome.evidence, dict):
            raise Refusal("handler-evidence-missing")
        value, evidence = outcome.value, outcome.evidence
        if evidence.get("value") is not value:
            raise Refusal("handler-evidence-mismatch")
    else:
        value = outcome
    if not value_matches(value, unit):
        raise Refusal("handler-value-outside-unit")
    result = {"schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion,
              "value": value, "unit": unit, "command": resolver(candidate, criterion), "exit": 0}
    data = encoded(result)
    if evidence is not None:
        bound = dict(evidence, report={"path": report, "sha256": hashlib.sha256(data).hexdigest()})
        write_exclusive(root, names[1], encoded(bound))
    try:
        write_exclusive(root, name, data)
    except BaseException:
        if evidence is not None:
            # This call created the evidence file exclusively; without its
            # report it would stand alone, so it goes.
            directory = open_report_directory(root, create=False)
            try:
                os.unlink(names[1], dir_fd=directory)
            finally:
                os.close(directory)
        raise
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


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def load_registered(path, name):
    """Load a module that must sit in sys.modules while it executes, then remove it."""
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise Refusal("module-unavailable")
    module = importlib.util.module_from_spec(specification)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def tokens_in(text):
    """The controller refusal tokens named in text, each matched whole."""
    return [token for token in TOKENS
            if re.search(r"(?<![a-z0-9-])" + re.escape(token) + r"(?![a-z0-9-])", text)]


def demonstration_runbook():
    """Two steps whose Exit and Elenchus commands name the runner Step 1 creates."""
    text = ("# Runbook\n\n```command-interfaces\nschema | protasis-command-interfaces/v1\n"
            + DEMO_ROW + "\n```\n\n")
    for number, (title, files, command) in enumerate(zip(DEMO_TITLES, DEMO_FILES, DEMO_EXITS), 1):
        text += (
            f"## Step {number}: {title}\n\n"
            f"**Goal.** Deliver {title.lower()}.\n"
            f"**Entry.** Step {number} is ready.\n"
            f"**Exit.** `{command}`\n"
            f"**Files.** `{files}`\n"
            f"**Tests.** Elenchus command: `{DEMO_ELENCHUS}`; format: `unittest-json-v1`; "
            f"report file: `.hexaemeron/reports/step-{number}-guard.json`.\n"
            "**Disciplines.** phylax: the runner denies network events.\n\n"
        )
    return text


def runbook_observation(data, receipt):
    """The receipted runbook's bytes, its registration rows and Step 1's gate records."""
    text = data.decode("utf-8")
    start, end = data.index(b"\n## Step 1:"), data.index(b"\n## Step 2:")
    fence = re.search(r"^```command-interfaces\n(.*?)^```$", text, re.M | re.S)
    rows = [] if fence is None else [
        line for line in fence.group(1).splitlines() if line and not line.startswith("schema |")]
    gate = receipt["gate_commands"]
    step_one = [
        {"command": record["command"], "report": record.get("report"),
         "invocations": [{"cli": item["cli"], "result": item["result"]}
                         for item in record["invocations"]]}
        for record in sorted(gate["commands"], key=lambda record: record["offset"])
        if start <= record["offset"] < end
    ]
    return {"file_sha256": sha256(data), "receipt_sha256": receipt["sha256"],
            "gate_artifact_sha256": gate["artifact_sha256"], "adapter_sha256": gate["adapter_sha256"],
            "interface_rows": rows, "step_one": step_one}


def demonstration_case(harness, elenchus):
    """A harness fixture case, driven by this script and never collected as a test."""

    class Demonstration(harness.HexctlCase):
        stage = "setup"

        def runTest(self):
            raise AssertionError("the demonstration is driven by proof.py")

        def at(self, stage):
            self.stage = stage

        def head(self):
            return self.git("rev-parse", "HEAD").stdout.strip()

        def blob(self, commit):
            """The runner's committed bytes, read as bytes rather than text."""
            completed = subprocess.run(
                ["git", "cat-file", "blob", commit + ":" + DEMO_RUNNER], cwd=self.target,
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=DEMO_SECONDS, check=False)
            if completed.returncode != 0:
                raise AssertionError("runner blob unavailable")
            return completed.stdout

        def digests(self):
            directory = Path(self.target, ".hexaemeron")
            return [sha256(directory.joinpath(name).read_bytes())
                    for name in ("state.json", "ledger.jsonl")]

        def gate_status(self):
            return json.loads(self.run_ctl("status", "--field", "gate_command_status").stdout)

        def refused(self, *args):
            """Run one command that must refuse; keep its tokens and the controller's bytes."""
            before = self.digests()
            completed = self.run_ctl(*args, expect=1)
            return {"returncode": completed.returncode, "tokens": tokens_in(completed.stderr),
                    "before": before, "after": self.digests()}

        def product_status(self):
            """Porcelain entries outside .hexaemeron/, untracked files listed one by one."""
            output = self.git("status", "--porcelain", "--untracked-files=all", "-z").stdout
            entries = sorted(entry for entry in output.split("\0")
                             if entry and not entry[3:].startswith(".hexaemeron/"))
            return {"entries": entries[:MAX_STATUS_ENTRIES], "count": len(entries)}

        def run_runner(self, scratch, name, script, extra):
            """Run one runner copy in the fixture; keep its exit and its parsed report."""
            report = Path(scratch, name + ".json")
            completed = subprocess.run(
                [sys.executable, "-I", "-B", script, *extra, "--elenchus-report", str(report)],
                cwd=self.target, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, env={"PATH": os.defpath, "LC_ALL": "C"},
                timeout=DEMO_SECONDS, check=False)
            result = {"returncode": completed.returncode, "parsed": False}
            try:
                parsed = elenchus.parse_unittest_report(read_bounded(report))
            except (OSError, elenchus.ReportError):
                return result
            result.update(parsed=True, executed=parsed.executed,
                          assertion_failures=parsed.assertion_failures,
                          errors=parsed.errors, skipped=parsed.skipped)
            return result

        def demonstrate(self, scratch):
            observations = {"status": {}}
            self.at("fixture-product")
            for path, text in DEMO_PRODUCT.items():
                self.write(path, text)
            self.git("add", *DEMO_PRODUCT)
            self.git("commit", "-q", "-m", "Fixture product without a runner")
            self.at("study")
            self.run_ctl("init", "--topic", "Deferred runner demonstration")
            self.write_design_evidence()
            study = self.write(".hexaemeron/study.md", DEMO_STUDY)
            self.run_ctl("done", "study", "--artifact", study, "--skills", "hexaemeron:protasis")
            runbook = self.write(".hexaemeron/runbook.md", demonstration_runbook())
            steps = self.write(".hexaemeron/steps.json", json.dumps(list(DEMO_TITLES)))
            receipt = ("done", "runbook", "--artifact", runbook, "--steps-file", steps)
            runner = Path(self.target, DEMO_RUNNER)

            # A runner already in the worktree refuses, and the status probe lists it.
            self.at("runbook-with-runner")
            self.write(DEMO_RUNNER, RUNNER_CREATED)
            observations["present-runner"] = {"status": self.product_status(),
                                              **self.refused(*receipt)}
            runner.unlink()
            self.at("runbook")
            before = {"status": self.product_status(), "runner_present": os.path.lexists(runner)}
            self.run_ctl(*receipt)
            after = {"status": self.product_status(), "runner_present": os.path.lexists(runner)}
            observations["receipt"] = {"before": before, "after": after}
            state = self.state()
            observations["runbook"] = runbook_observation(
                Path(self.target, runbook).read_bytes(), state["receipts"]["runbook"])
            observations["status"]["after-runbook"] = self.gate_status()
            self.run_ctl("record", "security_suite", '"waived: fixture"')
            for step in state["steps"]:
                self.git("branch", self.step_branch(step["n"], state))
            base = state["base"]
            first, second = self.step_branch(1, state), self.step_branch(2, state)
            observations["runner"] = {
                "base_entry": self.git("ls-tree", "-z", base, "--", DEMO_RUNNER).stdout}

            # Step 1 creates the runner.
            self.at("implement")
            self.git("checkout", "-q", first)
            self.write(DEMO_RUNNER, RUNNER_CREATED)
            self.git("add", DEMO_RUNNER)
            self.git("commit", "-q", "-m", "Add the fixture runner")
            implementation = self.head()
            self.run_ctl("done", "implement", "--branch", first, "--commit", implementation)

            # Round 1 finds that reverse lookups are not denied; the fix lands in Step 1.
            self.at("audit")
            self.run_ctl("audit-round", "--findings", "1", *harness.LINTS_CLEAN)
            self.write(DEMO_RUNNER, RUNNER_FIXED)
            self.write(DEMO_GUARD_TEST, DEMO_GUARD)
            self.git("add", DEMO_RUNNER, DEMO_GUARD_TEST)
            self.git("commit", "-q", "-m", "Deny reverse lookups in the fixture runner")
            fix = self.head()
            observations["verify-after-fix"] = self.run_ctl("verify").returncode
            observations["status"]["after-fix"] = self.gate_status()

            # The guard fails under the created runner and passes under the fix.
            self.at("runner-runs")
            created = Path(scratch, "created", "run_tests.py")
            created.parent.mkdir()
            created.write_bytes(self.blob(implementation))
            observations["runs"] = {
                "created": self.run_runner(scratch, "created", str(created),
                                           ["--pattern", Path(DEMO_GUARD_TEST).name]),
                "fixed": self.run_runner(scratch, "fixed", DEMO_RUNNER, []),
            }
            self.at("audit-close")
            self.run_ctl("audit-round", "--findings", "0", *harness.LINTS_CLEAN)
            self.run_ctl("done", "audit", "--fixes-ref", fix)
            self.run_ctl("done", "prose", "--files", "1",
                         "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")

            # An uncommitted edit at the push refuses before any write; then the push binds.
            self.at("push")
            head = self.head()
            self.fake_refs[first] = head
            push = ("done", "push", "--pr-url", DEMO_PR_URL + "1", "--head-commit", head,
                    "--pr-base", self.step_base(1, state))
            runner.write_bytes(RUNNER_FIXED.encode() + b"# uncommitted edit\n")
            observations["push-mismatch"] = self.refused(*push)
            runner.write_bytes(RUNNER_FIXED.encode())
            observations["status"]["before-push"] = self.gate_status()
            self.run_ctl(*push)
            observations["status"]["after-push"] = self.gate_status()
            observations["verify-after-push"] = self.run_ctl("verify").returncode
            state = self.state()
            binding = state["steps"][0]["receipts"]["push"]["gate_binding"]
            ledger = [json.loads(line) for line in Path(self.target, ".hexaemeron/ledger.jsonl")
                      .read_text(encoding="utf-8").splitlines()]
            invocations = [item for command in binding["gate_commands"]["commands"]
                           for item in command.get("invocations", [])]
            observations["binding"] = {
                "step": binding["step"], "starting_commit": binding["starting_commit"],
                "push_head": binding["push_head"], "paths": binding["paths"],
                "results": sorted({item["result"] for item in invocations}),
                "cli_sha256": sorted({item["cli"].get("sha256") or "" for item in invocations}),
                "adapter_sha256": binding["gate_commands"]["adapter_sha256"],
                "state_sha256": canonical_sha256(binding),
                "ledger_sha256": [canonical_sha256(entry["data"].get("gate_binding"))
                                  for entry in ledger if entry["event"] == "done:push"],
            }
            observations["runner"].update({
                "added_by": self.git("log", "--format=%H", "--diff-filter=A",
                                     base + ".." + head, "--", DEMO_RUNNER).stdout.split(),
                "created_sha256": sha256(self.blob(implementation)),
                "fixed_sha256": sha256(self.blob(fix)),
                "pushed_entry": self.git("ls-tree", "-z", head, "--", DEMO_RUNNER).stdout,
                "pushed_sha256": sha256(self.blob(head)),
            })
            observations["amendments"] = {
                "ledger_events": sum(entry["event"] == "amend:runbook" for entry in ledger),
                "receipt": len(state["receipts"]["runbook"].get("amendments") or []),
                "runbook_sha256": state["receipts"]["runbook"]["sha256"],
            }
            observations["audit"] = {
                "findings": [entry["findings"] for entry in state["steps"][0]["audit"]["rounds"]]}

            # A committed change to the bound runner in Step 2 refuses as drift.
            self.at("drift")
            self.git("checkout", "-q", "-B", second, head)
            runner.write_bytes(RUNNER_FIXED.encode() + b"# edited by Step 2\n")
            self.git("commit", "-q", "-am", "Edit the bound runner")
            later = self.head()
            observations["drift"] = {
                "verify": self.refused("verify"),
                "status": self.gate_status(),
                "implement": self.refused("done", "implement", "--branch", second,
                                          "--commit", later),
                "later_sha256": sha256(self.blob(later)),
            }
            observations["commits"] = {
                "starting": base, "implementation": implementation, "fix": fix,
                "push_head": head, "later_edit": later,
                "implement_receipt": state["steps"][0]["receipts"]["implement"]["commit"],
                "fixes_ref": state["steps"][0]["receipts"]["audit"]["fixes_ref"],
            }
            return observations

    return Demonstration()


def read_bounded(path, cap=64 * 1024):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise OSError("not a regular file")
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise OSError("over cap")
    return data


def run_demonstration(root):
    """Drive the checked-in controller once and return the raw observations."""
    root = Path(root)
    controller = read_tree_file(root, CONTROLLER)
    adapter = read_tree_file(root, ADAPTER)
    sources = [{"path": path, "sha256": sha256(read_tree_file(root, path))}
               for path in (SELF, HARNESS, ELENCHUS_PARSER)]
    harness = load_registered(regular_path(root, HARNESS), "deferred_runner_demonstration_harness")
    elenchus = load_registered(regular_path(root, ELENCHUS_PARSER),
                               "deferred_runner_demonstration_elenchus")
    try:
        driven = Path(harness.HEXCTL).resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        driven = None
    case = demonstration_case(harness, elenchus)
    with tempfile.TemporaryDirectory(prefix="deferred-runner-demonstration-") as scratch:
        try:
            case.setUp()
        except (OSError, subprocess.SubprocessError):
            raise Refusal("demonstration-fixture-unavailable") from None
        try:
            observations = case.demonstrate(Path(scratch).resolve())
        except (AssertionError, KeyError, IndexError, TypeError, ValueError, OSError,
                subprocess.SubprocessError):
            raise Refusal("demonstration-lifecycle-diverged:" + case.stage) from None
        finally:
            case.tearDown()
    observations["controller"] = {
        "path": CONTROLLER, "driven": driven, "bytes": len(controller),
        "sha256_before": sha256(controller), "sha256_after": sha256(read_tree_file(root, CONTROLLER))}
    observations["adapter"] = {
        "path": ADAPTER, "bytes": len(adapter),
        "sha256_before": sha256(adapter), "sha256_after": sha256(read_tree_file(root, ADAPTER))}
    observations["sources"] = sources
    return observations


HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
AWAITING = {"status": "awaiting-binding", "validation": "interface-only",
            "deferred": [{"path": DEMO_RUNNER, "step": "step:1"}]}
CURRENT = {"status": "current", "validation": "interface-only"}
UNTOUCHED = {"entries": [], "count": 0}


def refused_unchanged(refusal, token):
    """Exit 1, the named token, and state and ledger bytes equal before and after."""
    return (refusal["returncode"] == 1 and token in refusal["tokens"]
            and len(refusal["before"]) == 2 and refusal["before"] == refusal["after"])


def tree_entry(entry):
    """Split one `ls-tree -z` entry into mode, kind and object id."""
    match = re.fullmatch(r"([0-7]{6}) ([a-z]+) ([0-9a-f]{40})\t" + re.escape(DEMO_RUNNER) + "\0", entry)
    return match.groups() if match else (None, None, None)


def check_controller(o):
    c = o["controller"]
    return (c["path"] == CONTROLLER and c["driven"] == CONTROLLER
            and HEX64.fullmatch(c["sha256_before"]) is not None
            and c["sha256_before"] == c["sha256_after"])


def check_adapter(o):
    a = o["adapter"]
    loaded = (o["runbook"]["adapter_sha256"], o["binding"]["adapter_sha256"])
    return (HEX64.fullmatch(a["sha256_before"]) is not None
            and a["sha256_before"] == a["sha256_after"]
            and all(value == a["sha256_before"] for value in loaded))


def check_present_runner(o):
    p = o["present-runner"]
    return (p["status"] == {"entries": ["?? " + DEMO_RUNNER], "count": 1}
            and refused_unchanged(p, "deferred-source-present"))


def check_no_product_file(o):
    return all(o["receipt"][side] == {"status": UNTOUCHED, "runner_present": False}
               for side in ("before", "after"))


def check_step_one_commands(o):
    r = o["runbook"]
    deferred = [{"cli": {"path": DEMO_RUNNER, "deferred": "step:1"}, "result": "interface-deferred"}]
    expected = [
        {"command": DEMO_EXITS[0], "report": None, "invocations": deferred},
        {"command": DEMO_ELENCHUS, "report": {"format": "unittest-json-v1", "file": DEMO_GUARD_REPORT},
         "invocations": deferred},
    ]
    return (r["interface_rows"] == [DEMO_ROW] and r["step_one"] == expected
            and HEX64.fullmatch(r["file_sha256"]) is not None
            and r["file_sha256"] == r["receipt_sha256"] == r["gate_artifact_sha256"])


def check_awaiting(o):
    return o["status"]["after-runbook"] == AWAITING


def check_created_by_step_one(o):
    c, r = o["commits"], o["runner"]
    return (r["base_entry"] == "" and HEX40.fullmatch(c["implementation"]) is not None
            and r["added_by"] == [c["implementation"]] and c["implement_receipt"] == c["implementation"])


def check_binding(o):
    b, c, r, s = o["binding"], o["commits"], o["runner"], o["status"]
    mode, kind, blob = tree_entry(r["pushed_entry"])
    row = {"path": DEMO_RUNNER, "builder": "build_parser", "mode": mode, "blob": blob,
           "sha256": r["pushed_sha256"]}
    return (s["before-push"] == AWAITING and s["after-push"] == CURRENT
            and o["verify-after-push"] == 0
            and b["step"] == "step:1" and b["starting_commit"] == c["starting"]
            and b["push_head"] == c["push_head"] and mode == "100644" and kind == "blob"
            and b["paths"] == [row] and b["results"] == ["interface-valid"]
            and b["cli_sha256"] == [r["pushed_sha256"]]
            and b["ledger_sha256"] == [b["state_sha256"]])


def check_push_mismatch(o):
    return refused_unchanged(o["push-mismatch"], "deferred-worktree-mismatch")


def check_drift(o):
    d = o["drift"]
    return (refused_unchanged(d["verify"], "registered-source-drift")
            and refused_unchanged(d["implement"], "registered-source-drift")
            and d["status"]["status"] == "stale-or-invalid"
            and HEX64.fullmatch(d["later_sha256"]) is not None
            and d["later_sha256"] != o["runner"]["pushed_sha256"])


def check_in_step_fix(o):
    a, c, r = o["amendments"], o["commits"], o["runner"]
    return (r["created_sha256"] == sha256(RUNNER_CREATED.encode())
            and r["fixed_sha256"] == sha256(RUNNER_FIXED.encode())
            and r["created_sha256"] != r["fixed_sha256"] and r["pushed_sha256"] == r["fixed_sha256"]
            and o["binding"]["paths"][0]["sha256"] == r["fixed_sha256"]
            and a["ledger_events"] == 0 and a["receipt"] == 0
            and a["runbook_sha256"] == o["runbook"]["receipt_sha256"]
            and o["audit"]["findings"] == [1, 0] and c["fixes_ref"] == c["fix"]
            and o["status"]["after-fix"] == AWAITING and o["verify-after-fix"] == 0)


def check_fix_behaviour(o):
    runs = o["runs"]
    return (runs["created"] == {"returncode": 1, "parsed": True, "executed": 1,
                                "assertion_failures": 1, "errors": 0, "skipped": 0}
            and runs["fixed"] == {"returncode": 0, "parsed": True, "executed": 2,
                                  "assertion_failures": 0, "errors": 0, "skipped": 0})


# id, kind, criterion, check. The criterion numbers are the study's section 1.
CHECKS = (
    ("controller-bytes", "identity", "identity", check_controller),
    ("adapter-bytes", "identity", "identity", check_adapter),
    ("runbook-refuses-present-runner", "refusal", "criterion-1", check_present_runner),
    ("runbook-receipted-without-product-files", "positive", "criterion-1", check_no_product_file),
    ("step-one-commands-deferred", "positive", "criterion-1", check_step_one_commands),
    ("status-awaiting-binding", "positive", "criterion-1", check_awaiting),
    ("runner-created-by-step-one", "positive", "criterion-2", check_created_by_step_one),
    ("push-binds-runner", "positive", "criterion-2", check_binding),
    ("push-refuses-worktree-mismatch", "refusal", "criterion-3", check_push_mismatch),
    ("later-edit-refuses-drift", "refusal", "criterion-3", check_drift),
    ("in-step-fix-without-amendment", "positive", "criterion-4", check_in_step_fix),
    ("fix-changes-runner-behaviour", "positive", "criterion-4", check_fix_behaviour),
)
CLAIMS = {
    "identity": "The controller and adapter bytes named here are the bytes that ran, and the "
                "adapter digest each gate receipt records equals them.",
    "criterion-1": "The controller receipted a runbook whose Step 1 Exit and Elenchus commands name "
                   "tests/run_tests.py through a step:1 row, with no runner in the worktree and no "
                   "untracked product file; a runner already present refused.",
    "criterion-2": "Step 1 added the runner, and its push bound the pushed blob's SHA-256 while the "
                   "gate status moved from awaiting-binding to current.",
    "criterion-3": "An uncommitted runner change at the push refused as deferred-worktree-mismatch, "
                   "and a later committed change refused as registered-source-drift, each with "
                   "state and ledger bytes unchanged.",
    "criterion-4": "A runner fix inside Step 1's audit loop landed with zero runbook amendments; the "
                   "guard it added failed under the created runner and passed under the fix, and "
                   "the push bound the fixed bytes.",
}
EXCLUSIONS = (
    "GitHub, the remote and commit signatures are the harness's fake delivery tools; no remote "
    "state or signature was checked.",
    "The audit rounds are harness stand-in records, not Warden rounds, and no Elenchus verdict "
    "was recorded.",
    "The runner's network denial is an audit hook inside one test process, not host isolation.",
    "The init-pinned controller that drives the live run was not run; only the checked-in "
    "controller named here ran.",
)
UNCLAIMED = (
    "That these observations are sufficient for the issue's acceptance.",
    "That the fixture runner or its tests are correct beyond the counts recorded.",
    "Host, process or network isolation of the fixture.",
    "Any remote GitHub state.",
    "Behaviour on any other target, runbook or controller version.",
)


def assess(observations):
    """Derive every check from the observations; a missing or malformed one fails."""
    checks = []
    for identifier, kind, criterion, check in CHECKS:
        try:
            holds = check(observations) is True
        except (KeyError, IndexError, TypeError, AttributeError):
            holds = False
        checks.append({"id": identifier, "kind": kind, "criterion": criterion, "holds": holds})
    return checks


def demonstration_evidence(observations):
    """The value and the evidence record, both derived from the observations."""
    checks = assess(observations)
    value = bool(checks) and all(check["holds"] for check in checks)
    held = {criterion for criterion in CLAIMS
            if all(check["holds"] for check in checks if check["criterion"] == criterion)}
    commits = observations.get("commits", {})
    return value, {
        "schema": EVIDENCE_SCHEMA,
        "candidate": SELECTED,
        "criterion": "joined-demonstration",
        "value": value,
        "controller": {"path": CONTROLLER, "sha256": observations["controller"]["sha256_before"],
                       "bytes": observations["controller"]["bytes"]},
        "adapter": {"path": ADAPTER, "sha256": observations["adapter"]["sha256_before"],
                    "bytes": observations["adapter"]["bytes"]},
        "sources": observations["sources"],
        "fixture": {"commits": commits,
                    "runbook_sha256": observations.get("runbook", {}).get("receipt_sha256")},
        "checks": checks,
        "observations": observations,
        "establishes": [CLAIMS[criterion] for criterion in CLAIMS if criterion in held],
        "unclaimed": list(UNCLAIMED),
        "exclusions": list(EXCLUSIONS),
    }


def joined_demonstration(root):
    """Drive the checked-in controller once; the value is every check holding."""
    value, evidence = demonstration_evidence(run_demonstration(root))
    return Observed(value, evidence)


HANDLERS.update({
    "validator-deferred-contract": validator_deferred_contract,
    "released-adapter-replay": released_adapter_replay,
    "successor-replay-milliseconds": successor_replay_milliseconds,
    "controller-binding-custody": controller_binding_custody,
    "joined-demonstration": joined_demonstration,
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
