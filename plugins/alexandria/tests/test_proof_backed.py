"""Proof-backed-state earning through reconstructed Lazarus fixtures."""

from copy import deepcopy
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
EXAMPLE = PLUGIN_ROOT / "examples" / "proof-backed-state-v0"
EXAMPLE_INPUT = EXAMPLE / "input"
EXAMPLE_RELEASE = EXAMPLE / "release"
AAVE_V4 = REPO_ROOT / "plugins" / "lazarus" / "examples" / "aave-v4-spoke-v0"
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from alexandria_lib.canonical import canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib import proof_backed  # noqa: E402
from alexandria_lib.release import ingest, verify  # noqa: E402


def _tree_bytes(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _restore_modes(root):
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_symlink():
            path.chmod(0o700 if path.is_dir() else 0o600)
    root.chmod(0o700)


class ProofBackedTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="alexandria-proof-backed-")
        self.root = Path(self.temporary.name)
        self.input = self.root / "input"
        shutil.copytree(EXAMPLE_INPUT, self.input)
        self.plan_path = self.input / "capture-plan.json"
        self.release = self.root / "release"

    def tearDown(self):
        _restore_modes(self.root)
        self.temporary.cleanup()

    def plan(self):
        return load_bytes(self.plan_path.read_bytes(), "capture plan")

    def write_plan(self, plan):
        self.plan_path.write_bytes(canonical_bytes(plan))

    def build(self, output=None):
        return ingest(self.plan_path, output or self.release)

    def manifest(self, release=None):
        release = release or self.release
        return load_bytes((release / "manifest.json").read_bytes(), "release manifest")

    def _tracked_reconstruction(self):
        created = []
        real_mkdtemp = tempfile.mkdtemp

        def record(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            created.append(Path(path))
            return path

        return created, mock.patch.object(
            proof_backed,
            "tempfile",
            SimpleNamespace(mkdtemp=record),
        )

    def assert_plan_refused(self, mutate, message, *, reconstruction=None):
        original = self.plan()
        expected_id = self.build()
        unchanged = _tree_bytes(self.release)
        candidate = deepcopy(original)
        mutate(candidate)
        self.write_plan(candidate)
        attempted = self.root / "attempted"
        created, tracker = self._tracked_reconstruction()
        with tracker:
            with self.assertRaisesRegex(
                AlexandriaError,
                "^capture state-proof proof-backed-state is not earned: .*" + message,
            ):
                ingest(self.plan_path, attempted)
        if reconstruction is not None:
            self.assertEqual(bool(created), reconstruction)
        self.assertTrue(all(not path.exists() for path in created))
        self.assertFalse(attempted.exists())
        self.assertEqual(_tree_bytes(self.release), unchanged)
        self.write_plan(original)
        self.assertEqual(self.build(attempted), expected_id)
        self.assertEqual(verify(attempted), expected_id)

    def mutate_lazarus_manifest(self, mutate):
        path = self.input / "fixture" / "manifest.json"
        value = load_bytes(path.read_bytes(), "Lazarus manifest")
        mutate(value)
        path.write_bytes(canonical_bytes(value))

    def assert_manifest_refused(
        self,
        mutate,
        message,
        *,
        mutate_plan=None,
        reconstruction=None,
    ):
        original_plan = self.plan()
        manifest_path = self.input / "fixture" / "manifest.json"
        original_manifest = manifest_path.read_bytes()
        expected_id = self.build()
        unchanged = _tree_bytes(self.release)
        self.mutate_lazarus_manifest(mutate)
        if mutate_plan is not None:
            candidate = self.plan()
            mutate_plan(candidate)
            self.write_plan(candidate)
        attempted = self.root / "attempted"
        created, tracker = self._tracked_reconstruction()
        with tracker:
            with self.assertRaisesRegex(
                AlexandriaError,
                "^capture state-proof proof-backed-state is not earned: .*" + message,
            ):
                ingest(self.plan_path, attempted)
        if reconstruction is not None:
            self.assertEqual(bool(created), reconstruction)
        self.assertTrue(all(not path.exists() for path in created))
        self.assertFalse(attempted.exists())
        self.assertEqual(_tree_bytes(self.release), unchanged)
        manifest_path.write_bytes(original_manifest)
        self.write_plan(original_plan)
        self.assertEqual(self.build(attempted), expected_id)
        self.assertEqual(verify(attempted), expected_id)


class ProofBackedPositiveTests(ProofBackedTestCase):
    def test_ingest_and_verify_return_release_id(self):
        release_id = self.build()
        self.assertEqual(verify(self.release), release_id)

    def test_cli_verify_prints_release_id(self):
        release_id = self.build()
        result = subprocess.run(
            [sys.executable, str(COMMAND), "verify", str(self.release)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, release_id + "\n")

    def test_repeat_ingests_are_byte_identical(self):
        first_id = self.build()
        second = self.root / "second"
        second_id = self.build(second)
        self.assertEqual(first_id, second_id)
        self.assertEqual(_tree_bytes(self.release), _tree_bytes(second))

    def test_verify_changes_no_release_byte_or_entry(self):
        self.build()
        before = _tree_bytes(self.release)
        verify(self.release)
        self.assertEqual(_tree_bytes(self.release), before)

    def test_verify_accepts_read_only_release_tree(self):
        release_id = self.build()
        paths = sorted(self.release.rglob("*"), reverse=True) + [self.release]
        original = {path: stat.S_IMODE(path.stat().st_mode) for path in paths}
        try:
            for path in paths:
                path.chmod(0o555 if path.is_dir() else 0o444)
            self.assertEqual(verify(self.release), release_id)
        finally:
            for path in reversed(paths):
                path.chmod(original[path])

    def test_verify_opens_no_network_socket(self):
        release_id = self.build()
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            self.assertEqual(verify(self.release), release_id)


class ProofBackedMappingTests(ProofBackedTestCase):
    def test_missing_fixture_file_component_is_refused_by_path(self):
        def mutate(plan):
            plan["components"] = [
                item for item in plan["components"] if item["path"] != "fixture/anchors.jsonl"
            ]

        self.assert_plan_refused(mutate, "fixture path anchors\\.jsonl", reconstruction=False)

    def test_changed_fixture_bytes_are_refused_by_lazarus_digest(self):
        release_id = self.build()
        unchanged = _tree_bytes(self.release)
        manifest = self.manifest()
        lazarus = load_bytes(
            (self.input / "fixture" / "manifest.json").read_bytes(),
            "Lazarus manifest",
        )
        target_digest = "sha256:" + lazarus["components"][0]["sha256"]
        target = next(item for item in manifest["components"] if item["sha256"] == target_digest)
        from alexandria_lib import derivation

        original_reader = derivation.component_reader

        def changed_reader(release_root, release_manifest):
            read = original_reader(release_root, release_manifest)

            def changed(name):
                data = read(name)
                return data + b"x" if name == target["name"] else data

            return changed

        created, tracker = self._tracked_reconstruction()
        with tracker, mock.patch.object(derivation, "component_reader", changed_reader):
            with self.assertRaisesRegex(
                AlexandriaError,
                "Lazarus refused the fixture: component size mismatch: anchors\\.jsonl",
            ):
                verify(self.release)
        self.assertTrue(created)
        self.assertTrue(all(not path.exists() for path in created))
        self.assertEqual(_tree_bytes(self.release), unchanged)
        self.assertEqual(verify(self.release), release_id)

    def test_parent_traversal_is_refused_before_reconstruction(self):
        self.assert_manifest_refused(
            lambda value: value["components"][0].update(path="../escape"),
            "\\.\\./escape",
            reconstruction=False,
        )

    def test_absolute_path_is_refused_before_reconstruction(self):
        self.assert_manifest_refused(
            lambda value: value["components"][0].update(path="/absolute/escape"),
            "/absolute/escape",
            reconstruction=False,
        )

    def test_manifest_without_components_is_refused_by_name(self):
        def no_coverage(plan):
            coverage = plan["captures"][0]["coverage"]
            coverage["status"] = "unsupported"
            coverage["record_count"] = 0
            coverage["collections"] = []
            coverage["gaps"] = ["malformed fixture manifest"]

        self.assert_manifest_refused(
            lambda value: value.pop("components"),
            "manifest has no components list",
            mutate_plan=no_coverage,
            reconstruction=False,
        )


class ProofBackedBindingTests(ProofBackedTestCase):
    def _capture(self, plan):
        return plan["captures"][0]

    def test_wrong_source_kind_is_refused(self):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["source"].update(kind="other-fixture"),
            "source kind must be lazarus-fixture",
            reconstruction=True,
        )

    def test_wrong_locator_class_is_refused(self):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["source"].update(locator_class="external-object"),
            "source locator_class must be local-fixture",
            reconstruction=True,
        )

    def test_wrong_fixture_digest_reference_is_refused(self):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["source"].update(reference="0" * 64),
            "source reference does not match",
            reconstruction=True,
        )

    def test_wrong_component_role_is_refused(self):
        def mutate(plan):
            component = next(item for item in plan["components"] if item["name"] == "fixture-manifest")
            component["role"] = "lazarus-fixture-file"

        self.assert_plan_refused(mutate, "component role must be lazarus-manifest", reconstruction=False)

    def test_wrong_chain_is_refused(self):
        def mutate(plan):
            capture = self._capture(plan)
            capture["chain"] = "eip155:10"
            capture["scope"]["subjects"] = [
                "eip155:10:0x2222222222222222222222222222222222222222"
            ]

        self.assert_plan_refused(mutate, "chain must match.*eip155:1", reconstruction=True)

    def test_full_dataset_scope_is_refused(self):
        def mutate(plan):
            scope = self._capture(plan)["scope"]
            scope["kind"] = "full-dataset"
            scope.pop("subjects")

        self.assert_plan_refused(mutate, "finite proof set is not a full dataset", reconstruction=True)

    def test_subject_outside_proof_targets_is_refused(self):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["scope"].update(
                subjects=["eip155:1:0x3333333333333333333333333333333333333333"]
            ),
            "outside the fixture proof targets",
            reconstruction=True,
        )

    def _assert_finality_refused(self, finality):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["scope"].update(finality=finality),
            "finality must be unknown",
            reconstruction=True,
        )

    def test_provider_reported_finality_is_refused(self):
        self._assert_finality_refused("provider-reported")

    def test_safe_finality_is_refused(self):
        self._assert_finality_refused("safe")

    def test_finalized_finality_is_refused(self):
        self._assert_finality_refused("finalized")

    def test_wrong_block_number_is_refused(self):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["scope"]["interval"].update(block_number="1"),
            "block_number must match the proved block 0",
            reconstruction=True,
        )

    def test_wrong_block_hash_is_refused(self):
        self.assert_plan_refused(
            lambda plan: self._capture(plan)["scope"]["interval"].update(
                block_hash="0x" + "0" * 64
            ),
            "block_hash must match the proved block",
            reconstruction=True,
        )

    def test_block_range_is_refused(self):
        def mutate(plan):
            self._capture(plan)["scope"]["interval"] = {
                "kind": "block-range",
                "start": "0",
                "end": "0",
            }

        self.assert_plan_refused(mutate, "interval must be a snapshot", reconstruction=True)

    def test_snapshot_without_block_identifiers_is_refused(self):
        def mutate(plan):
            interval = self._capture(plan)["scope"]["interval"]
            interval.pop("block_number")
            interval.pop("block_hash")

        self.assert_plan_refused(mutate, "snapshot must carry the proved block", reconstruction=True)


