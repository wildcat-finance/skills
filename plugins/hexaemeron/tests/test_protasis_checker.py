"""The Protasis runbook schema check catches a step that omits a field.

A step missing its exit command is invisible until someone reads the runbook
carefully, and the phase that reads it carefully has already started building.
"""

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "protasis" / "scripts" / "protasis.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "protasis"
REPO = ROOT.parents[1]

spec = importlib.util.spec_from_file_location("protasis_check", SCRIPT)
protasis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protasis)

COMPLETE_STEP = """## Step 1: A complete step

**Goal.** Do the thing.
**Entry.** A clean tree.
**Exit.** Proved by `pytest`.
**Files.** `a.py`.
**Tests.** One case.
**Disciplines.** none, docs only.
"""

COMPLETE_RUNBOOK_AMENDMENT = """
### Amendment -- 2026-08-24

**What changed.** Complete replacement Exit: Proved by `fiat-v2.0.0`.
**Why.** The target changed.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.
"""

VERSION_RELATION_ROW = (
    "protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md | "
    "next-generation-after-integration-base"
)


def relation_block(*rows):
    return "```version-relations\n" + "\n".join(rows) + "\n```\n\n"


DESIGN_LOCK_BLOCK = """```design-lock
schema | protasis-design-evidence/v1
sha256 | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
candidate | streaming
```

"""


def findings(source):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "runbook.md"
        path.write_text(source, encoding="utf-8")
        return protasis.check(path)


def codes(source):
    return sorted(f.code for f in findings(source))


def without(field):
    """The complete step with one required field removed."""
    keep = [line for line in COMPLETE_STEP.splitlines()
            if not line.startswith(f"**{field}.**")]
    return "\n".join(keep) + "\n"


class RequiredFields(unittest.TestCase):
    def test_a_complete_step_is_clean(self):
        self.assertEqual(codes(COMPLETE_STEP), [])

    def test_each_required_field_is_required(self):
        for field in protasis.REQUIRED:
            with self.subTest(field=field):
                self.assertIn("P001", codes(without(field)))

    def test_the_finding_names_the_missing_field(self):
        found = findings(without("Disciplines"))
        self.assertEqual(len(found), 1)
        self.assertIn("**Disciplines.**", found[0].message)

    def test_the_finding_names_the_step_it_is_in(self):
        found = findings(without("Goal"))
        self.assertIn("A complete step", found[0].message)

    def test_the_finding_points_at_the_heading_line(self):
        found = findings("\n" + without("Goal"))
        self.assertEqual(found[0].line, 2)


