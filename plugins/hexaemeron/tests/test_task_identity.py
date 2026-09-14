"""The task identity a delegation is named for, and the reader that checks one.

Issue 363: a Mason continued under a handle minted for another issue kept that
issue's name. The controller now derives a `fiat-task-identity/v1` object and a
`fiat-<task>-<phase>-<role>` handle from state alone, and reads an observed
handle as hostile argv. Nothing calls either yet; these cases hold the grammar,
the determinism and the refusal shape before `next` carries them.
"""

import json
import os
import socket
import subprocess
import sys
import unittest

# `run_tests.py` discovers from this directory and puts it on the path; a reader
# running this module on its own does not get that, and the shared harness lives
# next door rather than in a package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hexctl_harness import HEXCTL, hexctl_module

TOPIC = "Bind delegated task identity to step and role"
TOPIC_SLUG = "bind-delegated-task-identity-to-step-and-role"
LONG_TOPIC = (
    "A topic whose slug runs well past the forty-eight character branch limit "
    "and keeps going"
)


def state_with_task(task, topic=TOPIC):
    """A controller state carrying only what the derivation is allowed to read."""
    return {
        "topic": topic,
        "receipts": {
            "run_anchor": {
                "schema": "fiat-run-anchor/v1",
                "task": task,
            }
        },
    }


def issue_state(number=320):
    return state_with_task({"kind": "github-issue", "number": number})


def topic_only_state(topic=TOPIC):
    return state_with_task({"kind": "none"}, topic)


def external_state():
    return state_with_task({"kind": "external", "sha256": "ab" * 32})


class TaskIdentityGrammarTests(unittest.TestCase):
    """`fiat-<task>-<phase>-<role>`, with `<task>` from the anchor or the topic."""

    def setUp(self):
        self.hexctl = hexctl_module()

    def test_issue_backed_run_names_the_issue_step_and_role(self):
        identity = self.hexctl.task_identity(issue_state(320), "mason", step=2)
        self.assertEqual(
            identity,
            {
                "schema": "fiat-task-identity/v1",
                "handle": "fiat-320-step-2-mason",
                "task": "320",
                "step": 2,
                "round": None,
                "role": "mason",
            },
        )

    def test_study_phase_is_named_study(self):
        identity = self.hexctl.task_identity(issue_state(320), "surveyor")
        self.assertEqual(identity["handle"], "fiat-320-study-surveyor")
        self.assertIsNone(identity["step"])
        self.assertIsNone(identity["round"])

    def test_step_phase_carries_the_step_number(self):
        for step in (1, 2, 3, 12):
            identity = self.hexctl.task_identity(issue_state(), "mason", step=step)
            self.assertEqual(identity["handle"], f"fiat-320-step-{step}-mason")
            self.assertEqual(identity["step"], step)

    def test_all_four_roles_are_distinct_in_the_handle(self):
        handles = {
            role: self.hexctl.task_identity(issue_state(), role, step=1)["handle"]
            for role in ("surveyor", "mason", "warden", "scribe")
        }
        self.assertEqual(
            handles,
            {
                "surveyor": "fiat-320-step-1-surveyor",
                "mason": "fiat-320-step-1-mason",
                "warden": "fiat-320-step-1-warden",
                "scribe": "fiat-320-step-1-scribe",
            },
        )
        self.assertEqual(len(set(handles.values())), 4)

    def test_another_issue_yields_another_handle(self):
        one = self.hexctl.task_identity(issue_state(318), "warden", step=2)
        other = self.hexctl.task_identity(issue_state(363), "warden", step=2)
        self.assertEqual(one["handle"], "fiat-318-step-2-warden")
        self.assertEqual(other["handle"], "fiat-363-step-2-warden")
        self.assertNotEqual(one["handle"], other["handle"])

    def test_role_outside_the_four_agents_is_refused(self):
        with self.assertRaises(ValueError):
            self.hexctl.task_identity(issue_state(), "controller", step=1)

    def test_step_and_round_must_be_positive_integers(self):
        for bad_step in (0, -1, "2", 2.0, True):
            with self.assertRaises(ValueError):
                self.hexctl.task_identity(issue_state(), "mason", step=bad_step)
        for bad_round in (0, "1", 1.0, False):
            with self.assertRaises(ValueError):
                self.hexctl.task_identity(
                    issue_state(), "warden", step=1, round=bad_round
                )


