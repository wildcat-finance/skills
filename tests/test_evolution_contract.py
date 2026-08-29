"""Govern every skill evolution ledger in the marketplace.

Hexaemeron-local rules stay in plugins/hexaemeron/tests/test_evolution.py.
This file owns the rules that hold for every governed skill, wherever it
lives, and deliberately assumes nothing about baseline version numbers:
skills adopt this contract at whatever version they already declared.
"""

from pathlib import Path
import hashlib
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"

# Vendored or third-party skills are not governed and keep no ledger. The
# bundled Pashov suite stays covered by Hexaemeron's own plugin frontier.
UNGOVERNED = {"fizz", "fizz-convert", "fizz-sync", "x-ray", "solidity-auditor"}

AXES = ("baseline", "evolution", "generation", "epoch")
FIAT_FRONTIER = (
    "load_state validates the version-1 state container spine in deterministic "
    "order before any command traverses it, with path-and-kind diagnostics shared "
    "by verify and mutations; delegated task identities can still expose an "
    "earlier issue when a collaboration handle is reused."
)
FIAT_NEXT_JOB = (
    "Complete [skills#363](https://github.com/wildcat-finance/skills/issues/363): "
    "bind every Fiat delegation task identity to the current issue or topic, step "
    "number and role, refusing or replacing a stale reused handle. Accepted when a "
    "task for issue N cannot retain issue M in its visible name, Surveyor, Mason, "
    "Warden and Scribe expose current deterministic identities, resume and "
    "post-compaction reconstruction preserve them, and an executable regression "
    "rejects stale reuse."
)


def field(text, name):
    match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", text)
    if match is None:
        raise AssertionError(f"missing {name}")
    return match.group(1).strip().strip("`")


def version_parts(label, skill):
    match = re.fullmatch(rf"{re.escape(skill)}-v(\d+)\.(\d+)\.(\d+)", label)
    if match is None:
        raise AssertionError(f"invalid version label for {skill}: {label}")
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


def governed_skills():
    """Every skill directory holding a SKILL.md, minus the ungoverned ones."""
    for skill_md in sorted(PLUGINS.glob("*/skills/**/SKILL.md")):
        directory = skill_md.parent
        if directory.name in UNGOVERNED:
            continue
        yield directory.name, directory


