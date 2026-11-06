#!/usr/bin/env python3
"""Surveyor policy specimens for the skills#1944 design record.

This is not the product controller. Each candidate is modelled as a thin
wrapper around the released Hexaemeron 1.6.82 gate adapter, read from Git at
the run's starting commit and checked by digest. A disposable Git fixture
stands in for a target repository with no runner. The specimen runner is
written as data and never executed.

The report mode prints one closed protasis-design-report/v1 object and writes
it to a fresh --report path; it refuses an existing, linked or escaping path.
The --hostile-cases mode prints the binding model's refusals and writes
nothing.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import statistics
import subprocess
import tempfile
import time

BASE = "e992a54b4e3e4671bae98b448d57690de8dfa044"
ADAPTER = "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
ADAPTER_SHA256 = "14a857dc44ce43d7a3771a2125b92f86435e39ab8ba2b027ef02b4f36ca48bad"
RUNNER = "tests/run_tests.py"
REVIEWED_NAME = "hexaemeron-unittest-runner/v1"
FENCE = "```"

CANDIDATES = (
    "creating-step-binding",
    "reviewed-stdlib-runner",
    "runbook-embedded-source",
    "pre-placed-untracked",
)
CRITERIA = {
    "pre-step-product-files": "count",
    "bound-drift-refused": "boolean",
    "interface-checked-by-step-close": "boolean",
    "legacy-results-unchanged": "boolean",
    "replay-milliseconds": "milliseconds",
    "in-step-fix-amendments": "count",
    "runbook-growth-bytes": "bytes",
}
PHASES = ("runbook", "step-1-implement", "step-1-audit", "step-1-push")

# The specimen runner is data. Its entry guard is assembled from parts so that
# no line of this probe spells the idiom that a text search could mistake for
# this file's own entry point.
ENTRY_GUARD = "if __name__ == " + '"__main__"' + ":"
RUNNER_TEMPLATE = '''#!/usr/bin/env python3
"""Run the fixture suite in one process and write an Elenchus report."""

import argparse
import json
import sys
import unittest

DENIED = ({denied})


def deny(event, args):
    if event in DENIED or event.startswith("os.exec"):
        raise RuntimeError("denied by the runner boundary: " + event)


def build_parser():
    parser = argparse.ArgumentParser(description="Run the fixture suite in one process.")
    parser.add_argument("--elenchus-report", help="write an elenchus.unittest.v1 report to this fresh path")
    parser.add_argument("--pattern", default="test_*.py", help="unittest discovery pattern")
    return parser


def run(argv=None):
    args = build_parser().parse_args(argv)
    sys.dont_write_bytecode = True
    sys.addaudithook(deny)
    suite = unittest.defaultTestLoader.discover("tests", pattern=args.pattern, top_level_dir=".")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if args.elenchus_report:
        payload = {{
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "expectedFailures": len(result.expectedFailures),
            "unexpectedSuccesses": len(result.unexpectedSuccesses),
        }}
        with open(args.elenchus_report, "x", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
    return 0 if result.wasSuccessful() else 1


{guard}
    raise SystemExit(run())
'''
DENIED_V1 = ('"socket.connect", "socket.getaddrinfo", "socket.gethostbyname", '
             '"subprocess.Popen", "os.system", "os.posix_spawn", "os.fork"')
# The observed S1-R1-01 analogue: the audit adds one missing resolver event.
DENIED_V2 = DENIED_V1 + ', "socket.getnameinfo"'
DENIED_V3 = DENIED_V2 + ', "socket.gethostbyaddr"'
RUNNER_V1 = RUNNER_TEMPLATE.format(denied=DENIED_V1, guard=ENTRY_GUARD).encode()
RUNNER_V2 = RUNNER_TEMPLATE.format(denied=DENIED_V2, guard=ENTRY_GUARD).encode()
RUNNER_V3 = RUNNER_TEMPLATE.format(denied=DENIED_V3, guard=ENTRY_GUARD).encode()


class ProbeError(RuntimeError):
    """A specimen observed something its model does not admit."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repository_root() -> Path:
    here = Path(__file__).resolve().parent
    out = subprocess.run(["git", "-C", str(here), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def load_adapter(scratch: Path):
    """Load the released adapter bytes from the starting commit, by digest."""
    data = subprocess.run(["git", "-C", str(repository_root()), "show", f"{BASE}:{ADAPTER}"],
                          capture_output=True, check=True).stdout
    if sha(data) != ADAPTER_SHA256:
        raise ProbeError("released adapter digest mismatch")
    path = scratch / "gate_commands.py"
    path.write_bytes(data)
    spec = importlib.util.spec_from_file_location("released_gate_commands", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_env(home: Path) -> dict:
    empty = home / "gitconfig"
    empty.touch()
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(empty),
        "LC_ALL": "C",
    }


class Fixture:
    """One disposable target repository whose base commit has no runner."""

    def __init__(self, place: Path):
        place.mkdir()
        self.root = place / "target"
        self.root.mkdir()
        self.env = git_env(place)
        self.git("init", "-q", "-b", "main")
        files = {
            "README.md": b"# fixture target\n",
            "src/fixture/__init__.py": b"",
            "src/fixture/core.py": b"def add(left, right):\n    return left + right\n",
            "tests/test_core.py": (
                b"import sys\nimport unittest\n\nsys.path.insert(0, 'src')\n"
                b"from fixture.core import add\n\n\n"
                b"class CoreTests(unittest.TestCase):\n"
                b"    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n"
            ),
            ".hexaemeron/.gitignore": b"*\n",
        }
        for name, data in files.items():
            self.write(name, data)
        self.git("add", "-A")
        self.base = self.commit("base: a target with no runner")

    def git(self, *args: str, check: bool = True) -> str:
        done = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True,
                              text=True, env=self.env, check=False)
        if check and done.returncode != 0:
            raise ProbeError("git " + " ".join(args) + ": " + done.stderr.strip())
        return done.stdout.strip()

    def commit(self, message: str) -> str:
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def write(self, name: str, data: bytes) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def untracked_product_files(self) -> int:
        lines = self.git("status", "--porcelain", "--untracked-files=all").splitlines()
        return sum(1 for line in lines
                   if line.startswith("?? ") and not line[3:].startswith(".hexaemeron/"))

    def blob(self, commit: str, name: str) -> tuple[str, bytes] | None:
        entry = self.git("ls-tree", commit, "--", name)
        if not entry:
            return None
        mode, kind, _ = entry.split("\t")[0].split(" ")
        data = subprocess.run(["git", "-C", str(self.root), "cat-file", "blob", f"{commit}:{name}"],
                              capture_output=True, env=self.env, check=True).stdout
        return mode + " " + kind, data


def fence(label: str, body: str) -> str:
    return f"{FENCE}{label}\n{body}{FENCE}\n"


def registration(third: str) -> str:
    return fence("command-interfaces",
                 f"schema | protasis-command-interfaces/v1\n{RUNNER} | build_parser | {third}\n")


def source_fence(source: bytes) -> str:
    return fence("command-source", f"path | {RUNNER}\nbuilder | build_parser\n" + source.decode())


STEPS = """
## Step 1: Add the suite runner

**Goal.** Add a single-process stdlib runner.
**Entry.** The base commit.
**Exit.** `python3 tests/run_tests.py`
**Files.** The runner.
**Tests.** The fixture suite through the runner.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
**Disciplines.** none, a fixture.

## Step 2: Extend the core

**Goal.** Extend the core module.
**Entry.** Step 1's exit.
**Exit.** `python3 tests/run_tests.py --pattern test_core.py`
**Files.** The core module.
**Tests.** The core tests.
Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
**Disciplines.** none, a fixture.
"""


def amendment(extra: str) -> str:
    return ("\n### Amendment -- 2026-09-27\n\n"
            "**What changed.** Complete replacement Files: the runner carries the "
            "S1-R1-01 network-denial repair.\n\n" + extra +
            "\n**Why.** Audit finding S1-R1-01 changed the runner inside Step 1.\n"
            "**Steps touched.** Step 1's files.\n"
            "**Still holding.** Step 1: entry holds; exit holds. "
            "Step 2: entry holds; exit holds.\n")


def lstat_absent(root: Path, relative: str) -> bool:
    """True only when some component is missing; a link or other type refuses."""
    current = root
    parts = relative.split("/")
    for index, part in enumerate(parts):
        current = current / part
        try:
            os.lstat(current)
        except FileNotFoundError:
            return True
        if os.path.islink(current):
            raise ProbeError("deferred-path-unsafe")
        if index < len(parts) - 1 and not os.path.isdir(current):
            raise ProbeError("deferred-path-unsafe")
    raise ProbeError("deferred-source-present")


class Model:
    """The per-candidate controller policy wrapped around the released adapter."""

    def __init__(self, candidate: str, adapter, fixture: Fixture, shadow: Path):
        self.name = candidate
        self.adapter = adapter
        self.fixture = fixture
        self.shadow = shadow
        self.bound: str | None = None
        self.amendments: list[str] = []
        if candidate == "creating-step-binding":
            self.preamble = "# Runbook\n\n" + registration("step:1")
        elif candidate == "reviewed-stdlib-runner":
            self.preamble = "# Runbook\n\n" + registration("reviewed:" + REVIEWED_NAME)
        elif candidate == "runbook-embedded-source":
            self.preamble = "# Runbook\n\n" + source_fence(RUNNER_V1) + "\n" + registration("embedded")
        else:
            self.preamble = "# Runbook\n\n" + registration(sha(RUNNER_V1))

    def text(self) -> str:
        return self.preamble + STEPS + "".join(self.amendments)

    def growth_bytes(self) -> int:
        grown = self.preamble[len("# Runbook\n\n"):] + "".join(self.amendments)
        return len(grown.encode("utf-8"))

    def _pinned(self, digest: str) -> bytes:
        """Rewrite the model's own row into the released pinned grammar."""
        text = self.text()
        text = re.sub(re.escape(FENCE) + r"command-source\n.*?" + re.escape(FENCE) + r"\n\n",
                      "", text, flags=re.S)
        text = re.sub(r"(?m)^" + re.escape(RUNNER) + r" \| build_parser \| (step:1|reviewed:\S+|embedded)$",
                      f"{RUNNER} | build_parser | {digest}", text)
        return text.encode("utf-8")

    def _shadow_validate(self, source: bytes) -> dict:
        target = self.shadow / RUNNER
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source)
        return self.adapter.validate(self.shadow, self._pinned(sha(source)))

    def capture(self, phase: str) -> dict:
        """Return a gate result or raise the adapter's refusal.

        Each model applies its own rule only when its own syntax occurs; any
        other runbook goes straight to the released adapter.
        """
        root = self.fixture.root
        text = self.text()
        if self.name == "creating-step-binding" and f"{RUNNER} | build_parser | step:1\n" in text:
            if self.bound is not None:
                return self.adapter.validate(root, self._pinned(self.bound))
            if phase == "runbook":
                lstat_absent(root, RUNNER)
            return self._deferred(root)
        if self.name == "reviewed-stdlib-runner" and "| reviewed:" in text:
            if phase == "runbook":
                lstat_absent(root, RUNNER)
                return self._shadow_validate(RUNNER_V1)
            return self.adapter.validate(root, self._pinned(sha(RUNNER_V1)))
        if self.name == "runbook-embedded-source" and FENCE + "command-source\n" in text:
            if phase == "runbook":
                lstat_absent(root, RUNNER)
                return self._shadow_validate(self.embedded_source())
            return self.adapter.validate(root, self._pinned(sha(self.embedded_source())))
        return self.adapter.validate(root, text.encode("utf-8"))

    def embedded_source(self) -> bytes:
        blocks = re.findall(re.escape(FENCE) + r"command-source\npath \| [^\n]+\nbuilder \| [^\n]+\n(.*?)"
                            + re.escape(FENCE) + r"\n", self.text(), flags=re.S)
        return blocks[-1].encode("utf-8")

    def _deferred(self, root: Path) -> dict:
        """Validate every command except the parser interface of the unbound runner."""
        stripped = self._pinned("0" * 64).decode()
        stripped = stripped.replace(f"{RUNNER} | build_parser | {'0' * 64}\n", "")
        records, _ = self.adapter.capture_runbook(stripped.encode("utf-8"))
        results = []
        for record in records:
            invocations = []
            for values in self.adapter.expand(record["command"]):
                if len(values) < 2 or values[0] != "python3" or values[1] != RUNNER:
                    raise ProbeError("fixture names only the deferred runner")
                resolved = list(values)
                if record["report"] is not None:
                    if values.count("{report}") != 1 or record["report"]["format"] != "unittest-json-v1":
                        raise self.adapter.Refusal("report-contract")
                    resolved[values.index("{report}")] = self.adapter.report_operand(
                        root, record["report"]["file"])
                invocations.append({"argv": values, "execution_argv": resolved,
                                    "cli": {"path": RUNNER, "deferred": "step:1"},
                                    "result": "interface-deferred"})
            results.append({"command": record["command"], "invocations": invocations})
        return {"schema": self.adapter.SCHEMA, "commands": results, "operation_ran": False}

    def bind_at_push(self, head: str) -> None:
        """Bind the committed blob at the creating step's push, or refuse."""
        if self.fixture.blob(self.fixture.base, RUNNER) is not None:
            raise ProbeError("deferred-source-present-at-base")
        found = self.fixture.blob(head, RUNNER)
        if found is None:
            raise ProbeError("deferred-source-absent-at-head")
        mode, data = found
        if mode not in ("100644 blob", "100755 blob"):
            raise ProbeError("deferred-source-mode")
        if (self.fixture.root / RUNNER).read_bytes() != data:
            raise ProbeError("deferred-worktree-mismatch")
        self.bound = sha(data)


