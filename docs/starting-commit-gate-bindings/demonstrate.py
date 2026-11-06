#!/usr/bin/env python3
"""Resolve the skills#2042 ``base-commit-controller-demonstration`` cell.

Only the selected candidate, ``base-commit-bindings``, and that one criterion
resolve here. The demonstration rebuilds the Hexaemeron tree of the starting
commit of run #1872 with ``git archive``, asserts the controller and adapter
digests the study records before running either, and drives that literal
1.6.77 controller through ``init``, ``done study``, ``done runbook`` and a
signed ``done implement`` in a disposable repository whose base commit holds
the registered CLI modules as that commit shipped them. The checked-in
controller then verifies the run, records a supersession and verifies again,
and three negative cases keep their refusal or legacy path with no byte
written under the fixture's state directory. The unfixed controller of this
run's starting commit is rebuilt the same way and reproduces the original
refusal on the same run.

The report is one closed ``protasis-design-report/v1`` object created
exclusively at the caller-named path; every other observation lands in a
sidecar created exclusively beside it, ``<report>.evidence.json``. A refusal
writes nothing. Nothing is written under ``docs/`` or ``.hexaemeron/`` except
those two files, and the disposable directories are removed on exit.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time

# The adapter and the test helpers are loaded as modules; nothing here caches bytecode.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = "base-commit-bindings"
CRITERION = "base-commit-controller-demonstration"
EVIDENCE_SCHEMA = "skills-2042-base-commit-controller-demonstration/v1"
# The starting commit of run #1872 and the controller bytes it shipped: the
# digests the study records, asserted before that tree runs anything.
BASE_COMMIT = "d162d0952782f09659370b6a554c9cd4511b8db9"
BASE_VERSION = "1.6.77"
BASE_LEDGER_VERSION = "fiat-v6.74.1"
CONTROLLER_SHA256 = "fa2cfc3dda1e3cef1a8a1829dbebee7e17cdd1887e0ee54e38e1c38fa2ea35f3"
ADAPTER_SHA256 = "ac527913dc737184f2a918cdd693aa4be2e16d813736060f870a17b98fdfd119"
# This run's own starting commit, whose controller refused run #1872.
UNFIXED_COMMIT = "dd2e6939ed460dcd987457a398a2765822349588"
UNFIXED_VERSION = "1.6.92"
UNFIXED_CONTROLLER_SHA256 = "e07e2c0065f6f2b18c01a29a312a5034889c417b8702ef25b3bdf028ee6d89ce"
PLUGIN = "plugins/hexaemeron"
CONTROLLER = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
ADAPTER = "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
PLUGIN_MANIFEST = "plugins/hexaemeron/.claude-plugin/plugin.json"
LEDGER = "plugins/hexaemeron/skills/fiat/EVOLUTION.md"
# The registered CLI modules outside the plugin tree, archived beside it so
# every pin of the base adapter has its module in the fixture.
OUTSIDE_MODULES = ("plugins/brevitas/skills/brevitas/scripts/brevitas.py", "scripts/run_checks.py")
# The module the #1872 runbook names, edited inside the run for the first
# negative case.
NAMED_MODULE = "plugins/hexaemeron/skills/protasis/scripts/protasis.py"
TESTS = ROOT / "plugins/hexaemeron/tests"
FIXED_CONTROLLER = ROOT / CONTROLLER
ORIGIN_URL = "https://github.com/wildcat-finance/example.git"
STUDY = "# Study\n\n```risk-register\ncontroller-skew | gate | name the recorded controller\n```\n"
COMMAND = "python3 " + NAMED_MODULE + " study.md"
RUNBOOK = ("# Runbook\n\n## Step 1: Gate\n\n**Goal.** Validate.\n**Entry.** Source.\n"
           "**Exit.** `" + COMMAND + "`\n**Files.** file.py\n**Tests.** Test interface.\n"
           "**Disciplines.** phylax: no execution.\n")
UNREGISTERED = "unregistered-cli-module-bindings"
PIN_SKEW = "pinned at different commits"
GIT_TIMEOUT_SECONDS = 120
CONTROLLER_TIMEOUT_SECONDS = 300
# The controller source is about 1.3 MiB; the cap bounds what one read holds.
OUTPUT_CAP_BYTES = 4 << 20
ARCHIVE_CAP_BYTES = 256 << 20
EXCERPT_BYTES = 2048
STRIPPED_GIT_VARIABLES = (
    "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE",
    "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX",
)
# Runs the historical controller with its init event's `gate_commands` marker
# withheld, the way the harness's historical construction builds a run that
# predates the marker; nothing else in the controller changes.
LEGACY_INIT = '''import importlib.util, os, sys
source = sys.argv[1]
spec = importlib.util.spec_from_file_location("legacy_fixture_controller", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
original = module.commit
def first_commit(base_dir, state, event, data):
    if event != "init" or os.path.exists(module.ledger_path(base_dir)):
        raise AssertionError("the legacy construction applies to the init event only")
    state["contracts"].pop("gate_commands")
    data["contracts"] = dict(state["contracts"])
    return original(base_dir, state, event, data)
module.commit = first_commit
sys.argv = [source, *sys.argv[2:]]
module.main()
'''
GIT_SHIM = '''#!%s
import json, os, sys
log = os.environ.get("DEMONSTRATION_GIT_LOG")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
os.execv(%r, [%r, *sys.argv[1:]])
'''


class Refusal(Exception):
    """The cell cannot be resolved; nothing is written."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def excerpt(data: bytes) -> str:
    return data[:EXCERPT_BYTES].decode("utf-8", "replace")


