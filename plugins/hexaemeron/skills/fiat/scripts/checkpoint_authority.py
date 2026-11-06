#!/usr/bin/env python3
"""Bounded offline command line for the released checkpoint authority protocol.

Every input is a file named on the command line and read without following a
link; nothing is fetched, signed, discovered from a record, or written outside
one exclusively created report. Exit 0 means the named operation completed,
1 that the evidence refused it, and 2 that the invocation itself was rejected.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import stat
import sys

SCRIPTS = Path(__file__).absolute().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from checkpoint_authority import demo, native_io as io, release, verifier  # noqa: E402
from checkpoint_authority.canonical import Refusal, canonical, digest  # noqa: E402
from checkpoint_authority.signatures import ToolPin  # noqa: E402

STAGE = "cli"
OPERATIONS = ("verify", "release", "lock", "demonstrate")
REPORT_MAX = 4194304
HEX = re.compile(r"[0-9a-f]{64}\Z")
DEFAULT_ROOT = SCRIPTS.parents[4]
"""The checkout that owns this file; `--root` names another released tree."""


class Parser(argparse.ArgumentParser):
    """Turn every usage error into one fixed code, never an echoed operand."""

    def error(self, message):
        raise Refusal("invalid-invocation", STAGE)

    def exit(self, status=0, message=None):
        if status:
            raise Refusal("invalid-invocation", STAGE)
        raise SystemExit(0)


def _tool_pin(path, sha256):
    if path is None or sha256 is None:
        return None
    if type(path) is not str or HEX.fullmatch(sha256 or "") is None:
        raise Refusal("invalid-invocation", STAGE)
    return ToolPin("cosign", str(Path(path).absolute()), sha256)


def _root(value):
    root = Path(value).absolute() if value else DEFAULT_ROOT
    if str(root) != os.path.normpath(root):
        raise Refusal("invalid-invocation", STAGE)
    return root


def _read(path, maximum):
    try:
        return io.read(Path(path).absolute(), maximum)
    except Refusal:
        raise
    except OSError:
        raise Refusal("input-unavailable", STAGE) from None


def _write(path, data):
    """Create the report exclusively; an existing path or link is never replaced."""
    if len(data) > REPORT_MAX:
        raise Refusal("report-limit", STAGE)
    target = Path(path).absolute()
    with io.directory(target.parent) as (parent, check):
        try:
            descriptor = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                                 | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
        except FileExistsError:
            raise Refusal("report-exists", STAGE) from None
        except OSError:
            raise Refusal("report-unavailable", STAGE) from None
        with os.fdopen(descriptor, "wb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise Refusal("report-unavailable", STAGE)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        check()


def _verify(args):
    limits = verifier.LIMITS
    bootstrap = verifier.bootstrap_from(_read(args.bootstrap, limits["bootstrap_file_bytes"]))
    tools = verifier.tools_from(_read(args.tools, limits["tools_file_bytes"]))
    native = verifier.native_from(_read(args.native, limits["native_file_bytes"]))
    freshness = (verifier.freshness_from(_read(args.freshness, limits["freshness_file_bytes"]))
                 if args.freshness else None)
    presence = (verifier.presence_from(_read(args.presence, limits["presence_file_bytes"]))
                if args.presence else None)
    history = verifier.History(Path(args.history).absolute())
    result = verifier.verify(history, bootstrap, tools, native=native,
                             freshness=freshness, presence=presence)
    return dict(result, history_sha256=history.sha256, history_records=history.count)


def _release(args):
    root = _root(args.root)
    data, _ = release.committed(root)
    manifest = release.check(root)
    return {"schema": "checkpoint-authority-release-check/v1",
            "event": "checkpoint_authority_release_verified", "stage": release.STAGE,
            "code": "components-agree", "complete": True,
            "release_manifest_sha256": digest(data), "pins": manifest["pins"],
            "native": manifest["native"],
            "tools": {"cosign": manifest["tools"]["cosign"]["version"],
                      "python": manifest["tools"]["python"]},
            "components": {name: value["sha256"] for name, value in manifest["components"].items()},
            "files": sum(len(value["files"]) for value in manifest["components"].values()),
            "transitive_files": len(manifest["transitive_files"])}


def _lock(args):
    return release.lock_check(_read(args.lock, release.LOCK_MAX), _root(args.root),
                              source_commit=args.source_commit)


def _demonstrate(args):
    return demo.run(_root(args.root),
                    tools_bytes=_read(args.tools, verifier.LIMITS["tools_file_bytes"]),
                    cosign=_tool_pin(args.cosign, args.cosign_sha256))


def refusal(error):
    """One closed refusal event; no operand value or child diagnostic leaves the process."""
    return {"schema": "checkpoint-authority-cli/v1", "event": "checkpoint_authority_cli_refused",
            "stage": error.stage, "code": error.code, "complete": False,
            "current_eligibility_established": False}


def parser():
    """One closed command surface; every operand is a path, a digest or a commit."""
    root = Parser(prog="checkpoint_authority.py", description=__doc__, allow_abbrev=False)
    operations = root.add_subparsers(dest="operation", required=True)
    for name in OPERATIONS:
        command = operations.add_parser(name, allow_abbrev=False)
        command.add_argument("--root")
        command.add_argument("--out")
        if name == "verify":
            for operand in ("history", "bootstrap", "tools", "native"):
                command.add_argument("--" + operand, required=True)
            command.add_argument("--freshness")
            command.add_argument("--presence")
        if name == "lock":
            command.add_argument("--lock", required=True)
            command.add_argument("--source-commit")
        if name == "demonstrate":
            command.add_argument("--tools", required=True)
            command.add_argument("--cosign")
            command.add_argument("--cosign-sha256")
    return root


def main(argv=None):
    """Return 0 for a completed operation, 1 for a refusal and 2 for a bad invocation."""
    handlers = {"verify": _verify, "release": _release, "lock": _lock, "demonstrate": _demonstrate}
    try:
        args = parser().parse_args(argv)
        event = handlers[args.operation](args)
        data = canonical(event, limit=REPORT_MAX)
        if args.out:
            _write(args.out, data + b"\n")
        sys.stdout.write(data.decode() + "\n")
        return 0
    except Refusal as error:
        sys.stdout.write(canonical(refusal(error), limit=REPORT_MAX).decode() + "\n")
        return 2 if error.code == "invalid-invocation" else 1
    except OSError:
        sys.stdout.write(canonical(refusal(Refusal("unsafe-or-unavailable-file", STAGE)),
                                   limit=REPORT_MAX).decode() + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
