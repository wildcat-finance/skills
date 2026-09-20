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
        ({"do": "merge-step", "step": 1}, {}, {}, "directive-not-authorised"),
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

    def granted(self, key, directive, command=None, evidence=None):
        try:
            grant = call(key, directive, command, evidence)
        except gate.Refusal as refusal:
            self.fail(f"refused with {refusal.report['code']}")
        self.assert_grant(grant, key, directive, {} if command is None else command)

    def assert_refusal(self, code, key, directive, command=None, evidence=None, **preimage):
        try:
            call(key, directive, command, evidence, **preimage)
        except gate.Refusal as refusal:
            report = refusal.report
        except Exception as error:  # the gate's contract is one grant or one Refusal
            self.fail(f"escaped as {type(error).__name__}, not a Refusal")
        else:
            self.fail("granted")
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
            self.assertIsInstance(owners, dict)
            self.assertLessEqual(set(owners), set(gate.RULES))
            for key, admitted in owners.items():
                self.assertLessEqual(admitted, gate.DIRECTIVES, key)
                self.assertLessEqual(gate.RULES[key].directives, admitted, key)
                self.assertNotIn("halted", admitted, key)
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


# Written out here, not read from the gate: the instruction each code carries,
# so a line attached to another code fails.
RECOVERY_PHRASES = {
    "preimage-malformed": "pass the verified state digest",
    "command-unknown": "no rule for the requested mutation",
    "directive-shape-unknown": "a directive carries only",
    "directive-unknown": "outside this controller's vocabulary",
    "round-out-of-range": "close the audit, halt, or use another",
    "command-field-unknown": "the rule names every field it admits",
    "command-field-missing": "supply the field the rule requires",
    "command-value-malformed": "pass each value as a string",
    "evidence-field-unknown": "the rule names all the evidence it admits",
    "promise-unknown": "name a Promise declared in Fiat's SKILL.md",
    "promise-mismatch": "name the Promise the rule for this command carries",
    "consequence-unknown": "name a consequence from",
    "consequence-mismatch": "name the consequence the rule's Promise declares",
    "recovery-path-unknown": "not one this controller can recover",
    "recovery-pending": "rerun the command that owns the pending record",
    "directive-not-authorised": "does not authorise it at the current directive",
    "config-path-immutable": "audit policy is fixed at init",
    "resume-needs-named-exit": "the halt covers an exhausted audit loop",
    "resume-exit-unknown": "the only typed exit",
    "resume-exit-mismatch": "the halt does not cover",
    "audit-close-needs-a-round": "no round is recorded for this step",
    "audit-close-needs-no-further-leads": "findings are open",
    "checkpoint-boundary-unaccepted": "export or archive only immediately after",
    "grant-oversized": "shorten the command values",
}


