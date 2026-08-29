"""The scaffold's own honesty checks.

The repository suite holds every plugin to the marketplace contract from the
outside. These tests hold berean's shell together from the inside, so a
drifted description, ledger digest or frontier sentence fails here, in this
plugin's suite, before the root suite has to say so. The repo-wide invariants
(version agreement, cross-host description parity) route through the shared
``repo_contract`` helper so the check has one definition; the ledger digest and
frontier assertions below stay berean's own.
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import unittest

from tests.support import PLUGIN_ROOT, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from repo_contract import assert_version_agreement, assert_host_descriptions_agree


def read(path):
    return path.read_text(encoding="utf-8")


GIT = shutil.which("git")


@unittest.skipIf(
    GIT is None or not (REPO_ROOT / ".git").is_dir(), "source checkout required"
)
class PackagingTests(unittest.TestCase):
    def test_pinned_release_corpora_are_not_fuzzer_output(self):
        paths = (
            "plugins/berean/examples/goldfinch-demo-v0/release/corpus/terms.md",
            "plugins/berean/tests/fixtures/conformance/pass-release/corpus/terms.md",
        )
        for path in paths:
            # phylax: allow subprocess: fixed git argv in source checkout
            completed = subprocess.run(
                [GIT, "-C", str(REPO_ROOT), "check-ignore", "--quiet", "--", path],
                capture_output=True,
                check=False,
            )
            with self.subTest(path=path):
                self.assertEqual(
                    completed.returncode,
                    1,
                    "Berean's pinned corpus bytes must not match an output ignore rule",
                )


class ManifestTests(unittest.TestCase):
    def test_the_three_manifests_agree(self):
        assert_version_agreement(self, "berean")
        assert_host_descriptions_agree(self, "berean")

    def test_the_openai_interface_carries_the_same_description(self):
        claude = json.loads(read(PLUGIN_ROOT / ".claude-plugin" / "plugin.json"))
        yaml_text = read(
            PLUGIN_ROOT / "skills" / "berean" / "agents" / "openai.yaml"
        )
        match = re.search(r'(?m)^  short_description: "([^"\n]+)"$', yaml_text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), claude["description"])


class LedgerTests(unittest.TestCase):
    def fields(self):
        text = read(PLUGIN_ROOT / "skills" / "berean" / "EVOLUTION.md")
        out = {}
        for key in (
            "Current version",
            "Frontier status",
            "Frontier revision",
            "Current frontier",
            "Next Fiat job",
        ):
            match = re.search(rf"(?m)^- {re.escape(key)}: (.+)$", text)
            self.assertIsNotNone(match, key)
            out[key] = match.group(1).strip().strip("`")
        return text, out

    def test_the_ledger_digest_reproduces(self):
        text, fields = self.fields()
        expected = hashlib.sha256(
            (
                "|".join(
                    (
                        fields["Frontier status"],
                        fields["Frontier revision"],
                        fields["Current frontier"],
                        fields["Next Fiat job"],
                    )
                )
                + "\n"
            ).encode("utf-8")
        ).hexdigest()
        rows = re.findall(r"(?m)^\| `berean-v[^`]+` \| .+ \|$", text)
        self.assertTrue(rows)
        self.assertIn(f"`{expected}`", rows[-1])

    def test_the_skill_version_matches_the_ledger(self):
        _, fields = self.fields()
        skill = read(PLUGIN_ROOT / "skills" / "berean" / "SKILL.md")
        match = re.search(r'(?m)^  version: "(\d+\.\d+\.\d+)"$', skill)
        self.assertIsNotNone(match)
        self.assertEqual(
            fields["Current version"], f"berean-v{match.group(1)}"
        )


class FrontierTests(unittest.TestCase):
    def test_every_marketplace_block_carries_the_same_frontier(self):
        landing = read(PLUGIN_ROOT / "README.md")
        expected = re.search(
            r"\*\*Current frontier\.\*\* ([^\n]+)", landing
        ).group(1).strip()
        surfaces = sorted(PLUGIN_ROOT.rglob("*.md"))
        surfaces.append(
            REPO_ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md"
        )
        checked = 0
        for path in surfaces:
            text = read(path)
            if "<!-- marketplace-context:start -->" not in text:
                continue
            found = re.search(r"\*\*Current frontier(?:\.|:)\*\*\s*([^\n]+)", text)
            self.assertIsNotNone(found, path)
            self.assertEqual(found.group(1).strip(), expected, path)
            checked += 1
        self.assertGreaterEqual(checked, 5)


if __name__ == "__main__":
    unittest.main()