class ProofBackedCompatibilityTests(ProofBackedTestCase):
    def test_recorded_rpc_local_fixture_does_not_load_lazarus(self):
        plan = self.plan()
        plan["captures"][0]["evidence_class"] = "recorded-rpc"
        self.write_plan(plan)
        with mock.patch.object(
            proof_backed,
            "_lazarus_api",
            side_effect=AssertionError("Lazarus loaded without a proof-backed claim"),
        ):
            release_id = self.build()
            self.assertEqual(verify(self.release), release_id)

    def test_existing_capture_plan_does_not_load_lazarus(self):
        shutil.rmtree(self.input)
        shutil.copytree(FIXTURES, self.input)
        self.plan_path = self.input / "capture-plan.json"
        with mock.patch.object(
            proof_backed,
            "_lazarus_api",
            side_effect=AssertionError("Lazarus loaded without a proof-backed claim"),
        ):
            release_id = self.build()
            self.assertEqual(verify(self.release), release_id)

    def test_unavailable_verifier_refuses_without_changing_release(self):
        release_id = self.build()
        before = _tree_bytes(self.release)
        with mock.patch.object(
            proof_backed,
            "_lazarus_api",
            side_effect=AlexandriaError(proof_backed.UNAVAILABLE_REASON),
        ):
            with self.assertRaisesRegex(AlexandriaError, "Lazarus verifier is unavailable"):
                verify(self.release)
        self.assertEqual(_tree_bytes(self.release), before)
        self.assertEqual(verify(self.release), release_id)


