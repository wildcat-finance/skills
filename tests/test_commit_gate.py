"""Hold the commit gate to what the run behind it promised.

The gate itself arrives in a later step. What is held here first is the record
that says where it lives, because the record is the part a reader reaches for
once the scripts are ordinary and nobody remembers the alternatives.

The record ships unnumbered. The arithmetic against this base gives ADR-074 and
run #856 is open on the same base claiming the same number;
`tests/test_decision_records.py` compares against `origin/main`, so it sees the
collision only once the other number has landed. That check is left exactly as
it is, and it globs `ADR-*.md`, so it never sees a draft. These cases hold the
draft's shape in its place, and one of them refuses an `ADR-074-*.md` file so
the run cannot drift back into the collision it is avoiding.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = REPOSITORY_ROOT / "docs" / "decisions"
RECORD = DECISIONS / "draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md"

REQUIRED_SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")
NUMBERED_HEADING = re.compile(r"\A#\s*ADR-\d+\b")
SECTION_HEADING = re.compile(r"\A##\s+(?P<name>\S.*?)\s*\Z")

# Each rejected option from the study's design section, and the word the record
# has to reach for beside it. Naming an option without saying what it cost is
# the failure mode the issue's first acceptance condition is aimed at.
REJECTED = ("installed-hooks", "ci-only", "null option")


def record_text() -> str:
    return RECORD.read_text(encoding="utf-8")


def sections(text: str) -> dict[str, str]:
    """The record's `## ` sections, each mapped to its own body."""
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        heading = SECTION_HEADING.match(line)
        if heading:
            current = heading.group("name")
            found.setdefault(current, [])
            continue
        if current is not None:
            found[current].append(line)
    return {name: "\n".join(body) for name, body in found.items()}


def bullets(body: str) -> list[str]:
    """Top-level `- ` bullets, each carrying its indented continuation lines."""
    found: list[list[str]] = []
    for line in body.splitlines():
        if line.startswith("- "):
            found.append([line])
        elif found and line.strip() and line.startswith(" "):
            found[-1].append(line)
    return [" ".join(part.strip() for part in block) for block in found]


class DecisionRecordTests(unittest.TestCase):
    def test_the_record_is_at_the_path_the_runbook_names(self):
        self.assertTrue(
            RECORD.is_file(),
            f"the decision record for the commit gate is not at {RECORD}",
        )

    def test_the_first_heading_is_a_title_rather_than_a_number(self):
        """A numbered heading here would claim a number nothing has assigned.

        The filename carries no `ADR-` prefix, so the heading must not carry a
        number either; the two disagreeing is exactly what
        `tests/test_decision_records.py` catches on the records it does see.
        """
        first = record_text().lstrip().splitlines()[0]
        self.assertTrue(first.startswith("# "), f"first heading is not an H1: {first!r}")
        self.assertIsNone(
            NUMBERED_HEADING.match(first),
            f"the draft claims a number nothing has assigned yet: {first!r}",
        )

    def test_the_record_carries_every_required_section(self):
        present = sections(record_text())
        missing = [name for name in REQUIRED_SECTIONS if name not in present]
        self.assertEqual(missing, [], f"sections missing from {RECORD.name}: {missing}")

    def test_the_alternatives_say_what_each_rejected_option_loses(self):
        body = sections(record_text()).get("Alternatives", "")
        self.assertTrue(body.strip(), "the Alternatives section is empty")
        silent = []
        for option in REJECTED:
            named = [b for b in bullets(body) if option in b]
            if not named:
                silent.append(f"{option}: not named")
            elif not any("loses" in b for b in named):
                silent.append(f"{option}: named without saying what it loses")
        self.assertEqual(silent, [], "; ".join(silent))

    def test_the_consequences_call_the_green_record_a_convenience(self):
        body = sections(record_text()).get("Consequences", "")
        self.assertIn(
            "convenience rather than proof", body,
            "the consequences must state that the green record is a convenience "
            "rather than proof that the suite ran; a reader who takes it as "
            "proof is trusting a record its own subject can write",
        )

    def test_no_record_claims_the_number_this_draft_is_avoiding(self):
        claimed = sorted(p.name for p in DECISIONS.glob("ADR-074-*.md"))
        self.assertEqual(
            claimed, [],
            "this run ships its record unnumbered because run #856 is open on "
            f"the same base and claims ADR-074; found {claimed}",
        )


if __name__ == "__main__":
    unittest.main()
