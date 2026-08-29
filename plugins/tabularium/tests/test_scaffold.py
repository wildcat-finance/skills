"""Discovery, packaging and public-document checks for Tabularium."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
from repo_contract import (
    assert_version_agreement,
    assert_host_descriptions_agree,
    assert_marketplace_source_path,
)

COMMAND = PLUGIN_ROOT / "scripts" / "tabularium.py"
SKILL = PLUGIN_ROOT / "skills" / "tabularium" / "SKILL.md"


def run(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TabulariumPackagingTests(unittest.TestCase):
    def test_help_names_both_commands(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("build", result.stdout)
        self.assertIn("verify", result.stdout)
        self.assertIn("compound-witness", result.stdout)
        self.assertIn("verify-compound-witness", result.stdout)
        self.assertIn("deterministic", result.stdout)

    def test_verify_help_requires_a_coverage_manifest(self):
        result = run("verify", "--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("coverage manifest", result.stdout)
        self.assertIn("offline", result.stdout)

    def test_skill_is_canonical_and_has_no_browsable_readme_shadow(self):
        self.assertTrue(SKILL.is_file())
        self.assertFalse((SKILL.parent / "README.md").exists())

    def test_package_metadata_agrees_and_points_at_the_skill(self):
        assert_version_agreement(self, "tabularium")
        assert_host_descriptions_agree(self, "tabularium")
        manifests = [
            json.loads((PLUGIN_ROOT / host / "plugin.json").read_text(encoding="utf-8"))
            for host in (".claude-plugin", ".codex-plugin")
        ]
        self.assertEqual([item["name"] for item in manifests], ["tabularium"] * 2)
        self.assertEqual([item["skills"] for item in manifests], ["./skills/"] * 2)
        self.assertTrue(SKILL.is_file())

    def test_public_documents_and_audit_log_are_present(self):
        for relative in (
            "README.md",
            "docs/adding-an-adapter.md",
            "docs/compound-v3-preservation.md",
            "docs/release-policy.md",
            "audit/AUDIT.md",
            "examples/goldfinch-v0/README.md",
            "examples/goldfinch-v0/DATA-DICTIONARY.md",
        ):
            self.assertTrue((PLUGIN_ROOT / relative).is_file(), relative)

    def test_public_document_links_resolve_inside_the_plugin(self):
        shared_versioning = (
            REPO_ROOT / "plugins" / "hexaemeron" / "skills" / "VERSIONING.md"
        ).resolve()
        for path in PLUGIN_ROOT.rglob("*.md"):
            if "__pycache__" in path.parts:
                continue
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if link.startswith(("#", "https://", "http://", "mailto:")):
                    continue
                target = (path.parent / link.split("#", 1)[0]).resolve()
                with self.subTest(document=path.relative_to(PLUGIN_ROOT), link=link):
                    if target == shared_versioning:
                        self.assertTrue(target.is_file())
                        continue
                    self.assertIn(PLUGIN_ROOT, target.parents)
                    self.assertTrue(target.exists())

    def test_marketplace_entries_use_the_local_plugin_path(self):
        assert_marketplace_source_path(self, "tabularium")

    def test_compound_spec_fails_closed_and_keeps_collection_offline(self):
        spec = " ".join(
            (PLUGIN_ROOT / "docs" / "compound-v3-preservation.md")
            .read_text()
            .split()
        )
        for phrase in (
            "Do not build from logs alone",
            "successful call frames whose destination is the Comet proxy",
            "Coverage fails closed",
            "It makes no RPC request",
            "not an independent confirmation source",
            "28 production market",
        ):
            self.assertIn(phrase, spec)


if __name__ == "__main__":
    unittest.main()
