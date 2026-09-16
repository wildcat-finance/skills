"""Write bounded, non-success evidence for protocol gates awaiting implementation."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import stat
import sys
from pathlib import Path


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
)
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
    if manifest != {
        "schema": "checkpoint-authority-conformance-corpus/v1",
        "candidate": CANDIDATE,
        "criteria": list(CRITERIA),
        "cases": [],
        "implemented_criteria": [],
    }:
        raise Refusal("unsupported-manifest")
    return {
        "source": [
            {"path": path, "sha256": hashlib.sha256(_read(root, path)).hexdigest()}
            for path in SOURCE_PATHS
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


def main(argv: list[str] | None = None, *, root: Path | None = None) -> int:
    """Return 3 for an unimplemented gate, or 2 for an invalid/unsafe request.

    Output contains fixed diagnostic codes. Each admitted invocation writes one
    closed Protasis report with value false and exit 3, plus its evidence file.
    Neither result establishes protocol conformance or authority.
    """
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
        _write(root, name, report, event)
    except (Refusal, OSError) as error:
        code = str(error) if isinstance(error, Refusal) else "unsafe-or-unavailable-file"
        print(json.dumps({
            "event": "checkpoint_authority_conformance_refused",
            "stage": "invocation", "code": code, "complete": False, "exit": 2,
        }, sort_keys=True))
        return 2
    print(json.dumps(event, sort_keys=True))
    return REFUSED_EXIT
