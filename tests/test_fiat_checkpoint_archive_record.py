"""Keep the outer checkpoint archive decision in its draft record and ADR-028.

The study and runbook committed under `docs/` are run artefacts: they point at
the record and are not it. ADR-028 gains one dated amendment that cites the
record by its stable slug and changes no operative clause. The record states
the three commands and the designs that lost with their measurements. It lives
at `docs/decisions/drafts/<slug>.md` until the integration composer numbers it
and at `docs/decisions/ADR-NNN-<slug>.md` afterwards, so every check here finds
it by the slug and survives the numbering.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "docs/decisions"
ADR = DECISIONS / "ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md"
SLUG = "build-the-outer-checkpoint-archive-natively"
STABLE_REFERENCE = f"adr/{SLUG}"
DRAFT = DECISIONS / "drafts" / f"{SLUG}.md"
NUMBERED_NAME = re.compile(rf"^ADR-[0-9]{{3}}-{re.escape(SLUG)}\.md$")
FIRST_HEADING = re.compile(
    r"^# (?:Decision|ADR-[0-9]{3}): Build the outer checkpoint archive natively$")
STUDY = ROOT / "docs/fiat-checkpoint-archive-study.md"
RUNBOOK = ROOT / "docs/fiat-checkpoint-archive-runbook.md"

AMENDMENT = "## Amendment: Native outer archive (2026-09-07)"
PREVIOUS_AMENDMENT = "## Amendment: distributed layer reinstated (2026-09-02)"
HEADINGS_BEFORE_AMENDMENT = (
    "## Status",
    "## Context",
    "## Decision",
    "## Amendment: Native controller-state relocation (2026-08-29)",
    "### Compatibility repair (2026-08-30)",
    "## Amendment: Immutable run anchors and checkpoint identity (2026-08-29)",
    "## Amendment: Mandatory local checkpoint hand-off (2026-08-30)",
    "## Alternatives",
    "## Consequences",
    PREVIOUS_AMENDMENT,
)
REJECTED_AUTOMATION = "**Complete standing-checkpoint automation.** Rejected"
RELATIVE_LINK = re.compile(r"\[[^]]+\]\((?!https?://|#)([^)#]+)")
DATED_STATUS = re.compile(r"^(?:Proposed|Accepted), \d{4}-\d{2}-\d{2}")
SECTIONS = ("## Status", "## Context", "## Decision", "## Alternatives", "## Consequences")

# The artefact's own words for not being the decision, matched with the
# source's line wrapping collapsed.
NOT_THE_DECISION = {
    STUDY: "never described as the decision",
    RUNBOOK: "the decision homes",
}


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required Step 1 record is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def record_path() -> Path:
    """The one record carrying the stable slug: the draft, or the numbered file."""
    matches = sorted(
        p for p in DECISIONS.iterdir() if p.is_file() and NUMBERED_NAME.match(p.name)
    )
    if DRAFT.is_file():
        matches.append(DRAFT)
    if len(matches) != 1:
        found = [str(p.relative_to(ROOT)) for p in matches]
        raise AssertionError(f"expected one record for {SLUG}, found {found}")
    return matches[0]


def dead_relative_links(path: Path, text: str) -> list[str]:
    return [
        link for link in RELATIVE_LINK.findall(text)
        if not (path.parent / link).resolve().exists()
    ]


def status_first_line(text: str) -> str:
    body = text.split("## Status", 1)[1].split("\n## ", 1)[0]
    for line in body.splitlines():
        if line.strip():
            return line.strip()
    return ""


class FiatCheckpointArchiveRecord(unittest.TestCase):
    def test_run_artefacts_point_to_the_draft_record_and_adr_028_and_are_not_the_decision(self):
        for path in (STUDY, RUNBOOK):
            with self.subTest(path=path.name):
                text = read(path)
                self.assertIn(SLUG, text, f"{path.name} does not name the draft record")
                self.assertIn(ADR.name, text, f"{path.name} does not point to ADR-028")
                self.assertRegex(text, r"(?i)run artefacts?")
                self.assertIn(NOT_THE_DECISION[path], " ".join(text.split()))
                self.assertEqual([], dead_relative_links(path, text), f"dead relative links in {path.name}")

    def test_adr_028_amendment_points_at_the_draft_record_and_stays_accepted(self):
        text = read(ADR)
        status = text.split("## Context", 1)[0]
        self.assertIn("Accepted", status, "ADR-028's status no longer reads Accepted")

        self.assertIn(AMENDMENT, text)
        self.assertLess(text.index(PREVIOUS_AMENDMENT), text.index(AMENDMENT))
        before = text.split(AMENDMENT, 1)[0]
        headings = tuple(
            line for line in before.splitlines() if line.startswith("## ") or line.startswith("### ")
        )
        self.assertEqual(HEADINGS_BEFORE_AMENDMENT, headings, "a clause before the amendment moved")
        self.assertIn(REJECTED_AUTOMATION, before, "the rejected alternative was rewritten")

        amendment = text.split(AMENDMENT, 1)[1].split("\n## ", 1)[0]
        self.assertIn("no operative clause", amendment)
        self.assertIn("stays Accepted", amendment)
        self.assertEqual(
            1, amendment.count(STABLE_REFERENCE),
            "the amendment must cite the record by its stable slug reference once",
        )
        self.assertEqual(
            [], [link for link in RELATIVE_LINK.findall(amendment) if SLUG in link],
            "a relative link to the record dies when the composer renames it",
        )
        self.assertEqual([], dead_relative_links(ADR, text))

    def test_draft_record_states_the_three_commands_and_the_rejected_designs(self):
        path = record_path()
        text = read(path)
        self.assertRegex(text.splitlines()[0], FIRST_HEADING)
        for heading in SECTIONS:
            self.assertIn(f"\n{heading}\n", text, f"{path.name} lacks {heading}")
        self.assertRegex(status_first_line(text), DATED_STATUS)

        for command in (
            "hexctl --dir <run-worktree> checkpoint archive",
            "hexctl checkpoint inspect --archive <zip> --sha256 <outer-hex>",
            "hexctl --dir <empty-destination> checkpoint restore --archive <zip> --sha256 <outer-hex>",
        ):
            self.assertIn(command, text, f"{path.name} omits the command {command!r}")

        decision = text.split("\n## Decision\n", 1)[1].split("\n## ", 1)[0]
        for term in (
            "stored ZIP",
            "content manifest",
            "sidecars inside the zip",
            "nine entry paths",
            "pack.threads=1",
            "disposable keyring",
            "`remote.origin.url`",
            "fetches nothing",
        ):
            self.assertIn(term, decision, f"{path.name} decision omits {term!r}")

        alternatives = text.split("\n## Alternatives\n", 1)[1].split("\n## ", 1)[0]
        for candidate in ("`sidecar-script`", "`inspector-only`", "`external-archiver`"):
            self.assertIn(candidate, alternatives)
        for reading in (
            "26", "1,977", "335",
            "100,790,501", "100,470,196", "100,790,483",
            "| 2 |", "| 3 |", "| 4 |",
        ):
            self.assertIn(reading, alternatives, f"{path.name} omits the measured reading {reading!r}")

        self.assertEqual([], dead_relative_links(path, text), f"dead relative links in {path.name}")


if __name__ == "__main__":
    unittest.main()