def valid_runner_commands(result: dict) -> bool:
    invocations = [item for command in result["commands"] for item in command.get("invocations", [])]
    return bool(invocations) and all(item["result"] == "interface-valid" for item in invocations)


def lifecycle(candidate: str, adapter, place: Path) -> dict:
    fixture = Fixture(place / "lifecycle")
    shadow = place / "shadow"
    shadow.mkdir()
    model = Model(candidate, adapter, fixture, shadow)
    first_valid = None

    # Runbook receipt. The status quo needs the runner in the worktree first.
    if candidate == "pre-placed-untracked":
        try:
            model.capture("runbook")
            raise ProbeError("released adapter accepted an absent registered runner")
        except adapter.Refusal as refusal:
            if not str(refusal).startswith("source-unavailable"):
                raise
        fixture.write(RUNNER, RUNNER_V1)
    result = model.capture("runbook")
    pre_step = fixture.untracked_product_files()
    if valid_runner_commands(result):
        first_valid = "runbook"

    # Step 1 implementation adds the runner on its own branch.
    fixture.git("checkout", "-q", "-b", "step-1")
    fixture.write(RUNNER, RUNNER_V1)
    fixture.git("add", "-A")
    fixture.commit("step 1: add the runner")
    result = model.capture("step-1-implement")
    if first_valid is None and valid_runner_commands(result):
        first_valid = "step-1-implement"

    # Audit round 1 fixes the runner inside Step 1 (the S1-R1-01 analogue).
    fixture.write(RUNNER, RUNNER_V2)
    fixture.git("add", "-A")
    head = fixture.commit("step 1: deny socket.getnameinfo (S1-R1-01)")
    try:
        result = model.capture("step-1-audit")
    except (adapter.Refusal, ProbeError):
        if candidate == "creating-step-binding":
            raise
        # The only in-run repair each route admits: one appended amendment.
        if candidate == "runbook-embedded-source":
            model.amendments.append(amendment(source_fence(RUNNER_V2)))
        else:
            model.amendments.append(amendment(registration(sha(RUNNER_V2))))
        result = model.capture("step-1-audit")
    if first_valid is None and valid_runner_commands(result):
        first_valid = "step-1-audit"

    # Step 1 closes at its push; the deferred route binds the pushed blob here.
    if candidate == "creating-step-binding":
        model.bind_at_push(head)
    result = model.capture("step-1-push")
    if first_valid is None and valid_runner_commands(result):
        first_valid = "step-1-push"
    if not valid_runner_commands(result):
        raise ProbeError("the runner commands are not interface-valid at Step 1's close")

    timings = []
    for _ in range(7):
        started = time.perf_counter()
        model.capture("step-1-push")
        timings.append((time.perf_counter() - started) * 1000)

    # Step 2 edits the committed runner without any registration change.
    fixture.git("checkout", "-q", "-b", "step-2")
    fixture.write(RUNNER, RUNNER_V3)
    fixture.git("add", "-A")
    fixture.commit("step 2: edit the runner without an amendment")
    try:
        model.capture("step-2")
        drift_refused = False
    except adapter.Refusal as refusal:
        drift_refused = str(refusal) == "registered-source-drift"

    return {
        "pre-step-product-files": (pre_step, "count"),
        "bound-drift-refused": (drift_refused, "boolean"),
        "interface-checked-by-step-close": (
            first_valid is not None and PHASES.index(first_valid) <= PHASES.index("step-1-push"),
            "boolean"),
        "replay-milliseconds": (math.ceil(statistics.median(timings)), "milliseconds"),
        "in-step-fix-amendments": (len(model.amendments), "count"),
        "runbook-growth-bytes": (model.growth_bytes(), "bytes"),
    }


