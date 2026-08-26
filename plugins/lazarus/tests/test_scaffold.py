"""The Lazarus shell keeps every host and document on one contract."""

import hashlib
import json
import re
import unittest

from . import support
from lazarus_lib import __version__


class ScaffoldTests(unittest.TestCase):
    def test_host_manifests_parse_and_agree(self):
        claude = support.load_json(".claude-plugin/plugin.json")
        codex = support.load_json(".codex-plugin/plugin.json")
        for manifest in (claude, codex):
            self.assertEqual(manifest["name"], "lazarus")
            self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(claude["version"], codex["version"])
        self.assertEqual(claude["description"], codex["description"])
        self.assertEqual(claude["license"], "Apache-2.0")

    def test_the_host_manifests_follow_the_package_and_not_the_skill_or_writer(self):
        """Two axes, kept apart on purpose.

        The host manifests carry the installable package version. The skill
        version moves under its evolution ledger, while `__version__` is what
        Lazarus stamps into a fixture as `tool_version`. A release may move the
        package without rewriting either behavioural history or old provenance.
        """
        marketplace = json.loads(
            (support.REPO_ROOT / ".claude-plugin/marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        entries = [entry for entry in marketplace["plugins"] if entry["name"] == "lazarus"]
        self.assertEqual(len(entries), 1)
        package = entries[0]["version"]
        for host in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            with self.subTest(host=host):
                self.assertEqual(support.load_json(host)["version"], package)
        self.assertNotEqual(package, support.skill_version())
        self.assertNotEqual(package, __version__)

    def test_the_writer_version_is_the_one_the_fixture_records(self):
        """Pinned to the artefact it appears in rather than to a literal, so a
        bump that would invalidate the checked-in fixture's provenance fails
        here rather than in the demonstration."""
        manifest = support.load_json("examples/goldfinch-v0/manifest.json")
        self.assertEqual(manifest["tool_version"], __version__)
        release = support.load_json("examples/goldfinch-v0-release/release.json")
        self.assertEqual(release["tool_version"], __version__)

    def test_skill_is_canonical_and_has_no_readme_shadow(self):
        self.assertTrue(support.SKILL.is_file())
        self.assertFalse((support.SKILL.parent / "README.md").exists())

    def test_promise_machine_router_reaches_the_runtime_contract(self):
        path = support.REPO_ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        links = re.findall(r"\[[^]]+\]\(([^)]+)\)", text)
        self.assertIn("../../../plugins/lazarus/AGENTS.md", links)
        contract = (support.PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("`skills/lazarus/SKILL.md`", contract)
        for alias in ("/lazarus:lazarus", "$lazarus"):
            self.assertIn(alias, contract)

    def test_runtime_contract_documents_planned_entrypoints_and_boundaries(self):
        contract = (support.PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("skills/lazarus/SKILL.md", contract)
        self.assertIn("scripts/lazarus.py", contract)
        for command in ("capture", "verify", "replay"):
            self.assertIn(f"`{command}`", contract)
        self.assertIn("implements format validation", contract)
        self.assertIn("no provider, proxy or fallback", contract)
        self.assertIn("--anchor-rpc-env", contract)
        self.assertIn("canonical-chain", contract)
        self.assertIn("provider independence", contract)

    def test_chain_anchor_guide_and_example_are_discoverable(self):
        guide = support.PLUGIN_ROOT / "docs" / "chain-anchors.md"
        self.assertTrue(guide.is_file())
        text = guide.read_text(encoding="utf-8")
        for term in (
            "SOURCE_ID=ENV_VAR",
            "share",
            "canonical-chain",
            "provider independence",
            "multi-provider-anchor-v0",
        ):
            self.assertIn(term, text)
        example = support.PLUGIN_ROOT / "examples" / "multi-provider-anchor-v0"
        self.assertEqual(
            {path.name for path in example.iterdir()},
            {
                "anchors.jsonl",
                "header.json",
                "manifest.json",
                "plan.json",
                "proofs.jsonl",
                "rpc.jsonl",
            },
        )

    def test_generation_1_2_0_remains_one_existing_ledger_row(self):
        self.assertEqual(support.skill_version(), "1.2.0")
        ledger = (support.SKILL.parent / "EVOLUTION.md").read_text(encoding="utf-8")
        self.assertEqual(ledger.count("| `lazarus-v1.2.0` |"), 1)
        for line in (
            "- Current version: `lazarus-v1.2.0`",
            "- Frontier status: `open`",
            "- Frontier revision: `receipt-inclusion-proofs`",
        ):
            self.assertIn(line, ledger)

    def test_requirements_are_exact_direct_pins(self):
        requirements = (support.PLUGIN_ROOT / "requirements.txt").read_text().splitlines()
        pins = [line for line in requirements if line and not line.startswith("#")]
        self.assertEqual(len(pins), 4)
        self.assertEqual(
            {re.split(r"(?:\[.*\])?==", pin, maxsplit=1)[0] for pin in pins},
            {"eth-hash", "jsonschema", "rlp", "trie"},
        )
        for pin in pins:
            self.assertRegex(pin, r"^[a-z0-9-]+(?:\[[a-z0-9-]+\])?==\d+\.\d+\.\d+$")

    def test_transitive_runtime_environment_is_locked(self):
        direct = {
            re.split(r"(?:\[.*\])?==", line, maxsplit=1)[0]
            for line in (support.PLUGIN_ROOT / "requirements.txt").read_text().splitlines()
            if line and not line.startswith("#")
        }
        lines = (support.PLUGIN_ROOT / "requirements.lock").read_text().splitlines()
        locked = [line for line in lines if line and not line.startswith("#")]
        names = {re.split(r"(?:\[.*\])?==", line, maxsplit=1)[0] for line in locked}
        self.assertTrue(direct.issubset(names))
        self.assertTrue({"eth-utils", "pydantic-core", "rpds-py"}.issubset(names))
        self.assertEqual(len(names), len(locked))
        for pin in locked:
            self.assertRegex(pin, r"^[a-z0-9-]+(?:\[[a-z0-9-]+\])?==\d+\.\d+\.\d+$")

    def test_reviewed_design_documents_are_committed(self):
        study = (support.PLUGIN_ROOT / "docs" / "study.md").read_text(encoding="utf-8")
        runbook = (support.PLUGIN_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
        self.assertTrue(study.startswith("# Lazarus study\n"))
        self.assertIn("## Selected format and verification details", study)
        self.assertTrue(runbook.startswith("# Lazarus implementation runbook\n"))
        self.assertIn("## Step 6: Ship and run the Goldfinch demonstration", runbook)

    def test_multi_provider_anchor_specification_copies_are_exact(self):
        root = support.REPO_ROOT / "docs" / "lazarus-multi-provider-chain-anchor"
        expected = {
            "study.md": "f16d14e2182f872d95e56b4485218a264286a845f80b2857960dcd32c14442fd",
            "runbook.md": "e6ad38a1b934a7d61ee81ce6b01341a863d79e4841bec7b75ca84c29f6f8d8d7",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    hashlib.sha256((root / name).read_bytes()).hexdigest(), digest
                )

    def test_lazarus_owns_its_structured_unittest_runner(self):
        tests = support.PLUGIN_ROOT / "tests"
        self.assertTrue((tests / "run_tests.py").is_file())
        self.assertTrue((tests / "test_runner.py").is_file())

    def test_cli_and_step_five_modules_exist(self):
        self.assertTrue((support.PLUGIN_ROOT / "scripts" / "lazarus.py").is_file())
        package_files = {
            path.name
            for path in (support.PLUGIN_ROOT / "scripts" / "lazarus_lib").glob("*.py")
        }
        self.assertEqual(
            package_files,
            {
                "__init__.py",
                "binding.py",
                "canonical.py",
                "capture.py",
                "errors.py",
                "header.py",
                "hexvalue.py",
                "limits.py",
                "manifest.py",
                "paths.py",
                "proofs.py",
                "records.py",
                "release.py",
                "replay.py",
                "rlp.py",
                "rpc.py",
                "schemas.py",
                "scrub.py",
                "text.py",
                "server.py",
                "trieproof.py",
                "verifier.py",
                "version.py",
            },
        )


if __name__ == "__main__":
    unittest.main()
