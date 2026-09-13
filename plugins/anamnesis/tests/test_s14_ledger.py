"""Step 14: the ledger records the resolved mapper, and the live prose agrees.

Two regions are outside the prose sweep and both are records rather than
descriptions. The design records under `docs/` say what was true when they were
written, and the ledger's own history rows are append-only, so correcting
either would be rewriting history. Everything else under `plugins/anamnesis/`
is swept, preserved specimens included: a producer's bytes may not be edited,
so a specimen that ever carried one of these phrases is a reason to narrow the
sweep deliberately rather than a defect to silently skip.
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

VERSION = "anamnesis-v5.1.0"
REVISION = "resolved-mapper"
PRIOR_VERSION = "anamnesis-v4.1.0"
PRIOR_REVISION = "declared-scope"
PRIOR_DIGEST = "13c730d9f26091188d16c8c640632c21943fe3f85b2c9363c70b8e0ed499965e"

# The two claims this run made false. The first says the declaration selected
# nothing; the second says an assertion attested a string no code had checked.
STALE = (
    "always runs `warden-audit-round-markdown`",
    "resolver always runs",
    "records the declared name",
)
INPUT_ID = "second-producer-findings"

STUDY = PLUGIN_ROOT / "docs/resolved-mapper-study.md"
RUNBOOK = PLUGIN_ROOT / "docs/resolved-mapper-runbook.md"
RUN_STUDY = WORKTREE / ".hexaemeron/study.md"
RUN_RUNBOOK = WORKTREE / ".hexaemeron/runbook.md"


def header_field(text: str, name: str) -> str:
    return re.search(rf"^- {re.escape(name)}: (.*)$", text, re.M).group(1).strip()


def rows(text: str) -> list[list[str]]:
    found = []
    for line in text.splitlines():
        if line.startswith("| `anamnesis-v"):
            found.append([cell.strip() for cell in line.strip("|").split("|")])
    return found


def swept() -> list[Path]:
    """Every live Markdown surface of the member, history and docs aside."""
    return [
        path
        for path in sorted(PLUGIN_ROOT.rglob("*.md"))
        if "docs" not in path.relative_to(PLUGIN_ROOT).parts
    ]


def live_prose(path: Path) -> str:
    """One swept document, with the ledger's append-only history cut off."""
    text = path.read_text(encoding="utf-8")
    return text.split("\n## History", 1)[0] if path == LEDGER else text


class LedgerRecordsTheResolvedMapper(unittest.TestCase):
    def setUp(self) -> None:
        self.text = LEDGER.read_text(encoding="utf-8")
        self.rows = rows(self.text)

    def test_the_header_version_matches_the_newest_row(self) -> None:
        header = header_field(self.text, "Current version").strip("`")
        self.assertEqual(header, VERSION)
        self.assertEqual(self.rows[-1][0].strip("`"), header)
        self.assertEqual(self.rows[-1][1], "evolution")
        self.assertEqual(self.rows[-1][2].strip("`"), REVISION)

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

    def test_the_superseded_row_keeps_its_revision_and_digest(self) -> None:
        prior = [row for row in self.rows if row[0].strip("`") == PRIOR_VERSION]
        self.assertEqual(len(prior), 1)
        self.assertEqual(prior[0][2].strip("`"), PRIOR_REVISION)
        self.assertEqual(prior[0][3].strip("`"), PRIOR_DIGEST)

    def test_the_skill_frontmatter_version_matches_the_header(self) -> None:
        declared = re.search(r'^  version: "(.+)"$', SKILL.read_text(encoding="utf-8"), re.M)
        self.assertEqual(
            f"anamnesis-v{declared.group(1)}",
            header_field(self.text, "Current version").strip("`"),
        )

    def test_the_declared_input_names_what_is_now_actually_missing(self) -> None:
        """The row the shipped corpus made false, replaced.

        `foreign-format-corpus` called a corpus in a format the Warden mapper
        does not read absent. This run shipped one, so the note may not repeat
        that claim; what is still absent is a second producer's findings and a
        rights basis to redistribute them.
        """
        block = self.text.split("```declared-inputs", 1)[1].split("```", 1)[0]
        lines = [line for line in block.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1)
        fields = [part.strip() for part in lines[0].split("|")]
        self.assertEqual(len(fields), 4)
        self.assertTrue(all(fields), fields)
        identifier, kind, availability, note = fields
        self.assertEqual(identifier, INPUT_ID)
        self.assertEqual(kind, "corpus")
        self.assertEqual(availability, "absent")
        self.assertLessEqual(len(note.encode("utf-8")), 200)
        self.assertNotIn("Warden", note)
        self.assertNotIn("does not read", note)
        self.assertIn("rights basis", note)


class LiveProseAgreesWithTheLedger(unittest.TestCase):
    def test_the_front_door_status_block_names_the_current_version(self) -> None:
        text = README.read_text(encoding="utf-8")
        self.assertIn(f'<!-- front-door:status skill="anamnesis" version="{VERSION}" -->', text)

    def test_no_live_document_still_says_the_declaration_selects_nothing(self) -> None:
        documents = swept()
        # Not a count: naming the three surfaces the run edited keeps an
        # over-broad exclusion from emptying the sweep and passing on nothing.
        for named in (SKILL, README, PLUGIN_ROOT / "AGENTS.md"):
            self.assertIn(named, documents, f"{named} dropped out of the sweep")
        for path in documents:
            text = live_prose(path)
            for claim in STALE:
                with self.subTest(path=path.relative_to(PLUGIN_ROOT), claim=claim):
                    self.assertNotIn(claim, text)


class CommittedDocumentsTrackTheRun(unittest.TestCase):
    def test_the_committed_documents_equal_the_receipted_artefacts(self) -> None:
        """Byte identity where the controller is present.

        `.hexaemeron/` exists only inside the run's own worktree, so this
        skips everywhere else. Step 11 pins the same two documents by SHA-256
        for the checkouts that have no controller to compare against.
        """
        for committed, artefact in ((STUDY, RUN_STUDY), (RUNBOOK, RUN_RUNBOOK)):
            with self.subTest(document=committed.name):
                if not artefact.exists():
                    self.skipTest(f"{artefact} is not in this checkout")
                self.assertEqual(committed.read_bytes(), artefact.read_bytes())


if __name__ == "__main__":
    unittest.main()
