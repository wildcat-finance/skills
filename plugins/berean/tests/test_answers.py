"""Answer records: the specification's first five gates, mechanically."""

import json
import os
import tempfile
import unittest

from tests.support import SCRIPTS, SCHEMAS  # noqa: F401

from berean_lib import answers, citations, corpus, digests, jsonio, reads
from tests.test_corpus import make_tree, failures
from tests.test_reads import record, write_reads

DOC = "# Terms\n\nThe pause flag halts new entries. Version 3 keeps it set.\n".encode("utf-8")
CHAIN_ID = 1
BLOCK = 13097494


def span(data, needle):
    start = data.index(needle.encode("utf-8"))
    return start, start + len(needle.encode("utf-8"))


class AnswerFixture(unittest.TestCase):
    def setUp(self):
        self.holder = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.holder.name, "docs")
        make_tree(self.root, {"terms.md": DOC})
        self.manifest = corpus.build(self.root, "v1")
        self.read_record = record("eth_getStorageAt", ["0x8bbd", "0x0", "0xc7da16"])
        self.reads_path = os.path.join(self.holder.name, "reads.jsonl")
        write_reads(self.reads_path, [self.read_record])
        self.records = reads.load(self.reads_path)

    def tearDown(self):
        self.holder.cleanup()

    def citation(self, needle, identifier="c1"):
        start, end = span(DOC, needle)
        return {
            "id": identifier,
            "format": citations.FORMAT,
            "doc": "terms.md",
            "byte_start": start,
            "byte_end": end,
            "sha256": digests.of_bytes(DOC[start:end]),
            "display_text": needle,
        }

    def read(self, identifier="r1"):
        return {
            "id": identifier,
            "chain_id": CHAIN_ID,
            "block_number": BLOCK,
            "request_key": self.read_record["request_key"],
        }

    def answer(self, **overrides):
        base = {
            "format": answers.FORMAT,
            "question": "Is the pause flag set?",
            "kind": "answer",
            "refusal": None,
            "sentences": [
                {
                    "text": "The documentation says the pause flag halts new entries.",
                    "source_class": "document",
                    "evidence": ["c1"],
                },
                {
                    "text": "Slot zero reads one at the declared block.",
                    "source_class": "chain_read",
                    "evidence": ["r1"],
                },
            ],
            "citations": [self.citation("The pause flag halts new entries.")],
            "reads": [self.read()],
            "discrepancies": [],
        }
        base.update(overrides)
        return base

    def check(self, answer):
        return answers.check(
            answer, self.manifest, self.root, self.records, CHAIN_ID, BLOCK
        )


class GateOneTests(AnswerFixture):
    def test_a_classified_answer_passes(self):
        self.assertEqual(failures(self.check(self.answer())), [])

    def test_an_unknown_source_class_fails_the_shape(self):
        bad = self.answer()
        bad["sentences"][0]["source_class"] = "vibes"
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_an_evidence_free_document_sentence_fails(self):
        bad = self.answer()
        bad["sentences"][0]["evidence"] = []
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_user_supplied_fact_names_the_question_spans_it_rests_on(self):
        # "Is the pause flag set?" is 22 bytes; "pause flag set" is bytes 7 to 21.
        for evidence in (["question:7-21"], ["question:7-12", "question:13-21"], ["question:0-22"]):
            with self.subTest(evidence=evidence):
                good = self.answer()
                good["sentences"].append(
                    {"text": "You said the lender is fund A.", "source_class": "user_supplied", "evidence": evidence}
                )
                self.assertEqual(failures(self.check(good)), [])
        for evidence in (["c1"], ["r1"], ["question:7-21", "c1"]):
            with self.subTest(evidence=evidence):
                bad = self.answer()
                bad["sentences"].append(
                    {"text": "You said the lender is fund A.", "source_class": "user_supplied", "evidence": evidence}
                )
                checks = self.check(bad)
                self.assertEqual(failures(checks), ["answer-shape"])
                self.assertIn("no artefact behind it", checks[0].detail)

    def test_a_calculation_derives_from_known_evidence(self):
        good = self.answer()
        good["sentences"].append(
            {"text": "So one of one flag is set.", "source_class": "calculation", "evidence": ["c1", "r1"]}
        )
        self.assertEqual(failures(self.check(good)), [])


