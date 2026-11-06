"""Fixed host policies for checkpoint network denial, with explicit syscall ABI.

Linux uses the distribution's Bubblewrap executable. Its namespace still has
loopback, so the inherited seccomp filter denies network calls independently.
These policies preserve the caller's filesystem access; they are not archive
or whole-host containment.
"""
from dataclasses import dataclass
import struct

from .canonical import Refusal, canonical, digest

MACOS_POLICY = "(version 1)(allow default)(deny network*)"
LINUX_ARGV = ("--unshare-net", "--unshare-pid", "--bind", "/", "/",
              "--dev-bind", "/dev", "/dev", "--die-with-parent", "--new-session",
              "--cap-drop", "ALL", "--seccomp", "0", "--")
"""The /dev bind lets cosign reopen stdin after Bubblewrap consumes seccomp fd 0.

Bubblewrap's root bind otherwise mounts devices nodev. These two binds retain
the caller's device/filesystem permissions; they grant no additional access.
The fixed verifier reads files, not a payload from stdin.
"""
DENIED_X86_64 = (*range(41, 56), 288, 299, 307, 425, 426, 427)
"""Linux x86-64 socket calls, accept4/recvmmsg/sendmmsg and io_uring entrypoints.

Source: Linux UAPI arch/x86/entry/syscalls/syscall_64.tbl and linux/audit.h.
An unmeasured ABI never reuses this table. io_uring must not submit network
work past the direct syscall filter.
"""


def linux_filter():
    """Build native x86-64 classic BPF; reject foreign and x32 syscall ABIs."""
    kill, deny, allow = 0x80000000, 0x00050001, 0x7fff0000
    rules = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e), (0x06, 0, 0, kill),
             (0x20, 0, 0, 0), (0x35, 0, 1, 0x40000000), (0x06, 0, 0, kill)]
    for number in DENIED_X86_64:
        rules.extend(((0x15, 0, 1, number), (0x06, 0, 0, deny)))
    rules.append((0x06, 0, 0, allow))
    return b"".join(struct.pack("<HBBI", *rule) for rule in rules)


@dataclass(frozen=True)
class Policy:
    platform: str
    abi: str
    mechanism: str
    launcher: str
    argv: tuple[str, ...]
    filter_bytes: bytes

    @property
    def sha256(self):
        """Bind the complete launch contract, including the exact filter bytes."""
        return digest(canonical({"platform": self.platform, "abi": self.abi,
                                 "mechanism": self.mechanism, "launcher": self.launcher,
                                 "argv": list(self.argv),
                                 "filter_sha256": digest(self.filter_bytes)}))


def for_host(system, machine):
    """Select a declared native ABI; missing or unknown profiles never fall back."""
    if system == "darwin" and machine in ("arm64", "x86_64"):
        return Policy(system, machine, "macos-sandbox-exec-deny-network",
                      "/usr/bin/sandbox-exec", ("-p", MACOS_POLICY), b"")
    if system == "linux" and machine == "x86_64":
        return Policy(system, machine, "linux-bubblewrap-seccomp-deny-network",
                      "/usr/bin/bwrap", LINUX_ARGV, linux_filter())
    raise Refusal("network-denial-unavailable", "demonstration")
