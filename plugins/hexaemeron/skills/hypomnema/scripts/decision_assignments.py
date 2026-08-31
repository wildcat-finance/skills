#!/usr/bin/env python3
"""Plan, apply, and replay merge-time ADR number assignments.

The planner reads two full immutable commits.  It never derives a number from
the worktree, a moving short name, or a hole below the greatest number on the
exact base.  Git replacement objects and inherited repository-repointing
variables are disabled for every native object read.

The report is canonical ASCII JSON under ``.hexaemeron/``.  Applying it is a
separate, fail-closed worktree operation: every source and destination is
validated before the first rename, and a failed rename restores every source.
Refusals emit one bounded code and no untrusted value.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any


REPORT_SCHEMA = "fiat-decision-assignments/v1"
COMMAND_SCHEMA = "fiat-decision-assignment-command/v1"
ERROR_SCHEMA = "fiat-decision-assignment-refusal/v1"
MAX_DRAFTS = 32
MAX_SLUG_BYTES = 96
MAX_BLOB_BYTES = 1 << 20
MAX_PATH_BYTES = 1024
MAX_TREE_ENTRIES = 20_000
MAX_GIT_OUTPUT_BYTES = 16 << 20
MAX_REPORT_BYTES = 256 << 10
MAX_REPORT_DEPTH = 16
MAX_GIT_INPUT_BYTES = 2 << 20
MAX_GIT_SECONDS = 20
MAX_ADR_NUMBER = 999
MAX_HEADING_BYTES = 4096

DECISIONS = b"docs/decisions/"
DRAFTS = b"docs/decisions/drafts/"
SLUG = re.compile(br"\A[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FINAL = re.compile(br"\Adocs/decisions/ADR-([0-9]{3})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md\Z")
LEGACY_FINAL = re.compile(
    br"\Adocs/decisions/ADR-([0-9]{3})-([A-Za-z0-9][A-Za-z0-9._-]*)\.md\Z"
)
REPORT_PATH = re.compile(r"\A\.hexaemeron/[a-z0-9][a-z0-9._-]*\.json\Z")
FULL_REF = re.compile(r"\Arefs/(?:heads|remotes)/[A-Za-z0-9._/-]+\Z")

LIMITS = {
    "max_adr_number": MAX_ADR_NUMBER,
    "max_blob_bytes": MAX_BLOB_BYTES,
    "max_drafts": MAX_DRAFTS,
    "max_git_input_bytes": MAX_GIT_INPUT_BYTES,
    "max_git_output_bytes": MAX_GIT_OUTPUT_BYTES,
    "max_git_seconds": MAX_GIT_SECONDS,
    "max_heading_bytes": MAX_HEADING_BYTES,
    "max_path_bytes": MAX_PATH_BYTES,
    "max_report_bytes": MAX_REPORT_BYTES,
    "max_report_depth": MAX_REPORT_DEPTH,
    "max_slug_bytes": MAX_SLUG_BYTES,
    "max_tree_entries": MAX_TREE_ENTRIES,
}


class AssignmentError(Exception):
    """One bounded refusal whose code is safe to expose."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Repository:
    root: Path
    object_format: str
    oid_length: int
    common_objects: Path


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    kind: str
    oid: str
    path: bytes


@dataclass(frozen=True)
class DecisionState:
    drafts: dict[bytes, TreeEntry]
    finals: dict[bytes, TreeEntry]
    numbers: dict[int, bytes]
    records: dict[bytes, TreeEntry]


def refuse(code: str) -> None:
    raise AssignmentError(code)


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("ascii")


def emit(value: dict[str, Any], *, error: bool = False) -> None:
    stream = sys.stderr.buffer if error else sys.stdout.buffer
    stream.write(canonical(value))
    stream.flush()


def git_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_ASKPASS": "/usr/bin/false",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NOGLOB_PATHSPECS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_PROTOCOL_FROM_USER": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    if extra:
        env.update(extra)
    return env


