"""The preserved Wildcat V1 mainnet interval: rebuilt from an external archive.

Unlike `usdc-interval-live-v0`, whose tiny staging tree ships inside this
repository, this interval's staging tree -- 667 shards, 107 files, 18,665,266 bytes -- is preserved outside this repository and reached only through the
`ALEXANDRIA_WILDCAT_V1_STAGING` environment variable. A test that needs that
tree and does not find it must report exactly that reason and never silently
pass; `demo.py` refuses by name when the variable is unset, and the tests
here that need it do the same, loudly, via `skipTest` with the same reason,
never a bare skip and never a pass.

A separate group needs no staging tree at all: `staging-manifest.json` binds
the preserved archive's own byte count and SHA-256 to the byte count and
SHA-256 of every file inside it, and `rebuild-record.json` is what this
collecting host got when it actually rebuilt the release from that tree. Those
two files are checked into this repository, and the tests in
`PreservedArtefactsTests` fail -- they do not skip -- if either one is
missing, malformed, or disagrees with `expected.json` or with each other.
"""

import copy
import hashlib
import json
from pathlib import Path
import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "wildcat-v1-interval-v0"
MODULE_NAME = "wildcat_v1_interval_demo"
STAGING_ENV_VAR = "ALEXANDRIA_WILDCAT_V1_STAGING"
REQUIRED = (
    "demo.py",
    "plan.json",
    "registry.json",
    "expected.json",
    "README.md",
    "staging-manifest.json",
    "rebuild-record.json",
)

sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import MAX_SHARDS, MAX_SHARD_WIDTH, validate_plan  # noqa: E402
from tests.test_usdc_interval import component_document  # noqa: E402
from tests.test_wildcat_venue import v1_row  # noqa: E402


