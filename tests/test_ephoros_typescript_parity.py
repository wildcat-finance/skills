"""Hold the shipped run documents for the Ephoros TypeScript parity run.

The study, the runbook and the design record for this run live in the tree
rather than in the controller's working directory, so a reader who clones the
repository gets the evidence behind the recognisers along with them. These
cases read only tracked paths, so they prove the copies from inside a clone.

The layout is split on purpose. The study and the runbook ship flat under
``docs/`` because the study links five phase skills as ``../plugins/...`` and
ADR-010 as ``../docs/decisions/...``; both forms resolve from ``docs/`` and
from nowhere deeper. The design record ships one directory down because it
cites its reports by the record-relative path ``reports/<name>.json``, and that
layout has to survive the copy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPOSITORY_ROOT / "docs"
STUDY = DOCS / "ephoros-typescript-rule-parity-study.md"
RUNBOOK = DOCS / "ephoros-typescript-rule-parity-runbook.md"
RECORD_DIRECTORY = DOCS / "ephoros-typescript-rule-parity"
RECORD = RECORD_DIRECTORY / "design-evidence.json"

SCHEMA = "protasis-design-evidence/v1"
SELECTED = "span-index"
CITED_REPORT_COUNT = 15

MARKDOWN_LINK = re.compile(r"\]\((?P<target>[^)]+)\)")
SCHEME = re.compile(r"\A[a-z][a-z0-9+.-]*:")


def record() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def cited_reports() -> list[dict]:
    """Every result cell in the shipped record that names a settled report."""
    found = []
    for result in record()["results"]:
        report = result.get("report")
        if isinstance(report, dict):
            found.append(report)
    return found


class ShippedRecordTests(unittest.TestCase):
    def test_study_and_runbook_ship_flat_under_docs(self):
        for path in (STUDY, RUNBOOK):
            self.assertTrue(path.is_file(), f"{path} is missing from the tree")
            self.assertTrue(
                path.read_text(encoding="utf-8").strip(),
                f"{path} is empty",
            )

    def test_shipped_record_selects_the_candidate_the_run_built(self):
        shipped = record()
        self.assertEqual(shipped["schema"], SCHEMA)
        self.assertEqual(shipped["selection"]["candidate"], SELECTED)
        self.assertIn(
            SELECTED,
            [candidate["id"] for candidate in shipped["candidates"]],
            "the selected candidate is not one of the record's candidates",
        )

    def test_every_cited_report_resolves_at_the_digest_the_record_states(self):
        reports = cited_reports()
        self.assertEqual(len(reports), CITED_REPORT_COUNT)
        for report in reports:
            path = RECORD_DIRECTORY / report["path"]
            self.assertTrue(path.is_file(), f"{report['path']} is missing")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                digest,
                report["sha256"],
                f"{report['path']} does not match the digest the record states",
            )

    def test_every_relative_link_in_the_shipped_study_resolves(self):
        text = STUDY.read_text(encoding="utf-8")
        targets = {
            match.group("target")
            for match in MARKDOWN_LINK.finditer(text)
            if not SCHEME.match(match.group("target"))
        }
        self.assertTrue(targets, "the shipped study has no relative links left")
        for target in sorted(targets):
            resolved = (STUDY.parent / target.split("#", 1)[0]).resolve()
            self.assertTrue(
                resolved.exists(),
                f"{target} in the shipped study resolves to nothing",
            )

    def test_report_paths_in_the_shipped_record_stay_record_relative(self):
        reports = cited_reports()
        self.assertEqual(
            len(reports),
            CITED_REPORT_COUNT,
            "the record cites no reports, so this case would prove nothing",
        )
        for report in reports:
            path = report["path"]
            self.assertFalse(
                Path(path).is_absolute(),
                f"{path} is an absolute path in a shipped record",
            )
            self.assertFalse(
                path.startswith(".."),
                f"{path} climbs above the record's own directory",
            )
            self.assertTrue(
                path.startswith("reports/"),
                f"{path} is not under the record's reports directory",
            )


if __name__ == "__main__":
    unittest.main()
