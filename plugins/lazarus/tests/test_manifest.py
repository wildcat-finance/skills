"""Manifest bytes bind every confined fixture component."""

from pathlib import Path
import copy
import os
import tempfile
import unittest
from unittest import mock

from lazarus_lib.canonical import dump, load
from lazarus_lib.errors import FormatError, IntegrityError, PathError, ResourceLimitError
from lazarus_lib.manifest import (
    build_manifest,
    fixture_digest,
    verify_manifest,
    write_manifest,
)
from lazarus_lib.records import (
    make_rpc_record,
    write_anchor_records,
    write_proof_records,
    write_rpc_records,
)

from . import support
from lazarus import run


COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
ANCHORED_COMPONENTS = (*COMPONENTS, "anchors.jsonl")


def write_components(root: Path) -> None:
    dump(root / "plan.json", support.sample_plan())
    dump(root / "header.json", support.sample_header())
    write_rpc_records(
        root / "rpc.jsonl",
        [
            make_rpc_record(
                "eth_chainId",
                [],
                required=True,
                evidence="recorded-rpc",
                result="0x1",
                name="chain-id",
            )
        ],
    )
    write_proof_records(root / "proofs.jsonl", [support.sample_proof_record()])


def write_anchored_components(root: Path, source_ids=("archive-a",)) -> None:
    write_components(root)
    dump(root / "plan.json", support.sample_plan_v2(source_ids))
    write_anchor_records(
        root / "anchors.jsonl",
        [support.sample_anchor_record(source_id) for source_id in source_ids],
    )


def make_manifest(root: Path, components=COMPONENTS):
    manifest = build_manifest(
        root,
        components,
        chain_id="0x1",
        block_number="0x10",
        block_hash=support.hash32("11"),
        evidence_counts={"proof_backed": 2, "header_bound": 1, "recorded_rpc": 1},
    )
    write_manifest(root, manifest)
    return manifest


