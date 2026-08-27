"""Hold the router-selection corpus to the prose it claims to grade.

`tests/test_portable_skills.py` checks that the router resolves: its links
reach real files, its canonical names match their directories and stay unique.
None of that presents a request. This module holds the corpus that does: every
case names the canonical skill the router should select, and quotes the
sentence that decides it from the file that sentence lives in.

What a pass here establishes is narrow and deliberate. The corpus has the shape
its schema declares, every canonical name it expects is a real skill under
`plugins/`, every sentence it quotes still occurs in the file it names, every
router row has a case presenting a request for it, and every sibling boundary
the corpus declares has a case that makes something choose between its members.
It establishes nothing about how an agent routes. That is a recorded grading run's
subject, and a recorded score is never this suite's pass condition.

The comparison collapses runs of whitespace before searching, so rewrapping a
paragraph does not fail the check and rewording one does. A reader who changes
a boundary sentence gets a failure naming the case, the file and the sentence
that is no longer there.

Collapsing costs two things, and neither is a defect the check can see. A
whitespace-only edit that changes how Markdown renders -- a newline inside a
table row, four spaces that turn prose into a code block -- leaves every quote
matching. And because the section's lines join with single spaces, a quotation
may span two adjacent rows or list items that no reader would read as one
sentence. Constraining that needs a rule about what counts as one sentence,
which the router's ambiguity rule now states rather than this module; what this
module does refuse is a quotation that is empty, because an empty string occurs in every section and would pass here
while establishing nothing.
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
# The prompt the graded context received, committed beside the corpus and
# reached the same way: one fixed constant, no argument, no caller component.
PROMPT_TEMPLATE_PATH = "tests/fixtures/router-selection/prompt-template.txt"
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
# A failure entry is model output written into a committed file, so its shape
# is closed: one case id this corpus holds and one canonical skill name.
FAILURE_FIELDS = frozenset({"case", "selected"})
REFUSALS = frozenset({"ambiguous", "uncovered"})

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

# The two guard corpora, named by key rather than by path. `load_corpus` keeps
# one fixed path and gains no argument; a caller that wants a degraded corpus
# picks from this closed set, so no path a caller computes reaches the disk.
GUARD_CORPORA = {
    "altered-sentence": "tests/fixtures/router-selection/guard-altered-sentence.json",
    "missing-row": "tests/fixtures/router-selection/guard-missing-row.json",
}

ROUTER_SECTION = "## Select one runtime contract"
# The one row whose canonical selection is a phrase rather than a name: the
# vendored Pashov suite ships several skills behind a single router row, so its
# case names one of them and quotes the row instead.
UNNAMED_ROW_SELECTION = "The named upstream Pashov skill"

SKILL_NAME = re.compile(r"(?m)^name:\s*([^\n]+)$")
TABLE_ROW = re.compile(r"(?m)^\|(?P<request>[^|]+)\|(?P<contract>[^|]+)\|(?P<selection>[^|]+)\|\s*$")
CANONICAL_CELL = re.compile(r"^`([a-z0-9-]+)`$")


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


def prompt_template_digest() -> str:
    """Digest the committed prompt template.

    A run block names the prompt it was graded under by digest. The digest is
    only evidence if the bytes it names are in the repository, so the checker
    reads them rather than trusting the recorded value.
    """
    path = REPOSITORY_ROOT / PROMPT_TEMPLATE_PATH
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise CorpusError(
            f"{PROMPT_TEMPLATE_PATH} could not be read: {error}"
        ) from error
    return hashlib.sha256(raw).hexdigest()


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


def sentence_faults(where: str, sentence) -> list:
    """Hold one `deciding_sentence` to its shape.

    `text` and `section` are required to be non-empty here rather than left to
    the occurrence check, because `"" in anything` is true: an empty quotation
    satisfies that check over every section of every file, so a corpus could
    void the prose binding case by case and still report clean.
    """
    if not isinstance(sentence, dict) or set(sentence) != SENTENCE_FIELDS:
        return [f"{where}: deciding_sentence is not {sorted(SENTENCE_FIELDS)}"]
    faults = []
    if sentence["path"] not in PROSE_SOURCES:
        faults.append(
            f"{where}: deciding_sentence names {sentence['path']!r}, which is "
            f"outside the quotable set {sorted(PROSE_SOURCES)}"
        )
    for field in ("section", "text"):
        if not isinstance(sentence[field], str) or not sentence[field].strip():
            faults.append(f"{where}: deciding_sentence {field} is not a non-empty string")
    return faults


def pair_faults(document: dict) -> list:
    """Hold the pairs block to the same shape the cases are held to.

    Pairs quote prose exactly as cases do, so an unchecked pair is an unchecked
    quotation: its path would skip the occurrence check rather than fail there,
    and a pair that lost its sentence entirely would go unnoticed.
    """
    faults = []
    for index, pair in enumerate(document["pairs"]):
        where = f"{CORPUS_PATH}#pairs[{index}]"
        if not isinstance(pair, dict) or set(pair) != PAIR_FIELDS:
            faults.append(f"{where}: fields are not exactly {sorted(PAIR_FIELDS)}")
            continue
        if not isinstance(pair["id"], str) or not pair["id"].strip():
            faults.append(f"{where}: id is not a non-empty string")
        if not isinstance(pair["skills"], list) or len(pair["skills"]) < 2 or any(
            not isinstance(name, str) or not name for name in pair["skills"]
        ):
            faults.append(f"{where}: skills is not a list of at least two canonical names")
        faults.extend(sentence_faults(where, pair["deciding_sentence"]))
    return faults


def run_faults(runs: list, expected: str) -> list:
    """Hold every recorded run block to its field set, digest and arithmetic.

    The promise files a run's counts under `measured`, which establishes that a
    value was observed under a recorded method. A block whose counts cannot all
    be true measured nothing, so the arithmetic the study gives them is checked
    here: every case the run covered was passed or failed, and a run records
    every failing case id.
    """
    faults = []
    for index, run in enumerate(runs):
        where = f"{CORPUS_PATH}#runs[{index}]"
        if not isinstance(run, dict) or set(run) != RUN_FIELDS:
            faults.append(f"{where}: fields are not exactly {sorted(RUN_FIELDS)}")
            continue
        if run["corpus_sha256"] != expected:
            faults.append(
                f"{where}: recorded against corpus {run['corpus_sha256'][:12]} "
                f"and the cases on disk digest to {expected[:12]}"
            )
        counts = {}
        for field in ("cases", "passed", "failed"):
            value = run[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                faults.append(f"{where}: {field} is not a count, it is {value!r}")
            else:
                counts[field] = value
        if len(counts) == 3 and counts["passed"] + counts["failed"] != counts["cases"]:
            faults.append(
                f"{where}: {counts['passed']} passed and {counts['failed']} failed "
                f"do not account for {counts['cases']} cases"
            )
        failures = run["failures"]
        if not isinstance(failures, list):
            faults.append(f"{where}: failures is not a list")
        elif "failed" in counts and len(failures) != counts["failed"]:
            faults.append(
                f"{where}: {counts['failed']} failed but {len(failures)} failing "
                f"case id(s) are recorded; a run records every one of them"
            )
    return faults


def run_completeness_faults(runs: list, case_ids: set, names: set, template: str) -> list:
    """Hold every recorded run block to its identity fields and its failures.

    `run_faults` holds a block's field set, its digest and the arithmetic
    between its counts. None of that reads what the identity fields say or
    what a failure names, so a block could carry an empty model, no date, a
    run over no cases at all, or the same failing case id twice and satisfy
    it. A block nobody can read back to the run that produced it is not
    evidence about one model on one date, which is the only thing a recorded
    score is.

    The recorded prompt-template digest is held equal to the digest of the
    template committed beside the corpus. A digest naming bytes the repository
    does not hold is the defect this corpus exists to argue against, one level
    up: a claim bound to nothing a later reader can retrieve. Holding them
    equal makes a regrade under a different prompt commit that prompt.
    """
    faults = []
    for index, run in enumerate(runs):
        where = f"{CORPUS_PATH}#runs[{index}]"
        if not isinstance(run, dict):
            faults.append(f"{where}: is not an object")
            continue
        model = run.get("model")
        if not isinstance(model, str) or not model.strip():
            faults.append(f"{where}: model is not a non-empty string, it is {model!r}")
        date = run.get("date")
        if not isinstance(date, str) or not ISO_DATE.match(date):
            faults.append(f"{where}: date is not a YYYY-MM-DD date, it is {date!r}")
        recorded = run.get("prompt_template_sha256")
        if not isinstance(recorded, str) or not SHA256.match(recorded):
            faults.append(
                f"{where}: prompt_template_sha256 is not a sha256 digest, it is "
                f"{recorded!r}; without it the prompt the run used is unrecoverable"
            )
        elif recorded != template:
            faults.append(
                f"{where}: prompt_template_sha256 records {recorded}, and "
                f"{PROMPT_TEMPLATE_PATH} digests to {template}; a score is evidence "
                f"about the prompt that produced it, so commit the prompt this run "
                f"used rather than editing the block to agree"
            )
        covered = run.get("cases")
        if isinstance(covered, int) and not isinstance(covered, bool) and covered < 1:
            faults.append(
                f"{where}: covered {covered} cases, so its counts are consistent "
                f"with each other and measure nothing"
            )
        failures = run.get("failures")
        if not isinstance(failures, list):
            continue
        seen = set()
        for position, failure in enumerate(failures):
            spot = f"{where}.failures[{position}]"
            if not isinstance(failure, dict) or set(failure) != FAILURE_FIELDS:
                faults.append(f"{spot}: fields are not exactly {sorted(FAILURE_FIELDS)}")
                continue
            case = failure["case"]
            if case not in case_ids:
                faults.append(f"{spot}: names case {case!r}, which this corpus does not hold")
            elif case in seen:
                faults.append(f"{spot}: names case {case!r} a second time")
            seen.add(case)
            if failure["selected"] not in names:
                faults.append(
                    f"{spot}: records the selection {failure['selected']!r}, which is "
                    f"not the frontmatter name of any SKILL.md under plugins/"
                )
    return faults


def prose_sources() -> dict:
    """Read the closed quotable set once, mapped path to text."""
    return {
        path: (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
        for path in sorted(PROSE_SOURCES)
    }


def quotation_faults(document: dict, sources: dict) -> list:
    """Every quoted sentence the file it names no longer carries.

    Split out of the method that asserts on it so a degraded corpus can be run
    through the same code the real corpus is run through. A guard that
    reimplemented the search would prove the guard works and say nothing about
    the check.
    """
    missing = []
    for owner, sentence in quoting(document):
        if not isinstance(sentence, dict):
            missing.append(f"{owner}: deciding_sentence is not an object")
            continue
        if sentence.get("path") not in sources:
            missing.append(
                f"{owner}: {sentence.get('path')!r} is outside the quotable set "
                f"{sorted(PROSE_SOURCES)}, so its sentence was never looked for"
            )
            continue
        if not collapsed(sentence.get("text") or ""):
            missing.append(
                f"{owner}: the quotation is empty, which occurs in every section "
                f"and would pass while establishing nothing"
            )
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
    return missing


def guard_corpus(name: str) -> dict:
    """Parse one of the two guard corpora, chosen by key from a closed set.

    The degraded corpora are read here rather than through `load_corpus`,
    which resolves one fixed path and takes no argument. Giving that loader a
    parameter so a test could aim it would put the first caller-supplied
    component into the only path this module opens for corpus data.
    """
    return parse_corpus((REPOSITORY_ROOT / GUARD_CORPORA[name]).read_bytes())


def router_rows(section: str) -> list:
    """Every selection row of the router's tables, as (request, selection).

    The header and separator lines are dropped by shape rather than by index,
    so a table gaining a row above or below them is still read.
    """
    rows = []
    for match in TABLE_ROW.finditer(section):
        request = collapsed(match.group("request"))
        selection = collapsed(match.group("selection"))
        if request == "Request" or set(request) <= set("- "):
            continue
        rows.append((request, selection))
    return rows


def row_coverage_faults(document: dict, rows: list) -> list:
    """Every router row no case presents a request for.

    This is the check that makes the corpus decay loudly. A row added to the
    router, or a case retired from the corpus, leaves a selection claim that
    nothing grades, and without this the gap is noticed whenever somebody next
    counts by hand.

    Rows are matched two ways because the router names its selection two ways.
    A row whose selection cell is a canonical name in backticks is covered by a
    case expecting that name. The one row that names no skill -- the vendored
    Pashov suite ships several behind it -- is covered by a case that selects
    something and quotes the row's own request predicate, which is the study's
    rule that the row's case names a skill rather than the row's phrase. A
    selection cell of any third shape is a fault, so a later unnamed row fails
    here instead of being skipped by both branches.

    Matching a named row by its selection alone leaves one way for a row to
    arrive ungraded, and it is not a shape the three branches above can see. Two
    rows selecting the same canonical skill are covered by one case, so the
    second row's request predicate is a selection claim nothing presents a
    request for -- the decay this check exists to make loud. A repeated
    selection is therefore a fault in its own right. The unnamed row needs no
    such rule: its branch matches the row's own request predicate rather than a
    skill name, so a second row carrying the same phrase already fails.
    """
    selected, quoted = set(), set()
    for case in document["cases"]:
        expect = case.get("expect")
        if not isinstance(expect, dict) or expect.get("outcome") != "select":
            continue
        selected.add(expect.get("canonical"))
        sentence = case.get("deciding_sentence")
        if isinstance(sentence, dict):
            quoted.add(collapsed(sentence.get("text") or ""))
    faults, claimed = [], set()
    for request, selection in rows:
        named = CANONICAL_CELL.match(selection)
        if named:
            if named.group(1) in claimed:
                faults.append(
                    f"router row {request!r} selects {named.group(1)!r}, which an "
                    f"earlier row already selects; coverage matches a named row by "
                    f"its skill, so one case would stand in for both and this row's "
                    f"request predicate would be graded by nothing"
                )
            claimed.add(named.group(1))
            if named.group(1) not in selected:
                faults.append(
                    f"router row {request!r} selects {named.group(1)!r} and no case "
                    f"expects it, so that row's selection claim is graded by nothing"
                )
        elif selection == UNNAMED_ROW_SELECTION:
            if request not in quoted:
                faults.append(
                    f"router row {request!r} names no canonical skill, so its case "
                    f"is the one that selects a skill and quotes the row, and no "
                    f"case does"
                )
        else:
            faults.append(
                f"router row {request!r} selects {selection!r}, which is neither a "
                f"canonical name in backticks nor {UNNAMED_ROW_SELECTION!r}; a row "
                f"this check cannot read is a row it would silently pass"
            )
    return faults


def pair_coverage_faults(document: dict) -> list:
    """Every declared pair no case actually contests.

    A pairs block is a list of boundaries the corpus claims to grade. A pair
    with no case behind it grades nothing: the boundary sentence is quoted and
    checked, and no request is ever presented that has to choose between the
    skills the sentence separates.
    """
    contested = [
        set(case["contested"])
        for case in document["cases"]
        if isinstance(case.get("contested"), list)
        and all(isinstance(name, str) for name in case["contested"])
    ]
    faults = []
    for index, pair in enumerate(document["pairs"]):
        where = f"{CORPUS_PATH}#pairs[{index}]"
        if not isinstance(pair, dict) or not isinstance(pair.get("skills"), list):
            faults.append(f"{where}: has no list of separated skills to contest")
            continue
        wanted = set(pair["skills"])
        if not any(wanted <= holder for holder in contested):
            faults.append(
                f"pair {pair.get('id')!r} separates {sorted(wanted)} and no case "
                f"contests all of them, so the boundary is declared and never graded"
            )
    return faults


class RouterSelectionCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = load_corpus()
        cls.sources = prose_sources()
        cls.rows = router_rows(
            section_of(cls.sources[ROUTER_PATH], ROUTER_SECTION) or ""
        )

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
            wrong.extend(sentence_faults(where, case["deciding_sentence"]))
        wrong.extend(pair_faults(self.document))
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
        missing = quotation_faults(self.document, prose_sources())
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

        The counts are held to the arithmetic the study gives them: every case
        the run covered was either passed or failed, and a run with failures
        records every failing case id. The promise files those counts under
        `measured`, which establishes that a value was observed under a recorded
        method, so a block whose counts cannot all be true is not a measurement
        of anything. The completeness of the block and the shape of each failure
        entry belong to step 3's own method.
        """
        wrong = run_faults(
            self.document["runs"], corpus_digest(self.document["cases"])
        )
        self.assertEqual(
            wrong, [],
            "a recorded run block does not describe the corpus in this file; "
            f"regrade against the current cases rather than editing the digest: {wrong}",
        )

    def test_the_recorded_run_block_is_complete_and_names_its_failures(self):
        """The half of a run block the digest check leaves unread.

        A score is only ever evidence about one model, one prompt template,
        one corpus digest and one date, so a block that does not say all four
        cites nothing. The digest check covers the corpus half. This covers the
        rest: who ran it, when, against which prompt template, over how many
        cases, and which case each failure names.

        A failure entry carries one case id this corpus holds and one canonical
        skill name, and no other key. Both sides are closed sets the checker
        already validates, which is what keeps model output out of a committed
        file. Recording a selection this suite cannot resolve, or the same
        failing case twice, would leave a score nobody could recount.
        """
        faults = run_completeness_faults(
            self.document["runs"],
            {case.get("id") for case in self.document["cases"]},
            set(canonical_skill_names()),
            prompt_template_digest(),
        )
        self.assertEqual(
            faults, [],
            "a recorded run block cannot be read back to the run that produced "
            "it, so the score it carries is not evidence about any model on any "
            f"date:\n  " + "\n  ".join(faults),
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
            "no pairs block": b'{"schema": "x", "cases": [{}], "runs": []}',
            "pairs not a list": b'{"schema": "x", "cases": [{}], "pairs": {}, "runs": []}',
            "no runs block": b'{"schema": "x", "cases": [{}], "pairs": []}',
            "runs not a list": b'{"schema": "x", "cases": [{}], "pairs": [], "runs": {}}',
        }
        for label, raw in hostile.items():
            with self.subTest(corpus=label):
                with self.assertRaises(CorpusError) as caught:
                    parse_corpus(raw)
                self.assertIn(CORPUS_PATH, str(caught.exception))

        # A corpus that parses can still read as empty. These are the shapes
        # that satisfied every check above while quoting nothing, so each one
        # is exercised against the validator rather than trusted to the corpus
        # on disk, which is well-formed and therefore proves nothing about them.
        good = {"path": "AGENTS.md", "section": "## Marketplace boundaries",
                "text": "Horos decides what an agent does not read."}
        vacuous = {
            "empty quotation": dict(good, text=""),
            "whitespace quotation": dict(good, text="   "),
            "empty section": dict(good, section=""),
            "quotation is not a string": dict(good, text=None),
            "path outside the closed set": dict(good, path="README.md"),
            "path escaping the tree": dict(good, path="../../../etc/passwd"),
            "sentence is not an object": "Horos decides what an agent does not read.",
        }
        for label, sentence in vacuous.items():
            with self.subTest(sentence=label):
                self.assertNotEqual(
                    sentence_faults("probe", sentence), [],
                    f"a {label} was accepted, so the prose binding can be voided "
                    f"entry by entry while every check reports clean",
                )
            with self.subTest(pair=label):
                document = {"pairs": [{"id": "probe", "skills": ["horos", "lemma"],
                                       "deciding_sentence": sentence}]}
                self.assertNotEqual(
                    pair_faults(document), [],
                    f"a pair carrying a {label} was accepted; pairs quote prose "
                    f"exactly as cases do and are held to the same shape",
                )

        # A run block that parses can still record counts that cannot all be
        # true. The promise files those counts under `measured`, so each shape
        # below is exercised against the validator rather than trusted to a
        # corpus that records no run yet.
        digest = "0" * 64
        honest = {"model": "m", "date": "2026-08-27", "prompt_template_sha256": "0" * 64,
                  "corpus_sha256": digest, "cases": 24, "passed": 24, "failed": 0,
                  "failures": []}
        self.assertEqual(
            run_faults([honest], digest), [],
            "an internally consistent run block was rejected",
        )
        for label, block in {
            "passed and failed exceeding cases": dict(honest, passed=24, failed=24),
            "passed exceeding cases": dict(honest, passed=99, failed=0, cases=24),
            "a negative failure count": dict(honest, passed=29, failed=-5),
            "counts recorded as strings": dict(honest, passed="24", failed="0"),
            "a boolean count": dict(honest, passed=True, failed=0, cases=1),
            "fewer failing ids than failures": dict(honest, passed=23, failed=1, failures=[]),
            "more failing ids than failures": dict(honest, failures=["RS-01"]),
            "failures that are not a list": dict(honest, failures={}),
            "a digest from another corpus": dict(honest, corpus_sha256="f" * 64),
        }.items():
            with self.subTest(run=label):
                self.assertNotEqual(
                    run_faults([block], digest), [],
                    f"a run block recording {label} was accepted, so a value the "
                    f"promise calls measured need not be internally true",
                )

        for label, pair in {
            "pair of an unknown shape": {"nonsense": True},
            "pair that lost its sentence": {"id": "p", "skills": ["horos", "lemma"]},
            "pair separating one skill": {"id": "p", "skills": ["horos"],
                                          "deciding_sentence": good},
            "pair naming an empty skill": {"id": "p", "skills": ["horos", ""],
                                           "deciding_sentence": good},
            "pair with no id": {"id": "", "skills": ["horos", "lemma"],
                                "deciding_sentence": good},
        }.items():
            with self.subTest(pair=label):
                self.assertNotEqual(
                    pair_faults({"pairs": [pair]}), [],
                    f"a {label} was accepted, so the pairs block carries no shape",
                )

    def test_every_router_row_is_named_by_at_least_one_case(self):
        """A router row nothing grades is a selection claim on trust.

        The corpus's reason to exist is that each row of the router asserts
        which requests it owns and nothing tested that. A row with no case
        restores exactly the gap the corpus was written to close, and a row
        added later would open it again quietly.
        """
        section = section_of(self.sources[ROUTER_PATH], ROUTER_SECTION)
        self.assertIsNotNone(section, f"{ROUTER_PATH} has no {ROUTER_SECTION!r}")
        lines = [line for line in section.splitlines() if line.startswith("|")]
        headers = sum(1 for line in lines if collapsed(line).startswith("| Request |"))
        self.assertTrue(headers, "no selection table was found in the router")
        self.assertEqual(
            len(self.rows), len(lines) - 2 * headers,
            "the row parser read a different number of rows than the section holds "
            "table lines, so a row it skipped would pass this check unexamined",
        )
        faults = row_coverage_faults(self.document, self.rows)
        self.assertEqual(
            faults, [],
            "the router makes a selection claim the corpus never presents a request "
            f"for; add a case for the row or retire the row:\n  " + "\n  ".join(faults),
        )

    def test_every_declared_pair_has_at_least_one_contested_case(self):
        """A boundary is graded by a request that has to choose, or not at all.

        The pairs block quotes the sentence that separates two siblings and the
        prose binding keeps that quotation current. Neither presents a request.
        Without a case whose `contested` list holds the pair's members, the
        corpus declares a boundary it never asks anything to respect.
        """
        self.assertTrue(
            self.document["pairs"],
            f"{CORPUS_PATH} declares no pairs, so this check would pass over nothing "
            f"while the corpus graded no sibling boundary at all",
        )
        faults = pair_coverage_faults(self.document)
        self.assertEqual(
            faults, [],
            "a declared pair has no case that contests it, so the boundary is quoted "
            f"and never graded:\n  " + "\n  ".join(faults),
        )

    def test_an_altered_deciding_sentence_fails_the_prose_binding_check(self):
        """The guard behind the prose binding.

        `test_every_deciding_sentence_occurs_in_the_file_it_names` passes over
        a corpus whose quotations are all current, which is the only corpus it
        ever sees. That proves the check ran, not that it can fail. This drives
        the same function over a corpus whose sentence has been reworded.
        """
        self.assertEqual(
            quotation_faults(self.document, self.sources), [],
            "the corpus on disk quotes prose that has moved, which this guard "
            "needs to be clean before it can say anything about the degraded one",
        )
        faults = quotation_faults(guard_corpus("altered-sentence"), self.sources)
        self.assertNotEqual(
            faults, [],
            "a corpus whose deciding sentence was reworded was accepted, so the "
            "prose binding cannot fail and establishes nothing",
        )
        self.assertEqual(
            len(faults), 1,
            f"the fixture reworded one sentence and left the other current, so a "
            f"second fault means the check refuses more than the rewording: {faults}",
        )
        self.assertIn(
            "GA-02", faults[0],
            f"the failure does not name the case that carries the reworded "
            f"sentence, so a reader is sent looking for it: {faults[0]}",
        )
        self.assertIn(
            "source-linked fragments", faults[0],
            f"the failure does not quote the sentence that was looked for and not "
            f"found, which is what tells a reader whether to requote or to revert: "
            f"{faults[0]}",
        )

    def test_a_router_row_with_no_case_fails_the_coverage_check(self):
        """The guard behind the row coverage check.

        The corpus on disk covers every row, so the coverage check over it can
        only ever pass. This drives the same function over a corpus with one
        row uncovered, and over the three router defects no fixture can hold:
        the unnamed Pashov row left unquoted, a selection cell of a shape the
        check cannot read, and two rows selecting the same canonical skill.
        """
        self.assertEqual(
            row_coverage_faults(self.document, self.rows), [],
            "the corpus on disk leaves a router row uncovered, which this guard "
            "needs to be clean before it can say anything about the degraded one",
        )
        faults = row_coverage_faults(guard_corpus("missing-row"), self.rows)
        self.assertNotEqual(
            faults, [],
            "a corpus leaving a router row uncovered was accepted, so the coverage "
            "check cannot fail and establishes nothing",
        )
        self.assertEqual(
            len(faults), 1,
            f"the fixture is the corpus's own row cases with one removed, so a "
            f"second fault means either the parser lost a row or the router gained "
            f"one the fixture never had: {faults}",
        )
        self.assertIn(
            "lemma", faults[0],
            f"the failure does not name the row the fixture leaves uncovered: {faults[0]}",
        )

        # Three router defects the fixture cannot carry, because they are
        # defects of the router rather than of a corpus. Each is driven against
        # the same function, so no branch ships having never run.
        covered = {"cases": [
            {"expect": {"outcome": "select", "canonical": "x-ray"},
             "deciding_sentence": {"path": ROUTER_PATH, "section": ROUTER_SECTION,
                                   "text": "Run audit-readiness"}},
        ]}
        for label, rows in {
            "the unnamed row quoted by no case": [
                ("Run audit-readiness, Solidity review, or stateful fuzzing",
                 UNNAMED_ROW_SELECTION),
            ],
            "a selection cell of a third shape": [
                ("Do something new", "Ask the maintainers"),
            ],
            # Both rows are covered by the one case above, which is the point:
            # without the repeated-selection fault the second row would pass
            # while nothing presented a request for its predicate.
            "two rows selecting the same canonical skill": [
                ("Run audit-readiness on this protocol", "`x-ray`"),
                ("Review these contracts for security", "`x-ray`"),
            ],
        }.items():
            with self.subTest(router=label):
                self.assertNotEqual(
                    row_coverage_faults(covered, rows), [],
                    f"{label} was accepted, so a router row this check cannot read "
                    f"would pass it unexamined",
                )



if __name__ == "__main__":
    unittest.main()
