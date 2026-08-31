"""The checked-in Goldfinch fixture runs and remains offline reproducible."""

import ast
import ipaddress
from io import StringIO
import os
from pathlib import Path
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from lazarus_lib.canonical import load, loads
from lazarus_lib.errors import LazarusError
from lazarus_lib.verifier import verify_fixture

from . import support


FIXTURE = support.PLUGIN_ROOT / "examples" / "goldfinch-v0"
RECEIPT_FIXTURE = support.PLUGIN_ROOT / "examples" / "goldfinch-v1"
ANCHOR_FIXTURE = support.PLUGIN_ROOT / "examples" / "multi-provider-anchor-v0"
DEMO_PATH = FIXTURE / "demo.py"
RECEIPT_DEMO_PATH = RECEIPT_FIXTURE / "demo.py"
RECEIPTS_ROOT = "0xaf03b0508121deb9ed0282a8961dc0ea695a97244a42ed2b0af04cb9bbc6226e"
# The complete demo contains five RPC calls with 5-second socket timeouts and a
# 2-second thread join, followed by CPU-bound fixture checks. Keep its outer
# compatibility ceiling explicit; only a hosted run establishes wall-clock fit.
LEGACY_DEMO_SUBPROCESS_TIMEOUT_SECONDS = 60


def load_demo():
    return SimpleNamespace(**runpy.run_path(str(DEMO_PATH)))


def load_receipt_demo():
    return SimpleNamespace(**runpy.run_path(str(RECEIPT_DEMO_PATH)))


class GoldfinchDemoTests(unittest.TestCase):
    def test_synthetic_multi_provider_fixture_keeps_anchor_claims_false(self):
        report = verify_fixture(ANCHOR_FIXTURE)
        self.assertEqual(
            report["fixture_digest"],
            "188eb293ac1de8036ff4be861e339fe5757b51995c88e8ea1afcfa498134a72e",
        )
        self.assertEqual(
            report["chain_anchors"],
            {
                "records": 2,
                "canonical_chain_claim": False,
                "provider_independence_claim": False,
            },
        )
        self.assertEqual(
            report["evidence_counts"],
            {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
        )
        fixture_bytes = b"".join(
            path.read_bytes() for path in ANCHOR_FIXTURE.rglob("*") if path.is_file()
        )
        self.assertNotIn(b"provider_url", fixture_bytes)
        self.assertNotIn(b"rpc-url", fixture_bytes)

    def test_fixture_verifies_with_expected_evidence_and_provenance(self):
        report = verify_fixture(FIXTURE)
        self.assertEqual(
            report["fixture_digest"],
            "d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49",
        )
        self.assertEqual(
            report["evidence_counts"],
            {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 4},
        )
        self.assertEqual(report["proof_backed"]["accounts_included"], 1)
        self.assertEqual(report["proof_backed"]["storage_included"], 1)
        self.assertFalse(report["header_bound"]["canonical_chain_claim"])

    def test_demo_command_runs_the_complete_application_check(self):
        result = subprocess.run(
            [sys.executable, str(DEMO_PATH)],
            cwd=support.REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=LEGACY_DEMO_SUBPROCESS_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("replayed code bytes: 45", result.stdout)
        self.assertIn("replayed logs: 5", result.stdout)
        self.assertIn("slot 0x1 miss: -32070", result.stdout)
        self.assertIn("one-nibble proof mutation: rejected", result.stdout)
        self.assertIn("manifest rebuild: identical", result.stdout)

    def test_complete_demo_timeout_exceeds_its_inner_fail_closed_bounds(self):
        tree = ast.parse(DEMO_PATH.read_text(encoding="utf-8"))
        rpc_calls = sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "rpc_call"
            for node in ast.walk(tree)
        )
        connection_timeouts = [
            keyword.value.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "HTTPConnection"
            for keyword in node.keywords
            if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant)
        ]
        join_timeouts = [
            keyword.value.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "join"
            for keyword in node.keywords
            if keyword.arg == "timeout" and isinstance(keyword.value, ast.Constant)
        ]
        self.assertEqual(rpc_calls, 5)
        self.assertEqual(connection_timeouts, [5])
        self.assertEqual(join_timeouts, [2])
        self.assertGreater(
            LEGACY_DEMO_SUBPROCESS_TIMEOUT_SECONDS,
            rpc_calls * connection_timeouts[0] + join_timeouts[0],
        )

    def test_complete_demo_invocation_uses_the_named_outer_bound(self):
        self.assertEqual(LEGACY_DEMO_SUBPROCESS_TIMEOUT_SECONDS, 60)
        command = [sys.executable, str(DEMO_PATH)]
        completed = subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=(
                "replayed code bytes: 45\n"
                "replayed logs: 5\n"
                "slot 0x1 miss: -32070\n"
                "one-nibble proof mutation: rejected\n"
                "manifest rebuild: identical\n"
            ),
            stderr="",
        )
        with mock.patch.object(subprocess, "run", return_value=completed) as runner:
            self.test_demo_command_runs_the_complete_application_check()
        runner.assert_called_once_with(
            command,
            cwd=support.REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=LEGACY_DEMO_SUBPROCESS_TIMEOUT_SECONDS,
        )

    def test_manifest_rebuild_is_byte_identical(self):
        demo = load_demo()
        before = (FIXTURE / "manifest.json").read_bytes()
        demo.rebuild_manifest_bytes(load(FIXTURE / "manifest.json"))
        self.assertEqual((FIXTURE / "manifest.json").read_bytes(), before)

    def test_one_nibble_proof_mutation_is_rejected(self):
        demo = load_demo()
        demo.reject_mutated_proof(load(FIXTURE / "manifest.json"))

    def test_application_replay_and_miss_cannot_leave_loopback(self):
        demo = load_demo()
        real_connect = socket.socket.connect
        destinations = []

        def guarded_connect(sock, address):
            destinations.append(address)
            if not ipaddress.ip_address(address[0]).is_loopback:
                raise AssertionError(f"outbound demo connection: {address}")
            return real_connect(sock, address)

        with mock.patch.object(socket.socket, "connect", guarded_connect):
            report = demo.run_demo()
        self.assertEqual(report["miss"], -32070)
        self.assertEqual(report["slot_zero"], "0x" + "00" * 31 + "01")
        self.assertTrue(destinations)
        self.assertTrue(
            all(ipaddress.ip_address(item[0]).is_loopback for item in destinations)
        )

    def test_schema_snapshots_and_fixture_inventory_are_exact(self):
        schema_names = {
            "header-v1.json",
            "manifest-v1.json",
            "plan-v1.json",
            "proof-record-v1.json",
            "rpc-record-v1.json",
        }
        for name in schema_names:
            with self.subTest(name=name):
                self.assertEqual(
                    (FIXTURE / "schemas" / name).read_bytes(),
                    (support.PLUGIN_ROOT / "schemas" / name).read_bytes(),
                )
        manifest = load(FIXTURE / "manifest.json")
        declared = {item["path"] for item in manifest["components"]}
        actual = {
            path.relative_to(FIXTURE).as_posix()
            for path in FIXTURE.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        }
        self.assertEqual(declared, actual)
        self.assertNotIn("rpc_url", DEMO_PATH.read_text(encoding="utf-8").lower())


