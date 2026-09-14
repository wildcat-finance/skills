#!/usr/bin/env python3
"""Offline conformance entrypoint for the bounded GitHub issue publisher.

The command uses injected signer and HTTPS doubles. It cannot read the live
PEM, mint a live token, open a socket, or make a network request.
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
from github_issue_publisher_lib.receipts import (  # noqa: E402
    MemoryReceiptSink,
    parse_closed_result,
    result_bytes,
)
from github_issue_publisher_lib.runtime import PublisherRuntime  # noqa: E402
from github_issue_publisher_lib.signer import (  # noqa: E402
    APP_ID,
    MAX_SIGNATURE_BYTES,
    OPENSSL_ARGUMENTS,
    PEM_PATH,
    RSA_SIGNATURE_BYTES,
    OpenSSLSigner,
)
from github_issue_publisher_lib.transport import (  # noqa: E402
    API_VERSION,
    GITHUB_API_HOST,
    GITHUB_REPOSITORY,
    HTTPS_PORT,
    ISSUES_ROUTE,
    INSTALLATION_ID,
    TOKEN_ROUTE,
    HTTPSRequest,
    PinnedGitHubTransport,
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
    "runtime-cases.json",
    "valid-request.json",
)
CRITERIA = {
    "ordered-admission-chain": (True, "boolean"),
    "request-work-bound": (MAX_JSON_MEMBERS, "count"),
    "request-byte-bound": (MAX_REQUEST_BYTES, "bytes"),
    "signer-and-post-boundary": (True, "boolean"),
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

    metadata_request = deepcopy(golden)
    for name in ("source", "sapheneia_candidate", "final_candidate"):
        metadata_request[name]["body"] = (
            "<!-- wildcat-origin: shoggoth -->\n\n"
            + metadata_request[name]["body"]
        )
    _refresh_request(metadata_request)
    try:
        metadata_admission = admit_request(canonical_json(metadata_request))
    except PublisherError as exc:
        raise PublisherError("GIP199", "conformance.metadata-comment") from exc
    if metadata_admission.mint_attempts != 0 or metadata_admission.post_attempts != 0:
        _refuse("conformance.metadata-comment")

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

    for character in ("\u00a0", "\u2028", "\u2029"):
        nonprinting_request = deepcopy(golden)
        for name in ("source", "sapheneia_candidate", "final_candidate"):
            nonprinting_request[name]["title"] = (
                f"framework-56: checked{character}publication boundary"
            )
        _refresh_request(nonprinting_request)
        _expect_refusal(
            canonical_json(nonprinting_request),
            "GIP110",
            "conformance.nonprinting-title",
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


class _ConformanceSigner:
    def __init__(self) -> None:
        self.calls: list[tuple[bytes, float]] = []
        self.runner_calls: list[tuple[tuple[str, ...], bytes, float, int]] = []
        self.closed = False
        self._signer = OpenSSLSigner(self._run)

    def _run(
        self,
        arguments: tuple[str, ...],
        signing_input: bytes,
        timeout_seconds: float,
        output_limit: int,
    ) -> bytes:
        self.runner_calls.append(
            (arguments, bytes(signing_input), timeout_seconds, output_limit)
        )
        if arguments != OPENSSL_ARGUMENTS or output_limit != MAX_SIGNATURE_BYTES:
            _refuse("conformance.runtime.signer")
        return b"\xa5" * RSA_SIGNATURE_BYTES

    def sign(self, signing_input: bytes, *, timeout_seconds: float) -> bytes:
        self.calls.append((bytes(signing_input), timeout_seconds))
        return self._signer.sign(
            signing_input,
            timeout_seconds=timeout_seconds,
        )

    def close(self) -> None:
        self._signer.close()
        self.closed = True


class _ConformanceResponse:
    def __init__(self, status: int, document: dict[str, object]):
        self.status = status
        self.headers = (("Content-Type", "application/json"),)
        self._raw = canonical_json(document)
        self._offset = 0
        self.closed = False

    def read(self, size: int) -> bytes:
        take = min(size, 7)
        chunk = self._raw[self._offset : self._offset + take]
        self._offset += len(chunk)
        return chunk

    def close(self) -> None:
        self.closed = True


class _ConformanceExchange:
    def __init__(
        self,
        *,
        title: str,
        body: str,
        labels: list[str],
        token: str,
        expires_at: str,
        issue_number: int,
        issue_url: str,
    ):
        self._title = title
        self._body = body
        self._labels = labels
        self._token = token
        self._expires_at = expires_at
        self._issue_number = issue_number
        self._issue_url = issue_url
        self.requests: list[HTTPSRequest] = []
        self.responses: list[_ConformanceResponse] = []

    @staticmethod
    def _header(request: HTTPSRequest, name: str) -> str | None:
        return next(
            (value for key, value in request.headers if key.casefold() == name.casefold()),
            None,
        )

    def _response(self, status: int, document: dict[str, object]) -> _ConformanceResponse:
        response = _ConformanceResponse(status, document)
        self.responses.append(response)
        return response

    def __call__(self, request: HTTPSRequest, _context: object) -> _ConformanceResponse:
        self.requests.append(request)
        call = len(self.requests)
        if call == 1:
            expected = canonical_json(
                {"permissions": {"issues": "write"}, "repositories": ["skills"]}
            )
            if (
                request.method != "POST"
                or request.path != TOKEN_ROUTE
                or request.body != expected
                or self._header(request, "Authorization") is None
                or self._header(request, "X-GitHub-Api-Version") != API_VERSION
            ):
                _refuse("conformance.runtime.token-request")
            return self._response(
                201,
                {
                    "token": self._token,
                    "expires_at": self._expires_at,
                    "permissions": {"issues": "write"},
                    "repository_selection": "selected",
                    "repositories": [{"full_name": GITHUB_REPOSITORY}],
                },
            )
        issue = {
            "number": self._issue_number,
            "html_url": self._issue_url,
            "title": self._title,
            "body": self._body,
        }
        if call == 2:
            expected = canonical_json(
                {"body": self._body, "labels": self._labels, "title": self._title}
            )
            if (
                request.method != "POST"
                or request.path != ISSUES_ROUTE
                or request.body != expected
                or self._header(request, "Authorization") != f"token {self._token}"
            ):
                _refuse("conformance.runtime.issue-request")
            return self._response(201, issue)
        if call not in (3, 4) or request.method != "GET" or request.body:
            _refuse("conformance.runtime.readback-request")
        if request.path != f"{ISSUES_ROUTE}/{self._issue_number}":
            _refuse("conformance.runtime.readback-request")
        authorization = self._header(request, "Authorization")
        if (call == 3 and authorization != f"token {self._token}") or (
            call == 4 and authorization is not None
        ):
            _refuse("conformance.runtime.readback-request")
        return self._response(200, issue)


def _verify_runtime_contract(fixtures: dict[str, bytes]) -> None:
    if (
        APP_ID != "4764812"
        or OPENSSL_ARGUMENTS
        != (
            "/usr/bin/openssl",
            "dgst",
            "-sha256",
            "-sign",
            "/var/db/wildcat-github-issue-publisher/shoggoth-wildcat-labs.pem",
        )
        or PEM_PATH
        != "/var/db/wildcat-github-issue-publisher/shoggoth-wildcat-labs.pem"
        or MAX_SIGNATURE_BYTES != 4_096
        or RSA_SIGNATURE_BYTES != 256
        or GITHUB_API_HOST != "api.github.com"
        or HTTPS_PORT != 443
        or GITHUB_REPOSITORY != "wildcat-finance/skills"
        or INSTALLATION_ID != "157591976"
        or API_VERSION != "2022-11-28"
        or TOKEN_ROUTE != "/app/installations/157591976/access_tokens"
        or ISSUES_ROUTE != "/repos/wildcat-finance/skills/issues"
    ):
        _refuse("conformance.runtime.constants")
    cases = _canonical_fixture(
        fixtures["runtime-cases.json"], "conformance.runtime-cases"
    )
    expected_fields = {
        "schema",
        "expected_stages",
        "expires_at",
        "issue_number",
        "issue_url",
    }
    stages = cases.get("expected_stages")
    if (
        set(cases) != expected_fields
        or cases.get("schema") != "github-issue-publisher-runtime-cases/v1"
        or stages
        != [
            "admission",
            "signer",
            "token",
            "create",
            "readback-authenticated",
            "readback-anonymous",
            "cleanup",
            "receipt",
        ]
        or cases.get("issue_number") != 9250
        or cases.get("issue_url")
        != "https://github.com/wildcat-finance/skills/issues/9250"
        or cases.get("expires_at") != "2033-05-18T04:33:20Z"
    ):
        _refuse("conformance.runtime-cases")
    request = _canonical_fixture(
        fixtures["valid-request.json"], "conformance.valid-request"
    )
    final = request.get("final_candidate")
    labels = request.get("labels")
    if not isinstance(final, dict) or not isinstance(labels, list):
        _refuse("conformance.runtime-cases")
    title = final.get("title")
    body = final.get("body")
    if not isinstance(title, str) or not isinstance(body, str):
        _refuse("conformance.runtime-cases")
    canary = "ghs_" + sha256_bytes(fixtures["valid-request.json"])[:48]
    signer = _ConformanceSigner()
    exchange = _ConformanceExchange(
        title=title,
        body=body,
        labels=labels,
        token=canary,
        expires_at=cases["expires_at"],
        issue_number=cases["issue_number"],
        issue_url=cases["issue_url"],
    )
    sink = MemoryReceiptSink()
    runtime = PublisherRuntime(
        signer=signer,
        transport=PinnedGitHubTransport(exchange),
        receipt_sink=sink,
        wall_clock=lambda: 2_000_000_000.0,
        monotonic=lambda: 100.0,
    )
    result = runtime.publish(fixtures["valid-request.json"][:-1])
    if (
        result.get("outcome") != "published"
        or result.get("readback") != "matched"
        or result.get("issue_number") != cases["issue_number"]
        or result.get("issue_url") != cases["issue_url"]
        or result.get("counts")
        != {
            "signer_attempts": 1,
            "token_attempts": 1,
            "post_attempts": 1,
            "authenticated_readbacks": 1,
            "anonymous_readbacks": 1,
        }
        or not signer.closed
        or not sink.closed
        or sink.payload != result_bytes(result)
        or parse_closed_result(sink.payload) != result
        or [event["stage"] for event in runtime.events] != stages
        or len(exchange.requests) != 4
        or len(signer.runner_calls) != 1
        or any(not response.closed for response in exchange.responses)
    ):
        _refuse("conformance.runtime-result")
    retained = (
        result_bytes(result)
        + canonical_json(list(runtime.events))
        + repr(signer.calls).encode("utf-8")
        + repr(exchange.requests).encode("utf-8")
    )
    if canary.encode("ascii") in retained:
        _refuse("conformance.runtime-disclosure")


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
    if criterion == "signer-and-post-boundary":
        _verify_runtime_contract(fixtures)
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
