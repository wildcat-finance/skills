#!/usr/bin/env python3
"""Credential-free Step 1 entrypoint for the bounded GitHub issue publisher.

The only available operation checks the code-owned admission fixtures and
emits one selected-candidate Protasis conformance report. Socket, signer,
transport, and publication commands arrive only in their receipted later
steps.
"""

from __future__ import annotations

from copy import deepcopy
import sys
import os
from pathlib import Path
import stat

from github_issue_publisher_lib import (
    FRAMEWORK_OPENING,
    MAX_JSON_MEMBERS,
    MAX_REQUEST_BYTES,
    MAX_STRING_BYTES,
    PublisherError,
    admit_request,
    candidate_sha256,
    canonical_json,
    frozen_sha256,
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
CARRYOVER_ROW = "none | none | This publication carries no work into another issue."


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


def _refresh_request(document: dict[str, object]) -> None:
    try:
        source = document["source"]
        shaped = document["sapheneia_candidate"]
        final = document["final_candidate"]
        frozen = document["frozen"]
        gates = document["gates"]
        authority = document["authority"]
        if not all(
            isinstance(value, dict) for value in (source, shaped, final, frozen, authority)
        ) or not isinstance(gates, list) or len(gates) != 4:
            _refuse("conformance.request-builder")
        source_digest = candidate_sha256(source["title"], source["body"])
        shaped_digest = candidate_sha256(shaped["title"], shaped["body"])
        final_digest = candidate_sha256(final["title"], final["body"])
        frozen_digest = frozen_sha256(frozen)
        gates[0].update(
            source_sha256=source_digest,
            candidate_sha256=shaped_digest,
            subject_sha256=shaped_digest,
            frozen_sha256=frozen_digest,
        )
        gates[1]["subject_sha256"] = shaped_digest
        gates[2].update(
            source_sha256=shaped_digest,
            candidate_sha256=final_digest,
            subject_sha256=final_digest,
            frozen_sha256=frozen_digest,
        )
        gates[3]["subject_sha256"] = final_digest
        authority["subject_sha256"] = final_digest
    except (KeyError, TypeError):
        _refuse("conformance.request-builder")


def _set_candidate(
    document: dict[str, object],
    *,
    title: str,
    body: str,
    prefix: str,
    opening: str,
    structure: list[str],
    inventory: list[str],
) -> None:
    for name in ("source", "sapheneia_candidate", "final_candidate"):
        candidate = document.get(name)
        if not isinstance(candidate, dict):
            _refuse("conformance.request-builder")
        candidate["title"] = title
        candidate["body"] = body
    frozen = document.get("frozen")
    if not isinstance(frozen, dict):
        _refuse("conformance.request-builder")
    frozen.update(
        title_prefix=prefix,
        body_opening=opening,
        host_structure=structure,
        protected_inventory=inventory,
    )
    _refresh_request(document)


def _queue_request(golden: dict[str, object], row: dict[str, object]) -> dict[str, object]:
    document = deepcopy(golden)
    queue = row["queue"]
    prefix = row["prefix"]
    opening = row["body_opening"]
    labels = row["labels"]
    if not all(isinstance(value, str) for value in (queue, prefix, opening)):
        _refuse("conformance.queue-cases")
    if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
        _refuse("conformance.queue-cases")
    prose = "## Status\n\nThe publisher checks exact bytes before it asks for a credential."
    sections = [prose, "Fiat-Required: 1", f"```carryover\n{CARRYOVER_ROW}\n```"]
    if opening:
        sections.insert(0, opening)
    if queue == "observation":
        sections.insert(
            0,
            "<!-- status:start -->\n"
            "Publication is pending a current admission record.\n"
            "<!-- status:end -->",
        )
    inventory = [prefix]
    if opening:
        inventory.append(opening)
    inventory.extend(
        ["## Status", "exact bytes", "credential", "Fiat-Required: 1", CARRYOVER_ROW]
    )
    document["queue"] = queue
    document["labels"] = list(labels)
    _set_candidate(
        document,
        title=f"{prefix}: checked publication boundary",
        body="\n\n".join(sections),
        prefix=prefix,
        opening=opening,
        structure=["## Status"],
        inventory=inventory,
    )
    return document


def _rejection_request(
    golden: dict[str, object],
    case_id: str,
    fixtures: dict[str, bytes],
) -> dict[str, object]:
    document = deepcopy(golden)
    if case_id == "issue-855-missing-framework-opening":
        try:
            title = fixtures["issue-855-title.txt"].removesuffix(b"\n").decode("utf-8")
            body = fixtures["issue-855-body.txt"].decode("utf-8")
        except UnicodeDecodeError:
            _refuse("conformance.issue-855")
        document["labels"] = ["fiat-run-needed", "observation", "origin:ai"]
        _set_candidate(
            document,
            title=title,
            body=body,
            prefix="framework-51",
            opening="",
            structure=["## What it looks like", "## Why it matters beyond one PR"],
            inventory=[
                "framework-51",
                "shoggoth-wildcat-labs",
                "## What it looks like",
                "wildcat-finance/skills#853",
                "## Why it matters beyond one PR",
                "HOST_PR_LOGINS",
            ],
        )
    elif case_id == "missing-gate":
        document["gates"].pop()
    elif case_id == "failed-gate":
        document["gates"][0]["outcome"] = "failed"
    elif case_id == "reordered-gate":
        document["gates"][0], document["gates"][1] = (
            document["gates"][1],
            document["gates"][0],
        )
    elif case_id == "gate-subject-mismatch":
        document["gates"][0]["subject_sha256"] = "0" * 64
    elif case_id == "imprimatur-defect":
        for name in ("source", "sapheneia_candidate", "final_candidate"):
            document[name]["body"] += "\n\nThis load-bearing phrase must be refused."
        _refresh_request(document)
    elif case_id == "authority-subject-mismatch":
        document["authority"]["subject_sha256"] = "0" * 64
    elif case_id == "missing-fiat-required":
        for name in ("source", "sapheneia_candidate", "final_candidate"):
            document[name]["body"] = document[name]["body"].replace(
                "\n\nFiat-Required: 1", ""
            )
        document["frozen"]["protected_inventory"].remove("Fiat-Required: 1")
        _refresh_request(document)
    elif case_id == "missing-carryover":
        carryover = f"\n\n```carryover\n{CARRYOVER_ROW}\n```"
        for name in ("source", "sapheneia_candidate", "final_candidate"):
            document[name]["body"] = document[name]["body"].replace(carryover, "")
        document["frozen"]["protected_inventory"].remove(CARRYOVER_ROW)
        _refresh_request(document)
    elif case_id == "noncanonical-title":
        _set_candidate(
            document,
            title="framework-0: checked publication boundary",
            body=document["source"]["body"],
            prefix="framework-0",
            opening=FRAMEWORK_OPENING,
            structure=document["frozen"]["host_structure"],
            inventory=[
                "framework-0" if item == "framework-56" else item
                for item in document["frozen"]["protected_inventory"]
            ],
        )
    elif case_id == "decision-label-mismatch":
        document["labels"] = ["observation", "only-pr-needed", "origin:ai"]
    else:
        _refuse("conformance.rejection-cases")
    return document


def _expect_refusal(raw: bytes, code: str, field: str) -> None:
    try:
        admit_request(raw)
    except PublisherError as exc:
        if exc.code != code or exc.mint_attempts != 0 or exc.post_attempts != 0:
            _refuse(field)
    else:
        _refuse(field)


def _verify_parser_bounds() -> None:
    at_member_limit = {f"field-{index}": index for index in range(MAX_JSON_MEMBERS)}
    parsed = parse_json_bytes(canonical_json(at_member_limit))
    if parsed != at_member_limit:
        _refuse("conformance.request-work-bound")
    above_member_limit = {
        f"field-{index}": index for index in range(MAX_JSON_MEMBERS + 1)
    }
    try:
        parse_json_bytes(canonical_json(above_member_limit))
    except PublisherError as exc:
        if exc.code != "GIP103" or exc.field != "request.members":
            _refuse("conformance.request-work-bound")
    else:
        _refuse("conformance.request-work-bound")
    at_string_limit = {"x" * MAX_STRING_BYTES: 0}
    if parse_json_bytes(canonical_json(at_string_limit)) != at_string_limit:
        _refuse("conformance.request-work-bound")
    above_string_limit = {"x" * (MAX_STRING_BYTES + 1): 0}
    try:
        parse_json_bytes(canonical_json(above_string_limit))
    except PublisherError as exc:
        if exc.code != "GIP103" or exc.field != "request.string":
            _refuse("conformance.request-work-bound")
    else:
        _refuse("conformance.request-work-bound")
    try:
        parse_json_bytes(b" " * (MAX_REQUEST_BYTES + 1))
    except PublisherError as exc:
        if exc.code != "GIP100" or exc.field != "request.bytes":
            _refuse("conformance.request-byte-bound")
    else:
        _refuse("conformance.request-byte-bound")


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

    golden = _canonical_fixture(valid, "conformance.valid-request")

    rejection_cases = _canonical_fixture(
        fixtures["rejection-cases.json"], "conformance.rejection-cases"
    )
    expected_rejections = {
        "issue-855-missing-framework-opening": "GIP130",
        "missing-gate": "GIP150",
        "failed-gate": "GIP150",
        "reordered-gate": "GIP120",
        "gate-subject-mismatch": "GIP150",
        "imprimatur-defect": "GIP151",
        "authority-subject-mismatch": "GIP160",
        "missing-fiat-required": "GIP132",
        "missing-carryover": "GIP132",
        "noncanonical-title": "GIP130",
        "decision-label-mismatch": "GIP131",
    }
    rejection_rows = rejection_cases.get("cases")
    if (
        set(rejection_cases) != {"schema", "cases"}
        or rejection_cases.get("schema")
        != "github-issue-publisher-rejection-cases/v1"
        or not isinstance(rejection_rows, list)
        or {
            row.get("id"): row.get("code")
            for row in rejection_rows
            if isinstance(row, dict) and set(row) == {"id", "code"}
        }
        != expected_rejections
        or len(rejection_rows) != len(expected_rejections)
    ):
        _refuse("conformance.rejection-cases")
    for case_id, code in expected_rejections.items():
        request = _rejection_request(golden, case_id, fixtures)
        _expect_refusal(
            canonical_json(request), code, "conformance.rejection-cases"
        )

    queue_cases = _canonical_fixture(
        fixtures["queue-cases.json"], "conformance.queue-cases"
    )
    expected_queues = {
        (
            "held-job",
            "phylax-next",
            "",
            ("fiat-run-needed", "held-job", "origin:ai"),
        ),
        ("wish", "phylax-7", "", ("fiat-run-needed", "origin:ai", "wish")),
        ("skill-wish", "phylax-wish", "", ("fiat-run-needed", "origin:ai")),
        (
            "observation",
            "framework-56",
            FRAMEWORK_OPENING,
            ("fiat-run-needed", "observation", "origin:ai"),
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
    for row in rows:
        request = _queue_request(golden, row)
        try:
            queue_admission = admit_request(canonical_json(request))
        except PublisherError as exc:
            raise PublisherError("GIP199", "conformance.queue-cases") from exc
        if (
            queue_admission.queue != row["queue"]
            or queue_admission.mint_attempts != 0
            or queue_admission.post_attempts != 0
        ):
            _refuse("conformance.queue-cases")

    _verify_parser_bounds()

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
        or body.startswith(FRAMEWORK_OPENING)
    ):
        _refuse("conformance.issue-855")


def _report_path(candidate: str, criterion: str) -> str:
    return f".hexaemeron/design-reports/{candidate}-{criterion}.json"


def _directory_descriptor(relative: Path) -> int:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    if relative.is_absolute() or not no_follow or any(
        part in ("", ".", "..") for part in relative.parts
    ):
        _refuse("conformance.report")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | no_follow
    )
    descriptor = -1
    try:
        descriptor = os.open(".", flags)
        for component in relative.parts:
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except OSError as exc:
        if descriptor >= 0:
            os.close(descriptor)
        raise PublisherError("GIP199", "conformance.report") from exc


def _write_report(relative: str, payload: bytes) -> None:
    destination = Path(relative)
    try:
        descriptor = _directory_descriptor(destination.parent)
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
