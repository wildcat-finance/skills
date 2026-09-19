"""Run records/signatures and retain bounded evidence; later gates refuse."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import signal
import stat
import sys
import subprocess
import tempfile
import time
from pathlib import Path
from .schema import RECORD_TYPES


CANDIDATE = "ordered-replay"
CRITERIA = (
    "records-and-signatures",
    "native-boundary-coverage",
    "authority-replay",
    "released-interoperability",
)
SOURCE_PATHS = (
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/__init__.py",
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/conformance.py",
    "plugins/hexaemeron/tests/checkpoint_authority_conformance.py",
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/canonical.py",
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/schema.py",
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/records.py",
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/signatures.py",
    "plugins/hexaemeron/skills/fiat/scripts/checkpoint_authority/trust.py",
    "plugins/hexaemeron/tests/test_checkpoint_authority_records.py",
    "plugins/hexaemeron/tests/checkpoint_authority_record_suite.py",
    "plugins/hexaemeron/tests/checkpoint_authority_corpus.py",
    "plugins/hexaemeron/tests/requirements.lock",
)
TOOLCHAIN_PATHS = (
    ".python-version",
    ".github/workflows/plugins.yml",
)
CORPUS_ROOT = "plugins/hexaemeron/skills/fiat/checkpoint-authority/"
PUBLIC_SPECIMENS = (
    "alternate-envelope.json", "bootstrap.json", "cosign-double-hashed-envelope.json",
    "cosign-envelope.json", "double-hashed-envelope.json", "hostile-records.json",
    "other-public.json", "other-public.pem", "root-public.json", "root-public.pem",
    "semantic-specimen", "trust-prefix.json", "valid-envelope.json", "wrong-public.json",
    "wrong-public.pem", "wrongcurve-public.json", "wrongcurve-public.pem",
    *(name + suffix for name in ("ssh-ed25519", "ssh-p256", "openpgp-v4")
      for suffix in ("-public.json", "-endorsement.json", "-trust-prefix.json")),
)
CORPUS_FILES = tuple(sorted((
    *(CORPUS_ROOT + "fixtures/" + kind + ".json" for kind in RECORD_TYPES),
    *(CORPUS_ROOT + "schemas/" + kind + ".schema.json" for kind in RECORD_TYPES),
    *(CORPUS_ROOT + "fixtures/" + name for name in PUBLIC_SPECIMENS),
    CORPUS_ROOT + "tool-profile.json",
)))
MANIFEST_PATH = (
    "plugins/hexaemeron/skills/fiat/checkpoint-authority/fixtures/manifest.json"
)
MAX_INPUT_BYTES = 64 * 1024
MAX_REPORT_BYTES = 16 * 1024
REFUSED_EXIT = 3
REPORT_PREFIX = ".hexaemeron/reports/"
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class Refusal(ValueError):
    """Carry a fixed diagnostic code without untrusted input or OS messages."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("invalid-invocation")


def _json_bytes(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _identity(value: os.stat_result) -> tuple:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
        value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


def _same_directory(value: os.stat_result, other: os.stat_result) -> bool:
    return (value.st_dev, value.st_ino) == (other.st_dev, other.st_ino)


@contextlib.contextmanager
def _directory(root: Path, parts: tuple[str, ...], *, create: bool = False):
    """Hold no-follow directory descriptors and detect observed namespace drift."""
    with contextlib.ExitStack() as stack:
        root_before = root.lstat()
        descriptor = os.open(root, DIRECTORY_FLAGS)
        stack.callback(os.close, descriptor)
        if not _same_directory(root_before, os.fstat(descriptor)):
            raise Refusal("directory-changed")
        links = []
        for part in parts:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            stack.callback(os.close, child)
            links.append((descriptor, part, child))
            descriptor = child

        def check():
            if not _same_directory(root_before, root.lstat()):
                raise Refusal("directory-changed")
            for parent, part, child in links:
                named = os.stat(part, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISDIR(named.st_mode) or not _same_directory(
                    named, os.fstat(child)
                ):
                    raise Refusal("directory-changed")

        check()
        yield descriptor, check
        check()


def _read(root: Path, relative: str) -> bytes:
    parts = tuple(relative.split("/"))
    with _directory(root, parts[:-1]) as (parent, check):
        descriptor = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=parent,
        )
        try:
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > MAX_INPUT_BYTES
            ):
                raise Refusal("unsafe-source")
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                data = stream.read(MAX_INPUT_BYTES + 1)
            if len(data) > MAX_INPUT_BYTES or _identity(before) != _identity(
                os.fstat(descriptor)
            ) or _identity(before) != _identity(
                os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            ):
                raise Refusal("source-changed-or-oversized")
            check()
            return data
        finally:
            os.close(descriptor)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("invalid-manifest")
        result[key] = value
    return result


