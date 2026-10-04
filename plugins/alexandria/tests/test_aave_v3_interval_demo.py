"""The preserved Aave V3 Ethereum segments: committed metadata and the offline path.

`PreservedArtefactsTests` and `OfflineDemoTests` are loaded by name: the Aave
conformance harness resolves `production-segments-preserved-and-rebuilt` and
`aave-fixture-rebuilds-offline-without-sockets` against them.

The segment staging trees are held outside this repository and reached only
through `ALEXANDRIA_AAVE_V3_STAGING`. `PreservedArtefactsTests` needs none of
them: it checks the one committed staging manifest, every committed segment's
rebuild record and its expected values against the pinned segment table, and fails rather than skips
on a missing or disagreeing file. A segment with no committed directory is
counted as not yet preserved and reported by index; nothing here treats it as
passing. `StagedRebuildTests` needs the unpacked trees and reports their
absence by name through `skipTest`. `OfflineDemoTests` runs the same rebuild
path over the Step 4 constructed fixture, collected in process from the
fixture transport, so it needs no external tree and opens no socket.
"""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import urllib.parse


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "aave-v3-interval-v0"
MODULE_NAME = "aave_v3_interval_demo"
STAGING_ENV_VAR = "ALEXANDRIA_AAVE_V3_STAGING"
REQUIRED = ("demo.py", "README.md", "segments.json", "registry.json", "staging-manifest.json")
SEGMENT_FILES = ("staging-manifest.json", "rebuild-record.json", "expected.json")
# What each segment directory holds; the manifest is one file for the whole archive.
SEGMENT_DIRECTORY_FILES = ("expected.json", "rebuild-record.json")
CEILING = 67_108_864

sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.venues import aave_v3  # noqa: E402
from usdc_interval import Collector, Reconciler  # noqa: E402

from tests import test_aave_v3_collector as collector  # noqa: E402


