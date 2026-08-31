#!/usr/bin/env python3
"""Verify selected vendored overlay bytes at their immutable upstream commits."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import http.client
import json
from pathlib import Path
import ssl
import tempfile
import time

if __package__:
    from . import promise_machine
else:
    import promise_machine


SCHEMA = "promise-machine-upstream-verification/v1"
RAW_HOST = "raw.githubusercontent.com"
MAX_UPSTREAM_BYTES = 256 * 1024
CHUNK_BYTES = 32 * 1024
CONNECT_TIMEOUT_SECONDS = 5.0
TOTAL_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class VerificationFinding:
    code: str
    path: str
    message: str
    remedy: str


def _failure(code, path, message, remedy):
    return VerificationFinding(code, path, message, remedy)


def _overlay_declarations(root: Path):
    inventory, inventory_findings = promise_machine.discover_inventory(root)
    _, overlay_findings = promise_machine.check_overlays(root, inventory)
    core_findings = inventory_findings + overlay_findings
    if core_findings:
        return {}, [
            _failure(item.code, item.path, item.message, item.remedy)
            for item in core_findings
        ]
    loaded, read_findings = promise_machine.read_markdown(
        root / promise_machine.OVERLAY_PATH,
        root,
        missing_code="PV002",
        unsafe_code="PV002",
    )
    if loaded is None:
        return {}, [
            _failure(item.code, item.path, item.message, item.remedy)
            for item in read_findings
        ]
    declarations = {}
    for promise_id, fields in promise_machine.declaration_field_blocks(
        loaded[1], promise_machine.OVERLAY_HEADING
    ):
        local_path = fields["Path"][0].strip("`")
        declarations[local_path] = {
            "promise_id": promise_id,
            "repository": fields["Repository"][0].strip("`"),
            "commit": fields["Commit"][0].strip("`"),
            "upstream_path": fields["Upstream path"][0].strip("`"),
            "upstream_sha256": fields["Upstream SHA-256"][0].strip("`"),
            "local_sha256": fields["Local SHA-256"][0].strip("`"),
        }
    return declarations, []


def _repository_parts(repository: str):
    if promise_machine.GITHUB_REPOSITORY_URI.fullmatch(repository) is None:
        raise ValueError("repository is outside the HTTPS GitHub allowlist")
    slug = repository.removeprefix("https://github.com/").removesuffix(".git")
    owner, name = slug.split("/", 1)
    return owner, name


def _bounded_fetch(
    declaration,
    destination: Path,
    *,
    connection_factory,
    context,
    deadline,
    clock,
):
    owner, repository = _repository_parts(declaration["repository"])
    commit = declaration["commit"]
    upstream_path = declaration["upstream_path"]
    request_target = f"/{owner}/{repository}/{commit}/{upstream_path}"
    remaining = deadline - clock()
    if remaining <= 0:
        raise TimeoutError("total verification deadline expired before connection")
    connection = connection_factory(
        RAW_HOST,
        timeout=min(CONNECT_TIMEOUT_SECONDS, remaining),
        context=context,
    )
    try:
        connection.request(
            "GET",
            request_target,
            headers={
                "Accept": "application/octet-stream",
                "User-Agent": "wildcat-promise-machine-provenance/1",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            if 300 <= response.status <= 399:
                raise ValueError(
                    f"redirect status {response.status} refused without following it"
                )
            raise ValueError(f"upstream returned HTTP status {response.status}")
        content_length = response.getheader("Content-Length")
        if content_length is not None:
            if not content_length.isdigit():
                raise ValueError("upstream Content-Length is malformed")
            if int(content_length) > MAX_UPSTREAM_BYTES:
                raise ValueError(
                    f"upstream Content-Length exceeds {MAX_UPSTREAM_BYTES} bytes"
                )

        digest = hashlib.sha256()
        total = 0
        with destination.open("xb") as handle:
            while True:
                remaining = deadline - clock()
                if remaining <= 0:
                    raise TimeoutError("total verification deadline expired while reading")
                connection_socket = getattr(connection, "sock", None)
                if connection_socket is not None:
                    connection_socket.settimeout(
                        max(0.001, min(CONNECT_TIMEOUT_SECONDS, remaining))
                    )
                chunk = response.read(
                    min(CHUNK_BYTES, MAX_UPSTREAM_BYTES + 1 - total)
                )
                if not isinstance(chunk, bytes):
                    raise ValueError("upstream response returned non-byte content")
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPSTREAM_BYTES:
                    raise ValueError(
                        f"upstream response exceeds {MAX_UPSTREAM_BYTES} bytes"
                    )
                digest.update(chunk)
                handle.write(chunk)
        return total, digest.hexdigest()
    finally:
        connection.close()


def verify_selected(
    root,
    selected_paths,
    *,
    connection_factory=http.client.HTTPSConnection,
    clock=time.monotonic,
):
    root = Path(root).resolve(strict=True)
    selected = list(selected_paths)
    if (
        not selected
        or len(set(selected)) != len(selected)
        or any(not isinstance(path, str) or not path for path in selected)
    ):
        return [], [
            _failure(
                "PV001",
                promise_machine.OVERLAY_PATH.as_posix(),
                "upstream verification selection must contain unique explicit local paths",
                "pass each affected declared vendored path exactly once",
            )
        ]

    declarations, findings = _overlay_declarations(root)
    if findings:
        return [], findings
    undeclared = sorted(set(selected) - set(declarations))
    if undeclared:
        return [], [
            _failure(
                "PV001",
                promise_machine.OVERLAY_PATH.as_posix(),
                f"selected paths are not declared vendored overlays: {undeclared!r}",
                "select only affected local paths from the checked overlay",
            )
        ]

    verified = []
    deadline = clock() + TOTAL_TIMEOUT_SECONDS
    context = ssl.create_default_context()
    with tempfile.TemporaryDirectory(prefix="promise-machine-upstream.") as raw:
        temporary_root = Path(raw)
        for index, local_path in enumerate(selected):
            declaration = declarations[local_path]
            destination = temporary_root / f"upstream-{index:04d}.bin"
            try:
                byte_count, actual = _bounded_fetch(
                    declaration,
                    destination,
                    connection_factory=connection_factory,
                    context=context,
                    deadline=deadline,
                    clock=clock,
                )
            except (OSError, TimeoutError, ValueError, http.client.HTTPException) as exc:
                findings.append(
                    _failure(
                        "PV003",
                        local_path,
                        f"bounded upstream read failed: {exc}",
                        "repair the immutable upstream location or retry the selected path",
                    )
                )
                continue
            expected = declaration["upstream_sha256"]
            if actual != expected:
                findings.append(
                    _failure(
                        "PV004",
                        local_path,
                        f"upstream bytes digest is {actual}; overlay records {expected}",
                        "review the immutable upstream bytes and reconcile the overlay deliberately",
                    )
                )
                continue
            verified.append(
                {
                    "local_path": local_path,
                    "repository": declaration["repository"],
                    "commit": declaration["commit"],
                    "upstream_path": declaration["upstream_path"],
                    "upstream_sha256": actual,
                    "bytes": byte_count,
                    "publisher_authentication": "unknown",
                }
            )
    return verified, findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        action="append",
        required=True,
        help="affected local vendored SKILL.md path; repeat for each path",
    )
    parser.add_argument("--root", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = promise_machine.repository_root(args.root)
        verified, findings = verify_selected(root, args.path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    document = {
        "schema": SCHEMA,
        "ok": not findings,
        "verified": verified,
        "findings": [asdict(item) for item in findings],
    }
    if args.json:
        print(json.dumps(document, sort_keys=True, separators=(",", ":")))
    elif findings:
        for item in findings:
            print(
                f"{item.code} path={item.path}: {item.message}; repair: {item.remedy}"
            )
        print(f"refused: {len(findings)} finding(s)")
    else:
        print(f"clean: verified={len(verified)} publisher-authentication=unknown")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
