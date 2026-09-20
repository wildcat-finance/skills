#!/usr/bin/env python3
"""Decide whether one Fiat mutation is authorised against one verified preimage.

`evaluate` takes the state digest, the ledger tail and count, the canonical
directive, the handler and subcommand, the normalised command and its evidence.
It returns one closed `fiat-transition-grant/v1` object or raises `Refusal`,
whose report is one closed `fiat-transition-refusal/v1` object.

The module is a decision table and nothing else. It imports only the standard
library, opens no file, starts no process and interprets no prose: a command
value is carried into the grant as data and compared only where a rule names an
exact vocabulary. The table is closed, so an unknown command, field, Promise
id, directive shape, recovery path or consequence level refuses.

The contract, every stable refusal code and the same-account limit are in
`references/transition-gate.md`.
"""

from __future__ import annotations

import json
import re
from typing import NamedTuple

GRANT_SCHEMA = "fiat-transition-grant/v1"
REFUSAL_SCHEMA = "fiat-transition-refusal/v1"
MAX_GRANT_BYTES = 65_536
"""The grant-size budget of the design record's `max-grant-bytes` gate."""

CONSEQUENCE_LEVELS = frozenset({0, 1, 2, 3})
LOOP_ROUND_MAX = 8
"""No directive, grant or refusal represents a ninth round."""

DEFAULT_PROMISE = "fiat-receipted-delivery"
"""The Promise a refusal names when no rule was reached.

It authorises advancing only to the single next controller directive, so it is
the Promise an unmapped or malformed mutation fails.
"""

PROMISES = {
    "fiat-receipted-delivery": 2,
    "fiat-run-observation-binding": 2,
    "fiat-study-amendment": 2,
    "fiat-runbook-amendment": 2,
    "fiat-known-failure-inoculation": 2,
    "fiat-version-resolution": 2,
    "fiat-final-integration": 3,
    "fiat-local-retirement": 2,
    "fiat-controller-checkpoint": 2,
    "fiat-checkpoint-archive": 2,
    "fiat-cumulative-carryover-custody": 2,
    "fiat-replacement-admission": 2,
}
"""Each Promise a rule names, with the consequence Fiat's `SKILL.md` declares."""

ABSENT = "absent"
HALTED = "halted"
DIRECTIVES = frozenset(
    {
        ABSENT,
        HALTED,
        "blocked",
        "study",
        "runbook",
        "inoculate",
        "implement",
        "run-exit",
        "resolve-security-suite",
        "audit-round",
        "close-audit",
        "audit-verdict",
        "prose",
        "push",
        "merge-step",
        "resolve-versions",
        "integrate",
        "done",
    }
)
"""Every `do` the canonical directive may carry. `absent` means no run exists."""

DIRECTIVE_FIELDS = frozenset({"do", "step", "round", "covers"})
ACTIVE = DIRECTIVES - {ABSENT}
RUNNING = ACTIVE - {HALTED}
STEP_WORK = frozenset(
    {
        "blocked",
        "inoculate",
        "implement",
        "run-exit",
        "resolve-security-suite",
        "audit-round",
        "close-audit",
        "audit-verdict",
        "prose",
        "push",
    }
)

RESUME_EXITS = frozenset({"audit-verdict"})
"""The exits a typed `resume` may name. Study assumption 4."""

CONFIG_SET_EXACT_PATHS = frozenset({"audit.log_path", "git"})
CONFIG_SET_PREFIXES = ("git.",)
"""The ADR-047 allowlist: the whole mutable configuration surface."""

CHECKPOINT_TAIL_EVENTS = frozenset({"done:push", "audit-round"})

COMMON_EVIDENCE = frozenset({"promise", "consequence", "recovery"})

_SHA256 = re.compile(r"[0-9a-f]{64}")
_GENESIS = "genesis"
_INT_MAX = 2**63 - 1
"""No integer the controller carries is wider, and a wider one cannot be serialised."""


class Rule(NamedTuple):
    """One row of the closed table."""

    promise: str
    transition: str
    directives: frozenset
    fields: frozenset = frozenset()
    required: frozenset = frozenset()
    evidence: frozenset = frozenset()
    check: str | None = None


def _done(promise: str, phase: str, directives: set, fields: set, check=None) -> Rule:
    return Rule(
        promise,
        f"receipt-{phase}",
        frozenset(directives),
        frozenset(fields),
        check=check,
    )


