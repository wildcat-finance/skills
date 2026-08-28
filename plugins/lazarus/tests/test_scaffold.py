"""The Lazarus shell keeps every host and document on one contract."""

import hashlib
import json
import re
import sys
import unittest

from . import support
from lazarus_lib import __version__

sys.path.insert(0, str(support.REPO_ROOT))
from repo_contract import (
    assert_version_agreement,
    assert_host_descriptions_agree,
    assert_router_reaches,
)


class ScaffoldTests(unittest.TestCase):
    def test_host_manifests_parse_and_agree(self):
        assert_version_agreement(self, "lazarus")
        assert_host_descriptions_agree(self, "lazarus")
        claude = support.load_json(".claude-plugin/plugin.json")
        codex = support.load_json(".codex-plugin/plugin.json")
        for manifest in (claude, codex):
            self.assertEqual(manifest["name"], "lazarus")
            self.assertEqual(manifest["skills"], "./skills/")
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
        entries = [
            entry
            for entry in marketplace["plugins"]
            if entry["name"] == "lazarus"
        ]
        self.assertEqual(len(entries), 1)
        package = entries[0]["version"]
        for host in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            with self.subTest(host=host):
                self.assertEqual(support.load_json(host)["version"], package)
        self.assertNotEqual(package, support.skill_version())
        self.assertNotEqual(package, __version__)

    def test_writer_0_2_0_applies_only_to_new_artifacts(self):
        """Historical provenance stays historical when the writer advances."""
        self.assertEqual(__version__, "0.2.0")
        legacy_manifest = support.load_json("examples/goldfinch-v0/manifest.json")
        legacy_release = support.load_json(
            "examples/goldfinch-v0-release/release.json"
        )
        self.assertEqual(legacy_manifest["tool_version"], "0.1.0")
        self.assertEqual(legacy_release["tool_version"], "0.1.0")
        receipt_manifest = support.load_json("examples/goldfinch-v1/manifest.json")
        receipt_release = support.load_json(
            "examples/goldfinch-v1-release/release.json"
        )
        self.assertEqual(receipt_manifest["tool_version"], __version__)
        self.assertEqual(receipt_release["tool_version"], __version__)

    def test_skill_is_canonical_and_has_no_readme_shadow(self):
        self.assertTrue(support.SKILL.is_file())
        self.assertFalse((support.SKILL.parent / "README.md").exists())

    def test_promise_machine_router_reaches_the_runtime_contract(self):
        assert_router_reaches(self, "lazarus")
        # Alias surface is lazarus-specific, not part of the repo-wide contract.
        contract = (support.PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
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

    def test_evolution_2_2_0_advances_the_completed_receipt_frontier_once(self):
        self.assertEqual(support.skill_version(), "2.2.0")
        ledger = (support.SKILL.parent / "EVOLUTION.md").read_text(encoding="utf-8")
        self.assertEqual(ledger.count("| `lazarus-v1.2.0` |"), 1)
        self.assertEqual(ledger.count("| `lazarus-v2.2.0` |"), 1)
        for line in (
            "- Current version: `lazarus-v2.2.0`",
            "- Frontier status: `open`",
            "- Frontier revision: `empty-block-receipt-witnesses`",
        ):
            self.assertIn(line, ledger)
        self.assertIn("Goldfinch v1 demonstration", ledger)
        self.assertIn("empty block cannot yet be represented", ledger)

    def test_receipt_inclusion_proof_guide_is_discoverable(self):
        guide = support.PLUGIN_ROOT / "docs" / "receipt-inclusion-proofs.md"
        text = guide.read_text(encoding="utf-8")
        for term in (
            "goldfinch-v1",
            "224 consensus receipts",
            "transaction index `0xbf`",
            "110 consensus logs",
            "five-log projection",
            "receipt_trie_proved",
            "Transaction hashes are RPC decorations",
            "writer 0.2.0",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertIn("None of these commands accepts", text)
        self.assertNotIn("Neither command accepts", text)

    def test_public_receipt_proof_claims_are_current_and_scoped(self):
        contract = (support.PLUGIN_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = support.SKILL.read_text(encoding="utf-8")
        preservation = (
            support.PLUGIN_ROOT / "docs" / "preservation-release.md"
        ).read_text(encoding="utf-8")
        proof = (
            support.REPO_ROOT
            / "docs"
            / "lazarus-receipt-inclusion-proofs"
            / "proof.md"
        ).read_text(encoding="utf-8")

        start = "<!-- marketplace-context:start -->"
        end = "<!-- marketplace-context:end -->"
        self.assertIn(start, preservation)
        self.assertIn(end, preservation)
        canonical_context = contract[
            contract.index(start) : contract.index(end) + len(end)
        ]
        preservation_context = preservation[
            preservation.index(start) : preservation.index(end) + len(end)
        ]
        compact_proof = " ".join(proof.split())
        self.assertEqual(preservation_context, canonical_context)
        self.assertIn("for plan v2 or plan v3", contract)
        self.assertIn("Exact plan-v2 or plan-v3 anchor coverage", skill)
        self.assertIn("release-v2 may carry the two", preservation)
        self.assertNotIn("Nothing yet proves them", preservation)
        self.assertIn("Implementation packet state", compact_proof)
        self.assertIn(
            "The Step 5 implementation worker ran no controller command",
            compact_proof,
        )
        self.assertNotIn(
            "No controller command, network capture, push, publication, merge or "
            "issue mutation ran in this step.",
            compact_proof,
        )
        self.assertIn("Twenty-three observed failures were localised", proof)
        self.assertEqual(proof.count("\n23. "), 1)
        self.assertIn("Round 6 Warden source-bound entry runner", proof)
        self.assertIn("Canonical round-6 Elenchus parent comparison", proof)

        delivery_runbook = (
            support.REPO_ROOT
            / "docs"
            / "lazarus-receipt-inclusion-proofs"
            / "runbook.md"
        )
        self.assertTrue(delivery_runbook.is_file())
        delivery_runbook = delivery_runbook.read_text(encoding="utf-8")
        latest_amendment = delivery_runbook.rsplit(
            "### Amendment -- 2026-08-27", 1
        )[-1]
        self.assertIn(
            "--capture-command python3 --capture-command "
            "plugins/lazarus/examples/goldfinch-v1/demo.py --capture-command "
            "build-fixture --capture-command=--out --capture-command "
            "tmp/goldfinch-v1-rebuild",
            latest_amendment,
        )
        self.assertNotIn(
            "--capture-command lazarus --capture-command capture "
            "--capture-command goldfinch-v1",
            latest_amendment,
        )

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

    def test_receipt_proof_source_documents_are_preserved(self):
        root = support.REPO_ROOT / "docs" / "lazarus-receipt-inclusion-proofs"
        study = (root / "study.md").read_text(encoding="utf-8")
        source_study = study.replace("](../../", "](../")
        self.assertEqual(
            hashlib.sha256(source_study.encode("utf-8")).hexdigest(),
            "f8dd4bad531e8dbc236fec0bf0580d4a6a3a6284ce293a57a4d37af8555f9b79",
        )
        self.assertEqual(
            hashlib.sha256((root / "runbook.md").read_bytes()).hexdigest(),
            "8df93f70a40df951238dfa881d70638f88d2971043f04590eb7c8299aba0c459",
        )

    def test_receipt_proof_decision_is_discoverable(self):
        path = (
            support.REPO_ROOT
            / "docs"
            / "decisions"
            / "ADR-037-prove-receipts-with-a-full-ordered-witness.md"
        )
        text = path.read_text(encoding="utf-8")
        for term in (
            "## Decision",
            "eth_getBlockReceipts",
            "Receipt-witness-v1",
            "filtered-log relation",
            "recorded_rpc",
            "recorded lookup label",
            "transaction trie",
            "## Alternatives",
            "Capture only the target receipt",
            "debug_getRawReceipts",
            "Re-execute every transaction",
        ):
            self.assertIn(term, text)

    def test_fixed_shell_ci_toolchain_and_licence_remain_in_place(self):
        workflow = (support.REPO_ROOT / ".github/workflows/lazarus.yml").read_text(
            encoding="utf-8"
        )

        def event_paths(source, event):
            match = re.search(
                rf"(?m)^  {event}:\n    paths:\n(?P<paths>(?:      - .+\n)+)",
                source,
            )
            self.assertIsNotNone(match)
            return set(re.findall(r'^      - "([^"]+)"$', match["paths"], re.M))

        repo_workflow = (
            support.REPO_ROOT / ".github/workflows/repo.yml"
        ).read_text(encoding="utf-8")
        router = ".agents/skills/promise-machine/SKILL.md"
        generated_runtime = ".agents/**"
        for event in ("push", "pull_request"):
            with self.subTest(event=event):
                lazarus_paths = event_paths(workflow, event)
                self.assertIn(router, lazarus_paths)
                self.assertNotIn(generated_runtime, lazarus_paths)
                self.assertIn(generated_runtime, event_paths(repo_workflow, event))

        self.assertIn('python-version-file: ".python-version"', workflow)
        self.assertNotIn("matrix.python-version", workflow)
        self.assertIn(
            "python3 -m pip install --requirement plugins/lazarus/requirements.lock",
            workflow,
        )
        self.assertEqual(
            (support.PLUGIN_ROOT / "LICENSE").read_bytes(),
            (support.REPO_ROOT / "LICENSE").read_bytes(),
        )

    def test_lazarus_owns_its_structured_unittest_runner(self):
        tests = support.PLUGIN_ROOT / "tests"
        self.assertTrue((tests / "run_tests.py").is_file())
        self.assertTrue((tests / "run_receipt_delivery_tests.py").is_file())
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
                "receipts.py",
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
