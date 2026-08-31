"""Keep the public marketplace prose pointed at the shipped boundaries."""

from pathlib import Path
import json
import re
import unittest

from repo_contract import (
    assert_host_descriptions_agree,
    assert_marketplace_source_path,
)


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
def discovered_plugins():
    """The universe is what ships, not what a list here remembers.

    A hand-maintained tuple lets a new plugin land with every one of these
    cases passing while none of them looked at it. Discovery makes the
    omission the failure it should be.
    """
    return tuple(
        sorted(
            path.parent.parent.name
            for path in (ROOT / "plugins").glob("*/.claude-plugin/plugin.json")
        )
    )


PLUGINS = discovered_plugins()
# The canonical skill takes the plugin's own name, with one recorded exception:
# Hexaemeron's entry point is Fiat, because the plugin ships a phase suite
# rather than a single agent.
CANONICAL_SKILL_NAMES = {"hexaemeron": "fiat"}
CANONICAL_SKILLS = {
    name: ROOT
    / "plugins"
    / name
    / "skills"
    / CANONICAL_SKILL_NAMES.get(name, name)
    / "SKILL.md"
    for name in PLUGINS
}
NEXT_JOB_LABEL = "**Next Fiat job.**"
NEXT_JOB_PREFIX = NEXT_JOB_LABEL + " Use /hexaemeron:fiat to "
NEXT_JOB_SUFFIX = (
    "Before the run finishes, cold-read and reconcile all mutable first-party "
    "marketplace prose. Change a skill's Next Fiat job only when that exact "
    "frontier job completed; otherwise leave it unchanged."
)
MATURE_NEXT_JOB = NEXT_JOB_LABEL + " None -- mature."
MARKETPLACE_CONTEXT_START = "<!-- marketplace-context:start -->"
MARKETPLACE_CONTEXT_END = "<!-- marketplace-context:end -->"
IMMUTABLE_CONTEXT_PREFIXES = (
    ("audit",),
    ("skills", "fizz"),
    ("skills", "solidity-auditor"),
    ("skills", "x-ray"),
)


def marketplace_entries():
    payload = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    return {entry["name"]: entry for entry in payload["plugins"]}


def plugin_landing_readmes():
    return {
        path.parent.name: path
        for path in (ROOT / "plugins").glob("*/README.md")
        if re.search(r"(?m)^## In one line$", path.read_text(encoding="utf-8"))
    }


def frontier_status(name):
    ledger = CANONICAL_SKILLS[name].parent / "EVOLUTION.md"
    match = re.search(
        r"(?m)^- Frontier status: `(open|mature)`$",
        ledger.read_text(encoding="utf-8"),
    )
    if match is None:
        raise AssertionError(f"skill ledger has no recognised frontier status: {ledger}")
    return match.group(1)


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


def mutable_marketplace_surface(plugin_root, path):
    """Whether a context block is first-party prose that may track now.

    Audit logs are historical evidence. The three Pashov roots are
    upstream-owned distribution copies. Their recorded marketplace context is
    allowed to describe the installation moment rather than being rewritten
    when the first-party landing page advances.
    """
    relative = path.relative_to(plugin_root)
    return not any(
        relative.parts[: len(prefix)] == prefix
        for prefix in IMMUTABLE_CONTEXT_PREFIXES
    )


# Directories that hold a checkout of this same repository rather than shipped
# content. A sweep that descends into one finds every landing README twice and
# reports the copies as strays.
#
# `.claude` was the only entry for a while, which missed the location Fiat
# actually uses: its documented worktree home is `tmp/fiat/<run>`, gitignored as
# `/tmp/`, so the suite failed for anybody with a delivery in flight in the same
# clone. Listing names is what let that happen, so nested checkouts are now
# detected rather than enumerated, and the names below are only the fast path.
NESTED_CHECKOUT_NAMES = {".git", ".hexaemeron", ".claude", "tmp"}
PORTABLE_RUNTIME = (".agents", "skills", "promise-machine", "runtime")


def _inside_nested_checkout(relative, root):
    if relative.parts and relative.parts[0] in NESTED_CHECKOUT_NAMES:
        return True
    current = root
    for part in relative.parts[:-1]:
        current = current / part
        if (current / ".git").exists():
            return True
    return False