RULES = {
    ("cmd_init", None): Rule(
        "fiat-receipted-delivery",
        "open-run",
        frozenset({ABSENT}),
        frozenset(
            {
                "topic",
                "base",
                "task_issue",
                "run_branch",
                "frontier",
                "controller_currency_waiver",
            }
        ),
    ),
    ("cmd_observe", None): Rule(
        "fiat-run-observation-binding",
        "bind-observation",
        ACTIVE,
        frozenset({"artifact", "capture_status", "redaction_status", "reason_code"}),
        frozenset({"capture_status", "redaction_status"}),
    ),
    ("cmd_record", None): Rule(
        "fiat-receipted-delivery",
        "record-receipt",
        ACTIVE,
        frozenset({"key", "value"}),
        frozenset({"key", "value"}),
    ),
    ("cmd_config", "set"): Rule(
        "fiat-receipted-delivery",
        "config-set",
        ACTIVE,
        frozenset({"path", "value"}),
        frozenset({"path", "value"}),
        check="config-set",
    ),
    ("cmd_amend_study", None): Rule(
        "fiat-study-amendment",
        "amend-study",
        STEP_WORK - {"blocked"},
        frozenset({"artifact"}),
        frozenset({"artifact"}),
    ),
    ("cmd_amend_runbook", None): Rule(
        "fiat-runbook-amendment",
        "amend-runbook",
        STEP_WORK,
        frozenset({"artifact"}),
        frozenset({"artifact"}),
    ),
    ("cmd_done", "study"): _done(
        "fiat-receipted-delivery", "study", {"study"}, {"artifact", "skills"}
    ),
    ("cmd_done", "runbook"): _done(
        "fiat-receipted-delivery", "runbook", {"runbook"}, {"artifact", "steps_file"}
    ),
    ("cmd_done", "inoculate"): _done(
        "fiat-known-failure-inoculation", "inoculate", {"inoculate"}, set()
    ),
    ("cmd_done", "implement"): _done(
        "fiat-receipted-delivery",
        "implement",
        {"implement"},
        {"branch", "commit", "tests"},
    ),
    ("cmd_done", "audit"): _done(
        "fiat-receipted-delivery",
        "audit",
        {"close-audit", "audit-round", "audit-verdict"},
        {"fixes_ref", "log", "no_further_leads", "reason"},
        check="close-audit",
    ),
    ("cmd_done", "prose"): _done(
        "fiat-receipted-delivery", "prose", {"prose"}, {"files", "skills"}
    ),
    ("cmd_done", "push"): _done(
        "fiat-receipted-delivery",
        "push",
        {"push"},
        {"pr_url", "pr_base", "head_commit", "merge_commit", "closed_issue_url"},
    ),
    ("cmd_done", "merge-step"): _done(
        "fiat-receipted-delivery",
        "merge-step",
        {"merge-step"},
        {"step", "merge_commit"},
    ),
    ("cmd_done", "sync-run"): _done(
        "fiat-receipted-delivery",
        "sync-run",
        {"integrate", "resolve-versions"},
        {
            "commit",
            "base_commit",
            "revalidation",
            "decision_assignments",
            "supersede_sync",
            "acknowledge_sync_paths",
            "reason",
        },
    ),
    ("cmd_done", "resolve-versions"): _done(
        "fiat-version-resolution",
        "resolve-versions",
        {"resolve-versions"},
        {"accept_evolution_base", "recovery_authority", "reason"},
    ),
    ("cmd_done", "integrate"): _done(
        "fiat-final-integration",
        "integrate",
        {"integrate"},
        {"pr_url", "merge_commit", "closed_issue_url"},
    ),
    ("cmd_audit_round", None): Rule(
        "fiat-receipted-delivery",
        "append-round",
        frozenset({"audit-round"}),
        frozenset(
            {
                "findings",
                "log",
                "audit_filter",
                "fixes_commit",
                "elenchus_verdict",
                "phylax_exit",
                "ephoros_exit",
                "hypomnema_exit",
            }
        ),
        frozenset({"findings"}),
    ),
    ("cmd_halt", None): Rule(
        "fiat-receipted-delivery",
        "set-halt",
        ACTIVE,
        frozenset({"reason"}),
        frozenset({"reason"}),
    ),
    ("cmd_resume", None): Rule(
        "fiat-receipted-delivery",
        "clear-halt",
        frozenset({HALTED}),
        frozenset({"note", "to"}),
        check="resume",
    ),
    ("cmd_reset", None): Rule(
        "fiat-local-retirement", "retire-run", frozenset({"done", HALTED})
    ),
    ("cmd_checkpoint_export", None): Rule(
        "fiat-controller-checkpoint",
        "export-checkpoint",
        RUNNING,
        frozenset({"out"}),
        frozenset({"out"}),
        frozenset({"tail_event"}),
        "checkpoint-boundary",
    ),
    ("cmd_checkpoint_archive", None): Rule(
        "fiat-checkpoint-archive",
        "archive-checkpoint",
        RUNNING,
        frozenset({"format"}),
        evidence=frozenset({"tail_event"}),
        check="checkpoint-boundary",
    ),
    ("cmd_carryover_export", None): Rule(
        "fiat-cumulative-carryover-custody",
        "export-carryover",
        frozenset({"audit-verdict"}),
        frozenset({"request"}),
        frozenset({"request"}),
    ),
    ("cmd_carryover_bind", None): Rule(
        "fiat-cumulative-carryover-custody",
        "bind-carryover",
        frozenset({"audit-verdict"}),
        frozenset({"request"}),
        frozenset({"request"}),
    ),
    ("cmd_replacement_begin", None): Rule(
        "fiat-replacement-admission",
        "begin-replacement",
        frozenset({"study"}),
        frozenset({"request"}),
        frozenset({"request"}),
    ),
    ("cmd_replacement_resume", None): Rule(
        "fiat-replacement-admission", "advance-replacement", frozenset({"study"})
    ),
    ("cmd_retain_guard", None): Rule(
        "fiat-known-failure-inoculation",
        "retain-guard",
        frozenset({"inoculate"}),
        frozenset({"finding_id", "guard_commit"}),
        frozenset({"finding_id", "guard_commit"}),
    ),
    ("cmd_run_exit", None): Rule(
        "fiat-receipted-delivery",
        "observe-exit",
        frozenset({"run-exit"}),
        frozenset({"criterion"}),
        frozenset({"criterion"}),
    ),
}
"""The closed table, keyed by handler and subcommand.

`config get` writes nothing and has no row. `start-audit-loop` has no row until
the controller declares the Promise that authorises it.
"""

