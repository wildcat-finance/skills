"""Terminal Fiat state is verified, archived locally, and left outside Git."""

import os
import subprocess

try:
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase
except ModuleNotFoundError:
    from test_hexctl import HexctlCase


class FiatLocalRetirementTests(HexctlCase):
    def land_a_run(self):
        self.to_steps(titles=("Scaffold",))
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)
        self.integrate_run()

    def archive_state(self):
        archive_root = os.path.join(self.dir, ".hexaemeron", "archive")
        archive = os.path.join(archive_root, os.listdir(archive_root)[0])
        return os.path.relpath(os.path.join(archive, "state.json"), self.dir)

    def test_done_directive_names_final_status_verification_and_retirement(self):
        self.land_a_run()
        self.assertEqual(
            self.next_json()["finalise"],
            {
                "status": "hexctl status",
                "verify": "hexctl verify",
                "retire": "hexctl reset",
                "archive": "local .hexaemeron/archive",
            },
        )

    def test_terminal_archive_is_local_and_ignored_by_git(self):
        self.land_a_run()
        proc = self.run_ctl("reset")
        self.assertIn("archived verified completed run", proc.stdout)
        self.assertIn("locally at", proc.stdout)
        self.assertEqual(
            subprocess.run(
                ["git", "check-ignore", "-q", self.archive_state()], cwd=self.dir
            ).returncode,
            0,
        )
        for command in (
            ["git", "ls-files", "--", ".hexaemeron"],
            ["git", "status", "--porcelain", "--", ".hexaemeron"],
        ):
            result = subprocess.run(
                command, cwd=self.dir, capture_output=True, text=True, check=True
            )
            self.assertEqual(result.stdout, "")

    def test_explicit_force_can_override_local_ignore_boundary(self):
        self.land_a_run()
        self.run_ctl("reset")
        state = self.archive_state()
        subprocess.run(["git", "add", "-f", "--", state], cwd=self.dir, check=True)
        tracked = subprocess.run(
            ["git", "ls-files", "--", state],
            cwd=self.dir,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(tracked.stdout.strip(), state)


if __name__ == "__main__":
    import unittest

    unittest.main()
