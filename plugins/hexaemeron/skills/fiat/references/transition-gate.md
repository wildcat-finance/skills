# Fiat transition gate

`scripts/transition_gate.py` decides whether one Fiat mutation is authorised
against one verified preimage. It returns one grant or raises one refusal. It
imports only the standard library, opens no file, starts no process and reads
no prose: a command value travels into the grant as data and is compared only
where a rule names an exact vocabulary.

`hexctl.py` does not call the gate yet. Until the dispatcher does, the gate
refuses nothing in a live run, and `resume --to`, which one recovery line
names, is not a controller flag.

## Same-account limit

The gate, its table and any pin that later guards them are files the
delivering agent can write under the same operating-system account. A
mismatch is tamper evidence and a deterministic refusal. It is not privilege
isolation, and no message or document may call it that. Prevention against an
agent that sets out to bypass the gate needs a writer and a pin authority
outside that agent's write authority, which this controller does not have.

## Call

```python
transition_gate.evaluate(
    state_sha256=..., ledger_tail=..., ledger_count=...,
    directive=..., handler=..., subcommand=..., command=..., evidence=...,
)
```

| Argument | Accepted form |
| --- | --- |
| `state_sha256` | 64 lowercase hex characters, the fingerprint of the verified state; `None` only when the directive is `absent` |
| `ledger_tail` | the `hash` of the last verified ledger entry; `genesis` only when the directive is `absent` |
| `ledger_count` | the verified entry count, at least 1; 0 only when the directive is `absent` |
| `directive` | the canonical directive below |
| `handler`, `subcommand` | one key of the rule table, such as `cmd_done` and `audit`; `None` where the handler has no subcommand |
| `command` | the fields the operator supplied, by argparse destination name; each value a string, an integer, a boolean, null or a list of strings |
| `evidence` | `promise`, `consequence` and `recovery`, each optional, plus any field the rule names |

Every value is an exact built-in type. A subclass of `dict`, `str` or `list`
refuses, and so does an integer outside the signed 64-bit range. No input
leaves `evaluate` as any exception but `Refusal`.

The canonical directive is a projection of `_next_directive`, not its whole
output. It carries `do`, an optional positive `step`, `round` when and only
when `do` is `audit-round`, and `covers` when and only when `do` is `halted`.
`covers` is the `do` the run would return with the halt removed. `absent`
means no run exists. `round` is 1 through 8; nothing represents a ninth round.

The `do` vocabulary is `absent`, `halted`, `blocked`, `study`, `runbook`,
`inoculate`, `implement`, `run-exit`, `resolve-security-suite`, `audit-round`,
`close-audit`, `audit-verdict`, `prose`, `push`, `merge-step`,
`resolve-versions`, `integrate` and `done`.

`evidence.promise` and `evidence.consequence` are the caller's claim. When
present they must be declared and must equal the rule's own. `evidence.recovery`
names a live pending record: `amendment`, `version-resolution` or
`no-known-inoculation`. While one is live, only the command that owns it is
granted: `amend study` or `amend runbook`, `done resolve-versions`, and `done
inoculate`.

A pending record outlives the state write it guards, so its owner is granted
at the directive the written state returns as well as at its own row's:

| Pending record | Owner | Directives while the record is live |
| --- | --- | --- |
| `amendment` | `amend study`, `amend runbook` | step work, `blocked` included |
| `version-resolution` | `done resolve-versions` | `resolve-versions`, `integrate` |
| `no-known-inoculation` | `done inoculate` | `inoculate`, `implement`, `run-exit` |

The gate cannot see the pending file. The caller must set `recovery` from the
record on disk, never from the operator's arguments.

## Schemas

`fiat-transition-grant/v1` has exactly these fields:

| Field | Content |
| --- | --- |
| `schema` | `fiat-transition-grant/v1` |
| `promise` | the rule's Promise id |
| `consequence` | the consequence that Promise declares in Fiat's `SKILL.md` |
| `transition` | the rule's transition name |
| `directive` | the canonical directive the grant holds for |
| `state_sha256` | the state digest the grant holds for |
| `ledger_tail`, `ledger_count` | the ledger tail and count the grant holds for |
| `handler`, `subcommand` | the rule key |
| `command` | the normalised command, with each list copied so the caller holds no reference into the grant |

