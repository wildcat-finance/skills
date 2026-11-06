#!/usr/bin/env python3
"""Invoke the literal owner CLI after installing Python socket instrumentation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import socket
import sys


class NetworkDenied(RuntimeError):
    """The demonstrated Python socket path was attempted."""


def _write_new(path, value):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode())


def install_guard():
    """Keep socket subclass compatibility while refusing construction and DNS."""
    counter = [0]
    original = socket.socket

    def deny(*args, **kwargs):
        counter[0] += 1
        raise NetworkDenied("Python network operation denied")

    class GuardedSocket(original):
        def __new__(cls, *args, **kwargs):
            return deny(*args, **kwargs)

    socket.socket = GuardedSocket
    socket.SocketType = GuardedSocket
    for name in ("create_connection", "getaddrinfo", "gethostbyname",
                 "gethostbyname_ex", "gethostbyaddr", "getnameinfo"):
        setattr(socket, name, deny)
    return counter


def loaded_modules():
    rows = []
    for name, module in sorted(sys.modules.items()):
        raw = getattr(module, "__file__", None)
        if not raw:
            continue
        path = Path(raw).resolve()
        if not path.is_file():
            raise ValueError("loaded module origin is unavailable")
        if path.suffix == ".pyc":
            raise ValueError("cached bytecode executed in the demonstrated path")
        data = path.read_bytes()
        rows.append({"name": name, "path": str(path), "bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest()})
    return {"schema": "wildcat-v3-loaded-modules/v1", "modules": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--guard-report", required=True)
    parser.add_argument("--modules-report", required=True)
    parser.add_argument("cli", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    cli = args.cli[1:] if args.cli[:1] == ["--"] else args.cli
    counter = install_guard()
    status, exception = 0, None
    try:
        if cli[:1] == ["diagnostic"]:
            if cli == ["diagnostic", "compatibility"]:
                import http.client
                import ssl
                import urllib.request
            elif cli == ["diagnostic", "socket"]:
                socket.socket()
            elif cli == ["diagnostic", "dns"]:
                socket.getaddrinfo("example.invalid", 443)
            elif cli == ["diagnostic", "connect"]:
                socket.create_connection(("example.invalid", 443))
            else:
                raise ValueError("unknown network diagnostic")
        else:
            entry = Path(args.repo) / "plugins/tabularium/scripts/tabularium.py"
            if not cli or Path(cli[0]) != entry or entry.is_symlink():
                raise ValueError("literal owner CLI entry differs")
            sys.path.insert(0, str(entry.parent))
            sys.argv = list(cli)
            runpy.run_path(str(entry), run_name="__main__")
    except SystemExit as error:
        if type(error.code) is not int:
            status, exception = 2, "NonIntegerSystemExit"
        else:
            status = error.code
    except BaseException as error:
        status, exception = 1, type(error).__name__
        if not isinstance(error, NetworkDenied):
            print("offline wrapper failed: " + exception, file=sys.stderr)
    finally:
        _write_new(args.modules_report, loaded_modules())
        _write_new(args.guard_report, {"schema": "wildcat-v3-network-observation/v1",
                                      "attempts": counter[0], "exception": exception,
                                      "cli_exit": status})
    return status


if __name__ == "__main__":
    raise SystemExit(main())
