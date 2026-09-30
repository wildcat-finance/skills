#!/usr/bin/env python3
"""Print the Alexandria version floor every ref claims, and hold the working tree above it.

Run from anywhere inside the run worktree, immediately before a push:

    python3 .hexaemeron/design/version_floor.py

The floor is the highest `version` in `plugins/alexandria/.claude-plugin/plugin.json`
that `main` or any local or `origin` branch claims, read from each ref's
committed bytes. A branch whose tip `HEAD` already contains is this branch's
own history, and a branch that already contains `HEAD` is its own stacked audit
branch or a later step; both are left out, so neither raises this branch's own
floor. `main` and `origin/main` always count.

The four surfaces a rise touches must agree: both plugin manifests, the
Alexandria entry in `.claude-plugin/marketplace.json` and the pin in
`tests/test_version_propagation.py`. The script exits 0 only when they do and
their version sits above the floor, 1 otherwise, and 2 when git or a surface
cannot be read. It reads git objects and working files and writes nothing.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
MANIFEST = "plugins/alexandria/.claude-plugin/plugin.json"
CODEX = "plugins/alexandria/.codex-plugin/plugin.json"
MARKETPLACE = ".claude-plugin/marketplace.json"
PIN = "tests/test_version_propagation.py"
VERSION = re.compile(r"(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\Z")
ALWAYS = ("refs/heads/main", "refs/remotes/origin/main")


class Refusal(Exception):
    pass


def git(root: Path, *argv: str, data: bytes | None = None) -> bytes:
    home = tempfile.mkdtemp(prefix="fiat-1891-version-floor-")
    try:
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith("GIT_")}
        environment.update(HOME=home, XDG_CONFIG_HOME=home, GIT_CONFIG_NOSYSTEM="1",
                           GIT_CONFIG_GLOBAL=os.devnull, LC_ALL="C")
        try:
            result = subprocess.run(  # phylax: allow subprocess: fixed git argv, no shell
                ["git", "-c", "color.ui=never", "-C", str(root), *argv], input=data,
                capture_output=True, timeout=120, env=environment, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise Refusal(f"git {argv[0]} could not run: {type(error).__name__}") from None
    finally:
        shutil.rmtree(home, ignore_errors=True)
    if result.returncode != 0:
        raise Refusal(f"git {argv[0]} failed: "
                      + result.stderr.decode("utf-8", "replace").strip()[:200])
    return result.stdout


def parse(value, label: str) -> tuple:
    if not isinstance(value, str) or VERSION.fullmatch(value) is None:
        raise Refusal(f"{label} is not a version")
    return tuple(int(part) for part in value.split("."))


def text(version: tuple) -> str:
    return ".".join(str(part) for part in version)


def claims(root: Path) -> list:
    """(version, ref) for main and every local and origin branch HEAD does not contain."""
    listed = git(root, "for-each-ref", "--format=%(refname)", "refs/heads",
                 "refs/remotes/origin").decode("utf-8").split()
    outside = set(git(root, "for-each-ref", "--no-merged=HEAD", "--format=%(refname)",
                      "refs/heads", "refs/remotes/origin").decode("utf-8").split())
    descendants = set(git(root, "for-each-ref", "--contains", "HEAD", "--format=%(refname)",
                          "refs/heads", "refs/remotes/origin").decode("utf-8").split())
    refs = [ref for ref in listed if (ref in ALWAYS or (ref in outside and ref not in descendants))
            and not ref.endswith("/HEAD")]
    if not refs:
        return []
    batch = "".join(f"{ref}:{MANIFEST}\n" for ref in refs).encode("utf-8")
    output = git(root, "cat-file", "--batch", data=batch)
    found, position = [], 0
    for ref in refs:
        end = output.index(b"\n", position)
        header = output[position:end].decode("utf-8", "replace")
        position = end + 1
        if header.endswith(" missing"):
            continue
        size = int(header.rsplit(" ", 1)[1])
        body = output[position:position + size]
        position += size + 1
        try:
            value = json.loads(body)["version"]
            found.append((parse(value, f"{ref}:{MANIFEST}"), ref))
        except (ValueError, KeyError, TypeError, Refusal):
            continue
    return found


def surfaces(root: Path) -> dict:
    values = {}
    for path in (MANIFEST, CODEX):
        values[path] = json.loads((root / path).read_text(encoding="utf-8")).get("version")
    marketplace = json.loads((root / MARKETPLACE).read_text(encoding="utf-8"))
    values[MARKETPLACE] = next((entry.get("version") for entry in marketplace.get("plugins", [])
                                if entry.get("name") == "alexandria"), None)
    pin = None
    for node in ast.walk(ast.parse((root / PIN).read_text(encoding="utf-8"))):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (isinstance(key, ast.Constant) and key.value == "alexandria"
                        and isinstance(value, ast.Constant)):
                    pin = value.value
    values[PIN] = pin
    return values


def main() -> int:
    try:
        root = Path(git(HERE, "rev-parse", "--show-toplevel").decode("utf-8").strip())
        found = claims(root)
        if not found:
            raise Refusal("no ref claims an Alexandria version")
        floor, ref = max(found)
        current = surfaces(root)
        parsed = {path: parse(value, path) for path, value in current.items()}
    except (Refusal, OSError, ValueError) as error:
        print(f"version-floor: {error}", file=sys.stderr)
        return 2
    print(f"floor {text(floor)} claimed by {ref} ({len(found)} refs read)")
    for path, version in parsed.items():
        print(f"{path} {text(version)}")
    versions = set(parsed.values())
    if len(versions) != 1:
        print("version-floor: the four surfaces disagree", file=sys.stderr)
        return 1
    version = versions.pop()
    if version <= floor:
        print(f"version-floor: {text(version)} does not sit above the floor {text(floor)}",
              file=sys.stderr)
        return 1
    print(f"above the floor: {text(version)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
