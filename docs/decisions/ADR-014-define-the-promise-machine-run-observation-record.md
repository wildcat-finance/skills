# ADR-014: Define the Promise Machine run observation record

## Status

Accepted, 2026-08-23. Recorded for [skills#434](https://github.com/wildcat-finance/skills/issues/434).

## Context

Promise Machine defines the suite-wide evidence classes and the limits on what
their records authorise. Fiat records delivery transitions, but its controller
ledger is not a host-neutral account of capability use, refusals, retries,
handoffs, unknowns, or observed outcomes. Host transcripts are not a stable or
safe interchange surface, and hidden model reasoning is not observable.

Later work needs one versioned JSON Lines record whose identities, order,
references, evidence subjects, and evidence classes can be checked offline.
The record must preserve missing host facts as unknown, accept token counts
only when a host or provider exposes them, and authorise no mutation or truth
claim merely because its structure validates.

## Decision

The root Promise Machine owns `promise-machine-run-observation/v1`: a closed
event schema, a bounded standard-library validator, and a narrow structural
validation promise. The schema belongs at
`schemas/promise-machine-run-observation-v1.schema.json`; relational checks
belong in `scripts/run_observation.py`; operator guidance belongs in
`docs/promise-machine/run-observation-v1.md`.

Fiat may produce or consume records at its own transitions, but its ledger
does not become the interchange format. Ephoros supplies the observability
questions and signal discipline without becoming a suite-wide record store.
Capture, redaction, persistence, search, Fiat receipt binding, and cross-run
diagnosis remain separate work.

## Alternatives

- **Put observations in Fiat's ledger.** This would reuse ordered JSON Lines,
  but would couple general observations to controller integrity, make Fiat the
  only producer, and pre-empt the separate receipt-binding work.
- **Adopt OpenTelemetry as the canonical record.** This offers existing
  telemetry conventions, but does not supply the repository's exact Promise
  Machine evidence semantics, offline fixtures, or closed payload boundary.
- **Publish prose examples without an executable contract.** This avoids a
  validator, but cannot enforce identity, order, backward references, evidence
  binding, or refusal of hidden-reasoning fields.

## Consequences

Producers gain one host-neutral versioned format and deterministic findings.
Consumers can validate structure and relations without executing record
content, fetching a service, or importing a host SDK. Optional host, model,
and token facts remain source-bound or unknown.

The repository takes on schema/runtime drift and fixture-maintenance duties.
Validation establishes only acceptance by the named structural rules; it does
not establish completeness, external truth, cause, model quality, delivery
correctness, or authority to mutate a repository. Any future capture, storage,
receipt binding, or diagnosis surface must preserve that boundary and record
its own promise.