Its canonical JSON is at most 65,536 bytes. A larger one refuses.

`fiat-transition-refusal/v1` has exactly these fields:

| Field | Content |
| --- | --- |
| `schema` | `fiat-transition-refusal/v1` |
| `promise` | the rule's Promise id, or `fiat-receipted-delivery` when no rule was reached |
| `consequence` | that Promise's consequence |
| `blocked_transition` | the rule's transition name, or `unmapped` |
| `code` | one stable code from the list below |
| `recovery` | the fixed recovery line for that code |

`Refusal.report` holds the object. A refusal answers the on-call question of
why a mutation refused. A later version of either schema takes a new name.

## Rule table

Each row grants only at the directives listed. `active` is every `do` except
`absent`; `running` is `active` without `halted`; `step work` is `blocked`,
`inoculate`, `implement`, `run-exit`, `resolve-security-suite`, `audit-round`,
`close-audit`, `audit-verdict`, `prose` and `push`.

| Handler | Subcommand | Promise | Transition | Directives |
| --- | --- | --- | --- | --- |
| `cmd_init` | | `fiat-receipted-delivery` | `open-run` | `absent` |
| `cmd_observe` | | `fiat-run-observation-binding` | `bind-observation` | active |
| `cmd_record` | | `fiat-receipted-delivery` | `record-receipt` | active |
| `cmd_config` | `set` | `fiat-receipted-delivery` | `config-set` | active |
| `cmd_amend_study` | | `fiat-study-amendment` | `amend-study` | step work except `blocked` |
| `cmd_amend_runbook` | | `fiat-runbook-amendment` | `amend-runbook` | step work |
| `cmd_done` | `study` | `fiat-receipted-delivery` | `receipt-study` | `study` |
| `cmd_done` | `runbook` | `fiat-receipted-delivery` | `receipt-runbook` | `runbook` |
| `cmd_done` | `inoculate` | `fiat-known-failure-inoculation` | `receipt-inoculate` | `inoculate` |
| `cmd_done` | `implement` | `fiat-receipted-delivery` | `receipt-implement` | `implement` |
| `cmd_done` | `audit` | `fiat-receipted-delivery` | `receipt-audit` | `close-audit`, `audit-round`, `audit-verdict` |
| `cmd_done` | `prose` | `fiat-receipted-delivery` | `receipt-prose` | `prose` |
| `cmd_done` | `push` | `fiat-receipted-delivery` | `receipt-push` | `push` |
| `cmd_done` | `merge-step` | `fiat-receipted-delivery` | `receipt-merge-step` | `merge-step` |
| `cmd_done` | `sync-run` | `fiat-receipted-delivery` | `receipt-sync-run` | `integrate`, `resolve-versions` |
| `cmd_done` | `resolve-versions` | `fiat-version-resolution` | `receipt-resolve-versions` | `resolve-versions`, `integrate` |
| `cmd_done` | `integrate` | `fiat-final-integration` | `receipt-integrate` | `integrate` |
| `cmd_audit_round` | | `fiat-receipted-delivery` | `append-round` | `audit-round` |
| `cmd_halt` | | `fiat-receipted-delivery` | `set-halt` | active |
| `cmd_resume` | | `fiat-receipted-delivery` | `clear-halt` | `halted` |
| `cmd_reset` | | `fiat-local-retirement` | `retire-run` | `done`, `halted` |
| `cmd_checkpoint_export` | | `fiat-controller-checkpoint` | `export-checkpoint` | running |
| `cmd_checkpoint_archive` | | `fiat-checkpoint-archive` | `archive-checkpoint` | running |
| `cmd_carryover_export` | | `fiat-cumulative-carryover-custody` | `export-carryover` | `audit-verdict` |
| `cmd_carryover_bind` | | `fiat-cumulative-carryover-custody` | `bind-carryover` | `audit-verdict` |
| `cmd_replacement_begin` | | `fiat-replacement-admission` | `begin-replacement` | `study` |
| `cmd_replacement_resume` | | `fiat-replacement-admission` | `advance-replacement` | `study` |
| `cmd_retain_guard` | | `fiat-known-failure-inoculation` | `retain-guard` | `inoculate` |
| `cmd_run_exit` | | `fiat-receipted-delivery` | `observe-exit` | `run-exit` |

