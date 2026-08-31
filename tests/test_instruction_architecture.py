"""Step 1 guards for the framework-74 research boundary."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
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
GRAPH = FIXTURES / "loader-graph.json"
PARTITION = FIXTURES / "byte-partition.json"
COHORTS = FIXTURES / "cohorts.json"
SEAL = FIXTURES / "holdout-seal.json"
INVENTORY = FIXTURES / "artifact-inventory.json"
SCHEMA = ROOT / "research/instruction-architecture/schemas/source-bound-v1.schema.json"
STUDY = ROOT / "docs/instruction-architecture/study.md"
RUNBOOK = ROOT / "docs/instruction-architecture/runbook.md"
RECEIPTED_STUDY_SHA256 = (
    "9edd0a06ae72dd1b9108ee47c0514ae70edc577e0d62a0603585a99455d96e7d"
)
AMENDED_RUNBOOK_SHA256 = (
    "9c6144a1b819b6ce04289722836a38d694770a10638af59afd6d147970e635f9"
)


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
        timeout=30,
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
        self.assertEqual(len(admissions), 69)
        self.assertEqual(
            {
                item["path"]
                for item in self.manifest["documents"]
                if item["admission_kind"] != "issue-census"
            },
            set(admissions),
        )
        self.assertEqual(sum(documents[path]["bytes"] for path in admissions), 523_721)
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
                "operation_reference": 24,
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
        self.assertEqual(self.manifest, AI.build_manifest())
        first = command("verify-corpus", "--manifest", str(MANIFEST))
        second = command("verify-corpus", "--manifest", str(MANIFEST))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_artifact_inventory_binds_every_baseline_record(self):
        inventory = load(INVENTORY)
        expected = {
            "corpus-manifest.json",
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
        self.assertNotEqual(changed, AI.build_manifest())

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
                "Path(os.environ['INSTRUCTION_ARCHITECTURE_TEST_MARKER']).write_text('done')\n"
            )
            fake_git.write_text(
                "#!/usr/bin/env python3\n"
                "import subprocess\n"
                "import sys\n"
                f"subprocess.Popen([sys.executable, '-c', {producer!r}])\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            environment = {
                "PATH": f"{binary}{os.pathsep}{os.environ.get('PATH', '')}",
                "INSTRUCTION_ARCHITECTURE_TEST_MARKER": str(marker),
            }
            with mock.patch.dict(AI.os.environ, environment, clear=False):
                with self.assertRaisesRegex(AI.Refusal, "output exceeded"):
                    AI._git(["ignored"], limit=1_024)
            time.sleep(1)
            self.assertFalse(marker.exists())

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
        depth_ceiling = 64
        token_ceiling = 100_000
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

    def test_study_copy_changes_only_relative_link_depth(self):
        shipped = STUDY.read_bytes()
        self.assertEqual(shipped.count(b"](../../plugins/"), 10)
        receipted = shipped.replace(b"](../../plugins/", b"](../plugins/")
        self.assertEqual(hashlib.sha256(receipted).hexdigest(), RECEIPTED_STUDY_SHA256)
        self.assertEqual(sha256(RUNBOOK), AMENDED_RUNBOOK_SHA256)


class BytePartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.partition = load(PARTITION)
        cls.sources = {item["path"]: item for item in cls.manifest["documents"]}

    def test_every_range_is_ordered_gapless_and_digest_bound(self):
        self.assertEqual(len(self.partition["files"]), 175)
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
        self.assertEqual(sum(self.partition["totals"].values()), 2_069_258)
        self.assertEqual(self.partition["unsupported_operative_bytes"], 0)
        self.assertEqual(self.partition["totals"]["generated_duplicate"], 471_444)

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
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        second = command(
            "verify-partition",
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
        cls.graph = load(GRAPH)

    def test_roots_and_edges_are_source_span_bound(self):
        self.assertEqual(len(self.graph["roots"]), 19)
        self.assertEqual(len(self.graph["edges"]), 205)
        self.assertEqual(len(self.graph["scenario_roots"]), 50)
        self.assertEqual(len(self.graph["scenario_edges"]), 193)
        for relation in [
            *self.graph["roots"],
            *self.graph["edges"],
            *self.graph["scenario_roots"],
            *self.graph["scenario_edges"],
            *self.graph["excluded_links"],
        ]:
            evidence = relation["evidence"]
            source = AI._source_blob(evidence["path"])
            self.assertEqual(
                hashlib.sha256(source).hexdigest(), evidence["source_sha256"]
            )
            self.assertEqual(
                hashlib.sha256(source[evidence["start"] : evidence["end"]]).hexdigest(),
                evidence["span_sha256"],
            )

    def test_installed_router_path_is_agent_skills_only(self):
        router = ".agents/skills/promise-machine/SKILL.md"
        portable = ".agents/skills/promise-machine/PORTABLE.md"
        edges = {
            (item["source"], item["target"]): item for item in self.graph["edges"]
        }
        self.assertEqual(edges[(router, portable)]["kind"], "installed-route")
        self.assertEqual(edges[(router, portable)]["active_roots"], ["agent-skills"])
        for target in ("AGENTS.md", "PROMISE_MACHINE.md", "SHOGGOTH.md"):
            self.assertEqual(
                edges[(portable, target)]["active_roots"], ["agent-skills"]
            )
        portable_record = next(
            item for item in self.manifest["documents"] if item["path"] == portable
        )
        self.assertEqual(portable_record["loader_roots"], ["agent-skills"])
        promise = next(
            item
            for item in self.manifest["documents"]
            if item["path"] == "PROMISE_MACHINE.md"
        )
        self.assertEqual(promise["loader_roots"], ["agent-skills", "repository"])

    def test_manifest_loader_roots_equal_graph_reachability(self):
        observed = AI._reachability_by_root(
            self.graph["roots"], self.graph["edges"], "active_roots"
        )
        for item in self.manifest["documents"]:
            self.assertEqual(set(item["loader_roots"]), observed[item["path"]])

    def test_manifest_scenarios_equal_graph_reachability(self):
        observed = AI._reachability_by_root(
            self.graph["scenario_roots"],
            self.graph["scenario_edges"],
            "active_scenarios",
        )
        for item in self.manifest["documents"]:
            self.assertEqual(
                set(item["scenario_reachability"]), observed[item["path"]]
            )

    def test_graph_refuses_fabricated_manifest_reachability(self):
        for field, message in (
            ("loader_roots", "loader roots disagree"),
            ("scenario_reachability", "scenario reachability disagrees"),
        ):
            changed = copy.deepcopy(self.manifest)
            changed["documents"][0][field].append("fabricated")
            with self.subTest(field=field):
                with self.assertRaisesRegex(AI.Refusal, message):
                    AI.build_loader_graph(changed)

    def test_every_reference_has_a_conditional_inbound_edge(self):
        references = {
            item["path"]
            for item in self.manifest["documents"]
            if item["document_class"] == "markdown_reference"
        }
        inbound = {
            item["target"]
            for item in self.graph["edges"]
            if item["kind"] == "conditional"
        }
        self.assertLessEqual(references, inbound)

    def test_all_69_admissions_have_exact_inbound_source_edges(self):
        edges = {
            (item["source"], item["target"]): item for item in self.graph["edges"]
        }
        for path, metadata in AI._additional_metadata().items():
            with self.subTest(path=path):
                edge = edges[(metadata["source_path"], path)]
                self.assertEqual(edge["kind"], metadata["edge_kind"])
                self.assertEqual(
                    edge["evidence"],
                    AI._evidence(metadata["source_path"], metadata["source_needle"]),
                )

    def test_recursive_frontier_and_workflow_closure_is_explicit(self):
        host_pairs = {
            (item["source"], item["target"]) for item in self.graph["edges"]
        }
        policy = "plugins/hexaemeron/skills/VERSIONING.md"
        for prefix in AI.FRONTIER_SKILLS:
            self.assertIn((f"{prefix}/EVOLUTION.md", policy), host_pairs)
        scenario_pairs = {
            (item["source"], item["target"])
            for item in self.graph["scenario_edges"]
        }
        fiat = "plugins/hexaemeron/skills/fiat/SKILL.md"
        fizz = "plugins/hexaemeron/skills/fizz/SKILL.md"
        kronos = "plugins/hexaemeron/skills/kronos/SKILL.md"
        xray = "plugins/hexaemeron/skills/x-ray/SKILL.md"
        self.assertIn((fiat, xray), scenario_pairs)
        self.assertIn((fizz, xray), scenario_pairs)
        self.assertIn((kronos, fiat), scenario_pairs)
        for path in AI.FIAT_WORKER_PROMPTS:
            self.assertIn((fiat, path), scenario_pairs)

    def test_excluded_link_classes_never_become_targets(self):
        excluded = {item["path"] for item in self.graph["excluded_links"]}
        self.assertEqual(
            {item[0] for item in AI.EXCLUDED_LINK_CLASSES},
            {item["class"] for item in self.graph["excluded_links"]},
        )
        targets = {
            item["target"]
            for item in [*self.graph["edges"], *self.graph["scenario_edges"]]
        }
        self.assertFalse(excluded & targets)

    def test_actual_loader_separates_unconditional_and_conditional_edges(self):
        kinds = {item["kind"] for item in self.graph["edges"]}
        self.assertEqual(
            kinds,
            {
                "conditional",
                "credential-identity",
                "frontier-gate",
                "installed-route",
                "operation-branch",
                "unconditional",
                "vendored-overlay",
                "worker-dispatch",
            },
        )
        self.assertFalse(self.graph["constraints"]["file_presence_creates_edge"])
        self.assertTrue(self.graph["constraints"]["fixtures_excluded"])
        self.assertTrue(self.graph["constraints"]["skills_runtime_excluded"])

    def test_graph_rebuild_and_command_are_exact(self):
        self.assertEqual(self.graph, AI.build_loader_graph(self.manifest))
        first = command(
            "verify-loader", "--manifest", str(MANIFEST), "--graph", str(GRAPH)
        )
        second = command(
            "verify-loader", "--manifest", str(MANIFEST), "--graph", str(GRAPH)
        )
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
        self.assertEqual(len(self.cohorts["holdout"]["logical_skills"]), 5)

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
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        second = command(
            "verify-seal",
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