class TopicOnlyRunTests(unittest.TestCase):
    """A run with no task issue is named for its topic slug, never a number."""

    def setUp(self):
        self.hexctl = hexctl_module()

    def test_none_anchor_uses_the_topic_slug(self):
        identity = self.hexctl.task_identity(topic_only_state(), "mason", step=1)
        self.assertEqual(identity["task"], TOPIC_SLUG)
        self.assertEqual(identity["handle"], f"fiat-{TOPIC_SLUG}-step-1-mason")

    def test_external_anchor_uses_the_topic_slug(self):
        identity = self.hexctl.task_identity(external_state(), "surveyor")
        self.assertEqual(identity["task"], TOPIC_SLUG)
        self.assertEqual(identity["handle"], f"fiat-{TOPIC_SLUG}-study-surveyor")

    def test_topic_slug_is_bounded_at_forty_eight_characters(self):
        identity = self.hexctl.task_identity(
            topic_only_state(LONG_TOPIC), "scribe", step=3
        )
        self.assertEqual(identity["task"], self.hexctl.slug(LONG_TOPIC, 48))
        self.assertLessEqual(len(identity["task"]), 48)
        self.assertFalse(identity["task"].startswith("-"))
        self.assertFalse(identity["task"].endswith("-"))

    def test_topic_only_run_never_fabricates_an_issue_number(self):
        for state in (topic_only_state(), external_state(), {"topic": TOPIC}):
            identity = self.hexctl.task_identity(state, "warden", step=2, round=1)
            self.assertFalse(identity["task"].isdigit(), identity)
            self.assertNotIn("number", identity)
            segments = identity["handle"].split("-")
            self.assertEqual(segments[0], "fiat")
            self.assertFalse(any(segment.isdigit() for segment in segments[1:-3]))

    def test_anchor_number_must_be_a_positive_integer_to_count(self):
        for number in ("320", 0, -5, True, None):
            state = state_with_task({"kind": "github-issue", "number": number})
            identity = self.hexctl.task_identity(state, "mason", step=1)
            self.assertEqual(identity["task"], TOPIC_SLUG, number)

    def test_empty_topic_falls_back_the_way_the_run_branch_does(self):
        identity = self.hexctl.task_identity(topic_only_state("***"), "mason", step=1)
        self.assertEqual(identity["task"], "run")
        self.assertEqual(identity["handle"], "fiat-run-step-1-mason")

    def test_a_digits_only_topic_cannot_take_an_issue_handle(self):
        # Bare, a slug of digits is the `<task>` an issue-backed run with that
        # number derives, so that issue's handle would pass this run's check.
        issue = self.hexctl.task_identity(
            issue_state(363), "warden", step=1, round=1
        )
        external = {"kind": "external", "sha256": "ab" * 32}
        for state in (
            topic_only_state("363"),
            topic_only_state("#363"),
            state_with_task(external, "363"),
            {"topic": "363"},
        ):
            identity = self.hexctl.task_identity(state, "warden", step=1, round=1)
            self.assertEqual(identity["task"], "topic-363", state)
            self.assertEqual(identity["handle"], "fiat-topic-363-step-1-warden")
            self.assertNotEqual(identity["handle"], issue["handle"])
            refusal = self.hexctl.task_handle_refusal(
                issue["handle"], identity["handle"]
            )
            self.assertIsNotNone(refusal)
            self.assertIn("(equality)", refusal)
        mixed = self.hexctl.task_identity(
            topic_only_state("363 follow-up"), "warden", step=1
        )
        self.assertEqual(mixed["task"], "363-follow-up")


class RoundContinuityTests(unittest.TestCase):
    """Round lives in the object and stays out of the handle."""

    def setUp(self):
        self.hexctl = hexctl_module()

    def test_rounds_of_one_step_share_a_handle(self):
        first = self.hexctl.task_identity(issue_state(), "warden", step=2, round=1)
        third = self.hexctl.task_identity(issue_state(), "warden", step=2, round=3)
        self.assertEqual(first["handle"], "fiat-320-step-2-warden")
        self.assertEqual(first["handle"], third["handle"])
        self.assertEqual((first["round"], third["round"]), (1, 3))
        self.assertNotEqual(first, third)

    def test_round_number_does_not_appear_in_the_handle(self):
        identity = self.hexctl.task_identity(issue_state(), "warden", step=2, round=7)
        self.assertNotIn("7", identity["handle"])
        self.assertNotIn("round", identity["handle"])

    def test_a_step_change_changes_the_handle(self):
        step_two = self.hexctl.task_identity(issue_state(), "warden", step=2, round=1)
        step_three = self.hexctl.task_identity(issue_state(), "warden", step=3, round=1)
        self.assertNotEqual(step_two["handle"], step_three["handle"])


