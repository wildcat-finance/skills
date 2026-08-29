"""Checks for the dependency-closed skills.sh Promise Machine package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / ".agents" / "skills" / "promise-machine"
RUNTIME = PACKAGE / "runtime"
MANIFEST = RUNTIME / "MANIFEST.json"
GENERATOR = ROOT / "scripts" / "portable_promise_machine.py"
CONFIG = ROOT / "skills.sh.json"

SCHEMA = "promise-machine-portable-runtime/v1"
CONTRACT = "promise-machine/v1"
MAX_FILES = 1_000
MAX_BYTES = 25 * 1024 * 1024
EXPECTED_OMISSIONS = {
    "plugins/*/.claude-plugin/**",
    "plugins/*/.codex-plugin/**",
    "plugins/*/audit/**",
    "plugins/*/tests/**",
    "plugins/alexandria/examples/compound-v3-phase0-v0/input/**",
    "plugins/alexandria/examples/compound-v3-phase0-v0/release/**",
    "plugins/alexandria/examples/compound-v3-phase0-v0/source/**",
}
PORTABLE_TEST_FILES = {
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/accepted-job.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/duplicate-field.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/excessive-depth.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/framing-cases.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/invalid-unicode.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/jobspec.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/lifecycle-cases.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/manifest.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/policy.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/policy.sha256",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/provider-cases.json",
    "plugins/hexaemeron/tests/fixtures/model-proxy-v1/rejections.json",
}


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


class SkillsShPackageTests(unittest.TestCase):
    def test_skills_sh_groups_only_the_supported_collective_install(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(
            config["$schema"], "https://skills.sh/schemas/skills.sh.schema.json"
        )
        self.assertEqual(config["notGrouped"], "bottom")
        self.assertEqual(
            [skill for group in config["groupings"] for skill in group["skills"]],
            ["promise-machine"],
        )

    def test_generated_runtime_is_current(self):
        result = subprocess.run(  # phylax: allow subprocess: fixed local checker
            [sys.executable, str(GENERATOR), "check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_binds_every_runtime_file_to_source_bytes(self):
        manifest = load_manifest()
        self.assertEqual(manifest["schema"], SCHEMA)
        self.assertEqual(manifest["contract"], CONTRACT)
        self.assertEqual(manifest["file_count"], len(manifest["files"]))
        self.assertLess(manifest["file_count"], MAX_FILES)
        self.assertLess(manifest["total_bytes"], MAX_BYTES)
        self.assertEqual(
            {entry["pattern"] for entry in manifest["omissions"]},
            EXPECTED_OMISSIONS,
        )
        tests_omission = next(
            entry
            for entry in manifest["omissions"]
            if entry["pattern"] == "plugins/*/tests/**"
        )
        self.assertEqual(set(tests_omission["exceptions"]), PORTABLE_TEST_FILES)

        expected = {"MANIFEST.json"}
        total = 0
        for row in manifest["files"]:
            relative = Path(row["path"])
            installed = RUNTIME / relative
            with self.subTest(path=row["path"]):
                self.assertFalse(relative.is_absolute())
                self.assertNotIn("..", relative.parts)
                self.assertTrue(installed.is_file())
                self.assertFalse(installed.is_symlink())
                data = installed.read_bytes()
                if row["source"] is None:
                    self.assertEqual(row["path"], ".horos/boundary.json")
                    self.assertEqual(
                        row["generated_by"],
                        "plugins/horos/skills/horos/scripts/horos.py",
                    )
                else:
                    source = ROOT / row["source"]
                    self.assertTrue(source.is_file())
                    self.assertEqual(data, source.read_bytes())
                self.assertEqual(row["bytes"], len(data))
                self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())
            total += row["bytes"]
            expected.add(relative.as_posix())
        self.assertEqual(manifest["total_bytes"], total)
        actual = {
            path.relative_to(RUNTIME).as_posix()
            for path in RUNTIME.rglob("*")
            if path.is_file() or path.is_symlink()
        }
        self.assertEqual(actual, expected)
        boundary = json.loads(
            (RUNTIME / ".horos/boundary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(boundary["universe"], "filesystem")
        self.assertTrue(boundary["entries"])
        self.assertEqual(
            (
                RUNTIME / ".agents/skills/promise-machine/SKILL.md"
            ).read_bytes(),
            (PACKAGE / "SKILL.md").read_bytes(),
        )

    def test_no_manifested_runtime_file_is_gitignored(self):
        paths = [
            (
                Path(".agents/skills/promise-machine/runtime") / row["path"]
            ).as_posix()
            for row in load_manifest()["files"]
        ]
        result = subprocess.run(  # phylax: allow subprocess: fixed git ignore query
            ["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin"],
            input="\n".join(paths) + "\n",
            capture_output=True,
            text=True,
        )
        ignored = result.stdout.splitlines()
        self.assertIn(result.returncode, (0, 1), result.stderr)
        self.assertEqual(ignored, [])

    def test_runtime_contracts_reach_every_copied_canonical_skill(self):
        plugins = RUNTIME / "plugins"
        for plugin in sorted(path for path in plugins.iterdir() if path.is_dir()):
            contract = (plugin / "AGENTS.md").read_text(encoding="utf-8")
            linked = {
                (plugin / relative).resolve()
                for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", contract)
            }
            expected = {path.resolve() for path in plugin.glob("skills/**/SKILL.md")}
            with self.subTest(plugin=plugin.name):
                self.assertEqual(linked, expected)
                self.assertTrue(expected)
                for path in linked:
                    self.assertTrue(path.is_file(), path)
                    self.assertTrue(path.is_relative_to(plugin), path)

    def test_authoritative_runtime_links_close_inside_the_package(self):
        documents = [
            RUNTIME / "AGENTS.md",
            RUNTIME / ".agents/skills/promise-machine/SKILL.md",
        ]
        documents.extend(sorted((RUNTIME / "plugins").glob("*/AGENTS.md")))
        documents.extend(sorted((RUNTIME / "plugins").glob("*/skills/**/SKILL.md")))
        missing = []
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for raw in re.findall(r"\[[^]]*\]\(([^)]+)\)", text):
                link = raw.split("#", 1)[0]
                if not link or "://" in link or link.startswith("mailto:"):
                    continue
                # X-Ray shows links to an invariants.md that the selected skill
                # produces in the user's target. It is output syntax, not a
                # package dependency.
                if document.parent.name == "x-ray" and link == "invariants.md":
                    continue
                target = (document.parent / link).resolve()
                if not target.exists():
                    missing.append(
                        f"{document.relative_to(RUNTIME).as_posix()} -> {raw}"
                    )
        self.assertEqual(missing, [])

    def test_declared_omissions_are_absent(self):
        for plugin in sorted((RUNTIME / "plugins").iterdir()):
            if not plugin.is_dir():
                continue
            with self.subTest(plugin=plugin.name):
                self.assertFalse((plugin / ".claude-plugin").exists())
                self.assertFalse((plugin / ".codex-plugin").exists())
                self.assertFalse((plugin / "audit").exists())
                if plugin.name != "hexaemeron":
                    self.assertFalse((plugin / "tests").exists())
        portable_tests = RUNTIME / "plugins/hexaemeron/tests"
        self.assertEqual(
            {
                path.relative_to(RUNTIME).as_posix()
                for path in portable_tests.rglob("*")
                if path.is_file() or path.is_symlink()
            },
            PORTABLE_TEST_FILES,
        )
        example = RUNTIME / "plugins/alexandria/examples/compound-v3-phase0-v0"
        self.assertTrue((example / "README.md").is_file())
        self.assertTrue((example / "rebuild.py").is_file())
        for omitted in ("input", "release", "source"):
            self.assertFalse((example / omitted).exists())

    def test_selected_directory_works_as_an_isolated_copy(self):
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            installed = project / ".agents" / "skills" / "promise-machine"
            installed.parent.mkdir(parents=True)
            shutil.copytree(PACKAGE, installed)
            self.assertFalse((project / "PROMISE_MACHINE.md").exists())
            self.assertFalse((project / "plugins").exists())
            result = subprocess.run(  # phylax: allow subprocess: fixed installed verifier
                [sys.executable, str(installed / "scripts" / "verify_runtime.py")],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(CONTRACT, result.stdout)
            self.assertTrue((installed / "runtime" / "AGENTS.md").is_file())
            self.assertTrue(
                (
                    installed
                    / "runtime/plugins/alexandria/skills/alexandria/SKILL.md"
                ).is_file()
            )
            horos = (
                installed
                / "runtime/plugins/horos/skills/horos/scripts/horos.py"
            )
            boundary = subprocess.run(  # phylax: allow subprocess: fixed installed Horos check
                [sys.executable, str(horos), "check", str(installed / "runtime")],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                boundary.returncode, 0, boundary.stdout + boundary.stderr
            )
            model_proxy = (
                installed
                / "runtime/plugins/hexaemeron/skills/phylax/scripts/model_proxy.py"
            )
            conformance_manifest = (
                installed
                / "runtime/plugins/hexaemeron/tests/fixtures/model-proxy-v1/manifest.json"
            )
            conformance = subprocess.run(  # phylax: allow subprocess: fixed installed demo
                [
                    sys.executable,
                    str(model_proxy),
                    "conformance",
                    "--manifest",
                    str(conformance_manifest),
                ],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                conformance.returncode,
                0,
                conformance.stdout + conformance.stderr,
            )
            self.assertEqual(
                json.loads(conformance.stdout)["outcome"],
                "conformance_checked",
            )


if __name__ == "__main__":
    unittest.main()