class RecoveryLineTests(GateCase):
    """A recovery line is what the operator acts on, so it cannot be empty or stale."""

    def test_every_code_has_its_own_instruction(self):
        lines = list(gate.REFUSALS.values())
        self.assertEqual(len(lines), 24)
        self.assertEqual(len(set(lines)), len(lines))
        for code, line in gate.REFUSALS.items():
            with self.subTest(code=code):
                self.assertIs(type(line), str)
                self.assertGreaterEqual(len(line.split()), 5)

    def test_each_line_belongs_to_the_code_written_here_and_to_no_other(self):
        self.assertEqual(set(RECOVERY_PHRASES), set(gate.REFUSALS))
        for code, phrase in RECOVERY_PHRASES.items():
            with self.subTest(code=code):
                self.assertGreaterEqual(len(phrase.split()), 3)
                holders = {other for other, line in gate.REFUSALS.items() if phrase in line}
                self.assertEqual(holders, {code})

    def test_a_line_names_the_value_of_each_constant_it_depends_on(self):
        lines = gate.REFUSALS
        self.assertIn(f"rounds 1 through {gate.LOOP_ROUND_MAX};", lines["round-out-of-range"])
        self.assertIn(f"at most {gate.MAX_GRANT_BYTES:,} bytes", lines["grant-oversized"])
        levels = sorted(gate.CONSEQUENCE_LEVELS)
        self.assertIn(f"from {levels[0]} through {levels[-1]},", lines["consequence-unknown"])
        for path in sorted(gate.CONFIG_SET_EXACT_PATHS) + [prefix + "*" for prefix in gate.CONFIG_SET_PREFIXES]:
            self.assertIn(path, re.split(r"[ ,;]+", lines["config-path-immutable"]), path)
        for exit_named in sorted(gate.RESUME_EXITS):
            self.assertIn(f"`hexctl resume --to {exit_named}`", lines["resume-needs-named-exit"])
            self.assertIn(f"`{exit_named}`", lines["resume-exit-unknown"])
            self.assertIn(f"`{exit_named}`", lines["resume-exit-mismatch"])
        for line in (lines["command-unknown"], lines["directive-shape-unknown"], lines["directive-unknown"],
                     lines["directive-not-authorised"]):
            self.assertIn("`hexctl next`", line)
        for line in (lines["preimage-malformed"], lines["recovery-path-unknown"]):
            self.assertIn("`hexctl verify`", line)
        self.assertIn("do, step, round and covers", lines["directive-shape-unknown"])
        self.assertEqual(gate.DIRECTIVE_FIELDS, {"do", "step", "round", "covers"})


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

    def test_a_run_holding_only_its_init_entry_is_granted(self):
        grant = call(self.HALT, at("study"), self.REASON, ledger_count=1)
        self.assertEqual(grant["ledger_count"], 1)

    def test_a_directive_carrying_all_four_fields_is_read_field_by_field(self):
        full = {"step": 2, "round": 1, "covers": "implement"}
        self.assert_refusal("directive-unknown", self.HALT, {"do": "round-9", **full}, self.REASON)
        for do in ("implement", "audit-round", "halted"):
            with self.subTest(do=do):
                self.assert_refusal("directive-shape-unknown", self.HALT, {"do": do, **full}, self.REASON)

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
            "resume-exit-mismatch", "grant-oversized", "audit-close-needs-a-round",
        }
        self.assertEqual(specimens, set(gate.REFUSALS))


ALL = {"absent", "halted", "blocked", "study", "runbook", "inoculate", "implement", "run-exit",
       "resolve-security-suite", "audit-round", "close-audit", "audit-verdict", "prose", "push",
       "merge-step", "resolve-versions", "integrate", "done"}
STEPS = {"blocked", "inoculate", "implement", "run-exit", "resolve-security-suite", "audit-round",
         "close-audit", "audit-verdict", "prose", "push"}
# Written out here, not read from the gate, so a rule widened in the table fails.
ADMITTED = {
    ("cmd_init", None): {"absent"},
    ("cmd_observe", None): ALL - {"absent"},
    ("cmd_record", None): ALL - {"absent"},
    ("cmd_config", "set"): ALL - {"absent"},
    ("cmd_amend_study", None): STEPS - {"blocked"},
    ("cmd_amend_runbook", None): STEPS,
    ("cmd_done", "study"): {"study"},
    ("cmd_done", "runbook"): {"runbook"},
    ("cmd_done", "inoculate"): {"inoculate"},
    ("cmd_done", "implement"): {"implement"},
    ("cmd_done", "audit"): {"close-audit", "audit-round", "audit-verdict"},
    ("cmd_done", "prose"): {"prose"},
    ("cmd_done", "push"): {"push"},
    ("cmd_done", "merge-step"): {"merge-step"},
    ("cmd_done", "sync-run"): {"integrate", "resolve-versions"},
    ("cmd_done", "resolve-versions"): {"resolve-versions", "integrate"},
    ("cmd_done", "integrate"): {"integrate"},
    ("cmd_audit_round", None): {"audit-round"},
    ("cmd_halt", None): ALL - {"absent"},
    ("cmd_resume", None): {"halted"},
    ("cmd_reset", None): {"done", "halted"},
    ("cmd_checkpoint_export", None): ALL - {"absent", "halted"},
    ("cmd_checkpoint_archive", None): ALL - {"absent", "halted"},
    ("cmd_carryover_export", None): {"audit-verdict"},
    ("cmd_carryover_bind", None): {"audit-verdict"},
    ("cmd_replacement_begin", None): {"study"},
    ("cmd_replacement_resume", None): {"study"},
    ("cmd_retain_guard", None): {"inoculate"},
    ("cmd_run_exit", None): {"run-exit"},
}


