"""Import a reviewed spreadsheet without losing what a row said.

Lineage is the whole point. Every imported case keeps the sheet it came from,
the row it sat on, its own identifier and every column the header named, so the
record can be read back to the workbook rather than standing in for it.

Splitting a compound row into atomic cases is declared, never inferred. Working
out that one row describes two things is a reviewer's judgement about product
intent, and this importer does not make judgements about product intent.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import xlsx
from . import schema as schema_lib

SCHEMA = "dokimasia-workbook/v1"
LINEAGE = "dokimasia-workbook-lineage/v1"
HEADER_KEY = "ID"
CASE_ID = re.compile(r"^[A-Z][A-Z0-9]*-\d+[a-z]?$")
MAX_CASES = 20_000


class WorkbookError(Exception):
    """One named refusal while importing."""


def _header_row(rows: list[list[str]]) -> int | None:
    for index, row in enumerate(rows):
        if row and row[0].strip() == HEADER_KEY:
            return index
    return None


def _columns(header: list[str]) -> dict[str, int]:
    """Header label to column index, first occurrence winning.

    A merged or repeated header keeps its leftmost column, so a later blank
    spanning cell cannot silently take a named field's place.
    """
    columns: dict[str, int] = {}
    for index, label in enumerate(header):
        name = label.strip()
        if name and name not in columns:
            columns[name] = index
    return columns


def _fields(row: list[str], columns: dict[str, int]) -> dict[str, str]:
    return {
        name: (row[index].strip() if index < len(row) else "")
        for name, index in sorted(columns.items())
    }


def read_cases(
    path: Path,
    splits: dict[str, list[str]] | None = None,
    sheet_log: list[dict] | None = None,
) -> list[dict]:
    """Every case row in the workbook, in sheet and row order.

    `splits` maps one source identifier to the atomic identifiers a reviewer
    decided it describes. Each atomic case carries the whole source row and the
    identifier it came from, so nothing about the split is lossy.

    `sheet_log`, when given, is filled with one entry per sheet recording what
    that sheet contributed and why, so a sheet that contributes nothing is a
    visible decision rather than an absence.
    """
    declared = splits or {}
    sheets = xlsx.read_sheets(path)
    cases: list[dict] = []
    seen: set[str] = set()
    matched: set[str] = set()
    for sheet_name, rows in sheets.items():
        before = len(cases)
        header_index = _header_row(rows)
        if header_index is None:
            if sheet_log is not None:
                sheet_log.append({
                    "sheet": sheet_name,
                    "rows": len(rows),
                    "cases": 0,
                    "reason": f"no row begins with {HEADER_KEY!r}",
                })
            continue
        columns = _columns(rows[header_index])
        for offset, row in enumerate(rows[header_index + 1:], start=header_index + 2):
            if not row:
                continue
            identifier = row[0].strip()
            if not CASE_ID.match(identifier):
                continue
            fields = _fields(row, columns)
            atomic = declared.get(identifier, [identifier])
            if identifier in declared:
                matched.add(identifier)
            for case_id in atomic:
                if case_id in seen:
                    raise WorkbookError(
                        f"case {case_id!r} appears more than once, so a "
                        "disposition could not be attached to one row"
                    )
                seen.add(case_id)
                cases.append({
                    "id": case_id,
                    "source_id": identifier,
                    "sheet": sheet_name,
                    "row": offset,
                    "split": len(atomic) > 1,
                    "fields": fields,
                })
            if len(cases) > MAX_CASES:
                raise WorkbookError(
                    f"the workbook holds more than the {MAX_CASES}-case cap"
                )
        if sheet_log is not None:
            produced = len(cases) - before
            body = len(rows) - header_index - 1
            sheet_log.append({
                "sheet": sheet_name,
                "rows": body,
                "cases": produced,
                "reason": (
                    "" if produced
                    else f"no row below the header carries an identifier "
                         f"shaped like {CASE_ID.pattern}"
                ),
            })
    unmatched = sorted(set(declared) - matched)
    if unmatched:
        # A split names a row a reviewer read. If no such row is here, either the
        # declaration is mistyped or the workbook is not the one it was written
        # against, and silently importing would report a compound row as atomic.
        raise WorkbookError(
            "declared split(s) for "
            + ", ".join(repr(identifier) for identifier in unmatched)
            + " matched no row in this workbook"
        )
    return cases


def source_rows(cases: list[dict]) -> dict[tuple[str, int], dict[str, str]]:
    """Rebuild the workbook rows the cases came from.

    This is the round trip. Every atomic case of one source row must carry the
    same fields, or the split lost something.
    """
    rebuilt: dict[tuple[str, int], dict[str, str]] = {}
    for case in cases:
        key = (case["sheet"], case["row"])
        if key in rebuilt and rebuilt[key] != case["fields"]:
            raise WorkbookError(
                f"two cases from {key} disagree about the row they came from"
            )
        rebuilt[key] = case["fields"]
    return rebuilt


def canonical_bytes(cases: list[dict]) -> bytes:
    return json.dumps(
        {"schema": SCHEMA, "lineage": LINEAGE, "cases": cases},
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def workbook_digest(cases: list[dict]) -> str:
    return hashlib.sha256(canonical_bytes(cases)).hexdigest()


def record(
    cases: list[dict], subject: dict, sheets: list[dict] | None = None
) -> dict:
    """The closed record, with counts a reviewer can check against the source.

    `sheets` reports what every sheet contributed, including the ones that
    contributed nothing and why. Without it, a sheet excluded correctly and a
    sheet excluded by a renamed header look identical in the record.
    """
    statuses: dict[str, int] = {}
    labels: dict[str, int] = {}
    for case in cases:
        status = case["fields"].get("Status", "") or "(blank)"
        statuses[status] = statuses.get(status, 0) + 1
        label = case["fields"].get("Source", "") or "(blank)"
        labels[label] = labels.get(label, 0) + 1
    return {
        "schema": SCHEMA,
        "lineage": LINEAGE,
        "subject": subject,
        "caps": {
            "cases": MAX_CASES,
            "members": xlsx.MAX_MEMBERS,
            "member_bytes": xlsx.MAX_MEMBER_BYTES,
            "expansion_ratio": xlsx.MAX_EXPANSION_RATIO,
        },
        "counts": {
            "cases": len(cases),
            "source_rows": len(source_rows(cases)),
            "by_status": dict(sorted(statuses.items())),
            "by_source": dict(sorted(labels.items())),
        },
        "sheets": sheets if sheets is not None else [],
        "workbook_sha256": workbook_digest(cases),
        "cases": cases,
    }


def fixture_builder():
    """Load the committed fixture builder without importing it as a package."""
    import importlib.util

    source = (
        Path(__file__).resolve().parents[2]
        / "tests" / "fixtures" / "workbooks" / "build.py"
    )
    spec = importlib.util.spec_from_file_location("dokimasia_workbook_fixtures", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check() -> list[str]:
    """Every failure this step's exit criteria name, or an empty list."""
    import tempfile

    failures: list[str] = []
    build = fixture_builder()
    hostile = {
        "zip-bomb.xlsx": "ratio cap",
        "traversal-member.xlsx": "parent-directory segment",
        "too-many-members.xlsx": "member",
        "far-right-cell.xlsx": "column cap",
        "unanchored-cell.xlsx": "names no column",
        "entity-declaration.xlsx": "entity declaration",
        "not-a-spreadsheet.xlsx": "not a spreadsheet archive",
    }
    with tempfile.TemporaryDirectory() as raw:
        made = build.build_all(Path(raw))

        benign = read_cases(made["benign.xlsx"])
        if not benign:
            failures.append("the benign fixture imported no cases")
        if len(source_rows(benign)) != len(benign):
            failures.append("the benign fixture lost a source row on import")
        if workbook_digest(benign) != workbook_digest(read_cases(made["benign.xlsx"])):
            failures.append("two imports of the same workbook disagreed")

        absolute = read_cases(made["absolute-targets.xlsx"])
        if [case["id"] for case in absolute] != [case["id"] for case in benign]:
            failures.append("package-absolute relationship targets changed the import")

        split = read_cases(made["benign.xlsx"], splits={"M2-03": ["M2-03a", "M2-03b"]})
        halves = [case for case in split if case["source_id"] == "M2-03"]
        if len(halves) != 2:
            failures.append("a declared split did not produce two atomic cases")
        elif halves[0]["fields"] != halves[1]["fields"]:
            failures.append("a declared split lost the row its halves came from")
        elif len(source_rows(split)) != len(source_rows(benign)):
            failures.append("a declared split changed how many source rows exist")

        log: list[dict] = []
        logged = read_cases(made["benign.xlsx"], sheet_log=log)
        if [entry["sheet"] for entry in log] != list(xlsx.read_sheets(made["benign.xlsx"])):
            failures.append("the sheet log did not name every sheet the reader saw")
        elif sum(entry["cases"] for entry in log) != len(logged):
            failures.append("the sheet log's case counts did not add up to the import")
        elif any(not e["reason"] for e in log if e["cases"] == 0):
            failures.append("a sheet yielding no case was passed over with no reason")

        unknown = [c for c in benign if c["fields"].get("Status") == "Weird"]
        if not unknown:
            failures.append("an unrecognised status was not kept as written")

        for name, expected in hostile.items():
            try:
                read_cases(made[name])
            except (xlsx.XlsxRefusal, WorkbookError) as refusal:
                if expected not in str(refusal):
                    failures.append(f"{name} refused with {refusal!r}, not for {expected!r}")
            else:
                failures.append(f"{name} was accepted; it must refuse")

        # The schema says the record is closed. Enforce it rather than stating it.
        emitted = record(benign, {"label": "benign.xlsx", "sha256": "0" * 64}, log)
        failures.extend(
            f"the workbook record breaches its schema: {line}"
            for line in schema_lib.check(emitted)
        )
    return failures
