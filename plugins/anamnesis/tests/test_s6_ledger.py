"""Step 6: the ledger records the completed job, and the live prose agrees with it.

The frozen design records under docs/synkrisis-admission-*.md and the append-only
history rows are excluded from the prose sweep on purpose: both are records of
what was true when they were written, and correcting them would be rewriting
history rather than reconciling prose.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
LEDGER = PLUGIN_ROOT / "skills/anamnesis/EVOLUTION.md"
SKILL = PLUGIN_ROOT / "skills/anamnesis/SKILL.md"

LIVE_PROSE = (
    PLUGIN_ROOT / "skills/anamnesis/SKILL.md",
    PLUGIN_ROOT / "README.md",
    PLUGIN_ROOT / "AGENTS.md",
)
STALE_CLAIMS = ("has not been made", "does not yet admit")

PRIOR_REVISION = "synkrisis-producer-admission"
PRIOR_DIGEST = "427bebd06deb3114fc00c0be50b6de44f2d1f2ebd36ed8788fb826983dea77cf"


def header_field(text: str, name: str) -> str:
    return re.search(rf"^- {re.escape(name)}: (.*)$", text, re.M).group(1).strip()


def rows(text: str) -> list[list[str]]:
    found = []
    for line in text.splitlines():
        if line.startswith("| `anamnesis-v"):
            found.append([cell.strip() for cell in line.strip("|").split("|")])
    return found


class LedgerRecordsTheCompletedJob(unittest.TestCase):
    def setUp(self) -> None:
        self.text = LEDGER.read_text(encoding="utf-8")
        self.rows = rows(self.text)

    def test_the_header_version_matches_the_newest_row(self) -> None:
        header = header_field(self.text, "Current version").strip("`")
        self.assertEqual(header, "anamnesis-v3.1.0")
        self.assertEqual(self.rows[-1][0].strip("`"), header)
        self.assertEqual(self.rows[-1][1], "evolution")

    def test_the_frontier_digest_recomputes_over_its_exact_line(self) -> None:
        line = "{}|{}|{}|{}\n".format(
            header_field(self.text, "Frontier status").strip("`"),
            header_field(self.text, "Frontier revision").strip("`"),
            header_field(self.text, "Current frontier"),
            header_field(self.text, "Next Fiat job"),
        )
        self.assertEqual(
            hashlib.sha256(line.encode("utf-8")).hexdigest(),
            self.rows[-1][3].strip("`"),
        )

    def test_the_skill_frontmatter_version_matches_the_ledger(self) -> None:
        declared = re.search(r'^  version: "(.+)"$', SKILL.read_text(encoding="utf-8"), re.M)
        self.assertEqual(
            f"anamnesis-v{declared.group(1)}",
            header_field(self.text, "Current version").strip("`"),
        )

    def test_the_superseded_row_keeps_its_revision_and_digest(self) -> None:
        prior = [row for row in self.rows if row[0].strip("`") == "anamnesis-v2.1.0"]
        self.assertEqual(len(prior), 1)
        self.assertEqual(prior[0][2].strip("`"), PRIOR_REVISION)
        self.assertEqual(prior[0][3].strip("`"), PRIOR_DIGEST)


class LiveProseAgreesWithTheDecision(unittest.TestCase):
    def test_no_live_document_still_says_the_decision_is_unmade(self) -> None:
        for path in LIVE_PROSE:
            # Not a skip: a renamed or deleted document would otherwise drop out
            # of the sweep silently and leave this passing on less than it names.
            self.assertTrue(path.is_file(), f"{path} is named here but absent")
            text = path.read_text(encoding="utf-8")
            for claim in STALE_CLAIMS:
                with self.subTest(path=path.name, claim=claim):
                    self.assertNotIn(claim, text)


if __name__ == "__main__":
    unittest.main()
