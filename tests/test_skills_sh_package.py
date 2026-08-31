"""Checks for the dependency-closed skills.sh Promise Machine package."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


# The model proxy's receipt path refuses symlinked components by design.
# macOS resolves TMPDIR under /var, a symlink to /private/var, so every
# temporary directory built here -- and every child process that inherits
# TMPDIR -- would trip that refusal before a test began.  Canonicalising the
# temporary root hands the runtime a real path and leaves the refusal itself
# untouched.
tempfile.tempdir = os.path.realpath(tempfile.gettempdir())
os.environ["TMPDIR"] = tempfile.tempdir


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "portable_promise_machine.py"
DISTRIBUTION = ROOT / "distribution" / "skills-runtime" / "sync.yml"

# The package guarantees below are asserted against a tree the generator builds
# during this run, not against a copy committed here. That keeps them true of
# what is actually published now that this repository no longer carries the
# payload.
_PACKAGE_TMP: tempfile.TemporaryDirectory | None = None
GENERATED = None
PACKAGE = None
RUNTIME = None
MANIFEST = None


def build_package(destination):
    """Generate a complete package into `destination` and return its root."""
    result = subprocess.run(  # phylax: allow subprocess: fixed local generator argv
        [sys.executable, str(GENERATOR), "package", "--out", str(destination)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(result.stdout + result.stderr)
    return Path(destination)


def setUpModule():
    global _PACKAGE_TMP, GENERATED, PACKAGE, RUNTIME, MANIFEST
    _PACKAGE_TMP = tempfile.TemporaryDirectory(prefix="skills-sh-package.")
    GENERATED = build_package(Path(_PACKAGE_TMP.name) / "package")
    PACKAGE = GENERATED / ".agents" / "skills" / "promise-machine"
    RUNTIME = PACKAGE / "runtime"
    MANIFEST = RUNTIME / "MANIFEST.json"


def tearDownModule():
    if _PACKAGE_TMP is not None:
        _PACKAGE_TMP.cleanup()

SCHEMA = "promise-machine-portable-runtime/v1"
CONTRACT = "promise-machine/v1"
# The skills CLI's SKILLS_EXTRACT_MAX_FILES and SKILLS_EXTRACT_MAX_BYTES
# defaults.  They gate its `well-known` and `download` source types, which are
# direct SKILL.md and archive URLs; the `github` type this repository installs
# through never consults them.  Held anyway so the package stays installable by
# every route the CLI offers.  See ADR-054.
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


    def test_package_action_writes_a_complete_installable_tree(self):
        """A generated package carries its own grouping, README and runtime."""
        config = json.loads((GENERATED / "skills.sh.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [skill for group in config["groupings"] for skill in group["skills"]],
            ["promise-machine"],
        )
        readme = (GENERATED / "README.md").read_text(encoding="utf-8")
        commit = subprocess.run(  # phylax: allow subprocess: fixed local git argv
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertIn(commit, readme)
        self.assertIn("wildcat-finance/skills-runtime", readme)
        for relative in (
            ".agents/plugins/marketplace.json",
            ".agents/skills/promise-machine/SKILL.md",
            ".agents/skills/promise-machine/PORTABLE.md",
            ".agents/skills/promise-machine/scripts/verify_runtime.py",
        ):
            self.assertTrue((GENERATED / relative).is_file(), relative)

    def test_generated_package_verifies_itself_offline(self):
        verifier = PACKAGE / "scripts" / "verify_runtime.py"
        result = subprocess.run(  # phylax: allow subprocess: fixed local verifier argv
            [sys.executable, str(verifier)],
            cwd=GENERATED,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_refuses_an_unsafe_output_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            real = base / "real"
            real.mkdir()
            link = base / "link"
            link.symlink_to(real)
            plain = base / "plain"
            plain.write_text("", encoding="utf-8")
            cases = {
                link: "symlink",
                plain: "not a directory",
                base / "absent" / "deep": "output parent is not a directory",
            }
            for destination, expected in cases.items():
                with self.subTest(destination=destination.name):
                    result = subprocess.run(  # phylax: allow subprocess: fixed local generator argv
                        [
                            sys.executable,
                            str(GENERATOR),
                            "package",
                            "--out",
                            str(destination),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected, result.stdout + result.stderr)
            self.assertEqual(sorted(path.name for path in real.iterdir()), [])


    def test_package_refuses_to_clear_a_directory_it_did_not_write(self):
        """--out replaces the whole directory, so an occupied one is refused."""
        with tempfile.TemporaryDirectory() as raw:
            occupied = Path(raw) / "occupied"
            (occupied / "precious").mkdir(parents=True)
            keep = occupied / "precious" / "data.txt"
            keep.write_text("irreplaceable", encoding="utf-8")
            result = subprocess.run(  # phylax: allow subprocess: fixed local generator argv
                [sys.executable, str(GENERATOR), "package", "--out", str(occupied)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a generated package", result.stdout + result.stderr)
            self.assertEqual(keep.read_text(encoding="utf-8"), "irreplaceable")

            empty = Path(raw) / "empty"
            empty.mkdir()
            self.assertEqual(build_package(empty), empty)
            self.assertEqual(build_package(empty), empty)


    def test_published_workflow_copy_stays_narrow(self):
        """The destination's job is authored here, and its powers are bounded.

        The job commits to its own repository with GITHUB_TOKEN. Two properties
        keep that safe to leave running: it may write contents and nothing else,
        and it never writes a path under .github/workflows/, which is the one
        place a token could widen what runs next. A third keeps it honest: it
        refuses to run when it has drifted from this copy.
        """
        text = DISTRIBUTION.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: write\n", text)
        for scope in ("actions:", "packages:", "id-token:", "pull-requests:"):
            self.assertNotIn(scope, text)
        self.assertIn(
            "if: github.repository == 'wildcat-finance/skills-runtime'", text
        )
        self.assertIn(
            "git clone --depth=1 https://github.com/wildcat-finance/skills.git", text
        )
        body = text.split("jobs:", 1)[1]
        writes = re.findall(r"(?:cp|mv|rm|tee|>>?)\s+[^\n]*\.github/workflows", body)
        self.assertEqual(writes, [])
        self.assertIn("source/distribution/skills-runtime/sync.yml", text)
        self.assertIn("verify_runtime.py", text)
        # The job executes a generator cloned from another repository. A
        # push-capable credential must not be sitting in .git/config while that
        # runs, so the checkout drops it and the push supplies one explicitly.
        self.assertIn("persist-credentials: false", text)
        self.assertIn("x-access-token:${GITHUB_TOKEN}", text)
        # An unparsed README would otherwise commit "…/skills@" and read as a
        # successful rebuild of nothing identifiable.
        self.assertIn("the generated README names no source commit", text)


    def test_the_generated_runtime_is_not_tracked_here(self):
        """The payload is published elsewhere; a local sync must not re-add it."""
        tracked = subprocess.run(  # phylax: allow subprocess: fixed git listing
            ["git", "-C", str(ROOT), "ls-files", ".agents"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        self.assertEqual(
            sorted(tracked),
            [
                ".agents/plugins/marketplace.json",
                ".agents/skills/promise-machine/PORTABLE.md",
                ".agents/skills/promise-machine/SKILL.md",
                ".agents/skills/promise-machine/scripts/verify_runtime.py",
            ],
        )
        ignored = subprocess.run(  # phylax: allow subprocess: fixed git ignore query
            [
                "git",
                "-C",
                str(ROOT),
                "check-ignore",
                ".agents/skills/promise-machine/runtime/MANIFEST.json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(ignored.returncode, 0, "the generated runtime is not ignored")

    def test_this_repository_advertises_no_skills_sh_install(self):
        """It cannot serve one: the runtime it would need is not carried here."""
        self.assertFalse((ROOT / "skills.sh.json").exists())
        for document in (ROOT / "INSTALL.md", ROOT / "README.md"):
            text = document.read_text(encoding="utf-8")
            for line in text.splitlines():
                if "npx skills add" in line:
                    self.assertIn("wildcat-finance/skills-runtime", line, document.name)


if __name__ == "__main__":
    unittest.main()