RECOVERY_PATHS = {
    "amendment": {
        ("cmd_amend_study", None): STEP_WORK,
        ("cmd_amend_runbook", None): STEP_WORK,
    },
    "version-resolution": {
        ("cmd_done", "resolve-versions"): frozenset({"resolve-versions", "integrate"}),
    },
    "no-known-inoculation": {
        ("cmd_done", "inoculate"): frozenset({"inoculate", "implement", "run-exit"}),
    },
}
"""Each live pending record, the only commands granted while it is live, and
the directives each is granted at.

A pending record outlives the state write it guards, so its owner must still be
granted at the directive the written state returns: `blocked` after a study
amendment that marks a step, `integrate` after a version resolution, and
`implement` or `run-exit` after a no-known inoculation.
"""

REFUSALS = {
    "preimage-malformed": (
        "rerun `hexctl verify` and pass the verified state digest, ledger tail "
        "and ledger count"
    ),
    "command-unknown": (
        "run `hexctl next` and use the command it names; this controller has no "
        "rule for the requested mutation"
    ),
    "directive-shape-unknown": (
        "recompute the directive with `hexctl next`; a directive carries only "
        "do, step, round and covers"
    ),
    "directive-unknown": (
        "recompute the directive with `hexctl next`; its `do` is outside this "
        "controller's vocabulary"
    ),
    "round-out-of-range": (
        "a loop holds rounds 1 through 8; close the audit, halt, or use another "
        "`audit-verdict` exit"
    ),
    "command-field-unknown": "remove the field; the rule names every field it admits",
    "command-field-missing": "supply the field the rule requires",
    "command-value-malformed": (
        "pass each value as a string, an integer, a boolean, null or a list of "
        "strings"
    ),
    "evidence-field-unknown": "remove the field; the rule names all the evidence it admits",
    "promise-unknown": "name a Promise declared in Fiat's SKILL.md, or name none",
    "promise-mismatch": "name the Promise the rule for this command carries",
    "consequence-unknown": "name a consequence from 0 through 3, or name none",
    "consequence-mismatch": "name the consequence the rule's Promise declares",
    "recovery-path-unknown": (
        "run `hexctl verify`; the pending record is not one this controller can "
        "recover"
    ),
    "recovery-pending": (
        "rerun the command that owns the pending record, then retry this one"
    ),
    "directive-not-authorised": (
        "run `hexctl next`; the command's Promise does not authorise it at the "
        "current directive"
    ),
    "config-path-immutable": (
        "`config set` may change only audit.log_path, git or git.*; audit policy "
        "is fixed at init"
    ),
    "resume-needs-named-exit": (
        "the halt covers an exhausted audit loop; run `hexctl resume --to "
        "audit-verdict`, or leave the run halted, `hexctl reset` it, or use "
        "replacement admission"
    ),
    "resume-exit-unknown": "name `audit-verdict`, the only typed exit, or name none",
    "resume-exit-mismatch": (
        "the halt does not cover `audit-verdict`; run `hexctl resume` with no "
        "exit"
    ),
    "audit-close-needs-no-further-leads": (
        "findings are open; record another round, or close with "
        "`--no-further-leads --reason`"
    ),
    "checkpoint-boundary-unaccepted": (
        "export or archive only immediately after `done push` or at an active "
        "`audit-verdict`"
    ),
    "grant-oversized": "shorten the command values; a grant is at most 65,536 bytes",
}
"""Every stable refusal code, with the recovery its report carries."""


