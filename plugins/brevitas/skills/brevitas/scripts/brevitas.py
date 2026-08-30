#!/usr/bin/env python3
"""Fail-closed structural linter for Brevitas engineering prose."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


SEVERITIES = r"critical|high|medium|low|informational|info"
CANONICAL_FINDING_RE = re.compile(
    rf"^\s*(?:#{{1,6}}\s+)?(?:\[(?:{SEVERITIES})\]|(?:{SEVERITIES})\s+[\u2014-])\s+\S",
    re.IGNORECASE,
)
SENTINEL_FINDING_RE = re.compile(r"^\s*FINDING\s*$")
SENTINEL_END_RE = re.compile(r"^\s*END\s*$")
EXCEPTION_RE = re.compile(
    r'^\s*<!--\s*brevitas:\s*evidence-exception\s+reason="([^"]+)"\s*-->\s*$'
)
HEADING_RE = re.compile(r"^(#{1,6})\s+\S")
LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")
TOP_LIST_RE = re.compile(r"^(?:[-*+]\s+|\d+[.)]\s+)")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
TABLE_SEPARATOR_RE = re.compile(
    r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$"
)
BOLD_LABEL_COLON_RE = re.compile(
    r"^\s*(?:[-*+]\s+)?\*\*[^*:\n]{1,60}(?::\*\*|\*\*:)\s*\S"
)
CONFIDENCE_THEATRE_RE = re.compile(
    r"\b(?:importantly|notably|it(?:'|\u2019)s worth noting|it is worth noting)\b",
    re.IGNORECASE,
)
PROCESS_RE = re.compile(
    r"^\s*(?:let me|i(?:'|\u2019)ll now|i will now|i(?:'|\u2019)m going to|"
    r"i am going to|first,? i(?:'|\u2019)ll|first,? i will|reading|checking|"
    r"reviewing|looking at)\b",
    re.IGNORECASE,
)
REQUEST_RE = re.compile(
    r"^\s*(?:you asked(?: me)? to|you(?:'|\u2019)ve asked|as requested|"
    r"per your request|your request is|the task is to)\b",
    re.IGNORECASE,
)
LIST_PREAMBLE_RE = re.compile(
    r"^\s*(?:here (?:are|is)|the following|i found|these are)\b.*:\s*$",
    re.IGNORECASE,
)
SUMMARY_RE = re.compile(
    r"^\s*(?:in summary|to summari[sz]e|overall|taken together|in conclusion)\b",
    re.IGNORECASE,
)
TRAILING_OFFER_RE = re.compile(
    r"^\s*(?:let me know if|i can also|if you(?:'|\u2019)d like|happy to|"
    r"would you like me to|feel free to ask)\b",
    re.IGNORECASE,
)
QUALIFIER_RE = re.compile(
    r"\b(?:may|might|could|possibly|probably|likely|apparently|appears?|seems?|"
    r"suggests?|arguably|potentially|perhaps)\b",
    re.IGNORECASE,
)
TX_HASH_RE = re.compile(r"\b0x[a-fA-F0-9]{64}\b")
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
SELECTOR_RE = re.compile(r"(?<![a-fA-F0-9])0x[a-fA-F0-9]{8}(?![a-fA-F0-9])")
DIGEST_RE = re.compile(
    r"(?<!0x)(?<!0X)(?<![a-fA-F0-9])[a-fA-F0-9]{64}(?![a-fA-F0-9])"
)
GIT_FULL_OID_RE = re.compile(
    r"(?<!0x)(?<!0X)(?<![a-fA-F0-9])[a-fA-F0-9]{40}(?![a-fA-F0-9])"
)
GIT_CODE_OID_RE = re.compile(
    r"(?P<ticks>`{1,3})(?P<oid>[a-fA-F0-9]{7,39})(?P=ticks)"
)
GIT_LABEL_OID_RE = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"(?:git|commit|sha(?:-1)?|oid|ref|head|base|parent|tree)"
    r"(?![A-Za-z0-9_-])(?:[ \t]*[:=][ \t]*|[ \t]+)"
    r"(?P<oid>[a-fA-F0-9]{7,39})(?![a-fA-F0-9])",
    re.IGNORECASE,
)
GIT_REPOSITORY_OID_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])"
    r"[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98}[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98}[A-Za-z0-9])?@"
    r"(?P<oid>[a-fA-F0-9]{7,39})(?![a-fA-F0-9])"
)
FILE_LINE_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\."
    r"[A-Za-z0-9]+:\d+(?:-\d+)?"
)
NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9_-])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?:%|[xX])?(?![A-Za-z0-9_-])"
)


@dataclass(frozen=True, order=True)
class Issue:
    line: int
    code: str
    message: str
    source: str = "draft"


@dataclass
class Finding:
    start: int
    end: int
    canonical: bool
    exception_line: int | None = None


def protected_tokens(text: str) -> dict[str, set[str]]:
    """Return evidence tokens whose literal survival can be checked mechanically."""
    tx_hashes = set(TX_HASH_RE.findall(text))
    addresses = set(ADDRESS_RE.findall(text))
    selectors = set(SELECTOR_RE.findall(text))
    digests = set(DIGEST_RE.findall(text))
    git_oids = set(GIT_FULL_OID_RE.findall(text))
    for pattern in (GIT_CODE_OID_RE, GIT_LABEL_OID_RE, GIT_REPOSITORY_OID_RE):
        git_oids.update(match.group("oid") for match in pattern.finditer(text))
    return {
        "transaction hash": tx_hashes,
        "address": addresses,
        "selector": selectors,
        "digest": digests,
        "Git object id": git_oids,
        "file:line reference": set(FILE_LINE_RE.findall(text)),
        "numeric token": set(NUMBER_RE.findall(text)),
    }


def _code_fences(lines: Sequence[str]) -> tuple[list[tuple[int, int, int]], set[int], list[Issue]]:
    fences: list[tuple[int, int, int]] = []
    code_lines: set[int] = set()
    issues: list[Issue] = []
    opener: tuple[int, str] | None = None
    for index, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if opener is None:
            if match:
                opener = (index, match.group(1))
                code_lines.add(index)
        else:
            code_lines.add(index)
            marker = opener[1]
            if re.match(rf"^\s*{re.escape(marker[0])}{{{len(marker)},}}\s*$", line):
                content_length = index - opener[0] - 1
                fences.append((opener[0], index, content_length))
                if content_length > 40:
                    issues.append(
                        Issue(opener[0], "B006", f"code fence has {content_length} lines; maximum is 40")
                    )
                opener = None
    if opener is not None:
        issues.append(Issue(opener[0], "B007", "unclosed code fence"))
    return fences, code_lines, issues


def _find_findings(lines: Sequence[str], code_lines: set[int]) -> list[Finding]:
    starts: list[tuple[int, bool]] = []
    sentinel_ranges: dict[int, int] = {}
    index = 1
    while index <= len(lines):
        if index in code_lines:
            index += 1
            continue
        line = lines[index - 1]
        if SENTINEL_FINDING_RE.match(line):
            starts.append((index, False))
            end = index
            while end <= len(lines) and not SENTINEL_END_RE.match(lines[end - 1]):
                end += 1
            sentinel_ranges[index] = min(end, len(lines))
            index = end + 1
            continue
        if CANONICAL_FINDING_RE.match(line):
            starts.append((index, True))
        index += 1

    findings: list[Finding] = []
    for position, (start, canonical) in enumerate(starts):
        if start in sentinel_ranges:
            end = sentinel_ranges[start]
        else:
            end = starts[position + 1][0] - 1 if position + 1 < len(starts) else len(lines)
        previous = start - 1
        while previous >= 1 and not lines[previous - 1].strip():
            previous -= 1
        exception_line = previous if previous >= 1 and EXCEPTION_RE.match(lines[previous - 1]) else None
        findings.append(Finding(start, end, canonical, exception_line))
    return findings


def _finding_issues(
    lines: Sequence[str], findings: Sequence[Finding], code_lines: set[int]
) -> list[Issue]:
    issues: list[Issue] = []
    used_exceptions: set[int] = set()
    for finding in findings:
        prose: list[tuple[int, str]] = []
        for line_number in range(finding.start, finding.end + 1):
            if line_number in code_lines:
                continue
            stripped = lines[line_number - 1].strip()
            if not stripped or stripped.startswith("<!--"):
                continue
            if not finding.canonical and (
                SENTINEL_FINDING_RE.match(stripped) or SENTINEL_END_RE.match(stripped)
            ):
                continue
            prose.append((line_number, stripped))

        if finding.exception_line is not None:
            used_exceptions.add(finding.exception_line)
            if len(prose) <= 5:
                issues.append(
                    Issue(finding.exception_line, "B005", "evidence exception is unnecessary")
                )
            if finding.canonical:
                evidence_prefixes = (
                    "evidence:",
                    "counterexample:",
                    "reproduction:",
                    "establishment limit:",
                    "could not establish:",
                    "address:",
                    "transaction:",
                    "numeric evidence:",
                )
                for line_number, value in prose[5:]:
                    if not value.lower().startswith(evidence_prefixes):
                        issues.append(
                            Issue(
                                line_number,
                                "B009",
                                "evidence exception retains non-evidence prose",
                            )
                        )
        elif len(prose) > 5:
            issues.append(
                Issue(
                    prose[5][0],
                    "B002",
                    f"finding has {len(prose)} prose lines; maximum is 5",
                )
            )

        if finding.canonical:
            required = ("Location:", "Mechanism:", "Impact:", "Fix:")
            values = [text for _, text in prose]
            for label in required:
                if not any(value.lower().startswith(label.lower()) for value in values[1:]):
                    issues.append(Issue(finding.start, "B003", f"canonical finding is missing {label}"))

    for line_number, line in enumerate(lines, start=1):
        match = EXCEPTION_RE.match(line)
        if match and line_number not in used_exceptions:
            issues.append(
                Issue(line_number, "B004", "evidence exception must immediately precede a finding")
            )
    return issues


def _section_issues(lines: Sequence[str], code_lines: set[int]) -> tuple[list[Issue], list[int]]:
    headings = [
        index
        for index, line in enumerate(lines, start=1)
        if index not in code_lines and HEADING_RE.match(line)
    ]
    sections = headings[:]
    if headings:
        first = headings[0]
        prior_content = any(lines[index - 1].strip() for index in range(1, first))
        if not prior_content and lines[first - 1].startswith("# "):
            sections = headings[1:]
    issues: list[Issue] = []
    if headings and len(sections) < 3:
        issues.append(
            Issue(headings[0], "B010", f"draft has {len(sections)} section headings; minimum is 3")
        )
    return issues, sections


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped)]


def _table_issues(lines: Sequence[str], code_lines: set[int]) -> list[Issue]:
    issues: list[Issue] = []
    index = 1
    while index < len(lines):
        if index in code_lines or index + 1 in code_lines:
            index += 1
            continue
        if "|" in lines[index - 1] and TABLE_SEPARATOR_RE.match(lines[index]):
            start = index
            rows = [lines[index - 1], lines[index]]
            cursor = index + 2
            while cursor <= len(lines) and "|" in lines[cursor - 1] and lines[cursor - 1].strip():
                rows.append(lines[cursor - 1])
                cursor += 1
            column_counts = [_split_table_row(row) for row in rows]
            real_columns = min((sum(bool(cell) for cell in row) for row in column_counts), default=0)
            data_rows = max(0, len(rows) - 2)
            if real_columns < 3 or data_rows < 3:
                issues.append(
                    Issue(
                        start,
                        "B011",
                        f"table has {data_rows} data rows and {real_columns} real-data columns; minimum is 3x3",
                    )
                )
            index = cursor
        else:
            index += 1
    return issues


def _point_for_line(
    line_number: int, findings: Sequence[Finding], headings: Sequence[int], list_points: Sequence[int]
) -> str:
    for position, finding in enumerate(findings):
        if finding.start <= line_number <= finding.end:
            return f"finding:{position}"
    candidates = [(line, f"heading:{line}") for line in headings if line < line_number]
    candidates += [(line, f"list:{line}") for line in list_points if line < line_number]
    return max(candidates, default=(0, "document"), key=lambda item: item[0])[1]


def _structural_move_issues(lines: Sequence[str], code_lines: set[int]) -> list[Issue]:
    issues: list[Issue] = []
    nonblank = [index for index, line in enumerate(lines, start=1) if line.strip()]
    first_six = set(nonblank[:6])
    last_five = set(nonblank[-5:])
    saw_list = False
    for index, line in enumerate(lines, start=1):
        if index in code_lines:
            continue
        if LIST_RE.match(line) or TABLE_SEPARATOR_RE.match(line):
            saw_list = True
        if index in first_six and REQUEST_RE.search(line):
            issues.append(Issue(index, "B020", "request restatement"))
        if index in first_six and LIST_PREAMBLE_RE.search(line):
            issues.append(Issue(index, "B021", "list preamble"))
        if PROCESS_RE.search(line):
            issues.append(Issue(index, "B022", "process narration"))
        if BOLD_LABEL_COLON_RE.search(line):
            issues.append(Issue(index, "B023", "bold-label-colon item"))
        if CONFIDENCE_THEATRE_RE.search(line):
            issues.append(Issue(index, "B024", "confidence theatre"))
        if saw_list and SUMMARY_RE.search(line):
            issues.append(Issue(index, "B025", "summary after list"))
        if index in last_five and TRAILING_OFFER_RE.search(line):
            issues.append(Issue(index, "B026", "trailing offer"))
        qualifiers = QUALIFIER_RE.findall(line)
        if len(qualifiers) > 1:
            issues.append(
                Issue(index, "B027", f"claim stacks {len(qualifiers)} qualifiers; maximum is 1")
            )
    return issues


def _direct_answer_issues(
    lines: Sequence[str], code_lines: set[int], mode: str, findings: Sequence[Finding], sections: Sequence[int]
) -> list[Issue]:
    is_report = mode == "report" or (mode == "auto" and (findings or len(sections) >= 3))
    if is_report:
        return []
    prose_lines: list[int] = []
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        if index in code_lines or LIST_RE.match(line) or FENCE_RE.match(line):
            break
        prose_lines.append(index)
    if len(prose_lines) > 6:
        return [
            Issue(
                prose_lines[6],
                "B001",
                f"direct answer has {len(prose_lines)} lines before a list or code fence; maximum is 6",
            )
        ]
    return []


def _evidence_issues(source_text: str, draft_text: str, source_name: str) -> list[Issue]:
    source_tokens = protected_tokens(source_text)
    draft_tokens = protected_tokens(draft_text)
    source_lines = source_text.splitlines()
    issues: list[Issue] = []
    for category, tokens in source_tokens.items():
        missing = sorted(tokens - draft_tokens[category])
        for token in missing:
            line = next(
                (index for index, text in enumerate(source_lines, start=1) if token in text),
                1,
            )
            issues.append(
                Issue(line, "B030", f"missing protected {category}: {token}", source_name)
            )
    return issues


def lint_text(
    text: str,
    *,
    mode: str = "auto",
    source_text: str | None = None,
    source_name: str = "source",
) -> list[Issue]:
    lines = text.splitlines()
    fences, code_lines, issues = _code_fences(lines)
    findings = _find_findings(lines, code_lines)
    section_issues, sections = _section_issues(lines, code_lines)
    issues.extend(section_issues)
    issues.extend(_finding_issues(lines, findings, code_lines))
    issues.extend(_table_issues(lines, code_lines))
    issues.extend(_structural_move_issues(lines, code_lines))
    issues.extend(_direct_answer_issues(lines, code_lines, mode, findings, sections))
    if source_text is not None:
        issues.extend(_evidence_issues(source_text, text, source_name))
    return sorted(set(issues))


def _read(path: str) -> tuple[str, str]:
    if path == "-":
        return sys.stdin.read(), "stdin"
    file_path = Path(path)
    return file_path.read_text(encoding="utf-8"), str(file_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("draft", nargs="?", default="-", help="draft file or - for stdin")
    parser.add_argument("--source", help="uncompressed source whose evidence must survive")
    parser.add_argument("--mode", choices=("auto", "answer", "report"), default="auto")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        draft_text, draft_name = _read(args.draft)
        source_text = source_name = None
        if args.source:
            source_text, source_name = _read(args.source)
    except OSError as error:
        print(f"brevitas: {error}", file=sys.stderr)
        return 2

    issues = lint_text(
        draft_text,
        mode=args.mode,
        source_text=source_text,
        source_name=source_name or "source",
    )
    for issue in issues:
        name = draft_name if issue.source == "draft" else issue.source
        print(f"{name}:{issue.line}: {issue.code} {issue.message}", file=sys.stderr)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
