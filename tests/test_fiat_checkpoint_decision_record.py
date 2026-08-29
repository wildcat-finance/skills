"""Keep Fiat's native checkpoint design in its accepted decision record."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
ADR = ROOT / "docs/decisions/ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md"
STUDY = ROOT / "docs/fiat-controller-checkpoint-study.md"
RUNBOOK = ROOT / "docs/fiat-controller-checkpoint-runbook.md"

EXPECTED_DIGESTS = {
    STUDY: "ef73798be8ed333cce2626c9a5ccd4a59bb7877217ae8516be1665daa619b000",
    RUNBOOK: "83577005612e532cbd56e589e1bac0aa7d27a2fa1eab0f765b840a6b91e88121",
}


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required Step 1 record is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


class FiatCheckpointDecisionRecord(unittest.TestCase):
    def test_run_artefacts_match_their_receipted_sources(self):
        mismatches = {}
        for path, expected in EXPECTED_DIGESTS.items():
            if not path.is_file():
                mismatches[str(path.relative_to(ROOT))] = "missing"
                continue
            actual = sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                mismatches[str(path.relative_to(ROOT))] = actual
        self.assertEqual({}, mismatches)

    def test_run_artefacts_point_to_adr_028_as_the_standing_record(self):
        for path in (STUDY, RUNBOOK):
            with self.subTest(path=path.name):
                text = read(path)
                self.assertIn(ADR.name, text, f"{path.name} does not point to ADR-028")
                self.assertRegex(text, r"(?i)run artefacts?")
                self.assertRegex(
                    text,
                    r"(?i)(?:not|neither|never).{0,80}(?:standing decision record|durable decision home)",
                )

                relative_links = re.findall(r"\[[^]]+\]\((?!https?://|#)([^)#]+)", text)
                dead = [link for link in relative_links if not (path.parent / link).resolve().exists()]
                self.assertEqual([], dead, f"dead relative links in {path.name}")

    def test_adr_records_the_accepted_native_recovery_design(self):
        text = read(ADR)
        required = (
            "## Amendment: Native controller-state relocation (2026-08-29)",
            "`fiat-controller-checkpoint/v1`",
            "same ledger",
            "`checkpoint:restore`",
            "Git bundle",
            "Drive",
            "issue note",
            "manual outer transport",
            "semantic checkpoint identity",
        )
        missing = [item for item in required if item not in text]
        self.assertEqual([], missing, "ADR-028 omits accepted recovery design terms")

    def test_adr_records_the_rejected_designs(self):
        text = read(ADR)
        required = (
            "**Complete standing-checkpoint automation.** Rejected",
            "**Git-only controller state.** Rejected",
            "**Reuse the halted predecessor's Step 1.** Rejected",
        )
        missing = [item for item in required if item not in text]
        self.assertEqual([], missing, "ADR-028 omits rejected recovery designs")


if __name__ == "__main__":
    unittest.main()
