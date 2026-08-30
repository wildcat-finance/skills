import base64
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_wave_mu_adversarial_corpus.py"
CORPUS = ROOT / "tests" / "fixtures" / "wave-mu-adversarial-corpus-v1"
SCHEMA = ROOT / "schemas" / "wave-mu-fixture-contract-v1.schema.json"
SOURCE_CATALOG = CORPUS / "source-catalog.json"
CROSSWALK = ROOT / "docs" / "wave-mu-retired-framework-crosswalk-v1.md"
PROVENANCE = ROOT / "docs" / "wave-mu-adversarial-corpus-v1.md"

SPEC = importlib.util.spec_from_file_location("wave_mu_validator_for_tests", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class WaveMuAdversarialCorpusTests(unittest.TestCase):
    """The validator must reject any local custody or safety-contract drift."""

    def copied_corpus(self):
        temporary = tempfile.TemporaryDirectory()
        target = Path(temporary.name) / "corpus"
        shutil.copytree(CORPUS, target)
        self.addCleanup(temporary.cleanup)
        return target

    def run_validator(self, corpus=CORPUS, schema=SCHEMA):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--corpus", str(corpus), "--schema", str(schema)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )

    def assert_rejected(self, result, code):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(code, result.stderr)

    def test_accepts_the_frozen_exact_byte_corpus_without_writing_it(self):
        before = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in CORPUS.iterdir()
        }
        result = self.run_validator()
        after = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in CORPUS.iterdir()
        }
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validated 60 fixtures", result.stdout)
        self.assertEqual(before, after)

    def test_validates_the_byte_addressed_source_catalog_and_all_evidence_ids(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("source catalog EV-01..EV-17", result.stdout)
        self.assertEqual(
            hashlib.sha256(SOURCE_CATALOG.read_bytes()).hexdigest(),
            "3f26d7741d3204ae39d670f31ebb1b790c2154eb7347edf27ddd288e8032935c",
        )

        corpus = self.copied_corpus()
        catalog = corpus / "source-catalog.json"
        catalog.write_bytes(catalog.read_bytes() + b"\n")
        self.assert_rejected(self.run_validator(corpus), "source-catalog-sha256")

    def test_reader_validates_the_open_descriptor_when_the_path_is_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            member = directory / "member.json"
            replacement = directory / "replacement.json"
            member.write_bytes(b"original")
            replacement.write_bytes(b"replacement")
            directory_fd = os.open(directory, os.O_RDONLY)
            self.addCleanup(os.close, directory_fd)
            original_open = os.open

            def open_then_replace(path, flags, mode=0o777, *, dir_fd=None):
                descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
                if path == "member.json" and dir_fd == directory_fd:
                    os.replace(replacement, member)
                return descriptor

            with mock.patch.object(validator.os, "open", side_effect=open_then_replace):
                self.assertEqual(
                    validator.read_regular_member(directory_fd, "member.json", 32), b"original"
                )
            self.assertEqual(member.read_bytes(), b"replacement")

    def test_reader_bounds_growth_after_fstat(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "member.json").write_bytes(b"x")
            directory_fd = os.open(directory, os.O_RDONLY)
            self.addCleanup(os.close, directory_fd)
            with mock.patch.object(validator.os, "read", return_value=b"y" * 9):
                with self.assertRaisesRegex(validator.ValidationFailure, "size-limit"):
                    validator.read_regular_member(directory_fd, "member.json", 8)

    def test_crosswalk_and_provenance_keep_the_review_and_authority_boundaries(self):
        crosswalk = CROSSWALK.read_text(encoding="utf-8")
        self.assertIn("| #700 | #700 |", crosswalk)
        self.assertIn("| #701 | #874 |", crosswalk)
        self.assertNotIn("| #700 | #873", crosswalk)
        self.assertNotIn("| #701 | #874 and #875", crosswalk)

        provenance = PROVENANCE.read_text(encoding="utf-8")
        self.assertIn("freeze-time custody metadata", provenance)
        self.assertIn("separate sharing event", provenance)
        self.assertIn("external and exact-action-specific", provenance)
        self.assertIn("local advisory review", provenance)
        self.assertIn("not an accepted independent implementation or Fiat security review", provenance)

    def test_rejects_missing_and_unexpected_members(self):
        corpus = self.copied_corpus()
        (corpus / "JS-01.json").unlink()
        self.assert_rejected(self.run_validator(corpus), "missing-member")

        corpus = self.copied_corpus()
        (corpus / "unexpected.json").write_text("{}\n", encoding="utf-8")
        self.assert_rejected(self.run_validator(corpus), "unexpected-member")

    def test_rejects_one_byte_fixture_mutation_and_root_mismatch(self):
        corpus = self.copied_corpus()
        fixture = corpus / "JS-01.json"
        fixture_json = json.loads(fixture.read_text(encoding="utf-8"))
        fixture_json["adapter"]["rule"] += "x"
        fixture.write_text(
            json.dumps(fixture_json, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_rejected(self.run_validator(corpus), "fixture-sha256")

        corpus = self.copied_corpus()
        manifest = json.loads((corpus / "corpus-manifest.json").read_text(encoding="utf-8"))
        manifest["corpus_root_sha256"] = "0" * 64
        (corpus / "corpus-manifest.json").write_text(
            json.dumps(manifest, separators=(",", ":")) + "\n", encoding="utf-8"
        )
        self.assert_rejected(self.run_validator(corpus), "support-sha256")

    def test_rejects_schema_mirror_drift_and_noncanonical_fixture_json(self):
        schema = Path(tempfile.mkdtemp()) / "mirror.json"
        self.addCleanup(shutil.rmtree, schema.parent)
        schema.write_bytes(SCHEMA.read_bytes() + b"\n")
        self.assert_rejected(self.run_validator(schema=schema), "schema-mirror")

        corpus = self.copied_corpus()
        fixture = corpus / "VM-01.json"
        fixture.write_bytes(fixture.read_bytes() + b"\n")
        self.assert_rejected(self.run_validator(corpus), "canonical-json")

    def test_rejects_malformed_oversized_and_symlink_members(self):
        corpus = self.copied_corpus()
        (corpus / "AG-01.json").write_text("{\n", encoding="utf-8")
        self.assert_rejected(self.run_validator(corpus), "invalid-json")

        corpus = self.copied_corpus()
        (corpus / "README.md").write_bytes(b"x" * 1_048_577)
        self.assert_rejected(self.run_validator(corpus), "size-limit")

        if hasattr(os, "symlink"):
            corpus = self.copied_corpus()
            target = corpus / "JS-01.json"
            target.unlink()
            target.symlink_to(corpus / "VM-01.json")
            self.assert_rejected(self.run_validator(corpus), "nonregular-member")

    def test_rejects_decoded_stimulus_and_safety_contract_drift(self):
        corpus = self.copied_corpus()
        fixture_path = corpus / "PB-01.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        decoded = base64.b64decode(fixture["stimulus"]["bytes_b64"], validate=True)
        tampered = bytearray(decoded)
        tampered[-2] ^= 1
        fixture["stimulus"]["bytes_b64"] = base64.b64encode(tampered).decode("ascii")
        fixture_path.write_text(
            json.dumps(fixture, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_rejected(self.run_validator(corpus), "stimulus-sha256")

        corpus = self.copied_corpus()
        fixture_path = corpus / "LC-06.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["execution_status"] = "run"
        fixture_path.write_text(
            json.dumps(fixture, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_rejected(self.run_validator(corpus), "not-run")

        corpus = self.copied_corpus()
        fixture_path = corpus / "LC-06.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["safety"]["live_credentials"] = True
        fixture_path.write_text(
            json.dumps(fixture, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_rejected(self.run_validator(corpus), "safety-contract")

        corpus = self.copied_corpus()
        fixture_path = corpus / "LC-06.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        fixture["oracle"]["required_evidence"] = ["EV-99"]
        fixture_path.write_text(
            json.dumps(fixture, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8"
        )
        self.assert_rejected(self.run_validator(corpus), "unresolved-evidence")


if __name__ == "__main__":
    unittest.main()
