"""Disposable fixture history must ignore inherited commit signing."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]

FIXTURE_COMMIT_MATRIX = (
        (
            "root-boundary",
            (sys.executable, "-m", "unittest", "tests.test_boundary_currency."
             "GuardMutationTests.test_two_scans_render_the_same_bytes"),
        ),
        (
            "hermes",
            (sys.executable, "plugins/hermes/skills/hermes/scripts/test_hermes.py",
             "HermesHarnessTests.test_rejects_any_gas_regression_at_gate_three"),
        ),
        (
            "elenchus",
            (sys.executable, "plugins/hexaemeron/tests/test_elenchus_checker.py",
             "UnittestReports.test_no_changed_test_is_still_unguarded"),
        ),
        (
            "kronos-and-clone",
            (sys.executable, "plugins/hexaemeron/tests/test_kronos_scoreboard.py",
             "DurableHomeTest.test_extra_blobs_in_the_state_ref_are_ignored"),
        ),
        (
            "hexctl-ad-hoc",
            (sys.executable, "plugins/hexaemeron/tests/test_hexctl.py",
             "TestStudyAmendments."
             "test_temporary_git_repositories_demonstrate_holding_and_broken_runs"),
        ),
        (
            "hexctl-integration-path-bounds",
            (sys.executable,
             "plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py",
             "V2OutsideSurfaceTests."
             "test_a_v2_artifact_with_more_than_500_outside_paths_is_accepted"),
        ),
        (
            "horos-demonstration",
            (sys.executable, "plugins/horos/tests/test_demonstration.py",
             "DemonstrationTests.test_entering_the_repository_matches_the_documented_wording"),
        ),
        (
            "horos-scoped-entry",
            (sys.executable, "plugins/horos/tests/test_scoped_entry.py",
             "ScopedEntryTests.test_the_root_check_keeps_its_whole_tree_wording"),
        ),
        (
            "horos-universe",
            (sys.executable, "plugins/horos/tests/test_universe.py",
             "UniverseTests.test_the_default_universe_is_tracked_only"),
        ),
        (
            "horos-binding-directory",
            (sys.executable, "plugins/horos/tests/test_universe.py",
             "BindingDirectoryTests."
             "test_a_vendored_name_holding_nothing_tracked_earns_no_entry"),
        ),
        (
            "horos-candidate-binding",
            (sys.executable, "plugins/horos/tests/test_universe.py",
             "CandidateBindingTests.test_one_tracked_file_still_raises_the_candidate"),
        ),
)


class DisposableGitSigningTests(unittest.TestCase):
    """Exercise one committing fixture from every affected construction site."""

    @staticmethod
    def git_bytes(*args):
        return subprocess.run(
            ["git", "-C", str(ROOT), *args],
            check=True,
            capture_output=True,
        ).stdout

    def test_command_scope_cannot_reenable_fixture_commit_signing(self):
        outer_before = (
            self.git_bytes("rev-parse", "HEAD"),
            self.git_bytes("status", "--porcelain=v1", "--untracked-files=all", "-z"),
            self.git_bytes("config", "--local", "--null", "--list"),
        )
        with tempfile.TemporaryDirectory(prefix="hostile-git-signing-") as temporary:
            fixture = Path(temporary)
            signer = fixture / "failing-signer"
            sentinel = fixture / "signer-invoked"
            global_config = fixture / "global.config"
            signer.write_text(
                "#!/bin/sh\n"
                ": > \"${HOSTILE_SIGNER_SENTINEL:?}\"\n"
                "exit 73\n",
                encoding="utf-8",
            )
            signer.chmod(0o700)
            for key, value in (
                ("commit.gpgsign", "true"),
                ("user.signingkey", "MISSING-TEST-KEY"),
                ("gpg.program", str(signer)),
            ):
                subprocess.run(
                    ["git", "config", "--file", str(global_config), key, value],
                    check=True,
                    capture_output=True,
                )
            config_before = global_config.read_bytes()
            environment = os.environ.copy()
            for name in tuple(environment):
                if (
                    name == "GIT_CONFIG_PARAMETERS"
                    or name == "GIT_CONFIG_COUNT"
                    or name.startswith("GIT_CONFIG_KEY_")
                    or name.startswith("GIT_CONFIG_VALUE_")
                ):
                    environment.pop(name, None)
            for name in (
                "GIT_DIR",
                "GIT_INDEX_FILE",
                "GIT_WORK_TREE",
                "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                "GIT_COMMON_DIR",
                "GIT_NAMESPACE",
                "GIT_PREFIX",
                "GIT_INTERNAL_SUPER_PREFIX",
            ):
                environment.pop(name, None)
            environment.update(
                GIT_CONFIG_GLOBAL=str(global_config),
                GIT_CONFIG_NOSYSTEM="1",
                GIT_CONFIG_COUNT="1",
                GIT_CONFIG_KEY_0="commit.gpgsign",
                GIT_CONFIG_VALUE_0="true",
                HOSTILE_SIGNER_SENTINEL=str(sentinel),
            )

            for case, command in FIXTURE_COMMIT_MATRIX:
                with self.subTest(case=case):
                    completed = subprocess.run(
                        list(command),
                        cwd=ROOT,
                        env=environment,
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    diagnostic = (completed.stdout + completed.stderr)[-4000:]
                    self.assertEqual(completed.returncode, 0, diagnostic)

            self.assertFalse(sentinel.exists(), "an inherited signer handled a fixture commit")
            self.assertEqual(global_config.read_bytes(), config_before)

        outer_after = (
            self.git_bytes("rev-parse", "HEAD"),
            self.git_bytes("status", "--porcelain=v1", "--untracked-files=all", "-z"),
            self.git_bytes("config", "--local", "--null", "--list"),
        )
        self.assertEqual(outer_after, outer_before)


if __name__ == "__main__":
    unittest.main()