def report_path(raw: str) -> Path:
    """Admit one caller-named destination that does not exist yet."""
    if not raw or "\x00" in raw or "\\" in raw:
        raise Refusal("report-path-unsafe")
    path = Path(raw)
    if any(part in ("", ".", "..") for part in path.parts if part != path.anchor):
        raise Refusal("report-path-escape")
    if os.path.lexists(path):
        raise Refusal("report-already-exists")
    return path


def sidecar_path(report: Path) -> Path:
    return report_path(str(report) + ".evidence.json")


def base_environment() -> dict:
    """The inherited environment without Git routing that would redirect a read."""
    environment = dict(os.environ)
    for name in STRIPPED_GIT_VARIABLES:
        environment.pop(name, None)
    return environment


def run(argv: list, *, cwd, env: dict, timeout: float) -> tuple:
    """One fixed-argv subprocess: no shell, a timeout, and output read under a cap."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        started = time.monotonic()
        try:
            completed = subprocess.run(  # phylax: allow subprocess: fixed argv, no shell
                argv, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                stdout=out, stderr=err, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            raise Refusal("timeout: " + argv[0] + " after " + str(timeout) + "s") from None
        wall_ms = int((time.monotonic() - started) * 1000)
        out.seek(0)
        stdout = out.read(OUTPUT_CAP_BYTES + 1)
        err.seek(0)
        stderr = err.read(OUTPUT_CAP_BYTES + 1)
    if len(stdout) > OUTPUT_CAP_BYTES or len(stderr) > OUTPUT_CAP_BYTES:
        raise Refusal("output-cap-exceeded: " + argv[0])
    return completed.returncode, stdout, stderr, wall_ms


def module_bindings(blob: bytes) -> dict:
    """The adapter's `MODULE_BINDINGS` table read as data, never imported."""
    tree = ast.parse(blob)
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "MODULE_BINDINGS"
                           for target in node.targets)]
    if len(assignments) != 1:
        raise Refusal("adapter-pin-table-unreadable")
    table = ast.literal_eval(assignments[0].value)
    if type(table) is not dict or not all(type(k) is str and type(v) is str for k, v in table.items()):
        raise Refusal("adapter-pin-table-unreadable")
    return table


def refused_by_fixed_adapter(blobs: dict) -> list:
    """The base modules this branch's adapter refuses under its own pins alone.

    The adapter is loaded as a module and asked the question the controller
    asks before it derives anything: `parser_bindings` with no starting
    bindings. A module admitted here, through the current pin or a reviewed
    prior runner pair, is never read from the starting commit, so the
    provenance a replay reports names exactly the modules refused here.
    """
    spec = importlib.util.spec_from_file_location("demonstration_gate_commands", ROOT / ADAPTER)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    refused = []
    for path, blob in sorted(blobs.items()):
        builder = adapter.REGISTRY.get(path)
        if builder is None or path not in adapter.MODULE_BINDINGS:
            continue
        try:
            adapter.parser_bindings(ast.parse(blob, filename=path), builder, path, sha256(blob))
        except adapter.Refusal as exc:
            if str(exc) == UNREGISTERED:
                refused.append(path)
    return refused


def snapshot(root: Path) -> dict:
    """Every entry below root with its type and, for a file, its digest."""
    entries = {}
    for directory, names, files in os.walk(root, followlinks=False):
        for name in names + files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries[relative] = ("link", os.readlink(path))
            elif path.is_dir():
                entries[relative] = ("directory", None)
            else:
                entries[relative] = ("file", sha256(path.read_bytes()))
    return entries