class EvolutionContractTests(unittest.TestCase):
    def test_sapheneia_generation_keeps_the_held_frontier(self):
        ledger = (
            PLUGINS / "sapheneia" / "skills" / "sapheneia" / "EVOLUTION.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(field(ledger, "Current version"), "sapheneia-v0.2.0")
        self.assertEqual(field(ledger, "Frontier status"), "open")
        self.assertEqual(field(ledger, "Frontier revision"), "cross-model-corpus")
        self.assertEqual(
            field(ledger, "Current frontier"),
            "Cross-model behaviour has not yet been held against a published AuDHD task corpus.",
        )
        self.assertEqual(
            field(ledger, "Next Fiat job"),
            "Build and publish a held cross-model corpus covering debugging, explanation, destructive-action and long-running task turns, then reconcile the ten rules against its results. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.",
        )
        latest = history_rows(ledger)[-1]
        self.assertEqual(latest["version"], "sapheneia-v0.2.0")
        self.assertEqual(latest["axis"], "generation")
        self.assertEqual(latest["revision"], "cross-model-corpus")
        self.assertEqual(
            latest["digest"],
            "06034ab3a9291b328ab65bef2436652833ac137dcb5726dee911a08fa632df87",
        )

    def test_fiat_state_shape_frontier_holds_the_task_identity_successor(self):
        ledger = (
            PLUGINS / "hexaemeron" / "skills" / "fiat" / "EVOLUTION.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(field(ledger, "Current version"), "fiat-v5.35.1")
        self.assertEqual(field(ledger, "Frontier status"), "open")
        self.assertEqual(field(ledger, "Frontier revision"), "state-shape-validation")
        self.assertEqual(field(ledger, "Current frontier"), FIAT_FRONTIER)
        self.assertEqual(field(ledger, "Next Fiat job"), FIAT_NEXT_JOB)
        latest = history_rows(ledger)[-1]
        self.assertEqual(latest["version"], "fiat-v5.35.1")
        self.assertEqual(latest["axis"], "generation")
        self.assertEqual(latest["revision"], "state-shape-validation")
        self.assertEqual(
            latest["digest"],
            "e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa",
        )
        self.assertIn("skills/issues/557", latest["evidence"])
        self.assertIn("ADR-028", latest["evidence"])
        self.assertIn("fiat-controller-checkpoint-study.md", latest["evidence"])
        self.assertIn("fiat-controller-checkpoint-runbook.md", latest["evidence"])
        self.assertIn("checkpoint export", latest["change"])
        self.assertIn("checkpoint restore", latest["change"])
        self.assertIn("same ledger", latest["change"])
        predecessor = history_rows(ledger)[-2]
        self.assertEqual(predecessor["version"], "fiat-v5.34.1")
        self.assertIn("Creator direction, 2026-08-29", predecessor["evidence"])
        self.assertIn("audit.max_rounds", predecessor["evidence"])
        earlier = history_rows(ledger)[-3]
        self.assertEqual(earlier["version"], "fiat-v5.33.1")
        self.assertIn("Creator direction, 2026-08-28", earlier["evidence"])
        self.assertIn("completed run", earlier["evidence"])
        integrated = history_rows(ledger)[-4]
        self.assertEqual(integrated["version"], "fiat-v5.32.1")
        self.assertIn("skills/issues/710", integrated["evidence"])
        self.assertIn("issuecomment-5451995033", integrated["evidence"])
        base_fix = history_rows(ledger)[-5]
        self.assertEqual(base_fix["version"], "fiat-v5.31.1")
        self.assertIn("skills/issues/710", base_fix["evidence"])
        self.assertIn("ADR-044", base_fix["evidence"])
        published = history_rows(ledger)[-6]
        self.assertEqual(published["version"], "fiat-v5.30.1")
        self.assertIn("skills/issues/622", published["evidence"])
        self.assertIn("Creator direction, 2026-08-27", published["evidence"])
        checkpoint = history_rows(ledger)[-7]
        self.assertEqual(checkpoint["version"], "fiat-v5.29.1")
        self.assertIn("issuecomment-5435028801", checkpoint["evidence"])
        self.assertIn("issuecomment-5435304048", checkpoint["evidence"])
        base_head = history_rows(ledger)[-8]
        self.assertEqual(base_head["version"], "fiat-v5.28.1")
        self.assertIn("skills/issues/608", base_head["evidence"])
        self.assertIn("fiat-integrate-base-head-study.md", base_head["evidence"])
        self.assertIn("fiat-integrate-base-head-runbook.md", base_head["evidence"])

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

    def test_every_governed_skill_has_a_ledger(self):
        for skill, directory in governed_skills():
            with self.subTest(skill=skill):
                self.assertTrue(
                    (directory / "EVOLUTION.md").is_file(),
                    f"{directory} has no EVOLUTION.md; add one or list it as ungoverned",
                )
                self.assertIn(
                    "[EVOLUTION.md](EVOLUTION.md)",
                    (directory / "SKILL.md").read_text(encoding="utf-8"),
                )

    def test_skill_metadata_matches_current_ledger_version(self):
        for skill, directory in governed_skills():
            instructions = (directory / "SKILL.md").read_text(encoding="utf-8")
            ledger = (directory / "EVOLUTION.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                metadata = re.search(r'(?m)^  version: "(\d+\.\d+\.\d+)"$', instructions)
                self.assertIsNotNone(metadata, f"{skill} has no metadata.version")
                self.assertEqual(
                    field(ledger, "Current version"), f"{skill}-v{metadata.group(1)}"
                )

    def test_current_frontier_digest_matches_latest_history_row(self):
        for skill, directory in governed_skills():
            ledger = (directory / "EVOLUTION.md").read_text(encoding="utf-8")
            canonical = "|".join(
                (
                    field(ledger, "Frontier status"),
                    field(ledger, "Frontier revision"),
                    field(ledger, "Current frontier"),
                    field(ledger, "Next Fiat job"),
                )
            ) + "\n"
            rows = history_rows(ledger)
            with self.subTest(skill=skill):
                self.assertGreaterEqual(len(rows), 1)
                self.assertEqual(rows[-1]["version"], field(ledger, "Current version"))
                self.assertEqual(rows[-1]["revision"], field(ledger, "Frontier revision"))
                self.assertEqual(
                    rows[-1]["digest"],
                    hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                )

    def test_history_axes_enforce_independent_counters_and_frontier_hold(self):
        for skill, directory in governed_skills():
            ledger = (directory / "EVOLUTION.md").read_text(encoding="utf-8")
            rows = history_rows(ledger)
            with self.subTest(skill=skill):
                self.assertEqual(rows[0]["axis"], "baseline")
            previous = rows[0]
            previous_version = version_parts(rows[0]["version"], skill)
            for row in rows[1:]:
                current_version = version_parts(row["version"], skill)
                with self.subTest(skill=skill, version=row["version"]):
                    if row["axis"] == "evolution":
                        self.assertEqual(
                            current_version,
                            (previous_version[0] + 1, previous_version[1], previous_version[2]),
                        )
                        self.assertNotEqual(row["digest"], previous["digest"])
                    elif row["axis"] == "generation":
                        self.assertEqual(
                            current_version,
                            (previous_version[0], previous_version[1] + 1, previous_version[2]),
                        )
                        self.assertEqual(row["revision"], previous["revision"])
                        self.assertEqual(row["digest"], previous["digest"])
                    elif row["axis"] == "epoch":
                        self.assertEqual(
                            current_version,
                            (previous_version[0], previous_version[1], previous_version[2] + 1),
                        )
                        if row["digest"] != previous["digest"]:
                            self.assertIn(
                                "reopen", (row["evidence"] + row["change"]).lower()
                            )
                previous = row
                previous_version = current_version

    def test_mature_frontiers_have_no_next_job(self):
        for skill, directory in governed_skills():
            ledger = (directory / "EVOLUTION.md").read_text(encoding="utf-8")
            status = field(ledger, "Frontier status")
            with self.subTest(skill=skill):
                self.assertIn(status, {"open", "mature"})
                if status == "mature":
                    self.assertEqual(field(ledger, "Next Fiat job"), "None -- mature")
                else:
                    self.assertNotEqual(field(ledger, "Next Fiat job"), "None -- mature")

    def test_ledgers_cite_the_versioning_contract(self):
        policy = (PLUGINS / "hexaemeron" / "skills" / "VERSIONING.md").resolve()
        for skill, directory in governed_skills():
            ledger_path = directory / "EVOLUTION.md"
            ledger = ledger_path.read_text(encoding="utf-8")
            match = re.search(r"(?m)^Policy: \[[^\]]+\]\(([^)]+)\)$", ledger)
            with self.subTest(skill=skill):
                self.assertIsNotNone(match, f"{skill} ledger cites no policy")
                self.assertEqual((ledger_path.parent / match.group(1)).resolve(), policy)


if __name__ == "__main__":
    unittest.main()
