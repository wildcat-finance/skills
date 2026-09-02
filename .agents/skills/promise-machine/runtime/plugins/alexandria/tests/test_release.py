"""Raw release ingestion and hostile offline verification cases."""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from unittest import mock
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from alexandria_lib.canonical import canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib import paths as path_helpers  # noqa: E402
from alexandria_lib.release import (  # noqa: E402
    MAX_RAW_COMPONENT_BYTES,
    ingest,
    sha256,
    verify,
)


class ReleaseTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture_root = self.root / "input"
        shutil.copytree(FIXTURES, self.fixture_root)
        self.plan_path = self.fixture_root / "capture-plan.json"
        self.release = self.root / "release"

    def tearDown(self):
        self.temporary.cleanup()

    def plan(self):
        return json.loads(self.plan_path.read_text(encoding="utf-8"))

    def write_plan(self, value):
        self.plan_path.write_bytes(canonical_bytes(value))

    def build(self):
        return ingest(self.plan_path, self.release)

    def manifest(self):
        return json.loads((self.release / "manifest.json").read_text(encoding="utf-8"))

    def write_manifest(self, value, *, resign=True):
        if resign:
            unsigned = deepcopy(value)
            unsigned.pop("release_id", None)
            value["release_id"] = sha256(canonical_bytes(unsigned))
        (self.release / "manifest.json").write_bytes(canonical_bytes(value))

    def object_path(self, index=0):
        return self.release / self.manifest()["components"][index]["object_path"]

    def assert_plan_rejected(self, mutate):
        value = self.plan()
        mutate(value)
        self.write_plan(value)
        with self.assertRaises(AlexandriaError):
            self.build()