class ProofBackedCleanupTests(ProofBackedTestCase):
    def test_cleanup_failure_after_success_is_a_named_refusal(self):
        self.build()
        unavailable_cleanup = SimpleNamespace(
            rmtree=mock.Mock(side_effect=OSError("cleanup denied"))
        )
        with mock.patch.object(proof_backed, "shutil", unavailable_cleanup):
            with self.assertRaises(AlexandriaError) as raised:
                verify(self.release)
        self.assertEqual(
            str(raised.exception),
            "capture state-proof proof-backed-state is not earned: "
            "cannot remove the reconstruction directory: cleanup denied",
        )

    def test_cleanup_failure_does_not_replace_the_first_refusal(self):
        plan = self.plan()
        plan["captures"][0]["scope"]["finality"] = "provider-reported"
        self.write_plan(plan)
        unavailable_cleanup = SimpleNamespace(
            rmtree=mock.Mock(side_effect=OSError("cleanup denied"))
        )
        with mock.patch.object(proof_backed, "shutil", unavailable_cleanup):
            with self.assertRaises(AlexandriaError) as raised:
                self.build()
        self.assertEqual(
            str(raised.exception),
            "capture state-proof proof-backed-state is not earned: finality must be "
            "unknown because Lazarus proves block binding but reports no finality class",
        )


