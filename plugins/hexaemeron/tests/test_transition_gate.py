"""The pure transition gate: one grant or one stable refusal per rule.

Every rule has one granted and one refused case. The unknown-value refusals of
hostile specimen 3 run here at the pure level, with no controller and no run on
disk. The purity test reads the module's AST; the behavioural twin runs every
granted case with the file, process and socket entry points made to raise.
"""

from __future__ import annotations

import ast
import builtins
import copy
import importlib.util
import os
import re
import socket
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
SOURCE = PLUGIN / "skills/fiat/scripts/transition_gate.py"
CONTROLLER = PLUGIN / "skills/fiat/scripts/hexctl.py"
SKILL = PLUGIN / "skills/fiat/SKILL.md"
REFERENCE = PLUGIN / "skills/fiat/references/transition-gate.md"

spec = importlib.util.spec_from_file_location("transition_gate_under_test", SOURCE)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

STATE = "b0" * 32
TAIL = "de" * 32
COUNT = 43
GRANT_FIELDS = {
    "schema",
    "promise",
    "consequence",
    "transition",
    "directive",
    "state_sha256",
    "ledger_tail",
    "ledger_count",
    "handler",
    "subcommand",
    "command",
}
REFUSAL_FIELDS = {
    "schema",
    "promise",
    "consequence",
    "blocked_transition",
    "code",
    "recovery",
}
EXHAUSTED_HALT = {"do": "halted", "step": 2, "covers": "audit-verdict"}
ORDINARY_HALT = {"do": "halted", "step": 2, "covers": "implement"}


def at(do: str, **extra) -> dict:
    return {"do": do, "step": 2, **extra}


def call(key, directive, command=None, evidence=None, **preimage):
    arguments = {
        "state_sha256": STATE,
        "ledger_tail": TAIL,
        "ledger_count": COUNT,
        "directive": directive,
        "handler": key[0],
        "subcommand": key[1],
        "command": {} if command is None else command,
        "evidence": {} if evidence is None else evidence,
    }
    if isinstance(directive, dict) and directive.get("do") == "absent":
        arguments.update(state_sha256=None, ledger_tail="genesis", ledger_count=0)
    arguments.update(preimage)
    return gate.evaluate(**arguments)


PUSHED = {"tail_event": "done:push"}
REQUEST = {"request": ".hexaemeron/request.json"}
ROUND = {
    "findings": 3,
    "audit_filter": "sapheneia:sapheneia",
    "phylax_exit": 0,
    "ephoros_exit": 0,
    "hypomnema_exit": 0,
}
SYNC = {
    "commit": "a" * 40,
    "base_commit": "b" * 40,
    "revalidation": ".hexaemeron/integration-revalidation.json",
    "acknowledge_sync_paths": ["docs/a.md", "docs/b.md"],
}