class RunbookAmendments(unittest.TestCase):
    def test_a_complete_final_amendment_is_clean(self):
        self.assertEqual(codes(COMPLETE_STEP + COMPLETE_RUNBOOK_AMENDMENT), [])

    def test_the_amendment_stops_the_last_step_before_replacement_fields(self):
        source = without("Exit") + COMPLETE_RUNBOOK_AMENDMENT
        found = codes(source)
        self.assertIn("P001", found)
        self.assertNotIn("P002", found)

    def test_each_amendment_field_occurs_once_in_order_and_is_not_empty(self):
        for field in protasis.AMENDMENT_FIELDS:
            with self.subTest(field=field):
                lines = [
                    line for line in COMPLETE_RUNBOOK_AMENDMENT.splitlines()
                    if not line.startswith(f"**{field}.**")
                ]
                self.assertIn("P005", codes(COMPLETE_STEP + "\n".join(lines) + "\n"))

        reordered = COMPLETE_RUNBOOK_AMENDMENT.replace(
            "**What changed.** Complete replacement Exit: Proved by `fiat-v2.0.0`.\n"
            "**Why.** The target changed.\n",
            "**Why.** The target changed.\n"
            "**What changed.** Complete replacement Exit: Proved by `fiat-v2.0.0`.\n",
        )
        self.assertIn("P005", codes(COMPLETE_STEP + reordered))
        empty = COMPLETE_RUNBOOK_AMENDMENT.replace(
            "**Why.** The target changed.", "**Why.**"
        )
        self.assertIn("P005", codes(COMPLETE_STEP + empty))

    def test_unknown_duplicate_and_partial_replacement_clauses_refuse(self):
        cases = (
            "Complete replacement Unknown: no.",
            "Complete replacement Exit: first. Complete replacement Exit: second.",
            "The Exit should use v2.",
        )
        for replacement in cases:
            with self.subTest(replacement=replacement):
                source = COMPLETE_STEP + COMPLETE_RUNBOOK_AMENDMENT.replace(
                    "Complete replacement Exit: Proved by `fiat-v2.0.0`.",
                    replacement,
                )
                self.assertIn("P005", codes(source))

    def test_a_complete_replacement_exit_still_needs_its_command(self):
        source = COMPLETE_STEP + COMPLETE_RUNBOOK_AMENDMENT.replace(
            "Complete replacement Exit: Proved by `fiat-v2.0.0`.",
            "Complete replacement Exit: Reviewed and working.",
        )
        self.assertIn("P005", codes(source))

    def test_fenced_amendment_decoy_does_not_end_or_validate_the_step(self):
        decoy = (
            "\n````markdown\n```\n### Amendment -- 2026-08-24\n"
            "**What changed.** vague\n````\n"
        )
        self.assertEqual(codes(COMPLETE_STEP + decoy), [])

    def test_only_three_leading_spaces_may_open_a_markdown_fence(self):
        hidden = (
            "**What changed.** Complete replacement Exit: Proved by `fiat-v2.0.0`.\n"
            "{indent}```\n"
            "## Step 2: Smuggled visible heading\n"
            "{indent}```\n"
        )
        three_spaces = COMPLETE_RUNBOOK_AMENDMENT.replace(
            "**What changed.** Complete replacement Exit: Proved by `fiat-v2.0.0`.\n",
            hidden.format(indent="   "),
        )
        four_spaces = COMPLETE_RUNBOOK_AMENDMENT.replace(
            "**What changed.** Complete replacement Exit: Proved by `fiat-v2.0.0`.\n",
            hidden.format(indent="    "),
        )
        self.assertNotIn("P005", codes(COMPLETE_STEP + three_spaces))
        self.assertIn("P005", codes(COMPLETE_STEP + four_spaces))

    def test_invalid_date_and_a_trailing_step_heading_refuse(self):
        invalid = COMPLETE_RUNBOOK_AMENDMENT.replace("2026-08-24", "2026-02-30")
        self.assertIn("P005", codes(COMPLETE_STEP + invalid))
        malformed = COMPLETE_RUNBOOK_AMENDMENT.replace("2026-08-24", "2026/08/24")
        self.assertIn("P005", codes(COMPLETE_STEP + malformed))
        trailing = COMPLETE_STEP + COMPLETE_RUNBOOK_AMENDMENT + "\n## Step 2: Smuggled\n"
        self.assertIn("P005", codes(trailing))

    def test_two_sequential_complete_amendments_are_checked(self):
        second = COMPLETE_RUNBOOK_AMENDMENT.replace("2026-08-24", "2026-08-25")
        self.assertEqual(codes(COMPLETE_STEP + COMPLETE_RUNBOOK_AMENDMENT + second), [])