DERIVE_SCRIPT = """
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("hexctl_under_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
states = json.loads(sys.argv[2])
out = []
for state in states:
    out.append(module.task_identity(state, "surveyor"))
    for step in (1, 2):
        for role in ("mason", "scribe"):
            out.append(module.task_identity(state, role, step=step))
        for round_number in (1, 2):
            out.append(module.task_identity(state, "warden", step=step, round=round_number))
sys.stdout.write(module.canonical(out))
"""


class DeterminismTests(unittest.TestCase):
    """Identical state gives identical bytes, from any process, anywhere."""

    def setUp(self):
        self.hexctl = hexctl_module()
        self.states = [issue_state(320), topic_only_state(), external_state()]

    def derive_in_a_fresh_process(self, cwd):
        completed = subprocess.run(
            [sys.executable, "-c", DERIVE_SCRIPT, HEXCTL, json.dumps(self.states)],
            cwd=cwd,
            capture_output=True,
            check=True,
        )
        return completed.stdout

    def test_two_processes_emit_identical_bytes(self):
        here = os.path.dirname(os.path.abspath(__file__))
        first = self.derive_in_a_fresh_process(here)
        second = self.derive_in_a_fresh_process(os.path.dirname(here))
        self.assertEqual(first, second)
        self.assertGreater(len(first), 0)
        decoded = json.loads(first)
        # One study identity, two roles on two steps, two Warden rounds on two steps.
        self.assertEqual(len(decoded), 3 * 9)
        self.assertEqual(decoded[0]["handle"], "fiat-320-study-surveyor")

    def test_output_carries_no_clock_pid_hostname_or_path(self):
        out = self.derive_in_a_fresh_process(os.getcwd())
        text = out.decode("utf-8")
        self.assertNotIn(str(os.getpid()), text)
        self.assertNotIn(socket.gethostname(), text)
        self.assertNotIn(os.getcwd(), text)
        self.assertNotIn(os.path.dirname(os.path.abspath(HEXCTL)), text)
        for identity in json.loads(out):
            self.assertEqual(
                sorted(identity),
                ["handle", "role", "round", "schema", "step", "task"],
            )
            self.assertEqual(identity["schema"], "fiat-task-identity/v1")
            # The schema's version separator is the only slash allowed anywhere.
            for key in ("handle", "task", "role"):
                self.assertNotIn("/", identity[key])
                self.assertNotIn(os.sep, identity[key])
            for value in identity.values():
                if isinstance(value, int):
                    self.assertLess(value, 1_000_000, "a clock or pid would be larger")

    def test_derivation_reads_only_topic_and_anchor(self):
        extra = issue_state(320)
        extra["base"] = "0" * 40
        extra["current_step"] = 2
        extra["steps"] = [{"n": 2, "phase": "implement"}]
        extra["receipts"]["task_issue"] = "https://github.com/example/repo/issues/999"
        self.assertEqual(
            self.hexctl.task_identity(extra, "mason", step=2),
            self.hexctl.task_identity(issue_state(320), "mason", step=2),
        )


