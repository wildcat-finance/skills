"""Keep the public marketplace prose pointed at the shipped boundaries."""

from pathlib import Path
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS = (
    "alexandria",
    "ariadne",
    "hermes",
    "hexaemeron",
    "lemma",
    "lazarus",
    "pandects",
    "probitas",
    "tabularium",
)
CANONICAL_SKILLS = {
    "alexandria": ROOT / "plugins" / "alexandria" / "skills" / "alexandria" / "SKILL.md",
    "ariadne": ROOT / "plugins" / "ariadne" / "skills" / "ariadne" / "SKILL.md",
    "hermes": ROOT / "plugins" / "hermes" / "skills" / "hermes" / "SKILL.md",
    "hexaemeron": ROOT / "plugins" / "hexaemeron" / "skills" / "fiat" / "SKILL.md",
    "lemma": ROOT / "plugins" / "lemma" / "skills" / "chunk" / "SKILL.md",
    "lazarus": ROOT / "plugins" / "lazarus" / "skills" / "lazarus" / "SKILL.md",
    "pandects": ROOT / "plugins" / "pandects" / "skills" / "pandects" / "SKILL.md",
    "probitas": ROOT / "plugins" / "probitas" / "skills" / "probitas" / "SKILL.md",
    "tabularium": ROOT / "plugins" / "tabularium" / "skills" / "tabularium" / "SKILL.md",
}
NEXT_JOB_PREFIX = "**Next Fiat job.** Use /hexaemeron:fiat to "
NEXT_JOB_SUFFIX = (
    "Before the run finishes, cold-read and reconcile all mutable first-party "
    "marketplace prose. Change a skill's Next Fiat job only when that exact "
    "frontier job completed; otherwise leave it unchanged."
)
MARKETPLACE_CONTEXT_START = "<!-- marketplace-context:start -->"
MARKETPLACE_CONTEXT_END = "<!-- marketplace-context:end -->"


def marketplace_entries():
    payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return {entry["name"]: entry for entry in payload["plugins"]}


def plugin_landing_readmes():
    return {
        path.parent.name: path
        for path in (ROOT / "plugins").glob("*/README.md")
        if re.search(r"(?m)^## In one line$", path.read_text(encoding="utf-8"))
    }


def marketplace_frontiers(path):
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(
        re.escape(MARKETPLACE_CONTEXT_START)
        + r"(.*?)"
        + re.escape(MARKETPLACE_CONTEXT_END),
        text,
        flags=re.DOTALL,
    )
    frontiers = []
    for block in blocks:
        match = re.search(r"\*\*Current frontier(?:\.|:)\*\*\s*([^\n]+)", block)
        if match is None:
            raise AssertionError(f"marketplace context has no current frontier: {path}")
        frontiers.append(match.group(1).strip())
    return frontiers


def root_readme_frontier(name):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        rf"(?m)^\| \[[^\]]+\]\(\./plugins/{re.escape(name)}\) "
        r"\| [^|\n]* \| [^|\n]* \| (?P<frontier>[^|\n]+) \|$",
        readme,
    )
    if match is None:
        raise AssertionError(f"root selection table has no row for {name}")
    return match.group("frontier").strip()


