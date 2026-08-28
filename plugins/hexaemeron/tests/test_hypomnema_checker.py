"""The Hypomnema record lint catches pointers that lead nowhere.

A record pointing at something absent is worse than no record, because it
reads as though the reason exists and was checked.
"""

import importlib.util
import io
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "hypomnema" / "scripts" / "hypomnema.py"
ALERT_FIXTURES = ROOT / "tests" / "fixtures" / "ephoros" / "alert-rules"

spec = importlib.util.spec_from_file_location("hypomnema_lint", SCRIPT)
hypomnema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hypomnema)


def codes(source, *, siblings=(), adrs=None):
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        for name in siblings:
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("present", encoding="utf-8")
        path = base / "record.md"
        path.write_text(source, encoding="utf-8")
        return sorted(f.code for f in hypomnema.check(path, adrs))


def hypomnema_findings(source, *, siblings=()):
    """Every finding for one Markdown document, so a line number can be read."""
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        for name in siblings:
            target = base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("present", encoding="utf-8")
        path = base / "record.md"
        path.write_text(source, encoding="utf-8")
        return hypomnema.check(path)


def yaml_codes(source, *, siblings=(), name="rules.yaml"):
    with tempfile.TemporaryDirectory() as directory:
        base = Path(directory)
        for sibling in siblings:
            target = base / sibling
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("present", encoding="utf-8")
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        return sorted(f.code for f in hypomnema.check(path))


class Links(unittest.TestCase):
    def test_it_flags_a_link_to_nothing(self):
        self.assertIn("H001", codes("See [the ledger](EVOLUTION.md)."))

    def test_it_allows_a_link_that_resolves(self):
        self.assertEqual([], codes("See [the ledger](EVOLUTION.md).",
                                   siblings=("EVOLUTION.md",)))

    def test_it_allows_an_external_link(self):
        self.assertEqual([], codes("See [the spec](https://example.org/spec)."))

    def test_it_allows_an_anchor_on_a_file_that_exists(self):
        self.assertEqual([], codes("See [rule four](rules.md#four).",
                                   siblings=("rules.md",)))

    def test_it_ignores_links_inside_a_code_fence(self):
        self.assertEqual([], codes("```\n[example](nowhere.md)\n```\n"))

    def test_it_ignores_an_image(self):
        self.assertEqual([], codes("![diagram](missing.png)"))

    def test_clean_pointer_check_does_not_establish_record_correctness(self):
        self.assertEqual(
            [],
            codes(
                "See [the decision](decision.md).",
                siblings=("decision.md",),
            ),
        )

    def test_missing_pointer_recovers_when_target_is_restored(self):
        source = "See [the decision](decision.md)."
        self.assertIn("H001", codes(source))
        self.assertEqual([], codes(source, siblings=("decision.md",)))


class Superseding(unittest.TestCase):
    def test_it_flags_a_successor_that_does_not_exist(self):
        self.assertIn("H002", codes("## Status\nSuperseded by ADR-009\n",
                                    adrs={"ADR-001"}))

    def test_it_allows_a_successor_that_exists(self):
        self.assertEqual([], codes("## Status\nSuperseded by ADR-009\n",
                                   adrs={"ADR-001", "ADR-009"}))