class ManifestTests(unittest.TestCase):
    def test_manifest_v1_accepts_the_optional_anchor_component_without_new_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_anchored_components(root)
            manifest = make_manifest(root, ANCHORED_COMPONENTS)
            self.assertEqual(
                set(manifest),
                {
                    "schema_version",
                    "tool_version",
                    "chain_id",
                    "block",
                    "components",
                    "evidence_counts",
                    "optional_failures",
                    "fixture_digest",
                },
            )
            self.assertEqual(
                manifest["evidence_counts"],
                {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 1},
            )
            self.assertIn(
                "anchors.jsonl",
                {component["path"] for component in manifest["components"]},
            )
            self.assertEqual(verify_manifest(root), manifest)

    def test_anchor_component_presence_tracks_the_plan_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            dump(root / "plan.json", support.sample_plan_v2())
            with self.assertRaisesRegex(IntegrityError, "plan-v2 requires anchors.jsonl"):
                make_manifest(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            write_anchor_records(
                root / "anchors.jsonl", [support.sample_anchor_record()]
            )
            with self.assertRaisesRegex(IntegrityError, "plan-v1 refuses anchors.jsonl"):
                make_manifest(root, ANCHORED_COMPONENTS)

    def test_repeated_builds_and_writes_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            first = make_manifest(root)
            first_bytes = (root / "manifest.json").read_bytes()
            second = make_manifest(root)
            self.assertEqual(first, second)
            self.assertEqual(first_bytes, (root / "manifest.json").read_bytes())
            self.assertEqual(verify_manifest(root), first)
            self.assertEqual([item["path"] for item in first["components"]], sorted(COMPONENTS))

    def test_same_size_mutation_fails_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            make_manifest(root)
            path = root / "header.json"
            data = path.read_bytes()
            path.write_bytes(data[:-2] + (b" " if data[-2:-1] != b" " else b"x") + data[-1:])
            with self.assertRaisesRegex(IntegrityError, "digest mismatch"):
                verify_manifest(root, validate_formats=False)

    def test_size_mutation_fails_size_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            make_manifest(root)
            with (root / "rpc.jsonl").open("ab") as handle:
                handle.write(b"\n")
            with self.assertRaisesRegex(IntegrityError, "size mismatch"):
                verify_manifest(root, validate_formats=False)

    def test_fixture_digest_is_recomputed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            make_manifest(root)
            manifest = load(root / "manifest.json")
            manifest["fixture_digest"] = "0" * 64
            dump(root / "manifest.json", manifest)
            with self.assertRaisesRegex(IntegrityError, "fixture digest mismatch"):
                verify_manifest(root)

    def test_fixture_digest_binds_counts_and_optional_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            manifest = make_manifest(root)
            original = manifest["fixture_digest"]
            manifest["evidence_counts"]["recorded_rpc"] += 1
            self.assertNotEqual(fixture_digest(manifest), original)
            manifest["evidence_counts"]["recorded_rpc"] -= 1
            manifest["optional_failures"] = ["0" * 64]
            self.assertNotEqual(fixture_digest(manifest), original)

    def test_rebound_false_coverage_claims_fail_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            manifest = make_manifest(root)
            manifest["evidence_counts"]["proof_backed"] = 99999
            manifest["fixture_digest"] = fixture_digest(manifest)
            dump(root / "manifest.json", manifest)
            with self.assertRaisesRegex(IntegrityError, "evidence counts"):
                verify_manifest(root)
            manifest["evidence_counts"]["proof_backed"] = 2
            manifest["optional_failures"] = ["0" * 64]
            manifest["fixture_digest"] = fixture_digest(manifest)
            dump(root / "manifest.json", manifest)
            with self.assertRaisesRegex(IntegrityError, "optional failures"):
                verify_manifest(root)

    def test_noncanonical_manifest_encoding_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            make_manifest(root)
            manifest = load(root / "manifest.json")
            import json
            (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            with self.assertRaisesRegex(IntegrityError, "not canonically encoded"):
                verify_manifest(root)

    def test_extra_and_missing_files_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            make_manifest(root)
            (root / "extra.json").write_text("{}\n")
            with self.assertRaisesRegex(IntegrityError, "unlisted fixture files"):
                verify_manifest(root)
            (root / "extra.json").unlink()
            (root / "header.json").unlink()
            with self.assertRaisesRegex(IntegrityError, "missing fixture files"):
                verify_manifest(root)

    def test_unsafe_and_symlink_components_fail(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            write_components(root)
            with self.assertRaises(PathError):
                build_manifest(
                    root,
                    ["../plan.json"],
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32(),
                )
            external = Path(outside) / "component"
            external.write_text("secret")
            os.symlink(external, root / "linked")
            with self.assertRaisesRegex(PathError, "symlink"):
                build_manifest(
                    root,
                    [*COMPONENTS, "linked"],
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32(),
                )

    def test_component_and_total_resource_limits_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            common = {
                "chain_id": "0x1",
                "block_number": "0x10",
                "block_hash": support.hash32(),
            }
            with self.assertRaises(ResourceLimitError):
                build_manifest(root, COMPONENTS, max_component_bytes=3, **common)
            with self.assertRaises(ResourceLimitError):
                build_manifest(root, COMPONENTS, max_fixture_bytes=7, **common)

    def test_core_components_are_mandatory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "only.json").write_text("{}\n")
            with self.assertRaisesRegex(IntegrityError, "missing required"):
                build_manifest(
                    root,
                    ["only.json"],
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32("11"),
                )

    def test_coverage_is_derived_and_false_claims_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            plan = support.sample_plan()
            plan["requests"].append(
                {
                    "name": "trace",
                    "method": "debug_traceCall",
                    "params": [],
                    "required": False,
                    "evidence": "recorded-rpc",
                }
            )
            dump(root / "plan.json", plan)
            records = [
                make_rpc_record(
                    "eth_chainId",
                    [],
                    required=True,
                    evidence="recorded-rpc",
                    result="0x1",
                    name="chain-id",
                ),
                make_rpc_record(
                    "debug_traceCall",
                    [],
                    required=False,
                    evidence="recorded-rpc",
                    error={"code": -32601, "message": "unavailable"},
                    name="trace",
                ),
            ]
            write_rpc_records(root / "rpc.jsonl", records)
            manifest = build_manifest(
                root,
                COMPONENTS,
                chain_id="0x1",
                block_number="0x10",
                block_hash=support.hash32("11"),
            )
            self.assertEqual(
                manifest["evidence_counts"],
                {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 2},
            )
            self.assertEqual(
                manifest["optional_failures"], [records[1]["request_key"]]
            )
            with self.assertRaisesRegex(IntegrityError, "evidence counts"):
                build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32("11"),
                    evidence_counts={
                        "proof_backed": 99999,
                        "header_bound": 0,
                        "recorded_rpc": 0,
                    },
                )
            with self.assertRaisesRegex(IntegrityError, "optional failures"):
                build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32("11"),
                    optional_failures=[],
                )

    def test_plan_requests_and_records_match_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            common = {
                "chain_id": "0x1",
                "block_number": "0x10",
                "block_hash": support.hash32("11"),
            }
            write_rpc_records(root / "rpc.jsonl", [])
            with self.assertRaisesRegex(IntegrityError, "requests are missing"):
                build_manifest(root, COMPONENTS, **common)
            write_components(root)
            extra = make_rpc_record(
                "eth_blockNumber",
                [],
                required=True,
                evidence="header-bound",
                result="0x10",
                name="block-number",
            )
            existing = make_rpc_record(
                "eth_chainId",
                [],
                required=True,
                evidence="recorded-rpc",
                result="0x1",
                name="chain-id",
            )
            write_rpc_records(root / "rpc.jsonl", [existing, extra])
            with self.assertRaisesRegex(IntegrityError, "unplanned RPC"):
                build_manifest(root, COMPONENTS, **common)
            write_components(root)
            wrong_name = dict(existing, name="not-the-plan-name")
            write_rpc_records(root / "rpc.jsonl", [wrong_name])
            with self.assertRaisesRegex(IntegrityError, "name disagrees"):
                build_manifest(root, COMPONENTS, **common)

    def test_plan_targets_match_proofs_slots_and_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            common = {
                "chain_id": "0x1",
                "block_number": "0x10",
                "block_hash": support.hash32("11"),
            }
            write_proof_records(root / "proofs.jsonl", [])
            with self.assertRaisesRegex(IntegrityError, "proof targets are missing"):
                build_manifest(root, COMPONENTS, **common)
            write_components(root)
            proof = support.sample_proof_record()
            extra = copy.deepcopy(proof)
            extra["address"] = support.address("55")
            write_proof_records(root / "proofs.jsonl", [proof, extra])
            with self.assertRaisesRegex(IntegrityError, "unplanned proof"):
                build_manifest(root, COMPONENTS, **common)
            write_components(root)
            proof = support.sample_proof_record()
            proof["block_hash"] = support.hash32("ff")
            write_proof_records(root / "proofs.jsonl", [proof])
            with self.assertRaisesRegex(IntegrityError, "block hash disagrees"):
                build_manifest(root, COMPONENTS, **common)
            write_components(root)
            proof = support.sample_proof_record()
            proof["storage_proof"][0]["key"] = support.slot("01")
            write_proof_records(root / "proofs.jsonl", [proof])
            with self.assertRaisesRegex(IntegrityError, "slots disagree"):
                build_manifest(root, COMPONENTS, **common)

    def test_manifest_write_replaces_links_without_touching_their_target(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "external"
            external.write_text("keep me")
            write_components(root)
            manifest = build_manifest(
                root,
                COMPONENTS,
                chain_id="0x1",
                block_number="0x10",
                block_hash=support.hash32("11"),
            )
            os.symlink(external, root / "manifest.json")
            write_manifest(root, manifest)
            self.assertEqual(external.read_text(), "keep me")
            self.assertFalse((root / "manifest.json").is_symlink())
            (root / "manifest.json").unlink()
            os.link(external, root / "manifest.json")
            write_manifest(root, manifest)
            self.assertEqual(external.read_text(), "keep me")
            self.assertNotEqual(
                (root / "manifest.json").stat().st_ino, external.stat().st_ino
            )

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are POSIX-only")
    def test_non_regular_fixture_entries_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            make_manifest(root)
            os.mkfifo(root / "unexpected")
            with self.assertRaisesRegex(PathError, "non-regular"):
                verify_manifest(root)

    def test_manifest_identity_and_plan_limits_bind_components(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            with self.assertRaisesRegex(IntegrityError, "block hash"):
                build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32("ff"),
                )
            plan = support.sample_plan()
            plan["limits"]["max_total_bytes"] = 1
            dump(root / "plan.json", plan)
            with self.assertRaisesRegex(ResourceLimitError, "max_total_bytes"):
                build_manifest(
                    root,
                    COMPONENTS,
                    chain_id="0x1",
                    block_number="0x10",
                    block_hash=support.hash32("11"),
                )

    def test_known_component_formats_are_checked_after_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)
            plan = support.sample_plan()
            plan["block"]["number"] = "0x00"
            dump(root / "plan.json", plan)
            with self.assertRaisesRegex(FormatError, "number"):
                make_manifest(root)

    def test_cli_verifies_the_fixture_after_writing_the_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_components(root)

            def write_then_change(fixture, manifest):
                data = write_manifest(fixture, manifest)
                header = root / "header.json"
                original = header.read_bytes()
                header.write_bytes(original[:-2] + b" " + original[-1:])
                return data

            arguments = ["build-manifest", str(root)]
            for component in COMPONENTS:
                arguments.extend(["--component", component])
            arguments.extend(
                [
                    "--chain-id",
                    "0x1",
                    "--block-number",
                    "0x10",
                    "--block-hash",
                    support.hash32("11"),
                ]
            )
            with mock.patch("lazarus.write_manifest", side_effect=write_then_change):
                with self.assertRaisesRegex(IntegrityError, "digest mismatch"):
                    run(arguments)


if __name__ == "__main__":
    unittest.main()
