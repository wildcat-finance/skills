#!/usr/bin/env python3
"""Verify the installed Promise Machine runtime against its byte manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys


SCHEMA = "promise-machine-portable-runtime/v1"
CONTRACT = "promise-machine/v1"


def fail(message: str) -> int:
    print(f"Promise Machine runtime verification failed: {message}", file=sys.stderr)
    return 1


def main() -> int:
    runtime = (Path(__file__).resolve().parent.parent / "runtime").resolve()
    manifest_path = runtime / "MANIFEST.json"
    if manifest_path.is_symlink():
        return fail("MANIFEST.json must not be a symlink")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return fail(f"cannot read MANIFEST.json: {error}")
    if manifest.get("schema") != SCHEMA or manifest.get("contract") != CONTRACT:
        return fail("manifest identity is absent or unsupported")
    rows = manifest.get("files")
    if not isinstance(rows, list) or manifest.get("file_count") != len(rows):
        return fail("manifest file count does not match its rows")

    expected = {"MANIFEST.json"}
    total = 0
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return fail("manifest contains a non-object file row")
        relative = row.get("path")
        if not isinstance(relative, str):
            return fail("manifest contains a file row without a path")
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or relative in seen:
            return fail(f"manifest contains an unsafe or repeated path: {relative!r}")
        seen.add(relative)
        expected.add(relative)
        target = runtime.joinpath(*path.parts)
        current = runtime
        for part in path.parts:
            current /= part
            if current.is_symlink():
                return fail(f"required path crosses a symlink: {relative}")
        if target.is_symlink() or not target.is_file():
            return fail(f"required file is absent or not regular: {relative}")
        data = target.read_bytes()
        if row.get("bytes") != len(data):
            return fail(f"byte count differs: {relative}")
        if row.get("sha256") != hashlib.sha256(data).hexdigest():
            return fail(f"digest differs: {relative}")
        total += len(data)
    if manifest.get("total_bytes") != total:
        return fail("manifest total byte count differs")

    actual = {
        path.relative_to(runtime).as_posix()
        for path in runtime.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if actual != expected:
        return fail(
            f"runtime file set differs: missing={sorted(expected - actual)!r} "
            f"extra={sorted(actual - expected)!r}"
        )

    law = (runtime / "PROMISE_MACHINE.md").read_bytes()
    for copy in sorted((runtime / "plugins").glob("*/PROMISE_MACHINE.md")):
        if copy.read_bytes() != law:
            return fail(f"installation law copy differs: {copy.relative_to(runtime)}")
    print(f"verified {len(rows)} files for {CONTRACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
