"""Bounded byte inventories and streaming edits for the reproduction executor."""

from __future__ import annotations

from collections import Counter
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat


FILE_CAP = 256 * 1024 * 1024
OBJECT_CAP = 2 * 1024 * 1024
MUTATIONS = ("party", "amount-shape", "selector", "mapping-class", "raw-source")


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate preserved JSON key")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("nonfinite preserved JSON")


def loads(data):
    return json.loads(data, object_pairs_hook=_pairs, parse_constant=_constant)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode()


def write_new(path, data):
    """Create one single-link artifact without replacing an earlier attempt."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def digest(path, cap=FILE_CAP):
    """Hash one stable regular file; refuse links, aliases and oversized bytes."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > cap:
        raise ValueError("file kind, link count or size outside reproduction bounds")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("file changed before reproduction read")
        count, state = 0, hashlib.sha256()
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            while block := stream.read(1024 * 1024):
                count += len(block)
                if count > cap:
                    raise ValueError("file exceeds reproduction byte cap")
                state.update(block)
        after = os.fstat(descriptor)
        named = path.lstat()
        fields = lambda item: (item.st_dev, item.st_ino, item.st_size,
                               item.st_mtime_ns, item.st_ctime_ns, item.st_nlink)
        if fields(before) != fields(after) or fields(after) != fields(named):
            raise ValueError("file changed during reproduction read")
        return {"bytes": count, "sha256": state.hexdigest()}
    finally:
        os.close(descriptor)


def inventory(root):
    """Record every regular leaf and reject any undeclared empty directory."""
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("inventory root is absent or linked")
    files, identities, directories = [], set(), set()
    for directory, subdirs, leaves in os.walk(root, followlinks=False):
        relative = Path(directory).relative_to(root)
        directories.add(relative.as_posix())
        for name in subdirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError("inventory directory link")
        for name in sorted(leaves):
            path = Path(directory) / name
            info = path.lstat()
            identity = (info.st_dev, info.st_ino)
            if identity in identities:
                raise ValueError("inventory files alias")
            identities.add(identity)
            files.append({"path": path.relative_to(root).as_posix(), **digest(path)})
    files.sort(key=lambda row: row["path"].encode())
    declared_dirs = {"."}
    for row in files:
        declared_dirs.update(parent.as_posix() for parent in Path(row["path"]).parents)
    if directories != declared_dirs:
        raise ValueError("inventory has an empty undeclared directory")
    return {"schema": "wildcat-v3-file-inventory/v1", "root": str(root),
            "files": files, "bytes": sum(row["bytes"] for row in files)}


def ref(custody, path):
    path = Path(path)
    return {"path": path.relative_to(custody).as_posix(), **digest(path)}


def save_inventory(custody, root, name):
    path = Path(custody) / "inventories" / (name + ".json")
    value = inventory(root)
    write_new(path, canonical(value))
    return ref(custody, path), value


def _array_start(stream, key):
    stream.seek(0)
    needle = ('"' + key + '":[').encode()
    buffer, consumed = b"", 0
    while block := stream.read(65536):
        buffer += block
        offset = buffer.find(needle)
        if offset >= 0:
            return consumed + offset + len(needle)
        retain = len(needle) - 1
        consumed += len(buffer) - retain
        buffer = buffer[-retain:]
    raise ValueError("bounded source array is absent: " + key)


def stream_array(path, key):
    """Yield bounded object values and byte ranges from a canonical JSON array."""
    supplied = hasattr(path, "read") and hasattr(path, "seek")
    size = os.fstat(path.fileno()).st_size if supplied else Path(path).stat().st_size
    if size > FILE_CAP:
        raise ValueError("source descriptor exceeds production cap")
    with nullcontext(path) if supplied else Path(path).open("rb") as stream:
        stream.seek(_array_start(stream, key))
        while True:
            char = stream.read(1)
            while char in (b" ", b"\n", b"\r", b"\t", b","):
                char = stream.read(1)
            if char == b"]":
                return
            if char != b"{":
                raise ValueError("source array contains a non-object")
            start = stream.tell() - 1
            buffer, depth, quoted, escaped = bytearray(char), 1, False, False
            while depth:
                char = stream.read(1)
                if not char:
                    raise ValueError("unterminated source array object")
                buffer.extend(char)
                if len(buffer) > OBJECT_CAP:
                    raise ValueError("source array object exceeds byte cap")
                if quoted:
                    if escaped:
                        escaped = False
                    elif char == b"\\":
                        escaped = True
                    elif char == b'"':
                        quoted = False
                elif char == b'"':
                    quoted = True
                elif char in (b"{", b"["):
                    depth += 1
                elif char in (b"}", b"]"):
                    depth -= 1
            yield loads(buffer), start, stream.tell()