class AdmittedDirectiveTests(GateCase):
    """Every rule against every directive, so no rule can be widened unseen."""

    @staticmethod
    def directives(do):
        if do == "absent":
            return [{"do": "absent"}]
        if do == "halted":
            return [{"do": "halted", "covers": covers} for covers in sorted(ALL - {"absent", "halted"})]
        if do == "audit-round":
            return [{"do": do, "step": 2, "round": number} for number in (1, 8)]
        return [{"do": do}, {"do": do, "step": 2}]

    def test_the_vocabulary_and_the_rules_are_the_ones_written_here(self):
        self.assertEqual(ALL, set(gate.DIRECTIVES))
        self.assertEqual(set(ADMITTED), set(gate.RULES))

    def test_each_rule_grants_at_its_directives_and_at_no_other(self):
        decided = 0
        for key, (granted, _) in CASES.items():
            _directive, command, evidence = granted
            evidence = {name: value for name, value in evidence.items() if name != "recovery"}
            for do in sorted(ALL):
                for directive in self.directives(do):
                    decided += 1
                    with self.subTest(key=key, directive=directive):
                        try:
                            call(key, directive, command, evidence)
                            code = None
                        except gate.Refusal as refusal:
                            code = refusal.report["code"]
                        except Exception as error:
                            self.fail(f"escaped as {type(error).__name__}, not a Refusal")
                        if do in ADMITTED[key]:
                            self.assertNotEqual(code, "directive-not-authorised")
                        else:
                            self.assertEqual(code, "directive-not-authorised")
        self.assertEqual(decided, 29 * (1 + 16 + 2 + 15 * 2))

    def test_no_mutation_but_config_halt_record_observe_resume_and_reset_is_granted_at_a_halt(self):
        open_at_halt = {key for key, admitted in ADMITTED.items() if "halted" in admitted}
        self.assertEqual(open_at_halt, {("cmd_observe", None), ("cmd_record", None), ("cmd_config", "set"),
                                        ("cmd_halt", None), ("cmd_resume", None), ("cmd_reset", None)})


# Written out here, not read from the gate, so a widened field set fails.
# key -> (every field the rule admits, the fields it requires)
FIELDS = {
    ("cmd_init", None): ({"topic", "base", "task_issue", "run_branch", "frontier", "controller_currency_waiver"}, set()),
    ("cmd_observe", None): ({"artifact", "capture_status", "redaction_status", "reason_code"},
                            {"capture_status", "redaction_status"}),
    ("cmd_record", None): ({"key", "value"}, {"key", "value"}),
    ("cmd_config", "set"): ({"path", "value"}, {"path", "value"}),
    ("cmd_amend_study", None): ({"artifact"}, {"artifact"}),
    ("cmd_amend_runbook", None): ({"artifact"}, {"artifact"}),
    ("cmd_done", "study"): ({"artifact", "skills"}, set()),
    ("cmd_done", "runbook"): ({"artifact", "steps_file"}, set()),
    ("cmd_done", "inoculate"): (set(), set()),
    ("cmd_done", "implement"): ({"branch", "commit", "tests"}, set()),
    ("cmd_done", "audit"): ({"fixes_ref", "log", "no_further_leads", "reason"}, set()),
    ("cmd_done", "prose"): ({"files", "skills"}, set()),
    ("cmd_done", "push"): ({"pr_url", "pr_base", "head_commit", "merge_commit", "closed_issue_url"}, set()),
    ("cmd_done", "merge-step"): ({"step", "merge_commit"}, set()),
    ("cmd_done", "sync-run"): ({"commit", "base_commit", "revalidation", "decision_assignments", "supersede_sync",
                                "acknowledge_sync_paths", "reason"}, set()),
    ("cmd_done", "resolve-versions"): ({"accept_evolution_base", "recovery_authority", "reason"}, set()),
    ("cmd_done", "integrate"): ({"pr_url", "merge_commit", "closed_issue_url"}, set()),
    ("cmd_audit_round", None): ({"findings", "log", "audit_filter", "fixes_commit", "elenchus_verdict",
                                 "phylax_exit", "ephoros_exit", "hypomnema_exit"}, {"findings"}),
    ("cmd_halt", None): ({"reason"}, {"reason"}),
    ("cmd_resume", None): ({"note", "to"}, set()),
    ("cmd_reset", None): (set(), set()),
    ("cmd_checkpoint_export", None): ({"out"}, {"out"}),
    ("cmd_checkpoint_archive", None): ({"format"}, set()),
    ("cmd_carryover_export", None): ({"request"}, {"request"}),
    ("cmd_carryover_bind", None): ({"request"}, {"request"}),
    ("cmd_replacement_begin", None): ({"request"}, {"request"}),
    ("cmd_replacement_resume", None): (set(), set()),
    ("cmd_retain_guard", None): ({"finding_id", "guard_commit"}, {"finding_id", "guard_commit"}),
    ("cmd_run_exit", None): ({"criterion"}, {"criterion"}),
}
TAIL_EVENT_RULES = {("cmd_checkpoint_export", None), ("cmd_checkpoint_archive", None)}
# Each list also carries the other vocabulary's names, so an evidence name
# admitted as a command field, or a command field admitted as evidence, fails.
EVIDENCE_NAMES = {"promise", "consequence", "recovery", "tail_event", "authority", "user"}
HOSTILE_FIELDS = {"max_rounds", "round", "loop", "force", "dir", "zz"} | EVIDENCE_NAMES
HOSTILE_EVIDENCE = {"authority", "user", "loop", "round", "max_rounds", "reason", "zz"}.union(
    *(fields for fields, _ in FIELDS.values())
)