def demo():
    """Import the demonstration, failing rather than skipping when it is absent."""
    missing = [name for name in REQUIRED if not (EXAMPLE / name).is_file()]
    if missing:
        raise AssertionError(
            f"the aave-v3-interval-v0 example is missing {', '.join(missing)} at {EXAMPLE}; "
            "this suite is the proof it is complete and must fail rather than skip"
        )
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    spec = importlib.util.spec_from_file_location(MODULE_NAME, EXAMPLE / "demo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class DemoTestCase(unittest.TestCase):
    def setUp(self):
        self.module = demo()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.table = load(EXAMPLE / "segments.json")
        self.rows = {row["index"]: row for row in self.table["segments"]}
        self.committed = sorted(
            int(path.name) for path in (EXAMPLE / "segments").iterdir()
            if path.is_dir() and path.name.isdigit()
        )
        self.document = load(EXAMPLE / "staging-manifest.json")
        sections = {section["segment"]: section for section in self.document["segments"]}
        self.segments = {
            index: {
                "staging-manifest.json": {"archive": self.document["archive"], "segment": index,
                                          **sections[index]},
                **{name: load(EXAMPLE / "segments" / str(index) / name) for name in SEGMENT_DIRECTORY_FILES},
            }
            for index in self.committed
        }

    def copied_segments(self):
        """A private copy of the committed manifest and segment metadata a case may edit."""
        target = self.root / "segments"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(EXAMPLE / "segments", target,
                        ignore=shutil.ignore_patterns("__pycache__"))
        manifest = self.root / "staging-manifest.json"
        if not manifest.exists():
            manifest.write_bytes((EXAMPLE / "staging-manifest.json").read_bytes())
        for name, value in (("SEGMENTS", target), ("MANIFEST", manifest)):
            if getattr(self.module, name) != value:
                patcher = mock.patch.object(self.module, name, value)
                patcher.start()
                self.addCleanup(patcher.stop)
        return target

    def rewrite(self, index, name, edit):
        target = self.copied_segments()
        if name == "staging-manifest.json":
            path = self.root / name
            document = load(path)
            edit(next(section for section in document["segments"] if section["segment"] == index))
            path.write_text(json.dumps(document), encoding="utf-8")
            return
        path = target / str(index) / name
        value = load(path)
        edit(value)
        path.write_text(json.dumps(value), encoding="utf-8")


class PreservedArtefactsTests(DemoTestCase):
    """Needs no staging tree. Fails -- never skips -- on a bad manifest, record or pin.

    Each case checks every committed segment. Until all twelve are committed,
    the uncommitted ones are counted by `verify_preserved` and named by
    `test_every_uncommitted_segment_is_reported_as_not_preserved`.
    """

    def test_verify_preserved_passes_against_the_committed_artefacts(self):
        result = self.module.verify_preserved()
        self.assertIs(result["rebuild_performed"], False)
        self.assertEqual(result["scope"], "committed-metadata-only")
        self.assertEqual(result["segments_in_table"], len(aave_v3.SEGMENT_PLAN_SHA256))
        self.assertEqual(self.committed, list(range(len(aave_v3.SEGMENT_PLAN_SHA256))))
        self.assertEqual(result["segments_without_rebuild_record"], [])
        self.assertEqual(result["archive"], {"bytes": self.document["archive"]["bytes"],
                                             "sha256": self.document["archive"]["sha256"]})
        self.assertEqual(result["segments_with_rebuild_record"], len(self.committed))
        self.assertEqual(sorted(int(index) for index in result["segments"]), self.committed)
        for index in self.committed:
            expected = self.segments[index]["expected.json"]
            manifest = self.segments[index]["staging-manifest.json"]
            self.assertEqual(result["segments"][str(index)], {
                "archive_sha256": manifest["archive"]["sha256"],
                "epochs": expected["epochs"],
                "reconciliation": expected["reconciliation"],
                "release_id": expected["release_id"],
                "shards": self.rows[index]["shards"],
            })

    def test_every_segment_rebuild_record_agrees_with_its_pin(self):
        for index in self.committed:
            with self.subTest(segment=index):
                files = self.segments[index]
                manifest, record, expected = (files[name] for name in SEGMENT_FILES)
                pin = aave_v3.SEGMENT_PLAN_SHA256[index]
                self.assertEqual(self.rows[index]["plan_sha256"], pin)
                plan_bytes = (EXAMPLE / self.rows[index]["plan"]).read_bytes()
                self.assertEqual(hashlib.sha256(plan_bytes).hexdigest(), pin)
                self.assertEqual(record["plan_sha256"], pin)
                self.assertEqual(expected["plan_sha256"], pin)
                self.assertEqual(record["archive_sha256"], manifest["archive"]["sha256"])
                for field in self.module.PRESERVED_COMPARED:
                    self.assertEqual(record["checked"][field], expected[field], field)
                self.assertEqual(expected["reconciliation"], "agreed")
                self.assertEqual(record["rebuilt_release_id"], expected["release_id"])
                self.assertIs(record["release_matches_collected"], True)
                self.assertIs(record["fresh_extraction"]["all_match"], True)
                self.assertEqual(record["fresh_extraction"]["files"], manifest["staging_files_total"])
                self.assertEqual(record["fresh_extraction"]["bytes"], manifest["staging_bytes_total"])
                commands = {command["label"]: command for command in record["commands"]}
                self.assertEqual(sorted(commands), ["build", "check", "verify"])
                for command in commands.values():
                    self.assertEqual(command["exit"], 0)
                    self.assertEqual(command["socket_refusals"], 0)
                    self.assertIn("socket.__new__", command["socket_policy"])
                walk = record["credential_walk_before_archive"]
                self.assertEqual(walk["files"], manifest["staging_files_total"])
                self.assertEqual(walk["bytes"], manifest["staging_bytes_total"])
                self.assertEqual(set(walk["matching_file_counts"].values()), {0})
                for name in ("credential_file_1_url", "credential_file_1_bearer", "primary_loopback_url"):
                    self.assertIn(name, walk["matching_file_counts"])

    def test_every_segment_counts_every_shard_and_class(self):
        for index in self.committed:
            with self.subTest(segment=index):
                row = self.rows[index]
                expected = self.segments[index]["expected.json"]
                manifest = self.segments[index]["staging-manifest.json"]
                self.assertEqual(sum(expected["shard_statuses"].values()), row["shards"])
                self.assertEqual(expected["interval"], {"end": str(row["end"]), "start": str(row["start"])})
                classes = expected["classes"]
                for name in self.module.RANGE_CLASSES:
                    self.assertEqual(classes[name]["parts"], row["ranges"], name)
                    self.assertEqual(sum(classes[name]["statuses"].values()), row["ranges"], name)
                for name in self.module.SHARD_CLASSES:
                    self.assertEqual(classes[name]["record_count"], row["shards"], name)
                for name in ("epoch-evidence", "epoch-table", "implementation-code", "interval-plan",
                             "reconciliation", "registry", "error-receipts"):
                    self.assertEqual(classes[name]["parts"], 1, name)
                self.assertEqual(classes["interval-plan"]["record_count"], row["shards"])
                self.assertEqual(classes["reconciliation"]["record_count"], row["shards"])
                self.assertEqual(expected["components"]["count"], row["components"])
                self.assertLessEqual(expected["components"]["largest_bytes"], CEILING)
                journals = [entry["bytes"] for entry in manifest["files"] if entry["path"].startswith("journals/")]
                self.assertEqual(len(journals), 3 * row["ranges"] + 1)
                self.assertLessEqual(max(journals), CEILING)
                self.assertIs(expected["constructed_staging_gap"], False)

    def test_one_manifest_binds_the_archive_and_every_segment(self):
        self.assertEqual(self.document["format"], self.module.MANIFEST_FORMAT)
        self.assertEqual([section["segment"] for section in self.document["segments"]],
                         list(range(len(aave_v3.SEGMENT_PLAN_SHA256))))
        self.assertEqual(set(self.document), {"archive", "format", "segments"})
        for index in self.committed:
            with self.subTest(segment=index):
                directory = EXAMPLE / "segments" / str(index)
                self.assertEqual(sorted(path.name for path in directory.iterdir()),
                                 list(SEGMENT_DIRECTORY_FILES))
                self.assertEqual(self.segments[index]["rebuild-record.json"]["archive_sha256"],
                                 self.document["archive"]["sha256"])
                self.assertEqual(self.segments[index]["rebuild-record.json"]["archive_bytes"],
                                 self.document["archive"]["bytes"])

    def test_the_manifest_lists_only_the_staging_layout_and_no_captured_bytes(self):
        allowed = ("checkpoint.json", "journals/", "receipts/", "reconciliation/")
        for section in self.document["segments"]:
            with self.subTest(segment=section["segment"]):
                self.assertEqual(set(section), {"segment", "staging_bytes_total",
                                                "staging_files_total", "files"})
                for entry in section["files"]:
                    self.assertEqual(set(entry), {"bytes", "path", "sha256"})
                    self.assertTrue(entry["path"].startswith(allowed), entry["path"])
        listed = sum(section["staging_files_total"] for section in self.document["segments"])
        self.assertEqual(listed, sum(
            self.segments[index]["rebuild-record.json"]["fresh_extraction"]["files"]
            for index in self.committed))

    def test_every_uncommitted_segment_is_reported_as_not_preserved(self):
        result = self.module.verify_preserved()
        pending = [index for index in sorted(self.rows) if index not in self.committed]
        self.assertEqual(result["segments_without_rebuild_record"], pending)
        self.assertEqual(result["segments_with_rebuild_record"] + len(pending), len(self.rows))

    def test_each_segment_records_collect_and_reconcile_beside_its_planned_bytes(self):
        for index in self.committed:
            with self.subTest(segment=index):
                measured = self.segments[index]["rebuild-record.json"]["measurements"]
                row = self.rows[index]
                self.assertEqual(measured["planned"]["release_bytes"], row["release_bytes"])
                self.assertEqual(measured["planned"]["shards"], row["shards"])
                for stage in ("collect", "reconcile"):
                    stage_record = measured[stage]
                    self.assertIsInstance(stage_record["elapsed_seconds"], int)
                    self.assertGreater(stage_record["elapsed_seconds"], 0)
                    self.assertEqual(stage_record["elapsed_seconds"], sum(
                        run["elapsed_seconds"] for run in stage_record["invocations"]))
                    self.assertEqual(stage_record["invocations"][-1]["exit"], 0)
                built = self.segments[index]["expected.json"]["components"]["bytes"]
                self.assertEqual(measured["built"]["release_bytes"], built)
                self.assertIsInstance(measured["overruns"], list)

    def test_no_committed_file_names_an_endpoint_host_header_or_bearer(self):
        forbidden = ["://", "authorization", "bearer ", "127.0.0.1", "localhost", ".invalid"]
        for name in ("ALEXANDRIA_COMPOUND_RPC_URL", "ALEXANDRIA_RPC_BEARER"):
            value = os.environ.get(name)
            if value:
                forbidden.append(value.lower())
                host = urllib.parse.urlsplit(value).hostname
                if host:
                    forbidden.append(host.lower())
        paths = [EXAMPLE / "README.md", EXAMPLE / "demo.py", EXAMPLE / "staging-manifest.json"] + [
            EXAMPLE / "segments" / str(index) / name
            for index in self.committed for name in SEGMENT_DIRECTORY_FILES
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8").lower()
            if path.suffix == ".py" or path.name == "README.md":
                text = text.replace("authorization header", "")
            for needle in forbidden:
                with self.subTest(path=path.name, needle="<value>" if needle.startswith(("http", "0x")) else needle):
                    self.assertNotIn(needle, text)

    def test_the_command_line_runs_verify_preserved(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "verify-preserved"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        printed = json.loads(result.stdout)
        self.assertIs(printed["rebuild_performed"], False)
        for index in self.committed:
            self.assertIn(self.segments[index]["expected.json"]["release_id"], result.stdout)

    def test_verify_preserved_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.module.verify_preserved()

    def test_a_missing_segment_file_fails_not_skips(self):
        index = self.committed[0]
        for name, message in (("staging-manifest.json", "staging manifest is missing"),
                              ("rebuild-record.json", "rebuild record is missing"),
                              ("expected.json", "pinned expectation is missing")):
            with self.subTest(name=name):
                target = self.copied_segments()
                (self.root / name if name == "staging-manifest.json" else target / str(index) / name).unlink()
                with self.assertRaisesRegex(AlexandriaError, message):
                    self.module.verify_preserved()

    def test_a_record_binding_a_different_archive_fails(self):
        self.rewrite(self.committed[0], "rebuild-record.json",
                     lambda value: value.update(archive_sha256="0" * 64))
        with self.assertRaisesRegex(AlexandriaError, "different archive"):
            self.module.verify_preserved()

    def test_a_record_that_disagrees_with_expected_fails(self):
        self.rewrite(self.committed[0], "rebuild-record.json",
                     lambda value: value["checked"].update(epochs=value["checked"]["epochs"] + 1))
        with self.assertRaisesRegex(AlexandriaError, "epochs"):
            self.module.verify_preserved()

    def test_an_expectation_missing_a_shard_fails(self):
        def drop(value):
            status = sorted(value["shard_statuses"])[0]
            value["shard_statuses"][status] -= 1
        self.rewrite(self.committed[0], "expected.json", drop)
        with self.assertRaisesRegex(AlexandriaError, "every planned shard"):
            self.module.verify_preserved()

    def test_a_manifest_whose_file_sizes_do_not_sum_fails(self):
        self.rewrite(self.committed[0], "staging-manifest.json",
                     lambda value: value["files"][0].update(bytes=value["files"][0]["bytes"] + 1))
        with self.assertRaisesRegex(AlexandriaError, "do not sum"):
            self.module.verify_preserved()

    def test_a_record_without_planned_bytes_fails(self):
        self.rewrite(self.committed[0], "rebuild-record.json",
                     lambda value: value["measurements"]["planned"].pop("release_bytes"))
        with self.assertRaisesRegex(AlexandriaError, "planned bytes"):
            self.module.verify_preserved()

    def test_an_unknown_segment_directory_refuses(self):
        (self.copied_segments() / "12").mkdir()
        with self.assertRaisesRegex(AlexandriaError, "not a segment the table names"):
            self.module.verify_preserved()

    def test_the_readme_documents_the_staging_variable_and_external_archive(self):
        readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        self.assertIn(STAGING_ENV_VAR, readme)
        self.assertIn("held outside this repository", readme)


class StagingManifestGuardTests(DemoTestCase):
    """Corrupt, missing, extra and linked files refuse before the builder runs."""

    def setUp(self):
        super().setUp()
        self.staging = self.root / "staging"
        self.segment = self.staging / "segment-4"
        self.segment.mkdir(parents=True)
        files = []
        for name, data in (("checkpoint.json", b"{}\n"), ("journal.jsonl", b"[]\n")):
            (self.segment / name).write_bytes(data)
            files.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        self.small = {"format": self.module.MANIFEST_FORMAT, "segment": 4,
                      "archive": {"bytes": 1, "format": "tar+zstd", "sha256": "a" * 64},
                      "files": files, "staging_files_total": 2, "staging_bytes_total": 6}

    def small_document(self):
        section = {key: self.small[key] for key in ("segment", "files", "staging_files_total",
                                                    "staging_bytes_total")}
        return {"format": self.module.MANIFEST_FORMAT, "archive": self.small["archive"],
                "segments": [section]}

    def assert_refused_before_build(self, reason):
        target = self.copied_segments()
        for path in target.iterdir():
            if path.name != "4":
                shutil.rmtree(path)
        (target / "4").mkdir(exist_ok=True)
        (self.root / "staging-manifest.json").write_text(json.dumps(self.small_document()))
        for name in ("rebuild-record.json", "expected.json"):
            if not (target / "4" / name).exists():
                (target / "4" / name).write_text(json.dumps({"created_at": "2026-09-25T00:00:00Z"}))
        with mock.patch.dict(os.environ, {STAGING_ENV_VAR: str(self.staging)}), \
                mock.patch.object(self.module, "Builder") as builder:
            with self.assertRaisesRegex(AlexandriaError, reason):
                self.module.build(self.root / "built")
            builder.assert_not_called()
        self.assertFalse((self.root / "built").exists())

    def test_one_changed_byte_refuses_before_build(self):
        (self.segment / "journal.jsonl").write_bytes(b"{}\n")
        self.assert_refused_before_build("journal.jsonl differs")

    def test_an_unlisted_file_refuses_before_build(self):
        (self.segment / "extra").write_bytes(b"extra")
        self.assert_refused_before_build("does not list")

    def test_a_missing_file_refuses_before_build(self):
        (self.segment / "journal.jsonl").unlink()
        self.assert_refused_before_build("lacks")

    def test_a_symlink_refuses_before_build(self):
        (self.segment / "journal.jsonl").unlink()
        (self.segment / "journal.jsonl").symlink_to(self.segment / "checkpoint.json")
        self.assert_refused_before_build("symlink")

    def test_a_matching_tree_checks_every_file(self):
        self.assertEqual(self.module.verify_staging_tree(self.segment, self.small),
                         {"files": 2, "bytes": 6})

    def test_malformed_manifest_fields_refuse(self):
        for field, value in (("sha256", "bad"), ("bytes", True), ("path", "./journal.jsonl")):
            with self.subTest(field=field):
                self.small = copy.deepcopy(self.small)
                original = self.small["files"][1][field]
                self.small["files"][1][field] = value
                self.assert_refused_before_build("manifest")
                self.small["files"][1][field] = original


class MissingStagingEnvironmentVariableTests(DemoTestCase):
    """`build` refuses by name; it never silently proceeds without the trees."""

    def test_an_unset_variable_refuses_by_name(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(STAGING_ENV_VAR, None)
            with self.assertRaisesRegex(AlexandriaError, STAGING_ENV_VAR):
                self.module.build(self.root / "unstaged")
        self.assertFalse((self.root / "unstaged").exists())

    def test_the_command_line_refuses_by_name_without_the_variable(self):
        environment = {key: value for key, value in os.environ.items() if key != STAGING_ENV_VAR}
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "build", "--output", str(self.root / "cli")],
            capture_output=True, text=True, check=False, env=environment,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn(STAGING_ENV_VAR, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.root / "cli").exists())

    def test_a_variable_naming_a_directory_without_the_segment_refuses_by_name(self):
        empty = self.root / "not-a-staging-root"
        empty.mkdir()
        with mock.patch.dict(os.environ, {STAGING_ENV_VAR: str(empty)}):
            with self.assertRaisesRegex(AlexandriaError, "holds no checkpoint.json"):
                self.module.build(self.root / "unstaged")

    def test_the_command_line_reports_a_controlled_usage_error(self):
        result = subprocess.run([sys.executable, str(EXAMPLE / "demo.py")],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class OfflineDemoTests(unittest.TestCase):
    """The demonstration's rebuild path over the Step 4 constructed fixture.

    The fixture tree is collected and reconciled in process from the fixture
    transport, which answers from a JSON file. `rebuild` and `derive` then run
    under `offline()` with `socket.socket.connect` also trapped, so a socket
    anywhere in the path fails the case.
    """

    def setUp(self):
        self.module = demo()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.state = collector.fixture()
        self.registry = collector.registry()
        patcher = mock.patch.dict(aave_v3.REVIEWED_PROXY_CODES, collector.admitted_codes(self.state))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.staging = self.root / "staging"
        self.staging.mkdir()
        Collector(self.state["plan"], self.staging, collector.AaveTransport(self.state),
                  registry=self.registry).collect()
        Reconciler(self.state["plan"], self.staging, collector.AaveTransport(self.state),
                   collector.SECOND_PROVIDER, registry=self.registry).reconcile()

    def rebuilt(self, name):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            return self.module.rebuild(self.state["plan"], self.staging, self.registry,
                                       collector.CREATED_AT, self.root / name)

    def test_build_and_verify_agree_without_a_socket(self):
        built = self.rebuilt("first")
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            derived = self.module.derive(self.root / "first")
        self.assertEqual(derived, built)
        self.module.compare(derived, {**built, "segment": "fixture"}, "fixture rebuild")
        again = self.rebuilt("second")
        self.assertEqual(again["release_id"], built["release_id"])
        self.assertEqual(built["reconciliation"], "agreed")
        self.assertEqual(sum(built["shard_statuses"].values()), len(self.state["plan"]["shards"]))
        tampered = dict(built, epochs=built["epochs"] + 1, segment="fixture")
        with self.assertRaisesRegex(AlexandriaError, "epochs"):
            self.module.compare(derived, tampered, "fixture rebuild")

    def test_fixture_release_declares_constructed_staging(self):
        built = self.rebuilt("fixture")
        self.assertNotEqual(self.state["plan"]["deployment"], aave_v3.PRODUCTION_DEPLOYMENT)
        self.assertIs(built["constructed_staging_gap"], True)
        for path in sorted((EXAMPLE / "segments").glob("*/expected.json")):
            self.assertIs(load(path)["constructed_staging_gap"], False, path)


class StagedRebuildTests(DemoTestCase):
    """Needs the unpacked segment trees; reports their absence by name."""

    def setUp(self):
        super().setUp()
        value = os.environ.get(STAGING_ENV_VAR)
        if not value or not all((Path(value) / f"segment-{index}" / "checkpoint.json").is_file()
                                for index in self.committed):
            self.skipTest(f"not run: {STAGING_ENV_VAR} does not name every committed segment's "
                          "unpacked preserved staging tree")

    def test_build_and_verify_reproduce_every_committed_segment(self):
        output = self.root / "built"
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            summary = self.module.build(output)
            verified = self.module.verify(output)
        self.assertEqual(summary["segments"], verified["segments"])
        for index in self.committed:
            self.assertEqual(verified["segments"][str(index)]["release_id"],
                             self.segments[index]["expected.json"]["release_id"])


if __name__ == "__main__":
    unittest.main()
