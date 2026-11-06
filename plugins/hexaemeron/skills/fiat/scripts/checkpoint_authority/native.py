"""Execute one pinned, public-only native checkpoint verification attempt."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
import time

from .canonical import Refusal, canonical, decode, digest
from .coverage import ApprovedRun, derive, verify_complete
from . import native_io as io
from .native_records import (CONTROLLER, CONTROLLER_SHA256, NATIVE_COMMIT, PROFILE,
    count, hexadecimal, identity_result, inspect_result, ledger, metadata, restore_result)
from .signatures import b64decode

LAYOUT_SHA256 = "dca86cde305bd5b1bce7daf6bfac7b86c71a855504d8733baaa768dd07e1389e"
PROFILE_PATH = Path(__file__).absolute().parents[2] / "checkpoint-authority/native-profile.json"


@dataclass(frozen=True)
class NativePin:
    """Trusted caller-owned source layout and executable pins, never record locators."""
    source_root: Path
    tools: tuple[io.NativeTool, ...]

    def check(self):
        payload = io.read(PROFILE_PATH, 65536)
        if digest(payload) != LAYOUT_SHA256:
            raise Refusal("native-profile-drift", "native")
        profile = decode(payload)
        if profile["source_commit"] != NATIVE_COMMIT or profile["executable_sha256"] != CONTROLLER_SHA256:
            raise Refusal("native-source-pin", "native")
        if type(self.tools) is not tuple or [tool.name for tool in self.tools] != ["python", "git", "gpg", "gpgconf"]:
            raise Refusal("native-tools-required", "native")
        for tool in self.tools: tool.check()
        for row in profile["files"]:
            if io.hash_file(self.source_root / row["path"])[0] != row["sha256"]:
                raise Refusal("native-source-pin", "native")
        return profile

    def tool(self, name):
        return next(tool for tool in self.tools if tool.name == name)


@dataclass(frozen=True)
class NativeInput:
    attempt_id: str
    lease_id: str
    candidate_id: str
    outer_sha256: str
    snapshot_id: str
    controller_manifest_sha256: str
    carrier_length: int

    def check(self):
        for name in ("attempt_id", "lease_id", "candidate_id"):
            if type(getattr(self, name)) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", getattr(self, name)) is None:
                raise Refusal("native-attempt-binding", "native")
        for name in ("outer_sha256", "snapshot_id", "controller_manifest_sha256"):
            hexadecimal(getattr(self, name))
        count(self.carrier_length, io.CARRIER_MAX, minimum=1)

    def record(self):
        self.check()
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


@dataclass(frozen=True)
class NativeResult:
    """Current execution evidence. It grants no acceptance, freshness or resume action."""
    payload: bytes
    directory: Path

    @property
    def record(self):
        return decode(self.payload, require_canonical=True)


class _Attempt:
    def __init__(self, root, pin, request, approval):
        self.root, self.pin, self.request, self.approval = root, pin, request, approval
        self.started = time.monotonic()
        self.deadline = self.started + 900
        self.stages = []
        self.environment = {}
        self.source_profile = pin.check()

    def command(self, name, args, cwd, stage, *, input_bytes=b""):
        result = io.execute(self.pin.tool(name), args, cwd, self.environment,
            stage=stage, attempt_id=self.request.attempt_id,
            input_sha256=self.request.outer_sha256,
            deadline=min(self.deadline, time.monotonic() + 120), input_bytes=input_bytes)
        if (not isinstance(result, io.Execution) or result.stage != stage
            or result.attempt_id != self.request.attempt_id
            or result.input_sha256 != self.request.outer_sha256
            or type(result.exit) is not int or type(result.stdout) is not bytes
            or type(result.stderr) is not bytes or len(result.stdout) > io.STDOUT_MAX
            or len(result.stderr) > io.STDERR_MAX):
            raise Refusal("native-current-attempt", stage)
        if stage in ("inspect", "restore", "verify", "identity"):
            expected = ("inspect", "restore", "verify", "identity")[len(self.stages)]
            if stage != expected:
                raise Refusal("native-stage-order", stage)
            io.create(self.root / (stage + ".stdout"), result.stdout)
            io.create(self.root / (stage + ".stderr"), result.stderr)
            self.stages.append(result.summary())
        if result.exit != 0:
            raise Refusal("native-command-failed", stage)
        return result

    def seed(self):
        keys = self.approval.keys()
        home = self.root / "home"; home.mkdir(mode=0o700)
        temporary = self.root / "tmp"; temporary.mkdir(mode=0o700)
        binary = self.root / "bin"; binary.mkdir(mode=0o700)
        for tool in self.pin.tools:
            os.symlink(tool.path, binary / ("python3" if tool.name == "python" else tool.name))
        self.environment = {"PATH": str(binary) + ":/usr/local/bin:/usr/bin:/bin",
            "HOME": str(home), "GNUPGHOME": str(home), "TMPDIR": str(temporary),
            "LC_ALL": "C", "LANG": "C.UTF-8", "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_TERMINAL_PROMPT": "0", "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_NO_LAZY_FETCH": "1", "GIT_CONFIG_COUNT": "6",
            "GIT_CONFIG_KEY_0": "core.hooksPath", "GIT_CONFIG_VALUE_0": "/dev/null",
            "GIT_CONFIG_KEY_1": "core.fsmonitor", "GIT_CONFIG_VALUE_1": "false",
            "GIT_CONFIG_KEY_2": "credential.helper", "GIT_CONFIG_VALUE_2": "",
            "GIT_CONFIG_KEY_3": "gpg.program", "GIT_CONFIG_VALUE_3": self.pin.tool("gpg").path,
            "GIT_CONFIG_KEY_4": "protocol.allow", "GIT_CONFIG_VALUE_4": "never",
            "GIT_CONFIG_KEY_5": "protocol.file.allow", "GIT_CONFIG_VALUE_5": "always"}
        unique = {}
        for row in keys:
            fingerprint, data = row["key"]["fingerprint"], b64decode(row["key"]["public"])
            if fingerprint in unique and unique[fingerprint] != data:
                raise Refusal("native-key-history-ambiguous", "trust")
            unique[fingerprint] = data
        public = b"".join(unique[key] for key in sorted(unique))
        io.create(home / "pubring.gpg", public)
        io.create(home / "gpg.conf", b"no-auto-key-retrieve\nno-autostart\n")
        prefix = ["--batch", "--no-options", "--no-auto-key-retrieve", "--no-autostart",
                  "--homedir", str(home), "--no-default-keyring", "--keyring", str(home / "pubring.gpg")]
        listed = self.command("gpg", [*prefix, "--with-colons", "--list-keys"], home, "trust")
        lines = listed.stdout.decode("ascii", errors="replace").splitlines()
        actual = []
        for index, line in enumerate(lines):
            if line.startswith("pub:"):
                if index + 1 >= len(lines) or not lines[index + 1].startswith("fpr:"):
                    raise Refusal("native-public-key", "trust")
                actual.append(lines[index + 1].split(":")[9])
        if sorted(actual) != sorted(unique):
            raise Refusal("native-public-key", "trust")
        for fingerprint, data in unique.items():
            exported = self.command("gpg", [*prefix, "--export", fingerprint], home, "trust")
            if exported.stdout != data:
                raise Refusal("native-public-key", "trust")
        secret = self.command("gpg", [*prefix, "--with-colons", "--list-secret-keys"], home, "trust")
        if any(line.startswith(b"sec:") or line.startswith(b"ssb:") for line in secret.stdout.splitlines()):
            raise Refusal("native-private-key-refused", "trust")
        self.trust_sha256 = digest(public)
        self.keyring = home / "pubring.gpg"

    def native(self, stage, args):
        self.pin.check()
        result = self.command("python", ["-I", str(self.pin.source_root / CONTROLLER), *args], self.root, stage)
        self.pin.check()
        if io.hash_file(self.keyring)[0] != self.trust_sha256:
            raise Refusal("native-trust-changed", stage)
        return result

    def git(self, args):
        result = self.command("git", ["--no-replace-objects", "-c", "core.hooksPath=/dev/null",
            "-c", "core.fsmonitor=false", "-c", "credential.helper=", "-c", "protocol.allow=never",
            "-c", "gpg.program=" + self.pin.tool("gpg").path, *args], self.worktree, "coverage")
        return result.stdout

    def verify_commit(self, commit):
        hexadecimal(commit, commit=True)
        result = self.command("git", ["--no-replace-objects", "-c", "gpg.format=openpgp",
            "-c", "gpg.program=" + self.pin.tool("gpg").path, "verify-commit", "--raw", commit],
            self.worktree, "coverage")
        lines = [line.split() for line in result.stderr.decode("ascii", errors="replace").splitlines()
                 if line.startswith("[GNUPG:] VALIDSIG ")]
        if len(lines) != 1 or len(lines[0]) != 12 or re.fullmatch(r"[0-9A-F]{40}", lines[0][-1]) is None:
            raise Refusal("native-signature-invalid", "coverage")
        return lines[0][-1]

    def run(self, archive):
        captured = self.root / "input.zip"
        size = io.copy_archive(archive, captured, self.request.outer_sha256)
        if size != self.request.carrier_length:
            raise Refusal("native-input-length", "native")
        meta = metadata(captured)
        if digest(meta.manifest_bytes) != self.request.controller_manifest_sha256:
            raise Refusal("native-controller-manifest", "native")
        self.seed()
        inspect_scratch = self.root / "inspect"; inspect_scratch.mkdir(mode=0o700)
        inspected = inspect_result(decode(self.native("inspect", ["checkpoint", "inspect", "--archive", str(captured),
            "--sha256", self.request.outer_sha256, "--scratch", str(inspect_scratch)]).stdout))
        if (inspected["outer_sha256"] != self.request.outer_sha256 or inspected["bytes"] != size
            or inspected["identity"]["snapshot_id"] != self.request.snapshot_id
            or inspected["refs"] != meta.manifest["boundary"]["refs"]):
            raise Refusal("native-inspect-input", "inspect")
        destination = self.root / "origin"
        if os.path.lexists(destination):
            raise Refusal("native-destination-occupied", "restore")
        restored = restore_result(decode(self.native("restore", ["--dir", str(destination), "checkpoint", "restore",
            "--archive", str(captured), "--sha256", self.request.outer_sha256]).stdout))
        inner = restored["restore"]
        expected_worktree = destination / "tmp/fiat" / meta.state["run_branch"].replace("/", "-")
        if inner["worktree"] != str(expected_worktree) or not expected_worktree.is_relative_to(destination):
            raise Refusal("native-worktree-outside-attempt", "restore")
        self.worktree = expected_worktree
        with io.directory(destination, private=True) as (_, check_destination), io.directory(self.worktree) as (_, check_worktree):
            if (restored["outer_sha256"] != self.request.outer_sha256 or restored["snapshot_id"] != self.request.snapshot_id
                or inner["manifest_sha256"] != self.request.controller_manifest_sha256
                or inner["source_state_sha256"] != digest(meta.state_bytes)
                or inner["source_ledger_sha256"] != digest(meta.ledger_bytes)
                or inner["refs"] != len(inspected["refs"])
                or restored["next"] != meta.manifest["boundary"]["next"]):
                raise Refusal("native-restore-input", "restore")
            verify = self.native("verify", ["--dir", str(self.worktree), "verify", "--observations"])
            match = re.fullmatch(rb"ok: ([1-9][0-9]*) ledger entries, chain intact, state consistent; ([1-9][0-9]*) observation prefixes verified\n", verify.stdout)
            if match is None or int(match[1]) != inner["ledger_entries"]:
                raise Refusal("native-observations-unavailable", "verify")
            reconstructed = identity_result(decode(self.native("identity", ["--dir", str(self.worktree), "checkpoint", "identity"]).stdout))
            evidence = reconstructed["identity"]["evidence"]
            if (reconstructed["snapshot_id"] != self.request.snapshot_id
                or evidence["ledger_sha256"] != digest(meta.ledger_bytes)
                or evidence["ledger_tail"] != meta.entries[-1]["hash"]
                or evidence["ledger_entries"] != len(meta.entries)
                or evidence["observation_bindings"] != int(match[2])):
                raise Refusal("native-identity-input", "identity")
            current_ledger = io.read(self.worktree / ".hexaemeron/ledger.jsonl")
            current_state = io.read(self.worktree / ".hexaemeron/state.json")
            rows = ledger(current_ledger)
            if (not current_ledger.startswith(meta.ledger_bytes) or len(rows) != len(meta.entries) + 1
                or rows[-1]["event"] != "checkpoint:restore" or digest(current_ledger) != inner["ledger_sha256"]
                or rows[-1]["hash"] != inner["ledger_tail"]
                or rows[-1]["data"].get("manifest_sha256") != self.request.controller_manifest_sha256
                or rows[-1]["state"] != digest(canonical(decode(current_state, limit=io.FILE_MAX), limit=io.FILE_MAX))):
                raise Refusal("native-immediate-restore-tail", "identity")
            coverage = verify_complete(derive(meta, reconstructed, self.approval, self.git),
                                       inspected, self.approval, self.verify_commit)
            check_destination(); check_worktree()
            if (io.read(self.worktree / ".hexaemeron/ledger.jsonl") != current_ledger
                or io.read(self.worktree / ".hexaemeron/state.json") != current_state
                or io.hash_file(captured, io.CARRIER_MAX) != (self.request.outer_sha256, size)):
                raise Refusal("native-attempt-changed", "native")
        return {"schema": "checkpoint-authority-native-result/v1", "complete": True,
            "request": self.request.record(), "source_commit": NATIVE_COMMIT,
            "executable_sha256": CONTROLLER_SHA256, "profile": PROFILE,
            "source_profile_sha256": LAYOUT_SHA256,
            "tools": [{"name": tool.name, "sha256": tool.sha256} for tool in self.pin.tools],
            "public_trust_sha256": self.trust_sha256, "native_results": self.stages,
            "identity": reconstructed, "status_sha256": restored["status_sha256"],
            "next": restored["next"], "coverage": coverage,
            "operation_ran": True, "historical_commands_executed": False,
            "current_eligibility": "unknown", "service_acceptance": "unavailable",
            "resources": {"input_bytes": size, "output_bytes": sum(row["output_bytes"] for row in self.stages),
                "duration_ms": int((time.monotonic() - self.started) * 1000)}}


def verify_native(archive, *, job_root, pin, request, approval):
    """Run a fresh attempt and leave its bounded private success or refusal evidence.

    The caller supplies an already isolated environment with an exclusively
    owned private job root. This function proves observed pathname ownership,
    not kernel isolation, aggregate descendant resources or atomic renames.
    It never follows a record-carried external locator or executes a directive.
    """
    if not isinstance(pin, NativePin) or not isinstance(request, NativeInput) or not isinstance(approval, ApprovedRun):
        raise Refusal("native-caller-input", "native")
    request.check(); approval.keys()
    job_root = Path(job_root)
    try:
        with io.directory(job_root, private=True) as (parent, check_job):
            try:
                os.mkdir(request.attempt_id, mode=0o700, dir_fd=parent)
            except FileExistsError:
                raise Refusal("native-attempt-exists", "native") from None
            check_job()
            root = job_root / request.attempt_id
            with io.directory(root, private=True) as (_, check_attempt):
                io.create(root / "input.json", canonical(request.record()))
                try:
                    attempt = _Attempt(root, pin, request, approval)
                    record = attempt.run(Path(archive))
                    pin.check(); check_attempt(); check_job()
                    payload = canonical(record)
                    io.create(root / "result.json", payload)
                    check_attempt(); check_job()
                    return NativeResult(payload, root)
                except (Refusal, OSError, subprocess.SubprocessError) as error:
                    refusal = error if isinstance(error, Refusal) else Refusal("native-execution-unavailable", "native")
                    io.create(root / "refusal.json", canonical(refusal.event()))
                    raise refusal from None
    except OSError:
        raise Refusal("native-scratch-unavailable", "native") from None
