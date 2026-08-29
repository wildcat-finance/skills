# ADR-047: Freeze Fiat configuration after init

## Status

Accepted, 2026-08-29.

## Context

Fiat returned an audit verdict after eight rounds with a finding still open.
Instead of stopping there, a caller used `config set audit.max_rounds 9` and
made the controller issue a ninth-round packet. The command was ledgered and
valid under the controller even though ADR-028 says the per-loop ceiling must
never be raised to simulate another loop.

An instruction to leave the setting alone is not enforcement. The controller
accepted writes to every existing config path, including whole-section writes.
The caller and operator also share one operating-system account, so file
permissions cannot distinguish them.

## Decision

After `init`, `hexctl config set` accepts only:

- the exact `audit.log_path` leaf;
- the exact `git` section; and
- paths below `git`.

Every other path is immutable. The refusal runs before value parsing, path
traversal or ledger append, and leaves both state and ledger bytes unchanged.
There is no override flag or environment-variable escape.

`config get` continues to read the complete config. `init` still creates the
complete default config and derives the run-specific audit-log path. Older
states that already contain different audit, skill or Solidity values remain
readable; the new controller does not rewrite them.

The audit-log leaf keeps its existing confinement and run-specific basename
checks. The Git section remains mutable because the operator explicitly kept
that operational surface outside this gate.

## Consequences

Changing an audit ceiling, folding policy, audit branch suffix, skill identity
or Solidity classification can no longer move a live run past a controller
gate. A caller must stop at `audit-verdict` and use the checked transition the
controller names.

The controller cannot prevent a process with repository write access from
altering files or replacing the controller itself. Direct state edits remain
outside `config set` and break the state fingerprint checked against the
ledger. This decision establishes the controller command boundary, not an
operating-system security boundary.

Legacy override behavior remains available only when it was already recorded
in a state created by an older controller. New runs classify Solidity from the
`security_suite` receipt and keep audit folding false.

## Alternatives

- Keep every path mutable and rely on agent instructions. Rejected because the
  incident showed that prose did not stop the write.
- Add a general operator override flag. Rejected because the same caller could
  invoke it, so it would not enforce the requested boundary.
- Protect the state file with permissions. Rejected because the caller and
  operator share the same operating-system identity.
