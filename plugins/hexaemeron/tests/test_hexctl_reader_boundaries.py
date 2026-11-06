"""Three reader boundaries the Wave Delta checkpoint work left open.

- skills#899: `checkpoint export` settles its boundary from the ledger tail
  before it computes a directive, so a refusal names the boundary rather than
  an input the directive needed.
- skills#901: the version-1 and version-2 integration readers read one native
  delta, so a rename is the same pair of paths to both.
- skills#1647: a signature refusal prints the signing key only in a
  key-identifier shape, and still refuses when it withholds it.
"""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"


def controller_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_reader_boundaries_under_test", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(directory, *args):
    return subprocess.run(
        ["git", "-C", str(directory), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class Refusals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = controller_module()

    def refusal(self, call):
        error = StringIO()
        with redirect_stderr(error), self.assertRaises(SystemExit):
            call()
        return error.getvalue()


class CheckpointBoundaryOrderTests(Refusals):
    """skills#899."""

    BOUNDARY = (
        "checkpoint export is allowed only immediately after done push or "
        "at an active audit-verdict"
    )

    def test_unaccepted_tail_refuses_before_any_directive(self):
        directive = mock.Mock(
            side_effect=lambda *_a, **_k: self.module.die(
                "version resolution freshness needs the run worktree", 1
            )
        )
        for event in ("done:sync-run", "done:integrate", "init", None):
            with self.subTest(event=event):
                with mock.patch.object(self.module, "_next_directive", directive):
                    error = self.refusal(
                        lambda: self.module._checkpoint_boundary(
                            {"phase": "integrate"}, [{"event": event}]
                        )
                    )
                self.assertIn(self.BOUNDARY, error)
                self.assertNotIn("freshness", error)
        directive.assert_not_called()

    def test_both_accepted_boundaries_still_return_their_directive(self):
        push = {"do": "next-step"}
        with mock.patch.object(self.module, "_next_directive", return_value=push):
            self.assertEqual(
                self.module._checkpoint_boundary({}, [{"event": "done:push"}]),
                ("post-push", push),
            )
        verdict = {"do": "audit-verdict"}
        with mock.patch.object(
            self.module, "_next_directive", return_value=verdict
        ):
            self.assertEqual(
                self.module._checkpoint_boundary({}, [{"event": "audit-round"}]),
                ("audit-verdict", verdict),
            )

    def test_audit_round_without_an_active_verdict_still_refuses(self):
        with mock.patch.object(
            self.module, "_next_directive", return_value={"do": "audit"}
        ):
            error = self.refusal(
                lambda: self.module._checkpoint_boundary(
                    {}, [{"event": "audit-round"}]
                )
            )
        self.assertIn(self.BOUNDARY, error)

    def test_an_empty_ledger_is_refused_first(self):
        error = self.refusal(lambda: self.module._checkpoint_boundary({}, []))
        self.assertIn("non-empty verified ledger", error)


class IntegrationReaderAgreementTests(Refusals):
    """skills#901."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="reader-agreement-")
        self.repository = Path(self.temporary.name)
        git(self.repository, "init", "--quiet", "-b", "main")
        for key, value in (
            ("user.name", "Fixture"),
            ("user.email", "fixture@example.invalid"),
            ("commit.gpgsign", "false"),
            ("gc.auto", "0"),
            # The repository's own setting must not shrink either surface.
            ("diff.renames", "true"),
        ):
            git(self.repository, "config", key, value)
        (self.repository / "old.txt").write_text("same bytes\n" * 20)
        (self.repository / "kept.txt").write_text("kept\n")
        git(self.repository, "add", "-A")
        git(self.repository, "commit", "--quiet", "--no-gpg-sign", "-m", "before")
        self.before = git(self.repository, "rev-parse", "HEAD")
        git(self.repository, "mv", "old.txt", "new.txt")
        git(self.repository, "commit", "--quiet", "--no-gpg-sign", "-m", "rename")
        self.after = git(self.repository, "rev-parse", "HEAD")

    def tearDown(self):
        self.temporary.cleanup()

    def test_both_readers_see_a_rename_as_old_and_new_path(self):
        self.assertEqual(
            git(
                self.repository, "diff", "--name-only", f"{self.before}..{self.after}"
            ),
            "new.txt",
        )
        base = str(self.repository)
        v1 = self.module.git_diff_paths(base, self.before, self.after)
        v2 = self.module.git_diff_paths_for_aggregates(base, self.before, self.after)
        self.assertEqual(v1, ["new.txt", "old.txt"])
        self.assertEqual(v2, v1)

    def test_only_the_version_one_reader_applies_the_count_bound(self):
        base = str(self.repository)
        with mock.patch.object(self.module, "INTEGRATION_PATHS_MAX", 1):
            error = self.refusal(
                lambda: self.module.git_diff_paths(base, self.before, self.after)
            )
            self.assertIn("integration path delta exceeds", error)
            self.assertEqual(
                self.module.git_diff_paths_for_aggregates(
                    base, self.before, self.after
                ),
                ["new.txt", "old.txt"],
            )


class SigningKeyDiagnosticTests(Refusals):
    """skills#1647."""

    COMMIT = "a" * 40

    def refused_with_key(self, key):
        with (
            mock.patch.object(self.module, "signing_key", return_value=key),
            mock.patch.object(self.module, "bounded_tool_status", return_value=1),
        ):
            return self.refusal(
                lambda: self.module.verify_local_commit(
                    str(ROOT), self.COMMIT, "specimen"
                )
            )

    def test_key_identifier_shapes_are_printed(self):
        for key in (
            "0123456789ABCDEF",
            "0123456789ABCDEF0123456789ABCDEF01234567",
            "0123456789abcdef" * 4,
            "SHA256:" + "aB3+/" * 8 + "xyz",
        ):
            with self.subTest(key=key):
                error = self.refused_with_key(key)
                self.assertIn(
                    f"(signed with key {key.upper()}, which this keyring "
                    "cannot validate)",
                    error,
                )

    def test_other_values_are_withheld_and_still_refused(self):
        for key in (
            "producer@example.invalid",
            "0123456789ABCDE",
            "0123456789ABCDEF\x1b[31m",
            "/Users/producer/.gnupg",
            "SHA256:short",
            "G" * 16,
        ):
            with self.subTest(key=key):
                error = self.refused_with_key(key)
                self.assertIn(
                    f"specimen commit {self.COMMIT} has no valid local signature "
                    "(its signing key identifier is not in a recognised form)",
                    error,
                )
                self.assertNotIn(key.upper(), error)

    def test_no_key_keeps_the_bare_refusal(self):
        error = self.refused_with_key("")
        self.assertIn(
            f"specimen commit {self.COMMIT} has no valid local signature\n",
            error,
        )

    def test_a_github_key_still_takes_the_github_refusal(self):
        key = sorted(self.module.GITHUB_SIGNING_KEYS)[0]
        error = self.refused_with_key(key)
        self.assertIn("is signed by GitHub", error)

    def test_a_verified_commit_passes_whatever_its_key_reads(self):
        with (
            mock.patch.object(self.module, "signing_key", return_value="junk"),
            mock.patch.object(self.module, "bounded_tool_status", return_value=0),
        ):
            self.assertEqual(
                self.module.verify_local_commit(str(ROOT), self.COMMIT, "specimen"),
                self.COMMIT,
            )


if __name__ == "__main__":
    unittest.main()