def repository_markdown(root):
    """Every shipped Markdown file, skipping checkouts of this repository."""
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if relative.parts[: len(PORTABLE_RUNTIME)] == PORTABLE_RUNTIME:
            continue
        if not _inside_nested_checkout(relative, root):
            yield path


class MarketplaceProseTests(unittest.TestCase):
    def test_wildcat_labs_identity_contains_the_promise_machine_architecture(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith('<p align="center">\n'))
        self.assertLess(
            readme.index("./assets/characters/shoggoth.png"),
            readme.index("# The Shoggoth"),
        )
        self.assertIn("## What can it do today?", readme)
        self.assertIn("## How the collective works", readme)
        self.assertIn("[Promise Machine contract](./PROMISE_MACHINE.md)", readme)
        self.assertIn("25 members: 16 domain agents and\n9 phase agents", readme)

        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
        self.assertIn("Wildcat Labs Skills", marketplace["description"])
        self.assertIn("Promise Machine", marketplace["description"])

        for name in PLUGINS:
            runtime = ROOT / "plugins" / name / "AGENTS.md"
            with self.subTest(plugin=name):
                text = runtime.read_text(encoding="utf-8")
                self.assertIn("## Promise Machine binding", text)
                self.assertIn("promise-machine/v1", text)

    def test_marketplace_names_exactly_the_shipped_plugins(self):
        self.assertEqual(set(marketplace_entries()), set(PLUGINS))

    def test_short_descriptions_agree_across_hosts(self):
        for name in PLUGINS:
            with self.subTest(plugin=name):
                assert_host_descriptions_agree(self, name)

    def test_marketplace_entries_use_the_local_source_path(self):
        for name in PLUGINS:
            with self.subTest(plugin=name):
                assert_marketplace_source_path(self, name)

    def test_fiat_public_prose_names_the_state_container_gate(self):
        plugin = ROOT / "plugins" / "hexaemeron"
        skill = (plugin / "skills" / "fiat" / "SKILL.md").read_text(encoding="utf-8")
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        agent = (plugin / "skills" / "fiat" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn("validates the required version-1 container", skill)
        self.assertIn("checks the required\nversion-1 container spine", readme)
        self.assertIn("validating the controller state containers", agent)
        self.assertIn("validates its required state containers", codex["interface"]["longDescription"])

    def test_fiat_public_prose_binds_a_known_task_issue_during_init(self):
        plugin = ROOT / "plugins" / "hexaemeron"
        skill = (plugin / "skills" / "fiat" / "SKILL.md").read_text(encoding="utf-8")
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        push = (plugin / "skills" / "fiat" / "references" / "push-discipline.md").read_text(
            encoding="utf-8"
        )
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn("init --task-issue <url>", " ".join(skill.split()))
        self.assertIn("--task-issue", readme)
        self.assertIn("fiat/<issue>-", push)
        self.assertIn("issue number in its run branch", codex["interface"]["longDescription"])

    def test_fiat_public_prose_names_durable_record_gates(self):
        plugin = ROOT / "plugins" / "hexaemeron"
        skill = (plugin / "skills" / "fiat" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        agent = (plugin / "skills" / "fiat" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertIn("--audit-filter sapheneia:sapheneia", skill)
        self.assertIn("--audit-filter sapheneia:sapheneia", readme)
        for text in (readme, agent, codex["interface"]["longDescription"]):
            self.assertIn("Sapheneia", text)
            self.assertIn("task issue", text.lower())
            self.assertIn("comment", text.lower())

    def test_sapheneia_public_prose_names_the_bounded_durable_record_operation(self):
        plugin = ROOT / "plugins" / "sapheneia"
        skill = (plugin / "skills" / "sapheneia" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        runtime = (plugin / "AGENTS.md").read_text(encoding="utf-8")
        readme = (plugin / "README.md").read_text(encoding="utf-8")
        agent = (plugin / "skills" / "sapheneia" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        codex = json.loads(
            (plugin / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        for text in (skill, runtime, readme, agent, codex["interface"]["longDescription"]):
            self.assertIn("audit record", text)
            self.assertIn("issue", text.lower())
            self.assertIn("comment", text.lower())

    def test_root_readme_maps_every_plugin(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Meet the collective", readme)
        self.assertNotIn("## Current status", readme)
        for name in PLUGINS:
            with self.subTest(plugin=name):
                self.assertIn("[", readme)
                self.assertIn("./plugins/%s" % name, readme)

    def test_root_readme_names_the_complete_collective(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        roster = readme.split("## Meet the collective", 1)[1].split(
            "## Try it", 1
        )[0]

        governed = sorted(
            skill
            for skill in (ROOT / "plugins").glob("*/skills/**/SKILL.md")
            if (skill.parent / "EVOLUTION.md").is_file()
        )
        self.assertEqual(len(governed), 25)
        for skill in governed:
            plugin = skill.parents[2]
            target = skill.parent if plugin.name == "hexaemeron" else plugin
            relative = target.relative_to(ROOT).as_posix()
            with self.subTest(skill=skill.parent.name):
                self.assertIn(f"(./{relative})", roster)

        for worker in ("Surveyor", "Mason", "Warden", "Scribe"):
            with self.subTest(worker=worker):
                self.assertIn(f"**{worker}**", roster)

        for upstream in (
            "X-Ray",
            "Solidity Auditor",
            "Fizz",
            "Fizz Convert",
            "Fizz Sync",
        ):
            with self.subTest(upstream=upstream):
                self.assertIn(upstream, roster)

    def test_external_contributor_prose_keeps_the_human_identity(self):
        paths = (ROOT / "README.md", ROOT / "docs" / "how-to-help-shoggoth.md")
        for path in paths:
            with self.subTest(path=path):
                text = " ".join(path.read_text(encoding="utf-8").split())
                self.assertIn("not Shoggoth", text)
                self.assertIn("own Git author", text)
                self.assertIn("signing identity", text)
                self.assertIn("GitHub account", text)
                self.assertNotIn("pull/479", text)
                self.assertNotIn("PR #479", text)

    def test_root_readme_documents_how_to_publish(self):
        """Install was documented for three hosts and publishing for none.

        The two routes take different commands, and only one of them has a
        publishing step at all, so an operator who guessed wrong either ran an
        update that does nothing or waited for a sync that was never involved.
        """
        readme = s_readme = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        flat = " ".join(readme.split())
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("## Publish", root_readme)
        self.assertIn("## Publish", readme)
        # Both routes, named.
        self.assertIn("claude plugin marketplace update wildcat-labs", readme)
        self.assertIn("Organization settings > Plugins", readme)
        # The constraint that forces the second repository.
        self.assertIn("has to be private", flat)
        self.assertIn("wildcat-finance/skills-marketplace", readme)
        # Measured, not declared: the cron says five minutes and GitHub has
        # been delivering closer to twenty, so the section must not promise
        # an interval somebody would wait on.
        self.assertIn("observed rather than declared", flat)
        self.assertIn("gh workflow run sync-skills-marketplace.yml", s_readme)
        # Nothing is packaged by hand.
        self.assertIn("nothing to package or upload", flat)
        # The relative-source rule that keeps sync able to package.
        self.assertIn("stay relative paths", flat)

    def test_the_publish_section_sits_under_its_own_heading(self):
        readme = (ROOT / "INSTALL.md").read_text(encoding="utf-8")
        install = readme.index("## Install")
        publish = readme.index("## Publish")
        self.assertLess(install, publish)
        self.assertLess(readme.index("### Local agents"), publish)
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("## Install", root_readme)
        self.assertNotIn("## Publish", root_readme)

    def test_plugin_landing_readmes_publish_unique_rolling_fiat_jobs(self):
        landings = plugin_landing_readmes()
        self.assertEqual(set(landings), set(PLUGINS))
        self.assertEqual(len(landings), len(marketplace_entries()))

        topics = {}
        for name, path in landings.items():
            text = path.read_text(encoding="utf-8")
            lines = [line for line in text.splitlines() if line.startswith(NEXT_JOB_LABEL)]
            with self.subTest(plugin=name):
                self.assertEqual(text.count(NEXT_JOB_LABEL), 1, path)
                self.assertEqual(len(lines), 1, path)
                context = re.search(
                    re.escape(MARKETPLACE_CONTEXT_START)
                    + r"(.*?)"
                    + re.escape(MARKETPLACE_CONTEXT_END),
                    text,
                    flags=re.DOTALL,
                )
                self.assertIsNotNone(context, path)
                self.assertIn(lines[0], context.group(1), path)
                if frontier_status(name) == "mature":
                    self.assertEqual(lines[0], MATURE_NEXT_JOB, path)
                    self.assertNotIn("/hexaemeron:fiat", context.group(1), path)
                    continue

                self.assertTrue(lines[0].startswith(NEXT_JOB_PREFIX), path)
                self.assertTrue(lines[0].endswith(NEXT_JOB_SUFFIX), path)
                topic = lines[0][len(NEXT_JOB_PREFIX) : -len(NEXT_JOB_SUFFIX)].strip()
                self.assertTrue(topic, path)
                self.assertTrue(topic.endswith("."), path)
                topics[name] = topic

        self.assertEqual(len(set(topics.values())), len(topics))

    def test_ariadne_grounded_agent_guides_carry_marketplace_context(self):
        docs = ROOT / "plugins" / "ariadne" / "docs"
        for name in ("grounded-agent.md", "capturing-a-grounded-agent.md"):
            path = docs / name
            text = path.read_text(encoding="utf-8")
            with self.subTest(guide=name):
                self.assertEqual(text.count(MARKETPLACE_CONTEXT_START), 1, path)
                self.assertEqual(text.count(MARKETPLACE_CONTEXT_END), 1, path)
                self.assertEqual(len(marketplace_frontiers(path)), 1, path)

    def test_rolling_fiat_jobs_exist_only_in_plugin_landing_readmes(self):
        allowed = set(plugin_landing_readmes().values())
        found = set()
        for path in repository_markdown(ROOT):
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

            plugin_root = ROOT / "plugins" / name
            surfaces = [
                path
                for path in plugin_root.rglob("*.md")
                if ".claude" not in path.parts
                and mutable_marketplace_surface(plugin_root, path)
            ]
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

        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("**Current frontier.**", root_readme)

    def test_canonical_skills_state_where_they_sit_and_their_frontier(self):
        """The sibling-handoff paragraph is deliberately absent.

        Every canonical skill used to carry a `Use another tool when.` line
        naming siblings to reach for instead, and the landing READMEs carried
        the same sentence under `Try something else when.`. Both were removed:
        a reader who does not already know what Ariadne or Fizz are learns
        nothing from being sent to one by name, and the marketplace boundaries
        in `AGENTS.md` are where that routing belongs. This case asserts the
        absence so neither label returns a paragraph at a time.
        """
        self.assertEqual(set(CANONICAL_SKILLS), set(PLUGINS))
        for name, skill in CANONICAL_SKILLS.items():
            text = skill.read_text(encoding="utf-8")
            with self.subTest(plugin=name):
                self.assertIn("## Where this sits", text)
                self.assertIn("**Current frontier.**", text)
                self.assertNotIn("**Use another tool when.**", text)
                self.assertNotIn("**Try something else when.**", text)

    def test_no_shipped_document_carries_a_sibling_handoff_label(self):
        strays = []
        for path in repository_markdown(ROOT):
            relative = path.relative_to(ROOT)
            text = path.read_text(encoding="utf-8")
            for label in ("**Use another tool when.**", "**Try something else when.**"):
                if label in text:
                    strays.append(f"{relative}: {label}")
        self.assertEqual(strays, [])

    def test_canonical_skill_directories_have_no_browsing_readme_mirrors(self):
        skills = sorted((ROOT / "plugins").glob("*/skills/**/SKILL.md"))
        self.assertTrue(skills)
        for skill in skills:
            with self.subTest(skill=skill.relative_to(ROOT)):
                self.assertFalse(
                    (skill.parent / "README.md").exists(),
                    "canonical skills must not carry shadow README.md mirrors",
                )

    # test_pandects_prose_counts_the_laws_the_catalogue_holds moved to
    # plugins/pandects/tests/test_prose_counts.py and
    # test_lazarus_release_readme_remains_digest_bound moved to
    # plugins/lazarus/tests/test_example_readme_digest.py by the test-scoping
    # de-duplication: a plugin-specific check runs in that plugin's suite, not on
    # every unrelated gated change.


if __name__ == "__main__":
    unittest.main()
