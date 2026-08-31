#!/usr/bin/env python3
"""Build and check the dependency-closed Promise Machine skill payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile


CONTRACT_ID = "promise-machine/v1"
MANIFEST_SCHEMA = "promise-machine-portable-runtime/v1"
GENERATOR = "scripts/portable_promise_machine.py"
TARGET = Path(".agents/skills/promise-machine/runtime")
PACKAGE_ROOT = Path(".agents/skills/promise-machine")
SKILLS_CONFIG = Path("skills.sh.json")

# The files the package carries that this repository authors rather than
# generates.  They stay at these paths here: repo_contract.py binds two of them
# by constant, and the Promise contract names the router inside a closed
# quotable set.  See ADR-054's successor.
PACKAGE_AUTHORED = (
    Path(".agents/plugins/marketplace.json"),
    Path(".agents/skills/promise-machine/SKILL.md"),
    Path(".agents/skills/promise-machine/PORTABLE.md"),
    Path(".agents/skills/promise-machine/scripts/verify_runtime.py"),
)
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
    Path("scripts/run_observation.py"),
    Path("scripts/run_observation_capture.py"),
    Path("docs/decisions/ADR-009-four-issue-queues-and-their-titles.md"),
    Path("docs/decisions/ADR-010-split-address-telemetry-from-boundary-control.md"),
    Path("docs/decisions/ADR-023-store-kronos-working-state-on-a-dedicated-git-ref.md"),
    Path("docs/decisions/ADR-046-use-a-job-scoped-model-proxy.md"),
    Path("docs/decisions/ADR-067-gate-a-run-on-what-its-issue-filed.md"),
    Path("docs/fiat-run-observation-binding-v1.md"),
)

PORTABLE_TEST_FILES = (
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/accepted-job.json"
    ),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/duplicate-field.json"
    ),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/excessive-depth.json"
    ),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/framing-cases.json"
    ),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/invalid-unicode.json"
    ),
    Path("plugins/hexaemeron/tests/fixtures/model-proxy-v1/jobspec.json"),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/lifecycle-cases.json"
    ),
    Path("plugins/hexaemeron/tests/fixtures/model-proxy-v1/manifest.json"),
    Path("plugins/hexaemeron/tests/fixtures/model-proxy-v1/policy.json"),
    Path("plugins/hexaemeron/tests/fixtures/model-proxy-v1/policy.sha256"),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/provider-cases.json"
    ),
    Path(
        "plugins/hexaemeron/tests/fixtures/model-proxy-v1/rejections.json"
    ),
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
        "exceptions": [path.as_posix() for path in PORTABLE_TEST_FILES],
        "reason": (
            "development suites and other fixtures remain in the full source "
            "checkout; the listed closed model-proxy-v1 fixture set closes the "
            "portable commands and vectors advertised by the copied reference"
        ),
    },
    {
        "pattern": "plugins/anamnesis/specimens/**",
        "reason": (
            "the preserved audit sources and the corpus release built from them are "
            "data the router never reads; they remain in the full source checkout, "
            "where the tests that rebuild and compare them run"
        ),
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
    if parts[:3] == ("plugins", "anamnesis", "specimens"):
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
    selected.update(PORTABLE_TEST_FILES)
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


# `import "p";`, `import "p" as N;`, `import {A} from "p";` and
# `import * as N from "p";` are all legal and all name a path. The trailing
# alias matters: without it the pattern skips the statement silently, and a
# check that exists to catch a lost import must not lose one to its own regex.
SOLIDITY_IMPORT = re.compile(
    r"""import\s+(?:[^;]*?\bfrom\s+)?["']([^"'\n]+)["']\s*"""
    r"""(?:as\s+[A-Za-z_$][A-Za-z0-9_$]*\s*)?;"""
)


def _resolve_relative(importer: str, target: str) -> str | None:
    """The tree-relative path a relative import names, or None if it escapes.

    Normalising and then asking whether the result left the tree is the control
    here, rather than refusing every `..` segment: 218 of the mirror's 265
    relative Solidity imports use one, so a rule that refused them would skip
    most of the surface and the check would pass by not looking.
    """
    if target.startswith("/"):
        return None
    parts: list[str] = []
    for segment in (PurePosixPath(importer).parent / target).parts:
        if segment == ".":
            continue
        if segment == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(segment)
    if not parts:
        return None
    return PurePosixPath(*parts).as_posix()


def import_closure_failures(root: Path, mirrored: dict[str, bytes]) -> list[str]:
    """Relative imports the mirror lost that the canonical source still resolves.

    The mirror's file set is built from the tracked sources, so a source that is
    not yet tracked never reaches it while the files importing it do. The result
    compiles in the checkout and not in the mirror, and comparing declared paths
    against digests cannot see it, because every file the manifest lists is
    byte-correct.

    Checked against the canonical tree rather than absolutely. A relative import
    that resolves in neither tree is a property of the source, not something
    mirroring broke; `plugins/horos/examples/fixture-sol/Market.sol` holds two of
    those and is meant to.
    """
    failures = []
    for name in sorted(mirrored):
        if not name.endswith(".sol"):
            continue
        text = mirrored[name].decode("utf-8", errors="replace")
        for target in SOLIDITY_IMPORT.findall(text):
            # Relative imports are the surface; a bare `@scope/...` or
            # remapped target is another tool's problem. A leading slash is
            # neither, and it is refused rather than skipped.
            if not target.startswith((".", "/")):
                continue
            resolved = _resolve_relative(name, target)
            if resolved is None:
                failures.append(
                    f"{name} imports {target}, which does not resolve inside the tree"
                )
                continue
            if resolved in mirrored:
                continue
            if (root / resolved).is_file():
                failures.append(
                    f"{name} imports {target}: {resolved} is in the source "
                    "and absent from the mirror"
                )
    return failures


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
            f"run python3 {GENERATOR} sync"
        )
    broken = import_closure_failures(root, actual)
    if broken:
        raise PackageError(
            "portable runtime is not import-closed: "
            + "; ".join(broken)
            + f"; run python3 {GENERATOR} sync after staging the missing source"
        )


def sync(root: Path) -> str:
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
    return stage_runtime(root)


def _git_work_tree(root: Path) -> bool:
    """True when git can answer for `root` and calls it a work tree."""
    try:
        result = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            check=False,
            capture_output=True,
            env=_git_environment(),
        )
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == b"true"


def _git_ignores(root: Path, relative: str) -> bool:
    """True when the repository's ignore rules cover `relative`.

    Asked before staging because `git add` treats an ignored pathspec as an
    error and exits 1. A repository that ignores its generated mirror is a
    reasonable thing to be; refusing to sync in one would regress the
    copy-mode install this script exists to serve.
    """
    try:
        result = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
            ["git", "-C", str(root), "check-ignore", "-q", "--", relative],
            check=False,
            capture_output=True,
            env=_git_environment(),
        )
    except OSError:
        return False
    return result.returncode == 0


def stage_runtime(root: Path) -> str:
    """Stage the mirror so the scan that runs next can see it.

    Horos builds its universe from `git ls-files`, which reads the index. A
    mirror written and left unstaged is therefore invisible to a scan that
    follows, and the boundary that scan writes describes the previous tree
    while `horos check` agrees with it. Staging here is what makes the
    documented sync-then-scan order correct rather than an alternation the
    caller has to know about.

    The pathspec is the mirror and nothing else, so regenerating a generated
    directory never stages an unrelated edit sitting in the working tree.
    `_git_environment()` strips the inherited git variables, so a
    GIT_INDEX_FILE belonging to another repository cannot redirect the write.
    """
    if not _git_work_tree(root):
        return "not a git work tree; mirror written but not staged"
    if _git_ignores(root, TARGET.as_posix()):
        return "mirror is ignored here; written but not staged"
    result = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ["git", "-C", str(root), "add", "--all", "--", TARGET.as_posix()],
        check=False,
        capture_output=True,
        env=_git_environment(),
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise PackageError(f"git could not stage the portable runtime: {detail}")
    return "staged"


def source_commit(root: Path) -> str:
    """Return the exact commit the package is generated from."""
    result = subprocess.run(  # phylax: allow subprocess: fixed local git argv, no shell
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        env=_git_environment(),
    )
    if result.returncode != 0:
        raise PackageError("could not read the source commit: " + result.stderr.strip())
    commit = result.stdout.strip()
    if len(commit) != 40 or not all(c in "0123456789abcdef" for c in commit):
        raise PackageError(f"source commit is not a full object name: {commit!r}")
    return commit


def _package_config() -> bytes:
    """The grouping the published package carries, independent of this tree."""
    document = {
        "$schema": "https://skills.sh/schemas/skills.sh.schema.json",
        "notGrouped": "bottom",
        "groupings": [
            {
                "title": "Install the Wildcat collective",
                "description": (
                    "The dependency-closed Promise Machine router verifies its "
                    "bundled runtime, selects one canonical specialist, and "
                    "preserves every evidence boundary and named hand-off."
                ),
                "skills": ["promise-machine"],
            }
        ],
    }
    return (json.dumps(document, indent=2) + "\n").encode("utf-8")


def _package_readme(commit: str) -> bytes:
    text = f"""# Wildcat skills runtime

