"""Changed installable files must move the package version."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "plugin_release.py"
MARKETPLACES = (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json")


class ReleaseWorkflowTests(unittest.TestCase):
    def test_required_invariants_gate_checks_plugin_release(self):
        workflow = (ROOT / ".github/workflows/repo.yml").read_text()
        self.assertIn("python3 scripts/plugin_release.py", workflow)
        self.assertIn('github.event.pull_request.base.sha', workflow)
        self.assertIn('github.event.before', workflow)
        self.assertIn('--base "$BASE_SHA" --head "$GITHUB_SHA"', workflow)
        self.assertNotIn('continue-on-error', workflow)


class PluginReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.git("init", "-q")
        self.plugin("alpha", "1.2.9")
        self.plugin("beta", "0.1.0")
        self.base = self.commit()

    def git(self, *args):
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
             "-c", "user.name=Release test", "-c", "user.email=release@example.invalid",
             *args], cwd=self.root, capture_output=True, text=True, timeout=15,
            check=True,
        )
        return result.stdout.strip()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def plugin(self, name, version):
        for host in (".claude-plugin", ".codex-plugin"):
            self.write(f"plugins/{name}/{host}/plugin.json", json.dumps(
                {"name": name, "version": version}))
        for relative in MARKETPLACES:
            path = self.root / relative
            listing = json.loads(path.read_text()) if path.exists() else {"plugins": []}
            listing["plugins"] = [p for p in listing["plugins"] if p["name"] != name]
            listing["plugins"].append({"name": name, "version": version})
            self.write(relative, json.dumps(listing))
        self.write(f"plugins/{name}/skills/example/SKILL.md", "original\n")

    def commit(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture")
        return self.git("rev-parse", "HEAD")

    def check(self, expected=0, *, base=None, head="HEAD"):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repository", str(self.root),
             "--base", base or self.base, "--head", head],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def test_changed_skill_cannot_keep_its_version(self):
        self.write("plugins/alpha/skills/example/SKILL.md", "changed\n")
        self.commit()
        self.assertIn("alpha: changed package requires a version above 1.2.9", self.check(1))

    def test_any_shipped_file_change_requires_a_bump(self):
        for relative in ("README.md", "tests/test_example.py", ".hidden", "assets/picture.bin"):
            with self.subTest(path=relative):
                self.git("reset", "--hard", self.base)
                self.write(f"plugins/alpha/{relative}", "changed\n")
                self.commit()
                self.check(1)

    def test_deletion_rename_and_mode_changes_require_a_bump(self):
        relative = "plugins/alpha/skills/example/SKILL.md"
        for operation in ("delete", "rename", "mode"):
            with self.subTest(operation=operation):
                self.git("reset", "--hard", self.base)
                if operation == "delete":
                    self.git("rm", relative)
                elif operation == "rename":
                    self.git("mv", relative, relative + ".old")
                else:
                    (self.root / relative).chmod(0o755)
                self.commit()
                self.check(1)

    def test_numeric_patch_minor_and_major_increases_pass(self):
        for version in ("1.2.10", "1.3.0", "2.0.0"):
            with self.subTest(version=version):
                self.git("reset", "--hard", self.base)
                self.plugin("alpha", version)
                self.commit()
                self.check()

    def test_lower_version_does_not_release_new_content(self):
        self.plugin("alpha", "1.2.8")
        self.commit()
        self.check(1)

    def test_concurrent_release_cannot_reuse_the_same_version(self):
        self.plugin("alpha", "1.2.10")
        self.write("plugins/alpha/skills/example/SKILL.md", "other release\n")
        released = self.commit()
        self.git("reset", "--hard", self.base)
        self.plugin("alpha", "1.2.10")
        self.write("plugins/alpha/skills/example/SKILL.md", "this release\n")
        self.commit()
        self.check(1, base=released)

    def test_bumping_another_plugin_does_not_cover_the_change(self):
        self.plugin("beta", "0.1.1")
        self.write("plugins/alpha/skills/example/SKILL.md", "changed\n")
        self.commit()
        self.check(1)

    def test_root_only_change_needs_no_package_bump(self):
        self.write("README.md", "repository documentation\n")
        self.commit()
        self.check()

    def test_new_and_fully_removed_plugins(self):
        self.plugin("gamma", "0.1.0")
        self.commit()
        self.check()
        self.git("rm", "-r", "plugins/alpha")
        for relative in MARKETPLACES:
            listing = json.loads((self.root / relative).read_text())
            listing["plugins"] = [p for p in listing["plugins"] if p["name"] != "alpha"]
            self.write(relative, json.dumps(listing))
        self.commit()
        self.check()

    def test_each_host_surface_must_agree(self):
        paths = (*MARKETPLACES, "plugins/alpha/.codex-plugin/plugin.json")
        for relative in paths:
            with self.subTest(path=relative):
                self.git("reset", "--hard", self.base)
                self.plugin("alpha", "1.2.10")
                path = self.root / relative
                self.write(relative, path.read_text().replace('1.2.10', '1.2.9'))
                self.commit()
                self.check(2)

    def test_missing_manifest_or_marketplace_entry_refuses(self):
        self.git("rm", "plugins/alpha/.claude-plugin/plugin.json")
        self.commit()
        self.check(2)

    def test_codex_marketplace_may_omit_its_optional_version(self):
        relative = MARKETPLACES[1]
        listing = json.loads((self.root / relative).read_text())
        for item in listing["plugins"]:
            del item["version"]
        self.write(relative, json.dumps(listing))
        self.commit()
        self.check()

    def test_null_optional_version_refuses(self):
        relative = MARKETPLACES[1]
        listing = json.loads((self.root / relative).read_text())
        listing["plugins"][0]["version"] = None
        self.write(relative, json.dumps(listing))
        self.commit()
        self.check(2)

    def test_missing_base_and_option_shaped_ref_refuse(self):
        self.check(2, base="missing-base")
        self.check(2, base="--help")

    def test_invalid_versions_refuse(self):
        for version in ("1.2", "01.2.10", "1.2.10+build", "1.2.10-beta", 4, None):
            with self.subTest(version=version):
                self.git("reset", "--hard", self.base)
                self.plugin("alpha", version)
                self.commit()
                self.check(2)

    def test_invalid_and_duplicate_key_json_refuse(self):
        path = "plugins/alpha/.claude-plugin/plugin.json"
        for source in ('{', '[]', '{"name":"alpha","version":"1.2.9","version":"1.2.10"}'):
            with self.subTest(source=source):
                self.git("reset", "--hard", self.base)
                self.write(path, source)
                self.commit()
                self.check(2)

    def test_unlisted_plugin_and_stale_removed_listing_refuse(self):
        self.git("rm", "-r", "plugins/alpha")
        self.commit()
        self.check(2)

    def test_duplicate_marketplace_entry_refuses(self):
        relative = MARKETPLACES[0]
        listing = json.loads((self.root / relative).read_text())
        listing["plugins"].append(listing["plugins"][0])
        self.write(relative, json.dumps(listing))
        self.commit()
        self.check(2)

    def test_symlink_cannot_supply_a_manifest(self):
        path = self.root / "plugins/alpha/.claude-plugin/plugin.json"
        path.unlink()
        path.symlink_to("../.codex-plugin/plugin.json")
        self.commit()
        self.check(2)

    def test_staged_tree_is_checked_without_reading_unstaged_files(self):
        self.write("plugins/alpha/skills/example/SKILL.md", "changed\n")
        self.git("add", "-A")
        tree = self.git("write-tree")
        self.plugin("alpha", "1.2.10")
        self.check(1, head=tree)
        self.git("add", "-A")
        self.check(head=self.git("write-tree"))


if __name__ == "__main__":
    unittest.main()
