"""Host-enforced network denial for the independent release demonstration.

The macOS policy denies network operations while preserving the filesystem and
process permissions the caller already has. It is not archive containment.
An unsupported host refuses; an offline flag is never a substitute.
"""
from dataclasses import dataclass
from pathlib import Path
import sys

from . import native_io as io, signatures
from .canonical import Refusal, digest

LAUNCHER = "/usr/bin/sandbox-exec"
POLICY = "(version 1)(allow default)(deny network*)"
PROBE = '''import errno, socket, sys
for family, address, label in (
    (socket.AF_INET, ('127.0.0.1', 0), 'ipv4-bind'),
    (socket.AF_INET6, ('::1', 0), 'ipv6-bind'),
    (socket.AF_INET, ('127.0.0.1', 9), 'ipv4-connect'),
    (socket.AF_INET6, ('::1', 9), 'ipv6-connect'),
):
    operation = 'bind' if label.endswith('bind') else 'connect'
    try:
        with socket.socket(family, socket.SOCK_STREAM) as connection:
            connection.settimeout(1)
            getattr(connection, operation)(address)
    except OSError as error:
        if error.errno != errno.EPERM:
            sys.exit(2)
    else:
        sys.exit(1)
    print(label + '-denied')
'''
PROBE_OUTPUT = b"ipv4-bind-denied\nipv6-bind-denied\nipv4-connect-denied\nipv6-connect-denied\n"


@dataclass(frozen=True)
class _Wrapped:
    """Check the host launcher and the actual verifier around the same child run."""
    path: str
    sha256: str
    inner: object

    def check(self):
        self.inner.check()
        try:
            observed = io.hash_file(self.path, io.FILE_MAX)[0]
        except (Refusal, OSError):
            raise Refusal("network-denial-unavailable", "demonstration") from None
        if observed != self.sha256:
            raise Refusal("network-denial-changed", "demonstration")


@dataclass(frozen=True)
class Boundary:
    launcher_sha256: str

    def run(self, pin, args, directory, *, timeout):
        wrapped = _Wrapped(LAUNCHER, self.launcher_sha256, pin)
        return signatures._run(wrapped, ["-p", POLICY, pin.path, *args], directory, timeout=timeout)

    def probe(self, directory):
        path = str(Path(sys.executable).resolve(strict=True))
        python = io.NativeTool("python", path, io.hash_file(path, 268435456)[0])
        result = self.run(python, ["-I", "-c", PROBE], directory, timeout=10)
        if result[0] != 0 or result[1] != PROBE_OUTPUT:
            raise Refusal("network-denial-probe", "demonstration")
        return {"mechanism": "macos-sandbox-exec-deny-network",
                "launcher_sha256": self.launcher_sha256, "policy_sha256": digest(POLICY.encode()),
                "probe_sha256": digest(PROBE.encode()), "probe_exit": 0, "probe_operations": 4}


def prepare():
    if sys.platform != "darwin":
        raise Refusal("network-denial-unavailable", "demonstration")
    try:
        return Boundary(io.hash_file(LAUNCHER, io.FILE_MAX)[0])
    except (Refusal, OSError):
        raise Refusal("network-denial-unavailable", "demonstration") from None