def legacy(candidate: str, adapter, place: Path) -> bool:
    """A runbook using only the released grammar yields the released result."""
    fixture = Fixture(place / "legacy")
    fixture.write(RUNNER, RUNNER_V1)
    fixture.git("add", "-A")
    fixture.commit("an existing tracked runner")
    shadow = place / "legacy-shadow"
    shadow.mkdir()
    model = Model(candidate, adapter, fixture, shadow)
    model.preamble = "# Runbook\n\n" + registration(sha(RUNNER_V1))
    released = adapter.validate(fixture.root, model.text().encode("utf-8"))
    return all(model.capture(phase) == released for phase in PHASES)


def measure(candidate: str, criterion: str) -> tuple[object, str]:
    with tempfile.TemporaryDirectory(prefix="fiat-1944-probe-") as scratch:
        place = Path(scratch)
        adapter = load_adapter(place)
        if criterion == "legacy-results-unchanged":
            return legacy(candidate, adapter, place), "boolean"
        return lifecycle(candidate, adapter, place)[criterion]


def hostile_cases() -> dict:
    """Observe the creating-step-binding model's refusals; writes nothing."""
    observed = {}

    def attempt(label, operation):
        try:
            operation()
            observed[label] = "accepted"
        except (ProbeError, RuntimeError, ValueError, OSError) as refusal:
            observed[label] = str(refusal).split(":")[0]

    with tempfile.TemporaryDirectory(prefix="fiat-1944-hostile-") as scratch:
        place = Path(scratch)
        adapter = load_adapter(place)

        def fresh(label):
            fixture = Fixture(place / label)
            return fixture, Model("creating-step-binding", adapter, fixture, place)

        fixture, model = fresh("untracked")
        fixture.write(RUNNER, RUNNER_V1)
        attempt("untracked-file-at-runbook", lambda: model.capture("runbook"))

        fixture, model = fresh("linked-parent")
        os.rename(fixture.root / "tests", fixture.root / "real-tests")
        os.symlink("real-tests", fixture.root / "tests")
        attempt("linked-parent-at-runbook", lambda: model.capture("runbook"))

        fixture, model = fresh("tracked")
        fixture.write(RUNNER, RUNNER_V1)
        fixture.git("add", "-A")
        fixture.base = fixture.commit("a tracked runner at the base")
        attempt("tracked-file-at-runbook", lambda: model.capture("runbook"))
        attempt("tracked-file-at-binding", lambda: model.bind_at_push(fixture.base))

        fixture, model = fresh("absent-at-head")
        model.capture("runbook")
        attempt("absent-at-head-binding", lambda: model.bind_at_push(fixture.base))

        fixture, model = fresh("worktree-edit")
        model.capture("runbook")
        fixture.git("checkout", "-q", "-b", "step-1")
        fixture.write(RUNNER, RUNNER_V1)
        fixture.git("add", "-A")
        head = fixture.commit("add the runner")
        fixture.write(RUNNER, RUNNER_V2)
        attempt("uncommitted-edit-at-binding", lambda: model.bind_at_push(head))

        fixture, model = fresh("linked-leaf")
        model.capture("runbook")
        fixture.git("checkout", "-q", "-b", "step-1")
        fixture.write("tests/real_runner.py", RUNNER_V1)
        os.symlink("real_runner.py", fixture.root / RUNNER)
        fixture.git("add", "-A")
        head = fixture.commit("commit a link at the runner path")
        attempt("committed-link-at-binding", lambda: model.bind_at_push(head))
    return observed


