"""Checks for the host-neutral Agent Skills entrypoints."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class PortableSkillTests(unittest.TestCase):
    def test_plugin_manifests_name_the_public_repository(self):
        repository = "https://github.com/wildcat-finance/skills"
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        for name in sorted(entry["name"] for entry in marketplace["plugins"]):
            plugin = ROOT / "plugins" / name
            for host in (".claude-plugin", ".codex-plugin"):
                manifest = json.loads(
                    (plugin / host / "plugin.json").read_text(encoding="utf-8")
                )
                with self.subTest(plugin=plugin.name, host=host):
                    self.assertEqual(manifest["repository"], repository)
                    self.assertEqual(
                        manifest["homepage"],
                        "%s/tree/main/plugins/%s" % (repository, plugin.name),
                    )

    def test_portable_entrypoints_exist_and_match_parent_name(self):
        for name in (
            "alexandria", "ariadne", "hermes", "hexaemeron", "lazarus", "lemma", "pandects", "probitas", "tabularium"
        ):
            path = ROOT / ".agents" / "skills" / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            match = re.search(r"^name:\s*([^\n]+)$", text, re.MULTILINE)
            self.assertIsNotNone(match)
            self.assertEqual(match.group(1).strip(), name)
            self.assertRegex(text, r"(?m)^description:\s*\S")

    def test_portable_entrypoint_links_resolve(self):
        for path in (ROOT / ".agents" / "skills").glob("*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
            self.assertTrue(links, path)
            for link in links:
                self.assertTrue((path.parent / link).resolve().is_file(), link)

    def test_plugin_runtime_contracts_point_to_canonical_skills(self):
        hermes = ROOT / "plugins" / "hermes" / "skills" / "hermes" / "SKILL.md"
        self.assertTrue(hermes.is_file())

        ariadne = ROOT / "plugins" / "ariadne"
        contract = (ariadne / "AGENTS.md").read_text(encoding="utf-8")
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract):
            self.assertTrue((ariadne / relative).is_file(), relative)

        lemma = ROOT / "plugins" / "lemma"
        contract = (lemma / "AGENTS.md").read_text(encoding="utf-8")
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract):
            self.assertTrue((lemma / relative).is_file(), relative)

        lazarus = ROOT / "plugins" / "lazarus"
        contract = (lazarus / "AGENTS.md").read_text(encoding="utf-8")
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract):
            self.assertTrue((lazarus / relative).is_file(), relative)

        probitas = ROOT / "plugins" / "probitas"
        contract = (probitas / "AGENTS.md").read_text(encoding="utf-8")
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract):
            self.assertTrue((probitas / relative).is_file(), relative)

        tabularium = ROOT / "plugins" / "tabularium"
        contract = (tabularium / "AGENTS.md").read_text(encoding="utf-8")
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract):
            self.assertTrue((tabularium / relative).is_file(), relative)

        hexa_root = ROOT / "plugins" / "hexaemeron"
        contract = (hexa_root / "AGENTS.md").read_text(encoding="utf-8")
        paths = re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract)
        self.assertEqual(len(paths), 9)
        for relative in paths:
            self.assertTrue((hexa_root / relative).is_file(), relative)

    def test_skill_names_match_canonical_parent_directories(self):
        skills = list((ROOT / "plugins" / "alexandria" / "skills").glob("*/SKILL.md"))
        skills += list((ROOT / "plugins" / "ariadne" / "skills").glob("*/SKILL.md"))
        skills += list((ROOT / "plugins" / "hermes" / "skills").glob("*/SKILL.md"))
        skills += list((ROOT / "plugins" / "hexaemeron" / "skills").glob("*/SKILL.md"))
        skills += list(
            (ROOT / "plugins" / "hexaemeron" / "skills" / "fizz" / "skills").glob("*/SKILL.md")
        )
        skills += list((ROOT / "plugins" / "lemma" / "skills").glob("*/SKILL.md"))
        skills += list((ROOT / "plugins" / "lazarus" / "skills").glob("*/SKILL.md"))
        skills += list((ROOT / "plugins" / "pandects" / "skills").glob("*/SKILL.md"))
        skills += list((ROOT / "plugins" / "probitas" / "skills").glob("*/SKILL.md"))
        skills += list(
            (ROOT / "plugins" / "tabularium" / "skills").glob("*/SKILL.md")
        )
        for path in skills:
            text = path.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*([^\n]+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, path)
            self.assertEqual(match.group(1).strip(), path.parent.name, path)


if __name__ == "__main__":
    unittest.main()
