# ADR-024: Bind run-observation prefixes to Fiat receipts

## Status

Accepted, 2026-08-24. Recorded for
[skills#436](https://github.com/wildcat-finance/skills/issues/436).

ADR-023 is reserved for another decision. This record follows ADR-015, which
defines the observation event stream, and ADR-022, which defines safe capture
before persistence.

## Context

Fiat receipts prove controller transitions and their recorded evidence. A
companion observation stream can explain what happened during a run, but its
availability and truth are independent of delivery. Putting every event in the
Fiat ledger would turn the controller's bounded transition record into a
telemetry store. Making observations mandatory would also let an observer
failure invalidate work whose own receipts remain sound.

## Decision

Fiat provides an explicit `hexctl observe` transition. It binds the complete,
validated `promise-machine-run-observation/v1` prefix available at that moment
to the immediately preceding ledger receipt. The binding records the
controller run identity, receipt hash, event interval, event and byte counts,
prefix SHA-256, and capture, validation, and redaction results. Observation
events remain outside controller state and the ledger.

The transition does not advance the workflow. Ordinary `hexctl verify` checks
only controller state and ledger integrity. `hexctl verify --observations`
asks the separate dependent claim and recomputes each selected prefix. A later
append leaves the earlier prefix valid and reports the tail as unbound.
Replacement, reordering, truncation, identity drift, and failed gates refuse
that claim with a stable `FOB` finding.

A missing, gapped, refused, unknown, or unavailable capture records no digest.
It stays visible without weakening or invalidating the preceding Fiat receipt.

## Alternatives

- **Store events in the Fiat ledger.** This gives one chain, but makes event
  volume and capture failure part of the controller's critical path.
- **Add optional observation fields to every phase command.** This appears
  convenient, but spreads capture semantics across every handler and obscures
  whether a failed observer also failed delivery.
- **Bind the whole mutable file.** This loses a valid earlier claim whenever
  another event is appended.

## Consequences

Operators make one additional explicit selection when an observation boundary
matters. The receipt remains small and exact, while the appendable stream stays
outside the delivery ledger. An observation binding proves only that the named
prefix passed the structural, identity, and gate checks and matched the named
receipt at verification time. It does not prove event truth, completeness,
causation, model quality, or successful delivery.