class GoldfinchReceiptProofDemoTests(unittest.TestCase):
    def test_fixed_fixture_proves_the_scoped_receipt_and_log_relations(self):
        report = verify_fixture(RECEIPT_FIXTURE)
        self.assertEqual(
            report["fixture_digest"],
            "aadf1b809ae45946967e17f2132ae4d73b06026345b0e8c7f1ca4c3c0add9535",
        )
        self.assertEqual(
            report["evidence_counts"],
            {
                "proof_backed": 2,
                "header_bound": 1,
                "recorded_rpc": 5,
                "receipt_trie_proved": 2,
            },
        )
        self.assertEqual(report["receipts_root"], RECEIPTS_ROOT)
        relation = report["receipt_trie_proved"]
        self.assertEqual(relation["computed_root"], RECEIPTS_ROOT)
        self.assertEqual(relation["receipt_count"], 224)
        self.assertEqual(relation["target_transaction_index"], "0xbf")
        self.assertEqual(relation["target_log_count"], 110)
        self.assertEqual(relation["filtered_log_count"], 5)
        self.assertEqual(relation["relations"], 2)
        self.assertEqual(relation["transaction_hash_attribution"], "recorded_rpc")

    def test_fixed_fixture_retains_the_verified_raw_source_bytes(self):
        source = support.RECEIPT_PROOF_FIXTURE
        for name in (
            "anchors.jsonl",
            "header.json",
            "plan.json",
            "proofs.jsonl",
            "receipt-witness.json",
            "rpc.jsonl",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    (RECEIPT_FIXTURE / name).read_bytes(),
                    (source / name).read_bytes(),
                )

    def test_manifest_rebuild_is_byte_identical_with_writer_0_2_0(self):
        expected = (RECEIPT_FIXTURE / "manifest.json").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "fixture"
            root.mkdir()
            for component in load(RECEIPT_FIXTURE / "manifest.json")["components"]:
                path = component["path"]
                (root / path).write_bytes((RECEIPT_FIXTURE / path).read_bytes())
            command = [
                sys.executable,
                str(support.PLUGIN_ROOT / "scripts" / "lazarus.py"),
                "build-manifest",
                str(root),
            ]
            for component in load(RECEIPT_FIXTURE / "manifest.json")["components"]:
                command.extend(("--component", component["path"]))
            command.extend(
                (
                    "--chain-id",
                    "0x1",
                    "--block-number",
                    "0xc7da16",
                    "--block-hash",
                    "0x41119192a8acdaae5ab06ca8f1d5943fd7ca2fb0a14323642dd6daf74eed2cfc",
                )
            )
            result = subprocess.run(
                command,
                cwd=support.REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "manifest.json").read_bytes(), expected)

    def test_builder_command_materializes_the_byte_identical_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            rebuilt = Path(directory) / "tmp" / "goldfinch-v1"
            self.assertFalse(rebuilt.parent.exists())
            result = subprocess.run(
                [
                    sys.executable,
                    str(RECEIPT_DEMO_PATH),
                    "build-fixture",
                    "--out",
                    str(rebuilt),
                ],
                cwd=support.REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(rebuilt.is_dir())
            self.assertEqual(
                load_receipt_demo()._tree_bytes(rebuilt),
                load_receipt_demo()._tree_bytes(RECEIPT_FIXTURE),
            )
            event = loads(result.stdout.encode("utf-8"))
            self.assertEqual(event["event"], "goldfinch_fixture_build")
            self.assertEqual(event["stage"], "complete")
            before = load_receipt_demo()._tree_bytes(rebuilt)
            repeated = subprocess.run(
                [
                    sys.executable,
                    str(RECEIPT_DEMO_PATH),
                    "build-fixture",
                    "--out",
                    str(rebuilt),
                ],
                cwd=support.REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
                timeout=20,
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(load_receipt_demo()._tree_bytes(rebuilt), before)
            self.assertEqual(
                list(rebuilt.parent.glob(f".{rebuilt.name}.stage-*")), []
            )
            with self.assertRaises(LazarusError):
                load_receipt_demo().build_fixture(RECEIPT_FIXTURE / "nested")
            self.assertFalse((RECEIPT_FIXTURE / "nested").exists())

    def test_release_verify_command_emits_one_bounded_offline_event(self):
        demo = load_receipt_demo()
        output = StringIO()
        error = StringIO()
        with mock.patch.object(
            demo.socket.socket,
            "connect",
            side_effect=AssertionError("network access"),
        ), mock.patch.object(
            demo.socket,
            "create_connection",
            side_effect=AssertionError("network access"),
        ), mock.patch("sys.stdout", output), mock.patch("sys.stderr", error):
            code = demo.main(
                [
                    "verify-release",
                    "--release",
                    str(demo.SHIPPED_RELEASE),
                ]
            )
        self.assertEqual(code, 0, error.getvalue())
        self.assertEqual(error.getvalue(), "")
        self.assertEqual(
            loads(output.getvalue().encode("utf-8")),
            {
                "event": "goldfinch_release_verify",
                "stage": "complete",
                "fixture_digest": (
                    "aadf1b809ae45946967e17f2132ae4d73b06026345b0e8c7f1ca4c3c0add9535"
                ),
                "release_digest": (
                    "701fa846f81c28ede5ab9539c0c19815dfe7435eca45ba663219c0c88c3bdb74"
                ),
            },
        )

    def test_builder_does_not_require_a_descriptor_filesystem_path(self):
        """The open fixture directory is the authority on every POSIX host."""

        demo = load_receipt_demo()
        real_stat = Path.stat

        def refuse_descriptor_filesystem(path, *args, **kwargs):
            spelling = os.fspath(path)
            if spelling.startswith("/proc/self/fd/") or spelling.startswith(
                "/dev/fd/"
            ):
                raise OSError("descriptor filesystem is not traversable")
            return real_stat(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            Path,
            "stat",
            refuse_descriptor_filesystem,
        ):
            output = Path(directory) / "fixture"
            try:
                report = demo.build_fixture(output)
            except LazarusError as exc:
                self.fail(f"builder required a descriptor filesystem path: {exc}")
            self.assertEqual(
                report["fixture_digest"],
                verify_fixture(output)["fixture_digest"],
            )
            self.assertEqual(
                demo._tree_bytes(output),
                demo._tree_bytes(RECEIPT_FIXTURE),
            )

    def test_builder_refuses_a_missing_descriptor_inventory_capability(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fixture"
            error = StringIO()
            with mock.patch.object(
                demo.os,
                "scandir",
                side_effect=NotImplementedError("private host detail"),
            ), mock.patch("sys.stderr", error):
                try:
                    code = demo.main(["build-fixture", "--out", str(output)])
                except NotImplementedError as exception:
                    self.fail(
                        "builder leaked an unsupported descriptor operation: "
                        f"{exception}"
                    )
            self.assertEqual(code, 1)
            self.assertEqual(
                error.getvalue(),
                "refused: platform lacks secure fixture directory operations\n",
            )
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob(".*.stage-*")), [])
            self.assertNotIn("private host detail", error.getvalue())

    def test_builder_refuses_a_missing_parent_inside_source_without_creating_it(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            shutil.copytree(support.RECEIPT_PROOF_FIXTURE, source)
            output = source / "created-before-refusal" / "fixture"
            with mock.patch.dict(
                demo.build_fixture.__globals__, {"SOURCE_FIXTURE": source}
            ):
                with self.assertRaises(LazarusError):
                    demo.build_fixture(output)
            self.assertFalse(output.parent.exists())

    def test_builder_cli_refusal_is_bounded_and_removes_a_created_parent(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new-parent" / "fixture"
            creator = getattr(demo, "_make_directory_entry", None)
            if callable(creator):
                creation_patch = {
                    "_make_directory_entry": mock.Mock(
                        side_effect=demo.PathError("fixture stage cannot be created")
                    )
                }
            else:
                creation_patch = {
                    "tempfile": SimpleNamespace(
                        mkdtemp=mock.Mock(side_effect=OSError("private host detail"))
                    )
                }
            with mock.patch.dict(demo.build_fixture.__globals__, creation_patch):
                error = StringIO()
                with mock.patch("sys.stderr", error):
                    try:
                        code = demo.main(["build-fixture", "--out", str(output)])
                    except OSError as exception:
                        self.fail(
                            "builder CLI leaked an unhandled "
                            f"{type(exception).__name__}"
                        )
            self.assertEqual(code, 1)
            self.assertEqual(error.getvalue(), "refused: fixture stage cannot be created\n")
            self.assertFalse(output.parent.exists())
            self.assertNotIn("private host detail", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())

    def test_builder_refuses_uninspectable_output_names_inside_its_bounded_surface(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            oversized = Path(directory) / ("x" * 500)
            error = StringIO()
            with mock.patch("sys.stderr", error):
                try:
                    code = demo.main(["build-fixture", "--out", str(oversized)])
                except OSError as exception:
                    self.fail(
                        "builder CLI leaked an unhandled "
                        f"{type(exception).__name__} for an oversized output name"
                    )
            self.assertEqual(code, 1)
            self.assertEqual(error.getvalue(), "refused: fixture output cannot be inspected\n")

            try:
                demo.build_fixture("embedded\x00name")
            except Exception as exception:
                self.assertIsInstance(exception, demo.LazarusError)
                self.assertEqual(str(exception), "fixture output cannot be resolved")
            else:
                self.fail("builder accepted an output name containing NUL")

    def test_output_probe_does_not_depend_on_pathlib_boolean_predicates(self):
        demo = load_receipt_demo()
        output = Path("uninspectable-output")
        with (
            mock.patch.object(Path, "exists", return_value=False),
            mock.patch.object(Path, "is_symlink", return_value=False),
            mock.patch.object(
                Path, "lstat", side_effect=OSError("private host detail")
            ),
        ):
            with self.assertRaisesRegex(
                demo.PathError, "fixture output cannot be inspected"
            ):
                demo._output_exists(output)

    def test_builder_rejects_a_parent_swapped_to_a_source_symlink(self):
        demo = load_receipt_demo()
        real_mkdtemp = tempfile.mkdtemp
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            shutil.copytree(support.RECEIPT_PROOF_FIXTURE, source)
            before = demo._tree_bytes(source)
            parent = root / "output-parent"
            parent.mkdir()
            original_parent = root / "original-output-parent"
            output = parent / "fixture"

            def swap_parent(*, prefix, dir):
                parent.rename(original_parent)
                parent.symlink_to(source, target_is_directory=True)
                return real_mkdtemp(prefix=prefix, dir=dir)

            creator = getattr(demo, "_make_directory_entry", None)
            if callable(creator):
                def swap_after_anchored_creation(directory_fd, prefix):
                    made = creator(directory_fd, prefix)
                    parent.rename(original_parent)
                    parent.symlink_to(source, target_is_directory=True)
                    return made

                creation_patch = {
                    "SOURCE_FIXTURE": source,
                    "_make_directory_entry": swap_after_anchored_creation,
                }
            else:
                creation_patch = {
                    "SOURCE_FIXTURE": source,
                    "tempfile": SimpleNamespace(mkdtemp=swap_parent),
                }
            with mock.patch.dict(
                demo.build_fixture.__globals__,
                creation_patch,
            ):
                with self.assertRaisesRegex(
                    LazarusError, "fixture output parent changed during build"
                ):
                    demo.build_fixture(output)
            self.assertEqual(demo._tree_bytes(source), before)
            self.assertFalse((source / "fixture").exists())
            self.assertEqual(list(source.glob(".*.stage-*")), [])

    def test_builder_rechecks_the_parent_after_each_source_snapshot_read(self):
        demo = load_receipt_demo()
        real_read = demo.read_confined_bytes
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            shutil.copytree(support.RECEIPT_PROOF_FIXTURE, source)
            before = demo._tree_bytes(source)
            parent = root / "output-parent"
            parent.mkdir()
            original_parent = root / "original-output-parent"
            output = parent / "fixture"

            def swap_parent_after_read(*args, **kwargs):
                data = real_read(*args, **kwargs)
                if not parent.is_symlink():
                    parent.rename(original_parent)
                    parent.symlink_to(source, target_is_directory=True)
                return data

            with mock.patch.dict(
                demo.build_fixture.__globals__,
                {
                    "SOURCE_FIXTURE": source,
                    "read_confined_bytes": swap_parent_after_read,
                },
            ):
                error = StringIO()
                with mock.patch("sys.stderr", error):
                    try:
                        code = demo.main(["build-fixture", "--out", str(output)])
                    except OSError as exception:
                        self.fail(
                            "builder CLI leaked an unhandled "
                            f"{type(exception).__name__}"
                        )
            self.assertEqual(code, 1)
            self.assertEqual(
                error.getvalue(),
                "refused: fixture output parent changed during build\n",
            )
            self.assertEqual(demo._tree_bytes(source), before)
            self.assertFalse((source / "fixture").exists())
            self.assertEqual(list(source.glob(".*.stage-*")), [])
            self.assertFalse((original_parent / "fixture").exists())
            self.assertEqual(list(original_parent.glob(".*.stage-*")), [])

    def test_builder_anchors_the_atomic_publish_to_the_open_parent(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            shutil.copytree(support.RECEIPT_PROOF_FIXTURE, source)
            before = demo._tree_bytes(source)
            parent = root / "output-parent"
            parent.mkdir()
            original_parent = root / "original-output-parent"
            output = parent / "fixture"

            anchored = getattr(demo, "_atomic_no_replace_in_directory", None)
            if anchored is None:
                path_finalizer = demo._atomic_no_replace

                def swap_during_path_finalisation(stage, destination):
                    parent.rename(original_parent)
                    parent.symlink_to(source, target_is_directory=True)
                    (source / Path(stage).name).mkdir()
                    return path_finalizer(stage, destination)

                finalizer_patch = {
                    "_atomic_no_replace": swap_during_path_finalisation
                }
            else:
                swapped = False

                def swap_during_anchored_finalisation(
                    stage_directory_fd,
                    stage_name,
                    destination_directory_fd,
                    destination_name,
                ):
                    nonlocal swapped
                    if not swapped and destination_name == output.name:
                        swapped = True
                        parent.rename(original_parent)
                        parent.symlink_to(source, target_is_directory=True)
                    return anchored(
                        stage_directory_fd,
                        stage_name,
                        destination_directory_fd,
                        destination_name,
                    )

                finalizer_patch = {
                    "_atomic_no_replace_in_directory": (
                        swap_during_anchored_finalisation
                    )
                }

            with mock.patch.dict(demo.build_fixture.__globals__, finalizer_patch):
                with self.assertRaisesRegex(
                    LazarusError, "fixture output parent changed during build"
                ):
                    demo.build_fixture(output)
            self.assertEqual(demo._tree_bytes(source), before)
            self.assertFalse((source / "fixture").exists())
            self.assertEqual(list(source.glob(".*.stage-*")), [])
            self.assertFalse((original_parent / "fixture").exists())
            self.assertEqual(list(original_parent.glob(".*.stage-*")), [])

    def test_builder_anchors_stage_writes_to_the_open_directory(self):
        demo = load_receipt_demo()
        real_write = Path.write_bytes
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            shutil.copytree(support.RECEIPT_PROOF_FIXTURE, source)
            parent = root / "output-parent"
            parent.mkdir()
            original_parent = root / "original-output-parent"
            output = parent / "fixture"
            stage_name = ".fixture.stage-fixed"
            source_shadow = source / stage_name
            source_shadow.mkdir()
            before = demo._tree_bytes(source)
            swapped = False

            def fixed_stage(*, prefix, dir):
                self.assertTrue(stage_name.startswith(prefix))
                stage = Path(dir) / stage_name
                stage.mkdir(mode=0o700)
                return str(stage)

            def swap_before_first_write(path, data):
                nonlocal swapped
                if not swapped and path.name == "anchors.jsonl":
                    swapped = True
                    parent.rename(original_parent)
                    parent.symlink_to(source, target_is_directory=True)
                return real_write(path, data)

            creator = getattr(demo, "_make_directory_entry", None)
            if callable(creator):
                def fixed_anchored_stage(directory_fd, prefix):
                    self.assertTrue(stage_name.startswith(prefix))
                    os.mkdir(stage_name, mode=0o700, dir_fd=directory_fd)
                    identity = demo._entry_identity(directory_fd, stage_name)
                    self.assertIsNotNone(identity)
                    return stage_name, identity

                creation_patch = {
                    "_make_directory_entry": fixed_anchored_stage,
                }
                anchored_write = demo._write_new_component

                def swap_before_first_anchored_write(directory_fd, name, data):
                    nonlocal swapped
                    if not swapped and name == "anchors.jsonl":
                        swapped = True
                        parent.rename(original_parent)
                        parent.symlink_to(source, target_is_directory=True)
                    return anchored_write(directory_fd, name, data)

                creation_patch["_write_new_component"] = (
                    swap_before_first_anchored_write
                )
                write_context = mock.patch.object(Path, "write_bytes", real_write)
            else:
                creation_patch = {
                    "tempfile": SimpleNamespace(mkdtemp=fixed_stage),
                }
                write_context = mock.patch.object(
                    Path, "write_bytes", swap_before_first_write
                )

            with mock.patch.dict(
                demo.build_fixture.__globals__,
                creation_patch,
            ), write_context:
                with self.assertRaisesRegex(
                    LazarusError, "fixture output parent changed during build"
                ):
                    demo.build_fixture(output)
            self.assertTrue(swapped)
            self.assertEqual(demo._tree_bytes(source), before)
            self.assertEqual(list(source_shadow.iterdir()), [])
            self.assertFalse((source / "fixture").exists())
            self.assertFalse((original_parent / "fixture").exists())
            self.assertEqual(list(original_parent.glob(".*.stage-*")), [])

    def test_builder_cleanup_failure_stays_inside_the_bounded_cli_surface(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new-parent" / "fixture"
            clearer = getattr(demo, "_clear_anchored_directory", None)
            if callable(clearer):
                cleanup_patch = {
                    "_clear_anchored_directory": mock.Mock(
                        side_effect=demo.PathError("private cleanup detail")
                    )
                }
            else:
                cleanup_patch = {
                    "shutil": SimpleNamespace(
                        rmtree=mock.Mock(side_effect=OSError("private cleanup detail"))
                    )
                }
            with mock.patch.dict(
                demo.build_fixture.__globals__,
                {
                    "write_manifest": mock.Mock(
                        side_effect=demo.IntegrityError("forced build failure")
                    ),
                    **cleanup_patch,
                },
            ):
                error = StringIO()
                with mock.patch("sys.stderr", error):
                    try:
                        code = demo.main(["build-fixture", "--out", str(output)])
                    except OSError as exception:
                        self.fail(
                            "builder CLI leaked an unhandled "
                            f"{type(exception).__name__}"
                        )
            self.assertEqual(code, 1)
            self.assertEqual(error.getvalue(), "refused: fixture stage cleanup failed\n")
            self.assertFalse(output.exists())
            self.assertTrue(output.parent.is_dir())
            self.assertEqual(
                len(list(output.parent.glob(f".{output.name}.stage-*"))), 1
            )
            self.assertNotIn("private cleanup detail", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())

    def test_cleanup_does_not_delete_a_quarantine_replaced_after_its_inode_check(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            stage.mkdir()
            (stage / "owned.txt").write_text("owned", encoding="utf-8")
            displaced = root / "displaced-stage"
            competitor_source = root / "competitor-source"
            competitor_source.mkdir()
            (competitor_source / "keep.txt").write_text("keep", encoding="utf-8")
            parent_fd = demo._open_directory(root)
            identity = demo._entry_identity(parent_fd, stage.name)
            self.assertIsNotNone(identity)
            real_identity = demo._entry_identity
            swapped = False

            def replace_after_quarantine_check(directory_fd, name):
                nonlocal swapped
                observed = real_identity(directory_fd, name)
                if ".cleanup-" in name and observed == identity and not swapped:
                    swapped = True
                    (root / name).rename(displaced)
                    shutil.copytree(competitor_source, root / name)
                return observed

            try:
                with mock.patch.dict(
                    demo._remove_anchored_tree.__globals__,
                    {"_entry_identity": replace_after_quarantine_check},
                ):
                    with self.assertRaisesRegex(
                        LazarusError,
                        "fixture stage cleanup failed|fixture stage identity changed during build",
                    ):
                        demo._remove_anchored_tree(parent_fd, stage.name, identity)
            finally:
                os.close(parent_fd)
            self.assertTrue(swapped)
            quarantines = list(root.glob("stage.cleanup-*"))
            self.assertEqual(len(quarantines), 1)
            self.assertEqual(
                (quarantines[0] / "keep.txt").read_text(encoding="utf-8"),
                "keep",
            )
            self.assertTrue(displaced.is_dir())

    def test_builder_cleans_a_stage_when_the_parent_moves_after_creation(self):
        demo = load_receipt_demo()
        real_mkdtemp = tempfile.mkdtemp
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "output-parent"
            parent.mkdir()
            moved_parent = root / "moved-output-parent"
            output = parent / "fixture"
            creator = getattr(demo, "_make_directory_entry", None)

            if callable(creator):
                def move_after_anchored_creation(directory_fd, prefix):
                    made = creator(directory_fd, prefix)
                    parent.rename(moved_parent)
                    return made

                creation_patch = {
                    "_make_directory_entry": move_after_anchored_creation,
                }
            else:
                def move_after_path_creation(*, prefix, dir):
                    stage = real_mkdtemp(prefix=prefix, dir=dir)
                    parent.rename(moved_parent)
                    return stage

                creation_patch = {
                    "tempfile": SimpleNamespace(mkdtemp=move_after_path_creation),
                }

            with mock.patch.dict(demo.build_fixture.__globals__, creation_patch):
                with self.assertRaisesRegex(
                    LazarusError, "fixture output parent changed during build|fixture stage cannot be created"
                ):
                    demo.build_fixture(output)
            self.assertTrue(moved_parent.is_dir())
            self.assertEqual(list(moved_parent.iterdir()), [])
            self.assertFalse(output.exists())

    def test_builder_refuses_a_staged_symlink_without_overwriting_its_target(self):
        demo = load_receipt_demo()
        real_write = Path.write_bytes
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            parent = root / "output-parent"
            parent.mkdir()
            output = parent / "fixture"
            protected = root / "protected.txt"
            protected.write_bytes(b"private original bytes")
            writer = getattr(demo, "_write_new_component", None)

            if callable(writer):
                planted = False

                def plant_before_anchored_write(directory_fd, name, data):
                    nonlocal planted
                    if not planted and name == "anchors.jsonl":
                        planted = True
                        os.symlink(protected, name, dir_fd=directory_fd)
                    return writer(directory_fd, name, data)

                write_patch = {
                    "_write_new_component": plant_before_anchored_write,
                }
                context = mock.patch.dict(demo.build_fixture.__globals__, write_patch)
            else:
                planted = False

                def plant_before_path_write(path, data):
                    nonlocal planted
                    if not planted and path.name == "anchors.jsonl":
                        planted = True
                        path.symlink_to(protected)
                    return real_write(path, data)

                context = mock.patch.object(Path, "write_bytes", plant_before_path_write)

            with context:
                with self.assertRaises(LazarusError):
                    demo.build_fixture(output)
            self.assertTrue(planted)
            self.assertEqual(protected.read_bytes(), b"private original bytes")
            self.assertFalse(output.exists())
            self.assertEqual(list(parent.iterdir()), [])

    def test_cleanup_does_not_delete_a_tree_replaced_after_the_inode_check(self):
        demo = load_receipt_demo()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            stage = root / "stage"
            stage.mkdir()
            (stage / "owned.txt").write_text("owned", encoding="utf-8")
            displaced = root / "displaced-stage"
            competitor_source = root / "competitor-source"
            competitor_source.mkdir()
            (competitor_source / "keep.txt").write_text("keep", encoding="utf-8")
            parent_fd = demo._open_directory(root)
            identity = demo._entry_identity(parent_fd, stage.name)
            self.assertIsNotNone(identity)
            real_identity = demo._entry_identity
            swapped = False

            def replace_after_check(directory_fd, name):
                nonlocal swapped
                observed = real_identity(directory_fd, name)
                if name == stage.name and not swapped:
                    swapped = True
                    stage.rename(displaced)
                    shutil.copytree(competitor_source, stage)
                return observed

            try:
                with mock.patch.dict(
                    demo._remove_anchored_tree.__globals__,
                    {"_entry_identity": replace_after_check},
                ):
                    with self.assertRaisesRegex(
                        LazarusError, "fixture stage identity changed during build"
                    ):
                        demo._remove_anchored_tree(parent_fd, stage.name, identity)
            finally:
                os.close(parent_fd)
            self.assertTrue(swapped)
            self.assertTrue(stage.is_dir())
            self.assertEqual((stage / "keep.txt").read_text(encoding="utf-8"), "keep")
            self.assertEqual(
                (displaced / "owned.txt").read_text(encoding="utf-8"), "owned"
            )
            self.assertEqual(list(root.glob("stage.cleanup-*")), [])

    def test_recorded_producer_argv_builds_the_fixture_ariadne_captures(self):
        demo = load_receipt_demo()
        runner = getattr(demo, "_run_producer_command", None)
        self.assertTrue(callable(runner))
        with tempfile.TemporaryDirectory() as directory:
            execution_root = Path(directory) / "execution-root"
            rebuilt = runner(execution_root)
            statement = Path(directory) / "statement.json"
            demo._capture_statement(demo._ariadne_module(), rebuilt, statement)
            recorded = load(statement)["predicate"]["capture"]["command"]
            self.assertEqual(recorded, list(demo.PRODUCER_COMMAND))
            self.assertEqual(
                rebuilt.resolve(),
                (execution_root / recorded[-1]).resolve(),
            )
            self.assertEqual(demo._tree_bytes(rebuilt), demo._tree_bytes(RECEIPT_FIXTURE))

    def test_every_fixture_mutation_materializes_before_verification(self):
        demo = load_receipt_demo()
        mutations = {
            "receipt": demo._receipt_mutation,
            "index": demo._index_mutation,
            "log": demo._log_mutation,
            "root": demo._root_mutation,
            "count": demo._count_mutation,
        }
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    changed = workspace / label
                    shutil.copytree(RECEIPT_FIXTURE, changed)
                    before = demo._tree_bytes(changed)
                    try:
                        mutate(changed)
                    except LazarusError as error:
                        self.fail(
                            f"{label} mutation did not materialize: {type(error).__name__}"
                        )
                    after = demo._tree_bytes(changed)
                    self.assertNotEqual(after, before)
                    self.assertNotEqual(
                        after["manifest.json"], before["manifest.json"]
                    )
                    with self.assertRaises(LazarusError):
                        verify_fixture(changed)

            changed = workspace / "log"
            before_log = load(RECEIPT_FIXTURE / "receipt-witness.json")[
                "receipts"
            ][0xBF]["logs"][0]
            after_log = load(changed / "receipt-witness.json")["receipts"][0xBF][
                "logs"
            ][0]
            # ephoros: allow receipt-witness field access is test data, not telemetry
            before_address = bytes.fromhex(before_log["address"][2:])
            # ephoros: allow receipt-witness field access is test data, not telemetry
            after_address = bytes.fromhex(after_log["address"][2:])
            self.assertEqual(len(before_address), len(after_address))
            self.assertEqual(
                sum(left != right for left, right in zip(before_address, after_address)),
                1,
            )

    def test_demo_guards_every_mutation_and_the_transaction_hash_boundary(self):
        report = load_receipt_demo().run_demo()
        self.assertEqual(report["stage"], "complete")
        self.assertEqual(report["network"], "denied")
        self.assertEqual(report.get("fixture_rebuild"), "identical")
        self.assertEqual(
            report.get("producer_command"),
            [
                "python3",
                "plugins/lazarus/examples/goldfinch-v1/demo.py",
                "build-fixture",
                "--out",
                "tmp/goldfinch-v1-rebuild",
            ],
        )
        self.assertEqual(
            report["mutations"],
            {
                "receipt": "rejected",
                "index": "rejected",
                "log": "rejected",
                "root": "rejected",
                "count": "rejected",
                "release": "rejected",
            },
        )
        self.assertEqual(report["coherent_transaction_hash_rewrite"], "unchanged")
        self.assertEqual(
            report["recorded_hash_disagreement"], "rejected-recorded-rpc"
        )
        self.assertEqual(
            report["legacy"],
            {
                "fixture": "d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49",
                "manifest": "c37cd789e5386a1347abd4dff24c8b1db96cdab771df4eb4d63056ba56145fa9",
                "statement": "d8b262278ffd4db76e449a2bfce4629903a70e7f4ad7c1f3a6ebbfb1f112555e",
                "release": "ec5c9b8091286de8713b6daf6cfdeaa7e9cfa6177b96c10a2ed20ffd6654bcff",
            },
        )

    def test_demo_command_emits_one_bounded_structured_event(self):
        result = subprocess.run(
            [sys.executable, str(RECEIPT_DEMO_PATH)],
            cwd=support.REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        event = loads(lines[0].encode("utf-8"))
        self.assertEqual(event["correlation_id"], "goldfinch-v1-offline-demo")
        self.assertEqual(event["relation"]["receipts_root"], RECEIPTS_ROOT)
        self.assertEqual(event["relation"]["proved_relations"], 2)
        self.assertEqual(event["versions"]["writer"], "0.2.0")
        self.assertEqual(
            event["versions"]["statement"],
            "https://ariadne.wildcat.finance/state-fixture/v2",
        )
        serialized = result.stdout.lower()
        forbidden_values = (
            "topics",
            '"data"',
            "rpc_url",
            "rpc-url",
            "credential",
            "bearer",
        )
        for forbidden in forbidden_values:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
