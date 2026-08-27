"""Hold the router-selection corpus to the prose it claims to grade.

`tests/test_portable_skills.py` checks that the router resolves: its links
reach real files, its canonical names match their directories and stay unique.
None of that presents a request. This module holds the corpus that does: every
case names the canonical skill the router should select, and quotes the
sentence that decides it from the file that sentence lives in.

What a pass here establishes is narrow and deliberate. The corpus has the shape
its schema declares, every canonical name it expects is a real skill under
`plugins/`, and every sentence it quotes still occurs in the file it names. It
establishes nothing about how an agent routes. That is a recorded grading run's
subject, and a recorded score is never this suite's pass condition.

The comparison collapses runs of whitespace before searching, so rewrapping a
paragraph does not fail the check and rewording one does. A reader who changes
a boundary sentence gets a failure naming the case, the file and the sentence
that is no longer there.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import re
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

# One fixed repository-relative corpus, resolved from a constant. No argument,
# no glob and no caller-supplied component reaches this path.
CORPUS_PATH = "tests/fixtures/router-selection/cases.json"
SCHEMA = "promise-machine-router-selection/v1"

ROUTER_PATH = ".agents/skills/promise-machine/SKILL.md"
# The closed set of files a case may quote. A corpus is data, so the path it
# names is checked against this set before anything is opened.
PROSE_SOURCES = frozenset({"AGENTS.md", ROUTER_PATH})

CASE_FIELDS = frozenset(
    {"id", "family", "request", "expect", "contested", "deciding_sentence",
     "not_established"}
)
PAIR_FIELDS = frozenset({"id", "skills", "deciding_sentence"})
SENTENCE_FIELDS = frozenset({"path", "section", "text"})
RUN_FIELDS = frozenset(
    {"model", "date", "prompt_template_sha256", "corpus_sha256", "cases",
     "passed", "failed", "failures"}
)
REFUSALS = frozenset({"ambiguous", "uncovered"})

SKILL_NAME = re.compile(r"(?m)^name:\s*([^\n]+)$")


class CorpusError(Exception):
    """The corpus could not be read as the schema this checker supports."""


def parse_corpus(raw: bytes) -> dict:
    """Turn corpus bytes into a document, or fail naming the corpus.

    Every refusal names `CORPUS_PATH`, because there is one corpus and a
    message that says only "invalid JSON" sends the reader looking. The empty
    case list is refused here rather than left to the loops below: a truncated
    write that lands `{"cases": []}` would otherwise make every check pass over
    nothing and report clean.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise CorpusError(f"{CORPUS_PATH} is not UTF-8: {error}") from error
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise CorpusError(f"{CORPUS_PATH} is not JSON: {error}") from error
    if not isinstance(document, dict):
        raise CorpusError(f"{CORPUS_PATH} is not a JSON object")
    if not isinstance(document.get("cases"), list) or not document["cases"]:
        raise CorpusError(f"{CORPUS_PATH} carries no cases")
    if not isinstance(document.get("pairs"), list):
        raise CorpusError(f"{CORPUS_PATH} carries no pairs block")
    if not isinstance(document.get("runs"), list):
        raise CorpusError(f"{CORPUS_PATH} carries no runs block")
    return document


def load_corpus() -> dict:
    path = REPOSITORY_ROOT / CORPUS_PATH
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise CorpusError(f"{CORPUS_PATH} could not be read: {error}") from error
    return parse_corpus(raw)


