"""Checks for the single host-neutral Promise Machine router."""

from pathlib import Path
import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
ROUTER = ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md"


def canonical_skills(plugin):
    return sorted(plugin.glob("skills/**/SKILL.md"))


class PortableSkillTests(unittest.TestCase):
    def test_plugin_manifests_name_the_public_repository(self):
        repository = "https://github.com/wildcat-finance/skills"
        marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        for name in sorted(entry["name"] for entry in marketplace["plugins"]):
            plugin = PLUGINS / name
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

    def test_promise_machine_is_the_only_portable_entrypoint(self):
        entries = sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
        self.assertEqual(entries, [ROUTER])
        text = ROUTER.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name:\s*promise-machine$")
        self.assertRegex(text, r"(?m)^description:\s*\S")
        self.assertNotRegex(text, r"(?m)^\s*version:\s*")

    def test_router_reaches_each_plugin_runtime_contract_once(self):
        text = ROUTER.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        resolved = [(ROUTER.parent / link).resolve() for link in links]
        expected = {(ROOT / "AGENTS.md").resolve()}
        expected.update((plugin / "AGENTS.md").resolve() for plugin in PLUGINS.iterdir() if plugin.is_dir())
        self.assertEqual(set(resolved), expected)
        self.assertEqual(len(resolved), len(expected))
        for target in resolved:
            self.assertTrue(target.is_file(), target)
            self.assertTrue(target.is_relative_to(ROOT), target)

    def test_plugin_runtime_contracts_resolve_every_canonical_skill(self):
        for plugin in sorted(path for path in PLUGINS.iterdir() if path.is_dir()):
            contract = (plugin / "AGENTS.md").read_text(encoding="utf-8")
            linked = {
                (plugin / relative).resolve()
                for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract)
            }
            expected = {path.resolve() for path in canonical_skills(plugin)}
            with self.subTest(plugin=plugin.name):
                self.assertEqual(linked, expected)
                for target in linked:
                    self.assertTrue(target.is_file(), target)
                    self.assertTrue(target.is_relative_to(plugin), target)

    def test_canonical_skill_names_match_parent_directories_and_are_unique(self):
        names = {}
        for skill in sorted(PLUGINS.glob("*/skills/**/SKILL.md")):
            text = skill.read_text(encoding="utf-8")
            match = re.search(r"(?m)^name:\s*([^\n]+)$", text)
            with self.subTest(skill=skill.relative_to(ROOT)):
                self.assertIsNotNone(match)
                name = match.group(1).strip()
                self.assertEqual(name, skill.parent.name)
                self.assertNotIn(name, names, f"{name} also owned by {names.get(name)}")
                names[name] = skill.relative_to(ROOT)


if __name__ == "__main__":
    unittest.main()


GENERATOR = ROOT / "scripts" / "portable_promise_machine.py"
GIT = shutil.which("git")

# Git exports these into any process it spawns, so a call meant for a
# throwaway tree can otherwise land on the outer repository's index. They are
# removed rather than overridden, so an unset one cannot fall through.
GIT_ENV_TO_DROP = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_PREFIX",
    "GIT_INTERNAL_SUPER_PREFIX",
)


def portable_module():
    spec = importlib.util.spec_from_file_location("portable_under_test", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_env():
    env = dict(os.environ)
    for name in GIT_ENV_TO_DROP:
        env.pop(name, None)
    env.update(
        GIT_AUTHOR_NAME="t",
        GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t",
        GIT_COMMITTER_EMAIL="t@t",
    )
    return env


def git(root, *args):
    return subprocess.run(  # phylax: allow subprocess: fixed argv git in a test tempdir, no shell
        ["git", "-c", "commit.gpgsign=false", "-C", str(root), *args],
        capture_output=True,
        check=True,
        env=git_env(),
    )


def tracked(root):
    """The universe a Horos scan would walk: the paths git has in its index."""
    out = git(root, "ls-files", "-z").stdout
    return {part.decode("utf-8") for part in out.split(b"\0") if part}


def write(root, relpath, content="x\n"):
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@unittest.skipIf(GIT is None, "git unavailable")
class RuntimeStagingTests(unittest.TestCase):
    """`sync` stages what it writes, so the scan that follows can see it.

    The defect these cover is an ordering one. `sync` writes the mirror and
    `horos scan` walks the git index, so running them in that order without a
    stage in between makes the scan describe the previous tree, and `horos
    check` agrees because it recomputes from the same index. Recorded as
    S4-R1-03 during skills#329 and filed as skills#854.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        git(self.root, "init", "-q")
        write(self.root, "PROMISE_MACHINE.md", "# contract\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "tracked tree")
        self.module = portable_module()
        self.target = self.module.TARGET.as_posix()

    def mirror(self, *names):
        for name in names:
            write(self.root, "%s/%s" % (self.target, name))

    def test_staging_puts_the_written_mirror_in_the_scan_universe(self):
        self.mirror("AGENTS.md", "scripts/promise_machine.py")
        self.assertEqual(self.module.stage_runtime(self.root), "staged")
        universe = tracked(self.root)
        self.assertIn("%s/AGENTS.md" % self.target, universe)
        self.assertIn("%s/scripts/promise_machine.py" % self.target, universe)

    def test_an_unstaged_mirror_is_invisible_to_the_scan_universe(self):
        # The guard above is worth nothing if it cannot fail, so this drives
        # the same comparison over a mirror that was written and not staged.
        # This is the defect itself, stated as a test.
        self.mirror("AGENTS.md")
        self.assertNotIn("%s/AGENTS.md" % self.target, tracked(self.root))

    def test_staging_leaves_an_unrelated_working_tree_edit_alone(self):
        self.mirror("AGENTS.md")
        write(self.root, "notes.txt", "not mine to stage\n")
        self.assertEqual(self.module.stage_runtime(self.root), "staged")
        self.assertIn("%s/AGENTS.md" % self.target, tracked(self.root))
        self.assertNotIn("notes.txt", tracked(self.root))

    def test_staging_records_a_mirror_file_a_later_sync_removed(self):
        self.mirror("AGENTS.md", "LICENSE")
        self.module.stage_runtime(self.root)
        git(self.root, "commit", "-qm", "mirror")
        (self.root / self.target / "LICENSE").unlink()
        self.assertEqual(self.module.stage_runtime(self.root), "staged")
        self.assertNotIn("%s/LICENSE" % self.target, tracked(self.root))

    def test_a_root_git_cannot_answer_for_skips_staging_without_failing(self):
        with tempfile.TemporaryDirectory() as raw:
            outside = Path(raw)
            write(outside, "%s/AGENTS.md" % self.target)
            status = self.module.stage_runtime(outside)
        self.assertEqual(status, "not a git work tree; mirror written but not staged")


if __name__ == "__main__":  # pragma: no cover - direct invocation
    unittest.main()