class ObservedHandleRefusalTests(unittest.TestCase):
    """The observed handle is host argv: bounded, character-checked, then compared."""

    EXPECTED = "fiat-320-step-2-mason"

    def setUp(self):
        self.hexctl = hexctl_module()

    def refusal(self, observed):
        return self.hexctl.task_handle_refusal(observed, self.EXPECTED)

    def test_the_expected_handle_is_accepted(self):
        self.assertIsNone(self.refusal(self.EXPECTED))

    def test_oversized_handle_is_refused_on_length_without_echo(self):
        observed = "a" * 201
        message = self.refusal(observed)
        self.assertIn("(length)", message)
        self.assertIn("201 bytes", message)
        self.assertNotIn(observed, message)
        self.assertNotIn("aaaa", message)
        self.assertLess(len(message), 200)

    def test_length_is_measured_in_bytes_not_characters(self):
        observed = "é" * 101
        self.assertEqual(len(observed), 101)
        message = self.refusal(observed)
        self.assertIn("(length)", message)
        self.assertIn("202 bytes", message)
        self.assertNotIn("é", message)

    def test_exactly_two_hundred_bytes_reaches_the_equality_check(self):
        observed = "b" * 200
        message = self.refusal(observed)
        self.assertIn("(equality)", message)

    def test_control_bearing_handle_is_refused_on_character_without_echo(self):
        for control in ("\x00", "\x1b", "\x7f", "\x85"):
            observed = f"fiat-320-step-2-mason{control}[31mpayload"
            message = self.refusal(observed)
            self.assertIn("(character)", message, repr(control))
            self.assertIn(f"U+{ord(control):04X}", message)
            self.assertIn("at index 21", message)
            self.assertNotIn("payload", message)
            self.assertNotIn(control, message)

    def test_whitespace_bearing_handle_is_refused_on_character(self):
        for space in (" ", "\t", "\n", "\r", " ", " "):
            for observed in (
                f"{self.EXPECTED}{space}",
                f"{space}{self.EXPECTED}",
                f"fiat-320{space}step-2-mason",
            ):
                message = self.refusal(observed)
                self.assertIn("(character)", message, repr(observed))
                self.assertIn(f"U+{ord(space):04X}", message)
                self.assertNotIn(self.EXPECTED, message)

    def test_lone_surrogate_is_refused_on_character(self):
        message = self.refusal("fiat-320-step-2-mason\udcff")
        self.assertIn("(character)", message)
        self.assertIn("U+DCFF", message)

    def test_every_lone_surrogate_is_refused_rather_than_raised(self):
        # POSIX argv decoding yields only U+DC80..U+DCFF, but a JSON escape or a
        # direct caller can hand over any lone surrogate.
        for code in (0xD800, 0xDBFF, 0xDC00, 0xDC7F, 0xDC80, 0xDCFF, 0xDD00, 0xDFFF):
            observed = f"{self.EXPECTED}{chr(code)}"
            try:
                message = self.refusal(observed)
            except UnicodeError as error:
                self.fail(f"U+{code:04X} raised {type(error).__name__}")
            self.assertIn("(character)", message, hex(code))
            self.assertIn(f"U+{code:04X}", message)
            self.assertIn("at index 21", message)
            self.assertNotIn(chr(code), message)
            self.assertNotIn(self.EXPECTED, message)

    def test_non_printable_characters_are_refused_on_character_without_echo(self):
        # Each renders as nothing, reorders what follows or has no agreed glyph,
        # so an equality diagnostic echoing one could print two handles that look
        # identical.
        for code in (0x00AD, 0x200B, 0x200E, 0x202E, 0x2066, 0xFEFF, 0xE000):
            observed = f"{self.EXPECTED}{chr(code)}"
            message = self.refusal(observed)
            self.assertIn("(character)", message, hex(code))
            self.assertIn(f"U+{code:04X}", message)
            self.assertNotIn(chr(code), message)
            self.assertNotIn(self.EXPECTED, message)

    def test_empty_and_non_string_observed_are_refused_on_length(self):
        for observed in ("", None, 320, b"fiat-320-step-2-mason", ["fiat"]):
            message = self.refusal(observed)
            self.assertIn("(length)", message, repr(observed))

    def test_stale_handle_from_another_issue_is_refused_on_equality(self):
        message = self.refusal("issue318_step2")
        self.assertIn("(equality)", message)
        self.assertIn("expected fiat-320-step-2-mason", message)
        self.assertIn("observed issue318_step2", message)

    def test_equality_is_exact_not_prefix_case_or_pattern(self):
        for observed in (
            "fiat-320-step-2-masonx",
            "fiat-320-step-2-maso",
            "FIAT-320-step-2-mason",
            "fiat-320-step-2-warden",
            "fiat-320-step-3-mason",
            "fiat-320-study-mason",
            "fiat-3200-step-2-mason",
            "fiat-.*-step-2-mason",
        ):
            message = self.refusal(observed)
            self.assertIn("(equality)", message, observed)
            self.assertIn(f"observed {observed}", message)

    def test_diagnostic_length_is_bounded_by_the_two_handles(self):
        observed = "c" * 200
        message = self.refusal(observed)
        self.assertLessEqual(
            len(message), len(observed) + len(self.EXPECTED) + 64
        )
        self.assertNotIn("\n", message)

    def test_checks_run_in_order_length_then_character_then_equality(self):
        # Oversized and control-bearing: length wins, so the control byte is never read.
        message = self.refusal("\x00" + "a" * 200)
        self.assertIn("(length)", message)
        self.assertNotIn("U+0000", message)
        # Control-bearing and unequal: character wins, so nothing is echoed.
        message = self.refusal("issue318\x00step2")
        self.assertIn("(character)", message)
        self.assertNotIn("issue318", message)

    def test_derived_handle_passes_its_own_reader(self):
        for state in (issue_state(320), topic_only_state(LONG_TOPIC)):
            for role in ("surveyor", "mason", "warden", "scribe"):
                identity = self.hexctl.task_identity(state, role, step=2, round=1)
                handle = identity["handle"]
                self.assertLessEqual(len(handle.encode("utf-8")), 200)
                self.assertIsNone(self.hexctl.task_handle_refusal(handle, handle))


if __name__ == "__main__":
    unittest.main()
