"""Read-only predicates for a separately installed macOS publisher.

The caller supplies the reviewed release digest. No credential bytes are read.
Root, administrators, interpreter integrity and undeclared copies are excluded.
"""
from __future__ import annotations

from collections.abc import Callable
import grp
import hashlib
import os
from pathlib import Path
import plistlib
import pwd
import re
import stat
import subprocess
import sys

from .canonical import canonical_json, read_bounded_file, sha256_bytes
from .errors import PublisherError
from .framing import SOCKET_PATH, validate_socket_path

SERVICE_USER = "_wildcatpublisher"
SERVICE_GROUP = "_wildcatpublishers"
SERVICE_UID = 499
SERVICE_GID = 499
WORKING_PATH = "/Library/WildcatIssuePublisher"
PROGRAM_PATH = WORKING_PATH + "/publisher-service.py"
PYTHON_PATH = WORKING_PATH + "/python3"
KEY_DIRECTORY = "/var/db/wildcat-github-issue-publisher"
KEY_PATH = KEY_DIRECTORY + "/shoggoth-wildcat-labs.pem"
DAEMON_PATH = "/Library/LaunchDaemons/finance.wildcat.issue-publisher.plist"
LABEL = "finance.wildcat.issue-publisher"
MAX_DEPLOYMENT_BYTES = 1_048_576
PREDICATES = (
    "platform", "verifier-identity", "service-identity", "caller-identity",
    "distinct-identity", "group", "parents", "key", "socket", "daemon",
    "program", "working", "interpreter", "helpers", "legacy-key", "release",
)


def daemon_document() -> dict[str, object]:
    """The closed launchd inetd contract creates one process per connection."""
    return {
        "Label": LABEL,
        "ProgramArguments": [PYTHON_PATH, "-I", PROGRAM_PATH],
        "UserName": SERVICE_USER,
        "GroupName": SERVICE_GROUP,
        "WorkingDirectory": WORKING_PATH,
        "Umask": 0o077,
        "inetdCompatibility": {"Wait": False},
        "Sockets": {"Listener": {
            "SockPathName": SOCKET_PATH, "SockPathMode": 0o660,
            "SockPathOwner": SERVICE_UID, "SockPathGroup": SERVICE_GID,
        }},
        "SoftResourceLimits": {"NumberOfFiles": 64, "NumberOfProcesses": 8,
                               "Core": 0, "CPU": 60},
        "HardResourceLimits": {"NumberOfFiles": 64, "NumberOfProcesses": 8,
                               "Core": 0, "CPU": 60},
        "StandardErrorPath": "/dev/null",
    }


def _no_acl(path: str) -> bool:
    # ls reads metadata only; its output is never exposed as a diagnostic.
    result = subprocess.run(
        ["/bin/ls", "-lde", path], stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        env={"LC_ALL": "C"}, timeout=3, check=False,
    )
    return (result.returncode == 0 and len(result.stdout) <= 8192
            and len(result.stdout.splitlines()) == 1)


class HostProbe:
    """Read metadata and bounded public program bytes; never open the key."""
    platform = sys.platform
    verifier_uid = staticmethod(os.geteuid)
    user = staticmethod(pwd.getpwnam)
    group = staticmethod(grp.getgrnam)
    groups = staticmethod(os.getgrouplist)
    lstat = staticmethod(os.lstat)
    @staticmethod
    def read(path):
        if path != DAEMON_PATH:
            raise PublisherError("GIP199", "deployment.public-file")
        return _public_read(Path(path))
    no_acl = staticmethod(_no_acl)