def corpus_digest(cases: list) -> str:
    """Digest the cases alone.

    A run block lives in the same file it pins, so a digest over the whole
    document would change the moment a run was recorded and could never match.
    """
    payload = json.dumps(cases, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_skill_names() -> dict:
    """Every canonical skill name under `plugins/`, mapped to its file."""
    names = {}
    for skill in sorted((REPOSITORY_ROOT / "plugins").glob("*/skills/**/SKILL.md")):
        match = SKILL_NAME.search(skill.read_text(encoding="utf-8"))
        if match:
            names[match.group(1).strip()] = skill.relative_to(REPOSITORY_ROOT).as_posix()
    return names


def section_of(text: str, heading: str) -> str | None:
    """The lines under one Markdown heading, up to the next heading."""
    lines = text.splitlines()
    if heading not in lines:
        return None
    start = lines.index(heading) + 1
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("#")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def collapsed(text: str) -> str:
    return " ".join(text.split())


def quoting(document: dict):
    """Every quoted sentence in the corpus, with the entry that quotes it."""
    for pair in document["pairs"]:
        yield f"pair {pair.get('id')}", pair.get("deciding_sentence")
    for case in document["cases"]:
        yield f"case {case.get('id')}", case.get("deciding_sentence")


class RouterSelectionCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_corpus()

    def test_the_corpus_declares_the_supported_schema(self):
        self.assertEqual(
            self.document.get("schema"), SCHEMA,
            f"{CORPUS_PATH} declares a schema this checker does not support; the "
            f"contract in docs/promise-machine/router-selection-v1.md is {SCHEMA}",
        )

    def test_every_case_carries_the_required_fields_and_a_unique_id(self):
        wrong, seen = [], set()
        for index, case in enumerate(self.document["cases"]):
            where = f"{CORPUS_PATH}#cases[{index}]"
            if not isinstance(case, dict) or set(case) != CASE_FIELDS:
                wrong.append(f"{where}: fields are not exactly {sorted(CASE_FIELDS)}")
                continue
            for field in ("id", "family", "request", "not_established"):
                if not isinstance(case[field], str) or not case[field].strip():
                    wrong.append(f"{where}: {field} is not a non-empty string")
            if case["id"] in seen:
                wrong.append(f"{where}: id {case['id']!r} is used by an earlier case")
            seen.add(case["id"])
            expect = case["expect"]
            if not isinstance(expect, dict):
                wrong.append(f"{where}: expect is not an object")
            elif expect.get("outcome") == "select":
                if set(expect) != {"outcome", "canonical"} or not expect["canonical"]:
                    wrong.append(f"{where}: a select expectation names no canonical skill")
            elif expect.get("outcome") == "refuse":
                if set(expect) != {"outcome", "reason"} or expect.get("reason") not in REFUSALS:
                    wrong.append(f"{where}: a refuse expectation names no reason in {sorted(REFUSALS)}")
            else:
                wrong.append(f"{where}: outcome is neither 'select' nor 'refuse'")
            if not isinstance(case["contested"], list) or any(
                not isinstance(item, str) or not item for item in case["contested"]
            ):
                wrong.append(f"{where}: contested is not a list of canonical names")
            sentence = case["deciding_sentence"]
            if not isinstance(sentence, dict) or set(sentence) != SENTENCE_FIELDS:
                wrong.append(f"{where}: deciding_sentence is not {sorted(SENTENCE_FIELDS)}")
            elif sentence["path"] not in PROSE_SOURCES:
                wrong.append(
                    f"{where}: deciding_sentence names {sentence['path']!r}, which is "
                    f"outside the quotable set {sorted(PROSE_SOURCES)}"
                )
        self.assertEqual(
            wrong, [],
            "the corpus is data a checker parses, and these entries do not have the "
            "shape it parses:\n  " + "\n  ".join(wrong),
        )

    def test_every_expected_canonical_name_is_a_real_canonical_skill(self):
        names = canonical_skill_names()
        self.assertTrue(names, "no canonical skills were discovered under plugins/")
        stray = []
        for case in self.document["cases"]:
            expected = case.get("expect", {}).get("canonical")
            wanted = ([expected] if expected else []) + list(case.get("contested") or [])
            for name in wanted:
                if name not in names:
                    stray.append(f"case {case.get('id')}: {name!r}")
        for pair in self.document["pairs"]:
            for name in pair.get("skills") or []:
                if name not in names:
                    stray.append(f"pair {pair.get('id')}: {name!r}")
        self.assertEqual(
            stray, [],
            "these names are not the frontmatter name of any SKILL.md under "
            "plugins/, so the corpus expects a selection nothing can make; correct "
            f"the name or add the skill: {stray}",
        )

    def test_every_deciding_sentence_occurs_in_the_file_it_names(self):
        """The check that turns quoted prose into evidence.

        A corpus that quotes a boundary sentence nobody maintains is a claim
        about prose rather than a check on it. This reads the named section and
        looks for the sentence, so a reworded boundary fails here instead of
        surviving until a reader notices the corpus no longer matches.
        """
        sources = {
            path: (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
            for path in sorted(PROSE_SOURCES)
        }
        missing = []
        for owner, sentence in quoting(self.document):
            if not isinstance(sentence, dict) or sentence.get("path") not in sources:
                continue
            path, heading = sentence["path"], sentence.get("section")
            section = section_of(sources[path], heading)
            if section is None:
                missing.append(f"{owner}: {path} has no section {heading!r}")
            elif collapsed(sentence.get("text", "")) not in collapsed(section):
                missing.append(
                    f"{owner}: {path} section {heading!r} no longer contains "
                    f"{sentence.get('text')!r}"
                )
        self.assertEqual(
            missing, [],
            "a deciding sentence is no longer in the file the corpus quotes it "
            "from, so the case rests on prose that has moved or been reworded. "
            "Requote the current sentence or retire the case; do not reword the "
            f"source to match the corpus:\n  " + "\n  ".join(missing),
        )

    def test_a_recorded_run_block_matches_the_corpus_digest(self):
        """Vacuous until a run is recorded, and exact once one is.

        The digest covers the cases array alone, so recording a block does not
        move the value it pins. A block whose digest disagrees with the bytes on
        disk was graded against a different corpus and is not evidence about
        this one.
        """
        expected = corpus_digest(self.document["cases"])
        wrong = []
        for index, run in enumerate(self.document["runs"]):
            where = f"{CORPUS_PATH}#runs[{index}]"
            if not isinstance(run, dict) or set(run) != RUN_FIELDS:
                wrong.append(f"{where}: fields are not exactly {sorted(RUN_FIELDS)}")
                continue
            if run["corpus_sha256"] != expected:
                wrong.append(
                    f"{where}: recorded against corpus {run['corpus_sha256'][:12]} "
                    f"and the cases on disk digest to {expected[:12]}"
                )
        self.assertEqual(
            wrong, [],
            "a recorded run block does not describe the corpus in this file; "
            f"regrade against the current cases rather than editing the digest: {wrong}",
        )

    def test_a_malformed_corpus_fails_by_name_rather_than_reading_as_empty(self):
        """The guard behind the fixed-path read.

        A half-written or non-UTF-8 corpus must stop the suite naming the file,
        not parse as zero cases and let every other check report clean over
        nothing.
        """
        hostile = {
            "truncated": b'{"schema": "promise-machine-router-selection/v1", "cases": [',
            "not utf-8": b'{"cases": [{"id": "\xff\xfe"}]}',
            "not an object": b"[]",
            "no cases": b'{"schema": "x", "pairs": [], "cases": [], "runs": []}',
            "cases not a list": b'{"schema": "x", "pairs": [], "cases": {}, "runs": []}',
        }
        for label, raw in hostile.items():
            with self.subTest(corpus=label):
                with self.assertRaises(CorpusError) as caught:
                    parse_corpus(raw)
                self.assertIn(CORPUS_PATH, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