class VersionRelations(unittest.TestCase):
    def test_one_valid_block_and_an_absent_legacy_block_are_clean(self):
        self.assertEqual(codes(relation_block(VERSION_RELATION_ROW) + COMPLETE_STEP), [])
        self.assertEqual(codes(COMPLETE_STEP), [])

    def test_partial_target_coverage_is_clean(self):
        two_targets = relation_block(
            "fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | "
            "next-generation-after-integration-base",
            VERSION_RELATION_ROW,
        ) + COMPLETE_STEP
        self.assertEqual(codes(two_targets.replace(
            "fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | "
            "next-generation-after-integration-base\n",
            "",
        )), [])

    def test_a_second_block_or_a_block_after_step_one_refuses(self):
        second = relation_block(VERSION_RELATION_ROW) * 2 + COMPLETE_STEP
        self.assertIn("P006", codes(second))
        self.assertIn(
            "P006",
            codes(COMPLETE_STEP + "\n" + relation_block(VERSION_RELATION_ROW)),
        )

    def test_each_row_has_exactly_three_non_empty_fields(self):
        malformed = (
            "protasis | plugins/hexaemeron/skills/protasis/EVOLUTION.md",
            VERSION_RELATION_ROW + " | extra",
            "protasis |  | next-generation-after-integration-base",
        )
        for row in malformed:
            with self.subTest(row=row):
                self.assertIn("P006", codes(relation_block(row) + COMPLETE_STEP))

    def test_ids_and_paths_are_unique(self):
        duplicate_id = relation_block(VERSION_RELATION_ROW, VERSION_RELATION_ROW)
        duplicate_path = relation_block(
            VERSION_RELATION_ROW,
            "fiat | plugins/hexaemeron/skills/protasis/EVOLUTION.md | "
            "next-generation-after-integration-base",
        )
        self.assertIn("P006", codes(duplicate_id + COMPLETE_STEP))
        self.assertIn("P006", codes(duplicate_path + COMPLETE_STEP))

    def test_unsafe_paths_refuse(self):
        paths = (
            "/plugins/hexaemeron/skills/protasis/EVOLUTION.md",
            "plugins/hexaemeron/skills/../protasis/EVOLUTION.md",
            "plugins/hexaemeron/skills/./protasis/EVOLUTION.md",
            "plugins\\hexaemeron\\skills\\protasis\\EVOLUTION.md",
            "plugins/hexaemeron/skills/protasis/EVOLUTION.md\x1f",
            "plugins/hexa\x80emeron/skills/protasis/EVOLUTION.md",
            "plugins/hexa\u202eemeron/skills/protasis/EVOLUTION.md",
        )
        for path in paths:
            with self.subTest(path=repr(path)):
                row = (
                    f"protasis | {path} | "
                    "next-generation-after-integration-base"
                )
                self.assertIn("P006", codes(relation_block(row) + COMPLETE_STEP))

    def test_unknown_relation_blank_row_and_target_directory_mismatch_refuse(self):
        unknown = VERSION_RELATION_ROW.replace(
            "next-generation-after-integration-base", "next-minor"
        )
        mismatch = VERSION_RELATION_ROW.replace(
            "/protasis/EVOLUTION.md", "/fiat/EVOLUTION.md"
        )
        self.assertIn("P006", codes(relation_block(unknown) + COMPLETE_STEP))
        self.assertIn(
            "P006",
            codes("```version-relations\n" + VERSION_RELATION_ROW + "\n\n```\n" + COMPLETE_STEP),
        )
        self.assertIn("P006", codes(relation_block(mismatch) + COMPLETE_STEP))

    def test_a_fenced_decoy_is_not_a_declaration(self):
        decoy = (
            "````markdown\n"
            "```version-relations\n"
            "bad | row\n"
            "```\n"
            "````\n\n"
        )
        self.assertEqual(codes(decoy + COMPLETE_STEP), [])

    def test_the_closed_block_has_a_row_cap_and_exact_info_string(self):
        rows = tuple(
            f"skill-{number} | plugins/example/skills/skill-{number}/EVOLUTION.md | "
            "next-generation-after-integration-base"
            for number in range(32)
        )
        self.assertEqual(codes(relation_block(*rows) + COMPLETE_STEP), [])
        self.assertIn("P006", codes(relation_block(*rows, VERSION_RELATION_ROW) + COMPLETE_STEP))
        malformed_info = relation_block(VERSION_RELATION_ROW).replace(
            "```version-relations", "```version-relations extra", 1
        )
        self.assertIn("P006", codes(malformed_info + COMPLETE_STEP))

    def test_a_declared_target_has_no_concrete_version_token_outside_the_block(self):
        token = "protasis-v4.8.0"
        valid = relation_block(VERSION_RELATION_ROW) + COMPLETE_STEP
        candidates = (
            valid.replace("```version-relations", token + "\n```version-relations", 1),
            valid.replace("## Step 1", token + "\n\n## Step 1", 1),
            valid.replace("Do the thing.", f"Do the thing for {token}."),
            valid.replace("A clean tree.", f"A clean tree at `{token}`."),
            valid.replace("Proved by `pytest`.", f"Proved by `pytest {token}`."),
            valid.replace("`a.py`.", f"`a.py` and {token}."),
            valid.replace("One case.", f"One case for {token}."),
            valid.replace("none, docs only.", f"none for {token}, docs only."),
            valid.replace(
                "**Tests.** One case.",
                f"**Tests.** One case.\n\n```bash\nprintf '{token}'\n```",
            ),
            valid + COMPLETE_RUNBOOK_AMENDMENT.replace("fiat-v2.0.0", token),
        )
        for position, source in enumerate(candidates):
            with self.subTest(position=position):
                self.assertIn("P006", codes(source))

    def test_relation_findings_do_not_echo_runbook_controlled_values(self):
        rows = (
            "PRIVATE-ID | plugins/example/skills/PRIVATE-ID/EVOLUTION.md | "
            "next-generation-after-integration-base",
            "unknown | plugins/example/skills/unknown/EVOLUTION.md | private-relation",
            "private-target | private-segment/private-target/EVOLUTION.md | "
            "next-generation-after-integration-base",
            "other-target | private-segment/private-target/EVOLUTION.md | "
            "next-generation-after-integration-base",
        )
        source = relation_block(*rows) + COMPLETE_STEP.replace(
            "Do the thing.", "Do the thing at private-target-v1.2.3."
        )
        messages = " ".join(finding.message for finding in findings(source))
        for value in (
            "PRIVATE-ID",
            "private-relation",
            "private-segment",
            "private-target",
        ):
            with self.subTest(value=value):
                self.assertNotIn(value, messages)