class CommandFieldTests(GateCase):
    """Every rule against every field, so no field set can be widened unseen."""

    @staticmethod
    def code(key, directive, command, evidence):
        try:
            call(key, directive, command, evidence)
        except gate.Refusal as refusal:
            return refusal.report["code"]
        return None

    def test_the_rules_are_the_ones_written_here(self):
        self.assertEqual(set(FIELDS), set(gate.RULES))
        self.assertEqual(len(FIELDS), 29)

    def test_each_rule_admits_the_fields_written_here_and_no_other(self):
        names = sorted(set().union(*(fields for fields, _ in FIELDS.values())) | HOSTILE_FIELDS)
        decided = 0
        for key, (granted, _) in CASES.items():
            directive, command, evidence = granted
            for name in names:
                decided += 1
                with self.subTest(key=key, field=name):
                    code = self.code(key, directive, {name: "x", **command}, evidence)
                    if name in FIELDS[key][0]:
                        self.assertNotEqual(code, "command-field-unknown")
                    else:
                        self.assertEqual(code, "command-field-unknown")
        self.assertEqual(decided, 29 * len(names))
        self.assertGreater(len(names), 56)
        self.assertLessEqual(EVIDENCE_NAMES, set(names))

    def test_each_rule_requires_the_fields_written_here_and_no_other(self):
        decided = 0
        for key, (granted, _) in CASES.items():
            directive, command, evidence = granted
            fields, required = FIELDS[key]
            self.assertLessEqual(required, set(command), key)
            for name in sorted(fields):
                without = {field: value for field, value in command.items() if field != name}
                for candidate in (without, {**without, name: None}):
                    decided += 1
                    with self.subTest(key=key, field=name, null=name in candidate):
                        code = self.code(key, directive, candidate, evidence)
                        if name in required:
                            self.assertEqual(code, "command-field-missing")
                        else:
                            self.assertNotEqual(code, "command-field-missing")
        self.assertEqual(decided, 2 * sum(len(fields) for fields, _ in FIELDS.values()))

    def test_only_the_checkpoint_rules_admit_a_tail_event(self):
        for key, (granted, _) in CASES.items():
            directive, command, evidence = granted
            with self.subTest(key=key):
                code = self.code(key, directive, command, {**evidence, "tail_event": "done:push"})
                if key in TAIL_EVENT_RULES:
                    self.assertIsNone(code)
                else:
                    self.assertEqual(code, "evidence-field-unknown")

    def test_each_rule_admits_the_evidence_written_here_and_no_other(self):
        names = sorted(HOSTILE_EVIDENCE | {"tail_event"})
        self.assertGreater(len(names), 56)
        self.assertLessEqual({"to", "request", "out", "reason", "path"}, set(names))
        decided = 0
        for key, (granted, _) in CASES.items():
            directive, command, evidence = granted
            for name in names:
                decided += 1
                with self.subTest(key=key, evidence=name):
                    code = self.code(key, directive, command, {**evidence, name: "x"})
                    if name == "tail_event" and key in TAIL_EVENT_RULES:
                        self.assertEqual(code, "checkpoint-boundary-unaccepted")
                    else:
                        self.assertEqual(code, "evidence-field-unknown")
        self.assertEqual(decided, 29 * len(names))

    def test_no_ledger_event_but_the_two_boundaries_is_an_accepted_tail(self):
        events = ("init", "record", "config-set", "halt", "resume", "retire", "observe", "amend:study",
                  "amend:runbook", "done:study", "done:runbook", "done:implement", "done:audit", "done:prose",
                  "done:merge-step", "done:sync-run", "done:integrate", "run-exit", "done:Push", "audit-round ")
        for key in sorted(TAIL_EVENT_RULES):
            command = CASES[key][0][1]
            for event in events:
                with self.subTest(key=key, event=event):
                    self.assert_refusal("checkpoint-boundary-unaccepted", key, at("audit-verdict"), command,
                                        {"tail_event": event})
            self.granted(key, at("audit-verdict"), command, {"tail_event": "audit-round"})
            self.granted(key, at("push"), command, {"tail_event": "done:push"})


