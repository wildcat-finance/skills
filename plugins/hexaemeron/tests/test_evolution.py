"""Govern first-party Hexaemeron skill versions and held frontiers."""

from pathlib import Path
import hashlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
FIRST_PARTY = ("fiat", "imprimatur", "vulgate", "kronos", "protasis", "elenchus", "phylax", "ephoros", "metron", "hypomnema")
PARENT_FRONTIER = (
    "The bundled Solidity audit suite has not yet been exercised in a "
    "published end-to-end Fiat delivery."
)


def field(text, name):
    match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", text)
    if match is None:
        raise AssertionError(f"missing {name}")
    return match.group(1).strip().strip("`")


def version_parts(label, skill):
    match = re.fullmatch(rf"{re.escape(skill)}-v(\d+)\.(\d+)\.(\d+)", label)
    if match is None:
        raise AssertionError(f"invalid version label: {label}")
    return tuple(int(part) for part in match.groups())


def history_rows(text):
    table = re.compile(
        r"^\| `(?P<version>[^`]+)` \| (?P<axis>baseline|evolution|generation|epoch) "
        r"\| `(?P<revision>[^`]+)` \| `(?P<digest>[0-9a-f]{64})` "
        r"\| (?P<evidence>.*?) \| (?P<change>.*?) \|$"
    )
    compact = re.compile(
        r"^- `(?P<version>[^`]+)` \| (?P<axis>baseline|evolution|generation|epoch) "
        r"\| `(?P<revision>[^`]+)` \| `(?P<digest>[0-9a-f]{64})` "
        r"\| (?P<evidence>.*?) \| (?P<change>.*?)$"
    )
    rows = []
    for line in text.splitlines():
        match = table.fullmatch(line) or compact.fullmatch(line)
        if match is not None:
            rows.append(match.groupdict())
    return rows