def _inputs(root: Path) -> dict:
    data = _read(root, MANIFEST_PATH)
    try:
        manifest = json.loads(data, object_pairs_hook=_unique_object)
    except (ValueError, RecursionError, UnicodeError):
        raise Refusal("invalid-manifest") from None
    scaffold = {
        "schema": "checkpoint-authority-conformance-corpus/v1", "candidate": CANDIDATE,
        "criteria": list(CRITERIA), "cases": [], "implemented_criteria": [],
    }
    implemented = manifest != scaffold
    if implemented:
        if (type(manifest) is not dict or set(manifest) != set(scaffold) | {"files"}
            or manifest["schema"] != scaffold["schema"] or manifest["candidate"] != CANDIDATE
            or manifest["criteria"] != list(CRITERIA)
            or manifest["implemented_criteria"] != ["records-and-signatures"]
            or type(manifest["cases"]) is not list or not 1 <= len(manifest["cases"]) <= 100
            or type(manifest["files"]) is not list or not 1 <= len(manifest["files"]) <= 128):
            raise Refusal("unsupported-manifest")
        if (any(type(case) is not str or not re.fullmatch(r"test_checkpoint_authority_records\.[A-Za-z]+\.test_[a-z0-9_]+", case) for case in manifest["cases"])
            or manifest["cases"] != sorted(set(manifest["cases"]))):
            raise Refusal("unsupported-manifest")
        paths = []
        for row in manifest["files"]:
            if type(row) is not dict or set(row) != {"path", "sha256"} or type(row["path"]) is not str or type(row["sha256"]) is not str:
                raise Refusal("unsupported-manifest")
            path = row["path"]
            if not re.fullmatch(r"plugins/hexaemeron/skills/fiat/checkpoint-authority/(?:fixtures|schemas)/[a-z0-9.-]+|plugins/hexaemeron/skills/fiat/checkpoint-authority/tool-profile.json", path) or path == MANIFEST_PATH:
                raise Refusal("unsupported-manifest")
            if hashlib.sha256(_read(root,path)).hexdigest() != row["sha256"]:
                raise Refusal("fixture-drift")
            paths.append(path)
        if tuple(paths) != CORPUS_FILES:
            raise Refusal("unsupported-manifest")
    return {
        "implemented": implemented, "cases": manifest["cases"],
        "source": [
            {"path": path, "sha256": hashlib.sha256(_read(root, path)).hexdigest()}
            for path in (*SOURCE_PATHS, *(TOOLCHAIN_PATHS if implemented else ()))
        ],
        "fixture_manifest": {
            "path": MANIFEST_PATH, "sha256": hashlib.sha256(data).hexdigest(),
        },
    }