class RecoveryWindowTests(GateCase):
    """A pending record outlives its state write; its owner must still be granted."""

    # Written out here, not read from the gate, so a widened recovery row fails.
    LIVE = {
        "amendment": {("cmd_amend_study", None): STEPS, ("cmd_amend_runbook", None): STEPS},
        "version-resolution": {("cmd_done", "resolve-versions"): {"resolve-versions", "integrate"}},
        "no-known-inoculation": {("cmd_done", "inoculate"): {"inoculate", "implement", "run-exit"}},
    }
    WINDOWS = (
        ("no-known-inoculation", ("cmd_done", "inoculate"), at("implement"), {}),
        ("no-known-inoculation", ("cmd_done", "inoculate"), at("run-exit"), {}),
        ("amendment", ("cmd_amend_study", None), at("blocked"), {"artifact": "study.md"}),
    )

    def test_the_owner_is_granted_at_the_directive_the_written_state_returns(self):
        for recovery, key, directive, command in self.WINDOWS:
            with self.subTest(recovery=recovery, directive=directive["do"]):
                self.granted(key, directive, command, {"recovery": recovery})

    def test_a_live_record_admits_its_owner_at_the_directives_written_here_and_no_other(self):
        self.assertEqual({name: set(owners) for name, owners in gate.RECOVERY_PATHS.items()},
                         {name: set(owners) for name, owners in self.LIVE.items()})
        decided = 0
        for recovery, owners in self.LIVE.items():
            for key, admitted in owners.items():
                _directive, command, evidence = CASES[key][0]
                evidence = {**evidence, "recovery": recovery}
                for do in sorted(ALL):
                    for directive in AdmittedDirectiveTests.directives(do):
                        decided += 1
                        with self.subTest(recovery=recovery, key=key, directive=directive):
                            try:
                                call(key, directive, command, evidence)
                                code = None
                            except gate.Refusal as refusal:
                                code = refusal.report["code"]
                            self.assertEqual(code, None if do in admitted else "directive-not-authorised")
        self.assertEqual(decided, 4 * (1 + 16 + 2 + 15 * 2))

    def test_version_resolution_is_renewed_at_integrate_with_no_record_live(self):
        self.granted(("cmd_done", "resolve-versions"), {"do": "integrate"}, {})

    def test_the_same_command_refuses_there_when_no_record_is_live(self):
        for _recovery, key, directive, command in self.WINDOWS:
            with self.subTest(key=key, directive=directive["do"]):
                self.assert_refusal("directive-not-authorised", key, directive, command)

    def test_a_live_record_widens_no_other_directive(self):
        for recovery, key, _directive, command in self.WINDOWS:
            self.assertIsInstance(gate.RECOVERY_PATHS[recovery], dict)
            admitted = gate.RECOVERY_PATHS[recovery][key]
            for do in sorted(gate.RUNNING - admitted - {"audit-round"}):
                with self.subTest(recovery=recovery, do=do):
                    self.assert_refusal("directive-not-authorised", key, {"do": do}, command, {"recovery": recovery})
            self.assert_refusal("directive-not-authorised", key, {"do": "halted", "covers": "implement"},
                                command, {"recovery": recovery})

    def test_a_fresh_study_amendment_refuses_at_blocked_and_the_repair_is_granted(self):
        self.assert_refusal("directive-not-authorised", ("cmd_amend_study", None), at("blocked"), {"artifact": "s.md"})
        command = {"artifact": "r.md"}
        self.granted(("cmd_amend_runbook", None), at("blocked"), command)

    def test_sync_run_is_granted_where_resolve_versions_names_it_as_recovery(self):
        key = ("cmd_done", "sync-run")
        for do in ("integrate", "resolve-versions"):
            with self.subTest(do=do):
                self.granted(key, {"do": do}, SYNC)
        self.assert_refusal("directive-not-authorised", ("cmd_done", "integrate"), {"do": "resolve-versions"},
                            {"merge_commit": "a" * 40})


