# Decision: Record execution once and join declared criteria to that result

## Status

Accepted, 2026-09-16, for the #1273 study. Publication in the canonical numberless draft home is due in Step 1; production conformance remains pending. This study record has no ADR number.

## Context

Protasis can require a checkable criterion without the current Fiat controller joining it to an actual successful execution at completion. Existing command-interface records deliberately carry `operation_ran:false`. Issue #1273 asks for the consuming step and exact settling Exit command, then a recorded successful result. It does not ask the controller to judge criterion sufficiency or whether the command truly tests its claim.

The new controller must preserve unmarked historical runs. The active outer controller is fixed outside the target and cannot enforce its own successor. The implementation therefore needs a separate demonstration using the new checked-in controller.

## Decision

Bind each closed study criterion to its effective step Exit command, let the controller record one actual execution with its source context, and require that bound successful result at the consuming-step and integration gates without rerunning commands during verification.

The all-criteria join must pass before `next` emits the integration directive, then pass again at `done integrate`. The GitHub merge occurs before that receipt, so a receipt-only check would be too late. Unsettled or tampered results withhold the directive; inspection does not execute commands.

A new immutable init contract marker activates the join. The descriptor includes id, claim, step and exact command. Several descriptors may share one observation. State alone cannot activate or erase the marker. Missing, failed, interrupted, oversized or mismatched evidence stays unmet.

Execution uses the pinned interpreter, registered argv, no shell, a closed environment and bounded streaming reads. Results bind the implementation commit, accepted source receipts, descriptor, command and CLI/adapter identities. Later audit changes do not turn this historical observation into final-tree correctness evidence.

Completed descriptors cannot be removed, changed or reassigned by amendment. Unbuilt descriptors may change through the existing admission path and then need new evidence. Unrelated amendments preserve identical completed descriptors through the verified history. Restoration preserves recorded context without granting execution authority to an old root.

## Alternatives

- **Producer report:** a caller supplies command/exit JSON. This takes less integration work, but the observed policy specimen accepted a fabricated success before a command ran. It failed the required execution-custody gate.
- **Terminal replay:** every terminal inspection executes the command. It observes real execution, but the specimen launched three times for one build and two inspections. Repeated verification would become an action and could repeat side effects.
- **Controller capture:** the specimen launched once, rejected unexecuted and mismatched evidence, kept failures unmet and preserved legacy absence. Durable custody, interruption handling and a new operation are the accepted implementation cost.

These were executed policy specimens with synthetic source descriptors, not proof of the future controller's security or correctness. The largest sample record was 345 bytes. That is not a production storage estimate or performance claim.

## Consequences

Read-only verification can explain which accepted criterion lacks which observed result. A deliberately vacuous successful command still passes this bounded contract. Criterion sufficiency, semantic correctness, final-tree correctness, hostile-host attestation and a new sandbox remain outside the promise.

The prototype adds declared limits: 128 criteria in the existing 256 KiB study, 512 attempts and 4 MiB of new canonical result data per run, and 4 MiB observed per stream plus a 1,800-second deadline per attempt. Interrupted execution has no at-most-once guarantee. An explicit retry creates a new observation; it cannot fabricate the old one.

The selected design has five pending conformance gates: standing record before Step 2, declaration behavior before Step 3, execution custody before Step 4, terminal/legacy replay before Step 5, and a new-controller demonstration before integration. Existing full-suite Elenchus limitations remain; no `guarded` verdict is promised in advance.

The standing home is `docs/decisions/drafts/settle-study-criteria-from-recorded-execution.md`. Number assignment belongs to final integration against the actual base. Protasis and Fiat keep their own promise/version decisions in their ledgers. Per-step package increments and the intervening #1685 sync are separate delivery obligations.