A fresh study amendment refuses at `blocked`, where only the runbook repair
is granted. `done sync-run` is granted at `resolve-versions` because that
directive names the base sync as its recovery when the base has advanced.
`done resolve-versions` is granted at `integrate` as well, because a base sync
leaves the recorded resolution stale and the handler renews it there.

`config get` writes nothing and has no row. `start-audit-loop` has no row: no
declared Promise authorises it, so an exhausted loop cannot be continued
through the gate.

Four rows carry a check of their own:

- `config set` grants only the ADR-047 allowlist: `audit.log_path`, `git` and
  any path below `git.`. `audit.max_rounds`, the whole `audit` section and
  every other path refuse.
- `resume` takes `note` and `to`. `to` may name only `audit-verdict`. When the
  halt covers `audit-verdict`, which is an exhausted audit loop, a `resume`
  that names no exit refuses and `to` naming `audit-verdict` is granted. When
  the halt covers anything else, a `resume` naming no exit is granted and one
  naming `audit-verdict` refuses.
- `done audit` at `audit-round` or `audit-verdict` needs `no_further_leads`
  true and a `reason` that is not empty. At `audit-round` with `round` 1 it
  refuses whatever it carries, because no round is recorded yet.
- `checkpoint export` and `checkpoint archive` need `evidence.tail_event`:
  `done:push`, or `audit-round` with the directive at `audit-verdict`.

## Stable refusal codes

| Code | Raised when |
| --- | --- |
| `command-unknown` | no rule has this handler and subcommand |
| `directive-shape-unknown` | the directive is not a mapping, carries an unknown field, lacks a string `do`, or carries `step`, `round` or `covers` in the wrong form or place |
| `directive-unknown` | `do` or `covers` is outside the vocabulary |
| `round-out-of-range` | `round` is not 1 through 8 |
| `preimage-malformed` | the state digest, ledger tail or ledger count has the wrong form for the directive |
| `command-field-unknown` | the command carries a field the rule does not name |
| `command-field-missing` | a field the rule requires is absent or null |
| `command-value-malformed` | the command is not a plain mapping with string keys, or a value is not a string, 64-bit integer, boolean, null or list of strings |
| `evidence-field-unknown` | the evidence is not a mapping, or carries a field the rule does not name |
| `promise-unknown` | the claimed Promise id is not one the table declares |
| `promise-mismatch` | the claimed Promise id is not the rule's |
| `consequence-unknown` | the claimed consequence is not an integer from 0 through 3 |
| `consequence-mismatch` | the claimed consequence is not the rule's |
| `recovery-path-unknown` | the named pending record is not one of the three |
| `recovery-pending` | a pending record is live and another command owns it |
| `directive-not-authorised` | the rule does not grant at the current directive |
| `config-path-immutable` | the `config set` path is outside the ADR-047 allowlist |
| `resume-needs-named-exit` | the halt covers an exhausted audit loop and `to` is absent |
| `resume-exit-unknown` | `to` names anything but `audit-verdict` |
| `resume-exit-mismatch` | `to` names `audit-verdict` and the halt covers something else |
| `audit-close-needs-a-round` | `done audit` arrives at `audit-round` with `round` 1, before any round is recorded |
| `audit-close-needs-no-further-leads` | `done audit` with findings open lacks `no_further_leads` or its reason |
| `checkpoint-boundary-unaccepted` | the ledger tail event and directive name neither accepted boundary |
| `grant-oversized` | the grant's canonical JSON exceeds 65,536 bytes |

Checks run in this order and the first failure is the one reported: rule
lookup, directive, preimage, command, evidence, directive admission, the
rule's own check, grant size. A code keeps its meaning; a new condition takes
a new code.
