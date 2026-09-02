"""A version stated in more than one place must agree in every one of them.

The repository states the same version at several layers: a plugin declares one
in its Claude manifest, again in its Codex manifest, and again in the root
marketplace listing, and a governed skill declares one in its ledger and again
in its own frontmatter. Nothing walked the layers, so a bump could land in one
and be missed in the rest. Ariadne shipped that way: `1.2.0` in two manifests
and `1.1.0` in the third.

What this deliberately does not enforce:

A plugin's version is not its skills' version. Horos is plugin `0.1.0` carrying
`horos-v9.2.3`, and the versioning contract governs a skill rather than a
plugin, so requiring the two to track each other would be inventing a rule the
contract denies.

A pinned historical reference is not drift. `EVOLUTION.md` history rows, audit
entries and `docs/` specs name the version that was current when they were
written, which is the point of them. So does a frozen eval corpus: the
imprimatur `labelled-prose-v1` directory names `imprimatur-v1.1.0` because that
is the version its labels were produced against, and repointing it at the
current version would make it claim an agreement nobody measured. Test fixtures
naming an invented version are likewise sound. A check that flagged those would
report eleven faults in a tree that has one.
"""

from pathlib import Path
import json
import re
import unittest

from repo_contract import assert_version_agreement

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

UNGOVERNED = {"fizz", "fizz-convert", "fizz-sync", "x-ray", "solidity-auditor"}
DELIVERY_PACKAGE_VERSIONS = {
    "alexandria": "0.4.0",
    "anamnesis": "0.3.0",
    "ariadne": "1.3.0",
    "berean": "0.1.2",
    "brevitas": "0.2.2",
    "dokimasia": "2.1.0",
    "hermes": "0.1.1",
    "hexaemeron": "1.6.22",
    "homologia": "1.1.0",
    "horos": "0.1.1",
    "janus": "0.1.1",
    "lazarus": "1.1.2",
    "lemma": "0.1.2",
    "pandects": "0.1.1",
    "probitas": "0.2.0",
    "sapheneia": "0.1.2",
    "synkrisis": "0.5.1",
    "tabularium": "0.3.1",
}


def marketplace_versions():
    listing = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return {entry["name"]: entry.get("version") for entry in listing["plugins"]}


