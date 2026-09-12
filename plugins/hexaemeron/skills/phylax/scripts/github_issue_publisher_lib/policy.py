"""Credential-free admission policy for one GitHub issue publication."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import re
from types import ModuleType
from typing import Any, Callable

from .canonical import (
    CANDIDATE_SCHEMA,
    FROZEN_SCHEMA,
    MAX_BODY_BYTES,
    MAX_TITLE_BYTES,
    REQUEST_SCHEMA,
    candidate_sha256,
    canonical_json,
    frozen_sha256,
    parse_json_bytes,
    safe_text,
    sha256_bytes,
)
from .errors import PublisherError, refuse


OPERATION = "issue.create"
REPOSITORY = "wildcat-finance/skills"
AUTHORITY_SCHEMA = "github-publication-authority/v1"
SAPHENEIA_VERSION = "0.3.0"
IMPRIMATUR_VERSION = "2.3.0"
VULGATE_VERSION = "1.1.0"
FRAMEWORK_OPENING = "Protasis decides which skill or skills this observation upgrades."
MAX_LABELS = 16
MAX_FROZEN_ITEMS = 64
LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .:_/-]{0,49}")
REFERENCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9#:/._-]{0,127}")
SKILL_RE = r"[a-z][a-z0-9-]*"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
QUEUE_RULES = {
    "held-job": (re.compile(rf"(?P<skill>{SKILL_RE})-next"), "held-job", ""),
    "wish": (re.compile(rf"(?P<skill>{SKILL_RE})-[0-9]+"), "wish", ""),
    "skill-wish": (re.compile(rf"(?P<skill>{SKILL_RE})-wish"), None, ""),
    "observation": (re.compile(r"framework-[0-9]+"), "observation", FRAMEWORK_OPENING),
}
QUEUE_LABELS = frozenset(
    required_label
    for _, required_label, _ in QUEUE_RULES.values()
    if required_label is not None
)
SAPHENEIA_CHECKS = (
    "subject-named",
    "host-structure-retained",
    "protected-inventory-retained",
    "connective-only",
    "five-step-complete",
)
VULGATE_CHECKS = (
    "facts-retained",
    "numbers-retained",
    "commitments-retained",
    "caveats-retained",
    "links-retained",
    "intent-retained",
)


ImprimaturRunner = Callable[[str], dict[str, Any]]


@dataclass(frozen=True)
class Candidate:
    title: str
    body: str
    sha256: str


@dataclass(frozen=True)
class AdmissionResult:
    request_sha256: str
    source_sha256: str
    sapheneia_sha256: str
    final_sha256: str
    frozen_sha256: str
    queue: str
    labels: tuple[str, ...]
    gate_versions: tuple[str, ...]
    mint_attempts: int = 0
    post_attempts: int = 0

    def document(self) -> dict[str, Any]:
        return {
            "schema": "github-issue-admission-result/v1",
            "outcome": "admitted",
            "request_sha256": self.request_sha256,
            "source_sha256": self.source_sha256,
            "sapheneia_sha256": self.sapheneia_sha256,
            "final_sha256": self.final_sha256,
            "frozen_sha256": self.frozen_sha256,
            "queue": self.queue,
            "labels": list(self.labels),
            "gate_versions": list(self.gate_versions),
            "mint_attempts": self.mint_attempts,
            "post_attempts": self.post_attempts,
        }


def _exact(document: Any, fields: set[str], field: str) -> dict[str, Any]:
    if not isinstance(document, dict) or set(document) != fields:
        refuse("GIP120", field)
    return document


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        refuse("GIP121", field)
    return value


def _candidate(document: Any, field: str) -> Candidate:
    candidate = _exact(document, {"schema", "title", "body"}, field)
    if candidate["schema"] != CANDIDATE_SCHEMA:
        refuse("GIP120", f"{field}.schema")
    title = safe_text(
        candidate["title"], f"{field}.title", max_bytes=MAX_TITLE_BYTES, multiline=False
    )
    body = safe_text(
        candidate["body"], f"{field}.body", max_bytes=MAX_BODY_BYTES, multiline=True
    )
    return Candidate(title, body, candidate_sha256(title, body))


def _ordered_presence(values: tuple[str, ...], candidate: Candidate, field: str) -> None:
    text = f"{candidate.title}\n{candidate.body}"
    cursor = 0
    for value in values:
        found = text.find(value, cursor)
        if found < 0:
            refuse("GIP141", field)
        cursor = found + len(value)


def _frozen(document: Any, candidates: tuple[Candidate, ...]) -> tuple[dict[str, Any], str]:
    frozen = _exact(
        document,
        {"schema", "title_prefix", "body_opening", "host_structure", "protected_inventory"},
        "frozen",
    )
    if frozen["schema"] != FROZEN_SCHEMA:
        refuse("GIP140", "frozen.schema")
    title_prefix = safe_text(
        frozen["title_prefix"], "frozen.title_prefix", max_bytes=128, multiline=False
    )
    body_opening = safe_text(
        frozen["body_opening"],
        "frozen.body_opening",
        max_bytes=1024,
        multiline=True,
        allow_empty=True,
    )
    structure = frozen["host_structure"]
    inventory = frozen["protected_inventory"]
    if (
        not isinstance(structure, list)
        or not structure
        or len(structure) > MAX_FROZEN_ITEMS
        or not isinstance(inventory, list)
        or not inventory
        or len(inventory) > MAX_FROZEN_ITEMS
    ):
        refuse("GIP140", "frozen.items")
    safe_structure = tuple(
        safe_text(item, "frozen.host_structure", max_bytes=1024, multiline=True)
        for item in structure
    )
    safe_inventory = tuple(
        safe_text(item, "frozen.protected_inventory", max_bytes=4096, multiline=True)
        for item in inventory
    )
    if len(set(safe_structure)) != len(safe_structure) or len(set(safe_inventory)) != len(safe_inventory):
        refuse("GIP140", "frozen.duplicate")
    for candidate in candidates:
        title_marker = f"{title_prefix}: "
        if (
            not candidate.title.startswith(title_marker)
            or not candidate.title[len(title_marker):].strip()
        ):
            refuse("GIP141", "frozen.title_prefix")
        if body_opening and not (
            candidate.body == body_opening
            or candidate.body.startswith(f"{body_opening}\n")
        ):
            refuse("GIP141", "frozen.body_opening")
        _ordered_presence(safe_structure, candidate, "frozen.host_structure")
        _ordered_presence(safe_inventory, candidate, "frozen.protected_inventory")
    normalised = {
        "schema": FROZEN_SCHEMA,
        "title_prefix": title_prefix,
        "body_opening": body_opening,
        "host_structure": list(safe_structure),
        "protected_inventory": list(safe_inventory),
    }
    return normalised, frozen_sha256(normalised)


def _labels(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or len(value) > MAX_LABELS:
        refuse("GIP131", "labels")
    labels = tuple(value)
    if (
        any(not isinstance(label, str) or LABEL_RE.fullmatch(label) is None for label in labels)
        or tuple(sorted(labels)) != labels
        or len(set(labels)) != len(labels)
    ):
        refuse("GIP131", "labels")
    return labels


def _queue(queue: Any, prefix: str, opening: str, labels: tuple[str, ...]) -> str:
    if not isinstance(queue, str) or queue not in QUEUE_RULES:
        refuse("GIP130", "queue")
    pattern, required_label, required_opening = QUEUE_RULES[queue]
    match = pattern.fullmatch(prefix)
    if match is None:
        refuse("GIP130", "queue.title_prefix")
    skill = match.groupdict().get("skill")
    if skill == "framework":
        refuse("GIP130", "queue.skill")
    expected_queue_labels = {required_label} if required_label is not None else set()
    if set(labels) & QUEUE_LABELS != expected_queue_labels:
        refuse("GIP130", "queue.labels")
    if required_opening != opening:
        refuse("GIP130", "queue.body_opening")
    return queue


def _authority(document: Any, final_sha256: str) -> None:
    authority = _exact(
        document,
        {"schema", "kind", "outcome", "reference", "subject_sha256"},
        "authority",
    )
    if (
        authority["schema"] != AUTHORITY_SCHEMA
        or authority["kind"] != "explicit-user-request"
        or authority["outcome"] != "recorded"
        or authority["subject_sha256"] != final_sha256
        or not isinstance(authority["reference"], str)
        or REFERENCE_RE.fullmatch(authority["reference"]) is None
    ):
        refuse("GIP160", "authority")


def _record(
    value: Any,
    fields: set[str],
    stage: str,
) -> dict[str, Any]:
    record = _exact(value, fields, f"gates.{stage}")
    if record.get("stage") != stage:
        refuse("GIP150", f"gates.{stage}.stage")
    return record


def _gates(
    value: Any,
    *,
    source: Candidate,
    shaped: Candidate,
    final: Candidate,
    frozen_digest: str,
) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) != 4:
        refuse("GIP150", "gates")
    sapheneia = _record(
        value[0],
        {
            "stage",
            "tool",
            "version",
            "outcome",
            "source_sha256",
            "candidate_sha256",
            "subject_sha256",
            "frozen_sha256",
            "checks",
        },
        "sapheneia",
    )
    if (
        sapheneia["tool"] != "sapheneia:sapheneia"
        or sapheneia["version"] != SAPHENEIA_VERSION
        or sapheneia["outcome"] != "passed"
        or sapheneia["source_sha256"] != source.sha256
        or sapheneia["candidate_sha256"] != shaped.sha256
        or sapheneia["subject_sha256"] != shaped.sha256
        or sapheneia["frozen_sha256"] != frozen_digest
        or sapheneia["checks"] != list(SAPHENEIA_CHECKS)
    ):
        refuse("GIP150", "gates.sapheneia")
    first_lint = _record(
        value[1],
        {"stage", "tool", "version", "outcome", "subject_sha256", "defects"},
        "imprimatur",
    )
    if (
        first_lint["tool"] != "hexaemeron:imprimatur"
        or first_lint["version"] != IMPRIMATUR_VERSION
        or first_lint["outcome"] != "clean"
        or first_lint["subject_sha256"] != shaped.sha256
        or type(first_lint["defects"]) is not int
        or first_lint["defects"] != 0
    ):
        refuse("GIP150", "gates.imprimatur")
    vulgate = _record(
        value[2],
        {
            "stage",
            "tool",
            "version",
            "outcome",
            "source_sha256",
            "candidate_sha256",
            "subject_sha256",
            "frozen_sha256",
            "checks",
        },
        "vulgate",
    )
    if (
        vulgate["tool"] != "hexaemeron:vulgate"
        or vulgate["version"] != VULGATE_VERSION
        or vulgate["outcome"] != "parity"
        or vulgate["source_sha256"] != shaped.sha256
        or vulgate["candidate_sha256"] != final.sha256
        or vulgate["subject_sha256"] != final.sha256
        or vulgate["frozen_sha256"] != frozen_digest
        or vulgate["checks"] != list(VULGATE_CHECKS)
    ):
        refuse("GIP150", "gates.vulgate")
    final_lint = _record(
        value[3],
        {"stage", "tool", "version", "outcome", "subject_sha256", "defects"},
        "imprimatur-final",
    )
    if (
        final_lint["tool"] != "hexaemeron:imprimatur"
        or final_lint["version"] != IMPRIMATUR_VERSION
        or final_lint["outcome"] != "clean"
        or final_lint["subject_sha256"] != final.sha256
        or type(final_lint["defects"]) is not int
        or final_lint["defects"] != 0
    ):
        refuse("GIP150", "gates.imprimatur-final")
    return (SAPHENEIA_VERSION, IMPRIMATUR_VERSION, VULGATE_VERSION, IMPRIMATUR_VERSION)


_IMPRIMATUR_MODULE: ModuleType | None = None


def _load_imprimatur() -> ModuleType:
    global _IMPRIMATUR_MODULE
    if _IMPRIMATUR_MODULE is not None:
        return _IMPRIMATUR_MODULE
    phylax_root = Path(__file__).resolve().parents[2]
    skills_root = phylax_root.parent
    skill_file = skills_root / "imprimatur" / "SKILL.md"
    script = skills_root / "imprimatur" / "scripts" / "imprimatur.py"
    try:
        skill_text = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise PublisherError("GIP152", "gates.imprimatur.version") from exc
    if f'version: "{IMPRIMATUR_VERSION}"' not in skill_text or not script.is_file():
        refuse("GIP152", "gates.imprimatur.version")
    specification = importlib.util.spec_from_file_location("github_issue_publisher_imprimatur", script)
    if specification is None or specification.loader is None:
        refuse("GIP152", "gates.imprimatur.load")
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
    except (ImportError, OSError, RuntimeError, SyntaxError, SystemExit, TypeError, ValueError) as exc:
        raise PublisherError("GIP152", "gates.imprimatur.load") from exc
    _IMPRIMATUR_MODULE = module
    return module


def default_imprimatur(text: str) -> dict[str, Any]:
    module = _load_imprimatur()
    try:
        result = module.build(text, source_suffix=".md")
    except (OSError, RuntimeError, SystemExit, TypeError, ValueError) as exc:
        raise PublisherError("GIP152", "gates.imprimatur.run") from exc
    if not isinstance(result, dict):
        refuse("GIP152", "gates.imprimatur.result")
    return result


def _run_imprimatur(candidate: Candidate, runner: ImprimaturRunner) -> None:
    try:
        result = runner(f"{candidate.title}\n\n{candidate.body}")
    except PublisherError:
        raise
    except SystemExit as exc:
        raise PublisherError("GIP152", "gates.imprimatur.run") from exc
    except Exception as exc:
        raise PublisherError("GIP152", "gates.imprimatur.run") from exc
    if (
        not isinstance(result, dict)
        or type(result.get("defects")) is not int
        or result["defects"] != 0
    ):
        refuse("GIP151", "gates.imprimatur.defects")


def admit_request(
    raw: bytes,
    *,
    imprimatur_runner: ImprimaturRunner | None = None,
) -> AdmissionResult:
    document = parse_json_bytes(raw)
    request = _exact(
        document,
        {
            "schema",
            "operation",
            "repository",
            "queue",
            "labels",
            "frozen",
            "source",
            "sapheneia_candidate",
            "final_candidate",
            "authority",
            "gates",
        },
        "request",
    )
    if request["schema"] != REQUEST_SCHEMA:
        refuse("GIP120", "request.schema")
    if request["operation"] != OPERATION:
        refuse("GIP120", "request.operation")
    if request["repository"] != REPOSITORY:
        refuse("GIP120", "request.repository")
    source = _candidate(request["source"], "source")
    shaped = _candidate(request["sapheneia_candidate"], "sapheneia_candidate")
    final = _candidate(request["final_candidate"], "final_candidate")
    frozen, frozen_digest = _frozen(request["frozen"], (source, shaped, final))
    labels = _labels(request["labels"])
    queue = _queue(
        request["queue"],
        frozen["title_prefix"],
        frozen["body_opening"],
        labels,
    )
    _authority(request["authority"], final.sha256)
    gate_versions = _gates(
        request["gates"],
        source=source,
        shaped=shaped,
        final=final,
        frozen_digest=frozen_digest,
    )
    runner = default_imprimatur if imprimatur_runner is None else imprimatur_runner
    _run_imprimatur(shaped, runner)
    _run_imprimatur(final, runner)
    return AdmissionResult(
        request_sha256=sha256_bytes(canonical_json(request)),
        source_sha256=source.sha256,
        sapheneia_sha256=shaped.sha256,
        final_sha256=final.sha256,
        frozen_sha256=frozen_digest,
        queue=queue,
        labels=labels,
        gate_versions=gate_versions,
    )
