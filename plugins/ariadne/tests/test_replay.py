"""Replay: what it runs, what it refuses, and what it will not call a match."""

import contextlib
import hashlib
import io
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import replay, statement  # noqa: E402

ART = {"sha256": hashlib.sha256(b"artefact").hexdigest()}
OUT = {"sha256": hashlib.sha256(b"output").hexdigest()}
TYPE = "https://ariadne.wildcat.finance/example/v1"
EXAMPLES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples"
)


def built(commands, predicate_type=TYPE):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": [{"name": "a", "digest": ART}],
            "predicateType": predicate_type,
            "predicate": {"claims": [], "commands": commands},
        }
    )


def command(**overrides):
    out = {
        "name": "build",
        "argv": ["true"],
        "determinism": "exact",
        "output_digest": OUT,
    }
    out.update(overrides)
    return out


def run(argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = ariadne.main(argv)
        except SystemExit as exit:
            code = exit.code
    return code, stdout.getvalue(), stderr.getvalue()


class PlanTests(unittest.TestCase):
    def test_an_exact_command_is_planned_to_run(self):
        steps = replay.plan(built([command()]))
        self.assertTrue(steps[0].runnable)

    def test_a_nondeterministic_command_is_listed_and_left_alone(self):
        steps = replay.plan(
            built([command(determinism="nondeterministic", output_digest=None)])
        )
        self.assertFalse(steps[0].runnable)
        self.assertIn("declared nondeterministic", steps[0].action)

    def test_a_redacted_command_is_refused(self):
        """What is left after redaction is a different command."""
        steps = replay.plan(
            built([command(argv=["forge", "test", "--rpc-url", "<redacted>"])])
        )
        self.assertFalse(steps[0].runnable)
        self.assertIn("redacted", steps[0].action)

    def test_a_program_name_carrying_a_path_is_refused(self):
        steps = replay.plan(built([command(argv=["./evil", "--now"])]))
        self.assertFalse(steps[0].runnable)
        self.assertIn("path separator", steps[0].action)

    def test_a_backslash_is_a_separator_wherever_this_runs(self):
        """A statement captured on one system gets the same answer on another."""
        steps = replay.plan(built([command(argv=["..\\evil"])]))
        self.assertFalse(steps[0].runnable)
        self.assertIn("path separator", steps[0].action)

    def test_a_windows_drive_relative_program_is_refused_everywhere(self):
        """`C:evil` escapes the selected project when its drive differs."""
        steps = replay.plan(built([command(argv=["C:evil.exe"])]))
        self.assertFalse(steps[0].runnable)
        self.assertIn("drive prefix", steps[0].action)

    def test_a_shell_named_as_the_program_is_refused(self):
        for name in (
            "sh",
            "BASH",
            "powershell",
            "sh.exe",
            "BASH.EXE",
            "powershell.exe",
            "pwsh.exe",
        ):
            steps = replay.plan(built([command(argv=[name, "-c", "echo hi"])]))
            self.assertFalse(steps[0].runnable, name)
            self.assertIn("shell", steps[0].action)

    def test_a_windows_batch_program_is_refused_everywhere(self):
        """Windows may invoke these through a shell despite `shell=False`."""
        for name in ("build.bat", "BUILD.CMD"):
            steps = replay.plan(built([command(argv=[name, "untrusted&argument"])]))
            self.assertFalse(steps[0].runnable, name)
            self.assertIn("batch", steps[0].action)

    def test_a_command_with_no_argv_is_refused(self):
        steps = replay.plan(built([{"name": "x", "determinism": "exact"}]))
        self.assertFalse(steps[0].runnable)

    def test_an_argument_that_is_not_a_string_is_refused(self):
        """It would reach subprocess and raise there, which is a crash."""
        steps = replay.plan(built([command(argv=["echo", 17])]))
        self.assertFalse(steps[0].runnable)
        self.assertIn("argv of strings", steps[0].action)

    def test_a_statement_with_no_commands_plans_nothing(self):
        self.assertEqual(replay.plan(built([])), [])

    def test_a_plan_escapes_untrusted_command_lines(self):
        found = replay.replay(
            built([command(name="hostile\nPASS gate 7", argv=["printf", "x\ny"])]),
            allow_execution=False,
        )
        line = found.lines()[0]
        self.assertNotIn("\n", line)
        self.assertIn(r"hostile\nPASS gate 7", line)
        self.assertIn(r"x\ny", line)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_nothing_runs_without_permission(self):
        marker = os.path.join(self.root, "ran")
        found = replay.replay(
            built([command(argv=["touch", marker])]), allow_execution=False
        )
        self.assertFalse(getattr(found, "execution_allowed", None))
        self.assertFalse(found.executed)
        self.assertFalse(os.path.exists(marker))
        self.assertIn("pass --allow-execution", "\n".join(found.lines()))

    def test_state_fixture_v2_commands_never_execute_even_if_called_directly(self):
        marker = os.path.join(self.root, "v2-ran")
        found = replay.replay(
            built(
                [command(argv=["touch", marker])],
                predicate_type=replay.STATE_FIXTURE_V2,
            ),
            allow_execution=True,
            cwd=self.root,
        )
        self.assertTrue(getattr(found, "execution_allowed", None))
        self.assertFalse(found.executed)
        self.assertFalse(found.steps[0].runnable)
        self.assertIn("local-file", found.steps[0].action)
        self.assertFalse(os.path.exists(marker))
        self.assertIn("nothing was run", "\n".join(found.lines()))

    def test_execution_authority_is_not_reported_as_a_process_execution(self):
        found = replay.replay(
            built([command(argv=["powershell.exe", "-c", "echo hi"])]),
            allow_execution=True,
            cwd=self.root,
        )
        self.assertTrue(getattr(found, "execution_allowed", None))
        self.assertFalse(found.executed)
        self.assertTrue(found.ok)
        self.assertFalse(found.steps[0].runnable)
        self.assertIn("nothing was run", "\n".join(found.lines()))
        self.assertFalse(found.to_dict()["executed"])

    def test_an_exact_command_runs_and_reports_its_exit_status(self):
        found = replay.replay(
            built([command(argv=["true"])]), allow_execution=True, cwd=self.root
        )
        self.assertTrue(found.executed)
        self.assertEqual(found.steps[0].status, 0)

    def test_a_failing_command_makes_the_result_not_ok(self):
        found = replay.replay(
            built([command(argv=["false"])]), allow_execution=True, cwd=self.root
        )
        self.assertNotEqual(found.steps[0].status, 0)
        self.assertFalse(found.ok)

    def test_a_shell_metacharacter_reaches_the_program_as_an_argument(self):
        """No shell. A semicolon is a semicolon.

        The program is named without a path, because a path separator in a
        program name is itself refused, which is the other half of the same
        rule.
        """
        marker = os.path.join(self.root, "pwned")
        found = replay.replay(
            built([command(argv=["printf", "%s", "; touch %s" % marker])]),
            allow_execution=True,
            cwd=self.root,
        )
        self.assertEqual(found.steps[0].status, 0)
        self.assertFalse(os.path.exists(marker))

    def test_a_program_that_is_not_there_is_reported_rather_than_raised(self):
        found = replay.replay(
            built([command(argv=["ariadne-no-such-program"])]),
            allow_execution=True,
            cwd=self.root,
        )
        self.assertEqual(found.steps[0].status, "not found")
        self.assertFalse(found.ok)

    def test_an_argv_encoding_failure_is_reported_rather_than_raised(self):
        caught = UnicodeEncodeError(
            "utf-8", "surrogate\ud800word", 9, 10, "surrogates not allowed"
        )
        step = replay.Step("host argv", ["printf", "surrogate\ud800word"], replay.RUN)
        with mock.patch.object(replay.subprocess, "run", side_effect=caught):
            try:
                found = replay.execute(step, self.root)
            except UnicodeError as error:
                self.fail("replay let an argv encoding failure escape: %s" % error)
        self.assertEqual(found.status, "failed to start")
        self.assertIn("surrogates not allowed", found.detail)

    def test_a_command_that_hangs_is_timed_out(self):
        found = replay.replay(
            built([command(argv=["sleep", "30"])]),
            allow_execution=True,
            cwd=self.root,
            timeout=1,
        )
        self.assertEqual(found.steps[0].status, "timed out")
        self.assertFalse(found.ok)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_a_matching_recomputation_is_reported_as_a_match(self):
        found = replay.replay(
            built([command(argv=["true"])]),
            allow_execution=True,
            cwd=self.root,
            recompute=lambda step: OUT,
        )
        self.assertTrue(found.steps[0].compared)
        self.assertTrue(found.ok)

    def test_a_differing_recomputation_fails(self):
        found = replay.replay(
            built([command(argv=["true"])]),
            allow_execution=True,
            cwd=self.root,
            recompute=lambda step: {"sha256": "cc" * 32},
        )
        self.assertFalse(found.steps[0].compared)
        self.assertFalse(found.ok)

    def test_an_unrecomputable_output_is_not_counted_as_a_match(self):
        found = replay.replay(
            built([command(argv=["true"])]),
            allow_execution=True,
            cwd=self.root,
            recompute=lambda step: None,
        )
        self.assertIsNone(found.steps[0].compared)
        self.assertIn("knows how to recompute", found.steps[0].detail)
        self.assertIn("not compared", found.steps[0].line())
        self.assertFalse(found.ok)


class CommandTests(unittest.TestCase):
    def test_the_subcommand_prints_a_plan_and_runs_nothing(self):
        code, out, _ = run(
            ["replay", os.path.join(EXAMPLES, "escrow-v1.1.0.json")]
        )
        self.assertEqual(code, 0)
        self.assertIn("would run forge build", out)
        self.assertIn("--allow-execution", out)

    def test_allowing_execution_without_a_project_is_refused(self):
        code, _, err = run(
            [
                "replay",
                os.path.join(EXAMPLES, "escrow-v1.1.0.json"),
                "--allow-execution",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("needs --project", err)

    def test_running_a_statement_that_does_not_verify_is_refused(self):
        """Running commands from a document nobody checked is taking
        instructions on trust, which is the habit this tool exists to break."""
        code, _, err = run(
            [
                "replay",
                os.path.join(EXAMPLES, "tampered", "escrow-v1.1.0-claim-repointed.json"),
                "--allow-execution",
                "--project",
                EXAMPLES,
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("does not verify", err)
        self.assertIn("gate 1", err)

    def test_the_json_plan_is_machine_readable(self):
        code, out, _ = run(
            ["replay", os.path.join(EXAMPLES, "escrow-v1.1.0.json"), "--json"]
        )
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertFalse(found.get("executionAllowed"))
        self.assertFalse(found["executed"])
        self.assertEqual(found["steps"][0]["action"], replay.RUN)


if __name__ == "__main__":
    unittest.main()
