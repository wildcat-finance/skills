"""Create and reproduce self-contained Wildcat canonical releases offline."""

from collections import Counter
import ctypes
import errno
import os
from pathlib import Path
import shutil
import stat
import sys
import uuid

from .builder import BuildReport
from .compound_witness import _bounded_file_bytes
from .core import TabulariumError, canonical_json, jsonl_bytes, loads_json, sha256_bytes
from .release_v2 import adapter_module, make_manifest, validate_event_row, validate_manifest
from .wildcat_source import MAX_COMPONENT_BYTES, _physical_inventory, load_raw
from .wildcat_view import _path


SOURCE_FORMAT = "tabularium-wildcat-source/v1"
MAX_OUTPUT_BYTES = 256 * 1024 * 1024
RELEASE_FILES = ("source.json", "capture.json", "events.jsonl", "coverage.json")


def _outputs(admitted, release):
    from .adapters.euler_common import MappingResult
    from .wildcat_rows import map_records

    if not isinstance(release, str) or not release or len(release) > 256 or any(ord(c) < 32 for c in release):
        raise TabulariumError("Wildcat release identifier is invalid")
    venue = admitted["venue"]
    mapped = map_records(venue, admitted["contexts"], admitted["records"])
    source = {
        "schema": SOURCE_FORMAT,
        "adapter": venue,
        "raw_release": {"path": "source/raw-release", "release_id": admitted["release_id"],
                        "inventory": admitted["inventory"]},
        "scope": admitted["scope"],
        "contexts": admitted["contexts"],
        "mapping_records": list(mapped["mapping_records"]),
        "dispositions": list(mapped["dispositions"]),
    }
    source_bytes = canonical_json(source) + b"\n"
    module = adapter_module(venue)
    capture = {
        "schema_version": 2, "release": release,
        "adapter": {"name": venue, "version": module.ADAPTER_VERSION},
        "protocol_generation": venue, "source_api": module.SOURCE_API,
        "captured_at": admitted["manifest"]["release"]["created_at"],
        "endpoint": "preserved-local-Alexandria-release",
        "request": {"operation": "offline-native-journal-mapping", "raw_release_id": admitted["release_id"]},
        "scope": admitted["scope"],
        "source": {"sha256": sha256_bytes(source_bytes), "bytes": len(source_bytes)},
    }
    capture_bytes = canonical_json(capture) + b"\n"
    events = tuple(mapped["events"])
    selectors = []
    for index, row in enumerate(events, 1):
        validate_event_row(row, module, 3, index)
        selectors.append(row["provenance"]["source_selector"])
    if len(set(selectors)) != len(selectors):
        raise TabulariumError("Wildcat canonical source selectors are duplicated")
    canonical_bytes = jsonl_bytes(events)
    result = MappingResult(events, mapped["included_counts"], mapped["unsupported_counts"])
    coverage = make_manifest(release, venue, "source.json", source_bytes,
                             "capture.json", capture_bytes, "events.jsonl", canonical_bytes,
                             capture, result, 3)
    validate_manifest(coverage, 3)
    coverage_bytes = canonical_json(coverage) + b"\n"
    outputs = dict(zip(RELEASE_FILES, (source_bytes, capture_bytes, canonical_bytes, coverage_bytes)))
    if any(len(data) > MAX_OUTPUT_BYTES for data in outputs.values()):
        raise TabulariumError("Wildcat release artefact exceeds the output byte budget")
    return outputs, mapped, coverage


def _write_new(path, data):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_publish(parent_fd, stage_name, target_name):
    # The same native no-replace operation used by Fiat's checkpoint carrier;
    # directory descriptors confine both names to the checked output parent.
    libc = ctypes.CDLL(None, use_errno=True)
    if hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(parent_fd, os.fsencode(stage_name), parent_fd, os.fsencode(target_name), 1)
    elif hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(parent_fd, os.fsencode(stage_name), parent_fd, os.fsencode(target_name), 4)
    else:
        raise TabulariumError("atomic no-replace directory publication is unavailable")
    if result:
        code = ctypes.get_errno()
        if code in (errno.EEXIST, errno.ENOTEMPTY):
            raise TabulariumError("Wildcat output became occupied")
        raise TabulariumError("Wildcat complete release could not be published atomically")
    os.fsync(parent_fd)


def _same_directory(path, identity):
    try:
        current = path.stat(follow_symlinks=False)
    except OSError:
        return False
    return (stat.S_ISDIR(current.st_mode) and
            (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino))


def _stage_path(parent, stage_name, identity):
    # macOS exposes the live directory by inode. This address survives a
    # rename of the output parent and cannot follow a replacement pathname.
    if sys.platform == "darwin":
        path = Path("/.vol") / str(identity.st_dev) / str(identity.st_ino)
        if not _same_directory(path, identity):
            raise TabulariumError("Wildcat staging inode cannot be resolved")
        return path
    return parent / stage_name


