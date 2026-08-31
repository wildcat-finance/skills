"""A push receipt names a commit, not a string.

`--head-commit` accepts any ref git resolves, including an abbreviated SHA, and
`done push` resolves it to validate it against the branch tip. It then has to
store the resolved identity, because the merge-order check at integration
compares that stored value against a full 40-character tip.

Storing what was typed instead let a short SHA read as a rewritten branch five
steps later, with no way back: `done push` refuses once the run has left the
steps phase, and the ledger is append-only. That is skills#329, where the run
halted with six steps built, audited, pushed and green, and the stack had to be
landed by hand.

These live outside `test_hexctl.py` because that file sits 144 bytes under the
bounded-read limit the Promise Machine contract enforces on it.
"""

import importlib.util
import os
import unittest
from contextlib import redirect_stderr
from io import StringIO
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
HEXCTL = os.path.join(HERE, "..", "skills", "fiat", "scripts", "hexctl.py")


def hexctl_module():
    spec = importlib.util.spec_from_file_location("hexctl_push_identity", HEXCTL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordedPushHeadIsResolved(unittest.TestCase):
    """What `done push` writes into the receipt."""

    def test_the_receipt_stores_the_resolved_identity_not_the_argument(self):
        """The line that caused #329. `supplied_head` is the resolved value the
        command already computed to validate the argument; storing
        `args.head_commit` beside it throws that resolution away."""
        with open(HEXCTL, encoding="utf-8") as handle:
            source = handle.read()
        marker = source.index('step["receipts"]["push"] = {')
        record = source[marker : marker + 600]
        self.assertIn(
            '"head_commit": supplied_head,',
            record,
            "the push receipt must store the resolved commit, not the raw argument",
        )
        self.assertNotIn(
            '"head_commit": args.head_commit,',
            record,
            "storing the argument lets an abbreviated SHA reach the merge-order check",
        )


class AbbreviatedReceiptsStillIntegrate(unittest.TestCase):
    """What the merge-order check does with receipts already written short."""

    def setUp(self):
        self.hexctl = hexctl_module()

    def _state(self):
        return {
            "integrate": {"merged": [1]},
            "steps": [
                {"n": 1, "title": "one",
                 "receipts": {"push": {"head_commit": "a" * 40}}},
                {"n": 2, "title": "two",
                 "receipts": {"push": {"head_commit": "b" * 40}}},
                {"n": 3, "title": "three",
                 "receipts": {"push": {"head_commit": "c" * 40}}},
            ],
        }

    def _refusal(self, state, current_step, tips, resolves=None, relations=None):
        """The stderr the check dies with, or None when it returns."""
        module = self.hexctl
        resolves = resolves or {}
        relations = relations or {}

        def tip(_dir, branch, label="remote run branch tip"):
            return tips[branch]

        def resolve(_dir, ref, label):
            """Stand in for native `git rev-parse --verify <ref>^{commit}`."""
            if ref in resolves:
                return resolves[ref]
            module.die(f"{label} does not resolve to a commit")

        def relation(_dir, recorded, tip):
            return relations.get((recorded, tip), 1)

        captured = StringIO()
        with mock.patch.object(module, "step_branch_name",
                               side_effect=lambda _s, step: f"branch-{step['n']}"), \
             mock.patch.object(module, "remote_branch_tip", side_effect=tip), \
             mock.patch.object(module, "_native_relation_commit", side_effect=resolve), \
             mock.patch.object(module, "_native_ancestry_status", side_effect=relation), \
             redirect_stderr(captured):
            try:
                module.refuse_rewritten_stack(".", state, current_step)
            except SystemExit:
                return captured.getvalue()
        return None

    def test_an_abbreviated_receipt_naming_the_tip_is_not_a_rewrite(self):
        """#329 in one assertion: eight characters that resolve to the branch
        tip are that commit, and comparing them to it as strings can only ever
        say they differ."""
        state = self._state()
        state["steps"][2]["receipts"]["push"]["head_commit"] = "c" * 8
        message = self._refusal(
            state, 2, {"branch-3": "c" * 40}, {"c" * 8: "c" * 40}
        )
        self.assertIsNone(
            message,
            "an abbreviated receipt naming the branch tip was read as a rewrite",
        )

    def test_an_abbreviated_ancestor_of_the_tip_is_accepted(self):
        """A legacy short receipt retains the same descendant route as a full one."""
        state = self._state()
        state["steps"][2]["receipts"]["push"]["head_commit"] = "b" * 8
        message = self._refusal(
            state,
            2,
            {"branch-3": "c" * 40},
            {"b" * 8: "b" * 40},
            {("b" * 40, "c" * 40): 0},
        )
        self.assertIsNone(message, "a resolved legacy ancestor was refused")

    def test_an_abbreviated_nonancestor_is_still_refused(self):
        """Resolving must not soften a relation whose old head is absent."""
        state = self._state()
        state["steps"][2]["receipts"]["push"]["head_commit"] = "b" * 8
        message = self._refusal(
            state, 2, {"branch-3": "c" * 40}, {"b" * 8: "b" * 40}
        )
        self.assertIsNotNone(message, "a genuine non-ancestor was accepted")
        self.assertIn("is not an ancestor", message)
        self.assertIn("b" * 40, message)
        self.assertIn("c" * 40, message)

    def test_an_unresolvable_receipt_is_named_rather_than_called_a_rewrite(self):
        """A receipt naming nothing is a receipt this check cannot evaluate. It
        is reported as unreadable, not as evidence of a rewrite it has not
        seen."""
        state = self._state()
        state["steps"][2]["receipts"]["push"]["head_commit"] = "f" * 12
        message = self._refusal(state, 2, {"branch-3": "c" * 40})
        self.assertIsNotNone(message, "an unresolvable receipt was accepted")
        self.assertIn("could not be read", message)
        self.assertIn("branch-3", message)

    def test_a_full_receipt_is_never_resolved(self):
        """The happy path does not shell out. Resolution is reached only when
        the strings differ and the stored value is abbreviated, so an untouched
        stack of full-length receipts asks git nothing."""
        module = self.hexctl
        calls = []

        def resolve(_dir, ref, label):
            calls.append(("resolve", ref))
            return ref

        def relation(_dir, recorded, tip):
            calls.append(("relation", recorded, tip))
            return 0

        with mock.patch.object(module, "step_branch_name",
                               side_effect=lambda _s, step: f"branch-{step['n']}"), \
             mock.patch.object(module, "remote_branch_tip",
                               side_effect=lambda *_a, **_k: "c" * 40), \
             mock.patch.object(module, "_native_relation_commit", side_effect=resolve), \
             mock.patch.object(module, "_native_ancestry_status", side_effect=relation):
            module.refuse_rewritten_stack(".", self._state(), 2)
        self.assertEqual(
            calls, [], "a full-length matching receipt performed relation work"
        )


if __name__ == "__main__":
    unittest.main()
