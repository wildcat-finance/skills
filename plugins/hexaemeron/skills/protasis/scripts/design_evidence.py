#!/usr/bin/env python3
"""Check one closed Protasis design-evidence record.

The record does not ask an author to predict a grade.  It names the candidates,
criteria, reports and unresolved work that make a design choice admissible.
Draft mode checks the closed shape.  A transition check additionally refuses
when evidence owed at that transition is absent or fails its declared gate.

Codes:

  D000  the record cannot be read as one bounded strict JSON object
  D001  a closed object has the wrong schema, fields or bounded value shape
  D002  candidate or criterion ids, counts or concern coverage are invalid
  D003  the candidate-by-criterion matrix is incomplete, duplicated or invalid
  D004  a pending result has no bounded resolver, report path or valid stop point
  D005  a report is unavailable, unsafe, malformed or digest-mismatched
  D006  a resolved state disagrees with the report and declared comparison
  D007  design lock cannot select the recorded candidate under the closed rules
  D008  evidence due at a named later transition is absent or does not pass

Exit 0 clean, 1 findings, 2 bad invocation.  The checker starts no subprocess
and opens no socket.  Record-relative report paths must stay below the record's
directory; every file is a non-symlink regular file below the same byte cap.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
import sys
from pathlib import Path


SCHEMA = "protasis-design-evidence/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
MAX_BYTES = 2 * 1024 * 1024
MAX_REPORT_BYTES = 64 * 1024
MAX_JSON_DEPTH = 64
MAX_CANDIDATES = 4
MIN_CANDIDATES = 2
MAX_CRITERIA = 32
MAX_RESULTS = MAX_CANDIDATES * MAX_CRITERIA
MAX_TEXT_BYTES = 4096
MAX_SUMMARY_BYTES = 512

ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STEP_BLOCK = re.compile(r"^step:(?P<number>[1-9][0-9]{0,3})$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")

CONCERNS = frozenset({"correctness", "time", "space", "compatibility", "recovery"})
KINDS = frozenset({"gate", "metric"})
STAGES = frozenset({"selection", "conformance"})
UNITS = frozenset({"boolean", "bytes", "count", "milliseconds", "ratio", "string"})
NUMERIC_UNITS = frozenset({"bytes", "count", "milliseconds", "ratio"})
GATE_COMPARATORS = frozenset({"at-least", "at-most", "equals"})
METRIC_COMPARATORS = frozenset({"maximise", "minimise"})
STATES = frozenset({"pass", "pending", "fail"})
SELECTION_RULES = frozenset({"unique-frontier", "exact-tie-simplicity", "user-policy"})

TOP_KEYS = frozenset({"schema", "candidates", "criteria", "results", "selection"})
CANDIDATE_KEYS = frozenset({"id", "summary"})
CRITERION_KEYS = frozenset({
    "id", "concern", "kind", "stage", "owner", "unit", "comparator",
    "threshold", "blocks",
})
RESOLVED_KEYS = frozenset({"candidate", "criterion", "state", "report"})
PENDING_KEYS = frozenset({
    "candidate", "criterion", "state", "resolver", "report", "blocks",
})
REPORT_REF_KEYS = frozenset({"path", "sha256"})
SELECTION_KEYS = frozenset({"candidate", "rule", "policy_ref"})
REPORT_KEYS = frozenset({
    "schema", "candidate", "criterion", "value", "unit", "command", "exit",
})


class DuplicateKey(ValueError):
    pass


class Finding:
    __slots__ = ("path", "line", "code", "message")

    def __init__(self, path: Path, code: str, message: str) -> None:
        self.path = path
        self.line = 1
        self.code = code
        self.message = message

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "line": self.line,
            "code": self.code,
            "message": self.message,
        }

    def __str__(self) -> str:
        return f"{self.path}:1: {self.code} {self.message}"


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey("duplicate object key")
        result[key] = value
    return result


def _stat_identity(value: os.stat_result) -> tuple:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _json_depth_within_limit(data: bytes) -> bool:
    depth = 0
    in_string = False
    escaped = False
    for byte in data:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_JSON_DEPTH:
                return False
        elif byte in (0x5D, 0x7D) and depth:
            depth -= 1
    return True


def _read_json(
    path: Path, *, maximum: int = MAX_BYTES
) -> tuple[object | None, bytes | None]:
    try:
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or stat.S_ISLNK(before.st_mode)
            or before.st_size > maximum
        ):
            return None, None
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            opened = os.fstat(descriptor)
            chunks = []
            total = 0
            while True:
                chunk = os.read(descriptor, min(64 * 1024, maximum + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > maximum:
                    return None, None
            after = os.fstat(descriptor)
            named = path.lstat()
        finally:
            os.close(descriptor)
        data = b"".join(chunks)
        if (
            len(data) != before.st_size
            or _stat_identity(opened) != _stat_identity(before)
            or _stat_identity(after) != _stat_identity(before)
            or _stat_identity(named) != _stat_identity(before)
            or not _json_depth_within_limit(data)
        ):
            return None, None
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite number {token}")
            ),
        )
        return value, data
    except (
        DuplicateKey,
        MemoryError,
        OSError,
        RecursionError,
        UnicodeDecodeError,
        ValueError,
    ):
        return None, None


def _bounded_text(value, *, maximum: int = MAX_TEXT_BYTES) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return (
        len(encoded) <= maximum
        and all(character.isprintable() for character in value)
    )


def _portable_path(value) -> bool:
    if not _bounded_text(value):
        return False
    parts = value.split("/")
    return not (
        value.startswith(("/", "\\"))
        or re.match(r"^[A-Za-z]:", value)
        or "\\" in value
        or any(part in ("", ".", "..") for part in parts)
    )


def _report_path(record_path: Path, supplied: str) -> Path | None:
    if not _portable_path(supplied):
        return None
    try:
        root = record_path.parent.resolve(strict=True)
        lexical = root
        for part in supplied.split("/"):
            lexical = lexical / part
            if stat.S_ISLNK(lexical.lstat().st_mode):
                return None
        candidate = lexical.resolve(strict=True)
        candidate.relative_to(root)
    except (OSError, ValueError):
        return None
    return candidate


def _number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _value_matches_unit(value, unit: str) -> bool:
    if unit == "boolean":
        return isinstance(value, bool)
    if unit == "string":
        return _bounded_text(value, maximum=MAX_SUMMARY_BYTES)
    if unit in ("bytes", "count", "milliseconds"):
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    if unit == "ratio":
        return _number(value) and 0 <= value <= 1
    return False


def _block_valid(value: object) -> bool:
    return value == "design-lock" or value == "integration" or (
        isinstance(value, str) and STEP_BLOCK.fullmatch(value) is not None
    )


def _criterion_fault(criterion: dict) -> str | None:
    kind = criterion["kind"]
    stage = criterion["stage"]
    unit = criterion["unit"]
    comparator = criterion["comparator"]
    threshold = criterion["threshold"]
    blocks = criterion["blocks"]

    if kind == "metric":
        if stage != "selection":
            return "comparative metrics are selection evidence"
        if unit not in NUMERIC_UNITS or comparator not in METRIC_COMPARATORS:
            return "comparative metric unit or comparator is unsupported"
        if threshold is not None:
            return "comparative metric threshold must be null"
    else:
        if comparator not in GATE_COMPARATORS:
            return "gate comparator is unsupported"
        if not _value_matches_unit(threshold, unit):
            return "gate threshold does not match its unit"
        if comparator != "equals" and unit not in NUMERIC_UNITS:
            return "ordered gate comparator requires a numeric unit"

    if stage == "selection" and blocks != "design-lock":
        return "selection evidence must block design-lock"
    if stage == "conformance" and (
        blocks == "design-lock" or not _block_valid(blocks)
    ):
        return "conformance evidence must block step:N or integration"
    return None


def _report_findings(
    record_path: Path,
    result: dict,
    criterion: dict,
    *,
    pending_at_transition: bool,
) -> tuple[list[Finding], object | None, str | None]:
    """Validate one report and return its value and digest when admitted."""
    findings: list[Finding] = []
    candidate_id = result["candidate"]
    criterion_id = result["criterion"]
    reference = result["report"]
    expected_digest = None
    supplied_path = reference
    if not pending_at_transition:
        if not isinstance(reference, dict) or set(reference) != REPORT_REF_KEYS:
            return [Finding(
                record_path, "D005",
                f"{candidate_id}/{criterion_id} report reference has an unsupported field set",
            )], None, None
        supplied_path = reference.get("path")
        expected_digest = reference.get("sha256")
        if not isinstance(expected_digest, str) or DIGEST.fullmatch(expected_digest) is None:
            return [Finding(
                record_path, "D005",
                f"{candidate_id}/{criterion_id} report reference has a malformed digest",
            )], None, None

    report_path = _report_path(record_path, supplied_path)
    if report_path is None:
        return [Finding(
            record_path, "D005" if not pending_at_transition else "D008",
            f"{candidate_id}/{criterion_id} report is unavailable or outside the record directory",
        )], None, None
    raw, data = _read_json(report_path, maximum=MAX_REPORT_BYTES)
    if not isinstance(raw, dict) or data is None or set(raw) != REPORT_KEYS:
        return [Finding(
            record_path, "D005" if not pending_at_transition else "D008",
            f"{candidate_id}/{criterion_id} report is not one closed {REPORT_SCHEMA} object",
        )], None, None
    digest = hashlib.sha256(data).hexdigest()
    if expected_digest is not None and digest != expected_digest:
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report digest does not match the record",
        ))
    if raw.get("schema") != REPORT_SCHEMA:
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report schema is unsupported",
        ))
    if raw.get("candidate") != candidate_id or raw.get("criterion") != criterion_id:
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report identity does not match",
        ))
    if raw.get("unit") != criterion["unit"]:
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report unit does not match",
        ))
    if not _value_matches_unit(raw.get("value"), criterion["unit"]):
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report value does not match its unit",
        ))
    if not _bounded_text(raw.get("command")):
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report command is missing or unbounded",
        ))
    if isinstance(raw.get("exit"), bool) or raw.get("exit") != 0:
        findings.append(Finding(
            record_path, "D005",
            f"{candidate_id}/{criterion_id} report must record exit 0",
        ))
    return findings, raw.get("value"), digest


def _derived_state(criterion: dict, value) -> str:
    if criterion["kind"] == "metric":
        return "pass"
    comparator = criterion["comparator"]
    threshold = criterion["threshold"]
    if comparator == "equals":
        passed = value == threshold
    elif comparator == "at-most":
        passed = value <= threshold
    else:
        passed = value >= threshold
    return "pass" if passed else "fail"


def _due(blocks: str, transition: str) -> bool:
    if transition == "integration":
        return blocks == "integration" or STEP_BLOCK.fullmatch(blocks) is not None
    wanted = STEP_BLOCK.fullmatch(transition)
    observed = STEP_BLOCK.fullmatch(blocks)
    return bool(
        wanted and observed
        and int(observed.group("number")) <= int(wanted.group("number"))
    )


def evaluate(path: Path, transition: str = "draft") -> tuple[list[Finding], dict | None, list[dict]]:
    """Return findings, the admitted record and reports consumed at transition."""
    raw, _ = _read_json(path)
    if not isinstance(raw, dict):
        return [Finding(path, "D000", "cannot be read as bounded strict JSON")], None, []
    if set(raw) != TOP_KEYS or raw.get("schema") != SCHEMA:
        return [Finding(path, "D001", f"record must be one closed {SCHEMA} object")], None, []

    findings: list[Finding] = []
    candidates = raw.get("candidates")
    criteria = raw.get("criteria")
    results = raw.get("results")
    selection = raw.get("selection")
    if not isinstance(candidates, list) or not MIN_CANDIDATES <= len(candidates) <= MAX_CANDIDATES:
        findings.append(Finding(
            path, "D002",
            f"candidates must contain {MIN_CANDIDATES} to {MAX_CANDIDATES} entries",
        ))
        candidates = []
    if not isinstance(criteria, list) or not 1 <= len(criteria) <= MAX_CRITERIA:
        findings.append(Finding(
            path, "D002", f"criteria must contain 1 to {MAX_CRITERIA} entries",
        ))
        criteria = []
    if not isinstance(results, list) or len(results) > MAX_RESULTS:
        findings.append(Finding(
            path, "D003", f"results must be an array of at most {MAX_RESULTS} entries",
        ))
        results = []
    if not isinstance(selection, dict) or set(selection) != SELECTION_KEYS:
        findings.append(Finding(path, "D001", "selection has an unsupported field set"))
        selection = {}

    candidate_map: dict[str, dict] = {}
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_KEYS:
            findings.append(Finding(
                path, "D001", f"candidate {index} has an unsupported field set",
            ))
            continue
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or ID.fullmatch(candidate_id) is None:
            findings.append(Finding(path, "D002", f"candidate {index} id is not kebab-case"))
            continue
        if candidate_id in candidate_map:
            findings.append(Finding(path, "D002", f"candidate {candidate_id} appears more than once"))
            continue
        if not _bounded_text(candidate.get("summary"), maximum=MAX_SUMMARY_BYTES):
            findings.append(Finding(path, "D001", f"candidate {candidate_id} summary is missing or unbounded"))
        candidate_map[candidate_id] = candidate

    criterion_map: dict[str, dict] = {}
    covered = set()
    selection_metrics = 0
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, dict) or set(criterion) != CRITERION_KEYS:
            findings.append(Finding(
                path, "D001", f"criterion {index} has an unsupported field set",
            ))
            continue
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str) or ID.fullmatch(criterion_id) is None:
            findings.append(Finding(path, "D002", f"criterion {index} id is not kebab-case"))
            continue
        if criterion_id in criterion_map:
            findings.append(Finding(path, "D002", f"criterion {criterion_id} appears more than once"))
            continue
        if criterion.get("concern") not in CONCERNS:
            findings.append(Finding(path, "D002", f"criterion {criterion_id} concern is unsupported"))
        else:
            covered.add(criterion["concern"])
        if criterion.get("kind") not in KINDS or criterion.get("stage") not in STAGES:
            findings.append(Finding(path, "D001", f"criterion {criterion_id} kind or stage is unsupported"))
            continue
        if criterion.get("unit") not in UNITS:
            findings.append(Finding(path, "D001", f"criterion {criterion_id} unit is unsupported"))
            continue
        if not _bounded_text(criterion.get("owner"), maximum=MAX_SUMMARY_BYTES):
            findings.append(Finding(path, "D001", f"criterion {criterion_id} owner is missing or unbounded"))
        fault = _criterion_fault(criterion)
        if fault:
            findings.append(Finding(path, "D001", f"criterion {criterion_id}: {fault}"))
            continue
        if criterion["kind"] == "metric":
            selection_metrics += 1
        criterion_map[criterion_id] = criterion
    missing_concerns = sorted(CONCERNS - covered)
    if missing_concerns:
        findings.append(Finding(
            path, "D002", "criteria omit required concerns: " + ", ".join(missing_concerns),
        ))
    if selection_metrics == 0:
        findings.append(Finding(path, "D002", "criteria carry no comparative selection metric"))

    values: dict[tuple[str, str], object] = {}
    matrix: dict[tuple[str, str], dict] = {}
    consumed: list[dict] = []
    report_paths = set()
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            findings.append(Finding(path, "D003", f"result {index} is not an object"))
            continue
        state = result.get("state")
        expected_keys = PENDING_KEYS if state == "pending" else RESOLVED_KEYS
        if state not in STATES or set(result) != expected_keys:
            findings.append(Finding(path, "D003", f"result {index} has an unsupported state or field set"))
            continue
        candidate_id = result.get("candidate")
        criterion_id = result.get("criterion")
        if candidate_id not in candidate_map or criterion_id not in criterion_map:
            findings.append(Finding(path, "D003", f"result {index} names an unknown candidate or criterion"))
            continue
        key = (candidate_id, criterion_id)
        if key in matrix:
            findings.append(Finding(path, "D003", f"result {candidate_id}/{criterion_id} appears more than once"))
            continue
        matrix[key] = result
        criterion = criterion_map[criterion_id]
        report_value = result.get("report")
        supplied_report_path = (
            report_value.get("path")
            if isinstance(report_value, dict)
            else report_value
        )
        if isinstance(supplied_report_path, str):
            if supplied_report_path in report_paths:
                findings.append(Finding(
                    path, "D003",
                    f"result {candidate_id}/{criterion_id} repeats a report path",
                ))
            report_paths.add(supplied_report_path)
        if state == "pending":
            if (
                not _bounded_text(result.get("resolver"))
                or not _portable_path(result.get("report"))
                or not _block_valid(result.get("blocks"))
                or result.get("blocks") != criterion["blocks"]
            ):
                findings.append(Finding(
                    path, "D004",
                    f"{candidate_id}/{criterion_id} pending result lacks its exact resolver, report or stop point",
                ))
                continue
            if transition != "draft" and criterion["stage"] == "selection":
                findings.append(Finding(
                    path, "D007",
                    f"{candidate_id}/{criterion_id} is pending and blocks design-lock; run {result['resolver']} to produce {result['report']}",
                ))
                continue
            if (
                transition not in ("draft", "design-lock")
                and candidate_id == selection.get("candidate")
                and _due(criterion["blocks"], transition)
            ):
                report_findings, value, digest = _report_findings(
                    path, result, criterion, pending_at_transition=True,
                )
                if report_findings:
                    for finding in report_findings:
                        if finding.code == "D005":
                            finding.code = "D008"
                    findings.extend(report_findings)
                    continue
                derived = _derived_state(criterion, value)
                if derived != "pass":
                    findings.append(Finding(
                        path, "D008",
                        f"{candidate_id}/{criterion_id} report fails the gate at {criterion['blocks']}",
                    ))
                    continue
                values[key] = value
                consumed.append({
                    "candidate": candidate_id,
                    "criterion": criterion_id,
                    "path": result["report"],
                    "sha256": digest,
                })
            continue

        report_findings, value, digest = _report_findings(
            path, result, criterion, pending_at_transition=False,
        )
        findings.extend(report_findings)
        if report_findings:
            continue
        derived = _derived_state(criterion, value)
        if state != derived:
            findings.append(Finding(
                path, "D006",
                f"{candidate_id}/{criterion_id} state {state} disagrees with its report-derived {derived}",
            ))
            continue
        values[key] = value
        if (
            transition == "design-lock" and criterion["stage"] == "selection"
        ) or (
            transition not in ("draft", "design-lock")
            and _due(criterion["blocks"], transition)
            and candidate_id == selection.get("candidate")
        ):
            consumed.append({
                "candidate": candidate_id,
                "criterion": criterion_id,
                "path": result["report"]["path"],
                "sha256": digest,
            })

    expected_matrix = {
        (candidate_id, criterion_id)
        for candidate_id in candidate_map
        for criterion_id in criterion_map
    }
    missing = sorted(expected_matrix - set(matrix))
    if missing:
        preview = ", ".join(f"{candidate}/{criterion}" for candidate, criterion in missing[:8])
        findings.append(Finding(path, "D003", f"result matrix is missing: {preview}"))
    extras = set(matrix) - expected_matrix
    if extras:
        findings.append(Finding(path, "D003", "result matrix contains unknown cells"))

    selected = selection.get("candidate")
    rule = selection.get("rule")
    policy_ref = selection.get("policy_ref")
    if selected not in candidate_map or rule not in SELECTION_RULES:
        findings.append(Finding(path, "D007", "selection candidate or rule is unsupported"))
    if rule == "user-policy":
        if not _bounded_text(policy_ref):
            findings.append(Finding(path, "D007", "user-policy selection requires a bounded policy_ref"))
    elif policy_ref is not None:
        findings.append(Finding(path, "D007", "policy_ref must be null outside user-policy selection"))

    selection_pending = [
        result for key, result in matrix.items()
        if criterion_map[key[1]]["stage"] == "selection"
        and result["state"] == "pending"
    ]
    can_select = not selection_pending and expected_matrix <= set(matrix)
    if transition != "draft" and can_select and selected in candidate_map and rule in SELECTION_RULES:
        eligible = []
        for candidate_id in candidate_map:
            failed = any(
                criterion["stage"] == "selection"
                and criterion["kind"] == "gate"
                and matrix[(candidate_id, criterion_id)]["state"] == "fail"
                for criterion_id, criterion in criterion_map.items()
            )
            if not failed:
                eligible.append(candidate_id)
        if not eligible:
            findings.append(Finding(path, "D007", "every candidate fails a selection hard gate"))
        metrics = [
            (criterion_id, criterion)
            for criterion_id, criterion in criterion_map.items()
            if criterion["stage"] == "selection" and criterion["kind"] == "metric"
        ]
        frontier = []
        for candidate_id in eligible:
            dominated = False
            for other_id in eligible:
                if other_id == candidate_id:
                    continue
                no_worse = True
                better = False
                for criterion_id, criterion in metrics:
                    left = values.get((other_id, criterion_id))
                    right = values.get((candidate_id, criterion_id))
                    if left is None or right is None:
                        no_worse = False
                        continue
                    if criterion["comparator"] == "minimise":
                        no_worse &= left <= right
                        better |= left < right
                    else:
                        no_worse &= left >= right
                        better |= left > right
                if no_worse and better:
                    dominated = True
                    break
            if not dominated:
                frontier.append(candidate_id)
        if selected not in frontier:
            findings.append(Finding(
                path, "D007", f"selected candidate {selected} is outside the non-dominated frontier",
            ))
        if rule == "unique-frontier" and (len(frontier) != 1 or frontier != [selected]):
            findings.append(Finding(path, "D007", "unique-frontier selection requires one surviving candidate"))
        elif rule == "user-policy" and len(frontier) < 2:
            findings.append(Finding(path, "D007", "user-policy selection requires several non-dominated candidates"))
        elif rule == "exact-tie-simplicity":
            tied = len(frontier) >= 2 and all(
                values.get((candidate_id, criterion_id))
                == values.get((frontier[0], criterion_id))
                for candidate_id in frontier[1:]
                for criterion_id, _ in metrics
            )
            if not tied:
                findings.append(Finding(path, "D007", "exact-tie-simplicity requires equal checked comparative values"))

        if selected in candidate_map:
            known_conformance_failures = [
                criterion_id
                for criterion_id, criterion in criterion_map.items()
                if criterion["stage"] == "conformance"
                and matrix[(selected, criterion_id)]["state"] == "fail"
            ]
            for criterion_id in known_conformance_failures:
                findings.append(Finding(
                    path, "D007", f"selected candidate {selected}/{criterion_id} already fails conformance",
                ))

    consumed.sort(key=lambda item: (item["candidate"], item["criterion"]))
    return findings, raw, consumed


def check(path: Path, transition: str = "draft") -> list[Finding]:
    return evaluate(path, transition)[0]


def _transition(value: str) -> str:
    if value in ("draft", "design-lock", "integration") or STEP_BLOCK.fullmatch(value):
        return value
    raise argparse.ArgumentTypeError(
        "transition must be draft, design-lock, step:N, or integration"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="design-evidence JSON record to check")
    parser.add_argument("--transition", type=_transition, default="draft")
    parser.add_argument("--format", choices=("text", "json", "receipt"), default="text")
    args = parser.parse_args(argv)
    findings, record, consumed = evaluate(Path(args.path), args.transition)
    if args.format == "receipt":
        selection = record.get("selection", {}) if isinstance(record, dict) else {}
        print(json.dumps({
            "schema": SCHEMA,
            "transition": args.transition,
            "selected": selection.get("candidate"),
            "consumed": consumed,
            "findings": [finding.as_dict() for finding in findings],
        }, indent=2, sort_keys=True))
    elif args.format == "json":
        print(json.dumps([finding.as_dict() for finding in findings], indent=2))
    else:
        for finding in findings:
            print(finding)
        print(f"{len(findings)} finding(s)" if findings else "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
