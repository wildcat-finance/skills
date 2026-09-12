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
EPHOROS = REPOSITORY_ROOT / "plugins" / "hexaemeron" / "skills" / "ephoros"
LEDGER = EPHOROS / "EVOLUTION.md"
SKILL = EPHOROS / "SKILL.md"
FUTUREPROOFING = REPOSITORY_ROOT / "FUTUREPROOFING.md"
STUDY = DOCS / "ephoros-typescript-rule-parity-study.md"
RUNBOOK = DOCS / "ephoros-typescript-rule-parity-runbook.md"
RECORD_DIRECTORY = DOCS / "ephoros-typescript-rule-parity"
RECORD = RECORD_DIRECTORY / "design-evidence.json"

SCHEMA = "protasis-design-evidence/v1"
SELECTED = "span-index"
CITED_REPORT_COUNT = 15

# The row this run adds. VERSIONING.md's evolution arithmetic from the prior
# row, ``ephoros-v1.2.0``, gives the label; the row's digest is recomputed from
# the ledger's own header bullets rather than restated here.
LEDGER_ROW_VERSION = "ephoros-v2.2.0"
CLONE_COMMIT = "564a189b"
CLONE_E001_COUNT = "14"
# The four header fields the canonical frontier line digests, in this order.
FRONTIER_FIELDS = (
    "Frontier status",
    "Frontier revision",
    "Current frontier",
    "Next Fiat job",
)
# The controller-pinned sources carried no amendment when the shipped copies
# were refreshed at this step's entry. The count is a literal so a fresh clone
# proves the copies without reading anything outside the repository.
AMENDMENT_HEADING = "### Amendment --"
SHIPPED_AMENDMENT_COUNTS = {STUDY: 0, RUNBOOK: 0}
HEADER_BULLET = re.compile(r"(?m)^- (?P<name>[^:]+): (?P<value>.+)$")
COMPACT_ROW = re.compile(
    r"(?m)^- `(?P<version>[^`]+)` \| (?P<axis>[a-z]+) \| `(?P<revision>[^`]+)` "
    r"\| `(?P<digest>[0-9a-f]{64})` \| (?P<rest>.+)$"
)

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


def ledger_text() -> str:
    return LEDGER.read_text(encoding="utf-8")


def ledger_field(text: str, name: str) -> str:
    """One held-frontier bullet, read the way tests.test_evolution_contract reads it."""
    for match in HEADER_BULLET.finditer(text):
        if match.group("name") == name:
            return match.group("value").strip().strip("`")
    raise AssertionError(f"the ephoros ledger has no {name!r} bullet")


def ledger_rows(text: str) -> list[dict]:
    return [match.groupdict() for match in COMPACT_ROW.finditer(text)]


class LedgerRowTests(unittest.TestCase):
    """The evolution row this run adds says what the run measured."""

    def test_the_ledger_holds_exactly_one_row_for_this_version(self):
        rows = [row for row in ledger_rows(ledger_text()) if row["version"] == LEDGER_ROW_VERSION]
        self.assertEqual(len(rows), 1, f"expected one {LEDGER_ROW_VERSION} row, found {len(rows)}")
        self.assertEqual(rows[0]["axis"], "evolution")

    def test_the_row_digest_is_the_sha256_of_the_ledger_canonical_line(self):
        text = ledger_text()
        canonical = "|".join(ledger_field(text, name) for name in FRONTIER_FIELDS) + "\n"
        recomputed = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        rows = ledger_rows(text)
        self.assertTrue(rows, "the ephoros ledger has no compact history row")
        self.assertEqual(rows[-1]["version"], LEDGER_ROW_VERSION)
        self.assertEqual(rows[-1]["digest"], recomputed)

    def test_the_skill_frontmatter_version_equals_the_ledger_current_version(self):
        metadata = re.search(r'(?m)^  version: "(\d+\.\d+\.\d+)"$', SKILL.read_text(encoding="utf-8"))
        self.assertIsNotNone(metadata, "ephoros SKILL.md has no metadata.version")
        self.assertEqual(f"ephoros-v{metadata.group(1)}", ledger_field(ledger_text(), "Current version"))
        self.assertEqual(f"ephoros-v{metadata.group(1)}", LEDGER_ROW_VERSION)

    def test_the_row_names_the_clone_commit_and_the_e001_count(self):
        rows = [row for row in ledger_rows(ledger_text()) if row["version"] == LEDGER_ROW_VERSION]
        self.assertEqual(len(rows), 1)
        rest = rows[0]["rest"]
        self.assertIn(f"`{CLONE_COMMIT}`", rest)
        self.assertRegex(rest, rf"E001 reports {CLONE_E001_COUNT} findings")
        self.assertIn("none suppressed", rest)


class ShippedCopyRefreshTests(unittest.TestCase):
    """The shipped copies carry the receipted state, and the closed offer is gone."""

    def test_futureproofing_no_longer_offers_typescript_parity_for_e001_to_e003(self):
        lines = FUTUREPROOFING.read_text(encoding="utf-8").splitlines()
        offers = [line for line in lines if "TypeScript parity for Ephoros rules E001 to E003" in line]
        self.assertEqual(offers, [], "FUTUREPROOFING.md still offers a job this run closed")

    def test_each_shipped_copy_carries_the_receipted_amendment_count(self):
        for path, expected in SHIPPED_AMENDMENT_COUNTS.items():
            with self.subTest(path=path.name):
                lines = path.read_text(encoding="utf-8").splitlines()
                found = sum(1 for line in lines if line.startswith(AMENDMENT_HEADING))
                self.assertEqual(found, expected, f"{path.name} carries {found} amendment headings, receipted {expected}")


if __name__ == "__main__":
    unittest.main()
