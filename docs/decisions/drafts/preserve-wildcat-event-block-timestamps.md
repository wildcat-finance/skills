# Decision: Preserve Wildcat event block timestamps in an additive journal

## Status

Accepted, 2026-10-11, for issue #1997; implementation conformance remains pending.

## Context

Most Wildcat archive records lack a preserved header for their event block.
Existing immutable captures bind exact opening sequences and component inventories.
A new mandatory read would invalidate those releases. Consumers need row-local
dates without treating provider records as independent chain proof.

## Decision

Select `collector-journal`: opt new bounded Wildcat V1/V2 plans into an additive
event-header journal, and join preserved headers by exact event block number and
hash in the offline archive view and dossier.

## Alternatives

`existing-only` adds no collection boundary but leaves most future event blocks
without dates and fails the future-coverage selection gate. `external-sidecar`
can enrich old releases but requires one additional independently supplied input
and custody join. The integrated journal needs none and wins that criterion.
The eighteen source-bound selection reports under `docs/kickoff/1997/reports/`
observe a proposal model; they do not establish production conformance.

## Consequences

An absent opt-in marker preserves legacy opening reads and inventories. New
captures must bind the marker, complete header inventory and checkpoint/resume
bytes while respecting existing request, byte, partition and time limits.
Headers are deduplicated by event block identity; contradictory evidence cannot
be selected by first or last arrival. Missing or mismatched evidence leaves
only the affected record undated with a specific reason.

Timestamps retain provider-recorded class and exact response/component references.
Neither neighbouring headers, native close arguments nor fabricated zero supply
a date. Canonical schema-3 timestamps, fleet recapture, private fixture publication
and stronger chain or borrower-identity claims remain outside this decision.
Step 1 records the format choice and proof scaffold. The production demonstration
must pass before the selected design's integration conformance can be admitted.
