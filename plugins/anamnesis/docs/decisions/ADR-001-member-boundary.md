# ADR-001: Own audit corpus custody in a separate member

## Status

Accepted, 2026-08-31.

## Context

Hundreds of Fiat runs have produced audit rounds, findings, fixes and Elenchus
verdicts. Nothing keeps them. Warden writes one round's record inside one run
and stops. Elenchus starts from a failure already in hand, proves its cause,
and guards it. Synkrisis compares declared run observations and infers bounded
relations between named events.

Custody is a different job from all three. It runs on a different clock: a
source admitted today must still be readable, and still carry its permission
basis, years after the run that produced it closed. It carries obligations the
other three do not have, because a corpus that redistributes bytes has to know
what it is allowed to redistribute.

Two cheaper placements were available, and the study measured both against a
closed criterion matrix rather than a prose rubric.

## Decision

Anamnesis is a separate Promise Machine member with three promises: source
admission, corpus curation, and corpus release. No existing member's promise
is broadened.

Elenchus and Synkrisis become consumers of read-only projections, described in
[ADR-004](ADR-004-consumer-projections.md).

## Alternatives

**Make the corpus an Elenchus reference library.** Cheapest to start: a
directory of cases beside a skill that already reasons about failures. It fails
the closed-corpus gate, because Elenchus would then own acquisition, rights,
deduplication and release alongside its one-failure causal proof. It also fails
the preserved-consumer gate: the member that must prove a present cause would
hold the library of past ones, and a reader could not tell which of the two a
`guarded` verdict came from.

**Extend Synkrisis to ingest findings before comparing them.** Synkrisis
already builds cohorts, so the comparison machinery exists. It fails the same
two gates. Synkrisis refuses capture and redaction by design; giving it source
custody reverses that refusal, and its bounded inference boundary would then sit
downstream of its own ingestion.

Both alternatives broaden exactly one existing promise. The separate member
broadens none, at the cost of more visible scaffolding.

## Consequences

The suite gains a member, its manifests, its ledger and its tests. That cost is
paid once and is visible in the tree.

Elenchus keeps its narrow claim: a `guarded` verdict still requires the present
failure reproduced and the old-fails/new-passes specimen bound. An analogue
retrieved from the corpus is a hypothesis and can never supply that verdict.

Synkrisis keeps its refusal of capture and custody. It reads a declared
projection and nothing else.

The corpus can be versioned, migrated and re-released without touching either
consumer, because neither owns its schema.