class EvolutionContractTests(unittest.TestCase):
    def test_history_rows_accept_compact_list(self):
        digest = "a" * 64
        rows = history_rows(
            f"- `example-v0.1.0` | baseline | `held-job` | `{digest}` | "
            "[evidence](README.md) | Versioning starts here."
        )
        self.assertEqual(
            rows,
            [
                {
                    "version": "example-v0.1.0",
                    "axis": "baseline",
                    "revision": "held-job",
                    "digest": digest,
                    "evidence": "[evidence](README.md)",
                    "change": "Versioning starts here.",
                }
            ],
        )

    def test_first_party_skills_have_governed_ledgers(self):
        for skill in FIRST_PARTY:
            directory = SKILLS / skill
            ledger = directory / "EVOLUTION.md"
            instructions = directory / "SKILL.md"
            with self.subTest(skill=skill):
                self.assertTrue(ledger.is_file())
                self.assertIn("[EVOLUTION.md](EVOLUTION.md)", instructions.read_text(encoding="utf-8"))

    def test_skill_metadata_matches_current_ledger_version(self):
        for skill in FIRST_PARTY:
            instructions = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            ledger = (SKILLS / skill / "EVOLUTION.md").read_text(encoding="utf-8")
            metadata = re.search(r'(?m)^  version: "(\d+\.\d+\.\d+)"$', instructions)
            self.assertIsNotNone(metadata, skill)
            current = field(ledger, "Current version")
            self.assertEqual(current, f"{skill}-v{metadata.group(1)}")

    def test_current_frontier_digest_matches_latest_history_row(self):
        for skill in FIRST_PARTY:
            ledger = (SKILLS / skill / "EVOLUTION.md").read_text(encoding="utf-8")
            canonical = "|".join(
                (
                    field(ledger, "Frontier status"),
                    field(ledger, "Frontier revision"),
                    field(ledger, "Current frontier"),
                    field(ledger, "Next Fiat job"),
                )
            ) + "\n"
            digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            rows = history_rows(ledger)
            self.assertGreaterEqual(len(rows), 1, skill)
            self.assertEqual(rows[-1]["version"], field(ledger, "Current version"))
            self.assertEqual(rows[-1]["digest"], digest)
            self.assertEqual(rows[-1]["revision"], field(ledger, "Frontier revision"))

    def test_axes_enforce_independent_counters_frontier_hold(self):
        for skill in FIRST_PARTY:
            ledger = (SKILLS / skill / "EVOLUTION.md").read_text(encoding="utf-8")
            rows = history_rows(ledger)
            self.assertEqual(rows[0]["axis"], "baseline")
            # Baselines are adopted, not assigned: a skill enters the contract at
            # whatever version it already declared, so no fixed pair holds across
            # the marketplace. Assert the label parses; tests/test_evolution_contract.py
            # owns the rules that span every governed skill.
            version_parts(rows[0]["version"], skill)
            previous = rows[0]
            previous_version = version_parts(previous["version"], skill)
            for row in rows[1:]:
                current_version = version_parts(row["version"], skill)
                with self.subTest(skill=skill, version=row["version"]):
                    if row["axis"] == "evolution":
                        self.assertEqual(current_version, (previous_version[0] + 1, previous_version[1], previous_version[2]))
                        self.assertNotEqual(row["digest"], previous["digest"])
                    elif row["axis"] == "generation":
                        self.assertEqual(current_version, (previous_version[0], previous_version[1] + 1, previous_version[2]))
                        self.assertEqual(row["revision"], previous["revision"])
                        self.assertEqual(row["digest"], previous["digest"])
                    elif row["axis"] == "epoch":
                        self.assertEqual(current_version, (previous_version[0], previous_version[1], previous_version[2] + 1))
                        if row["digest"] != previous["digest"]:
                            self.assertIn("reopen", (row["evidence"] + row["change"]).lower())
                previous = row
                previous_version = current_version

    def test_mature_frontiers_have_no_next_job(self):
        for skill in FIRST_PARTY:
            ledger = (SKILLS / skill / "EVOLUTION.md").read_text(encoding="utf-8")
            status = field(ledger, "Frontier status")
            self.assertIn(status, {"open", "mature"})
            if status == "mature":
                self.assertEqual(field(ledger, "Next Fiat job"), "None -- mature")

    def test_subsidiaries_do_not_inherit_parent_frontier(self):
        for skill in FIRST_PARTY:
            instructions = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertNotIn(PARENT_FRONTIER, instructions)
                self.assertNotIn("<!-- marketplace-context:start -->", instructions)

    def test_fiat_resolves_controller_from_active_skill_file(self):
        fiat = (SKILLS / "fiat" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("FIAT_SKILL_FILE=<exact path of the active fiat/SKILL.md>", fiat)
        self.assertIn('"$FIAT_SKILL_DIR/scripts/hexctl.py"', fiat)
        self.assertIn('--dir "$PROJECT_ROOT"', fiat)
        self.assertNotIn('"$SKILL_DIR/scripts/hexctl.py"', fiat)
        self.assertNotIn('--dir "$PWD"', fiat)

    def test_fiat_refuses_mature_or_exhausted_frontiers(self):
        fiat = (SKILLS / "fiat" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("If its frontier status is `mature`, refuse to start or resume", fiat)
        self.assertIn("do not overseason", fiat)
        self.assertIn("Never run or recommend a frontier Fiat job", fiat)

    def test_kronos_only_ranks_and_loops_eligible_frontiers(self):
        kronos = (SKILLS / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("material user or protocol impact: 40", kronos)
        self.assertIn("evidenced urgency or defect severity: 25", kronos)
        self.assertIn("readiness of inputs and acceptance conditions: 20", kronos)
        self.assertIn("work it unblocks or shapes in other in-scope skills: 15", kronos)
        self.assertIn("Never create one goal\n   per skill", kronos)
        self.assertIn("Invoke Fiat with the held Next Fiat job byte for byte", kronos)
        self.assertIn("Kronos itself", kronos)
        self.assertIn("Never edit, implement, audit, or rewrite a target itself", kronos)

    def test_kronos_phase_only_mode_keeps_loop_closes_market(self):
        kronos = (SKILLS / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        phase_mode = kronos.split("## Phase-only mode", 1)[1].split("## Loop", 1)[0]
        for skill in ("Protasis", "Phylax", "Ephoros", "Metron", "Elenchus", "Hypomnema"):
            self.assertIn(skill, phase_mode)
        self.assertIn("Do not discover, report, score, select or start", phase_mode)
        self.assertIn("rescan all six phase ledgers from disk and no others", phase_mode)
        self.assertIn("rerank from scratch and\nrepeat", phase_mode)
        self.assertIn("stop only when none of the six\nphase ledgers remains eligible", phase_mode)
        self.assertIn("iteration cap", phase_mode)


if __name__ == "__main__":
    unittest.main()
