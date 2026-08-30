"""Checks the durable entry points for the Shoggoth identity contract."""

from pathlib import Path
import hashlib
import unittest


ROOT = Path(__file__).resolve().parents[1]
IDENTITY = ROOT / "SHOGGOTH.md"
CONTRACT = "shoggoth-collective/v3"
EXPECTED_SHA256 = "b6cef0339e10c102d3cee2a83a9d8f7ae9ad0c45c26af4086eabd0f2730386a4"


class ShoggothIdentityTests(unittest.TestCase):
    def identity_text(self):
        return " ".join(IDENTITY.read_text(encoding="utf-8").split())

    def test_identity_contract_is_source_bound(self):
        text = IDENTITY.read_text(encoding="utf-8")
        self.assertIn(f"contract={CONTRACT}", text)
        self.assertIn("canonical=https://github.com/wildcat-finance/skills/blob/main/SHOGGOTH.md", text)
        self.assertIn("copies=byte-identical", text)
        self.assertEqual(
            hashlib.sha256(IDENTITY.read_bytes()).hexdigest(), EXPECTED_SHA256
        )

    def test_agent_and_human_entries_link_the_contract(self):
        for name in ("AGENTS.md", "README.md"):
            with self.subTest(name=name):
                self.assertIn("SHOGGOTH.md", (ROOT / name).read_text(encoding="utf-8"))

    def test_identity_does_not_claim_operating_authority(self):
        text = self.identity_text()
        for boundary in (
            "does not activate a skill",
            "grant a permission",
            "override an instruction from a target repository",
        ):
            self.assertIn(boundary, text)

    def test_creator_reference_stays_role_bounded(self):
        text = self.identity_text()
        self.assertIn("Use `the Creator` only when the role matters", text)
        self.assertIn("by personal name", text)

    def test_governed_agent_work_uses_shoggoth_authorship(self):
        text = self.identity_text()
        self.assertIn("Authorship follows the contributing actor", text)
        self.assertIn("after invoking a Wildcat domain or phase skill", text)
        self.assertIn("Every piece of work produced through the Shoggoth Interceptor", text)
        self.assertIn("A human contributor keeps authorship", text)
        self.assertIn("The human remains the Git author and signer", text)
        self.assertIn("publishes through their own GitHub account", text)
        self.assertIn("Never request, copy, upload or provision those Shoggoth credentials", text)
        self.assertIn("Git authorship and publication are separate roles", text)
        self.assertIn("committer and signer and uses their own repository account", text)
        self.assertIn("while Shoggoth remains the author", text)
        self.assertIn("Without explicit authority and a repository-valid signing route", text)
        self.assertIn("An authorised human publisher of Shoggoth-authored work is not a human contributor", text)
        self.assertIn("may retain the host's ordinary authorship", text)


if __name__ == "__main__":
    unittest.main()