def build_wildcat_canonical(release_root, output, release):
    """Install one complete new release, keeping all original raw bytes."""
    root, target = _path(release_root), _path(output)
    if target.is_relative_to(root) or root.is_relative_to(target):
        raise TabulariumError("Wildcat output aliases or overlaps preserved raw input")
    if target.exists():
        raise TabulariumError("Wildcat output directory must be fresh")
    parent = target.parent
    if not parent.is_dir():
        raise TabulariumError("Wildcat output parent must already exist")
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    parent_identity = os.fstat(parent_fd)
    stage_name = ".wildcat-stage-" + uuid.uuid4().hex
    stage = parent / stage_name
    stage_identity = None
    published = False
    try:
        os.mkdir(stage_name, mode=0o700, dir_fd=parent_fd)
        stage_identity = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
        stage = _stage_path(parent, stage_name, stage_identity)
        admitted = load_raw(root)
        raw_copy = stage / "source" / "raw-release"
        raw_copy.mkdir(parents=True, mode=0o700)
        for relative, claim in admitted["inventory"].items():
            if not _same_directory(stage, stage_identity):
                raise TabulariumError("Wildcat staging directory changed during copy")
            source = root / relative
            data = _bounded_file_bytes(source, MAX_COMPONENT_BYTES, "raw source copy")
            if len(data) != claim["bytes"] or sha256_bytes(data) != claim["sha256"]:
                raise TabulariumError("raw source bytes changed before copy")
            destination = raw_copy / relative
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            _write_new(destination, data)
        copied = load_raw(raw_copy)
        if copied["inventory"] != admitted["inventory"] or copied["release_id"] != admitted["release_id"]:
            raise TabulariumError("raw release copy differs from admitted source")
        outputs, mapped, coverage = _outputs(copied, release)
        for name, data in outputs.items():
            if not _same_directory(stage, stage_identity):
                raise TabulariumError("Wildcat staging directory changed during build")
            _write_new(stage / name, data)
        verify_wildcat_canonical(stage / "coverage.json")
        if _physical_inventory(root) != admitted["inventory"]:
            raise TabulariumError("raw source changed while release was built")
        for directory, _, _ in os.walk(stage, topdown=False):
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        if not _same_directory(parent, parent_identity):
            raise TabulariumError("Wildcat output parent changed before publication")
        named_stage = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
        if (named_stage.st_dev, named_stage.st_ino) != (stage_identity.st_dev, stage_identity.st_ino):
            raise TabulariumError("Wildcat staging name changed before publication")
        _atomic_publish(parent_fd, stage_name, target.name)
        published = True
        return BuildReport(len(mapped["events"]), dict(Counter(row["event_family"] for row in mapped["events"])),
                           mapped["unsupported_counts"], coverage["canonical"]["sha256"], sha256_bytes(outputs["coverage.json"]))
    finally:
        try:
            if not published and stage_identity is not None:
                try:
                    named_stage = os.stat(stage_name, dir_fd=parent_fd, follow_symlinks=False)
                except FileNotFoundError:
                    named_stage = None
                if named_stage is not None and (named_stage.st_dev, named_stage.st_ino) == (stage_identity.st_dev, stage_identity.st_ino):
                    # rmtree uses the held parent descriptor and refuses links;
                    # the identity check leaves a replacement name untouched.
                    shutil.rmtree(stage_name, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)


def _closed_release_tree(root, inventory):
    allowed = {*RELEASE_FILES, *("source/raw-release/" + name for name in inventory)}
    allowed_directories = {"."}
    for name in allowed:
        allowed_directories.update(parent.as_posix() for parent in Path(name).parents)
    seen, identities = set(), set()
    for directory, subdirs, files in os.walk(root, followlinks=False):
        if Path(directory).relative_to(root).as_posix() not in allowed_directories:
            raise TabulariumError("Wildcat release has an undeclared directory")
        for name in subdirs:
            if (Path(directory) / name).is_symlink():
                raise TabulariumError("Wildcat release contains a directory link")
        for name in files:
            path = Path(directory) / name
            information = path.lstat()
            if not stat.S_ISREG(information.st_mode) or information.st_nlink != 1:
                raise TabulariumError("Wildcat release contains a linked or non-regular file")
            identity = (information.st_dev, information.st_ino)
            if identity in identities:
                raise TabulariumError("Wildcat release files alias each other")
            identities.add(identity)
            seen.add(path.relative_to(root).as_posix())
    if seen != allowed:
        raise TabulariumError("Wildcat release tree has missing or undeclared artefacts")


def verify_wildcat_canonical(manifest_path):
    """Reconstruct every semantic and coverage byte from the copied raw source."""
    from .verifier import VerificationReport

    manifest_path = _path(manifest_path)
    if manifest_path.name != "coverage.json":
        raise TabulariumError("Wildcat coverage path must name coverage.json")
    root = manifest_path.parent
    manifest_bytes = _bounded_file_bytes(manifest_path, MAX_OUTPUT_BYTES, "Wildcat coverage manifest")
    manifest = loads_json(manifest_bytes, "Wildcat coverage manifest")
    validate_manifest(manifest, 3)
    if manifest["versions"]["adapter"]["name"] not in ("wildcat-v1", "wildcat-v2"):
        raise TabulariumError("coverage does not name a Wildcat adapter")
    if (manifest["source"]["path"] != "source.json" or manifest["capture_manifest"]["path"] != "capture.json" or manifest["canonical"]["path"] != "events.jsonl"):
        raise TabulariumError("Wildcat release artefact names are unsupported or aliased")
    admitted = load_raw(root / "source" / "raw-release")
    _closed_release_tree(root, admitted["inventory"])
    expected, mapped, coverage = _outputs(admitted, manifest["release"])
    for name, data in expected.items():
        actual = _bounded_file_bytes(root / name, MAX_OUTPUT_BYTES, "Wildcat " + name)
        if actual != data:
            raise TabulariumError("Wildcat " + name + " differs from its offline semantic rebuild")
    return VerificationReport(manifest["release"], len(mapped["events"]), coverage["canonical"]["sha256"], 3,
                              admitted["venue"])