class ExactTypeTests(GateCase):
    """Every hostile value refuses with a stable code; none escapes as another exception."""

    HALT = ("cmd_halt", None)
    REASON = {"reason": "stop"}

    class Text(str):
        pass

    class Mapping(dict):
        def get(self, name, default=None):
            return "absent" if name == "do" else dict.get(self, name, default)

    def test_an_unhashable_covers_refuses(self):
        for covers in (["audit-verdict"], {"do": "audit-verdict"}, 7, True, self.Text("implement")):
            with self.subTest(covers=covers):
                self.assert_refusal("directive-unknown", self.HALT, {"do": "halted", "covers": covers}, self.REASON)

    def test_an_unhashable_resume_exit_refuses(self):
        for exit_named in (["audit-verdict"], [], self.Text("audit-verdict")):
            with self.subTest(exit_named=exit_named):
                code = "command-value-malformed" if isinstance(exit_named, str) else "resume-exit-unknown"
                self.assert_refusal(code, ("cmd_resume", None), EXHAUSTED_HALT, {"to": exit_named})

    def test_an_integer_too_wide_to_serialise_refuses(self):
        wide = 10**5000
        self.assert_refusal("command-value-malformed", ("cmd_done", "prose"), at("prose"), {"files": wide})
        self.assert_refusal("command-value-malformed", ("cmd_done", "prose"), at("prose"), {"files": -(2**63)})
        self.assert_refusal("preimage-malformed", self.HALT, at("implement"), self.REASON, ledger_count=wide)
        self.assert_refusal("directive-shape-unknown", self.HALT, {"do": "implement", "step": wide}, self.REASON)
        self.assert_refusal("directive-shape-unknown", self.HALT, {"do": "audit-round", "round": wide}, self.REASON)
        self.assert_refusal("consequence-unknown", self.HALT, at("implement"), self.REASON, {"consequence": wide})
        self.granted(("cmd_done", "prose"), at("prose"), {"files": 2**63 - 1})
        self.granted(("cmd_done", "prose"), at("prose"), {"files": -(2**63 - 1)})

    def test_a_subclass_cannot_stand_in_for_a_plain_value(self):
        text = self.Text
        self.assert_refusal("directive-shape-unknown", self.HALT, self.Mapping({"do": "implement"}), self.REASON)
        self.assert_refusal("directive-shape-unknown", self.HALT, {"do": text("implement")}, self.REASON)
        self.assert_refusal("command-value-malformed", self.HALT, at("implement"), self.Mapping(self.REASON))
        self.assert_refusal("command-value-malformed", self.HALT, at("implement"), {"reason": text("stop")})
        self.assert_refusal("command-value-malformed", self.HALT, at("implement"), {text("reason"): "stop"})
        self.assert_refusal("command-value-malformed", ("cmd_done", "prose"), at("prose"), {"skills": [text("a")]})
        self.assert_refusal("evidence-field-unknown", self.HALT, at("implement"), self.REASON, self.Mapping({}))
        self.assert_refusal("promise-unknown", self.HALT, at("implement"), self.REASON,
                            {"promise": text("fiat-receipted-delivery")})
        self.assert_refusal("recovery-path-unknown", ("cmd_amend_runbook", None), at("implement"),
                            {"artifact": "r.md"}, {"recovery": text("amendment")})
        self.assert_refusal("preimage-malformed", self.HALT, at("implement"), self.REASON, state_sha256=text(STATE))
        for key in ((text("cmd_halt"), None), ("cmd_done", text("study"))):
            try:
                call(key, {"do": "study"}, {"reason": "stop"})
            except gate.Refusal as refusal:
                self.assertEqual(refusal.report["code"], "command-unknown")
            else:
                self.fail("a subclassed rule key was granted")

    def test_no_hostile_combination_escapes_as_anything_but_a_refusal(self):
        import random

        rng = random.Random(871)
        text = self.Text
        pool = [None, True, False, 0, 1, -1, 8, 9, 2**63, 10**5000, 1.5, float("nan"), b"x", "", "x", "b0" * 32,
                "B0" * 32, "genesis", "audit-verdict", "halted", "absent", "implement", "amendment",
                "version-resolution", "no-known-inoculation", "done:push", "audit-round", "git", "audit.max_rounds",
                [], ["a"], [1], [["a"]], {}, {"a": 1}, (), ("a",), set(), text("implement"), self.Mapping(), object(),
                "\ud800", "fiat-receipted-delivery", 2, 3]
        keys = list(gate.RULES) + [("cmd_x", None), (None, None), (1, 2), ([], None)]
        fields = sorted({name for rule in gate.RULES.values() for name in rule.fields} | {"zz"})
        grants = 0
        for _ in range(10_000):
            handler, subcommand = rng.choice(keys)
            directive = {"do": rng.choice(sorted(ALL))} if rng.random() < 0.85 else rng.choice(pool)
            if type(directive) is dict:
                for name in ("step", "round", "covers", "zz"):
                    if rng.random() < 0.3:
                        directive[name] = rng.choice(pool)
                if directive.get("do") == "halted" and rng.random() < 0.7:
                    directive["covers"] = rng.choice(sorted(ALL))
                if directive.get("do") == "audit-round" and rng.random() < 0.7:
                    directive["round"] = rng.randint(-1, 10)
            command = ({rng.choice(fields): rng.choice(pool) for _ in range(rng.randint(0, 3))}
                       if rng.random() < 0.9 else rng.choice(pool))
            evidence = ({rng.choice(["promise", "consequence", "recovery", "tail_event", "zz"]): rng.choice(pool)
                         for _ in range(rng.randint(0, 2))} if rng.random() < 0.9 else rng.choice(pool))
            preimage = (STATE, TAIL, COUNT) if rng.random() < 0.8 else tuple(rng.choice(pool) for _ in range(3))
            try:
                grant = gate.evaluate(state_sha256=preimage[0], ledger_tail=preimage[1], ledger_count=preimage[2],
                                      directive=directive, handler=handler, subcommand=subcommand,
                                      command=command, evidence=evidence)
            except gate.Refusal as refusal:
                self.assertIn(refusal.report["code"], gate.REFUSALS)
            except Exception as error:
                self.fail(f"escaped as {type(error).__name__}: {directive!r} {command!r} {evidence!r}")
            else:
                grants += 1
                self.assertEqual(set(grant), GRANT_FIELDS)
                self.assertIn(grant["directive"]["do"], ADMITTED[(handler, subcommand)] | {"blocked", "implement", "run-exit"})
        self.assertGreater(grants, 0)

    def test_the_grant_shares_no_list_with_its_caller(self):
        command = copy.deepcopy(SYNC)
        grant = call(("cmd_done", "sync-run"), {"do": "integrate"}, command)
        command["acknowledge_sync_paths"].append("docs/smuggled.md")
        self.assertEqual(grant["command"], SYNC)