class Tools:
    """The two attributes the harness's fake delivery tools read."""

    def __init__(self, directory: str):
        self.dir = directory
        self.env = {}


class Demonstration:
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.env = base_environment()
        self.records = []
        self.gh_log = workspace / "gh.log"
        self.git_logs = 0
        self.real_git = shutil.which("git", path=self.env.get("PATH"))
        if self.real_git is None:
            raise Refusal("git-unavailable")

    # -- this repository ---------------------------------------------------

    def repository_git(self, *args) -> bytes:
        code, out, err, _ = run([self.real_git, *args], cwd=ROOT, env=self.env,
                                timeout=GIT_TIMEOUT_SECONDS)
        if code != 0:
            raise Refusal("repository-git-failed: " + " ".join(args[:2]) + ": " + excerpt(err).strip())
        return out

    def blob(self, commit: str, path: str) -> bytes:
        return self.repository_git("--no-replace-objects", "cat-file", "blob", commit + ":" + path)

    def archive(self, commit: str, paths: tuple, destination: Path) -> int:
        """Extract `paths` at `commit` below `destination`; the archive is read from disk."""
        tar_path = self.workspace / ("archive-" + str(len(self.records)) + "-" + commit[:12] + ".tar")
        with open(tar_path, "wb") as handle, tempfile.TemporaryFile() as err:
            try:
                completed = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
                    [self.real_git, "archive", "--format=tar", commit, *paths], cwd=str(ROOT),
                    env=self.env, stdin=subprocess.DEVNULL, stdout=handle, stderr=err,
                    timeout=GIT_TIMEOUT_SECONDS, check=False)
            except subprocess.TimeoutExpired:
                raise Refusal("timeout: git archive " + commit[:12]) from None
            err.seek(0)
            detail = excerpt(err.read(EXCERPT_BYTES))
        if completed.returncode != 0:
            raise Refusal("base-commit-unavailable: " + commit[:12] + ": " + detail.strip())
        size = tar_path.stat().st_size
        if size > ARCHIVE_CAP_BYTES:
            raise Refusal("archive-cap-exceeded: " + commit[:12])
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path) as archive:
            archive.extractall(destination, filter="data")
        tar_path.unlink()
        return size

    def rebuilt_controller(self, label: str, commit: str, expected: dict) -> dict:
        """One historical controller tree, its digests asserted before any use."""
        home = self.workspace / label
        size = self.archive(commit, (PLUGIN,), home)
        observed = {path: sha256((home / path).read_bytes()) for path in (CONTROLLER, ADAPTER)}
        for path, digest in expected.items():
            if observed[path] != digest:
                raise Refusal(label + "-digest-mismatch: " + path + " is " + observed[path])
        manifest = json.loads((home / PLUGIN_MANIFEST).read_bytes())
        ledger = (home / LEDGER).read_text(encoding="utf-8")
        current = [line for line in ledger.splitlines() if line.startswith("- Current version:")]
        return {
            "label": label, "commit": commit, "home": home, "archive_bytes": size,
            "hexctl": str(home / CONTROLLER), "controller_sha256": observed[CONTROLLER],
            "adapter_sha256": observed[ADAPTER], "package_version": manifest.get("version"),
            "ledger_version": current[0].split("`")[1] if len(current) == 1 and current[0].count("`") >= 2 else None,
            "module_bindings": module_bindings((home / ADAPTER).read_bytes()),
        }

    # -- fixture tooling -----------------------------------------------------

    def install_tools(self) -> None:
        """The fixture's own signing key, the harness's fake GitHub client, and a logging git."""
        sys.path.insert(0, str(TESTS))
        from fixture_tools import native_signing_tools  # noqa: E402  (test helpers, not copied here)
        from hexctl_harness import HexctlCase  # noqa: E402
        self.signing = native_signing_tools()
        self.tools = self.signing.__enter__()
        self.env = base_environment()
        home = self.workspace / "h"
        home.mkdir(mode=0o700)
        socket_path = os.path.realpath(home / "S.gpg-agent.browser")
        if len(os.fsencode(socket_path)) >= 104:
            raise Refusal("gpg-home-path-too-long")
        self.gpg_home = str(home)
        self.env["GNUPGHOME"] = self.gpg_home
        code, _, err, _ = run(
            [self.tools["gpg"], "--batch", "--pinentry-mode", "loopback", "--passphrase", "",
             "--quick-generate-key", "Fixture <fixture@example.invalid>", "ed25519", "sign", "0"],
            cwd=self.workspace, env=self.env, timeout=60)
        if code != 0:
            raise Refusal("fixture-key-generation-failed: " + excerpt(err).strip())
        holder = Tools(str(self.workspace / "tools"))
        HexctlCase.install_fake_delivery_tools(holder)
        fake_bin = Path(holder.dir, "delivery-tools")
        (fake_bin / "git").unlink()
        shim_dir = self.workspace / "git-shim"
        shim_dir.mkdir()
        shim = shim_dir / "git"
        shim.write_text(GIT_SHIM % (sys.executable, self.real_git, self.real_git), encoding="utf-8")
        shim.chmod(0o755)
        self.env["PATH"] = os.pathsep.join([str(shim_dir), str(fake_bin), self.env.get("PATH", "")])
        self.env["FAKE_GH_LOG"] = str(self.gh_log)
        self.harness = HexctlCase

    def kill_agent(self) -> None:
        tools = getattr(self, "tools", None)
        if tools and getattr(self, "gpg_home", None):
            subprocess.run(  # phylax: allow subprocess: fixed argv, no shell
                [tools["gpgconf"], "--homedir", self.gpg_home, "--kill", "gpg-agent"],
                check=False, capture_output=True, timeout=10)
        signing = getattr(self, "signing", None)
        if signing is not None:
            signing.__exit__(None, None, None)
            self.signing = None

    def fixture_git(self, cwd: Path, *args) -> str:
        code, out, err, _ = run(["git", *args], cwd=cwd, env=self.env, timeout=GIT_TIMEOUT_SECONDS)
        if code != 0:
            raise Refusal("fixture-git-failed: " + " ".join(args[:2]) + ": " + excerpt(err).strip())
        return out.decode("utf-8", "replace").strip()

    def origin(self, name: str) -> dict:
        """A repository whose signed base commit holds the base tree's modules."""
        directory = self.workspace / name
        self.archive(BASE_COMMIT, (PLUGIN, *OUTSIDE_MODULES), directory)
        self.fixture_git(directory, "init", "-q", "-b", "main")
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid"),
                           ("commit.gpgsign", "true"), ("user.signingkey", "fixture@example.invalid"),
                           ("gpg.format", "openpgp")):
            self.fixture_git(directory, "config", key, value)
        self.fixture_git(directory, "remote", "add", "origin", ORIGIN_URL)
        self.fixture_git(directory, "add", "-A")
        self.fixture_git(directory, "commit", "-q", "-S", "-m", "Fixture base: the tree of " + BASE_COMMIT[:12])
        base = self.fixture_git(directory, "rev-parse", "HEAD")
        return {"name": name, "dir": directory, "base": base}

    @staticmethod
    def target(origin: dict) -> Path:
        crumb = origin["dir"] / ".hexaemeron" / "worktree"
        recorded = crumb.read_text(encoding="utf-8").strip()
        if not recorded or not (Path(recorded) / ".hexaemeron" / "state.json").is_file():
            raise Refusal("run-worktree-missing: " + origin["name"])
        return Path(recorded)

    # -- controller invocations ---------------------------------------------

    def controller(self, which: dict, origin: dict, *args, cwd=None, expect: int = 0,
                   boundary: str, wrapper: str | None = None) -> dict:
        """Run one controller command and record it; a wrong exit refuses."""
        self.git_logs += 1
        git_log = self.workspace / ("git-" + str(self.git_logs) + ".log")
        env = {**self.env, "DEMONSTRATION_GIT_LOG": str(git_log)}
        program = [sys.executable, which["hexctl"]] if wrapper is None else [sys.executable, "-c", wrapper, which["hexctl"]]
        directory = cwd or self.target(origin)
        state_dir = directory / ".hexaemeron"
        before = snapshot(state_dir) if state_dir.is_dir() else None
        code, out, err, wall_ms = run([*program, *args], cwd=directory, env=env,
                                      timeout=CONTROLLER_TIMEOUT_SECONDS)
        after = snapshot(state_dir) if state_dir.is_dir() else None
        git_argv = []
        if git_log.is_file():
            git_argv = [json.loads(line) for line in git_log.read_text(encoding="utf-8").splitlines() if line]
        record = {
            "boundary": boundary, "controller": which["label"], "run": origin["name"],
            "argv": ["hexctl", *args], "exit": code, "wall_ms": wall_ms,
            "stdout": excerpt(out), "stderr": excerpt(err),
            "state_unchanged": before is not None and before == after,
            "git_calls": len(git_argv),
            "starting_commit_reads": [argv for argv in git_argv if "cat-file" in argv],
        }
        self.records.append(record)
        if code != expect:
            raise Refusal(boundary + ": exit " + str(code) + " (expected " + str(expect) + "): "
                          + excerpt(out).strip() + " " + excerpt(err).strip())
        record["stdout_bytes"] = out
        record["stderr_bytes"] = err
        return record

    def gate_status(self, which: dict, origin: dict, boundary: str) -> tuple:
        record = self.controller(which, origin, "status", "--field", "gate_command_status", boundary=boundary)
        return json.loads(record.pop("stdout_bytes")), record

    def state(self, which: dict, origin: dict, boundary: str) -> dict:
        record = self.controller(which, origin, "status", "--json", boundary=boundary)
        return json.loads(record.pop("stdout_bytes"))

    @staticmethod
    def require(condition: bool, boundary: str, detail: str) -> None:
        if not condition:
            raise Refusal(boundary + ": " + detail)

    # -- runs ------------------------------------------------------------------

    def receipted_run(self, which: dict, origin: dict, *, legacy: bool = False,
                      implement: bool = True) -> dict:
        """Drive init, study, runbook and, unless told otherwise, a signed implementation."""
        tag = origin["name"] + "/"
        self.controller(which, origin, "init", "--topic", "Base controller demonstration",
                        cwd=origin["dir"], boundary=tag + "init", wrapper=LEGACY_INIT if legacy else None)
        target = self.target(origin)
        self.harness.write_design_evidence(Tools(str(target)), str(target))
        (target / "study.md").write_text(STUDY, encoding="utf-8")
        self.controller(which, origin, "done", "study", "--artifact", "study.md",
                        "--skills", "hexaemeron:protasis", boundary=tag + "done-study")
        state = self.state(which, origin, tag + "status")
        design = state["receipts"]["study"]["design_evidence"]
        lock = ("```design-lock\nschema | " + design["schema"] + "\nsha256 | " + design["sha256"]
                + "\ncandidate | " + design["selected"] + "\n```\n")
        (target / "runbook.md").write_text(lock + "\n" + RUNBOOK, encoding="utf-8")
        (target / "steps.json").write_text(json.dumps(["Gate"]), encoding="utf-8")
        self.controller(which, origin, "done", "runbook", "--artifact", "runbook.md",
                        "--steps-file", "steps.json", boundary=tag + "done-runbook")
        run_branch = self.fixture_git(target, "rev-parse", "--abbrev-ref", "HEAD")
        result = {"origin": origin, "target": target, "run_branch": run_branch}
        if not implement:
            return result
        branch = run_branch + "-step-1-gate"
        self.fixture_git(target, "switch", "-q", "-c", branch)
        (target / "step-1.txt").write_text("tree content for the receipt\n", encoding="utf-8")
        self.fixture_git(target, "add", "step-1.txt")
        self.fixture_git(target, "commit", "-q", "-S", "-m", "Step 1 implementation")
        commit = self.fixture_git(target, "rev-parse", "HEAD")
        self.controller(which, origin, "done", "implement", "--branch", branch, "--commit", commit,
                        boundary=tag + "done-implement")
        result.update({"branch": branch, "commit": commit})
        return result

    def positive_path(self, base: dict, unfixed: dict, fixed: dict, moved: list, derived: list) -> dict:
        """The 1.6.77 run: refused by the unfixed controller, verified and superseded by this one."""
        origin = self.origin("run-base")
        run = self.receipted_run(base, origin)
        self.controller(base, origin, "verify", boundary="run-base/verify-under-base")
        # Elenchus: the original refusal, reproduced against the controller of
        # this run's starting commit before any later controller touches the run.
        refused = self.controller(unfixed, origin, "verify", expect=1, boundary="run-base/verify-under-unfixed")
        detail = refused["stderr"]
        self.require(UNREGISTERED in detail and PIN_SKEW in detail, "run-base/verify-under-unfixed",
                     "the refusal does not name the pin skew: " + detail.strip())
        self.require(refused["state_unchanged"], "run-base/verify-under-unfixed", "a refusal wrote state")
        unfixed_status, record = self.gate_status(unfixed, origin, "run-base/status-under-unfixed")
        self.require(unfixed_status.get("cause") == "controller-pin-skew", "run-base/status-under-unfixed",
                     json.dumps(unfixed_status))
        skewed = sorted(row["module"] for row in unfixed_status.get("modules", []))
        self.require(set(derived) <= set(skewed) <= set(moved), "run-base/status-under-unfixed",
                     json.dumps(unfixed_status))
        self.require(record["state_unchanged"], "run-base/status-under-unfixed", "status wrote state")
        verified = self.controller(fixed, origin, "verify", boundary="run-base/verify-under-fixed")
        self.require(verified["stdout"].startswith("ok: "), "run-base/verify-under-fixed", verified["stdout"])
        self.require(verified["state_unchanged"], "run-base/verify-under-fixed", "verify wrote state")
        provenance = {"starting_commit": origin["base"], "adapter_sha256": ADAPTER_SHA256, "modules": derived}
        status, record = self.gate_status(fixed, origin, "run-base/status-under-fixed")
        self.require(status == {"status": "current", "validation": "interface-only", "provenance": provenance},
                     "run-base/status-under-fixed", json.dumps(status))
        self.require(record["state_unchanged"], "run-base/status-under-fixed", "status wrote state")
        target = run["target"]
        self.fixture_git(target, "commit", "--amend", "--no-edit", "-S", "-q")
        replacement = self.fixture_git(target, "rev-parse", "HEAD")
        self.require(replacement != run["commit"], "run-base/amend", "the amended commit kept its id")
        self.require(self.fixture_git(target, "rev-parse", run["commit"] + "^{tree}")
                     == self.fixture_git(target, "rev-parse", replacement + "^{tree}"),
                     "run-base/amend", "the amended commit changed the tree")
        superseded = self.controller(fixed, origin, "supersede-commit", "--old", run["commit"],
                                     "--new", replacement, boundary="run-base/supersede-commit")
        self.require("receipted; original receipt retained" in superseded["stdout"],
                     "run-base/supersede-commit", superseded["stdout"])
        ledger = (target / ".hexaemeron" / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        last_event = json.loads([line for line in ledger if line.strip()][-1])["event"]
        self.require(last_event == "commit:supersede", "run-base/supersede-commit", "last event " + last_event)
        verified = self.controller(fixed, origin, "verify", boundary="run-base/verify-after-supersession")
        self.require(verified["stdout"].startswith("ok: "), "run-base/verify-after-supersession", verified["stdout"])
        self.require(verified["state_unchanged"], "run-base/verify-after-supersession", "verify wrote state")
        status, _ = self.gate_status(fixed, origin, "run-base/status-after-supersession")
        self.require(status == {"status": "current", "validation": "interface-only", "provenance": provenance},
                     "run-base/status-after-supersession", json.dumps(status))
        # Negative case 1: a registered module edited inside the run.
        module = target / NAMED_MODULE
        original = module.read_bytes()
        module.write_bytes(original + b"\nREVISION_EDITED_IN_RUN = True\n")
        refused = self.controller(fixed, origin, "verify", expect=1, boundary="run-base/edited-module-verify")
        detail = refused["stderr"]
        self.require(UNREGISTERED in detail and NAMED_MODULE + " changed inside the run since its starting commit" in detail
                     and PIN_SKEW not in detail, "run-base/edited-module-verify", detail.strip())
        self.require(refused["state_unchanged"], "run-base/edited-module-verify", "a refusal wrote state")
        status, record = self.gate_status(fixed, origin, "run-base/edited-module-status")
        self.require(status.get("cause") == "module-edited-in-run" and status.get("modules") == [
            {"module": NAMED_MODULE, "since_base": "changed", "named_by_runbook": True}],
            "run-base/edited-module-status", json.dumps(status))
        self.require(record["state_unchanged"], "run-base/edited-module-status", "status wrote state")
        module.write_bytes(original)
        restored = self.controller(fixed, origin, "verify", boundary="run-base/restored-module-verify")
        self.require(restored["stdout"].startswith("ok: "), "run-base/restored-module-verify", restored["stdout"])
        return {
            "fixture_base": origin["base"], "run_branch": run["run_branch"], "step_branch": run["branch"],
            "receipted_commit": run["commit"], "replacement_commit": replacement,
            "provenance": provenance, "unfixed_status": unfixed_status, "ledger_entries": len(ledger),
        }

    def forged_adapter_run(self, base: dict, fixed: dict) -> dict:
        """Negative case 2: a receipt whose adapter digest is neither the base's nor reviewed."""
        home = self.workspace / "base-controller-forged"
        shutil.copytree(base["home"], home, symlinks=True)
        adapter = home / ADAPTER
        adapter.write_bytes(adapter.read_bytes() + b"\n# A later build of the same release.\n")
        forged = {**base, "label": "base-controller-forged", "home": home, "hexctl": str(home / CONTROLLER),
                  "adapter_sha256": sha256(adapter.read_bytes())}
        self.require(forged["adapter_sha256"] != ADAPTER_SHA256, "run-forged/controller", "the forged adapter kept its digest")
        origin = self.origin("run-forged")
        self.receipted_run(forged, origin)
        self.controller(forged, origin, "verify", boundary="run-forged/verify-under-forged")
        receipts = self.state(forged, origin, "run-forged/status")["receipts"]
        receipt_digest = receipts["runbook"]["gate_commands"]["adapter_sha256"]
        self.require(receipt_digest == forged["adapter_sha256"], "run-forged/receipt", receipt_digest)
        refused = self.controller(fixed, origin, "verify", expect=1, boundary="run-forged/verify-under-fixed")
        detail = refused["stderr"]
        self.require("gate-receipt-drift" in detail and UNREGISTERED not in detail,
                     "run-forged/verify-under-fixed", detail.strip())
        self.require(refused["state_unchanged"], "run-forged/verify-under-fixed", "a refusal wrote state")
        status, record = self.gate_status(fixed, origin, "run-forged/status-under-fixed")
        self.require(status.get("status") == "stale-or-invalid" and "cause" not in status
                     and "modules" not in status
                     and "submit a freshly validated runbook amendment" in status.get("recovery", ""),
                     "run-forged/status-under-fixed", json.dumps(status))
        self.require(record["state_unchanged"], "run-forged/status-under-fixed", "status wrote state")
        return {"fixture_base": origin["base"], "receipt_adapter_sha256": receipt_digest,
                "forged_adapter_sha256": forged["adapter_sha256"],
                "forged_hexctl_sha256": forged["controller_sha256"]}

    def legacy_run(self, base: dict, fixed: dict) -> dict:
        """Negative case 3: a run without the gate marker stays legacy and reads no starting commit."""
        origin = self.origin("run-legacy")
        self.receipted_run(base, origin, legacy=True, implement=False)
        self.controller(base, origin, "verify", boundary="run-legacy/verify-under-base")
        contracts = self.state(base, origin, "run-legacy/status-under-base")["contracts"]
        self.require("gate_commands" not in contracts, "run-legacy/contracts", json.dumps(contracts))
        verified = self.controller(fixed, origin, "verify", boundary="run-legacy/verify-under-fixed")
        self.require(verified["stdout"].startswith("ok: "), "run-legacy/verify-under-fixed", verified["stdout"])
        self.require(verified["state_unchanged"], "run-legacy/verify-under-fixed", "verify wrote state")
        self.require(verified["starting_commit_reads"] == [], "run-legacy/verify-under-fixed",
                     "a legacy run read its starting commit: " + json.dumps(verified["starting_commit_reads"]))
        status, record = self.gate_status(fixed, origin, "run-legacy/status-under-fixed")
        self.require(status == {"status": "legacy", "validation": "not-recorded"},
                     "run-legacy/status-under-fixed", json.dumps(status))
        self.require(record["state_unchanged"] and record["starting_commit_reads"] == [],
                     "run-legacy/status-under-fixed", "status wrote state or read the starting commit")
        receipts = self.state(fixed, origin, "run-legacy/status-under-fixed-json")["receipts"]
        self.require("gate_commands" not in receipts.get("runbook", {}), "run-legacy/receipts", "a gate receipt exists")
        return {"fixture_base": origin["base"], "contracts": contracts}

    # -- the whole demonstration ------------------------------------------------

    def evidence(self) -> dict:
        base = self.rebuilt_controller("base-controller", BASE_COMMIT,
                                       {CONTROLLER: CONTROLLER_SHA256, ADAPTER: ADAPTER_SHA256})
        self.require(base["package_version"] == BASE_VERSION and base["ledger_version"] == BASE_LEDGER_VERSION,
                     "base-controller", "version " + str(base["package_version"]) + " " + str(base["ledger_version"]))
        unfixed_blob = sha256(self.blob(UNFIXED_COMMIT, CONTROLLER))
        unfixed = self.rebuilt_controller("unfixed-controller", UNFIXED_COMMIT,
                                          {CONTROLLER: UNFIXED_CONTROLLER_SHA256})
        self.require(unfixed["controller_sha256"] == unfixed_blob, "unfixed-controller",
                     "archive and blob disagree: " + unfixed_blob)
        self.require(unfixed["package_version"] == UNFIXED_VERSION, "unfixed-controller", str(unfixed["package_version"]))
        fixed_adapter = (ROOT / ADAPTER).read_bytes()
        fixed = {"label": "fixed-controller", "hexctl": str(FIXED_CONTROLLER),
                 "controller_sha256": sha256(FIXED_CONTROLLER.read_bytes()),
                 "adapter_sha256": sha256(fixed_adapter), "module_bindings": module_bindings(fixed_adapter),
                 "package_version": json.loads((ROOT / PLUGIN_MANIFEST).read_bytes()).get("version")}
        moved = sorted(path for path, pin in base["module_bindings"].items()
                       if fixed["module_bindings"].get(path) != pin)
        self.require(NAMED_MODULE in moved, "pins", "the named module's pin did not move: " + json.dumps(moved))
        self.require(unfixed["module_bindings"] == fixed["module_bindings"], "pins",
                     "the unfixed controller's pins differ from this branch's")
        blobs = {path: self.blob(BASE_COMMIT, path) for path in sorted(base["module_bindings"])}
        modules = {path: sha256(blob) for path, blob in blobs.items()}
        derived = refused_by_fixed_adapter(blobs)
        self.require(derived and NAMED_MODULE in derived and set(derived) <= set(moved), "pins",
                     "the derived set is not a subset of the moved pins: " + json.dumps(derived))
        self.install_tools()
        positive = self.positive_path(base, unfixed, fixed, moved, derived)
        forged = self.forged_adapter_run(base, fixed)
        legacy = self.legacy_run(base, fixed)
        gh_reads = []
        if self.gh_log.is_file():
            gh_reads = [json.loads(line) for line in self.gh_log.read_text(encoding="utf-8").splitlines() if line]
        for record in self.records:
            record.pop("stdout_bytes", None)
            record.pop("stderr_bytes", None)
        return {
            "schema": EVIDENCE_SCHEMA,
            "candidate": CANDIDATE,
            "criterion": CRITERION,
            "python": sys.version.split()[0],
            "controllers": {
                label: {key: value for key, value in which.items() if key not in ("home", "hexctl", "label")}
                for label, which in (("base", base), ("unfixed", unfixed), ("fixed", fixed))
            },
            "fixed_controller_path": CONTROLLER,
            "registered_modules_at_base": modules,
            "moved_pins": moved,
            "derived_modules": derived,
            "runs": {"base": positive, "forged": forged, "legacy": legacy},
            "boundaries": self.records,
            "platform_reads": {"count": len(gh_reads), "paths": sorted({argv[-1] for argv in gh_reads if argv})},
        }


def demonstrate() -> dict:
    """Run the whole demonstration in a disposable workspace, removed on exit.

    A refusal prints each boundary it had recorded, bounded, so the refusal
    names what was seen; nothing is written.
    """
    workspace = Path(tempfile.mkdtemp(prefix="d-")).resolve()
    demonstration = None
    try:
        demonstration = Demonstration(workspace)
        return demonstration.evidence()
    except Refusal:
        for record in (demonstration.records if demonstration is not None else []):
            print(json.dumps({key: value for key, value in record.items()
                              if key not in ("stdout_bytes", "stderr_bytes")}), file=sys.stderr)
        raise
    finally:
        if demonstration is not None:
            demonstration.kill_agent()
        shutil.rmtree(workspace, ignore_errors=True)


def write_exclusively(path: Path, payload: dict) -> None:
    """Create the file once; an existing file or link at the path refuses."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        destination = report_path(args.report)
        sidecar = sidecar_path(destination)
        if args.candidate != CANDIDATE:
            raise Refusal("unknown-candidate")
        if args.criterion != CRITERION:
            raise Refusal("unknown-criterion")
        evidence = demonstrate()
    except (Refusal, subprocess.SubprocessError, OSError, tarfile.TarError) as exc:
        print("refused: " + str(exc), file=sys.stderr)
        return 1
    payload = {
        "schema": "protasis-design-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": True,
        "unit": "boolean",
        "command": ("python3 docs/starting-commit-gate-bindings/demonstrate.py --candidate "
                    + args.candidate + " --criterion " + args.criterion + " --report " + args.report),
        "exit": 0,
    }
    try:
        write_exclusively(sidecar, evidence)
        write_exclusively(destination, payload)
    except FileExistsError:
        print("refused: report-already-exists", file=sys.stderr)
        return 1
    except OSError as exc:
        print("refused: report-not-written: " + str(exc), file=sys.stderr)
        return 1
    print(args.candidate + "/" + args.criterion + " = True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