class ProofBackedRealFixtureTests(ProofBackedTestCase):
    def test_aave_v4_nested_real_chain_fixture_verifies(self):
        shutil.rmtree(self.input / "fixture")
        shutil.copytree(AAVE_V4, self.input / "fixture")
        lazarus_manifest = load_bytes(
            (self.input / "fixture" / "manifest.json").read_bytes(),
            "Aave v4 manifest",
        )
        lazarus_plan = load_bytes(
            (self.input / "fixture" / "plan.json").read_bytes(),
            "Aave v4 plan",
        )
        plan = self.plan()
        plan["components"] = [{
            "name": "fixture-manifest",
            "path": "fixture/manifest.json",
            "media_type": "application/json",
            "role": "lazarus-manifest",
            "access": "public",
            "redistribution": "permitted",
        }]
        for index, entry in enumerate(lazarus_manifest["components"]):
            suffix = "jsonl" if entry["path"].endswith(".jsonl") else entry["path"].rsplit(".", 1)[-1]
            media_type = {
                "json": "application/json",
                "jsonl": "application/jsonl",
                "md": "text/markdown",
                "py": "text/x-python",
            }.get(suffix, "application/octet-stream")
            plan["components"].append({
                "name": f"fixture-file-{index:02d}",
                "path": "fixture/" + entry["path"],
                "media_type": media_type,
                "role": "lazarus-fixture-file",
                "access": "public",
                "redistribution": "permitted",
            })
        capture = plan["captures"][0]
        capture["chain"] = "eip155:1"
        capture["source"]["reference"] = lazarus_manifest["fixture_digest"]
        capture["scope"]["interval"]["block_number"] = str(
            int(lazarus_manifest["block"]["number"], 16)
        )
        capture["scope"]["interval"]["block_hash"] = lazarus_manifest["block"]["hash"].lower()
        capture["scope"]["subjects"] = [
            f"eip155:{int(lazarus_manifest['chain_id'], 16)}:"
            f"{lazarus_plan['proof_targets'][0]['address'].lower()}"
        ]
        capture["coverage"]["record_count"] = len(lazarus_manifest["components"])
        capture["coverage"]["collections"][0]["record_count"] = len(
            lazarus_manifest["components"]
        )
        self.write_plan(plan)
        release_id = self.build()
        self.assertEqual(verify(self.release), release_id)
        self.assert_plan_refused(
            lambda candidate: candidate["captures"][0]["scope"].update(
                subjects=["eip155:1:0x3333333333333333333333333333333333333333"]
            ),
            "outside the fixture proof targets",
            reconstruction=True,
        )

    def test_checked_in_example_rebuilds_byte_identically_and_verifies(self):
        rebuilt = self.root / "rebuilt"
        release_id = self.build(rebuilt)
        self.assertEqual(_tree_bytes(rebuilt), _tree_bytes(EXAMPLE_RELEASE))
        self.assertEqual(verify(EXAMPLE_RELEASE), release_id)


class ProofBackedPromiseCoverageTests(ProofBackedTestCase):
    def test_alexandria_proof_backed_p_accepts_verified_fixture(self):
        release_id = self.build()
        self.assertEqual(verify(self.release), release_id)

    def test_alexandria_proof_backed_m_refuses_missing_fixture_component(self):
        def mutate(plan):
            plan["components"] = [
                item for item in plan["components"] if item["path"] != "fixture/anchors.jsonl"
            ]

        self.assert_plan_refused(mutate, "fixture path anchors\\.jsonl", reconstruction=False)

    def test_alexandria_proof_backed_o_refuses_proof_overclaim(self):
        self.assert_plan_refused(
            lambda plan: plan["captures"][0]["scope"].update(
                subjects=["eip155:1:0x3333333333333333333333333333333333333333"]
            ),
            "outside the fixture proof targets",
            reconstruction=True,
        )

    def test_alexandria_proof_backed_r_accepts_repaired_plan(self):
        original = self.plan()
        broken = deepcopy(original)
        broken["captures"][0]["source"]["reference"] = "0" * 64
        self.write_plan(broken)
        with self.assertRaisesRegex(AlexandriaError, "source reference does not match"):
            self.build()
        self.assertFalse(self.release.exists())
        self.write_plan(original)
        release_id = self.build()
        self.assertEqual(verify(self.release), release_id)

    def test_alexandria_proof_backed_s_is_offline_and_read_only(self):
        release_id = self.build()
        before = _tree_bytes(self.release)
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            self.assertEqual(verify(self.release), release_id)
        self.assertEqual(_tree_bytes(self.release), before)


if __name__ == "__main__":
    unittest.main()
