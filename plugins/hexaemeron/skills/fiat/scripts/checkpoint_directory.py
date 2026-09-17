"""Bounded directory carrier for complete, large Git checkpoint bundles.

The caller supplies the pinned controller implementation. The manifest digest
travels out of band; every consumed member is captured before verification.
Filesystem clones are independent copy-on-write files, never hard links.
"""

import ctypes
import errno
import fcntl
import hashlib
import os
import re
import stat
import sys
import time


IO_CHUNK = 1024 * 1024
UNSUPPORTED_CLONE = {errno.ENOTSUP, errno.EXDEV, errno.EINVAL, errno.ENOSYS, errno.ENOTTY}


def clone_file(source_fd, destination):
    """Clone an already opened file, or return False for a stream-copy fallback."""
    if sys.platform == "darwin":
        library = ctypes.CDLL(None, use_errno=True)
        operation = getattr(library, "fclonefileat", None)
        if operation is None:
            return False
        operation.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        operation.restype = ctypes.c_int
        parent = os.open(os.path.dirname(destination), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            result = operation(source_fd, parent, os.fsencode(os.path.basename(destination)), 0)
            if result == 0:
                os.chmod(destination, 0o600)
                return True
            code = ctypes.get_errno()
            if code in UNSUPPORTED_CLONE:
                return False
            raise OSError(code, "checkpoint clone failed")
        finally:
            os.close(parent)
    if sys.platform.startswith("linux"):
        target = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            # Linux UAPI FICLONE takes the held source descriptor, not a path.
            fcntl.ioctl(target, 0x40049409, source_fd)
            return True
        except OSError as error:
            if error.errno not in UNSUPPORTED_CLONE:
                raise
        finally:
            os.close(target)
        os.unlink(destination)
    return False


def open_member(h, root_fd, name):
    """Walk only validated components, pinning every directory without links."""
    parts = name.split("/")
    current = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = child
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW,
                             dir_fd=current)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o7111:
            os.close(descriptor)
            h._checkpoint_archive_refuse("entry-mode")
        return descriptor, info
    except OSError:
        h._checkpoint_archive_refuse("entry-mode")
    finally:
        os.close(current)


def capture(h, root_fd, name, destination, ceiling, deadline, *, clone=False, expected_bytes=None):
    """Capture, hash and scan one stable regular file under a fixed byte cap."""
    source, before = open_member(h, root_fd, name)
    target = None
    reader = None
    copied = 0
    digest = hashlib.sha256()
    secret = False
    window = b""
    try:
        if expected_bytes is not None and before.st_size != expected_bytes:
            h._checkpoint_archive_refuse("manifest-mismatch")
        if before.st_size > ceiling:
            h._checkpoint_archive_refuse("entry-limit")
        os.makedirs(os.path.dirname(destination), mode=0o700, exist_ok=True)
        cloned = clone and clone_file(source, destination)
        if cloned:
            reader = os.open(destination, os.O_RDONLY | os.O_NOFOLLOW)
        else:
            reader = source
            target = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        while True:
            if time.monotonic() > deadline:
                h.die("checkpoint directory capture timed out", 1)
            chunk = os.read(reader, IO_CHUNK)
            if not chunk:
                break
            copied += len(chunk)
            if copied > ceiling or copied > before.st_size:
                h._checkpoint_archive_refuse("manifest-mismatch")
            digest.update(chunk)
            if target is not None:
                h._checkpoint_write_all(target, chunk)
            if not secret and h._checkpoint_archive_secret_shaped(window + chunk):
                secret = True
            window = (window + chunk)[-h.CHECKPOINT_ARCHIVE_SECRET_WINDOW:]
        if target is not None:
            os.fsync(target)
        after = os.fstat(source)
        if copied != before.st_size or h._checkpoint_stat_identity(before) != h._checkpoint_stat_identity(after):
            h._checkpoint_archive_refuse("manifest-mismatch")
        return copied, digest.hexdigest(), secret
    except OSError:
        h.die("checkpoint directory member could not be captured", 1)
    finally:
        if target is not None:
            os.close(target)
        if reader is not None and reader != source:
            os.close(reader)
        os.close(source)


def inventory(h, root_fd, expected):
    """Require exactly the manifest's regular files and their parent directories."""
    directories = {""}
    for name in expected:
        parts = name.split("/")
        directories.update("/".join(parts[:at]) for at in range(1, len(parts)))
    if len(directories) > h.CHECKPOINT_DIRECTORIES_MAX:
        h._checkpoint_archive_refuse("entry-limit")
    seen = set()

    def walk(descriptor, prefix):
        before = os.fstat(descriptor)
        with os.scandir(descriptor) as iterator:
            count = 0
            for entry in iterator:
                count += 1
                if count > h.CHECKPOINT_ARCHIVE_ENTRIES_MAX * 2:
                    h._checkpoint_archive_refuse("entry-limit")
                name = prefix + "/" + entry.name if prefix else entry.name
                info = os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    if name not in directories:
                        h._checkpoint_archive_refuse("manifest-mismatch")
                    child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                    dir_fd=descriptor)
                    try:
                        if h._checkpoint_stat_identity(info) != h._checkpoint_stat_identity(os.fstat(child)):
                            h._checkpoint_archive_refuse("manifest-mismatch")
                        walk(child, name)
                    finally:
                        os.close(child)
                else:
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o7111:
                        h._checkpoint_archive_refuse("entry-mode")
                    if name not in expected:
                        h._checkpoint_archive_refuse("manifest-mismatch")
                    seen.add(name)
        if h._checkpoint_stat_identity(before) != h._checkpoint_stat_identity(os.fstat(descriptor)):
            h._checkpoint_archive_refuse("manifest-mismatch")

    try:
        walk(root_fd, "")
    except OSError:
        h._checkpoint_archive_refuse("entry-mode")
    if seen != expected:
        h._checkpoint_archive_refuse("manifest-mismatch")