class Refusal(Exception):
    """One closed `fiat-transition-refusal/v1` report, raised before any write."""

    def __init__(self, promise: str, transition: str, code: str) -> None:
        self.report = {
            "schema": REFUSAL_SCHEMA,
            "promise": promise,
            "consequence": PROMISES[promise],
            "blocked_transition": transition,
            "code": code,
            "recovery": REFUSALS[code],
        }
        super().__init__(code)


def canonical(value) -> str:
    """Serialise exactly as the controller fingerprints state."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _is_int(value) -> bool:
    return type(value) is int and -_INT_MAX <= value <= _INT_MAX


def _is_digest(value) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _preimage_holds(state_sha256, ledger_tail, ledger_count, directive) -> bool:
    if not _is_int(ledger_count) or ledger_count < 0:
        return False
    if directive["do"] == ABSENT:
        return state_sha256 is None and ledger_tail == _GENESIS and ledger_count == 0
    return _is_digest(state_sha256) and _is_digest(ledger_tail) and ledger_count >= 1


def _directive_code(directive) -> str | None:
    if (
        type(directive) is not dict
        or not set(directive) <= DIRECTIVE_FIELDS
        or type(directive.get("do")) is not str
    ):
        return "directive-shape-unknown"
    do = directive["do"]
    if do not in DIRECTIVES:
        return "directive-unknown"
    if "step" in directive and (not _is_int(directive["step"]) or directive["step"] < 1):
        return "directive-shape-unknown"
    if ("round" in directive) != (do == "audit-round"):
        return "directive-shape-unknown"
    if ("covers" in directive) != (do == HALTED):
        return "directive-shape-unknown"
    if do == HALTED and (
        type(directive["covers"]) is not str or directive["covers"] not in RUNNING
    ):
        return "directive-unknown"
    if do == "audit-round":
        if not _is_int(directive["round"]):
            return "directive-shape-unknown"
        if not 1 <= directive["round"] <= LOOP_ROUND_MAX:
            return "round-out-of-range"
    return None


def _value_holds(value) -> bool:
    if value is None or type(value) in (str, bool) or _is_int(value):
        return True
    return type(value) is list and all(type(item) is str for item in value)


def _command_code(rule: Rule, command) -> str | None:
    if type(command) is not dict or not all(type(key) is str for key in command):
        return "command-value-malformed"
    if not set(command) <= rule.fields:
        return "command-field-unknown"
    if any(command.get(name) is None for name in rule.required):
        return "command-field-missing"
    if not all(_value_holds(value) for value in command.values()):
        return "command-value-malformed"
    return None


def _evidence_code(rule: Rule, key: tuple, evidence) -> str | None:
    if type(evidence) is not dict or not set(evidence) <= COMMON_EVIDENCE | rule.evidence:
        return "evidence-field-unknown"
    promise = evidence.get("promise")
    if promise is not None:
        if type(promise) is not str or promise not in PROMISES:
            return "promise-unknown"
        if promise != rule.promise:
            return "promise-mismatch"
    consequence = evidence.get("consequence")
    if consequence is not None:
        if not _is_int(consequence) or consequence not in CONSEQUENCE_LEVELS:
            return "consequence-unknown"
        if consequence != PROMISES[rule.promise]:
            return "consequence-mismatch"
    recovery = evidence.get("recovery")
    if recovery is not None:
        if type(recovery) is not str or recovery not in RECOVERY_PATHS:
            return "recovery-path-unknown"
        if key not in RECOVERY_PATHS[recovery]:
            return "recovery-pending"
    return None


def _check_config_set(directive: dict, command: dict, evidence: dict) -> str | None:
    path = command["path"]
    if type(path) is not str:
        return "command-value-malformed"
    if path in CONFIG_SET_EXACT_PATHS or path.startswith(CONFIG_SET_PREFIXES):
        return None
    return "config-path-immutable"


def _check_resume(directive: dict, command: dict, evidence: dict) -> str | None:
    exit_named = command.get("to")
    if exit_named is not None and (
        type(exit_named) is not str or exit_named not in RESUME_EXITS
    ):
        return "resume-exit-unknown"
    covered = directive["covers"]
    if covered in RESUME_EXITS and exit_named is None:
        return "resume-needs-named-exit"
    if exit_named is not None and exit_named != covered:
        return "resume-exit-mismatch"
    return None


def _check_close_audit(directive: dict, command: dict, evidence: dict) -> str | None:
    if directive["do"] == "close-audit":
        return None
    reason = command.get("reason")
    if command.get("no_further_leads") is True and type(reason) is str and reason:
        return None
    return "audit-close-needs-no-further-leads"


def _check_checkpoint_boundary(directive: dict, command: dict, evidence: dict) -> str | None:
    tail_event = evidence.get("tail_event")
    if type(tail_event) is not str or tail_event not in CHECKPOINT_TAIL_EVENTS:
        return "checkpoint-boundary-unaccepted"
    if tail_event == "audit-round" and directive["do"] != "audit-verdict":
        return "checkpoint-boundary-unaccepted"
    return None


CHECKS = {
    "config-set": _check_config_set,
    "resume": _check_resume,
    "close-audit": _check_close_audit,
    "checkpoint-boundary": _check_checkpoint_boundary,
}


def evaluate(
    *,
    state_sha256,
    ledger_tail,
    ledger_count,
    directive,
    handler,
    subcommand,
    command,
    evidence,
) -> dict:
    """Return one exact grant, or raise one stable `Refusal`. Writes nothing."""
    key = (handler, subcommand)
    rule = None
    if type(handler) is str and (subcommand is None or type(subcommand) is str):
        rule = RULES.get(key)
    if rule is None:
        raise Refusal(DEFAULT_PROMISE, "unmapped", "command-unknown")

    def refuse(code: str) -> Refusal:
        return Refusal(rule.promise, rule.transition, code)

    code = _directive_code(directive)
    if code is None and not _preimage_holds(
        state_sha256, ledger_tail, ledger_count, directive
    ):
        code = "preimage-malformed"
    if code is None:
        code = _command_code(rule, command)
    if code is None:
        code = _evidence_code(rule, key, evidence)
    if code is None:
        admitted = rule.directives
        if evidence.get("recovery") is not None:
            admitted = RECOVERY_PATHS[evidence["recovery"]][key]
        if directive["do"] not in admitted:
            code = "directive-not-authorised"
    if code is None and rule.check is not None:
        code = CHECKS[rule.check](directive, command, evidence)
    if code is not None:
        raise refuse(code)
    grant = {
        "schema": GRANT_SCHEMA,
        "promise": rule.promise,
        "consequence": PROMISES[rule.promise],
        "transition": rule.transition,
        "directive": dict(directive),
        "state_sha256": state_sha256,
        "ledger_tail": ledger_tail,
        "ledger_count": ledger_count,
        "handler": handler,
        "subcommand": subcommand,
        "command": {
            name: list(value) if type(value) is list else value
            for name, value in command.items()
        },
    }
    if len(canonical(grant).encode("utf-8")) > MAX_GRANT_BYTES:
        raise refuse("grant-oversized")
    return grant