class MarketplaceProseTests(unittest.TestCase):
    def test_marketplace_names_exactly_the_shipped_plugins(self):
        self.assertEqual(set(marketplace_entries()), set(PLUGINS))

    def test_short_descriptions_agree_across_hosts(self):
        entries = marketplace_entries()
        for name in PLUGINS:
            expected = entries[name]["description"]
            plugin = ROOT / "plugins" / name
            for host in (".claude-plugin", ".codex-plugin"):
                manifest = json.loads(
                    (plugin / host / "plugin.json").read_text(encoding="utf-8")
                )
                with self.subTest(plugin=name, host=host):
                    self.assertEqual(manifest["description"], expected)
            codex = json.loads(
                (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(codex["interface"]["shortDescription"], expected)

            agent = plugin / "skills" / name / "agents" / "openai.yaml"
            if agent.is_file():
                match = re.search(
                    r'(?m)^  short_description: ["\']?([^"\'\n]+)',
                    agent.read_text(encoding="utf-8"),
                )
                self.assertIsNotNone(match, agent)
                self.assertEqual(match.group(1), expected)

    def test_root_readme_maps_every_plugin(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Choose the job, then the plugin", readme)
        for name in PLUGINS:
            with self.subTest(plugin=name):
                self.assertIn("[", readme)
                self.assertIn("./plugins/%s" % name, readme)

    def test_plugin_landing_readmes_publish_unique_rolling_fiat_jobs(self):
        landings = plugin_landing_readmes()
        self.assertEqual(set(landings), set(PLUGINS))
        self.assertEqual(len(landings), 9)

        topics = {}
        for name, path in landings.items():
            text = path.read_text(encoding="utf-8")
            lines = [line for line in text.splitlines() if line.startswith(NEXT_JOB_PREFIX)]
            with self.subTest(plugin=name):
                self.assertEqual(text.count(NEXT_JOB_PREFIX), 1, path)
                self.assertEqual(len(lines), 1, path)
                self.assertTrue(lines[0].startswith(NEXT_JOB_PREFIX), path)
                self.assertTrue(lines[0].endswith(NEXT_JOB_SUFFIX), path)
                context = re.search(
                    re.escape(MARKETPLACE_CONTEXT_START)
                    + r"(.*?)"
                    + re.escape(MARKETPLACE_CONTEXT_END),
                    text,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(context, path)
                self.assertIn(lines[0], context.group(1), path)
                topic = lines[0][len(NEXT_JOB_PREFIX) : -len(NEXT_JOB_SUFFIX)].strip()
                self.assertTrue(topic, path)
                self.assertTrue(topic.endswith("."), path)
                topics[name] = topic

        self.assertEqual(len(set(topics.values())), len(PLUGINS))

    def test_rolling_fiat_jobs_exist_only_in_plugin_landing_readmes(self):
        allowed = set(plugin_landing_readmes().values())
        found = set()
        for path in ROOT.rglob("*.md"):
            relative = path.relative_to(ROOT)
            if relative.parts[0] in {".git", ".hexaemeron"}:
                continue
            if "**Next Fiat job.**" in path.read_text(encoding="utf-8"):
                found.add(path)
        self.assertEqual(found, allowed)

    def test_current_frontiers_agree_with_each_plugin_landing_readme(self):
        landings = plugin_landing_readmes()
        self.assertEqual(set(landings), set(PLUGINS))
        for name in PLUGINS:
            landing_frontiers = marketplace_frontiers(landings[name])
            with self.subTest(plugin=name, surface="landing"):
                self.assertEqual(len(landing_frontiers), 1)
            expected = landing_frontiers[0]

            surfaces = list((ROOT / "plugins" / name).rglob("*.md"))
            portable = ROOT / ".agents" / "skills" / name / "SKILL.md"
            if portable.is_file():
                surfaces.append(portable)
            for path in surfaces:
                text = path.read_text(encoding="utf-8")
                if MARKETPLACE_CONTEXT_START not in text:
                    continue
                with self.subTest(plugin=name, surface=path.relative_to(ROOT)):
                    frontiers = marketplace_frontiers(path)
                    self.assertTrue(frontiers, path)
                    self.assertEqual(frontiers, [expected] * len(frontiers))

            with self.subTest(plugin=name, surface="root selection table"):
                self.assertEqual(root_readme_frontier(name), expected)

    def test_canonical_skills_state_handoff_and_frontier(self):
        self.assertEqual(set(CANONICAL_SKILLS), set(PLUGINS))
        for name, skill in CANONICAL_SKILLS.items():
            text = skill.read_text(encoding="utf-8")
            with self.subTest(plugin=name):
                self.assertIn("## Where this sits", text)
                self.assertIn("**Use another tool when.**", text)
                self.assertIn("**Current frontier.**", text)

    def test_canonical_skill_directories_have_no_browsing_readme_mirrors(self):
        skills = sorted((ROOT / "plugins").glob("*/skills/**/SKILL.md"))
        self.assertTrue(skills)
        for skill in skills:
            with self.subTest(skill=skill.relative_to(ROOT)):
                self.assertFalse(
                    (skill.parent / "README.md").exists(),
                    "canonical skills must not carry shadow README.md mirrors",
                )

    def test_lazarus_release_readme_remains_digest_bound(self):
        manifest = json.loads(
            (ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "manifest.json").read_text(encoding="utf-8")
        )
        files = {entry["path"]: entry["sha256"] for entry in manifest["components"]}
        readme = ROOT / "plugins" / "lazarus" / "examples" / "goldfinch-v0" / "README.md"
        import hashlib

        self.assertEqual(hashlib.sha256(readme.read_bytes()).hexdigest(), files["README.md"])


if __name__ == "__main__":
    unittest.main()