def _create(parent: int, name: str, data: bytes) -> None:
    if len(data) > MAX_REPORT_BYTES:
        raise Refusal("report-limit")
    descriptor = os.open(
        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600, dir_fd=parent,
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _write(root: Path, name: str, report: dict, evidence: dict) -> None:
    with _directory(root, (".hexaemeron", "reports"), create=True) as (parent, check):
        evidence_name = name[:-5] + ".evidence.json"
        for member in (name, evidence_name):
            try:
                os.stat(member, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise Refusal("report-exists")
        check()
        # A partial pair remains non-success evidence and is never overwritten.
        _create(parent, evidence_name, _json_bytes(evidence))
        check()
        _create(parent, name, _json_bytes(report))
        check()


def _execute(root):
    command = [sys.executable, str(root / "plugins/hexaemeron/tests/checkpoint_authority_record_suite.py")]
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(command, cwd=root, stdout=stdout, stderr=stderr,
                                   stdin=subprocess.DEVNULL, start_new_session=True)
        deadline = time.monotonic() + 120
        try:
            while process.poll() is None:
                if time.monotonic() > deadline or os.fstat(stdout.fileno()).st_size > 65536 or os.fstat(stderr.fileno()).st_size > 16384:
                    raise Refusal("execution-limit")
                time.sleep(0.02)
        finally:
            # Reporter exit does not establish that its descendants stopped.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        stdout.seek(0); stderr.seek(0)
        out, err = stdout.read(65537), stderr.read(16385)
        if len(out) > 65536 or len(err) > 16384:
            raise Refusal("execution-limit")
        try:
            value = json.loads(out, object_pairs_hook=_unique_object)
        except (ValueError, UnicodeError, RecursionError):
            raise Refusal("execution-report") from None
        _validate_execution(value, root)
        return value, process.returncode, hashlib.sha256(out).hexdigest(), hashlib.sha256(err).hexdigest()


def _validate_execution(value, root):
    counters = ("tests_run", "subtests_run", "failures", "errors", "skips",
                "expected_failures", "unexpected_successes", "output_bytes")
    fields = {"schema", "complete", "passed", "started", "completed", "output_sha256",
              "tools", "python", "schema_tools", "failure_cases", "error_cases", *counters}
    if (type(value) is not dict or set(value) != fields
        or value["schema"] != "checkpoint-authority-record-execution/v1"
        or any(type(value[field]) is not bool for field in ("complete", "passed"))
        or any(type(value[field]) is not int or not 0 <= value[field] <= 1000000 for field in counters)
        or type(value["output_sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", value["output_sha256"])):
        raise Refusal("execution-report")
    for field in ("started", "completed", "failure_cases", "error_cases"):
        if type(value[field]) is not list or len(value[field]) > 100 or any(
            type(case) is not str or not re.fullmatch(r"test_checkpoint_authority_records\.[A-Za-z]+\.test_[a-z0-9_]+", case)
            for case in value[field]):
            raise Refusal("execution-report")
    for field, counter in (("failure_cases", "failures"), ("error_cases", "errors")):
        if (value[field] != sorted(set(value[field])) or len(value[field]) > value[counter]
            or bool(value[field]) != bool(value[counter]) or not set(value[field]).issubset(value["started"])):
            raise Refusal("execution-report")
    rows = value["tools"]
    if type(rows) is not list or len(rows) != 4:
        raise Refusal("execution-report")
    for row, name in zip(rows, ("openssl", "ssh-keygen", "gpg", "cosign")):
        if (type(row) is not dict or set(row) != {"name", "sha256"} or row["name"] != name
            or type(row["sha256"]) is not str or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
            raise Refusal("execution-report")
    profile = json.loads(_read(root, CORPUS_ROOT + "tool-profile.json"))
    if value["schema_tools"] != profile["schema_tools"] or value["python"] != _read(root, ".python-version").decode().strip():
        raise Refusal("execution-toolchain")


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    """Return 0 only for complete passing cases; later criteria retain exit 3."""
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--report", required=True)
    try:
        args = parser.parse_args(argv)
        if args.candidate != CANDIDATE:
            raise Refusal("unsupported-candidate")
        if args.criterion not in CRITERIA:
            raise Refusal("unknown-criterion")
        name = CANDIDATE + "-" + args.criterion + ".json"
        if args.report != REPORT_PREFIX + name:
            raise Refusal("unsafe-report-path")
        if root is None:
            root = Path(__file__).absolute().parents[6]
        inputs = _inputs(root)
        command = (
            "python3 plugins/hexaemeron/tests/checkpoint_authority_conformance.py"
            " --candidate " + CANDIDATE + " --criterion " + args.criterion
            + " --report " + args.report
        )
        report = {
            "schema": "protasis-design-report/v1",
            "candidate": CANDIDATE,
            "criterion": args.criterion,
            "value": False,
            "unit": "boolean",
            "command": command,
            "exit": REFUSED_EXIT,
        }
        event = {
            "schema": "checkpoint-authority-conformance-evidence/v1",
            "event": "checkpoint_authority_conformance_refused",
            "stage": "implementation",
            "code": "criterion-not-implemented",
            "status": "unresolved",
            "candidate": CANDIDATE,
            "criterion": args.criterion,
            "complete": False,
            "executed_cases": [],
            "exit": REFUSED_EXIT,
            "design_report_sha256": hashlib.sha256(_json_bytes(report)).hexdigest(),
            **inputs,
        }
        if inputs["implemented"] and args.criterion == "records-and-signatures":
            execution, runner_exit, stdout_hash, stderr_hash = _execute(root)
            passed = (runner_exit == 0 and execution.get("complete") is True
                      and execution.get("passed") is True
                      and sorted(execution.get("started", [])) == inputs["cases"]
                      and execution.get("started") == execution.get("completed")
                      and execution.get("tests_run") == len(inputs["cases"])
                      and all(type(execution.get(field)) is int and execution[field] == 0
                              for field in ("failures", "errors", "skips", "expected_failures", "unexpected_successes")))
            if _inputs(root) != inputs:
                raise Refusal("source-changed")
            report["value"], report["exit"] = passed, 0 if passed else 1
            event.update(event="checkpoint_authority_conformance_complete" if passed else "checkpoint_authority_conformance_refused",
                         stage="records-and-signatures", code="cases-passed" if passed else "cases-failed",
                         status="passed" if passed else "failed", complete=passed,
                         executed_cases=execution.get("completed", []), exit=report["exit"],
                         execution={key:value for key,value in execution.items() if key not in ("started", "completed")},
                         runner_exit=runner_exit, stdout_sha256=stdout_hash, stderr_sha256=stderr_hash,
                         design_report_sha256=hashlib.sha256(_json_bytes(report)).hexdigest())
        event.pop("implemented"); event.pop("cases")
        if inputs["implemented"] and args.criterion == "native-boundary-coverage":
            from . import native_conformance
            event = native_conformance.run(root, report)
        _write(root, name, report, event)
    except (Refusal, OSError) as error:
        code = str(error) if isinstance(error, Refusal) else "unsafe-or-unavailable-file"
        print(json.dumps({
            "event": "checkpoint_authority_conformance_refused",
            "stage": "invocation", "code": code, "complete": False, "exit": 2,
        }, sort_keys=True))
        return 2
    print(json.dumps(event, sort_keys=True))
    return report["exit"]