def fresh_destination(supplied: str) -> Path:
    path = Path(supplied)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise SystemExit("report must be a relative path without traversal")
    current = Path.cwd()
    for part in path.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise SystemExit("report path crosses a link")
    if os.path.lexists(path):
        raise SystemExit("report path already exists")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=CANDIDATES)
    parser.add_argument("--criterion", choices=tuple(CRITERIA))
    parser.add_argument("--report")
    parser.add_argument("--hostile-cases", action="store_true",
                        help="print the binding model's refusal observations and write nothing")
    args = parser.parse_args(argv)
    if args.hostile_cases:
        if args.candidate or args.criterion or args.report:
            parser.error("--hostile-cases takes no other argument")
        print(json.dumps(hostile_cases(), indent=2, sort_keys=True))
        return 0
    if not (args.candidate and args.criterion and args.report):
        parser.error("--candidate, --criterion and --report are required together")
    destination = fresh_destination(args.report)
    value, unit = measure(args.candidate, args.criterion)
    if unit != CRITERIA[args.criterion]:
        raise ProbeError("unit mismatch")
    command = " ".join(["python3", ".hexaemeron/design/probe.py", "--candidate", args.candidate,
                        "--criterion", args.criterion, "--report", args.report])
    report = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
              "criterion": args.criterion, "value": value, "unit": unit,
              "command": command, "exit": 0}
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
