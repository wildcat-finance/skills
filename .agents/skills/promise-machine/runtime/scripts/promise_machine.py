#!/usr/bin/env python3
"""Check and synchronise the Promise Machine law at fixed repository paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
import re
import tempfile


CONTRACT_ID = "promise-machine/v1"
LAW_NAME = "PROMISE_MACHINE.md"
LICENSE_NAME = "LICENSE"
MARKER = (
    "<!-- promise-machine: contract=promise-machine/v1; "
    "canonical=PROMISE_MACHINE.md; copies=generated -->"
)
MAX_MARKDOWN_BYTES = 256 * 1024
MAX_JSON_BYTES = 64 * 1024
MAX_COVERAGE_BYTES = 512 * 1024
MAX_RUNTIME_SOURCE_BYTES = 1024 * 1024
MAX_LICENSE_BYTES = 64 * 1024
REQUIRED_HEADINGS = (
    "# Promise Machine contract",
    "## Contract identity",
    "## Governing principle",
    "## Scope",
    "## Vocabulary",
    "## Evidence classes",
    "## Promise declarations",
    "## Consequence levels",
    "## Composition",
    "## Refusal and recovery",
    "## Exceptions",
    "## Conformance",
    "## First-party licence promise",
    "## Installation copies",
)
REQUIRED_FIELDS = (
    "Promise",
    "Evidence",
    "Evidence classes",
    "Boundary",
    "Authorises",
    "Consequence",
    "Refuses",
    "Recovery",
    "Exceptions",
)
PLUGIN_MANIFESTS = (
    Path(".claude-plugin/plugin.json"),
    Path(".codex-plugin/plugin.json"),
)
SUPPORTED_EVIDENCE_CLASSES = {
    "checked",
    "recomputed",
    "proved",
    "measured",
    "recorded",
    "attested",
    "inferred",
    "unknown",
}
PROMISE_ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
OVERLAY_PATH = Path("plugins/hexaemeron/PROMISES.md")
OVERLAY_HEADING = "# Hexaemeron Promise Machine overlays"
OVERLAY_FIELDS = ("Path", "SHA-256", *REQUIRED_FIELDS)
COVERAGE_PATH = Path("tests/promise_machine_coverage.json")
COVERAGE_SCHEMA = "promise-machine-coverage/v1"
OBLIGATION_PATH = Path("tests/promise_machine_obligations.json")
OBLIGATION_SCHEMA = "promise-machine-obligations/v1"
OBLIGATION_SPECIMEN_SCHEMA = "promise-machine-obligation-specimen/v1"
OBLIGATION_FIXTURE_ROOT = Path("tests/fixtures/promise-machine/obligations")
OBLIGATION_MARKER = re.compile(
    r"<!-- promise-machine-obligation: id=([a-z][a-z0-9]*(?:-[a-z0-9]+)*) -->"
)
OBLIGATION_MARKER_PREFIX = "<!-- promise-machine-obligation:"
OBLIGATION_CLAUSE_PREFIX = "> Obligation:"
OBLIGATION_ROW_KEYS = {
    "id",
    "gate",
    "specimen",
    "finding",
    "consequence",
    "blocked_transition",
    "recovery",
}
OBLIGATION_GATE_CODES = {
    "law.generated-copy-marker": "PM005",
    "law.required-sections": "PM006",
    "law.contract-identity": "PM007",
    "law.declaration-fields": "PM008",
    "law.governing-principle": "PM009",
}
COVERAGE_CODES = ("P", "M", "S", "O", "R", "X")
EVALUATION_KEYS = {"status", "model", "prompt", "corpus", "disposition"}
RUNTIME_BINDING_KEYS = {
    "promise_id",
    "subject",
    "scope",
    "evidence_references",
    "evidence_classes",
    "unknowns",
    "transition",
    "exception",
}
PROMPT_SKILLS = {
    "brevitas",
    "hypomnema",
    "imprimatur",
    "kronos",
    "sapheneia",
    "vulgate",
}
PRESERVATION_REQUIREMENTS = {
    "berean-corpus-binding": {"corpus-digest", "source-class", "subject"},
    "berean-answer-evidence": {
        "answer-truth-refused",
        "read-class",
        "source-class",
        "subject",
        "time-domain",
    },
    "berean-evaluation-report": {
        "answer-digest",
        "answer-truth-refused",
        "corpus-digest",
        "time-domain",
    },
    "berean-release-promotion": {
        "answer-digest",
        "answer-truth-refused",
        "corpus-digest",
        "evaluation-digest",
    },
    "janus-manifest-validation": {"adapter", "manifest"},
    "janus-bounded-conformance": {
        "adapter",
        "bounded-search",
        "cross-host-refused",
        "manifest",
        "recorder",
        "safety-refused",
        "unknown-effect-refused",
    },
    "janus-report-rendering": {
        "adapter",
        "bounded-search",
        "manifest",
        "recorder",
        "safety-refused",
    },
}
REQUIRED_HANDOFFS = {
    ("lazarus-fixture-verification", "berean-answer-evidence"),
    ("berean-release-promotion", "ariadne-capture-statement"),
}
HANDOFF_PRESERVES = {
    ("lazarus-fixture-verification", "berean-answer-evidence"): {
        "block",
        "evidence-class",
        "subject",
    },
    ("berean-release-promotion", "ariadne-capture-statement"): {
        "answer-digest",
        "evidence-class",
        "subject",
    },
}


@dataclass(frozen=True)
class Finding:
    code: str
    fault: str
    path: str
    message: str
    remedy: str
    promise_id: str | None = None
    obligation_id: str | None = None
    consequence: int | None = None
    blocked_transition: str | None = None
    recovery: str | None = None


@dataclass(frozen=True)
class SkillRecord:
    name: str
    path: str
    plugin: str
    governance: str
    ownership: str


@dataclass(frozen=True)
class Inventory:
    plugins: tuple[str, ...]
    skills: tuple[SkillRecord, ...]
    routers: tuple[str, ...]
    overlays: tuple[str, ...]


@dataclass(frozen=True)
class PromiseRecord:
    promise_id: str
    skill_path: str
    group: str
    evidence_classes: frozenset[str]
    consequence: int


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def confined(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
        return True
    except (OSError, ValueError):
        return False


def bounded_sha256(path: Path, limit: int):
    digest = hashlib.sha256()
    total = 0
    try:
        with path.open("rb") as source:
            while chunk := source.read(64 * 1024):
                total += len(chunk)
                if total > limit:
                    return None, f"source exceeds the {limit}-byte limit"
                digest.update(chunk)
    except OSError as exc:
        return None, f"source could not be read: {exc}"
    return digest.hexdigest(), None


def bounded_read_bytes(path: Path, limit: int):
    """Read at most one byte beyond a declared input boundary."""
    with path.open("rb") as source:
        return source.read(limit + 1)


def read_markdown(path: Path, root: Path, *, missing_code: str, unsafe_code: str):
    findings: list[Finding] = []
    shown = relative(path, root)
    if path.is_symlink() or not confined(path, root):
        findings.append(
            Finding(
                unsafe_code,
                "identity",
                shown,
                "contract path is a symlink or resolves outside the repository",
                "replace it with a regular file at the fixed destination",
            )
        )
        return None, findings
    if not path.is_file():
        findings.append(
            Finding(
                missing_code,
                "drift",
                shown,
                "required contract file is absent",
                "run scripts/promise_machine.py sync",
            )
        )
        return None, findings
    try:
        payload = bounded_read_bytes(path, MAX_MARKDOWN_BYTES)
    except OSError as exc:
        findings.append(
            Finding(
                unsafe_code,
                "identity",
                shown,
                f"contract file could not be read: {exc}",
                "restore a readable regular file inside the repository",
            )
        )
        return None, findings
    if len(payload) > MAX_MARKDOWN_BYTES:
        findings.append(
            Finding(
                "PM003",
                "structural",
                shown,
                f"contract is {len(payload)} bytes; limit is {MAX_MARKDOWN_BYTES}",
                "reduce the authored law below the bounded-read limit",
            )
        )
        return None, findings
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        findings.append(
            Finding(
                "PM004",
                "structural",
                shown,
                "contract is not UTF-8",
                "write the contract as UTF-8 Markdown",
            )
        )
        return None, findings
    return (payload, text), findings


def read_json(
    path: Path,
    root: Path,
    *,
    max_bytes: int = MAX_JSON_BYTES,
    missing_code: str = "PM021",
    unsafe_code: str = "PM021",
    malformed_code: str = "PM022",
    noun: str = "plugin manifest",
):
    shown = relative(path, root)
    if path.is_symlink() or not confined(path, root):
        return None, [
            Finding(
                unsafe_code,
                "identity",
                shown,
                f"{noun} is a symlink or resolves outside the repository",
                f"restore a regular {noun} at the fixed path",
            )
        ]
    if not path.is_file():
        return None, [
            Finding(
                missing_code,
                "structural",
                shown,
                f"{noun} is absent",
                f"restore the required {noun}",
            )
        ]
    try:
        payload = bounded_read_bytes(path, max_bytes)
    except OSError as exc:
        return None, [
            Finding(
                unsafe_code,
                "identity",
                shown,
                f"{noun} could not be read: {exc}",
                f"restore a readable {noun} inside the repository",
            )
        ]
    if len(payload) > max_bytes:
        return None, [
            Finding(
                malformed_code,
                "structural",
                shown,
                f"JSON document is {len(payload)} bytes; limit is {max_bytes}",
                "reduce the document below the bounded-read limit",
            )
        ]
    def reject_duplicate_keys(pairs):
        document = {}
        for key, value in pairs:
            if key in document:
                raise ValueError(f"duplicate object key: {key!r}")
            document[key] = value
        return document

    try:
        document = json.loads(payload, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return None, [
            Finding(
                malformed_code,
                "structural",
                shown,
                f"{noun} is not valid UTF-8 JSON: {exc}",
                f"restore a valid {noun}",
            )
        ]
    if not isinstance(document, dict):
        return None, [
            Finding(
                malformed_code,
                "structural",
                shown,
                f"{noun} root is not an object",
                f"restore the {noun} object",
            )
        ]
    return document, []


def frontmatter_lines(text: str):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None
    return lines[1:end]


def check_law(root: Path):
    law_path = root / LAW_NAME
    loaded, findings = read_markdown(
        law_path, root, missing_code="PM001", unsafe_code="PM002"
    )
    if loaded is None:
        return None, findings
    payload, text = loaded
    findings.extend(validate_law_document(payload, text, LAW_NAME))
    return payload, findings


def validate_law_document(payload: bytes, text: str, shown: str):
    """Apply the production law gates to one already bounded Markdown payload."""
    findings: list[Finding] = []
    lines = text.splitlines()
    if MARKER not in lines[:5]:
        findings.append(
            Finding(
                "PM005",
                "identity",
                shown,
                "generated-copy marker is absent from the law header",
                "restore the promise-machine/v1 canonical/copies marker",
            )
        )
    for heading in REQUIRED_HEADINGS:
        if lines.count(heading) != 1:
            findings.append(
                Finding(
                    "PM006",
                    "structural",
                    shown,
                    f"required heading must occur once: {heading}",
                    "restore the one normative section with that exact heading",
                )
            )
    versions = set(re.findall(r"promise-machine/v[0-9]+", text))
    if versions != {CONTRACT_ID}:
        findings.append(
            Finding(
                "PM007",
                "version",
                shown,
                f"contract identities are {sorted(versions)!r}; expected only {CONTRACT_ID}",
                "use the shared contract identity and remove competing identities",
            )
        )
    for field in REQUIRED_FIELDS:
        if f"`{field}`" not in text:
            findings.append(
                Finding(
                    "PM008",
                    "structural",
                    shown,
                    f"promise declaration field is absent: {field}",
                    "restore the field in the per-promise schema",
                )
            )
    principle = (
        "No skill may claim more than its evidence establishes, or authorise a more\n"
        "> consequential transition than that evidence warrants."
    )
    if principle not in text:
        findings.append(
            Finding(
                "PM009",
                "structural",
                shown,
                "the governing principle is absent or changed",
                "restore the settled suite-wide principle exactly",
            )
        )
    return findings


def discover_obligations(text: str):
    """Discover the closed explicit obligation grammar from the authored law."""
    findings: list[Finding] = []
    lines = text.splitlines()
    markers: dict[str, int] = {}
    marker_lines: dict[int, str] = {}
    clause_markers: set[int] = set()

    for index, line in enumerate(lines):
        if OBLIGATION_MARKER_PREFIX not in line:
            continue
        matched = OBLIGATION_MARKER.fullmatch(line)
        if matched is None:
            findings.append(
                Finding(
                    "PM080",
                    "structural",
                    LAW_NAME,
                    f"malformed obligation marker at line {index + 1}",
                    "use the exact promise-machine-obligation id marker grammar",
                )
            )
            continue
        obligation_id = matched.group(1)
        if obligation_id in markers:
            findings.append(
                Finding(
                    "PM081",
                    "identity",
                    LAW_NAME,
                    f"obligation id is marked more than once: {obligation_id}",
                    "retain one marker on the one clause that owns this stable id",
                    obligation_id=obligation_id,
                )
            )
            continue
        markers[obligation_id] = index
        marker_lines[index] = obligation_id

    for index, line in enumerate(lines):
        if not line.startswith(OBLIGATION_CLAUSE_PREFIX):
            continue
        previous = index - 1
        while previous >= 0 and not lines[previous].strip():
            previous -= 1
        obligation_id = marker_lines.get(previous)
        if obligation_id is None:
            findings.append(
                Finding(
                    "PM080",
                    "structural",
                    LAW_NAME,
                    f"explicit obligation clause at line {index + 1} has no marker",
                    "put one valid stable obligation marker immediately before the clause",
                )
            )
            continue
        clause_markers.add(previous)

    for index, obligation_id in marker_lines.items():
        if index in clause_markers:
            continue
        findings.append(
            Finding(
                "PM080",
                "structural",
                LAW_NAME,
                f"obligation marker has no following explicit clause: {obligation_id}",
                "place the marker immediately before one > Obligation: clause",
                obligation_id=obligation_id,
            )
        )
    return set(markers), findings


def obligation_finding(code: str, path: str, message: str, remedy: str, row=None):
    row = row if isinstance(row, dict) else {}
    return Finding(
        code,
        "obligation",
        path,
        message,
        remedy,
        obligation_id=row.get("id"),
        consequence=row.get("consequence"),
        blocked_transition=row.get("blocked_transition"),
        recovery=row.get("recovery"),
    )


def repository_relative_fixture(raw: str):
    if not isinstance(raw, str) or not raw or raw != raw.strip():
        return None
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != raw:
        return None
    try:
        candidate.relative_to(OBLIGATION_FIXTURE_ROOT)
    except ValueError:
        return None
    if candidate.suffix != ".json":
        return None
    return candidate


def validate_obligation_specimen(root: Path, law_text: str, row: dict):
    specimen_raw = row["specimen"]
    relative_specimen = repository_relative_fixture(specimen_raw)
    if relative_specimen is None:
        return [
            obligation_finding(
                "PM087",
                str(specimen_raw),
                "negative specimen path is not a confined JSON path under the fixture root",
                "use one repository-relative JSON fixture below tests/fixtures/promise-machine/obligations",
                row,
            )
        ]
    specimen_path = root / relative_specimen
    document, findings = read_json(
        specimen_path,
        root,
        max_bytes=MAX_JSON_BYTES,
        missing_code="PM087",
        unsafe_code="PM087",
        malformed_code="PM088",
        noun="Promise Machine obligation specimen",
    )
    if document is None:
        return [
            obligation_finding(
                item.code,
                item.path,
                item.message,
                item.remedy,
                row,
            )
            for item in findings
        ]
    if set(document) != {"schema", "obligation_id", "mutation"}:
        return [
            obligation_finding(
                "PM088",
                relative_specimen.as_posix(),
                "specimen fields are not exactly schema, obligation_id, and mutation",
                "restore the closed promise-machine-obligation-specimen/v1 shape",
                row,
            )
        ]
    if document["schema"] != OBLIGATION_SPECIMEN_SCHEMA:
        return [
            obligation_finding(
                "PM088",
                relative_specimen.as_posix(),
                f"unsupported specimen schema: {document['schema']!r}",
                f"declare {OBLIGATION_SPECIMEN_SCHEMA}",
                row,
            )
        ]
    if document["obligation_id"] != row["id"]:
        return [
            obligation_finding(
                "PM088",
                relative_specimen.as_posix(),
                "specimen obligation id does not match its registry row",
                "bind the specimen to the row's exact stable obligation id",
                row,
            )
        ]
    mutation = document["mutation"]
    if not isinstance(mutation, dict) or set(mutation) != {"operation", "old", "new"}:
        return [
            obligation_finding(
                "PM088",
                relative_specimen.as_posix(),
                "specimen mutation is not the closed operation, old, and new object",
                "restore one bounded replace_once mutation",
                row,
            )
        ]
    old = mutation.get("old")
    new = mutation.get("new")
    if (
        mutation.get("operation") != "replace_once"
        or not isinstance(old, str)
        or not old
        or not isinstance(new, str)
        or old == new
        or law_text.count(old) != 1
    ):
        return [
            obligation_finding(
                "PM088",
                relative_specimen.as_posix(),
                "replace_once mutation is invalid or its source text is not unique",
                "name one exact unique law fragment and a different replacement",
                row,
            )
        ]
    mutated_text = law_text.replace(old, new, 1)
    mutated_payload = mutated_text.encode("utf-8")
    if len(mutated_payload) > MAX_MARKDOWN_BYTES:
        return [
            obligation_finding(
                "PM088",
                relative_specimen.as_posix(),
                f"mutated law exceeds the {MAX_MARKDOWN_BYTES}-byte limit",
                "keep the hostile specimen inside the bounded law surface",
                row,
            )
        ]
    produced = validate_law_document(
        mutated_payload, mutated_text, relative_specimen.as_posix()
    )
    expected = row["finding"]
    if len(produced) != 1 or produced[0].code != expected:
        observed = [item.code for item in produced]
        return [
            obligation_finding(
                "PM089",
                relative_specimen.as_posix(),
                f"negative specimen produced {observed!r}; expected only {expected}",
                "restore the selected production gate or narrow the specimen to its one expected finding",
                row,
            )
        ]
    return []


def check_obligations(root: Path, law: bytes | None):
    findings: list[Finding] = []
    if law is None:
        return 0, findings
    law_text = law.decode("utf-8")
    marker_ids, marker_findings = discover_obligations(law_text)
    findings.extend(marker_findings)
    registry_path = root / OBLIGATION_PATH
    document, registry_findings = read_json(
        registry_path,
        root,
        max_bytes=MAX_JSON_BYTES,
        missing_code="PM082",
        unsafe_code="PM082",
        malformed_code="PM082",
        noun="Promise Machine obligation registry",
    )
    findings.extend(registry_findings)
    if document is None:
        return len(marker_ids), findings
    if set(document) != {"contract", "schema", "obligations"}:
        findings.append(
            obligation_finding(
                "PM083",
                OBLIGATION_PATH.as_posix(),
                "registry fields are not exactly contract, schema, and obligations",
                "restore the closed promise-machine-obligations/v1 document",
            )
        )
        return len(marker_ids), findings
    if document["contract"] != CONTRACT_ID or document["schema"] != OBLIGATION_SCHEMA:
        findings.append(
            obligation_finding(
                "PM083",
                OBLIGATION_PATH.as_posix(),
                "registry contract or schema identity is unsupported",
                f"declare contract {CONTRACT_ID} and schema {OBLIGATION_SCHEMA}",
            )
        )
    rows = document["obligations"]
    if not isinstance(rows, list) or not rows:
        findings.append(
            obligation_finding(
                "PM083",
                OBLIGATION_PATH.as_posix(),
                "registry obligations must be a non-empty list",
                "register every discovered explicit obligation exactly once",
            )
        )
        return len(marker_ids), findings

    valid_rows: dict[str, dict] = {}
    for index, row in enumerate(rows):
        path = f"{OBLIGATION_PATH.as_posix()}#obligations[{index}]"
        if not isinstance(row, dict) or set(row) != OBLIGATION_ROW_KEYS:
            findings.append(
                obligation_finding(
                    "PM084",
                    path,
                    "registry row does not have the exact required fields",
                    "restore id, gate, specimen, finding, consequence, blocked_transition, and recovery",
                    row,
                )
            )
            continue
        obligation_id = row["id"]
        strings = ("id", "gate", "specimen", "finding", "blocked_transition", "recovery")
        if any(
            not isinstance(row[key], str)
            or not row[key]
            or row[key] != row[key].strip()
            for key in strings
        ) or PROMISE_ID.fullmatch(obligation_id) is None:
            findings.append(
                obligation_finding(
                    "PM084",
                    path,
                    "registry row has an invalid or empty scalar field",
                    "use a stable kebab-case id and non-empty exact string fields",
                    row,
                )
            )
            continue
        consequence = row["consequence"]
        if type(consequence) is not int or consequence not in range(4):
            findings.append(
                obligation_finding(
                    "PM084",
                    path,
                    "registry consequence is not an integer from 0 through 3",
                    "record the root-law consequence level for the blocked transition",
                    row,
                )
            )
            continue
        if obligation_id in valid_rows:
            findings.append(
                obligation_finding(
                    "PM085",
                    path,
                    f"registry contains a duplicate obligation row: {obligation_id}",
                    "retain exactly one row for the stable obligation id",
                    row,
                )
            )
            continue
        valid_rows[obligation_id] = row

    row_ids = set(valid_rows)
    for obligation_id in sorted(marker_ids - row_ids):
        findings.append(
            obligation_finding(
                "PM085",
                OBLIGATION_PATH.as_posix(),
                f"discovered obligation has no registry row: {obligation_id}",
                "add its gate and hostile specimen in the same change",
                {"id": obligation_id},
            )
        )
    for obligation_id in sorted(row_ids - marker_ids):
        findings.append(
            obligation_finding(
                "PM085",
                OBLIGATION_PATH.as_posix(),
                f"registry-only obligation has no authored law marker: {obligation_id}",
                "restore the matching explicit law clause or retire the row with its owning change",
                valid_rows[obligation_id],
            )
        )

    for obligation_id in sorted(row_ids & marker_ids):
        row = valid_rows[obligation_id]
        expected_code = OBLIGATION_GATE_CODES.get(row["gate"])
        if expected_code is None:
            findings.append(
                obligation_finding(
                    "PM086",
                    OBLIGATION_PATH.as_posix(),
                    f"obligation gate selector is unknown: {row['gate']}",
                    "bind the row to a production Promise Machine gate",
                    row,
                )
            )
            continue
        if row["finding"] != expected_code:
            findings.append(
                obligation_finding(
                    "PM086",
                    OBLIGATION_PATH.as_posix(),
                    f"gate {row['gate']} emits {expected_code}, not {row['finding']}",
                    "record the selected production gate's stable finding code",
                    row,
                )
            )
            continue
        findings.extend(validate_obligation_specimen(root, law_text, row))
    return len(marker_ids), findings


def discover_plugins(root: Path):
    findings: list[Finding] = []
    plugins_root = root / "plugins"
    if plugins_root.is_symlink() or not confined(plugins_root, root):
        findings.append(
            Finding(
                "PM011",
                "identity",
                "plugins",
                "plugin root is a symlink or resolves outside the repository",
                "restore plugins as a regular directory beneath the repository",
            )
        )
        return [], findings
    if not plugins_root.is_dir():
        findings.append(
            Finding(
                "PM010",
                "structural",
                "plugins",
                "no plugin directory exists",
                "restore the repository plugin tree",
            )
        )
        return [], findings

    plugins: list[Path] = []
    for entry in sorted(plugins_root.iterdir(), key=lambda item: item.name):
        if entry.is_symlink():
            findings.append(
                Finding(
                    "PM011",
                    "identity",
                    relative(entry, root),
                    "plugin directory is a symlink",
                    "replace it with a regular directory inside plugins",
                )
            )
            continue
        if not entry.is_dir():
            continue
        manifests = [entry / item for item in PLUGIN_MANIFESTS]
        present = [item for item in manifests if item.exists() or item.is_symlink()]
        if not present:
            continue
        documents = []
        for manifest in manifests:
            document, manifest_findings = read_json(manifest, root)
            findings.extend(manifest_findings)
            if document is not None:
                documents.append((manifest, document))
        for manifest, document in documents:
            if document.get("name") != entry.name:
                findings.append(
                    Finding(
                        "PM023",
                        "identity",
                        relative(manifest, root),
                        f"manifest name is {document.get('name')!r}; expected {entry.name!r}",
                        "make the manifest name match its fixed plugin directory",
                    )
                )
        plugins.append(entry)
    if not plugins:
        findings.append(
            Finding(
                "PM010",
                "structural",
                "plugins",
                "plugin discovery returned an empty set",
                "restore at least one manifested plugin; empty discovery never passes",
            )
        )
    return plugins, findings


def walk_skill_files(skill_root: Path, root: Path):
    findings: list[Finding] = []
    found: list[Path] = []
    if skill_root.is_symlink() or not confined(skill_root, root):
        return found, [
            Finding(
                "PM025",
                "identity",
                relative(skill_root, root),
                "skill root is a symlink or resolves outside the repository",
                "restore a regular skills directory inside the plugin",
            )
        ]
    if not skill_root.is_dir():
        return found, findings
    for directory, names, files in os.walk(skill_root, followlinks=False):
        base = Path(directory)
        kept = []
        for name in sorted(names):
            child = base / name
            if child.is_symlink():
                findings.append(
                    Finding(
                        "PM025",
                        "identity",
                        relative(child, root),
                        "skill directory is a symlink",
                        "replace it with a regular directory inside the plugin",
                    )
                )
            else:
                kept.append(name)
        names[:] = kept
        if "SKILL.md" in files:
            candidate = base / "SKILL.md"
            if candidate.is_symlink() or not confined(candidate, root):
                findings.append(
                    Finding(
                        "PM025",
                        "identity",
                        relative(candidate, root),
                        "canonical skill is a symlink or resolves outside the repository",
                        "restore a regular canonical SKILL.md",
                    )
                )
            else:
                found.append(candidate)
    return sorted(found), findings


def ownership_for(skill_path: Path, plugin: Path, root: Path):
    evolution = skill_path.parent / "EVOLUTION.md"
    if evolution.is_symlink():
        return "unclassified", relative(evolution, root), [
            Finding(
                "PM025",
                "identity",
                relative(evolution, root),
                "evolution ownership marker is a symlink",
                "restore a regular evolution ledger",
            )
        ]
    if evolution.is_file():
        return "first-party", relative(evolution, root), []

    current = skill_path.parent
    partial = None
    while True:
        notice = current / "NOTICE.md"
        licence = current / "LICENSE"
        if notice.exists() or notice.is_symlink() or licence.exists() or licence.is_symlink():
            partial = current
            if (
                notice.is_file()
                and not notice.is_symlink()
                and licence.is_file()
                and not licence.is_symlink()
                and confined(notice, root)
                and confined(licence, root)
            ):
                loaded, read_findings = read_markdown(
                    notice, root, missing_code="PM026", unsafe_code="PM025"
                )
                if loaded is None:
                    return "unclassified", relative(notice, root), read_findings
                _, text = loaded
                required = (
                    "vendored verbatim",
                    "- Upstream:",
                    "- Release tag:",
                    "- Vendored:",
                )
                if all(item in text for item in required):
                    return "vendored", relative(notice, root), []
            break
        if current == plugin:
            break
        current = current.parent

    if partial is not None:
        return "unclassified", relative(partial, root), [
            Finding(
                "PM026",
                "structural",
                relative(skill_path, root),
                "vendored ownership binding is incomplete",
                "provide a regular licence and notice with upstream, release and vendored provenance",
            )
        ]
    return "unclassified", "", [
        Finding(
            "PM024",
            "identity",
            relative(skill_path, root),
            "canonical skill is neither first-party nor vendored",
            "add a governed evolution ledger or a complete vendored ownership binding",
        )
    ]


def skill_name(skill_path: Path, root: Path):
    loaded, findings = read_markdown(
        skill_path, root, missing_code="PM020", unsafe_code="PM025"
    )
    if loaded is None:
        return skill_path.parent.name, findings
    _, text = loaded
    frontmatter = frontmatter_lines(text)
    names = [] if frontmatter is None else [
        match.group(1).strip().strip("'\"")
        for line in frontmatter
        if (match := re.fullmatch(r"name:\s*(.+)", line)) is not None
    ]
    name = names[0] if len(names) == 1 else ""
    if len(names) != 1 or name != skill_path.parent.name:
        findings.append(
            Finding(
                "PM023",
                "identity",
                relative(skill_path, root),
                f"canonical frontmatter names are {names!r}; expected only {skill_path.parent.name!r}",
                "make frontmatter name match the canonical parent directory",
            )
        )
    return name or skill_path.parent.name, findings


def discover_inventory(root: Path):
    plugins, findings = discover_plugins(root)
    records: list[SkillRecord] = []
    for plugin in plugins:
        paths, walk_findings = walk_skill_files(plugin / "skills", root)
        findings.extend(walk_findings)
        for path in paths:
            name, name_findings = skill_name(path, root)
            findings.extend(name_findings)
            governance, ownership, ownership_findings = ownership_for(path, plugin, root)
            findings.extend(ownership_findings)
            records.append(
                SkillRecord(
                    name=name,
                    path=relative(path, root),
                    plugin=plugin.name,
                    governance=governance,
                    ownership=ownership,
                )
            )
    if not records:
        findings.append(
            Finding(
                "PM020",
                "structural",
                "plugins/*/skills",
                "canonical skill discovery returned an empty set",
                "restore at least one canonical SKILL.md; empty discovery never passes",
            )
        )

    router_root = root / ".agents" / "skills"
    routers: list[str] = []
    if router_root.exists() or router_root.is_symlink():
        if router_root.is_symlink() or not confined(router_root, root):
            findings.append(
                Finding(
                    "PM025",
                    "identity",
                    relative(router_root, root),
                    "portable router root is a symlink or resolves outside the repository",
                    "restore a regular .agents/skills directory",
                )
            )
        elif router_root.is_dir():
            for entry in sorted(router_root.iterdir(), key=lambda item: item.name):
                if entry.is_symlink() or not confined(entry, root):
                    findings.append(
                        Finding(
                            "PM025",
                            "identity",
                            relative(entry, root),
                            "portable router directory is a symlink or resolves outside the repository",
                            "restore a regular router directory inside .agents/skills",
                        )
                    )
                    continue
                if not entry.is_dir():
                    continue
                router = entry / "SKILL.md"
                if router.is_symlink() or not confined(router, root):
                    findings.append(
                        Finding(
                            "PM025",
                            "identity",
                            relative(router, root),
                            "portable router is a symlink or resolves outside the repository",
                            "restore a regular router SKILL.md",
                        )
                    )
                elif router.is_file():
                    routers.append(relative(router, root))
            if not routers:
                findings.append(
                    Finding(
                        "PM027",
                        "structural",
                        relative(router_root, root),
                        "portable router discovery returned an empty set",
                        "restore at least one portable router or remove the empty surface",
                    )
                )
    overlays = []
    for plugin in plugins:
        overlay = plugin / "PROMISES.md"
        if not (overlay.exists() or overlay.is_symlink()):
            continue
        if overlay.is_symlink() or not confined(overlay, root):
            findings.append(
                Finding(
                    "PM025",
                    "identity",
                    relative(overlay, root),
                    "promise overlay is a symlink or resolves outside the repository",
                    "restore a regular plugin-local PROMISES.md",
                )
            )
        elif overlay.is_file():
            overlays.append(relative(overlay, root))
        else:
            findings.append(
                Finding(
                    "PM025",
                    "structural",
                    relative(overlay, root),
                    "promise overlay is not a regular file",
                    "restore a regular plugin-local PROMISES.md",
                )
            )
    inventory = Inventory(
        plugins=tuple(relative(plugin, root) for plugin in plugins),
        skills=tuple(records),
        routers=tuple(routers),
        overlays=tuple(overlays),
    )
    return inventory, findings


def parse_contract(skill: SkillRecord, root: Path, *, required: bool = False):
    path = root / skill.path
    loaded, findings = read_markdown(
        path, root, missing_code="PM020", unsafe_code="PM025"
    )
    if loaded is None:
        return [], findings
    _, text = loaded
    lines = text.splitlines()
    headings = [index for index, line in enumerate(lines) if line == "## Promise Machine contract"]
    if not headings:
        if required:
            findings.append(
                Finding(
                    "PM031",
                    "structural",
                    skill.path,
                    "required Promise Machine contract section is absent",
                    "add one contract section with at least one stable promise block",
                )
            )
        return [], findings
    if len(headings) != 1:
        findings.append(
            Finding(
                "PM030",
                "structural",
                skill.path,
                "Promise Machine contract heading must occur exactly once",
                "keep one contract section in the canonical skill",
            )
        )
        return [], findings
    start = headings[0] + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    blocks = [index for index in range(start, end) if lines[index].startswith("### ")]
    if not blocks:
        findings.append(
            Finding(
                "PM031",
                "structural",
                skill.path,
                "contract section contains no promise declaration",
                "add at least one stable level-three promise block",
            )
        )
        return [], findings
    promises = []
    for offset, block_start in enumerate(blocks):
        block_end = blocks[offset + 1] if offset + 1 < len(blocks) else end
        promise_id = lines[block_start][4:].strip()
        if not PROMISE_ID.fullmatch(promise_id):
            findings.append(
                Finding(
                    "PM032",
                    "structural",
                    skill.path,
                    "promise id is not a stable lowercase hyphenated identifier",
                    "use a lowercase identifier made of letters, digits and hyphens",
                    promise_id=promise_id or None,
                )
            )
        fields: dict[str, list[str]] = {}
        for line in lines[block_start + 1 : block_end]:
            match = re.fullmatch(r"- \*\*([^*]+):\*\*\s*(.*)", line)
            if match is None:
                match = re.fullmatch(r"- ([^:]+):\s*(.*)", line)
            if match is not None:
                fields.setdefault(match.group(1).strip(), []).append(match.group(2).strip())
        unknown = sorted(set(fields) - set(REQUIRED_FIELDS))
        if unknown:
            findings.append(
                Finding(
                    "PM033",
                    "structural",
                    skill.path,
                    f"promise declaration contains unknown fields: {unknown!r}",
                    "use only the nine promise declaration fields",
                    promise_id=promise_id or None,
                )
            )
        for field in REQUIRED_FIELDS:
            values = fields.get(field, [])
            if len(values) != 1 or not values[0]:
                findings.append(
                    Finding(
                        "PM034",
                        "structural",
                        skill.path,
                        f"promise field must occur once and be non-empty: {field}",
                        f"provide exactly one non-empty {field} field",
                        promise_id=promise_id or None,
                    )
                )
        evidence_values = fields.get("Evidence classes", [])
        classes: list[str] = []
        if len(evidence_values) == 1:
            classes = [
                item.strip().strip("`").split(":", 1)[0].strip()
                for item in re.split(r"[,;]", evidence_values[0])
                if item.strip()
            ]
            unsupported = sorted(set(classes) - SUPPORTED_EVIDENCE_CLASSES)
            if not classes or unsupported:
                findings.append(
                    Finding(
                        "PM036",
                        "structural",
                        skill.path,
                        f"unsupported evidence classes: {unsupported or ['<empty>']!r}",
                        "use a recognised base evidence class from the law",
                        promise_id=promise_id or None,
                    )
                )
        consequences = fields.get("Consequence", [])
        if len(consequences) == 1 and consequences[0] not in {"0", "1", "2", "3"}:
            findings.append(
                Finding(
                    "PM037",
                    "structural",
                    skill.path,
                    f"unsupported consequence level: {consequences[0]!r}",
                    "use consequence level 0, 1, 2 or 3",
                    promise_id=promise_id or None,
                )
            )
        exceptions = fields.get("Exceptions", [])
        if len(exceptions) == 1 and exceptions[0].lower() != "none":
            required = ("authority", "scope", "record", "expiry")
            absent = [
                item
                for item in required
                if re.search(
                    rf"(?:^|;)\s*{item}\s*(?::|=)\s*[^;\s].*?(?=;|$)",
                    exceptions[0],
                    re.IGNORECASE,
                )
                is None
            ]
            if absent:
                findings.append(
                    Finding(
                        "PM038",
                        "structural",
                        skill.path,
                        f"exception omits required attribution: {absent!r}",
                        "name authority, scope, record and expiry, or declare none",
                        promise_id=promise_id or None,
                    )
                )
        consequence = (
            int(consequences[0])
            if len(consequences) == 1 and consequences[0] in {"0", "1", "2", "3"}
            else -1
        )
        promises.append((promise_id, skill.path, frozenset(classes), consequence))
    return promises, findings


def check_structure(
    root: Path,
    inventory: Inventory,
    *,
    require_standalone_contracts: bool = False,
    require_hexaemeron_contracts: bool = False,
):
    findings: list[Finding] = []
    promises: list[tuple[str, str, frozenset[str], int]] = []
    for skill in inventory.skills:
        if skill.governance == "vendored":
            loaded, read_findings = read_markdown(
                root / skill.path,
                root,
                missing_code="PM020",
                unsafe_code="PM025",
            )
            findings.extend(read_findings)
            if loaded is not None and "## Promise Machine contract" in loaded[1].splitlines():
                findings.append(
                    Finding(
                        "PM029",
                        "structural",
                        skill.path,
                        "vendored instruction authors a Promise Machine contract",
                        "remove the local contract and bind the unchanged instruction through a first-party overlay",
                    )
                )
            continue
        if skill.governance != "first-party":
            continue
        parsed, parsed_findings = parse_contract(
            skill,
            root,
            required=(
                require_standalone_contracts and skill.plugin != "hexaemeron"
            )
            or (
                require_hexaemeron_contracts and skill.plugin == "hexaemeron"
            ),
        )
        promises.extend(parsed)
        findings.extend(parsed_findings)
    owners: dict[str, list[str]] = {}
    for promise_id, path, _, _ in promises:
        owners.setdefault(promise_id, []).append(path)
    for promise_id, paths in sorted(owners.items()):
        if len(paths) > 1:
            for path in paths:
                findings.append(
                    Finding(
                        "PM035",
                        "identity",
                        path,
                        f"promise id is duplicated across canonical skills: {paths!r}",
                        "give every suite promise a unique stable id",
                        promise_id=promise_id,
                    )
                )
    return len(promises), findings


def check_overlays(root: Path, inventory: Inventory):
    findings: list[Finding] = []
    expected_overlay = OVERLAY_PATH.as_posix()
    discovered = set(inventory.overlays)
    if expected_overlay not in discovered:
        findings.append(
            Finding(
                "PM050",
                "structural",
                expected_overlay,
                "required Hexaemeron vendored-promise overlay is absent",
                "add the fixed first-party overlay for every vendored skill",
            )
        )
    for unexpected in sorted(discovered - {expected_overlay}):
        findings.append(
            Finding(
                "PM051",
                "identity",
                unexpected,
                "promise overlay exists outside the fixed Hexaemeron boundary",
                "remove the unexpected overlay or record a new first-party boundary in the law",
            )
        )

    if expected_overlay not in discovered:
        return 0, findings

    path = root / OVERLAY_PATH
    loaded, read_findings = read_markdown(
        path, root, missing_code="PM050", unsafe_code="PM025"
    )
    findings.extend(read_findings)
    if loaded is None:
        return 0, findings
    _, text = loaded
    lines = text.splitlines()
    if lines.count(OVERLAY_HEADING) != 1:
        findings.append(
            Finding(
                "PM052",
                "structural",
                expected_overlay,
                f"overlay heading must occur once: {OVERLAY_HEADING}",
                "restore the single Hexaemeron overlay heading",
            )
        )

    heading_index = lines.index(OVERLAY_HEADING) if OVERLAY_HEADING in lines else 0
    section_end = next(
        (
            index
            for index in range(heading_index + 1, len(lines))
            if lines[index].startswith("# ") or lines[index].startswith("## ")
        ),
        len(lines),
    )
    blocks = [
        index
        for index in range(heading_index + 1, section_end)
        if lines[index].startswith("### ")
    ]
    if not blocks:
        findings.append(
            Finding(
                "PM052",
                "structural",
                expected_overlay,
                "overlay contains no vendored promise block",
                "add one digest-bound block for every vendored skill",
            )
        )
        return 0, findings

    skills = {item.path: item for item in inventory.skills}
    vendored = {item.path for item in inventory.skills if item.governance == "vendored"}
    canonical_ids: set[str] = set()
    for skill in inventory.skills:
        if skill.governance != "first-party":
            continue
        parsed, _ = parse_contract(skill, root)
        canonical_ids.update(promise_id for promise_id, _, _, _ in parsed)
    seen_paths: dict[str, list[str]] = {}
    seen_ids: set[str] = set()
    for offset, block_start in enumerate(blocks):
        block_end = blocks[offset + 1] if offset + 1 < len(blocks) else len(lines)
        promise_id = lines[block_start][4:].strip()
        if not PROMISE_ID.fullmatch(promise_id):
            findings.append(
                Finding(
                    "PM032",
                    "structural",
                    expected_overlay,
                    "overlay promise id is not a stable lowercase hyphenated identifier",
                    "use a lowercase identifier made of letters, digits and hyphens",
                    promise_id=promise_id or None,
                )
            )
        if promise_id in seen_ids or promise_id in canonical_ids:
            findings.append(
                Finding(
                    "PM035",
                    "identity",
                    expected_overlay,
                    "overlay promise id is duplicated across the suite",
                    "give every suite promise one unique stable promise id",
                    promise_id=promise_id or None,
                )
            )
        seen_ids.add(promise_id)

        fields: dict[str, list[str]] = {}
        for line in lines[block_start + 1 : block_end]:
            match = re.fullmatch(r"- \*\*([^*]+):\*\*\s*(.*)", line)
            if match is None:
                match = re.fullmatch(r"- ([^:]+):\s*(.*)", line)
            if match is not None:
                fields.setdefault(match.group(1).strip(), []).append(match.group(2).strip())
        unknown = sorted(set(fields) - set(OVERLAY_FIELDS))
        if unknown:
            findings.append(
                Finding(
                    "PM053",
                    "structural",
                    expected_overlay,
                    f"overlay declaration contains unknown fields: {unknown!r}",
                    "use only Path, SHA-256 and the nine promise fields",
                    promise_id=promise_id or None,
                )
            )
        for field in OVERLAY_FIELDS:
            values = fields.get(field, [])
            if len(values) != 1 or not values[0]:
                findings.append(
                    Finding(
                        "PM054",
                        "structural",
                        expected_overlay,
                        f"overlay field must occur once and be non-empty: {field}",
                        f"provide exactly one non-empty {field} field",
                        promise_id=promise_id or None,
                    )
                )

        declared_paths = fields.get("Path", [])
        if len(declared_paths) == 1:
            declared = declared_paths[0].strip("`")
            seen_paths.setdefault(declared, []).append(promise_id)
            skill = skills.get(declared)
            if skill is None:
                findings.append(
                    Finding(
                        "PM055",
                        "identity",
                        expected_overlay,
                        f"overlay path is not a discovered canonical skill: {declared!r}",
                        "bind the block to one discovered vendored SKILL.md path",
                        promise_id=promise_id or None,
                    )
                )
            elif skill.governance != "vendored":
                findings.append(
                    Finding(
                        "PM055",
                        "identity",
                        expected_overlay,
                        f"overlay path belongs to a {skill.governance} skill: {declared!r}",
                        "put first-party promises in the canonical SKILL.md itself",
                        promise_id=promise_id or None,
                    )
                )
            target = root / declared
            if (
                Path(declared).is_absolute()
                or ".." in Path(declared).parts
                or target.is_symlink()
                or not confined(target, root)
                or not target.is_file()
            ):
                findings.append(
                    Finding(
                        "PM055",
                        "identity",
                        expected_overlay,
                        f"overlay path is unsafe or absent: {declared!r}",
                        "use the confined regular path of the vendored SKILL.md",
                        promise_id=promise_id or None,
                    )
                )
            digests = fields.get("SHA-256", [])
            if len(digests) == 1:
                digest = digests[0].strip("`")
                if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    findings.append(
                        Finding(
                            "PM056",
                            "structural",
                            expected_overlay,
                            "overlay SHA-256 is not 64 lowercase hexadecimal characters",
                            "record the full lowercase SHA-256 of the vendored instruction bytes",
                            promise_id=promise_id or None,
                        )
                    )
                elif target.is_file() and not target.is_symlink() and confined(target, root):
                    target_loaded, target_findings = read_markdown(
                        target, root, missing_code="PM055", unsafe_code="PM055"
                    )
                    findings.extend(target_findings)
                    actual = (
                        hashlib.sha256(target_loaded[0]).hexdigest()
                        if target_loaded is not None
                        else ""
                    )
                    if actual != digest:
                        findings.append(
                            Finding(
                                "PM057",
                                "drift",
                                declared,
                                f"vendored instruction digest is {actual}; overlay records {digest}",
                                "review the upstream change and update the first-party overlay deliberately",
                                promise_id=promise_id or None,
                            )
                        )

        evidence_values = fields.get("Evidence classes", [])
        if len(evidence_values) == 1:
            classes = [
                item.strip().strip("`").split(":", 1)[0].strip()
                for item in re.split(r"[,;]", evidence_values[0])
                if item.strip()
            ]
            unsupported = sorted(set(classes) - SUPPORTED_EVIDENCE_CLASSES)
            if not classes or unsupported:
                findings.append(
                    Finding(
                        "PM036",
                        "structural",
                        expected_overlay,
                        f"unsupported evidence classes: {unsupported or ['<empty>']!r}",
                        "use a recognised base evidence class from the law",
                        promise_id=promise_id or None,
                    )
                )
        consequences = fields.get("Consequence", [])
        if len(consequences) == 1 and consequences[0] not in {"0", "1", "2", "3"}:
            findings.append(
                Finding(
                    "PM037",
                    "structural",
                    expected_overlay,
                    f"unsupported consequence level: {consequences[0]!r}",
                    "use consequence level 0, 1, 2 or 3",
                    promise_id=promise_id or None,
                )
            )
        exceptions = fields.get("Exceptions", [])
        if len(exceptions) == 1 and exceptions[0].lower() != "none":
            required = ("authority", "scope", "record", "expiry")
            absent = [
                item
                for item in required
                if re.search(
                    rf"(?:^|;)\s*{item}\s*(?::|=)\s*[^;\s].*?(?=;|$)",
                    exceptions[0],
                    re.IGNORECASE,
                )
                is None
            ]
            if absent:
                findings.append(
                    Finding(
                        "PM038",
                        "structural",
                        expected_overlay,
                        f"exception omits required attribution: {absent!r}",
                        "name authority, scope, record and expiry, or declare none",
                        promise_id=promise_id or None,
                    )
                )

    for declared, owners in sorted(seen_paths.items()):
        if len(owners) > 1:
            findings.append(
                Finding(
                    "PM058",
                    "identity",
                    expected_overlay,
                    f"vendored path has multiple overlays: {declared!r} -> {owners!r}",
                    "retain exactly one promise block for each vendored path",
                )
            )
    declared_set = set(seen_paths)
    for missing in sorted(vendored - declared_set):
        findings.append(
            Finding(
                "PM059",
                "structural",
                missing,
                "vendored skill has no digest-bound Promise Machine overlay",
                "add one first-party overlay block for the vendored path",
            )
        )
    for extra in sorted(declared_set - vendored):
        if extra in skills:
            continue
        findings.append(
            Finding(
                "PM055",
                "identity",
                expected_overlay,
                f"overlay does not belong to the vendored inventory: {extra!r}",
                "remove the block or correct its path to a discovered vendored skill",
            )
        )
    return len(blocks), findings


def promise_records(root: Path, inventory: Inventory):
    records: list[PromiseRecord] = []
    for skill in inventory.skills:
        if skill.governance != "first-party":
            continue
        parsed, _ = parse_contract(skill, root)
        group = "prompt" if skill.name in PROMPT_SKILLS else "executable"
        records.extend(
            PromiseRecord(
                promise_id, skill.path, group, evidence_classes, consequence
            )
            for promise_id, _, evidence_classes, consequence in parsed
        )

    loaded, _ = read_markdown(
        root / OVERLAY_PATH, root, missing_code="PM060", unsafe_code="PM060"
    )
    if loaded is not None:
        lines = loaded[1].splitlines()
        heading_index = lines.index(OVERLAY_HEADING) if OVERLAY_HEADING in lines else 0
        section_end = next(
            (
                index
                for index in range(heading_index + 1, len(lines))
                if lines[index].startswith("# ") or lines[index].startswith("## ")
            ),
            len(lines),
        )
        blocks = [
            index
            for index in range(heading_index + 1, section_end)
            if lines[index].startswith("### ")
        ]
        for offset, block_start in enumerate(blocks):
            block_end = blocks[offset + 1] if offset + 1 < len(blocks) else len(lines)
            promise_id = lines[block_start][4:].strip()
            declared = ""
            evidence_classes: frozenset[str] = frozenset()
            consequence = -1
            for line in lines[block_start + 1 : block_end]:
                match = re.fullmatch(r"- Path:\s*`?([^`]+?)`?\s*", line)
                if match is not None:
                    declared = match.group(1).strip()
                evidence_match = re.fullmatch(r"- Evidence classes:\s*(.+)", line)
                if evidence_match is not None:
                    evidence_classes = frozenset(
                        item.strip().strip("`").split(":", 1)[0].strip()
                        for item in re.split(r"[,;]", evidence_match.group(1))
                        if item.strip()
                    )
                consequence_match = re.fullmatch(r"- Consequence:\s*([0-3])\s*", line)
                if consequence_match is not None:
                    consequence = int(consequence_match.group(1))
            records.append(
                PromiseRecord(
                    promise_id, declared, "vendored", evidence_classes, consequence
                )
            )
    return tuple(sorted(records, key=lambda item: item.promise_id))


def parse_groups(raw: str):
    groups = {item.strip() for item in raw.split(",") if item.strip()}
    unknown = sorted(groups - {"executable", "prompt", "vendored"})
    if unknown or not groups:
        raise ValueError(f"unsupported --group value(s): {unknown or ['<empty>']}")
    return groups


def selector_resolves(path: Path, text: str, selector: str):
    if path.suffix == ".py":
        pattern = rf"^\s*def\s+{re.escape(selector)}\s*\("
    elif path.suffix == ".sol":
        pattern = rf"^\s*function\s+{re.escape(selector)}\s*\("
    else:
        return False
    return re.search(pattern, text, re.MULTILINE) is not None


def check_coverage(root: Path, inventory: Inventory, selected_groups: set[str]):
    findings: list[Finding] = []
    expected_records = promise_records(root, inventory)
    expected = {item.promise_id: item for item in expected_records}
    required_handoffs = {
        pair for pair in REQUIRED_HANDOFFS if pair[0] in expected and pair[1] in expected
    }
    document, read_findings = read_json(
        root / COVERAGE_PATH,
        root,
        max_bytes=MAX_COVERAGE_BYTES,
        missing_code="PM060",
        unsafe_code="PM060",
        malformed_code="PM061",
        noun="coverage file",
    )
    findings.extend(read_findings)
    if document is None:
        return 0, 0, findings
    if document.get("contract") != CONTRACT_ID or document.get("schema") != COVERAGE_SCHEMA:
        findings.append(
            Finding(
                "PM061",
                "structural",
                COVERAGE_PATH.as_posix(),
                "coverage contract or schema identity is absent or unsupported",
                f"use contract {CONTRACT_ID!r} and schema {COVERAGE_SCHEMA!r}",
            )
        )
    handoffs = document.get("handoffs")
    seen_handoffs: set[tuple[str, str]] = set()
    if not isinstance(handoffs, list):
        findings.append(
            Finding(
                "PM068",
                "composition",
                COVERAGE_PATH.as_posix(),
                "coverage handoffs are not an array",
                "record the required producer-to-consumer evidence boundaries",
            )
        )
        handoffs = []
    for index, handoff in enumerate(handoffs):
        handoff_path = f"{COVERAGE_PATH.as_posix()}#handoffs[{index}]"
        required_keys = {"producer", "consumer", "path", "selector", "preserves", "refuses"}
        if not isinstance(handoff, dict) or set(handoff) != required_keys:
            findings.append(
                Finding(
                    "PM068",
                    "composition",
                    handoff_path,
                    "handoff does not have the required evidence-bound shape",
                    "name producer, consumer, exact test, preserved fields and refused overclaim",
                )
            )
            continue
        if not all(
            isinstance(handoff[key], str) and handoff[key].strip()
            for key in ("producer", "consumer", "path", "selector", "refuses")
        ):
            findings.append(
                Finding(
                    "PM068",
                    "composition",
                    handoff_path,
                    "handoff identities and test reference are not non-empty strings",
                    "state concrete producer, consumer, path, selector and refused overclaim",
                )
            )
            continue
        pair = (handoff["producer"], handoff["consumer"])
        seen_handoffs.add(pair)
        preserves = handoff["preserves"]
        if (
            pair not in required_handoffs
            or not isinstance(preserves, list)
            or not preserves
            or any(not isinstance(item, str) or not item for item in preserves)
            or not HANDOFF_PRESERVES.get(pair, set()).issubset(
                set(item for item in preserves if isinstance(item, str))
            )
            or handoff["refuses"] != "answer-truth"
        ):
            findings.append(
                Finding(
                    "PM068",
                    "composition",
                    handoff_path,
                    "handoff does not preserve its declared evidence boundary or refusal",
                    "preserve subject and evidence class without promoting answer truth",
                )
            )
        target = root / handoff["path"]
        loaded, target_findings = read_markdown(
            target, root, missing_code="PM065", unsafe_code="PM065"
        )
        findings.extend(target_findings)
        if loaded is not None and not selector_resolves(
            target, loaded[1], handoff["selector"]
        ):
            findings.append(
                Finding(
                    "PM065",
                    "composition",
                    handoff["path"],
                    f"handoff test selector does not resolve: {handoff['selector']!r}",
                    "cite the exact existing cross-skill test selector",
                )
            )
    for pair in sorted(required_handoffs - seen_handoffs):
        findings.append(
            Finding(
                "PM068",
                "composition",
                COVERAGE_PATH.as_posix(),
                f"required evidence handoff is absent: {pair!r}",
                "add its exact subject, evidence-class and answer-truth guard",
            )
        )
    handoff_counts: dict[tuple[str, str], int] = {}
    for handoff in handoffs:
        if not isinstance(handoff, dict):
            continue
        producer = handoff.get("producer")
        consumer = handoff.get("consumer")
        if isinstance(producer, str) and isinstance(consumer, str):
            pair = (producer, consumer)
            handoff_counts[pair] = handoff_counts.get(pair, 0) + 1
    for pair, count in sorted(handoff_counts.items()):
        if count > 1:
            findings.append(
                Finding(
                    "PM068",
                    "composition",
                    COVERAGE_PATH.as_posix(),
                    f"evidence handoff is repeated {count} times: {pair!r}",
                    "retain one exact record for each required handoff",
                )
            )
    rows = document.get("rows")
    evidence_catalog = document.get("evidence")
    runtime_catalog = document.get("runtime", {})
    if not isinstance(evidence_catalog, dict):
        findings.append(
            Finding(
                "PM061",
                "structural",
                COVERAGE_PATH.as_posix(),
                "coverage evidence catalogue is not an object",
                "provide named exact test references for coverage rows",
            )
        )
        evidence_catalog = {}
    if not isinstance(rows, list):
        findings.append(
            Finding(
                "PM061",
                "structural",
                COVERAGE_PATH.as_posix(),
                "coverage rows are not an array",
                "provide one row object for every discovered promise",
            )
        )
        return 0, 0, findings

    required_runtime = {
        record.promise_id for record in expected_records if record.consequence >= 2
    }
    if not isinstance(runtime_catalog, dict):
        findings.append(
            Finding(
                "PM070",
                "structural",
                COVERAGE_PATH.as_posix(),
                "runtime binding inventory is not an object",
                "map every level-2 or level-3 promise to its result surface and binding fields",
            )
        )
        runtime_catalog = {}
    actual_runtime = set(runtime_catalog)
    for promise_id in sorted(required_runtime - actual_runtime):
        findings.append(
            Finding(
                "PM070",
                "coverage",
                COVERAGE_PATH.as_posix(),
                "level-2 or level-3 promise has no runtime binding",
                "name the existing result surface and all eight Promise Machine bindings",
                promise_id=promise_id,
            )
        )
    for promise_id in sorted(actual_runtime - required_runtime):
        findings.append(
            Finding(
                "PM070",
                "coverage",
                COVERAGE_PATH.as_posix(),
                "runtime binding does not belong to a discovered level-2 or level-3 promise",
                "remove the stale binding or correct its promise id",
                promise_id=promise_id,
            )
        )
    for promise_id in sorted(required_runtime & actual_runtime):
        binding = runtime_catalog[promise_id]
        binding_path = f"{COVERAGE_PATH.as_posix()}#runtime.{promise_id}"
        if not isinstance(binding, dict) or set(binding) != {
            "source",
            "sha256",
            "bindings",
        }:
            findings.append(
                Finding(
                    "PM070",
                    "structural",
                    binding_path,
                    "runtime binding must contain exactly source, sha256 and bindings",
                    "name one digest-bound result schema, writer or contract and its field map",
                    promise_id=promise_id,
                )
            )
            continue
        source = binding.get("source")
        if not isinstance(source, str) or not source.strip():
            findings.append(
                Finding(
                    "PM070",
                    "structural",
                    binding_path,
                    "runtime binding source is absent",
                    "name the existing result schema, writer or contract",
                    promise_id=promise_id,
                )
            )
        else:
            source_path = Path(source)
            source_target = root / source_path
            if (
                source_path.is_absolute()
                or ".." in source_path.parts
                or source_target.is_symlink()
                or not confined(source_target, root)
                or not source_target.is_file()
            ):
                findings.append(
                    Finding(
                        "PM070",
                        "identity",
                        binding_path,
                        f"runtime binding source does not resolve inside the repository: {source!r}",
                        "name a confined existing result schema, writer or contract",
                        promise_id=promise_id,
                    )
                )
            else:
                digest = binding.get("sha256")
                if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    findings.append(
                        Finding(
                            "PM070",
                            "structural",
                            binding_path,
                            "runtime binding source digest is absent or malformed",
                            "record the full lowercase SHA-256 of the reviewed source bytes",
                            promise_id=promise_id,
                        )
                    )
                else:
                    actual, digest_error = bounded_sha256(
                        source_target, MAX_RUNTIME_SOURCE_BYTES
                    )
                    if digest_error is not None:
                        findings.append(
                            Finding(
                                "PM070",
                                "structural",
                                binding_path,
                                f"runtime binding {digest_error}",
                                "name a bounded readable result surface inside the repository",
                                promise_id=promise_id,
                            )
                        )
                    elif actual != digest:
                        findings.append(
                            Finding(
                                "PM071",
                                "drift",
                                binding_path,
                                f"runtime binding source digest is {actual}; inventory records {digest}",
                                "review the changed result surface and update its field map and digest together",
                                promise_id=promise_id,
                            )
                        )
        fields = binding.get("bindings")
        if (
            not isinstance(fields, dict)
            or set(fields) != RUNTIME_BINDING_KEYS
            or any(
                not isinstance(fields.get(key), str) or not fields[key].strip()
                for key in RUNTIME_BINDING_KEYS
            )
        ):
            findings.append(
                Finding(
                    "PM070",
                    "structural",
                    binding_path,
                    "runtime field map is absent, incomplete or contains unknown fields",
                    "bind promise id, subject, scope, evidence references and classes, unknowns, transition and exception",
                    promise_id=promise_id,
                )
            )

    seen: dict[str, int] = {}
    selected = 0
    for index, row in enumerate(rows):
        row_path = f"{COVERAGE_PATH.as_posix()}#rows[{index}]"
        if not isinstance(row, dict):
            findings.append(
                Finding(
                    "PM061",
                    "structural",
                    row_path,
                    "coverage row is not an object",
                    "replace it with a typed coverage row",
                )
            )
            continue
        promise_id = row.get("promise_id")
        if not isinstance(promise_id, str):
            findings.append(
                Finding(
                    "PM061",
                    "structural",
                    row_path,
                    "coverage row has no string promise_id",
                    "name the discovered stable promise id",
                )
            )
            continue
        seen[promise_id] = seen.get(promise_id, 0) + 1
        record = expected.get(promise_id)
        if record is None:
            findings.append(
                Finding(
                    "PM062",
                    "identity",
                    row_path,
                    "coverage row names no discovered promise",
                    "remove the stale row or restore its canonical declaration",
                    promise_id=promise_id,
                )
            )
            continue
        if row.get("skill_path") != record.skill_path or row.get("group") != record.group:
            findings.append(
                Finding(
                    "PM063",
                    "identity",
                    row_path,
                    f"coverage owner or group disagrees with discovery: expected {record.skill_path!r} in {record.group!r}",
                    "derive the owner and group from the canonical declaration",
                    promise_id=promise_id,
                )
            )

        allowed_row_keys = {
            "promise_id",
            "skill_path",
            "group",
            "cases",
            "pending",
            "preserves",
            "evaluation",
        }
        unknown_row_keys = sorted(set(row) - allowed_row_keys)
        if unknown_row_keys:
            findings.append(
                Finding(
                    "PM061",
                    "structural",
                    row_path,
                    f"coverage row contains unknown fields: {unknown_row_keys!r}",
                    "use only the coverage-row fields defined by the checked schema",
                    promise_id=promise_id,
                )
            )

        required_preservation = PRESERVATION_REQUIREMENTS.get(promise_id)
        if required_preservation is not None:
            preserves = row.get("preserves")
            if not isinstance(preserves, list) or not required_preservation.issubset(
                set(item for item in preserves if isinstance(item, str))
            ):
                findings.append(
                    Finding(
                        "PM068",
                        "composition",
                        row_path,
                        f"coverage row omits required preserved boundaries: {sorted(required_preservation)!r}",
                        "retain the producer evidence class, subject and refused overclaim",
                        promise_id=promise_id,
                    )
                )

        cases = row.get("cases")
        if record.group not in selected_groups:
            pending_reason = row.get("pending")
            if cases is None and (
                not isinstance(pending_reason, str) or not pending_reason.strip()
            ):
                findings.append(
                    Finding(
                        "PM066",
                        "coverage",
                        row_path,
                        "unselected incomplete row has no visible pending reason",
                        "state the later runbook step that will classify this row",
                        promise_id=promise_id,
                    )
                )
            continue

        selected += 1
        if record.group in {"prompt", "vendored"}:
            evaluation = row.get("evaluation")
            if (
                not isinstance(evaluation, dict)
                or set(evaluation) != EVALUATION_KEYS
                or evaluation.get("status") not in {"recorded", "unknown"}
                or any(
                    not isinstance(evaluation.get(key), str)
                    or not evaluation[key].strip()
                    for key in EVALUATION_KEYS - {"status"}
                )
            ):
                findings.append(
                    Finding(
                        "PM069",
                        "coverage",
                        row_path,
                        "prompt or vendored evaluation provenance is absent, incomplete or overclaimed",
                        "record status as recorded or unknown and name model, prompt, corpus and disposition",
                        promise_id=promise_id,
                    )
                )
            else:
                corpus_path = Path(evaluation["corpus"])
                corpus_target = root / corpus_path
                if (
                    corpus_path.is_absolute()
                    or ".." in corpus_path.parts
                    or corpus_target.is_symlink()
                    or not confined(corpus_target, root)
                    or not corpus_target.exists()
                    or not (corpus_target.is_file() or corpus_target.is_dir())
                ):
                    findings.append(
                        Finding(
                            "PM069",
                            "coverage",
                            row_path,
                            f"evaluation corpus does not resolve inside the repository: {evaluation['corpus']!r}",
                            "name the exact first-party file or directory that carries the evaluation cases",
                            promise_id=promise_id,
                        )
                    )
        if not isinstance(cases, dict) or set(cases) != set(COVERAGE_CODES):
            findings.append(
                Finding(
                    "PM066",
                    "coverage",
                    row_path,
                    f"selected row must classify exactly {list(COVERAGE_CODES)!r}",
                    "provide evidence or an explicit inapplicability reason for every class",
                    promise_id=promise_id,
                )
            )
            continue
        if "pending" in row:
            findings.append(
                Finding(
                    "PM066",
                    "coverage",
                    row_path,
                    "completed coverage row still carries a pending reason",
                    "remove the stale pending field once every case is classified",
                    promise_id=promise_id,
                )
            )

        references: dict[tuple[str, str], str] = {}
        for code in COVERAGE_CODES:
            raw_case = cases[code]
            case_path = f"{row_path}.{code}"
            if isinstance(raw_case, str):
                case = evidence_catalog.get(raw_case)
                if case is None:
                    findings.append(
                        Finding(
                            "PM064",
                            "coverage",
                            case_path,
                            f"coverage evidence id does not resolve: {raw_case!r}",
                            "cite an existing evidence-catalogue entry",
                            promise_id=promise_id,
                        )
                    )
                    continue
            else:
                case = raw_case
            if not isinstance(case, dict):
                findings.append(
                    Finding(
                        "PM064",
                        "coverage",
                        case_path,
                        "coverage case is not an object",
                        "provide one evidence reference or inapplicability reason",
                        promise_id=promise_id,
                    )
                )
                continue
            if "not_applicable" in case:
                if set(case) != {"not_applicable", "reason"} or case.get("not_applicable") is not True or not isinstance(case.get("reason"), str) or not case["reason"].strip():
                    findings.append(
                        Finding(
                            "PM064",
                            "coverage",
                            case_path,
                            "inapplicability is not an attributed non-empty reason",
                            "set not_applicable true and state why the class cannot apply",
                            promise_id=promise_id,
                        )
                    )
                elif code in {"P", "M", "O", "R"}:
                    findings.append(
                        Finding(
                            "PM066",
                            "coverage",
                            case_path,
                            f"material {code} evidence may not be inapplicable",
                            "cite a distinct positive, missing, overclaim or recovery case",
                            promise_id=promise_id,
                        )
                    )
                continue
            evidence_keys = {"path", "selector", "claim"}
            allowed_evidence_keys = (
                frozenset(evidence_keys),
                frozenset(evidence_keys | {"evidence_class"}),
            )
            if set(case) not in allowed_evidence_keys or not all(
                isinstance(case.get(key), str) and case[key].strip()
                for key in ("path", "selector", "claim")
            ):
                findings.append(
                    Finding(
                        "PM064",
                        "coverage",
                        case_path,
                        "evidence reference must contain non-empty path, selector and claim, with at most one evidence class",
                        "cite one exact existing selector, its bounded interpretation and an optional base evidence class",
                        promise_id=promise_id,
                    )
                )
                continue
            if "evidence_class" in case and (
                not isinstance(case["evidence_class"], str)
                or case["evidence_class"] not in SUPPORTED_EVIDENCE_CLASSES
            ):
                findings.append(
                    Finding(
                        "PM064",
                        "coverage",
                        case_path,
                        f"coverage evidence class is unsupported: {case['evidence_class']!r}",
                        "use one base evidence class from the Promise Machine law",
                        promise_id=promise_id,
                    )
                )
                continue
            if "evidence_class" in case and case["evidence_class"] not in record.evidence_classes:
                findings.append(
                    Finding(
                        "PM064",
                        "coverage",
                        case_path,
                        f"coverage evidence class {case['evidence_class']!r} is not accepted by the promise",
                        f"use one of the promise's declared classes: {sorted(record.evidence_classes)!r}",
                        promise_id=promise_id,
                    )
                )
                continue
            if record.group in {"prompt", "vendored"} and "evidence_class" not in case:
                findings.append(
                    Finding(
                        "PM064",
                        "coverage",
                        case_path,
                        "prompt or vendored evidence omits its base evidence class",
                        "state one class accepted by the canonical promise declaration",
                        promise_id=promise_id,
                    )
                )
                continue
            evidence_path = Path(case["path"])
            target = root / evidence_path
            loaded, target_findings = read_markdown(
                target, root, missing_code="PM065", unsafe_code="PM065"
            )
            findings.extend(target_findings)
            if loaded is not None and not selector_resolves(
                target, loaded[1], case["selector"]
            ):
                findings.append(
                    Finding(
                        "PM065",
                        "coverage",
                        case["path"],
                        f"test selector does not resolve: {case['selector']!r}",
                        "cite an exact function or test name present in the file",
                        promise_id=promise_id,
                    )
                )
            reference = (case["path"], case["selector"])
            if reference in references:
                findings.append(
                    Finding(
                        "PM067",
                        "coverage",
                        case_path,
                        f"one test selector is reused for incompatible {references[reference]} and {code} cases",
                        "cite distinct evidence for each incompatible class",
                        promise_id=promise_id,
                    )
                )
            references[reference] = code

    actual_ids = set(seen)
    for promise_id in sorted(set(expected) - actual_ids):
        findings.append(
            Finding(
                "PM062",
                "coverage",
                COVERAGE_PATH.as_posix(),
                "discovered promise has no coverage row",
                "add the promise without removing any discovered entry",
                promise_id=promise_id,
            )
        )
    for promise_id, count in sorted(seen.items()):
        if count > 1:
            findings.append(
                Finding(
                    "PM062",
                    "identity",
                    COVERAGE_PATH.as_posix(),
                    f"promise has {count} coverage rows",
                    "retain exactly one row for each discovered promise",
                    promise_id=promise_id,
                )
            )
    return len(rows), selected, findings


def check_identity(inventory: Inventory):
    findings: list[Finding] = []
    owners: dict[str, list[str]] = {}
    for skill in inventory.skills:
        owners.setdefault(skill.name, []).append(skill.path)
    for name, paths in sorted(owners.items()):
        if len(paths) > 1:
            for path in paths:
                findings.append(
                    Finding(
                        "PM044",
                        "identity",
                        path,
                        f"canonical logical id is duplicated: {paths!r}",
                        "retain one canonical implementation for the logical skill id",
                        promise_id=name,
                    )
                )
    return findings


def check_routers(root: Path, inventory: Inventory):
    findings: list[Finding] = []
    expected_router = ".agents/skills/promise-machine/SKILL.md"
    if inventory.routers != (expected_router,):
        findings.append(
            Finding(
                "PM040",
                "identity",
                ".agents/skills",
                f"portable routers are {list(inventory.routers)!r}; expected only {expected_router!r}",
                "remove duplicate portable catalogues and retain the sole Promise Machine router",
            )
        )
        return findings

    router = root / expected_router
    loaded, read_findings = read_markdown(
        router, root, missing_code="PM040", unsafe_code="PM025"
    )
    findings.extend(read_findings)
    if loaded is None:
        return findings
    _, text = loaded
    frontmatter = frontmatter_lines(text)
    version_lines = [] if frontmatter is None else [
        line for line in frontmatter if re.fullmatch(r"\s*version:\s*.*", line)
    ]
    if version_lines:
        findings.append(
            Finding(
                "PM043",
                "version",
                expected_router,
                "portable router declares a behavioural version",
                "remove the router version; canonical skills own behavioural versions",
            )
        )
    names = [] if frontmatter is None else [
        match.group(1).strip().strip("'\"")
        for line in frontmatter
        if (match := re.fullmatch(r"name:\s*(.+)", line)) is not None
    ]
    if names != ["promise-machine"]:
        findings.append(
            Finding(
                "PM040",
                "identity",
                expected_router,
                "portable router frontmatter does not name promise-machine",
                "restore the fixed router name",
            )
        )

    expected_targets = {root / "AGENTS.md"}
    expected_targets.update(root / plugin / "AGENTS.md" for plugin in inventory.plugins)
    resolved: list[Path] = []
    for link in re.findall(r"\[[^]]+\]\(([^)]+)\)", text):
        if "://" in link or link.startswith("#"):
            findings.append(
                Finding(
                    "PM042",
                    "identity",
                    expected_router,
                    f"portable router contains a non-runtime link: {link!r}",
                    "keep only confined root and plugin runtime-contract links",
                )
            )
            continue
        target = (router.parent / link).resolve(strict=False)
        if not confined(target, root) or not target.is_file():
            findings.append(
                Finding(
                    "PM041",
                    "identity",
                    expected_router,
                    f"portable route does not resolve inside the repository: {link!r}",
                    "point the route at an existing root or plugin AGENTS.md",
                )
            )
            continue
        resolved.append(target)
    actual_targets = set(resolved)
    missing = sorted(relative(path, root) for path in expected_targets - actual_targets)
    extra = sorted(relative(path, root) for path in actual_targets - expected_targets)
    duplicates = sorted(
        relative(path, root) for path in actual_targets if resolved.count(path) != 1
    )
    if missing:
        findings.append(
            Finding(
                "PM041",
                "identity",
                expected_router,
                f"portable router omits runtime contracts: {missing!r}",
                "add one route to the root and every discovered plugin runtime contract",
            )
        )
    if extra or duplicates:
        findings.append(
            Finding(
                "PM042",
                "identity",
                expected_router,
                f"portable router has extra or repeated targets: extra={extra!r} repeated={duplicates!r}",
                "retain exactly one link to each runtime contract",
            )
        )

    for skill in inventory.skills:
        plugin_root = root / "plugins" / skill.plugin
        contract = plugin_root / "AGENTS.md"
        loaded_contract, contract_findings = read_markdown(
            contract, root, missing_code="PM041", unsafe_code="PM025"
        )
        findings.extend(contract_findings)
        if loaded_contract is None:
            continue
        canonical = Path(skill.path).relative_to(Path("plugins") / skill.plugin).as_posix()
        if f"`{canonical}`" not in loaded_contract[1]:
            findings.append(
                Finding(
                    "PM041",
                    "identity",
                    relative(contract, root),
                    f"runtime contract does not resolve canonical skill {canonical!r}",
                    "add the canonical path to the plugin selection table",
                )
            )
    return findings


SEMVER = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def check_versions(root: Path, inventory: Inventory):
    findings: list[Finding] = []
    package_versions = 0
    skill_versions = 0
    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    marketplace, marketplace_findings = read_json(marketplace_path, root)
    findings.extend(marketplace_findings)
    listed_versions: dict[str, str | None] = {}
    if marketplace is not None:
        entries = marketplace.get("plugins")
        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                    name = entry["name"]
                    if name in listed_versions:
                        findings.append(
                            Finding(
                                "PM045",
                                "version",
                                relative(marketplace_path, root),
                                f"package marketplace repeats {name!r}",
                                "retain one versioned marketplace entry per plugin",
                            )
                        )
                    listed_versions[name] = entry.get("version")
        else:
            findings.append(
                Finding(
                    "PM045",
                    "version",
                    relative(marketplace_path, root),
                    "package marketplace plugins value is not a list",
                    "restore the versioned package marketplace list",
                )
            )
    for plugin_path in inventory.plugins:
        plugin = root / plugin_path
        values = []
        for manifest_path in PLUGIN_MANIFESTS:
            manifest, manifest_findings = read_json(plugin / manifest_path, root)
            findings.extend(manifest_findings)
            if manifest is not None:
                value = manifest.get("version")
                if not isinstance(value, str) or SEMVER.fullmatch(value) is None:
                    findings.append(
                        Finding(
                            "PM045",
                            "version",
                            relative(plugin / manifest_path, root),
                            f"package version is not semantic: {value!r}",
                            "state a semantic package version in each host manifest",
                        )
                    )
                else:
                    values.append(value)
        listed = listed_versions.get(plugin.name)
        if not isinstance(listed, str) or SEMVER.fullmatch(listed) is None:
            findings.append(
                Finding(
                    "PM045",
                    "version",
                    relative(marketplace_path, root),
                    f"marketplace package version for {plugin.name!r} is absent or not semantic: {listed!r}",
                    "state the plugin package version in the Claude marketplace",
                )
            )
        if (
            len(values) == len(PLUGIN_MANIFESTS)
            and len(set(values)) == 1
            and listed == values[0]
        ):
            package_versions += 1
        elif values:
            findings.append(
                Finding(
                    "PM045",
                    "version",
                    plugin_path,
                    f"package versions disagree: manifests={values!r} marketplace={listed!r}",
                    "propagate one package version across manifests and marketplace",
                )
            )

    for skill in inventory.skills:
        if skill.governance != "first-party":
            continue
        skill_path = root / skill.path
        loaded, read_findings = read_markdown(
            skill_path, root, missing_code="PM020", unsafe_code="PM025"
        )
        findings.extend(read_findings)
        if loaded is None:
            continue
        frontmatter = frontmatter_lines(loaded[1])
        metadata = [] if frontmatter is None else [
            match.group(1)
            for line in frontmatter
            if (match := re.fullmatch(r'  version: "([^"]+)"', line)) is not None
        ]
        value = metadata[0] if len(metadata) == 1 else None
        if len(metadata) != 1 or value is None or SEMVER.fullmatch(value) is None:
            findings.append(
                Finding(
                    "PM046",
                    "version",
                    skill.path,
                    f"skill metadata versions are absent, duplicated or not semantic: {metadata!r}",
                    "state the canonical skill version as metadata.version without a package namespace",
                )
            )
            continue
        ledger = skill_path.parent / "EVOLUTION.md"
        loaded_ledger, ledger_findings = read_markdown(
            ledger, root, missing_code="PM046", unsafe_code="PM025"
        )
        findings.extend(ledger_findings)
        if loaded_ledger is None:
            continue
        current = re.search(
            rf"(?m)^- Current version: `{re.escape(skill.name)}-v([0-9]+\.[0-9]+\.[0-9]+)`$",
            loaded_ledger[1],
        )
        if current is None or current.group(1) != value:
            findings.append(
                Finding(
                    "PM047",
                    "version",
                    relative(ledger, root),
                    f"skill metadata {value!r} does not match its evolution ledger",
                    "propagate the canonical skill version within the skill layer",
                )
            )
            continue
        skill_versions += 1
    return package_versions, skill_versions, findings


def marketplace_names(root: Path, path: Path, inventory: Inventory, host: str):
    document, findings = read_json(root / path, root)
    names: set[str] = set()
    if document is None:
        return names, findings
    entries = document.get("plugins")
    if not isinstance(entries, list):
        findings.append(
            Finding(
                "PM048",
                "structural",
                path.as_posix(),
                "host marketplace plugins value is not a list",
                "restore the explicit host plugin list",
            )
        )
        return names, findings
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            findings.append(
                Finding(
                    "PM048",
                    "structural",
                    path.as_posix(),
                    "host marketplace contains an unnamed plugin entry",
                    "name every host marketplace entry",
                )
            )
            continue
        name = entry["name"]
        if name in names:
            findings.append(
                Finding(
                    "PM048",
                    "identity",
                    path.as_posix(),
                    f"host marketplace repeats plugin {name!r}",
                    "retain one host entry per plugin",
                )
            )
        names.add(name)
        source = entry.get("source")
        raw = source if host == "claude" else source.get("path") if isinstance(source, dict) else None
        expected = f"./plugins/{name}"
        if raw != expected:
            findings.append(
                Finding(
                    "PM049",
                    "identity",
                    path.as_posix(),
                    f"host source for {name!r} is {raw!r}; expected {expected!r}",
                    "use the fixed repository-relative plugin source",
                )
            )
    expected_names = {Path(plugin).name for plugin in inventory.plugins}
    if names != expected_names:
        findings.append(
            Finding(
                "PM048",
                "identity",
                path.as_posix(),
                f"host set differs from discovered plugins: missing={sorted(expected_names - names)!r} extra={sorted(names - expected_names)!r}",
                "make the host marketplace set equal the discovered plugin set",
            )
        )
    return names, findings


def check_hosts(root: Path, inventory: Inventory):
    claude, claude_findings = marketplace_names(
        root, Path(".claude-plugin/marketplace.json"), inventory, "claude"
    )
    codex, codex_findings = marketplace_names(
        root, Path(".agents/plugins/marketplace.json"), inventory, "codex"
    )
    return len(claude), len(codex), claude_findings + codex_findings


def read_licence(path: Path, root: Path, *, code: str):
    shown = relative(path, root)
    if path.is_symlink() or not confined(path, root):
        return None, [
            Finding(
                code,
                "identity",
                shown,
                "licence path is a symlink or resolves outside the repository",
                "restore a regular licence at the fixed path",
            )
        ]
    if not path.is_file():
        return None, [
            Finding(
                code,
                "structural",
                shown,
                "required first-party licence is absent",
                "restore the Apache-2.0 licence at the fixed path",
            )
        ]
    try:
        payload = path.read_bytes()
    except OSError as exc:
        return None, [
            Finding(
                code,
                "identity",
                shown,
                f"licence could not be read: {exc}",
                "restore a readable regular licence inside the repository",
            )
        ]
    if len(payload) > MAX_LICENSE_BYTES:
        return None, [
            Finding(
                code,
                "structural",
                shown,
                f"licence is {len(payload)} bytes; limit is {MAX_LICENSE_BYTES}",
                "restore the bounded canonical Apache-2.0 licence",
            )
        ]
    return payload, []


def check_licences(root: Path, inventory: Inventory):
    findings: list[Finding] = []
    canonical, read_findings = read_licence(root / LICENSE_NAME, root, code="PM072")
    findings.extend(read_findings)
    if canonical is not None:
        required = (b"Apache License", b"Version 2.0", b"Copyright 2026 Wildcat Labs")
        missing = [marker.decode("ascii") for marker in required if marker not in canonical]
        if missing:
            findings.append(
                Finding(
                    "PM073",
                    "structural",
                    LICENSE_NAME,
                    f"canonical first-party licence lacks markers: {missing!r}",
                    "restore the Apache-2.0 text and Wildcat Labs copyright notice",
                )
            )

    first_party_plugins = sorted(
        {skill.plugin for skill in inventory.skills if skill.governance == "first-party"}
    )
    licensed_plugins = 0
    for name in first_party_plugins:
        plugin = root / "plugins" / name
        plugin_clean = True
        payload, plugin_findings = read_licence(
            plugin / LICENSE_NAME, root, code="PM074"
        )
        findings.extend(plugin_findings)
        if plugin_findings or canonical is None or payload != canonical:
            plugin_clean = False
            if payload is not None and canonical is not None and payload != canonical:
                findings.append(
                    Finding(
                        "PM074",
                        "drift",
                        relative(plugin / LICENSE_NAME, root),
                        "first-party plugin licence differs from the root licence",
                        "restore the byte-identical root Apache-2.0 licence copy",
                    )
                )
        for manifest_path in PLUGIN_MANIFESTS:
            manifest, manifest_findings = read_json(plugin / manifest_path, root)
            findings.extend(manifest_findings)
            if manifest is None:
                plugin_clean = False
                continue
            author = manifest.get("author")
            if (
                manifest.get("license") != "Apache-2.0"
                or not isinstance(author, dict)
                or author.get("name") != "Wildcat Labs"
            ):
                plugin_clean = False
                findings.append(
                    Finding(
                        "PM075",
                        "identity",
                        relative(plugin / manifest_path, root),
                        "first-party host manifest does not name Apache-2.0 and Wildcat Labs",
                        "set license to Apache-2.0 and author.name to Wildcat Labs",
                    )
                )
        if plugin_clean:
            licensed_plugins += 1
    return licensed_plugins, findings


def check_copies(root: Path, law: bytes | None, plugins: list[Path]):
    findings: list[Finding] = []
    if law is None:
        return findings
    for plugin in plugins:
        copy = plugin / LAW_NAME
        loaded, read_findings = read_markdown(
            copy, root, missing_code="PM012", unsafe_code="PM013"
        )
        findings.extend(read_findings)
        if loaded is None:
            continue
        payload, _ = loaded
        if payload != law:
            findings.append(
                Finding(
                    "PM014",
                    "drift",
                    relative(copy, root),
                    "plugin-local law differs from the authored root law",
                    "run scripts/promise_machine.py sync",
                )
            )
    return findings


def atomic_write(path: Path, payload: bytes):
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def sync_copies(root: Path, law: bytes, plugins: list[Path]):
    findings: list[Finding] = []
    written = 0
    for plugin in plugins:
        destination = plugin / LAW_NAME
        if destination.is_symlink() or not confined(destination, root):
            findings.append(
                Finding(
                    "PM013",
                    "identity",
                    relative(destination, root),
                    "copy destination is a symlink or resolves outside the repository",
                    "replace it with a regular fixed destination before synchronising",
                )
            )
            continue
        current = destination.read_bytes() if destination.is_file() else None
        if current == law:
            continue
        try:
            atomic_write(destination, law)
            written += 1
        except OSError as exc:
            findings.append(
                Finding(
                    "PM015",
                    "drift",
                    relative(destination, root),
                    f"atomic copy write failed: {exc}",
                    "restore a writable plugin directory and rerun sync",
                )
            )
    return written, findings


def report(
    command: str,
    root: Path,
    plugins: list[Path],
    findings: list[Finding],
    *,
    as_json: bool,
    written: int = 0,
    copies: int = 0,
    inventory: Inventory | None = None,
    promises: int = 0,
    obligations: int = 0,
    stats: dict[str, int] | None = None,
):
    findings = sorted(findings, key=lambda item: (item.path, item.code, item.message))
    counts = {
        "plugins": len(plugins),
        "copies": copies,
        "written": written,
        "findings": len(findings),
        "canonical_skills": len(inventory.skills) if inventory else 0,
        "governed_skills": (
            sum(item.governance == "first-party" for item in inventory.skills)
            if inventory
            else 0
        ),
        "vendored_skills": (
            sum(item.governance == "vendored" for item in inventory.skills)
            if inventory
            else 0
        ),
        "routers": len(inventory.routers) if inventory else 0,
        "overlays": len(inventory.overlays) if inventory else 0,
        "promises": promises,
        "obligations": obligations,
        "claude_plugins": 0,
        "codex_plugins": 0,
        "package_versions": 0,
        "skill_versions": 0,
        "licensed_plugins": 0,
    }
    if stats:
        counts.update(stats)
    document = {
        "contract": CONTRACT_ID,
        "command": command,
        "ok": not findings,
        "counts": counts,
        "findings": [asdict(item) for item in findings],
    }
    if inventory is not None:
        document["inventory"] = {
            "plugins": list(inventory.plugins),
            "skills": [asdict(item) for item in inventory.skills],
            "routers": list(inventory.routers),
            "overlays": list(inventory.overlays),
        }
    if as_json:
        print(json.dumps(document, sort_keys=True, separators=(",", ":")))
    elif findings:
        for item in findings:
            promise = f" promise={item.promise_id}" if item.promise_id else ""
            obligation = (
                f" obligation={item.obligation_id}" if item.obligation_id else ""
            )
            consequence = (
                f" consequence={item.consequence}"
                if item.consequence is not None
                else ""
            )
            blocked = (
                f" blocked={item.blocked_transition!r}"
                if item.blocked_transition
                else ""
            )
            print(
                f"{item.code} fault={item.fault} path={item.path}{promise}"
                f"{obligation}{consequence}{blocked}: "
                f"{item.message}; repair: {item.remedy}"
            )
        print(f"refused: {len(findings)} finding(s)")
    elif command in {"inventory", "coverage"}:
        keys = (
            (
                "plugins",
                "canonical_skills",
                "governed_skills",
                "vendored_skills",
                "routers",
                "overlays",
            )
            if command == "inventory"
            else ("promises", "coverage_rows", "coverage_selected")
        )
        print(
            "clean: "
            + " ".join(f"{key}={counts[key]}" for key in keys)
        )
    else:
        suffix = f"; wrote {written}" if command == "sync" else ""
        print(f"clean: {len(plugins)} plugin(s), {counts['copies']} copy/copies{suffix}")
    return 0 if not findings else 1


def repository_root(raw: str | None):
    candidate = Path(raw) if raw else Path(__file__).resolve().parents[1]
    if candidate.is_symlink():
        raise ValueError("repository root may not be a symlink")
    return candidate.resolve(strict=True)


def parse_only(raw: str):
    requested = tuple(item.strip() for item in raw.split(",") if item.strip())
    allowed = {
        "law",
        "copies",
        "inventory",
        "structure",
        "contracts",
        "overlays",
        "identity",
        "routers",
        "versions",
        "hosts",
        "coverage",
        "licences",
        "obligations",
    }
    unknown = sorted(set(requested) - allowed)
    if unknown or not requested:
        raise ValueError(f"unsupported --only value(s): {unknown or ['<empty>']}")
    return set(requested)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="write or check fixed plugin copies")
    sync_parser.add_argument("--check", action="store_true", help="check without writing")
    sync_parser.add_argument("--root", help=argparse.SUPPRESS)
    sync_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    check_parser = subparsers.add_parser("check", help="check the law and plugin copies")
    check_parser.add_argument(
        "--only",
        default=(
            "law,copies,inventory,structure,contracts,overlays,identity,routers,"
            "versions,hosts,coverage,licences,obligations"
        ),
    )
    check_parser.add_argument("--root", help=argparse.SUPPRESS)
    check_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    inventory_parser = subparsers.add_parser(
        "inventory", help="discover plugins, canonical skills, routers and overlays"
    )
    inventory_parser.add_argument("--check", action="store_true", help="validate discovery")
    inventory_parser.add_argument("--root", help=argparse.SUPPRESS)
    inventory_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    coverage_parser = subparsers.add_parser(
        "coverage", help="check promise-to-evidence classifications"
    )
    coverage_parser.add_argument("--check", action="store_true")
    coverage_parser.add_argument(
        "--group", default="executable,prompt,vendored", help="comma-separated groups"
    )
    coverage_parser.add_argument("--root", help=argparse.SUPPRESS)
    coverage_parser.add_argument("--json", action="store_true", help="emit canonical JSON")

    args = parser.parse_args(argv)
    try:
        root = repository_root(args.root)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.command == "inventory":
        inventory, findings = discover_inventory(root)
        plugins = [root / path for path in inventory.plugins]
        return report(
            "inventory",
            root,
            plugins,
            findings,
            as_json=args.json,
            inventory=inventory,
        )

    if args.command == "coverage":
        try:
            selected_groups = parse_groups(args.group)
        except ValueError as exc:
            parser.error(str(exc))
        inventory, findings = discover_inventory(root)
        plugins = [root / path for path in inventory.plugins]
        canonical_promises, structure_findings = check_structure(
            root,
            inventory,
            require_standalone_contracts=True,
            require_hexaemeron_contracts=True,
        )
        overlay_promises, overlay_findings = check_overlays(root, inventory)
        coverage_rows, coverage_selected, coverage_findings = check_coverage(
            root, inventory, selected_groups
        )
        findings.extend(structure_findings)
        findings.extend(overlay_findings)
        findings.extend(coverage_findings)
        return report(
            "coverage",
            root,
            plugins,
            findings,
            as_json=args.json,
            inventory=inventory,
            promises=canonical_promises + overlay_promises,
            stats={
                "coverage_rows": coverage_rows,
                "coverage_selected": coverage_selected,
            },
        )

    if args.command == "check":
        try:
            only = parse_only(args.only)
        except ValueError as exc:
            parser.error(str(exc))
        law = None
        findings: list[Finding] = []
        plugins: list[Path] = []
        inventory = None
        promises = 0
        stats: dict[str, int] = {}
        if "law" in only or "copies" in only or "obligations" in only:
            law, law_findings = check_law(root)
            findings.extend(law_findings)
        if "copies" in only:
            plugins, discovery_findings = discover_plugins(root)
            findings.extend(discovery_findings)
            findings.extend(check_copies(root, law, plugins))
        inventory_components = {
            "inventory",
            "structure",
            "contracts",
            "overlays",
            "identity",
            "routers",
            "versions",
            "hosts",
            "coverage",
            "licences",
        }
        if only & inventory_components:
            inventory, inventory_findings = discover_inventory(root)
            findings.extend(inventory_findings)
            plugins = [root / path for path in inventory.plugins]
        if only & {"structure", "contracts", "overlays"} and inventory is not None:
            promises, structure_findings = check_structure(
                root,
                inventory,
                require_standalone_contracts="contracts" in only,
                require_hexaemeron_contracts="overlays" in only,
            )
            findings.extend(structure_findings)
        if "overlays" in only and inventory is not None:
            overlay_promises, overlay_findings = check_overlays(root, inventory)
            promises += overlay_promises
            findings.extend(overlay_findings)
        if "identity" in only and inventory is not None:
            findings.extend(check_identity(inventory))
        if "routers" in only and inventory is not None:
            findings.extend(check_routers(root, inventory))
        if "versions" in only and inventory is not None:
            package_versions, skill_versions, version_findings = check_versions(
                root, inventory
            )
            stats["package_versions"] = package_versions
            stats["skill_versions"] = skill_versions
            findings.extend(version_findings)
        if "hosts" in only and inventory is not None:
            claude_plugins, codex_plugins, host_findings = check_hosts(root, inventory)
            stats["claude_plugins"] = claude_plugins
            stats["codex_plugins"] = codex_plugins
            findings.extend(host_findings)
        if "licences" in only and inventory is not None:
            licensed_plugins, licence_findings = check_licences(root, inventory)
            stats["licensed_plugins"] = licensed_plugins
            findings.extend(licence_findings)
        if "coverage" in only and inventory is not None:
            coverage_rows, coverage_selected, coverage_findings = check_coverage(
                root, inventory, {"executable", "prompt", "vendored"}
            )
            stats["coverage_rows"] = coverage_rows
            stats["coverage_selected"] = coverage_selected
            findings.extend(coverage_findings)
        obligations = 0
        if "obligations" in only:
            obligations, obligation_findings = check_obligations(root, law)
            findings.extend(obligation_findings)
        return report(
            "check",
            root,
            plugins,
            findings,
            as_json=args.json,
            copies=len(plugins) if "copies" in only else 0,
            inventory=inventory,
            promises=promises,
            obligations=obligations,
            stats=stats,
        )

    law, law_findings = check_law(root)
    plugins, discovery_findings = discover_plugins(root)
    findings = list(law_findings) + list(discovery_findings)
    written = 0
    if args.check:
        findings.extend(check_copies(root, law, plugins))
    elif not findings and law is not None:
        written, write_findings = sync_copies(root, law, plugins)
        findings.extend(write_findings)
        findings.extend(check_copies(root, law, plugins))
    return report(
        "sync",
        root,
        plugins,
        findings,
        as_json=args.json,
        written=written,
        copies=len(plugins),
    )


if __name__ == "__main__":
    raise SystemExit(main())
