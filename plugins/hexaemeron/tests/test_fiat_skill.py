"""Contract checks for Fiat's host-directed workflow."""

from pathlib import Path
import importlib.util
import json
import subprocess
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIAT = ROOT / "skills" / "fiat" / "SKILL.md"
MARKETPLACE = ROOT / "skills" / "fiat" / "references" / "wildcat-marketplace.md"
CONTRIBUTOR_CHECK = ROOT / "skills" / "fiat" / "scripts" / "check_wildcat_contributor.py"
ISSUE_DISCIPLINE = ROOT / "skills" / "fiat" / "references" / "issue-discipline.md"
ISSUE_TEMPLATE = ROOT / "skills" / "fiat" / "assets" / "issue-body.md"


def load_contributor_check():
    spec = importlib.util.spec_from_file_location("check_wildcat_contributor", CONTRIBUTOR_CHECK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FiatSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fiat = FIAT.read_text(encoding="utf-8")
        cls.marketplace = MARKETPLACE.read_text(encoding="utf-8")
        cls.issue_discipline = ISSUE_DISCIPLINE.read_text(encoding="utf-8")
        cls.issue_template = ISSUE_TEMPLATE.read_text(encoding="utf-8")

    def test_marketplace_reference_is_linked(self):
        self.assertIn("[wildcat-marketplace.md](references/wildcat-marketplace.md)", self.fiat)
        self.assertTrue(MARKETPLACE.is_file())

    def test_failed_identity_check_is_silent_and_non_persistent(self):
        self.assertIn("do not record a receipt", self.marketplace)
        self.assertRegex(self.marketplace, r"say nothing about the\s+check")
        self.assertIn("do not ask a follow-up question", self.marketplace)

    def test_supported_contributor_signals_and_acknowledgement_are_explicit(self):
        self.assertIn("`@wildcat.finance`", self.marketplace)
        self.assertIn("active membership in the `wildcat-finance`", self.marketplace)
        self.assertIn("exact normalised display name or login", self.marketplace)
        self.assertIn("Acknowledge that this is a Wildcat Labs run", self.marketplace)
        self.assertIn("List every other available plugin separately", self.marketplace)

    def test_authenticated_github_does_not_require_a_connector(self):
        self.assertIn("Do not require a connector", self.marketplace)
        self.assertIn("already-authenticated local GitHub account", self.marketplace)
        self.assertIn("under-permissioned\nconnector is not itself a failed check", self.marketplace)
        self.assertIn("a GitHub connector is optional", self.fiat)
        self.assertTrue(CONTRIBUTOR_CHECK.is_file())

    def test_private_discovery_does_not_fetch_or_disclose_references(self):
        self.assertIn("discover\n   private plugin descriptors", self.marketplace)
        self.assertIn("must not fetch its image\n   references", self.marketplace)
        self.assertIn("Do not name a\n   source repository", self.marketplace)
        self.assertIn("`.wildcat-labs/private-plugin.json`", self.marketplace)
        self.assertIn("`fiat-contributor-check`", self.marketplace)
        self.assertIn("fetch its declared plugin subtree", self.marketplace)
        self.assertIn("Delete staging afterwards", self.marketplace)
        self.assertIn("Never\n   clone or copy its source repository root", self.marketplace)

    def test_installation_waits_for_completed_study(self):
        completed = self.marketplace.index("The spec is complete only after `hexctl done study ...` succeeds")
        install = self.marketplace.index("Install each relevant missing plugin now")
        refresh = self.marketplace.index("Finish every selected install before any skill or plugin refresh")
        self.assertLess(completed, install)
        self.assertLess(install, refresh)
        self.assertIn("Never install a wider-marketplace plugin before the study receipt exists", self.fiat)

    def test_success_receipts_omit_identity_data(self):
        self.assertIn("Never record the account email, name, login, or matching evidence", self.marketplace)
        self.assertIn("hexctl record labs_marketplace", self.marketplace)

    def test_ai_origin_markers_are_required_for_delivery_artifacts(self):
        self.assertIn("`origin:ai`", self.issue_discipline)
        self.assertIn("<!-- wildcat-origin: shoggoth -->", self.issue_discipline)
        self.assertIn(
            "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
            self.issue_discipline,
        )
        self.assertIn("Wildcat-Origin: shoggoth", self.issue_discipline)
        self.assertIn("<!-- wildcat-origin: shoggoth -->", self.issue_template)

    def test_provenance_is_verified_without_reclassifying_human_work(self):
        self.assertIn("Read the pull request back from GitHub", self.issue_discipline)
        self.assertIn("read the issue back from GitHub", self.issue_discipline)
        self.assertIn("pre-existing human issue, commit or pull request", self.issue_discipline)


class ContributorCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_contributor_check()

    @staticmethod
    def completed(returncode=0, payload=None):
        stdout = "" if payload is None else json.dumps(payload)
        return subprocess.CompletedProcess(["gh"], returncode, stdout=stdout, stderr="")

    def test_active_org_membership_passes(self):
        responses = [
            self.completed(),
            self.completed(payload={"login": "member", "email": None}),
            self.completed(payload={"state": "active"}),
        ]
        with mock.patch.object(self.module, "_gh", side_effect=responses):
            self.assertTrue(self.module.authenticated_github_user_is_contributor())

    def test_verified_wildcat_email_passes_when_membership_is_unavailable(self):
        responses = [
            self.completed(),
            self.completed(payload={"login": "member", "email": None}),
            self.completed(returncode=1),
            self.completed(payload=[{"email": "member@wildcat.finance", "verified": True}]),
        ]
        with mock.patch.object(self.module, "_gh", side_effect=responses):
            self.assertTrue(self.module.authenticated_github_user_is_contributor())

    def test_missing_auth_fails_without_output(self):
        with mock.patch.object(self.module, "_gh", return_value=self.completed(returncode=1)):
            with mock.patch("sys.stdout") as stdout, mock.patch("sys.stderr") as stderr:
                self.assertEqual(self.module.main(), 1)
                stdout.write.assert_not_called()
                stderr.write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