class Runbooks(unittest.TestCase):
    def test_it_flags_a_missing_runbook(self):
        self.assertIn("H003", codes("Alert: pending age. runbook: docs/runbooks/pending.md"))

    def test_it_allows_a_runbook_that_exists(self):
        self.assertEqual([], codes("Alert: pending age. runbook: docs/runbooks/pending.md",
                                   siblings=("docs/runbooks/pending.md",)))

    def test_it_ignores_prose_after_the_word_runbook(self):
        self.assertEqual([], codes(
            "Three lines is a runbook: what fired, what to check, who to wake."))

    def test_word_suffixes_do_not_create_runbook_pointers(self):
        for prefix in ("myrunbook", "ourrunbook"):
            with self.subTest(prefix=prefix):
                self.assertEqual([], codes(
                    f"{prefix}: runbooks/missing.md"))

    def test_a_hyphenated_runbook_token_does_not_create_a_pointer(self):
        self.assertEqual([], codes(
            "sub-runbook: runbooks/missing.md"))

    def test_the_left_boundary_preserves_live_runbook_forms(self):
        for source in (
            "runbook: runbooks/missing.md",
            "- runbook: runbooks/missing.md",
            "annotations.runbook: runbooks/missing.md",
        ):
            with self.subTest(source=source):
                self.assertEqual(["H003"], codes(source))

    def test_markdown_h003_is_unchanged(self):
        source = "Alert: pending age. runbook: docs/runbooks/pending.md"
        self.assertEqual(["H003"], codes(source))
        self.assertEqual([], codes(source, siblings=("docs/runbooks/pending.md",)))


    # A quoted specimen tells nobody a file exists. These guards fix the
    # boundary between the two readings, one per concern the study registered.

    def test_a_wholly_quoted_pointer_is_a_specimen(self):
        self.assertEqual([], codes(
            "The round reproduced it with `runbook: runbooks/missing.md`."))

    def test_a_backticked_path_after_a_bare_keyword_stays_live(self):
        self.assertEqual(["H003"], codes(
            "Alert: pending age. runbook: `docs/runbooks/pending.md`"))
        self.assertEqual([], codes(
            "Alert: pending age. runbook: `docs/runbooks/pending.md`",
            siblings=("docs/runbooks/pending.md",)))

    def test_an_unmatched_backtick_run_opens_no_span(self):
        self.assertEqual(["H003"], codes(
            "`the round said runbook: runbooks/missing.md"))

    def test_an_escaped_backtick_pair_opens_no_span(self):
        self.assertEqual(["H003"], codes(
            "\\`runbook: runbooks/missing.md\\`"))

    def test_an_escaped_backslash_still_opens_a_span(self):
        self.assertEqual([], codes(
            "\\\\`runbook: runbooks/missing.md`"))

    def test_a_span_does_not_carry_to_the_next_line(self):
        findings = [f.code for f in hypomnema_findings(
            "an opening `tick\nrunbook: runbooks/missing.md`\n")]
        self.assertEqual(["H003"], findings)

    def test_both_recorded_ledger_specimens_go_clean(self):
        self.assertEqual([], codes(
            "An alert pointer such as `runbook: runbooks/missing#book.md` is "
            "accepted by Ephoros as a relative Markdown annotation."))
        self.assertEqual([], codes(
            "reproduced it with `runbook: runbooks/present.md` followed by a "
            "more-indented `extra`."))

    def test_a_span_hides_no_other_code(self):
        self.assertEqual(["H002"], codes(
            "## Status\n`Superseded by ADR-009`\n", adrs={"ADR-001"}))

    # H001 reads a relative link the same way: quoted in a span it is a
    # mention, and the same boundaries keep a live link read.

    def test_a_relative_link_inside_a_code_span_is_a_specimen(self):
        self.assertEqual([], codes(
            "The row links `[study and runbook](../../docs/study/)` from the ledger."))

    def test_a_bare_relative_link_on_the_same_kind_of_line_stays_live(self):
        self.assertEqual(["H001"], codes(
            "The row links [study and runbook](../../docs/study/) from the ledger."))
        self.assertEqual(["H001"], codes(
            "`[quoted](missing-a.md)` beside [live](missing-b.md)."))

    def test_an_unmatched_backtick_run_leaves_a_link_read(self):
        self.assertEqual(["H001"], codes(
            "`the row said [study and runbook](../../docs/study/)"))

    def test_a_span_crossing_a_line_break_leaves_a_link_read(self):
        findings = hypomnema_findings(
            "an opening `tick\n[study and runbook](../../docs/study/)`\n")
        self.assertEqual([("H001", 2)], [(f.code, f.line) for f in findings])

    def test_the_recorded_study_specimen_goes_clean(self):
        # Line 805 of docs/fiat-host-byline-readback/study.md, byte for byte:
        # a ledger-relative link quoted in a code span, which resolves from
        # the ledger and not from the study.
        self.assertEqual([], codes(
            "  `[study and runbook](../../../../docs/fiat-host-byline-readback/)`, relative"))

    def test_a_link_whose_text_is_a_code_span_is_still_read(self):
        # The common documentation form: the span is the link text and the
        # opening bracket sits before it, so the link is read and resolved
        # like any other. A rule that skipped every link touching a span
        # would drop these silently, with fewer findings and no red test.
        self.assertEqual(["H001"], codes(
            "See [`hexctl.py`](scripts/missing.py) for the gate."))
        self.assertEqual([], codes(
            "See [`hexctl.py`](scripts/hexctl.py) for the gate.",
            siblings=("scripts/hexctl.py",)))
        self.assertEqual(["H001"], codes(
            "See [the `hexctl.py` gate](scripts/missing.py)."))

    def test_a_span_holding_part_of_a_link_decides_by_its_bracket(self):
        # CommonMark binds a code span before a link, so a bracket inside a
        # span opens no link and the line is a specimen, while a bracket
        # outside a span opens a link the lint still reads even when the
        # span swallows the rest of it: the ambiguous case stays reported.
        self.assertEqual([], codes("`[text`](missing.md)"))
        self.assertEqual(["H001"], codes("[te`xt](missing.md)`"))

    def test_a_reasoned_pragma_still_suppresses_a_live_pointer(self):
        self.assertEqual([], codes(
            "runbook: runbooks/missing.md "
            "<!-- hypomnema: allow the target lands in the next step -->"))

    def test_backticks_carry_no_span_meaning_in_yaml(self):
        source = "note: `quoted`\nrunbook: runbooks/missing.md\n"
        self.assertEqual(["H003"], yaml_codes(source))

    def test_the_span_scan_stays_linear_on_an_adversarial_line(self):
        # 60k characters and 30k runs, the shape of this plugin's own round-1
        # adversarial sweep. A pair search over runs that never match is
        # quadratic and would not return inside this bound.
        line = ("` " * 30000) + " runbook: runbooks/missing.md"
        started = time.perf_counter()
        self.assertEqual(["H003"], codes(line))
        self.assertLess(time.perf_counter() - started, 2.0)