# key -> (granted directive, command, evidence), (refused directive, command,
# evidence, code)
CASES = {
    ("cmd_init", None): (
        ({"do": "absent"}, {"topic": "a gate", "base": "main"}, {}),
        (at("study"), {"topic": "a gate"}, {}, "directive-not-authorised"),
    ),
    ("cmd_observe", None): (
        (at("implement"), {"capture_status": "captured", "redaction_status": "passed"}, {}),
        (at("implement"), {"redaction_status": "passed"}, {}, "command-field-missing"),
    ),
    ("cmd_record", None): (
        (ORDINARY_HALT, {"key": "halt_note", "value": "waiting"}, {}),
        ({"do": "absent"}, {"key": "k", "value": "v"}, {}, "directive-not-authorised"),
    ),
    ("cmd_config", "set"): (
        (at("implement"), {"path": "audit.log_path", "value": "audit/rounds/x.md"}, {}),
        (at("implement"), {"path": "audit.max_rounds", "value": "16"}, {}, "config-path-immutable"),
    ),
    ("cmd_amend_study", None): (
        (at("implement"), {"artifact": "candidate.md"}, {"recovery": "amendment"}),
        (at("study"), {"artifact": "candidate.md"}, {}, "directive-not-authorised"),
    ),
    ("cmd_amend_runbook", None): (
        (at("blocked"), {"artifact": "candidate.md"}, {}),
        (at("blocked"), {"artifact": "candidate.md"}, {"recovery": "version-resolution"}, "recovery-pending"),
    ),
    ("cmd_done", "study"): (
        ({"do": "study"}, {"artifact": "study.md", "skills": "protasis"}, {}),
        ({"do": "runbook"}, {"artifact": "study.md"}, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "runbook"): (
        ({"do": "runbook"}, {"artifact": "runbook.md", "steps_file": "steps.json"}, {}),
        ({"do": "runbook"}, {"artifact": "runbook.md", "no_further_leads": True}, {}, "command-field-unknown"),
    ),
    ("cmd_done", "inoculate"): (
        (at("inoculate"), {}, {"recovery": "no-known-inoculation"}),
        (at("inoculate"), {}, {"recovery": "amendment"}, "recovery-pending"),
    ),
    ("cmd_done", "implement"): (
        (at("implement"), {"branch": "fiat/x-step-2", "commit": "a" * 40, "tests": "45 passed"}, {}),
        (at("run-exit"), {"branch": "fiat/x-step-2"}, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "audit"): (
        (at("audit-verdict"), {"no_further_leads": True, "reason": "user accepted"}, {}),
        (at("audit-verdict"), {"no_further_leads": True}, {}, "audit-close-needs-no-further-leads"),
    ),
    ("cmd_done", "prose"): (
        (at("prose"), {"files": 3, "skills": "imprimatur,vulgate"}, {}),
        (at("push"), {"files": 3}, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "push"): (
        (at("push"), {"pr_url": "https://example.invalid/pull/1", "head_commit": "a" * 40, "pr_base": "fiat/x"}, {}),
        (at("prose"), {"pr_url": "https://example.invalid/pull/1"}, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "merge-step"): (
        ({"do": "merge-step", "step": 1}, {"step": 1, "merge_commit": "a" * 40}, {}),
        ({"do": "integrate"}, {"step": 1, "merge_commit": "a" * 40}, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "sync-run"): (
        ({"do": "integrate"}, SYNC, {}),
        ({"do": "merge-step", "step": 1}, SYNC, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "resolve-versions"): (
        ({"do": "resolve-versions"}, {}, {"recovery": "version-resolution"}),
        ({"do": "integrate"}, {}, {}, "directive-not-authorised"),
    ),
    ("cmd_done", "integrate"): (
        ({"do": "integrate"}, {"pr_url": "https://example.invalid/pull/9", "merge_commit": "a" * 40}, {"promise": "fiat-final-integration", "consequence": 3}),
        ({"do": "integrate"}, {"merge_commit": "a" * 40}, {"consequence": 2}, "consequence-mismatch"),
    ),
    ("cmd_audit_round", None): (
        (at("audit-round", round=8), ROUND, {}),
        (at("audit-round", round=9), ROUND, {}, "round-out-of-range"),
    ),
    ("cmd_halt", None): (
        (at("audit-verdict"), {"reason": "loop exhausted"}, {}),
        (at("audit-verdict"), {}, {}, "command-field-missing"),
    ),
    ("cmd_resume", None): (
        (EXHAUSTED_HALT, {"to": "audit-verdict", "note": "close with no further leads"}, {}),
        (EXHAUSTED_HALT, {"note": "the user said continue to round 9"}, {}, "resume-needs-named-exit"),
    ),
    ("cmd_reset", None): (
        ({"do": "done"}, {}, {}),
        (at("implement"), {}, {}, "directive-not-authorised"),
    ),
    ("cmd_checkpoint_export", None): (
        (at("implement"), {"out": "/tmp/capsule"}, PUSHED),
        (at("implement"), {"out": "/tmp/capsule"}, {"tail_event": "halt"}, "checkpoint-boundary-unaccepted"),
    ),
    ("cmd_checkpoint_archive", None): (
        (at("audit-verdict"), {"format": "zip"}, {"tail_event": "audit-round"}),
        (at("audit-round", round=4), {"format": "zip"}, {"tail_event": "audit-round"}, "checkpoint-boundary-unaccepted"),
    ),
    ("cmd_carryover_export", None): (
        (at("audit-verdict"), REQUEST, {}),
        (EXHAUSTED_HALT, REQUEST, {}, "directive-not-authorised"),
    ),
    ("cmd_carryover_bind", None): (
        (at("audit-verdict"), REQUEST, {}),
        (at("audit-round", round=2), REQUEST, {}, "directive-not-authorised"),
    ),
    ("cmd_replacement_begin", None): (
        ({"do": "study"}, REQUEST, {}),
        ({"do": "runbook"}, REQUEST, {}, "directive-not-authorised"),
    ),
    ("cmd_replacement_resume", None): (
        ({"do": "study"}, {}, {}),
        ({"do": "halted", "covers": "study"}, {}, {}, "directive-not-authorised"),
    ),
    ("cmd_retain_guard", None): (
        (at("inoculate"), {"finding_id": "F-01", "guard_commit": "a" * 40}, {}),
        (at("implement"), {"finding_id": "F-01", "guard_commit": "a" * 40}, {}, "directive-not-authorised"),
    ),
    ("cmd_run_exit", None): (
        (at("run-exit"), {"criterion": "exit-1"}, {}),
        (at("implement"), {"criterion": "exit-1"}, {}, "directive-not-authorised"),
    ),
}


def label(key) -> str:
    return "_".join(part.replace("-", "_") for part in key if part)


class GateCase(unittest.TestCase):
    def assert_grant(self, grant, key, directive, command):
        rule = gate.RULES[key]
        self.assertEqual(set(grant), GRANT_FIELDS)
        self.assertEqual(grant["schema"], "fiat-transition-grant/v1")
        self.assertEqual(grant["promise"], rule.promise)
        self.assertEqual(grant["consequence"], gate.PROMISES[rule.promise])
        self.assertEqual(grant["transition"], rule.transition)
        self.assertEqual(grant["directive"], directive)
        self.assertEqual((grant["handler"], grant["subcommand"]), key)
        self.assertEqual(grant["command"], command)
        self.assertLessEqual(len(gate.canonical(grant).encode()), 65_536)

    def assert_refusal(self, code, key, directive, command=None, evidence=None, **preimage):
        with self.assertRaises(gate.Refusal) as caught:
            call(key, directive, command, evidence, **preimage)
        report = caught.exception.report
        self.assertEqual(set(report), REFUSAL_FIELDS)
        self.assertEqual(report["schema"], "fiat-transition-refusal/v1")
        self.assertEqual(report["code"], code)
        self.assertEqual(report["recovery"], gate.REFUSALS[code])
        rule = gate.RULES.get(key) if isinstance(key[0], str) else None
        if rule is None:
            self.assertEqual(report["promise"], "fiat-receipted-delivery")
            self.assertEqual(report["blocked_transition"], "unmapped")
        else:
            self.assertEqual(report["promise"], rule.promise)
            self.assertEqual(report["blocked_transition"], rule.transition)
        self.assertEqual(report["consequence"], gate.PROMISES[report["promise"]])
        return report


class RuleTests(GateCase):
    """One granted and one refused case per rule, generated from CASES."""


def _granted(key):
    def test(self):
        directive, command, evidence = CASES[key][0]
        grant = call(key, directive, command, evidence)
        self.assert_grant(grant, key, directive, command)
        if directive["do"] == "absent":
            self.assertEqual(
                (grant["state_sha256"], grant["ledger_tail"], grant["ledger_count"]),
                (None, "genesis", 0),
            )
        else:
            self.assertEqual(
                (grant["state_sha256"], grant["ledger_tail"], grant["ledger_count"]),
                (STATE, TAIL, COUNT),
            )

    return test


def _refused(key):
    def test(self):
        directive, command, evidence, code = CASES[key][1]
        self.assert_refusal(code, key, directive, command, evidence)

    return test


for _key in CASES:
    setattr(RuleTests, f"test_{label(_key)}_is_granted", _granted(_key))
    setattr(RuleTests, f"test_{label(_key)}_is_refused", _refused(_key))


class TableTests(GateCase):
    def mutating(self) -> set:
        tree = ast.parse(CONTROLLER.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "MUTATING"
                for target in node.targets
            ):
                return {
                    item.value
                    for item in ast.walk(node.value)
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                }
        self.fail("hexctl.py declares no MUTATING set")

    def test_every_mutating_handler_has_a_rule_and_no_other_handler_does(self):
        names = self.mutating()
        self.assertEqual(len(names), 19)
        self.assertEqual({handler for handler, _ in gate.RULES}, names)

    def test_every_rule_has_one_granted_and_one_refused_case(self):
        self.assertEqual(set(CASES), set(gate.RULES))

    def test_start_audit_loop_has_no_rule_yet(self):
        for key in (("cmd_start_audit_loop", None), ("start-audit-loop", None)):
            self.assert_refusal("command-unknown", key, EXHAUSTED_HALT)
            self.assert_refusal("command-unknown", key, at("audit-verdict"))

    def test_every_rule_names_a_promise_fiat_declares_with_its_consequence(self):
        declared = {}
        current = None
        for line in SKILL.read_text(encoding="utf-8").splitlines():
            heading = re.fullmatch(r"### (fiat-[a-z0-9-]+)", line)
            if heading:
                current = heading.group(1)
            level = re.fullmatch(r"- Consequence: (\d)", line)
            if level and current:
                declared[current] = int(level.group(1))
        for key, rule in gate.RULES.items():
            self.assertIn(rule.promise, declared, key)
            self.assertEqual(gate.PROMISES[rule.promise], declared[rule.promise], key)
        self.assertEqual({rule.promise for rule in gate.RULES.values()}, set(gate.PROMISES))
        self.assertLessEqual(set(gate.PROMISES.values()), gate.CONSEQUENCE_LEVELS)

    def test_table_is_internally_closed(self):
        for key, rule in gate.RULES.items():
            self.assertLessEqual(rule.directives, gate.DIRECTIVES, key)
            self.assertLessEqual(rule.required, rule.fields, key)
            self.assertTrue(rule.check is None or rule.check in gate.CHECKS, key)
        self.assertEqual(
            {rule.check for rule in gate.RULES.values()} - {None}, set(gate.CHECKS)
        )
        for owners in gate.RECOVERY_PATHS.values():
            self.assertLessEqual(owners, set(gate.RULES))
        self.assertEqual(
            len({rule.transition for rule in gate.RULES.values()}), len(gate.RULES)
        )

    def test_config_get_has_no_rule(self):
        self.assert_refusal("command-unknown", ("cmd_config", "get"), at("implement"), {"path": "audit"})

    def test_reference_states_both_schemas_every_code_and_the_limit(self):
        text = REFERENCE.read_text(encoding="utf-8")
        listed = set(re.findall(r"^\| `([a-z-]+)` \| ", text.split("## Stable refusal codes")[1], re.M))
        self.assertEqual(listed, set(gate.REFUSALS))
        for schema in (gate.GRANT_SCHEMA, gate.REFUSAL_SCHEMA):
            self.assertIn(schema, text)
        for field in GRANT_FIELDS | REFUSAL_FIELDS:
            self.assertIn(f"`{field}`", text)
        for key, rule in gate.RULES.items():
            subcommand = f"`{key[1]}` " if key[1] else ""
            row = f"| `{key[0]}` | {subcommand}| `{rule.promise}` | `{rule.transition}` |"
            self.assertTrue(row in text, row)
        self.assertIn("## Same-account limit", text)
        self.assertIn("It is not privilege\nisolation", text)


class ConfigAllowlistTests(GateCase):
    KEY = ("cmd_config", "set")

    def test_adr_047_paths_are_granted(self):
        for path in ("audit.log_path", "git", "git.base", "git.remote.name"):
            with self.subTest(path=path):
                command = {"path": path, "value": "x"}
                self.assert_grant(call(self.KEY, EXHAUSTED_HALT, command), self.KEY, EXHAUSTED_HALT, command)

    def test_the_622_widening_refuses_at_the_exhausted_halt_and_the_verdict(self):
        for directive in (EXHAUSTED_HALT, at("audit-verdict")):
            for path, value in (("audit.max_rounds", "16"), ("audit", '{"max_rounds": 16}')):
                with self.subTest(directive=directive["do"], path=path):
                    report = self.assert_refusal(
                        "config-path-immutable", self.KEY, directive, {"path": path, "value": value}
                    )
                    self.assertEqual(report["consequence"], 2)
                    self.assertEqual(report["blocked_transition"], "config-set")

    def test_every_other_path_refuses(self):
        for path in ("", "gitx", "Git", "audit.log_path.x", "audit.log_pat", "skills", "solidity", " git", "git\n.base"):
            with self.subTest(path=path):
                self.assert_refusal("config-path-immutable", self.KEY, at("implement"), {"path": path, "value": "x"})

    def test_a_path_that_is_not_a_string_refuses(self):
        for path in (7, True, ["git"]):
            with self.subTest(path=path):
                self.assert_refusal("command-value-malformed", self.KEY, at("implement"), {"path": path, "value": "x"})


class TypedResumeTests(GateCase):
    KEY = ("cmd_resume", None)

    def test_resume_naming_no_exit_refuses_at_an_exhausted_halt(self):
        for command in ({}, {"note": "resume as round 9"}, {"to": None}):
            with self.subTest(command=command):
                report = self.assert_refusal("resume-needs-named-exit", self.KEY, EXHAUSTED_HALT, command)
                self.assertEqual(report["promise"], "fiat-receipted-delivery")
                self.assertEqual(report["consequence"], 2)
                self.assertEqual(report["blocked_transition"], "clear-halt")
                self.assertIn("resume --to audit-verdict", report["recovery"])

    def test_resume_naming_the_audit_verdict_exit_is_granted(self):
        command = {"to": "audit-verdict"}
        grant = call(self.KEY, EXHAUSTED_HALT, command)
        self.assert_grant(grant, self.KEY, EXHAUSTED_HALT, command)
        self.assertEqual(grant["transition"], "clear-halt")

    def test_resume_naming_no_exit_still_clears_an_ordinary_halt(self):
        for covers in sorted(gate.ACTIVE - {"halted", "audit-verdict"}):
            with self.subTest(covers=covers):
                directive = {"do": "halted", "covers": covers}
                self.assert_grant(call(self.KEY, directive, {"note": "back"}), self.KEY, directive, {"note": "back"})

    def test_the_named_exit_must_be_the_one_the_halt_covers(self):
        self.assert_refusal("resume-exit-mismatch", self.KEY, ORDINARY_HALT, {"to": "audit-verdict"})

    def test_an_unknown_exit_refuses(self):
        for exit_named in ("audit-round", "round-9", "start-audit-loop", "", 9, True):
            with self.subTest(exit_named=exit_named):
                self.assert_refusal("resume-exit-unknown", self.KEY, EXHAUSTED_HALT, {"to": exit_named})

    def test_resume_refuses_a_run_that_is_not_halted(self):
        self.assert_refusal("directive-not-authorised", self.KEY, at("audit-verdict"), {"to": "audit-verdict"})


class UnknownValueTests(GateCase):
    """Hostile specimen 3, at the pure level."""

    HALT = ("cmd_halt", None)
    REASON = {"reason": "stop"}

    def test_unknown_command_refuses(self):
        for key in (("cmd_status", None), ("cmd_done", "audit-round-9"), ("cmd_done", None),
                    ("cmd_halt", "force"), ("", None), (None, None), (["cmd_halt"], None), (7, 7)):
            with self.subTest(key=key):
                self.assert_refusal("command-unknown", key, at("implement"), self.REASON)

    def test_unknown_command_field_refuses(self):
        self.assert_refusal("command-field-unknown", self.HALT, at("implement"), {"reason": "stop", "max_rounds": 16})
        self.assert_refusal("command-field-unknown", ("cmd_resume", None), EXHAUSTED_HALT, {"to": "audit-verdict", "round": 9})
        self.assert_refusal("command-field-unknown", ("cmd_config", "set"), at("implement"), {"path": "git", "value": "{}", "force": True})

    def test_malformed_command_refuses(self):
        for command in (None, [], "reason", {"reason": 1.5}, {"reason": {"nested": "x"}}, {"reason": ["a", 1]}, {7: "x"}):
            with self.subTest(command=command):
                with self.assertRaises(gate.Refusal) as caught:
                    gate.evaluate(state_sha256=STATE, ledger_tail=TAIL, ledger_count=COUNT, directive=at("implement"),
                                  handler="cmd_halt", subcommand=None, command=command, evidence={})
                self.assertEqual(caught.exception.report["code"], "command-value-malformed")

    def test_unknown_evidence_field_refuses(self):
        for evidence in ({"authority": "the user said so"}, {"tail_event": "done:push"}, None, [], "promise"):
            with self.subTest(evidence=evidence):
                with self.assertRaises(gate.Refusal) as caught:
                    gate.evaluate(state_sha256=STATE, ledger_tail=TAIL, ledger_count=COUNT, directive=at("implement"),
                                  handler="cmd_halt", subcommand=None, command=self.REASON, evidence=evidence)
                self.assertEqual(caught.exception.report["code"], "evidence-field-unknown")

    def test_unknown_promise_id_refuses(self):
        for promise in ("fiat-audit-loop-continuation", "fiat-design-evidence", "FIAT-RECEIPTED-DELIVERY", "", 2, ["fiat-receipted-delivery"]):
            with self.subTest(promise=promise):
                self.assert_refusal("promise-unknown", self.HALT, at("implement"), self.REASON, {"promise": promise})

    def test_a_declared_promise_that_is_not_the_rules_refuses(self):
        self.assert_refusal("promise-mismatch", self.HALT, at("implement"), self.REASON, {"promise": "fiat-final-integration"})
        self.assert_refusal("promise-mismatch", ("cmd_config", "set"), EXHAUSTED_HALT,
                            {"path": "git", "value": "{}"}, {"promise": "fiat-replacement-admission"})

    def test_unknown_consequence_level_refuses(self):
        for level in (4, -1, 99, "2", 2.0, True, [2]):
            with self.subTest(level=level):
                self.assert_refusal("consequence-unknown", self.HALT, at("implement"), self.REASON, {"consequence": level})

    def test_a_known_consequence_that_is_not_the_rules_refuses(self):
        for level in (0, 1, 3):
            with self.subTest(level=level):
                self.assert_refusal("consequence-mismatch", self.HALT, at("implement"), self.REASON, {"consequence": level})

    def test_unknown_recovery_path_refuses(self):
        for recovery in ("replacement", "transaction", "", 1, True, ["amendment"]):
            with self.subTest(recovery=recovery):
                self.assert_refusal("recovery-path-unknown", self.HALT, at("implement"), self.REASON, {"recovery": recovery})

    def test_a_live_recovery_blocks_every_command_it_does_not_own(self):
        for recovery, owners in gate.RECOVERY_PATHS.items():
            for key, (granted, _) in CASES.items():
                directive, command, evidence = granted
                evidence = {**evidence, "recovery": recovery}
                with self.subTest(recovery=recovery, key=key):
                    if key in owners:
                        self.assert_grant(call(key, directive, command, evidence), key, directive, command)
                    else:
                        self.assert_refusal("recovery-pending", key, directive, command, evidence)

    def test_unknown_directive_shape_refuses(self):
        shapes = (
            None, [], "halted", {}, {"step": 2}, {"do": None}, {"do": 7}, {"do": ["implement"]},
            {"do": "implement", "loop": 2}, {"do": "implement", "reason": "x"},
            {"do": "implement", "step": 0}, {"do": "implement", "step": "2"}, {"do": "implement", "step": True},
            {"do": "implement", "round": 1}, {"do": "implement", "covers": "audit-verdict"},
            {"do": "audit-round"}, {"do": "audit-round", "round": "8"}, {"do": "audit-round", "round": True},
            {"do": "halted"},
        )
        for directive in shapes:
            with self.subTest(directive=directive):
                self.assert_refusal("directive-shape-unknown", self.HALT, directive, self.REASON)

    def test_unknown_directive_refuses(self):
        for directive in ({"do": "start-audit-loop"}, {"do": "round-9"}, {"do": "Implement"}, {"do": ""},
                          {"do": "halted", "covers": "halted"}, {"do": "halted", "covers": "absent"},
                          {"do": "halted", "covers": "round-9"}, {"do": "halted", "covers": None}):
            with self.subTest(directive=directive):
                self.assert_refusal("directive-unknown", self.HALT, directive, self.REASON)

    def test_no_ninth_round_is_representable(self):
        for number in (0, 9, 16, -1):
            with self.subTest(round=number):
                self.assert_refusal("round-out-of-range", ("cmd_audit_round", None), at("audit-round", round=number), ROUND)
        for number in range(1, 9):
            with self.subTest(round=number):
                call(("cmd_audit_round", None), at("audit-round", round=number), ROUND)

    def test_stale_or_malformed_preimage_refuses(self):
        preimages = (
            {"state_sha256": None}, {"state_sha256": "B0" * 32}, {"state_sha256": "b0" * 31}, {"state_sha256": "b0" * 32 + "\n"},
            {"state_sha256": 7}, {"ledger_tail": "genesis"}, {"ledger_tail": None}, {"ledger_tail": "de" * 33},
            {"ledger_count": 0}, {"ledger_count": -1}, {"ledger_count": True}, {"ledger_count": "43"}, {"ledger_count": 43.0},
        )
        for preimage in preimages:
            with self.subTest(preimage=preimage):
                self.assert_refusal("preimage-malformed", self.HALT, at("implement"), self.REASON, **preimage)

    def test_an_absent_run_carries_no_digest(self):
        key = ("cmd_init", None)
        for preimage in ({"state_sha256": STATE}, {"ledger_tail": TAIL}, {"ledger_count": 1}):
            with self.subTest(preimage=preimage):
                self.assert_refusal("preimage-malformed", key, {"do": "absent"}, {"topic": "x"}, **preimage)

    def test_every_stable_code_has_a_specimen(self):
        specimens = {code for _, (_, (_, _, _, code)) in CASES.items()}
        specimens |= {
            "command-unknown", "command-field-unknown", "command-value-malformed", "evidence-field-unknown",
            "promise-unknown", "promise-mismatch", "consequence-unknown", "recovery-path-unknown",
            "directive-shape-unknown", "directive-unknown", "preimage-malformed", "resume-exit-unknown",
            "resume-exit-mismatch", "grant-oversized",
        }
        self.assertEqual(specimens, set(gate.REFUSALS))


class CloseAuditTests(GateCase):
    KEY = ("cmd_done", "audit")

    def test_a_clean_last_round_closes_without_a_waiver(self):
        self.assert_grant(call(self.KEY, at("close-audit"), {"fixes_ref": "a" * 40}), self.KEY, at("close-audit"), {"fixes_ref": "a" * 40})

    def test_open_findings_need_the_waiver_and_its_reason(self):
        for directive in (at("audit-round", round=3), at("audit-verdict")):
            for command in ({}, {"reason": "accepted"}, {"no_further_leads": True, "reason": ""},
                            {"no_further_leads": False, "reason": "accepted"}, {"no_further_leads": "true", "reason": "accepted"}):
                with self.subTest(directive=directive["do"], command=command):
                    self.assert_refusal("audit-close-needs-no-further-leads", self.KEY, directive, command)
            granted = {"no_further_leads": True, "reason": "accepted by the maintainer"}
            self.assert_grant(call(self.KEY, directive, granted), self.KEY, directive, granted)


class CheckpointBoundaryTests(GateCase):
    def test_both_accepted_boundaries_and_no_other(self):
        for key, command in ((("cmd_checkpoint_export", None), {"out": "capsule"}), (("cmd_checkpoint_archive", None), {})):
            self.assert_grant(call(key, at("inoculate"), command, PUSHED), key, at("inoculate"), command)
            self.assert_grant(call(key, at("audit-verdict"), command, {"tail_event": "audit-round"}), key, at("audit-verdict"), command)
            for evidence in ({}, {"tail_event": None}, {"tail_event": "resume"}, {"tail_event": 7}):
                with self.subTest(key=key, evidence=evidence):
                    self.assert_refusal("checkpoint-boundary-unaccepted", key, at("audit-verdict"), command, evidence)
            self.assert_refusal("directive-not-authorised", key, EXHAUSTED_HALT, command, PUSHED)


class GrantBudgetTests(GateCase):
    def test_every_granted_case_is_within_the_budget(self):
        sizes = {
            key: len(gate.canonical(call(key, *granted)).encode())
            for key, (granted, _) in CASES.items()
        }
        self.assertEqual(gate.MAX_GRANT_BYTES, 65_536)
        self.assertLessEqual(max(sizes.values()), gate.MAX_GRANT_BYTES)
        # The design record measured 493 bytes; a rule that balloons is a finding.
        self.assertLess(max(sizes.values()), 1_024, sizes)

    def test_a_grant_over_the_budget_refuses(self):
        key = ("cmd_halt", None)
        fixed = len(gate.canonical(call(key, at("implement"), {"reason": ""})).encode())
        fits = {"reason": "r" * (65_536 - fixed)}
        self.assertEqual(len(gate.canonical(call(key, at("implement"), fits)).encode()), 65_536)
        self.assert_refusal("grant-oversized", key, at("implement"), {"reason": fits["reason"] + "r"})

    def test_non_ascii_values_are_measured_in_bytes(self):
        key = ("cmd_halt", None)
        grant = call(key, at("implement"), {"reason": "é" * 100})
        self.assertGreater(len(gate.canonical(grant).encode()), 100)


class PurityTests(GateCase):
    ALLOWED_IMPORTS = {"__future__", "json", "re", "typing"}
    FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "print", "breakpoint", "globals", "vars"}
    FORBIDDEN_ATTRIBUTES = {"load", "dump", "system", "popen", "Popen", "run", "call", "check_output", "spawn",
                            "read_text", "write_text", "read_bytes", "write_bytes", "open", "urlopen", "connect"}

    def setUp(self):
        self.tree = ast.parse(SOURCE.read_text(encoding="utf-8"))

    def test_module_imports_only_the_standard_library(self):
        imported = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                imported |= {alias.name.split(".")[0] for alias in node.names}
            if isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                imported.add(node.module.split(".")[0])
        self.assertLessEqual(imported, set(sys.stdlib_module_names))
        self.assertEqual(imported, self.ALLOWED_IMPORTS)

    def test_module_opens_no_file_and_starts_no_process(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, self.FORBIDDEN_NAMES, node.lineno)
            if isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, self.FORBIDDEN_ATTRIBUTES, node.lineno)
            self.assertNotIsInstance(node, (ast.With, ast.AsyncWith, ast.Global, ast.Nonlocal))

    def test_module_reads_no_prose(self):
        # The only pattern is the digest form, and a command value meets a
        # string method in one place: the ADR-047 prefix test on a config path.
        patterns = [node for node in ast.walk(self.tree) if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "re"]
        self.assertEqual([ast.unparse(node) for node in patterns], ["re.compile('[0-9a-f]{64}')"])
        methods = {node.func.attr for node in ast.walk(self.tree)
                   if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertEqual(methods, {"compile", "dumps", "fullmatch", "get", "startswith", "encode", "values", "__init__"})

    def test_importing_the_module_runs_nothing_but_definitions(self):
        for node in self.tree.body:
            self.assertIsInstance(node, (ast.Expr, ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign,
                                         ast.ClassDef, ast.FunctionDef), node.lineno)
            if isinstance(node, ast.Expr):
                self.assertIsInstance(node.value, ast.Constant)

    def test_every_case_decides_with_files_processes_and_sockets_disabled(self):
        def forbidden(*_args, **_kwargs):
            raise AssertionError("the gate touched a file, a process or a socket")

        with mock.patch.object(builtins, "open", forbidden), mock.patch.object(os, "open", forbidden), \
                mock.patch.object(subprocess, "Popen", forbidden), mock.patch.object(os, "system", forbidden), \
                mock.patch.object(socket, "socket", forbidden):
            for key, (granted, refused) in CASES.items():
                call(key, *granted)
                with self.assertRaises(gate.Refusal):
                    call(key, *refused[:3])

    def test_evaluate_is_deterministic_and_leaves_its_inputs_alone(self):
        for key, (granted, _) in CASES.items():
            directive, command, evidence = copy.deepcopy(granted)
            first = call(key, directive, command, evidence)
            self.assertEqual((directive, command, evidence), granted)
            self.assertEqual(first, call(key, directive, command, evidence))
            self.assertIsNot(first["directive"], directive)
            self.assertIsNot(first["command"], command)

    def test_evaluate_takes_exactly_the_named_inputs(self):
        function = next(node for node in self.tree.body if isinstance(node, ast.FunctionDef) and node.name == "evaluate")
        self.assertEqual(function.args.args, [])
        self.assertEqual([argument.arg for argument in function.args.kwonlyargs],
                         ["state_sha256", "ledger_tail", "ledger_count", "directive", "handler", "subcommand", "command", "evidence"])


if __name__ == "__main__":
    unittest.main()
