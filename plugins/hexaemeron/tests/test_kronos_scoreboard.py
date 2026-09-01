"""The Kronos scoreboard records a ranking pass so the next one can be compared.

Kronos reranks from scratch every pass, so an axis score that moves for a job
nobody touched is invisible. These cases hold the writer to the two things that
make the record worth keeping: it refuses a pass it cannot vouch for, and the
held-job hash it writes is the one the ledger itself records.
"""

import hashlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "kronos" / "scripts" / "kronos.py"
REPO = ROOT.parents[1]

spec = importlib.util.spec_from_file_location("kronos_scoreboard", SCRIPT)
kronos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kronos)


LEDGER = """# Example evolution ledger

- Current version: `example-v0.2.0`
- Frontier status: `open`
- Frontier revision: `some-revision`
- Current frontier: A frontier sentence.
- Next Fiat job: Do the thing that is held.
"""


def canonical_digest(status, revision, frontier, job):
    line = "|".join((status, revision, frontier, job)) + "\n"
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


class ScoreboardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.scoreboard = self.root / ".kronos" / "scoreboard.jsonl"
        (self.root / "alpha").mkdir()
        (self.root / "alpha" / "EVOLUTION.md").write_text(LEDGER, encoding="utf-8")
        (self.root / "beta").mkdir()
        (self.root / "beta" / "EVOLUTION.md").write_text(
            LEDGER.replace("some-revision", "other-revision"), encoding="utf-8"
        )
        self.addCleanup(self.tmp.cleanup)

    def candidate(self, skill="alpha", **overrides):
        base = {
            "skill": skill,
            "ledger": f"{skill}/EVOLUTION.md",
            "impact": 30,
            "urgency": 20,
            "readiness": 15,
            "unblocks": 10,
            "basis": f"{skill} has a held job with evidence behind it.",
        }
        base.update(overrides)
        return base

    def document(self, candidates=None, **overrides):
        base = {
            "scope": "the checkout",
            "mode": "full",
            "candidates": candidates or [self.candidate()],
            "selected": "alpha",
        }
        base.update(overrides)
        return base

    def run_record(self, document, root=None):
        argv = ["record", "--scoreboard", str(self.scoreboard), "--root", str(root or self.root)]
        payload = document if isinstance(document, str) else json.dumps(document)
        out, err = io.StringIO(), io.StringIO()

        class Stdin:
            buffer = io.BytesIO(payload.encode("utf-8"))

        real_stdin, kronos.sys.stdin = kronos.sys.stdin, Stdin()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = kronos.main(argv)
        finally:
            kronos.sys.stdin = real_stdin
        return code, out.getvalue(), err.getvalue()

    def run_show(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = kronos.main(["show", "--scoreboard", str(self.scoreboard)])
        return code, out.getvalue()

    def lines(self):
        return self.scoreboard.read_text(encoding="utf-8").splitlines()

    # -- the clean path -------------------------------------------------

    def test_a_valid_pass_appends_exactly_one_line(self):
        code, out, _ = self.run_record(self.document())
        self.assertEqual(code, 0)
        self.assertIn("pass 1 recorded", out)
        self.assertEqual(len(self.lines()), 1)

    def test_the_written_hash_is_the_digest_the_ledger_itself_records(self):
        self.run_record(self.document())
        entry = json.loads(self.lines()[0])
        self.assertEqual(
            entry["candidates"][0]["held_job"],
            canonical_digest(
                "open", "some-revision", "A frontier sentence.", "Do the thing that is held."
            ),
        )

    def test_the_scoreboard_directory_is_created_gitignored(self):
        self.run_record(self.document())
        self.assertEqual((self.scoreboard.parent / ".gitignore").read_text(encoding="utf-8"), "*\n")

    def test_pass_numbers_increase(self):
        self.run_record(self.document())
        code, out, _ = self.run_record(self.document())
        self.assertEqual(code, 0)
        self.assertIn("pass 2 recorded", out)
        self.assertEqual([json.loads(line)["pass"] for line in self.lines()], [1, 2])

    def test_the_axis_caps_sum_to_one_hundred(self):
        self.assertEqual(sum(cap for _, cap in kronos.AXES), 100)

    # -- refusals -------------------------------------------------------

    def assertRefused(self, document, code_name, root=None):
        code, _, err = self.run_record(document, root=root)
        self.assertEqual(code, 1)
        self.assertIn(code_name, err)
        self.assertFalse(self.scoreboard.exists(), "a refusal must append nothing")

    def test_stdin_that_is_not_json_is_refused(self):
        self.assertRefused("not json at all", "K001")

    def test_an_axis_over_its_cap_is_refused(self):
        self.assertRefused(self.document([self.candidate(unblocks=16)]), "K004")

    def test_a_negative_axis_is_refused(self):
        self.assertRefused(self.document([self.candidate(impact=-1)]), "K004")

    def test_a_stated_total_that_disagrees_with_the_axes_is_refused(self):
        self.assertRefused(self.document([self.candidate(total=105)]), "K005")

    def test_a_stated_total_that_agrees_is_accepted(self):
        code, _, err = self.run_record(self.document([self.candidate(total=75)]))
        self.assertEqual(code, 0, err)

    def test_an_unknown_field_is_refused_rather_than_stored(self):
        self.assertRefused(self.document([self.candidate(note="extra")]), "K003")

    def test_a_missing_field_is_refused(self):
        candidate = self.candidate()
        del candidate["basis"]
        self.assertRefused(self.document([candidate]), "K002")

    def test_a_selection_the_tie_break_does_not_pick_is_refused(self):
        candidates = [self.candidate("alpha"), self.candidate("beta", impact=40)]
        self.assertRefused(self.document(candidates, selected="alpha"), "K006")

    def test_the_tie_break_prefers_impact_then_readiness(self):
        candidates = [
            self.candidate("alpha", impact=20, urgency=25, readiness=15, unblocks=10),
            self.candidate("beta", impact=25, urgency=20, readiness=15, unblocks=10),
        ]
        code, _, err = self.run_record(self.document(candidates, selected="beta"))
        self.assertEqual(code, 0, err)

    def test_a_ledger_outside_the_root_is_refused(self):
        outside = Path(self.tmp.name).parent / "elsewhere.md"
        self.assertRefused(
            self.document([self.candidate(ledger=str(outside))]), "K007"
        )

    def test_a_ledger_that_is_a_directory_is_refused(self):
        self.assertRefused(self.document([self.candidate(ledger="alpha")]), "K007")

    def test_a_ledger_missing_a_frontier_field_is_refused(self):
        (self.root / "alpha" / "EVOLUTION.md").write_text("# nothing here\n", encoding="utf-8")
        self.assertRefused(self.document(), "K007")

    def test_more_candidates_than_the_cap_is_refused(self):
        many = [self.candidate(f"skill-{n}") for n in range(kronos.MAX_CANDIDATES + 1)]
        self.assertRefused(self.document(many, selected="skill-0"), "K009")

    def test_two_candidates_naming_one_skill_is_refused(self):
        self.assertRefused(self.document([self.candidate(), self.candidate()]), "K002")

    def test_an_unknown_mode_is_refused(self):
        self.assertRefused(self.document(mode="whatever"), "K002")

    def test_a_truncated_final_line_is_refused_rather_than_written_past(self):
        self.run_record(self.document())
        with self.scoreboard.open("a", encoding="utf-8") as handle:
            handle.write('{"pass": 2, "candi')
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K008", err)
        self.assertEqual(len(self.lines()), 2, "the partial line stays, nothing is appended")

    def test_a_symlinked_scoreboard_directory_is_refused(self):
        """Round 1 wrote through a symlinked .kronos into an unnamed directory.

        Both the scoreboard and its `*` gitignore landed there. Where the link
        pointed somewhere git watches, that is the dirty tree the whole design
        exists to avoid.
        """
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.scoreboard.parent.symlink_to(elsewhere)
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K010", err)
        self.assertEqual(list(elsewhere.iterdir()), [], "nothing may be written through the link")

    def test_a_symlinked_scoreboard_file_is_refused(self):
        """resolve() follows the link, so the first fix never saw it."""
        elsewhere = self.root / "elsewhere.jsonl"
        self.scoreboard.parent.mkdir(parents=True)
        self.scoreboard.symlink_to(elsewhere)
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K010", err)
        self.assertFalse(elsewhere.exists(), "nothing may be written through the link")

    def test_a_scoreboard_directory_that_is_a_file_is_refused(self):
        self.scoreboard.parent.write_text("not a directory", encoding="utf-8")
        code, _, err = self.run_record(self.document())
        self.assertEqual(code, 1)
        self.assertIn("K010", err)

    def test_a_run_field_that_is_not_a_string_is_refused(self):
        self.assertRefused(self.document(run={"url": "https://example.invalid"}), "K002")

    def test_a_run_field_that_is_a_string_survives_into_the_record(self):
        url = "https://github.com/wildcat-finance/skills/pull/1"
        code, _, err = self.run_record(self.document(run=url))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(self.lines()[0])["run"], url)

    # -- reading it back ------------------------------------------------

    def test_show_marks_an_axis_that_moved_under_an_unchanged_held_job(self):
        self.run_record(self.document())
        self.run_record(self.document([self.candidate(impact=35)]))
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("drift: impact 30 -> 35, held job unchanged", out)
        self.assertIn("2 pass(es), 1 with drift", out)

    def test_show_reports_no_drift_when_the_held_job_changed_too(self):
        self.run_record(self.document())
        (self.root / "alpha" / "EVOLUTION.md").write_text(
            LEDGER.replace("Do the thing that is held.", "Do a different held thing."),
            encoding="utf-8",
        )
        self.run_record(self.document([self.candidate(impact=35)]))
        _, out = self.run_show()
        self.assertNotIn("drift:", out)
        self.assertIn("2 pass(es), 0 with drift", out)

    def test_show_on_an_absent_scoreboard_says_so_and_exits_clean(self):
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("no scoreboard at", out)

    def test_show_marks_the_selected_candidate(self):
        self.run_record(self.document([self.candidate("alpha"), self.candidate("beta", impact=40)],
                                      selected="beta"))
        _, out = self.run_show()
        selected = [line for line in out.splitlines() if line.lstrip().startswith("*")]
        self.assertEqual(len(selected), 1)
        self.assertIn("beta", selected[0])

    # -- the parked lane ------------------------------------------------

    def run_park(self, skill="alpha", ledger=None, reason="Waiting on a human approval."):
        return self.run_cli([
            "park", "--scoreboard-dir", str(self.scoreboard.parent),
            "--skill", skill, "--ledger", ledger or f"{skill}/EVOLUTION.md",
            "--reason", reason, "--root", str(self.root),
        ])

    def run_unpark(self, skill="alpha", reason="The approval landed."):
        return self.run_cli([
            "unpark", "--scoreboard-dir", str(self.scoreboard.parent),
            "--skill", skill, "--reason", reason,
        ])

    def run_parked(self):
        return self.run_cli([
            "parked", "--scoreboard-dir", str(self.scoreboard.parent),
            "--root", str(self.root),
        ])

    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = kronos.main(argv)
        return code, out.getvalue(), err.getvalue()

    def park_lines(self):
        path = self.scoreboard.parent / kronos.PARKED_NAME
        return path.read_text(encoding="utf-8").splitlines()

    def test_a_park_stores_the_reason_byte_for_byte(self):
        reason = "Halted: legal sign-off on the licence change, owner away until the 30th."
        code, out, err = self.run_park(reason=reason)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(self.park_lines()[0])["reason"], reason)
        self.assertIn("parked alpha", out)

    def test_a_reason_carrying_a_newline_stays_one_record(self):
        code, _, err = self.run_park(reason="First line.\nSecond line.")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.park_lines()), 1)
        self.assertEqual(
            json.loads(self.park_lines()[0])["reason"], "First line.\nSecond line."
        )

    def test_an_empty_reason_is_refused(self):
        code, _, err = self.run_park(reason="   ")
        self.assertEqual(code, 1)
        self.assertIn("K011", err)

    def test_an_oversized_reason_is_refused(self):
        code, _, err = self.run_park(reason="x" * (kronos.MAX_REASON_BYTES + 1))
        self.assertEqual(code, 1)
        self.assertIn("K011", err)

    def test_a_park_whose_ledger_cannot_be_read_is_refused(self):
        code, _, err = self.run_park(ledger="alpha/NOPE.md")
        self.assertEqual(code, 1)
        self.assertIn("K007", err)

    def test_parking_an_already_parked_skill_is_refused(self):
        self.run_park()
        code, _, err = self.run_park()
        self.assertEqual(code, 1)
        self.assertIn("K012", err)
        self.assertEqual(len(self.park_lines()), 1)

    def test_unparking_something_never_parked_is_refused(self):
        code, _, err = self.run_unpark()
        self.assertEqual(code, 1)
        self.assertIn("K013", err)

    def test_park_unpark_park_replays_to_one_standing_park(self):
        self.run_park()
        self.run_unpark()
        self.run_park(reason="Blocked again, same approval.")
        self.assertEqual(len(self.park_lines()), 3)
        code, out, _ = self.run_parked()
        self.assertEqual(code, kronos.STANDS)
        self.assertIn("1 park(s) standing", out)

    def test_parked_exits_clean_when_nothing_stands(self):
        code, out, _ = self.run_parked()
        self.assertEqual(code, 0)
        self.assertIn("no parks standing", out)
        self.run_park()
        self.run_unpark()
        code, out, _ = self.run_parked()
        self.assertEqual(code, 0)

    def test_parked_exits_three_while_a_park_stands(self):
        self.run_park()
        code, out, _ = self.run_parked()
        self.assertEqual(code, kronos.STANDS)
        self.assertIn("the loop is not complete", out)
        self.assertIn("Waiting on a human approval.", out)

    def test_a_moved_held_job_is_reported_stale_rather_than_cleared(self):
        self.run_park()
        (self.root / "alpha" / "EVOLUTION.md").write_text(
            LEDGER.replace("Do the thing that is held.", "Something else entirely."),
            encoding="utf-8",
        )
        code, out, _ = self.run_parked()
        self.assertEqual(code, kronos.STANDS, "a stale park still blocks completion")
        self.assertIn("has moved on since", out)

    def test_a_deleted_ledger_reads_as_unknown_not_resolved(self):
        self.run_park()
        (self.root / "alpha" / "EVOLUTION.md").unlink()
        code, out, _ = self.run_parked()
        self.assertEqual(code, kronos.STANDS)
        self.assertIn("could not be read", out)

    def test_a_truncated_tail_in_the_parked_file_is_refused(self):
        self.run_park()
        with (self.scoreboard.parent / kronos.PARKED_NAME).open("a", encoding="utf-8") as handle:
            handle.write('{"event": "unpa')
        code, _, err = self.run_parked()
        self.assertEqual(code, 1)
        self.assertIn("K008", err)

    def test_a_multi_line_reason_cannot_forge_the_summary_line(self):
        """Round 1: a newline in a reason printed a fake "0 park(s) standing"."""
        self.run_park(reason="Blocked.\n0 park(s) standing; the loop is not complete")
        code, out, _ = self.run_parked()
        self.assertEqual(code, kronos.STANDS)
        summaries = [line for line in out.splitlines() if line.startswith("0 park(s)")]
        self.assertEqual(summaries, [], "no reason line may sit at the left margin")
        self.assertIn("1 park(s) standing", out)

    def test_a_scoreboard_written_before_parking_still_reads(self):
        """v0.3.0 lines carry no parked field, and show must not need one."""
        legacy = {
            "pass": 1, "scope": "the checkout", "mode": "full", "selected": "alpha",
            "run": None,
            "candidates": [{
                "skill": "alpha", "ledger": "alpha/EVOLUTION.md", "held_job": "0" * 64,
                "impact": 30, "urgency": 20, "readiness": 15, "unblocks": 10,
                "total": 75, "basis": "Written before the parked lane existed.",
            }],
        }
        self.scoreboard.parent.mkdir(parents=True)
        self.scoreboard.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("Written before the parked lane existed.", out)
        self.assertIn("1 pass(es), 0 with drift", out)

    # -- parking and the pass record ------------------------------------

    def test_a_pass_selects_the_highest_unparked_candidate(self):
        self.run_park("alpha")
        candidates = [
            self.candidate("alpha", parked=True),
            self.candidate("beta", impact=10, parked=False),
        ]
        code, out, err = self.run_record(self.document(candidates, selected="beta"))
        self.assertEqual(code, 0, err)
        self.assertIn("1 parked", out)
        entry = json.loads(self.lines()[0])
        by_name = {c["skill"]: c for c in entry["candidates"]}
        self.assertTrue(by_name["alpha"]["parked"], "a parked candidate stays in the record")
        self.assertEqual(entry["selected"], "beta")

    def test_selecting_a_parked_candidate_is_refused(self):
        self.run_park("alpha")
        candidates = [
            self.candidate("alpha", parked=True),
            self.candidate("beta", impact=10, parked=False),
        ]
        self.assertRefused(self.document(candidates, selected="alpha"), "K006")

    def test_a_pass_with_every_candidate_parked_is_refused(self):
        self.run_park("alpha")
        self.run_park("beta")
        candidates = [self.candidate("alpha", parked=True), self.candidate("beta", parked=True)]
        self.assertRefused(self.document(candidates, selected="alpha"), "K015")

    def test_a_parked_flag_the_standing_parks_do_not_support_is_refused(self):
        self.assertRefused(self.document([self.candidate(parked=True)]), "K014")

    def test_a_standing_park_left_unflagged_is_refused(self):
        self.run_park("alpha")
        self.assertRefused(self.document([self.candidate(parked=False)]), "K014")

    def test_a_non_boolean_parked_flag_is_refused(self):
        self.assertRefused(self.document([self.candidate(parked="yes")]), "K004")

    def test_show_marks_a_parked_candidate(self):
        """Otherwise a parked candidate outscoring the selected one reads as a bug."""
        self.run_park("alpha")
        candidates = [
            self.candidate("alpha", parked=True),
            self.candidate("beta", impact=10, parked=False),
        ]
        self.run_record(self.document(candidates, selected="beta"))
        _, out = self.run_show()
        marked = [line for line in out.splitlines() if line.lstrip().startswith("P")]
        self.assertEqual(len(marked), 1)
        self.assertIn("alpha", marked[0])

    def test_rank_only_mode_says_what_it_still_records_and_reads(self):
        """It says steps 5 to 8 do not happen, and step 6 is where recording lives.

        Without naming the two exceptions a reader takes that sentence literally
        and drops both the pass record and the parked read.
        """
        skill = (ROOT / "skills" / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Rank-only mode", 1)[1].split("## Loop", 1)[0]
        self.assertIn("step 6", section, "it must say which step's recording still happens")
        self.assertIn("parked", section, "it must say to read the standing parks")
        self.assertIn("3", section, "it must say what that exit code means here")

    def test_phase_only_mode_stops_on_a_standing_park_too(self):
        """Its stop condition is restated, so the park clause has to be in it."""
        skill = (ROOT / "skills" / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Phase-only mode", 1)[1].split("## Loop", 1)[0]
        self.assertIn("park", section)

    # -- rank-only ------------------------------------------------------

    def test_a_rank_only_pass_is_recorded_with_no_run(self):
        code, out, err = self.run_record(self.document(rank_only=True))
        self.assertEqual(code, 0, err)
        self.assertIn("rank-only pass 1 recorded", out)
        entry = json.loads(self.lines()[0])
        self.assertTrue(entry["rank_only"])
        self.assertIsNone(entry["run"])

    def test_a_rank_only_pass_naming_a_run_is_refused(self):
        """The two contradict: a pass that stopped after selection launched nothing."""
        self.assertRefused(
            self.document(rank_only=True, run="https://example.invalid/1"), "K016"
        )

    def test_a_non_boolean_rank_only_is_refused(self):
        self.assertRefused(self.document(rank_only="yes"), "K004")

    def test_a_pass_with_neither_field_records_as_before(self):
        code, out, err = self.run_record(self.document())
        self.assertEqual(code, 0, err)
        self.assertIn("pass 1 recorded", out)
        self.assertNotIn("rank-only", out)
        entry = json.loads(self.lines()[0])
        self.assertFalse(entry["rank_only"])
        self.assertEqual(entry["ungoverned"], [])

    def test_an_ungoverned_list_is_stored(self):
        code, _, err = self.run_record(self.document(ungoverned=["gamma", "delta"]))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(self.lines()[0])["ungoverned"], ["gamma", "delta"])

    def test_an_ungoverned_list_over_the_cap_is_refused(self):
        many = [f"skill-{n}" for n in range(kronos.MAX_UNGOVERNED + 1)]
        self.assertRefused(self.document(ungoverned=many), "K017")

    def test_an_ungoverned_element_that_is_not_a_name_is_refused(self):
        self.assertRefused(self.document(ungoverned=["gamma", 7]), "K017")

    def test_an_empty_ungoverned_name_is_refused(self):
        self.assertRefused(self.document(ungoverned=["  "]), "K017")

    def test_an_ungoverned_field_that_is_not_a_list_is_refused(self):
        self.assertRefused(self.document(ungoverned="gamma"), "K017")

    def test_a_skill_both_scored_and_reported_ungoverned_is_refused(self):
        """Round 1 recorded protasis as scored from a ledger and as having none."""
        self.assertRefused(self.document(ungoverned=["alpha"]), "K017")

    def test_show_marks_a_rank_only_pass_and_lists_the_ungoverned(self):
        self.run_record(self.document(rank_only=True, ungoverned=["gamma"]))
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("(rank-only)", out)
        self.assertIn("ungoverned: gamma", out)

    def test_a_pass_written_before_either_field_still_reads(self):
        """v0.4.0 lines carry neither field, and show must not need them."""
        legacy = {
            "pass": 1, "scope": "the checkout", "mode": "full", "selected": "alpha",
            "run": None,
            "candidates": [{
                "skill": "alpha", "ledger": "alpha/EVOLUTION.md", "held_job": "0" * 64,
                "impact": 30, "urgency": 20, "readiness": 15, "unblocks": 10,
                "total": 75, "parked": False, "basis": "Written before rank-only existed.",
            }],
        }
        self.scoreboard.parent.mkdir(parents=True)
        self.scoreboard.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
        code, out = self.run_show()
        self.assertEqual(code, 0)
        self.assertIn("Written before rank-only existed.", out)
        self.assertIn("no run recorded", out)
        self.assertNotIn("ungoverned:", out)

    # -- the skill and the script agree ---------------------------------

    def test_every_field_the_script_accepts_is_named_in_the_skill(self):
        """Round 1 documented a refusal for `total` without documenting the field.

        A caller reading only SKILL.md could be refused over something it never
        told them they could send, and the two drift apart silently otherwise.
        """
        skill = (ROOT / "skills" / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        section = skill.split("## Scoreboard", 1)[1].split("## Hard rules", 1)[0]
        for name in sorted(kronos.PASS_FIELDS | kronos.CANDIDATE_FIELDS):
            with self.subTest(field=name):
                self.assertIn(f"`{name}`", section)

    def test_the_pass_is_recorded_once_the_fiat_run_is_named(self):
        """The run link is half the record, and it does not exist at selection."""
        skill = (ROOT / "skills" / "kronos" / "SKILL.md").read_text(encoding="utf-8")
        loop = skill.split("## Loop", 1)[1].split("## Scoreboard", 1)[0]
        step_four = loop.split("4. ", 1)[1].split("5. ", 1)[0]
        step_six = loop.split("6. ", 1)[1].split("7. ", 1)[0]
        self.assertNotIn("record the pass", step_four)
        self.assertIn("record the pass", step_six)

    # -- against the real ledgers ---------------------------------------

    def test_the_hash_matches_a_real_governed_ledger_history_row(self):
        ledger = REPO / "plugins" / "hexaemeron" / "skills" / "kronos" / "EVOLUTION.md"
        computed = kronos.held_job_hash(ledger)
        self.assertIn(f"`{computed}`", ledger.read_text(encoding="utf-8"))

    def test_record_park_and_parked_start_no_subprocess(self):
        def boom(*_args, **_kwargs):
            raise AssertionError("ranking verbs start no subprocess")

        original_popen = kronos.subprocess.Popen
        original_run = kronos.subprocess.run
        kronos.subprocess.Popen = boom
        kronos.subprocess.run = boom
        try:
            code, _, err = self.run_record(self.document())
            self.assertEqual(code, 0, err)
            code, _, err = self.run_park()
            self.assertEqual(code, 0, err)
            code, _, err = self.run_parked()
            self.assertEqual(code, kronos.STANDS, err)
        finally:
            kronos.subprocess.Popen = original_popen
            kronos.subprocess.run = original_run


class DurableHomeTest(unittest.TestCase):
    """pull and push against a local bare remote, never the network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.bare = self.home / "remote.git"
        self.git(None, "init", "--bare", str(self.bare))
        self.addCleanup(self.tmp.cleanup)

    def git(self, cwd, *args):
        result = subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout

    def make_scope(self, name, remotes=None):
        path = self.home / name
        path.mkdir()
        (path / "alpha").mkdir()
        (path / "alpha" / "EVOLUTION.md").write_text(LEDGER, encoding="utf-8")
        (path / "beta").mkdir()
        (path / "beta" / "EVOLUTION.md").write_text(
            LEDGER.replace("some-revision", "other-revision"), encoding="utf-8"
        )
        self.git(path, "init")
        self.git(path, "config", "--local", "commit.gpgsign", "false")
        self.git(path, "config", "user.name", "Kronos Test")
        self.git(path, "config", "user.email", "kronos@test.invalid")
        self.git(path, "add", "alpha", "beta")
        self.git(path, "commit", "-m", "init")
        for remote_name, url in (remotes or (("origin", self.bare),)):
            self.git(path, "remote", "add", remote_name, str(url))
        return path

    def runner(self, scope):
        helper = ScoreboardTest()
        helper.scoreboard = scope / ".kronos" / "scoreboard.jsonl"
        helper.root = scope
        helper.tmp = self.tmp
        return helper

    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = kronos.main(argv)
        return code, out.getvalue(), err.getvalue()

    def pull(self, scope, remote=None):
        argv = ["pull", "--root", str(scope)]
        if remote is not None:
            argv.extend(["--remote", remote])
        return self.run_cli(argv)

    def push(self, scope, remote=None):
        argv = ["push", "--root", str(scope)]
        if remote is not None:
            argv.extend(["--remote", remote])
        return self.run_cli(argv)

    def status(self, scope):
        return self.git(scope, "status", "--short")

    def test_pull_of_a_missing_ref_leaves_both_jsonl_files_absent(self):
        scope = self.make_scope("a")
        (scope / ".kronos").mkdir()
        (scope / ".kronos" / "scoreboard.jsonl").write_text("{}\n", encoding="utf-8")
        (scope / ".kronos" / "parked.jsonl").write_text("{}\n", encoding="utf-8")
        code, out, err = self.pull(scope)
        self.assertEqual(code, 0, err)
        self.assertIn("empty start", out)
        self.assertFalse((scope / ".kronos" / "scoreboard.jsonl").exists())
        self.assertFalse((scope / ".kronos" / "parked.jsonl").exists())

    def test_park_and_record_on_one_tree_are_visible_on_a_fresh_tree(self):
        tree_a = self.make_scope("a")
        tree_b = self.make_scope("b")
        helper = self.runner(tree_a)
        code, _, err = helper.run_record(helper.document())
        self.assertEqual(code, 0, err)
        code, _, err = helper.run_park(reason="Waiting on a person.")
        self.assertEqual(code, 0, err)
        parked = json.loads((tree_a / ".kronos" / "parked.jsonl").read_text(encoding="utf-8"))
        code, _, err = self.push(tree_a)
        self.assertEqual(code, 0, err)
        code, _, err = self.pull(tree_b)
        self.assertEqual(code, 0, err)
        helper_b = self.runner(tree_b)
        code, out, err = helper_b.run_parked()
        self.assertEqual(code, kronos.STANDS, err)
        self.assertIn(parked["held_job"][:12], out)
        self.assertIn("Waiting on a person.", out)
        self.assertEqual(
            json.loads((tree_b / ".kronos" / "parked.jsonl").read_text(encoding="utf-8"))["reason"],
            "Waiting on a person.",
        )
        code, shown = helper_b.run_show()
        self.assertEqual(code, 0)
        self.assertIn("pass 1", shown)
        self.assertIn("alpha", shown)

    def test_show_on_the_second_tree_prints_drift_against_a_later_pass(self):
        tree_a = self.make_scope("a")
        tree_b = self.make_scope("b")
        helper = self.runner(tree_a)
        helper.run_record(helper.document())
        self.push(tree_a)
        self.pull(tree_b)
        helper.run_record(helper.document([helper.candidate(impact=35)]))
        self.push(tree_a)
        self.pull(tree_b)
        code, out = self.runner(tree_b).run_show()
        self.assertEqual(code, 0)
        self.assertIn("drift: impact 30 -> 35, held job unchanged", out)

    def test_extra_blobs_in_the_state_ref_are_ignored(self):
        tree_a = self.make_scope("a")
        helper = self.runner(tree_a)
        helper.run_record(helper.document())
        self.push(tree_a)
        edit = self.home / "edit"
        self.git(None, "clone", "--branch", "kronos/state", str(self.bare), str(edit))
        self.git(edit, "config", "--local", "commit.gpgsign", "false")
        self.git(edit, "config", "user.name", "Kronos Test")
        self.git(edit, "config", "user.email", "kronos@test.invalid")
        (edit / "README").write_text("not a kronos file\n", encoding="utf-8")
        self.git(edit, "add", "README")
        self.git(edit, "commit", "-m", "extra blob")
        self.git(edit, "push", "origin", "HEAD:refs/heads/kronos/state")
        tree_b = self.make_scope("b")
        code, _, err = self.pull(tree_b)
        self.assertEqual(code, 0, err)
        names = {path.name for path in (tree_b / ".kronos").iterdir()}
        self.assertNotIn("README", names)
        self.assertTrue((tree_b / ".kronos" / "scoreboard.jsonl").is_file())

    def test_a_failed_read_of_an_existing_ref_does_not_clear_a_park(self):
        tree_a = self.make_scope("a")
        helper = self.runner(tree_a)
        helper.run_park()
        parked = (tree_a / ".kronos" / "parked.jsonl").read_bytes()
        broken = self.home / "not-a-git"
        broken.mkdir()
        self.git(tree_a, "remote", "add", "broken", str(broken))
        code, _, err = self.pull(tree_a, remote="broken")
        self.assertEqual(code, 1)
        self.assertIn("K018", err)
        self.assertNotIn("fatal", err)
        self.assertEqual((tree_a / ".kronos" / "parked.jsonl").read_bytes(), parked)

    def test_a_symlink_at_the_kronos_directory_is_refused_on_pull_and_push(self):
        tree_a = self.make_scope("a")
        elsewhere = tree_a / "elsewhere"
        elsewhere.mkdir()
        (tree_a / ".kronos").symlink_to(elsewhere)
        code, _, err = self.pull(tree_a)
        self.assertEqual(code, 1)
        self.assertIn("K010", err)
        self.assertEqual(list(elsewhere.iterdir()), [])
        code, _, err = self.push(tree_a)
        self.assertEqual(code, 1)
        self.assertIn("K010", err)

    def test_a_symlink_at_a_jsonl_file_is_refused_on_pull_and_push(self):
        tree_a = self.make_scope("a")
        holder = tree_a / ".kronos"
        holder.mkdir()
        target = tree_a / "elsewhere.jsonl"
        (holder / "scoreboard.jsonl").symlink_to(target)
        code, _, err = self.pull(tree_a)
        self.assertEqual(code, 1)
        self.assertIn("K010", err)
        self.assertFalse(target.exists())
        code, _, err = self.push(tree_a)
        self.assertEqual(code, 1)
        self.assertIn("K010", err)

    def test_a_url_remote_and_an_unknown_name_are_refused(self):
        tree_a = self.make_scope("a")

        def boom(*_args, **_kwargs):
            raise AssertionError("a URL remote must be refused before git starts")

        original = kronos.subprocess.Popen
        kronos.subprocess.Popen = boom
        try:
            code, _, err = self.pull(tree_a, remote="https://example.invalid/skills.git")
        finally:
            kronos.subprocess.Popen = original
        self.assertEqual(code, 1)
        self.assertIn("K020", err)
        code, _, err = self.pull(tree_a, remote="not-a-remote")
        self.assertEqual(code, 1)
        self.assertIn("K020", err)

    def test_kronos_state_remote_is_used_when_remote_is_absent(self):
        other = self.home / "other.git"
        self.git(None, "init", "--bare", str(other))
        tree_a = self.make_scope("a", remotes=(("origin", other), ("special", self.bare)))
        helper = self.runner(tree_a)
        helper.run_record(helper.document())
        code, _, err = self.push(tree_a, remote="special")
        self.assertEqual(code, 0, err)
        tree_b = self.make_scope("b", remotes=(("origin", other), ("special", self.bare)))
        with patch.dict(os.environ, {kronos.REMOTE_ENV: "special"}):
            code, _, err = self.pull(tree_b)
        self.assertEqual(code, 0, err)
        self.assertTrue((tree_b / ".kronos" / "scoreboard.jsonl").is_file())

    def test_a_non_fast_forward_push_leaves_local_files_untouched(self):
        tree_a = self.make_scope("a")
        tree_b = self.make_scope("b")
        helper_a = self.runner(tree_a)
        helper_a.run_record(helper_a.document())
        before = (tree_a / ".kronos" / "scoreboard.jsonl").read_bytes()
        self.push(tree_a)
        helper_b = self.runner(tree_b)
        self.pull(tree_b)
        helper_b.run_record(helper_b.document([helper_b.candidate(impact=35)]))
        self.push(tree_b)
        code, _, err = self.push(tree_a)
        self.assertEqual(code, 1)
        self.assertIn("K019", err)
        self.assertNotIn("fatal", err)
        self.assertEqual((tree_a / ".kronos" / "scoreboard.jsonl").read_bytes(), before)

    def test_git_status_is_empty_after_pull_record_park_and_push(self):
        tree_a = self.make_scope("a")
        self.assertEqual(self.status(tree_a), "")
        helper = self.runner(tree_a)
        self.pull(tree_a)
        self.assertEqual(self.status(tree_a), "")
        helper.run_record(helper.document())
        self.assertEqual(self.status(tree_a), "")
        helper.run_park()
        self.assertEqual(self.status(tree_a), "")
        self.push(tree_a)
        self.assertEqual(self.status(tree_a), "")

    def test_a_failed_replace_does_not_leave_a_truncated_scoreboard(self):
        tree_a = self.make_scope("a")
        tree_b = self.make_scope("b")
        helper = self.runner(tree_a)
        helper.run_record(helper.document())
        self.push(tree_a)
        self.pull(tree_b)
        previous = (tree_b / ".kronos" / "scoreboard.jsonl").read_bytes()
        helper.run_record(helper.document())
        self.push(tree_a)

        def boom(_src, _dst):
            raise OSError("simulated kill")

        with patch.object(kronos.os, "replace", side_effect=boom):
            code, _, err = self.pull(tree_b)
        self.assertEqual(code, 1)
        self.assertIn("K000", err)
        self.assertEqual((tree_b / ".kronos" / "scoreboard.jsonl").read_bytes(), previous)
        code, _, err = self.runner(tree_b).run_record(self.runner(tree_b).document())
        self.assertEqual(code, 0, err)

    def test_a_missing_final_newline_still_refuses_with_k008(self):
        tree_a = self.make_scope("a")
        helper = self.runner(tree_a)
        helper.run_record(helper.document())
        path = tree_a / ".kronos" / "scoreboard.jsonl"
        path.write_text(path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8")
        code, _, err = helper.run_record(helper.document())
        self.assertEqual(code, 1)
        self.assertIn("K008", err)

    def test_default_remote_prefers_upstream_over_origin(self):
        empty = self.home / "empty.git"
        self.git(None, "init", "--bare", str(empty))
        tree_a = self.make_scope("a", remotes=(("origin", self.bare), ("upstream", empty)))
        helper = self.runner(tree_a)
        helper.run_record(helper.document())
        self.push(tree_a, remote="origin")
        tree_b = self.make_scope("b", remotes=(("origin", self.bare), ("upstream", empty)))
        code, out, err = self.pull(tree_b)
        self.assertEqual(code, 0, err)
        self.assertIn("empty start", out)
        self.assertFalse((tree_b / ".kronos" / "scoreboard.jsonl").exists())

    def test_git_that_cannot_start_is_k021(self):
        tree_a = self.make_scope("a")

        def boom(*_args, **_kwargs):
            raise FileNotFoundError("git")

        with patch.object(kronos.subprocess, "Popen", side_effect=boom):
            code, _, err = self.pull(tree_a)
        self.assertEqual(code, 1)
        self.assertIn("K021", err)


DEMO_FRONTIER = {
    "status": "open",
    "revision": "a-preserved-source",
    "current": "The registered offline path runs over checked-in inputs.",
    "next": "Run the same path over one preserved real-world source.",
}


def demonstration_ledger(skill, frontier=None):
    """Return one DEMONSTRATION.md whose fenced record carries a demo frontier."""
    frontier = dict(frontier or DEMO_FRONTIER)
    frontier.setdefault(
        "sha256",
        canonical_digest(
            frontier["status"], frontier["revision"], frontier["current"], frontier["next"]
        ),
    )
    frontier.setdefault("version", f"{skill}-demo-v0.1.0")
    record = {
        "schema": "shoggoth-demonstration/v1",
        "skill": skill,
        "plugin": skill,
        "status": "constructed",
        "claim_id": f"{skill}-example",
        "claim": "The registered path exits zero over checked-in inputs.",
        "non_claim": "It establishes nothing about real-world data.",
        "network": {"policy": "denied"},
        "timeout_seconds": 300,
        "sources": [],
        "commands": [],
        "observations": [],
        "frontier": frontier,
    }
    return (
        f"# {skill} demonstration ledger\n\n"
        "```shoggoth-demonstration\n" + json.dumps(record, indent=2) + "\n```\n"
    )


class DemoLaneTest(ScoreboardTest):
    """The demo lane reads DEMONSTRATION.md, ranks, and dispatches nothing."""

    def setUp(self):
        super().setUp()
        (self.root / "alpha" / "DEMONSTRATION.md").write_text(
            demonstration_ledger("alpha"), encoding="utf-8"
        )
        (self.root / "beta" / "DEMONSTRATION.md").write_text(
            demonstration_ledger("beta"), encoding="utf-8"
        )

    def demo_document(self, **overrides):
        base = self.document(
            candidates=[self.candidate(ledger="alpha/DEMONSTRATION.md")],
            mode="demo",
            rank_only=True,
        )
        base.update(overrides)
        return base

    def test_a_demo_pass_over_demonstration_ledgers_records(self):
        code, out, err = self.run_record(self.demo_document())
        self.assertEqual(code, 0, err)
        self.assertIn("rank-only pass 1 recorded", out)
        entry = json.loads(self.lines()[0])
        self.assertEqual(entry["mode"], "demo")
        self.assertEqual(entry["candidates"][0]["ledger"], "alpha/DEMONSTRATION.md")

    def test_the_demo_hash_is_the_demo_frontier_digest(self):
        self.run_record(self.demo_document())
        entry = json.loads(self.lines()[0])
        self.assertEqual(
            entry["candidates"][0]["held_job"],
            canonical_digest(
                DEMO_FRONTIER["status"],
                DEMO_FRONTIER["revision"],
                DEMO_FRONTIER["current"],
                DEMO_FRONTIER["next"],
            ),
        )

    def test_the_demo_lane_refuses_an_evolution_ledger(self):
        code, _, err = self.run_record(
            self.demo_document(candidates=[self.candidate(ledger="alpha/EVOLUTION.md")])
        )
        self.assertEqual(code, 1)
        self.assertIn("K023", err)
        self.assertIn("DEMONSTRATION.md", err)

    def test_the_default_lane_refuses_a_demonstration_ledger(self):
        code, _, err = self.run_record(
            self.document(candidates=[self.candidate(ledger="alpha/DEMONSTRATION.md")])
        )
        self.assertEqual(code, 1)
        self.assertIn("K023", err)
        self.assertIn("EVOLUTION.md", err)

    def test_the_phase_only_lane_refuses_a_demonstration_ledger(self):
        code, _, err = self.run_record(
            self.document(
                candidates=[self.candidate(ledger="alpha/DEMONSTRATION.md")], mode="phase-only"
            )
        )
        self.assertEqual(code, 1)
        self.assertIn("K023", err)

    def test_a_demo_pass_that_names_a_run_is_refused(self):
        code, _, err = self.run_record(self.demo_document(rank_only=False, run="fiat/whatever"))
        self.assertEqual(code, 1)
        self.assertIn("K024", err)
        self.assertIn("dispatches nothing", err)

    def test_a_rank_only_demo_pass_that_names_a_run_keeps_the_older_refusal(self):
        code, _, err = self.run_record(self.demo_document(run="fiat/whatever"))
        self.assertEqual(code, 1)
        self.assertIn("K016", err)

    def test_a_demo_pass_that_is_not_rank_only_is_refused(self):
        code, _, err = self.run_record(self.demo_document(rank_only=False))
        self.assertEqual(code, 1)
        self.assertIn("K024", err)

    def test_a_tampered_demo_frontier_digest_is_refused(self):
        (self.root / "alpha" / "DEMONSTRATION.md").write_text(
            demonstration_ledger("alpha", dict(DEMO_FRONTIER, sha256="f" * 64)), encoding="utf-8"
        )
        code, _, err = self.run_record(self.demo_document())
        self.assertEqual(code, 1)
        self.assertIn("K022", err)

    def test_a_ledger_without_a_record_fence_is_refused(self):
        (self.root / "alpha" / "DEMONSTRATION.md").write_text("# nothing\n", encoding="utf-8")
        code, _, err = self.run_record(self.demo_document())
        self.assertEqual(code, 1)
        self.assertIn("K022", err)

    def test_a_demo_pass_writes_only_the_scoreboard_line(self):
        before = sorted(path.name for path in self.root.iterdir())
        self.run_record(self.demo_document())
        after = sorted(path.name for path in self.root.iterdir())
        self.assertEqual(sorted(before + [".kronos"]), after)
        self.assertEqual(len(self.lines()), 1)
        self.assertEqual(
            (self.root / "alpha" / "DEMONSTRATION.md").read_text(encoding="utf-8"),
            demonstration_ledger("alpha"),
        )
        self.assertEqual((self.root / "alpha" / "EVOLUTION.md").read_text(encoding="utf-8"), LEDGER)


if __name__ == "__main__":
    unittest.main()
