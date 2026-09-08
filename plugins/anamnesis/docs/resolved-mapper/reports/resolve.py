#!/usr/bin/env python3
"""Resolve one cell of the declared-mapper design record.

Usage::

    python3 .hexaemeron/reports/resolve.py <candidate> <criterion> [--out PATH]

The report is printed. It is written only to a path named by ``--out``, and
only when that path does not already exist, so a rerun can never replace a
receipted report the way the corpus-scope run's resolver once did.

Every value is computed from bytes in the checkout plus the candidate
specification declared below. Nothing here shells out to ``git grep``: the
corpus-scope run learned that a grep-based count moves whenever a guard or a
record quoting the same token is committed, so this resolver counts only
declared artefacts and measures only parses.

Run it from the worktree root.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import statistics
import sys
import time

SCHEMA = "protasis-design-report/v1"
REPORTS = ".hexaemeron/reports"
SCRIPT = "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py"
PILOT = "plugins/anamnesis/specimens/pilot"
ESTATE = "plugins/anamnesis/specimens/estate"

SYNOPSIS_SOURCES = (
    "plugins/hexaemeron/audit/AUDIT_SYNOPSIS.md",
    "plugins/pandects/audit/AUDIT_SYNOPSIS.md",
    "plugins/tabularium/audit/AUDIT_SYNOPSIS.md",
)
RED_TEAM_SOURCES = (
    "plugins/brevitas/skills/brevitas/evals/cases/"
    "fund-safety-evidence-exception/original.md",
)
WARDEN_SOURCES = (
    f"{PILOT}/sources/hexaemeron-audit-rounds.md",
    f"{PILOT}/sources/pandects-audit-rounds.md",
    f"{PILOT}/sources/tabularium-audit-rounds.md",
)

# The two shipped corpora whose curation policies carry the mapper today.
SHIPPED_CURATION_POLICIES = (
    f"{PILOT}/curation-policy.json",
    f"{ESTATE}/curation-policy.json",
)

CANDIDATES = {
    "registry-and-synopsis-mapper": {
        "registry": True,
        "records_resolved_mapper": True,
        "mapper_home": "curation-policy",
        "second_format": "fiat-audit-synopsis",
        "second_sources": SYNOPSIS_SOURCES,
    },
    "registry-and-red-team-mapper": {
        "registry": True,
        "records_resolved_mapper": True,
        "mapper_home": "curation-policy",
        "second_format": "red-team-finding-block",
        "second_sources": RED_TEAM_SOURCES,
    },
    "registry-only": {
        "registry": True,
        "records_resolved_mapper": True,
        "mapper_home": "curation-policy",
        "second_format": None,
        "second_sources": (),
    },
    "per-source-mapper": {
        "registry": True,
        "records_resolved_mapper": True,
        "mapper_home": "admission-policy",
        "second_format": "fiat-audit-synopsis",
        "second_sources": SYNOPSIS_SOURCES,
    },
}

SYNOPSIS_HEADER = re.compile(
    r"^Synopsis schema=(?P<schema>\S+) \| source=(?P<source>\S+) \| "
    r"source_sha256=(?P<sha>[0-9a-f]{64}) \| h2_count=(?P<count>\d+)$"
)
SYNOPSIS_SCHEMA = "fiat-audit-synopsis/v1"

RED_TEAM_OPEN = "FINDING"
RED_TEAM_CLOSE = "END"
RED_TEAM_FIELD = re.compile(r"^(?P<name>[a-z_]+):\s*(?P<value>.*)$")


def load_anamnesis():
    """Load the shipped program so the mappers reuse its own row grammar."""
    spec = importlib.util.spec_from_file_location("anamnesis_probe", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def parse_synopsis(text, source_id, module):
    """Read one ``fiat-audit-synopsis/v1`` record into rounds and findings.

    The synopsis puts one whole round on one physical line with ``<br>``
    between the cells. Splitting on that separator recovers the producer's own
    cells, so the round-field and finding-row grammar the Warden mapper already
    owns applies to them unchanged.
    """
    lines = text.splitlines()
    if not lines:
        return None
    header = SYNOPSIS_HEADER.match(lines[0])
    if header is None or header.group("schema") != SYNOPSIS_SCHEMA:
        return None
    rounds = []
    for number, line in enumerate(lines[1:], start=2):
        cells = line.split("<br>")
        heading = module.ROUND_HEADING.match(cells[0])
        if heading is None:
            continue
        current = {
            "id": f"round:{source_id}:{len(rounds) + 1}",
            "label": heading.group("label").strip(),
            "date": heading.group("date").strip(),
            "line": number,
            "fields": {},
            "findings": [],
        }
        for cell in cells[1:]:
            field = module.ROUND_FIELD.match(cell)
            if field:
                current["fields"][field.group("name")] = field.group("value").strip()
                continue
            row = module.FINDING_ROW.match(cell)
            if row and row.group("severity") != "---":
                current["findings"].append({
                    "native_id": row.group("native"),
                    "severity": row.group("severity"),
                    "file": module._strip_code(row.group("file")),
                    "finding": row.group("finding").strip(),
                    "status": row.group("status").strip(),
                    "line": number,
                })
        rounds.append(current)
    return rounds


def parse_red_team(text, source_id, module):
    """Read one ``FINDING`` ... ``END`` key-value block into one round."""
    del module
    findings = []
    current = None
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped == RED_TEAM_OPEN:
            current = {"line": number, "fields": {}}
            continue
        if stripped == RED_TEAM_CLOSE and current is not None:
            fields = current["fields"]
            findings.append({
                "native_id": f"{source_id}:F{len(findings) + 1:02d}",
                "severity": fields.get("severity", ""),
                "file": fields.get("claim_source", ""),
                "finding": fields.get("title", ""),
                "status": fields.get("disposition", ""),
                "line": current["line"],
            })
            current = None
            continue
        if current is None:
            continue
        field = RED_TEAM_FIELD.match(line)
        if field:
            current["fields"][field.group("name")] = field.group("value").strip()
    if not findings:
        return None
    return [{
        "id": f"round:{source_id}:1",
        "label": f"{source_id}, round 1",
        "date": "",
        "line": 1,
        "fields": {},
        "findings": findings,
    }]


PARSERS = {
    "fiat-audit-synopsis": parse_synopsis,
    "red-team-finding-block": parse_red_team,
}


def declared_mapper_is_dead(module):
    """Establish that the shipped constant names nothing the resolver picks."""
    source = read(SCRIPT)
    occurrences = len(re.findall(r"\bMAPPER\b", source))
    return occurrences == 1 and module.MAPPER["name"] == "warden-audit-round-markdown"


def canonical_policy_without_mapper(path, module):
    policy = json.loads(read(path))
    reduced = {key: value for key, value in policy.items() if key != "mapper"}
    return module.canonical(policy), module.canonical(reduced)


# --- criteria ---------------------------------------------------------------


def criterion_unknown_mapper_refuses(candidate):
    module = load_anamnesis()
    if not declared_mapper_is_dead(module):
        raise SystemExit("the declared mapper is not the dead constant this record assumes")
    return bool(CANDIDATES[candidate]["registry"]), "boolean"


def criterion_assertion_records_the_mapper_that_ran(candidate):
    spec = CANDIDATES[candidate]
    return bool(spec["registry"] and spec["records_resolved_mapper"]), "boolean"


def criterion_second_format_declares_its_own_schema(candidate):
    spec = CANDIDATES[candidate]
    sources = spec["second_sources"]
    if not sources:
        return False, "boolean"
    if spec["second_format"] != "fiat-audit-synopsis":
        # No other admitted format carries a schema token in its own bytes.
        for path in sources:
            first = read(path).splitlines()[0] if read(path).splitlines() else ""
            if SYNOPSIS_HEADER.match(first):
                raise SystemExit(f"{path} unexpectedly declares a synopsis header")
        return False, "boolean"
    for path in sources:
        lines = read(path).splitlines()
        header = SYNOPSIS_HEADER.match(lines[0]) if lines else None
        if header is None or header.group("schema") != SYNOPSIS_SCHEMA:
            return False, "boolean"
    return True, "boolean"


def criterion_shipped_release_policies_changed(candidate):
    module = load_anamnesis()
    if CANDIDATES[candidate]["mapper_home"] == "curation-policy":
        return 0, "count"
    changed = 0
    for path in SHIPPED_CURATION_POLICIES:
        before, after = canonical_policy_without_mapper(path, module)
        if before != after:
            changed += 1
    return changed, "count"


def criterion_second_format_findings_read(candidate):
    spec = CANDIDATES[candidate]
    if not spec["second_sources"]:
        return 0, "count"
    module = load_anamnesis()
    parser = PARSERS[spec["second_format"]]
    total = 0
    for path in spec["second_sources"]:
        source_id = os.path.basename(os.path.dirname(path))
        rounds = parser(read(path), source_id, module)
        if rounds is None:
            raise SystemExit(f"{spec['second_format']} refused {path}")
        total += sum(len(entry["findings"]) for entry in rounds)
    return total, "count"


def criterion_source_bytes_added(candidate):
    sources = CANDIDATES[candidate]["second_sources"]
    return sum(os.path.getsize(path) for path in sources), "bytes"


def criterion_acceptance_check_ms(candidate):
    """Time the parses each candidate's acceptance condition needs.

    Both halves are parse work: the refusal half re-reads the pilot's three
    Warden sources, and the second-format half reads whatever sources the
    candidate admits. Five samples, median, rounded to whole milliseconds.
    """
    spec = CANDIDATES[candidate]
    module = load_anamnesis()
    warden = [(path, read(path)) for path in WARDEN_SOURCES]
    second = [(path, read(path)) for path in spec["second_sources"]]
    parser = PARSERS[spec["second_format"]] if spec["second_format"] else None
    samples = []
    for _ in range(5):
        started = time.perf_counter()
        for path, text in warden:
            module.parse_source(text, os.path.basename(path))
        for path, text in second:
            parser(text, os.path.basename(os.path.dirname(path)), module)
        samples.append((time.perf_counter() - started) * 1000.0)
    return int(round(statistics.median(samples))), "milliseconds"


def criterion_recovery_without_a_program_edit(candidate):
    """A wrong mapper declaration is corrected by editing one policy file."""
    spec = CANDIDATES[candidate]
    return spec["mapper_home"] in ("curation-policy", "admission-policy"), "boolean"


CRITERIA = {
    "unknown-mapper-refuses-at-curation": criterion_unknown_mapper_refuses,
    "assertion-records-the-mapper-that-ran":
        criterion_assertion_records_the_mapper_that_ran,
    "second-format-declares-its-own-schema":
        criterion_second_format_declares_its_own_schema,
    "shipped-release-policies-changed": criterion_shipped_release_policies_changed,
    "second-format-findings-read": criterion_second_format_findings_read,
    "source-bytes-added": criterion_source_bytes_added,
    "acceptance-check-ms": criterion_acceptance_check_ms,
    "recovery-without-a-program-edit": criterion_recovery_without_a_program_edit,
}


def main(argv):
    out = None
    if len(argv) == 4 and argv[2] == "--out":
        argv, out = argv[:2], argv[3]
    if len(argv) != 2 or argv[0] not in CANDIDATES or argv[1] not in CRITERIA:
        print(__doc__, file=sys.stderr)
        return 2
    if out is not None and os.path.lexists(out):
        print(f"resolve.py: refusing to replace {out}", file=sys.stderr)
        return 2
    candidate, criterion = argv
    value, unit = CRITERIA[criterion](candidate)
    report = {
        "schema": SCHEMA,
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": f"python3 {REPORTS}/resolve.py {candidate} {criterion}",
        "exit": 0,
    }
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if out is not None:
        with open(out, "x", encoding="utf-8") as handle:
            handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