class IngestTests(ReleaseTestCase):
    def test_exact_source_bytes_are_retained(self):
        self.build()
        manifest = self.manifest()
        by_name = {item["name"]: item for item in manifest["components"]}
        for name, source in (("full-response", "full-dataset.json"), ("subject-logs", "subject-scoped.json")):
            self.assertEqual(
                (self.release / by_name[name]["object_path"]).read_bytes(),
                (self.fixture_root / source).read_bytes(),
            )

    def test_repeat_builds_have_identical_release_truth(self):
        first_id = self.build()
        second = self.root / "second"
        second_id = ingest(self.plan_path, second)
        self.assertEqual(first_id, second_id)
        first_files = {
            path.relative_to(self.release): path.read_bytes()
            for path in self.release.rglob("*") if path.is_file()
        }
        second_files = {
            path.relative_to(second): path.read_bytes()
            for path in second.rglob("*") if path.is_file()
        }
        self.assertEqual(first_files, second_files)

    def test_repeat_ingest_to_same_output_is_idempotent(self):
        expected = self.build()
        before = (self.release / "manifest.json").stat().st_mtime_ns
        self.assertEqual(ingest(self.plan_path, self.release), expected)
        self.assertEqual((self.release / "manifest.json").stat().st_mtime_ns, before)

    def test_components_and_captures_are_sorted(self):
        self.build()
        manifest = self.manifest()
        self.assertEqual([item["name"] for item in manifest["components"]], ["full-response", "subject-logs"])
        self.assertEqual([item["id"] for item in manifest["captures"]], ["full-capture", "subject-capture"])

    def test_release_id_is_manifest_content_digest(self):
        release_id = self.build()
        manifest = self.manifest()
        manifest.pop("release_id")
        self.assertEqual(release_id, sha256(canonical_bytes(manifest)))

    def test_object_path_is_derived_from_digest(self):
        self.build()
        for component in self.manifest()["components"]:
            digest = component["sha256"].split(":", 1)[1]
            self.assertEqual(component["object_path"], f"objects/sha256/{digest[:2]}/{digest}")

    def test_cli_prints_release_id(self):
        result = subprocess.run(
            [sys.executable, str(COMMAND), "ingest", "--plan", str(self.plan_path), "--output", str(self.release)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^sha256:[0-9a-f]{64}\n$")

    def test_partial_build_is_removed_after_validation_failure(self):
        value = self.plan()
        value["captures"][0]["coverage"]["collections"][0]["record_count"] = 99
        value["captures"][0]["coverage"]["record_count"] = 99
        self.write_plan(value)
        with self.assertRaises(AlexandriaError):
            self.build()
        self.assertFalse(self.release.exists())
        self.assertEqual(list(self.root.glob(".release.tmp-*")), [])

    def test_existing_different_release_is_not_overwritten(self):
        self.build()
        original = (self.release / "manifest.json").read_bytes()
        value = self.plan()
        value["release"]["name"] = "different-release"
        self.write_plan(value)
        with self.assertRaises(AlexandriaError):
            ingest(self.plan_path, self.release)
        self.assertEqual((self.release / "manifest.json").read_bytes(), original)


class PlanBoundaryTests(ReleaseTestCase):
    def test_platform_without_safe_open_support_fails_closed(self):
        with mock.patch.object(path_helpers, "SAFE_OPEN_SUPPORTED", False):
            with self.assertRaisesRegex(AlexandriaError, "safe confined reads"):
                self.build()

    def test_capture_plan_fifo_swap_fails_without_blocking(self):
        real_open = path_helpers.os.open
        swapped = False

        def fifo_before_plan_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if path == "capture-plan.json" and kwargs.get("dir_fd") is not None and not swapped:
                swapped = True
                self.plan_path.unlink()
                os.mkfifo(self.plan_path)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(path_helpers.os, "open", side_effect=fifo_before_plan_open):
            with self.assertRaisesRegex(AlexandriaError, "regular file"):
                self.build()

    def test_duplicate_json_keys_are_rejected(self):
        self.plan_path.write_text('{"format":"x","format":"y"}', encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "duplicate key"):
            self.build()

    def test_floats_are_rejected(self):
        self.plan_path.write_text('{"format":1.5}', encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "floating-point"):
            self.build()

    def test_oversized_integers_are_rejected(self):
        self.plan_path.write_text('{"value":' + ('9' * 79) + '}', encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "integer longer"):
            self.build()

    def test_deep_nesting_is_rejected(self):
        data = ("[" * 66 + "0" + "]" * 66).encode()
        with self.assertRaisesRegex(AlexandriaError, "nesting"):
            load_bytes(data, "deep plan")

    def test_unknown_plan_fields_are_rejected(self):
        self.assert_plan_rejected(lambda p: p.update({"surprise": True}))

    def test_source_traversal_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["components"][0].update(path="../outside.json"))

    def test_absolute_source_path_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["components"][0].update(path="/tmp/source.json"))

    def test_source_symlink_is_rejected(self):
        link = self.fixture_root / "linked.json"
        link.symlink_to(self.fixture_root / "subject-scoped.json")
        self.assert_plan_rejected(lambda p: p["components"][0].update(path="linked.json"))

    def test_intermediate_directory_swap_cannot_escape_source_root(self):
        plan = self.plan()
        component = next(item for item in plan["components"] if item["name"] == "full-response")
        nested = self.fixture_root / "nested"
        nested.mkdir()
        original = (self.fixture_root / "full-dataset.json").read_bytes()
        (self.fixture_root / "full-dataset.json").rename(nested / "full-dataset.json")
        component["path"] = "nested/full-dataset.json"
        outside = self.root / "outside"
        outside.mkdir()
        outside_bytes = b'{"data":{"pools":[{"outside":1},{"outside":2}],"repayments":[{"outside":3}]}}\n'
        (outside / "full-dataset.json").write_bytes(outside_bytes)
        self.write_plan(plan)

        real_open = path_helpers.os.open
        swapped = False

        def swap_before_final_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if path == "full-dataset.json" and kwargs.get("dir_fd") is not None and not swapped:
                swapped = True
                saved = self.root / "saved-nested"
                nested.rename(saved)
                nested.symlink_to(outside, target_is_directory=True)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(path_helpers.os, "open", side_effect=swap_before_final_open):
            self.build()
        manifest = self.manifest()
        archived = next(item for item in manifest["components"] if item["name"] == "full-response")
        self.assertEqual((self.release / archived["object_path"]).read_bytes(), original)
        self.assertNotEqual((self.release / archived["object_path"]).read_bytes(), outside_bytes)

    def test_final_fifo_swap_fails_without_blocking(self):
        target = self.fixture_root / "subject-scoped.json"
        real_open = path_helpers.os.open
        swapped = False

        def fifo_before_final_open(path, flags, *args, **kwargs):
            nonlocal swapped
            if path == "subject-scoped.json" and kwargs.get("dir_fd") is not None and not swapped:
                swapped = True
                target.unlink()
                os.mkfifo(target)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(path_helpers.os, "open", side_effect=fifo_before_final_open):
            with self.assertRaisesRegex(AlexandriaError, "regular file"):
                self.build()

    def test_oversized_raw_component_is_rejected_before_read(self):
        oversized = self.fixture_root / "oversized.bin"
        with oversized.open("wb") as handle:
            handle.truncate(MAX_RAW_COMPONENT_BYTES + 1)
        plan = self.plan()
        plan["components"][0]["path"] = "oversized.bin"
        coverage = plan["captures"][0]["coverage"]
        coverage.update(status="failed", record_count=0, collections=[], gaps=["provider response exceeded the local limit"])
        self.write_plan(plan)
        with self.assertRaisesRegex(AlexandriaError, "byte limit"):
            self.build()

    def test_duplicate_component_names_are_rejected(self):
        self.assert_plan_rejected(lambda p: p["components"][1].update(name=p["components"][0]["name"]))

    def test_duplicate_capture_ids_are_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][1].update(id=p["captures"][0]["id"]))

    def test_unknown_component_reference_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][0].update(component="missing"))

    def test_unknown_evidence_class_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][0].update(evidence_class="trust-me"))

    def test_capture_source_is_required_and_preserved(self):
        self.build()
        sources = {item["id"]: item["source"] for item in self.manifest()["captures"]}
        self.assertEqual(sources["full-capture"]["reference"], "full-dataset.json")
        self.assertEqual(sources["subject-capture"]["kind"], "ethereum-logs")

    def test_missing_capture_source_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][0].pop("source"))

    def test_unknown_source_locator_class_is_rejected(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["source"].update(locator_class="somewhere")
        )

    def test_source_reference_refuses_control_characters(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["source"].update(reference="provider\nsecret")
        )

    def test_unknown_finality_class_is_rejected(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["scope"].update(finality="probably-final")
        )

    def test_safe_finality_requires_block_identifiers(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["scope"].update(finality="safe")
        )

    def test_snapshot_block_number_and_hash_are_bound_together(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][1]["scope"]["interval"].update(block_number="123")
        )

    def test_block_range_boundary_hashes_are_bound_together(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["scope"]["interval"].update(
                start_hash="0x" + "1" * 64
            )
        )

    def test_valid_block_identifiers_are_preserved(self):
        value = self.plan()
        value["captures"][0]["scope"]["interval"].update(
            start_hash="0x" + "1" * 64,
            end_hash="0x" + "2" * 64,
        )
        value["captures"][1]["scope"]["interval"].update(
            block_number="15900000",
            block_hash="0x" + "3" * 64,
        )
        self.write_plan(value)
        self.build()
        intervals = {item["id"]: item["scope"]["interval"] for item in self.manifest()["captures"]}
        self.assertEqual(intervals["subject-capture"]["end_hash"], "0x" + "2" * 64)
        self.assertEqual(intervals["full-capture"]["block_number"], "15900000")

    def test_non_string_enum_values_fail_cleanly(self):
        baseline = self.plan()
        mutators = {
            "access": lambda p: p["components"][0].update(access=[]),
            "redistribution": lambda p: p["components"][0].update(redistribution={}),
            "evidence": lambda p: p["captures"][0].update(evidence_class=[]),
            "locator": lambda p: p["captures"][0]["source"].update(locator_class={}),
            "scope": lambda p: p["captures"][0]["scope"].update(kind=[]),
            "finality": lambda p: p["captures"][0]["scope"].update(finality={}),
            "coverage": lambda p: p["captures"][0]["coverage"].update(status=[]),
        }
        for label, mutate in mutators.items():
            with self.subTest(label=label):
                value = deepcopy(baseline)
                mutate(value)
                self.write_plan(value)
                with self.assertRaises(AlexandriaError):
                    self.build()

    def test_full_dataset_scope_refuses_subjects(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["scope"].update(subjects=["eip155:1:0x" + "1" * 40]))

    def test_subject_scope_requires_subjects(self):
        def mutate(plan):
            del plan["captures"][0]["scope"]["subjects"]
        self.assert_plan_rejected(mutate)

    def test_subject_must_match_capture_chain(self):
        self.assert_plan_rejected(lambda p: p["captures"][0]["scope"].update(subjects=["eip155:10:0x" + "1" * 40]))

    def test_subject_must_be_lowercase(self):
        self.assert_plan_rejected(lambda p: p["captures"][0]["scope"].update(subjects=["eip155:1:0x" + "A" * 40]))

    def test_non_string_subject_fails_cleanly(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["scope"].update(subjects=[{}])
        )

    def test_block_range_must_be_canonical_decimal(self):
        self.assert_plan_rejected(lambda p: p["captures"][0]["scope"]["interval"].update(start="0x100"))

    def test_block_range_must_be_ordered(self):
        self.assert_plan_rejected(lambda p: p["captures"][0]["scope"]["interval"].update(start="258", end="257"))

    def test_overlong_block_number_fails_cleanly(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][0]["scope"]["interval"].update(end="9" * 5000)
        )

    def test_snapshot_requires_utc_whole_seconds(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["scope"]["interval"].update(observed_at="2022-11-04T00:00:00.1Z"))

    def test_unknown_interval_kind_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["scope"].update(interval={"kind": "forever"}))

    def test_inflated_collection_count_is_rejected(self):
        def mutate(plan):
            coverage = plan["captures"][1]["coverage"]
            coverage["collections"][0]["record_count"] = 3
            coverage["record_count"] = 4
        self.assert_plan_rejected(mutate)

    def test_raw_json_numbers_do_not_narrow_preserved_bytes(self):
        path = self.fixture_root / "full-dataset.json"
        original = path.read_text(encoding="utf-8").rstrip()
        raw = (
            original[:-1]
            + ',"ratio":1.25,"very_large":'
            + "9" * 5000
            + "}\n"
        ).encode()
        path.write_bytes(raw)
        self.build()
        component = next(
            item for item in self.manifest()["components"] if item["name"] == "full-response"
        )
        self.assertEqual((self.release / component["object_path"]).read_bytes(), raw)

    def test_duplicate_keys_in_raw_json_are_rejected_for_coverage(self):
        path = self.fixture_root / "full-dataset.json"
        path.write_text(
            '{"data":{"pools":[],"pools":[],"repayments":[]}}\n',
            encoding="utf-8",
        )
        with self.assertRaisesRegex(AlexandriaError, "duplicate key"):
            self.build()

    def test_inflated_total_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["coverage"].update(record_count=4))

    def test_unresolved_selector_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["coverage"]["collections"][0].update(selector="/data/missing"))

    def test_duplicate_selectors_cannot_inflate_coverage(self):
        def mutate(plan):
            coverage = plan["captures"][1]["coverage"]
            coverage["collections"][1]["selector"] = coverage["collections"][0]["selector"]
            coverage["collections"][1]["record_count"] = 2
            coverage["record_count"] = 4
        self.assert_plan_rejected(mutate)

    def test_selector_must_resolve_to_list(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["coverage"]["collections"][0].update(selector="/data"))

    def test_complete_coverage_refuses_unsupported_collections(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["coverage"].update(unsupported_collections=["defaults"]))

    def test_complete_coverage_requires_a_counted_collection(self):
        def mutate(plan):
            plan["captures"][1]["coverage"].update(record_count=0, collections=[])
        self.assert_plan_rejected(mutate)

    def test_partial_coverage_records_unsupported_collections(self):
        value = self.plan()
        value["captures"][1]["coverage"].update(status="partial", unsupported_collections=["defaults"])
        self.write_plan(value)
        self.assertRegex(self.build(), r"^sha256:")

    def test_partial_coverage_requires_negative_space(self):
        self.assert_plan_rejected(lambda p: p["captures"][1]["coverage"].update(status="partial"))

    def test_failed_coverage_records_a_gap_without_counted_rows(self):
        value = self.plan()
        coverage = value["captures"][1]["coverage"]
        coverage.update(status="failed", record_count=0, collections=[], gaps=["provider request failed"])
        self.write_plan(value)
        self.assertRegex(self.build(), r"^sha256:")

    def test_unsupported_coverage_records_a_gap_without_counted_rows(self):
        value = self.plan()
        coverage = value["captures"][1]["coverage"]
        coverage.update(status="unsupported", record_count=0, collections=[], gaps=["source kind is not supported"])
        self.write_plan(value)
        self.assertRegex(self.build(), r"^sha256:")

    def test_failed_coverage_requires_a_gap_reason(self):
        def mutate(plan):
            plan["captures"][1]["coverage"].update(status="failed", record_count=0, collections=[])
        self.assert_plan_rejected(mutate)

    def test_component_access_class_is_required_and_preserved(self):
        self.build()
        self.assertEqual({item["access"] for item in self.manifest()["components"]}, {"public"})
        self.assertEqual(
            {item["redistribution"] for item in self.manifest()["components"]},
            {"permitted"},
        )

    def test_missing_component_access_class_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["components"][0].pop("access"))

    def test_unknown_component_access_class_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["components"][0].update(access="probably-public"))

    def test_missing_component_redistribution_class_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["components"][0].pop("redistribution"))

    def test_unknown_component_redistribution_class_is_rejected(self):
        self.assert_plan_rejected(
            lambda p: p["components"][0].update(redistribution="probably-permitted")
        )

    def test_json_pointer_refuses_a_trailing_tilde_escape(self):
        self.assert_plan_rejected(
            lambda p: p["captures"][1]["coverage"]["collections"][0].update(selector="/data/pools~")
        )

    def test_valid_correction_links_are_preserved(self):
        value = self.plan()
        prior = "sha256:" + "1" * 64
        value["release"]["correction"] = {"supersedes": [prior], "reason": "Corrected capture boundary"}
        self.write_plan(value)
        self.build()
        self.assertEqual(self.manifest()["release"]["correction"]["supersedes"], [prior])

    def test_malformed_supersedes_link_is_rejected(self):
        self.assert_plan_rejected(lambda p: p["release"].update(correction={"supersedes": ["latest"], "reason": "fix"}))

    def test_non_string_supersedes_link_fails_cleanly(self):
        self.assert_plan_rejected(
            lambda p: p["release"].update(correction={"supersedes": [{}], "reason": "fix"})
        )

    def test_duplicate_supersedes_links_are_rejected(self):
        prior = "sha256:" + "1" * 64
        self.assert_plan_rejected(lambda p: p["release"].update(correction={"supersedes": [prior, prior], "reason": "fix"}))


