"""Exact evidence contract for retiring the hosted identity status."""

from copy import deepcopy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/ruleset-identity-retirement"
REQUIRED_FIELDS = {
    "_links",
    "bypass_actors",
    "conditions",
    "created_at",
    "current_user_can_bypass",
    "enforcement",
    "id",
    "name",
    "node_id",
    "rules",
    "source",
    "source_type",
    "target",
    "updated_at",
}


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def assert_identity_only_delta(before: dict, after: dict) -> None:
    """Refuse anything except one exact required-context removal."""
    for label, document in (("preimage", before), ("postimage", after)):
        if set(document) != REQUIRED_FIELDS:
            raise AssertionError(f"{label} is partial or carries unknown fields")
    if before["source"] != "wildcat-finance/skills" or before["id"] != 21830871:
        raise AssertionError("wrong repository or ruleset")
    if before["bypass_actors"] != []:
        raise AssertionError("preimage bypass actors are not the explicit empty set")

    expected = deepcopy(before)
    removed = []
    for rule in expected["rules"]:
        if rule.get("type") != "required_status_checks":
            continue
        checks = rule["parameters"]["required_status_checks"]
        kept = []
        for check in checks:
            if check.get("context") == "identity":
                removed.append(check)
            else:
                kept.append(check)
        rule["parameters"]["required_status_checks"] = kept
    if removed != [{"context": "identity", "integration_id": 15368}]:
        raise AssertionError("preimage identity context changed")
    expected["updated_at"] = after["updated_at"]
    if expected != after:
        raise AssertionError("postimage changed outside the identity context")


class RulesetComparatorTests(unittest.TestCase):
    def setUp(self):
        self.before = load("preimage.json")
        self.after = load("postimage.json")

    def test_exact_live_pre_and_post_images_pass(self):
        assert_identity_only_delta(self.before, self.after)

    def test_wrong_repository_refuses(self):
        self.before["source"] = "wildcat-finance/not-skills"
        with self.assertRaisesRegex(AssertionError, "wrong repository"):
            assert_identity_only_delta(self.before, self.after)

    def test_changed_preimage_refuses(self):
        self.before["rules"][0]["parameters"]["required_status_checks"][0][
            "integration_id"
        ] = 1
        with self.assertRaisesRegex(AssertionError, "identity context changed"):
            assert_identity_only_delta(self.before, self.after)

    def test_partial_response_refuses(self):
        self.after.pop("conditions")
        with self.assertRaisesRegex(AssertionError, "partial"):
            assert_identity_only_delta(self.before, self.after)

    def test_unrelated_field_drift_refuses(self):
        self.after["enforcement"] = "active"
        with self.assertRaisesRegex(AssertionError, "outside the identity"):
            assert_identity_only_delta(self.before, self.after)


class RetiredSurfaceTests(unittest.TestCase):
    def test_hosted_identity_workflow_and_checker_are_absent(self):
        self.assertFalse((ROOT / ".github/workflows/identity.yml").exists())
        self.assertFalse((ROOT / "scripts/check_commit_identity.py").exists())

    def test_claude_attribution_override_is_absent(self):
        self.assertFalse((ROOT / ".claude/settings.json").exists())

    def test_contributor_ranking_has_no_hosted_status_compatibility_aliases(self):
        source = (ROOT / "scripts/contributors.py").read_text(encoding="utf-8")
        for name in (
            "HOST_IDENTITY_NAMES",
            "HOST_IDENTITY_EMAILS",
            "HOST_PR_LOGINS",
            "is_host_identity",
            "is_host_login",
        ):
            self.assertNotIn(name, source)

    def test_python_workflow_inventory_does_not_name_identity(self):
        source = (ROOT / "tests/test_python_contract.py").read_text(encoding="utf-8")
        self.assertNotIn('"identity.yml"', source)


if __name__ == "__main__":
    unittest.main()
