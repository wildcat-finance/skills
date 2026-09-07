"""Step 10: the ledger records the completed job, and the live prose agrees.

The frozen design records under docs/ and the append-only history rows are
excluded from the prose sweep on purpose: both record what was true when they
were written, and correcting them would be rewriting history rather than
reconciling prose.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
WORKTREE = PLUGIN_ROOT.parents[1]
LEDGER = PLUGIN_ROOT / "skills/anamnesis/EVOLUTION.md"
SKILL = PLUGIN_ROOT / "skills/anamnesis/SKILL.md"
README = PLUGIN_ROOT / "README.md"

VERSION = "anamnesis-v4.1.0"
PRIOR_VERSION = "anamnesis-v3.1.0"
PRIOR_REVISION = "corpus-scope"
PRIOR_DIGEST = "1da8d2f843cb3b0ff1fd6dac5d41d4cafb5746388635c3f1ba5e41adde1d1f77"
STALE = ("resolver-side constant", "hand-picked pilot", "beyond the pilot")
# The ledger's own history and the shipped design records say what was true when
# they were written; the sweep is over prose that describes the member now.
SWEPT = (
    PLUGIN_ROOT / "skills/anamnesis/SKILL.md",
    PLUGIN_ROOT / "README.md",
    PLUGIN_ROOT / "AGENTS.md",
)
INPUT_ROW = re.compile(r"^[a-z0-9-]{1,64} \| (?:credential|endpoint|person|corpus|tool) \| "
                       r"(?:available|absent|unknown) \| .{1,200}$")


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
        self.assertEqual(header, VERSION)
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

    def test_the_evolution_counter_moved_once_and_no_other(self) -> None:
        def parts(version: str) -> tuple[int, ...]:
            return tuple(int(n) for n in version.strip("`").removeprefix("anamnesis-v").split("."))

        self.assertEqual(parts(self.rows[-1][0]), (4, 1, 0))
        self.assertEqual(parts(self.rows[-2][0]), (3, 1, 0))

    def test_the_superseded_row_keeps_its_revision_and_digest(self) -> None:
        prior = [row for row in self.rows if row[0].strip("`") == PRIOR_VERSION]
        self.assertEqual(len(prior), 1)
        self.assertEqual(prior[0][2].strip("`"), PRIOR_REVISION)
        self.assertEqual(prior[0][3].strip("`"), PRIOR_DIGEST)

    def test_the_skill_frontmatter_version_matches_the_ledger(self) -> None:
        declared = re.search(r'^  version: "(.+)"$', SKILL.read_text(encoding="utf-8"), re.M)
        self.assertEqual(f"anamnesis-v{declared.group(1)}", VERSION)

    def test_the_declared_input_the_next_job_needs_is_one_valid_row(self) -> None:
        block = self.text.split("```declared-inputs", 1)[1].split("```", 1)[0]
        lines = [line for line in block.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], INPUT_ROW)
        self.assertTrue(lines[0].startswith("foreign-format-corpus | corpus | absent | "))


class LiveProseAgreesWithTheLedger(unittest.TestCase):
    def test_the_front_door_card_names_the_current_version(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(f'<!-- front-door:status skill="anamnesis" version="{VERSION}" -->', text)

    def test_no_live_document_still_describes_the_question_as_open(self) -> None:
        for path in SWEPT:
            # Not a skip: a renamed or deleted document would otherwise drop out
            # of the sweep silently and leave this passing on less than it names.
            self.assertTrue(path.is_file(), f"{path} is named here but absent")
            text = path.read_text(encoding="utf-8")
            for claim in STALE:
                with self.subTest(path=path.name, claim=claim):
                    self.assertNotIn(claim, text)

    def test_both_declared_scopes_are_named_where_a_reader_starts(self) -> None:
        text = README.read_text(encoding="utf-8")
        for scope in ("Warden seed pilot", "capture estate"):
            with self.subTest(scope=scope):
                self.assertIn(scope, text)


if __name__ == "__main__":
    unittest.main()
