#!/usr/bin/env python3
"""Source-bound workbench for framework-74 instruction architecture research.

Step 1 owns the corpus, loader, byte partition, and sealed cohort boundary.
Later steps extend this CLI without changing the authority of the Markdown
sources recorded here.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import subprocess
import sys
from functools import lru_cache
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REF = "a2b634d8e039af988bf30c8316defccf70071d8d"
SCHEMA_PREFIX = "wildcat-instruction-architecture"
SELECTION_SEED = "framework-74-holdout-v1-2026-08-31"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_GIT_OUTPUT = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_TOKENS = 100_000
EXPECTED_COUNTS = {
    "skill_contract": 32,
    "runtime_contract": 18,
    "promise_machine_contract": 18,
    "markdown_reference": 38,
}
EXPECTED_TOTALS = {
    "physical_files": 106,
    "physical_bytes": 1_545_537,
    "unique_files": 89,
    "unique_bytes": 1_074_093,
}
PARTITION_CLASSES = (
    "governed_operative_semantics",
    "exact_literal_or_evidence",
    "human_only_explanation_or_rationale",
    "generated_duplicate",
    "unsupported_or_unknown",
)
EXTERNAL_SKILL_PREFIXES = (
    "plugins/hexaemeron/skills/fizz/",
    "plugins/hexaemeron/skills/solidity-auditor/",
    "plugins/hexaemeron/skills/x-ray/",
)


class Refusal(ValueError):
    """A bounded input or source relation failed closed."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _reject_constant(value: str) -> None:
    raise Refusal(f"non-finite JSON number: {value}")


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Refusal(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _safe_relative(path: str) -> PurePosixPath:
    if not isinstance(path, str) or not path or len(path.encode("utf-8")) > 1024:
        raise Refusal("unsafe repository path")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or "\\" in path:
        raise Refusal("unsafe repository path")
    if any(part in ("", ".", "..") for part in candidate.parts):
        raise Refusal("unsafe repository path")
    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        raise Refusal("unsafe repository path")
    return candidate


def _identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _directory_identity(item: os.stat_result) -> tuple[int, ...]:
    return (item.st_dev, item.st_ino, item.st_mode)


def _repository_relative(path: Path, label: str) -> PurePosixPath:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise Refusal(f"{label} leaves repository") from exc
    return _safe_relative(relative)


def _directory_flags() -> int:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise Refusal("descriptor-relative no-follow operations are unavailable")
    flags = os.O_RDONLY
    return flags | os.O_DIRECTORY | os.O_NOFOLLOW


def _open_parent(
    relative: PurePosixPath, *, create: bool, label: str
) -> tuple[int, str]:
    """Open a repository-relative parent one no-follow component at a time."""
    flags = _directory_flags()
    try:
        descriptor = os.open(ROOT, flags)
    except OSError as exc:
        raise Refusal(f"{label} root is unavailable or unsafe") from exc
    try:
        for part in relative.parent.parts:
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise Refusal(f"{label} parent is unavailable or unsafe")
                try:
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                    child = os.open(part, flags, dir_fd=descriptor)
                except OSError as exc:
                    raise Refusal(f"{label} parent is unavailable or unsafe") from exc
            except OSError as exc:
                raise Refusal(f"{label} parent is unavailable or unsafe") from exc
            metadata = os.fstat(child)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(child)
                raise Refusal(f"{label} parent is unavailable or unsafe")
            os.close(descriptor)
            descriptor = child
        return descriptor, relative.name
    except BaseException:
        os.close(descriptor)
        raise


def _read_descriptor(descriptor: int, limit: int) -> tuple[bytes, os.stat_result]:
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise Refusal("input is not a single-link regular file")
    if before.st_size > limit:
        raise Refusal("input exceeds byte limit")
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = os.read(descriptor, min(65_536, limit + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > limit:
            raise Refusal("input exceeds byte limit")
    after = os.fstat(descriptor)
    if _identity(before) != _identity(after):
        raise Refusal("input changed during read")
    return b"".join(chunks), after


def _read_regular(path: Path, limit: int) -> bytes:
    relative = _repository_relative(path, "path")
    parent, name = _open_parent(relative, create=False, label="input")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(name, flags, dir_fd=parent)
    except OSError as exc:
        os.close(parent)
        raise Refusal("input is unavailable or unsafe") from exc
    try:
        data, after = _read_descriptor(descriptor, limit)
    finally:
        os.close(descriptor)
        os.close(parent)

    current_parent, current_name = _open_parent(relative, create=False, label="input")
    try:
        try:
            current = os.open(current_name, flags, dir_fd=current_parent)
        except OSError as exc:
            raise Refusal("input changed during read") from exc
        try:
            if _identity(os.fstat(current)) != _identity(after):
                raise Refusal("input changed during read")
        finally:
            os.close(current)
    finally:
        os.close(current_parent)
    return data


def _preflight_json(raw: bytes) -> None:
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAX_JSON_DEPTH:
                raise Refusal("record exceeds JSON depth limit")
        elif byte in (0x7D, 0x5D):
            depth -= 1
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAX_JSON_TOKENS:
            raise Refusal("record exceeds JSON token limit")


def _load_record(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular(path, MAX_JSON_BYTES)
    _preflight_json(raw)
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_closed_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Refusal("record is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise Refusal("record root must be an object")
    if _canonical_json(value) != raw:
        raise Refusal("record is not canonical JSON")
    return value, raw


def _require_fields(
    value: dict[str, Any], required: Iterable[str], allowed: Iterable[str], where: str
) -> None:
    required_set = set(required)
    allowed_set = set(allowed)
    keys = set(value)
    if not required_set <= keys or not keys <= allowed_set:
        raise Refusal(f"{where} has a non-closed field set")


def _git(arguments: list[str], limit: int = MAX_GIT_OUTPUT) -> bytes:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_LITERAL_PATHSPECS": "1",
        }
    )
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(ROOT), *arguments],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=20,
            env=environment,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refusal("bounded Git read failed") from exc
    if len(result.stdout) > limit or len(result.stderr) > 65_536:
        raise Refusal("bounded Git output exceeded its limit")
    if result.returncode != 0:
        raise Refusal("bounded Git read refused the source")
    return result.stdout


@lru_cache(maxsize=256)
def _source_blob(path: str) -> bytes:
    _safe_relative(path)
    blob = _git(["cat-file", "blob", f"{SOURCE_REF}:{path}"], MAX_SOURCE_BYTES)
    live = _read_regular(ROOT / path, MAX_SOURCE_BYTES)
    if live != blob:
        raise Refusal(f"source drift: {path}")
    return blob


def _corpus_paths() -> list[str]:
    raw = _git(["ls-tree", "-r", "-z", "--name-only", SOURCE_REF])
    try:
        names = [
            item.decode("utf-8", errors="strict") for item in raw.split(b"\0") if item
        ]
    except UnicodeDecodeError as exc:
        raise Refusal("Git tree contains a non-UTF-8 path") from exc
    selected: list[str] = []
    for name in names:
        _safe_relative(name)
        if name == "AGENTS.md" or (
            name.startswith("plugins/") and name.endswith("/AGENTS.md")
        ):
            selected.append(name)
        elif name == "PROMISE_MACHINE.md" or (
            name.startswith("plugins/") and name.endswith("/PROMISE_MACHINE.md")
        ):
            selected.append(name)
        elif name == ".agents/skills/promise-machine/SKILL.md":
            selected.append(name)
        elif (
            name.startswith("plugins/")
            and name.endswith("/SKILL.md")
            and "/tests/" not in name
        ):
            selected.append(name)
        elif re.fullmatch(r"plugins/[^/]+/skills/.+/references/.+\.md", name):
            selected.append(name)
    result = sorted(set(selected))
    if len(result) != len(selected):
        raise Refusal("corpus selection produced duplicate paths")
    if any(path.startswith("distribution/skills-runtime/") for path in result):
        raise Refusal("moved skills-runtime package entered the corpus")
    return result


def _document_class(path: str) -> str:
    if path == "AGENTS.md" or path.endswith("/AGENTS.md"):
        return "runtime_contract"
    if path == "PROMISE_MACHINE.md" or path.endswith("/PROMISE_MACHINE.md"):
        return "promise_machine_contract"
    if path.endswith("/SKILL.md"):
        return "skill_contract"
    return "markdown_reference"


def _plugin(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    return parts[1] if len(parts) > 1 and parts[0] == "plugins" else None


def _reference_owner(path: str) -> str:
    parts = list(PurePosixPath(path).parts)
    index = parts.index("references")
    return PurePosixPath(*parts[:index], "SKILL.md").as_posix()


@lru_cache(maxsize=64)
def _skill_name(path: str) -> str:
    text = _source_blob(path).decode("utf-8", errors="strict")
    match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text[:4096])
    if match:
        return match.group(1)
    return PurePosixPath(path).parent.name


def _logical_document(path: str, document_class: str) -> str:
    if document_class == "promise_machine_contract":
        return "promise-machine/v1"
    if path == "AGENTS.md":
        return "suite-runtime"
    if document_class == "runtime_contract":
        return f"plugin:{_plugin(path)}"
    if document_class == "markdown_reference":
        return f"skill:{_skill_name(_reference_owner(path))}"
    return f"skill:{_skill_name(path)}"


def _authority_tier(path: str, document_class: str) -> str:
    if path == "AGENTS.md":
        return "suite_runtime"
    if path == "PROMISE_MACHINE.md":
        return "suite_law"
    if document_class == "promise_machine_contract":
        return "generated_copy"
    if path == ".agents/skills/promise-machine/SKILL.md":
        return "router"
    if document_class == "runtime_contract":
        return "plugin_runtime"
    if document_class == "skill_contract":
        return "canonical_skill"
    return "conditional_reference"


def _external_owner(path: str) -> str | None:
    if any(path.startswith(prefix) for prefix in EXTERNAL_SKILL_PREFIXES):
        return "upstream-pashov"
    return None


def _loader_roots(path: str, document_class: str) -> list[str]:
    plugin = _plugin(path)
    if path == "AGENTS.md":
        return ["repository", "agent-skills"]
    if path == "PROMISE_MACHINE.md":
        return ["repository"]
    if path == ".agents/skills/promise-machine/SKILL.md":
        return ["repository", "agent-skills"]
    if document_class == "promise_machine_contract":
        return [f"standalone:{plugin}"]
    return ["repository", "agent-skills", f"standalone:{plugin}"]


def _scenarios(path: str, document_class: str) -> list[str]:
    if path in (
        "AGENTS.md",
        "PROMISE_MACHINE.md",
        ".agents/skills/promise-machine/SKILL.md",
    ):
        return ["all"]
    if document_class in ("runtime_contract", "promise_machine_contract"):
        return [f"plugin:{_plugin(path)}"]
    owner = path if document_class == "skill_contract" else _reference_owner(path)
    return [f"skill:{_skill_name(owner)}"]


def build_manifest() -> dict[str, Any]:
    paths = _corpus_paths()
    provisional: list[dict[str, Any]] = []
    by_digest: dict[str, list[str]] = {}
    for path in paths:
        blob = _source_blob(path)
        digest = _sha256(blob)
        by_digest.setdefault(digest, []).append(path)
        document_class = _document_class(path)
        owner = (
            _reference_owner(path) if document_class == "markdown_reference" else path
        )
        if document_class == "promise_machine_contract":
            owner = "PROMISE_MACHINE.md"
        provisional.append(
            {
                "path": path,
                "logical_document": _logical_document(path, document_class),
                "document_class": document_class,
                "bytes": len(blob),
                "sha256": digest,
                "exact_duplicate_group": None,
                "canonical_content_path": None,
                "canonical_owner": owner,
                "authority_tier": _authority_tier(path, document_class),
                "loader_roots": _loader_roots(path, document_class),
                "scenario_reachability": _scenarios(path, document_class),
                "external_runtime_owner": _external_owner(path),
            }
        )
    canonical_by_digest: dict[str, str] = {}
    for digest, members in by_digest.items():
        canonical_by_digest[digest] = (
            "PROMISE_MACHINE.md" if "PROMISE_MACHINE.md" in members else min(members)
        )
    for record in provisional:
        members = by_digest[record["sha256"]]
        record["canonical_content_path"] = canonical_by_digest[record["sha256"]]
        if len(members) > 1:
            record["exact_duplicate_group"] = f"sha256:{record['sha256']}"
    class_counts = {
        name: sum(1 for item in provisional if item["document_class"] == name)
        for name in sorted(EXPECTED_COUNTS)
    }
    unique_records = [
        item for item in provisional if item["path"] == item["canonical_content_path"]
    ]
    totals = {
        "physical_files": len(provisional),
        "physical_bytes": sum(item["bytes"] for item in provisional),
        "unique_files": len(unique_records),
        "unique_bytes": sum(item["bytes"] for item in unique_records),
    }
    if class_counts != EXPECTED_COUNTS:
        raise Refusal(f"corpus class count drift: {class_counts}")
    if totals != EXPECTED_TOTALS:
        raise Refusal(f"corpus denominator drift: {totals}")
    tree_rows = [
        f"{item['path']}\0{item['bytes']}\0{item['sha256']}\n" for item in provisional
    ]
    return {
        "schema": f"{SCHEMA_PREFIX}-corpus-manifest/v1",
        "source": {
            "ref": SOURCE_REF,
            "tree_sha256": _sha256("".join(tree_rows).encode("utf-8")),
        },
        "counts": class_counts,
        "totals": totals,
        "documents": provisional,
    }


def _artifact_digest(value: dict[str, Any]) -> str:
    return _sha256(_canonical_json(value))


def _evidence(path: str, needle: str) -> dict[str, Any]:
    data = _source_blob(path)
    encoded = needle.encode("utf-8")
    start = data.find(encoded)
    if start < 0:
        raise Refusal(f"loader evidence missing in {path}")
    end = start + len(encoded)
    return {
        "path": path,
        "start": start,
        "end": end,
        "source_sha256": _sha256(data),
        "span_sha256": _sha256(data[start:end]),
    }


def _reference_link(
    owner: str, target: str, reachable: set[str]
) -> tuple[str, str] | None:
    target_path = PurePosixPath(target)
    candidates: list[tuple[int, str, str]] = []
    for source in sorted(reachable):
        source_path = PurePosixPath(source)
        relative = os.path.relpath(
            target_path.as_posix(), source_path.parent.as_posix()
        )
        owner_relative = os.path.relpath(
            target_path.as_posix(), PurePosixPath(owner).parent.as_posix()
        )
        needles = sorted(
            {relative, owner_relative, target_path.name},
            key=lambda value: (-len(value), value),
        )
        text = _source_blob(source).decode("utf-8", errors="strict")
        for needle in needles:
            position = text.find(needle)
            if position >= 0:
                candidates.append((position, source, needle))
    if not candidates:
        return None
    _, source, needle = min(candidates, key=lambda value: (value[1] != owner, value))
    return source, needle


def build_loader_graph(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest_digest = _artifact_digest(manifest)
    documents = manifest["documents"]
    document_paths = {item["path"] for item in documents}
    plugins = sorted(
        {_plugin(path) for path in document_paths if _plugin(path) is not None}
    )
    roots = [
        {
            "id": "repository",
            "node": "AGENTS.md",
            "mode": "unconditional",
            "evidence": _evidence("AGENTS.md", "The safe loading path is short:"),
        },
        {
            "id": "agent-skills",
            "node": ".agents/skills/promise-machine/SKILL.md",
            "mode": "unconditional",
            "evidence": _evidence(
                ".agents/skills/promise-machine/SKILL.md",
                "Choose the runtime before routing.",
            ),
        },
    ]
    for plugin in plugins:
        node = f"plugins/{plugin}/AGENTS.md"
        roots.append(
            {
                "id": f"standalone:{plugin}",
                "node": node,
                "mode": "unconditional",
                "evidence": _evidence(node, "## Promise Machine binding"),
            }
        )
    edges: list[dict[str, Any]] = []

    def add_edge(source: str, target: str, kind: str, reason: str, needle: str) -> None:
        if source not in document_paths or target not in document_paths:
            raise Refusal("loader edge leaves the frozen corpus")
        edges.append(
            {
                "id": f"edge-{len(edges) + 1:03d}",
                "source": source,
                "target": target,
                "kind": kind,
                "reason": reason,
                "evidence": _evidence(source, needle),
            }
        )

    add_edge(
        "AGENTS.md",
        "PROMISE_MACHINE.md",
        "unconditional",
        "the repository runtime requires the suite-wide law before selection",
        "[Promise Machine contract](PROMISE_MACHINE.md)",
    )
    add_edge(
        "AGENTS.md",
        ".agents/skills/promise-machine/SKILL.md",
        "unconditional",
        "the repository runtime routes requests through the sole host-neutral entrypoint",
        "`.agents/skills/promise-machine/SKILL.md`",
    )
    router = ".agents/skills/promise-machine/SKILL.md"
    for plugin in plugins:
        runtime = f"plugins/{plugin}/AGENTS.md"
        add_edge(
            router,
            runtime,
            "conditional",
            "the router loads the runtime contract only when its selection row wins",
            f"../../../plugins/{plugin}/AGENTS.md",
        )
        promise = f"plugins/{plugin}/PROMISE_MACHINE.md"
        add_edge(
            runtime,
            promise,
            "unconditional",
            "a standalone plugin runtime loads its generated suite-law copy",
            "[Promise Machine contract](PROMISE_MACHINE.md)",
        )
        skills = sorted(
            item["path"]
            for item in documents
            if item["document_class"] == "skill_contract"
            and _plugin(item["path"]) == plugin
        )
        for skill in skills:
            relative = (
                PurePosixPath(skill)
                .relative_to(PurePosixPath("plugins") / plugin)
                .as_posix()
            )
            add_edge(
                runtime,
                skill,
                "conditional",
                "the plugin selection table loads exactly the selected canonical skill",
                relative,
            )
    references_by_owner: dict[str, list[str]] = {}
    for item in documents:
        if item["document_class"] == "markdown_reference":
            references_by_owner.setdefault(item["canonical_owner"], []).append(
                item["path"]
            )
    for owner, references in sorted(references_by_owner.items()):
        reachable = {owner}
        pending = set(references)
        while pending:
            progress = False
            for target in sorted(pending):
                link = _reference_link(owner, target, reachable)
                if link is None:
                    continue
                source, needle = link
                add_edge(
                    source,
                    target,
                    "conditional",
                    "the selected skill or an already linked reference directs this load",
                    needle,
                )
                reachable.add(target)
                pending.remove(target)
                progress = True
                break
            if not progress:
                raise Refusal(f"unproved reference loader edge: {sorted(pending)[0]}")
    return {
        "schema": f"{SCHEMA_PREFIX}-loader-graph/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": manifest_digest,
        "roots": roots,
        "edges": edges,
        "constraints": {
            "file_presence_creates_edge": False,
            "fixtures_excluded": True,
            "skills_runtime_excluded": True,
            "conditional_references_require_source_span": True,
        },
    }


def _partition_ranges(path: str, generated: bool) -> list[dict[str, Any]]:
    data = _source_blob(path)
    if generated:
        return [
            {
                "start": 0,
                "end": len(data),
                "classification": "generated_duplicate",
                "span_sha256": _sha256(data),
            }
        ]
    ranges: list[tuple[int, int, str]] = []
    offset = 0
    fence_stack: list[tuple[int, int]] = []
    for line in data.splitlines(keepends=True):
        marker = re.match(rb"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
        classification = "governed_operative_semantics"
        if fence_stack:
            classification = "exact_literal_or_evidence"
            if marker is not None:
                fence = marker.group(1)
                remainder = marker.group(2)
                active = fence_stack[-1]
                if (
                    fence[0] == active[0]
                    and len(fence) >= active[1]
                    and not remainder.strip(b" \t")
                ):
                    fence_stack.pop()
                elif fence[:1] == b"~" or b"`" not in remainder:
                    fence_stack.append((fence[0], len(fence)))
        elif marker is not None:
            fence = marker.group(1)
            remainder = marker.group(2)
            if fence[:1] == b"~" or b"`" not in remainder:
                classification = "exact_literal_or_evidence"
                fence_stack.append((fence[0], len(fence)))
        end = offset + len(line)
        if ranges and ranges[-1][2] == classification:
            ranges[-1] = (ranges[-1][0], end, classification)
        else:
            ranges.append((offset, end, classification))
        offset = end
    if offset < len(data):
        classification = (
            "exact_literal_or_evidence"
            if fence_stack
            else "governed_operative_semantics"
        )
        ranges.append((offset, len(data), classification))
    if fence_stack:
        raise Refusal(f"unterminated Markdown fence: {path}")
    return [
        {
            "start": start,
            "end": end,
            "classification": classification,
            "span_sha256": _sha256(data[start:end]),
        }
        for start, end, classification in ranges
    ]


def build_partition(manifest: dict[str, Any]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    totals = {name: 0 for name in PARTITION_CLASSES}
    for document in manifest["documents"]:
        generated = (
            document["document_class"] == "promise_machine_contract"
            and document["path"] != "PROMISE_MACHINE.md"
        )
        ranges = _partition_ranges(document["path"], generated)
        for item in ranges:
            totals[item["classification"]] += item["end"] - item["start"]
        files.append(
            {
                "path": document["path"],
                "source_sha256": document["sha256"],
                "bytes": document["bytes"],
                "ranges": ranges,
            }
        )
    if sum(totals.values()) != manifest["totals"]["physical_bytes"]:
        raise Refusal("byte partition does not reconcile to physical bytes")
    return {
        "schema": f"{SCHEMA_PREFIX}-byte-partition/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": _artifact_digest(manifest),
        "classifications": list(PARTITION_CLASSES),
        "unsupported_operative_bytes": totals["unsupported_or_unknown"],
        "totals": totals,
        "files": files,
    }


def _logical_skill_groups(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in manifest["documents"]:
        if item["path"] != item["canonical_content_path"]:
            continue
        logical = item["logical_document"]
        if logical.startswith("skill:"):
            groups.setdefault(logical.removeprefix("skill:"), []).append(item)
    return groups


def _choose_holdout(manifest: dict[str, Any]) -> list[str]:
    groups = _logical_skill_groups(manifest)
    excluded = {"fiat", "horos", "promise-machine"}
    eligible = sorted(name for name in groups if name not in excluded)
    sizes = {name: sum(item["bytes"] for item in groups[name]) for name in eligible}
    ordered_sizes = sorted((size, name) for name, size in sizes.items())
    quartile: dict[str, int] = {}
    for index, (_, name) in enumerate(ordered_sizes):
        quartile[name] = min(3, index * 4 // len(ordered_sizes))
    total = manifest["totals"]["unique_bytes"]
    minimum = math.ceil(total * 0.20)
    maximum = math.floor(total * 0.50)
    best: tuple[int, str, tuple[str, ...]] | None = None
    for names in itertools.combinations(eligible, 5):
        held = sum(sizes[name] for name in names)
        if held < minimum or held > maximum:
            continue
        if len({_plugin(item["path"]) for name in names for item in groups[name]}) < 3:
            continue
        if len({quartile[name] for name in names}) < 3:
            continue
        tie = _sha256((SELECTION_SEED + "\0" + "\0".join(names)).encode("utf-8"))
        score = (held - minimum, tie, names)
        if best is None or score < best:
            best = score
    if best is None:
        raise Refusal(
            "deterministic holdout selection has no feasible five-skill cohort"
        )
    return list(best[2])


def _size_deciles(records: list[dict[str, Any]]) -> dict[str, int]:
    ordered = sorted(records, key=lambda item: (item["bytes"], item["path"]))
    return {
        item["path"]: min(9, index * 10 // len(ordered))
        for index, item in enumerate(ordered)
    }


def _observed_constructs(paths: list[str]) -> list[str]:
    data = b"\n".join(_source_blob(path) for path in paths)
    checks = {
        "authority": (b"authoris", b"authority"),
        "failure": (b"fail",),
        "recovery": (b"Recovery:",),
        "exact-literal": (b"```", b"`"),
        "cross-document": (b".md",),
        "order": (b"order",),
        "scope": (b"scope",),
        "negation": (b" not ",),
        "exception": (b"Exceptions:",),
        "unknown": (b"unknown",),
        "refusal": (b"Refuses:",),
    }
    present = [
        name
        for name, needles in checks.items()
        if any(needle in data for needle in needles)
    ]
    if set(present) != set(checks):
        raise Refusal("development cohort misses an observed construct class")
    return sorted(present)


def _case_envelope(skills: list[str]) -> list[dict[str, str]]:
    semantic = ["authority", "failure", "recovery", "exact-literal", "cross-document"]
    shapes = ["decision", "refusal", "recovery", "tool-invocation", "structured-plan"]
    slots: list[dict[str, str]] = []
    for index in range(16):
        slots.append(
            {
                "id": f"holdout-{index + 1:02d}",
                "logical_skill": skills[index % len(skills)],
                "semantic_class": semantic[index % len(semantic)],
                "response_shape": shapes[(index * 3) % len(shapes)],
            }
        )
    return slots


def build_cohorts(manifest: dict[str, Any]) -> dict[str, Any]:
    unique_records = [
        item
        for item in manifest["documents"]
        if item["path"] == item["canonical_content_path"]
    ]
    holdout_skills = _choose_holdout(manifest)
    holdout_logical = {f"skill:{name}" for name in holdout_skills}
    holdout_records = [
        item for item in unique_records if item["logical_document"] in holdout_logical
    ]
    development_records = [
        item for item in unique_records if item not in holdout_records
    ]
    generated_paths = sorted(
        item["path"]
        for item in manifest["documents"]
        if item["path"] != item["canonical_content_path"]
    )
    total = manifest["totals"]["unique_bytes"]
    deciles = _size_deciles(unique_records)
    development_deciles = sorted(
        {deciles[item["path"]] for item in development_records}
    )
    if development_deciles != list(range(10)):
        raise Refusal("development cohort does not cover every size decile")
    development_skills = sorted(
        {
            item["logical_document"].removeprefix("skill:")
            for item in development_records
            if item["logical_document"].startswith("skill:")
        }
    )
    development_bytes = sum(item["bytes"] for item in development_records)
    holdout_bytes = sum(item["bytes"] for item in holdout_records)
    if len(development_skills) < 12 or development_bytes / total < 0.50:
        raise Refusal("development cohort coverage gate failed")
    if len(holdout_skills) != 5 or holdout_bytes / total < 0.20:
        raise Refusal("holdout cohort coverage gate failed")
    if {item["path"] for item in development_records} & {
        item["path"] for item in holdout_records
    }:
        raise Refusal("development and holdout cohorts overlap")
    slots = _case_envelope(holdout_skills)
    return {
        "schema": f"{SCHEMA_PREFIX}-cohorts/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": _artifact_digest(manifest),
        "selection": {
            "seed": SELECTION_SEED,
            "method": "enumerate five-skill combinations; require three plugins and three size quartiles; minimise bytes above the 20 percent floor; break ties by seeded SHA-256",
            "excluded_from_holdout": [
                "fiat: required by the merged WAI1 development control",
                "horos: required by the merged WAI1 development control",
                "promise-machine: shared root and merged WAI1 development control",
            ],
        },
        "development": {
            "logical_skills": development_skills,
            "paths": sorted(item["path"] for item in development_records),
            "unique_bytes": development_bytes,
            "unique_byte_ratio": f"{development_bytes / total:.6f}",
            "authority_tiers": sorted(
                {item["authority_tier"] for item in development_records}
            ),
            "size_deciles": development_deciles,
            "constructs": _observed_constructs(
                sorted(item["path"] for item in development_records)
            ),
        },
        "holdout": {
            "logical_skills": holdout_skills,
            "paths": sorted(item["path"] for item in holdout_records),
            "unique_bytes": holdout_bytes,
            "unique_byte_ratio": f"{holdout_bytes / total:.6f}",
            "semantic_classes": [
                "authority",
                "failure",
                "recovery",
                "exact-literal",
                "cross-document",
            ],
            "case_slots": slots,
        },
        "generated_duplicates_excluded": generated_paths,
    }


def build_holdout_seal(
    manifest: dict[str, Any], cohorts: dict[str, Any]
) -> dict[str, Any]:
    membership = {
        "logical_skills": cohorts["holdout"]["logical_skills"],
        "paths": cohorts["holdout"]["paths"],
    }
    envelope = {
        "slots": cohorts["holdout"]["case_slots"],
        "forbidden_until_open": [
            "prompt",
            "expected_answer",
            "scorer_key",
            "model_output",
        ],
    }
    body = {
        "schema": f"{SCHEMA_PREFIX}-holdout-seal/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": _artifact_digest(manifest),
        "cohorts_sha256": _artifact_digest(cohorts),
        "selection_seed": SELECTION_SEED,
        "membership": membership,
        "membership_sha256": _sha256(_canonical_json(membership)),
        "closed_future_case_envelope": envelope,
        "case_envelope_sha256": _sha256(_canonical_json(envelope)),
        "opened": False,
    }
    return {**body, "commitment_sha256": _sha256(_canonical_json(body))}


def _validate_manifest_shape(manifest: dict[str, Any]) -> None:
    _require_fields(
        manifest,
        ("schema", "source", "counts", "totals", "documents"),
        ("schema", "source", "counts", "totals", "documents"),
        "manifest",
    )
    if manifest["schema"] != f"{SCHEMA_PREFIX}-corpus-manifest/v1":
        raise Refusal("unsupported manifest schema")
    if not isinstance(manifest["documents"], list):
        raise Refusal("manifest documents must be an array")
    fields = {
        "path",
        "logical_document",
        "document_class",
        "bytes",
        "sha256",
        "exact_duplicate_group",
        "canonical_content_path",
        "canonical_owner",
        "authority_tier",
        "loader_roots",
        "scenario_reachability",
        "external_runtime_owner",
    }
    for index, item in enumerate(manifest["documents"]):
        if not isinstance(item, dict) or set(item) != fields:
            raise Refusal(f"manifest document {index} has a non-closed field set")
        _safe_relative(item["path"])


def _validate_partition_closure(partition: dict[str, Any]) -> None:
    for file_record in partition["files"]:
        cursor = 0
        data = _source_blob(file_record["path"])
        for item in file_record["ranges"]:
            if set(item) != {"start", "end", "classification", "span_sha256"}:
                raise Refusal("partition range has a non-closed field set")
            if item["start"] != cursor or item["end"] <= item["start"]:
                raise Refusal("partition ranges overlap, gap, or are unordered")
            if item["classification"] not in PARTITION_CLASSES:
                raise Refusal("partition range has an unknown class")
            if _sha256(data[item["start"] : item["end"]]) != item["span_sha256"]:
                raise Refusal("partition span digest mismatch")
            cursor = item["end"]
        if cursor != len(data) or cursor != file_record["bytes"]:
            raise Refusal("partition does not close over its source")


def _verify_exact(
    path: Path, expected: dict[str, Any], label: str
) -> tuple[dict[str, Any], bytes]:
    actual, raw = _load_record(path)
    if actual != expected:
        raise Refusal(f"{label} differs from its source-bound derivation")
    return actual, raw


def _result(command: str, artifact: bytes, metrics: dict[str, Any]) -> bytes:
    artifact_sha = _sha256(artifact)
    return _canonical_json(
        {
            "schema": f"{SCHEMA_PREFIX}-verification/v1",
            "command": command,
            "run_id": _sha256(
                (SOURCE_REF + "\0" + command + "\0" + artifact_sha).encode()
            ),
            "source_ref": SOURCE_REF,
            "artifact_sha256": artifact_sha,
            "status": "pass",
            "metrics": metrics,
        }
    )


def verify_corpus(args: argparse.Namespace) -> bytes:
    expected = build_manifest()
    manifest, raw = _verify_exact(args.manifest, expected, "corpus manifest")
    _validate_manifest_shape(manifest)
    return _result("verify-corpus", raw, manifest["totals"])


def verify_loader(args: argparse.Namespace) -> bytes:
    manifest, _ = _load_record(args.manifest)
    _validate_manifest_shape(manifest)
    if manifest != build_manifest():
        raise Refusal("loader manifest is stale")
    expected = build_loader_graph(manifest)
    graph, raw = _verify_exact(args.graph, expected, "loader graph")
    paths = {item["path"] for item in manifest["documents"]}
    for edge in graph["edges"]:
        if edge["source"] not in paths or edge["target"] not in paths:
            raise Refusal("loader graph escapes the manifest")
        evidence = edge["evidence"]
        data = _source_blob(evidence["path"])
        span = data[evidence["start"] : evidence["end"]]
        if (
            _sha256(data) != evidence["source_sha256"]
            or _sha256(span) != evidence["span_sha256"]
        ):
            raise Refusal("loader evidence digest mismatch")
    return _result(
        "verify-loader",
        raw,
        {"roots": len(graph["roots"]), "edges": len(graph["edges"])},
    )


def verify_partition(args: argparse.Namespace) -> bytes:
    manifest, _ = _load_record(args.manifest)
    _validate_manifest_shape(manifest)
    if manifest != build_manifest():
        raise Refusal("partition manifest is stale")
    expected = build_partition(manifest)
    partition, raw = _verify_exact(args.partition, expected, "byte partition")
    _validate_partition_closure(partition)
    if partition["unsupported_operative_bytes"] != 0:
        raise Refusal("unsupported operative bytes block selection")
    return _result("verify-partition", raw, partition["totals"])


def verify_seal(args: argparse.Namespace) -> bytes:
    manifest, _ = _load_record(args.manifest)
    _validate_manifest_shape(manifest)
    if manifest != build_manifest():
        raise Refusal("seal manifest is stale")
    expected_cohorts = build_cohorts(manifest)
    cohorts, _ = _verify_exact(args.cohorts, expected_cohorts, "cohorts")
    expected_seal = build_holdout_seal(manifest, cohorts)
    seal, raw = _verify_exact(args.seal, expected_seal, "holdout seal")
    body = dict(seal)
    commitment = body.pop("commitment_sha256")
    if _sha256(_canonical_json(body)) != commitment or seal["opened"] is not False:
        raise Refusal("holdout commitment is open or inconsistent")
    forbidden = set(seal["closed_future_case_envelope"]["forbidden_until_open"])
    for slot in seal["closed_future_case_envelope"]["slots"]:
        if forbidden & set(slot):
            raise Refusal("sealed slot contains answer-bearing material")
    return _result(
        "verify-seal",
        raw,
        {
            "development_skills": len(cohorts["development"]["logical_skills"]),
            "holdout_skills": len(cohorts["holdout"]["logical_skills"]),
            "holdout_case_slots": len(cohorts["holdout"]["case_slots"]),
        },
    )


def _safe_output(path: Path) -> Path:
    relative = _repository_relative(path, "output")
    parent, name = _open_parent(relative, create=True, label="output")
    try:
        try:
            metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            metadata = None
        except OSError as exc:
            raise Refusal("output target is unavailable or unsafe") from exc
        if metadata is not None and not stat.S_ISREG(metadata.st_mode):
            raise Refusal("output target is not an ordinary file")
    finally:
        os.close(parent)
    return ROOT / Path(*relative.parts)


def _fresh_named_identity(
    relative: PurePosixPath, parent_identity: tuple[int, ...], expected: os.stat_result
) -> None:
    parent, name = _open_parent(relative, create=False, label="output")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    try:
        if _directory_identity(os.fstat(parent)) != parent_identity:
            raise Refusal("output parent changed during publication")
        try:
            descriptor = os.open(name, flags, dir_fd=parent)
        except OSError as exc:
            raise Refusal("output changed during publication") from exc
        try:
            if _identity(os.fstat(descriptor)) != _identity(expected):
                raise Refusal("output changed during publication")
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def _atomic_write(path: Path, data: bytes) -> None:
    path = _safe_output(path)
    relative = _repository_relative(path, "output")
    parent, name = _open_parent(relative, create=True, label="output")
    parent_identity = _directory_identity(os.fstat(parent))
    temporary: str | None = None
    try:
        descriptor = -1
        for _ in range(32):
            candidate = f".{name}.{secrets.token_hex(16)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=parent,
                )
                temporary = candidate
                break
            except FileExistsError:
                continue
            except OSError as exc:
                raise Refusal("output stage is unavailable or unsafe") from exc
        if temporary is None or descriptor < 0:
            raise Refusal("could not allocate an output stage")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            staged = os.fstat(handle.fileno())
        try:
            named_stage = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError as exc:
            raise Refusal("output stage changed before publication") from exc
        try:
            if _identity(os.fstat(named_stage)) != _identity(staged):
                raise Refusal("output stage changed before publication")
        finally:
            os.close(named_stage)
        routed_parent, _ = _open_parent(relative, create=False, label="output")
        try:
            if _directory_identity(os.fstat(routed_parent)) != parent_identity:
                raise Refusal("output parent changed before publication")
        finally:
            os.close(routed_parent)
        os.replace(
            temporary,
            name,
            src_dir_fd=parent,
            dst_dir_fd=parent,
        )
        temporary = None
        os.fsync(parent)
        try:
            published = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError as exc:
            raise Refusal("published output is unavailable or unsafe") from exc
        try:
            reread, published_stat = _read_descriptor(
                published, max(MAX_JSON_BYTES, len(data))
            )
        finally:
            os.close(published)
        if reread != data:
            raise Refusal("published output failed reread")
        _fresh_named_identity(relative, parent_identity, published_stat)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _reconciliation_markdown(
    manifest: dict[str, Any],
    graph: dict[str, Any],
    partition: dict[str, Any],
    cohorts: dict[str, Any],
) -> bytes:
    totals = manifest["totals"]
    classes = manifest["counts"]
    text = f"""# instruction architecture corpus reconciliation

source: `{SOURCE_REF}`

the framework-74 corpus contains {totals["physical_files"]:,} physical files and
{totals["physical_bytes"]:,} physical bytes. exact whole-file deduplication leaves
{totals["unique_files"]:,} files and {totals["unique_bytes"]:,} bytes. these are
repository denominators, not prompt-size or semantic-compression claims.

## inventory

| class | files |
| --- | ---: |
| canonical skill contracts | {classes["skill_contract"]} |
| runtime contracts | {classes["runtime_contract"]} |
| Promise Machine contracts | {classes["promise_machine_contract"]} |
| linked Markdown references | {classes["markdown_reference"]} |

the sole exact duplicate family is the root Promise Machine contract and its
17 generated plugin copies. that family accounts for
{totals["physical_bytes"] - totals["unique_bytes"]:,} bytes removed by exact
deduplication. similar prose is not deduplicated.

## loader evidence

`loader-graph.json` records {len(graph["roots"])} roots and {len(graph["edges"])}
edges. every edge cites a source path, exact byte range, source digest and span
digest. unconditional runtime loads and conditional selection or reference
loads remain distinct. a file's presence creates no edge. fixtures and
`distribution/skills-runtime/` are outside this corpus.

## byte classes

the partition is gapless over every physical source byte. generated Promise
Machine copies are `generated_duplicate`; fenced command and data blocks are
`exact_literal_or_evidence`; all remaining canonical Markdown stays in the
conservative `governed_operative_semantics` class. no prose is discarded as
human-only and no byte is treated as a saving through uncertainty.

## cohorts

the development cohort holds {len(cohorts["development"]["logical_skills"])}
logical skills and {cohorts["development"]["unique_bytes"]:,} exact-unique
bytes ({cohorts["development"]["unique_byte_ratio"]}). the sealed holdout holds
five logical skills and {cohorts["holdout"]["unique_bytes"]:,} exact-unique
bytes ({cohorts["holdout"]["unique_byte_ratio"]}). memberships are disjoint.
the development set covers every shared root and runtime contract, all ten
file-size deciles and every construct class recorded in `cohorts.json`.

`holdout-seal.json` commits the selection method, seed, membership and 16-slot
case envelope. it contains no prompt, expected answer, scorer key or model
output. later work may open that envelope once; Step 1 does not score it.

## refusal boundary

all four verification commands rebuild from the fixed Git ref and compare the
live source bytes before accepting an artefact. a path, byte, digest, loader
span, partition range, cohort member or commitment that drifts refuses with
the failed predicate. current prompt and scenario-reachable denominators remain
unmeasured until the later arm and case builders exist.
"""
    return text.encode("utf-8")


def build_baseline(args: argparse.Namespace) -> bytes:
    manifest = build_manifest()
    graph = build_loader_graph(manifest)
    partition = build_partition(manifest)
    cohorts = build_cohorts(manifest)
    seal = build_holdout_seal(manifest, cohorts)
    output = args.output
    records = {
        "corpus-manifest.json": manifest,
        "loader-graph.json": graph,
        "byte-partition.json": partition,
        "cohorts.json": cohorts,
        "holdout-seal.json": seal,
    }
    digests: dict[str, dict[str, Any]] = {}
    for name, value in records.items():
        data = _canonical_json(value)
        _atomic_write(output / name, data)
        digests[name] = {"bytes": len(data), "sha256": _sha256(data)}
    inventory = {
        "schema": f"{SCHEMA_PREFIX}-artifact-inventory/v1",
        "source_ref": SOURCE_REF,
        "source_tree_sha256": manifest["source"]["tree_sha256"],
        "artifacts": digests,
    }
    _atomic_write(output / "artifact-inventory.json", _canonical_json(inventory))
    if args.reconciliation is not None:
        _atomic_write(
            args.reconciliation,
            _reconciliation_markdown(manifest, graph, partition, cohorts),
        )
    return _result(
        "build-baseline",
        _canonical_json(inventory),
        {
            **manifest["totals"],
            "loader_edges": len(graph["edges"]),
            "holdout_skills": len(cohorts["holdout"]["logical_skills"]),
        },
    )


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Build and verify the framework-74 source-bound research corpus."
    )
    subparsers = result.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-baseline")
    build.add_argument(
        "--output",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture",
    )
    build.add_argument(
        "--reconciliation",
        type=_path,
        default=ROOT / "docs/instruction-architecture/corpus-reconciliation.md",
    )
    build.set_defaults(handler=build_baseline)

    corpus = subparsers.add_parser("verify-corpus")
    corpus.add_argument("--manifest", type=_path, required=True)
    corpus.set_defaults(handler=verify_corpus)

    loader = subparsers.add_parser("verify-loader")
    loader.add_argument("--manifest", type=_path, required=True)
    loader.add_argument("--graph", type=_path, required=True)
    loader.set_defaults(handler=verify_loader)

    partition = subparsers.add_parser("verify-partition")
    partition.add_argument("--manifest", type=_path, required=True)
    partition.add_argument("--partition", type=_path, required=True)
    partition.set_defaults(handler=verify_partition)

    seal = subparsers.add_parser("verify-seal")
    seal.add_argument("--manifest", type=_path, required=True)
    seal.add_argument("--cohorts", type=_path, required=True)
    seal.add_argument("--seal", type=_path, required=True)
    seal.set_defaults(handler=verify_seal)
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        sys.stdout.buffer.write(args.handler(args))
        return 0
    except Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
