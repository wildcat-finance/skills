# ADR-069: Gate Fiat mutations and continue audits as append-only loops

## Status

Accepted, 2026-09-03.

## Context

Fiat's state and hash-chained ledger can prove the order and shape of recorded
transitions, but the current dispatcher does not join that evidence to one
closed grant before every effect. The same gap exists around writers outside
the ordinary state-and-ledger path, including delegated brief output,
checkpoint export and restore, reset, archive, breadcrumb, and publication
effects.

The audit model also has one flat `steps[*].audit.rounds` list. The list cannot
represent another bounded audit loop without rewriting the existing records or
continuing the numbering as round 9. Both outcomes conflict with
[ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md):
legacy rounds are loop 1, a later loop starts at round 1 on the same ledger,
and the earlier loop remains immutable. Raising a completed loop's ceiling is
also barred by
[ADR-047](ADR-047-freeze-fiat-configuration-after-init.md).

The checked design record selected `append-only-loop-kernel` from three
candidates. The selection preserves the physical loop-1 bytes, covers every
declared effect class, and admits a recoverable state-and-ledger publication
path. Later conformance evidence remains due at the transitions named by
[the study](../fiat-transition-gate-study.md), consistent with
[ADR-061](ADR-061-lock-designs-with-progressive-checked-evidence.md).

## Decision

Fiat will use `append-only-loop-kernel`.

Existing `steps[*].audit.rounds` entries remain the physical record of loop 1.
Later loops are appended as closed continuation objects. Each continuation
records its loop number, immutable maximum of 1 through 8 rounds, predecessor
digest, checkpoint and active-preimage identities, authority evidence,
complete finding carryover, and its own append-only rounds. One projection
helper presents both layouts to readers; no writer migrates loop 1.

A pure transition gate decides whether a normalised command may produce one
effect. Its grant binds the active state and ledger preimage, canonical
directive, Promise id, consequence, command digest, evidence digest, and one
transition id. A closed effect registry assigns every effectful command to its
Promise, evidence builder, grant rule, and sole writer path. Read-only commands
receive no writer capability, and derived-output or publication writes keep
their own effect classes.

Audit continuation uses a separate
`fiat-checkpoint-audit-loop-continuation` Promise and the checked
`start-audit-loop` command. It accepts only an exhausted, finding-bearing
`audit-verdict` whose checkpoint or unique restored descendant matches the
active preimage. It appends loop `N + 1` with round 1, preserves every prior
loop and the audit-log prefix, and carries every final-round finding id plus
the exact unresolved-leads digest. It never changes an earlier loop's maximum
or treats a generic resume note as authority.

State and ledger publication uses a write-ahead transaction. The writer stages
`state.next`, `ledger.next`, the grant, and a closed manifest in one private
directory, makes those bytes durable, then publishes a durable pending marker
before replacing either live file. Recovery accepts only the exact preimage,
the exact postimage, or the two named mixed windows whose staged bytes match.
It completes the recorded postimage and never guesses or rolls back an
append-only ledger. This costs a projection helper, staged copies, fsyncs, and
explicit crash recovery, but it avoids claiming that two file replacements are
one POSIX-atomic operation.

The gate ships inside the artefact it gates. This delivery therefore cannot
claim that the new gate governed its own creation; final integration installs
and pins the checked path, and later changes require a separate maintainer
review and new manifest and controller digests. Integrity checks provide
deterministic refusal and tamper evidence. They do not provide privilege
isolation from a process that can replace both the verifier and launcher under
the same operating-system account.

## Alternatives

- **`nested-loop-state-v2`.** Migrate every legacy audit into a uniform
  `audit.loops` structure, then add the same gate and transaction machinery.
  Uniform readers would be simpler after migration, but migration rewrites the
  physical loop-1 subtree and fails the required byte identity. It also needs
  three safe continuation slices instead of one before the path can exist.
- **`continuation-sidecar`.** Add a checked sidecar for later rounds while
  retaining the current dispatcher and state-ledger commit path. It reaches a
  loop-2-shaped display with no legacy rewrite, but leaves two authorities for
  one audit and supplies no complete writer discovery, central transaction,
  integrity-first dispatch, or publication grant. It therefore fails the
  protected-scope and recovery gates.

## Consequences

Legacy Fiat states remain readable and byte-preserved, and a later audit loop
can continue the same ledger without inventing round 9. Readers pay for one
audited projection across the legacy list and continuation objects. Writers
pay for closed effect classification and recoverable staged publication.

Every mutation and external write now needs exact preimage and grant evidence.
This expands hostile tests and integrity manifests, but makes a refusal occur
before the effect or leave one labelled recovery transaction. The resulting
checks establish only the named command and evidence boundary; they do not
close inherited findings, prove the selected criteria sufficient, or turn an
authority statement into proof of its author.

The bootstrap and same-account limits remain visible in the standing record.
A later deployment may add operating-system separation or an external broker,
but that would be a new trust boundary and requires a new decision.