def demo():
    """Import the demonstration, failing rather than skipping when it is absent.

    Every file this checks is meant to be committed to this repository (the
    preserved staging tree itself is the one exception, handled separately
    below); a missing one here is a defect in the example, not something to
    wave past.
    """
    missing = [name for name in REQUIRED if not (EXAMPLE / name).is_file()]
    if missing:
        raise AssertionError(
            f"the wildcat-v1-interval-v0 example is missing {', '.join(missing)} "
            f"at {EXAMPLE}; this suite is the proof it is complete and must fail "
            "rather than skip"
        )
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    spec = importlib.util.spec_from_file_location(MODULE_NAME, EXAMPLE / "demo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class DemoTestCase(unittest.TestCase):
    def setUp(self):
        self.module = demo()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.expected = json.loads((EXAMPLE / "expected.json").read_text(encoding="utf-8"))
        self.manifest = json.loads((EXAMPLE / "staging-manifest.json").read_text(encoding="utf-8"))
        self.record = json.loads((EXAMPLE / "rebuild-record.json").read_text(encoding="utf-8"))


class PreservedArtefactsTests(DemoTestCase):
    """Needs no staging tree. Fails -- never skips -- on a bad manifest or record."""

    def test_verify_preserved_passes_against_the_committed_artefacts(self):
        result = self.module.verify_preserved()
        self.assertEqual(result["manifest"], self.manifest)
        self.assertEqual(result["record"], self.record)

    def test_committed_plan_fits_both_transport_and_collector_bounds(self):
        plan = json.loads((EXAMPLE / "plan.json").read_text())
        validate_plan(plan)
        self.assertLessEqual(plan["shard_width"], MAX_SHARD_WIDTH)
        self.assertLessEqual(len(plan["shards"]), MAX_SHARDS)
        self.assertTrue(all(shard["end"] - shard["start"] <= 29_999 for shard in plan["shards"]))
        self.assertGreaterEqual(int(plan["finality"]["block_number"]), int(plan["interval"]["end"]))
        self.assertEqual(len(plan["subjects"]), 16)

    def test_the_manifest_is_well_formed(self):
        self.assertEqual(self.manifest["format"], self.module.MANIFEST_FORMAT)
        archive = self.manifest["archive"]
        self.assertIn("sha256", archive)
        self.assertIn("bytes", archive)
        self.assertIsInstance(self.manifest["files"], list)
        self.assertEqual(len(self.manifest["files"]), 107)
        for entry in self.manifest["files"]:
            self.assertIn("path", entry)
            self.assertIn("bytes", entry)
            self.assertIn("sha256", entry)

    def test_the_manifest_file_sizes_sum_to_its_own_declared_total(self):
        total = sum(entry["bytes"] for entry in self.manifest["files"])
        self.assertEqual(total, self.manifest["staging_bytes_total"])
        self.assertEqual(len(self.manifest["files"]), self.manifest["staging_files_total"])

    def test_the_manifest_names_no_path_twice(self):
        paths = [entry["path"] for entry in self.manifest["files"]]
        self.assertEqual(len(paths), len(set(paths)))

    def test_the_rebuild_record_is_well_formed_and_binds_the_manifests_archive(self):
        self.assertEqual(self.record["format"], self.module.RECORD_FORMAT)
        for field in ("archive_sha256", "checked", "rebuilt_at", "rebuilt_by"):
            self.assertIn(field, self.record)
        self.assertEqual(self.record["archive_sha256"], self.manifest["archive"]["sha256"])

    def test_the_rebuild_record_agrees_with_the_pinned_expectation(self):
        checked = self.record["checked"]
        for field in ("epochs", "reconciliation", "release_id", "shard_statuses"):
            self.assertEqual(checked[field], self.expected[field], field)

    def test_a_missing_manifest_fails_not_skips(self):
        with mock.patch.object(self.module, "MANIFEST", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "staging manifest is missing"):
                self.module.verify_preserved()

    def test_a_missing_rebuild_record_fails_not_skips(self):
        with mock.patch.object(self.module, "RECORD", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "rebuild record is missing"):
                self.module.verify_preserved()

    def test_a_malformed_manifest_format_fails(self):
        broken = self.root / "manifest.json"
        broken.write_text(json.dumps(dict(self.manifest, format="unknown/v0")), encoding="utf-8")
        with mock.patch.object(self.module, "MANIFEST", broken):
            with self.assertRaisesRegex(AlexandriaError, "unknown format"):
                self.module.verify_preserved()

    def test_a_manifest_whose_file_sizes_do_not_sum_fails(self):
        tampered = copy.deepcopy(self.manifest)
        tampered["files"][0]["bytes"] += 1
        broken = self.root / "manifest.json"
        broken.write_text(json.dumps(tampered), encoding="utf-8")
        with mock.patch.object(self.module, "MANIFEST", broken):
            with self.assertRaisesRegex(AlexandriaError, "do not sum"):
                self.module.verify_preserved()

    def test_a_record_binding_a_different_archive_fails(self):
        tampered = dict(self.record, archive_sha256="0" * 64)
        broken = self.root / "record.json"
        broken.write_text(json.dumps(tampered), encoding="utf-8")
        with mock.patch.object(self.module, "RECORD", broken):
            with self.assertRaisesRegex(AlexandriaError, "different archive"):
                self.module.verify_preserved()

    def test_a_record_that_disagrees_with_expected_fails(self):
        tampered = copy.deepcopy(self.record)
        tampered["checked"]["epochs"] += 1
        broken = self.root / "record.json"
        broken.write_text(json.dumps(tampered), encoding="utf-8")
        with mock.patch.object(self.module, "RECORD", broken):
            with self.assertRaisesRegex(AlexandriaError, "epochs"):
                self.module.verify_preserved()

    def test_the_command_line_runs_verify_preserved(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "verify-preserved"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.expected["release_id"], result.stdout)

    def test_neither_this_group_nor_verify_preserved_opens_a_socket(self):
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            self.module.verify_preserved()

    def test_the_readme_never_names_the_external_repository_that_holds_the_archive(self):
        for path in sorted(p for p in EXAMPLE.iterdir() if p.is_file()):
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("secretsauce", text.lower(), path)

    def test_the_readme_documents_the_staging_environment_variable(self):
        readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        self.assertIn(STAGING_ENV_VAR, readme)
        self.assertIn("preserved outside this repository", readme)

    def test_capture_provenance_and_both_pre_plan_archive_probes_are_bound(self):
        raw = (EXAMPLE / "capture-evidence.json").read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.record["capture_evidence_sha256"])
        evidence = json.loads(raw)
        for field in ("plan", "registry"):
            self.assertEqual(
                hashlib.sha256((EXAMPLE / (field + ".json")).read_bytes()).hexdigest(),
                evidence[field + "_sha256"],
            )
        probes = evidence["pre_plan_readiness"]
        self.assertLess(probes["observed_at"], evidence["executions"]["superseded_plan"][0]["started_at"])
        self.assertLess(probes["observed_at"], evidence["plan_replacement"]["observed_at"])
        opening = []
        for probe in probes["results"]:
            path = EXAMPLE / "pre-plan-probes" / (probe["provider"] + "-" + probe["label"] + ".json")
            payload = path.read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), probe["response_sha256"])
            response = json.loads(payload)["result"]
            if probe["label"] == "opening-code":
                code = bytes.fromhex(response[2:])
                self.assertEqual(len(code), probe["code_bytes"])
                self.assertGreater(len(code), 0)
                self.assertEqual(hashlib.sha256(code).hexdigest(), probe["code_sha256"])
                self.assertEqual(int(probe["params"][1], 16), 18743513)
                opening.append(probe["provider"])
            else:
                self.assertEqual(int(response["number"], 16), probe["block_number"])
                self.assertEqual(response["hash"], probe["block_hash"])
        self.assertEqual(sorted(opening), ["primary", "secondary"])
        self.assertEqual(evidence["runtime"]["source_commit"], "296a794d8bca1ad051d3b4d9cae1339f5e433571")
        self.assertEqual(evidence["runtime"]["collector_sha256"], "11b05610845142c814d13a21ea90802a0bbd7c2b6e90bdfdbd20eb03ce56aba9")
        self.assertEqual([row["exit"] for row in evidence["executions"]["superseded_plan"]], [1, 1])
        self.assertEqual([row["exit"] for row in evidence["executions"]["current_plan"]], [-2, 1, 0, 0])
        reconciliation = evidence["executions"]["current_plan"][-1]["reconciliation"]
        self.assertEqual(reconciliation["compared"], 4325)
        self.assertEqual(reconciliation["matched"], 4325)
        self.assertEqual(reconciliation["disputed"], [])

    def test_registry_keeps_all_source_identities_and_deployment_gaps(self):
        registry = json.loads((EXAMPLE / "registry.json").read_bytes())
        source = v1_row()
        rows = {row["address"]: row for row in source["deployment"]["contracts"]}
        self.assertEqual(len(registry["entries"]), 16)
        self.assertEqual(sum(row["deployment_block"] is None for row in registry["entries"]), 12)
        self.assertEqual(sum(row["deployment_block"] is not None for row in registry["entries"]), 4)
        for entry in registry["entries"]:
            self.assertEqual(entry["source_commit"], rows[entry["address"]]["code_match"]["source_commit"])
        for field in ("equivalent_commits", "equivalence_note"):
            self.assertEqual(registry["source"][field], source["source"][field])
        self.assertEqual(len(registry["source"]["equivalent_commits"]), 4)

    def test_every_committed_example_file_excludes_endpoint_and_header_shapes(self):
        for path in sorted(EXAMPLE.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            payload = path.read_bytes()
            for prohibited in (b"http://127.0.0.1", b"http://localhost", b"Authorization: Bearer "):
                self.assertNotIn(prohibited, payload, str(path))


class StagingManifestGuardTests(DemoTestCase):
    """Check corrupt, missing and extra files before the builder consumes staging."""

    def setUp(self):
        super().setUp()
        self.staging = self.root / "staging"
        self.staging.mkdir()
        files = []
        for name, data in (("checkpoint.json", b"{}\n"), ("journal.jsonl", b"[]\n")):
            (self.staging / name).write_bytes(data)
            files.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        self.small_manifest = {
            "format": self.module.MANIFEST_FORMAT,
            "archive": {"bytes": 1, "sha256": "a" * 64},
            "files": files, "staging_files_total": 2, "staging_bytes_total": 6,
        }
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.small_manifest))

    def assert_refused_before_build(self, reason):
        with mock.patch.object(self.module, "MANIFEST", self.manifest_path), mock.patch.dict(
            os.environ, {STAGING_ENV_VAR: str(self.staging)}
        ), mock.patch.object(self.module, "Builder") as builder:
            with self.assertRaisesRegex(AlexandriaError, reason):
                self.module.build(self.root / "built")
            builder.assert_not_called()
        self.assertFalse((self.root / "built").exists())

    def test_one_changed_byte_refuses_before_build(self):
        (self.staging / "journal.jsonl").write_bytes(b"{}\n")
        self.assert_refused_before_build("journal.jsonl differs")

    def test_an_unlisted_file_refuses_before_build(self):
        (self.staging / "extra").write_bytes(b"extra")
        self.assert_refused_before_build("does not list")

    def test_a_missing_file_refuses_before_build(self):
        (self.staging / "journal.jsonl").unlink()
        self.assert_refused_before_build("lacks")

    def test_a_symlink_refuses_before_build(self):
        (self.staging / "journal.jsonl").unlink()
        (self.staging / "journal.jsonl").symlink_to(self.staging / "checkpoint.json")
        self.assert_refused_before_build("symlink")

    def test_a_matching_tree_checks_every_file(self):
        self.assertEqual(
            self.module.verify_staging_tree(self.staging, self.small_manifest),
            {"files": 2, "bytes": 6},
        )

    def test_malformed_manifest_fields_refuse(self):
        for field, value in (("sha256", "bad"), ("bytes", True), ("path", "./journal.jsonl")):
            with self.subTest(field=field):
                broken = copy.deepcopy(self.small_manifest)
                broken["files"][1][field] = value
                self.manifest_path.write_text(json.dumps(broken))
                self.assert_refused_before_build("manifest")