def bounded_git(
    repo: Path,
    argv: list[str],
    *,
    input_bytes: bytes | None = None,
    output_cap: int = MAX_GIT_OUTPUT_BYTES,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    """Run native Git with fixed framing, timeout, and output ceilings."""
    if input_bytes is not None and len(input_bytes) > MAX_GIT_INPUT_BYTES:
        refuse("git-input-limit")
    try:
        process = subprocess.Popen(  # phylax: allow subprocess: native Git, fixed argv, no shell
            [
                "git",
                "--no-replace-objects",
                "-c", "core.fsmonitor=false",
                "-c", f"core.hooksPath={os.devnull}",
                "-c", "diff.external=",
                "-C", str(repo),
                *argv,
            ],
            stdin=subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            env=git_environment(extra_env),
        )
    except OSError:
        refuse("git-start")
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    output = bytearray()
    deadline = time.monotonic() + MAX_GIT_SECONDS
    input_view = memoryview(input_bytes or b"")
    input_offset = 0
    input_failed = False
    try:
        os.set_blocking(process.stdout.fileno(), False)
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        if input_bytes is not None:
            assert process.stdin is not None
            os.set_blocking(process.stdin.fileno(), False)
            if input_view:
                selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
            else:
                process.stdin.close()
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.wait()
                refuse("git-timeout")
            events = selector.select(min(remaining, 0.1))
            if not events and process.poll() is not None:
                for key in list(selector.get_map().values()):
                    if key.data == "stdin":
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        input_failed = input_offset != len(input_view)
            for key, _ in events:
                if key.data == "stdin":
                    try:
                        written = os.write(
                            key.fd,
                            input_view[input_offset:input_offset + 65536],
                        )
                    except BlockingIOError:
                        continue
                    except (BrokenPipeError, OSError):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        input_failed = True
                        continue
                    if written <= 0:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        input_failed = True
                        continue
                    input_offset += written
                    if input_offset == len(input_view):
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                try:
                    chunk = os.read(key.fd, 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                else:
                    output.extend(chunk)
                    if len(output) > output_cap:
                        process.kill()
                        process.wait()
                        refuse("git-output-limit")
        try:
            status = process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            refuse("git-timeout")
        if input_bytes is not None and (
                input_failed or input_offset != len(input_view)):
            refuse("git-input")
    except OSError:
        if process.poll() is None:
            process.kill()
            process.wait()
        refuse("git-io")
    finally:
        selector.close()
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        process.stdout.close()
    return status, bytes(output)


def git(
    repo: Path,
    argv: list[str],
    *,
    code: str = "git-read",
    input_bytes: bytes | None = None,
    output_cap: int = MAX_GIT_OUTPUT_BYTES,
    extra_env: dict[str, str] | None = None,
) -> bytes:
    status, output = bounded_git(
        repo,
        argv,
        input_bytes=input_bytes,
        output_cap=output_cap,
        extra_env=extra_env,
    )
    if status != 0:
        refuse(code)
    return output


def decode_ascii(raw: bytes, code: str) -> str:
    try:
        return raw.decode("ascii").strip()
    except UnicodeDecodeError:
        refuse(code)
    raise AssertionError("unreachable")


def repository(raw: str) -> Repository:
    if not raw or "\x00" in raw or len(os.fsencode(raw)) > MAX_PATH_BYTES:
        refuse("repository-path")
    candidate = Path(raw)
    try:
        if candidate.is_symlink():
            refuse("repository-path")
        root = candidate.resolve(strict=True)
    except OSError:
        refuse("repository-path")
    if not root.is_dir():
        refuse("repository-path")
    top = git(root, ["rev-parse", "--show-toplevel"], code="repository", output_cap=MAX_PATH_BYTES)
    try:
        top_path = Path(os.fsdecode(top.rstrip(b"\n"))).resolve(strict=True)
    except (OSError, UnicodeError):
        refuse("repository")
    if top_path != root:
        refuse("repository")
    shallow = decode_ascii(
        git(root, ["rev-parse", "--is-shallow-repository"], code="repository", output_cap=32),
        "repository",
    )
    if shallow == "true":
        refuse("repository-shallow")
    if shallow != "false":
        refuse("repository")
    object_format = decode_ascii(
        git(root, ["rev-parse", "--show-object-format"], code="repository", output_cap=32),
        "repository",
    )
    if object_format not in {"sha1", "sha256"}:
        refuse("object-format")
    oid_length = 40 if object_format == "sha1" else 64
    common_raw = git(
        root,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        code="repository",
        output_cap=MAX_PATH_BYTES,
    ).rstrip(b"\n")
    try:
        common = Path(os.fsdecode(common_raw)).resolve(strict=True)
    except (OSError, UnicodeError):
        refuse("repository")
    objects = common / "objects"
    if not objects.is_dir() or objects.is_symlink() or os.pathsep in str(objects):
        refuse("repository")
    return Repository(root, object_format, oid_length, objects)


def valid_oid(repo: Repository, value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        rf"[0-9a-f]{{{repo.oid_length}}}", value
    ):
        refuse("object-id")
    return value


def object_commit(repo: Repository, oid: str) -> None:
    status, output = bounded_git(repo.root, ["cat-file", "-t", oid], output_cap=64)
    if status != 0 or output != b"commit\n":
        refuse("object-type")


def valid_ref(value: Any) -> str:
    if not isinstance(value, str) or len(value.encode("ascii", "ignore")) > MAX_PATH_BYTES:
        refuse("base-ref")
    if not FULL_REF.fullmatch(value):
        refuse("base-ref")
    if ".." in value or "@{" in value or "//" in value or "\\" in value:
        refuse("base-ref")
    for part in value.split("/"):
        if not part or part.startswith(".") or part.endswith((".", ".lock")):
            refuse("base-ref")
    return value


def verify_base_ref(repo: Repository, ref: str, base: str) -> None:
    status, output = bounded_git(
        repo.root,
        ["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        output_cap=128,
    )
    if status != 0 or decode_ascii(output, "base-moved") != base:
        refuse("base-moved")


def tree_entries(repo: Repository, commit: str) -> dict[bytes, TreeEntry]:
    raw = git(
        repo.root,
        ["ls-tree", "-r", "-z", "--full-tree", commit],
        code="object-incomplete",
    )
    if raw and not raw.endswith(b"\0"):
        refuse("tree-framing")
    records = [record for record in raw.split(b"\0") if record]
    if len(records) > MAX_TREE_ENTRIES:
        refuse("tree-entry-limit")
    entries: dict[bytes, TreeEntry] = {}
    for record in records:
        try:
            metadata, path = record.split(b"\t", 1)
            mode_raw, kind_raw, oid_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            kind = kind_raw.decode("ascii")
            oid = oid_raw.decode("ascii")
        except (ValueError, UnicodeDecodeError):
            refuse("tree-framing")
        if not path or len(path) > MAX_PATH_BYTES or b"\0" in path:
            refuse("tree-path")
        valid_oid(repo, oid)
        if path in entries:
            refuse("tree-order")
        entries[path] = TreeEntry(mode, kind, oid, path)
    return entries


def verify_tree_objects(repo: Repository, entries: dict[bytes, TreeEntry]) -> None:
    """Prove every blob named by the commit tree is present and typed."""
    object_ids = sorted({entry.oid for entry in entries.values()
                         if entry.kind == "blob"})
    request = b"".join(oid.encode("ascii") + b"\n" for oid in object_ids)
    status, output = bounded_git(
        repo.root,
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        input_bytes=request,
    )
    if status != 0:
        refuse("object-incomplete")
    lines = output.splitlines()
    if len(lines) != len(object_ids):
        refuse("object-incomplete")
    for oid, line in zip(object_ids, lines, strict=True):
        if line != f"{oid} blob".encode("ascii"):
            refuse("object-incomplete")


def valid_slug(raw: bytes) -> bytes:
    if not raw or len(raw) > MAX_SLUG_BYTES or not SLUG.fullmatch(raw):
        refuse("slug-invalid")
    return raw


def regular_blob(entry: TreeEntry) -> None:
    if entry.kind != "blob" or entry.mode not in {"100644", "100755"}:
        refuse("entry-type")


def decision_state(entries: dict[bytes, TreeEntry]) -> DecisionState:
    drafts: dict[bytes, TreeEntry] = {}
    finals: dict[bytes, TreeEntry] = {}
    numbers: dict[int, bytes] = {}
    records: dict[bytes, TreeEntry] = {}
    for path, entry in entries.items():
        if path.startswith(DRAFTS):
            relative = path[len(DRAFTS):]
            if b"/" in relative or not relative.endswith(b".md"):
                refuse("slug-invalid")
            slug = valid_slug(relative[:-3])
            if relative.startswith(b"ADR-"):
                refuse("identity-mismatch")
            regular_blob(entry)
            if slug in drafts:
                refuse("identity-duplicate")
            drafts[slug] = entry
            continue
        if not path.startswith(DECISIONS):
            continue
        relative = path[len(DECISIONS):]
        if b"/" in relative:
            continue
        if relative.endswith(b".md") and not relative.startswith(b"ADR-"):
            refuse("draft-placement")
        if not relative.startswith(b"ADR-"):
            continue
        legacy_match = LEGACY_FINAL.fullmatch(path)
        if legacy_match is None:
            refuse("record-path")
        regular_blob(entry)
        number = int(legacy_match.group(1))
        if number < 1 or number > MAX_ADR_NUMBER:
            refuse("namespace-exhausted")
        if number in numbers:
            refuse("number-duplicate")
        numbers[number] = legacy_match.group(2)
        records[path] = entry
        match = FINAL.fullmatch(path)
        if match is not None:
            slug = valid_slug(match.group(2))
            if slug in finals:
                refuse("identity-duplicate")
            finals[slug] = entry
    return DecisionState(drafts, finals, numbers, records)


def read_blob(repo: Repository, entry: TreeEntry) -> bytes:
    regular_blob(entry)
    size_raw = git(
        repo.root,
        ["cat-file", "-s", entry.oid],
        code="object-incomplete",
        output_cap=64,
    )
    try:
        size = int(size_raw.strip())
    except ValueError:
        refuse("object-incomplete")
    if size < 0 or size > MAX_BLOB_BYTES:
        refuse("blob-limit")
    raw = git(
        repo.root,
        ["cat-file", "blob", entry.oid],
        code="object-incomplete",
        output_cap=MAX_BLOB_BYTES,
    )
    if len(raw) != size:
        refuse("object-incomplete")
    return raw


def transformed(blob: bytes, number_text: str) -> bytes:
    newline = blob.find(b"\n")
    if newline < 0 or newline > MAX_HEADING_BYTES:
        refuse("heading-invalid")
    first = blob[:newline]
    prefix = b"# Decision: "
    if not first.startswith(prefix) or len(first) == len(prefix):
        refuse("heading-invalid")
    title = first[len(prefix):]
    if b"\r" in title or any(byte < 0x20 or byte == 0x7F for byte in title):
        refuse("heading-invalid")
    try:
        title.decode("utf-8")
    except UnicodeDecodeError:
        refuse("heading-invalid")
    output = f"# ADR-{number_text}: ".encode("ascii") + title + blob[newline:]
    if output.split(b"\n", 1)[1] != blob.split(b"\n", 1)[1]:
        refuse("byte-drift")
    return output


def temporary_object_environment(repo: Repository, directory: Path) -> dict[str, str]:
    objects = directory / "objects"
    (objects / "info").mkdir(parents=True)
    (objects / "pack").mkdir()
    return {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(repo.common_objects),
        "GIT_INDEX_FILE": str(directory / "index"),
        "GIT_OBJECT_DIRECTORY": str(objects),
    }


def build_report(
    repo: Repository, base: str, product: str, base_ref: str
) -> dict[str, Any]:
    base = valid_oid(repo, base)
    product = valid_oid(repo, product)
    base_ref = valid_ref(base_ref)
    object_commit(repo, base)
    object_commit(repo, product)
    verify_base_ref(repo, base_ref, base)
    relation, _ = bounded_git(repo.root, ["merge-base", "--is-ancestor", base, product])
    if relation == 1:
        refuse("object-ancestry")
    if relation != 0:
        refuse("object-incomplete")

    base_entries = tree_entries(repo, base)
    product_entries = tree_entries(repo, product)
    verify_tree_objects(repo, base_entries)
    verify_tree_objects(repo, product_entries)
    base_state = decision_state(base_entries)
    product_state = decision_state(product_entries)
    if base_state.drafts:
        refuse("base-draft")
    for path, entry in base_state.records.items():
        if product_state.records.get(path) != entry:
            refuse("inherited-record-drift")
    if set(product_state.drafts) & set(product_state.finals):
        refuse("identity-duplicate")
    if set(product_state.records) != set(base_state.records):
        refuse("numbered-addition")
    if not product_state.drafts:
        refuse("draft-missing")
    if len(product_state.drafts) > MAX_DRAFTS:
        refuse("draft-limit")

    maximum = max(base_state.numbers, default=0)
    if maximum + len(product_state.drafts) > MAX_ADR_NUMBER:
        refuse("namespace-exhausted")
    rows: list[dict[str, Any]] = []
    outputs: list[bytes] = []
    for offset, slug_raw in enumerate(sorted(product_state.drafts), start=1):
        entry = product_state.drafts[slug_raw]
        source = read_blob(repo, entry)
        number = maximum + offset
        number_text = f"{number:03d}"
        output = transformed(source, number_text)
        slug = slug_raw.decode("ascii")
        rows.append({
            "draft_path": f"docs/decisions/drafts/{slug}.md",
            "final_path": f"docs/decisions/ADR-{number_text}-{slug}.md",
            "identity": f"adr/{slug}",
            "input_blob": entry.oid,
            "mode": entry.mode,
            "number": number,
            "number_text": number_text,
            "output_blob": "",
            "slug": slug,
        })
        outputs.append(output)

    with tempfile.TemporaryDirectory(prefix="hypomnema-assignment-") as temporary:
        temp_path = Path(temporary)
        object_env = temporary_object_environment(repo, temp_path)
        for row, output in zip(rows, outputs, strict=True):
            oid = decode_ascii(
                git(
                    repo.root,
                    ["hash-object", "-w", "--stdin"],
                    code="object-write",
                    input_bytes=output,
                    output_cap=128,
                    extra_env=object_env,
                ),
                "object-write",
            )
            row["output_blob"] = valid_oid(repo, oid)
        git(repo.root, ["read-tree", product], code="tree-build", extra_env=object_env)
        for row in rows:
            git(
                repo.root,
                ["update-index", "--force-remove", "--", row["draft_path"]],
                code="tree-build",
                extra_env=object_env,
            )
            cache = f"{row['mode']},{row['output_blob']},{row['final_path']}"
            git(
                repo.root,
                ["update-index", "--add", "--cacheinfo", cache],
                code="tree-build",
                extra_env=object_env,
            )
        result_tree = valid_oid(
            repo,
            decode_ascii(
                git(
                    repo.root,
                    ["write-tree"],
                    code="tree-build",
                    output_cap=128,
                    extra_env=object_env,
                ),
                "tree-build",
            ),
        )
    verify_base_ref(repo, base_ref, base)
    return {
        "base": base,
        "base_ref": base_ref,
        "limits": LIMITS,
        "mappings": rows,
        "object_format": repo.object_format,
        "product": product,
        "result_tree": result_tree,
        "schema": REPORT_SCHEMA,
    }


def report_path(repo: Repository, raw: str, *, create_parent: bool) -> Path:
    if not isinstance(raw, str) or not REPORT_PATH.fullmatch(raw):
        refuse("report-path")
    if len(raw.encode("ascii")) > MAX_PATH_BYTES:
        refuse("report-path")
    state = repo.root / ".hexaemeron"
    try:
        if state.exists() and (state.is_symlink() or not state.is_dir()):
            refuse("report-path")
        if create_parent:
            state.mkdir(mode=0o700, exist_ok=True)
        elif not state.is_dir():
            refuse("report-read")
        target = repo.root / raw
        if target.is_symlink() or (target.exists() and not target.is_file()):
            refuse("report-path")
    except OSError:
        refuse("report-path")
    return target


def atomic_report(path: Path, raw: bytes) -> None:
    descriptor = -1
    temporary = ""
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=".assignment-", dir=path.parent)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
        refuse("report-write")


def json_depth(raw: bytes) -> None:
    depth = 0
    quoted = False
    escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                quoted = False
            continue
        if byte == 0x22:
            quoted = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_REPORT_DEPTH:
                refuse("report-depth")
        elif byte in (0x5D, 0x7D):
            depth -= 1
            if depth < 0:
                refuse("report-json")
    if quoted or depth != 0:
        refuse("report-json")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            refuse("report-duplicate-key")
        result[key] = value
    return result


def validate_report_shape(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict) or set(report) != {
        "base", "base_ref", "limits", "mappings", "object_format",
        "product", "result_tree", "schema",
    }:
        refuse("report-shape")
    if report["schema"] != REPORT_SCHEMA or report["limits"] != LIMITS:
        refuse("report-shape")
    if report["object_format"] not in {"sha1", "sha256"}:
        refuse("report-shape")
    if not isinstance(report["mappings"], list) or not 1 <= len(report["mappings"]) <= MAX_DRAFTS:
        refuse("report-shape")
    keys = {
        "draft_path", "final_path", "identity", "input_blob", "mode",
        "number", "number_text", "output_blob", "slug",
    }
    for row in report["mappings"]:
        if not isinstance(row, dict) or set(row) != keys:
            refuse("report-shape")
        if type(row["number"]) is not int:
            refuse("report-shape")
        for key in keys - {"number"}:
            if not isinstance(row[key], str):
                refuse("report-shape")
    return report


def load_report(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        if path.is_symlink() or not path.is_file():
            refuse("report-read")
        with path.open("rb") as stream:
            raw = stream.read(MAX_REPORT_BYTES + 1)
    except OSError:
        refuse("report-read")
    if len(raw) > MAX_REPORT_BYTES:
        refuse("report-limit")
    json_depth(raw)
    try:
        report = json.loads(raw.decode("ascii"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, ValueError):
        refuse("report-json")
    report = validate_report_shape(report)
    if canonical(report) != raw:
        refuse("report-canonical")
    return report, raw


def checked_replay(repo: Repository, path: Path) -> dict[str, Any]:
    report, raw = load_report(path)
    if report["object_format"] != repo.object_format:
        refuse("report-mismatch")
    expected = build_report(
        repo,
        report["base"],
        report["product"],
        report["base_ref"],
    )
    if canonical(expected) != raw:
        refuse("report-mismatch")
    return expected


def safe_worktree_path(repo: Repository, relative: str, *, source: bool) -> Path:
    try:
        encoded = relative.encode("ascii")
    except UnicodeEncodeError:
        refuse("worktree-path")
    if len(encoded) > MAX_PATH_BYTES or relative.startswith("/") or ".." in Path(relative).parts:
        refuse("worktree-path")
    target = repo.root / relative
    current = repo.root
    try:
        for part in Path(relative).parts[:-1]:
            current = current / part
            mode = current.lstat().st_mode
            if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
                refuse("worktree-path")
        if source:
            mode = target.lstat().st_mode
            if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                refuse("worktree-path")
        elif target.exists() or target.is_symlink():
            refuse("worktree-destination")
    except FileNotFoundError:
        refuse("worktree-path")
    except OSError:
        refuse("worktree-path")
    return target


def apply_report(repo: Repository, report: dict[str, Any]) -> None:
    head = decode_ascii(
        git(repo.root, ["rev-parse", "--verify", "HEAD"], code="worktree-head", output_cap=128),
        "worktree-head",
    )
    if head != report["product"]:
        refuse("worktree-head")
    filter_status, filter_config = bounded_git(
        repo.root,
        [
            "config", "--local", "--includes", "--name-only",
            "--get-regexp", r"^filter\..*\.(clean|process)$",
        ],
        output_cap=MAX_PATH_BYTES,
    )
    if filter_status not in {0, 1}:
        refuse("repository-config")
    if filter_status == 0 or filter_config:
        refuse("repository-filter")
    status_raw = git(
        repo.root,
        [
            "status", "--porcelain=v1", "-z", "--untracked-files=all",
            "--ignore-submodules=all",
        ],
        code="worktree-status",
    )
    if status_raw:
        refuse("worktree-dirty")

    sources: list[Path] = []
    targets: list[Path] = []
    outputs: list[bytes] = []
    for row in report["mappings"]:
        source = safe_worktree_path(repo, row["draft_path"], source=True)
        target = safe_worktree_path(repo, row["final_path"], source=False)
        try:
            raw = source.read_bytes()
            executable = bool(source.stat().st_mode & 0o111)
        except OSError:
            refuse("worktree-read")
        expected_executable = row["mode"] == "100755"
        if executable != expected_executable:
            refuse("worktree-mismatch")
        entry = TreeEntry(row["mode"], "blob", row["input_blob"], row["draft_path"].encode("ascii"))
        immutable = read_blob(repo, entry)
        if raw != immutable:
            refuse("worktree-mismatch")
        output = transformed(raw, row["number_text"])
        computed = decode_ascii(
            git(
                repo.root,
                ["hash-object", "--stdin"],
                code="object-read",
                input_bytes=output,
                output_cap=128,
            ),
            "object-read",
        )
        if computed != row["output_blob"]:
            refuse("report-mismatch")
        sources.append(source)
        targets.append(target)
        outputs.append(output)

    verify_base_ref(repo, report["base_ref"], report["base"])
    prepared: list[Path] = []
    backups: list[Path] = []
    moved = 0
    installed = 0
    try:
        for target, output, row in zip(targets, outputs, report["mappings"], strict=True):
            descriptor, temporary = tempfile.mkstemp(prefix=".hypomnema-output-", dir=target.parent)
            temp_path = Path(temporary)
            prepared.append(temp_path)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(output)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temp_path, 0o755 if row["mode"] == "100755" else 0o644)
        for source in sources:
            descriptor, temporary = tempfile.mkstemp(prefix=".hypomnema-backup-", dir=source.parent)
            os.close(descriptor)
            backup = Path(temporary)
            backups.append(backup)
            os.replace(source, backup)
            moved += 1
        for temporary, target in zip(prepared, targets, strict=True):
            os.replace(temporary, target)
            installed += 1
        for backup in backups:
            backup.unlink()
    except OSError:
        for target in targets[:installed]:
            try:
                target.unlink()
            except OSError:
                pass
        for index in range(moved - 1, -1, -1):
            try:
                os.replace(backups[index], sources[index])
            except OSError:
                pass
        for temporary in prepared[installed:]:
            try:
                temporary.unlink()
            except OSError:
                pass
        for backup in backups[moved:]:
            try:
                backup.unlink()
            except OSError:
                pass
        refuse("apply-io")


def success(outcome: str, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "base": report["base"],
        "mapping_count": len(report["mappings"]),
        "outcome": outcome,
        "product": report["product"],
        "result_tree": report["result_tree"],
        "schema": COMMAND_SCHEMA,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assign ADR numbers from immutable Git objects.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--repo", required=True)
    plan.add_argument("--base", required=True)
    plan.add_argument("--base-ref", required=True)
    plan.add_argument("--product", required=True)
    plan.add_argument("--report", required=True)
    for name in ("apply", "replay"):
        command = subparsers.add_parser(name)
        command.add_argument("--repo", required=True)
        command.add_argument("--report", required=True)
    args = parser.parse_args(argv)

    try:
        repo = repository(args.repo)
        if args.command == "plan":
            report = build_report(repo, args.base, args.product, args.base_ref)
            path = report_path(repo, args.report, create_parent=True)
            atomic_report(path, canonical(report))
            emit(success("planned", report))
        elif args.command == "replay":
            path = report_path(repo, args.report, create_parent=False)
            report = checked_replay(repo, path)
            emit(success("replayed", report))
        else:
            path = report_path(repo, args.report, create_parent=False)
            report = checked_replay(repo, path)
            apply_report(repo, report)
            emit(success("applied", report))
        return 0
    except AssignmentError as error:
        emit({"code": error.code, "outcome": "refused", "schema": ERROR_SCHEMA}, error=True)
        return 2
    except KeyboardInterrupt:
        emit({"code": "interrupted", "outcome": "refused", "schema": ERROR_SCHEMA}, error=True)
        return 2
    except Exception:
        emit({"code": "internal", "outcome": "failed", "schema": ERROR_SCHEMA}, error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