def bounded_object(path, key):
    """Read a small top-level metadata object without loading the descriptor."""
    needle = ('"' + key + '":').encode()
    supplied = hasattr(path, "read") and hasattr(path, "seek")
    with nullcontext(path) if supplied else Path(path).open("rb") as stream:
        stream.seek(0)
        buffer, consumed = b"", 0
        while block := stream.read(65536):
            buffer += block
            offset = buffer.find(needle)
            if offset >= 0:
                stream.seek(consumed + offset + len(needle))
                break
            retain = len(needle) - 1
            consumed += len(buffer) - retain
            buffer = buffer[-retain:]
        else:
            raise ValueError("source metadata object is absent")
        buffer = b""
        while len(buffer) <= OBJECT_CAP:
            block = stream.read(65536)
            if not block:
                raise ValueError("source metadata object is malformed")
            buffer += block
            try:
                value, _ = json.JSONDecoder(object_pairs_hook=_pairs,
                                           parse_constant=_constant).raw_decode(buffer.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(value, dict):
                raise ValueError("source metadata is not an object")
            return value
    raise ValueError("source metadata object exceeds byte cap")


def source_counts(path):
    """Count preserved native dispositions and mapping classes by streaming."""
    classes, contexts, dispositions = Counter(), Counter(), Counter()
    mapping_count = 0
    for row, _, _ in stream_array(path, "mapping_records"):
        classes[row["evidence_class"]] += 1
        mapping_count += 1
    native_count = 0
    for row, _, _ in stream_array(path, "dispositions"):
        dispositions[row["disposition"]] += 1
        native_count += 1
    for row in bounded_object(path, "contexts").values():
        contexts[row["role"]] += 1
    return {"native_logs": native_count, "mapping_records": mapping_count,
            "disposition_counts": dict(sorted(dispositions.items())),
            "evidence_class_counts": dict(sorted(classes.items())),
            "context_counts": dict(sorted(contexts.items()))}


def summary(root, rows, canonical_sha256):
    root = Path(root)
    actions = Counter()
    event_count = 0
    with (root / "events.jsonl").open("rb") as stream:
        for line in stream:
            if len(line) > OBJECT_CAP:
                raise ValueError("canonical row exceeds bounded reader")
            row = loads(line)
            actions[row["action"]] += 1
            event_count += 1
    if event_count != rows or digest(root / "events.jsonl")["sha256"] != canonical_sha256:
        raise ValueError("observed build rows or digest differ from actual output")
    raw = inventory(root / "source" / "raw-release")
    all_files = inventory(root)
    return {"rows": rows, "canonical_sha256": canonical_sha256,
            "raw_bytes": raw["bytes"], "release_bytes": all_files["bytes"],
            "action_counts": dict(sorted(actions.items())),
            **source_counts(root / "source.json")}


def _replace_range(path, start, finish, replacement):
    temporary = path.with_name(path.name + ".mutation")
    with path.open("rb") as source, temporary.open("xb") as target:
        remaining = start
        while remaining:
            block = source.read(min(remaining, 1024 * 1024))
            if not block:
                raise ValueError("source changed during mutation")
            target.write(block)
            remaining -= len(block)
        target.write(replacement)
        source.seek(finish)
        shutil.copyfileobj(source, target, 1024 * 1024)
    os.replace(temporary, path)


def _descriptor(path):
    return digest(path)


def mutate(root, kind):
    """Alter one native claim while rebinding only the derived descriptors."""
    root = Path(root)
    coverage_path = root / "coverage.json"
    coverage = loads(coverage_path.read_bytes())
    if kind in ("party", "amount-shape", "selector"):
        events = root / "events.jsonl"
        start = 0
        with events.open("rb") as stream:
            for line in stream:
                if len(line) > OBJECT_CAP:
                    raise ValueError("mutation row exceeds byte cap")
                row = loads(line)
                if row["action"] in ("wildcat-v1.deposit", "wildcat-v2.deposit"):
                    finish = start + len(line)
                    if kind == "party":
                        party = next(item for item in row["parties"] if item["role"] == "depositor")
                        party["address"] = "0x" + ("e" if party["address"] == "0x" + "f" * 40 else "f") * 40
                    elif kind == "amount-shape":
                        old = row["amounts"]
                        row["amounts"] = [item for item in old if item["kind"] != "scaled-claims"]
                        if len(old) == len(row["amounts"]):
                            raise ValueError("deposit has no scaled-claims amount")
                    else:
                        old = row["provenance"]["source_selector"]
                        row["provenance"]["source_selector"] = "wildcat-journal:" + ("1" if old.endswith("0" * 64) else "0") * 64
                    break
                start += len(line)
            else:
                raise ValueError("deposit mutation specimen is unavailable")
        _replace_range(events, start, finish, canonical(row))
        coverage["canonical"].update(_descriptor(events))
        coverage_path.write_bytes(canonical(coverage))
        return "Wildcat events.jsonl differs from its offline semantic rebuild"
    if kind == "mapping-class":
        source_path = root / "source.json"
        row, start, finish = next(stream_array(source_path, "mapping_records"))
        row["evidence_class"] = "inferred" if row["evidence_class"] != "inferred" else "directly-observed"
        _replace_range(source_path, start, finish, canonical(row).rstrip(b"\n"))
        capture_path = root / "capture.json"
        capture = loads(capture_path.read_bytes())
        capture["source"].update(_descriptor(source_path))
        capture_path.write_bytes(canonical(capture))
        coverage["source"].update(_descriptor(source_path))
        coverage["capture_manifest"].update(_descriptor(capture_path))
        coverage_path.write_bytes(canonical(coverage))
        return "Wildcat source.json differs from its offline semantic rebuild"
    if kind == "raw-source":
        raw = root / "source" / "raw-release"
        manifest = loads((raw / "manifest.json").read_bytes())
        component = manifest["components"][0]
        with (raw / component["object_path"]).open("ab") as stream:
            stream.write(b" ")
        return "Alexandria Wildcat raw verification failed: component " + component["name"] + " byte count does not match"
    raise ValueError("unknown mutation kind")
