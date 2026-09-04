#!/usr/bin/env python3
"""Derive this repository's plugin and skill topology instead of writing it down.

Public prose has repeatedly carried counts a person typed once and nobody
updated. This module answers the same questions from the tree and the two
marketplace manifests, so a claim about how many plugins or governed skills
exist can be checked rather than trusted.

Three sources must agree. The Claude manifest at
`.claude-plugin/marketplace.json` and the agent manifest at
`.agents/plugins/marketplace.json` each declare a plugin set; discovery walks
`plugins/<id>/skills/<skill>/EVOLUTION.md` and derives the same set from the
tree. A governed skill is one that carries an `EVOLUTION.md`, because that
ledger is what puts a skill under the behaviour-frontier contract. Every
plugin has exactly one canonical entry skill, named after the plugin, except
the phase host, whose entry skill is named separately; the remaining governed
skills are its phase skills.

The reader refuses rather than guesses. A duplicate id, a disagreement between
the manifests, a governed directory without a regular `SKILL.md`, a symlinked
entry in a skill tree, a declared path outside `plugins/`, and a phase skill
outside the phase host each raise `TopologyError` with a stable code.

Reads are bounded and follow no symlink: each path is walked one component at
a time from an already-opened root descriptor, so a component cannot be
swapped between the check and the open. JSON with a duplicate key is refused
rather than silently resolved to its last value. No socket is opened and no
subprocess is started.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
from typing import Any, Iterable, Sequence

# The repository's own phase arrangement. Both are parameters rather than
# literals in the walk, so a specimen tree can declare its own host and the
# derivation stays the same function.
DEFAULT_PHASE_HOST = "hexaemeron"
DEFAULT_PHASE_HOST_ENTRY = "fiat"

CLAUDE_MANIFEST = ".claude-plugin/marketplace.json"
AGENTS_MANIFEST = ".agents/plugins/marketplace.json"

PLUGIN_ROOT = "plugins"
SKILLS_DIRECTORY = "skills"
LEDGER_NAME = "EVOLUTION.md"
ENTRY_NAME = "SKILL.md"

# Bounds. A manifest that outgrows these is a change worth noticing, not a
# file to read anyway.
MAX_MANIFEST_BYTES = 1 << 20
MAX_PLUGINS = 512
MAX_SKILLS_PER_PLUGIN = 512
MAX_SKILL_DEPTH = 8
MAX_JSON_DEPTH = 32
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9-]{0,127}$")


class TopologyError(Exception):
    """A refusal with a stable code, so a caller can assert on the reason."""

    def __init__(self, code: str, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail

    def __str__(self) -> str:
        if self.detail is None:
            return f"{self.code}: {self.message}"
        return f"{self.code}: {self.message} ({self.detail!r})"


def _identifier(value: Any, *, label: str, code: str) -> str:
    """Return one portable plugin or skill id, or refuse it by name."""
    if not isinstance(value, str) or IDENTIFIER_RE.fullmatch(value) is None:
        raise TopologyError(
            code,
            f"{label} must match {IDENTIFIER_RE.pattern}",
            value,
        )
    return value


@dataclass(frozen=True)
class Topology:
    """The derived answer. Every field is sorted, so comparison is stable."""

    plugins: tuple[str, ...]
    governed: tuple[str, ...]
    canonical: tuple[str, ...]
    phase: tuple[str, ...]
    phase_host: str
    phase_host_entry: str

    @property
    def plugin_count(self) -> int:
        return len(self.plugins)

    @property
    def governed_count(self) -> int:
        return len(self.governed)

    @property
    def canonical_count(self) -> int:
        return len(self.canonical)

    @property
    def phase_count(self) -> int:
        return len(self.phase)

    @property
    def phase_ids(self) -> tuple[str, ...]:
        """The phase skill names alone, without their governed path."""
        return tuple(path.rsplit("/", 1)[1] for path in self.phase)

    def counts(self) -> dict[str, int]:
        return {
            "plugins": self.plugin_count,
            "governed": self.governed_count,
            "canonical": self.canonical_count,
            "phase": self.phase_count,
        }


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise TopologyError(
                "duplicate-json-key",
                "a manifest object declares the same key twice",
                key,
            )
        seen[key] = value
    return seen


def _refuse_deep(value: Any, depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise TopologyError(
            "manifest-too-deep",
            f"a manifest nests deeper than {MAX_JSON_DEPTH} levels",
        )
    if isinstance(value, dict):
        for item in value.values():
            _refuse_deep(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _refuse_deep(item, depth + 1)


def _safe_relpath(value: str, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TopologyError(
            "unsafe-path", f"{label} must be a non-empty string", value
        )
    if value.startswith("/") or ":" in value:
        raise TopologyError(
            "unsafe-path", f"{label} must be repository-relative", value
        )
    parts = [part for part in value.split("/") if part and part != "."]
    if any(part == ".." for part in parts):
        raise TopologyError("unsafe-path", f"{label} must not traverse", value)
    if any(part == ".git" for part in parts):
        raise TopologyError(
            "unsafe-path", f"{label} must not enter a Git namespace", value
        )
    if not parts:
        raise TopologyError("unsafe-path", f"{label} is empty", value)
    return "/".join(parts)


def _open_flags(*, directory: bool) -> int:
    """Return the platform flags required for a no-follow descriptor walk."""
    no_follow = getattr(os, "O_NOFOLLOW", None)
    directory_only = getattr(os, "O_DIRECTORY", None)
    if not isinstance(no_follow, int) or no_follow == 0:
        raise TopologyError(
            "unsupported-platform",
            "platform lacks O_NOFOLLOW for confined traversal",
        )
    if directory and (
        not isinstance(directory_only, int) or directory_only == 0
    ):
        raise TopologyError(
            "unsupported-platform",
            "platform lacks O_DIRECTORY for confined traversal",
        )

    flags = os.O_RDONLY | no_follow
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    if isinstance(close_on_exec, int):
        flags |= close_on_exec
    if directory:
        flags |= directory_only
    else:
        # A fixed manifest leaf can still be a FIFO. Non-blocking open lets the
        # regular-file check refuse it instead of waiting for a writer forever.
        nonblocking = getattr(os, "O_NONBLOCK", 0)
        if isinstance(nonblocking, int):
            flags |= nonblocking
    return flags


def _open_confined_directory(root: Path, parts: Sequence[str]) -> int:
    """Open a root-relative directory chain without following a component.

    Validating a pathname and then opening it leaves a substitution window at
    every component. Walking from an already-opened root descriptor makes each
    next component relative to the directory that was actually checked. The
    returned descriptor belongs to the caller.
    """
    flags = _open_flags(directory=True)
    try:
        current = os.open(root, flags)
    except OSError as exc:
        raise TopologyError(
            "unreadable-root", f"cannot open repository root: {exc}"
        ) from exc
    try:
        for part in parts:
            nxt = -1
            try:
                nxt = os.open(part, flags, dir_fd=current)
                if not stat.S_ISDIR(os.fstat(nxt).st_mode):
                    raise OSError(f"not a directory: {part}")
            except OSError:
                if nxt >= 0:
                    os.close(nxt)
                raise
            os.close(current)
            current = nxt
        return current
    except OSError as exc:
        os.close(current)
        raise TopologyError(
            "unsafe-path",
            "a path component is missing, symlinked or not a directory",
            "/".join(parts),
        ) from exc


def _open_regular_at(parent_fd: int, name: str, *, label: str) -> int:
    """Open one no-follow, non-blocking regular leaf below a directory fd."""
    try:
        fd = os.open(name, _open_flags(directory=False), dir_fd=parent_fd)
    except OSError as exc:
        raise TopologyError(
            "unreadable-file", f"cannot open {label}: {exc}", name
        ) from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise TopologyError(
                "unsafe-path", f"{label} is not a regular file", name
            )
        return fd
    except BaseException:
        os.close(fd)
        raise


def _file_identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    """Fields that must stay fixed while one manifest descriptor is read."""
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _read_confined_regular(root: Path, relative: str, *, label: str) -> bytes:
    """Read a bounded regular file through a no-follow descriptor walk."""
    safe = _safe_relpath(relative, label=label)
    parts = safe.split("/")
    parent_fd = _open_confined_directory(root, parts[:-1])
    fd = -1
    try:
        fd = _open_regular_at(parent_fd, parts[-1], label=label)
        opened = os.fstat(fd)
        if opened.st_size > MAX_MANIFEST_BYTES:
            raise TopologyError(
                "manifest-oversized",
                f"{label} exceeds {MAX_MANIFEST_BYTES} bytes",
                safe,
            )
        body = bytearray()
        while len(body) <= MAX_MANIFEST_BYTES:
            chunk = os.read(fd, min(65_536, MAX_MANIFEST_BYTES - len(body) + 1))
            if not chunk:
                break
            body.extend(chunk)
        if len(body) > MAX_MANIFEST_BYTES:
            raise TopologyError(
                "manifest-oversized",
                f"{label} exceeds {MAX_MANIFEST_BYTES} bytes",
                safe,
            )
        closed = os.fstat(fd)
        try:
            named = os.stat(parts[-1], dir_fd=parent_fd, follow_symlinks=False)
        except OSError as exc:
            raise TopologyError(
                "file-changed-during-read",
                f"{label} changed while it was read",
                safe,
            ) from exc
        if not (
            _file_identity(opened)
            == _file_identity(closed)
            == _file_identity(named)
        ):
            raise TopologyError(
                "file-changed-during-read",
                f"{label} changed while it was read",
                safe,
            )
        return bytes(body)
    except TopologyError:
        raise
    except OSError as exc:
        raise TopologyError(
            "unreadable-file", f"cannot read {label}: {exc}", safe
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)


def _load_manifest(root: Path, relative: str, *, label: str) -> Any:
    raw = _read_confined_regular(root, relative, label=label)
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys)
    except UnicodeDecodeError as exc:
        raise TopologyError(
            "manifest-unreadable", f"{label} is not valid UTF-8", relative
        ) from exc
    except json.JSONDecodeError as exc:
        raise TopologyError(
            "manifest-unreadable", f"{label} is not valid JSON: {exc}", relative
        ) from exc
    _refuse_deep(data)
    return data


def _plugin_entries(data: Any, *, label: str) -> list[Any]:
    if not isinstance(data, dict):
        raise TopologyError("manifest-invalid", f"{label} is not an object")
    entries = data.get("plugins")
    if not isinstance(entries, list) or not entries:
        raise TopologyError(
            "manifest-invalid", f"{label} declares no plugins list"
        )
    if len(entries) > MAX_PLUGINS:
        raise TopologyError(
            "manifest-oversized",
            f"{label} declares more than {MAX_PLUGINS} plugins",
            len(entries),
        )
    return entries


def _entry_source(entry: Any, *, label: str) -> str:
    """Pull the declared path out of either manifest's entry shape.

    The Claude manifest carries `source` as a string; the agent manifest
    carries it as an object with a `path`. Both name the same directory, and
    disagreement between them is exactly what this reader exists to catch.
    """
    source = entry.get("source")
    if isinstance(source, str):
        return source
    if isinstance(source, dict):
        path = source.get("path")
        if isinstance(path, str):
            return path
    raise TopologyError(
        "manifest-invalid", f"{label} entry declares no usable source", entry.get("name")
    )


def _declared(root_data: Any, *, label: str) -> dict[str, str]:
    declared: dict[str, str] = {}
    for entry in _plugin_entries(root_data, label=label):
        if not isinstance(entry, dict):
            raise TopologyError(
                "manifest-invalid", f"{label} declares a non-object plugin"
            )
        name = _identifier(
            entry.get("name"),
            label=f"{label} plugin id",
            code="invalid-plugin-id",
        )
        if name in declared:
            raise TopologyError(
                "duplicate-plugin-id",
                f"{label} declares the same plugin id twice",
                name,
            )
        source = _entry_source(entry, label=label)
        expected = f"./{PLUGIN_ROOT}/{name}"
        if source != expected:
            raise TopologyError(
                "path-outside-plugins",
                f"{label} source must exactly name its own plugin directory",
                {"actual": source, "expected": expected},
            )
        declared[name] = expected.removeprefix("./")
    return declared


def _sorted_names(
    directory_fd: int,
    *,
    label: str,
    limit: int,
    already_seen: int = 0,
) -> list[str]:
    """Consume at most ``limit`` names, then sort the bounded collection."""
    names: list[str] = []
    try:
        with os.scandir(directory_fd) as entries:
            for entry in entries:
                names.append(entry.name)
                if already_seen + len(names) > limit:
                    raise TopologyError(
                        "tree-oversized",
                        f"{label} exceeds its {limit}-entry cap",
                        already_seen + len(names),
                    )
    except OSError as exc:
        raise TopologyError(
            "unsafe-path", f"cannot scan {label}: {exc}", label
        ) from exc
    names.sort()
    return names


def _governed_skills(root: Path, plugin: str) -> list[str]:
    """Return governed repository paths under one plugin, recursively sorted.

    A skill is governed when its directory holds a regular `EVOLUTION.md`. The
    walk is anchored at `plugins/<id>/skills` and never follows a link, so a
    ledger reachable only through a symlink is a refusal rather than a count.
    """
    parts = (PLUGIN_ROOT, plugin, SKILLS_DIRECTORY)
    skills_fd = _open_confined_directory(root, parts)
    try:
        governed: list[str] = []
        entries_seen = 0

        def walk(directory_fd: int, relative: str, depth: int) -> None:
            nonlocal entries_seen
            names = _sorted_names(
                directory_fd,
                label=relative,
                limit=MAX_SKILLS_PER_PLUGIN,
                already_seen=entries_seen,
            )
            # Count every consumed entry before descending, including siblings
            # already retained for deterministic ordering.
            entries_seen += len(names)
            for name in names:
                where = f"{relative}/{name}"
                try:
                    info = os.lstat(name, dir_fd=directory_fd)
                except OSError as exc:
                    raise TopologyError(
                        "unsafe-path", f"cannot inspect {where}: {exc}", where
                    ) from exc
                if stat.S_ISLNK(info.st_mode):
                    raise TopologyError(
                        "symlinked-entry",
                        "a skill tree entry is a symbolic link",
                        where,
                    )
                if stat.S_ISDIR(info.st_mode):
                    if depth >= MAX_SKILL_DEPTH:
                        raise TopologyError(
                            "tree-oversized",
                            f"skill tree exceeds depth {MAX_SKILL_DEPTH}",
                            where,
                        )
                    child_fd = -1
                    try:
                        child_fd = os.open(
                            name,
                            _open_flags(directory=True),
                            dir_fd=directory_fd,
                        )
                        if not stat.S_ISDIR(os.fstat(child_fd).st_mode):
                            raise OSError(f"not a directory: {where}")
                    except OSError as exc:
                        if child_fd >= 0:
                            os.close(child_fd)
                        raise TopologyError(
                            "unsafe-path",
                            "a skill-tree entry changed or is not a directory",
                            where,
                        ) from exc
                    try:
                        walk(child_fd, where, depth + 1)
                    finally:
                        os.close(child_fd)
                    continue
                if name != LEDGER_NAME:
                    continue
                if not stat.S_ISREG(info.st_mode):
                    raise TopologyError(
                        "unsafe-path", "a governed ledger is not regular", where
                    )
                ledger_fd = _open_regular_at(
                    directory_fd, LEDGER_NAME, label="governed ledger"
                )
                os.close(ledger_fd)
                _identifier(
                    relative.rsplit("/", 1)[-1],
                    label="governed skill id",
                    code="invalid-skill-id",
                )
                try:
                    entry_fd = _open_regular_at(
                        directory_fd, ENTRY_NAME, label="canonical skill entry"
                    )
                except TopologyError as exc:
                    raise TopologyError(
                        "missing-skill-md",
                        f"a governed skill has no regular {ENTRY_NAME}",
                        relative,
                    ) from exc
                os.close(entry_fd)
                governed.append(relative)

        walk(skills_fd, "/".join(parts), 0)
        return governed
    finally:
        os.close(skills_fd)


def _tree_governed(root: Path) -> tuple[str, ...]:
    """Discover governed skills from the plugin tree, independent of manifests."""
    plugins_fd = _open_confined_directory(root, (PLUGIN_ROOT,))
    try:
        names = _sorted_names(
            plugins_fd,
            label=PLUGIN_ROOT,
            limit=MAX_PLUGINS,
        )
        governed: list[str] = []
        for name in names:
            where = f"{PLUGIN_ROOT}/{name}"
            try:
                info = os.lstat(name, dir_fd=plugins_fd)
            except OSError as exc:
                raise TopologyError(
                    "unsafe-path", f"cannot inspect {where}: {exc}", where
                ) from exc
            if stat.S_ISLNK(info.st_mode):
                raise TopologyError(
                    "symlinked-entry",
                    "a plugin-tree entry is a symbolic link",
                    where,
                )
            if not stat.S_ISDIR(info.st_mode):
                continue
            _identifier(
                name,
                label="discovered plugin id",
                code="invalid-plugin-id",
            )
            found = _governed_skills(root, name)
            if not found:
                continue
            governed.extend(found)
        return tuple(sorted(governed))
    finally:
        os.close(plugins_fd)


def read(
    root: Path | str,
    *,
    phase_host: str = DEFAULT_PHASE_HOST,
    phase_host_entry: str = DEFAULT_PHASE_HOST_ENTRY,
) -> Topology:
    """Derive the topology of the repository rooted at `root`.

    Raises `TopologyError` when the two manifests and the tree do not agree,
    or when the tree breaks one of the structural rules the docstring names.
    """
    root = Path(root)
    phase_host = _identifier(
        phase_host,
        label="phase host plugin id",
        code="invalid-plugin-id",
    )
    phase_host_entry = _identifier(
        phase_host_entry,
        label="phase host entry skill id",
        code="invalid-skill-id",
    )

    claude = _declared(
        _load_manifest(root, CLAUDE_MANIFEST, label="claude manifest"),
        label="claude manifest",
    )
    agents = _declared(
        _load_manifest(root, AGENTS_MANIFEST, label="agent manifest"),
        label="agent manifest",
    )
    if claude != agents:
        raise TopologyError(
            "manifest-disagreement",
            "the two marketplace manifests declare different plugins",
            {
                "claude-only": sorted(set(claude) - set(agents)),
                "agents-only": sorted(set(agents) - set(claude)),
                "path-conflicts": sorted(
                    name
                    for name in set(claude) & set(agents)
                    if claude[name] != agents[name]
                ),
            },
        )

    plugins = tuple(sorted(claude))
    governed = _tree_governed(root)

    from_tree = tuple(sorted({path.split("/")[1] for path in governed}))
    if from_tree != plugins:
        raise TopologyError(
            "manifest-disagreement",
            "the manifests and the tree derive different plugin sets",
            {
                "manifest-only": sorted(set(plugins) - set(from_tree)),
                "tree-only": sorted(set(from_tree) - set(plugins)),
            },
        )

    by_skill_id: dict[str, str] = {}
    for path in governed:
        skill_id = path.rsplit("/", 1)[-1]
        previous = by_skill_id.get(skill_id)
        if previous is not None:
            raise TopologyError(
                "duplicate-skill-id",
                "the tree declares the same governed skill id twice",
                {"first": previous, "second": path},
            )
        by_skill_id[skill_id] = path

    canonical: list[str] = []
    for plugin in plugins:
        entry = phase_host_entry if plugin == phase_host else plugin
        want = f"{PLUGIN_ROOT}/{plugin}/{SKILLS_DIRECTORY}/{entry}"
        if want not in governed:
            raise TopologyError(
                "missing-canonical-skill",
                "a plugin has no governed canonical entry skill",
                want,
            )
        canonical.append(want)

    phase = tuple(sorted(set(governed) - set(canonical)))
    outside = sorted(path for path in phase if path.split("/")[1] != phase_host)
    if outside:
        raise TopologyError(
            "phase-outside-host",
            f"a phase skill sits outside {phase_host}",
            outside,
        )

    return Topology(
        plugins=plugins,
        governed=governed,
        canonical=tuple(sorted(canonical)),
        phase=phase,
        phase_host=phase_host,
        phase_host_entry=phase_host_entry,
    )


def _format(topology: Topology) -> Iterable[str]:
    counts = topology.counts()
    yield (
        f"{counts['plugins']} plugins, {counts['governed']} governed skills, "
        f"{counts['canonical']} canonical, {counts['phase']} phase"
    )
    yield "phase skills: " + ", ".join(topology.phase_ids)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Derive the repository topology.")
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="repository root to read"
    )
    parser.add_argument(
        "--json", action="store_true", help="print the derived topology as JSON"
    )
    args = parser.parse_args(argv)
    try:
        topology = read(args.root)
    except TopologyError as exc:
        print(str(exc))
        return 1
    if args.json:
        print(
            json.dumps(
                {
                    "counts": topology.counts(),
                    "plugins": list(topology.plugins),
                    "governed": list(topology.governed),
                    "canonical": list(topology.canonical),
                    "phase": list(topology.phase),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        for line in _format(topology):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