def inspect(h, archive, expected_digest, scratch, *, existing_repo=None):
    """Verify a captured carrier and return only its private verified read view."""
    if not isinstance(expected_digest, str) or re.fullmatch(r"[0-9a-f]{64}", expected_digest) is None:
        h.die("checkpoint inspect requires a lowercase SHA-256 --sha256")
    try:
        root = os.open(archive, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        h._checkpoint_archive_refuse("entry-mode")
    local = os.path.join(scratch, "directory-members")
    try:
        os.mkdir(local, 0o700)
    except OSError:
        os.close(root)
        h.die("checkpoint directory scratch could not be created", 1)
    deadline = time.monotonic() + h.CHECKPOINT_DIRECTORY_TOOL_TIMEOUT
    manifest_name = h.CHECKPOINT_ARCHIVE_MANIFEST_ENTRY
    manifest_path = os.path.join(local, manifest_name)
    captured = {}
    physical = []
    try:
        size, digest, secret_found = capture(h, root, manifest_name, manifest_path,
                                           h.CHECKPOINT_MANIFEST_BYTES_MAX, deadline)
        if digest != expected_digest:
            h._checkpoint_archive_refuse("outer-digest-mismatch")
        with open(manifest_path, "rb") as handle:
            manifest_bytes = handle.read(h.CHECKPOINT_MANIFEST_BYTES_MAX + 1)
        manifest = h._checkpoint_archive_guarded("schema-unsupported", lambda:
            h._checkpoint_inspect_manifest_shape(manifest_bytes, directory=True))
        records = manifest["archive"]["entries"]
        names = [manifest_name, *(row["path"] for row in records)]
        h._checkpoint_inspect_name_policy(names)
        if len(names) > h.CHECKPOINT_ARCHIVE_ENTRIES_MAX:
            h._checkpoint_archive_refuse("entry-limit")
        inventory(h, root, set(names))
        total = size
        for record in records:
            name = record["path"]
            bundle = name == h.CHECKPOINT_ARCHIVE_BUNDLE_ENTRY
            ceiling = h.CHECKPOINT_DIRECTORY_BUNDLE_BYTES_MAX if bundle else h.CHECKPOINT_ARCHIVE_ENTRY_BYTES_MAX
            if record["bytes"] > ceiling:
                h._checkpoint_archive_refuse("entry-limit")
            total += record["bytes"]
            if total > h.CHECKPOINT_DIRECTORY_EXPANDED_BYTES_MAX:
                h._checkpoint_archive_refuse("entry-limit")
        for record in records:
            name = record["path"]
            destination = os.path.join(local, *name.split("/"))
            size, digest, secret = capture(h, root, name, destination, record["bytes"], deadline,
                                           clone=name == h.CHECKPOINT_ARCHIVE_BUNDLE_ENTRY,
                                           expected_bytes=record["bytes"])
            if size != record["bytes"] or digest != record["sha256"]:
                h._checkpoint_archive_refuse("manifest-mismatch")
            secret_found |= secret
            physical.append({"name": name, "size": size, "data_offset": 0})
            if name in h.CHECKPOINT_INSPECT_CAPTURE_ENTRIES:
                with open(destination, "rb") as handle:
                    captured[name] = handle.read(h.CHECKPOINT_ARCHIVE_ENTRY_BYTES_MAX + 1)
        inventory(h, root, set(names))
    finally:
        os.close(root)
    sidecar_path = archive + ".sha256"
    if os.path.lexists(sidecar_path):
        try:
            handle = h._checkpoint_inspect_open_regular(sidecar_path)
            if handle is None:
                h._checkpoint_archive_refuse("sidecar-mismatch")
            with handle:
                sidecar = handle.read(4096)
        except OSError:
            h._checkpoint_archive_refuse("sidecar-mismatch")
        if sidecar != f"{expected_digest}  {os.path.basename(archive)}\n".encode():
            h._checkpoint_archive_refuse("sidecar-mismatch")
    capsule = h._checkpoint_inspect_capsule(manifest, captured.get(h.CHECKPOINT_INSPECT_CAPSULE_MANIFEST_ENTRY))
    bundle_path = os.path.join(local, h.CHECKPOINT_ARCHIVE_BUNDLE_ENTRY)
    heads, prerequisites, algorithm = h._checkpoint_inspect_bundle_heads(manifest, bundle_path)
    h._checkpoint_inspect_refs(manifest, capsule, heads)
    repository = existing_repo or h._checkpoint_inspect_clone(scratch, bundle_path, directory=True)
    h._checkpoint_inspect_bundle_completeness(manifest, bundle_path, repository,
                                             prerequisites, algorithm, directory=True)
    signatures = h._checkpoint_inspect_signatures(repository, manifest, captured, scratch)
    h._checkpoint_inspect_identity(manifest["identity"], captured.get(h.CHECKPOINT_ARCHIVE_IDENTITY_ENTRY))
    h._checkpoint_inspect_acceptance(manifest, names)
    if secret_found:
        h._checkpoint_archive_refuse("secret-shaped-member")
    result = {"schema": "fiat-checkpoint-directory-inspect/v1", "outer_sha256": expected_digest,
              "entries": len(names), "bytes": total, "findings": [], "bundle": manifest["bundle"],
              "signatures": signatures, "identity": manifest["identity"], "refs": manifest["refs"]}
    return result, {"manifest": manifest, "local": local, "physical": physical,
                    "directory_repository": repository}
