"""Step 1 guards for the framework-74 research boundary."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/instruction-architecture/benchmark.py"
FIXTURES = ROOT / "tests/fixtures/instruction-architecture"
MANIFEST = FIXTURES / "corpus-manifest.json"
PROFILES = FIXTURES / "invocation-profiles.json"
GRAPH = FIXTURES / "loader-graph.json"
PARTITION = FIXTURES / "byte-partition.json"
COHORTS = FIXTURES / "cohorts.json"
SEAL = FIXTURES / "holdout-seal.json"
INVENTORY = FIXTURES / "artifact-inventory.json"
SCHEMA = ROOT / "research/instruction-architecture/schemas/source-bound-v1.schema.json"
PROFILE_SCHEMA = ROOT / "research/instruction-architecture/schemas/invocation-profile-v1.schema.json"
STUDY = ROOT / "docs/instruction-architecture/study.md"
RUNBOOK = ROOT / "docs/instruction-architecture/runbook.md"
RECEIPTED_STUDY_SHA256 = (
    "566bbe3d7f6467d2d398cc25ea9ae4047d86aad0181f22402e1f0b558cb470fc"
)
AMENDED_RUNBOOK_SHA256 = (
    "9cea8c520b471e8b9975421b33c9fa345baa4d57fc930e74df75ffc90b715e92"
)
EXPECTED_KRONOS_RANKING_LEDGERS = {
    "plugins/alexandria/skills/alexandria/EVOLUTION.md",
    "plugins/anamnesis/skills/anamnesis/EVOLUTION.md",
    "plugins/ariadne/skills/ariadne/EVOLUTION.md",
    "plugins/berean/skills/berean/EVOLUTION.md",
    "plugins/brevitas/skills/brevitas/EVOLUTION.md",
    "plugins/hermes/skills/hermes/EVOLUTION.md",
    "plugins/hexaemeron/skills/elenchus/EVOLUTION.md",
    "plugins/hexaemeron/skills/ephoros/EVOLUTION.md",
    "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
    "plugins/hexaemeron/skills/hypomnema/EVOLUTION.md",
    "plugins/hexaemeron/skills/imprimatur/EVOLUTION.md",
    "plugins/hexaemeron/skills/metron/EVOLUTION.md",
    "plugins/hexaemeron/skills/phylax/EVOLUTION.md",
    "plugins/hexaemeron/skills/protasis/EVOLUTION.md",
    "plugins/hexaemeron/skills/vulgate/EVOLUTION.md",
    "plugins/homologia/skills/homologia/EVOLUTION.md",
    "plugins/horos/skills/horos/EVOLUTION.md",
    "plugins/janus/skills/janus/EVOLUTION.md",
    "plugins/lazarus/skills/lazarus/EVOLUTION.md",
    "plugins/lemma/skills/lemma/EVOLUTION.md",
    "plugins/pandects/skills/pandects/EVOLUTION.md",
    "plugins/probitas/skills/probitas/EVOLUTION.md",
    "plugins/sapheneia/skills/sapheneia/EVOLUTION.md",
    "plugins/synkrisis/skills/synkrisis/EVOLUTION.md",
    "plugins/tabularium/skills/tabularium/EVOLUTION.md",
}

EXPECTED_STRUCTURED_REFERENCES = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": (177_562, "5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac"),
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": (3_779, "d2ecc41b3da60df47d5a7ce86f338dbadf7beb18080957dee21881dae4503d1d"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": (3_716, "e554ab6f9661d88095f285c6651983c980bd672b854287f74daa288b1dabc34c"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": (7_842, "a6ad7adbc6c8e06512032cf460c92749a49a6c139b4f2aee101de8bdc95df844"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": (3_843, "908e20c6319b587e95fa21de5949a10c0088ed698d546b0a1048686211826240"),
    "plugins/homologia/references/manifest-v1.schema.json": (3_554, "b60b46a65def47e11347fe408709c137b17accdd6fe2b39872c102c7c7db7413"),
    "plugins/homologia/references/vectors-v1.schema.json": (3_494, "1031838d2405c949a2ad7fcb9c693119499f1f8183286fe2019e02fa6680b056"),
    "plugins/synkrisis/references/cohort-v1.schema.json": (3_204, "5e71420816444af4582e0380b9d6e7ff845e4b3686126233c24a9d1ab5335b0d"),
    "plugins/synkrisis/references/findings-v1.schema.json": (4_152, "52cf6589e57a93fa82eef75520be44f10636d2469eafe2dae9c91e1d457627c8"),
    "plugins/synkrisis/references/policy-v1.schema.json": (1_982, "04d440bdbd96fcff165d4b0badc029a79634bf17b1a7ac380baee85630c873bb"),
    "plugins/synkrisis/references/rule-v1.schema.json": (3_087, "c8b45c1b6e2b9de010d7ce17109a6f7d49a4797d5a79b07186eabdfa1ed44698"),
    "plugins/synkrisis/references/rules-v1.json": (2_361, "e754bb72235103290ec4ea58b2c71b851782573c3e27eb16a08fe762c3f3a4af"),
}

EXPECTED_OPERATION_REFERENCES = {
    "docs/fiat-run-observation-binding-v1.md",
    "plugins/alexandria/docs/runbook.md",
    "plugins/alexandria/docs/study.md",
    "plugins/alexandria/docs/usdc-interval-collector.md",
    "plugins/anamnesis/docs/demo.md",
    "plugins/ariadne/docs/capturing-a-dataset.md",
    "plugins/ariadne/docs/capturing-a-grounded-agent.md",
    "plugins/ariadne/docs/capturing-a-release.md",
    "plugins/ariadne/docs/capturing-a-state-fixture.md",
    "plugins/ariadne/docs/conformance.md",
    "plugins/ariadne/docs/dataset.md",
    "plugins/ariadne/docs/grounded-agent.md",
    "plugins/ariadne/docs/solidity-release.md",
    "plugins/ariadne/docs/state-fixture.md",
    "plugins/lazarus/docs/chain-anchors.md",
    "plugins/lazarus/docs/preservation-release.md",
    "plugins/lazarus/docs/runbook.md",
    "plugins/lazarus/docs/study.md",
    "plugins/lemma/INVARIANTS.md",
    "plugins/pandects/docs/applicability.md",
    "plugins/pandects/docs/writing-a-law.md",
    "plugins/pandects/integrations/wildcat/APPLICABILITY.md",
    "plugins/probitas/docs/adding-a-venue.md",
    "plugins/tabularium/docs/adding-an-adapter.md",
    "plugins/tabularium/docs/release-policy.md",
}

EXPECTED_ARIADNE_OPERATIONS = {
    "operation:ariadne:capture-dataset": {
        "plugins/ariadne/docs/capturing-a-dataset.md",
        "plugins/ariadne/docs/dataset.md",
    },
    "operation:ariadne:capture-grounded-agent": {
        "plugins/ariadne/docs/capturing-a-grounded-agent.md",
        "plugins/ariadne/docs/grounded-agent.md",
    },
    "operation:ariadne:capture-release": {
        "plugins/ariadne/docs/capturing-a-release.md",
        "plugins/ariadne/docs/solidity-release.md",
    },
    "operation:ariadne:capture-state-fixture": {
        "plugins/ariadne/docs/capturing-a-state-fixture.md",
        "plugins/ariadne/docs/state-fixture.md",
    },
    "operation:ariadne:conformance": {"plugins/ariadne/docs/conformance.md"},
}


def load_module():
    spec = importlib.util.spec_from_file_location("instruction_architecture", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AI = load_module()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_source_cache() -> None:
    cached = getattr(AI, "_source_object", AI._source_blob)
    cached.cache_clear()


def scratch_directory(prefix: str = "instruction-architecture-"):
    """Keep confined-path fixtures under the repository's ignored scratch root."""
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def command(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


class CorpusManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)

    def test_exact_inventory_and_denominators(self):
        self.assertEqual(self.manifest["counts"], AI.EXPECTED_COUNTS)
        self.assertEqual(self.manifest["totals"], AI.EXPECTED_TOTALS)
        paths = [item["path"] for item in self.manifest["documents"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))

    def test_source_directed_admission_is_exact_and_anchored(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        admissions = AI._additional_metadata()
        self.assertEqual(len(admissions), 70)
        self.assertEqual(
            {
                item["path"]
                for item in self.manifest["documents"]
                if item["admission_kind"] != "issue-census"
            },
            set(admissions)
            | set(AI._structured_metadata())
            | set(AI._fixed_agent_metadata()),
        )
        self.assertEqual(sum(documents[path]["bytes"] for path in admissions), 526_326)
        self.assertEqual(
            {
                class_name: sum(
                    1
                    for metadata in admissions.values()
                    if metadata["document_class"] == class_name
                )
                for class_name in sorted(
                    {metadata["document_class"] for metadata in admissions.values()}
                )
            },
            {
                "frontier_ledger": 26,
                "frontier_policy": 1,
                "identity_contract": 1,
                "identity_roster": 1,
                "operation_reference": 25,
                "overlay_contract": 1,
                "router_install_contract": 1,
                "worker_prompt": 14,
            },
        )
        for path, metadata in admissions.items():
            with self.subTest(path=path):
                self.assertEqual(
                    documents[path]["document_class"], metadata["document_class"]
                )
                evidence = AI._evidence(
                    metadata["source_path"], metadata["source_needle"]
                )
                self.assertGreater(evidence["end"], evidence["start"])

    def test_structured_reference_inventory_and_evidence_are_exact(self):
        documents = {
            item["path"]: item
            for item in self.manifest["documents"]
            if item["document_class"] == "structured_reference"
        }
        self.assertEqual(
            {
                path: (item["bytes"], item["sha256"])
                for path, item in documents.items()
            },
            EXPECTED_STRUCTURED_REFERENCES,
        )
        metadata = AI._structured_metadata()
        self.assertEqual(set(documents), set(metadata))
        self.assertEqual(sum(item["bytes"] for item in documents.values()), 218_576)
        for path, item in documents.items():
            with self.subTest(path=path):
                row = metadata[path]
                self.assertEqual(item["canonical_owner"], row["canonical_owner"])
                self.assertEqual(item["load_semantics"], row["load_semantics"])
                self.assertEqual(
                    item["source_evidence"],
                    AI._evidence(row["source_path"], row["source_needle"]),
                )
                if row["runtime_path"] is None:
                    self.assertIsNone(item["runtime_evidence"])
                    self.assertEqual(item["loader_roots"], [])
                    self.assertEqual(item["scenario_reachability"], [])
                else:
                    self.assertEqual(
                        item["runtime_evidence"],
                        AI._evidence(row["runtime_path"], row["runtime_needle"]),
                    )
                    self.assertTrue(item["loader_roots"])
                    self.assertTrue(item["scenario_reachability"])

    def test_fixed_agent_inputs_are_exact_and_never_executable(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/x-ray/VERSION": (
                2,
                "53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3",
            ),
            "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
                2,
                "1121cfccd5913f0a63fec40a6ffd44ea64f9dc135c66634ba001d10bcf4302a2",
            ),
        }
        self.assertEqual(set(AI._fixed_agent_metadata()), set(expected))
        for path, (size, digest) in expected.items():
            with self.subTest(path=path):
                item = documents[path]
                metadata = AI._fixed_agent_metadata()[path]
                self.assertEqual((item["bytes"], item["sha256"]), (size, digest))
                self.assertEqual(item["document_class"], "fixed_input")
                self.assertEqual(item["load_semantics"], "agent-or-prompt")
                self.assertIsNone(item["runtime_evidence"])
                self.assertEqual(
                    item["source_evidence"],
                    AI._evidence(metadata["source_path"], metadata["source_needle"]),
                )
                self.assertTrue(item["loader_roots"])
                self.assertTrue(item["scenario_reachability"])

    def test_operation_reference_closure_and_anamnesis_anchor_are_independent(self):
        operations = {
            item["path"]
            for item in self.manifest["documents"]
            if item["document_class"] == "operation_reference"
        }
        self.assertEqual(operations, EXPECTED_OPERATION_REFERENCES)
        demo = next(
            item
            for item in self.manifest["documents"]
            if item["path"] == "plugins/anamnesis/docs/demo.md"
        )
        self.assertEqual(demo["bytes"], 2_605)
        self.assertEqual(
            demo["sha256"],
            "b523e14fc000502dfc4aafc8732a77091803ab25b7e9ab990ff234f9702673cb",
        )
        self.assertEqual(
            demo["canonical_owner"],
            "plugins/anamnesis/skills/anamnesis/SKILL.md",
        )
        evidence = AI._evidence(
            "plugins/anamnesis/skills/anamnesis/SKILL.md", "../../docs/demo.md"
        )
        self.assertEqual((evidence["start"], evidence["end"]), (7_636, 7_654))
        self.assertEqual(
            evidence["span_sha256"],
            "9dfc4f04bae4c35cad57e454454283642f1676e2bb1e75178e1d83da81b793bc",
        )

    def test_independent_markdown_fixed_point_detects_an_unclassified_directive(self):
        derived = AI._derive_operative_markdown_targets(self.manifest["documents"])
        manifest_paths = {item["path"] for item in self.manifest["documents"]}
        self.assertEqual(derived["occurrences"], 298)
        self.assertEqual(len(derived["targets"]), 112)
        self.assertEqual(len(derived["excluded"]), 127)
        self.assertIn("plugins/anamnesis/docs/demo.md", derived["targets"])
        self.assertFalse(set(derived["targets"]) - manifest_paths)

        without_demo = [
            item
            for item in self.manifest["documents"]
            if item["path"] != "plugins/anamnesis/docs/demo.md"
        ]
        second_pass = AI._derive_operative_markdown_targets(without_demo)
        self.assertIn(
            "plugins/anamnesis/docs/demo.md",
            set(second_pass["targets"]) - {item["path"] for item in without_demo},
        )

        source = "plugins/anamnesis/skills/anamnesis/SKILL.md"
        synthetic = {
            "plugins/anamnesis/docs/new-operation.md",
            "plugins/anamnesis/docs/new-runbook.md",
        }
        repurposed = "plugins/pandects/docs/catalogue.md"
        changed_source = AI._source_blob(source) + (
            b"\nRead [the new operation](../../docs/new-operation.md) before acting.\n"
            b"Read [the new runbook](../../docs/new-runbook.md) before acting.\n"
            b"Read [the catalogue](../../../pandects/docs/catalogue.md) before acting.\n"
        )
        changed = AI._derive_operative_markdown_targets(
            self.manifest["documents"],
            source_overrides={source: changed_source},
            tree_paths={*AI._frozen_tree_paths(), *synthetic},
        )
        self.assertLessEqual(
            synthetic | {repurposed}, set(changed["targets"]) - manifest_paths
        )
        self.assertFalse(
            any(
                item["target"] in synthetic | {repurposed}
                for item in changed["excluded"]
            )
        )

    def test_independent_fixed_point_deriver_is_required(self):
        self.assertTrue(
            callable(getattr(AI, "_derive_operative_markdown_targets", None))
        )

    def test_extension_agnostic_fixed_point_and_runtime_anchor_mutations(self):
        derived = AI._derive_corpus_fixed_point(self.manifest["documents"])
        self.assertEqual(
            set(derived["structured_targets"]), set(EXPECTED_STRUCTURED_REFERENCES)
        )
        mandatory = {
            path
            for path, row in AI._structured_metadata().items()
            if row["load_semantics"] == "mandatory-executable"
        }
        self.assertEqual(set(derived["mandatory_executable_targets"]), mandatory)

        synthetic = "plugins/hermes/skills/hermes/references/new-rules.data"
        decoys = {
            "plugins/hermes/skills/hermes/scripts/generated-rules.json",
            "plugins/hexaemeron/skills/fizz/templates/output.json",
            "plugins/hermes/tests/fixtures/rules.json",
            "plugins/synkrisis/examples/specimens/rules.json",
            "project-inputs/rules.json",
        }
        with_synthetic = AI._derive_corpus_fixed_point(
            self.manifest["documents"],
            tree_paths={*AI._frozen_tree_paths(), synthetic, *decoys},
        )
        self.assertIn(synthetic, with_synthetic["structured_targets"])
        self.assertFalse(decoys & set(with_synthetic["structured_targets"]))

        for path in sorted(mandatory):
            row = AI._structured_metadata()[path]
            runtime_path = row["runtime_path"]
            self.assertIsNotNone(runtime_path)
            runtime = AI._source_blob(runtime_path)
            needle = row["runtime_needle"].encode()
            self.assertIn(needle, runtime)
            changed = AI._derive_corpus_fixed_point(
                self.manifest["documents"],
                source_overrides={runtime_path: runtime.replace(needle, b"", 1)},
            )
            self.assertNotIn(path, changed["mandatory_executable_targets"])
            source_path = row["source_path"]
            source = AI._source_blob(source_path)
            source_needle = row["source_needle"].encode()
            self.assertIn(source_needle, source)
            changed = AI._derive_corpus_fixed_point(
                self.manifest["documents"],
                source_overrides={
                    source_path: source.replace(source_needle, b"", 1)
                },
            )
            self.assertNotIn(path, changed["mandatory_executable_targets"])

    def test_every_structured_input_omission_and_move_refuses(self):
        tree = set(AI._frozen_tree_paths())
        for path in sorted(EXPECTED_STRUCTURED_REFERENCES):
            changed = tuple(sorted(tree - {path}))
            with self.subTest(path=path):
                with mock.patch.object(AI, "_frozen_tree_paths", return_value=changed):
                    with self.assertRaisesRegex(
                        AI.Refusal, "structured reference missing|topology drift"
                    ):
                        AI._corpus_paths()
        lexicon = "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json"
        moved = "plugins/hexaemeron/skills/imprimatur/templates/hard.json"
        with mock.patch.object(
            AI,
            "_frozen_tree_paths",
            return_value=tuple(sorted((tree - {lexicon}) | {moved})),
        ):
            with self.assertRaisesRegex(AI.Refusal, "structured reference missing"):
                AI._corpus_paths()

    def test_reference_suffix_does_not_control_non_markdown_admission(self):
        original = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        renamed = original.removesuffix(".json") + ".bin"
        tree = (set(AI._frozen_tree_paths()) - {original}) | {renamed}
        changed = AI._derive_corpus_fixed_point(
            self.manifest["documents"], tree_paths=tree
        )
        self.assertNotIn(original, changed["structured_targets"])
        self.assertIn(renamed, changed["structured_targets"])

    def test_same_repository_url_requires_exact_repository_ref_and_path(self):
        self.assertEqual(
            AI._same_repository_markdown_url(AI.CONTRIBUTORS_CANONICAL_URL),
            "CONTRIBUTORS.md",
        )
        for changed in (
            AI.CONTRIBUTORS_CANONICAL_URL.replace("wildcat-finance", "attacker"),
            AI.CONTRIBUTORS_CANONICAL_URL.replace("/main/", "/other/"),
            AI.CONTRIBUTORS_CANONICAL_URL.replace(
                "CONTRIBUTORS.md", "contributors.md"
            ),
            f"{AI.CONTRIBUTORS_CANONICAL_URL}?raw=1",
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(AI._same_repository_markdown_url(changed))

    def test_exact_duplicate_group_is_only_promise_machine(self):
        groups: dict[str, list[dict]] = {}
        for item in self.manifest["documents"]:
            if item["exact_duplicate_group"] is not None:
                groups.setdefault(item["exact_duplicate_group"], []).append(item)
        self.assertEqual(len(groups), 1)
        members = next(iter(groups.values()))
        self.assertEqual(len(members), 18)
        self.assertEqual(
            {item["logical_document"] for item in members}, {"promise-machine/v1"}
        )
        self.assertTrue(
            all(
                item["canonical_content_path"] == "PROMISE_MACHINE.md"
                for item in members
            )
        )

    def test_manifest_rebuild_is_exact(self):
        self.assertEqual(self.manifest, AI.build_manifest(load(PROFILES)))
        first = command(
            "verify-corpus", "--profiles", str(PROFILES), "--manifest", str(MANIFEST)
        )
        second = command(
            "verify-corpus", "--profiles", str(PROFILES), "--manifest", str(MANIFEST)
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_artifact_inventory_binds_every_baseline_record(self):
        inventory = load(INVENTORY)
        expected = {
            "corpus-manifest.json",
            "invocation-profiles.json",
            "loader-graph.json",
            "byte-partition.json",
            "cohorts.json",
            "holdout-seal.json",
        }
        self.assertEqual(set(inventory["artifacts"]), expected)
        for name, record in inventory["artifacts"].items():
            path = FIXTURES / name
            self.assertEqual(
                record, {"bytes": path.stat().st_size, "sha256": sha256(path)}
            )

    def test_build_baseline_reproduces_all_committed_outputs(self):
        with scratch_directory("instruction-architecture-rebuild-") as inside:
            output = Path(inside) / "records"
            reconciliation = Path(inside) / "corpus-reconciliation.md"
            AI.build_baseline(
                mock.Mock(output=output, reconciliation=reconciliation)
            )
            for name in (*AI.BASELINE_RECORD_NAMES, "artifact-inventory.json"):
                self.assertEqual((output / name).read_bytes(), (FIXTURES / name).read_bytes())
            self.assertEqual(
                reconciliation.read_bytes(),
                (ROOT / "docs/instruction-architecture/corpus-reconciliation.md").read_bytes(),
            )

    def test_moved_runtime_and_fixtures_are_excluded(self):
        paths = [item["path"] for item in self.manifest["documents"]]
        self.assertFalse(
            any(path.startswith("distribution/skills-runtime/") for path in paths)
        )
        self.assertFalse(
            any("/fixtures/" in path or path.startswith("tests/") for path in paths)
        )

    def test_external_runtime_ownership_is_explicit(self):
        external = {
            item["path"]
            for item in self.manifest["documents"]
            if item["external_runtime_owner"] == "upstream-pashov"
        }
        self.assertTrue(any(path.endswith("/fizz/SKILL.md") for path in external))
        self.assertTrue(any(path.endswith("/x-ray/SKILL.md") for path in external))
        self.assertTrue(
            any(path.endswith("/solidity-auditor/SKILL.md") for path in external)
        )

    def test_changed_manifest_refuses(self):
        changed = copy.deepcopy(self.manifest)
        changed["totals"]["physical_bytes"] += 1
        self.assertNotEqual(changed, AI.build_manifest(load(PROFILES)))

    def test_live_source_drift_refuses(self):
        clear_source_cache()
        with mock.patch.object(AI, "_read_regular", return_value=b"not the Git blob"):
            with self.assertRaisesRegex(AI.Refusal, "source drift"):
                AI._source_blob("AGENTS.md")
        clear_source_cache()

    def test_cached_git_object_never_skips_live_source_drift_check(self):
        clear_source_cache()
        self.addCleanup(clear_source_cache)
        with (
            mock.patch.object(AI, "_git", return_value=b"pinned"),
            mock.patch.object(
                AI, "_read_regular", side_effect=[b"pinned", b"drifted"]
            ) as live_read,
        ):
            self.assertEqual(AI._source_blob("AGENTS.md"), b"pinned")
            with self.assertRaisesRegex(AI.Refusal, "source drift"):
                AI._source_blob("AGENTS.md")
            self.assertEqual(live_read.call_count, 2)

    def test_git_output_limit_stops_producer_before_completion(self):
        with scratch_directory() as inside:
            root = Path(inside)
            binary = root / "bin"
            binary.mkdir()
            marker = root / "producer-finished"
            fake_git = binary / "git"
            producer = (
                "import os\n"
                "from pathlib import Path\n"
                "import time\n"
                "for _ in range(8):\n"
                "    os.write(1, b'x' * 512)\n"
                "    time.sleep(0.1)\n"
                f"Path({str(marker)!r}).write_text('done')\n"
            )
            fake_git.write_text(
                f"#!{sys.executable}\n"
                "import subprocess\n"
                "import sys\n"
                f"subprocess.Popen([sys.executable, '-c', {producer!r}])\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            environment = {
                "PATH": f"{binary}{os.pathsep}{os.environ.get('PATH', '')}"
            }
            with (
                mock.patch.object(
                    AI,
                    "_git_executable",
                    return_value=str(fake_git.resolve()),
                    create=True,
                ),
                mock.patch.dict(AI.os.environ, environment, clear=False),
            ):
                with self.assertRaisesRegex(AI.Refusal, "output exceeded"):
                    AI._git(["ignored"], limit=1_024)
            time.sleep(1)
            self.assertFalse(marker.exists())

    def test_git_child_is_absolute_closed_and_network_inert(self):
        with scratch_directory() as inside:
            fake_git = Path(inside) / "git"
            fake_git.write_text(
                f"#!{sys.executable}\n"
                "import json\n"
                "import os\n"
                "import sys\n"
                "print(json.dumps({'argv': sys.argv, 'env': dict(os.environ)}, sort_keys=True))\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            spawned: dict[str, str] = {}
            real_popen = AI.subprocess.Popen

            def capture_environment(*arguments, **keywords):
                spawned.update(keywords["env"])
                return real_popen(*arguments, **keywords)

            with (
                mock.patch.object(
                    AI,
                    "_git_executable",
                    return_value=str(fake_git.resolve()),
                    create=True,
                ),
                mock.patch.object(
                    AI.subprocess, "Popen", side_effect=capture_environment
                ),
                mock.patch.dict(
                    AI.os.environ,
                    {
                        "INSTRUCTION_ARCHITECTURE_SECRET": "do-not-copy",
                        "PATH": f"{inside}{os.pathsep}{os.environ.get('PATH', '')}",
                    },
                    clear=False,
                ),
            ):
                observed = json.loads(AI._git(["version"]))
        self.assertEqual(observed["argv"][0], str(fake_git.resolve()))
        self.assertIn("--no-lazy-fetch", observed["argv"])
        expected_environment = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
        self.assertEqual(spawned, expected_environment)
        self.assertEqual(
            {key: observed["env"].get(key) for key in expected_environment},
            expected_environment,
        )
        self.assertNotIn("INSTRUCTION_ARCHITECTURE_SECRET", observed["env"])
        self.assertNotIn("HOME", observed["env"])
        self.assertNotIn("PATH", observed["env"])

    def test_git_executable_ignores_ambient_path(self):
        with scratch_directory() as inside:
            fake_git = Path(inside) / "git"
            fake_git.write_text("not executable by the workbench\n", encoding="utf-8")
            fake_git.chmod(0o755)
            with mock.patch.dict(AI.os.environ, {"PATH": str(inside)}, clear=False):
                resolver = getattr(AI, "_git_executable", lambda: "git")
                executable = Path(resolver())
        self.assertTrue(executable.is_absolute())
        self.assertNotEqual(executable, fake_git)

    def test_nonzero_git_exit_never_signals_a_reaped_process_group(self):
        with mock.patch.object(AI.os, "killpg") as killpg:
            with self.assertRaisesRegex(AI.Refusal, "refused the source"):
                AI._git(["definitely-not-a-git-command"])
        killpg.assert_not_called()

    def test_git_replace_ref_cannot_pivot_the_source_object(self):
        with scratch_directory("instruction-architecture-git-") as inside:
            repository = Path(inside) / "repository"
            repository.mkdir()

            def git(*arguments: str) -> str:
                result = subprocess.run(
                    ["git", "-C", str(repository), *arguments],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "commit.gpgsign", "false")
            source = repository / "source.md"
            source.write_text("original\n", encoding="utf-8")
            git("add", "source.md")
            git("commit", "--quiet", "-m", "original")
            original = git("rev-parse", "HEAD")
            source.write_text("replacement\n", encoding="utf-8")
            git("commit", "--quiet", "-am", "replacement")
            replacement = git("rev-parse", "HEAD")
            git("replace", original, replacement)
            self.assertEqual(
                git("cat-file", "blob", f"{original}:source.md"), "replacement"
            )
            with mock.patch.object(AI, "ROOT", repository):
                self.assertEqual(
                    AI._git(["cat-file", "blob", f"{original}:source.md"]),
                    b"original\n",
                )

    def test_regular_read_refuses_parent_symlink_escape(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            outside_record = Path(outside) / "record.json"
            outside_record.write_text("{}\n", encoding="utf-8")
            escape = Path(inside) / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(
                AI.Refusal, "outside repository|unavailable or unsafe"
            ):
                AI._read_regular(escape / "record.json", AI.MAX_JSON_BYTES)

    def test_regular_read_refuses_concurrent_parent_swap(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            holder = Path(inside)
            outside = Path(outside)
            safe = holder / "safe"
            safe.mkdir()
            target = safe / "record.json"
            target.write_text("inside\n", encoding="utf-8")
            (outside / "record.json").write_text("outside\n", encoding="utf-8")
            original_open = os.open
            swapped = False

            def racing_open(path, flags, *arguments, **keywords):
                nonlocal swapped
                if not swapped and path == "record.json" and "dir_fd" in keywords:
                    swapped = True
                    safe.rename(holder / "safe-old")
                    safe.symlink_to(outside, target_is_directory=True)
                return original_open(path, flags, *arguments, **keywords)

            with mock.patch.object(AI.os, "open", side_effect=racing_open):
                with self.assertRaisesRegex(AI.Refusal, "parent|changed"):
                    AI._read_regular(target, AI.MAX_JSON_BYTES)

    def test_atomic_write_refuses_concurrent_parent_swap_without_escape(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            holder = Path(inside)
            outside = Path(outside)
            safe = holder / "safe"
            safe.mkdir()
            target = safe / "record.json"
            original_replace = os.replace
            swapped = False

            def racing_replace(source, destination, *arguments, **keywords):
                nonlocal swapped
                if not swapped:
                    swapped = True
                    safe.rename(holder / "safe-old")
                    safe.symlink_to(outside, target_is_directory=True)
                    if "src_dir_fd" not in keywords:
                        staged = holder / "safe-old" / Path(source).name
                        staged.rename(outside / Path(source).name)
                return original_replace(source, destination, *arguments, **keywords)

            with mock.patch.object(AI.os, "replace", side_effect=racing_replace):
                with self.assertRaisesRegex(
                    AI.Refusal, "parent|outside repository"
                ):
                    AI._atomic_write(target, b"bounded\n")
            self.assertFalse((outside / "record.json").exists())

    def test_json_depth_and_token_caps_refuse_before_decode(self):
        depth_ceiling = AI.MAX_JSON_DEPTH
        token_ceiling = AI.MAX_JSON_TOKENS
        with scratch_directory() as inside:
            deep = Path(inside) / "deep.json"
            deep.write_bytes(
                b"[" * (depth_ceiling + 1) + b"0" + b"]" * (depth_ceiling + 1)
            )
            with self.assertRaisesRegex(AI.Refusal, "JSON depth limit"):
                AI._load_record(deep)

            wide = Path(inside) / "wide.json"
            wide.write_bytes(
                b'{"items":[' + b"0," * (token_ceiling + 1) + b"0]}\n"
            )
            with self.assertRaisesRegex(AI.Refusal, "JSON token limit"):
                AI._load_record(wide)

    def test_oversized_json_integer_refuses_without_parser_exception(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(b'{"value":' + b"1" * 5_000 + b"}\n")
            try:
                AI._load_record(record)
            except Exception as exc:
                self.assertIsInstance(exc, AI.Refusal)
                self.assertRegex(str(exc), "number length limit|strict UTF-8 JSON")
            else:
                self.fail("oversized JSON integer was accepted")

    def test_integer_bound_does_not_depend_on_the_host_python_limit(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(b'{"value":' + b"1" * 5_000 + b"}\n")
            prior_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0)
                with self.assertRaisesRegex(AI.Refusal, "number length limit"):
                    AI._load_record(record)
            finally:
                sys.set_int_max_str_digits(prior_limit)

    def test_integer_bound_remains_usable_at_the_lowest_host_limit(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(
                b'{"value":' + b"1" * AI.MAX_JSON_NUMBER_CHARS + b"}\n"
            )
            prior_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(sys.int_info.str_digits_check_threshold)
                value, _ = AI._load_record(record)
            finally:
                sys.set_int_max_str_digits(prior_limit)
            self.assertEqual(len(str(value["value"])), AI.MAX_JSON_NUMBER_CHARS)

    def test_non_scalar_json_refuses_without_encoder_exception(self):
        with scratch_directory() as inside:
            record = Path(inside) / "surrogate.json"
            record.write_bytes(b'{"value":"\\ud800"}\n')
            duplicate = Path(inside) / "duplicate-surrogate.json"
            duplicate.write_bytes(b'{"\\ud800":1,"\\ud800":2}\n')
            for specimen in (record, duplicate):
                with self.subTest(specimen=specimen.name):
                    try:
                        AI._load_record(specimen)
                    except AI.Refusal as exc:
                        self.assertTrue(str(exc).isascii())
                    except Exception as exc:
                        self.fail(f"unbounded parser exception: {type(exc).__name__}")
                    else:
                        self.fail("non-scalar JSON was accepted")

    def test_build_baseline_refuses_unowned_output_paths_before_derivation(self):
        manifest = {"source": {"tree_sha256": "0" * 64}, "totals": {}}
        graph = {"roots": [], "edges": []}
        cohorts = {"holdout": {"logical_skills": []}}
        for output, reconciliation in (
            (ROOT, None),
            (FIXTURES, ROOT / "AGENTS.md"),
            (FIXTURES, ROOT / ".git/config"),
        ):
            with self.subTest(output=output, reconciliation=reconciliation):
                arguments = mock.Mock(output=output, reconciliation=reconciliation)
                with (
                    mock.patch.object(AI, "build_manifest", return_value=manifest) as derive,
                    mock.patch.object(AI, "build_loader_graph", return_value=graph),
                    mock.patch.object(AI, "build_partition", return_value={}),
                    mock.patch.object(AI, "build_cohorts", return_value=cohorts),
                    mock.patch.object(AI, "build_holdout_seal", return_value={}),
                    mock.patch.object(AI, "_reconciliation_markdown", return_value=b""),
                    mock.patch.object(AI, "_atomic_write") as write,
                ):
                    try:
                        AI.build_baseline(arguments)
                    except AI.Refusal:
                        refused = True
                    else:
                        refused = False
                self.assertTrue(refused, "unowned output path was accepted")
                derive.assert_not_called()
                write.assert_not_called()

    def test_build_baseline_refuses_output_aliases_before_derivation(self):
        with scratch_directory("instruction-architecture-alias-") as inside:
            output = Path(inside) / "records"
            for reconciliation in (
                output,
                output / "corpus-manifest.json",
                output / "artifact-inventory.json",
                output / "corpus-manifest.json" / "nested.md",
            ):
                with self.subTest(reconciliation=reconciliation):
                    arguments = mock.Mock(
                        output=output,
                        reconciliation=reconciliation,
                    )
                    with mock.patch.object(AI, "build_manifest") as derive:
                        with self.assertRaisesRegex(AI.Refusal, "overlaps"):
                            AI.build_baseline(arguments)
                    derive.assert_not_called()

    def test_output_refuses_parent_symlink_escape_without_writing(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            escape = Path(inside) / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            target = escape / "record.json"
            with self.assertRaisesRegex(
                AI.Refusal, "not a real directory|parent is unavailable or unsafe"
            ):
                AI._safe_output(target)
            self.assertFalse((Path(outside) / "record.json").exists())

    def test_schema_closes_every_object_definition(self):
        schema = load(SCHEMA)
        self.assertEqual(
            {item["$ref"] for item in schema["oneOf"]},
            {
                "#/$defs/artifactInventory",
                "#/$defs/cohorts",
                "#/$defs/holdoutSeal",
                "#/$defs/loaderGraph",
                "#/$defs/manifest",
                "#/$defs/partition",
            },
        )
        object_definitions = [
            value for value in schema["$defs"].values() if value.get("type") == "object"
        ]
        self.assertGreaterEqual(len(object_definitions), 15)
        self.assertTrue(
            all(
                value.get("additionalProperties") is False
                for value in object_definitions
            )
        )

    def test_runtime_and_schema_share_the_canonical_path_language(self):
        schema = load(SCHEMA)["$defs"]["path"]
        pattern = re.compile(schema["pattern"])

        def schema_accepts(value: str) -> bool:
            return (
                schema["minLength"] <= len(value) <= schema["maxLength"]
                and pattern.search(value) is not None
            )

        accepted = ("a", "a b", "a/b", "a" * 1_024)
        refused = (
            "",
            ".",
            "..",
            "a/.",
            "a/..",
            "a//b",
            "a/",
            "/a",
            "a\\b",
            "a\x00b",
            "a\x1fb",
            "a\n",
            "a\r",
            "a\x7fb",
            "é",
            "a" * 1_025,
        )
        for specimen in accepted:
            with self.subTest(accepted=repr(specimen[:32])):
                self.assertEqual(AI._safe_relative(specimen).as_posix(), specimen)
                self.assertTrue(schema_accepts(specimen))
        for specimen in refused:
            with self.subTest(refused=repr(specimen[:32])):
                with self.assertRaises(AI.Refusal):
                    AI._safe_relative(specimen)
                self.assertFalse(schema_accepts(specimen))

    def test_runtime_refuses_a_noncanonical_path_before_normalisation(self):
        with self.assertRaises(AI.Refusal):
            AI._safe_relative("a//b")

    def test_study_copy_changes_only_relative_link_depth(self):
        shipped = STUDY.read_bytes()
        self.assertEqual(shipped.count(b"](../../plugins/"), 10)
        receipted = shipped.replace(b"](../../plugins/", b"](../plugins/")
        self.assertEqual(hashlib.sha256(receipted).hexdigest(), RECEIPTED_STUDY_SHA256)
        self.assertEqual(sha256(RUNBOOK), AMENDED_RUNBOOK_SHA256)


class FollowOnAudit2ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on the exact follow-on-2 parent."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.graph = load(GRAPH)

    def test_source_owned_profile_product_replaces_singleton_witnesses(self):
        self.assertEqual(len(self.graph["scenario_roots"]), 2_595)
        self.assertTrue(
            self.graph["constraints"].get("invocation_profiles_are_source_owned")
        )
        self.assertTrue(
            self.graph["constraints"].get("profile_route_product_is_exact")
        )

    def test_local_version_files_are_fixed_read_only_agent_inputs(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/solidity-auditor/VERSION",
            "plugins/hexaemeron/skills/x-ray/VERSION",
        }
        self.assertLessEqual(expected, set(documents))
        for path in expected:
            self.assertEqual(documents[path]["load_semantics"], "agent-or-prompt")
            incoming = [
                edge
                for edge in self.graph["scenario_edges"]
                if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(all(edge["kind"] == "fixed-agent-input" for edge in incoming))

    def test_human_reference_docs_have_no_production_reachability(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md",
            "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md",
            "plugins/hexaemeron/skills/imprimatur/references/rewriting.md",
            "plugins/pandects/docs/applicability.md",
            "plugins/pandects/docs/writing-a-law.md",
            "plugins/pandects/integrations/wildcat/APPLICABILITY.md",
        }
        for path in expected:
            self.assertEqual(documents[path]["load_semantics"], "reference-only")
            self.assertEqual(documents[path]["loader_roots"], [])
            self.assertEqual(documents[path]["scenario_reachability"], [])


class InvocationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)

    def reseal(self, changed: dict) -> str:
        digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
        changed["projection_sha256"] = digest
        return digest

    def validate_past_projection_oracle(self, changed: dict) -> None:
        digest = self.reseal(changed)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            AI._validate_invocation_profiles(changed)

    def test_profile_ledger_is_exact_and_source_owned(self):
        self.assertEqual(self.profiles, AI.build_invocation_profiles())
        AI._validate_invocation_profiles(self.profiles)
        self.assertEqual(
            self.profiles["projection_sha256"],
            "82a352d00f210ceb91dfae12b9060fbcd284e20739f891e1908625546a7a8814",
        )
        self.assertEqual(self.profiles["counts"], AI.EXPECTED_PROFILE_COUNTS)

    def test_profile_route_denominators_are_exact(self):
        self.assertEqual(
            self.profiles["totals"],
            {
                "normalized_profiles": 519,
                "repository_roots": 1_038,
                "agent_skills_roots": 1_038,
                "standalone_roots": 519,
                "scenario_roots": 2_595,
            },
        )
        self.assertEqual(len(self.graph["scenario_roots"]), 2_595)

    def test_fiat_phase_product_is_not_a_curated_edge_count(self):
        phases: dict[str, int] = {}
        for profile in self.profiles["profiles"]:
            if profile["selected_skill"] == "fiat":
                phases[profile["phase"]] = phases.get(profile["phase"], 0) + 1
        self.assertEqual(
            phases,
            {
                "implement directive": 360,
                "Solidity audit round": 18,
                "non-Solidity audit round": 8,
                "prose directive": 16,
                "study directive": 2,
                "bounded controller operation": 11,
            },
        )

    def test_every_profile_document_union_and_worker_set_is_closed(self):
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                documents = profile["required_documents"]
                workers = profile["worker_prompts"]
                self.assertEqual(documents, sorted(set(documents)))
                self.assertEqual(workers, sorted(set(workers)))
                self.assertLessEqual(set(workers), set(documents))
                self.assertIn(
                    AI.SELECTABLE_SKILL_PATHS[profile["selected_skill"]], documents
                )

    def test_profile_schema_is_closed_at_every_object(self):
        schema = load(PROFILE_SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        objects = [
            value
            for value in schema["$defs"].values()
            if value.get("type") == "object"
        ]
        self.assertGreaterEqual(len(objects), 5)
        self.assertTrue(all(value.get("additionalProperties") is False for value in objects))

    def test_verify_profiles_is_read_only_and_repeatable(self):
        first = command("verify-profiles", "--profiles", str(PROFILES))
        second = command("verify-profiles", "--profiles", str(PROFILES))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_projection_mutation_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["projection_sha256"] = "0" * 64
        with self.assertRaisesRegex(AI.Refusal, "projection digest"):
            AI._validate_invocation_profiles(changed)

    def test_one_profile_omission_refuses_even_when_totals_are_forged(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"].pop()
        with self.assertRaisesRegex(AI.Refusal, "denominator"):
            self.validate_past_projection_oracle(changed)

    def test_duplicate_profile_id_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"][1]["id"] = changed["profiles"][0]["id"]
        with self.assertRaisesRegex(AI.Refusal, "id product"):
            self.validate_past_projection_oracle(changed)

    def test_worker_outside_required_union_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(item for item in changed["profiles"] if item["worker_prompts"])
        profile["required_documents"].remove(profile["worker_prompts"][0])
        with self.assertRaisesRegex(AI.Refusal, "document or worker union"):
            self.validate_past_projection_oracle(changed)

    def test_reference_only_document_in_profile_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = changed["profiles"][0]
        profile["required_documents"].append(sorted(AI.REFERENCE_ONLY_MARKDOWN)[0])
        profile["required_documents"].sort()
        with self.assertRaisesRegex(AI.Refusal, "human reference"):
            self.validate_past_projection_oracle(changed)

    def test_fixed_input_execution_fiction_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item
            for item in changed["profiles"]
            if any(row["path"].endswith("/VERSION") for row in item["fixed_inputs"])
        )
        version = next(
            row for row in profile["fixed_inputs"] if row["path"].endswith("/VERSION")
        )
        version["load_semantics"] = "mandatory-executable"
        with self.assertRaisesRegex(AI.Refusal, "fixed input semantics"):
            self.validate_past_projection_oracle(changed)

    def test_source_span_drift_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"][0]["source_evidence"][0]["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(AI.Refusal, "source span"):
            self.validate_past_projection_oracle(changed)

    def test_missing_bundle_edge_refuses_against_profile_union(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["kind"] == "worker-dispatch"
        )
        removed = edge["active_scenarios"].pop()
        edge["eligible_base_scenarios"] = sorted(
            {
                root["base_scenario"]
                for root in changed["scenario_roots"]
                if root["id"] in edge["active_scenarios"]
            }
        )
        with self.assertRaisesRegex(AI.Refusal, "scenario document union"):
            AI._validate_complete_scenarios(changed, self.profiles)
        self.assertTrue(removed)

    def test_synchronized_route_omission_refuses_5n_oracle(self):
        changed = copy.deepcopy(self.graph)
        profile_id = self.profiles["profiles"][0]["id"]
        removed = {
            root["id"]
            for root in changed["scenario_roots"]
            if root["profile_id"] == profile_id
        }
        changed["scenario_roots"] = [
            root for root in changed["scenario_roots"] if root["id"] not in removed
        ]
        for edge in changed["scenario_edges"]:
            edge["active_scenarios"] = [
                item for item in edge["active_scenarios"] if item not in removed
            ]
            if edge["active_scenarios"]:
                edge["eligible_base_scenarios"] = sorted(
                    {
                        root["base_scenario"]
                        for root in changed["scenario_roots"]
                        if root["id"] in edge["active_scenarios"]
                    }
                )
        changed["scenario_edges"] = [
            edge for edge in changed["scenario_edges"] if edge["active_scenarios"]
        ]
        with self.assertRaisesRegex(AI.Refusal, "denominator|5N"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_bogus_profile_binding_refuses(self):
        changed = copy.deepcopy(self.graph)
        changed["scenario_roots"][0]["profile_id"] = "fiat:invented"
        with self.assertRaisesRegex(AI.Refusal, "5N|unknown profile"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_credential_roster_leak_refuses(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["target"] == "CONTRIBUTORS.md"
        )
        absent = next(
            root["id"]
            for root in changed["scenario_roots"]
            if root["route"] == "repository"
            and root["credential"] == "absent"
            and root["base_scenario"] in edge["eligible_base_scenarios"]
        )
        edge["active_scenarios"].append(absent)
        edge["active_scenarios"].sort()
        with self.assertRaisesRegex(AI.Refusal, "scenario document union"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_reference_only_reachability_refuses(self):
        changed = copy.deepcopy(self.graph)
        target = changed["reference_only"][0]["path"]
        edge = copy.deepcopy(changed["scenario_edges"][0])
        edge["id"] = "scenario-edge-99999"
        edge["target"] = target
        changed["scenario_edges"].append(edge)
        with self.assertRaisesRegex(AI.Refusal, "scenario document union|reference-only"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_fixed_input_edge_kind_mutation_refuses(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["kind"] == "fixed-agent-input"
        )
        edge["kind"] = "mandatory-executable"
        with self.assertRaisesRegex(AI.Refusal, "fixed agent input"):
            AI._validate_complete_scenarios(changed, self.profiles)


class BytePartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.partition = load(PARTITION)
        cls.sources = {item["path"]: item for item in cls.manifest["documents"]}

    def test_every_range_is_ordered_gapless_and_digest_bound(self):
        self.assertEqual(len(self.partition["files"]), 190)
        for file_record in self.partition["files"]:
            source = AI._source_blob(file_record["path"])
            cursor = 0
            for item in file_record["ranges"]:
                self.assertEqual(item["start"], cursor)
                self.assertGreater(item["end"], item["start"])
                self.assertEqual(
                    item["span_sha256"],
                    hashlib.sha256(source[item["start"] : item["end"]]).hexdigest(),
                )
                cursor = item["end"]
            self.assertEqual(cursor, len(source))
            self.assertEqual(
                file_record["source_sha256"],
                self.sources[file_record["path"]]["sha256"],
            )

    def test_partition_totals_reconcile(self):
        self.assertEqual(sum(self.partition["totals"].values()), 2_290_443)
        self.assertEqual(self.partition["unsupported_operative_bytes"], 0)
        self.assertEqual(self.partition["totals"]["generated_duplicate"], 471_444)
        self.assertEqual(
            self.partition["totals"],
            {
                "exact_literal_or_evidence": 345_600,
                "generated_duplicate": 471_444,
                "governed_operative_semantics": 1_473_399,
                "human_only_explanation_or_rationale": 0,
                "unsupported_or_unknown": 0,
            },
        )

    def test_only_generated_promise_copies_use_duplicate_class(self):
        generated = {
            item["path"]
            for item in self.partition["files"]
            if {row["classification"] for row in item["ranges"]}
            == {"generated_duplicate"}
        }
        self.assertEqual(len(generated), 17)
        self.assertNotIn("PROMISE_MACHINE.md", generated)
        self.assertTrue(all(path.endswith("/PROMISE_MACHINE.md") for path in generated))

    def test_structured_references_are_whole_file_exact_evidence(self):
        by_path = {item["path"]: item for item in self.partition["files"]}
        for path, (size, digest) in EXPECTED_STRUCTURED_REFERENCES.items():
            with self.subTest(path=path):
                self.assertEqual(
                    by_path[path]["ranges"],
                    [{
                        "start": 0,
                        "end": size,
                        "classification": "exact_literal_or_evidence",
                        "span_sha256": digest,
                    }],
                )

    def test_nested_fences_remain_exact_literal_evidence(self):
        specimens = {
            "plugins/hexaemeron/skills/fiat/references/push-discipline.md": b"plugin-ci-workflow | filed",
            "plugins/hexaemeron/skills/solidity-auditor/references/report-formatting.md": b"- vulnerable line(s)",
        }
        by_path = {item["path"]: item for item in self.partition["files"]}
        for path, needle in specimens.items():
            source = AI._source_blob(path)
            position = source.index(needle)
            containing = next(
                item
                for item in by_path[path]["ranges"]
                if item["start"] <= position < item["end"]
            )
            self.assertEqual(
                containing["classification"], "exact_literal_or_evidence", path
            )

    def test_shorter_or_mismatched_fence_inside_long_fence_is_literal(self):
        specimens = {
            "shorter-backtick": b"````text\n```\nstill literal\n````\nafter\n",
            "shorter-backtick-info": b"````text\n```python\nstill literal\n````\nafter\n",
            "mismatched-tilde": b"````text\n~~~\nstill literal\n````\nafter\n",
            "mismatched-tilde-info": b"````text\n~~~text\nstill literal\n````\nafter\n",
        }
        for name, source in specimens.items():
            with self.subTest(name=name):
                with mock.patch.object(AI, "_source_blob", return_value=source):
                    try:
                        ranges = AI._partition_ranges(f"{name}.md", generated=False)
                    except AI.Refusal as exc:
                        self.fail(f"valid outer fence was refused: {exc}")
                literal = source.index(b"still literal")
                prose = source.index(b"after")
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= literal < item["end"]
                    ),
                    "exact_literal_or_evidence",
                )
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= prose < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_partition_rebuild_and_command_are_exact(self):
        self.assertEqual(self.partition, AI.build_partition(self.manifest))
        first = command(
            "verify-partition",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        second = command(
            "verify-partition",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_overlap_mutation_refuses(self):
        changed = copy.deepcopy(self.partition)
        changed["files"][0]["ranges"][0]["start"] = 1
        with self.assertRaisesRegex(AI.Refusal, "overlap, gap, or are unordered"):
            AI._validate_partition_closure(changed)


class LoaderGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)
        cls.profile_by_id = {
            item["id"]: item for item in cls.profiles["profiles"]
        }
        cls.root_by_id = {
            item["id"]: item for item in cls.graph["scenario_roots"]
        }
        cls.host_reach = AI._reachability_by_root(
            cls.graph["roots"], cls.graph["edges"], "active_roots"
        )
        cls.scenario_reach = AI._reachability_by_root(
            cls.graph["scenario_roots"],
            cls.graph["scenario_edges"],
            "active_scenarios",
        )

    def test_exact_graph_counts_are_derived_outputs(self):
        self.assertEqual(
            (
                len(self.graph["roots"]),
                len(self.graph["edges"]),
                len(self.graph["scenario_roots"]),
                len(self.graph["scenario_edges"]),
                len(self.graph["reference_only"]),
            ),
            (19, 324, 2_595, 325, 12),
        )

    def test_profile_constraints_are_explicit(self):
        constraints = self.graph["constraints"]
        self.assertTrue(constraints["invocation_profiles_are_source_owned"])
        self.assertTrue(constraints["profile_route_product_is_exact"])
        self.assertTrue(constraints["fixed_agent_inputs_are_not_executed"])

    def test_graph_binds_the_profile_fixture_digest(self):
        self.assertEqual(
            self.graph["invocation_profiles_sha256"],
            hashlib.sha256(PROFILES.read_bytes()).hexdigest(),
        )

    def test_every_graph_evidence_span_binds_frozen_bytes(self):
        relations = [
            *self.graph["roots"],
            *self.graph["edges"],
            *self.graph["scenario_roots"],
            *self.graph["scenario_edges"],
            *self.graph["excluded_links"],
        ]
        for relation in relations:
            AI._validate_source_evidence(relation["evidence"], "test evidence")
        for relation in self.graph["reference_only"]:
            AI._validate_source_evidence(
                relation["source_evidence"], "test reference evidence"
            )

    def test_runtime_evidence_exists_only_for_executable_edges(self):
        for edge in [*self.graph["edges"], *self.graph["scenario_edges"]]:
            with self.subTest(edge=edge["id"]):
                self.assertEqual(
                    edge["runtime_evidence"] is not None,
                    edge["load_type"] == "mandatory-executable",
                )

    def test_host_root_identities_are_exact(self):
        self.assertEqual(
            {item["id"] for item in self.graph["roots"]},
            {"repository", "agent-skills"}
            | {f"standalone:{name}" for name in {
                AI._plugin(path) for path in AI.SELECTABLE_SKILL_PATHS.values()
            }},
        )

    def test_host_edge_scopes_are_closed(self):
        known = {item["id"] for item in self.graph["roots"]}
        for edge in self.graph["edges"]:
            self.assertEqual(edge["active_roots"], sorted(set(edge["active_roots"])))
            self.assertTrue(set(edge["active_roots"]) <= known)
            self.assertNotIn("*", edge["active_roots"])

    def test_manifest_host_reachability_is_graph_derived(self):
        for document in self.manifest["documents"]:
            self.assertEqual(
                set(document["loader_roots"]),
                self.host_reach.get(document["path"], set()),
            )

    def test_manifest_scenario_reachability_is_graph_derived(self):
        for document in self.manifest["documents"]:
            self.assertEqual(
                set(document["scenario_reachability"]),
                self.scenario_reach.get(document["path"], set()),
            )

    def test_scenario_denominator_is_exactly_5n(self):
        self.assertEqual(
            len(self.graph["scenario_roots"]),
            5 * self.profiles["totals"]["normalized_profiles"],
        )

    def test_scenario_route_totals_are_2n_2n_n(self):
        counts = {
            route: sum(root["route"] == route for root in self.graph["scenario_roots"])
            for route in ("repository", "agent-skills", "standalone")
        }
        self.assertEqual(
            counts,
            {"repository": 1_038, "agent-skills": 1_038, "standalone": 519},
        )

    def test_each_profile_has_five_scenario_roots(self):
        counts = {identifier: 0 for identifier in self.profile_by_id}
        for root in self.graph["scenario_roots"]:
            counts[root["profile_id"]] += 1
        self.assertEqual(set(counts.values()), {5})

    def test_route_credential_matrix_is_exact(self):
        for profile_id in self.profile_by_id:
            rows = [
                (root["route"], root["credential"])
                for root in self.graph["scenario_roots"]
                if root["profile_id"] == profile_id
            ]
            self.assertEqual(
                set(rows),
                {
                    ("repository", "absent"),
                    ("repository", "github-contributor"),
                    ("agent-skills", "absent"),
                    ("agent-skills", "github-contributor"),
                    ("standalone", "absent"),
                },
            )

    def test_route_skill_base_product_has_93_members(self):
        self.assertEqual(
            len({root["base_scenario"] for root in self.graph["scenario_roots"]}),
            93,
        )

    def test_root_conditions_bind_profile_and_optional_credential(self):
        for root in self.graph["scenario_roots"]:
            expected = [f"profile:{root['profile_id']}"]
            if root["credential"] == "github-contributor":
                expected.append("credential:github-contributor")
            self.assertEqual(root["conditions"], sorted(expected))
            self.assertEqual(root["mode"], "conditional")

    def test_each_scenario_starts_at_its_real_host_entry(self):
        for root in self.graph["scenario_roots"]:
            plugin = AI._plugin(AI.SELECTABLE_SKILL_PATHS[root["selected_skill"]])
            expected = {
                "repository": "AGENTS.md",
                "agent-skills": ".agents/skills/promise-machine/SKILL.md",
                "standalone": f"plugins/{plugin}/AGENTS.md",
            }[root["route"]]
            self.assertEqual(root["node"], expected)

    def test_each_reached_union_exactly_matches_its_profile_and_route(self):
        for identifier, root in self.root_by_id.items():
            expected = AI._scenario_expected_documents(
                root["route"],
                root["credential"],
                self.profile_by_id[root["profile_id"]],
            )
            observed = {
                path for path, scope in self.scenario_reach.items() if identifier in scope
            }
            self.assertEqual(observed, expected)

    def test_scenario_edge_scopes_are_sorted_closed_and_nonempty(self):
        known = set(self.root_by_id)
        for edge in self.graph["scenario_edges"]:
            scope = edge["active_scenarios"]
            self.assertTrue(scope)
            self.assertEqual(scope, sorted(set(scope)))
            self.assertNotIn("*", scope)
            self.assertTrue(set(scope) <= known)

    def test_edge_base_scopes_are_derived_from_active_roots(self):
        for edge in self.graph["scenario_edges"]:
            self.assertEqual(
                edge["eligible_base_scenarios"],
                sorted(
                    {
                        self.root_by_id[identifier]["base_scenario"]
                        for identifier in edge["active_scenarios"]
                    }
                ),
            )

    def test_every_scenario_edge_has_a_realisable_witness(self):
        for edge in self.graph["scenario_edges"]:
            for identifier in edge["active_scenarios"]:
                self.assertIn(identifier, self.scenario_reach[edge["source"]])
                self.assertIn(identifier, self.scenario_reach[edge["target"]])

    def test_profile_scopes_replace_edge_minimised_conditions(self):
        self.assertTrue(
            all(edge["condition"] is None for edge in self.graph["scenario_edges"])
        )
        self.assertTrue(
            all(root["conditions"][0].startswith(("credential:", "profile:")) for root in self.graph["scenario_roots"])
        )

    def test_reference_only_ledger_is_exact(self):
        expected = {
            path
            for path, row in AI._structured_metadata().items()
            if row["load_semantics"] == "reference-only"
        } | set(AI.REFERENCE_ONLY_MARKDOWN)
        self.assertEqual({row["path"] for row in self.graph["reference_only"]}, expected)

    def test_reference_only_documents_have_zero_reachability(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        for row in self.graph["reference_only"]:
            document = documents[row["path"]]
            self.assertEqual(document["loader_roots"], [])
            self.assertEqual(document["scenario_reachability"], [])

    def test_fixed_agent_inputs_have_nonexecuting_edges(self):
        for path in AI._fixed_agent_metadata():
            incoming = [
                edge for edge in self.graph["scenario_edges"] if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(
                all(
                    edge["kind"] == "fixed-agent-input"
                    and edge["load_type"] == "agent-or-prompt"
                    and edge["runtime_evidence"] is None
                    for edge in incoming
                )
            )

    def test_fixed_input_scopes_equal_profile_declarations(self):
        for path in AI._fixed_agent_metadata():
            expected = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if path in self.profile_by_id[root["profile_id"]]["required_documents"]
            }
            self.assertEqual(self.scenario_reach[path], expected)

    def test_mandatory_inputs_keep_executable_semantics(self):
        for path, metadata in AI._structured_metadata().items():
            if metadata["load_semantics"] != "mandatory-executable":
                continue
            incoming = [
                edge for edge in self.graph["scenario_edges"] if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(
                all(
                    edge["kind"] == "mandatory-executable"
                    and edge["runtime_evidence"] is not None
                    for edge in incoming
                )
            )

    def test_mandatory_input_scopes_equal_profile_declarations(self):
        for path, metadata in AI._structured_metadata().items():
            if metadata["load_semantics"] != "mandatory-executable":
                continue
            expected = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if path in self.profile_by_id[root["profile_id"]]["required_documents"]
            }
            self.assertEqual(self.scenario_reach[path], expected)

    def test_synkrisis_rule_runtime_has_two_exclusive_operation_spans(self):
        path = "plugins/synkrisis/references/rules-v1.json"
        spans = {
            edge["runtime_evidence"]["span_sha256"]
            for edge in self.graph["scenario_edges"]
            if edge["target"] == path
        }
        expected = {
            AI._evidence(
                AI._structured_metadata()[path]["runtime_path"], needle
            )["span_sha256"]
            for needle in AI.SYNKRISIS_RULE_RUNTIME_NEEDLES.values()
        }
        self.assertEqual(spans, expected)

    def test_every_declared_worker_is_reached_in_all_five_routes(self):
        for profile in self.profiles["profiles"]:
            roots = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if root["profile_id"] == profile["id"]
            }
            for worker in profile["worker_prompts"]:
                self.assertLessEqual(roots, self.scenario_reach[worker])

    def test_kronos_is_bounded_to_one_rank_or_one_dispatch_iteration(self):
        profiles = [
            row for row in self.profiles["profiles"] if row["selected_skill"] == "kronos"
        ]
        self.assertEqual(len(profiles), 26)
        self.assertEqual(sum("rank-only" in row["id"] for row in profiles), 2)
        self.assertTrue(
            all("rank-only" in row["id"] or "dispatch-" in row["id"] for row in profiles)
        )

    def test_graph_rebuild_is_exact(self):
        self.assertEqual(
            self.graph,
            AI.build_loader_graph(self.manifest, self.profiles),
        )

    def test_verify_loader_is_read_only_and_repeatable(self):
        arguments = (
            "verify-loader",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--graph",
            str(GRAPH),
        )
        first = command(*arguments)
        second = command(*arguments)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


class HoldoutSealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.cohorts = load(COHORTS)
        cls.seal = load(SEAL)

    def test_cohorts_are_disjoint_and_meet_byte_gates(self):
        development = set(self.cohorts["development"]["paths"])
        holdout = set(self.cohorts["holdout"]["paths"])
        self.assertFalse(development & holdout)
        self.assertGreaterEqual(
            float(self.cohorts["development"]["unique_byte_ratio"]), 0.50
        )
        self.assertGreaterEqual(
            float(self.cohorts["holdout"]["unique_byte_ratio"]), 0.20
        )
        self.assertGreaterEqual(len(self.cohorts["development"]["logical_skills"]), 12)
        self.assertEqual(
            self.cohorts["holdout"]["logical_skills"],
            ["alexandria", "fizz", "phylax", "probitas", "sapheneia"],
        )
        self.assertEqual(len(self.cohorts["holdout"]["paths"]), 31)
        self.assertEqual(self.cohorts["holdout"]["unique_bytes"], 363_804)
        self.assertEqual(self.cohorts["holdout"]["unique_byte_ratio"], "0.200002")
        self.assertEqual(self.cohorts["development"]["unique_bytes"], 1_455_195)
        self.assertEqual(
            self.cohorts["development"]["unique_byte_ratio"], "0.799998"
        )
        self.assertEqual(self.cohorts["selection"]["seed"], AI.SELECTION_SEED)

    def test_development_covers_roots_tiers_constructs_and_deciles(self):
        development = set(self.cohorts["development"]["paths"])
        self.assertIn("AGENTS.md", development)
        self.assertIn("PROMISE_MACHINE.md", development)
        self.assertIn(".agents/skills/promise-machine/SKILL.md", development)
        self.assertEqual(self.cohorts["development"]["size_deciles"], list(range(10)))
        self.assertEqual(
            set(self.cohorts["development"]["constructs"]),
            {
                "authority",
                "cross-document",
                "exact-literal",
                "exception",
                "failure",
                "negation",
                "order",
                "recovery",
                "refusal",
                "scope",
                "unknown",
            },
        )
        self.assertEqual(
            set(self.cohorts["development"]["authority_tiers"]),
            {
                item["authority_tier"]
                for item in self.manifest["documents"]
                if item["path"] == item["canonical_content_path"]
            },
        )
        self.assertEqual(
            set(self.cohorts["development"]["document_classes"]),
            set(AI.EXPECTED_COUNTS),
        )

    def test_sealed_envelope_has_required_classes_without_answers(self):
        envelope = self.seal["closed_future_case_envelope"]
        self.assertEqual(len(envelope["slots"]), 16)
        self.assertEqual(
            {slot["semantic_class"] for slot in envelope["slots"]},
            {"authority", "failure", "recovery", "exact-literal", "cross-document"},
        )
        forbidden = set(envelope["forbidden_until_open"])
        self.assertEqual(
            forbidden, {"prompt", "expected_answer", "scorer_key", "model_output"}
        )
        self.assertTrue(all(not forbidden & set(slot) for slot in envelope["slots"]))
        self.assertIs(self.seal["opened"], False)

    def test_commitments_recompute(self):
        membership = self.seal["membership"]
        envelope = self.seal["closed_future_case_envelope"]
        self.assertEqual(
            self.seal["membership_sha256"],
            hashlib.sha256(canonical(membership)).hexdigest(),
        )
        self.assertEqual(
            self.seal["case_envelope_sha256"],
            hashlib.sha256(canonical(envelope)).hexdigest(),
        )
        body = dict(self.seal)
        commitment = body.pop("commitment_sha256")
        self.assertEqual(commitment, hashlib.sha256(canonical(body)).hexdigest())

    def test_seed_replay_and_command_are_exact(self):
        rebuilt = AI.build_cohorts(self.manifest)
        self.assertEqual(rebuilt, self.cohorts)
        self.assertEqual(AI.build_holdout_seal(self.manifest, rebuilt), self.seal)
        first = command(
            "verify-seal",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        second = command(
            "verify-seal",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