class DesignLocks(unittest.TestCase):
    def test_one_valid_block_and_an_absent_legacy_block_are_clean(self):
        self.assertEqual(codes(DESIGN_LOCK_BLOCK + COMPLETE_STEP), [])
        self.assertEqual(codes(COMPLETE_STEP), [])

    def test_duplicate_late_unclosed_and_near_info_blocks_refuse(self):
        cases = (
            DESIGN_LOCK_BLOCK * 2 + COMPLETE_STEP,
            COMPLETE_STEP + DESIGN_LOCK_BLOCK,
            DESIGN_LOCK_BLOCK.replace("\n```\n", "\n", 1) + COMPLETE_STEP,
            DESIGN_LOCK_BLOCK.replace("```design-lock", "```design-lock extra", 1)
            + COMPLETE_STEP,
        )
        for source in cases:
            with self.subTest(source=source[:40]):
                self.assertIn("P007", codes(source))

    def test_rows_are_closed_ordered_and_typed(self):
        cases = (
            DESIGN_LOCK_BLOCK.replace("schema |", "private |", 1),
            DESIGN_LOCK_BLOCK.replace("sha256 | " + "a" * 64, "sha256 | short", 1),
            DESIGN_LOCK_BLOCK.replace("candidate | streaming", "candidate | Bad_Id", 1),
            DESIGN_LOCK_BLOCK.replace("candidate | streaming\n", "", 1),
            DESIGN_LOCK_BLOCK.replace(
                "schema | protasis-design-evidence/v1\nsha256 | " + "a" * 64,
                "sha256 | " + "a" * 64 + "\nschema | protasis-design-evidence/v1",
                1,
            ),
        )
        for source in cases:
            with self.subTest(source=source[:80]):
                self.assertIn("P007", codes(source + COMPLETE_STEP))

    def test_a_design_lock_quoted_in_an_outer_fence_is_inert(self):
        quoted = "````markdown\n" + DESIGN_LOCK_BLOCK + "````\n\n"
        self.assertEqual(codes(quoted + COMPLETE_STEP), [])


