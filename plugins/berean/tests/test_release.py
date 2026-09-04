"""Release gates: every one provable and every one breachable by name."""

import json
import os
import shutil
import tempfile
import unittest

from tests.support import SCRIPTS, SCHEMAS, FIXTURES  # noqa: F401

from berean_lib import canonical, release
from tests import release_fixture
from tests.test_corpus import failures

PASS_RELEASE = FIXTURES / "conformance" / "pass-release"
BREACHES = FIXTURES / "conformance" / "breaches.json"


def build_temp_release(holder):
    directory = os.path.join(holder, "release")
    os.makedirs(directory)
    document = release_fixture.build(directory)
    return directory, document


class BuildTests(unittest.TestCase):
    def test_the_built_release_verifies_clean(self):
        with tempfile.TemporaryDirectory() as holder:
            directory, _ = build_temp_release(holder)
            self.assertEqual(failures(release.verify(directory)), [])

    def test_the_digest_covers_every_identity_field(self):
        self.assertEqual(
            set(release.IDENTITY_FIELDS) | {"release_digest"}, set(release.FIELDS)
        )
        with tempfile.TemporaryDirectory() as holder:
            _directory, document = build_temp_release(holder)
            for field in release.IDENTITY_FIELDS:
                mutated = json.loads(json.dumps(document))
                if field == "retention":
                    mutated[field] = "none" if document[field] != "none" else "answers-only"
                elif field == "release_version":
                    mutated[field] = "v-other"
                else:
                    continue
                with self.subTest(field=field):
                    self.assertNotEqual(
                        release.release_digest(mutated), document["release_digest"]
                    )

    def test_two_builds_are_byte_identical(self):
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            build_temp_release(one)
            build_temp_release(two)
            with open(os.path.join(one, "release", "release.json"), "rb") as handle:
                first = handle.read()
            with open(os.path.join(two, "release", "release.json"), "rb") as handle:
                second = handle.read()
            self.assertEqual(first, second)


class ConformanceTests(unittest.TestCase):
    """The committed fixture is the builder's output, held still, and every
    breach in breaches.json fails exactly the gate it names."""

    def test_the_committed_fixture_is_the_builder_output(self):
        with tempfile.TemporaryDirectory() as holder:
            directory, _ = build_temp_release(holder)
            fresh = sorted(
                os.path.relpath(os.path.join(current, name), directory)
                for current, _, files in os.walk(directory)
                for name in files
            )
            committed = sorted(
                os.path.relpath(os.path.join(current, name), PASS_RELEASE)
                for current, _, files in os.walk(PASS_RELEASE)
                for name in files
            )
            self.assertEqual(fresh, committed)
            for relative in fresh:
                with self.subTest(file=relative):
                    with open(os.path.join(directory, relative), "rb") as handle:
                        expected = handle.read()
                    with open(os.path.join(PASS_RELEASE, relative), "rb") as handle:
                        self.assertEqual(handle.read(), expected)

    def test_the_committed_fixture_verifies_clean(self):
        self.assertEqual(failures(release.verify(str(PASS_RELEASE))), [])

    def apply(self, directory, breach):
        target = os.path.join(directory, breach["path"]) if breach.get("path") else None
        op = breach["op"]
        if op in ("json-set", "json-set-release"):
            with open(target, encoding="utf-8") as handle:
                document = json.loads(handle.read())
            cursor = document
            keys = breach["pointer"]
            for key in keys[:-1]:
                cursor = cursor[key] if isinstance(key, str) else cursor[int(key)]
            last = keys[-1]
            if isinstance(cursor, list):
                cursor[int(last)] = breach["value"]
            else:
                cursor[last] = breach["value"]
            if op == "json-set-release":
                document["release_digest"] = release.release_digest(document)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(canonical.dumps(document) + "\n")
        elif op == "append-byte":
            with open(target, "ab") as handle:
                handle.write(b"\n")
        elif op == "delete-file":
            os.remove(target)
        elif op == "add-file":
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(breach["value"])
        else:
            raise AssertionError(f"unknown breach op: {op}")

    def test_every_breach_fails_exactly_its_named_gate(self):
        with open(BREACHES, encoding="utf-8") as handle:
            breaches = json.load(handle)
        self.assertTrue(breaches)
        gates_breached = set()
        for breach in breaches:
            with self.subTest(breach=breach["name"]):
                with tempfile.TemporaryDirectory() as holder:
                    directory = os.path.join(holder, "release")
                    shutil.copytree(PASS_RELEASE, directory)
                    self.apply(directory, breach)
                    self.assertEqual(
                        failures(release.verify(directory)), breach["gates"]
                    )
                    gates_breached.update(breach["gates"])
        every_gate = {
            "release-shape",
            "release-corpus",
            "release-reads",
            "release-allowlists",
            "release-answers",
            "release-retention",
            "release-evals",
            "release-components",
            "release-promotions",
        }
        self.assertEqual(gates_breached, every_gate)

    def test_the_verifier_names_each_gate_once(self):
        names = [check.name for check in release.verify(str(PASS_RELEASE))]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            names,
            [
                "release-shape",
                "release-corpus",
                "release-reads",
                "release-allowlists",
                "release-answers",
                "release-retention",
                "release-evals",
                "release-components",
                "release-promotions",
            ],
        )


