from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable

from skills.brevitas.scripts.held_corpus import (
    CorpusError,
    FAMILIES,
    MODEL_IDENTITIES,
    failure_line,
    validate_corpus,
)


CORPUS = Path(__file__).resolve().parents[1] / "skills" / "brevitas" / "evals"


class HeldCorpusTests(unittest.TestCase):
    def copy_corpus(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "evals"
        shutil.copytree(CORPUS, root, symlinks=True)
        return temporary, root

    def load_manifest(self, root: Path) -> dict[str, Any]:
        return json.loads((root / "corpus.json").read_text(encoding="utf-8"))

    def write_manifest(self, root: Path, manifest: dict[str, Any]) -> None:
        (root / "corpus.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def expect_failure(
        self,
        code: str,
        change: Callable[[Path, dict[str, Any]], None],
    ) -> CorpusError:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        manifest = self.load_manifest(root)
        change(root, manifest)
        self.write_manifest(root, manifest)
        with self.assertRaises(CorpusError) as raised:
            validate_corpus(root)
        self.assertEqual(raised.exception.code, code)
        return raised.exception

    @staticmethod
    def fixture_path(root: Path, case: dict[str, Any], field: str = "output") -> Path:
        return root / case["files"][field]

    @staticmethod
    def refresh_digest(case: dict[str, Any], field: str, data: bytes) -> None:
        case["files"][f"{field}_sha256"] = hashlib.sha256(data).hexdigest()

    def test_clean_corpus_covers_every_family_and_both_models(self) -> None:
        result = validate_corpus(CORPUS)

        self.assertEqual(len(result.cases), 10)
        self.assertEqual(set(result.family_models), FAMILIES)
        self.assertEqual(result.unclassified, 0)
        self.assertEqual(result.stale, 0)
        for models in result.family_models.values():
            self.assertEqual(set(models), MODEL_IDENTITIES)

    def test_unknown_field_is_refused(self) -> None:
        self.expect_failure(
            "HC010",
            lambda _root, manifest: manifest["cases"][0].__setitem__("unknown", True),
        )

    def test_duplicate_json_field_is_refused(self) -> None:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / "corpus.json"
        text = manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text(
            text.replace(
                '"schema": "brevitas-held-corpus-v1",',
                '"schema": "brevitas-held-corpus-v1",\n  "schema": "brevitas-held-corpus-v1",',
                1,
            ),
            encoding="utf-8",
        )

        with self.assertRaises(CorpusError) as raised:
            validate_corpus(root)
        self.assertEqual(raised.exception.code, "HC002")

    def test_duplicate_case_id_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][1]["id"] = manifest["cases"][0]["id"]

        self.expect_failure("HC011", change)

    def test_missing_provider_or_full_model_id_is_refused(self) -> None:
        for field in ("provider", "returned_model_id"):
            with self.subTest(field=field):
                self.expect_failure(
                    "HC010",
                    lambda _root, manifest, field=field: manifest["cases"][0][
                        "capture"
                    ].pop(field),
                )

    def test_stale_digest_is_refused_with_short_digest_diagnostics(self) -> None:
        error = self.expect_failure(
            "HC024",
            lambda _root, manifest: manifest["cases"][0]["files"].__setitem__(
                "output_sha256", "0" * 64
            ),
        )
        rendered = failure_line(error)
        self.assertIn("expected=000000000000", rendered)
        self.assertIn("actual=", rendered)
        self.assertNotIn("output-gpt", rendered)

    def test_absolute_path_is_refused(self) -> None:
        self.expect_failure(
            "HC020",
            lambda _root, manifest: manifest["cases"][0]["files"].__setitem__(
                "output", "/tmp/held-output.md"
            ),
        )

    def test_parent_escape_is_refused(self) -> None:
        self.expect_failure(
            "HC020",
            lambda _root, manifest: manifest["cases"][0]["files"].__setitem__(
                "output", "../held-output.md"
            ),
        )

    def test_symlink_escape_is_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            outside = root.parent / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            linked = self.fixture_path(root, case).parent / "linked.md"
            linked.symlink_to(outside)
            case["files"]["output"] = str(linked.relative_to(root))
            self.refresh_digest(case, "output", outside.read_bytes())

        self.expect_failure("HC021", change)

    def test_non_regular_file_is_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            directory = self.fixture_path(root, case).parent
            case["files"]["output"] = str(directory.relative_to(root))

        self.expect_failure("HC021", change)

    def test_oversized_input_is_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            oversized = self.fixture_path(root, case).parent / "oversized.md"
            data = b"x" * (32 * 1024 + 1)
            oversized.write_bytes(data)
            case["files"]["output"] = str(oversized.relative_to(root))
            self.refresh_digest(case, "output", data)

        self.expect_failure("HC022", change)

    def test_invalid_utf8_is_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            invalid = self.fixture_path(root, case).parent / "invalid.md"
            data = b"\xff\xfe"
            invalid.write_bytes(data)
            case["files"]["output"] = str(invalid.relative_to(root))
            self.refresh_digest(case, "output", data)

        self.expect_failure("HC023", change)

    def test_missing_family_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"] = [
                case for case in manifest["cases"] if case["family"] != "x-ray"
            ]

        self.expect_failure("HC040", change)

    def test_one_model_family_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"] = [
                case
                for case in manifest["cases"]
                if not (
                    case["family"] == "x-ray"
                    and case["capture"]["returned_model_id"] == "openai/gpt-5.6-terra"
                )
            ]

        self.expect_failure("HC041", change)

    def test_duplicated_protected_span_is_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            output = self.fixture_path(root, case)
            span = case["protected_spans"][0]["text"].encode("utf-8")
            data = output.read_bytes() + b"\n" + span + b"\n"
            output.write_bytes(data)
            self.refresh_digest(case, "output", data)

        self.expect_failure("HC032", change)

    def test_reordered_protected_span_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            spans = manifest["cases"][0]["protected_spans"]
            spans[0]["order"], spans[1]["order"] = spans[1]["order"], spans[0]["order"]

        self.expect_failure("HC033", change)

    def test_hidden_session_and_credential_metadata_are_refused(self) -> None:
        for field in ("hidden_reasoning", "session_id", "credential"):
            with self.subTest(field=field):
                self.expect_failure(
                    "HC013",
                    lambda _root, manifest, field=field: manifest["cases"][0][
                        "capture"
                    ].__setitem__(field, "forbidden"),
                )

    def test_unclassified_case_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            case["classification"]["outcome"] = "unclassified"
            case["classification"]["expected_codes"] = []

        self.expect_failure("HC015", change)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO support is unavailable")
    def test_fifo_is_refused_without_reading_it(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            fifo = self.fixture_path(root, case).parent / "output.fifo"
            os.mkfifo(fifo)
            case["files"]["output"] = str(fifo.relative_to(root))

        self.expect_failure("HC021", change)