class ExitCommands(unittest.TestCase):
    def test_an_exit_with_no_command_is_a_finding(self):
        source = COMPLETE_STEP.replace("**Exit.** Proved by `pytest`.",
                                       "**Exit.** Reviewed and working.")
        self.assertIn("P002", codes(source))

    def test_a_fenced_block_counts_as_a_command(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** Proved by the suite.\n\n```bash\npytest\n```\n")
        self.assertNotIn("P002", codes(source))

    def test_an_inline_span_counts_as_a_command(self):
        self.assertNotIn("P002", codes(COMPLETE_STEP))

    def test_no_exit_reports_the_missing_field_not_the_missing_command(self):
        self.assertEqual(codes(without("Exit")), ["P001"])

    def test_another_field_s_code_does_not_answer_for_the_exit(self):
        """The guard for the step-wide search.

        `**Files.** `a.py`` is close to universal, so a command search over the
        whole step lets any other field answer for the exit and P002 never
        fires on a real runbook.
        """
        source = COMPLETE_STEP.replace("**Exit.** Proved by `pytest`.",
                                       "**Exit.** Reviewed and working.")
        self.assertIn("`a.py`", source)
        self.assertIn("P002", codes(source))

    def test_a_fenced_block_after_the_exit_still_counts(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** Proved by the suite.\n\n```bash\npytest\n```")
        self.assertNotIn("P002", codes(source))

    def test_a_fenced_block_under_a_later_field_does_not_count(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.", "**Exit.** Reviewed.").replace(
            "**Tests.** One case.", "**Tests.** One case.\n\n```bash\npytest\n```")
        self.assertIn("P002", codes(source))


class Documents(unittest.TestCase):
    def test_a_document_with_no_step_is_a_finding(self):
        self.assertEqual(codes("# Title\n\n## Steps\n\nDecided later.\n"),
                         ["P003"])
        malformed_relation = relation_block("bad | row")
        self.assertEqual(codes(malformed_relation), ["P003", "P006"])

    def test_a_step_heading_inside_a_fence_is_not_a_step(self):
        source = "# Title\n\n```markdown\n## Step 1: Example\n```\n"
        self.assertEqual(codes(source), ["P003"])

    def test_a_fenced_heading_does_not_truncate_the_last_step(self):
        """The guard for fence tracking in the end scan.

        A runbook that quotes a step heading inside an example, which this
        repository's own contract does, would otherwise cut its last step short
        at the quote and report the fields below it missing.
        """
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** Proved by:\n\n```markdown\n## Step 99: quoted, not real\n```")
        self.assertEqual(codes(source), [])

    def test_a_tilde_fence_is_a_fence(self):
        """The guard for backtick-only fence matching.

        Tildes are a CommonMark fence, so a runbook using them had its examples
        read as real content: a quoted step heading became a step with no fields
        and the document collected findings it had not earned. A false positive
        costs more trust than a miss.
        """
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** see\n\n~~~\n## Step 9: quoted, not real\n~~~")
        self.assertEqual(codes(source), [])

    def test_a_fence_is_closed_only_by_its_own_marker(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** see\n\n~~~\n```\n## Step 9: quoted\n```\n~~~")
        self.assertEqual(codes(source), [])

    def test_a_longer_fence_run_is_a_fence(self):
        source = COMPLETE_STEP.replace(
            "**Exit.** Proved by `pytest`.",
            "**Exit.** see\n\n````\n## Step 9: quoted\n````")
        self.assertEqual(codes(source), [])

    def test_a_trailing_section_is_not_read_into_the_last_step(self):
        source = COMPLETE_STEP + "\n## Notes\n\n**Goal.** Not a step field.\n"
        self.assertEqual(codes(source), [])

    def test_a_missing_path_is_reported_not_raised(self):
        found = protasis.check(Path("does-not-exist-9d3f.md"))
        self.assertEqual([f.code for f in found], ["P000"])

    def test_a_directory_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            found = protasis.check(Path(directory))
        self.assertEqual([f.code for f in found], ["P000"])

    def test_an_oversized_document_is_refused(self):
        source = COMPLETE_STEP + ("x" * (protasis.MAX_BYTES + 1))
        self.assertEqual(codes(source), ["P000"])

    def test_steps_past_the_cap_are_reported_not_dropped(self):
        """The guard for silent truncation.

        Capping the work is right; capping it and still reporting clean is the
        false confidence this module exists to avoid. A broken step past the cap
        must not hide behind a clean verdict.
        """
        capped = "\n".join(COMPLETE_STEP.replace("Step 1:", f"Step {n}:")
                           for n in range(1, protasis.MAX_STEPS + 1))
        source = capped + "\n## Step 9999: Broken\n\n**Goal.** only this.\n"
        found = codes(source)
        self.assertIn("P004", found)

    def test_a_dropped_step_does_not_answer_for_the_last_tracked_one(self):
        """The guard for span absorption past the cap.

        The last tracked step's body ran to the next non-step heading, so a step
        dropped by the cap donated its fields upward and the broken step above
        it passed while missing five of six.
        """
        original = protasis.MAX_STEPS
        try:
            protasis.MAX_STEPS = 2
            sound = COMPLETE_STEP.replace("Step 1:", "Step 1:")
            broken = "## Step 2: Broken and last tracked\n\n**Goal.** only this.\n"
            past = COMPLETE_STEP.replace("Step 1:", "Step 3:")
            found = codes(sound + "\n" + broken + "\n" + past)
        finally:
            protasis.MAX_STEPS = original
        self.assertEqual(found.count("P001"), 5, found)
        self.assertIn("P004", found)

    def test_a_document_inside_the_cap_reports_no_truncation(self):
        capped = "\n".join(COMPLETE_STEP.replace("Step 1:", f"Step {n}:")
                           for n in range(1, protasis.MAX_STEPS + 1))
        self.assertEqual(codes(capped), [])


class Suppression(unittest.TestCase):
    def test_an_allow_comment_above_the_heading_suppresses_the_step(self):
        source = "<!-- protasis: allow fields live upstream -->\n" + \
                 "## Step 1: Bare\n"
        self.assertEqual(codes(source), [])

    def test_an_allow_comment_on_the_heading_line_suppresses_the_step(self):
        source = "## Step 1: Bare <!-- protasis: allow fields live upstream -->\n"
        self.assertEqual(codes(source), [])

    def test_an_allow_comment_needs_a_reason(self):
        source = "<!-- protasis: allow -->\n## Step 1: Bare\n"
        self.assertIn("P001", codes(source))


class Invocation(unittest.TestCase):
    def test_clean_exits_zero(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = protasis.main([str(FIXTURES / "complete-runbook.md")])
        self.assertEqual(code, 0)
        self.assertIn("clean", buffer.getvalue())

    def test_findings_exit_one(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = protasis.main([str(FIXTURES / "incomplete-runbook.md")])
        self.assertEqual(code, 1)

    def test_json_format_is_machine_readable(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            protasis.main([str(FIXTURES / "incomplete-runbook.md"),
                           "--format", "json"])
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload)
        self.assertEqual(sorted(payload[0]), ["code", "line", "message", "path"])

    def test_no_paths_is_a_bad_invocation(self):
        with self.assertRaises(SystemExit) as caught:
            with redirect_stdout(io.StringIO()):
                protasis.main([])
        self.assertEqual(caught.exception.code, 2)


class Fixtures(unittest.TestCase):
    def test_the_incomplete_fixture_catches_every_omission(self):
        found = protasis.check(FIXTURES / "incomplete-runbook.md")
        missing = {f.message.split("**")[1] for f in found if f.code == "P001"}
        self.assertEqual(missing, {f"{name}." for name in protasis.REQUIRED})
        self.assertEqual(sum(1 for f in found if f.code == "P002"), 1)

    def test_this_runs_own_runbook_is_clean(self):
        """The acceptance condition: the contract's first runbook passes."""
        runbook = REPO / "docs" / "protasis-discipline-cores" / "runbook.md"
        self.assertTrue(runbook.is_file(), runbook)
        self.assertEqual(protasis.check(runbook), [])


if __name__ == "__main__":
    unittest.main()

COMPLETE_STUDY = (FIXTURES / "complete-study.md").read_text(encoding="utf-8")

COMPLETE_STUDY_AMENDMENT = """
### Amendment -- 2026-08-29

**What changed.** Study mode now checks the amendment shape.
**Why.** A malformed correction must fail before it is receipted.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds.
"""


def study_findings(source):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "study.md"
        path.write_text(source, encoding="utf-8")
        return protasis.check_study(path)


def study_codes(source):
    return sorted(f.code for f in study_findings(source))


def without_item(number):
    """The complete study with one item's heading and body removed."""
    lines = COMPLETE_STUDY.splitlines()
    kept, skipping = [], False
    for line in lines:
        match = protasis.ITEM.match(line)
        if match:
            skipping = int(match.group("n")) == number
        if not skipping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def with_answer(number, answer):
    """The complete study with one item's body replaced."""
    lines = COMPLETE_STUDY.splitlines()
    out, skipping = [], False
    for line in lines:
        match = protasis.ITEM.match(line)
        if match:
            if skipping:
                skipping = False
            if int(match.group("n")) == number:
                out.append(line)
                out.append("")
                out.append(answer)
                skipping = True
                continue
        if not skipping:
            out.append(line)
    return "\n".join(out) + "\n"


class StudyAmendments(unittest.TestCase):
    def test_each_fixture_omission_reports_s008(self):
        fixtures = (
            "missing-amendment-date-study.md",
            "missing-amendment-what-changed-study.md",
            "missing-amendment-why-study.md",
            "missing-amendment-steps-touched-study.md",
            "missing-amendment-still-holding-study.md",
        )
        for name in fixtures:
            with self.subTest(fixture=name):
                found = protasis.check_study(FIXTURES / name)
                self.assertEqual([finding.code for finding in found], ["S008"])

    def test_complete_and_absent_amendments_are_clean(self):
        self.assertEqual(
            protasis.check_study(FIXTURES / "complete-amended-study.md"), []
        )
        self.assertEqual(protasis.check_study(FIXTURES / "complete-study.md"), [])

    def test_backtick_tilde_and_longer_closing_fences_hide_decoys(self):
        fences = (
            ("```markdown", "```"),
            ("~~~markdown", "~~~"),
            ("```markdown", "````"),
        )
        for opening, closing in fences:
            with self.subTest(opening=opening, closing=closing):
                decoy = (
                    f"\n{opening}\n"
                    "### Amendment\n"
                    "**Unexpected.** private-amendment-value\n"
                    f"{closing}\n"
                )
                self.assertNotIn("S008", study_codes(COMPLETE_STUDY + decoy))

    def test_malformed_and_non_calendar_dates_report_s008(self):
        for date in ("2026/08/29", "2026-02-30"):
            with self.subTest(date=date):
                source = COMPLETE_STUDY + COMPLETE_STUDY_AMENDMENT.replace(
                    "2026-08-29", date
                )
                self.assertIn("S008", study_codes(source))

    def test_fields_are_ordered_unique_known_and_non_empty(self):
        duplicate = COMPLETE_STUDY_AMENDMENT.replace(
            "**Why.** A malformed correction must fail before it is receipted.",
            "**Why.** First reason.\n**Why.** Second reason.",
        )
        reordered = COMPLETE_STUDY_AMENDMENT.replace(
            "**What changed.** Study mode now checks the amendment shape.\n"
            "**Why.** A malformed correction must fail before it is receipted.\n",
            "**Why.** A malformed correction must fail before it is receipted.\n"
            "**What changed.** Study mode now checks the amendment shape.\n",
        )
        unexpected = COMPLETE_STUDY_AMENDMENT.replace(
            "**Why.** A malformed correction must fail before it is receipted.",
            "**Private field.** private-amendment-value\n"
            "**Why.** A malformed correction must fail before it is receipted.",
        )
        empty = COMPLETE_STUDY_AMENDMENT.replace(
            "**Steps touched.** Step 1.", "**Steps touched.**"
        )
        for source in (duplicate, reordered, unexpected, empty):
            with self.subTest(source=source):
                self.assertIn("S008", study_codes(COMPLETE_STUDY + source))

        messages = " ".join(
            finding.message
            for finding in study_findings(COMPLETE_STUDY + unexpected)
        )
        self.assertNotIn("private-amendment-value", messages)
        self.assertNotIn("Private field", messages)

    def test_an_amendment_must_remain_final(self):
        source = (
            COMPLETE_STUDY
            + COMPLETE_STUDY_AMENDMENT
            + "\n## Appendix\n\nLater section.\n"
        )
        self.assertIn("S008", study_codes(source))

    def test_text_and_json_reports_carry_the_same_finding(self):
        path = FIXTURES / "missing-amendment-date-study.md"
        text_output = io.StringIO()
        with redirect_stdout(text_output):
            text_status = protasis.main(["--study", str(path)])
        json_output = io.StringIO()
        with redirect_stdout(json_output):
            json_status = protasis.main([
                "--study", str(path), "--format", "json",
            ])
        payload = json.loads(json_output.getvalue())
        self.assertEqual((text_status, json_status), (1, 1))
        self.assertEqual([finding["code"] for finding in payload], ["S008"])
        self.assertIn(
            f"S008 {payload[0]['message']}",
            text_output.getvalue(),
        )

    def test_only_runbooks_require_complete_replacement_clauses(self):
        self.assertEqual(study_codes(COMPLETE_STUDY + COMPLETE_STUDY_AMENDMENT), [])
        self.assertIn("P005", codes(COMPLETE_STEP + COMPLETE_STUDY_AMENDMENT))


class StudyItems(unittest.TestCase):
    def test_a_complete_study_is_clean(self):
        self.assertEqual(study_codes(COMPLETE_STUDY), [])

    def test_each_of_the_twelve_items_is_required(self):
        for number in protasis.ITEMS:
            with self.subTest(item=number):
                found = study_codes(without_item(number))
                self.assertIn("S001", found)

    def test_the_finding_names_the_missing_item(self):
        found = study_findings(without_item(5))
        self.assertEqual(len(found), 1)
        self.assertIn("Risk register seed", found[0].message)

    def test_a_duplicate_item_earns_no_verdict(self):
        source = COMPLETE_STUDY + "\n## 10. The budget, or its absence\n\nAgain.\n"
        found = study_codes(source)
        self.assertIn("S004", found)
        self.assertNotIn("S002", found)

    def test_an_item_heading_inside_a_fence_is_not_an_item(self):
        source = without_item(12) + "\n```markdown\n## 12. Decisions and their homes\n```\n"
        self.assertEqual(study_codes(source), ["S001"])


class StudyAnswers(unittest.TestCase):
    def test_an_empty_answer_is_a_finding(self):
        for number in protasis.ANSWERED:
            with self.subTest(item=number):
                self.assertIn("S002", study_codes(with_answer(number, "")))

    def test_a_bare_none_is_a_finding(self):
        for answer in ("None.", "none", "N/A.", "TBD", "No."):
            with self.subTest(answer=answer):
                self.assertIn("S002", study_codes(with_answer(9, answer)))

    def test_a_stated_none_with_its_reason_passes(self):
        source = with_answer(9, "None, and here is why: the diff is markdown.")
        self.assertEqual(study_codes(source), [])

    def test_content_passes(self):
        source = with_answer(11, "A failing suite stops the step; the guard is a test.")
        self.assertEqual(study_codes(source), [])

    def test_a_comment_is_not_content(self):
        source = with_answer(8, "<!-- filled in later -->")
        self.assertIn("S002", study_codes(source))

    def test_the_first_seven_are_presence_only(self):
        source = with_answer(3, "")
        self.assertEqual(study_codes(source), [])

    def test_an_allow_comment_suppresses_the_answer_check(self):
        source = with_answer(10, "").replace(
            "## 10. The budget, or its absence",
            "## 10. The budget, or its absence <!-- protasis: allow measured upstream -->")
        self.assertEqual(study_codes(source), [])

    def test_a_trailing_section_does_not_answer_for_the_last_item(self):
        source = with_answer(12, "") + "\n# Appendix\n\nWords that are not item 12.\n"
        self.assertIn("S002", study_codes(source))


class StudyDocuments(unittest.TestCase):
    def test_a_document_with_no_item_is_a_finding(self):
        self.assertEqual(study_codes("# Title\n\nProse only.\n"), ["S003"])

    def test_a_missing_path_is_reported_not_raised(self):
        found = protasis.check_study(Path("does-not-exist-4c1a.md"))
        self.assertEqual([f.code for f in found], ["S000"])

    def test_a_directory_is_reported_not_raised(self):
        with tempfile.TemporaryDirectory() as directory:
            found = protasis.check_study(Path(directory))
        self.assertEqual([f.code for f in found], ["S000"])

    def test_the_incomplete_fixture_names_each_fault(self):
        found = protasis.check_study(FIXTURES / "incomplete-study.md")
        self.assertEqual(sorted(f.code for f in found), ["S001", "S002", "S005"])

    def test_the_run_that_shipped_this_mode_passes_its_own_study(self):
        study = REPO / "docs" / "protasis-study-schema-check-study.md"
        self.assertEqual([f.code for f in protasis.check_study(study)], [])

    def test_study_mode_is_selected_by_flag(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = protasis.main(["--study", str(FIXTURES / "complete-study.md")])
        self.assertEqual(code, 0)
        with redirect_stdout(io.StringIO()):
            code = protasis.main(["--study", str(FIXTURES / "incomplete-study.md")])
        self.assertEqual(code, 1)

    def test_the_runbook_mode_is_unchanged_by_the_flagless_call(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = protasis.main([str(FIXTURES / "complete-runbook.md")])
        self.assertEqual(code, 0)


REGISTER_BLOCK = """```risk-register
partial-write | the release directory during a long run | a killed run leaves no half-written file
subprocess-input | the argv of the spawned tool | inputs are pinned and no shell is used
```"""


class RiskRegisterBlocks(unittest.TestCase):
    def test_a_study_whose_block_carries_every_field_is_clean(self):
        self.assertEqual(study_codes(with_answer(5, REGISTER_BLOCK)), [])

    def test_a_prose_item_5_is_a_finding(self):
        found = study_findings(with_answer(5, "Look hardest at partial writes."))
        self.assertEqual([f.code for f in found], ["S005"])
        self.assertIn("Risk register seed", found[0].message)

    def test_an_empty_block_is_a_finding(self):
        source = with_answer(5, "```risk-register\n```")
        self.assertEqual(study_codes(source), ["S005"])

    def test_a_block_with_another_info_string_is_not_a_register(self):
        source = with_answer(5, REGISTER_BLOCK.replace("risk-register", "text", 1))
        self.assertEqual(study_codes(source), ["S005"])

    def test_a_register_quoted_inside_another_fence_earns_no_verdict(self):
        """The guard for the false clean.

        A study explaining the shape quotes a register block inside a tilde
        fence, and the quoted lines must not answer for item 5: every recorded
        protasis finding is a verdict the scanner had not earned on fenced
        content.
        """
        source = with_answer(5, "~~~markdown\n" + REGISTER_BLOCK + "\n~~~")
        self.assertEqual(study_codes(source), ["S005"])

    def test_a_tilde_register_fence_is_a_register(self):
        block = REGISTER_BLOCK.replace("```risk-register", "~~~risk-register").replace("\n```", "\n~~~")
        self.assertEqual(study_codes(with_answer(5, block)), [])

    def test_a_two_field_line_is_a_finding(self):
        source = with_answer(5, "```risk-register\nshort-line | only two fields\n```")
        self.assertEqual(study_codes(source), ["S006"])

    def test_a_four_field_line_is_a_finding(self):
        source = with_answer(5, "```risk-register\na | b | c | d\n```")
        self.assertEqual(study_codes(source), ["S006"])

    def test_an_id_that_is_not_kebab_case_is_a_finding(self):
        source = with_answer(5, "```risk-register\nBad_Id | a boundary | a check\n```")
        found = study_findings(source)
        self.assertEqual([f.code for f in found], ["S007"])
        self.assertIn("kebab-case", found[0].message)

    def test_a_duplicated_id_is_a_finding_on_the_reuse(self):
        source = with_answer(5, "```risk-register\ntwice | a | b\ntwice | c | d\n```")
        found = study_findings(source)
        self.assertEqual([f.code for f in found], ["S007"])
        self.assertIn("more than once", found[0].message)

    def test_an_empty_boundary_or_check_is_a_finding(self):
        source = with_answer(5, "```risk-register\nid-one |  | a check\nid-two | a boundary |\n```")
        self.assertEqual(study_codes(source), ["S007", "S007"])

    def test_a_duplicate_item_5_earns_no_register_verdict(self):
        source = with_answer(5, "prose, no block") + "\n## 5. Risk register seed\n\nAgain.\n"
        found = study_codes(source)
        self.assertIn("S004", found)
        self.assertNotIn("S005", found)

    def test_an_allow_comment_on_item_5_suppresses_the_register_checks(self):
        source = with_answer(5, "prose, no block").replace(
            "## 5. Risk register seed",
            "## 5. Risk register seed <!-- protasis: allow predates the block shape -->")
        self.assertEqual(study_codes(source), [])

    def test_the_malformed_fixture_catches_each_missing_or_malformed_field(self):
        found = protasis.check_study(FIXTURES / "malformed-register-study.md")
        self.assertEqual(sorted(f.code for f in found),
                         ["S006", "S006", "S007", "S007", "S007", "S007"])

    def test_the_shape_run_and_this_run_pass_their_own_studies(self):
        for name in ("protasis-risk-register-block-study.md",
                     "protasis-risk-register-block-check-study.md"):
            with self.subTest(study=name):
                found = protasis.check_study(REPO / "docs" / name)
                self.assertEqual([f.code for f in found], [])
