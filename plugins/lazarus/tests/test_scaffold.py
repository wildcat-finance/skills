"""The Lazarus shell keeps every host and document on one contract."""

import ast
import hashlib
import json
import re
import sys
import textwrap
import unittest
from pathlib import Path

if __package__:
    from . import support
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from tests import support
from lazarus_lib import __version__

sys.path.insert(0, str(support.REPO_ROOT))
from repo_contract import (
    assert_version_agreement,
    assert_host_descriptions_agree,
    assert_router_reaches,
)


def darwin_workflow_function(workflow, name, namespace=None):
    """Compile one helper from the embedded Darwin acceptance program."""
    match = re.search(
        r"(?ms)^          python3 - <<'PY'\n(?P<script>.*?)^          PY$",
        workflow,
    )
    if match is None:
        raise AssertionError("the Darwin acceptance program is missing")
    module = ast.parse(textwrap.dedent(match["script"]))
    function = next(
        (
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ),
        None,
    )
    if function is None:
        raise AssertionError(f"the Darwin acceptance helper {name} is missing")
    selected = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(selected)
    scope = dict(namespace or {})
    # phylax: allow execute one AST-selected committed workflow helper in a closed test namespace
    exec(compile(selected, ".github/workflows/lazarus.yml", "exec"), scope)
    return scope[name]


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

    def test_writer_0_2_0_stamps_every_shipped_artifact(self):
        """Both shipped fixtures were written by the current writer.

        The repository previously kept one writer-0.1.0 artefact so the
        manifest-v1 path had a shipped example. Both fixtures were recaptured
        with 0.2.0, so that example is gone; manifest-v1 and manifest-v2
        coexistence is still proved by schema_version below.
        """
        self.assertEqual(__version__, "0.2.0")
        legacy_manifest = support.load_json("examples/aave-v4-spoke-v0/manifest.json")
        legacy_release = support.load_json(
            "examples/aave-v4-spoke-v0-release/release.json"
        )
        self.assertEqual(legacy_manifest["tool_version"], __version__)
        self.assertEqual(legacy_release["tool_version"], __version__)
        receipt_manifest = support.load_json("examples/aave-v4-spoke-v1/manifest.json")
        receipt_release = support.load_json(
            "examples/aave-v4-spoke-v1-release/release.json"
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
        self.assertIn("Aave v4 demonstration", ledger)
        self.assertIn("empty block cannot yet be represented", ledger)

    def test_receipt_inclusion_proof_guide_is_discoverable(self):
        guide = support.PLUGIN_ROOT / "docs" / "receipt-inclusion-proofs.md"
        text = guide.read_text(encoding="utf-8")
        for term in (
            "aave-v4-spoke-v1",
            "177 consensus receipts",
            "transaction index `0x3f`",
            "4 consensus logs",
            "two-log projection",
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
            "plugins/lazarus/examples/aave-v4-spoke-v1/demo.py --capture-command "
            "build-fixture --capture-command=--out --capture-command "
            "tmp/aave-v4-spoke-v1-rebuild",
            latest_amendment,
        )
        self.assertNotIn(
            "--capture-command lazarus --capture-command capture "
            "--capture-command aave-v4-spoke-v1",
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
        self.assertIn("## Step 6: Ship and run the Aave v4 demonstration", runbook)

    def test_multi_provider_anchor_specification_copies_are_exact(self):
        root = support.REPO_ROOT / "docs" / "lazarus-multi-provider-chain-anchor"
        expected = {
            "study.md": "6bf3442ecf32a3b875a9711b2660783cbe02806cc19d96978969cc7ab49a94ef",
            "runbook.md": "fd25aba20a8d21b49e1c3d48aead7a345c122fce22cbbe1995b641848dc651ef",
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
            "4b84aefc50ce34c15a523ad931888930ba2186ac2bc0497e0a24f6e89630f25e",
        )
        self.assertEqual(
            hashlib.sha256((root / "runbook.md").read_bytes()).hexdigest(),
            "08da441e7dd2a0293c5f466d6c691d50d67b5c742fe6907e48d54261da6ec0a4",
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

    def test_fixed_shell_ci_scope_toolchain_and_licence_remain_in_place(self):
        workflow = (support.REPO_ROOT / ".github/workflows/lazarus.yml").read_text(
            encoding="utf-8"
        )

        def event_paths(source, event, required=True):
            event_match = re.search(
                rf"(?ms)^  {re.escape(event)}:\n(?P<body>.*?)(?=^  [a-z_]+:|\Z)",
                source,
            )
            self.assertIsNotNone(event_match)
            paths_match = re.search(
                r"(?m)^    paths:\n(?P<paths>(?:      - .+\n)+)",
                event_match["body"],
            )
            if not required and paths_match is None:
                return None
            self.assertIsNotNone(paths_match)
            return set(
                re.findall(r'^      - "([^"]+)"$', paths_match["paths"], re.M)
            )

        repo_workflow = (
            support.REPO_ROOT / ".github/workflows/repo.yml"
        ).read_text(encoding="utf-8")
        shared_paths = {".agents/**", ".claude-plugin/**", "AGENTS.md"}
        for event in ("push", "pull_request"):
            with self.subTest(event=event):
                lazarus_paths = event_paths(workflow, event)
                self.assertTrue(lazarus_paths.isdisjoint(shared_paths))
                self.assertIsNone(event_paths(repo_workflow, event, required=False))

        plugins_path = support.REPO_ROOT / ".github/workflows/plugins.yml"
        self.assertTrue(plugins_path.is_file(), "the complete plugin workflow is missing")
        plugins_workflow = plugins_path.read_text(encoding="utf-8")
        for event in ("push", "pull_request"):
            with self.subTest(aggregate_event=event):
                self.assertIsNone(event_paths(plugins_workflow, event, required=False))
        # The aggregate gate shards the declared graph, one job per scope, so
        # Lazarus is covered by its own shard rather than by a single --full
        # invocation. What matters here is unchanged: the gate carries no path
        # filter, so its context reaches every pull request.
        self.assertIn(
            "python3 scripts/run_checks.py\n          --scope ${{ matrix.scope }}",
            plugins_workflow,
        )
        self.assertIn("          - lazarus\n", plugins_workflow)

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

    def test_darwin_job_holds_both_macos_path_repairs(self):
        workflow = (support.REPO_ROOT / ".github/workflows/lazarus.yml").read_text(
            encoding="utf-8"
        )
        match = re.search(r"(?ms)^  darwin:\n(?P<body>.*?)(?=^  [a-z][a-z0-9_-]*:\n|\Z)", workflow)
        self.assertIsNotNone(match, "the durable Darwin job is missing")
        body = match["body"]
        self.assertEqual(
            (support.REPO_ROOT / ".python-version").read_text(encoding="utf-8"),
            "3.14.6\n",
        )

        for term in (
            "runs-on: macos-15",
            'python-version-file: ".python-version"',
            "python3 -m pip install --requirement plugins/lazarus/requirements.lock",
            "test ! -e .lazarus-ci",
            "python3 plugins/lazarus/tests/run_tests.py --elenchus-report .lazarus-ci/lazarus-darwin-tests.json",
            "read_confined_bytes(",
            '"report_sha256": test_report_sha256',
            '"exit": 0',
            'tests["skipped"] != 0',
            "tempfile.TemporaryDirectory()",
            '"build-fixture"',
            "_tree_bytes(rebuilt_fixture) != _tree_bytes(checked_fixture)",
            "write_release(rebuilt_fixture, statement, release)",
            "verify_release(release)",
            '["git", "rev-parse", "HEAD"]',
            "platform.system()",
            "platform.machine()",
            "platform.python_version()",
            '"event": "lazarus_darwin_acceptance"',
            '"comparison": "byte-identical"',
            '"verification_exit": 0',
            '"statement_sha256": statement_sha256',
            '"lexical_root": alias_class',
            '"darwin_root_alias": alias_class',
            '"verified": True',
        ):
            with self.subTest(term=term):
                self.assertIn(term, body)

        self.assertEqual(
            re.findall(r"(?m)^permissions:\n  ([a-z-]+): ([a-z]+)$", workflow),
            [("contents", "read")],
        )
        for forbidden in (
            ".hexaemeron",
            "permissions:",
            "secrets.",
            "--rpc-url",
            "lazarus.py capture",
            "actions/upload-artifact",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, body)

    def test_darwin_job_refuses_malformed_test_report_counters(self):
        workflow = (support.REPO_ROOT / ".github/workflows/lazarus.yml").read_text(
            encoding="utf-8"
        )
        valid = {
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 621,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
        report = {"bytes": (json.dumps(valid, sort_keys=True) + "\n").encode()}
        calls = []

        def read_confined_bytes(root, relative, *, max_bytes):
            calls.append((root, relative, max_bytes))
            return report["bytes"]

        read_test_report = darwin_workflow_function(
            workflow,
            "_read_test_report",
            {
                "hashlib": hashlib,
                "json": json,
                "read_confined_bytes": read_confined_bytes,
            },
        )
        parsed, digest = read_test_report(Path("/checked-worktree"))
        self.assertEqual(parsed, valid)
        self.assertEqual(digest, hashlib.sha256(report["bytes"]).hexdigest())
        self.assertEqual(
            calls,
            [
                (
                    Path("/checked-worktree"),
                    ".lazarus-ci/lazarus-darwin-tests.json",
                    4096,
                )
            ],
        )

        malformed = []
        truthy_complete = dict(valid)
        truthy_complete["complete"] = "false"
        malformed.append(("truthy-complete", truthy_complete))
        boolean_counter = dict(valid)
        boolean_counter["testsRun"] = True
        malformed.append(("boolean-counter", boolean_counter))
        unknown_field = dict(valid)
        unknown_field["unknown"] = "silently accepted"
        malformed.append(("unknown-field", unknown_field))
        negative_counter = dict(valid)
        negative_counter["skipped"] = -1
        malformed.append(("negative-counter", negative_counter))
        for label, payload in malformed:
            with self.subTest(label=label):
                report["bytes"] = (json.dumps(payload, sort_keys=True) + "\n").encode()
                with self.assertRaises(AssertionError):
                    read_test_report(Path("/checked-worktree"))

    def test_darwin_acceptance_event_carries_the_required_signal_inventory(self):
        workflow = (support.REPO_ROOT / ".github/workflows/lazarus.yml").read_text(
            encoding="utf-8"
        )
        acceptance_event = darwin_workflow_function(
            workflow,
            "_acceptance_event",
        )
        tests = {
            "testsRun": 621,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }
        event = acceptance_event(
            "d" * 40,
            {"os": "Darwin", "architecture": "arm64", "python": "3.14.6"},
            tests,
            "1" * 64,
            "2" * 64,
            "3" * 64,
            "4" * 64,
            "var",
        )
        self.assertEqual(event["tests"]["exit"], 0)
        self.assertEqual(event["tests"]["report_sha256"], "1" * 64)
        self.assertEqual(event["release"]["verification_exit"], 0)
        self.assertEqual(event["release"]["statement_sha256"], "4" * 64)
        self.assertEqual(event["lexical_root"], "var")
        self.assertEqual(event["darwin_root_alias"], "var")
        rendered = json.dumps(event, sort_keys=True, separators=(",", ":"))
        for private_value in (
            ".lazarus-ci",
            "/private/tmp",
            "/var/folders",
            "statement bytes",
        ):
            with self.subTest(private_value=private_value):
                self.assertNotIn(private_value, rendered)

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