class QuestionSpanTests(AnswerFixture):
    """A user_supplied sentence rests on real, whole, non-blank bytes of the question."""

    def supplied(self, evidence, question=None):
        document = self.answer()
        if question is not None:
            document["question"] = question
        document["sentences"].append(
            {"text": "You said the lender is fund A.", "source_class": "user_supplied", "evidence": evidence}
        )
        return document

    def refused(self, evidence, question=None):
        """The answer-shape detail, proved free of the question's words."""
        document = self.supplied(evidence, question)
        checks = self.check(document)
        self.assertEqual(failures(checks), ["answer-shape"])
        detail = checks[0].detail
        self.assertNotIn(document["question"], detail)
        self.assertNotIn("pause flag", detail)
        return detail

    def test_an_empty_span_list_fails_the_shape(self):
        self.assertIn("names no span", self.refused([]))

    def test_a_misspelled_span_reference_fails_the_shape(self):
        details = set()
        for reference in (
            "question",
            "question:",
            "question:7",
            "question:7-",
            "question:07-21",
            "question:+7-21",
            "question:7-21-3",
            "Question:7-21",
            " question:7-21",
            "question:7-21 ",
            "question:7-21\n",
            "question:12345678-12345679",
        ):
            with self.subTest(reference=reference):
                detail = self.refused([reference])
                self.assertIn("question:<start>-<end>", detail)
                details.add(detail)
        # One detail for every misspelling: a reference that did not parse is never echoed.
        self.assertEqual(len(details), 1)

    def test_a_non_string_span_reference_fails_the_shape(self):
        for reference in (7, None, ["question:7-21"]):
            with self.subTest(reference=reference):
                self.assertIn("is not a string", self.refused([reference]))

    def test_an_inverted_or_empty_span_fails_the_shape(self):
        for reference, offsets in (("question:21-7", "21..7"), ("question:7-7", "7..7")):
            with self.subTest(reference=reference):
                detail = self.refused([reference])
                self.assertIn("empty or inverted", detail)
                self.assertIn(offsets, detail)

    def test_a_span_past_the_question_fails_the_shape(self):
        for reference in ("question:7-23", "question:22-30"):
            with self.subTest(reference=reference):
                self.assertIn("leaves the 22 byte question", self.refused([reference]))

    def test_a_span_splitting_a_character_fails_the_shape(self):
        question = "Is the pause flag set \u2014 today?"  # the em dash is bytes 22 to 25
        whole = self.supplied(["question:22-25"], question)
        self.assertEqual(failures(self.check(whole)), [])
        detail = self.refused(["question:7-24"], question)
        self.assertIn("splits a character", detail)
        self.assertIn("7..24", detail)

    def test_a_blank_span_fails_the_shape(self):
        self.assertIn("is blank", self.refused(["question:2-3"]))

    def test_an_artefact_id_with_the_reserved_prefix_fails_at_collection(self):
        bad = self.answer()
        bad["citations"][0]["id"] = "question:7-21"
        bad["sentences"][0]["evidence"] = ["question:7-21"]
        checks = self.check(bad)
        self.assertEqual(failures(checks), ["answer-shape"])
        self.assertIn("reserved prefix", checks[0].detail)
        self.assertNotIn("7-21", checks[0].detail)
        bad = self.answer()
        bad["reads"][0]["id"] = "question:x"
        bad["sentences"][1]["evidence"] = ["question:x"]
        checks = self.check(bad)
        self.assertEqual(failures(checks), ["answer-shape"])
        self.assertIn("reserved prefix", checks[0].detail)

    def test_an_unencodable_question_fails_the_shape_by_name(self):
        # json turns the escape "\udc80" into a lone surrogate, a str with no UTF-8
        # encoding. It passes jsonio on the way in, so the checker has to refuse it
        # by name rather than crash at the slice.
        question = jsonio.loads('"Is the pause flag set?\\udc80"')
        self.assertEqual(question, "Is the pause flag set?\udc80")
        refusal = self.answer(
            question=question,
            kind="refusal",
            refusal={"boundary": "outside the corpus", "detail": "no pinned document covers it"},
            sentences=[],
            citations=[],
            reads=[],
            discrepancies=[],
        )
        for document in (self.supplied(["question:7-21"], question), refusal):
            with self.subTest(kind=document["kind"]):
                try:
                    checks = self.check(document)
                except UnicodeEncodeError:
                    self.fail("the checker crashed on an unencodable question instead of refusing it")
                self.assertEqual(failures(checks), ["answer-shape"])
                self.assertIn("not encodable as UTF-8 at character 22", checks[0].detail)
                self.assertNotIn("pause flag", checks[0].detail)


class GateTwoTests(AnswerFixture):
    def test_a_mismatched_span_fails_answer_citations(self):
        bad = self.answer()
        bad["citations"][0]["display_text"] = "The pause flag halts all entries."
        self.assertEqual(failures(self.check(bad)), ["answer-citations"])

    def test_a_drifted_corpus_file_fails_answer_citations(self):
        with open(os.path.join(self.root, "terms.md"), "ab") as handle:
            handle.write(b"\n")
        self.assertEqual(failures(self.check(self.answer())), ["answer-citations"])