class StagedRebuildTests(DemoTestCase):
    """Needs the real preserved staging tree, unpacked locally.

    Every test here reports its absence by name through `skipTest`, which
    unittest renders as skipped -- distinct from a pass -- rather than a
    silent omission or a green result with nothing behind it.
    """

    def setUp(self):
        super().setUp()
        value = os.environ.get(STAGING_ENV_VAR)
        if not value or not (Path(value) / "checkpoint.json").is_file():
            self.skipTest(
                f"not run: {STAGING_ENV_VAR} is not set to an unpacked preserved "
                "staging tree"
            )

    def test_the_rebuild_reproduces_the_pinned_identifier(self):
        output = self.root / "built"
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            summary = self.module.build(output)
        self.assertEqual(summary["release_id"], self.expected["release_id"])
        self.assertEqual(summary["epochs"], self.expected["epochs"])
        self.assertEqual(summary["reconciliation"], self.expected["reconciliation"])
        self.assertEqual(summary["shard_statuses"], self.expected["shard_statuses"])

    def test_verify_compares_every_pinned_identity_and_the_cli_agrees(self):
        output = self.root / "built"
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            self.module.build(output)
            derived = self.module.verify(output)
        for field in self.module.COMPARED:
            self.assertEqual(derived[field], self.expected[field], field)

        cli_output = self.root / "cli"
        built = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "build", "--output", str(cli_output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertIn(self.expected["release_id"], built.stdout)
        verified = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "verify", str(cli_output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)

    def test_release_preserves_source_caveats_opening_code_and_observed_attribution(self):
        output = self.root / "capture"
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network used")):
            self.module.build(output)
            self.module.verify(output)
        release = output / "release"
        registry = component_document(release, "registry")
        self.assertEqual(registry, json.loads((EXAMPLE / "registry.json").read_bytes()))
        receipt = component_document(release, "epoch-table")
        code = component_document(release, "implementation-code")["records"]
        code_digests = {row["address"]: hashlib.sha256(bytes.fromhex(row["code"][2:])).hexdigest() for row in code}
        self.assertEqual(len(code_digests), 16)
        for row in receipt["epochs"]:
            self.assertEqual(row["epochs"][0]["implementation_code_sha256"], code_digests[row["subject"]])
        manifest = json.loads((release / "manifest.json").read_bytes())
        self.assertEqual({capture["venue"] for capture in manifest["captures"]}, {"wildcat-v1"})
        missing = {row["address"] for row in registry["entries"] if row["deployment_block"] is None}
        for capture in manifest["captures"]:
            gaps = capture["coverage"]["gaps"]
            self.assertFalse(any("constructed rather than collected" in gap for gap in gaps))
            self.assertFalse(any("establish no source commit" in gap for gap in gaps))
            if capture["id"] == "registry":
                for address in missing:
                    self.assertTrue(any(address in gap and "deployment block" in gap for gap in gaps))
        self.assertEqual({row["subject"] for row in receipt["first_code"]}, missing)
        observed = json.loads((EXAMPLE / "shared-subject-comparison.json").read_bytes())
        self.assertEqual(hashlib.sha256((EXAMPLE / "shared-subject-comparison.json").read_bytes()).hexdigest(), self.record["shared_subject_comparison_sha256"])
        attributions = receipt["log_attributions"]
        self.assertEqual(len(attributions), 1941)
        for address, count in observed["log_counts"]["wildcat-v1"].items():
            self.assertEqual(sum(row["subject"] == address for row in attributions), count)
        declared = {row["address"] for row in registry["entries"]}
        self.assertTrue(all(row["subject"] in declared for row in attributions))
        reconciliation = component_document(release, "reconciliation")["reconciliation"]
        self.assertEqual(reconciliation["status"], "agreed")
        self.assertEqual(reconciliation["compared"], 4325)
        self.assertEqual(reconciliation["matched"], 4325)
        self.assertEqual(reconciliation["disputed"], [])

    def test_actual_shared_logs_agree_across_both_captures_and_keep_sentinel_absence(self):
        from tests.test_wildcat_v2_interval_demo import demo as v2_demo

        v2 = v2_demo()
        second = os.environ.get(v2.STAGING_ENV_VAR)
        if not second or not (Path(second) / "checkpoint.json").is_file():
            self.skipTest("not run: ALEXANDRIA_WILDCAT_V2_STAGING does not name preserved staging")
        observed = json.loads((EXAMPLE / "shared-subject-comparison.json").read_bytes())
        overlap = observed["overlapping_interval"]
        shared = set(observed["shared_subjects"])
        compared = []
        for venue, module in (("wildcat-v1", self.module), ("wildcat-v2", v2)):
            output = self.root / venue
            with mock.patch.object(socket, "socket", side_effect=AssertionError("network used")):
                module.build(output)
                module.verify(output)
            release = output / "release"
            manifest = json.loads((release / "manifest.json").read_bytes())
            self.assertEqual({capture["venue"] for capture in manifest["captures"]}, {venue})
            receipt = component_document(release, "epoch-table")
            for address, count in observed["log_counts"][venue].items():
                self.assertEqual(sum(row["subject"] == address for row in receipt["log_attributions"]), count)
            declared = set(json.loads(module.PLAN.read_bytes())["subjects"])
            logs = []
            for component in manifest["components"]:
                if component["name"].split(".")[0] != "logs":
                    continue
                for envelope in component_document(release, component["name"])["records"]:
                    logs.extend(json.loads(envelope["response"])["result"])
            self.assertEqual(len(logs), observed["total_subject_logs"][venue])
            # ephoros: allow raw Ethereum event emitters in capture assertions, not telemetry keys.
            self.assertTrue(all(log["address"] in declared for log in logs))
            # ephoros: allow raw Ethereum event emitters in capture assertions, not telemetry keys.
            selected = [log for log in logs if log["address"] in shared and
                        overlap["start"] <= int(log["blockNumber"], 16) <= overlap["end"]]
            compared.append(sorted(selected, key=lambda log: (
                int(log["blockNumber"], 16), int(log["transactionIndex"], 16),
                int(log["logIndex"], 16),
            )))
        self.assertEqual(len(compared[0]), observed["overlapping_shared_logs"])
        self.assertEqual(compared[0], compared[1])


class MissingStagingEnvironmentVariableTests(DemoTestCase):
    """`build` refuses by name; it never silently proceeds without the tree."""

    def test_an_unset_variable_refuses_by_name(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(STAGING_ENV_VAR, None)
            with self.assertRaisesRegex(AlexandriaError, STAGING_ENV_VAR):
                self.module.build(self.root / "unstaged")
        self.assertFalse((self.root / "unstaged").exists())

    def test_a_variable_naming_a_tree_with_no_checkpoint_refuses_by_name(self):
        empty = self.root / "not-a-staging-tree"
        empty.mkdir()
        with mock.patch.dict(os.environ, {STAGING_ENV_VAR: str(empty)}):
            with self.assertRaisesRegex(AlexandriaError, "no checkpoint.json"):
                self.module.build(self.root / "unstaged")

    def test_the_command_line_reports_a_controlled_usage_error(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