class CloseAuditTests(GateCase):
    KEY = ("cmd_done", "audit")

    def test_a_clean_last_round_closes_without_a_waiver(self):
        self.assert_grant(call(self.KEY, at("close-audit"), {"fixes_ref": "a" * 40}), self.KEY, at("close-audit"), {"fixes_ref": "a" * 40})

    def test_the_audit_cannot_close_before_a_round_is_recorded(self):
        first = at("audit-round", round=1)
        for command in ({}, {"no_further_leads": True, "reason": "accepted by the maintainer"}):
            with self.subTest(command=command):
                report = self.assert_refusal("audit-close-needs-a-round", self.KEY, first, command)
                self.assertIn("audit-round", report["recovery"])
        granted = {"no_further_leads": True, "reason": "accepted by the maintainer"}
        self.granted(self.KEY, at("audit-round", round=2), granted)

    def test_open_findings_need_the_waiver_and_its_reason(self):
        for directive in (at("audit-round", round=3), at("audit-verdict")):
            for command in ({}, {"reason": "accepted"}, {"no_further_leads": True, "reason": ""},
                            {"no_further_leads": False, "reason": "accepted"}, {"no_further_leads": "true", "reason": "accepted"}):
                with self.subTest(directive=directive["do"], command=command):
                    self.assert_refusal("audit-close-needs-no-further-leads", self.KEY, directive, command)
            for reason in (True, 7, ["accepted"]):
                with self.subTest(directive=directive["do"], reason=reason):
                    self.assert_refusal("audit-close-needs-no-further-leads", self.KEY, directive,
                                        {"no_further_leads": True, "reason": reason})
            granted = {"no_further_leads": True, "reason": "accepted by the maintainer"}
            self.assert_grant(call(self.KEY, directive, granted), self.KEY, directive, granted)