class YamlRunbooks(unittest.TestCase):
    def test_a_dangling_yaml_pointer_reports_h003(self):
        findings = hypomnema.check(ALERT_FIXTURES / "dangling.yaml")
        self.assertEqual(["H003"], [finding.code for finding in findings])

    def test_a_yaml_pointer_recovers_when_its_target_is_restored(self):
        source = "annotations:\n  runbook: runbooks/pending.md\n"
        self.assertEqual(["H003"], yaml_codes(source))
        self.assertEqual([], yaml_codes(source, siblings=("runbooks/pending.md",)))

    def test_a_yaml_pointer_resolves_from_the_yaml_files_directory(self):
        source = "runbook: runbooks/pending.md\n"
        self.assertEqual([], yaml_codes(
            source,
            name="config/rules.yaml",
            siblings=("config/runbooks/pending.md",),
        ))

    def test_the_yaml_pass_is_generic_and_accepts_a_top_level_pointer(self):
        source = "runbook: runbooks/pending.md\n"
        self.assertEqual([], yaml_codes(source, siblings=("runbooks/pending.md",)))

    def test_comments_and_block_scalars_do_not_create_yaml_pointers(self):
        source = ("# runbook: runbooks/comment.md\n"
                  "notes: |\n"
                  "  runbook: runbooks/example.md\n")
        self.assertEqual([], yaml_codes(source))

    def test_the_complete_alert_to_runbook_fixture_is_clean(self):
        alert = ALERT_FIXTURES / "complete.yaml"
        runbook = ALERT_FIXTURES / "runbooks" / "pending-submission-too-old.md"
        self.assertEqual([], hypomnema.check(alert))
        self.assertEqual([], hypomnema.check(runbook))

    def test_an_oversized_yaml_file_fails_visibly(self):
        source = "#" * (hypomnema.MAX_YAML_BYTES + 1)
        self.assertEqual(["H000"], yaml_codes(source))

    def test_yaml_read_requests_only_the_cap_plus_one_byte(self):
        class RecordingReader(io.BytesIO):
            requested = None

            def read(self, size=-1):
                self.requested = size
                return super().read(size)

        reader = RecordingReader(b"#" * (hypomnema.MAX_YAML_BYTES + 1))
        with mock.patch.object(Path, "open", return_value=reader), \
                mock.patch.object(Path, "read_bytes", side_effect=AssertionError):
            findings = hypomnema.check(Path("bounded.yaml"))
        self.assertEqual(["H000"], [finding.code for finding in findings])
        self.assertEqual(hypomnema.MAX_YAML_BYTES + 1, reader.requested)

    def test_bare_sequence_block_scalars_do_not_create_runbook_pointers(self):
        for marker in ("|", ">"):
            with self.subTest(marker=marker):
                source = f"examples:\n  - {marker}\n    runbook: runbooks/example.md\n"
                self.assertEqual([], yaml_codes(source))

    def test_yaml_runbook_keys_are_case_sensitive(self):
        self.assertEqual([], yaml_codes("Runbook: runbooks/wrong-case.md\n"))

    def test_an_unseparated_hash_is_preserved_in_a_missing_runbook_path(self):
        source = "runbook: runbooks/missing#book.md\n"
        self.assertEqual(["H003"], yaml_codes(source))

    def test_multiline_quoted_runbook_text_does_not_fire_h003(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = (f"note: {quote}\n"
                          "  runbook: runbooks/quoted.md\n"
                          f"  {quote}\n")
                self.assertEqual([], yaml_codes(source))

    def test_quotes_inside_plain_scalars_do_not_hide_runbook_pointers(self):
        for quote, value in (("'", "O'Brien"), ('"', 'six" pipe')):
            with self.subTest(quote=quote):
                source = f"note: {value}\nrunbook: runbooks/missing.md\n"
                self.assertEqual(["H003"], yaml_codes(source))

    def test_unseparated_quote_starts_do_not_hide_runbook_pointers(self):
        for shape in ("- note: plain:{quote}text", "  -{quote}text"):
            for quote in ("'", '"'):
                with self.subTest(shape=shape, quote=quote):
                    source = (f"{shape.format(quote=quote)}\n"
                              "runbook: runbooks/missing.md\n")
                    self.assertEqual(["H003"], yaml_codes(source))

    def test_plain_scalar_continuation_quotes_do_not_hide_runbook_pointers(self):
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                source = ("note: first\n"
                          f"  {quote}continued\n"
                          "runbook: runbooks/missing.md\n")
                self.assertEqual(["H003"], yaml_codes(source))

    def test_a_folded_plain_runbook_cannot_resolve_through_a_first_line_decoy(self):
        source = "runbook: runbooks/present.md\n  extra\n"
        self.assertEqual(
            ["H003"], yaml_codes(source, siblings=("runbooks/present.md",)))

    def test_a_valid_folded_plain_runbook_resolves_as_one_path(self):
        source = "runbook: runbooks/present.md\n  target.md\n"
        self.assertEqual([], yaml_codes(
            source, siblings=("runbooks/present.md target.md",)))

    def test_a_single_line_plain_runbook_stays_clean(self):
        source = "runbook: runbooks/present.md\n"
        self.assertEqual(
            [], yaml_codes(source, siblings=("runbooks/present.md",)))

    def test_a_blank_plain_fold_cannot_resolve_through_a_space_decoy(self):
        source = "runbook: runbooks/present\n\n  target.md\n"
        self.assertEqual(["H003"], yaml_codes(
            source, siblings=("runbooks/present target.md",)))

    def test_a_blank_plain_fold_resolves_the_newline_path(self):
        source = "runbook: runbooks/present\n\n  target.md\n"
        self.assertEqual([], yaml_codes(
            source, siblings=("runbooks/present\ntarget.md",)))


COMPLETE_RUNBOOK = """# Pending age

## What fired

The pending-age alert fired.

## First check

Check the oldest pending item.

## Who to wake

Wake the on-call maintainer.
"""


def runbook_findings(source, name="pending.md", directory="docs/runbooks"):
    with tempfile.TemporaryDirectory() as base:
        target = Path(base) / directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        return hypomnema.check(target)


class RunbookShape(unittest.TestCase):
    def test_a_complete_runbook_is_clean(self):
        self.assertEqual([], runbook_findings(COMPLETE_RUNBOOK))

    def test_h007_still_rejects_a_missing_required_answer(self):
        source = COMPLETE_RUNBOOK.replace("## Who to wake\n", "## Escalation\n")
        self.assertEqual(["H007"], [f.code for f in runbook_findings(source)])

    def test_each_answer_is_required(self):
        for name in hypomnema.RUNBOOK_SECTIONS:
            with self.subTest(section=name):
                source = COMPLETE_RUNBOOK.replace(f"## {name}\n", "## Kept out\n")
                findings = runbook_findings(source)
                self.assertEqual(["H007"], [f.code for f in findings])
                self.assertIn(f"## {name}", findings[0].message)

    def test_each_answer_must_be_non_empty(self):
        bodies = {
            "What fired": "The pending-age alert fired.\n",
            "First check": "Check the oldest pending item.\n",
            "Who to wake": "Wake the on-call maintainer.\n",
        }
        for name, body in bodies.items():
            with self.subTest(section=name):
                findings = runbook_findings(COMPLETE_RUNBOOK.replace(body, ""))
                self.assertEqual(["H007"], [f.code for f in findings])
                self.assertIn("empty", findings[0].message)

    def test_a_markdown_file_outside_a_runbooks_directory_is_out_of_scope(self):
        self.assertEqual([], runbook_findings("", directory="docs", name="runbook.md"))

    def test_a_heading_inside_a_fence_does_not_count(self):
        source = COMPLETE_RUNBOOK.replace(
            "## Who to wake\n\nWake the on-call maintainer.\n",
            "```markdown\n## Who to wake\n\nWake the on-call maintainer.\n```\n",
        )
        self.assertEqual(["H007"], [f.code for f in runbook_findings(source)])

    def test_fenced_example_text_does_not_fill_an_empty_answer(self):
        source = COMPLETE_RUNBOOK.replace(
            "Check the oldest pending item.\n",
            "```text\nCheck the oldest pending item.\n```\n",
        )
        self.assertEqual(["H007"], [f.code for f in runbook_findings(source)])

    def test_a_reasoned_pragma_on_the_first_line_suppresses_all_shape_findings(self):
        source = "<!-- hypomnema: allow generated downstream -->\n"
        self.assertEqual([], runbook_findings(source))

    def test_a_reasoned_pragma_on_the_relevant_heading_suppresses_its_finding(self):
        source = COMPLETE_RUNBOOK.replace(
            "## First check\n\nCheck the oldest pending item.",
            "## First check <!-- hypomnema: allow supplied during deployment -->",
        )
        self.assertEqual([], runbook_findings(source))

    def test_a_pragma_above_the_relevant_heading_does_not_suppress(self):
        source = COMPLETE_RUNBOOK.replace(
            "## First check\n\nCheck the oldest pending item.",
            "<!-- hypomnema: allow supplied during deployment -->\n## First check",
        )
        self.assertEqual(["H007"], [f.code for f in runbook_findings(source)])

    def test_a_bare_pragma_does_not_suppress(self):
        source = "<!-- hypomnema: allow -->\n"
        self.assertEqual(["H007", "H007", "H007"],
                         [f.code for f in runbook_findings(source)])

    def test_the_fixture_runbooks_name_six_shape_faults(self):
        files = hypomnema.walk([str(FIXTURES / "runbooks")])
        findings = [finding for path in files for finding in hypomnema.check(path)]
        self.assertEqual(["H007"] * 6, sorted(f.code for f in findings))


class Suppression(unittest.TestCase):
    def test_a_stated_reason_on_the_line_above_suppresses(self):
        self.assertEqual([], codes(
            "<!-- hypomnema: allow generated in the target repository -->\n"
            "See [generated output](invariants.md)."))

    def test_a_stated_reason_on_the_same_line_suppresses(self):
        self.assertEqual([], codes(
            "See [it](invariants.md). <!-- hypomnema: allow generated downstream -->"))

    def test_a_pragma_below_the_finding_does_not_suppress(self):
        self.assertIn("H001", codes(
            "See [generated output](invariants.md).\n"
            "<!-- hypomnema: allow generated in the target repository -->"))

    def test_a_bare_pragma_does_not_suppress(self):
        self.assertIn("H001", codes(
            "<!-- hypomnema: allow -->\nSee [generated output](invariants.md)."))


class OverTheMarketplace(unittest.TestCase):
    def test_the_vendored_suite_is_skipped_by_default(self):
        marketplace = ROOT.parents[1]
        paths = hypomnema.walk([str(marketplace / "plugins" / "hexaemeron" / "skills")])
        self.assertEqual([], [p for p in paths if "x-ray" in p.parts])

    def test_a_directory_named_like_source_is_not_read_as_source(self):
        with tempfile.TemporaryDirectory() as base:
            (Path(base) / "generated.sol").mkdir()
            self.assertEqual([], hypomnema.walk([base]))


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hypomnema"

COMPLETE_RECORD = """# ADR-051: A complete specimen

## Status

Accepted, 2026-08-21.

## Context

What forced a choice.

## Decision

What was chosen.

## Alternatives

- What lost, and why.

## Consequences

What this commits us to.
"""


def record_codes(source, name="ADR-051-complete.md", directory="decisions"):
    with tempfile.TemporaryDirectory() as base:
        target = Path(base) / directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        return sorted(f.code for f in hypomnema.check(target))


class RecordShape(unittest.TestCase):
    def test_a_complete_record_is_clean(self):
        self.assertEqual([], record_codes(COMPLETE_RECORD))

    def test_each_of_the_five_sections_is_required(self):
        for name in hypomnema.SECTIONS:
            with self.subTest(section=name):
                source = COMPLETE_RECORD.replace(f"## {name}\n", f"## Kept out\n")
                found = record_codes(source)
                self.assertIn("H004", found)

    def test_the_finding_names_the_missing_section(self):
        source = COMPLETE_RECORD.replace("## Alternatives\n", "## Options\n")
        with tempfile.TemporaryDirectory() as base:
            target = Path(base) / "decisions" / "ADR-051-complete.md"
            target.parent.mkdir(parents=True)
            target.write_text(source, encoding="utf-8")
            found = hypomnema.check(target)
        self.assertEqual(["H004"], [f.code for f in found])
        self.assertIn("## Alternatives", found[0].message)

    def test_an_undated_status_is_a_finding(self):
        source = COMPLETE_RECORD.replace("Accepted, 2026-08-21.", "Accepted.")
        self.assertEqual(["H005"], record_codes(source))

    def test_an_empty_status_section_is_a_finding(self):
        source = COMPLETE_RECORD.replace("Accepted, 2026-08-21.\n", "")
        self.assertEqual(["H005"], record_codes(source))

    def test_a_file_not_named_as_a_record_earns_no_shape_verdict(self):
        source = COMPLETE_RECORD.replace("## Alternatives\n", "## Options\n")
        self.assertEqual([], record_codes(source, name="notes.md"))

    def test_a_record_name_outside_a_decisions_directory_earns_no_shape_verdict(self):
        source = COMPLETE_RECORD.replace("## Alternatives\n", "## Options\n")
        self.assertEqual([], record_codes(source, directory="drafts"))

    def test_a_section_heading_inside_a_fence_does_not_count(self):
        source = COMPLETE_RECORD.replace(
            "## Alternatives\n\n- What lost, and why.\n",
            "```markdown\n## Alternatives\n```\n")
        self.assertEqual(["H004"], record_codes(source))

    def test_a_pragma_on_the_first_line_suppresses_the_missing_section(self):
        source = COMPLETE_RECORD.replace(
            "# ADR-051: A complete specimen",
            "# ADR-051: A complete specimen "
            "<!-- hypomnema: allow imported before the template settled -->"
        ).replace("## Alternatives\n", "## Options\n")
        self.assertEqual([], record_codes(source))

    def test_a_pragma_on_the_status_heading_suppresses_the_dated_check(self):
        source = COMPLETE_RECORD.replace(
            "## Status", "## Status <!-- hypomnema: allow imported undated -->"
        ).replace("Accepted, 2026-08-21.", "Accepted.")
        self.assertEqual([], record_codes(source))

    def test_the_fixture_records_name_each_omission(self):
        findings = []
        for path in sorted((FIXTURES / "decisions").glob("*.md")):
            findings.extend(hypomnema.check(path))
        self.assertEqual(sorted(f.code for f in findings),
                         ["H004", "H004", "H004", "H005"])

    def test_the_walk_skips_fixture_specimens_by_default(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / "bar.md").write_text(COMPLETE_RECORD, encoding="utf-8")
            (root / "fixtures").mkdir()
            (root / "fixtures" / "foo.md").write_text(COMPLETE_RECORD, encoding="utf-8")
            paths = hypomnema.walk([str(root)])
            self.assertIn("bar.md", {p.name for p in paths})
            self.assertEqual([], [p for p in paths if "fixtures" in p.parts])

    def test_naming_a_fixtures_path_still_reads_it(self):
        paths = hypomnema.walk([str(FIXTURES / "decisions")])
        self.assertEqual(2, len(paths))


def source_codes(source, name="specimen.py", adrs=frozenset({"ADR-001"})):
    with tempfile.TemporaryDirectory() as base:
        target = Path(base) / name
        target.write_text(source, encoding="utf-8")
        return sorted(f.code for f in hypomnema.check(target, set(adrs)))


class SourceComments(unittest.TestCase):
    def test_a_hash_comment_citing_a_missing_record_is_a_finding(self):
        source = "".join(["# see ", "ADR-909", "\n"]) + "WINDOW = 60\n"
        self.assertEqual(["H006"], source_codes(source))

    def test_a_comment_citing_a_present_record_resolves(self):
        source = "".join(["# see ", "ADR-001", "\n"]) + "WINDOW = 60\n"
        self.assertEqual([], source_codes(source))

    def test_a_trailing_comment_is_scanned(self):
        source = "WINDOW = 60  " + "# per " + "ADR-909" + "\n"
        self.assertEqual(["H006"], source_codes(source))

    def test_a_reference_inside_a_string_is_left_alone(self):
        source = 'MESSAGE = "superseded by ' + 'ADR-909"' + "\n"
        self.assertEqual([], source_codes(source))

    def test_a_quote_glued_marker_is_left_alone(self):
        source = 'HEADING = "' + '## Status ' + 'ADR-909"' + "\n"
        self.assertEqual([], source_codes(source))

    def test_a_slash_comment_in_solidity_is_scanned(self):
        source = "".join(["/// see ", "ADR-909", "\n"]) + "uint256 x;\n"
        self.assertEqual(["H006"], source_codes(source, name="specimen.sol"))

    def test_a_block_comment_is_scanned(self):
        source = "/*\n   recorded in " + "ADR-909" + "\n*/\nuint256 x;\n"
        self.assertEqual(["H006"], source_codes(source, name="specimen.sol"))

    def test_a_url_double_slash_is_left_alone(self):
        source = 'URL = "https://example.org/' + 'ADR-909"' + "\n"
        self.assertEqual([], source_codes(source, name="specimen.ts"))

    def test_a_marker_pragma_on_the_line_suppresses(self):
        source = ("WINDOW = 60  " + "# per " + "ADR-909"
                  + "  # hypomnema: allow recorded downstream\n")
        self.assertEqual([], source_codes(source))

    def test_a_marker_pragma_above_the_line_suppresses(self):
        source = ("# hypomnema: allow recorded downstream\n"
                  + "WINDOW = 60  " + "# per " + "ADR-909" + "\n")
        self.assertEqual([], source_codes(source))

    def test_a_file_with_no_index_earns_no_verdict(self):
        source = "".join(["# see ", "ADR-909", "\n"])
        with tempfile.TemporaryDirectory() as base:
            target = Path(base) / "specimen.py"
            target.write_text(source, encoding="utf-8")
            self.assertEqual([], hypomnema.check(target, None))

    def test_the_source_fixtures_name_the_one_dangling_reference(self):
        files = hypomnema.walk([str(FIXTURES)])
        index = hypomnema.adr_index(files)
        findings = []
        for path in files:
            findings.extend(hypomnema.check(path, index))
        self.assertEqual(["H006"],
                         sorted(f.code for f in findings if f.code == "H006"))



if __name__ == "__main__":
    unittest.main()