def _public_read(path: Path) -> bytes:
    """Read a public file through no-follow directory descriptors."""
    if not path.is_absolute() or ".." in path.parts or str(path) == KEY_PATH:
        raise PublisherError("GIP199", "deployment.release")
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    directory = os.open("/", flags | os.O_DIRECTORY)
    file = -1
    try:
        for name in path.parts[1:-1]:
            child = os.open(name, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = child
        file = os.open(path.name, flags | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(file)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                or not 0 < before.st_size <= MAX_DEPLOYMENT_BYTES):
            raise PublisherError("GIP199", "deployment.release")
        raw = os.read(file, MAX_DEPLOYMENT_BYTES + 1)
        after = os.fstat(file)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if (len(raw) != before.st_size
                or any(getattr(before, f) != getattr(after, f) for f in fields)):
            raise PublisherError("GIP199", "deployment.release")
        return raw
    finally:
        if file >= 0:
            os.close(file)
        os.close(directory)


def release_inventory(root: Path) -> dict[str, str]:
    """Hash bounded public files in the exact runtime and lexicon closure."""
    root = root.absolute()
    paths = ["publisher-service.py", "publisher-client.py", "python3",
             "plugins/hexaemeron/skills/imprimatur/SKILL.md"]
    directories = ["plugins/hexaemeron/skills/phylax/scripts/github_issue_publisher_lib",
                   "plugins/hexaemeron/skills/imprimatur/scripts",
                   "plugins/hexaemeron/skills/imprimatur/lexicon"]
    for relative in directories:
        directory = root / relative
        for parent in (directory, *directory.parents):
            if not stat.S_ISDIR(parent.lstat().st_mode):
                raise PublisherError("GIP199", "deployment.release")
        with os.scandir(directory) as entries:
            for entry in entries:
                # Installed code contains no caches, symlinks or nested packages.
                if not entry.is_file(follow_symlinks=False) or len(paths) >= 128:
                    raise PublisherError("GIP199", "deployment.release")
                paths.append(str(Path(entry.path).relative_to(root)))
    if not 10 <= len(paths) <= 128:
        raise PublisherError("GIP199", "deployment.release")
    return {path: sha256_bytes(_public_read(root / path)) for path in sorted(paths)}


def check_deployment(*, caller: str, release_sha256: str, probe=None,
                     inventory: Callable[[Path], dict[str, str]] = release_inventory
                     ) -> dict[str, object]:
    """Return fixed safe predicates. A passed snapshot never proves live isolation."""
    probe = HostProbe() if probe is None else probe
    passed = dict.fromkeys(PREDICATES, False)
    def finish():
        result = _result(passed)
        result["subject_sha256"] = sha256_bytes(canonical_json({
            "caller": caller, "release_sha256": release_sha256}))
        return result
    if (not isinstance(caller, str) or re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", caller) is None
            or not isinstance(release_sha256, str) or re.fullmatch(r"[0-9a-f]{64}", release_sha256) is None):
        return _result(passed)
    passed["platform"] = probe.platform == "darwin"
    try:
        passed["verifier-identity"] = probe.verifier_uid() == 0
        service = probe.user(SERVICE_USER)
        person = probe.user(caller)
        group = probe.group(SERVICE_GROUP)
        admin = probe.group("admin")
        passed["service-identity"] = (service.pw_name == SERVICE_USER
            and type(service.pw_uid) is int and service.pw_uid == SERVICE_UID
            and service.pw_shell == "/usr/bin/false"
            and service.pw_dir == KEY_DIRECTORY)
        passed["caller-identity"] = (person.pw_name == caller
            and type(person.pw_uid) is int and person.pw_uid > 0
            and caller not in admin.gr_mem and person.pw_gid != admin.gr_gid
            and admin.gr_gid not in probe.groups(caller, person.pw_gid))
        passed["distinct-identity"] = service.pw_uid != person.pw_uid
        passed["group"] = (group.gr_name == SERVICE_GROUP
            and type(group.gr_gid) is int and group.gr_gid == SERVICE_GID
            and service.pw_gid == group.gr_gid
            and (caller in group.gr_mem or person.pw_gid == group.gr_gid)
            and group.gr_gid in probe.groups(caller, person.pw_gid))
    except (KeyError, OSError, ValueError, AttributeError, TypeError):
        return finish()

    def metadata(path, uid, gid, mode, kind=stat.S_ISREG):
        item = probe.lstat(path)
        return (kind(item.st_mode) and item.st_uid == uid and item.st_gid == gid
                and stat.S_IMODE(item.st_mode) == mode
                and (kind == stat.S_ISDIR or item.st_nlink == 1)
                and probe.no_acl(path))

    def check(name, operation):
        try:
            passed[name] = operation() is True
        except (OSError, ValueError, TypeError, AttributeError, PublisherError,
                subprocess.SubprocessError, plistlib.InvalidFileException):
            passed[name] = False

    def parents():
        # Darwin /var is a system symlink; inspect its fixed physical target.
        for path in ("/", "/Library", "/Library/LaunchDaemons", "/private",
                     "/private/var", "/private/var/db", "/private/var/run"):
            item = probe.lstat(path)
            if (not stat.S_ISDIR(item.st_mode) or item.st_uid != 0
                    or stat.S_IMODE(item.st_mode) & 0o022 or not probe.no_acl(path)):
                return False
        return (stat.S_ISLNK(probe.lstat("/var").st_mode)
                and os.readlink("/var") == "private/var") if isinstance(probe, HostProbe) else True

    def key():
        return (metadata(KEY_DIRECTORY, service.pw_uid, group.gr_gid, 0o700, stat.S_ISDIR)
                and metadata(KEY_PATH, service.pw_uid, group.gr_gid, 0o600))

    def socket_check():
        validate_socket_path(SOCKET_PATH, service_uid=service.pw_uid,
                             service_gid=group.gr_gid, lstat=probe.lstat)
        return probe.no_acl(SOCKET_PATH)

    def daemon():
        return (metadata(DAEMON_PATH, 0, 0, 0o644)
                and probe.read(DAEMON_PATH) == plistlib.dumps(daemon_document(), sort_keys=True))

    def absent(path):
        try:
            probe.lstat(path)
        except FileNotFoundError:
            return True
        return False

    def release():
        if (len(release_sha256) != 64
                or any(c not in "0123456789abcdef" for c in release_sha256)):
            return False
        if not all(passed[name] for name in ("parents", "working", "program", "interpreter")):
            return False
        files = inventory(Path(WORKING_PATH))
        for path in files:
            full = Path(WORKING_PATH) / path
            if (Path(path).is_absolute() or ".." in Path(path).parts
                    or not metadata(str(full), 0, 0, 0o755 if path == "python3" else 0o644)):
                return False
            for parent in full.parents:
                if str(parent) == WORKING_PATH:
                    break
                if not metadata(str(parent), 0, 0, 0o755, stat.S_ISDIR):
                    return False
        return hashlib.sha256(canonical_json(files)).hexdigest() == release_sha256

    check("parents", parents)
    check("key", key)
    check("socket", socket_check)
    check("daemon", daemon)
    check("working", lambda: metadata(WORKING_PATH, 0, 0, 0o755, stat.S_ISDIR))
    check("program", lambda: metadata(PROGRAM_PATH, 0, 0, 0o644))
    check("interpreter", lambda: metadata(PYTHON_PATH, 0, 0, 0o755))
    check("helpers", lambda: all(absent(person.pw_dir + suffix) for suffix in (
        "/.config/gh-app/file_as_app.sh", "/.config/gh-app/mint_token.sh")))
    check("legacy-key", lambda: absent(person.pw_dir + "/.config/gh-app/shoggoth-wildcat-labs.pem"))
    check("release", release)
    return finish()


def _result(predicates):
    return {"schema": "github-issue-publisher-deployment/v1",
            "predicates": predicates, "outcome": "passed" if all(predicates.values()) else "refused",
            "live_isolation": "not-established",
            "boundary": "named-paths-and-identities-only"}
