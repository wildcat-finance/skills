"""Issue 888: Fiat binds merge-time ADR assignments to signed composition.

The Hypomnema allocator owns numbering and byte transformation.  These cases
exercise only Fiat's evidence boundary: replay the canonical report, compare
the immutable candidate tree, verify the signed trailer sequence, and retain
only a replayable active receipt.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
ALLOCATOR = (
    ROOT
    / "plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py"
)
COAUTHOR = "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>"
ORIGIN = "Wildcat-Origin: shoggoth"


def controller_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_fiat_decision_assignments_under_test", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(directory: Path, *args: str, check: bool = True) -> str:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }
    result = subprocess.run(
        [
            "git",
            "-C",
            str(directory),
            "-c",
            "commit.gpgsign=false",
            "-c",
            "tag.gpgsign=false",
            *args,
        ],
        check=check,
        capture_output=True,
        text=True,
        env=environment,
    )
    return result.stdout.strip()


def write(directory: Path, relative: str, content: str) -> None:
    target = directory / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def commit_all(directory: Path, message: str) -> str:
    git(directory, "add", "-A")
    git(directory, "commit", "--quiet", "--no-gpg-sign", "-m", message)
    return git(directory, "rev-parse", "HEAD")


class AssignmentRepository:
    def __init__(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name)
        git(self.path, "init", "--quiet", "-b", "main")
        git(self.path, "config", "user.name", "Fixture")
        git(self.path, "config", "user.email", "fixture@example.invalid")
        write(self.path, ".gitignore", ".hexaemeron/\n")
        write(
            self.path,
            "docs/decisions/ADR-060-existing.md",
            "# ADR-060: Existing\n\nStatus: accepted\n",
        )
        self.base = commit_all(self.path, "base")
        git(self.path, "checkout", "--quiet", "-b", "product")
        write(
            self.path,
            "docs/decisions/drafts/alpha-choice.md",
            "# Decision: Alpha choice\n\nStatus: proposed\n",
        )
        self.product = commit_all(self.path, "product")
        self.report_path = ".hexaemeron/assignments.json"
        self.plan()
        self.report = self.read_report()
        self.materialize_result_tree()
        self.candidate = self.make_candidate()
        git(
            self.path,
            "update-ref",
            "refs/heads/candidate",
            self.candidate,
        )

    def cleanup(self) -> None:
        self.temporary.cleanup()

    def plan(self) -> None:
        subprocess.run(
            [
                "python3",
                str(ALLOCATOR),
                "plan",
                "--repo",
                str(self.path),
                "--base",
                self.base,
                "--base-ref",
                "refs/heads/main",
                "--product",
                self.product,
                "--report",
                self.report_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def read_report(self) -> dict:
        return json.loads((self.path / self.report_path).read_text(encoding="ascii"))

    def materialize_result_tree(self) -> None:
        subprocess.run(
            [
                "python3",
                str(ALLOCATOR),
                "apply",
                "--repo",
                str(self.path),
                "--report",
                self.report_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        git(self.path, "add", "-A")
        self.asserted_result_tree = git(self.path, "write-tree")
        if self.asserted_result_tree != self.report["result_tree"]:
            raise AssertionError("fixture apply did not materialize the reported tree")
        git(self.path, "reset", "--quiet", "--hard", self.product)

    def write_report(self, report: dict) -> None:
        raw = json.dumps(
            report,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"
        (self.path / self.report_path).write_text(raw, encoding="ascii")

    def message(self, *, mappings=None, base=None) -> str:
        rows = self.report["mappings"] if mappings is None else mappings
        base = self.base if base is None else base
        lines = ["Assign decision records", "", f"ADR-Assignment-Base: {base}"]
        lines.extend(
            f"ADR-Assignment: {row['identity']}=ADR-{row['number_text']}"
            for row in rows
        )
        lines.extend((COAUTHOR, ORIGIN))
        return "\n".join(lines)

    def make_candidate(
        self,
        *,
        tree: str | None = None,
        parent: str | None = None,
        message: str | None = None,
    ) -> str:
        return git(
            self.path,
            "commit-tree",
            "--no-gpg-sign",
            tree or self.report["result_tree"],
            "-p",
            parent or self.product,
            "-m",
            message or self.message(),
        )


class FiatDecisionAssignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = controller_module()

    def setUp(self) -> None:
        self.repo = AssignmentRepository()

    def tearDown(self) -> None:
        self.repo.cleanup()

    def refusal(self, callable_object, *args, **kwargs) -> str:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as stopped:
            callable_object(*args, **kwargs)
        self.assertEqual(stopped.exception.code, 2)
        return stderr.getvalue()

    def receipt(self, *, candidate=None, candidate_ref="refs/heads/candidate"):
        with mock.patch.object(
            self.module,
            "verify_local_commit",
            return_value=candidate or self.repo.candidate,
        ) as verifier:
            receipt = self.module.decision_assignment_receipt(
                str(self.repo.path),
                self.repo.report_path,
                candidate or self.repo.candidate,
                candidate_ref=candidate_ref,
            )
        verifier.assert_called_once()
        return receipt

    def assert_clean_filter_refuses_without_execution(self, scope: str) -> None:
        with tempfile.TemporaryDirectory() as outside:
            sentinel = Path(outside) / "clean-filter-executed"
            if scope == "--worktree":
                git(
                    self.repo.path,
                    "config",
                    "--local",
                    "extensions.worktreeConfig",
                    "true",
                )
            git(
                self.repo.path,
                "config",
                scope,
                "filter.hostile.clean",
                "sh -c 'touch \"$FILTER_SENTINEL\"; cat'",
            )
            write(
                self.repo.path,
                ".git/info/attributes",
                "* filter=hostile\n",
            )
            stderr = io.StringIO()
            stopped = None
            with (
                mock.patch.dict(
                    os.environ,
                    {"FILTER_SENTINEL": str(sentinel)},
                ),
                mock.patch.object(
                    self.module,
                    "verify_local_commit",
                    return_value=self.repo.candidate,
                ),
                contextlib.redirect_stderr(stderr),
            ):
                try:
                    self.module.decision_assignment_receipt(
                        str(self.repo.path),
                        self.repo.report_path,
                        self.repo.candidate,
                        candidate_ref="refs/heads/candidate",
                    )
                except SystemExit as error:
                    stopped = error.code
            self.assertEqual((stopped, sentinel.exists()), (2, False))
            self.assertIn(
                "configures a clean or process filter",
                stderr.getvalue(),
            )

    def test_exact_report_candidate_and_ordered_trailers_are_receipted(self):
        receipt = self.receipt()
        self.assertEqual(receipt["schema"], "fiat-decision-assignment-composition/v1")
        self.assertEqual(receipt["report_schema"], "fiat-decision-assignments/v1")
        self.assertEqual(receipt["base"], self.repo.base)
        self.assertEqual(receipt["product"], self.repo.product)
        self.assertEqual(receipt["candidate"], self.repo.candidate)
        self.assertEqual(receipt["result_tree"], self.repo.report["result_tree"])
        self.assertEqual(receipt["mappings"], self.repo.report["mappings"])
        self.assertRegex(receipt["report_sha256"], r"\A[0-9a-f]{64}\Z")
        self.assertRegex(receipt["commit_message_sha256"], r"\A[0-9a-f]{64}\Z")

    def test_repository_without_clean_filters_still_verifies(self):
        self.assertEqual(self.receipt()["candidate"], self.repo.candidate)

    def test_local_clean_filter_refuses_before_worktree_observation(self):
        self.assert_clean_filter_refuses_without_execution("--local")

    def test_worktree_clean_filter_refuses_before_worktree_observation(self):
        self.assert_clean_filter_refuses_without_execution("--worktree")

    def test_filter_added_after_preflight_cannot_execute_during_status(self):
        with tempfile.TemporaryDirectory() as outside:
            sentinel = Path(outside) / "clean-filter-executed"
            write(
                self.repo.path,
                ".git/info/attributes",
                "* filter=hostile\n",
            )
            tracked = self.repo.path / "docs/decisions/ADR-060-existing.md"
            os.utime(tracked, None)
            original_probe = self.module.bounded_probe
            config_probes = 0
            installed = False

            def changing_probe(
                base_dir,
                program,
                argv,
                extra_env=None,
                *,
                environment=None,
            ):
                nonlocal config_probes, installed
                is_status = program == "git" and "status" in argv
                try:
                    result = original_probe(
                        base_dir,
                        program,
                        argv,
                        extra_env,
                        environment=environment,
                    )
                finally:
                    if is_status and installed:
                        git(
                            self.repo.path,
                            "config",
                            "--local",
                            "--unset-all",
                            "filter.hostile.clean",
                            check=False,
                        )
                if program == "git" and len(argv) > 1 and argv[1] == "config":
                    config_probes += 1
                    if config_probes == 2:
                        git(
                            self.repo.path,
                            "config",
                            "--local",
                            "filter.hostile.clean",
                            "sh -c 'touch \"$FILTER_SENTINEL\"; cat'",
                        )
                        installed = True
                return result

            with (
                mock.patch.dict(
                    os.environ,
                    {"FILTER_SENTINEL": str(sentinel)},
                ),
                mock.patch.object(
                    self.module,
                    "bounded_probe",
                    side_effect=changing_probe,
                ),
            ):
                receipt = self.receipt()
            configured = git(
                self.repo.path,
                "config",
                "--local",
                "--get-all",
                "filter.hostile.clean",
                check=False,
            )
            self.assertEqual(
                (receipt["schema"], sentinel.exists(), configured),
                ("fiat-decision-assignment-composition/v1", False, ""),
            )

    def test_stale_base_ref_refuses_before_a_receipt(self):
        git(self.repo.path, "checkout", "--quiet", "main")
        write(self.repo.path, "base-advance.txt", "advanced\n")
        commit_all(self.repo.path, "base advance")
        git(self.repo.path, "checkout", "--quiet", "product")
        with mock.patch.object(self.module, "verify_local_commit"):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                self.repo.candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_altered_candidate_tree_refuses(self):
        candidate = self.repo.make_candidate(
            tree=git(self.repo.path, "rev-parse", f"{self.repo.product}^{{tree}}")
        )
        git(self.repo.path, "update-ref", "refs/heads/candidate", candidate)
        with mock.patch.object(self.module, "verify_local_commit", return_value=candidate):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_mismatched_input_blob_refuses(self):
        report = self.repo.read_report()
        report["mappings"][0]["input_blob"] = "0" * len(
            report["mappings"][0]["input_blob"]
        )
        self.repo.write_report(report)
        with mock.patch.object(self.module, "verify_local_commit"):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                self.repo.candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_mismatched_output_blob_refuses(self):
        report = self.repo.read_report()
        report["mappings"][0]["output_blob"] = "0" * len(
            report["mappings"][0]["output_blob"]
        )
        self.repo.write_report(report)
        with mock.patch.object(self.module, "verify_local_commit"):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                self.repo.candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_unordered_assignment_trailers_refuse(self):
        second = dict(self.repo.report["mappings"][0])
        second["identity"] = "adr/zeta-choice"
        second["number_text"] = "062"
        message = self.repo.message(mappings=[second, self.repo.report["mappings"][0]])
        candidate = self.repo.make_candidate(message=message)
        git(self.repo.path, "update-ref", "refs/heads/candidate", candidate)
        with mock.patch.object(self.module, "verify_local_commit", return_value=candidate):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_extra_assignment_trailer_refuses(self):
        message = self.repo.message() + "\nADR-Assignment: adr/extra=ADR-999"
        candidate = self.repo.make_candidate(message=message)
        git(self.repo.path, "update-ref", "refs/heads/candidate", candidate)
        with mock.patch.object(self.module, "verify_local_commit", return_value=candidate):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_unsigned_candidate_refuses(self):
        message = self.refusal(
            self.module.decision_assignment_receipt,
            str(self.repo.path),
            self.repo.report_path,
            self.repo.candidate,
            candidate_ref="refs/heads/candidate",
        )
        self.assertIn("signature", message)

    def test_moved_candidate_ref_refuses(self):
        git(
            self.repo.path,
            "update-ref",
            "refs/heads/candidate",
            self.repo.product,
        )
        with mock.patch.object(self.module, "verify_local_commit"):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                self.repo.candidate,
                candidate_ref="refs/heads/candidate",
            )

    def test_dirty_worktree_refuses_without_mutation(self):
        write(self.repo.path, "dirty.txt", "dirty\n")
        before = git(self.repo.path, "status", "--porcelain=v1")
        with mock.patch.object(self.module, "verify_local_commit"):
            self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                self.repo.candidate,
                candidate_ref="refs/heads/candidate",
            )
        self.assertEqual(git(self.repo.path, "status", "--porcelain=v1"), before)

    def test_partial_receipt_refuses_replay(self):
        receipt = self.receipt()
        receipt.pop("result_tree")
        with mock.patch.object(self.module, "verify_local_commit"):
            self.refusal(
                self.module.replay_decision_assignment_receipt,
                str(self.repo.path),
                receipt,
            )

    def test_canonical_receipt_replays_after_recovery_round_trip(self):
        receipt = self.receipt()
        recovered = json.loads(json.dumps(receipt, sort_keys=True))
        with mock.patch.object(
            self.module,
            "verify_local_commit",
            return_value=self.repo.candidate,
        ):
            replayed = self.module.replay_decision_assignment_receipt(
                str(self.repo.path), recovered
            )
        self.assertEqual(replayed, receipt)

    def test_recovery_replays_policy_without_requiring_the_mutable_base_ref(self):
        receipt = self.receipt()
        base_tree = git(self.repo.path, "rev-parse", f"{self.repo.base}^{{tree}}")
        advanced_base = git(
            self.repo.path,
            "commit-tree",
            "--no-gpg-sign",
            base_tree,
            "-p",
            self.repo.base,
            "-m",
            "move base before recovery",
        )
        git(
            self.repo.path,
            "update-ref",
            "refs/heads/main",
            advanced_base,
        )
        with (
            mock.patch.object(
                self.module,
                "_replay_decision_assignment_report",
                wraps=self.module._replay_decision_assignment_report,
            ) as replay,
            mock.patch.object(
                self.module,
                "verify_local_commit",
                return_value=self.repo.candidate,
            ),
        ):
            replayed = self.module.replay_decision_assignment_receipt(
                str(self.repo.path),
                receipt,
                verify_base_ref=False,
            )
        self.assertEqual(replayed, receipt)
        replay.assert_called_once()
        self.assertFalse(replay.call_args.kwargs["verify_base_ref"])

    def test_base_ref_movement_after_policy_replay_refuses(self):
        base_tree = git(self.repo.path, "rev-parse", f"{self.repo.base}^{{tree}}")
        advanced_base = git(
            self.repo.path,
            "commit-tree",
            "--no-gpg-sign",
            base_tree,
            "-p",
            self.repo.base,
            "-m",
            "advance base ref",
        )

        def move_base_ref(*_args, **_kwargs):
            git(
                self.repo.path,
                "update-ref",
                "refs/heads/main",
                advanced_base,
            )

        with (
            mock.patch.object(
                self.module,
                "_replay_decision_assignment_report",
                side_effect=move_base_ref,
            ),
            mock.patch.object(
                self.module,
                "verify_local_commit",
                return_value=self.repo.candidate,
            ),
        ):
            message = self.refusal(
                self.module.decision_assignment_receipt,
                str(self.repo.path),
                self.repo.report_path,
                self.repo.candidate,
                candidate_ref="refs/heads/candidate",
            )
        self.assertIn("base ref moved during evidence collection", message)

    def test_superseded_assignment_cannot_remain_in_active_ancestry(self):
        old = self.receipt()
        descendant = self.repo.make_candidate(parent=self.repo.candidate)
        current = dict(old, candidate=descendant)
        self.refusal(
            self.module.require_decision_assignment_supersession,
            str(self.repo.path),
            old,
            current,
        )

    def test_every_superseded_assignment_is_excluded_from_active_ancestry(self):
        first = self.receipt()
        sibling_candidate = self.repo.make_candidate(
            message=self.repo.message().replace(
                "Assign decision records", "First replacement assignment", 1
            )
        )
        second = dict(first, candidate=sibling_candidate)
        active_candidate = self.repo.make_candidate(
            parent=self.repo.candidate,
            message=self.repo.message().replace(
                "Assign decision records", "Second replacement assignment", 1
            ),
        )
        active = dict(first, candidate=active_candidate)
        message = self.refusal(
            self.module.require_decision_assignment_supersession,
            str(self.repo.path),
            [first, second],
            active,
        )
        self.assertIn(
            "superseded decision assignment remains in active ancestry",
            message,
        )

    def test_complete_supersession_history_reaches_receipt_replay(self):
        active_receipt = self.receipt()
        first_receipt = dict(active_receipt, candidate=self.repo.base)
        second_receipt = dict(active_receipt, candidate=self.repo.product)
        active_sync = {
            "commit": self.repo.candidate,
            "parents": [self.repo.base, self.repo.product],
            self.module.DECISION_ASSIGNMENT_SYNC_KEY: active_receipt,
        }
        history = [
            {
                "commit": self.repo.base,
                self.module.DECISION_ASSIGNMENT_SYNC_KEY: first_receipt,
            },
            {
                "commit": self.repo.product,
                self.module.DECISION_ASSIGNMENT_SYNC_KEY: second_receipt,
            },
        ]
        with mock.patch.object(
            self.module,
            "replay_decision_assignment_receipt",
            return_value=active_receipt,
        ) as replay:
            self.module.replay_sync_decision_assignment(
                str(self.repo.path),
                active_sync,
                previous_sync=history,
            )
        self.assertEqual(
            replay.call_args.kwargs["previous_receipt"],
            [first_receipt, second_receipt],
        )

    def test_replacement_assignment_may_be_a_sibling(self):
        old = self.receipt()
        replacement = self.repo.make_candidate(
            message=self.repo.message().replace(
                "Assign decision record", "Replace decision assignment", 1
            )
        )
        self.assertNotEqual(replacement, self.repo.candidate)
        current = dict(old, candidate=replacement)
        self.module.require_decision_assignment_supersession(
            str(self.repo.path), old, current
        )

    def test_read_only_command_is_exposed(self):
        args = self.module.build_parser().parse_args(
            [
                "verify-decision-assignments",
                "--report",
                self.repo.report_path,
                "--candidate",
                self.repo.candidate,
                "--candidate-ref",
                "refs/heads/candidate",
            ]
        )
        self.assertIs(args.fn, self.module.cmd_verify_decision_assignments)

    def test_read_only_command_requires_candidate_ref(self):
        with self.assertRaises(SystemExit) as stopped:
            self.module.build_parser().parse_args(
                [
                    "verify-decision-assignments",
                    "--report",
                    self.repo.report_path,
                    "--candidate",
                    self.repo.candidate,
                ]
            )
        self.assertEqual(stopped.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
