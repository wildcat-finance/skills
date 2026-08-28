# ADR-004: Separate run and reachability evidence

## Status

Accepted, 2026-08-27.

## Context

Issue 437 proposes a report-only dead-code baseline. Its candidates describe
repository reachability, and issue 437 itself records that an analyser
finding does not prove semantic uselessness. Run observations describe what
one agent run did. The two say different things about different subjects, and
merging them would let a reachability guess borrow the credibility of a
checked run record.

## Decision

The prototype rejects issue-437 data as an input class. The manifest admits
only `promise-machine-run-observation/v1` records, the rule kinds read only
run events, and no finding type describes dead or unreachable code. Admitting
reachability evidence requires its own study and its own promise before any
schema here changes.

## Alternatives

- Admit dead-code candidates as a third disposition. Rejected: a disposition
  describes a run, and a reachability candidate is not a run.
- Join the two in one finding when they point at the same path. Rejected:
  the join is exactly the unsupported inference, dressed as a convenience.

## Consequences

Synkrisis stays smaller than the observations people may want from it, and a
future admission of reachability evidence has a clean seam: a new producer
contract in the manifest, a new rule kind, and a promise stating what the
combination establishes and what it refuses.