class CheckpointBoundaryTests(GateCase):
    def test_both_accepted_boundaries_and_no_other(self):
        for key, command in ((("cmd_checkpoint_export", None), {"out": "capsule"}), (("cmd_checkpoint_archive", None), {})):
            self.assert_grant(call(key, at("inoculate"), command, PUSHED), key, at("inoculate"), command)
            self.assert_grant(call(key, at("audit-verdict"), command, {"tail_event": "audit-round"}), key, at("audit-verdict"), command)
            class Text(str):
                pass

            for evidence in ({}, {"tail_event": None}, {"tail_event": "resume"}, {"tail_event": 7},
                             {"tail_event": ["done:push"]}, {"tail_event": {"done:push": 1}},
                             {"tail_event": Text("done:push")}, {"tail_event": True}):
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

    def test_the_measured_form_is_the_controllers_canonical_json(self):
        self.assertEqual(gate.canonical({"b": [1, "\u00e9", True], "a": None}), '{"a":null,"b":[1,"\\u00e9",true]}')
        key = ("cmd_done", "push")
        forward = {"pr_url": "https://example.invalid/pull/1", "head_commit": "a" * 40}
        backward = dict(reversed(list(forward.items())))
        one = call(key, {"do": "push", "step": 2}, forward)
        other = call(key, {"step": 2, "do": "push"}, backward)
        self.assertNotEqual(list(one["command"]), list(other["command"]))
        self.assertEqual(gate.canonical(one), gate.canonical(other))
        self.assertNotIn(" ", gate.canonical(one))

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
        self.assertEqual(methods, {"compile", "dumps", "fullmatch", "get", "startswith", "encode", "values", "items", "__init__"})

    def test_module_calls_only_a_closed_set_of_names(self):
        # A forbidden attribute is reachable through `getattr`, and a forbidden
        # module through `__builtins__` or `sys.modules`, so the names the module
        # may call or read dynamically are pinned as well as the ones it may not.
        called = {node.func.id for node in ast.walk(self.tree)
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        defined = {node.name for node in self.tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertEqual(called - defined, {"frozenset", "set", "dict", "type", "all", "any", "len", "list", "super", "refuse"})
        for node in ast.walk(self.tree):
            self.assertNotIsInstance(node, (ast.Lambda, ast.Await, ast.Yield, ast.YieldFrom, ast.Starred))
            if isinstance(node, ast.Name):
                self.assertNotIn(node.id, {"getattr", "setattr", "delattr", "__builtins__", "locals", "sys", "os"},
                                 node.lineno)
            if isinstance(node, ast.Attribute):
                self.assertFalse(node.attr.startswith("__") and node.attr != "__init__", node.lineno)

    def test_no_function_writes_module_state(self):
        # One call cannot poison the next: inside a function the only stores are
        # local names and the refusal's own report.
        for function in ast.walk(self.tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            for node in ast.walk(function):
                if isinstance(node, (ast.Delete, ast.AugAssign)):
                    self.fail(f"line {node.lineno} mutates in place")
                targets = node.targets if isinstance(node, ast.Assign) else (
                    [node.target] if isinstance(node, (ast.AnnAssign, ast.NamedExpr)) else [])
                for target in targets:
                    if isinstance(target, ast.Name):
                        continue
                    self.assertEqual(ast.unparse(target), "self.report", node.lineno)
        before = copy.deepcopy((gate.RULES, gate.PROMISES, gate.RECOVERY_PATHS, gate.REFUSALS, sorted(gate.CHECKS)))
        for key, (granted, refused) in CASES.items():
            call(key, *granted)
            with self.assertRaises(gate.Refusal):
                call(key, *refused[:3])
        self.assertEqual(before, (gate.RULES, gate.PROMISES, gate.RECOVERY_PATHS, gate.REFUSALS, sorted(gate.CHECKS)))

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