def manifest_version(path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8")).get("version")


def plugin_dirs():
    for directory in sorted(PLUGINS.glob("*")):
        if directory.is_dir() and (directory / ".claude-plugin" / "plugin.json").is_file():
            yield directory.name, directory


class PluginVersionPropagationTests(unittest.TestCase):
    def setUp(self):
        self.marketplace = marketplace_versions()

    def test_every_plugin_states_a_version_in_each_manifest_that_has_one(self):
        for name, directory in plugin_dirs():
            with self.subTest(plugin=name):
                self.assertIsNotNone(
                    manifest_version(directory / ".claude-plugin" / "plugin.json"),
                    f"{name} Claude manifest states no version",
                )
                self.assertIsNotNone(
                    self.marketplace.get(name),
                    f"{name} is not listed with a version in the marketplace",
                )
                codex = directory / ".codex-plugin" / "plugin.json"
                self.assertTrue(codex.is_file(), f"{name} has no Codex manifest")
                self.assertIsNotNone(
                    manifest_version(codex),
                    f"{name} Codex manifest states no version",
                )

    def test_the_three_manifests_agree(self):
        for name, directory in plugin_dirs():
            with self.subTest(plugin=name):
                assert_version_agreement(self, name)

    def test_promise_machine_delivery_versions_are_exact_and_current(self):
        self.assertEqual(set(self.marketplace), set(DELIVERY_PACKAGE_VERSIONS))
        for name, directory in plugin_dirs():
            expected = DELIVERY_PACKAGE_VERSIONS[name]
            actual = {
                "marketplace": self.marketplace[name],
                "claude": manifest_version(directory / ".claude-plugin" / "plugin.json"),
                "codex": manifest_version(directory / ".codex-plugin" / "plugin.json"),
            }
            with self.subTest(plugin=name):
                self.assertEqual(actual, {key: expected for key in actual})

    def test_hexaemeron_version_reaches_both_marketplaces(self):
        expected = DELIVERY_PACKAGE_VERSIONS["hexaemeron"]
        agents = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        agents_entry = next(
            entry for entry in agents["plugins"] if entry["name"] == "hexaemeron"
        )
        directory = PLUGINS / "hexaemeron"
        self.assertEqual(
            {
                "agents_marketplace": agents_entry["version"],
                "claude_marketplace": self.marketplace["hexaemeron"],
                "claude_manifest": manifest_version(
                    directory / ".claude-plugin" / "plugin.json"
                ),
                "codex_manifest": manifest_version(
                    directory / ".codex-plugin" / "plugin.json"
                ),
            },
            {
                "agents_marketplace": expected,
                "claude_marketplace": expected,
                "claude_manifest": expected,
                "codex_manifest": expected,
            },
        )

    def test_ariadne_version_reaches_both_marketplaces(self):
        expected = DELIVERY_PACKAGE_VERSIONS["ariadne"]
        agents = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        agents_entry = next(
            entry for entry in agents["plugins"] if entry["name"] == "ariadne"
        )
        directory = PLUGINS / "ariadne"
        self.assertEqual(
            {
                "agents_marketplace": agents_entry["version"],
                "claude_marketplace": self.marketplace["ariadne"],
                "claude_manifest": manifest_version(
                    directory / ".claude-plugin" / "plugin.json"
                ),
                "codex_manifest": manifest_version(
                    directory / ".codex-plugin" / "plugin.json"
                ),
            },
            {
                "agents_marketplace": expected,
                "claude_marketplace": expected,
                "claude_manifest": expected,
                "codex_manifest": expected,
            },
        )

    def test_sapheneia_version_reaches_both_marketplaces(self):
        expected = DELIVERY_PACKAGE_VERSIONS["sapheneia"]
        agents = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        agents_entry = next(
            entry for entry in agents["plugins"] if entry["name"] == "sapheneia"
        )
        directory = PLUGINS / "sapheneia"
        self.assertEqual(
            {
                "agents_marketplace": agents_entry["version"],
                "claude_marketplace": self.marketplace["sapheneia"],
                "claude_manifest": manifest_version(
                    directory / ".claude-plugin" / "plugin.json"
                ),
                "codex_manifest": manifest_version(
                    directory / ".codex-plugin" / "plugin.json"
                ),
            },
            {
                "agents_marketplace": expected,
                "claude_marketplace": expected,
                "claude_manifest": expected,
                "codex_manifest": expected,
            },
        )

    def test_a_codex_manifest_exists_wherever_codex_metadata_ships(self):
        """A plugin shipping a .codex-plugin directory must put a manifest in it.

        An empty directory would pass the agreement check by having nothing to
        disagree with.
        """
        for name, directory in plugin_dirs():
            codex_dir = directory / ".codex-plugin"
            if codex_dir.is_dir():
                with self.subTest(plugin=name):
                    self.assertTrue(
                        (codex_dir / "plugin.json").is_file(),
                        f"{name} ships .codex-plugin/ with no plugin.json in it",
                    )


class SkillVersionPropagationTests(unittest.TestCase):
    """The skill layer, from the ledger down into the frontmatter.

    `tests/test_evolution_contract.py` owns the equality itself. What is checked
    here is that the pair is reachable at all: a skill whose ledger cannot be
    parsed for a current version has no version to propagate, and the equality
    test would pass over it by finding nothing to compare.
    """

    def test_every_governed_skill_declares_a_parseable_current_version(self):
        found = 0
        for skill_md in sorted(PLUGINS.glob("*/skills/**/SKILL.md")):
            directory = skill_md.parent
            if directory.name in UNGOVERNED:
                continue
            ledger = directory / "EVOLUTION.md"
            with self.subTest(skill=directory.name):
                self.assertTrue(ledger.is_file(), f"{directory} has no ledger")
                match = re.search(
                    r"(?m)^- Current version: `([a-z-]+)-v(\d+\.\d+\.\d+)`$",
                    ledger.read_text(encoding="utf-8"),
                )
                self.assertIsNotNone(
                    match,
                    f"{directory.name} ledger states no parseable current version",
                )
                self.assertEqual(
                    match.group(1), directory.name,
                    f"{directory.name} ledger labels itself {match.group(1)}",
                )
                found += 1
        self.assertGreater(found, 0, "no governed skills found; the glob is wrong")


if __name__ == "__main__":
    unittest.main()