class GateThreeTests(AnswerFixture):
    def test_a_read_without_a_preserved_record_fails(self):
        bad = self.answer()
        bad["reads"][0]["request_key"] = "0" * 64
        self.assertEqual(failures(self.check(bad)), ["answer-reads"])

    def test_a_read_naming_another_block_fails(self):
        bad = self.answer()
        bad["reads"][0]["block_number"] = BLOCK + 1
        self.assertEqual(failures(self.check(bad)), ["answer-reads"])

    def test_a_read_naming_another_chain_fails(self):
        bad = self.answer()
        bad["reads"][0]["chain_id"] = 10
        self.assertEqual(failures(self.check(bad)), ["answer-reads"])

    def test_a_boolean_block_number_fails_the_shape(self):
        bad = self.answer()
        bad["reads"][0]["block_number"] = True
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class GateFourTests(AnswerFixture):
    def test_a_declared_disagreement_passes_and_is_counted(self):
        good = self.answer()
        good["discrepancies"] = [
            {
                "subject": "pause flag",
                "document_evidence": "c1",
                "chain_evidence": "r1",
                "note": "the document says set; the block read disagrees",
            }
        ]
        checks = self.check(good)
        self.assertEqual(failures(checks), [])
        domains = [c for c in checks if c.name == "answer-domains"][0]
        self.assertIn("1 declared", domains.detail)

    def test_a_disagreement_naming_unknown_evidence_fails_the_shape(self):
        bad = self.answer()
        bad["discrepancies"] = [
            {
                "subject": "pause flag",
                "document_evidence": "c9",
                "chain_evidence": "r1",
                "note": "the sides disagree",
            }
        ]
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class GateFiveTests(AnswerFixture):
    def refusal(self):
        return {
            "format": answers.FORMAT,
            "question": "What is the lender's home address?",
            "kind": "refusal",
            "refusal": {
                "boundary": "outside the declared question families",
                "detail": "the release answers protocol questions, not personal ones",
            },
            "sentences": [],
            "citations": [],
            "reads": [],
            "discrepancies": [],
        }

    def test_a_clean_refusal_passes(self):
        checks = self.check(self.refusal())
        self.assertEqual(failures(checks), [])
        self.assertEqual([c.name for c in checks], ["answer-shape", "answer-refusal"])

    def test_a_refusal_carrying_sentences_fails_the_shape(self):
        bad = self.refusal()
        bad["sentences"] = [
            {"text": "Here it is anyway.", "source_class": "document", "evidence": []}
        ]
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_refusal_without_a_boundary_fails_the_shape(self):
        bad = self.refusal()
        bad["refusal"] = {"boundary": " ", "detail": "unnamed"}
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class HygieneTests(AnswerFixture):
    def test_unused_evidence_fails_the_shape(self):
        bad = self.answer()
        bad["citations"].append(self.citation("Version 3 keeps it set.", "c2"))
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_duplicate_evidence_ids_fail_the_shape(self):
        bad = self.answer()
        bad["citations"].append(self.citation("Version 3 keeps it set.", "c1"))
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_a_shared_citation_and_read_id_fails_the_shape(self):
        bad = self.answer()
        bad["reads"][0]["id"] = "c1"
        bad["sentences"][1]["evidence"] = ["c1"]
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])

    def test_an_undeclared_field_fails_the_shape(self):
        bad = self.answer()
        bad["model"] = "gpt"
        self.assertEqual(failures(self.check(bad)), ["answer-shape"])


class SchemaAgreementTests(unittest.TestCase):
    def test_the_shipped_schema_matches_the_module(self):
        with open(SCHEMAS / "answer-v1.json", "r", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(schema["properties"]["format"]["const"], answers.FORMAT)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(tuple(schema["required"]), answers.FIELDS)
        self.assertEqual(tuple(schema["properties"]["kind"]["enum"]), answers.KINDS)
        sentence = schema["properties"]["sentences"]["items"]
        self.assertEqual(tuple(sentence["required"]), answers.SENTENCE_FIELDS)
        self.assertEqual(
            tuple(sentence["properties"]["source_class"]["enum"]), answers.SOURCE_CLASSES
        )
        self.assertEqual(
            tuple(schema["properties"]["reads"]["items"]["required"]), answers.READ_FIELDS
        )
        self.assertEqual(
            schema["properties"]["sentences"]["maxItems"], answers.MAX_SENTENCES
        )


class CliTests(AnswerFixture):
    def test_the_cli_proves_and_refuses_an_answer(self):
        import importlib

        berean = importlib.import_module("berean")
        from berean_lib import canonical

        manifest_path = os.path.join(self.holder.name, "corpus-manifest.json")
        corpus.write(self.manifest, manifest_path)
        answer_path = os.path.join(self.holder.name, "answer.json")
        with open(answer_path, "w", encoding="utf-8") as handle:
            handle.write(canonical.dumps(self.answer()) + "\n")
        argv = [
            "check-answer", answer_path,
            "--corpus", manifest_path,
            "--root", self.root,
            "--reads", self.reads_path,
            "--chain-id", str(CHAIN_ID),
            "--block-number", str(BLOCK),
        ]
        self.assertEqual(berean.main(argv), 0)
        self.assertEqual(berean.main(argv[:-1] + [str(BLOCK + 1)]), 1)


if __name__ == "__main__":
    unittest.main()