class VerifyTests(ReleaseTestCase):
    def test_verify_returns_release_id(self):
        expected = self.build()
        self.assertEqual(verify(self.release), expected)

    def test_cli_verify_prints_release_id(self):
        expected = self.build()
        result = subprocess.run([sys.executable, str(COMMAND), "verify", str(self.release)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, expected + "\n")

    def test_noncanonical_manifest_is_rejected(self):
        self.build()
        path = self.release / "manifest.json"
        path.write_text(json.dumps(self.manifest(), indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "not canonical"):
            verify(self.release)

    def test_manifest_identity_tamper_is_rejected(self):
        self.build()
        value = self.manifest()
        value["release"]["name"] = "tampered"
        self.write_manifest(value, resign=False)
        with self.assertRaisesRegex(AlexandriaError, "identity"):
            verify(self.release)

    def test_undeclared_release_file_is_rejected(self):
        self.build()
        (self.release / "notes.txt").write_text("not bound\n", encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "undeclared entry"):
            verify(self.release)

    def test_undeclared_release_directory_is_rejected(self):
        self.build()
        (self.release / "scratch").mkdir()
        with self.assertRaisesRegex(AlexandriaError, "undeclared entry"):
            verify(self.release)

    def test_object_byte_tamper_is_rejected(self):
        self.build()
        path = self.object_path()
        path.write_bytes(path.read_bytes() + b"x")
        with self.assertRaises(AlexandriaError):
            verify(self.release)

    def test_component_size_tamper_is_rejected(self):
        self.build()
        value = self.manifest()
        value["components"][0]["bytes"] += 1
        self.write_manifest(value)
        with self.assertRaisesRegex(AlexandriaError, "byte count"):
            verify(self.release)

    def test_component_digest_tamper_is_rejected(self):
        self.build()
        value = self.manifest()
        value["components"][0]["sha256"] = "sha256:" + "0" * 64
        value["components"][0]["object_path"] = "objects/sha256/00/" + "0" * 64
        self.write_manifest(value)
        with self.assertRaises(AlexandriaError):
            verify(self.release)

    def test_digest_key_mismatch_is_rejected(self):
        self.build()
        value = self.manifest()
        value["components"][0]["object_path"] = "objects/sha256/00/" + "0" * 64
        self.write_manifest(value)
        with self.assertRaisesRegex(AlexandriaError, "path does not match"):
            verify(self.release)

    def test_capture_component_digest_mismatch_is_rejected(self):
        self.build()
        value = self.manifest()
        value["captures"][0]["component_sha256"] = "sha256:" + "0" * 64
        self.write_manifest(value)
        with self.assertRaisesRegex(AlexandriaError, "component digest"):
            verify(self.release)

    def test_manifest_object_traversal_is_rejected(self):
        self.build()
        value = self.manifest()
        value["components"][0]["object_path"] = "../outside"
        self.write_manifest(value)
        with self.assertRaises(AlexandriaError):
            verify(self.release)

    def test_object_symlink_is_rejected(self):
        self.build()
        path = self.object_path()
        saved = self.root / "saved-object"
        path.rename(saved)
        path.symlink_to(saved)
        with self.assertRaisesRegex(AlexandriaError, "symlink"):
            verify(self.release)

    def test_manifest_symlink_is_rejected(self):
        self.build()
        path = self.release / "manifest.json"
        saved = self.root / "saved-manifest"
        path.rename(saved)
        path.symlink_to(saved)
        with self.assertRaisesRegex(AlexandriaError, "symlink"):
            verify(self.release)

    def test_self_supersedes_is_rejected(self):
        self.build()
        value = self.manifest()
        value["release"]["correction"] = {"supersedes": [value["release_id"]], "reason": "loop"}
        self.write_manifest(value, resign=False)
        with self.assertRaisesRegex(AlexandriaError, "supersede itself"):
            verify(self.release)

    def test_verify_does_not_open_network_socket(self):
        expected = self.build()
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            self.assertEqual(verify(self.release), expected)

    def test_verify_does_not_change_release(self):
        self.build()
        before = {path: (path.stat().st_mtime_ns, path.read_bytes()) for path in self.release.rglob("*") if path.is_file()}
        verify(self.release)
        after = {path: (path.stat().st_mtime_ns, path.read_bytes()) for path in self.release.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_verify_accepts_read_only_release_tree(self):
        expected = self.build()
        paths = sorted(self.release.rglob("*"), reverse=True) + [self.release]
        original = {path: stat.S_IMODE(path.stat().st_mode) for path in paths}
        try:
            for path in paths:
                path.chmod(0o555 if path.is_dir() else 0o444)
            self.assertEqual(verify(self.release), expected)
        finally:
            for path in reversed(paths):
                path.chmod(original[path])

    def test_verify_recounts_coverage_from_raw_bytes(self):
        self.build()
        value = self.manifest()
        value["captures"][0]["coverage"]["collections"][0]["record_count"] += 1
        value["captures"][0]["coverage"]["record_count"] += 1
        self.write_manifest(value)
        with self.assertRaisesRegex(AlexandriaError, "declares"):
            verify(self.release)


class CanonicalJsonTests(unittest.TestCase):
    def test_canonical_bytes_sort_keys_and_add_one_newline(self):
        self.assertEqual(canonical_bytes({"z": 1, "a": "é"}), '{"a":"é","z":1}\n'.encode())

    def test_canonical_bytes_refuses_floats(self):
        with self.assertRaises(AlexandriaError):
            canonical_bytes({"amount": 1.0})

    def test_canonical_bytes_refuses_overlong_programmatic_integer(self):
        with self.assertRaisesRegex(AlexandriaError, "integer longer"):
            canonical_bytes({"amount": 10 ** 78})

    def test_canonical_bytes_refuses_lone_surrogates(self):
        with self.assertRaises(AlexandriaError):
            canonical_bytes({"reason": "\ud800"})

    def test_parser_refuses_nonfinite_numbers(self):
        with self.assertRaises(AlexandriaError):
            load_bytes(b'{"amount":NaN}')

    def test_parser_refuses_utf8_bom(self):
        with self.assertRaises(AlexandriaError):
            load_bytes(b'\xef\xbb\xbf{}')


if __name__ == "__main__":
    unittest.main()
