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


def _open_flags(*, directory: bool) -> int:
    """Return the platform flags required for a no-follow descriptor walk."""

    if not hasattr(os, "O_NOFOLLOW") or (directory and not hasattr(os, "O_DIRECTORY")):
        raise TopologyError("T018 platform lacks no-follow directory traversal")
    flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    if directory:
        flags |= os.O_DIRECTORY
    else:
        flags |= getattr(os, "O_NONBLOCK", 0)
    return flags


def _open_directory(
    target: str | os.PathLike[str],
    *,
    display: Path,
    dir_fd: int | None = None,
) -> int:
    """Open one directory without following its final path component."""

    try:
        descriptor = os.open(target, _open_flags(directory=True), dir_fd=dir_fd)
    except OSError as exc:
        raise TopologyError(
            f"T009 directory is absent, non-directory, or symlinked: {display}: {exc}"
        ) from exc
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise TopologyError(f"T009 input is not a directory: {display}")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_regular_file(
    target: str | os.PathLike[str],
    *,
    display: Path,
    dir_fd: int,
) -> int:
    """Open one regular file without following its final path component."""

    try:
        descriptor = os.open(target, _open_flags(directory=False), dir_fd=dir_fd)
    except OSError as exc:
        raise TopologyError(f"T002 cannot read regular file {display}: {exc}") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise TopologyError(f"T002 input is not a regular file: {display}")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _read_regular_file(root: Path, relative: Path, *, maximum: int) -> bytes:
    """Read one bounded regular file through no-follow directory descriptors."""

    parts = _safe_parts(relative)
    descriptors: list[int] = []
    try:
        current = _open_directory(root, display=Path("."))
        descriptors.append(current)
        for part in parts[:-1]:
            current = _open_directory(
                part,
                display=Path(*parts[: len(descriptors)]),
                dir_fd=current,
            )
            descriptors.append(current)
        descriptor = _open_regular_file(
            parts[-1], display=relative, dir_fd=current
        )
        descriptors.append(descriptor)
        info = os.fstat(descriptor)
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
        closed = os.fstat(descriptor)
        try:
            named = os.stat(parts[-1], dir_fd=current, follow_symlinks=False)
        except OSError as exc:
            raise TopologyError(
                f"T019 input changed while it was read: {relative}: {exc}"
            ) from exc
        opened_identity = (
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        )
        closed_identity = (
            closed.st_dev,
            closed.st_ino,
            closed.st_size,
            closed.st_mtime_ns,
            closed.st_ctime_ns,
        )
        named_identity = (
            named.st_dev,
            named.st_ino,
            named.st_size,
            named.st_mtime_ns,
            named.st_ctime_ns,
        )
        if opened_identity != closed_identity or closed_identity != named_identity:
            raise TopologyError(f"T019 input changed while it was read: {relative}")
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


def _discover_plugin_skills(root: Path, plugin_id: str) -> list[GovernedSkill]:
    discovered: list[GovernedSkill] = []
    entries_seen = 0

    def walk(directory_fd: int, relative: Path, depth: int) -> None:
        nonlocal entries_seen
        try:
            with os.scandir(directory_fd) as scan:
                names: list[str] = []
                for entry in scan:
                    names.append(entry.name)
                    if entries_seen + len(names) > MAX_SKILL_ENTRIES:
                        raise TopologyError(
                            f"T010 skill tree exceeds {MAX_SKILL_ENTRIES} entries: "
                            f"plugins/{plugin_id}/skills"
                        )
                names.sort()
        except OSError as exc:
            raise TopologyError(f"T009 cannot scan {relative}: {exc}") from exc
        for name in names:
            entries_seen += 1
            child = relative / name
            try:
                info = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError as exc:
                raise TopologyError(f"T009 cannot inspect {child}: {exc}") from exc
            if stat.S_ISLNK(info.st_mode):
                raise TopologyError(
                    f"T011 symlinked skill-tree entry is refused: {child}"
                )
            if stat.S_ISDIR(info.st_mode):
                if depth >= MAX_SKILL_DEPTH:
                    raise TopologyError(
                        f"T010 skill tree exceeds depth {MAX_SKILL_DEPTH}: "
                        f"{child}"
                    )
                child_fd = _open_directory(name, display=child, dir_fd=directory_fd)
                try:
                    walk(child_fd, child, depth + 1)
                finally:
                    os.close(child_fd)
                continue
            if name != "EVOLUTION.md":
                continue
            if not stat.S_ISREG(info.st_mode):
                raise TopologyError(f"T002 input is not a regular file: {child}")
            evolution_fd = _open_regular_file(
                name, display=child, dir_fd=directory_fd
            )
            os.close(evolution_fd)
            skill_directory = relative
            skill_id = relative.name
            if IDENTIFIER_RE.fullmatch(skill_id) is None:
                raise TopologyError(
                    f"T012 invalid governed skill id {skill_id!r}: "
                    f"{skill_directory}"
                )
            canonical = skill_directory / "SKILL.md"
            try:
                canonical_fd = _open_regular_file(
                    "SKILL.md", display=canonical, dir_fd=directory_fd
                )
            except TopologyError as exc:
                raise TopologyError(
                    f"T013 governed skill lacks a regular canonical SKILL.md: "
                    f"{skill_directory}"
                ) from exc
            os.close(canonical_fd)
            discovered.append(
                GovernedSkill(
                    id=skill_id,
                    plugin_id=plugin_id,
                    directory=skill_directory.as_posix(),
                )
            )

    root_fd = _open_directory(root, display=Path("."))
    try:
        plugins_fd = _open_directory("plugins", display=Path("plugins"), dir_fd=root_fd)
        try:
            plugin_fd = _open_directory(
                plugin_id,
                display=Path("plugins") / plugin_id,
                dir_fd=plugins_fd,
            )
            try:
                skills_relative = Path("plugins") / plugin_id / "skills"
                skills_fd = _open_directory(
                    "skills", display=skills_relative, dir_fd=plugin_fd
                )
                try:
                    walk(skills_fd, skills_relative, 0)
                finally:
                    os.close(skills_fd)
            finally:
                os.close(plugin_fd)
        finally:
            os.close(plugins_fd)
    finally:
        os.close(root_fd)
    return discovered


def discover_topology(root: str | os.PathLike[str] = ".") -> ShoggothTopology:
    """Return the closed host-manifest and governed-skill topology at ``root``."""

    repository = Path(os.path.abspath(os.fspath(root)))
    repository_fd = _open_directory(repository, display=Path("."))
    os.close(repository_fd)
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
