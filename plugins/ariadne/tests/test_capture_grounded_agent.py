"""The bounded local ``berean-release/v1`` capture boundary."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from unittest import mock

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import envelope, registry, verify  # noqa: E402
from ariadne_lib.capture import grounded_agent as capture  # noqa: E402
from ariadne_lib.predicates import grounded_agent as predicate  # noqa: E402


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def listing_digest(entries):
    body = "".join(
        "%s\0%s\n" % (path, digest) for path, digest in sorted(entries)
    ).encode("utf-8")
    return sha256(body)


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(data)


def write_json(path, value):
    write_bytes(path, canonical(value) + b"\n")


def read_json(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def semantic_digest(document):
    identity = {
        field: document[field] for field in predicate.BEREAN_IDENTITY_FIELDS
    }
    return sha256(canonical(identity))


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.release = os.path.join(self.root, "release")
        self.output = os.path.join(self.root, "statement.json")
        self.build_release()

    def build_release(self, reads=True, evals=True, promotion=True):
        if os.path.isdir(self.release):
            shutil.rmtree(self.release)
        os.makedirs(self.release)

        corpus_bytes = b"bounded corpus\n"
        corpus_path = "corpus/source.md"
        write_bytes(os.path.join(self.release, corpus_path), corpus_bytes)
        corpus_entry = {
            "path": "source.md",
            "bytes": len(corpus_bytes),
            "sha256": sha256(corpus_bytes),
        }
        corpus_digest = listing_digest(
            [(corpus_entry["path"], corpus_entry["sha256"])]
        )
        manifest = {
            "format": "berean-corpus/v1",
            "corpus_version": "test-v1",
            "files": [corpus_entry],
            "corpus_digest": corpus_digest,
        }
        manifest_path = os.path.join(self.release, "corpus-manifest.json")
        write_json(manifest_path, manifest)

        answer_bytes = b'{"answer":"bounded"}\n'
        write_bytes(os.path.join(self.release, "answers/answer.json"), answer_bytes)

        reads_block = None
        if reads:
            reads_bytes = b'{"jsonrpc":"2.0","result":"0x1"}\n'
            write_bytes(os.path.join(self.release, "reads.jsonl"), reads_bytes)
            reads_block = {
                "path": "reads.jsonl",
                "sha256": sha256(reads_bytes),
                "chain_id": 1,
                "block_number": 10,
                "block_hash": "0x" + "12" * 32,
                "source": "preserved test RPC bytes; no stronger evidence claimed",
            }

        evals_block = None
        cases_bytes = b'{"format":"test-cases/v1"}\n'
        report_bytes = b'{"format":"test-report/v1","passed":1,"failed":0}\n'
        if evals:
            write_bytes(os.path.join(self.release, "evals/cases.json"), cases_bytes)
            write_bytes(os.path.join(self.release, "evals/report.json"), report_bytes)
            evals_block = {
                "cases": "evals/cases.json",
                "cases_sha256": sha256(cases_bytes),
                "report": "evals/report.json",
                "report_sha256": sha256(report_bytes),
            }

        document = {
            "format": "berean-release/v1",
            "release_version": "test-v1",
            "corpus": {
                "path": "corpus",
                "manifest": "corpus-manifest.json",
                "manifest_sha256": sha256(canonical(manifest) + b"\n"),
                "corpus_version": "test-v1",
                "corpus_digest": corpus_digest,
            },
            "reads": reads_block,
            "answers": [
                {
                    "path": "answers/answer.json",
                    "sha256": sha256(answer_bytes),
                }
            ],
            "question_families": ["bounded test questions"],
            "refusal_conditions": ["anything outside the test corpus"],
            "rules": {
                "source_classes": list(predicate.BEREAN_SOURCE_CLASSES),
                "evidence_classes": list(predicate.BEREAN_EVIDENCE_CLASSES),
            },
            "allowlists": {"chains": [1], "contracts": ["0x" + "34" * 20]},
            "evals": evals_block,
            "retention": "none",
        }
        document["release_digest"] = semantic_digest(document)
        write_json(os.path.join(self.release, "release.json"), document)

        if promotion:
            self.assertIsNotNone(evals_block)
            record = {
                "format": "berean-promotion/v1",
                "sequence": 1,
                "action": "promote",
                "release_digest": document["release_digest"],
                "note": "test release promoted on its pinned report",
                "evals": {
                    "report_sha256": evals_block["report_sha256"],
                    "cases_sha256": evals_block["cases_sha256"],
                    "thresholds": {"failures_allowed": 0},
                    "cases": 1,
                    "passed": 1,
                    "failed": 0,
                },
            }
            write_bytes(
                os.path.join(self.release, "promotions.jsonl"),
                canonical(record) + b"\n",
            )

    def rewrite_release(self, mutate=None):
        path = os.path.join(self.release, "release.json")
        document = read_json(path)
        if mutate is not None:
            mutate(document)
        document["release_digest"] = semantic_digest(document)
        write_json(path, document)
        return document

    def taken(self, **overrides):
        arguments = {
            "name": "test-v1",
            "producer_tool": "berean",
            "producer_version": "1.0.0",
            "producer_command": ["python3", "scripts/berean.py", "release"],
            "output": self.output,
            "first_capture_reason": "first Ariadne capture of this release",
        }
        arguments.update(overrides)
        return capture.capture(self.release, **arguments)

    def report_for(self, statement):
        document = envelope.read(json.dumps(statement).encode("utf-8"))
        return verify.report(document, registry.DEFAULT)

    def run_cli(self, producer_command=None, previous=None, extra=None):
        out = io.StringIO()
        err = io.StringIO()
        argv = [
            "capture-grounded-agent",
            "--release",
            self.release,
            "--name",
            "test-v1",
            "--producer-tool",
            "berean",
            "--producer-version",
            "1.0.0",
            "--producer-command",
            *(producer_command or ["python3"]),
        ]
        if previous is None:
            argv.extend(["--first-capture-reason", "first capture"])
        else:
            argv.extend(["--previous", previous])
        argv.extend(["--output", self.output])
        argv.extend(extra or [])
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = ariadne.main(argv)
            except SystemExit as error:
                code = error.code
        return code, out.getvalue(), err.getvalue()

    def test_capture_is_deterministic_and_projects_only_byte_backed_evidence(self):
        first = self.taken()
        second = self.taken()
        self.assertEqual(first, second)
        self.assertTrue(self.report_for(first).ok)
        body = first["predicate"]
        self.assertEqual(body["release"]["release_digest"], semantic_digest(read_json(os.path.join(self.release, "release.json"))))
        self.assertEqual(len(body["given"]["corpus"]["components"]), 1)
        self.assertEqual(len(body["produced"]["answers"]), 1)
        self.assertIsNotNone(body["given"]["reads"])
        self.assertIsNotNone(body["produced"]["evaluations"])
        self.assertEqual(
            body["produced"]["promotion"]["terminal"],
            {
                "sequence": 1,
                "action": "promote",
                "target_release_digest": body["release"]["release_digest"],
            },
        )
        self.assertEqual(body["claims"], [])
        self.assertEqual(body["commands"], [])
        self.assertEqual(
            set(body["produced"]["promotion"]),
            {"component", "format", "terminal"},
        )
        self.assertEqual(
            set(body["produced"]["promotion"]["terminal"]),
            {"sequence", "action", "target_release_digest"},
        )

    def test_the_shipped_berean_demo_captures_and_verifies_offline(self):
        demo = os.path.join(
            support.REPO_ROOT,
            "plugins",
            "berean",
            "examples",
            "goldfinch-demo-v0",
            "release",
        )
        if not os.path.isdir(demo):
            self.skipTest("the Berean demo is not beside Ariadne")
        statement = capture.capture(
            demo,
            name="goldfinch-demo-v0",
            producer_tool="berean",
            producer_version="1.0.0",
            producer_command=["python3", "scripts/berean.py", "release"],
            output=self.output,
            first_capture_reason="first Ariadne capture of this Berean release",
        )
        self.assertTrue(self.report_for(statement).ok)
        self.assertEqual(
            statement["predicate"]["release"]["release_digest"],
            "7b104766e0df92de73d2b2cf98379e417151c0f824ada105c37eafdd367a7e8c",
        )
        self.assertEqual(len(statement["subject"]), 12)

    def test_absent_optional_evidence_stays_null_with_reasons(self):
        self.build_release(reads=False, evals=False, promotion=False)
        body = self.taken()["predicate"]
        self.assertIsNone(body["given"]["reads"])
        self.assertTrue(body["given"]["reads_absence_reason"])
        self.assertIsNone(body["produced"]["evaluations"])
        self.assertTrue(body["produced"]["evaluations_absence_reason"])
        self.assertIsNone(body["produced"]["promotion"])
        self.assertTrue(body["produced"]["promotion_absence_reason"])

    def test_previous_statement_supplies_the_verified_baseline(self):
        self.build_release(promotion=False)
        first = self.taken()
        capture.write(self.output, first, self.release)
        self.rewrite_release(
            lambda document: document.__setitem__("release_version", "test-v2")
        )
        second_output = os.path.join(self.root, "second.json")
        second = self.taken(
            name="test-v2",
            output=second_output,
            previous=self.output,
            first_capture_reason=None,
        )
        comparison = second["predicate"]["comparison"]
        self.assertEqual(comparison["baseline"], first["predicate"]["comparison"]["current"])
        self.assertIsNone(comparison["first_capture_reason"])
        self.assertTrue(self.report_for(second).ok)

    def test_same_release_previous_is_refused(self):
        statement = self.taken()
        capture.write(self.output, statement, self.release)
        with self.assertRaisesRegex(capture.CaptureError, "same semantic release"):
            self.taken(previous=self.output, first_capture_reason=None)

    def test_semantic_release_digest_is_not_the_release_file_digest(self):
        path = os.path.join(self.release, "release.json")
        document = read_json(path)
        document["release_version"] = "tampered-v2"
        write_json(path, document)
        with self.assertRaisesRegex(capture.CaptureError, "canonical identity"):
            self.taken()

    def test_each_declared_component_digest_is_checked(self):
        cases = (
            "corpus/source.md",
            "reads.jsonl",
            "answers/answer.json",
            "evals/cases.json",
            "evals/report.json",
        )
        for relative in cases:
            with self.subTest(relative=relative):
                self.build_release()
                with open(os.path.join(self.release, relative), "ab") as handle:
                    handle.write(b"tamper")
                with self.assertRaisesRegex(capture.CaptureError, "declared"):
                    self.taken()

    def test_promotion_chain_is_closed_ordered_and_release_bound(self):
        path = os.path.join(self.release, "promotions.jsonl")
        with open(path, encoding="utf-8") as handle:
            record = json.loads(handle.read())
        record["sequence"] = 2
        write_bytes(path, canonical(record) + b"\n")
        with self.assertRaisesRegex(capture.CaptureError, "gapped or reordered"):
            self.taken()

        self.build_release()
        with open(path, encoding="utf-8") as handle:
            record = json.loads(handle.read())
        record["evals"]["report_sha256"] = "ab" * 32
        write_bytes(path, canonical(record) + b"\n")
        with self.assertRaisesRegex(capture.CaptureError, "release report"):
            self.taken()

    def test_present_reserved_promotion_path_is_never_treated_as_absent(self):
        kinds = ["directory", "symlink"]
        if hasattr(os, "mkfifo"):
            kinds.append("fifo")
        for kind in kinds:
            with self.subTest(kind=kind):
                if os.path.exists(self.output):
                    os.unlink(self.output)
                self.build_release(promotion=False)
                path = os.path.join(self.release, "promotions.jsonl")
                if kind == "directory":
                    os.mkdir(path)
                elif kind == "symlink":
                    target = os.path.join(self.root, "outside-promotions.jsonl")
                    write_bytes(target, b"{}\n")
                    os.symlink(target, path)
                else:
                    os.mkfifo(path)
                code, out, err = self.run_cli()
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertIn("promotion", err)
                self.assertNotIn("Traceback", err)
                self.assertEqual(len(err.splitlines()), 1)
                self.assertFalse(os.path.exists(self.output))

    def test_unicode_line_separators_do_not_create_promotion_records(self):
        path = os.path.join(self.release, "promotions.jsonl")
        with open(path, "rb") as handle:
            record = handle.read().rstrip(b"\n")
        write_bytes(path, record + "\u2028".encode("utf-8") + record + b"\n")
        with self.assertRaisesRegex(capture.CaptureError, "not JSON"):
            self.taken()

    def test_duplicate_deep_and_float_json_are_controlled_refusals(self):
        path = os.path.join(self.release, "release.json")
        with open(path, "rb") as handle:
            raw = handle.read()
        write_bytes(
            path,
            raw.replace(
                b'"format":"berean-release/v1"',
                b'"format":"berean-release/v1","format":"berean-release/v1"',
                1,
            ),
        )
        with self.assertRaisesRegex(capture.CaptureError, "duplicate key"):
            self.taken()

        self.build_release()
        path = os.path.join(self.release, "release.json")
        with open(path, "rb") as handle:
            raw = handle.read().replace(b'"chain_id":1', b'"chain_id":1.0', 1)
        write_bytes(path, raw)
        with self.assertRaisesRegex(capture.CaptureError, "float"):
            self.taken()

        self.build_release()
        write_bytes(path, b'{"nested":' + b"[" * 40 + b"0" + b"]" * 40 + b"}")
        with self.assertRaisesRegex(capture.CaptureError, "deeper"):
            self.taken()

    def test_posix_and_windows_path_escapes_are_refused_before_reads(self):
        for escaped in ("../outside.json", "C:\\outside.json", "/outside.json"):
            with self.subTest(path=escaped):
                self.build_release()
                path = os.path.join(self.release, "release.json")
                document = read_json(path)
                document["answers"][0]["path"] = escaped
                document["release_digest"] = semantic_digest(document)
                write_json(path, document)
                with self.assertRaisesRegex(capture.CaptureError, "portable"):
                    self.taken()

    def test_undeclared_file_is_refused(self):
        write_bytes(os.path.join(self.release, "smuggled.txt"), b"not declared")
        with self.assertRaisesRegex(capture.CaptureError, "undeclared file"):
            self.taken()

    def test_every_file_beneath_the_corpus_path_is_manifest_listed(self):
        cases = (
            ("corpus-manifest.json", "corpus/manifest.json", ("corpus", "manifest")),
            ("reads.jsonl", "corpus/reads.jsonl", ("reads", "path")),
            ("answers/answer.json", "corpus/answer.json", ("answers", 0, "path")),
            ("evals/report.json", "corpus/report.json", ("evals", "report")),
        )
        for source, target, locator in cases:
            with self.subTest(role=source):
                self.build_release(promotion=False)
                os.makedirs(
                    os.path.dirname(os.path.join(self.release, target)),
                    exist_ok=True,
                )
                os.replace(
                    os.path.join(self.release, source),
                    os.path.join(self.release, target),
                )
                document = read_json(os.path.join(self.release, "release.json"))
                current = document
                for part in locator[:-1]:
                    current = current[part]
                current[locator[-1]] = target
                document["release_digest"] = semantic_digest(document)
                write_json(os.path.join(self.release, "release.json"), document)
                with self.assertRaisesRegex(capture.CaptureError, "corpus subtree"):
                    self.taken()

    def test_symlink_and_fifo_components_are_refused_without_opening(self):
        target = os.path.join(self.root, "outside")
        write_bytes(target, b"outside")
        answer = os.path.join(self.release, "answers/answer.json")
        os.unlink(answer)
        os.symlink(target, answer)
        with self.assertRaisesRegex(capture.CaptureError, "symlink"):
            self.taken()

        if not hasattr(os, "mkfifo"):
            return
        self.build_release()
        answer = os.path.join(self.release, "answers/answer.json")
        os.unlink(answer)
        os.mkfifo(answer)
        with self.assertRaisesRegex(capture.CaptureError, "not a regular file"):
            self.taken()

    def test_file_count_per_file_and_aggregate_ceilings_fail_before_output(self):
        manifest_path = os.path.join(self.release, "corpus-manifest.json")
        manifest = read_json(manifest_path)
        manifest["files"] = [
            {"path": "f%04d" % index, "bytes": 0, "sha256": "ab" * 32}
            for index in range(predicate.MAX_COMPONENTS + 1)
        ]
        write_json(manifest_path, manifest)
        self.rewrite_release(
            lambda document: document["corpus"].__setitem__(
                "manifest_sha256", sha256(canonical(manifest) + b"\n")
            )
        )
        with self.assertRaisesRegex(capture.CaptureError, "entry ceiling"):
            self.taken()
        self.assertFalse(os.path.exists(self.output))

        self.build_release()
        with mock.patch.object(capture, "MAX_COMPONENT_BYTES", 1):
            with self.assertRaisesRegex(capture.CaptureError, "per-file byte ceiling"):
                self.taken()
        with mock.patch.object(capture, "MAX_TOTAL_BYTES", 1):
            with self.assertRaisesRegex(capture.CaptureError, "total more"):
                self.taken()

    def test_wide_directory_refuses_before_scandir_is_drained(self):
        class Entry:
            def __init__(self, root, index):
                self.name = "wide-%06d.json" % index
                self.path = os.path.join(root, self.name)

            def is_dir(self, follow_symlinks=True):
                return False

            def is_symlink(self):
                return False

            def stat(self, follow_symlinks=True):
                return os.stat_result((0o100644, 0, 0, 1, 0, 0, 0, 0, 0, 0))

        class WideScan:
            def __init__(self, root, total):
                self.root = root
                self.total = total
                self.consumed = 0
                self.closed = False

            def __enter__(self):
                return self

            def __exit__(self, *_):
                self.close()

            def __iter__(self):
                return self

            def __next__(self):
                if self.consumed == self.total:
                    raise StopIteration
                entry = Entry(self.root, self.consumed)
                self.consumed += 1
                return entry

            def close(self):
                self.closed = True

        scan = WideScan(self.release, capture.tree.MAX_FILES + 1024)
        with mock.patch.object(capture.tree.os, "scandir", return_value=scan):
            code, out, err = self.run_cli()

        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("more than %d entries" % capture.tree.MAX_FILES, err)
        self.assertLessEqual(len(err.encode("utf-8")), 1024)
        self.assertEqual(len(err.splitlines()), 1)
        self.assertLessEqual(scan.consumed, capture.tree.MAX_FILES + 1)
        self.assertTrue(scan.closed)
        self.assertFalse(os.path.exists(self.output))

    def test_an_unstable_descriptor_read_is_a_controlled_refusal(self):
        original = capture.state_fixture.read_component

        def unstable(root, relative, *args, **kwargs):
            if relative == "answers/answer.json":
                raise capture.CaptureError("release answer changed while it was read")
            return original(root, relative, *args, **kwargs)

        with mock.patch.object(capture.state_fixture, "read_component", unstable):
            with self.assertRaisesRegex(capture.CaptureError, "changed while"):
                self.taken()
        self.assertFalse(os.path.exists(self.output))

    def test_output_inside_or_aliasing_the_release_is_refused(self):
        with self.assertRaisesRegex(capture.CaptureError, "inside"):
            self.taken(output=os.path.join(self.release, "statement.json"))

        hardlink = os.path.join(self.root, "hardlink.json")
        os.link(os.path.join(self.release, "release.json"), hardlink)
        with self.assertRaisesRegex(capture.CaptureError, "hard-link alias"):
            self.taken(output=hardlink)

        symlink = os.path.join(self.root, "symlink.json")
        os.symlink(os.path.join(self.release, "release.json"), symlink)
        with self.assertRaisesRegex(capture.CaptureError, "inside|symlink"):
            self.taken(output=symlink)

    def test_case_insensitive_release_alias_is_refused_by_capture_and_write(self):
        alias_root = os.path.join(self.root, "RELEASE")
        try:
            aliases_release = os.path.samefile(alias_root, self.release)
        except OSError:
            aliases_release = False
        if not aliases_release:
            self.skipTest("filesystem is case-sensitive")
        alias = os.path.join(alias_root, "captured.json")
        statement = self.taken()
        with self.assertRaisesRegex(capture.CaptureError, "inside"):
            self.taken(output=alias)
        with self.assertRaisesRegex(capture.CaptureError, "inside"):
            capture.write(alias, statement, self.release)
        self.assertFalse(os.path.exists(alias))

    def test_unicode_normalisation_alias_is_refused_by_capture_and_write(self):
        composed_name = "r\u00e9lease"
        composed = os.path.join(self.root, composed_name)
        os.replace(self.release, composed)
        self.release = composed
        decomposed = os.path.join(
            self.root, unicodedata.normalize("NFD", composed_name)
        )
        try:
            aliases_release = os.path.samefile(decomposed, self.release)
        except OSError:
            aliases_release = False
        if not aliases_release:
            self.skipTest("filesystem distinguishes Unicode normalisation forms")
        alias = os.path.join(decomposed, "captured.json")
        statement = self.taken()
        with self.assertRaisesRegex(capture.CaptureError, "inside"):
            self.taken(output=alias)
        with self.assertRaisesRegex(capture.CaptureError, "inside"):
            capture.write(alias, statement, self.release)
        self.assertFalse(os.path.exists(alias))

    def test_existing_output_is_replaced_and_interruption_preserves_old_bytes(self):
        statement = self.taken()
        write_bytes(self.output, b"old bytes\n")
        capture.write(self.output, statement, self.release)
        self.assertEqual(read_json(self.output), statement)

        write_bytes(self.output, b"survives\n")
        with mock.patch.object(capture.dataset.os, "replace", side_effect=OSError("stop")):
            with self.assertRaisesRegex(OSError, "stop"):
                capture.write(self.output, statement, self.release)
        with open(self.output, "rb") as handle:
            self.assertEqual(handle.read(), b"survives\n")
        leftovers = [name for name in os.listdir(self.root) if name.startswith(".ariadne-")]
        self.assertEqual(leftovers, [])

    def test_self_verification_failure_never_reaches_output(self):
        statement = self.taken()
        statement["predicate"]["claims"] = [
            {
                "name": "smuggled result",
                "subject": statement["subject"][0]["digest"],
                "disposition": "passed",
                "detail": {"thresholds": {"failures_allowed": 0}},
            }
        ]
        with self.assertRaisesRegex(capture.CaptureError, "self-verification"):
            capture.write(self.output, statement, self.release)
        self.assertFalse(os.path.exists(self.output))

    def test_cli_errors_are_one_line_without_a_traceback(self):
        write_bytes(os.path.join(self.release, "undeclared"), b"x")
        code, out, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("capture failed:", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(len(err.splitlines()), 1)
        self.assertFalse(os.path.exists(self.output))

    def test_unknown_field_diagnostics_are_small_and_do_not_dump_the_key(self):
        document = read_json(os.path.join(self.release, "release.json"))
        oversized = "x" * (1024 * 1024)
        document[oversized] = None
        write_json(os.path.join(self.release, "release.json"), document)
        code, out, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertLessEqual(len(err.encode("utf-8")), 1024)
        self.assertNotIn(oversized, err)
        self.assertEqual(len(err.splitlines()), 1)
        self.assertFalse(os.path.exists(self.output))

    def test_rules_vocabularies_require_arrays_without_cli_tracebacks(self):
        for field in ("source_classes", "evidence_classes"):
            for invalid in (None, 7, {}):
                with self.subTest(field=field, invalid=invalid):
                    self.build_release()
                    document = read_json(os.path.join(self.release, "release.json"))
                    document["rules"][field] = invalid
                    document["release_digest"] = semantic_digest(document)
                    write_json(os.path.join(self.release, "release.json"), document)
                    code, out, err = self.run_cli()
                    self.assertEqual(code, 2)
                    self.assertEqual(out, "")
                    self.assertIn("release %s" % field, err)
                    self.assertNotIn("Traceback", err)
                    self.assertEqual(len(err.splitlines()), 1)
                    self.assertFalse(os.path.exists(self.output))

    def test_previous_parser_diagnostic_is_bounded_and_does_not_dump_input(self):
        previous = os.path.join(self.root, "previous.json")
        oversized = "p" * (1024 * 1024)
        write_json(previous, {"payload": "", oversized: None})
        code, out, err = self.run_cli(previous=previous)
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertLessEqual(len(err.encode("utf-8")), 1024)
        self.assertNotIn(oversized, err)
        self.assertNotIn("Traceback", err)
        self.assertEqual(len(err.splitlines()), 1)
        self.assertFalse(os.path.exists(self.output))

    def test_cli_argument_diagnostics_are_bounded_and_do_not_dump_tokens(self):
        for size in (8 * 1024, 1024 * 1024):
            token = "--" + "x" * size
            with self.subTest(size=size):
                code, out, err = self.run_cli(extra=[token])
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertLessEqual(len(err.encode("utf-8")), 1024)
                self.assertNotIn(token, err)
                self.assertNotIn("Traceback", err)
                self.assertEqual(len(err.splitlines()), 1)
                self.assertFalse(os.path.exists(self.output))

    def test_cli_writes_utf8_under_an_ascii_process_locale(self):
        self.build_release(promotion=False)
        self.rewrite_release(
            lambda document: document["question_families"].__setitem__(
                0, "caf\u00e9 questions"
            )
        )
        command = [
            sys.executable,
            ariadne.__file__,
            "capture-grounded-agent",
            "--release",
            self.release,
            "--name",
            "test-v1",
            "--producer-tool",
            "berean",
            "--producer-version",
            "1.0.0",
            "--producer-command",
            "python3",
            "--first-capture-reason",
            "first capture",
            "--output",
            self.output,
        ]
        environment = dict(os.environ)
        environment.update(
            {
                "LANG": "C",
                "LC_ALL": "C",
                "PYTHONCOERCECLOCALE": "0",
                "PYTHONUTF8": "0",
            }
        )
        completed = subprocess.run(
            command,
            cwd=support.REPO_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(
            completed.returncode,
            0,
            completed.stderr.decode("utf-8", "backslashreplace"),
        )
        with open(self.output, "rb") as handle:
            statement = json.loads(handle.read().decode("utf-8"))
        self.assertEqual(
            statement["predicate"]["policy"]["question_families"][0],
            "caf\u00e9 questions",
        )
        self.assertTrue(self.report_for(statement).ok)

    def test_non_unicode_scalar_strings_are_controlled_cli_refusals(self):
        identity = b"bounded test questions"
        provenance = b"preserved test RPC bytes; no stronger evidence claimed"
        cases = (
            (identity, b"\\ud800", None),
            (provenance, b"\\ud800", None),
            (None, None, ["\ud800"]),
        )
        for old, new, command in cases:
            with self.subTest(surface="argv" if command else old.decode("ascii")):
                self.build_release()
                if old is not None:
                    path = os.path.join(self.release, "release.json")
                    with open(path, "rb") as handle:
                        raw = handle.read()
                    self.assertIn(old, raw)
                    write_bytes(path, raw.replace(old, new, 1))
                code, out, err = self.run_cli(producer_command=command)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertLessEqual(len(err.encode("utf-8")), 1024)
                self.assertNotIn("Traceback", err)
                self.assertEqual(len(err.splitlines()), 1)
                self.assertFalse(os.path.exists(self.output))

    def test_capture_source_has_no_berean_runtime_or_execution_boundary(self):
        with open(capture.__file__, encoding="utf-8") as handle:
            source = handle.read()
        for forbidden in ("berean_lib", "subprocess", "urllib", "requests", "socket"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
