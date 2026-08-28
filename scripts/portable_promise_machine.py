#!/usr/bin/env python3
"""Build and check the dependency-closed Promise Machine skill payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile


CONTRACT_ID = "promise-machine/v1"
MANIFEST_SCHEMA = "promise-machine-portable-runtime/v1"
GENERATOR = "scripts/portable_promise_machine.py"
TARGET = Path(".agents/skills/promise-machine/runtime")
PORTABLE_BOUNDARY = ".horos/boundary.json"

ROOT_FILES = (
    Path(".python-version"),
    Path(".agents/skills/promise-machine/SKILL.md"),
    Path("AGENTS.md"),
    Path("LICENSE"),
    Path("PROMISE_MACHINE.md"),
    Path("SHOGGOTH.md"),
    Path("assets/characters/promise-machine.png"),
    Path("pyproject.toml"),
    Path("repo_contract.py"),
    Path("schemas/promise-machine-run-observation-capture-v1.schema.json"),
    Path("schemas/promise-machine-run-observation-v1.schema.json"),
    Path("scripts/promise_machine.py"),
    Path("scripts/python"),
    Path("scripts/run_observation.py"),
    Path("scripts/run_observation_capture.py"),
    Path("docs/decisions/ADR-009-four-issue-queues-and-their-titles.md"),
    Path("docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md"),
    Path("docs/decisions/ADR-023-store-kronos-working-state-on-a-dedicated-git-ref.md"),
    Path("docs/fiat-run-observation-binding-v1.md"),
)

OMISSIONS = (
    {
        "pattern": "plugins/*/.claude-plugin/**",
        "reason": "host discovery manifests are not part of the portable runtime",
    },
    {
        "pattern": "plugins/*/.codex-plugin/**",
        "reason": "host discovery manifests are not part of the portable runtime",
    },
    {
        "pattern": "plugins/*/audit/**",
        "reason": "historical audit records remain in the full source checkout",
    },
    {
        "pattern": "plugins/*/tests/**",
        "reason": "development suites remain in the full source checkout",
    },
    {
        "pattern": "plugins/alexandria/examples/compound-v3-phase0-v0/input/**",
        "reason": "the large offline trace inputs remain in the full source checkout",
    },
    {
        "pattern": "plugins/alexandria/examples/compound-v3-phase0-v0/release/**",
        "reason": "the built offline trace release remains in the full source checkout",
    },
    {
        "pattern": "plugins/alexandria/examples/compound-v3-phase0-v0/source/**",
        "reason": "the offline trace release sources remain in the full source checkout",
    },
)


class PackageError(RuntimeError):
    """A deterministic package boundary or byte check failed."""


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
        "GIT_INTERNAL_SUPER_PREFIX",
    ):
        environment.pop(name, None)
    return environment


def _tracked_plugin_files(root: Path) -> list[Path]:
    result = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ["git", "-C", str(root), "ls-files", "-z", "--", "plugins"],
        check=False,
        capture_output=True,
        env=_git_environment(),
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PackageError(f"git could not enumerate the plugin sources: {detail}")
    return [Path(raw.decode("utf-8")) for raw in result.stdout.split(b"\0") if raw]


def _omitted(relative: Path) -> bool:
    parts = relative.parts
    if len(parts) < 3 or parts[0] != "plugins":
        return False
    if parts[2] in {".claude-plugin", ".codex-plugin", "audit", "tests"}:
        return True
    example = parts[:4] == (
        "plugins",
        "alexandria",
        "examples",
        "compound-v3-phase0-v0",
    )
    return example and len(parts) >= 5 and parts[4] in {"input", "release", "source"}


def source_files(root: Path) -> list[Path]:
    """Return the exact canonical files copied into the portable runtime."""
    selected = set(ROOT_FILES)
    selected.update(path for path in _tracked_plugin_files(root) if not _omitted(path))
    ordered = sorted(selected, key=lambda path: path.as_posix())
    for relative in ordered:
        if relative.is_absolute() or ".." in relative.parts:
            raise PackageError(f"unsafe source path: {relative}")
        source = root / relative
        if source.is_symlink() or not source.is_file():
            raise PackageError(f"portable source is absent or not a regular file: {relative}")
    return ordered


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _render_portable_boundary(root: Path, payload: dict[str, bytes]) -> bytes:
    """Scan the install-shaped tree, including a non-classifying manifest slot."""
    horos = root / "plugins/horos/skills/horos/scripts/horos.py"
    with tempfile.TemporaryDirectory(prefix="promise-machine-boundary.") as raw:
        candidate = Path(raw)
        for relative, data in payload.items():
            destination = candidate / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        (candidate / "MANIFEST.json").write_text("{}\n", encoding="utf-8")
        result = subprocess.run(  # phylax: allow subprocess: fixed local Horos argv, no shell
            [sys.executable, str(horos), "scan", str(candidate), "--json"],
            check=False,
            capture_output=True,
            env=_git_environment(),
        )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PackageError(f"Horos could not build the portable boundary: {detail}")
    try:
        document = json.loads(result.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise PackageError(f"Horos returned an invalid portable boundary: {error}") from error
    if document.get("universe") != "filesystem":
        raise PackageError("portable Horos scan did not use its isolated filesystem")
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def expected_files(root: Path) -> tuple[dict[str, bytes], bytes]:
    """Return payload bytes and the deterministic manifest bytes."""
    payload: dict[str, bytes] = {}
    rows = []
    total_bytes = 0
    for relative in source_files(root):
        data = (root / relative).read_bytes()
        name = relative.as_posix()
        payload[name] = data
        total_bytes += len(data)
        rows.append(
            {
                "bytes": len(data),
                "path": name,
                "sha256": _digest(data),
                "source": name,
            }
        )
    boundary = _render_portable_boundary(root, payload)
    payload[PORTABLE_BOUNDARY] = boundary
    total_bytes += len(boundary)
    rows.append(
        {
            "bytes": len(boundary),
            "generated_by": "plugins/horos/skills/horos/scripts/horos.py",
            "path": PORTABLE_BOUNDARY,
            "sha256": _digest(boundary),
            "source": None,
        }
    )
    rows.sort(key=lambda row: row["path"])
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "contract": CONTRACT_ID,
        "generated_by": GENERATOR,
        "file_count": len(rows),
        "total_bytes": total_bytes,
        "omissions": list(OMISSIONS),
        "files": rows,
    }
    encoded = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return payload, encoded


def _actual_files(target: Path) -> dict[str, bytes]:
    if target.is_symlink() or not target.is_dir():
        raise PackageError(f"portable runtime is absent or not a directory: {target}")
    actual = {}
    for path in sorted(target.rglob("*")):
        if path.is_symlink():
            raise PackageError(f"portable runtime contains a symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(target).as_posix()
        if PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts:
            raise PackageError(f"unsafe portable runtime path: {relative}")
        actual[relative] = path.read_bytes()
    return actual


def check(root: Path) -> None:
    payload, manifest = expected_files(root)
    expected = dict(payload)
    expected["MANIFEST.json"] = manifest
    actual = _actual_files(root / TARGET)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    changed = sorted(path for path in set(expected) & set(actual) if expected[path] != actual[path])
    if missing or extra or changed:
        raise PackageError(
            "portable runtime drift: "
            f"missing={missing!r} extra={extra!r} changed={changed!r}; "
            f"run ./scripts/python {GENERATOR} sync"
        )


def sync(root: Path) -> None:
    payload, manifest = expected_files(root)
    target = root / TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".promise-machine-runtime.", dir=target.parent) as raw:
        candidate = Path(raw) / "runtime"
        candidate.mkdir()
        for relative, data in payload.items():
            destination = candidate / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            source_mode = (root / relative).stat().st_mode & 0o777
            destination.chmod(source_mode)
        (candidate / "MANIFEST.json").write_bytes(manifest)
        if target.exists():
            if target.is_symlink() or not target.is_dir():
                raise PackageError(f"refusing to replace non-directory target: {target}")
            shutil.rmtree(target)
        candidate.replace(target)
    check(root)


def repository_root(raw: str | None) -> Path:
    root = Path(raw) if raw else Path(__file__).resolve().parents[1]
    root = root.resolve()
    if not (root / "PROMISE_MACHINE.md").is_file() or not (root / ".git").exists():
        raise PackageError(f"not a Wildcat Skills checkout: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "sync"))
    parser.add_argument("--root", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
        if args.action == "sync":
            sync(root)
            print(f"synchronised {TARGET.as_posix()}")
        else:
            check(root)
            print(f"checked {TARGET.as_posix()}")
    except PackageError as error:
        parser.exit(1, f"portable Promise Machine: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
