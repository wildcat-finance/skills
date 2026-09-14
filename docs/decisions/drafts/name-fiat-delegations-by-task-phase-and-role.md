# Decision: Name each Fiat delegation by task, phase and role on the `next` envelope

## Status

Accepted, 2026-09-14. The record takes its number at the integration
composition, where the merge composer assigns one from the base branch.

## Context

Fiat delegates four phases: `study` to Surveyor, `implement` to Mason,
`audit-round` to Warden and `prose` to Scribe. Before issue 363 the `next`
envelope carried `state_sha256`, `agent` and a source-bound `brief`, and nothing
named the task a delegate was spawned or continued for. The orchestrator chose
the name, and on the issue 320 run it continued a Mason under `issue318_step2`,
a handle from an earlier issue.

A host spawns and names its own agents, so the controller cannot rename one. It
can state the name the current delegation should carry and refuse a name it is
shown that differs. Everything that name needs is already in controller state.
The study behind this record is `docs/fiat-delegated-task-identity-study.md`.

## Decision

`hexctl next` puts a `fiat-task-identity/v1` object beside `agent` on every
delegated envelope as `task_identity`, holding its `schema`, `handle`, `task`,
`step`, `round` and `role`. An inline directive carries `task_identity: null`.
The handle grammar is `fiat-<task>-<phase>-<role>`:

- `<task>` is the run anchor's GitHub issue number. A run whose anchor names no
  GitHub issue uses its topic slug, at most 48 characters, or `run` when the
  slug is empty. A slug of digits alone takes the prefix `topic-`, so topic
  `363` derives `topic-363` and cannot equal the segment issue 363 derives.
- `<phase>` is `study` for the Surveyor and `step-<n>` for Mason, Warden and
  Scribe.
- `<role>` is `surveyor`, `mason`, `warden` or `scribe`.

`round` stays in the object and out of the handle, so a Warden continued across
the rounds of one step keeps one handle and a step change changes it.

`hexctl next --task-handle <observed>` compares the handle an orchestrator is
about to continue with `task_identity.handle` by exact equality. It exits 2
before printing a directive or writing a brief when the value differs, is
empty, exceeds 200 bytes, holds a whitespace or non-printable character, or
meets a directive with no delegate. Fiat's `SKILL.md` makes that check
unconditional before any existing handle is continued.

The identity lives on the envelope, not in the brief, and `next` stays
read-only: no ledger event, state container or receipt field is added.

## Alternatives

**Bind the handle into each phase receipt.** `done` would refuse a receipt
whose recorded handle names another issue, step or role. The mismatch would
surface only after the whole phase had run, and every receipt shape and the
`verify` replay would change: two durable additions, and a compatibility
question for runs recorded before them.

**Require the name in prose alone.** Fiat's `SKILL.md` and the agent files
would ask for a fresh, correctly named handle, and nothing would check it. A
stale handle would never be refused and the identity would be whatever the
orchestrator typed, so this failed the `stale-handle-refused-mechanically`
gate.

**Mint handles in a ledger registry.** A mutating `hexctl delegate` would
record each handle and refuse one already issued for another step or role. Its
refusal is the strongest, but it adds a state registry, a ledger event and a
`verify` rule, after compaction `next` would no longer reconstruct the whole
delegation, and a derived handle already gives the same answer from state.

**Carry the identity inside the brief.** Four brief key sets are pinned by
tests, and `--brief-out` moves the brief body out of the printed directive. On
the envelope the identity leaves every brief shape unchanged and stays on the
directive the orchestrator reads.

## Consequences

A stale handle is detected before any phase runs, and a refused handle never
receives a brief. Identical state gives an identical identity across processes,
after compaction and after a checkpoint restore.

The guarantee rests on the orchestrator running the check. The controller
refuses only a handle it is shown, so a host or orchestrator that continues a
delegate without asking is not caught, and whether a host displays the handle
as the task's name is outside the controller.

A refusal leaves no durable record. A refused `next` writes nothing, and no
`next` call writes state or a ledger entry, so whether a refusal happened
earlier in a run cannot be answered from state or the ledger; only the session
that saw it knows. That signal gap is accepted to keep `next` read-only. For
the same reason, a brief that an earlier `next --brief-out` call left at its
path survives a refused call and is not the current directive's.

A handle carries no run discriminator. A run reset and initialised again for
the same issue, or a run of that issue in another clone, derives the same
handles, so a delegate left from the earlier run passes the check. Topic-only
runs whose topics share a slug share handles as well: topics `363` and
`Topic 363` both derive `topic-363`.

Anything that names delegated tasks by this grammar depends on it, so a later
change to the grammar changes every handle an in-flight run expects.
