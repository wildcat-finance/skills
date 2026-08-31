"""Focused guards for the checked-input admission boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "scripts" / "homologia.py"
FIXTURES = PLUGIN / "tests" / "fixtures" / "check"
EXAMPLE = PLUGIN / "examples" / "wad-interest-v0"
MANIFEST_SCHEMA = PLUGIN / "references" / "manifest-v1.schema.json"
VECTOR_SCHEMA = PLUGIN / "references" / "vectors-v1.schema.json"

SPEC = importlib.util.spec_from_file_location("homologia_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
HOMOLOGIA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOMOLOGIA)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(FIXTURES / "valid", self.root / "case")
        self.manifest_path = self.root / "case" / "manifest.json"
        self.vectors_path = self.root / "case" / "vectors.jsonl"
        self.output_path = self.root / "build" / "checked.json"

    def manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def write_manifest(self, value: dict) -> None:
        self.manifest_path.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    def vectors(self) -> list[dict]:
        return [
            json.loads(line)
            for line in self.vectors_path.read_text(encoding="utf-8").splitlines()
        ]

    def write_vectors(self, values: list[dict], path: Path | None = None) -> None:
        target = path or self.vectors_path
        target.write_text(
            "".join(json.dumps(value, sort_keys=True) + "\n" for value in values),
            encoding="utf-8",
        )

    def check(self, *, limits=None):
        kwargs = {"root": self.root}
        if limits is not None:
            kwargs["limits"] = limits
        return HOMOLOGIA.check_manifest(
            "case/manifest.json", "build/checked.json", **kwargs
        )

    def assert_refuses(self, code: str, *, limits=None) -> HOMOLOGIA.Refusal:
        with self.assertRaises(HOMOLOGIA.Refusal) as raised:
            self.check(limits=limits)
        self.assertEqual(raised.exception.code, code)
        self.assertFalse(self.output_path.exists())
        return raised.exception

    def test_proved_answer_requires_a_lazarus_artefact(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {"class": "proved"}
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-PROVENANCE")

    def test_proved_answer_with_a_safe_lazarus_artefact_is_admitted(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {
            "class": "proved",
            "lazarus_artifact": "plugins/lazarus/fixtures/state-v1",
        }
        self.write_vectors([vector])
        result = self.check()
        self.assertEqual(result.record["vector_sets"][0]["vectors"][0], vector)

    def test_recorded_answer_requires_chain_and_block_identity(self):
        vector = self.vectors()[0]
        for missing in ("chain_id", "block_number", "block_hash"):
            with self.subTest(missing=missing):
                provenance = {
                    "class": "recorded",
                    "chain_id": "1",
                    "block_number": "100",
                    "block_hash": "0x" + "2" * 64,
                }
                del provenance[missing]
                vector["expected"]["provenance"] = provenance
                self.write_vectors([vector])
                self.assert_refuses("HOM-CHECK-PROVENANCE")

    def test_recorded_answer_is_admitted(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {
            "class": "recorded",
            "chain_id": "1",
            "block_number": "100",
            "block_hash": "0x" + "2" * 64,
        }
        self.write_vectors([vector])
        self.check()

    def test_recorded_answer_chain_must_match_the_pair(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {
            "class": "recorded",
            "chain_id": "43114",
            "block_number": "100",
            "block_hash": "0x" + "2" * 64,
        }
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-PROVENANCE")

    def test_asserted_answer_requires_a_named_author(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {"class": "asserted"}
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-PROVENANCE")

    def test_unknown_provenance_refuses(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {"class": "assumed"}
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-PROVENANCE")

    def test_missing_mirror_scale_refuses(self):
        manifest = self.manifest()
        del manifest["pair"]["mirror"]["scale"]
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-SHAPE")

    def test_missing_vector_set_scale_refuses(self):
        manifest = self.manifest()
        del manifest["vector_sets"][0]["scale"]
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-SHAPE")

    def test_unequal_scale_id_refuses(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["scale"]["id"] = "ray"
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-SCALE")

    def test_unequal_scale_decimals_refuses(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["scale"]["decimals"] = 27
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-SCALE")

    def test_duplicate_vector_set_id_refuses(self):
        manifest = self.manifest()
        duplicate = dict(manifest["vector_sets"][0])
        duplicate["path"] = "second.jsonl"
        shutil.copyfile(self.vectors_path, self.root / "case" / "second.jsonl")
        manifest["vector_sets"].append(duplicate)
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-DUPLICATE")

    def test_duplicate_vector_path_refuses(self):
        manifest = self.manifest()
        duplicate = dict(manifest["vector_sets"][0])
        duplicate["id"] = "second"
        manifest["vector_sets"].append(duplicate)
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-DUPLICATE")

    def test_filesystem_alias_of_a_vector_path_refuses(self):
        alias = self.root / "case" / "vectors-alias.jsonl"
        os.link(self.vectors_path, alias)
        manifest = self.manifest()
        duplicate = dict(manifest["vector_sets"][0])
        duplicate["id"] = "alias"
        duplicate["path"] = alias.name
        manifest["vector_sets"].append(duplicate)
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-DUPLICATE")

    def test_absolute_vector_path_refuses(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["path"] = str(self.vectors_path)
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-PATH")

    def test_parent_vector_path_refuses(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["path"] = "../vectors.jsonl"
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-PATH")

    def test_backslash_vector_path_refuses(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["path"] = "nested\\vectors.jsonl"
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-PATH")

    def test_symlink_vector_path_refuses(self):
        real = self.root / "case" / "real.jsonl"
        self.vectors_path.replace(real)
        self.vectors_path.symlink_to(real.name)
        self.assert_refuses("HOM-CHECK-PATH")

    @unittest.skipUnless(
        hasattr(os, "mkfifo") and hasattr(os, "O_NONBLOCK"),
        "FIFO non-blocking reads require POSIX support",
    )
    def test_fifo_manifest_refuses_without_blocking(self):
        self.manifest_path.unlink()
        os.mkfifo(self.manifest_path)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "check",
                    "--manifest",
                    "case/manifest.json",
                    "--out",
                    "build/checked.json",
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self.fail("a FIFO input blocked before the regular-file refusal")
        self.assertEqual(result.returncode, HOMOLOGIA.INPUT_REFUSED)
        self.assertEqual(json.loads(result.stderr)["code"], "HOM-CHECK-PATH")
        self.assertFalse(self.output_path.exists())

    def test_malformed_manifest_refuses(self):
        shutil.copyfile(FIXTURES / "malformed-manifest.json", self.manifest_path)
        self.assert_refuses("HOM-CHECK-JSON")

    def test_malformed_jsonl_refuses(self):
        shutil.copyfile(FIXTURES / "malformed-vectors.jsonl", self.vectors_path)
        self.assert_refuses("HOM-CHECK-JSON")

    def test_unicode_line_separators_inside_json_strings_are_data(self):
        original = self.vectors()[0]
        for separator in ("\u0085", "\u2028", "\u2029"):
            with self.subTest(separator=ord(separator)):
                vector = json.loads(json.dumps(original))
                author = f"Wildcat{separator}Labs"
                vector["expected"]["provenance"]["author"] = author
                self.vectors_path.write_text(
                    json.dumps(vector, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                result = self.check()
                checked_author = result.record["vector_sets"][0]["vectors"][0][
                    "expected"
                ]["provenance"]["author"]
                self.assertEqual(checked_author, author)

    def test_bare_carriage_return_is_not_a_jsonl_record_separator(self):
        first = self.vectors()[0]
        second = json.loads(json.dumps(first))
        second["id"] = "second"
        self.vectors_path.write_text(
            json.dumps(first, sort_keys=True) + "\r" + json.dumps(second, sort_keys=True),
            encoding="utf-8",
        )
        self.assert_refuses("HOM-CHECK-JSON")

    def test_crlf_separates_jsonl_records(self):
        first = self.vectors()[0]
        second = json.loads(json.dumps(first))
        second["id"] = "second"
        self.vectors_path.write_text(
            json.dumps(first, sort_keys=True)
            + "\r\n"
            + json.dumps(second, sort_keys=True)
            + "\r\n",
            encoding="utf-8",
        )
        result = self.check()
        self.assertEqual(result.record["vector_sets"][0]["vector_count"], 2)

    def test_duplicate_json_key_refuses(self):
        shutil.copyfile(FIXTURES / "duplicate-key-vectors.jsonl", self.vectors_path)
        self.assert_refuses("HOM-CHECK-JSON")

    def test_duplicate_manifest_key_refuses(self):
        self.manifest_path.write_text(
            '{"schema":"homologia-manifest/v1","schema":"other"}\n',
            encoding="utf-8",
        )
        self.assert_refuses("HOM-CHECK-JSON")

    def test_unpaired_unicode_escape_refuses_stably_and_preserves_output(self):
        manifest = self.manifest()
        manifest["pair"]["chain"]["function"] = "\ud800"
        self.write_manifest(manifest)
        self.output_path.parent.mkdir(parents=True)
        self.output_path.write_bytes(b"sentinel\n")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "check",
                "--manifest",
                "case/manifest.json",
                "--out",
                "build/checked.json",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, HOMOLOGIA.INPUT_REFUSED)
        self.assertEqual(json.loads(result.stderr)["code"], "HOM-CHECK-JSON")
        self.assertEqual(self.output_path.read_bytes(), b"sentinel\n")

    def test_oversized_json_integer_refuses_stably_and_preserves_output(self):
        manifest = self.manifest_path.read_text(encoding="utf-8")
        manifest = manifest.replace('"decimals": 18', '"decimals": ' + "1" * 5000)
        self.manifest_path.write_text(manifest, encoding="utf-8")
        self.output_path.parent.mkdir(parents=True)
        self.output_path.write_bytes(b"sentinel\n")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "check",
                "--manifest",
                "case/manifest.json",
                "--out",
                "build/checked.json",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, HOMOLOGIA.INPUT_REFUSED)
        self.assertEqual(json.loads(result.stderr)["code"], "HOM-CHECK-JSON")
        self.assertEqual(self.output_path.read_bytes(), b"sentinel\n")

    def test_non_canonical_input_integer_refuses(self):
        vector = self.vectors()[0]
        vector["inputs"]["principal"] = "01"
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-INTEGER")

    def test_non_canonical_expected_integer_refuses(self):
        vector = self.vectors()[0]
        vector["expected"]["integer"] = "-0"
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-INTEGER")

    def test_undeclared_tolerance_refuses(self):
        vector = self.vectors()[0]
        vector["tolerance"] = {"absolute": "1"}
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-TOLERANCE")

    def test_unequal_tolerance_refuses(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["tolerance"] = {"absolute": "1"}
        self.write_manifest(manifest)
        vector = self.vectors()[0]
        vector["tolerance"] = {"absolute": "2"}
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-TOLERANCE")

    def test_declared_tolerance_is_admitted(self):
        manifest = self.manifest()
        manifest["vector_sets"][0]["tolerance"] = {"absolute": "1"}
        self.write_manifest(manifest)
        vector = self.vectors()[0]
        vector["tolerance"] = {"absolute": "1"}
        self.write_vectors([vector])
        self.check()

    def test_duplicate_vector_id_refuses(self):
        vector = self.vectors()[0]
        self.write_vectors([vector, vector])
        self.assert_refuses("HOM-CHECK-DUPLICATE")

    def test_empty_vector_file_refuses(self):
        self.vectors_path.write_bytes(b"")
        self.assert_refuses("HOM-CHECK-SHAPE")

    def test_per_file_cap_refuses(self):
        limits = HOMOLOGIA.Limits(
            max_vector_sets=16,
            max_vectors_per_set=100_000,
            max_file_bytes=self.vectors_path.stat().st_size - 1,
            max_aggregate_bytes=64 * 1024 * 1024,
        )
        self.assert_refuses("HOM-CHECK-FILE-CAP", limits=limits)

    def test_aggregate_cap_refuses(self):
        total = self.manifest_path.stat().st_size + self.vectors_path.stat().st_size
        limits = HOMOLOGIA.Limits(
            max_vector_sets=16,
            max_vectors_per_set=100_000,
            max_file_bytes=8 * 1024 * 1024,
            max_aggregate_bytes=total - 1,
        )
        self.assert_refuses("HOM-CHECK-AGGREGATE-CAP", limits=limits)

    def test_vector_set_count_cap_refuses(self):
        limits = HOMOLOGIA.Limits(
            max_vector_sets=0,
            max_vectors_per_set=100_000,
            max_file_bytes=8 * 1024 * 1024,
            max_aggregate_bytes=64 * 1024 * 1024,
        )
        self.assert_refuses("HOM-CHECK-SET-CAP", limits=limits)

    def test_vector_count_cap_refuses(self):
        limits = HOMOLOGIA.Limits(
            max_vector_sets=16,
            max_vectors_per_set=0,
            max_file_bytes=8 * 1024 * 1024,
            max_aggregate_bytes=64 * 1024 * 1024,
        )
        self.assert_refuses("HOM-CHECK-VECTOR-CAP", limits=limits)

    def test_refusal_preserves_existing_output(self):
        self.output_path.parent.mkdir(parents=True)
        self.output_path.write_bytes(b"sentinel\n")
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {"class": "proved"}
        self.write_vectors([vector])
        with self.assertRaises(HOMOLOGIA.Refusal):
            self.check()
        self.assertEqual(self.output_path.read_bytes(), b"sentinel\n")

    def test_output_symlink_refuses_without_changing_its_target(self):
        target = self.root / "target.json"
        target.write_bytes(b"sentinel\n")
        self.output_path.parent.mkdir(parents=True)
        self.output_path.symlink_to(target)
        with self.assertRaises(HOMOLOGIA.Refusal) as raised:
            self.check()
        self.assertEqual(raised.exception.code, "HOM-CHECK-PATH")
        self.assertEqual(target.read_bytes(), b"sentinel\n")

    def test_output_cannot_replace_the_manifest_input(self):
        original = self.manifest_path.read_bytes()
        with self.assertRaises(HOMOLOGIA.Refusal) as raised:
            HOMOLOGIA.check_manifest(
                "case/manifest.json", "case/manifest.json", root=self.root
            )
        self.assertEqual(raised.exception.code, "HOM-CHECK-PATH")
        self.assertEqual(self.manifest_path.read_bytes(), original)

    def test_output_case_alias_cannot_replace_the_manifest_input(self):
        alias = self.root / "case" / "MANIFEST.JSON"
        if not alias.exists():
            self.skipTest("filesystem is case-sensitive")
        original = self.manifest_path.read_bytes()
        with self.assertRaises(HOMOLOGIA.Refusal) as raised:
            HOMOLOGIA.check_manifest(
                "case/manifest.json", "case/MANIFEST.JSON", root=self.root
            )
        self.assertEqual(raised.exception.code, "HOM-CHECK-PATH")
        self.assertEqual(self.manifest_path.read_bytes(), original)

    def test_output_cannot_replace_a_vector_input(self):
        original = self.vectors_path.read_bytes()
        with self.assertRaises(HOMOLOGIA.Refusal) as raised:
            HOMOLOGIA.check_manifest(
                "case/manifest.json", "case/vectors.jsonl", root=self.root
            )
        self.assertEqual(raised.exception.code, "HOM-CHECK-PATH")
        self.assertEqual(self.vectors_path.read_bytes(), original)

    def test_mixed_sets_are_admitted(self):
        manifest = self.manifest()
        second = {
            "id": "recorded-small",
            "path": "recorded.jsonl",
            "scale": {"id": "wad", "decimals": 18},
        }
        manifest["vector_sets"].append(second)
        self.write_manifest(manifest)
        vector = self.vectors()[0]
        vector["id"] = "recorded-one"
        vector["expected"]["provenance"] = {
            "class": "recorded",
            "chain_id": "1",
            "block_number": "100",
            "block_hash": "0x" + "2" * 64,
        }
        self.write_vectors([vector], self.root / "case" / "recorded.jsonl")
        result = self.check()
        self.assertEqual(result.record["summary"], {"vector_count": 2, "vector_set_count": 2})

    def test_checked_record_is_canonical_and_repeatable(self):
        first = self.check()
        first_bytes = self.output_path.read_bytes()
        second_path = self.root / "build" / "second.json"
        second = HOMOLOGIA.check_manifest(
            "case/manifest.json", "build/second.json", root=self.root
        )
        self.assertEqual(first_bytes, second_path.read_bytes())
        self.assertEqual(first.output_sha256, second.output_sha256)
        self.assertTrue(first_bytes.endswith(b"\n"))
        self.assertEqual(
            first_bytes,
            (json.dumps(first.record, sort_keys=True, separators=(",", ":")) + "\n").encode(),
        )

    def test_checked_record_binds_source_digests(self):
        result = self.check()
        self.assertEqual(
            result.record["manifest"]["sha256"],
            hashlib.sha256(self.manifest_path.read_bytes()).hexdigest(),
        )
        self.assertEqual(
            result.record["vector_sets"][0]["source"]["sha256"],
            hashlib.sha256(self.vectors_path.read_bytes()).hexdigest(),
        )

    def test_checked_record_is_not_a_verdict(self):
        result = self.check()
        rendered = json.dumps(result.record, sort_keys=True).lower()
        self.assertNotIn("verdict", rendered)
        self.assertNotIn("agreement", rendered)
        self.assertNotIn("correctness", rendered)

    def test_cli_success_emits_one_bounded_json_summary(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "check",
                "--manifest",
                "case/manifest.json",
                "--out",
                "build/checked.json",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        event = json.loads(result.stderr)
        self.assertEqual(event["event"], "homologia_check_ok")
        self.assertEqual(event["vector_set_count"], 1)
        self.assertEqual(event["vector_count"], 1)
        self.assertRegex(event["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(event["output_sha256"], r"^[0-9a-f]{64}$")

    def test_cli_refusal_emits_a_stable_code_subject_and_recovery(self):
        vector = self.vectors()[0]
        vector["expected"]["provenance"] = {"class": "proved"}
        self.write_vectors([vector])
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "check",
                "--manifest",
                "case/manifest.json",
                "--out",
                "build/checked.json",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, HOMOLOGIA.INPUT_REFUSED)
        self.assertEqual(result.stdout, "")
        event = json.loads(result.stderr)
        self.assertEqual(event["event"], "homologia_check_refused")
        self.assertEqual(event["code"], "HOM-CHECK-PROVENANCE")
        self.assertLessEqual(len(event["subject"]), 256)
        self.assertTrue(event["recovery"])

    def test_closed_manifest_refuses_unknown_fields(self):
        manifest = self.manifest()
        manifest["verdict"] = "agree"
        self.write_manifest(manifest)
        self.assert_refuses("HOM-CHECK-SHAPE")

    def test_closed_vector_refuses_unknown_fields(self):
        vector = self.vectors()[0]
        vector["answer"] = "1050000000000000000"
        self.write_vectors([vector])
        self.assert_refuses("HOM-CHECK-SHAPE")

    def test_named_file_replacement_refuses(self):
        original = HOMOLOGIA._read_bounded_file

        def replace_after_read(*args, **kwargs):
            value = original(*args, **kwargs)
            if Path(args[0]).name == "vectors.jsonl":
                replacement = self.root / "case" / "replacement.jsonl"
                replacement.write_bytes(self.vectors_path.read_bytes())
                replacement.replace(self.vectors_path)
            return value

        with mock.patch.object(HOMOLOGIA, "_read_bounded_file", replace_after_read):
            self.assert_refuses("HOM-CHECK-PATH")

    def test_published_schemas_are_closed_draft_2020_12_documents(self):
        for path in (MANIFEST_SCHEMA, VECTOR_SCHEMA):
            with self.subTest(path=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
                )
                self.assertIs(schema["additionalProperties"], False)
                path_pattern = re.compile(schema["$defs"]["path"]["pattern"])
                for invalid in (
                    "./vectors.jsonl",
                    "nested/./vectors.jsonl",
                    "nested/",
                    "vectors\x00.jsonl",
                    "nested/vectors.jsonl\n",
                ):
                    with self.subTest(path=path.name, invalid=invalid):
                        self.assertIsNone(path_pattern.search(invalid))
                self.assertIsNotNone(path_pattern.search("nested/vectors.jsonl"))

    def test_published_path_patterns_are_ecma_portable(self):
        expected = (
            r"^(?!/)(?![\s\S]*(?:^|/)\.{1,2}(?:/|$))"
            r"(?![\s\S]*[\u0000-\u001f\u007f])"
            r"(?![\s\S]*\\)(?![\s\S]*//)(?![\s\S]*/$)"
            r"[\s\S]+(?![\s\S])"
        )
        for path in (MANIFEST_SCHEMA, VECTOR_SCHEMA):
            with self.subTest(path=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(schema["$defs"]["path"]["pattern"], expected)
        for separator in ("\u2028", "\u2029"):
            with self.subTest(separator=ord(separator)):
                value = f"vectors{separator}set.jsonl"
                self.assertEqual(HOMOLOGIA._lexical_parts(value, "path"), (value,))
                self.assertIsNotNone(re.search(expected, value))

    def test_published_text_patterns_pin_whitespace_explicitly(self):
        expected = (
            r"[^\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680"
            r"\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]"
        )
        manifest = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
        vectors = json.loads(VECTOR_SCHEMA.read_text(encoding="utf-8"))
        fields = (
            manifest["properties"]["pair"]["properties"]["chain"]["properties"][
                "function"
            ],
            vectors["$defs"]["provenance"]["oneOf"][2]["properties"]["author"],
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertEqual(field["pattern"], expected)
        for whitespace in ("\u001c", "\u0085"):
            with self.subTest(whitespace=ord(whitespace)):
                self.assertIsNone(re.search(expected, whitespace))
                with self.assertRaises(HOMOLOGIA.Refusal):
                    HOMOLOGIA._text(whitespace, "text")
        self.assertIsNotNone(re.search(expected, "\ufeff"))
        self.assertEqual(HOMOLOGIA._text("\ufeff", "text"), "\ufeff")

    def test_published_schema_patterns_match_the_authoritative_text_boundary(self):
        manifest = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
        vectors = json.loads(VECTOR_SCHEMA.read_text(encoding="utf-8"))

        required_patterns = (
            (manifest["$defs"]["identifier"], "pair\n"),
            (manifest["properties"]["pair"]["properties"]["chain"]["properties"]["id"], "1\n"),
            (
                manifest["properties"]["pair"]["properties"]["chain"]["properties"]["contract"],
                "0x" + "1" * 40 + "\n",
            ),
            (
                manifest["properties"]["pair"]["properties"]["mirror"]["properties"]["revision"],
                "sha256:" + "a" * 64 + "\n",
            ),
            (vectors["$defs"]["canonicalInteger"], "1\n"),
            (vectors["properties"]["id"], "vector\n"),
            (
                vectors["$defs"]["provenance"]["oneOf"][1]["properties"]["block_hash"],
                "0x" + "1" * 64 + "\n",
            ),
        )
        for field, invalid in required_patterns:
            with self.subTest(invalid=invalid):
                self.assertIn("pattern", field)
                self.assertIsNone(re.search(field["pattern"], invalid))

        chain_function = manifest["properties"]["pair"]["properties"]["chain"]["properties"]["function"]
        asserted_author = vectors["$defs"]["provenance"]["oneOf"][2]["properties"]["author"]
        for field in (chain_function, asserted_author):
            with self.subTest(field=field):
                self.assertIn("pattern", field)
                self.assertIsNone(re.search(field["pattern"], "   "))

    def test_committed_example_repeats_the_committed_checked_bytes(self):
        example_root = self.root / "plugins" / "homologia" / "examples" / "wad-interest-v0"
        shutil.copytree(EXAMPLE, example_root)
        relative_manifest = "plugins/homologia/examples/wad-interest-v0/manifest.json"
        first = HOMOLOGIA.check_manifest(
            relative_manifest, "build/first.json", root=self.root
        )
        second = HOMOLOGIA.check_manifest(
            relative_manifest, "build/second.json", root=self.root
        )
        first_bytes = (self.root / "build" / "first.json").read_bytes()
        self.assertEqual(first_bytes, (self.root / "build" / "second.json").read_bytes())
        self.assertEqual(first.output_sha256, second.output_sha256)
        self.assertEqual(first_bytes, (EXAMPLE / "checked-inputs.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
