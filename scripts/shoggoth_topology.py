#!/usr/bin/env python3
"""Discover the shipped Shoggoth plugin and governed-skill topology."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
import re
import stat
from typing import Any


CLAUDE_MARKETPLACE = Path(".claude-plugin/marketplace.json")
CODEX_MARKETPLACE = Path(".agents/plugins/marketplace.json")
MAX_MANIFEST_BYTES = 1_048_576
MAX_PLUGINS = 128
MAX_SKILL_ENTRIES = 4_096
MAX_SKILL_DEPTH = 8
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9-]{0,127}$")
CANONICAL_ENTRY_OVERRIDES = {"hexaemeron": "fiat"}
PHASE_PLUGIN = "hexaemeron"


class TopologyError(ValueError):
    """A repository topology input failed its closed boundary."""


class _DuplicateKey(ValueError):
    pass


@dataclass(frozen=True, order=True)
class GovernedSkill:
    """One first-party skill directory discovered from its evolution ledger."""

    id: str
    plugin_id: str
    directory: str


@dataclass(frozen=True)
class ShoggothTopology:
    """The joined host manifests and governed first-party skill universe."""

    plugin_ids: tuple[str, ...]
    governed_skills: tuple[GovernedSkill, ...]
    canonical_ids: tuple[str, ...]
    phase_ids: tuple[str, ...]

    @property
    def governed_ids(self) -> tuple[str, ...]:
        return tuple(skill.id for skill in self.governed_skills)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _safe_parts(relative: Path) -> tuple[str, ...]:
    if relative.is_absolute() or not relative.parts:
        raise TopologyError(f"T001 unsafe repository path: {relative}")
    parts = tuple(relative.parts)
    if any(part in {"", ".", ".."} or "/" in part or "\\" in part for part in parts):
        raise TopologyError(f"T001 unsafe repository path: {relative}")
    return parts


def _read_regular_file(root: Path, relative: Path, *, maximum: int) -> bytes:
    """Read one bounded regular file through no-follow directory descriptors."""

    parts = _safe_parts(relative)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptors: list[int] = []
    try:
        current = os.open(os.fspath(root), directory_flags)
        descriptors.append(current)
        for part in parts[:-1]:
            current = os.open(part, directory_flags, dir_fd=current)
            descriptors.append(current)
        descriptor = os.open(parts[-1], file_flags, dir_fd=current)
        descriptors.append(descriptor)
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise TopologyError(f"T002 input is not a regular file: {relative}")
        if info.st_size > maximum:
            raise TopologyError(
                f"T003 input exceeds {maximum} bytes: {relative}"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise TopologyError(
                    f"T003 input exceeds {maximum} bytes: {relative}"
                )
        return b"".join(chunks)
    except TopologyError:
        raise
    except OSError as exc:
        raise TopologyError(f"T002 cannot read regular file {relative}: {exc}") from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _read_json(root: Path, relative: Path) -> dict[str, Any]:
    payload = _read_regular_file(root, relative, maximum=MAX_MANIFEST_BYTES)
    try:
        text = payload.decode("utf-8")
        document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateKey) as exc:
        raise TopologyError(f"T004 invalid JSON in {relative}: {exc}") from exc
    if not isinstance(document, dict):
        raise TopologyError(f"T004 JSON root is not an object: {relative}")
    return document


def _plugin_id(value: Any, *, location: str) -> str:
    if not isinstance(value, str) or IDENTIFIER_RE.fullmatch(value) is None:
        raise TopologyError(f"T005 invalid plugin id at {location}: {value!r}")
    return value


def _manifest_plugins(root: Path, relative: Path, *, host: str) -> tuple[str, ...]:
    document = _read_json(root, relative)
    entries = document.get("plugins")
    if not isinstance(entries, list) or not entries or len(entries) > MAX_PLUGINS:
        raise TopologyError(
            f"T006 plugins must be a non-empty list of at most {MAX_PLUGINS}: {relative}"
        )
    found: list[str] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        location = f"{relative}:plugins[{index}]"
        if not isinstance(entry, dict):
            raise TopologyError(f"T006 plugin entry is not an object: {location}")
        plugin_id = _plugin_id(entry.get("name"), location=location)
        if plugin_id in seen:
            raise TopologyError(f"T007 duplicate plugin id {plugin_id!r}: {relative}")
        seen.add(plugin_id)
        source = entry.get("source")
        if host == "codex":
            source = source.get("path") if isinstance(source, dict) else None
        expected = f"./plugins/{plugin_id}"
        if source != expected:
            raise TopologyError(
                f"T008 plugin path is outside the closed plugins mapping for "
                f"{plugin_id!r}: {source!r}; expected {expected!r}"
            )
        found.append(plugin_id)
    return tuple(sorted(found))


def _regular_path(path: Path) -> bool:
    try:
        return stat.S_ISREG(os.lstat(path).st_mode)
    except OSError:
        return False


def _directory_path(path: Path) -> bool:
    try:
        return stat.S_ISDIR(os.lstat(path).st_mode)
    except OSError:
        return False


def _discover_plugin_skills(root: Path, plugin_id: str) -> list[GovernedSkill]:
    plugin_root = root / "plugins" / plugin_id
    skills_root = plugin_root / "skills"
    if not _directory_path(plugin_root) or not _directory_path(skills_root):
        raise TopologyError(
            f"T009 plugin or skills directory is absent, non-directory, or symlinked: "
            f"plugins/{plugin_id}"
        )

    discovered: list[GovernedSkill] = []
    stack: list[tuple[Path, int]] = [(skills_root, 0)]
    entries_seen = 0
    while stack:
        directory, depth = stack.pop()
        try:
            with os.scandir(directory) as scan:
                entries = sorted(scan, key=lambda entry: entry.name)
        except OSError as exc:
            raise TopologyError(f"T009 cannot scan {directory.relative_to(root)}: {exc}") from exc
        for entry in entries:
            entries_seen += 1
            if entries_seen > MAX_SKILL_ENTRIES:
                raise TopologyError(
                    f"T010 skill tree exceeds {MAX_SKILL_ENTRIES} entries: "
                    f"plugins/{plugin_id}/skills"
                )
            if entry.is_symlink():
                raise TopologyError(
                    f"T011 symlinked skill-tree entry is refused: "
                    f"{Path(entry.path).relative_to(root)}"
                )
            if entry.is_dir(follow_symlinks=False):
                if depth >= MAX_SKILL_DEPTH:
                    raise TopologyError(
                        f"T010 skill tree exceeds depth {MAX_SKILL_DEPTH}: "
                        f"{Path(entry.path).relative_to(root)}"
                    )
                stack.append((Path(entry.path), depth + 1))
                continue
            if entry.name != "EVOLUTION.md" or not entry.is_file(follow_symlinks=False):
                continue
            skill_directory = Path(entry.path).parent
            skill_id = skill_directory.name
            if IDENTIFIER_RE.fullmatch(skill_id) is None:
                raise TopologyError(
                    f"T012 invalid governed skill id {skill_id!r}: "
                    f"{skill_directory.relative_to(root)}"
                )
            canonical = skill_directory / "SKILL.md"
            if not _regular_path(canonical):
                raise TopologyError(
                    f"T013 governed skill lacks a regular canonical SKILL.md: "
                    f"{skill_directory.relative_to(root)}"
                )
            discovered.append(
                GovernedSkill(
                    id=skill_id,
                    plugin_id=plugin_id,
                    directory=skill_directory.relative_to(root).as_posix(),
                )
            )
    return discovered


def discover_topology(root: str | os.PathLike[str] = ".") -> ShoggothTopology:
    """Return the closed host-manifest and governed-skill topology at ``root``."""

    repository = Path(os.path.abspath(os.fspath(root)))
    if not _directory_path(repository):
        raise TopologyError(f"T001 repository root is absent, non-directory, or symlinked: {root}")
    claude = _manifest_plugins(repository, CLAUDE_MARKETPLACE, host="claude")
    codex = _manifest_plugins(repository, CODEX_MARKETPLACE, host="codex")
    if claude != codex:
        raise TopologyError(
            "T014 host marketplace disagreement: "
            f"claude-only={sorted(set(claude) - set(codex))!r} "
            f"codex-only={sorted(set(codex) - set(claude))!r}"
        )

    governed: list[GovernedSkill] = []
    for plugin_id in claude:
        governed.extend(_discover_plugin_skills(repository, plugin_id))
    governed.sort()
    seen_skills: set[str] = set()
    for skill in governed:
        if skill.id in seen_skills:
            raise TopologyError(f"T015 duplicate governed skill id {skill.id!r}")
        seen_skills.add(skill.id)

    canonical: list[GovernedSkill] = []
    for plugin_id in claude:
        expected = CANONICAL_ENTRY_OVERRIDES.get(plugin_id, plugin_id)
        matches = [
            skill
            for skill in governed
            if skill.plugin_id == plugin_id and skill.id == expected
        ]
        if len(matches) != 1:
            raise TopologyError(
                f"T016 plugin {plugin_id!r} lacks its one governed canonical skill "
                f"{expected!r}"
            )
        canonical.append(matches[0])

    canonical_directories = {skill.directory for skill in canonical}
    phases = [skill for skill in governed if skill.directory not in canonical_directories]
    unexpected = [skill for skill in phases if skill.plugin_id != PHASE_PLUGIN]
    if unexpected:
        rendered = [f"{skill.plugin_id}:{skill.id}" for skill in unexpected]
        raise TopologyError(
            f"T017 unexpected phase outside {PHASE_PLUGIN!r}: {rendered!r}"
        )

    return ShoggothTopology(
        plugin_ids=claude,
        governed_skills=tuple(governed),
        canonical_ids=tuple(sorted(skill.id for skill in canonical)),
        phase_ids=tuple(sorted(skill.id for skill in phases)),
    )


__all__ = [
    "GovernedSkill",
    "ShoggothTopology",
    "TopologyError",
    "discover_topology",
]
