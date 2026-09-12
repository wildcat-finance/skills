"""Step 13: the four guards the risk register still owed, and the record.

Steps 11 and 12 built the registry and the second implementation. This suite
closes the four register rows that were left as this step's obligations, and
each guard names the exact specimen or bytes that reproduce its concern.

`registry-mutability`. The registry is a module-level constant, so every write
attempted after import is tried here for real rather than asserted about the
source text: assignment, replacement of an entry, deletion, and the four
mutating methods a plain dict would have. A source that declares an
implementation in its own bytes, a curation policy field that names a module
path and an environment variable naming one are each run through the pipeline
that would have to honour them.

`synopsis-cell-splitting`. Three specimens: a producer cell whose content
carries the literal separator, an unterminated finding row, and a file whose
final line is truncated. Each is checked against the source bytes rather than
against a rendering, and the question asked of each is whether anything
shortened reached a record.

`mapper-backtracking`. Every pattern the synopsis mapper runs is fed the widest
cell any admitted source produces, and the decision record has to carry the
outcome in one of the two forms the runbook allows. No duration is asserted
anywhere here: study section 10 declares no budget, and a guard that asserted
a wall clock would be one.

`fail-open-mapper`. The synopsis implementation is fed the format the first
implementation owns and the exact bytes the pilot preserves, because those are
the two inputs a mapper that fails open would accept in silence.

Beside them the record itself is checked, and both shipped releases are rebuilt,
because a guard suite that let a release id drift would be guarding nothing.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import textwrap
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
WORKTREE = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"

PILOT = PLUGIN_ROOT / "specimens/pilot"
ESTATE = PLUGIN_ROOT / "specimens/estate"
SYNOPSIS = PLUGIN_ROOT / "specimens/synopsis"
DECISIONS = PLUGIN_ROOT / "docs/decisions"

# One Warden Markdown record that is not a specimen, so the fail-open probe
# covers the format the first implementation owns and not only the three files
# the pilot preserves.
WARDEN_MARKDOWN = WORKTREE / "plugins/hexaemeron/audit/AUDIT.md"

PILOT_RELEASE = "41d640fb168049d5061e12c9d7282dafad2266343eeb0be2a078db8797c0bfbf"
ESTATE_RELEASE = "509239765f9fa2db782d3bc70fadea3b05411fc0638402fe5e0a43882f0063e3"
SYNOPSIS_RELEASE = "74c591e1f010868b3aadd048cdeb6db20df9ea4ac146b43f52c577a41dd6ac39"

SHIPPED_ENTRIES = {
    ("warden-audit-round-markdown", "1"),
    ("fiat-audit-synopsis", "1"),
}
SYNOPSIS_MAPPER = {"name": "fiat-audit-synopsis", "version": "1"}
UNRESOLVED = "A078"
NOT_MY_FORMAT = "A079"

SYNOPSIS_FINDINGS = 41
SYNOPSIS_ASSERTIONS = 173

# The five patterns `parse_synopsis` and `read_cells` run between them. The
# helper below derives the set from the two functions, so a pattern added to
# either one fails this guard rather than escaping it.
EXPECTED_PATTERNS = {
    "SYNOPSIS_HEADER",
    "ROUND_HEADING",
    "OTHER_HEADING",
    "ROUND_FIELD",
    "FINDING_ROW",
}

# The two forms the runbook allows the backtracking outcome to take. The record
# has to carry exactly one of them, and this guard fails if it carries neither.
OUTCOME_MARKER = "Backtracking outcome:"
OUTCOME_FORMS = (
    re.compile(
        r"^Backtracking outcome: the source byte cap restated as the only "
        r"bound claimed\.$"),
    re.compile(r"^Backtracking outcome: a measured bound of .+?\.(?:\s|$)"),
)


def outcome_sentence(text: str) -> list[str]:
    """The `Backtracking outcome:` sentence, read across its line wrapping.

    A record is hard-wrapped, so the sentence is not a line. Reading it line by
    line made the record's shape depend on where a wrap happened to fall, which
    is a property of the margin and not of the claim.
    """
    found = []
    for paragraph in text.split("\n\n"):
        flat = " ".join(paragraph.split())
        if flat.startswith(OUTCOME_MARKER):
            found.append(flat)
    return found

RECORD_SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")
RECORD_HEADING = re.compile(r"^# ADR-\d{3}: \S.*$")
RECORD_STATUS = re.compile(r"^Accepted, \d{1,2} [A-Z][a-z]+ \d{4}\.$|^Accepted, \d{4}-\d{2}-\d{2}\.$")

# The three decisions study section 12 sends to this record, each as a phrase
# the record has to carry once whitespace is normalised.
DECISION_PHRASES = (
    "The mapper is resolved through a registry keyed by name and version, and "
    "the resolved entry is what an assertion records.",
    "The mapper stays in the curation policy rather than moving per source.",
    "The second corpus preserves the same findings the pilot preserves.",
)
MEASURED_CITATION = (
    "per-source-mapper-shipped-release-policies-changed.json")
MEASURED_VALUE = "`shipped-release-policies-changed` value is 2"
SECOND_HOME = "scope.preserves"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anamnesis = load("anamnesis_guards", SCRIPT)


def scratch_directory(prefix: str = "anamnesis-s13-"):
    """Transient space under the ignored top-level tmp/, which git never sees."""
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def source_bytes(source_id: str) -> bytes:
    """The admitted bytes as they sit on disk, never a rendering of them."""
    return (SYNOPSIS / "sources" / f"{source_id}.md").read_bytes()


def admitted_source_ids() -> list[str]:
    policy = json.loads((SYNOPSIS / "policy.json").read_text(encoding="utf-8"))
    return [entry["id"] for entry in policy["sources"]]


def cells_of(raw: bytes) -> list[str]:
    """Every producer cell an admitted source produces, from its own bytes."""
    lines = raw.decode("utf-8").splitlines()
    return [
        cell
        for line in lines[1:]
        for cell in line.split(anamnesis.SYNOPSIS_SEPARATOR)
    ]


def widest_admitted_cell() -> tuple[str, str, int]:
    """The widest cell any admitted synopsis source produces, and where it is."""
    widest, home, width = "", "", -1
    for source_id in admitted_source_ids():
        for cell in cells_of(source_bytes(source_id)):
            size = len(cell.encode("utf-8"))
            if size > width:
                widest, home, width = cell, source_id, size
    return widest, home, width


def patterns_the_synopsis_mapper_runs() -> dict:
    """Every compiled pattern named inside `parse_synopsis` or `read_cells`.

    Derived rather than listed, so a pattern added to either function is fed
    the widest cell too instead of quietly escaping the guard.
    """
    found = {}
    for function in (anamnesis.parse_synopsis, anamnesis.read_cells):
        source = textwrap.dedent(inspect.getsource(function))
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Name):
                value = getattr(anamnesis, node.id, None)
                if isinstance(value, re.Pattern):
                    found[node.id] = value
    return found


def decision_records() -> list[Path]:
    return sorted(DECISIONS.glob("ADR-*.md"))


def committed_decision_record() -> Path:
    """The one record this step committed, found by the outcome it has to carry.

    The number is chosen against the default branch immediately before the pull
    request is pushed, so nothing here may depend on it being 007.
    """
    carrying = [
        path for path in decision_records()
        if OUTCOME_MARKER in path.read_text(encoding="utf-8")
    ]
    if len(carrying) != 1:
        raise AssertionError(
            f"expected exactly one decision record under {DECISIONS} carrying "
            f"{OUTCOME_MARKER!r}, found {[p.name for p in carrying]}"
        )
    return carrying[0]


def normalised(text: str) -> str:
    """Whitespace-folded text, because the record is hard-wrapped prose."""
    return " ".join(text.split())


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        self.scratch = Path(holder.name)

    def copy_specimen(self, shipped: Path, label: str = "") -> Path:
        """A writable copy of a shipped specimen, without its built release."""
        target = self.scratch / f"{shipped.name}{label}"
        shutil.copytree(shipped, target)
        shutil.rmtree(target / "release", ignore_errors=True)
        shutil.rmtree(target / "projections", ignore_errors=True)
        return target

    def rewrite_source(self, specimen: Path, source_id: str, text: str) -> None:
        """Replace one admitted source and re-pin the digest admission checks.

        Admission verifies the digest and the byte count before curation reads
        anything, so a crafted source only reaches the mapper if the policy is
        re-pinned to it. Doing that here is the point: the attempt has to get
        far enough to be refused by the registry rather than by admission.
        """
        policy_path = specimen / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        raw = text.encode("utf-8")
        for entry in policy["sources"]:
            if entry["id"] == source_id:
                (specimen / entry["path"]).write_bytes(raw)
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
                entry["bytes"] = len(raw)
                break
        else:
            raise AssertionError(f"{source_id} is not an admitted source")
        policy_path.write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    def rewrite_mapper(self, specimen: Path, mapper: dict) -> None:
        path = specimen / "curation-policy.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        policy["mapper"] = mapper
        path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

    def refusal(self, call):
        with self.assertRaises(anamnesis.Refusal) as caught:
            call()
        return caught.exception

    def assertRegistryUnchanged(self) -> None:
        self.assertEqual(set(anamnesis.MAPPER_REGISTRY), SHIPPED_ENTRIES)
        for key in SHIPPED_ENTRIES:
            entry = anamnesis.MAPPER_REGISTRY[key]
            self.assertEqual((entry.name, entry.version), key)
        self.assertIs(
            anamnesis.MAPPER_REGISTRY[("fiat-audit-synopsis", "1")].parse,
            anamnesis.parse_synopsis)
        self.assertIs(
            anamnesis.MAPPER_REGISTRY[("warden-audit-round-markdown", "1")].parse,
            anamnesis.parse_source)


# ---------------------------------------------------------------------------
# registry-mutability


class TheRegistryIsClosedAfterImport(Fixture):
    """`registry-mutability`: the module-level map at import time."""

    def test_every_write_attempted_after_import_fails(self) -> None:
        """Real attempts, not assertions about the source text.

        Assignment into the map, replacement of an entry that is already there,
        deletion of one, and the four mutating methods a plain dict would carry
        are each executed against the live object.
        """
        registry = anamnesis.MAPPER_REGISTRY
        shipped = ("warden-audit-round-markdown", "1")
        crafted = anamnesis.Mapper("crafted", "1", anamnesis.parse_source)

        attempts = {
            "assign a new entry":
                lambda: registry.__setitem__(("crafted", "1"), crafted),
            "replace an entry that resolves":
                lambda: registry.__setitem__(shipped, crafted),
            "delete an entry": lambda: registry.__delitem__(shipped),
            "update the map": lambda: registry.update({("crafted", "1"): crafted}),
            "clear the map": lambda: registry.clear(),
            "pop an entry": lambda: registry.pop(shipped),
            "pop any entry": lambda: registry.popitem(),
            "insert through setdefault":
                lambda: registry.setdefault(("crafted", "1"), crafted),
        }
        for label, attempt in attempts.items():
            with self.subTest(attempt=label):
                with self.assertRaises((TypeError, AttributeError)):
                    attempt()

        # The map that survived every attempt is the one resolution reads, and
        # a second independent import agrees with it, so nothing above left a
        # mark that a later reader would inherit.
        self.assertRegistryUnchanged()
        again = load("anamnesis_guards_reimport", SCRIPT)
        self.assertEqual(set(again.MAPPER_REGISTRY), SHIPPED_ENTRIES)
        self.assertEqual(
            {key: (entry.name, entry.version)
             for key, entry in again.MAPPER_REGISTRY.items()},
            {key: (entry.name, entry.version)
             for key, entry in anamnesis.MAPPER_REGISTRY.items()})

    def test_no_source_policy_field_or_environment_variable_reaches_it(self) -> None:
        """Three real attempts to name an implementation from outside the module.

        Each one is run through the pipeline that would have to honour it: a
        source whose own bytes declare an implementation, a curation policy
        field naming a module path, and an environment variable naming one.
        """
        # One: a source that declares an implementation in its own bytes. The
        # admission digest is re-pinned to the crafted bytes on purpose, so the
        # declaration reaches the mapper rather than being stopped short of it.
        specimen = self.copy_specimen(SYNOPSIS, "-declaring")
        original = source_bytes("hexaemeron-audit-synopsis").decode("utf-8")
        header, body = original.split("\n", 1)
        declaring = (
            header + " | mapper=warden-audit-round-markdown | mapper_version=1\n"
            + "mapper: warden-audit-round-markdown<br>"
            + "implementation: "
            + "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py:parse_source\n"
            + body
        )
        self.rewrite_source(specimen, "hexaemeron-audit-synopsis", declaring)
        release_id, _ = anamnesis.verify_rebuild(str(specimen))
        built = self.scratch / "declared-source-release"
        manifest = anamnesis._rebuild_once(str(specimen), str(built))
        assertions = json.loads(
            (built / "assertions.json").read_text(encoding="utf-8"))
        recorded = {
            json.dumps(record["mapper"], sort_keys=True)
            for record in assertions
        }
        self.assertEqual(
            recorded, {json.dumps(SYNOPSIS_MAPPER, sort_keys=True)},
            "a source's own bytes selected an implementation")
        self.assertEqual(len(assertions), SYNOPSIS_ASSERTIONS)
        self.assertEqual(
            sum(1 for record in assertions if record["kind"] == "finding"),
            SYNOPSIS_FINDINGS,
            "the declaration in the source bytes changed what was read")
        self.assertNotEqual(release_id, SYNOPSIS_RELEASE)  # crafted bytes, new id
        self.assertEqual(release_id, manifest["release_id"])
        self.assertRegistryUnchanged()

        # Two: a curation policy field naming a module path. Nothing resolves
        # it, and the refusal lands before a release directory exists.
        paths = (
            "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py:parse_source",
            "anamnesis.parse_synopsis",
            "/etc/anamnesis/mapper.py",
        )
        for index, named in enumerate(paths):
            with self.subTest(module_path=named):
                clean = self.copy_specimen(SYNOPSIS, f"-path-{index}")
                self.rewrite_mapper(clean, {"name": named, "version": "1"})
                destination = self.scratch / f"never-built-{index}"
                refusal = self.refusal(
                    lambda: anamnesis._rebuild_once(str(clean), str(destination)))
                self.assertEqual(refusal.code, UNRESOLVED)
                self.assertFalse(destination.exists())
                self.assertRegistryUnchanged()

        # Three: an environment variable naming an implementation. The rebuild
        # is byte-identical to the one without it, id included.
        control = self.copy_specimen(SYNOPSIS, "-control")
        expected, components = anamnesis.verify_rebuild(str(control))
        self.assertEqual(expected, SYNOPSIS_RELEASE)
        named_by_environment = {
            "ANAMNESIS_MAPPER": "warden-audit-round-markdown",
            "ANAMNESIS_MAPPER_VERSION": "1",
            "ANAMNESIS_MAPPER_MODULE":
                "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py",
            "MAPPER": "warden-audit-round-markdown",
        }
        preserved = {key: os.environ.get(key) for key in named_by_environment}

        def restore() -> None:
            for key, was in preserved.items():
                if was is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = was

        self.addCleanup(restore)
        os.environ.update(named_by_environment)
        under_environment, also = anamnesis.verify_rebuild(str(control))
        self.assertEqual(under_environment, expected)
        self.assertEqual(also, components)
        self.assertRegistryUnchanged()


# ---------------------------------------------------------------------------
# synopsis-cell-splitting


class Fabricated(Fixture):
    """Three crafted synopsis sources, each one named by the bytes it carries."""

    HEADER = (
        "Synopsis schema=fiat-audit-synopsis/v1 | source=x/AUDIT.md | "
        "source_sha256=" + "0" * 64 + " | h2_count=1"
    )
    OPENING = (
        "## Step 1, round 1 -- 2026-09-08",
        "| id | severity | file | finding | status |",
        "| --- | --- | --- | --- | --- |",
    )
    CONTROL = "| S1-R1-99 | high | `control.py` | a complete row | open |"

    def specimen(self, *cells: str, tail: str = "") -> bytes:
        body = anamnesis.SYNOPSIS_SEPARATOR.join(self.OPENING + cells)
        return (self.HEADER + "\n" + body + tail).encode("utf-8")

    def read(self, raw: bytes) -> list:
        return anamnesis.parse_synopsis(raw.decode("utf-8"), "crafted")

    def findings(self, rounds) -> list:
        return [finding for entry in rounds for finding in entry["findings"]]

    def assertNothingShortened(self, raw: bytes, rounds, absent: str) -> None:
        """Every recorded field is the producer's bytes, and `absent` is not there.

        The check is against the source bytes rather than against a rendering:
        each recorded value has to occur in the file as written, and no record
        may carry any leading part of the cell the separator or the truncation
        cut in half.
        """
        text = raw.decode("utf-8")
        for finding in self.findings(rounds):
            for field in ("native_id", "severity", "file", "finding", "status"):
                value = finding[field]
                self.assertIn(
                    value, text,
                    f"recorded {field} {value!r} is not in the source bytes")
            for length in range(4, len(absent) + 1):
                self.assertNotEqual(
                    finding["finding"], absent[:length],
                    "a shortened cell reached a record")

    def assertControlSurvives(self, rounds) -> None:
        """The specimen is not refused wholesale, so the guard is about the cell."""
        recorded = self.findings(rounds)
        self.assertEqual([finding["native_id"] for finding in recorded], ["S1-R1-99"])
        self.assertEqual(recorded[0]["finding"], "a complete row")
        self.assertEqual(recorded[0]["file"], "control.py")

    def test_a_producer_cell_carrying_the_separator_is_never_shortened(self) -> None:
        """The cell is `| S1-R1-01 | high | `a.py` | says <br> and continues | open |`.

        Splitting on the separator cuts it in two, and the finding grammar is
        anchored on a whole cell, so neither half matches. The row is absent
        from the record rather than present in a shortened form.
        """
        content = "says " + anamnesis.SYNOPSIS_SEPARATOR + " and continues"
        cell = f"| S1-R1-01 | high | `a.py` | {content} | open |"
        raw = self.specimen(cell, self.CONTROL)
        self.assertIn(anamnesis.SYNOPSIS_SEPARATOR.encode(), raw)

        rounds = self.read(raw)
        self.assertNothingShortened(raw, rounds, absent="says ")
        self.assertControlSurvives(rounds)

    def test_an_unterminated_finding_row_is_never_shortened(self) -> None:
        """The cell is `| S1-R1-02 | high | `b.py` | the row never closes | open`.

        The closing pipe is missing, so the grammar declines the cell whole and
        no prefix of it is recorded.
        """
        cell = "| S1-R1-02 | high | `b.py` | the row never closes | open"
        raw = self.specimen(cell, self.CONTROL)

        rounds = self.read(raw)
        self.assertNothingShortened(raw, rounds, absent="the row never closes")
        self.assertControlSurvives(rounds)

    def test_a_truncated_final_line_is_never_shortened(self) -> None:
        """The file ends mid-row, with no separator and no newline after it.

        A truncated tail is the shape a partial write leaves. The declined cell
        reaches no record, and the complete rows before it still do.
        """
        raw = self.specimen(
            self.CONTROL, tail=anamnesis.SYNOPSIS_SEPARATOR
            + "| S1-R1-03 | high | `c.py` | the file ends mid-r")
        self.assertFalse(raw.endswith(b"\n"))

        rounds = self.read(raw)
        self.assertNothingShortened(raw, rounds, absent="the file ends mid-r")
        self.assertControlSurvives(rounds)


# ---------------------------------------------------------------------------
# mapper-backtracking


class TheWidestCellIsRunThroughEveryPattern(Fixture):
    """`mapper-backtracking`: the widest cell any admitted source produces."""

    def test_every_pattern_reads_it_and_the_outcome_is_recorded(self) -> None:
        """No duration is asserted. Study section 10 declares no budget.

        Two things have to hold. Every pattern the synopsis mapper runs returns
        on the widest admitted cell, and on every other cell those sources
        produce. And the decision record carries the outcome in one of the two
        forms the runbook allows, so a run that measured nothing and recorded
        nothing fails here rather than passing quietly.
        """
        widest, home, width = widest_admitted_cell()
        self.assertGreater(width, 0)
        self.assertIn(home, admitted_source_ids())
        self.assertIn(widest, source_bytes(home).decode("utf-8"))

        patterns = patterns_the_synopsis_mapper_runs()
        self.assertEqual(set(patterns), EXPECTED_PATTERNS)
        for name, pattern in sorted(patterns.items()):
            with self.subTest(pattern=name):
                # A returned match or a returned None both establish that the
                # pattern terminated on these bytes, which is the claim.
                self.assertIn(
                    type(pattern.match(widest)).__name__, ("Match", "NoneType"))

        for source_id in admitted_source_ids():
            for cell in cells_of(source_bytes(source_id)):
                for pattern in patterns.values():
                    pattern.match(cell)

        record = committed_decision_record()
        text = record.read_text(encoding="utf-8")
        carried = outcome_sentence(text)
        self.assertEqual(
            len(carried), 1,
            f"{record.name} must carry exactly one {OUTCOME_MARKER!r} sentence")
        self.assertTrue(
            any(form.match(carried[0]) for form in OUTCOME_FORMS),
            f"{carried[0]!r} is neither a measured bound nor the byte cap "
            f"restated as the only bound claimed")

        # Whichever form it took, the consequences section is where it sits.
        consequences = text.split("\n## Consequences\n", 1)
        self.assertEqual(len(consequences), 2, "no consequences section")
        self.assertIn(carried[0], outcome_sentence(consequences[1]))


# ---------------------------------------------------------------------------
# fail-open-mapper


class TheSynopsisMapperRefusesWhatIsNotItsFormat(Fixture):
    """`fail-open-mapper`, fed the two inputs a fail-open mapper would accept."""

    def test_it_refuses_warden_markdown_and_the_pilots_own_bytes(self) -> None:
        """`A079` and no rounds, on the first mapper's format and the pilot's files.

        The control matters as much as the refusal: the first implementation
        reads every one of these files and returns rounds, so the refusal is
        about the format declaration and not about bytes nothing can read.
        """
        subjects = {"plugins/hexaemeron/audit/AUDIT.md": WARDEN_MARKDOWN}
        for source in sorted((PILOT / "sources").glob("*.md")):
            subjects[f"pilot/{source.name}"] = source
        self.assertEqual(len(subjects), 4)

        for label, path in sorted(subjects.items()):
            with self.subTest(source=label):
                text = path.read_bytes().decode("utf-8")
                refusal = self.refusal(
                    lambda: anamnesis.parse_synopsis(text, label))
                self.assertEqual(refusal.code, NOT_MY_FORMAT)
                self.assertEqual(refusal.record, label)
                # The bytes are readable Warden Markdown, so nothing empty or
                # partial was returned in place of the refusal.
                self.assertGreater(len(anamnesis.parse_source(text, label)), 0)


# ---------------------------------------------------------------------------
# The record, and the two shipped releases


class TheDecisionRecordCarriesWhatTheStudySentIt(Fixture):
    """hypomnema: all three of study section 12's decisions, in one record."""

    def test_it_carries_five_sections_a_dated_status_and_three_decisions(self) -> None:
        record = committed_decision_record()
        text = record.read_text(encoding="utf-8")
        lines = text.splitlines()

        self.assertRegex(record.name, r"^ADR-\d{3}-[a-z0-9]+(-[a-z0-9]+)*\.md$")
        self.assertTrue(RECORD_HEADING.match(lines[0]), lines[0])
        for section in RECORD_SECTIONS:
            self.assertIn(f"\n## {section}\n", text, f"no {section} section")

        status = text.split("\n## Status\n", 1)[1].split("\n## ", 1)[0].strip()
        self.assertTrue(RECORD_STATUS.match(status), f"undated status {status!r}")

        folded = normalised(text)
        for phrase in DECISION_PHRASES:
            self.assertIn(normalised(phrase), folded, f"decision missing: {phrase}")
        self.assertIn(MEASURED_VALUE, folded, "the measured value 2 is not cited")
        self.assertIn(MEASURED_CITATION, folded, "the report is not named")
        self.assertIn(SECOND_HOME, folded, "decision 3's second home is not cited")

        # Cited rather than restated: the sentence itself lives in the policy
        # that is inside the release, and only one document carries it.
        curation = json.loads(
            (SYNOPSIS / "curation-policy.json").read_text(encoding="utf-8"))
        preserves = curation["scope"]["preserves"]
        self.assertNotIn(normalised(preserves), folded)

    def test_the_pilot_still_rebuilds_to_its_recorded_release_id(self) -> None:
        """`release-identity-drift`: the id this run may not move."""
        release_id, _ = anamnesis.verify_rebuild(str(PILOT))
        self.assertEqual(release_id, PILOT_RELEASE)

    def test_the_estate_still_rebuilds_to_its_recorded_release_id(self) -> None:
        """`release-identity-drift`, at the second shipped corpus."""
        release_id, _ = anamnesis.verify_rebuild(str(ESTATE))
        self.assertEqual(release_id, ESTATE_RELEASE)



class TheFindingRowPatternCannotBacktrackOverWhitespace(unittest.TestCase):
    """S3-R1-01: the property the measured bound rests on, held structurally.

    A greedy `\\s*` beside a lazy group lets the engine try every way of
    splitting one span across both, and `FINDING_ROW` had six such pairs. The
    duration is not asserted here, because study section 10 declares no budget
    and a wall clock would be one. What is asserted is the shape that makes the
    duration linear: no whitespace run in the pattern may be backtrackable.
    """

    def test_every_whitespace_run_in_the_row_pattern_is_possessive(self) -> None:
        pattern = anamnesis.FINDING_ROW.pattern
        # Every `\s*` must be written `\s*+`; a bare one is the ambiguity.
        self.assertNotIn("|", pattern[:1], "pattern is anchored")
        bare = re.findall(r"\\s\*(?!\+)", pattern)
        self.assertEqual(
            bare, [],
            "FINDING_ROW carries a backtrackable whitespace run; every "
            "`\\s*` must be possessive `\\s*+`")
        self.assertGreaterEqual(len(re.findall(r"\\s\*\+", pattern)), 6)

if __name__ == "__main__":
    unittest.main()
