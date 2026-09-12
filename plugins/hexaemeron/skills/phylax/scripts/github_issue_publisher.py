#!/usr/bin/env python3
"""Credential-free Step 1 entrypoint for the bounded GitHub issue publisher.

The only available operation checks the code-owned admission fixtures and
emits one selected-candidate Protasis conformance report. Socket, signer,
transport, and publication commands arrive only in their receipted later
steps.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
import stat

from github_issue_publisher_lib import (
    MAX_JSON_MEMBERS,
    MAX_REQUEST_BYTES,
    PublisherError,
    admit_request,
    candidate_sha256,
    canonical_json,
    parse_json_bytes,
    read_bounded_file,
    sha256_bytes,
)


MANIFEST_PATH = (
    "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1/manifest.json"
)
MANIFEST_SCHEMA = "github-issue-publisher-admission-manifest/v1"
SELECTED_CANDIDATE = "isolated-publisher"
FIXTURE_NAMES = (
    "issue-855-body.txt",
    "issue-855-source.json",
    "issue-855-title.txt",
    "queue-cases.json",
    "rejection-cases.json",
    "valid-request.json",
)
CRITERIA = {
    "ordered-admission-chain": (True, "boolean"),
    "request-work-bound": (MAX_JSON_MEMBERS, "count"),
    "request-byte-bound": (MAX_REQUEST_BYTES, "bytes"),
}
CLI_PREFIX = "python3 plugins/hexaemeron/skills/phylax/scripts/github_issue_publisher.py"


def _refuse(field: str) -> None:
    raise PublisherError("GIP199", field)


def _canonical_fixture(raw: bytes, field: str) -> dict[str, object]:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        _refuse(field)
    try:
        return parse_json_bytes(raw[:-1])
    except PublisherError as exc:
        raise PublisherError("GIP199", field) from exc


def _closed_manifest(raw: bytes) -> dict[str, str]:
    document = _canonical_fixture(raw, "conformance.manifest")
    if set(document) != {"schema", "files"} or document.get("schema") != MANIFEST_SCHEMA:
        _refuse("conformance.manifest")
    rows = document.get("files")
    if not isinstance(rows, list) or len(rows) != len(FIXTURE_NAMES):
        _refuse("conformance.manifest")
    files: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            _refuse("conformance.manifest")
        name = row.get("path")
        digest = row.get("sha256")
        if (
            not isinstance(name, str)
            or name not in FIXTURE_NAMES
            or name in files
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            _refuse("conformance.manifest")
        files[name] = digest
    if tuple(sorted(files)) != FIXTURE_NAMES:
        _refuse("conformance.manifest")
    return files


def _fixture_bytes(root: Path, files: dict[str, str]) -> dict[str, bytes]:
    fixtures: dict[str, bytes] = {}
    for name in FIXTURE_NAMES:
        try:
            raw = read_bounded_file(root / name)
        except PublisherError as exc:
            raise PublisherError("GIP199", "conformance.fixture") from exc
        if sha256_bytes(raw) != files[name]:
            _refuse("conformance.fixture")
        fixtures[name] = raw
    return fixtures


def _verify_fixture_contract(fixtures: dict[str, bytes]) -> None:
    valid = fixtures["valid-request.json"]
    if not valid.endswith(b"\n") or valid.endswith(b"\n\n"):
        _refuse("conformance.valid-request")
    try:
        admission = admit_request(valid[:-1])
    except PublisherError as exc:
        raise PublisherError("GIP199", "conformance.valid-request") from exc
    if (
        admission.mint_attempts != 0
        or admission.post_attempts != 0
        or admission.gate_versions != ("0.3.0", "2.3.0", "1.1.0", "2.3.0")
    ):
        _refuse("conformance.valid-request")

    queue_cases = _canonical_fixture(
        fixtures["queue-cases.json"], "conformance.queue-cases"
    )
    expected_queues = {
        ("held-job", "phylax-next", "", ("held-job", "origin:ai")),
        ("wish", "phylax-7", "", ("origin:ai", "wish")),
        ("skill-wish", "phylax-wish", "", ("origin:ai",)),
        (
            "observation",
            "framework-56",
            "Protasis decides which skill or skills this observation upgrades.",
            ("observation", "origin:ai"),
        ),
    }
    rows = queue_cases.get("cases")
    if (
        set(queue_cases) != {"schema", "cases"}
        or queue_cases.get("schema") != "github-issue-publisher-queue-cases/v1"
        or not isinstance(rows, list)
        or len(rows) != 4
    ):
        _refuse("conformance.queue-cases")
    observed_queues: set[tuple[str, str, str, tuple[str, ...]]] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "queue",
            "prefix",
            "body_opening",
            "labels",
        }:
            _refuse("conformance.queue-cases")
        labels = row.get("labels")
        if not isinstance(labels, list) or any(not isinstance(item, str) for item in labels):
            _refuse("conformance.queue-cases")
        values = (row.get("queue"), row.get("prefix"), row.get("body_opening"))
        if any(not isinstance(item, str) for item in values):
            _refuse("conformance.queue-cases")
        observed_queues.add((values[0], values[1], values[2], tuple(labels)))
    if observed_queues != expected_queues:
        _refuse("conformance.queue-cases")

    rejection_cases = _canonical_fixture(
        fixtures["rejection-cases.json"], "conformance.rejection-cases"
    )
    expected_rejections = {
        ("issue-855-missing-framework-opening", "GIP130"),
        ("missing-gate", "GIP150"),
        ("failed-gate", "GIP150"),
        ("reordered-gate", "GIP150"),
        ("gate-subject-mismatch", "GIP150"),
        ("imprimatur-defect", "GIP151"),
        ("authority-subject-mismatch", "GIP160"),
    }
    rejection_rows = rejection_cases.get("cases")
    if (
        set(rejection_cases) != {"schema", "cases"}
        or rejection_cases.get("schema")
        != "github-issue-publisher-rejection-cases/v1"
        or not isinstance(rejection_rows, list)
        or {
            (row.get("id"), row.get("code"))
            for row in rejection_rows
            if isinstance(row, dict) and set(row) == {"id", "code"}
        }
        != expected_rejections
        or len(rejection_rows) != len(expected_rejections)
    ):
        _refuse("conformance.rejection-cases")

    source = _canonical_fixture(
        fixtures["issue-855-source.json"], "conformance.issue-855"
    )
    if set(source) != {
        "schema",
        "author",
        "created_at",
        "html_url",
        "title_sha256",
        "body_sha256",
        "candidate_sha256",
    } or (
        source.get("schema") != "github-issue-source-fixture/v1"
        or source.get("author") != "shoggoth-wildcat-labs[bot]"
        or source.get("created_at") != "2026-08-29T22:50:49Z"
        or source.get("html_url")
        != "https://github.com/wildcat-finance/skills/issues/855"
    ):
        _refuse("conformance.issue-855")
    try:
        title_raw = fixtures["issue-855-title.txt"]
        if not title_raw.endswith(b"\n") or title_raw.endswith(b"\n\n"):
            _refuse("conformance.issue-855")
        title = title_raw[:-1].decode("utf-8")
        body = fixtures["issue-855-body.txt"].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PublisherError("GIP199", "conformance.issue-855") from exc
    if (
        source.get("title_sha256") != sha256_bytes(title.encode("utf-8"))
        or source.get("body_sha256") != sha256_bytes(body.encode("utf-8"))
        or source.get("candidate_sha256") != candidate_sha256(title, body)
        or not title.startswith("framework-51: ")
        or body.startswith(
            "Protasis decides which skill or skills this observation upgrades."
        )
    ):
        _refuse("conformance.issue-855")


def _report_path(candidate: str, criterion: str) -> str:
    return f".hexaemeron/design-reports/{candidate}-{criterion}.json"


def _write_report(relative: str, payload: bytes) -> None:
    destination = Path(relative)
    parent = destination.parent
    try:
        parent_stat = parent.lstat()
        if not stat.S_ISDIR(parent_stat.st_mode) or stat.S_ISLNK(parent_stat.st_mode):
            _refuse("conformance.report")
        descriptor = os.open(
            parent,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except (OSError, PublisherError) as exc:
        raise PublisherError("GIP199", "conformance.report") from exc
    temporary = f".{destination.name}.tmp-{os.getpid()}"
    output = -1
    try:
        try:
            existing = os.stat(destination.name, dir_fd=descriptor, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and (
            not stat.S_ISREG(existing.st_mode) or existing.st_nlink != 1
        ):
            _refuse("conformance.report")
        output = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=descriptor,
        )
        written = 0
        while written < len(payload):
            written += os.write(output, payload[written:])
        os.fsync(output)
        os.close(output)
        output = -1
        os.replace(
            temporary,
            destination.name,
            src_dir_fd=descriptor,
            dst_dir_fd=descriptor,
        )
        os.fsync(descriptor)
    except (OSError, PublisherError) as exc:
        try:
            os.unlink(temporary, dir_fd=descriptor)
        except OSError:
            pass
        if isinstance(exc, PublisherError):
            raise
        raise PublisherError("GIP199", "conformance.report") from exc
    finally:
        if output >= 0:
            os.close(output)
        os.close(descriptor)


def _conformance(argv: list[str]) -> int:
    if len(argv) != 9 or argv[0] != "conformance" or argv[1] != "--manifest":
        _refuse("cli.arguments")
    if argv[3] != "--design-candidate" or argv[5] != "--design-criterion":
        _refuse("cli.arguments")
    if argv[7] != "--design-report":
        _refuse("cli.arguments")
    manifest, candidate, criterion, report_path = argv[2], argv[4], argv[6], argv[8]
    if (
        manifest != MANIFEST_PATH
        or candidate != SELECTED_CANDIDATE
        or criterion not in CRITERIA
        or report_path != _report_path(candidate, criterion)
    ):
        _refuse("cli.arguments")
    try:
        manifest_raw = read_bounded_file(manifest)
    except PublisherError as exc:
        raise PublisherError("GIP199", "conformance.manifest") from exc
    files = _closed_manifest(manifest_raw)
    fixtures = _fixture_bytes(Path(manifest).parent, files)
    _verify_fixture_contract(fixtures)
    value, unit = CRITERIA[criterion]
    command = (
        f"{CLI_PREFIX} conformance --manifest {manifest} "
        f"--design-candidate {candidate} --design-criterion {criterion} "
        f"--design-report {report_path}"
    )
    report = {
        "schema": "protasis-design-report/v1",
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": command,
        "exit": 0,
    }
    payload = canonical_json(report) + b"\n"
    _write_report(report_path, payload)
    sys.stdout.buffer.write(payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    try:
        return _conformance(arguments)
    except PublisherError as exc:
        sys.stderr.buffer.write(canonical_json(exc.diagnostic()) + b"\n")
        return 2
    except Exception:
        diagnostic = PublisherError("GIP199", "cli.internal").diagnostic()
        sys.stderr.buffer.write(canonical_json(diagnostic) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
