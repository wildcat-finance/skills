"""Host-enforced network denial for the independent release demonstration.

The host policies deny network operations while preserving the filesystem
permissions the caller already has. This is not archive containment.
An unsupported host refuses; an offline flag is never a substitute.
"""
from dataclasses import dataclass
from pathlib import Path
import platform
import sys

from . import native_io as io, network_policy, signatures
from .canonical import Refusal, digest

POLICY = network_policy.MACOS_POLICY
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
DESCENDANT_PROBE = ("import subprocess, sys\n"
                    "sys.exit(subprocess.run([sys.executable, '-I', '-c', " + repr(PROBE) + "]).returncode)\n")


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
    policy: network_policy.Policy

    def expected(self):
        """Return the closed expected observation without preparing a host."""
        return {"schema": "checkpoint-network-boundary/v1",
                "mechanism": self.policy.mechanism, "platform": self.policy.platform,
                "abi": self.policy.abi, "launcher_sha256": self.launcher_sha256,
                "policy_sha256": self.policy.sha256,
                "filter_sha256": digest(self.policy.filter_bytes),
                "probe_sha256": digest(PROBE.encode()), "probe_exit": 0, "probe_operations": 4,
                "descendant_probe_sha256": digest(DESCENDANT_PROBE.encode()),
                "descendant_probe_exit": 0, "descendant_probe_operations": 4}

    def run(self, pin, args, directory, *, timeout):
        if self.policy != network_policy.for_host(sys.platform, platform.machine()):
            raise Refusal("network-denial-changed", "demonstration")
        wrapped = _Wrapped(self.policy.launcher, self.launcher_sha256, pin)
        return signatures._run(wrapped, [*self.policy.argv, pin.path, *args], directory,
                               input_bytes=self.policy.filter_bytes, timeout=timeout)

    def probe(self, directory):
        path = str(Path(sys.executable).resolve(strict=True))
        python = io.NativeTool("python", path, io.hash_file(path, 268435456)[0])
        for program in (PROBE, DESCENDANT_PROBE):
            result = self.run(python, ["-I", "-c", program], directory, timeout=10)
            if result[0] != 0 or result[1] != PROBE_OUTPUT or result[2] != b"":
                raise Refusal("network-denial-probe", "demonstration")
        return self.expected()


def validate_observation(value, expected):
    """Check every field and exact scalar type against the execution owner's descriptor."""
    if (type(value) is not dict or set(value) != set(expected)
            or any(type(value[key]) is not type(wanted) or value[key] != wanted
                   for key, wanted in expected.items())):
        raise Refusal("network-denial-evidence", "demonstration")


def prepare():
    policy = network_policy.for_host(sys.platform, platform.machine())
    try:
        return Boundary(io.hash_file(policy.launcher, io.FILE_MAX)[0], policy)
    except (Refusal, OSError):
        raise Refusal("network-denial-unavailable", "demonstration") from None