class AllowlistWalkTests(unittest.TestCase):
    def test_an_address_nested_in_a_filter_object_is_walked(self):
        found = list(
            release._address_shaped(
                [{"address": "0x" + "8b" * 20, "topics": [["0x" + "11" * 20]]}]
            )
        )
        self.assertEqual(found, ["0x" + "8b" * 20, "0x" + "11" * 20])

    def test_a_nested_unallowlisted_address_fails_the_gate(self):
        import shutil as _shutil

        from berean_lib import reads as reads_lib

        with tempfile.TemporaryDirectory() as holder:
            directory = os.path.join(holder, "release")
            _shutil.copytree(PASS_RELEASE, directory)
            method = "eth_getLogs"
            params = [{"address": "0x" + "99" * 20, "fromBlock": "0xf4240"}]
            extra = {
                "schema_version": 1,
                "request_key": reads_lib.request_key(method, params),
                "method": method,
                "params": params,
                "required": True,
                "evidence": "recorded-rpc",
                "outcome": {"result": []},
            }
            reads_path = os.path.join(directory, "reads.jsonl")
            with open(reads_path, encoding="utf-8") as handle:
                records = [json.loads(line) for line in handle.read().splitlines()]
            records.append(extra)
            records.sort(key=lambda record: record["request_key"])
            with open(reads_path, "w", encoding="utf-8") as handle:
                handle.write("\n".join(canonical.dumps(r) for r in records) + "\n")
            document_path = os.path.join(directory, "release.json")
            with open(document_path, encoding="utf-8") as handle:
                document = json.loads(handle.read())
            document["reads"]["sha256"] = release.digests.of_file(reads_path)
            document["release_digest"] = release.release_digest(document)
            with open(document_path, "w", encoding="utf-8") as handle:
                handle.write(canonical.dumps(document) + "\n")
            self.assertEqual(
                failures(release.verify(directory)), ["release-allowlists"]
            )


class QuestionSpanTests(unittest.TestCase):
    def test_a_blanked_span_list_fails_release_answers_by_shape(self):
        with tempfile.TemporaryDirectory() as holder:
            directory = os.path.join(holder, "release")
            shutil.copytree(PASS_RELEASE, directory)
            answer_path = os.path.join(directory, "answers", "a1.json")
            with open(answer_path, encoding="utf-8") as handle:
                answer = json.loads(handle.read())
            supplied = [s for s in answer["sentences"] if s["source_class"] == "user_supplied"]
            self.assertEqual([s["evidence"] for s in supplied], [["question:7-21"]])
            supplied[0]["evidence"] = []
            with open(answer_path, "w", encoding="utf-8") as handle:
                handle.write(canonical.dumps(answer) + "\n")
            document_path = os.path.join(directory, "release.json")
            with open(document_path, encoding="utf-8") as handle:
                document = json.loads(handle.read())
            self.assertEqual(document["answers"][0]["path"], "answers/a1.json")
            document["answers"][0]["sha256"] = release.digests.of_file(answer_path)
            document["release_digest"] = release.release_digest(document)
            with open(document_path, "w", encoding="utf-8") as handle:
                handle.write(canonical.dumps(document) + "\n")
            checks = release.verify(directory)
            self.assertEqual(failures(checks), ["release-answers"])
            detail = [check for check in checks if check.name == "release-answers"][0].detail
            self.assertIn("answers/a1.json: answer-shape", detail)


class SchemaAgreementTests(unittest.TestCase):
    def test_the_shipped_schema_matches_the_module(self):
        with open(SCHEMAS / "release-v1.json", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(schema["properties"]["format"]["const"], release.FORMAT)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(tuple(schema["required"]), release.FIELDS)
        self.assertEqual(
            tuple(schema["properties"]["retention"]["enum"]), release.RETENTION
        )
        reads_shape = schema["properties"]["reads"]["oneOf"][1]
        self.assertEqual(tuple(reads_shape["required"]), release.READS_FIELDS)
        corpus_shape = schema["properties"]["corpus"]
        self.assertEqual(tuple(corpus_shape["required"]), release.CORPUS_FIELDS)
        from berean_lib import answers, reads

        rules = schema["properties"]["rules"]["properties"]
        self.assertEqual(
            tuple(rules["source_classes"]["const"]), answers.SOURCE_CLASSES
        )
        self.assertEqual(
            tuple(rules["evidence_classes"]["const"]), reads.EVIDENCE_CLASSES
        )


class CliTests(unittest.TestCase):
    def test_verify_release_passes_and_refuses(self):
        import importlib

        berean = importlib.import_module("berean")
        self.assertEqual(berean.main(["verify-release", str(PASS_RELEASE)]), 0)
        with tempfile.TemporaryDirectory() as holder:
            directory = os.path.join(holder, "release")
            shutil.copytree(PASS_RELEASE, directory)
            with open(os.path.join(directory, "corpus", "terms.md"), "ab") as handle:
                handle.write(b"\n")
            self.assertEqual(berean.main(["verify-release", directory]), 1)


if __name__ == "__main__":
    unittest.main()
