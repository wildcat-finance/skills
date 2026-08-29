"""Both plugin manifests have to parse, agree, and point at things that exist."""

import json
import pathlib
import re
import sys
import unittest

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
from repo_contract import assert_version_agreement, assert_marketplace_source_path

CLAUDE_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
CODEX_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"

SKILL = PLUGIN_ROOT / "skills" / "probitas" / "SKILL.md"
LEDGER = PLUGIN_ROOT / "skills" / "probitas" / "EVOLUTION.md"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ledger_version():
    """The skill version the evolution ledger currently holds.

    Read rather than pinned. The inverse invariant below is that the package
    version does not track the skill version, and a literal here turns every
    legitimate generation bump into a failure of a test that was never about
    the number.
    """
    match = re.search(r"(?m)^- Current version: `probitas-v(\d+\.\d+\.\d+)`$",
                      LEDGER.read_text(encoding="utf-8"))
    assert match is not None, "the ledger states no current version"
    return match.group(1)


def skill_frontmatter():
    """Read the SKILL.md frontmatter without a YAML parser.

    Handles the two shapes this plugin uses: `key: value` at the top level,
    and a `key: >` folded block or a nested mapping whose lines are indented
    under it. Nested mappings come back as dicts, folded blocks as one string.
    """
    lines = SKILL.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError("SKILL.md does not open with frontmatter")
    block = lines[1 : lines.index("---", 1)]

    fields = {}
    key = None
    folded = False
    for line in block:
        if not line.strip():
            continue
        if line.startswith(" ") and key is not None:
            if folded:
                fields[key] = (fields[key] + " " + line.strip()).strip()
            else:
                name, _, value = line.strip().partition(":")
                fields[key][name.strip()] = value.strip().strip('"')
            continue
        name, _, value = line.partition(":")
        key = name.strip()
        value = value.strip()
        folded = value in (">", "|", ">-", "|-")
        fields[key] = "" if folded else ({} if value == "" else value.strip('"'))
    return fields


class TestManifests(unittest.TestCase):
    def test_both_manifests_parse_and_name_the_plugin(self):
        claude, codex = load(CLAUDE_MANIFEST), load(CODEX_MANIFEST)
        self.assertEqual(claude["name"], "probitas")
        self.assertEqual(codex["name"], "probitas")

    def test_package_versions_agree_without_moving_the_skill(self):
        # Three-manifest agreement + pin is the repo-wide contract.
        assert_version_agreement(self, "probitas")
        # Deliberate inverse-invariant: the package version must NOT track the
        # skill version. Keep local; do not fold into the shared contract helper.
        claude = load(CLAUDE_MANIFEST)
        self.assertEqual(skill_frontmatter()["metadata"]["version"], ledger_version())
        self.assertNotEqual(
            skill_frontmatter()["metadata"]["version"], claude["version"]
        )

    def test_codex_manifest_carries_an_interface(self):
        interface = load(CODEX_MANIFEST)["interface"]
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "defaultPrompt",
        ):
            self.assertTrue(interface.get(field), f"{field} is empty")

    def test_skills_path_exists(self):
        for manifest in (CLAUDE_MANIFEST, CODEX_MANIFEST):
            skills = load(manifest)["skills"]
            self.assertTrue(
                (manifest.parent.parent / skills).is_dir(),
                f"{manifest} points at a missing skills directory",
            )

    def test_marketplace_entries_point_at_the_plugin(self):
        assert_marketplace_source_path(self, "probitas")

    def test_skill_description_states_when_to_trigger(self):
        fields = skill_frontmatter()
        self.assertEqual(fields["name"], "probitas")
        description = fields["description"]
        self.assertIsInstance(description, str)
        self.assertIn("Use when", description)
        self.assertIn("Do not use", description)


if __name__ == "__main__":
    unittest.main()
