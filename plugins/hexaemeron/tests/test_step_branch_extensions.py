"""A waiting Fiat step may extend without losing its receipted history.

Issue 923 exposed an equality check that called every moved branch a rewrite.
This fixture keeps the four observable outcomes separate: an equal head makes
no graph query, a strict descendant passes topology only, a non-ancestor
refuses, and an unanswered native graph query refuses as unknown.  The
controller's existing merge receipt remains responsible for signatures,
trailers, GitHub verification, and author/committer attribution over the live
range.

The graph cases use real Git objects.  The end-to-end case uses the established
delivery harness so it can inspect the immutable push receipt and the repaired
``effective_push`` record independently.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
HEXCTL = HERE.parent / "skills" / "fiat" / "scripts" / "hexctl.py"

# ``run_tests.py`` discovers from this directory and already exposes the
# harness.  Direct execution needs the same explicit import path.
sys.path.insert(0, str(HERE))
from test_hexctl import HexctlCase, LINTS_CLEAN, SUITE  # noqa: E402


def hexctl_module():
    spec = importlib.util.spec_from_file_location(
        "hexctl_step_branch_extensions", HEXCTL
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NativeGraphCase(unittest.TestCase):
    """One real ``P -> E`` graph plus a commit from unrelated history."""

    def setUp(self):
        self.hexctl = hexctl_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self._git("init", "-q", "-b", "main")
        self._git("config", "commit.gpgsign", "false")
        self._git("config", "user.name", "Fixture")
        self._git("config", "user.email", "fixture@example.invalid")

        (self.repo / "history.txt").write_text("P\n", encoding="utf-8")
        self._git("add", "history.txt")
        self._git("commit", "-q", "-m", "P")
        self.recorded = self._git("rev-parse", "HEAD").stdout.strip()

        (self.repo / "history.txt").write_text("P\nE\n", encoding="utf-8")
        self._git("commit", "-q", "-am", "E")
        self.descendant = self._git("rev-parse", "HEAD").stdout.strip()

        tree = self._git("mktree", input_text="").stdout.strip()
        identity = {
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
        self.unrelated = self._git(
            "commit-tree", tree, "-m", "unrelated", extra_env=identity
        ).stdout.strip()

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *argv, input_text=None, extra_env=None):
        executable = shutil.which("git", path=os.defpath)
        self.assertIsNotNone(executable)
        result = subprocess.run(
            [executable, "-c", "commit.gpgsign=false", *argv],
            cwd=self.repo,
            input=input_text,
            capture_output=True,
            text=True,
            env=dict(extra_env or {}),
        )
        if result.returncode:
            self.fail(
                f"git {' '.join(argv)} -> {result.returncode}\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return result

    def _state(self, recorded=None):
        return {
            "integrate": {"merged": [1]},
            "steps": [
                {
                    "n": 1,
                    "title": "merged",
                    "receipts": {"push": {"head_commit": "a" * 40}},
                },
                {
                    "n": 2,
                    "title": "current",
                    "receipts": {"push": {"head_commit": "b" * 40}},
                },
                {
                    "n": 3,
                    "title": "waiting",
                    "receipts": {
                        "push": {"head_commit": recorded or self.recorded}
                    },
                },
            ],
        }

    def _run_guard(self, tip, *, state=None, current_step=2):
        """Return the bounded refusal text, or ``None`` when topology passes."""
        module = self.hexctl
        captured = StringIO()
        with mock.patch.object(
            module,
            "step_branch_name",
            side_effect=lambda _state, step: f"branch-{step['n']}",
        ), mock.patch.object(module, "remote_branch_tip", return_value=tip), \
                redirect_stderr(captured):
            try:
                module.refuse_rewritten_stack(
                    str(self.repo), state or self._state(), current_step
                )
            except SystemExit:
                return captured.getvalue()
        return None

    def test_equal_head_makes_no_relation_call(self):
        module = self.hexctl
        with mock.patch.object(
            module,
            "bounded_probe",
            side_effect=AssertionError("equality started an ancestry process"),
        ):
            self.assertIsNone(self._run_guard(self.recorded))

    def test_strict_descendant_passes_the_waiting_topology_guard(self):
        self.assertIsNone(
            self._run_guard(self.descendant),
            "P remained in E's native history but equality refused the branch",
        )

    def test_nonancestor_refusal_names_only_the_observed_relation(self):
        message = self._run_guard(self.unrelated)
        self.assertIsNotNone(message)
        self.assertIn("step 3", message)
        self.assertIn("branch-3", message)
        self.assertIn(self.recorded, message)
        self.assertIn(self.unrelated, message)
        self.assertIn("is not an ancestor", message)
        self.assertNotIn("GitHub's stacked-pull-request flow", message)
        self.assertNotIn("re-signs", message)

    def test_missing_object_is_unknown_not_a_claim_about_rewrite_cause(self):
        missing = "f" * 40
        message = self._run_guard(missing)
        self.assertIsNotNone(message)
        self.assertIn("step 3", message)
        self.assertIn("branch-3", message)
        self.assertIn(self.recorded, message)
        self.assertIn(missing, message)
        self.assertIn("ancestry could not be determined", message)
        self.assertNotIn("GitHub's stacked-pull-request flow", message)

    def test_start_timeout_cap_and_unexpected_status_are_all_unknown(self):
        outcomes = (
            (None, b"", "start"),
            (None, b"", "timeout"),
            (None, b"ignored", "output-cap"),
            (128, b"ignored", None),
        )
        for outcome in outcomes:
            with self.subTest(outcome=outcome), mock.patch.object(
                self.hexctl, "bounded_probe", return_value=outcome
            ):
                message = self._run_guard(self.descendant)
                self.assertIsNotNone(message)
                self.assertIn("ancestry could not be determined", message)
                self.assertIn(self.recorded, message)
                self.assertIn(self.descendant, message)

    def test_native_query_scrubs_git_state_and_uses_fixed_no_replace_argv(self):
        module = self.hexctl
        calls = []
        native_probe = module.bounded_probe

        def record_probe(*args, **kwargs):
            calls.append((args, kwargs))
            return native_probe(*args, **kwargs)

        hostile = {
            "GIT_DIR": str(self.repo / "absent-git-dir"),
            "GIT_OBJECT_DIRECTORY": str(self.repo / "absent-objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(self.repo / "absent-alts"),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.repositoryformatversion",
            "GIT_CONFIG_VALUE_0": "999",
        }
        with mock.patch.dict(os.environ, hostile, clear=False), mock.patch.object(
            module, "bounded_probe", side_effect=record_probe
        ):
            message = self._run_guard(self.descendant)
        self.assertIsNone(message)
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertEqual(args[1], module._native_git_executable())
        self.assertTrue(os.path.isabs(args[1]))
        self.assertEqual(
            args[2],
            [
                "--no-replace-objects",
                "merge-base",
                "--is-ancestor",
                self.recorded,
                self.descendant,
            ],
        )
        environment = kwargs["environment"]
        for name, value in hostile.items():
            self.assertNotEqual(environment.get(name), value)
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], os.devnull)
        self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(environment["GIT_CONFIG_SYSTEM"], os.devnull)
        self.assertEqual(environment["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")

    def test_relation_guard_and_signature_git_use_closed_environments(self):
        module = self.hexctl
        hostile = {
            "BASH_ENV": str(self.repo / "bash-env"),
            "DYLD_FRAMEWORK_PATH": str(self.repo / "frameworks"),
            "DYLD_INSERT_LIBRARIES": str(self.repo / "inject.dylib"),
            "DYLD_LIBRARY_PATH": str(self.repo / "libraries"),
            "ENV": str(self.repo / "shell-env"),
            "GCONV_PATH": str(self.repo / "gconv"),
            "GIT_DIR": str(self.repo / "foreign-git-dir"),
            "GIT_OBJECT_DIRECTORY": str(self.repo / "foreign-objects"),
            "HOME": str(self.repo / "home"),
            "LD_AUDIT": str(self.repo / "audit.so"),
            "LD_LIBRARY_PATH": str(self.repo / "ld-libraries"),
            "LD_PRELOAD": str(self.repo / "preload.so"),
            "GNUPGHOME": str(self.repo / "gnupg"),
            "PYTHONHOME": str(self.repo / "python-home"),
            "PYTHONPATH": str(self.repo / "python-path"),
            "SSH_AUTH_SOCK": str(self.repo / "agent.sock"),
        }
        with mock.patch.dict(os.environ, hostile, clear=True), mock.patch.object(
            module, "bounded_tool", return_value=b""
        ) as runner:
            module._native_relation_git(str(self.repo), ["status"], "relation")
            module._guard_native_git(str(self.repo), ["status"], "guard")
            module._guard_exact_git(str(self.repo), ["status"], "exact")
            module._native_signature_git(
                str(self.repo), ["verify-commit", "a" * 40], "signature"
            )

        base = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": os.defpath,
            "SSH_AUTH_SOCK": hostile["SSH_AUTH_SOCK"],
        }
        calls = runner.call_args_list
        self.assertEqual(len(calls), 4)
        for call in calls[:3]:
            self.assertEqual(call.kwargs["environment"], base)
        verifier_directories = [
            *os.defpath.split(os.pathsep),
            "/usr/local/bin",
            "/opt/homebrew/bin",
            "/opt/local/bin",
        ]
        signature = {
            **base,
            "GNUPGHOME": hostile["GNUPGHOME"],
            "HOME": hostile["HOME"],
            "PATH": os.pathsep.join(
                dict.fromkeys(
                    path for path in verifier_directories if os.path.isabs(path)
                )
            ),
        }
        self.assertEqual(calls[3].kwargs["environment"], signature)

    def test_native_fixture_git_ignores_the_ambient_environment(self):
        hostile = {
            "GIT_DIR": str(self.repo / "foreign-git-dir"),
            "GIT_OBJECT_DIRECTORY": str(self.repo / "foreign-objects"),
            "LD_PRELOAD": str(self.repo / "preload.so"),
        }
        native_run = subprocess.run
        calls = []

        def record_run(*args, **kwargs):
            calls.append((args, kwargs))
            return native_run(*args, **kwargs)

        with mock.patch.dict(os.environ, hostile, clear=False), mock.patch.object(
            subprocess, "run", side_effect=record_run
        ):
            result = self._git("rev-parse", "HEAD")
        self.assertEqual(result.stdout.strip(), self.descendant)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1]["env"], {})
        self.assertTrue(os.path.isabs(calls[0][0][0][0]))

    def test_replacement_ref_cannot_manufacture_native_ancestry(self):
        # Replacing the unrelated tip with E makes ordinary Git report P as an
        # ancestor.  The controller must ask about native objects instead.
        self._git("replace", self.unrelated, self.descendant)
        ordinary = self._git(
            "merge-base", "--is-ancestor", self.recorded, self.unrelated
        )
        self.assertEqual(ordinary.returncode, 0, ordinary.stderr)
        message = self._run_guard(self.unrelated)
        self.assertIsNotNone(message)
        self.assertIn("is not an ancestor", message)

    def test_only_waiting_steps_receive_relation_queries(self):
        module = self.hexctl
        state = self._state()
        state["integrate"]["merged"] = [1, 2]
        calls = []
        native_probe = module.bounded_probe

        def record_probe(*args, **kwargs):
            calls.append(args[2])
            return native_probe(*args, **kwargs)

        with mock.patch.object(
            module, "bounded_probe", side_effect=record_probe
        ):
            self.assertIsNone(
                self._run_guard(self.descendant, state=state, current_step=3)
            )
        self.assertEqual(calls, [])

    def test_refusal_does_not_mutate_the_supplied_state(self):
        state = self._state()
        before = json.dumps(state, sort_keys=True, separators=(",", ":"))
        self.assertIsNotNone(self._run_guard(self.unrelated, state=state))
        after = json.dumps(state, sort_keys=True, separators=(",", ":"))
        self.assertEqual(after, before)


class DescendantMergeReceiptCase(HexctlCase):
    """A descendant passes topology, then earns fresh full-range evidence."""

    URL_TEMPLATE = "https://github.com/wildcat-finance/example/pull/{}"

    def _finish_step(self, number, head_commit=None):
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(number),
            "--commit",
            f"abc{number}",
        )
        if number == 1:
            self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done",
            "prose",
            "--files",
            "1",
            "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.run_ctl(
            "done",
            "push",
            "--pr-url",
            self.URL_TEMPLATE.format(number),
            "--head-commit",
            head_commit or format(number, "x") * 40,
            "--pr-base",
            self.step_base(number),
        )

    def test_descendant_is_reverified_without_rewriting_the_push_receipt(self):
        self.to_steps(("lower", "extended"))
        self._finish_step(1)

        state = self.state()
        branch = self.step_branch(2, state)
        parent = self.git("rev-parse", branch).stdout.strip()
        tree = self.git("show", "-s", "--format=%T", parent).stdout.strip()
        recorded = self.git(
            "commit-tree", tree, "-p", parent, "-m", "recorded step head"
        ).stdout.strip()
        extended = self.git(
            "commit-tree", tree, "-p", recorded, "-m", "extended step head"
        ).stdout.strip()
        self._finish_step(2, head_commit=recorded)

        state = self.state()
        original_push = copy.deepcopy(state["steps"][1]["receipts"]["push"])
        url = original_push["pr_url"]
        self.fake_refs[branch] = extended
        self.fake_prs[url]["head"]["sha"] = extended

        directive = self.next_json()
        self.assertEqual((directive["do"], directive["step"]), ("merge-step", 1))
        self.run_ctl(
            "done", "merge-step", "--step", "1", "--merge-commit", "a" * 40
        )

        # The full live range now carries the authorised publisher committer in
        # both the local and GitHub views; topology alone supplied neither.
        self.env["FAKE_GIT_MODE"] = "publisher-committer"
        self.env["FAKE_GH_MODE"] = "publisher-committer"
        try:
            self.run_ctl(
                "done",
                "merge-step",
                "--step",
                "2",
                "--merge-commit",
                "b" * 40,
            )
        finally:
            self.env.pop("FAKE_GIT_MODE", None)
            self.env.pop("FAKE_GH_MODE", None)

        finished = self.state()
        self.assertEqual(finished["steps"][1]["receipts"]["push"], original_push)
        effective = finished["integrate"]["merges"]["2"]["effective_push"]
        self.assertTrue(effective["repaired"])
        self.assertEqual(effective["head"], extended)
        self.assertEqual(effective["verified_commits"], [extended])
        self.assertEqual(effective["github_verified"], [extended])
        identity = effective["attribution"]["commits"][0]
        self.assertEqual(identity["login"], "shoggoth-wildcat")
        self.assertEqual(identity["committer"]["login"], "laurenceday")
        self.assertNotIn("@", json.dumps(effective["attribution"]))


def run_elenchus_report(argv):
    """Run this focused module and write through the suite's secure reporter."""
    if len(argv) != 2 or argv[0] != "--elenchus-report":
        raise SystemExit(
            "test_step_branch_extensions.py accepts exactly one "
            "--elenchus-report PATH"
        )

    from run_tests import parse_arguments, result_payload, write_report

    _arguments, target = parse_arguments(argv)
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    try:
        write_report(target, result_payload(result))
    except OSError:
        print(
            "test_step_branch_extensions.py: report write failed",
            file=sys.stderr,
        )
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--elenchus-report" in arguments:
        raise SystemExit(run_elenchus_report(arguments))
    unittest.main()
