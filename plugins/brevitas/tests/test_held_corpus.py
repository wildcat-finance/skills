from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable
from unittest import mock

from skills.brevitas.scripts.held_corpus import (
    CorpusError,
    FAMILIES,
    MODEL_IDENTITIES,
    _read_regular_utf8,
    failure_line,
    result_lines,
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

    def test_clean_corpus_covers_every_family_and_both_requested_models(self) -> None:
        result = validate_corpus(CORPUS)

        self.assertEqual(len(result.cases), 10)
        self.assertEqual(set(result.family_models), FAMILIES)
        self.assertEqual(result.unclassified, 0)
        self.assertEqual(result.stale, 0)
        for models in result.family_models.values():
            self.assertEqual(set(models), MODEL_IDENTITIES)
        self.assertTrue(
            all(
                getattr(case, "provider_returned_backend_id", "missing") is None
                for case in result.cases
            )
        )
        rendered = "\n".join(result_lines(result))
        self.assertIn("requested_models=2", rendered)
        self.assertIn("backends_established=0", rendered)
        self.assertIn("backend_identity=unestablished", rendered)
        self.assertEqual(rendered.count(" request="), 10)

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
                '"schema": "brevitas-held-corpus-v2",',
                '"schema": "brevitas-held-corpus-v2",\n  "schema": "brevitas-held-corpus-v2",',
                1,
            ),
            encoding="utf-8",
        )

        with self.assertRaises(CorpusError) as raised:
            validate_corpus(root)
        self.assertEqual(raised.exception.code, "HC002")

    def test_escaped_invalid_unicode_scalar_is_refused(self) -> None:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / "corpus.json"
        manifest = self.load_manifest(root)
        manifest["cases"][0]["classification"]["basis"] = "\ud800"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

        try:
            with self.assertRaises(CorpusError) as raised:
                validate_corpus(root)
        except UnicodeEncodeError:
            self.fail("invalid Unicode scalar escaped the bounded refusal")
        self.assertEqual(raised.exception.code, "HC002")

    def test_deep_manifest_nesting_is_bounded(self) -> None:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        nested = '{"hidden_reasoning":"forbidden"}'
        for _ in range(1000):
            nested = "[" + nested + "]"
        (root / "corpus.json").write_text(
            '{"schema":"brevitas-held-corpus-v2",'
            '"request_format":"prompt-source-v1",'
            '"cases":' + nested + "}",
            encoding="utf-8",
        )

        try:
            with self.assertRaises(CorpusError) as raised:
                validate_corpus(root)
        except RecursionError:
            self.fail("deep manifest nesting escaped the bounded refusal")
        self.assertEqual(raised.exception.code, "HC013")

    def test_duplicate_case_id_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][1]["id"] = manifest["cases"][0]["id"]

        self.expect_failure("HC011", change)

    def test_missing_provider_or_requested_model_id_is_refused(self) -> None:
        for field in ("provider", "requested_model_id"):
            with self.subTest(field=field):
                self.expect_failure(
                    "HC010",
                    lambda _root, manifest, field=field: manifest["cases"][0][
                        "capture"
                    ].pop(field, None),
                )

    def test_non_null_provider_returned_backend_id_is_refused(self) -> None:
        self.expect_failure(
            "HC012",
            lambda _root, manifest: manifest["cases"][0]["capture"].__setitem__(
                "provider_returned_backend_id", "openai/internal-backend"
            ),
        )

    def test_missing_or_mismatched_client_identity_evidence_is_refused(self) -> None:
        def missing(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][0]["capture"].pop("client_identity_evidence", None)

        def mismatched_banner(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][0]["capture"].setdefault(
                "client_identity_evidence", {}
            )[
                "acknowledged_model_banner"
            ] = "model: gpt-5.6-terra"

        def mismatched_binding(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][0]["capture"].setdefault(
                "client_identity_evidence", {}
            )[
                "binding_sha256"
            ] = "0" * 64

        for expected, change in (
            ("HC010", missing),
            ("HC012", mismatched_banner),
            ("HC012", mismatched_binding),
        ):
            with self.subTest(expected=expected, change=change.__name__):
                self.expect_failure(expected, change)

    def test_false_human_review_provenance_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            classification = manifest["cases"][0]["classification"]
            classification["reviewer"] = "human-review"
            classification["reviewer_kind"] = "human"

        self.expect_failure("HC015", change)

    def test_unknown_rule_citation_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            classification = manifest["cases"][0]["classification"]
            classification["outcome"] = "expected-diagnostics"
            classification["expected_codes"] = ["B999"]
            classification["rule_citations"] = ["B999"]
            classification["basis"] = "B999: fabricated rule citation."

        self.expect_failure("HC016", change)

    def test_rule_citation_requires_a_complete_basis_token(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            classification = manifest["cases"][0]["classification"]
            classification["expected_codes"] = ["B003"]
            classification["rule_citations"] = ["B003"]
            classification["basis"] = "B0030 is not the cited rule."

        self.expect_failure("HC016", change)

    def test_basis_rule_tokens_match_rule_citations(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            classification = manifest["cases"][0]["classification"]
            classification["basis"] += " B030: additional cited rule."

        self.expect_failure("HC016", change)

    def test_basis_may_repeat_a_declared_rule_token(self) -> None:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        manifest = self.load_manifest(root)
        classification = manifest["cases"][0]["classification"]
        repeated = classification["rule_citations"][0]
        classification["basis"] += f" {repeated}: repeated supporting reference."
        self.write_manifest(root, manifest)

        result = validate_corpus(root)
        self.assertEqual(len(result.cases), 10)

    def test_json_escaped_forbidden_value_is_refused(self) -> None:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / "corpus.json"
        manifest = self.load_manifest(root)
        marker = "credential" + "=" + "A" * 12
        manifest["cases"][0]["classification"]["basis"] += " " + marker
        encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        escaped = b"credential" + b"\\u003d" + b"A" * 12
        manifest_path.write_bytes(encoded.replace(marker.encode(), escaped, 1))

        with self.assertRaises(CorpusError) as raised:
            validate_corpus(root)
        self.assertEqual(raised.exception.code, "HC013")

    def test_json_escaped_nonsecret_value_is_allowed(self) -> None:
        temporary, root = self.copy_corpus()
        self.addCleanup(temporary.cleanup)
        manifest_path = root / "corpus.json"
        manifest = self.load_manifest(root)
        marker = "credential" + "=" + "short"
        manifest["cases"][0]["classification"]["basis"] += " " + marker
        encoded = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
        escaped = b"credential" + b"\\u003d" + b"short"
        manifest_path.write_bytes(encoded.replace(marker.encode(), escaped, 1))

        result = validate_corpus(root)
        self.assertEqual(len(result.cases), 10)

    def test_zero_or_malformed_source_commit_is_refused(self) -> None:
        for value in ("0" * 40, "not-a-commit"):
            with self.subTest(value=value):
                self.expect_failure(
                    "HC014",
                    lambda _root, manifest, value=value: manifest["cases"][0][
                        "provenance"
                    ]["origins"][0].__setitem__("commit", value),
                )

    def test_unbound_source_derivation_is_refused(self) -> None:
        def zero_output(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][0]["provenance"].setdefault("derivation", {})[
                "output_sha256"
            ] = "0" * 64

        def relabel_diff_as_exact(_root: Path, manifest: dict[str, Any]) -> None:
            derivation = manifest["cases"][0]["provenance"].setdefault(
                "derivation", {}
            )
            output_digest = manifest["cases"][0]["files"]["source_sha256"]
            derivation.update(
                {
                    "method": "exact-line-range-v1",
                    "input_sha256": output_digest,
                    "output_sha256": output_digest,
                    "steps": ["select-declared-line-range"],
                }
            )

        for change in (zero_output, relabel_diff_as_exact):
            with self.subTest(change=change.__name__):
                self.expect_failure("HC014", change)

    def test_malformed_nested_types_are_bounded(self) -> None:
        def method_list(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][0]["provenance"]["derivation"]["method"] = []

        def citation_object(_root: Path, manifest: dict[str, Any]) -> None:
            manifest["cases"][0]["classification"]["rule_citations"] = [{}]

        for expected, change in (
            ("HC014", method_list),
            ("HC016", citation_object),
        ):
            with self.subTest(change=change.__name__):
                try:
                    self.expect_failure(expected, change)
                except TypeError:
                    self.fail("malformed nested type escaped the bounded refusal")

    def test_malformed_source_range_is_refused(self) -> None:
        for value in ("lines one to many", "L" + "9" * 5000 + "-L1"):
            with self.subTest(value_length=len(value)):
                def change(
                    _root: Path,
                    manifest: dict[str, Any],
                    value: str = value,
                ) -> None:
                    exact_case = next(
                        case
                        for case in manifest["cases"]
                        if case["family"] != "diff-review"
                    )
                    exact_case["provenance"]["origins"][0]["range"] = value

                try:
                    self.expect_failure("HC014", change)
                except ValueError:
                    self.fail("malformed source range escaped the bounded refusal")

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

    def test_noncanonical_path_alias_is_refused(self) -> None:
        def change(_root: Path, manifest: dict[str, Any]) -> None:
            first, second = manifest["cases"][:2]
            second["files"]["output"] = first["files"]["output"].replace(
                "cases/", "cases//", 1
            )
            second["files"]["output_sha256"] = first["files"]["output_sha256"]
            second["classification"] = first["classification"]
            second["protected_spans"] = first["protected_spans"]

        self.expect_failure("HC020", change)

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

    def test_fixture_io_error_is_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "fixture.md").write_text("safe\n", encoding="utf-8")

            with mock.patch.object(os, "read", side_effect=OSError("simulated I/O")):
                try:
                    _read_regular_utf8(
                        root,
                        "fixture.md",
                        byte_limit=1024,
                        case_id="io-probe",
                    )
                except Exception as caught:
                    raised = caught
                else:
                    self.fail("fixture I/O failure was accepted")

        self.assertIsInstance(raised, CorpusError)
        self.assertEqual(getattr(raised, "code", None), "HC021")

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
                    and case["capture"].get(
                        "requested_model_id", case["capture"].get("returned_model_id")
                    )
                    == "openai/gpt-5.6-terra"
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

    def test_overlapping_protected_span_is_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            output = b"aaaa\n"
            self.fixture_path(root, case).write_bytes(output)
            self.refresh_digest(case, "output", output)
            text = "aaa"
            case["protected_spans"] = [
                {
                    "order": 1,
                    "kind": "causal-mechanism",
                    "text": text,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                }
            ]

        self.expect_failure("HC032", change)

    def test_equal_start_protected_spans_are_refused(self) -> None:
        def change(root: Path, manifest: dict[str, Any]) -> None:
            case = manifest["cases"][0]
            output = b"abc\n"
            self.fixture_path(root, case).write_bytes(output)
            self.refresh_digest(case, "output", output)
            case["protected_spans"] = [
                {
                    "order": order,
                    "kind": "causal-mechanism",
                    "text": text,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                }
                for order, text in enumerate(("abc", "ab"), start=1)
            ]

        self.expect_failure("HC033", change)

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

    def test_github_credential_bytes_are_refused(self) -> None:
        tokens = (
            b"gh" + b"p_" + b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            b"github" + b"_pat_" + b"A" * 82,
        )

        for token in tokens:
            with self.subTest(prefix=token.split(b"_", 1)[0]):
                def change(
                    root: Path,
                    manifest: dict[str, Any],
                    token: bytes = token,
                ) -> None:
                    case = manifest["cases"][0]
                    self.fixture_path(root, case).write_bytes(
                        b"captured value " + token + b"\n"
                    )

                self.expect_failure("HC013", change)

    def test_common_credential_and_session_bytes_are_refused(self) -> None:
        markers = {
            "aws-access-key": b"AK" + b"IA" + b"A" * 16,
            "slack-bot-token": (
                b"xo" + b"xb-" + b"1" * 12 + b"-" + b"2" * 12 + b"-" + b"A" * 24
            ),
            "gitlab-pat": b"gl" + b"pat-" + b"A" * 20,
            "jwt": b"e" + b"y" + b"J" + b"A" * 20 + b"." + b"B" * 24 + b"." + b"C" * 24,
            "credential-assignment": b"credential=" + b"A" * 24,
            "session-assignment": b"session=" + b"A" * 24,
        }

        for label, marker in markers.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "fixture.md").write_bytes(b"captured " + marker + b"\n")
                with self.assertRaises(CorpusError) as raised:
                    _read_regular_utf8(
                        root,
                        "fixture.md",
                        byte_limit=1024,
                        case_id="credential-probe",
                    )
                self.assertEqual(raised.exception.code, "HC013")

    def test_adjacent_credential_like_prose_without_values_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            data = (
                b"credential=short session=short AK"
                + b"IA"
                + b"A" * 15
                + b" xoxb-short glpat-short eyJheader.payload\n"
            )
            (root / "fixture.md").write_bytes(data)

            actual, text = _read_regular_utf8(
                root,
                "fixture.md",
                byte_limit=1024,
                case_id="credential-near-miss",
            )

        self.assertEqual(actual, data)
        self.assertEqual(text, data.decode("utf-8"))

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