Every file here is generated. Nothing in this repository is authored, and an
edit made here is overwritten by the next rebuild.

The source is [wildcat-finance/skills](https://github.com/wildcat-finance/skills).
This package was generated from commit `{commit}` by
`{GENERATOR}` in that repository.

## Install

```
npx skills add wildcat-finance/skills-runtime --skill promise-machine
```

Then verify the installed copy against its own manifest:

```
python3 .agents/skills/promise-machine/scripts/verify_runtime.py
```

## Rebuilding

A scheduled workflow in this repository clones the public source hourly,
regenerates the package, verifies it, and commits only when the bytes changed.
A failed verification publishes nothing and fails the run, so the last good
package stays published.

Changes belong upstream. Open issues and pull requests against
`wildcat-finance/skills`.
"""
    return text.encode("utf-8")


def _package_bytes(root: Path, commit: str) -> tuple[dict[str, bytes], dict[str, int]]:
    """Return every path the published package carries, keyed relative to it.

    The second mapping carries the permission bits of the entries that come
    from a file in `root`, keyed the same way.  A package key is not a source
    path -- the payload is republished under a prefix -- so a caller holding
    only the key cannot find the origin to read its mode from.  Both paths are
    in hand here, which is the only place the pairing can be recorded.
    """
    payload, manifest = expected_files(root)
    files: dict[str, bytes] = {}
    modes: dict[str, int] = {}
    for relative in PACKAGE_AUTHORED:
        source = root / relative
        if source.is_symlink() or not source.is_file():
            raise PackageError(f"authored package file is absent: {relative}")
        files[relative.as_posix()] = source.read_bytes()
        modes[relative.as_posix()] = source.stat().st_mode & 0o777
    runtime = PACKAGE_ROOT / "runtime"
    for relative, data in payload.items():
        key = (runtime / relative).as_posix()
        files[key] = data
        # A payload key is a path in `root`, except for the boundary this
        # generator renders itself; that one keeps the default mode.
        origin = root / relative
        if origin.is_file() and not origin.is_symlink():
            modes[key] = origin.stat().st_mode & 0o777
    files[(runtime / "MANIFEST.json").as_posix()] = manifest
    files[SKILLS_CONFIG.as_posix()] = _package_config()
    files["README.md"] = _package_readme(commit)
    return files, modes


# A directory this generator wrote carries its manifest at this path. Anything
# else that is not empty belongs to somebody, and writing a package replaces the
# whole directory, so an occupied destination is refused rather than cleared.
PACKAGE_MARKER = PACKAGE_ROOT / "runtime" / "MANIFEST.json"


def _checked_output(raw: str) -> Path:
    """Resolve the output directory, refusing a symlink, a bad parent, or work."""
    out = Path(raw)
    if out.is_symlink():
        raise PackageError(f"output directory is a symlink: {out}")
    resolved = out.resolve()
    parent = resolved.parent
    if not parent.is_dir():
        raise PackageError(f"output parent is not a directory: {parent}")
    if not resolved.exists():
        return resolved
    if not resolved.is_dir():
        raise PackageError(f"output path is not a directory: {resolved}")
    if not any(resolved.iterdir()):
        return resolved
    if not (resolved / PACKAGE_MARKER).is_file():
        raise PackageError(
            f"output directory is not empty and is not a generated package: {resolved}; "
            "remove it or name an empty directory"
        )
    return resolved


def package(root: Path, raw_out: str, commit: str | None) -> Path:
    """Write a complete installable package into a named directory."""
    out = _checked_output(raw_out)
    files, modes = _package_bytes(root, commit or source_commit(root))
    for relative in files:
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise PackageError(f"unsafe package path: {relative}")
    with tempfile.TemporaryDirectory(prefix=".promise-machine-package.", dir=out.parent) as raw:
        candidate = Path(raw) / "package"
        candidate.mkdir()
        for relative, data in sorted(files.items()):
            destination = candidate / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            mode = modes.get(relative)
            if mode is not None:
                destination.chmod(mode)
        if out.exists():
            shutil.rmtree(out)
        candidate.replace(out)
    return out


def repository_root(raw: str | None) -> Path:
    root = Path(raw) if raw else Path(__file__).resolve().parents[1]
    root = root.resolve()
    if not (root / "PROMISE_MACHINE.md").is_file() or not (root / ".git").exists():
        raise PackageError(f"not a Wildcat Skills checkout: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "sync", "package"))
    parser.add_argument("--out", help="directory to write a complete package into")
    parser.add_argument("--source-commit", help="exact source commit to record in the package")
    parser.add_argument("--root", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
        if args.action == "sync":
            status = sync(root)
            print(f"synchronised {TARGET.as_posix()} ({status})")
        elif args.action == "package":
            if not args.out:
                parser.exit(2, "portable Promise Machine: package needs --out\n")
            written = package(root, args.out, args.source_commit)
            print(f"packaged {written}")
        else:
            check(root)
            print(f"checked {TARGET.as_posix()}")
    except PackageError as error:
        parser.exit(1, f"portable Promise Machine: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
