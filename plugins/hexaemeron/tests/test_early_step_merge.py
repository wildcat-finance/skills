"""A step whose pull request merged before integrate can still be receipted.

Issue 1021 recorded a run that dead-ended: both stacked pull requests were
merged into their bases minutes after they opened, and `done push` refused with
nothing to go to afterwards.  Recovery took a maintainer force-pushing a
published ref back to a head the run had already receipted.

The gate was right to notice the merge and wrong to have no exit.  The evidence
it protects survives an early merge: each head was still the exact head of its
pull request when it merged.  So adoption is admitted on two hard checks and
refused otherwise, and the four outcomes are kept apart here: a merge still in
its base is adopted, a head that moved refuses, a merge that left its base
refuses as a rewrite, and a graph query that gave no answer refuses as unknown
rather than as a claim about anybody.

The graph cases use real Git objects.  The receipt cases use the established
delivery harness, so the recorded `early_merge` block is inspected as the
controller actually writes it.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEXCTL = HERE.parent / "skills" / "fiat" / "scripts" / "hexctl.py"

# ``run_tests.py`` discovers from this directory and already exposes the
# harness.  Direct execution needs the same explicit import path.
sys.path.insert(0, str(HERE))
from test_hexctl import HexctlCase, LINTS_CLEAN, SUITE  # noqa: E402


def hexctl_module():
    spec = importlib.util.spec_from_file_location("hexctl_early_step_merge", HEXCTL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AncestryAnswerCase(unittest.TestCase):
    """One real `base -> merge` graph plus a commit from unrelated history."""

    def setUp(self):
        self.hexctl = hexctl_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self._git("init", "-q", "-b", "main")
        self._git("config", "commit.gpgsign", "false")
        self._git("config", "user.name", "Fixture")
        self._git("config", "user.email", "fixture@example.invalid")

        (self.repo / "history.txt").write_text("base\n", encoding="utf-8")
        self._git("add", "history.txt")
        self._git("commit", "-q", "-m", "base")
        self.merge = self._git("rev-parse", "HEAD").stdout.strip()

        (self.repo / "history.txt").write_text("base\ntip\n", encoding="utf-8")
        self._git("commit", "-q", "-am", "tip")
        self.tip = self._git("rev-parse", "HEAD").stdout.strip()

        self.absent = hashlib.sha1(b"never-written").hexdigest()

    def _git(self, *args, input_text=None):
        return subprocess.run(
            ["git", *args], cwd=self.repo, capture_output=True, text=True,
            check=True, input=input_text,
        )

    def test_a_merge_still_in_its_base_answers_yes(self):
        self.assertIs(
            self.hexctl._ancestry_answer(str(self.repo), self.merge, self.tip), True
        )

    def test_a_commit_outside_the_base_answers_no(self):
        self.assertIs(
            self.hexctl._ancestry_answer(str(self.repo), self.tip, self.merge), False
        )

    def test_a_missing_object_answers_unknown_rather_than_no(self):
        """The distinction the refusal rests on: unknown is not a denial."""
        self.assertIsNone(
            self.hexctl._ancestry_answer(str(self.repo), self.absent, self.tip)
        )

    def test_unknown_and_no_are_different_answers_for_the_same_pair(self):
        answered = self.hexctl._ancestry_answer(str(self.repo), self.tip, self.merge)
        unknown = self.hexctl._ancestry_answer(str(self.repo), self.absent, self.merge)
        self.assertIs(answered, False)
        self.assertIsNone(unknown)


class EarlyMergeAdoptionCase(HexctlCase):
    """The receipt an adopted early merge leaves, and the three refusals."""

    URL_TEMPLATE = "https://github.com/wildcat-finance/example/pull/{}"

    def setUp(self):
        super().setUp()
        # On a successful `done push` the harness re-synthesises the pull
        # request from `--merge-commit` alone, because a step push is supposed
        # to leave one open. Adoption is exactly the case that contradicts
        # that, so the fixture factory carries the merge instead of the
        # argument, which `done push` refuses for a stacked step.
        self.adopted_merge = None

    def fake_pr(self, url, head, base, head_sha, merge_sha=None, *, body=None):
        if self.adopted_merge is not None and merge_sha is None:
            merge_sha = self.adopted_merge
        return HexctlCase.fake_pr(url, head, base, head_sha, merge_sha, body=body)

    def digests(self):
        """State and ledger bytes, so a refusal can be proved inert."""
        root = Path(self.target) / ".hexaemeron"
        out = {}
        for name in ("state.json", "ledger.jsonl"):
            path = root / name
            out[name] = (
                hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            )
        return out

    def _to_push(self, number=1):
        """Drive one step to the boundary where `done push` is the directive."""
        self.to_steps(("Scaffold", "Core"))
        self.run_ctl(
            "done", "implement",
            "--branch", self.step_branch(number),
            "--commit", f"abc{number}",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1",
            "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate",
        )

    def _pull_request(self, number, *, merge_sha=None, head_sha=None):
        state = self.state()
        branch = self.step_branch(number, state)
        head = head_sha or (format(number, "x") * 40)
        url = self.URL_TEMPLATE.format(number)
        self.fake_refs[branch] = head
        self.fake_prs[url] = self.fake_pr(
            url, branch, self.step_base(number, state), head, merge_sha
        )
        return url, head, branch

    def _push(self, number, url, head, *, expect=0):
        state = self.state()
        return self.run_ctl(
            "done", "push",
            "--pr-url", url,
            "--head-commit", head,
            "--pr-base", self.step_base(number, state),
            expect=expect,
        )

    def test_an_early_merged_step_is_adopted_and_recorded_explicitly(self):
        self._to_push(1)
        merge = "e" * 40
        self.adopted_merge = merge
        url, head, _branch = self._pull_request(1, merge_sha=merge)
        self._push(1, url, head)

        receipt = self.state()["steps"][0]["receipts"]["push"]
        early = receipt["early_merge"]
        self.assertEqual(early["merge_commit"], merge)
        self.assertEqual(early["reachable_from"], receipt["pr_base"])
        self.assertEqual(early["github_verified"], [merge])
        self.assertRegex(early["base_tip"], r"^[0-9a-f]{40}$")

    def test_an_open_pull_request_records_no_early_merge(self):
        self._to_push(1)
        url, head, _branch = self._pull_request(1)
        self._push(1, url, head)
        receipt = self.state()["steps"][0]["receipts"]["push"]
        self.assertIsNone(receipt["early_merge"])
        self.assertIsNone(receipt["merge_commit"])

    def test_a_head_that_moved_still_refuses_when_the_pull_request_merged(self):
        """The rewrite case the original refusal existed for."""
        self._to_push(1)
        url, head, branch = self._pull_request(1, merge_sha="e" * 40)
        self.fake_prs[url]["head"]["sha"] = "9" * 40
        result = self._push(1, url, head, expect=2)
        self.assertIn("head", result.stderr)
        self.assertNotIn("early_merge", result.stderr)

    def test_a_merge_that_left_its_base_refuses_as_a_rewritten_ref(self):
        self._to_push(1)
        merge = "e" * 40
        url, head, _branch = self._pull_request(1, merge_sha=merge)
        self.env["FAKE_GIT_MODE"] = "not-ancestor"
        self.env["FAKE_GIT_NOT_ANCESTOR"] = merge
        try:
            result = self._push(1, url, head, expect=2)
        finally:
            self.env.pop("FAKE_GIT_MODE", None)
            self.env.pop("FAKE_GIT_NOT_ANCESTOR", None)
        self.assertIn("not reachable from the recorded base", result.stderr)
        self.assertIn("rewritten ref", result.stderr)

    def test_an_unanswered_graph_query_refuses_rather_than_denying(self):
        """The unknown branch, asserted where it can be observed.

        Driving it end to end is not available here: the fixture's only way to
        silence `merge-base` is a mode that also silences the range check
        running before it, so the run would refuse for the wrong reason. The
        unit case above proves the answer is `None` rather than `False`, and
        this proves the branch that consumes it refuses about reachability
        instead of asserting a rewrite.
        """
        source = HEXCTL.read_text(encoding="utf-8")
        self.assertIn(
            'f"reachability of adopted merge {merge_sha} in \'{base_ref}\' could "\n'
            '            "not be determined"',
            source,
        )

    def test_a_refused_adoption_leaves_state_and_ledger_byte_identical(self):
        self._to_push(1)
        merge = "e" * 40
        url, head, _branch = self._pull_request(1, merge_sha=merge)
        before = self.digests()
        self.env["FAKE_GIT_MODE"] = "not-ancestor"
        self.env["FAKE_GIT_NOT_ANCESTOR"] = merge
        try:
            self._push(1, url, head, expect=2)
        finally:
            self.env.pop("FAKE_GIT_MODE", None)
            self.env.pop("FAKE_GIT_NOT_ANCESTOR", None)
        self.assertEqual(self.digests(), before)

    def test_the_adopted_merge_is_github_verified_like_any_other_commit(self):
        self._to_push(1)
        merge = "e" * 40
        self.adopted_merge = merge
        url, head, _branch = self._pull_request(1, merge_sha=merge)
        self.env["FAKE_GH_MODE"] = "verified-false"
        try:
            result = self._push(1, url, head, expect=2)
        finally:
            self.env.pop("FAKE_GH_MODE", None)
        self.assertIn("verified", result.stderr)


class AdoptionSwitchCase(unittest.TestCase):
    """Adoption is offered explicitly; absent the switch nothing changes."""

    def setUp(self):
        self.hexctl = hexctl_module()

    def test_the_original_refusal_is_unchanged_without_the_switch(self):
        source = HEXCTL.read_text(encoding="utf-8")
        self.assertIn(
            'if not adopt_early_merge:\n'
            '            die("step pull request was already merged before integrate")',
            source,
        )

    def test_adoption_requires_a_full_merge_sha(self):
        source = HEXCTL.read_text(encoding="utf-8")
        self.assertIn(
            'die("early-merged pull request did not return a full merge SHA")', source
        )

    def test_only_a_stacked_step_is_offered_adoption(self):
        source = HEXCTL.read_text(encoding="utf-8")
        self.assertIn("adopt_early_merge=stacked,", source)


def run_elenchus_report(argv):
    """Run this focused module and write through the suite's secure reporter."""
    if len(argv) != 2 or argv[0] != "--elenchus-report":
        raise SystemExit(
            "test_early_step_merge.py accepts exactly one --elenchus-report PATH"
        )

    from run_tests import parse_arguments, result_payload, write_report

    _arguments, target = parse_arguments(argv)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print("test_early_step_merge.py: report write failed", file=sys.stderr)
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--elenchus-report" in arguments:
        raise SystemExit(run_elenchus_report(arguments))
    unittest.main()
